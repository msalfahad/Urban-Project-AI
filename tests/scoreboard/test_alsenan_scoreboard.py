"""T-001a: tools/alsenan_scoreboard.py on a hand-calculated synthetic fixture (two trades, m2 + nr).

Hand calculation (written before running the scorer):
  PLASTER m2 - 4 reference lines
    R1 LIV  ref 100.0, engine E1 104.0 (RELEASED)              |err| 4, signed +4, verdict ENGINE_RIGHT (hand calc)
    R2 KIT  ref  50.0, engine E2 30.0 + E3 30.0 (same surface)  = 60.0, |err| 10, signed +10, E3 is a DUPLICATE,
            verdict FREELANCER_RIGHT
    R3 BED  ref  80.0, no engine row                            SILENT OMISSION
    R4 BATH ref  20.0, engine E4 BLOCKED, qty None              HELD (covered, not compared)
    coverage 3/4 = 0.75; WAPE (4 + 10) / (100 + 50) = 14/150 = 0.0933333...; signed +14/150;
    adjudicated (ENGINE_RIGHT not counted) 10/150 = 0.0666666...; false positive E8 (key ROOF) 12.0 m2; duplicates 1
  DOORS nr - 3 reference lines (+1 without a unit, own bucket)
    R5 GF   ref 10, engine E5 9 (RELEASED)                      |err| 1, signed -1, no verdict (counts)
    R6 1F   ref  8, engine E6 16.8 m2                           UNIT_MISMATCH, refused, not covered
    R7 RF   ref  2, engine E7 NOT_IN_SOURCE                     UNSUPPORTED (covered)
    coverage 2/3; WAPE 1/10 = 0.1; signed -0.1; adjudicated 0.1
    R8 GAR  ref 1, unit ''  engine E9 1 nr                      REFERENCE_UNIT_MISSING, bucket DOORS / (missing)
"""

from __future__ import annotations

import json
import random
import subprocess
import sys
from pathlib import Path

import pytest

from tools import alsenan_scoreboard as S

ROOT = Path(__file__).resolve().parents[2]
TOL = 1e-6


def reference():
    return [
        {"id": "R1", "trade": "PLASTER", "unit": "m2", "qty": 100.0, "key": "P-GF-LIV"},
        {"id": "R2", "trade": "PLASTER", "unit": "م2", "qty": 50.0, "key": "P-GF-KIT"},
        {"id": "R3", "trade": "PLASTER", "unit": "m2", "qty": 80.0, "key": "P-1F-BED"},
        {"id": "R4", "trade": "PLASTER", "unit": "m2", "qty": 20.0, "key": "P-1F-BATH"},
        {"id": "R5", "trade": "DOORS", "unit": "nr", "qty": 10, "key": "D-GF"},
        {"id": "R6", "trade": "DOORS", "unit": "عدد", "qty": 8, "key": "D-1F"},
        {"id": "R7", "trade": "DOORS", "unit": "nr", "qty": 2, "key": "D-RF"},
        {"id": "R8", "trade": "DOORS", "unit": "", "qty": 1, "key": "D-GAR"},
    ]


def engine():
    return [
        {"id": "E1", "trade": "PLASTER", "unit": "m2", "qty": 104.0, "status": "COMPUTED", "key": "P-GF-LIV",
         "surface": "S1"},
        {"id": "E2", "trade": "PLASTER", "unit": "m²", "qty": 30.0, "status": "COMPUTED", "key": "P-GF-KIT",
         "surface": "S2"},
        {"id": "E3", "trade": "PLASTER", "unit": "m2", "qty": 30.0, "status": "COMPUTED", "key": "P-GF-KIT",
         "surface": "S2"},
        {"id": "E4", "trade": "PLASTER", "unit": "m2", "qty": None, "status": "BLOCKED", "key": "P-1F-BATH"},
        {"id": "E5", "trade": "DOORS", "unit": "nr", "qty": 9, "status": "COMPUTED", "key": "D-GF"},
        {"id": "E6", "trade": "DOORS", "unit": "m2", "qty": 16.8, "status": "COMPUTED", "key": "D-1F"},
        {"id": "E7", "trade": "DOORS", "unit": "nr", "qty": None, "status": "NOT_IN_SOURCE", "key": "D-RF"},
        {"id": "E8", "trade": "PLASTER", "unit": "m2", "qty": 12.0, "status": "COMPUTED", "key": "P-ROOF"},
        {"id": "E9", "trade": "DOORS", "unit": "nr", "qty": 1, "status": "COMPUTED", "key": "D-GAR"},
    ]


VERDICTS = {
    "R1": {"verdict": "ENGINE_RIGHT", "hand_calc": "2 x (5.20 + 4.80) x 5.20 = 104.00 m2 from A-101"},
    "R2": {"verdict": "FREELANCER_RIGHT"},
}


def bucket(res, trade, unit):
    [b] = [b for b in res["buckets"] if b["trade"] == trade and b["unit"] == unit]
    return b


def line(res, rid):
    [ln] = [ln for ln in res["lines"] if ln["ref_id"] == rid]
    return ln


def test_plaster_m2_matches_hand_calculation():
    res = S.score(engine(), reference(), VERDICTS)
    b = bucket(res, "PLASTER", "m2")
    assert b["reference_lines"] == 4
    assert b["covered"] == 3 and abs(b["coverage"] - 0.75) < TOL
    assert b["silent_omissions"] == 1
    assert b["held"] == 1 and b["compared"] == 2
    assert abs(b["sum_reference"] - 150.0) < TOL
    assert abs(b["wape"] - 14.0 / 150.0) < TOL
    assert abs(b["signed_error_ratio"] - 14.0 / 150.0) < TOL
    assert abs(b["wape_adjudicated"] - 10.0 / 150.0) < TOL
    assert b["false_positives"] == 1 and abs(b["false_positive_qty"] - 12.0) < TOL
    assert b["duplicates"] == 1
    assert line(res, "R2")["duplicate_engine_ids"] == ["E3"]
    assert abs(line(res, "R2")["engine_qty"] - 60.0) < TOL
    assert line(res, "R3")["outcome"] == S.OUT_SILENT
    assert line(res, "R4")["outcome"] == S.OUT_HELD and line(res, "R4")["engine_qty"] is None


def test_doors_nr_matches_hand_calculation_and_refuses_unit_mismatch():
    res = S.score(engine(), reference(), VERDICTS)
    b = bucket(res, "DOORS", "nr")
    assert b["reference_lines"] == 3
    assert b["covered"] == 2 and abs(b["coverage"] - 2.0 / 3.0) < TOL
    assert b["unit_mismatch"] == 1 and b["silent_omissions"] == 0
    assert b["unsupported"] == 1 and b["compared"] == 1
    assert abs(b["wape"] - 0.1) < TOL
    assert abs(b["signed_error_ratio"] + 0.1) < TOL
    assert abs(b["wape_adjudicated"] - 0.1) < TOL
    r6 = line(res, "R6")
    assert r6["outcome"] == S.OUT_UNIT_MISMATCH and r6["refused_engine_ids"] == ["E6"]
    assert r6["engine_qty"] is None and r6["abs_error"] is None
    # the refused m2 answer never lands in an m2 bucket either
    assert not [b for b in res["buckets"] if b["trade"] == "DOORS" and b["unit"] == "m2"]


def test_reference_without_unit_is_its_own_bucket_never_compared():
    res = S.score(engine(), reference(), VERDICTS)
    b = bucket(res, "DOORS", S.MISSING_UNIT)
    assert b["reference_lines"] == 1 and b["covered"] == 0 and b["compared"] == 0
    assert b["wape"] is None
    assert line(res, "R8")["outcome"] == S.OUT_REF_UNIT_MISSING


def test_missing_never_becomes_zero():
    eng = engine()
    eng[0] = dict(eng[0], qty=None)  # RELEASED without a quantity -> HELD, not 0
    ref = reference()
    ref[1] = dict(ref[1], qty=None)  # reference without a quantity -> covered, not in WAPE
    res = S.score(eng, ref, VERDICTS)
    assert line(res, "R1")["outcome"] == S.OUT_HELD
    assert line(res, "R2")["outcome"] == S.OUT_REF_QTY_MISSING
    b = bucket(res, "PLASTER", "m2")
    assert b["compared"] == 0 and b["sum_reference"] == 0.0
    assert b["wape"] is None and b["signed_error_ratio"] is None and b["wape_adjudicated"] is None


def test_zero_reference_sum_gives_none_not_zero_percent():
    res = S.score([{"id": "E", "trade": "T", "unit": "m2", "qty": 0.0, "status": "COMPUTED", "key": "k"}],
                  [{"id": "R", "trade": "T", "unit": "m2", "qty": 0.0, "key": "k"}])
    assert res["buckets"][0]["wape"] is None


def test_partly_held_answer_is_not_compared():
    eng = engine() + [{"id": "E10", "trade": "PLASTER", "unit": "m2", "qty": 5.0, "status": "PARTIAL",
                       "key": "P-GF-LIV"}]
    res = S.score(eng, reference(), VERDICTS)
    assert line(res, "R1")["outcome"] == S.OUT_HELD
    assert abs(bucket(res, "PLASTER", "m2")["wape"] - 10.0 / 50.0) < TOL


def test_engine_right_without_hand_calc_counts_against_engine():
    res = S.score(engine(), reference(), {"R1": {"verdict": "ENGINE_RIGHT"}})
    assert line(res, "R1")["verdict"] == "UNRESOLVED" and line(res, "R1")["verdict_downgraded"]
    assert abs(bucket(res, "PLASTER", "m2")["wape_adjudicated"] - 14.0 / 150.0) < TOL
    assert res["warnings"]


def test_rule_difference_is_not_counted():
    res = S.score(engine(), reference(), {"R2": {"verdict": "RULE_DIFFERENCE"}})
    assert abs(bucket(res, "PLASTER", "m2")["wape_adjudicated"] - 4.0 / 150.0) < TOL


def test_row_order_does_not_change_the_score():
    base = S.score(engine(), reference(), VERDICTS)["buckets"]
    rng = random.Random(7)
    for _ in range(5):
        eng, ref = engine(), reference()
        rng.shuffle(eng)
        rng.shuffle(ref)
        got = S.score(eng, ref, VERDICTS)["buckets"]
        assert len(got) == len(base)
        for a, b in zip(base, got):
            for k, v in a.items():
                assert (abs(v - b[k]) < TOL) if isinstance(v, float) else v == b[k], k


def test_unmapped_engine_row_is_listed_not_a_false_positive():
    eng = engine() + [{"id": "E11", "trade": "PLASTER", "unit": "m2", "qty": 3.0, "status": "COMPUTED"}]
    res = S.score(eng, reference(), VERDICTS)
    assert [u["engine_id"] for u in res["unmapped_engine_rows"]] == ["E11"]
    assert bucket(res, "PLASTER", "m2")["false_positives"] == 1


@pytest.mark.parametrize("bad", [
    {"unit": "furlong"}, {"status": "MAYBE"}, {"qty": "12"}, {"qty": float("nan")}, {"qty": True},
])
def test_bad_engine_input_is_refused(bad):
    eng = engine()
    eng[0] = dict(eng[0], **bad)
    with pytest.raises(ValueError):
        S.score(eng, reference(), VERDICTS)


def test_ambiguous_keys_ids_and_verdicts_are_refused():
    ref = reference() + [{"id": "R9", "trade": "PLASTER", "unit": "m2", "qty": 1.0, "key": "P-GF-LIV"}]
    with pytest.raises(ValueError):
        S.score(engine(), ref)
    with pytest.raises(ValueError):
        S.score(engine() + [dict(engine()[0])], reference())
    with pytest.raises(ValueError):
        S.score(engine(), reference(), {"R1": {"verdict": "PROBABLY_FINE"}})


def test_units_are_folded_never_converted():
    assert S.norm_unit("م.ط") == S.norm_unit("m") == "lm"
    assert S.norm_unit("kg") != S.norm_unit("t")
    assert S.norm_unit("mm") != S.norm_unit("m")
    assert S.norm_unit("") is None and S.norm_unit(None) is None


def test_adapters_on_register_shapes():
    boq = {"lines": [{"line_id": "B1", "trade": "PLASTER_PAINT", "unit": "m2", "qty": 5.0, "status": "COMPUTED"},
                     {"line_id": "B2", "trade": "PLASTER_PAINT", "unit": "m2", "qty": None, "status": "BLOCKED"}]}
    rows = S.engine_rows_from_boq_lines(boq, {"B1": "k1"})
    assert rows[0]["key"] == "k1" and rows[1]["key"] is None
    norm = {"records": [{"id": "F:1", "row_kind": "DETAIL", "trade": "PLASTER", "unit": "م2", "qty": 6.0},
                        {"id": "F:2", "row_kind": "DETAIL", "trade": "PLASTER", "unit": "م2", "qty": 1.0},
                        {"id": "F:3", "row_kind": "COVER_TOTAL", "trade": "PLASTER", "unit": "م2", "qty": 7.0}]}
    ref, unmapped = S.reference_rows_from_normalised(norm, {"F:1": "k1"})
    assert [r["id"] for r in ref] == ["F:1"] and unmapped == ["F:2"]
    res = S.score(rows, ref)
    assert abs(res["buckets"][0]["wape"] - 1.0 / 6.0) < TOL


def test_cli_writes_only_where_told(tmp_path):
    (tmp_path / "e.json").write_text(json.dumps(engine()), encoding="utf-8")
    (tmp_path / "r.json").write_text(json.dumps({"rows": reference()}), encoding="utf-8")
    (tmp_path / "v.json").write_text(json.dumps(VERDICTS), encoding="utf-8")
    out, md = tmp_path / "out.json", tmp_path / "out.md"
    cp = subprocess.run([sys.executable, "-I", str(ROOT / "tools" / "alsenan_scoreboard.py"),
                         "--engine", str(tmp_path / "e.json"), "--reference", str(tmp_path / "r.json"),
                         "--verdicts", str(tmp_path / "v.json"), "--out", str(out), "--markdown", str(md)],
                        capture_output=True, text=True, cwd=tmp_path)
    assert cp.returncode == 0, cp.stderr
    res = json.loads(out.read_text(encoding="utf-8"))
    assert abs(bucket(res, "PLASTER", "m2")["wape"] - 14.0 / 150.0) < TOL
    assert "| PLASTER | m2 | 4 | 75.00 % | 1 |" in md.read_text(encoding="utf-8")
