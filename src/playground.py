import cv2
import sys
import os

sys.path.append(os.getcwd())
from src.core.upscaler import Upscaler


upscaler = Upscaler(model_path='weights/RealESRGAN_x4plus.pth')

img = cv2.imread('src/image.png')

res = upscaler.process_image(img)

cv2.imwrite('result_class.png', res)