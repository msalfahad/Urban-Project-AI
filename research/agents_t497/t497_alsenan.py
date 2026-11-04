"""T-497 on the development villa: the external main ground-beam TRENCH (B1-02, cut for the blinding only, 0.10 m below
the existing ground) re-measured under EXCAVATION_ZONE_OWNERSHIP_V1 (R-T497-1): the trench owns only the ground no other
excavation zone digs, in the plot and beyond it.

Inputs (all merged, Checker-verified, none re-typed): the structural DXF (Drive 'Alsenan chalet project' / 'ST7757 dxf.dxf',
decoded into .work/private; sha256 prefix 9f9d1179 checked by t484.read) read with the T-484 functions (MERGED 12395ea4,
Verifier Gate A 2026-11-03 09:56): the 24 pits grown 0.10 (blinding projection), the pool envelope (T-189 frame via
t350r2), the F10F outline 1B1B and its S02 readings (F10 alone, F10 + F union, drawn outline; T-484 f10f), the FF lift
raft outline, the MAIN_EXT ground-beam strips (T-484 pieces: the run categories of the merged T-350 r2 BEAM_OVER_PITS
table; columns removed) and the plot line 1658.

Dig order (deeper / earlier first; ELEMENT_REGISTER ruling EXCAVATION ZONES): pool envelope, footing pits, F10F, FF,
then the trench. Each S02 reading of F10F is ONE scenario with ONE consistent set of zone plans (owner 2026-11-02).

    .work/venv/bin/python -I research/agents_t497/t497_alsenan.py .work/private/ST7757.dxf
      -> summary_t497.json beside this file (areas and volumes only; no handle list, no coordinate)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RES = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(RES / "agents_t484"))

from shapely.geometry import box  # noqa: E402
from shapely.ops import unary_union  # noqa: E402

import t484_alsenan as T  # noqa: E402
import zone_ownership_v1 as Z  # noqa: E402

TRENCH_DEPTH = T.BLINDING            # 0.10 m: the ext main GB is cut for its blinding only (RULE MAIN_EXT BLINDING_ONLY)
PIT_DEPTH = -T.LIMIT + T.D_S01       # 1.67 m (S01 ESTIMATED, owner-accepted): pits and F10F
# merged figures this re-measure must reproduce (T-484 summary / V3.0.48 inputs; Checker F-C-T350R4-1)
_S484 = json.loads((RES / "agents_t484/summary_t484.json").read_text())
T484 = dict(_S484["ext_gb_trench"]["own_strip"], zone_plan_m2=_S484["zone_plan_m2"],
            outline_plan_m2=_S484["f10f"]["outline_plan_m2"])
V3048_TRENCH = (1.203269, 1.432834)
CHECKER_DRAWN_OUTLINE = (1.069269, 1.176467)


def _r(x):
    return round(x + 0.0, 6)


def _pieces(d, cols, zone, pits, ftype, union):
    """The T-484 beam pieces exactly as the merged code builds them (captured from its own call, then restored)."""
    cap = {}
    orig = T.R.beam_solid_bounds

    def keep(pieces, *a, **k):
        cap.setdefault("pieces", pieces)
        return orig(pieces, *a, **k)
    T.R.beam_solid_bounds = keep
    try:
        bm = T.beams(d, cols, zone, pits, ftype, d["sched_ftg"], union=union)
    finally:
        T.R.beam_solid_bounds = orig
    return cap["pieces"], bm


def f10f_scenarios(d, ftype):
    """The S02 plans of the F10F zone, grown 0.10, NOT clipped (beyond-plot ground is ground too)."""
    h = next(h for h, t in ftype.items() if t[0] == ["F", "F10"])
    x0, y0, x1, y1 = d["ftg"][h].bounds
    W10, L10 = d["sched_ftg"]["F10"][:2]
    WF, LF = d["sched_ftg"]["F"][:2]
    g = lambda b: b.buffer(T.P, join_style=2)  # noqa: E731
    f10s = {"west": box(x0, y0, x0 + W10, y0 + L10), "east": box(x1 - W10, y0, x1, y0 + L10)}
    fs = {"south-west": box(x0, y0, x0 + WF, y0 + LF), "south-east": box(x1 - WF, y0, x1, y0 + LF),
          "north-west": box(x0, y1 - LF, x0 + WF, y1), "north-east": box(x1 - WF, y1 - LF, x1, y1)}
    sc = {"drawn outline": g(d["ftg"][h])}
    for k, b in f10s.items():
        sc[f"F10 alone {k}"] = g(b)
    for k, b in f10s.items():
        for j, f in fs.items():
            sc[f"F10 {k} + F {j} (union)"] = unary_union([g(b), g(f)])
    return sc


def run(dxf):
    d = T.read(dxf)
    ftype = T.footing_types(d)
    pits, union, env, zone = T.pits_and_zone(d, ftype)
    assert len(pits) == 24, len(pits)
    cols = unary_union(list(d["cols"].values()))
    pieces, bm = _pieces(d, cols, zone, pits, ftype, union)
    ext = unary_union([p["strip"] for p in pieces if p["cat"] == "MAIN_EXT"]).difference(cols)
    plot = d["plot"]
    # reproduce the merged T-484 strip before anything new
    eo = bm["main_ext_own"]
    for k in ("strip_total_m2", "beyond_plot_m2", "in_zone_m2"):
        assert abs(eo[k] - T484[k]) < 1e-6, (k, eo[k])
    assert abs(zone.area - T484["zone_plan_m2"]) < 1e-6, zone.area
    ff = unary_union([d["ftg"][h].buffer(T.P, join_style=2) for h, t in ftype.items() if t[0] == ["FF"]])
    scen = f10f_scenarios(d, ftype)
    rows = {}
    for name, f10f in scen.items():
        own = Z.own_plans([("pool envelope", env), ("footing pits", union), ("F10F", f10f), ("FF lift raft", ff),
                           ("ext main GB trench", ext)], plot)
        t = own["ext main GB trench"]
        pi, pb = own["footing pits"]["in_plot_m2"], own["footing pits"]["beyond_plot_m2"]
        assert abs(pi - T484["zone_plan_m2"]) < 1e-6, ("pits own plan moved", pi)   # pits line unchanged
        fi = own["F10F"]["in_plot_m2"]
        vin, vby = Z.strip_volume(t, TRENCH_DEPTH)
        rows[name] = {"trench_in_plot_m2": _r(t["in_plot_m2"]), "trench_beyond_plot_m2": _r(t["beyond_plot_m2"]),
                      "trench_given_up_m2": {k: _r(v) for k, v in t["given_up_m2"].items()},
                      "trench_given_up_in_plot_m2": {k: _r(o["own"].intersection(ext).intersection(plot).area)
                                                     for k, o in own.items() if k != "ext main GB trench"},
                      "trench_m3": [_r(vin), _r(vin + vby)],
                      "f10f_in_plot_m2": _r(fi), "f10f_m3": _r(fi * PIT_DEPTH),
                      "pits_in_plot_m2": _r(pi), "pits_beyond_plot_m2": _r(pb),
                      "trench_plus_f10f_m3": [_r(vin + fi * PIT_DEPTH), _r(vin + vby + fi * PIT_DEPTH)]}
    do = rows["drawn outline"]
    assert abs(scen["drawn outline"].intersection(plot).area - T484["outline_plan_m2"]) < 1e-6
    f10f_all = [min(r["f10f_m3"] for r in rows.values()), max(r["f10f_m3"] for r in rows.values())]
    line = do["trench_m3"]
    # the line sum (F10F all-scenario range + trench at the drawn outline) must bound every consistent scenario total
    total_bound = [_r(f10f_all[0] + line[0]), _r(f10f_all[1] + line[1])]
    cons = [min(r["trench_plus_f10f_m3"][0] for r in rows.values()),
            max(r["trench_plus_f10f_m3"][1] for r in rows.values())]
    assert total_bound[0] <= cons[0] + 1e-9 and cons[1] <= total_bound[1] + 1e-9, (total_bound, cons)
    tr_all = [min(r["trench_m3"][0] for r in rows.values()), max(r["trench_m3"][1] for r in rows.values())]
    return {"method": Z.METHOD_ID, "rule": f"{Z.RULE_ID} {Z.RULE_VERSION}", "dxf_sha8": d["sha8"],
            "dig_order": ["pool envelope", "footing pits", "F10F", "FF lift raft", "ext main GB trench"],
            "depths_m": {"trench": TRENCH_DEPTH, "pits_and_f10f": round(PIT_DEPTH, 4)},
            "reproduced_t484": {k: eo[k] for k in ("strip_total_m2", "beyond_plot_m2", "in_zone_m2")},
            "pool_envelope_over_trench_m2": _r(ext.intersection(env).area),
            "ff_over_trench_m2": _r(ext.intersection(ff).area),
            "scenarios": rows,
            "trench_line_m3_drawn_outline": line,
            "checker_drawn_outline_m3": list(CHECKER_DRAWN_OUTLINE),
            "v3048_trench_m3": list(V3048_TRENCH),
            "trench_all_scenarios_m3": tr_all,
            "scenario_residual_m3": {"in plot, F10F reading other than the drawn outline (up to)":
                                     _r(max(r["trench_m3"][0] for r in rows.values()) - line[0]),
                                     "with beyond plot (up to)": _r(tr_all[1] - line[1])},
            "f10f_m3_all_scenarios": [_r(x) for x in f10f_all],
            "excavation_held_bound_m3": {"v3048": [_r(f10f_all[0] + V3048_TRENCH[0]), _r(f10f_all[1] + V3048_TRENCH[1])],
                                         "restated": total_bound, "consistent_scenarios": [_r(x) for x in cons]}}


if __name__ == "__main__":
    res = run(sys.argv[1])
    (HERE / "summary_t497.json").write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")
    print(json.dumps({k: res[k] for k in ("trench_line_m3_drawn_outline", "checker_drawn_outline_m3",
                                          "trench_all_scenarios_m3", "scenario_residual_m3",
                                          "excavation_held_bound_m3")}, indent=1))
