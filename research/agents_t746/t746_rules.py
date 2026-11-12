"""T-746 PAINT AT OPENING EDGES AS LM (every villa; research, unwired: no method, candidate or default reads this module).

Owner rule 2026-11-12 (main chat; board top note 'OWNER RULE 2026-11-12 PAINT'; AGENT_BRIEF 'Paint area'): "... the
difference is with the corners outside maybe only and lm for windows doors and corners, so the Area is the same."
UP-FIN-PAINT-002 1.0.0 (rules/rulebook/URBAN_COMPANY_RULEBOOK_1.2.0.json) param 'edges' = LM_ITEMS_NOT_AREA: "window /
door edges are lm lines beside the m2, never extra paint area". Its 'not_given' left the reveal (return) reading open;
the Lead ruled it on the board row T-746 (2026-11-12 16:20, no owner question): reading B, the painted return of a
door / window is an lm item per opening, never paint m2. This module applies that ruling; it states no new rule value,
so no rule version is added (the stale 'not_given' sentence is named for the next rulebook version, never edited).

PHYSICAL ELEMENT: the return (reveal) of an opening = the strip of wall surface inside the opening, from one wall face
to the frame (or through the wall for a door), along both jambs and the head (and the sill where it is a painted
surface). Its LENGTH is 2 x height + width (+ width for a painted sill); its depth is the wall (or reveal) depth.

R-T746-1  EDGE LM. Per opening and side: painted edge lm = 2 x h + w (+ w for a sill only when the drawing shows the sill
          as a painted surface; an external sill is its own item). Status:
            PAINT_LM       every term drawn / owner-approved and the return is a painted plastered surface
            BOUNDED        a named physical extreme gives 0 at the low end (frame covering the whole return, or a
                           tiled reveal between two wet rooms, neither printed): 0 .. L, the cause carried
            NO_PAINT_EDGE  the drawing shows no painted return: the frame flush with the wall face (depth 0), the
                           return tiled, or a frame covering the whole return DRAWN: 0, a determined zero, named
            HELD           a width or height not established: blank, never 0
          Per component (edge_parts): jambs 2 x h and head w are judged apart. A door block whose frame posts are
          closed rectangles over the full wall depth at both jambs (plan DXF, by handle; the wall depth equal to the
          measured wall) DRAWS the frame over the whole jamb reveal: jambs 0 (FRAME_COVERS_RETURN_DRAWN). A plan does
          not draw the head member: the head stays 0 .. w (FRAME_COVERAGE_NOT_PRINTED) until a door section / elevation
          shows it. Never a default frame depth.
          Inputs in m; a value above 10 m is refused as mm; a negative or missing size is never a number.
R-T746-2  RETURN LINE RESTATED. A FIN.PAINT return line (one plastered return face) carries paint m2 = 0 under reading
          B (the area moved to the lm item, not dropped: a determined zero with its lm beside it); its plaster m2 is
          untouched. Identity check: plaster m2 = depth x the return's full lm (2h + w), to 0.000001; a line whose
          plaster does not satisfy it is refused (the lm would not belong to that face). A blank plaster return gives a
          HELD lm (blank), never 0. One opening binds one return line, one line one opening.
R-T746-3  TOTALS. paint m2 after = paint m2 before - the return faces' paint m2 (per end, scenario-paired); the
          residual (after recomputed from the faces - stated after) must be 0 and is reported.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

RULE_IDS = ("R-T746-1", "R-T746-2", "R-T746-3")
OWNER_RULE = "UP-FIN-PAINT-002 1.0.0 param 'edges' (LM_ITEMS_NOT_AREA); Lead ruling T-746 reading B"
STATUSES = ("PAINT_LM", "BOUNDED", "NO_PAINT_EDGE", "HELD")
LOW_CAUSES = ("FRAME_COVERAGE_NOT_PRINTED", "WET_BOTH_SIDES_TILE_NOT_ESTABLISHED")
ZERO_CAUSES = ("FRAME_FLUSH_NO_RETURN", "TILED_RETURN", "FRAME_COVERS_RETURN_DRAWN")
KINDS = ("DOOR", "WINDOW", "ARCH", "GATE")
MAX_M = Decimal("10")


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
    return D(x).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)


def _m(x, name):
    v = D(x)
    if v < 0:
        raise RuleError(f"{name} negative")
    if v > MAX_M:
        raise RuleError(f"{name} {v} looks like mm, not m")
    return v


# ---- R-T746-1 ------------------------------------------------------------------------------------------------------
def edge_lm(kind, width, height, *, painted_sill=False, zero_cause=None, low_cause=None):
    """painted return edge of one opening side. width / height in m or None (not established).
    zero_cause: the drawing shows no painted return (ZERO_CAUSES) -> NO_PAINT_EDGE 0.
    low_cause: a named, unprinted physical extreme gives 0 at the low end (LOW_CAUSES) -> BOUNDED 0 .. L.
    -> {"status", "lm": (lo, hi) | None, "gross_lm": L | None, "cause", "why"}"""
    if kind not in KINDS:
        raise RuleError(f"unknown opening kind {kind}")
    if zero_cause is not None and zero_cause not in ZERO_CAUSES:
        raise RuleError(f"unknown zero cause {zero_cause}")
    if low_cause is not None and low_cause not in LOW_CAUSES:
        raise RuleError(f"unknown low cause {low_cause}")
    if zero_cause and low_cause:
        raise RuleError("a determined zero and a bound low cannot both hold")
    if painted_sill and kind in ("DOOR", "ARCH", "GATE"):
        raise RuleError("a door / arch / gate has no sill return")
    if width is None or height is None:
        return {"status": "HELD", "lm": None, "gross_lm": None, "cause": "SIZE_NOT_ESTABLISHED",
                "why": "width or height not established: the edge lm is HELD (blank), never 0"}
    w, h = _m(width, "width"), _m(height, "height")
    if w == 0 or h == 0:
        raise RuleError("a zero-size opening is not an opening (missing is HELD, not 0)")
    gross = 2 * h + w + (w if painted_sill else D(0))
    if zero_cause:
        return {"status": "NO_PAINT_EDGE", "lm": (q6(0), q6(0)), "gross_lm": q6(gross), "cause": zero_cause,
                "why": "the drawing shows no painted return here: 0 lm, a determined zero"}
    if low_cause:
        return {"status": "BOUNDED", "lm": (q6(0), q6(gross)), "gross_lm": q6(gross), "cause": low_cause,
                "why": "low end 0 = the named physical extreme (not printed); high = the full return length"}
    return {"status": "PAINT_LM", "lm": (q6(gross), q6(gross)), "gross_lm": q6(gross), "cause": None,
            "why": "2 x h + w" + (" + sill w" if painted_sill else "") + " of a painted plastered return"}


def edge_parts(kind, width, height, *, jambs=None, head=None, sill=False):
    """R-T746-1 per component: jambs (2 x h) and head (w), each painted (None), a ZERO_CAUSES cause (the drawing shows
    no painted surface on that component) or a LOW_CAUSES cause (0 .. full, not printed); sill: False (no painted sill),
    True (painted) or a cause. -> the edge_lm record + "parts": [{part, gross, lm, cause}]."""
    if kind not in KINDS:
        raise RuleError(f"unknown opening kind {kind}")
    if sill is not False and kind in ("DOOR", "ARCH", "GATE"):
        raise RuleError("a door / arch / gate has no sill return")
    if width is None or height is None:
        return dict(edge_lm(kind, None, None), parts=[])
    w, h = _m(width, "width"), _m(height, "height")
    if w == 0 or h == 0:
        raise RuleError("a zero-size opening is not an opening (missing is HELD, not 0)")
    comp = [("JAMBS", 2 * h, jambs), ("HEAD", w, head)]
    if sill is not False:
        comp.append(("SILL", w, None if sill is True else sill))
    parts, lo, hi, causes = [], D(0), D(0), []
    for name, g, c in comp:
        if c is None:
            pl = (g, g)
        elif c in ZERO_CAUSES:
            pl = (D(0), D(0))
        elif c in LOW_CAUSES:
            pl = (D(0), g)
        else:
            raise RuleError(f"unknown cause {c}")
        if c:
            causes.append(f"{name} {c}")
        lo, hi = lo + pl[0], hi + pl[1]
        parts.append({"part": name, "gross": str(q6(g)), "lm": [str(q6(pl[0])), str(q6(pl[1]))], "cause": c})
    gross = sum((D(p["gross"]) for p in parts), D(0))
    if hi == 0:
        status = "NO_PAINT_EDGE"
    elif lo != hi:
        status = "BOUNDED"
    else:
        status = "PAINT_LM"
    return {"status": status, "lm": (q6(lo), q6(hi)), "gross_lm": q6(gross), "cause": "; ".join(causes) or None,
            "why": "per component: " + ", ".join(f"{p['part']} {p['lm'][0]} .. {p['lm'][1]}" for p in parts),
            "parts": parts}


# ---- R-T746-2 ------------------------------------------------------------------------------------------------------
def restate_return_line(plaster_m2, depth, edge):
    """one FIN.PAINT return line under reading B. plaster_m2: (lo, hi), a number or None (blank face).
    -> {"paint_m2_after": (0, 0) | None, "lm": edge lm, "status", "why"}"""
    if plaster_m2 is None:
        if edge["status"] != "HELD":
            raise RuleError("a blank plaster return cannot carry a determined edge lm")
        return {"paint_m2_after": None, "lm": None, "status": "HELD",
                "why": "plaster return blank: paint m2 and lm both HELD by name (never 0)"}
    lo, hi = (plaster_m2 if isinstance(plaster_m2, (tuple, list)) else (plaster_m2, plaster_m2))
    lo, hi = D(lo), D(hi)
    if lo < 0 or hi < lo:
        raise RuleError("plaster range not (low <= high), or negative")
    if edge["status"] == "HELD":
        raise RuleError("a valued plaster return with an unknown edge: the sizes disagree, refuse")
    t = _m(depth, "depth")
    if t == 0:
        raise RuleError("a plastered return of depth 0 does not exist")
    full = q6(t * edge["gross_lm"])
    if q6(hi) != full:
        raise RuleError(f"plaster {hi} != depth {t} x return lm {edge['gross_lm']} = {full}: not this face")
    return {"paint_m2_after": (q6(0), q6(0)), "lm": edge["lm"], "status": edge["status"],
            "why": "reading B: the return is an lm item, its paint m2 moves to the lm line (determined 0, not dropped)"}


def bind_once(pairs):
    """[(opening_id, line_id)] -> refuses an opening on two lines or a line on two openings."""
    seen_o, seen_l = {}, {}
    for o, ln in pairs:
        if o in seen_o:
            raise RuleError(f"opening {o} bound to two lines ({seen_o[o]}, {ln})")
        if ln in seen_l:
            raise RuleError(f"line {ln} bound to two openings ({seen_l[ln]}, {o})")
        seen_o[o], seen_l[ln] = ln, o
    return True


# ---- R-T746-3 ------------------------------------------------------------------------------------------------------
def paint_after(before, return_faces_paint):
    """before: (lo, hi) paint m2; return_faces_paint: [(lo, hi)] of the return faces inside `before`.
    -> {"after": (lo, hi), "removed": (lo, hi)}; refuses a negative result."""
    b0, b1 = D(before[0]), D(before[1])
    r0 = sum((D(x[0]) for x in return_faces_paint), D(0))
    r1 = sum((D(x[1]) for x in return_faces_paint), D(0))
    a0, a1 = b0 - r0, b1 - r1
    if a0 < 0 or a1 < 0:
        raise RuleError("return paint larger than the total it is part of")
    return {"after": (q6(a0), q6(a1)), "removed": (q6(r0), q6(r1))}


def sum_lm(edges):
    """sum of edge lm over records; HELD records are counted apart (never as 0)."""
    lo = hi = D(0)
    held = 0
    for e in edges:
        if e["lm"] is None:
            held += 1
            continue
        lo += D(e["lm"][0])
        hi += D(e["lm"][1])
    return {"lm": (q6(lo), q6(hi)), "held": held}
