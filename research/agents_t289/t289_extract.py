"""T-289 extract (read-only): from a finished ARCH_TAKEOFF_V3.0.15 run on the development villa's Drive copies and the
structural DXF, write the two committed inputs of the basis ledger (no coordinates of the client drawing beyond the
entity handles and the engine's own element ids, no names):

  CANDIDATE_V3015_BASIS_LINES.json  the candidate lines behind the four named totals + the cross-trade lines that read
                                    the same element (formwork, reinforcement, waterproofing), by line id / item code /
                                    element id, with the engine quantity and the dimensions the line was computed on;
  BAND_PAIRING_T289.json            each engine ground-beam band id -> the T-242 run(s) (face-line handle pair) it
                                    lies on, with the overlap length; built from the run's own SH08 overlay (engine
                                    band polygons) registered on the DXF face lines named by research/agents_t242.

    python3 -I research/agents_t289/t289_extract.py <run>/v3015 <ST7757 dxf.dxf> --out research/agents_t289

The overlay is drawn at a uniform scale with the y axis flipped; the registration (scale, x0, y1) is found by voting
the vertical / horizontal band edges against the vertical / horizontal face lines of the T-242 handles, and every
pairing is reported with its overlap so the Checker can re-run it.
"""

from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
import math
import sys
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
T242 = ROOT / "research" / "agents_t242"
T248 = ROOT / "research" / "agents_t248"

ANNEX_COLUMNS = ("GFRS:34A", "GFRS:34D", "GFRS:356", "GFRS:350", "GFRS:353", "GFRS:35F", "GFRS:365")
ST03_LINE = "L-061e18cf35a4b6b33d68"         # the ST-03 entrance flight line (T-258 CANDIDATE_V3011_STAIR_DOME_LINES)
CROSS_TRADES = ("FORMWORK", "REINFORCEMENT", "WATERPROOFING", "EXCAVATION", "BACKFILL", "BLINDING")


def _lines(p):
    d = json.loads(Path(p).read_text(encoding="utf-8"))
    return d if isinstance(d, list) else d["lines"]


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _key(eid):
    """the engine component behind an element id: 'P-C:GROUND_BEAMS:GROUND:BAND0001.1' -> 'GROUND_BEAMS:GROUND:BAND0001.1'"""
    return eid.split(":", 1)[1] if eid and ":" in eid else eid


def _slim(l):
    c = (l.get("calculation") or {})
    dims = (c.get("inputs") or {}).get("dimensions") or {}
    return {"line_id": l["line_id"], "item_code": l["item_code"], "trade": l.get("trade"), "floor": l["location"]["floor"],
            "element_id": l["location"]["element_id"], "unit": l["unit"], "evidence_state": l["evidence_state"],
            "measured_net": l.get("measured_net"),
            "bounded_low": (l.get("bounded_range") or {}).get("low"), "bounded_high": (l.get("bounded_range") or {}).get("high"),
            "formula": c.get("formula"), "notes": l.get("notes"),
            "dimensions": {k: dims.get(k) for k in ("length_m", "width_m", "net_plan_m2", "depth_m", "sides", "height_m",
                                                     "H", "h_m", "top_m", "base_m", "area_m2", "section") if k in dims}}


def candidate_lines(run_dir):
    L = _lines(Path(run_dir) / "V3_0_15_BOQ_LINES.json")
    import t289_alsenan as A
    members = A.t248_members()
    cols = [l for l in L if l["item_code"] == "STR.CONC.COLUMN" and l.get("measured_net") is not None]
    off = A.column_offset([{"element_id": l["location"]["element_id"]} for l in cols], members)
    annex_eids = {}
    for l in cols:
        m = A.bind_column(l["location"]["element_id"], members, off)
        if m is not None and m["member"] in ANNEX_COLUMNS:
            annex_eids[l["location"]["element_id"]] = m["member"]
    groups = {"GB_EXTERIOR_24": [], "COL_2F": [], "COL_ANNEX_7": [], "ST03": [], "GB_OTHER_RELEASED": []}
    for l in L:
        if l.get("measured_net") is None:
            continue
        eid = l["location"]["element_id"] or ""
        dims = ((l.get("calculation") or {}).get("inputs") or {}).get("dimensions") or {}
        if l["item_code"] == "STR.CONC.GROUND_BEAM" and "OUTSIDE" in (dims.get("sides") or []):
            groups["GB_EXTERIOR_24"].append(l)
        elif l["item_code"] == "STR.CONC.GROUND_BEAM":
            groups["GB_OTHER_RELEASED"].append(l)     # pool: the builder picks the ones on a main exterior run
        elif l["item_code"] == "STR.CONC.COLUMN" and l["location"]["floor"] == "2F":
            groups["COL_2F"].append(l)
        elif l["item_code"] == "STR.CONC.COLUMN" and eid in annex_eids:
            groups["COL_ANNEX_7"].append(l)
        elif l["line_id"] == ST03_LINE:
            groups["ST03"].append(l)
    keys = {_key(l["location"]["element_id"]) for n, g in groups.items() if n != "GB_OTHER_RELEASED" for l in g}
    cross = [l for l in L if l.get("trade") in CROSS_TRADES and (
        any(k and k in (l["location"]["element_id"] or "") for k in keys) or
        (l["location"]["element_id"] or "").startswith("WPF:BURIED_GROUND_BEAM"))]   # heights read D - 0.10
    return L, groups, cross, {"by_element_id": annex_eids, "frame_offset": off}


def handles(dxf, runs):
    import ezdxf
    doc = ezdxf.readfile(str(dxf))
    out = {}
    for s in runs:
        for h in s["handles"]:
            e = doc.entitydb.get(h)
            if e is not None and e.dxftype() == "LINE":
                out[h] = [list(e.dxf.start)[:2], list(e.dxf.end)[:2]]
            elif e is not None and e.dxftype() == "ARC":
                out["ARC:" + h] = {"c": list(e.dxf.center)[:2], "r": float(e.dxf.radius)}
    return out


def _bands_svg(svg):
    out = {}
    for m in re.finditer(r'<polygon points="([^"]+)"[^>]*><title>(BAND[0-9.]+)\s', svg):
        out[m.group(2)] = [tuple(map(float, p.split(","))) for p in m.group(1).split()]
    return out


def register(bands, H):
    LN = [p for p in H.values() if isinstance(p, list)]
    V = [p[0][0] for p in LN if abs(p[0][0] - p[1][0]) < 1]
    Hz = [p[0][1] for p in LN if abs(p[0][1] - p[1][1]) < 1]
    svx, svy = [], []
    for P in bands.values():
        xs, ys = [p[0] for p in P], [p[1] for p in P]
        (svx if max(xs) - min(xs) < max(ys) - min(ys) else svy).extend([min(xs), max(xs)] if
                                                                       max(xs) - min(xs) < max(ys) - min(ys) else
                                                                       [min(ys), max(ys)])
    best = None
    for k5 in range(2900, 3100):
        k = k5 / 100000.0
        cx = collections.Counter(round((X - sx / k) / 10) for sx in svx for X in V)
        cy = collections.Counter(round((Y + sy / k) / 10) for sy in svy for Y in Hz)
        (xo, nx), (yo, ny) = cx.most_common(1)[0], cy.most_common(1)[0]
        if best is None or nx + ny > best["votes"]:
            best = {"k_px_per_mm": k, "x0_mm": xo * 10.0, "y1_mm": yo * 10.0, "votes": nx + ny}
    return best


def pair(bands, H, spans, reg, arcs=()):
    k, x0, y1 = reg["k_px_per_mm"], reg["x0_mm"], reg["y1_mm"]
    out = {}
    for bid, P in sorted(bands.items()):
        Q = [(x0 + a / k, y1 - b / k) for a, b in P]
        xs, ys = [p[0] for p in Q], [p[1] for p in Q]
        d = "Y" if max(xs) - min(xs) < max(ys) - min(ys) else "X"
        c_across = (sum(xs) / len(xs)) if d == "Y" else (sum(ys) / len(ys))
        b0, b1 = (min(ys), max(ys)) if d == "Y" else (min(xs), max(xs))
        hits = []
        cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
        for s in spans:
            if s["span_id"].startswith("ARC:"):
                continue
            ls = [H.get(h) for h in s["handles"]]
            if s["direction"] != d or not ls or any(not isinstance(l, list) for l in ls):
                continue
            ax = 0 if d == "Y" else 1                 # the across coordinate of the face lines
            us = sorted(l[0][ax] for l in ls)
            if not (us[0] - 30 <= c_across <= us[-1] + 30):
                continue
            sides = {}                                # face lines grouped by side (a face may be drawn in pieces)
            for l in ls:
                sides.setdefault(round(l[0][ax] / 50.0), []).append(min(l[0][1 - ax], l[1][1 - ax]))
            lo = max(min(v) for v in sides.values())
            f0, f1 = lo + s["span_from_m"] * 1000.0, lo + s["span_to_m"] * 1000.0
            ov = min(f1, b1) - max(f0, b0)
            if ov > 50:
                hits.append({"run": s["span_id"], "overlap_m": round(ov / 1000.0, 3)})
        if not hits:                                  # a curved band: drawn as its chord box in the overlay
            for a in arcs:
                c = [H.get("ARC:" + h) for h in a["handles"]]
                if any(v is None for v in c):
                    continue
                dist = max(math.hypot(cx - v["c"][0], cy - v["c"][1]) for v in c)   # chord box inside the sweep
                if dist <= max(v["r"] for v in c) + 100.0:
                    hits.append({"run": a["span_id"], "overlap_m": None, "centre_distance_mm": round(dist, 1),
                                 "net_plan_m2": a.get("net_plan_m2")})
        out[bid] = {"direction": d, "band_length_m": round((b1 - b0) / 1000.0, 3), "runs": hits}
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("run", help="the V3.0.15 output directory (holding V3_0_15_BOQ_LINES.json)")
    ap.add_argument("structural", help="Drive 'ST7757 dxf.dxf'")
    ap.add_argument("--svg", help="the run's SH08 ground-beam overlay (default: <run>/structural/overlays/...)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    run = Path(a.run)
    L, groups, cross, annex = candidate_lines(run)
    lines_p = run / "V3_0_15_BOQ_LINES.csv"
    proj = L[0]["project"]
    cand = {"schema": "T289_CANDIDATE_V3015_BASIS_LINES", "candidate": "ARCH_TAKEOFF_V3.0.15",
            "candidate_lines_csv_sha256": _sha(lines_p) if lines_p.exists() else None,
            "project": proj, "lines_in_candidate": len(L),
            "annex_column_element_ids": annex,
            "groups": {g: [_slim(l) for l in sorted(v, key=lambda x: x["line_id"])] for g, v in groups.items()},
            "cross_trade": [_slim(l) for l in sorted(cross, key=lambda x: x["line_id"])]}
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "CANDIDATE_V3015_BASIS_LINES.json").write_text(json.dumps(cand, indent=1, ensure_ascii=False) + "\n",
                                                          encoding="utf-8")
    G = json.loads((T242 / "ALSENAN_GROUND_INPUT.json").read_text(encoding="utf-8"))
    spans = G["spans"]
    arcs = [dict(a, span_id=a["arc_band"], handles=a["arc_band"][4:].split("+"), direction="ARC")
            for a in G["arc_bands"]]
    H = handles(a.structural, spans + arcs)
    svg_p = Path(a.svg) if a.svg else None
    if svg_p is None:
        c = sorted(run.rglob("SH08_GROUND_BEAM_PLAN_GROUND.svg"))
        svg_p = c[0] if c else None
    bands = _bands_svg(svg_p.read_text(encoding="utf-8"))
    reg = register(bands, H)
    pr = {"schema": "T289_BAND_PAIRING", "structural_sha256": _sha(a.structural), "overlay": svg_p.name,
          "overlay_sha256": _sha(svg_p), "registration": reg, "bands": pair(bands, H, spans, reg, arcs)}
    (out / "BAND_PAIRING_T289.json").write_text(json.dumps(pr, indent=1) + "\n", encoding="utf-8")
    for g, v in groups.items():
        print(g, len(v), round(sum(float(l["measured_net"]) for l in v), 6))
    print("cross-trade lines", len(cross), "registration", reg)
    return 0


if __name__ == "__main__":
    main()
