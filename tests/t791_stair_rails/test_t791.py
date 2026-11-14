"""T-791 r2: stair rails, guards and stair-hall skirting fix rows. Synthetic villa (not Alsenan), hand-calculated.

Villa S (synthetic): dog-leg stair, flight 8 goings x 0.28 / risers 0.17; quarter-round flight on a 2.000 m band,
10 goings x 9.0 deg, risers 0.16; a GF well band 3.000 m (centreline) of which a 4-going lobby flight (4 x 0.28 = 1.120)
already carries a rail; hall skirting run 9.000 m with children 3.000 + 2.500 + 1.200.
"""
import hashlib, importlib.util, json, math, pathlib
import pytest

_D = pathlib.Path(__file__).resolve().parents[2] / "research/agents_t791"


def _load():
    s = importlib.util.spec_from_file_location("t791_fill", _D / "t791_fill.py")
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


F = _load()


def _line(eid="E1", cls="HELD", net=None, code="FIN.RAILING"):
    return dict(line_id="L-x", item_code=code, unit="lm", element_id=eid, **{"class": cls}, measured_net=net,
                held_low=None, held_high=None)


EVIDENCE = "section B-B draws an open guard standing on the slab with no upstand; plan has two thin bands, no wall line"


# ---- normal: hand calculations --------------------------------------------------------------------------------------
def test_flight_rail_is_the_pitch_hypotenuse():
    # plan 8 x 0.28 = 2.240, rise 8 x 0.17 = 1.360 -> sqrt(5.0176 + 1.8496) = sqrt(6.8672) = 2.620534
    assert F.rail_sloped(8 * 0.28, 8 * 0.17) == pytest.approx(2.620534, abs=1e-6)


def test_curved_flight_plan_on_band_centreline_then_pitch():
    plan = F.arc_plan(2.000, 9.0, 10)                     # 2.000 x pi / 2 = 3.141593
    assert plan == pytest.approx(3.141593, abs=1e-6)
    assert F.rail_sloped(plan, 10 * 0.16) == pytest.approx(math.sqrt(9.869604 + 2.56), abs=1e-5)   # 3.525706


def test_level_guard_beyond_the_lobby_flight_with_its_well_end_turn():
    # 3.000 - 1.120 = 1.880 + across 0.150 + leg 0.025 = 2.055
    assert F.level_run(3.000, 4 * 0.28, 0.150, 0.025) == pytest.approx(2.055, abs=1e-9)


def test_parent_skirting_remainder():
    assert F.skirting_remainder(9.000, (3.000, 2.500, 1.200)) == pytest.approx(2.300, abs=1e-9)


def test_split_band_with_open_section_is_a_rail_and_carries_no_skirting():
    role = F.band_role(on_cut_wall_layer=False, inner_gap_lines=True, section="open_guard")
    assert role == F.RAIL
    assert F.settle_rail_or_skirting(role, 2.055, 2.200) == (2.055, F.NA)


def test_rows_released_and_not_applicable():
    r = F.make_row(_line(), 2.055, "DRAWING-READ", "level guard")
    assert r["after"] == {"class": "RELEASED", "net": 2.055}
    n = F.make_row(_line("E2", code="FIN.SKIRTING"), F.NA, F.NA, EVIDENCE)
    assert n["after"]["class"] == "EXCLUDED" and n["after"]["net"] is None


def test_mirror_and_rotation_do_not_change_lengths():
    # a mirrored / rotated band gives the same centreline lengths (absolute differences); the function sees lengths only
    a = F.level_run(abs(-793.0 - (-796.0)), 1.120, abs(10.15 - 10.0), 0.025)
    b = F.level_run(abs(796.0 - 793.0), 1.120, abs(10.0 - 10.15), 0.025)
    assert a == pytest.approx(b) == pytest.approx(2.055)


# ---- adverse --------------------------------------------------------------------------------------------------------
def test_adverse_closed_double_outline_on_rail_layer_that_is_a_divider_wall():
    # drawn like a rail band (thin layer, inner lines) but the section shows a solid body to the floor: WALL, skirting
    role = F.band_role(on_cut_wall_layer=False, inner_gap_lines=True, section="solid")
    assert role == F.WALL
    assert F.settle_rail_or_skirting(role, 2.055, 2.200) == (F.NA, 2.200)


def test_adverse_unresolved_band_never_carries_both():
    role = F.band_role(on_cut_wall_layer=False, inner_gap_lines=False, section=None)
    assert role == F.UNRESOLVED
    with pytest.raises(F.Refused):
        F.settle_rail_or_skirting(role, 2.055, 2.200)
    assert F.band_role(True, False, None) == F.WALL


def test_adverse_missing_pitch_stays_held_never_zero():
    with pytest.raises(F.Refused):
        F.rail_sloped(2.240, None)
    with pytest.raises(F.Refused):
        F.make_row(_line(), None, "ESTIMATE", "pitch unknown")
    with pytest.raises(F.Refused):
        F.make_row(_line(), 0.0, "ESTIMATE", "zero")


def test_adverse_units_mm_refused():
    with pytest.raises(F.Refused):
        F.rail_sloped(2240.0, 1360.0)
    with pytest.raises(F.Refused):
        F.level_run(3000.0, 1120.0, 150.0, 25.0)


def test_adverse_na_without_evidence_refused():
    with pytest.raises(F.Refused):
        F.make_row(_line(), F.NA, F.NA, "")
    with pytest.raises(F.Refused):
        F.make_row(_line(), 1.0, F.NA, EVIDENCE)              # NA carrying a value


def test_adverse_non_held_or_valued_line_refused():
    with pytest.raises(F.Refused):
        F.make_row(_line(cls="RELEASED", net=3.0), 2.0, "ESTIMATE", "x")
    with pytest.raises(F.Refused):
        F.make_row(_line(cls="HELD", net=1.0), 2.0, "ESTIMATE", "x")


def test_adverse_unknown_label_and_negative_remainder_refused():
    with pytest.raises(F.Refused):
        F.make_row(_line(), 1.0, "GUESS", "x")
    with pytest.raises(F.Refused):
        F.skirting_remainder(5.0, (3.0, 2.5))


def test_adverse_wrong_index_sha_refused(tmp_path):
    p = tmp_path / "idx.json"
    p.write_bytes(json.dumps({"lines": []}).encode())
    raw = p.read_bytes()
    assert F.check_index(raw, hashlib.sha256(raw).hexdigest()[:16]) == []
    with pytest.raises(F.Refused):
        F.check_index(raw, "0000000000000000")


# ---- committed output (Alsenan fix rows): mutual exclusivity and no zero -------------------------------------------
def test_committed_rows_rail_and_divider_skirting_exclusive():
    doc = json.loads((_D / "out" / "FIX_ROWS.json").read_text())
    rows = {r["element_id"]: r for r in doc["rows_detail"]}
    assert len(rows) == 14 and doc["left_after"] == 0
    assert rows["RAIL:ST-01b:GF east-lane band beyond D1"]["after"]["net"] == pytest.approx(2.050)
    assert rows["SKIRT-T443:GF-ST-HALL:DIVIDER-BAND"]["after"]["class"] == "EXCLUDED"
    for r in rows.values():
        a = r["after"]
        assert (a["class"] == "EXCLUDED" and a["net"] is None) or (a["class"] == "RELEASED" and a["net"] > 0)
