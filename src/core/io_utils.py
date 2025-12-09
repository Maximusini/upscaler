import cv2
import os
import numpy as np

def read_image(path):
    stream = np.fromfile(path, dtype=np.uint8)
    img = cv2.imdecode(stream, cv2.IMREAD_COLOR)
    return img

def save_image(path, img):
    ext = os.path.splitext(path)[1]
    success, buffer = cv2.imencode(ext, img)
    if success:
        buffer.tofile(path)