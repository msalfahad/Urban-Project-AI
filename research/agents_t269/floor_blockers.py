"""T-269 floor-area closure blockers that the drawings can settle (research module, not wired; any villa).

Three general checks, each returning a quantity with a status, or HELD (None, never 0) with the missing item named.

1. ARRIVING FLIGHT FOOT (R-T269-1). A plan may draw fewer goings than the governing riser count (owner Q-46 A: the
   section count governs; plan lines are a check). The top riser of an ARRIVING flight is then placed from its drawn
   first riser, the governing count n and the drawn going g (all drawn goings equal): s_top = s_first + (n - 1) * g
   toward the arrival. The undrawn strip between the last drawn nosing and the landing edge splits into the flight's
   missing treads (stair, not floor) and the landing's nosing band beyond the top riser (floor of the landing), using the
   nosing projection drawn on the same flight (nosing line minus riser line). Refused / HELD: no governing count, unequal
   drawn goings, a top riser beyond the printed landing edge (the flight would run into the landing: a design conflict),
   no drawn nosing offset (band HELD).
2. SIDE BAND OF A FLIGHT (R-T269-2). A closed narrow band beside a flight (balustrade / string / upstand) is floor
   only when the floor exists under it: the STRUCTURAL slab edge of the stair opening runs along the band's face on the
   flight side (the band stands on the slab) and no upstand / kerb (height, section, separate material) is printed. A
   slab edge along the band's outer face puts the band in the opening (not floor). No structural edge found, or both
   faces, or an upstand printed: HELD.
3. FLOOR UNDER A RISING STAIR ON THE LOWEST STOREY (R-T269-3). An element drawn OVERHEAD (above the plan's cut, beyond
   the cut symbol) never removes floor at this level: the floor under such treads is floor unless a closed element
   (wall, column, enclosure, door) is drawn under them on this plan. Treads drawn below the cut stand on or close to
   this floor; whether floor finish exists under them depends on the stair's structure (where the soffit leaves the
   floor), which only a section / structural detail gives: HELD without one.

Plus a pure overlap check: the tread union inside a floor piece (a piece with 0.000 m2 of treads is not blocked by a
tread rule).

Units: metres in, m2 out. No project names, layers, handles or sizes are built in.
"""

from __future__ import annotations

from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union

TOL = 0.002  # drawing noise in metres (2 mm); not a construction tolerance


def _held(reason, **kw):
    out = {"status": "HELD", "reason": reason}
    out.update(kw)
    return out


# ---------------------------------------------------------------------------------------------------------------- 1
def arriving_flight_foot(*, first_riser, drawn_risers, drawn_nosings, governing_risers, landing_edge, width):
    """Split the undrawn strip at the top of an ARRIVING flight.

    Positions are coordinates along the flight axis (metres), any direction: the arrival side is where landing_edge
    lies. first_riser: the drawn riser farthest from the arrival (the flight's first riser on this plan);
    drawn_risers / drawn_nosings: every drawn riser / nosing line of the flight; governing_risers: the riser count of the
    governing drawing (section), or None; landing_edge: the printed landing edge on the arrival side; width: flight
    width (m). Returns tread_m2 (missing treads: stair), landing_band_m2 (floor), strip_m2, top_riser, status."""
    if governing_risers is None:
        return _held("no governing riser count (section) for this flight")
    if not drawn_risers or len(drawn_risers) < 2:
        return _held("fewer than two drawn risers: the going is not drawn")
    sgn = 1.0 if landing_edge > first_riser else -1.0
    rs = sorted(drawn_risers, key=lambda s: sgn * s)
    goings = [abs(b - a) for a, b in zip(rs, rs[1:])]
    g = sum(goings) / len(goings)
    if max(goings) - min(goings) > TOL:
        return _held("drawn goings unequal", goings=[round(x, 4) for x in goings])
    if abs(rs[0] - first_riser) > TOL:
        return _held("first_riser is not the drawn riser farthest from the arrival")
    if governing_risers < len(rs):
        return _held("governing count below the drawn riser count: the plan and the section conflict the other way")
    top = first_riser + sgn * (governing_risers - 1) * g
    last_drawn = rs[-1]
    over = sgn * (top - landing_edge)
    if over > TOL:
        return _held("top riser beyond the printed landing edge (the flight runs into the landing): design conflict",
                     top_riser=round(top, 4), overshoot_m=round(over, 4))
    # nosing projection drawn on this flight: every nosing lies |p| beyond a riser toward the flight's start
    proj = None
    if drawn_nosings:
        offs = []
        for n in drawn_nosings:
            d = min(rs, key=lambda r: abs(r - n))
            offs.append(-sgn * (n - d))
        if offs and max(offs) - min(offs) <= TOL and min(offs) > 0:
            proj = sum(offs) / len(offs)
    # visible top edge of the last drawn tread = the nosing of the last drawn riser's tread (drawn), else the riser
    last_visible = last_drawn - sgn * (proj or 0.0)
    strip = abs(landing_edge - last_visible) * width
    missing = governing_risers - len(rs)
    if proj is None:
        if missing == 0:
            return {"status": "DRAWN", "tread_m2": 0.0, "landing_band_m2": round(strip, 6), "strip_m2": round(strip, 6),
                    "top_riser": round(top, 4), "going": round(g, 4), "missing_risers": 0}
        return _held("no drawn nosing projection on this flight: the landing band beyond the top riser is not set",
                     tread_m2=round(missing * g * width, 6), strip_m2=round(strip, 6), top_riser=round(top, 4))
    # the landing's own nosing projects beyond the top riser by the same projection, never beyond the landing edge
    landing_visible = top - sgn * proj
    tread = abs(landing_visible - last_visible) * width
    band = strip - tread
    if band < -1e-9:
        return _held("landing nosing would lie beyond the strip", top_riser=round(top, 4))
    return {"status": "DERIVED", "tread_m2": round(tread, 6), "landing_band_m2": round(band, 6),
            "strip_m2": round(strip, 6), "top_riser": round(top, 4), "going": round(g, 4), "nosing_m": round(proj, 4),
            "missing_risers": missing}


# ---------------------------------------------------------------------------------------------------------------- 2
def side_band_floor(band, flight, slab_edges, *, upstand_printed=False, cover=0.9):
    """band, flight: shapely Polygons on one plan frame (metres). slab_edges: LineStrings of the STRUCTURAL slab edge
    of the opening in the same frame. Returns floor_m2 (band area when it stands on the slab, 0.0 when it lies in the
    opening) and status, or HELD."""
    if band is None or band.is_empty or flight is None or flight.is_empty:
        return _held("band or flight outline missing")
    if upstand_printed:
        return _held("an upstand / kerb is printed: the floor stops at its face (finish detail needed)")
    if not slab_edges:
        return _held("no structural slab edge drawn along the band")
    # the band face shared with (touching) the flight = inner face; the opposite long face = outer face
    ring = LineString(band.exterior.coords)
    segs = [LineString([a, b]) for a, b in zip(ring.coords, list(ring.coords)[1:])]
    inner = [s for s in segs if s.length > TOL and s.distance(flight) <= TOL and
             s.buffer(TOL).intersection(flight.exterior).length >= cover * s.length - TOL]
    if not inner:
        return _held("the band does not run along the flight")
    inner = max(inner, key=lambda s: s.length)
    outer = max((s for s in segs if s.distance(inner) > TOL), key=lambda s: s.length, default=None)
    edges = unary_union(slab_edges)

    def covered(seg):
        return edges.intersection(seg.buffer(TOL, cap_style=2)).length >= cover * seg.length

    on_inner, on_outer = covered(inner), (outer is not None and covered(outer))
    if on_inner and not on_outer:
        return {"status": "ON_SLAB", "floor_m2": round(band.area, 6), "slab_edge_on": "flight side"}
    if on_outer and not on_inner:
        return {"status": "IN_OPENING", "floor_m2": 0.0, "slab_edge_on": "outer face"}
    return _held("structural slab edge on both faces or on neither", on_inner=on_inner, on_outer=on_outer)


# ---------------------------------------------------------------------------------------------------------------- 3
def floor_under_rising_stair(face, flights, closed_under=()):
    """Lowest storey. face: Polygon; flights: [{id, quads: [Polygon], drawn_overhead: bool}]; closed_under: Polygons
    of closed elements drawn on THIS plan (walls, columns, enclosures). Returns per flight floor_m2 (overhead, nothing
    closed under) or HELD (below the cut, or overhead with a closed element under it), and the totals."""
    closed = unary_union(list(closed_under)) if closed_under else None
    rows, floor, held = [], 0.0, 0.0
    union_all = unary_union([q for f in flights for q in f["quads"]]).intersection(face)
    seen = None
    for f in flights:
        if not f.get("quads"):
            rows.append({"flight": f["id"], **_held("no tread outline")})
            continue
        p = unary_union(f["quads"]).intersection(face)
        if seen is not None:
            p = p.difference(seen)  # two flights over one point counted once
        seen = p if seen is None else seen.union(p)
        a = p.area
        if f.get("drawn_overhead") is None:
            rows.append({"flight": f["id"], "m2": round(a, 6), **_held("cut position not drawn")})
            held += a
        elif not f["drawn_overhead"]:
            rows.append({"flight": f["id"], "m2": round(a, 6),
                         **_held("drawn below the cut: floor under it depends on the stair structure (section)")})
            held += a
        elif closed is not None and p.intersection(closed).area > 1e-6:
            rows.append({"flight": f["id"], "m2": round(a, 6), **_held("a closed element is drawn under it")})
            held += a
        else:
            rows.append({"flight": f["id"], "m2": round(a, 6), "status": "FLOOR_UNDER_OVERHEAD", "floor_m2": round(a, 6)})
            floor += a
    return {"rows": rows, "treads_m2": round(union_all.area, 6), "floor_m2": round(floor, 6), "held_m2": round(held, 6)}


# ---------------------------------------------------------------------------------------------------------------- 4
def treads_in_piece(piece, quads):
    """m2 of the tread union inside a floor piece (0.0 = no tread rule applies to that piece)."""
    if piece is None or piece.is_empty:
        return None
    if not quads:
        return 0.0
    return round(unary_union(list(quads)).intersection(piece).area, 6)


def rect(x0, y0, x1, y1):
    return Polygon([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
