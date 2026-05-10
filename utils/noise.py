import os

import numpy as np
from PIL import Image


def load_noise(path):
    path = os.path.join(path)
    img = Image.open(path).convert("L")
    # shape (H, W), values in [0, 1]
    arr = np.array(img, dtype=np.float32) / 255.0
    return arr


def sample_noise(arr, x, y, width, height):
    H, W = arr.shape
    ix = int((x / width) * W) % W
    iy = int((y / height) * H) % H
    return arr[iy, ix] * 2.0 - 1.0
