"""T-681 rules: tiles and adhesive HELD census (R-T681-1), skirting at an opening by its foot level (R-T681-2), tile
materials beside the m2 (R-T681-3). Research only; every villa; no project value in this module.

R-T681-1 CENSUS. One row per HELD candidate line of the tile scope codes (floor tile, wall tile, skirting, stair
skirting, tile bed, outdoor floor); the census count equals the candidate index filter, no line missing, none twice.
Each row has one cause class: DESIGNER_ITEM (a value the drawings do not print), OWNER_OPEN (an open owner item or an
owner HOLD decision), OPEN_BOUND (bounded by an owner band or two drawn readings), WIRING_GAP (a merged record already
settles the line but the candidate does not carry it), MEASURABLE_NOW (the drawings settle it now). Totals per code:
bounded low / high sums, blank lines counted and named, never summed as 0.

R-T681-2 SKIRTING AT AN OPENING. Skirting is a trim fixed at the junction of the walking surface and the wall face. On
a stretch beside an opening of the same face and plan interval, with walking levels z_min .. z_max (finished treads /
landing), sill S and head H (absolute, metres):
  - S - tol <= z_min and z_max < H: no wall face at the junction anywhere on the stretch -> NOT_APPLICABLE (length 0
    by a full deduction of an actual opening, Q-73), whatever the skirting height;
  - z_min >= H (and the wall is drawn continuous above the head): the junction is on solid wall -> FULL plan length;
  - z_max < S - tol: wall at the junction, but whether the skirting band clears the sill needs a skirting height:
    FULL only when a sourced height h fits (z_max + h <= S), else HELD;
  - anything else (the stretch straddles S or H): HELD by piece;
  - a missing level, a head not above its sill, or levels that look like millimetres: refused (never 0).
R-T681-3 MATERIALS. Adhesive (owner 2026-11-02 / Q-45): 20 kg bag covers 5 m2 for normal tiles incl. 60 x 60, 3 m2
for 120 x 60 and 160 x 80; ceil once per purchasing group; a size that is not sourced makes the row HELD with the
owner-rule bound (area_low / 5 .. area_high / 3), a size outside the rule is refused. Bed mortar 1:4 (Q-45 B, Q-78
figures): about 8 x 50 kg cement and 1.1 m3 loose sand per m3, PROVISIONAL; waste is a separate figure, not applied.
"""
from __future__ import annotations

from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal

SCOPE = ("FIN.FLOOR.PORCELAIN", "FIN.FLOOR.WET_TILE", "FIN.FLOOR.FINISH_HELD", "EXT.FLOOR.PORCELAIN",
         "EXT.FLOOR.OUTDOOR", "FIN.WALL.TILE", "FIN.SKIRTING", "FIN.STAIR.SKIRTING.SLOPED",
         "FIN.STAIR.SKIRTING.ZIGZAG", "FIN.FLOOR.BED.DRY", "FIN.FLOOR.BED.WET")
CLASSES = ("DESIGNER_ITEM", "MEASURABLE_NOW", "OPEN_BOUND", "OWNER_OPEN", "WIRING_GAP")
ADHESIVE_M2_PER_BAG = {"60x60": Decimal(5), "normal": Decimal(5), "120x60": Decimal(3), "160x80": Decimal(3)}
BED_BAGS_PER_M3, BED_SAND_PER_M3 = Decimal(8), Decimal("1.1")
TOL = Decimal("0.005")
MAX_LEVEL_M = Decimal(60)  # an absolute level above 60 m in a villa is read as millimetres and refused


class RuleError(ValueError):
    pass


def D(x):
    if x is None:
        return None
    return x if isinstance(x, Decimal) else Decimal(str(x))


def q(x, p="0.000001"):
    return D(x).quantize(Decimal(p), rounding=ROUND_HALF_UP)


def S(x):
    return None if x is None else format(q(x).normalize(), "f")


def code_in_scope(code):
    return code in SCOPE


def census(entries, held_ids):
    """R-T681-1 totals per code; raises if the census and the candidate filter differ."""
    ids = [e["line_id"] for e in entries]
    if len(ids) != len(set(ids)):
        raise RuleError("a line is in the census twice")
    if sorted(ids) != sorted(held_ids):
        raise RuleError(f"census {len(ids)} lines != candidate filter {len(held_ids)} lines")
    tot = {}
    for e in entries:
        if e["class"] not in CLASSES:
            raise RuleError(f"{e['line_id']}: class {e['class']!r} unknown")
        k = f"{e['item_code']} [{e['unit']}]"
        t = tot.setdefault(k, {"lines": 0, "bounded": 0, "blank": 0, "low": Decimal(0), "high": Decimal(0),
                               "by_class": {}})
        t["lines"] += 1
        t["by_class"][e["class"]] = t["by_class"].get(e["class"], 0) + 1
        if e["held_low"] is None or e["held_high"] is None:
            t["blank"] += 1
        else:
            t["bounded"] += 1
            t["low"] += D(e["held_low"])
            t["high"] += D(e["held_high"])
    for t in tot.values():
        t["low"], t["high"] = (S(t["low"]), S(t["high"])) if t["bounded"] else (None, None)
        t["by_class"] = dict(sorted(t["by_class"].items()))
    return dict(sorted(tot.items()))


def _level(x, name):
    if x is None:
        raise RuleError(f"{name} missing: the stretch stays HELD, never 0")
    v = D(x)
    if abs(v) > MAX_LEVEL_M:
        raise RuleError(f"{name} {v} looks like millimetres, not metres")
    return v


def skirting_at_opening(z_min, z_max, sill, head, plan_length, skirting_height=None, wall_above_head=False):
    """R-T681-2 -> dict(state, length_lm, why)."""
    z0, z1 = _level(z_min, "z_min"), _level(z_max, "z_max")
    s, h = _level(sill, "sill"), _level(head, "head")
    L = D(plan_length)
    if L is None or L <= 0:
        raise RuleError("plan length missing or not positive")
    if z1 < z0:
        raise RuleError("z_max below z_min")
    if h <= s:
        raise RuleError("head not above sill")
    if z0 >= s - TOL and z1 < h:
        return {"state": "NOT_APPLICABLE", "length_lm": "0",
                "why": f"walking levels {S(z0)} .. {S(z1)} lie inside the opening {S(s)} .. {S(h)}: no wall face at "
                       f"the junction (full deduction of an actual opening)"}
    if z0 >= h:
        if not wall_above_head:
            return {"state": "HELD", "length_lm": None, "why": "junction above the head but wall continuity not drawn"}
        return {"state": "FULL", "length_lm": S(L),
                "why": f"walking level {S(z0)} at or above the head {S(h)}: the junction is on solid wall"}
    if z1 < s - TOL:
        hh = D(skirting_height)
        if hh is not None and z1 + hh <= s:
            return {"state": "FULL", "length_lm": S(L), "why": f"skirting band clears the sill {S(s)}"}
        return {"state": "HELD", "length_lm": None,
                "why": "wall at the junction; whether the skirting band clears the sill needs a sourced height"}
    return {"state": "HELD", "length_lm": None, "why": "the stretch straddles the sill or the head: split by piece"}


def adhesive(area_low, area_high, size):
    """R-T681-3 adhesive bags (fractional, before the group ceil) -> dict(status, bags[low, high])."""
    lo, hi = D(area_low), D(area_high)
    if lo is None or hi is None:
        return {"status": "HELD", "bags": None, "why": "host area blank"}
    if size is None:
        return {"status": "HELD", "bags": [S(lo / 5), S(hi / 3)],
                "why": "tile size not sourced: owner-rule bound area / 5 .. area / 3"}
    if size not in ADHESIVE_M2_PER_BAG:
        raise RuleError(f"tile size {size!r} is not in the owner adhesive rule")
    r = ADHESIVE_M2_PER_BAG[size]
    return {"status": "CALCULATED", "bags": [S(lo / r), S(hi / r)], "why": f"{r} m2 per 20 kg bag ({size})"}


def group_bags(rows):
    """Ceil once per purchasing group; any HELD row keeps the group HELD with its bound."""
    lo = sum((D(r["bags"][0]) for r in rows if r["bags"]), Decimal(0))
    hi = sum((D(r["bags"][1]) for r in rows if r["bags"]), Decimal(0))
    blank = sum(1 for r in rows if not r["bags"])
    held = any(r["status"] == "HELD" for r in rows)
    return {"status": "HELD" if held else "CALCULATED", "blank_rows": blank,
            "bags_low": int(lo.to_integral_value(ROUND_CEILING)), "bags_high": int(hi.to_integral_value(ROUND_CEILING)),
            "exact_low": S(lo), "exact_high": S(hi)}


def bed_materials(m3_low, m3_high):
    lo, hi = D(m3_low), D(m3_high)
    if lo is None or hi is None:
        return {"status": "HELD", "cement_bags": None, "sand_m3": None}
    return {"status": "PROVISIONAL", "cement_bags": [S(lo * BED_BAGS_PER_M3), S(hi * BED_BAGS_PER_M3)],
            "sand_m3": [S(lo * BED_SAND_PER_M3), S(hi * BED_SAND_PER_M3)]}
