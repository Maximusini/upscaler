import os
import shutil
from PySide6.QtWidgets import QWidget, QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, \
    QComboBox, QFileDialog, QProgressBar, QListWidget, QListWidgetItem, QCheckBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from src.gui.worker import UpscaleWorker
from src.gui.comparison_widget import ComparisonWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.VIDEO_EXTS = {'.mp4', '.avi', '.mov', '.mkv', '.webm'}
        self.IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}
        
        self.setup_ui()
        
        self.input_path = None
        self.output_path = None
        self.temp_output_path = None
    
    def setup_ui(self):
        self.setWindowTitle('Neural Upscaler')
        self.setMinimumSize(800, 600)
        
        widget = QWidget()
        self.setCentralWidget(widget)
        
        main_layout = QHBoxLayout()
        widget.setLayout(main_layout)
        
        controls_layout = QVBoxLayout()
        image_layout = QVBoxLayout()
        
        self.file_list = QListWidget()
        self.file_list.itemClicked.connect(self.on_file_clicked)
        controls_layout.addWidget(self.file_list)
        
        self.btn_file = QPushButton('Выбрать файл')
        self.btn_file.clicked.connect(self.select_file)
        controls_layout.addWidget(self.btn_file)
        
        self.combo_model = QComboBox()
        self.combo_model.addItems(['x2', 'x4'])
        controls_layout.addWidget(self.combo_model)
        
        self.check_batch = QCheckBox('Обработать все файлы сразу')
        controls_layout.addWidget(self.check_batch)
        
        self.btn_start = QPushButton('Начать')
        self.btn_start.setEnabled(False)
        self.btn_start.clicked.connect(self.start_processing)
        controls_layout.addWidget(self.btn_start)
        
        self.btn_save = QPushButton('Сохранить результат')
        self.btn_save.setEnabled(False)
        self.btn_save.clicked.connect(self.save_result)
        controls_layout.addWidget(self.btn_save)
        
        self.btn_stop = QPushButton('Стоп')
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_processing)
        controls_layout.addWidget(self.btn_stop)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        controls_layout.addWidget(self.progress_bar)
        
        self.label_status = QLabel('Выберите файл для обработки')
        controls_layout.addWidget(self.label_status)
        
        controls_layout.addStretch()
        
        self.image = ComparisonWidget()
        self.image.file_dropped.connect(self.load_file)
        self.image.setStyleSheet('border: 2px dashed grey;')
        image_layout.addWidget(self.image)
        
        main_layout.addLayout(controls_layout)
        main_layout.addLayout(image_layout)
        main_layout.setStretch(0, 1)
        main_layout.setStretch(1, 3)
                
    def load_file(self, file_path):
        ext = os.path.splitext(file_path)[1].lower()
        if file_path:
            self.btn_save.setEnabled(False)
            self.input_path = file_path
            if ext in self.VIDEO_EXTS | self.IMAGE_EXTS:
                file_name = os.path.basename(file_path)
                item = QListWidgetItem(file_name)
                item.setData(Qt.UserRole, file_path)
                self.file_list.addItem(item)
                self.file_list.setCurrentItem(item)
                self.on_file_clicked(item)
            else:
                self.label_status.setText('Ошибка. Данный формат не поддерживается.')
                self.btn_start.setEnabled(False)
                
    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Выберите файл', '', 'Images & Video (*.jpg *.png *.mp4)')
        self.load_file(file_path)
            
    def update_status(self, text):
        self.label_status.setText(text)
    
    def update_progress(self, percent):
        self.progress_bar.setValue(percent)
    
    def start_processing(self):
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.progress_bar.setValue(0)
        
        files_to_process = []
        if self.check_batch.isChecked():
            for i in range(self.file_list.count()):
                item = self.file_list.item(i)
                path = item.data(Qt.UserRole)
                files_to_process.append(path)
                
            if not files_to_process:
                self.label_status.setText('Нет файлов для обработки.')
                self.btn_start.setEnabled(True)
                self.btn_stop.setEnabled(False)
                return
            
            self.temp_output_path = os.path.join(os.getcwd(), 'temp_batch_folder')
            if os.path.exists(self.temp_output_path):
                shutil.rmtree(self.temp_output_path)
            os.makedirs(self.temp_output_path)
            
        else:
            if not self.input_path:
                self.label_status.setText('Файл не выбран.')
                self.btn_start.setEnabled(True)
                self.btn_stop.setEnabled(False)
                return
            
            files_to_process = [self.input_path]
            ext = os.path.splitext(files_to_process[0])
            self.temp_output_path = os.path.join(os.getcwd(), f'temp{ext}')
            if os.path.exists(self.temp_output_path):
                os.remove(self.temp_output_path)
        
        model_choice = self.combo_model.currentText()
        
        self.worker = UpscaleWorker(files_to_process, model_choice, self.temp_output_path)
        
        self.worker.log_signal.connect(self.update_status)
        self.worker.finished_signal.connect(self.process_finished)
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.stopped_signal.connect(self.process_stopped)
        
        self.worker.start()
        
    def process_finished(self):
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.btn_save.setEnabled(True)
        if self.temp_output_path:
            ext = os.path.splitext(self.temp_output_path)[1].lower()
            if ext not in self.VIDEO_EXTS:
                self.image.set_images(self.input_path, self.temp_output_path)
            
    def stop_processing(self):
        self.worker.requestInterruption()
        self.label_status.setText('Останавливаю...')
        
    def process_stopped(self):
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.btn_save.setEnabled(False)
        self.label_status.setText('Отменено.')
        
    def save_result(self):        
        if os.path.isdir(self.temp_output_path):
            suggested_path = 'upscaled_batch'
            archive_path, _ = QFileDialog.getSaveFileName(self, 'Сохранить архив', suggested_path, 'ZIP Archive (*.zip)')
            if archive_path:
                self.label_status.setText('Упаковка архива...')
                root = os.path.splitext(archive_path)[0]
                shutil.make_archive(root, 'zip', self.temp_output_path)
                self.label_status.setText('Архив успешно сохранён!')
                
        else:
            root, ext = os.path.splitext(self.input_path)
            suggested_path = f'{root}_upscaled{ext}'
            file_path, _ = QFileDialog.getSaveFileName(self, 'Сохранить результат', suggested_path, 'Images (*.png *.jpg);;Video (*.mp4)')
            
            if file_path:
                shutil.copy2(self.temp_output_path, file_path)
                self.label_status.setText('Файл успешно сохранён')
            
    def closeEvent(self, event):
        if self.temp_output_path and os.path.exists(self.temp_output_path):
            os.remove(self.temp_output_path)
        event.accept()

    def on_file_clicked(self, item):
        file_path = item.data(Qt.UserRole)
        self.input_path = file_path
        self.btn_save.setEnabled(False)
        ext = os.path.splitext(self.input_path)[1].lower()
        
        if ext in self.VIDEO_EXTS:
            self.image.set_images(file_path, None)
            self.label_status.setText(f'Выбрано видео: {os.path.basename(self.input_path)}. Предпросмотр не доступен.')
            self.btn_start.setEnabled(True)
            self.image.set_images("", None) 
        elif ext in self.IMAGE_EXTS:
            self.image.set_images(file_path, None)
            self.label_status.setText(f'Выбрано изображение: {os.path.basename(file_path)}.')
            self.btn_start.setEnabled(True)