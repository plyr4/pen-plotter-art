import random

from art.cube_shared import cube_isometric_lines, wiggle_polyline


def generate_lines(width, height):
    lines = cube_isometric_lines(width, height)
    amplitude = 0.5
    return [
        wiggle_polyline(line, lambda mx, my: random.gauss(0, amplitude), segments=120)
        for line in lines
    ]
