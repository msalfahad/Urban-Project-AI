"""T-322 LIFT_BASE_LEDGER_V1 on a NON-Alsenan hand fixture (villa R) and its adverse cases.

Villa R (hand calculation, m): raft 4.00 x 4.50 x 0.55 at (0, 0)-(4.00, 4.50); lift pit 1.60 x 1.80 clear inside a
0.20 RC ring, ring outer (1.00, 1.00)-(3.00, 3.20) = 2.00 x 2.20; blinding 0.10 thick with its projection 0.10 printed
on the GOVERNING (lift) detail; screed 0.05 printed; membrane thickness not printed; pit height 1.40 printed.
  raft      4.00 x 4.50 x 0.55                       = 9.9000 m3
  blinding  (4.00 + 0.20) x (4.50 + 0.20) x 0.10      = 4.20 x 4.70 x 0.10 = 1.9740 m3
  screed    18.00 x 0.05                              = 0.9000 m3 (membrane area 18.00 m2, volume HELD)
  ring      2.00 x 2.20 - 1.60 x 1.80 = 4.40 - 2.88   = 1.5200 m2; x 1.40 = 2.1280 m3
  with a 0.20 x 0.20 corner column in the band        = 1.4800 m2; x 1.40 = 2.0720 m3
  blinding offset not printed on the lift detail      -> HELD, AT_LEAST 18.00 x 0.10 = 1.8000 m3
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t322"))
import lift_base_ledger_v1 as X  # noqa: E402

GOV = "lift detail R-7"
TYP = "typical footing detail R-3"


def villa_r(unit="m"):
    k = {"m": 1.0, "cm": 100.0, "mm": 1000.0}[unit]

    def d(v, src, det=GOV):
        return {"value": v * k, "source": src, "detail": det, "status": "PRINTED"}
    return {
        "unit": unit, "governing_detail": GOV,
        "raft": {"rect": [0, 0, 4.0 * k, 4.5 * k], "schedule": [4.5 * k, 4.0 * k], "H": d(0.55, "schedule R"),
                 "source": "outline R-FF"},
        "blinding": {"t": d(0.10, "lift detail '10 plain'"), "p": d(0.10, "lift detail '10' each side")},
        "underlay": [{"name": "screed", "t": d(0.05, "lift detail '5 screed'"), "owner": "SCREED"},
                     {"name": "membrane", "t": None, "owner": "WP"}],
        "ring": {"outer": [1.0 * k, 1.0 * k, 3.0 * k, 3.2 * k], "inner": [1.2 * k, 1.2 * k, 2.8 * k, 3.0 * k],
                 "columns": [], "source": "ring R"},
        "pit_height": d(1.40, "lift detail pit depth 1.40"),
        "side_buildup": [{"name": "board", "t": None, "owner": "WP"}],
    }


def comps(res):
    return {c["id"]: c for c in res["components"]}


def test_normal_villa_r_by_hand():
    r = X.build(villa_r())
    c = comps(r)
    assert c["RAFT"]["value"] == pytest.approx(9.900) and c["RAFT"]["status"] == X.DC
    assert c["BLINDING"]["value"] == pytest.approx(1.974) and c["BLINDING"]["status"] == X.DC
    assert c["UNDERLAY:screed:VOL"]["value"] == pytest.approx(0.900)
    assert c["UNDERLAY:membrane:AREA"]["value"] == pytest.approx(18.00)
    assert c["UNDERLAY:membrane:VOL"]["value"] is None and c["UNDERLAY:membrane:VOL"]["status"] == X.HELD
    assert c["PIT_WALL:PLAN"]["value"] == pytest.approx(1.52)
    assert c["PIT_WALL:CONC"]["value"] == pytest.approx(2.128)
    assert c["PIT_FLOOR"]["value"] == 0.0                     # the raft top, never a second volume
    assert r["totals"]["established_m3"] == pytest.approx(9.900 + 1.974 + 0.900 + 2.128)


def test_column_in_ring_band_is_the_column_lines():
    s = villa_r()
    s["ring"]["columns"] = [[1.0, 1.0, 1.2, 1.2]]
    c = comps(X.build(s))
    assert c["PIT_WALL:PLAN"]["value"] == pytest.approx(1.48)
    assert c["PIT_WALL:CONC"]["value"] == pytest.approx(2.072)
    # a column 0.05 proud of the ring: only the part in the band leaves the wall
    s["ring"]["columns"] = [[2.8, 1.0, 3.05, 2.0]]
    assert comps(X.build(s))["PIT_WALL:PLAN"]["value"] == pytest.approx(1.52 - 0.20 * 1.00)


def test_offset_not_printed_on_governing_detail_is_held_with_bound():
    s = villa_r()
    s["blinding"]["p"] = None
    b = comps(X.build(s))["BLINDING"]
    assert b["value"] is None and b["status"] == X.AT_LEAST
    assert b["low"] == pytest.approx(1.800)                   # raft plan x 0.10: the screed and raft stand on it
    assert "BLINDING_PROJECTION_NOT_PRINTED_ON_GOVERNING_DETAIL" in b["held"]


def test_offset_from_a_typical_detail_of_another_element_is_inherited_not_confirmed():
    s = villa_r()
    s["blinding"]["p"] = {"value": 0.10, "source": "typical footing '10 | L x W | 10'", "detail": TYP,
                          "status": "PRINTED"}
    b = comps(X.build(s))["BLINDING"]
    assert b["value"] is None and b["status"] == X.AT_LEAST
    assert b["readings"] == [{"p_m": 0.1, "kind": X.INHERITED, "basis": "typical footing '10 | L x W | 10'",
                              "volume_m3": pytest.approx(1.974)}]


def test_scaled_reading_is_evidence_never_a_quantity():
    sc = X.scaled_reading([(0.05, 2.5), (0.10, 5.0)], 7.5)    # 1:20 at 50 paper units per m
    assert sc["value_m"] == pytest.approx(0.15) and sc["kind"] == X.SCALED
    s = villa_r()
    s["blinding"]["p"] = {"value": sc["value_m"], "source": "scaled", "kind": X.SCALED}
    b = comps(X.build(s))["BLINDING"]
    assert b["value"] is None and b["readings"][0]["volume_m3"] == pytest.approx(4.30 * 4.80 * 0.10)
    with pytest.raises(X.Refused) as e:
        X.scaled_reading([(0.05, 2.5), (0.10, 6.0)], 7.5)      # printed dims disagree by 20 %: not to scale
    assert e.value.code == "NOT_TO_SCALE"
    with pytest.raises(X.Refused) as e:
        X.scaled_reading([(0.05, 2.5)], 7.5)
    assert e.value.code == "SCALE_NOT_PROVEN"


def test_pit_wall_in_raft_and_wall_refused():
    s = villa_r()
    s["raft_includes_wall"] = True
    with pytest.raises(X.Refused) as e:
        X.build(s)
    assert e.value.code == "PIT_WALL_IN_RAFT_AND_WALL"
    s = villa_r()
    s["wall_bottom"] = -0.55                                   # wall solid modelled down through the raft
    with pytest.raises(X.Refused) as e:
        X.build(s)
    assert e.value.code == "PIT_WALL_IN_RAFT_AND_WALL"
    s = villa_r()
    s["pit_floor_slab"] = {"t": 0.30}
    with pytest.raises(X.Refused) as e:
        X.build(s)
    assert e.value.code == "PIT_FLOOR_IN_RAFT"


def test_pit_height_missing_is_held_never_zero():
    s = villa_r()
    s["pit_height"] = {"value": None, "source": "as per lift manufacturer"}
    w = comps(X.build(s))["PIT_WALL:CONC"]
    assert w["value"] is None and w["status"] == X.HELD and "PIT_HEIGHT_NOT_PRINTED" in w["held"]
    s["pit_height"] = {"value": 1.4, "source": "x", "status": "HELD"}
    with pytest.raises(X.Refused) as e:
        X.build(s)
    assert e.value.code == "HELD_AS_VALUE"


def test_ring_outside_raft_and_column_into_pit_refused():
    s = villa_r()
    s["ring"]["outer"] = [2.5, 1.0, 4.5, 3.2]
    s["ring"]["inner"] = [2.7, 1.2, 4.3, 3.0]
    with pytest.raises(X.Refused) as e:
        X.build(s)
    assert e.value.code == "RING_OUTSIDE_RAFT"
    s = villa_r()
    s["ring"]["columns"] = [[1.0, 1.0, 1.5, 1.5]]              # reaches into the clear pit
    with pytest.raises(X.Refused) as e:
        X.build(s)
    assert e.value.code == "COLUMN_INTO_PIT"


def test_outline_vs_schedule_conflict_never_a_value():
    s = villa_r()
    s["raft"]["schedule"] = [4.6, 4.0]
    r = X.build(s)
    assert r["components"][0]["status"] == X.CONFLICT and r["components"][0]["value"] is None


@pytest.mark.parametrize("unit", ["cm", "mm"])
def test_units_give_identical_results(unit):
    a, b = comps(X.build(villa_r())), comps(X.build(villa_r(unit)))
    for k in a:
        assert b[k]["value"] == pytest.approx(a[k]["value"]) if a[k]["value"] is not None else b[k]["value"] is None


def test_undeclared_unit_refused():
    s = villa_r()
    s["unit"] = "in"
    with pytest.raises(X.Refused) as e:
        X.build(s)
    assert e.value.code == "UNIT_NOT_DECLARED"


def test_mirror_and_quarter_turn_identical():
    base = comps(X.build(villa_r()))

    def mirror(r):
        return [-r[2], r[1], -r[0], r[3]]

    def turn(r):
        return [-r[3], r[0], -r[1], r[2]]
    for f in (mirror, turn):
        s = copy.deepcopy(villa_r())
        s["raft"]["rect"] = f(s["raft"]["rect"])
        s["ring"]["outer"] = f(s["ring"]["outer"])
        s["ring"]["inner"] = f(s["ring"]["inner"])
        c = comps(X.build(s))
        for k in base:
            assert c[k]["value"] == pytest.approx(base[k]["value"]) if base[k]["value"] is not None \
                else c[k]["value"] is None


def test_no_governing_detail_or_source_refused():
    s = villa_r()
    s["governing_detail"] = ""
    with pytest.raises(X.Refused):
        X.build(s)
    s = villa_r()
    s["blinding"]["t"]["source"] = ""
    with pytest.raises(X.Refused) as e:
        X.build(s)
    assert e.value.code == "NO_SOURCE"
