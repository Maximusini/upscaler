import numpy as np
import math
import cv2
import gc
import onnxruntime as ort
from src.core.system_utils import get_vram_limit
import logging

class Upscaler:
    def __init__(self, model_path:str, scale:int = 4):
        self.scale = scale
        
        options = ort.SessionOptions()
        options.enable_mem_pattern = True
        options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
        options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        
        availible_providers = ort.get_available_providers()
        logging.info(f'Available ONNX Runtime providers: {availible_providers}')
        
        providers_list = []
        if 'CUDAExecutionProvider' in availible_providers:
            providers_list.append('CUDAExecutionProvider')
        if 'DmlExecutionProvider' in availible_providers:
            providers_list.append('DmlExecutionProvider')
        providers_list.append('CPUExecutionProvider')
        
        try:
            self.session = ort.InferenceSession(model_path, sess_options=options, providers=providers_list)
        except Exception as e:
            logging.error(f'Failed to create ONNX Runtime session: {e}')
            raise RuntimeError(f'Failed to create ONNX Runtime session: {e}')
        
        active_provider = self.session.get_providers()[0]
        input_type = self.session.get_inputs()[0].type
        self.is_fp16 = 'float16' in input_type
        
        logging.info(f'ONNX Runtime session created with provider: {active_provider}, model precision: {"FP16" if self.is_fp16 else "FP32"}')
        
        self.vram_bytes = get_vram_limit()
        
        if active_provider == 'CUDAExecutionProvider':
            memory_coef = 5000 if self.is_fp16 else 12000
        elif active_provider == 'DmlExecutionProvider':
            memory_coef = 25000
        else:
            memory_coef = 30000
            
        pixel_limit = self.vram_bytes / memory_coef
        
        side = int(math.sqrt(pixel_limit))
        self.tile_size = max((side // 32) * 32, 256) # Кратность 32 для оптимизации, минимум 256 пикселей
        
        logging.info(f'VRAM: {self.vram_bytes / 1024**3:.2f} GB. Pixel limit: {int(pixel_limit)}. Tile size: {self.tile_size}x{self.tile_size}')
    
    def process_image(self, img:np.ndarray, tile_pad=10) -> np.ndarray:
        """
        Основной метод для обработки изображения с тайлингом.
        - img: входное изображение в формате BGR (uint8).
        - tile_pad: размер паддинга для каждого тайла (в пикселях).
        """
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w, c = img.shape
        
        if h <= self.tile_size and w <= self.tile_size:
            return self.process_patch(img)
        
        actual_tile_size = self.tile_size
        
        pad_h_mod = (actual_tile_size - (h % actual_tile_size)) % actual_tile_size
        pad_w_mod = (actual_tile_size - (w % actual_tile_size)) % actual_tile_size
        
        img_padded = cv2.copyMakeBorder(
            img, 
            tile_pad, tile_pad + pad_h_mod, 
            tile_pad, tile_pad + pad_w_mod, 
            cv2.BORDER_REFLECT_101
        )
        
        target_h = (h + pad_h_mod) * self.scale
        target_w = (w + pad_w_mod) * self.scale
        img_up = np.zeros((target_h, target_w, c), dtype=np.uint8)
        
        for y in range(0, h + pad_h_mod, actual_tile_size):
            for x in range(0, w + pad_w_mod, actual_tile_size):
                y_start = y
                y_end = y + actual_tile_size + (tile_pad * 2)
                x_start = x
                x_end = x + actual_tile_size + (tile_pad * 2)
                
                patch = img_padded[y_start:y_end, x_start:x_end, :]
                
                try:
                    chunk = self.process_patch(patch)
                except Exception as e:
                    logging.error(f'Error processing tile at ({y}:{x}): {e}')
                    h_patch, w_patch, _ = patch.shape
                    chunk = np.zeros((h_patch * self.scale, w_patch * self.scale, c), dtype=np.uint8)
                
                valid_start = tile_pad * self.scale
                valid_end = valid_start + (actual_tile_size * self.scale)
                
                chunk = chunk[valid_start:valid_end, valid_start:valid_end, :]
                
                dest_y = y * self.scale
                dest_x = x * self.scale
                
                h_c, w_c, _ = chunk.shape
                img_up[dest_y : dest_y + h_c, dest_x : dest_x + w_c, :] = chunk
                
        final_h = h * self.scale
        final_w = w * self.scale
        
        gc.collect()
        return img_up[:final_h, :final_w, :]
    
    def process_patch(self, patch:np.ndarray) -> np.ndarray:
        """
        Метод для обработки одного куска (без тайлинга).
        Возвращает сырой результат (с паддингами, в BGR формате).
        - patch: входной кусок изображения (RGB, uint8).
        """
        if self.is_fp16:
            img_blob = (patch.astype(np.float16) / 255.0)
        else:
            img_blob = (patch.astype(np.float32) / 255.0)
            
        img_blob = np.transpose(img_blob, (2, 0, 1))
        img_blob = np.expand_dims(img_blob, axis=0)
        img_blob = np.ascontiguousarray(img_blob)
            
        try:
            result = self.session.run(None, {'input': img_blob})[0]
        except Exception as e:
            logging.error(f'Error processing image: {e}')
            raise RuntimeError(f'Error processing image: {e}')
            
        result = result[0]
        result = np.clip(result, 0, 1)
        result = np.transpose(result, (1, 2, 0))
        
        result = (result * 255.0).round().astype(np.uint8)
        result = cv2.cvtColor(result, cv2.COLOR_RGB2BGR)
        
        return result