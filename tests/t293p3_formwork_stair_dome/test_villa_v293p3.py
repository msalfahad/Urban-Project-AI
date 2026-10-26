"""T-293 part 3 rules on a hand-calculated villa (V293P3, not Alsenan): stair / dome / tank formwork rows tied to the
lines that carry their pieces' concrete (R-FW-P3-1), a volume / thickness soffit row split to its physical causes
(R-FW-P3-2), one member one face view (R-FW-P3-4), a drawn element with no line (R-FW-P3-5).

Villa V293P3 (by hand). Stair S: lane 1.00 m, going 0.25, riser 0.175 (printed), waist printed.
  sec = hypot(0.25, 0.175) / 0.25 = 1.220656
  flight F (closable part line LP): 8 risers 8 x 1.00 x 0.175 = 1.400 m2
     drawn soffit: beam face -> last riser 1.75 m plan x 1.00 x sec = 2.136147 m2
     the volume / thickness row runs 0.20 further, inside the beam band: 0.20 x 1.00 x sec = 0.244131 m2 (no surface)
     row printed 2.380 = 2.136147 + 0.244131 + rounding -0.000278
  landing D (closable part line LP): plate 1.20 x 1.00 = 1.200 m2, column 0.20 x 0.10 = 0.020 inside it
     row printed 1.200 = soffit 1.180 + column 0.020 (no surface)
  winder W (still held in the parent line PS): its row CALCULATED 0.900 -> HELD, blank, 0.900 kept
Dome Q: chord 3.00, rise 1.00, shell 0.08: R_o = (1.5^2 + 1^2) / 2 = 1.625, R_i = 1.545, h_i = 0.92
  intrados = 2 pi R_i h_i = 8.930920 m2 on the shell line LQ; its drum: drawn, no line -> NO_CANDIDATE_LINE, blank
Tank T: its walls are beam B (0.20 x 1.00 x 3.00): faces tied under BEAM; the TANK row is a second view, no face
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t293"))
import face_line_ledger as F  # noqa: E402
import t293p3_ledger as L  # noqa: E402

SEC = math.hypot(0.25, 0.175) / 0.25
LINES = {"LP": {"item_code": "STR.CONC.STAIR", "element_id": "S#CLOSABLE:F+D", "evidence_state": "SOURCE_DERIVED"},
         "PS": {"item_code": "STR.CONC.STAIR", "element_id": "S", "evidence_state": "BLOCKED_RFI"},
         "LQ": {"item_code": "STR.CONC.DOME", "element_id": "Q:SHELL", "evidence_state": "SOURCE_DERIVED"},
         "LB": {"item_code": "STR.CONC.BEAM", "element_id": "B", "evidence_state": "PROVISIONAL"}}
BIND = {"_reason": {"DRUM:Q": "drum drawn, no candidate line"}, "PIECE:F": ["LP"], "PIECE:D": ["LP"],
        "PIECE:W": ["PS"], "SHELL:Q": ["LQ"], "DRUM:Q": [], "BEAM:B": ["LB"]}
HELD_PIECES = {"PIECE:W"}


def row(fid, item, m2, member, status="CALCULATED", element="STAIR", **kw):
    return dict({"face_id": fid, "revision": "V293P3 r4-like", "element": element, "floor": "GF", "item": item,
                 "face_kind": "SOFFIT", "contact": "FORM", "alternative": "", "method": "G", "m2": m2, "lo": None,
                 "hi": None, "status": status, "members": [member], "unit": "m2"}, **kw)


def villa(order=1):
    flight = row("R1", "F waist soffit", 2.380, "PIECE:F")
    risers = row("R2", "F riser forms", 1.400, "PIECE:F")
    landing = row("R3", "D landing soffit", 1.200, "PIECE:D")
    winder = row("R4", "W winder faces", 0.900, "PIECE:W")
    shell = row("R5", "Q shell intrados", round(2 * math.pi * 1.545 * 0.92, 6), "SHELL:Q", element="DOME")
    drum = row("R6", "Q drum faces", None, "DRUM:Q", status="HELD", element="DOME")
    tank = row("R7", "T tank walls (beam B)", None, "TANK", status="HELD", element="TANK")
    src = [flight, risers, landing, winder, shell, drum, tank][::order]
    pf = L.split_row(flight, [dict(id="SOFFIT", member="PIECE:F", m2=1.75 * 1.0 * SEC, alt_D=2.10),
                              dict(id="IN_BEAM", member="PIECE:F", m2=0.20 * 1.0 * SEC, kind=L.NO_FACE)][::order])
    pl = L.split_row(landing, [dict(id="SOFFIT", member="PIECE:D", m2=1.18),
                               dict(id="COL", member="PIECE:D", m2=0.02, kind=L.NO_FACE)][::order])
    faces = pf + pl + [risers, winder, shell, drum, tank]
    named = L.named_kinds(pf + pl)
    named["R7"] = (L.DUPVIEW, "the tank walls are beam B, tied under BEAM")
    out = F.tie(faces, BIND, LINES, named, source=src)
    L.hold_pieces(out["rows"])
    L.hold_on_unbooked_pieces(out["rows"], HELD_PIECES)
    L.refuse_measured_on_held(out["rows"], HELD_PIECES)
    return out


def by_id(out):
    return {r["face_id"]: r for r in out["rows"]}


# ----------------------------------------------------------------------------------------------------- normal

def test_hand_values():
    assert SEC == pytest.approx(1.220656, abs=1e-6)
    assert 1.75 * SEC == pytest.approx(2.136147, abs=1e-6)
    assert 0.20 * SEC == pytest.approx(0.244131, abs=1e-6)
    assert 2 * math.pi * 1.545 * 0.92 == pytest.approx(8.930920, abs=1e-6)


def test_flight_row_split_to_its_causes():
    r = by_id(villa())
    assert r["R1.SOFFIT"]["tie"] == F.TIED and r["R1.SOFFIT"]["line_id"] == "LP"
    assert r["R1.SOFFIT"]["m2"] == pytest.approx(2.136147, abs=1e-6)
    assert r["R1.SOFFIT"]["alt_D_m2"] == 2.10                 # method D beside it, never summed
    assert r["R1.IN_BEAM"]["tie"] == L.NO_FACE and r["R1.IN_BEAM"].get("line_id") is None
    assert r["R1.ROUNDING"]["tie"] == L.ROUND
    assert r["R1.ROUNDING"]["m2"] == pytest.approx(2.380 - 2.136147 - 0.244131, abs=1e-6)


def test_landing_and_risers_on_the_part_line():
    r = by_id(villa())
    assert r["R3.SOFFIT"]["m2"] == pytest.approx(1.18) and r["R3.SOFFIT"]["line_id"] == "LP"
    assert r["R3.COL"]["tie"] == L.NO_FACE
    assert r["R2"]["m2"] == pytest.approx(1.40) and r["R2"]["line_id"] == "LP"


def test_face_of_held_piece_held_with_its_parent():
    r = by_id(villa())["R4"]
    assert r["line_id"] == "PS" and r["status"] == "HELD" and r["m2"] is None and r["held_from"] == 0.9


def test_dome_shell_and_drum():
    r = by_id(villa())
    assert r["R5"]["line_id"] == "LQ" and r["R5"]["m2"] == pytest.approx(8.930920, abs=1e-6)
    assert r["R6"]["tie"] == F.NO_LINE and r["R6"]["m2"] is None


def test_tank_row_is_a_second_view_not_a_face():
    r = by_id(villa())["R7"]
    assert r["tie"] == L.DUPVIEW and r.get("line_id") is None


def test_closure_zero_and_consumer_lines():
    out = villa()
    for c in out["closure"]:
        assert c["residual_m2"] == 0 and c["residual_lo"] == 0 and c["residual_hi"] == 0
    cons = F.consumer(out["rows"], LINES, "V293P3", {"project_id": "V293P3"})
    lp = next(x for x in cons["lines"] if x["concrete_line_id"] == "LP")
    assert lp["totals"]["CALCULATED||G"]["m2"] == pytest.approx(2.136147 + 1.40 + 1.18, abs=1e-6)
    assert all(f["tie"] == F.TIED for x in cons["lines"] for f in x["faces"])


def test_order_invariant_mirror():
    a, b = villa(1), villa(-1)
    tot = lambda o: sorted((r["face_id"], r["tie"], r["m2"], r.get("held_from")) for r in o["rows"])  # noqa: E731
    assert tot(a) == tot(b)


# ----------------------------------------------------------------------------------------------------- adverse

def test_measured_face_on_held_piece_refused():
    out = villa()
    r = by_id(out)["R4"]
    r["m2"], r["status"] = 0.9, "CALCULATED"
    with pytest.raises(F.Refused, match="held piece"):
        L.refuse_measured_on_held(out["rows"], HELD_PIECES)


def test_pieces_not_closing_refused():
    with pytest.raises(F.Refused, match="do not close"):
        L.split_row(row("R1", "F waist", 2.380, "PIECE:F"), [dict(id="SOFFIT", member="PIECE:F", m2=2.136147)])


def test_negative_or_missing_piece_refused():
    with pytest.raises(F.Refused, match="positive"):
        L.split_row(row("R1", "F", 1.0, "PIECE:F"), [dict(id="A", member="PIECE:F", m2=1.2),
                                                     dict(id="B", member="PIECE:F", m2=-0.2)])
    with pytest.raises(F.Refused, match="positive"):
        L.split_row(row("R1", "F", 1.0, "PIECE:F"), [dict(id="A", member="PIECE:F", m2=None)])
    with pytest.raises(F.Refused, match="without a member"):
        L.split_row(row("R1", "F", 1.0, "PIECE:F"), [dict(id="A", member="", m2=1.0)])


def test_row_without_quantity_not_split():
    with pytest.raises(F.Refused, match="without a quantity"):
        L.split_row(row("R6", "drum", None, "DRUM:Q", status="HELD"), [dict(id="A", member="DRUM:Q", m2=0.0)])


def test_unit_slip_refused():
    bad = row("R9", "F risers in mm2", 1.4e6, "PIECE:F", unit="mm2")
    with pytest.raises(F.Refused, match="unit"):
        F.tie([bad], BIND, LINES)


def test_held_piece_never_zero():
    r = by_id(villa())["R4"]
    assert r["m2"] is None and r["held_from"] == 0.9            # blank, never 0


def test_drum_face_never_invents_a_value():
    r = by_id(villa())["R6"]
    assert r["m2"] is None and r.get("held_from") is None and r.get("lo") is None


def test_tank_and_beam_views_on_one_member_refused():
    rows = [dict(face_id="X1", tie=F.TIED, members=["BEAM:B"], element="BEAM", m2=0.6),
            dict(face_id="X2", tie=F.TIED, members=["BEAM:B"], element="TANK", m2=6.0)]
    with pytest.raises(F.Refused, match="two element views"):
        L.check_one_view(rows)
    L.check_one_view(rows[:1] + [dict(rows[1], tie=L.DUPVIEW)])   # the view kept as a pointer passes


def test_duplicate_piece_never_reaches_the_consumer():
    out = villa()
    cons = F.consumer(out["rows"], LINES, "V293P3", {})
    ids = {f["face_id"] for x in cons["lines"] for f in x["faces"]}
    assert "R1.IN_BEAM" not in ids and "R3.COL" not in ids and "R1.ROUNDING" not in ids
