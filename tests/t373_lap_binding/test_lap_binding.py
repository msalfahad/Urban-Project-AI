"""T-373: rule R-T373-1 (a lap / development length is valued only from a printed authority naming the bar population,
or an answered owner rule) and the line binder, on a hand-calculated villa that is NOT Alsenan (villa V373).

Villa V373 (synthetic, hand kg from the Urban bar table engine/bbs_steel.py: d16 1.578, d14 1.208, d12 0.888 kg/m):
  its general notes print  N-ST 'starter bars lap 50 d'  and  N-COL 'column bars lap 45 d at every floor'.
  1. footing starters 8 ø16 at N-ST: 8 x 50 x 0.016 = 6.400 m x 1.578 = 10.0992 kg            -> KEEP
  2. column storey lap 4 ø12 at N-COL: 4 x 45 x 0.012 = 2.160 m x 0.888 = 1.91808 kg           -> KEEP
  3. beam bottom bar ends 4 ø14 x 2 ends booked at the STARTER note 40 d .. 70 d:
     8 x 0.56 .. 8 x 0.98 = 4.48 .. 7.84 m x 1.208 = 5.41184 .. 9.47072 kg                     -> HELD, BLANK
"""

import importlib.util
import json
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("t373", ROOT / "research/agents_t373/t373_lap_binding.py")
T = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(T)

KG = {16: Decimal("1.578"), 14: Decimal("1.208"), 12: Decimal("0.888")}
V373 = {
    "N-ST": {"ref": "V373 note 4 'starter bars lap 50 d'", "names": {"STARTER"}, "value": "50 d", "category": "STARTER_BARS"},
    "N-COL": {"ref": "V373 note 5 'column bars lap 45 d'", "names": {"COLUMN_MAIN"}, "value": "45 d", "category": "LAP_SPLICE"},
}


def kg(n, mult_d, d):
    return Decimal(n) * Decimal(mult_d) * Decimal(d) / 1000 * KG[d]


def test_hand_fixture_three_populations():
    st = T.lap_authority("STARTER", ["N-ST"], V373)
    col = T.lap_authority("COLUMN_MAIN", ["N-COL"], V373)
    beam = T.lap_authority("BEAM_MAIN", ["N-ST"], V373)
    assert st[:2] == ("PRINTED", "KEEP") and col[:2] == ("PRINTED", "KEEP")
    assert beam[:2] == ("PRINTED_FOR_OTHER_GROUP", "HELD")
    assert kg(8, 50, 16) == Decimal("10.0992")
    assert kg(4, 45, 12) == Decimal("1.91808")
    lo, hi = kg(8, 40, 14), kg(8, 70, 14)
    assert (lo, hi) == (Decimal("5.41184"), Decimal("9.47072"))
    assert T.value_line(st[1], kg(8, 50, 16), kg(8, 50, 16)) == (Decimal("10.0992"), Decimal("10.0992"))
    assert T.value_line(beam[1], lo, hi) == (None, None)            # BLANK, never 0
    valued_before = kg(8, 50, 16) + kg(4, 45, 12) + lo, kg(8, 50, 16) + kg(4, 45, 12) + hi
    valued_after = kg(8, 50, 16) + kg(4, 45, 12)
    assert valued_before == (Decimal("17.42912"), Decimal("21.48800"))
    assert valued_after == Decimal("12.01728")


def test_normal_starter_at_note9_kept():
    assert T.lap_authority("STARTER", ["P8-NOTE9"])[:2] == ("PRINTED", "KEEP")


def test_adverse_beam_end_at_note9_refused_held():
    cls, st, why = T.lap_authority("BEAM_MAIN", ["P8-NOTE9"])
    assert (cls, st) == ("NOTE9_OUTSIDE_GROUP", "HELD") and "BLANK" in why
    for g in ("COLUMN_MAIN", "GROUND_BEAM_MAIN", "SLAB_END"):
        assert T.lap_authority(g, ["P8-NOTE9"])[1] == "HELD"


def test_temperature_note_does_not_cover_column_lap():
    assert T.lap_authority("COLUMN_MAIN", ["P15-NOTE1"])[:2] == ("PRINTED_FOR_OTHER_GROUP", "HELD")
    assert T.lap_authority("TEMPERATURE", ["P15-NOTE1"])[:2] == ("PRINTED", "KEEP")


def test_no_authority_held_and_owner_rule_kept():
    assert T.lap_authority("GROUND_BEAM_MAIN", [])[:2] == ("NONE", "HELD")
    assert T.lap_authority("GROUND_BEAM_MAIN", [], owner_rules={"GROUND_BEAM_MAIN"})[:2] == ("OWNER_RULE", "KEEP")


def test_adverse_unknown_authority_and_missing_group_refused():
    with pytest.raises(T.BindingError):
        T.lap_authority("BEAM_MAIN", ["code default 50 d"])
    with pytest.raises(T.BindingError):
        T.lap_authority("", ["P8-NOTE9"])
    with pytest.raises(T.BindingError):
        T.value_line("PROMOTE", 1, 2)


def _line(lid, eid, state, lo=None, hi=None, formula="", comp="", basis=None):
    br = {"low": lo, "high": hi, "basis": basis} if lo is not None else None
    return {"line_id": lid, "item_code": "STR.REBAR", "trade": "REINFORCEMENT", "evidence_state": state,
            "measured_net": None, "bounded_range": br, "subtrade": "x", "location": {"element_id": eid, "floor": "GF"},
            "calculation": {"formula": formula, "inputs": {"component": comp}}}


def _pop(l):
    e = l["element_id"]
    return {"B": "BEAM-SIMPLE-MAIN", "N": "NECK-STARTER-SHALLOW|NECK-STARTER-DEEP", "S": "SLAB-BOTTOM-MAIN",
            "P": "OUT:POOL", "C": "COL-MAIN"}[e[0]]


def test_binder_on_v373_lines_normal_and_adverse():
    lines = [
        _line("L1", "B:BM1:BOTTOM_ENDS_NOTE_9_40D_70D", "BOUNDED_EXPOSURE", 5.41184, 9.47072,
              "held: development at bar ends; note 9 ...", "bottom ends (note 9, 40d..70d)"),
        _line("L2", "N:NECK:COL:F1:MAIN:D16", "BLOCKED_RFI", formula="count x (neck height + lap)"),
        _line("L3", "S:SLAB:GF-1:DEVELOPMENT_ANCHORAGE:X#SLAB_BAR_ENDS:VALUED", "BOUNDED_EXPOSURE", 1.944, 2.074,
              "valued ends: p.15 straight part w - 0.040 m"),
        _line("L4", "S:SLAB:GF-2:DEVELOPMENT_ANCHORAGE:Y", "BLOCKED_RFI",
              formula="HELD remainder (blank in the BOQ, never 0); note-9 basis refused"),
        _line("L5", "P:POOL:WALL", "BOUNDED_EXPOSURE", 1, 2, "note 9 40 d .. 70 d"),
        _line("L6", "C:COL1:LAP_AT_STOREY_BOTTOM_READING_P", "BOUNDED_EXPOSURE", 8.091, 14.159, "held: lap zone",
              "LAP at storey bottom", basis="40 d .. 70 d (p.8 note 9, zone not printed)"),
    ]
    rows = {r["line_id"]: r for r in T.bind_candidate(lines, _pop)}
    assert rows["L1"]["proposed"] == "HELD" and rows["L1"]["kg_low_after"] == "" and rows["L1"]["kg_low_now"] == "5.41184"
    assert rows["L2"]["authority_class"] == "NOT_BOOKED"            # no figure: nothing to downgrade
    assert rows["L3"]["authority_class"] == "PRINTED" and rows["L3"]["kg_high_after"] == "2.074"
    assert rows["L4"]["authority_class"] == "NOT_BOOKED"             # already re-booked (T-318): not downgraded twice
    assert rows["L5"]["proposed"] == "LISTED_ONLY"
    assert rows["L6"]["kind"] == "COLUMN_STOREY_LAP" and rows["L6"]["proposed"] == "HELD"
    with pytest.raises(T.BindingError):
        T.bind_candidate(lines + [lines[0]], _pop)                    # one line bound twice
    tonne = dict(lines[0], line_id="L7", unit="t")
    with pytest.raises(T.BindingError):
        T.bind_candidate([tonne], _pop)                               # units: a tonne figure is refused, never mixed
    tot = {(t["group"], t["proposed"]): t for t in T.totals(list(rows.values()))}
    assert tot[("beam ends", "HELD")]["held_blank"] == 1 and tot[("beam ends", "HELD")]["high_after"] == "BLANK"


def test_committed_alsenan_binding_consistent():
    """the committed Alsenan table: no HELD row carries an after-figure, no KEEP row on note 9 outside its group,
    and the summary totals equal the CSV."""
    import csv
    p = ROOT / "research/agents_t373/T373_LAP_BINDING.csv"
    s = json.loads((ROOT / "research/agents_t373/T373_SUMMARY.json").read_text(encoding="utf-8"))
    rows = list(csv.DictReader(p.open(encoding="utf-8")))
    assert len(rows) == s["bound_rows"]
    for r in rows:
        if r["proposed"] == "HELD":
            assert r["kg_low_after"] == "" and r["kg_high_after"] == "" and r["kg_high_now"] not in ("", "0")
        if r["authority_class"] == "NOTE9_OUTSIDE_GROUP" and r["population"] != "OUT_OF_ROUTE(T-359)":
            assert r["proposed"] == "HELD"
    assert len({r["line_id"] for r in rows}) == len(rows)
    held = sum(Decimal(r["kg_high_now"]) for r in rows if r["proposed"] == "HELD")
    assert held == sum(Decimal(t["high_now"]) for t in s["totals"] if t["proposed"] == "HELD")


def test_projection_from_committed_extract_equals_the_v3027_record():
    """without private data: the merged V3.0.16 extract + the merged T-318 re-booking gives the same 351 HELD lines,
    the same kg on each and the same 59 drawn parts as the binding of the reproduced V3.0.27 (committed CSV)."""
    import csv
    sys.path.insert(0, str(ROOT / "research" / "agents_t366"))
    sys.path.insert(0, str(ROOT / "research" / "agents_t318"))
    import t366_alsenan_input as B
    import t318_inputs as L27
    d = json.loads((ROOT / "research/agents_t297/CANDIDATE_V3016_REBAR_LINES.json").read_text(encoding="utf-8"))
    pid = d["project"] if isinstance(d["project"], str) else d["project"]["project_id"]
    proj = T.rebook_t318(T.bind_candidate(d["lines"], B.bind), L27.build(pid)["lines"])
    rec = list(csv.DictReader((ROOT / "research/agents_t373/T373_LAP_BINDING.csv").open(encoding="utf-8")))
    held = lambda rows: {(r["line_id"], r["kg_low_now"], r["kg_high_now"]) for r in rows if r["proposed"] == "HELD"}
    parts = lambda rows: sorted((r["element_id"], r["kg_low_now"], r["kg_high_now"]) for r in rows
                                if r["kind"] == "SLAB_DEV_DRAWN_PART")
    assert held(proj) == held(rec) and len(held(rec)) == 351
    assert parts(proj) == parts(rec) and len(parts(rec)) == 59
    assert len(proj) == len(rec) == 584
