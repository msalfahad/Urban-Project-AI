"""KNOWLEDGE REGISTRY 1.7.0 BUILDER (board task T-079) - knowledge/URBAN_ENGINEERING_KNOWLEDGE_1.7.0.json is the
frozen 1.5.0 registry (read byte for byte, never rebuilt) plus the owner's answers on wet areas, roofs and the
membrane (docs/agents/OWNER_QUESTIONS.md, answered 2026-10-18 / 19), as read by ARCH_TAKEOFF_V2.11.

    amended   UP-WET-001     (1.7.0): kitchens are waterproofed like a bathroom (Q-30 A); basin-only hand-wash spaces
                             are wet (Q-06 a); the pantry with a floor drain is waterproofed within its printed size
                             (Q-37 A); the architectural label decides what a room is, the sanitary drawing
                             corroborates, uncertain fixtures never make wet quantities (Q-13 B)
              UP-WP-003      (1.7.0): the BOQ upturn line is walls only; one doorway transition line per door (a door
                             between two wet rooms once); the membrane to BUY follows the strip method, strips 0.20 m
                             longer at both ends whatever sits in the wall; every figure per wet area, totals only as
                             sums (Q-35 C); no extra shower tanking (Q-40 A)
              UP-WP-ROOF-001 (1.7.0): a roof is measured like a bathroom floor inside the parapet (Q-24 A (ii)); every
                             drafting gap is closed by the membrane and listed, no size limit given (Q-25); no dome is
                             concrete, each dome position is an open skylight with a 0.20 m upturn round it (Q-29); the
                             top roof that no plan draws stays held (Q-34, parked): a held line, never silent (T-093)
              UP-WP-LAY-001  (1.7.0): the owner's strip method (Q-30 worked example; Q-24 addendum): whole strips with
                             0.10 m laps and cut edges, never area / roll area; the purchase (Q-49 A, T-093): each
                             wet area and each roof alone, the layout (2 directions x 2 start walls) with the fewest
                             whole rolls, tie the shorter strip length; cutting plan and leftover metres per area;
                             the project total is the sum of the areas
    1.5.0 and 1.6.0 are unchanged. 1.7.0 is built on 1.5.0 (the registry of ARCH_TAKEOFF_V2.9 / V2.10), NOT on 1.6.0:
    the door-minimum answer of 1.6.0 is read by no method yet (T-055 wires it), so ARCH_TAKEOFF_V2.11 changes no door
    quantity. Its rule records (UP-DOOR-OPEN-002 / 003) are those of 1.5.0 here.

    python3 -I tools/kb_build_1_7.py            write the 1.7.0 registry
    python3 -I tools/kb_build_1_7.py --check    exit 1 when the committed 1.7.0 registry differs from a fresh build

Stdlib only."""
import copy
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "knowledge" / "URBAN_ENGINEERING_KNOWLEDGE_1.5.0.json"
OUT = ROOT / "knowledge" / "URBAN_ENGINEERING_KNOWLEDGE_1.7.0.json"
D = "2026-10-20"
Q = "docs/agents/OWNER_QUESTIONS.md"
T = "tests/t079_arch_v211/test_arch_v211.py::"
CODE = "engine/source/arch_v211.py::"

AMEND = {
    "UP-WET-001": {
        "answers": {"Q-06": "(a) wet: basin-only hand-wash spaces get porcelain floor, full-height wall porcelain, "
                            "waterproofing and a marble threshold (owner 2026-10-18)",
                    "Q-13": "B: the architectural room label is the primary evidence; the sanitary drawing says where "
                            "fixtures and drains are; uncertain fixture recognition never creates wet quantities; no "
                            "label and ambiguous sanitary evidence: hold (owner 2026-10-19)",
                    "Q-30": "A: kitchens are waterproofed like a bathroom (whole floor + 0.20 m upturn), with the "
                            "owner's 3 x 4 m worked example (owner 2026-10-19 14:45)",
                    "Q-37": "A: the pantry is waterproofed within its printed size with the upturn round it, the open "
                            "side a threshold line (owner 2026-10-19 16:40)"},
        "code": [CODE + "decide_review", CODE + "wet_classes"],
        "tests": [T + "test_review_space_decided_wet_by_label_releases_the_wet_scope",
                  T + "test_unlabelled_space_without_evidence_stays_in_review"],
    },
    "UP-WP-003": {
        "answers": {"Q-35": "C: the membrane to BUY follows the strip method per wet area (strips 0.20 m longer at "
                            "both ends whatever sits in the wall); the BOQ upturn line is walls only; one doorway "
                            "transition line per door (a door between two wet rooms once); every figure per wet area, "
                            "the total only as a sum (owner 2026-10-19 16:40; Lead reading 18:15)",
                    "Q-40": "A: no extra shower tanking: the 0.20 m upturn on every wall, wet areas fully tiled "
                            "(owner 2026-10-19 20:45)"},
        "code": [CODE + "door_transition_lines"],
        "tests": [T + "test_door_transitions_one_per_door_shared_door_once"],
    },
    "UP-WP-ROOF-001": {
        "answers": {"Q-24": "roofs are measured like a bathroom: membrane inside the parapet + 0.20 m upturn, whole "
                            "strips with 0.10 m laps (owner 2026-10-19 12:55 and addendum 13:50)",
                    "Q-25": "every drafting gap is covered by the membrane (0.10 m overlap + 0.20 m upturn + the gap) "
                            "and listed with its length; no size limit given (owner 2026-10-19 12:55)",
                    "Q-29": "client change: no dome is concrete; each dome position is an open skylight area with a "
                            "0.20 m upturn round it (owner 2026-10-19 14:45)",
                    "Q-34": "parked: the top roof drawn on no plan stays HELD (no number, never 0) (owner 16:40); "
                            "it is a held line of its own (the uppermost storey plan with rooms has no plan above "
                            "it), never left out of the roof lines (T-093)"},
        "state_1_7_0": "a roof released by EXTERIOR_SPACES_V1 (one closing layer, every gap closed) is SOURCE_DERIVED "
                       "(owner Q-24); a balcony stays PROVISIONAL (this rule, not changed by the answers)",
        "code": [CODE + "roof_lines", CODE + "top_roofs", CODE + "top_roof_lines"],
        "tests": [T + "test_roof_with_skylight_released_like_a_bathroom",
                  T + "test_roof_without_closing_layer_is_held_never_zero",
                  T + "test_top_roofs_storey_order_and_roof_plans"],
    },
    "UP-WP-LAY-001": {
        "answers": {"Q-30": "the owner's worked example: strip 1 = W - 0.20 of floor, next strips W - 0.10, the last "
                            "cut to remaining + 0.10 + 0.20; strip length = floor + 0.20 + 0.20; rolls from the strips "
                            "(16.28 m2 cut, 2 rolls for a 3 x 4 m kitchen), never floor area / roll area",
                    "Q-24 addendum": "full membranes, the edges cut; 1.00 x 10.00 m roll, 0.10 m lap between strips",
                    "Q-49": "A: each wet area and each roof alone (no offcut carried to another area), laid in the "
                            "layout that needs the fewest whole rolls (two strip directions x two start walls; tie: "
                            "the shorter total strip length); per area the cutting plan, the rolls and the leftover "
                            "metres; the project total and leftover as the sums of the areas (owner 2026-10-19 "
                            "22:35)"},
        "code": [CODE + "purchase", CODE + "membrane_table", CODE + "rolls_lines"],
        "tests": [T + "test_rolls_each_area_alone_fewest_rolls_with_cutting_plan",
                  T + "test_membrane_table_owner_kitchen_example"],
    },
}


def build():
    base_bytes = BASE.read_bytes()
    reg = copy.deepcopy(json.loads(base_bytes.decode("utf-8")))
    rules = {r["rule_id"]: r for r in reg["rules"]}
    for rid, a in AMEND.items():
        r = rules[rid]
        lg = dict(r["logic"], owner_answers_1_7_0=dict(a["answers"]))
        if "state_1_7_0" in a:
            lg["state_1_7_0"] = a["state_1_7_0"]
        r.update(logic=lg, effective_version="1.7.0", code=r["code"] + a["code"], tests=r["tests"] + a["tests"],
                 history=r["history"] + [{"version": "1.7.0", "date": D,
                                          "change": "owner answers " + ", ".join(sorted(a["answers"])) + " (" + Q +
                                                    ") recorded for ARCH_TAKEOFF_V2.11 (T-079, T-093)"}])
    reg.update(version="1.7.0", effective=D,
               base={"version": "1.5.0", "sha256": hashlib.sha256(base_bytes).hexdigest()},
               consumed_by=["ARCH_TAKEOFF_V2.11 (tools/urban_boq_m9.py, engine/source/arch_v211.py)"],
               not_consumed_by="ARCH_TAKEOFF_V1 / V2 / V2.1 / V2.2 (frozen; rules/ 1.5.0); ARCH_TAKEOFF_V2.3 reads "
                               "registry 1.0.0; ARCH_TAKEOFF_V2.4 .. V2.6 read registry 1.1.0; ARCH_TAKEOFF_V2.7 "
                               "reads registry 1.2.0; ARCH_TAKEOFF_V2.7.1 reads registry 1.3.0; ARCH_TAKEOFF_V2.8 "
                               "reads registry 1.4.0; ARCH_TAKEOFF_V2.9 / V2.10 read registry 1.5.0 (frozen); "
                               "registry 1.6.0 (door minimum, T-011) is read by no method and is not in 1.7.0",
               rules=sorted(rules.values(), key=lambda r: r["rule_id"]),
               delta={"builder": "tools/kb_build_1_7.py", "new": [], "amended": sorted(AMEND),
                      "owner_questions": [], "answered": [],
                      "status_note": "owner answers recorded in the logic of four rules; no status, value or other "
                                     "rule changed (the 0.20 m upturn, 0.10 m lap and 1.00 x 10.00 m roll are the "
                                     "1.5.0 values)"})
    ids = [r["rule_id"] for r in reg["rules"]]
    assert len(ids) == len(set(ids)), "duplicate rule id"
    return reg


TEXT = json.dumps(build(), indent=1, sort_keys=True, ensure_ascii=False) + "\n"
if __name__ == "__main__":
    if "--check" in sys.argv[1:]:
        same = OUT.is_file() and OUT.read_text(encoding="utf-8") == TEXT
        print("registry 1.7.0 up to date" if same else "registry 1.7.0 differs from a fresh build: run "
                                                        "tools/kb_build_1_7.py")
        sys.exit(0 if same else 1)
    OUT.write_text(TEXT, encoding="utf-8")
    reg = json.loads(TEXT)
    print(len(reg["rules"]), "rules", len(reg["owner_questions"]), "owner questions", OUT.stat().st_size, "bytes")
