"""T-590: RULE_DIFF provenance audit, structural (R-T590-1 = R-T591-1 + (g)..(j)). Synthetic villa "K590" (not the
training villa) by hand with its own registers: three RULE_DIFFERENCE rows, two with rule ids (one owner rule, one
method-register method) and one without -> UNRESOLVED; adverse cases (an id in no RULES_INDEX, a method id in no
register, a requirement-only owner answer offered as the choice, a Lead / worker record alone, his side a typed lump,
his side empty, a non-RULE_DIFF row, mirror / units); then the committed training-villa audit rebuilt from committed
research outputs and the repository registers (no private input)."""
from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t590"))
import t590_rules as R  # noqa: E402
import t590_alsenan as B  # noqa: E402

Dd = Decimal
E = R.ProvenanceError

REG = R.Registers(
    rules={"UP-CONC-JOINT-001": "OWNER_APPROVED", "UP-OLD-001": "DEPRECATED"},
    book={}, methods=set(), families=set(),
    method_reg={"URBAN-REBAR-NET-AND-PROCUREMENT@v1": "OD-V3-3", "URBAN-NO-DECISION@v1": ""},
    requirement_only={"Q-62": "measured once, one convention"})


def _row(delta, name="", source="", cls="RULE_DIFFERENCE"):
    return {"class": cls, "delta": delta, "name": name, "note": "", "source": source}


# K590 one bay, column 0.30 x 0.50 (A = 0.15 m2), storey 3.60 slab top to slab top, beam 0.20 x 0.60 x 4.00 clear,
# slab 0.15:
#  row 0 column JOINT_HEAD: ours slab top to slab top (UP-CONC-JOINT-001: column owns the joint), his clear 3.00 m ->
#        reference - engine = -0.15 x 0.60 = -0.090 m3                      -> SOURCED (cites its rule)
#  row 1 rebar group: ours counted bars (URBAN-REBAR-...@v1), his bars by a stated 100 kg/m3 rate on his rows
#        (readable convention) 0.250 - 0.212 = +0.038 t                      -> SOURCED_RECITE (cites only R-T999-1)
#  row 2 beam bearing 2 x 0.15 into the walls, ours none, no rule        -> NONE -> UNRESOLVED (+0.036 m3)
#  row 3 rounding TOLERANCE +0.001 m3
K_ROWS = [_row("-0.090", "column JOINT_HEAD (UP-CONC-JOINT-001)"),
          _row("0.038", "rebar group G1 (R-T999-1)"),
          _row("0.036", "beam bearing 2 x 0.15 x 0.20 x 0.60 into the walls (R-T999-2)"),
          _row("0.001", "rounding", cls="TOLERANCE")]


def test_k590_three_rows_by_hand():
    r0 = R.classify(REG, K_ROWS[0], ["UP-CONC-JOINT-001"], "column clear height 3.00 to the beam soffit")
    r1 = R.classify(REG, K_ROWS[1], ["URBAN-REBAR-NET-AND-PROCUREMENT@v1"], "100 kg/m3 on each of his rows")
    r2 = R.classify(REG, K_ROWS[2], [], "his beam rows add 0.15 m bearing at each end")
    assert (r0["outcome"], r0["class_after"]) == ("SOURCED", "RULE_DIFFERENCE")
    assert (r1["outcome"], r1["class_after"]) == ("SOURCED_RECITE", "RULE_DIFFERENCE")
    assert r1["sources"][0]["kind"] == "METHOD_REGISTER" and r1["sources"][0]["status"] == "OWNER_DECISION:OD-V3-3"
    assert "R-T999-1" in r1["cited_not_governing"]
    assert (r2["outcome"], r2["class_after"]) == ("NONE", "UNRESOLVED")
    # hand: 0.036 = 2 x 0.15 x 0.20 x 0.60
    assert Dd("2") * Dd("0.15") * Dd("0.20") * Dd("0.60") == Dd(K_ROWS[2]["delta"])
    m = R.reclass_section(K_ROWS, {0: r0, 1: r1, 2: r2})
    assert m["before"] == {"RULE_DIFFERENCE": Dd("-0.016"), "TOLERANCE": Dd("0.001")}
    assert m["after"] == {"RULE_DIFFERENCE": Dd("-0.052"), "UNRESOLVED": Dd("0.036"), "TOLERANCE": Dd("0.001")}
    assert sum(m["after"].values()) == sum(m["before"].values())       # section difference unchanged


def test_adverse_rule_id_not_in_rules_index_refused():
    with pytest.raises(E, match="not in docs/RULES_INDEX.md"):
        R.classify(REG, K_ROWS[0], ["UP-CONC-JOINT-099"], "clear height")
    with pytest.raises(E, match="DEPRECATED"):
        R.classify(REG, K_ROWS[0], ["UP-OLD-001"], "clear height")


def test_adverse_method_register():
    with pytest.raises(E, match="not in the Urban method register"):
        REG.judge("URBAN-REBAR-NOT-THERE@v1")
    with pytest.raises(E, match="without an owner decision"):
        REG.judge("URBAN-NO-DECISION@v1")


def test_requirement_only_does_not_source_a_choice():
    # Q-62 requires 'once, one convention'; offered alone for the ownership choice -> NONE, kept as a requirement
    r = R.classify(REG, K_ROWS[0], ["Q-62"], "column clear height")
    assert r["outcome"] == "NONE" and r["requirements"][0]["source"] == "Q-62"
    # with the choice rule beside it the row is sourced and the requirement stays listed
    r = R.classify(REG, K_ROWS[0], ["Q-62", "UP-CONC-JOINT-001"], "column clear height")
    assert r["outcome"] == "SOURCED" and [q["source"] for q in r["requirements"]] == ["Q-62"]


def test_lead_and_worker_records_alone_with_conflict_are_none():
    r = R.classify(REG, K_ROWS[0], ["R-T394-1", "REGISTER:column owns", "REGISTER:beam owns"], "clear height",
                   conflict="CONVENTION_RECORD_CONFLICT: two records, opposite owners")
    assert r["outcome"] == "NONE" and r["class_after"] == "UNRESOLVED"
    assert r["convention_record_conflict"].startswith("CONVENTION_RECORD_CONFLICT")


def test_his_side_typed_lump_unresolved_even_when_ours_sourced():
    r = R.classify(REG, K_ROWS[1], ["URBAN-REBAR-NET-AND-PROCUREMENT@v1"], "typed 0.250 t, no formula, no row",
                   his_readable=False)
    assert r["our_side_outcome"] == "SOURCED_RECITE"
    assert (r["outcome"], r["class_after"]) == ("HIS_SIDE_UNREADABLE", "UNRESOLVED")
    with pytest.raises(E, match="still states"):
        R.classify(REG, K_ROWS[1], ["URBAN-REBAR-NET-AND-PROCUREMENT@v1"], "  ", his_readable=False)
    with pytest.raises(E, match="his convention missing"):
        R.classify(REG, K_ROWS[1], ["URBAN-REBAR-NET-AND-PROCUREMENT@v1"], "")


def test_only_rule_difference_rows_and_units():
    with pytest.raises(E, match="only a RULE_DIFFERENCE"):
        R.classify(REG, K_ROWS[3], [], "x")
    with pytest.raises(E, match="unknown unit"):
        R.per_unit([("kg", "NONE", Dd("1"))])            # kg never beside t (owner rebar rule: tons)
    with pytest.raises(E, match="unknown outcome"):
        R.per_unit([("t", "MAYBE", Dd("1"))])


def test_mirror_sign_independent():
    # a mirrored bay gives the same deltas; a reclass never depends on the sign and never makes a delta 0
    neg = [_row(str(-Dd(r["delta"])), r["name"], cls=r["class"]) for r in K_ROWS]
    r2 = R.classify(REG, neg[2], [], "his bearing")
    m = R.reclass_section(neg, {2: r2})
    assert m["after"]["UNRESOLVED"] == Dd("-0.036")


# ------------------------------------------------------------------------------- training villa (committed) ----
def test_alsenan_rebuild_matches_committed():
    o = B.build()
    assert json.loads(B.JSON_OUT.read_text("utf-8")) == json.loads(json.dumps(o, ensure_ascii=False))
    assert B.MD_OUT.read_text("utf-8") == B.to_markdown(o)


def test_alsenan_counts_and_closure():
    o = B.build()
    assert o["rows_audited"] == 44 and o["rows_headline"] == 12 and o["released_quantities_changed"] == 0
    assert o["outcome_counts_headline"] == {"HIS_SIDE_UNREADABLE": 6, "NONE": 6}
    pu = o["per_unit_headline"]
    assert pu["m3"]["NONE"] == {"n": 6, "signed": "2.369278", "gross": "7.701778"}
    assert pu["t"]["HIS_SIDE_UNREADABLE"]["signed"] == "34.814694"
    assert o["b1_earthworks"]["rd_rows"] == 0
    for s in o["sections"]:
        if s["rd_rows"]:
            b = sum((Dd(v) for v in s["by_class_before"].values()), Dd(0))
            a = sum((Dd(v) for v in s["by_class_after"].values()), Dd(0))
            assert a == b == Dd(s["difference"]) and Dd(s["by_class_after"].get("RULE_DIFFERENCE", "0")) == 0
    assert all(r["delta"] not in ("0", "0.000000") for r in o["rows"])


def test_alsenan_pins_refuse_a_changed_input(monkeypatch):
    monkeypatch.setitem(B.PINS, "research/agents_t587/out/RECONCILED_STATEMENT_T587.json", "0" * 64)
    with pytest.raises(E, match="differs from its pin"):
        B.build()
