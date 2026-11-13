"""T-710 rules (any villa; research, unwired). Waterproofing round 3: census by cause, sunken wet-room recesses,
wet-room upturns with no drawn height.

R-T710-1  SUNKEN RECESS (provenance T-710 on T-213 / T-702; scope: a wet room over a lowered slab panel).
          The panel is lowered at full thickness by a drop d. A membrane laid on the structural slab (a tray) lines the
          recess: its plan area is unchanged (the released floor m2 stands) and it gains vertical faces equal to the
          recess loop inside the room x d, where the loop is the boundary of (panel n room): along a room face the
          wall upturn starts d lower, at a free panel edge inside the room it is a step face. A membrane laid on the
          fill under the tile gains nothing. So: system position printed -> value; d printed -> value; otherwise
          HELD low 0 (position unprinted) .. high loop x d_max. d_max = min over the panel's boundary beams of
          (h_beam - t_slab): a full-thickness panel cannot hang below the beams that carry it. A boundary beam with
          no scheduled depth leaves the high end OPEN (None), never 0. A panel part outside every wet room is NOT
          waterproofing scope (it is a floor-bed item for that room) and is never folded into a wet-room line.
R-T710-2  UPTURN NEEDS ITS HEIGHT. A wet-room wall upturn is run x height; the run comes from the faces, the height
          from the governing rule (UP-WP-003 0.20 m) or the drawing. A room whose upturn height is neither drawn nor
          governed by a rule stays HELD with its run stated; a run is never multiplied by a default.
R-T710-3  CENSUS BY CAUSE. Every HELD or MISSING waterproofing entry carries exactly one cause: MEASURABLE_NOW (the
          drawings print it; measured, waiting for wiring), DESIGNER (a datum only the designer can print: drop,
          detail, outlet type, system), NEEDS_OWNER_RULE (an open owner question governs it), NO_PHYSICAL_ELEMENT (the
          line has no built element: proposed EXCLUDED, never 0 in a total). The census count must equal the
          candidate filter; a HELD entry is never counted as 0.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

CAUSES = ("MEASURABLE_NOW", "DESIGNER", "NEEDS_OWNER_RULE", "NO_PHYSICAL_ELEMENT")
Q6 = Decimal("0.000001")


def D(x):
    if x is None:
        return None
    if isinstance(x, float) and x != x:  # NaN
        raise ValueError("NaN is not a quantity")
    v = Decimal(str(x))
    if v < 0:
        raise ValueError("negative length / depth")
    return v


def q6(v):
    return None if v is None else v.quantize(Q6, rounding=ROUND_HALF_UP)


def d_max(beam_depths_m, t_slab_m):
    """R-T710-1: largest drop a full-thickness panel can take inside its boundary beams; None if any depth unknown"""
    if t_slab_m is None or not beam_depths_m or any(h is None for h in beam_depths_m):
        return None
    t = D(t_slab_m)
    hs = [D(h) for h in beam_depths_m]
    if any(h > Decimal("5") for h in hs) or t > Decimal("1"):
        raise ValueError("depth reads as mm, not m")
    m = min(hs) - t
    if m <= 0:
        raise ValueError("a boundary beam no deeper than the slab cannot carry a lowered panel")
    return m


def recess_wp(loop_m, drop_m=None, drop_max_m=None, membrane_position=None):
    """R-T710-1: extra vertical membrane of one wet room over one sunken panel (m2).

    membrane_position: 'ON_SLAB' (tray in the recess), 'ON_FILL' (under the tile) or None (unprinted)."""
    L = D(loop_m)
    if L is None:
        return {"status": "HELD", "value": None, "low": None, "high": None, "why": "recess loop not measured"}
    if membrane_position == "ON_FILL":
        return {"status": "DRAWING-CONFIRMED", "value": Decimal("0"), "low": None, "high": None,
                "why": "membrane on the fill: the recess is not lined"}
    if membrane_position not in (None, "ON_SLAB"):
        raise ValueError("unknown membrane position")
    if drop_m is not None:
        v = q6(L * D(drop_m))
        if membrane_position == "ON_SLAB":
            return {"status": "DRAWING-CONFIRMED", "value": v, "low": None, "high": None, "why": "loop x printed d"}
        return {"status": "HELD", "value": None, "low": Decimal("0"), "high": v,
                "why": "d printed, membrane position unprinted"}
    high = None if drop_max_m is None else q6(L * D(drop_max_m))
    low = None if membrane_position == "ON_SLAB" else Decimal("0")
    return {"status": "HELD", "value": None, "low": low, "high": high,
            "why": "d unprinted (designer)" + ("" if high is not None else "; d_max unknown: high OPEN")}


def upturn(run_m, height_m):
    """R-T710-2: wall upturn m2, or HELD with the run when no height is drawn or governed"""
    r = D(run_m)
    if r is None:
        return {"status": "HELD", "value": None, "run_m": None, "why": "run not measured"}
    if height_m is None:
        return {"status": "HELD", "value": None, "run_m": q6(r), "why": "no upturn height drawn or governed"}
    return {"status": "MEASURED", "value": q6(r * D(height_m)), "run_m": q6(r)}


def split_panel(panel_m2, in_wet_m2):
    """R-T710-1: the part of a panel outside every wet room is floor-bed scope, never wet-room waterproofing"""
    p, w = D(panel_m2), D(in_wet_m2)
    if w > p + Decimal("0.0005"):
        raise ValueError("more panel inside the rooms than the panel")
    return {"wp_scope_m2": q6(w), "outside_wet_m2": q6(max(p - w, Decimal("0")))}


def census_check(entries, expected_count):
    """R-T710-3: one cause per entry, count equals the candidate filter, a HELD entry never reads 0"""
    if len(entries) != expected_count:
        raise ValueError(f"census {len(entries)} != candidate filter {expected_count}")
    by = {}
    for e in entries:
        if e.get("cause") not in CAUSES:
            raise ValueError(f"entry {e.get('key')} has no valid cause")
        if e.get("status") == "HELD" and e.get("value") in (0, "0", Decimal("0")):
            raise ValueError(f"entry {e.get('key')} HELD read as 0")
        by[e["cause"]] = by.get(e["cause"], 0) + 1
    return by
