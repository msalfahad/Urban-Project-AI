"""R8.13 lab: Qortuba AFTER the blind run of the frozen WALL_BAND_POLICY_V4 - band diff against V3, the owner finish
facts (scoped, trade layer only), the Q-13 rebuild with the strip allocation audit, the Q-14 regression, six-row
status with full provenance, the closure release evaluation and determinism.

    python3 research/external_engine_lab/r8_13_qortuba.py <work> <register_dir> [code_commit]

The blind record (tests/r8_13/registers/BLIND_QORTUBA_V4_RESULT.json) is read, never rewritten. The owner floor fact
enters ONLY the Q-13 trade run, after the frozen V4 topology. Project semantics live here only.
"""

from __future__ import annotations

import json
import random
import shutil
import sys
from collections import Counter
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

import r8_10_claims as CL                                                                     # noqa: E402
import r8_10_qortuba as Q10                                                                   # noqa: E402
import r8_11_owner_facts as OF11                                                              # noqa: E402
import r8_11_qortuba as Q11                                                                   # noqa: E402
import r8_12_qortuba as R12                                                                   # noqa: E402
import r8_8_topology as LAB                                                                   # noqa: E402
from engine.source import closure_release as CR, owner_facts as OF, owner_method_facts as MF  # noqa: E402
from engine.source import run_manifest as RM, topology_closures as TC, trade_regions as TR    # noqa: E402
from engine.source import trade_strips as TS, wall_bands as WB                                # noqa: E402

C = LAB.C
ROWS = LAB.ROUND1
REG12 = ROOT / "tests/r8_12/registers"
REG13 = ROOT / "tests/r8_13/registers"
FINISH = ROOT / "data/registry/OWNER_FINISH_FACTS.json"
OWNER_RULES = "research/qs_wall_treatment_01/pa08/qortuba/boq/owner_rules.py"
handle = Q10.handle
jl = R12.jl
Q14_R8_12 = 141.0263                     # the R8.12 regression observation - compared, never a target

# ---------------------------------------------------------------------------------------------- semantic classes v2
SPACE_CLASSES_V2 = TR.SemanticClassRule(
    "QORTUBA-SPACE-CLASS", 2, "PROJECT_OWNER_RULE (owner rule store + R8.13 owner finish facts)",
    (f"{OWNER_RULES}: US-01 WET_SERVICE_ROOM_CERAMIC", f"{OWNER_RULES}: QP-07 QORTUBA_CERAMIC_SERVICE_ROOMS = "
     "BATH x3 + PAINTRY", f"{OWNER_RULES}: QP-14 QORTUBA_DRY_FLOOR_FINISH = PORCELAIN",
     "data/registry/OWNER_FINISH_FACTS.json: QORTUBA-NEW-WET-SERVICE-FINISH-OWNER-001@v1"),
    {"project": "QORTUBA", "region": C.REGION_ID, "plan": CL.PLAN, "revision": C.REV_NEW_ID},
    by_label={"BATH": "WET_SERVICE_ROOM", "PAINTRY": "SERVICE_ROOM"}, otherwise_class="DRY_INTERNAL_ROOM",
    scope_labels=tuple(sorted(LAB.apartment_names() - {"BATH", "PAINTRY"})))
FLOOR_BY_CLASS_V2 = {"WET_SERVICE_ROOM": "CERAMIC_WET_FLOOR", "SERVICE_ROOM": "CERAMIC_SERVICE_FLOOR",
                     "DRY_INTERNAL_ROOM": "PORCELAIN_DRY_FLOOR"}
FLOOR_RULE_V2 = TR.class_rule_as_treatment(
    "QORTUBA-FLOOR-TREATMENT", 3, "FLOOR_FINISH", "PROJECT_OWNER_RULE (owner rule store, rank 2)",
    Q10.FLOOR_RULE.source_refs, SPACE_CLASSES_V2, FLOOR_BY_CLASS_V2, TR.POLICY_UNRESOLVED)
ROW_CLASS = {"Q-03": ["WET_SERVICE_ROOM"], "Q-11": ["WET_SERVICE_ROOM"], "Q-03P": ["SERVICE_ROOM"],
             "Q-12": ["SERVICE_ROOM"], "Q-13": ["DRY_INTERNAL_ROOM"], "Q-14": None}
ROW_FINISH = {"Q-03": "CERAMIC_WET_FLOOR", "Q-11": "CERAMIC_WET_FLOOR", "Q-03P": "CERAMIC_SERVICE_FLOOR",
              "Q-12": "CERAMIC_SERVICE_FLOOR", "Q-13": "PORCELAIN_DRY_FLOOR", "Q-14": "CEILING_BY_AREA"}
OWNER_ROOM_TYPES = {      # owner room type -> the EXACT source label texts of this plan that carry it (no similarity)
    "BATHROOM": {"labels": ["BATH"], "class": "WET_SERVICE_ROOM", "authority": "US-01 + QP-07 + R8.13 §4"},
    "KITCHEN": {"labels": ["PAINTRY"], "class": "SERVICE_ROOM", "authority": "QP-07 (the owner named PAINTRY the "
                "preparation / kitchen service zone); PAINTRY keeps its QP-07 rule and class"},
    "IRONING_ROOM": {"labels": [], "class": "WET_SERVICE_ROOM", "authority": "R8.13 §4 (no such label in this plan)"},
    "WASHING_LAUNDRY_ROOM": {"labels": [], "class": "WET_SERVICE_ROOM",
                             "authority": "R8.13 §4 (no such label in this plan)"}}


@contextmanager
def lab_rules(footprints=None):
    keep = (Q11.FOOTPRINT_POLICIES, Q11.SPACE_CLASSES, Q11.FLOOR_RULE)
    Q11.SPACE_CLASSES, Q11.FLOOR_RULE = SPACE_CLASSES_V2, FLOOR_RULE_V2
    if footprints is not None:
        Q11.FOOTPRINT_POLICIES = footprints
    try:
        yield
    finally:
        Q11.FOOTPRINT_POLICIES, Q11.SPACE_CLASSES, Q11.FLOOR_RULE = keep


def finish_facts():
    return [MF.from_record(r) for r in jl(FINISH)["facts"]]


# ---------------------------------------------------------------------------------------------- runs
def runs(work, commit):
    inps, _, facts = Q10.inputs(work)
    pc, xc, _ = CL.load()
    prov = {"code_commit": commit, "lab": "research/external_engine_lab/r8_13_qortuba.py"}
    return {"inputs": inps, "facts": facts, "claims": (pc, xc),
            "new": Q11.run(inps["NEW_K2"], "NEW_K2", facts, pc, xc, TC.POLICY_ID, prov),
            "old": Q11.run(inps["OLD_K1"], "OLD_K1", facts, pc, xc, TC.POLICY_ID, prov)}


def asm(r, inp):
    u = inp.unit_native_to_mm
    return [{"band_id": b["band_id"], "state": b["state"], "faces": sorted(handle(f) for f in b["faces"]),
             "width_mm": round(b["width"] * u, 2), "length_mm": round((b["interval"][1] - b["interval"][0]) * u, 1),
             "support": b["evidence"].get("structural_support", {}).get("state"),
             "ends": [e["kind"] for e in b["ends"]]} for b in r["wall_bands"]["bands"]]


def band_diff(v3, v4):
    key = lambda b: (b["state"], tuple(sorted(b["faces"])), b["width_mm"], b["length_mm"])
    c3, c4 = Counter(map(key, v3)), Counter(map(key, v4))
    lost, gained = c3 - c4, c4 - c3
    return {"v3_records": len(v3), "v4_records": len(v4), "v3_distinct": len(c3), "v4_distinct": len(c4),
            "v3_duplicate_records": sum(n - 1 for n in c3.values() if n > 1),
            "lost": [{"state": k[0], "faces": list(k[1]), "width_mm": k[2], "length_mm": k[3], "n": n}
                     for k, n in sorted(lost.items())],
            "gained": [{"state": k[0], "faces": list(k[1]), "width_mm": k[2], "length_mm": k[3], "n": n}
                       for k, n in sorted(gained.items())],
            "unchanged_distinct": len(set(c3) & set(c4))}


# ---------------------------------------------------------------------------------------------- rows
def site_treatments(res, rule):
    names = LAB.apartment_names()
    lab_sites, internal_sites = LAB.apartment_sites(res)
    internal = {s["site_id"] for s in internal_sites}
    out = {}
    for s in lab_sites + internal_sites:
        dec = TR.zone_decision(Q10.site_zone_names(s, names, internal), rule)
        t = {v for v in dec["treatments"].values() if v}
        out[s["site_id"]] = next(iter(t)) if len(t) == 1 and dec["state"] in (TR.SINGLE_ZONE, TR.NOT_REQUIRED) \
            else None
    return out


def strips(res):
    u2 = res["_unit2"]
    out = [{"id": t["threshold_id"], "kind": "THRESHOLD", "location": TS.SEPARATE_SITE, "sides": list(t["sides"]),
            "site": t["physical_site_id"], "area_m2": round(t["area"] * u2, 6), "opening": t["opening"]}
           for t in res["semantic"]["thresholds"]]
    out += [{"id": p["passage_id"], "kind": "OPEN_PASSAGE", "location": TS.INSIDE_SITE, "site": p["strip_in_site"],
             "sides": [p["strip_in_site"]], "area_m2": round(p["area_m2"], 6), "width_mm": round(p["width_mm"], 2)}
            for p in res.get("passages") or [] if p.get("strip_in_site")]
    return out


def strip_audit(res, row, rid):
    rule = Q11.rule_for(rid)
    tr = site_treatments(res, rule)
    want = Q10.ROW_TREATMENT[rid]
    sites = {u["site"] for u in row["sites_used"]}
    aud = [TS.audit(s, sites, tr, want) for s in strips(res)]
    aud = [a for a in aud if a["state"] != TS.NOT_IN_ROW]
    return aud, TS.row_effect(aud)


def build_rows(res, tp, revision_id, owner_passage, floor_policy):
    """All six rows WITHOUT the floor fact; Q-13 again WITH it (its only row); a leak check on the other five."""
    with lab_rules((Q11.CEILING_FOOTPRINT,)):
        base = R12.rows(res, tp, revision_id, owner_passage)
    if floor_policy is None:
        out = base
    else:
        with lab_rules((Q11.CEILING_FOOTPRINT, floor_policy)):
            withf = R12.rows(res, tp, revision_id, owner_passage)
        leak = {rid: (base[rid]["state"], base[rid]["value"]) != (withf[rid]["state"], withf[rid]["value"])
                for rid in ROWS if rid != "Q-13"}
        out = dict(base, **{"Q-13": withf["Q-13"]})
        out["_leak_check"] = leak
        out["_q13_without_fact"] = {"state": base["Q-13"]["state"], "blocker_classes": base["Q-13"]["blocker_classes"],
                                    "blockers": base["Q-13"]["blockers"]}
    with lab_rules():
        for rid in ROWS:
            row = out[rid]
            aud, eff = strip_audit(res, row, rid)
            row["strip_audit"] = aud
            row["strip_effect"] = eff
            rel = [b for b in row["release_blockers"] if not (b.startswith("OBJECT_FOOTPRINT_IMPLICIT") and
                                                               rid == "Q-13" and floor_policy is not None)]
            if eff["release"]:
                rel.insert(len(rel) - 1, f"STRIP_ALLOCATION: {len(eff['release'])} door-threshold strip(s) "
                                         f"({eff['excluded_area_m2']} m2) are separate sites outside this row; no "
                                         "allocation authority assigns them")
            row["release_blockers"] = rel
            if eff["blocking"] and row["state"] == "COMPUTED_SHADOW":
                row["state"], row["value"] = "BLOCKED_TRADE_RULE", None
                row["blocker_classes"] = sorted(set(row["blocker_classes"]) | {"TRADE_RULE"})
    return out


def digests(row, rid, policies, owner_applied_row, reviews, owner_applied_release):
    ta = row["trade_authority"]
    rad = RM.row_authority_digest(
        row["run_input_digest"], row_id=rid, row_method="TS01 (WALL_BAND_POLICY_V4) + trade layer + "
        f"{TS.POLICY_ID} (lab rows)", trade_rules=[ta["rule"]],
        semantic_class_rules=[f"{SPACE_CLASSES_V2.rule_id}@v{SPACE_CLASSES_V2.version}"] if rid != "Q-14" else [],
        footprint_policies=[f"{p.policy_id}@v{p.version}:{p.trade}:{p.treatment}" for p in policies],
        row_claims=row["claims_applied"], owner_facts_applied=owner_applied_row)
    rel = RM.release_input_digest(rad["digest"], source_anchor_state="DWG_DXF_IDENTITY_NOT_ESTABLISHED",
                                  reviews=reviews, release_policy="SHADOW_ONLY_NO_RELEASE_GATE",
                                  release_blockers=row["release_blockers"], owner_facts_applied=owner_applied_release)
    return {"TOPOLOGY_RUN_INPUT_DIGEST": row["run_input_digest"], "ROW_AUTHORITY_DIGEST": rad,
            "RELEASE_INPUT_DIGEST": rel}


# ---------------------------------------------------------------------------------------------- source anchor
def source_anchor():
    tools = {t: shutil.which(t) for t in ("dwg2dxf", "dwgread", "ODAFileConverter", "TeighaFileConverter")}
    try:
        import ezdxf
        ez = ezdxf.__version__
    except Exception:                                          # noqa: BLE001
        ez = None
    return {"SCHEMA": "URBAN_R8_13_SOURCE_ANCHOR_STATUS_V1", "state": "NOT_ESTABLISHED",
            "dxf_sha256": C.NEW_DXF, "dwg_candidate_sha256": Q10.DWG_CANDIDATE,
            "decoders_found_locally": {k: v for k, v in tools.items()}, "ezdxf": ez,
            "why": "no local DWG decoder (libredwg dwg2dxf / dwgread, ODA / Teigha converter) is installed; ezdxf "
                   "reads DXF only. No unpinned software was downloaded. V4 and Q-13 did not wait on this",
            "effect": "SOURCE_ANCHOR stays a release blocker on every new-revision row",
            "next": "R8.14: a pinned, hash-locked decoder (libredwg release tarball + sha256 in DONORS.lock) and a "
                    "DWG -> DXF entity-level reconciliation of the measured region"}


# ---------------------------------------------------------------------------------------------- determinism
def shuffle_check(work, base):
    inps, _, facts = Q10.inputs(work)
    pc, xc, _ = CL.load()
    inp = inps["NEW_K2"]
    out = {}
    key = lambda x: (sorted(c["chain_id"] for c in x["wall_bands"]["chains"]),
                     sorted(b["band_id"] for b in x["wall_bands"]["bands"]),
                     sorted(s["span_id"] for s in x["wall_bands"]["spans"]),
                     sorted(c["closure_id"] for c in x["topology_closures"]["closures"]),
                     sorted(p["passage_id"] for p in x["passages"]),
                     sorted((s["site_id"], round(s["area"], 6)) for s in x["sites"]),
                     x["run_manifest"]["RUN_INPUT_DIGEST"])
    for seed in (5, 17):
        parts, texts = list(inp.parts), list(inp.texts)
        random.Random(seed).shuffle(parts)
        random.Random(seed + 1).shuffle(texts)
        r = Q11.run(replace(inp, parts=tuple(parts), texts=tuple(texts)), "NEW_K2", facts, pc, xc, TC.POLICY_ID)
        out[f"seed_{seed}"] = key(r) == key(base)
    return out


# ---------------------------------------------------------------------------------------------- the build
def build(work, commit=None):
    R = runs(work, commit)
    new, old = R["new"], R["old"]
    inp_new, inp_old = R["inputs"]["NEW_K2"], R["inputs"]["OLD_K1"]
    pc, _ = R["claims"]
    tp_new, tp_old = Q11.topo(inp_new, pc), Q11.topo(inp_old, pc)
    blind = jl(REG13 / "BLIND_QORTUBA_V4_RESULT.json")
    freeze = jl(REG13 / "R8_13_V4_FREEZE.json")
    assert WB.policy_record()["digest"] == freeze["wall_band_policy"]["digest"]
    reproduces = {"closures": sorted(c["closure_id"] for c in new["topology_closures"]["closures"]) ==
                  sorted(c["closure_id"] for c in blind["NEW_K2"]["closures"]),
                  "passages": sorted(p["passage_id"] for p in new["passages"]) ==
                  sorted(p["passage_id"] for p in blind["NEW_K2"]["passages"]),
                  "topology_digest": new["run_manifest"]["RUN_INPUT_DIGEST"] == blind["NEW_K2"]["run_input_digest"]}
    # ---- the Hall / Lobby physical fact (R8.12 model), compared after the blind record
    fact_rec = OF11.load()[0]
    pfact, b_new, per, domains = R12.compare_fact(fact_rec, inp_new, new)
    owner_passage = OF11.hall_lobby_passage(inp_new, new, {"fact": pfact.ref, "state": b_new["binding"]})
    eng_pass = next((p for p in new["passages"] if abs(p["width_mm"] - owner_passage["clear_width_mm_measured"])
                     < 0.01), None)
    owner_passage = dict(owner_passage, engine_detection=(f"DETECTED: {eng_pass['passage_id']}" if eng_pass else
                                                          "NOT_DETECTED"),
                         engine_width_mm=round(eng_pass["width_mm"], 2) if eng_pass else None)
    # ---- the owner finish facts: bound, then used ONLY in the trade layer
    mfacts = finish_facts()
    binds_new = [(f, MF.bind(f, inp_new)) for f in mfacts]
    binds_old = [(f, MF.bind(f, inp_old)) for f in mfacts]
    floor_fact = next(f for f in mfacts if f.kind == "TRADE_OBJECT_FOOTPRINT")
    q13_pols = MF.policies_for(binds_new, trade="FLOOR_FINISH", space_classes=ROW_CLASS["Q-13"],
                               finish=ROW_FINISH["Q-13"])
    other_pols = {rid: MF.policies_for(binds_new, trade=Q11.rule_for(rid).trade, space_classes=ROW_CLASS[rid] or (),
                                       finish=ROW_FINISH[rid]) for rid in ROWS if rid != "Q-13"}
    assert len(q13_pols) == 1 and not any(other_pols.values()), "the floor fact reached a row outside its scope"
    old_pols = MF.policies_for(binds_old, trade="FLOOR_FINISH", space_classes=ROW_CLASS["Q-13"],
                               finish=ROW_FINISH["Q-13"])
    rows_new = build_rows(new, tp_new, C.REV_NEW_ID, owner_passage, q13_pols[0])
    rows_old = build_rows(old, tp_old, C.REV_OLD_ID, None, old_pols[0] if old_pols else None)
    leak = rows_new.pop("_leak_check")
    q13_without = rows_new.pop("_q13_without_fact")
    rows_old.pop("_leak_check", None)
    rows_old.pop("_q13_without_fact", None)
    r812 = jl(REG12 / "QORTUBA_R8_12_STATUS.json")["rows"]
    reviews = [f"{c['closure_id']}:CORROBORATED_BY_OWNER({pfact.ref})" for c in new["topology_closures"]["closures"]
               if set(map(handle, c["source_evidence_ids"])) & {"2430", "2431"}]
    pol_of = {rid: ((Q11.CEILING_FOOTPRINT,) if rid == "Q-14" else (q13_pols if rid == "Q-13" else ()))
              for rid in ROWS}
    applied_row = {rid: [floor_fact.ref] if rid == "Q-13" else [] for rid in ROWS}
    dig = {rid: digests(rows_new[rid], rid, pol_of[rid], applied_row[rid], reviews if rid == "Q-14" else [],
                        [pfact.ref] if rid == "Q-14" else []) for rid in ROWS}
    dig_nofact = digests(rows_new["Q-13"], "Q-13", (), [], [], [])
    # ---- fact outcomes per row
    outcomes = {}
    old_binding = {f.ref: b["binding"] for f, b in binds_old}
    for f, b in binds_new:
        o = {}
        for rid in ROWS:
            trade = Q11.rule_for(rid).trade
            used = f.kind == "TRADE_OBJECT_FOOTPRINT" and rid == "Q-13"
            corr = f.kind == "FINISH_SCOPE" and rid in ("Q-03", "Q-11", "Q-03P", "Q-12")
            o[rid] = MF.row_outcome(f, b, trade=trade if f.kind == "TRADE_OBJECT_FOOTPRINT" else None,
                                    space_classes=ROW_CLASS[rid] or ["CEILING_SCOPE"], used=used, corroborates=corr)
        outcomes[f.ref] = {"binding_new": b["binding"], "binding_old": old_binding[f.ref], "rows": o}
    outcomes[pfact.ref] = {"binding_new": b_new["binding"], "domains": {k: v["outcome"] for k, v in domains.items()},
                           "rows": {rid: OF.APPLIED if rid == "Q-14" else OF.CORROBORATING_ONLY for rid in ROWS},
                           "rows_meaning": "Q-14: APPLIED at RELEASE (passage-soffit note); every row: no ROW authority"}
    # ---- closure release evaluation (design only)
    auth = [c for c in new["topology_closures"]["closures"] if c["release"] == TC.AUTHORISED_FOR_SHADOW]
    cre = {c["closure_id"]: dict(CR.evaluate(c["release"], {
        "POLICY_FROZEN": WB.policy_record()["digest"] == freeze["wall_band_policy"]["digest"] and
        TC.policy_record()["digest"] == freeze["closure_policy"]["digest"],
        "CROSS_ROUTE_AGREEMENT": None, "OWNER_OR_SOURCE_CORROBORATION": all(x["matrix"] == OF.AGREES for x in per),
        "SOURCE_ANCHOR": False, "HUMAN_REVIEW": None}), evidence_parts=[handle(x) for x in c["source_evidence_ids"]],
        geometry=[round(v, 4) for v in c["geometry"]]) for c in auth}
    det = shuffle_check(work, new)
    hall = lambda r: next(s for s in r["sites"] if any("HALL" in v for v in LAB.stamps(s).values()))
    return {"R": R, "new": new, "old": old, "inp_new": inp_new, "inp_old": inp_old, "blind": blind, "freeze": freeze,
            "reproduces": reproduces, "pfact": pfact, "per": per, "domains": domains, "owner_passage": owner_passage,
            "mfacts": mfacts, "binds_new": binds_new, "binds_old": binds_old, "floor_fact": floor_fact,
            "q13_policy": q13_pols[0], "rows_new": rows_new, "rows_old": rows_old, "leak": leak,
            "q13_without": q13_without, "r812": r812, "dig": dig, "dig_q13_without_fact": dig_nofact,
            "outcomes": outcomes, "closure_release": cre, "det": det,
            "band_diff": {"NEW_K2": band_diff(jl(REG12 / "WALL_BAND_ASSEMBLY_REGISTER.json")["NEW_K2"],
                                              asm(new, inp_new)),
                          "OLD_K1": band_diff(jl(REG12 / "WALL_BAND_ASSEMBLY_REGISTER.json")["OLD_K1"],
                                              asm(old, inp_old))},
            "asm_new": asm(new, inp_new), "hall_new": hall(new), "source_anchor": source_anchor()}


def main(work, regdir, commit=None):
    import r8_13_registers as REGS
    regs, ctx = REGS.registers(build(work, commit))
    regdir = Path(regdir)
    regdir.mkdir(parents=True, exist_ok=True)
    for n, o in regs.items():
        (regdir / f"{n}.json").write_text(json.dumps(o, indent=1, ensure_ascii=False, default=str) + "\n")
    print(json.dumps({k: (v["state"], v["value"]) for k, v in ctx["rows_new"].items()}, indent=1))
    return regs, ctx


if __name__ == "__main__":
    main(*sys.argv[1:4])
