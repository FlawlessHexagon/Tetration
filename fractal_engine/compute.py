import taichi as ti
import numpy as np

# Initialize Taichi
# We let Taichi choose the best available backend (CUDA/Metal/Vulkan/OpenGL/CPU)
ti.init(arch=ti.gpu)

@ti.data_oriented
class TetrationEngine:
    def __init__(self, max_width=3840, max_height=2160):
        # We pre-allocate a large buffer to avoid re-allocating when resizing up to max resolution
        self.max_width = max_width
        self.max_height = max_height
        
        # Field for storing the divergence map (0: converged, 1: diverged)
        self.divergence_map = ti.field(dtype=ti.i32, shape=(max_width, max_height))
        # Image field for output visualization (RGB)
        self.image = ti.Vector.field(3, dtype=ti.f32, shape=(max_width, max_height))
        
    @ti.kernel
    def compute_kernel(
        self,
        nx: ti.i32,
        ny: ti.i32,
        max_iter: ti.i32,
        escape_radius_sq: ti.f32,
        px: ti.f32,
        py: ti.f32,
        scale: ti.f32,
        aspect_ratio: ti.f32,
        rotation: ti.f32
    ):
        # Cosine and sine for rotation
        cos_rot = ti.math.cos(rotation)
        sin_rot = ti.math.sin(rotation)

        for i, j in ti.ndrange(nx, ny):
            # Calculate normalized device coordinates (-1 to 1)
            u = (i / ti.cast(nx - 1, ti.f32)) * 2.0 - 1.0
            v = (j / ti.cast(ny - 1, ti.f32)) * 2.0 - 1.0

            # Scale and aspect ratio
            x_unrot = u * scale
            y_unrot = v * scale * aspect_ratio

            # Rotate
            x_rot = x_unrot * cos_rot - y_unrot * sin_rot
            y_rot = x_unrot * sin_rot + y_unrot * cos_rot

            # Translate to target center
            c_x = x_rot + px
            c_y = y_rot + py

            # Initial z = c
            z_x = c_x
            z_y = c_y
            
            diverged = 0

            for k in range(max_iter):
                r2 = c_x*c_x + c_y*c_y
                if r2 == 0:
                    break
                    
                r = ti.sqrt(r2)
                theta = ti.math.atan2(c_y, c_x)
                
                # ln(c) = ln|c| + i arg(c)
                ln_c_x = ti.math.log(r)
                ln_c_y = theta
                
                # z * ln(c)
                re = z_x * ln_c_x - z_y * ln_c_y
                im = z_x * ln_c_y + z_y * ln_c_x
                
                # exp(z * ln(c))
                e_re = ti.math.exp(re)
                z_x = e_re * ti.math.cos(im)
                z_y = e_re * ti.math.sin(im)
                
                if z_x*z_x + z_y*z_y > escape_radius_sq:
                    diverged = 1
                    break
            
            self.divergence_map[i, j] = diverged

    @ti.kernel
    def render_kernel(self, nx: ti.i32, ny: ti.i32):
        for i, j in ti.ndrange(nx, ny):
            if self.divergence_map[i, j] == 1:
                # Diverged: White
                self.image[i, j] = ti.Vector([1.0, 1.0, 1.0])
            else:
                # Converged: Black
                self.image[i, j] = ti.Vector([0.0, 0.0, 0.0])

    def render(self, nx, ny, max_iter, escape_radius, px, py, scale, rotation=0.0):
        # Ensure nx, ny are within allocated bounds
        nx = min(nx, self.max_width)
        ny = min(ny, self.max_height)
        aspect_ratio = ny / nx if nx != 0 else 1.0
        
        # Run computation
        self.compute_kernel(
            nx, ny, max_iter, escape_radius**2, px, py, scale, aspect_ratio, rotation
        )
        
        # Update image buffer
        self.render_kernel(nx, ny)
        
        # Return NumPy array for PySide6 or Pillow (shape: nx, ny, 3)
        # Slicing the field ensures we only grab the used portion
        return self.image.to_numpy()[:nx, :ny]

    def render_map(self, nx, ny, max_iter, escape_radius, px, py, scale, rotation=0.0):
        nx = min(nx, self.max_width)
        ny = min(ny, self.max_height)
        aspect_ratio = ny / nx if nx != 0 else 1.0
        
        self.compute_kernel(
            nx, ny, max_iter, escape_radius**2, px, py, scale, aspect_ratio, rotation
        )
        return self.divergence_map.to_numpy()[:nx, :ny]
