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
        self.is_dragging = False
        
    def set_images(self, before_path:str, after_path:str):
        self.before = QPixmap(before_path)
        if after_path:
            self.after = QPixmap(after_path)
        else:
            self.after = None
            
        self.slider_x = self.width() // 2
        
        self.update()
        
    def paintEvent(self, event):
        if not self.before:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        target_rect = self.target_rect(self.before)
        
        if not self.after:
            painter.drawPixmap(target_rect, self.before)
        else:
            painter.drawPixmap(target_rect, self.after)
            painter.setClipRect(0, 0, self.slider_x, self.height())
            painter.drawPixmap(target_rect, self.before)
            painter.setClipping(False)
            painter.setPen(QPen(Qt.white, 1))
            painter.drawLine(self.slider_x, target_rect.top(), self.slider_x, target_rect.bottom())
            
            painter.setBrush(Qt.white)
            painter.setPen('grey')
            center_y = target_rect.center().y()
            rect_x = self.slider_x - 7
            rect_y = center_y - 20
            painter.drawRoundedRect(rect_x, rect_y, 14, 40, 5, 5)
        
        painter.end()
        
    def mouseMoveEvent(self, event):
        x = event.x()
        if self.before:
            target_rect = self.target_rect(self.before)
        
            if abs(self.slider_x - x) < 15:
                self.setCursor(Qt.SplitHCursor)
            else:
                self.setCursor(Qt.ArrowCursor)
            
            if self.is_dragging == True:
                self.slider_x = x
                self.slider_x = max(target_rect.left(), min(x, target_rect.right()))
                self.update()
            else:
                pass
        
    def mousePressEvent(self, event):
        if abs(self.slider_x - event.x()) < 15:
            self.is_dragging = True
        else:
            pass
    
    def mouseReleaseEvent(self, event):
        self.is_dragging = False
        
    def target_rect(self, pixmap):
        if not pixmap:
            return QRect()
        
        w_widget = self.width()
        h_widget = self.height()
        w_img = pixmap.width()
        h_img = pixmap.height()
        
        scale_w = w_widget / w_img
        scale_h = h_widget / h_img
        scale = min(scale_w, scale_h)
        new_w = int(w_img * scale)
        new_h = int(h_img * scale)
        offset_x = int((w_widget - new_w) / 2)
        offset_y = int((h_widget - new_h) / 2)
        return QRect(offset_x, offset_y, new_w, new_h)