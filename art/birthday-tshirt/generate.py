import math
import os
import sys

import vpype as vp
import vsketch
from shapely.geometry import LineString, Point, Polygon
from vpype.text import _Font
from vsketch.style import stylize_path

# cross-compatibility with "vsk run"
# fmt: off
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from models.models import MODELS_PATH
# fmt: on


class BirthdayTshirtSketch(vsketch.SketchClass):
    # Sketch parameters:
    text = vsketch.Param("Happy Birthday! ")
    repetitions = vsketch.Param(12, 1)
    start_radius = vsketch.Param(0.3, 0.0, step=0.1)
    start_size = vsketch.Param(0.25, 0.01, step=0.05)
    growth = vsketch.Param(0.2, 0.0, step=0.01)
    line_spacing = vsketch.Param(1.3, 0.5, step=0.1)
    letter_spacing = vsketch.Param(0.05, 0.0, step=0.01)
    font = vsketch.Param("futural", choices=vp.FONT_NAMES)
    font_weight = vsketch.Param(1, 1)
    reverse_spiral = vsketch.Param(False)
    ring_radius = vsketch.Param(7.35, 0.5, step=0.05)
    ring_thickness = vsketch.Param(0.6, 0.0, step=0.1)
    pen_width_mm = vsketch.Param(0.5, 0.05, step=0.05)
    arc_text = vsketch.Param("HAPPY BIRTHDAY")
    arc_text_size = vsketch.Param(1.4, 0.1, step=0.1)
    arc_text_gap = vsketch.Param(0.3, 0.0, step=0.1)
    arc_letter_spacing = vsketch.Param(0.15, 0.0, step=0.01)
    arc_font = vsketch.Param("futural", choices=vp.FONT_NAMES)
    arc_font_weight = vsketch.Param(1, 1)
    bottom_arc_text = vsketch.Param("HAPPY BIRTHDAY")
    outer_ring_gap = vsketch.Param(0.4, 0.0, step=0.1)
    star_margin = vsketch.Param(0.15, 0.0, step=0.05)
    star_inner_ratio = vsketch.Param(0.4, 0.1, 0.9, step=0.05)
    star_rotation = vsketch.Param(0.0, -72.0, 72.0, step=1.0)
    footer_text = vsketch.Param("MAKE A WISH")
    footer_text_size = vsketch.Param(1.0, 0.1, step=0.1)
    footer_text_gap = vsketch.Param(0.3, 0.0, step=0.1)
    footer_letter_spacing = vsketch.Param(0.15, 0.0, step=0.01)
    footer_font = vsketch.Param("futural", choices=vp.FONT_NAMES)
    footer_font_weight = vsketch.Param(1, 1)

    def draw(self, vsk: vsketch.Vsketch) -> None:
        vsk.size("a4", landscape=True)
        vsk.scale("cm")

        cm = vp.convert_length("cm")
        cx, cy = vsk.width / cm / 2, vsk.height / cm / 2

        vsk.penWidth(f"{self.pen_width_mm}mm")

        pen_width = self.pen_width_mm / 10

        # the spiral is free to grow past the ring; everything else is built off
        # the ring radius alone
        draw_text_spiral(
            vsk,
            self.text * self.repetitions,
            cx,
            cy,
            start_radius=self.start_radius,
            start_size=self.start_size,
            growth=self.growth,
            line_spacing=self.line_spacing,
            letter_spacing=self.letter_spacing,
            font=self.font,
            weight=self.font_weight,
            pen_width=pen_width,
            reverse=self.reverse_spiral,
        )

        outer = self.ring_radius
        draw_thick_ring(vsk, cx, cy, outer - self.ring_thickness, outer, pen_width)

        arcs_extent = outer
        for arc_text, side in ((self.arc_text, "top"), (self.bottom_arc_text, "bottom")):
            extent = draw_text_arc(
                vsk,
                arc_text,
                cx,
                cy,
                outer + self.arc_text_gap,
                size=self.arc_text_size,
                letter_spacing=self.arc_letter_spacing,
                font=self.arc_font,
                side=side,
                weight=self.arc_font_weight,
                pen_width=pen_width,
            )
            arcs_extent = max(arcs_extent, extent)

        # second ring wrapping the arc texts, same thickness
        wrap_inner = arcs_extent + self.outer_ring_gap
        wrap_outer = wrap_inner + self.ring_thickness
        draw_thick_ring(vsk, cx, cy, wrap_inner, wrap_outer, pen_width)

        # a filled star on the left and right of the band between the two rings,
        # sized so its width fits the band with a margin on both sides. The right
        # star is the mirror image of the left one, so it rotates the other way.
        band_mid = (outer + wrap_inner) / 2
        band_width = wrap_inner - outer
        for side in (-1, 1):
            rotation = -side * self.star_rotation
            half_width = band_width / 2 - self.star_margin
            star_radius = half_width / _star_half_width(self.star_inner_ratio, rotation)
            draw_filled_star(
                vsk,
                cx + side * band_mid,
                cy,
                star_radius,
                self.star_inner_ratio,
                pen_width,
                rotation=rotation,
            )

        # text wrapped around the bottom of the outer ring
        footer_extent = draw_text_arc(
            vsk,
            self.footer_text,
            cx,
            cy,
            wrap_outer + self.footer_text_gap,
            size=self.footer_text_size,
            letter_spacing=self.footer_letter_spacing,
            font=self.footer_font,
            side="bottom",
            weight=self.footer_font_weight,
            pen_width=pen_width,
        )

        # the footer only hangs below the rings, so lift everything by half of
        # it to keep the whole design centered on the page
        overhang = footer_extent - wrap_outer
        if overhang > 0:
            vsk.document.translate(0, -overhang / 2 * vp.convert_length("cm"))

    def finalize(self, vsk: vsketch.Vsketch) -> None:
        vsk.vpype(
            "linemerge --tolerance 0.5mm linesimplify --tolerance 0.1mm linesort reloop --tolerance 0.05mm")


def _glyph_advance(ch: str, font: _Font, size: float) -> float:
    """Horizontal advance of a single character at the given size."""
    index = ord(ch) - 32
    if index < 0 or index >= len(font.glyphs):
        return 0.0
    glyph = font.glyphs[index]
    return (glyph.rt - glyph.lt) * size / font.max_height


def _draw_glyph(
    vsk: vsketch.Vsketch, lines: vp.LineCollection, weight: int, pen_width: float
) -> None:
    """Add glyph strokes at the current transform, ``weight`` pen widths thick.

    vsketch's own text ignores ``strokeWeight``, so the strokes are thickened
    here the same way vsketch thickens shapes: weight 1 is the plain stroke and
    each extra pair of lines is an offset of it, ``pen_width`` apart.
    """
    for line in lines:
        for path in stylize_path(line, weight, pen_width, vsk.epsilon, "round"):
            if len(path) > 1:
                vsk.geometry(LineString(vp.as_vector(path)))


def draw_text_spiral(
    vsk: vsketch.Vsketch,
    text: str,
    x: float,
    y: float,
    *,
    start_radius: float = 0.3,
    start_size: float = 0.25,
    growth: float = 0.12,
    line_spacing: float = 1.3,
    letter_spacing: float = 0.05,
    font: str = "futural",
    max_radius: float | None = None,
    weight: int = 1,
    pen_width: float = 0.05,
    reverse: bool = False,
) -> float:
    """Write ``text`` along a spiral starting at (x, y) and winding outward.

    The font size grows linearly with distance from the center
    (``size = start_size + growth * r``). The gap between consecutive turns is
    ``line_spacing`` times the current font size, so turns never overlap as the
    letters get larger. Letters are oriented with their tops pointing away from
    the center. ``weight`` is the stroke thickness in pen widths. All lengths
    are in the sketch's current units.

    With ``reverse`` the spiral keeps exactly the same shape but is read from
    the outside in: the first character sits at the outer end and the last one
    at the center, with the letters turned around (tops toward the center) so
    they read along the inward direction.

    Returns the radius of the smallest circle centered on (x, y) that encloses
    all of the drawn text.
    """
    hershey = _Font.get(font)

    # the path is always walked from the center out, so a text that is read from
    # the outside in has to be laid out back to front
    if reverse:
        text = text[::-1]

    r = start_radius
    theta = 0.0
    extent = 0.0

    def size_at(radius: float) -> float:
        return start_size + growth * radius

    def advance(arc: float) -> None:
        # step along the spiral by an arc length, in small increments since
        # both r and dθ depend on the current position
        nonlocal r, theta
        remaining = arc
        while remaining > 1e-9:
            ds = min(remaining, 0.05 * max(size_at(r), 1e-3))
            dr_dtheta = line_spacing * size_at(r) / (2 * math.pi)
            dtheta = ds / math.hypot(r, dr_dtheta)
            theta += dtheta
            r += dr_dtheta * dtheta
            remaining -= ds

    for ch in text:
        if max_radius is not None and r > max_radius:
            break

        size = size_at(r)
        half = (_glyph_advance(ch, hershey, size) + letter_spacing * size) / 2

        # place the glyph at the middle of its advance so it sits on the curve
        advance(half)
        if ch.strip():
            # tangent direction: θ + 90° in screen space (y down) keeps the
            # glyph's top pointing outward
            dr_dtheta = line_spacing * size_at(r) / (2 * math.pi)
            tangent = theta + math.atan2(r, dr_dtheta)
            if reverse:
                tangent += math.pi

            # measure the glyph's actual outermost point relative to the center
            pos = complex(r * math.cos(theta), r * math.sin(theta))
            rot = complex(math.cos(tangent), math.sin(tangent))
            lines = vp.text_line(ch, font, size_at(r), align="center")
            for line in lines:
                extent = max(extent, float(abs(pos + line * rot).max()))

            vsk.pushMatrix()
            vsk.translate(x + r * math.cos(theta), y + r * math.sin(theta))
            vsk.rotate(tangent)
            _draw_glyph(vsk, lines, weight, pen_width)
            vsk.popMatrix()
        advance(half)

    return extent + (weight - 1) * pen_width / 2


def draw_text_arc(
    vsk: vsketch.Vsketch,
    text: str,
    x: float,
    y: float,
    radius: float,
    *,
    size: float = 1.0,
    letter_spacing: float = 0.1,
    font: str = "futural",
    side: str = "top",
    weight: int = 1,
    pen_width: float = 0.05,
) -> float:
    """Write ``text`` along the outside of a circle, centered at its top or bottom.

    ``side="top"`` reads left to right across the top with letter tops pointing
    away from the center; the lowest point of the text sits on ``radius``.
    ``side="bottom"`` reads left to right across the bottom with letters upright
    (tops pointing toward the center); the highest point of the text sits on
    ``radius``. Either way, passing a ring's outer radius puts the text just
    outside it. ``letter_spacing`` is a fraction of ``size`` and ``weight`` the
    stroke thickness in pen widths. All lengths are in the sketch's current
    units.

    Returns the radius of the farthest point drawn from (x, y).
    """
    if side not in ("top", "bottom"):
        raise ValueError(f"unknown side '{side}'")
    if not text:
        return radius

    top = side == "top"
    hershey = _Font.get(font)
    advances = [
        _glyph_advance(ch, hershey, size) + letter_spacing * size for ch in text
    ]

    # glyphs are drawn centered on y=0 (y down); push that line out so the edge
    # of the text facing the ring lands on the requested radius
    bounds = vp.text_line(text, font, size).bounds()
    if bounds is None:
        return radius
    # thicker strokes spread half the extra thickness to each side
    spread = (weight - 1) * pen_width / 2
    r = (radius + bounds[3] if top else radius - bounds[1]) + spread

    # angles grow clockwise on screen (y down), so the bottom text runs
    # backwards in angle to still read left to right
    direction = 1.0 if top else -1.0
    center_angle = -math.pi / 2 if top else math.pi / 2
    total = sum(advances) - letter_spacing * size
    theta = center_angle - direction * total / (2 * r)
    extent = radius
    for ch, adv in zip(text, advances):
        half = (adv - letter_spacing * size) / 2
        glyph_theta = theta + direction * half / r
        if ch.strip():
            lines = vp.text_line(ch, font, size, align="center")
            angle = glyph_theta + direction * math.pi / 2
            pos = complex(r * math.cos(glyph_theta), r * math.sin(glyph_theta))
            rot = complex(math.cos(angle), math.sin(angle))
            for line in lines:
                extent = max(extent, float(abs(pos + line * rot).max()) + spread)

            vsk.pushMatrix()
            vsk.translate(x + pos.real, y + pos.imag)
            vsk.rotate(angle)
            _draw_glyph(vsk, lines, weight, pen_width)
            vsk.popMatrix()
        theta += direction * adv / r

    return extent


def _star_unit_vertices(
    inner_ratio: float, rotation: float, points: int = 5
) -> list[tuple[float, float]]:
    """Vertices of a star with tips at distance 1 from the origin."""
    vertices = []
    for i in range(points * 2):
        r = 1.0 if i % 2 == 0 else inner_ratio
        angle = -math.pi / 2 + math.radians(rotation) + i * math.pi / points
        vertices.append((r * math.cos(angle), r * math.sin(angle)))
    return vertices


def _star_half_width(inner_ratio: float, rotation: float) -> float:
    """Largest horizontal distance from the center of a unit-radius star."""
    return max(abs(dx) for dx, _ in _star_unit_vertices(inner_ratio, rotation))


def draw_filled_star(
    vsk: vsketch.Vsketch,
    x: float,
    y: float,
    radius: float,
    inner_ratio: float,
    pen_width: float,
    points: int = 5,
    rotation: float = 0.0,
) -> None:
    """Draw a star filled with nested outlines.

    With ``rotation`` 0 one point faces straight up; ``rotation`` is in degrees,
    clockwise on screen.

    ``radius`` is the distance from the center to the tips and ``inner_ratio``
    the inner vertices' distance as a fraction of it. The fill is the outline
    repeatedly inset by ``pen_width``, so the plotter keeps drawing continuous
    star-shaped loops until the shape closes up. ``radius`` and ``pen_width``
    are in the sketch's current units.
    """
    if radius <= 0:
        return

    vertices = [
        (x + dx * radius, y + dy * radius)
        for dx, dy in _star_unit_vertices(inner_ratio, rotation, points)
    ]

    shape = Polygon(vertices)
    # the first path sits half a pen width inside the edge so the ink stays
    # within the requested outline
    shape = shape.buffer(-pen_width / 2, join_style="mitre", mitre_limit=10.0)
    while not shape.is_empty:
        for poly in getattr(shape, "geoms", [shape]):
            vsk.geometry(poly.exterior)
        shape = shape.buffer(-pen_width, join_style="mitre", mitre_limit=10.0)


def draw_thick_ring(
    vsk: vsketch.Vsketch,
    x: float,
    y: float,
    inner_radius: float,
    outer_radius: float,
    pen_width: float,
) -> None:
    """Draw a solid ring as concentric circles spaced by the pen width.

    Concentric circles plot as one continuous stroke each (no hatching pen
    lifts), and the edges stay perfectly round. ``pen_width`` must be in the
    sketch's current units.
    """
    thickness = max(outer_radius - inner_radius, 0.0)
    # the pen covers half its width on each side of the path, so keep the
    # outermost/innermost paths inset to land the ink on the requested radii
    count = max(1, math.ceil(max(thickness - pen_width, 0.0) / pen_width) + 1)
    start = inner_radius + pen_width / 2
    end = max(outer_radius - pen_width / 2, start)
    step = (end - start) / (count - 1) if count > 1 else 0.0
    for i in range(count):
        vsk.geometry(Point(x, y).buffer(start + i * step, quad_segs=64).exterior)


if __name__ == "__main__":
    BirthdayTshirtSketch.display()
