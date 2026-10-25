"""T-297 line-to-member basis rules on a hand-calculated NON-Alsenan villa (K297). Every expected value is worked by
hand below; nothing here comes from a client drawing.

Villa K297 (invented): beam B1, clear span 4.20 m face to face, schedule row 'B1 bottom 3 ø 16' printed; column C1 core
4 ø 14 from the footing top to GF FFL +1.00 on the printed chain formation <= -1.50 (a LIMIT), underlay 0.17 (printed
detail), footing H 0.60 (schedule): core >= 1.00 - (-1.50 + 0.17 + 0.60) = 1.73 m (upper OPEN); C1 links '6 ø 8 / m'
with no first-link offset printed (count HELD); B1 bottom-bar lap from a default 40 d factor (no lap printed).

Hand values (kg/m = d^2 / 162 as the check table of the fixture, unit mass is the fixture's choice):
  B1 bottom: 3 x 4.20 x 256 / 162 = 3 x 4.20 x 1.580247 = 19.911111 kg  (DRAWING_CONFIRMED)
  C1 core:   4 x 1.73 x 196 / 162 = 4 x 1.73 x 1.209877 =  8.372346 kg  (BOUND low; high OPEN)
  B1 lap:    3 x 40 x 0.016 x 1.580247 = 3 x 0.64 x 1.580247 = 3.034074 kg (CONVENTION, never measured)
  C1 links:  HELD blank
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t297"))
import t297_ledger as L  # noqa: E402

B1 = 3 * 4.20 * 256 / 162
C1 = 4 * 1.73 * 196 / 162
LAP = 3 * 40 * 0.016 * 256 / 162
DATUM = "GF FFL +1.00 - footing top (formation limit -1.50 + printed underlay 0.17 + schedule H 0.60)"


def rows():
    return [
        L.Row("L-B1-BOT", "BEAMS", ("BM-GF-B1",), "BOTTOM", "DRAWING_CONFIRMED", quantity_kg=B1,
              evidence="schedule row B1 bottom 3 ø 16; clear span 4.20 m"),
        L.Row("L-C1-CORE", "COLUMNS", ("COL-C1-FOUNDATION",), "MAIN_CORE", "BOUND", bound_low_kg=C1,
              datum=DATUM, datum_status="DRAWING_CONFIRMED", evidence="formation printed as a limit"),
        L.Row("L-B1-LAP", "BEAMS", ("BM-GF-B1",), "LAP", "CONVENTION", quantity_kg=LAP, lap_basis="DEFAULT_FACTOR",
              reason="40 d default factor, no lap printed"),
        L.Row("L-C1-LINKS", "COLUMNS", ("COL-C1-GF",), "LINKS", "HELD",
              reason="first-link offset not printed (Q-71: count HELD)"),
    ]


IDS = ["L-B1-BOT", "L-C1-CORE", "L-B1-LAP", "L-C1-LINKS"]


def test_hand_values():
    assert round(B1, 6) == 19.911111
    assert round(C1, 6) == 8.372346
    assert round(LAP, 6) == 3.034074


def test_normal_build_every_line_once_totals_per_status():
    s = L.build(rows(), IDS, named_totals={("BEAMS", "DRAWING_CONFIRMED"): 19.911111,
                                           ("COLUMNS", "BOUND"): 8.372346})
    t = s["totals"]
    assert t["BEAMS|DRAWING_CONFIRMED"]["kg"] == 19.911111 and t["BEAMS|DRAWING_CONFIRMED"]["t"] == 0.019911
    assert t["BEAMS|CONVENTION"]["kg"] == 3.034074
    assert t["COLUMNS|BOUND"]["low_kg"] == 8.372346 and t["COLUMNS|BOUND"]["high_kg"] is None
    assert t["COLUMNS|BOUND"]["high_open_lines"] == 1
    assert "kg" not in t["COLUMNS|HELD"] and t["COLUMNS|HELD"]["lines"] == 1
    assert s["residuals_kg"] == {"BEAMS|DRAWING_CONFIRMED": 0.0, "COLUMNS|BOUND": 0.0}


def test_normal_consumer_carries_bound_as_bound_and_t_once():
    c = {r["line_id"]: r for r in L.consumer(rows())}
    assert c["L-B1-BOT"]["quantity_t"] == 0.019911 and c["L-B1-BOT"]["bound_t"] is None
    assert c["L-C1-CORE"]["quantity_t"] is None
    assert c["L-C1-CORE"]["bound_t"] == {"low": 0.008372, "high": None, "datum": DATUM,
                                         "datum_status": "DRAWING_CONFIRMED"}
    assert c["L-C1-LINKS"]["quantity_t"] is None and c["L-C1-LINKS"]["held_reason"]


def test_adverse_bound_reported_as_measured_refused():
    r = rows()
    r[1] = L.Row("L-C1-CORE", "COLUMNS", ("COL-C1-FOUNDATION",), "MAIN_CORE", "BOUND", quantity_kg=C1,
                 bound_low_kg=C1, datum=DATUM, datum_status="DRAWING_CONFIRMED")
    with pytest.raises(L.LedgerError, match="never a quantity"):
        L.build(r, IDS)
    with pytest.raises(L.LedgerError, match="BOUND rows carry no summable"):
        L.total(rows()[1:2], ["BOUND"])


def test_adverse_bound_without_datum_refused():
    with pytest.raises(L.LedgerError, match="datum"):
        L.check_row(L.Row("x", "COLUMNS", ("C",), "MAIN_CORE", "BOUND", bound_low_kg=1.0))


def test_adverse_lap_from_default_factor_refused_as_measured():
    for st in ("DRAWING_CONFIRMED", "VERIFIED", "ASSUMED_OWNER_APPROVED"):
        with pytest.raises(L.LedgerError, match="default factor"):
            L.check_row(L.Row("x", "BEAMS", ("B1",), "LAP", st, quantity_kg=LAP, lap_basis="DEFAULT_FACTOR",
                              evidence="40 d"))
    with pytest.raises(L.LedgerError, match="CONVENTION datum"):
        L.check_row(L.Row("x", "BEAMS", ("B1",), "LAP", "BOUND", bound_low_kg=LAP, lap_basis="DEFAULT_FACTOR",
                          datum="40 d", datum_status="DRAWING_CONFIRMED"))


def test_adverse_held_as_zero_refused():
    with pytest.raises(L.LedgerError, match="never 0"):
        L.check_row(L.Row("x", "COLUMNS", ("C1",), "LINKS", "HELD", quantity_kg=0.0, reason="Q-71"))
    with pytest.raises(L.LedgerError, match="reason"):
        L.check_row(L.Row("x", "COLUMNS", ("C1",), "LINKS", "HELD"))


def test_adverse_kg_and_t_mixed_refused():
    with pytest.raises(L.LedgerError, match="kg internally"):
        L.check_row(L.Row("x", "BEAMS", ("B1",), "BOTTOM", "DRAWING_CONFIRMED", unit="t", quantity_kg=0.019911,
                          evidence="s"))
    r = rows()[0]
    r.unit = "t"
    with pytest.raises(L.LedgerError, match="unit t"):
        L.total([rows()[0], r], ["DRAWING_CONFIRMED"])
    with pytest.raises(L.LedgerError):
        L.kg_to_t("19.911111")


def test_adverse_statuses_never_summed_together():
    with pytest.raises(L.LedgerError, match="per basis status"):
        L.total(rows()[:3], ["DRAWING_CONFIRMED", "CONVENTION"])
    with pytest.raises(L.LedgerError, match="CONVENTION row in a DRAWING_CONFIRMED"):
        L.total([rows()[0], rows()[2]], ["DRAWING_CONFIRMED"])


def test_adverse_every_line_exactly_once():
    with pytest.raises(L.LedgerError, match="tied twice"):
        L.build(rows() + [rows()[0]], IDS)
    with pytest.raises(L.LedgerError, match="missing"):
        L.build(rows()[:3], IDS)
    with pytest.raises(L.LedgerError, match="extra"):
        L.build(rows(), IDS[:3])


def test_adverse_residual_against_named_total_refused():
    with pytest.raises(L.LedgerError, match="residual"):
        L.build(rows(), IDS, named_totals={("BEAMS", "DRAWING_CONFIRMED"): 19.92})


def test_adverse_measured_without_evidence_and_no_member_refused():
    with pytest.raises(L.LedgerError, match="evidence"):
        L.check_row(L.Row("x", "BEAMS", ("B1",), "BOTTOM", "DRAWING_CONFIRMED", quantity_kg=1.0))
    with pytest.raises(L.LedgerError, match="member"):
        L.check_row(L.Row("x", "BEAMS", (), "BOTTOM", "CONVENTION", quantity_kg=1.0))


def test_adverse_lap_read_from_another_categorys_note_never_measured():
    """K297 note N4 prints a starter-bar development length 40 d .. 70 d; read as a beam lap it is a NOTE_READING:
    BOUND with a HELD datum at most, never DRAWING_CONFIRMED (3 x 0.64 .. 3 x 1.12 m of ø 16)"""
    lo, hi = 3 * 0.64 * 256 / 162, 3 * 1.12 * 256 / 162
    ok = L.check_row(L.Row("x", "BEAMS", ("B1",), "LAP", "BOUND", bound_low_kg=lo, bound_high_kg=hi,
                           lap_basis="NOTE_READING", datum="note N4 40 d .. 70 d", datum_status="HELD"))
    assert round(ok.bound_low_kg, 6) == 3.034074 and round(ok.bound_high_kg, 6) == 5.30963
    with pytest.raises(L.LedgerError, match="never DRAWING_CONFIRMED"):
        L.check_row(L.Row("x", "BEAMS", ("B1",), "LAP", "DRAWING_CONFIRMED", quantity_kg=lo,
                          lap_basis="NOTE_READING", evidence="note N4"))
    with pytest.raises(L.LedgerError, match="HELD datum"):
        L.check_row(L.Row("x", "BEAMS", ("B1",), "LAP", "BOUND", bound_low_kg=lo, bound_high_kg=hi,
                          lap_basis="NOTE_READING", datum="note N4", datum_status="DRAWING_CONFIRMED"))


def test_minimum_cover_as_exact_length_is_a_convention_not_drawing_confirmed():
    """K297 footing FA 2.00 x 2.00, '12 | 12' printed, general note 'cover not less than 5 cm': the straight bar
    2.00 - 2 x 0.05 = 1.90 m is the longest straight bar the minimum allows, and the drawn hooks are not derived, so
    12 x 1.90 x 0.888889 = 20.266667 kg is neither a lower nor an upper bound of the installed bar: CONVENTION"""
    sys.path.insert(0, str(ROOT / "research" / "agents_t297"))
    import t297_alsenan as A
    line = {"line_id": "L-FA", "physical_element": "FOOTINGS", "element_id": "FTG:FA:BOTTOM_LONG",
            "evidence_state": "SOURCE_DERIVED", "measured_net": 12 * 1.90 * 144 / 162,
            "formula": "n x (side 2000 - 2 x 50 mm) x kg/m",
            "inputs": {"policy": "FOOTING_REBAR_POPULATION_V1", "component": "BOTTOM_LONG", "printed": "12 | 12",
                       "cover": "MINIMUM 50 mm (general note: not less than 5 cm)"}}
    r = A.classify(line)
    assert r.status == "CONVENTION" and "MIN_COVER_AS_EXACT" in r.flags and round(r.quantity_kg, 6) == 20.266667
    line["evidence_state"], line["measured_net"] = "BLOCKED_RFI", None
    r = A.classify(line)
    assert r.status == "HELD" and r.quantity_kg is None


def test_zero_lower_bound_with_open_top_is_held_not_a_bound():
    sys.path.insert(0, str(ROOT / "research" / "agents_t297"))
    import t297_alsenan as A
    line = {"line_id": "L-SB", "physical_element": "BEAMS", "element_id": "HL:BEAM_STEEL:B9:SIDE",
            "evidence_state": "BLOCKED_RFI", "measured_net": None, "formula": "held",
            "inputs": {"policy": "BEAM_STEEL_HAND_LEDGER_V1", "ledger": "villa-k297.csv", "element": "B9",
                       "component": "side bars", "ledger_state": "HELD_LOWER_BOUND", "lower_bound_kg": 0.0,
                       "reasons": ["two marks on one span"]}}
    r = A.classify(line)
    assert r.status == "HELD" and r.bound_low_kg is None and "LOWER_BOUND_ZERO_OPEN" in r.flags
    line["inputs"]["lower_bound_kg"] = 4.5
    r = A.classify(line)
    assert r.status == "BOUND" and r.bound_low_kg == 4.5 and r.bound_high_kg is None and r.datum
