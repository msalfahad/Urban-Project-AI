"""Round 6E: a stable identity, one release state, and one truth.

The four defects the independent audit found, each as a test that fails
if the engine ever goes back to them:

    an id that follows the enumeration rather than the space
    a release state that contradicts itself
    a report number the export's own rows do not add up to
    a stair read off its width, and a floor read as a landing
"""

from __future__ import annotations

import io
import tokenize

import pytest

from engine import export_provenance as xp
from engine import report_consistency as rcons
from engine import round6e_fixtures as fx
from engine import round6e_selftest as r6e
from engine import space_lineage as lineage
from engine import space_register as sreg
from engine import stair_assembly as stair
from engine import vertical_evidence as ve


def _code(module):
    out = []
    for tok in tokenize.generate_tokens(
            io.StringIO(open(module.__file__, encoding="utf-8").read())
            .readline):
        if tok.type in (tokenize.COMMENT, tokenize.STRING):
            continue
        out.append(tok.string)
    return " ".join(out)


@pytest.mark.parametrize("case", fx.cases(), ids=lambda c: c.name)
def test_every_round_6e_case_holds(case):
    result = r6e.check(case)
    assert result.passed, result.failures


def test_the_round_6e_requirements_are_frozen():
    rep = r6e.assert_frozen()
    assert rep["passed"] == rep["cases"] == 17
    assert rep["ROUND_6E_SYNTHETIC_HASH"]


# ---------------------------------------------------- §4, §5, §6 identity

def test_a_split_never_gives_a_child_the_parents_id():
    case = next(c for c in fx.cases() if c.name.startswith("C_"))
    rep = r6e.check(case)
    ids = rep.observed["stable_ids"].values()
    assert "PS-001" not in ids
    assert all(v == "SPLIT" for v in rep.observed["lineage"].values())


def test_a_merge_keeps_every_predecessor():
    case = next(c for c in fx.cases() if c.name.startswith("D_"))
    rep = r6e.check(case)
    assert sorted(rep.observed["predecessors"]["PS-101"]) == ["PS-001",
                                                              "PS-002"]


def test_nothing_in_the_lineage_matches_on_area():
    """§5. Do NOT match by area alone — not even as a tie-break."""
    body = _code(lineage)
    assert "area_m2" in body          # it is carried, and reported
    for forbidden in ("abs ( a . area_m2 - b . area_m2 )",
                      "area_m2 ==", "== area_m2"):
        assert forbidden not in body


def test_the_two_ids_are_different_things():
    assert lineage.MODEL.startswith("RUN_CANDIDATE_IS_NOT_A_PHYSICAL")
    link = lineage.Link(run_candidate_id="PS-DR-001-004",
                        stable_space_id="SP-abc")
    rec = link.record()
    assert rec["run_candidate_id"] != rec["stable_space_id"]


# -------------------------------------------------------- §3 one state

def test_release_eligible_never_coexists_with_its_own_refusal():
    for role in sreg.NEVER_A_ROOM_QUANTITY:
        assert role not in sreg.SPACE_ROLES or role in (
            sreg.EXTERIOR, sreg.VOID, sreg.SHAFT, sreg.STAIR)


def test_a_withheld_entry_always_says_why():
    case = next(c for c in fx.cases() if c.name.startswith("J_"))
    rep = r6e.check(case)
    assert "PS-900" not in rep.observed["released"]
    assert rep.observed["withheld"]["PS-900"]


# ------------------------------------------------------- §7 one truth

def test_a_disagreement_is_reported_and_never_adjusted():
    rows = [{"released": "true", "area_m2": "21.0"}]
    out = rcons.check(
        [("A", "T", 26.3085, {"where": {"released": True},
                              "column": "area_m2"})], {"T": rows})
    assert out["status"] == rcons.INCONSISTENT
    bad = out["disagreements"][0]
    assert bad["report_value"] == 26.3085
    assert bad["export_value"] == 21.0


def test_an_aggregation_is_deterministic():
    rows = [{"a": "1.5"}, {"a": "2.5"}]
    assert rcons.aggregate(rows, column="a") == \
        rcons.aggregate(list(reversed(rows)), column="a")


# ------------------------------------------- §1, §2 the export gate

def test_the_provenance_block_requires_every_field():
    with pytest.raises(xp.ExportRefused):
        xp.seal({"SOURCE_COMMIT": "abc"}, [])


def test_the_two_hashes_answer_two_questions():
    a = {"b": 2, "a": [1, 2]}
    b = {"a": [1, 2], "b": 2}
    assert xp.canonical_sha256(a) == xp.canonical_sha256(b)
    assert xp.canonical_sha256(a) != xp.canonical_sha256({"a": [2, 1],
                                                          "b": 2})


def test_an_export_from_a_failing_test_run_is_refused():
    with pytest.raises(xp.ExportRefused):
        xp.gate(input_sources=[], engine_hashes={},
                tests={"passed": 10, "failed": 1}, allow_dirty=True)


# --------------------------------------------- §9, §13 stairs

def test_a_main_stair_carries_a_storey():
    role, ev = stair._role(interior="INTERIOR", floors=["GROUND"],
                           width=9999.0, widest=9999.0, ties=1, hint="",
                           plans=1)
    assert role == stair.STAIR_ROLE_UNKNOWN
    assert "IT_IS_NOT_ESTABLISHED_TO_CARRY_A_STOREY" in ev


def test_a_service_stair_needs_more_than_geometry():
    for floors in (["GROUND"], ["GROUND", "FIRST"]):
        role, _ev = stair._role(interior="INTERIOR", floors=floors,
                                width=1200.0, widest=1200.0, ties=1,
                                hint="", plans=len(floors))
        assert role != stair.SERVICE_STAIR
    role, ev = stair._role(interior="INTERIOR", floors=["GROUND"],
                           width=1200.0, widest=1200.0, ties=1,
                           hint=stair.SERVICE_STAIR, plans=1)
    assert role == stair.SERVICE_STAIR
    assert ev and "RULE" in ev[0]


def test_only_a_landing_is_stair_quantity():
    a = stair.Assembly(stair_id="SA-1")
    a.landings = [stair.Landing(landing_id="L1", area_m2=1.8,
                                role=stair.STAIR_LANDING),
                  stair.Landing(landing_id="L2", area_m2=11.93,
                                role=stair.FLOOR_PLATE)]
    assert a.landing_m2 == 1.8
    assert a.not_stair_landing_m2 == 11.93
    assert a.landings[1].record()["landing_area_m2"] is None


def test_no_riser_height_is_ever_assumed():
    out = ve.assess([])
    assert out["riser_height_status"] == ve.NOT_ESTABLISHED
    body = _code(ve)
    for habit in ("170", "175", "150.0", "0.17"):
        assert f"= {habit}" not in body


def test_a_take_off_total_is_refused_by_name():
    found = ve.scan(["TOTAL GROUND FLOOR AREA =319.99M (68.00%%%)"],
                    source="x", representation="DESIGN_DWF", placed=False)
    assert found[0].status == ve.REFUSED_TAKE_OFF
    assert found[0].value_mm is None


def test_square_metres_and_linear_metres_are_never_added():
    q = stair.quantities([], [])
    assert "totals" in q and "units_are_never_added" in q
    units = {v["unit"] for v in q["totals"].values()}
    assert units == {"m2", "lm", "pcs"}
