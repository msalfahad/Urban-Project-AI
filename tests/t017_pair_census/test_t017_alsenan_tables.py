"""T-017: the committed development-villa agreement tables are complete and internally consistent (offline: the drawing
is private; `research/agents_t017/alsenan_t017.py ... --check` reproduces them byte for byte from the drawing)."""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "research" / "agents_t017"
STATUSES = {"AGREE", "DIFFERS", "NOT_READ_OR_NOT_FOUND"}
VERDICTS = {"RULE_DIFFERENCE", "UNRESOLVED", "ENGINE_RIGHT", "FREELANCER_RIGHT"}


def rows():
    return list(csv.DictReader(open(D / "T017_WALL_AGREEMENT.csv", encoding="utf-8")))


def test_every_ledger_wall_listed_once():
    hand = [r["row_id"] for r in csv.DictReader(open(ROOT / "research/agents_t143/T143_BLOCK_BY_WALL_RUN.csv", encoding="utf-8"))]
    got = [r["row_id"] for r in rows()]
    assert len(hand) == 75 and sorted(got) == sorted(hand) and len(set(got)) == 75


def test_statuses_causes_and_tolerance():
    for r in rows():
        assert r["status"] in STATUSES
        if r["status"] == "AGREE":
            assert abs(float(r["census_minus_ledger_m"])) <= 0.05 and not r["cause"]
        else:
            assert r["cause"] and r["verdict_proposal"] in VERDICTS and r["why"]
        if r["status"] == "NOT_READ_OR_NOT_FOUND":
            assert r["census_arch_run_m"] == ""          # never 0
        if r["t_census_m"]:
            assert float(r["t_census_m"]) == float(r["t_ledger_m"])


def test_floor_thickness_identity():
    """census - ledger per floor and thickness = sum of the row differences + minus the rows the census did not read
    (the merged 1F-W14 + 1F-W15 run counted once)."""
    want = defaultdict(float)
    seen = set()
    for r in rows():
        key = r["ledger_row (T-108 r2)"] or r["row_id"]
        if key in seen:
            continue
        seen.add(key)
        k = (r["floor"], f"{float(r['t_ledger_m']):.2f}")
        if r["census_minus_ledger_m"]:
            want[k] += float(r["census_minus_ledger_m"])
        elif r["ledger_physical_m (Q-69 B)"]:
            want[k] -= float(r["ledger_physical_m (Q-69 B)"])
    for f in csv.DictReader(open(D / "T017_BY_FLOOR_THICKNESS.csv", encoding="utf-8")):
        k = (f["floor"], f["t_m"])
        assert abs(float(f["census_minus_ledger_m"]) - want.get(k, 0.0)) <= 0.002, k


def test_census_components_add_up():
    for f in csv.DictReader(open(D / "T017_BY_FLOOR_THICKNESS.csv", encoding="utf-8")):
        parts = (float(f["census_both_faces_m (columns drawn through included)"]) - float(f["census_column_cut_m"])
                 + float(f["census_openings_in_run_m"]) + float(f["census_one_face_m"])
                 + float(f["census_corner_extensions_m"]) + float(f["census_crossings_m"]))
        assert abs(parts - float(f["census_arch_run_m"])) <= 0.002, f["floor"] + f["t_m"]


def test_no_drawing_coordinates_in_committed_tables():
    for name in ("T017_WALL_AGREEMENT.csv", "T017_BAND_AGREEMENT.csv", "T017_BY_FLOOR_THICKNESS.csv", "summary.json"):
        head = (D / name).read_text().splitlines()[0].lower()
        for word in ("_x", "_y", "coord", "origin", "centre_m", "position"):
            assert word not in head, (name, word)
    s = json.loads((D / "summary.json").read_text())
    assert "\"_a\"" not in json.dumps(s) and "\"_off\"" not in json.dumps(s) and s["rows"]["total"] == 75
