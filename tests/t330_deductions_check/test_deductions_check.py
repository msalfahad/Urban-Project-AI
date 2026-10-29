"""T-330: the canonical deductions check and the guarded export (tools/t330_deductions_check.py).

Hand calculation (synthetic villa VG-330, not the development villa; one bedroom 4.20 x 3.60 m, wall height 3.10 m):
  wall faces            2 x (4.20 + 3.60) = 15.60 m perimeter; 15.60 x 3.10 = 48.360 m2 GROSS
  W1 window             1.50 x 1.20 = 1.800 m2
  D1 door               0.90 x 2.10 = 1.890 m2
  plaster NET           48.360 - (1.800 + 1.890) = 48.360 - 3.690 = 44.670 m2
  skirting              15.60 lm - D1 width 0.90 lm = 14.700 lm
  ceiling (no opening)  4.20 x 3.60 = 15.120 m2 gross = net, no deduction needed
  bulkhead return       gross 2.000 m2, + addition 0.360 m2 (a 0.30 x 1.20 soffit) = 2.360 m2 net
The ADVERSE copies keep the same numbers and break one thing each: the list emptied (a consumer reading
gross - deductions would get 48.360, i.e. +3.690 m2 = +8.26 % over the net 44.670), deductions above the gross, a lm
deduction on an m2 line, a deduction with no id, a range instead of a number, a negative deduction, a list that is
0.250 m2 short.
"""
from __future__ import annotations

import json

import pytest

from engine.source import boq_line as BL
from tools import t330_deductions_check as C

PID, REV = "SYNTH-VILLA-VG330", "d" * 64
CVER = "ARCH_TAKEOFF_V3.0.TEST"
W1 = {"opening": "W1", "area": 1.80, "unit": "m2", "basis": "1.50 x 1.20"}
D1 = {"opening": "D1", "area": 1.89, "unit": "m2", "basis": "0.90 x 2.10"}


def ln(code, eid, *, gross, net, unit="m2", deductions=(), additions=(), ev="MEASURED", inputs=None, **kw):
    return BL.make_line(project_id=PID, revision_set_sha256=REV, item_code=code, unit=unit, evidence_state=ev,
                        measured_net=net, element_id=eid, gross=gross, deductions=deductions, additions=additions,
                        formula="perimeter x height - openings", rule_id="R-SYN", rule_version="1",
                        floor=kw.pop("floor", "GF"), room_id="GF-BED1", inputs=inputs or {"perimeter": 15.6, "h": 3.1},
                        **kw)


def plaster_ok():
    return ln("FIN.PLASTER", "GF-BED1-WALLS", gross=48.36, net=44.67, deductions=[W1, D1])


def villa():
    return [plaster_ok(),
            ln("FIN.SKIRTING", "GF-BED1-SK", unit="lm", gross=15.6, net=14.7,
               deductions=[{"opening": "D1", "qty": 0.9, "unit": "lm"}]),
            ln("FIN.CEILING", "GF-BED1-CEIL", gross=15.12, net=15.12),
            ln("FIN.CEILING", "GF-BED1-BULK", gross=2.0, net=2.36,
               additions=[{"element_id": "BULK-1-SOFFIT", "area": 0.36, "unit": "m2"}])]


def one(line):
    return C.check_line(line)


# ---- normal ----------------------------------------------------------------------------------------------------------

def test_normal_listed_deductions_that_sum_pass():
    for line in villa():
        r = one(line)
        assert r["category"] == C.OK, (line["location"]["element_id"], r)
    r = one(plaster_ok())
    assert (r["gross"], r["deductions_sum"], r["measured_net"], r["residual"]) == (48.36, 3.69, 44.67, 0.0)


def test_normal_report_counts_every_line_and_no_finding():
    rep = C.check_lines(villa())
    assert rep["lines"] == 4 and rep["categories"] == {"OK": 4}
    assert rep["flagged"] == rep["refused"] == 0 and rep["findings"] == []
    assert C.exit_code(rep) == 0


def test_normal_plain_number_deductions_without_unit_are_in_the_line_unit():
    # a bare number has no id: it is not canonical (who was deducted is unknown) -> MISSING_ID, never OK
    r = one(ln("FIN.PLASTER", "P", gross=48.36, net=44.67, deductions=[1.80, 1.89]))
    assert r["category"] == "MISSING_ID" and r["severity"] == C.FLAG


# ---- adverse ---------------------------------------------------------------------------------------------------------

def test_adverse_empty_list_with_gross_above_net_is_flagged():
    r = one(ln("FIN.PLASTER", "P", gross=48.36, net=44.67))
    assert (r["category"], r["severity"]) == ("EMPTY_DEDUCTIONS", C.FLAG)
    assert r["gross_minus_net"] == 3.69                      # what a consumer would over-read as net, m2
    assert round(r["gross_minus_net"] / r["measured_net"] * 100, 2) == 8.26


def test_adverse_deductions_above_gross_refused():
    r = one(ln("FIN.PLASTER", "P", gross=3.0, net=0.0, deductions=[W1, D1]))   # 3.690 > 3.000
    assert (r["category"], r["severity"]) == ("EXCEEDS_GROSS", C.REFUSED)


def test_adverse_mixed_units_refused():
    r = one(ln("FIN.PLASTER", "P", gross=48.36, net=47.46, deductions=[{"opening": "D1", "qty": 0.9, "unit": "lm"}]))
    assert (r["category"], r["severity"]) == ("MIXED_UNITS", C.REFUSED)
    # also on an addition
    r = one(ln("FIN.CEILING", "B", gross=2.0, net=2.36, additions=[{"element_id": "S", "area": 0.36, "unit": "lm"}]))
    assert r["category"] == "MIXED_UNITS"


def test_adverse_negative_deduction_refused():
    r = one(ln("FIN.PLASTER", "P", gross=48.36, net=50.16, deductions=[{"opening": "W1", "area": -1.80}]))
    assert (r["category"], r["severity"]) == ("NEGATIVE_DEDUCTION", C.REFUSED)


def test_adverse_missing_id_and_non_numeric_flagged():
    r = one(ln("FIN.PLASTER", "P", gross=48.36, net=44.67, deductions=[W1, {"area": 1.89}]))
    assert r["category"] == "MISSING_ID"
    r = one(ln("FIN.PLASTER", "P", gross=48.36, net=44.67, deductions=[W1, {"opening": "D1", "area": [1.7, 1.9]}]))
    assert r["category"] == "NON_NUMERIC"


def test_adverse_list_short_of_the_gap_is_not_summing():
    short = {"opening": "D1", "area": 1.64}                   # 0.250 m2 short
    r = one(ln("FIN.PLASTER", "P", gross=48.36, net=44.67, deductions=[W1, short]))
    assert r["category"] == "NOT_SUMMING" and r["residual"] == 0.25


def test_adverse_net_above_gross_without_additions_is_flagged():
    r = one(ln("FIN.CEILING", "B", gross=2.0, net=2.36))
    assert r["category"] == "EMPTY_DEDUCTIONS" and r["gross_minus_net"] == -0.36


def test_tolerance_is_the_export_tolerance():
    assert C.TOL == 0.0005
    assert one(ln("FIN.PLASTER", "P", gross=48.36, net=44.6704, deductions=[W1, D1]))["category"] == C.OK
    assert one(ln("FIN.PLASTER", "P", gross=48.36, net=44.6710, deductions=[W1, D1]))["category"] == "NOT_SUMMING"


def test_held_line_is_not_applicable_never_ok():
    held = BL.make_line(project_id=PID, revision_set_sha256=REV, item_code="FIN.PLASTER", unit="m2",
                        evidence_state="BLOCKED_RFI", element_id="H", gross=48.36, formula="held",
                        rule_id="R-SYN", rule_version="1", rfi={"question": "wall height not printed"})
    r = one(held)
    assert r["category"] == C.NOT_APPLICABLE and r["severity"] == ""
    rep = C.check_lines([held])
    assert rep["families"][0]["ok"] == 0 and rep["families"][0]["not_applicable"] == 1


def test_shadow_list_is_reported_but_never_passes_the_line():
    om = {"owner_manual_method": {"gross": 48.36, "deductions": [{"opening": "W1", "m2": 1.8},
                                                                 {"opening": "D1", "m2": 1.89}]}}
    r = one(ln("FIN.PLASTER", "P", gross=48.36, net=44.67, inputs=om))
    assert r["category"] == "EMPTY_DEDUCTIONS"
    assert (r["shadow_path"], r["shadow_n"], r["shadow_sum"], r["shadow_open"], r["shadow_explains_gap"]) == \
        ("calculation.inputs.owner_manual_method.deductions", 2, 3.69, 0, True)
    om["owner_manual_method"]["deductions"][1] = {"opening": "D1", "m2": [1.7, 1.9]}      # a held range
    r = one(ln("FIN.PLASTER", "P", gross=48.36, net=44.67, inputs=om))
    assert r["shadow_open"] == 1 and r["shadow_explains_gap"] is False


def test_unit_named_key_is_a_quantity_in_that_unit_but_the_export_cannot_read_it():
    # the shape the V3.0.x finish lines carry: {"m2": value, "what": text}; arithmetic sums (48.360 - 3.690 = 44.670)
    # but no opening id and boq_export_v1._deductions reads no total from it (BOQ.csv: deductions_n 2, total blank)
    ded = [{"m2": 1.80, "what": "window"}, {"m2": 1.89, "what": "door"}]
    r = one(ln("FIN.PLASTER", "P", gross=48.36, net=44.67, deductions=ded))
    assert r["residual"] == 0.0 and r["deductions_sum"] == 3.69 and r["export_deductions_total"] is None
    assert (r["category"], r["issues"]) == ("EXPORT_TOTAL_BLANK", "EXPORT_TOTAL_BLANK MISSING_ID")
    # adverse: an lm-keyed deduction on an m2 line is another unit
    r = one(ln("FIN.PLASTER", "P", gross=48.36, net=47.46, deductions=[{"lm": 0.9, "what": "door width"}]))
    assert r["category"] == "MIXED_UNITS" and r["severity"] == C.REFUSED
    # adverse: a unit-keyed range is not one number
    r = one(ln("FIN.PLASTER", "P", gross=48.36, net=44.67, deductions=[{"opening": "W1", "m2": [1.7, 1.9]}]))
    assert r["category"] == "NON_NUMERIC"


def test_adverse_deductions_listed_but_gross_already_net():
    # gross written equal to the net while the list still carries 3.690 m2: a consumer computing gross - deductions
    # gets 44.670 - 3.690 = 40.980 m2, i.e. 3.690 m2 (8.26 %) UNDER the net
    r = one(ln("FIN.FLOOR.PORCELAIN", "F", gross=44.67, net=44.67, deductions=[W1, D1]))
    assert r["category"] == "NOT_SUMMING" and r["residual"] == -3.69 and r["gross_minus_net"] == 0.0


def test_duplicate_line_ids_refused():
    with pytest.raises(C.DeductionsError):
        C.check_lines([plaster_ok(), plaster_ok()])


def test_family_totals_per_unit_never_mixed():
    bad = [ln("FIN.PLASTER", "P1", gross=48.36, net=44.67),
           ln("FIN.PLASTER", "P2", gross=30.0, net=28.11, floor="1F"),
           ln("FIN.SKIRTING", "S1", unit="lm", gross=15.6, net=14.7), plaster_ok()]
    rep = C.check_lines(bad)
    fam = {(f["item_code"], f["unit"]): f for f in rep["families"]}
    p, s = fam[("FIN.PLASTER", "m2")], fam[("FIN.SKIRTING", "lm")]
    assert (p["lines"], p["ok"], p["flagged"], p["by_category"]) == (3, 1, 2, {"EMPTY_DEDUCTIONS": 2})
    assert (p["flagged_gross"], p["flagged_net"], p["flagged_gross_minus_net"]) == (78.36, 72.78, 5.58)
    assert (s["flagged"], s["flagged_gross_minus_net"]) == (1, 0.9)
    assert C.exit_code(rep) == 1
    # sorted by (trade, item code, floor, element id): FLOOR_FINISH before PLASTER, 1F before GF; producer order ignored
    assert [r["element_id"] for r in rep["findings"]] == ["S1", "P2", "P1"]
    assert C.check_lines(list(reversed(bad)))["findings"] == rep["findings"]
    rep2 = C.check_lines(bad + [ln("FIN.PLASTER", "X", gross=3.0, net=0.0, deductions=[W1, D1])])
    assert C.exit_code(rep2) == 2


# ---- command line and the guarded export -----------------------------------------------------------------------------

def _write(tmp_path, lines, name="lines.json"):
    p = tmp_path / name
    p.write_text(BL.dumps(lines), encoding="utf-8")
    return p


def test_cli_check_writes_report_and_csv(tmp_path):
    p = _write(tmp_path, villa() + [ln("FIN.PLASTER", "P9", gross=48.36, net=44.67)])
    j, c = tmp_path / "r.json", tmp_path / "r.csv"
    assert C.main(["check", "--lines", str(p), "--json", str(j), "--csv", str(c)]) == 1
    rep = json.loads(j.read_text(encoding="utf-8"))
    assert rep["schema"] == C.SCHEMA and rep["flagged"] == 1 and rep["findings"][0]["element_id"] == "P9"
    rows = c.read_text(encoding="utf-8").splitlines()
    assert rows[0].split(",")[:7] == ["line_id", "trade", "item_code", "floor", "element_id", "unit", "category"]
    assert len(rows) == 2 and ",EMPTY_DEDUCTIONS,FLAG," in rows[1]
    assert C.main(["check", "--lines", str(_write(tmp_path, villa(), "ok.json"))]) == 0


def test_guarded_export_refuses_and_writes_nothing(tmp_path, capsys):
    p = _write(tmp_path, villa() + [ln("FIN.PLASTER", "P9", gross=48.36, net=44.67)])
    out = tmp_path / "export"
    assert C.main(["export", "--lines", str(p), "--candidate-version", CVER, "--out", str(out),
                   "--code-commit", "abc1234"]) == 2
    assert not out.exists()
    assert "EMPTY_DEDUCTIONS" in capsys.readouterr().err


def test_guarded_export_delegates_unchanged_when_clean(tmp_path):
    from tools import boq_export_v1 as X
    p = _write(tmp_path, villa())
    a, b = tmp_path / "guarded", tmp_path / "plain"
    common = ["--lines", str(p), "--candidate-version", CVER, "--code-commit", "abc1234"]
    assert C.main(["export", *common, "--out", str(a)]) == 0
    assert X.main([*common, "--out", str(b)]) == 0
    for name in ("BOQ.csv", "BOQ_ENGINE_UNITS.csv"):
        assert (a / name).read_bytes() == (b / name).read_bytes()
    rows = X.read_csv(a / "BOQ.csv")
    pl = [r for r in rows if r["element_id"] == "GF-BED1-WALLS"][0]
    assert (pl["gross"], pl["deductions_n"], pl["deductions_total"], pl["net"]) == \
        ("48.360000", "2", "3.690000", "44.670000")


def test_usage_without_subcommand():
    assert C.main([]) == 64
