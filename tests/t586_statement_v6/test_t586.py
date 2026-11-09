"""T-586: reconciled-quantities statement V6 adapters for T-571 (lintel count, nr), T-574 (skirting, lm / nr), T-575
(rebar HELD ranges, t) and T-577 (marble by unit). Synthetic villa "S586" (not the training villa) by hand per adapter,
adverse cases (% on a NO_ROW / implied lintel count, count x length shown as m2, HELD_RANGE shown as a point, kg inside
a t block, AGREE terms that do not cancel, an unmapped verdict), then the merged training-villa sources (committed
research outputs only; no private input)."""
from __future__ import annotations

import copy
import json
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t586"))
import t586_adapters as A  # noqa: E402
import t586_build as B  # noqa: E402

Dd = Decimal
E = A.StatementError


# ------------------------------------------------------------------------------- T-571 lintel count (nr) ----------
# S586: engine openings E1 0.90 -> 1.20, E2 1.00 -> 1.50, E3 1.30 -> 2.50 (engine only); his rows H1 0.90 -> 1.20
# (same piece), H2 1.10 -> 1.50 vs E2 (same piece), H4 3.60 -> 4.00 (his only, NOT_IN_MASONRY on our side).
# Engine 1.20 x1, 1.50 x1, 2.50 x1 = 3; implied 1.20 x1, 1.50 x1, 4.00 x1 = 3; implied - engine: 2.50 -1, 4.00 +1, net 0.
def _tab(**kw):
    t = {L: {"GF": 0, "1F": 0, "2F": 0, "UNSPLIT": 0} for L in A.LENGTHS}
    for L, n in kw.items():
        t[L.replace("_", ".")]["GF"] = n
    return t


def _s571():
    eng = {"at_most": _tab(**{"1_2": 1, "1_5": 1, "2_5": 1}), "total_at_most_nr": 3, "total_established_nr": 1,
           "lm_beside_at_most": {"1.2": 1.2, "1.5": 1.5, "2.5": 2.5, "3.0": 0.0, "4.0": 0.0}}
    his = {"at_most": _tab(**{"1_2": 1, "1_5": 1, "4_0": 1}), "total_at_most_nr": 3, "total_established_nr": 3,
           "lm_beside_at_most": {"1.2": 1.2, "1.5": 1.5, "2.5": 0.0, "3.0": 0.0, "4.0": 4.0}}
    pairs = [{"ours": "E1", "theirs": "H1", "piece_ours": 1.2, "piece_theirs": 1.2, "state_ours": "REQUIRED",
              "cause": "SAME_PIECE"},
             {"ours": "E2", "theirs": "H2", "piece_ours": 1.5, "piece_theirs": 1.5, "state_ours": "HELD",
              "cause": "SAME_PIECE"},
             {"ours": "P-1F-01", "theirs": None, "piece_ours": 2.5, "state_ours": "HELD", "cause": "ENGINE_ONLY"},
             {"ours": "W17", "theirs": "H4", "piece_ours": None, "piece_theirs": 4.0, "state_ours": "NO_LINTEL",
              "cause": "NOT_IN_MASONRY"}]
    return {"engine_owner_0.15": eng, "freelancer_owner_0.15": his, "pairs_owner_0.15": pairs}


def test_t571_implied_count_by_hand():
    (sec,), (nc,) = A.t571_sections(_s571())
    assert (sec["reference_total"], sec["engine_valued"], sec["difference"]) == ("3", "3", "0")
    assert sec["by_length"]["2.5"]["difference"] == -1 and sec["by_length"]["4.0"]["difference"] == 1
    assert sec["reference_kind"] == "FREELANCER_IMPLIED" and sec["difference_pct_of_reference"] is None
    assert sec["beside_lm"] == {"unit": "lm", "implied": "6.7", "engine_at_most": "5.2",
                                "note": "count x stock length, beside the nr section, never summed with it"}
    assert nc["reference_total"] == "NO_ROW" and nc["difference_pct_of_reference"] is None


def test_t571_adverse_pct_on_no_row_refused():
    (sec,), (nc,) = A.t571_sections(_s571())
    bad = dict(sec, difference_pct_of_reference="0.00")
    with pytest.raises(E, match="FREELANCER_IMPLIED"):
        A.refuse_pct_without_row(bad)
    with pytest.raises(E, match="no reference row|NO_ROW"):
        A.refuse_pct_without_row(dict(nc, section_id=nc["block_id"], difference_pct_of_reference="1.00"))


def test_t571_adverse_closure_and_unknown_cause():
    d = _s571()
    d["freelancer_owner_0.15"]["at_most"]["4.0"]["GF"] = 2           # a row with no pair: causes no longer close
    d["freelancer_owner_0.15"]["total_at_most_nr"] = 4
    with pytest.raises(E, match="causes"):
        A.t571_sections(d)
    d = _s571()
    d["pairs_owner_0.15"][2]["cause"] = "GUESS"
    with pytest.raises(E, match="no Checker class"):
        A.t571_sections(d)


# ------------------------------------------------------------------------------- T-574 skirting (lm) --------------
# S586 room R1 4.00 x 3.00, one door 0.90, one arch 1.00 he also leaves out: his perimeter 2 x 7.00 - 1.00 = 13.00;
# ours 14.00 - 0.90 door - 1.00 arch = 12.10. ours - his = -0.90: door RULE_DIFFERENCE -0.90; arch -1.00 (ours) and
# +1.00 (his outline) AGREE, cancelling.
def _room():
    return {"id": "R1", "unit": "lm", "ours": "12.10", "his": "13.00", "gap": "-0.90",
            "causes": [{"label": "door 0.90", "verdict": "RULE_DIFFERENCE", "kind": "DEDUCTION", "amount": "-0.90"},
                       {"label": "arch 1.00", "verdict": "AGREE", "kind": "DEDUCTION", "amount": "-1.00"},
                       {"label": "his outline leaves the arch out", "verdict": "AGREE", "kind": "OUTLINE",
                        "amount": "1.00"}]}


def test_t574_cause_rows_sign_and_agree():
    rows, agree, mv = A.cause_rows([_room()], "lm", "S", "v")
    assert [(r["delta"], r["class"]) for r in rows] == [("0.90", "RULE_DIFFERENCE")]
    assert len(agree) == 2 and sum(Dd(a["amount"]) for a in agree) == 0 and mv == []


def test_t574_adverse_agree_not_cancelling_refused():
    g = _room()
    g["causes"][2]["amount"] = "0.80"
    g["gap"] = "-1.10"
    with pytest.raises(E, match="AGREE terms net"):
        A.cause_rows([g], "lm", "S", "v")


def test_adverse_unmapped_verdict_refused_and_omission_mapped():
    g = _room()
    g["causes"][0]["verdict"] = "LOOKS_FINE"
    with pytest.raises(E, match="neither a class"):
        A.cause_rows([g], "lm", "S", "v")
    g = _room()
    g["causes"][0]["verdict"] = "ENGINE_OMISSION"
    rows, _, mv = A.cause_rows([g], "lm", "S", "v")
    assert rows[0]["class"] == "UNRESOLVED" and rows[0]["tag"] == "F-T586-1" and mv[0]["from"] == "ENGINE_OMISSION"


# ------------------------------------------------------------------------------- T-575 rebar ranges (t) -----------
def _rr(**kw):
    r = {"row_id": "X", "status": "HELD_RANGE", "unit": "t", "t_low": 0.1, "t_high": 0.2}
    r.update(kw)
    return r


def test_t575_held_range_ok():
    A.check_held_range(_rr(), "t")
    A.check_held_range(_rr(status="HELD_BLANK", t_low=None, t_high=None, missing="height not printed"), "t")


@pytest.mark.parametrize("kw", [dict(value=0.15), dict(t_low=None), dict(t_high=None), dict(t_low=0.3),
                                dict(t_low=0.0), dict(valued=0.1)])
def test_t575_adverse_held_range_as_point_refused(kw):
    with pytest.raises(E):
        A.check_held_range(_rr(**kw), "t")


def test_t575_adverse_kg_in_t_refused():
    with pytest.raises(E, match="kg"):
        A.check_held_range(_rr(unit="kg", t_low=100.0, t_high=200.0), "t")
    with pytest.raises(E, match="HELD_BLANK"):
        A.check_held_range(_rr(status="HELD_BLANK", t_low=0.1, t_high=None, missing="x"), "t")


# ------------------------------------------------------------------------------- T-577 marble by unit -------------
# S586: his m2 column 3.00 = landing area 1.00 (1.00 x 1.00) + door steps 2 x 1.00 (count x length booked as area).
# Ours: landing 1.00 m2, two door strips 0.90 x 0.20 = 0.36 m2. m2 reference = 1.00 only; lm 2 x 0.90 = 1.80 vs his 2.00.
def _s577():
    m2 = [{"id": "LANDING", "ours": "1.00", "his": "1.00", "gap": "0", "cells": ["H17"], "causes": []},
          {"id": "DOORS", "ours": "0.36", "his": "2.00", "gap": "-1.64", "cells": ["H36", "H37"],
           "causes": [{"label": "length in area column", "verdict": "RULE_DIFFERENCE", "kind": "UNIT",
                       "amount": "-2.00"},
                      {"label": "strips", "verdict": "ENGINE_RIGHT", "kind": "SCOPE", "amount": "0.36"}]}]
    lm = [{"id": "DOORS", "ours": "1.80", "his": "2.00", "gap": "-0.20", "cells": ["B36xC36", "B37xC37"],
           "causes": [{"label": "step vs strip", "verdict": "UNRESOLVED", "kind": "SCOPE", "amount": "-0.20"}]}]
    nr = [{"id": "DOORS", "ours": "2", "his": "2", "gap": "0", "cells": ["B36", "B37"],
           "causes": [{"label": "count", "verdict": "AGREE", "kind": "MEASURE", "amount": "0"}]}]
    tot = lambda o, h: {"ours": o, "his": h, "gap": Z(o, h)}          # noqa: E731
    return {"tables": {"m2": {"groups": m2, "totals": tot("1.36", "3.00")},
                       "lm": {"groups": lm, "totals": tot("1.80", "2.00")},
                       "nr": {"groups": nr, "totals": tot("2", "2")}}}


def Z(o, h):
    return str(Dd(o) - Dd(h))


def test_t577_length_leaves_the_area_total():
    secs, (nc,), _ = A.t577_sections(_s577())
    m2 = secs[0]
    assert (Dd(m2["reference_total"]), Dd(m2["engine_valued"]), Dd(m2["difference"])) == (Dd("1.00"), Dd("1.36"),
                                                                                         Dd("-0.36"))
    assert nc["reference_total"] == "2.00" and nc["cells"] == ["H36", "H37"]
    lm = secs[1]
    assert Dd(lm["difference"]) == Dd("0.20") and lm["by_class"]["UNRESOLVED"] == "0.20"


def test_t577_adverse_count_x_length_as_m2_refused():
    with pytest.raises(E, match="count x length"):
        A.refuse_length_in_area([{"cell": "H36", "cell_class": "LENGTH_IN_AREA_COLUMN"}], "m2", "S")
    A.refuse_length_in_area([{"cell": "H36", "cell_class": "LENGTH_IN_AREA_COLUMN"}], "lm", "S")   # fine in lm


# ------------------------------------------------------------------------------- training villa --------------------
@pytest.fixture(scope="module")
def st():
    return B.build()


def sec6(st, sid):
    return [c for c in st["sections_v6"] if c["section_id"] == sid][0]


def test_villa_rebuild_equals_out(st):
    assert json.loads(B.JSON_OUT.read_text(encoding="utf-8")) == st
    assert B.MD_OUT.read_text(encoding="utf-8") == B.to_markdown(st)


def test_villa_v5_carried(st):
    st5 = B.v5_statement()
    B.check_v5_unchanged(st, st5)
    bad = copy.deepcopy(st)
    bad["sections_v5"][0]["engine_valued"] = "1"
    with pytest.raises(E):
        B.check_v5_unchanged(bad, st5)
    pads = [c for c in st["sections_v5"] if c["section_id"] == B.PADS][0]
    assert pads["cause_split"].startswith("not split (F-C-T579-1)") and pads["difference"] == "-0.628000"


def test_villa_every_new_section_closes(st):
    for c in st["sections_v6"]:
        tot = sum((Dd(r["delta"]) for r in c["rows"]), Dd(0))
        assert tot == Dd(c["reference_total"]) - Dd(c["engine_valued"]) == Dd(c["difference"])
        assert Dd(c["closure_residual"]) == 0 and c["difference_pct_of_reference"] is None
        assert all(r["unit"] == c["unit"] for r in c["rows"])


def test_villa_figures(st):
    lin = sec6(st, "T-571/lintel-count-implied")
    assert (lin["reference_total"], lin["engine_valued"], lin["engine_established_nr"]) == ("54", "60", 16)
    assert lin["beside_lm"]["implied"] == "84.9" and lin["beside_lm"]["engine_at_most"] == "91.5"
    room = sec6(st, "T-574/skirting-room")
    assert room["difference"] == "85.571408"
    assert room["beside"]["gross_vs_gross_outline_terms"]["difference_pct_of_reference"] == "2.37"
    assert Dd(room["beside"]["gross_vs_gross_outline_terms"]["difference"]) + \
        Dd(room["beside"]["deduction_terms_lm"]) == Dd("85.571408")
    stairs = sec6(st, "T-574/skirting-stairs")
    assert stairs["by_class"]["HELD"] == "17.009049" and Dd(room["engine_valued"]) + Dd(stairs["engine_valued"]) \
        == Dd("209.428592")
    m2, lm, nr = (sec6(st, f"T-577/marble-{u}") for u in ("m2", "lm", "nr"))
    assert (m2["reference_total"], m2["engine_valued"]) == ("5.1", "18.0382")
    assert (lm["difference"], nr["difference"]) == ("-35.13", "-56")
    b = st["beside_v6"][0]
    assert b["range_t"] == ["0.733792", "1.161932"] and b["valued_t"] == "0" and b["candidate_line"] is False
    assert b["expected_after_v8_rebar_rows"]["residual_after_bounded_held_t"] == ["1.294397", "2.127048"]
    ncs = {x["block_id"]: x for x in st["not_comparable"]}
    assert ncs["T-571/lintel-figure"]["reference_total"] == "NO_ROW"
    assert ncs["T-577/length-in-area-column"]["reference_total"] == "21.7"
    assert st["reports_pending"] == ["T-576", "T-578"] and st["released_quantities_changed"] == 0
