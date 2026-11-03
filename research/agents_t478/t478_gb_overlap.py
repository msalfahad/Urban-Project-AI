"""T-478 own check of F-C-T445-2 (values only): the ground-beam blinding strips against the pit layer by PLAN OVERLAP,
on route G's own geometry (ROUTE_G_SCOPE_V1 blinding_scope, footprint REACH, the same call ARCH_TAKEOFF_V3.0.2 makes).
Recomputes the held range 4.949374 .. 9.422514 m3 and states the overlap area the merged low end nets.

    .work/venv/bin/python -I research/agents_t478/t478_gb_overlap.py <structural.dxf>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import generic_route as GR  # noqa: E402
from engine.source import route_g_scope_v1 as SC  # noqa: E402
from tools import urban_boq_m2 as M2  # noqa: E402

CONV = ROOT / "engine/profiles/URBAN_M8_GENERIC_CONVENTIONS_V6.json"
M4 = ROOT / "research/urban_engine_m4_correctness/profile_st7757_m4.json"


def main(dxf):
    R = M2.compute([dxf], conventions=str(CONV), profile=str(M4), route="G", completeness=False)
    rc = SC.blinding_scope(R, footprint="REACH")
    gb = next(r for r in rc["records"] if r["family"] == "GROUND_BEAM")
    D, conv = R["generic"]["D"], R["conv"]
    p, t = GR._trip(conv, "BLINDING_PROJECTION_M")[1], GR._trip(conv, "BLINDING_THICKNESS_M")[1]
    u = D["unit_m"]
    pn = p / u
    state, shift, _ = GR._register_on_foundation(D)
    F = []
    for rec in SC._sheets(D, "FOUNDATION_PLAN"):
        for f in rec.get("footings", []):
            dims = SC._footing_dims(f, conv)
            if dims and f.get("box") and f.get("drawn_m") and list(dims) == list(f["drawn_m"][:2]) and \
                    state == "REGISTERED":
                F.append(SC._quad(f["box"], pn))
    Fp = list(F)                                   # the placed (outlined) footings' grown plans only
    F += SC._reach_windows(D, state, u, p, pn)[0]
    S, free = [], 0.0
    for rec in sorted(D["sheets"].values(), key=lambda r: r["sheet"]["sheet_id"]):
        if rec["sheet"]["role"] != "GROUND_BEAM_PLAN":
            continue
        sid = rec["sheet"]["sheet_id"]
        bpoly = {x["band_id"]: x for x in rec.get("bands", [])}
        for b in rec.get("beams", []):
            q = GR._strip_outline(b, bpoly.get(b["band_id"]), pn, *shift[sid]) if (state == "REGISTERED" and sid in
                                                                                    shift) else None
            if q is None:
                free += b["net_plan_m2"] + 2 * p * b["length_m"]
            else:
                S.append(q)
    uF, uS, uFS = SC._union(F) * u * u, SC._union(S) * u * u, SC._union(F + S) * u * u
    ov = uS + uF - uFS
    uFp, uFpS = SC._union(Fp) * u * u, SC._union(Fp + S) * u * u
    ovp = uS + uFp - uFpS
    print(json.dumps({"route_g_ground_beam_record": {k: gb.get(k) for k in ("status", "exposure_m3", "members",
                                                                             "column_footprints_in_strips_m2",
                                                                             "low_merged_m3", "high_own_layer_m3")},
                      "t": t, "p": p, "strips": len(S), "free_strip_m2": round(free, 6),
                      "pit_layer_m2 (incl. REACH windows)": round(uF, 6), "strips_union_m2": round(uS, 6),
                      "strips_over_pit_layer_m2": round(ov, 6), "merged_low_recomputed_m3": round((uFS - uF + free) * t, 6),
                      "overlap_m3_at_t": round(ov * t, 6),
                      "placed_footings_layer_m2": round(uFp, 6), "strips_over_placed_footings_m2": round(ovp, 6),
                      "strips_over_reach_windows_only_m2": round(ov - ovp, 6)}, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
