"""T-739 on the development villa: the committed statement equals a rebuild from sha-pinned merged files, the keyed
freelancer ranges reproduce the SCOREBOARD v2 cells restated on V3.0.73, every HELD line carries a cause and no HELD
line is summed. Repository files only (no drawing, no Drive)."""
from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t739"))
import t739_alsenan as A  # noqa: E402
import t739_rules as R  # noqa: E402


@pytest.fixture(scope="module")
def built():
    return A.build()


def test_committed_output_equals_rebuild(built):
    assert A.JSON_OUT.read_text(encoding="utf-8") == A.dumps(built)
    assert A.MD_OUT.read_text(encoding="utf-8") == A.render_md(built)


def test_every_line_once_and_states(built):
    assert built["line_count"] == 5123
    assert built["state_count"] == {"BLANK": 1602, "BOUNDED": 1163, "EXCLUDED": 843, "RELEASED": 1515}
    assert sum(sum(t["counts"].values()) for t in built["trades"]) == 5123


def test_held_never_summed_into_a_total(built):
    for t in built["trades"]:
        held = sum(t["counts"][s] for s in R.HELD_STATES)
        assert (t["total"] is None) == (held > 0), t


def test_every_held_line_has_a_cause(built):
    h = built["held"]
    assert h["lines"] == 2765 and h["findings_F_T739_1"] == 0
    assert all(r["cause"] and r["cause_class_t716"] for r in h["rows"])
    assert all(not r["cause_source"].startswith("T-662") for r in h["rows"])


def test_chain_readd(built):
    ch = built["chain_readd_v3_0_72_to_v3_0_73"]
    assert ch == {"package_rows": 33, "rows_checked_before_after": 33, "lines_changed": 5,   # NARROW 5; the 10 AT_LEAST + 18 NAMED rows move no index field
                  "other_lines_byte_equal": 5090}


SCOREBOARD_V2 = {   # cells of SCOREBOARD v2 (board, Verifier, restated on V3.0.73 2026-11-12 03:44 .. 09:59 UTC)
    "CONC.BLINDING": "at least -56.70 %, upper end open", "CONC.FOOTING": "-2.69 .. +5.18 %",
    "CONC.GROUND": "at least -37.97 %, upper end open", "CONC.COLUMN": "at least +1.50 %, upper end open",
    "CONC.BEAM": "at least +10.52 %, upper end open", "CONC.SLAB": "+0.77 %",
    "CONC.STAIR_DOME": "at least -52.14 %, upper end open", "CONC.POOL": "at least -41.67 %, upper end open",
    "PAINT.INTERNAL_WALL": "-31.25 .. -24.48 %", "DOORS.ALUMINIUM": "+6.33 %",
    "WINDOWS.ALUMINIUM": "at least -26.33 %, upper end open"}


def test_keyed_reproduces_scoreboard(built):
    k = {r["key"]: r for r in built["freelancer_keyed"]}
    for key, cell in SCOREBOARD_V2.items():
        assert k[key]["compare"] == cell, key
    assert "-14.83 .. -8.82" in k["PLASTER.INTERNAL"]["compare"] and "%" not in k["PLASTER.INTERNAL"]["released"]
    assert k["FLOOR.INTERNAL"]["compare"].startswith("TYPED_KEY")


def test_hand_cells(built):
    c = {(x["trade"], x["unit"]): x for x in built["hand_readd_cells"]}
    m3 = c[("B7 Stairs", "m3")]
    assert sum(Decimal(str(r["measured_net"])) for r in m3["lines"] if r["state"] == "RELEASED") == Decimal("5.368881")
    m2 = c[("B9 Masonry", "m2")]
    assert sum(Decimal(str(r["measured_net"])) for r in m2["lines"] if r["state"] == "RELEASED") == Decimal("467.7925")
    assert all(r["state"] in ("RELEASED", "BLANK") for r in m2["lines"])


def test_missing_families(built):
    m = built["missing_families"]
    assert m["families"] == 104 and m["no_line"] == 39
    assert {r["family"] for r in m["t692_rows_now_with_lines"]} == {"B7-01"}


def test_pins_refuse_a_changed_input(monkeypatch):
    monkeypatch.setitem(A.PIN, "t722", (A.PIN["t722"][0], "0" * 64))
    with pytest.raises(R.AggregationError):
        A.load("t722")
