"""T-267 development-villa check (ST-01, the dog-leg stair GF -> 1F -> 2F) with ITS drawing facts only.

Reads research/agents_t267/ALSENAN_ST01_INPUT.json (dimensions, counts and levels already in the merged T-184 / T-214 /
T-258 research; no coordinates, names or drawing content) and runs engine/source/stair_finish_levels_v1.py twice:
DRAWING (the tread finish is printed nowhere: HELD) and OWNER_RULE_UP_STAIR_006 (0.030 m tread finish, ASSUMED - OWNER-
APPROVED, shown beside). No candidate or released line is read or changed.

    python3 -I research/agents_t267/t267_alsenan_check.py          print summary.json
    python3 -I research/agents_t267/t267_alsenan_check.py write    rewrite research/agents_t267/summary.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))

from engine.source import stair_finish_levels_v1 as M  # noqa: E402
from engine.source import stair_geometry as SG  # noqa: E402

# T-258 ledger values (research/agents_t258/LEDGER_T258.csv, MERGED): flight net (owner method) + parts owned by beams
T258 = {"MS1-U": {"net": 0.997552, "owned_elsewhere": 0.057261, "head": "B20"},
        "MS2-L": {"net": 1.033444, "owned_elsewhere": 0.025448, "head": "B20 (foot)"},
        "MS2-U": {"net": 1.001373, "owned_elsewhere": 0.057451, "head": "B23"}}


def load():
    return json.loads((HERE / "ALSENAN_ST01_INPUT.json").read_text(encoding="utf-8"))


def _r(x, p=4):
    return None if x is None else round(x, p)


def summary(doc):
    out = {"schema": "T267_ALSENAN_ST01_SUMMARY_V1", "policy_id": M.POLICY_ID, "runs": {}}
    for label, recs in doc["runs"].items():
        out["runs"][label] = {}
        for key, rec in recs.items():
            res = M.check_stair(rec)
            lv = res["levels"]
            rs = lv["risers"]
            out["runs"][label][key] = {
                "risers": lv["n_risers"], "finished_riser_mm": _r(lv["riser_mm"], 3),
                "first_structural_riser_mm": _r(rs[0]["structural_riser_mm"], 3),
                "last_structural_riser_mm": _r(rs[-1]["structural_riser_mm"], 3),
                "first_last_status": [rs[0]["status"], rs[-1]["status"]],
                "first_last_missing": sorted(set(rs[0]["missing"] + rs[-1]["missing"])),
                "closure": None if lv["closure"] is None else {k: (_r(v, 3) if isinstance(v, float) else v)
                                                               for k, v in lv["closure"].items()},
                "flights": [{"flight": g["flight"], "risers": g["risers"], "goings": g["goings"],
                             "configuration": g["configuration"],
                             "run_change_mm_at_280_300": None if not g["alternatives"] or "run_change_mm" not in g["alternatives"]
                             else [_r(v, 1) for v in g["alternatives"]["run_change_mm"]]} for g in res["goings"]],
                "findings": sorted({f["code"] for f in res["findings"]}),
                "lines": [{"component": x["component"], "part": x["part"], "unit": x["unit"],
                           "quantity": _r(x["quantity"], 6), "status": x["status"]} for x in res["lines"]
                          if x["component"] in ("CONCRETE", "MARBLE_LANDING", "HANDRAIL", "BARS")],
                "marble_tread_m2_measured": _r(sum(x["quantity"] for x in res["lines"]
                                                   if x["component"] == "MARBLE_TREAD" and x["status"] == M.MEASURED), 4),
                "marble_tread_held": sorted(x["part"] for x in res["lines"]
                                            if x["component"] == "MARBLE_TREAD" and x["status"] != M.MEASURED),
                "code": res["code"]["regulatory_status"], "code_applicability_decided": res["code"]["applicability_decided"]}
    # reconciliation of the gross flight sections with the merged T-258 ledger (owner-rule run, where finishes are known)
    rec = []
    own = {x["part"]: x for k in ("GF_1F", "1F_2F") for x in out["runs"]["OWNER_RULE_UP_STAIR_006"][k]["lines"]
           if x["component"] == "CONCRETE"}
    for f, t in T258.items():
        g = own.get(f"flight {f}")
        riser = 4500.0 / 27 if f == "MS1-U" else 4200.0 / 25         # section A-A counts (Q-46 A)
        ref = SG.straight_flight(12, riser, 300.0, 1200.0, 160.0)["STAIR_CONCRETE_VOLUME"] / 1e9   # 12 risers, 11 goings
        rec.append({"flight": f, "t267_gross_m3": g["quantity"], "frozen_straight_flight_m3": _r(ref, 6),
                    "t258_net_m3": t["net"], "t258_owned_elsewhere_m3": t["owned_elsewhere"],
                    "t258_net_plus_owned_m3": _r(t["net"] + t["owned_elsewhere"], 6),
                    "residual_m3": None if g["quantity"] is None else _r(g["quantity"] - t["net"] - t["owned_elsewhere"], 6)})
    out["reconciliation_t258"] = rec
    return out


def render(doc):
    return json.dumps(summary(doc), indent=1, sort_keys=True) + "\n"


if __name__ == "__main__":
    text = render(load())
    if sys.argv[1:] == ["write"]:
        (HERE / "summary.json").write_text(text, encoding="utf-8")
    print(text)
