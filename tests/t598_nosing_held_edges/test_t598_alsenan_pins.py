"""T-598 development-villa pins on the committed reading (research/agents_t598/ALSENAN_EDGES_T598.json, built by
t598_alsenan.py from the private DXFs by handle; recomputed here without private input), plus a re-read of the private
drawings when they are present (skipped otherwise)."""
from __future__ import annotations

import json
import math
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "research" / "agents_t598"
PRIV = ROOT.parents[1] / ".work" / "private"
ARCH = Path(os.environ.get("T598_DXF", PRIV / "P7757_DXF_COMPRESSED" / "P7757.dxf"))
ST = Path(os.environ.get("T598_ST", PRIV / "ST7757.dxf"))


def data():
    return json.loads((D / "ALSENAN_EDGES_T598.json").read_text())


def res():
    return data()["result"]


def edges():
    return {e["id"]: e for e in res()["edges"]}


def test_reproduces_from_committed_json():
    p = subprocess.run([sys.executable, "-I", str(D / "t598_alsenan.py"), "--check"], capture_output=True, text=True)
    assert p.returncode == 0 and "REPRODUCED" in p.stdout, p.stdout + p.stderr


@pytest.mark.skipif(not (ARCH.exists() and ST.exists()), reason="private drawings absent (decode into .work/private)")
def test_private_reread_equals_committed():
    p = subprocess.run([sys.executable, "-I", str(D / "t598_alsenan.py"), "--dxf", str(ARCH), "--st", str(ST),
                        "--compare"], capture_output=True, text=True)
    assert p.returncode == 0 and "SAME AS COMMITTED" in p.stdout, p.stdout + p.stderr


def test_twenty_named_edges_closed_by_class():
    e = edges()
    named = [k for k in e if k != "ST02-RSC-256-BAND"]
    # T-412 named 20 HELD: MS1-T 5 (N05 closed by T-434 MERGED), MS1-U floor, MS2-TR, MS2-U floor, RS-C 12
    assert len(named) == 19
    assert sorted(k for k in named if e[k]["cls"] == "DESIGNER_ITEM") == [f"ST01-MS1T-N0{i}" for i in range(1, 5)]
    assert all(e[k]["cls"] == "VALUE" for k in named if not k.startswith("ST01-MS1T"))
    assert not any(v["cls"] == "DRAWING_CONFLICT" for v in e.values())


def test_held_edges_never_zero_and_bounded():
    for v in edges().values():
        if v["cls"] != "VALUE":
            assert v["lm"] is None and v["status"] == "HELD" and v["bound"][1] > 0
    # hand: winder front >= the 1.150 lane, <= hypot(1.150, 1.300) = 1.735655 (the turn region, T-434)
    assert edges()["ST01-MS1T-N01"]["bound"] == [1.15, pytest.approx(math.hypot(1.15, 1.30), abs=1e-6)]
    assert res()["held_bound_lm"] == [4.6, pytest.approx(4 * 1.735655 + 0.05, abs=1e-6)]


def test_floor_edges_and_closing_riser():
    e, ck = edges(), res()["checks"]
    assert ck["ms1u_floor_face_on_st4"] and not ck["ms2u_floor_on_any_plan"] and ck["ms2tr_face_agrees"]
    # hand: 12 risers (section A-A, Q-46 A); 11 drawn fronts s 1.15 .. 4.15 at 0.300 -> floor front 4.45;
    # slab opening ends at riser-face s 4.30 on ST p.4 and p.5 -> clash 4.50 - 4.30 = 0.200 (Q-46 RFI B20 / B23)
    assert ck["ms1u_clash_m"] == pytest.approx(0.200) and ck["ms2u_clash_m"] == pytest.approx(0.200)
    for k in ("ST01-MS1U-FLOOR", "ST01-MS2U-FLOOR", "ST01-MS2TR"):
        assert e[k]["lm"] == 1.15 and e[k]["status"] == "DRAWING-CONFIRMED"
    assert e["ST01-MS2TR"]["beside_if_diagonal_were_the_riser_m"] == pytest.approx(math.hypot(1.15, 1.15), abs=1e-6)


def test_round_stair_lengths_and_curtail_by_hand():
    e, r = edges(), data()["reading"]["RSC"]
    assert r["outer_r"] - r["inner_r"] == pytest.approx(1.150, abs=1e-6)
    c258, c25a = r["curtail"]["258"], r["curtail"]["25A"]
    hand258 = math.pi * c258["r_m"] * c258["sweep_deg"] / 180.0
    hand25a = math.pi * c25a["r_m"] * c25a["sweep_deg"] / 180.0
    assert hand258 == pytest.approx(0.949440, abs=2e-6) and hand25a == pytest.approx(0.672000, abs=2e-6)
    assert c258["chord_m"] < c258["len_m"]                       # the chord is never used
    assert e["ST02-RSC-256"]["lm"] == pytest.approx(1.150 + hand258, abs=2e-6)
    assert e["ST02-RSC-254"]["lm"] == pytest.approx(1.150 + hand25a, abs=2e-6)
    assert all(e[f"ST02-RSC-{h}"]["lm"] == 1.15 for h in ("252", "250", "24E", "24C", "24A", "248", "246", "244",
                                                          "242", "240"))
    assert all(e[k]["status"] == "ASSUMED - OWNER-APPROVED" for k in e if k.startswith("ST02-RSC-2") and "BAND" not in k)
    assert e["ST02-RSC-256-BAND"]["bound"] == [0.0, pytest.approx(0.05)]
    assert res()["checks"]["rsc_curtail_faces_match_st"]


def test_totals_and_reconciliation_close_exactly():
    R = res()
    # hand: 87.350 (T-412) + 1.150 (T-434 N05) + 3 x 1.150 + 12 x 1.150 + 0.949440 + 0.672000 = 107.371440
    assert R["nosing_after"] == {"valued_lm": pytest.approx(107.37144, abs=1e-6), "edges_valued": 85, "edges_held": 4}
    assert R["his_total"] == pytest.approx(123.20)
    assert R["his_minus_ours_total"] == pytest.approx(15.82856, abs=1e-6)
    tot = 0.0
    for st, rec in R["reconciliation"].items():
        assert rec["unexplained"] == pytest.approx(0.0, abs=1e-9)
        assert sum(c["lm"] for c in rec["causes"]) == pytest.approx(rec["his_minus_ours"], abs=1e-6)
        tot += rec["his_minus_ours"]
    assert tot == pytest.approx(15.82856, abs=1e-6)
    st01 = {c["cause"].split()[0]: c["lm"] for c in R["reconciliation"]["ST-01"]["causes"]}
    assert st01 == {"COUNT": 8.4, "HELD": 4.8, "WIDTH": 2.6, "NOTCH": 0.1}


def test_no_coordinates_or_text_committed():
    def nums(x):
        if isinstance(x, dict):
            for v in x.values():
                yield from nums(v)
        elif isinstance(x, list):
            for v in x:
                yield from nums(v)
        elif isinstance(x, (int, float)) and not isinstance(x, bool):
            yield x
    assert max(abs(v) for v in nums(data()["reading"])) <= 360.0     # run positions, radii, sweeps only
    raw = (D / "ALSENAN_EDGES_T598.json").read_text()
    assert all(ord(ch) < 128 for ch in raw)
