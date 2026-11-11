"""T-682: R-T682-1 (one slab plane in plan AND section, over R-T678-2) on hand figures of the NON-Alsenan villa V682,
and the inputs builder on the committed, sha-pinned T-678 ledger / T-677 V3.0.66 index (no drawing read).

  V682 annex: head +2.60 drawn (tol 0.01) under a printed 0.60 beam -> s_lo = 2.60 - 0.01 + 0.60 = 3.19; finished
  mark +3.60. Normal: section A-A draws a 0.20 step OUTSIDE the plane -> bounded 3.19, the step kept as checked.
  Adverse (F-V678-2): the same step INSIDE the plane -> refused; a step with no stated position -> refused (never
  assumed outside); a LEVEL text inside the outline -> refused; a step 200 (mm as m) -> refused; a section with no
  evidence -> refused; no outline -> refused; s_lo above the finished mark -> FLAGGED (R-T678-2 unchanged)."""
from __future__ import annotations

import copy
import json
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t682"))

import t682_inputs as L  # noqa: E402
import t682_rules as R  # noqa: E402

HEADS = [{"id": "H1", "head_abs": "2.60", "tol": "0.01", "status": "DRAWING-CONFIRMED", "beam_depth": "0.60"}]


def plane(**kw):
    p = {"outline": "V682 annex roof", "plan_texts_inside": [],
         "section_steps": [{"section": "A-A", "step_m": "0.20", "inside_plane": False, "evidence": "drawn east"}]}
    p.update(kw)
    return p


def test_one_plane_normal():
    r = R.slab_top_lower_bound(heads=HEADS, plane=plane(), finished_ceiling="3.60")
    assert r["state"] == "BOUNDED" and Decimal(r["s_lo"]) == Decimal("3.19") and r["governing"] == "H1"
    assert r["plane"]["state"] == "ONE_PLANE" and r["plane"]["steps_outside"][0]["section"] == "A-A"
    assert r["plane"]["sections_checked"] == ["A-A"] and r["rule"].startswith("R-T682-1")


def test_zero_step_is_no_step():
    p = plane(section_steps=[{"section": "B-B", "step_m": "0", "evidence": "flat"}])
    assert R.check_plane(p)["steps_outside"] == []


@pytest.mark.parametrize("kw,msg", [
    ({"section_steps": [{"section": "A-A", "step_m": "0.20", "inside_plane": True, "evidence": "x"}]}, "inside the plane"),
    ({"section_steps": [{"section": "A-A", "step_m": "0.20", "evidence": "x"}]}, "not stated"),
    ({"plan_texts_inside": [{"text": "+3.40", "kind": "LEVEL"}]}, "two planes"),
    ({"plan_texts_inside": [{"text": "T 20", "kind": "THICKNESS"}]}, "two planes"),
    ({"section_steps": [{"section": "A-A", "step_m": "200", "inside_plane": False, "evidence": "x"}]}, "in metres"),
    ({"section_steps": [{"section": "A-A", "step_m": "0.20", "inside_plane": False}]}, "evidence"),
    ({"outline": None}, "outline"),
])
def test_stepped_or_unchecked_plane_refused(kw, msg):
    with pytest.raises(R.Refused, match=msg):
        R.slab_top_lower_bound(heads=HEADS, plane=plane(**kw), finished_ceiling="3.60")


def test_contradiction_flagged_unchanged():
    r = R.slab_top_lower_bound(heads=HEADS, plane=plane(), finished_ceiling="3.10")
    assert r["state"] == "FLAGGED"


# ------------------------------------------------------------------------------------------------ inputs builder
def test_build_on_committed_ledger():
    d = L.build("P")
    s = L.summary(d)
    assert s["entries"] == 11 and s["by_code_action"] == {"STR.CONC.COLUMN BOUND": 2, "STR.CONC.LINTEL BOUND": 7,
                                                          "STR.CONC.LINTEL LOWER_ONLY": 2}
    trig = dict(s["assumed_owner_approved"])
    assert trig == {"D-1F-05": 3.19, "D-1F-06": 3.44, "D-GF-01": 2.584, "D-GF-02": 2.234, "D-GF-03": 2.234,
                    "D-GF-04": 2.234}                                         # F-V678-1: 2.20 + spare
    assert s["plane"] == 5                                                     # 4 annex doors + C3 (F-V678-2)
    by = {e["member"].split(" ")[1]: e for e in d["entries"] if e["expect"]["item_code"] == "STR.CONC.LINTEL"}
    lo = sum(Decimal(str(e["after"]["low"] if e["action"] == "BOUND" else e["beside"]["value"])) for e in by.values())
    hi = sum(Decimal(str(e["after"]["high"])) for e in by.values() if e["action"] == "BOUND")
    assert (lo, hi) == (Decimal("0.520"), Decimal("0.554224"))
    assert {k for k, e in by.items() if e["action"] == "LOWER_ONLY"} == {"D-1F-06", "D-GF-04"}
    assert by["D-GF-07"]["existence"]["status"] == "DRAWING-CONFIRMED" and "assumption" not in by["D-GF-07"]
    assert "2.234" in by["D-GF-02"]["assumption"]["rerun_trigger"]
    cols = {e["line_id"]: e for e in d["entries"] if e["expect"]["item_code"] == "STR.CONC.COLUMN"}
    assert cols[L.PC2F]["after"] == {"low": 0.1824, "high": 0.35}
    assert cols[L.C3]["after"] == {"low": 0.41175, "high": 0.50625} and cols[L.C3]["plane"]["s_lo_m"] == 3.544
    assert all(e["expect"]["low"] is None and e["expect"]["class"] == "HELD" for e in d["entries"])
    x = d["expect_totals"]                                   # V3.0.66 (T-677 run of record) + this package, by hand
    assert x["STR.CONC.LINTEL|m3"] == {"released": 1.016, "lines": 61, "bounded_lines": 24, "blocked_lines": 21,
                                       "held_low": 1.361, "held_high": 2.050636}
    assert x["STR.CONC.COLUMN|m3"] == {"released": 19.7765, "lines": 59, "bounded_lines": 22, "blocked_lines": 7,
                                       "held_low": 10.26435, "held_high": 13.27025}
    txt = json.dumps(d)
    assert "@" not in txt.replace(json.dumps(cols[L.C3]["expect"]["element_id"])[1:-1], "")   # no new coordinate


def test_engine_accepts_the_built_inputs():
    from engine.source import arch_v3067 as A
    d = A.load_inputs(L.build("P"), "P")
    assert len(d["_entries"]) == 11


def test_lintel_hand_refuses_a_tampered_row():
    led = json.loads(L.T678.read_text(encoding="utf-8"))
    r = copy.deepcopy(next(x for x in led["lintels"] if x["opening"] == "D-GF-07"))
    assert L.lintel_hand(r)[:2] == (Decimal("0.096000"), Decimal("0.108000"))
    r["ends"][0][3] = "0.450000"                                              # START now >= 0.40: the low changes
    assert L.lintel_hand(r)[0] == Decimal("0.112000")
    r2 = copy.deepcopy(next(x for x in led["lintels"] if x["opening"] == "D-1F-06"))
    r2["high_m3"] = "0.05"                                                    # an open end given a high: refused
    with pytest.raises(SystemExit, match="open"):
        L.lintel_hand(r2)


def test_pins_refuse_an_edited_ledger(monkeypatch):
    monkeypatch.setitem(L.PINS, L.T678, "0" * 64)
    with pytest.raises(SystemExit, match="edited file"):
        L.build()
