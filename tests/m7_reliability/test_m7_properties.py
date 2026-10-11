"""M7 properties of the whole route on cluttered synthetic villas (tools/synthetic_villa_m6, every completeness case,
distractors and drafting noise), under the V5 conventions:
  metamorphic   translate, rotate 90/180/270, mirror, reorder, explode polylines, duplicate every text, add an
                unrelated furniture layer, change the drawing unit: every quantity (concrete and reinforcement, base,
                low, high, exposure, item count by family / storey / category) stays the same (tools/m7_metamorphic;
                only the DXF is changed, never an expected value)
  quantities    against the generator's design truth (tools/m7_evaluate): no SILENT row - every family / storey is
                EXACT, inside an ambiguous-scope range, or short by no more than what the engine reported unresolved
Seed 1 is a millimetre drawing with drafting noise; seed 2 a metre drawing; seed 4 the one whose furniture rectangle
lands on a column mark. Synthetic drawings share the generator's drafting assumptions: these tests prove the rules
hold across placements and noise, not real-drawing accuracy."""

from __future__ import annotations

import pytest

ezdxf = pytest.importorskip("ezdxf")

from tools import m7_evaluate as EV                         # noqa: E402
from tools import m7_metamorphic as MM                      # noqa: E402
from tools import synthetic_villa_m6 as SM6                 # noqa: E402

V5 = "engine/profiles/URBAN_M7_GENERIC_CONVENTIONS_V5.json"


@pytest.mark.parametrize("seed", [1, 2, 4])
def test_quantities_do_not_depend_on_how_the_drawing_is_placed_or_encoded(tmp_path, seed):
    dxf = SM6.generate(tmp_path, seed, defects=seed % 2 == 1, hard=True, m6v2=True)
    r = MM.run(dxf, profile=str(tmp_path / f"villa_m6_{seed}.profile.json"), conventions=V5, work=str(tmp_path))
    bad = {op: (v.get("error") or v["differences"][:3]) for op, v in r["ops"].items() if op in r["failed"]}
    assert not bad, bad
    assert set(r["passed"]) == set(MM.OPS)


def test_the_frozen_v4_conventions_fail_the_unrelated_layer_property(tmp_path):
    """the before: the same villa under V4 changes its quantities when a furniture layer is added (seed 4)."""
    dxf = SM6.generate(tmp_path, 4, hard=True, m6v2=True)
    r = MM.run(dxf, profile=str(tmp_path / "villa_m6_4.profile.json"),
               conventions="engine/profiles/URBAN_M5_GENERIC_CONVENTIONS_V4.json", ops=("noise_layer",),
               work=str(tmp_path))
    assert r["failed"] == ["noise_layer"]


@pytest.mark.parametrize("seed", [3, 6, 9, 12])
def test_no_silent_quantity_on_cluttered_villas(tmp_path, seed):
    rec = EV.evaluate(seed, tmp_path, defects=seed % 2 == 1, hard=True, m6v2=True)
    assert rec["ok"], rec.get("error")
    silent = [r for r in rec["rows"] if r["state"] == "SILENT"]
    assert not silent, silent
