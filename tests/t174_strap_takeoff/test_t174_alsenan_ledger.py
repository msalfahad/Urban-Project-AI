"""T-174 Alsenan ledger (research/agents_t174/T174_STRAPS.json, written by run_t174_alsenan.py from the structural DXF
sha 9f9d1179): the committed values agree with the hand calculation in T-174_STRAPS.md, and re-running the check on the
private DXF (when present: .work/private/ST7757.dxf beside the checkout, never in the repository) reproduces them.

Hand (ST7757 dxf, foundation plan; ST7757.pdf p.9 / p.10):
  SB2 faces y 37,847.96 (F11 top) / 40,097.96 (F6 bottom), axis direction (-0.19224, 0.98135): 2,250.0 / 0.98135 =
      2,292.8 mm; 1.00 x 2.2928 x 0.50 = 1.1464 m3; projection gap 1.8287 = 2.2927 - 0.2911 - 0.1730
  SB3 faces y 37,347.96 (F15 top) / 40,397.96 (F3 bottom); the two drawn edges are 0.03 deg off parallel (1B26 cos
      0.93625, 1B27 cos 0.93608 to the y axis): 3,050.0 / cos = 3,257.7 .. 3,258.3 mm, mean axis 3,258.0 mm; 0.50 x 3.2577 x 0.40 = 0.6516 m3; inside F3 (H 0.30 < D 0.40) 0.3417 - 0.0463 (column) = 0.2954 m2
  SB1 orthogonal: 42,297.96 - 37,747.96 = 4,550.0 mm; 0.70 x 4.55 x 0.50 = 1.5925 m3 (projection = axis)
"""

import json
import os
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
LEDGER = ROOT / "research/agents_t174/T174_STRAPS.json"


def ledger():
    return {r["mark"]: r for r in json.loads(LEDGER.read_text(encoding="utf-8"))}


def test_axis_lengths_verify_the_owner_figures():
    L = ledger()
    assert L["SB2"]["lengths"]["axis_face_to_face_m"] == pytest.approx(2.2928, abs=2e-4)   # owner: 2.29
    assert L["SB3"]["lengths"]["axis_face_to_face_m"] == pytest.approx(3.2580, abs=4e-4)   # owner: 3.26
    assert L["SB1"]["lengths"]["axis_face_to_face_m"] == pytest.approx(4.55, abs=2e-4)
    for m in ("SB2", "SB3"):
        g = L[m]["lengths"]
        assert g["axis_face_to_face_m"] - sum(g["corner_overreach_m"]) == pytest.approx(g["projection_gap_m"],
                                                                                       abs=2e-4)


def test_concrete_and_held_items():
    L = ledger()
    assert L["SB2"]["concrete"]["volume_m3"] == pytest.approx(1.1464, abs=2e-4)
    assert L["SB3"]["concrete"]["volume_m3"] == pytest.approx(0.6516, abs=2e-4)
    assert L["SB1"]["concrete"]["volume_m3"] == pytest.approx(1.5925, abs=2e-4)
    f3 = [o for o in L["SB3"]["concrete_in_footings"] if o["footing"].startswith("F3")][0]
    assert f3["status"] == "HELD" and f3["A_in_m2"] == pytest.approx(0.2954, abs=3e-4)
    f10 = [o for o in L["SB1"]["concrete_in_footings"] if o["footing"].startswith("F10")][0]
    assert f10["status"] == "HELD"                                      # owner Q-31: F10 + F outline HELD
    for m in ("SB1", "SB2", "SB3"):
        assert L[m]["excavation"]["status"] == "HELD" and L[m]["excavation"]["volume_m3"] is None


PRIVATE = ROOT.parent / "private" / "ST7757.dxf"


@pytest.mark.skipif(not PRIVATE.exists(), reason="private structural DXF absent (Drive, read-only)")
def test_rerun_on_the_private_dxf_reproduces_the_ledger():
    import importlib.util
    spec = importlib.util.spec_from_file_location("run_t174", ROOT / "research/agents_t174/run_t174_alsenan.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    fresh = {r["mark"]: r for r in json.loads(json.dumps(mod.run(str(PRIVATE))))}
    assert fresh == ledger()
