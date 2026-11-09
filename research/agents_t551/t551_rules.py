"""T-551 rules (research, unwired): B10 column, neck, footing (+ straps + boundary band) and blinding concrete reconciled
against a freelancer by COMPONENT, for any villa.

R-T551-1 COLUMN SPLIT PER STOREY AND MARK. engine valued - his rows = COUNT + HELD + SECTION + HEIGHT, exactly
    (Decimal, 6 dp), with his section A_h, his height h_h and his count n_h per mark:
      COUNT   = (n_drawn - n_h) x A_h x h_h          (n_drawn = valued + held lines bound to a drawn member; when he has
                                                     no row of the mark: the engine's valued m3, held lines add nothing)
      HELD    = - n_held x A_h x h_h                 (engine blank, his share on the held lines; never closed as 0)
      SECTION = sum over valued lines (A_e - A_h) x h_h
      HEIGHT  = sum over valued lines A_e x (h_e - h_h), split into JOINT_HEAD = A_e x D_ctrl (the joint + head the column
                line owns to the slab top, R-T394-1), BASE = A_e x (storey base datum - member base) and GLOBAL_DEPTH = the
                rest (his one soffit depth against the member's own controlling depth); with D_ctrl open the HEIGHT of
                that member stays one term HEIGHT_OPEN. Extends R-T394-2 .. 4 to a candidate whose printed-vs-drawn
                CONFLICT columns are HELD lines (T-394 P1 adopted): their volume is HELD, never SECTION.
R-T551-2 FOOTING LINE SPLIT PER MARK. The keyed footing line = isolated / combined footings + straps + the boundary band.
    engine valued - his rows = COUNT + HELD + a per-piece remainder that must carry a NAMED cause from the drawing
    (OVERLAP: an intersection his rows bill twice and the deeper element owns, R-CONC-OWN-1; LENGTH: his rounded length
    against the drawn length); a remainder without a named cause is UNTRACED, never folded into another term.
R-T551-3 OWNERSHIP ONCE AND FAMILY GUARD. Column / slab: the column to the slab TOP with the slab NET of the column
    outline, or the column to the slab SOFFIT with the slab GROSS; any other pairing bills A x t twice or nowhere. Neck:
    from the footing TOP (the footing owns its depth). Plain-concrete blinding is never added to a structural RC total.
    Volumes are m3 only (mm, kg or t refused); a percentage is not a quantity; a missing value is HELD, never 0.
R-T551-4 HELD BOUND BESIDE HIS ROW. Per held line his share (his section x his height, or his row volume) is printed
    beside the engine bound and classed INSIDE / BELOW / ABOVE / UNBOUNDED; information for the Checker only, never a
    reason to release, raise or lower an engine figure.

Provenance: T-551 (2026-11-06), on R-T394-1 .. 6 (T-394), T-233 (footing / blinding closure), T-478 (blinding plate),
R-T545-1 .. 3 (T-545) and R-CONC-OWN-1. Scope: every villa.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

Q6 = Decimal("0.000001")
COLUMN_COMPONENTS = ("COUNT", "HELD", "SECTION", "JOINT_HEAD", "BASE", "GLOBAL_DEPTH", "HEIGHT_OPEN")
FOOTING_COMPONENTS = ("COUNT", "HELD", "OVERLAP", "LENGTH", "UNTRACED")
FAMILY_COMPONENTS = ("HELD", "SCOPE_DOUBLE", "RULE_DIFFERENCE")
VERDICT = {"COUNT": "ENGINE_RIGHT", "HELD": "HELD", "SECTION": "UNRESOLVED", "JOINT_HEAD": "RULE_DIFFERENCE",
           "BASE": "ENGINE_RIGHT", "GLOBAL_DEPTH": "ENGINE_RIGHT", "HEIGHT_OPEN": "TRACED_SPLIT_OPEN",
           "OVERLAP": "ENGINE_RIGHT", "LENGTH": "ENGINE_RIGHT", "UNTRACED": "UNRESOLVED",
           "SCOPE_DOUBLE": "ENGINE_RIGHT", "RULE_DIFFERENCE": "RULE_DIFFERENCE"}
STRUCTURAL_RC = ("STR.CONC.COLUMN", "STR.CONC.NECK", "STR.CONC.FOOTING", "STR.CONC.STRAP", "STR.CONC.BOUNDARY_WALL",
                 "STR.CONC.BEAM", "STR.CONC.SLAB", "STR.CONC.GROUND_BEAM", "STR.CONC.LIFT")
PLAIN = ("STR.CONC.BLINDING",)


class Refused(ValueError):
    """A reading the rules refuse."""


def d6(x) -> Decimal:
    if x is None:
        raise Refused("missing value: carry it HELD, never 0")
    if isinstance(x, str):
        s = x.strip().lower()
        if s.endswith("%"):
            raise Refused("a component given as a percentage is not a quantity")
        if s.endswith(("kg", " t", "mm")):
            raise Refused("concrete is reconciled in m3 only")
    return Decimal(str(x)).quantize(Q6, rounding=ROUND_HALF_UP)


def _m(v, what="dimension"):
    v = Decimal(str(v))
    if v <= 0:
        raise Refused(f"non-positive or missing {what}")
    return v


# ---------------------------------------------------------------------------------------------------------- R-T551-1
def column_mark_split(*, his_n, his_b, his_c, his_h, valued, held_n, storey_base):
    """One storey x one mark. valued = [{'A': m2, 'h': m, 'base': m, 'd_ctrl': m or None, 'm3': engine m3}].
    Returns component -> Decimal (engine - his) that re-adds exactly to sum(valued m3) - his rows."""
    out = {k: Decimal(0) for k in COLUMN_COMPONENTS}
    eng = sum((d6(v["m3"]) for v in valued), Decimal(0))
    for v in valued:
        if d6(v["A"]) * d6(v["h"]) != d6(v["m3"]):
            raise Refused(f"engine line {v} is not A x h")
        if max(Decimal(str(v["A"])), Decimal(str(v["h"]))) > 50:
            raise Refused("dimension looks like mm: give metres")
    if his_n == 0:
        out["COUNT"] = eng
        return out, eng, Decimal(0)
    b, c, h = _m(his_b), _m(his_c), _m(his_h)
    if max(b, c, h) > 20:
        raise Refused("dimension looks like mm: give metres")
    A_h = b * c
    his = Decimal(his_n) * A_h * h
    n_drawn = len(valued) + held_n
    out["COUNT"] = Decimal(n_drawn - his_n) * A_h * h
    out["HELD"] = -Decimal(held_n) * A_h * h
    base0 = Decimal(str(storey_base))
    for v in valued:
        A, he, base = Decimal(str(v["A"])), Decimal(str(v["h"])), Decimal(str(v["base"]))
        out["SECTION"] += (A - A_h) * h
        dh = A * (he - h)
        if v.get("d_ctrl") is None:
            out["HEIGHT_OPEN"] += dh
            continue
        d = Decimal(str(v["d_ctrl"]))
        jh, bs = A * d, A * (base0 - base)
        out["JOINT_HEAD"] += jh
        out["BASE"] += bs
        out["GLOBAL_DEPTH"] += dh - jh - bs
    out = {k: d6(v) for k, v in out.items()}
    if sum(out.values(), Decimal(0)) != d6(eng) - d6(his):
        raise Refused("column split does not re-add to the residual")
    return out, d6(eng), d6(his)


# ---------------------------------------------------------------------------------------------------------- R-T551-2
def footing_mark_split(*, his_n, his_unit_m3, valued_m3, held_n, cause=None):
    """One footing / strap mark. cause names the per-piece remainder ('OVERLAP' or 'LENGTH') from the drawing."""
    out = {k: Decimal(0) for k in FOOTING_COMPONENTS}
    eng = sum((d6(v) for v in valued_m3), Decimal(0))
    if his_n == 0:
        out["COUNT"] = eng
        return out, eng, Decimal(0)
    u = d6(his_unit_m3)
    if u <= 0:
        raise Refused("his row volume missing")
    his = Decimal(his_n) * u
    out["COUNT"] = Decimal(len(valued_m3) + held_n - his_n) * u
    out["HELD"] = -Decimal(held_n) * u
    rem = sum((d6(v) - u for v in valued_m3), Decimal(0))
    if rem:
        if cause not in ("OVERLAP", "LENGTH"):
            cause = "UNTRACED"
        out[cause] = rem
    if sum(out.values(), Decimal(0)) != eng - his:
        raise Refused("footing split does not re-add to the residual")
    return out, eng, his


# ---------------------------------------------------------------------------------------------------------- tables
def component_table(engine_m3, his_m3, components: dict, *, held_his_share=None, allowed=None) -> dict:
    """components: name -> m3 (engine - his); refuses an open sum, a percentage, a HELD closed as 0."""
    E, F = d6(engine_m3), d6(his_m3)
    allowed = allowed or (COLUMN_COMPONENTS + FOOTING_COMPONENTS + FAMILY_COMPONENTS)
    out = {}
    for k, v in components.items():
        if k not in allowed:
            raise Refused(f"unknown component {k}")
        out[k] = d6(v)
    if held_his_share is not None and d6(held_his_share) != 0 and out.get("HELD", Decimal(0)) == 0:
        raise Refused("his rows carry the held lines: the HELD component cannot be closed as 0")
    res = E - F
    if sum(out.values(), Decimal(0)) != res:
        raise Refused(f"components {sum(out.values(), Decimal(0))} do not re-add to the residual {res}")
    return {"engine_m3": str(E), "his_m3": str(F), "residual_m3": str(res),
            "components": {k: {"m3": str(v), "verdict": VERDICT[k]} for k, v in out.items() if v}}


# ---------------------------------------------------------------------------------------------------------- R-T551-3
def column_slab_volumes(*, col_b, col_c, h_top, t, slab_area_gross, column_basis, slab_basis):
    """One column under one slab: column to the slab TOP (h_top) or to the SOFFIT (h_top - t)."""
    b, c, H, t, A = (_m(v) for v in (col_b, col_c, h_top, t, slab_area_gross))
    if max(b, c, t) > 5 or H > 20:
        raise Refused("dimension looks like mm: give metres")
    if t >= H:
        raise Refused("slab thickness not below the column height")
    a = b * c
    pair = (column_basis, slab_basis)
    if pair == ("TO_SLAB_TOP", "NET"):
        col, slab = a * H, (A - a) * t
    elif pair == ("TO_SOFFIT", "GROSS"):
        col, slab = a * (H - t), A * t
    elif pair == ("TO_SLAB_TOP", "GROSS"):
        raise Refused("column to the slab top under a GROSS slab bills A x t twice")
    elif pair == ("TO_SOFFIT", "NET"):
        raise Refused("column to the soffit under a NET slab bills A x t nowhere")
    else:
        raise Refused(f"unknown basis {pair}")
    return col, slab, col + slab


def neck_volume(*, b, c, top_level, footing_bottom, footing_depth, measured_from):
    """Neck from the footing TOP (footing owns its depth); from the bottom is a double with the footing."""
    b, c, D = _m(b), _m(c), _m(footing_depth)
    if measured_from != "FOOTING_TOP":
        raise Refused("neck measured from the footing bottom bills the footing depth twice")
    h = Decimal(str(top_level)) - (Decimal(str(footing_bottom)) + D)
    if h <= 0:
        raise Refused("neck top not above the footing top")
    return b * c * h


def structural_total(lines: list[dict]) -> Decimal:
    """Sum of structural RC m3; a plain-concrete (blinding) line or a non-m3 unit is refused, a held line stays out."""
    tot = Decimal(0)
    for ln in lines:
        if ln["item_code"] in PLAIN:
            raise Refused("blinding is plain concrete: never inside a structural RC total")
        if ln.get("unit", "m3") != "m3":
            raise Refused(f"unit {ln.get('unit')} is not m3")
        if ln["item_code"] not in STRUCTURAL_RC:
            raise Refused(f"unknown family {ln['item_code']}")
        if ln.get("class") == "HELD":
            if ln.get("m3") not in (None, ""):
                held_value(ln["m3"])
            continue
        tot += d6(ln["m3"])
    return tot


# ---------------------------------------------------------------------------------------------------------- R-T551-4
def held_bound_class(his_share, low, high) -> str:
    if low is None or high is None:
        return "UNBOUNDED"
    s, lo, hi = d6(his_share), d6(low), d6(high)
    if lo > hi:
        raise Refused("held bound low > high")
    if s < lo:
        return "BELOW"
    if s > hi:
        return "ABOVE"
    return "INSIDE"


def held_value(v):
    if v is not None and Decimal(str(v)) == 0:
        raise Refused("a HELD quantity stays blank: 0 is refused")
    return v
