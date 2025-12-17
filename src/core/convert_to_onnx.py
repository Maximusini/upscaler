import torch
import sys
import os

sys.path.append(os.getcwd())
from src.core.model_arch import RRDBNet

model = RRDBNet(num_in_ch=3, 
                num_out_ch=3, 
                scale=2, 
                num_feat=64, 
                num_block=23, 
                num_grow_ch=32)

loadnet = torch.load('weights\RealESRGAN_x2plus.pth', map_location='cuda')

if 'params_ema' in loadnet:
    keyname = 'params_ema'
else:
    keyname = 'params'
            
model.load_state_dict(loadnet[keyname], strict=True)
model.eval()
dummy_input = torch.rand(1, 3, 64, 64)
torch.onnx.export(model, 
                  dummy_input, 
                  'weights\RealESRGAN_x2plus.onnx',
                  opset_version=11,
                  input_names = ['input'], 
                  output_names = ['output'],
                  dynamic_axes = {
                      'input': {
                          0: 'batch_size',
                          2: 'height',
                          3: 'width'
                          }, 
                      'output': {
                          0: 'batch_size',
                          2: 'height',
                          3: 'width'
                          }
                      }
                  )