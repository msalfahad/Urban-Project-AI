"""R8.8 registers that are not computed from geometry: owner actions (only what the owner can attach / confirm /
approve / decide), engineering actions (everything Urban does itself), the source sub-part identity schema, and the
R8.8 decision register (decisions, findings, gates, answers, recommendation). Reads the topology registers written by
r8_8_topology.py from the same register directory.

    python3 research/external_engine_lab/r8_8_registers.py <register_dir>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import canonical_input as CI, geometry_role as GR, region_membership as RM  # noqa: E402
from engine.source import topology_policy as TP                                                # noqa: E402

R87_OWNER = ROOT / "tests/r8_7/registers/OWNER_ACTION_REGISTER.json"
ENGINEERING = ("ESTABLISH_NEW_DWG_SOURCE_IDENTITY", "ALLOW_DECODER_INSTALL_IN_ENVIRONMENT",
               "ANCHOR_SELECTED_PLAN_TO_EXACT_NEW_DWG")


def load(regdir, name):
    return json.loads((Path(regdir) / f"{name}.json").read_text())


def owner_actions():
    v4 = json.loads(R87_OWNER.read_text())
    keep, moved = [], []
    for a in v4["actions"]:
        if a["action_id"] in ENGINEERING:
            moved.append(a["action_id"])
            continue
        a = dict(a)
        if a["action_id"] == "SUPPLY_QORTUBA_NEW_REVISION_DWG":
            a["status"] = "FILE_RECEIVED"
            a["outstanding_request"] = False
            a["note"] = ("the owner supplied the DWG (sha256 e4babbc2...); nothing more is asked of the owner for it. "
                         "Its identity with the DXF is an Urban engineering task (ENGINEERING_ACTION_REGISTER)")
        if a["action_id"] == "APPROVE_QORTUBA_NEW_ROUND1_BASELINE":
            a["status"] = "NOT_REQUESTED_YET"
            a["outstanding_request"] = False
            a["note"] = ("deliberately not asked: the new-revision topology is not stable enough to approve "
                         "(R8.8: Q-03/Q-11/Q-13/Q-14 blocked on the new revision)")
        if a["status"] == "OPEN":
            a["needed_for_next_coding_round"] = False
            a["outstanding_request"] = False
            a["note"] = (a.get("note", "") + " Standing decision; not needed for the next coding round and not "
                         "re-asked in R8.8.").strip()
        keep.append(a)
    return {"SCHEMA": "URBAN_R8_8_OWNER_ACTION_REGISTER_V5", "supersedes": "URBAN_R8_7_OWNER_ACTION_REGISTER_V4",
            "rule": "an owner action is only something the owner can attach, confirm, approve or decide; installing "
                    "tools, running comparisons and re-anchoring claims are engineering actions",
            "moved_to_engineering": moved,
            "required_now": [],
            "headline": "NO OWNER ACTION REQUIRED FOR THE NEXT CODING ROUND",
            "actions": keep}


def engineering_actions(regdir):
    six = load(regdir, "QORTUBA_SIX_ROW_STATUS")
    roles = load(regdir, "GEOMETRY_ROLE_REGISTER")
    unknown = roles["runs"]["NEW_K2"]["unknown_by_layer"]
    return {"SCHEMA": "URBAN_R8_8_ENGINEERING_ACTION_REGISTER_V1",
            "rule": "work Urban does itself; none of it waits on the owner",
            "actions": [
                {"action_id": "ESTABLISH_NEW_DWG_SOURCE_IDENTITY", "from": "R8.7 owner register", "status": "OPEN",
                 "what": "compare DWG e4babbc2 with DXF df0e1d69 with a pinned decoder that reads AutoCAD 2018 (AC1032) "
                         "object sections; re-anchor only on SAME_EXACT_SOURCE_REVISION",
                 "state_now": "SOURCE_IDENTITY = NOT_ESTABLISHED (not forced)", "critical_path_for_topology": False},
                {"action_id": "OBTAIN_PINNED_AC1032_DECODER", "from": "R8.7 owner register (ALLOW_DECODER_INSTALL_IN_"
                 "ENVIRONMENT)", "status": "OPEN", "what": "environment / tooling: a newer LibreDWG build or the ODA "
                 "File Converter, pinned by hash; the cloud network policy currently denies github.com and ftp.gnu.org",
                 "owner_action": False, "unpinned_download": "never"},
                {"action_id": "ANCHOR_SELECTED_PLAN_TO_EXACT_NEW_DWG", "from": "R8.7 owner register", "status":
                 "BLOCKED_BY_ESTABLISH_NEW_DWG_SOURCE_IDENTITY", "what": "re-anchor the four new-revision owner claims "
                 "(supersede, keep history)"},
                {"action_id": "ROLE_EVIDENCE_FOR_UNKNOWN_GEOMETRY", "status": "OPEN",
                 "what": "unknown-role geometry blocks Qortuba rooms: " + ", ".join(
                     f"{k} ({v['parts']} parts)" for k, v in sorted(unknown.items()) if v["sites_blocked"]),
                 "options": ["a reviewed, revision-scoped role claim (needs an authority path; NOT requested from the "
                             "owner in R8.8)", "structural evidence rules that do not use the layer name alone"],
                 "never": "fuzzy layer-name matching ('FIRNTUR' ~ 'FURNITURE') or a project-specific lexicon entry"},
                {"action_id": "SEMANTIC_SUBDIVISION_OF_CONNECTED_SPACES", "status": "OPEN",
                 "what": "physically connected spaces with two room stamps (old: M.B.ROOM + DRESS; new: HALL + BED.ROOM "
                         "+ BATH) are REVIEW_REQUIRED; a subdivision needs source evidence (a drawn threshold, a finish "
                         "boundary) - never wet-wins / first / largest / alphabetical"},
                {"action_id": "TS01_SECOND_DRAWING_FAMILY_SHADOW", "status": "PROPOSED_NEXT_ROUND",
                 "what": "run TS01 shadow on P7757 to test the door / glazing closure rules on a second drafting style "
                         "(no change to its published outputs)"},
                {"action_id": "RETIRE_QS01_FOR_ROUND1_ROWS", "status": "NOT_NOW",
                 "what": "QS01 stays research/legacy; no migration while TS01 rows are blocked"}],
            "six_row_snapshot": {k: {r: v["state"] for r, v in rows.items()} for k, rows in six["rows"].items()}}


def subpart_schema():
    return {"SCHEMA": "URBAN_R8_8_SOURCE_SUBPART_IDENTITY_SCHEMA_V1",
            "key": "revision_id | H<source handle> | insert path ('/'-joined, MINSERT cells as '<handle>[c,r]') | "
                   "realised kind | source sub-part",
            "source_sub_part": {"LINE": "0", "ARC": "0", "CIRCLE": "0", "ELLIPSE": "0",
                                "LWPOLYLINE": "span index i (vertex i -> i+1), degenerate spans keep their index and "
                                              "realise nothing; a bulged span is ARC (or ELLIPTICAL_ARC under a "
                                              "non-uniform map) with the SAME index",
                                "curve converted under transform": "same source entity + same sub-part; the realised "
                                                                   "kind (ELLIPTICAL_ARC) is the conversion role",
                                "MINSERT": "source insert + grid-cell label in the insert path + child + sub-part",
                                "K2 (ezdxf) exploded parts": "None: ezdxf's virtual_entities() does not name the "
                                                              "source span -> key None -> METHOD_INPUT_INCOMPLETE"},
            "where_set": "the kernels (K1 kernel.py, K2 kernel_ezdxf.py) record Lineage.sub_part from source structure "
                         "while walking the entity; canonical_build copies it; nothing counts realised output",
            "never": ["an ordinal over realised output", "a coordinate hash", "nearest entity", "sorted-by-coordinate index"],
            "missing": "key None -> METHOD_INPUT_INCOMPLETE (missing parts.source_part_id)",
            "proof": ["tests/r8_8/test_r8_8_subpart_identity.py: shuffle, unrelated insertion, degenerate span, MINSERT "
                      "cells, missing sub-part, K2 span indices"]}


def decision_register(regdir):
    xr = load(regdir, "OLD_QORTUBA_CROSS_ROUTE")
    six = load(regdir, "QORTUBA_SIX_ROW_STATUS")
    ell = load(regdir, "ELLIPSE_EXCLUSION_AUDIT")
    new = load(regdir, "NEW_QORTUBA_TOPOLOGY")
    roles = load(regdir, "GEOMETRY_ROLE_REGISTER")
    pol = TP.record()
    old = six["rows"]["OLD_K1"]
    nr = six["rows"]["NEW_K2"]
    rooms = [{"site": r["site_id"], "stamps": r["stamps"], "area_m2": r["area_m2"], "status": r["status"],
              "issues": r["issues"]} for r in new["rooms"] if r["stamps"]]
    bx = roles["new_revision_bound_xref_audit"]
    return {
        "SCHEMA": "URBAN_R8_8_DECISION_REGISTER_V1",
        "assessment_before_coding": {
            "1_biggest_risk_topology_not_decoder": "YES: the decoder fixes source identity; the room path amplified "
                                                   "4.4e-11 into 1.64 m2 on ONE route",
            "2_perfect_parser_makes_QS01_safe": "NO: raster cells, exact axis predicates and band heuristics are "
                                                 "discontinuous in their input; a perfect parser still sits on cliffs",
            "3_H584_unacceptable": "YES",
            "4_admission_before_topology": "YES",
            "5_R8_7_membership_exact_for_curves": "NO: 5-point sampling",
            "6_R8_7_source_part_id_source_stable": "NO: an ordinal over realised output per kind",
            "7_safer_architecture": "YES, implemented: a vector topology with NO axis predicate, three tolerance bands "
                                    "and a two-build stability certificate (a site is certified only if identical at "
                                    "eps_n and eps_r), positive role admission, closures only from proven openings, "
                                    "label occurrences from source structure"},
        "decisions": [
            {"id": "R88-D01", "decision": "TS01 (engine/source/topology + room_topology) replaces QS01 as the room / space "
                                          "topology path in SHADOW; QS01 stays research/legacy only"},
            {"id": "R88-D02", "decision": "TOPOLOGY_TOLERANCE_POLICY_V1 frozen (digest " + pol["digest"][:16] + "): "
                                          "eps_n = 2**-30 x max|coord|, eps_r = 1 mm via the unit claim, jamb 0.25"},
            {"id": "R88-D03", "decision": "region membership exact (RM-EXACT-1, RM-TANGENT-1)"},
            {"id": "R88-D04", "decision": "source sub-part identity from source structure (Lineage.sub_part); R8.6 "
                                          "calculation path re-frozen deliberately (kernel.py)"},
            {"id": "R88-D05", "decision": "a method exclusion needs role authority (MethodExclusion); the R8.7 bare "
                                          "declaration and its test are superseded; QS01 contract v2"},
            {"id": "R88-D06", "decision": "visibility is an authority for parts, texts and dimensions; nothing is VISIBLE "
                                          "by default"},
            {"id": "R88-D07", "decision": "ROOM TOPOLOGY consumes only TOPOLOGY_BOUNDARY / STRUCTURAL_OBSTACLE / "
                                          "GLAZING_BOUNDARY / OPENING_BOUNDARY; unknown blocks the sites it touches"},
            {"id": "R88-D08", "decision": "two stamps in one physical space = MULTIPLE_SEMANTIC_LABELS (REVIEW); no rule "
                                          "picks a winner"},
            {"id": "R88-D09", "decision": "owner register V5: only owner-doable actions; tooling / comparison / "
                                          "re-anchoring moved to the engineering register"},
            {"id": "R88-D10", "decision": "the new DWG identity stays NOT_ESTABLISHED; not on the topology critical path"}],
        "findings": [
            {"id": "F-R88-01", "finding": "R8.7 region sampler unsafe: an arc whose 5 samples are inside crossed the "
                                          "boundary (test A); same for an ellipse between parameters (test B)"},
            {"id": "F-R88-02", "finding": "R8.7 part_index was a per-kind ordinal over realised output: a polyline's "
                                          "later spans changed index when an earlier span was degenerate or of another "
                                          "kind; ezdxf-exploded parts had no source span at all (now None, fail closed)"},
            {"id": "F-R88-03", "finding": "R8.7 builders marked every TEXT and DIMENSION VISIBLE (no layer state, no "
                                          "dynamic state); a text under an unresolved dynamic block could label a room"},
            {"id": "F-R88-04", "finding": "R8.7 bare exclusions let 8 ellipses out with no authority; all 8 are now "
                                          "proven door swings (GR-02) with established closures"},
            {"id": "F-R88-05", "finding": "the legacy QS01 path has exact axis predicates and raster cells; H584 "
                                          "(4.4e-11) moved 1.6425 m2 BED.ROOM <-> UNLABELLED; TS01 has no axis predicate"},
            {"id": "F-R88-06", "finding": "FIRNTUR (furniture by name, misspelled) has no lexicon role and blocks HALL "
                                          "and M.B.ROOM/DRESS; the R8.5 active-path profile even listed it as WALL-like"},
            {"id": "F-R88-07", "finding": "open passages join physically connected spaces: old M.B.ROOM + DRESS and HALL "
                                          "+ lobby; new HALL + BED.ROOM + BATH (the redrawn partition). The legacy method "
                                          "split them by chords without source evidence"},
            {"id": "F-R88-08", "finding": "post-freeze (found by the K1/K2 run): a near-collinear overlap could create "
                                          "a crossing from a near-zero determinant -> crossings now need ends beyond eps "
                                          "on both sides (no tolerance number changed)"},
            {"id": "F-R88-09", "finding": "post-freeze (found by the K1/K2 run): a zero-length probe piece at a shared "
                                          "corner let an unknown line 'touch' a site on one route only -> split "
                                          "parameters within eps merged"},
            {"id": "F-R88-10", "finding": "post-freeze (found by the new-revision run): a room touching both closures of "
                                          "one door was classed OPENING_SITE -> an opening site must lie between them"},
            {"id": "F-R88-11", "finding": "legacy Q-03 17.8625 includes one bathroom's door threshold strip (0.12 m2); "
                                          "TS01 keeps every opening strip as its own OPENING_SITE (17.7425): "
                                          "METHOD_DIFFERENCE, a trade rule for later, not a topology error"},
            {"id": "F-R88-12", "finding": f"new revision: bound-xref block 'BED 3' ({bx[0]['parts'] if bx else 0} parts) "
                                          "proven FURNITURE (GR-03) and excluded; three 'SF3' occurrences (81 parts, "
                                          "layer PM) have no role evidence -> UNKNOWN -> HALL blocked"},
            {"id": "F-R88-13", "finding": "unknown layers '0', RCC, BB, Layer4, BOUNDRY W block only the stair core and "
                                          "the roof; OFFICE NAME (title logo, 571 parts + 37 unrealised REGIONs) touches "
                                          "no bounded site"},
            {"id": "F-R88-14", "finding": "unrealised source entities (REGION / ACIS, RTEXT, proxies, xref content) were "
                                          "invisible to every room method; TS01 now accounts for them per layer"},
            {"id": "F-R88-15", "finding": "the old Q-14 has no TS01 ceiling basis: the owner's ceiling = floor claim is "
                                          "scoped to REV_NEW (OWNER_SCOPE_MISMATCH for REV_OLD), as intended"},
            {"id": "F-R88-16", "finding": "any visible text inside a site counts as a label occurrence (conservative); "
                                          "no annotation text sits inside a Qortuba apartment room"},
            {"id": "F-R88-17", "finding": "no frozen / off layer exists in either Qortuba revision (both routes agree); "
                                          "three unresolved dynamic blocks exist in the new file, none in the region"}],
        "post_freeze_changes": {"tolerance_numbers": "unchanged", "fixes": ["F-R88-08", "F-R88-09", "F-R88-10"],
                                "freeze_commit": "9f77e4d"},
        "gates": {"MIGRATION_PLANNING_READY": "YES", "MIGRATION_EXECUTION_READY": "NO", "PRODUCTION_MIGRATION": "NO",
                  "TS01_ROOM_TOPOLOGY": "IMPLEMENTED_SHADOW", "QS01": "LEGACY_RESEARCH_ONLY",
                  "OLD_QORTUBA_ROUTE_STABLE_TOPOLOGY": "YES" if xr["comparison"]["same_topology"] else "NO",
                  "NEW_DWG_SOURCE_IDENTITY": "NOT_ESTABLISHED", "OWNER_ACTION_REQUIRED_NOW": "NONE"},
        "answers": {
            "1_r87_sampler_unsafe": "YES (tests A, B reproduce the miss)",
            "2_membership_now_exact": "YES: exact bounds and edge intersections for SEGMENT / ARC / CIRCLE / "
                                      "ELLIPTICAL_ARC; eps_n noise only; tangent rule frozen",
            "3_r87_identity_order_dependent": "YES (per-kind realised ordinal)",
            "4_subpart_identity_explicit": "YES (Lineage.sub_part from source structure, both routes)",
            "5_shuffle_changes_identity": "NO (tests: shuffle, unrelated insertion)",
            "6_visibility_authoritative": "YES for parts, texts and dimensions (entity flag, frozen / off layer, ByLayer, "
                                          "dynamic state); layer table not read -> VISIBILITY_UNRESOLVED",
            "7_ellipses_safe_to_exclude": "YES, all eight, by proven role (not by declaration)",
            "8_ellipse_counts": ell["classification_counts"],
            "9_why_205_furniture_parts_affected_MB_ROOM": "the legacy room method had no admission layer: every curve in "
                                                          "the region entered its band / raster arrangement, so the "
                                                          "bound-xref bed block's lines bounded cells inside M.B.ROOM",
            "10_can_furniture_enter_topology": "NO: proven furniture is excluded; unproven furniture-like geometry is "
                                               "UNKNOWN and blocks its room",
            "11_tolerance_policy": "three bands + certificate: noise eps_n = 2**-30 x max|coord| (numeric "
                                   "representation), authored eps_r = 1 mm (via the unit claim); a site counts only if "
                                   "identical at both; no axis predicate exists",
            "12_frozen_before_totals": "the numbers yes (before any Qortuba topology run); the policy register and the "
                                       "TS01 rules were committed (9f77e4d) after the old-K1 development run and before "
                                       "the K2 cross-route run and the new-revision diagnostic",
            "13_old_k1_vs_k2_same_topology": "YES: " + f"{xr['comparison']['common_site_ids']} sites, identical ids, "
                                             "labels, issues, contents; max area difference "
                                             f"{xr['comparison']['max_area_difference_m2']:.1e} m2; rows equal: "
                                             f"{xr['rows_equal']}",
            "14_H584_can_move_area": "NO (sites bounded by H584 identical across routes)",
            "15_above_tolerance_perturbation": "inside the ambiguous band -> TOLERANCE_SENSITIVE (REVIEW); above eps_r -> "
                                               "the topology genuinely changes (rooms merge -> MULTIPLE_SEMANTIC_LABELS)",
            "16_two_labels_one_space": "MULTIPLE_SEMANTIC_LABELS -> REVIEW_REQUIRED; a stamp is one source occurrence",
            "17_title_block_room": "NO (GR-01 / GR-15 never admitted; a cut frame occurrence blocks the input)",
            "18_new_revision_sites": rooms,
            "19_rows_computable": {"OLD (both routes)": {r: [v["state"], v["value"]] for r, v in old.items()},
                                   "NEW": {r: [v["state"], v["value"]] for r, v in nr.items()}},
            "20_what_blocks": {r: v["blockers"] for r, v in nr.items() if v["blockers"]},
            "21_ac1032_decoder_relevant_to_migration": "YES for anchoring the new revision before any migration; NOT for "
                                                       "the topology architecture",
            "22_biggest_remaining_technical_risk": "role evidence and semantic subdivision: unknown-role geometry and "
                                                   "physically connected multi-room spaces now block most rows; the "
                                                   "door / glazing closure rules are proven on one drafting family only",
            "23_owner_action_now": "NONE (NO OWNER ACTION REQUIRED FOR THE NEXT CODING ROUND)",
            "24_next_round": "R8.9 role evidence + semantic subdivision with authority paths, and TS01 shadow on a second "
                             "drawing family (P7757) - no migration"},
        "recommendation": "do not migrate; keep QS01 legacy; make TS01's blockers resolvable by evidence (reviewed role "
                          "claims with an authority path, evidenced subdivision), then prove TS01 on a second drawing "
                          "family before any baseline approval"}


def main(regdir):
    regdir = Path(regdir)
    regs = {"OWNER_ACTION_REGISTER": owner_actions(), "ENGINEERING_ACTION_REGISTER": engineering_actions(regdir),
            "SOURCE_SUBPART_IDENTITY_SCHEMA": subpart_schema(), "R8_8_DECISION_REGISTER": decision_register(regdir)}
    for k, v in regs.items():
        (regdir / f"{k}.json").write_text(json.dumps(v, indent=1, default=str) + "\n")
    print(sorted(regs), CI.COMPLETE, GR.POLICY_ID, RM.POLICY["id"])


if __name__ == "__main__":
    main(sys.argv[1])
