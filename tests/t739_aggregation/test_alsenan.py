"""T-739 on the development villa: the committed statement equals a rebuild from sha-pinned merged files, the keyed
freelancer ranges reproduce the SCOREBOARD v2 cells (V3.0.73) on every key V3.0.74 left unchanged, every HELD line
carries a cause and no HELD line is summed. r2: restated on V3.0.74 only; cause sources sha-pinned (a later merge of
another task's output cannot change the statement). Repository files only (no drawing, no Drive)."""
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
    assert built["line_count"] == 5155
    # V3.0.73 BLANK 1602 / BOUNDED 1163 + the T-717 ADD rows (3 BLANK, 29 BOUNDED); released / excluded unchanged
    assert built["state_count"] == {"BLANK": 1605, "BOUNDED": 1192, "EXCLUDED": 843, "RELEASED": 1515}
    assert sum(sum(t["counts"].values()) for t in built["trades"]) == 5155
    assert built["candidate"].startswith("ARCH_TAKEOFF_V3.0.74 (NOT RELEASED), lines sha bea5be02")


def test_held_never_summed_into_a_total(built):
    for t in built["trades"]:
        held = sum(t["counts"][s] for s in R.HELD_STATES)
        assert (t["total"] is None) == (held > 0), t


def test_every_held_line_has_a_cause(built):
    h = built["held"]
    assert h["lines"] == 2797 and h["findings_F_T739_1"] == 0
    assert h["cause_source_counts"]["T-717"] == 32   # the 32 lines added in V3.0.74, bound to their T-709 records
    assert all(r["cause"] and r["cause_class_t716"] for r in h["rows"])
    assert all(not r["cause_source"].startswith("T-662") for r in h["rows"])


def test_chain_readd(built):
    ch = built["chain_readd_v3_0_73_to_v3_0_74"]
    assert ch == {"package_rows": 36, "rows_checked_before_after": 36, "lines_changed_or_added": 36,
                  "replaced": 4, "added": 32, "other_lines_byte_equal": 5119}


def test_fin_census_equals_t717(built):
    """FIN.PLASTER / FIN.PAINT m2 re-added here equal the T-717 census after (its own figures), exactly."""
    t717 = A.load("t717")["identity"]["fin_census_after"]
    c = {x["item_code"]: x for x in built["item_codes"] if x["unit"] == "m2"}
    for code in ("FIN.PLASTER", "FIN.PAINT"):
        t = t717[code]
        assert c[code]["counts"]["RELEASED"] == t["released"] and c[code]["counts"]["BLANK"] == t["blank"]
        assert c[code]["counts"]["BOUNDED"] == t["bounded"] and c[code]["counts"]["EXCLUDED"] == t["excluded"]
        assert Decimal(c[code]["released"]) == Decimal(str(t["released_m2"]))
        assert Decimal(c[code]["bounded_low"]) == Decimal(str(t["low"]))
        assert Decimal(c[code]["bounded_high"]) == Decimal(str(t["high"]))


SCOREBOARD_V2 = {   # cells of SCOREBOARD v2 (board, Verifier, restated on V3.0.73 2026-11-12 03:44 .. 09:59 UTC); T-717 moved
    # FIN.PLASTER / FIN.PAINT only, so every other key's cell must reproduce unchanged on V3.0.74
    "CONC.BLINDING": "at least -56.70 %, upper end open", "CONC.FOOTING": "-2.69 .. +5.18 %",
    "CONC.GROUND": "at least -37.97 %, upper end open", "CONC.COLUMN": "at least +1.50 %, upper end open",
    "CONC.BEAM": "at least +10.52 %, upper end open", "CONC.SLAB": "+0.77 %",
    "CONC.STAIR_DOME": "at least -52.14 %, upper end open", "CONC.POOL": "at least -41.67 %, upper end open",
    "DOORS.ALUMINIUM": "+6.33 %",
    "WINDOWS.ALUMINIUM": "at least -26.33 %, upper end open"}


def test_keyed_reproduces_scoreboard(built):
    k = {r["key"]: r for r in built["freelancer_keyed"]}
    for key, cell in SCOREBOARD_V2.items():
        assert k[key]["compare"] == cell, key
    # V3.0.74: plaster quoted from T-717 (row apart / gross); paint key opened by the 3 BLANK return-paint lines
    assert "-16.76 .. -8.68 % with his 13.50 m2" in k["PLASTER.INTERNAL"]["compare"]
    assert "-17.72 .. -9.74 %" in k["PLASTER.INTERNAL"]["compare"] and "%" not in k["PLASTER.INTERNAL"]["released"]
    assert k["PAINT.INTERNAL_WALL"]["compare"] == "at least -30.97 %, upper end open"
    assert k["PAINT.INTERNAL_WALL"]["blank_n"] == 3
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
    assert m["families"] == 104 and m["no_line"] == 39 and m["master"] == "1.75.0"
    assert {r["family"] for r in m["t692_rows_now_with_lines"]} == {"B7-01"}


def test_pins_refuse_a_changed_input(monkeypatch):
    monkeypatch.setitem(A.PIN, "t722", (A.PIN["t722"][0], "0" * 64))
    with pytest.raises(R.AggregationError):
        A.load("t722")


def test_cause_pin_refuses_a_changed_source(monkeypatch, tmp_path):
    pin = json.loads(A.CAUSE_PIN.read_text(encoding="utf-8"))
    for rel in pin["files"]:          # every pinned file, the T-654 base register included
        pin["files"][rel] = "0" * 64
    p = tmp_path / "pin.json"
    p.write_text(json.dumps(pin), encoding="utf-8")
    monkeypatch.setattr(A, "CAUSE_PIN", p)
    with pytest.raises(R.AggregationError):
        A.cause_records(set())


def test_cause_pin_is_for_this_candidate(monkeypatch, tmp_path):
    pin = json.loads(A.CAUSE_PIN.read_text(encoding="utf-8"))
    pin["candidate"] = "ARCH_TAKEOFF_V3.0.73"
    p = tmp_path / "pin.json"
    p.write_text(json.dumps(pin), encoding="utf-8")
    monkeypatch.setattr(A, "CAUSE_PIN", p)
    with pytest.raises(R.AggregationError):
        A.load_cause_pin()


# synthetic package (not the development villa): normal and adverse cases of the chain and the package-cause binding
def _ln(lid, low=None, high=None, net=None, cls="HELD", code="FIN.PAINT"):
    return {"line_id": lid, "held_low": low, "held_high": high, "measured_net": net, "class": cls,
            "item_code": code, "unit": "m2"}


def _row(lid, change, after, before=None, piece="RETURN_PAINT", flag=None, eid="E1"):
    return {"line_id": lid, "change": change, "piece": piece, "flag": flag, "element_id": eid, "item_code": "FIN.PAINT",
            "unit": "m2", "map_row": "T-9:x", "class": [None if change == "ADD" else "HELD", "HELD"],
            "before_base": before or {"low": None, "high": None, "value": None},
            "after_v3_0_74": dict(after, state="BOUNDED_EXPOSURE")}


SYN_A = "L-aaaaaaaaaaaaaaaaaaaa"
SYN_B = "L-bbbbbbbbbbbbbbbbbbbb"
SYN_C = "L-cccccccccccccccccccc"


def test_synthetic_chain_normal_and_adverse():
    base = {"lines": [_ln(SYN_A, 1.0, 2.0), _ln(SYN_B, None, None, 5.0, "RELEASED")]}
    new = {"lines": [_ln(SYN_A, 0.5, 2.0), _ln(SYN_B, None, None, 5.0, "RELEASED"), _ln(SYN_C, 0.0, 0.7)]}
    pk = {"rows": [_row(SYN_A, "CHANGE", {"low": 0.5, "high": 2.0, "value": None},
                        {"low": 1.0, "high": 2.0, "value": None}),
                   _row(SYN_C, "ADD", {"low": 0.0, "high": 0.7, "value": None})]}
    ch = A.chain_readd(base, new, pk)
    assert ch["replaced"] == 1 and ch["added"] == 1 and ch["other_lines_byte_equal"] == 1
    moved = {"lines": [_ln(SYN_A, 0.5, 2.0), _ln(SYN_B, None, None, 5.1, "RELEASED"), _ln(SYN_C, 0.0, 0.7)]}
    with pytest.raises(R.AggregationError):      # a released line moved with no package row
        A.chain_readd(base, moved, pk)
    wrong = {"lines": [_ln(SYN_A, 0.5, 2.0), _ln(SYN_B, None, None, 5.0, "RELEASED"), _ln(SYN_C, 0.0, 0.8)]}
    with pytest.raises(R.AggregationError):      # added line differs from its package record
        A.chain_readd(base, wrong, pk)


def test_synthetic_package_causes_normal_and_adverse():
    t709 = {"c_return_paint": {"rule": "R-X", "rows": [{"paint_row": {"element_id": "E1", "flag": "depth not printed",
                                                                         "bound_beside_m2": ["0", "0.7"]}}]},
            "a_double_height": {"rule": "R-Y", "paint_band": {"status": "BOUNDED: x"}}}
    pk = {"rows": [_row(SYN_C, "ADD", {"low": 0.0, "high": 0.7, "value": None}),            # bound by element id
                   _row(SYN_B, "ADD", {"low": 0.0, "high": 0.7, "value": None}, eid="E9"),  # no record: no cause
                   _row(SYN_A, "CHANGE", {"low": 0.5, "high": 2.0, "value": None})]}        # not new: never re-caused
    out = {r[2]: r[3] for r in A.package_causes(pk, t709)}
    assert set(out) == {SYN_C} and "depth not printed" in out[SYN_C]
    causes, findings = R.resolve_causes([SYN_B, SYN_C], A.package_causes(pk, t709), {})
    assert findings == [SYN_B] and SYN_C in causes        # a HELD line with no bound record stays a finding, never 0
