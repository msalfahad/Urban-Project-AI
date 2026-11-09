"""T-522: the HELD parts of an exposed-slab WP zone (window run under a sill, a covered ledge and its bounding face)
measured from printed evidence or narrowed (research/agents_t522/t522_ledge_window.py, R-T522-1 .. 4). Synthetic
villa "Q522" (not the training villa), hand calculations; adverse cases; then the development villa from the private
drawing (skipped when it is absent)."""
from __future__ import annotations

import math
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t522"))
from engine.source import wp_applicability_rules_v1 as W  # noqa: E402
import t522_ledge_window as L  # noqa: E402

SRC = {"drawing": "Q522 A-201", "view": "section 2-2", "dimension": "D-17"}

# ---- villa "Q522" (hand-drawn, metres): a 3.00 x 0.40 ledge printed at +0.15 in front of a house wall (x = 0), open to
# the sky, a 1.00 m window in the wall with its sill printed 0.90 above the ledge, the wall face 2.00 m solid; the
# detail prints a 0.15 m upturn. Hand: membrane 3.00 x 0.40 = 1.200 m2; upturn (2.00 + 1.00) x 0.15 = 0.450 m2
# (UP-WP-003 default would be 3.00 x 0.20 = 0.600 m2).


def q_zone(sill=0.90, src=SRC, exposure=W.EXPOSED):
    return {"zone_id": "Q522-LEDGE", "exposure": exposure, "doors": 0, "membrane_m2": 1.2,
            "upturn_runs": [{"run": "wall", "lm": 2.0, "kind": "WALL"},
                            L.window_run("window", 1.0, sill, src if sill is not None else None)],
            "doorways": [], "open_edge_lm": 3.0, "void_edge_lm": None, "carried": [], "outlet_printed": True}


def _by(rows, comp, run=None):
    return [r for r in rows if r["component"] == comp and (run is None or r.get("run") == run)]


def test_normal_printed_ledge_and_upturn_by_hand():
    rows = L.apply_printed_upturn(W.component_rows(q_zone()), 0.15, SRC)
    assert _by(rows, "FLAT_MEMBRANE")[0]["qty"] == pytest.approx(1.200, abs=1e-9)
    ups = _by(rows, "UPTURN")
    assert [r["status"] for r in ups] == [W.MEASURED, W.MEASURED]
    assert sum(r["qty"] for r in ups) == pytest.approx(0.450, abs=1e-9)
    assert all(r["height_m"] == 0.15 and r["height_replaced_m"] == 0.20 and r["height_source"] == SRC for r in ups)


def test_default_upturn_without_detail_is_up_wp_003():
    assert L.UPTURN_H_M == W.UPTURN_H_M == 0.20
    rows = L.apply_printed_upturn(W.component_rows(q_zone()), None)
    assert sum(r["qty"] for r in _by(rows, "UPTURN")) == pytest.approx(0.600, abs=1e-9)


def test_adverse_nothing_printed_is_held_with_bound_never_zero():
    rows = W.component_rows(q_zone(sill=None))
    w = _by(rows, "UPTURN", "window")[0]
    assert w["status"] == W.HELD and w["qty"] is None and w["held_bound"] == pytest.approx(0.2)
    assert "sill" in w["held_reason"]


def test_adverse_sill_without_source_refused_and_mm_refused():
    with pytest.raises(ValueError):
        L.window_run("w", 1.0, 0.90, None)
    with pytest.raises(ValueError):
        L.window_run("w", 1.0, 0.90, {"drawing": "x", "view": "", "dimension": "d"})
    with pytest.raises(ValueError):
        L.window_run("w", 1.0, 900.0, SRC)          # millimetres entered as metres
    with pytest.raises(ValueError):
        L.apply_printed_upturn(W.component_rows(q_zone()), 0.15, None)
    with pytest.raises(ValueError):
        L.apply_printed_upturn(W.component_rows(q_zone()), 150.0, SRC)


def test_low_sill_is_transition_not_upturn():
    rows = W.component_rows(q_zone(sill=0.10))
    assert not _by(rows, "UPTURN", "window")
    t = _by(rows, "WINDOW_TRANSITION", "window")[0]
    assert t["status"] == W.HELD and t["held_bound"] == pytest.approx(1.0) and t["unit"] == "lm"


# ---- bounding face split (R-T522-2): a 3.00 m bay face = 0.50 solid + 2.00 glazing on the slab + 0.50 solid --------
PIECES = [{"piece": "a", "lm": 0.5, "stands": "SOLID"},
          {"piece": "g", "lm": 2.0, "stands": "GLAZING_ON_SLAB", "source": SRC},
          {"piece": "b", "lm": 0.5, "stands": "SOLID"}]


def test_face_split_on_exposed_ledge_by_hand():
    runs, na, rec = L.split_face("bay", 3.0, PIECES)
    assert rec["residual_lm"] == 0.0 and not na
    z = dict(q_zone(), upturn_runs=runs)
    rows = W.component_rows(z)
    assert sum(r["qty"] for r in _by(rows, "UPTURN")) == pytest.approx(1.0 * 0.20)
    t = _by(rows, "WINDOW_TRANSITION")
    assert len(t) == 1 and t[0]["held_bound"] == pytest.approx(2.0) and t[0]["status"] == W.HELD


def test_face_split_on_covered_ledge_stays_held():
    runs, _, _ = L.split_face("bay", 3.0, PIECES)
    rows = W.component_rows(dict(q_zone(exposure=W.COVERED_OPEN_SIDE), upturn_runs=runs))
    m = _by(rows, "FLAT_MEMBRANE")[0]
    assert m["status"] == W.HELD and m["qty"] is None and m["held_bound"] == pytest.approx(1.2)
    assert all(r["status"] == W.HELD and r["qty"] is None for r in rows)
    assert sum(r["held_bound"] for r in _by(rows, "UPTURN")) == pytest.approx(0.20)


def test_window_on_kerb_needs_section_and_is_not_applicable():
    k = [{"piece": "g", "lm": 2.0, "stands": "GLAZING_ON_KERB", "kerb_m": 0.25, "source": SRC}]
    runs, na, _ = L.split_face("bay", 2.0, k)
    assert runs == [{"run": "bay:g:kerb_face", "lm": 2.0, "kind": "SOLID"}]
    assert na[0]["status"] == "NOT_APPLICABLE" and na[0]["source"] == SRC and na[0]["qty"] == 0.0
    with pytest.raises(ValueError):
        L.split_face("bay", 2.0, [{"piece": "g", "lm": 2.0, "stands": "GLAZING_ON_KERB", "kerb_m": 0.25}])
    low = [{"piece": "g", "lm": 2.0, "stands": "GLAZING_ON_KERB", "kerb_m": 0.10, "source": SRC}]
    runs, na, _ = L.split_face("bay", 2.0, low)
    assert not na and runs[0]["kind"] == "UNDER_WINDOW" and runs[0]["sill_above_slab_m"] == 0.10


def test_adverse_face_split_refusals():
    with pytest.raises(ValueError):                       # glazing on the slab without the elevation / section
        L.split_face("bay", 2.0, [{"piece": "g", "lm": 2.0, "stands": "GLAZING_ON_SLAB"}])
    with pytest.raises(ValueError):                       # pieces do not reconcile to the run
        L.split_face("bay", 3.2, PIECES)
    with pytest.raises(ValueError):                       # piece not measured
        L.split_face("bay", 0.0, [{"piece": "a", "lm": None, "stands": "SOLID"}])
    with pytest.raises(ValueError):
        L.split_face("bay", 1.0, [{"piece": "a", "lm": 1.0, "stands": "GUESS"}])


# ---- covered strip (R-T522-4): 3.00 x 0.40 strip behind a straight cover edge, clear height 3.00 --------------------
def _strip(mirror=False, rot=False):
    from shapely import affinity
    from shapely.geometry import LineString, Polygon
    s, e = Polygon([(-0.4, 0), (0, 0), (0, 3), (-0.4, 3)]), LineString([(0, -50), (0, 50)])
    if mirror:
        s, e = affinity.scale(s, -1, 1, origin=(0, 0)), affinity.scale(e, -1, 1, origin=(0, 0))
    if rot:
        s, e = affinity.rotate(s, 37, origin=(1, 1)), affinity.rotate(e, 37, origin=(1, 1))
    return s, e


def test_covered_strip_narrowing_by_hand():
    s, e = _strip()
    x = L.covered_strip_exposure(s, e, 3.0, angles_deg=(0.0, 5.0, 10.0))
    assert x["d_max_m"] == pytest.approx(0.40) and x["area_m2"] == pytest.approx(1.2)
    assert x["theta_c_deg"] == pytest.approx(math.degrees(math.atan(0.4 / 3.0)), abs=1e-4)   # 7.5946 deg
    t = {r["theta_deg"]: r["wetted_m2"] for r in x["table"]}
    assert t[0.0] == 0.0 and t[5.0] == pytest.approx(3.0 * 3.0 * math.tan(math.radians(5)), abs=1e-6)  # 0.787398
    assert t[10.0] == pytest.approx(1.2)
    assert x["status"] == "HELD" and x["never_a_quantity"] is True


def test_covered_strip_mirror_rotation_invariant_and_refusals():
    base = L.covered_strip_exposure(*_strip(), 3.0)
    for m, r in ((True, False), (False, True), (True, True)):
        o = L.covered_strip_exposure(*_strip(m, r), 3.0)
        assert o["theta_c_deg"] == pytest.approx(base["theta_c_deg"], abs=1e-6)
        assert [a["wetted_m2"] for a in o["table"]] == pytest.approx([a["wetted_m2"] for a in base["table"]], abs=1e-6)
    s, e = _strip()
    with pytest.raises(ValueError):
        L.covered_strip_exposure(s, e, None)
    with pytest.raises(ValueError):
        L.covered_strip_exposure(s.buffer(-1.0), e, 3.0)


# ---- development villa (private drawing; skipped when absent) -------------------------------------------------------
def _dxf():
    p = os.environ.get("T486_DXF")
    for c in (p, str(ROOT.parent / "private" / "P7757_DXF_COMPRESSED" / "P7757.dxf"),
              str(ROOT.parent / "private" / "P7757" / "P7757.dxf")):
        if c and os.path.exists(c):
            return c
    return None


@pytest.mark.skipif(_dxf() is None, reason="private drawing absent")
def test_development_villa():
    import t522_alsenan as X
    r = X.build(_dxf())
    c = r["window_checks"]
    assert c["sill_printed_cm"] == "84" and c["sill_from_slab_top_mm"] == 0.0 and c["width_printed_cm"] == "50"
    assert r["sill_m"] == 0.84
    w = [x for x in r["rows_open_sky"] if x.get("run") == "window_face"][0]
    assert w["status"] == W.MEASURED and w["length_lm"] == pytest.approx(0.500002) and w["qty"] == pytest.approx(0.1)
    assert r["bay_reconciliation"]["residual_lm"] == 0.0
    assert abs(r["bay_pieces"][1]["chord_m"] - c["bay_chord_measured_m"]) < 0.001        # '269' = BCE chord
    e = r["effect"]
    assert e["FIN.WP.ROOF_UPTURN_valued_lm"]["after"] == pytest.approx(187.282546)
    assert e["ledge_upturn"]["after_upturn_bound_lm"] == pytest.approx(0.551615)
    assert e["ledge_upturn"]["after_transition_lm"] == pytest.approx(2.976663)
    m = [x for x in r["rows_ledge"] if x["component"] == "FLAT_MEMBRANE"][0]
    assert m["status"] == W.HELD and m["qty"] is None and m["held_bound"] == pytest.approx(0.639573)
    assert r["exposure"][4.2]["d_max_m"] == pytest.approx(0.75, abs=1e-4)
    assert r["exposure"][4.2]["theta_c_deg"] == pytest.approx(10.1247, abs=1e-3)
