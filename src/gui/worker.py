import os
from PySide6.QtCore import QThread, Signal
from src.core.path_utils import get_resource_path
from src.core.upscaler import Upscaler
from src.core.video import VideoUpscaler
from src.core.io_utils import read_image, save_image

class UpscaleWorker(QThread):
    finished_signal = Signal()
    log_signal = Signal(str)
    progress_signal = Signal(int)
    stopped_signal = Signal()
    
    def __init__(self, input_files, model_choice, output_path, save_format):
        super().__init__()
        self.input_files = input_files
        self.model_choice = model_choice
        self.output_path = output_path
        self.save_format = save_format
    
    def report_progress(self, percent):
        self.progress_signal.emit(percent)
        return not self.isInterruptionRequested()
        
    def run(self):
        self.log_signal.emit('Загрузка нейросети...')
        
        if self.model_choice == 'x2':
            model_path = get_resource_path('weights/RealESRGAN_x2plus_fp16.onnx')
            scale = 2
        else:
            model_path = get_resource_path('weights/RealESRGAN_x4plus_fp16.onnx')
            scale = 4
        
        upscaler = Upscaler(model_path=model_path, scale=scale)
        self.log_signal.emit('Обработка...')
        
        for i, file_path in enumerate(self.input_files):
            src_ext = os.path.splitext(file_path)[1].lower()
            if self.isInterruptionRequested():
                break
            
            self.log_signal.emit(f'Файл {i + 1} из {len(self.input_files)}: {os.path.basename(file_path)}')
            current_progress = int((i / len(self.input_files)) * 100)
            self.progress_signal.emit(current_progress)
            
            if self.save_format == 'Auto':
                ext = os.path.splitext(file_path)[1]
            else:
                ext = f'.{self.save_format.lower()}'
            
            if os.path.isdir(self.output_path):
                file_name = os.path.splitext(os.path.basename(file_path))[0]
                file = f'{file_name}_upscaled{ext}'
                current_output = os.path.join(self.output_path, file)
                
            else:
                current_output = self.output_path
                
            if src_ext.lower() in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
                current_output_path = os.path.splitext(current_output)[0]
                final_video_path  = f'{current_output_path}{src_ext}'
                video_upscaler = VideoUpscaler(upscaler)
                video_upscaler.process_video(file_path, final_video_path, self.report_progress)
                
            elif src_ext.lower() in ['.jpg', '.jpeg', '.png', '.bmp', '.webp']:
                img = read_image(file_path)
                res = upscaler.process_image(img)
                save_image(current_output, res)
                
        self.progress_signal.emit(100)
        
        if self.isInterruptionRequested():
            self.log_signal.emit('Обработка остановлена.')
            self.stopped_signal.emit()
        else:
            self.log_signal.emit('Готово! Все файлы обработаны.')
            self.finished_signal.emit()