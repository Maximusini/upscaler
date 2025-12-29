import numpy as np
import math
import cv2
import gc
import onnxruntime as ort
from src.core.system_utils import get_vram_limit

class Upscaler:
    def __init__(self, model_path:str, scale:int = 4):
        self.scale = scale
        
        self.vram_bytes = get_vram_limit()
        self.pixel_limit = self.vram_bytes / 30000
        
        print(f'VRAM: {self.vram_bytes / 1024**3:.2f} GB. Pixel limit: {int(self.pixel_limit)}')

        options = ort.SessionOptions()
        options.enable_mem_pattern = True
        options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
        options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
             
        self.session = ort.InferenceSession(model_path, sess_options=options, providers = ['DmlExecutionProvider', 'CPUExecutionProvider'])
        
        input_type = self.session.get_inputs()[0].type
        self.is_fp16 = 'float16' in input_type
        print(f"Model loaded. Precision: {'FP16' if self.is_fp16 else 'FP32'}")
    
    def process_image(self, img:np.ndarray, tile_size=0, tile_pad=10) -> np.ndarray:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w, c = img.shape
        
        if tile_size == 0:
            total_pixels = h * w
            if total_pixels <= self.pixel_limit:
                raw_size = max(h, w) + tile_pad * 2
                actual_tile_size = raw_size + (raw_size % 2)
            else:
                safe_pixels = self.pixel_limit
                side = int(math.sqrt(safe_pixels)) # Сторона квадрата, площадь которого равна лимиту
                actual_tile_size = side - (side % 2)
                print(f'Adaptive tile size: {actual_tile_size}')
        else:
            actual_tile_size = tile_size
        
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
                
                if self.is_fp16:
                    patch_blob = (patch.astype(np.float16) / 255.0)
                else:
                    patch_blob = (patch.astype(np.float32) / 255.0)
                
                patch_blob = np.transpose(patch_blob, (2, 0, 1))
                patch_blob = np.expand_dims(patch_blob, axis=0)
                patch_blob = np.ascontiguousarray(patch_blob)
                
                try:
                    result = self.session.run(None, {'input': patch_blob})[0]
                except Exception as e:
                    print(f"Error tile {y}:{x} - {e}")
                    continue
                
                result = result[0] 
                
                result = np.clip(result, 0, 1)
                result = np.transpose(result, (1, 2, 0))
                
                valid_start = tile_pad * self.scale
                valid_size = actual_tile_size * self.scale
                
                crop = result[valid_start : valid_start + valid_size, 
                              valid_start : valid_start + valid_size, :]
                
                crop = (crop * 255.0).round().astype(np.uint8)
                crop = cv2.cvtColor(crop, cv2.COLOR_RGB2BGR)
                
                dest_y = y * self.scale
                dest_x = x * self.scale
                
                h_c, w_c, _ = crop.shape
                img_up[dest_y : dest_y + h_c, dest_x : dest_x + w_c, :] = crop
                
        final_h = h * self.scale
        final_w = w * self.scale
        gc.collect()
        return img_up[:final_h, :final_w, :]