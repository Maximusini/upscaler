import logging
import os
from PySide6.QtCore import QThread, Signal
from src.core.path_utils import get_resource_path
from src.core.upscaler import Upscaler
from src.core.video_pipeline import VideoUpscaleWorker
from src.core.io_utils import read_image, save_image

class UpscaleWorker(QThread):
    finished_signal = Signal()
    log_signal = Signal(str)
    progress_signal = Signal(int)
    stopped_signal = Signal()
    
    def __init__(self, input_files, model_choice, output_path, save_format, work_dir):
        super().__init__()
        self.input_files = input_files
        self.model_choice = model_choice
        self.output_path = output_path
        self.save_format = save_format
        self.work_dir = work_dir
        
        self.current_pipeline = None
    
    def report_progress(self, percent):
        self.progress_signal.emit(percent)
        if self.isInterruptionRequested():
            return False
        return True
        
    def run(self):
        self.log_signal.emit('Загрузка нейросети...')
        
        if self.model_choice == 'x2':
            model_path = get_resource_path('weights/RealESRGAN_x2plus_fp16.onnx')
            scale = 2
        else:
            model_path = get_resource_path('weights/RealESRGAN_x4plus_fp16.onnx')
            scale = 4
        try:
            upscaler = Upscaler(model_path=model_path, scale=scale)
        except Exception as e:
            self.log_signal.emit(f'Ошибка загрузки нейросети: {e}')
            logging.error(f'Error loading model: {e}')
            self.stopped_signal.emit()
            return
            
        self.log_signal.emit('Обработка...')
        
        total_files = len(self.input_files)
        
        for i, file_path in enumerate(self.input_files):
            if self.isInterruptionRequested():
                break
            
            current_file_output = self.output_path
            
            file_name_full = os.path.basename(file_path)
            file_name_only = os.path.splitext(file_name_full)[0]
            src_ext = os.path.splitext(file_name_full)[1].lower()
                                
            self.log_signal.emit(f'Файл {i + 1} из {total_files}: {file_name_full}')
            
            self.progress_signal.emit(0)
            
            if self.save_format == 'Auto':
                ext = src_ext
            else:
                ext = f'.{self.save_format.lower()}'
            
            if total_files > 1:
                if os.path.isdir(self.output_path):
                    target_dir = self.output_path
                else:
                    target_dir = os.path.dirname(self.output_path)
                    
                save_name = f'{file_name_only}_upscaled{ext}'
                current_file_output = os.path.join(target_dir, save_name)
            else:
                if os.path.isdir(self.output_path):
                    save_name = f'{file_name_only}_upscaled{ext}'
                    current_file_output = os.path.join(self.output_path, save_name)
                else:
                    current_file_output = self.output_path
                
            if src_ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
                if os.path.splitext(current_file_output)[1].lower() not in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
                    current_file_output = os.path.splitext(current_file_output)[0] + '.mp4'
                
                self.current_pipeline = VideoUpscaleWorker(upscaler)
                
                try:
                    run = self.current_pipeline.process_video(
                        input_path=file_path, 
                        output_path=current_file_output, 
                        work_dir=self.work_dir, 
                        progress=self.report_progress
                    )
                    
                    if run is False:
                        self.log_signal.emit('Обработка видео была остановлена пользователем.')
                        break
                except Exception as e:
                    self.log_signal.emit(f'Ошибка при обработке видео: {e}')
                    logging.error(f'Error processing video {file_path}: {e}')
                
                self.current_pipeline = None
                
            elif src_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.webp']:
                try:
                    img = read_image(file_path)
                    if img is not None:
                        try:
                            res = upscaler.process_image(img, check_interrupt=self.isInterruptionRequested)
                            save_image(current_file_output, res)
                        except InterruptedError:
                            self.log_signal.emit('Обработка изображения была остановлена пользователем.')
                            break
                        
                        self.progress_signal.emit(100)
                    else:
                        self.log_signal.emit(f'Не удалось прочитать изображение: {file_path}')
                        logging.error(f'Failed to read image: {file_path}')
                except Exception as e:
                    self.log_signal.emit(f'Ошибка при обработке изображения: {e}')
                    logging.error(f'Error processing image {file_path}: {e}')                
                        
        if self.isInterruptionRequested():
            self.log_signal.emit('Обработка остановлена пользователем.')
            self.stopped_signal.emit()
        else:
            self.progress_signal.emit(100)
            self.log_signal.emit('Готово! Все файлы обработаны.')
            self.finished_signal.emit()
    
    def requestInterruption(self):
        super().requestInterruption()
        if self.current_pipeline:
            self.current_pipeline.stop_event.set()