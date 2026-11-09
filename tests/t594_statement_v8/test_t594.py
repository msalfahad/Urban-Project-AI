"""T-594: reconciled-quantities statement V8 (restate T-571 lintels, T-574 yard / stair skirting, T-577 marble lm on
T-581 r2 / T-585 / T-592 + register 08:15; T-589 / T-595 beside). Synthetic villa "S594" (not the training villa) by
hand for the restatement rule R-T594-1 with adverse cases (parts that do not re-add, PAIRED parts that do not net 0, an
amend that moves a delta, a HELD part at 0 with no bound, a row named twice), then the merged training-villa sources
(committed research outputs only; no private input): V7 carried byte-equal (adverse: a changed V7 row fails), every
restated section closes with its V7 totals, the evidence map audited, the beside blocks re-added."""
from __future__ import annotations

import copy
import json
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t594"))
import t594_adapters as A  # noqa: E402
import t594_build as B  # noqa: E402

Dd = Decimal
E = A.StatementError


# ------------------------------------------------------------------------------- S594 by hand ---------------------
# S594 strip line: his 10.0 lm, engine valued 6.0 lm -> reference - engine +4.0.
#   V7 rows: "STRIPS: ours only" -1.0 ENGINE_RIGHT (WP); "STEPS: his block" +5.0 UNRESOLVED (PV).
#   A later report rules the step = the strip (one element): of his 5.0, 2.0 sit on our HELD strip lines (HELD, bound
#   2.0 .. 2.0), 0.5 is our VALUED strip S-3 (PAIRED with the 0.5 taken out of 'ours only'), 2.5 stay UNRESOLVED.
#   Restated: ENGINE_RIGHT -0.5, HELD +2.0, UNRESOLVED +2.5 = +4.0 (totals unchanged, residual 0); pairs +0.5 / -0.5.
def _sec() -> dict:
    rows = [A.A7.stamp(A.row("STRIPS: ours only", Dd("-1.0"), "ENGINE_RIGHT", "lm", "S594", "v"), A.WP, "v"),
            A.A7.stamp(A.row("STEPS: his block", Dd("5.0"), "UNRESOLVED", "lm", "S594", "v"), A.PV, "v"),
            A.A7.stamp(A.row("STRIPS: held lines", Dd("0"), "HELD", "lm", "S594", "v", bound=["3.0", "3.0"]), A.WP, "v")]
    return A.Z.section("S594/strips", "S594", "strips", "lm", "10.0", "6.0", rows, basis="S594 his block",
                       verification="v")


def _splits(pair_ok: bool = True) -> dict:
    return {"STEPS: his block": [
        {"name": "steps on held strips", "delta": Dd("2.0"), "class": "HELD", "evidence": A.CV, "tag": "S-1",
         "bound": ["2.0", "2.0"]},
        {"name": "S-3 pair", "delta": Dd("0.5"), "class": A.PAIRED, "evidence": A.PV, "tag": "S-1", "side": "ref"},
        {"name": "residual", "delta": Dd("2.5"), "class": "UNRESOLVED", "evidence": A.PV, "tag": "S-1"}],
        "STRIPS: ours only": [
        {"name": "strips ours only", "delta": Dd("-0.5"), "class": "ENGINE_RIGHT", "evidence": A.WP, "tag": "S-1"},
        {"name": "S-3 pair", "delta": Dd("-0.5") if pair_ok else Dd("-0.4"), "class": A.PAIRED, "evidence": A.PV,
         "tag": "S-1", "side": "eng"}] if pair_ok else [
        {"name": "strips ours only", "delta": Dd("-0.6"), "class": "ENGINE_RIGHT", "evidence": A.WP, "tag": "S-1"},
        {"name": "S-3 pair", "delta": Dd("-0.4"), "class": A.PAIRED, "evidence": A.PV, "tag": "S-1", "side": "eng"}]}


def test_s594_restate_by_hand():
    amends = {"STRIPS: held lines": {"tag": "S-2", "evidence": A.WP, "set": {"bound": ["1.0", "1.0"]}}}
    sec, moves, pairs = A.restate(_sec(), "S594/strips@V8", _splits(), amends, "v", lambda r: r["evidence_status"])
    assert (sec["reference_total"], sec["engine_valued"], sec["difference"]) == ("10.0", "6.0", "4.0")
    assert Dd(sec["closure_residual"]) == 0 and sec["restates"] == "S594/strips"
    bc = {k: Dd(v) for k, v in sec["by_class"].items() if Dd(v)}
    assert bc == {"ENGINE_RIGHT": Dd("-0.5"), "HELD": Dd("2.0"), "UNRESOLVED": Dd("2.5")}
    assert sorted(Dd(p["delta"]) for p in pairs) == [Dd("-0.5"), Dd("0.5")]
    assert {(m["from"], m["to"], Dd(m["delta"])) for m in moves} == {
        ("UNRESOLVED", "HELD", Dd("2.0")), ("UNRESOLVED", A.PAIRED, Dd("0.5")), ("ENGINE_RIGHT", A.PAIRED, Dd("-0.5"))}
    held = [r for r in sec["rows"] if r["name"] == "STRIPS: held lines"][0]
    assert held["bound"] == ["1.0", "1.0"] and held["delta"] == "0" and held["tag"] == "S-2"


def test_s594_adverse_parts_do_not_readd():
    sp = _splits()
    sp["STEPS: his block"][2]["delta"] = Dd("2.4")
    with pytest.raises(E, match="do not re-add"):
        A.restate(_sec(), "S594/strips@V8", sp, {}, "v", lambda r: r["evidence_status"])


def test_s594_adverse_pairs_not_net_zero():
    with pytest.raises(E, match="PAIRED parts net"):
        A.restate(_sec(), "S594/strips@V8", _splits(pair_ok=False), {}, "v", lambda r: r["evidence_status"])


def test_s594_adverse_amend_moves_delta_and_held_zero():
    with pytest.raises(E, match="may not change a delta"):
        A.restate(_sec(), "x", {}, {"STEPS: his block": {"tag": "t", "evidence": A.PV, "set": {"delta": "4"}}}, "v",
                  lambda r: r["evidence_status"])
    with pytest.raises(E, match="HELD row"):
        A.restate(_sec(), "x", {}, {"STRIPS: held lines": {"tag": "t", "evidence": A.WP, "set": {"bound": None}}}, "v",
                  lambda r: r["evidence_status"])
    with pytest.raises(E, match="found 0 times"):
        A.restate(_sec(), "x", {"nope": []}, {}, "v", lambda r: r["evidence_status"])
    s2 = _sec()
    s2["rows"].append(copy.deepcopy(s2["rows"][0]))
    s2["reference_total"] = "9.0"
    with pytest.raises(E, match="found 2 times"):
        A.restate(s2, "x", {"STRIPS: ours only": []}, {}, "v", lambda r: r["evidence_status"])


def test_s594_adverse_unknown_class_and_evidence():
    sp = _splits()
    sp["STEPS: his block"][2]["class"] = "GUESS"
    with pytest.raises(E, match="not a statement class"):
        A.restate(_sec(), "x", sp, {}, "v", lambda r: r["evidence_status"])
    sp = _splits()
    sp["STEPS: his block"][2]["evidence"] = "LOOKS_RIGHT"
    with pytest.raises(E, match="not a status"):
        A.restate(_sec(), "x", sp, {}, "v", lambda r: r["evidence_status"])


# ------------------------------------------------------------------------------- training villa ------------------
@pytest.fixture(scope="module")
def st7():
    return B.v7_statement()


@pytest.fixture(scope="module")
def st(st7):
    return B.build_from(st7, B.sources())


def _sec8(st, sid):
    return [c for c in st["sections_v8"] if c["section_id"] == sid][0]


def test_build_reproduces_committed_output(st):
    assert st == json.loads(B.JSON_OUT.read_text(encoding="utf-8"))
    assert B.to_markdown(st) == B.MD_OUT.read_text(encoding="utf-8")


def test_v7_carried_byte_equal_and_adverse(st, st7):
    B.check_v7_unchanged(st, st7)
    bad = copy.deepcopy(st)
    bad["sections_v7"][0]["rows"][0]["delta"] = "9.999"
    with pytest.raises(E, match="V7 key sections_v7 changed"):
        B.check_v7_unchanged(bad, st7)
    bad = copy.deepcopy(st)
    bad["reclasses"] = bad["reclasses"][1:]
    with pytest.raises(E, match="prefix"):
        B.check_v7_unchanged(bad, st7)


def test_restated_sections_close_with_v7_totals(st, st7):
    olds = {c["section_id"]: c for c in st7["sections_v6"] + st7["sections_v7"]}
    for c in st["sections_v8"]:
        o = olds[c["restates"]]
        assert (c["reference_total"], c["engine_valued"], c["difference"]) == \
               (o["reference_total"], o["engine_valued"], o["difference"])
        assert Dd(c["closure_residual"]) == 0 and c["difference_pct_of_reference"] is None
        assert sum(Dd(r["delta"]) for r in c["rows"]) == Dd(c["difference"])
        assert B.SUPERSEDES[c["restates"]] == c["section_id"]
        for r in c["rows"]:
            assert not (r["class"] == "HELD" and Dd(r["delta"]) == 0 and not r.get("bound"))


def test_lintels_d_gf_09_conflict(st):
    c = _sec8(st, "T-571/lintel-count-implied@V8")
    r = [x for x in c["rows"] if x["name"].startswith("D-GF-09")][0]
    assert (r["class"], r["was_class"], r["delta"], r["evidence_status"]) == ("UNRESOLVED", "RULE_DIFFERENCE", "0",
                                                                           A.CV)
    assert c["beside_lm"]["engine_at_most"] == "91.5 .. 91.8" and c["beside_lm"]["implied"] == "84.9"
    rd = c["by_length_engine_readings"]
    lo, hi = rd["low (D-GF-09 0.90)"], rd["high (D-GF-09 1.00)"]
    assert sum(lo.values()) == sum(hi.values()) == 60 and (lo["1.2"], lo["1.5"], hi["1.2"], hi["1.5"]) == (30, 20, 29, 21)
    assert sum(Dd(L) * n for L, n in hi.items()) == Dd("91.8")


def test_yard_and_stair_skirting(st):
    o = _sec8(st, "T-574/skirting-outdoor@V8")
    assert {k: v for k, v in o["by_class"].items() if Dd(v)} == {"RULE_DIFFERENCE": "81.32"}
    assert o["beside"]["wall_foot_not_in_drawing_lm"] == "59.582"
    sk = _sec8(st, "T-574/skirting-stairs@V8")
    assert Dd(sk["by_class"]["HELD"]) == Dd("19.359049") == Dd(sk["beside"]["flight_lower_bounds_lm_v8"])
    assert Dd(sk["by_class"]["UNRESOLVED"]) == Dd("0.710951") - Dd("2.35")
    w = [r for r in sk["rows"] if r["name"].startswith("ST-01 main: winder")][0]
    assert w["bound"] == ["2.35", "2.620191"] and w["was_class"] == "UNRESOLVED"
    e1 = [r for r in sk["rows"] if r["name"].startswith("ST-03 entrance (E1): his")][0]
    assert "NOT_IN_DRAWING" in e1["note_v8"] and e1["class"] == "UNRESOLVED"


def test_marble_lm_door_and_gate_steps(st, st7):
    m = _sec8(st, "T-577/marble-lm@V8")
    bc = {k: Dd(v) for k, v in m["by_class"].items()}
    assert bc["HELD"] == Dd("3.8") and bc["UNRESOLVED"] == Dd("2.9") and bc["ENGINE_WRONG"] == Dd("11.2")
    assert bc["ENGINE_RIGHT"] == Dd("-48.13")
    assert sum(Dd(p["delta"]) for p in m["beside"]["agree_pairs_v8"]) == 0
    assert len(m["beside"]["agree_pairs_v8"]) == 2 and m["beside"]["door_steps_t592"]["gate_status"] == "PARTIAL"
    old = [c for c in st7["sections_v7"] if c["section_id"] == "T-577/marble-lm@V7"][0]
    keep = [r for r in m["rows"] if "tag" not in r or not r["tag"].startswith("F-T594")]
    assert all(r in old["rows"] for r in keep) and len(keep) == len(old["rows"]) - 4


def test_marble_adverse_gate_folded_or_length_moved(st7):
    src = B.sources()
    bad = copy.deepcopy(src)
    bad["T-593"]["door_steps"]["gate"]["in_house_total"] = True
    with pytest.raises(E, match="manifest V10"):
        A.t592_marble_lm(st7, bad["T-592"], bad["T-577"], bad["T-593"])
    bad = copy.deepcopy(src)
    bad["T-592"]["openings"]["D-GF-05"]["payable_lm"] = "0.9"
    with pytest.raises(E, match="D-GF-05"):
        A.t592_marble_lm(st7, bad["T-592"], bad["T-577"], bad["T-593"])


def test_evidence_audit_refuses_a_promoted_row(st):
    c = copy.deepcopy(_sec8(st, "T-577/marble-lm@V8"))
    r = [x for x in c["rows"] if x["name"].startswith("EXT gate step")][0]
    r["evidence_status"] = A.CV
    with pytest.raises(E, match="verdict gives PARTIALLY_VERIFIED"):
        A.A7.audit_evidence(c, lambda x: B.expected_v8(c["section_id"], x))


def test_headline_keeps_v7_rows_and_marks_supersession(st):
    h7 = {h["section_id"]: h for h in st["headline_v7"]}
    for h in st["headline_v8"]:
        if h["section_id"] in h7:
            assert h["by_class_evidence"] == h7[h["section_id"]]["by_class_evidence"]
    sup = {h["section_id"]: h["superseded_by"] for h in st["headline_v8"]}
    assert sup["T-577/marble-lm@V7"] == "T-577/marble-lm@V8" and sup["T-571/lintel-count-implied"].endswith("@V8")
    assert sup["T-577/marble-lm"] == "T-577/marble-lm@V7" and sup["T-577/marble-lm@V8"] is None


def test_beside_blocks(st):
    t589, rb, fb = st["beside_v8"]
    assert {k: v["n"] for k, v in t589["sections"].items()} == {"B1": 19, "B10": 59, "B11": 13}
    assert rb["at_least_t"] == "0.789555" and rb["valued_t"] == "0" and rb["candidate_line"] is False
    e = rb["expected_after_v8_rebar_rows"]
    assert (e["held_at_least_t"], e["residual_after_held_at_most_t"]) == ("1.828715", "2.071285")
    assert Dd(e["held_at_least_t"]) + Dd(e["residual_after_held_at_most_t"]) == \
           Dd(e["held_at_least_was_t"]) + Dd(e["residual_was_at_most_t"])
    assert fb["family_bounded_part_m3"]["low"] == "7.628500" and fb["his"]["class"] == "WITHIN"
    assert st["released_quantities_changed"] == 0


def test_no_new_private_text(st, st7):
    """V8 adds no non-Latin text (the V4 parapet label inherited byte-equal from V7 is not re-checked here)."""
    txt = json.dumps({k: v for k, v in st.items() if k not in st7 or k in B.EXTENDED and k != "reclasses"},
                     ensure_ascii=False) + json.dumps(st["reclasses"][len(st7["reclasses"]):], ensure_ascii=False)
    assert not any("؀" <= ch <= "ۿ" for ch in txt)
