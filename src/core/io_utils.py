import cv2
import os
import numpy as np

def read_image(path):
    stream = np.fromfile(path, dtype=np.uint8)
    img = cv2.imdecode(stream, cv2.IMREAD_COLOR)
    return img

def save_image(path, img):
    ext = os.path.splitext(path)[1].lower()
    
    params = []
    if ext in ['.jpg', '.jpeg']:
        params = [cv2.IMWRITE_JPEG_QUALITY, 100]
    elif ext == '.webp':
        params = [cv2.IMWRITE_WEBP_QUALITY, 100]
        
    success, buffer = cv2.imencode(ext, img, params)
    if success:
        buffer.tofile(path)