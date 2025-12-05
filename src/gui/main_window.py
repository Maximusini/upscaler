import os
from PySide6.QtWidgets import QWidget, QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox, QFileDialog, QProgressBar
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from src.gui.worker import UpscaleWorker
from src.gui.comparison_widget import ComparisonWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
        self.input_path = None
        self.output_path = None
    
    def setup_ui(self):
        self.setWindowTitle('Neural Upscaler')
        self.setMinimumSize(800, 600)
        
        widget = QWidget()
        self.setCentralWidget(widget)
        
        main_layout = QHBoxLayout()
        widget.setLayout(main_layout)
        
        controls_layout = QVBoxLayout()
        image_layout = QVBoxLayout()
        
        self.label_status = QLabel('Выберите файл для обработки')
        controls_layout.addWidget(self.label_status)
        
        self.btn_file = QPushButton('Выбрать файл')
        self.btn_file.clicked.connect(self.select_file)
        controls_layout.addWidget(self.btn_file)
        
        self.combo_model = QComboBox()
        self.combo_model.addItems(['x2', 'x4'])
        controls_layout.addWidget(self.combo_model)
        
        self.btn_start = QPushButton('Начать')
        self.btn_start.setEnabled(False)
        self.btn_start.clicked.connect(self.start_processing)
        controls_layout.addWidget(self.btn_start)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        controls_layout.addWidget(self.progress_bar)
        
        controls_layout.addStretch()
        
        self.image = ComparisonWidget()
        self.image.setStyleSheet('border: 2px dashed grey;')
        image_layout.addWidget(self.image)
        
        main_layout.addLayout(controls_layout)
        main_layout.addLayout(image_layout)
        main_layout.setStretch(0, 1)
        main_layout.setStretch(1, 3)
    

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Выберите файл', '', 'Images & Video (*.jpg *.png *.mp4)')
        root, ext = os.path.splitext(file_path)
        if file_path:
            if ext.lower() in ['.mp4', '.avi', '.mov']:
                self.label_status.setText('Видео выбрано (предпросмотр недоступен)')
            else:
                self.input_path = file_path
                self.image.set_images(self.input_path, None)
                
                file_name = os.path.basename(file_path)
                self.label_status.setText(f'Выбран файл: {file_name}')
                self.btn_start.setEnabled(True)
            
    def update_status(self, text):
        self.label_status.setText(text)
        
    def process_finished(self):
        self.btn_start.setEnabled(True)
        if self.output_path and not self.output_path.endswith('.mp4'):
            self.image.set_images(self.input_path, self.output_path)
    
    def update_progress(self, percent):
        self.progress_bar.setValue(percent)
    
    def start_processing(self):
        self.btn_start.setEnabled(False)
        self.progress_bar.setValue(0)
        
        root, ext = os.path.splitext(self.input_path)
        suggested_path = f'{root}_upscaled{ext}'
        
        file_path, _ = QFileDialog.getSaveFileName(self, 'Сохранить результат', suggested_path, 'Images (*.png *.jpg);;Video (*.mp4)')
        
        if not file_path:
            self.btn_start.setEnabled(True)
            return
        else:
            self.output_path = file_path
        
        input_path = self.input_path
        model_choice = self.combo_model.currentText()
        
        self.worker = UpscaleWorker(input_path, model_choice, self.output_path)
        
        self.worker.log_signal.connect(self.update_status)
        self.worker.finished_signal.connect(self.process_finished)
        self.worker.progress_signal.connect(self.update_progress)
        
        self.worker.start()