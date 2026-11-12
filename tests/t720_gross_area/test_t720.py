"""T-720 gross / covered floor area (R-T720-1 .. -5): a non-Alsenan hand-calculated villa, adverse cases, and the
development-villa build pinned to its own drawing read (no private file needed)."""
import json
import math
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t720"))
import t720_rules as R  # noqa: E402


def _bay_house(n=720):
    """12 x 10 m house, its east face x = 12 broken by a concave curved glazing bay: circle centre (13, 5), r 2 m.
    Hand: the circle meets x = 12 at y = 5 +- sqrt(3); the bay is the circular segment beyond the chord,
    theta = 120 deg, segment = r^2 / 2 (theta - sin theta) = 2 (2.094395 - 0.866025) = 2.456739 m2 -> 117.543261 m2."""
    y0, y1 = 5 - math.sqrt(3), 5 + math.sqrt(3)
    ring = [(0, 0), (12, 0), (12, y0)]
    a0, a1 = math.radians(240), math.radians(120)          # from the south chord end, westward round to the north end
    for k in range(1, n):
        a = a0 + (a1 - a0) * k / n
        ring.append((13 + 2 * math.cos(a), 5 + 2 * math.sin(a)))
    ring += [(12, y1), (12, 10), (0, 10)]
    return ring


HAND_BAY = 120 - 2 * (2 * math.pi / 3 - math.sin(2 * math.pi / 3))


def test_normal_curved_external_wall_hand_calc():
    g = R.gross([{"id": "house", "kind": "BUILDING", "ring": _bay_house()}])
    assert g["state"] == "DRAWING-CONFIRMED"
    assert g["gross_m2"] == pytest.approx(HAND_BAY, abs=2e-4)
    assert HAND_BAY == pytest.approx(117.543261, abs=1e-6)


def test_adverse_mirror_rotation_units():
    ring = _bay_house()
    mirrored = [(-x, y) for x, y in ring]
    rotated = [(-y, x) for x, y in ring]
    mm = [(x * 1000, y * 1000) for x, y in ring]
    a = R.gross([{"id": "h", "kind": "BUILDING", "ring": ring}])["gross_m2"]
    assert R.gross([{"id": "h", "kind": "BUILDING", "ring": mirrored}])["gross_m2"] == pytest.approx(a, abs=1e-9)
    assert R.gross([{"id": "h", "kind": "BUILDING", "ring": rotated}])["gross_m2"] == pytest.approx(a, abs=1e-9)
    assert R.gross([{"id": "h", "kind": "BUILDING", "ring": mm}])["gross_m2"] / 1e6 == pytest.approx(a, abs=1e-9)


def test_adverse_missing_outline_is_held_never_zero():
    g = R.gross([{"id": "house", "kind": "BUILDING", "ring": _bay_house()},
                 {"id": "annex", "kind": "BUILDING", "ring": None}])
    assert g["state"] == "HELD" and g["gross_m2"] is None
    assert [r["state"] for r in g["rows"]] == ["DRAWING-CONFIRMED", "HELD"]
    assert R.reconcile(None, 100.0, [])["state"] == "HELD"


def test_symbol_never_floor_area_and_components_add():
    annex = [(-8, 0), (-2, 0), (-2, 5), (-8, 5)]                        # 30 m2, separate component
    arrow = [(3, 20), (4, 20), (3.5, 21)]                               # closed figure of a north arrow
    g = R.gross([{"id": "house", "kind": "BUILDING", "ring": _bay_house()},
                 {"id": "annex", "kind": "BUILDING", "ring": annex},
                 {"id": "north arrow", "kind": "SYMBOL", "ring": arrow}])
    assert g["gross_m2"] == pytest.approx(HAND_BAY + 30.0, abs=2e-4)
    assert g["rows"][2]["state"] == "EXCLUDED" and g["rows"][2]["m2"] is None


def test_court_open_to_sky_and_cover_counted_once():
    plot = [(-10, -2), (20, -2), (20, 16), (-10, 16)]                   # 540 m2 to the boundary outer face
    house = [(0, 0), (12, 0), (12, 10), (0, 10)]                        # 120
    upper = [(-2, 0), (12, 0), (12, 10), (-2, 10)]                      # overhangs 2 m west: 20 m2 over the ground
    slab = [(-3, 0), (0, 0), (0, 10), (-3, 10)]                         # canopy outline overlapping the overhang
    c = R.cover(plot, [upper], slabs=[{"id": "canopy", "ring": slab}], lower_envelope_rings=[house])
    assert c["COVERED_BY_FLOOR"] == pytest.approx(20.0)
    assert c["COVERED_BY_SLAB"] == pytest.approx(10.0)                  # 30 - 20 already under the floor: once
    assert c["OPEN_TO_SKY"] == pytest.approx(540 - 120 - 20 - 10)
    # a court with nothing over it is all open to sky
    c2 = R.cover(plot, [], lower_envelope_rings=[house])
    assert c2["OPEN_TO_SKY"] == pytest.approx(420.0) and c2["COVERED_BY_FLOOR"] == 0


def test_adverse_slab_without_outline_holds_open_area():
    plot = [(-10, -2), (20, -2), (20, 16), (-10, 16)]
    house = [(0, 0), (12, 0), (12, 10), (0, 10)]
    c = R.cover(plot, [], slabs=[{"id": "balcony", "ring": None}], lower_envelope_rings=[house])
    assert c["OPEN_TO_SKY"] is None and c["held"] == ["balcony"]
    assert c["open_to_sky_upper_bound_m2"] == pytest.approx(420.0)


def test_passage_rule():
    assert R.passage(thresholds=2) == "OUTSIDE_ENVELOPE"
    assert R.passage(thresholds=1, doors=1) == "INSIDE_ENVELOPE"
    with pytest.raises(ValueError):
        R.passage(thresholds=0)


def test_reconcile_named_vs_unnamed():
    ok = R.reconcile(100.0, 105.88, [("passage closed by thresholds", -5.88)])
    assert ok["state"] == "RESIDUAL_NAMED" and ok["accept"]
    bad = R.reconcile(100.0, 101.0, [])
    assert bad["state"] == "RESIDUAL_UNNAMED" and not bad["accept"]       # 1 % unnamed fails
    small = R.reconcile(100.0, 100.2, [])
    assert small["state"] == "RESIDUAL_UNNAMED" and small["accept"]       # 0.2 % unnamed passes, still listed
    assert R.reconcile(100.0, 100.001, [])["state"] == "BALANCED"


def test_invalid_outline_refused():
    with pytest.raises(ValueError):
        R.gross([{"id": "bow", "kind": "BUILDING", "ring": [(0, 0), (1, 1), (1, 0), (0, 1)]}])


# ---- development villa (pinned own read; no private file needed) -------------------------------------------------------
HERE = ROOT / "research" / "agents_t720"


def test_alsenan_build_identical_and_values():
    r = subprocess.run([sys.executable, "-I", str(HERE / "t720_alsenan.py"), "--check"], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    o = json.loads((HERE / "out" / "T720_GROSS.json").read_text())
    g = {f["floor"]: f for f in o["floors"]}
    assert g["GF"]["gross_m2"] == pytest.approx(278.266291, abs=1e-6)
    assert g["1F"]["gross_m2"] == pytest.approx(209.839104, abs=1e-6)
    assert g["2F"]["gross_m2"] == pytest.approx(55.08, abs=1e-6)
    for f in o["floors"]:
        assert f["reconcile"]["state"] in ("BALANCED", "RESIDUAL_NAMED") and f["reconcile"]["accept"]
        assert abs(f["reconcile"]["residual_m2"]) <= R.TOL_M2
    assert all(abs(x["diff_mm"]) < 0.5 for x in o["printed_dims"])
    assert o["gf_ground"]["OPEN_TO_SKY_m2"] is None                       # slab projections held, not 0


def test_alsenan_drawn_has_no_coordinates_or_text():
    raw = (HERE / "T720_DRAWN.json").read_text()
    d = json.loads(raw)
    assert not any(k in raw for k in ('"pts"', '"polygon"', '"point"', '"corners"'))
    assert all(ord(ch) < 128 for ch in raw)                              # no drawing text (Arabic) copied
    assert set(d["outlines"]) == {"GF_MAIN", "GF_ANNEX", "GF_PASSAGE", "PLOT", "1F", "2F"}
