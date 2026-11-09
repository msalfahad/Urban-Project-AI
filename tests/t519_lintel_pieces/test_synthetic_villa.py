"""T-519 R-T519-1 on a synthetic villa X (not the training villa): lintel system per opening, then pieces.

Villa X prints a lintel schedule for BLACK block walls only (note 'lintels in black block walls'), bands L1 0-100 cm,
L2 101-200, L3 201-300, L4 301-500, detail 'MIN 30 cm' (b 0.30). White AAC walls are outside its scope -> owner precast
rule UPC-LINTEL-001 (company minimum bearing 0.15 m, stock 1.20 / 1.50 / 2.50 / 3.00 / 4.00 m).

NORMAL (hand):
  P1 white w 0.85: 0.85 + 0.30 = 1.15 -> 1.20 m; piers 1.00 / 1.00 >= 0.15 and 2.00 >= 1.20 - 0.85 -> PRODUCED
  P2 white w 1.10: 1.40 -> 1.50 m PRODUCED
  P3 white w 2.00: 2.30 -> 2.50 m PRODUCED
  P4 white w 2.60: 2.90 -> 3.00 m PRODUCED
  P5 white w 3.50: 3.80 -> 4.00 m PRODUCED (overhang 0.50, piers 2.00)
  B1 black w 1.20 (L2): ends 0.50 / 0.45 >= 0.30 -> RC PRODUCED, cast to length L in [1.80, 2.15] m, no stock length
  -> every stock length hit once, 5 precast + 1 RC, label COMPLETE.
ADVERSE (hand):
  A1 white w 4.10: 4.40 > 4.00 -> FLAGGED, no piece (never forced, never 0)
  A2 white w 1.10, START pier 0.10 < 0.15 -> FLAGGED_DEFICIT, piece 1.50 not produced, bearing never defaulted
  A3 white w 1.10, END not measured -> HELD
  A4 white w 1.10, piers 0.16 / 0.16 (each >= 0.15) but 0.32 < 1.50 - 1.10 = 0.40 -> DOES_NOT_FIT
  A5 black w 1.005 (100.5 cm, between L1 and L2) -> system HELD (SCHEDULE_SILENT), never L1 or L2
  B2 black w 0.90: START 0.20 to a column < 0.30 -> RC count HELD, hard ceiling 0.90 + 0.20 + 1.00 = 2.10 m
  H1 white w 1.00, decision HELD -> HELD by name, in no count
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t519"))

import t519_lintel_pieces as P  # noqa: E402

SCHED = {"source": "villa X lintel schedule", "scope": ("BLACK",), "bearing_m": 0.30,
         "bearing_source": "villa X lintel detail 'MIN 30 cm'",
         "bands": [{"row": "L1", "lo_cm": 0, "hi_cm": 100, "d_cm": 20}, {"row": "L2", "lo_cm": 101, "hi_cm": 200,
                                                                        "d_cm": 20},
                   {"row": "L3", "lo_cm": 201, "hi_cm": 300, "d_cm": 30}, {"row": "L4", "lo_cm": 301, "hi_cm": 500,
                                                                          "d_cm": 40}]}


def e(side, a, stopper="END_OF_MASONRY", shared=None):
    return {"side": side, "available_m": a, "stopper": stopper, "shared_with": shared}


def op(oid, w, block="WHITE", s=1.0, t=1.0, decision="REQUIRED", **kw):
    return dict(opening_id=oid, floor="GF", block_type=block, width_m=w, decision=decision,
                ends=[e("START", s), e("END", t)], **kw)


NORMAL = [op("P1", 0.85), op("P2", 1.10), op("P3", 2.00), op("P4", 2.60), op("P5", 3.50),
          op("B1", 1.20, "BLACK", 0.50, 0.45)]


def by(doc):
    return {r["opening_id"]: r for r in doc["rows"]}


def test_normal_every_stock_length_once_and_rc():
    doc = P.census(NORMAL, SCHED)
    b = by(doc)
    pieces = {k: b[k]["precast"]["piece_m"] for k in ("P1", "P2", "P3", "P4", "P5")}
    assert pieces == {"P1": 1.2, "P2": 1.5, "P3": 2.5, "P4": 3.0, "P5": 4.0}
    assert all(b[k]["system"] == P.OWNER_PRECAST and b[k]["state"] == P.PRODUCED for k in pieces)
    assert b["P1"]["precast"]["bearing_m"] == 0.15 and b["P1"]["precast"]["required_m"] == pytest.approx(1.15)
    s = doc["summary"]
    assert {k: v["produced_nr"] for k, v in s["precast_governing_by_length"].items()} == \
        {"1.20": 1, "1.50": 1, "2.50": 1, "3.00": 1, "4.00": 1}
    assert b["B1"]["system"] == P.PROJECT_RC and b["B1"]["schedule_row"] == "L2" and b["B1"]["state"] == P.PRODUCED
    assert (b["B1"]["rc"]["length_lo_m"], b["B1"]["rc"]["length_hi_m"]) == (1.8, 2.15)
    assert b["B1"]["stock_length"].startswith("NOT_APPLICABLE")
    assert b["B1"]["precast_beside"]["state"] == "NOT_APPLICABLE"     # black wall: no atab (Q-60)
    assert s["system_count"] == {"PROJECT_RC": 1, "OWNER_PRECAST": 5, "HELD": 0}
    assert s["rc_produced_nr"] == 1 and s["label"] == "COMPLETE"


def test_mirror_swapping_the_ends_changes_nothing():
    a = by(P.census([op("B1", 1.20, "BLACK", 0.50, 0.45)], SCHED))["B1"]["rc"]
    m = by(P.census([op("B1", 1.20, "BLACK", 0.45, 0.50)], SCHED))["B1"]["rc"]
    assert (a["length_lo_m"], a["length_hi_m"]) == (m["length_lo_m"], m["length_hi_m"])
    x = by(P.census([op("A2", 1.10, s=0.10)], SCHED))["A2"]
    y = by(P.census([op("A2", 1.10, t=0.10)], SCHED))["A2"]
    assert x["state"] == y["state"] == P.FLAGGED


def test_adverse_cases():
    recs = NORMAL + [op("A1", 4.10), op("A2", 1.10, s=0.10), op("A3", 1.10, t=None), op("A4", 1.10, s=0.16, t=0.16),
                     op("A5", 1.005, "BLACK"), op("B2", 0.90, "BLACK", s=0.20), op("H1", 1.00, decision="HELD")]
    recs[-2]["ends"][0]["stopper"] = "COLUMN"
    doc = P.census(recs, SCHED)
    b = by(doc)
    assert b["A1"]["state"] == P.FLAGGED and b["A1"]["precast"]["piece_m"] is None
    assert b["A2"]["state"] == P.FLAGGED and b["A2"]["precast"]["fit"] == P.NO_FIT
    assert b["A2"]["precast"]["piece_m"] == 1.5 and b["A2"]["precast"]["bearing_m"] == 0.15
    assert b["A3"]["state"] == P.HELD and b["A3"]["precast"]["fit"] == P.HELD
    assert b["A4"]["state"] == P.FLAGGED and "does not fit" in b["A4"]["why"]
    assert b["A5"]["system"] == P.SYS_HELD and b["A5"]["schedule_row"] is None and "SCHEDULE_SILENT" in b["A5"]["why"]
    assert b["B2"]["state"] == P.HELD and b["B2"]["rc"]["count"] is None
    assert b["B2"]["rc"]["length_hi_m"] == pytest.approx(2.10) and b["B2"]["rc"]["length_lo_m"] is None
    assert b["H1"]["state"] == P.HELD
    s = doc["summary"]
    # held / flagged are named, never counted, never 0 in a count
    g = s["precast_governing_by_length"]
    assert g["1.50"] == {"produced_nr": 1, "produced": ["P2"], "held": ["A3"], "flagged": ["A2", "A4"]}
    assert s["precast_governing_flagged_no_piece"] == ["A1"]
    assert s["rc_held"] == ["B2"] and s["system_held"] == ["A5"] and s["not_required_held_by_name"] == ["H1"]
    assert s["label"].startswith("PARTIAL")


def test_no_schedule_black_wall_system_held():
    b = by(P.census([op("B9", 1.0, "BLACK"), op("W9", 1.0)], None))
    assert b["B9"]["system"] == P.SYS_HELD and b["B9"]["state"] == P.HELD
    assert b["W9"]["system"] == P.OWNER_PRECAST and b["W9"]["precast"]["piece_m"] == 1.5


def test_schedule_scope_covers_white_uses_project_bearing_for_the_precast_beside():
    sch = dict(SCHED, scope=("WHITE", "BLACK"), bearing_m=0.40, bearing_source="detail 'MIN 40 cm'")
    r = by(P.census([op("W1", 1.00, s=0.615, t=0.50)], sch))["W1"]
    assert r["system"] == P.PROJECT_RC and r["state"] == P.PRODUCED
    pb = r["precast_beside"]
    assert pb["bearing_m"] == 0.40 and pb["required_m"] == pytest.approx(1.80) and pb["piece_m"] == 2.5
    assert pb["fit"] == P.NO_FIT and pb["state"] == P.FLAGGED    # 0.615 + 0.50 = 1.115 < 2.50 - 1.00 = 1.50
    ok = by(P.census([op("W1", 1.00, s=0.615, t=1.00)], sch))["W1"]["precast_beside"]
    assert ok["fit"] == P.FITS and ok["state"] == P.PRODUCED      # 1.615 >= 1.50, each end >= 0.40


def test_shared_pier():
    # pier 0.25 shared with a REQUIRED neighbour: 0.25 - 0.15 = 0.10 < 0.15 -> deficit
    a = op("S1", 1.10, t=None)
    a["ends"][1] = e("END", 0.25, "OPENING", "S2")
    nb = op("S2", 1.10)
    nb["ends"][0] = e("START", 0.25, "OPENING", "S1")
    b = by(P.census([a, nb], None))
    assert b["S1"]["state"] == P.FLAGGED and b["S2"]["state"] == P.FLAGGED
    # with a HELD neighbour: 0.25 < 2 x 0.15 -> CONDITIONAL, HELD by name; 0.35 >= 0.30 -> PRODUCED
    c = op("S1", 1.10)
    c["ends"][1] = e("END", 0.25, "OPENING", "S3")
    h = op("S3", 1.10, decision="HELD")
    r = by(P.census([c, h], None))["S1"]
    assert r["state"] == P.HELD and r["precast"]["fit"] == P.CONDITIONAL
    c["ends"][1] = e("END", 0.35, "OPENING", "S3")
    assert by(P.census([c, h], None))["S1"]["state"] == P.PRODUCED


@pytest.mark.parametrize("w", [1100, 85, 0, -1.0, "1.10", True])
def test_units_refused(w):
    with pytest.raises(P.LintelPiecesError):
        P.census([op("U1", w)], SCHED)


def test_second_record_and_bad_inputs_refused():
    with pytest.raises(P.LintelPiecesError):
        P.census([op("D1", 1.0), op("D1", 1.0)], SCHED)
    with pytest.raises(P.LintelPiecesError):
        P.census([op("D2", 1.0, "GREY")], SCHED)
    one = op("D3", 1.0)
    one["ends"] = one["ends"][:1]
    with pytest.raises(P.LintelPiecesError):
        P.census([one], SCHED)
    x = op("D4", 1.0)
    x["ends"][1] = e("END", 0.5, "OPENING", "NOPE")
    with pytest.raises(P.LintelPiecesError):
        P.census([x], None)
