import numpy as np
from gradients import gradients
from windows import patch_system
from solve import solve_window


def dense_lk(frame0, frame1, radius=1, min_eigenvalue=1e-6):
    """Frames: finite same-shape (H,W), H,W>=2. radius>=0. Return (flow float (H,W,2), valid bool (H,W)). At every full patch, use gradients, patch_system and solve_window; copy uv into flow[y,x]. Invalid or incomplete patches have flow=[0,0], valid=False. u is component 0, v component 1."""
    # TODO: implement the stated operation using NumPy.
    raise NotImplementedError("Implement dense_lk")

