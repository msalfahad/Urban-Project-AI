"""T-712 rules (project-agnostic; scope: every villa). Research only, unwired. Built on R-T658-3 (literal two-level
floor), R-T658-7 (drawn plan area), R-T658-8 (loaded run: least title), R-CONC-OWN-1 / R-T666-1 (one owner per junction
square, a column owns its full section), R-T711-3 (blank with a per-unit quantity) and R-T696-1 (bound_rounding_v1,
directed rounding); none of them edited.

R-T712-1 1.0.0  ONE-SIDED FLOOR OF A HELD GROUND-BEAM LINE = EXACT DRAWN PLAN AREA x THE SMALLEST GUARANTEED DEPTH.
    Physical element: the RC ground beam between the faces that own its ends (columns of the GROUND-BEAM frame, the face
    of the band that owns the junction). Plan area = the drawn outline (both edges to the owning faces, junction pieces
    owned once, columns netted), never L x b of a census span. Depth guarantee, by the drawing's own statement:
      LITERAL_LEVELS  a section printed between two APPROVED levels (top = slab level, underside = outer normal ground)
                      that cannot hold its printed bars (designer item open): depth >= top - underside (R-T658-3);
      LEAST_TITLE     a run that carries another beam (sections printed 'without concentrated load' only): depth >= the
                      least printed title that holds over every span reading, the two adjacent titles on a limit
                      (R-T658-8);
      JUNCTION        a junction remainder owned by one line: depth >= the LEAST guaranteed depth among the members that
                      may own the square (a section may step at the junction face); a deeper member through it is a
                      reading beside, not the floor.
    AT_LEAST = round_low(area x depth). Several plan readings (frames, span bases): the least. AT_MOST only where a drawn
    level caps the underside (a printed footing-top / formation level the beam cannot pass); a printed MINIMUM founding
    depth is not a cap. Refused: a depth basis not in the list, a zero / negative / mm-sized input, an AT_MOST without
    its capping level, an area below the area of the census run it must contain.

R-T712-2 1.0.0  A GROUND BEAM WHOSE TOP OR UNDERSIDE DATUM IS NOT PRINTED STAYS BLANK, WITH m3 PER m OF DEPTH.
    An exterior ('FOLLOW ARCH.') beam on a stretch where neither the slab level it carries nor the ground it stands on is
    printed (a court / yard landing, a pool-deck end) has no guaranteed depth: no AT_LEAST (it would be a chosen
    number), no AT_MOST. HELD BLANK with its designer item and its drawn plan area (= m3 per m of depth) beside; a piece
    of the band that runs on under a column outline is listed beside as a second plan reading, never added silently.

R-T712-3 1.0.0  THE GROUND-BEAM FRAME GOVERNS THE NET LENGTH OF A FLOOR.
    Where another frame (a roof / slab frame) draws the same columns smaller, the run net of the GROUND-BEAM frame's
    column outlines is the shorter reading; the floor uses the least reading, so a longer reading from another frame never
    lowers a floor and never becomes its high.

Rounding: R-T696-1 (AT_LEAST floors at 6 dp from the exact decimal product).
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "agents_t696"))
import bound_rounding_v1 as BR  # noqa: E402

RULES = {"R-T712-1": "1.0.0", "R-T712-2": "1.0.0", "R-T712-3": "1.0.0"}
BASES = ("LITERAL_LEVELS", "LEAST_TITLE", "JUNCTION")
CLASSES = ("AT_LEAST", "BLANK_NAMED")


class Refused(ValueError):
    pass


def _m(v, what, *, allow_zero=False, allow_negative=False):
    if v is None:
        raise Refused(f"{what}: missing (HELD by name, never a default)")
    d = BR.D(v)
    if not allow_negative and (d < 0 or (d == 0 and not allow_zero)):
        raise Refused(f"{what}: {d} not positive")
    if abs(d) >= 100:
        raise Refused(f"{what}: {d} looks like mm (inputs are metres)")
    return d


# ------------------------------------------------------------------ depth guarantees
def depth_literal_levels(*, top, underside, approved=True):
    """LITERAL_LEVELS: top and underside are approved levels (m). Returns the guaranteed depth."""
    if not approved:
        raise Refused("LITERAL_LEVELS: a level that is not approved is no guarantee")
    d = _m(top, "top level", allow_zero=True, allow_negative=True) - _m(underside, "underside level", allow_zero=True,
                                                                         allow_negative=True)
    if d <= 0:
        raise Refused(f"LITERAL_LEVELS: top not above the underside ({d})")
    return d


def titles_holding(span, titles):
    """titles: [(kind, limit_m, depth_m)] with kind 'LT' (less than limit) or 'GT' (more than limit). Returns the depths
    whose condition holds literally; on an exact limit, the two adjacent titles (R-T658-2)."""
    s = _m(span, "span")
    hold = [BR.D(d) for k, lim, d in titles if (k == "LT" and s < BR.D(lim)) or (k == "GT" and s > BR.D(lim))]
    on = [lim for k, lim, d in titles if s == BR.D(lim)]
    if on:
        hold += [BR.D(d) for k, lim, d in titles if BR.D(lim) == s]
    if not hold:
        raise Refused(f"span {s}: no printed title holds")
    return sorted(set(hold))


def depth_least_title(spans, titles):
    """LEAST_TITLE over every span reading."""
    if not spans:
        raise Refused("LEAST_TITLE: no span reading")
    return min(min(titles_holding(s, titles)) for s in spans)


def depth_junction(member_floors):
    """JUNCTION: the least guaranteed depth among the members that may own the square."""
    if not member_floors:
        raise Refused("JUNCTION: no member named")
    return min(_m(v, f"junction member {k}") for k, v in member_floors.items())


# ------------------------------------------------------------------ R-T712-1
def floor(*, areas_m2, depth, basis, census_area_m2=None, at_most=None, capping_level=None):
    if basis not in BASES:
        raise Refused(f"depth basis {basis} is not a drawing guarantee")
    if at_most is not None and not capping_level:
        raise Refused("an AT_MOST needs the printed level that caps the underside")
    if not areas_m2:
        raise Refused("no plan-area reading")
    a = min(_m(x, "plan area") for x in areas_m2)
    if census_area_m2 is not None and a < _m(census_area_m2, "census area") - BR.D("0.000001"):
        raise Refused(f"drawn area {a} below the census run area {census_area_m2}: outline not closed to its faces")
    d = _m(depth, "depth")
    return {"rule": "R-T712-1", "basis": basis, "area_min_m2": a, "depth_m": d,
            "at_least": BR.round_low(BR.mul(a, d)), "at_most": None if at_most is None else BR.round_high(at_most)}


# ------------------------------------------------------------------ R-T712-2
def blank(*, item, why, areas_m2):
    if not item:
        raise Refused("R-T712-2: a blank line names its designer item")
    if not why:
        raise Refused("R-T712-2: a blank line says why no depth is guaranteed")
    if not areas_m2:
        raise Refused("R-T712-2: the per-unit quantity needs the drawn plan area")
    return {"rule": "R-T712-2", "class": "BLANK_NAMED", "at_least": None, "at_most": None, "item": item, "why": why,
            "m3_per_m_depth": sorted({str(BR.round_low(_m(a, 'plan area'))) for a in areas_m2})}


# ------------------------------------------------------------------ R-T712-3
def governing_length(readings_by_frame, gb_frame):
    """readings_by_frame: {frame: net length m}. The floor takes the least; the GB frame must be one of the readings."""
    if gb_frame not in readings_by_frame:
        raise Refused("R-T712-3: the ground-beam frame reading is missing")
    vals = {k: _m(v, f"{k} length") for k, v in readings_by_frame.items()}
    least = min(vals.values())
    return {"rule": "R-T712-3", "floor_length_m": least, "gb_frame_m": vals[gb_frame],
            "frames": {k: str(v) for k, v in vals.items()}}


# ------------------------------------------------------------------ statement guard
def statement(line_id, element_id, cls, *, at_least=None, at_most=None, item=None):
    if cls not in CLASSES:
        raise Refused(f"{line_id}: class {cls}")
    if cls == "AT_LEAST":
        if at_least is None or BR.D(at_least) <= 0:
            raise Refused(f"{line_id}: AT_LEAST must be a positive floor (never 0)")
        if at_most is not None and BR.D(at_most) < BR.D(at_least):
            raise Refused(f"{line_id}: AT_MOST below AT_LEAST")
    else:
        if at_least is not None or at_most is not None:
            raise Refused(f"{line_id}: a blank line carries no figure")
    if not item:
        raise Refused(f"{line_id}: every held line names its item")
    return {"line_id": line_id, "element_id": element_id, "class_after": "HELD", "bound": cls,
            "at_least_m3": None if at_least is None else str(BR.D(at_least)),
            "at_most_m3": None if at_most is None else str(BR.D(at_most)), "measured_net": None, "item": item}
