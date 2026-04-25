import os

import numpy as np
from PIL import Image

from art.cube_shared import cube, wiggle_polyline


def _load_noise():
    path = os.path.join(os.path.dirname(__file__), "noise1.png")
    img = Image.open(path).convert("L")
    arr = np.array(img, dtype=np.float32) / 255.0  # shape (H, W), values in [0, 1]
    return arr


def _sample_noise(arr, x, y, width, height):
    """
    Sample the noise array at canvas position (x, y).
    Returns a value in [-1, 1]: mid-gray → 0, white → +1, black → -1.
    Coordinates wrap if they fall outside the canvas.
    """
    H, W = arr.shape
    ix = int((x / width) * W) % W
    iy = int((y / height) * H) % H
    return arr[iy, ix] * 2.0 - 1.0


def generate_polylines(width, height):
    noise = _load_noise()
    amplitude = 2.5
    lines = cube(width, height)
    return [
        wiggle_polyline(line, lambda mx, my: _sample_noise(noise, mx, my, width, height) * amplitude, segments=400)
        for line in lines
    ]
