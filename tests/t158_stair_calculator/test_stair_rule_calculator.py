"""T-158: owner stair rule UP-STAIR-015 (URBAN_RULES 1.6.0) - calculator and check mode.

Expected values are the owner's acceptance table (docs/agents/OWNER_RULE_STAIRS_2026-10-21.md, checked by hand by the
main chat) and hand calculations written next to each case. Nothing here reads a drawing or writes a file."""

import decimal
import json
from decimal import Decimal
from pathlib import Path

import pytest

from engine.source import stair_rule_calculator as S

ROOT = Path(__file__).resolve().parents[2]


def line(res, item):
    return next(x for x in res["lines"] if x["item"] == item)


# ------------------------------------------------------------------ the owner's six acceptance cases (landing 1.00)
OWNER = [
    # H, L, risers, actual riser (3 dp), single treads / length, U flights / treads / length, result
    (3.20, 6.0, 20, 0.160, 19, 5.70, [10, 10], 18, 3.70, S.FITS_SINGLE),
    (3.20, 4.0, 20, 0.160, 19, 5.70, [10, 10], 18, 3.70, S.FITS_U),
    (3.20, 3.0, 20, 0.160, 19, 5.70, [10, 10], 18, 3.70, S.DOES_NOT_FIT),
    (3.00, None, 19, 0.158, 18, 5.40, [10, 9], 17, 3.70, S.NOT_CHECKED),
    (3.50, None, 22, 0.159, 21, 6.30, [11, 11], 20, 4.00, S.NOT_CHECKED),
    (4.00, None, 25, 0.160, 24, 7.20, [13, 12], 23, 4.60, S.NOT_CHECKED),
]


@pytest.mark.parametrize("H,L,n,h,st,sl,uf,ut,ul,res", OWNER)
def test_owner_acceptance_table(H, L, n, h, st, sl, uf, ut, ul, res):
    r = S.design(H, 1.20, L, landing_depth=1.00)
    assert r["risers"] == n
    assert round(r["actual_riser_m"], 3) == h
    assert r["single"]["treads"] == st and r["single"]["required_length_m"] == pytest.approx(sl, abs=1e-9)
    assert r["u"]["flights"] == uf and r["u"]["treads"] == ut
    assert r["u"]["required_length_m"] == pytest.approx(ul, abs=1e-9)
    assert r["fit"] == res


def test_failing_fit_says_needs_at_least_and_holds_every_line():
    r = S.design(3.20, 1.20, 3.0, landing_depth=1.00)
    assert r["stair_type"] is None and r["needs_at_least_m"] == pytest.approx(3.70)
    w = [x for x in r["warnings"] if x["code"] == "NOT_ENOUGH_SPACE"][0]
    assert "needs at least 3.70 m" in w["text"] and "3.70" in w["text_ar"]
    for x in r["lines"]:
        assert x["status"] == S.HELD and x["quantity"] is None and x["held_cause"] == "STAIR_DOES_NOT_FIT"
    assert line(r, "tread pieces")["candidates"] == {"SINGLE": 19, "U": 18}


# ------------------------------------------------------------------ exact arithmetic
@pytest.mark.parametrize("H,n", [(4.48, 28), ("4.48", 28), (Decimal("4.48"), 28), (4480, 28), (3.2, 20), (0.48, 3),
                                 (4.4800001, 29), (4.47, 28)])
def test_exact_ceil(H, n):
    unit = "mm" if H == 4480 else "m"
    assert S.design(H, 1.0, unit=unit)["risers"] == n


def test_binary_float_trap_is_not_hit():
    assert 4.48 / 0.16 > 28              # the trap the rule's implementation note names
    r = S.design(4.48, 1.10, landing_depth=1.10)
    assert r["risers"] == 28 and r["actual_riser_m"] == pytest.approx(0.16, abs=1e-12)
    assert r["warnings"] == []           # 0.16 exactly is not above the limit


def test_global_decimal_context_untouched():
    before = decimal.getcontext().prec
    S.design(3.17, 1.0)
    assert decimal.getcontext().prec == before


# ------------------------------------------------------------------ BOQ lines (hand calculations)
def test_lines_u_type_hand_values():
    # H 3.20, W 1.20, landing 1.00, U: 20 risers, 18 treads
    r = S.design(3.20, 1.20, 4.0, landing_depth=1.00)
    assert r["stair_type"] == "U" and r["treads"] == 18 and r["required_length_m"] == pytest.approx(3.70)
    assert line(r, "riser pieces")["quantity"] == 20
    assert line(r, "tread pieces")["quantity"] == 18
    assert line(r, "tread cladding")["quantity"] == pytest.approx(18 * 0.30 * 1.20)          # 6.480
    assert line(r, "riser cladding (visible riser)")["quantity"] == pytest.approx(20 * 0.13 * 1.20)  # 3.120 (S-2)
    assert line(r, "mid landing")["quantity"] == pytest.approx(1.00 * 2 * 1.20)            # 2.400
    for x in r["lines"]:
        assert x["status"] == S.ASSUMED and x["rule"] == "UP-STAIR-015"


def test_lines_single_type_no_landing_line_and_default_landing():
    # H 2.88, W 0.90, L 6.0: 18 risers x 0.160, single 17 treads = 5.10 m
    r = S.design(2.88, 0.90, 6.0)
    assert r["inputs_m"]["landing_depth"] == 0.90                 # default = stair width
    assert r["stair_type"] == "SINGLE" and r["treads"] == 17
    assert line(r, "mid landing")["status"] == "NOT_APPLICABLE" and line(r, "mid landing")["quantity"] is None
    assert line(r, "tread cladding")["quantity"] == pytest.approx(17 * 0.30 * 0.90)          # 4.590
    assert line(r, "riser cladding (visible riser)")["quantity"] == pytest.approx(18 * 0.13 * 0.90)  # 2.106


def test_no_available_length_holds_only_type_dependent_lines():
    r = S.design(3.00, 1.00, None, landing_depth=1.00)
    assert line(r, "riser pieces")["status"] == S.ASSUMED and line(r, "riser pieces")["quantity"] == 19
    for item in ("tread pieces", "tread cladding", "mid landing"):
        x = line(r, item)
        assert x["status"] == S.HELD and x["quantity"] is None and x["held_cause"] == "AVAILABLE_LENGTH_NOT_GIVEN"
    assert line(r, "tread pieces")["candidates"] == {"SINGLE": 18, "U": 17}
    assert line(r, "mid landing")["candidates"] == {"U": 2.0}


def test_units_are_never_summed():
    r = S.design(3.20, 1.20, 4.0, landing_depth=1.00)
    assert {x["unit"] for x in r["lines"]} == {"nr", "m2"}
    assert not any(k in r for k in ("total", "total_m2"))


def test_exact_boundary_fit_and_odd_count():
    # H 3.04: 19 risers (odd) x 0.160; single 18 x 0.30 = 5.40; U 10 + 9, (10 - 1) x 0.30 + 1.10 = 3.80
    assert S.design(3.04, 1.10, 5.40)["fit"] == S.FITS_SINGLE        # equal length fits
    r = S.design(3.04, 1.10, 5.39)
    assert r["fit"] == S.FITS_U and r["u"]["flights"] == [10, 9] and r["treads"] == 17
    assert r["required_length_m"] == pytest.approx(3.80)
    assert S.design(3.04, 1.10, 3.799)["fit"] == S.DOES_NOT_FIT


# ------------------------------------------------------------------ units, rotation-free inputs, adversarial
def test_millimetre_input_gives_the_same_result_as_metres():
    a = S.design(3.50, 1.25, 4.20, landing_depth=1.25)
    b = S.design(3500, 1250, 4200, landing_depth=1250, tread=300, max_riser=160, tread_buildup=30, unit="mm")
    assert {k: a[k] for k in ("risers", "fit", "treads", "required_length_m")} == \
           {k: b[k] for k in ("risers", "fit", "treads", "required_length_m")}
    assert [x["quantity"] for x in a["lines"]] == [x["quantity"] for x in b["lines"]]


def test_tread_warnings():
    r = S.design(3.20, 1.20, 8.0, tread=0.27)
    assert [w["code"] for w in r["warnings"]] == ["TREAD_BELOW_MIN"]
    assert r["single"]["required_length_m"] == pytest.approx(19 * 0.27)       # 5.13
    assert [w["code"] for w in S.design(3.20, 1.20, 8.0, tread=0.31)["warnings"]] == ["TREAD_ABOVE_ALLOWED_RANGE"]
    assert S.design(3.20, 1.20, 8.0, tread=0.28)["warnings"] == []


def test_riser_above_limit_when_max_riser_is_raised():
    # max riser 0.17: 3.40 / 0.17 = 20 risers of 0.170 > 0.16 -> warning (rule step 6)
    r = S.design(3.40, 1.20, 8.0, max_riser=0.17)
    assert r["risers"] == 20 and [w["code"] for w in r["warnings"]] == ["RISER_ABOVE_LIMIT"]


def test_single_riser_level_change():
    r = S.design(0.15, 1.50, 1.0)
    assert r["risers"] == 1 and r["single"]["treads"] == 0 and r["u"] is None and r["fit"] == S.FITS_SINGLE


@pytest.mark.parametrize("kw", [dict(floor_height=0), dict(floor_height=-3.2), dict(stair_width=0),
                                dict(stair_width=-1.2), dict(floor_height=float("nan")),
                                dict(floor_height=float("inf")), dict(floor_height=None), dict(floor_height=True),
                                dict(floor_height="abc"), dict(tread=0), dict(max_riser=0),
                                dict(available_length=-1.0), dict(tread_buildup=0.20)])
def test_invalid_inputs_raise(kw):
    args = dict(floor_height=3.2, stair_width=1.2, available_length=6.0)
    args.update(kw)
    with pytest.raises(S.StairRuleError):
        S.design(**args)


def test_unknown_unit_raises():
    with pytest.raises(S.StairRuleError):
        S.design(3.2, 1.2, unit="ft")


# ------------------------------------------------------------------ check mode (owner S-1: the drawing governs)
def test_check_flags_a_drawn_riser_above_the_limit_and_keeps_the_drawn_count():
    # development villa entrance flight (stair flight ledger E1): +0.15 -> +1.00 FFL, 5 drawn risers x 0.170,
    # 4 treads, going 0.300. Rule: ceil(0.85 / 0.16) = 6 risers of 0.1417.
    r = S.check_drawn(0.85, 5, drawn_treads=4, drawn_tread_depth=0.30)
    codes = [f["code"] for f in r["findings"]]
    assert codes == ["RISER_COUNT_DIFFERS", "DRAWN_RISER_ABOVE_LIMIT"]
    assert r["governs"] == "DRAWING" and r["kept"]["risers"] == 5 and r["kept"]["treads"] == 4
    assert r["drawn_actual_riser_m"] == pytest.approx(0.170) and r["rule_risers"] == 6
    assert r["quantities"] is None and r["flagged"] is True


def test_check_single_level_change_is_a_check_result_only():
    r = S.check_drawn(0.15, 1, drawn_treads=0)
    assert r["findings"] == [] and r["rule_risers"] == 1 and r["rule_treads_for_drawn_flights"] == 0
    assert r["quantities"] is None and "lines" not in r


def test_check_consistent_drawn_u_stair_has_no_finding():
    r = S.check_drawn(3.20, 20, drawn_treads=18, drawn_tread_depth=0.29, drawn_flights=2,
                      drawn_riser_heights=[0.16] * 20)
    assert r["findings"] == []


def test_check_finds_tread_count_short_tread_and_uneven_risers():
    hs = [0.16] * 19 + [0.12]          # a leftover short step: sum 3.16 != 3.20
    r = S.check_drawn(3.20, 20, drawn_treads=20, drawn_tread_depth=0.27, drawn_riser_heights=hs)
    codes = {f["code"] for f in r["findings"]}
    assert {"TREAD_COUNT_INCONSISTENT", "DRAWN_TREAD_BELOW_MIN", "NON_UNIFORM_RISERS",
            "RISER_SUM_DIFFERS_FROM_FLOOR_HEIGHT"} <= codes
    assert "RISER_COUNT_DIFFERS" not in codes and r["kept"]["treads"] == 20


def test_defaults_stay_metres_in_millimetre_mode():
    # an omitted max riser / tread / build-up is the rule default in m, never 0.16 mm
    a = S.design(3.20, 1.20, 4.0, landing_depth=1.00)
    b = S.design(3200, 1200, 4000, landing_depth=1000, unit="mm")
    assert b["risers"] == 20 and b["fit"] == S.FITS_U
    assert [x["quantity"] for x in a["lines"]] == [x["quantity"] for x in b["lines"]]


def test_check_in_millimetres():
    r = S.check_drawn(850, 5, drawn_tread_depth=300, unit="mm")
    assert r["drawn_actual_riser_m"] == pytest.approx(0.170) and r["rule_risers"] == 6


@pytest.mark.parametrize("kw", [dict(drawn_risers=0), dict(drawn_risers=2.0), dict(drawn_risers=True),
                                dict(drawn_flights=0), dict(drawn_flights=6), dict(drawn_treads=-1),
                                dict(floor_height=0)])
def test_check_invalid_inputs_raise(kw):
    args = dict(floor_height=0.85, drawn_risers=5)
    args.update(kw)
    with pytest.raises(S.StairRuleError):
        S.check_drawn(**args)


# ------------------------------------------------------------------ the rule record
def test_rule_record_is_owner_approved_over_1_5_0():
    r = S.rule_record()
    assert r["rule_id"] == "UP-STAIR-015" and r["status"] == "OWNER_APPROVED" and r["approval"]["on"] == "2026-10-21"
    assert {p["id"]: p["status"] for p in r["open_points"]} == {"S-1": "ANSWERED", "S-2": "ANSWERED", "S-3": "ANSWERED"}
    assert set(r["relations"]) == {"UP-STAIR-002", "UP-STAIR-003", "UP-STAIR-006", "UP-STAIR-009"}
    assert len(r["acceptance"]) == 6


def test_acceptance_table_in_the_rule_file_matches_the_calculator():
    for a in S.rule_record()["acceptance"]:
        res = S.design(a["floor_height"], 1.0, a.get("available_length"), landing_depth=a["landing_depth"])
        assert res["risers"] == a["risers"] and round(res["actual_riser_m"], 3) == a["actual_riser"]
        st, sl = a["single"].split(" / ")
        assert res["single"]["treads"] == int(st) and res["single"]["required_length_m"] == pytest.approx(float(sl))
        fl, ut, ul = a["u"].split(" / ")
        assert res["u"]["flights"] == [int(x) for x in fl.split("+")] and res["u"]["treads"] == int(ut)
        assert res["u"]["required_length_m"] == pytest.approx(float(ul))


def test_new_id_does_not_collide_and_old_rule_files_are_untouched():
    ov15 = json.loads((ROOT / "rules/owner_decisions/URBAN_RULES_1.5.0.json").read_text(encoding="utf-8"))
    lib = json.loads((ROOT / "rules/owner_library/URBAN_PROJECTS_RULE_LIBRARY_1.4.0.json").read_text(encoding="utf-8"))
    ids = {r["rule_id"] for r in ov15["records"]} | {r["rule_id"] for r in lib["rules"]}
    assert "UP-STAIR-015" not in ids
    from engine.source import rule_store as RS
    assert RS.LATEST_APPROVED == "1.5.0" and "UP-STAIR-015" not in RS.rule_set()["rules"]
    assert RS.check() == []
