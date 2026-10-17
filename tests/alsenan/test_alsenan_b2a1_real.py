"""Phase B2A.1 - generic QA patch on the frozen B2A registers: independent riser / tread stair model, unambiguous curved
bases, self-contained freeze. These tests read the frozen B2A.1 files only (built twice from the committed code,
byte-identical)."""

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
REG = ROOT / "tests/alsenan/registers_b2a1"
PARENT = ROOT / "tests/alsenan/registers_b2a"
FREEZE = "ALSENAN_PHASE_B2A1_REGISTER_FREEZE"
pytestmark = pytest.mark.skipif(not REG.exists(), reason="B2A.1 registers not frozen yet")


def R(n, d=REG):
    return json.loads((d / f"{n}.json").read_text())


def _digest(o):
    return hashlib.sha256(json.dumps(o, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()


def test_freeze_pins_the_parent_b2a_freeze_and_the_benchmark_stays_closed():
    fz = R(FREEZE)
    assert fz["BENCHMARK_OPENED"] is False
    assert fz["parent_b2a_freeze"]["sha256"] == hashlib.sha256((PARENT / "ALSENAN_PHASE_B2A_FREEZE.json").read_bytes()).hexdigest()
    assert fz["xlsx"]["rewrite_identical"] and fz["xlsx"]["readback"] == "PASS"
    assert R("QA_GATES")["state"] == "PASS"


def test_register_digests_match_the_freeze():
    fz = R(FREEZE)
    for n, d in fz["register_digests"].items():
        if n in (FREEZE, "QORTUBA_REGRESSION", "ALSENAN_REGRESSION"):
            continue                                    # the freeze itself; the regressions run after the build
        assert _digest(R(n)) == d, n


def test_engines_match_the_b2a1_freeze():
    for m, h in R(FREEZE)["b2a_engine_sha256"].items():
        assert hashlib.sha256((ROOT / "engine/source" / f"{m}.py").read_bytes()).hexdigest() == h, m


def test_stair_stays_blocked_with_known_and_unknown_inputs():
    s = R("STAIR_REGISTER")
    assert s["policy"] == "STAIR_CONCRETE_V2"
    assert s["result"]["state"] == "BLOCKED_INPUT_MISSING" and s["result"]["volume_m3"] is None
    assert {"riser_count", "riser_height_m", "waist_thickness_m", "landing_thickness_m"} <= set(s["unknown_inputs"])
    k = s["known_inputs"]
    assert k["tread_going_m"]["value"] == pytest.approx(0.30) and k["flight_width_m"]["values"]
    assert k["tread_count"]["authority"] == "CANDIDATE" and k["observed_tread_line_runs"]
    missing = s["result"]["missing"]
    assert any(m.endswith(": riser_count") for m in missing) and any(m.endswith(": tread_count") for m in missing)


def test_curved_bases_are_explicit_aliases_equal_and_default_is_min_radius():
    for r in R("CURVED_OPENING_REGISTER")["rows"]:
        b = r["bases_m"]
        assert b["MIN_RADIUS_ARC"] < b["MID_BAND_ARC"] < b["MAX_RADIUS_ARC"] and b["CHORD"] < b["MIN_RADIUS_ARC"]
        assert (b["INNER"], b["CENTRE"], b["OUTER"]) == (b["MIN_RADIUS_ARC"], b["MID_BAND_ARC"], b["MAX_RADIUS_ARC"])
        assert r["commercial_basis"] == "MIN_RADIUS_ARC" and r["commercial_m"] == b["MIN_RADIUS_ARC"]
        o = r["orientation"]
        if o["state"] == "ESTABLISHED":
            assert r["side_probe"]["state"] == "ESTABLISHED"
            side = {"MIN_RADIUS": b["MIN_RADIUS_ARC"], "MAX_RADIUS": b["MAX_RADIUS_ARC"]}
            assert o["ROOM_SIDE_ARC"] / 1000.0 == pytest.approx(side[o["room_side"]])
        else:
            assert o["ROOM_SIDE_ARC"] is None and o["EXTERIOR_SIDE_ARC"] is None


def test_curved_commercial_lengths_unchanged_from_b2a():
    old = {r["id"]: r["commercial_m"] for r in R("CURVED_OPENING_REGISTER", PARENT)["rows"]}
    new = {r["id"]: r["commercial_m"] for r in R("CURVED_OPENING_REGISTER")["rows"]}
    assert old == new


def test_alsenan_regression_passes():
    a = R("ALSENAN_REGRESSION")
    assert a["state"] == "PASS" and a["failed"] == []
    assert a["parent_freeze_sha256"] == R(FREEZE)["parent_b2a_freeze"]["sha256"]
    for n, v in a["per_register"].items():
        assert set(v.get("classes", [])) <= {"SCHEMA", "TERMINOLOGY"}, n


def test_qortuba_regression():
    assert R("QORTUBA_REGRESSION")["state"] in ("UNCHANGED", "PROVENANCE_ONLY")


def test_frozen_parent_registers_untouched():
    for d, c in (("tests/alsenan/registers_b2a", "e2afb69"), ("tests/alsenan/registers_b2a_eval", "e2afb69"),
                 ("tests/alsenan/registers_a3", "9aa2741"), ("tests/alsenan/registers_b1", "f820263")):
        out = subprocess.run(["git", "-C", str(ROOT), "diff", "--stat", c, "--", d], capture_output=True, text=True)
        assert out.returncode == 0 and out.stdout.strip() == "", out.stdout
