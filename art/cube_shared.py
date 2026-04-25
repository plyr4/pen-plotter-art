import math


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
