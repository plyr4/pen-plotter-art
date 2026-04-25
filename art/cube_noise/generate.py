import math
import os

import numpy as np
from PIL import Image

from art.cube_shared import wiggle_polyline


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


def rotate_points(points_3d, rot_x=0.0, rot_y=0.0):
    """
    Rotate a list of (x, y, z) points around the X axis then the Y axis.
    rot_x, rot_y are in radians.
    """
    cx, sx = math.cos(rot_x), math.sin(rot_x)
    cy, sy = math.cos(rot_y), math.sin(rot_y)
    result = []
    for x, y, z in points_3d:
        # Rotate around X axis
        y1 = cx * y - sx * z
        z1 = sx * y + cx * z
        # Rotate around Y axis
        x2 = cy * x + sy * z1
        z2 = -sy * x + cy * z1
        result.append((x2, y1, z2))
    return result


def project_points_orthographic(points_3d, width, height):
    """
    Orthographic projection of (x, y, z) coordinates to 2D screen coordinates.
    """
    cx, cy = width / 2, height / 2
    size = min(width, height) * 0.28
    result = []
    for x, y, z in points_3d:
        result.append((cx + x * size, cy + y * size))
    return result


def cube(width, height, rot_x=math.radians(30), rot_y=math.radians(45)):
    """
    Returns polylines for a cube at the given viewing angles.
    Uses face loops to minimise pen lifts: 2 face loops + 4 connecting edges = 6 strokes.
    """
    vertices_3d = [
        (-1, -1, -1),  # v0
        ( 1, -1, -1),  # v1
        ( 1,  1, -1),  # v2
        (-1,  1, -1),  # v3
        (-1, -1,  1),  # v4
        ( 1, -1,  1),  # v5
        ( 1,  1,  1),  # v6
        (-1,  1,  1),  # v7
    ]

    rotated = rotate_points(vertices_3d, rot_x=rot_x, rot_y=rot_y)
    v = project_points_orthographic(rotated, width, height)

    return [
        # face loops (closed — pen never lifts mid-face)
        [v[0], v[1], v[2], v[3], v[0]],  # back face
        [v[4], v[5], v[6], v[7], v[4]],  # front face
        # connecting edges (genuinely separate strokes)
        [v[0], v[4]],
        [v[1], v[5]],
        [v[2], v[6]],
        [v[3], v[7]],
    ]


def generate_lines(width, height):
    noise = _load_noise()
    amplitude = 2.5
    lines = cube(width, height)
    return [
        wiggle_polyline(line, lambda mx, my: _sample_noise(noise, mx, my, width, height) * amplitude, segments=400)
        for line in lines
    ]
