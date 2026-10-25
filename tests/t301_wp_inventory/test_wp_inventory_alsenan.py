"""T-301 on the development villa (committed ledgers + the committed V3.0.17 waterproofing-line extract; no private
input): the WP.FOUNDATION inventory closes on the candidate of record ARCH_TAKEOFF_V3.0.17 (canonical lines 366be2f8,
own run on the Drive copies), and its whole / component reading agrees with the Verifier's V2 records."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research/agents_t301"))

import t301_alsenan as A  # noqa: E402
import t301_wp_inventory as W  # noqa: E402
from engine.source import trade_completeness_v1 as TC  # noqa: E402

# the Verifier's V2 records on V3.0.17 (docs/agents/verdicts/V3.0.17 on agents/control): line id -> scope
RECORDS = {"L-69e6e6d74707afe3ac5b": "COMPONENT", "L-e6280a91646613667b62": "COMPONENT",
           "L-4ec54f9922da7281573a": "COMPONENT", "L-d3ec19448415e0a0f083": "COMPONENT",
           "L-1f3aaafcc460173462d9": "COMPONENT", "L-e11f17bb076058bf172d": "WHOLE",
           "L-e4789d76efedbc351bd4": "WHOLE"}


def run():
    els = A.inventory()
    cand = json.loads(A.EXTRACT.read_text(encoding="utf-8"))["lines"]
    fl = [ln for ln in cand if ln["item_code"].startswith("WP.FOUNDATION.")]
    lk, unread, mk = A.links(fl, els)
    return els, fl, lk, unread, mk, W.join(els, fl, lk)


def test_every_foundation_wp_face_in_a_line_or_not_applicable():
    els, fl, lk, unread, mk, rep = run()
    assert len(fl) == 19 and unread == [] and mk == []
    assert rep["counts"] == {"IN_LINE": 320, "NOT_APPLICABLE": 96, "MISSING": 0}
    assert rep["register_only"] == [] and rep["unlinked_lines"] == []
    assert all(r["evidence"]["sheet"] and r["evidence"]["ref"] for r in rep["elements"] if r["status"] == "NOT_APPLICABLE")


def test_residual_zero_on_every_released_item():
    *_x, rep = run()
    got = {(f["item_code"], f["unit"]): (f["inventory_qty_in_line"], f["line_qty"], f["residual"]) for f in rep["families"]}
    assert got[("WP.FOUNDATION.FOOTING_MEMBRANE", "m2")] == (109.85, 109.85, 0.0)      # 24 T-233 outline areas
    assert got[("WP.FOUNDATION.FOOTING_SCREED", "m3")] == (5.4925, 5.4925, 0.0)
    assert got[("WP.FOUNDATION.LIFT_PIT_MEMBRANE", "m2")] == (47.43, 47.43, 0.0)        # 20.700 + 10.920 + 15.810
    assert got[("WP.FOUNDATION.LIFT_PIT_BOARD", "m2")] == (26.73, 26.73, 0.0)
    assert got[("WP.FOUNDATION.BURIED_LIQUID", "m2")] == (45.4682, 45.4682, 0.0)       # 32 T-276 faces
    assert got[("WP.FOUNDATION.FOOTING_SIDES", "m2")] == (None, None, None)             # all held: blank, never 0


def test_whole_or_component_agrees_with_the_verifier_records():
    els, fl, lk, unread, mk, rep = run()
    whole = {(f["item_code"], f["unit"]): f["whole_line_countable"] for f in rep["families"]}
    by_id = {ln["line_id"]: ln for ln in fl}
    for lid, scope in RECORDS.items():
        ln = by_id[lid]
        assert whole[(ln["item_code"], ln["unit"])] is (scope == "WHOLE"), lid


def test_presence_crosschecks_and_t236_schema():
    els, fl, lk, *_r = run()
    assert A.crosschecks() == {"necks": {"T-217 census DRAWN": 36, "T-263 ledger": 36, "agree": True},
                               "footings": {"T-233 outlines": 26, "T-219 outlines": 26, "agree": True}}
    inv, exc, ll = W.to_t236(els, lk, "T-301 WP.FOUNDATION inventory")
    canon = [{"line_id": x["line_id"], "item_code": x["item_code"], "unit": x["unit"], "trade": "WATERPROOFING",
              "evidence_state": x["evidence_state"], "measured_net": x["measured_net"],
              "rfi": {"question": "held"} if x["measured_net"] is None else None} for x in fl]
    rep = TC.check(inventories=inv, lines=canon, line_links=ll, exclusions=exc)
    row = next(r for r in rep["trades"] if r["trade"] == "WATERPROOFING")
    assert row["status"] == "COMPLETE_AGAINST_INVENTORY"
    assert (row["found"], row["measured"], row["held"], row["missing"], row["excluded"]) == (320, 111, 209, 0, 96)
    # measured 111 = 3 x 24 footing underlay rows + 3 pit membrane + 2 pit board + 2 pit screed + 32 buried faces


def test_committed_report_is_the_reproduced_one(tmp_path):
    A.main(["--out", str(tmp_path)])
    for f in ("WP_FOUNDATION_INVENTORY_T301.csv", "WP_FOUNDATION_REPORT_T301.json"):
        assert (tmp_path / f).read_bytes() == (A.HERE / f).read_bytes(), f
