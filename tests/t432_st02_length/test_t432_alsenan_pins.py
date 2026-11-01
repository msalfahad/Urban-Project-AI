"""T-432 Alsenan pins (no private input): the committed summary reproduces; 16.4 m is no drawn construction."""

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "research" / "agents_t432"
S = json.loads((D / "summary_t432.json").read_text(encoding="utf-8"))


def _mod():
    spec = importlib.util.spec_from_file_location("t432_alsenan", D / "t432_alsenan.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_check_reproduced(capsys):
    assert _mod().main(["--check"]) == 0
    assert "REPRODUCED" in capsys.readouterr().out


def test_pieces_by_handle():
    p = {x["id"]: x for x in S["geometry"]["pieces"]}
    assert [p[k]["n_risers"] for k in ("ST02-RS-C", "ST02-RS-S", "ST02-RS-LD", "ST02-RS-A")] == [12, 11, 0, 5]
    assert p["ST02-RS-S"]["plan"]["CENTRE"] == pytest.approx(3.0, abs=1e-6)
    assert p["ST02-RS-A"]["plan"]["CENTRE"] == pytest.approx(1.2, abs=1e-6)
    assert p["ST02-RS-LD"]["plan"] == pytest.approx(dict(INNER=0.0, CENTRE=1.15, OUTER=2.35, RISERS=0.849264), abs=1e-6)
    assert p["ST02-RS-C"]["plan"]["CENTRE"] == pytest.approx(3.571913, abs=1e-6)
    assert S["geometry"]["rsc_dtheta_centre_deg"]["min"] == S["geometry"]["rsc_dtheta_centre_deg"]["max"]


def test_rsc_centre_by_hand():
    # r_c (1.530511 + 2.780511) / 2; 2EA at phi 175.9736 + asin(0.05 / r_c); arc to 270 deg + straight 0.0846 to 2BA
    import math
    rc = (1.530511 + 2.780511) / 2
    th = 175.9736 + math.degrees(math.asin(0.05 / rc))
    assert rc * math.radians(270 - th) + 0.0846 == pytest.approx(3.571913, abs=1e-4)


def test_unresolved_with_every_construction_listed():
    d = S["derived"]
    c = d["classification"]
    assert d["drawn_risers"] == 28 and d["rise"] == pytest.approx(4.5, abs=1e-9)
    assert c["state"] == "UNRESOLVED" and c["exact"] == [] and d["within_his_rounding_band"] == []
    assert d["n_constructions"] == len(c["table"]) == 49
    assert abs(c["nearest"][2]) > 0.05
    t = {k: v for k, v, _ in c["table"]}
    assert t["CENTRE / PROFILE"] == pytest.approx(13.421913, abs=1e-6)       # the T-417 basis on ST-02
    assert t["OUTER / PROFILE"] == pytest.approx(15.644408, abs=1e-6)


def test_term_stays_whole_and_no_coordinates():
    d = S["derived"]
    assert d["restated"]["unexplained_m3"] == pytest.approx(-2.476433, abs=1e-6)
    assert d["his_beyond_drawn_m"] == pytest.approx(7.370337, abs=1e-6)
    txt = json.dumps(S)
    for k in ('"x"', '"y"', '"center"', '"start"', '"end"'):
        assert k not in txt
