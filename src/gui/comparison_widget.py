from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QPixmap, QColor, QPen
from PySide6.QtCore import Qt, QRect

class ComparisonWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setMouseTracking(True)
        
        self.before = None
        self.after = None
        self.slider_pos = 0.5 
        self.slider_x = 0
        
    def set_images(self, before_path:str, after_path:str):
        self.before = QPixmap(before_path)
        if after_path:
            self.after = QPixmap(after_path)
        
        self.update()
        
    def paintEvent(self, event):
        if not self.before:
            return
        
        painter = QPainter(self)
        if not self.after:
            painter.drawPixmap(self.rect(), self.before)
        else:
            painter.drawPixmap(self.rect(), self.after)
            painter.setClipRect(0, 0, self.slider_x, self.height())
            painter.drawPixmap(self.rect(), self.before)
            painter.setClipping(False)
            painter.setPen(QPen(Qt.white, 1))
            painter.drawLine(self.slider_x, 0, self.slider_x, self.height())
        
        painter.end()
        
    def mouseMoveEvent(self, event):
        x = event.x()
        self.slider_x = x
        self.update()
    
    