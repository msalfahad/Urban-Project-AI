"""R8.12 lab: Qortuba after the BLIND run of the frozen WALL_BAND_POLICY_V3 - six rows rebuilt, the owner physical
fact compared AFTER the blind record, Q-13 sole-blocker counterfactual, digest hierarchy, policy provenance audit.

    python3 research/external_engine_lab/r8_12_qortuba.py <work> <register_dir> [code_commit]

The blind result (tests/r8_12/registers/BLIND_QORTUBA_RESULT.json) is read, never rewritten. Project semantics live
here only.
"""

from __future__ import annotations

import ast
import hashlib
import json
import random
import sys
from collections import Counter
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

import r8_10_claims as CL                                                                     # noqa: E402
import r8_10_qortuba as Q10                                                                   # noqa: E402
import r8_11_owner_facts as OF11                                                              # noqa: E402
import r8_11_qortuba as Q11                                                                   # noqa: E402
import r8_8_topology as LAB                                                                   # noqa: E402
from engine.source import owner_facts as OF, run_manifest as RM, topology_closures as TC      # noqa: E402
from engine.source import trade_regions as TR, wall_bands as WB                               # noqa: E402

C = LAB.C
ROWS = LAB.ROUND1
REG12 = ROOT / "tests/r8_12/registers"
REG11 = ROOT / "tests/r8_11/registers"
handle = Q10.handle


def jl(p):
    return json.loads(Path(p).read_text())


def runs(work, commit):
    inps, _, facts = Q10.inputs(work)
    pc, xc, raw = CL.load()
    prov = {"code_commit": commit, "lab": "research/external_engine_lab/r8_12_qortuba.py"}
    i_new, i_old = inps["NEW_K2"], inps["OLD_K1"]
    return {"inputs": inps, "facts": facts, "claims": (pc, xc),
            "new": Q11.run(i_new, "NEW_K2", facts, pc, xc, TC.POLICY_ID, prov),
            "old": Q11.run(i_old, "OLD_K1", facts, pc, xc, TC.POLICY_ID, prov),
            "new_r810": Q11.run(i_new, "NEW_K2", facts, pc, xc),
            "old_r810": Q11.run(i_old, "OLD_K1", facts, pc, xc)}


# ---------------------------------------------------------------------------------------------- engine readings
def engine_readings(res):
    """{handle: (engine state, engine reading)} for every face / cap the engine itself establishes."""
    out = {}
    est = [b for b in res["wall_bands"]["bands"] if b["state"] == WB.ESTABLISHED]
    for b in est:
        for f in b["faces"]:
            out[handle(f)] = (OF.ENGINE_ESTABLISHED, OF11.REAL_WALL_FACE)
    auth = {(c["band_id"], tuple(c["geometry"])) for c in res["topology_closures"]["closures"]
            if c["release"] == TC.AUTHORISED_FOR_SHADOW}
    for b in est:
        for e in b["ends"]:
            if e["kind"] != WB.ALIGNED_FREE_END:
                continue
            g = (e["face_a_end"][0], e["face_a_end"][1], e["face_b_end"][0], e["face_b_end"][1])
            if (b["band_id"], g) in auth:
                for cap in e.get("drawn_caps", []):
                    out[handle(cap["source"])] = (OF.ENGINE_ESTABLISHED, OF11.REAL_WALL_END)
    return out


def compare_fact(fact_rec, inp, res):
    f = OF.from_record(fact_rec)
    b = OF.bind(f, inp)
    eng = engine_readings(res)
    per = []
    for key, _, reading in f.parts:
        h = handle(key)
        st, er = eng.get(h, (OF.ENGINE_UNRESOLVED, None))
        per.append({"part": h, "owner_reading": reading, "engine_state": st, "engine_reading": er,
                    "matrix": OF.compare(st, reading, er) if b["binding"] == "APPLIES" else None})
    comps = [x["matrix"] for x in per if x["matrix"]]
    domains = {
        OF.TOPOLOGY_ROLE: {"outcome": OF.OFFERED if b["binding"] == "APPLIES" else OF.outcome(b, OF.TOPOLOGY_ROLE,
                                                                                               used=False),
                           "note": "never applied: no part-scoped owner role claim was needed (the engine "
                                   "established every bound part)"},
        OF.TOPOLOGY_CLOSURE_REVIEW: {"outcome": OF.outcome(b, OF.TOPOLOGY_CLOSURE_REVIEW, used=False,
                                                           comparisons=comps),
                                     "note": "both closures are ENGINE authorised; the owner reading agrees"},
        OF.BLOCKER_CLASSIFICATION: {"outcome": OF.outcome(b, OF.BLOCKER_CLASSIFICATION, used=False,
                                                          comparisons=comps),
                                    "note": "no H2430 blocker remains to classify"},
        OF.PASSAGE_ATTRIBUTES: {"outcome": OF.outcome(b, OF.PASSAGE_ATTRIBUTES, used=True),
                                "note": "door NONE, head 2.20 m, block + plaster sides: attributes of the ENGINE "
                                        "detected passage (release layer)"}}
    return f, b, per, domains


# ---------------------------------------------------------------------------------------------- rows
def rows(res, tp, revision_id, owner_passage=None):
    res["_owner_physical"] = {}                       # the fact is corroborating only: it classifies no blocker
    res["_owner_passage"] = owner_passage
    res["_probe_geom"] = {p.source_id: (p.kind, p.geometry) for p in tp["probes"]}
    return Q11.rows_r811(res, tp, revision_id)


def counterfactual_floor(res, tp, revision_id, owner_passage):
    """Q-13 STATE (never a value) under each possible owner answer to the floor-under-object question."""
    out = {}
    keep = Q11.FOOTPRINT_POLICIES
    for name, treatment in (("YES_WHOLE_ROOM", TR.FOOTPRINT_INCLUDED), ("NO_FOOTPRINT_DEDUCTED", TR.FOOTPRINT_DEDUCTED)):
        Q11.FOOTPRINT_POLICIES = keep + (TR.TradeObjectFootprintPolicy(
            "HYPOTHETICAL-FLOOR-FOOTPRINT", 1, "FLOOR_FINISH", TR.ANY_NON_PARTITION_OBJECT, treatment,
            "COUNTERFACTUAL_ONLY", {}, ()),)
        try:
            q = rows(res, tp, revision_id, owner_passage)["Q-13"]
        finally:
            Q11.FOOTPRINT_POLICIES = keep
        out[name] = {"state": q["state"], "blocker_classes": q["blocker_classes"],
                     "value_recorded": False}
    return out


def digests(row, rid, release_reviews, owner_applied_release):
    ta = row["trade_authority"]
    rad = RM.row_authority_digest(row["run_input_digest"], row_id=rid, row_method="TS01 + trade layer (lab rows)",
                                  trade_rules=[ta["rule"]], semantic_class_rules=[ta["semantic_class_rule"]]
                                  if ta.get("semantic_class_rule") else [],
                                  footprint_policies=[f"{p.policy_id}@v{p.version}:{p.trade}:{p.treatment}"
                                                      for p in Q11.FOOTPRINT_POLICIES],
                                  row_claims=row["claims_applied"], owner_facts_applied=[])
    rel = RM.release_input_digest(rad["digest"], source_anchor_state="DWG_DXF_IDENTITY_NOT_ESTABLISHED",
                                  reviews=release_reviews, release_policy="SHADOW_ONLY_NO_RELEASE_GATE",
                                  release_blockers=row["release_blockers"],
                                  owner_facts_applied=owner_applied_release)
    return {"TOPOLOGY_RUN_INPUT_DIGEST": row["run_input_digest"], "ROW_AUTHORITY_DIGEST": rad,
            "RELEASE_INPUT_DIGEST": rel}


# ---------------------------------------------------------------------------------------------- audit
def policy_audit():
    src = Path(WB.__file__).read_text()
    tree = ast.parse(src)
    params = next(n for n in tree.body if isinstance(n, ast.Assign) and any(getattr(t, "id", "") == "PARAMS"
                                                                           for t in n.targets))
    loose = sorted({(n.value) for n in ast.walk(tree) if isinstance(n, ast.Constant)
                    and isinstance(n.value, (int, float)) and not isinstance(n.value, bool)
                    and not params.lineno <= n.lineno <= params.end_lineno})
    return {"SCHEMA": "URBAN_R8_12_POLICY_PROVENANCE_AUDIT_V1",
            "wall_bands": {"policy": WB.POLICY_ID, "params_in_policy_record": WB.PARAMS,
                           "removed_hidden_constants_from_V2": ["direction buckets of 2e-3 rad and their +-1 "
                                                                "neighbourhood (replaced by exhaustive parallel "
                                                                "search)", "ray / clip numeric guards 1e-15, 1e-12 "
                                                                "(now PARAMS.numeric_guards)", "id rounding 6 "
                                                                "(now PARAMS.id_coordinate_decimals)"],
                           "integer_literals_outside_params": loose,
                           "why_allowed": "tuple indices, halving (midpoints), the 16-character id length, record "
                                          "truncation (8), a closed loop needs >= 3 segments - none tunes discovery",
                           "derived_from_other_policies": ["eps_r / eps_n: TOPOLOGY_TOLERANCE_POLICY_V1",
                                                           "review band: ROLE_AUTHORITY near-miss band"]},
            "topology_closures": {"policy": TC.POLICY_ID, "digest": TC.policy_record()["digest"],
                                  "found": ["closure id rounds face end points to 9 decimals (identity only, not "
                                            "discovery)", "area balance bound eps_r x perimeter (stated in the "
                                            "policy text)"],
                                  "action": "R8.13: put the id rounding into the closure policy record with a "
                                            "version bump (no behaviour change)"},
            "room_topology": {"band_review": "role_authority.NEAR_MISS_REVIEW_BAND_MM / unit (recorded in the run "
                                             "manifest policies)"}}


# ---------------------------------------------------------------------------------------------- registers
def registers(work, commit=None):
    R = runs(work, commit)
    new, old = R["new"], R["old"]
    inp_new, inp_old = R["inputs"]["NEW_K2"], R["inputs"]["OLD_K1"]
    pc, xc = R["claims"]
    tp_new, tp_old = Q11.topo(inp_new, pc), Q11.topo(inp_old, pc)
    blind = jl(REG12 / "BLIND_QORTUBA_RESULT.json")
    freeze = jl(REG12 / "R8_12_FRAGMENT_BAND_FREEZE.json")
    assert WB.policy_record()["digest"] == freeze["wall_band_policy"]["digest"]
    # the lab run reproduces the blind record exactly
    same_as_blind = sorted(c["closure_id"] for c in new["topology_closures"]["closures"]) == \
        sorted(c["closure_id"] for c in blind["NEW_K2"]["closures"])
    fact_rec = OF11.load()[0]
    fact, b_new, per, domains = compare_fact(fact_rec, inp_new, new)
    b_old = OF.bind(fact, inp_old)
    owner_passage = OF11.hall_lobby_passage(inp_new, new, {"fact": fact.ref, "state": b_new["binding"]})
    eng_pass = next((p for p in new["passages"] if abs(p["width_mm"] - owner_passage["clear_width_mm_measured"])
                     < 0.01), None)
    owner_passage = dict(owner_passage, record_origin="ENGINE_DETECTED + owner attributes" if eng_pass else
                         owner_passage["record_origin"],
                         engine_detection=(f"DETECTED: {eng_pass['passage_id']} (band {eng_pass['band_id']} end -> "
                                           f"{handle(eng_pass['target']) if '|H' in eng_pass['target'] else eng_pass['target']})"
                                           if eng_pass else "NOT_DETECTED"),
                         engine_width_mm=round(eng_pass["width_mm"], 2) if eng_pass else None)
    rows_new = rows(new, tp_new, C.REV_NEW_ID, owner_passage)
    rows_old = rows(old, tp_old, C.REV_OLD_ID)
    rows_810 = Q10.rows_r810(R["new_r810"], C.REV_NEW_ID, R["new_r810"]["owner_claims"]["part_claims"])
    r811 = jl(REG11 / "QORTUBA_R8_11_STATUS.json")["rows"]
    cf = counterfactual_floor(new, tp_new, C.REV_NEW_ID, owner_passage)
    reviews = [f"{c['closure_id']}:CORROBORATED_BY_OWNER({fact.ref})" for c in new["topology_closures"]["closures"]
               if set(map(handle, c["source_evidence_ids"])) & {"2430", "2431"}]
    dig = {rid: digests(rows_new[rid], rid, reviews if rid == "Q-14" else [],
                        [fact.ref] if rid == "Q-14" else []) for rid in ROWS}
    hall = lambda r: next(s for s in r["sites"] if any("HALL" in v for v in LAB.stamps(s).values()))
    q13, q14 = rows_new["Q-13"], rows_new["Q-14"]
    other13 = sorted({f"{b['class']}:{b['issue']}" + (f":{b['detail'].get('source')}" if isinstance(b["detail"], dict)
                                                       and b["detail"].get("source") else "")
                      for x in q13["blockers"] for b in x["blockers"]})
    sole = cf["YES_WHOLE_ROOM"]["state"] == "COMPUTED_SHADOW"
    regs = {}
    regs["FRAGMENT_FACE_POLICY"] = {"SCHEMA": "URBAN_R8_12_FRAGMENT_FACE_POLICY_V1", "policy": WB.policy_record(),
                                    "freeze": freeze}
    collisions = {k: v for k, v in Counter(c["chain_id"] for c in new["wall_bands"]["chains"]).items() if v > 1}
    regs["FACE_CHAIN_REGISTER"] = {
        "SCHEMA": "URBAN_R8_12_FACE_CHAIN_REGISTER_V1",
        "NEW_K2": {"count": len(new["wall_bands"]["chains"]),
                   "multi_fragment": [{"chain_id": c["chain_id"], "fragments": [handle(f["source"]) for f in c["fragments"]],
                                       "nodes": [{"kind": n["kind"], "s": round(n["s"], 4),
                                                  "by": handle(n["by"]) if n.get("by") else None} for n in c["nodes"]]}
                                      for c in new["wall_bands"]["chains"] if len(c["fragments"]) > 1],
                   "chain_breaks": new["wall_bands"]["chain_breaks"],
                   "duplicate_intervals": [c["chain_id"] for c in new["wall_bands"]["chains"]
                                           if c["duplicate_intervals"]],
                   "id_collisions": {k: [[handle(f["source"]) + "|" + f["source"].rsplit("|", 1)[1]
                                          for f in c["fragments"]] for c in new["wall_bands"]["chains"]
                                         if c["chain_id"] == k] for k in collisions}},
        "OLD_K1": {"count": len(old["wall_bands"]["chains"]),
                   "multi_fragment": sum(1 for c in old["wall_bands"]["chains"] if len(c["fragments"]) > 1)},
        "finding_V3_D1": "chain ids of the parallel sides of ONE closed polyline with the same extent collide (H2060, "
                         "H2061: rectangles): the id uses entity + extent, not the supporting-line offset. Effect: "
                         "only these already-ambiguous rectangles; no closure, no row. Fix in R8.13 (add the offset / "
                         "sub-part set to the chain id) with a version bump - NOT inside the frozen V3"}
    regs["BAND_SPAN_REGISTER"] = {
        "SCHEMA": "URBAN_R8_12_BAND_SPAN_REGISTER_V1",
        "NEW_K2": [{"span_id": s["span_id"], "band_id": s["band_id"], "state": s["state"],
                    "s": [round(v, 4) for v in s["s"]], "width_mm": round(s["width"] * inp_new.unit_native_to_mm, 2),
                    "source_intervals": [dict(x, source=handle(x["source"])) for x in s["source_intervals"]]}
                   for s in new["wall_bands"]["spans"]],
        "OLD_K1_count": len(old["wall_bands"]["spans"]),
        "rule": "every span keeps the exact source-part parameter intervals it uses; topology never implies that a "
                "whole source face belongs to one band"}
    def asm(r, inp):
        u = inp.unit_native_to_mm
        return [{"band_id": b["band_id"], "state": b["state"], "faces": [handle(f) for f in b["faces"]],
                 "width_mm": round(b["width"] * u, 2), "length_mm": round((b["interval"][1] - b["interval"][0]) * u, 1),
                 "intervals": [dict(iv, by=[handle(x) for x in iv["by"]]) for iv in b["evidence"]["intervals"]],
                 "ends": [e["kind"] for e in b["ends"]], "spans": b["spans"]} for b in r["wall_bands"]["bands"]]
    a_new = asm(new, inp_new)
    regs["WALL_BAND_ASSEMBLY_REGISTER"] = {
        "SCHEMA": "URBAN_R8_12_WALL_BAND_ASSEMBLY_REGISTER_V1", "NEW_K2": a_new, "OLD_K1": asm(old, inp_old),
        "counts": {k: dict(Counter(b["state"] for b in r["wall_bands"]["bands"])) for k, r in (("NEW_K2", new),
                                                                                              ("OLD_K1", old))},
        "means": "TOPOLOGY_OBSTACLE_GEOMETRY - no wall length, thickness authority, masonry, plaster, paint or skirting",
        "finding_V3_D2": "elongation is tested on the raw CHAIN overlap; one pair (574 / 584, 1.80 m apart) is locally "
                         "mutual-nearest over only 150 mm and still forms a 'band' in an unlabelled site outside the "
                         "apartment, with a false 6.0 m passage record. No closure, no row. Fix in R8.13: test "
                         "elongation on the LOCAL RUN (spans + overlaps + nodes) - NOT inside the frozen V3",
        "wide_bands": [b for b in a_new if b["width_mm"] > 300]}
    r811_tc = jl(REG11 / "TOPOLOGY_CLOSURE_REGISTER.json")
    regs["TOPOLOGY_CLOSURE_REGISTER"] = {
        "SCHEMA": "URBAN_R8_12_TOPOLOGY_CLOSURE_REGISTER_V1", "policy": TC.policy_record(),
        "NEW_K2": blind["NEW_K2"]["closures"], "OLD_K1": blind["OLD_K1"]["closures"],
        "h2431_regression": {
            "r8_11": next(c for c in r811_tc["NEW_K2"] if c["closure_id"] in r811_tc["applied"]["NEW_K2"]),
            "r8_12": next(c for c in blind["NEW_K2"]["closures"] if "2431" in c["evidence"]),
            "same_geometry": next(c for c in blind["NEW_K2"]["closures"] if "2431" in c["evidence"])["geometry"] ==
            [round(v, 4) for v in next(c for c in r811_tc["NEW_K2"] if c["closure_id"] in
                                       r811_tc["applied"]["NEW_K2"])["geometry"]],
            "id_changed_because": "closure ids derive from the band id, and band ids are V3 assembly ids"},
        "h1316_control": {"closures_with_1316": [c for c in blind["NEW_K2"]["closures"] if "1316" in c["evidence"]],
                          "classification": "NOT_WALL_CAP (window jamb; unchanged)"},
        "material": "NONE for every closure"}
    regs["OWNER_FACT_COMPARISON"] = {
        "SCHEMA": "URBAN_R8_12_OWNER_FACT_COMPARISON_V1", "fact": fact.ref, "policy": OF.policy_record(),
        "order": "the blind record (BLIND_QORTUBA_RESULT.json, committed first) was compared afterwards",
        "binding": {"NEW_K2": b_new["binding"], "OLD_K1": b_old["binding"]}, "per_part": per, "domains": domains,
        "matrix_states": dict(Counter(x["matrix"] for x in per)), "fallback_owner_role_claim_required": False,
        "fallback_not_computed": "the engine established H2430 itself: no OWNER_ROLE_AUTHORITY path was needed or run",
        "matrix_definition": OF.MATRIX}
    regs["Q14_STATUS"] = dict(Q11._row_status("Q-14", q14, rows_810["Q-14"], rows_old["Q-14"]),
                              SCHEMA="URBAN_R8_12_Q14_STATUS_V1",
                              r8_11={k: r811["NEW_K2_R8_11"]["Q-14"][k] for k in ("state", "value", "blocker_classes")},
                              rebuild={k: q14[k] for k in ("physical_site_ids", "wall_bands", "topology_closures_applied",
                                                           "opening_closures", "threshold_sites", "open_passage_sites",
                                                           "trade_authority", "footprint_authority", "claims_applied",
                                                           "source_anchor")},
                              owner_facts={"corroborating": [fact.ref], "applied_to_row": [],
                                           "applied_to_release": [fact.ref]},
                              digests=dig["Q-14"], final=False)
    regs["Q13_STATUS"] = dict(Q11._row_status("Q-13", q13, rows_810["Q-13"], rows_old["Q-13"]),
                              SCHEMA="URBAN_R8_12_Q13_STATUS_V1",
                              r8_11={k: r811["NEW_K2_R8_11"]["Q-13"][k] for k in ("state", "value", "blocker_classes")},
                              blocker_set=other13, digests=dig["Q-13"],
                              sole_blocker_test={"question": "would ONE owner answer (floor laid under the built-in "
                                                             "wardrobes and loose furniture) release Q-13?",
                                                 "method": "counterfactual: the rows rebuilt under each possible "
                                                           "answer as a hypothetical FLOOR_FINISH footprint policy; "
                                                           "only the STATE is recorded, never a value",
                                                 "counterfactual": cf, "answer": "YES" if sole else "NO",
                                                 "consequence": "prepare ONE owner question" if sole else
                                                 "no owner question"}, final=False)
    regs["DIGEST_HIERARCHY"] = {
        "SCHEMA": "URBAN_R8_12_DIGEST_HIERARCHY_V1", "layers": list(RM.DIGEST_LAYERS),
        "definition": {RM.TOPOLOGY_LAYER: "everything that can change TS01 physical topology (= RUN_INPUT_DIGEST)",
                       RM.ROW_LAYER: "topology digest + trade rules + semantic class rules + footprint policies + row "
                                     "claims + owner facts APPLIED to the row + row method",
                       RM.RELEASE_LAYER: "row authority digest + source-anchor state + review states + release policy + "
                                         "release blockers + owner facts applied at release"},
        "rows": dig,
        "hall_lobby_fact": {"topology": "never an input of TS01 -> TOPOLOGY digest unchanged by construction",
                            "row": "CORROBORATING_ONLY for every row in R8.12 -> not in any ROW_AUTHORITY digest",
                            "release": "APPLIED (passage attributes -> the Q-14 passage-soffit release note) -> in "
                                       "the Q-14 RELEASE_INPUT_DIGEST",
                            "r8_11_difference": "in R8.11 the same fact classified the H2430 blocker, i.e. it WAS row "
                                                "authority (row_input_digest); in R8.12 the engine resolved H2430 and "
                                                "the fact left the row layer"}}
    regs["POLICY_PROVENANCE_AUDIT"] = policy_audit()
    det = shuffle_check(work, new)
    regs["BLIND_QORTUBA_RESULT"] = blind
    regs["R8_12_FRAGMENT_BAND_FREEZE"] = freeze
    regs["QORTUBA_R8_12_STATUS"] = {
        "SCHEMA": "URBAN_R8_12_QORTUBA_STATUS_V1",
        "rows": {"NEW_K2_R8_12": rows_new,
                 "OLD_K1_R8_12": {k: {"state": v["state"], "value": v["value"]} for k, v in rows_old.items()},
                 "NEW_K2_R8_11": {k: {"state": v["state"], "value": v["value"]} for k, v in r811["NEW_K2_R8_11"].items()},
                 "OLD_K1_R8_11": r811["OLD_K1_R8_11"]},
        "old_revision_unchanged": {k: (rows_old[k]["state"], rows_old[k]["value"]) ==
                                   (r811["OLD_K1_R8_11"][k]["state"], r811["OLD_K1_R8_11"][k]["value"]) for k in ROWS},
        "hall": {"r8_11_m2": r811["NEW_K2_R8_11"]["Q-14"]["blockers"][0]["area_m2"] if
                 r811["NEW_K2_R8_11"]["Q-14"]["blockers"] else None, "r8_12_m2": round(hall(new)["area_m2"], 4),
                 "issues": hall(new)["issues"]},
        "lab_reproduces_blind_record": same_as_blind, "determinism": det,
        "owner_passage": owner_passage, "final": "SHADOW only: no row is FINAL"}
    ctx = {"rows_new": rows_new, "rows_old": rows_old, "cf": cf, "sole": sole, "per": per, "domains": domains,
           "dig": dig, "det": det, "owner_passage": owner_passage, "other13": other13}
    return regs, ctx


def shuffle_check(work, base):
    inps, _, facts = Q10.inputs(work)
    pc, xc, _ = CL.load()
    inp = inps["NEW_K2"]
    out = {}
    for seed in (5, 17):
        parts, texts = list(inp.parts), list(inp.texts)
        random.Random(seed).shuffle(parts)
        random.Random(seed + 1).shuffle(texts)
        r = Q11.run(replace(inp, parts=tuple(parts), texts=tuple(texts)), "NEW_K2", facts, pc, xc, TC.POLICY_ID)
        key = lambda x: (sorted(c["chain_id"] for c in x["wall_bands"]["chains"]),
                         sorted(b["band_id"] for b in x["wall_bands"]["bands"]),
                         sorted(s["span_id"] for s in x["wall_bands"]["spans"]),
                         sorted(c["closure_id"] for c in x["topology_closures"]["closures"]),
                         sorted((s["site_id"], round(s["area"], 6)) for s in x["sites"]),
                         x["run_manifest"]["RUN_INPUT_DIGEST"])
        out[f"seed_{seed}"] = key(r) == key(base)
    return out


def main(work, regdir, commit=None):
    regdir = Path(regdir)
    regdir.mkdir(parents=True, exist_ok=True)
    regs, ctx = registers(work, commit)
    for n, o in regs.items():
        (regdir / f"{n}.json").write_text(json.dumps(o, indent=1, ensure_ascii=False, default=str) + "\n")
    print(json.dumps({k: (v["state"], v["value"]) for k, v in ctx["rows_new"].items()}, indent=1))
    print(json.dumps(ctx["cf"]), ctx["det"])
    return regs, ctx


if __name__ == "__main__":
    main(*sys.argv[1:4])
