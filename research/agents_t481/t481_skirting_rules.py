"""T-481: skirting remainder rules (any villa; research, not wired into any candidate).

Physical element (UP-SKIRT-001 1.4.0): a room skirting is a strip fixed to a finished DRY wall / column face at the
FLOOR level of the room. Three rules, each enforced in code here:

R-T481-1 WINDOW BASE. Under a window the skirting exists only where wall stands below the opening. The deciding value is
  the MASONRY opening base above the room's finished floor (the jamb lines), never the frame / threshold member (an
  aluminium bottom rail 0.05 above the floor is not a wall). sill_above_ffl > 0.02 m -> SKIRTED (the base continues
  under the window: the whole edge returns to the line); <= 0.02 m -> NOT_SKIRTED (floor-level glazing: the edge leaves
  the held range); not established -> HELD (the edge stays whole in the range, never 0). Several views of one opening:
  the decision is taken only when every view gives the same decision (spread recorded); a split decision is HELD.
  A datum is required in the SAME view (a printed level); no datum -> refused, never the drawing origin.

R-T481-2 CELL WALK. A room's skirting = sum of the drawn wall / column stretches at floor level of each side; door and
  passage gaps carry none (deducted by opening id, no jamb returns); fixed joinery (a wardrobe box) is never a
  deduction (WALL_CONTACT_PATH_POLICY V1 / V2: the wall behind it stays on the path), it is reported beside. Each
  side closes: stretches + gaps == side length within 0.0005 m.

R-T481-3 ONE FACE, ONE OWNER IN A STAIR SHAFT (with R-T441-2 / R-T410-1). Along a shaft wall face (face-local metres),
  a piece is ROOM skirting (B3-06) only inside the floor zone of the floor the room line measures, i.e. beyond the
  flight's station (its first / last NOSING, T-410 convention) on the floor side; a piece beside a flight or an
  intermediate landing is STAIR skirting (B7-07 / B7-08, the T-410 stretch that covers it); a window in the face goes
  with its owner (its base is measured against that owner's level). A point covered by the floor zone AND by a flight
  of the same floor level is refused (two owners); flights of other levels stacked over the same plan length are
  level-separated and do not conflict (T-441 level test). Uncovered wall -> UNKNOWN, never assigned.

Units: metres everywhere; a value that looks like millimetres (> 50) is refused.
"""
from __future__ import annotations

import math

SILL_TOL_M = 0.02
CLOSE_TOL_M = 0.0005
SKIRTED, NOT_SKIRTED, HELD = "SKIRTED", "NOT_SKIRTED", "HELD"
ROOM, STAIR, WINDOW, UNKNOWN = "ROOM", "STAIR", "WINDOW", "UNKNOWN"


class RuleError(ValueError):
    pass


def _m(v, what):
    if v is None:
        raise RuleError(f"{what}: missing (never a default)")
    v = float(v)
    if not math.isfinite(v):
        raise RuleError(f"{what}: not a number")
    if abs(v) > 50:
        raise RuleError(f"{what}: {v} is not a building dimension in metres (millimetres?)")
    return v


# ------------------------------------------------------------------------------------------------ R-T481-1
def sill_above_ffl(opening_base_level, ffl_level, datum_source):
    """Opening base above the finished floor, both read as levels of the SAME datum (printed levels)."""
    if not datum_source:
        raise RuleError("no datum: a level must be printed in the view (never the drawing origin)")
    d = _m(opening_base_level, "opening base level") - _m(ffl_level, "finished floor level")
    if d < -SILL_TOL_M:
        raise RuleError(f"opening base {d:.3f} m below the finished floor: binding or datum error")
    return round(max(d, 0.0), 6)


def window_base(sill_m):
    """One reading -> SKIRTED / NOT_SKIRTED / HELD (R-T481-1)."""
    if sill_m is None:
        return HELD
    s = _m(sill_m, "sill above floor")
    if s < -SILL_TOL_M:
        raise RuleError("sill below the floor")
    return SKIRTED if s > SILL_TOL_M else NOT_SKIRTED


def decide(readings):
    """readings: [(view, sill_above_ffl or None)]. Same decision in every established view -> that decision."""
    if not readings:
        return {"decision": HELD, "why": "no reading", "spread_m": None}
    est = [(v, s) for v, s in readings if s is not None]
    if not est:
        return {"decision": HELD, "why": "sill not established in any view", "spread_m": None}
    dec = {window_base(s) for _, s in est}
    vals = [s for _, s in est]
    spread = round(max(vals) - min(vals), 6)
    if len(dec) > 1:
        return {"decision": HELD, "why": "views disagree on the decision", "spread_m": spread}
    return {"decision": dec.pop(), "why": f"{len(est)} view(s) agree", "spread_m": spread}


def line_effect(decision, line_net, range_hi, edge, gross=None, listed_doors=None):
    """Before / after of a room line and its held range for one window edge (lm).
    SKIRTED: the whole edge returns to the line (net + edge), range - edge; optional closure gross - doors.
    NOT_SKIRTED: net unchanged, range - edge. HELD: unchanged."""
    net, hi, e = _m(line_net, "net") if line_net is not None else None, _m(range_hi, "range"), _m(edge, "edge")
    if e <= 0:
        raise RuleError("edge must be positive")
    if hi + CLOSE_TOL_M < e:
        raise RuleError(f"edge {e} is not inside the held range {hi}")
    if decision == HELD:
        return {"net": net, "range_hi": hi}
    new_hi = round(hi - e, 6)
    if decision == NOT_SKIRTED:
        return {"net": net, "range_hi": max(new_hi, 0.0)}
    if decision != SKIRTED:
        raise RuleError(f"unknown decision {decision}")
    if net is None:
        raise RuleError("a release needs the line's net value")
    after = round(net + e, 6)
    if gross is not None:
        close = round(_m(gross, "gross") - _m(listed_doors, "doors"), 6)
        if abs(close - after) > CLOSE_TOL_M:
            raise RuleError(f"released net {after} does not close on gross - doors {close}")
    return {"net": after, "range_hi": max(new_hi, 0.0)}


# ------------------------------------------------------------------------------------------------ R-T481-2
def walk_cell(sides, joinery=()):
    """sides: [{'id', 'length', 'stretches': [{'kind': WALL|COLUMN|DOOR|PASSAGE, 'length', 'ref'}]}].
    Returns skirting lm, deductions by id, joinery-backed length (reported, never deducted)."""
    total, ded, rows = 0.0, {}, []
    for sd in sides:
        L = _m(sd["length"], f"side {sd['id']}")
        acc = 0.0
        for st in sd["stretches"]:
            ln = _m(st["length"], f"stretch {sd['id']}")
            if ln <= 0:
                raise RuleError(f"side {sd['id']}: non-positive stretch")
            acc += ln
            if st["kind"] in ("WALL", "COLUMN"):
                total += ln
                rows.append((sd["id"], st["kind"], ln, st.get("ref", "")))
            elif st["kind"] in ("DOOR", "PASSAGE"):
                if not st.get("ref"):
                    raise RuleError("an opening is deducted by its id")
                if st["ref"] in ded:
                    raise RuleError(f"opening {st['ref']} deducted twice")
                ded[st["ref"]] = ln
            elif st["kind"] == "JOINERY":
                raise RuleError("joinery is not a site boundary: the wall behind it stays a stretch")
            else:
                raise RuleError(f"unknown stretch kind {st['kind']}")
        if abs(acc - L) > CLOSE_TOL_M:
            raise RuleError(f"side {sd['id']} does not close: {acc:.4f} vs {L:.4f}")
    jb = round(sum(_m(j["length"], "joinery contact") for j in joinery), 6)
    gross = round(sum(_m(s["length"], "side") for s in sides), 6)
    sk = round(total, 6)
    if abs(gross - sum(ded.values()) - sk) > CLOSE_TOL_M:
        raise RuleError("gross - openings != skirting")
    return {"skirting_lm": sk, "gross_lm": gross, "deductions": ded, "joinery_backed_lm": jb, "rows": rows}


# ------------------------------------------------------------------------------------------------ R-T481-3
def _cut(iv, cuts):
    """Subtract intervals cuts from iv=(a,b); returns list of intervals."""
    out = [iv]
    for c0, c1 in cuts:
        nxt = []
        for a, b in out:
            if c1 <= a or c0 >= b:
                nxt.append((a, b))
                continue
            if c0 > a:
                nxt.append((a, c0))
            if c1 < b:
                nxt.append((c1, b))
        out = nxt
    return [(a, b) for a, b in out if b - a > 1e-9]


def _inter(a, b):
    lo, hi = max(a[0], b[0]), min(a[1], b[1])
    return (lo, hi) if hi - lo > 1e-9 else None


def shaft_owners(face, floor_level):
    """face: {'id', 'length', 'walls': [(s0,s1,ref)], 'windows': [(s0,s1,id)], 'floor_zone': [(s0,s1)],
    'flights': [(s0,s1,sid,level_band)]}; level_band = (lo, hi) levels the flight stretch spans.
    Returns pieces [(s0, s1, owner, ref, by)] and lm per owner."""
    L = _m(face["length"], "face length")
    fl = _m(floor_level, "floor level")
    for s0, s1, sid, band in face["flights"]:
        if band[0] < fl - 1e-9 < band[1] or band[0] < fl + 1e-9 < band[1]:
            same = True
        else:
            same = False
        for z in face["floor_zone"]:
            iv = _inter((s0, s1), z)
            if iv and same:
                raise RuleError(f"{face['id']}: {sid} and the floor zone both own {iv[0]:.3f}..{iv[1]:.3f}")
    pieces = []
    for s0, s1, ref in face["walls"]:
        if not (0 <= s0 < s1 <= L + CLOSE_TOL_M):
            raise RuleError(f"{face['id']}: wall stretch outside the face")
        rest = [(s0, s1)]
        for z in face["floor_zone"]:
            nxt = []
            for iv in rest:
                hit = _inter(iv, z)
                if hit:
                    pieces.append((hit[0], hit[1], ROOM, ref, "floor zone"))
                    nxt += _cut(iv, [z])
                else:
                    nxt.append(iv)
            rest = nxt
        for iv in rest:
            covered = []
            for f0, f1, sid, _ in face["flights"]:
                hit = _inter(iv, (f0, f1))
                if hit:
                    covered.append(hit)
                    pieces.append((hit[0], hit[1], STAIR, ref, sid))
            for u in _cut(iv, sorted(covered)):
                pieces.append((u[0], u[1], UNKNOWN, ref, "no owner"))
    for s0, s1, wid in face.get("windows", []):
        pieces.append((s0, s1, WINDOW, wid, "window: goes with the owner of its stretch"))
    # stacked flights may cover the same wall twice in plan: count each wall point once per owner class
    by = {}
    for owner in (ROOM, STAIR, UNKNOWN):
        ivs = sorted((a, b) for a, b, o, _, _ in pieces if o == owner)
        merged = []
        for a, b in ivs:
            if merged and a <= merged[-1][1] + 1e-9:
                merged[-1] = (merged[-1][0], max(merged[-1][1], b))
            else:
                merged.append((a, b))
        by[owner] = round(sum(b - a for a, b in merged), 6)
    return {"pieces": sorted(pieces), "lm": by}
