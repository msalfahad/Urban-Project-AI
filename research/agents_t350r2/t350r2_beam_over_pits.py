"""T-350 r2 own read (values only): the ground-beam blinding strips (band +- the p.13 projection 0.10, route G's own
geometry registered on the foundation plan, the same call ARCH_TAKEOFF_V3.0.2 / T-478 make) against the 24 pit neat
plans (outlined footings grown 0.10), PER RUN, so the pit / trench overlaps Vo (main exterior runs, blinding -0.10 ..
0.00) and Va (annex runs, below EG on D-34 / D-33 / D-35) are areas, not names.

    .work/venv/bin/python -I research/agents_t350r2/t350r2_beam_over_pits.py <structural.dxf>   (prints JSON; writes
    BEAM_OVER_PITS_T350R2.csv beside this file: run id, route G piece, lengths, strip m2, overlap m2; no coordinates)
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from shapely.geometry import Polygon  # noqa: E402
from shapely.ops import unary_union  # noqa: E402

from engine.source import generic_route as GR  # noqa: E402
from engine.source import route_g_scope_v1 as SC  # noqa: E402
from tools import urban_boq_m2 as M2  # noqa: E402

CONV = ROOT / "engine/profiles/URBAN_M8_GENERIC_CONVENTIONS_V6.json"
M4 = ROOT / "research/urban_engine_m4_correctness/profile_st7757_m4.json"
HERE = Path(__file__).resolve().parent
# frozen sheet frames of the structural DXF (research/agents_t141/run_t141_alsenan.py GBP / FP)
GBP = (78929.89653886131, 29036.09943562183, 114124.2067251332, 57066.43175431111)
GBPX0, FPX0 = GBP[0], 117654.3026476346
PLOT_HANDLE = "1658"                    # the plot rectangle on the foundation sheet (31.37 x 15.00 = 470.55 m2, T-357)
UPPER_GB = ("7FC", "7FE", "810")        # the upper boundary G.B at N.G. runs (T-253 7FC#1, 7FE#1..3, 810#1)


def _key(b):
    return "+".join(sorted(format(int(h.split(":")[1]), "X") for h in b["handles"]))


def main(dxf):
    R = M2.compute([dxf], conventions=str(CONV), profile=str(M4), route="G", completeness=False)
    D, conv = R["generic"]["D"], R["conv"]
    p = GR._trip(conv, "BLINDING_PROJECTION_M")[1]
    u = D["unit_m"]
    pn = p / u
    state, shift, _ = GR._register_on_foundation(D)
    assert state == "REGISTERED", state
    t170 = json.loads((ROOT / "research/agents_t170/ALSENAN_EXCAVATION_INPUT.json").read_text())["footings"]
    # route G works in its own frame: one translation to the raw foundation-sheet frame of the T-170 ledger, taken
    # from the one footing with a unique drawn size (F8 4.00 x 3.60) and then checked on every footing (residual mm)
    feet = [f for rec in SC._sheets(D, "FOUNDATION_PLAN") for f in rec.get("footings", [])
            if f.get("box") and f.get("drawn_m") and SC._footing_dims(f, conv) and
            list(SC._footing_dims(f, conv)) == list(f["drawn_m"][:2])]
    f8r = next(t for t in t170 if t["type"] == "F8")
    f8g = [f for f in feet if sorted(round(v, 3) for v in f["drawn_m"][:2]) == [3.6, 4.0]]
    assert len(f8g) == 1
    bx = f8g[0]["box"]
    ox = (bx[0] + bx[2]) / 2 - (f8r["x0_mm"] + f8r["dx_mm"] / 2)
    oy = (bx[1] + bx[3]) / 2 - (f8r["y0_mm"] + f8r["dy_mm"] / 2)
    pits, pitH, res_mm, other = [], [], [], []
    for f in feet:
        bx = f["box"]
        cx, cy = (bx[0] + bx[2]) / 2 - ox, (bx[1] + bx[3]) / 2 - oy
        dist = lambda t: abs(t["x0_mm"] + t["dx_mm"] / 2 - cx) + abs(t["y0_mm"] + t["dy_mm"] / 2 - cy)  # noqa: E731
        m = min(t170, key=dist)
        res_mm.append(round(dist(m), 1))
        if m["type"] in ("FF", "F10/F"):
            other.append((m["type"], Polygon(SC._quad(bx, pn))))
            continue
        pits.append(Polygon(SC._quad(bx, pn)))
        pitH.append((m["type"], m["schedule_L_W_H_m"][2]))
    PU = unary_union(pits)
    import math
    import ezdxf
    msp = ezdxf.readfile(dxf).modelspace()
    to_g = lambda pts: [(x + (FPX0 - GBPX0) + ox, y + oy) for x, y in pts]  # noqa: E731  GB sheet raw -> route G
    plot = None
    for e in msp.query("LWPOLYLINE[layer=='S-BOUN']"):
        pts = [tuple(p[:2]) for p in e.get_points()]
        if e.dxf.handle == PLOT_HANDLE:                  # on the foundation sheet: raw foundation frame
            plot = Polygon([(x + ox, y + oy) for x, y in pts])
            plot_raw = [round(min(x for x, _ in pts), 3), round(min(y for _, y in pts), 3),
                        round(max(x for x, _ in pts), 3), round(max(y for _, y in pts), 3)]
    assert plot is not None and abs(plot.area * u * u - 470.55) < 0.01
    # pool envelope (T-189 frame -> raw foundation frame by F8's corner -> route G), outer r + 0.10 (T-320 A10)
    pool = json.loads((ROOT / "research/agents_t189/ALSENAN_OVERLAP_INPUT.json").read_text())["pool"]
    from shapely.geometry import Point, box
    r, bxp = pool["outline"]["r_outer"], pool["outline"]["back_x"]
    d_ = Point(0, 0).buffer(r, quad_segs=256).intersection(box(-r, -r, 0, r)).union(box(0, -r, bxp, r))
    env = d_.buffer(0.10, quad_segs=256)
    ex_, ey_ = f8r["x0_mm"] / 1000 - pool["F8"]["x"][0], f8r["y0_mm"] / 1000 - pool["F8"]["y"][0]
    from shapely import affinity
    env = affinity.translate(affinity.scale(affinity.translate(env, ex_, ey_), 1000, 1000, origin=(0, 0)), ox, oy)
    Z = PU.intersection(plot).difference(env)
    ENV_BY_PIT = [(pitH[i][0], round(P.intersection(env).area * u * u, 6), round(P.intersection(env).difference(plot).area * u * u, 6), round(P.difference(plot).area * u * u, 6), [round(v) for v in P.bounds]) for i, P in enumerate(pits) if P.intersection(env).area > 0]
    DBG = {"beyond_plot_m2": round(PU.difference(plot).area * u * u, 6), "pits_in_env_m2": round(PU.intersection(env).area * u * u, 6), "pits_in_env_and_beyond_m2": round(PU.intersection(env).difference(plot).area * u * u, 6), "env_m2": round(env.area * u * u, 6), "env_beyond_plot_m2": round(env.difference(plot).area * u * u, 6)}
    order = sorted(range(len(pits)), key=lambda i: -pitH[i][1])
    ZP, taken = [], None
    for i in order:
        part = pits[i].intersection(Z)
        if taken is not None:
            part = part.difference(taken)
        taken = part if taken is None else taken.union(part)
        if part.area > 0:
            ZP.append((pitH[i][0], pitH[i][1], part))
    t253 = {r["item"]: r for r in csv.DictReader(open(ROOT / "research/agents_t253/LEDGER_T253.csv"))}
    for r in csv.DictReader(open(ROOT / "research/agents_t242/LEDGER_T242.csv")):
        if r["component"] == "GB-INTERIOR" and r["run"] not in t253:
            t253[r["run"]] = {"item": r["run"], "component": f"GB-INTERIOR {r['part']}", "L_m": r["L_m"],
                              "reasons": r["reasons"], "titles": r["titles"]}
    rows = []
    for rec in sorted(D["sheets"].values(), key=lambda r: r["sheet"]["sheet_id"]):
        if rec["sheet"]["role"] != "GROUND_BEAM_PLAN":
            continue
        sid = rec["sheet"]["sheet_id"]
        bpoly = {x["band_id"]: x for x in rec.get("bands", [])}
        seq = {}
        for b in rec.get("beams", []):
            k = _key(b)
            seq[k] = seq.get(k, 0) + 1
            q = GR._strip_outline(b, bpoly.get(b["band_id"]), pn, *shift[sid])
            if q is None:
                poly = b.get("polygon")
                if not poly:
                    rows.append({"piece": f"{k}#{seq[k]}", "kind": b["kind"], "L_routeG_m": round(b["length_m"], 4),
                                 "strip_m2": None, "over_pits_m2": None, "note": "no outline: not netted"})
                    continue
                dx, dy = shift[sid]
                Bm = Polygon([(x + dx, y + dy) for x, y in poly])
                Bm = Bm if Bm.is_valid else Bm.buffer(0)
                S = Bm.buffer(pn, join_style=2)          # the ends grow by p too: an upper bound of the strip
                rows.append({"piece": f"{k}#{seq[k]}", "kind": b["kind"], "L_routeG_m": round(b["length_m"], 4),
                             "strip_m2": round(S.area * u * u, 6), "over_pits_m2": round(S.intersection(Z).area * u * u, 6),
                             "beam_over_pits_m2": round(Bm.intersection(Z).area * u * u, 6),
                             "pits": " ".join(f"{t}:{H}:{round(S.intersection(P).area * u * u, 6)}:"
                                              f"{round(Bm.intersection(P).area * u * u, 6)}" for t, H, P in ZP
                                              if S.intersects(P) and S.intersection(P).area > 0),
                             "note": "arc: strip = band buffered by p (ends grown too: upper bound); beam = band"})
                continue
            S = Polygon(q)
            Bm = Polygon(GR._strip_outline(b, bpoly.get(b["band_id"]), 0.0, *shift[sid]))
            per = [(t, H, round(S.intersection(P).area * u * u, 6), round(Bm.intersection(P).area * u * u, 6))
                   for t, H, P in ZP if S.intersects(P)]
            per = [x for x in per if x[2] > 1e-9]
            rows.append({"piece": f"{k}#{seq[k]}", "kind": b["kind"], "L_routeG_m": round(b["length_m"], 4),
                         "strip_m2": round(S.area * u * u, 6), "over_pits_m2": round(S.intersection(Z).area * u * u, 6),
                         "beam_over_pits_m2": round(Bm.intersection(Z).area * u * u, 6),
                         "min_H_under_m": min((x[1] for x in per), default=""),
                         "pits": " ".join(f"{t}:{H}:{a}:{bm}" for t, H, a, bm in per), "note": ""})
            gb_sid, gb_shift = sid, shift[sid]
    # upper boundary G.B at N.G. (S-BOUN bands on the ground-beam sheet, p.14 20 x 40 wholly -0.40 .. 0.00)
    from engine.source import generic_route as _g  # noqa: F401
    boun = []
    for e in msp.query("LWPOLYLINE[layer=='S-BOUN']"):
        pts = [tuple(p[:2]) for p in e.get_points()]
        if not (GBP[0] <= pts[0][0] <= GBP[2] and GBP[1] <= pts[0][1] <= GBP[3]):
            continue
        if e.dxf.handle not in UPPER_GB:
            continue
        Pb = Polygon(to_g(pts))
        if not Pb.is_valid:
            Pb = Pb.buffer(0)
        boun.append({"handle": e.dxf.handle, "plan_m2": round(Pb.area * u * u, 6),
                     "over_pits_m2": round(Pb.intersection(Z).area * u * u, 6),
                     "pits": " ".join(f"{t}:{H}:{round(Pb.intersection(P).area * u * u, 6)}"
                                      for t, H, P in ZP if Pb.intersection(P).area > 1e-6)})
    # bind to the T-253 / T-242 run ids (handle pair + piece order)
    alias = {"114+115+7DF": "114+7DF"}
    by = {r["piece"]: r for r in rows}
    for item, r in t253.items():
        if not r["component"].startswith(("GB-EXTERIOR", "GB-INTERIOR")):
            continue
        h, n = item.split("#") if "#" in item else (item.split(":", 1)[1], "1")
        rr = by.get(f"{alias.get(h, h)}#{n}")
        if rr:
            rr.update({"run": item, "component": r["component"].split(" (")[0].split(" at ")[0],
                       "reasons": r.get("reasons", ""), "titles": r.get("titles", ""),
                       "L_t253_m": float(r["L_m"]), "dL_m": round(rr["L_routeG_m"] - float(r["L_m"]), 4)})
    out = {"pit_union_m2_unclipped": round(PU.area * u * u, 6), "zone_plan_m2": round(Z.area * u * u, 6),
           "zone_parts_m2": round(sum(P.area for _, _, P in ZP) * u * u, 6), "pits": len(pits), "p": p,
           "main_ext": {}, "annex_ext": {}}
    out["boundary_upper"] = boun
    out["pit_types_H"] = sorted(set(pitH))
    out["pit_match_residual_mm_max"] = max(res_mm)
    out["zone_checks"] = DBG
    out["pits_in_pool_envelope"] = ENV_BY_PIT
    out["frame_offset_mm"] = [round(ox, 3), round(oy, 3)]
    out["excluded_pits"] = [t for t, _ in other]
    for grp, tag in (("main_ext", "GB-EXTERIOR MAIN"), ("annex_ext", "GB-EXTERIOR ANNEX"),
                     ("annex_int", "GB-INTERIOR ANNEX"), ("main_int", "GB-INTERIOR MAIN")):
        sel = [r for r in rows if r.get("component", "").startswith(tag)]
        out[grp] = {"runs_bound": len(sel), "over_pits_m2": round(sum(r["over_pits_m2"] or 0 for r in sel), 6),
                    "beam_over_pits_m2": round(sum(r.get("beam_over_pits_m2") or 0 for r in sel), 6),
                    "length_mismatch_runs": [(r["run"], r["dL_m"]) for r in sel if abs(r["dL_m"]) > 0.001]}
    with open(HERE / "BEAM_OVER_PITS_T350R2.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["run", "component", "reasons", "titles", "piece", "kind", "L_t253_m",
                                           "L_routeG_m", "dL_m", "strip_m2", "over_pits_m2", "beam_over_pits_m2",
                                           "min_H_under_m", "pits", "note"], lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in w.fieldnames})
    out["plot_rect_raw_mm"] = plot_raw
    (HERE / "ZONE_INPUT_T350R2.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
