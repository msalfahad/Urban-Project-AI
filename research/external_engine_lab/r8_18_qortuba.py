"""R8.18 lab: Qortuba AFTER the frozen R8.18 blind run - the R8.17 assembly (rows, V4 skirting regression, R8.17 wall
faces), the frozen R8.18 run recomputed (must equal the blind record), and the rebuild with ONE disclosed wiring
correction of the blind script (WF2-L1: a reveal face must be drawn by an admitted WALL / STRUCTURAL part - the blind
check accepted any layer, so a FIXTURE line closed the PAINTRY-side south jamb of the sliding door).

    python3 research/external_engine_lab/r8_18_qortuba.py <work> <register_dir> [code_commit]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

import r8_17_qortuba as R17                                                                   # noqa: E402
import r8_18_blind as BL                                                                      # noqa: E402
from engine.source import wall_contact_path as WC                                             # noqa: E402

REG18 = ROOT / "tests/r8_18/registers"


def jl(p):
    return json.loads(Path(p).read_text())


def norm(x):
    return json.loads(json.dumps(x, default=str))


def wall_parts(res, inp):
    """Parts admitted as wall / structural boundary in the certified arrangement (the only legitimate reveal faces)."""
    keys = {s for e in res["_arr"].edges if set(e["roles"]) & set(WC.WALL_ROLES) for s in e["sources"]}
    return [p for p in inp.parts if p.identity.key in keys]


def rebuild(res, inp, fz):
    """The frozen run with the WF2-L1 correction: `drawn` reads admitted wall / structural parts only."""
    orig = BL.drawn
    walls = wall_parts(res, inp)
    BL.drawn = lambda _parts, a, b, eps: orig(walls, a, b, eps)
    try:
        return norm(BL.run(res, inp, fz))
    finally:
        BL.drawn = orig


def diff_reveals(a, b):
    ka = {(x["opening"], x["surface"], x.get("owner_site")): x for x in a["reveals"]}
    kb = {(x["opening"], x["surface"], x.get("owner_site")): x for x in b["reveals"]}
    return [{"reveal": list(k), "blind": {f: ka[k].get(f) for f in ("finish", "area_m2", "depth_basis")},
             "rebuild": {f: kb[k].get(f) for f in ("finish", "area_m2", "depth_basis")}}
            for k in sorted(ka) if k in kb and (ka[k].get("finish"), ka[k].get("area_m2")) !=
            (kb[k].get("finish"), kb[k].get("area_m2"))]


def build(work, commit=None):
    ctx = R17.build(work, commit)
    new, inp = ctx["new"], ctx["inp_new"]
    fz = jl(REG18 / "R8_18_FREEZE.json")
    blind = jl(REG18 / "WALL_FACE_V2_BLIND_RESULT.json")
    again = norm(BL.run(new, inp, fz))
    keys = ("heights", "per_site", "reveals", "trade_rows", "waterproofing", "double_count_guard")
    ctx["reproduces_r8_18_blind"] = {k: again[k] == blind[k] for k in keys}
    rb = rebuild(new, inp, fz)
    ctx["r8_18"] = rb
    ctx["r8_18_blind"] = blind
    ctx["r8_18_freeze"] = fz
    ctx["blind_vs_rebuild"] = {
        "reveal_differences": diff_reveals(blind, rb),
        "trade_row_differences": {t: {"blind": {k: blind["trade_rows"][t].get(k) for k in
                                                ("AUTHORISED_SUBTOTAL_M2", "wet_service_owned_reveal_plaster_m2")},
                                      "rebuild": {k: rb["trade_rows"][t].get(k) for k in
                                                  ("AUTHORISED_SUBTOTAL_M2", "wet_service_owned_reveal_plaster_m2")}}
                                  for t in rb["trade_rows"]},
        "cause": "WF2-L1: the blind reveal-face check accepted ANY drawn segment; the PAINTRY-side south jamb of the "
                 "sliding door is covered only by H480 (layer FIXTURE, not admitted as wall) - the rebuild reads "
                 "admitted wall / structural parts only",
        "engine": "identical frozen policies in both"}
    ctx["skirting_v4_vs_r8_17"] = {"payable": ctx["skirting_v4"]["PAYABLE_LM"] ==
                                   jl(ROOT / "tests/r8_17/registers/SKIRTING_REGISTER.json")["SKIRTING_LM"]}
    return ctx


def main(work, regdir, commit=None):
    import r8_18_registers as REGS
    regs, ctx = REGS.registers(build(work, commit))
    regdir = Path(regdir)
    regdir.mkdir(parents=True, exist_ok=True)
    for n, o in regs.items():
        (regdir / f"{n}.json").write_text(json.dumps(o, indent=1, ensure_ascii=False, default=str) + "\n")
    print(json.dumps({t: (v["state"], v["AUTHORISED_SUBTOTAL_M2"]) for t, v in ctx["r8_18"]["trade_rows"].items()} |
                     {"waterproofing": ctx["r8_18"]["waterproofing"]["totals"]}, indent=1))
    return regs, ctx


if __name__ == "__main__":
    main(*sys.argv[1:4])
