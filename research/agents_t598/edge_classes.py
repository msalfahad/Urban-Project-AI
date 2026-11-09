"""T-598 rules (any villa; research, unwired): the CLASS of a held stair nosing edge and its lm.

R-T598-1 EDGE CLASS (proposed, every villa; provenance T-598; builds on R-T412-1..4 (one riser, one nosing; the drawn
front edge), R-T434-1 / -2 (a count governs by the owner rule's source when consistent; a winder subdivision is measured
only where drawn), OWNER_RULE_STAIRS_2026-10-24 S-9 / A8 (winders never generated; missing winder geometry HELD),
Q-46 A (section A-A counts ST-01), Q-50 A cond (round stair: reconstructed, no section), ERS s.2.1-2.6):
  A held nosing edge is closed by asking two separate questions, never one:
    (1) EXISTENCE: does the governing riser count put a riser (hence a nosing) here? One riser, one nosing; the count
        comes from the governing source (section where an owner rule names it; the plan reconstruction where the owner
        approved it). No governing count -> the edge stays HELD.
    (2) LENGTH: is the edge's length fixed by DRAWN geometry, whatever the open item? A straight edge across a lane is
        the lane width between two drawn bounds that run through the whole range of positions the open item allows; a
        drawn front edge is its own length.
  Classes:
    VALUE            existence governed AND length drawn (the edge line itself drawn on one plan, a riser face of
                     it on a second drawing, or a lane width invariant over the open position range). An open
                     POSITION (head clash, a drafting conflict about where a riser stands) leaves the LENGTH valued and
                     is named beside; it never holds the lm.
    DRAWING_CONFLICT existence governed, but two drawings give two different LENGTHS for it: lm HELD with the bound
                     (lo = the smaller reading, hi = the larger), never 0; a governed value may be stated beside when
                     two drawings agree on one reading and only one drawing carries the other.
    DESIGNER_ITEM    the geometry is not drawn (e.g. the plan subdivision of winders whose count is governed): lm HELD,
                     bound from first principles only (lo = n x the lane width each front must cross, hi = n x the
                     longest straight segment the region admits), never a generated winder.
  An edge part over a band of undetermined kind (stringer cap / upstand / tread) is its own DESIGNER_ITEM, bound
  0 .. band width; the tread part across the lane stays VALUE.

R-T598-2 CURVED FRONT EDGES (proposed, every villa): a front edge that continues as an arc (curtail / bullnose step) is
  measured on the developed arc (r x sweep in radians), never the chord, and belongs to the edge it continues (one riser,
  one nosing: an arc never adds a riser); an arc counts as a nosing only where it is drawn as a front + riser-face PAIR
  like the straight edges of the same flight. Sweep is taken counter-clockwise from start to end angle (DXF convention).

R-T598-3 STATUS (ERS s.2.6): DRAWING-CONFIRMED where the count is governed by a drawing an owner rule names and the length
  is drawn; ASSUMED - OWNER-APPROVED where the count rests on an owner-approved reconstruction (no section); HELD for
  DRAWING_CONFLICT / DESIGNER_ITEM. VERIFIED is the Checker's word and is refused here. Nothing is released.
"""
from __future__ import annotations

import math
from decimal import Decimal, getcontext

getcontext().prec = 40
CLASSES = ("VALUE", "DRAWING_CONFLICT", "DESIGNER_ITEM")
STATUSES = ("DRAWING-CONFIRMED", "ASSUMED - OWNER-APPROVED", "HELD")
COUNT_SOURCES = ("SECTION_OWNER_RULE", "PLAN_RECONSTRUCTION_OWNER_APPROVED", "NONE")
LENGTH_BASES = ("DRAWN_EDGE", "DRAWN_RISER_FACE_SECOND_DRAWING", "LANE_INVARIANT", "NOT_DRAWN", "TWO_READINGS")
TOL = 1e-6


class RuleError(ValueError):
    pass


def arc_length(r: float, start_deg: float, end_deg: float) -> float:
    """Developed length of a DXF arc (counter-clockwise from start to end); never the chord."""
    if r is None or start_deg is None or end_deg is None:
        raise RuleError("arc with a missing parameter: HELD, never 0")
    if r <= 0:
        raise RuleError("arc radius must be positive")
    sweep = (end_deg - start_deg) % 360.0
    if sweep <= 0:
        raise RuleError("zero sweep")
    return r * math.radians(sweep)


def chord(r: float, start_deg: float, end_deg: float) -> float:
    sweep = (end_deg - start_deg) % 360.0
    return 2 * r * math.sin(math.radians(sweep) / 2)


def lane_invariant(lane_bounds: list[tuple[float, float]], pos_lo: float, pos_hi: float) -> bool:
    """True when both lane bounds (each a drawn line given by its run extent (a, b)) cover the whole position range."""
    if pos_lo > pos_hi:
        raise RuleError("position range inverted")
    if len(lane_bounds) != 2:
        raise RuleError("a lane needs exactly two drawn bounds")
    return all(min(a, b) - TOL <= pos_lo and pos_hi <= max(a, b) + TOL for a, b in lane_bounds)


def classify(edge: dict) -> dict:
    """edge: id, count_source, length_basis, length_m (VALUE) or readings_m (two readings) or region (designer:
    n_fronts, lane_m, longest_m); optional position_conflict (text) and band_m (undetermined band part)."""
    cs = edge.get("count_source")
    lb = edge.get("length_basis")
    if cs not in COUNT_SOURCES:
        raise RuleError(f"{edge.get('id')}: unknown count source {cs!r}")
    if lb not in LENGTH_BASES:
        raise RuleError(f"{edge.get('id')}: unknown length basis {lb!r}")
    if edge.get("generated"):
        raise RuleError(f"{edge.get('id')}: generated winder / edge refused (S-9)")
    out = {"id": edge["id"], "lm": None, "bound": None, "status": "HELD"}
    if cs == "NONE":
        out.update(cls="DESIGNER_ITEM", why="no governing riser count")
        return out
    if lb == "NOT_DRAWN":
        reg = edge.get("region")
        if not reg:
            raise RuleError(f"{edge['id']}: designer item without its region bound")
        n, lane, longest = reg["n_fronts"], reg["lane_m"], reg["longest_m"]
        if n <= 0 or lane <= 0 or longest < lane:
            raise RuleError(f"{edge['id']}: bad region bound")
        out.update(cls="DESIGNER_ITEM", bound=(round(n * lane, 6), round(n * longest, 6)), why="geometry not drawn")
        return out
    if lb == "TWO_READINGS":
        rd = edge.get("readings_m")
        if not rd or len(rd) != 2 or any(v is None or v <= 0 for v in rd):
            raise RuleError(f"{edge['id']}: a drawing conflict needs two positive readings")
        if abs(rd[0] - rd[1]) <= TOL:
            raise RuleError(f"{edge['id']}: equal readings are not a conflict")
        out.update(cls="DRAWING_CONFLICT", bound=(min(rd), max(rd)), why="two drawn lengths")
        return out
    if lb == "LANE_INVARIANT":
        if not lane_invariant(edge["lane_bounds"], *edge["position_range"]):
            raise RuleError(f"{edge['id']}: a lane bound does not cover the open position range: length not fixed")
    L = edge.get("length_m")
    if L is None:
        raise RuleError(f"{edge['id']}: VALUE without a length (HELD is never 0)")
    if L <= 0:
        raise RuleError(f"{edge['id']}: non-positive length")
    status = "DRAWING-CONFIRMED" if cs == "SECTION_OWNER_RULE" else "ASSUMED - OWNER-APPROVED"
    out.update(cls="VALUE", lm=round(L, 6), status=status, why=edge.get("position_conflict") or "")
    return out


def to_m(value: float, unit: str) -> float:
    if unit == "m":
        return value
    if unit == "mm":
        return value / 1000.0
    raise RuleError(f"unit {unit!r} refused (m or mm only)")


def residual(his: dict, causes: list[tuple[str, float]], ours: float) -> float:
    """his - ours must equal the sum of the signed causes exactly (to 1e-6); returns the unexplained residual."""
    his_total = sum(Decimal(str(c)) * Decimal(str(w)) for c, w in his["rows"])
    diff = his_total - Decimal(str(ours))
    s = sum(Decimal(str(v)) for _, v in causes)
    return float(diff - s)
