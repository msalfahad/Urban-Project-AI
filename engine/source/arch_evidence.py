"""ARCHITECTURAL EVIDENCE (M4) - what an architectural floor plan says about the ground beams under it (generic; stdlib +
engine.source geometry helpers). Nothing here reads a layer name, a coordinate or a mark of any project.

The printed exterior ground-beam detail of a villa set is usually captioned 'for exterior walls': it applies where an
exterior wall stands on the beam, which only the architectural plan shows. A beam on the perimeter of the ground-beam
network is a CANDIDATE, never evidence by itself.

    plan_sheets(model)              architectural floor-plan sheets by their printed title ('GROUND FLOOR PLAN') ->
                                    {storey: sheet}; roof / slab titles are structural and never match
    register(arch_boxes, struct_boxes)
                                    the translation that lands the architectural column outlines on the structural
                                    ones: centre differences of size-compatible pairs are voted on a 10 mm grid; the
                                    winner is refined on every column within 60 mm and accepted only when at least
                                    min_share of the architectural columns land and it beats the runner-up clearly
    levels(texts)                   printed levels on the plan ('+1.00', '%%p0.00'), metres
    wall_cover(axis, segments)      share of a beam's length under a drawn wall: a 50 mm station is covered when at
                                    least two parallel lines lie over the beam (within its width plus the wall
                                    reach) at offsets 0.10 - 0.45 m apart - the two faces of a wall, or the frame of a
                                    window / door set in it
    gb_exterior(D, arch_intake)     per ground-beam band of the plan: wall cover, the band's outside side (structural
                                    band_sides), the nearest printed floor level on its inside ->
                                        EXTERIOR_WALL          a wall stands on the band and one side is outside
                                        INTERIOR_WALL          a wall stands on the band, both sides inside
                                        PERIMETER_NO_WALL      one side is outside, no wall on the band
                                        NOT_PERIMETER          inside, no wall
                                        NOT_REGISTERED         no architectural plan / registration failed
"""

from __future__ import annotations

import math
import re
from collections import Counter

from engine.source import drawing_model as DM
from engine.source import level_marks as LM
from engine.source import member_detection as MD

POLICY_ID = "ARCH_EVIDENCE_V1"
PLAN_TITLE = re.compile(r"\b(GROUND|FIRST|1ST|SECOND|2ND|THIRD|3RD|BASEMENT)\s*\.?\s*FLOOR\s*PLAN\b")
NOT_ARCH = re.compile(r"ROOF|SLAB|BEAM|FOUNDATION|COLUMN|CEILING")
STOREY = {"GROUND": "GF", "FIRST": "1F", "1ST": "1F", "SECOND": "2F", "2ND": "2F", "THIRD": "3F", "3RD": "3F",
          "BASEMENT": "B1"}
CLASSES = ("EXTERIOR_WALL", "INTERIOR_WALL", "PERIMETER_NO_WALL", "NOT_PERIMETER", "NOT_REGISTERED")


def plan_sheets(model):
    out = {}
    for s in model["sheets"]:
        for t in model["texts"]:
            if t.get("sheet") != s["sheet_id"]:
                continue
            up = t["norm"].upper()
            m = PLAN_TITLE.search(up)
            if m and not NOT_ARCH.search(up):
                out.setdefault(STOREY[m.group(1)], s)
    return out


def _centre(b):
    return (b[0] + b[2]) / 2.0, (b[1] + b[3]) / 2.0, b[2] - b[0], b[3] - b[1]


def register(arch_boxes, struct_boxes, unit_m, *, size_tol_m=0.03, land_m=0.06, min_share=0.6, min_lead=2.0):
    """-> {state, dx, dy, landed, n_arch, votes, runner_up} (dx, dy in drawing units: struct = arch + (dx, dy))."""
    votes = Counter()
    st = [_centre(b) for b in struct_boxes]
    for a in arch_boxes:
        ca = _centre(a)
        for cs in st:
            same = (abs(ca[2] - cs[2]) <= size_tol_m / unit_m and abs(ca[3] - cs[3]) <= size_tol_m / unit_m)
            if same:
                g = 0.01 / unit_m
                votes[(round((cs[0] - ca[0]) / g) * g, round((cs[1] - ca[1]) / g) * g)] += 1
    if not votes:
        return {"state": "NO_COMMON_COLUMNS", "n_arch": len(arch_boxes)}
    (dx, dy), n1 = votes.most_common(1)[0]
    n2 = votes.most_common(2)[1][1] if len(votes) > 1 else 0
    land = land_m / unit_m
    pairs = []
    for a in arch_boxes:
        ca = _centre(a)
        best = min(st, key=lambda cs: math.hypot(ca[0] + dx - cs[0], ca[1] + dy - cs[1]))
        if math.hypot(ca[0] + dx - best[0], ca[1] + dy - best[1]) <= land:
            pairs.append((best[0] - ca[0], best[1] - ca[1]))
    if pairs:
        dx = sum(p[0] for p in pairs) / len(pairs)
        dy = sum(p[1] for p in pairs) / len(pairs)
    share = len(pairs) / max(1, len(arch_boxes))
    ok = share >= min_share and n1 >= min_lead * max(1, n2)
    return {"state": "REGISTERED" if ok else "NOT_REGISTERED", "dx": dx, "dy": dy, "landed": len(pairs),
            "n_arch": len(arch_boxes), "share": round(share, 3), "votes": n1, "runner_up": n2}


def levels(texts):
    out = []
    for t in texts:
        v = LM.parse_level(t.get("value") or t.get("norm"))
        if v is not None:
            out.append({"x": t["x"], "y": t["y"], "level_m": v})
    return out


def wall_cover(axis, segments, unit_m, *, beam_w_m, reach_m=0.25, t_min_m=0.10, t_max_m=0.45, angle_tol_deg=2.0,
               station_m=0.05):
    """axis: (p0, p1) beam centreline in the segments' frame. -> share of stations covered by a wall (0..1)."""
    (x0, y0), (x1, y1) = axis
    L = math.hypot(x1 - x0, y1 - y0)
    if L <= 0:
        return 0.0
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    nx, ny = -uy, ux
    lim = (beam_w_m / 2.0 + reach_m) / unit_m
    lines = []
    for s in segments:
        (ax, ay), (bx, by) = s["a"], s["b"]
        ls = math.hypot(bx - ax, by - ay)
        if ls <= 0:
            continue
        if abs((bx - ax) / ls * ny - (by - ay) / ls * nx) > math.sin(math.radians(angle_tol_deg)) and \
                abs(abs((bx - ax) / ls * ux + (by - ay) / ls * uy) - 1.0) > 1 - math.cos(math.radians(angle_tol_deg)):
            continue
        oa = (ax - x0) * nx + (ay - y0) * ny
        ob = (bx - x0) * nx + (by - y0) * ny
        if abs(oa - ob) > 0.01 / unit_m or abs(oa) > lim:
            continue
        ta = (ax - x0) * ux + (ay - y0) * uy
        tb = (bx - x0) * ux + (by - y0) * uy
        lines.append((min(ta, tb), max(ta, tb), (oa + ob) / 2.0))
    n = max(1, int(L * unit_m / station_m))
    cov = 0
    for k in range(n):
        t = (k + 0.5) * L / n
        offs = sorted(o for a, b, o in lines if a <= t <= b)
        hit = False
        for i in range(len(offs)):
            for j in range(i + 1, len(offs)):
                d = (offs[j] - offs[i]) * unit_m
                if t_min_m <= d <= t_max_m:
                    hit = True
                    break
            if hit:
                break
        cov += hit
    return cov / n


def gb_exterior(D, arch_intake, *, min_cover=0.5):
    """-> {registration, sheet, bands: {band_id: {class, wall_cover, outside, floor_level_m}}} for the ground-beam
    plan of D (generic_route.detect), from one architectural intake (tools.urban_intake)."""
    gb = next((r for r in D["sheets"].values() if r["sheet"]["role"] == "GROUND_BEAM_PLAN"), None)
    if gb is None or not gb.get("bands"):
        return {"registration": {"state": "NO_GROUND_BEAM_PLAN"}, "bands": {}}
    u_s = D["unit_m"]
    M = DM.build(arch_intake)
    plans = plan_sheets(M)
    sh = plans.get("GF")
    if sh is None:
        return {"registration": {"state": "NO_GROUND_FLOOR_PLAN", "arch_sheets": len(M["sheets"])},
                "bands": {b["band_id"]: {"class": "NOT_REGISTERED"} for b in gb["bands"]}}
    u_a = arch_intake.get("unit_m") or M["units"]["unit_m"]
    if abs(u_a - u_s) > 1e-12:
        return {"registration": {"state": "UNIT_MISMATCH"}, "bands": {}}
    E = DM.sheet_entities(M, arch_intake, sh["sheet_id"])
    rects = MD.candidate_rects(E, u_a)
    acol = [r["box"] for r in rects if MD._layer_role(r["layer"]) == "COLUMN"]
    if len(acol) < 3:      # no layer named for columns: every column-sized outline is a candidate
        acol = [r["box"] for r in rects if 0.15 <= min(r["box"][2] - r["box"][0], r["box"][3] - r["box"][1]) * u_a
                and max(r["box"][2] - r["box"][0], r["box"][3] - r["box"][1]) * u_a <= 1.5]
    scol = list(gb.get("column_boxes", [])) + list(gb.get("column_presence", []))
    reg = register(acol, scol, u_s)
    reg.update(arch_sheet=sh["sheet_id"], arch_columns=len(acol), struct_columns=len(scol))
    if reg["state"] != "REGISTERED":
        return {"registration": reg, "bands": {b["band_id"]: {"class": "NOT_REGISTERED"} for b in gb["bands"]}}
    dx, dy = reg["dx"], reg["dy"]
    segs = [dict(s, a=(s["a"][0] + dx, s["a"][1] + dy), b=(s["b"][0] + dx, s["b"][1] + dy)) for s in E["segments"]
            if MD._layer_role(s["layer"]) not in MD.ANNOTATION_ROLES + ("COLUMN",)]
    lv = [dict(v, x=v["x"] + dx, y=v["y"] + dy) for v in levels(E["texts"])]
    sides = gb.get("band_sides", {})
    faces = (gb.get("slab") or {}).get("faces", [])
    out = {}
    for b in gb["bands"]:
        if b["kind"] != "STRAIGHT":
            out[b["band_id"]] = {"class": "NOT_PERIMETER" if "OUTSIDE" not in sides.get(b["band_id"], []) else
                                 "PERIMETER_NO_WALL", "wall_cover": None, "note": "curved band: wall cover not tested"}
            continue
        u, n = b["u"], (-b["u"][1], b["u"][0])
        mid = (b["lo_off"] + b["hi_off"]) / 2.0
        p0 = (u[0] * b["t0"] + n[0] * mid, u[1] * b["t0"] + n[1] * mid)
        p1 = (u[0] * b["t1"] + n[0] * mid, u[1] * b["t1"] + n[1] * mid)
        w_m = b["width_native"] * u_s
        cov = wall_cover((p0, p1), segs, u_s, beam_w_m=w_m)
        sd = sides.get(b["band_id"], [])
        outside = "OUTSIDE" in sd
        wall = cov >= min_cover
        cls = ("EXTERIOR_WALL" if outside else "INTERIOR_WALL") if wall else \
            ("PERIMETER_NO_WALL" if outside else "NOT_PERIMETER")
        # the inside floor level: the nearest printed level on the inside half-plane, within 8 m of the band middle
        fl = None
        if outside:
            mx, my = (p0[0] + p1[0]) / 2.0, (p0[1] + p1[1]) / 2.0
            probe = (w_m / 2.0 + 0.3) / u_s
            sgn = None
            # the inside is the side whose probe lands in a slab panel; several stations, since a beam meeting the
            # band at one station leaves no panel there
            for f_ in (0.5, 0.25, 0.75, 0.1, 0.9):
                sx, sy = p0[0] + (p1[0] - p0[0]) * f_, p0[1] + (p1[1] - p0[1]) * f_
                for s_ in (1.0, -1.0):
                    q = (sx + n[0] * probe * s_, sy + n[1] * probe * s_)
                    if any(f["class"] == "PANEL" and MD.point_in_poly(q[0], q[1], f["polygon"]) for f in faces):
                        sgn = s_
                        break
                if sgn is not None:
                    break
            cand = []
            for v in lv if sgn is not None else ():
                o = (v["x"] - mx) * n[0] + (v["y"] - my) * n[1]
                dist = math.hypot(v["x"] - mx, v["y"] - my) * u_s
                if o * sgn > 0 and dist <= 8.0:
                    cand.append((dist, v["level_m"]))
            if cand:
                fl = min(cand)[1]
        out[b["band_id"]] = {"class": cls, "wall_cover": round(cov, 3), "outside": outside,
                             "floor_level_m": fl, "sides": sd}
    return {"registration": reg, "bands": out, "levels_found": len(lv)}


def lintel_openings(D, arch_intake):
    """M4: per architectural floor plan, the jambed wall openings (lintel_measure.openings) and whether a structural
    beam of the slab above covers each (the plan is registered on that slab plan's column outlines).
    -> {storey: {registration, wall_layers, openings: [opening + beam_over], rejected}}."""
    from engine.source import lintel_measure as LM_
    M = DM.build(arch_intake)
    u = arch_intake.get("unit_m") or M["units"]["unit_m"]
    out = {}
    for st, sh in sorted(plan_sheets(M).items()):
        slab = next((r for r in D["sheets"].values() if r["sheet"]["role"] == "SLAB_PLAN" and
                     r["sheet"]["storey"] == st), None)
        E = DM.sheet_entities(M, arch_intake, sh["sheet_id"])
        rects = MD.candidate_rects(E, u)
        acol = [r["box"] for r in rects if MD._layer_role(r["layer"]) == "COLUMN"]
        lays, score = LM_.wall_layers(E["segments"], u)
        ops, rej = LM_.openings(E["segments"], u, lays, acol)
        rec = {"arch_sheet": sh["sheet_id"], "wall_layers": lays, "openings": ops, "rejected": rej,
               "registration": {"state": "NO_SLAB_PLAN"}}
        if slab is not None:
            reg = register(acol, list(slab.get("column_boxes", [])) + list(slab.get("column_presence", [])),
                           D["unit_m"])
            rec["registration"] = reg
            if reg["state"] == "REGISTERED":
                beams = [[(x - reg["dx"], y - reg["dy"]) for x, y in b["polygon"]] for b in slab.get("bands", [])
                         if b["kind"] == "STRAIGHT"]
                for op in ops:
                    op["beam_over"] = LM_.beam_over(op, beams)
        out[st] = rec
    return out


def policy_record():
    return {"policy": POLICY_ID, "classes": list(CLASSES),
            "rule": "the exterior detail applies where the architecture draws a wall on a band with an outside side; "
                    "perimeter position alone is a candidate, never evidence"}
