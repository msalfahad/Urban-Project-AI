"""T-444 rules (pure; shapely only for the plan partition): a ground-slab cell that holds a lift shaft, bound to its own
pieces. Method for every villa without a basement whose lift pit stands on its own raft (LIFT_STRUCTURE_V1, T-401).

R-T444-1  ONE PARTITION: the cell's outline is cut into pieces (slab PANEL, lift SHAFT, pit RING band, COLUMN outline,
          ground-BEAM strip); the pieces re-add to the outline to 1e-4 m2, or the cell is refused (no piece unnamed).
R-T444-2  SHAFT = LIFT PIT: the area inside the pit ring's inner face is the pit; its floor is the raft top (no slab of its
          own, T-401 p.14). Owner LIFT_PIT (the raft line); never ground slab.
R-T444-3  RING = PIT WALL: the band between the ring faces, net of the column outlines, is the pit wall (owner LIFT_PIT
          walls line, HELD while its height is held). Never ground slab, never ground beam.
R-T444-4  LIFT COLUMN, NOT FREE: a column outline that stands on the pit ring (or touches it) is a lift column: owned by
          its column / neck lines and cut out of the cell. A column read as 'free-standing' inside the cell is not a
          reason to hold the slab panels around it.
R-T444-5  SLAB VALUE = sum(PANEL area) x printed T. T not printed -> HELD (None), never 0, never a default.
R-T444-6  ONE OWNER: every piece has exactly one owner; a piece id claimed by another ledger (lift-pit lines, other GS
          parts) is a double and is refused.
R-T444-7  LEVEL BAND: a plan overlap with a solid in another level band (raft, footing, strap at founding level under
          the slab on grade) is not a deduction; only a solid in the slab's own band is (T-356 rule).
"""

from __future__ import annotations

KINDS = ("PANEL", "SHAFT", "RING", "COLUMN", "BEAM")
OWNER = {"PANEL": "GROUND_SLAB", "SHAFT": "LIFT_PIT_FLOOR=RAFT_TOP", "RING": "LIFT_PIT_WALLS",
         "COLUMN": "COLUMN/NECK", "BEAM": "GROUND_BEAM"}
TOL = 1e-4


class Refused(ValueError):
    pass


def _area(x):
    if not isinstance(x, (int, float)) or x < 0:
        raise Refused(f"area must be a non-negative number in m2, got {x!r}")
    if x > 1e4:
        raise Refused(f"area {x} m2 is not a villa slab cell (mm2 given?)")
    return float(x)


# ---------------------------------------------------------------- plan partition (R-T444-1 .. -4)
def partition(outer, shaft, ring_outer, columns=(), beams=(), unit_m=1.0):
    """Cut a cell outline (shapely polygons, any unit; unit_m = metres per drawing unit) into pieces.

    shaft = the ring's inner outline (pit), ring_outer = the ring's outer outline, columns / beams = outlines.
    Returns a list of {"id", "kind", "area_m2"}. Order of precedence: column > beam > shaft > ring > panel."""
    from shapely.ops import unary_union
    k = unit_m * unit_m
    if not ring_outer.contains(shaft):
        raise Refused("the pit (ring inner face) must lie inside the ring outer face")
    pieces, taken = [], None

    def take(kind, ident, g):
        nonlocal taken
        part = g.intersection(outer) if taken is None else g.intersection(outer).difference(taken)
        taken = part if taken is None else unary_union([taken, part])
        if part.area * k > TOL / 10:
            pieces.append({"id": ident, "kind": kind, "area_m2": round(part.area * k, 6)})

    for i, c in enumerate(columns, 1):
        take("COLUMN", f"COL-{i}", c)
    for i, b in enumerate(beams, 1):
        take("BEAM", f"GB-{i}", b)
    take("SHAFT", "SHAFT", shaft)
    take("RING", "RING", ring_outer.difference(shaft))
    take("PANEL", "PANEL", outer)
    readd(pieces, outer.area * k)
    return pieces


def lift_columns(columns, ring_outer, tol=1e-6):
    """R-T444-4: columns that touch or overlap the ring are lift columns (never 'free')."""
    return [i for i, c in enumerate(columns) if c.distance(ring_outer) <= tol]


# ---------------------------------------------------------------- checks
def readd(pieces, outer_m2):
    """R-T444-1: the pieces re-add to the outline."""
    s = sum(_area(p["area_m2"]) for p in pieces)
    if abs(s - _area(outer_m2)) > TOL:
        raise Refused(f"pieces re-add to {s:.6f} m2, outline {outer_m2:.6f} m2: unnamed piece")
    return round(s, 6)


def owners(pieces, other_ledgers=None):
    """R-T444-2 / -3 / -6: one owner per piece; ids claimed by another ledger are refused."""
    out = {}
    for p in pieces:
        if p["kind"] not in KINDS:
            raise Refused(f"{p['id']}: unknown kind {p['kind']!r}")
        if p["id"] in out:
            raise Refused(f"{p['id']}: listed twice")
        out[p["id"]] = OWNER[p["kind"]]
    for name, ids in (other_ledgers or {}).items():
        for i in ids:
            if i in out and not _same_owner(out[i], name):
                raise Refused(f"{i}: owned by {out[i]} here and claimed by ledger {name}: double")
    return out


def _same_owner(owner, ledger):
    """other_ledgers keys are owner names of OWNER (e.g. 'LIFT_PIT_FLOOR=RAFT_TOP' for the lift-pit raft ledger)."""
    if ledger not in OWNER.values():
        raise Refused(f"unknown ledger owner {ledger!r}")
    return owner == ledger


def slab_value(pieces, t_m):
    """R-T444-5: m3 of the slab panels; None (HELD) when T is not printed."""
    a = sum(_area(p["area_m2"]) for p in pieces if p["kind"] == "PANEL")
    if t_m is None:
        return {"area_m2": round(a, 6), "t_m": None, "m3": None, "state": "HELD", "missing": "slab thickness"}
    if not isinstance(t_m, (int, float)) or not 0.05 <= t_m <= 0.40:
        raise Refused(f"slab thickness {t_m!r} m is not a printed slab-on-grade thickness (cm or mm given?)")
    return {"area_m2": round(a, 6), "t_m": t_m, "m3": round(a * t_m, 6), "state": "VALUED"}


def check_value(value_m3, pieces, t_m):
    """Refuse a cell value that carries shaft / ring / column / beam area (the engine's free-column reading)."""
    if value_m3 is None:
        return "HELD"
    if value_m3 == 0:
        raise Refused("a held cell valued 0: HELD is None, never 0")
    sv = slab_value(pieces, t_m)
    extra = round(value_m3 - sv["m3"], 6)
    if abs(extra) <= TOL * t_m:
        return "EQUAL"
    named = {k: round(sum(p["area_m2"] for p in pieces if p["kind"] == k) * t_m, 6) for k in ("SHAFT", "RING", "COLUMN", "BEAM")}
    raise Refused(f"cell value {value_m3} m3 differs from its panels {sv['m3']} m3 by {extra:+.6f}: "
                  f"carries non-slab pieces (shaft {named['SHAFT']}, ring {named['RING']}, columns {named['COLUMN']}, "
                  f"beam strips {named['BEAM']} m3 at T)")


def overlap_deducted(slab_band, other_band):
    """R-T444-7: deduct a plan overlap only when the two solids share a level band ((bottom, top) in m)."""
    for b in (slab_band, other_band):
        if b is None or len(b) != 2 or b[0] is None or b[1] is None:
            raise Refused("a level band with a missing level cannot decide a deduction: HELD")
        if b[0] >= b[1]:
            raise Refused(f"level band {b} has bottom >= top")
    return min(slab_band[1], other_band[1]) - max(slab_band[0], other_band[0]) > 0


# ---------------------------------------------------------------- lane I proposal and comparison term
def proposal(line_id, pieces, t_m, engine_net_m2, engine_in_cell):
    """Lane I proposal for the cell's line: value = own panels x T; the engine net reconciled piece by piece.

    engine_in_cell: {kind: m2 of that kind inside the engine's net cell} (what the engine's net carries)."""
    sv = slab_value(pieces, t_m)
    carried = round(sum(engine_in_cell.get(k, 0.0) for k in KINDS), 6)
    if abs(carried - engine_net_m2) > TOL:
        raise Refused(f"engine net {engine_net_m2} m2 not reconciled by its pieces ({carried} m2)")
    if abs(engine_in_cell.get("PANEL", 0.0) - sv["area_m2"]) > TOL:
        raise Refused("engine cell panels differ from the own panels: the binding is not one-to-one")
    out_terms = {k: round(v, 6) for k, v in engine_in_cell.items() if k != "PANEL" and v > 0}
    return {"line_id": line_id, "from": {"state": "HELD", "bound_m2": engine_net_m2},
            "to": {"state": sv["state"], "area_m2": sv["area_m2"], "t_m": t_m, "m3": sv["m3"],
                   "evidence": "DRAWING-CONFIRMED (VERIFIED only after the Checker re-measure)"},
            "out_of_line_m2": out_terms, "out_of_line_owner": {k: OWNER[k] for k in out_terms},
            "held_part_m3": None if sv["m3"] is not None else "ALL", "never_zero": True}


def term_class(held_term_m3, engine_m3, freelancer_panels_m3):
    """The comparison term after the cell is valued: the HELD term becomes a value difference on the same panels."""
    if engine_m3 is None:
        return {"class": "HELD", "m3": held_term_m3}
    d = round(engine_m3 - freelancer_panels_m3, 6)
    return {"class": "AGREE" if abs(d) <= 1e-6 else "UNRESOLVED", "m3": d, "was_held_m3": held_term_m3}
