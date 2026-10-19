"""KNOWLEDGE REGISTRY 1.6.0 BUILDER (board task T-011) - knowledge/URBAN_ENGINEERING_KNOWLEDGE_1.6.0.json is the
frozen 1.5.0 registry (read byte for byte, never rebuilt) plus the owner's answer to the door-minimum question
(docs/agents/OWNER_QUESTIONS.md Q-04 / D-16, answered 2026-10-18; registry question OQ-05).

    amended          UP-DOOR-OPEN-002 (1.6.0): OWNER_APPROVED. The owner minimum is the NOMINAL door opening
                     (ordinary / internal PVC 1.00, bathroom PVC 0.90, external aluminium 1.00); the architectural wall
                     opening = nominal + 0.10 m (internal 1.10, bathroom 1.00 wall to wall, external 1.10); these are
                     minimums: a wider drawn opening keeps its drawn size; the main entrance is measured as drawn
                     (UP-DOOR-CLS-004). The 0.10 m is the owner's rule, never a second time.
                     UP-DOOR-OPEN-003 (1.6.0): which width the minimum measures is settled (the nominal door, OQ-05
                     answered); the allowance is the owner rule UP-DOOR-OPEN-002; every value is still kept apart and
                     an enlargement is still proposed, never applied to a quantity.
    owner questions  OQ-05 answered (the 1.5.0 record is kept; the answer is added beside it)
    1.5.0 is unchanged and stays the registry of ARCH_TAKEOFF_V2.9. No method version reads 1.6.0 yet: the reading
    is engine.source.door_standards.opening_record_kb16 (a new method piece; wiring it into a method is later work).

    python3 -I tools/kb_build_1_6.py            write the 1.6.0 registry
    python3 -I tools/kb_build_1_6.py --check    exit 1 when the committed 1.6.0 registry differs from a fresh build

Stdlib only."""
import copy
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "knowledge" / "URBAN_ENGINEERING_KNOWLEDGE_1.5.0.json"
OUT = ROOT / "knowledge" / "URBAN_ENGINEERING_KNOWLEDGE_1.6.0.json"
D = "2026-10-18"
SRC = ("owner answer 2026-10-18 to Q-04 / D-16 (docs/agents/OWNER_QUESTIONS.md): the minimum is the door opening; "
       "ordinary 1.00 m opening = 1.10 m wall to wall; bathroom 0.90 m opening = 1.00 m wall to wall; minimums: a plan "
       "drawn wider keeps its drawn size; the main door is measured as drawn")
AUTH = {"kind": "OWNER", "received": D, "source": SRC}
T = "tests/m9_kb/test_kb_door_standards.py::"
CODE = "engine/source/door_standards.py::opening_record_kb16"
NEW_TESTS = [T + "test_kb16_hand_table", T + "test_kb16_main_door_elevator_and_unsettled_class",
             T + "test_kb16_missing_width_is_never_zero", T + "test_kb16_on_the_door_floor"]

OPEN_002 = {
    "allowance_m": 0.10,
    "table": {"BATHROOM_PVC": {"required_nominal_door_m": 0.9, "required_wall_opening_m": 1.0},
              "EXTERNAL_ALUMINIUM": {"required_nominal_door_m": 1.0, "required_wall_opening_m": 1.1},
              "INTERNAL_PVC": {"required_nominal_door_m": 1.0, "required_wall_opening_m": 1.1}},
    "confirmed_1_6_0": {"answer": "Q-04 / OQ-05: the owner minimums are nominal door openings; the wall opening is "
                                  "nominal + 0.10 m; minimums only (the drawn size when wider); the main door as drawn",
                        "examples_from_the_answer": [
                            {"category": "INTERNAL_PVC", "nominal_door_m": 1.0, "wall_opening_m": 1.1},
                            {"category": "BATHROOM_PVC", "nominal_door_m": 0.9, "wall_opening_m": 1.0}],
                        "external_aluminium": "the 1.00 m nominal of this rule's table (registry 1.1.0 reading, which "
                                              "the answer confirms as a whole)",
                        "superseded_1_5_0": "requires_confirmation (the reading kept, never imposed)"},
}
OPEN_003 = {
    "applies_to": "the NOMINAL door opening (OQ-05 answered 2026-10-18); the wall opening = nominal + 0.10 m "
                  "(UP-DOOR-OPEN-002, OWNER_APPROVED 1.6.0)",
    "allowance_1_6_0": {"value_m": 0.10, "supported_by": "UP-DOOR-OPEN-002 (owner rule, Q-04 answer)"},
    "never": ["a measured width overwritten", "an enlargement applied to a quantity",
              "the 0.10 m allowance added a second time", "the ordinary minimum applied to the main entrance"],
    "superseded_1_5_0": {"applies_to": "UNRESOLVED (OQ-05): the structural opening, the door leaf or the clear passage",
                         "never_item": "the 0.10 m allowance of registry 1.1.0 imposed as an unconditional owner rule"},
}
OQ05_ANSWER = {"state": "ANSWERED", "answered": D, "answer_source": "docs/agents/OWNER_QUESTIONS.md Q-04 (D-16)",
               "answer": "the minimum is the door (nominal) opening; the wall opening = minimum + 0.10 m (ordinary "
                         "1.00 -> 1.10, bathroom 0.90 -> 1.00 wall to wall); the drawn size when wider; the main door "
                         "as drawn",
               "chosen_alternative": 1}


def build():
    base_bytes = BASE.read_bytes()
    reg = copy.deepcopy(json.loads(base_bytes.decode("utf-8")))
    rules = {r["rule_id"]: r for r in reg["rules"]}
    r2 = rules["UP-DOOR-OPEN-002"]
    lg2 = dict(r2["logic"], **OPEN_002)
    lg2.pop("requires_confirmation", None)
    r2.update(status="OWNER_APPROVED", authority=AUTH, effective_version="1.6.0", logic=lg2,
              assumptions_permitted="NONE (the 0.10 m allowance is the owner's rule, Q-04 answer)",
              code=r2["code"] + [CODE], tests=r2["tests"] + NEW_TESTS,
              conflicts=[c for c in r2["conflicts"] if c["with"] != "UP-DOOR-OPEN-003"] +
              [{"with": "UP-DOOR-OPEN-003", "resolution": "1.6.0: OQ-05 answered by the owner (Q-04): the minimum is "
                                                          "the nominal door; the 0.10 m allowance applies"}],
              history=r2["history"] + [{"version": "1.6.0", "date": D,
                                        "change": "OWNER_APPROVED: owner answer Q-04 / OQ-05 (T-011)"}])
    r3 = rules["UP-DOOR-OPEN-003"]
    r3.update(logic=dict(r3["logic"], **OPEN_003), effective_version="1.6.0", code=r3["code"] + [CODE],
              tests=r3["tests"] + NEW_TESTS,
              conflicts=[{"with": "UP-DOOR-OPEN-002", "resolution": "1.6.0: resolved by the owner (Q-04 / OQ-05): "
                                                                    "the minimum is the nominal door, wall opening = "
                                                                    "nominal + 0.10 m"}],
              history=r3["history"] + [{"version": "1.6.0", "date": D,
                                        "change": "OQ-05 answered: the minimum is the nominal door (T-011)"}])
    oq = []
    for x in reg["owner_questions"]:
        oq.append(dict(x, **OQ05_ANSWER) if x["id"] == "OQ-05" else x)
    assert sum(x.get("state") == "ANSWERED" for x in oq) == 1
    reg.update(version="1.6.0", effective=D,
               base={"version": "1.5.0", "sha256": hashlib.sha256(base_bytes).hexdigest()},
               consumed_by=["engine/source/door_standards.py::opening_record_kb16 (using('1.6.0')); no method version "
                            "reads 1.6.0 yet"],
               not_consumed_by="ARCH_TAKEOFF_V1 / V2 / V2.1 / V2.2 (frozen; rules/ 1.5.0); ARCH_TAKEOFF_V2.3 reads "
                               "registry 1.0.0; ARCH_TAKEOFF_V2.4 .. V2.6 read registry 1.1.0; ARCH_TAKEOFF_V2.7 "
                               "reads registry 1.2.0; ARCH_TAKEOFF_V2.7.1 reads registry 1.3.0; ARCH_TAKEOFF_V2.8 "
                               "reads registry 1.4.0; ARCH_TAKEOFF_V2.9 reads registry 1.5.0 (frozen)",
               rules=sorted(rules.values(), key=lambda r: r["rule_id"]), owner_questions=oq,
               delta={"builder": "tools/kb_build_1_6.py", "new": [], "amended": ["UP-DOOR-OPEN-002",
                                                                                 "UP-DOOR-OPEN-003"],
                      "owner_questions": [], "answered": ["OQ-05"],
                      "status_note": "UP-DOOR-OPEN-002 promoted to OWNER_APPROVED on the owner's own answer (Q-04); "
                                     "no other rule changed"})
    ids = [r["rule_id"] for r in reg["rules"]]
    assert len(ids) == len(set(ids)), "duplicate rule id"
    return reg


TEXT = json.dumps(build(), indent=1, sort_keys=True, ensure_ascii=False) + "\n"
if __name__ == "__main__":
    if "--check" in sys.argv[1:]:
        same = OUT.is_file() and OUT.read_text(encoding="utf-8") == TEXT
        print("registry 1.6.0 up to date" if same else "registry 1.6.0 differs from a fresh build: run "
                                                        "tools/kb_build_1_6.py")
        sys.exit(0 if same else 1)
    OUT.write_text(TEXT, encoding="utf-8")
    reg = json.loads(TEXT)
    print(len(reg["rules"]), "rules", len(reg["owner_questions"]), "owner questions", OUT.stat().st_size, "bytes")
