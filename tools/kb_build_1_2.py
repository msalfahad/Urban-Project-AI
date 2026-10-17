"""KNOWLEDGE REGISTRY 1.2.0 BUILDER (M9 Phase 2B-7) - knowledge/URBAN_ENGINEERING_KNOWLEDGE_1.2.0.json is the frozen
1.1.0 registry (read byte for byte, never rebuilt) plus the delta of the Phase 2B-7 authorization (2026-10-17), read
only by ARCH_TAKEOFF_V2.7:

    new rules        UP-DOOR-OPEN-003 the owner minimum door openings (1.00 / 0.90 m) kept apart from the CAD
                     structural opening, the door leaf, the clear passage, the frame allowance and the proposed
                     enlargement; which reading the minimum refers to is owner question OQ-05
                     UP-WET-002 a wash basin alone does not make a space wet; a water closet may be drawn as a block,
                     as linework or named by an Arabic / English room word; two independent pieces of evidence type an
                     unlabelled space, ambiguous spaces stay REVIEW (never DRY)
    requires confirmation  UP-DOOR-OPEN-002 (the 0.10 m wall-opening allowance and the reading of the minimums as
                     nominal doors): kept as history and as one reading, never imposed; 1.1.0 is unchanged and stays
                     the registry of ARCH_TAKEOFF_V2.4 .. V2.6
    questions        OQ-05 (door minimum reference); the V2.7 refusals and reviews (layer roles, columns, wet spaces)

    python3 -I tools/kb_build_1_2.py            write the 1.2.0 registry
    python3 -I tools/kb_build_1_2.py --check    exit 1 when the committed 1.2.0 registry differs from a fresh build

Stdlib only."""
import copy
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "knowledge" / "URBAN_ENGINEERING_KNOWLEDGE_1.1.0.json"
OUT = ROOT / "knowledge" / "URBAN_ENGINEERING_KNOWLEDGE_1.2.0.json"
D17 = "2026-10-17"
P = "owner program 2026-10-17 (URBAN PROJECT AI - Phase 2B-7 controlled implementation authorization)"
P6 = "owner program 2026-10-16 (URBAN PROJECT AI - overnight engineering intelligence and BOQ development) Part 4"
T = "tests/m9_p2b7/"
H = [{"version": "1.2.0", "date": D17, "change": "first registry record (Phase 2B-7)"}]


def rec(rule_id, title, *, purpose, scope, elements, locations=("ALL",), preconditions=(), exceptions=(),
        authority, status, logic, evidence=(), assumptions="NONE", conflicts=(), trades=(), tests=(), code=(),
        examples=(), limitations=(), supersedes=(), superseded_by=None, kind="OWNER_RULE"):
    return {"rule_id": rule_id, "title": title, "kind": kind, "purpose": purpose, "scope": scope,
            "elements": list(elements), "locations": list(locations), "preconditions": list(preconditions),
            "exceptions": list(exceptions), "authority": authority, "status": status, "effective_version": "1.2.0",
            "logic": logic, "required_evidence": list(evidence), "assumptions_permitted": assumptions,
            "conflicts": list(conflicts), "dependent_trades": list(trades), "tests": list(tests), "code": list(code),
            "examples": list(examples), "limitations": list(limitations), "history": H,
            "supersedes": list(supersedes), "superseded_by": superseded_by}


NEW = [
    rec("UP-DOOR-OPEN-003", "Owner minimum door openings, kept apart from every measured and derived door width",
        purpose="the owner's minimum openings (ordinary doors 1.00 m, bathroom doors 0.90 m) are checked without "
                "assuming what they measure: the CAD structural opening, the door leaf, the finished clear passage, "
                "the frame / installation allowance and the proposed enlargement are separate values",
        scope="ordinary internal PVC, bathroom PVC and ordinary external aluminium doors (ARCH_TAKEOFF_V2.7)",
        elements=("DOOR",), locations=("INTERIOR", "BATHROOM", "FACADE"),
        exceptions=("main entrance: drawing and specification (UP-DOOR-CLS-004)",
                    "elevator entrances: excluded (UP-DOOR-CLS-005)"),
        authority={"kind": "OWNER", "received": D17,
                   "source": f"{P} section 4; the minimums: {P6} (minimum openings: ordinary 1.00, bathroom 0.90)"},
        status="OWNER_APPROVED",
        logic={"owner_minimum_m": {"INTERNAL_PVC": 1.0, "BATHROOM_PVC": 0.9, "EXTERNAL_ALUMINIUM": 1.0},
               "applies_to": "UNRESOLVED (OQ-05): the structural opening, the door leaf or the clear passage",
               "readings": ["STRUCTURAL_OPENING", "DOOR_LEAF", "CLEAR_PASSAGE"],
               "kept_apart": ["CAD_STRUCTURAL_OPENING", "DOOR_LEAF (if established)",
                              "FINISHED_CLEAR_PASSAGE (if established)", "OWNER_REQUIRED_MINIMUM",
                              "FRAME_OR_INSTALLATION_ALLOWANCE (if independently supported)", "PROPOSED_ENLARGEMENT",
                              "CONFLICT_REVIEW_STATUS"],
               "allowance_sources": ["an approved door schedule or shop drawing", "a manufacturer installation detail",
                                     "a project rule (UP-RULES-001, scope DOOR_CATEGORY / OPENING)"],
               "question": "OQ-05",
               "never": ["the 0.10 m allowance of registry 1.1.0 imposed as an unconditional owner rule",
                         "a measured width overwritten", "an enlargement applied to a quantity"]},
        trades=("OPENINGS", "MASONRY", "PLASTER", "WALL_FINISH", "FLOOR_FINISH", "MARBLE", "WATERPROOFING"),
        tests=(T + "test_p2b7_doors.py::test_crossing_door_opening_record",),
        code=("engine/source/door_standards.py::opening_record_v27",),
        conflicts=({"with": "UP-DOOR-OPEN-002", "resolution": "1.2.0: UP-DOOR-OPEN-002 requires confirmation (its "
                    "reading of the minimums as nominal doors and its 0.10 m allowance are one reading, OQ-05)"},),
        supersedes=("UP-DOOR-OPEN-002",)),
    rec("UP-WET-002", "Wet-room evidence: a wash basin alone does not make a space wet",
        purpose="a space is typed a wet room from evidence that it is one, never from a wash basin alone; a water "
                "closet may be drawn as a block, as loose linework or named by an Arabic or English room word",
        scope="spaces without a room word (ARCH_TAKEOFF_V2.7)", elements=("ROOM",),
        locations=("BATHROOM", "LOBBY", "CORRIDOR"),
        authority={"kind": "OWNER", "received": D17,
                   "source": f"{P} section 5; {P6} (do not classify a lobby as wet merely because it contains a wash "
                             "basin; if classification is unresolved, keep a review status)"},
        status="OWNER_APPROVED",
        logic={"evidence_sources": ["a room word in the space (Arabic or English, arch_rooms.LEXICON)",
                                    "a room-tag block", "a WC / shower / bath fixture block",
                                    "a water closet drawn as linework (bowl + cistern, arch_v27.wc_shapes)",
                                    "sanitary-layer linework that is not the basin's own"],
               "basin_only": "REVIEW (no room type; no wet and no dry scope)",
               "basin_plus_independent": "BATHROOM (two independent pieces of evidence), flagged for review",
               "one_shape_alone": "REVIEW (WC_CANDIDATE_REVIEW): one geometric shape never types a space",
               "kept_from_v2_6": ["a WC / shower / bath block types the space (an explicit sanitary symbol)",
                                  "sanitary-layer linework (3+ segments) types the space"],
               "never": ["a basin-only space typed wet", "an ambiguous space typed dry"]},
        trades=("FLOOR_FINISH", "WALL_FINISH", "WATERPROOFING", "PAINT", "MARBLE"),
        tests=(T + "test_p2b7_wet.py::test_basin_alone_is_review", T + "test_p2b7_wet.py::test_basin_and_drawn_wc"),
        code=("engine/source/arch_v27.py::wet_evidence", "engine/source/arch_v27.py::wc_shapes"),
        conflicts=({"with": "UP-WET-001", "resolution": "no conflict: UP-WET-001 gives the scope of a wet room, "
                    "UP-WET-002 when an unlabelled space is one"},)),
]

OWNER_QUESTIONS = [
    {"id": "OQ-05", "group": "DOOR_MINIMUM_REFERENCE", "category": "C_RULE_CONFLICT", "continue_safely": True,
     "found": "the owner minimum openings (1.00 / 0.90 m) and the registry 1.1.0 reading (the minimums are nominal "
              "doors; the wall opening is nominal + 0.10 m) give different required openings for the same door",
     "alternatives": ["the minimum is the wall's structural opening (no allowance)",
                      "the minimum is the door (leaf); the wall opening = minimum + a frame / installation allowance "
                      "from a schedule, a detail or a project rule",
                      "the minimum is the finished clear passage"],
     "affects": ["DOOR_SCENARIOS opening_record", "proposed enlargements", "door feasibility"],
     "rules_checked": ["UP-DOOR-OPEN-003", "UP-DOOR-OPEN-002"],
     "recommendation": "keep every reading side by side; the structural reading is the lower bound; no enlargement "
                       "is applied",
     "why_unresolved": "the owner's minimum does not say which width it measures; the 0.10 m allowance is not "
                       "independently supported"},
]

QUESTIONS = [
    {"pattern": r"^DOOR_MINIMUM_REFERENCE", "category": "C_RULE_CONFLICT", "group": "DOOR_MINIMUM_REFERENCE",
     "rule": "UP-DOOR-OPEN-003", "question_id": "OQ-05",
     "example": ("DOOR_MINIMUM_REFERENCE (OQ-05): 4 door(s) - the owner minimum ...",
                 "DOOR.OPENING_RECORD (owner minimum)")},
    {"pattern": r"^LAYER_ROLE_REFUSED", "category": "B_MISSING_DRAWING_EVIDENCE", "group": "LAYER_ROLE_REFUSED",
     "rule": "UP-REF-COLUMN-001",
     "request": "the layer's role (a layer legend, or --layer-roles LAYER=ROLE): its geometry fits two roles",
     "example": ("LAYER_ROLE_REFUSED: layer A-OPEN: TWO_ROLES ...", "LAYER A-OPEN")},
    {"pattern": r"^COLUMN_ROLE_REFUSED", "category": "B_MISSING_DRAWING_EVIDENCE", "group": "COLUMN_ROLE_REFUSED",
     "rule": "UP-REF-COLUMN-001",
     "request": "the structural plan (column positions) or the layer's role (--layer-roles LAYER=COLUMN)",
     "example": ("COLUMN_ROLE_REFUSED: layer P-DRAIN: TOO_SMALL ...", "LAYER P-DRAIN")},
    {"pattern": r"^WET_CLASSIFICATION_REVIEW", "category": "B_MISSING_DRAWING_EVIDENCE",
     "group": "WET_CLASSIFICATION_REVIEW", "rule": "UP-WET-002",
     "request": "the space's room name, or its sanitary fixtures (a water closet, shower or bath)",
     "example": ("WET_CLASSIFICATION_REVIEW (UP-WET-002): no room word inside; it holds only wash basin(s) ...",
                 "ARCH.SPACE")},
    {"pattern": r"^WC_CANDIDATE_REVIEW", "category": "B_MISSING_DRAWING_EVIDENCE", "group": "WET_CLASSIFICATION_REVIEW",
     "rule": "UP-WET-002", "request": "the space's room name, or a second piece of sanitary evidence",
     "example": ("WC_CANDIDATE_REVIEW (UP-WET-002): no room word inside; a water-closet shape ...", "ARCH.SPACE")},
]


def build():
    base_bytes = BASE.read_bytes()
    reg = copy.deepcopy(json.loads(base_bytes.decode("utf-8")))
    rules = {r["rule_id"]: r for r in reg["rules"]}
    old = rules["UP-DOOR-OPEN-002"]
    lg = dict(old["logic"])
    lg["allowance_registry_1_1_0_m"] = lg["allowance_m"]
    lg["allowance_m"] = None
    lg["table"] = {k: {"required_nominal_door_m": v["required_nominal_door_m"], "required_wall_opening_m": None}
                   for k, v in lg["table"].items()}
    lg["requires_confirmation"] = ("the reading of the owner minimums as nominal doors and the 0.10 m wall-opening "
                                   "allowance (OQ-05): kept as one reading, never imposed (UP-DOOR-OPEN-003)")
    old.update(status="REQUIRES_CONFIRMATION", superseded_by="UP-DOOR-OPEN-003", logic=lg, effective_version="1.2.0",
               history=old["history"] + [{"version": "1.2.0", "date": D17, "change": "requires confirmation: the 0.10 m "
                                          "allowance is not imposed by ARCH_TAKEOFF_V2.7 (Phase 2B-7 section 4)"}])
    for r in NEW:
        assert r["rule_id"] not in rules, r["rule_id"]
        rules[r["rule_id"]] = r
    qs = []
    for q in QUESTIONS:
        q = dict(q)
        reason, item = q.pop("example")
        q["example"] = {"reason": reason, "item": item}
        qs.append(q)
    reg.update(version="1.2.0", effective=D17,
               base={"version": "1.1.0", "sha256": hashlib.sha256(base_bytes).hexdigest()},
               consumed_by=["ARCH_TAKEOFF_V2.7 (engine/source/knowledge.py, using('1.2.0'))"],
               not_consumed_by="ARCH_TAKEOFF_V1 / V2 / V2.1 / V2.2 (frozen; rules/ 1.5.0); ARCH_TAKEOFF_V2.3 reads "
                               "registry 1.0.0; ARCH_TAKEOFF_V2.4 .. V2.6 read registry 1.1.0 (frozen)",
               rules=sorted(rules.values(), key=lambda r: r["rule_id"]),
               owner_questions=reg["owner_questions"] + OWNER_QUESTIONS,
               question_catalogue=reg["question_catalogue"] + qs,
               delta={"builder": "tools/kb_build_1_2.py", "new": sorted(r["rule_id"] for r in NEW),
                      "requires_confirmation": ["UP-DOOR-OPEN-002"], "owner_questions": ["OQ-05"],
                      "questions": [q["pattern"] for q in qs]})
    ids = [r["rule_id"] for r in reg["rules"]]
    assert len(ids) == len(set(ids)), "duplicate rule id"
    return reg


TEXT = json.dumps(build(), indent=1, sort_keys=True, ensure_ascii=False) + "\n"
if __name__ == "__main__":
    if "--check" in sys.argv[1:]:
        same = OUT.is_file() and OUT.read_text(encoding="utf-8") == TEXT
        print("registry 1.2.0 up to date" if same else "registry 1.2.0 differs from a fresh build: run "
                                                        "tools/kb_build_1_2.py")
        sys.exit(0 if same else 1)
    OUT.write_text(TEXT, encoding="utf-8")
    reg = json.loads(TEXT)
    print(len(reg["rules"]), "rules", len(reg["question_catalogue"]), "question patterns", OUT.stat().st_size, "bytes")
