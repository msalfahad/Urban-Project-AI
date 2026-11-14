"""R-T796-1 (MAIN FILL overlay precedence) and R-T796-2 (disposal balance) on a synthetic villa (not Alsenan)."""
import copy, importlib.util, pathlib
import pytest

_D = pathlib.Path(__file__).resolve().parents[2] / "research/agents_t796"


def _load(name):
    s = importlib.util.spec_from_file_location(name, _D / f"{name}.py")
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


O = _load("overlay_precedence")
B = _load("disposal_balance_t796")


def _l(lid, cls, net=None, lo=None, hi=None, code="X", fb=None, eid="E"):
    d = dict(line_id=lid, item_code=code, unit="m3", element_id=eid, **{"class": cls}, measured_net=net, held_low=lo, held_high=hi)
    if fb:
        d["fill_basis"] = fb
    return d


def _r(lid, before, after):
    return dict(line_id=lid, item_code="X", unit="m3", set="S", label="DEFAULT", basis="b", before=before, after=after)


BLANK = {"class": "HELD", "net": None, "low": None, "high": None}


def test_normal_overlay_over_blank_applies():
    lines = [_l("a", "HELD")]
    log = O.apply_overlay(lines, {"rows": [_r("a", BLANK, {"class": "RELEASED", "net": 4.2})]})
    assert log[0]["action"] == O.APPLY
    assert lines[0]["class"] == "RELEASED" and lines[0]["measured_net"] == 4.2 and lines[0]["fill_label"] == "DEFAULT"


def test_pending_released_line_at_before_state_applies():
    # owner rule changed a RELEASED value; nothing newer wired it: row applies
    lines = [_l("t", "RELEASED", 30.0)]
    log = O.apply_overlay(lines, {"rows": [_r("t", {"class": "RELEASED", "net": 30.0}, {"class": "RELEASED", "net": 28.6})]})
    assert log[0]["action"] == O.APPLY and lines[0]["measured_net"] == 28.6


def test_adverse_overlay_over_newer_released_line_is_skipped_and_logged():
    # the disposal case: row written on a blank line (range 105.6 .. 115.5); a later fix row wired 10.48 RELEASED
    lines = [_l("d", "RELEASED", 10.476796, fb="T-764 9.0486 + changes")]
    orig = copy.deepcopy(lines)
    log = O.apply_overlay(lines, {"rows": [_r("d", BLANK, {"class": "HELD", "low": 105.632, "high": 115.546})]})
    assert log[0]["action"] == O.SKIP_NEWER and "T-764" in log[0]["reason"]
    assert lines == orig                                   # index value stands, byte-identical
    assert log[0]["index"] == ["RELEASED", 10.476796, None, None]


def test_adverse_line_moved_without_fill_basis_is_skipped():
    lines = [_l("m", "HELD", lo=1.0, hi=2.0)]               # row was written when the line was blank
    orig = copy.deepcopy(lines)
    log = O.apply_overlay(lines, {"rows": [_r("m", BLANK, {"class": "RELEASED", "net": 9.0})]})
    assert log[0]["action"] == O.SKIP_CHANGED and lines == orig


def test_already_wired_is_noop_and_absent_line_logged():
    lines = [_l("w", "RELEASED", 5.25, fb="wired")]
    log = O.apply_overlay(lines, {"rows": [_r("w", BLANK, {"class": "RELEASED", "net": 5.25}),
                                           _r("gone", BLANK, {"class": "RELEASED", "net": 1.0})]})
    assert [e["action"] for e in log] == [O.ALREADY, O.SKIP_ABSENT]
    assert "fill_label" not in lines[0]
    assert O.summary(log) == {O.ALREADY: 1, O.SKIP_ABSENT: 1}


def test_held_overlay_keeps_range_never_zero():
    lines = [_l("h", "HELD")]
    O.apply_overlay(lines, {"rows": [_r("h", BLANK, {"class": "HELD", "low": 2.0, "high": 3.0})]})
    assert lines[0]["class"] == "HELD" and (lines[0]["held_low"], lines[0]["held_high"]) == (2.0, 3.0)
    assert lines[0]["measured_net"] is None


# R-T796-2 synthetic villa: pits 60.0 + trench 20.0 = E 80.0; Z1 backfill 30.0; Z2 placed fill 42.0 (EG -> slab soffit)
def _villa():
    return [_l("e1", "RELEASED", 60.0, code="STR.EARTH.EXCAVATION", eid="EW:Z1-PITS"),
            _l("e2", "RELEASED", 20.0, code="STR.EARTH.EXCAVATION", eid="EW:Z1-TRENCH"),
            _l("b1", "RELEASED", 30.0, code="STR.EARTH.BACKFILL", eid="EW:B1-03:Z1-PITS"),
            _l("b2", "RELEASED", 42.0, code="STR.EARTH.BACKFILL", eid="EW:B1-03:Z2")]


def test_disposal_normal_hand_calc():
    E, Z1, Z2, held = B.split_b1(_villa())
    assert (E, Z1, Z2, held) == (80.0, 30.0, 42.0, [])
    r = B.balance(E, Z1, Z2)
    assert r["disposal_in_situ"] == pytest.approx(8.0)       # 80 - (30 + 42)
    assert r["import_compacted"] == 0.0 and r["k_break"] == pytest.approx(80 / 72) and r["label"] == "ESTIMATE"
    # stale snapshot error: subtracting only Z1 (Z2 still blank) overstates the surplus by Z2
    assert B.balance(E, Z1, 0.0)["disposal_in_situ"] - r["disposal_in_situ"] == pytest.approx(42.0)


def test_disposal_adverse_factor_flips_to_import_and_imported_z2():
    r = B.balance(80.0, 30.0, 42.0, k=1.2)                   # needs 86.4 in situ > 80
    assert r["disposal_in_situ"] == 0.0 and r["import_compacted"] == pytest.approx(72 - 80 / 1.2)
    r2 = B.balance(80.0, 30.0, 42.0, z2_from_excavation=False)
    assert r2["disposal_in_situ"] == pytest.approx(50.0) and r2["import_compacted"] == pytest.approx(42.0)
    with pytest.raises(ValueError):
        B.balance(80.0, 30.0, 42.0, k=0)


def test_disposal_held_line_never_summed_as_zero():
    v = _villa(); v[1] = _l("e2", "HELD", lo=18.0, hi=22.0, code="STR.EARTH.EXCAVATION", eid="EW:Z1-TRENCH")
    E, Z1, Z2, held = B.split_b1(v)
    assert E == 60.0 and held == ["e2"]
