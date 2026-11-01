"""T-436 Alsenan run: the three ground-slab parts the r4 concrete roll-up left with no owner (T-428), re-measured.

    .work/venv/bin/python -I research/agents_t436/t436_alsenan.py --dxf "<.work/private>/ST7757 dxf.dxf" \
        [--freelancer "<.work/private>/<concrete + rebar workbook>.xlsx" --out <checkout>/.work/private/t436] [--write]
    .work/venv/bin/python -I research/agents_t436/t436_alsenan.py --check      # no private input: summary re-adds

Inputs: the structural DXF (sha 9f9d1179, Drive 'Alsenan chalet project'), the T-391 own partition rebuilt with the
merged extractor (research/agents_t391/t391_extract.py, asserted face by face against OWN_GROUND_T391.json), the
candidate ground-slab lines (research/agents_t347/CANDIDATE_V3024_BURIED_LINES.json = V3.0.29 .. V3.0.37 for this
family, T-428), the T-428 r4 parts. Printed: values in m2 / m3, DXF handles, engine ids; no coordinates, no names, no
freelancer row value (his area stays in --out, outside the repository).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "research" / "agents_t391"))
import t436_rules as R  # noqa: E402

DXF_SHA = "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079"
OWN = ROOT / "research" / "agents_t391" / "OWN_GROUND_T391.json"
LINES = ROOT / "research" / "agents_t347" / "CANDIDATE_V3024_BURIED_LINES.json"
SUMMARY = HERE / "summary_t436.json"
T_SLAB = 0.10                                   # 'T=10cm' GROUND BEAMS PLAN (T-206 DRAWING-CONFIRMED)
FP_DX = 117654.3026476346 - 78929.89653886131   # T-141 frames: FOUNDATION PLAN -> GROUND BEAMS PLAN (same size)
# T-428 r4 parts (merged ea8f5ae5) this task restates; asserted against its committed summary below
PARTS = {"GS-STAIR-ZONE": -0.837230, "GS-BEYOND-NETWORK": -0.638640, "GS-FACES": -0.084700}
CELLS = {"stair": "SITE-4df8fcd99d130701", "f18": "SITE-49a7dae5c139aebb", "court_n": "SITE-d74f3fe29b88467a",
         "court_s": "SITE-0caa2bd2c0478041", "lift_a": "SITE-3f7728a83b30ec14", "lift_b": "SITE-c1b4b440fb6ecf4c"}
BAND0038 = "L-970bac563cbcd69e2a30"


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def t428_parts():
    d = json.loads((ROOT / "research" / "agents_t428" / "summary_t428.json").read_text(encoding="utf-8"))
    found = []

    def walk(x):
        if isinstance(x, dict):
            if x.get("component") == "GS-SLAB" and isinstance(x.get("m3"), (int, float)) and "owner" in x:
                found.append(x)
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
    walk(d)
    causes = {}
    for k, v in PARTS.items():
        hit = [x for x in found if abs(x["m3"] - v) < 5e-7]
        if len(hit) != 1:
            raise SystemExit(f"T-428 part {k} {v}: found {len(hit)} times in the merged unexplained list, not once")
        causes[k] = hit[0]["cause"]
    return causes


def engine_lines():
    d = json.loads(LINES.read_text(encoding="utf-8"))
    gs = {ln["element_id"].split(":")[-1]: ln for ln in d["lines"] if ln["item_code"] == "STR.CONC.GROUND_SLAB"}
    gb = {ln["line_id"]: ln for ln in d["lines"] if ln["item_code"] == "STR.CONC.GROUND_BEAM"}
    return gs, gb


def measure(dxf):
    import ezdxf
    from ezdxf import bbox as BB
    from shapely.geometry import LineString, Point, Polygon
    from shapely.ops import split, unary_union
    import t391_extract as X

    if _sha(dxf) != DXF_SHA:
        raise SystemExit("structural DXF sha mismatch")
    out, _ = X.read(dxf)
    own = {f["face"]: f for f in json.loads(OWN.read_text(encoding="utf-8"))["faces"]}
    for r in out:
        if abs(r["area_m2"] - own[r["face"]]["area_m2"]) > 1e-4 or r["kind"] != own[r["face"]]["kind"]:
            raise SystemExit(f"{r['face']}: T-391 partition not reproduced")
    F = {r["face"]: r["_g"] for r in out}
    doc = ezdxf.readfile(dxf)
    db = doc.entitydb
    res = {}

    # ---- A. stair-zone panel OWN-011 (physical element: slab on grade under / beside the GF curved flight foot)
    g = F["OWN-011"]
    inside, other = [], []
    for e in doc.modelspace():
        try:
            b = BB.extents([e])
        except Exception:
            continue
        if not b.has_data:
            continue
        box = Polygon([(b.extmin.x, b.extmin.y), (b.extmax.x, b.extmin.y), (b.extmax.x, b.extmax.y),
                       (b.extmin.x, b.extmax.y)]) if b.size.x > 0 and b.size.y > 0 else Point(b.center.x, b.center.y)
        if not g.buffer(-5).intersects(box):
            continue
        lt = e.dxf.get("linetype", "BYLAYER")
        if lt.upper() == "BYLAYER":
            lt = doc.layers.get(e.dxf.layer).dxf.linetype
        rec = {"handle": e.dxf.handle, "type": e.dxftype(), "layer": e.dxf.layer, "linetype": lt.upper()}
        (inside if e.dxf.layer == "2" else other).append(rec)
    # foundation plan: what is drawn below the panel (outlines moved by the frame offset)
    fp_hits = []
    for e in doc.modelspace().query("LWPOLYLINE INSERT"):
        if e.dxf.layer != "S-FOOTINGS" and not (e.dxftype() == "INSERT" and e.dxf.name.upper().startswith("F")):
            continue
        try:
            b = BB.extents([e])
        except Exception:
            continue
        if not b.has_data:
            continue
        box = Polygon([(b.extmin.x - FP_DX, b.extmin.y), (b.extmax.x - FP_DX, b.extmin.y),
                       (b.extmax.x - FP_DX, b.extmax.y), (b.extmin.x - FP_DX, b.extmax.y)])
        if box.intersects(g):
            cols = []
            for cpl in doc.modelspace().query("LWPOLYLINE[layer=='S-COL.BON']"):
                cb = BB.extents([cpl])
                if cb.has_data and box.contains(Point(cb.center.x - FP_DX, cb.center.y)):
                    cols.append(cpl.dxf.handle)
            fp_hits.append({"handle": e.dxf.handle, "layer": e.dxf.layer, "column_outlines_inside": cols,
                            "under_panel_m2": round(box.intersection(g).area / 1e6, 4)})
    res["stair_panel"] = {"face": "OWN-011", "area_m2": round(g.area / 1e6, 6), "edge_handles": own["OWN-011"]["edge_handles"],
                          "layer2_inside": inside, "other_inside": other, "foundation_plan_below": fp_hits}

    # ---- B. OWN-018 / engine cell 49a7dae5: the diagonal band stub BAND0038 (faces 181 + the face OWN-018 already has)
    e181 = db["181"]
    s, t = tuple(e181.dxf.start)[:2], tuple(e181.dxf.end)[:2]
    L = math.dist(s, t)
    u = ((t[0] - s[0]) / L, (t[1] - s[1]) / L)
    g18 = F["OWN-018"]
    gap = Point(t).distance(g18.exterior)
    ext = LineString([(s[0] - u[0] * 1000, s[1] - u[1] * 1000), (t[0] + u[0] * 1000, t[1] + u[1] * 1000)])
    pieces = sorted(split(g18, ext).geoms, key=lambda p: p.area)
    strip_a, panel_a = pieces[0], pieces[1]
    # alternative closure: the band stops square at the end of 181 (perpendicular through its end point)
    perp = LineString([(t[0] + u[1] * 1000, t[1] - u[0] * 1000), (t[0] - u[1] * 1000, t[1] + u[0] * 1000)])
    cut = [p for p in split(strip_a, perp).geoms]
    notch = min(cut, key=lambda p: p.area) if len(cut) == 2 else None
    face_len = []
    for h in own["OWN-018"]["edge_handles"]:
        en = db[h]
        if en.dxftype() == "LINE":
            a, bb = tuple(en.dxf.start)[:2], tuple(en.dxf.end)[:2]
            if abs(abs(a[0] - bb[0]) - abs(a[1] - bb[1])) < 2 and math.dist(a, bb) > 100:
                face_len.append({"handle": h, "length_m": round(math.dist(a, bb) / 1e3, 4)})
    res["f18"] = {"face": "OWN-018", "own_m2": round(g18.area / 1e6, 6), "face_181_length_m": round(L / 1e3, 4),
                  "face_181_gap_to_band_face_m": round(gap / 1e3, 4), "parallel_face": face_len,
                  "strip_closed_to_face_m2": round(strip_a.area / 1e6, 6), "panel_closed_m2": round(panel_a.area / 1e6, 6),
                  "strip_square_end_m2": round((strip_a.area - (notch.area if notch else 0)) / 1e6, 6)}
    # band width between 181 and its parallel face: |delta(y - x)| / sqrt2
    pa = [db[x["handle"]] for x in face_len if x["handle"] != "181"][0]
    c181 = s[1] - s[0]
    cpa = pa.dxf.start[1] - pa.dxf.start[0]
    res["f18"]["band_width_m"] = round(abs(c181 - cpa) / math.sqrt(2) / 1e3, 4)

    # ---- C. OWN-006 against the true arc 158 (ring outer face), split by the band faces 177 / 7CD that end on it
    a158 = db["158"]
    c, r = a158.dxf.center, a158.dxf.radius
    n = 40000
    disk = Polygon([(c.x + r * math.cos(2 * math.pi * i / n), c.y + r * math.sin(2 * math.pi * i / n)) for i in range(n)])
    g6 = F["OWN-006"].difference(disk)

    def extl(h, d=50.0):
        en = db[h]
        a, bb = tuple(en.dxf.start)[:2], tuple(en.dxf.end)[:2]
        ll = math.dist(a, bb)
        w = ((bb[0] - a[0]) / ll, (bb[1] - a[1]) / ll)
        return LineString([(a[0] - w[0] * d, a[1] - w[1] * d), (bb[0] + w[0] * d, bb[1] + w[1] * d)])

    parts6 = [g6]
    for h in ("177", "7CD"):
        nxt = []
        for p in parts6:
            nxt += list(split(p, extl(h)).geoms)
        parts6 = nxt
    parts6 = sorted(parts6, key=lambda p: -p.area)
    ends = {h: round(abs(math.dist(tuple(db[h].dxf.end)[:2], (c.x, c.y)) - r), 3) for h in ("177", "7CD")}
    res["court"] = {"face": "OWN-006", "own_48chord_m2": round(F["OWN-006"].area / 1e6, 6),
                    "own_true_arc_m2": round(g6.area / 1e6, 6),
                    "pieces_true_arc_m2": [round(p.area / 1e6, 6) for p in parts6],
                    "band_faces_end_on_arc158_mm": ends,
                    "band_width_m": round(abs(db["177"].dxf.start[1] - db["7CD"].dxf.start[1]) / 1e3, 4)}

    # ---- D. lift-side panels OWN-022 / OWN-025 (closed by drawn lines; no arc)
    res["lift"] = {k: {"own_m2": round(F[k].area / 1e6, 6), "edge_handles": own[k]["edge_handles"]}
                   for k in ("OWN-022", "OWN-025")}

    # ---- E. the drawn network with true arcs (the 48-chord polygons of T-391 differ by the chord segments)
    segs = {}
    for h in ("139", "13A", "157", "158"):
        en = db[h]
        span = math.radians((en.dxf.end_angle - en.dxf.start_angle) % 360)
        th = span / 48
        segs[h] = en.dxf.radius ** 2 / 2 * (th - math.sin(th)) * 48 / 1e6
    net48 = unary_union(list(F.values())).area / 1e6
    res["network"] = {"own_48chord_m2": round(net48, 6), "chord_segments_m2": {k: round(v, 6) for k, v in segs.items()}}
    # only arc 139 (annex corner, the network inside the circle) is on the network's outer boundary: its chords lose
    # the segments; 13A, 157 (ring / pool piece) and 158 (ring / panels) lie between two network faces (total unchanged)
    inner = {}
    for h in ("139", "13A", "157", "158"):
        en = db[h]
        ring = Point(en.dxf.center.x, en.dxf.center.y).buffer(en.dxf.radius + 20).difference(
            Point(en.dxf.center.x, en.dxf.center.y).buffer(en.dxf.radius - 20))
        inner[h] = sorted({k for k, f in F.items() if f.intersection(ring).area > 1e3})
    res["network"]["faces_along_arc"] = inner
    res["network"]["own_true_arc_m2"] = round(net48 + segs["139"], 6)
    # outline offset by the printed blinding / footing projection 0.10 (ST p.13, T-347): mitred corners
    res["network"]["offset_0p10_m2"] = round(unary_union(list(F.values())).buffer(100, join_style=2).area / 1e6, 6)
    return res


def area_table_constructions():
    """ARCH p.1 GROUND FLOOR AREA PLAN 1:200 printed pieces (municipal area table, Drive 'Alsenan chalet project',
    Alsenan_Architectural_P7757_Pages_01-02 p.1), their printed products to 0.01 m2."""
    return {"1": 220.99, "2": 18.08, "3": 51.83, "4": 23.76, "5": 4.87, "6": 0.46}


def build(meas, other_area=None):
    gs, gb = engine_lines()
    sp = meas["stair_panel"]
    f18, court, lift, net = meas["f18"], meas["court"], meas["lift"], meas["network"]
    eng = {k: gs[v]["dimensions"]["area_m2"] for k, v in CELLS.items() if v in gs}
    eng_f18 = gs[CELLS["f18"]]["measured_net"] / T_SLAB
    eng_cn = gs[CELLS["court_n"]]["measured_net"] / T_SLAB
    eng_cs = gs[CELLS["court_s"]]["measured_net"] / T_SLAB
    eng_la = gs[CELLS["lift_a"]]["measured_net"] / T_SLAB
    eng_lb = gs[CELLS["lift_b"]]["measured_net"] / T_SLAB
    band = gb[BAND0038]

    stair = R.stair_zone_panel(area_m2=sp["area_m2"], closed_by_bands=True,
                               stair_linetypes=[x["linetype"] for x in sp["layer2_inside"]],
                               void_or_pit_drawn=any(x["layer"] in ("S-BW", "VOID", "S-OPENING") for x in sp["other_inside"]),
                               stair_base_drawn=any(not x["column_outlines_inside"] for x in sp["foundation_plan_below"]),
                               section_replaces_slab=False, floored_above=True)

    # GS-FACES: sub-parts on the T-391 own figures (OWN-018 3.8344, OWN-006 13.4514, OWN-022 2.7212, OWN-025 2.2534)
    subs_faces = [
        {"id": "F-018-STRIP", "m3": -f18["strip_closed_to_face_m2"] * T_SLAB, "verdict": "ENGINE_RIGHT",
         "cause": "drawn 0.30 diagonal band stub (faces 181 + the panel's diagonal face) the T-391 partition merged into "
                  "OWN-018 because face 181 stops short of the band face; the beam owns it, his plate covers it"},
        {"id": "F-018-ENDS", "m3": (eng_f18 - f18["panel_closed_m2"]) * T_SLAB, "verdict": "ENGINE_WRONG",
         "cause": "engine deducts the stub as short face x 0.30, leaving the two 45 degree end triangles in the slab face",
         "correction_owner": "lane I (Worker 3): stub BAND0038 net plan to the drawn faces, slab face 49a7dae5 to the "
                             "closed panel"},
        {"id": "F-006-STRIP", "m3": -court["pieces_true_arc_m2"][2] * T_SLAB, "verdict": "ENGINE_RIGHT",
         "cause": "drawn band 177 / 7CD (C9 to the ring) whose faces end on arc 158; the T-391 48-chord arc did not node "
                  "them, so the strip was read as panel; the engine stops the panels at the band faces"},
        {"id": "F-006-CHORD", "m3": -(court["own_48chord_m2"] - court["own_true_arc_m2"]) * T_SLAB,
         "verdict": "ENGINE_RIGHT",
         "cause": "own-read chord segments of arc 158 counted in OWN-006; the engine panels equal the true-arc panels"},
        {"id": "F-LIFT", "m3": ((eng_la - lift["OWN-022"]["own_m2"]) + (eng_lb - lift["OWN-025"]["own_m2"])) * T_SLAB,
         "verdict": "UNRESOLVED",
         "cause": "two panels against the lift ring 7C2 and the oblique band 17E / 17F: both own faces are closed by "
                  "drawn lines; the engine cell outlines are not in any committed output"},
    ]
    rnd = PARTS["GS-FACES"] - sum(x["m3"] for x in subs_faces)
    subs_faces.append({"id": "F-ROUND", "m3": rnd, "verdict": "AGREE",
                       "cause": "T-391 own areas carried to 0.0001 m2 (exact figures above)"})
    for x in subs_faces:
        x["m3"] = round(x["m3"], 7)

    beyond_exact = None
    tests = []
    if other_area is not None:
        tests = R.bare_area_tests(other_area, {
            "drawn network, 48-chord arcs (T-391)": net["own_48chord_m2"],
            "drawn network, true arcs": net["own_true_arc_m2"],
            "drawn network outline offset by the printed projection 0.10": net["offset_0p10_m2"],
            **{f"ARCH p.1 area-table pieces {'+'.join(k)}": v for k, v in R.subset_sums(area_table_constructions()).items()},
        }, precision_m2=0.1)
    subs_beyond = [
        {"id": "B-HIS", "m3": PARTS["GS-BEYOND-NETWORK"] - (net["own_48chord_m2"] - net["own_true_arc_m2"]) * T_SLAB,
         "verdict": "UNRESOLVED",
         "cause": "his bare plate area beyond the drawn network (true arcs): no construction tried reproduces it"},
        {"id": "B-CHORD", "m3": (net["own_48chord_m2"] - net["own_true_arc_m2"]) * T_SLAB, "verdict": "ENGINE_RIGHT",
         "cause": "own-read chord segments of the network boundary arc 139 left out of the T-391 network"},
    ]
    for x in subs_beyond:
        x["m3"] = round(x["m3"], 7)
    subs_stair = [{"id": "S-PANEL", "m3": PARTS["GS-STAIR-ZONE"], "verdict": "ENGINE_WRONG",
                   "cause": "slab on grade under the GF curved flight foot dropped whole as a stair zone; the flight is "
                            "drawn above it (hidden), founded on a ground beam, with no void, pit or stair base",
                   "correction_owner": "lane I (Worker 3): a GS line for cell 4df8fcd9 at the drawn panel x T"}]
    out = {"schema": "T436_SUMMARY_V1", "t428_parts_m3": PARTS, "stair_zone": {**sp, "class": stair},
           "faces": {"f18": f18, "court": court, "lift": lift,
                     "engine_m2": {"49a7dae5": round(eng_f18, 6), "d74f3fe2": round(eng_cn, 6), "0caa2bd2": round(eng_cs, 6),
                                   "3f7728a8": round(eng_la, 6), "c1b4b440": round(eng_lb, 6)},
                     "band0038": {"line": BAND0038, "net_plan_m2": band["dimensions"]["net_plan_m2"],
                                  "value_m3": round(band["measured_net"], 6),
                                  "length_m": band["dimensions"]["length_m"]}},
           "network": net,
           "subparts": {"GS-STAIR-ZONE": subs_stair, "GS-BEYOND-NETWORK": subs_beyond, "GS-FACES": subs_faces},
           "bare_area_misfits_m2": [{"construction": t["construction"], "misfit_m2": t["misfit_m2"],
                                     "reproduces": t["reproduces"]} for t in tests[:8]],
           "bare_area_constructions_tried": len(tests)}
    R.check_split(out["subparts"], PARTS)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dxf")
    ap.add_argument("--freelancer")
    ap.add_argument("--out")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    t428_parts()
    if a.check:
        d = json.loads(SUMMARY.read_text(encoding="utf-8"))
        R.check_split(d["subparts"], PARTS)
        print("REPRODUCED: sub-parts re-add to the T-428 parts", json.dumps(R.totals(d["subparts"]), sort_keys=True))
        return d
    meas = measure(a.dxf)
    other = None
    if a.freelancer:
        import openpyxl  # private step only
        ws = openpyxl.load_workbook(a.freelancer, data_only=True).worksheets[2]
        other = float(ws.cell(11, 2).value)
    out = build(meas, other)
    if a.out:
        o = Path(a.out).resolve()
        if ROOT.resolve() in o.parents or o == ROOT.resolve():
            raise SystemExit("--out inside the repository: the freelancer's values stay in .work/private")
        o.mkdir(parents=True, exist_ok=True)
        (o / "T436_PRIVATE.json").write_text(json.dumps({"other_area_m2": other, **out}, indent=1, sort_keys=True) + "\n",
                                             encoding="utf-8")
    if a.write:
        SUMMARY.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"totals": R.totals(out["subparts"]), "stair_class": out["stair_zone"]["class"],
                      "f18": out["faces"]["f18"], "court": out["faces"]["court"], "network": out["network"]}, indent=1))
    return out


if __name__ == "__main__":
    main()
