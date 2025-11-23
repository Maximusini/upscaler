import cv2
import sys
import os

sys.path.append(os.getcwd())
from src.core.video import VideoUpscaler
from src.core.upscaler import Upscaler

upscaler = Upscaler(model_path='weights/RealESRGAN_x2plus.pth', scale = 2)
video_upscaler = VideoUpscaler(upscaler)

res = video_upscaler.process_video('video.mp4', 'output_video.mp4')