"""T-281 development-villa stair-soffit ledger pinned (values and handles only; the private DXF is never in the repo)."""

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t281"


def _load(name):
    s = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    m = importlib.util.module_from_spec(s)
    sys.modules.setdefault(name, m)
    s.loader.exec_module(m)
    return m


S = _load("t281_stair_soffit")
A = _load("t281_alsenan_check")


@pytest.fixture(scope="module")
def run():
    s, rows = A.summary(A.load())
    return s, {r["id"]: r for r in rows}


def test_committed_files_regenerate_byte_identical():
    js, cs = A.render(A.load())
    assert (HERE / "summary.json").read_text(encoding="utf-8") == js
    assert (HERE / "LEDGER_T281.csv").read_text(encoding="utf-8") == cs


def test_rows_classes_and_nothing_released(run):
    s, r = run
    assert s["rows"] == 29
    assert s["by_class"] == {"BEAM_HELD": 3, "COLUMN_HELD": 2, "NO_SOFFIT": 3, "STAIR_SOFFIT": 16, "UNKNOWN": 5}
    assert s["released"] is False
    for rid in ("ST02-RS-C", "ST01-MS1-T", "ST01-MS2-TR"):        # curved, winder, junction: plan yes, true HELD
        assert r[rid]["plan_O"] > 0 and r[rid]["true_O"] is None and r[rid]["true_D"] is None
    assert r["ST01-MS1-L"]["status"] == "CONFLICT" and r["ST01-MS1-L"]["plan_O"] is None


def test_st01_flights_and_landings(run):
    s, r = run
    assert s["pitch"]["ST01-MS1-U"] == pytest.approx(1.143959, abs=1e-6)          # 4.50 / 27 over 0.30
    assert s["pitch"]["ST01-MS2-L"] == pytest.approx(1.146124, abs=1e-6)          # 4.20 / 25 over 0.30
    assert r["ST01-MS1-U"]["plan_O"] == pytest.approx(3.72, abs=1e-9)            # 25B -> B20 face, 3.10 x 1.20
    assert r["ST01-MS1-U"]["true_O"] == pytest.approx(4.255527, abs=1e-6)
    assert r["ST01-MS1-U"]["true_D"] == pytest.approx(4.248365, abs=1e-6)        # 0.041460 flat at the foot
    assert r["ST01-MS2-L"]["plan_O"] == pytest.approx(3.755, abs=1e-9)           # B20 face -> 632 less column 691
    assert r["ST01-MS2-L/head kink"]["plan_D"] == pytest.approx(0.4101, abs=1e-6)  # 0.341750 x 1.20 under MS2-LD-W
    assert r["ST01-MS2-LD-W"]["plan_O"] == pytest.approx(1.495, abs=1e-9)
    assert r["ST01-MS2-LD-W"]["plan_D"] == pytest.approx(1.495 - 0.4101, abs=1e-6)
    assert r["ST01-MS2-U"]["true_O"] == pytest.approx(4.263581, abs=1e-6)
    t = s["totals"]["ST-01"]
    assert t["plan_O"] == pytest.approx(17.07, abs=1e-9) and t["plan_D"] == pytest.approx(17.07, abs=1e-9)
    assert t["true_O_measured"] == pytest.approx(17.197803, abs=1e-6)
    assert t["true_D_measured"] == pytest.approx(17.243246, abs=1e-6)
    assert t["held_plan_m2"] == pytest.approx(1.5, abs=1e-9)                      # winder 1.495 + MS2-TR 0.005


def test_ms1_l_conflict_both_readings_never_one_end(run):
    s, _ = run
    c = s["MS1-L CONFLICT"]
    assert c["B_structural"]["plan_O"] == pytest.approx(3.935, abs=1e-9)
    assert c["A_architectural"]["plan_O"] == pytest.approx(3.215, abs=1e-9)
    assert c["B_structural"]["slab_borne_D"] == pytest.approx(0.395352, abs=1e-6)
    lane = 3.15 * 1.2 - 0.025
    for k, v in c.items():                          # each reading partitions the MS1-L lane of face GF-025
        assert v["plan_O"] - v["under_B20_band"] + v["open_in_GF025"] == pytest.approx(lane, abs=1e-9)


def test_st02_pieces_and_the_beam_pieces_under_them(run):
    s, r = run
    assert s["pitch"]["ST02-RS-S"] == pytest.approx(1.134456, abs=1e-6)           # Q-50 A cond 4.50 / 28
    assert r["ST02-RS-S"]["status"] == "ASSUMED — OWNER-APPROVED"
    assert r["ST02-RS-S"]["plan_O"] == pytest.approx(1.845, abs=1e-9)
    assert r["ST02-RS-S/B3 'With Stair' band underside"]["plan_O"] == pytest.approx(1.1, abs=1e-9)
    assert r["ST02-RS-S/CA member underside"]["plan_O"] == pytest.approx(0.345, abs=1e-9)
    assert r["ST02-RS-LD"]["plan_O"] == pytest.approx(0.870394, abs=1e-6)
    assert r["ST02-RS-A"]["plan_O"] == pytest.approx(1.32, abs=1e-9)
    assert r["ST02-RS-C"]["plan_O"] == pytest.approx(4.443156, abs=1e-6)
    assert r["ST02-RS-A/head kink"]["plan_D"] + r["ST02-RS-A/head kink/hidden pair 2CC / 2CD"]["plan_D"] == \
        pytest.approx(0.340157 * 1.2, abs=1e-5)


def test_zone_reconciliations_close(run):
    s, _ = run
    rc = s["reconciliation"]
    assert rc["GF-025"]["residual"] == pytest.approx(0.0, abs=1e-9)
    assert rc["1F-016"]["residual"] == pytest.approx(0.0, abs=1e-9)
    t = rc["T271-GF"]
    assert t["held_m2"] == pytest.approx(9.853618, abs=1e-6)
    assert t["ST-02 pieces inside the T-271 stair faces"] == pytest.approx(9.013781, abs=1e-6)
    assert t["slab north of the top riser 315 (GF-131 / GF-132 parts; plate C-T1)"] == pytest.approx(0.777392, abs=1e-6)
    assert abs(t["residual (named)"]) < 1e-4
    assert t["closure ST-02 plan = inside + beam pieces + slivers"] == pytest.approx(0.0, abs=1e-6)
    e = rc["T271-GF-effect"]
    assert e["horizontal decor ceiling, method O"] == pytest.approx(92.146117, abs=1e-5)
    assert e["horizontal decor ceiling, method D"] == pytest.approx(91.737928, abs=1e-5)


def test_adverse_a_landing_counted_in_two_rows_breaks_the_zone():
    d = A.load()
    d["held"].append(dict(d["held"][1], id="ST01-MS1-LD-twice", plan=1.44))
    rows, _, rng = A.build(d)
    rows = [x for x in rows if x["id"] != "ST01-MS1-LD"] + [dict(x, id="ST01-MS1-LD", plan_O=1.44 * 2)
                                                            for x in rows if x["id"] == "ST01-MS1-LD"]
    with pytest.raises(S.SoffitError):
        A.reconcile(d, rows, rng)


def test_adverse_convention_riser_on_the_round_stair_refused():
    d = A.load()
    d["risers"]["ST02"]["source"] = "CONVENTION 0.165"
    with pytest.raises(S.SoffitError):
        A.summary(d)


def _private_dxf():
    for p in sorted((ROOT.parent / "private").glob("*.dxf")) if (ROOT.parent / "private").is_dir() else []:
        if hashlib.sha256(p.read_bytes()).hexdigest().startswith("9f9d1179"):
            return p
    return None


@pytest.mark.skipif(_private_dxf() is None, reason="private structural DXF not decoded in this checkout")
def test_extract_reproduces_the_committed_inputs():
    E = _load("t281_extract")
    m = E.measure(str(_private_dxf()))
    d = A.load()
    assert m["p4 RS-C plan 2EA -> 2BA (m2)"] == pytest.approx(d["held"][0]["plan"], abs=1e-6)
    t = d["zones"]["T271-GF"]
    assert m["p4 RS-C arc start -> 2EA, bottom-step strip (m2)"] == pytest.approx(t["bottom_step_strip"], abs=1e-6)
    assert m["face GF-131 area / inside the ST-02 pieces (m2)"][1] == pytest.approx(t["inside_pieces"]["GF-131"], abs=1e-6)
    assert m["face GF-132 area / inside the ST-02 pieces (m2)"][1] == pytest.approx(t["inside_pieces"]["GF-132"], abs=1e-6)
    assert m["face GF-130 area / inside the ST-02 pieces (m2)"][1] == pytest.approx(t["inside_pieces"]["GF-130/STAIR"], abs=1e-6)
    assert m["face GF-025 area"] == pytest.approx(d["zones"]["GF-025"]["face_m2"], abs=1e-6)
    assert m["face 1F-016 inside the shaft 5E3 / 5D4 / 5E1 / 5C0"] == pytest.approx(d["zones"]["1F-016"]["face_m2"], abs=1e-6)
    assert m["p4 CA 54E from 2BA (s0, s1), from 283 (u0, u1)"] == pytest.approx((0.6, 0.9, 0.05, 1.2), abs=1e-6)
    assert m["p4 hidden pair 535 end past 2C4"] == pytest.approx(0.977312, abs=1e-6)
