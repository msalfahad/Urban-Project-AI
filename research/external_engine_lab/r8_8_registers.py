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
                {"action_id": "ADMIT_BLOCK_HOSTED_BUILDING_GEOMETRY", "status": "OPEN",
                 "what": "an evidence rule for walls inside an insert occurrence whose block definition is a building "
                         "assembly (F-R88-18); until then such plans fail closed"},
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
            {"id": "R88-D10", "decision": "the new DWG identity stays NOT_ESTABLISHED; not on the topology critical path"},
            {"id": "R88-D11", "decision": "ADDENDUM: architecture = TS01 vector authority + independent GEOS cross-check "
                                          "(topology_crosscheck; can only withhold a site) + raster QA only; wall_solid "
                                          "/ free_space are not the spine"},
            {"id": "R88-D12", "decision": "ADDENDUM: tolerances are classed (numeric / node / material / region / "
                                          "comparison); V1 kept unchanged (no V2); the noise / authored separation is "
                                          "measured per drawing (topology_policy.separation, NOISE_NEAR_EPS_N)"},
            {"id": "R88-D13", "decision": "ADDENDUM: band(d == eps_r) = AMBIGUOUS (matches the <= of the certificate "
                                          "build); a site found only in the eps_r build is stated "
                                          "(SITE_ONLY_IN_AUTHORED_BUILD)"},
            {"id": "R88-D14", "decision": "ADDENDUM: GEOS output never acquires identity; the cross-check proves "
                                          "boundary provenance by containment in ALL source items (no nearest rule)"}],
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
                                          "three unresolved dynamic blocks exist in the new file, none in the region"},
            {"id": "F-R88-18", "finding": "walls drawn INSIDE a block occurrence (a plan inserted or xref-bound as a "
                                          "block) are not admitted by GR-05 (model space only): such a plan fails "
                                          "closed (UNKNOWN), it is never measured; an assembly-context rule is needed "
                                          "before TS01 can read block-hosted plans (synthetic test, not a Qortuba case)"},
            {"id": "F-R88-19", "finding": "exact GEOS (no node equivalence) on old Qortuba gives 61 faces with a 280 m2 "
                                          "merged face vs 75 TS01 sites: end points 1e-12..1e-9 apart are distinct "
                                          "nodes to GEOS; any GEOS use needs a node equivalence"},
            {"id": "F-R88-20", "finding": "a precision GRID (set_precision; wall_solid's 0.05 mm) has a cliff at every "
                                          "grid line, independent of the grid size: two points 1 ULP apart can be "
                                          "split; the cross-check runs four grid phases for this reason"},
            {"id": "F-R88-21", "finding": "route noise on old Qortuba reaches 1e-9 units (~70 ULP): a 1-ULP or 16-ULP "
                                          "equivalence is not noise-safe (1 ULP: K1 58 vs K2 59 sites; 16 ULP: 68 of "
                                          "75); the measured gap is empty from 1e-9 to 1 unit"},
            {"id": "F-R88-22", "finding": "the certificate had no flag for a site that exists ONLY at eps_r (a room "
                                          "whose only gap, inside the band, opens outside): now "
                                          "SITE_ONLY_IN_AUTHORED_BUILD; its labels are outside every site, so it was "
                                          "never measured, but it was not stated"},
            {"id": "F-R88-23", "finding": "band() returned AUTHORED at d == eps_r while the certificate build merges "
                                          "d <= eps_r: fixed (no number changed)"},
            {"id": "F-R88-24", "finding": "requirements.txt says the project does not own a geometry kernel; TS01 owns "
                                          "its noding (needed for exact arcs and source identity); mitigated by the "
                                          "independent GEOS cross-check, which agrees on every site of all three runs"},
            {"id": "F-R88-25", "finding": "a stub partition inside a room is in the TS01 site's boundary ids but not in "
                                          "a GEOS face ring (polygonize drops dangles): any per-room wall-length or "
                                          "finish measurement must treat stubs (two faces, both inside the room) "
                                          "explicitly"},
            {"id": "F-R88-26", "finding": "the core between two faces of a double-line wall is an UNLABELLED_SITE "
                                          "(an obstacle interior, not free space); classify by role evidence in R8.9, "
                                          "never by a thickness threshold"},
            {"id": "F-R88-27", "finding": "wall_solid / free_space recover lineage after the union by touching length "
                                          "(> 1 mm): a proximity rule that cannot prove which source bounds which room"},
            {"id": "F-R88-28", "finding": "the legacy paths mix material, semantic and topological thresholds (wall "
                                          "thickness, room size, shaft area, 600 mm, 2 mm snap) in one pass; TS01 has "
                                          "none of them and a test keeps them out of engine/source"}],
        "post_freeze_changes": {"tolerance_numbers": "unchanged", "fixes": ["F-R88-08", "F-R88-09", "F-R88-10"],
                                "freeze_commit": "9f77e4d",
                                "addendum": ["topology_crosscheck (new; can only withhold a site)",
                                             "band edge (F-R88-23)", "SITE_ONLY_IN_AUTHORED_BUILD (F-R88-22)",
                                             "separation measurement / NOISE_NEAR_EPS_N (measurement only)"],
                                "addendum_effect_on_rows": "none: all six rows identical before and after; the policy "
                                                          "digest is unchanged"},
        "gates": {"MIGRATION_PLANNING_READY": "YES", "MIGRATION_EXECUTION_READY": "NO", "PRODUCTION_MIGRATION": "NO",
                  "TS01_ROOM_TOPOLOGY": "IMPLEMENTED_SHADOW", "QS01": "LEGACY_RESEARCH_ONLY",
                  "OLD_QORTUBA_ROUTE_STABLE_TOPOLOGY": "YES" if xr["comparison"]["same_topology"] else "NO",
                  "NEW_DWG_SOURCE_IDENTITY": "NOT_ESTABLISHED", "OWNER_ACTION_REQUIRED_NOW": "NONE",
                  "TOPOLOGY_CROSSCHECK": " / ".join(f"{k} {v['counts']['AGREES']} of {sum(v['counts'].values())} AGREE"
                                                    for k, v in load(regdir, "TOPOLOGY_CROSSCHECK")["runs"].items()),
                  "ARCHITECTURE": "TS01_VECTOR_AUTHORITY + GEOS_CROSSCHECK + RASTER_QA_ONLY"},
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


def architecture_review(regdir):
    """R8.8 addendum: the architecture review, recommendation first. Evidence is read from the lab registers."""
    xc = load(regdir, "TOPOLOGY_CROSSCHECK")["runs"]
    ta = load(regdir, "TOLERANCE_ARCHITECTURE")
    h = ta["h584_numeric_study"]
    sens = {r["eps"]: [r["K1"]["sites"], r["K2"]["sites"], r["routes_agree"]] for r in h["eps_sensitivity"]}
    cx = {k: v["counts"] for k, v in xc.items()}
    return {
        "SCHEMA": "URBAN_R8_8_ARCHITECTURE_REVIEW_V1",
        "recommendation": "VECTOR AUTHORITY + INDEPENDENT VECTOR CROSS-CHECK + RASTER QA ONLY (a hybrid, option D, "
                          "with TS01 as the single authority). Do NOT build the room topology on wall_solid / "
                          "free_space. Reuse their principles, not their code path.",
        "questions": {
            "1_wall_solid_free_space_as_foundation": {
                "answer": "NO",
                "why": ["axis-aligned only: WallPolygon rings are built from H/V face pairs; skew and curved walls do "
                        "not exist for it",
                        "it needs MATERIAL pairing (two faces, thickness >= 40 mm, length >= 50 mm): a single-line "
                        "partition, a glazing line or a column outline is not an obstacle, so room topology would "
                        "inherit material semantics (TOPOLOGY_OBSTACLE != MATERIAL_WALL is violated)",
                        "NODE_SNAP_GRID_MM = 0.05 is a grid snap chosen from one project's outcome (AR-00: 49 -> 46 "
                        "components); a grid has a cliff at every grid line, so two points 1 ULP apart can be split "
                        "by any grid size (demonstrated: tests/r8_8/test_r8_8_architecture.py grid-phase test)",
                        "the envelope is derived from the wall solid itself: inside / outside is assumed, not "
                        "evidenced",
                        "lineage is recovered after the union by geometric touching (intersects, exterior "
                        "intersection length > 1 mm): a proximity rule, not a proof; boundary source identity per "
                        "room is lost",
                        "space roles come from size thresholds (700 mm, 1.2 m2, 3.0 m2, aspect 6)",
                        "portal barriers need a host wall band: an opening in a single-line wall cannot close"]},
            "2_safer_than_raster": {
                "answer": "the vector route is safer than raster, YES; wall_solid / free_space is NOT safer than TS01",
                "why": "a 50 mm cell cannot resolve a <= 1 mm decision, 4-connectivity depends on the cell phase, "
                       "arcs are sampled every 50 mm and areas are quantised; wall_solid removes those but adds its "
                       "own grid cliff and material coupling"},
            "3_reusable": ["FREE = ENVELOPE - OBSTACLES as a DOWNSTREAM trade operation (clear internal area against "
                           "double-line wall solids), after topology, not as topology",
                           "assert_non_overlapping as an invariant (TS01 faces partition the plane by construction; "
                           "kept as a test)",
                           "MAX_DEFENSIBLE_SNAP_MM = 1.0: the same principle as eps_r (authored precision)",
                           "snap_tolerance.py's measured noise-vs-gap separation: adopted as "
                           "topology_policy.separation (measured per drawing, never a chosen number)",
                           "GEOS as the declared kernel: used as the independent cross-check"],
            "4_project_or_material_specific": [r["where"] + ": " + r["name"] for r in ta["legacy_inventory"]
                                               if r["class"].startswith(("MATERIAL", "SEMANTIC", "PROJECT",
                                                                         "TOPOLOGY_NODE_EQUIVALENCE (implemented",
                                                                         "TOPOLOGY_NODE_EQUIVALENCE +", "RASTER"))],
            "5_choice": "D (hybrid) in this form: TS01 = authority (own exact noding, arcs, source identity, "
                        "two-build certificate); GEOS node + polygonize = independent cross-check that can only "
                        "withhold a site; raster = QA / localisation only. Not A (material-coupled, axis-only, grid "
                        "cliff), not C (resolution), not plain B (TS01 already is the principled module; GEOS cannot "
                        "be the authority because it has no exact arc, keeps no source identity through noding and "
                        "offers node equivalence only as a grid)",
            "6_why_this_architecture": [
                "authority needs exact arcs: GEOS would need flattening (forbidden)",
                "authority needs source identity through noding: GEOS output would need a nearest-geometry identity "
                "(forbidden without a proof rule)",
                "authority needs node equivalence by DISTANCE with a certificate: GEOS offers only a precision grid, "
                "whose cliffs are not aligned with the noise / authored bands",
                "an independent kernel still catches TS01 defects: three were found in R8.8 by real data "
                "(F-R88-08..10); the cross-check now reproduces every straight-edged site with area AND boundary "
                f"provenance: {cx}"],
            "7_problems_not_identified_by_the_prompt": "see findings F-R88-19 .. F-R88-28 in R8_8_DECISION_REGISTER"},
        "sections": {
            "reuse_or_not": "NOT as the spine; principles reused (Q3)",
            "raster": "QA / localisation / independent cross-check only; never an authority for topology or area",
            "vector_area_vs_arrangement": "area is computed from the certified site cycle itself (exact chord polygon + "
                                          "circular segments, holes subtracted); there is no rectangle "
                                          "decomposition in TS01; any decomposition is presentation only",
            "tolerance_architecture": {"classes": ta["classes"], "rule": "one class, one tolerance, one stated basis; "
                                       "no universal snap; no grid snap as an authority"},
            "H584": {"route_difference": f"{h['H584_route_difference_units']:.3e} units = "
                                         f"{h['H584_route_difference_ulps']:.0f} ULP at |coord| {h['coordinate_magnitude_M']:.0f}",
                     "measured_end_point_distances_by_decade": h["endpoint_pair_distance_decades_K1_admitted"],
                     "sensitivity_sites_K1_K2_agree": sens,
                     "geos_exact": h["geos_exact_no_node_equivalence_K1"],
                     "decision": "keep V1 (eps_n = 2**-30 x max|coord| = {:.1e} units = {:.1e} ULP). Observed route "
                                 "noise reaches 1e-9 units (~70 ULP): 16 ULP still loses 7 sites, 1 ULP splits the "
                                 "routes. A ULP-count policy would need calibration on observed noise; V1 sits about "
                                 "five decades above the noise and three below eps_r. No V2 is introduced; instead the "
                                 "separation is MEASURED per drawing (topology_policy.separation): ".format(
                                     h["v1_eps_n"], h["v1_eps_n_in_ulps"]) + json.dumps(ta["separation_per_run"]),
                     "authored_gaps_mm": ta["authored_gap_behaviour_mm"]},
            "role_admission": "positive admission before topology (geometry_role, GR-01..GR-16, GR-99); only "
                              "TOPOLOGY_BOUNDARY / STRUCTURAL_OBSTACLE / GLAZING_BOUNDARY / OPENING_BOUNDARY bound a "
                              "site; UNKNOWN_* and BOUNDARY_CURVE_UNSUPPORTED block the sites they touch; MATERIAL "
                              "identity is not consulted",
            "flow": ["CANONICAL_MEASUREMENT_INPUT: canonical_input.validate (TS01 contract)",
                     "GEOMETRY_ROLE_ADMISSION: geometry_role.admit",
                     "TOPOLOGY_OBSTACLE_SET: admitted boundary roles + closures from proven openings",
                     "VECTOR_FREE_SPACE: bounded faces of the exact arrangement of the obstacle set",
                     "SPACE_GEOMETRY_CANDIDATES: sites + two-build certificate + GEOS cross-check",
                     "SEMANTIC_LABEL_ASSIGNMENT: label occurrences; two or more -> MULTIPLE_SEMANTIC_LABELS",
                     "unknown geometry at any step -> REVIEW / BLOCK"],
            "curves": "SEGMENT / ARC / CIRCLE exact in TS01; ELLIPTICAL_ARC on a boundary role -> "
                      "BOUNDARY_CURVE_UNSUPPORTED (blocks); splines etc. are unrealised -> accounted; the cross-check "
                      "marks arc-bounded sites NOT_APPLICABLE_CURVE (never flattened); nothing pre-empts R11",
            "provenance_after_geos": "GEOS output is compared and discarded; it never acquires a source identity. "
                                     "Proof rule used by the cross-check: every boundary piece of the GEOS face must "
                                     "be contained (both ends within 2 x eps_n) in at least one straight admitted "
                                     "source item; its identities = ALL items containing it (never the nearest); the "
                                     "union must equal the TS01 site's boundary + hole ids (less two-sided stubs)",
            "legacy_project_logic": "STAIR / lift by layer count, 600 mm, 3 m2, BATH / PAINTRY, SNAP_MM 2, H/V-only "
                                    "arrangement: QS01 and r3 (lab, legacy) only. engine/source holds generic tokens "
                                    "(exact-token lexicon) and no size threshold; enforced by "
                                    "test_no_legacy_project_rule_reaches_the_generic_topology",
            "anything_else": "an obstacle INTERIOR (the core between two faces of a double-line wall) is today an "
                             "UNLABELLED_SITE: R8.9 should classify it by role evidence (both sides bounded by the "
                             "same wall's faces), not by a thickness threshold (F-R88-26)"}}


def main(regdir):
    regdir = Path(regdir)
    regs = {"OWNER_ACTION_REGISTER": owner_actions(), "ENGINEERING_ACTION_REGISTER": engineering_actions(regdir),
            "SOURCE_SUBPART_IDENTITY_SCHEMA": subpart_schema(), "R8_8_DECISION_REGISTER": decision_register(regdir),
            "ARCHITECTURE_REVIEW": architecture_review(regdir)}
    for k, v in regs.items():
        (regdir / f"{k}.json").write_text(json.dumps(v, indent=1, default=str) + "\n")
    print(sorted(regs), CI.COMPLETE, GR.POLICY_ID, RM.POLICY["id"])


if __name__ == "__main__":
    main(sys.argv[1])
