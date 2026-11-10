"""T-680 stair-shaft storey-band lines, round 2 (R-T680-1 .. -3): synthetic villa V680 by hand (normal + adverse) and
the development villa pinned to the committed outputs.

Villa V680 (synthetic, not the development villa), by hand. One shaft face, u 0 .. 3.00 m, z 0 .. 9.00 m, storey mark
+4.50 (two band lines). Window held as a band u 1.00 .. 2.00, z 3.00 .. 7.00 (sill / head printed nowhere). Pier return
at u 0.50, depth 0.05.
  gross 3.00 x 9.00 = 27.00; per band 13.50 / 13.50
  BEFORE (window HELD): high (nothing held deducted) 13.50 / 13.50;
                        low  (whole held band deducted) 13.50 - 1.00 x 1.50 = 12.00 / 13.50 - 1.00 x 2.50 = 11.00
  vector record: sill +4.50, head +6.00, width 1.00 (DWF elevation) -> known opening 1.00 x 1.50 = 1.50, upper band only
  AFTER: both cases 13.50 / 13.50 - 1.50 = 12.00
  returns: 0.05 x 4.50 = 0.225 per band (the window does not reach u 0.50); whole 0.45
  AFTER with returns: 13.725 / 12.225; whole 25.95 = 27.00 - 1.50 + 0.45
Adverse: a raster-scaled record, a width 0.10 off, millimetres as metres, head below sill, an opening outside the face,
a non-confirmed status: refused (the band stays HELD); a roof datum missing: no number (HELD, never 0); a band split
that drops the returns: refused; a bound <= 0 or low > high: refused; a mirrored face gives the same areas.
"""
import importlib.util
import json
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t680"
sys.path.insert(0, str(HERE))
import t680_rules as R  # noqa: E402

_spec = importlib.util.spec_from_file_location("t680_alsenan", HERE / "t680_alsenan.py")
B = importlib.util.module_from_spec(_spec)
sys.modules["t680_alsenan"] = B
_spec.loader.exec_module(B)

OUT = HERE / "out" / "T680_SHAFT_ROUND2.json"
REGION = [[0.0, 3.0, 0.0, 9.0]]
REC = {"id": "VW1", "status": "DRAWING-CONFIRMED", "view": "DWF EAST ELEVATION (vector)", "sill_m": "4.50",
       "head_m": "6.00", "width_m": "1.00", "source": "DWF EAST ELEVATION (vector); V680 issue sheet 4"}
HELD = {"id": "VW1", "u": [1.0, 2.0], "status": "HELD"}


def face(window, mirror=False, returns=True):
    f = {"id": "V680 F1", "region": [list(r) for r in REGION], "contacts": [], "openings": [window],
         "returns": [{"u": 0.5, "depth": 0.05}] if returns else []}
    if mirror:
        def m(r):
            return [3.0 - r[1], 3.0 - r[0], r[2], r[3]]
        f["region"] = [m(r) for r in f["region"]]
        f["openings"] = [dict(o, rect=m(o["rect"])) for o in f["openings"]]
        f["returns"] = [{"u": 3.0 - x["u"], "depth": x["depth"]} for x in f["returns"]]
    return f


HELD_WINDOW = {"id": "VW1", "status": "HELD", "rect": [1.0, 2.0, 3.0, 7.0]}


def r3(xs):
    return [round(x, 3) for x in xs]


# ---------------------------------------------------------------- normal cases (hand values)

def test_before_held_band():
    a = B.band_areas([face(HELD_WINDOW, returns=False)], marks=[4.5])
    assert r3(a["hi"]) == [13.5, 13.5]
    assert r3(a["lo"]) == [12.0, 11.0]


def test_after_vector_head_both_cases():
    o = R.opening_from_geometry(HELD, REC, REGION)
    assert o["rect"] == [1.0, 2.0, 4.5, 6.0] and o["evidence"] == "DRAWING-CONFIRMED"
    a = B.band_areas([face(o, returns=False)], marks=[4.5])
    assert r3(a["hi"]) == r3(a["lo"]) == [13.5, 12.0]


def test_returns_split_by_band_and_whole_reconciles():
    o = R.opening_from_geometry(HELD, REC, REGION)
    a = B.band_areas([face(o)], marks=[4.5])
    assert r3(a["ret_hi"]) == [0.225, 0.225]
    assert r3([x + y for x, y in zip(a["hi"], a["ret_hi"])]) == [13.725, 12.225]
    assert round(a["whole"][0], 3) == 25.95


def test_mirror_invariant():
    o = R.opening_from_geometry(HELD, REC, REGION)
    a, b = B.band_areas([face(o)], marks=[4.5]), B.band_areas([face(o, mirror=True)], marks=[4.5])
    assert r3(a["hi"]) == r3(b["hi"]) and r3(a["ret_lo"]) == r3(b["ret_lo"])


def test_restate_delta():
    after = R.line_bound(Decimal("13.725"), Decimal("13.725"), "")
    d = R.restate(Decimal("13.5"), Decimal("13.5"), after)
    assert d["delta"] == ["0.225", "0.225"]
    assert R.restate(None, None, after)["delta"] == [None, None]


# ---------------------------------------------------------------- adverse cases

@pytest.mark.parametrize("change, msg", [
    ({"view": "section A-A scan", "source": "scaled 157.5 px/m"}, "raster"),
    ({"width_m": "1.10"}, "differs"),
    ({"sill_m": "4500", "head_m": "6000"}, "millimetres"),
    ({"head_m": "4.00"}, "not above"),
    ({"head_m": "9.50"}, "outside"),
    ({"status": "ASSUMED"}, "DRAWING-CONFIRMED"),
    ({"head_m": None}, "lacks"),
])
def test_record_refused_band_stays_held(change, msg):
    with pytest.raises(R.RuleError, match=msg):
        R.opening_from_geometry(HELD, dict(REC, **change), REGION)


def test_missing_roof_datum_is_held_never_zero():
    top = R.face_top(None, 0.0, 0.16)
    assert top is None
    b = R.line_bound(None, None, "no printed roof level")
    assert b["held_low"] is None and b["measured_net"] is None and b["class"] == "HELD"
    assert R.face_top(13.90, 0.10, 0.16) == pytest.approx(13.64)


def test_band_split_dropping_returns_refused():
    o = R.opening_from_geometry(HELD, REC, REGION)
    a = B.band_areas([face(o)], marks=[4.5])
    with pytest.raises(R.RuleError, match="in no band"):
        R.check_bands_sum(a["whole"][0], a["hi"])


@pytest.mark.parametrize("lo, hi", [(Decimal("0"), Decimal("5")), (Decimal("6"), Decimal("5"))])
def test_bad_bound_refused(lo, hi):
    with pytest.raises(R.RuleError):
        R.line_bound(lo, hi, "")


def test_return_without_depth_refused():
    from shapely.geometry import box
    with pytest.raises(R.RuleError):
        R.returns_by_band(box(0, 0, 3, 9), [{"u": 0.5, "depth": None}], [4.5])


# ---------------------------------------------------------------- development villa (committed outputs)

def _out():
    return json.loads(OUT.read_text())


def test_alsenan_outputs_reproduce():
    p = subprocess.run([sys.executable, "-I", str(HERE / "t680_alsenan.py"), "--check"], capture_output=True, text=True)
    assert p.returncode == 0, p.stdout + p.stderr


def test_alsenan_baseline_reproduced_before_change():
    assert all(b["match"] for b in _out()["baseline_reproduction"])


def test_alsenan_restated_lines():
    got = {e["line_id"]: (e["held_low"], e["held_high"]) for e in _out()["lines"]}
    assert got == {
        "L-95f2c45c2eccaaeccb08": ("50.945", "62.434"), "L-145bd2394f2907558243": ("50.945", "62.434"),
        "L-0eac839f9132da7bd116": ("45.317", "46.564"), "L-2ab93d5029a4b7cc4dca": ("45.317", "46.564"),
        "L-418121a4b223cb4e8646": ("47.342", "48.772"), "L-5a7a5c6f070ec7142ca5": ("45.392", "46.822"),
    }
    for e in _out()["lines"]:
        assert Decimal(e["held_low"]) <= Decimal(e["held_high"]) and e["measured_net"] is None


def test_alsenan_blank_count_down_and_wet_rooms_named():
    t = _out()["code_totals_m2"]
    assert (t["FIN.PLASTER"]["before"]["blank"], t["FIN.PLASTER"]["after_t680"]["blank"]) == (10, 9)
    assert (t["FIN.PAINT"]["before"]["blank"], t["FIN.PAINT"]["after_t680"]["blank"]) == (3, 2)
    assert t["FIN.PLASTER"]["before"]["low"].startswith("932.72581")
    for w in _out()["wet_room_lines"]:
        assert w["held_low"] is None and w["measured_net"] is None and len(w["missing_datum"]) == 3


def test_alsenan_checker_faces_by_hand():
    # N face, HI case: 1F band 10.50 - 0.40 (MS2-LD bands) - 1.50 (W25) = 8.60; 2F plaster 10.10 - 1.50 (W27) = 8.60
    north = [f for f in B.case_faces("HI", "plaster", True) if f["id"].startswith("N ")]
    a = B.band_areas(north)
    assert round(a["hi"][1], 3) == 8.6 and round(a["hi"][2], 3) == 8.6
