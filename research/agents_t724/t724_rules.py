"""T-724 rules (project-agnostic; scope: every villa). Research only, unwired. Built on R-T721-1 (bar-stack floor),
R-T714-1 (formwork follows the member face by face), R-T712-1 (floor from drawn plan x least guaranteed depth),
R-CONC-OWN-1 (one owner per square; a gap is never closed by a zero), UP-QTY-STATUS-001 (every line reported once in one
state) and R-T696-1 (bound_rounding_v1, directed rounding); none of them edited.

R-T724-1 1.0.0  WHICH DRAWN BAR LEVELS COUNT IN A BAR-STACK FLOOR.
    A bar level adds its diameter to the R-T721-1 stack only when (a) it is TIED TO THE MEMBER FACE (the bar circles sit
    inside the link outline, on the same vertical as the top and bottom bars) and (b) its NUMBER is a stated quantity:
    a level labelled with a count (e.g. '3T16' top, '3T18' bottom, 'n levels') counts as printed. A set labelled by a
    pitch ('2T14/20cm': two bars per level, levels at <= 0.20 m) has a level count that is a FUNCTION OF THE DEPTH being
    bounded, so the levels drawn in a not-to-scale detail are a picture of the pitch, not a stated number: the set counts
    ONCE (its labelled level). Counting the other drawn levels would derive the depth from a drawing of the depth
    (circular) and from a sheet that tells the builder to work with stated dimensions only. Unlabelled circles (a lapping
    shell bar, a hanger) never count. Cover is added only when printed (R-T721-1).

R-T724-2 1.0.0  A SCALED FACE USES THE MEMBER'S OWN DRAWN EDGE WIDTH.
    A formwork face proportional to a held width (beam soffit b x L) recorded at the drawn reading is scaled to the other
    printed reading by (other width / DRAWN EDGE WIDTH), where the drawn edge width is the perpendicular distance between
    the member's two drawn edge entities. A width derived from a concrete ratio (band polygon area / length / depth, which
    carries joint slivers and 4 dp rounding) is not the edge width and is refused as the scale denominator when it differs
    from the edges by more than 0.05 mm. Reported beside, never used to scale: the face's implied length
    (figure / edge width) against the member's face-to-face length (a soffit netted at column joints, a remainder piece or
    a skew-ended trapezoid differs by its own geometry). The scaled low is never below the figure the drawn
    edges give (a wrong, wider denominator under-states the low end).

R-T724-3 1.0.0  A RANGE THAT STARTS AT 0 IS NO BOUND: ONE CENSUS STATE.
    A line whose index carries low 0 (or none) and a positive high is HELD BLANK with the high beside as a CAP (AT_MOST,
    never printed as a quantity); it is never counted among BOUNDED lines and its high is never added to a BOUNDED family
    high. A positive low makes it BOUNDED (low .. high) or AT_LEAST (low, no high). The same line carries the same state
    in every census, statement and code total.

R-T724-4 1.0.0  A DRAWN PIECE THAT NO LINE CARRIES IS OWNED ONCE OR NAMED.
    A piece of a member's drawn outline (e.g. a projection strip in front of a flush column at which the lines were
    split, a rounded corner square between two strips) goes to the ONE line whose stated basis (its own drawn extent)
    contains it. If two bases contain it: refused (double count). If none does: it is NAMED as a blank child of its
    member with its exact drawn plan area (m3 per m of depth when the depth is held), never 0 and never folded into a
    neighbour line by choice. Before either, the piece must lie outside every column footprint, beam band and slab face
    that carries m3 (an EDGE_HELD slab face with no m3 is no carrier); an overlap is refused (counted twice). A line
    record that reaches into the piece by a rounding sliver (stated sliver limit, e.g. a length recorded 0.5 mm past
    the drawn face) is reported by name, never silently absorbed.

Rounding: R-T696-1 (lows floor at 6 dp from the exact decimal product; highs round up).
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "agents_t696"))
import bound_rounding_v1 as BR  # noqa: E402

D = BR.D
RULES = {"R-T724-1": "1.0.0", "R-T724-2": "1.0.0", "R-T724-3": "1.0.0", "R-T724-4": "1.0.0"}
EDGE_TOL = D("0.00005")      # 0.05 mm: drawn edge pair vs recorded width
LEN_TOL = D("0.005")         # 5 mm: figure / width vs face-to-face length


class Refused(ValueError):
    pass


def _m(v, what, *, small=False):
    if v is None:
        raise Refused(f"{what}: missing (HELD by name, never a default)")
    d = D(v)
    if d <= 0:
        raise Refused(f"{what}: {d} not positive")
    if d >= (1 if small else 100):
        raise Refused(f"{what}: {d} looks like mm (inputs are metres)")
    return d


# ------------------------------------------------------------------ R-T724-1
def counted_levels(levels):
    """levels: dicts {name, dia, tied_to_face, label ('count' | 'pitch' | None), set_id}. Returns (counted, excluded)."""
    counted, excluded, pitch_sets = [], [], set()
    for lv in levels:
        name = lv["name"]
        if not lv.get("tied_to_face"):
            excluded.append((name, "not tied to the member face (outside the link / off the shared vertical)"))
            continue
        lab = lv.get("label")
        if lab == "count":
            counted.append(lv)
        elif lab == "pitch":
            sid = lv.get("set_id") or name
            if sid in pitch_sets:
                excluded.append((name, "further drawn level of a pitch-labelled set: count depends on the depth "
                                       "(not a stated number; not-to-scale detail)"))
            else:
                pitch_sets.add(sid)
                counted.append(lv)
        else:
            excluded.append((name, "unlabelled circle (no stated bar): not counted"))
    return counted, excluded


def stack_depth(*, link_dia, levels, cover=None, cover_printed=False):
    if cover is not None and not cover_printed:
        raise Refused("R-T724-1: a cover not printed on the sheet is a default value")
    counted, excluded = counted_levels(levels)
    names = {lv["role"] for lv in counted if lv.get("role")}
    if not {"top", "bottom"} <= names:
        raise Refused("R-T724-1: a stack needs a counted top and bottom level tied to the face")
    d = 2 * _m(link_dia, "link dia", small=True)
    for lv in counted:
        d += _m(lv["dia"], f"{lv['name']} dia", small=True)
    if cover is not None:
        d += 2 * _m(cover, "printed cover", small=True)
    return {"rule": "R-T724-1", "depth_m": d, "counted": [lv["name"] for lv in counted], "excluded": excluded}


# ------------------------------------------------------------------ R-T724-2
def scaled_face(*, figure, edge_width, other_width, f2f_length, recorded_width=None):
    """figure: the face m2 at the drawn edge width. Returns low / high at (edge, other) and the shift vs recorded."""
    fig = _m(figure, "face figure")
    we, wo = _m(edge_width, "drawn edge width", small=True), _m(other_width, "other printed width", small=True)
    L = _m(f2f_length, "face-to-face length")
    other = BR.mul(fig, wo) / we
    lo, hi = (other, fig) if wo < we else (fig, other)
    out = {"rule": "R-T724-2", "low": BR.round_low(lo), "high": BR.round_high(hi), "ratio": wo / we,
           "implied_length_m": BR.round_point(fig / we), "length_matches_f2f": abs(fig / we - L) <= LEN_TOL}
    if recorded_width is not None:
        wr = _m(recorded_width, "recorded width", small=True)
        out["recorded_width"] = wr
        out["recorded_differs"] = abs(wr - we) > EDGE_TOL
        if out["recorded_differs"]:
            old = BR.mul(fig, wo) / wr
            old_lo = old if wo < we else fig
            out["low_with_recorded"] = BR.round_low(old_lo)
            out["shift_low"] = out["low"] - out["low_with_recorded"]
    return out


def check_denominator(*, recorded_width, edge_width):
    wr, we = _m(recorded_width, "recorded width", small=True), _m(edge_width, "drawn edge width", small=True)
    if abs(wr - we) > EDGE_TOL:
        raise Refused(f"R-T724-2: denominator {wr} is not the drawn edge width {we}")
    return we


# ------------------------------------------------------------------ R-T724-3
def census_state(low, high):
    lo = None if low is None else D(low)
    hi = None if high is None else D(high)
    if lo is not None and lo < 0 or hi is not None and hi < 0:
        raise Refused("R-T724-3: negative bound")
    if lo is not None and hi is not None and hi < lo:
        raise Refused("R-T724-3: high below low")
    if lo is None or lo == 0:
        if hi is None or hi == 0:
            return {"state": "HELD_BLANK", "cap": None, "bounded_low": None, "bounded_high": None}
        return {"state": "HELD_BLANK_CAP", "cap": hi, "bounded_low": None, "bounded_high": None}
    if hi is None:
        return {"state": "AT_LEAST", "cap": None, "bounded_low": lo, "bounded_high": None}
    return {"state": "BOUNDED", "cap": None, "bounded_low": lo, "bounded_high": hi}


def family_census(lines):
    """lines: {line_id: (low, high)}. BOUNDED totals never include a capped blank."""
    out = {"BOUNDED": [], "AT_LEAST": [], "HELD_BLANK_CAP": [], "HELD_BLANK": []}
    lo_sum, hi_sum, al_sum, cap_sum = D(0), D(0), D(0), D(0)
    for lid, (lo, hi) in sorted(lines.items()):
        s = census_state(lo, hi)
        out[s["state"]].append(lid)
        if s["state"] == "BOUNDED":
            lo_sum += s["bounded_low"]
            hi_sum += s["bounded_high"]
        elif s["state"] == "AT_LEAST":
            al_sum += s["bounded_low"]
        elif s["state"] == "HELD_BLANK_CAP":
            cap_sum += s["cap"]
    return {"by_state": {k: len(v) for k, v in out.items()}, "ids": out, "bounded_low": lo_sum,
            "bounded_high": hi_sum, "at_least": al_sum, "caps_beside": cap_sum}


# ------------------------------------------------------------------ R-T724-4
def own_piece(*, piece_id, piece, line_bases, carriers, member, item, sliver_m2=0.0):
    """piece: shapely polygon (m). line_bases: {line_id: polygon of the line's stated extent}. carriers: {name: polygon}
    of every column / beam band / slab face that carries m3 near the piece. Returns the owner or the named child."""
    area = D(repr(round(piece.area, 12)))
    if area <= 0:
        raise Refused(f"{piece_id}: empty piece")
    for name, g in carriers.items():
        if piece.intersection(g).area > 1e-9:
            raise Refused(f"{piece_id}: overlaps {name}, which carries m3 (counted twice)")
    owners = [lid for lid, g in line_bases.items() if g.buffer(1e-9).contains(piece)]
    slivers = {lid: piece.intersection(g).area for lid, g in line_bases.items() if lid not in owners}
    partial = [lid for lid, a in slivers.items() if a > max(1e-9, sliver_m2)]
    if partial:
        raise Refused(f"{piece_id}: partly inside {partial}: split the piece first")
    if len(owners) > 1:
        raise Refused(f"{piece_id}: inside {owners}: two bases contain it (double count)")
    if owners:
        return {"rule": "R-T724-4", "piece": piece_id, "owner": owners[0], "state": "OWNED", "area_m2": area}
    named_slivers = {lid: round(a, 9) for lid, a in slivers.items() if a > 1e-9}
    if not item:
        raise Refused(f"{piece_id}: a named piece names its designer item")
    return {"rule": "R-T724-4", "piece": piece_id, "owner": None, "state": "NAMED_BLANK_CHILD", "member": member,
            "area_m2": area, "m3_per_m_depth": BR.round_point(area), "item": item, "record_slivers_m2": named_slivers}
