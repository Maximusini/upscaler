import sys
import os
import onnxruntime as ort
from PySide6.QtGui import QImageReader

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

from PySide6.QtWidgets import QApplication
from src.gui.main_window import MainWindow
from qt_material import apply_stylesheet


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setApplicationName('NeuralUpscaler')
    
    try:
        if hasattr(ort, 'preload_dlls'):
            ort.preload_dlls()
            print('NVIDIA libs preloaded.')
    except Exception as e:
        print(f'Info: {e}')
        
    QImageReader.setAllocationLimit(0)
    apply_stylesheet(app, theme='dark_blue.xml')

    window = MainWindow()
    window.show()
    sys.exit(app.exec())