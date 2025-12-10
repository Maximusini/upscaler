from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QPixmap, QColor, QPen
from PySide6.QtCore import Qt, QRect, Signal

class ComparisonWidget(QWidget):
    file_dropped = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.setMouseTracking(True)
        self.setAcceptDrops(True)
        
        self.before = None
        self.after = None
        self.slider_pos = 0.5
        self.is_dragging = False
        self.zoom = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.is_panning = False
        self.last_mouse_pos = None
        
    def set_images(self, before_path:str, after_path:str):
        self.before = QPixmap(before_path)
        self.slider_pos = 0.5
        if after_path:
            self.after = QPixmap(after_path)
        else:
            self.after = None
        
        self.update()
        
    def paintEvent(self, event):
        if not self.before:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        zoomed_rect = self.get_final_rect()
        visual_slider_x = int(zoomed_rect.left() + zoomed_rect.width() * self.slider_pos)
        visual_slider_x = max(zoomed_rect.left(), min(visual_slider_x, zoomed_rect.right()))
        
        if not self.after:
            painter.drawPixmap(zoomed_rect, self.before)
        else:
            painter.drawPixmap(zoomed_rect, self.after)
            
            clip_width = visual_slider_x - zoomed_rect.left()
            if clip_width > 0:
                painter.setClipRect(zoomed_rect.left(), zoomed_rect.top(), clip_width, zoomed_rect.height())
                painter.drawPixmap(zoomed_rect, self.before)
                painter.setClipping(False)
                
            painter.setPen(QPen(Qt.white, 1))
            painter.drawLine(visual_slider_x, zoomed_rect.top(), visual_slider_x, zoomed_rect.bottom())
            
            painter.setBrush(Qt.white)
            painter.setPen('grey')
            center_y = zoomed_rect.center().y()
            rect_x = visual_slider_x - 7
            rect_y = center_y - 20
            painter.drawRoundedRect(rect_x, rect_y, 14, 40, 5, 5)
        
        painter.end()
        
    def mouseMoveEvent(self, event):
        x = event.x()
        if self.before:
            zoomed_rect = self.get_final_rect()
            visual_slider_x = int(zoomed_rect.left() + zoomed_rect.width() * self.slider_pos)
        
            if abs(visual_slider_x - x) < 15:
                self.setCursor(Qt.SplitHCursor)
            elif self.is_panning:
                self.setCursor(Qt.ClosedHandCursor)
            else:
                self.setCursor(Qt.ArrowCursor)
            
            if self.is_dragging:
                pos = (event.x() - zoomed_rect.left()) / zoomed_rect.width()
                self.slider_pos = max(0.0, min(pos, 1.0))
                self.update()
            elif self.is_panning:
                delta = event.pos() - self.last_mouse_pos
                self.offset_x += delta.x()
                self.offset_y += delta.y()
                self.last_mouse_pos = event.pos()
                self.update()
            else:
                self.setCursor(Qt.ArrowCursor)
        
    def mousePressEvent(self, event):
        if self.before:
            zoomed_rect = self.get_final_rect()
            visual_slider_x = int(zoomed_rect.left() + zoomed_rect.width() * self.slider_pos)
            if abs(visual_slider_x - event.x()) < 15:
                self.is_dragging = True
                return
        self.is_panning = True
        self.last_mouse_pos = event.pos()

    
    def mouseReleaseEvent(self, event):
        self.is_dragging = False
        self.is_panning = False
        
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
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
    
    def dropEvent(self, event):
        files = event.mimeData().urls()
        if files:
            file_path = files[0].toLocalFile()
            self.file_dropped.emit(file_path)
        
    def wheelEvent(self, event):
        angle = event.angleDelta().y()
        if angle > 0:
            self.zoom *= 1.1
        else:
            self.zoom /= 1.1
        self.zoom = max(0.1, min(self.zoom, 10.0))
        self.update()
        
    def get_final_rect(self):
        base_rect = self.target_rect(self.before)
        
        final_w = base_rect.width() * self.zoom
        final_h = base_rect.height() * self.zoom
        
        final_x = base_rect.x() + self.offset_x - (final_w - base_rect.width()) / 2
        final_y = base_rect.y() + self.offset_y - (final_h - base_rect.height()) / 2
        
        return QRect(int(final_x), int(final_y), int(final_w), int(final_h))