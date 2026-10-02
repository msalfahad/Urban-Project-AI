"""R8.16 lab: the BLIND Qortuba run of the frozen DOOR_OPENING_CLOSURE_POLICY_V2 (topology) and the frozen
WALL_CONTACT_PATH_POLICY_V3 + QORTUBA-NEW-SKIRTING-METHOD@v2 (skirting).

    python3 research/external_engine_lab/r8_16_blind.py <work> <closure_out.json> <skirting_out.json>

No expected value, no historical total, no target (84.795214 / 9.091605 / 1.75 / 0.55 / 0.30 / 76.389 are never read).
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
from engine.source import owner_method_facts as MF, topology as T, wall_contact_path as WC     # noqa: E402

FZ_FILE = ROOT / "tests/r8_16/registers/R8_16_FREEZE.json"
WINDOWS_FACT = "QORTUBA-NEW-NORMAL-WINDOWS-ABOVE-FLOOR-OWNER-001"
handle = R14.handle


def method(fz):
    m = fz["qortuba_method"]
    return WC.SkirtingMethodV3(m["method_id"], m["version"], m["authority"], **m["parameters"])


def closure_record(res, inp):
    u = inp.unit_native_to_mm
    ops = {occ: {"closure_a": st.get("closure_a"), "closure_b": st.get("closure_b"),
                 "rule": st.get("closure_b_rule"), "blocked": st.get("closure_b_blocked"),
                 "evidence": st.get("closure_b_evidence"), "width_mm": round(st.get("width", 0) * u, 2),
                 "caps": [handle(x) for x in st.get("hits", [])]} for occ, st in sorted(res["openings"].items())}
    tcs = [{"closure_id": c["closure_id"], "release": c["release"], "geometry": [round(v, 4) for v in c["geometry"]],
            "evidence": sorted(map(handle, c["source_evidence_ids"])),
            "separated_m2": [round(p["area"] * res["_unit2"], 4)
                             for p in (c.get("safety") or {}).get("separated_pieces", [])]}
           for c in res["topology_closures"]["closures"]]
    labelled = sorted((sorted({v for vs in R14.LAB.stamps(s).values() for v in vs}), round(s["area_m2"], 4))
                      for s in res["sites"] if R14.LAB.stamps(s))
    return {"run_input_digest": res["run_manifest"]["RUN_INPUT_DIGEST"],
            "door_closure_policy": res["run_manifest"]["policies"]["door_opening_closure"],
            "openings": ops, "closure_b_rules": {k: sum(1 for v in ops.values() if v["rule"] == k)
                                                 for k in (T.B_END_POINT, T.B_OFFSET_JAMB)},
            "closure_b_missing": [k for k, v in ops.items() if v["closure_a"] and not v["closure_b"]],
            "thresholds": [{"threshold": t["threshold_id"], "opening": t["opening"], "site": t["physical_site_id"],
                            "area_m2": round(t["area"] * res["_unit2"], 6)} for t in res["semantic"]["thresholds"]],
            "topology_closures": tcs,
            "passages": [{"passage": p["passage_id"], "width_mm": round(p["width_mm"], 2),
                          "thickness_mm": round(p["thickness_mm"], 2), "site": p["strip_in_site"]}
                         for p in res["passages"]],
            "labelled_sites": labelled,
            "counts": {"sites": len(res["sites"]), "closures": len(res["closures"])}}


def floor_contact_map(res, inp, dry_sites):
    """Glazing on the dry-room boundaries: a normal window (glazing on a hosting wall face line) takes the scoped owner
    sill fact when it binds; anything else (glazing-only closures) has no floor-contact authority."""
    f = next(MF.from_record(x) for x in json.loads(R14.METHOD.read_text())["facts"] if x["fact_id"] == WINDOWS_FACT)
    b = MF.bind(f, inp)
    sites = {s["site_id"]: s for s in res["sites"]}
    out, windows = {}, []
    for sid, zones in dry_sites:
        for e in WC.site_edges(res["_arr"], sites[sid]):
            if WC.GLAZING_ROLE not in e["roles"]:
                continue
            closure = any(s.startswith("CLOSURE|") for s in e["sources"])
            hosted = not closure and set(e["roles"]) - {WC.GLAZING_ROLE} <= set(WC.WALL_ROLES) and \
                set(e["roles"]) - {WC.GLAZING_ROLE}
            if hosted and b["binding"] == "APPLIES":
                st = WC.floor_contact(sill_m=f.statement["sill_height_m"], sill_authority=f.ref)
            else:
                st = WC.floor_contact()
            for s in e["sources"]:
                out[s if s.startswith("CLOSURE|") else s.rsplit("|", 1)[0]] = st
            windows.append({"site": sid, "zones": zones, "sources": [handle(s) if not s.startswith("CLOSURE|") else s
                                                                     for s in e["sources"]],
                            "length_mm": round(e["length"] * inp.unit_native_to_mm, 1),
                            "hosted_on_wall_face_line": bool(hosted), "floor_contact": st})
    return out, windows, b["binding"]


def skirting_record(res, inp, fz):
    eps = R14.Q11.TP.tolerances(R14.Q11.RT.max_abs_coordinate(inp.parts), inp.unit_native_to_mm)["eps_r"]
    u = inp.unit_native_to_mm / 1000
    dry, wet = SB.dry_and_wet_sites(res)
    _, states = SB.obstacle_states(res, inp)
    bands = {b["band_id"]: b for b in res["wall_bands"]["bands"]}
    jambs = [j for p in res["passages"] for j in WC.passage_jambs(p, bands, eps)] + \
        WC.door_jambs(res["openings"], res["closures"])
    fcm, windows, wb = floor_contact_map(res, inp, dry)
    m = method(fz)
    sites = {s["site_id"]: s for s in res["sites"]}
    per, tot = {}, []
    for sid, zones in dry:
        r = WC.measure_v3(WC.site_edges(res["_arr"], sites[sid]), m, jambs=jambs, eps=eps, obstacle_authority=states,
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
                               "why": j.get("why")} for j in r["jambs_counted"]]}
        tot.append(r["length"] * u)
    for sid, zones, why in wet:
        per[sid] = {"zones": zones, "state": WC.NO_SKIRTING, "payable_lm": 0.0, "class": why}

    def agg(key, c):
        return round(math.fsum(v.get(key, {}).get(c, 0.0) for v in per.values()), 6)
    comps = (WC.REAL_WALL_FACE, WC.COLUMN_FACE, WC.AUTHORISED_OBSTACLE_FACE, WC.WINDOW_ABOVE_FLOOR,
             WC.PHYSICAL_OPENING_JAMB)
    excl = (WC.DOOR_PRESENT, WC.TOPOLOGY_CLOSURE, WC.FULL_HEIGHT_GLAZED, "DOOR_JAMB", "DOORLESS_JAMB_NOT_COUNTED")
    withheld = [dict(w, site=s) for s, v in per.items() for w in v.get("withheld", [])]
    return {"method": m.ref, "windows_fact_binding": wb, "windows": windows, "per_site": per,
            "PAYABLE_LM": round(math.fsum(tot), 6), "components_lm": {c: agg("components_lm", c) for c in comps},
            "excluded_lm": {c: agg("excluded_lm", c) for c in excl}, "withheld": withheld,
            "withheld_lm": round(math.fsum(w["length_lm"] for w in withheld), 6),
            "state": "COMPUTED_WITH_WITHHELD_SPANS" if withheld else "COMPUTED",
            "jamb_records": [{k: (v if k != "segment" else [[round(c, 4) for c in q] for q in v]) for k, v in j.items()}
                             for j in jambs]}


def main(work, closure_out, skirting_out):
    fz = json.loads(FZ_FILE.read_text())
    R = R14.R13.runs(work, None)
    new, old = R["new"], R["old"]
    inp_new, inp_old = R["inputs"]["NEW_K2"], R["inputs"]["OLD_K1"]
    head = {"freeze": fz["frozen_commit"], "door_closure_policy": fz["door_closure_policy"],
            "wall_contact_path_policy": fz["wall_contact_path_policy"],
            "blind": {"expected_value_given": False, "historical_totals_used": False,
                      "r8_15_values_read": False}}
    cr = dict(head, SCHEMA="URBAN_R8_16_CLOSURE_BLIND_RESULT_V1", NEW_K2=closure_record(new, inp_new),
              OLD_K1=closure_record(old, inp_old))
    sk = dict(head, SCHEMA="URBAN_R8_16_SKIRTING_BLIND_RESULT_V1", method=fz["qortuba_method"]["ref"],
              run_input_digest=new["run_manifest"]["RUN_INPUT_DIGEST"], **skirting_record(new, inp_new, fz))
    Path(closure_out).write_text(json.dumps(cr, indent=1, ensure_ascii=False, default=str) + "\n")
    Path(skirting_out).write_text(json.dumps(sk, indent=1, ensure_ascii=False, default=str) + "\n")
    print(json.dumps({"closure_b_rules": cr["NEW_K2"]["closure_b_rules"], "missing_b": cr["NEW_K2"]["closure_b_missing"],
                      "PAYABLE_LM": sk["PAYABLE_LM"], "withheld_lm": sk["withheld_lm"],
                      "components": sk["components_lm"]}, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:4])
