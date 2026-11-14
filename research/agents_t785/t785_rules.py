"""T-785 rules (any villa): wet-room membrane in the freelancer's unit, and the sunken wet-room default.

R-T785-1 UPTURN IN LM BESIDE M2. The wall upturn is one physical strip: run (lm) x height (m). The engine keeps the m2
line; the lm line is the same strip's run = m2 / its own rule height (never the freelancer's multiplier, never a
'height 1'). A per-room freelancer upturn priced in lm is his GROSS room perimeter: our like-for-like figure is
    run (walls only) + doorway segments (each room side) + open edges without a wall,
and the remaining difference is named per room (reveal taken into his room, printed vs typed sides, rounding).

R-T785-2 SUNKEN WET ROOM (company default, owner 2026-11-13: 'sunken wet room: recess + 0.30 up'). Where a wet room
sits on a lowered slab panel and the membrane is laid on the structural slab (a tray), the membrane lines the recess
and turns 0.30 m up the walls:
    upturn m2 = wall run x 0.30           (replaces run x 0.20 of a flat wet room in that room only)
    recess m2 = recess loop (panel boundary inside the room) x d
d = the printed drop if one is printed (DRAWING-READ); else the team default recess 0.30 (main chat 2026-11-13 17:30,
same value as the T-765 drop walls), but never deeper than the geometric bound d_max = boundary beam depth - slab
thickness (a full-thickness panel cannot hang below the beams carrying it, T-710); a capped default is flagged.
Refused: missing / non-positive run or loop, NaN, a drop over 1.0 m (mm read as m), a bound below 0.
Floor m2 is unchanged by a recess (the recess faces are vertical).
"""
from __future__ import annotations

import math

FLAT_UPTURN_H = 0.20      # owner Q-03 / UP-WP-002 2.0.0: flat wet room
SUNKEN_UP_H = 0.30        # owner company default 2026-11-13: sunken wet room, 0.30 up
RECESS_D_DEFAULT = 0.30   # main chat 2026-11-13 17:30 (T-765 row): D-41 default recess 0.30
D_MAX_PLAUSIBLE = 1.0     # m; above this a drop is a unit error (mm as m)


class WetRuleError(ValueError):
    pass


def _pos(v, what):
    if v is None or not isinstance(v, (int, float)) or isinstance(v, bool) or math.isnan(v) or v <= 0:
        raise WetRuleError(f"{what} missing or not positive: {v!r} (HELD, never 0)")
    return float(v)


def run_lm(upturn_m2, height_m):
    """R-T785-1: run of one upturn strip from its m2 line and the engine's own rule height."""
    a = _pos(upturn_m2, "upturn m2")
    h = _pos(height_m, "upturn rule height")
    if h > D_MAX_PLAUSIBLE:
        raise WetRuleError(f"upturn height {h} m: unit error (mm as m?)")
    return a / h


def like_for_like_perimeter(run_m, door_segments_m=(), open_edges_m=()):
    """R-T785-1: our figure on his gross-perimeter basis."""
    r = _pos(run_m, "wall run")
    s = sum(_pos(x, "doorway segment") for x in door_segments_m)
    o = sum(_pos(x, "open edge") for x in open_edges_m)
    return r + s + o


def recess_depth(d_max_m=None, d_printed_m=None, default_m=RECESS_D_DEFAULT):
    """R-T785-2: (d, label, capped). Printed governs; else the default, capped by the beam bound."""
    if d_printed_m is not None:
        d = _pos(d_printed_m, "printed drop")
        if d > D_MAX_PLAUSIBLE:
            raise WetRuleError(f"printed drop {d}: unit error (mm as m?)")
        return d, "DRAWING-READ", False
    dflt = _pos(default_m, "default drop")
    if d_max_m is None:
        return dflt, "DEFAULT", False
    dm = _pos(d_max_m, "beam bound d_max")
    if dm > D_MAX_PLAUSIBLE:
        raise WetRuleError(f"d_max {dm}: unit error (mm as m?)")
    if dflt > dm:
        return dm, "DEFAULT", True
    return dflt, "DEFAULT", False


def sunken_room(run_m, recesses, up_h=SUNKEN_UP_H):
    """R-T785-2 for one room. recesses: [{'loop_m', 'd_max_m' (or None), 'd_printed_m' (or None), 'panel'}]."""
    r = _pos(run_m, "wall run")
    if not recesses:
        raise WetRuleError("sunken room without a recess: not R-T785-2 (flat room keeps 0.20)")
    parts, rec = [], 0.0
    for x in recesses:
        loop = _pos(x.get("loop_m"), "recess loop")
        d, label, capped = recess_depth(x.get("d_max_m"), x.get("d_printed_m"))
        parts.append({"panel": x.get("panel"), "loop_m": loop, "d_m": d, "label": label, "capped": capped,
                      "m2": loop * d})
        rec += loop * d
    return {"upturn_m2": r * _pos(up_h, "sunken upturn height"), "recess_m2": rec, "parts": parts,
            "label": "DRAWING-READ" if all(p["label"] == "DRAWING-READ" for p in parts) else "DEFAULT"}


def split(ours, his, components, tol_pct=1.0):
    """named split of ours - his; returns residual and whether it is below tol_pct % of his figure."""
    o = float(ours)
    h = _pos(his, "freelancer figure")
    named = sum(float(c["qty"]) * c["sign"] for c in components)
    res = (o - h) - named
    return {"ours": o, "his": h, "diff": o - h, "pct": 100.0 * (o - h) / h, "named": named, "residual": res,
            "residual_pct": 100.0 * abs(res) / h, "closed": 100.0 * abs(res) / h < tol_pct}
