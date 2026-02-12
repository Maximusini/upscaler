import sys
import os
import onnxruntime as ort
import logging
from logging.handlers import RotatingFileHandler

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImageReader
from PySide6.QtCore import QStandardPaths
from src.gui.main_window import MainWindow
from qt_material import apply_stylesheet

def setup_logging():
    """
    Настройка логирования для приложения. Логи сохраняются в папке AppData с ротацией файлов. Также логи выводятся в консоль.
    """
    app_data_path = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
    log_dir = os.path.join(app_data_path, 'logs')
    if not os.path.exists(log_dir): 
        os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, 'upscaler.log')

    file_handler = RotatingFileHandler(log_file, maxBytes=1*1024*1024, backupCount=5, encoding='utf-8')
    stream_handler = logging.StreamHandler()

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s: %(module)s - %(message)s',
        datefmt='%H:%M:%S',
        handlers=[file_handler, stream_handler]
    )

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setApplicationName('NeuralUpscaler')
    
    setup_logging()
       
    QImageReader.setAllocationLimit(0)
    apply_stylesheet(app, theme='dark_blue.xml')

    window = MainWindow()
    window.show()
    sys.exit(app.exec())