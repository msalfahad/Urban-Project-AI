"""T-703: the V3.0.72 inputs built from the merged T-696 / T-713 ledgers (development-villa regression, merged files only;
no drawing). Hand figures any reviewer can redo: 2F part hosts W08 9.47 x 12.5 = 118.375 pcs, x 0.0110625 =
0.104761875 -> UP 0.104762 m3; W05 3.85 x 0.01475 = 0.0567875 -> 0.056788; W01 + W06 21.945 x 0.01475 = 0.32368875 ->
0.323689; W03 25.895 x 3.5 = 90.6325 kg; MAIN_S 11.389 x 0.0110625 = 0.1259908125 -> DOWN 0.125990 (CONDITIONAL leaf);
2F 0.15 parent 0.425 + 0.77 + 0.77 = 1.965 m2 AT_MOST; GF 0.15 parent AT_LEAST 12.9311 m2 (GF-W22 low end) ->
161.63875 pcs, 0.14305029375 -> DOWN 0.143050 m3."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "research" / "agents_t703"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import t703_inputs as T  # noqa: E402
from engine.source import arch_v3072 as A  # noqa: E402

INDEX = ROOT / "research/agents_t704/out/LINE_INDEX_V3_0_71.json"


def test_counts_and_hand_figures():
    v = A.load_inputs(T.build())
    os_ = {e["line_id"]: e for e in v["_one_sided"]}
    assert len(os_) == 18 and len(v["_rounding"]) == 15
    assert sum(1 for e in v["_rounding"] if e["_moves"]) == 10
    want = {"L-c76dd0d11a5776939008": ("AT_MOST", 118.375), "L-b765c24ac4b275c661bc": ("AT_MOST", 0.104762),
            "L-3cdc29f2fadd13ef35d4": ("AT_MOST", 0.056788), "L-539af3a600dcf190cd01": ("AT_MOST", 0.323689),
            "L-bd48d897f8f11b6377ef": ("AT_MOST", 90.6325), "L-cf220ce7edefedd935b4": ("AT_LEAST", 0.12599),
            "L-bd21b0ea1ce4e1c8dabd": ("AT_LEAST", 142.3625), "L-246f3c09de4c6b90efe5": ("AT_MOST", 1.965),
            "L-318e6311ab5e01c0fa3e": ("AT_MOST", 24.5625), "L-cdb8d54311c5c841528f": ("AT_MOST", 0.021738),
            "L-d6373b9f427e4b599a5d": ("AT_MOST", 6.8775), "L-0d9b9e89bb6455da475d": ("AT_LEAST", 12.9311),
            "L-dc7b4e20a2f54668b179": ("AT_LEAST", 161.63875), "L-39a62186ff15c48d51d5": ("AT_LEAST", 0.14305)}
    for lid, (kind, val) in want.items():
        assert (os_[lid]["kind"], os_[lid]["_value"]) == (kind, val), lid
    br = {e["line_id"]: (e["_lo"], e["_hi"]) for e in v["_rounding"]}
    assert br["L-686a15f1996005bed645"] == (0.0, 0.001112)
    assert br["L-c596929191d328f3878c"] == (0.028342, 0.049797)
    assert br["L-866a6602ffa70d03f210"] == (0.618315, 0.622077)


def test_bindings_on_the_candidate_of_record_index():
    ix = {ln["line_id"]: ln for ln in json.loads(INDEX.read_text(encoding="utf-8"))["lines"]}
    d = T.build()
    for e in d["one_sided"]:
        ln = ix[e["line_id"]]
        assert ln["class"] == "HELD" and ln["held_low"] is None and ln["item_code"] == e["item_code"]
        assert ix[e["host_line_id"]]["item_code"] == "MAS.BLOCK"
        want = e["host"] if e["item_code"] == "MAS.BLOCK" else f"MATERIAL:{e['host']}"
        assert ln["element_id"] == want
    for e in d["rounding"]:
        ln = ix[e["line_id"]]
        assert (ln["held_low"], ln["held_high"]) == tuple(e["was"])


def test_no_figure_for_white_units_or_perimeter():
    d = T.build()
    assert not [e for e in d["one_sided"] if e["item_code"] in ("MAS.UNITS.WHITE", "MAS.MORTAR.BLACK.PERIMETER")]


def test_tampered_ledger_refused(monkeypatch):
    monkeypatch.setitem(T.PINS, T.REST, "00000000")
    with pytest.raises(SystemExit, match="tampered"):
        T.build()
