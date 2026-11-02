"""T-475 pins on the development villa (station-local values only; no drawing content): three landings + closed roof,
2F right band HELD 0 .. 0.400, surround 2.750 .. 13.980 m2, threshold 1.500 m2 / 3.000 m.l, landing depth 1.250 on 1F /
2F (the 0.50 fallback fits), FLUSH on the printed F.F.L.s, and agreement with the T-421 V3.0.38 lines."""
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[2] / "research" / "agents_t475"
sys.path.insert(0, str(HERE))
import t475_alsenan as A  # noqa: E402

C = A.C


def test_committed_outputs_reproduce():
    assert A.main(["--check"]) == 0


def test_census_and_totals():
    cen, st = A.build()
    assert cen["stations"] == ["ELV-01-GF", "ELV-01-1F", "ELV-01-2F"]
    assert [f["state"] for f in cen["floors"]] == [C.LANDING] * 3 + [C.NO_LANDING]
    t = C.family_totals(st)
    assert t["surround"]["bound"] == pytest.approx([2.750, 13.980])
    assert t["threshold"]["value"] == pytest.approx(1.500) and t["front_edge_lm"] == pytest.approx(3.000)


def test_2f_right_band_and_depth_fit():
    _, st = A.build()
    by = {s["station_id"]: s for s in st}
    r = by["ELV-01-2F"]["surround"]["bands"][2]
    assert r["width_m"] is None and r["bound"] == [0.0, 0.4]
    for sid in ("ELV-01-1F", "ELV-01-2F"):
        assert by[sid]["threshold"]["landing_depth"]["value"] == 1.25
        assert by[sid]["threshold"]["area_m2"] == 0.5
    assert by["ELV-01-GF"]["threshold"]["landing_depth"]["status"] == "NOT_LIMITING"
    assert [by[s]["level"]["relation"] for s in by] == [C.FLUSH] * 3


def test_candidate_agreement():
    d = json.loads((HERE / "summary.json").read_text(encoding="utf-8"))
    assert all(a["threshold_m2"][2] and a["surround_bound_m2"][2] for a in d["candidate_agreement"])
    assert d["equivalent_stations"] is False
