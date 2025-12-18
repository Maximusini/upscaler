import onnx
import sys
import os
from onnxconverter_common import float16
sys.path.append(os.getcwd())

def convert_model(input_path:str, output_path:str):
    model = onnx.load(input_path)
    model_fp16 = float16.convert_float_to_float16(model)
    onnx.save(model_fp16, output_path)
    
convert_model('weights/RealESRGAN_x2plus.onnx', 'weights/RealESRGAN_x2plus_fp16.onnx')
convert_model('weights/RealESRGAN_x4plus.onnx', 'weights/RealESRGAN_x4plus_fp16.onnx')