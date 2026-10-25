"""T-297 Alsenan rebar line-to-member basis ledger, rebuilt from committed inputs only (own ARCH_TAKEOFF_V3.0.16 run on
the Drive copies, extracted by research/agents_t297/t297_extract.py; merged hand ledgers T-148 / T-138 / T-149 / T-152,
T-280 core datums). Re-builds without writing and compares with the committed outputs; checks the ledger invariants
(development villa; not an accuracy claim)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t297"
sys.path.insert(0, str(HERE))
import pytest  # noqa: E402

import t297_ledger as L  # noqa: E402


@pytest.fixture(scope="module")
def built():
    import t297_alsenan as A
    cand, rows, summary, join_rows = A.build()
    return A, cand, rows, summary, join_rows


def test_rebuild_equals_committed_outputs(built):
    A, CAND, ROWS, SUMMARY, JOIN = built
    assert A.csv_text(ROWS) == (HERE / "LINE_BASIS_T297.csv").read_text(encoding="utf-8")
    assert json.loads((HERE / "LINE_BASIS_SUMMARY_T297.json").read_text(encoding="utf-8")) == SUMMARY


def test_every_reinforcement_line_of_the_candidate_once(built):
    A, CAND, ROWS, SUMMARY, JOIN = built
    ids = [r.line_id for r in ROWS]
    assert len(ids) == len(set(ids)) == CAND["rebar_lines"] == len(CAND["lines"])
    assert SUMMARY["candidate"]["candidate_lines_csv_sha256"] == CAND["candidate_lines_csv_sha256"]


def test_no_bound_or_held_carries_a_quantity_and_every_bound_has_a_datum(built):
    A, CAND, ROWS, SUMMARY, JOIN = built
    for r in ROWS:
        L.check_row(r)
        if r.status == "BOUND":
            assert r.quantity_kg is None and r.datum and r.datum_status
        if r.status in L.NO_QUANTITY:
            assert r.quantity_kg is None and r.bound_low_kg is None


def test_residuals_against_the_candidate_and_the_source_ledgers_are_zero(built):
    A, CAND, ROWS, SUMMARY, JOIN = built
    for k, v in SUMMARY["residuals_vs_candidate_kg"].items():
        assert abs(v) <= 5e-6, k
    for k, v in SUMMARY["residuals_vs_sources_kg"].items():
        assert abs(v["residual_kg"]) <= v["tolerance_kg"], k


def test_line_state_and_basis_agree(built):
    A, CAND, ROWS, SUMMARY, JOIN = built
    for r in ROWS:
        if r.line_state == "NOT_APPLICABLE_WITH_EVIDENCE":
            assert r.status == "NOT_APPLICABLE"
        if r.line_state in ("BLOCKED_RFI", "EXCLUDED_WITH_REASON"):
            assert r.status in ("HELD", "BOUND")
        if r.status in ("DRAWING_CONFIRMED", "VERIFIED", "CONVENTION", "ASSUMED_OWNER_APPROVED"):
            assert r.line_state in ("SOURCE_DERIVED", "MEASURED", "PROVISIONAL")
            assert abs(r.quantity_kg - r.line_kg) <= 5e-7


def test_alsenan_pins(built):
    """engineering results of the candidate of record (csv a4dc01dd), per family and basis status"""
    A, CAND, ROWS, SUMMARY, JOIN = built
    t = SUMMARY["totals_by_family_status"]
    assert CAND["candidate_lines_csv_sha256"].startswith("a4dc01dd") and len(ROWS) == 2505
    # r2 (LB-10, F-T297-04): 4 2F main-bar lines 159.288 kg leave DRAWING_CONFIRMED (1.887128 - 0.159288 t)
    assert t["COLUMNS|DRAWING_CONFIRMED"] == {"lines": 28, "kg": 1727.84, "t": 1.72784}
    assert t["BEAMS|DRAWING_CONFIRMED"]["kg"] == 5171.031
    assert t["GROUND_BEAMS|DRAWING_CONFIRMED"]["kg"] == 1252.907
    assert t["FOOTINGS|CONVENTION"]["kg"] == 874.862227 and "FOOTINGS|DRAWING_CONFIRMED" not in t
    assert t["GROUND_SLAB|CONVENTION"]["kg"] == 1064.239762
    assert t["BEAMS|BOUND"]["high_kg"] is None and t["BEAMS|BOUND"]["high_open_lines"] == 51
    assert not any(k.endswith(("|VERIFIED", "|ASSUMED_OWNER_APPROVED")) for k in t)
    f = SUMMARY["coverage_findings"][0]["foundation_column_lines_by_bar_group"]
    assert f == {"MAIN": {"BLOCKED_RFI -> HELD": 28}, "TIES": {"BLOCKED_RFI -> HELD": 28}}
    by = {r.line_id: r for r in ROWS}
    dc = sum(t[f"{f}|DRAWING_CONFIRMED"]["kg"] for f in ("COLUMNS", "BEAMS", "GROUND_BEAMS"))
    assert round(dc / 1000, 6) == 8.151778          # was 8.311066 t in r1
    lap = [r for r in ROWS if r.family == "COLUMNS" and r.bar_group.startswith("LAP")]
    assert len(lap) == 56 and all(r.status == "BOUND" and r.lap_basis == "NOTE_READING" for r in lap)
    assert by["L-03062228b230a7fff3bd"].quantity_kg == 53.096     # COL-1F-35 C2: 8 x 4.20 x 256 / 162
    assert round(by["L-00fbbdf4ad454311231c"].quantity_kg, 6) == 40.177778 and \
        by["L-00fbbdf4ad454311231c"].status == "CONVENTION"      # F5 bottom long: 20 x 2.26 x 0.888889


def test_the_ledger_holds_for_the_v3017_candidate_too():
    """T-254 (V3.0.17, csv 429008af) merged during this task: its 2,505 reinforcement lines equal V3.0.16's line by
    line (ids, states, quantities, ranges, locations), so every row of this ledger applies to V3.0.17 unchanged"""
    eq = json.loads((HERE / "REBAR_EQUIVALENCE_T297.json").read_text(encoding="utf-8"))
    assert eq["later_csv_sha256"].startswith("429008af") and eq["later_json_sha256"].startswith("366be2f8")
    assert eq["same_line_ids"] and eq["differing"] == [] and eq["rebar_lines_later"] == eq["rebar_lines_base"] == 2505


F04 = {"L-5fca13cebe2e259988bc": "COL-2F-50", "L-4247172eb6f60bb0b98b": "COL-2F-51",
       "L-930151c44e50a06944a6": "COL-2F-53", "L-57836098c8dc67817e1d": "COL-2F-54"}


def test_r2_the_four_2f_main_bar_lines_are_held_on_the_d39_datum(built):
    """Checker F-T297-04: 4 x 6 x 4.20 x 256 / 162 = 4 x 39.822 = 159.288 kg; the bars' interval 4.20 is the 2F storey
    interval to the roof slab top, the D-39 datum V3.0.17 holds for the same members' concrete"""
    A, CAND, ROWS, SUMMARY, JOIN = built
    by = {r.line_id: r for r in ROWS}
    for lid, mem in F04.items():
        r = by[lid]
        assert r.members == (mem,) and r.status == "HELD" and r.quantity_kg is None
        assert r.line_state == "SOURCE_DERIVED" and r.line_kg == 39.822 and "BAR_LENGTH_ON_HELD_DATUM" in r.flags
        assert r.length_datum_status == "HELD" and "D-39_ROOF_DATUM" in r.length_datum
    j = SUMMARY["datum_join"]["F-T297-04 candidate releases, ledger holds (bar length on a held datum)"]
    assert sorted(j["lines"]) == sorted(F04) and j["candidate_kg"] == 159.288 and j["candidate_t"] == 0.159288


def test_r2_join_of_the_13_held_members_and_the_5_absent_stacks(built):
    """the T-148 member <-> V3.0.17 concrete line join: 8 2F + 5 annex on D-39 / Q-54 B, CB5 2 re-based, planted 2F,
    5 NOT_PRESENT (no member; their 10 route bar lines NOT_APPLICABLE)"""
    A, CAND, ROWS, SUMMARY, JOIN = built
    jr = JOIN
    held = {r["member"]: r for r in jr if r["length_datum_status"] == "HELD" and r["group"] in ("COL_2F", "COL_ANNEX_7")}
    assert sorted(held) == ["COL-2F-49", "COL-2F-50", "COL-2F-51", "COL-2F-52", "COL-2F-53", "COL-2F-54", "COL-2F-55",
                            "COL-2F-56", "COL-GF-15", "COL-GF-16", "COL-GF-18", "COL-GF-28", "COL-GF-29"]
    assert all("D-39_ROOF_DATUM" in r["length_datum"] for r in held.values())
    assert sorted(r["member"] for r in jr if r["length_datum_status"] == "SUPERSEDED") == ["COL-GF-20", "COL-GF-21"]
    assert [r["member"] for r in jr if r["length_datum_status"] == "NOT_PRESENT"] == [None] * 5
    assert all(r["storey_shift_m"] == 38.724 for r in jr)
    rows_on = [r for r in ROWS if r.members[0] in held and J_length(r)]
    assert all(r.status in ("HELD", "BOUND") for r in rows_on)
    assert not any(r.status in ("DRAWING_CONFIRMED", "VERIFIED", "CONVENTION") and r.length_datum_status
                   for r in ROWS)
    absent = [r for r in ROWS if r.length_datum_status == "NOT_PRESENT"]
    assert len(absent) == 10 and all(r.status == "NOT_APPLICABLE" for r in absent)
    sup = SUMMARY["datum_join"]["F-T297-05 bound on a superseded concrete height -> HELD"]
    assert sup["members"] == ["COL-GF-20", "COL-GF-21"] and sup["bound_low_kg_withdrawn"] == 28.485


def J_length(r):
    import t297_datum_join as J
    return J.length_on_height(r.bar_group)


def test_r2_join_file_is_committed(built):
    A, CAND, ROWS, SUMMARY, JOIN = built
    assert A.join_text(JOIN) == (HERE / "DATUM_JOIN_T297.json").read_text(encoding="utf-8")
    assert A.consumer_text(CAND, ROWS) == (HERE / "LINE_BASIS_CONSUMER_T297.json").read_text(encoding="utf-8")
