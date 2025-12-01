import os
import cv2
from PySide6.QtWidgets import QWidget, QMainWindow, QVBoxLayout, QPushButton, QLabel, QComboBox, QFileDialog

from src.core.upscaler import Upscaler
from src.core.video import VideoUpscaler

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
        self.input_path = None
    
    def setup_ui(self):
        self.setWindowTitle('Neural Upscaler')
        self.setMinimumSize(800, 600)
        
        widget = QWidget()
        self.setCentralWidget(widget)
        
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        self.label_status = QLabel('Выберите файл для обработки')
        layout.addWidget(self.label_status)
        
        self.btn_file = QPushButton('Выбрать файл')
        self.btn_file.clicked.connect(self.select_file)
        layout.addWidget(self.btn_file)
        
        self.combo_model = QComboBox()
        self.combo_model.addItems(['x2', 'x4'])
        layout.addWidget(self.combo_model)
        
        self.btn_start = QPushButton('Начать')
        self.btn_start.setEnabled(False)
        self.btn_start.clicked.connect(self.start_processing)
        layout.addWidget(self.btn_start)
    
    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Выберите файл', '', 'Images & Video (*.jpg *.png *.mp4)')
        if file_path:
            self.input_path = file_path
            
            file_name = os.path.basename(file_path)
            self.label_status.setText(f'Выбран файл: {file_name}')
            self.btn_start.setEnabled(True)
            
    def start_processing(self):
        self.btn_start.setEnabled(False)
        self.label_status.setText('Обработка...')
        
        model_choice = self.combo_model.currentText()
        if model_choice == 'x2':
            model_path='weights/RealESRGAN_x2plus.pth'
            scale=2
        else:
            model_path='weights/RealESRGAN_x4plus.pth'
            scale=4
        
        root, ext = os.path.splitext(self.input_path)
        output_path = f'{root}_upscaled{ext}'
        
        upscaler = Upscaler(model_path=model_path, scale=scale)
        
        if ext.lower() in ['.mp4', '.avi', '.mov']:
            video_upscaler = VideoUpscaler(upscaler)
            res = video_upscaler.process_video(input_path=self.input_path, output_path=output_path)
        else:
            img = cv2.imread(self.input_path)
            res = upscaler.process_image(img)
            cv2.imwrite(output_path, res)
        
        self.label_status.setText(f'Готово! Сохранено: {os.path.basename(output_path)}')
        self.btn_start.setEnabled(True)