import torch
import numpy as np

from src.core.model_arch import RRDBNet


class Upscaler:
    def __init__(self, model_path:str, device:str = 'cuda', scale:int = 4):
        self.device = device
        self.scale = scale
        
        self.model = RRDBNet(num_in_ch=3, 
                        num_out_ch=3, 
                        scale=scale, 
                        num_feat=64, 
                        num_block=23, 
                        num_grow_ch=32)
        
        loadnet = torch.load(model_path, map_location=device)
        
        if 'params_ema' in loadnet:
            keyname = 'params_ema'
        else:
            keyname = 'params'
            
        self.model.load_state_dict(loadnet[keyname], strict=True)
        self.model.eval()
        self.model.to(self.device)
    
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
                img_patch = img_patch.astype(np.float32) / 255.0
                img_patch = np.transpose(img_patch[:, :, [2, 1, 0]], (2, 0, 1))
                img_patch = torch.from_numpy(img_patch).float()
                img_patch = img_patch.unsqueeze(0).to(self.device)
                
                with torch.no_grad():
                    output = self.model(img_patch)
                
                output_patch = output.data.squeeze().float().cpu().clamp_(0, 1).numpy()
                output_patch = np.transpose(output_patch[[2, 1, 0], :, :], (1, 2, 0))
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
        