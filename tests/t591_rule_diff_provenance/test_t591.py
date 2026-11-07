"""T-591: RULE_DIFF provenance audit (R-T591-1). Synthetic villa "K591" (not the training villa) by hand with its own
registers, adverse cases (open / withdrawn / deferred owner question cited as a rule, an id in no register, a
deprecated rule, a worker method record or a Lead register ruling alone, a scenario-only answer, a wrong-trade
citation, no convention on his side, a non-RULE_DIFF row, a unit outside the list), then the committed training-villa
audit (rebuilt from committed research outputs and the repository registers; no private input)."""
from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t591"))
import t591_rules as R  # noqa: E402
import t591_alsenan as B  # noqa: E402

Dd = Decimal
E = R.ProvenanceError

# K591 registers: two owner rules, one provisional, one deprecated, one rulebook record, one owner method, one family.
REG = R.Registers(
    rules={"UP-CER-003": "RULE_STORE_MANDATORY", "UP-SKIRT-001": "OWNER_APPROVED",
           "UP-MAS-HEIGHT-001": "REQUIRES_CONFIRMATION", "UP-DOOR-MIN-001": "DEPRECATED",
           "UP-OPEN-SCHED-001": "OWNER_APPROVED"},
    book={"UPC-BLOCK-OPENINGS-001": "OWNER_CONFIRMED", "UPC-CEMENT-LAYERS-METHOD-001": "METHOD_ONLY_VALUES_HELD"},
    methods={"URBAN-SKIRTING-OPENING-METHOD"}, families={"EXT.FENCE.WALL"})


def _row(delta, name="", note="", source="", cls="RULE_DIFFERENCE"):
    return {"class": cls, "delta": delta, "name": name, "note": note, "source": source}


# K591 skirting, one dry room 4.00 x 3.00 (outline 14.00 lm), his gross 14.00, ours 12.78:
#   door D1 0.90 deducted (UP-CER-003)            RULE_DIFFERENCE +0.90  -> SOURCED
#   wet-room tile height (Q-48, another section)   RULE_DIFFERENCE +0.00  (nr check below uses Q-48)
#   doorless arch A1 jambs 2 x 0.15 refused by us  RULE_DIFFERENCE +0.30  -> NONE -> UNRESOLVED
#   outline rounding                               TOLERANCE      +0.02
#   difference 14.00 - 12.78 = 1.22 = 0.90 + 0.30 + 0.02
K_ROWS = [_row("0.90", "door D1 0.90 deducted (UP-CER-003)"),
          _row("0.30", "arch A1 jamb returns 2 x 0.15: a jamb takes no skirting (R-T999-1)"),
          _row("0.02", "outline", cls="TOLERANCE")]


def test_k591_hand_closure_and_reclass():
    r0 = R.classify(REG, K_ROWS[0], ["UP-CER-003"], "gross perimeter, no door deducted")
    r1 = R.classify(REG, K_ROWS[1], [], "his outline adds both 0.15 m arch jambs")
    assert r0["outcome"] == "SOURCED" and r0["class_after"] == "RULE_DIFFERENCE"
    assert r1["outcome"] == "NONE" and r1["class_after"] == "UNRESOLVED"
    assert r1["cited_in_row"] == ["R-T999-1"]
    m = R.reclass_section(K_ROWS, {0: r0, 1: r1})
    assert m["before"] == {"RULE_DIFFERENCE": Dd("1.20"), "TOLERANCE": Dd("0.02")}
    assert m["after"] == {"RULE_DIFFERENCE": Dd("0.90"), "UNRESOLVED": Dd("0.30"), "TOLERANCE": Dd("0.02")}
    assert sum(m["after"].values()) == Dd("14.00") - Dd("12.78")


def test_k591_answered_q_sourced_and_q_for_his_side_neutral():
    row = _row("-3.15", "W.C. tile height: owner tile top (Q-48 A) vs his flat height; his 1.10 = Q-04 minimum")
    r = R.classify(REG, row, ["Q-48"], "one flat tile height per room")
    assert r["outcome"] == "SOURCED" and r["cited_valid"] == ["Q-48"] and not r["cited_not_governing"]


def test_recite_when_row_cites_only_a_method_record_or_nothing():
    r = R.classify(REG, _row("1.0", "door OP-1 (T-296 table)"), ["UP-CER-003"], "gross")
    assert r["outcome"] == "SOURCED_RECITE"
    r = R.classify(REG, _row("1.0", "door OP-1 (R-T443-1)"), ["UP-CER-003"], "gross")
    assert r["outcome"] == "SOURCED_RECITE"


def test_recite_wrong_trade_citation():
    row = _row("7.88", "opening deductions (Q-73 full)")
    r = R.classify(REG, row, ["UP-OPEN-SCHED-001"], "half his openings",
                   {"Q-73": "blockwork, not plaster"})
    assert r["outcome"] == "SOURCED_RECITE" and "Q-73" in r["cited_not_governing"]


def test_provisional_rule_alone_is_labelled():
    r = R.classify(REG, _row("2.5", "height (UP-MAS-HEIGHT-001)"), ["UP-MAS-HEIGHT-001"], "flat storey height")
    assert r["outcome"] == "SOURCED" and r["provisional"] is True


@pytest.mark.parametrize("src,msg", [
    ("Q-80", "OPEN"), ("Q-79", "WITHDRAWN"), ("Q-34", "not a rule"), ("Q-23", "not a rule"),
    ("Q-99", "not an answered"), ("UP-FOO-999", "not in docs/RULES_INDEX.md"), ("UP-DOOR-MIN-001", "DEPRECATED"),
    ("UPC-NONE-001", "rulebook"), ("URBAN-NOT-A-METHOD", "owner method"), ("FAMILY:EXT.NOPE", "family"),
    ("OWNER_FILE:OWNER_NOTES_SIGMA_2026-10-21#item 9", "owner rule"), ("OWNER_FILE:MY_NOTES#all", "owner rule"),
    ("SOMETHING", "unknown source form")])
def test_adverse_refused_sources(src, msg):
    with pytest.raises(E, match=msg):
        R.classify(REG, _row("1.0", "x"), [src], "his convention")


@pytest.mark.parametrize("alone", [["R-T443-1"], ["REGISTER:STAIR SKIRTING vs ROOM SKIRTING"], ["Q-29"],
                                   ["UPC-CEMENT-LAYERS-METHOD-001", "R-T100-1"]])
def test_adverse_non_rule_sources_alone_give_none(alone):
    r = R.classify(REG, _row("0.4", "x"), alone, "his convention")
    if alone[0].startswith("UPC-"):
        assert r["outcome"] == "SOURCED_RECITE" and r["provisional"] is True  # a method-only rulebook record: provisional
    else:
        assert r["outcome"] == "NONE" and r["class_after"] == "UNRESOLVED"


def test_adverse_open_q_cited_in_row_is_not_a_valid_citation():
    r = R.classify(REG, _row("1.0", "black block face (Q-80)"), ["UPC-BLOCK-OPENINGS-001"], "his convention")
    assert r["outcome"] == "SOURCED_RECITE" and "Q-80" in r["cited_not_governing"]


def test_adverse_his_side_and_class_and_unit():
    with pytest.raises(E, match="his convention"):
        R.classify(REG, _row("1.0"), ["UP-CER-003"], "  ")
    with pytest.raises(E, match="only a RULE_DIFFERENCE"):
        R.classify(REG, _row("1.0", cls="HELD"), ["UP-CER-003"], "x")
    with pytest.raises(E, match="unknown unit"):
        R.per_unit([("m", "NONE", Dd(1))])
    t = R.per_unit([("lm", "NONE", Dd("0.3")), ("m2", "NONE", Dd("-2")), ("lm", "NONE", Dd("-0.1"))])
    assert t["lm"]["NONE"] == {"n": 2, "signed": Dd("0.2"), "gross": Dd("0.4")} and t["m2"]["NONE"]["n"] == 1


def test_adverse_reclass_keeps_delta_never_zero():
    r = R.classify(REG, K_ROWS[1], [], "his jambs")
    m = R.reclass_section(K_ROWS, {1: r})
    assert m["after"]["UNRESOLVED"] == Dd("0.30")


# ---------------------------------------------------------------------------------- training villa (committed) -----
@pytest.fixture(scope="module")
def built():
    return B.build()


def test_alsenan_rebuild_identical(built):
    js = json.dumps(built, indent=1, ensure_ascii=False) + "\n"
    assert B.JSON_OUT.read_text(encoding="utf-8") == js
    assert B.MD_OUT.read_text(encoding="utf-8") == B.to_markdown(built)


def test_alsenan_scope_and_counts(built):
    assert built["rows_audited"] == 119 and built["rows_live"] == 117
    assert built["outcome_counts_live"] == {"NONE": 1, "SOURCED": 40, "SOURCED_RECITE": 76}
    secs = {s["section_id"] for s in built["sections"]}
    assert not any(s.startswith(("T-545", "T-551", "T-560", "T-572", "T-576")) for s in secs)
    none = [r for r in built["rows"] if r["outcome"] == "NONE"]
    assert [(r["section_id"], r["row"], r["delta"]) for r in none] == [("T-574/skirting-room", 29, "0.30")]
    assert "URBAN-SKIRTING-OPENING-METHOD" in none[0]["contrary_rule"]


def test_alsenan_sections_close_and_only_skirting_moves(built):
    for s in built["sections"]:
        b, a = s["by_class_before"], s["by_class_after"]
        assert sum(Dd(v) for v in b.values()) == sum(Dd(v) for v in a.values()) == Dd(s["difference"])
        if s["section_id"] != "T-574/skirting-room":
            assert a == b
    sk = next(s for s in built["sections"] if s["section_id"] == "T-574/skirting-room")
    assert Dd(sk["by_class_before"]["RULE_DIFFERENCE"]) - Dd(sk["by_class_after"]["RULE_DIFFERENCE"]) == Dd("0.30")
    assert Dd(sk["by_class_after"]["UNRESOLVED"]) - Dd(sk["by_class_before"]["UNRESOLVED"]) == Dd("0.30")


def test_alsenan_q73_never_cited_for_plaster_or_paint(built):
    for r in built["rows"]:
        if r["section_id"].startswith(("T-552/plaster-internal", "T-561/paint-internal")) and "Q-73" in r["cited_in_row"]:
            assert "Q-73" in r["cited_not_governing"] and r["outcome"] == "SOURCED_RECITE"
            assert [s["source"] for s in r["our_side"]][0] == "UP-OPEN-SCHED-001"


def test_alsenan_no_percent_and_no_release(built):
    assert built["released_quantities_changed"] == 0
    assert "%" not in B.MD_OUT.read_text(encoding="utf-8").split("No % anywhere")[1]
    assert all(r["his_side"] for r in built["rows"])


def test_alsenan_pin_refused_on_drift(monkeypatch):
    monkeypatch.setitem(B.PINS, "research/agents_t587/out/RECONCILED_STATEMENT_T587.json", "0" * 64)
    with pytest.raises(E, match="sha256"):
        B.build()


def test_alsenan_doorless_jamb_check(built):
    rows = {d["opening"]: d for d in built["doorless_jamb_check"]}
    a = rows["A-1F-01 / 1F OP-011"]
    assert a["status"] == "CONDITIONS_MET" and Dd(a["jamb_lm"]) == 2 * Dd(a["wall_t_m"]) == Dd("0.30")
    none = next(r for r in built["rows"] if r["outcome"] == "NONE")
    assert Dd(none["delta"]) == Dd(a["jamb_lm"]) and a["statement_row"] == "T-574/skirting-room row 29"
    for d in built["doorless_jamb_check"]:
        if d["status"] == "HELD":                       # an unknown jamb depth is held by name, never 0
            assert d["jamb_lm"].startswith("HELD") and d["wall_t_m"] == "not established"
