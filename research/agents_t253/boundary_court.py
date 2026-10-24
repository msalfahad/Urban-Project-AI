"""T-253 BOUNDARY_COURT_V1 (research, unwired, stdlib only): the CONC.GROUND parts the drawings settle without the
consultant: the boundary-wall ground beam at natural ground, the court runs, the outer-ground datum of the exterior
ground beams and the annex depth conflict; the consultant rows narrowed to exact runs.

Physical elements (structural set p.3 ground-beams plan, p.13 "Ground Beams" sections, p.14 "TYPICAL BOUNDARY WALL";
architectural GF plan and section B-B; merged records T-065 / T-073 boundary members, T-214 structural tops, T-230
ends, T-242 ground ledger):

- BOUNDARY-WALL GROUND BEAM AT NATURAL GROUND (p.14 plan "GROUND BEAM (20x40)", section A-A: top at "N.G. LEVEL",
  dimension 40, 2 d14 + 3 d16, d8/20): the upper of the two boundary-wall beams. Its plan is the brick-hatched band of
  the ground-beams plan where no building stands on the plot line. One RUN = one straight leg of that band; a corner
  square belongs to exactly one run (the longer one). A run ends at the face of the member it meets in 3-D (a column
  or neck that runs from the footing up through natural ground, a pool wall that runs below the beam soffit, another
  beam at the same elevation); a footing (founded below the soffit) never ends it and is never crossed by its length.
  The brick wall below it and the lower G.B on its 80 x 30 base (the foundation-plan band, owner Q-28) share no
  concrete with it. The 20 x 30 boundary columns ("SEE ARCH PLAN") pass through it; with no column drawn the PHYSICAL
  band volume is settled and only its split between the beam line and the column line waits on the count.
- OUTER GROUND DATUM of an exterior ground beam (p.13 "for exterior walls": top "Ground Floor slab level", underside
  "Outer Normal ground level", depth "FOLLOW ARCH."): the natural ground the architectural drawings print outside the
  building. A finished paving drawn ON the natural ground (a court at +0.15 = 0.15 plain concrete on N.G.) is a
  finish, never the datum.
- COURT RUN: a ground beam with outside ground on both sides (or on one side and an unestablished panel on the
  other): no printed section applies; its length closes when both ends meet members, its section stays HELD.
- EXTERIOR DEPTH CONFLICT: the literal depth (top - datum) shallower than every printed ground-beam section while the
  printed exterior section draws more bar layers than that depth can hold: two printed sources disagree; the literal
  value is shown as one reading, the section reading has no value; never one picked.

Rules applied: R-CONC-OWN-1 (one owner per 3-D piece), the T-230 end rule, UP-QTY-STATUS-001 (missing never 0), the
no-assumptions rule (no default depth, no borrowed member), ERS s.3 (a notation's meaning before its arithmetic).
Statuses: CALCULATED / HELD / CONFLICT, as T-242; every function returns plain dicts.
"""
from __future__ import annotations

POLICY_ID = "BOUNDARY_COURT_V1"
DEFAULT_GUARD_CLASS = "UNWIRED_PRODUCER"   # research module: no released or candidate method imports it

CALCULATED = "CALCULATED"
HELD = "HELD"
CONFLICT = "CONFLICT"

# members that physically run through natural ground at the plot line (they can end a beam at N.G. in 3-D)
THROUGH_MEMBERS = {"COLUMN", "NECK", "POOL_WALL", "BEAM_SAME_LEVEL"}

UNITS = {"m": 1.0, "cm": 0.01, "mm": 0.001}


class BoundaryCourtError(ValueError):
    """A refused input: a default, a borrowed value, a length through a member, a held value shown as 0."""


def metres(v, unit):
    if unit not in UNITS:
        raise BoundaryCourtError(f"unknown unit {unit!r}")
    if v is None:
        raise BoundaryCourtError("a missing dimension is never converted (HELD, not 0)")
    return float(v) * UNITS[unit]


def _pos(v, name):
    if v is None:
        raise BoundaryCourtError(f"{name} missing: HELD, never 0 or a default")
    v = float(v)
    if v <= 0:
        raise BoundaryCourtError(f"{name} must be > 0 (got {v})")
    return v


# ---------------------------------------------------------------- band -> runs (uniform-width rectilinear band)
def _inside(pt, poly):
    x, y = pt
    c = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            xi = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if x < xi:
                c = not c
    return c


def band_runs(vertices, width, tol=1e-6):
    """Split one closed, axis-aligned band of uniform width into straight runs, each corner square in ONE run.

    vertices: the band outline (any unit, consistent); width: the drawn band width. Returns runs with axis, length
    (along the run, owned corners included), the corner squares it owns, and the two end faces (None where a corner
    joins it to another run). Sum of run length x width == band area (each piece once)."""
    w = _pos(width, "band width")
    raw = [(float(x), float(y)) for x, y in vertices]

    def snap(vals):              # merge drafting noise: coordinates within tol are one face
        out = {}
        for v in sorted(vals):
            hit = next((k for k in out if abs(k - v) <= tol), None)
            out[v] = v if hit is None else out[hit]
        return out
    sx, sy = snap([p[0] for p in raw]), snap([p[1] for p in raw])
    pts = [(sx[x], sy[y]) for x, y in raw]
    if len(pts) > 1 and pts[0] == pts[-1]:
        pts = pts[:-1]
    if len(pts) < 4:
        raise BoundaryCourtError("a band needs at least 4 vertices")
    for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]):
        if abs(x1 - x2) > tol and abs(y1 - y2) > tol:
            raise BoundaryCourtError("band outline not axis-aligned: split it by its drawn faces first")
    xs = sorted({p[0] for p in pts})
    ys = sorted({p[1] for p in pts})
    cells = {}
    for i in range(len(xs) - 1):
        for j in range(len(ys) - 1):
            cx, cy = (xs[i] + xs[i + 1]) / 2, (ys[j] + ys[j + 1]) / 2
            if _inside((cx, cy), pts):
                cells[(i, j)] = (xs[i + 1] - xs[i], ys[j + 1] - ys[j])
    for (i, j), (dx, dy) in cells.items():
        if abs(dx - w) > tol and abs(dy - w) > tol:
            raise BoundaryCourtError("band is not of uniform width: piece wider than the band in both directions")

    def along(k, axis):
        dx, dy = cells[k]
        return abs(dy - w) <= tol if axis == "X" else abs(dx - w) <= tol

    def chains(axis):
        out, seen = [], set()
        for key in sorted(cells):
            if key in seen or not along(key, axis):
                continue
            i, j = key
            run = [key]
            for step in (1, -1):
                k = 1
                while True:
                    nb = (i + step * k, j) if axis == "X" else (i, j + step * k)
                    if nb in cells and along(nb, axis):
                        run.append(nb) if step == 1 else run.insert(0, nb)
                        k += 1
                    else:
                        break
            seen.update(run)
            out.append(run)
        return out

    cand = [("X", c) for c in chains("X")] + [("Y", c) for c in chains("Y")]

    def length(axis, run):
        return sum(cells[k][0] if axis == "X" else cells[k][1] for k in run)

    corner = {k for k, (dx, dy) in cells.items() if abs(dx - w) <= tol and abs(dy - w) <= tol}
    # a w x w cell that only lies in a chain of length w on one axis is a plain run piece of the other axis
    owner = {}
    for c in corner:
        holders = [(length(a, r), a, tuple(r)) for a, r in cand if c in r and length(a, r) > w + tol]
        if not holders:
            holders = [(length(a, r), a, tuple(r)) for a, r in cand if c in r]
        holders.sort(key=lambda t: (-t[0], t[1]))
        owner[c] = (holders[0][1], holders[0][2])
    runs = []
    for a, r in cand:
        keep = [k for k in r if k not in corner or owner[k] == (a, tuple(r))]
        if not keep:
            continue
        L = length(a, keep)
        if L <= tol:
            continue
        first, last = keep[0], keep[-1]

        def face(k, start):
            i, j = k
            if a == "X":
                x = xs[i] if start else xs[i + 1]
                return ("X", x, ys[j], ys[j + 1])
            y = ys[j] if start else ys[j + 1]
            return ("Y", y, xs[i], xs[i + 1])

        def joined(k, start):
            i, j = k
            if k in corner:          # the run turns into a perpendicular run here: a corner, not an end face
                return True
            nb = ((i - 1, j) if start else (i + 1, j)) if a == "X" else ((i, j - 1) if start else (i, j + 1))
            return nb in cells
        runs.append({"axis": a, "length": L, "corners_owned": sum(1 for k in keep if k in corner),
                     "end_faces": [None if joined(first, True) else face(first, True),
                                   None if joined(last, False) else face(last, False)]})
    dedup = []
    for r in runs:
        if r not in dedup:
            dedup.append(r)
    area = sum(dx * dy for dx, dy in cells.values())
    total = sum(r["length"] for r in dedup) * w
    if abs(area - total) > max(tol, 1e-9 * area) * 10:
        raise BoundaryCourtError(f"run partition does not conserve the band area ({total} vs {area})")
    return {"runs": sorted(dedup, key=lambda r: -r["length"]), "band_area": area, "runs_area": total}


# ---------------------------------------------------------------- ends in 3-D
def end_in_3d(member_kind, member_top=None, member_bottom=None, beam_top=None, beam_bottom=None):
    """Does a beam at natural ground end on this member in 3-D? Levels in m (structural datums), None = not printed.

    A member in THROUGH_MEMBERS that spans the beam's band of levels ends it; a footing below the soffit never does
    (T-230); nothing at the end -> a free end, HELD (support not established); a member whose levels are not printed
    -> HELD with the item named."""
    if member_kind in (None, "NONE", "FREE_END"):
        return {"status": HELD, "ends": False, "why": "free end: no member at the end face; support not established"}
    if member_kind == "FOOTING":
        if member_top is not None and beam_bottom is not None and member_top < beam_bottom:
            return {"status": "REFUSED", "ends": False,
                    "why": "footing top below the beam soffit: a plan outline at another level never ends a beam"}
        return {"status": HELD, "ends": False, "why": "footing levels not printed against the beam: contact not shown"}
    if member_kind in THROUGH_MEMBERS:
        if None in (member_top, member_bottom, beam_top, beam_bottom):
            if member_kind in ("COLUMN", "NECK", "POOL_WALL") and beam_top is not None and beam_bottom is not None \
                    and member_top is None and member_bottom is None:
                return {"status": CALCULATED, "ends": True,
                        "why": f"{member_kind.lower()} runs from below the soffit to above the top at the plot line"}
            return {"status": HELD, "ends": False, "why": "member levels not printed: 3-D contact not shown"}
        ov = min(member_top, beam_top) - max(member_bottom, beam_bottom)
        if ov <= 0:
            return {"status": HELD, "ends": False,
                    "why": f"no level overlap ({ov:+.3f} m): the plan face is not a 3-D end"}
        return {"status": CALCULATED, "ends": True, "why": f"level overlap {ov:.3f} m"}
    if member_kind == "MASONRY":
        return {"status": HELD, "ends": False, "why": "masonry at the end face: not a structural support"}
    raise BoundaryCourtError(f"unknown member kind {member_kind!r}")


def refuse_length_through(run_length, face_to_face_length, tol=1e-6):
    """A run's length is between the faces it meets; a longer length runs through a member."""
    if run_length - face_to_face_length > tol:
        raise BoundaryCourtError(
            f"length {run_length} runs {run_length - face_to_face_length:.4f} through a member (face to face "
            f"{face_to_face_length})")
    return face_to_face_length


# ---------------------------------------------------------------- volumes
def boundary_run(run_id, length_m, b_m, d_m, d_source=None):
    """The beam solid b x D x L of one run; D only from a printed section (d_source names it), never a default."""
    L = _pos(length_m, "run length")
    b = _pos(b_m, "printed width")
    if d_m is None:
        return {"run": run_id, "status": HELD, "value_m3": None, "why": "depth not printed: HELD, never 0"}
    if not d_source:
        raise BoundaryCourtError("a depth without its printed source is a default: refused")
    d = _pos(d_m, "printed depth")
    return {"run": run_id, "status": CALCULATED, "value_m3": round(L * b * d, 6), "L_m": L, "b_m": b, "d_m": d,
            "d_source": d_source}


def column_share(n_columns, col_a_m, col_b_m, d_m):
    """Concrete of the boundary columns inside the beam's depth (R-CONC-OWN-1: the column line, billed through,
    owns it). With no printed count: HELD, no number; the band's physical volume does not change."""
    a, b, d = _pos(col_a_m, "column side a"), _pos(col_b_m, "column side b"), _pos(d_m, "beam depth")
    if n_columns is None:
        return {"status": HELD, "value_m3": None, "each_m3": round(a * b * d, 6),
                "why": "boundary column count / positions not printed ('SEE ARCH PLAN', none drawn)"}
    n = int(n_columns)
    if n < 0:
        raise BoundaryCourtError("negative column count")
    return {"status": CALCULATED, "value_m3": round(n * a * b * d, 6), "each_m3": round(a * b * d, 6)}


def boundary_line(runs, share):
    """Physical band concrete (sum of runs) and its split: beam line = band - column share (held while the count is)."""
    if any(r["status"] != CALCULATED for r in runs):
        return {"status": HELD, "band_m3": None, "beam_line_m3": None, "column_share": share,
                "why": "a run is HELD"}
    band = round(sum(r["value_m3"] for r in runs), 6)
    if share["status"] != CALCULATED:
        return {"status": HELD, "band_m3": band, "beam_line_m3": None, "column_share": share,
                "why": "band physically settled; beam / column split waits on the column count"}
    return {"status": CALCULATED, "band_m3": band, "beam_line_m3": round(band - share["value_m3"], 6),
            "column_share": share}


# ---------------------------------------------------------------- outer ground datum and exterior depth
def outer_ground_datum(readings):
    """readings: [{"level": float, "kind": "NATURAL" | "FINISHED_PAVING", "on": float|None, "source": str}].

    The datum is the NATURAL ground; a finished paving counts only to locate the natural ground under it ('on').
    Natural readings that disagree -> CONFLICT (both kept); no natural reading -> HELD (a finish is never the datum)."""
    if not readings:
        return {"status": HELD, "datum_m": None, "why": "no outer ground printed"}
    nat = []
    for r in readings:
        if not r.get("source"):
            raise BoundaryCourtError("a level reading without its drawing source is refused")
        if r["kind"] == "NATURAL":
            nat.append(round(float(r["level"]), 3))
        elif r["kind"] == "FINISHED_PAVING":
            if r.get("on") is not None:
                nat.append(round(float(r["on"]), 3))
        else:
            raise BoundaryCourtError(f"unknown ground kind {r['kind']!r}")
    vals = sorted(set(nat))
    if not vals:
        return {"status": HELD, "datum_m": None,
                "why": "only finished levels printed; the natural ground under them is not shown"}
    if len(vals) > 1:
        return {"status": CONFLICT, "datum_m": None, "readings_m": vals, "why": "natural ground printed differently"}
    return {"status": CALCULATED, "datum_m": vals[0], "why": f"{len([r for r in readings])} readings agree"}


def exterior_depth(top_m, datum, min_printed_depth_m, section_min_depth_m=None):
    """D = structural top - natural ground. CONFLICT when D is shallower than every printed ground-beam section
    (min_printed_depth_m) or than what the printed exterior section draws (section_min_depth_m, if a printed value
    exists; None = the section prints none): the literal value is kept as ONE reading, never adopted."""
    if top_m is None:
        return {"status": HELD, "value_m": None, "why": "structural top not printed"}
    if datum["status"] != CALCULATED:
        return {"status": datum["status"], "value_m": None, "why": "outer ground datum: " + datum["why"]}
    d = round(float(top_m) - datum["datum_m"], 4)
    if d <= 0:
        return {"status": CONFLICT, "value_m": None, "literal_m": d, "why": "top at or below the outer ground"}
    floor = max(x for x in (min_printed_depth_m, section_min_depth_m) if x is not None)
    if d < floor:
        return {"status": CONFLICT, "value_m": None, "literal_m": d,
                "why": f"literal depth {d:.2f} m below every printed section ({floor:.2f} m): source conflict"}
    return {"status": CALCULATED, "value_m": d, "why": "top - natural ground"}


def court_run(run_id, length_m, b_m, ends_ok, candidates_m):
    """A court run: length closed when both ends meet members; section never chosen (no printed section)."""
    L = _pos(length_m, "court run length")
    b = _pos(b_m, "printed width")
    if not candidates_m:
        return {"run": run_id, "status": HELD, "L_m": L, "low_m3": None, "high_m3": None,
                "why": "no printed section and no candidate"}
    lo, hi = min(candidates_m), max(candidates_m)
    return {"run": run_id, "status": HELD, "L_m": L, "length_closed": bool(ends_ok),
            "candidates_m": sorted(set(candidates_m)), "low_m3": round(L * b * lo, 6),
            "high_m3": round(L * b * hi, 6), "why": "court: no printed section"}


def policy_record():
    return {"policy_id": POLICY_ID, "guard_class": DEFAULT_GUARD_CLASS, "statuses": [CALCULATED, HELD, CONFLICT],
            "through_members": sorted(THROUGH_MEMBERS)}
