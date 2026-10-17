"""ARCH_QUANTITY_TRUTH_V1 - generic architectural quantity calculators with explicit evidence states.

Every calculator returns the quantity AND its release state, derived from the states of the evidence it needs
(TRADE_DEPENDENCIES). No trade is more certain than its weakest required dependency; a missing dependency is BLOCKED,
never a default. Quantities and materials are separate (a VERIFIED area may carry material = BY_SPEC).

    release states   VERIFIED_COMPLETE > VERIFIED_PARTIAL_LOWER_BOUND > PROVISIONAL > BLOCKED  (NOT_IN_SCOPE apart)

    wall_class()          terminal wall classification; masonry needs identity evidence beyond thickness
    ledger_check()        every admitted candidate piece terminates in exactly one class; length conserved
    floor_conservation()  plate area = sum of accounted components (+ explicit residual); unaccounted = 0
    trade_state()         the release of one trade quantity from its dependency states
    skirting_path()       boundary path with per-segment inclusion / exclusion reasons
    waterproofing()       wet floor + gross upturn path (door crossings counted, never deducted)
    wall_tile()           gross wet face - established openings + reveals (left / right / head, no sill)
    plaster_paint()       plaster to masonry termination and paint to finished ceiling, separate heights
    blockwork_area()      length x height - established openings - RC overlap (never masonry behind RC)
    opening_height()      typed height-authority ladder; area only with width AND height established
    ceiling_area()        physical ceiling plane only (no void / external / open-to-below)
    cross_trade_check()   cross-trade completeness invariants (no absence, no double treatment)

Project-agnostic; stdlib only.
"""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict

POLICY_ID = "ARCH_QUANTITY_TRUTH_V1"
VC, LB, PROV, BLK, NIS = ("VERIFIED_COMPLETE", "VERIFIED_PARTIAL_LOWER_BOUND", "PROVISIONAL", "BLOCKED",
                          "NOT_IN_SCOPE")
ORDER = (VC, LB, PROV, BLK)
EPS = 1e-6


def weakest(*states) -> str:
    """The weakest of release states (NOT_IN_SCOPE ignored unless everything is out of scope)."""
    s = [x for x in states if x != NIS]
    if not s:
        return NIS
    for st in s:
        if st not in ORDER:
            raise ValueError(f"unknown release state {st}")
    return max(s, key=ORDER.index)


# ============================================================================================ walls
WALL_CLASSES = ("MASONRY_100", "MASONRY_150", "MASONRY_200", "OTHER_MASONRY", "RC_WALL", "RC_COLUMN_INTERFACE",
                "GLAZING", "DOOR_OPENING", "OPEN_TRANSITION", "RAILING_VOID_EDGE", "NON_MASONRY_PARTITION",
                "EXTERNAL_BOUNDARY_NON_WALL", "AMBIGUOUS_BLOCKED", "BLOCKED_MATERIAL", "NOT_WALL",
                "EXCLUDED_WITH_REASON")
MASONRY_CLASSES = ("MASONRY_100", "MASONRY_150", "MASONRY_200", "OTHER_MASONRY")
STD_WIDTHS = {100: "MASONRY_100", 150: "MASONRY_150", 200: "MASONRY_200"}


def wall_class(*, width_mm, paired, on_wall_layer, rc_overlap, structural_checked, width_tol_mm=12.0,
               max_masonry_mm=300.0):
    """Terminal class of one paired wall interval. Masonry identity needs ALL of: paired faces, the architectural wall
    layer, a structural cross-check that found no RC element there. Thickness alone never makes masonry: without the
    identity evidence the interval is BLOCKED_MATERIAL (its length stays accounted)."""
    if not paired:
        return "AMBIGUOUS_BLOCKED", None, "single line: no paired face, thickness unknown"
    if rc_overlap:
        return "RC_COLUMN_INTERFACE", "STRUCTURAL_REGISTERED", "band lies on a registered RC element"
    if width_mm is None or width_mm > max_masonry_mm:
        return "EXCLUDED_WITH_REASON", None, f"band width {width_mm} mm outside the masonry range"
    if not (on_wall_layer and structural_checked):
        return "BLOCKED_MATERIAL", None, ("material identity not established (needs the architectural wall layer and a "
                                          "structural cross-check); thickness alone is not masonry")
    for w, cls in STD_WIDTHS.items():
        if abs(width_mm - w) <= width_tol_mm:
            return cls, "ARCH_WALL_LAYER+STRUCTURAL_NEGATIVE+URBAN_CONVENTION", None
    return "OTHER_MASONRY", "ARCH_WALL_LAYER+STRUCTURAL_NEGATIVE+URBAN_CONVENTION", f"non-standard width {width_mm} mm"


def ledger_check(admitted, pieces, tol_m=1e-3) -> dict:
    """admitted: {segment_id: length_m}; pieces: [{piece_id, parent, length_m, class}] - every piece one class, every
    admitted segment fully covered by its pieces. Returns the violations and the conservation totals."""
    v = []
    seen = set()
    by_parent = defaultdict(float)
    for p in pieces:
        if p["piece_id"] in seen:
            v.append(("PIECE_DOUBLE_TERMINATED", p["piece_id"]))
        seen.add(p["piece_id"])
        if p.get("class") not in WALL_CLASSES:
            v.append(("UNKNOWN_OR_MISSING_CLASS", p["piece_id"], p.get("class")))
        if p["parent"] not in admitted:
            v.append(("PIECE_WITHOUT_ADMITTED_PARENT", p["piece_id"]))
        by_parent[p["parent"]] += p["length_m"]
    for sid, L in admitted.items():
        if abs(by_parent.get(sid, 0.0) - L) > tol_m:
            v.append(("LENGTH_NOT_CONSERVED", sid, round(L, 6), round(by_parent.get(sid, 0.0), 6)))
    tot_in = sum(admitted.values())
    tot_cls = sum(p["length_m"] for p in pieces if p.get("class") in WALL_CLASSES)
    return {"violations": v, "admitted_m": round(tot_in, 6), "classified_m": round(tot_cls, 6),
            "unaccounted_m": round(tot_in - tot_cls, 6)}


# ============================================================================================ floors
FLOOR_COMPONENTS = ("INTERNAL_SPACE", "EXTERNAL_SPACE", "WALL_BAND", "COLUMN", "SHAFT", "VOID", "STAIR_OPENING",
                    "OPENING_STRIP", "SLIVER", "RECOVERED_SPACE", "UNRESOLVED_BLOCKED")


def floor_conservation(plate_m2, parts, tol_m2=0.01) -> dict:
    """parts: [{id, component, area_m2}] (already clipped to the plate). The plate is conserved when the components sum
    to it; a residual is never dropped - it must appear as an UNRESOLVED_BLOCKED component."""
    v = []
    by = defaultdict(float)
    ids = set()
    for p in parts:
        if p["id"] in ids:
            v.append(("DUPLICATE_COMPONENT", p["id"]))
        ids.add(p["id"])
        if p["component"] not in FLOOR_COMPONENTS:
            v.append(("UNKNOWN_COMPONENT", p["id"], p["component"]))
        if p["area_m2"] < -EPS:
            v.append(("NEGATIVE_AREA", p["id"]))
        by[p["component"]] += p["area_m2"]
    s = sum(by.values())
    un = plate_m2 - s
    if abs(un) > tol_m2:
        v.append(("PLATE_NOT_CONSERVED", round(plate_m2, 6), round(s, 6), round(un, 6)))
    return {"plate_m2": round(plate_m2, 6), "sum_m2": round(s, 6), "unaccounted_m2": round(un, 6),
            "by_component_m2": {k: round(x, 6) for k, x in sorted(by.items())}, "violations": v}


# ============================================================================================ trades
TRADE_DEPENDENCIES = {
    "FLOOR_FINISH": ("physical_area", "indoor_state", "floor_semantic"),
    "CEILING": ("physical_area", "indoor_state", "ceiling_scope"),
    "SKIRTING": ("dry_region", "boundary_path", "opening_transitions", "void_railing_exclusion"),
    "WALL_TILE": ("wet_semantic", "wall_faces", "height", "openings"),
    "WATERPROOFING": ("wet_semantic", "floor_area", "wp_eligibility", "upturn_path"),
    "PLASTER": ("wall_faces", "plaster_eligibility", "height", "openings"),
    "PAINT": ("wall_faces", "paint_eligibility", "finished_ceiling_height", "openings"),
    "BLOCKWORK": ("wall_segment", "material", "height", "openings"),
    "ALUMINIUM": ("opening_identity", "width", "height", "function_material"),
}


def trade_state(trade, deps) -> dict:
    """deps: {dependency: release state}. A dependency not given is BLOCKED (never defaulted)."""
    need = TRADE_DEPENDENCIES[trade]
    states = {d: deps.get(d, BLK) for d in need}
    missing = [d for d in need if d not in deps]
    st = weakest(*states.values())
    return {"trade": trade, "state": st, "dependencies": states, "missing": missing,
            "weakest": [d for d, s in states.items() if s == st and st != VC]}


# ---------------------------------------------------------------------------------- skirting
SKIRT_INCLUDE = ("WALL", "COLUMN", "WINDOW")
SKIRT_EXCLUDE = {"DOOR": "door opening (doors excluded)", "OPEN_PASSAGE": "open passage",
                 "FULL_HEIGHT_GLAZING": "full-height glazing", "VOID_EDGE": "void edge / railing (no wall)",
                 "RAILING": "railing", "STAIR_OPENING": "stair opening", "EXTERNAL_EDGE": "external edge",
                 "ZONE_SPLIT": "semantic-zone split line (no wall)", "WET_TILED_WALL": "wet full-tile wall face",
                 "CABINET": "base unit (Urban rule)", "DRAFTING_JOIN": "drafting join (no physical edge)"}
SKIRT_BLOCK = {"GLAZING_UNKNOWN": "glazing of unknown sill (window continuous vs full-height door unresolved)",
               "UNKNOWN_EDGE": "boundary edge of unknown physical kind"}


def skirting_path(edges, *, region_wet_full_tile=False, region_dry=True) -> dict:
    """edges: [{edge_id, kind, length_m, ...}]. Hidden skirting and hidden profile share this path. Returns the
    included length, the exclusions by reason, the blocked length and a state (VC when nothing is blocked, LB when
    blocked edges exist, BLOCKED when no dry region is established)."""
    segs, inc, blk = [], 0.0, 0.0
    exc = defaultdict(float)
    for e in edges:
        k = e["kind"]
        if region_wet_full_tile:
            why, use = "wet full-tile region: no dry skirting", "EXCLUDED"
        elif k in SKIRT_INCLUDE:
            why, use = ("window: skirting continuous below the sill" if k == "WINDOW" else "wall face"), "INCLUDED"
        elif k in SKIRT_EXCLUDE:
            why, use = SKIRT_EXCLUDE[k], "EXCLUDED"
        else:
            why, use = SKIRT_BLOCK.get(k, f"unknown edge kind {k}"), "BLOCKED"
        if use == "INCLUDED":
            inc += e["length_m"]
        elif use == "EXCLUDED":
            exc[why] += e["length_m"]
        else:
            blk += e["length_m"]
        segs.append(dict(e, use=use, reason=why))
    if not region_dry and not region_wet_full_tile:
        st = BLK
    elif region_wet_full_tile:
        st = NIS
    else:
        st = VC if blk < EPS else LB
    return {"included_m": round(inc, 6), "blocked_m": round(blk, 6),
            "excluded_m_by_reason": {k: round(x, 6) for k, x in sorted(exc.items())}, "state": st, "segments": segs,
            "path_total_m": round(sum(e["length_m"] for e in edges), 6)}


# ---------------------------------------------------------------------------------- waterproofing
def waterproofing(*, floor_m2, edges, upturn_m=0.15, upturn_authority="URBAN wet-room upturn 0.15 m",
                  wet_state=VC, area_state=VC) -> dict:
    """Wet floor membrane + upturn along the GROSS boundary: doorways do not interrupt the upturn (they are counted,
    never deducted). The upturn m2 is a reference figure."""
    total = sum(e["length_m"] for e in edges)
    doors = sum(e["length_m"] for e in edges if e["kind"] in ("DOOR", "OPEN_PASSAGE"))
    st = weakest(wet_state, area_state)
    return {"floor_membrane_m2": round(floor_m2, 6), "upturn_path_m": round(total, 6),
            "door_crossings_m": round(doors, 6), "door_crossings_deducted": False, "upturn_m": upturn_m,
            "upturn_area_reference_m2": round(total * upturn_m, 6), "upturn_authority": upturn_authority, "state": st}


# ---------------------------------------------------------------------------------- openings
HEIGHT_LADDER = ("EXACT_SOURCE", "TYPE_SCHEDULE_SOURCE", "CROSS_VERIFIED_REPEATED_TYPE", "OWNER_PROJECT_FACT",
                 "SCALED_SOURCE_SINGLE", "URBAN_FALLBACK", "BUDGET", "BLOCKED")
# SCALED_SOURCE_SINGLE: one scaled reading of a drawn elevation / section (not printed, not repeated) - source-derived,
# so it is not a fallback, but it is PROVISIONAL
LADDER_STATE = {"EXACT_SOURCE": VC, "TYPE_SCHEDULE_SOURCE": VC, "CROSS_VERIFIED_REPEATED_TYPE": VC,
                "OWNER_PROJECT_FACT": VC, "SCALED_SOURCE_SINGLE": PROV, "URBAN_FALLBACK": PROV, "BUDGET": PROV,
                "BLOCKED": BLK}


def opening_height(evidence, *, kind) -> dict:
    """evidence: [{authority, height_m, ref}]. The highest-ranked authority wins. A window never takes a fallback or a
    budget height (NO DEFAULT WINDOW HEIGHT)."""
    ok = []
    for e in evidence:
        a = e["authority"]
        if a not in HEIGHT_LADDER:
            raise ValueError(f"unknown height authority {a}")
        if kind in ("WINDOW", "GLAZED_DOOR_CANDIDATE") and a in ("URBAN_FALLBACK", "BUDGET"):
            continue
        if e.get("height_m") is not None:
            ok.append(e)
    if not ok:
        return {"authority": "BLOCKED", "height_m": None, "state": BLK, "ref": None}
    best = min(ok, key=lambda e: HEIGHT_LADDER.index(e["authority"]))
    return {"authority": best["authority"], "height_m": best["height_m"], "state": LADDER_STATE[best["authority"]],
            "ref": best.get("ref")}


def opening_area(*, width_m, width_state, height_m, height_state) -> dict:
    if width_m is None or height_m is None or BLK in (width_state, height_state):
        return {"area_m2": None, "state": BLK, "why": "an opening area needs an established width AND height"}
    return {"area_m2": round(width_m * height_m, 6), "state": weakest(width_state, height_state)}


def reveal_area(*, width_m, height_m, depth_m=0.25) -> float:
    """Urban reveal: depth on the left jamb, the right jamb and the head; never at the sill."""
    return round(depth_m * (2.0 * height_m + width_m), 6)


# ---------------------------------------------------------------------------------- wall finishes
def _net_faces(face_m, height_m, openings, reveal_depth_m):
    gross = face_m * height_m
    ded, rev, blocked = 0.0, 0.0, []
    for o in openings:
        a = opening_area(width_m=o.get("width_m"), width_state=o.get("width_state", BLK), height_m=o.get("height_m"),
                         height_state=o.get("height_state", BLK))
        if a["state"] == BLK:
            blocked.append(o.get("id"))
            continue
        h = min(o["height_m"], height_m)
        ded += o["width_m"] * h
        if reveal_depth_m:
            rev += reveal_area(width_m=o["width_m"], height_m=h, depth_m=reveal_depth_m)
    return gross, ded, rev, blocked


def wall_tile(*, face_m, height_m, height_state, openings=(), reveal_depth_m=0.25, wet_state=VC) -> dict:
    """Wet / service wall tile: gross face x tile height - established openings + reveals. An opening whose area is
    not established is listed and keeps the net at most PROVISIONAL (gross minus known openings)."""
    if height_m is None:
        return {"gross_m2": None, "net_m2": None, "state": BLK, "why": "tile height not established",
                "face_m": round(face_m, 6)}
    g, d, r, blocked = _net_faces(face_m, height_m, openings, reveal_depth_m)
    st = weakest(height_state, wet_state, PROV if blocked else VC)
    return {"face_m": round(face_m, 6), "height_m": height_m, "gross_m2": round(g, 6), "opening_deduction_m2": round(d, 6),
            "reveal_addition_m2": round(r, 6), "net_m2": round(g - d + r, 6), "openings_not_deducted": blocked,
            "state": st}


def plaster_paint(*, face_m, plaster_h, plaster_state, paint_h, paint_state, openings=(), reveal_depth_m=0.25,
                  wet_tiled=False) -> dict:
    """Plaster to the masonry termination and paint to the finished ceiling (two heights). A full wet-tiled face gets
    neither (spatter / tile preparation only) - never both tile and plaster / paint."""
    if wet_tiled:
        return {"plaster": {"state": NIS, "net_m2": 0.0, "why": "full wet tile face"},
                "paint": {"state": NIS, "net_m2": 0.0, "why": "full wet tile face"}}
    out = {}
    for name, h, st in (("plaster", plaster_h, plaster_state), ("paint", paint_h, paint_state)):
        if h is None:
            out[name] = {"state": BLK, "net_m2": None, "gross_m2": None, "height_m": None,
                         "geometry": {"face_m": round(face_m, 6), "height": "UNRESOLVED"}}
            continue
        g, d, r, blocked = _net_faces(face_m, h, openings, reveal_depth_m)
        out[name] = {"height_m": h, "gross_m2": round(g, 6), "opening_deduction_m2": round(d, 6),
                     "reveal_addition_m2": round(r, 6), "net_m2": round(g - d + r, 6), "openings_not_deducted": blocked,
                     "state": weakest(st, PROV if blocked else VC)}
    return out


def blockwork_area(*, length_m, height_m, height_state, material_state, openings=(), rc_overlap_m=0.0) -> dict:
    """Masonry area = (length - RC overlap) x height - established openings inside the band. Masonry never runs
    behind an RC column: the overlap length is removed before the area."""
    if height_m is None:
        return {"gross_m2": None, "net_m2": None, "state": BLK, "why": "height not established"}
    L = max(length_m - rc_overlap_m, 0.0)
    g = L * height_m
    d = 0.0
    blocked = []
    for o in openings:
        a = opening_area(width_m=o.get("width_m"), width_state=o.get("width_state", BLK), height_m=o.get("height_m"),
                         height_state=o.get("height_state", BLK))
        if a["state"] == BLK:
            blocked.append(o.get("id"))
        else:
            d += a["area_m2"]
    return {"length_m": round(length_m, 6), "rc_overlap_m": round(rc_overlap_m, 6), "height_m": height_m,
            "gross_m2": round(g, 6), "opening_deduction_m2": round(d, 6), "net_m2": round(g - d, 6),
            "openings_not_deducted": blocked, "state": weakest(height_state, material_state, PROV if blocked else VC)}


# ---------------------------------------------------------------------------------- ceilings
CEILING_EXCLUDED = ("VOID", "OPEN_TO_BELOW", "EXTERNAL", "UNCOVERED_TERRACE", "SHAFT", "STAIR_OPENING", "GARDEN",
                    "COURT", "POOL", "ROOF")


def ceiling_area(*, area_m2, region_class, covered_state, double_height_m2=0.0) -> dict:
    """A ceiling quantity needs a physical ceiling plane: void / external / shaft / uncovered regions have none; the
    part of an indoor region lying under a double-height void of the storey above has none at this level."""
    if region_class in CEILING_EXCLUDED:
        return {"area_m2": 0.0, "state": NIS, "why": f"{region_class}: no ceiling plane"}
    a = max(area_m2 - double_height_m2, 0.0)
    return {"area_m2": round(a, 6), "double_height_excluded_m2": round(double_height_m2, 6), "state": covered_state}


# ---------------------------------------------------------------------------------- cross-trade invariants
def cross_trade_check(*, regions, openings, walls, faces) -> list:
    """regions: [{id, indoor, internal_area_m2, wet, trades: {TRADE: {state, qty}}}]; openings: [{id, count_state,
    area_m2, width_state, height_state}]; walls: [{id, class, blockwork_length_m}]; faces: [{id, treatments: [...]}].
    Returns violations (no absence, no double treatment, no area without width + height)."""
    v = []
    for r in regions:
        t = r.get("trades") or {}
        if r.get("internal_area_m2", 0) > 0 and "FLOOR_FINISH" not in t:
            v.append(("FLOOR_RECORD_MISSING", r["id"]))
        if r.get("indoor") and "CEILING" not in t:
            v.append(("CEILING_RECORD_MISSING", r["id"]))
        if r.get("wet"):
            for k in ("WATERPROOFING", "FLOOR_FINISH", "WALL_TILE"):
                if k not in t:
                    v.append(("WET_TRADE_MISSING", r["id"], k))
        for k, q in t.items():
            if q.get("qty") is not None and q["qty"] < -EPS:
                v.append(("NEGATIVE_QUANTITY", r["id"], k))
    for o in openings:
        if not o.get("count_state"):
            v.append(("OPENING_COUNT_MISSING", o["id"]))
        if o.get("area_m2") is not None and BLK in (o.get("width_state"), o.get("height_state")):
            v.append(("OPENING_AREA_WITHOUT_WIDTH_AND_HEIGHT", o["id"]))
    for w in walls:
        if w["class"] in MASONRY_CLASSES and not w.get("blockwork_length_m"):
            v.append(("MASONRY_WITHOUT_BLOCKWORK_LENGTH", w["id"]))
        if w["class"] not in MASONRY_CLASSES and w.get("blockwork_length_m"):
            v.append(("BLOCKWORK_ON_NON_MASONRY", w["id"], w["class"]))
    for f in faces:
        tr = set(f.get("treatments") or ())
        if not tr:
            v.append(("FACE_WITHOUT_TREATMENT_STATE", f["id"]))
        if "WALL_TILE_FULL" in tr and ({"PLASTER", "PAINT"} & tr):
            v.append(("FACE_DOUBLE_TREATED", f["id"], sorted(tr)))
    return v


def policy_record() -> dict:
    rec = {"policy_id": POLICY_ID, "release_order": list(ORDER), "wall_classes": list(WALL_CLASSES),
           "floor_components": list(FLOOR_COMPONENTS), "trade_dependencies": {k: list(v) for k, v in
                                                                             TRADE_DEPENDENCIES.items()},
           "height_ladder": list(HEIGHT_LADDER), "skirting_include": list(SKIRT_INCLUDE),
           "skirting_exclude": SKIRT_EXCLUDE, "skirting_block": SKIRT_BLOCK, "ceiling_excluded": list(CEILING_EXCLUDED),
           "never": ["masonry from thickness alone", "a default window height", "an opening area without width and "
                     "height", "a door deducted from a waterproofing upturn", "skirting along a void edge or a door",
                     "masonry behind an RC column", "tile and plaster / paint on the same full face"]}
    rec["digest"] = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()
    return rec


# ============================================================================================ geometry helpers
def pair_wall_faces(segments, *, min_mm=60.0, max_mm=450.0, angle_tol=0.02, min_overlap=30.0):
    """segments: [(id, (x0, y0), (x1, y1))] on the wall layer (mm). Each segment is split at the ends of its parallel
    partners min..max mm away; each piece takes the NEAREST partner covering it. Returns pieces
    [{seg, t0, t1, a, b, length, partner, width, side}] (partner None = unpaired)."""
    import math as _m
    out = []
    unit = {}
    for sid, a, b in segments:
        L = _m.dist(a, b)
        unit[sid] = ((b[0] - a[0]) / L, (b[1] - a[1]) / L, L) if L > 0 else None
    for sid, a, b in segments:
        u = unit[sid]
        if u is None:
            continue
        ux, uy, L = u
        nx, ny = -uy, ux
        cand = []
        for sj, c, d in segments:
            if sj == sid or unit[sj] is None:
                continue
            vx, vy, Lj = unit[sj]
            if abs(ux * vy - uy * vx) > angle_tol:
                continue
            o1 = (c[0] - a[0]) * nx + (c[1] - a[1]) * ny
            o2 = (d[0] - a[0]) * nx + (d[1] - a[1]) * ny
            if abs(o1 - o2) > 5.0 or not (min_mm <= abs(o1) <= max_mm):
                continue
            t0 = (c[0] - a[0]) * ux + (c[1] - a[1]) * uy
            t1 = (d[0] - a[0]) * ux + (d[1] - a[1]) * uy
            lo, hi = max(0.0, min(t0, t1)), min(L, max(t0, t1))
            if hi - lo > min_overlap:
                cand.append((lo, hi, abs(o1), sj, 1 if o1 > 0 else -1))
        cuts = sorted({0.0, L} | {x for c_ in cand for x in c_[:2]})
        for t0, t1 in zip(cuts, cuts[1:]):
            if t1 - t0 < 1e-6:
                continue
            cov = [c_ for c_ in cand if c_[0] <= t0 + 1e-6 and c_[1] >= t1 - 1e-6]
            best = min(cov, key=lambda z: (z[2], str(z[3]))) if cov else None
            pa = (a[0] + ux * t0, a[1] + uy * t0)
            pb = (a[0] + ux * t1, a[1] + uy * t1)
            rec = {"seg": sid, "t0": t0, "t1": t1, "a": pa, "b": pb, "length": t1 - t0,
                   "partner": best[3] if best else None, "width": best[2] if best else None,
                   "side": best[4] if best else None, "normal": (nx, ny)}
            if best:
                h = best[4] * best[2] / 2.0
                rec["centre_a"] = (pa[0] + nx * h, pa[1] + ny * h)
                rec["centre_b"] = (pb[0] + nx * h, pb[1] + ny * h)
            out.append(rec)
    return out


def assign_split(pieces):
    """pieces of one mixed physical space: [{id, area_m2, classes}] - one class -> that class (PROVISIONAL: the boundary
    is positive non-wall evidence); no label -> UNASSIGNED (BLOCKED); several classes -> MIXED_UNRESOLVED (BLOCKED)."""
    out = []
    for p in pieces:
        c = sorted(set(p["classes"]))
        if len(c) == 1:
            out.append(dict(p, cls=c[0], state=PROV))
        elif not c:
            out.append(dict(p, cls="UNASSIGNED", state=BLK))
        else:
            out.append(dict(p, cls="MIXED_UNRESOLVED", state=BLK))
    return out


def orphan_outcome(*, in_route_a_space, in_plate, recovered, over_thin_site=False, external_class=False):
    if in_route_a_space:
        return "BOUND"
    if not in_plate or external_class:
        return "NOT_IN_SCOPE_EXTERNAL"
    if recovered:
        return "RECOVERED_PHYSICAL_REGION"
    if over_thin_site:
        return "LABEL_BELONGS_TO_EXISTING_REGION"
    return "BLOCKED_TOPOLOGY"


def masonry_around_opening(*, width_m, wall_h_m, opening_h_m, lintel_m=0.0, sill_m=0.0) -> dict:
    """Masonry in the wall height not taken by the opening: above the head (minus the lintel) and below the sill.
    head = sill + opening height; total = width x (wall height - opening height - lintel)."""
    above = max(wall_h_m - (sill_m + opening_h_m) - lintel_m, 0.0)
    below = max(sill_m, 0.0)
    return {"above_m2": round(width_m * above, 6), "below_m2": round(width_m * below, 6),
            "total_m2": round(width_m * (above + below), 6)}


# ============================================================================================ mutation-proof checks
def region_class_check(regions):
    """A region holding labels of different semantic classes must be MIXED_UNRESOLVED (never fully DRY)."""
    v = []
    for r in regions:
        cl = set(r.get("label_classes") or ())
        if len(cl) > 1 and r["class"] != "MIXED_UNRESOLVED":
            v.append(("MIXED_LABELS_IN_RESOLVED_REGION", r["region_id"], sorted(cl), r["class"]))
    return v


def label_conservation(source_label_ids, records):
    ids = [r["occurrence"] for r in records]
    missing = sorted(set(source_label_ids) - set(ids))
    dup = sorted({i for i in ids if ids.count(i) > 1})
    return [("LABEL_MISSING", m) for m in missing] + [("LABEL_DUPLICATED", d) for d in dup]


def masonry_identity_check(pieces):
    """A masonry piece must carry paired faces and a material authority (never thickness alone)."""
    return [("MASONRY_WITHOUT_IDENTITY", p["piece_id"]) for p in pieces
            if p["class"] in MASONRY_CLASSES and (not p.get("paired") or not p.get("material_authority"))]


def masonry_rc_check(pieces, inside_rc):
    """inside_rc(piece) -> True when the band centre lies on an RC element: such a piece can never be masonry."""
    return [("MASONRY_THROUGH_RC", p["piece_id"]) for p in pieces if p["class"] in MASONRY_CLASSES and inside_rc(p)]


def opening_function_check(openings):
    return [("GLAZED_DOOR_CANDIDATE_COLLAPSED", o["id"], o["type"]) for o in openings
            if "GLAZED_DOOR_CANDIDATE" in (o.get("flags") or []) and o["type"] != "GLAZED_DOOR_CANDIDATE"]


def skirting_check(segments):
    bad = {"DOOR", "OPEN_PASSAGE", "VOID_EDGE", "RAILING", "STAIR_OPENING", "ZONE_SPLIT", "FULL_HEIGHT_GLAZING"}
    return [("SKIRTING_ON_EXCLUDED_EDGE", s.get("edge_id"), s["kind"]) for s in segments
            if s.get("use") == "INCLUDED" and s["kind"] in bad]


def height_consistency(faces, tol=1e-6):
    """Each face height must equal ITS interval - ITS terminating member depth (one global height never replaces a
    source-varying one)."""
    v = []
    for f in faces:
        if f.get("height_m") is None or f.get("interval_m") is None or f.get("D_cm") is None:
            continue
        if abs(f["height_m"] - (f["interval_m"] - f["D_cm"] / 100.0)) > tol:
            v.append(("HEIGHT_NOT_FROM_OWN_TERMINATION", f["id"]))
    return v


def internal_floor_check(rows):
    return [("EXTERNAL_IN_INTERNAL_FLOOR", r["region"]) for r in rows
            if r.get("internal") and r.get("cls") in ("EXTERNAL", "VOID", "SHAFT", "ROOF")]


def face_uniqueness(faces):
    ids = [f["id"] for f in faces]
    return [("WALL_FACE_DOUBLE_COUNTED", i) for i in sorted({i for i in ids if ids.count(i) > 1})]
