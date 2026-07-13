import os
from PySide6.QtWidgets import QMainWindow, QHBoxLayout, QWidget, QMessageBox, QProgressDialog
from PySide6.QtCore import Qt, QTimer
from PIL import Image

from .viewport import ViewportWidget
from .control_panel import ControlPanel
from fractal_engine import TetrationEngine

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tetration Fractal Generator")
        self.resize(1200, 800)

        # Main Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Components
        self.viewport = ViewportWidget()
        self.control_panel = ControlPanel()

        layout.addWidget(self.viewport, stretch=1)
        layout.addWidget(self.control_panel, stretch=0)

        # Taichi Engine Setup
        self.engine = TetrationEngine(max_width=4000, max_height=4000)

        # Connect signals
        self.viewport.view_changed.connect(self.request_render)
        self.control_panel.parameters_changed.connect(self.request_render)
        self.control_panel.export_requested.connect(self.export_image)
        self.control_panel.animation_export_requested.connect(self.export_animation)

        # Debounce timer for rendering to avoid lag during fast scaling
        self.render_timer = QTimer()
        self.render_timer.setSingleShot(True)
        self.render_timer.timeout.connect(self.render_fractal)

        # Initial render delay
        QTimer.singleShot(100, self.request_render)

    def request_render(self):
        # Debounce rendering for 16ms (~60fps)
        self.render_timer.start(16)

    def render_fractal(self):
        params = self.control_panel.get_parameters()
        w = self.viewport.width()
        h = self.viewport.height()
        
        if w <= 0 or h <= 0:
            return

        img_array = self.engine.render(
            nx=w,
            ny=h,
            max_iter=params["max_iter"],
            escape_radius=params["escape_radius"],
            px=params["px"],
            py=params["py"],
            scale=params["scale"],
            rotation=params["rotation"]
        )

        self.viewport.set_image(img_array)

    def pan_viewport(self, dx, dy):
        """
        Adjust center coordinates based on mouse drag.
        dx, dy are in pixels.
        """
        params = self.control_panel.get_parameters()
        w = self.viewport.width()
        h = self.viewport.height()
        scale = params["scale"]
        aspect = h / w if w > 0 else 1.0

        # In OpenGL/ND coordinates, total width is 2*scale, total height is 2*scale*aspect
        # So 1 pixel = (2*scale) / w
        dx_val = -dx * (2.0 * scale / w)
        dy_val = -dy * (2.0 * scale * aspect / h)

        import math
        # Consider rotation when panning
        rot = params["rotation"]
        cos_rot = math.cos(rot)
        sin_rot = math.sin(rot)
        
        real_dx = dx_val * cos_rot - dy_val * sin_rot
        real_dy = dx_val * sin_rot + dy_val * cos_rot

        self.control_panel.set_parameters(
            params["px"] + real_dx,
            params["py"] + real_dy,
            scale
        )
        self.request_render()

    def zoom_viewport(self, zoom_in, mouse_x, mouse_y):
        """
        Zoom in or out.
        """
        params = self.control_panel.get_parameters()
        zoom_factor = 0.9 if zoom_in else 1.1111111
        
        # To zoom towards mouse, we'd need more complex logic. 
        # For simplicity, zooming in/out from center.
        new_scale = params["scale"] * zoom_factor
        
        self.control_panel.set_parameters(
            params["px"],
            params["py"],
            new_scale
        )
        self.request_render()

    def export_image(self, width, height):
        params = self.control_panel.get_parameters()
        QMessageBox.information(self, "Exporting", f"Exporting {width}x{height} image... This might take a moment.")
        
        # Create a new engine instance for export to support higher resolutions
        # or use existing if it fits
        engine = TetrationEngine(max_width=width, max_height=height)
        
        img_array = engine.render(
            nx=width,
            ny=height,
            max_iter=params["max_iter"],
            escape_radius=params["escape_radius"],
            px=params["px"],
            py=params["py"],
            scale=params["scale"],
            rotation=params["rotation"]
        )

        img_8u = (img_array * 255.0).astype('uint8')
        # Image is (width, height, 3). PIL expects (height, width, 3)
        img_8u = img_8u.transpose((1, 0, 2))
        
        im = Image.fromarray(img_8u)
        filename = f"tetration_{width}x{height}_px_{params['px']:.3f}_py_{params['py']:.3f}_eps_{params['scale']:.3f}.png"
        im.save(filename)
        QMessageBox.information(self, "Success", f"Saved to {filename}")

    def export_animation(self, width, height, frames):
        # We assume the user wants to zoom in to the current parameters 
        # from a larger scale, like in the reference code.
        params = self.control_panel.get_parameters()
        
        # Ask for confirmation
        reply = QMessageBox.question(self, "Export Animation", 
                                     f"Generate {frames} frames zooming into the current view at {width}x{height}?",
                                     QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.No:
            return

        engine = TetrationEngine(max_width=width, max_height=height)
        
        target_scale = params["scale"]
        # Assuming we want to start from scale 5.0 and reach target_scale in `frames` frames
        start_scale = 5.0
        
        if target_scale >= start_scale:
            QMessageBox.warning(self, "Error", "Current scale must be less than 5.0 to create a zoom-in animation.")
            return

        # scale_n = start_scale * (zoom_factor ^ n)
        # target_scale = start_scale * (zoom_factor ^ frames)
        import math
        zoom_factor = math.pow(target_scale / start_scale, 1.0 / frames)

        # Target center
        px_target = params["px"]
        py_target = params["py"]
        
        # Start center
        px = 0.0
        py = 0.0
        
        os.makedirs("zoom_output", exist_ok=True)

        progress = QProgressDialog("Rendering frames...", "Cancel", 0, frames, self)
        progress.setWindowModality(Qt.WindowModal)

        for frame in range(frames):
            if progress.wasCanceled():
                break

            current_scale = start_scale * math.pow(zoom_factor, frame)
            
            # Gradually move center
            px = px + (px_target - px) * (1 - zoom_factor)
            py = py + (py_target - py) * (1 - zoom_factor)

            img_array = engine.render(
                nx=width,
                ny=height,
                max_iter=params["max_iter"],
                escape_radius=params["escape_radius"],
                px=px,
                py=py,
                scale=current_scale,
                rotation=params["rotation"]
            )

            img_8u = (img_array * 255.0).astype('uint8')
            img_8u = img_8u.transpose((1, 0, 2))
            im = Image.fromarray(img_8u)
            
            filename = f"zoom_output/frame_{frame:04d}.png"
            im.save(filename)

            progress.setValue(frame + 1)
        
        if not progress.wasCanceled():
            QMessageBox.information(self, "Success", f"Animation frames saved to 'zoom_output' directory.")
