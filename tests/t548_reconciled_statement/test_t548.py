"""T-548: reconciled-quantities statement builder (research/agents_t548, R-T548-1).
Synthetic villa "S548" (not the training villa) with hand totals, adverse cases, then the merged T-541 / T-534
reports (committed research outputs only; no private input)."""
from __future__ import annotations

import copy
import json
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t548"))
import adapters as A  # noqa: E402
import statement as S  # noqa: E402

# ---- villa "S548", by hand.
# Report X, wall tiles (m2), freelancer row 100.00. Engine valued: A 40.00 + B 50.00 = 90.00; held line H (engine
# bound 2.00 .. 6.00). Components: H face 5.00 (HELD), openings not deducted by him 3.00 (RULE_DIFFERENCE), a missed
# engine face 1.50 (ENGINE_WRONG, fix T-999), residual 0.50 (UNRESOLVED): 5 + 3 + 1.5 + 0.5 = 10.00 = 100 - 90.
# Report Y, wall tiles (m2), freelancer row 20.00; engine C 22.00; the engine's extra return 2.00 is drawn (ENGINE_RIGHT,
# -2.00). Trade total m2: reference 120.00, engine 112.00, difference 8.00 = -2 + 1.5 + 3 + 5 + 0.5;
# bounded 112 + 2 = 114.00 .. 112 + 6 = 118.00.
# Report Z, tile edge trim (lm), freelancer 30.00, engine D 28.00, residual 2.00 UNRESOLVED: its own total.


def sec_x():
    return {"section_id": "X", "report": "S548-X", "trade": "wall tiles", "unit": "m2",
            "reference": {"kind": "FREELANCER", "total": "100.00", "basis": "S548 tile sheet row 4"},
            "engine": {"valued_total": "90.00",
                       "valued_lines": [{"line_id": "A", "qty": "40.00"}, {"line_id": "B", "qty": "50.00"}],
                       "held_lines": [{"line_id": "H", "low": "2.00", "high": "6.00"}], "excluded_lines": []},
            "rows": [
                {"name": "H face", "delta": "5.00", "class": "HELD", "engine_status": "HELD", "held_line_ids": ["H"]},
                {"name": "openings", "delta": "3.00", "class": "RULE_DIFFERENCE", "engine_status": "NONE"},
                {"name": "missed face", "delta": "1.50", "class": "ENGINE_WRONG", "engine_status": "NONE",
                 "fix_row": "T-999"},
                {"name": "RESIDUAL", "delta": "0.50", "class": "UNRESOLVED", "engine_status": "NONE"}]}


def sec_y():
    return {"section_id": "Y", "report": "S548-Y", "trade": "wall tiles", "unit": "m2",
            "reference": {"kind": "FREELANCER", "total": "20.00", "basis": "S548 tile sheet row 9"},
            "engine": {"valued_lines": [{"line_id": "C", "qty": "22.00"}], "held_lines": []},
            "rows": [{"name": "return", "delta": "-2.00", "class": "ENGINE_RIGHT", "engine_status": "VALUED"}]}


def sec_z():
    return {"section_id": "Z", "report": "S548-Z", "trade": "wall tiles", "unit": "lm",
            "reference": {"kind": "FREELANCER", "total": "30.00", "basis": "S548 trim row"},
            "engine": {"valued_lines": [{"line_id": "D", "qty": "28.00", "unit": "lm"}], "held_lines": []},
            "rows": [{"name": "RESIDUAL", "delta": "2.00", "unit": "lm", "class": "UNRESOLVED",
                      "engine_status": "NONE"}]}


def test_s548_hand_totals():
    st = S.build_statement([sec_x(), sec_y(), sec_z()])
    m2 = [t for t in st["totals"] if t["unit"] == "m2"][0]
    assert m2["freelancer_total"] == "120" and m2["engine_valued"] == "112" and m2["difference"] == "8"
    assert m2["engine_bounded"] == {"low_at_least": "114", "high": "118", "high_open": False}
    assert m2["held_count"] == 1
    assert m2["by_class"] == {"ENGINE_RIGHT": "-2", "ENGINE_WRONG": "1.5", "RULE_DIFFERENCE": "3", "HELD": "5",
                              "TOLERANCE": "0", "UNRESOLVED": "0.5"}
    lm = [t for t in st["totals"] if t["unit"] == "lm"][0]
    assert lm["difference"] == "2" and lm["by_class"]["UNRESOLVED"] == "2" and lm["sections"] == ["Z"]
    assert len(st["totals"]) == 2  # m2 and lm never in one total
    assert st["released_quantities_changed"] == 0
    assert "| wall tiles | m2 | freelancer row | 120 | 112 | AT_LEAST 114 .. 118 | 1 | 8 |" in S.to_markdown(st)


def test_open_high_when_a_held_line_has_no_bound():
    x = sec_x()
    x["engine"]["held_lines"][0]["high"] = None
    c = S.check_section(x)
    assert c["engine_bounded"] == {"low_at_least": "92", "high": None, "high_open": True}


def _refused(sec, match):
    with pytest.raises(S.StatementError, match=match):
        S.check_section(sec)


def test_adverse_m2_row_in_lm_section_refused():
    z = sec_z()
    z["rows"][0]["unit"] = "m2"
    _refused(z, "never enters a lm total")


def test_adverse_m2_and_lm_never_one_total():
    st = S.build_statement([sec_x(), sec_z()])
    a, b = st["totals"]
    with pytest.raises(S.StatementError, match="never in one total"):
        S.merge_totals(a, b)


def test_adverse_reference_kinds_never_one_total():
    y = sec_y()
    y["reference"]["kind"] = "OWNER_QUESTION_FIGURE"
    st = S.build_statement([sec_x(), y])
    assert len(st["totals"]) == 2
    assert [t for t in st["totals"] if t["reference_kind"] == "OWNER_QUESTION_FIGURE"][0]["freelancer_total"] is None
    with pytest.raises(S.StatementError, match="never in one total"):
        S.merge_totals(*st["totals"])


def test_adverse_held_counted_as_agreement_refused():
    x = sec_x()
    x["rows"][0]["class"] = "ENGINE_RIGHT"
    _refused(x, "HELD is never agreement")
    x = sec_x()  # HELD with zero difference, the rest moved to the residual
    x["rows"][0]["delta"] = "0"
    x["rows"][3]["delta"] = "5.50"
    _refused(x, "HELD counted as agreement")
    x = sec_x()
    x["rows"][0]["class"] = "AGREE"
    _refused(x, "refused")


def test_adverse_held_row_must_name_a_held_line():
    x = sec_x()
    x["rows"][0]["held_line_ids"] = []
    _refused(x, "names no held line")
    x = sec_x()
    x["rows"][0]["held_line_ids"] = ["A"]
    _refused(x, "VALUED")
    x = sec_x()
    x["rows"][0]["engine_status"] = "VALUED"
    _refused(x, "class HELD but engine status")


def test_adverse_table_does_not_close():
    x = sec_x()
    x["rows"][3]["delta"] = "0.49"
    _refused(x, "does not close")


def test_adverse_unknown_never_zero():
    x = sec_x()
    x["rows"][1]["delta"] = None
    _refused(x, "never 0")
    x = sec_x()
    x["engine"]["valued_lines"][0]["qty"] = None
    _refused(x, "never 0")
    x = sec_x()
    x["reference"]["total"] = None
    _refused(x, "never 0")


def test_adverse_stale_total_and_double_lines():
    x = sec_x()
    x["engine"]["valued_total"] = "91.00"
    _refused(x, "declared engine total")
    x = sec_x()
    x["engine"]["held_lines"][0]["line_id"] = "A"
    _refused(x, "both valued and held")


def test_adverse_units_and_labels():
    x = sec_x()
    x["unit"] = "m.l"
    _refused(x, "unit")
    x = sec_x()
    x["engine"]["valued_lines"][0]["unit"] = "lm"
    _refused(x, "unit")
    x = sec_x()
    x["rows"][2]["fix_row"] = None
    _refused(x, "fix row")
    x = sec_x()
    x["reference"]["kind"] = "ENGINE"
    _refused(x, "reference kind")
    x = sec_x()
    x["engine"]["held_lines"][0]["low"] = "7.00"
    _refused(x, "high < low")
    with pytest.raises(S.StatementError, match="twice"):
        S.build_statement([sec_x(), sec_x()])


# ---- merged reports (development villa): committed research outputs only.
def test_t541_membrane_and_upturn_pins():
    st = S.build_statement(A.t541_sections())
    mem = [c for c in st["sections"] if c["section_id"] == "T-541/membrane"][0]
    assert (mem["freelancer_total"], mem["engine_valued"], mem["difference"]) == ("285", "209.65844", "75.34156")
    assert mem["by_class"] == {"ENGINE_RIGHT": "-5.54644", "ENGINE_WRONG": "0", "RULE_DIFFERENCE": "45.992784",
                               "HELD": "34.390242", "TOLERANCE": "-0.018026", "UNRESOLVED": "0.523"}
    assert mem["engine_bounded"]["high_open"] and mem["held_count"] == 1
    up = [c for c in st["sections"] if c["section_id"] == "T-541/upturn"][0]
    assert (up["freelancer_total"], up["engine_valued"], up["difference"]) == ("194", "187.83416", "6.16584")
    assert up["by_class"]["UNRESOLVED"] == "11.893" and up["by_class"]["HELD"] == "28.3"
    assert len(st["totals"]) == 2  # m2 and lm apart


def test_t534_stair_bed_pins():
    (c,) = [S.check_section(x) for x in A.t534_sections()]
    assert c["freelancer_total"] is None and c["reference_kind"] == "OWNER_QUESTION_FIGURE"
    assert (c["reference_total"], c["engine_valued"], c["difference"]) == ("39.485", "35.4313", "4.0537")
    # T-534 s.3 by cause, negated: COUNT 3.00 + WIDTH 0.66 + HEIGHT 0.42 = 4.08 ENGINE_RIGHT; POLYGON 0.0006;
    # SCOPE out 14.905 = 10.28 held risers + 3.125 MS2-LD (HELD 13.405) + 1.500 MS1-LD (ENGINE_WRONG, T-502);
    # SCOPE in -14.9319 RULE_DIFFERENCE.
    assert c["by_class"] == {"ENGINE_RIGHT": "4.08", "ENGINE_WRONG": "1.5", "RULE_DIFFERENCE": "-14.9319",
                             "HELD": "13.405", "TOLERANCE": "0.0006", "UNRESOLVED": "0"}
    assert c["held_count"] == 20 and c["excluded_count"] == 3 and c["valued_count"] == 11
    assert c["engine_bounded"] == {"low_at_least": "35.4313", "high": None, "high_open": True}
    assert sum(Decimal(v) for v in c["by_class"].values()) == Decimal("4.0537")


def test_adapter_refuses_an_unknown_row(tmp_path):
    d = json.loads(A.T541_JSON.read_text(encoding="utf-8"))
    d["membrane"]["rows"].insert(0, {"name": "parapet copings", "qty": "1", "unit": "m2", "delta": "1",
                                     "cause": "RULE_DIFFERENCE", "source": "x", "note": ""})
    p = tmp_path / "t541.json"
    p.write_text(json.dumps(d), encoding="utf-8")
    with pytest.raises(A.AdapterError, match="not in the adapter table"):
        A.t541_sections(json_path=p)


def test_adapter_binds_lines_to_the_index():
    idx = A.load_index()
    secs = A.t534_sections()
    assert A.bind_to_index(secs[0], idx) == []
    bad = copy.deepcopy(secs[0])
    bad["engine"]["valued_lines"][0]["qty"] = "9.9999"
    with pytest.raises(A.AdapterError, match="in the index"):
        A.bind_to_index(bad, idx)
    t541 = A.t541_sections()
    # the five V3.0.58 pool-court lines are not in the V3.0.57 index: named, never dropped
    assert len(A.bind_to_index(t541[0], idx)) == 2 and len(A.bind_to_index(t541[1], idx)) == 3


def test_committed_output_reproduces():
    r = subprocess.run([sys.executable, "-I", str(ROOT / "research/agents_t548/t548_build.py"), "--check"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
