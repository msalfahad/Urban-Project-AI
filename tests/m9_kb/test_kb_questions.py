"""Phase 2B-1 WP-2: question generation (UP-KB-QUES-001; engine.source.knowledge.owner_questions) - an unresolved
item is classified A (an approved rule answers it: never asked), B (a document is missing), C (rules disagree), D (no
owner policy) or E (an engine defect); repeated instances make one question, and only C / D reach the owner."""

from __future__ import annotations

import copy
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import kb_fixtures as KF                                      # noqa: E402
from engine.source import knowledge as K                      # noqa: E402

CAT = K.registry()["question_catalogue"]
V22, V23 = "ARCH_TAKEOFF_V2.2", "ARCH_TAKEOFF_V2.3"


@pytest.fixture(scope="module")
def villa(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("villa")
    return {m: KF.villa_run(tmp, m, facts=f) for m, f in ((V22, None), (V23, None))} | {
        "v23_tile": KF.villa_run(tmp, V23, facts=KF.FX.HEIGHT_FACTS)}


def test_every_catalogue_entry_is_reached_by_its_example():
    """no entry is shadowed by an earlier, broader pattern (a stair-hall finish once fell into STAIR_SECTIONS)."""
    for q in CAT:
        got = K.classify_question(q["example"])
        assert got is not None and (got["pattern"], got.get("item")) == (q["pattern"], q.get("item")), q["group"]
    assert all(q["category"] in K.CATEGORIES for q in CAT)
    assert all(q.get("question_id") for q in CAT if q["category"] == "D_MISSING_OWNER_POLICY")


def test_established_rules_are_never_asked(villa):
    """the A items V2.2 still raises on the villa (door heights, doorway strip finish ...) are answered under V2.3;
    nothing is unclassified; the owner list holds only C / D questions."""
    before = K.owner_questions(villa[V22][0]["unresolved"], method=V22)["summary"]
    assert before["instances"]["A_ESTABLISHED"] > 0                       # failing-before evidence
    for key in (V23, "v23_tile"):
        oq = villa[key][1]["owner_questions"]
        assert oq["summary"]["established_but_still_raised"] == 0 and oq["by_category"]["A_ESTABLISHED"] == []
        assert oq["summary"]["unclassified"] == 0
        assert {q["category"] for q in oq["owner_questions"]} <= {"C_RULE_CONFLICT", "D_MISSING_OWNER_POLICY"}
    # the genuine policy gaps only: the stair-hall finishes (OQ-03) and the head of an enlarged wall opening
    # (OQ-02, raised once for the run, however many doors) - the approved door widths are never re-asked
    oq = villa["v23_tile"][1]["owner_questions"]
    assert sorted(q["id"] for q in oq["owner_questions"]) == ["OQ-02", "OQ-03"]
    d = {g["group"]: g["instances"] for g in oq["by_category"]["D_MISSING_OWNER_POLICY"]}
    assert d == {"STAIR_HALL_FINISHES": 3, "DOOR_HEAD_ALLOWANCE": 1}


def test_repeated_instances_are_grouped_into_one_question():
    """the same underlying question on many rooms and floors is one group with its instance count, floors, items
    and a few examples - and one owner question."""
    items = [{"floor": fl, "room_id": f"{fl}-R{i}", "item": "FIN.PAINT",
              "reason": f"STAIR_HALL_FINISH_NOT_ESTABLISHED (Q-S6-4): stair {i}"} for fl in ("GF", "1F", "2F")
             for i in range(4)]
    items += [{"floor": "GF", "room_id": "-", "item": "ARCH.EXTERIOR",
               "reason": "EXTERIOR_FINISH_SCOPE_NOT_ESTABLISHED (Q1): a garden"}] * 2
    out = K.owner_questions(items, method=V23)
    (g,) = out["by_category"]["D_MISSING_OWNER_POLICY"][:1]
    assert g["group"] == "STAIR_HALL_FINISHES" and g["instances"] == 12 and g["floors"] == ["1F", "2F", "GF"]
    assert len(g["examples"]) == 3 and g["items"] == ["FIN.PAINT"]
    assert sorted(q["id"] for q in out["owner_questions"]) == ["OQ-03", "OQ-04"]
    assert out["summary"]["groups"]["D_MISSING_OWNER_POLICY"] == 2 and out["summary"]["unresolved_items"] == 14


def test_engine_defects_are_never_owner_questions():
    """E items (reader limits, strip attribution, geometry checks) are engineering backlog: never on the owner list,
    whatever their count; a B item is a document request, not a question either."""
    items = [{"floor": "GF", "item": "ARCH.THRESHOLD", "reason": "STRIP_NOT_ATTRIBUTED: a strip"},
             {"floor": "GF", "item": "ADMISSION:X", "reason": "WARNING: 3 HATCH: READ_ONE_BLOCK_LEVEL"},
             {"floor": "GF", "item": "door symbol D1", "reason": "DOOR_CLOSURE_UNRESOLVED: no leaf"},
             {"floor": "GF", "item": "ARCH.THRESHOLD", "reason": "THRESHOLD_STRIP_NOT_ATTRIBUTED (UP-THR-001)"},
             {"floor": "GF", "item": "FIN.PAINT", "reason": "WALL_FINISH_HEIGHT_NOT_ESTABLISHED (PAINT)"}] * 5
    out = K.owner_questions(items, method=V23)
    assert out["owner_questions"] == [] and out["summary"]["owner_questions"] == 0
    assert out["summary"]["instances"]["E_ENGINEERING_DEFECT"] == 20
    assert {g["group"] for g in out["by_category"]["E_ENGINEERING_DEFECT"]} == {"STRIP_ATTRIBUTION", "READER_LIMITS"}
    assert all(not q.get("question_id") for q in CAT if q["category"] in ("B_MISSING_DRAWING_EVIDENCE",
                                                                         "E_ENGINEERING_DEFECT"))


def test_an_unknown_reason_is_reported_unclassified_never_dropped():
    out = K.owner_questions([{"floor": "GF", "item": "X", "reason": "SOMETHING_NEW: never seen"}], method=V23)
    assert out["summary"]["unclassified"] == 1 and out["unclassified"][0]["reason"].startswith("SOMETHING_NEW")
    assert sum(out["summary"]["instances"].values()) == 0


def test_the_catalogue_prefixes_are_the_engine_prefixes():
    """every catalogue prefix the V2.3 modules raise appears verbatim in engine code (no dead pattern)."""
    src = "".join((KF.ROOT / "engine" / "source" / f).read_text(encoding="utf-8") for f in (
        "arch_measure.py", "arch_completeness.py", "owner_finish_scope.py", "door_model.py", "door_standards.py",
        "arch_rooms.py", "release_safety.py", "discovery.py", "materials.py") if (KF.ROOT / "engine" / "source" / f).exists())
    for q in CAT:
        lit = re.match(r"\^\(?([A-Z][A-Z0-9_\-]+)", q["pattern"])
        if lit and q["category"] != "A_ESTABLISHED" and lit.group(1) not in ("REVIEW", "WARNING", "MISSING_SOURCE"):
            assert lit.group(1) in src, q["pattern"]


def test_copying_the_unresolved_list_changes_nothing(villa):
    """the question register is a pure function of the unresolved items (deterministic, order-stable)."""
    u = villa[V23][0]["unresolved"]
    a = K.owner_questions(copy.deepcopy(u), method=V23)
    b = K.owner_questions(copy.deepcopy(u), method=V23)
    assert a == b and a["summary"] == villa[V23][1]["owner_questions"]["summary"]
