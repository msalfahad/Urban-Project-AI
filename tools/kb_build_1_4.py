"""KNOWLEDGE REGISTRY 1.4.0 BUILDER (M9 Phase 2B-9) - knowledge/URBAN_ENGINEERING_KNOWLEDGE_1.4.0.json is the frozen
1.3.0 registry (read byte for byte, never rebuilt) plus the delta of the Phase 2B-9 program (2026-10-17), read only by
ARCH_TAKEOFF_V2.8:

    new rules        UP-HGT-001 heights come from the drawing: element / room annotation > door-window schedule >
                     section / elevation > derived > floor note > project note > project rule > Urban default; each
                     height carries its source, value, unit and scope; floor-to-floor is never a wall height
                     UP-OPEN-SCHED-001 the opening schedule: width (plan) and schedule width checked, height, sill, head,
                     class; a wall finish deducts the opening's own band; floor-level glazing is not skirted; a window
                     without a height releases its width and holds its area
                     UP-REVEAL-001 window reveals from the measured depth to the glazing: jambs and head soffit plaster
                     (PROVISIONAL), the internal sill surface its own item, a floor-level window's strip floor
                     UP-WALL-GEOM-001 the wall geometry per face: centreline, faces, plan strip; short returns and curved
                     stubs under the 0.30 m band rule are wall
    amended          UP-SKIRT-001 (1.4.0): floor-level glazing is not skirted; a window whose sill is not established is
                     skirted under one reading only (a range)
                     UP-DOOR-HGT-001 (1.4.0): an annotation on the door ranks before the schedule (UP-HGT-001)
                     UP-REF-REVEAL-001 (1.4.0): applied by UP-REVEAL-001 in ARCH_TAKEOFF_V2.8
    1.3.0 is unchanged and stays the registry of ARCH_TAKEOFF_V2.7.1.

    python3 -I tools/kb_build_1_4.py            write the 1.4.0 registry
    python3 -I tools/kb_build_1_4.py --check    exit 1 when the committed 1.4.0 registry differs from a fresh build

Stdlib only."""
import copy
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "knowledge" / "URBAN_ENGINEERING_KNOWLEDGE_1.3.0.json"
OUT = ROOT / "knowledge" / "URBAN_ENGINEERING_KNOWLEDGE_1.4.0.json"
D = "2026-10-17"
P = ("owner program 2026-10-17 (URBAN PROJECT AI - Phase 2B-9: architectural BOQ completion, drawing-derived heights, "
     "wall geometry and independent quantity proof)")
T = "tests/m9_p2b9/"
C = "engine/source/arch_v28.py::"
H = [{"version": "1.4.0", "date": D, "change": "first registry record (Phase 2B-9)"}]


def rec(rule_id, title, *, purpose, scope, elements, locations=("ALL",), preconditions=(), exceptions=(),
        authority, status, logic, evidence=(), assumptions="NONE", conflicts=(), trades=(), tests=(), code=(),
        examples=(), limitations=(), supersedes=(), superseded_by=None, kind="ENGINEERING_RULE"):
    return {"rule_id": rule_id, "title": title, "kind": kind, "purpose": purpose, "scope": scope,
            "elements": list(elements), "locations": list(locations), "preconditions": list(preconditions),
            "exceptions": list(exceptions), "authority": authority, "status": status, "effective_version": "1.4.0",
            "logic": logic, "required_evidence": list(evidence), "assumptions_permitted": assumptions,
            "conflicts": list(conflicts), "dependent_trades": list(trades), "tests": list(tests), "code": list(code),
            "examples": list(examples), "limitations": list(limitations), "history": H,
            "supersedes": list(supersedes), "superseded_by": superseded_by}


NEW = [
    rec("UP-HGT-001", "Heights are read from the drawing, by an evidence hierarchy, each with its source and scope",
        purpose="every wall, ceiling, tile and opening height a quantity uses comes from the project's own drawings "
                "where they state it; an Urban default is the last fallback and always labelled",
        scope="every height-dependent quantity of ARCH_TAKEOFF_V2.8",
        elements=("WALL_FACE", "CEILING", "DOOR", "WINDOW"),
        authority={"kind": "OWNER", "received": D, "source": f"{P} section 3"},
        status="OWNER_APPROVED",
        logic={"order": ["ELEMENT_ANNOTATION (a text on the opening or inside the room)", "SCHEDULE (door / window "
                         "schedule row, bound by the mark next to the opening)", "SECTION / ELEVATION (level texts on "
                         "the floor's band)", "DERIVED (the plan-level interval minus every sourced component)",
                         "FLOOR_NOTE (a general note on the plan sheet)", "PROJECT_NOTE (a general note elsewhere)",
                         "PROJECT_RULE (the project facts / approved project rules)",
                         "URBAN_DEFAULT (UP-DOOR-HGT-001 door heights only, HEIGHT_ASSUMED)"],
               "scope_order": ["OPENING", "ROOM", "FLOOR", "PROJECT"],
               "trades": {"PLASTER": "to the structural soffit (U/S SLAB - F.F.L.)",
                          "PAINT": "to the finished ceiling (F.C.L. - F.F.L.; URBAN-PAINT-TO-FINISHED-CEILING)",
                          "WALL_TILE": "a printed tile height, else full height to the finished ceiling (UP-FIN-WALL-001)"},
               "conflict": "two candidates of the governing rank and scope that disagree by more than 5 mm: CONFLICT, "
                           "no value; a lower-ranked disagreeing candidate is kept as overridden",
               "units": "a stated unit converts; otherwise only a reading that is physically plausible and unique is "
                        "used (else UNIT_AMBIGUOUS)",
               "never": ["a floor-to-floor height as a wall height", "a real-project height invented",
                         "an Urban default presented as a drawing value"]},
        trades=("PLASTER", "PAINT", "WALL_FINISH", "OPENINGS"),
        tests=(T + "test_p2b9_heights.py::test_section_heights_govern_the_wall_finish",
               T + "test_p2b9_heights.py::test_the_evidence_hierarchy_order",
               T + "test_p2b9_heights.py::test_a_same_rank_conflict_holds_the_value",
               T + "test_p2b9_heights.py::test_the_missing_evidence_report"),
        code=(C + "read_schedules", C + "read_views", C + "bind_floor", C + "resolve")),
    rec("UP-OPEN-SCHED-001", "The opening schedule: width, height, sill, head and class, and their effect on finishes",
        purpose="a window in a plan without its height is not enough for its area; each opening's effect on plaster, "
                "paint, porcelain and skirting follows from its own band",
        scope="every door and window opening of ARCH_TAKEOFF_V2.8",
        elements=("DOOR", "WINDOW"),
        authority={"kind": "OWNER", "received": D, "source": f"{P} sections 4 (example 1) and 6"},
        status="OWNER_APPROVED",
        logic={"fields": ["plan width", "schedule width (checked within 0.03 m)", "height", "sill", "head = sill + "
                          "height", "class: DOOR / WINDOW / FLOOR_GLAZING"],
               "wall_finish_deduction": "the opening's own length on the boundary x (min(head, H) - max(sill, 0))",
               "skirting": "floor-level glazing (sill <= 0.02 m) is not skirted; a sill window is; an unknown sill is "
                           "a range",
               "unknown_height": "the width is released, the area held with the reason",
               "never": ["a window area from a schedule row whose width is not the window's"]},
        trades=("PLASTER", "PAINT", "WALL_FINISH", "FLOOR_FINISH", "OPENINGS"),
        tests=(T + "test_p2b9_openings.py::test_example1_wall_face_and_openings",
               T + "test_p2b9_openings.py::test_floor_glazing_is_not_skirted",
               T + "test_p2b9_openings.py::test_an_unknown_sill_makes_skirting_a_range",
               T + "test_p2b9_openings.py::test_a_window_without_a_height_holds_its_area"),
        code=(C + "band_height", C + "height_of", C + "skirting_adjustment")),
    rec("UP-REVEAL-001", "Window reveals from the measured depth to the glazing; the sill surface is its own item",
        purpose="reveals are real plaster surfaces, measured from the geometry, never inside the main wall face and "
                "never double counted",
        scope="window openings with an established height and sill in ARCH_TAKEOFF_V2.8",
        elements=("REVEAL", "WINDOW"),
        authority={"kind": "OWNER", "received": D, "source": f"{P} section 4 example 1; data/registry/"
                                                              "URBAN_OWNER_METHOD_RULES.json URBAN-REVEAL-FINISH-METHOD"},
        status="OWNER_APPROVED",
        logic={"depth": "the strip between the room's wall face and the glazing / its opening width (measured)",
               "jambs": "2 x depth x the window's height inside the plaster band",
               "head": "depth x width, only where wall remains above the head inside the plaster band",
               "sill": "a sill window: the strip is its internal sill surface, released as geometry, finish by the "
                       "window detail; floor-level glazing: the strip is floor (the room's floor finish)",
               "state": "PROVISIONAL (plaster by the owner method; a frame detail can change it)",
               "never": ["a fixed reveal depth", "a reveal inside the main wall face", "the door jamb plaster "
                         "counted again"]},
        trades=("PLASTER", "FLOOR_FINISH"),
        tests=(T + "test_p2b9_openings.py::test_example1_reveals_and_sill_surface",
               T + "test_p2b9_openings.py::test_floor_glazing_reveals_and_floor_strip"),
        code=(C + "window_strip_lines",)),
    rec("UP-WALL-GEOM-001", "Wall geometry per face; short returns and curved stubs are wall",
        purpose="masonry and finishing faces are measured on their own bases; a wall stretch is not dropped because "
                "it is short",
        scope="the wall bands of ARCH_TAKEOFF_V2.8",
        elements=("WALL",),
        authority={"kind": "OWNER", "received": D, "source": f"{P} sections 4 (examples 3, 4) and 5"},
        status="OWNER_APPROVED",
        logic={"measures": ["centreline (masonry run)", "each face (finishing)", "plan strip (centreline x t)"],
               "stubs": "a both-faces stretch of 0.05 - 0.30 m that no band holds: a straight return closed at one end "
                        "at least, of a thickness family the floor has, or a pair of concentric arcs: measured as wall, "
                        "its plan area moved out of the junction pieces",
               "curved": "inner face, centreline and outer face arcs kept apart; a finish uses its own face",
               "never": ["one wall-length convention for every trade", "a mean-radius length for a face finish"]},
        trades=("MASONRY", "PLASTER"),
        tests=(T + "test_p2b9_walls.py::test_a_short_return_is_measured_as_wall",
               T + "test_p2b9_walls.py::test_collinear_stubs_were_already_counted",
               T + "test_p2b9_walls.py::test_curved_wall_faces_kept_apart"),
        code=(C + "straight_stubs", C + "curved_stubs")),
]

SKIRT_AMEND = {"windows_1_4_0": {"floor_glazing": "not skirted (sill <= 0.02 m, UP-OPEN-SCHED-001)",
                                 "sill_window": "skirted under the sill",
                                 "sill_not_established": "not in the released skirting: a range line [0, its length]"}}
DOOR_HGT_AMEND = {"order_1_4_0": ["element annotation", "door schedule", "section", "elevation", "floor note",
                                  "project rule (facts)", "owner reference height (HEIGHT_ASSUMED)"]}
REVEAL_AMEND = {"applied_by_1_4_0": "UP-REVEAL-001 in ARCH_TAKEOFF_V2.8 (window reveals; door jamb plaster stays "
                                    "UP-FIN-PLASTER-001)"}


def build():
    base_bytes = BASE.read_bytes()
    reg = copy.deepcopy(json.loads(base_bytes.decode("utf-8")))
    rules = {r["rule_id"]: r for r in reg["rules"]}
    for rid, extra, change, tests in (
            ("UP-SKIRT-001", SKIRT_AMEND, "floor-level glazing and unknown sills (Phase 2B-9)",
             [T + "test_p2b9_openings.py::test_floor_glazing_is_not_skirted"]),
            ("UP-DOOR-HGT-001", DOOR_HGT_AMEND, "the element annotation ranks first (UP-HGT-001, Phase 2B-9)",
             [T + "test_p2b9_heights.py::test_the_evidence_hierarchy_order"]),
            ("UP-REF-REVEAL-001", REVEAL_AMEND, "applied by UP-REVEAL-001 in ARCH_TAKEOFF_V2.8 (Phase 2B-9)",
             [T + "test_p2b9_openings.py::test_example1_reveals_and_sill_surface"])):
        r = rules[rid]
        r.update(logic=dict(r["logic"], **extra), effective_version="1.4.0", tests=r["tests"] + tests,
                 history=r["history"] + [{"version": "1.4.0", "date": D, "change": change}])
        if rid == "UP-REF-REVEAL-001":
            r["limitations"] = ["applied in ARCH_TAKEOFF_V2.8 only (UP-REVEAL-001); no earlier route emits these "
                                "surfaces"]
    for r in NEW:
        assert r["rule_id"] not in rules, r["rule_id"]
        rules[r["rule_id"]] = r
    reg.update(version="1.4.0", effective=D,
               base={"version": "1.3.0", "sha256": hashlib.sha256(base_bytes).hexdigest()},
               consumed_by=["ARCH_TAKEOFF_V2.8 (engine/source/knowledge.py, using('1.4.0'))"],
               not_consumed_by="ARCH_TAKEOFF_V1 / V2 / V2.1 / V2.2 (frozen; rules/ 1.5.0); ARCH_TAKEOFF_V2.3 reads "
                               "registry 1.0.0; ARCH_TAKEOFF_V2.4 .. V2.6 read registry 1.1.0; ARCH_TAKEOFF_V2.7 "
                               "reads registry 1.2.0; ARCH_TAKEOFF_V2.7.1 reads registry 1.3.0 (frozen)",
               rules=sorted(rules.values(), key=lambda r: r["rule_id"]),
               delta={"builder": "tools/kb_build_1_4.py", "new": sorted(r["rule_id"] for r in NEW),
                      "amended": ["UP-DOOR-HGT-001", "UP-REF-REVEAL-001", "UP-SKIRT-001"]})
    ids = [r["rule_id"] for r in reg["rules"]]
    assert len(ids) == len(set(ids)), "duplicate rule id"
    return reg


TEXT = json.dumps(build(), indent=1, sort_keys=True, ensure_ascii=False) + "\n"
if __name__ == "__main__":
    if "--check" in sys.argv[1:]:
        same = OUT.is_file() and OUT.read_text(encoding="utf-8") == TEXT
        print("registry 1.4.0 up to date" if same else "registry 1.4.0 differs from a fresh build: run "
                                                        "tools/kb_build_1_4.py")
        sys.exit(0 if same else 1)
    OUT.write_text(TEXT, encoding="utf-8")
    reg = json.loads(TEXT)
    print(len(reg["rules"]), "rules", len(reg["question_catalogue"]), "question patterns", OUT.stat().st_size, "bytes")
