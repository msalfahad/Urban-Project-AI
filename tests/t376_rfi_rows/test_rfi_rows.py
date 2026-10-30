"""T-376 DESIGNER_RFI_ROWS_V1: citations resolve against the merged T-366 / T-371 ledgers (an uncited row refused),
one fact once, every open gap mapped, HELD never 0, the V3.0.27 projection agrees with the committed T-373 binding,
and a synthetic (non-Alsenan) villa by hand. Read-only; nothing is written outside a temporary folder."""

import copy
import csv
import json
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t376"))
import t376_rfi_rows as T  # noqa: E402

OUT = ROOT / "research" / "agents_t376"


@pytest.fixture(scope="module")
def led():
    return T._ledgers()


@pytest.fixture(scope="module")
def register(led):
    return set(led["t371"]["register"]["rfi_register"])


@pytest.fixture(scope="module")
def built():
    return T.build()


def test_every_citation_resolves_and_every_row_cites_a_merged_ledger(led, register):
    assert T.check_rows(T.ROWS, led, register)
    for r in T.ROWS:
        assert T.ledger_cites(r), r["row"]
        for c in r["cites"]:
            assert T.resolve_cite(c, led)
    for n in T.NOT_ASKED:
        assert T.resolve_cite(n["cite"], led)


def test_adverse_uncited_row_refused(led, register):
    rows = copy.deepcopy(T.ROWS)
    rows[3]["cites"] = [{"doc": "research/agents_t273/T-273_LAPS_AND_TONNES.md", "quote": "278.836"}]
    with pytest.raises(T.RowError, match="uncited row refused"):
        T.check_rows(rows, led, register)


@pytest.mark.parametrize("bad", [
    {"t366_checked": "P10", "handle": "FFFF"},            # a handle the T-366 sheet record does not carry
    {"t371": "STARTER", "attr": "leg_length", "quote": "Min. 40cm"},   # a quote the ledger does not print
    {"t371": "STARTER", "attr": "leg_length", "state": "PRINTED"},     # a state the census did not give
    {"t371": "NO-SUCH-POP", "attr": "body"},
    {"t366": "COL-MAIN", "field": "no_such_field"},
    {"t371_gap": "G-T371-9"},
])
def test_adverse_citation_not_in_the_ledger_refused(led, register, bad):
    rows = copy.deepcopy(T.ROWS)
    rows[0]["cites"].append(bad)
    with pytest.raises(T.RowError):
        T.check_rows(rows, led, register)


def test_adverse_one_fact_twice_unknown_target_and_id_collision(led, register):
    rows = copy.deepcopy(T.ROWS)
    rows[1]["fact"] = rows[0]["fact"]
    with pytest.raises(T.RowError, match="asked twice"):
        T.check_rows(rows, led, register)
    rows = copy.deepcopy(T.ROWS)
    rows[0]["target"] = "RFI-B-S99"
    with pytest.raises(T.RowError, match="in no RFI file"):
        T.check_rows(rows, led, register)
    rows = copy.deepcopy(T.ROWS)
    rows[2]["new_id"] = "RFI-B-S21"
    with pytest.raises(T.RowError, match="already exists"):
        T.check_rows(rows, led, register)


def test_adverse_held_as_zero_or_unsourced_range_refused(led, register):
    rows = copy.deepcopy(T.ROWS)
    r06 = next(r for r in rows if r["row"] == "R06")
    r06["kg"]["low"] = "0"
    with pytest.raises(T.RowError, match="never 0"):
        T.check_rows(rows, led, register)
    rows = copy.deepcopy(T.ROWS)
    r06 = next(r for r in rows if r["row"] == "R06")
    r06["kg"]["cite"] = []
    with pytest.raises(T.RowError, match="without its ledger citation"):
        T.check_rows(rows, led, register)


def test_every_open_gap_has_a_row():
    assert T.check_gap_coverage(T.ROWS)
    with pytest.raises(T.RowError, match="G-T371-1"):
        T.check_gap_coverage([r for r in T.ROWS if r["gap"] != "G-T371-1"])


def test_v3027_projection_agrees_with_the_t373_binding(built):
    rows, lines, summary = built
    assert summary["rebar_lines_v3027"] == 2643          # T-373: 2,643 reinforcement lines in V3.0.27
    t373 = {r["line_id"]: r for r in csv.DictReader((ROOT / "research/agents_t373/T373_LAP_BINDING.csv")
                                                    .open(encoding="utf-8"))}
    dg = [x for x in lines if x["dgp_record"]]
    seen = {}
    for x in dg:
        r = t373[x["line_id"]]
        assert Decimal(x["kg_low"]) == Decimal(r["kg_low_now"]) and Decimal(x["kg_high"]) == Decimal(r["kg_high_now"])
        seen[x["line_id"]] = x["dgp_record"]
    by = {o["row"]: o for o in rows}
    assert by["R07"]["kg_low_now"] == "517.818000" and by["R07"]["kg_high_now"] == "906.178000"   # 56 + 2 lines
    assert by["R08"]["kg_low_now"] == "239.868000" and by["R08"]["kg_high_now"] == "419.769000"   # 29 CB bottom ends
    assert by["R07"]["dgp_lines"] == 58 and by["R08"]["dgp_lines"] == 29


def test_committed_outputs_reproduce(built, tmp_path):
    rows, lines, summary = built
    T.write(tmp_path, rows, lines, summary)
    for f in ("T376_RFI_ROWS.csv", "T376_LINE_UNLOCK.csv", "T376_SUMMARY.json"):
        assert (tmp_path / f).read_bytes() == (OUT / f).read_bytes(), f


def test_committed_rows_held_blank_never_zero():
    for r in csv.DictReader((OUT / "T376_RFI_ROWS.csv").open(encoding="utf-8")):
        for k in ("kg_low_now", "kg_high_now", "kg_low_governed", "kg_high_governed"):
            assert r[k] == "" or Decimal(r[k]) > 0, (r["row"], k)
        if r["governed_basis"].startswith("HELD"):
            assert r["kg_low_governed"] == r["kg_high_governed"] == ""
        if int(r["valued"]) == 0:
            assert r["kg_low_now"] == ""
    for x in csv.DictReader((OUT / "T376_LINE_UNLOCK.csv").open(encoding="utf-8")):
        assert x["kg_low"] == "" or Decimal(x["kg_low"]) >= 0
        assert (x["kg_low"] == "") == (x["kg_high"] == "")


# ------------------------------------------------------------------ synthetic villa (not Alsenan), by hand
def _syn():
    lines = [
        {"line_id": "S-1", "element_id": "X:LINK:C1", "evidence_state": "BOUNDED_EXPOSURE", "measured_net": None,
         "bounded_range": {"low": 4.0, "high": 5.5}},
        {"line_id": "S-2", "element_id": "X:LINK:C2", "evidence_state": "SOURCE_DERIVED", "measured_net": 3.25,
         "bounded_range": None},
        {"line_id": "S-3", "element_id": "X:LINK:C3", "evidence_state": "BLOCKED_RFI", "measured_net": None,
         "bounded_range": None},
        {"line_id": "S-4", "element_id": "X:LAP:C1", "evidence_state": "BOUNDED_EXPOSURE", "measured_net": None,
         "bounded_range": {"low": 2.0, "high": 3.5}},
        {"line_id": "S-5", "element_id": "X:SLAB:P1", "evidence_state": "BOUNDED_EXPOSURE", "measured_net": None,
         "bounded_range": {"low": 1.0, "high": 2.0}},
    ]
    bind = {"S-1": "COL-LINKS", "S-2": "COL-LINKS", "S-3": "COL-LINKS", "S-4": "COL-STOREY-LAP", "S-5": "SLAB-TOP"}
    return lines, bind


def test_synthetic_villa_by_hand():
    lines, bind = _syn()
    view = T.v3027_view(lines, None)
    row = {"row": "X1", "pops": ["COL-LINKS"]}
    u = T.unlock(row, view, bind, [], {})
    # hand: valued S-1 (4.0 .. 5.5) + S-2 (3.25) = 7.25 .. 8.75 kg; S-3 BLANK, counted, never 0
    assert (u["n_lines"], u["n_valued"], u["n_blank"]) == (3, 2, 1)
    assert u["kg_low"] == Decimal("7.250000") and u["kg_high"] == Decimal("8.750000")
    u2 = T.unlock({"row": "X2", "pops": ["COL-STOREY-LAP"]}, view, bind, [], {"S-4": "DG-x"})
    assert (u2["n_dgp"], u2["dgp_low"], u2["dgp_high"]) == (1, Decimal("2.000000"), Decimal("3.500000"))
    lo, hi, basis = T.governed({"kg": {"kind": "LINES"}}, u2)
    assert (lo, hi) == (Decimal("2.000000"), Decimal("3.500000")) and "DG-x" in basis
    lo, hi, basis = T.governed({"kg": {"kind": "UNQUANTIFIED", "why": "leg undimensioned"}}, u)
    assert lo is None and hi is None and basis.startswith("HELD")
    # a population with only blank lines has no figure (BLANK, not 0)
    u3 = T.unlock(row, [v for v in view if v["line_id"] == "S-3"], bind, [], {})
    assert u3["kg_low"] is None and T.governed({"kg": {"kind": "LINES"}}, u3)[0] is None


def test_synthetic_adverse():
    lines, bind = _syn()
    view = T.v3027_view(lines, None)
    with pytest.raises(T.RowError, match="no line holds"):
        T.unlock({"row": "X3", "pops": ["SLAB-TOP"], "held_item": "HOOK_DOWN_LEG"}, view, bind, [], {})
    bad = [dict(v) for v in view]
    bad[2]["high"] = Decimal("1")            # a blank line carrying a figure
    with pytest.raises(T.RowError, match="blank low with a high"):
        T.unlock({"row": "X4", "pops": ["COL-LINKS"]}, bad, bind, [], {})
    with pytest.raises(T.RowError, match="no record"):
        T.dgp_of([{"line_id": "S-9", "proposed": "HELD", "report_group": "unknown group"}])
    # a stale T-318 'before' stops the projection
    doc = {"lines": [{"line_id": "S-5", "action": "RESTATE", "before": {"low": 1.0, "high": 2.5}}]}
    with pytest.raises(T.RowError, match="stale"):
        T.v3027_view(lines, doc)
    doc = {"lines": [{"line_id": "S-5", "action": "PARENT", "before": {"low": 1.0, "high": 2.0},
                      "part": {"low": 0.4, "high": 0.6}, "held_items": "HOOK_DOWN_LEG at 1..1 ends"}]}
    v = T.v3027_view(lines, doc)
    p = [x for x in v if x["parent"] == "S-5"]
    assert len(v) == 6 and p[0]["element_id"] == "X:SLAB:P1#SLAB_BAR_ENDS:VALUED"
    assert next(x for x in v if x["line_id"] == "S-5")["low"] is None      # parent BLANK, part valued
    u = T.unlock({"row": "X5", "pops": ["SLAB-TOP"], "held_item": "HOOK_DOWN_LEG"}, v, bind, [], {})
    assert (u["n_lines"], u["kg_low"], u["kg_high"]) == (2, Decimal("0.400000"), Decimal("0.600000"))
