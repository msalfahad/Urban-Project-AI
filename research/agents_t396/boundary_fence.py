"""T-396 BOUNDARY_FENCE_V1: plot boundary / fence masonry ABOVE natural ground, run by run (research rules, stdlib only).

Not wired into any method. Every villa; provenance T-396 (built on merged T-253 R-BOUND-GB-1, T-361 R-T361-1 / -2,
owner Q-63 C and Q-65 C, ERS s.2 / s.3, lesson 2026-10-29 'a quantity's status is the weakest of its inputs').

Physical element: a boundary wall stands on the upper boundary ground beam (top at N.G.) and rises above N.G.; it is
block masonry with reinforced-concrete columns at intervals (a typical boundary-wall detail) and gate openings in it.
Its quantities are kept apart:

  * the RUN (plan length on the plot-line band, corner squares once), gate openings inside it (no wall);
  * the WALL PLANE above N.G. = solid length x height: the gross face of the wall (block + columns + any plinth);
  * the BLOCK NET = plane - column faces - any lower band of another material - any undimensioned profile cut;
  * the block TYPE / count / mortar (procurement), never defaulted (Q-65 C).

Rules (R-T396-n, proposed; a rule change is a new version, never an edit in place):
  R-T396-1  a boundary run is measured on its plot-line band with each corner square counted once (in the run that owns
            it, the same convention as the boundary G.B band, R-BOUND-GB-1); gate openings are not wall: solid = run -
            gates, each gate inside the run; a part of the band owned by another element's line (a pool back) is
            excluded by name, never counted in both.
  R-T396-2  the height above N.G. comes from a PRINTED dimension of the boundary wall itself (its section or
            elevation); drawn-only geometry (elevation lines) corroborates a printed height and never replaces it; a
            run whose element the owner holds (Q-63 C) or whose top is not settled (a closure under a roof) is HELD
            blank, never 0 and never the freelancer's height.
  R-T396-3  the block net is the plane less the column faces (0.30 x h each, count printed) less a lower band whose
            material is not block (when the material is unresolved the band is HELD) less any profile cut (a dip drawn
            in an elevation but not dimensioned -> HELD at most the plane); a block net with an unknown term is HELD
            with AT_MOST = the plane, never the plane itself.
  R-T396-4  block type, count and mortar stay HELD until the material is specified (Q-65 C); masonry BELOW N.G.
            (between the upper and lower boundary beams) is its own component with its own depth, never folded into
            the above-ground wall.
  R-T396-5  a freelancer fence row is mapped to runs by length before any comparison: a corner square counted in two
            runs is a named cause; a height with no printed source is never adopted.
"""

from __future__ import annotations

DC = "DRAWING-CONFIRMED"
HELD = "HELD"
UNKNOWN = "UNKNOWN"
COLUMN_ALONG_WALL_M = 0.30          # typical boundary-wall column 20 x 30, the 30 along the wall (ST typical plan)
HEIGHT_BASES = ("PRINTED", "DRAWN", "INHERITED", "NONE")


class FenceError(ValueError):
    pass


def _pos(x, what, zero_ok=False):
    if x is None:
        raise FenceError(f"{what}: missing (a missing value is HELD, never 0)")
    if not isinstance(x, (int, float)) or isinstance(x, bool):
        raise FenceError(f"{what}: not a number")
    if x < 0 or (x == 0 and not zero_ok):
        raise FenceError(f"{what}: {x} not positive")
    return float(x)


def _metres(x, what, unit):
    if unit != "m":
        raise FenceError(f"{what}: unit {unit!r} (convert to m once, at the source)")
    v = _pos(x, what)
    if v > 200:
        raise FenceError(f"{what}: {v} m is not a plot dimension (mm passed as m?)")
    return v


def run_solid(run_m, gates_m=(), excluded_m=(), unit="m", corner_owned_elsewhere_m=0.0):
    """R-T396-1: solid wall length of one run. run_m is the band length the run owns (corner squares once);
    gates and excluded parts (owned by another line) are taken out, each named once; nothing may exceed the run."""
    run = _metres(run_m, "run", unit)
    corner = float(corner_owned_elsewhere_m or 0.0)
    if corner < 0 or corner >= run:
        raise FenceError("corner square larger than the run")
    run -= corner
    g = [_metres(x, "gate", unit) for x in gates_m]
    e = [_metres(x, "excluded part", unit) for x in excluded_m]
    if sum(g) + sum(e) > run + 1e-9:
        raise FenceError("gates / excluded parts exceed the run (a gate is inside its run, never added to it)")
    return round(run - sum(g) - sum(e), 6)


def height(value_m, basis, source, unit="m", corroborated_by=None):
    """R-T396-2: a height record. Only PRINTED gives a value; DRAWN / INHERITED / NONE are HELD."""
    if basis not in HEIGHT_BASES:
        raise FenceError(f"height basis {basis!r}")
    if basis == "NONE":
        if value_m is not None:
            raise FenceError("a height with no source carries no value")
        return {"value": None, "basis": basis, "source": source, "status": HELD}
    v = _metres(value_m, "height", unit)
    if v > 10:
        raise FenceError(f"height {v} m: not a boundary wall")
    if not source:
        raise FenceError("a height needs its source (sheet / handle)")
    status = DC if basis == "PRINTED" else HELD
    return {"value": v, "basis": basis, "source": source, "status": status,
            "corroborated_by": corroborated_by or []}


def plane(solid_m, h, element_held=False):
    """wall plane above N.G. (gross face). Valued only with a PRINTED height and an element not held by the owner."""
    if h["status"] != DC or element_held:
        cand = None if h["value"] is None else round(solid_m * h["value"], 6)
        return {"m2": None, "status": HELD, "comparison_only_m2": cand}
    return {"m2": round(solid_m * h["value"], 6), "status": DC, "comparison_only_m2": None}


def block_net(pl, h, columns_n, lower_band=None, profile_cut="NONE"):
    """R-T396-3: net block face. columns_n None = count not printed. lower_band = (height_m, material) with material
    'BLOCK' / 'NOT_BLOCK' / 'UNRESOLVED'. profile_cut = 'NONE' / 'UNDIMENSIONED' / <m2 printed>."""
    if pl["m2"] is None:
        return {"m2": None, "status": HELD, "at_most_m2": pl["comparison_only_m2"], "held_terms": ["plane HELD"]}
    hv = h["value"]
    gross = pl["m2"]
    known = 0.0
    held = []
    if columns_n is None:
        held.append(f"columns: count not printed ({COLUMN_ALONG_WALL_M} x {hv} = {round(COLUMN_ALONG_WALL_M * hv, 6)} m2 each)")
    else:
        if not isinstance(columns_n, int) or isinstance(columns_n, bool) or columns_n < 0:
            raise FenceError("column count must be a whole number >= 0")
        known += columns_n * COLUMN_ALONG_WALL_M * hv
    if lower_band is not None:
        bh, mat = lower_band
        bh = _pos(bh, "lower band height")
        if bh >= hv:
            raise FenceError("lower band not below the wall top")
        if mat == "NOT_BLOCK":
            known += gross / hv * bh
        elif mat == "UNRESOLVED":
            held.append(f"lower {bh} m band material unresolved ({round(gross / hv * bh, 6)} m2)")
        elif mat != "BLOCK":
            raise FenceError(f"lower band material {mat!r}")
    if profile_cut == "UNDIMENSIONED":
        held.append("profile cut drawn, not dimensioned")
    elif profile_cut != "NONE":
        known += _pos(profile_cut, "profile cut m2")
    if known > gross + 1e-9:
        raise FenceError("deductions exceed the wall plane")
    if held:
        return {"m2": None, "status": HELD, "at_most_m2": round(gross - known, 6), "held_terms": held}
    return {"m2": round(gross - known, 6), "status": DC, "at_most_m2": None, "held_terms": []}


def ledger_row(run_id, run_m, gates_m, excluded_m, h, columns_n, lower_band=None, profile_cut="NONE",
               element_held=False, corner_owned_elsewhere_m=0.0, unit="m", thickness_m=0.20):
    solid = run_solid(run_m, gates_m, excluded_m, unit, corner_owned_elsewhere_m)
    pl = plane(solid, h, element_held)
    bn = block_net(pl, h, columns_n, lower_band, profile_cut)
    return {"run": run_id, "run_m": run_m, "corner_owned_elsewhere_m": corner_owned_elsewhere_m,
            "gates_m": list(gates_m), "excluded_m": list(excluded_m), "solid_m": solid, "thickness_m": thickness_m,
            "height_m": h["value"], "height_basis": h["basis"], "height_status": h["status"],
            "plane_m2": pl["m2"], "plane_status": pl["status"], "plane_comparison_only_m2": pl["comparison_only_m2"],
            "block_net_m2": bn["m2"], "block_status": bn["status"], "block_at_most_m2": bn["at_most_m2"],
            "block_held_terms": bn["held_terms"], "block_type": "HELD (Q-65 C)", "block_count": "HELD (Q-65 C)"}


def totals(rows):
    """each status separately; HELD never counted as 0 (a HELD row adds its name, not a number)."""
    out = {"plane_dc_m2": 0.0, "plane_held_runs": [], "block_dc_m2": 0.0, "block_held_runs": [], "solid_m": 0.0}
    for r in rows:
        out["solid_m"] += r["solid_m"]
        if r["plane_status"] == DC:
            out["plane_dc_m2"] += r["plane_m2"]
        else:
            out["plane_held_runs"].append(r["run"])
        if r["block_status"] == DC:
            out["block_dc_m2"] += r["block_net_m2"]
        else:
            out["block_held_runs"].append(r["run"])
    for k in ("plane_dc_m2", "block_dc_m2", "solid_m"):
        out[k] = round(out[k], 6)
    return out


def map_freelancer(his_len, his_h, runs_outer, corner_m, own_len, own_h):
    """R-T396-5: his length rebuilt from the runs' OUTER lengths; returns the cause split in m and m2 (residual named)."""
    his_len = _pos(his_len, "his length")
    his_h = _pos(his_h, "his height")
    outer_sum = round(sum(runs_outer), 6)
    corner_twice = round(outer_sum - own_len, 6)
    if abs(corner_twice - corner_m) > 1e-6:
        raise FenceError("outer sum - own length is not the shared corner square")
    unexplained_len = round(his_len - outer_sum, 6)
    his_m2 = round(his_len * his_h, 6)
    own_m2 = round(own_len * own_h, 6)
    c_corner = round(corner_twice * his_h, 6)
    c_unexpl = round(unexplained_len * his_h, 6)
    c_height = round((his_h - own_h) * own_len, 6)
    resid = round(his_m2 - own_m2 - c_corner - c_unexpl - c_height, 6)
    return {"his_m2": his_m2, "own_plane_m2": own_m2, "diff_m2": round(his_m2 - own_m2, 6),
            "corner_twice_m": corner_twice, "corner_twice_m2": c_corner,
            "length_unexplained_m": unexplained_len, "length_unexplained_m2": c_unexpl,
            "height_diff_m": round(his_h - own_h, 6), "height_m2": c_height, "residual_m2": resid}


def bind_once(parts):
    """R-T396-1: every physical part (id) has exactly one owner line; a part bound to two lines is refused."""
    seen = {}
    for pid, owner in parts:
        if not owner:
            raise FenceError(f"{pid}: no owner line")
        if pid in seen and seen[pid] != owner:
            raise FenceError(f"{pid}: owned by {seen[pid]} and {owner} (counted twice)")
        seen[pid] = owner
    return seen
