import os
import cv2
from PySide6.QtCore import QThread, Signal
from src.core.upscaler import Upscaler
from src.core.video import VideoUpscaler
from src.core.io_utils import read_image, save_image

class UpscaleWorker(QThread):
    finished_signal = Signal()
    log_signal = Signal(str)
    progress_signal = Signal(int)
    stopped_signal = Signal()
    
    def __init__(self, input_path, model_choice, output_path):
        super().__init__()
        self.input_path = input_path
        self.model_choice = model_choice
        self.output_path = output_path
    
    def report_progress(self, percent):
        self.progress_signal.emit(percent)
        return not self.isInterruptionRequested()
        
    def run(self):
        self.log_signal.emit('Загрузка нейросети...')
        
        if self.model_choice == 'x2':
            model_path='weights/RealESRGAN_x2plus.pth'
            scale=2
        else:
            model_path='weights/RealESRGAN_x4plus.pth'
            scale=4
            
        root, ext = os.path.splitext(self.input_path)
        
        upscaler = Upscaler(model_path=model_path, scale=scale)
        self.log_signal.emit('Обработка...')
        
        if ext.lower() in ['.mp4', '.avi', '.mov']:
            video_upscaler = VideoUpscaler(upscaler)
            res = video_upscaler.process_video(self.input_path, self.output_path, self.report_progress)
        else:
            img = read_image(self.input_path)
            res = upscaler.process_image(img)
            save_image(self.output_path, res)
        
        if self.isInterruptionRequested():
            self.log_signal.emit('Обработка остановлена.')
            self.stopped_signal.emit()
        else:
            self.log_signal.emit('Обработка завершена! Можете сохранить файл.')
            self.finished_signal.emit()