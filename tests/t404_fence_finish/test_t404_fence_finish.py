"""T-404: boundary fence finishes face by face (FENCE_FINISH_V1 rules R-T404-1 .. -6, any villa).

Synthetic 'Villa M' (not the development villa): an L-shaped plot fence, 0.20 thick, printed height 2.40 m above N.G.;
side run A outer 20.00 m and street run B outer 12.00 m meet at ONE external corner (each outer line runs to the corner
point), a 3.50 m gate in B whose one jamb is the fence end (own stop-end) and whose other jamb is the house wall; a
printed garden level +0.30 drawn along both plot faces. Hand values:
  A outside 20.00 x 2.40 = 48.000; A plot (20.00 - 0.20) x 2.40 = 47.520
  B outside 12.00 x 2.40 - 3.50 x 2.40 = 28.800 - 8.400 = 20.400; B plot 11.80 x 2.40 - 8.400 = 19.920
  physical faces 135.840 m2 DRAWING-CONFIRMED; finishable plot faces (2.40 - 0.30 = 2.10): A 41.580, B 24.780 - 7.350
  = 17.430; stop-end 0.20 x 2.40 = 0.480; tops A 20.00 m.l / 4.000 m2, B 8.30 m.l / 1.660 m2.
  No printed finish note and no owner rule: plaster and Sigma / paint HELD on every face at most the face.
Adverse: the house Sigma carried to the fence by default, one face counted for both sides, a held face or layer summed
as 0, a gate wider than its face, mm passed as m, the house jamb counted as a fence end, a level above the top, an
undimensioned dip released, the plan length released as a shaped top. Development villa: committed values-only
outputs reproduce and the pinned figures hold; no coordinate is committed.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
DIR = ROOT / "research" / "agents_t404"


def _load(name):
    spec = importlib.util.spec_from_file_location(name, DIR / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


FF = _load("fence_finish")
H = {"value": 2.40, "status": FF.DC}


def _villa_m(order=("A", "B")):
    a_out, a_in = FF.face_lengths(20.00, 0.20, 1)
    b_out, b_in = FF.face_lengths(12.00, 0.20, 1)
    g = [("G-1", 3.50)]
    faces = {
        "A": [FF.physical_face("A", "OUTSIDE", a_out, H), FF.physical_face("A", "PLOT", a_in, H)],
        "B": [FF.physical_face("B", "OUTSIDE", b_out, H, g), FF.physical_face("B", "PLOT", b_in, H, g)],
    }
    return [f for k in order for f in faces[k]]


def test_villa_m_faces_by_hand():
    f = {x["key"]: x for x in _villa_m()}
    assert f["A/OUTSIDE"]["net_m2"] == pytest.approx(48.000)
    assert f["A/PLOT"]["net_m2"] == pytest.approx(47.520)
    assert f["B/OUTSIDE"]["net_m2"] == pytest.approx(20.400)
    assert f["B/PLOT"]["net_m2"] == pytest.approx(19.920)
    assert f["B/OUTSIDE"]["deductions"] == [("G-1", pytest.approx(8.400))]
    t = FF.totals(list(f.values()))
    assert t["dc"] == pytest.approx(135.840) and t["held"] == []


def test_villa_m_finishable_stop_end_tops():
    f = {x["key"]: x for x in _villa_m()}
    a = FF.finishable(f["A/PLOT"], 2.40, 0.30, along_whole_run=True)
    b = FF.finishable(f["B/PLOT"], 2.40, 0.30, along_whole_run=True)
    assert (a["m2"], a["status"]) == (pytest.approx(41.580), FF.DC)
    assert (b["m2"], b["status"]) == (pytest.approx(17.430), FF.DC)
    part = FF.finishable(f["A/PLOT"], 2.40, 0.30, along_whole_run=False)
    assert part["status"] == FF.HELD and part["m2"] is None
    assert (part["lo_m2"], part["hi_m2"]) == (pytest.approx(41.580), pytest.approx(47.520))
    out = FF.finishable(f["A/OUTSIDE"], 2.40, None)
    assert out["status"] == FF.HELD and out["m2"] is None and out["hi_m2"] == pytest.approx(48.000)
    assert FF.stop_end("B", "G-1", 0.20, H)["m2"] == pytest.approx(0.480)
    ta, tb = FF.top("A", 20.00, 0.20), FF.top("B", 12.00 - 0.20 - 3.50, 0.20)
    assert (ta["ml"], ta["m2"]) == (pytest.approx(20.00), pytest.approx(4.000))
    assert (tb["ml"], tb["m2"]) == (pytest.approx(8.30), pytest.approx(1.660))


def test_villa_m_layers_held_without_authority_and_valued_with_it():
    f = _villa_m()[0]
    lyr = FF.layer(f["key"], "PLASTER", f["net_m2"])
    assert lyr["status"] == FF.HELD and lyr["m2"] is None and lyr["at_most_m2"] == pytest.approx(48.000)
    ok = FF.layer(f["key"], "PLASTER", f["net_m2"], authority="Villa M fence detail note 'plaster both faces'")
    assert ok["status"] == FF.DC and ok["m2"] == pytest.approx(48.000)


def test_order_and_mirror_invariance():
    t1 = FF.totals(_villa_m(("A", "B")))
    t2 = FF.totals(_villa_m(("B", "A")))
    assert t1 == t2


# ---- adverse -------------------------------------------------------------------------------------------------------

def test_house_sigma_by_default_refused():
    with pytest.raises(FF.FinishError, match="house facade"):
        FF.layer("A/OUTSIDE", "SIGMA_PAINT", 48.0, house_method=True)


def test_one_face_counted_for_both_sides_refused():
    a = FF.physical_face("A", "OUTSIDE", 20.00, H)
    with pytest.raises(FF.FinishError, match="counted twice"):
        FF.once([a, dict(a)])
    out, plot = FF.face_lengths(20.00, 0.20, 1)
    assert out != plot          # 'both sides = 2 x one length' would over-count the plot face by t x h per corner
    with pytest.raises(FF.FinishError):
        FF.physical_face("A", "BOTH", 20.00, H)


def test_held_never_summed_as_zero():
    held = FF.physical_face("S", "OUTSIDE", 2.40, {"value": 2.65, "status": FF.HELD})
    assert held["net_m2"] is None and held["status"] == FF.HELD and held["comparison_only_m2"] == pytest.approx(6.36)
    none = FF.physical_face("P", "PLOT", 1.20, None)
    assert none["net_m2"] is None and none["comparison_only_m2"] is None
    t = FF.totals([FF.physical_face("A", "OUTSIDE", 20.0, H), held, none])
    assert t["dc"] == pytest.approx(48.0) and t["held"] == ["S/OUTSIDE", "P/PLOT"]
    assert t["held_at_most_complete"] is False
    with pytest.raises(FF.FinishError, match="never 0"):
        FF.face_lengths(None, 0.20, 1)


def test_gate_and_unit_errors_refused():
    with pytest.raises(FF.FinishError, match="gates fill"):
        FF.physical_face("B", "OUTSIDE", 3.0, H, [("G-1", 3.50)])
    with pytest.raises(FF.FinishError, match="repeated"):
        FF.physical_face("B", "OUTSIDE", 12.0, H, [("G-1", 1.0), ("G-1", 1.0)])
    with pytest.raises(FF.FinishError, match="mm passed"):
        FF.face_lengths(20000, 0.20, 1)
    with pytest.raises(FF.FinishError, match="unit"):
        FF.face_lengths(2000, 20, 1, unit="cm")


def test_house_jamb_and_level_above_top_refused():
    with pytest.raises(FF.FinishError, match="another element"):
        FF.stop_end("B", "G-1", 0.20, H, own_end=False)
    f = FF.physical_face("A", "PLOT", 19.80, H)
    with pytest.raises(FF.FinishError, match="above the wall top"):
        FF.finishable(f, 2.40, 2.50)


def test_undimensioned_profile_not_released():
    f = FF.physical_face("B", "OUTSIDE", 12.0, H, [("G-1", 3.5)], profile="UNDIMENSIONED")
    assert f["net_m2"] is None and f["status"] == FF.HELD and f["at_most_m2"] == pytest.approx(20.400)
    tp = FF.top("B", 8.30, 0.20, "UNDIMENSIONED")
    assert tp["ml"] is None and tp["at_least_ml"] == pytest.approx(8.30)
    end = FF.stop_end("B", "G-1", 0.20, H, profile="UNDIMENSIONED")
    assert end["m2"] is None and end["at_most_m2"] == pytest.approx(0.480)


def test_shared_with_house_refused():
    with pytest.raises(FF.FinishError, match="both ledgers"):
        FF.no_shared_faces(["A/OUTSIDE"], ["A/OUTSIDE", "GF/SE-1/EDGE/storey"])


def test_freelancer_reconcile_closes_to_causes():
    # his one row 'both sides' 2 x 32.00 x 2.20 against our A + B faces (outside 20.00 + 8.50 solid, plot 19.80 + 8.30)
    rec = FF.reconcile([("r1", 1, 32.00, 2.20, 28.50), ("r2", 1, 32.00, 2.20, 28.10)], [("B/END-G-1", 0.48)], 2.40)
    assert rec["his_m2"] == pytest.approx(140.8)
    assert rec["own_m2"] == pytest.approx(28.5 * 2.4 + 28.1 * 2.4 + 0.48)
    assert rec["residual_m2"] == pytest.approx(0.0, abs=1e-9)


# ---- development villa (committed values-only outputs) ---------------------------------------------------------------

def test_development_villa_reproduces_and_pins():
    al = _load("t404_alsenan")
    outs = al.outputs()
    for p, s in outs.items():
        assert p.read_text(encoding="utf-8") == s, p.name
    d = json.loads((DIR / "summary.json").read_text(encoding="utf-8"))
    assert d["physical_faces_dc_m2"] == pytest.approx(165.201)            # 83.1305 + 82.0705
    assert d["faces"]["F-NORTH/OUTSIDE"]["net_m2"] == pytest.approx(31.37 * 2.65)
    assert d["faces"]["F-NORTH/PLOT"]["net_m2"] == pytest.approx(30.97 * 2.65)
    assert d["faces"]["F-STREET/OUTSIDE"]["at_most_m2"] == pytest.approx(5.80 * 2.65)
    assert d["faces"]["F-STREET/PLOT"]["at_most_m2"] == pytest.approx(5.60 * 2.65)
    assert d["faces"]["F-SEA/OUTSIDE"]["status"] == "HELD" and d["faces"]["F-SEA/OUTSIDE"]["net_m2"] is None
    assert d["coping"] == "NOT_DRAWN" and d["shared_faces_with_house"] == 0 and d["house_band_overlap_m2"] == 0.0
    fr = d["freelancer"]
    assert fr["his_total_m2"] == pytest.approx(107.24)
    assert fr["mapping_A"]["residual_m2"] == pytest.approx(0.0, abs=1e-9)
    assert fr["mapping_B"]["residual_m2"] == pytest.approx(0.0, abs=1e-9)
    assert fr["mapping_A"]["diff_m2"] == pytest.approx(-5.5705)
    assert fr["mapping_B"]["diff_m2"] == pytest.approx(-6.6305)


def test_no_coordinates_or_names_committed():
    for name in ("FACES_T404.csv", "ITEMS_T404.csv", "FREELANCER_T404.csv", "summary.json"):
        txt = (DIR / name).read_text(encoding="utf-8")
        for tok in txt.replace(",", " ").replace('"', " ").replace(":", " ").split():
            try:
                v = float(tok)
            except ValueError:
                continue
            assert abs(v) < 200, f"{name}: {tok} looks like a coordinate"
