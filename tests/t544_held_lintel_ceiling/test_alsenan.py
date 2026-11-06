"""T-544 on the development villa from committed numbers-only evidence (no drawing needed).

Hand calculation (metres; ceilings = measured a rounded UP to the mm, R-T544-1 (1); host L-2fdc0f97 1F white AAC 0.20,
contract net 101.976 m2, 4.5 kg/m2):
  W16 (gap 1.5523): START 0.4933 OPENING W15 -> 0.494; END 1.2322 COLUMN -> 1.233; L_ceil 3.2796 -> 3.280
  W19 (0.6000): START 0.7250 COLUMN -> 0.725; END 0.875 OPENING W20 -> 0.875; L_ceil 2.200
  W20 (0.6000): START 0.875 OPENING W19; END 1.011731 COLUMN -> 1.012; L_ceil 2.487
  W24 (1.5524): START 0.937069 COLUMN -> 0.938; END 3.000 SEARCH_LIMIT (V3) -> extended 4.2188 COLUMN -> 4.219;
      L_ceil 6.7094 -> 6.710
  joints (pier once): W15 + W16 = 0.795 + 1.5523 + 0.494 + 1.5523 + 1.233 = 5.6266 -> 5.627 (column face to column face
      5.625 + roundings), face [0.47, 1.1254]; W19 + W20 = 0.725 + 0.6 + 0.875 + 0.6 + 1.012 = 3.812, face [0, 0.7624]
  faces hi: W14 1.23 + W18 0.20886 + 1.1254 + 0.7624 + W24 1.342 = 4.66866; lo: 0.975 + 0.47 + 0.17346 = 1.61846
  base [101.976 - 4.66866, 101.976 - 1.61846] = [97.30734, 100.35754] m2 -> glue [437.88303, 451.60893] kg
  before (T-537 r2): HELD blank, AT_MOST 451.60893 kg (the high end does not move).
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t544"))
sys.path.insert(0, str(ROOT / "research" / "agents_t537"))
import held_lintel_ceiling as H  # noqa: E402
import r_t498_2 as R  # noqa: E402
import t544_apply as T  # noqa: E402


@pytest.fixture(scope="module")
def app():
    return T.build()


def test_evidence_is_numbers_only():
    for p in (T.EVIDENCE, T.EXTENDED):
        rows = list(csv.DictReader(open(p, encoding="utf-8")))
        assert rows
        for r in rows:
            for k, v in r.items():
                assert not any(w in k.lower() for w in ("x_", "y_", "coord", "name")), k
    assert {(r["opening_id"], r["side"]) for r in csv.DictReader(open(T.EVIDENCE))} == \
        {(o, s) for o in T.HELD_IDS for s in ("START", "END")}


def test_end_ceilings(app):
    want = {"W16": {"START": 0.494, "END": 1.233}, "W19": {"START": 0.725, "END": 0.875},
            "W20": {"START": 0.875, "END": 1.012}, "W24": {"START": 0.938, "END": 4.219}}
    got = {k: v["ceilings_m"] for k, v in app["held_lintels"].items()}
    assert got == want
    stops = {(k, s): e["stopper"] for k, es in app["ends"].items() for s, e in es.items()}
    assert stops[("W24", "END")] == "COLUMN" and stops[("W16", "START")] == "OPENING"
    assert app["ends"]["W24"]["END"]["search"].startswith("20.0")


def test_lintel_ceilings(app):
    assert {k: v["L_ceil_m"] for k, v in app["held_lintels"].items()} == \
        {"W16": 3.28, "W19": 2.2, "W20": 2.487, "W24": 6.71}
    assert all(v["face_m2"][0] == 0.0 for v in app["held_lintels"].values())     # existence not established


def test_joint_records_and_column_span_crosscheck(app):
    f = {x["opening_id"]: x for x in app["after"]["base"]["faces"]}
    assert f["W15+W16"]["L_ceil_m"] == 5.627 and f["W15+W16"]["face_m2"] == [0.47, 1.1254]
    assert f["W19+W20"]["L_ceil_m"] == 3.812 and f["W19+W20"]["face_m2"] == [0.0, 0.7624]
    # the joint span reproduces the column-face-to-column-face distance within the up-roundings (<= 5 mm)
    e = app["ends"]
    span_15_16 = e["W15"]["START"]["a_m"] + 1.5523 + e["W16"]["START"]["a_m"] + 1.5523 + e["W16"]["END"]["a_m"]
    span_19_20 = e["W19"]["START"]["a_m"] + 0.6 + e["W19"]["END"]["a_m"] + 0.6 + e["W20"]["END"]["a_m"]
    assert abs(span_15_16 - 5.625) < 1e-3 and abs(span_19_20 - 3.8117) < 1e-3
    assert 0 <= 5.627 - span_15_16 <= 0.005 and 0 <= 3.812 - span_19_20 <= 0.005


def test_host_after(app):
    a = app["after"]
    assert a["base"]["state"] == "RANGE"
    assert a["base"]["base_m2"] == [97.30734, 100.35754]
    assert a["base"]["face_sum_m2"] == [1.61846, 4.66866]
    assert a["glue_kg"] == {"state": "BOUNDED_EXPOSURE", "value": None, "range": [437.88303, 451.60893], "unit": "kg"}
    assert a["bags_25kg_net"]["range"] == [17.515321, 18.064357]


def test_before_reproduced_and_high_end_unmoved(app):
    b = app["before_t537_r2"]
    assert b["glue_kg"]["state"] == "HELD" and b["glue_kg"]["at_most_beside"] == 451.60893
    assert app["after"]["glue_kg"]["range"][1] == b["glue_kg"]["at_most_beside"]


def test_individual_ceilings_beside_not_the_bound(app):
    s = app["beside_individual_ceilings"]
    # each lintel taking the whole shared pier: the piers 0.494 + 0.875 counted twice x D 0.20 = 0.2738 m2 more face
    # (0.2730 after the per-lintel up-roundings): W14 1.23 + W15 0.5674 + W18 0.20886 + W16 0.656 + W19 0.44
    # + W20 0.4974 + W24 1.342 = 4.94166
    assert s["face_sum_m2"] == [1.61846, 4.94166]
    assert abs((4.94166 - 4.66866) - 0.2 * (0.494 + 0.875)) < 1e-3
    assert s["base_m2"][0] < app["after"]["base"]["base_m2"][0]


def test_conditional_t530_low_end_was_not_a_lower_bound(app):
    # T-530 / T-537 conditional low end 443.27313 kg assumed D x (w + 0.80) maxima; the measured ceilings go below it
    assert app["after"]["glue_kg"]["range"][0] < 443.27313
    assert round(443.27313 - app["after"]["glue_kg"]["range"][0], 5) == 5.3901


def test_glue_group(app):
    g = app["glue_group"]
    assert g["before_t537_r2"]["at_least"] == [17.643906, 18.16227]
    assert g["after"]["status"] == "HELD"                 # other members stay open (losses HELD): AT_LEAST only
    assert g["after"]["at_least"] == [35.159227, 36.226627] and g["after"]["to_buy_at_least"] == [36, 37]
    assert "L-2fdc0f971a94348ec855 (range) (loss HELD)" in g["after"]["open"]


def test_concrete_beside(app):
    c = app["beside_concrete_if_built"]
    assert {k: v["concrete_m3"] for k, v in c.items()} == \
        {"W16": [0.0, 0.1312], "W19": [0.0, 0.088], "W20": [0.0, 0.09948], "W24": [0.0, 0.2684]}
    assert app["released_quantities_changed"] == 0


def test_adverse_min_bearing_ceiling_on_villa_input_refused(app):
    e = dict(app["ends"]["W24"]["START"], basis="MIN_BEARING", a_m=0.40)
    with pytest.raises(R.RuleError):
        H.held_face("W24", [0.20, 0.20], 1.5524, [e, app["ends"]["W24"]["END"]], 0.20)


def test_adverse_unsearched_end_holds_the_host(app, monkeypatch):
    rows = [r for r in csv.DictReader(open(T.EXTENDED))]
    monkeypatch.setattr(T, "_csv", lambda p, _o=T._csv: [] if Path(p) == T.EXTENDED else _o(p))
    d = T.build()
    assert d["after"]["glue_kg"]["state"] == "HELD" and d["after"]["glue_kg"]["value"] is None
    assert d["after"]["glue_kg"]["at_most_beside"] == 451.60893 and rows
