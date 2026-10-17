"""WATERPROOFING INSTALLATION LAYER (M9 Phase 2B-5, ARCH_TAKEOFF_V2.6 only) - what a membrane cutting plan means on
site. It reads the plan the engine actually cut (membrane_layout's trace: every segment, rip, lane and piece, with
its place) and the area's typed boundary (wp_geometry.ring_segments), and gives:

    piece_plan(trace, area, spec, min_re)   -> the cuttable plan: every roll, every cut along it with its position,
                                               every rip across it and every cross-cut; each piece with an id, size,
                                               source and destination; every offcut as a real rectangle (the floor
                                               material beyond a stepped wall included), classed TRUE_WASTE or
                                               REUSABLE_SUBJECT_TO_N7; the untouched roll stock; the material balance
    run_paths(area, runs, transitions, ...) -> each band run along the boundary: its wall parts, its corners
                                               (INTERNAL / EXTERNAL) and its two ends (a doorway jamb or another break)
    installation(...)                       -> the band pieces placed on their runs - as planned and in the best order
                                               of the same pieces; every joint's distance to the corners and to the
                                               floor-seam ends; the floor seams and where they meet the boundary; the
                                               doorway jamb junctions; corner continuity and the flange at corners;
                                               multi-layer points; penetrations with their clearances; drains;
                                               terminations; the lay order against the falls
    junction(area, spec, c, layout, ...)    -> the FLOOR_WALL_JUNCTION detail: UNRESOLVED unless the project sets it,
                                               with its alternatives - SEPARATE_UPSTAND (the owner's alternative B) at
                                               the plan's flange, the widest flange with the same rolls and the first
                                               that adds one; CONTINUOUS_FOLD (the owner's alternative A; rectangular
                                               rooms, otherwise BLOCKED with the reason)
    install(...)                            -> all of the above for one area, with its flags

Nothing here changes a quantity of the layout or selects a detail: alternatives are shown, open details stay open.
Distances are reported and never judged against a product value that is not given (JOINT_OFFSET_UNVERIFIED). A drain
that is not drawn is NOT_SHOWN, never zero. Project-agnostic; stdlib only."""

from __future__ import annotations

import itertools
import math
from collections import Counter

from engine.source import membrane_layout as ML
from engine.source import plane_poly as PP
from engine.source import wp_geometry as WG

POLICY_ID = "WATERPROOFING_INSTALLATION_V1"
EPS = 1e-6
INTERNAL, EXTERNAL = "INTERNAL", "EXTERNAL"
JUNCTION_STATES = ("UNRESOLVED", "SEPARATE_UPSTAND", "CONTINUOUS_FOLD")
ARRANGEMENT_CAP = 5040            # distinct piece orders searched per run; beyond it the search is limited (flagged)
CLOSED_EVAL_CAP = 200000          # placements evaluated for a closed run (orders x directions x start offsets)
OFFCUT_CLASSES = ("TRUE_WASTE", "REUSABLE_SUBJECT_TO_N7", "RETAINED_BY_N7", "WASTE_BY_N7")
TRIM_NOISE_M2 = 1e-4              # below 1 cm2 outside the wall line a floor piece is not trimmed
DRAIN_KINDS = ("FLOOR_DRAIN", "ROOF_DRAIN")


class InstallError(ValueError):
    pass


def _r(x, n=4):
    return None if x is None else round(x + 0.0, n)


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def _cross(a, b):
    return a[0] * b[1] - a[1] * b[0]


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1]


def _frame(theta, direction):
    """original metres -> the strip frame (a along the strips, c across them), as membrane_layout's floor uses it."""
    def to(p):
        x, y = PP.rotate([p], theta)[0]
        return (y, x) if direction == "ALONG_Y" else (x, y)
    return to


def _in_region(x, y, P, H):
    def inside(ring):
        c = False
        n = len(ring)
        for i in range(n):
            (x0, y0), (x1, y1) = ring[i - 1], ring[i]
            if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
                c = not c
        return c
    return inside(P) and not any(inside(h) for h in H)


# ------------------------------------------------------------------------------------------------- floor pieces
def floor_pieces(trace):
    """the floor pieces of the trace, named by strip (S1, S2 ...; a letter when a strip has several runs of the room,
    .1 .2 when a piece is spliced), with their rectangle in the strip frame."""
    by_strip = {}
    for s in trace["segments"]:
        if s.get("place"):
            by_strip.setdefault(s["place"]["strip"], []).append(s)
    out = []
    for i in sorted(by_strip):
        ss = sorted(by_strip[i], key=lambda s: (s["place"]["interval_m"][0], s["place"]["a0_m"]))
        ivs = sorted({tuple(s["place"]["interval_m"]) for s in ss})
        for s in ss:
            p = s["place"]
            iv = tuple(p["interval_m"])
            same = [t for t in ss if tuple(t["place"]["interval_m"]) == iv]
            pid = f"S{i}" + (chr(ord("a") + ivs.index(iv)) if len(ivs) > 1 else "") + \
                (f".{same.index(s) + 1}" if len(same) > 1 else "")
            out.append({"id": pid, "sid": s["sid"], "strip": i, "a0": p["a0_m"], "a1": p["a0_m"] + s["length_m"],
                        "c0": p["c0_m"], "c1": p["c0_m"] + p["w_m"], "w": p["w_m"], "len": s["length_m"],
                        "interval": iv, "theta": p["theta_rad"], "direction": p["direction"]})
    return out


def _outside(P, H, rect):
    """the parts of the rectangle (a0, c0, a1, c1) outside the region (outer P less holes H) in the strip frame, as
    rectangles (w across, l along): one per cross slab, joined over consecutive slabs with the same along interval.
    Exact when the region's edges inside the rectangle are frame-parallel; None otherwise (a shaped trim)."""
    a0, c0, a1, c1 = rect
    xs = sorted({a0, a1} | {x for ring in [P] + list(H) for x, _ in ring if a0 + EPS < x < a1 - EPS})
    ys = sorted({c0, c1} | {y for ring in [P] + list(H) for _, y in ring if c0 + EPS < y < c1 - EPS})
    inside_area, rows = 0.0, []
    for k in range(len(ys) - 1):
        out, cur = [], None
        for i in range(len(xs) - 1):
            mx, my = (xs[i] + xs[i + 1]) / 2, (ys[k] + ys[k + 1]) / 2
            if _in_region(mx, my, P, H):
                inside_area += (xs[i + 1] - xs[i]) * (ys[k + 1] - ys[k])
                cur = None
            elif cur is not None and abs(cur[1] - xs[i]) <= EPS:
                cur[1] = xs[i + 1]
            else:
                cur = [xs[i], xs[i + 1]]
                out.append(cur)
        rows.append([(ys[k], ys[k + 1], x0, x1) for x0, x1 in out])
    if abs(PP.region_area_in_rect(P, H, rect) - inside_area) > 1e-6:
        return None
    rects = []
    for row in rows:
        for u, v, x0, x1 in row:
            for r in rects:
                if abs(r[1] - u) <= EPS and abs(r[2] - x0) <= EPS and abs(r[3] - x1) <= EPS:
                    r[1] = v
                    break
            else:
                rects.append([u, v, x0, x1])
    return [{"c0": u, "c1": v, "a0": x0, "a1": x1, "w": v - u, "l": x1 - x0} for u, v, x0, x1 in
            sorted(rects, key=lambda r: (r[0], r[2]))]


def offcut_class(w, l, b, end, min_re):
    """TRUE_WASTE: no band lane can come from it (narrower than the band, or no longer than an end lap); otherwise
    REUSABLE_SUBJECT_TO_N7 - or, with a minimum reusable size set (N-7), RETAINED_BY_N7 / WASTE_BY_N7."""
    if w is None or w < b - EPS or l <= end + EPS:
        return "TRUE_WASTE"
    if min_re is None:
        return "REUSABLE_SUBJECT_TO_N7"
    return "RETAINED_BY_N7" if min(w, l) >= min_re - EPS else "WASTE_BY_N7"


# --------------------------------------------------------------------------------------------------- piece plan
def piece_plan(trace, area, spec, min_re=None):
    """the cuttable plan of one area's layout (see module doc). Raises InstallError when the trace does not close."""
    W, L = trace["roll_width_m"], trace["roll_length_m"]
    b, end = trace["band_width_m"], spec["min_end_lap_m"]
    nodes, kids, parent, placed = {}, {}, {}, {}

    def add(nid, w, l, par=None, **kw):
        if nid in nodes:
            raise InstallError(f"duplicate piece id {nid}")
        nodes[nid] = dict(id=nid, w=w, l=l, **kw)
        if par is not None:
            kids.setdefault(par, []).append(nid)
            parent[nid] = par
    by_sid, seg_id = {}, {}
    for s in trace["segments"]:
        nid = f"R{s['roll']}-{s['k']}"
        by_sid[s["sid"]], seg_id[s["sid"]] = s, nid
        add(nid, W, s["length_m"], kind="SEGMENT", roll=s["roll"], at_m=s["at_m"], purpose=s["for"])
    floor = floor_pieces(trace)
    fl_of = {f["sid"]: f for f in floor}
    direct, from_lane, seen = {}, [], Counter()
    for d in trace["doorway_pieces"]:
        seen[d["doorway"]] += 1                                 # a doorway listed twice keeps both pieces, flagged
        rid = f"DW-{d['doorway']}" + (f"#{seen[d['doorway']]}" if seen[d["doorway"]] > 1 else "")
        rec = {"id": rid, "kind": "DOORWAY", "w": d["width_m"], "l": d["length_m"],
               "laid": d["piece_m"][0] * d["piece_m"][1], "to": f"doorway {d['doorway']}", "count": 1, "t": d}
        (direct.setdefault(d["sid"], []) if d["from"] == "SEGMENT" else from_lane).append(rec)
    n_det = 0
    for t in trace["detail_pieces"]:
        n_det += 1
        rec = {"id": f"P{n_det}", "kind": "DETAIL", "w": t["width_m"], "l": t["length_m"],
               "laid": t["count"] * t["width_m"] * t["length_m"], "to": t["what"], "count": t["count"], "t": t}
        (direct.setdefault(t["sid"], []) if t["from"] == "SEGMENT" else from_lane).append(rec)
    lane_ids = {}
    for s in trace["segments"]:
        nid = seg_id[s["sid"]]
        y, parts = 0.0, []
        if s["sid"] in fl_of:
            f = fl_of[s["sid"]]
            parts.append(("FLOOR", f["id"], f["w"], f))
            y += f["w"]
        for rec in direct.get(s["sid"], ()):
            for q in range(rec["count"]):
                pid = rec["id"] if rec["count"] == 1 else f"{rec['id']}.{q + 1}"
                parts.append(("DIRECT", pid, rec["w"], rec))
                y += rec["w"]
        rip = s.get("rip")
        lanes = []
        if rip:
            if abs(rip["y0_m"] - y) > 1e-5:
                raise InstallError(f"{nid}: lanes start at {rip['y0_m']}, the pieces before them end at {y}")
            for q in range(rip["lanes"]):
                lanes.append((f"{nid}/L{q + 1}", rip["y0_m"] + q * b))
            y = rip["y0_m"] + rip["lanes"] * b
        if y > W + 1e-5:
            raise InstallError(f"{nid}: {y} m of pieces across a {W} m roll")
        whole = len(parts) == 1 and not lanes and abs(parts[0][2] - W) <= EPS
        for kind, pid, w, rec in parts:
            if kind == "FLOOR":
                add(pid, w, s["length_m"], None if whole else nid, kind="FLOOR", strip=rec["strip"])
                if whole:
                    kids.setdefault(nid, []).append(pid)
                    parent[pid] = nid
            else:
                add(pid, w, s["length_m"], nid, kind=rec["kind"])
                placed[pid] = (rec["laid"] / rec["count"], rec["to"])
        for lid, ly in lanes:
            add(lid, b, s["length_m"], nid, kind="LANE", y=ly)
            lane_ids[(s["sid"], round(ly, 5))] = lid
        if W - y > EPS and not whole:
            add(f"{nid}~w", W - y, s["length_m"], nid, kind="OFFCUT", why="rip remainder")
        nodes[nid]["cut"] = "WHOLE" if whole else "RIP"
    # pieces cut from lanes, in their order along each lane
    on_lane = {}

    def lane_of(sid, yy):
        lid = lane_ids.get((sid, round(yy, 5)))
        if lid is None:
            raise InstallError(f"no lane of segment {sid} at {yy}")
        return lid
    for p in trace["band_pieces"]:
        on_lane.setdefault(lane_of(p["sid"], p["y_m"]), []).append(
            (p["off_m"], f"B{p['seq']}", b, p["length_m"], "BAND", b * p["length_m"], None))
    for rec in from_lane:
        t = rec["t"]
        on_lane.setdefault(lane_of(t["sid"], t["y_m"]), []).append(
            (t["off_m"], rec["id"], rec["w"], rec["l"], rec["kind"], rec["laid"], rec["to"]))
    for lid, ps in on_lane.items():
        ps.sort()
        pos = 0.0
        for off, pid, w, l, kind, laid, to in ps:
            if abs(off - pos) > 1e-5:
                raise InstallError(f"{lid}: a piece starts at {off}, the lane is cut to {pos}")
            if w < b - EPS:                                      # a narrow piece: cut b wide, then trimmed
                add(pid + "^", b, l, lid, kind="CROSS_CUT")
                add(pid, w, l, pid + "^", kind=kind)
                add(pid + "~t", b - w, l, pid + "^", kind="OFFCUT", why="width trim")
            else:
                add(pid, w, l, lid, kind=kind)
            placed[pid] = (laid, to)
            pos += l
        if nodes[lid]["l"] - pos > EPS:
            add(f"{lid}~l", b, nodes[lid]["l"] - pos, lid, kind="OFFCUT", why="lane remainder")
    for lid in lane_ids.values():
        if lid not in on_lane:
            nodes[lid]["kind"] = "OFFCUT"
            nodes[lid]["why"] = "unused lane"
    # floor pieces: what lies outside the room (a stepped or splayed wall, an obstruction) is an offcut
    poly = [tuple(map(float, q)) for q in area["polygon_m"]]
    holes = [[tuple(map(float, q)) for q in h] for h in area.get("hole_polygons_m") or ()]
    shaped = 0
    for f in floor:
        to = _frame(f["theta"], f["direction"])
        P, H = [to(q) for q in poly], [[to(q) for q in h] for h in holes]
        rect = (f["a0"], f["c0"], f["a1"], f["c1"])
        cov = PP.region_area_in_rect(P, H, rect)
        gap = f["w"] * f["len"] - cov
        outs = _outside(P, H, rect) if gap > 1e-9 else []
        if outs is None and gap <= TRIM_NOISE_M2:               # a wall line drawn a hair off square: no cut
            add(f"{f['id']}.o~", None, None, f["id"], kind="OFFCUT", why="drawing tolerance at the wall line",
                area=gap)
        elif outs is None:
            shaped += 1
            add(f"{f['id']}.o~", None, None, f["id"], kind="OFFCUT", why="trim at a splayed wall (shaped)",
                area=gap)
        else:
            for q, o in enumerate(outs, 1):
                add(f"{f['id']}.o{q}", o["w"], o["l"], f["id"], kind="OFFCUT", why="beyond the wall line",
                    at={"along_m": _r(o["a0"] - f["a0"]), "across_m": _r(o["c0"] - f["c0"])})
        placed[f["id"]] = (cov, f"floor strip {f['strip']}, across {f['c0']:.2f}-{f['c1']:.2f} m, along "
                                f"{f['a0']:.2f}-{f['a1']:.2f} m ({f['direction']})")
    # material balance over the tree
    roll_of = {}
    for nid in nodes:
        n = nid
        while n in parent:
            n = parent[n]
        roll_of[nid] = nodes[n].get("roll")
    leaves = [n for n in nodes if n not in kids]
    offcuts = []
    for n in sorted(leaves):
        if n in placed:
            continue
        nd = nodes[n]
        a = nd["area"] if nd.get("area") is not None else nd["w"] * nd["l"]
        cls = offcut_class(nd["w"], nd["l"], b, end, min_re)
        offcuts.append({"id": n, "w_m": _r(nd["w"]), "l_m": _r(nd["l"]), "area_m2": _r(a, 6), "from": parent.get(n),
                        "roll": roll_of[n], "class": cls, "why": nd.get("why") or nd["kind"].lower(),
                        **({"in_piece_m": nd["at"]} if nd.get("at") else {})})
    consumed = sum(s["length_m"] for s in trace["segments"]) * W
    installed = sum(v[0] for v in placed.values())
    off = sum(o["area_m2"] for o in offcuts)
    if abs(consumed - installed - off) > 1e-5:
        raise InstallError(f"piece plan does not balance: consumed {consumed} vs installed {installed} + offcuts {off}")
    by_roll = {}
    for s in trace["segments"]:
        by_roll.setdefault(s["roll"], []).append(s)
    rolls = []
    for r in sorted(by_roll):
        cut = sum(s["length_m"] for s in by_roll[r])
        rolls.append({"roll": r, "cuts": [{"id": seg_id[s["sid"]], "at_m": _r(s["at_m"]), "length_m": _r(s["length_m"]),
                                           "for": s["for"], "cut": nodes[seg_id[s["sid"]]]["cut"],
                                           "parts": [{"id": k, "w_m": _r(nodes[k]["w"]), "l_m": _r(nodes[k]["l"])}
                                                     for k in kids.get(seg_id[s["sid"]], ())]}
                                          for s in sorted(by_roll[r], key=lambda s: s["at_m"])],
                      "cut_m": _r(cut, 6), "stock_m": _r(L - cut, 6)})
    pieces = []
    for n in nodes:
        if n not in placed:
            continue
        nd = nodes[n]
        pieces.append({"id": n, "kind": nd["kind"], "w_m": _r(nd["w"]), "l_m": _r(nd["l"]), "from": parent.get(n),
                       "roll": roll_of[n], "laid_m2": _r(placed[n][0], 6), "destination": placed[n][1]})
    cuts = []
    for n in nodes:
        if n in kids and nodes[n]["kind"] != "SEGMENT":
            cuts.append({"id": n, "kind": "CROSS_CUT" if nodes[n]["kind"] in ("LANE", "CROSS_CUT") else "TRIM",
                         "into": list(kids[n])})
    tw = sum(o["area_m2"] for o in offcuts if o["class"] in ("TRUE_WASTE", "WASTE_BY_N7"))
    stock = sum(r["stock_m"] for r in rolls) * W
    tree = [{"id": n, "kind": nodes[n]["kind"], "w_m": _r(nodes[n]["w"]), "l_m": _r(nodes[n]["l"]),
             "from": parent.get(n), "roll": roll_of[n]} for n in nodes]
    return {"rolls": rolls, "pieces": pieces, "cross_cuts": cuts, "offcuts": offcuts, "tree": tree,
            "shaped_trims": shaped, "nodes": nodes, "kids": kids, "parent": parent,
            "duplicate_doorways": sorted(k for k, n in seen.items() if n > 1),
            "balance": {"consumed_m2": _r(consumed, 6), "installed_m2": _r(installed, 6), "offcuts_m2": _r(off, 6),
                        "true_waste_m2": _r(tw, 6), "reusable_m2": _r(off - tw, 6), "roll_stock_m2": _r(stock, 6),
                        "rolls": len(rolls), "closes": True,
                        "rule": "consumed = installed + offcuts; roll stock (untouched tails) is not consumed"}}


# ----------------------------------------------------------------------------------------------------- run paths
def _turn(da, db, hole):
    la, lb = math.hypot(*da), math.hypot(*db)
    if la <= EPS or lb <= EPS:
        return None
    c = _cross(da, db) / (la * lb)
    if abs(c) <= WG.ANG_TOL and _dot(da, db) > 0:
        return None
    convex = c > 0
    return INTERNAL if (convex if not hole else not convex) else EXTERNAL


def _ring_runs(segs, elig):
    if not segs:
        return []
    if all(elig(s) for s in segs):
        return [{"closed": True, "parts": list(segs), "start": None, "end": None}]
    k0 = next(i for i, s in enumerate(segs) if not elig(s))
    order = segs[k0 + 1:] + segs[:k0 + 1]
    out, cur, start = [], [], segs[k0]
    for s in order:
        if elig(s):
            cur.append(s)
        else:
            if cur:
                out.append({"closed": False, "parts": cur, "start": start, "end": s})
            cur, start = [], s
    return out


def _brk(s):
    return None if s is None else {"role": s["role"], "id": s["id"]}


def _run_geom(rr, hole, jamb_returns):
    parts = []
    for s in rr["parts"]:
        parts.append({"a": tuple(s["a"]), "b": tuple(s["b"]), "role": s["role"], "id": s["id"], "len": s["length_m"]})
    if not rr["closed"]:
        for where in ("start", "end"):
            br = rr[where]
            if br["role"] == "DOOR" and br["id"] in jamb_returns:
                d = jamb_returns[br["id"]]
                ref = parts[0] if where == "start" else parts[-1]
                u = _sub(ref["b"], ref["a"])
                ln = math.hypot(*u)
                n_out = (u[1] / ln, -u[0] / ln)             # outward: right of a counter-clockwise ring
                p = ref["a"] if where == "start" else ref["b"]
                q = (p[0] + n_out[0] * d, p[1] + n_out[1] * d)
                v = {"a": q, "b": p, "role": "JAMB_RETURN", "id": br["id"], "len": d} if where == "start" else \
                    {"a": p, "b": q, "role": "JAMB_RETURN", "id": br["id"], "len": d}
                parts = [v] + parts if where == "start" else parts + [v]
    r = 0.0
    for p in parts:
        p["r0"], p["r1"] = r, r + p["len"]
        r += p["len"]
    corners = []
    pairs = list(zip(parts, parts[1:])) + ([(parts[-1], parts[0])] if rr["closed"] else [])
    for pa, pb in pairs:
        k = _turn(_sub(pa["b"], pa["a"]), _sub(pb["b"], pb["a"]), hole)
        if k is not None:
            corners.append({"r": pb["r0"] if pb is not parts[0] else 0.0, "kind": k,
                            "at": [_r(pb["a"][0]), _r(pb["a"][1])]})
    return {"length": r, "closed": rr["closed"], "hole": hole, "parts": parts,
            "corners": sorted(corners, key=lambda x: x["r"]), "start": _brk(rr["start"]), "end": _brk(rr["end"])}


def run_paths(area, runs, transitions, topology_applied):
    """the band runs of the layout as paths along the boundary, in the layout's run order. -> (paths, None) or
    (None, reason) when the geometry cannot be matched to the layout's runs."""
    rs = area.get("ring_segments")
    if not rs:
        return None, "RING_SEGMENTS_NOT_KEPT"
    if area["boundary"].get("approximate"):
        return None, "WP_BOUNDARY_SEGMENTATION_REVIEW: the band runs are approximated"
    thr, jr, extra = set(), {}, []
    for x in transitions:
        if x.get("kind") != "DOORWAY":
            continue
        if x.get("selected") == "UPTURN_ACROSS_THRESHOLD":
            if topology_applied:
                thr.add(x["opening_id"])
            else:
                extra.append({"length": x["width_m"], "why": f"threshold upturn {x['opening_id']}"})
        elif x.get("selected") == "JAMB_RETURNS" and x.get("depth_m"):
            if topology_applied:
                jr[x["opening_id"]] = x["depth_m"]
            else:
                extra += [{"length": x["depth_m"], "why": f"jamb return {x['opening_id']}"}] * 2
    out = []
    for ring in rs:
        hole = ring["ring"] == "HOLE"

        def elig(s):
            return s["role"] in WG.ELIGIBLE or (s["role"] == "DOOR" and s["id"] in thr)
        for rr in _ring_runs(ring["segments"], elig):
            out.append(_run_geom(rr, hole, jr))
    for x in extra:
        out.append({"length": x["length"], "closed": False, "hole": False, "parts": [], "corners": [], "start": None,
                    "end": None, "virtual": x["why"]})
    lens = [r["length_m"] for r in runs]
    if len(lens) != len(out) or any(abs(a - p["length"]) > 1e-4 for a, p in zip(lens, out)):
        return None, ("INSTALLATION_GEOMETRY_MISMATCH: the layout's band runs " + ", ".join(f"{x:.3f}" for x in lens)
                      + " do not match the boundary paths " + ", ".join(f"{p['length']:.3f}" for p in out))
    return out, None


# ------------------------------------------------------------------------------------------------------- seams
def floor_seams(floor):
    """the lap zones of the floor membrane in the strip frame: SIDE laps between neighbouring strips (one zone per
    contiguous stretch where the two strips overlap), END laps where a strip is spliced.
    -> [{"kind", "between", "rect": (a0, c0, a1, c1)}]."""
    out = []
    by = {}
    for f in floor:
        by.setdefault(f["strip"], []).append(f)
    ks = sorted(by)
    for i, j in zip(ks, ks[1:]):
        ivs = []
        for p in by[i]:
            for q in by[j]:
                a0, a1 = max(p["a0"], q["a0"]), min(p["a1"], q["a1"])
                if a1 - a0 > EPS and p["c1"] - q["c0"] > EPS:
                    ivs.append((a0, a1, p["c1"], q["c0"]))
        if not ivs:
            continue
        c1, c0 = ivs[0][2], ivs[0][3]                         # strip i ends, strip j starts: the same for all pieces
        for a0, a1 in PP.merge([(a, b) for a, b, _, _ in ivs]):
            out.append({"kind": "SIDE", "between": [f"S{i}", f"S{j}"], "rect": (a0, c0, a1, c1)})
    for i in ks:
        ivs = {}
        for f in by[i]:
            ivs.setdefault(f["interval"], []).append(f)
        for ps in ivs.values():
            ps.sort(key=lambda f: f["a0"])
            for p, q in zip(ps, ps[1:]):
                out.append({"kind": "END", "between": [p["id"], q["id"]], "rect": (q["a0"], p["c0"], p["a1"], p["c1"])})
    return out


def _clip_t(p, q, rect):
    a0, c0, a1, c1 = rect
    t0, t1 = 0.0, 1.0
    dx, dy = q[0] - p[0], q[1] - p[1]
    for pk, qk in ((-dx, p[0] - a0), (dx, a1 - p[0]), (-dy, p[1] - c0), (dy, c1 - p[1])):
        if abs(pk) < 1e-12:
            if qk < -EPS:
                return None
        else:
            t = qk / pk
            if pk < 0:
                t0 = max(t0, t)
            else:
                t1 = min(t1, t)
    return (t0, t1) if t1 - t0 > 1e-9 else None


def seam_ends(area, floor, zones, paths):
    """where each lap zone meets the boundary: on a band run (WALL - under the band flange), in a doorway (under the
    doorway piece's lap) or at another break (at a termination); END where the seam crosses the boundary, ALONG where
    the boundary runs inside the lap zone."""
    if not floor:
        return []
    to = _frame(floor[0]["theta"], floor[0]["direction"])
    where = {}
    for k, rn in enumerate(paths or ()):
        for p in rn["parts"]:
            if p["role"] != "JAMB_RETURN":
                where[(round(p["a"][0], 6), round(p["a"][1], 6), round(p["b"][0], 6), round(p["b"][1], 6))] = (k, p)
    out = []
    for ring in area.get("ring_segments") or ():
        for s in ring["segments"]:
            fa, fb = to(s["a"]), to(s["b"])
            key = (round(s["a"][0], 6), round(s["a"][1], 6), round(s["b"][0], 6), round(s["b"][1], 6))
            for zi, z in enumerate(zones):
                t = _clip_t(fa, fb, z["rect"])
                if t is None:
                    continue
                ln = (t[1] - t[0]) * s["length_m"]
                width = (z["rect"][3] - z["rect"][1]) if z["kind"] == "SIDE" else (z["rect"][2] - z["rect"][0])
                d = _sub(fb, fa)
                along = abs(d[1]) <= 1e-9 if z["kind"] == "SIDE" else abs(d[0]) <= 1e-9
                rec = {"zone": zi, "seam": z["kind"], "between": z["between"], "kind": None, "shape":
                       "ALONG" if along and ln > width + EPS else "END", "length_m": _r(ln)}
                if key in where:
                    k, p = where[key]
                    rec.update(kind="WALL", run=k, r=[_r(p["r0"] + t[0] * p["len"]), _r(p["r0"] + t[1] * p["len"])])
                elif s["role"] == "DOOR":
                    rec.update(kind="DOORWAY", door=s["id"])
                else:
                    rec.update(kind="BREAK", role=s["role"], id=s["id"])
                out.append(rec)
    return out


# ---------------------------------------------------------------------------------------------- joints and corners
def _dpt(a, b, x, R):
    if R is None:
        return max(0.0, a - x, x - b)
    return min(max(0.0, a - (x + k * R), (x + k * R) - b) for k in (-1, 0, 1))


def _gap(a, b, u, v, R):
    if R is None:
        return max(0.0, u - b, a - v), min(b, v) - max(a, u)
    best = None
    for k in (-1, 0, 1):
        g, o = max(0.0, u + k * R - b, a - v - k * R), min(b, v + k * R) - max(a, u + k * R)
        if best is None or (g, -o) < (best[0], -best[1]):
            best = (g, o)
    return best


def _layout_run(R, closed, lens, end, reverse=False, offset=0.0):
    """pieces of the given lengths laid in order from the run start (closed: every piece laps the one before, the
    first over the last). -> positions [(start, end)], joint zones [(from, to)]."""
    pos, s = [], 0.0
    for k, ln in enumerate(lens):
        lap = end if (closed or k) else 0.0
        pos.append((s - lap, s - lap + ln))
        s += ln - lap
    if abs(s - R) > 1e-5:
        raise InstallError(f"pieces cover {s} m of a {R} m run")
    joints = [(a, a + (end if (closed or k) else 0.0)) for k, (a, _) in enumerate(pos) if (closed or k)]
    if reverse:
        pos = [(R - b, R - a) for a, b in pos]
        joints = [(R - b, R - a) for a, b in joints]
    if offset:
        pos = [(a + offset, b + offset) for a, b in pos]
        joints = [(a + offset, b + offset) for a, b in joints]
    return pos, joints


def _metrics(R, closed, joints, corners, seams):
    RR = R if closed else None
    cd = [min(_dpt(a, b, c, RR) for c in corners) for a, b in joints] if corners else []
    sd, stack, touch = [], 0, 0
    for a, b in joints:
        best = None
        for u, v in seams:
            g, o = _gap(a, b, u, v, RR)
            if o > EPS:
                stack += 1
            elif abs(o) <= EPS:
                touch += 1
            best = g if best is None else min(best, g)
        if best is not None:
            sd.append(best)
    return {"corner": min(cd) if cd else None, "seam_end": min(sd) if sd else None, "corner_each": cd,
            "seam_end_each": sd, "stacked": stack, "touching": touch}


def _key(m):
    c = m["corner"] if m["corner"] is not None else 1e9
    s = m["seam_end"] if m["seam_end"] is not None else 1e9
    return (round(min(c, s), 6), round(c, 6), round(s, 6))


def _n_perms(lens):
    n = math.factorial(len(lens))
    for v in Counter(lens).values():
        n //= math.factorial(v)
    return n


def best_arrangement(R, closed, pieces, end, corners, seams):
    """the order and laying direction (and, for a closed run, the start) of the same pieces that keeps the joints
    farthest from the corners and the floor-seam ends: the smaller of the two distances first, then the corner
    distance, then the seam-end distance. -> {"order", "reversed", "offset_m", metrics, "searched", "limited"}."""
    lens = [round(p[1], 6) for p in pieces]
    ids = {}
    for pid, ln, _ in pieces:
        ids.setdefault(round(ln, 6), []).append(pid)
    limited = _n_perms(lens) > ARRANGEMENT_CAP
    if limited:
        perms = [tuple(lens), tuple(reversed(lens))]
    elif closed:
        first = sorted(lens)[0]
        rest = list(lens)
        rest.remove(first)
        perms = sorted({(first,) + p for p in itertools.permutations(rest)})
    else:
        perms = sorted(set(itertools.permutations(lens)))
    offs = [0.0]
    if closed:
        n = int(round(R / 0.01))                                 # 10 mm steps, coarser only beyond the cap
        while len(perms) * 2 * n > CLOSED_EVAL_CAP and n > 8:
            n //= 2
            limited = True
        offs = [R * k / n for k in range(n)]
    best, searched = None, 0
    for perm in perms:
        for rev in (False, True):
            for off in offs:
                _, joints = _layout_run(R, closed, perm, end, rev, off)
                m = _metrics(R, closed, joints, corners, seams)
                searched += 1
                k = _key(m)
                if best is None or k > best[0]:
                    best = (k, perm, rev, off, m)
    _, perm, rev, off, m = best
    pool = {k: list(v) for k, v in ids.items()}
    order = [pool[ln].pop(0) for ln in perm]
    return {"order": order, "reversed": rev, "offset_m": _r(off), "min_corner_m": _r(m["corner"]),
            "min_seam_end_m": _r(m["seam_end"]), "stacked_on_seam_ends": m["stacked"], "searched": searched,
            "limited": limited}


def place_band(paths, band_pieces, end):
    """the trace's band pieces on their runs, in the order the engine cut them (each run from its start; a closed
    run from the start of its first part). -> per run [(piece id, length, lap, start, end)]."""
    out, k = [], 0
    for rn in paths:
        need, s, row = rn["length"], 0.0, []
        while need > 1e-6:
            if k >= len(band_pieces):
                raise InstallError("the band pieces do not cover the runs")
            p = band_pieces[k]
            cover = p["length_m"] - p["lap_m"]
            row.append((f"B{p['seq']}", p["length_m"], p["lap_m"], s - p["lap_m"], s + cover))
            s += cover
            need -= cover
            k += 1
        if abs(need) > 1e-5:
            raise InstallError("a band piece runs past the end of its run")
        out.append(row)
    if k != len(band_pieces):
        raise InstallError("band pieces left over after the runs are covered")
    return out


# ------------------------------------------------------------------------------------------------ penetrations
def _linf_seg(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    x0, y0 = p[0] - a[0], p[1] - a[1]
    ts = {0.0, 1.0}
    for den, num in ((dx - dy, x0 - y0), (dx + dy, x0 + y0), (dx, x0), (dy, y0)):
        if abs(den) > 1e-12:
            ts.add(min(1.0, max(0.0, num / den)))
    return min(max(abs(x0 - t * dx), abs(y0 - t * dy)) for t in ts)


def _linf_poly(p, poly):
    if _in_region(p[0], p[1], poly, ()):
        return 0.0
    return min(_linf_seg(p, poly[i - 1], poly[i]) for i in range(len(poly)))


def _flange_zone(part, j, hole):
    a, b = part["a"], part["b"]
    u = _sub(b, a)
    ln = math.hypot(*u)
    n = (-u[1] / ln, u[0] / ln) if not hole else (u[1] / ln, -u[0] / ln)   # into the room
    return [a, b, (b[0] + n[0] * j, b[1] + n[1] * j), (a[0] + n[0] * j, a[1] + n[1] * j)]


def penetration_clearances(items, floor, zones, paths, j):
    """per drawn penetration: the clear distance (in the strip frame, square measure) to every floor lap zone and
    every band flange; the largest centred square collar that clears them is twice the smallest."""
    if not floor:
        return []
    to = _frame(floor[0]["theta"], floor[0]["direction"])
    flanges = []
    for rn in paths or ():
        for p in rn["parts"]:
            if p["role"] in WG.ELIGIBLE:
                flanges.append([to(q) for q in _flange_zone(p, j, rn["hole"])])
    out = []
    for it in items:
        q = to(tuple(it["at_m"]))
        ds = [(max(z["rect"][0] - q[0], q[0] - z["rect"][2], z["rect"][1] - q[1], q[1] - z["rect"][3], 0.0),
               "floor seam") for z in zones]
        ds += [(_linf_poly(q, f), "band flange") for f in flanges]
        if not ds:
            continue
        ds.sort()
        out.append({"ref": it.get("ref"), "kind": it["kind"], "at_m": it["at_m"], "nearest": ds[0][1],
                    "clear_m": _r(ds[0][0]), "max_centred_square_m": _r(2 * ds[0][0]),
                    "clearances_m": {w: _r(min(d for d, ww in ds if ww == w)) for w in sorted({w for _, w in ds})}})
    return out


# ------------------------------------------------------------------------------------------------ installation
def installation(area, spec, c, lay, plan, transitions, topology_applied, min_joint_offset_m=None):
    """the installation geometry of one area (see module doc)."""
    tr = lay["trace"]
    end, j = spec["min_end_lap_m"], tr["junction_flange_m"]
    flags, notes = [], []
    floor = floor_pieces(tr)
    zones = floor_seams(floor)
    paths, why = run_paths(area, c["runs"], transitions, topology_applied)
    out = {"state": "COMPUTED", "junction_flange_m": j, "floor_seams": [
        {"kind": z["kind"], "between": z["between"], "rect_frame_m": [_r(x) for x in z["rect"]]} for z in zones]}
    if paths is None:
        out.update(state="GEOMETRY_NOT_ESTABLISHED", reason=why)
        flags.append(why.split(":")[0])
        out["flags"] = flags
        return out
    ends = seam_ends(area, floor, zones, paths)
    rows = place_band(paths, tr["band_pieces"], end) if paths else []
    runs, n_int, n_ext = [], 0, 0
    joints_total = 0
    for k, (rn, row) in enumerate(zip(paths, rows)):
        R, closed = rn["length"], rn["closed"]
        seam_r = [tuple(x["r"]) for x in ends if x["kind"] == "WALL" and x["run"] == k]
        cpos = [x["r"] for x in rn["corners"]]
        joints = [(a, a + lap) for _, _, lap, a, _ in row if lap > EPS]
        joints_total += len(joints)
        m = _metrics(R, closed, joints, cpos, seam_r)
        jrows = []
        for q, (a, b) in enumerate(joints):
            f = []
            if m["corner_each"] and m["corner_each"][q] <= EPS:
                f.append("JOINT_AT_CORNER")
            if seam_r:
                g = [_gap(a, b, u, v, R if closed else None) for u, v in seam_r]
                if any(o > EPS for _, o in g):
                    f.append("JOINT_ON_SEAM_END")
                elif any(abs(o) <= EPS for _, o in g):
                    f.append("JOINT_TOUCHES_SEAM_END")
            if min_joint_offset_m is not None:
                lo = min(x for x in (m["corner_each"][q] if m["corner_each"] else None,
                                     m["seam_end_each"][q] if m["seam_end_each"] else None) if x is not None) \
                    if (m["corner_each"] or m["seam_end_each"]) else None
                if lo is not None and lo < min_joint_offset_m - EPS:
                    f.append("JOINT_OFFSET_BELOW_MINIMUM")
            if closed and a < -EPS:                              # the closing joint, shown at the run's end
                a, b = a + R, b + R
            jrows.append({"from_m": _r(a), "to_m": _r(b),
                          "corner_m": _r(m["corner_each"][q]) if m["corner_each"] else None,
                          "seam_end_m": _r(m["seam_end_each"][q]) if m["seam_end_each"] else None, "flags": f})
            flags += f
        crow = []
        for cr in rn["corners"]:
            x = cr["r"]
            inside = [pid for pid, _, _, a, b in row if a + EPS < x < b - EPS or (closed and a < 0 and
                                                                                  a + R + EPS < x)]
            edge = [pid for pid, _, _, a, b in row if abs(a - x) <= EPS or abs(b - x) <= EPS or
                    (closed and (abs(a + R - x) <= EPS or abs(b - R - x) <= EPS))]
            n_int += cr["kind"] == INTERNAL
            n_ext += cr["kind"] == EXTERNAL
            crow.append({"r_m": _r(x), "kind": cr["kind"], "at_m": cr["at"], "continuous_in": inside,
                         "piece_edge_at_corner": edge,
                         "flange": ("PLEAT %.2f x %.2f m inside the band material" % (j, j)) if cr["kind"] == INTERNAL
                         else ("GAP %.2f x %.2f m in the flange (no material)" % (j, j))})
            if edge and not inside:
                flags.append("BAND_PIECE_EDGE_AT_CORNER")
        best = best_arrangement(R, closed, [(pid, ln, lap) for pid, ln, lap, _, _ in row], end, cpos, seam_r) \
            if len(row) > 1 or closed else None
        if best and best["limited"]:
            flags.append("ARRANGEMENT_SEARCH_LIMITED")
        jambs = []
        for wh in ("start", "end"):
            br = rn.get(wh)
            if br is None:
                continue
            if br["role"] == "DOOR":
                jr = any(p["role"] == "JAMB_RETURN" for p in rn["parts"])
                jambs.append({"door": br["id"], "at": f"run {wh}", "state": "RETURN_ON_JAMB" if jr else
                              "BUTT_JOINT_OPEN", "detail": "the doorway detail (N-1): the doorway piece meets the band "
                                                           "end edge to edge; the jamb reveal is not covered"
                              if not jr else "the band returns onto the jamb reveal"})
            else:
                jambs.append({"break": br["role"], "id": br["id"], "at": f"run {wh}", "state": "TERMINATION_OPEN"})
        runs.append({"run": k + 1, "length_m": _r(R), "closed": closed, "virtual": rn.get("virtual"),
                     "from": rn.get("start"), "to": rn.get("end"),
                     "parts": [{"role": p["role"], "id": p["id"], "from_m": _r(p["r0"]), "to_m": _r(p["r1"]),
                                "a": [_r(p["a"][0]), _r(p["a"][1])], "b": [_r(p["b"][0]), _r(p["b"][1])]}
                               for p in rn["parts"]],
                     "pieces": [{"id": pid, "length_m": _r(ln), "lap_m": _r(lap), "from_m": _r(a), "to_m": _r(b)}
                                for pid, ln, lap, a, b in row],
                     "joints": jrows, "min_joint_corner_m": _r(m["corner"]), "min_joint_seam_end_m": _r(m["seam_end"]),
                     "joints_stacked_on_seam_ends": m["stacked"], "joints_touching_seam_ends": m["touching"],
                     "corners": crow, "best_arrangement": best, "ends": jambs})
    t_points = Counter(x["kind"] for x in ends if x["shape"] == "END")
    along = [x for x in ends if x["shape"] == "ALONG"]
    if along:
        flags.append("FLOOR_SEAM_ALONG_A_WALL")
    crossings, stagger = 0, []
    ends_z = [z for z in zones if z["kind"] == "END"]
    for z in ends_z:
        for w in zones:
            if w["kind"] == "SIDE":
                a0, c0, a1, c1 = z["rect"]
                b0, d0, b1, d1 = w["rect"]
                if min(a1, b1) - max(a0, b0) > EPS and min(c1, d1) - max(c0, d0) > EPS:
                    crossings += 1
    strip_of = {f["id"]: f["strip"] for f in floor}
    for z in ends_z:
        for w in ends_z:
            si, sj = strip_of[z["between"][0]], strip_of[w["between"][0]]
            if sj == si + 1:
                g = max(0.0, w["rect"][0] - z["rect"][2], z["rect"][0] - w["rect"][2])
                stagger.append({"strips": [si, sj], "stagger_m": _r(g)})
    if any(x["stagger_m"] <= EPS for x in stagger):
        flags.append("END_LAPS_NOT_STAGGERED")
    pen = area["penetrations"]
    items = pen.get("items") or []
    drains = [x for x in items if x["kind"] in DRAIN_KINDS]
    clear = penetration_clearances(items, floor, zones, paths, j)
    lay_order = _lay_order(floor, zones, drains)
    if pen["state"] == "NOT_SHOWN":
        flags.append("DRAIN_NOT_SHOWN")
    elif not drains:
        flags.append("NO_DRAIN_DRAWN")
    if lay_order["state"] != "FROM_THE_DRAIN":
        flags.append("LAY_ORDER_NOT_VALIDATED")
    if lay_order.get("drain_on_seam"):
        flags.append("DRAIN_ON_A_FLOOR_SEAM")
    if min_joint_offset_m is None and joints_total:
        flags.append("JOINT_OFFSET_UNVERIFIED")
    out.update(runs=runs, seam_ends=[dict(x) for x in ends],
               corners={"internal": n_int, "external": n_ext,
                        "flange_pleats_m2": _r(n_int * j * j, 6), "flange_gaps_m2": _r(n_ext * j * j, 6)},
               multi_layer_points={"flange_over_seam_end": t_points.get("WALL", 0),
                                   "doorway_lap_over_seam_end": t_points.get("DOORWAY", 0),
                                   "seam_end_at_termination": t_points.get("BREAK", 0),
                                   "band_joint_over_seam_end": sum(r["joints_stacked_on_seam_ends"] for r in runs),
                                   "floor_end_lap_over_side_lap": crossings, "seams_along_walls": len(along)},
               end_lap_stagger=stagger,
               band_joints=joints_total,
               jamb_junctions=sum(1 for r in runs for e in r["ends"] if e.get("door")),
               terminations=[e for r in runs for e in r["ends"] if e.get("break")],
               penetrations={"state": pen["state"], "count": pen["count"], "items": clear,
                             "drains": {"state": "COUNTED_FROM_DRAWING" if drains else "NOT_SHOWN",
                                        "count": len(drains) if drains else None}},
               lay_order=lay_order, falls={"state": "NOT_SHOWN", "note": "the plan gives no falls; the lap shingling "
                                                                         "is checked only against a drawn drain"})
    out["flags"] = sorted(set(flags))
    return out


def _lay_order(floor, zones, drains):
    """the order to lay the floor strips so that every side lap sheds water towards the drain: the strip with the
    drain first, then outwards (the sheet farther from the drain on top). Without a drawn drain it is not validated."""
    strips = sorted({f["strip"] for f in floor})
    if not drains or not floor:
        return {"state": "NOT_VALIDATED", "order": strips, "why": "no drain drawn: the falls are not known"}
    to = _frame(floor[0]["theta"], floor[0]["direction"])
    on_seam = []
    for d in drains:
        q = to(tuple(d["at_m"]))
        if any(z["rect"][0] - EPS <= q[0] <= z["rect"][2] + EPS and z["rect"][1] - EPS <= q[1] <= z["rect"][3] + EPS
               for z in zones):
            on_seam.append(d.get("ref"))
    if len(drains) > 1:
        return {"state": "NOT_VALIDATED", "order": strips, "drain_on_seam": on_seam,
                "why": f"{len(drains)} drains: the catchments (falls) are not drawn, so no lay order is derived"}
    cd = to(tuple(drains[0]["at_m"]))[1]
    span = {}
    for f in floor:
        lo, hi = span.get(f["strip"], (f["c0"], f["c1"]))
        span[f["strip"]] = (min(lo, f["c0"]), max(hi, f["c1"]))
    mid = {s: (span[s][0] + span[s][1]) / 2 for s in strips}
    order = sorted(strips, key=lambda s: (abs(mid[s] - cd), s))
    return {"state": "FROM_THE_DRAIN", "order": order, "drain": drains[0].get("ref"), "drain_on_seam": on_seam,
            "rule": "each side lap: the strip farther from the drain laps over the nearer one"}


# ------------------------------------------------------------------------------------------- junction alternatives
def _is_rect(area):
    segs = (area.get("ring_segments") or [{}])[0].get("segments") or []
    if len(area.get("ring_segments") or ()) != 1:
        return None, "an obstruction ring (column / shaft) inside the area"
    poly = [tuple(map(float, q)) for q in area["polygon_m"]]
    if len(poly) != 4 or PP.frame_angle(poly) != 0.0:
        return None, "not an axis-parallel rectangle"
    xs, ys = sorted({round(p[0], 6) for p in poly}), sorted({round(p[1], 6) for p in poly})
    if len(xs) != 2 or len(ys) != 2:
        return None, "not an axis-parallel rectangle"
    if any(s["role"] not in WG.ELIGIBLE + ("DOOR",) for s in segs):
        return None, "a break other than a doorway (open edge, passage, glazing): the fold has no wall to rise on"
    return (xs[1] - xs[0], ys[1] - ys[0]), None


def continuous_fold(area, spec, h):
    """method B for a rectangular room: the strips cover the developed surface (floor + every upturn folded out flat
    + every doorway floor, whose depth must equal the upturn height), no band and no junction lap; each internal
    corner leaves an h x h square of excess sheet; each door needs two jamb slits h deep. -> the plan of the better
    strip direction (fewest rolls, fewest seams, least membrane) or {"state": "BLOCKED", "reason"}."""
    sides, why = _is_rect(area)
    if sides is None:
        return {"state": "BLOCKED", "reason": f"CONTINUOUS_FOLD_NOT_COMPUTED: {why}"}
    for d in area["continuation_pieces"]:
        if d.get("depth_m") is None or abs(d["depth_m"] - h) > EPS:
            return {"state": "BLOCKED", "reason": "CONTINUOUS_FOLD_NOT_COMPUTED: a doorway depth is not the upturn "
                                                  "height (the fold-down flap would need its own piece)"}
    W, L = spec["roll_width_m"], spec["roll_length_m"]
    side, end = spec["min_side_lap_m"], spec["min_end_lap_m"]
    X, Y = sides
    DX, DY = X + 2 * h, Y + 2 * h
    req = X * Y + 2 * (X + Y) * h
    corners = [(0.0, 0.0, h, h), (DX - h, 0.0, DX, h), (DX - h, DY - h, DX, DY), (0.0, DY - h, h, DY)]
    opts = []
    for direction in ("ALONG_X", "ALONG_Y"):
        Ls, Dc = (DX, DY) if direction == "ALONG_X" else (DY, DX)
        n = 1 if Dc <= W + EPS else math.ceil((Dc - W) / (W - side) - EPS) + 1
        w_last = Dc - (n - 1) * (W - side)
        k = 1 if Ls <= L + EPS else math.ceil((Ls - L) / (L - end) - EPS) + 1
        lens = [L] * (k - 1) + [Ls - (k - 1) * (L - end)] if k > 1 else [Ls]
        rects, cuts = [], []
        for i in range(n):
            c0 = i * (W - side)
            w = W if i < n - 1 else w_last
            a = 0.0
            for q, ln in enumerate(lens):
                a0 = a if q == 0 else a - end
                rects.append((a0, c0, a0 + ln, c0 + w))
                cuts.append(ln)
                a = a0 + ln
        bins, packing = ML.pack_rolls(cuts, L)
        cons = sum(cuts) * W
        inst = sum((r[2] - r[0]) * (r[3] - r[1]) for r in rects)

        def ov(r, s):
            return max(0.0, min(r[2], s[2]) - max(r[0], s[0])) * max(0.0, min(r[3], s[3]) - max(r[1], s[1]))
        # the corner squares in the strip frame (a along, c across): (x, y) for ALONG_X, (y, x) for ALONG_Y
        cf = corners if direction == "ALONG_X" else [(cq[1], cq[0], cq[3], cq[2]) for cq in corners]
        corner_ex = sum(ov(r, cq) for r in rects for cq in cf)
        seams = (n - 1) + n * (k - 1)
        opts.append({"direction": direction, "strips": n, "last_strip_width_m": _r(w_last), "strip_length_m": _r(Ls),
                     "pieces_per_strip": k, "rolls": len(bins), "consumed_m2": _r(cons, 6),
                     "installed_m2": _r(inst, 6), "required_m2": _r(req, 6), "corner_excess_m2": _r(corner_ex, 6),
                     "laps_m2": _r(inst - req - corner_ex, 6), "trim_m2": _r(cons - inst, 6), "seams": seams,
                     "floor_seams": n - 1, "end_laps": n * (k - 1), "packing": packing})
    sel = min(opts, key=lambda o: (o["rolls"], o["seams"], o["consumed_m2"], ("ALONG_X", "ALONG_Y").index(
        o["direction"])))
    n_doors = len(area["continuation_pieces"])
    return dict(sel, state="COMPUTED", method="CONTINUOUS_FOLD", developed_m=[_r(DX), _r(DY)],
                corner_squares=4, jamb_slits=2 * n_doors, slit_length_m=_r(h),
                alternatives=[{k_: o[k_] for k_ in ("direction", "rolls", "seams", "consumed_m2")} for o in opts],
                conditions=["the sheet may be folded 90 degrees at the junction and pleated at the corners (P-2)",
                            "every doorway floor is the upturn flap laid flat (depth = upturn height)",
                            "the corner squares and jamb slits need the product's corner / slit detail (P-4)"])


def _summ(res):
    return {"rolls": res["units"]["consumed_units"], "consumed_m2": res["consumed_m2"],
            "installed_m2": round(res["placed_m2"] + res["overlap_m2"], 6),
            "seams": sum((res["layout"]["seams"].get(k) or {}).get("count") or 0
                         for k in ("longitudinal", "transverse_floor", "upturn_end_laps")),
            "direction": res["layout"]["direction"]}


def junction(area, spec, c, layout, relayout, project_junction=None):
    """FLOOR_WALL_JUNCTION (N-11 / P-1): the state and the alternatives. A at the plan's flange is the V2.5 figure;
    the flange sweep (1 cm steps up to the upturn height, a sensitivity range, not a standard) finds the widest flange
    with the same roll count and the first that adds a roll; B is the continuous fold."""
    h = c["upturn_h_m"]
    j0 = layout["layout"]["trace"]["junction_flange_m"]
    base = _summ(layout)
    alts = [dict(base, method="SEPARATE_UPSTAND", flange_m=_r(j0), basis="the plan (flange = the side lap of "
                                                                        "UP-WP-002, as V2.5 assumes)")]
    sweep, same, more = [], None, None
    jj = round(j0 + 0.01, 4)
    while jj <= h + EPS:
        r = relayout(jj)
        if r["state"] == "BLOCKED":
            break
        s = _summ(r)
        sweep.append({"flange_m": _r(jj), "rolls": s["rolls"], "consumed_m2": s["consumed_m2"]})
        if s["rolls"] == base["rolls"]:
            same = dict(s, flange_m=_r(jj), trace=r["layout"].get("trace"))
        elif s["rolls"] > base["rolls"]:
            more = dict(s, flange_m=_r(jj), trace=r["layout"].get("trace"))
            break
        jj = round(jj + 0.01, 4)
    if same:
        alts.append(dict(same, method="SEPARATE_UPSTAND", basis="the widest flange (1 cm steps) with the plan's "
                                                                "roll count"))
    if more:
        alts.append(dict(more, method="SEPARATE_UPSTAND", basis="the first flange that adds a roll"))
    fold = continuous_fold(area, spec, h)
    if fold["state"] == "COMPUTED":
        alts.append({"method": "CONTINUOUS_FOLD", "rolls": fold["rolls"], "consumed_m2": fold["consumed_m2"],
                     "installed_m2": fold["installed_m2"], "seams": fold["seams"], "direction": fold["direction"],
                     "basis": "the developed surface, no band"})
    state = project_junction or "UNRESOLVED"
    rolls = [a["rolls"] for a in alts]
    return {"state": state, "decision": "N-11 (owner) / P-1 (product data sheet)",
            "flange_in_plan_m": _r(j0), "alternatives": alts, "flange_sweep": sweep,
            "sweep_range_m": [_r(j0 + 0.01), _r(h)], "continuous_fold": fold,
            "rolls_range": [min(rolls), max(rolls)], "changes_roll_count": len(set(rolls)) > 1,
            "note": "flanges other than the plan's are sensitivities, never standards; the junction stays open until "
                    "the membrane system's data sheet or the owner (N-11) sets it"}


# ------------------------------------------------------------------------------------------------------- install
def install(area, spec, c, layout, *, relayout, transitions, topology_applied, min_joint_offset_m=None,
            project_junction=None):
    """the installation layer of one area: the piece plan, the installation geometry, the junction alternatives,
    the flags and the material state it leaves."""
    lay = layout.get("layout") or {}
    tr = lay.get("trace")
    if layout["state"] == "BLOCKED" or tr is None:
        return {"state": "BLOCKED", "reason": layout.get("blocked_by") or "NO_TRACE"}
    if (area.get("net_m2") or 0.0) <= EPS:
        return {"state": "BLOCKED", "reason": "DEGENERATE_AREA: the area has no floor (a ring without area)"}
    try:
        plan = piece_plan(tr, area, spec, c.get("min_reusable_m"))
        inst = installation(area, spec, c, lay, plan, transitions, topology_applied, min_joint_offset_m)
    except InstallError as ex:                                  # never a silent plan: the run continues, flagged
        return {"state": "INCONSISTENT", "reason": f"INSTALLATION_PLAN_INCONSISTENT: {ex}",
                "flags": ["INSTALLATION_PLAN_INCONSISTENT"]}
    dest = {}
    for rn in inst.get("runs") or ():
        for p in rn["pieces"]:
            dest[p["id"]] = f"band run {rn['run']} at {p['from_m']:.2f}-{p['to_m']:.2f} m"
    for p in plan["pieces"]:
        if p["id"] in dest:
            p["destination"] = dest[p["id"]]
        elif p["kind"] == "BAND" and p["destination"] is None:
            p["destination"] = "band (placement not established)"
    jun = junction(area, spec, c, layout, relayout, project_junction)
    flags = list(inst.get("flags") or ())
    if jun["state"] == "UNRESOLVED":
        flags.append("FLOOR_WALL_JUNCTION_UNRESOLVED")
    if jun["changes_roll_count"]:
        flags.append("JUNCTION_CHANGES_ROLL_COUNT")
    if plan["shaped_trims"]:
        flags.append("SHAPED_TRIM_NOT_DECOMPOSED")
    if plan["duplicate_doorways"]:
        flags.append("DUPLICATE_DOORWAY_PIECE")
    for k in ("nodes", "kids", "parent"):
        plan.pop(k)
    return {"state": "COMPUTED", "policy": POLICY_ID, "piece_plan": plan, "installation": inst, "junction": jun,
            "flags": sorted(set(flags))}


def policy_record():
    return {"policy": POLICY_ID, "offcut_classes": list(OFFCUT_CLASSES), "junction_states": list(JUNCTION_STATES),
            "arrangement_cap": ARRANGEMENT_CAP, "closed_run_evaluation_cap": CLOSED_EVAL_CAP,
            "drain_kinds": list(DRAIN_KINDS)}
