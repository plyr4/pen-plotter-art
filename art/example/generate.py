def generate_polylines(width, height):
    """
    width, height: page dimensions in mm (default A4: 210 x 297)
    Returns a list of polylines, where each polyline is a list of (x, y) tuples in mm.
    """

    # just two random two polylines
    polyline_1 = [(0, 0), (width, height)]
    polyline_2 = [(width, 0), (width, height)]

    return [polyline_1, polyline_2]
