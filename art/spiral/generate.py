import math


def generate_lines(width, height):
    a = 0
    b = 1.3
    freq = 8.0
    step = 0.02
    amp = 10.0
    max_theta = 18 * 3.141592653589793
    cx, cy = width / 2, height / 2
    points, t = [], 0.0
    while t < max_theta:
        r = a + b * t + math.sin(t * freq) * amp
        points.append((cx + r * math.cos(t), cy + r * math.sin(t)))
        t += step
    return [points]
