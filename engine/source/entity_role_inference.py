"""ENTITY ROLE INFERENCE (V1): what a drawing's linework IS, from evidence the drawing itself carries.

Why
    geometry_role admits a part only on a generic name lexicon (WALL, DOOR, WINDOW ...). Many real drawings use
    numeric or single-letter layer names ("1", "W", "D"), so nothing is admitted and every site is blocked. A
    layer map written by hand for one project is forbidden: it would not travel, and it is not evidence.

    This module computes OBSERVATIONS from the source (geometry, CAD structure, context), scores ROLE CANDIDATES
    per evidence channel, and DECIDES: a candidate becomes a source-scoped CLAIM only when it clears the frozen
    threshold on enough independent channels and no competing candidate is close; otherwise the layer / part stays
    UNKNOWN (and the frozen topology then blocks exactly the sites it separates). Claims are
    role_authority.SourceLayerRoleClaim with review_state POLICY_ACCEPTED and authority POLICY_ID: they change role
    authority only, for this source revision and region only, and they are never REVIEWED (no human looked).

        OBSERVATION -> ROLE_CANDIDATE (channel scores + reasons) -> CLAIM -> ACCEPTED | BLOCKED

Evidence channels (never one alone)
    GEOMETRY      parallel pairs at a wall-thickness offset, endpoint joins / T-junctions, small closed rectangles,
                  regular parallel runs (treads), door-swing motifs, glazing-in-gap motifs, enclosure of the drawing
    CAD_STRUCTURE linetype pattern class (continuous / uniform dashes / dash-dot) read from the LTYPE definition -
                  not its name, model-space vs symbol-occurrence share, fills (SOLID hatches) over rectangles
    CONTEXT       association with text inside the same occurrence, relation to the detected plan region / frame,
                  door hinges anchored on wall-face candidates

Physical constants (frozen before any project run; facts about buildings and drafting, not fitted to a sheet)
    wall thickness 80 - 400 mm; door leaf (swing radius) 500 - 1300 mm; swing sweep 0.7 - 2.1 rad (a quarter turn,
    give or take); tread going 200 - 400 mm; column side 150 - 1200 mm; sheet aspect 1.2 - 1.8.

Never: a layer name, a block name or a handle as authority; a coordinate list; a desired quantity; a project.
A block / layer NAME may only CORROBORATE (it is recorded, it never decides). Project-agnostic; stdlib only.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict

from . import canonical_input as CI
from . import geometry_role as GR
from . import role_authority as RA

POLICY_ID = "ENTITY_ROLE_INFERENCE_V1"
POLICY_ACCEPTED = RA.POLICY_ACCEPTED

PHYSICAL_MM = {
    "wall_thickness": (80.0, 400.0),
    "pair_min_overlap_ratio": 0.5,
    "min_segment": 50.0,
    "door_radius": (500.0, 1300.0),
    "tread_going": (200.0, 400.0),
    "column_side": (150.0, 1200.0),
    "authoring_tolerance": 10.0,          # a drafted join / alignment, not a snap tolerance
}
SWING_SWEEP_RAD = (0.7, 2.1)
LEAF_LENGTH_RATIO = 0.12                  # leaf length within 12 % of the swing radius
PARALLEL_RAD = math.radians(1.0)
SHEET_ASPECT = (1.2, 1.8)
FRAME_CONTENT_SHARE = 0.95
MIN_TREADS = 4
DECISION = {"accept": 3, "min_channels": 2, "margin": 2}

# ERI roles (what the evidence says) -> geometry_role roles (what topology consumes)
WALL_FACE, COLUMN, GLAZING, DOOR_SYMBOL = "WALL_FACE", "COLUMN", "GLAZING", "DOOR_SYMBOL"
OVERHEAD, AXIS_GRID, ANNOTATION, SYMBOL, SANITARY, STAIR = (
    "OVERHEAD", "AXIS_GRID", "ANNOTATION", "SYMBOL", "SANITARY", "STAIR")
SHEET_FRAME, PLOT_BOUNDARY = "SHEET_FRAME", "PLOT_BOUNDARY"
TO_GR = {WALL_FACE: GR.TOPOLOGY_BOUNDARY, COLUMN: GR.STRUCTURAL_OBSTACLE, GLAZING: GR.GLAZING_BOUNDARY,
         DOOR_SYMBOL: GR.OPENING_SYMBOL, OVERHEAD: GR.PRESENTATION_OVERHEAD, AXIS_GRID: GR.ANNOTATION_GRAPHICS,
         ANNOTATION: GR.ANNOTATION_GRAPHICS, SYMBOL: GR.FURNITURE, SANITARY: GR.SANITARY_FIXTURE,
         STAIR: GR.STAIR_GEOMETRY, SHEET_FRAME: GR.SHEET_FRAME, PLOT_BOUNDARY: GR.SEMANTIC_BOUNDARY,
         "JOINERY": GR.FURNITURE}
NEGATIVE_ROLES = (OVERHEAD, AXIS_GRID, ANNOTATION, SYMBOL, SANITARY, STAIR, SHEET_FRAME, PLOT_BOUNDARY, DOOR_SYMBOL,
                  "JOINERY")

CONTINUOUS, UNIFORM_DASH, DASH_DOT, LT_UNKNOWN = "CONTINUOUS", "UNIFORM_DASH", "DASH_DOT", "LINETYPE_UNKNOWN"


def policy_record() -> dict:
    rec = {"id": POLICY_ID, "physical_mm": {k: list(v) if isinstance(v, tuple) else v for k, v in PHYSICAL_MM.items()},
           "swing_sweep_rad": list(SWING_SWEEP_RAD), "leaf_length_ratio": LEAF_LENGTH_RATIO,
           "parallel_rad": PARALLEL_RAD, "sheet_aspect": list(SHEET_ASPECT),
           "frame_content_share": FRAME_CONTENT_SHARE, "min_treads": MIN_TREADS, "decision": dict(DECISION),
           "motifs_v2": {"curved_glazing": dict(CURVED_GLAZING),
                         "counter_run": {k: list(v) if isinstance(v, tuple) else v for k, v in COUNTER.items()}},
           "to_geometry_role": dict(TO_GR),
           "claim": {"review_state": POLICY_ACCEPTED, "authority": POLICY_ID,
                     "scope": "this source revision + anchor + region only; never inherited; versioned",
                     "applies_through": "role_authority.claim_applies (POLICY_ACCEPTED + this authority + evidence)"},
           "inferred_doors": "door-motif occurrences are passed to room_topology.run(inferred_doors=...) and merged "
                             "into the door set the frozen opening closure uses (both leaf ends tried; exactly one "
                             "must land on admitted walls)",
           "never": ["layer name", "block name", "handle list", "coordinates", "a desired quantity", "a project"],
           "name_evidence": "CORROBORATION ONLY (recorded, never decides)"}
    rec["digest"] = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()
    return rec


# ======================================================================== small geometry
def _seg(p):
    g = p.geometry
    return (g[0], g[1], g[2], g[3])


def _len(s):
    return math.hypot(s[2] - s[0], s[3] - s[1])


def _angle(s):
    return math.atan2(s[3] - s[1], s[2] - s[0]) % math.pi


def _pt_seg(pt, s):
    ax, ay, bx, by = s
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((pt[0] - ax) * dx + (pt[1] - ay) * dy) / L2))
    return math.hypot(pt[0] - ax - t * dx, pt[1] - ay - t * dy)


def _close(a, b, tol):
    return math.hypot(a[0] - b[0], a[1] - b[1]) <= tol


def _occ(p):
    return GR._occurrence(p)


def _layer(p):
    return CI.effective_layer(p)[0]


def linetype_class(pattern) -> str:
    """From the LTYPE definition (dash / gap / dot element lengths), never from its name. None -> unknown;
    () -> continuous; dashes of one length -> UNIFORM_DASH (hidden / overhead family); two or more dash lengths
    or dots mixed with dashes -> DASH_DOT (centre / axis family)."""
    if pattern is None:
        return LT_UNKNOWN
    els = [float(e) for e in pattern]
    if not els or all(e == 0 for e in els):
        return CONTINUOUS
    dashes = sorted({round(e, 6) for e in els if e > 0})
    dots = any(e == 0 for e in els)
    if not dashes:
        return DASH_DOT if dots else LT_UNKNOWN
    if dots or (len(dashes) >= 2 and dashes[-1] >= 2 * dashes[0]):
        return DASH_DOT
    return UNIFORM_DASH


# ======================================================================== observations
def _pairs(segs, mm):
    """{index: offset_mm} for segments with a parallel partner at a wall-thickness offset overlapping >= half."""
    lo, hi = PHYSICAL_MM["wall_thickness"]
    buckets = defaultdict(list)
    for i, s in enumerate(segs):
        buckets[int(_angle(s) / PARALLEL_RAD)].append(i)
    out = {}
    nb = int(math.pi / PARALLEL_RAD) + 1
    for b, idx in buckets.items():
        cand = idx + buckets.get((b + 1) % nb, []) + buckets.get((b - 1) % nb, [])
        for i in idx:
            s = segs[i]
            L = _len(s)
            ux, uy = (s[2] - s[0]) / L, (s[3] - s[1]) / L
            best = None
            for j in cand:
                if j == i:
                    continue
                t = segs[j]
                off = abs((t[0] - s[0]) * -uy + (t[1] - s[1]) * ux) * mm
                off2 = abs((t[2] - s[0]) * -uy + (t[3] - s[1]) * ux) * mm
                if abs(off - off2) > PHYSICAL_MM["authoring_tolerance"] or not (lo <= off <= hi):
                    continue
                a0, a1 = sorted(((t[0] - s[0]) * ux + (t[1] - s[1]) * uy, (t[2] - s[0]) * ux + (t[3] - s[1]) * uy))
                ov = min(L, a1) - max(0.0, a0)
                if ov >= PHYSICAL_MM["pair_min_overlap_ratio"] * min(L, _len(t)):
                    best = off if best is None else min(best, off)
            if best is not None:
                out[i] = best
    return out


def _junction_share(segs, tol):
    ends = [(s[0], s[1]) for s in segs] + [(s[2], s[3]) for s in segs]
    grid = defaultdict(list)
    for k, e in enumerate(ends):
        grid[(int(e[0] // tol), int(e[1] // tol))].append(k)
    joined = 0
    n = len(segs)
    for k, e in enumerate(ends):
        gx, gy = int(e[0] // tol), int(e[1] // tol)
        hit = any(m != k and m % n != k % n and _close(e, ends[m], tol)
                  for dx in (-1, 0, 1) for dy in (-1, 0, 1) for m in grid.get((gx + dx, gy + dy), ()))
        if not hit:
            hit = any(j != k % n and _pt_seg(e, segs[j]) <= tol for j in range(n)) if n <= 400 else False
        joined += hit
    return joined / len(ends) if ends else 0.0


def _rectangles(segs, keys, mm):
    """Small closed rectangles from 4 segments meeting corner to corner (column outlines), any orientation.
    -> [(part keys, side_a_mm, side_b_mm, centre)]"""
    tol = PHYSICAL_MM["authoring_tolerance"] / mm
    lo, hi = PHYSICAL_MM["column_side"]
    at = defaultdict(set)
    for i, s in enumerate(segs):
        for e in ((s[0], s[1]), (s[2], s[3])):
            at[(round(e[0] / tol), round(e[1] / tol))].add(i)

    def ending_at(p, skip):
        k = (round(p[0] / tol), round(p[1] / tol))
        out = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for j in at.get((k[0] + dx, k[1] + dy), ()):
                    if j in skip:
                        continue
                    t = segs[j]
                    if _close((t[0], t[1]), p, tol):
                        out.append((j, (t[2], t[3])))
                    elif _close((t[2], t[3]), p, tol):
                        out.append((j, (t[0], t[1])))
        return out
    found, seen = [], set()
    for i, s in enumerate(segs):
        if not (lo <= _len(s) * mm <= hi):
            continue
        a, b = (s[0], s[1]), (s[2], s[3])
        ux, uy = b[0] - a[0], b[1] - a[1]
        for j, c in ending_at(b, {i}):
            vx, vy = c[0] - b[0], c[1] - b[1]
            lv = math.hypot(vx, vy)
            if lv == 0 or abs(ux * vx + uy * vy) > 0.02 * _len(s) * lv or not (lo <= lv * mm <= hi):
                continue
            d = (a[0] + c[0] - b[0], a[1] + c[1] - b[1])
            k = [m for m, e in ending_at(c, {i, j}) if _close(e, d, tol)]
            m_ = [m for m, e in ending_at(d, {i, j}) if _close(e, a, tol)]
            if not k or not m_ or k[0] == m_[0]:
                continue
            ks = tuple(sorted({keys[i], keys[j], keys[k[0]], keys[m_[0]]}))
            if len(ks) == 4 and ks not in seen:
                seen.add(ks)
                found.append((ks, round(_len(s) * mm, 1), round(lv * mm, 1), ((a[0] + c[0]) / 2, (a[1] + c[1]) / 2)))
    return found


def observe(inp: CI.CanonicalMeasurementInput, *, linetypes=None, layer_linetype=None, fills=(),
            exclude=frozenset()) -> dict:
    """Per effective layer: what the source says about its MODEL-SPACE linework (the geometry channels), plus how
    much of the layer lives inside symbol occurrences (decided per occurrence by occurrence_roles, never here).

    linetypes       {linetype name: dash pattern (element lengths)} from the source LTYPE table
    layer_linetype  {layer name: linetype name} from the source LAYER table
    fills           [(layer, (x0, y0, x1, y1))] solid-fill extents from the source (CAD structure)
    exclude         part keys already given a negative role (the sheet frame): never evidence for a layer"""
    mm = inp.unit_native_to_mm
    linetypes, layer_linetype = linetypes or {}, layer_linetype or {}
    by = defaultdict(list)
    for p in inp.parts:
        if p.visibility == CI.VISIBLE and p.identity.key not in exclude:
            by[_layer(p)].append(p)
    out = {}
    for lay, ps in sorted(by.items(), key=lambda kv: str(kv[0])):
        ms = [p for p in ps if not p.identity.instance_handles]
        segs_p = [p for p in ms if p.kind == "SEGMENT" and _len(_seg(p)) * mm >= PHYSICAL_MM["min_segment"]]
        segs = [_seg(p) for p in segs_p]
        total = sum(_len(s) for s in segs) or 0.0
        pairs = _pairs(segs, mm) if segs else {}
        paired_len = sum(_len(segs[i]) for i in pairs)
        offs = sorted(pairs.values())
        rects = _rectangles(segs, [p.identity.key for p in segs_p], mm) if segs else []
        rect_keys = {k for r in rects for k in r[0]}
        rect_len = sum(_len(_seg(p)) for p in segs_p if p.identity.key in rect_keys)
        filled = sum(1 for r in rects if any(f[1][0] <= r[3][0] <= f[1][2] and f[1][1] <= r[3][1] <= f[1][3]
                                             for f in fills))
        lt_name = layer_linetype.get(lay)
        kinds = defaultdict(int)
        for p in ms:
            kinds[p.kind] += 1
        out[lay] = {
            "parts": len(ps), "model_space_parts": len(ms), "segments": len(segs),
            "length_m": round(total * mm / 1000, 3), "kinds": dict(sorted(kinds.items())),
            "model_space_share": round(len(ms) / len(ps), 4) if ps else 0.0,
            "pair_share": round(paired_len / total, 4) if total else 0.0,
            "pair_offset_median_mm": round(offs[len(offs) // 2], 1) if offs else None,
            "junction_share": round(_junction_share(segs, PHYSICAL_MM["authoring_tolerance"] / mm), 4) if segs else 0.0,
            "rectangles": len(rects), "rect_share": round(rect_len / total, 4) if total else 0.0,
            "filled_rectangles": filled,
            "linetype": lt_name, "linetype_class": linetype_class(linetypes.get(lt_name)) if lt_name else LT_UNKNOWN,
            "curves": sum(1 for p in ms if p.kind in ("ARC", "CIRCLE", "ELLIPTICAL_ARC")),
            "name_corroboration": {"layer_lexicon": GR.layer_role(lay)},
            "_rects": rects, "_segs": segs, "_seg_keys": [p.identity.key for p in segs_p],
            "_ms_keys": sorted(p.identity.key for p in ms),
        }
    return out


def occurrence_roles(inp: CI.CanonicalMeasurementInput, skip=frozenset()) -> dict:
    """Each top-level SYMBOL occurrence (an insert in the region) by what it holds:
       text inside (a callout, north arrow, section mark, level mark, label box) and no wall-pair linework
           -> ANNOTATION
       no text, curves present, no wall-pair linework -> SYMBOL (furniture / fixture / equipment; a SANITARY
           block-name token only corroborates SANITARY)
       otherwise -> no claim (geometry_role decides; unknown content then blocks where it matters)
    -> {occ: {role, parts, evidence}}"""
    mm = inp.unit_native_to_mm
    occ = defaultdict(list)
    for p in inp.parts:
        if p.visibility == CI.VISIBLE and p.identity.instance_handles:
            occ["I" + p.identity.instance_handles[0]].append(p)
    texts = defaultdict(int)
    for t in list(inp.texts):
        if t.visibility == CI.VISIBLE and t.identity.instance_handles:
            texts["I" + t.identity.instance_handles[0]] += 1
    out = {}
    for o, ps in sorted(occ.items()):
        if o in skip:
            continue
        segs = [_seg(p) for p in ps if p.kind == "SEGMENT" and _len(_seg(p)) * mm >= PHYSICAL_MM["min_segment"]]
        total = sum(_len(s) for s in segs)
        pr = _pairs(segs, mm) if 1 < len(segs) <= 600 else {}
        pair_share = (sum(_len(segs[i]) for i in pr) / total) if total else 0.0
        curves = sum(1 for p in ps if p.kind in ("ARC", "CIRCLE", "ELLIPTICAL_ARC"))
        names = sorted({q.lineage[-1].block_name for q in ps if q.lineage and q.lineage[-1].block_name})
        ev = {"texts": texts.get(o, 0), "parts": len(ps), "curves": curves, "pair_share": round(pair_share, 4),
              "block_names": names[:6]}
        if texts.get(o, 0) and pair_share < 0.3:
            role = ANNOTATION
        elif not texts.get(o, 0) and curves and pair_share < 0.3:
            role = SANITARY if any(GR.block_name_role(n) == "SANITARY" for n in names) else SYMBOL
        else:
            continue
        out[o] = {"role": role, "parts": sorted(p.identity.key for p in ps), "evidence": ev}
    return out


# ======================================================================== motifs (part level)
def _arc_info(p):
    if p.kind != "ARC":
        return None
    cx, cy, r, a0, a1 = p.geometry
    sweep = (a1 - a0) % (2 * math.pi)
    return (cx, cy), r, (cx + r * math.cos(a0), cy + r * math.sin(a0)), (cx + r * math.cos(a1), cy + r * math.sin(a1)), sweep


def door_motifs(inp: CI.CanonicalMeasurementInput, wall_segments) -> dict:
    """Door symbols read from their own swing (OpenTakeoff door-seal idea, clean vector reimplementation):
    one swing arc (0.7 - 2.1 rad, radius 500 - 1300 mm) + a straight LEAF from the hinge of length ~= radius
    toward one swing end + the HINGE anchored on a wall-face candidate (within the maximum wall thickness).
    In a symbol occurrence the occurrence must hold exactly one such swing (geometry_role.door_signature);
    in model space the arc and its leaf are paired by geometry. -> {"doors": {occ: signature}, "parts": {occ:
    [part keys]}, "rejected": [...]} - names never decide; they are recorded as corroboration."""
    mm = inp.unit_native_to_mm
    tol = PHYSICAL_MM["authoring_tolerance"] / mm
    rlo, rhi = PHYSICAL_MM["door_radius"]
    anchor = PHYSICAL_MM["wall_thickness"][1] / mm
    vis = [p for p in inp.parts if p.visibility == CI.VISIBLE]
    by_occ = defaultdict(list)
    for p in vis:
        by_occ[_occ(p)].append(p)
    ms_segs = [p for p in vis if p.kind == "SEGMENT" and not p.identity.instance_handles]
    grid = defaultdict(list)
    for p in ms_segs:
        s = _seg(p)
        for e in ((s[0], s[1]), (s[2], s[3])):
            grid[(int(e[0] // tol), int(e[1] // tol))].append(p)
    doors, parts, rejected = {}, {}, []
    for p in sorted(vis, key=lambda q: q.identity.key):
        ai = _arc_info(p)
        if ai is None:
            continue
        c, r, a, b, sweep = ai
        rec = {"arc": p.identity.key, "radius_mm": round(r * mm, 1), "sweep_rad": round(sweep, 4)}
        if not (SWING_SWEEP_RAD[0] <= sweep <= SWING_SWEEP_RAD[1] and rlo <= r * mm <= rhi):
            continue                                     # not door-shaped: not even a candidate
        o = _occ(p)
        if p.identity.instance_handles:
            pool = [q for q in by_occ[o] if q.kind == "SEGMENT"]
        else:
            k = (int(c[0] // tol), int(c[1] // tol))
            pool = [q for dx in (-1, 0, 1) for dy in (-1, 0, 1) for q in grid.get((k[0] + dx, k[1] + dy), ())]
        leaf = None
        for q in pool:
            s = _seg(q)
            for h, f in (((s[0], s[1]), (s[2], s[3])), ((s[2], s[3]), (s[0], s[1]))):
                if _close(h, c, tol) and abs(_len(s) - r) <= LEAF_LENGTH_RATIO * r and \
                        (_close(f, a, LEAF_LENGTH_RATIO * r) or _close(f, b, LEAF_LENGTH_RATIO * r)):
                    leaf = q
                    break
            if leaf is not None:
                break
        if leaf is None:
            rejected.append(dict(rec, why="NO_LEAF_FROM_HINGE"))
            continue
        if not any(_pt_seg(c, w) <= anchor for w in wall_segments):
            rejected.append(dict(rec, why="HINGE_NOT_ANCHORED_ON_A_WALL_FACE_CANDIDATE"))
            continue
        if p.identity.instance_handles:
            sig = GR.door_signature(by_occ[o])
            if sig is None:
                rejected.append(dict(rec, why="OCCURRENCE_HAS_NOT_EXACTLY_ONE_SWING"))
                continue
            keys = sorted(q.identity.key for q in by_occ[o])
        else:
            sig = {"swing_part": p.identity.key, "hinge": c, "radius": r, "ends": (a, b), "sweep_rad": sweep}
            keys = sorted({p.identity.key, leaf.identity.key})
        sig = dict(sig, inferred=POLICY_ID, leaf_part=leaf.identity.key,
                   block_name=(p.lineage[-1].block_name if p.lineage else None))
        doors[o] = sig
        parts[o] = keys
    return {"doors": doors, "parts": parts, "rejected": rejected}


def wall_gaps(wall_segments, mm) -> list:
    """Openings in wall-face pairs: on one face line, an interval between two collinear face segments (300 - 8000
    mm wide, nothing of that line between) matched by the same interval on a parallel face line at a wall-thickness
    offset (both jambs aligned within the authoring tolerance). -> [{u, n, origin, t0, t1, o0, o1, width_mm,
    thickness_mm}] in the face frame (u along the wall, n across it)."""
    tol = PHYSICAL_MM["authoring_tolerance"] / mm
    lo, hi = PHYSICAL_MM["wall_thickness"]
    nb = int(math.pi / PARALLEL_RAD)
    lines = defaultdict(list)
    for w in wall_segments:
        L = _len(w)
        if L == 0:
            continue
        ang = _angle(w)
        b = int(round(ang / PARALLEL_RAD)) % nb
        u = (math.cos(b * PARALLEL_RAD), math.sin(b * PARALLEL_RAD))
        n = (-u[1], u[0])
        c = w[0] * n[0] + w[1] * n[1]
        t0, t1 = sorted((w[0] * u[0] + w[1] * u[1], w[2] * u[0] + w[3] * u[1]))
        lines[(b, round(c / tol))].append((t0, t1, c))
    gaps_by_b = defaultdict(list)
    for (b, ck), iv in lines.items():
        iv.sort()
        cur = list(iv[0][:2])
        merged = []
        for t0, t1, _ in iv[1:]:
            if t0 <= cur[1] + tol:
                cur[1] = max(cur[1], t1)
            else:
                merged.append(tuple(cur))
                cur = [t0, t1]
        merged.append(tuple(cur))
        c = sum(z[2] for z in iv) / len(iv)
        for (a0, a1), (b0, b1) in zip(merged, merged[1:]):
            wmm = (b0 - a1) * mm
            if 300 <= wmm <= 8000:
                gaps_by_b[b].append((c, a1, b0))
    out = []
    for b, gs in sorted(gaps_by_b.items()):
        u = (math.cos(b * PARALLEL_RAD), math.sin(b * PARALLEL_RAD))
        n = (-u[1], u[0])
        for i, (c1, a1, b1) in enumerate(gs):
            for c2, a2, b2 in gs[i + 1:]:
                d = abs(c2 - c1) * mm
                if lo <= d <= hi and abs(a1 - a2) <= tol and abs(b1 - b2) <= tol:
                    out.append({"u": u, "n": n, "t0": min(a1, a2), "t1": max(b1, b2), "o0": min(c1, c2),
                                "o1": max(c1, c2), "width_mm": round((min(b1, b2) - max(a1, a2)) * mm, 1),
                                "thickness_mm": round(d, 1)})
    return sorted(out, key=lambda g: (round(g["o0"], 3), round(g["t0"], 3)))


def _in_gap(pt, g, tol):
    t = pt[0] * g["u"][0] + pt[1] * g["u"][1]
    o = pt[0] * g["n"][0] + pt[1] * g["n"][1]
    return g["t0"] - tol <= t <= g["t1"] + tol and g["o0"] - tol <= o <= g["o1"] + tol


def glazing_motifs(inp: CI.CanonicalMeasurementInput, wall_segments, exclude=frozenset(), only=None) -> dict:
    """Glazing in a wall gap: the linework (not wall faces, not a door) lying wholly INSIDE one wall gap
    (wall_gaps), containing at least one line parallel to the wall that spans >= half the gap width; no swing.
    The whole in-gap set (glazing lines, frame caps) is the window symbol. -> {parts, windows: [...]}"""
    mm = inp.unit_native_to_mm
    tol = PHYSICAL_MM["authoring_tolerance"] / mm
    gaps = wall_gaps(wall_segments, mm)
    members = defaultdict(list)
    for p in sorted(inp.parts, key=lambda q: q.identity.key):
        if p.visibility != CI.VISIBLE or p.kind not in ("SEGMENT", "ARC") or p.identity.key in exclude:
            continue
        if only is not None and p.identity.key not in only:
            continue
        if p.kind == "ARC":
            continue                                       # a swing in a gap is a door, never glazing
        s = _seg(p)
        for i, g in enumerate(gaps):
            if _in_gap((s[0], s[1]), g, tol) and _in_gap((s[2], s[3]), g, tol):
                members[i].append(p)
                break
    parts, windows = [], []
    for i, ps in sorted(members.items()):
        g = gaps[i]
        span = max((abs((q.geometry[2] - q.geometry[0]) * g["u"][0] + (q.geometry[3] - q.geometry[1]) * g["u"][1])
                    for q in ps if abs((q.geometry[2] - q.geometry[0]) * g["n"][0] + (q.geometry[3] - q.geometry[1]) * g["n"][1]) <= tol),
                   default=0.0)
        if span * mm < 0.5 * g["width_mm"]:
            continue
        ks = sorted(q.identity.key for q in ps)
        parts += ks
        windows.append({"gap": i, "width_mm": g["width_mm"], "thickness_mm": g["thickness_mm"], "parts": ks,
                        "span_mm": round(span * mm, 1),
                        "jambs": [[round(g["t0"], 3), round(g["t1"], 3)], [round(g["o0"], 3), round(g["o1"], 3)]],
                        "axis": [round(v, 9) for v in g["u"]]})
    return {"parts": sorted(set(parts)), "windows": windows, "gaps": len(gaps)}


CURVED_GLAZING = {"min_arcs": 2, "min_radius_mm": PHYSICAL_MM["door_radius"][1], "max_band_mm": 400.0,
                  "min_sweep_rad": 0.5}
COUNTER = {"offset_mm": (450.0, 750.0), "min_front_mm": 300.0, "min_run_mm": 900.0, "max_connector_mm": 750.0,
           "front_cover": 0.8}
JOINERY = "JOINERY"


def curved_glazing_motifs(inp: CI.CanonicalMeasurementInput, wall_segments, glazing_layers, exclude=frozenset()) -> dict:
    """Curved glazing: on a layer that already carries PROVEN glazing (straight glazing in a wall gap, or an accepted
    glazing layer), a set of >= 2 concentric ARCS (same centre within the authoring tolerance) whose radii differ by
    no more than a wall thickness, each larger than any door swing, sweeping >= 0.5 rad, with BOTH ends of the outer
    and inner arcs within a wall thickness of an accepted wall face (anchored at its jambs). No text inside the
    glazing band. -> {parts, windows: [{arcs, centre, radii, sweep_rad, developed_length_mm, chord_mm, ...}]}"""
    mm = inp.unit_native_to_mm
    tol = PHYSICAL_MM["authoring_tolerance"] / mm
    reach = PHYSICAL_MM["wall_thickness"][1] / mm
    arcs = [p for p in sorted(inp.parts, key=lambda q: q.identity.key) if p.visibility == CI.VISIBLE
            and p.kind == "ARC" and not p.identity.instance_handles and p.identity.key not in exclude
            and _layer(p) in glazing_layers and p.geometry[2] * mm > CURVED_GLAZING["min_radius_mm"]
            and _arc_info(p)[4] >= CURVED_GLAZING["min_sweep_rad"]]
    groups = []
    for p in arcs:
        c = (p.geometry[0], p.geometry[1])
        for g in groups:
            if g["layer"] == _layer(p) and math.hypot(c[0] - g["c"][0], c[1] - g["c"][1]) <= tol:
                g["arcs"].append(p)
                break
        else:
            groups.append({"layer": _layer(p), "c": c, "arcs": [p]})
    out, parts = [], []
    for g in groups:
        ps = sorted(g["arcs"], key=lambda q: q.geometry[2])
        if len(ps) < CURVED_GLAZING["min_arcs"]:
            continue
        radii = [q.geometry[2] for q in ps]
        if (radii[-1] - radii[0]) * mm > CURVED_GLAZING["max_band_mm"]:
            continue
        if any((b - a) * mm >= PHYSICAL_MM["wall_thickness"][0] for a, b in zip(radii, radii[1:])):
            continue                                       # lines a wall thickness apart: a curved wall, not glazing
        anchored = True
        for q in (ps[0], ps[-1]):
            ai = _arc_info(q)
            for end in (ai[2], ai[3]):
                if not any(_pt_seg(end, w) <= reach for w in wall_segments):
                    anchored = False
        if not anchored:
            continue
        lens = [q.geometry[2] * _arc_info(q)[4] * mm for q in ps]
        mid = ps[len(ps) // 2]
        ai = _arc_info(mid)
        ks = sorted(q.identity.key for q in ps)
        parts += ks
        out.append({"layer": str(g["layer"]), "parts": ks, "centre": [round(v, 3) for v in g["c"]],
                    "radii_mm": [round(r * mm, 1) for r in radii],
                    "sweep_rad": [round(_arc_info(q)[4], 6) for q in ps],
                    "arc_lengths_mm": [round(v, 1) for v in lens],
                    "developed_length_mm": round(sum(lens) / len(lens), 1),
                    "developed_length_range_mm": [round(min(lens), 1), round(max(lens), 1)],
                    "chord_mm": round(math.hypot(ai[2][0] - ai[3][0], ai[2][1] - ai[3][1]) * mm, 1),
                    "band_mm": round((radii[-1] - radii[0]) * mm, 1), "form": "CURVED"})
    return {"parts": sorted(set(parts)), "windows": out}


def counter_run_motifs(inp: CI.CanonicalMeasurementInput, wall_segments, exclude=frozenset()) -> dict:
    """Fixed counters / joinery: a chain of single model-space lines (no wall layer) in which
       FRONT       a segment >= 300 mm parallel to an accepted wall face at a constant 450 - 750 mm offset, the
                   face covering >= 80 % of it, no other wall face between them, and NO parallel mate at a wall
                   thickness (80 - 400 mm) - so it is not a wall face itself;
       CONNECTOR   a segment <= 750 mm joining two fronts or a front to a wall face;
    the chain's free ends lie on accepted wall faces, its fronts total >= 900 mm, and no room label lies in the strip
    between a front and its wall. -> {parts, runs: [{parts, fronts, offsets_mm, front_length_mm}]}"""
    mm = inp.unit_native_to_mm
    tol = PHYSICAL_MM["authoring_tolerance"] / mm
    lo, hi = (v / mm for v in COUNTER["offset_mm"])
    wlo, whi = (v / mm for v in PHYSICAL_MM["wall_thickness"])
    vis = [p for p in sorted(inp.parts, key=lambda q: q.identity.key) if p.visibility == CI.VISIBLE
           and p.kind == "SEGMENT" and not p.identity.instance_handles and p.identity.key not in exclude]
    segs = {p.identity.key: _seg(p) for p in vis}
    allseg = list(segs.items())
    texts = [(t.x, t.y) for t in inp.texts if t.visibility == CI.VISIBLE and t.x is not None and t.value
             and any(ch.isalpha() for ch in t.value)]

    def frame(s):
        L = _len(s)
        u = ((s[2] - s[0]) / L, (s[3] - s[1]) / L)
        return L, u, (-u[1], u[0])

    openings = []                                             # proven wall gaps: a face line interrupted by an
    for g in wall_gaps(wall_segments, mm):                    # opening is still that wall line (coverage only)
        for o in (g["o0"], g["o1"]):
            a = (g["u"][0] * g["t0"] + g["n"][0] * o, g["u"][1] * g["t0"] + g["n"][1] * o)
            b = (g["u"][0] * g["t1"] + g["n"][0] * o, g["u"][1] * g["t1"] + g["n"][1] * o)
            openings.append((a[0], a[1], b[0], b[1]))

    def front_of(k, s):
        L, u, n = frame(s)
        if L * mm < COUNTER["min_front_mm"]:
            return None
        par = [w for w in wall_segments if _len(w) > 0 and (abs(_angle(w) - _angle(s)) % math.pi <= PARALLEL_RAD or
                                                           abs(abs(_angle(w) - _angle(s)) - math.pi) <= PARALLEL_RAD)]
        par_open = [w for w in openings if _len(w) > 0 and (abs(_angle(w) - _angle(s)) % math.pi <= PARALLEL_RAD or
                                                           abs(abs(_angle(w) - _angle(s)) - math.pi) <= PARALLEL_RAD)]
        offs = defaultdict(list)
        for w in par + par_open:
            o = (w[0] - s[0]) * n[0] + (w[1] - s[1]) * n[1]
            if lo <= abs(o) <= hi:
                t0, t1 = sorted(((w[0] - s[0]) * u[0] + (w[1] - s[1]) * u[1], (w[2] - s[0]) * u[0] + (w[3] - s[1]) * u[1]))
                offs[round(o / tol)].append((max(0.0, t0), min(L, t1), o))
        best = None
        for key, iv in offs.items():
            iv.sort()
            cov, cur = 0.0, None
            for a, b, _ in iv:
                if b <= a:
                    continue
                if cur is None or a > cur[1]:
                    cov += (cur[1] - cur[0]) if cur else 0.0
                    cur = [a, b]
                else:
                    cur[1] = max(cur[1], b)
            cov += (cur[1] - cur[0]) if cur else 0.0
            o = iv[0][2]
            if cov >= COUNTER["front_cover"] * L:
                # no wall face strictly between the front and that face
                between = [w for w in par if 0 < ((w[0] - s[0]) * n[0] + (w[1] - s[1]) * n[1]) * (1 if o > 0 else -1)
                           < abs(o) - tol]
                if between:
                    continue
                if best is None or abs(o) < abs(best):
                    best = o
        if best is None:
            return None
        for k2, s2 in allseg:                                 # a mate at a wall thickness = a wall, not a counter
            if k2 == k or _len(s2) == 0:
                continue
            if abs(_angle(s2) - _angle(s)) % math.pi > PARALLEL_RAD and abs(abs(_angle(s2) - _angle(s)) - math.pi) > PARALLEL_RAD:
                continue
            o2 = abs((s2[0] - s[0]) * n[0] + (s2[1] - s[1]) * n[1])
            t0, t1 = sorted(((s2[0] - s[0]) * u[0] + (s2[1] - s[1]) * u[1], (s2[2] - s[0]) * u[0] + (s2[3] - s[1]) * u[1]))
            if wlo <= o2 <= whi and min(L, t1) - max(0.0, t0) >= 0.5 * L:
                return None
        for x, y in texts:                                    # a label in the strip: the strip is a room
            t = (x - s[0]) * u[0] + (y - s[1]) * u[1]
            o = (x - s[0]) * n[0] + (y - s[1]) * n[1]
            if 0 <= t <= L and 0 < o * (1 if best > 0 else -1) < abs(best):
                return None
        return round(abs(best) * mm, 1)
    fronts = {k: f for k, s in segs.items() if (f := front_of(k, s)) is not None}
    # chains: fronts + short connectors joined end to end
    cand = dict(fronts)
    for k, s in segs.items():
        if k not in cand and _len(s) * mm <= COUNTER["max_connector_mm"]:
            cand[k] = None
    ends = {k: ((segs[k][0], segs[k][1]), (segs[k][2], segs[k][3])) for k in cand}
    adj = defaultdict(set)
    ks = sorted(cand)
    for i, a in enumerate(ks):
        for b in ks[i + 1:]:
            if any(_close(p, q, tol) for p in ends[a] for q in ends[b]):
                adj[a].add(b)
                adj[b].add(a)
    seen, runs, parts = set(), [], []
    for k0 in sorted(fronts):
        if k0 in seen:
            continue
        comp, stack = set(), [k0]
        while stack:
            k = stack.pop()
            if k in comp:
                continue
            comp.add(k)
            stack += [j for j in adj[k] if j not in comp and (j in fronts or any(m in fronts for m in adj[j]))]
        seen |= comp
        conns = [k for k in comp if k not in fronts]
        if any(not any(m in fronts for m in adj[k] & comp) for k in conns):
            continue
        free = []
        for k in comp:
            for p in ends[k]:
                if not any(_close(p, q, tol) for j in comp - {k} for q in ends[j]):
                    free.append(p)
        if not free or not all(any(_pt_seg(p, w) <= tol for w in wall_segments) for p in free):
            continue
        flen = sum(_len(segs[k]) for k in comp if k in fronts) * mm
        if flen < COUNTER["min_run_mm"]:
            continue
        runs.append({"parts": sorted(comp), "fronts": sorted(k for k in comp if k in fronts),
                     "offsets_mm": sorted({fronts[k] for k in comp if k in fronts}),
                     "front_length_mm": round(flen, 1), "free_ends_on_walls": len(free)})
        parts += sorted(comp)
    return {"parts": sorted(set(parts)), "runs": runs}


def _cross(s, w):
    """Proper interior intersection of two segments (not at an end point)."""
    d1x, d1y, d2x, d2y = s[2] - s[0], s[3] - s[1], w[2] - w[0], w[3] - w[1]
    den = d1x * d2y - d1y * d2x
    if den == 0:
        return False
    t = ((w[0] - s[0]) * d2y - (w[1] - s[1]) * d2x) / den
    u = ((w[0] - s[0]) * d1y - (w[1] - s[1]) * d1x) / den
    return 1e-6 < t < 1 - 1e-6 and 1e-6 < u < 1 - 1e-6


def residual_motifs(inp: CI.CanonicalMeasurementInput, wall_segments, exclude=frozenset()) -> dict:
    """Three physical facts for linework no layer decision covered:
      WALL_CROSSING  an open segment that passes THROUGH both faces of a wall band (a partition ends at a wall; a
                     service run, drain or leader crosses it) -> ANNOTATION (never topology)
      ISOLATED_SMALL_CIRCLE  a circle (diameter <= the largest column side) touching no wall face, no text inside
                     -> SYMBOL (fixture / drain footprint)
      GAP_INFILL     linework wholly inside one wall gap that covers >= 90 % of the gap width but carries no
                     swing and no spanning glazing line -> DOOR_SYMBOL of unresolved type (sliding / folding
                     candidate): no closure is derived from it
    -> {parts: {key: role}, gap_infill: [...]}"""
    mm = inp.unit_native_to_mm
    tol = PHYSICAL_MM["authoring_tolerance"] / mm
    lo, hi = PHYSICAL_MM["wall_thickness"]
    out, infill = {}, []
    vis = [p for p in inp.parts if p.visibility == CI.VISIBLE and p.identity.key not in exclude
           and not p.identity.instance_handles]
    for p in sorted(vis, key=lambda q: q.identity.key):
        if p.kind != "SEGMENT":
            continue
        s = _seg(p)
        hits = [w for w in wall_segments if _cross(s, w)]
        crossed = False
        for i, a in enumerate(hits):
            for b in hits[i + 1:]:
                if abs(_angle(a) - _angle(b)) % math.pi <= PARALLEL_RAD or \
                        abs(abs(_angle(a) - _angle(b)) - math.pi) <= PARALLEL_RAD:
                    L = _len(a)
                    n = (-(a[3] - a[1]) / L, (a[2] - a[0]) / L)
                    off = abs((b[0] - a[0]) * n[0] + (b[1] - a[1]) * n[1]) * mm
                    if lo <= off <= hi:
                        crossed = True
                        break
            if crossed:
                break
        if crossed:
            out[p.identity.key] = ANNOTATION
    texts = [(t.x, t.y) for t in inp.texts if t.visibility == CI.VISIBLE and t.x is not None]
    for p in sorted(vis, key=lambda q: q.identity.key):
        if p.kind != "CIRCLE" or p.identity.key in out:
            continue
        cx, cy, r = p.geometry[:3]
        if 2 * r * mm > PHYSICAL_MM["column_side"][1]:
            continue
        if any(_pt_seg((cx, cy), w) <= r + tol for w in wall_segments):
            continue
        if any(math.hypot(x - cx, y - cy) <= r for x, y in texts):
            continue
        out[p.identity.key] = SYMBOL
    gaps = wall_gaps(wall_segments, mm)
    members = defaultdict(list)
    for p in sorted(vis, key=lambda q: q.identity.key):
        if p.identity.key in out:
            continue
        if p.kind == "SEGMENT":
            pts = [(p.geometry[0], p.geometry[1]), (p.geometry[2], p.geometry[3])]
        elif p.kind == "ARC":
            ai = _arc_info(p)
            if ai[1] * mm >= PHYSICAL_MM["door_radius"][0]:
                continue                                   # a swing: the door motif decides it
            pts = [ai[0]]
        else:
            continue
        for i, g in enumerate(gaps):
            if all(_in_gap(q, g, tol) for q in pts):
                members[i].append(p)
                break
    for i, ps in sorted(members.items()):
        g = gaps[i]
        iv = []
        for q in ps:
            if q.kind != "SEGMENT":
                continue
            t0 = q.geometry[0] * g["u"][0] + q.geometry[1] * g["u"][1]
            t1 = q.geometry[2] * g["u"][0] + q.geometry[3] * g["u"][1]
            iv.append(tuple(sorted((t0, t1))))
        iv.sort()
        cover, cur = 0.0, None
        for a0, a1 in iv:
            if cur is None or a0 > cur[1]:
                if cur is not None:
                    cover += cur[1] - cur[0]
                cur = [max(a0, g["t0"]), min(a1, g["t1"])]
            else:
                cur[1] = max(cur[1], min(a1, g["t1"]))
        if cur is not None:
            cover += max(0.0, cur[1] - cur[0])
        if cover * mm >= 0.9 * g["width_mm"]:
            ks = sorted(q.identity.key for q in ps)
            for k in ks:
                out[k] = DOOR_SYMBOL
            infill.append({"gap": i, "width_mm": g["width_mm"], "thickness_mm": g["thickness_mm"], "parts": ks,
                           "type": "NO_SWING_INFILL (sliding / folding candidate)",
                           "jambs": [[round(g["t0"], 3), round(g["t1"], 3)], [round(g["o0"], 3), round(g["o1"], 3)]],
                           "axis": [round(v, 9) for v in g["u"]]})
    return {"parts": out, "gap_infill": infill}


def tread_motifs(inp: CI.CanonicalMeasurementInput, exclude=frozenset()) -> dict:
    """Stair treads: >= MIN_TREADS parallel segments of equal length (authoring tolerance) on one layer, spaced
    at a regular going of 200 - 400 mm with their ends aligned. -> {runs: [{parts, going_mm, width_mm, risers}]}"""
    mm = inp.unit_native_to_mm
    tol = PHYSICAL_MM["authoring_tolerance"] / mm
    glo, ghi = PHYSICAL_MM["tread_going"]
    groups = defaultdict(list)
    for p in inp.parts:
        if p.visibility == CI.VISIBLE and p.kind == "SEGMENT" and p.identity.key not in exclude:
            s = _seg(p)
            L = _len(s)
            if L * mm >= 600:
                groups[(_layer(p), round(_angle(s) / PARALLEL_RAD) % int(math.pi / PARALLEL_RAD), round(L / tol))].append(p)
    runs = []
    for (lay, ab, lk), ps in sorted(groups.items(), key=lambda kv: str(kv[0])):
        if len(ps) < MIN_TREADS:
            continue
        s0 = _seg(ps[0])
        L = _len(s0)
        ux, uy = (s0[2] - s0[0]) / L, (s0[3] - s0[1]) / L
        rows = []
        for p in ps:
            s = _seg(p)
            mx, my = (s[0] + s[2]) / 2, (s[1] + s[3]) / 2
            rows.append(((mx - s0[0]) * -uy + (my - s0[1]) * ux, (mx - s0[0]) * ux + (my - s0[1]) * uy, p))
        rows.sort(key=lambda z: z[0])
        cur = [rows[0]]
        for z in rows[1:] + [None]:
            if z is not None and abs(z[1] - cur[-1][1]) <= tol and glo <= (z[0] - cur[-1][0]) * mm <= ghi and \
                    (len(cur) < 2 or abs((z[0] - cur[-1][0]) - (cur[1][0] - cur[0][0])) <= tol):
                cur.append(z)
                continue
            if len(cur) >= MIN_TREADS:
                runs.append({"layer": lay, "parts": sorted(c[2].identity.key for c in cur),
                             "going_mm": round((cur[1][0] - cur[0][0]) * mm, 1), "width_mm": round(L * mm, 1),
                             "tread_lines": len(cur)})
            cur = [z] if z is not None else []
    return {"runs": runs}


def sheet_frames(inp: CI.CanonicalMeasurementInput) -> dict:
    """The sheet frame of the region: a closed rectangle (4 segments) with sheet aspect that encloses at least
    FRAME_CONTENT_SHARE of the region's visible parts. -> {frames: [{parts, bounds}]}"""
    mm = inp.unit_native_to_mm
    tol = PHYSICAL_MM["authoring_tolerance"] / mm
    segs = [p for p in inp.parts if p.visibility == CI.VISIBLE and p.kind == "SEGMENT"]
    mids = [((p.geometry[0] + p.geometry[2]) / 2, (p.geometry[1] + p.geometry[3]) / 2) for p in segs]
    H = [p for p in segs if abs(p.geometry[1] - p.geometry[3]) <= tol and abs(p.geometry[0] - p.geometry[2]) > 0]
    V = [p for p in segs if abs(p.geometry[0] - p.geometry[2]) <= tol and abs(p.geometry[1] - p.geometry[3]) > 0]
    H.sort(key=lambda p: -abs(p.geometry[0] - p.geometry[2]))
    out = []
    longest = H[:12]
    for i, a in enumerate(longest):
        for b in longest[i + 1:]:
            xa = sorted((a.geometry[0], a.geometry[2]))
            xb = sorted((b.geometry[0], b.geometry[2]))
            if abs(xa[0] - xb[0]) > tol or abs(xa[1] - xb[1]) > tol:
                continue
            y0, y1 = sorted((a.geometry[1], b.geometry[1]))
            w, h = xa[1] - xa[0], y1 - y0
            if h <= 0 or not (SHEET_ASPECT[0] <= max(w, h) / min(w, h) <= SHEET_ASPECT[1]):
                continue
            sides = [v for v in V if any(abs(v.geometry[0] - x) <= tol for x in xa)
                     and abs(min(v.geometry[1], v.geometry[3]) - y0) <= tol and abs(max(v.geometry[1], v.geometry[3]) - y1) <= tol]
            if len({round(v.geometry[0] / tol) for v in sides}) < 2:
                continue
            inside = sum(1 for m in mids if xa[0] - tol <= m[0] <= xa[1] + tol and y0 - tol <= m[1] <= y1 + tol)
            if inside < FRAME_CONTENT_SHARE * len(mids):
                continue
            out.append({"parts": sorted({a.identity.key, b.identity.key} | {v.identity.key for v in sides}),
                        "bounds": (xa[0], y0, xa[1], y1), "aspect": round(max(w, h) / min(w, h), 4),
                        "content_share": round(inside / len(mids), 4)})
    return {"frames": out}


def plot_boundaries(inp: CI.CanonicalMeasurementInput, wall_segments, exclude=frozenset()) -> dict:
    """Site / plot boundary: unpaired linework that lies OUTSIDE the extent of every wall-face candidate (the
    building), not on a wall layer, and that bounds the building on at least three sides. -> part keys."""
    if not wall_segments:
        return {"parts": [], "building_extent": None}
    xs = [v for w in wall_segments for v in (w[0], w[2])]
    ys = [v for w in wall_segments for v in (w[1], w[3])]
    bx = (min(xs), min(ys), max(xs), max(ys))
    tol = PHYSICAL_MM["authoring_tolerance"] / inp.unit_native_to_mm
    cand, sides = [], set()
    for p in sorted(inp.parts, key=lambda q: q.identity.key):
        if p.visibility != CI.VISIBLE or p.kind != "SEGMENT" or p.identity.key in exclude:
            continue
        s = _seg(p)
        if _len(s) < 0.25 * min(bx[2] - bx[0], bx[3] - bx[1]):
            continue
        if max(s[0], s[2]) < bx[0] - tol:
            sides.add("W")
        elif min(s[0], s[2]) > bx[2] + tol:
            sides.add("E")
        elif max(s[1], s[3]) < bx[1] - tol:
            sides.add("S")
        elif min(s[1], s[3]) > bx[3] + tol:
            sides.add("N")
        else:
            continue
        cand.append(p.identity.key)
    return {"parts": cand if len(sides) >= 3 else [], "sides": sorted(sides), "building_extent": bx}


# ======================================================================== candidates and decisions
def layer_candidates(obs: dict, doors_anchored=None, glazing_share=None, corroboration=None) -> dict:
    """{layer: [candidate]} - each candidate {role, score, channels{channel: points}, required, reasons}.
    Geometry channels read MODEL-SPACE linework only; CONTRA evidence removes a candidate.
    corroboration {layer: {role: [other region ids]}}: the same layer ACCEPTED for that role in another plan region
    of the SAME source revision (one drawing, one drafting convention) adds CONTEXT_SAME_SOURCE (+1); it never
    creates a candidate by itself and never crosses source revisions."""
    doors_anchored, glazing_share, corroboration = doors_anchored or {}, glazing_share or {}, corroboration or {}
    out = {}
    for lay, o in obs.items():
        cands = []
        lt = o["linetype_class"]
        if o["segments"] == 0:
            out[lay] = []
            continue
        # WALL_FACE: paired continuous model-space lines at a wall-thickness offset
        ch = {}
        if o["pair_share"] >= 0.5:
            ch["GEOMETRY_PAIRS"] = 2
        elif o["pair_share"] >= 0.3:
            ch["GEOMETRY_PAIRS"] = 1
        if o["junction_share"] >= 0.6:
            ch["GEOMETRY_JOINS"] = 1
        if doors_anchored.get(lay, 0) >= 1:
            ch["CONTEXT_DOOR_HINGES"] = 1
        contra = []
        if lt in (UNIFORM_DASH, DASH_DOT):
            contra.append(f"linetype {lt}")
        if o["rect_share"] >= 0.7:
            contra.append(f"rect share {o['rect_share']} (closed outlines, not faces)")
        if glazing_share.get(lay, 0.0) >= 0.5:
            contra.append(f"glazing-in-gap share {glazing_share[lay]} (lines span other walls' gaps)")
        if "GEOMETRY_PAIRS" in ch and not contra:
            cands.append({"role": WALL_FACE, "channels": ch, "required": "GEOMETRY_PAIRS",
                          "reasons": [f"pair share {o['pair_share']}", f"pair offset median {o['pair_offset_median_mm']} mm",
                                      f"junction share {o['junction_share']}", f"linetype {lt}",
                                      f"door hinges anchored {doors_anchored.get(lay, 0)}"]})
        # GLAZING (layer-level only as a CANDIDATE: glazing parts are claimed per part by the motif)
        if glazing_share.get(lay, 0.0) >= 0.5:
            cands.append({"role": GLAZING, "channels": {"GEOMETRY_GAP_SPAN": 2, "CAD_MODEL_SPACE": 1},
                          "required": "GEOMETRY_GAP_SPAN", "part_level_only": True,
                          "reasons": [f"glazing-in-gap share {glazing_share[lay]}"]})
        # OVERHEAD / AXIS from the linetype definition
        if lt in (UNIFORM_DASH, DASH_DOT):
            ch = {"CAD_LINETYPE_PATTERN": 2}
            if o["pair_share"] < 0.5:
                ch["GEOMETRY_NOT_WALL_PAIRS"] = 1
            if o["junction_share"] < 0.6:
                ch["GEOMETRY_OPEN_NETWORK"] = 1
            cands.append({"role": OVERHEAD if lt == UNIFORM_DASH else AXIS_GRID, "channels": ch,
                          "required": "CAD_LINETYPE_PATTERN",
                          "reasons": [f"linetype {o['linetype']} = {lt}", f"pair share {o['pair_share']}"]})
        # COLUMN: small closed rectangles, filled, model space
        if o["rectangles"] >= 2 and o["rect_share"] >= 0.7:
            ch = {"GEOMETRY_RECTANGLES": 2}
            if o["filled_rectangles"] >= 0.5 * o["rectangles"]:
                ch["CAD_SOLID_FILL"] = 1
            if lt in (CONTINUOUS, LT_UNKNOWN) and o["curves"] == 0:
                ch["CAD_CONTINUOUS_STRAIGHT"] = 1
            cands.append({"role": COLUMN, "channels": ch, "required": "GEOMETRY_RECTANGLES",
                          "reasons": [f"{o['rectangles']} closed rectangles {list(PHYSICAL_MM['column_side'])} mm",
                                      f"rect share {o['rect_share']}", f"filled {o['filled_rectangles']}"]})
        for c in cands:
            if corroboration.get(lay, {}).get(c["role"]):
                c["channels"]["CONTEXT_SAME_SOURCE"] = 1
                c["reasons"].append("accepted in other regions of this source: " + ",".join(corroboration[lay][c["role"]]))
            c["score"] = sum(c["channels"].values())
        out[lay] = sorted(cands, key=lambda c: (-c["score"], c["role"]))
    return out


def decide(cands: dict) -> dict:
    """{layer: {state ACCEPTED | PART_LEVEL | BLOCKED | NO_CANDIDATE, role, score, competing, why}}"""
    out = {}
    for lay, cs in sorted(cands.items(), key=lambda kv: str(kv[0])):
        if not cs:
            out[lay] = {"state": "NO_CANDIDATE", "role": None, "why": "no role candidate from any channel"}
            continue
        best = cs[0]
        nxt = cs[1]["score"] if len(cs) > 1 else None
        if best["score"] < DECISION["accept"] or len(best["channels"]) < DECISION["min_channels"] \
                or best["required"] not in best["channels"]:
            out[lay] = {"state": "BLOCKED", "role": None, "best": best["role"], "score": best["score"],
                        "why": f"score {best['score']} / channels {len(best['channels'])} below the frozen decision"}
        elif nxt is not None and best["score"] - nxt < DECISION["margin"]:
            out[lay] = {"state": "BLOCKED", "role": None, "best": best["role"], "score": best["score"],
                        "competing": [c["role"] for c in cs[1:]], "why": "a competing candidate is within the margin"}
        elif best.get("part_level_only"):
            out[lay] = {"state": "PART_LEVEL", "role": None, "best": best["role"], "score": best["score"],
                        "why": "decided per part (motif); the rest of the layer stays UNKNOWN"}
        else:
            out[lay] = {"state": "ACCEPTED", "role": best["role"], "score": best["score"],
                        "channels": best["channels"], "reasons": best["reasons"],
                        "competing": [c["role"] for c in cs[1:]]}
    return out


def _accepted(dec, role):
    return {l for l, d in dec.items() if d["state"] == "ACCEPTED" and d["role"] == role}


def _glazing_share(inp, obs, wall_layers, frame_keys):
    """For each wall-pair candidate layer L: the largest share of its >= 300 mm model-space lines that lie as
    glazing inside the gaps of ONE other wall-pair candidate layer (each other layer tested on its own, so a
    mixed layer cannot fill another layer's gaps)."""
    out = {}
    mm = inp.unit_native_to_mm
    for L in sorted(wall_layers, key=str):
        mine = [k for s, k in zip(obs[L]["_segs"], obs[L]["_seg_keys"]) if _len(s) * mm >= 300 and k not in frame_keys]
        if not mine:
            continue
        best = 0.0
        for M in sorted(wall_layers - {L}, key=str):
            others = [s for s, k in zip(obs[M]["_segs"], obs[M]["_seg_keys"]) if k not in frame_keys]
            g = glazing_motifs(inp, others, only=frozenset(mine))
            best = max(best, len(g["parts"]) / len(mine))
        out[L] = round(best, 4)
    return out


# ======================================================================== the whole inference
def infer(inp: CI.CanonicalMeasurementInput, *, linetypes=None, layer_linetype=None, fills=(), version=1,
          corroboration=None) -> dict:
    """Run every step for one region and return observations, candidates, decisions, motifs, the claims and the
    inferred door set. Order: frame -> layer pre-decision -> glazing-in-gap test of wall candidates against each
    other -> door motifs (hinges on wall candidates) -> final layer decision -> part motifs (glazing, treads,
    plot boundary, symbol / annotation occurrences). Every claim names its parts explicitly (part_keys)."""
    assert POLICY_ID == RA.INFERENCE_AUTHORITY
    vis = [p for p in inp.parts if p.visibility == CI.VISIBLE]
    frames = sheet_frames(inp)
    frame_keys = {k for f in frames["frames"] for k in f["parts"]}
    obs = observe(inp, linetypes=linetypes, layer_linetype=layer_linetype, fills=fills, exclude=frozenset(frame_keys))
    pre_c = layer_candidates(obs)
    paired = {l for l, cs in pre_c.items() if any(c["role"] == WALL_FACE for c in cs)}   # wall-pair evidence
    gshare = _glazing_share(inp, obs, paired, frame_keys)
    pre = decide(layer_candidates(obs, glazing_share=gshare, corroboration=corroboration))
    wall_layers = _accepted(pre, WALL_FACE)
    wall_segs = [s for l in wall_layers for s, k in zip(obs[l]["_segs"], obs[l]["_seg_keys"]) if k not in frame_keys]
    dm = door_motifs(inp, wall_segs)
    anchored = defaultdict(int)
    reach = PHYSICAL_MM["wall_thickness"][1] / inp.unit_native_to_mm
    for o, sig in dm["doors"].items():
        for l in wall_layers:
            if any(_pt_seg(sig["hinge"], s) <= reach for s in obs[l]["_segs"]):
                anchored[l] += 1
    cands = layer_candidates(obs, anchored, gshare, corroboration)
    dec = decide(cands)
    door_keys = {k for ks in dm["parts"].values() for k in ks}
    wall_layers = _accepted(dec, WALL_FACE)
    wall_ms = {k for l in wall_layers for k in obs[l]["_ms_keys"]}
    wall_segs = [s for l in wall_layers for s, k in zip(obs[l]["_segs"], obs[l]["_seg_keys"])
                 if k not in frame_keys and k not in door_keys]
    taken = set(frame_keys) | door_keys
    gm = glazing_motifs(inp, wall_segs, exclude=frozenset(wall_ms | taken))
    taken |= set(gm["parts"])
    tm = tread_motifs(inp, exclude=frozenset(wall_ms | taken))
    tread_keys = {k for r in tm["runs"] for k in r["parts"]}
    taken |= tread_keys
    pb = plot_boundaries(inp, wall_segs, exclude=frozenset(wall_ms | taken))
    taken |= set(pb["parts"])
    col_ms = {k for l in _accepted(dec, COLUMN) for k in obs[l]["_ms_keys"]}
    key_lay = {p.identity.key: _layer(p) for p in vis}
    glz_layers = {key_lay[k] for k in gm["parts"] if k in key_lay} | set(_accepted(dec, GLAZING))
    cg = curved_glazing_motifs(inp, wall_segs, glz_layers, exclude=frozenset(wall_ms | col_ms | taken))
    taken |= set(cg["parts"])
    cr = counter_run_motifs(inp, wall_segs, exclude=frozenset(wall_ms | col_ms | taken))
    taken |= set(cr["parts"])
    rm = residual_motifs(inp, wall_segs, exclude=frozenset(wall_ms | col_ms | taken))
    occ = occurrence_roles(inp, skip=frozenset(dm["doors"]))
    part_roles = {}
    for role, keys in ((SHEET_FRAME, frame_keys), (DOOR_SYMBOL, door_keys), (GLAZING, set(gm["parts"])),
                       (GLAZING, set(cg["parts"])), (JOINERY, set(cr["parts"])),
                       (STAIR, tread_keys), (PLOT_BOUNDARY, set(pb["parts"]))):
        for k in sorted(keys):
            part_roles.setdefault(k, role)
    for o, v in occ.items():
        for k in v["parts"]:
            part_roles.setdefault(k, v["role"])
    for k, role in sorted(rm["parts"].items()):
        part_roles.setdefault(k, role)
    for l, d in dec.items():
        if d["state"] == "ACCEPTED":
            for k in obs[l]["_ms_keys"]:
                part_roles.setdefault(k, d["role"])
    key_layer = {p.identity.key: _layer(p) for p in vis}
    groups = defaultdict(list)
    for k, role in part_roles.items():
        if key_layer.get(k) is not None:
            groups[(role, key_layer[k])].append(k)
    rev = inp.revision
    claims = []
    for (role, lay), ks in sorted(groups.items(), key=lambda kv: (kv[0][0], str(kv[0][1]))):
        d = dec.get(lay, {})
        layer_level = d.get("state") == "ACCEPTED" and d.get("role") == role
        ev = (tuple(f"{c}={v}" for c, v in sorted(d["channels"].items())) + tuple(d["reasons"])) if layer_level \
            else (f"MOTIF={role}", f"parts={len(ks)}")
        claims.append(RA.SourceLayerRoleClaim(
            f"ERI-{'L' if layer_level else 'P'}-{role}-{lay}", rev.revision_id, rev.anchor_sha256, lay, "EFFECTIVE",
            TO_GR[role], ev, POLICY_ID, POLICY_ACCEPTED, scope=inp.region_id, version=version,
            part_keys=tuple(sorted(ks))))
    clean_obs = {l: {k: v for k, v in o.items() if not k.startswith("_")} for l, o in obs.items()}
    return {"policy": policy_record(), "observations": clean_obs, "candidates": cands, "decisions": dec,
            "glazing_share": gshare, "frames": frames, "doors": dm, "glazing": gm, "treads": tm,
            "plot_boundary": pb, "occurrences": occ, "residual": rm, "curved_glazing": cg, "counter_runs": cr,
            "columns": {l: [{"parts": list(r[0]), "w_mm": r[1], "h_mm": r[2], "centre": r[3]} for r in obs[l]["_rects"]]
                        for l in _accepted(dec, COLUMN)},
            "claims": claims, "inferred_doors": dm["doors"], "part_roles": part_roles}


def corroboration_from(results: dict) -> dict:
    """{region id: infer() result} of ONE source revision -> per region {layer: {role: [OTHER region ids]}} built
    from first-pass decisions (pass 2 uses it; a region never corroborates itself)."""
    acc = defaultdict(lambda: defaultdict(set))
    for rid, r in results.items():
        for lay, d in r["decisions"].items():
            if d["state"] == "ACCEPTED":
                acc[lay][d["role"]].add(rid)
    out = {}
    for rid in results:
        out[rid] = {lay: {role: sorted(rs - {rid}) for role, rs in roles.items() if rs - {rid}}
                    for lay, roles in acc.items()}
    return out


def claim_record(c) -> dict:
    return {"claim_id": c.claim_id, "layer": c.layer, "role": c.role, "review_state": c.review_state,
            "authority": c.authority, "scope": c.scope, "version": c.version, "evidence": list(c.evidence),
            "part_keys": len(c.part_keys)}
