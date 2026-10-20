"""T-135 Alsenan check: STAIR_FLIGHT_ONCE_V1 on the released ARCH_TAKEOFF_V2.9 flights of the architectural DXF, with
the slab-above evidence read from the structural DXF.

What it does (no engine or tools file is changed; research output only):
    1. the V2.9 run (pickle (boq, arch, extra) of tools.urban_boq_m9.arch_compute(<arch DXF>, method=
       "ARCH_TAKEOFF_V2.9"), the same run T-113 / T-116 / T-122 / T-129 used): per plan region its floor, level and
       the stair flights the route found (room symbols_inside), in storey order;
    2. the plan-to-plan offset from the column grid (arch_rooms.floor_offset on the column rectangles of the layer the
       run typed COLUMN), the same alignment the released cross_plan_flights uses;
    3. the printed level marks of each plan (arch_rooms._level on every text inside the region);
    4. the slab above each storey from the structural DXF: the three roof-slab plans (titles '... ROOF SLAB.'), each
       plan's window between the neighbouring plans; inside it the stair panel lines (layer ST), the slab openings
       (layer S-OPENING) and the '(With Stair)' tags are counted. A plan with none of them -> NONE_DRAWN; a plan with
       them -> DRAWN (not located on the architectural plan; the piece then counts a flight as its storey's own only
       where it differs from the flight under it);
    5. STAIR_FLIGHT_ONCE_V1 per flight, with the released V2.9 reading beside it.
Usage (Python 3.11; drawings stay outside the clone):
    python3 -I research/agents_t135/alsenan_stair_flight_once.py --v29 <v29.pkl> --st <structural DXF> --out <dir>
Writes only to --out: flights CSV (floor, flight, treads, m2, lm, reading, state, reasons) and a summary JSON. Only
areas, lengths, levels and counts are written; no coordinates, names or file contents of the drawings.
"""

from __future__ import annotations

import argparse
import csv
import json
import pickle
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_rooms as AR  # noqa: E402
from engine.source import stair_flight_once_v1 as SO  # noqa: E402

SLAB_TITLES = {"GF": "GROUND FLOOR ROOF SLAB", "1F": "FIRST FLOOR ROOF SLAB", "2F": "SECOND FLOOR ROOF SLAB"}
SECTION_RISERS = {"GF": 27, "1F": 25}          # owner Q-46 A: section A-A, main stair (10 + 5 + 12 and 13 + 12)


def column_boxes(segments, layer, box):
    """rectangles of one layer inside a region box: connected segment groups (shared end points) -> bounding boxes."""
    segs = [s for s in segments if s["layer"] == layer and all(box[0] <= p[0] <= box[2] and box[1] <= p[1] <= box[3]
                                                              for p in (s["a"], s["b"]))]
    key = lambda p: (round(p[0], 1), round(p[1], 1))  # noqa: E731
    parent = {}

    def find(k):
        parent.setdefault(k, k)
        while parent[k] != k:
            parent[k] = parent[parent[k]]
            k = parent[k]
        return k
    for s in segs:
        parent[find(key(s["a"]))] = find(key(s["b"]))
    groups = defaultdict(list)
    for s in segs:
        groups[find(key(s["a"]))] += [s["a"], s["b"]]
    out = []
    for pts in groups.values():
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        if len(pts) >= 8:
            out.append((min(xs), min(ys), max(xs), max(ys)))
    return out


def slab_evidence(st_path):
    import ezdxf
    doc = ezdxf.readfile(st_path)
    msp = doc.modelspace()
    texts, segs = [], []

    def walk(es, depth=0):                       # titles sit inside title blocks (INSERT): read them too
        for e in es:
            t = e.dxftype()
            if t in ("TEXT", "MTEXT"):
                v = e.dxf.text if t == "TEXT" else e.plain_text()
                texts.append((v, e.dxf.insert.x, e.dxf.insert.y))
            elif t == "INSERT" and depth < 3:
                try:
                    walk(e.virtual_entities(), depth + 1)
                except Exception:  # noqa: BLE001  (a block that does not explode carries no title)
                    pass
    walk(msp)
    for e in msp:
        t = e.dxftype()
        if t == "LINE":
            segs.append((e.dxf.layer, e.dxf.start.x, e.dxf.start.y, e.dxf.end.x, e.dxf.end.y))
        elif t == "LWPOLYLINE":
            p = [(a[0], a[1]) for a in e.get_points()]
            if e.closed:
                p.append(p[0])
            segs += [(e.dxf.layer, a[0], a[1], b[0], b[1]) for a, b in zip(p, p[1:])]
    titles = {}
    for v, x, y in texts:
        for fl, ttl in SLAB_TITLES.items():
            if v.strip().upper().startswith(ttl):
                titles[fl] = (x, y)
    xs = sorted(titles.values())
    out = {}
    for fl, (x, y) in titles.items():
        i = xs.index((x, y))
        lo = (xs[i - 1][0] + x) / 2 if i > 0 else -1e12
        hi = (xs[i + 1][0] + x) / 2 if i + 1 < len(xs) else 1e12
        inside = lambda a, b: lo <= a <= hi and y - 1000 <= b <= y + 30000  # noqa: E731  (plan above its title, mm)
        n_st = sum(1 for s in segs if s[0] == "ST" and inside(s[1], s[2]) and inside(s[3], s[4]))
        n_op = sum(1 for s in segs if s[0] == "S-OPENING" and inside(s[1], s[2]) and inside(s[3], s[4]))
        n_tag = sum(1 for v, a, b in texts if "with stair" in v.lower() and inside(a, b))
        state = "DRAWN" if (n_st or n_tag) else "NONE_DRAWN"
        out[fl] = {"state": state, "stair_panel_lines": n_st, "opening_lines": n_op, "with_stair_tags": n_tag,
                   "source": f"structural '{SLAB_TITLES[fl]}' plan: {n_st} stair-panel lines, {n_tag} '(With Stair)' "
                             f"tags, {n_op} slab-opening lines"}
    return out


def run(v29_path, st_path, out):
    boq, arch, extra = pickle.load(open(v29_path, "rb"))
    u = arch["run"]["unit_m"]
    regs = sorted((r for r in arch["regions"] if not r.get("warning")), key=lambda r: r["level_m"] or 0.0)
    slab = slab_evidence(st_path)
    plans, prev_cols = [], None
    for r in regs:
        col_layer = next(k for k, v in r["layer_roles"].items() if v == "COLUMN")
        cols = column_boxes(extra["segments"], col_layer, r["box"])
        fls = [dict(f) for rm in arch["rooms"] if rm["floor"] == r["floor"]
               for f in (rm.get("symbols_inside") or {}).get("stair_flights") or ()]
        b = r["box"]
        marks = [{"x": t["x"], "y": t["y"], "value_m": AR._level(t["value"])} for t in extra["texts"]
                 if b[0] <= t["x"] <= b[2] and b[1] <= t["y"] <= b[3] and AR._level(t["value"]) is not None]
        off = AR.floor_offset(prev_cols, cols, u) if prev_cols else None
        plans.append({"floor": r["floor"], "level_m": r["level_m"], "flights": fls, "level_marks": marks,
                      "slab_above": slab.get(r["floor"]), "offset_to_below": (off["dx"], off["dy"]) if off else None,
                      "_align": off})
        prev_cols = cols
    rec = SO.flights_once(plans, unit_m=u)
    # the main stair = the flights the cross-plan pairing chains (the 2F copies lie over 1F F2 / F3, which lie over the
    # GF flights): the section A-A riser counts are compared with these flights only
    over = defaultdict(set)
    for x in rec["flights"]:
        if x.get("over"):
            below = plans[[p["floor"] for p in plans].index(x["floor"]) - 1]["floor"]
            over[below].add(x["over"])
    rec = SO.flights_once(plans, unit_m=u, section_risers={fl: {"risers": n, "flight_ids": sorted(over[fl])}
                                                          for fl, n in SECTION_RISERS.items()})
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "FLIGHTS_ONCE.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["floor", "flight", "kind", "treads", "tread_m2", "step_lm", "released_reading", "over", "over_treads",
                    "outline_shift_m", "state", "storey", "counted_tread_m2", "counted_step_lm", "held_high_m2",
                    "held_high_lm", "evidence", "reasons"])
        for x in rec["flights"]:
            w.writerow([x["floor"], x["flight_id"], x["kind"], x["treads"], x["tread_m2"], x["step_lm"],
                        x["released_reading"], x.get("over") or "", x.get("over_treads"),
                        x.get("outline_shift_m"), x["state"], x["storey"], x["counted_tread_m2"], x["counted_step_lm"],
                        (x["held"] or {}).get("tread_m2", {}).get("high"), (x["held"] or {}).get("step_lm", {}).get("high"),
                        " | ".join(x["evidence"]), " | ".join(x["reasons"])])
    summ = {"method": rec["method"], "unit_m": u,
            "plans": [{"floor": p["floor"], "level_m": p["level_m"], "flights": len(p["flights"]),
                       "level_marks": len(p["level_marks"]),
                       "alignment": None if not p["_align"] else {"votes": p["_align"]["votes"], "of": p["_align"]["of"],
                                                                 "dx_m": round(p["_align"]["dx"] * u, 4),
                                                                 "dy_m": round(p["_align"]["dy"] * u, 4)},
                       "slab_above": p["slab_above"]} for p in plans],
            "totals": rec["totals"], "section_check": rec["section_check"], "warnings": rec["warnings"]}
    (out / "flights_once_summary.json").write_text(json.dumps(summ, indent=1), encoding="utf-8")
    print(json.dumps(summ["totals"], indent=1))
    for x in rec["flights"]:
        print(x["floor"], x["flight_id"].split(":")[-1], x["treads"], x["tread_m2"], x["step_lm"], x["released_reading"],
              "->", x["state"], x["storey"], "|", "; ".join(x["evidence"] + x["reasons"])[:220])
    return rec


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--v29", required=True)
    ap.add_argument("--st", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    run(a.v29, a.st, a.out)
