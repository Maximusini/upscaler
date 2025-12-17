import numpy as np
import cv2
import onnxruntime as ort


class Upscaler:
    def __init__(self, model_path:str, scale:int = 4):
        self.scale = scale
        
        self.session = ort.InferenceSession(model_path, providers = ['CUDAExecutionProvider', 'CPUExecutionProvider'])
    
    def process_image(self, img:np.ndarray, tile_size=400, tile_pad=10) -> np.ndarray:
        h, w, c = img.shape
        img_up = np.zeros((h * self.scale, w * self.scale, c), dtype=np.uint8)
        
        for i in range(0, h, tile_size):
            for j in range(0, w, tile_size):
                y_start = max(0, i - tile_pad)
                y_end = min(h, i + tile_pad + tile_size)
                x_start = max(0, j - tile_pad)
                x_end = min(w, j + tile_pad + tile_size)
                
                img_patch = img[y_start:y_end, x_start:x_end, :]
                
                pad_h = 0
                pad_w = 0
                h_patch, w_patch = img_patch.shape[:2]
                
                if h_patch % 2 != 0:
                    pad_h = 1
                if w_patch % 2 != 0:
                    pad_w = 1
                
                if pad_h > 0 or pad_w > 0:
                    img_patch = cv2.copyMakeBorder(img_patch, 0, pad_h, 0, pad_w, cv2.BORDER_REFLECT_101)
                img_patch = img_patch.astype(np.float32) / 255.0
                img_patch = np.transpose(img_patch[:, :, [2, 1, 0]], (2, 0, 1))
                img_patch = np.expand_dims(img_patch, axis=0) 

                output_patch = self.session.run(None, {'input': img_patch})[0]
                output_patch = np.squeeze(output_patch)
                output_patch = np.clip(output_patch, 0, 1)
                output_patch = np.transpose(output_patch[:, :, [2, 1, 0]], (1, 2, 0))
                output_patch = (output_patch * 255.0).round().astype(np.uint8)
                
                start_y_in_patch = (i - y_start) * self.scale
                start_x_in_patch = (j - x_start) * self.scale
                
                len_h = min(tile_size, h - i) * self.scale
                len_w = min(tile_size, w - j) * self.scale
                
                result_valid = output_patch[
                    start_y_in_patch : start_y_in_patch + len_h,
                    start_x_in_patch : start_x_in_patch + len_w, 
                    :]
                final_y = i * self.scale
                final_x = j * self.scale
                img_up[final_y:final_y + len_h, final_x:final_x + len_w, :] = result_valid
                
        return img_up
        