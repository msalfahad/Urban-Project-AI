"""R8.16 lab: Qortuba AFTER the frozen R8.16 blind run - the R8.15 row assembly re-run on the V2-closure topology
(I1471 now has its own door strip), the V3 skirting row (recomputed, must equal the blind record), the hidden
profile on the same path, door / passage reveal surfaces, the I1471 source audit, marble regression.

    python3 research/external_engine_lab/r8_16_qortuba.py <work> <register_dir> [code_commit]
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

import r8_15_qortuba as R15                                                                   # noqa: E402
import r8_16_blind as BL                                                                      # noqa: E402
from engine.source import opening_reveals as OR, topology as T, wall_contact_path as WC       # noqa: E402

REG16 = ROOT / "tests/r8_16/registers"
QP21_DOOR_HEAD = 2.20
handle = R15.handle


def jl(p):
    return json.loads(Path(p).read_text())


def i1471_audit(res, inp):
    u = inp.unit_native_to_mm
    st = res["openings"]["I1471"]
    parts = {p.identity.key: p for p in inp.parts}
    caps = [{"cap": handle(k), "layer": parts[k].layer, "geometry_mm": [round(v * u / 1, 1) for v in parts[k].geometry],
             "length_mm": round(math.dist(parts[k].geometry[:2], parts[k].geometry[2:4]) * u, 1)} for k in st["hits"]]
    bands = []
    for b in res["wall_bands"]["bands"]:
        fs = sorted(handle(f) for f in b["faces"])
        if set(fs) & {"518", "523", "519", "525"}:
            bands.append({"band": b["band_id"], "state": b["state"], "faces": fs, "thickness_mm": round(b["width"] * u, 1),
                          "ends": [e["kind"] for e in b["ends"]]})
    door = res["roles"]["doors"]["I1471"]
    return {"SCHEMA": "URBAN_R8_16_I1471_SOURCE_AUDIT_V1", "door_occurrence": "I1471",
            "door_symbol": {"swing_part": door["swing_part"], "hinge": [round(v, 2) for v in door["hinge"]],
                            "radius_mm": round(door["radius"] * u, 1),
                            "layers": sorted({p.layer for p in inp.parts if p.identity.instance_handles == ("1471",)})},
            "closure_a": st["closure_a"], "jamb_caps": caps, "hosting_bands": bands,
            "face_lines_mm": {"H523 (150 wall, HALL face)": "y = 15574.72", "H525 (200 wall, HALL face)": "y = 15574.72",
                              "H518 (150 wall, M.B face)": "y = 15589.72", "H519 (200 wall, M.B face)": "y = 15594.72"},
            "cause": "LEGITIMATE STAGGERED CONSTRUCTION: a 200 mm wall (WB-d0fa, H519 / H525) meets a 150 mm wall "
                     "(WB-2c6e, H518 / H523) at the door, flush on the HALL side; the 50 mm step is on the M.B.ROOM "
                     "side. Each band is ESTABLISHED on its own parallel faces - not drafting noise, not a finish "
                     "offset. Closure A (closed leaf on the 150 mm wall's M.B face) meets cap H1473 at its END but cap "
                     "H1472 in its MIDDLE, so the R8.9 end-point rule never formed closure B",
            "v2_result": {"closure_b": st.get("closure_b"), "rule": st.get("closure_b_rule"),
                          "evidence": st.get("closure_b_evidence"), "width_mm": round(st["width"] * u, 2)},
            "strip_site": next(({"threshold": t["threshold_id"], "site": t["physical_site_id"],
                                 "area_m2": round(t["area"] * res["_unit2"], 6)}
                                for t in res["semantic"]["thresholds"] if t["opening"] == "I1471"), None)}


def door_reveals(res, inp):
    """Door reveal surfaces (plaster / finish) - independent of skirting (door jamb skirting is zero)."""
    u = inp.unit_native_to_mm / 1000
    out = []
    for j in WC.door_jambs(res["openings"], res["closures"]):
        out.append({"opening": j["opening"], "surface": "JAMB", "depth_m": round(j["length"] * u, 6),
                    "height_m": QP21_DOOR_HEAD, "area_m2": round(j["length"] * u * QP21_DOOR_HEAD, 6),
                    "height_authority": "QP-21 OWNER_CONFIRMED_INTERNAL_DOOR_HEIGHT 2.20 m (Qortuba project parameter)",
                    "skirting": 0.0, "plaster_eligible": True, "paint": "NOT ASSUMED"})
    for t in res["semantic"]["thresholds"]:
        st = res["openings"][t["opening"]]
        out.append({"opening": t["opening"], "surface": "TOP_REVEAL", "width_m": round(st["width"] * u, 6),
                    "plan_area_m2": round(t["area"] * res["_unit2"], 6), "ceiling": "NOT_IN_TRADE (door head reveal)",
                    "skirting": 0.0, "plaster_eligible": True, "paint": "NOT ASSUMED"})
    return out


def build(work, commit=None):
    ctx = R15.build(work, commit)
    new, inp = ctx["new"], ctx["inp_new"]
    fz = jl(REG16 / "R8_16_FREEZE.json")
    cblind, sblind = jl(REG16 / "CLOSURE_BLIND_RESULT.json"), jl(REG16 / "SKIRTING_BLIND_RESULT.json")
    crec = BL.closure_record(new, inp)
    srec = BL.skirting_record(new, inp, fz)
    ctx["reproduces_r8_16"] = {"closures": json.loads(json.dumps(crec, default=str)) == cblind["NEW_K2"],
                               "topology_digest": crec["run_input_digest"] == cblind["NEW_K2"]["run_input_digest"],
                               "skirting": srec["PAYABLE_LM"] == sblind["PAYABLE_LM"] and
                               json.loads(json.dumps(srec["per_site"], default=str)) == sblind["per_site"]}
    v3o1 = []
    for sid, v in srec["per_site"].items():
        for j in v.get("jambs", []):
            if j["end_kind"] == "CONTINUOUS_WALL_FACE":
                v3o1.append({"site": sid, "opening": j["opening"], "length_lm": j["length_lm"]})
    ctx["v3_o1"] = {"id": "V3-O1", "what": "measure_v3 subtracts the overlap of EVERY jamb record from the wall path, "
                                         "including a CONTINUOUS_WALL_FACE side (not a jamb) - that wall span then "
                                         "counts nowhere", "spans": v3o1,
                    "effect_lm": round(sum(x["length_lm"] for x in v3o1), 6),
                    "action": "next round (no post-result edit inside the frozen V3)"}
    ctx["skirting_v3"] = srec
    ctx["closure_v2"] = crec
    ctx["i1471"] = i1471_audit(new, inp)
    ctx["door_reveals"] = door_reveals(new, inp)
    ctx["r8_16_freeze"] = fz
    ctx["closure_blind"], ctx["skirting_blind"] = cblind, sblind
    blk = ["SOURCE_ANCHOR: DXF anchored, DWG identity NOT_ESTABLISHED"]
    if srec["withheld"]:
        blk.append(f"WITHHELD_SPAN: {srec['withheld_lm']} lm whose floor contact is not proven (" + "; ".join(
            f"{w['site']} {w['class']} {w['length_lm']} lm" for w in srec["withheld"]) + ")")
    if ctx["v3_o1"]["effect_lm"]:
        blk.append(f"V3_O1_CONTINUOUS_FACE_UNDERCOUNT: {ctx['v3_o1']['effect_lm']} lm of continuous wall face at a "
                   "passage side is consumed by a non-jamb record (frozen V3 defect, fixed next round)")
    blk.append("SHADOW_ONLY: no baseline approval, no migration transaction, no release gate passed")
    ctx["skirting_blockers"] = blk
    return ctx


def main(work, regdir, commit=None):
    import r8_16_registers as REGS
    regs, ctx = REGS.registers(build(work, commit))
    regdir = Path(regdir)
    regdir.mkdir(parents=True, exist_ok=True)
    for n, o in regs.items():
        (regdir / f"{n}.json").write_text(json.dumps(o, indent=1, ensure_ascii=False, default=str) + "\n")
    print(json.dumps({k: (v["state"], v["value"]) for k, v in ctx["rows_new"].items()} |
                     {"SKIRTING": ctx["skirting_v3"]["PAYABLE_LM"]}, indent=1))
    return regs, ctx


if __name__ == "__main__":
    main(*sys.argv[1:4])
