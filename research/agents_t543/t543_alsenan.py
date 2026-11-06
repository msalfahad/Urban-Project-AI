"""T-543 development-villa run (research, unwired): the B9 blockwork reconciliation table, R-T543-1.

    .work/venv/bin/python -I research/agents_t543/t543_alsenan.py [--write]

Reads merged repository files only (t543_inputs); prints the table; --write stores out/T543_BLOCKWORK_RECONCILE.json.
"""
from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import t543_inputs as I  # noqa: E402
import t543_reconcile as R  # noqa: E402

OUT = HERE / "out" / "T543_BLOCKWORK_RECONCILE.json"


def parapet_decomposition(runs: list[dict], his_m2: Decimal) -> dict:
    c_hi = sum((Decimal(r["centreline_hi"]) for r in runs), Decimal(0))
    ba = sum((Decimal(r["block_alt_hi_m2"]) for r in runs), Decimal(0))
    rc = sum((Decimal(r["centreline_hi"]) * Decimal("0.30") for r in runs), Decimal(0))
    face = sum((Decimal(r["centreline_hi"]) * Decimal(r["h_hi"]) for r in runs), Decimal(0))
    rnd = face - ba - rc                            # stored block-alternative prints (6 dp) vs c x (h - 0.30)
    assert abs(rnd) < Decimal("0.00001"), rnd
    rows = [
        {"name": "parapet face above the RC upstand: block ALTERNATIVE (material HELD, Q-65 C designer), upper end",
         "delta": str(ba), "cause": "HELD", "walls": [], "basis": f"{I.S_PARAPET}: sum of 25 runs [0, c x (h - 0.30)]"},
        {"name": "RC upstand 0.30 m above the slab on every run (concrete, STR.CONC.PARAPET; never masonry)",
         "delta": str(rc), "cause": "ENGINE_RIGHT", "walls": [], "basis": f"{I.S_P1}; centreline {c_hi} m x 0.30"},
    ]
    rows.append({"name": "print rounding of the stored block alternatives (6 dp)", "delta": str(rnd),
                 "cause": "TOLERANCE", "walls": [], "basis": "face above finish - block alternative - RC upstand"})
    resid = his_m2 - face
    rows.append({"name": "RESIDUAL: parapet height below the finished roof (b_edge, HELD D-39) + length census",
                 "delta": str(resid), "cause": "UNRESOLVED", "walls": [],
                 "basis": f"engine runs above finish {face} m2 on {c_hi} m centreline; b_edge x {c_hi} m stays HELD"})
    return {"rows": rows, "centreline_hi_m": str(c_hi), "face_above_finish_hi_m2": str(face)}


def build() -> dict:
    I.freelancer_check()
    lines = I.engine_lines()
    valued = [ln for ln in lines if ln["qty"] is not None]
    held_lines = [ln for ln in lines if ln["qty"] is None]
    assert sum(Decimal(ln["qty"]) for ln in valued) == Decimal(I.ENGINE_RELEASED_M2)
    walls = I.engine_walls()
    # per floor x thickness: register valued == line index valued (no stale, no double)
    chk: dict[tuple, Decimal] = {}
    for w in walls:
        if w["valued_m2"] is not None:
            k = (w["floor"], Decimal(w["t_m"]).normalize())
            chk[k] = chk.get(k, Decimal(0)) + Decimal(w["valued_m2"])
    lchk: dict[tuple, Decimal] = {}
    for ln in valued:
        fl = ln["element_id"].split("-WALLS")[0]
        t = Decimal(ln["element_id"].split("t=")[1].split("#")[0]).normalize()
        lchk[(fl, t)] = lchk.get((fl, t), Decimal(0)) + Decimal(ln["qty"])
    assert chk == lchk, (chk, lchk)

    comps = []
    for fl in I.FLOORS:
        fw = [w for w in walls if w["floor"] == fl]
        dec = R.floor_decomposition(floor=fl, his=I.FREELANCER_FLOOR[fl], walls=fw)
        ev = Decimal(dec["engine_valued_m2"])
        comps.append({"name": f"{fl} storey walls (net of openings)",
                      "engine_valued_m2": None if ev == 0 and all(w["valued_m2"] is None for w in fw) else str(ev),
                      "engine_status": "HELD (all walls, D-39)" if all(w["valued_m2"] is None for w in fw)
                      else "PARTIAL (valued walls; the others in the split)",
                      "his_m2": dec["his_net_m2"],
                      "his_basis": f"his external + 15 cm + 20 cm wall rows: L {dec['L_his']} m, H {dec['H_his']} m",
                      "cause": "SPLIT", "decomposition": dec, "source": f"{I.S_LINES}; {I.S_V4}; {I.S_V2}"})
    nw = I.FREELANCER_NON_WALL
    comps.append({"name": "boundary wall (his 15 cm section)", "engine_valued_m2": None,
                  "engine_status": "booked in EXT.FENCE.* (not MAS.BLOCK)", "his_m2": nw["BOUNDARY_WALL"][0],
                  "his_basis": "one row, length x 2.00, no opening", "cause": "RULE_DIFFERENCE",
                  "source": f"{I.S_LINES}: EXT.FENCE.WALL F-STREET 14.84 + F-NORTH 83.1305 valued, F-SEA / F-LOWER HELD",
                  "note": "family placement; the quantity is compared under the fence family, not here"})
    par_his = Decimal(nw["PARAPET_1F_ROW"][0]) + Decimal(nw["PARAPET_ROOF_ROW"][0]) + Decimal(nw["ROOF_ROW_UNLABELLED"][0])
    pdec = parapet_decomposition(I.parapet_runs(), par_his)
    comps.append({"name": "parapets (his 15 cm section: three rows)", "engine_valued_m2": None,
                  "engine_status": "STR.CONC.PARAPET HELD BLANK x 4; block alternative records [0, x]",
                  "his_m2": str(par_his), "his_basis": "three rows at 1.00 / 1.80 / 1.00 m, total length 138.65 m",
                  "cause": "SPLIT", "decomposition": pdec, "source": I.S_PARAPET,
                  "note": "his unlabelled 29.80 m row = 2 x (8.100 + 6.800), the +13.90 roof's outer parapet faces "
                          "(T-541 handles): a parapet, not a wall"})
    comps.append({"name": "1F 'projections' row (his external section)", "engine_valued_m2": None,
                  "engine_status": "no masonry element identified", "his_m2": nw["PROJECTIONS_1F"][0],
                  "his_basis": "one row 7.50 x 5.50, no opening", "cause": "UNRESOLVED",
                  "source": "freelancer row; no engine element (MAS.BLOCK carries none)",
                  "note": "physical element not identified this run (facade feature on the 1F elevation?)"})
    comps.append({"name": "his 20 cm openings with no floor", "engine_valued_m2": None,
                  "engine_status": "engine deducts openings inside each wall",
                  "his_m2": str(-Decimal(I.FREELANCER_20CM_OPENINGS_NO_FLOOR)), "his_deduction": True,
                  "his_basis": "4 openings deducted in his 20 cm section, floor not printed", "cause": "UNRESOLVED",
                  "source": "freelancer section deduction", "note": "belongs to one of the three storey rows"})
    res = R.partition(freelancer_total=I.FREELANCER_TOTAL, engine_valued_lines=valued, components=comps,
                      engine_only_held=[{"name": ln["element_id"], "engine_status": ln["class"],
                                         "line_id": ln["line_id"], "engine_valued_m2": None,
                                         "note": "HELD blank; below-ground masonry (T-407), not in his sheet"}
                                        for ln in held_lines if ln["element_id"].startswith("HOUSE_BELOW_NG")])
    assert sum(Decimal(r["difference_m2"]) for r in res["rows"]) == Decimal(res["gap"])
    assert sum(Decimal(v) for v in res["by_cause"].values()) == Decimal(res["gap"])
    res["method"] = "R-T543-1"
    res["candidate"] = "ARCH_TAKEOFF_V3.0.58"
    res["engine_held_lines"] = [{"line_id": ln["line_id"], "element_id": ln["element_id"]} for ln in held_lines]
    res["freelancer_printed"] = I.FREELANCER_PRINTED
    return res


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    res = build()
    print("his", res["freelancer_total"], "engine valued", res["engine_valued_total"], "gap", res["gap"])
    for r in res["rows"]:
        print(f"  {r['name']:<45} his {r['his_m2']:>10} eng {str(r['engine_valued_m2']):>10} diff {r['difference_m2']:>12} {r['cause']}")
        if r["decomposition"]:
            for x in r["decomposition"]["rows"]:
                print(f"      {Decimal(x['delta']):>14.6f} {x['cause']:<16} {x['name']}")
    print("by cause:", res["by_cause"])
    if "--write" in argv:
        OUT.parent.mkdir(exist_ok=True)
        OUT.write_text(json.dumps(res, indent=1, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        print("written", OUT.relative_to(HERE.parents[1]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
