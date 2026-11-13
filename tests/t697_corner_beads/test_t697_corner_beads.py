"""T-697: corner bead ledger (B4-09) bound to the candidate. Non-Alsenan villa E697 by hand (normal + adverse), then the
development-villa ledger pinned on committed merged inputs (V3.0.68 index)."""

import csv
import importlib.util
import io
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HERE = os.path.join(ROOT, "research", "agents_t697")


def _load(name):
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


R = _load("t697_rules")
A = _load("t697_alsenan")

# Villa E697 (hand): ground floor finish +0.60, first-floor slab soffit +4.70 -> soffit height 4.10 above the floor
# finish; owner finished ceiling 3.40 (an E697 owner value, not the development villa's). Bedroom B1 has a column
# 0.40 wide standing 0.08 proud of the east wall (2 arrises), a door 0.90 x 2.20 to the hall (both faces plastered),
# a door 0.80 x 2.20 to the bathroom (bathroom face tiled), a window with its frame flush with the room face, and a
# stair landing drawn HIDDEN over the hall column whose soffit is +3.75 .. +3.85 (build-up 0 .. 0.10 not printed).
E_G1, E_SOFFIT = 3.40, 4.10
INDEX = {
    "L-B1": {"item_code": "FIN.PLASTER", "class": "HELD"},
    "L-HALL": {"item_code": "FIN.PLASTER", "class": "RELEASED"},
    "L-TILE": {"item_code": "FIN.WALL.TILE", "class": "RELEASED"},
    "L-STEEL": {"item_code": "STR.REBAR", "class": "RELEASED"},
}


def test_column_arrises_owner_and_drawing_side_by_side():
    own, lo, hi, rule = R.exposed_vertical(E_G1, E_SOFFIT)
    assert (own, lo, hi, rule) == (3.40, 3.40, 4.10, "R-T697-1")
    assert R.q4(2 * own) == 6.80 and R.q4(2 * hi) == 8.20       # 2 arrises: 6.80 owner, 6.80 .. 8.20 drawing


def test_door_two_plastered_faces_count_two_rings():
    assert R.opening_ring(0.90, 2.20, plastered_sides=2) == 10.60   # (2 x 2.20 + 0.90) x 2


def test_adverse_tiled_jamb_gets_no_bead():
    # bathroom door: only the bedroom face is plastered; the tiled face is the tile family's (B4-10)
    assert R.opening_ring(0.80, 2.20, plastered_sides=1) == 5.20
    ex = R.exclusion("B4-10", "L-TILE")
    assert ex["status"] == "NOT_APPLICABLE" and ex["owning_line"] == "L-TILE"
    with pytest.raises(R.BeadRuleError):
        R.exclusion("B4-10", "")


def test_flush_window_side_has_no_arris():
    assert R.opening_ring(1.20, 1.50, plastered_sides=1, flush_sides=1) == 0.0


def test_adverse_arris_under_a_landing_stops_at_its_soffit():
    # hall column under the landing: soffit +3.75 .. +3.85 - 0.60 floor = 3.15 .. 3.25 above the floor, below G1 3.40
    own, lo, hi, rule = R.exposed_vertical(E_G1, E_SOFFIT, overhead=(3.15, 3.25))
    assert own is None and (lo, hi) == (3.15, 3.25) and rule == "R-T697-2"
    # an overhead element above the ceiling changes nothing
    assert R.exposed_vertical(E_G1, E_SOFFIT, overhead=(3.80, 3.90))[0] == 3.40


def test_adverse_heights_missing_inverted_or_mixed_units_refused():
    with pytest.raises(R.BeadRuleError):
        R.exposed_vertical(None, E_SOFFIT)                 # missing height is never borrowed
    with pytest.raises(R.BeadRuleError):
        R.exposed_vertical(3400.0, E_SOFFIT)               # G1 in mm against a soffit in m: ceiling above soffit
    with pytest.raises(R.BeadRuleError):
        R.opening_ring(0.90, None, 2)


def test_shaft_band_arrises_from_pier_returns():
    assert R.shaft_band_arrises(0.40, 0.40, 0.08) == (5.0, 5.0)    # two returns, 0.40 m2 at depth 0.08 -> 5.00 m.l
    with pytest.raises(R.BeadRuleError):
        R.shaft_band_arrises(0.40, 0.40, 0)


def test_binding_one_host_two_hosts_absent_wrong_code():
    assert R.bind(["L-B1"], INDEX) == ("BOUND", "L-B1")
    assert R.bind(["L-B1", "L-HALL"], INDEX) == ("BINDING_OPEN", "L-B1 | L-HALL")
    with pytest.raises(R.BeadRuleError):
        R.bind(["L-GONE"], INDEX)
    with pytest.raises(R.BeadRuleError):
        R.bind(["L-STEEL"], INDEX)


def _row(**kw):
    base = {"edge_id": "B1#V1", "status": "ASSUMED — OWNER-APPROVED", "owner_m": 3.40, "binding": "BOUND",
            "held_low": "", "held_high": "", "cause": "x"}
    base.update(kw)
    return base


def test_adverse_held_as_zero_unbound_duplicate_refused():
    with pytest.raises(R.BeadRuleError):
        R.check_row(_row(status="HELD", owner_m=0.0))
    with pytest.raises(R.BeadRuleError):
        R.check_row(_row(status="HELD", owner_m="", held_low=0.0, held_high=0.0))
    with pytest.raises(R.BeadRuleError):
        R.check_row(_row(binding="NO_HOST"))
    with pytest.raises(R.BeadRuleError):
        R.check_row(_row(owner_m=""))
    with pytest.raises(R.BeadRuleError):
        R.check_ledger([_row(), _row()])
    assert R.check_row(_row(status="HELD", owner_m="", held_low=0.0, held_high=1.2))


def test_villa_e697_total_by_hand():
    rows = [_row(edge_id="B1#COL", owner_m=6.80, dwg_low=6.80, dwg_high=8.20),
            _row(edge_id="B1#D1", owner_m=10.60, status="DRAWING-CONFIRMED"),
            _row(edge_id="B1#D2", owner_m=5.20),
            _row(edge_id="HALL#COL", status="HELD", owner_m="", held_low=6.30, held_high=6.50),
            {"edge_id": "B1#D2-TILE", "status": "NOT_APPLICABLE", "owner_trade": "B4-10"}]
    t = R.totals(rows)
    assert t["owner_measured_m"] == 22.60 and t["drawing_high_m"] == 24.00
    assert (t["held_bounded_low_m"], t["held_bounded_high_m"]) == (6.30, 6.50)


# ---- development villa, committed merged inputs ------------------------------------------------------------------

@pytest.fixture(scope="module")
def built():
    rows, idx = A.build()
    return rows, idx, A.summarise(rows, idx)


def test_every_counted_arris_bound_to_a_candidate_plaster_line(built):
    rows, idx, _ = built
    index = {l["line_id"]: l for l in idx["lines"]}
    assert idx["candidate_version"] == "ARCH_TAKEOFF_V3.0.68"
    counted = [r for r in rows if r["status"] in ("ASSUMED — OWNER-APPROVED", "DRAWING-CONFIRMED")]
    for r in counted:
        assert r["binding"] in ("BOUND", "BINDING_OPEN"), r["edge_id"]
        for h in r["host_line"].split(" | "):
            assert h in index and index[h]["item_code"] in R.PLASTER_HOST_CODES, (r["edge_id"], h)
    assert [r["edge_id"] for r in counted if r["binding"] == "BINDING_OPEN"] == ["D-1F-02#1F-13|ST-1F"]


def test_development_villa_totals(built):
    _, _, s = built
    assert s["interior"]["owner_measured_m"] == 285.03            # 275.95 - 2 x 3.65 + 8.46 + 7.92
    assert s["interior"]["drawing_high_m"] == 308.71               # + 37 corners x (soffit - G1) 23.68
    assert (s["interior"]["held_bounded_low_m"], s["interior"]["held_bounded_high_m"]) == (14.4528, 14.8528)
    assert s["exterior"]["owner_measured_m"] == 310.6831           # T-405 exterior unchanged
    assert s["t405_measured_m"] == {"interior": 275.95, "exterior": 310.6831}


def test_v61_is_held_under_the_landing_not_dropped(built):
    rows, _, _ = built
    v = {r["edge_id"]: r for r in rows}
    for e in ("GF-08#V60", "GF-08#V61"):
        assert v[e]["status"] == "HELD" and v[e]["owner_m"] == ""
        assert (v[e]["held_low"], v[e]["held_high"]) == (3.4364, 3.5364)
    assert v["GF-08#V62"]["owner_m"] == 3.65


def test_lift_entrances_owned_by_the_surround(built):
    rows, idx, _ = built
    index = {l["line_id"]: l for l in idx["lines"]}
    lifts = [r for r in rows if r["edge_id"].startswith("LIFT#")]
    assert len(lifts) == 3
    for r in lifts:
        assert r["status"] == "NOT_APPLICABLE" and r["owner_trade"] == "B6-06"
        assert index[r["owning_line"]]["item_code"] == "FIN.MARBLE.LIFT_SURROUND"


def test_no_bead_host_carries_a_wall_tile_line(built):
    rows, idx, _ = built
    tile_polys = {l["element_id"].split(":")[0].split("#")[0] for l in idx["lines"] if l["item_code"] == "FIN.WALL.TILE"}
    index = {l["line_id"]: l for l in idx["lines"]}
    for r in rows:
        if r["status"] in ("ASSUMED — OWNER-APPROVED", "DRAWING-CONFIRMED") and r["scope"] == "INTERIOR":
            for h in r["host_line"].split(" | "):
                assert index[h]["element_id"].split(":")[0] not in tile_polys, (r["edge_id"], h)


def test_committed_outputs_reproduce(built):
    rows, _, s = built
    csv_txt, js = A.render(rows, s)
    assert open(os.path.join(HERE, "out", "T697_BEAD_LEDGER.csv"), encoding="utf-8").read() == csv_txt
    assert json.loads(open(os.path.join(HERE, "out", "T697_SUMMARY.json"), encoding="utf-8").read()) == json.loads(js)
    assert len(list(csv.DictReader(io.StringIO(csv_txt)))) == s["rows"]
