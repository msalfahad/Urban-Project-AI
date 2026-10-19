"""T-001b: tools/alsenan_keymap.py (canonical engine lines + freelancer rows -> scorer rows through a key map) on a
hand-calculated synthetic fixture that is not Alsenan, plus a validity check of the committed key map.

Hand calculation (written before running the adapter):
  CONCRETE m3 - 3 reference lines
    FOOT ref 20.0: L1 FOOTING 10.0 (SOURCE_DERIVED, element F1) + L2 STRAP 2.5 (PROVISIONAL, S1)
                   + L3 FOOTING 10.0 (SOURCE_DERIVED, element F1 again)    = 22.5, |err| 2.5, L3 a DUPLICATE
    SLAB ref  8.0: L4 SLAB BLOCKED_RFI, no qty                             HELD
    BEAM ref  6.0: L5 BEAM BOUNDED_EXPOSURE, measured_net 5.0 (a range)    HELD, the 5.0 never released
    coverage 3/3; compared 1; WAPE 2.5 / 20 = 0.125; signed +0.125; duplicates 1
  PAINT m2 - 1 reference line, its unit from the map (record unit empty, source given)
    WALL ref 50.0: L6 PAINT 40.0 (MEASURED); L7 PAINT NOT_APPLICABLE (excluded, not an answer);
                   L8 PAINT 4000 mm (refused: never converted)             = 40.0, |err| 10, WAPE 0.2, signed -0.2
  FLOOR_AREA m2 - FLR ref 35.0: L9 PORCELAIN 30.0 (MEASURED) + one CONDITIONAL set carrying PORCELAIN -> HELD
  WINDOWS m2 - WIN ref 12.0: L10 + L11 ARCH.WINDOW 1 pcs each              UNIT_MISMATCH (coverage 0)
  CEILING m2 - CEIL ref 9.0: L12 FIN.CEILING state 'ODD_STATE', qty 9.0    HELD (unknown state is never released)
  L13 ARCH.SPACE 30.0 m2: no key -> UNMAPPED, not a false positive
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from tools import alsenan_keymap as K

ROOT = Path(__file__).resolve().parents[2]
TOL = 1e-6


def line(lid, code, unit, ev, net, element):
    return {"line_id": lid, "item_code": code, "unit": unit, "evidence_state": ev, "measured_net": net,
            "trade": "X", "location": {"element_id": element}}


def lines():
    return [
        line("L1", "STR.CONC.FOOTING", "m3", "SOURCE_DERIVED", 10.0, "F1"),
        line("L2", "STR.CONC.STRAP", "m3", "PROVISIONAL", 2.5, "S1"),
        line("L3", "STR.CONC.FOOTING", "m3", "SOURCE_DERIVED", 10.0, "F1"),
        line("L4", "STR.CONC.SLAB", "m3", "BLOCKED_RFI", None, "SL1"),
        line("L5", "STR.CONC.BEAM", "m3", "BOUNDED_EXPOSURE", 5.0, "B1"),
        line("L6", "FIN.PAINT", "m2", "MEASURED", 40.0, "R1:paint"),
        line("L7", "FIN.PAINT", "m2", "NOT_APPLICABLE_WITH_EVIDENCE", None, "R2:paint"),
        line("L8", "FIN.PAINT", "mm", "MEASURED", 4000.0, "R3:paint"),
        line("L9", "FIN.FLOOR.PORCELAIN", "m2", "MEASURED", 30.0, "R1:floor"),
        line("L10", "ARCH.WINDOW", "pcs", "SOURCE_DERIVED", 1.0, "W1"),
        line("L11", "ARCH.WINDOW", "pcs", "SOURCE_DERIVED", 1.0, "W2"),
        line("L12", "FIN.CEILING", "m2", "ODD_STATE", 9.0, "R1:ceiling"),
        line("L13", "ARCH.SPACE", "m2", "MEASURED", 30.0, "R1"),
    ]


def release_report():
    return {"categories": {"CONDITIONAL": {"scenario_sets": [
        {"set_id": "REVIEW:X1", "by_scenario": {"DRY": {"FIN.FLOOR.PORCELAIN [m2]": 4.0},
                                                "WET": {"FIN.FLOOR.WET_TILE [m2]": 4.0}}},
        {"set_id": "DOOR:X2", "by_scenario": {"A": {"doors": 1}}}]}}}


def rec(rid, unit, qty, kind="COVER_TOTAL"):
    return {"id": rid, "unit": unit, "qty": qty, "row_kind": kind, "trade": "FREELANCER_TRADE"}


def normalised():
    return {"records": [rec("R-FOOT", "m3", 20.0), rec("R-SLAB", "m3", 8.0), rec("R-BEAM", "م3", 6.0),
                        rec("R-WALL", None, 50.0), rec("R-FLR", "م2", 35.0), rec("R-WIN", "m2", 12.0),
                        rec("R-CEIL", "m2", 9.0), rec("R-DET", "m2", 1.0, kind="DETAIL")]}


def key_map():
    return {"reference_row_kinds": ["COVER_TOTAL"], "keys": [
        {"key": "FOOT", "trade": "CONCRETE", "reference_id": "R-FOOT", "item_codes": ["STR.CONC.FOOTING", "STR.CONC.STRAP"]},
        {"key": "SLAB", "trade": "CONCRETE", "reference_id": "R-SLAB", "item_codes": ["STR.CONC.SLAB"]},
        {"key": "BEAM", "trade": "CONCRETE", "reference_id": "R-BEAM", "item_codes": ["STR.CONC.BEAM"]},
        {"key": "WALL", "trade": "PAINT", "reference_id": "R-WALL", "item_codes": ["FIN.PAINT"],
         "reference_unit": "m2", "reference_unit_source": "label says m2"},
        {"key": "FLR", "trade": "FLOOR_AREA", "reference_id": "R-FLR", "item_codes": ["FIN.FLOOR.PORCELAIN"],
         "conditional_items": ["FIN.FLOOR.PORCELAIN [m2]"]},
        {"key": "WIN", "trade": "WINDOWS", "reference_id": "R-WIN", "item_codes": ["ARCH.WINDOW"]},
        {"key": "CEIL", "trade": "CEILING", "reference_id": "R-CEIL", "item_codes": ["FIN.CEILING"]}]}


def write_run(tmp_path, with_report=True):
    d = tmp_path / "run"
    d.mkdir()
    (d / "BOQ_LINES.json").write_text(json.dumps(lines()), encoding="utf-8")
    if with_report:
        (d / "BOQ_RELEASE_REPORT.json").write_text(json.dumps(release_report()), encoding="utf-8")
    return d


@pytest.fixture()
def result(tmp_path):
    return K.run(write_run(tmp_path), normalised(), key_map())


def by_key(res):
    return {ln["key"]: ln for ln in res["lines"]}


def bucket(res, trade, unit):
    return next(b for b in res["buckets"] if b["trade"] == trade and b["unit"] == unit)


def test_concrete_hand_values(result):
    b = bucket(result, "CONCRETE", "m3")
    assert b["reference_lines"] == 3 and b["covered"] == 3 and b["compared"] == 1 and b["held"] == 2
    assert b["wape"] == pytest.approx(0.125, abs=TOL)
    assert b["signed_error_ratio"] == pytest.approx(0.125, abs=TOL)
    assert b["duplicates"] == 1 and b["silent_omissions"] == 0 and b["false_positives"] == 0
    ln = by_key(result)
    assert ln["FOOT"]["engine_qty"] == pytest.approx(22.5, abs=TOL)
    assert ln["FOOT"]["duplicate_engine_ids"] == ["L3"]


def test_range_and_blocked_never_released(result):
    ln = by_key(result)
    assert ln["SLAB"]["outcome"] == "HELD" and ln["SLAB"]["engine_qty"] is None
    assert ln["BEAM"]["outcome"] == "HELD" and ln["BEAM"]["engine_qty"] is None   # the bounded 5.0 stays out


def test_paint_unit_from_map_exclusion_and_mm_refused(result):
    ln = by_key(result)["WALL"]
    assert ln["outcome"] == "COMPARED" and ln["unit"] == "m2"
    assert ln["engine_qty"] == pytest.approx(40.0, abs=TOL)
    assert ln["refused_engine_ids"] == ["L8"]                     # 4000 mm never converted to m2
    assert "L7" not in ln["engine_ids"]
    assert result["adapter"]["excluded_lines_by_key"] == {"WALL": 1}
    b = bucket(result, "PAINT", "m2")
    assert b["wape"] == pytest.approx(0.2, abs=TOL) and b["signed_error_ratio"] == pytest.approx(-0.2, abs=TOL)


def test_conditional_set_holds_the_floor(result):
    ln = by_key(result)["FLR"]
    assert ln["outcome"] == "HELD" and ln["engine_qty"] is None
    assert result["adapter"]["conditional_sets_by_key"] == {"FLR": 1}


def test_floor_compared_without_release_report(tmp_path):
    res = K.run(write_run(tmp_path, with_report=False), normalised(), key_map())
    ln = by_key(res)["FLR"]
    assert ln["outcome"] == "COMPARED" and ln["abs_error"] == pytest.approx(5.0, abs=TOL)
    assert res["adapter"]["release_report_present"] is False


def test_windows_count_refused_against_area(result):
    ln = by_key(result)["WIN"]
    assert ln["outcome"] == "UNIT_MISMATCH" and sorted(ln["refused_engine_ids"]) == ["L10", "L11"]
    assert bucket(result, "WINDOWS", "m2")["coverage"] == 0.0


def test_unknown_state_is_held(result):
    assert by_key(result)["CEIL"]["outcome"] == "HELD"


def test_unmapped_is_listed_not_false_positive(result):
    assert result["false_positives"] == []
    assert result["adapter"]["unmapped_by_item"] == [{"item_code": "ARCH.SPACE", "unit": "m2", "lines": 1}]
    assert [u["engine_id"] for u in result["unmapped_engine_rows"]] == ["L13"]


def test_key_map_errors():
    km = key_map()
    km["keys"][1]["item_codes"].append("STR.CONC.FOOTING")
    with pytest.raises(ValueError, match="answers two keys"):
        K.load_key_map(km)
    km = key_map()
    km["keys"][1]["reference_id"] = "R-FOOT"
    with pytest.raises(ValueError, match="used by two keys"):
        K.load_key_map(km)
    km = key_map()
    del km["keys"][3]["reference_unit_source"]
    with pytest.raises(ValueError, match="needs its source"):
        K.reference_rows(normalised(), km)
    km = key_map()
    km["keys"][0]["reference_id"] = "R-DET"
    with pytest.raises(ValueError, match="DETAIL"):
        K.reference_rows(normalised(), km)
    km = key_map()
    km["keys"][0]["reference_id"] = "R-NONE"
    with pytest.raises(ValueError, match="not found"):
        K.reference_rows(normalised(), km)


def test_reference_unit_kept_when_record_has_one():
    km = key_map()
    km["keys"][0]["reference_unit"] = "m2"
    km["keys"][0]["reference_unit_source"] = "ignored: the record has its own unit"
    rows = {r["key"]: r for r in K.reference_rows(normalised(), km)}
    assert rows["FOOT"]["unit"] == "m3"


def test_cli_writes_only_out(tmp_path):
    run_dir = write_run(tmp_path)
    ref = tmp_path / "ref.json"
    km = tmp_path / "km.json"
    ref.write_text(json.dumps(normalised()), encoding="utf-8")
    km.write_text(json.dumps(key_map()), encoding="utf-8")
    out, md = tmp_path / "o.json", tmp_path / "o.md"
    p = subprocess.run([sys.executable, "-I", str(ROOT / "tools" / "alsenan_keymap.py"), "--run", str(run_dir),
                        "--reference", str(ref), "--key-map", str(km), "--out", str(out), "--markdown", str(md)],
                       capture_output=True, text=True, cwd=tmp_path)
    assert p.returncode == 0, p.stderr
    assert "| CONCRETE | m3 | 3 |" in md.read_text(encoding="utf-8")
    assert json.loads(out.read_text(encoding="utf-8"))["adapter"]["boq_lines"] == 13


def test_committed_key_map_matches_committed_reference():
    km = json.loads((ROOT / "tests/alsenan/T001B_KEY_MAP.json").read_text(encoding="utf-8"))
    ref = json.loads((ROOT / "tests/alsenan/registers_b1/BENCHMARK_NORMALISED.json").read_text(encoding="utf-8"))
    rows = K.reference_rows(ref, km)
    assert len(rows) == len(km["keys"]) == 13
    assert all(r["unit"] for r in rows)
    assert {r["trade"] for r in rows} == {"CONCRETE", "PLASTER", "PAINT", "FLOOR_AREA", "DOORS", "WINDOWS"}
