"""General closed-contour geometry — the domain-v3 shape kernel.

A `Contour` is a closed, counter-clockwise loop of straight or circular-arc
edges in module-local mm. It replaces "width × height rectangle" as the
module's outer shape: frame members follow edges, the fill region is the
contour offset inward, and every cut angle derives from real corner
geometry — never from a product-type lookup.

Conventions
-----------

- Edge i runs from `vertices[i]` to `vertices[(i + 1) % n]`.
- `bulges[i]` is the signed sagitta (rise) of edge i: ``None``/``0`` is a
  straight line; a positive bulge makes the edge a circular arc bulging to
  the RIGHT of the directed edge — outward, on a CCW loop. Only minor arcs
  are accepted (`|sagitta| <= chord/2`): every fenestration arch is one.
- All math is `Decimal`; angles flow through `trig` (Taylor series), so
  results stay deterministic and well below the 0.01 mm quantum.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from pydantic import Field, model_validator

from dekopen_engine.models import EngineModel, PlanPoint
from dekopen_engine.trig import asin_degrees, atan2_degrees, cos_degrees, sin_degrees

QUANTUM_MM = Decimal("0.01")
_ARC_SAMPLE_STEP_MM = Decimal("5")
_PI = Decimal("3.1415926535897932384626433832795028841971693993751")
_TWO = Decimal("2")


def _q(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM_MM, rounding=ROUND_HALF_UP)


def _pt(x: Decimal, y: Decimal) -> PlanPoint:
    return PlanPoint(x_mm=_q(x), y_mm=_q(y))


def _sub(a: PlanPoint, b: PlanPoint) -> tuple[Decimal, Decimal]:
    return a.x_mm - b.x_mm, a.y_mm - b.y_mm


def _length(dx: Decimal, dy: Decimal) -> Decimal:
    return (dx * dx + dy * dy).sqrt()


def _dist(a: PlanPoint, b: PlanPoint) -> Decimal:
    dx, dy = _sub(b, a)
    return _length(dx, dy)


class Contour(EngineModel):
    """Closed CCW loop of line/arc edges; see module docstring for bulges."""

    vertices: list[PlanPoint] = Field(min_length=3)
    bulges: list[Decimal | None] = Field(min_length=3)

    @model_validator(mode="after")
    def _lengths_match(self) -> "Contour":
        if len(self.bulges) != len(self.vertices):
            raise ValueError("bulges must match vertices one edge per vertex")
        return self

    @classmethod
    def rect(cls, width_mm: Decimal, height_mm: Decimal) -> "Contour":
        return cls(
            vertices=[
                PlanPoint(x_mm=Decimal(0), y_mm=Decimal(0)),
                PlanPoint(x_mm=width_mm, y_mm=Decimal(0)),
                PlanPoint(x_mm=width_mm, y_mm=height_mm),
                PlanPoint(x_mm=Decimal(0), y_mm=height_mm),
            ],
            bulges=[None] * 4,
        )

    @classmethod
    def trapezoid(
        cls,
        width_mm: Decimal,
        height_mm: Decimal,
        offset_left_mm: Decimal,
        offset_right_mm: Decimal,
    ) -> "Contour":
        """Rectangle with a sloped top: top-left/right corners inset inward.

        `offset_left_mm`/`offset_right_mm` move the top corners toward the
        interior horizontally; a centered trapezoid uses equal offsets.
        """
        return cls(
            vertices=[
                PlanPoint(x_mm=Decimal(0), y_mm=Decimal(0)),
                PlanPoint(x_mm=width_mm, y_mm=Decimal(0)),
                PlanPoint(x_mm=width_mm - offset_right_mm, y_mm=height_mm),
                PlanPoint(x_mm=offset_left_mm, y_mm=height_mm),
            ],
            bulges=[None] * 4,
        )

    @classmethod
    def arch_top(cls, width_mm: Decimal, height_mm: Decimal, rise_mm: Decimal) -> "Contour":
        """Rectangle whose top edge is an arc rising `rise_mm` above chord."""
        return cls(
            vertices=[
                PlanPoint(x_mm=Decimal(0), y_mm=Decimal(0)),
                PlanPoint(x_mm=width_mm, y_mm=Decimal(0)),
                PlanPoint(x_mm=width_mm, y_mm=height_mm),
                PlanPoint(x_mm=Decimal(0), y_mm=height_mm),
            ],
            bulges=[None, None, rise_mm, None],
        )


def signed_area(vertices: list[PlanPoint]) -> Decimal:
    """Shoelace area; positive when vertices are counter-clockwise."""
    total = Decimal(0)
    n = len(vertices)
    for i in range(n):
        a = vertices[i]
        b = vertices[(i + 1) % n]
        total += a.x_mm * b.y_mm - b.x_mm * a.y_mm
    return total / _TWO


def ensure_ccw(contour: Contour) -> Contour:
    """Return the contour wound CCW, reversing vertex/bulge order if needed."""
    if signed_area(contour.vertices) > 0:
        return contour
    n = len(contour.vertices)
    vertices = [contour.vertices[0]] + [contour.vertices[i] for i in range(n - 1, 0, -1)]
    # Reversed edge i runs vertices[n-i] -> vertices[n-i-1] of the original,
    # i.e. original edge (n-i-1); its sagitta flips sign (same arc, other
    # travel direction mirrors the bulge side).
    bulges = [contour.bulges[n - 1]] + [
        -b if b is not None else None for b in reversed(contour.bulges[: n - 1])
    ]
    return Contour(vertices=vertices, bulges=bulges)


def _edge(contour: Contour, index: int) -> tuple[PlanPoint, PlanPoint, Decimal | None]:
    n = len(contour.vertices)
    return (
        contour.vertices[index % n],
        contour.vertices[(index + 1) % n],
        contour.bulges[index % n],
    )


def arc_params(
    p0: PlanPoint, p1: PlanPoint, sagitta: Decimal
) -> tuple[PlanPoint, Decimal, Decimal]:
    """Center point, radius and span (deg) of the arc p0 -> p1.

    Positive sagitta bulges right of the directed chord; the center sits on
    the left at distance (radius - sagitta). Callers must ensure
    |sagitta| <= chord/2 (validated by `validate_contour`).
    """
    chord = _dist(p0, p1)
    half = chord / _TWO
    s = abs(sagitta)
    radius = (s * s + half * half) / (_TWO * s)
    mid_x = (p0.x_mm + p1.x_mm) / _TWO
    mid_y = (p0.y_mm + p1.y_mm) / _TWO
    dx, dy = _sub(p1, p0)
    # left unit normal of the directed chord
    nx, ny = -dy / chord, dx / chord
    offset = radius - s
    if sagitta > 0:
        cx, cy = mid_x + nx * offset, mid_y + ny * offset
    else:
        cx, cy = mid_x - nx * offset, mid_y - ny * offset
    span = _TWO * asin_degrees(half / radius)
    return _pt(cx, cy), radius, span


def arc_length(p0: PlanPoint, p1: PlanPoint, sagitta: Decimal) -> Decimal:
    _, radius, span = arc_params(p0, p1, sagitta)
    return radius * span * _PI / Decimal("180")


def edge_length(contour: Contour, index: int) -> Decimal:
    p0, p1, bulge = _edge(contour, index)
    if bulge:
        return arc_length(p0, p1, bulge)
    return _dist(p0, p1)


def _edge_tangent(contour: Contour, index: int, *, at_end: bool) -> tuple[Decimal, Decimal]:
    """Unit tangent of edge `index` at its start (or end), pointing along travel."""
    p0, p1, bulge = _edge(contour, index)
    dx, dy = _sub(p1, p0)
    if not bulge:
        length = _length(dx, dy)
        return dx / length, dy / length
    center, _, _ = arc_params(p0, p1, bulge)
    point = p1 if at_end else p0
    rx, ry = _sub(point, center)
    # Positive sagitta = right bulge = clockwise travel around the center;
    # CW tangent rotates the radius vector (x,y) -> (y,-x). CCW uses (-y,x).
    if bulge > 0:
        tx, ty = ry, -rx
    else:
        tx, ty = -ry, rx
    length = _length(tx, ty)
    return tx / length, ty / length


def interior_angle(contour: Contour, vertex_index: int) -> Decimal:
    """Interior angle at vertex i, in degrees — from edge tangents."""
    n = len(contour.vertices)
    d_in = _edge_tangent(contour, (vertex_index - 1) % n, at_end=True)
    d_out = _edge_tangent(contour, vertex_index, at_end=False)
    cross = d_in[0] * d_out[1] - d_in[1] * d_out[0]
    dot = d_in[0] * d_out[0] + d_in[1] * d_out[1]
    turn = atan2_degrees(cross, dot)  # signed left turn on the CCW loop
    return Decimal("180") - turn


def validate_contour(contour: Contour) -> list[str]:
    """Structural validation; returns human-readable failure reasons."""
    contour = ensure_ccw(contour)
    problems: list[str] = []
    n = len(contour.vertices)
    for i in range(n):
        p0, p1, bulge = _edge(contour, i)
        chord = _dist(p0, p1)
        if chord <= QUANTUM_MM:
            problems.append(f"edge {i}: zero-length segment")
            continue
        if bulge:
            if abs(bulge) * _TWO > chord:
                problems.append(f"edge {i}: arc sagitta exceeds half the chord")
    # Segment intersection: lines exact, arcs chord-sampled at 1 mm.
    samples = [edge_points(contour, i, step_mm=Decimal("1")) for i in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            if (i + 1) % n == j or (j + 1) % n == i:
                continue  # adjacent edges share a vertex legitimately
            for a in range(len(samples[i]) - 1):
                for b in range(len(samples[j]) - 1):
                    if _seg_intersects(
                        samples[i][a], samples[i][a + 1], samples[j][b], samples[j][b + 1]
                    ):
                        problems.append(f"edges {i} and {j} self-intersect")
                        return problems
    return problems


def _seg_intersects(a1: PlanPoint, a2: PlanPoint, b1: PlanPoint, b2: PlanPoint) -> bool:
    def orient(p: PlanPoint, q: PlanPoint, r: PlanPoint) -> Decimal:
        return (q.x_mm - p.x_mm) * (r.y_mm - p.y_mm) - (q.y_mm - p.y_mm) * (r.x_mm - p.x_mm)

    o1 = orient(a1, a2, b1)
    o2 = orient(a1, a2, b2)
    o3 = orient(b1, b2, a1)
    o4 = orient(b1, b2, a2)
    return (o1 * o2 < 0) and (o3 * o4 < 0)


def edge_points(
    contour: Contour, index: int, *, step_mm: Decimal = _ARC_SAMPLE_STEP_MM
) -> list[PlanPoint]:
    """Boundary points of one edge: endpoints for lines, chord-sampled arcs."""
    p0, p1, bulge = _edge(contour, index)
    if not bulge:
        return [_pt(p0.x_mm, p0.y_mm), _pt(p1.x_mm, p1.y_mm)]
    center, radius, span = arc_params(p0, p1, bulge)
    steps = max(2, int((radius * span * _PI / Decimal("180")) / step_mm) + 1)
    rx, ry = _sub(p0, center)
    start = atan2_degrees(ry, rx)
    sign = Decimal("-1") if bulge > 0 else Decimal("1")  # CW vs CCW travel
    points = [_pt(p0.x_mm, p0.y_mm)]
    for k in range(1, steps):
        angle = start + sign * span * Decimal(k) / Decimal(steps)
        points.append(
            _pt(
                center.x_mm + radius * cos_degrees(angle),
                center.y_mm + radius * sin_degrees(angle),
            )
        )
    points.append(_pt(p1.x_mm, p1.y_mm))
    return points


def contour_points(contour: Contour, *, step_mm: Decimal = _ARC_SAMPLE_STEP_MM) -> list[PlanPoint]:
    """Closed boundary as points: vertices exact, arcs chord-sampled."""
    contour = ensure_ccw(contour)
    points: list[PlanPoint] = []
    for i in range(len(contour.vertices)):
        edge = edge_points(contour, i, step_mm=step_mm)
        points.extend(edge[:-1])
    return points


def contour_area(vertices: list[PlanPoint], bulges: list[Decimal | None]) -> Decimal:
    """Exact area: shoelace over vertices + signed circular-segment areas."""
    area = signed_area(vertices)
    n = len(vertices)
    for i in range(n):
        s = bulges[i]
        if not s:
            continue
        p0 = vertices[i]
        p1 = vertices[(i + 1) % n]
        chord = _dist(p0, p1)
        half = chord / _TWO
        radius = (s * s + half * half) / (_TWO * abs(s))
        span_rad = _TWO * asin_degrees(half / radius) * _PI / Decimal("180")
        # Circular segment between chord and arc; a right-of-edge bulge on
        # a CCW loop expands the interior (outward), a left bulge shrinks it.
        segment = radius * radius * (span_rad - sin_degrees(span_rad * Decimal("180") / _PI)) / _TWO
        area += segment * (Decimal(1) if s > 0 else Decimal(-1))
    return area


def _offset_line(p0: PlanPoint, p1: PlanPoint, distance: Decimal) -> tuple[PlanPoint, PlanPoint]:
    """Line p0->p1 shifted `distance` to the left of its direction."""
    dx, dy = _sub(p1, p0)
    length = _length(dx, dy)
    nx, ny = -dy / length * distance, dx / length * distance
    return (
        PlanPoint(x_mm=p0.x_mm + nx, y_mm=p0.y_mm + ny),
        PlanPoint(x_mm=p1.x_mm + nx, y_mm=p1.y_mm + ny),
    )


def _line_intersect(a0: PlanPoint, a1: PlanPoint, b0: PlanPoint, b1: PlanPoint) -> PlanPoint | None:
    ax, ay = _sub(a1, a0)
    bx, by = _sub(b1, b0)
    det = ax * by - ay * bx
    if abs(det) < Decimal("1e-20"):
        return None
    cx, cy = _sub(b0, a0)
    t = (cx * by - cy * bx) / det
    return PlanPoint(x_mm=a0.x_mm + ax * t, y_mm=a0.y_mm + ay * t)


def _circle_line_intersect(
    center: PlanPoint, radius: Decimal, a0: PlanPoint, a1: PlanPoint, near: PlanPoint
) -> PlanPoint:
    """Circle ∩ line, choosing the intersection closest to `near`."""
    ax, ay = _sub(a1, a0)
    fx, fy = _sub(a0, center)
    a = ax * ax + ay * ay
    b = _TWO * (fx * ax + fy * ay)
    c = fx * fx + fy * fy - radius * radius
    disc = b * b - Decimal(4) * a * c
    if disc <= 0:
        return near
    root = disc.sqrt()
    best: PlanPoint | None = None
    best_d: Decimal | None = None
    for sign in (Decimal(1), Decimal(-1)):
        t = (-b + sign * root) / (_TWO * a)
        candidate = PlanPoint(x_mm=a0.x_mm + ax * t, y_mm=a0.y_mm + ay * t)
        d = _dist(candidate, near)
        if best_d is None or d < best_d:
            best, best_d = candidate, d
    return best if best is not None else near


def _circle_circle_intersect(
    c0: PlanPoint, r0: Decimal, c1: PlanPoint, r1: Decimal, near: PlanPoint
) -> PlanPoint:
    """Circle ∩ circle, choosing the intersection closest to `near`."""
    d = _dist(c0, c1)
    if d <= 0 or d > r0 + r1 or d < abs(r0 - r1):
        return near
    a = (r0 * r0 - r1 * r1 + d * d) / (_TWO * d)
    h_sq = r0 * r0 - a * a
    if h_sq < 0:
        return near
    h = h_sq.sqrt()
    ux, uy = _sub(c1, c0)
    ux, uy = ux / d, uy / d
    px, py = c0.x_mm + ux * a, c0.y_mm + uy * a
    first = PlanPoint(x_mm=px + uy * h, y_mm=py - ux * h)
    second = PlanPoint(x_mm=px - uy * h, y_mm=py + ux * h)
    return first if _dist(first, near) <= _dist(second, near) else second


def offset_contour(contour: Contour, distance_mm: Decimal) -> Contour:
    """Contour offset inward (left of each CCW-directed edge).

    Line edges slide along their left normal; arc edges keep their center
    and adjust radius (`r - d` for outward bulges, `r + d` for inward).
    New vertices are the intersections of adjacent offset edges, resolved
    nearest the original vertex.
    """
    contour = ensure_ccw(contour)
    n = len(contour.vertices)

    # Per-edge offset geometry: either a line pair or (center, radius, s).
    offset_lines: list[tuple[PlanPoint, PlanPoint] | None] = []
    offset_arcs: list[tuple[PlanPoint, Decimal, Decimal] | None] = []
    for i in range(n):
        p0, p1, bulge = _edge(contour, i)
        if not bulge:
            offset_lines.append(_offset_line(p0, p1, distance_mm))
            offset_arcs.append(None)
        else:
            center, radius, _ = arc_params(p0, p1, bulge)
            new_radius = radius - distance_mm if bulge > 0 else radius + distance_mm
            if new_radius <= QUANTUM_MM:
                raise ValueError(f"edge {i}: offset collapses the arc")
            offset_lines.append(None)
            offset_arcs.append((center, new_radius, bulge))

    vertices: list[PlanPoint] = []
    for i in range(n):
        vertex = contour.vertices[i]
        prev = (i - 1) % n
        line_a, arc_a = offset_lines[prev], offset_arcs[prev]
        line_b, arc_b = offset_lines[i], offset_arcs[i]
        if line_a is not None and line_b is not None:
            point = _line_intersect(line_a[0], line_a[1], line_b[0], line_b[1])
            if point is None:
                raise ValueError(f"vertex {i}: offset edges are parallel")
            vertices.append(_pt(point.x_mm, point.y_mm))
        elif arc_a is not None and line_b is not None:
            center, radius, _ = arc_a
            vertices.append(_circle_line_intersect(center, radius, line_b[0], line_b[1], vertex))
        elif line_a is not None and arc_b is not None:
            center, radius, _ = arc_b
            vertices.append(_circle_line_intersect(center, radius, line_a[0], line_a[1], vertex))
        else:
            assert arc_a is not None and arc_b is not None
            c0, r0, _ = arc_a
            c1, r1, _ = arc_b
            vertices.append(_circle_circle_intersect(c0, r0, c1, r1, vertex))

    # Offset sagitta: the offset arc keeps the same center; its sagitta
    # measured against the new chord shrinks by the same amount as radius.
    bulges: list[Decimal | None] = []
    for i in range(n):
        p0, p1, bulge = _edge(contour, i)
        if not bulge:
            bulges.append(None)
            continue
        center, radius, _ = arc_params(p0, p1, bulge)
        new_radius = radius - distance_mm if bulge > 0 else radius + distance_mm
        new_chord = _dist(vertices[i], vertices[(i + 1) % n])
        under = new_radius * new_radius - (new_chord / _TWO) ** 2
        if under <= 0:
            raise ValueError(f"edge {i}: offset degenerates the arc chord")
        new_sagitta = new_radius - under.sqrt()
        bulges.append(new_sagitta if bulge > 0 else -new_sagitta)
    return Contour(vertices=vertices, bulges=bulges)


def is_axis_aligned_rect(contour: Contour) -> bool:
    """True when the contour is a rectangle (arcs absent, 4 right angles)."""
    if len(contour.vertices) != 4 or any(bulge for bulge in contour.bulges):
        return False
    c = ensure_ccw(contour)
    v = c.vertices
    horizontal = all(v[i].y_mm == v[(i + 1) % 4].y_mm for i in (0, 2)) and all(
        v[i].x_mm == v[(i + 1) % 4].x_mm for i in (1, 3)
    )
    return horizontal
