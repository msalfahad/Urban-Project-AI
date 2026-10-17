"""R8.15 lab: the BLIND Qortuba run of the frozen WALL_CONTACT_PATH_POLICY_V2 with the frozen Qortuba skirting method.

    python3 research/external_engine_lab/r8_15_skirting_blind.py <work> <out.json>

Inputs: the frozen V5 topology run, the dry tiled room sites (the class rule), the owner physical facts (duct
authority), the passage jamb faces. No expected value, no historical total, no target.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

import r8_14_qortuba as Q                                                                      # noqa: E402
from engine.source import obstacle_authority as OA, owner_facts as OF, wall_contact_path as WC  # noqa: E402

FZ = json.loads((ROOT / "tests/r8_15/registers/R8_15_SKIRTING_FREEZE.json").read_text())
PHYS = ROOT / "data/registry/OWNER_PHYSICAL_FACTS.json"


def method():
    m = FZ["qortuba_method"]
    return WC.SkirtingMethod(m["method_id"], m["version"], m["authority"], **m["parameters"])


def physical_facts():
    return [OF.from_record(f) for f in json.loads(PHYS.read_text())["facts"]]


def obstacle_states(res, inp):
    bound = [(f, OF.bind(f, inp)) for f in physical_facts()]
    auth = OA.entity_authority(res["wall_bands"]["isolated_loops"], bound)
    return auth, {k: v["state"] for k, v in auth.items()}


def jamb_segments(res):
    return [tuple(map(tuple, j["segment"])) for p in res.get("passages") or [] for j in p.get("jamb_faces", [])]


def run(res, inp, dry_sites, wet_sites, *, eps):
    u = inp.unit_native_to_mm / 1000
    auth, states = obstacle_states(res, inp)
    js = jamb_segments(res)
    sites = {s["site_id"]: s for s in res["sites"]}
    m = method()
    per, total, cf_passage = {}, [], []
    for sid, zones in dry_sites:
        edges = WC.site_edges(res["_arr"], sites[sid])
        kw = {"obstacle_authority": states, "jamb_segments": js, "eps": eps}
        meas = WC.measure(edges, m, **kw)
        phys = WC.physical_path(edges, **kw)
        per[sid] = {"zones": zones, "class": "DRY_INTERNAL_ROOM (tiled floor)", "state": meas["state"],
                    "lm": None if meas["length"] is None else round(meas["length"] * u, 6),
                    "components_lm": {k: round(v * u, 6) for k, v in meas["components"].items()},
                    "excluded_lm": {k: round(v * u, 6) for k, v in meas["excluded"].items()},
                    "withheld": meas["withheld"],
                    "physical_path_lm": {k: {"edges": v["edges"], "lm": round(v["length"] * u, 6)}
                                         for k, v in phys["by_class"].items()},
                    "floor_contact_lm": round(phys["floor_contact_length"] * u, 6)}
        if meas["length"] is not None:
            total.append(meas["length"] * u)
        cf_passage.append(meas["excluded"].get(WC.OPENING_JAMB, 0.0) * u)
    for sid, zones, why in wet_sites:
        edges = WC.site_edges(res["_arr"], sites[sid])
        meas = WC.measure(edges, m, full_wall_tile=True)
        per[sid] = {"zones": zones, "class": why, "state": meas["state"], "lm": 0.0,
                    "floor_contact_lm": round(WC.physical_path(edges, obstacle_authority=states, jamb_segments=js,
                                                               eps=eps)["floor_contact_length"] * u, 6)}
    complete = all(v["state"] in (WC.COMPUTED, WC.NO_SKIRTING) for v in per.values())
    return {"method": m.ref, "per_site": per, "complete": complete,
            "SKIRTING_LM": round(math.fsum(total), 6) if complete else None,
            "components_lm": {c: round(math.fsum(v["components_lm"].get(c, 0.0) for v in per.values()
                                                 if "components_lm" in v), 6)
                              for c in (WC.REAL_WALL_FACE, WC.COLUMN_FACE, WC.OBSTACLE_FACE)},
            "excluded_lm": {c: round(math.fsum(v["excluded_lm"].get(c, 0.0) for v in per.values()
                                               if "excluded_lm" in v), 6)
                            for c in (WC.DOOR_OPENING, WC.GLAZED_OPENING, WC.WINDOW_OPENING, WC.OPENING_JAMB,
                                      WC.TOPOLOGY_CLOSURE)},
            "passage_jamb_return_counterfactual_lm": round(math.fsum(cf_passage), 6),
            "obstacle_authority": auth}


def dry_and_wet_sites(res):
    names = Q.LAB.apartment_names()
    lab, internal = Q.LAB.apartment_sites(res)
    internal_ids = {s["site_id"] for s in internal}
    dry, wet = [], []
    for s in lab + internal:
        zn = [z for z in Q.Q10.site_zone_names(s, names, internal_ids) if z != "UNLABELLED_INTERNAL_SPACE"]
        cls = sorted({Q.R13.SPACE_CLASSES_V2.space_class(z) for z in zn} - {None})
        if cls == ["DRY_INTERNAL_ROOM"]:
            dry.append((s["site_id"], zn))
        elif cls:
            wet.append((s["site_id"], zn, f"{'/'.join(cls)} - full wall tile (no skirting: owner fact + US-02)"))
    return sorted(dry), sorted(wet)


def main(work, out):
    R = Q.R13.runs(work, None)
    res, inp = R["new"], R["inputs"]["NEW_K2"]
    eps = Q.Q11.TP.tolerances(Q.Q11.RT.max_abs_coordinate(inp.parts), inp.unit_native_to_mm)["eps_r"]
    dry, wet = dry_and_wet_sites(res)
    r = run(res, inp, dry, wet, eps=eps)
    rec = {"SCHEMA": "URBAN_R8_15_BLIND_QORTUBA_SKIRTING_V1", "freeze": FZ["frozen_commit"],
           "policy": FZ["wall_contact_path_policy"], "method": FZ["qortuba_method"]["ref"],
           "blind": {"expected_value_given": False, "historical_total_used": False, "qp10_compared": False,
                     "inputs": ["the frozen V5 topology run (new revision)", "the class rule (dry tiled rooms)",
                                "owner physical facts (duct authority)", "passage jamb faces"]},
           "run_input_digest": res["run_manifest"]["RUN_INPUT_DIGEST"], "eps_r": eps,
           "dry_sites": [s for s, _ in dry], "no_skirting_sites": [s for s, _, _ in wet], **r}
    Path(out).write_text(json.dumps(rec, indent=1, ensure_ascii=False, default=str) + "\n")
    print(json.dumps({k: rec[k] for k in ("SKIRTING_LM", "complete", "components_lm", "excluded_lm",
                                          "passage_jamb_return_counterfactual_lm")}, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:3])
