"""T-607 development-villa pins on the committed reading (research/agents_t607/T607_DRAWN.json, built by
t607_extract.py from the private DXFs by handle) and on the committed build (out/T607_SHARED_RESIDUAL.json), plus a
re-read of the private drawings when they are present (skipped otherwise)."""
from __future__ import annotations

import csv
import importlib
import json
import os
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "research" / "agents_t607"
PRIV = ROOT.parents[1] / ".work" / "private"
ARCH = Path(os.environ.get("T607_DXF", PRIV / "P7757_DXF_COMPRESSED" / "P7757.dxf"))
ST = Path(os.environ.get("T607_ST", PRIV / "ST7757.dxf"))


def drawn():
    return json.loads((D / "T607_DRAWN.json").read_text())


def out():
    return json.loads((D / "out" / "T607_SHARED_RESIDUAL.json").read_text())


def test_reproduces_from_committed_inputs():
    p = subprocess.run([sys.executable, "-I", str(D / "t607_alsenan.py"), "--check"], capture_output=True, text=True)
    assert p.returncode == 0 and "REPRODUCED" in p.stdout, p.stdout + p.stderr


@pytest.mark.skipif(not (ARCH.exists() and ST.exists()), reason="private drawings absent (decode into .work/private)")
def test_private_reread_equals_committed():
    p = subprocess.run([sys.executable, "-I", str(D / "t607_extract.py"), "--dxf", str(ARCH), "--st", str(ST)],
                       capture_output=True, text=True)
    assert p.returncode == 0 and "SAME AS COMMITTED" in p.stdout, p.stdout + p.stderr


def test_every_stair_line_in_the_shaft_is_classed():
    d = drawn()
    cls = {}
    for rows in d["plans"].values():
        for r in rows:
            cls[r["cls"]] = cls.get(r["cls"], 0) + 1
    assert cls.get("UNMATCHED", 0) == 0
    assert {r["handle"] for rows in d["plans"].values() for r in rows if r["cls"] == "NAMED_OPEN"} == {"2F1F", "2F20"}
    for k, v in d["registration"].items():
        assert v["votes"] > 2 * v["runner_up_votes"], k
    assert all(r["residual_mm"] <= 2.0 for rows in d["plans"].values() for r in rows if "residual_mm" in r)


def test_governing_count_56_from_the_census():
    o = out()
    assert o["governing"]["risers_by_storey"] == {"GF->1F": 27, "1F->2F": 25, "D1 lobby": 4}
    assert o["governing"]["total"] == 56 == o["governing"]["edges"]
    # second drawing: ST p.4 12 + 3 + 1 + 12, ST p.5 12 + 1 + 11 (+ the diagonal face, Q-ST-11)
    s = o["structural_second_drawing"]
    assert s["ST_P4"] == {"west_lane_MS1L": 12, "turn_radials": 3, "closing_face": 1, "east_lane_MS1U": 12}
    assert s["ST_P5"] == {"west_lane_MS2L": 12, "closing_face": 1, "diagonal_face": 1, "east_lane_MS2U": 11}
    assert drawn()["structural"]["ST_P5"]["diagonal_vs_arch_2F20_mm"] == 0.0


def test_shared_edge_table_one_line_per_edge():
    o = out()
    rows = o["shared_edge_table"]
    assert len(rows) == 56 and len({r["edge"] for r in rows}) == 56 and all(r["claims"] == 1 for r in rows)
    fam = [r["family"] for r in rows]
    assert fam.count("STEP") == 50 and fam.count("NOSING") == 6
    assert all(r["lm"] is None for r in rows if r["status"] == "HELD")
    per = o["edges_per_pricing_line"]
    assert per["L-e085c168dee5fb19a7fb"] == 5 and per["L-d4d764ae7bb07b474b6f"] == 9
    assert "L-1e88ac0d4ba0b4e8a950" not in per          # the MS2-L second reading claims no edge


def test_step_line_ids_equal_the_merged_t584_table():
    sys.path.insert(0, str(D))
    sys.path.insert(0, str(ROOT / "research" / "agents_t584"))
    sys.path.insert(0, str(ROOT / "research" / "agents_t577"))
    A = importlib.import_module("t607_alsenan")
    T584 = importlib.import_module("t584_alsenan")
    st01 = {fl: lid for lid, (stair, fl, _, disp) in T584.STEP_LINES.items() if stair == "ST-01" and disp != "SECOND_READING"}
    assert st01 == A.STEP_LINE_OF
    sec = [lid for lid, (stair, _, _, disp) in T584.STEP_LINES.items() if stair == "ST-01" and disp == "SECOND_READING"]
    assert tuple(sec) == A.SECOND_STEP_LINES


def test_the_seven_pieces_by_edge_and_by_storey():
    o = out()
    c = o["causes"][0]
    assert c["nr"] == 7 == int(o["his"]["ST-01"]["nr"]) - 56
    assert Decimal(c["lm_his_basis"]) == 7 * Decimal("1.2") == Decimal("8.4")
    r1 = c["named_readings"]["R1 SECOND_READING"]
    assert r1["edges_repeated"] == [f"ST01-MS1U-N{n:02d}" for n in range(5, 12)]
    r2 = c["named_readings"]["R2 STOREY_ESTIMATE"]
    assert r2["pieces_by_storey"] == {"D1 lobby": 1, "GF->1F": 3, "1F->2F": 3}    # 5-4, 30-27, 28-25
    assert r2["riser_mm"] == ["150.0", "155.0"]
    assert c["verdict"] == "ENGINE_RIGHT" and "never chosen" in c["his_mechanism"]


def test_only_the_gf_east_pairs_reproduce_without_a_rejected_reading():
    rep = out()["reproductions"]
    adm = [x for x in rep["second_reading_sets"] if x["admissible"]]
    assert len(adm) == rep["admissible"] == 1
    assert list(adm[0]["parts"]) == ["GF east lane, 7 pairs above the cut (= MS1-U N05..N11)"]
    # every exact combination, admissible or not, contains the 7 GF east pairs
    assert all(any(k.startswith("GF east lane") for k in x["parts"]) for x in rep["second_reading_sets"])
    # the same storey estimate does not give his other two stairs (reported, never used to choose)
    other = rep["storey_estimate_on_his_other_stairs"]
    assert all(Decimal(h["riser_mm"][0]) > Decimal("155") for v in other.values() for h in v)


def test_shared_cause_counted_once_and_units_kept():
    s = out()["shared"]
    assert s["total_once"] == [7, "8.4"]
    assert {k: v[1] for k, v in s["per_line"].items()} == {"T-584/stair-steps-lm": "lm", "T-584/stair-steps-nr": "nr",
                                                           "T-598/nosing@V9 lm": "lm", "T-598/nosing@V9 nr": "nr"}
    assert "16.8" in s["refused"]


def test_no_coordinates_or_text_in_committed_files():
    for f in (D / "T607_DRAWN.json", D / "out" / "T607_SHARED_RESIDUAL.json"):
        t = f.read_text()
        assert t.isascii()
        js = json.loads(t)

        def walk(o):
            if isinstance(o, dict):
                for k, v in o.items():
                    assert k not in ("x", "y", "mx", "my", "dx", "dy", "ends"), k
                    walk(v)
            elif isinstance(o, list):
                for v in o:
                    walk(v)
            elif isinstance(o, (int, float)) and not isinstance(o, bool):
                assert abs(o) < 10000, o         # lengths, angles, counts, votes, residuals: never a drawing coordinate (~1e5 mm)
        walk(js)


def test_census_input_is_the_merged_t412_table():
    rows = [r for r in csv.DictReader((ROOT / "research" / "agents_t412" / "NOSING_TABLE_T412.csv").open())
            if r["stair"] == "ST-01"]
    assert len(rows) == 56
