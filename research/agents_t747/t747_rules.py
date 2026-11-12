"""R-T747-1 .. -3 1.0.0 (every villa): exterior paint faces by the owner paint rule (OWNER RULE PAINT 2026-11-12,
UP-FIN-PAINT-002 1.0.0: "paint = plaster area on the same faces, inside and outside ... lm for windows doors and
corners, so the Area is the same"; OWNER_NOTES_SIGMA 2026-10-21: exterior Sigma is not measured separately, it is the
exterior plaster area).

Physical element: the painted exterior face = the rendered facade face (storey band, parapet outer / inner above the
upturn / top, plinth, slab edge), per facade side and storey, minus the parts the drawing finishes otherwise.

R-T747-1 FACE (per render face id, once):
  1. paint m2 = the render m2 of the SAME face id, net of its openings (each hole once, in full, Q-73 A, on the face
     that holds it; never deducted again from the paint). The render face's state is carried: a HELD bound stays a
     bound, a blank face stays blank (never 0), a point stays a point.
  2. Deductions ONLY from the drawing, each named, per face:
       CLAD / TILED (printed: hatch, legend or note)       -> that area leaves the paint at both ends (determined)
       NOT_PRINTED_FINISH zone (a distinct surface drawn on the face, e.g. stone / quoin outlines, whose material is
       printed nowhere)                                     -> 0 .. zone: the paint low end drops by the zone only
     A face with no drawn zone has no deduction (no 'maybe clad'); a deduction larger than the face is refused.
  3. A boundary / fence wall face (Q-65, its own EXT.FENCE.* lines) is REFUSED here: it is not a facade face.
  4. Units: m2 only; a figure that reads as mm2 (> 10,000 m2 for one face) or a negative is refused.
R-T747-2 LINE / SIDE ROLL-UP: a line (or a side x storey group) = the sum of its paint faces, low and high apart;
  any blank face makes the group blank-with-part (the valued part is shown, the blank is named, never 0); the
  residual render - paint - deductions is 0 exactly per face, per side and per line.
R-T747-3 EDGES AS LM (never m2): opening edges per opening once and corners per arris once, each bound to ONE source
  ledger (arris once with the B4-09 beads); a developed (arched) outline governs a rectangle composition of the same
  opening; a door whose drawn frame covers the jambs has 0 jamb edge (T-746); an edge with no size is HELD blank.
"""
from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

RULE_IDS = ("R-T747-1", "R-T747-2", "R-T747-3")
VERSION = "1.0.0"
OWNER_RULE = "UP-FIN-PAINT-002 1.0.0 (OWNER RULE PAINT 2026-11-12) + OWNER_NOTES_SIGMA 2026-10-21"
ELEMENTS = ("STOREY", "PARAPET_OUTER", "PARAPET_INNER", "PARAPET_TOP", "PLINTH", "SLAB_EDGE")
DED_DETERMINED = ("CLAD", "TILED")
DED_ZONE = ("NOT_PRINTED_FINISH",)
MAX_FACE_M2 = Decimal("10000")
Q = Decimal("0.000001")


class RuleError(ValueError):
    pass


def D(x) -> Decimal:
    if x is None:
        raise RuleError("a missing value is HELD, not a number")
    if isinstance(x, bool):
        raise RuleError("not a number")
    if isinstance(x, float):
        x = repr(x)
    try:
        v = Decimal(str(x))
    except Exception as e:  # noqa: BLE001
        raise RuleError(f"not a number: {x!r}") from e
    if not v.is_finite():
        raise RuleError(f"not finite: {x!r}")
    return v


def q6(x) -> Decimal:
    return D(x).quantize(Q, rounding=ROUND_HALF_UP)


def _m2(x, name):
    v = D(x)
    if v < 0:
        raise RuleError(f"{name} negative")
    if v > MAX_FACE_M2:
        raise RuleError(f"{name} {v} reads as mm2, not m2")
    return v


# ---- R-T747-1 ------------------------------------------------------------------------------------------------------
def paint_face(face_id, element, render, *, deductions=(), boundary=False, unit="m2"):
    """render: (lo, hi) net m2 of the render face (holes already out) or None (blank face).
    deductions: [{"kind": CLAD|TILED|NOT_PRINTED_FINISH, "m2": x, "why": text}] drawn on THIS face.
    -> {face_id, element, render, paint, state, deductions, residual}"""
    if boundary:
        raise RuleError(f"{face_id}: a boundary / fence wall face is not a facade face (Q-65, EXT.FENCE.* lines)")
    if unit != "m2":
        raise RuleError(f"{face_id}: unit {unit!r} refused (m2 only)")
    if element not in ELEMENTS:
        raise RuleError(f"{face_id}: unknown facade element {element}")
    ded = []
    for d in deductions:
        k = d.get("kind")
        if k not in DED_DETERMINED + DED_ZONE:
            raise RuleError(f"{face_id}: deduction kind {k!r} is not a drawn finish (CLAD / TILED / zone)")
        if not d.get("why"):
            raise RuleError(f"{face_id}: every deduction names its drawing evidence")
        a = _m2(d.get("m2"), "deduction")
        if a == 0:
            raise RuleError(f"{face_id}: a zero deduction is no deduction")
        ded.append({"kind": k, "m2": q6(a), "why": d["why"]})
    if render is None:
        return {"face_id": face_id, "element": element, "render": None, "paint": None, "state": "BLANK",
                "deductions": ded, "residual": None,
                "why": "render face blank (HELD, no bound): paint blank, never 0"}
    lo, hi = _m2(render[0], "render low"), _m2(render[1], "render high")
    if lo > hi:
        raise RuleError(f"{face_id}: inverted render bound {lo} > {hi}")
    det = sum((d["m2"] for d in ded if d["kind"] in DED_DETERMINED), Decimal(0))
    zone = sum((d["m2"] for d in ded if d["kind"] in DED_ZONE), Decimal(0))
    if det + zone > lo:
        raise RuleError(f"{face_id}: deductions {det + zone} exceed the face {lo}")
    p_lo, p_hi = lo - det - zone, hi - det
    state = "POINT" if (p_lo == p_hi) else "BOUNDED"
    return {"face_id": face_id, "element": element, "render": (q6(lo), q6(hi)), "paint": (q6(p_lo), q6(p_hi)),
            "state": state, "deductions": ded,
            "residual": (q6(lo - p_lo - det - zone), q6(hi - p_hi - det)),
            "why": "paint = render of the same face" + ("" if not ded else " - drawn deductions")}


# ---- R-T747-2 ------------------------------------------------------------------------------------------------------
def roll_up(faces):
    """sum paint faces, low and high apart; blank faces named, never 0."""
    lo = hi = r_lo = r_hi = d_lo = d_hi = Decimal(0)
    blank, n = [], 0
    for f in faces:
        n += 1
        if f["paint"] is None:
            blank.append(f["face_id"])
            continue
        lo += f["paint"][0]
        hi += f["paint"][1]
        r_lo += f["render"][0]
        r_hi += f["render"][1]
        det = sum((d["m2"] for d in f["deductions"] if d["kind"] in DED_DETERMINED), Decimal(0))
        zone = sum((d["m2"] for d in f["deductions"] if d["kind"] in DED_ZONE), Decimal(0))
        d_lo += det + zone
        d_hi += det
    if n == 0:
        raise RuleError("an empty group is not a line")
    valued = n - len(blank)
    state = ("BLANK" if valued == 0 else "BLANK_PART" if blank else "POINT" if lo == hi else "BOUNDED")
    return {"faces": n, "blank_faces": blank, "state": state,
            "render": None if valued == 0 else (q6(r_lo), q6(r_hi)),
            "paint": None if valued == 0 else (q6(lo), q6(hi)),
            "deducted": (q6(d_lo), q6(d_hi)),
            "residual": None if valued == 0 else (q6(r_lo - lo - d_lo), q6(r_hi - hi - d_hi))}


# ---- R-T747-3 ------------------------------------------------------------------------------------------------------
def opening_edge(opening, sources):
    """sources: {name: {"lm": (lo, hi) | None, "basis": text}} for ONE opening from different ledgers.
    The governing source is chosen by basis rank (ARC_DEVELOPED > DRAWN_FRAME > RECTANGLE); the others are cited
    with their difference, never added. -> {opening, lm, source, basis, others: [{source, lm, diff}]}"""
    rank = {"ARC_DEVELOPED": 3, "DRAWN_FRAME": 2, "RECTANGLE": 1}
    if not sources:
        raise RuleError(f"{opening}: no edge source")
    for k, s in sources.items():
        if s.get("basis") not in rank:
            raise RuleError(f"{opening}: unknown edge basis {s.get('basis')!r} in {k}")
    best = max(sources, key=lambda k: (rank[sources[k]["basis"]], k))
    g = sources[best]
    lm = None if g["lm"] is None else (q6(g["lm"][0]), q6(g["lm"][1]))
    if lm is not None and lm[0] > lm[1]:
        raise RuleError(f"{opening}: inverted lm")
    others = []
    for k, s in sorted(sources.items()):
        if k == best:
            continue
        o = None if s["lm"] is None else (q6(s["lm"][0]), q6(s["lm"][1]))
        diff = None if (o is None or lm is None) else (q6(o[0] - lm[0]), q6(o[1] - lm[1]))
        others.append({"source": k, "lm": o, "basis": s["basis"], "diff": diff})
    return {"opening": opening, "lm": lm, "state": "HELD" if lm is None else
            ("POINT" if lm[0] == lm[1] else "BOUNDED"), "source": best, "basis": g["basis"], "others": others}


def sum_lm(edges):
    lo = hi = Decimal(0)
    held = []
    for e in edges:
        if e["lm"] is None:
            held.append(e["opening"])
            continue
        lo += e["lm"][0]
        hi += e["lm"][1]
    return {"lm": (q6(lo), q6(hi)), "held": held}
