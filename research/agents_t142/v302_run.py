"""T-142 read-only run: ARCH_TAKEOFF_V3.0.2 on the development villa's Drive copies (the architectural DXF from
P7757_DXF_COMPRESSED.zip and the structural "ST7757 dxf.dxf"), with the same project inputs, decision and history runs
as research/agents_t133/v301_run.py, the route G profile (required: Gate B defect D1) and the V3.0.2 project inputs
below (typed from the printed sheets, owner Q-17 A; every value names where it is printed and who checked it). Prints
the V3.0.2 rows (quantities, units, states and engine ids only: no coordinates, no names) and the totals. Every output
goes to --out (outside the repository).

    python3 -I research/agents_t142/v302_run.py <plan.dxf> <structural.dxf> --out <scratch>/t142 \
        --profile research/urban_engine_m4_correctness/profile_st7757_m4.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t131"))

import alsenan_v30_run as T131  # noqa: E402

CHECK_T127 = "T-127 MERGED 5315d48 (verifier 2026-10-21 04:10 UTC)"
INPUTS = {
    "schema": "URBAN_V302_PROJECT_INPUTS_V1", "project": T131.PID,
    "footing_rebar": {
        "size_unit": {"value": "cm", "source": "structural set p.9 'Schedule of Footings' header 'FOOTING SIZE (cm)'"},
        "cover": {"value_mm": 70.0, "wording": "MINIMUM",
                  "source": "structural set p.8 general note 22 (not less than 7 cm in concrete against soil)"},
        "end_treatment": {"BOTTOM": {"state": "STRAIGHT", "source": "structural set p.13 'TYP. DETAIL OF ISOLATED "
                                                                    "FOOTING' (long and short bottom bars straight)"},
                          "TOP": None},
        "checked_by": "T-136 MERGED 6d532c5 (verifier re-counted the schedule cells against the PDF)"},
    "soffits": {
        "finish_question": "Q-68 (answered C, option A provisional only)",
        "places": [
            {"place": "PL-01", "floor": "GF", "name_en": "entrance porch soffit (under the 1F block)", "m2": 19.181,
             "status": "DRAWING-VERIFIED", "evidence_status": "DRAWING-CONFIRMED",
             "drawing_reference": "architectural sheets 03 / 04, structural 1F slab plan: 4.60 x 4.096 + 4.40 x 0.20 + "
                                  "0.02 - 1.40 x 0.40",
             "verification": "T-121 hand 19.182, verifier CAD 19.198 (+0.09 %); not re-measured in " + CHECK_T127},
            {"place": "PL-02", "floor": "GF", "name_en": "side passage soffit", "m2": 5.640,
             "status": "DRAWING-VERIFIED", "evidence_status": "VERIFIED",
             "condition": "owner Q-67 A conditional: open to outside air, no enclosing door or glazing (met, T-123 "
                          "6699bb6, verifier run 45)",
             "drawing_reference": "architectural sheet 03: 1.560 + 0.240 + 3.600 + 0.240 (1.20 x 4.70), all roofed",
             "verification": "verifier T-123 (run 45) measured 5.640; " + CHECK_T127},
            {"place": "PL-03", "floor": "GF", "name_en": "pool court soffit", "m2": 12.834,
             "status": "DRAWING-VERIFIED", "evidence_status": "VERIFIED", "void_excluded_m2": 3.690,
             "drawing_reference": "architectural sheet 03 printed chain 1.800 x 5.400 + west bulge inside the printed "
                                  "657 line (6.8295) - column 0.025 = 16.5245 gross; less the drawn void inside the "
                                  "B7 ring inner faces (GF roof-slab sheet) 3.6901",
             "verification": "verifier re-measured 12.834 m2 (void 3.689); " + CHECK_T127},
            {"place": "PL-04", "floor": "1F", "name_en": "1F roof slab east edge beyond CB12", "m2": 4.374,
             "status": "DRAWING-VERIFIED", "evidence_status": "DRAWING-CONFIRMED",
             "drawing_reference": "structural 1F roof-slab plan, drawn slab faces 3.189 + 0.873 + 0.312",
             "verification": "T-121 CAD faces, verifier reproduced; " + CHECK_T127},
            {"place": "PL-05", "floor": "1F", "name_en": "1F roof slab west / north edge band 0.20 m", "m2": 2.417,
             "status": "DRAWING-VERIFIED", "evidence_status": "DRAWING-CONFIRMED",
             "drawing_reference": "structural 1F roof-slab plan, drawn slab faces (band about 12 m x 0.20)",
             "verification": "T-121 CAD faces, verifier reproduced; " + CHECK_T127}],
        "listed_apart": [
            {"id": "SX-01", "m2": 0.904, "what": "head soffit of the printed 4.521 m opening in the court's east "
                                                 "facade wall (4.521 x 0.200): with the opening reveals (M-11)"},
            {"id": "SX-02", "m2": 0.561, "what": "0.08 m recess between the curved pool frame and the printed 657 "
                                                 "band face: with the glazing reveal (M-11)"},
            {"id": "SX-03", "m2": 0.200, "what": "head soffit of the 1.00 m opening in the court's north facade wall: "
                                                 "with the opening reveals (M-11)"}]},
}


def q(x):
    if not x or x.get("state") is None:
        return "-"
    if x.get("value") is not None:
        return f"{x['value']:.4f} {x['state']}"
    if x.get("low") is not None:
        return f"{x['low']:.4f}..{x['high']:.4f} {x['state']}"
    return x["state"]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("plan")
    ap.add_argument("structural")
    ap.add_argument("--out", required=True)
    ap.add_argument("--profile", required=True, help="route G drawing profile (Gate B defect D1)")
    a = ap.parse_args(argv)
    from tools import urban_boq_m9 as M
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "facts.json").write_text(json.dumps(T131.facts(Path(a.plan).name), ensure_ascii=False), encoding="utf-8")
    common = T131.common_args(a, out)
    M.main(["arch", "--out", str(out / "v29"), "--method", "ARCH_TAKEOFF_V2.9"] + common)
    extra = ["--v30-released", str(out / "v29" / "BOQ_LINES.json")]
    hist = []
    for m in ("ARCH_TAKEOFF_V2.10", "ARCH_TAKEOFF_V2.11", "ARCH_TAKEOFF_V2.12"):
        tag = "v" + m.split("_V")[-1].replace(".", "")
        M.main(["arch", "--out", str(out / tag), "--method", m] + common)
        hist.append(f"{m}={out / tag / 'BOQ_LINES.json'}")
    (out / "decisions.json").write_text(json.dumps(T131.DECISIONS), encoding="utf-8")
    (out / "v302_inputs.json").write_text(json.dumps(INPUTS, ensure_ascii=False), encoding="utf-8")
    extra += ["--v30-history"] + hist + ["--v30-decisions", str(out / "decisions.json"),
                                         "--v302-inputs", str(out / "v302_inputs.json")]
    M.main(["arch", "--out", str(out / "v302"), "--method", "ARCH_TAKEOFF_V3.0.2"] + common + extra)
    led = json.loads((out / "v302" / "V3_0_2_INTEGRATION_LEDGER.json").read_text(encoding="utf-8"))
    run = json.loads((out / "v302" / "V3_0_2_RUN.json").read_text(encoding="utf-8"))
    print("identity:", json.dumps(run["identity"], indent=1))
    print("totals:", json.dumps(run["totals"], indent=1))
    print("evidence status:", run["evidence_status_counts"])
    for r in led["rows"]:
        if r["piece"] == "MEMBRANE_PROOF":
            continue
        print(f"{r['piece']:13s} {r['action']:8s} {r['item_code']:18s} {r['floor'] or '':10s} {r['unit']:3s} "
              f"{str(r['element_id'])[-46:]:46s} V2.9 {q(r['before_released_v2_9'])} | V3.0.1 {q(r['before_v3_0_1'])}"
              f" | V3.0.2 {q(r['after_v3_0_2'])} [{r['evidence_status']}]")
    for lg in run["piece_logs"]:
        if lg["piece"] == "MEMBRANE_PROOF":
            for x in lg["lines"]:
                print(f"rolls {x['floor']:4s} {str(x['room_id'])[-24:]:24s} {x['rolls']} {x['state']} {x['verdict']} "
                      f"layouts {x['layouts']} chosen {x['chosen_v2_13']} {x['why'] or ''}")
        elif lg["piece"] == "FOOTING_REBAR":
            print("footing steel:", json.dumps({k: lg.get(k) for k in ("state", "schedule_rows", "totals",
                                                                       "count_readings_kg", "check",
                                                                       "schedule_rows_without_footing")}))
            for o in lg.get("occurrences") or ():
                print("  ", o["mark"], o["status"], o["released_kg"], o["held_kg_range"], o["held_unquantified"],
                      o["route_lines"], "->", o["new_lines"])
        else:
            print(lg["piece"], json.dumps({k: v for k, v in lg.items() if k not in ("piece",)}, default=str)[:1500])
    return 0


if __name__ == "__main__":
    main()
