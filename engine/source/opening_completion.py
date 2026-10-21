"""OPENING COMPLETION (V3) - zero-material topology closures for door openings the frozen door-closure rule leaves
open, from positive door evidence only.

Three generic gaps of the frozen TS01 chain (room_topology + topology.opening_closures):

  0. NEAR-COLLINEAR RAY HIT. topology._ray_hit treats a segment as parallel to the ray only when the cross product
     is within 1e-12 x its length; a wall face drawn with a sub-nanometre skew (an export artefact) is then
     "crossed" at a far point instead of being hit at its near end, and the door stays OPENING_CLOSURE_UNRESOLVED.
     door_closures retries ONLY the unresolved doors with the same rule (both rays of exactly one leaf
     hypothesis must land on admitted boundaries within the jamb allowance) and a parallel test on the segment's
     end-to-end deviation from the ray direction (<= eps_n). Closure B follows the frozen rules (topology).

  1. DOUBLE-LEAF DOORS. A double-leaf door is two swing arcs of the same radius whose hinges stand one leaf width
     either side of the meeting point, and whose closed-leaf ends meet there. When the symbol is drawn in a block
     whose layer / name does not carry door vocabulary, role admission files its arcs as FURNITURE and no door
     closure is attempted: the opening stays open and the rooms either side merge.
  2. DOOR IN A WALL GAP. topology.opening_closures needs both rays of one leaf hypothesis to land on admitted walls
     within the jamb allowance; a door hung in a wall gap without drawn jamb returns stays
     OPENING_CLOSURE_UNRESOLVED and the gap stays open.

Release rule (every condition must hold; nothing is released on geometry alone):
  - a wall-gap CANDIDATE: two established wall bands on one axis, same width (30 mm), face lines collinear
    (15 mm), facing free ends (CAPPED / OPENING_JAMB / ALIGNED_FREE_END) separated by a clear gap of 400-3600 mm
    that no arrangement edge crosses;
  - DOOR EVIDENCE inside the gap: a double-leaf motif with both hinges in the gap, or a door whose frozen closure
    state is OPENING_CLOSURE_UNRESOLVED with its hinge in the gap and a leaf no wider than the gap;
  - the door evidence is in exactly one gap and the gap holds exactly one door evidence;
  - no closure already lies on either face line inside the gap (a door the frozen rule CLOSED is never re-closed).

  2b. CLOSURE B FROM THE DOOR'S OWN JAMB FRAMES. When closure A lies on one wall face and the frozen closure-B
     rules fail (no compatible caps), the wall interior strip stays open to the room on the other side and
     connects rooms along the wall. The door symbol's own frame lines are positive evidence of the wall
     thickness: two frame segments of the door occurrence, perpendicular to A, one at each end of A (within
     the frame inset, 60 mm), each running from A's line to the same depth t (50 - 400 mm, equal within eps_r),
     give closure B = A offset by t. Refused when an admitted boundary enters the strip between A and B.
  3. DRAFTING GAP. A boundary end that stops a few millimetres short of another boundary (a drafting near-miss)
     leaves the rooms either side connected through a hairline. The frozen near-miss analysis (role_authority,
     band 50 mm) only reviews these. Owner decision OD-V3-7 authorises a zero-material join for the class
     DRAWING_GAP where positive geometry supports the boundary: a DANGLING end (degree 1 in the arrangement) of an
     admitted, non-closure straight boundary whose nearest admitted boundary lies within (eps_r, 10 mm]; the join
     runs from the end to that nearest point. 10 - 50 mm stays review-only (no join).

A released gap gets two closures, one along each wall face line across the gap (the door sits in the opening
between them; the opening strip becomes its own opening site and neither room absorbs it). Each closure is a
topology boundary only: physical_material NONE, affects_wall_quantity False, affects_finish_quantity False.

Project-agnostic; stdlib only. Lengths in source units, thresholds in mm converted with unit_native_to_mm.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict

from . import topology as T
from . import topology_policy as TP

POLICY_ID = "OPENING_COMPLETION_V1"
ROLE = "OPENING_BOUNDARY"
PREFIX = "CLOSURE|"                 # the closure prefix topology.analyse reads for opening sites and adjacency
NEAR_COLLINEAR_RULE = "NEAR_COLLINEAR_RAY_HIT_V1"
WALL_GAP_RULE = "DOOR_IN_WALL_GAP_V1"
DOUBLE_LEAF_DOOR = "DOUBLE_LEAF_DOOR"
RELEASED, NOT_RELEASED = "RELEASED_ZERO_MATERIAL_CLOSURE", "NOT_RELEASED"
FREE_END_KINDS = ("CAPPED", "OPENING_JAMB", "ALIGNED_FREE_END")
PARAMS_MM = {"leaf_min": 400.0, "leaf_max": 1700.0, "radius_ratio": 0.05, "meet_ratio": 0.10, "sweep_deg": 10.0,
             "gap_min": 400.0, "gap_max": 3600.0, "face_tol": 15.0, "width_tol": 30.0, "interior_margin": 5.0,
             "drafting_gap_max": 10.0}
DRAFTING_GAP_RULE = "DRAFTING_GAP_JOIN_V1"
JAMB_FRAME_B_RULE = "JAMB_FRAME_CLOSURE_B_V1"
JAMB = {"inset_max": 60.0, "depth_min": 50.0, "depth_max": 400.0, "on_line": 5.0}


def _d(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _arc_ends(g):
    cx, cy, r, a0, a1 = g[:5]
    return (cx + r * math.cos(a0), cy + r * math.sin(a0)), (cx + r * math.cos(a1), cy + r * math.sin(a1))


def _sweep(g):
    s = (g[4] - g[3]) % (2 * math.pi)
    return s if s > 0 else 2 * math.pi


def double_leaf_doors(inp, *, unit_native_to_mm=None) -> dict:
    """{occurrence: motif} for every insert occurrence holding exactly one double-leaf pair of swing arcs. The test
    is the drawn motif only (role, layer and block name are not consulted)."""
    u = unit_native_to_mm or inp.unit_native_to_mm or 1.0
    P = {k: v / u for k, v in PARAMS_MM.items() if k not in ("radius_ratio", "meet_ratio", "sweep_deg")}
    arcs = defaultdict(list)
    for p in inp.parts:
        if p.kind == "ARC" and p.identity.instance_handles and p.visibility == "VISIBLE":
            arcs[p.identity.instance_handles[0]].append(p)
    out = {}
    for occ in sorted(arcs):
        ps = sorted(arcs[occ], key=lambda q: q.identity.key or "")
        pairs = []
        for i, a in enumerate(ps):
            for b in ps[i + 1:]:
                ga, gb = a.geometry, b.geometry
                ra, rb = ga[2], gb[2]
                r = (ra + rb) / 2
                if not (P["leaf_min"] <= r <= P["leaf_max"]) or abs(ra - rb) > PARAMS_MM["radius_ratio"] * r:
                    continue
                if any(abs(math.degrees(_sweep(g)) - 90.0) > PARAMS_MM["sweep_deg"] for g in (ga, gb)):
                    continue
                ha, hb = (ga[0], ga[1]), (gb[0], gb[1])
                meet = ((ha[0] + hb[0]) / 2, (ha[1] + hb[1]) / 2)
                if abs(_d(ha, hb) - 2 * r) > 2 * PARAMS_MM["meet_ratio"] * r:
                    continue
                ea = min(_arc_ends(ga), key=lambda e: _d(e, meet))
                eb = min(_arc_ends(gb), key=lambda e: _d(e, meet))
                if _d(ea, meet) > PARAMS_MM["meet_ratio"] * r or _d(eb, meet) > PARAMS_MM["meet_ratio"] * r:
                    continue
                oa = max(_arc_ends(ga), key=lambda e: _d(e, meet))
                pairs.append({"arc_parts": [a.identity.key, b.identity.key], "hinges": [ha, hb], "radius": r,
                              "width": _d(ha, hb), "meet": meet,
                              "open_side": ((oa[0] - ha[0]) / r, (oa[1] - ha[1]) / r)})
        if len(pairs) == 1:
            out[occ] = dict(pairs[0], kind=DOUBLE_LEAF_DOOR, occurrence=occ,
                            rule="two equal swing arcs (90 deg), hinges one leaf either side of the meeting point, "
                                 "closed-leaf ends meet")
    return out


def _ray_hit(o, d, items, eps, max_s):
    """topology._ray_hit with one change: a segment is parallel to the ray when its end-to-end deviation from the
    ray direction is <= eps (not when the cross product is <= 1e-12 x its length). Curves: the frozen routine."""
    hits = []
    curves = []
    for it in items:
        if it.kind != "SEGMENT":
            curves.append(it)
            continue
        a, b = (it.geometry[0], it.geometry[1]), (it.geometry[2], it.geometry[3])
        r = (b[0] - a[0], b[1] - a[1])
        L = math.hypot(*r)
        if L == 0.0:
            continue
        den = d[0] * r[1] - d[1] * r[0]
        ao = (a[0] - o[0], a[1] - o[1])
        if abs(den) <= eps:
            dist = abs(ao[0] * d[1] - ao[1] * d[0])
            if dist > eps:
                continue
            cands = [(ao[0] * d[0] + ao[1] * d[1], a), ((b[0] - o[0]) * d[0] + (b[1] - o[1]) * d[1], b)]
            cands = [c for c in cands if -eps <= c[0] <= max_s]
            if cands:
                sv, pt = min(cands)
                hits.append((sv, 1, pt, it))
            continue
        sv = (ao[0] * r[1] - ao[1] * r[0]) / den
        t = (ao[0] * d[1] - ao[1] * d[0]) / den
        if -eps / L <= t <= 1 + eps / L and -eps <= sv <= max_s:
            hits.append((sv, 0, (o[0] + sv * d[0], o[1] + sv * d[1]), it))
    if curves:
        h = T._ray_hit(o, d, curves, eps, max_s)
        if h is not None:
            hits.append((h[0], 0, h[1], h[2]))
    if not hits:
        return None
    s0 = min(h[0] for h in hits)
    tied = sorted((h for h in hits if h[0] <= s0 + eps), key=lambda h: (h[1], h[0], h[3].source_id))
    sv, _, pt, it = tied[0]
    return sv, pt, it


def door_closures(doors, status, items, eps, jamb_ratio=TP.JAMB_ALLOWANCE_RATIO):
    """Closures for the doors the frozen rule left OPENING_CLOSURE_UNRESOLVED, with the near-collinear ray hit.
    Same hypothesis test and closure-B rules as topology.opening_closures. -> (closures, {occ: state record})."""
    closures, out = [], {}
    for occ in sorted(doors):
        if (status.get(occ) or {}).get("state") != T.OPENING_CLOSURE_UNRESOLVED:
            continue
        sig = doors[occ]
        c, r = sig["hinge"], sig["radius"]
        reach = jamb_ratio * r
        ok = []
        for end in sig["ends"]:
            L = _d(end, c)
            if L == 0:
                continue
            d = ((end[0] - c[0]) / L, (end[1] - c[1]) / L)
            f = _ray_hit(end, d, items, eps, reach)
            b = _ray_hit(c, (-d[0], -d[1]), items, eps, reach)
            if f is not None and b is not None:
                ok.append((end, f, b))
        if len(ok) != 1:
            out[occ] = {"state": T.OPENING_CLOSURE_UNRESOLVED, "rule": NEAR_COLLINEAR_RULE,
                        "why": "no leaf hypothesis lands on admitted boundaries at both ends" if not ok
                        else "both leaf hypotheses land on admitted boundaries"}
            continue
        end, (s1, h1, it1), (s2, h2, it2) = ok[0]
        a_id = f"{PREFIX}{occ}|A"
        closures.append(T.BoundaryItem(a_id, "SEGMENT", (h2[0], h2[1], h1[0], h1[1]), ROLE,
                                       (sig["swing_part"], it1.source_id, it2.source_id)))
        rec = {"state": "CLOSED", "closure_a": a_id, "hits": [it2.source_id, it1.source_id],
               "reach": [round(s2, 9), round(s1, 9)], "width": _d(h1, h2), "closure_b": None,
               "rule": NEAR_COLLINEAR_RULE, "physical_material": "NONE", "affects_wall_quantity": False,
               "affects_finish_quantity": False}
        f1, f2 = T._other_end(it1, h1, eps), T._other_end(it2, h2, eps)
        if f1 is not None and f2 is not None:
            A = (h1[0] - h2[0], h1[1] - h2[1])
            B = (f1[0] - f2[0], f1[1] - f2[1])
            la, lb = math.hypot(*A), math.hypot(*B)
            if la > 0 and lb > 0 and abs(A[0] * B[1] - A[1] * B[0]) <= eps * max(la, lb) and abs(la - lb) <= 2 * eps \
                    and (A[0] * B[0] + A[1] * B[1]) > 0:
                rec["closure_b"], rec["closure_b_rule"] = f"{PREFIX}{occ}|B", T.B_END_POINT
                closures.append(T.BoundaryItem(rec["closure_b"], "SEGMENT", (f2[0], f2[1], f1[0], f1[1]), ROLE,
                                               (sig["swing_part"], it1.source_id, it2.source_id)))
        if rec["closure_b"] is None:
            fb, ev = T._offset_closure_b(h1, h2, it1, it2, items, eps)
            if fb is not None:
                (g2, g1) = fb
                rec["closure_b"], rec["closure_b_rule"], rec["closure_b_evidence"] = f"{PREFIX}{occ}|B", \
                    T.B_OFFSET_JAMB, ev
                closures.append(T.BoundaryItem(rec["closure_b"], "SEGMENT", (g2[0], g2[1], g1[0], g1[1]), ROLE,
                                               (sig["swing_part"], it1.source_id, it2.source_id)))
            else:
                rec["closure_b_blocked"] = ev
        out[occ] = rec
    return closures, out


def drafting_gaps(res, items, *, unit_native_to_mm=1.0):
    """Zero-material joins for dangling admitted boundary ends within (eps_r, drafting_gap_max] of another admitted
    boundary. -> (closures, records)."""
    from . import role_authority as RA
    eps_r = res["tolerances"]["eps_r"]
    band = PARAMS_MM["drafting_gap_max"] / unit_native_to_mm
    arr = res["_arr"]
    deg = defaultdict(list)
    for i, e in enumerate(arr.edges):
        deg[e["n0"]].append(i)
        deg[e["n1"]].append(i)
    prims = [T._Prim(i, it) for i, it in enumerate(items)]
    closures, records = [], []
    for n in sorted(k for k, v in deg.items() if len(v) == 1):
        e = arr.edges[deg[n][0]]
        srcs = sorted(e.get("sources") or ())
        if e.get("kind") != "S" or not srcs or any(x.startswith(("CLOSURE|", "GLAZED|")) for x in srcs):
            continue
        pt = arr.nodes[n]
        best = RA._nearest_on(pt, prims, srcs[0], band)
        if best is None or not (eps_r < best[0] <= band):
            continue
        cid = f"{PREFIX}DRAFTING_GAP|{srcs[0]}|{n}"
        closures.append(T.BoundaryItem(cid, "SEGMENT", (pt[0], pt[1], best[1][0], best[1][1]), ROLE,
                                       (srcs[0], best[2])))
        records.append({"closure_id": cid, "rule": DRAFTING_GAP_RULE, "class": "DRAWING_GAP", "from": srcs[0],
                        "to": best[2], "gap_native": best[0], "end": [round(pt[0], 6), round(pt[1], 6)],
                        "physical_material": "NONE", "affects_wall_quantity": False,
                        "affects_finish_quantity": False, "decision": "OD-V3-7"})
    return closures, records


def jamb_frame_b(a_geom, frame_segs, items, eps_r, unit_native_to_mm=1.0):
    """Closure B geometry from the door's own frame lines, or (None, why)."""
    um = unit_native_to_mm
    p, q = (a_geom[0], a_geom[1]), (a_geom[2], a_geom[3])
    L = _d(p, q)
    if L <= 0:
        return None, "DEGENERATE_A"
    u = ((q[0] - p[0]) / L, (q[1] - p[1]) / L)
    n = (-u[1], u[0])
    on, inset = JAMB["on_line"] / um, JAMB["inset_max"] / um
    cands = []
    for g in frame_segs:
        a, b = (g[0], g[1]), (g[2], g[3])
        lg = _d(a, b)
        if lg <= 0 or abs((b[0] - a[0]) * u[0] + (b[1] - a[1]) * u[1]) > 0.01 * lg:
            continue                                      # not perpendicular to A
        sa = ((a[0] - p[0]) * u[0] + (a[1] - p[1]) * u[1] + (b[0] - p[0]) * u[0] + (b[1] - p[1]) * u[1]) / 2
        oa, ob = [(z[0] - p[0]) * n[0] + (z[1] - p[1]) * n[1] for z in (a, b)]
        if min(abs(oa), abs(ob)) > on:
            continue                                      # does not start on A's line
        t = ob if abs(oa) <= abs(ob) else oa
        if not (JAMB["depth_min"] / um <= abs(t) <= JAMB["depth_max"] / um):
            continue
        cands.append((sa, t))
    starts = [c for c in cands if -on <= c[0] <= inset]
    ends = [c for c in cands if L - inset <= c[0] <= L + on]
    best = None
    for s0, t0 in sorted(starts):
        for s1, t1 in sorted(ends, reverse=True):
            if t0 * t1 > 0 and abs(t0 - t1) <= eps_r:
                best = (t0 + t1) / 2
                break
        if best is not None:
            break
    if best is None:
        return None, "NO_JAMB_FRAME_PAIR"
    t = best
    f1 = (p[0] + t * n[0], p[1] + t * n[1])
    f2 = (q[0] + t * n[0], q[1] + t * n[1])
    for it in items:                                      # an admitted boundary inside the strip refuses B
        if it.kind != "SEGMENT":
            continue
        a, b = (it.geometry[0], it.geometry[1]), (it.geometry[2], it.geometry[3])
        for k in range(1, 8):
            m = (a[0] + (b[0] - a[0]) * k / 8, a[1] + (b[1] - a[1]) * k / 8)
            su = (m[0] - p[0]) * u[0] + (m[1] - p[1]) * u[1]
            sn = ((m[0] - p[0]) * n[0] + (m[1] - p[1]) * n[1]) * (1 if t > 0 else -1)
            if on < su < L - on and on < sn < abs(t) - on:
                return None, "INTERVENING_BOUNDARY"
    return (f1[0], f1[1], f2[0], f2[1]), {"depth": abs(t), "frames": len(cands)}


def _frames(bands, geom_of):
    out = []
    for b in bands:
        if b.get("state") != "WALL_BAND_ESTABLISHED" or len(b.get("faces") or ()) < 2:
            continue
        u = tuple(b["axis"])
        n = (-u[1], u[0])
        offs = []
        for f in b["faces"][:2]:
            g = geom_of.get(f)
            if g is None:
                break
            offs.append(((g[0] + g[2]) / 2) * n[0] + ((g[1] + g[3]) / 2) * n[1])
        if len(offs) == 2:
            out.append({"band": b, "u": u, "n": n, "o": sorted(offs), "w": float(b["width"]),
                        "s": tuple(b["interval"])})
    return out


def wall_gaps(bands, geom_of, edges_xy, *, unit_native_to_mm=1.0) -> list:
    """Wall-gap candidates between collinear established bands with facing free ends; each with the arrangement
    roles that cross its interior (blocked_by) - a clear gap has none."""
    P = {k: v / unit_native_to_mm for k, v in PARAMS_MM.items()}
    F = _frames(bands, geom_of)
    cands = []
    for i, A in enumerate(F):
        for B in F[i + 1:]:
            if abs(A["u"][0] * B["u"][1] - A["u"][1] * B["u"][0]) > 0.005 or abs(A["w"] - B["w"]) > P["width_tol"]:
                continue
            sgn = 1 if A["u"][0] * B["u"][0] + A["u"][1] * B["u"][1] > 0 else -1
            oB = sorted(sgn * x for x in B["o"])
            if abs(A["o"][0] - oB[0]) > P["face_tol"] or abs(A["o"][1] - oB[1]) > P["face_tol"]:
                continue
            sB = B["s"] if sgn == 1 else (-B["s"][1], -B["s"][0])
            endA = {e["outward"]: e for e in A["band"]["ends"]}
            endB = {e["outward"] * sgn: e for e in B["band"]["ends"]}
            for lo, hi, e1, e2 in ((A["s"], sB, endA.get(1), endB.get(-1)), (sB, A["s"], endB.get(1), endA.get(-1))):
                g = hi[0] - lo[1]
                if not (P["gap_min"] <= g <= P["gap_max"]) or e1 is None or e2 is None:
                    continue
                if e1["kind"] not in FREE_END_KINDS or e2["kind"] not in FREE_END_KINDS:
                    continue
                cands.append({"bands": sorted([A["band"]["band_id"], B["band"]["band_id"]]), "s0": lo[1], "s1": hi[0],
                              "u": A["u"], "n": A["n"], "o": A["o"], "width": A["w"], "gap": g,
                              "end_kinds": sorted([e1["kind"], e2["kind"]])})
    m = P["interior_margin"]
    for c in cands:
        u, n = c["u"], c["n"]
        hit = set()
        for (x0, y0, x1, y1, roles) in edges_xy:
            for k in range(9):
                t = k / 8
                x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
                s, o = x * u[0] + y * u[1], x * n[0] + y * n[1]
                if c["s0"] + m < s < c["s1"] - m and c["o"][0] + m < o < c["o"][1] - m:
                    hit |= set(roles)
                    break
        c["blocked_by"] = sorted(hit)
        c["gap_id"] = "GAP-" + hashlib.sha256(json.dumps(
            [c["bands"], round(c["s0"], 3), round(c["s1"], 3)]).encode()).hexdigest()[:16]
    return sorted(cands, key=lambda c: c["gap_id"])


def _in_gap(c, pt, tol):
    s = pt[0] * c["u"][0] + pt[1] * c["u"][1]
    o = pt[0] * c["n"][0] + pt[1] * c["n"][1]
    return c["s0"] - tol <= s <= c["s1"] + tol and c["o"][0] - tol <= o <= c["o"][1] + tol


def _face_segments(c):
    u, n = c["u"], c["n"]
    return [(c["s0"] * u[0] + o * n[0], c["s0"] * u[1] + o * n[1], c["s1"] * u[0] + o * n[0], c["s1"] * u[1] + o * n[1])
            for o in c["o"]]


def _on_face_line(c, seg, tol):
    """True when a closure segment lies along a face line of the gap and overlaps the gap span."""
    u, n = c["u"], c["n"]
    s = sorted((seg[0] * u[0] + seg[1] * u[1], seg[2] * u[0] + seg[3] * u[1]))
    o = (seg[0] * n[0] + seg[1] * n[1], seg[2] * n[0] + seg[3] * n[1])
    if min(s[1], c["s1"]) - max(s[0], c["s0"]) <= tol:
        return False
    return any(abs(o[0] - f) <= tol and abs(o[1] - f) <= tol for f in c["o"])


def derive(res, inp, *, unit_native_to_mm=None) -> dict:
    """Closures, opening states and records for one TS01 result (room_topology_v3 output with wall bands and
    "_items") and its canonical input. Deterministic; reads only. -> {"closures": [BoundaryItem],
    "opening_status": {occ: state}, "doors": {...}, "records": [...], "double_leaf": {...}, "gaps": [...]}"""
    um = unit_native_to_mm or inp.unit_native_to_mm or 1.0
    tol = PARAMS_MM["face_tol"] / um
    eps = res["tolerances"]["eps_n"]
    doors = (res.get("roles") or {}).get("doors") or {}
    status = dict(res.get("openings") or {})
    items = res.get("_items")
    if items is None:
        raise ValueError("opening_completion needs the room_topology_v3 result (admitted items under '_items')")
    d_closures, d_status = door_closures(doors, status, items, eps)
    status.update(d_status)
    frames, occ_of_part = defaultdict(list), {}
    for p in inp.parts:
        if p.identity.instance_handles:
            occ_of_part[p.identity.key] = p.identity.instance_handles[0]
        if p.kind == "SEGMENT" and p.identity.instance_handles and p.visibility == "VISIBLE":
            frames[p.identity.instance_handles[0]].append(tuple(p.geometry))
    a_geom = {c.source_id: c.geometry for c in list(res.get("closures") or ()) + d_closures}
    eps_r = res["tolerances"]["eps_r"]
    for occ in sorted(doors):
        st = status.get(occ) or {}
        if st.get("state") != "CLOSED" or st.get("closure_b") or st.get("closure_a") not in a_geom:
            continue
        ins = occ_of_part.get(doors[occ]["swing_part"])     # the insert that holds the door symbol
        if ins is None:
            continue
        g, ev = jamb_frame_b(a_geom[st["closure_a"]], frames.get(ins, ()), items, eps_r, um)
        if g is None:
            continue
        bid = f"{PREFIX}{occ}|B"
        d_closures.append(T.BoundaryItem(bid, "SEGMENT", g, ROLE, (doors[occ]["swing_part"], st["closure_a"])))
        rec = dict(st, closure_b=bid, closure_b_rule=JAMB_FRAME_B_RULE, closure_b_evidence=ev)
        rec.pop("closure_b_blocked", None)
        d_status[occ] = dict(rec, physical_material="NONE", affects_wall_quantity=False,
                             affects_finish_quantity=False, completed_by=POLICY_ID)
        status[occ] = d_status[occ]
    geom_of = {p.identity.key: tuple(p.geometry) for p in inp.parts if p.kind == "SEGMENT"}
    arr = res["_arr"]
    edges_xy = []
    for e in arr.edges:
        if e.get("kind") != "S":
            continue
        a, b = arr.nodes[e["n0"]], arr.nodes[e["n1"]]
        edges_xy.append((a[0], a[1], b[0], b[1], tuple(sorted(e.get("roles") or ()))))
    edges_xy += [tuple(c.geometry) + ((ROLE,),) for c in d_closures]
    bands = (res.get("wall_bands") or {}).get("bands") or []
    gaps = wall_gaps(bands, geom_of, edges_xy, unit_native_to_mm=um)
    motifs = double_leaf_doors(inp, unit_native_to_mm=um)
    existing = [c.geometry for c in list(res.get("closures") or ()) + d_closures if c.kind == "SEGMENT"]
    evidence = []                                  # (occurrence, kind, points that must lie in the gap, width, extra)
    for occ, m in sorted(motifs.items()):
        if occ in doors:
            continue                               # already a door of the frozen chain: its own rule decides
        evidence.append((occ, DOUBLE_LEAF_DOOR, m["hinges"], m["width"], {"arc_parts": m["arc_parts"],
                                                                         "radius": m["radius"]}))
    for occ, sig in sorted(doors.items()):
        if (status.get(occ) or {}).get("state") == T.OPENING_CLOSURE_UNRESOLVED:
            evidence.append((occ, "SINGLE_LEAF_DOOR_CLOSURE_UNRESOLVED", [sig["hinge"]], sig["radius"],
                             {"swing_part": sig["swing_part"], "radius": sig["radius"]}))
    by_gap, by_ev = defaultdict(list), defaultdict(list)
    for ev in evidence:
        for c in gaps:
            if all(_in_gap(c, p, tol) for p in ev[2]) and ev[3] <= c["gap"] + tol:
                by_gap[c["gap_id"]].append(ev[0])
                by_ev[ev[0]].append(c["gap_id"])
    g_closures, records, g_status = [], [], {}
    for c in gaps:
        evs = by_gap.get(c["gap_id"], [])
        if not evs:
            continue                               # a gap without door evidence is an open passage: never closed
        rec = {"gap_id": c["gap_id"], "bands": c["bands"], "gap_length": c["gap"], "wall_width": c["width"],
               "end_kinds": c["end_kinds"], "blocked_by": c["blocked_by"], "door_evidence": [], "closures": [],
               "rule": WALL_GAP_RULE, "physical_material": "NONE", "affects_topology": True,
               "affects_wall_quantity": False, "affects_finish_quantity": False, "policy": POLICY_ID}
        for ev in evidence:
            if ev[0] in evs:
                rec["door_evidence"].append({"occurrence": ev[0], "kind": ev[1], "leaf_or_width": ev[3], **ev[4]})
        why = None
        if c["blocked_by"]:
            why = "GAP_NOT_CLEAR: arrangement edges cross the gap (" + ", ".join(c["blocked_by"]) + ")"
        elif len(evs) > 1:
            why = "AMBIGUOUS: more than one door evidence in the gap"
        elif len(by_ev[evs[0]]) > 1:
            why = "AMBIGUOUS: the door evidence lies in more than one gap"
        elif any(_on_face_line(c, g, tol) for g in existing):
            why = "ALREADY_CLOSED: a closure already lies on a face line of the gap"
        if why:
            rec.update(state=NOT_RELEASED, why=why)
            records.append(rec)
            continue
        occ = evs[0]
        ids = []
        for k, seg in enumerate(_face_segments(c)):
            cid = f"{PREFIX}{occ}|{'AB'[k]}"
            ids.append(cid)
            g_closures.append(T.BoundaryItem(cid, "SEGMENT", tuple(seg), ROLE, (occ,) + tuple(c["bands"])))
            rec["closures"].append({"closure_id": cid, "geometry": [round(x, 6) for x in seg]})
        rec.update(state=RELEASED, why="door evidence in a clear wall gap between collinear bands with free ends")
        g_status[occ] = {"state": "CLOSED", "closure_a": ids[0], "closure_b": ids[1], "rule": WALL_GAP_RULE,
                         "gap_id": c["gap_id"], "width": c["gap"], "physical_material": "NONE",
                         "affects_wall_quantity": False, "affects_finish_quantity": False}
        records.append(rec)
    j_closures, j_records = drafting_gaps(res, items, unit_native_to_mm=um)
    opening_status = {k: v for k, v in sorted(d_status.items()) if v["state"] == "CLOSED"}
    opening_status.update(g_status)
    return {"closures": d_closures + g_closures + j_closures, "opening_status": dict(sorted(opening_status.items())),
            "doors": d_status, "records": records, "drafting_gaps": j_records, "double_leaf": motifs, "gaps": gaps,
            "policy": policy_record()}

def policy_record() -> dict:
    rec = {"id": POLICY_ID, "parameters_mm": dict(PARAMS_MM), "role": ROLE, "free_end_kinds": list(FREE_END_KINDS),
           "release": ["clear wall gap between collinear established bands with facing free ends",
                       "double-leaf motif or OPENING_CLOSURE_UNRESOLVED door inside the gap",
                       "one door evidence per gap and one gap per door evidence",
                       "no closure already on a face line of the gap"],
           "closure": "two zero-material segments along the wall face lines across the gap",
           "never": ["closing a gap without door evidence", "re-closing a door the frozen rule closed",
                     "generating wall, finish or material quantity from a closure"]}
    rec["digest"] = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()
    return rec
