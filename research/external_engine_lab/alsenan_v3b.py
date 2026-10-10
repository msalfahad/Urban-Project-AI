"""ALSENAN V3b - FULL-BOQ CANDIDATE (lab adapter, project-scoped; the decisions are in the generic engines).

Chain: the V3a build (alsenan_v3.build, unchanged) -> V3b layers:
    raster      calibrated elevations / sections (alsenan_v3b_raster)                      B11 / B04 / B05 / B14
    struct      slab binding, domes, residue, exterior GB, necks, F / F10, ground zones,
                blinding (both methods), pool, boundary wall, stairs, courtyard           B01-B07, B09, B10, B14
    rebar       inventory + hooks (code method) + BBS cutting on 12 m stock                B08 / B09
    finish      opening heights / areas, NET finishes + reveals, sequences, beads,
                facades, over-opening infill, paint under unbound beams                    B11-B14
    dual        Route B room areas from the DXF DIMENSION entities                         OC-V3B-D
Owner decisions OD-V3B-1..13 / OC-V3B-A..E (alsenan_v3b_owner_decisions.json) are the new authority.

    python3 research/external_engine_lab/alsenan_v3b.py <work_dir> <register_dir> [commit]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1]))

import alsenan_v3 as V3                                                                        # noqa: E402

PHASE = "ALSENAN_P7757_ST7757_V3B_FULL_BOQ_CANDIDATE"
DECISIONS = HERE / "alsenan_v3b_owner_decisions.json"


def layers(ctx) -> dict:
    import alsenan_v3_registers as REGS
    import alsenan_v3b_dual as DU
    import alsenan_v3b_finish as F
    import alsenan_v3b_raster as R
    import alsenan_v3b_rebar as RB
    import alsenan_v3b_struct as ST
    raster = R.run()
    st, ar = ST._doc(ctx, "ST7757.dxf"), ST._doc(ctx, "P7757.dxf")
    S = {"slab": ST.slab_rebar(ctx, st), "domes": ST.domes(ctx, st, ar, raster), "residue": ST.residue(ctx),
         "ext_gb": ST.ext_ground_beams(ctx), "necks": ST.necks(ctx), "f_f10": ST.f_f10(ctx),
         "pool": ST.pool(ctx, st, raster), "boundary_wall": ST.boundary_wall(ctx, st, raster), "stairs": ST.stairs(ctx)}
    gz = ST.ground_zones(ctx)
    S["blinding"] = ST.blinding(ctx, gz, S["ext_gb"], S["f_f10"])
    S["courtyard"] = ST.courtyard(ctx, st, gz)
    S["ground_zones"] = {k: v for k, v in gz.items() if k != "_fp"}
    sets = RB.inventory(ctx, st) + RB.extra_sets(ctx, S)
    w = RB.weigh(sets)
    rebar = {"weighed": w, "population": RB.population_register(w), "cutting": RB.cutting(w)}
    H = F.opening_heights(ctx, raster)
    oa = F.opening_areas(ctx, H)
    nf = F.net_finishes(ctx, H, oa)
    v3a = REGS.lines(ctx)
    fin = {"heights": H, "areas": oa, "net": nf, "facades": F.facades(ctx, H, oa), "over_openings": F.over_openings(ctx, oa),
           "paint_blocked": F.paint_blocked(ctx, nf), "parapet_faces": F.parapet_faces(v3a)}
    dual = DU.rooms(ctx, ar)
    return {"raster": raster, "struct": S, "rebar": rebar, "finish": fin, "dual": dual,
            "external": {"courtyard": S["courtyard"]}, "v3a_lines": v3a}


def build(work, commit=None) -> dict:
    ctx = V3.build(work, commit)
    ctx["v3b"] = layers(ctx)
    return ctx


def main(work, regdir, commit=None):
    import alsenan_v3b_registers as REGS
    ctx = build(work, commit)
    regs = REGS.registers(ctx)
    regdir = Path(regdir)
    regdir.mkdir(parents=True, exist_ok=True)
    for n, o in regs.items():
        (regdir / f"{n}.json").write_text(json.dumps(o, indent=1, ensure_ascii=False, default=REGS.jdefault) + "\n")
    print(json.dumps(REGS.summary(regs), indent=1, ensure_ascii=False, default=REGS.jdefault))
    return regs, ctx


if __name__ == "__main__":
    main(*sys.argv[1:4])
