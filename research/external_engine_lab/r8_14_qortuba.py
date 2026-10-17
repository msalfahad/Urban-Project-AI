"""R8.14 lab: Qortuba AFTER the blind run of the frozen WALL_BAND_POLICY_V5 - six rows rebuilt from the TS01 sites
with door-threshold allocations (door_transition), the Hall / Lobby soffit out of the ceiling (opening_reveals),
the V4-O1 obstacle-authority audit, skirting readiness (wall_contact_path), source anchor, closure release status.

    python3 research/external_engine_lab/r8_14_qortuba.py <work> <register_dir> [code_commit]

Owner method facts enter ONLY the trade layer, after the frozen V5 topology. Project semantics live here only.
"""

from __future__ import annotations

import json
import math
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

import r8_10_claims as CL                                                                     # noqa: E402
import r8_10_qortuba as Q10                                                                   # noqa: E402
import r8_11_owner_facts as OF11                                                              # noqa: E402
import r8_11_qortuba as Q11                                                                   # noqa: E402
import r8_12_qortuba as R12                                                                   # noqa: E402
import r8_13_qortuba as R13                                                                   # noqa: E402
import r8_8_topology as LAB                                                                   # noqa: E402
from engine.source import closure_release as CR, door_transition as DT, opening_reveals as OR  # noqa: E402
from engine.source import owner_facts as OF, owner_method_facts as MF, run_manifest as RM      # noqa: E402
from engine.source import topology as T, topology_closures as TC, trade_strips as TS           # noqa: E402
from engine.source import wall_bands as WB, wall_contact_path as WC                           # noqa: E402

C = LAB.C
ROWS = LAB.ROUND1
REG13 = ROOT / "tests/r8_13/registers"
REG14 = ROOT / "tests/r8_14/registers"
METHOD = ROOT / "data/registry/OWNER_METHOD_FACTS.json"
handle = Q10.handle
jl = R12.jl
R813 = {"Q-03": 17.7425, "Q-03P": 11.685, "Q-11": 17.7425, "Q-12": 11.685, "Q-13": 111.5988, "Q-14": 141.0263}
F_CONT, F_SPLIT, F_MARBLE = ("QORTUBA-NEW-DOOR-THRESHOLD-CONTINUITY-OWNER-001", "QORTUBA-NEW-DRY-WET-TRANSITION-AT-"
                             "DOOR-PLANE-OWNER-001", "QORTUBA-NEW-MARBLE-THRESHOLD-ONLY-IF-EXPLICIT-OWNER-001")
F_REVEAL, F_SOFFIT = "QORTUBA-NEW-OPEN-PASSAGE-REVEALS-PLASTERED-OWNER-001", "QORTUBA-NEW-OPEN-PASSAGE-SOFFIT-NOT-" \
                                                                              "CEILING-OWNER-001"
F_SKIRT, F_NOSKIRT = "QORTUBA-NEW-DRY-ROOM-SKIRTING-ALL-REAL-WALLS-OWNER-001", "QORTUBA-NEW-NO-SKIRTING-FULL-WALL-" \
                                                                               "TILE-ROOMS-OWNER-001"
OUTSIDE_UNIT = "OUTSIDE_MEASURED_UNIT"
DXF = ROOT / f"data/inputs/by_sha256/{C.NEW_DXF}.dxf"
MARBLE_PATTERNS = ("marble", "threshold", "برطاش", "رخام", "عتبة", "عتبه", "granite", "جرانيت",
                   "\\U+0631\\U+062E\\U+0627\\U+0645", "\\U+0628\\U+0631\\U+0637\\U+0627\\U+0634")


def method_facts():
    return {f["fact_id"]: MF.from_record(f) for f in jl(METHOD)["facts"]}


# ---------------------------------------------------------------------------------------------- marble evidence
def marble_evidence(inp):
    """Explicit marble / threshold evidence: the whole source DXF (every layout and block, raw text), the measured
    region's texts, and the owner rule store / registries. Only an explicit record naming an opening counts."""
    raw = {}
    with open(DXF, "rb") as fh:
        data = fh.read().lower()
    for p in MARBLE_PATTERNS:
        raw[p] = data.count(p.lower().encode())
    ctx = []
    if raw["threshold"]:
        i = 0
        while True:
            i = data.find(b"threshold", i)
            if i < 0:
                break
            ctx.append(data[max(0, data.rfind(b"\n", 0, i) + 1):data.find(b"\n", i)].decode(errors="replace").strip())
            i += 1
    region = [t.value for t in inp.texts if any(p.lower() in (t.value or "").lower() for p in MARBLE_PATTERNS)]
    rules = subprocess.run(["grep", "-n", "-i", "-E", "marble|برطاش|رخام|threshold",
                            "research/qs_wall_treatment_01/pa08/qortuba/boq/owner_rules.py"],
                           capture_output=True, text=True, cwd=ROOT).stdout.strip().splitlines()
    return {"SCHEMA": "URBAN_R8_14_MARBLE_THRESHOLD_EVIDENCE_V1",
            "searched": {"source_dxf": f"{C.NEW_DXF} (raw, every layout / block / text / attribute)",
                         "region_texts": len(inp.texts), "rule_store": "owner_rules.py + data/registry",
                         "patterns": list(MARBLE_PATTERNS)},
            "raw_counts": raw, "threshold_hits_context": sorted(set(ctx)),
            "threshold_hits_meaning": "AEC display-class names (AecDbDispRepDoorThreshold*) in the DXF class table: an "
                                      "Architectural Desktop object type, not a threshold finish or a schedule entry",
            "region_text_hits": region, "rule_store_hits": rules,
            "rule_store_meaning": "US-05 (membrane upturn not broken at a threshold) - a waterproofing rule, not marble",
            "result": "NO EXPLICIT MARBLE THRESHOLD EVIDENCE FOUND", "applies": "continuous floor-transition rule",
            "owner_question": "NONE (the owner's 'sometimes' is not current-project marble authority)"}


# ---------------------------------------------------------------------------------------------- thresholds
def _locate(res, p):
    sid, _ = T.locate(res["_arr"], res["sites"], p, 0.0)
    return sid


def thresholds(res, inp, mfacts, binds):
    """Every door threshold: physical strip, transition plane, side sites / classes / finishes, allocation."""
    unit2 = res["_unit2"]
    eps_r = Q11.TP.tolerances(Q11.RT.max_abs_coordinate(inp.parts), inp.unit_native_to_mm)["eps_r"]
    names = LAB.apartment_names()
    lab_sites, internal_sites = LAB.apartment_sites(res)
    internal = {s["site_id"] for s in internal_sites}
    unit_sites = {s["site_id"] for s in lab_sites + internal_sites}
    sites = {s["site_id"]: s for s in res["sites"]}
    cl = {c.source_id: c.geometry for c in res["closures"] if c.source_id.startswith("CLOSURE|")}
    bound = {f.fact_id: b["binding"] == "APPLIES" for f, b in binds}
    centred = mfacts[F_SPLIT].ref if bound.get(F_SPLIT) and mfacts[F_SPLIT].statement.get("door_centred") else None
    out = []
    with R13.lab_rules():
        rule = Q11.FLOOR_RULE

        def side(sid):
            s = sites.get(sid)
            if s is not None and sid not in unit_sites:
                # beyond the measured unit (e.g. a common landing): not this unit's finish domain; the unit's own
                # finish meets it at the door plane (lab scope decision, taken AFTER the run - disclosed)
                return {"site": sid, "scope": OUTSIDE_UNIT, "zones": [], "class": None, "treatment": OUTSIDE_UNIT,
                        "area_m2": round(s["area_m2"], 6)}
            if s is None:
                return {"site": sid, "zones": None, "class": None, "treatment": None}
            zn = [z for z in Q10.site_zone_names(s, names, internal) if z != "UNLABELLED_INTERNAL_SPACE"]
            cls = sorted({R13.SPACE_CLASSES_V2.space_class(z) for z in zn} - {None})
            tr = R13.site_treatments(res, rule).get(sid)
            return {"site": sid, "zones": zn, "class": cls[0] if len(cls) == 1 else None, "treatment": tr,
                    "area_m2": round(s["area_m2"], 6)}
        for t in res["semantic"]["thresholds"]:
            occ = t["opening"]
            st = res["openings"][occ]
            a, b = cl[st["closure_a"]], cl[st["closure_b"]]
            fa, fb = (tuple(a[:2]), tuple(a[2:])), (tuple(b[:2]), tuple(b[2:]))
            hinge = res["roles"]["doors"][occ]["hinge"]
            site = sites[t["physical_site_id"]]
            plane = DT.transition_plane(fa, fb, hinge, eps_r=eps_r, owner_centred=centred)
            n = plane["normal_from_a"]
            mid = lambda f: ((f[0][0] + f[1][0]) / 2, (f[0][1] + f[1][1]) / 2)
            step = 5 * eps_r
            pa = (mid(fa)[0] - n[0] * step, mid(fa)[1] - n[1] * step)
            pb = (mid(fb)[0] + n[0] * step, mid(fb)[1] + n[1] * step)
            sa, sb = side(_locate(res, pa)), side(_locate(res, pb))
            outside = [k for k, v in (("A", sa), ("B", sb)) if v.get("scope") == OUTSIDE_UNIT]
            alloc = DT.allocate(site["area"], site["perimeter"], plane, sa, sb, eps_r=eps_r, marble=None) \
                if bound.get(F_CONT) and len(outside) < 2 else None
            regions = [dict(r, area_m2=round(r["area"] * unit2, 6)) for r in (alloc or {}).get("regions", [])]
            out.append({"threshold": t["threshold_id"], "physical_site": t["physical_site_id"], "door_occurrence": occ,
                        "door_symbol": res["roles"]["doors"][occ]["swing_part"],
                        "wall_opening_sources": [handle(x) for x in st["hits"]],
                        "face_closures": {"A": [round(v, 4) for v in a], "B": [round(v, 4) for v in b]},
                        "strip_m2": round(site["area"] * unit2, 6),
                        "width_mm": round(plane["width"] * inp.unit_native_to_mm, 2),
                        "thickness_mm": round(plane["thickness"] * inp.unit_native_to_mm, 2),
                        "hinge_offset_mm": round(plane["hinge_offset"] * inp.unit_native_to_mm, 3),
                        "symbol": plane.get("symbol"), "transition_plane_authority": plane["authority"],
                        "plane_offset_mm": None if plane.get("offset") is None else
                        round(plane["offset"] * inp.unit_native_to_mm, 3), "plane_fact": plane.get("fact"),
                        "side_A": sa, "side_B": sb, "marble_evidence": "NONE",
                        "sides_outside_unit": outside, "unit_boundary": len(outside) == 1,
                        "allocation_state": alloc["state"] if alloc else (OUTSIDE_UNIT if len(outside) == 2 and
                                                                          bound.get(F_CONT) else TS.EXCLUDED),
                        "allocation_authority": [mfacts[F_CONT].ref] + ([mfacts[F_SPLIT].ref] if alloc and
                                                                        alloc["state"] == DT.SPLIT else [])
                        if alloc else [], "regions": regions,
                        "reconciles": alloc is None or abs(sum(r["area"] for r in alloc["regions"]) - site["area"]) == 0,
                        "_alloc": alloc})
    return out


# ---------------------------------------------------------------------------------------------- rows
def hall_passage(res, owner_passage):
    return next((p for p in res["passages"] if abs(p["width_mm"] - owner_passage["clear_width_mm_measured"]) < 0.01),
                None)


def build_rows(res, inp, revision_id, ths, owner_passage, floor_policy, mfacts, binds):
    rows = R13_rows(res, inp, revision_id, owner_passage, floor_policy)
    bound = {f.fact_id: b["binding"] == "APPLIES" for f, b in binds}
    hp = hall_passage(res, owner_passage) if owner_passage else None
    heads = {}
    for p in res.get("passages") or []:
        heads[p["passage_id"]] = OR.WITH_HEAD if (hp is not None and p["passage_id"] == hp["passage_id"] and
                                                  bound.get(F_SOFFIT)) else None
    strips = R13.strips(res)
    alloc = {t["threshold"]: t["_alloc"] for t in ths}
    for rid in ROWS:
        row = rows[rid]
        rule = Q11.rule_for(rid)
        with R13.lab_rules():
            tr = R13.site_treatments(res, Q11.rule_for(rid))
        want = Q10.ROW_TREATMENT[rid]
        sites = {u["site"] for u in row["sites_used"]}
        aud = []
        for s in strips:
            a = TS.audit_v2(s, sites, tr, want, trade=rule.trade, allocation=alloc.get(s["id"]),
                            head=heads.get(s["id"]))
            if a["state"] != TS.NOT_IN_ROW:
                a["contribution_m2"] = round(a["contribution_m2"] * (res["_unit2"] if s["kind"] == "THRESHOLD" and
                                                                     a.get("regions") else 1.0), 6)
                aud.append(a)
        eff = TS.row_effect_v2(aud)
        base = round(sum(u["area_m2"] for u in row["sites_used"]), 6)
        row["strip_audit"] = aud
        row["strip_effect"] = eff
        row["base_site_area_m2"] = base
        rel = [b for b in row["release_blockers"] if not (
            b.startswith("PASSAGE_SOFFIT_ALLOCATION") and eff["soffit_exclusion_m2"] > 0) and not (
            b.startswith("OBJECT_FOOTPRINT_IMPLICIT") and rid == "Q-13" and floor_policy is not None)]
        add = []
        if eff["release"]:
            ex = [a for a in aud if a["state"] == TS.EXCLUDED]
            hd = [a for a in aud if a["state"] == TS.HEAD_UNRESOLVED]
            if ex:
                add.append(f"STRIP_ALLOCATION: {len(ex)} door-threshold strip(s) ({round(sum(a['area_m2'] for a in ex), 6)}"
                           " m2) have no allocation authority")
        ub = [t for t in ths if t["unit_boundary"] and t["_alloc"] and any(
            a["strip"] == t["threshold"] and a["state"] in TS.RESOLVED_V2 and a["contribution_m2"] for a in aud)]
        if ub:
            add.append("UNIT_BOUNDARY_THRESHOLD: " + "; ".join(
                f"{t['threshold']} ({t['strip_m2']} m2, {t['width_mm']} mm door to a space outside the measured unit) "
                "is split at the owner-centred door plane - the owner facts name dry / wet doors; applying the split "
                "at the unit entrance is a scope decision taken after the run (not blind-tested)" for t in ub))
        if eff["release"]:
            hd = [a for a in aud if a["state"] == TS.HEAD_UNRESOLVED]
            if hd:
                add.append("PASSAGE_HEAD_CONDITION_NOT_ESTABLISHED: " + "; ".join(
                    f"{a['strip']} ({a['area_m2']} m2) is in the ceiling site but its head condition is not "
                    "established for this revision (old QP-18 does not transfer)" for a in hd))
        row["release_blockers"] = rel[:-1] + add + rel[-1:]
        if row["state"] == "COMPUTED_SHADOW":
            if eff["blocking"]:
                row["state"], row["value"] = "BLOCKED_TRADE_RULE", None
            else:
                row["value"] = round(base + eff["threshold_contribution_m2"] - eff["soffit_exclusion_m2"], 4)
                if ub:
                    c = sum(a["contribution_m2"] for a in aud if a["strip"] in {t["threshold"] for t in ub})
                    row["counterfactual_unit_boundary"] = {
                        "unit_floor_stops_at_unit_face": round(row["value"] - c, 4),
                        "split_at_door_plane (computed)": row["value"],
                        "whole_strip_to_unit": round(row["value"] - c + sum(t["strip_m2"] for t in ub), 4)}
    return rows


def R13_rows(res, inp, revision_id, owner_passage, floor_policy):
    """The R8.13 row assembly (class rule v2; the floor footprint policy for Q-13 only) WITHOUT its V1 strip audit."""
    tp = Q11.topo(inp, CL.load()[0])
    with R13.lab_rules((Q11.CEILING_FOOTPRINT,)):
        base = R12.rows(res, tp, revision_id, owner_passage)
    if floor_policy is not None:
        with R13.lab_rules((Q11.CEILING_FOOTPRINT, floor_policy)):
            base["Q-13"] = R12.rows(res, tp, revision_id, owner_passage)["Q-13"]
    return base


def obstacle_audit(res, rows):
    """V4-O1: sites whose holes are cut by isolated closed loops without physical authority (V5 isolated_loops)."""
    iso = {x["entity"]: x["segments"] for x in res["wall_bands"]["isolated_loops"]}
    iso_src = {s for v in iso.values() for s in v}
    out = []
    for s in res["sites"]:
        hs = set(s.get("hole_source_ids", []))
        if not hs or not hs & iso_src:
            continue
        pure = hs <= iso_src
        out.append({"site": s["site_id"], "labels": sorted({v for vs in LAB.stamps(s).values() for v in vs}),
                    "site_area_m2": round(s["area_m2"], 6),
                    "hole_area_m2": round((s["gross_outer_area"] - s["area"]) * res["_unit2"], 6) if pure else None,
                    "holes_only_isolated_loops": pure,
                    "entities": sorted({handle(x + "|0") for x in iso if set(iso[x]) & hs}),
                    "rows": sorted(r for r, v in rows.items() if s["site_id"] in {u["site"] for u in v["sites_used"]})})
    return out


def digests(row, rid, policies, facts_row, reviews, facts_release):
    ta = row["trade_authority"]
    rad = RM.row_authority_digest(
        row["run_input_digest"], row_id=rid, row_method=f"TS01 (WALL_BAND_POLICY_V5) + trade layer + {TS.POLICY_ID_V2} + "
        f"{DT.POLICY_ID} + {OR.POLICY_ID} (lab rows)", trade_rules=[ta["rule"]],
        semantic_class_rules=[f"{R13.SPACE_CLASSES_V2.rule_id}@v{R13.SPACE_CLASSES_V2.version}"] if rid != "Q-14" else [],
        footprint_policies=[f"{p.policy_id}@v{p.version}:{p.trade}:{p.treatment}" for p in policies],
        row_claims=row["claims_applied"], owner_facts_applied=facts_row)
    rel = RM.release_input_digest(rad["digest"], source_anchor_state="DWG_DXF_IDENTITY_NOT_ESTABLISHED", reviews=reviews,
                                  release_policy="SHADOW_ONLY_NO_RELEASE_GATE", release_blockers=row["release_blockers"],
                                  owner_facts_applied=facts_release)
    return {"TOPOLOGY_RUN_INPUT_DIGEST": row["run_input_digest"], "ROW_AUTHORITY_DIGEST": rad,
            "RELEASE_INPUT_DIGEST": rel}


def skirting_readiness(res, rows, mfacts):
    iso = {x["entity"] for x in res["wall_bands"]["isolated_loops"]}
    sites = {s["site_id"]: s for s in res["sites"]}
    per = {}
    for u in rows["Q-13"]["sites_used"]:
        p = WC.path(WC.site_edges(res["_arr"], sites[u["site"]]), isolated_entities=iso)
        per[u["site"]] = {"zones": u["zones"], "edges_by_class": {k: v["edges"] for k, v in p["by_class"].items()},
                          "withheld": p["withheld"]}
    return {"SCHEMA": "URBAN_R8_14_SKIRTING_READINESS_V1", "policy": WC.policy_record(),
            "facts": [mfacts[F_SKIRT].ref, mfacts[F_NOSKIRT].ref],
            "dry_rooms_classified": per, "no_skirting_classes": ["WET_SERVICE_ROOM", "SERVICE_ROOM"],
            "quantity": "NOT PRODUCED",
            "missing_components": [
                "a FROZEN, blind-tested WALL_CONTACT_PATH policy (built and synthetically tested this round; never run "
                "under freeze + blind protocol)",
                "a jamb-return rule: the Hall / Lobby jamb faces are TOPOLOGY_CLOSURE edges (zero by rule); their "
                "physical 200 mm returns need source / owner length authority before they can carry skirting",
                "a glazed-opening rule for the new revision (QP-09 is an old-revision rule store entry)",
                "the V4-O1 hole edges (UNPROVEN_OBSTACLE) withheld until the obstacle has physical authority"],
            "never_used": "a room polygon perimeter"}


def source_anchor():
    import hashlib
    dwg = ROOT / f"data/inputs/by_sha256/{Q10.DWG_CANDIDATE}.dwg"
    binp = Path("/tmp/ldwg/programs/dwgread")
    rec = {"SCHEMA": "URBAN_R8_14_SOURCE_ANCHOR_STATUS_V1", "dxf_sha256": C.NEW_DXF, "dwg_sha256": Q10.DWG_CANDIDATE,
           "dwg_present": dwg.exists()}
    if binp.exists():
        r = subprocess.run([str(binp), "--version"], capture_output=True, text=True)
        run = subprocess.run([str(binp), "-v1", "-O", "JSON", "-o", "/dev/null", str(dwg)], capture_output=True,
                             text=True, timeout=600)
        errs = sorted({ln.strip() for ln in (run.stderr + run.stdout).splitlines() if "ERROR" in ln})
        rec["decoder"] = {"tool": "libredwg dwgread", "version": (r.stdout or r.stderr).strip(),
                          "binary_sha256": hashlib.sha256(binp.read_bytes()).hexdigest(),
                          "pinned_sha256_r8_7": "fe49cf28f5ee5cd84cbb7b9c7ae0475586cedbfcb1a9ca9bc2cab8c72e094c47",
                          "input_sha256": hashlib.sha256(dwg.read_bytes()).hexdigest() if dwg.exists() else None,
                          "exit_code": run.returncode, "errors": errs,
                          "capability_signature": "AC1032 R2018: Header / Classes / AcDbObjects sections NOT readable",
                          "entity_coverage": 0, "unsupported_classes": "all (no object section decoded)",
                          "handle_preservation": "NOT_TESTABLE", "block_lineage": "NOT_TESTABLE",
                          "geometry_comparison": "NOT_POSSIBLE"}
    rec.update({"state": "NOT_ESTABLISHED",
                "correction": "R8.13 said 'no local DWG decoder is installed': the pinned libredwg 0.13.3 build IS "
                              "present (off PATH, /tmp/ldwg) - it was re-run here and still cannot read this AC1032 file. "
                              "K1 is built on the same reader. ezdxf reads DXF only. Nothing was downloaded",
                "confidence": "NONE for exact identity; R8.7 header-level corroboration (same creator, creation time, "
                              "editing time + ~2 min) is consistent but cannot exclude an edit",
                "effect": "SOURCE_ANCHOR stays a release blocker on every new-revision row; R8.14 does not fail on it",
                "next": "a pinned AC1032-capable reader (hash-locked), or an owner-supplied DXF re-export with a "
                        "checksum chain from the DWG"})
    return rec


# ---------------------------------------------------------------------------------------------- the build
def build(work, commit=None):
    R = R13.runs(work, commit)
    new, old = R["new"], R["old"]
    inp_new, inp_old = R["inputs"]["NEW_K2"], R["inputs"]["OLD_K1"]
    blind = jl(REG14 / "BLIND_QORTUBA_V5_RESULT.json")
    freeze = jl(REG14 / "R8_14_V5_FREEZE.json")
    assert WB.policy_record()["digest"] == freeze["wall_band_policy"]["digest"]
    reproduces = {"closures": sorted(c["closure_id"] for c in new["topology_closures"]["closures"]) ==
                  sorted(c["closure_id"] for c in blind["NEW_K2"]["closures"]),
                  "topology_digest": new["run_manifest"]["RUN_INPUT_DIGEST"] == blind["NEW_K2"]["run_input_digest"]}
    pfact, b_new, per, domains = R12.compare_fact(OF11.load()[0], inp_new, new)
    owner_passage = OF11.hall_lobby_passage(inp_new, new, {"fact": pfact.ref, "state": b_new["binding"]})
    mf13 = R13.finish_facts()
    b13 = [(f, MF.bind(f, inp_new)) for f in mf13]
    floor_pol = MF.policies_for(b13, trade="FLOOR_FINISH", space_classes=["DRY_INTERNAL_ROOM"],
                                finish="PORCELAIN_DRY_FLOOR")[0]
    mfacts = method_facts()
    binds_new = [(f, MF.bind(f, inp_new)) for f in mfacts.values()]
    binds_old = [(f, MF.bind(f, inp_old)) for f in mfacts.values()]
    ths_new = thresholds(new, inp_new, mfacts, binds_new)
    ths_old = thresholds(old, inp_old, mfacts, binds_old)
    rows_new = build_rows(new, inp_new, C.REV_NEW_ID, ths_new, owner_passage, floor_pol, mfacts, binds_new)
    rows_old = build_rows(old, inp_old, C.REV_OLD_ID, ths_old, None, None, mfacts, binds_old)
    hp = hall_passage(new, owner_passage)
    reveals = OR.passage_reveals(
        hp, head=OR.WITH_HEAD, clear_height=pfact.statement.get("clear_height_m"),
        jamb_authority={OR.LEFT_JAMB: f"{pfact.ref}: H2430 REAL_WALL_END", OR.RIGHT_JAMB: f"{pfact.ref}: H2431 REAL_WALL_END"},
        finish=mfacts[F_REVEAL].statement["surfaces"], unit_to_m=inp_new.unit_native_to_mm / 1000,
        source_refs=[mfacts[F_REVEAL].ref, mfacts[F_SOFFIT].ref, pfact.ref])
    soffit_audit = next(a for a in rows_new["Q-14"]["strip_audit"] if a["strip"] == hp["passage_id"])
    guard = OR.ownership_guard([(hp["passage_id"], "TOP_SOFFIT")] +
                               [(hp["passage_id"], "CEILING")] * (soffit_audit["state"] != TS.SOFFIT_EXCLUDED))
    obst = obstacle_audit(new, rows_new)
    for o in obst:
        for rid in o["rows"]:
            r = rows_new[rid]
            if o["hole_area_m2"] is not None:
                r["release_blockers"].insert(len(r["release_blockers"]) - 1,
                                             f"OBSTACLE_AUTHORITY_UNPROVEN: {o['hole_area_m2']} m2 excluded from "
                                             f"{'/'.join(o['labels'][:1])} by isolated closed loop(s) "
                                             f"H{'/H'.join(o['entities'])} (layer-only; no physical authority)")
                r["counterfactual_if_not_an_obstacle"] = round(r["value"] + o["hole_area_m2"], 4) if r["value"] else None
    facts_row = {rid: [] for rid in ROWS}
    for rid in ROWS:
        ts = [a for a in rows_new[rid]["strip_audit"] if a["state"] in TS.RESOLVED_V2]
        if ts:
            facts_row[rid] += [mfacts[F_CONT].ref] + ([mfacts[F_SPLIT].ref] if any(a["state"] == DT.SPLIT for a in ts)
                                                       else [])
    facts_row["Q-13"] = [R13.finish_facts()[0].ref] + facts_row["Q-13"]
    if soffit_audit["state"] == TS.SOFFIT_EXCLUDED:
        facts_row["Q-14"] += [mfacts[F_SOFFIT].ref]
    pol_of = {rid: ((Q11.CEILING_FOOTPRINT,) if rid == "Q-14" else ((floor_pol,) if rid == "Q-13" else ())) for rid in ROWS}
    reviews = [f"{c['closure_id']}:CORROBORATED_BY_OWNER({pfact.ref})" for c in new["topology_closures"]["closures"]
               if set(map(handle, c["source_evidence_ids"])) & {"2430", "2431"}]
    dig = {rid: digests(rows_new[rid], rid, pol_of[rid], sorted(set(facts_row[rid])), reviews if rid == "Q-14" else [],
                        [pfact.ref] if rid == "Q-14" else []) for rid in ROWS}
    auth = [c for c in new["topology_closures"]["closures"] if c["release"] == TC.AUTHORISED_FOR_SHADOW]
    cre = {c["closure_id"]: dict(CR.evaluate(c["release"], {
        "POLICY_FROZEN": WB.policy_record()["digest"] == freeze["wall_band_policy"]["digest"] and
        TC.policy_record()["digest"] == freeze["closure_policy"]["digest"],
        "CROSS_ROUTE_AGREEMENT": None, "OWNER_OR_SOURCE_CORROBORATION": all(x["matrix"] == OF.AGREES for x in per),
        "SOURCE_ANCHOR": False, "HUMAN_REVIEW": None}), evidence_parts=[handle(x) for x in c["source_evidence_ids"]],
        geometry=[round(v, 4) for v in c["geometry"]]) for c in auth}
    return {"R": R, "new": new, "old": old, "inp_new": inp_new, "blind": blind, "freeze": freeze,
            "reproduces": reproduces, "pfact": pfact, "per": per, "domains": domains, "owner_passage": owner_passage,
            "mfacts": mfacts, "binds_new": binds_new, "binds_old": binds_old, "floor_policy": floor_pol,
            "thresholds_new": ths_new, "thresholds_old": ths_old, "rows_new": rows_new, "rows_old": rows_old,
            "reveals": reveals, "soffit_audit": soffit_audit, "ownership_guard": guard, "hall_passage": hp,
            "obstacles": obst, "dig": dig, "closure_release": cre, "marble": marble_evidence(inp_new),
            "skirting": skirting_readiness(new, rows_new, mfacts), "source_anchor": source_anchor(),
            "band_diff_v4_v5": {k: {"v4_counts": jl(REG13 / "BLIND_QORTUBA_V4_RESULT.json")[k]["counts"],
                                    "v5_counts": blind[k]["counts"],
                                    "v4_digest": jl(REG13 / "BLIND_QORTUBA_V4_RESULT.json")[k]["run_input_digest"],
                                    "v5_digest": blind[k]["run_input_digest"]} for k in ("NEW_K2", "OLD_K1")},
            "det": R13.shuffle_check(work, new)}


def main(work, regdir, commit=None):
    import r8_14_registers as REGS
    regs, ctx = REGS.registers(build(work, commit))
    regdir = Path(regdir)
    regdir.mkdir(parents=True, exist_ok=True)
    for n, o in regs.items():
        (regdir / f"{n}.json").write_text(json.dumps(o, indent=1, ensure_ascii=False, default=str) + "\n")
    print(json.dumps({k: (v["state"], v["value"]) for k, v in ctx["rows_new"].items()}, indent=1))
    return regs, ctx


if __name__ == "__main__":
    main(*sys.argv[1:4])
