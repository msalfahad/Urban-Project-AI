"""T-422: research/agents_t296/t296_skirting_opening_rules.py (the task-prefixed name, a new file) behaves exactly as the
merged research/agents_t296/skirting_opening_rules.py (kept unchanged on disk): same results on the K296 hand cases,
same refusals on the adverse ones; the body below the docstring is the same text."""
from __future__ import annotations

import ast
import copy
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
OLD = ROOT / "research/agents_t296/skirting_opening_rules.py"
NEW = ROOT / "research/agents_t296/t296_skirting_opening_rules.py"


def _load(p, name):
    spec = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


O, N = _load(OLD, "t422_old_rules"), _load(NEW, "t422_new_rules")


def _room(sill_state="ESTABLISHED", sill_m=0.90, fc="DRY"):
    # K296-B1 (tests/t296_skirting_ledger): 15.00 m boundary, doors 0.90 + 0.80, tiled wall 3.50, W-1 1.20 sill 0.90
    return {"room_id": "K296-B1", "finish_class": fc, "pieces": [
        {"piece_id": "A1", "kind": "WALL", "length_m": 3.10},
        {"piece_id": "A2", "kind": "DOOR", "opening_id": "D-1", "length_m": 0.90},
        {"piece_id": "B", "kind": "TILED_WALL", "length_m": 3.50},
        {"piece_id": "C1", "kind": "WALL", "length_m": 2.80},
        {"piece_id": "C2", "kind": "WINDOW", "opening_id": "W-1", "length_m": 1.20, "sill_state": sill_state,
         "sill_m": sill_m},
        {"piece_id": "D1", "kind": "WALL", "length_m": 2.70},
        {"piece_id": "D2", "kind": "DOOR", "opening_id": "D-2", "length_m": 0.80}]}


def test_body_identical_below_the_docstring():
    def body(p):
        t = ast.parse(p.read_text(encoding="utf-8"))
        return ast.dump(ast.Module(body=t.body[1:], type_ignores=[]))
    assert body(OLD) == body(NEW)


@pytest.mark.parametrize("case", [("ESTABLISHED", 0.90, "DRY"), ("HELD", None, "DRY"), ("ESTABLISHED", 0.0, "DRY"),
                                  ("ESTABLISHED", 0.90, "WET_FULL_HEIGHT_TILE"), ("ESTABLISHED", 0.90, "UNKNOWN")])
def test_same_ledger(case):
    r = _room(*case)
    assert O.room_ledger(copy.deepcopy(r)) == N.room_ledger(copy.deepcopy(r))
    if case == ("ESTABLISHED", 0.90, "DRY"):
        assert N.room_ledger(r)["certain_lm"] == pytest.approx(9.80, abs=1e-9)


def test_same_refusals():
    twice = _room()
    twice["pieces"].append({"piece_id": "X", "kind": "DOOR", "opening_id": "D-1", "length_m": 0.9})
    held0 = _room("HELD", None, "UNKNOWN")
    held0["reported_lm"] = 0
    deducted = _room()
    deducted["pieces"][4]["deduct"] = True
    for bad in (twice, held0, deducted):
        with pytest.raises(ValueError) as e_old:
            O.room_ledger(copy.deepcopy(bad))
        with pytest.raises(ValueError) as e_new:
            N.room_ledger(copy.deepcopy(bad))
        assert str(e_old.value) == str(e_new.value)


def test_same_trail():
    line = {"line_id": "L-k296", "gross": 15.0, "net": 8.6}
    ded = [{"opening_id": "D-1", "length_m": 0.9, "listed": True}, {"opening_id": "D-2", "length_m": 0.8, "listed": True},
           {"cause": "W-1 threshold", "length_m": 1.2, "listed": False},
           {"cause": "tiled base", "length_m": 3.5, "listed": False}]
    assert O.line_trail(line, ded) == N.line_trail(line, ded)
    assert N.line_trail(line, ded)["readds_with_named"] is True
