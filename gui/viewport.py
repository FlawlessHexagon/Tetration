import numpy as np
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QImage, QPainter
from PySide6.QtCore import Qt, Signal

class ViewportWidget(QWidget):
    # Signals for interactive panning and zooming
    view_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.image = None
        
        # Interaction state
        self.last_mouse_pos = None
        self.is_panning = False

        self.setMouseTracking(True)

    def set_image(self, img_array: np.ndarray):
        """
        Takes an RGB numpy array (width, height, 3) in float32 [0..1]
        and displays it.
        """
        if img_array is None or img_array.size == 0:
            return

        # Convert to uint8
        img_8u = (np.clip(img_array, 0.0, 1.0) * 255.0).astype(np.uint8)
        
        # The Taichi array is typically (width, height, channels).
        # QImage expects (height, width, channels) or (width, height) depending on format,
        # but the data stride is per row. So we transpose to (height, width, channels)
        img_8u = np.transpose(img_8u, (1, 0, 2))
        
        height, width, channels = img_8u.shape
        bytes_per_line = channels * width
        
        # We need to keep a reference to img_8u so it doesn't get garbage collected
        # while QImage is using its memory.
        self._current_image_data = np.ascontiguousarray(img_8u)
        
        self.image = QImage(
            self._current_image_data.data, 
            width, 
            height, 
            bytes_per_line, 
            QImage.Format_RGB888
        )
        
        # Trigger a repaint
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        if self.image:
            # We draw the image scaled to fit the widget (though normally the engine 
            # renders exactly the widget's resolution)
            painter.drawImage(self.rect(), self.image)
        else:
            painter.fillRect(self.rect(), Qt.black)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # We emit view_changed so the engine can re-render at the new resolution
        self.view_changed.emit()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_panning = True
            self.last_mouse_pos = event.position()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_panning = False

    def mouseMoveEvent(self, event):
        if self.is_panning and self.last_mouse_pos is not None:
            delta = event.position() - self.last_mouse_pos
            # Pass the pixel delta to main window to adjust px, py
            self.parent().pan_viewport(delta.x(), delta.y())
            self.last_mouse_pos = event.position()

    def wheelEvent(self, event):
        # Determine scroll direction
        zoom_in = event.angleDelta().y() > 0
        # Pass zoom event to main window
        self.parent().zoom_viewport(zoom_in, event.position().x(), event.position().y())
