"""T-372 research part: B9-04 perimeter joint mortar bound to the V3.0.63 black-block mortar lines (R-T372-1).

Hand fixture (not the development villa), joint 10 mm, face 0.39 x 0.19 on a 0.40 x 0.20 module,
kappa = 0.0741 / 0.08 = 0.92625:
 - wall A, 0.20 m, 4.00 m between two RC columns, 3.00 m under a beam soffit, one uncredited top corner:
   f = 0.92625 x 0.20 x 0.01 = 0.0018525 m3/m; (4.00 + 3.00 - 0.01) x 0.0018525 = 0.012948975 m3;
 - wall B, 0.15 m, 2.50 m under a soffit, both ends block-to-block (butt or bonded, 2.80 m of course band):
   f = 0.001389375; low 2.50 f = 0.0034734375, high + 2.80 f = 0.0073636875 m3;
 - lintel over a 1.00 m opening, 0.40 m bearing each end: one end 1.20 m of block (EXACT 0.40), the other end 0.08 m
   to a column (DEFICIT): 0.40 + [0, 0.08] m -> 0.15 m wall f x [0.40, 0.48] = 0.00055575 .. 0.00066690 m3.
"""
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("t372", ROOT / "research/agents_t372/t372_perimeter_ledger.py")
T = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(T)

FACE, MOD, J = (0.39, 0.19), (0.40, 0.20), 0.01


def line(lid, host, cls="RELEASED", net=None, after=("VALUE", 1.0)):
    return {"line_id": lid, "host_line_id": host, "host": f"X-WALLS:walls t=0.20#{host}", "host_class": cls,
            "host_net_m2": net, "after": list(after)}


def wall(wid, host, area, low, high=None, fig=None, status="COMPUTED", in_host=True):
    return {"wall_id": wid, "host_line_id": host, "area_m2": area, "in_host": in_host, "low": low,
            "figure": low if fig is None else fig, "high": low if high is None else high, "status": status,
            "held_why": "", "expression": "", "held_bands": 0, "held_pieces": ""}


# ------------------------------------------------------------------------------------------------ fixture
def test_factor_by_hand():
    assert T.factor(0.20, FACE, MOD, J) == pytest.approx(0.0018525, abs=1e-12)
    assert T.factor(0.15, FACE, MOD, J) == pytest.approx(0.001389375, abs=1e-12)


def test_wall_a_exact_by_hand():
    f = T.factor(0.20, FACE, MOD, J)
    assert T.wall_exact(4.00, 3.00, 1, f, J) == pytest.approx(0.012948975, abs=1e-12)


def test_wall_b_range_by_hand():
    f = T.factor(0.15, FACE, MOD, J)
    lo = T.wall_exact(2.50, 0.0, 0, f, J)
    assert lo == pytest.approx(0.0034734375, abs=1e-12)
    assert lo + 2.80 * f == pytest.approx(0.0073636875, abs=1e-12)


def test_bind_normal_two_lines():
    lines = [line("M1", "H1", net=12.0), line("M2", "H2", net=7.0)]
    walls = [wall("A", "H1", 12.0, 0.012949), wall("B", "H2", 7.0, 0.003473, 0.007364, status=T.STATUS_015)]
    rows = {r["line_id"]: r for r in T.bind(lines, walls)}
    assert rows["M1"]["state"] == "VALUE" and rows["M1"]["low"] == 0.012949
    assert rows["M2"]["state"] == "RANGE" and rows["M2"]["range_part"] == pytest.approx(0.003891, abs=1e-9)
    # the panel figure is carried untouched beside (never summed with the perimeter)
    assert rows["M1"]["panel_after"] == ["VALUE", 1.0]


def test_mirror_order_invariant():
    lines = [line("M1", "H1", net=10.0)]
    w = [wall("A", "H1", 4.0, 0.001), wall("B", "H1", 6.0, 0.002, 0.003)]
    a = T.bind(lines, w)[0]
    b = T.bind(lines, list(reversed(w)))[0]
    assert (a["low"], a["high"]) == (b["low"], b["high"]) == (0.003, 0.004)


def test_held_host_blank_never_zero():
    rows = T.bind([line("M1", "H1", cls="HELD", after=("HELD", None))], [wall("A", "H1", 5.0, 0.004)])
    r = rows[0]
    assert r["state"] == "HELD" and r["low"] is None and r["high"] is None
    assert [w["wall_id"] for w in r["beside_held_walls"]] == ["A"]


def test_wall_outside_host_area_goes_beside():
    rows = T.bind([line("M1", "H1", net=5.0)], [wall("A", "H1", 5.0, 0.002), wall("C", "H1", 3.0, 0.001,
                                                                                   in_host=False)])
    assert rows[0]["low"] == 0.002 and [w["wall_id"] for w in rows[0]["beside_held_walls"]] == ["C"]


def test_refuse_white_or_missing_host():
    with pytest.raises(T.T372Error, match="no MAS.MORTAR.BLACK line"):
        T.bind([line("M1", "H1", net=5.0)], [wall("A", "H9", 5.0, 0.002)])


def test_refuse_wall_twice():
    with pytest.raises(T.T372Error, match="bound twice"):
        T.bind([line("M1", "H1", net=5.0)], [wall("A", "H1", 2.5, 0.001), wall("A", "H1", 2.5, 0.001)])


def test_refuse_area_mismatch():
    with pytest.raises(T.T372Error, match="!= host"):
        T.bind([line("M1", "H1", net=5.0)], [wall("A", "H1", 4.9, 0.002)])


def test_refuse_missing_figure_on_released_host():
    with pytest.raises(T.T372Error, match="never 0"):
        T.bind([line("M1", "H1", net=5.0)], [wall("A", "H1", 5.0, None)])


def test_refuse_two_lines_one_host():
    with pytest.raises(T.T372Error, match="two"):
        T.bind([line("M1", "H1", net=5.0), line("M2", "H1", net=5.0)], [])


def test_bearing_end_classes():
    assert T.bearing_end(1.20, "END_OF_MASONRY") == {"state": "EXACT", "low": 0.40, "high": 0.40,
                                                       "why": "available >= bearing"}
    c = T.bearing_end(0.08, "COLUMN")
    assert (c["state"], c["low"], c["high"]) == ("RANGE", 0.0, 0.08)
    m = T.bearing_end(0.25, "END_OF_MASONRY")
    assert (m["state"], m["low"], m["high"]) == ("RANGE", 0.0, 0.40)
    assert T.bearing_end(None, "COLUMN")["state"] == "HELD"
    with pytest.raises(T.T372Error):
        T.bearing_end(-0.01, "COLUMN")


def test_lintel_bed_fixture_and_mirror():
    f = T.factor(0.15, FACE, MOD, J)
    a = T.lintel_bearing_bed("L1", [("START", 1.20, "END_OF_MASONRY"), ("END", 0.08, "COLUMN")], f)
    b = T.lintel_bearing_bed("L1", [("END", 1.20, "END_OF_MASONRY"), ("START", 0.08, "COLUMN")], f)
    assert a["state"] == "RANGE" and (a["bearing_low_m"], a["bearing_high_m"]) == (0.40, 0.48)
    assert a["low"] == pytest.approx(0.000556, abs=1e-6) and a["high"] == pytest.approx(0.000667, abs=1e-6)
    assert (a["low"], a["high"]) == (b["low"], b["high"])
    assert T.lintel_bearing_bed("L2", [("START", 1.0, "COLUMN")], f)["state"] == "HELD"


def test_materials_own_key():
    m = T.materials(0.1, 0.2, 8.0, 1.1)
    assert m["producer_key"].startswith("B9-04 PERIMETER")
    assert m["cement_bags_50kg"] == [0.8, 1.6] and m["sand_m3_loose"] == [0.11, 0.22]


# ------------------------------------------------------------------------------------------------ development villa pins
@pytest.fixture(scope="module")
def res():
    return T.build()


def test_reproduces_stored_ledger(res):
    stored = json.loads((ROOT / "research/agents_t372/out/T372_PERIMETER_LEDGER.json").read_text(encoding="utf-8"))
    assert stored == json.loads(json.dumps(res))


def test_index_second_path(res):
    assert res["index_check"] == {"lines_checked": 20, "mismatches": 0}


def test_every_mortar_line_once(res):
    assert len(res["lines"]) == 20 and len({r["mortar_line_id"] for r in res["lines"]}) == 20
    assert res["totals"]["lines_valued"] == 8 and res["totals"]["lines_held"] == 12


def test_totals_pinned(res):
    t = res["totals"]
    assert (t["low"], t["figure"], t["high"]) == (0.176727, 0.177283, 0.188035)
    assert t["by_t"]["0.20"] == {"lines": 2, "low": 0.098145, "high": 0.098145}
    assert t["by_t"]["0.15"] == {"lines": 6, "low": 0.078582, "high": 0.08989}
    assert t["panel_t670_valued"] == [3.211255, 3.215016]


def test_reconciles_to_t520_twenty_walls(res):
    # T-520 s.5: GF + 1F 20 walls 0.180867 .. 0.192179; the only one not in its host figure is GF-W22 (D-27)
    beside = [b for r in res["lines"] for b in r["beside_held"] if b["wall_id"] == "GF-W22"]
    assert len(beside) == 1
    lo, hi = beside[0]["figure_beside"]
    assert round(res["totals"]["low"] + lo, 6) == 0.180867 and round(res["totals"]["high"] + hi, 6) == 0.192179


def test_t615_equals_t520(res):
    assert len(res["t615_equals_t520"]) == 15 and max(e["max_diff"] for e in res["t615_equals_t520"]) == 0.0


def test_own_arithmetic_residuals_named(res):
    off = {x["wall_id"]: (x["d_low"], x["d_high"]) for x in res["own_arithmetic"]
           if abs(x["d_low"]) > 2e-6 or abs(x["d_high"]) > 2e-6}
    # GF-W22 high: soffit 2.9795 .. 2.9825 (D-27 area range, 0.003 m x f); GF-W28 / 1F-W23 low: one 0.20 m lintel
    # band (lintel reaching the column scenario of T-520) = 0.20 x 0.001389375 = 0.000278
    assert off == {"GF-W22": (0.0, -4e-06), "GF-W28": (0.000278, 0.0), "1F-W23": (0.000278, 0.0)}


def test_held_lines_have_cause_and_blank(res):
    for r in res["lines"]:
        if r["perimeter_state"] == "HELD":
            assert r["perimeter_low_m3"] is None and r["held_cause"]
        else:
            assert r["host_class"] == "RELEASED" and r["materials"]["producer_key"] == T.PRODUCER_KEY


def test_beside_components(res):
    t = res["totals"]
    assert t["lintel_bearing_bed_beside"] == {"lintels": 8, "held": 1, "low": 0.006113, "high": 0.008443}
    assert t["held_junction_bands_beside"]["bands"] == 23


def test_no_client_text(res):
    s = json.dumps(res)
    for bad in ("Alsenan", "alsenan", "chalet"):
        assert bad not in s


def test_trial_r4_overlay_reconciles(res):
    tr = res["trial_r4_reconcile"]
    assert len(tr) == 8 and all(x["residual_low"] == 0.0 for x in tr)
    by = {x["host_line_id"]: x for x in tr}
    # bounded companions agree; OPEN companions are exactly the hosts with named HELD pieces
    assert by["L-73acd5a9d7e7cf6515c1"]["trial_companion_high"] == by["L-73acd5a9d7e7cf6515c1"]["ledger_range_part"]
    assert by["L-abf15bdf70ccf1e7b474"]["trial_companion_high"] == by["L-abf15bdf70ccf1e7b474"]["ledger_range_part"]
    for h in ("L-a56a8add7812d1b52cb7", "L-4054259959463edd70fb"):
        assert by[h]["trial_companion_high"] is None and by[h]["ledger_open_named"]
    # F-T372-1: the two 0.20 m perimeter lines carry no evidence label in the trial
    assert sorted(x["host_line_id"] for x in tr if x["trial_evidence"] == "UNKNOWN") == \
        ["L-10dd62f66ad05488e63b", "L-1c53fadb2f92d1f36d4e"]
