import math


def wiggle_segment(p1, p2, offset_fn, segments=8):
    """
    Subdivide a line segment and displace each interior point perpendicularly.

    offset_fn(mx, my) -> float
        Called at each midpoint (mx, my) in canvas coordinates.
        Return value is the perpendicular displacement in mm.
    Endpoints are kept fixed so corners stay sharp.
    """
    x1, y1 = p1
    x2, y2 = p2
    dx, dy = x2 - x1, y2 - y1
    length = math.sqrt(dx * dx + dy * dy)
    if length == 0:
        return [p1, p2]
    # perpendicular unit vector (rotated 90°)
    px, py = -dy / length, dx / length
    pts = [p1]
    for i in range(1, segments):
        t = i / segments
        mx = x1 + t * dx
        my = y1 + t * dy
        offset = offset_fn(mx, my)
        pts.append((mx + px * offset, my + py * offset))
    pts.append(p2)
    return pts


def wiggle_polyline(polyline, offset_fn, segments=8):
    """
    Wiggle every segment in a polyline using offset_fn, joining them
    without duplicate corner points.
    """
    result = []
    for i in range(len(polyline) - 1):
        seg = wiggle_segment(polyline[i], polyline[i + 1], offset_fn, segments)
        result.extend(seg if i == 0 else seg[1:])
    return result
