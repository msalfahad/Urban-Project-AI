"""PRE-S5.1 ground-system source resolution + provenance cleanup (no S5 calculation, no kg).

    python3 -I research/pre_s5_1_source_resolution/build_pre_s5_1.py [ST7757.dxf] [P7757.dxf]

Inputs (Urban project sources only):
  * ST7757.dxf and P7757.dxf, sha256-checked (default data/inputs/by_sha256/<sha>.dxf), K2-decoded;
  * the pre-S5 network functions (research/pre_s5_ground_system_readiness/build_pre_s5.py, unchanged geometry) and
    its committed 04 / 06 registers (checked equal before anything is compared);
  * frozen S1 registers (slab panels, column chains, levels, project rules), the R4 visual claim / rule registers,
    the A3 PDF vertical evidence register (sections A-A / B-B), the floor-plan register.
No reference, donor or benchmark file is read. Decisions are made by engine/source/ground_system_resolution.py; this
builder only measures.

Measurements:
  * registration P7757 GF -> ST7757 GBP: architectural column outlines voted against GF-roof-slab outlines (one
    translation, every outline), plus the shared GFRS / GBP sheet frames;
  * wall-line cover of each ground-beam span: the span centreline is cut every 50 mm by a cross-section of the beam
    width + 50 mm; a P7757 GF wall-line element (paired masonry band, single wall-layer line, glazing, curved wall /
    glazing) parallel to the beam that crosses the cut covers that station; door / gate geometry in an otherwise
    uncovered station is an opening in the wall line;
  * exterior class of every wall element: the two faces are probed 400 mm out and the probe classified on the
    frozen S1 ground-beam-plan slab panels (ground slab = INSIDE, S1 OUTSIDE_BUILDING_OR_COURT = OUTSIDE, beyond the
    panelled plate = OUTSIDE, an unpanelled hole inside the plate = its architectural labels);
  * support faces: the member centreline (straight or arc) intersected with the actual start / end support
    polygons (column, supporting beam band, footing outline);
  * levels: the P7757 GF level marks inside the space the beam carries; outer ground from the sections.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import os
import re
import shutil
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
LAB = ROOT / "research" / "external_engine_lab"
PRE = ROOT / "research" / "pre_s5_ground_system_readiness"
for p in (ROOT, LAB, PRE, HERE):
    sys.path.insert(0, str(p))

import build_pre_s5 as B  # noqa: E402
from engine.source import arch_quantity_truth as AQ  # noqa: E402
from engine.source import canonical_input as CI  # noqa: E402
from engine.source import ground_system_provenance as GP  # noqa: E402
from engine.source import ground_system_resolution as GR  # noqa: E402
from engine.source import rebar_provenance as RP  # noqa: E402

BASELINE = "0a23c06"
ST_SHA = B.DXF_SHA
ARCH_SHA = "ab54dd554c31fe4a6a63ff773dc6d034159a736c7dd78158483b473a4ed31cc4"
DEFAULT_ST = B.DEFAULT_DXF
DEFAULT_ARCH = ROOT / "data" / "inputs" / "by_sha256" / f"{ARCH_SHA}.dxf"
S1 = ROOT / "research/alsenan_structural_census_s1"
R4 = ROOT / "research/alsenan_rebar_source_exhaustion_04/registers"
FLOOR_PLANS = ROOT / "tests/alsenan/registers/FLOOR_PLAN_REGISTER.json"
VERTICAL = ROOT / "tests/alsenan/registers_a3/PDF_VERTICAL_EVIDENCE_REGISTER.json"
PANELS = S1 / "SLAB_PANEL_REGISTER.json"
CHAINS = S1 / "COLUMN_VERTICAL_CHAIN_REGISTER.json"
LEVELS = S1 / "STRUCTURAL_LEVEL_REGISTER.json"
S1_RULES = S1 / "STRUCTURAL_PROJECT_RULE_REGISTER.json"
PRE_04 = PRE / "04_GROUND_BEAM_DETAIL_APPLICABILITY.csv"
PRE_06 = PRE / "06_GROUND_SYSTEM_REBAR_READINESS_MATRIX.csv"
CODE = ["engine/source/ground_system_resolution.py", "engine/source/rebar_provenance.py",
        "engine/source/ground_system_provenance.py", "engine/source/ground_beam_network.py",
        "research/pre_s5_ground_system_readiness/build_pre_s5.py",
        "research/pre_s5_1_source_resolution/build_pre_s5_1.py"]
INPUTS = [FLOOR_PLANS, VERTICAL, PANELS, CHAINS, LEVELS, S1_RULES, B.CLAIMS, B.RULES, PRE_04, PRE_06,
          S1 / "FOOTING_OCCURRENCE_REGISTER.json", S1 / "BEAM_OCCURRENCE_REGISTER.json", B.V3_REGISTER]
CONTEXT = dict(B.CONTEXT, REGISTER_VERSION="GROUND_SYSTEM_RESOLUTION_V1", CALCULATION_ROUND="PRE_S5_1")

WALL_LAYER, GLAZING_LAYER, DOOR_LAYER, COLUMN_LAYER, BOUNDARY_LAYER, LEVEL_LAYER = "1", "W", "D", "S-COL.BON", \
    "S-BOUN", "LEVEL"
WALL_PAIR_MM = (60.0, 450.0)          # R5 wall-ledger pairing convention (paired faces 60-450 mm apart)
SAMPLE_MM = 50.0
CUT_TOL_MM = 50.0
PARALLEL_DEG = 10.0
PROBE_MM = 400.0
PANEL_CLOSE_MM = 250.0                # bridges the 300 mm beam bands between S1 slab panels
END_ZONE_MM = 350.0                   # a junction within this distance of a span end is at the support
STAIR_NEAR_MM = 300.0
SYMBOL_NEAR_MM = 500.0
EXTEND_MM = 3000.0
INSIDE_WORDS = ("W.C", "WASH", "MOSL", "DINING", "KITCHEN", "BATH", "BED", "SALOON", "RECEPTION", "PANTRY",
                "DEWANEYA", "DRIVER")
OPEN_WORDS = ("COURT", "GARDEN", "POOL", "STREET", "NEIGHBOUR", "SEA VIEW")
LEVEL_RX = re.compile(r"^(?:%%p|\+|±|-)?(\d+\.\d\d)$")
INTERIOR_CLAUSE = ("P13-GB-GT5M", "P13-GB-LT5M")       # titles carrying 'without concentrated load'
EXT = "P13-GB-EXTERIOR"


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def code_digest():
    h = hashlib.sha256()
    for c in CODE:
        h.update((ROOT / c).read_bytes())
    return h.hexdigest()


J, r3, r1, wcsv, wjson = B.J, B.r3, B.r1, B.wcsv, B.wjson


def lay(p):
    return CI.effective_layer(p)[0]


def key_hex(k):
    return format(int(k.split("|")[1][1:]), "X")


# ===================================================================================================== network
def network(dxf, work):
    """The NEW pre-S5 network (unchanged functions) with occurrence ids and topology; checked equal to the committed
    pre-S5 register before use."""
    S, ctx = B.decode(dxf, work)
    cols = B.columns(S)
    bands, diag = B.bands_new(S, B.FACE_LAYERS)
    spans, outers = B.spans_v3_rule(S, bands, cols)
    fps = B.footprints(S, B.bands_new(S, {"1", "2"})[0], cols)
    src, S1M = B.fp_sheet(dxf)
    g0 = src.sheets["GBP"]["frame"]
    feet = B.footings_on(src, S1M, (g0[0], g0[1]))
    per = defaultdict(list)
    for sp in spans:
        per[sp["band"]].append(sp)
    for bid, sps in per.items():
        b = sps[0]["b"]
        if b["u"] is not None:
            sps.sort(key=lambda s: min(x * b["u"][0] + y * b["u"][1] for x, y in s["poly"].exterior.coords))
        else:
            sps.sort(key=lambda s: (round(s["poly"].centroid.x), round(s["poly"].centroid.y)))
        for k, sp in enumerate(sps):
            sp["occ_id"] = f"GSO-{bid.replace('ARC:', 'A-').replace('+', '-')}-{k + 1}"
    occs = []
    for sp in sorted(spans, key=lambda s: s["occ_id"]):
        topo = B.classify_ends(sp, spans, bands, cols, feet)
        occs.append({"occ_id": sp["occ_id"], "sp": sp, "b": sp["b"], "poly": sp["poly"], "topo": topo,
                     "clear_mm": sp["length_mm"], "cc_mm": topo["cc_mm"], "zone": bool(sp["exterior"]),
                     "footprint": min(f.exterior.distance(sp["poly"]) for f in fps) < B.TOUCH,
                     "width": sp["b"]["gn"]["width"] if "gn" in sp["b"] else B.WIDTH})
    pre = {r["OCCURRENCE_ID"]: r for r in csv.DictReader(io.StringIO(PRE_04.read_text(encoding="utf-8")))}
    bad = [o["occ_id"] for o in occs if o["occ_id"] not in pre or
           abs(float(pre[o["occ_id"]]["CLEAR_LENGTH_M"]) - o["clear_mm"] / 1000) > 6e-4 or
           (pre[o["occ_id"]]["EXTERIOR_ZONE_TEST"] == "True") != o["zone"] or
           (pre[o["occ_id"]]["EXTERIOR_FOOTPRINT_TEST"] == "True") != o["footprint"]]
    if bad or len(pre) != len(occs):
        raise SystemExit(f"STOP: the network does not reproduce the committed pre-S5 register: {bad}")
    return {"S": S, "cols": cols, "bands": bands, "occs": occs, "feet": feet, "src": src, "S1M": S1M, "gbp0": g0}


# ===================================================================================================== architecture
def architecture(arch_dxf, work, net):
    """P7757 GF plan in GBP coordinates: registration, wall-line elements, doors, texts."""
    import alsenan_phase_a as AP
    import alsenan_phase_b2a as B2A
    from shapely.geometry import LineString
    if _sha(arch_dxf) != ARCH_SHA:
        raise SystemExit(f"P7757.dxf sha mismatch (expected {ARCH_SHA})")
    A = AP.k2(Path(arch_dxf), AP.REV_ARCH, work / "p7757_k2.pkl")
    fp = J(FLOOR_PLANS)
    gf = tuple(next(s["bounds"] for s in fp["sheets"] if s["floor"] == "GF"))
    gfrs = net["src"].sheets["GFRS"]["frame"]
    gbp = net["src"].sheets["GBP"]["frame"]
    a_rects = B2A._col_rects(A, gf)
    s_rects = B2A._col_rects(net["S"], tuple(gfrs))
    votes = Counter()
    for x in a_rects:
        for y in s_rects:
            if round(x[1]) == round(y[1]) and round(x[2]) == round(y[2]):
                votes[(round(y[3][0] - x[3][0], 3), round(y[3][1] - x[3][1], 3))] += 1
    (tx, ty), n = votes.most_common(1)[0]
    second = votes.most_common(2)[1][1] if len(votes) > 1 else 0
    if n != len(a_rects) or n < 5 or second > 1:
        raise SystemExit(f"STOP: P7757 GF does not register to the GF roof slab ({n}/{len(a_rects)}, second {second})")
    T = (tx + gbp[0] - gfrs[0], ty + gbp[1] - gfrs[1])
    reg = {"arch_outlines": len(a_rects), "structural_outlines": len(s_rects), "matched": n, "second_best": second,
           "translation_arch_to_gfrs": [round(tx, 3), round(ty, 3)],
           "frame_offset_gfrs_to_gbp": [round(gbp[0] - gfrs[0], 3), round(gbp[1] - gfrs[1], 3)],
           "translation_arch_to_gbp": [round(T[0], 3), round(T[1], 3)], "state": "REGISTERED",
           "rule": "every architectural GF column outline lands on an equal GF-roof-slab outline under one "
                   "translation (no other translation explains more than one); GFRS and GBP share their sheet "
                   "frame (S1 frames)"}
    tr = lambda x, y: (x + T[0], y + T[1])
    parts = [p for p in A["parts"] if AP.in_box(p.geometry[0], p.geometry[1], gf)]
    segs = defaultdict(list)
    arcs = defaultdict(list)
    for p in parts:
        if p.kind == "SEGMENT" and math.dist(p.geometry[0:2], p.geometry[2:4]) > 1.0:
            segs[lay(p)].append((key_hex(p.identity.key), tr(*p.geometry[0:2]), tr(*p.geometry[2:4])))
        elif p.kind == "ARC":
            cx, cy, r, a0, a1 = p.geometry[:5]
            arcs[lay(p)].append((key_hex(p.identity.key), tr(cx, cy), r, a0, a1))
    els = []
    for q in AQ.pair_wall_faces(segs[WALL_LAYER], min_mm=WALL_PAIR_MM[0], max_mm=WALL_PAIR_MM[1]):
        if q["partner"] is not None:
            w = q["width"]
            kind = ("MASONRY_200" if abs(w - 200) < 15 else "MASONRY_150" if abs(w - 150) < 15 else
                    f"PAIRED_{round(w)}")
            els.append({"kind": kind, "line": LineString([q["centre_a"], q["centre_b"]]), "hw": w / 2.0,
                        "handles": sorted({q["seg"], q["partner"]}), "arc": False})
        else:
            els.append({"kind": "SINGLE_WALL_LINE", "line": LineString([q["a"], q["b"]]), "hw": 0.0,
                        "handles": [q["seg"]], "arc": False})
    for h, a, b in segs[GLAZING_LAYER]:
        els.append({"kind": "GLAZING", "line": LineString([a, b]), "hw": 0.0, "handles": [h], "arc": False})
    for layer, kind in ((WALL_LAYER, "CURVED_WALL_LINE"), (GLAZING_LAYER, "CURVED_GLAZING")):
        for h, c, r, a0, a1 in arcs[layer]:
            els.append({"kind": kind, "line": LineString(arc_points(c, r, a0, a1)), "hw": 0.0, "handles": [h],
                        "arc": True})
    doors = [LineString([a, b]) for h, a, b in segs[DOOR_LAYER]] + \
            [LineString(arc_points(c, r, a0, a1, 16)) for h, c, r, a0, a1 in arcs[DOOR_LAYER]]
    texts = [{"value": t.value.strip(), "xy": tr(t.x, t.y), "layer": t.layer}
             for t in A["texts"] if t.x is not None and t.value and AP.in_box(t.x, t.y, gf)]
    return {"registration": reg, "els": els, "doors": doors, "texts": texts, "gf_bounds": gf,
            "census": {"wall_layer_segments": len(segs[WALL_LAYER]), "glazing_segments": len(segs[GLAZING_LAYER]),
                       "wall_arcs": len(arcs[WALL_LAYER]), "glazing_arcs": len(arcs[GLAZING_LAYER]),
                       "door_entities": len(doors),
                       "elements_by_kind": dict(Counter(e["kind"] for e in els))}}


def arc_points(c, r, a0, a1, n=48):
    """K2 arc angles are radians (counter-clockwise from a0 to a1)."""
    if a1 < a0:
        a1 += 2 * math.pi
    return [(c[0] + r * math.cos(a0 + (a1 - a0) * i / n), c[1] + r * math.sin(a0 + (a1 - a0) * i / n))
            for i in range(n + 1)]


# ===================================================================================================== sides
def side_model(net, arch):
    """S1 ground-beam-plan slab panels in GBP coordinates, the panelled plate and its unpanelled holes."""
    from shapely.geometry import Point, Polygon
    from shapely.ops import unary_union
    g0 = net["gbp0"]
    panels = [{"id": r["panel_id"], "class": r["class"],
               "poly": Polygon([(x + g0[0], y + g0[1]) for x, y in r["polygon_mm"]]).buffer(0)}
              for r in J(PANELS)["rows"] if r["sheet"] == "GBP"]
    U = unary_union([p["poly"].buffer(PANEL_CLOSE_MM, join_style=2) for p in panels]).buffer(-PANEL_CLOSE_MM,
                                                                                            join_style=2)
    plate = unary_union([Polygon(g.exterior) for g in getattr(U, "geoms", [U])])
    holes_g = plate.difference(unary_union([p["poly"].buffer(160.0, join_style=2) for p in panels]))
    holes = []
    for g in getattr(holes_g, "geoms", [holes_g]):
        if g.area < 0.5e6:
            continue
        labs = [t["value"] for t in arch["texts"] if g.contains(Point(t["xy"]))]
        ins = [v for v in labs if any(w in v.upper() for w in INSIDE_WORDS)] + \
              [v for v in labs if LEVEL_RX.match(v) and v.startswith("+") and float(v[1:]) >= 0.30]
        out = [v for v in labs if any(w in v.upper() for w in OPEN_WORDS)] + \
              [v for v in labs if v in ("+0.15", "%%p0.00")]
        cls = "INSIDE" if ins and not out else "OUTSIDE" if out and not ins else "UNKNOWN"
        holes.append({"poly": g, "class": cls, "inside_labels": ins, "open_labels": out,
                      "area_m2": round(g.area / 1e6, 2)})

    def classify(p):
        pt = Point(p)
        for pn in panels:
            if pn["poly"].contains(pt):
                c = pn["class"]
                return ("INSIDE" if c in ("SLAB_PANEL", "STAIR_FLIGHT_ZONE") else
                        "OUTSIDE" if c == "OUTSIDE_BUILDING_OR_COURT" else "UNKNOWN"), pn["id"]
        for h in holes:
            if h["poly"].contains(pt):
                return h["class"], "HOLE"
        if not plate.contains(pt):
            return "OUTSIDE", "OFF_PLATE"
        return "UNKNOWN", None
    return {"panels": panels, "plate": plate, "holes": holes, "classify": classify}


def tangent(line, d):
    a = line.interpolate(max(d - 20.0, 0.0))
    b = line.interpolate(min(d + 20.0, line.length))
    tx, ty = b.x - a.x, b.y - a.y
    n = math.hypot(tx, ty) or 1.0
    return tx / n, ty / n


def classify_elements(arch, sides):
    for e in arch["els"]:
        L = e["line"]
        res = []
        for f in (0.25, 0.5, 0.75):
            d = L.length * f
            p = L.interpolate(d)
            tx, ty = tangent(L, d)
            nx, ny = -ty, tx
            o = e["hw"] + PROBE_MM
            a = sides["classify"]((p.x + nx * o, p.y + ny * o))[0]
            b = sides["classify"]((p.x - nx * o, p.y - ny * o))[0]
            res.append(GR.side_pair_class(a, b))
        e["ext"] = GR.vote(res)


# ===================================================================================================== spans
def span_path(o, offset=0.0):
    """Centreline (offset = 0) or a bar line (offset across the width, mm; arcs: radial) of the span, extended
    EXTEND_MM past both ends, as a LineString + the piece start / end params on it."""
    from shapely.geometry import LineString
    b = o["b"]
    if b["u"] is not None:
        s0, s1, mid, hw, u, n = B.piece_frame(o["sp"])
        pt = lambda s: (s * u[0] + (mid + offset) * n[0], s * u[1] + (mid + offset) * n[1])
        path = LineString([pt(s0 - EXTEND_MM), pt(s1 + EXTEND_MM)])
        return {"path": path, "p0": EXTEND_MM, "p1": EXTEND_MM + (s1 - s0), "hw": hw, "arc": False}
    g = b["gn"]
    cx, cy = g["centre"]
    rc = g["CENTERLINE_RADIUS"] + offset
    angs = sorted(math.atan2(y - cy, x - cx) % (2 * math.pi) for x, y in o["poly"].exterior.coords)
    gaps = [(angs[(i + 1) % len(angs)] - angs[i]) % (2 * math.pi) for i in range(len(angs))]
    k = max(range(len(gaps)), key=lambda i: gaps[i])
    a0 = angs[(k + 1) % len(angs)]
    sweep = (angs[k] - a0) % (2 * math.pi)
    ext = EXTEND_MM / rc
    m = 720
    path = LineString([(cx + rc * math.cos(a0 - ext + (sweep + 2 * ext) * i / m),
                        cy + rc * math.sin(a0 - ext + (sweep + 2 * ext) * i / m)) for i in range(m + 1)])
    return {"path": path, "p0": EXTEND_MM, "p1": EXTEND_MM + rc * sweep, "hw": g["width"] / 2.0, "arc": True}


def wall_samples(o, P, arch):
    from shapely.geometry import LineString, Point
    from shapely.strtree import STRtree
    tree = arch.setdefault("_tree", STRtree([e["line"].buffer(max(e["hw"], 30.0)) for e in arch["els"]]))
    dtree = arch.setdefault("_dtree", STRtree(arch["doors"]))
    path, p0, p1, hw = P["path"], P["p0"], P["p1"], P["hw"]
    m = max(1, int(round((p1 - p0) / SAMPLE_MM)))
    ds = (p1 - p0) / m
    out = []
    for i in range(m):
        d = p0 + (i + 0.5) * ds
        c = path.interpolate(d)
        ux, uy = tangent(path, d)
        nx, ny = -uy, ux
        h = hw + CUT_TOL_MM
        cut = LineString([(c.x - nx * h, c.y - ny * h), (c.x + nx * h, c.y + ny * h)])
        hits = []
        for j in tree.query(cut):
            e = arch["els"][j]
            if not e["line"].buffer(max(e["hw"], 30.0)).intersects(cut):
                continue
            ex, ey = tangent(e["line"], e["line"].project(c))
            if abs(ex * uy - ey * ux) > math.sin(math.radians(PARALLEL_DEG)):
                continue
            hits.append(e)
        if hits:
            best = max(hits, key=lambda e: (e["kind"].startswith(("MASONRY", "PAIRED")), e["kind"] == "GLAZING",
                                            e["hw"], e["handles"][0]))
            out.append({"len": ds, "element": best["kind"], "ext": best["ext"], "opening": False,
                        "handle": best["handles"][0], "handles": best["handles"]})
        else:
            box = cut.buffer(hw, cap_style=2)
            opening = any(arch["doors"][j].intersects(box) for j in dtree.query(box))
            out.append({"len": ds, "element": None, "ext": None, "opening": opening, "handle": None, "handles": []})
    return out


def slab_edge(o, P, sides):
    path, p0, p1, hw = P["path"], P["p0"], P["p1"], P["hw"]
    res, panels_in, panels_out = [], Counter(), Counter()
    for f in (0.2, 0.4, 0.6, 0.8):
        d = p0 + f * (p1 - p0)
        c = path.interpolate(d)
        ux, uy = tangent(path, d)
        nx, ny = -uy, ux
        o_ = hw + PROBE_MM
        (a, pa), (b, pb) = sides["classify"]((c.x + nx * o_, c.y + ny * o_)), \
            sides["classify"]((c.x - nx * o_, c.y - ny * o_))
        res.append(GR.side_pair_class(a, b))
        for cls, pid in ((a, pa), (b, pb)):
            (panels_in if cls == "INSIDE" else panels_out)[pid] += 1
    v = GR.vote(res)
    edge = {"EXTERIOR": "PERIMETER", "INTERIOR": "INTERNAL"}.get(v, "UNKNOWN")
    return {"SLAB_EDGE": edge, "PROBES": res, "INSIDE_PANELS": sorted(k for k in panels_in if k),
            "OUTSIDE_REFS": sorted(k for k in panels_out if k)}


# ===================================================================================================== supports
def support_polys(o, end, net, extra):
    """Polygons of the support at one end (column / beam band / footing), by the (re)classified node."""
    node = o["nodes"][end]
    kind, refs = node["kind"], node["refs"]
    if kind == "COLUMN":
        return [c["poly"] for c in net["cols"] if c["id"] in refs] or extra.get((o["occ_id"], end), [])
    if kind == "BEAM_JUNCTION":
        return [b["poly"] for b in net["bands"] if b["id"] in refs]
    if kind == "FOOTING":
        return [f["poly"] for f in net["feet"] if f["id"] in refs]
    return []


def face_param(P, polys, end):
    """Face station of the support at one end on one line (centreline or bar line): where the line enters the support
    outline on the span side; when the line passes beside the support (offset column, L-corner), the support face
    plane that crosses the beam direction, extended to the line. Returns (param, method) or (None, reason)."""
    from shapely.geometry import LineString
    path, p0, p1 = P["path"], P["p0"], P["p1"]
    pm = (p0 + p1) / 2.0
    side = (lambda t: t <= pm) if end == "start" else (lambda t: t >= pm)
    pick = max if end == "start" else min
    direct = [t for g in polys for t in _crossing(path, g) if side(t)]
    if direct:
        return pick(direct), "line x support outline"
    pe = p0 if end == "start" else p1
    ux, uy = tangent(path, pe)
    cands = []
    for g in polys:
        cs = list(g.exterior.coords)
        for a_, b_ in zip(cs, cs[1:]):
            ex, ey = b_[0] - a_[0], b_[1] - a_[1]
            L = math.hypot(ex, ey)
            if L < 1.0 or abs(ex / L * ux + ey / L * uy) > 0.5:      # the face must cross the beam direction (> 60 deg)
                continue
            ext = LineString([(a_[0] - ex / L * EXTEND_MM, a_[1] - ey / L * EXTEND_MM),
                              (b_[0] + ex / L * EXTEND_MM, b_[1] + ey / L * EXTEND_MM)])
            cands += [t for t in _crossing(path, ext) if side(t) and abs(t - pe) <= 1000.0]
    if cands:
        return pick(cands), "support face plane extended to the line (the support lies beside the line)"
    return None, "the line meets no support face"


def end_faces(P, polys):
    """Face params at the start / end of one line; None when that end has no support or no face."""
    out = {}
    for end in ("start", "end"):
        out[end] = face_param(P, polys[end], end)[0] if polys[end] else None
    return out


def faces_and_centres(o, P, polys):
    """Support face (centreline x support outline) and support reference point at each end."""
    path, p0, p1 = P["path"], P["p0"], P["p1"]
    out = {}
    for end in ("start", "end"):
        node = o["nodes"][end]
        if not polys[end]:
            out[end] = {"face": None, "centre": None, "how": f"no support polygon ({node['kind']})",
                        "centre_how": None}
            continue
        face, how = face_param(P, polys[end], end)
        if node["kind"] == "BEAM_JUNCTION":
            full = [t for g in polys[end] for t in _crossing(path, g)]
            centre = (min(full) + max(full)) / 2.0 if full else None
            centre_how = "carrier band mid-crossing on the centreline"
        elif node["kind"] == "FOOTING":
            centre = path.project(polys[end][0].centroid)
            centre_how = "footing outline centroid projected (no column: the centre is the footing's)"
        else:
            centre = path.project(polys[end][0].centroid)
            centre_how = "column centroid projected"
        out[end] = {"face": face, "centre": centre, "how": how, "centre_how": centre_how}
    return out


def _crossing(path, g):
    from shapely.geometry import Point
    x = path.intersection(g)
    return [path.project(Point(c)) for gg in getattr(x, "geoms", [x]) if not gg.is_empty for c in gg.coords]


# ===================================================================================================== free ends
def free_ends(net, arch):
    """Re-examine every FREE_END node with physical evidence; returns register rows and the corrected nodes."""
    from shapely.geometry import LineString, Point, Polygon
    from shapely.ops import polygonize, unary_union
    import alsenan_phase_a as AP
    S = net["S"]
    col_lines = [LineString([p.geometry[0:2], p.geometry[2:4]]) for p in S["parts"] if p.kind == "SEGMENT" and
                 lay(p) == COLUMN_LAYER and AP.in_box(p.geometry[0], p.geometry[1], B.GB_SHEET)]
    col_handles = [key_hex(p.identity.key) for p in S["parts"] if p.kind == "SEGMENT" and lay(p) == COLUMN_LAYER
                   and AP.in_box(p.geometry[0], p.geometry[1], B.GB_SHEET)]
    bnd = [(key_hex(p.identity.key), LineString([p.geometry[0:2], p.geometry[2:4]])) for p in S["parts"]
           if p.kind == "SEGMENT" and lay(p) == BOUNDARY_LAYER and AP.in_box(p.geometry[0], p.geometry[1],
                                                                              B.GB_SHEET)]
    rows, extra = [], {}
    for o in net["occs"]:
        for end in ("start", "end"):
            node = o["topo"][end]
            if node["kind"] != "FREE_END":
                continue
            if o["b"]["u"] is None:
                rows.append({"occ": o, "end": end, "cls": {"CLASS": "UNRESOLVED", "WHY": "curved span end"},
                             "ev": {}})
                continue
            s0, s1, mid, hw, u, n = B.piece_frame(o["sp"])
            s = s0 if end == "start" else s1
            pt = lambda ss, oo: (ss * u[0] + oo * n[0], ss * u[1] + oo * n[1])
            edge = LineString([pt(s, mid - hw), pt(s, mid + hw)])
            P = Point(pt(s, mid))
            dcol = min(((c["poly"].distance(edge), c["id"]) for c in net["cols"]), default=(None, None))
            near_lines = [(l, h) for l, h in zip(col_lines, col_handles) if l.distance(edge) <= GR.GAP_TOL_MM]
            outline_gap = min((l.distance(edge) for l, h in near_lines), default=None)
            outline_poly = None
            if near_lines:
                local = [l for l in col_lines if l.distance(edge) <= 1500.0]
                polys = [g for g in polygonize(unary_union(local)) if g.distance(edge) <= GR.GAP_TOL_MM]
                outline_poly = unary_union(polys) if polys else None
            inside = next((f["id"] for f in net["feet"] if f["poly"].contains(P)), None)
            bgap = min(((l.distance(P), h) for h, l in bnd), default=(None, None))
            band_gap = min((b["poly"].distance(edge) for b in net["bands"] if b["id"] != o["b"]["id"]), default=None)
            beyond = 0.0
            at_end = False
            sign = 1 if end == "end" else -1
            for e in arch["els"]:
                if e["line"].distance(P) < 350.0:
                    at_end = True
                    pr = [((x * u[0] + y * u[1]) - s) * sign for x, y in e["line"].coords]
                    beyond = max(beyond, max(pr))
            rect_gap = dcol[0] if dcol[0] is not None and dcol[0] <= GR.GAP_TOL_MM else None
            use_outline = outline_poly is not None and outline_gap is not None and \
                (rect_gap is None or outline_gap < rect_gap)
            cls = GR.free_end_class(column_gap_mm=None if use_outline else rect_gap,
                                    column_outline_gap_mm=outline_gap if use_outline else None,
                                    inside_footing=inside, boundary_gap_mm=bgap[0], band_gap_mm=band_gap,
                                    arch_wall_beyond_mm=beyond, arch_wall_at_end=at_end)
            ref = ("OUTLINE:" + "+".join(sorted({h for l, h in near_lines})) if cls["CLASS"] == "COLUMN" and use_outline
                   else dcol[1] if cls["CLASS"] == "COLUMN" else inside if cls["CLASS"] == "FOOTING" else
                   bgap[1] if cls["CLASS"] == "BOUNDARY" else None)
            if cls["CLASS"] == "COLUMN" and use_outline:
                extra[(o["occ_id"], end)] = [outline_poly]
            ev = {"nearest_column_rectangle": [dcol[1], r1(dcol[0])],
                  "column_outline_lines_within_50mm": sorted({h for l, h in near_lines}),
                  "column_outline_gap_mm": r1(outline_gap), "inside_footing_outline": inside,
                  "plot_boundary_line": [bgap[1], r1(bgap[0])], "nearest_other_beam_band_mm": r1(band_gap),
                  "arch_wall_at_end": at_end, "arch_wall_beyond_end_mm": r1(beyond)}
            rows.append({"occ": o, "end": end, "cls": cls, "ref": ref, "ev": ev})
    return rows, extra


# ===================================================================================================== loads
def load_evidence(o, net, sides):
    from shapely.geometry import Point
    import alsenan_phase_a as AP
    ev = []
    L = o["clear_mm"]
    for j in o["topo"]["intermediate"]:
        ob = next(b for b in net["bands"] if b["id"] == j["ref"])
        rest = ob["poly"].difference(o["b"]["poly"].buffer(1.0))
        geoms = [g for g in getattr(rest, "geoms", [rest]) if g.area > 1e4]
        if o["b"]["u"] is not None:
            u = o["b"]["u"]
            n = (-u[1], u[0])
            c = o["poly"].centroid
            sides_ = {1 if (g.centroid.x - c.x) * n[0] + (g.centroid.y - c.y) * n[1] > 0 else -1 for g in geoms}
            shape = "T" if len(sides_) == 1 else "X"
        else:
            shape = "T"
        st = j["station"]
        if st < END_ZONE_MM or st > L - END_ZONE_MM:
            ev.append({"kind": "JUNCTION_AT_SUPPORT", "ref": j["ref"], "detail": f"{shape}-junction at {st:.0f} mm "
                                                                                  f"of {L:.0f} mm (end zone)"})
        else:
            ev.append({"kind": "BEAM_END_REACTION" if shape == "T" else "BEAM_CROSSING", "ref": j["ref"],
                       "detail": f"{'beam ends on' if shape == 'T' else 'beam crosses'} the span at {st:.0f} mm of "
                                 f"{L:.0f} mm"})
    for c in net["cols"]:
        if c["poly"].intersection(o["poly"]).area > 1.0:
            ev.append({"kind": "COLUMN_BEARING_ON_SPAN", "ref": c["id"], "detail": "column outline inside the span"})
    for pn in sides["panels"]:
        if "STAIR" in pn["class"] and pn["poly"].distance(o["poly"]) <= STAIR_NEAR_MM:
            ev.append({"kind": "STAIR_BEARING_CANDIDATE", "ref": pn["id"],
                       "detail": f"ground-floor stair zone {pn['poly'].distance(o['poly']):.0f} mm from the span"})
    for t in net["gbp_texts"]:
        if re.fullmatch(r"\*{3,}", t["value"]) and Point(t["xy"]).distance(o["poly"]) <= SYMBOL_NEAR_MM:
            ev.append({"kind": "UNIDENTIFIED_SYMBOL", "ref": t["handle"],
                       "detail": f"'{t['value']}' (S-TEXT, no legend) {Point(t['xy']).distance(o['poly']):.0f} mm "
                                 "from the span"})
        if re.search(r"\b(LOAD|KN|TON|P\s*=)\b", t["value"].upper()) and \
                Point(t["xy"]).distance(o["poly"]) <= SYMBOL_NEAR_MM:
            ev.append({"kind": "POINT_LOAD_NOTE", "ref": t["handle"], "detail": t["value"]})
    return ev


# ===================================================================================================== levels
def level_marks(arch):
    out = []
    for t in arch["texts"]:
        m = LEVEL_RX.match(t["value"].replace(" ", ""))
        if t["layer"] == LEVEL_LAYER and m:
            v = float(m.group(1)) * (-1 if t["value"].startswith("-") else 1)
            out.append({"value_m": v, "xy": t["xy"], "text": t["value"]})
    return out


def follow_arch(o, edge, sides, marks, blocks, vert):
    from shapely.geometry import Point
    ins = [pn for pn in sides["panels"] if pn["id"] in edge["INSIDE_PANELS"]]
    holes_in = [h for h in sides["holes"] if "HOLE" in edge["INSIDE_PANELS"] and h["class"] == "INSIDE"]
    m_in = sorted({m["value_m"] for m in marks for g in [p["poly"] for p in ins] + [h["poly"] for h in holes_in]
                   if g.contains(Point(m["xy"]))})
    top, src, conf = None, None, "LOW"
    if len(m_in) == 1:
        top, src, conf = m_in[0], f"P7757 GF level mark {m_in[0]:+.2f} inside the carried space " \
                                  f"({', '.join(edge['INSIDE_PANELS'])})", "MEDIUM"
    else:
        blk = sorted({b["id"] for b in blocks for pn in ins if b["poly"].intersects(pn["poly"])} |
                     {b["id"] for b in blocks for h in holes_in if b["poly"].intersects(h["poly"])})
        bm = sorted({v for b in blocks if b["id"] in blk for v in b["marks"]})
        cands = m_in or bm
        if len(cands) == 1:
            top, src, conf = cands[0], f"building block {blk} carries the single GF level {cands[0]:+.2f}", "MEDIUM"
        elif cands:
            top, src, conf = max(cands), f"carried space / block level candidates {cands}: the upper bound uses " \
                                         f"{max(cands):+.2f}", "LOW"
        else:
            src = "no level mark in the carried space or its block"
    outs = edge["OUTSIDE_REFS"]
    bottom, bsrc = [], []
    if "OFF_PLATE" in outs:
        bottom.append(0.0)
        bsrc.append("outer natural ground +-0.00 (sections A-A VE-AA-01, B-B VE-BB-01; plan +-0.00 marks outside "
                    "the plate)")
    for pid in outs:
        if pid and pid.startswith("SP-"):
            pm = sorted({m["value_m"] for m in marks for pn in sides["panels"] if pn["id"] == pid
                         and pn["poly"].contains(Point(m["xy"]))})
            bottom += [0.0] + pm
            bsrc.append(f"{pid} (court / yard): natural ground +-0.00 (sections) and paving {pm} (plan)")
    bottom = sorted(set(bottom))
    d = GR.follow_arch_depth(top_ffl_m=top, top_source=src, buildup_known_m=None, bottom_levels_m=bottom,
                             bottom_source="; ".join(bsrc) or "outer side not established")
    flags = []
    if d["DEPTH_MAX_M"] is not None and d["DEPTH_MAX_M"] < 0.40:
        flags.append(f"DEPTH_BOUND_BELOW_TYPICAL_SECTION: D <= {d['DEPTH_MAX_M']:.2f} m is shallower than the "
                     "shallowest cross-verified ground-beam section (30 x 40); the exterior section draws three bar "
                     "levels and 70 mm soil cover")
    return dict(d, TOP_LEVEL_M=top, TOP_LEVEL=("GF slab level = FFL " + (f"{top:+.2f}" if top is not None else "?") +
                                               " - floor build-up (not printed)"),
                BOTTOM_LEVEL_M=bottom, CONFIDENCE=conf, FLAGS=flags)


def building_blocks(sides, marks):
    from shapely.geometry import Point
    from shapely.ops import unary_union
    ins = [pn["poly"] for pn in sides["panels"] if pn["class"] in ("SLAB_PANEL", "STAIR_FLIGHT_ZONE")] + \
          [h["poly"] for h in sides["holes"] if h["class"] == "INSIDE"]
    U = unary_union([g.buffer(PANEL_CLOSE_MM, join_style=2) for g in ins])
    out = []
    for i, g in enumerate(sorted(getattr(U, "geoms", [U]), key=lambda g: (round(g.bounds[0]), round(g.bounds[1])))):
        out.append({"id": f"BLOCK-{i + 1}", "poly": g, "area_m2": round(g.area / 1e6, 1),
                    "marks": sorted({m["value_m"] for m in marks if g.contains(Point(m["xy"]))})})
    return out


# ===================================================================================================== readiness
def bars(t):
    return None if t is None else f"{t[0]}Ø{t[1]}"


def readiness(o, lib, rules):
    C = o["cand"]["CANDIDATES"]
    state = o["cand"]["STATE"]
    run = o["run"]
    comp = {}

    def val(d, f):
        return None if d == GR.NO_DETAIL_IF_LOADED else f(lib[d])
    if not C or state == "NO_APPLICABLE_DETAIL":
        return {k: ("NO_APPLICABLE_DETAIL", None, "no applicable detail") for k in COMPONENTS}
    conflict = state == "SOURCE_CONFLICT"
    lb = run["BAR_STRAIGHT_RUN_LOWER_BOUND_MM"]
    for k, f in (("TOP_MAIN", lambda d: d["top"]), ("BOTTOM_ROW_1", lambda d: d["rows"][0]),
                 ("BOTTOM_ROW_2", lambda d: d["rows"][1])):
        vals = [val(d, f) for d in C]
        if any(v is None for v in vals):
            comp[k] = ("BLOCKED_COMPONENT", " | ".join(sorted({str(bars(v)) for v in vals})),
                       "concentrated-load case has no project detail (the 'without concentrated load' sections "
                       "cannot be confirmed)")
        elif len({repr(v) for v in vals}) > 1:
            comp[k] = ("BLOCKED_COMPONENT", " | ".join(sorted({bars(v) for v in vals})),
                       "candidate details disagree: " + "; ".join(f"{d} {bars(f(lib[d]))}" for d in C))
        elif conflict:
            comp[k] = ("BLOCKED_COMPONENT", bars(vals[0]), "exterior authority SOURCE_CONFLICT")
        elif lb is None:
            comp[k] = ("BLOCKED_COMPONENT", bars(vals[0]), f"bar run {run['BAR_RUN_STATE']}: " +
                       "; ".join(run["ISSUES"] or [run.get("WHY", "support face not established")]))
        else:
            comp[k] = ("READY_LOWER_BOUND", bars(vals[0]),
                       f"straight run >= support face-to-face {lb / 1000:.3f} m; development / anchorage not "
                       "source-established")
    real = [lib[d] for d in C if d != GR.NO_DETAIL_IF_LOADED]
    sides_ = [d["side"] for d in real]
    if GR.NO_DETAIL_IF_LOADED in C:
        comp["SIDE_BARS"] = ("BLOCKED_COMPONENT", None, "concentrated-load case has no project detail")
    elif all(s is None for s in sides_):
        comp["SIDE_BARS"] = ("NOT_APPLICABLE", None, "the candidate section(s) carry no side bars")
    else:
        dep = o.get("depth") or {}
        comp["SIDE_BARS"] = ("BLOCKED_COMPONENT", " | ".join(sorted(str(s) for s in sides_)),
                             "side bars 2Ø12 per 30 cm of depth; FOLLOW ARCH. depth " +
                             (f"bounded D <= {dep['DEPTH_MAX_M']:.2f} m (no lower bound)" if dep.get("DEPTH_MAX_M")
                              is not None else "unresolved") +
                             ("" if all(s is not None for s in sides_) else "; other candidates have none"))
    st = [None if d == GR.NO_DETAIL_IF_LOADED else lib[d]["stirrup"] for d in C]
    if any(s is None for s in st):
        dia = ("BLOCKED_COMPONENT", " | ".join(sorted(str(s) for s in st)),
               "a candidate has no stirrup callout (the < 2.5 m section draws a link with no size / spacing) or no "
               "detail")
        rate = dia
    elif len({repr(s) for s in st}) == 1 and not conflict:
        dia = ("READY", f"Ø{st[0][0]}", "typical section callout")
        rate = ("READY", f"{st[0][1]} mm", "typical section callout")
    else:
        dia = rate = ("BLOCKED_COMPONENT", " | ".join(sorted(str(s) for s in st)),
                      "candidate callouts differ" if not conflict else "exterior authority SOURCE_CONFLICT")
    comp["STIRRUP_DIAMETER"], comp["STIRRUP_RATE"] = dia, rate
    Ds = [d["D"] for d in real]
    if GR.NO_DETAIL_IF_LOADED in C:
        core = ("BLOCKED_COMPONENT", None, "concentrated-load case has no project detail")
    elif any(D is None for D in Ds):
        core = ("BLOCKED_COMPONENT", "D = FOLLOW ARCH.", "section depth FOLLOW ARCH.: bounded above only")
    elif len(set(Ds)) > 1:
        core = ("BLOCKED_COMPONENT", " | ".join(f"300x{D:.0f}" for D in sorted(set(Ds))),
                "candidate sections differ in depth")
    elif any(d["section_state"] != "CROSS_VERIFIED_SOURCE" for d in real):
        core = ("PROVISIONAL_ONLY", f"300x{Ds[0]:.0f}", "section size is an AI transcription only")
    else:
        core = ("PROVISIONAL_ONLY", f"300x{Ds[0]:.0f}, cover 70 (soil)",
                "B, D and cover source-established; the closed link is drawn but its topology is not a verified "
                "facet")
    comp["STIRRUP_CORE_PATH"] = core
    comp["STIRRUP_COUNT"] = (("READY_LOWER_BOUND", rate[1], f"count >= ceil(face-to-face {lb / 1000:.3f} m / "
                                                            "spacing); first / last position not stated")
                             if rate[0] == "READY" and lb is not None else
                             ("BLOCKED_COMPONENT", None, "spacing or face-to-face run not established"))
    hook = rules["HOOKS_AND_BENDS"]
    comp["HOOK_1"] = comp["HOOK_2"] = ("BLOCKED_COMPONENT", None,
                                       f"hook angle / extension: {hook['source_state']} ({hook['note']})")
    comp["END_ZONE_EXTRA"] = ("NOT_APPLICABLE", None, "the section prints one uniform spacing; no end-zone callout")
    dev = rules["DEVELOPMENT_STARTER_70D_40D"]
    comp["END_TREATMENT"] = ("BLOCKED_COMPONENT", None, "bar ends at the supports are not detailed")
    comp["DEVELOPMENT_INTO_SUPPORT_1"] = comp["DEVELOPMENT_INTO_SUPPORT_2"] = (
        "BLOCKED_COMPONENT", None, f"no beam-end anchorage rule in the project source ({dev['rule_id']} is "
                                   f"'{dev['scope']}' only)")
    comp["LAP"] = ("NOT_APPLICABLE", None, "net measurement: laps are a procurement matter (BBS firewall)")
    return comp


COMPONENTS = ("TOP_MAIN", "BOTTOM_ROW_1", "BOTTOM_ROW_2", "SIDE_BARS", "STIRRUP_DIAMETER", "STIRRUP_RATE",
              "STIRRUP_CORE_PATH", "STIRRUP_COUNT", "HOOK_1", "HOOK_2", "END_ZONE_EXTRA", "END_TREATMENT",
              "DEVELOPMENT_INTO_SUPPORT_1", "DEVELOPMENT_INTO_SUPPORT_2", "LAP")


def strap_readiness(st, rules):
    rows = st["_rows"]
    comp = {}
    clear = st["_clear_m"]
    straight = (f"straight run >= clear concrete length between footing faces {clear:.3f} m (the bars cross the clear "
                "opening); DEVELOPMENT_INTO_FOOTING_1 / _2 BLOCKED_UNQUANTIFIED")
    for k, f in (("TOP_MAIN", lambda r: r["top"]), ("BOTTOM_ROW_1", lambda r: r["bottom"])):
        vals = [f(r) for r in rows]
        comp[k] = (("READY_LOWER_BOUND", bars(vals[0]), straight) if len(set(vals)) == 1 else
                   ("BLOCKED_COMPONENT", " | ".join(bars(v) for v in vals),
                    "duplicated schedule key: the two rows give different bars (SOURCE_CONFLICT)"))
    comp["BOTTOM_ROW_2"] = ("NOT_APPLICABLE", None, "the schedule gives one BOTTOM total; no second row is stated")
    comp["SIDE_BARS"] = ("NOT_APPLICABLE", None, "p.8 note 21 applies to depth > 60 cm; schedule H = " +
                         ", ".join("%.0f" % r["H_cm"] for r in rows) + " cm")
    stv = [r["stirrups_per_m"] for r in rows]
    inv = len(set(stv)) == 1
    tag = " (identical in every schedule row: CANDIDATE_INVARIANT)" if len(rows) > 1 and inv else ""
    comp["STIRRUP_DIAMETER"] = (("READY", f"Ø{stv[0][1]}", "SBT D column" + tag) if inv else
                                ("BLOCKED_COMPONENT", " | ".join(str(v) for v in stv), "rows disagree"))
    comp["STIRRUP_RATE"] = (("READY", f"{stv[0][0]}/m", "SBT STI-B ('STIRRUPS/m')" + tag) if inv else
                            comp["STIRRUP_DIAMETER"])
    comp["STIRRUP_CORE_PATH"] = ("BLOCKED_COMPONENT", " | ".join("%.0fx%.0f" % (r["W_cm"], r["H_cm"]) for r in rows),
                                 ("section width conflict; " if len({r["W_cm"] for r in rows}) > 1 else "") +
                                 "leg count / link topology not stated (schedule row, no section sketch)")
    comp["STIRRUP_COUNT"] = (("READY_LOWER_BOUND", comp["STIRRUP_RATE"][1],
                              f"count >= ceil(rate x clear length {clear:.3f} m)" + tag)
                             if comp["STIRRUP_RATE"][0] == "READY" else ("BLOCKED_COMPONENT", None, "rate unknown"))
    hook = rules["HOOKS_AND_BENDS"]
    comp["HOOK_1"] = comp["HOOK_2"] = ("BLOCKED_COMPONENT", None, f"{hook['source_state']} ({hook['note']})")
    comp["END_ZONE_EXTRA"] = ("NOT_APPLICABLE", None, "the schedule gives one rate per metre")
    comp["END_TREATMENT"] = ("BLOCKED_COMPONENT", None, "bar ends inside the footings are not detailed")
    dev = rules["DEVELOPMENT_STARTER_70D_40D"]
    comp["DEVELOPMENT_INTO_SUPPORT_1"] = comp["DEVELOPMENT_INTO_SUPPORT_2"] = (
        "BLOCKED_COMPONENT", None, f"BLOCKED_UNQUANTIFIED: development into the footing not source-established "
                                   f"({dev['rule_id']} is '{dev['scope']}' only)")
    comp["LAP"] = ("NOT_APPLICABLE", None, "net measurement: laps are a procurement matter (BBS firewall)")
    return comp


# ===================================================================================================== main
def main(st_dxf, arch_dxf):
    work = Path(tempfile.mkdtemp(prefix="pre_s5_1_"))
    try:
        return _main(Path(st_dxf), Path(arch_dxf), work)
    finally:
        shutil.rmtree(work, ignore_errors=True)


def _main(st_dxf, arch_dxf, work):
    import alsenan_phase_a as AP
    from shapely.geometry import Point
    stamp = f"{BASELINE}+code:{code_digest()[:16]}"
    context = dict(CONTEXT, ENGINE_COMMIT=stamp)
    net = network(st_dxf, work)
    net["gbp_texts"] = [{"value": t.value.strip(), "xy": (t.x, t.y), "layer": t.layer,
                         "handle": key_hex(t.identity.key)} for t in net["S"]["texts"]
                        if t.x is not None and t.value and AP.in_box(t.x, t.y, B.GB_SHEET)]
    arch = architecture(arch_dxf, work, net)
    sides = side_model(net, arch)
    classify_elements(arch, sides)
    marks = level_marks(arch)
    blocks = building_blocks(sides, marks)
    lib, claims = B.detail_library()
    rules = {r["rule_id"]: r for r in J(B.RULES)["rules"]}
    vert = J(VERTICAL)
    conditions = {k: d["cond"] for k, d in lib.items() if d["cond"]}
    cover = float(rules["COVER_AGAINST_SOIL_70MM"]["value"])          # mm, p.8 n.22 (ground beams, straps)

    # ---------------- free ends -> corrected nodes
    fe_rows, extra = free_ends(net, arch)
    fe_map = {(r["occ"]["occ_id"], r["end"]): r for r in fe_rows}
    for o in net["occs"]:
        o["nodes"] = {}
        for end in ("start", "end"):
            n0 = dict(o["topo"][end])
            r = fe_map.get((o["occ_id"], end))
            if r is not None:
                c = r["cls"]["CLASS"]
                n0 = {"kind": {"COLUMN": "COLUMN", "FOOTING": "FOOTING", "BOUNDARY": "BOUNDARY"}.get(c, "FREE_END"),
                      "refs": [r["ref"]] if r.get("ref") else [], "station": None, "was": "FREE_END",
                      "class": c}
            o["nodes"][end] = n0

    # ---------------- per span
    for o in net["occs"]:
        P = span_path(o)
        o["P"] = P
        samples = wall_samples(o, P, arch)
        o["wall"] = GR.wall_relation(samples)
        o["wall"]["HANDLES"] = sorted({h for s in samples for h in s["handles"]})
        o["edge"] = slab_edge(o, P, sides)
        o["auth"] = GR.exterior_authority(relation=o["wall"]["RELATION"], slab_edge=o["edge"]["SLAB_EDGE"],
                                          zone_test=o["zone"], footprint_test=o["footprint"])
        polys = {e: support_polys(o, e, net, extra) for e in ("start", "end")}
        fc = faces_and_centres(o, P, polys)
        cs, ce = fc["start"]["centre"], fc["end"]["centre"]
        cl = abs(ce - cs) if cs is not None and ce is not None else None
        o["fc"] = fc
        lines = []
        d = P["hw"] - cover
        for off in (-d, d):
            Pl = span_path(o, off)
            f = end_faces(Pl, polys)
            lines.append({"offset_mm": off, "run_mm": (f["end"] - f["start"]) if None not in f.values() else None,
                          "misses": [e for e in ("start", "end") if f[e] is None and polys[e]]})
        o["run"] = GR.bar_run(centreline_mm=cl, clear_concrete_mm=o["clear_mm"], face_start=fc["start"]["face"],
                              face_end=fc["end"]["face"], bar_lines=lines)
        if o["run"]["SUPPORT_FACE_TO_FACE_RUN_MM"] is None:
            o["run"]["WHY"] = "; ".join(f"{e}: {fc[e]['how']}" for e in ("start", "end") if fc[e]["face"] is None)
        clear_basis = o["run"]["SUPPORT_FACE_TO_FACE_RUN_MM"] if o["run"]["SUPPORT_FACE_TO_FACE_RUN_MM"] is not None \
            else o["clear_mm"]
        o["basis"] = GR.length_basis({"CLEAR": clear_basis / 1000.0,
                                      "CENTRELINE": cl / 1000.0 if cl is not None else None}, conditions)
        o["basis"]["CLEAR_BASIS_MEASURE"] = ("SUPPORT_FACE_TO_FACE_RUN" if o["run"]["SUPPORT_FACE_TO_FACE_RUN_MM"]
                                             is not None else "MEMBER_CLEAR_CONCRETE_LENGTH")
        conc = GR.length_conditions(o["clear_mm"] / 1000.0, conditions)
        o["basis"]["DETAIL_BY_CLEAR_CONCRETE_LENGTH"] = conc
        o["load"] = GR.concentrated_load(load_evidence(o, net, sides))
        nested = {"P13-GB-LT2_5M", "P13-GB-LT5M"} <= set(o["basis"]["UNION"])
        o["prec"] = GR.nested_precedence(narrower_condition="P13-GB-LT2_5M" if nested else None)
        o["nested"] = nested
        o["cand"] = GR.candidate_details(authority=o["auth"]["AUTHORITY"], length_union=o["basis"]["UNION"],
                                         load_state=o["load"]["STATE"], clause_details=INTERIOR_CLAUSE,
                                         exterior_detail=EXT, basis_same=o["basis"]["SAME_RESULT"], nested=nested,
                                         precedence=o["prec"])
        o["depth"] = follow_arch(o, o["edge"], sides, marks, blocks, vert) if EXT in o["cand"]["CANDIDATES"] else None
        o["comp"] = readiness(o, lib, rules)
        o["status"] = B.occ_status(o["comp"])

    # ---------------- straps
    straps, _ = B.strap_census(net["src"], net["S1M"], st_dxf)
    for st in straps:
        st["comp"] = strap_readiness(st, rules)
        st["status"] = B.occ_status(st["comp"])
        st["app_state"] = "EXPLICIT_MARK_MATCH" if len(st["_rows"]) == 1 else "CANDIDATE_DETAIL"

    out = HERE
    return write_all(out, net, arch, sides, marks, blocks, straps, fe_rows, lib, claims, rules, vert, context, stamp)


# ===================================================================================================== writers
def nodej(n):
    return {"kind": n["kind"], "refs": n.get("refs") or []}


def write_all(out, net, arch, sides, marks, blocks, straps, fe_rows, lib, claims, rules, vert, context, stamp):
    occs = net["occs"]
    pre06 = list(csv.DictReader(io.StringIO(PRE_06.read_text(encoding="utf-8"))))
    pre_status = {r["OCCURRENCE_ID"]: r["OCCURRENCE_S5_STATUS"] for r in pre06}
    pre_comp = {(r["OCCURRENCE_ID"], r["COMPONENT"]): r["S5_STATUS"] for r in pre06}
    pre04 = {r["OCCURRENCE_ID"]: r for r in csv.DictReader(io.StringIO(PRE_04.read_text(encoding="utf-8")))}

    # 02 overlay
    ov = []
    for o in occs:
        w = o["wall"]
        ov.append({"GB_SPAN_ID": o["occ_id"], "STRUCTURAL_HANDLES": o["b"]["handles"],
                   "ARCH_WALL_HANDLES": w["HANDLES"], "SPAN_LENGTH_M": r3(w["SPAN_LENGTH_MM"] / 1000),
                   "OVERLAP_LENGTH": r3(w["OVERLAP_LENGTH_MM"] / 1000), "WALL_LENGTH_M": r3(w["WALL_LENGTH_MM"] / 1000),
                   "OPENING_LENGTH_M": r3(w["OPENING_LENGTH_MM"] / 1000),
                   "OVERLAP_PERCENT": round(100 * w["OVERLAP_PERCENT"], 1),
                   "WALL_WIDTH": w["WALL_CLASS"], "WALL_CLASS": w["RELATION"], "EXTERIOR_CLASS": w["EXTERIOR_CLASS"],
                   "EXTERIOR_SHARE": round(w["EXTERIOR_SHARE"], 3), "INTERIOR_SHARE": round(w["INTERIOR_SHARE"], 3),
                   "BY_EXTERIOR_CLASS_M": {k: r3(v / 1000) for k, v in w["BY_EXTERIOR_CLASS_MM"].items()},
                   "BY_ELEMENT_M": {k: r3(v / 1000) for k, v in w["BY_ELEMENT_MM"].items()},
                   "SLAB_EDGE": o["edge"]["SLAB_EDGE"], "INSIDE_PANELS": o["edge"]["INSIDE_PANELS"],
                   "OUTSIDE_REFS": o["edge"]["OUTSIDE_REFS"],
                   "MATCH_METHOD": "centreline cut every 50 mm across beam width + 50 mm; parallel (< 10 deg) P7757 GF "
                                   "wall-line element crossing the cut; wall class by 400 mm face probes on the S1 "
                                   "GBP slab panels",
                   "AUTHORITY": "ARCHITECTURAL_PLAN (P7757 GF) + STRUCTURAL_SLAB_PANELS (S1 GBP)",
                   "NOTES": w["WHY"]})
    wcsv(out / "02_GROUND_BEAM_ARCH_WALL_OVERLAY.csv", ov, list(ov[0]))

    # 03 exterior authority
    ex = []
    for o in occs:
        a = o["auth"]
        pre_state = pre04[o["occ_id"]]["DETAIL_APPLICABILITY_STATE"]
        ex.append({"GB_SPAN_ID": o["occ_id"], "V3_ZONE_TEST": o["zone"], "R4_FOOTPRINT_TEST": o["footprint"],
                   "PROXIES_DISAGREED": o["zone"] != o["footprint"], "ARCH_WALL_RELATION": o["wall"]["RELATION"],
                   "SLAB_EDGE": o["edge"]["SLAB_EDGE"], "EXTERIOR_AUTHORITY": a["AUTHORITY"], "WHY": a["WHY"],
                   "PROXIES_AGREE_WITH_AUTHORITY": a["PROXIES_AGREE_WITH_AUTHORITY"],
                   "PRE_S5_APPLICABILITY": pre_state, "PRE_S5_1_APPLICABILITY": o["cand"]["STATE"],
                   "DETAIL_CANDIDATES": o["cand"]["CANDIDATES"]})
    wcsv(out / "03_EXTERIOR_AUTHORITY_REGISTER.csv", ex, list(ex[0]))

    # 04 follow arch
    fa = []
    for o in occs:
        d = o["depth"]
        if d is None:
            continue
        fa.append({"GB_SPAN_ID": o["occ_id"], "EXTERIOR_AUTHORITY": o["auth"]["AUTHORITY"],
                   "TOP_LEVEL": d["TOP_LEVEL"], "TOP_LEVEL_FFL_M": d["TOP_LEVEL_M"], "BOTTOM_LEVEL_M": d["BOTTOM_LEVEL_M"],
                   "ARCH_LEVEL_SOURCE": d["TOP_SOURCE"], "BOTTOM_LEVEL_SOURCE": d["BOTTOM_SOURCE"],
                   "DERIVED_DEPTH_MAX_M": d["DEPTH_MAX_M"], "DERIVED_DEPTH_MIN_M": d["DEPTH_MIN_M"],
                   "DERIVATION": d["DERIVATION"], "OUTCOME": d["STATE"], "CONFIDENCE": d["CONFIDENCE"],
                   "FLAGS": d["FLAGS"]})
    wcsv(out / "04_FOLLOW_ARCH_DEPTH_REGISTER.csv", fa, list(fa[0]))

    # 05 length basis
    lb = []
    for o in occs:
        r, b = o["run"], o["basis"]
        lb.append({"GB_SPAN_ID": o["occ_id"], "START_NODE": nodej(o["nodes"]["start"]),
                   "END_NODE": nodej(o["nodes"]["end"]),
                   "MEMBER_CENTERLINE_LENGTH_M": r3(r["MEMBER_CENTERLINE_LENGTH_MM"] / 1000
                                                    if r["MEMBER_CENTERLINE_LENGTH_MM"] is not None else None),
                   "MEMBER_CLEAR_CONCRETE_LENGTH_M": r3(r["MEMBER_CLEAR_CONCRETE_LENGTH_MM"] / 1000),
                   "SUPPORT_FACE_TO_FACE_RUN_M": r3(r["SUPPORT_FACE_TO_FACE_RUN_MM"] / 1000
                                                    if r["SUPPORT_FACE_TO_FACE_RUN_MM"] is not None else None),
                   "BAR_STRAIGHT_RUN_LOWER_BOUND_M": r3(r["BAR_STRAIGHT_RUN_LOWER_BOUND_MM"] / 1000
                                                        if r["BAR_STRAIGHT_RUN_LOWER_BOUND_MM"] is not None else None),
                   "LENGTH_STATE": r["LENGTH_STATE"], "BAR_RUN_STATE": r["BAR_RUN_STATE"],
                   "LENGTH_ISSUES": r["ISSUES"] + ([r["WHY"]] if r.get("WHY") else []),
                   "FACE_METHOD": {e: o["fc"][e]["how"] for e in ("start", "end")},
                   "CENTRE_METHOD": {e: o["fc"][e].get("centre_how") for e in ("start", "end")},
                   "CLEAR_BASIS_MEASURE": b["CLEAR_BASIS_MEASURE"],
                   "DETAIL_BY_CLEAR_LENGTH": b["DETAIL_BY_CLEAR_LENGTH"],
                   "DETAIL_BY_CENTRELINE_LENGTH": b["DETAIL_BY_CENTRELINE_LENGTH"],
                   "DETAIL_BY_CLEAR_CONCRETE_LENGTH": b["DETAIL_BY_CLEAR_CONCRETE_LENGTH"],
                   "SAME_RESULT": b["SAME_RESULT"], "ON_THRESHOLD": b["ON_THRESHOLD"],
                   "PRE_S5_CLEAR_M": float(pre04[o["occ_id"]]["CLEAR_LENGTH_M"]),
                   "PRE_S5_CENTRELINE_M": (float(pre04[o["occ_id"]]["SUPPORT_CENTRELINE_LENGTH_M"])
                                           if pre04[o["occ_id"]]["SUPPORT_CENTRELINE_LENGTH_M"] else None)})
    wcsv(out / "05_LENGTH_BASIS_ANALYSIS.csv", lb, list(lb[0]))

    # 06 concentrated loads
    cl = []
    for o in occs:
        ev = o["load"]["EVIDENCE"]
        cl.append({"GB_SPAN_ID": o["occ_id"], "LOAD_STATE": o["load"]["STATE"],
                   "EVIDENCE_KINDS": dict(Counter(e["kind"] for e in ev)), "EVIDENCE": ev,
                   "TITLE_CLAUSE_AFFECTS": [d for d in o["basis"]["UNION"] if d in INTERIOR_CLAUSE]
                   if o["auth"]["AUTHORITY"] != "EXTERIOR_SOURCE_VERIFIED" else [],
                   "SEARCHED": "columns on the span, planted-column chains (S1), beam junctions inside the span, "
                               "GF stair zones (S1 GBP panels), GBP texts (symbols, LOAD / kN / P= notes)",
                   "NOTE": "absence of a symbol is not proof: NO_CONCENTRATED_LOAD_EVIDENCE means no bearing member "
                           "or symbol was found, not that the span is load-free"})
    wcsv(out / "06_CONCENTRATED_LOAD_REGISTER.csv", cl, list(cl[0]))

    # 09 free ends
    fr = []
    for r in fe_rows:
        o = r["occ"]
        fr.append({"GB_SPAN_ID": o["occ_id"], "END": r["end"], "PRE_S5_NODE": "FREE_END",
                   "CLASSIFICATION": r["cls"]["CLASS"], "SUPPORT_REF": r.get("ref"), "WHY": r["cls"]["WHY"],
                   "EVIDENCE": r["ev"],
                   "EFFECT": {"COLUMN": "support face from the column outline", "FOOTING":
                              "support face where the centreline enters the footing outline; centre = footing "
                              "centroid (no column)", "BOUNDARY": "no support: the bar run at this end is unresolved"}
                   .get(r["cls"]["CLASS"], "unresolved")})
    wcsv(out / "09_GROUND_BEAM_FREE_END_REGISTER.csv", fr, list(fr[0]))

    # 10 readiness matrix
    mat, templates = [], []
    for o in occs:
        a = o["cand"]
        t = GP.template(family="GROUND_BEAM", occurrence_id=o["occ_id"], mark="GB (typical p.13)",
                        start_node=nodej(o["nodes"]["start"]), end_node=nodej(o["nodes"]["end"]),
                        handles=o["b"]["handles"], detail_id=a["CANDIDATES"], applicability=a["STATE"],
                        context=context)
        templates.append(t)
        base = {"OCCURRENCE_ID": o["occ_id"], "ELEMENT_FAMILY": "GROUND_BEAM", "MARK": "untagged (p.13 typical)",
                "EXTERIOR_AUTHORITY": o["auth"]["AUTHORITY"], "LOAD_STATE": o["load"]["STATE"],
                "LENGTH_STATE": o["run"]["LENGTH_STATE"],
                "BAR_STRAIGHT_RUN_LOWER_BOUND_M": r3(o["run"]["BAR_STRAIGHT_RUN_LOWER_BOUND_MM"] / 1000
                                                     if o["run"]["BAR_STRAIGHT_RUN_LOWER_BOUND_MM"] else None),
                "REBAR_DETAIL_ID": a["CANDIDATES"], "DETAIL_APPLICABILITY": a["STATE"],
                "PROVENANCE_READY": GP.provenance_ready(t), "OCCURRENCE_S5_STATUS": o["status"],
                "PRE_S5_OCCURRENCE_STATUS": pre_status.get(o["occ_id"])}
        for f in COMPONENTS:
            st_, val, why = o["comp"][f]
            inv = a["STATE"] == "CANDIDATE_DETAIL" and st_ in ("READY", "READY_LOWER_BOUND")
            mat.append(dict(base, COMPONENT=f, COMPONENT_VALUE=val, S5_STATUS=st_, WHY=why, CANDIDATE_INVARIANT=inv,
                            MAY_RELEASE=st_ in ("READY", "READY_LOWER_BOUND") and
                            GP.may_release(a["STATE"], candidate_invariant=inv),
                            PRE_S5_STATUS=pre_comp.get((o["occ_id"], f))))
    for st in straps:
        rows_def = st["_rows"]
        t = GP.template(family="STRAP_BEAM", occurrence_id=st["STRAP_OCCURRENCE_ID"], mark=st["MARK"],
                        start_node=nodej(dict(kind="FOOTING", refs=[st["START_SUPPORT"]["footing"]])),
                        end_node=nodej(dict(kind="FOOTING", refs=[st["END_SUPPORT"]["footing"]])),
                        handles=st["SOURCE_HANDLES"], detail_id=[f"SBT:{r['insert']}" for r in rows_def],
                        applicability=st["app_state"], context=context)
        templates.append(t)
        base = {"OCCURRENCE_ID": st["STRAP_OCCURRENCE_ID"], "ELEMENT_FAMILY": "STRAP_BEAM", "MARK": st["MARK"],
                "EXTERIOR_AUTHORITY": "NOT_APPLICABLE", "LOAD_STATE": "NOT_ASSESSED (straps: schedule-defined)",
                "LENGTH_STATE": "CONSISTENT",
                "BAR_STRAIGHT_RUN_LOWER_BOUND_M": st["CLEAR_CONCRETE_LENGTH_M"],
                "REBAR_DETAIL_ID": [f"SBT:{r['insert']}" for r in rows_def], "DETAIL_APPLICABILITY": st["app_state"],
                "PROVENANCE_READY": GP.provenance_ready(t), "OCCURRENCE_S5_STATUS": st["status"],
                "PRE_S5_OCCURRENCE_STATUS": pre_status.get(st["STRAP_OCCURRENCE_ID"])}
        for f in COMPONENTS:
            st_, val, why = st["comp"][f]
            inv = st["app_state"] == "CANDIDATE_DETAIL" and st_ in ("READY", "READY_LOWER_BOUND")
            mat.append(dict(base, COMPONENT=f, COMPONENT_VALUE=val, S5_STATUS=st_, WHY=why, CANDIDATE_INVARIANT=inv,
                            MAY_RELEASE=st_ in ("READY", "READY_LOWER_BOUND") and
                            GP.may_release(st["app_state"], candidate_invariant=inv),
                            PRE_S5_STATUS=pre_comp.get((st["STRAP_OCCURRENCE_ID"], f))))
    wcsv(out / "10_GROUND_SYSTEM_REBAR_READINESS_MATRIX.csv", mat, list(mat[0]))
    wjson(out / "S5_1_PROVENANCE_TEMPLATES.json", {"fields": list(GP.S5_PROVENANCE_FIELDS),
                                                    "identity_fields": list(RP.IDENTITY_FIELDS),
                                                    "context": context, "templates": templates})

    # summary json (feeds the markdown + tests)
    gb_status = Counter(o["status"] for o in occs)
    moved = [{"OCCURRENCE_ID": o["occ_id"], "FROM": pre_status.get(o["occ_id"]), "TO": o["status"],
              "EXTERIOR_AUTHORITY": o["auth"]["AUTHORITY"], "LOAD_STATE": o["load"]["STATE"],
              "BAR_RUN_STATE": o["run"]["BAR_RUN_STATE"], "APPLICABILITY": o["cand"]["STATE"],
              "BLOCKERS": sorted({o["comp"][k][2] for k in ("TOP_MAIN", "BOTTOM_ROW_1", "BOTTOM_ROW_2")
                                  if o["comp"][k][0] not in ("READY", "READY_LOWER_BOUND")})}
             for o in occs if pre_status.get(o["occ_id"]) != o["status"]]
    amb = [o for o in occs if o["zone"] != o["footprint"]]
    summary = {
        "baseline": BASELINE, "engine_stamp": stamp, "st7757_sha256": ST_SHA, "p7757_sha256": ARCH_SHA,
        "policy": GR.policy_record(), "registration": arch["registration"], "arch_census": arch["census"],
        "slab_panels": {"gbp_panels": len(sides["panels"]),
                        "by_class": dict(Counter(p["class"] for p in sides["panels"])),
                        "plate_area_m2": round(sides["plate"].area / 1e6, 1),
                        "holes": [{k: h[k] for k in ("class", "inside_labels", "open_labels", "area_m2")}
                                  for h in sides["holes"]]},
        "blocks": [{"id": b["id"], "area_m2": b["area_m2"], "level_marks_m": b["marks"]} for b in blocks],
        "level_marks": sorted(Counter(m["value_m"] for m in marks).items()),
        "wall_relation": dict(Counter(o["wall"]["RELATION"] for o in occs)),
        "exterior_authority": dict(Counter(o["auth"]["AUTHORITY"] for o in occs)),
        "ambiguous_19": {"count": len(amb), "by_authority": dict(Counter(o["auth"]["AUTHORITY"] for o in amb)),
                         "resolved": sum(o["auth"]["AUTHORITY"] in ("EXTERIOR_SOURCE_VERIFIED",
                                                                    "INTERIOR_SOURCE_VERIFIED") for o in amb),
                         "spans": {o["occ_id"]: o["auth"]["AUTHORITY"] for o in amb}},
        "follow_arch": {"spans": len(fa), "by_outcome": dict(Counter(r["OUTCOME"] for r in fa)),
                        "depth_max_m": dict(Counter(str(r["DERIVED_DEPTH_MAX_M"]) for r in fa)),
                        "flagged_shallow": [r["GB_SPAN_ID"] for r in fa if r["FLAGS"]]},
        "length": {"by_length_state": dict(Counter(o["run"]["LENGTH_STATE"] for o in occs)),
                   "by_bar_run_state": dict(Counter(o["run"]["BAR_RUN_STATE"] for o in occs)),
                   "basis_same": sum(o["basis"]["SAME_RESULT"] for o in occs),
                   "basis_differs": [o["occ_id"] for o in occs if not o["basis"]["SAME_RESULT"]],
                   "conflicts": {o["occ_id"]: o["run"]["ISSUES"] for o in occs
                                 if o["run"]["LENGTH_STATE"] == "LENGTH_GEOMETRY_CONFLICT"},
                   "unresolved": {o["occ_id"]: o["run"].get("WHY") for o in occs
                                  if o["run"]["LENGTH_STATE"] == "BAR_RUN_GEOMETRY_UNRESOLVED"}},
        "loads": {"by_state": dict(Counter(o["load"]["STATE"] for o in occs)),
                  "by_kind": dict(Counter(e["kind"] for o in occs for e in o["load"]["EVIDENCE"])),
                  "planted_columns": [{"chain": r["chain_id"], "planted_on": r["planted_on"], "type": r["column_type"]}
                                      for r in J(CHAINS)["rows"] if r.get("planted_on")]},
        "nested": {"spans": sum(o["nested"] for o in occs),
                   "precedence": dict(Counter(o["prec"]["RULE_PRECEDENCE_SOURCE"] for o in occs if o["nested"]))},
        "free_ends": {"nodes": len(fe_rows), "by_class": dict(Counter(r["cls"]["CLASS"] for r in fe_rows))},
        "applicability": dict(Counter(o["cand"]["STATE"] for o in occs)),
        "readiness": {"ground_beams": dict(gb_status),
                      "ground_beams_pre_s5": dict(Counter(pre_status[o["occ_id"]] for o in occs)),
                      "straps": {s["MARK"]: s["status"] for s in straps},
                      "straps_pre_s5": {s["MARK"]: pre_status.get(s["STRAP_OCCURRENCE_ID"]) for s in straps},
                      "gb_component_status": {k: dict(Counter(o["comp"][k][0] for o in occs)) for k in COMPONENTS},
                      "strap_component_status": {k: dict(Counter(s["comp"][k][0] for s in straps))
                                                 for k in COMPONENTS},
                      "moved": moved},
        "straps": [{k: s[k] for k in ("STRAP_OCCURRENCE_ID", "MARK", "SOURCE_HANDLES", "START_SUPPORT", "END_SUPPORT",
                                      "CLEAR_CONCRETE_LENGTH_M", "CENTERLINE_SUPPORT_TO_SUPPORT_M",
                                      "FOOTING_CENTRE_TO_CENTRE_M", "DRAWN_FACE_LENGTH_M", "WIDTH_DRAWN_MM",
                                      "WIDTH_SCHEDULE_CM", "DEPTH_SCHEDULE_CM", "SCHEDULE_DETAIL_REFERENCE",
                                      "REINFORCEMENT_REFERENCE", "AUTHORITY_STATE", "FLAGS")} for s in straps],
        "vertical_evidence": [{k: i.get(k) for k in ("id", "view", "kind", "text", "value_m", "reading")}
                              for i in vert["items"] if i["kind"] in ("LEVEL_MARK", "FFL", "DIMENSION_CHAIN")],
        "gbp_dimensions": gbp_dimension_census(net),
    }
    wjson(out / "PRE_S5_1_SUMMARY.json", summary)
    import write_docs  # noqa: E402  (sibling module: markdown deliverables from the summary)
    write_docs.write(out, summary, occs, straps, lib, claims, rules)
    index = {"baseline": BASELINE, "engine_stamp": stamp, "drawings": {"ST7757.dxf": ST_SHA, "P7757.dxf": ARCH_SHA},
             "inputs": {str(Path(p).relative_to(ROOT)): _sha(p) for p in INPUTS},
             "code": {c: _sha(ROOT / c) for c in CODE + ["research/pre_s5_1_source_resolution/write_docs.py"]},
             "outputs": {n: _sha(out / n) for n in sorted(os.listdir(out))
                         if n[:2].isdigit() or n in ("PRE_S5_1_SUMMARY.json", "S5_1_PROVENANCE_TEMPLATES.json")}}
    wjson(out / "INDEX.json", index)
    print(json.dumps({k: summary[k] for k in ("wall_relation", "exterior_authority", "ambiguous_19", "follow_arch",
                                              "loads", "free_ends", "applicability")}, indent=1, default=str))
    print(json.dumps({k: v for k, v in summary["readiness"].items() if k != "moved" and "component" not in k},
                     indent=1))
    print(json.dumps(summary["length"], indent=1, default=str)[:3000])
    return summary


def gbp_dimension_census(net):
    """Printed dimensions on the ground-beam plan: what their extension points sit on (axis / face)."""
    import alsenan_phase_a as AP
    from shapely.geometry import LineString, Point
    S = net["S"]
    axes = [LineString([p.geometry[0:2], p.geometry[2:4]]) for p in S["parts"] if p.kind == "SEGMENT"
            and lay(p) == "S-AXIS" and AP.in_box(p.geometry[0], p.geometry[1], B.GB_SHEET)]
    faces = [LineString([p.geometry[0:2], p.geometry[2:4]]) for p in S["parts"] if p.kind == "SEGMENT"
             and lay(p) in ("1", COLUMN_LAYER) and AP.in_box(p.geometry[0], p.geometry[1], B.GB_SHEET)]
    D = [d for d in S["dims"] if d.definition_points and
         AP.in_box(d.definition_points[0][0], d.definition_points[0][1], B.GB_SHEET)]
    kinds = Counter()
    for d in D:
        k = []
        for p in d.definition_points[:2]:
            a = min(ax.distance(Point(p)) for ax in axes) if axes else 1e9
            f = min(fa.distance(Point(p)) for fa in faces) if faces else 1e9
            k.append("AXIS" if a < 5 else "FACE" if f < 5 else "OTHER")
        kinds["-".join(sorted(k))] += 1
    return {"dimensions": len(D), "extension_points": dict(kinds),
            "reading": "the plan dimensions are axis-to-axis grid chains (plus edge offsets); none dimensions a "
                       "ground-beam span face-to-face; the plan does not define what 'length' means in the p.13 "
                       "titles"}


if __name__ == "__main__":
    a = sys.argv[1:]
    main(a[0] if len(a) > 0 else DEFAULT_ST, a[1] if len(a) > 1 else DEFAULT_ARCH)
