"""BENCHMARK RUNNER - Phase 2B-5 Stages D / F: every room reader on every benchmark case, against the hand truth.

    python3 -s tests/m9_p2b5_bench/bench_run.py --out research/urban_m9_p2b5/bench [--work DIR]

Methods: the native engine (layer roles inferred, and declared), the independent DXF reader (ezdxf + shapely), the
raster prototype (10 mm / px render; a 25 mm / px degraded scan), the vector-PDF prototype, and the CAD MCP servers
studied earlier (NOT_AVAILABLE: none is connected in this session; their adapters plug in here). Metrics per case:
room recall, false rooms, IoU, area and perimeter error, boundary (Hausdorff) and corner error, openings found by kind
and width, adjacency, the raster scale check, runtime. The CAD-encoding cases (bench_cases.ENCODED: nested and
non-uniform blocks, metres, polylines, Arabic words with DIMENSIONs, a window block, an XREF) run through the DXF
readers only - their picture is the base case's; a case whose truth is a refusal (expect_state) is scored on whether
the reader refused, not on rooms. Synthetic drawings only."""

from __future__ import annotations

import argparse
import json
import math
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import bench_cases as BC                                      # noqa: E402
import bench_drawings as BD                                   # noqa: E402
import hybrid as HY                                           # noqa: E402
import native_adapter as NA                                   # noqa: E402
import ref_reader as RR                                       # noqa: E402
import vision as VI                                           # noqa: E402

MCP_ADAPTERS = {"U-C4N/Autocad-MCP": "NOT_AVAILABLE: not connected in this session",
                "beiming183-cloud/AutoCAD-MCP": "NOT_AVAILABLE: not connected in this session",
                "christiannp/autocad": "NOT_AVAILABLE: repository inaccessible (earlier audit)"}
METHODS = ("NATIVE_AUTO", "NATIVE_DECLARED", "REF_DXF", "RASTER_10MM", "SCAN_25MM", "PDF_VECTOR")
DXF_METHODS = METHODS[:3]
ALL_CASES = BC.CASES + BC.ENCODED


def methods_for(case):
    return DXF_METHODS if "encoding" in case else METHODS
W_TOL = 0.06                                                  # opening width tolerance (m)


def _poly(p):
    from shapely.geometry import Polygon
    g = Polygon(p)
    return g if g.is_valid else g.buffer(0)


def _rooms(method, case, work):
    """-> (rooms [{label, polygon_mm, area_m2}], openings [{kind, width_m, rooms?}] or None, extra, runtime)."""
    cid = case["id"]
    dxf = work / f"{cid}.dxf"
    t0 = time.time()
    if method.startswith("NATIVE"):
        r = NA.read(dxf, work / f"{cid}_{method}", roles=NA.DECLARED if method == "NATIVE_DECLARED" else None)
        rooms = [{"label": x["name"], "polygon_mm": x["polygon_mm"], "area_m2": x["area_m2"], "codes": x["codes"]}
                 for x in r["rooms"]]
        return rooms, r["openings"], {"status": r["status"]}, time.time() - t0
    if method == "REF_DXF":
        r = RR.read(dxf)
        rooms = [{"label": x["name"], "polygon_mm": x["polygon_mm"], "area_m2": x["area_m2"]} for x in r["rooms"]
                 if x["status"] == "OK"]
        ops = []
        for x in r["rooms"]:
            for o in x.get("openings", ()):
                if not any(o["kind"] == q["kind"] and math.dist(o["mid_mm"], q["mid_mm"]) <= 320 for q in ops):
                    ops.append(dict(o))
        return rooms, ops, {"status": r["status"]}, time.time() - t0
    if method in ("RASTER_10MM", "SCAN_25MM"):
        png = work / f"{cid}_{method}.png"
        meta = BD.raster(case, png, 10.0 if method == "RASTER_10MM" else 25.0, scan=method == "SCAN_25MM")
        t0 = time.time()
        r = VI.raster_rooms(png, meta)
        rooms = [{"label": x["label"], "polygon_mm": x["polygon_mm"], "area_m2": x["area_m2"],
                  "component": x["component"]} for x in r["rooms"]]
        return rooms, r["openings"], {"wall_thickness_mm": r["wall_thickness_mm"], "deskew_deg": r["deskew_deg"],
                                      "ocr": r["ocr"]}, time.time() - t0
    if method == "PDF_VECTOR":
        pdf = work / f"{cid}.pdf"
        meta = BD.vector_pdf(case, pdf)
        t0 = time.time()
        r = VI.vector_pdf_rooms(pdf, meta)
        return [{"label": x["label"], "polygon_mm": x["polygon_mm"], "area_m2": x["area_m2"]} for x in r["rooms"]], \
            None, {}, time.time() - t0
    raise ValueError(method)


def _openings_score(found, truth):
    if found is None:
        return {"state": "NOT_SUPPORTED"}
    want = [("DOOR", w) for w in truth["doors_m"]] + [("WINDOW", w) for w in truth["windows_m"]] + \
        [("PASSAGE", w) for w in truth["passages_m"]]
    left = list(found)
    ok, wrong_kind = 0, 0
    for k, w in want:
        hit = next((o for o in left if o["kind"] == k and abs(o["width_m"] - w) <= W_TOL), None)
        if hit:
            ok += 1
            left.remove(hit)
            continue
        hit = next((o for o in left if abs(o["width_m"] - w) <= W_TOL), None)
        if hit:
            wrong_kind += 1
            left.remove(hit)
    return {"state": "OK", "expected": len(want), "correct": ok, "wrong_kind": wrong_kind, "missed": len(want) - ok -
            wrong_kind, "spurious": len(left)}


def score(method, case, work):
    rooms, ops, extra, rt = _rooms(method, case, work)
    truth_polys, cols, labels = BD.truth_polygons(case)
    T = case["truth"]
    res = {"method": method, "case": case["id"], "rooms": [], "runtime_s": round(rt, 2), **extra}
    if T.get("expect_state"):                                     # the truth is a refusal, with its reason
        res["expected_state"] = T["expect_state"]
        res["refused_ok"] = not rooms and "XREF" in extra.get("status", "")
        return res
    if not rooms and extra.get("status", "OK") != "OK":
        res["state"] = extra["status"]
        return res
    det = [(r, _poly(r["polygon_mm"])) for r in rooms]
    from shapely.geometry import Polygon
    used = set()
    for name, ring in truth_polys.items():
        tp = Polygon(ring)                                        # outer rings on both sides (holes: area)
        best, bi = None, None
        for k, (r, p) in enumerate(det):
            i = tp.intersection(p).area / tp.union(p).area if tp.union(p).area else 0.0
            if i >= 0.5 and k not in used and (best is None or i > best):
                best, bi = i, k
        unl = name in (T.get("unlabelled") or {})
        tt = (T["rooms"].get(name) or T["unlabelled"].get(name))
        if bi is None:
            res["rooms"].append({"truth": name, "unlabelled": unl, "found": False})
            continue
        used.add(bi)
        r, p = det[bi]
        ext = Polygon(r["polygon_mm"]).exterior
        corner = sum(min(math.dist(v, q) for q in ext.coords) for v in ring) / len(ring)
        res["rooms"].append({
            "truth": name, "unlabelled": unl, "found": True, "label": r.get("label"),
            "label_ok": ((r.get("label") or "").upper().startswith(name[:3]) or r.get("label") == case["words"].get(name))
            if not unl else None,
            "iou": round(best, 4), "area_m2": round(r["area_m2"], 4),
            "area_err_pct": round(100 * (r["area_m2"] - tt["area_m2"]) / tt["area_m2"], 3),
            "perimeter_err_pct": round(100 * (ext.length / 1000 - tt["perimeter_m"]) / tt["perimeter_m"], 3),
            "boundary_err_mm": round(Polygon(ring).exterior.hausdorff_distance(ext), 1),
            "corner_err_mm": round(corner, 1)})
    res["false_rooms"] = len(det) - len(used)
    res["openings"] = _openings_score(ops, T)
    res["recall"] = round(sum(1 for x in res["rooms"] if x["found"] and not x["unlabelled"]) /
                          max(1, sum(1 for x in res["rooms"] if not x["unlabelled"])), 3)
    if "wall_thickness_mm" in extra and extra["wall_thickness_mm"] is not None:
        res["scale_check_err_mm"] = round(extra["wall_thickness_mm"] - 200.0, 1)
    return res


def hybrid_pairs(work):
    """the DXF / PDF pair and the DXF / raster pair of every case, through the reconciliation rules."""
    out = []
    for c in BC.CASES:                                            # the encoding cases draw the same pictures
        cad, _, _, _ = _rooms("REF_DXF", c, work)
        for vm in ("PDF_VECTOR", "RASTER_10MM", "SCAN_25MM"):
            vis, _, _, _ = _rooms(vm, c, work)
            recs = HY.reconcile(cad, vis, {"kind": "CAD", "reader": "ref_reader", "version": "1", "method": "REF_DXF"},
                                {"kind": vm, "reader": "vision", "version": "1", "method": vm})
            out.append({"case": c["id"], "vision": vm, "records": recs})
    return out


def run(work):
    work = Path(work)
    for c in ALL_CASES:
        BD.dxf(c, work / f"{c['id']}.dxf")
    results = [score(m, c, work) for c in ALL_CASES for m in methods_for(c)]
    return {"schema": "URBAN_ROOM_READER_BENCHMARK_V1", "cases": [{"id": c["id"], "title": c["title"]} for c in ALL_CASES],
            "methods": list(METHODS), "mcp": MCP_ADAPTERS, "results": results, "hybrid": hybrid_pairs(work)}


def _md(doc):
    rows = ["| case | method | recall | false rooms | IoU (min) | area err % (max abs) | perimeter err % (max abs) | "
            "boundary mm (max) | corner mm (max) | openings correct / expected (wrong kind, spurious) |",
            "|---|---|---|---|---|---|---|---|---|---|"]
    for r in doc["results"]:
        if "expected_state" in r:
            rows.append(f"| {r['case']} | {r['method']} | refusal expected ({r['expected_state']}): "
                        f"{'REFUSED' if r['refused_ok'] else 'NOT REFUSED'} - {r.get('status', '')} |||||||| ")
            continue
        f = [x for x in r["rooms"] if x["found"]]
        o = r.get("openings") or {}
        ops = "NOT_SUPPORTED" if o.get("state") == "NOT_SUPPORTED" else \
            f"{o.get('correct', 0)} / {o.get('expected', 0)} ({o.get('wrong_kind', 0)}, {o.get('spurious', 0)})"
        mx = lambda k: max((abs(x[k]) for x in f), default=None)                  # noqa: E731
        mn = min((x["iou"] for x in f), default=None)
        rows.append(f"| {r['case']} | {r['method']} | {r.get('recall', '-')} | {r.get('false_rooms', '-')} | "
                    f"{mn if mn is not None else '-'} | {mx('area_err_pct') if f else '-'} | "
                    f"{mx('perimeter_err_pct') if f else '-'} | {mx('boundary_err_mm') if f else '-'} | "
                    f"{mx('corner_err_mm') if f else '-'} | {ops} |")
    return "\n".join(rows)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--work")
    a = ap.parse_args(argv)
    with tempfile.TemporaryDirectory() as tmp:
        doc = run(a.work or tmp)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    stable = json.loads(json.dumps(doc))
    for r in stable["results"]:
        r.pop("runtime_s", None)
    (out / "BENCHMARK_RESULTS.json").write_text(json.dumps(stable, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    rt = {}
    for r in doc["results"]:
        rt.setdefault(r["method"], []).append(r["runtime_s"])
    (out / "BENCHMARK_RESULTS.md").write_text(
        "# Room reader benchmark (generated)\n\nSynthetic plans with hand-derived truth (tests/m9_p2b5_bench/"
        "bench_cases.py). See ROOM_READER_BENCHMARK.md for the method and the reading of these figures.\n\n" + _md(doc) +
        "\n\nCAD MCP servers: " + "; ".join(f"{k}: {v}" for k, v in doc["mcp"].items()) +
        "\n\nRuntime per case (s, indicative, varies by machine): " +
        "; ".join(f"{m} median {sorted(v)[len(v) // 2]:.2f}" for m, v in rt.items()) + "\n", encoding="utf-8")
    return doc


if __name__ == "__main__":
    main()
