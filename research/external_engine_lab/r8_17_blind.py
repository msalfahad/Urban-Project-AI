"""R8.17 lab: the BLIND Qortuba skirting run of the frozen WALL_CONTACT_PATH_POLICY_V4 + QORTUBA-NEW-SKIRTING-METHOD@v3
(with the owner's HALL / PAINTRY sliding-glass-door physical fact).

    python3 research/external_engine_lab/r8_17_blind.py <work> <skirting_out.json>

No expected value, no historical total, no target (93.98682 / 94.13682 / 96.73682 / 96.88682 / 84.795214 / 76.389 /
9.091605 / 0.15 / 2.75 are never read). Topology is the R8.16 closure-V2 run, untouched.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

import r8_14_qortuba as R14                                                                   # noqa: E402
import r8_15_skirting_blind as SB                                                             # noqa: E402
from engine.source import opening_facts as OPF, owner_facts as OF, owner_method_facts as MF   # noqa: E402
from engine.source import wall_contact_path as WC                                             # noqa: E402

FZ_FILE = ROOT / "tests/r8_17/registers/R8_17_V4_FREEZE.json"
PHYS = ROOT / "data/registry/OWNER_PHYSICAL_FACTS.json"
SLIDE = "QORTUBA-NEW-HALL-PAINTRY-SLIDING-GLASS-DOOR-OWNER-001"
WINDOWS_FACT = ("QORTUBA-NEW-NORMAL-WINDOWS-ABOVE-FLOOR-OWNER-001", 1)
handle = R14.handle


def method(fz):
    m = fz["qortuba_method"]
    return WC.SkirtingMethodV3(m["method_id"], m["version"], m["authority"], **m["parameters"])


def slide_contact(inp):
    f = OF.from_record(next(x for x in json.loads(PHYS.read_text())["facts"] if x["fact_id"] == SLIDE))
    b = OF.bind(f, inp)
    return f, b, OPF.contact_map(f, b)


def floor_contact_map(res, inp, dry_sites, slide_map):
    """Physical class FIRST (a bound door is never a window), then the scoped sill fact for hosted glazing, else
    unproven."""
    w = next(MF.from_record(x) for x in json.loads(R14.METHOD.read_text())["facts"]
             if (x["fact_id"], x["version"]) == WINDOWS_FACT)
    wb = MF.bind(w, inp)
    sites = {s["site_id"]: s for s in res["sites"]}
    out, windows = dict(slide_map), []
    for sid, zones in dry_sites:
        for e in WC.site_edges(res["_arr"], sites[sid]):
            if WC.GLAZING_ROLE not in e["roles"] and not any(s.startswith("CLOSURE|GLAZED|") for s in e["sources"]):
                continue
            door = [slide_map.get(s) or slide_map.get(WC._entity(s)) for s in e["sources"]]
            door = [d for d in door if d]
            closure = any(s.startswith("CLOSURE|") for s in e["sources"])
            walls = set(e["roles"]) - {WC.GLAZING_ROLE}
            hosted = not closure and bool(walls) and walls <= set(WC.WALL_ROLES)
            if door:
                st = door[0]
            elif hosted and wb["binding"] == "APPLIES":
                st = WC.opening_contact(sill_m=w.statement["sill_height_m"], sill_authority=w.ref)
            else:
                st = WC.opening_contact()
            for s in e["sources"]:
                out.setdefault(s if s.startswith("CLOSURE|") else WC._entity(s), st)
            windows.append({"site": sid, "zones": zones, "sources": [handle(s) if not s.startswith("CLOSURE|") else s
                                                                     for s in e["sources"]],
                            "length_mm": round(e["length"] * inp.unit_native_to_mm, 1),
                            "hosted_on_wall_face_line": hosted, "floor_contact": st,
                            "class": WC.classify_v4(e, floor_contact_by_entity=out)})
    return out, windows, wb["binding"]


def skirting_record(res, inp, fz):
    eps = R14.Q11.TP.tolerances(R14.Q11.RT.max_abs_coordinate(inp.parts), inp.unit_native_to_mm)["eps_r"]
    u = inp.unit_native_to_mm / 1000
    dry, wet = SB.dry_and_wet_sites(res)
    _, states = SB.obstacle_states(res, inp)
    bands = {b["band_id"]: b for b in res["wall_bands"]["bands"]}
    sf, sb, smap = slide_contact(inp)
    gj = WC.glazed_door_jambs(res["closures"], {k: v for k, v in smap.items() if k.startswith("GLAZED|")})
    jambs = [j for p in res["passages"] for j in WC.passage_jambs(p, bands, eps)] + \
        WC.door_jambs(res["openings"], res["closures"]) + gj
    fcm, windows, wb = floor_contact_map(res, inp, dry, smap)
    m = method(fz)
    sites = {s["site_id"]: s for s in res["sites"]}
    per, tot = {}, []
    for sid, zones in dry:
        r = WC.measure_v4(WC.site_edges(res["_arr"], sites[sid]), m, jambs=jambs, eps=eps, obstacle_authority=states,
                          floor_contact_by_entity=fcm)
        per[sid] = {"zones": zones, "state": r["state"], "payable_lm": round(r["length"] * u, 6),
                    "components_lm": {k: round(v * u, 6) for k, v in r["components"].items()},
                    "excluded_lm": {k: round(v * u, 6) for k, v in r["excluded"].items()},
                    "withheld": [dict(w, length_lm=round(w["length"] * u, 6)) for w in r["withheld"]],
                    "continuity_under_windows": [dict(c, length_lm=round(c["length"] * u, 6))
                                                 for c in r["continuity_under_windows"]],
                    "jambs": [{"opening": j["opening"], "kind": j["kind"], "side": j.get("side"),
                               "source": j.get("source"), "end_kind": j.get("end_kind"), "physical": j["physical"],
                               "length_lm": round(j["length"] * u, 6), "counted_lm": round(j["counted"] * u, 6),
                               "why": j.get("why")} for j in r["jambs_counted"]],
                    "opening_side_annotations": [{"opening": j["opening"], "side": j.get("side"),
                                                  "source": j.get("source"), "end_kind": j.get("end_kind"),
                                                  "overlap_lm": round(j["overlap"] * u, 6), "consumed_lm": 0.0}
                                                 for j in r["opening_side_annotations"]],
                    "conservation": {k: (round(v * u, 6) if isinstance(v, float) else v)
                                     for k, v in r["conservation"].items()}}
        tot.append(r["length"] * u)
    for sid, zones, why in wet:
        per[sid] = {"zones": zones, "state": WC.NO_SKIRTING, "payable_lm": 0.0, "class": why}

    def agg(key, c):
        return round(math.fsum(v.get(key, {}).get(c, 0.0) for v in per.values()), 6)
    comps = (WC.REAL_WALL_FACE, WC.COLUMN_FACE, WC.AUTHORISED_OBSTACLE_FACE, WC.WINDOW_ABOVE_FLOOR,
             WC.PHYSICAL_OPENING_JAMB)
    excl = (WC.DOOR_PRESENT, WC.SLIDING_GLAZED_DOOR_TO_FLOOR, WC.TOPOLOGY_CLOSURE, WC.FULL_HEIGHT_GLAZED,
            "DOOR_JAMB", "DOORLESS_JAMB_NOT_COUNTED")
    withheld = [dict(w, site=s) for s, v in per.items() for w in v.get("withheld", [])]
    return {"method": m.ref, "policy": [WC.POLICY_ID_V4, WC.policy_record_v4()["digest"]],
            "sliding_door_fact": {"fact": sf.ref, "binding": sb["binding"], "parts": sb["parts"],
                                  "glazed_door_jambs": [{"opening": j["opening"], "length_lm": round(j["length"] * u, 6),
                                                         "skirting_lm": 0.0} for j in gj]},
            "windows_fact": {"fact": f"{WINDOWS_FACT[0]}@v{WINDOWS_FACT[1]}", "binding": wb}, "windows": windows,
            "per_site": per, "PAYABLE_LM": round(math.fsum(tot), 6),
            "components_lm": {c: agg("components_lm", c) for c in comps},
            "excluded_lm": {c: agg("excluded_lm", c) for c in excl}, "withheld": withheld,
            "withheld_lm": round(math.fsum(w["length_lm"] for w in withheld), 6),
            "conservation_all_sites": all(v.get("conservation", {}).get("reconciles", True) for v in per.values()),
            "state": "COMPUTED_WITH_WITHHELD_SPANS" if withheld else "COMPUTED",
            "jamb_records": [{k: (v if k != "segment" else [[round(c, 4) for c in q] for q in v]) for k, v in j.items()}
                             for j in jambs]}


def main(work, skirting_out):
    fz = json.loads(FZ_FILE.read_text())
    R = R14.R13.runs(work, None)
    new, inp_new = R["new"], R["inputs"]["NEW_K2"]
    sk = {"SCHEMA": "URBAN_R8_17_SKIRTING_V4_BLIND_RESULT_V1", "freeze": fz["frozen_commit"],
          "wall_contact_path_policy": fz["wall_contact_path_policy"],
          "blind": {"expected_value_given": False, "historical_totals_used": False, "r8_16_values_read": False},
          "run_input_digest": new["run_manifest"]["RUN_INPUT_DIGEST"], **skirting_record(new, inp_new, fz)}
    Path(skirting_out).write_text(json.dumps(sk, indent=1, ensure_ascii=False, default=str) + "\n")
    print(json.dumps({"PAYABLE_LM": sk["PAYABLE_LM"], "withheld_lm": sk["withheld_lm"], "state": sk["state"],
                      "components": sk["components_lm"], "excluded": sk["excluded_lm"],
                      "conservation": sk["conservation_all_sites"]}, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:3])
