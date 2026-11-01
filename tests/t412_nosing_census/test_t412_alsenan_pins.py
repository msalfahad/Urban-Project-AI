"""T-412 development-villa pins on the committed edge table (research/agents_t412, built by t412_alsenan.py from the
private architectural DXF by handle; recomputed here from the committed ALSENAN_EDGES_T412.json, no private input)."""

import csv
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "research" / "agents_t412"


def edges():
    with open(D / "NOSING_TABLE_T412.csv", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_reproduces_from_committed_edges():
    p = subprocess.run([sys.executable, "-I", str(D / "t412_alsenan.py"), "--check"], capture_output=True, text=True)
    assert p.returncode == 0 and "REPRODUCED" in p.stdout, p.stdout + p.stderr


def test_totals_hand_checked():
    s = json.loads((D / "summary.json").read_text())
    st = s["per_stair"]
    # ST-01: MS1-L 10 x 1.150 - 0.050 (2FBD at s 0.6) + MS1-U 11 x 1.150 + MS2-L 12 x 1.150 - 0.050 (3005 at s 1.2)
    #        + MS2-U 11 x 1.150 + D1 4 x 1.150 = 11.45 + 12.65 + 13.75 + 12.65 + 4.60 = 55.10
    assert st["ST-01"]["nosing_lm_confirmed"] == pytest.approx(55.10, abs=1e-9)
    # ST-02 straight parts: RS-S 11 x 1.150 - 3 x 0.050 (2FD2 at s 0.3 / 0.6 / 0.9) + RS-A 5 x 1.150 = 18.25
    assert st["ST-02"]["nosing_lm_confirmed"] == pytest.approx(18.25, abs=1e-9)
    assert st["ST-03"]["nosing_lm_confirmed"] == pytest.approx(5 * 2.80, abs=1e-9)
    assert s["totals"]["nosing_lm_confirmed"] == pytest.approx(87.35, abs=1e-9)
    # landing / floor edges outside the B7-06 step basis: MS2-LD 1.15 + D1 floor 1.15 + E1 2.80 + RS-LD 1.15 + RS-A 1.15
    assert s["totals"]["nosing_lm_confirmed_landing_floor"] == pytest.approx(7.40, abs=1e-9)
    # held beside the blank: winder fronts 1.259 + 1.626 + 1.259 (+ band 1.150), 2 floor edges 1.150, RS-C 11 x 1.150
    # + 1.200
    assert st["ST-02"]["held_beside_lm"] == pytest.approx(11 * 1.15 + 1.2, abs=1e-9)


def test_every_riser_has_one_nosing_and_counts():
    s = json.loads((D / "summary.json").read_text())["per_stair"]
    assert (s["ST-01"]["risers"], s["ST-02"]["risers"], s["ST-03"]["risers"]) == (56, 28, 5)
    assert (s["ST-01"]["treads"], s["ST-02"]["treads"], s["ST-03"]["treads"]) == (50, 26, 4)
    assert len(edges()) == 89


def test_notched_edges_are_the_proud_columns():
    s = json.loads((D / "summary.json").read_text())
    assert s["notched_edges"] == ["ST01-MS1L-N03", "ST01-MS2L-N05", "ST02-RSS-N02", "ST02-RSS-N03", "ST02-RSS-N04"]


def test_held_rows_blank_and_caused():
    for r in edges():
        if r["status"] != "DRAWING-CONFIRMED":
            assert r["qty_lm"] == "" and r["cause"], r["eid"]
        else:
            assert float(r["qty_lm"]) > 0 and not r["cause"], r["eid"]


def test_no_front_edge_shared_with_skirting_or_railing():
    with open(ROOT / "research" / "agents_t410" / "SIDE_TABLE_T410.csv", newline="", encoding="utf-8") as f:
        side = list(csv.DictReader(f))
    side_ids = {r["sid"] for r in side} | {b for r in side for b in r["binds"].split()}
    ids = {r["eid"] for r in edges()}
    assert not ids & side_ids
    assert all(b.startswith("B7-05:") for r in edges() for b in r["binds"].split())


def test_freelancer_pieces_quantities_only():
    rec = {x["stair"]: x for x in json.loads((D / "summary.json").read_text())["freelancer_pieces_vs_risers"]}
    assert rec["ST-03"]["his_minus_ours"] == 0 and rec["ST-02"]["his_minus_ours"] == 0
    assert rec["ST-01"]["his_minus_ours"] == 7


def test_second_drawing_cross_read():
    st = json.loads((D / "ALSENAN_EDGES_T412.json").read_text())["st_cross_read"]
    assert st["p5_west_MS2-L"]["lines"] == 12 and st["D1"]["lines"] == 4 and st["p4_RS-C_radial"]["lines"] == 12
    assert st["p4_east_MS1-U"]["lines"] == 12 and st["p5_east_MS2-U"]["lines"] == 11
    # the MS1-L / winder split differs between the drawings: the turn stays HELD (all 5 edges)
    assert st["p4_west_MS1-L"]["lines"] == 12 and st["p4_turn_radial"]["lines"] == 3
    held = [r for r in edges() if r["flight"] == "MS1-T"]
    assert len(held) == 5 and all(r["status"] == "HELD" and r["qty_lm"] == "" for r in held)
    assert all(abs(v["width_m"] - 1.150) < 1e-9 for v in st.values() if "width_m" in v)


def test_candidate_binding_pinned():
    b = json.loads((D / "CANDIDATE_BINDING_T412.json").read_text())
    assert b["candidate"] == "ARCH_TAKEOFF_V3.0.35" and b["sha256"].startswith("b011bace")
    assert b["nosing_lines_in_candidate"] == 0 and len(b["flights"]) == 14
    by = {r["engine_flight"]: r for r in b["flights"]}
    assert by["SITE-3759f2457b22cb4a:F1"]["drawn_flight"] == "MS1-L" and by["SITE-3759f2457b22cb4a:F1"]["engine_treads"] == 7
    assert by["SITE-a95bf979baf4cfae:F2"]["drawn_treads"] == by["SITE-a95bf979baf4cfae:F2"]["engine_treads"] == 11
    assert by["SITE-a95bf979baf4cfae:F5"]["drawn_flight"] is None
    for r in b["flights"]:
        assert r["lines"]["FIN.MARBLE.TREAD"]["line_id"].startswith("L-")
