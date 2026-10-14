"""RELEASE SAFETY (M9 Phase 2B-0, ARCH_TAKEOFF_V2.2 only) - the corrections of the Phase 2A acceptance review that make
a released architectural quantity either right or not released. V1, V2 and V2.1 never call this module (their call
paths pass no release-safety policy), so their outputs stay byte-identical.

F-24  wall-finish deductions. An opening is deducted from a room's plaster / paint / wall tile only by the length of it
      that lies on that room's own boundary (from the source identity THR|<opening>|<face> of each boundary edge), at
      the opening's height - never by its full width in every room whose boundary touches it. Every wall-finish line is
      checked geometrically:
        - an opening's own length on the boundary <= its width (+ 1 mm);
        - no boundary edge belongs to two openings at once;
        - the boundary decomposes into wall + band-opening + undeducted-opening lengths equal to the wall run (1 mm);
        - known deductions <= gross; the lower bound of a range >= 0.
      A line that fails a check is BLOCKED_RFI "GEOMETRY_INCONSISTENT" (no released value, no clamping). A line whose
      boundary holds openings with an unknown deduction - a door closed only by its leaf (provisional door), a glazed
      screen drawn on the room face, an edge that is wall and something else at once, an opening without a height - is
      a BOUNDED_EXPOSURE range: high = no deduction for them, low = their full length at the finish height.
F-17  boundary roles for skirting. A boundary edge that carries a skirted role (wall, wall cap, column, window
      threshold) and an unskirted one (glazing, door / passage threshold, door closure, zone line) at once is no
      longer split 50 / 50 between them. The skirting that holds under both readings is released; the edge's length
      is a separate range [0, length] ("skirting where the boundary role is unresolved", e.g. a window frame drawn on
      the room face: floor-level glazing -> no skirting, sill window -> skirting).

The documented role sets (one-sided boundary edges of a room face):
    SKIRTED_OUTER   WALL, WALL_CAP, COLUMN, WINDOW_THRESHOLD   (the V1 convention: a window threshold is a sill window)
    SKIRTED_HOLE    WALL, WALL_CAP, COLUMN                     (obstructions inside the room)
    WALL_FINISHED   WALL, WALL_CAP, COLUMN                     (a boundary that carries plaster / paint / wall tile)
An edge whose role set lies inside the skirted set is skirted; one that shares no role with it is not; one with both is
unresolved. For the wall finish, an edge with a THR source is a band opening (deducted by its own length), one inside
WALL_FINISHED is wall, a pure zone line is no wall (not in the wall run, as in V1), anything else is an undeducted
opening.

Stdlib only; project-agnostic; pure functions on plain dicts."""

from __future__ import annotations

import math
from collections import defaultdict

POLICY_ID = "URBAN_RELEASE_SAFETY_V1"
SKIRTED_OUTER = frozenset({"WALL", "WALL_CAP", "COLUMN", "WINDOW_THRESHOLD"})
SKIRTED_HOLE = frozenset({"WALL", "WALL_CAP", "COLUMN"})
WALL_FINISHED = frozenset({"WALL", "WALL_CAP", "COLUMN"})
ZONE = "ZONE_LINE"
TOL_M = 1e-3                     # geometric consistency tolerance (1 mm)
GEOMETRY_INCONSISTENT = "GEOMETRY_INCONSISTENT"


def _edge_lm(arr, e, unit_m):
    if e["kind"] == "S":
        return math.dist(arr.nodes[e["n0"]], arr.nodes[e["n1"]]) * unit_m
    return e["prim"].r * (e["t1"] - e["t0"]) * unit_m


def _key(roles):
    return "+".join(sorted(roles))


def boundary_detail(arr, cycle, hole_cycles, unit_m):
    """the boundary of one face, edge by edge (one-sided edges only, as the face perimeter): role set -> lm for the
    outer boundary and the holes; band opening id -> lm on this face's outer boundary; door-closure key -> lm; the lm
    of outer edges that belong to two openings at once."""
    out = {"outer_sets_lm": defaultdict(float), "hole_sets_lm": defaultdict(float), "opening_lm": defaultdict(float),
           "closure_lm": defaultdict(float), "shared_opening_lm": 0.0, "shared_openings": []}

    def one_sided(cyc):
        seen = defaultdict(int)
        for ei, _ in cyc:
            seen[ei] += 1
        return [ei for ei, n in seen.items() if n == 1]

    for ei in one_sided(cycle):
        e = arr.edges[ei]
        ln = _edge_lm(arr, e, unit_m)
        out["outer_sets_lm"][_key(e["roles"])] += ln
        ops = sorted({s.split("|")[1] for s in e["sources"] if s.startswith("THR|")})
        for o in ops:
            out["opening_lm"][o] += ln
        if len(ops) > 1:
            out["shared_opening_lm"] += ln
            out["shared_openings"].append(ops)
        for s in e["sources"]:
            if s.startswith("CLOSURE|"):
                out["closure_lm"][s.rsplit("|", 1)[0]] += ln
    for hc in hole_cycles:
        for ei in one_sided(hc):
            e = arr.edges[ei]
            out["hole_sets_lm"][_key(e["roles"])] += _edge_lm(arr, e, unit_m)
    return {"outer_sets_lm": dict(sorted(out["outer_sets_lm"].items())),
            "hole_sets_lm": dict(sorted(out["hole_sets_lm"].items())),
            "opening_lm": dict(sorted(out["opening_lm"].items())),
            "closure_lm": dict(sorted(out["closure_lm"].items())),
            "shared_opening_lm": out["shared_opening_lm"],
            "shared_openings": sorted({tuple(x) for x in out["shared_openings"]})}


def skirting(legacy_skirt_lm, detail):
    """F-17. legacy_skirt_lm: the V1 skirting run of the room (wall + column + window threshold, coincident roles split
    equally). -> {"certain_lm": the skirting that holds under every reading of the boundary, "unresolved_lm": the
    length of the edges that are skirted under one reading and not under the other, "unresolved_by_roles": {role set:
    lm}, "legacy_credit_lm": what V1 credited for those edges}. certain_lm == legacy_skirt_lm exactly when no edge is
    unresolved."""
    credit, unresolved, by = 0.0, 0.0, {}
    for sets, skirted in ((detail["outer_sets_lm"], SKIRTED_OUTER), (detail["hole_sets_lm"], SKIRTED_HOLE)):
        for key, ln in sets.items():
            roles = set(key.split("+"))
            inside = roles & skirted
            if inside and roles - skirted:
                credit += ln * len(inside) / len(roles)
                unresolved += ln
                by[key] = by.get(key, 0.0) + ln
    certain = legacy_skirt_lm - credit if credit else legacy_skirt_lm
    return {"certain_lm": certain, "unresolved_lm": unresolved,
            "unresolved_by_roles": {k: round(v, 6) for k, v in sorted(by.items())}, "legacy_credit_lm": credit}


def wall_finish(*, run_lm, height_m, openings, opening_heights, detail):
    """F-24. One wall-finish quantity of one room (one trade).

    run_lm      the room's wall run (perimeter - zone lines), as V1
    height_m    the finish height (established)
    openings    [(opening dict with opening_id / kind / width_m)] of the room's band openings (doors, windows, passages)
    opening_heights  {kind: {"value_m", "authority"}} from the facts (DOOR / WINDOW); passages run full height
    detail      the face's boundary_detail
    -> {"state": "MEASURED" | "RANGE" | GEOMETRY_INCONSISTENT, "gross", "net", "low", "high", "deductions",
        "undeducted", "checks": [failed check, ...], "decomposition": {...}}"""
    H = height_m
    gross = run_lm * H
    checks, deductions, missing = [], [], []
    for o in openings:
        own = detail["opening_lm"].get(o["opening_id"], 0.0)
        w = o.get("width_m") or 0.0
        if own > w + TOL_M:
            checks.append(f"{o['opening_id']}: {own:.4f} m on this boundary > its width {w:.4f} m")
        if o["kind"] == "PASSAGE":
            h, auth = H, "passage: full finish height"
        else:
            hh = (opening_heights or {}).get(o["kind"])
            if not hh:
                missing.append({"what": f"{o['kind'].lower()} {o['opening_id']}", "lm": round(own, 6)})
                continue
            h, auth = min(hh["value_m"], H), hh["authority"]
        deductions.append({"what": f"{o['kind'].lower()} {o['opening_id']}", "lm_on_this_boundary": round(own, 6),
                           "width_m": round(w, 6), "height_m": round(h, 6), "height_authority": auth,
                           "m2": round(own * h, 6)})
    if detail["shared_opening_lm"] > TOL_M:
        checks.append(f"{detail['shared_opening_lm']:.4f} m of boundary belongs to two openings at once "
                      f"({'; '.join('+'.join(x) for x in detail['shared_openings'])})")
    wall = opening = undeducted = zone = 0.0
    und_by = {}
    for sets, outer in ((detail["outer_sets_lm"], True), (detail["hole_sets_lm"], False)):
        for key, ln in sets.items():
            roles = set(key.split("+"))
            rest = roles - {ZONE}
            if outer and any(r.endswith("_THRESHOLD") for r in roles):
                opening += ln                                   # a band opening's threshold (THR source)
            elif not rest:
                zone += ln
            elif rest <= WALL_FINISHED:
                wall += ln
            else:
                undeducted += ln
                und_by[key] = und_by.get(key, 0.0) + ln
    # every THR edge was counted per opening; the role-set view above must give the same opening length
    op_total = sum(detail["opening_lm"].values()) - detail["shared_opening_lm"]
    if abs(op_total - opening) > TOL_M:
        checks.append(f"band-opening length {opening:.4f} m by role vs {op_total:.4f} m by source")
    if abs(wall + opening + undeducted - run_lm) > TOL_M:
        checks.append(f"wall {wall:.4f} + openings {opening:.4f} + undeducted {undeducted:.4f} m != wall run "
                      f"{run_lm:.4f} m")
    known = sum(d["m2"] for d in deductions)
    worst = sum(m["lm"] for m in missing) * H + undeducted * H
    high, low = gross - known, gross - known - worst
    if high < -1e-9:
        checks.append(f"deductions {known:.4f} m2 > gross {gross:.4f} m2")
    elif low < -1e-9:
        checks.append(f"the lower bound {low:.4f} m2 is negative (undeducted openings longer than the wall)")
    dec = {"wall_lm": round(wall, 6), "band_opening_lm": round(opening, 6), "undeducted_opening_lm": round(undeducted, 6),
           "undeducted_by_roles": {k: round(v, 6) for k, v in sorted(und_by.items())}, "zone_lm": round(zone, 6),
           "closures": {k: round(v, 6) for k, v in detail["closure_lm"].items()}}
    if checks:
        state = GEOMETRY_INCONSISTENT
    elif missing or undeducted > TOL_M:
        state = "RANGE"
    else:
        state = "MEASURED"
    return {"state": state, "gross": gross, "net": high if state == "MEASURED" else None,
            "low": low if state == "RANGE" else None, "high": high if state == "RANGE" else None,
            "deductions": deductions, "missing_heights": missing, "checks": checks, "decomposition": dec}


def policy_record():
    return {"policy": POLICY_ID, "skirted_outer": sorted(SKIRTED_OUTER), "skirted_hole": sorted(SKIRTED_HOLE),
            "wall_finished": sorted(WALL_FINISHED), "tolerance_m": TOL_M,
            "findings": ["F-17 (no equal split of coincident boundary roles)",
                         "F-24 (openings deducted from the boundary they lie on; geometric checks)"],
            "never": ["an opening deducted by more than its own length on a room's boundary",
                      "a negative or impossible quantity released", "a value clamped to zero",
                      "an arbitrary midpoint of two boundary readings released"]}
