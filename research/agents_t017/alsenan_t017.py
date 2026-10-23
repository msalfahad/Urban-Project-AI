"""T-017 development-villa run: PAIR_MIDLINE_CENSUS_V1 on P7757.dxf, wall by wall against the block ledger.

Reads the drawing with its own reader (ezdxf entities, inserts exploded; no engine module), runs the census
(masonry_pair_census.py), and matches each census run to the ledger rows (T-143 rows / T-108 r2 lengths / T-125 V2 runs)
by position. Matching key only: the V2 band centrelines in floor-local metres (from one MASONRY_CENTRELINE_V2 capture,
research/agents_t125/alsenan_v2_run.py output) give each ledger row a place on the plan; no ledger number feeds the
census. Writes only the tables named below (wall ids, lengths, causes; no drawing coordinates).

Usage (Python 3.11; drawing and capture outside the repository):
    python3 -I research/agents_t017/alsenan_t017.py <P7757.dxf> <t125_inputs.pkl> <t125_v2.json> [--check]
Floor frames (drawing units, a partition of the model space into the three plan sheets, not a measurement): taken from
the wall-stage capture's entity extents of each floor, padded 0.5 m."""
from __future__ import annotations

import argparse
import csv
import io
import json
import math
import pickle
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import masonry_pair_census as PC  # noqa: E402

WALL_LAYERS = {"1"}          # project fact: the plan's wall-face layer (P7757 layer table); not engine code
COLUMN_LAYERS = {"S-COL.BON"}
OPENING_LAYERS = {"D", "W"}
OUT_ROWS = HERE / "T017_WALL_AGREEMENT.csv"
OUT_BANDS = HERE / "T017_BAND_AGREEMENT.csv"
OUT_SUMMARY = HERE / "summary.json"


def read_floors(dxf_path, frames):
    import ezdxf
    from ezdxf import path as ezpath
    doc = ezdxf.readfile(dxf_path)

    def lay(e):
        try:
            return e.dxf.layer
        except Exception:
            return "?"

    def walk(ents, parent=None, depth=0):
        for e in ents:
            L = lay(e)
            if L == "0" and parent:
                L = parent
            t = e.dxftype()
            if t == "INSERT" and depth < 6:
                try:
                    yield from walk(e.virtual_entities(), L, depth + 1)
                except Exception:
                    continue
            elif t in ("LINE", "LWPOLYLINE", "POLYLINE", "ARC", "CIRCLE"):
                yield L, t, e

    out = {fl: {"wall": [], "col_lines": [], "open_pts": [], "other": [], "wall_arcs": 0} for fl in frames}

    def floor_of(x, y):
        for fl, (x0, x1, y0, y1) in frames.items():
            if x0 <= x <= x1 and y0 <= y <= y1:
                return fl
        return None

    for L, t, e in walk(doc.modelspace()):
        if L in WALL_LAYERS and t in ("ARC", "CIRCLE"):
            c = e.dxf.center
            fl = floor_of(c.x, c.y)
            if fl:
                out[fl]["wall_arcs"] += 1
            continue
        try:
            p = ezpath.make_path(e)
        except Exception:
            continue
        straight = all(not hasattr(cmd, "ctrl1") and not hasattr(cmd, "ctrl") for cmd in p)
        pts = [(v.x, v.y) for v in p.flattening(5)]
        for a, b in zip(pts, pts[1:]):
            fl = floor_of(*a)
            if not fl:
                continue
            seg = ((a[0] / 1000.0, a[1] / 1000.0), (b[0] / 1000.0, b[1] / 1000.0))
            if L in WALL_LAYERS:
                if straight:
                    out[fl]["wall"].append(seg)
                else:
                    out[fl]["wall_arcs"] += 0  # curved pieces of a polyline: counted below as not read
            elif L in COLUMN_LAYERS:
                out[fl]["col_lines"].append(seg)
            else:
                if L in OPENING_LAYERS:
                    out[fl]["open_pts"].extend(seg)
                if straight:
                    out[fl]["other"].append(seg)
        if L in WALL_LAYERS and not straight:
            fl = floor_of(*pts[0]) if pts else None
            if fl:
                out[fl]["wall_arcs"] += 1
    from shapely.geometry import LineString
    from shapely.ops import polygonize, unary_union
    for fl, f in out.items():
        ls = [LineString(s) for s in f["col_lines"] if s[0] != s[1]]
        f["columns"] = [list(p.exterior.coords) for p in polygonize(unary_union(ls))] if ls else []
    return out


def frames_from_capture(cap):
    fr = {}
    for fl, f in cap["floors"].items():
        seg = f["ents"]["segments"]
        xs = [p[0] for s in seg for p in (s["a"], s["b"])]
        ys = [p[1] for s in seg for p in (s["a"], s["b"])]
        fr[fl] = (min(xs) - 500, max(xs) + 500, min(ys) - 500, max(ys) + 500)
    return fr


def origin(cap, fl):
    f = cap["floors"][fl]
    pts = [p for w in f["walls"] for p in (w.get("centreline") or [])]
    u = f["unit_m"]
    return min(p[0] for p in pts) * u, min(p[1] for p in pts) * u


def ledger():
    rows = list(csv.DictReader(open(ROOT / "research/agents_t143/T143_BLOCK_BY_WALL_RUN.csv", encoding="utf-8")))
    t108 = {r["row_id"]: r for r in csv.DictReader(open(ROOT / "research/agents_t108/T108_BY_WALL.csv", encoding="utf-8"))}
    v2 = {(r["floor"], r["run_id"]): r for r in csv.DictReader(open(ROOT / "research/agents_t108/T108_V2_RUN_LENGTHS.csv", encoding="utf-8"))}
    return rows, t108, v2


def band_geom(v2json, fl, band):
    pts = v2json["floors"][fl]["bands_local_m"].get(band)
    return pts


def project(run, ox, oy):
    (ux, uy), (nx, ny) = PC._axis(run.ang)
    # census axis coordinates are in absolute metres; shift to the floor-local frame
    so = ox * ux + oy * uy
    oo = ox * nx + oy * ny
    return run.s0 - run.ext_m[0] - so, run.s1 + run.ext_m[1] - so, run.off - oo


def match(runs, bands, ox, oy):
    """band id -> census runs on it (same direction, midline within 0.03 m, axis overlap)."""
    hit = defaultdict(list)
    used = set()
    for bid, pts in bands.items():
        if not pts or len(pts) != 2:
            continue
        (x0, y0), (x1, y1) = pts
        ang = PC._norm_ang(math.atan2(y1 - y0, x1 - x0))
        (ux, uy), (nx, ny) = PC._axis(ang)
        b0, b1 = sorted((x0 * ux + y0 * uy, x1 * ux + y1 * uy))
        bo = x0 * nx + y0 * ny
        for r in runs:
            if abs(r.ang - ang) > PC.ANG_TOL:
                continue
            s0, s1, o = project(r, ox, oy)
            if abs(o - bo) <= 0.012 and min(s1, b1) - max(s0, b0) > 0.01:
                hit[bid].append((s0, r))
                used.add(r.key)
    return hit, used


RESULTS = {}


def build(dxf, cap_p, v2_p):
    cap = pickle.load(open(cap_p, "rb"))
    v2json = json.load(open(v2_p))
    frames = frames_from_capture(cap)
    floors = read_floors(dxf, frames)
    rows, t108, v2 = ledger()
    band_rows, row_out, summ = [], [], {"method": PC.METHOD, "floors": {}}
    for fl in ("GF", "1F", "2F"):
        f = floors[fl]
        res = PC.census(f["wall"], f["columns"], f["open_pts"], floor=fl, other_segments=f["other"])
        ox, oy = origin(cap, fl)
        bands = v2json["floors"][fl]["bands_local_m"]
        hit, used = match(res["runs"], bands, ox, oy)
        unmatched = [r for r in res["runs"] if r.key not in used]
        RESULTS[fl] = (res, unmatched)
        summ["floors"][fl] = {"totals": PC.totals(res), "runs": len(res["runs"]), "unmatched_runs": len(unmatched),
                              "unmatched_m": round(sum(r.arch_run_m for r in unmatched), 4),
                              "unmatched_by_t": {}, "wall_arcs_not_read": f["wall_arcs"],
                              "gaps": defaultdict(float), "caps": len(res["listed"])}
        for r in unmatched:
            k = f"{r.t:.2f}"
            summ["floors"][fl]["unmatched_by_t"][k] = round(summ["floors"][fl]["unmatched_by_t"].get(k, 0) + r.arch_run_m, 4)
        for g in res["gaps"]:
            summ["floors"][fl]["gaps"][g["kind"]] += g["width"]
        summ["floors"][fl]["gaps"] = {k: round(v, 4) for k, v in summ["floors"][fl]["gaps"].items()}
        # ledger rows per band
        by_band = defaultdict(list)
        for r in rows:
            if r["floor"] != fl:
                continue
            for run_id in (r["v2_runs"] or "").split():
                by_band[run_id.split("#")[0]].append(r["row_id"])
        for bid in sorted(set(by_band) | set(hit)):
            v2_runs = [v for (vf, rid), v in v2.items() if vf == fl and rid.split("#")[0] == bid]
            v2_arch = sum(float(v["arch_run_m"]) for v in v2_runs)
            cr = sorted(hit.get(bid, []), key=lambda q: q[0])
            pc_arch = sum(r.arch_run_m for _, r in cr)
            band_rows.append({"floor": fl, "band": bid, "ledger_rows": " + ".join(sorted(set(by_band.get(bid, [])))),
                              "t_m": (v2_runs[0]["t_m"] if v2_runs else (f"{cr[0][1].t:.2f}" if cr else "")),
                              "v2_runs": len(v2_runs), "v2_arch_run_m": f"{v2_arch:.4f}",
                              "census_runs": len(cr), "census_arch_run_m": f"{pc_arch:.4f}",
                              "census_t_m": " ".join(sorted({f"{r.t:.2f}" for _, r in cr})),
                              "census_ends": " | ".join("+".join(r.ends) for _, r in cr),
                              "census_openings_m": f"{sum(sum(r.openings) for _, r in cr):.4f}",
                              "diff_m": f"{pc_arch - v2_arch:+.4f}"})
            # row level: each census run goes to the V2 run whose stretch of the band holds its midpoint; the V2 run
            # boundaries are the band's split stretches (in_run False), in band order (matching key only)
            v2_sorted = sorted(v2_runs, key=lambda v: int(v["run_id"].split("#")[1]) if "#" in v["run_id"] else 0)
            if not v2_sorted:
                continue
            pts = bands.get(bid)
            cuts = []
            for st in v2json["floors"][fl]["v2"].get("stretches") or ():
                if st.get("wall_id") == bid and str(st.get("in_run")) == "False":
                    cuts.append((float(st["from_m"]) + float(st["to_m"])) / 2)
            cuts.sort()
            assign = defaultdict(list)
            if len(v2_sorted) == 1 or not pts or len(cuts) != len(v2_sorted) - 1:
                if len(v2_sorted) == 1:
                    assign[v2_sorted[0]["run_id"]] = [r for _, r in cr]
                elif len(v2_sorted) == len(cr):
                    for v, (_, r) in zip(v2_sorted, cr):
                        assign[v["run_id"]].append(r)
            else:
                (x0, y0), (x1, y1) = pts
                ang = PC._norm_ang(math.atan2(y1 - y0, x1 - x0))
                (ux, uy), _ = PC._axis(ang)
                s_first = x0 * ux + y0 * uy
                sgn = 1.0 if (x1 * ux + y1 * uy) >= s_first else -1.0
                for _, r in cr:
                    a_, b_, _o = project(r, ox, oy)
                    pos = sgn * ((a_ + b_) / 2 - s_first)
                    i = sum(1 for c in cuts if pos > c)
                    assign[v2_sorted[i]["run_id"]].append(r)
            for rid, rs in assign.items():
                row_out.append((fl, rid, rs))
    return band_rows, row_out, summ, rows, t108


def row_table(row_out, rows, t108):
    by_run = {(fl, rid): rs for fl, rid, rs in row_out}
    out = []
    for r in rows:
        runs = (r["v2_runs"] or "").split()
        t = t108.get(r["row_id"]) or next((x for x in t108.values()
                                           if r["row_id"] in [q.strip() for q in x["row_id"].split("+")]), None)
        got = [by_run.get((r["floor"], x)) for x in runs]
        cr = [c for g in got if g for c in g] if got and all(g is not None for g in got) else []
        led = float(t["physical_length_m"]) if t and t.get("physical_length_m") else None
        v2a = None
        if runs:
            v2a = 0.0
        pc = sum(c.arch_run_m for c in cr) if cr else None
        out.append({"row_id": r["row_id"], "floor": r["floor"], "group": r["group"], "t_ledger_m": r["t_m"],
                    "t108_row": t["row_id"] if t else "", "v2_runs": " ".join(runs),
                    "ledger_length_m (T-108 r2, Q-69 B)": f"{led:.4f}" if led is not None else "",
                    "hand_t143_L1_m": r["L1_arch_run_m"],
                    "census_t_m": " ".join(sorted({f"{c.t:.2f}" for c in cr if c})) if cr else "",
                    "census_arch_run_m": f"{pc:.4f}" if pc is not None else "",
                    "census_ends": " | ".join("+".join(c.ends) for c in cr if c),
                    "census_openings_m": f"{sum(sum(c.openings) for c in cr if c):.4f}" if pc is not None else ""})
    return out


def to_csv(rs):
    o = io.StringIO()
    w = csv.DictWriter(o, fieldnames=list(rs[0]), lineterminator="\n")
    w.writeheader()
    w.writerows(rs)
    return o.getvalue()


# Causes of every row that does not agree within 0.05 m (this run's own reading of the linework; development villa).
# Each names the physical cause; none is resolved toward either side (ERS s.2.4). Verdict proposals for the Checker.
CAUSES = {
    "GF-W00": ("CORNER_SQUARE_OWNERSHIP", "RULE_DIFFERENCE",
               "one 0.20 x 0.20 corner square with GF-W17: the plan carries GF-W17's outer face to the exterior face "
               "and stops the exterior wall's faces at it; census gives the square to GF-W17 (-0.100 here, +0.100 there), "
               "the ledger splits it at the midlines; 0.20 family total unchanged"),
    "GF-W17": ("CORNER_SQUARE_OWNERSHIP", "RULE_DIFFERENCE", "pair of GF-W00 (+0.100 / -0.100)"),
    "1F-W04": ("CORNER_SQUARE_OWNERSHIP", "RULE_DIFFERENCE",
               "same pattern as GF-W00 / GF-W17 at 1F-W08's end: census +0.100 here, -0.100 on 1F-W08; family total unchanged"),
    "1F-W08": ("CORNER_SQUARE_OWNERSHIP", "RULE_DIFFERENCE", "pair of 1F-W04 (-0.100 / +0.100)"),
    "1F-W16": ("CORNER_SQUARE_OWNERSHIP", "RULE_DIFFERENCE",
               "0.15 x 0.15 corner with 1F-W21, both outer faces drawn: census shares it at the midlines (+0.075 here, "
               "-0.075 on 1F-W21); the ledger gives it to 1F-W21 (to the far face) and stops 1F-W16 on the face; 0.15 family unchanged"),
    "1F-W21": ("CORNER_SQUARE_OWNERSHIP", "RULE_DIFFERENCE", "pair of 1F-W16 (-0.075 / +0.075)"),
    "GF-W19": ("CORNER_SQUARE_OWNERSHIP", "RULE_DIFFERENCE",
               "0.15 corner with GF-W30 (the wall with no plan-run band): census shares it at the midlines (+0.075 here, "
               "+0.075 inside the GF-W30 census run); the ledger stops GF-W19 at a free end"),
    "GF-W02": ("CORNER_SQUARE_OWNERSHIP", "RULE_DIFFERENCE",
               "L corner of GF-W02 (0.20) and GF-W23 (0.15), both outer faces drawn (handles D2:309 / D2:335): census "
               "shares the 0.20 x 0.15 square at the midlines (-0.075 here, +0.100 on GF-W23); the ledger's plan run reads "
               "the corner as a T and gives the square to GF-W02 (to the far face). Same plan area (0.030 m2); 0.075 m "
               "of 0.20 moves to 0.100 m of 0.15 between thickness families"),
    "GF-W23": ("CORNER_SQUARE_OWNERSHIP", "RULE_DIFFERENCE", "pair of GF-W02 (+0.100 / -0.075, two thickness families)"),
    "GF-W20": ("OBLIQUE_END_NOT_CLOSED", "UNRESOLVED",
               "45 deg end: the census closes only right-angle junctions and stops on the drawn pair (-0.125); the ledger "
               "measures to its module end and holds 0 .. 0.137 m more (T-108 r2); both methods leave the 45 deg end open"),
    "GF-W21": ("OBLIQUE_END_NOT_CLOSED", "UNRESOLVED", "as GF-W20 (-0.062)"),
    "GF-W30": ("OBLIQUE_END_NOT_CLOSED", "UNRESOLVED",
               "wall missing from the plan run (no band) but FOUND by the census: 0.279 m both faces + 0.800 door + "
               "0.039 m stub + 0.075 corner = 1.193 m (handles D2:741 / D2:743); its west end meets the 45 deg wedge walls "
               "(D2:793 / D2:805), where one face runs 0.094 m further: the hand 1.525 m runs to the oblique wall's "
               "centreline. True length between 1.193 and 1.525 m (oblique junction piece); matched by elimination"),
    "GF-W35": ("CURVED_NOT_READ", "UNRESOLVED", "curved wall (arcs): not read by this census (NOT READ, never 0)"),
    "1F-W25": ("CURVED_NOT_READ", "UNRESOLVED", "concave glazed bay with its curved stub: not read by this census"),
    "GF-W37": ("GLAZING_END_PIECE_NOT_FOUND", "UNRESOLVED",
               "ledger 0.100 m masonry at the pool-side glazing (the glazing itself is out of the run): no paired faces "
               "on the wall layer there; census finds nothing (not 0: NOT FOUND)"),
    "GF-H02": ("NOT_ON_WALL_LAYER", "UNRESOLVED",
               "ledger row HELD (layer material held): its faces are not on the wall-face layer, which is all this census reads"),
}


def final_rows(row_out, rows, t108):
    base = row_table(row_out, rows, t108)
    res_gf, unmatched_gf = RESULTS["GF"]
    um15 = [r for r in unmatched_gf if abs(r.t - 0.15) < 1e-6]
    out = []
    for r in base:
        L = r["ledger_length_m (T-108 r2, Q-69 B)"]
        c = r["census_arch_run_m"]
        if r["row_id"] == "GF-W30" and len(um15) == 1 and not c:
            c = f"{um15[0].arch_run_m:.4f}"
            r["census_t_m"] = "0.15"
            r["census_ends"] = "+".join(um15[0].ends)
            r["census_openings_m"] = f"{sum(um15[0].openings):.4f}"
        d = (float(c) - float(L)) if (L and c) else None
        if r["row_id"] in CAUSES:
            cause, verdict, why = CAUSES[r["row_id"]]
            status = "DIFFERS" if d is not None else "NOT_READ_OR_NOT_FOUND"
        elif d is not None and abs(d) <= 0.05:
            cause, verdict, why, status = "", "", "", "AGREE"
        else:
            cause, verdict, why, status = "UNEXPLAINED", "UNRESOLVED", "no cause named", "DIFFERS" if d is not None else "NOT_READ_OR_NOT_FOUND"
        out.append({"row_id": r["row_id"], "floor": r["floor"], "group": r["group"], "t_ledger_m": r["t_ledger_m"],
                    "t_census_m": r["census_t_m"], "ledger_row (T-108 r2)": r["t108_row"],
                    "ledger_physical_m (Q-69 B)": L, "hand_L1_t143_m": r["hand_t143_L1_m"],
                    "census_arch_run_m": c, "census_minus_ledger_m": f"{d:+.4f}" if d is not None else "",
                    "status": status, "cause": cause, "verdict_proposal": verdict, "why": why,
                    "census_ends": r["census_ends"], "census_openings_m": r["census_openings_m"]})
    return out


def floor_table(rows_final):
    # T-225 follow-up evidence (agents/task-T-225 @ 96500525, RUN_A_VS_ENGINE_BY_FLOOR_THICKNESS.csv, residual_m column):
    # engine physical - run A both faces - openings kept in the run, the residual named for this census
    t225 = {("GF", "0.15"): {"residual_m": "1.457"}, ("GF", "0.20"): {"residual_m": "2.529"},
            ("GF", "0.40"): {"residual_m": "0.000"}, ("1F", "0.15"): {"residual_m": "2.376"},
            ("1F", "0.20"): {"residual_m": "1.781"}, ("2F", "0.15"): {"residual_m": "0.400"},
            ("2F", "0.20"): {"residual_m": "0.500"}}
    out = []
    for fl in ("GF", "1F", "2F"):
        res, unmatched = RESULTS[fl]
        comp = defaultdict(lambda: defaultdict(float))
        for r in res["runs"]:
            k = f"{r.t:.2f}"
            c = comp[k]
            c["arch"] += r.arch_run_m
            c["solid"] += r.solid_m
            c["openings"] += sum(r.openings)
            c["one_face"] += r.one_face_m
            c["corner_ext"] += r.ext_m[0] + r.ext_m[1]
            c["col_cut"] += r.col_cut_m
            c["crossings"] += sum(r.crossings)
            c["runs"] += 1
        led = defaultdict(float)
        seen = set()
        for r in rows_final:
            if r["floor"] != fl or not r["ledger_physical_m (Q-69 B)"]:
                continue
            key = r["ledger_row (T-108 r2)"] or r["row_id"]
            if key in seen:
                continue
            seen.add(key)
            led[f"{float(r['t_ledger_m']):.2f}"] += float(r["ledger_physical_m (Q-69 B)"])
        for k in sorted(set(comp) | set(led)):
            c = comp[k]
            tr = t225.get((fl, k), {})
            out.append({"floor": fl, "t_m": k, "census_runs": int(c["runs"]),
                        "ledger_physical_m (T-108 r2 rows)": f"{led.get(k, 0.0):.4f}",
                        "census_arch_run_m": f"{c['arch']:.4f}",
                        "census_minus_ledger_m": f"{c['arch'] - led.get(k, 0.0):+.4f}",
                        "census_both_faces_m (columns drawn through included)": f"{c['solid']:.4f}",
                        "census_column_cut_m": f"{c['col_cut']:.4f}", "census_openings_in_run_m": f"{c['openings']:.4f}",
                        "census_one_face_m": f"{c['one_face']:.4f}", "census_corner_extensions_m": f"{c['corner_ext']:.4f}",
                        "census_crossings_m": f"{c['crossings']:.4f}",
                        "census_junction_residual_m (one face + corners)": f"{c['one_face'] + c['corner_ext']:.4f}",
                        "t225_residual_m (engine physical - run A both faces - openings)": tr.get("residual_m", ""),
                        "curved_wall_entities_not_read": RESULTS_ARCS.get(fl, 0) if k == "0.20" else 0})
    return out


RESULTS_ARCS = {}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("dxf")
    ap.add_argument("capture")
    ap.add_argument("v2json")
    ap.add_argument("--dump", help="also write the band table and run pickle to this folder (outside the repository)")
    ap.add_argument("--check", action="store_true", help="compare with the committed tables instead of writing")
    a = ap.parse_args(argv)
    band_rows, row_out, summ, rows, t108 = build(a.dxf, a.capture, a.v2json)
    for fl, f in summ["floors"].items():
        RESULTS_ARCS[fl] = f["wall_arcs_not_read"]
    rf = final_rows(row_out, rows, t108)
    ft = floor_table(rf)
    st = defaultdict(int)
    for r in rf:
        st[r["status"]] += 1
    summ["rows"] = {"total": len(rf), **st}
    summ["causes"] = {k: sum(1 for r in rf if r["cause"] == k) for k in sorted({r["cause"] for r in rf if r["cause"]})}
    bands_csv = to_csv([{k: v for k, v in b.items()} for b in band_rows])
    outs = {OUT_ROWS: to_csv(rf), HERE / "T017_BY_FLOOR_THICKNESS.csv": to_csv(ft), OUT_BANDS: bands_csv,
            OUT_SUMMARY: json.dumps(summ, indent=1, sort_keys=True) + "\n"}
    if a.check:
        bad = [p.name for p, txt in outs.items() if not p.exists() or p.read_text() != txt]
        print("check:", "PASS" if not bad else "DIFFERS " + " ".join(bad))
        return 1 if bad else 0
    for p, txt in outs.items():
        p.write_text(txt)
    if a.dump:
        d = Path(a.dump)
        d.mkdir(parents=True, exist_ok=True)
        pickle.dump(row_out, open(d / "row_runs.pkl", "wb"))
    print(json.dumps(summ["rows"]), json.dumps(summ["causes"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
