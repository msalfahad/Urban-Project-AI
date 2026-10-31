"""T-199: the Alsenan V3.0.30 inputs, built only from the Checker-merged ledgers (pinned): totals close on the merged
ledgers, every face of the T-332 face ledger accounted for once, held blank, S1 never, the downgrade-bound concrete
lines carry no valued formwork, an edited ledger stops the build. (No private drawing is read here.)"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t199"))

import t199_inputs as T  # noqa: E402
from engine.source import arch_v3030 as A  # noqa: E402

PID = "development-villa-t131"


@pytest.fixture(scope="module")
def d():
    return T.build(PID)


def test_validates(d):
    A.load_inputs(d, PID)


def test_calculated_closes_on_t332(d):
    calc = {}
    for r in d["formwork"]:
        if r["status"] == "CALCULATED":
            calc[r["method"]] = calc.get(r["method"], 0.0) + r["m2"]
    assert round(calc["G"], 6) == 626.872989 and round(calc["E=G"], 6) == 434.854504      # T-332 s.2
    assert round(sum(calc.values()), 6) == 1061.727493                                    # T-332 s.3 total
    assert round(sum(d["comparison_e_m2"].values()), 6) == 422.69342                      # E, comparison only


def test_stair_sides_t352(d):
    s = d["stair_sides"]
    assert len({r["line_id"] for r in s}) == 8 and sum(r["faces"] for r in s) == 27
    assert round(sum(r["m2"] for r in s if r["status"] == "CALCULATED"), 6) == 4.1054
    assert sum(r["faces"] for r in s if r["status"] == "CALCULATED") == 7
    assert all(r["m2"] is None for r in s if r["status"] != "CALCULATED")
    assert any(n.startswith("T352-27") for r in s for n in r["notes"])                    # N-T352-1 carried


def test_every_face_once(d):
    faces = [r["face_id"] for r in csv.DictReader((ROOT / "research/agents_t332/FORMWORK_T332_BY_FACE.csv")
                                                  .read_text(encoding="utf-8").splitlines())]
    booked = A.load_inputs(d, PID)["_faces"]
    e_faces = {f for r in csv.DictReader((ROOT / "research/agents_t332/T199_FILL_T332.csv").read_text(
        encoding="utf-8").splitlines()) if r["method"] == "E" for f in r["face_ids"].split()}
    named = {n["face_id"] for n in d["named_not_lines"]}
    t332_booked = {f for f in booked if not f.startswith("T352-")}
    assert set(faces) == t332_booked | e_faces | named
    assert not (t332_booked & e_faces) and not (t332_booked & named) and not (e_faces & named)
    assert sum(1 for f in booked if f.startswith("T352-")) == 27


def test_superseded_and_scenario_not_lines(d):
    named = {n["face_id"]: n["class"] for n in d["named_not_lines"]}
    assert named["R4-339"] == "SUPERSEDED" and named["R4-314"] == "OWNED_BY_OTHER_LINE"
    assert sum(1 for c in named.values() if c == "SCENARIO_NOT_IN_CANDIDATE") == 7
    assert not any("S1" in f.upper().split(".") for f in A.load_inputs(d, PID)["_faces"])


def test_parapet_and_lift_faces_held_blank(d):
    par = [u for u in d["untied"] if u["face_id"].startswith("T332-PARAPET-")]
    assert len(par) == 24
    assert round(sum(u["lo"] for u in par), 6) == 81.58869 and round(sum(u["hi"] for u in par), 6) == 202.781594
    assert {u["face_id"] for u in d["untied"] if u["element"] == "LIFT"} == {"T332-LIFT-PIT-INNER",
                                                                             "T332-LIFT-PIT-OUTER"}
    assert len(d["untied"]) == 108 and all(u.get("m2") is None for u in d["untied"])


def test_held_rows_blank_and_alternatives_paired(d):
    assert all(r["m2"] is None for r in d["formwork"] if r["status"] != "CALCULATED")
    assert len(d["alternatives"]) == 60
    assert round(sum(a["alternatives"]["OQ10_FORMED"]["m2"] for a in d["alternatives"]), 6) == 183.696276


def test_downgrade_bound_lines_carry_no_valued_formwork(d):
    dg = set(d["downgrade_bound_lines"])
    assert len(d["downgrade_records"]) == 9
    assert not [r for r in d["formwork"] if r["line_id"] in dg and r["status"] == "CALCULATED"]


def test_railings_and_shutters(d):
    rl = {r["run"]: r for r in d["railings"]}
    conf = [r for r in d["railings"] if r["status"] == "DRAWING-CONFIRMED"]
    assert round(sum(r["lm"] for r in conf), 6) == 38.916                                 # T-164 confirmed
    assert round(sum(r["lm"] for r in conf if r["verified"]), 6) == 12.888                # Checker RL-02 + RL-03
    assert rl["RL-04"]["lm"] is None and rl["RL-04"]["measured_part_lm"] == 6.127
    assert rl["RL-07"]["lm"] is None and rl["RL-07"]["measured_part_lm"] == 16.153
    assert rl["RL-09"]["status"] == "UNKNOWN" and rl["RL-12"]["status"] == "EXCLUDED"
    assert sum(s["pcs"] for s in d["shutters"]) == 6 and all(s["m2"] is None for s in d["shutters"])


def test_edited_ledger_stops_the_build(monkeypatch):
    monkeypatch.setitem(T.PINS, T.FILL, "0" * 64)
    with pytest.raises(T.PinError, match="edited ledger"):
        T.build(PID)
