"""T-321 on the development villa (research/agents_t321; local metres measured on P7757.dxf by entity handle, Drive
titles only). What the drawings establish: every roof's plan area by layer edge (membrane / screed to the wall and
parapet faces, finish to the designer's hatch), the dome footprints, the vertical faces for the upturns; NO roof layer
(insulation, protection, thickness) is printed anywhere, so those stay UNKNOWN / HELD (never 0); the +13.90 roof stays
HELD (owner Q-34) with its drawing-derived values beside. Closures: own areas vs T-221 and the candidate WP lines, own
parapet faces vs T-311's runs, every residual named."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t321"))
import t321_alsenan as A  # noqa: E402


@pytest.fixture(scope="module")
def res():
    return A.build()


def _rows(res, zone, layer=None):
    return [r for r in res["rows"] if r["zone"] == zone and (layer is None or r["layer"] == layer)]


@pytest.mark.parametrize("zid,wall,dband,finish", [("ROOF-430", 55.560332, 54.920332, 54.920332),
                                                   ("TERRACE-550", 32.721, 32.721, 31.6431),
                                                   ("ROOF-970", 146.532, 146.3745, 115.65646)])
def test_zone_areas_by_layer_edge(res, zid, wall, dband, finish):
    z = res["zones"][zid]
    assert z["face_wall_m2"] == pytest.approx(wall, abs=1e-5)
    assert z["face_dband_m2"] == pytest.approx(dband, abs=1e-5)
    assert z["finish_physical_m2"] == pytest.approx(finish, abs=1e-4)


def test_hand_checks(res):
    # ROOF-430: 11.8 x 1.3 + 10.4 x 3.2 + (4.0 x 1.8 - 1.1^2 + pi 1.1^2 / 4)
    import math
    assert res["zones"]["ROOF-430"]["face_wall_m2"] == pytest.approx(
        11.8 * 1.3 + 10.4 * 3.2 + 4.0 * 1.8 - 1.1 ** 2 + math.pi * 1.1 ** 2 / 4, abs=1e-6)
    # ROOF-970: 18.87 x 5.0 + 4.2 x 2.1 + 6.57 x 6.6; domes 2 x pi 2.211092^2
    assert res["zones"]["ROOF-970"]["face_wall_m2"] == pytest.approx(18.87 * 5 + 4.2 * 2.1 + 6.57 * 6.6, abs=1e-6)
    assert sum(res["zones"]["ROOF-970"]["footprints_m2"].values()) == pytest.approx(2 * math.pi * 2.211092 ** 2,
                                                                                   abs=1e-4)
    # ROOF-1390: 7.70 x 6.45 inside the parapet faces (the 2F walls continued), 8.10 x 6.80 outside
    d = res["roof_1390_drawing_derived"]
    assert d["inside_parapet_faces_m2"] == pytest.approx(7.7 * 6.45) and d["outer_wall_outline_m2"] == pytest.approx(55.08)


def test_every_closure_names_its_residual(res):
    for c in res["closures"]:
        if c["closure"].startswith("TERRACE-550 own finish"):
            assert abs(c["unexplained"]) < 0.003       # the Checker's own 31.681: 0.0027 m2 left UNEXPLAINED
            continue
        assert c["closes"], c


def test_parapet_faces_close_on_t311_with_the_finding(res):
    c = next(c for c in res["closures"] if c["closure"].startswith("ROOF-430 parapet"))
    assert c["residual"] == pytest.approx(1.1998, abs=1e-4)
    assert any("F-T321-02" in k and v == pytest.approx(1.4) for k, v in c["named"])


def test_no_b13_layer_is_carried_or_zero(res):
    for r in res["rows"]:
        if r.get("layer") in ("INSULATION", "PROTECTION"):
            assert r["status"] in ("UNKNOWN", "HELD") and r["line_state"] == "NO_LINE"
            assert r["volume_lo_m3"] is None
        if r.get("layer") == "FALLS_SCREED":
            assert r["thickness_m"] is None and r["volume_lo_m3"] is None and r["line_state"] == "NO_LINE"
            assert "CONFLICT" in r["trade_conflict"]
        if r.get("layer") == "MEMBRANE":
            assert r["in_b13_01"] is False
        for k in ("plan_area_lo", "plan_area_hi", "volume_lo_m3", "upturn_lm_lo"):
            assert r.get(k) != 0


def test_top_roof_held_with_drawing_derived_beside(res):
    for r in _rows(res, "ROOF-1390"):
        assert r["status"] == "HELD" and r["plan_area_lo"] is None
    assert res["roof_1390_drawing_derived"]["status"].startswith("HELD")


def test_falls_on_corrected_outlines(res):
    f = res["falls"]
    assert f["TERRACE-550"]["rise_max_m"] == pytest.approx([0.190, 0.203], abs=1.5e-3)
    assert f["ROOF-970"]["rise_max_m"] == pytest.approx([0.1068, 0.1443], abs=1.5e-3)
    # ROOF-430 now includes the 1.6 x 1.3 strip east of the house corner: the far point moves, the rise grows
    assert f["ROOF-430"]["rise_max_m"][0] > 0.112 and f["ROOF-430"]["rise_max_m"][1] > 0.147


def test_freelancer_scope_decomposition(res):
    fl = res["freelancer"]
    assert fl["residual_m2"] == pytest.approx(0.52, abs=0.01) and "NOT a proof" in fl["note"]


def test_measure_reproduces_the_committed_input():
    dxf = os.environ.get("T321_P7757_DXF")
    if not dxf or not Path(dxf).is_file():
        pytest.skip("private drawing not present (set T321_P7757_DXF to Drive 'Alsenan chalet project' P7757.dxf)")
    import t321_measure as M
    got = json.loads(json.dumps(M.measure(dxf), sort_keys=True))
    want = json.loads((ROOT / "research" / "agents_t321" / "ALSENAN_ROOF_LAYERS_INPUT.json").read_text())
    assert got == want
