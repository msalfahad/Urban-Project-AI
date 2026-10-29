"""T-325 development-villa pins on the committed ledger (research/agents_t325, written by t325_alsenan.py from the
candidate of record V3.0.20 and the merged T-249 / T-313 / T-240 / T-321 ledgers). No private input is read here."""

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "research" / "agents_t325"


def rd(name):
    with open(D / name, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_every_census_opening_component_once():
    rows = rd("SILL_THRESHOLD_LEDGER_T325.csv")
    keys = [(r["opening"], r["component"]) for r in rows]
    assert len(keys) == len(set(keys))
    census = {r["ID"] for r in csv.DictReader(open(ROOT / "research" / "agents_t249" / "OPENINGS_T249.csv",
                                                     encoding="utf-8"))}
    assert {r["opening"] for r in rows} == census and len(census) == 59


def test_one_line_one_opening_and_no_component_in_two_lines():
    rows = rd("SILL_THRESHOLD_LEDGER_T325.csv")
    bound = [r for r in rows if r["binding"] == "BOUND"]
    lids = [r["line_id"] for r in bound]
    assert len(lids) == len(set(lids))
    per = {}
    for r in bound:
        per.setdefault((r["opening"], r["component"]), []).append(r["line_id"])
    assert all(len(v) == 1 for v in per.values())


def test_floor_level_window_thresholds_only_in_their_reveal_line():
    rows = {(r["opening"], r["component"]): r for r in rd("SILL_THRESHOLD_LEDGER_T325.csv")}
    lines = rd("LINES_T325.csv")
    for w in ("W15", "W16", "W25", "W27"):
        r = rows[(w, "THRESHOLD_OUT")]
        assert r["state"] == "MEASURED"
        carriers = [l for l in lines if w in l["census"].split(";")]
        assert [l["item_code"] for l in carriers] == ["ARCH.WINDOW_REVEAL"]


def test_held_and_unresolved_never_zero_and_material_never_invented():
    for r in rd("SILL_THRESHOLD_LEDGER_T325.csv"):
        if r["state"] in ("UNRESOLVED",):
            assert r["m2"] == ""
        if r["component"] in ("SILL_OUT", "SILL_IN") and r["state"] == "MEASURED":
            assert r["material"] == "UNKNOWN"          # no printed specification, no owner rule
        if r["component"] == "FINISH_CHANGE_EDGE":
            assert r["line_id"] == "NOT_AN_ITEM"


def test_line_reconciliation_has_no_unexplained_difference():
    for r in rd("LINE_RECONCILIATION_T325.csv"):
        assert not r["verdict"].startswith(("DIFFERS", "OUTSIDE_BOUND")), r


def test_strips_are_in_no_room_floor():
    for r in rd("STRIP_FLOOR_OVERLAP_T325.csv"):
        assert float(r["overlap_with_room_floors_m2"]) < 0.001, r


def test_summary_pins():
    s = json.loads((D / "summary.json").read_text(encoding="utf-8"))
    assert s["inputs"]["plan_sha8"] == "ab54dd55"
    assert s["census_openings"] == 59
    assert s["freelancer"]["threshold_or_sill_rows"] == 0
    assert abs(s["freelancer"]["door_step_length_sum_m"] - 7.7) < 1e-9
    t = s["totals"]
    assert abs(t["SILL_OUT|UNKNOWN|MEASURED"]["m2"] - 2.5614) < 1e-6          # = T-313 external sills
    assert abs(t["THRESHOLD|MARBLE|MEASURED"]["m2"] - 1.82) < 1e-6
