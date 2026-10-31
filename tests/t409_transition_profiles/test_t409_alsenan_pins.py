"""T-409 development-villa pins on the committed boundary table (research/agents_t409, written by t409_alsenan.py
from the merged T-325 / T-312 / T-303 / T-296 ledgers). No private input is read here."""

import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "research" / "agents_t409"


def rows():
    with open(D / "BOUNDARY_TABLE_T409.csv", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_reproduces_from_committed_ledgers():
    p = subprocess.run([sys.executable, "-I", str(D / "t409_alsenan.py"), "--check"], capture_output=True, text=True)
    assert p.returncode == 0 and "REPRODUCED" in p.stdout, p.stdout + p.stderr


def test_every_census_door_and_arch_once():
    ids = [r["id"] for r in rows()]
    assert len(ids) == len(set(ids)) == 40
    with open(ROOT / "research" / "agents_t325" / "SILL_THRESHOLD_LEDGER_T325.csv", encoding="utf-8") as f:
        census = {r["opening"] for r in csv.DictReader(f) if r["kind"] in ("DOOR", "ARCH")}
    assert len(census) == 30 and census <= set(ids)


def test_marble_never_also_a_strip_and_held_never_zero():
    for r in rows():
        if r["class"] == "RULE_INTERFACE":
            assert r["threshold"] == "MARBLE" and r["qty_ml"] == "0.000000"
        if r["status"] in ("HELD", "UNKNOWN"):
            assert r["qty_ml"] == ""
        if r["status"] == "HELD":
            assert r["bound_lo_ml"] == "0.000000" and float(r["bound_hi_ml"]) > 0


def test_class_counts_and_held_bound():
    s = json.loads((D / "summary.json").read_text())
    c = {k: v["n"] for k, v in s["by_class"].items()}
    assert c == {"RULE_INTERFACE": 17, "NO_FINISH_CHANGE": 7, "SILL_HELD": 6, "INTERFACE_HELD": 2,
                 "OTHER_ELEMENT": 5, "UNRESOLVED": 3}
    assert s["transition_profile"] == {"released_ml": 0.0, "held_rows": 8, "held_bound_ml": [0.0, 19.09],
                                       "unknown_rows": 3}
    assert s["by_class"]["RULE_INTERFACE"]["width_ml"] == 14.645
    hp = s["hidden_profile_us08"]
    assert hp["status"] == "HELD" and hp["qty_ml"] is None and hp["path_ml"] == [179.186752, 205.149668]


def test_basin_space_openings_take_the_q06_marble_threshold():
    r = {x["id"]: x for x in rows()}
    for oid in ("A-GF-01", "P-GF-01", "OPEN-GF-14"):
        assert r[oid]["class"] == "RULE_INTERFACE" and "Q-06" in r[oid]["why"]
    assert r["OPEN-GF-07"]["class"] == "INTERFACE_HELD"      # pantry: marble rule not applicable by name
    assert r["A-1F-01"]["class"] == "INTERFACE_HELD"         # dressing floor material HELD
