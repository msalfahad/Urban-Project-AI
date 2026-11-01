"""T-417 Alsenan pins (no private input): the committed summary reproduces, and the ST-01 terms close."""

import importlib.util
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "research" / "agents_t417"


def _mod():
    spec = importlib.util.spec_from_file_location("t417_alsenan", D / "t417_alsenan.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


S = json.loads((D / "summary_t417.json").read_text(encoding="utf-8"))


def test_check_reproduced(capsys):
    assert _mod().main(["--check"]) == 0
    assert "REPRODUCED" in capsys.readouterr().out


def test_drawn_flights():
    for fid, f in S["geometry"]["flights"].items():
        assert f["risers"] == 12 and f["run"] == pytest.approx(3.30, abs=1e-6) and f["lane"] == pytest.approx(1.20)
    assert S["geometry"]["flights"]["ST01-MS2-U"]["risers_drawn"] == 11


def test_flight_terms_close_and_length_traced():
    d = S["derived"]
    assert d["flights_contribution_m3"] == pytest.approx(-2.310031, abs=1e-6)       # T-398 merged figure
    assert d["length_term_m3"] == pytest.approx(-2.016, abs=1e-6)
    assert d["rise_in_length_m3"] == pytest.approx(-2.026752, abs=1e-6)
    assert d["one_length_m3"] == pytest.approx(0.010752, abs=1e-6)
    assert d["flight_untraced_m3"] == 0.0
    for f in d["flights"].values():
        assert abs(f["net_m3"] - f["ledger_m3"]) <= 2e-6
        assert sum(t["m3"] for t in f["terms"]) == pytest.approx(f["contribution_m3"], abs=2e-6)
    assert d["flights"]["ST01-MS1-U"]["profile_m"] == pytest.approx(5.30, abs=1e-9)   # his 5.3 exactly


def test_landing_terms_close():
    d = S["derived"]
    assert d["landing_area_term_m3"] == pytest.approx(0.1624, abs=1e-6)
    assert sum(t["m3"] for t in d["landing_terms"]) == pytest.approx(0.1624, abs=1e-6)
    assert d["landing_contribution_m3"] == pytest.approx(0.028, abs=1e-6)


def test_column_projection_held_never_zero_valued():
    c = S["derived"]["columns"]
    assert c["691"]["state"] == "HELD" and c["691"]["high"] == pytest.approx(0.006684, abs=1e-6)
    assert c["36B"]["m3"] is None
    assert c["341"]["state"] == "FLUSH" and c["682"]["state"] == "FLUSH"


def test_summary_holds_no_coordinates_or_text():
    raw = (D / "summary_t417.json").read_text(encoding="utf-8")
    assert raw.isascii()
    assert not re.search(r"\d{5,}\.\d", raw)          # no drawing coordinates (mm) in the tracked summary
