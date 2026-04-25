import math


def project_points_isometric(points_3d, width, height):
    """
    Isometric projection of (x, y, z) coordinates to 2D screen coordinates.
    """
    cx, cy = width / 2, height / 2
    size = min(width / (2 * math.sqrt(3)), height / 4) * 0.5
    a = math.pi / 6  # 30° isometric angle
    result = []
    for x, y, z in points_3d:
        xi = (x - z) * math.cos(a)
        yi = (x + z) * math.sin(a) - y
        result.append((cx + xi * size, cy + yi * size))
    return result


def cube_isometric_lines(width, height):
    """
    Returns the 4 polylines that form an isometric cube view:
    one closed hexagon (outer silhouette) and three interior diagonals.
    """
    vertices_3d = [
        ( 1, -1, -1),  # v0 - right
        ( 1,  1, -1),  # v1 - lower-right
        (-1,  1, -1),  # v2 - bottom
        (-1, -1,  1),  # v3 - left
        ( 1, -1,  1),  # v4 - upper
        (-1,  1,  1),  # v5 - upper-left
    ]
    v = project_points_isometric(vertices_3d, width, height)
    return [
        # outer hexagon (closed loop)
        [v[2], v[1], v[0], v[4], v[3], v[5], v[2]],
        # inner diagonals
        [v[0], v[5]],
        [v[2], v[4]],
        [v[3], v[1]],
    ]


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
    # Perpendicular unit vector (rotated 90°)
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
