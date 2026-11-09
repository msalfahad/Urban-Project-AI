"""T-592 rules (any villa; research, unwired): the ONE payable length of an external door / gate step that is the
threshold stone's outer nosing + riser (ELEMENT_REGISTER 'EXTERNAL DOOR STEP', R-T584-1 (b)), and the outside level
that sets its riser.

R-T592-1 (proposed, every villa; provenance T-592; builds on R-T584-1, UP-THR-001 (one threshold strip through the wall
at a doorway, measured with the full door width), ERS s.2-4):
  (a) THE PIECE. The threshold stone of an external door fills the wall gap: its installed length is the MASONRY
      OPENING (the drawn wall-line ends on the face that carries the step), the same measure as the owning threshold
      strip line. The visible nosing (the drawn front edge between the frame jambs) is shorter by the jambs; it is an
      ATTRIBUTE of the same piece, carried beside the line, never a second payable length and never added to it.
  (b) ONE PAYABLE LENGTH. The step is paid ONCE, on the owning threshold line, as its installed piece length (a). A line
      that carries both lengths as quantities is refused; a nosing lm becomes payable only if a separate nosing item
      exists in the BOQ, and then the stone line keeps the piece length (two items, two descriptions, never one sum).
  (c) THE RISER is the front face of the same stone: riser m2 = installed piece length x (inside level - outside
      level). The edge length is never used for the riser area while the piece length is the payable basis.
  (d) THE OUTSIDE LEVEL is a printed level figure in the SAME open region as the step's low side: reachable from a point
      just outside the face without crossing any drawn line (wall, fence, step edge, door / window block). One distinct
      figure in that region: DRAWING-CONFIRMED. Two or more distinct figures: HELD with the bound (min .. max riser).
      None: HELD with the R-T584-1 (a) bound. A level printed elsewhere on the plan (behind a wall, a fence or a step
      edge) never sets the riser; neither does 'the lowest level of the plan' as a fact.
  (e) Units never meet (lm, m2, nr); HELD is never 0; VERIFIED is the Checker's word.
"""
from __future__ import annotations

from decimal import Decimal, getcontext

getcontext().prec = 40
LEN_UNITS = {"m": Decimal(1), "mm": Decimal("0.001")}
STATUSES = ("DRAWING-CONFIRMED", "HELD", "NOT_APPLICABLE")


class RuleError(ValueError):
    pass


def D(x) -> Decimal:
    if x is None:
        raise RuleError("quantity unknown (None) used as a number: HELD / UNKNOWN is never 0")
    if isinstance(x, float):
        return Decimal(repr(x))
    return Decimal(str(x))


def length(x, unit="m"):
    if unit not in LEN_UNITS:
        raise RuleError(f"length unit {unit!r} unknown (m or mm only)")
    v = D(x) * LEN_UNITS[unit]
    if v <= 0:
        raise RuleError("a piece / edge length is positive")
    return v


def level(txt):
    """A printed level figure ('+0.30', '-0.15', '+-0.00', '%%p0.00') -> Decimal."""
    if txt is None:
        raise RuleError("a level that is not printed is not a figure")
    t = str(txt).strip().replace("+-", "").replace("%%p", "")
    return D(t)


def outside_level(region_levels, plan_levels=None, high=None):
    """R-T592-1 (d). region_levels: the printed figures REACHABLE from the step's low side without crossing a drawn
    line (the caller's region read). plan_levels: every figure on the plan (only for the R-T584-1 bound when the
    region prints none). -> dict(status, low, bound)."""
    figs = sorted({level(t) for t in region_levels})
    if len(figs) == 1:
        return {"status": "DRAWING-CONFIRMED", "low": figs[0], "bound": None}
    if len(figs) > 1:
        return {"status": "HELD", "low": None, "bound": (figs[0], figs[-1]),
                "why": "two or more printed levels in the low-side region: no single outside level"}
    if high is None or not plan_levels:
        return {"status": "HELD", "low": None, "bound": None, "why": "no printed level in the region; no bound"}
    lo = min(level(t) for t in plan_levels)
    return {"status": "HELD", "low": None, "bound": (lo, level(high)),
            "why": "no printed level in the region: bound by the plan's lowest figure (R-T584-1 (a)), never a fact"}


def riser_from(high, low_txt, region_levels):
    """Refuses a riser computed from a level that is not in the step's low-side region."""
    if low_txt not in set(region_levels):
        raise RuleError(f"riser from level {low_txt!r} not printed in the step's low-side region: refused")
    r = level(high) - level(low_txt)
    if r <= 0:
        raise RuleError("an edge between equal (or inverted) levels is not a step: CONFLICT, HELD by name")
    return r


def door_step(opening, masonry_opening, nosing_edge, high, outside, unit="m"):
    """R-T592-1 (a)-(c): one external door / gate step. masonry_opening = the wall gap on the step face; nosing_edge =
    the drawn front edge (None: no step). outside = outside_level(...) result. -> the line record (one payable lm)."""
    if nosing_edge is None:
        return {"opening": opening, "status": "NOT_APPLICABLE", "payable_lm": None, "nosing_lm": None,
                "riser_m": None, "riser_m2": None, "nr": 0}
    piece = length(masonry_opening, unit)
    edge = length(nosing_edge, unit)
    if edge > piece:
        raise RuleError(f"{opening}: visible nosing {edge} longer than the stone in the wall gap {piece}: a drawing "
                        "conflict, HELD by name")
    rec = {"opening": opening, "payable_lm": piece, "payable_basis": "INSTALLED_PIECE_MASONRY_OPENING",
           "nosing_lm": edge, "nosing_basis": "VISIBLE_EDGE_BETWEEN_JAMBS (attribute, not payable)",
           "jambs_lm": piece - edge, "nr": 1}
    if outside["status"] == "DRAWING-CONFIRMED":
        r = level(high) - outside["low"]
        if r <= 0:
            raise RuleError(f"{opening}: edge drawn between equal levels: CONFLICT, HELD by name")
        rec.update(status="DRAWING-CONFIRMED", riser_m=r, riser_m2=piece * r, riser_m2_bound=None)
    else:
        b = outside.get("bound")
        rb = None if b is None else (max(level(high) - b[1], D(0)), level(high) - b[0])
        rec.update(status="HELD", riser_m=None, riser_m2=None,
                   riser_m2_bound=None if rb is None else (piece * rb[0], piece * rb[1]))
    return rec


def payable_line(records):
    """A threshold line's payable step quantity: one lm per piece. Refuses a record that books both lengths."""
    lm = D(0)
    for r in records:
        if r.get("status") == "NOT_APPLICABLE":
            continue
        if "payable_lm" not in r or r["payable_lm"] is None:
            raise RuleError(f"{r.get('opening')}: no payable length: HELD, never 0")
        if r.get("nosing_payable"):
            raise RuleError(f"{r.get('opening')}: both the piece length and the nosing edge booked as payable on one "
                            "line: refused (R-T592-1 (b))")
        lm += r["payable_lm"]
    return lm


def book(line_unit, value_unit):
    """lm, m2, nr never meet."""
    if line_unit != value_unit:
        raise RuleError(f"a {value_unit} quantity booked on a {line_unit} line: refused")
    return True
