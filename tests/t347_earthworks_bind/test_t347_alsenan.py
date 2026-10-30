"""T-347 development-villa checks on the COMMITTED outputs (the T-332 lesson: test what a consumer reads)."""

import csv
import io
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t347"
sys.path.insert(0, str(HERE))
import t347_alsenan as A  # noqa: E402
import t347_rules as R  # noqa: E402


def _rows(name):
    return list(csv.DictReader(io.StringIO((HERE / name).read_text(encoding="utf-8"))))


@pytest.fixture(scope="module")
def built():
    return A.main([])


def test_byte_rebuild(built):
    for name, text in built.items():
        assert (HERE / name).read_text(encoding="utf-8") == text, name


def test_candidate_is_v3024_of_record():
    c = json.loads((HERE / "CANDIDATE_V3024_BURIED_LINES.json").read_text(encoding="utf-8"))
    assert c["candidate"] == "ARCH_TAKEOFF_V3.0.24"
    assert c["candidate_lines_json_sha256"].startswith("19394733")       # T-338 record of V3.0.24
    assert c["earthworks_lines_in_candidate"] == []                       # B1-02 .. B1-04 not integrated


def test_every_displacement_row_bound_once():
    rows = _rows("BINDING_T347.csv")
    t320 = _rows("../agents_t320/LEDGER_T320.csv")
    ids = [r["id"] for r in rows]
    assert len(ids) == len(set(ids))
    # 222 T-320 rows - the pool envelope + 9 pool components + 27 underlay rows split in two
    assert len(rows) == len(t320) - 1 + 9 + sum(r["kind"] == "UNDERLAY" for r in t320)
    for r in rows:
        assert (r["line_id"] != "") == (r["binding"] != "NO_LINE"), r["id"]
        if r["binding"] == "NO_LINE":
            assert r["reason"], r["id"]
    covered = {r["id"].replace(":SCREED", "").replace(":MEMBRANE", "") for r in rows}
    for r in t320:
        assert r["id"] == "POOL:ENVELOPE" or r["id"] in covered


def test_closures_on_valued_lines():
    s = json.loads((HERE / "summary_t347.json").read_text(encoding="utf-8"))
    pl = s["per_line"]
    footings = [p for p in pl.values() if p["item_code"] == "STR.CONC.FOOTING" and p["value_m3"] > 0]
    assert len(footings) == 24 and all(abs(p["closure_m3"]) < 1e-6 for p in footings)
    assert pl["L-4ec54f9922da7281573a"]["closure_m3"] == pytest.approx(0.0, abs=1e-6)    # screed 5.4925
    assert pl["L-69e6e6d74707afe3ac5b"]["value_m3"] == pytest.approx(109.85, abs=1e-6)  # membrane m2 = T-219
    assert pl["L-98eb2d58075c9eddf1b4"]["closure_m3"] == pytest.approx(2.256, abs=1e-5)  # = the HELD FF blinding
    assert pl["L-d2c75eb10451e4dd1db5"]["value_m3"] == pytest.approx(0.258, abs=1e-6)   # FN net of F9 (D-32)
    assert pl["L-15a128c38982af899894"]["closure_m3"] == pytest.approx(0.0, abs=1e-6)   # pool walls 2.121 + 0.707


def test_over_line_findings_named():
    s = json.loads((HERE / "summary_t347.json").read_text(encoding="utf-8"))
    over = {o["line_id"]: o for o in s["over_line_findings"]}
    assert set(over) >= {"L-c823e0dbd81e30c66aa5", "L-35382b18e2e362df3ae6", "L-6290a9f3d93f38cd46d6"}
    assert all(o["cause"] and o["verdict"] for o in over.values())
    assert over["L-c823e0dbd81e30c66aa5"]["carried"] == pytest.approx(0.2683)


def test_fill_held_blank_never_zero():
    for r in _rows("FILL_T350_T347.csv"):
        R.check_fill_row({k: (v if v != "" else None) for k, v in r.items()})
        if r["status"] == "HELD":
            assert r["value_m3"] == ""
        if r["status"] == "ZERO_BY_BOUND":
            assert r["value_m3"] == "" and r["hi_m3"] == "0.000000" and r["held_items"]


def test_fill_pits_bound_by_hand():
    rows = {r["zone"].split(" ")[0] + "|" + r["family"]: r for r in _rows("FILL_T350_T347.csv")}
    pits = rows["Z1-PITS-24|B1-02 EXCAVATION"]
    # hand: neat 129.570 - real overlaps 0.330 (F9 / FN) - 0.005625 (F8 / FN) = 129.234375 m2;
    # - D-14 beyond plot 1.890 m2 - F8 neat in the pool envelope 1.99957 m2 = 125.344805 m2 x 1.50 = 188.017207 m3
    assert float(pits["lo_m3"]) == pytest.approx((129.57 - 0.33 - 0.005625 - 1.89 - 1.99957) * 1.5, abs=1e-5)
    assert pits["value_m3"] == "" and pits["hi_m3"] == ""
    pool = rows["Z1-POOL|B1-02 EXCAVATION"]
    assert float(pool["lo_m3"]) == pytest.approx(17.776576, abs=1e-6)
    assert rows["ALL|B1-04 DISPOSAL"]["value_m3"] == ""


def test_pits_and_overlaps_listed():
    pits = _rows("PITS_T347.csv")
    assert len(pits) == 26
    assert sum(p["neat_status"] == "DRAWING-CONFIRMED" for p in pits) == 24
    assert all(p["outline_handle"] for p in pits if p["neat_status"] == "DRAWING-CONFIRMED")
    ov = _rows("OVERLAPS_T347.csv")
    assert len(ov) == 30
    assert sum(float(o["neat_overlap_m2"]) > 0 for o in ov) == 2
