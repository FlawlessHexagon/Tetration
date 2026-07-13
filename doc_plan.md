# Tetration Fractal Generator Project Plan

## 1. Project Overview
This project aims to develop a high-performance program to generate **Tetration (Power Tower) Fractals**. The application will allow users to customize parameters extensively, including resolution, coordinates, max iteration, eps (scale), aspect ratio, and rotation. It will offer real-time smooth zooming functionality and offline high-resolution rendering capabilities.

## 2. Technology Stack
- **Language**: Python 3
- **Computation**: [Taichi](https://github.com/taichi-dev/taichi)
  - Taichi will compile the fractal mathematics into optimized GPU kernels at runtime.
  - This provides native GPU acceleration across multiple platforms (CUDA for Nvidia/Linux, Vulkan, Metal for macOS).
- **GUI & Interaction**: [PySide6](https://doc.qt.io/qtforpython-6/) (Qt for Python)
  - A responsive desktop application providing real-time controls and a smooth viewport for fractal exploration.
- **Image Export**: Pillow & NumPy
  - Used for rapid saving of high-resolution single frames or frame sequences.

## 3. Directory Structure
```text
Tetration/
├── README.md               # Project documentation and setup guide
├── requirements.txt        # Python dependencies
├── .gitignore              # Ignored files (venv, pycache, Reference)
├── doc_plan.md             # This document (overall project plan)
├── main.py                 # Application entry point
├── fractal_engine/         # Core GPU math and computation modules
│   ├── __init__.py
│   └── compute.py          # Taichi kernels for tetration
├── gui/                    # Graphical User Interface modules
│   ├── __init__.py
│   ├── main_window.py      # Main application layout and state management
│   ├── viewport.py         # PySide6 widget for rendering Taichi output
│   └── control_panel.py    # Sliders, spinboxes for parameter input
└── Reference/              # Original pure-Python reference implementations (ignored)
```

## 4. Development Phases

### Phase 1: Setup and Foundation (Current)
- Initialize Git repository with proper `.gitignore`.
- Set up Python virtual environment and dependencies (`requirements.txt`).
- Document the overarching architectural plan (`doc_plan.md`).

### Phase 2: Core GPU Engine (Taichi)
- Translate the pure-Python complex number logic `c_val ** z` into an optimized Taichi kernel (`@ti.kernel`).
- Support parameter inputs to the kernel: resolution, scale, center coordinates, max_iter, and escape radius.
- Verify correctness by comparing output with the `Reference/` code.

### Phase 3: Graphical User Interface (PySide6)
- Develop the main application window.
- Create a `Viewport` widget that frequently pulls rendering data from Taichi and paints it onto the screen for smooth real-time viewing.
- Implement UI controls to modify parameters (`px`, `py`, `scale`, `max_iter`, etc.) and instantly trigger a viewport update.
- Implement drag-and-drop or mouse scrolling for interactive panning and zooming.

### Phase 4: High-Resolution Rendering & Animation Export
- Implement a feature to export the current viewport at custom resolutions (e.g., 4K, 8K) overriding the screen size.
- Implement a "Zoom Animation Export" panel:
  - Takes `start_frame`, `end_frame`, `initial_scale`, `target_center`, and `zoom_factor` (similar to `PTF_zoom.py`).
  - Sequentially calculates and saves frames to disk seamlessly.

### Phase 5: Cross-Platform Verification & Release
- Verify installation and performance on Linux with CUDA/Vulkan.
- Provide instructions for macOS (Metal) and Windows (CUDA/Vulkan).
- Push complete application to GitHub.
