"""The P7757 wall-treatment estimate (§29-§33): per face, zone, floor, trade
and project, with a human-readable QS trace, floor summaries, parameter
sensitivity in scenario mode, and a freeze.

Everything here is arithmetic over the frozen traces, the recorded
declarations and the owner parameter registry. The established subtotals
are small and truthful; the unresolved scope is listed, never bridged.

    python3 -m research.qs_wall_treatment_01.build_estimate
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from engine import material_role_audit as MRA
from engine import wall_face_set as FS
from engine import wall_treatment_engine as E
from research.qs_wall_treatment_01 import declarations as D
from research.qs_wall_treatment_01 import faces_from_traces as F
from research.qs_wall_treatment_01 import owner_parameters as OP
from research.qs_wall_treatment_01 import protocol as P

OUT = Path(P.OUT_DIR)

SCENARIOS = {
    "NORMAL_HEIGHT_3.00": {"NORMAL_INTERNAL_PLASTER_HEIGHT": 3.00},
    "NORMAL_HEIGHT_3.40": {"NORMAL_INTERNAL_PLASTER_HEIGHT": 3.40},
    "DOOR_REVEAL_0.20": {"DOOR_REVEAL_DEPTH": 0.20},
}


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _num(x):
    return isinstance(x, (int, float))


def run_sets(reg_params: dict, trace_reg: dict, owners: dict, use_cad_lengths: bool = False) -> list:
    out = []
    for plan in D.FACE_SET_PLAN:
        inp = F.face_set_inputs(plan, trace_reg, owners, use_cad_lengths=use_cad_lengths)
        fs = FS.build_face_set(set_id=plan["SET_ID"], faces=inp["faces"],
                               openings=inp["openings"], trade=plan["TRADE"],
                               basis=plan["BASIS"], zone=plan["ZONE"], floor=plan["FLOOR"])
        floor_key = {"GROUND": "GROUND", "FIRST": "FIRST"}.get(plan["FLOOR"], plan["FLOOR"])
        sheet = E.calculate(fs, reg_params, treatment=plan["TRADE"], floor=floor_key)
        out.append({"PLAN": plan, "FACE_SET": fs, "SHEET": sheet})
    return out


def aggregate(results: list) -> dict:
    """Established subtotals only are summed; provisional stays apart; a
    total is never claimed."""
    def agg(keyf):
        g = {}
        for r in results:
            k = keyf(r)
            res = r["SHEET"]["RESULT"]
            a = g.setdefault(k, {"ESTABLISHED_SUBTOTAL_M2": 0.0, "PROVISIONAL_SUBTOTAL_M2": 0.0,
                                 "SETS": [], "COVERAGE_STATUS": "NONE",
                                 "COMPLETE_TOTAL_STATUS": "NOT_ESTABLISHED",
                                 "UNRESOLVED_SCOPE": []})
            a["SETS"].append(r["PLAN"]["SET_ID"])
            if _num(res["ESTABLISHED_SUBTOTAL_M2"]):
                a["ESTABLISHED_SUBTOTAL_M2"] = round(
                    a["ESTABLISHED_SUBTOTAL_M2"] + res["ESTABLISHED_SUBTOTAL_M2"], 4)
                a["COVERAGE_STATUS"] = "PARTIAL"
            if _num(res["PROVISIONAL_SUBTOTAL_M2"]):
                a["PROVISIONAL_SUBTOTAL_M2"] = round(
                    a["PROVISIONAL_SUBTOTAL_M2"] + res["PROVISIONAL_SUBTOTAL_M2"], 4)
                if a["COVERAGE_STATUS"] == "NONE":
                    a["COVERAGE_STATUS"] = "PARTIAL"
            a["UNRESOLVED_SCOPE"] += [{"SET_ID": r["PLAN"]["SET_ID"], **u}
                                      for u in res["UNRESOLVED_SCOPE"]]
        for a in g.values():
            a["THE_ESTABLISHED_SUBTOTAL_IS_NOT_THE_TOTAL"] = True
        return g
    return {
        "BY_ZONE_AND_TRADE": {f"{k[0]}|{k[1]}|{k[2]}": v for k, v in agg(
            lambda r: (r["PLAN"]["FLOOR"], r["PLAN"]["ZONE"], r["PLAN"]["TRADE"])).items()},
        "BY_FLOOR_AND_TRADE": {f"{k[0]}|{k[1]}": v for k, v in agg(
            lambda r: (r["PLAN"]["FLOOR"], r["PLAN"]["TRADE"])).items()},
        "BY_FLOOR": agg(lambda r: r["PLAN"]["FLOOR"]),
        "BY_TRADE": agg(lambda r: r["PLAN"]["TRADE"]),
        "PROJECT": agg(lambda r: "P7757")["P7757"],
    }


def qs_trace_md(results: list, aggr: dict, reg_params: dict) -> str:
    L = ["# P7757 wall-treatment estimate - QS trace", "",
         "Every number below is the product of numbers also shown. Established "
         "subtotals are NOT totals: coverage is a traced subset of the building, "
         "and unresolved scope is listed, not estimated.", "",
         "## Parameters used", ""]
    for pid in ("NORMAL_INTERNAL_PLASTER_HEIGHT", "EXTERNAL_STOREY_HEIGHT_GROUND",
                "EXTERNAL_STOREY_HEIGHT_FIRST", "EXTERNAL_STOREY_HEIGHT_SECOND_ROOF_ROOM",
                "DOOR_WIDTH", "DOOR_HEIGHT", "WINDOW_WIDTH", "WINDOW_HEIGHT",
                "DOOR_REVEAL_DEPTH", "WINDOW_REVEAL_DEPTH", "DOUBLE_HEIGHT_PLASTER_HEIGHT",
                "STAIR_WELL_PLASTER_HEIGHT", "TARTUSHA_HEIGHT", "STEEL_PROFILE_RULE",
                "CONTROL_JOINT_RULE"):
        p = reg_params[pid]
        L.append(f"- `{pid}` = {p['VALUE']} {p['UNIT'] or ''} - {p['SOURCE_TYPE']} "
                 f"({p['STATUS']})")
    for r in results:
        pl, fs, sh = r["PLAN"], r["FACE_SET"], r["SHEET"]
        L += ["", f"## {pl['SET_ID']} - {pl['FLOOR']} / {pl['ZONE']} / {pl['TRADE']}", "",
              f"Basis `{pl['BASIS']}` on sheet `{pl['SHEET']}` (case {pl['CASE']}). "
              f"Coverage: {fs['COVERAGE_STATUS']}; complete total: {fs['COMPLETE_TOTAL_STATUS']}.",
              ""]
        for k in ("DOUBLE_HEIGHT_STATUS", "OPEN_PLAN_NOTE", "EXTERNAL_EXPOSURE_NOTE",
                  "HEIGHT_NOTE", "NOTE"):
            if pl.get(k):
                L.append(f"- {k}: {pl[k]}")
        L += ["", "| line | id | length m | h/w m | calc | m2 | provenance |",
              "|---|---|---|---|---|---|---|"]
        for ln in sh["SHEET"]:
            t = ln["LINE"]
            if t.endswith("_FACE") and t != "UNRESOLVED_FACE" and t != "EXCLUDED_FACE":
                hk = "WIDTH_M" if "WIDTH_M" in ln else "HEIGHT_M"
                L.append(f"| {t} | {ln['FACE_ID']} ({ln['MATERIAL_ROLE']}) | {ln['LENGTH_M']} "
                         f"| {ln.get(hk)} | {ln['CALC']} | {ln['AREA_M2']} | "
                         f"L:{ln['LENGTH_SOURCE']} ({ln.get('LENGTH_BASIS')}), "
                         f"{hk[0]}:{ln.get(hk.replace('_M', '_SOURCE'))} |")
            elif t == "UNRESOLVED_FACE":
                L.append(f"| UNRESOLVED | {ln['FACE_ID']} | - | - | - | - | {ln['WHY']} |")
            elif t == "EXCLUDED_FACE":
                L.append(f"| EXCLUDED | {ln['FACE_ID']} ({ln['MATERIAL_ROLE']}) | - | - | - | 0 | {ln['WHY']} |")
            elif t in ("DEDUCTION",):
                L.append(f"| DEDUCTION | {ln['OPENING_ID']} {ln['TYPE']} | {ln['WIDTH_M']} | "
                         f"{ln['HEIGHT_M']} | {ln['CALC']} | -{ln['AREA_M2']} | "
                         f"w:{ln['WIDTH_SOURCE']}, h:{ln['HEIGHT_SOURCE']} |")
            elif t == "UNRESOLVED_OPENING":
                L.append(f"| UNRESOLVED_OPENING | {ln['OPENING_ID']} | - | - | - | - | {ln['WHY']} |")
            elif t == "REVEAL":
                L.append(f"| REVEAL | {ln['OPENING_ID']} | girth {ln['GIRTH_M']} | depth {ln['DEPTH_M']} "
                         f"| {ln['CALC']} | {ln['AREA_M2']} (separate) | {ln['DEPTH_SOURCE']} |")
            elif t in ("ESTABLISHED_SUBTOTAL", "PROVISIONAL_SUBTOTAL",
                       "REVEALS_AND_RETURNS_SUBTOTAL"):
                L.append(f"| **{t}** | | | | {ln.get('CALC', '')} | **{ln['AREA_M2']}** | "
                         f"{sh['QUANTITY_STATE'].get(t.replace('_AND_RETURNS_SUBTOTAL', '_AND_RETURNS'), '')} |")
            elif t == "PROFILE_ELIGIBLE_EDGE" and ln["ELIGIBLE_LM"]:
                L.append(f"| PROFILE_ELIGIBLE | {ln['CATEGORY']} | | | | {ln['ELIGIBLE_LM']} lm | rule {ln['PROFILE_RULE']} |")
        L += ["", "Unresolved scope:"]
        for u in fs["UNRESOLVED_SCOPE"]:
            L.append(f"- {u['FACE_ID']}: {u['WHY']}")
        g = sh["DOUBLE_COUNT_GUARD"]
        L.append(f"\nDouble-count guard: {g['GUARD_STATUS']}")
    L += ["", "## Floor summaries (established subtotals only; never totals)", "",
          "| floor | trade | established m2 | provisional m2 (apart) | coverage | complete total |",
          "|---|---|---|---|---|---|"]
    for k, v in aggr["BY_FLOOR_AND_TRADE"].items():
        fl, tr = k.split("|")
        L.append(f"| {fl} | {tr} | {v['ESTABLISHED_SUBTOTAL_M2']} | {v['PROVISIONAL_SUBTOTAL_M2']} "
                 f"| {v['COVERAGE_STATUS']} | {v['COMPLETE_TOTAL_STATUS']} |")
    pr = aggr["PROJECT"]
    L += ["", f"Project established subtotal (all trades, traced subset): "
              f"**{pr['ESTABLISHED_SUBTOTAL_M2']} m2**; provisional apart: "
              f"{pr['PROVISIONAL_SUBTOTAL_M2']} m2; complete total: {pr['COMPLETE_TOTAL_STATUS']}.",
          "", "m2 and lm are never combined. Floors are not ceilings. Nothing here is a BOQ."]
    return "\n".join(L) + "\n"


def sensitivity(trace_reg: dict, owners: dict, base_params: dict, base_results: list,
                use_cad_lengths: bool = False) -> dict:
    base_proj = aggregate(base_results)["PROJECT"]["ESTABLISHED_SUBTOTAL_M2"]
    out = {"MODE": "SCENARIO_ONLY",
           "THE_OFFICIAL_PARAMETER_IS_NOT_CHANGED": True,
           "BASELINE_PROJECT_ESTABLISHED_SUBTOTAL_M2": base_proj, "SCENARIOS": {}}
    for name, changes in SCENARIOS.items():
        reg = json.loads(json.dumps(base_params))
        for pid, v in changes.items():
            reg[pid] = dict(reg[pid], VALUE=v, SCENARIO=True,
                            STATUS="SCENARIO_NOT_OFFICIAL")
        res = run_sets(reg, trace_reg, owners, use_cad_lengths)
        proj = aggregate(res)["PROJECT"]["ESTABLISHED_SUBTOTAL_M2"]
        out["SCENARIOS"][name] = {
            "CHANGES": changes,
            "PROJECT_ESTABLISHED_SUBTOTAL_M2": proj,
            "DELTA_M2": round(proj - base_proj, 4) if _num(proj) and _num(base_proj) else None,
            "PER_SET": {r["PLAN"]["SET_ID"]: r["SHEET"]["RESULT"]["ESTABLISHED_SUBTOTAL_M2"]
                        for r in res},
        }
    return out


def main(version: str = "", use_cad_lengths: bool = False) -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    sfx = f"_{version}" if version else ""
    trace_reg = F.load_register()
    owners_doc = json.loads((OUT / "DIMENSION_OWNER_REGISTER.json").read_text("utf-8"))
    owners = owners_doc["PER_CASE"]
    params = OP.p7757_registry()
    results = run_sets(params, trace_reg, owners, use_cad_lengths)
    aggr = aggregate(results)
    guard = MRA.guard_contributions([c for r in results for c in r["SHEET"]["CONTRIBUTIONS"]
                                     if c["BUCKET"] == "ESTABLISHED"])
    body = {
        "PHASE_ID": P.PHASE_ID, "ARTIFACT": f"P7757_WALL_TREATMENT_ESTIMATE{sfx}",
        "VERSION": version or "v1", "CAD_LENGTHS_USED": use_cad_lengths,
        "CAD_LENGTHS": ({f"{k[0]}/{k[1]}": v for k, v in D.CAD_LENGTHS.items()}
                        if use_cad_lengths else {}),
        "PROJECT_ID": P.PROJECT_ID,
        "TRACE_REGISTER_SHA256": _sha(Path(P.TRACE_REGISTER)),
        "PARAMETER_REGISTRY": params,
        "FACE_SET_PLAN": D.FACE_SET_PLAN,
        "DERIVED_LENGTHS": {f"{k[0]}/{k[1]}": v for k, v in D.DERIVED_LENGTHS.items()},
        "FACE_DIMENSIONS": {f"{k[0]}/{k[1]}": v for k, v in D.FACE_DIMENSIONS.items()},
        "SETS": results,
        "AGGREGATES": aggr,
        "PROJECT_DOUBLE_COUNT_GUARD": guard,
        "PARTIAL_QUANTITY_ARCHITECTURE": P.PARTIAL_QUANTITY_ARCHITECTURE,
        "COVERAGE_NOTE": ("the estimate covers the four frozen trace cases only; "
                          "every other zone of P7757 is outside the traced subset "
                          "and is not estimated"),
        "NOT_A_BOQ": True, "NO_FIREBASE_WRITE": True, "E1_4_CONSULTED": False,
        "BENCHMARK_OPENED": False,
    }
    p = OUT / f"P7757_WALL_TREATMENT_ESTIMATE{sfx}.json"
    p.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (OUT / f"QS_TRACE{sfx}.md").write_text(qs_trace_md(results, aggr, params), encoding="utf-8")
    sens = sensitivity(trace_reg, owners, params, results, use_cad_lengths)
    (OUT / f"SENSITIVITY{sfx}.json").write_text(json.dumps(sens, indent=2) + "\n", encoding="utf-8")
    return {
        "ESTIMATE_SHA256": _sha(p), "QS_TRACE_SHA256": _sha(OUT / f"QS_TRACE{sfx}.md"),
        "SENSITIVITY_SHA256": _sha(OUT / f"SENSITIVITY{sfx}.json"),
        "PROJECT": aggr["PROJECT"], "BY_TRADE": {
            k: (v["ESTABLISHED_SUBTOTAL_M2"], v["PROVISIONAL_SUBTOTAL_M2"], v["COVERAGE_STATUS"])
            for k, v in aggr["BY_TRADE"].items()},
        "GUARD": guard["GUARD_STATUS"],
        "SENSITIVITY": {k: v["PROJECT_ESTABLISHED_SUBTOTAL_M2"] for k, v in sens["SCENARIOS"].items()},
    }


if __name__ == "__main__":
    import sys
    v = sys.argv[1] if len(sys.argv) > 1 else ""
    print(json.dumps(main(version=v, use_cad_lengths=(v if v in ("v2", "v3") else False)), indent=2))
