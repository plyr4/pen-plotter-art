import math
import os
import struct
from functools import lru_cache

import numpy as np


def _rotation_matrix(rot_x=0.0, rot_y=0.0, rot_z=0.0):
    """Combined XYZ rotation matrix (Rx applied first, then Ry, then Rz)."""
    cx, sx = math.cos(rot_x), math.sin(rot_x)
    cy, sy = math.cos(rot_y), math.sin(rot_y)
    cz, sz = math.cos(rot_z), math.sin(rot_z)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]], dtype=float)
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]], dtype=float)
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]], dtype=float)
    return Rz @ Ry @ Rx


@lru_cache(maxsize=None)
def parse_stl(path):
    """Parse an ASCII or binary STL file.

    Returns a list of triangles, each a numpy array of shape (3, 3):
    3 vertices × (x, y, z).
    """
    file_size = os.path.getsize(path)

    # try to detect binary vs ASCII.
    # binary STL: 80-byte header + 4-byte count + count * 50 bytes per triangle.
    with open(path, 'rb') as f:
        header = f.read(80)
        count_data = f.read(4)

    if len(header) == 80 and len(count_data) == 4:
        count = struct.unpack('<I', count_data)[0]
        if file_size == 80 + 4 + count * 50:
            # binary STL
            triangles = []
            with open(path, 'rb') as f:
                f.read(84)  # skip header + count
                for _ in range(count):
                    data = f.read(50)
                    if len(data) < 50:
                        break
                    # layout: normal (12 B) + 3×vertex (36 B) + attrib (2 B)
                    floats = struct.unpack('<9f', data[12:48])
                    triangles.append(
                        np.array(floats, dtype=float).reshape(3, 3))
            return triangles

    # ASCII STL
    triangles = []
    verts = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line.startswith("vertex"):
                parts = line.split()
                verts.append(
                    [float(parts[1]), float(parts[2]), float(parts[3])])
            elif line.startswith("endloop"):
                if len(verts) == 3:
                    triangles.append(np.array(verts, dtype=float))
                verts = []
    return triangles


def _mesh_edges(triangles, tol=1e-6):
    """Extract wireframe edges from a triangle soup.

    Edges shared between two co-planar triangles (face-triangulation diagonals)
    are removed, leaving only fold/boundary edges for a clean wireframe.
    Returns list of (v0, v1) numpy array pairs.
    """
    def face_normal(tri):
        e1, e2 = tri[1] - tri[0], tri[2] - tri[0]
        n = np.cross(e1, e2)
        mag = np.linalg.norm(n)
        return n / mag if mag > 0 else n

    normals = [face_normal(tri) for tri in triangles]

    # edge, triangle index list
    edge_data = {}
    for ti, tri in enumerate(triangles):
        for i in range(3):
            a = tri[i]
            b = tri[(i + 1) % 3]
            key = tuple(sorted([
                tuple(np.round(a / tol).astype(int)),
                tuple(np.round(b / tol).astype(int)),
            ]))
            if key not in edge_data:
                edge_data[key] = {"edge": (a.copy(), b.copy()), "tris": []}
            edge_data[key]["tris"].append(ti)

    edges = []
    for data in edge_data.values():
        tris = data["tris"]
        if len(tris) == 2:
            # skip edge if both adjacent triangles are co-planar (face diagonal)
            if np.dot(normals[tris[0]], normals[tris[1]]) > 1.0 - tol:
                continue
        edges.append(data["edge"])
    return edges


def project_mesh(stl_path, width, height,
                 rot_x=math.radians(25), rot_y=0.0, rot_z=math.radians(45),
                 scale=None, center_x=None, center_y=None):
    """Load an ASCII STL, rotate, and orthographically project to 2D canvas space.

    Assumes Blender Z-up convention (X=right, Y=forward, Z=up).
    Projects as: screen_x = rotated_x, screen_y = -rotated_z
    so that Blender's "up" maps to canvas "up".

    Args:
        stl_path: path to an ASCII STL file.
        width, height: canvas dimensions in mm.
        rot_x: tilt around X axis in radians (tips the top toward viewer).
        rot_y: rotation around Y axis in radians.
        rot_z: spin around Z (vertical) axis in radians.
        scale: mm per model unit. Defaults to fill ~80% of the shorter canvas axis.

    Returns:
        List of 2-point polylines [(x0, y0), (x1, y1)], one per unique edge.
    """
    triangles = parse_stl(stl_path)
    edges = _mesh_edges(triangles)
    R = _rotation_matrix(rot_x, rot_y, rot_z)
    rotated = [(R @ a, R @ b) for a, b in edges]

    if scale is None:
        all_pts = np.array([v for e in rotated for v in e])
        # scale based on the XZ footprint (the axes visible on canvas)
        extent = max(np.max(np.abs(all_pts[:, 0])), np.max(
            np.abs(all_pts[:, 2])))
        scale = (min(width, height) * 0.4) / extent if extent > 0 else 1.0

    cx = center_x if center_x is not None else width / 2
    cy = center_y if center_y is not None else height / 2

    def proj(v):
        # Blender Z-up: X → screen X, -Z → screen Y (so Z-up = canvas-up)
        return (cx + v[0] * scale, cy - v[2] * scale)

    return [[proj(a), proj(b)] for a, b in rotated]


def project_mesh_occluded(stl_path, width, height,
                          rot_x=math.radians(25), rot_y=0.0, rot_z=math.radians(45),
                          scale=None, center_x=None, center_y=None):
    """Like project_mesh but with back-face culling for hidden-line removal.

    Each edge is classified by its adjacent faces.  An edge is drawn only if at
    least one neighbouring face is front-facing (normal·view < 0).  For a closed
    solid mesh this correctly hides every back-face edge without any 2-D polygon
    operations.

    Returns:
        List of 2-point polylines [(x0, y0), (x1, y1)], one per visible edge.
    """
    tol = 1e-6
    triangles = parse_stl(stl_path)
    R = _rotation_matrix(rot_x, rot_y, rot_z)

    rotated_tris = [np.array([R @ v for v in tri]) for tri in triangles]

    def face_normal(tri):
        e1, e2 = tri[1] - tri[0], tri[2] - tri[0]
        n = np.cross(e1, e2)
        mag = np.linalg.norm(n)
        return n / mag if mag > 0 else n

    normals = [face_normal(tri) for tri in rotated_tris]
    # viewer at Y = -inf, front-facing when rotated normal Y < 0
    face_is_front = [n[1] < 0 for n in normals]

    if scale is None:
        all_pts = np.concatenate(rotated_tris)
        extent = max(np.max(np.abs(all_pts[:, 0])), np.max(
            np.abs(all_pts[:, 2])))
        scale = (min(width, height) * 0.4) / extent if extent > 0 else 1.0

    cx = center_x if center_x is not None else width / 2
    cy = center_y if center_y is not None else height / 2

    def proj2d(v):
        return (cx + v[0] * scale, cy - v[2] * scale)

    # build edge, adjacent face list
    edge_data = {}
    for ti, tri in enumerate(rotated_tris):
        for i in range(3):
            a = tri[i]
            b = tri[(i + 1) % 3]
            key = tuple(sorted([
                tuple(np.round(a / tol).astype(int)),
                tuple(np.round(b / tol).astype(int)),
            ]))
            if key not in edge_data:
                edge_data[key] = {"verts": (a.copy(), b.copy()), "tris": []}
            edge_data[key]["tris"].append(ti)

    result = []
    for data in edge_data.values():
        tris = data["tris"]
        a3d, b3d = data["verts"]

        # drop coplanar shared edges (face-triangulation diagonals)
        if len(tris) == 2:
            if np.dot(normals[tris[0]], normals[tris[1]]) > 1.0 - tol:
                continue

        # keep only edges adjacent to at least one front-facing triangle.
        # pure back-face edges are always occluded on a closed solid mesh.
        if any(face_is_front[ti] for ti in tris):
            result.append([proj2d(a3d), proj2d(b3d)])

    return result
