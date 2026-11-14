"""T-780 ROOF_LAYER_AREA_V1 (proposed): every roof layer on ONE area per roof surface = the face inside the parapet /
wall faces (beam tops included) less closed-upstand footprints, each with an upturn round it.

Normal: a synthetic villa (not Alsenan): 9.00 x 7.50 roof with one 1.50 m dome, layers equal, screed x 0.075, upturn =
parapet + ring; the Alsenan fix-row set closes to named causes vs the freelancer with a residual below 1 %.
Adverse: slab-panel or finish-hatch basis refused (beam tops / hatch gaps are roof), missing side -> refused (HELD,
never 0), footprints larger than the face refused, a mirrored / unit-scaled roof gives the same area. Writes nothing."""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t780"))
import t780_rules as R  # noqa: E402
import fill_t780 as F  # noqa: E402


# ------------------------------------------------------------------ normal (synthetic villa)
def test_synthetic_roof_with_dome_by_hand():
    face = R.rect_face(9.00, 7.50)                       # 67.50 m2 inside the parapet
    s = R.roof_surface(face, (1.50,), parapet_inner_lm=2 * (9.00 + 7.50))
    assert s["footprints_m2"] == pytest.approx(math.pi * 2.25)
    assert s["layer_m2"] == pytest.approx(67.50 - 7.068583, abs=1e-6)
    assert s["upturn_lm"] == pytest.approx(33.00 + 3 * math.pi, abs=1e-9)
    L = R.layers_for(s)
    assert len({round(L[k], 9) for k in ("FIN.WP.ROOF", "FIN.ROOF.FINISH", "FIN.ROOF.INSULATION", "FIN.ROOF.PROTECTION")}) == 1
    assert L["FIN.ROOF.SCREED"] == pytest.approx(s["layer_m2"] * 0.075)


def test_rotation_mirror_and_units_do_not_change_the_area():
    a = R.rect_face(9.00, 7.50)
    assert R.rect_face(7.50, 9.00) == pytest.approx(a)                 # rotated / mirrored rectangle
    assert R.rect_face(9000, 7500) / 1e6 == pytest.approx(a)           # millimetres in, m2 out after / 1e6


def test_alsenan_fix_rows_close_to_named_causes():
    out = F.main(write=False)
    s = out["summary"]
    assert s["blank_roof_lines_after"] == 0
    for k in ("roof_finish_m2", "roof_membrane_m2"):
        t = s[k]
        assert t["freelancer"] - t["after"] == pytest.approx(sum(t["causes_m2_his_minus_ours"].values()), abs=1e-4)
        unres = sum(v for n, v in t["causes_m2_his_minus_ours"].items() if n.startswith("UNRESOLVED"))
        assert abs(unres) < 0.01 * t["freelancer"]
    # every m2 layer of one surface equals its membrane line after the set
    after = {r["line_id"]: r["after"]["net"] for r in out["rows"]}
    import json
    idx = {l["line_id"]: l for l in json.load(open(F.IDX))["lines"]}
    for z, ids in F.LINES.items():
        vals = {round(after.get(ids[c], idx[ids[c]]["measured_net"]), 6)
                for c in ("FIN.WP.ROOF", "FIN.ROOF.FINISH", "FIN.ROOF.INSULATION", "FIN.ROOF.PROTECTION")}
        assert len(vals) == 1, (z, vals)
    assert all(r["label"] in ("DRAWING-READ", "ESTIMATE") and r["basis"] for r in out["rows"])


# ------------------------------------------------------------------ adverse
@pytest.mark.parametrize("basis", ["SLAB_PANELS", "FINISH_HATCH"])
def test_panel_or_hatch_basis_refused(basis):
    with pytest.raises(R.RoofRuleError):
        R.roof_surface(46.589, basis=basis)


@pytest.mark.parametrize("bad", [(None, 6.45), (7.70, 0), (7.70, -1.0)])
def test_missing_side_is_held_never_zero(bad):
    with pytest.raises(R.RoofRuleError):
        R.rect_face(*bad)
    with pytest.raises(R.RoofRuleError):
        R.roof_surface(None)


def test_footprints_larger_than_face_refused():
    with pytest.raises(R.RoofRuleError):
        R.roof_surface(10.0, (2.0,))
