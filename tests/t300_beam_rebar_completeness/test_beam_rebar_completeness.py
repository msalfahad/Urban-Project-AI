"""T-300 beam reinforcement completeness safeguard: hand fixture (not Alsenan), normal and adverse cases."""
from __future__ import annotations

import copy
import csv
import json
import re
from pathlib import Path

import pytest

from engine.source import beam_rebar_completeness as BRC
from tests.t300_beam_rebar_completeness import fixture as FX

ROOT = Path(__file__).resolve().parents[2]


def run(*, evidence=(FX.NOTE,), printed_inputs=None, **kw):
    attrs, texts, segs = FX.build(**kw)
    rows = FX.rows_for(attrs)
    res = BRC.evaluate(texts, attrs, segs, rows, evidence=list(evidence), printed_inputs=printed_inputs,
                       unit_mass=FX.UNIT_MASS)
    return res, rows


def beam(res, mark):
    (b,) = [b for b in res["beams"] if b["mark"] == mark]
    return b


def comp(b, kind, span=None):
    (c,) = [c for c in b["components"] if c["kind"] == kind and c["span"] == span]
    return c


# ------------------------------------------------------------------ normal cases
def test_simple_table_side_bars_nested_links_and_top():
    res, _ = run()
    b41, b42, b43, b44 = (beam(res, m) for m in ("B41", "B42", "B43", "B44"))
    # B41 25 x 50: note 7 does not apply (0.50 <= 0.60), table prints symbols elsewhere, top = TOP attribute
    assert [comp(b41, k)["status"] for k in BRC.KINDS] == ["NOT_REQUIRED"] * 3
    assert b41["completeness"] == "COMPLETE" and b41["incomplete_because"] == []
    # B42 30 x 80: remark 2Ø14/25cm read inline; 3-loop symbol = nested links, 6 legs; both HELD, kg blank
    s = comp(b42, "SIDE_BARS")
    assert s["status"] == "DETECTED" and s["reading"]["count"] == 2 and s["reading"]["dia_mm"] == 14
    assert s["reading"]["spacing"] == {"value": 25.0, "unit": "cm", "printed": "INLINE"}
    assert s["quantity_kg"] is None and s["quantity_state"] == "HELD" and s["kg_blank_reason"] == "NO_PRINTED_INPUTS"
    n = comp(b42, "NESTED_LINKS")
    assert n["status"] == "DETECTED" and n["reading"]["loops"] == 3 and n["reading"]["legs"] == 6
    assert n["quantity_kg"] is None and b42["completeness"] == "INCOMPLETE"
    # B43 30 x 90: deeper than the note's 60 cm and no remark -> UNRESOLVED, HELD, blank (never 0)
    s43 = comp(b43, "SIDE_BARS")
    assert s43["status"] == "UNRESOLVED" and s43["quantity_kg"] is None and s43["quantity_state"] == "HELD"
    assert s43["basis"].startswith("GENERAL_NOTE_REQUIRES_SIDE_BARS_NOT_PRINTED")
    assert comp(b43, "NESTED_LINKS")["basis"].startswith("NOT_PRINTED: the table prints a link symbol on 2 row")
    # B44: single loop symbol -> not nested
    assert comp(b44, "NESTED_LINKS")["basis"] == "LINK_SYMBOL_SINGLE_LOOP"
    assert comp(b44, "SIDE_BARS")["reading"]["spacing"]["value"] == 30.0
    assert all(b["association"]["rule"] == "ROW_GRID_LINES" for b in res["beams"])


def test_continuous_table_corner_bars_and_middle_reint():
    res, _ = run()
    cb21 = beam(res, "CB21")
    c1, c2 = comp(cb21, "TOP_CORNER", 1), comp(cb21, "TOP_CORNER", 2)
    assert (c1["status"], c1["reading"]) == ("DETECTED", {"count": 2, "dia_mm": 12})      # split '2' 'Ø' '12'
    assert (c2["status"], c2["reading"]) == ("DETECTED", {"count": 3, "dia_mm": 16})
    assert c1["evidence"][0]["ids"] == ["C1a", "C1b", "C1c"]
    s = comp(cb21, "SIDE_BARS")
    assert s["status"] == "DETECTED" and s["reading"]["header"] == "MIDDLE"
    assert s["reading"]["spacing"]["value"] == 20.0 and s["reading"]["spacing"]["printed"].startswith("SEPARATE")
    assert "UNRESOLVED" in s["reading"]["notation_meaning"]
    # the glyph lying on the filled MID slot is that slot's own glyph: never a new group, never a flag
    assert cb21["flags"] == []
    # no link symbol anywhere in the table and no link detail -> UNRESOLVED, the beam is never COMPLETE
    assert comp(cb21, "NESTED_LINKS")["status"] == "UNRESOLVED" and cb21["completeness"] == "INCOMPLETE"


def test_kg_only_with_every_printed_input_and_complete_beam():
    inputs = {("CB21", "TOP_CORNER", 1): {"count": 2, "dia_mm": 12, "length_m": 3.10, "source": "fixture detail D1"},
              ("CB21", "TOP_CORNER", 2): {"count": 3, "dia_mm": 16, "length_m": 3.40, "source": "fixture detail D1"},
              ("CB21", "SIDE_BARS", None): {"count": 4, "dia_mm": 12, "length_m": 8.50, "count_basis": "TOTAL",
                                           "source": "fixture designer reply R3"}}
    link = {"kind": "LINK_DETAIL", "family": "CONTINUOUS_BEAM", "loops": 1, "source": "fixture section S-S"}
    res, _ = run(evidence=(FX.NOTE, link), printed_inputs=inputs)
    cb21 = beam(res, "CB21")
    # hand: 2 x 3.10 x 144/162 = 5.511111; 3 x 3.40 x 256/162 = 16.118519; 4 x 8.50 x 144/162 = 30.222222 kg
    assert comp(cb21, "TOP_CORNER", 1)["quantity_kg"] == pytest.approx(2 * 3.10 * 144 / 162, abs=1e-9)
    assert comp(cb21, "TOP_CORNER", 1)["quantity_kg"] == pytest.approx(5.511111, abs=1e-6)
    assert comp(cb21, "TOP_CORNER", 2)["quantity_kg"] == pytest.approx(16.118519, abs=1e-6)
    assert comp(cb21, "SIDE_BARS")["quantity_kg"] == pytest.approx(30.222222, abs=1e-6)
    assert comp(cb21, "NESTED_LINKS")["status"] == "NOT_REQUIRED"
    assert cb21["completeness"] == "COMPLETE"
    assert res["summary"]["kg_measured"] == pytest.approx(5.511111 + 16.118519 + 30.222222, abs=1e-5)


def test_missing_inputs_keep_kg_blank():
    inputs = {("CB21", "TOP_CORNER", 1): {"count": 2, "dia_mm": 12, "source": "x"},           # no length
              ("CB21", "SIDE_BARS", None): {"count": 2, "dia_mm": 12, "length_m": 8.5, "source": "x"}}  # no basis
    res, _ = run(printed_inputs=inputs)
    cb21 = beam(res, "CB21")
    assert comp(cb21, "TOP_CORNER", 1)["quantity_kg"] is None
    assert comp(cb21, "TOP_CORNER", 1)["kg_blank_reason"] == "MISSING_INPUT:length_m"
    assert comp(cb21, "SIDE_BARS")["kg_blank_reason"] == "MISSING_INPUT:count_basis"
    assert res["summary"]["kg_measured"] == 0


# ------------------------------------------------------------------ adverse cases
def test_text_between_two_beams_is_never_assigned():
    res, _ = run(boundary_text=True)
    amb = [u for u in res["unassigned"] if u.get("ids") == ["RX"]]
    assert len(amb) == 1 and amb[0]["state"] == "AMBIGUOUS_BOUNDARY"
    assert comp(beam(res, "B42"), "SIDE_BARS")["reading"]["dia_mm"] == 14                 # its own remark only
    assert comp(beam(res, "B43"), "SIDE_BARS")["status"] == "UNRESOLVED"                  # not given RX


def test_empty_slot_text_and_unclassified_callout_are_flagged():
    res, _ = run()
    cb22 = beam(res, "CB22")
    codes = sorted(f["code"] for f in cb22["flags"])
    assert codes == ["EMPTY_SLOT_TEXT_VALUE", "UNCLASSIFIED_CALLOUT"]
    assert [f["text"] for f in cb22["flags"] if f["code"] == "EMPTY_SLOT_TEXT_VALUE"] == ["4Ø16"]
    assert comp(cb22, "TOP_CORNER", 1)["status"] == "DETECTED"
    assert comp(cb22, "TOP_CORNER", 2)["status"] == "UNRESOLVED"
    assert comp(cb22, "SIDE_BARS")["status"] == "NOT_REQUIRED"                            # 0.50 m, note 7
    assert cb22["completeness"] == "INCOMPLETE"


def test_missing_group_reported_as_zero_is_refused():
    res, _ = run()
    bad = copy.deepcopy(res)
    c = comp(beam(bad, "B43"), "SIDE_BARS")
    c["quantity_kg"] = 0.0
    with pytest.raises(BRC.SafeguardError, match="never 0"):
        BRC.validate(bad)
    bad2 = copy.deepcopy(res)
    c2 = comp(beam(bad2, "B42"), "SIDE_BARS")                       # DETECTED, inputs absent
    c2["quantity_kg"] = 12.0
    with pytest.raises(BRC.SafeguardError, match="every printed input"):
        BRC.validate(bad2)
    assert BRC._kg({"count": 0, "dia_mm": 12, "length_m": 3, "source": "x"}, FX.UNIT_MASS) == (None,
                                                                                              "NON_POSITIVE_INPUT")


def test_measured_group_altered_is_refused_and_inputs_untouched():
    attrs, texts, segs = FX.build()
    rows = FX.rows_for(attrs)
    before = BRC.measured_digest(rows)
    snapshot = json.dumps(rows, sort_keys=True, default=str)
    BRC.evaluate(texts, attrs, segs, rows, evidence=[FX.NOTE], unit_mass=FX.UNIT_MASS)
    assert json.dumps(rows, sort_keys=True, default=str) == snapshot
    altered = copy.deepcopy(rows)
    altered[0]["bars"][0]["count"] += 1
    with pytest.raises(BRC.SafeguardError, match="measured bar groups changed"):
        BRC.assert_measured_unchanged(before, altered)


def test_beam_marked_complete_with_held_component_is_refused():
    res, _ = run()
    bad = copy.deepcopy(res)
    beam(bad, "B42")["completeness"] = "COMPLETE"
    with pytest.raises(BRC.SafeguardError, match="COMPLETE with a HELD"):
        BRC.validate(bad)
    bad2 = copy.deepcopy(res)
    beam(bad2, "CB22")["completeness"] = "COMPLETE"                                       # flags open
    with pytest.raises(BRC.SafeguardError):
        BRC.validate(bad2)


def test_translation_and_units_do_not_change_the_reading():
    base, _ = run()
    for kw in ({"shift": (1.0e6, -2.5e5)}, {"scale": 0.001}, {"scale": 0.001, "shift": (-40.0, 12.5)}):
        other, _ = run(**kw)
        key = lambda r: [(b["mark"], [(c["kind"], c["span"], c["status"], c["basis"]) for c in b["components"]],  # noqa
                          sorted(f["code"] for f in b["flags"]), b["completeness"]) for b in r["beams"]]
        assert key(other) == key(base), kw


def test_single_row_table_and_evidence_without_source():
    attrs, texts, segs = FX.build()
    only = [a for a in attrs if a["owner"] == "42"]
    rows = FX.rows_for(only)
    segs1 = [s for s in segs if not s["id"].startswith("H")]                                # no grid lines either
    res = BRC.evaluate(texts, only, segs1, rows, evidence=[FX.NOTE], unit_mass=FX.UNIT_MASS)
    b = beam(res, "B42")
    assert comp(b, "SIDE_BARS")["status"] == "UNRESOLVED" and b["completeness"] == "INCOMPLETE"
    assert any(u["state"] == "NO_PITCH_SINGLE_ROW_TABLE" for u in res["unassigned"])
    with pytest.raises(BRC.SafeguardError, match="without a source"):
        BRC.evaluate(texts, attrs, segs, FX.rows_for(attrs), evidence=[{"kind": "SIDE_BAR_NOTE", "depth_gt_m": 0.6}])


def test_no_note_means_unresolved_not_zero():
    res, _ = run(evidence=())
    s = comp(beam(res, "B41"), "SIDE_BARS")
    assert s["status"] == "UNRESOLVED" and s["basis"] == "NO_REMARK_AND_NO_GOVERNING_NOTE" and s["quantity_kg"] is None


def test_module_is_generic_and_unwired():
    src = (ROOT / "engine/source/beam_rebar_completeness.py").read_text(encoding="utf-8")
    for word in ("Alsenan", "ST7757", "CB11", "B17", "S-TEXT", "SH09"):
        assert word not in src, word
    for p in list((ROOT / "engine").rglob("*.py")) + list((ROOT / "tools").rglob("*.py")):
        if p.name != "beam_rebar_completeness.py":
            assert "beam_rebar_completeness" not in p.read_text(encoding="utf-8", errors="ignore"), p
    assert BRC.policy_record()["wired"] is False


def test_alsenan_dry_run_record():
    """The committed dry run (research/agents_t300): route G byte-identical; the flags agree with the merged T-149."""
    d = json.loads((ROOT / "research/agents_t300/T300_ALSENAN_SUMMARY.json").read_text(encoding="utf-8"))
    assert d["route_g_byte_identical"] is True
    assert d["route_g_items_sha256_before"] == d["route_g_items_sha256_after"]
    s = d["summary"]
    assert (s["beams"], s["SIDE_BARS.DETECTED"], s["NESTED_LINKS.DETECTED"], s["TOP_CORNER.DETECTED"]) == (43, 30, 9, 28)
    assert s["kg_measured"] == 0
    rows = list(csv.DictReader(open(ROOT / "research/agents_t300/T300_ALSENAN_FLAGS.csv", encoding="utf-8")))
    assert not [r for r in rows if r["agrees_with_t149"] == "NO"]
    assert all(r["quantity_kg"] == "" for r in rows)
    held = [r for r in rows if r["status"] in ("UNRESOLVED", "FLAGGED")]
    assert all(r["quantity_state"] == "HELD" for r in held)
    assert all(not re.search(r"\d{4,}\.\d", r["evidence_ids"]) for r in rows)              # handles only, no coords
