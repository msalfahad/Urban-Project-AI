"""T-647: structural HELD lines to a named cause (R-T647-1). Synthetic villa "V647" (not the development villa): three
HELD lines, one per cause kind (owner decision, designer item, dependency), with adverse cases (a cause with no source,
HELD summed as 0, a released host, a HELD line carrying a quantity, a malformed reference, a fix row without its hand
calculation); then the development villa: the 183 B9 / B10 / B11 lines of finding F-T636-1 (repository files only)."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t647"))
import t647_rules as R  # noqa: E402
import t647_alsenan as A  # noqa: E402

S = [{"file": "villa-v647/ledger.md", "read_on": "row 7"}]


def v647():
    """villa V647: a 0.20 m parapet (owner answered: material by the designer), a beam whose section the designer
    has not printed, and the mortar of a HELD block wall."""
    return [
        {"line_id": "L-" + "1" * 20, "class": "HELD", "cause_class": "OWNER_DECISION", "ref": "Q-12 C",
         "cause": "parapet material left to the designer by the owner", "sources": S, "measured_net": None},
        {"line_id": "L-" + "2" * 20, "class": "HELD", "cause_class": "DESIGNER_ITEM", "ref": "D-07",
         "cause": "beam B4 section not printed", "sources": S, "measured_net": None},
        {"line_id": "L-" + "3" * 20, "class": "HELD", "cause_class": "DEPENDENCY", "ref": "L-" + "4" * 20,
         "cause": "mortar follows its HELD wall", "sources": S, "measured_net": None},
    ]


HELD_V647 = {"L-" + c * 20 for c in "1234"}


def test_v647_three_causes_accepted():
    for r in v647():
        assert R.check(r, HELD_V647) is r


def test_adverse_cause_without_source_refused():
    r = dict(v647()[1], sources=[])
    with pytest.raises(R.CauseError, match="invented"):
        R.check(r, HELD_V647)
    with pytest.raises(R.CauseError, match="invented"):
        R.check(dict(r, sources=[{"file": "x.md"}]), HELD_V647)


def test_adverse_held_summed_as_zero_refused():
    lines = [{"line_id": "L-a", "class": "RELEASED", "measured_net": 2.5},
             {"line_id": "L-b", "class": "HELD", "measured_net": None}]
    with pytest.raises(R.CauseError, match="never summed"):
        R.held_total(lines)
    assert R.held_total(lines[:1]) == 2.5


def test_adverse_held_with_a_quantity_refused():
    with pytest.raises(R.CauseError, match="HELD is blank"):
        R.check(dict(v647()[0], measured_net=0), HELD_V647)


def test_adverse_dependency_on_released_or_self_refused():
    r = v647()[2]
    with pytest.raises(R.CauseError, match="not HELD"):
        R.check(r, {"L-" + "3" * 20})
    with pytest.raises(R.CauseError, match="itself"):
        R.check(dict(r, ref=r["line_id"]), HELD_V647)


def test_adverse_reference_form_and_class():
    with pytest.raises(R.CauseError, match="not a OWNER_DECISION"):
        R.check(dict(v647()[0], ref="owner said so"), HELD_V647)
    with pytest.raises(R.CauseError, match="not one of"):
        R.check(dict(v647()[0], cause_class="CONVENTION"), HELD_V647)
    with pytest.raises(R.CauseError, match="not a PRINTED_VALUE_GAP"):
        R.check(dict(v647()[0], cause_class="PRINTED_VALUE_GAP", ref="somewhere"), HELD_V647)


def test_adverse_fix_row_needs_hand_calculation_and_is_never_wired():
    base = dict(v647()[0], cause_class="FIX_ROW", ref="FR-T647-9")
    with pytest.raises(R.CauseError, match="hand calculation"):
        R.check(dict(base, fix_row={"proposed_state": "NOT_APPLICABLE_WITH_EVIDENCE"}), HELD_V647)
    with pytest.raises(R.CauseError, match="never wired"):
        R.check(dict(base, fix_row={"proposed_state": "X", "hand_calculation": "1 x 2", "wired": True}), HELD_V647)


# ---- development villa ------------------------------------------------------------------------------------------------
@pytest.fixture(scope="module")
def census():
    return A.build()


def test_every_structural_line_has_one_cause(census):
    assert census["lines"] == 183 == census["with_cause"]
    groups = {}
    for r in census["records"]:
        groups[r["group"]] = groups.get(r["group"], 0) + 1
        assert r["cause"] and r["sources"]
    assert groups == {"B11": 138, "B9": 32, "B10": 13}
    assert len({r["line_id"] for r in census["records"]}) == 183


def test_class_split(census):
    assert census["by_group_and_class"] == {
        "B10 DESIGNER_ITEM": 4, "B10 FIX_ROW": 5, "B10 OWNER_DECISION": 4,
        "B11 DESIGNER_ITEM": 79, "B11 FIX_ROW": 17, "B11 PRINTED_VALUE_GAP": 42,
        "B9 DEPENDENCY": 19, "B9 DESIGNER_ITEM": 7, "B9 PRINTED_VALUE_GAP": 6}


def test_held_census_unchanged_and_never_zero(census):
    assert census["held_census_before"] == census["held_census_after"]
    b11 = census["held_census_before"]["B11 kg"]
    assert b11["held_bounded"] == 138 and b11["held_blank"] == 0
    for r in census["records"]:
        assert r["measured_net"] is None


def test_slab_parts_match_the_t318_split(census):
    slab = [r for r in census["records"] if r["group"] == "B11"]
    assert all(r["element_id"].endswith(A.SUFFIX) and r["parent_line_id"] for r in slab)
    assert sum(1 for r in slab if r["population"] == "TOP") == 79
    assert sum(1 for r in slab if r["population"] == "DEVELOPMENT") == 59
    for r in slab:   # every development part re-added by hand end by end equals its bound (A = low, B = high)
        if r["population"] == "DEVELOPMENT":
            hc = r["hand_calculation"]
            ka, kb = float(hc["A"]["kg"]), float(hc["B"]["kg"])
            lo, hi = float(r["bound_kg"]["low"]), float(r["bound_kg"]["high"])
            if "bare label" in r["ref"]:          # '5 in all' widens the bound: the counts lie inside it
                assert lo - 0.0015 <= min(ka, kb) and max(ka, kb) <= hi + 0.0015
                continue
            assert abs(min(ka, kb) - lo) <= 0.0015 and abs(max(ka, kb) - hi) <= 0.0015
            assert (r["cause_class"] == "FIX_ROW") == (r["bound_kg"]["low"] == r["bound_kg"]["high"])


def test_adverse_dev_hand_matches_one_line_by_hand():
    # L-10830d73 parent: 15 edge-beam ends, T10: 1.481 kg = sum(w - 0.040) x 100/162 -> sum = 2.399 m (3 dp)
    idx = {l["line_id"]: l for l in A._json(A.INDEX)["lines"]}
    eid = idx["L-10830d7336f146563db7"]["element_id"][: -len(A.SUFFIX)]
    par = next(l["line_id"] for l in idx.values() if l["element_id"] == eid)
    hc = A.dev_hand(par)
    assert hc["A"]["ends"] == hc["B"]["ends"] == 15 and hc["A"]["d_mm"] == 10
    assert abs(float(hc["A"]["kg"]) - 1.481) <= 0.0015


def test_fix_rows_are_proposals(census):
    fr = census["fix_rows"]
    assert sorted(f["id"] for f in fr) == sorted(f"FR-T647-{i}" for i in range(1, 23))
    assert all(f["wired"] is False for f in fr)
    assert sum(f["proposed_state"] == "NOT_APPLICABLE_WITH_EVIDENCE" for f in fr) == 5
    eff = census["fix_row_effect_if_wired"]
    assert eff["lines_leaving_held"] == 22
    assert eff["census_without_fix_lines"]["B11 kg"]["held_bounded"] == 121
    assert eff["census_without_fix_lines"]["B10 m3"]["held_blank"] == census["held_census_before"]["B10 m3"]["held_blank"] - 2


def test_dependencies_point_at_held_hosts_in_this_census(census):
    own = {r["line_id"]: r for r in census["records"]}
    for r in census["records"]:
        if r["cause_class"] == "DEPENDENCY":
            assert r["ref"] in own and own[r["ref"]]["cause_class"] != "DEPENDENCY" and r["host_cause"]


def test_outputs_current(census):
    p = A.OUT / "HELD_CAUSE_CENSUS_T647.json"
    assert p.exists(), "run test_write_outputs with URBAN_T647_WRITE=1"
    assert json.loads(p.read_text(encoding="utf-8")) == json.loads(A.dumps(census))


@pytest.mark.skipif(os.environ.get("URBAN_T647_WRITE") != "1", reason="writer: URBAN_T647_WRITE=1")
def test_write_outputs():
    A.write()
