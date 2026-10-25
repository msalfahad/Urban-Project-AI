"""T-280: foundation column cores start at the footing top on the printed level chain (R-COL-CORE-DATUM-1 proposed).

Villa K280 (synthetic, NOT Alsenan; hand-calculated below): two isolated footings, a 2-storey column on each.
  existing plot level EGL -0.20 (the plot sits below the datum), excavation 'not less than 1.20 m below the plot',
  underlay 0.15 (10 blinding + 5 screed), GF FFL +0.80, 1F FFL +4.30, roof +7.80.
  column A on footing FA, H 0.40, 6 T14;  column B on footing FB, H 0.60, 8 T16.
  formation limit = -0.20 - 1.20 = -1.40
  A: footing top <= -1.40 + 0.15 + 0.40 = -0.85 -> core >= 0.80 + 0.85 = 1.65 m
  B: footing top <= -1.40 + 0.15 + 0.60 = -0.65 -> core >= 0.80 + 0.65 = 1.45 m
  kg/m (7850 kg/m3): T14 = pi/4 x 0.014^2 x 7850 = 1.2084291; T16 = 1.5783362
  A: 6 x 1.65 x 1.2084291 = 11.963448 kg;  B: 8 x 1.45 x 1.5783362 = 18.308700 kg
  ledger convention (footing UNDERSIDE at the formation limit): A 2.20 - 0.40 = 1.80, B 1.60 m
  delta A = -6 x 0.15 x 1.2084291 = -1.087586 kg; B = -8 x 0.15 x 1.5783362 = -1.894003 kg
"""

from __future__ import annotations

import copy
import json
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t280"))

import t280_core_datum as CD  # noqa: E402

KGM14 = math.pi / 4 * 0.014 ** 2 * 7850
KGM16 = math.pi / 4 * 0.016 ** 2 * 7850

CHAIN_K = {
    "gf_ffl_m": 0.80, "egl_m": -0.20, "min_excavation_m": 1.20,
    "underlay_m": {"P13_ISOLATED": 0.15, "P13_CONFLICT": 0.15, "LIFT_PIT_FF": None, "UNBOUND": None},
    "schedule_h_m": {"FA": 0.40, "FB": 0.60},
}


def _main(cid, floor, n, d, length_mm, basis):
    kg = n * length_mm / 1000 * (KGM14 if d == 14 else KGM16)
    return {"chain_id": cid, "component": "MAIN_BARS", "floor": floor, "count": n, "dia_mm": d, "type": cid[-1],
            "kg": round(kg, 3), "total_length_m": n * length_mm / 1000,
            "interval": {"length_mm": length_mm, "state": "LOWER_BOUND" if floor == "FOUNDATION" else "ESTABLISHED",
                         "basis": basis}}


def villa_k():
    fb = "GF FFL +0.80 m minus founding level <= -1.40 m minus footing depth {} mm (bound footing)"
    main = [
        _main("COL-A", "FOUNDATION", 6, 14, 1800.0, fb.format(400.0)),
        _main("COL-A", "GF", 6, 14, 3500.0, "printed floor-to-floor 3.5 m (FFL basis)"),
        _main("COL-A", "1F", 6, 14, 3500.0, "printed floor-to-floor 3.5 m (FFL basis)"),
        _main("COL-B", "FOUNDATION", 8, 16, 1600.0, fb.format(600.0)),
        _main("COL-B", "GF", 8, 16, 3500.0, "printed floor-to-floor 3.5 m (FFL basis)"),
        _main("COL-B", "1F", 8, 16, 3500.0, "printed floor-to-floor 3.5 m (FFL basis)"),
    ]
    rule = {"bottom_cover_mm": 70, "foot_mm": 300, "projection_D": 40}
    rows = []
    for cid, ref, H, n, d in (("COL-A", "FTG-FA-1-1", 400.0, 6, 14), ("COL-B", "FTG-FB-2-2", 600.0, 8, 16)):
        rows.append({"chain_id": cid, "component": "STARTER", "release_state": "PROVISIONAL", "count": n, "dia_mm": d,
                     "footing": {"ref": ref, "depth_mm": H}, "length_per_piece_mm": (H - 70) + 300 + 40 * d,
                     "part_id": f"SEG-{cid}-FOUNDATION|STARTER", "floor": "FOUNDATION"})
        for fl in ("FOUNDATION", "GF"):
            rows.append({"chain_id": cid, "component": "LAP", "release_state": "PROVISIONAL", "count": n,
                         "dia_mm": d, "floor": fl, "part_id": f"SEG-{cid}-{fl}|LAP_TOP"})
    return main, {"rows": rows, "starter_rule": rule}


# ---------------------------------------------------------------- normal case (hand-calculated villa K280)

def test_villa_k_cores_from_footing_top():
    main, ls = villa_k()
    out = CD.build(main, ls, CHAIN_K)
    by = {r["chain_id"]: r for r in out["rows"]}
    assert out["foundation_core_rows"] == 2           # only the FOUNDATION segments; GF / 1F untouched
    a, b = by["COL-A"], by["COL-B"]
    assert a["status"] == b["status"] == CD.STATUS_LOWER
    assert a["lower_length_m"] == pytest.approx(1.65, abs=1e-9)
    assert b["lower_length_m"] == pytest.approx(1.45, abs=1e-9)
    assert a["lower"]["footing_top_max_m"] == pytest.approx(-0.85, abs=1e-9)
    assert b["lower"]["footing_top_max_m"] == pytest.approx(-0.65, abs=1e-9)
    assert a["lower_kg"] == pytest.approx(11.963, abs=5e-4)
    assert b["lower_kg"] == pytest.approx(18.309, abs=5e-4)
    assert a["delta_kg_vs_ledger"] == pytest.approx(-1.088, abs=5e-4)
    assert b["delta_kg_vs_ledger"] == pytest.approx(-1.894, abs=5e-4)
    assert a["upper"] == b["upper"] == CD.UPPER_OPEN       # never a value
    assert a["ledger"]["label_restated"] == "CONVENTION_NOT_A_BOUND"
    assert a["ledger"]["implied_formation_m"] == pytest.approx(-1.55, abs=1e-9)   # 0.15 below the printed limit
    assert out["lower_t_restated_rows"] == pytest.approx((11.963448 + 18.308700) / 1000, abs=2e-6)
    assert out["starters_ok"] == 2 and out["laps_ok"] == 4 and out["findings"] == []


def test_lower_bound_is_below_every_deeper_formation():
    # physical check: any formation deeper than the limit gives a LONGER core, never a shorter one
    lim = CD.core_bounds(0.80, -0.20, 1.20, 0.15, [0.40], "P13_ISOLATED")["lower_m"]
    for extra in (0.0, 0.01, 0.30, 1.0):
        ftop = -0.20 - 1.20 - extra + 0.15 + 0.40
        assert 0.80 - ftop >= lim - 1e-12


def test_conflict_uses_every_candidate():
    b = CD.core_bounds(1.00, 0.00, 1.50, 0.17, [0.30, 0.50], "P13_CONFLICT")
    assert b["lower_m"] == pytest.approx(1.83, abs=1e-9)        # max H: valid for both readings
    assert b["lower_m"] <= CD.core_bounds(1.00, 0.00, 1.50, 0.17, [0.30], "P13_ISOLATED")["lower_m"]


# ---------------------------------------------------------------- adverse cases

def test_underlay_missing_is_held_never_formation():
    main, ls = villa_k()
    chain = copy.deepcopy(CHAIN_K)
    chain["underlay_m"]["P13_ISOLATED"] = None
    out = CD.build(main, ls, chain)
    for r in out["rows"]:
        assert r["status"] == CD.STATUS_HELD
        assert r["lower_length_m"] is None and r["lower_kg"] is None      # held, never 0, never formation-based
        assert "UNDERLAY_NOT_ESTABLISHED" in r["delta_cause"]
    assert out["lower_kg_restated_rows"] == 0 and out["held_rows"] == 2
    b = CD.core_bounds(0.80, -0.20, 1.20, None, [0.40], "P13_ISOLATED")
    assert b["lower_m"] is None and b["status"] == CD.STATUS_HELD


def test_core_from_formation_would_be_longer_than_the_bound_not_equal():
    # a core counted from the formation (footing bottom taken AT the formation) is the ledger convention: 0.15 longer
    main, ls = villa_k()
    a = {r["chain_id"]: r for r in CD.build(main, ls, CHAIN_K)["rows"]}["COL-A"]
    assert a["ledger"]["length_m"] - a["lower_length_m"] == pytest.approx(0.15, abs=1e-9)


def test_lift_pit_and_unbound_held():
    main, ls = villa_k()
    ls["rows"][0]["footing"] = {"ref": "FTG-FF-9-9", "depth_mm": 400.0}
    chain = copy.deepcopy(CHAIN_K)
    chain["schedule_h_m"]["FF"] = 0.40
    ls["rows"][3]["footing"] = {"ref": "FT:RB-xyz", "depth_mm": None}
    out = CD.build(main, ls, chain)
    by = {r["chain_id"]: r for r in out["rows"]}
    assert by["COL-A"]["status"] == CD.STATUS_HELD and "PIT_DEPTH_NOT_PRINTED" in by["COL-A"]["delta_cause"]
    assert by["COL-B"]["status"] == CD.STATUS_HELD and "SUPPORT_NOT_BOUND" in by["COL-B"]["delta_cause"]
    cond = by["COL-B"]["conditional_lower_if_p13_footing"]
    assert cond["status"].startswith("CONDITIONAL") and cond["h_m"] == 0.60
    assert out["lower_kg_restated_rows"] == 0          # nothing conditional is summed


def test_stopping_column_top_datum_held():
    # a column that stops in the foundation storey ends in the closing ground beam, not at GF FFL
    main, ls = villa_k()
    main[0]["chain_continues_above"] = False
    out = CD.build(main, ls, CHAIN_K)
    a = {r["chain_id"]: r for r in out["rows"]}["COL-A"]
    assert a["status"] == CD.STATUS_HELD and a["lower_kg"] is None
    assert a["delta_cause"].startswith("TOP_DATUM_NOT_PRINTED")
    assert a["lower"]["core_to_gf_ffl_if_top_were_ffl_m"] == pytest.approx(1.65, abs=1e-9)   # information only
    assert out["restated_rows"] == 1


def test_ledger_h_not_schedule_h_is_a_finding():
    main, ls = villa_k()
    main[0]["interval"]["basis"] = main[0]["interval"]["basis"].replace("400.0", "500.0")
    out = CD.build(main, ls, CHAIN_K)
    assert [f["finding"] for f in out["findings"]] == ["LEDGER_H_NOT_SCHEDULE_H"]


@pytest.mark.parametrize("args", [
    (None, 0.0, 1.5, 0.17, [0.3]), (1.0, float("nan"), 1.5, 0.17, [0.3]), (True, 0.0, 1.5, 0.17, [0.3]),
    (1000.0, 0.0, 1500.0, 170.0, [300.0]),          # millimetres passed as metres
    (1.0, 0.0, -1.5, 0.17, [0.3]),                  # a negative excavation depth
    (1.0, 0.0, 1.5, 0.17, [3.0]),                   # footing top above GF FFL: inconsistent chain
])
def test_bad_inputs_refused(args):
    with pytest.raises(CD.CoreDatumError):
        CD.core_bounds(*args, "P13_ISOLATED")


def test_missing_depth_held():
    assert CD.core_bounds(1.0, 0.0, 1.5, 0.17, [None], "P13_ISOLATED")["status"] == CD.STATUS_HELD
    assert CD.core_bounds(1.0, 0.0, 1.5, 0.17, [], "P13_ISOLATED")["lower_m"] is None


# ---------------------------------------------------------------- Alsenan (development villa; merged ledger, read only)

def test_alsenan_pinned():
    out = CD.build()
    assert out["foundation_core_rows"] == 36
    assert out["by_support_family"] == {"LIFT_PIT_FF": 4, "P13_CONFLICT": 2, "P13_ISOLATED": 27, "UNBOUND": 3}
    assert out["ledger_kg_all"] == pytest.approx(974.831, abs=1e-3)
    assert out["restated_rows"] == 26 and out["held_rows"] == 10
    assert out["held_by_reason"] == {"PIT_DEPTH_NOT_PRINTED": 4, "TOP_DATUM_NOT_PRINTED": 3, "SUPPORT_NOT_BOUND": 3}
    assert out["delta_kg_restated_rows"] == pytest.approx(-66.548, abs=2e-3)
    assert out["delta_kg_by_family"]["P13_ISOLATED"] == pytest.approx(-61.718, abs=2e-3)
    assert out["delta_kg_by_family"]["P13_CONFLICT"] == pytest.approx(-4.830, abs=2e-3)
    assert out["lower_kg_restated_rows"] == pytest.approx(734.781, abs=2e-3)
    rec = out["t273_finding_reconciled"]
    parts = (rec["of_which_restated_p13_continuing_kg"], rec["of_which_lift_ff_withdrawn_kg"],
             rec["of_which_stopping_cn_withdrawn_kg"])
    assert parts == pytest.approx((-61.713, -10.196, -2.465), abs=2e-3)
    assert sum(parts) == pytest.approx(rec["recomputed_same_formula_kg"], abs=1.5e-3)     # residual named, not hidden
    assert rec["recomputed_same_formula_kg"] - rec["t273_kg"] == pytest.approx(0.007, abs=1e-3)
    assert out["starters_ok"] == out["starters_checked"] == 36
    assert out["laps_ok"] == out["laps_checked"] == 56
    assert out["findings"] == []
    by = {r["chain_id"]: r for r in out["rows"]}
    x = by["COLPOS-X01-Y01-2138-7462"]          # hand: 8 T16, F H 0.30: 2.33 - 0.30 = 2.03 m
    assert x["lower_length_m"] == pytest.approx(2.03, abs=1e-9)
    assert x["lower_kg"] == pytest.approx(8 * 2.03 * KGM16, abs=5e-4)
    for r in out["rows"]:
        assert r["upper"] in (CD.UPPER_OPEN, "HELD")
        if r["support_family"] in ("LIFT_PIT_FF", "UNBOUND") or r["type"] == "CN":
            assert r["lower_kg"] is None          # lift pit, unbound support or a column stopping in the foundation


def test_alsenan_json_reproducible():
    disk = json.loads((ROOT / "research" / "agents_t280" / "CORE_DATUM_T280.json").read_text(encoding="utf-8"))
    assert json.loads(json.dumps(CD.build(), sort_keys=True)) == disk
