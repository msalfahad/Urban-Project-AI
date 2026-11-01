"""T-438 development-villa pins on the committed summary (research/agents_t438/ALSENAN_T438.json, built by
t438_alsenan.py from the private DXFs by handle; recomputed here without private input)."""

import json
import math
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "research" / "agents_t438"


def sm():
    return json.loads((D / "ALSENAN_T438.json").read_text())["summary"]


def test_reproduces_from_committed_json():
    p = subprocess.run([sys.executable, "-I", str(D / "t438_alsenan.py"), "--check"], capture_output=True, text=True)
    assert p.returncode == 0 and "REPRODUCED" in p.stdout, p.stdout + p.stderr


def test_rss_no_conflict_the_short_tread_is_a_family_mix():
    s = sm()
    r = s["rss"]
    assert r["governing"] == "ARCH_1F" and r["agreeing"] == ["ST_P4"] and r["risers"] == 11
    assert r["run_faces_m"] == pytest.approx(3.000)
    assert r["classes"]["ARCH_GF"] == {"class": "AGREES", "edges": 11, "missing_edges": 0}
    assert r["gf_overhead_family"] == "NOSING" and r["gf_same_family_goings"] == [0.3] * 10
    # T-432 worker reading reproduced: first hidden FACE to last hidden overhead NOSING
    assert r["worker_mixed_run_m"] == pytest.approx(2.950)
    assert r["worker_mixed_goings"] == [0.3] * 6 + [0.25] + [0.3] * 3
    assert s["projection_m"] == pytest.approx(0.050) and 0.300 - s["projection_m"] == pytest.approx(0.250)


def test_rsa_gf_is_a_partial_projection_missing_the_first_edge():
    r = sm()["rsa"]
    assert r["governing"] == "ARCH_1F" and r["agreeing"] == ["ST_P4"] and r["risers"] == 5
    assert r["classes"]["ARCH_GF"] == {"class": "PARTIAL_PROJECTION", "edges": 4, "missing_edges": 1}
    assert r["gf_missing_edge"].startswith("first RS-A edge")
    assert r["gf_lines_on_first_edge"] == 0          # swept by handle incl. block contents: nothing drawn there
    assert (r["gf_lane_lines"], r["f1_lane_lines"]) == (4, 10)   # 4 singles vs 5 pairs


def test_checks_both_pass_and_do_not_select():
    c = sm()["checks"]
    a, b = c["28 (ARCH_1F + ST_P4)"], c["27 (ARCH_GF overhead)"]
    assert a["riser_m"] == pytest.approx(4.50 / 28, abs=1e-6) and a["riser_check"] == "PASS"
    assert b["riser_m"] == pytest.approx(4.50 / 27, abs=1e-6) and b["riser_check"] == "PASS"
    # the printed '240' (1F) = wall face to the arrival edge: both layouts fill it (1.200 + 1.200 / 1.500 + 0.900)
    assert a["run_m"] == b["run_m"] == pytest.approx(2.400) and a["run_check"] == b["run_check"] == "PASS"
    assert a["landing_m"] == [1.15, 1.2] and b["landing_m"] == [1.15, 1.5]
    # landing level 1.00 + 23 R: 4.6964 / 4.8333 (no level printed: s8_7 'corner landing level is not printed')
    assert a["landing_level"] == pytest.approx(1.00 + 23 * 4.50 / 28, abs=1e-4)
    assert b["landing_level"] == pytest.approx(1.00 + 23 * 4.50 / 27, abs=1e-4)


def test_effects_by_hand_and_engine_unchanged():
    s = sm()
    e28, e27 = s["effects"]["28"], s["effects"]["27"]
    k28 = 0.16 * math.sqrt(1 + (4.5 / 28 / 0.3) ** 2) + 4.5 / 28 / 2      # 0.261870 per m2 of plan
    k27 = 0.16 * math.sqrt(1 + (4.5 / 27 / 0.3) ** 2) + 4.5 / 27 / 2      # 0.266367
    assert e28["m3"]["ST02-RS-S"] == pytest.approx(3.6 * k28, abs=1e-6)            # 0.942732
    assert e28["m3"]["ST02-RS-A"] == pytest.approx(1.44 * k28, abs=1e-6)           # 0.377093
    assert e28["m3"]["ST02-RS-LD"] == pytest.approx((1.15 * 1.2 - 0.0275) * 0.16)  # 1.3525 x 0.16 = 0.2164
    assert e27["plan_m2"] == {"RS-S": 3.6, "RS-LD": 1.7125, "RS-A": 1.08}          # 1.3525 + 1.2 x 0.3; 1.44 - 0.36
    assert e27["m3"]["ST02-RS-A"] == pytest.approx(1.08 * k27, abs=1e-6)           # 0.287676
    assert e27["m3"]["ST02-RS-S"] == pytest.approx(3.6 * k27, abs=1e-6)            # 0.958920
    assert s["delta_27_minus_28"]["straight_total"] == pytest.approx(-0.015629, abs=1e-6)
    assert all(v == 0.0 for v in s["engine_minus_28"].values())   # the merged ledger already rests on 28
    b28, b27 = e28["b7"], e27["b7"]
    assert (b28["RS-A treads"], b28["RS-A tread m2"], b28["RS-A nosing lm"]) == (4, 1.38, 5.75)
    assert (b27["RS-A treads"], b27["RS-A tread m2"], b27["RS-A nosing lm"]) == (3, 1.035, 4.6)
    assert b28["RS-S tread m2"] == b27["RS-S tread m2"] == 3.45


def test_no_positions_in_the_committed_summary():
    doc = json.loads((D / "ALSENAN_T438.json").read_text())
    assert "raw" not in doc and "missing_faces" not in json.dumps(doc)
    # every handle list holds strings only (no coordinates)
    for frame in doc["handles"].values():
        for v in frame.values():
            for h in (v if isinstance(v, (list, tuple)) else [v]):
                assert isinstance(h, str) and len(h) <= 5
