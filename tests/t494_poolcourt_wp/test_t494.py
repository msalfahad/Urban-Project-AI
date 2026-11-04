"""T-494 B8-06 pool-court slab waterproofing: WP_APPLICABILITY_RULES_V1 (engine/source/wp_applicability_rules_v1.py)
and its component rows. Synthetic villa "R" (not the training villa) with hand calculations: normal case (an open
court slab round a void, a pier, a window, a parapet) and adverse cases (a covered ledge HELD and not added, covered =
not applicable, sill unknown / low, a door makes it a terrace, a roof line already carrying the surface, held never 0,
rotation / mirror / mm); then the development villa from the private drawing (skipped when it is absent)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t486"))
sys.path.insert(0, str(ROOT / "research" / "agents_t494"))
from engine.source import wp_applicability_rules_v1 as W  # noqa: E402
import t486_terrace_wp as T  # noqa: E402
import t486_alsenan as A  # noqa: E402

# ---- villa "R" (hand-drawn, metres): a 6.00 x 3.00 slab over an open court, house wall on the west (x = 0) with a
# 0.80 m window (sill 0.90 above the slab top) at y 2.0 .. 2.8, a 0.30 x 0.30 pier against the wall at y 1.0 .. 1.3,
# a parapet on the south (y = 0), open slab edges north and east, a 1.20 x 1.00 void through the slab.
SLAB = [(0, 0), (6, 0), (6, 3), (0, 3)]
PIER = [(0, 1), (0.3, 1), (0.3, 1.3), (0, 1.3)]
VOID = [(3, 1), (4.2, 1), (4.2, 2), (3, 2)]
OPEN = [[(0, 3), (6, 3), (6, 0)]]


def zone(**kw):
    z = {"zone_id": "R-COURT", "exposure": W.EXPOSED, "doors": 0, "membrane_m2": 16.71,
         "upturn_runs": [{"run": "wall", "lm": 1.9, "kind": "WALL"},
                         {"run": "window", "lm": 0.8, "kind": "UNDER_WINDOW", "sill_above_slab_m": 0.90},
                         {"run": "pier", "lm": 0.9, "kind": "SOLID"},
                         {"run": "parapet", "lm": 6.0, "kind": "PARAPET"}],
         "doorways": [], "open_edge_lm": 9.0, "void_edge_lm": 4.4, "carried": [], "outlet_printed": False}
    z.update(kw)
    return z


def by(rows, comp, run=None):
    return [r for r in rows if r["component"] == comp and (run is None or r.get("run") == run)]


def test_villa_r_geometry_by_hand():
    g = T.zone_geometry(SLAB, footprints=[PIER], openings=[VOID], open_edges=OPEN)
    # 18.00 - 0.09 pier - 1.20 void = 16.71 m2
    assert g["net_m2"] == pytest.approx(16.71)
    # upturn: wall 3.00 - 0.30 under the pier + pier faces 0.90 + parapet 6.00 = 9.60 lm (window run included)
    assert g["upturn_lm"] == pytest.approx(9.6)
    assert g["open_edge_lm"] == pytest.approx(9.0)
    assert g["opening_edge_lm"] == pytest.approx(4.4)


def test_normal_open_court_slab_rows():
    rows = W.component_rows(zone())
    flat = by(rows, "FLAT_MEMBRANE")[0]
    assert (flat["status"], flat["qty"], flat["family"]) == (W.MEASURED, pytest.approx(16.71), W.FAMILY_ROOF)
    ups = by(rows, "UPTURN")
    assert all(r["status"] == W.MEASURED for r in ups)
    assert sum(r["qty"] for r in ups) == pytest.approx(9.6 * 0.20)          # 1.92 m2
    edges = by(rows, "SLAB_EDGE_TERMINATION") + by(rows, "VOID_EDGE_TERMINATION")
    assert [(r["status"], r["qty"], r["held_bound"]) for r in edges] == [(W.HELD, None, 9.0), (W.HELD, None, 4.4)]
    rfi = by(rows, "DRAINAGE_FALLS")[0]
    assert rfi["status"] == W.RFI and rfi["blocks_quantity"] is False       # the RFI never blocks the membrane
    t = W.totals(rows)
    assert t["B8-06|FLAT_MEMBRANE"]["state"] == "VALUED" and t["B8-06|FLAT_MEMBRANE"]["measured"] == 16.71
    assert t["B8-06|UPTURN"]["measured"] == pytest.approx(1.92)
    assert all(r["rule_version"] == "WP_APPLICABILITY_RULES_V1" for r in rows)


def test_outlet_printed_means_no_rfi():
    assert not by(W.component_rows(zone(outlet_printed=True)), "DRAINAGE_FALLS")


def test_adverse_covered_ledge_held_not_added():
    ledge = zone(zone_id="R-LEDGE", exposure=W.COVERED_OPEN_SIDE, membrane_m2=0.64,
                 upturn_runs=[{"run": "bay", "lm": 3.5, "kind": "WALL"}], open_edge_lm=None)
    rows = W.component_rows(zone()) + W.component_rows(ledge)
    lf = [r for r in by(rows, "FLAT_MEMBRANE") if r["zone_id"] == "R-LEDGE"][0]
    assert (lf["status"], lf["qty"], lf["held_bound"]) == (W.HELD, None, 0.64)
    assert all(r["status"] == W.HELD for r in rows if r["zone_id"] == "R-LEDGE" and r["component"] != "DRAINAGE_FALLS")
    t = W.totals(rows)["B8-06|FLAT_MEMBRANE"]
    assert t["measured"] == 16.71 and t["held_bounds"] == [0.64] and t["state"] == "PART_AT_LEAST"
    assert not [r for r in rows if r["zone_id"] == "R-LEDGE" and r["component"] == "DRAINAGE_FALLS"]


def test_adverse_covered_is_not_applicable():
    rows = W.component_rows(zone(exposure=W.COVERED))
    assert [(r["component"], r["status"], r["qty"]) for r in rows] == [("FLAT_MEMBRANE", W.NOT_APPLICABLE, 0.0)]


def test_adverse_exposure_unknown_and_area_missing_never_zero():
    r = by(W.component_rows(zone(exposure=None)), "FLAT_MEMBRANE")[0]
    assert r["status"] == W.HELD and r["qty"] is None and r["held_bound"] == 16.71
    r = by(W.component_rows(zone(membrane_m2=None)), "FLAT_MEMBRANE")[0]
    assert r["status"] == W.HELD and r["qty"] is None and "held_bound" not in r
    t = W.totals(W.component_rows(zone(membrane_m2=None)))["B8-06|FLAT_MEMBRANE"]
    assert t["state"] == "HELD" and t["measured"] is None                  # never 0


def test_adverse_window_sill_unknown_or_low():
    runs = zone()["upturn_runs"]
    runs[1] = dict(runs[1], sill_above_slab_m=None)
    w = by(W.component_rows(zone(upturn_runs=runs)), "UPTURN", "window")[0]
    assert w["status"] == W.HELD and w["held_bound"] == pytest.approx(0.16)
    runs[1] = dict(runs[1], sill_above_slab_m=0.10)
    rows = W.component_rows(zone(upturn_runs=runs))
    assert not by(rows, "UPTURN", "window")                                # a low sill is never an upturn
    tr = by(rows, "WINDOW_TRANSITION", "window")[0]
    assert tr["status"] == W.HELD and tr["held_bound"] == 0.8 and tr["unit"] == "lm"


def test_adverse_door_makes_a_terrace_with_its_transition():
    rows = W.component_rows(zone(doors=1, doorways=[{"id": "D1", "width_m": 0.9, "depth_m": 0.2}]))
    assert {r["family"] for r in rows} == {W.FAMILY_TERRACE}
    d = by(rows, "DOORWAY_TRANSITION")[0]
    assert d["status"] == W.MEASURED and d["qty"] == pytest.approx(0.18)
    assert by(W.component_rows(zone(doors=None)), "FLAT_MEMBRANE")[0]["status"] == W.HELD    # access unknown


def test_adverse_surface_already_in_a_roof_line_is_not_added():
    rows = W.component_rows(zone(carried=[{"line_id": "L-x", "m2": 16.70}]))
    assert len(rows) == 1                                                   # one membrane, one line: nothing re-added
    r = rows[0]
    assert (r["status"], r["qty"], r["carried_m2"], r["residual_m2"]) == (W.CARRIED, 0.0, 16.7, pytest.approx(0.01))
    r = W.component_rows(zone(carried=[{"line_id": "L-y", "m2": None}]))[0]
    assert r["status"] == W.HELD and r["qty"] is None


@pytest.mark.parametrize("angle,mirror,unit", [(0, True, 1.0), (33, False, 1.0), (33, True, 1.0), (0, False, 1000.0)])
def test_adverse_rotation_mirror_units(angle, mirror, unit):
    f = (lambda r: [(x * unit, y * unit) for x, y in T.transformed(r, angle_deg=angle, mirror=mirror)])
    g = T.zone_geometry(f(SLAB), footprints=[f(PIER)], openings=[f(VOID)], open_edges=[f(OPEN[0])],
                        unit_m=1.0 / unit)
    assert g["net_m2"] == pytest.approx(16.71, abs=1e-5)
    assert g["upturn_lm"] == pytest.approx(9.6, abs=1e-5)


def test_rule_module_is_unwired_and_stdlib_only():
    src = (ROOT / "engine" / "source" / "wp_applicability_rules_v1.py").read_text()
    assert W.DEFAULT_GUARD_CLASS == "UNWIRED_PRODUCER" and W.UPTURN_H_M == 0.20
    assert "import shapely" not in src and "import ezdxf" not in src
    hits = [p for p in (ROOT / "engine").rglob("*.py") if "wp_applicability_rules_v1" in p.read_text(errors="ignore")
            and p.name != "wp_applicability_rules_v1.py"]
    assert hits == []                                                       # wired into no method


# ---- development villa (private drawing at run time) ------------------------------------------------------------------
HAVE_DXF = A.default_dxf() is not None


@pytest.fixture(scope="module")
def dev():
    import t494_alsenan as D
    return D.build()


def test_dev_villa_without_drawing_is_held(monkeypatch):
    import t494_alsenan as D
    monkeypatch.setattr(A, "default_dxf", lambda: None)
    r = D.build()
    assert r["drawing_read"] is False
    assert all(x["status"] in (W.HELD, W.RFI) or x["qty"] is None for x in r["rows"])
    assert not [x for x in r["rows"] if x["status"] == W.MEASURED]


@pytest.mark.skipif(not HAVE_DXF, reason="private drawing not decoded in this checkout")
def test_dev_villa_components(dev):
    rn = dev["runs"]
    assert rn["unassigned"] == 0.0
    parts = sum(v for k, v in rn.items() if k not in ("unassigned", "perimeter", "net_m2"))
    assert parts == pytest.approx(rn["perimeter"], abs=1e-4)   # end-point overlap of the 1.1 um bands and rn["perimeter"] == pytest.approx(17.446513, abs=1e-5)
    t = dev["totals"]
    assert t["B8-06|FLAT_MEMBRANE"]["measured"] == pytest.approx(4.906867, abs=1e-6)     # = T-486, Checker 4.9069
    assert t["B8-06|FLAT_MEMBRANE"]["held_bounds"] == [pytest.approx(0.639573, abs=1e-6)]
    up = t["B8-06|UPTURN"]
    assert up["measured"] == pytest.approx(5.1935 * 0.20, abs=2e-4)      # piers 3.8672 + parapet 0.8948 + end 0.4316
    assert rn["window_face"] == pytest.approx(0.500, abs=1e-4)            # HELD (sill not read)
    assert rn["open_edge"] == pytest.approx(6.868, abs=2e-3) and rn["void_edge"] == pytest.approx(4.3214, abs=1e-4)
    assert sum(o["overlap_m2"] for o in dev["overlap"]) == 0.0
