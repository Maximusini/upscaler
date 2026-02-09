import os
import shutil
import tempfile
from PySide6.QtWidgets import QWidget, QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, \
    QComboBox, QFileDialog, QProgressBar, QListWidget, QListWidgetItem, QCheckBox, QGroupBox, \
    QTabWidget, QStyle
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from src.core.config import ConfigManager
from src.gui.worker import UpscaleWorker
from src.gui.comparison_widget import ComparisonWidget
from src.core.system_utils import get_gpu_info, check_ffmpeg

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.VIDEO_EXTS = {'.mp4', '.avi', '.mov', '.mkv', '.webm'}
        self.IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}
        
        self.setup_ui()
        
        self.input_path = ""
        self.output_path = ""
        self.temp_output_path = ""
        
        system_temp = tempfile.gettempdir()
        self.work_dir = os.path.join(system_temp, 'NeuralUpscaler_work')
        
        self.config_manager = ConfigManager()
        self.settings = self.config_manager.load_config()
        self.apply_settings()
    
    def setup_ui(self):
        self.setWindowTitle('Neural Upscaler')
        self.setMinimumSize(900, 700)
        
        widget = QWidget()
        self.setCentralWidget(widget)
        main_layout = QHBoxLayout()
        widget.setLayout(main_layout)
        
        controls_layout = QVBoxLayout()
        image_layout = QVBoxLayout()
        
        self.tabs = QTabWidget()
        self.create_main_tab()
        self.create_info_tab()
        controls_layout.addWidget(self.tabs)
        
        self.create_actions_group()
        controls_layout.addWidget(self.actions_group)
        
        self.label_status = QLabel('Готов к работе')
        self.label_status.setStyleSheet("color: #888;")
        controls_layout.addWidget(self.label_status)
        
        self.image = ComparisonWidget()
        self.image.file_dropped.connect(self.load_file)
        self.image.setStyleSheet('border: 2px dashed #444; background-color: #222;')
        image_layout.addWidget(self.image)
        
        main_layout.addLayout(controls_layout)
        main_layout.addLayout(image_layout)
        main_layout.setStretch(0, 35)
        main_layout.setStretch(1, 65)
        
    def create_main_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        self.files_group = QGroupBox('Файлы')
        files_layout = QVBoxLayout()
        
        files_layout.addWidget(QLabel('Список файлов:'))
        self.file_list = QListWidget()
        self.file_list.itemClicked.connect(self.on_file_clicked)
        files_layout.addWidget(self.file_list)
        
        self.btn_file = QPushButton('Добавить файлы...')
        self.btn_file.clicked.connect(self.select_file)
        files_layout.addWidget(self.btn_file)
        
        self.check_batch = QCheckBox('Обработать все файлы')
        files_layout.addWidget(self.check_batch)
        
        self.files_group.setLayout(files_layout)
        layout.addWidget(self.files_group)

        self.params_group = QGroupBox('Настройки')
        params_layout = QVBoxLayout()
        
        params_layout.addWidget(QLabel('Модель нейросети:'))
        self.combo_model = QComboBox()
        self.combo_model.addItems(['x2', 'x4'])
        params_layout.addWidget(self.combo_model)
        
        params_layout.addWidget(QLabel('Формат сохранения:'))
        self.combo_format = QComboBox()
        self.combo_format.addItems(['Auto', 'PNG', 'JPG', 'WEBP'])
        params_layout.addWidget(self.combo_format)
        
        self.params_group.setLayout(params_layout)
        layout.addWidget(self.params_group)

        layout.addStretch()

        self.tabs.addTab(tab, 'Главная')
        
    def create_info_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        gpu_info = get_gpu_info()
        lbl_gpu = QLabel(gpu_info)
        if "GPU" in gpu_info:
            lbl_gpu.setStyleSheet("color: green; font-weight: bold;") # Зеленый
        else:
            lbl_gpu.setStyleSheet("color: red; font-weight: bold;") # Красный

        has_ffmpeg = check_ffmpeg()
        ffmpeg_text = "FFmpeg: Установлен (Видео доступно)" if has_ffmpeg else "FFmpeg: Не найден (Только фото)"
        lbl_ffmpeg = QLabel(ffmpeg_text)
        color = "green" if has_ffmpeg else "red"
        lbl_ffmpeg.setStyleSheet(f"color: {color}; font-weight: bold;")

        lbl_ver = QLabel("Версия: v1.0.0 Release")
        lbl_ver.setStyleSheet("color: #888; margin-top: 20px;")
        
        layout.addWidget(lbl_gpu)
        layout.addWidget(lbl_ffmpeg)
        layout.addWidget(lbl_ver)
        layout.addStretch()
        
        self.tabs.addTab(tab, "Система")

    def create_actions_group(self):
        self.actions_group = QGroupBox('Управление')
        layout = QVBoxLayout()
        
        self.btn_start = QPushButton('НАЧАТЬ ОБРАБОТКУ')
        self.btn_start.setMinimumHeight(40)
        self.btn_start.setEnabled(False)
        self.btn_start.clicked.connect(self.start_processing)
        layout.addWidget(self.btn_start)

        btns_layout = QHBoxLayout()
        
        self.btn_save = QPushButton('Сохранить')
        self.btn_save.setEnabled(False)
        self.btn_save.clicked.connect(self.save_result)
        btns_layout.addWidget(self.btn_save)
        
        self.btn_stop = QPushButton('Стоп')
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_processing)
        btns_layout.addWidget(self.btn_stop)
        
        layout.addLayout(btns_layout)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(10)
        layout.addWidget(self.progress_bar)
        
        self.actions_group.setLayout(layout)
        
    def cleanup_temp(self):
        if os.path.exists(self.work_dir):
            shutil.rmtree(self.work_dir)
                
    def load_file(self, file_path):
        ext = os.path.splitext(file_path)[1].lower()
        if file_path:
            self.btn_save.setEnabled(False)
            self.input_path = file_path
            if ext in (self.VIDEO_EXTS | self.IMAGE_EXTS):
                file_name = os.path.basename(file_path)
                item = QListWidgetItem(file_name)
                item.setData(Qt.ItemDataRole.UserRole, file_path)
                self.file_list.addItem(item)
                
                if self.file_list.count() == 1:
                    self.file_list.setCurrentItem(item)
                    self.on_file_clicked(item)
                
                widget = QWidget()
                layout = QHBoxLayout(widget)
                layout.setContentsMargins(5, 2, 5, 2)
                label = QLabel(os.path.basename(file_path))
                btn_del = QPushButton()
                btn_del.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TitleBarCloseButton))
                btn_del.setFlat(True)
                btn_del.setFixedSize(24, 24)
                btn_del.setStyleSheet('QPushButton:hover { background-color: red; border-radius: 4px; }')
                layout.addWidget(label)
                layout.addStretch()
                layout.addWidget(btn_del)
                
                btn_del.clicked.connect(lambda: self.remove_item(item))
                self.file_list.setItemWidget(item, widget)
            else:
                self.label_status.setText('Ошибка. Данный формат не поддерживается.')
                self.btn_start.setEnabled(False)
                
    def remove_item(self, item):
        row = self.file_list.row(item)
        self.file_list.takeItem(row)
        
        if self.file_list.count() == 0:
            self.image.set_images("", "")
            self.btn_start.setEnabled(False)
            self.label_status.setText("Список пуст")
                
    def select_file(self):
        start_dir = self.settings.get('last_path', '')
            
        file_paths, _ = QFileDialog.getOpenFileNames(self, 'Выберите файлы', start_dir, 'Images & Video (*.jpg *.png *.mp4)')
        if file_paths:
            current_dir = os.path.dirname(file_paths[0])
            self.settings['last_path'] = current_dir
            
            for file_path in file_paths:              
                self.load_file(file_path)
            
    def update_status(self, text):
        self.label_status.setText(text)
    
    def update_progress(self, percent):
        self.progress_bar.setValue(percent)
    
    def start_processing(self):
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.progress_bar.setValue(0)

        
        self.cleanup_temp()
        os.makedirs(self.work_dir, exist_ok=True)

        save_format = self.combo_format.currentText()        
        files_to_process = []
        if self.check_batch.isChecked():
            for i in range(self.file_list.count()):
                item = self.file_list.item(i)
                path = item.data(Qt.ItemDataRole.UserRole)
                files_to_process.append(path)
                
            if not files_to_process:
                self.label_status.setText('Нет файлов для обработки.')
                self.btn_start.setEnabled(True)
                self.btn_stop.setEnabled(False)
                return
            
            self.temp_output_path = os.path.join(self.work_dir, 'batch_results')
            os.makedirs(self.temp_output_path, exist_ok=True)
            
        else:
            if not self.input_path:
                self.label_status.setText('Файл не выбран.')
                self.btn_start.setEnabled(True)
                self.btn_stop.setEnabled(False)
                return
            
            files_to_process = [self.input_path]
            src_ext = os.path.splitext(self.input_path)[1].lower()
            if src_ext in self.VIDEO_EXTS:
                ext = src_ext
            elif save_format == 'Auto':
                ext = src_ext
            else:
                ext = f'.{save_format.lower()}'
            self.temp_output_path = os.path.join(self.work_dir, f'result{ext}')
        
        model_choice = self.combo_model.currentText()
        
        self.worker = UpscaleWorker(files_to_process, model_choice, self.temp_output_path, save_format, self.work_dir)
        
        self.worker.log_signal.connect(self.update_status)
        self.worker.finished_signal.connect(self.process_finished)
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.stopped_signal.connect(self.process_stopped)
        
        self.worker.start()
        
    def process_finished(self):
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.btn_save.setEnabled(True)
        
        if not self.temp_output_path:
            return
        
        if os.path.isdir(self.temp_output_path):
            current_item = self.file_list.currentItem()
            if current_item:
                self.on_file_clicked(current_item)
        
        elif os.path.isfile(self.temp_output_path):
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
            root = os.path.splitext(self.input_path)[0]
            result_ext = os.path.splitext(self.temp_output_path)[1]
            
            suggested_path = f'{root}_upscaled{result_ext}'

            file_path, _ = QFileDialog.getSaveFileName(self, 'Сохранить результат', suggested_path, 'Images (*.png *.jpg *.webp)')
            
            if file_path:
                shutil.copy2(self.temp_output_path, file_path)
                self.label_status.setText('Файл успешно сохранён')
            
    def closeEvent(self, event):
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.requestInterruption()
            self.worker.wait(2000)
            if self.worker.isRunning():
                self.worker.terminate()
                
        if self.temp_output_path and os.path.exists(self.temp_output_path):
            if os.path.isdir(self.temp_output_path):
                shutil.rmtree(self.temp_output_path)
            else:
                os.remove(self.temp_output_path)
        
        self.settings['model'] = self.combo_model.currentText()
        self.settings['format'] = self.combo_format.currentText()
        self.config_manager.save_config(self.settings)
        
        self.cleanup_temp()
        event.accept()

    def on_file_clicked(self, item):
        file_path = item.data(Qt.ItemDataRole.UserRole)
        self.input_path = file_path
        
        if self.temp_output_path and os.path.isdir(self.temp_output_path):
            self.btn_save.setEnabled(True)
        else:
            self.btn_save.setEnabled(False)
            
        ext = os.path.splitext(self.input_path)[1].lower()
        
        if ext in self.VIDEO_EXTS:
            self.label_status.setText(f'Выбрано видео: {os.path.basename(self.input_path)}. Предпросмотр не доступен.')
            self.btn_start.setEnabled(True)
            self.image.set_images("", "") 
            
        elif ext in self.IMAGE_EXTS:
            self.label_status.setText(f'Выбрано изображение: {os.path.basename(file_path)}.')
            self.btn_start.setEnabled(True)
            
            output_to_show = None
            
            if self.temp_output_path and os.path.isdir(self.temp_output_path):
                file_name = os.path.splitext(os.path.basename(file_path))[0]
                possible_exts = [ext, '.png', '.jpg', '.jpeg', '.webp']
                
                for ext in possible_exts:
                    expected_name = f'{file_name}_upscaled{ext}'
                    expected_path = os.path.join(self.temp_output_path, expected_name)
                
                    if os.path.exists(expected_path):
                        output_to_show = expected_path
                        break
            
            elif self.temp_output_path and os.path.isfile(self.temp_output_path):
                pass
            
            self.image.set_images(file_path, output_to_show if output_to_show is not None else "")
            
    def apply_settings(self):
        if 'model' in self.settings:
            self.combo_model.setCurrentText(self.settings['model'])
        if 'format' in self.settings:
            self.combo_format.setCurrentText(self.settings['format'])