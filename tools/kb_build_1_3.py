"""KNOWLEDGE REGISTRY 1.3.0 BUILDER (M9 Phase 2B-8) - knowledge/URBAN_ENGINEERING_KNOWLEDGE_1.3.0.json is the frozen
1.2.0 registry (read byte for byte, never rebuilt) plus the delta of the Phase 2B-8 acceptance-hardening program
(2026-10-17), read only by ARCH_TAKEOFF_V2.7.1:

    new rules        UP-REVIEW-001 a space under classification review is measured under each plausible
                     classification; a quantity is released only when it is identical under every one AND its system
                     does not depend on the classification; the rest are conditional scenario quantities, never added
                     together
                     UP-QTY-STATUS-001 every BOQ line is reported once: CONFIRMED, HELD (with its reason class) or
                     EXCLUDED (with its reason); scenario quantities are CONDITIONAL and never in a confirmed total
                     UP-COL-ORIENT-001 a column turned off the drawing axes is a jamb and a wall interruption like an
                     axis-aligned one (a plan measures the same at every angle)
    amended          UP-WET-002 (1.3.0): the water-closet linework profile - a cistern on a wall face, a bowl no wider
                     than a WC pan, a round bowl centred on its cistern - and a basin block's own linework identified
                     by the insert path of every entity drawn inside it
                     UP-DOOR-OPEN-003 (1.3.0): the door-standard reconciliation record - the as-drawn wall opening and
                     the measured jamb span apart, the drawn leaf-to-opening difference reported as CAD geometry (never
                     an allowance), whether the proposal fits inside the drawn gap and the consultant / structural
                     review it needs
    1.2.0 is unchanged and stays the registry of ARCH_TAKEOFF_V2.7.

    python3 -I tools/kb_build_1_3.py            write the 1.3.0 registry
    python3 -I tools/kb_build_1_3.py --check    exit 1 when the committed 1.3.0 registry differs from a fresh build

Stdlib only."""
import copy
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "knowledge" / "URBAN_ENGINEERING_KNOWLEDGE_1.2.0.json"
OUT = ROOT / "knowledge" / "URBAN_ENGINEERING_KNOWLEDGE_1.3.0.json"
D = "2026-10-17"
P = "owner program 2026-10-17 (URBAN PROJECT AI - V2.7 acceptance hardening and second-villa readiness)"
T = "tests/m9_p2b8/"
H = [{"version": "1.3.0", "date": D, "change": "first registry record (Phase 2B-8)"}]


def rec(rule_id, title, *, purpose, scope, elements, locations=("ALL",), preconditions=(), exceptions=(),
        authority, status, logic, evidence=(), assumptions="NONE", conflicts=(), trades=(), tests=(), code=(),
        examples=(), limitations=(), supersedes=(), superseded_by=None, kind="ENGINEERING_RULE"):
    return {"rule_id": rule_id, "title": title, "kind": kind, "purpose": purpose, "scope": scope,
            "elements": list(elements), "locations": list(locations), "preconditions": list(preconditions),
            "exceptions": list(exceptions), "authority": authority, "status": status, "effective_version": "1.3.0",
            "logic": logic, "required_evidence": list(evidence), "assumptions_permitted": assumptions,
            "conflicts": list(conflicts), "dependent_trades": list(trades), "tests": list(tests), "code": list(code),
            "examples": list(examples), "limitations": list(limitations), "history": H,
            "supersedes": list(supersedes), "superseded_by": superseded_by}


NEW = [
    rec("UP-REVIEW-001", "Review spaces: release only what every plausible classification measures the same way",
        purpose="a space whose type is under review is not left without quantities: its geometry is reported, the "
                "quantities identical under every plausible classification are released, the others are kept as "
                "conditional scenario quantities",
        scope="spaces under classification review (UP-WET-002) in ARCH_TAKEOFF_V2.7.1",
        elements=("ROOM",), locations=("ALL",),
        authority={"kind": "OWNER", "received": D, "source": f"{P} section 1"},
        status="OWNER_APPROVED",
        logic={"plausible": {
                   "WET_CLASSIFICATION_REVIEW": ["WET_SCOPE (UP-WET-001, as a W.C.)", "DRY_SCOPE (a lobby / wash area)"],
                   "WC_CANDIDATE_REVIEW": ["WET_SCOPE (UP-WET-001, as a W.C.)", "DRY_SCOPE (a lobby / wash area)"],
                   "UNLABELLED_SPACE": "NOT_ESTABLISHED (no fixture says what the space is: nothing is released)"},
               "plausible_requires": ["a sanitary fixture or a water-closet shape drawn inside",
                                      "no stair flight and no void outline inside",
                                      "not possibly exterior (space model)"],
               "release_when": ["the same item, element and unit in every plausible classification",
                                "the same quantity (or range), evidence state and rule",
                                "a system that does not depend on the classification"],
               "system_dependent": {"FIN.PLASTER": "the substrate behind wall porcelain is its own line "
                                                   "(UP-FIN-PAINT-001): plaster is released only when the wall finish "
                                                   "over it is the same in every classification"},
               "never": ["two scenarios added together", "a scenario quantity in the main BOQ",
                         "a quantity released whose rule or system differs between classifications",
                         "a classification chosen to release a quantity"]},
        trades=("CEILING", "PLASTER", "FLOOR_FINISH", "WALL_FINISH", "PAINT", "WATERPROOFING", "MARBLE"),
        tests=(T + "test_p2b8_review_release.py::test_basin_space_releases_its_ceiling_and_nothing_else",
               T + "test_p2b8_review_release.py::test_equal_quantities_are_not_released_when_the_system_or_rule_differs"),
        code=("tools/urban_boq_m9.py::_arch_v271", "tools/urban_boq_m9.py::_review_release"),
        conflicts=({"with": "UP-WET-002", "resolution": "no conflict: UP-WET-002 keeps the space REVIEW (no type); "
                    "UP-REVIEW-001 says which of its quantities are known without the type"},)),
    rec("UP-QTY-STATUS-001", "Every BOQ line reported once: confirmed, conditional, held or excluded",
        purpose="the BOQ shows what is confirmed, what depends on an open classification or decision, what is held "
                "for missing evidence and what is excluded, without double counting",
        scope="the BOQ release report of ARCH_TAKEOFF_V2.7.1 (BOQ_RELEASE_REPORT.json / .csv)",
        elements=("BOQ_LINE",),
        authority={"kind": "OWNER", "received": D, "source": f"{P} section 1"},
        status="OWNER_APPROVED",
        logic={"CONFIRMED": "a line with a quantity (MEASURED, SOURCE_DERIVED or PROVISIONAL)",
               "CONDITIONAL": "scenario quantities (review classifications, owner door minimum): never in a "
                              "confirmed total, scenarios of one set never added together",
               "HELD": {"BOUNDED_EXPOSURE": "a range, its bounds kept", "BLOCKED_RFI": "no quantity, its question",
                        "reason_class": {"B_MISSING_DRAWING_EVIDENCE": "REQUIRES_DRAWING_EVIDENCE",
                                         "C_RULE_CONFLICT": "REQUIRES_OWNER_DECISION",
                                         "D_MISSING_OWNER_POLICY": "REQUIRES_OWNER_DECISION",
                                         "E_ENGINEERING_DEFECT": "ENGINEERING_REVIEW",
                                         "A_ESTABLISHED": "ENGINEERING_REVIEW (an established item still held is a "
                                                          "defect of the run)",
                                         "unclassified": "ENGINEERING_REVIEW (the hold is in no catalogue group: "
                                                         "an engineering item to classify)"},
                        "CANNOT_BE_ESTABLISHED": "a hold whose value no design document can give before "
                                                 "construction or product selection (catalogue groups listed in "
                                                 "cannot_be_established_groups; none in this registry)",
                        "cannot_be_established_groups": []},
               "EXCLUDED": "NOT_APPLICABLE_WITH_EVIDENCE / EXCLUDED_WITH_REASON, with the reason",
               "never": ["a line in two categories", "a conditional quantity in a confirmed total",
                         "an unsupported quantity reported as zero"]},
        tests=(T + "test_p2b8_review_release.py::test_every_line_is_reported_exactly_once",
               T + "test_p2b8_review_release.py::test_scenarios_are_never_added_to_the_main_boq"),
        code=("tools/urban_boq_m9.py::_release_report",)),
    rec("UP-COL-ORIENT-001", "A column turned off the drawing axes is a jamb and a wall interruption",
        purpose="a plan measures the same at every angle: a column standing at a wall gap bounds the opening, and a "
                "column standing in a wall line is concrete, not wall, whatever its orientation",
        scope="COLUMN-role rectangles of any orientation (ARCH_TAKEOFF_V2.7.1)",
        elements=("COLUMN", "WALL", "OPENING"),
        authority={"kind": "OWNER", "received": D, "source": f"{P} section 3 (turned columns used as door jambs or "
                                                              "wall interruptions)"},
        status="OWNER_APPROVED",
        logic={"jamb": "the turned column's polygon is an obstacle of the band-opening search (COLUMN_JAMB)",
               "wall": "the stretch of a wall band the turned polygon occupies across more than half the band "
                       "thickness is cut from the wall run",
               "invariance": "rot30 / rot90 / mirror / metres of a plan give the unturned plan's totals"},
        trades=("MASONRY", "PLASTER", "PAINT", "WALL_FINISH", "OPENINGS"),
        tests=(T + "test_p2b8_recognition.py::test_turned_column_is_a_jamb",
               T + "test_p2b8_recognition.py::test_turned_column_interrupts_the_wall"),
        code=("engine/source/arch_rooms.py::spaces", "engine/source/arch_walls.py::walls")),
]

WET_AMEND = {
    "wc_profile_1_3_0": {"cistern_on_wall_face_m": 0.10, "bowl_width_m": [0.32, 0.42],
                         "round_bowl": {"diameter_m": [0.32, 0.42], "centred_on_cistern_m": 0.05},
                         "why": "a WC pan's cistern stands against a wall (the flush and soil connection) and the "
                                "pan is narrower than a seat; a weak resemblance stays REVIEW",
                         "limitation": "a seat at a pan's size touching a back on a wall face is a WC outline: "
                                       "geometry alone cannot tell them apart (L-P8-01)"},
    "basin_linework_1_3_0": "a basin block's own linework (every entity whose insert path contains the basin's "
                            "insert) is the basin, never a second piece of evidence"}
DOOR_AMEND = {
    "reconciliation_1_3_0": {
        "fields": ["AS_DRAWN_WALL_OPENING (the band gap jamb to jamb)",
                   "MEASURED_JAMB_SPAN (the door symbol's own jamb lines)", "DOOR_LEAF (if established)",
                   "FINISHED_CLEAR_WIDTH (if established; not in a plan)", "OWNER_MINIMUM",
                   "FRAME_ALLOWANCE (only from an accepted source)", "PROPOSED_ENLARGEMENT",
                   "CONSULTANT_REVIEW", "STRUCTURAL_REVIEW"],
        "drawn_symbol_difference": "the structural opening minus the drawn leaf is CAD symbol geometry, reported, "
                                   "never an allowance",
        "review": {"consultant": "every proposed enlargement (UP-DOOR-DEP-001)",
                   "structural": "an enlargement that cuts drawn wall (beyond the drawn opening, or into a wall "
                                 "remainder inside the gap) or lengthens the lintel span"},
        "never": ["the CAD geometry changed to satisfy the minimum", "an enlargement applied to a quantity",
                  "the registry 1.1.0 allowance imposed"]}}


def build():
    base_bytes = BASE.read_bytes()
    reg = copy.deepcopy(json.loads(base_bytes.decode("utf-8")))
    rules = {r["rule_id"]: r for r in reg["rules"]}
    for rid, extra, change, tests in (
            ("UP-WET-002", WET_AMEND, "the water-closet linework profile and the basin's own linework (Phase 2B-8)",
             [T + "test_p2b8_recognition.py::test_wc_evidence_to_truth",
              T + "test_p2b8_recognition.py::test_basin_block_linework_is_the_basin"]),
            ("UP-DOOR-OPEN-003", DOOR_AMEND, "the door-standard reconciliation record (Phase 2B-8 section 2)",
             [T + "test_p2b8_doors.py::test_bathroom_door_every_value_kept_apart",
              T + "test_p2b8_doors.py::test_bathroom_door_proposed_enlargement_and_review"])):
        r = rules[rid]
        r.update(logic=dict(r["logic"], **extra), effective_version="1.3.0", tests=r["tests"] + tests,
                 history=r["history"] + [{"version": "1.3.0", "date": D, "change": change}])
    for r in NEW:
        assert r["rule_id"] not in rules, r["rule_id"]
        rules[r["rule_id"]] = r
    reg.update(version="1.3.0", effective=D,
               base={"version": "1.2.0", "sha256": hashlib.sha256(base_bytes).hexdigest()},
               consumed_by=["ARCH_TAKEOFF_V2.7.1 (engine/source/knowledge.py, using('1.3.0'))"],
               not_consumed_by="ARCH_TAKEOFF_V1 / V2 / V2.1 / V2.2 (frozen; rules/ 1.5.0); ARCH_TAKEOFF_V2.3 reads "
                               "registry 1.0.0; ARCH_TAKEOFF_V2.4 .. V2.6 read registry 1.1.0; ARCH_TAKEOFF_V2.7 "
                               "reads registry 1.2.0 (frozen)",
               rules=sorted(rules.values(), key=lambda r: r["rule_id"]),
               delta={"builder": "tools/kb_build_1_3.py", "new": sorted(r["rule_id"] for r in NEW),
                      "amended": ["UP-DOOR-OPEN-003", "UP-WET-002"]})
    ids = [r["rule_id"] for r in reg["rules"]]
    assert len(ids) == len(set(ids)), "duplicate rule id"
    return reg


TEXT = json.dumps(build(), indent=1, sort_keys=True, ensure_ascii=False) + "\n"
if __name__ == "__main__":
    if "--check" in sys.argv[1:]:
        same = OUT.is_file() and OUT.read_text(encoding="utf-8") == TEXT
        print("registry 1.3.0 up to date" if same else "registry 1.3.0 differs from a fresh build: run "
                                                        "tools/kb_build_1_3.py")
        sys.exit(0 if same else 1)
    OUT.write_text(TEXT, encoding="utf-8")
    reg = json.loads(TEXT)
    print(len(reg["rules"]), "rules", len(reg["question_catalogue"]), "question patterns", OUT.stat().st_size, "bytes")
