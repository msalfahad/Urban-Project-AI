"""T-674 run on the private development-villa copy (writes VALUES, ids and DXF handles only; no coordinates, no names).

    .work/venv/bin/python -I research/agents_t674/t674_alsenan.py .work/private/ST7757_dxf.dxf \
        --out research/agents_t674/summary_t674.json

1. Engine side: route G (engine.source.generic_route, URBAN_M8_GENERIC_CONVENTIONS_V6, no profile: the run that names
   the V3.0 ground-slab cells SITE-...) on the structural DXF; ground sheet SH08 faces, bands and the member-overlap
   deduction of each target cell (the M4 rule of generic_route._slab_m4, re-computed per member).
2. Own side: the GROUND BEAMS PLAN frame (T-141 box, as T-391) noded on layer-1 LINE / ARC, S-COL.BON and S-BW,
   with every line end that lies on a true arc (R-T674-2, 0.5 mm) inserted as an arc vertex before polygonising.
3. Per target line: engine m2, own m2, the member each deduction rests on, the correction (t674_rules), m3 at the
   printed T = 0.10 (T-206 DRAWING-CONFIRMED 'T=10cm').
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "research" / "agents_t391"))
import t674_rules as R  # noqa: E402

DXF_SHA = "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079"
T_M = 0.10
TARGETS = {   # V3.0.57 .. V3.0.64 line id -> route-G cell
    "L-69527cb9affdad474268": "SITE-49a7dae5c139aebb",
    "L-8b681fdaa3b3910b2b7b": "SITE-3f7728a83b30ec14",
    "L-f192ff5f4962efa8d08f": "SITE-c1b4b440fb6ecf4c",
    "L-1031c9be9aaae364fef4": "SITE-d74f3fe29b88467a",
    "L-5e881fd31885949d4e66": "SITE-0caa2bd2c0478041",
}
CANDIDATE_M3 = {"L-69527cb9affdad474268": 0.359768, "L-8b681fdaa3b3910b2b7b": 0.261557,
                "L-f192ff5f4962efa8d08f": 0.22447, "L-1031c9be9aaae364fef4": 1.090505,
                "L-5e881fd31885949d4e66": 0.20502}     # research/agents_t507/out/LINE_INDEX_V3_0_57.json (unchanged since)
CHECKER_OWN_M3 = {"L-69527cb9affdad474268": 0.383438}  # T-180 P18 (SCOREBOARD 2026-11-10 08:59): the other 4 as sums


def engine_side(dxf):
    from engine.source import generic_route as GR
    from engine.source import member_detection as MD
    from tools import urban_intake as UI
    generic = json.loads((ROOT / "engine/profiles/URBAN_M8_GENERIC_CONVENTIONS_V6.json").read_text(encoding="utf-8"))
    conv = GR.merge_conventions(generic, None, {})
    opt = GR.detect_options(conv)
    intake = UI.read(dxf)
    if opt.get("local_origin"):
        intake = GR.to_local_origin(intake)
    D = GR.detect(intake, typical_widths_m=GR.typical_gb_widths(conv), options=opt)
    rec = D["sheets"]["SH08"]
    u = D["unit_m"]
    bands = [b for b in rec.get("bands", []) if b["kind"] == "STRAIGHT"]
    cols = rec.get("slab_column_boxes", rec.get("column_boxes", []))
    faces = {f["face_id"]: f for f in rec["slab"]["faces"]}
    return D, rec, u, bands, cols, faces


def own_partition(dxf):
    import ezdxf
    from ezdxf import bbox as BB
    from shapely.geometry import LineString, Polygon
    from shapely.ops import polygonize, unary_union
    import t391_extract as X
    doc = ezdxf.readfile(dxf)
    lines, arcs, polys = [], [], []
    for e in doc.modelspace():
        try:
            layer = e.dxf.layer
            b = BB.extents([e])
        except Exception:
            continue
        if not b.has_data or not (X.GBP[0] <= b.center.x <= X.GBP[2] and X.GBP[1] <= b.center.y <= X.GBP[3]):
            continue
        t = e.dxftype()
        if layer in ("1", "S-COL.BON") and t == "LINE":
            lines.append((e.dxf.handle, (tuple(e.dxf.start)[:2], tuple(e.dxf.end)[:2])))
        elif layer == "1" and t == "ARC":
            arcs.append((e.dxf.handle, e))
        elif layer in ("S-COL.BON", "S-BW") and t == "LWPOLYLINE":
            p = [tuple(v)[:2] for v in e.get_points("xy")]
            if e.closed:
                p = p + [p[0]]
            polys.append((e.dxf.handle, p))
    noded = []
    geoms = [LineString(p) for _, p in lines] + [LineString(p) for _, p in polys]
    for h, a in arcs:
        c, r = (a.dxf.center.x, a.dxf.center.y), a.dxf.radius
        ends = [pt for _, (p, q) in lines for pt in (p, q)]
        # R-T674-2 in drawing units (mm): node a line end within 0.5 mm of the true arc
        pts, nd = R.arc_points(c, r, a.dxf.start_angle, a.dxf.end_angle, 256, ends, tol=0.5)
        noded += [{"arc": h, "line": next(lh for lh, (p, q) in lines if e in (p, q))} for e in nd]
        geoms.append(LineString(pts))
    faces = [f for f in polygonize(unary_union(geoms)) if f.area > 1.0]
    return faces, noded, {h: p for h, p in lines}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("dxf")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    sha = hashlib.sha256(Path(a.dxf).read_bytes()).hexdigest()
    if sha != DXF_SHA:
        raise SystemExit(f"unexpected drawing sha {sha[:8]}")
    from shapely.geometry import Polygon
    from engine.source import member_detection as MD
    D, rec, u, bands, cols, efaces = engine_side(a.dxf)
    own, noded, L = own_partition(a.dxf)
    # the route-G sheet is drawn in the same units, translated: recover the translation from one drawn edge pair
    ref = efaces[TARGETS["L-69527cb9affdad474268"]]["polygon"]
    xs = min(x for x, _ in ref) - L["176"][0][0]
    ys = min(y for _, y in ref) - L["180D"][0][1]
    out = {"schema": "T674_SUMMARY_V1", "drawing_sha8": sha[:8], "t_m": T_M, "noded_line_ends_on_arcs": len(noded),
           "own_faces": len(own), "own_network_m2": round(sum(f.area for f in own) / 1e6, 4), "lines": {}}
    for lid, cid in TARGETS.items():
        f = efaces[cid]
        P = Polygon([(x - xs, y - ys) for x, y in f["polygon"]]).buffer(0)
        hits = sorted(((g.intersection(P).area, g) for g in own), key=lambda t: -t[0])
        best = hits[0][1]
        poly = f["polygon"]
        members = []
        for b in bands:
            ov = MD.overlap_area(poly, b["polygon"]) * u * u
            if ov > 1e-4:
                members.append({"member": b["band_id"], "kind": "BAND", "area_m2": round(ov, 6),
                                "drawn_faces": list(b.get("handles") or [])})
        for c in cols:
            ov = MD.overlap_area(poly, MD.box_poly(c)) * u * u
            if ov > 1e-4:
                members.append({"member": "COLUMN_BOX", "kind": "COLUMN", "area_m2": round(ov, 6), "drawn_faces": []})
        out["lines"][lid] = {"cell": cid, "engine_gross_m2": round(f["area_m2"], 6), "members": members,
                             "own_face_m2": round(best.area / 1e6, 6), "candidate_m3": CANDIDATE_M3[lid]}
    # --- L-69527cb9: oblique ground beam 180 / 181 (layer 1, BAND0038) framing into 176 and 180D
    ln = out["lines"]["L-69527cb9affdad474268"]
    m = lambda p: (p[0] / 1000, p[1] / 1000)                                            # noqa: E731
    seg = lambda h: (m(L[h][0]), m(L[h][1]))                                            # noqa: E731
    _, strip = R.strip_to_carriers(seg("180"), seg("181"), seg("176"), seg("180D"))
    f181 = min(L["181"], key=lambda p: p[1])
    ln.update({"deduction_m2": R.deduction_basis([dict(x) for x in ln["members"]]),
               "member_line": "L-970bac563cbcd69e2a30 (P-C:GROUND_BEAMS:GROUND:BAND0038, HELD)",
               "strip_to_carriers_m2": strip, "face_181_gap_to_180D_m": round(R.face_gap(m(f181), seg("180D")), 4)})
    ln["corrected_m2"] = round(ln["engine_gross_m2"] - strip, 6)   # engine cell = own face to 0.0001 m2
    # --- the court pair: one drawn beam 177 / 7CD between them (BAND0008.2), ends noded on arc 158
    pair = ["L-1031c9be9aaae364fef4", "L-5e881fd31885949d4e66"]
    sb = next(x for x in efaces.values() if x["class"] == "BEAM" and
              any(MD.overlap_area(x["polygon"], b["polygon"]) > 0 for b in bands if b["band_id"] == "BAND0008.2"))
    out["court_pair"] = {"split_on": "layer-1 lines 177 / 7CD (beam band BAND0008.2, GB line L-d53e5eb08e2c6c668254 "
                                     "HELD)", "ends_on_arc_158": sorted({x["line"] for x in noded if x["arc"] == "158"}),
                         "engine_strip_face_m2": round(sb["area_m2"], 6)}
    for lid in pair:   # the engine cell IS the drawn panel (arc 158 followed): AGREE within the arc flattening
        ln = out["lines"][lid]
        ln["own_minus_engine_m2"] = round(ln["own_face_m2"] - ln["engine_gross_m2"], 6)
        if abs(ln["own_minus_engine_m2"]) > 0.001:
            raise SystemExit(f"{lid}: own face differs from the engine cell by {ln['own_minus_engine_m2']} m2")
        ln["corrected_m2"] = round(ln["engine_gross_m2"], 6)
    # --- lift side: the junction-gap face over the drawn ring 7C2 / column 1EF
    jg = [x for x in efaces.values() if x["class"] == "JUNCTION_GAP"]
    out["junction_gap_faces_m2"] = sorted(round(x["area_m2"], 6) for x in jg)
    for lid in ("L-8b681fdaa3b3910b2b7b", "L-f192ff5f4962efa8d08f"):
        ln = out["lines"][lid]
        c = R.junction_clip(ln["own_face_m2"], ln["engine_gross_m2"], support_drawn=True)
        ln.update({"junction_returned_m2": c["returned_m2"], "corrected_m2": c["corrected_m2"],
                   "support": "S-BW ring 7C2 outer face + S-COL.BON 1EF"})
    tot_c = tot_e = 0.0
    for lid, ln in out["lines"].items():
        ln["corrected_m3"] = R.volume(ln["corrected_m2"], T_M)
        ln["delta_m3"] = round(ln["corrected_m3"] - ln["candidate_m3"], 6)
        tot_c += ln["corrected_m3"]
        tot_e += ln["candidate_m3"]
    out["five_lines"] = {"candidate_m3": round(tot_e, 6), "corrected_m3": round(tot_c, 6),
                         "delta_m3": round(tot_c - tot_e, 6)}
    Path(a.out).write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(out["five_lines"]), {k: (v["corrected_m2"], v["delta_m3"]) for k, v in out["lines"].items()})


if __name__ == "__main__":
    main()
