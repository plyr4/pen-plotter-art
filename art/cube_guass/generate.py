import random

from art.cube_shared import cube, wiggle_polyline


def generate_polylines(width, height):
    lines = cube(width, height)
    amplitude = 0.5
    return [
        wiggle_polyline(line, lambda mx, my: random.gauss(0, amplitude), segments=120)
        for line in lines
    ]
