"""T-141 Alsenan check: GROUND_SYSTEM_SPANS_V2 on the structural DXF, span by span against the T-138 r2 hand ledger
and the frozen S5 register.

    .venv/bin/python -I research/agents_t141/run_t141_alsenan.py <structural.dxf> [--out <dir outside the clone>]

Inputs read from the drawing (nothing typed): ground-beam bands = layer "1" face pairs on the GROUND BEAMS PLAN sheet
(engine ground_beam_network.pair_straight, the same pairing S5 used, width 300 +- 12 mm); columns = every S-COL.BON
outline on that sheet (closed / open polylines and line rectangles); footings = every S-FOOTINGS outline on the
FOUNDATION PLAN sheet (polylines, "F" block inserts, line rectangles), moved onto the ground-beam sheet by the offset of
the two sheet frames (the frames are the same size; the offset is checked against the plot boundary polylines); straps =
the strap edge lines the frozen S5 strap register names (its SOURCE_HANDLES), measured on the foundation plan.
The sheet frames are the frozen structural census frames (alsenan_structural_s1 Source). Length classes = the p.13
titles "more than 5 m", "less than 5 m", "less than 2.5 m" (structural PDF p.13).

Writes T141_SPANS.csv / T141_STRAPS.csv (ids and lengths only, no coordinates) next to this file, or into --out.
Prints the comparison and exits 1 if a released span differs from the hand ledger by more than 5 mm without a named
explanation in EXPLAINED below.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)

from engine.source import ground_beam_network as GN  # noqa: E402
from engine.source import ground_system_spans_v2 as V2  # noqa: E402

DXF_SHA = "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079"
# frozen sheet frames of ST7757 (research/external_engine_lab/alsenan_structural_s1.py Source(...).sheets[...]["frame"])
GBP = (78929.89653886131, 29036.09943562183, 114124.2067251332, 57066.43175431111)
FP = (117654.3026476346, 29036.09943562183, 152848.6128339064, 57066.43175431111)
CLASSES = [{"detail_id": "P13-GB-GT5M", "op": ">", "limit_m": 5.0},
           {"detail_id": "P13-GB-LT5M", "op": "<", "limit_m": 5.0},
           {"detail_id": "P13-GB-LT2_5M", "op": "<", "limit_m": 2.5}]
S5_GB = os.path.join(ROOT, "research/alsenan_ground_system_rebar_s5/GROUND_BEAM_REBAR_SUMMARY.csv")
S5_STRAPS = os.path.join(ROOT, "research/pre_s5_ground_system_readiness/03_STRAP_OCCURRENCE_REGISTER.csv")
T138 = os.path.join(ROOT, "research/agents_t138/t138_hand_ledger.py")

# a released span may differ from the hand ledger by more than 5 mm only with a reason written here
EXPLAINED = {
    "177+7CD#1": "V2 HELD (GAP_TO_COLUMN): the band is drawn to x 100,718, 50 mm beside column 1EC (x 100,518 .. 100,768, "
                 "its edge 50 mm off the band face); the hand took the column face (4.97 m, < 5 m), the drawn band end "
                 "gives 5.02 m (> 5 m) and the footing face 3.52 m: the p.13 section changes with the reading, so V2 "
                 "holds it with the three candidates (designer question, S5 Q-G1 / D-34)",
}


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def inb(x, y, B):
    return B[0] <= x <= B[2] and B[1] <= y <= B[3]


def outlines(msp, layer, box, *, blocks=(), shift=0.0):
    """Closed outlines on one layer inside a sheet box: polylines (an open one is closed by its last -> first chord,
    which is where a strap crosses the footing outline), block inserts named in `blocks` (exploded) and rectangles of
    loose lines (polygonized). Returns [(id, polygon, handles)], x shifted by -shift."""
    from shapely.geometry import LineString
    from shapely.ops import polygonize
    out, loose = [], []
    for e in msp:
        t = e.dxftype()
        if t == "INSERT" and e.dxf.name in blocks and inb(*tuple(e.dxf.insert)[:2], box):
            for v in e.virtual_entities():
                if v.dxftype() == "LWPOLYLINE" and v.dxf.layer == layer:
                    out.append((f"{e.dxf.handle}:{e.dxf.name}", [tuple(p[:2]) for p in v.get_points()],
                                [e.dxf.handle]))
            continue
        if t not in ("LINE", "LWPOLYLINE") or e.dxf.layer != layer:
            continue
        if t == "LWPOLYLINE":
            pts = [tuple(p[:2]) for p in e.get_points()]
            if inb(*pts[0], box) and len(pts) >= 3:
                out.append((e.dxf.handle, pts, [e.dxf.handle]))
        elif inb(*tuple(e.dxf.start)[:2], box):
            loose.append((e.dxf.handle, LineString([tuple(e.dxf.start)[:2], tuple(e.dxf.end)[:2]])))
    from shapely.geometry import Polygon
    for g in polygonize([ls for _, ls in loose]):
        if g.area < 0.5e6 or len(g.exterior.coords) != 5:     # rectangles of four lines, >= 0.5 m2 (strap hatching out)
            continue
        hs = sorted(h for h, ls in loose if ls.distance(g.exterior) < 1.0 and ls.length > 1.0 and
                    g.exterior.buffer(1.0).contains(ls))
        out.append(("+".join(hs), list(g.exterior.coords)[:-1], hs))
    res = []
    for i, pts, hs in out:
        poly = [(x - shift, y) for x, y in pts]
        if Polygon(poly).area <= 0:
            continue
        res.append((i, poly, hs))
    return res


def load_hand():
    spec = importlib.util.spec_from_file_location("t138_hand_ledger", T138)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dxf")
    ap.add_argument("--out", default=HERE)
    a = ap.parse_args()
    import ezdxf
    if sha(a.dxf) != DXF_SHA:
        raise SystemExit(f"structural DXF sha mismatch (expected {DXF_SHA})")
    doc = ezdxf.readfile(a.dxf)
    msp = doc.modelspace()
    shift = FP[0] - GBP[0]
    if abs((FP[2] - FP[0]) - (GBP[2] - GBP[0])) > 1e-6 or abs(FP[1] - GBP[1]) > 1e-6:
        raise SystemExit("sheet frames differ in size: no frame offset")
    # independent check of the offset: the plot boundary polylines (S-BOUN) on both sheets
    bb = {}
    for e in msp.query("LWPOLYLINE[layer=='S-BOUN']"):
        pts = [tuple(p[:2]) for p in e.get_points()]
        for key, B in (("GBP", GBP), ("FP", FP)):
            if inb(*pts[0], B):
                bb.setdefault(key, []).append(min(x for x, _ in pts))
    if not bb.get("GBP") or not bb.get("FP") or abs(min(bb["FP"]) - min(bb["GBP"]) - shift) > 1.0:
        raise SystemExit(f"plot boundary offset does not match the frame offset {shift:.1f}: {bb}")

    # ---- bands (same pairing as S5) and arcs (listed, not measured)
    faces = [{"handle": e.dxf.handle, "layer": e.dxf.layer, "p0": tuple(e.dxf.start)[:2], "p1": tuple(e.dxf.end)[:2]}
             for e in msp.query("LINE[layer=='1']") if inb(*tuple(e.dxf.start)[:2], GBP)]
    res = GN.pair_straight(faces, width=300.0, tol=12.0, admitted_layers={"1"})
    bands = [{"band_id": "+".join(b["handles"]), "u": b["u"], "lo_off": b["lo_off"], "hi_off": b["hi_off"],
              "t0": b["t0"], "t1": b["t1"], "handles": b["handles"]} for b in res["bands"]]
    arcs = [{"handle": e.dxf.handle, "layer": "1", "cx": e.dxf.center[0], "cy": e.dxf.center[1], "r": e.dxf.radius,
             "a0": e.dxf.start_angle, "a1": e.dxf.end_angle} for e in msp.query("ARC[layer=='1']")
            if inb(e.dxf.center[0], e.dxf.center[1], GBP)]
    ares = GN.pair_arcs(arcs, width=300.0, tol=12.0, admitted_layers={"1"})
    for k, b in enumerate(ares["bands"], start=1):
        bands.append({"band_id": f"ARC:{'+'.join(b['handles'])}/{k}", "u": (1.0, 0.0), "lo_off": 0, "hi_off": 1,
                      "t0": 0, "t1": 1, "handles": b["handles"], "kind": "ARC",
                      "polygon": [tuple(p) for p in b["polygon"]]})

    cols = outlines(msp, "S-COL.BON", GBP)
    feet_fp = outlines(msp, "S-FOOTINGS", FP, blocks=("F",))
    feet_gb = [(i, [(x - shift, y) for x, y in p], h) for i, p, h in feet_fp]
    supports = [{"support_id": "COL:" + i, "kind": "COLUMN", "polygon": p, "handles": h} for i, p, h in cols] + \
               [{"support_id": "FTG:" + i, "kind": "FOOTING", "polygon": p, "handles": h} for i, p, h in feet_gb]
    out = V2.split_ground_beams(bands, supports, units="mm", classes=CLASSES)
    if not out["conservation"]["all_pass"]:
        raise SystemExit(f"conservation failed: {out['conservation']}")

    # ---- footing census check against the frozen S1 footing register (frame-relative bboxes)
    reg = json.load(open(os.path.join(ROOT, "research/alsenan_structural_census_s1/FOOTING_OCCURRENCE_REGISTER.json")))
    got = sorted((round(min(x for x, _ in p) - GBP[0] + shift - shift, 0), round(min(y for _, y in p) - GBP[1], 0))
                 for _, p, _ in feet_gb)
    want = sorted((round(r["outline"]["bbox"][0], 0), round(r["outline"]["bbox"][1], 0)) for r in reg["rows"])
    print(f"footing outlines read {len(feet_gb)}, register {len(want)}, same lower-left corners: {got == want}")

    # ---- founded check: a column that splits a band, is it over a footing on the foundation plan?
    from shapely.geometry import Polygon
    fpolys = [(i, Polygon(p)) for i, p, _ in feet_gb]
    def founded(cid):
        c = next(Polygon(s["polygon"]) for s in supports if s["support_id"] == cid)
        return sorted(i for i, f in fpolys if f.intersection(c).area > 0.5 * c.area)

    # ---- compare with the hand ledger and S5
    H = load_hand()
    s5 = {r["occurrence_id"]: r for r in csv.DictReader(open(S5_GB, encoding="utf-8"))}
    by_band = {}
    for s in out["spans"]:
        by_band.setdefault(s["band_id"], []).append(s)
    hand_by_band, s5_by_band = {}, {}
    for oid, v in H.HAND.items():
        band = H.band_of(oid)
        hand_by_band.setdefault(band, []).append((oid, v))
    for oid, r in s5.items():
        s5_by_band.setdefault(H.band_of(oid), []).append((oid, r))
    rows, bad = [], []
    for band in sorted(set(by_band) | {b.replace("-", "+") for b in hand_by_band if not b.startswith("A-")}):
        key = band.replace("+", "-")
        spans = by_band.get(band, [])
        hand = []
        for oid, v in sorted(hand_by_band.get(key, [])):
            L = v[0]
            if isinstance(L, list):
                hand += [(oid, x) for x in L]
            else:
                hand.append((oid, L))
        s5l = [(oid, float(r["support_face_to_face_run_m"] or "nan"), r["occurrence_state"])
               for oid, r in sorted(s5_by_band.get(key, []))]
        n = max(len(spans), len(hand), len(s5l))
        for i in range(n):
            sp = spans[i] if i < len(spans) else None
            hd = hand[i] if i < len(hand) else (None, None)
            fz = s5l[i] if i < len(s5l) and len(s5l) == len(spans) else None
            v2 = sp["lengths"]["face_to_face_m"] if sp else None
            diff = None if (v2 is None or hd[1] is None) else round(v2 - hd[1], 4)
            note = ""
            if diff is not None and abs(diff) > 0.005:
                note = EXPLAINED.get(sp["span_id"], "UNEXPLAINED")
                if note == "UNEXPLAINED" and sp["status"] == V2.RELEASED:
                    bad.append(sp["span_id"])
            founded_cols = []
            if sp:
                for nd in (sp["start"], sp["end"]):
                    if nd["kind"] == "COLUMN":
                        founded_cols += [f"{r}:{'+'.join(founded(r)) or 'NOT_FOUNDED'}" for r in nd["refs"]]
            rows.append({
                "span_id": sp["span_id"] if sp else f"{band}#-", "hand_occurrence": hd[0] or "",
                "v2_face_to_face_m": v2, "hand_m": hd[1], "diff_v2_minus_hand_m": diff,
                "s5_occurrence": fz[0] if fz else "", "s5_face_to_face_m": fz[1] if fz else "",
                "v2_centreline_m": sp["lengths"]["centreline_m"] if sp else None,
                "v2_status": sp["status"] if sp else "NO_SPAN", "v2_class": "+".join(sp["class_face_to_face"]) if sp
                else "", "class_state": sp["class_state"] if sp else "",
                "start": f"{sp['start']['kind']} {'+'.join(sp['start']['refs'])}" if sp else "",
                "end": f"{sp['end']['kind']} {'+'.join(sp['end']['refs'])}" if sp else "",
                "founded": "; ".join(founded_cols), "flags": " | ".join(sp["flags"] + sp["held_reasons"]) if sp else "",
                "note": note})
    # ---- straps
    sres = []
    for r in csv.DictReader(open(S5_STRAPS, encoding="utf-8")):
        hs = json.loads(r["SOURCE_HANDLES"])[:2]
        edges = []
        for h in hs:
            e = doc.entitydb.get(h)
            edges.append((tuple(e.dxf.start)[:2], tuple(e.dxf.end)[:2]))
        sres.append((r, edges, hs))
    feet_fp_s = [{"support_id": "FTG:" + i, "kind": "FOOTING", "polygon": p, "handles": h} for i, p, h in feet_fp]
    straps = V2.measure_straps([{"strap_id": r["STRAP_OCCURRENCE_ID"], "mark": r["MARK"], "edges": e, "handles": hs}
                                for r, e, hs in sres], feet_fp_s, units="mm")
    srows = []
    for st, (r, _, _) in zip(straps, sres):
        c = st["candidates"]
        hand = H.STRAPS[st["mark"]]["clear"]
        srows.append({"strap_id": st["strap_id"], "mark": st["mark"], "status": st["status"],
                      "axis_face_to_face_m": c.get("axis_face_to_face_m"), "hand_m": hand,
                      "diff_axis_minus_hand_m": None if c.get("axis_face_to_face_m") is None else
                      round(c["axis_face_to_face_m"] - hand, 4),
                      "edge_face_to_face_m": json.dumps(c.get("edge_face_to_face_m")),
                      "projection_gap_m": c.get("projection_gap_m"), "s5_clear_m": float(r["CLEAR_CONCRETE_LENGTH_M"]),
                      "footing_centre_to_centre_m": c.get("footing_centre_to_centre_m"),
                      "s5_column_centre_to_centre_m": float(r["CENTERLINE_SUPPORT_TO_SUPPORT_M"]),
                      "footings": f"{st.get('start_footing')} / {st.get('end_footing')}", "width_m": st["width_m"],
                      "flags": " | ".join(st["flags"] + st["held_reasons"])})
    # ---- kg effect on the hand ledger's released longitudinal rows (same bars, V2 length)
    v2_by_member = {}
    for r in rows:
        if r["hand_occurrence"] and r["v2_face_to_face_m"] is not None:
            v2_by_member.setdefault(r["hand_occurrence"], []).append((r["v2_face_to_face_m"], r["v2_status"]))
    kg_hand = kg_v2 = kg_through = 0.0
    held_members = []
    for m in csv.DictReader(open(os.path.join(ROOT, "research/agents_t138/T138_MEMBERS.csv"), encoding="utf-8")):
        if m["family"] != "GROUND_BEAM" or not m["status"].startswith("RELEASED") or not m["length_m"]:
            continue
        n, d = int(m["count"]), int(m["dia_mm"])
        parts = v2_by_member.get(m["member"], [])
        if m["member"].startswith("through"):
            kg_through += float(m["kg"])          # bars through interior columns: V2 lists the columns, no kg
            continue
        if not parts or any(st != V2.RELEASED for _, st in parts):
            held_members.append((m["member"], float(m["kg"])))
            continue
        kg_hand += float(m["kg"])
        kg_v2 += n * sum(L for L, _ in parts) * H.kgm(d)
    s5_rel = sum(float(r["known_kg"]) for r in s5.values() if r["occurrence_state"] == "LOWER_BOUND")
    hm = {}
    for mm, kg in held_members:
        hm[mm] = hm.get(mm, 0.0) + kg
    print(f"ground-beam longitudinal steel, the hand ledger's released spans that V2 releases: hand {kg_hand:.2f} kg, "
          f"same bars on V2 lengths {kg_v2:.2f} kg ({kg_v2 - kg_hand:+.2f}); hand-released spans V2 does not release: "
          + ", ".join(f"{k_} {v:.2f} kg" for k_, v in sorted(hm.items())) +
          f"; bars through interior columns (hand) {kg_through:.2f} kg; frozen S5 released {s5_rel:.2f} kg")
    os.makedirs(a.out, exist_ok=True)
    for name, rr in (("T141_SPANS.csv", rows), ("T141_STRAPS.csv", srows)):
        with open(os.path.join(a.out, name), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rr[0]), lineterminator="\n")
            w.writeheader()
            w.writerows(rr)
    rel = [s for s in out["spans"] if s["status"] == V2.RELEASED]
    print(f"bands {len(out['bands'])} straight + {len(out['unsupported'])} arc (unsupported); spans {len(out['spans'])}"
          f" ({len(rel)} released, {len(out['spans']) - len(rel)} held); columns {len(cols)}; footings {len(feet_fp)}")
    for r in rows:
        print(f"{r['span_id']:<22} v2 {r['v2_face_to_face_m']!s:>7} hand {r['hand_m']!s:>6} d {r['diff_v2_minus_hand_m']!s:>7}"
              f" s5 {r['s5_face_to_face_m']!s:>6} {r['v2_status']:<8} {r['v2_class']:<28} {r['start']} -> {r['end']}"
              f" {r['note']} {r['flags'][:120]}")
    for r in srows:
        print(r)
    if bad:
        print("UNEXPLAINED released differences > 5 mm:", bad)
        sys.exit(1)


if __name__ == "__main__":
    main()
