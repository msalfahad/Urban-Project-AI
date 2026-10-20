"""KNOWLEDGE REGISTRY 1.8.0 BUILDER (board task T-081 rework) - knowledge/URBAN_ENGINEERING_KNOWLEDGE_1.8.0.json is the
frozen 1.5.0 registry (read byte for byte, never rebuilt) plus the owner's wall-height and room-level answers
(docs/agents/OWNER_QUESTIONS.md Q-43, answered 2026-10-19 21:40, and Q-48, answered 2026-10-19 22:35), as read by
engine/source/finish_height_v2.py (owner_wall_rule) and engine/source/room_levels.py (room_levels_v2).

    amended   UP-HGT-001      (1.8.0): owner wall height for plaster, paint and wet-wall tiles = floor-to-floor (slab
                              to slab, from the printed level marks) - 0.60 m beam - 0.15 m decor ceiling - 0.10 m floor
                              finishing (Q-43; the decor depth fixed at 0.15 m in every room by Q-48 A); a value printed
                              on the drawings comes first; a drawn beam over the room deeper or shallower than 0.60 m
                              holds that room for the owner; room levels of unmarked rooms (Q-43)
              UP-FIN-WALL-001 (1.8.0): wet-room wall tiles run from the floor to the underside of the decor ceiling,
                              the same owner wall height (Q-48 A); a tile height printed on a drawing or detail
                              replaces it
    1.5.0, 1.6.0 and 1.7.0 are unchanged. 1.8.0 is built on 1.5.0 (the registry of ARCH_TAKEOFF_V2.9 / V2.10), like
    1.7.0 (T-079): neither carries the other's amendments, and 1.8.0 is not yet listed in engine/source/knowledge.py
    VERSIONS (that file belongs to the claimed T-079); the method version that wires the heights registers it and, if
    it also needs 1.7.0's wet-area answers, builds the next version from both.

    python3 -I tools/kb_build_1_8.py            write the 1.8.0 registry
    python3 -I tools/kb_build_1_8.py --check    exit 1 when the committed 1.8.0 registry differs from a fresh build

Stdlib only."""
import copy
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "knowledge" / "URBAN_ENGINEERING_KNOWLEDGE_1.5.0.json"
OUT = ROOT / "knowledge" / "URBAN_ENGINEERING_KNOWLEDGE_1.8.0.json"
D = "2026-10-19"
Q = "docs/agents/OWNER_QUESTIONS.md"
T = "tests/t081_room_levels/test_t081_rework.py::"
FH = "engine/source/finish_height_v2.py::"
RL = "engine/source/room_levels.py::"

OWNER_WALL_HEIGHT = {
    "formula": "floor_to_floor - beam_m - decor_ceiling_m - floor_finishing_m",
    "beam_m": 0.60,
    "decor_ceiling_m": 0.15,
    "floor_finishing_m": 0.10,
    "floor_to_floor": "slab to slab from the printed level marks (F.F.L. of the floor above - F.F.L. of this floor; "
                      "+1.00 to +5.50 = 4.50 m); a printed floor-to-floor dimension, or a level the owner states, "
                      "with its source",
    "applies_to": ["PLASTER", "PAINT", "WALL_TILE (wet rooms, UP-FIN-WALL-001 1.8.0)"],
    "precedence": "a height printed on the drawings for the room or its floor (element annotation, section F.C.L. / "
                  "clear height / soffit, a derivation from printed values) comes first; this owner rule only "
                  "when nothing is printed",
    "beam_hold": "the 0.60 m is the owner's standard beam deduction: where a beam drawn over the room is deeper or "
                 "shallower than 0.60 m, that room's height is HELD for the owner, never adjusted; where the beams "
                 "over the room were not read, the height is HELD (BEAM_OVER_ROOM_NOT_CHECKED) with the rule value "
                 "shown as a diagnostic",
    "worked": {"GF 4.50 m (+1.00 to +5.50)": 3.65, "1F 4.20 m (+5.50 to +9.70)": 3.35,
               "2F 4.20 m (+9.70 to +13.90)": 3.35},
    "replaces": "the Q-14 line 'do not subtract an assumed floor build-up or false-ceiling depth' for these three "
                "values only (the owner now states them); the finish_height V1 constant 0.150 m and the register "
                "fallback 0.10 m stay refused as inputs (they are not this rule)",
}
ROOM_LEVEL = {
    "printed": "a level mark printed inside the room is its floor level (ROOM_LEVELS_V1)",
    "one_level_floor": "a room with no printed level on a floor whose printed room levels are all the same takes "
                       "that level (FLOOR_LEVEL: floor level, not printed in the room)",
    "split_floor": "on a floor with two levels a room with no printed level takes +1.00 or +0.30 (the floor's "
                   "levels) only from what is drawn: a section through it, drawn steps, the door sill, the room it "
                   "opens into (nothing drawn across that doorway); a room that stays unclear is HELD and listed, "
                   "never guessed",
    "datum": "levels are measured from the outside ground 0.00; a court or yard level is never a room floor level",
}

AMEND = {
    "UP-HGT-001": {
        "answers": {"Q-43": "levels and the heights rule (owner, main chat 2026-10-19 21:40, with section sheet 10): "
                            "'4.5 m floor height - 0.6 m beam - 0.15 to 0.20 m decor ceiling - 0.10 m floor "
                            "finishing = 3.65 m, the height that plastering and paint count'; first floor 4.20 m; "
                            "'the final floor is +13.9, so 9.7 to 13.9 = 4.2 m'; a room with no printed level takes "
                            "the level of its floor read from the plans, floor by floor",
                    "Q-48": "A: 'floor height minus beam minus ceiling 15cm': the decor ceiling is 0.15 m in every "
                            "room, wet and dry (owner, Lead session 2026-10-19 22:35)"},
        "logic": {"owner_wall_height_1_8_0": OWNER_WALL_HEIGHT, "room_level_1_8_0": ROOM_LEVEL,
                  "trades_1_8_0": {"PLASTER": "printed values first (UP-HGT-001 order), else the owner wall height",
                                   "PAINT": "printed finished-ceiling values first, else the owner wall height",
                                   "WALL_TILE": "a printed tile height, else the owner wall height (Q-48 A)"}},
        "code": [FH + "owner_wall_rule", FH + "room_heights", RL + "room_levels_v2", RL + "doorway_reading"],
        "tests": [T + "test_owner_rule_ground_floor_4_50_gives_3_65", T + "test_owner_rule_first_floor_4_20_gives_3_35",
                  T + "test_beam_deeper_than_0_60_holds_the_room", T + "test_beams_not_read_hold_with_diagnostic",
                  T + "test_printed_ceiling_outranks_the_owner_rule",
                  T + "test_unmarked_room_on_a_one_level_floor_takes_the_floor_level",
                  T + "test_split_floor_room_opens_into_a_levelled_room_with_nothing_drawn"],
    },
    "UP-FIN-WALL-001": {
        "answers": {"Q-48": "A: wet-room wall tiles run from the floor to the underside of the decor ceiling, 0.15 m "
                            "decor in every room: GF 3.65 m, 1F and 2F 3.35 m; a tile height printed on a drawing or "
                            "detail replaces it (owner, Lead session 2026-10-19 22:35)"},
        "logic": {"height_1_8_0": "the owner wall height of UP-HGT-001 1.8.0 (to the underside of the 0.15 m decor "
                                  "ceiling); a printed tile height replaces it"},
        "code": [FH + "room_heights"],
        "tests": [T + "test_wet_room_tiles_take_the_owner_height_and_a_printed_tile_height_wins"],
    },
}


def build():
    base_bytes = BASE.read_bytes()
    reg = copy.deepcopy(json.loads(base_bytes.decode("utf-8")))
    rules = {r["rule_id"]: r for r in reg["rules"]}
    for rid, a in AMEND.items():
        r = rules[rid]
        lg = dict(r["logic"], owner_answers_1_8_0=dict(a["answers"]), **a["logic"])
        r.update(logic=lg, effective_version="1.8.0", code=r["code"] + a["code"], tests=r["tests"] + a["tests"],
                 history=r["history"] + [{"version": "1.8.0", "date": D,
                                          "change": "owner answers " + ", ".join(sorted(a["answers"])) + " (" + Q +
                                                    ") recorded as owner rule values (T-081 rework)"}])
    reg.update(version="1.8.0", effective=D,
               base={"version": "1.5.0", "sha256": hashlib.sha256(base_bytes).hexdigest()},
               consumed_by=["engine/source/finish_height_v2.py (owner_wall_rule; not wired into a method)",
                            "engine/source/room_levels.py (room_levels_v2; not wired into a method)"],
               not_consumed_by="every released method (ARCH_TAKEOFF_V1 .. V2.10 read registries 1.0.0 .. 1.5.0 or "
                               "rules/ 1.5.0); registry 1.6.0 (door minimum, T-011) and 1.7.0 (wet areas, T-079) are "
                               "not in 1.8.0",
               rules=sorted(rules.values(), key=lambda r: r["rule_id"]),
               delta={"builder": "tools/kb_build_1_8.py", "new": [], "amended": sorted(AMEND),
                      "owner_questions": [], "answered": ["Q-43", "Q-48"],
                      "status_note": "owner answers recorded in the logic of two rules; their status stays "
                                     "OWNER_APPROVED; no other rule changed"})
    ids = [r["rule_id"] for r in reg["rules"]]
    assert len(ids) == len(set(ids)), "duplicate rule id"
    return reg


TEXT = json.dumps(build(), indent=1, sort_keys=True, ensure_ascii=False) + "\n"
if __name__ == "__main__":
    if "--check" in sys.argv[1:]:
        same = OUT.is_file() and OUT.read_text(encoding="utf-8") == TEXT
        print("registry 1.8.0 up to date" if same else "registry 1.8.0 differs from a fresh build: run "
                                                        "tools/kb_build_1_8.py")
        sys.exit(0 if same else 1)
    OUT.write_text(TEXT, encoding="utf-8")
    reg = json.loads(TEXT)
    print(len(reg["rules"]), "rules", len(reg["owner_questions"]), "owner questions", OUT.stat().st_size, "bytes")
