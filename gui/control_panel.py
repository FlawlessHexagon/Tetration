from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QDoubleSpinBox, QSpinBox, QPushButton, QGroupBox, QFormLayout
)
from PySide6.QtCore import Signal

class ControlPanel(QWidget):
    parameters_changed = Signal()
    export_requested = Signal(int, int) # width, height
    animation_export_requested = Signal(int, int, int) # width, height, frames

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(300)

        main_layout = QVBoxLayout(self)

        # Basic Parameters Group
        param_group = QGroupBox("Fractal Parameters")
        param_layout = QFormLayout()

        self.px_spin = QDoubleSpinBox()
        self.px_spin.setRange(-10.0, 10.0)
        self.px_spin.setDecimals(6)
        self.px_spin.setSingleStep(0.01)
        self.px_spin.setValue(0.0)

        self.py_spin = QDoubleSpinBox()
        self.py_spin.setRange(-10.0, 10.0)
        self.py_spin.setDecimals(6)
        self.py_spin.setSingleStep(0.01)
        self.py_spin.setValue(0.0)

        self.scale_spin = QDoubleSpinBox()
        self.scale_spin.setRange(1e-12, 100.0)
        self.scale_spin.setDecimals(12)
        self.scale_spin.setSingleStep(0.1)
        self.scale_spin.setValue(5.0)

        self.max_iter_spin = QSpinBox()
        self.max_iter_spin.setRange(1, 10000)
        self.max_iter_spin.setValue(500)

        self.escape_radius_spin = QDoubleSpinBox()
        self.escape_radius_spin.setRange(1.0, 1e12)
        self.escape_radius_spin.setDecimals(1)
        self.escape_radius_spin.setValue(1e10)

        self.rotation_spin = QDoubleSpinBox()
        self.rotation_spin.setRange(-360.0, 360.0)
        self.rotation_spin.setValue(0.0)

        param_layout.addRow("Center X (px):", self.px_spin)
        param_layout.addRow("Center Y (py):", self.py_spin)
        param_layout.addRow("Scale (eps):", self.scale_spin)
        param_layout.addRow("Max Iterations:", self.max_iter_spin)
        param_layout.addRow("Escape Radius:", self.escape_radius_spin)
        param_layout.addRow("Rotation (deg):", self.rotation_spin)
        param_group.setLayout(param_layout)

        # Export Group
        export_group = QGroupBox("Export High Res")
        export_layout = QFormLayout()

        self.export_w_spin = QSpinBox()
        self.export_w_spin.setRange(100, 16384)
        self.export_w_spin.setValue(3840)

        self.export_h_spin = QSpinBox()
        self.export_h_spin.setRange(100, 16384)
        self.export_h_spin.setValue(2160)

        self.export_btn = QPushButton("Export Current View")

        export_layout.addRow("Width:", self.export_w_spin)
        export_layout.addRow("Height:", self.export_h_spin)
        export_layout.addRow(self.export_btn)
        export_group.setLayout(export_layout)

        # Animation Group
        anim_group = QGroupBox("Zoom Animation Export")
        anim_layout = QFormLayout()

        self.anim_frames_spin = QSpinBox()
        self.anim_frames_spin.setRange(1, 10000)
        self.anim_frames_spin.setValue(600)

        self.anim_btn = QPushButton("Export Zoom Video Frames")
        
        anim_layout.addRow("Total Frames:", self.anim_frames_spin)
        anim_layout.addRow(self.anim_btn)
        anim_group.setLayout(anim_layout)

        # Add groups to main layout
        main_layout.addWidget(param_group)
        main_layout.addWidget(export_group)
        main_layout.addWidget(anim_group)
        main_layout.addStretch()

        # Connect signals
        self.px_spin.valueChanged.connect(self.on_param_changed)
        self.py_spin.valueChanged.connect(self.on_param_changed)
        self.scale_spin.valueChanged.connect(self.on_param_changed)
        self.max_iter_spin.valueChanged.connect(self.on_param_changed)
        self.escape_radius_spin.valueChanged.connect(self.on_param_changed)
        self.rotation_spin.valueChanged.connect(self.on_param_changed)

        self.export_btn.clicked.connect(self.on_export_clicked)
        self.anim_btn.clicked.connect(self.on_anim_clicked)

        # To avoid emitting signal constantly during typing/spin
        self._emit_enabled = True

    def set_parameters(self, px, py, scale):
        self._emit_enabled = False
        self.px_spin.setValue(px)
        self.py_spin.setValue(py)
        self.scale_spin.setValue(scale)
        self._emit_enabled = True

    def get_parameters(self):
        import math
        return {
            "px": self.px_spin.value(),
            "py": self.py_spin.value(),
            "scale": self.scale_spin.value(),
            "max_iter": self.max_iter_spin.value(),
            "escape_radius": self.escape_radius_spin.value(),
            "rotation": math.radians(self.rotation_spin.value())
        }

    def on_param_changed(self):
        if self._emit_enabled:
            self.parameters_changed.emit()

    def on_export_clicked(self):
        w = self.export_w_spin.value()
        h = self.export_h_spin.value()
        self.export_requested.emit(w, h)

    def on_anim_clicked(self):
        w = self.export_w_spin.value()
        h = self.export_h_spin.value()
        frames = self.anim_frames_spin.value()
        self.animation_export_requested.emit(w, h, frames)
