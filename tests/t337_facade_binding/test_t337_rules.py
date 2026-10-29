"""T-337 rules R-T337-1 .. 3 on a hand-made villa (NOT the development villa).

Villa N (metres, one datum; hand calculation):
  parts   HOUSE  F.F.L. GF +0.60, 1F +4.00, top roof +7.20 (parapet top +8.00)
          ANNEX  F.F.L. GF +0.20 (a ground floor with TWO F.F.L.s), roof +3.70 (parapet top +4.20)
  faces   A annex face 5.00 m, ground 0.00 -> +4.20: plinth 0.00-0.20 = 1.000 | GF storey 0.20-3.70 = 17.500 |
            annex parapet 3.70-4.20 = 2.500                                                             (21.000)
          B house GF face 8.00 m, 0.00 -> +4.00: plinth 0.00-0.60 = 4.800 | GF storey 0.60-4.00 = 27.200   (32.000)
          C house 1F face 8.00 m, +4.00 -> +8.00: 1F storey 4.00-7.20 = 25.600 | parapet 7.20-8.00 = 6.400 (32.000)
          D a 1F face standing on the annex roof, 3.00 m, +3.70 -> +7.20: 3.70-4.00 = 0.900 is inside the GF levels
            (+0.60 -> +4.00) -> GF storey, 4.00-7.20 = 9.600 -> 1F storey                               (10.500)
          every face once: 95.500
  holes   W1 1.20 x 1.50 on B, sill 1.00 above +0.60 (+1.60 -> +3.10)                 1.800 DRAWING-CONFIRMED
          D1 0.90 x 2.10 on A, from the annex F.F.L. (+0.20 -> +2.30)                  1.890 ASSUMED — OWNER-APPROVED
          W2 on C, height not printed: 0 .. 3.000 (width 1.50 x the 2.00 m the band allows at most)        HELD
  lines   GF storey gross 17.500 + 27.200 + 0.900 = 45.600, net 45.600 - 1.800 - 1.890 = 41.910
          1F storey gross 25.600 + 9.600 = 35.200, net 32.200 .. 35.200 (HELD, no point value)
          parapet annex 2.500, parapet house 6.400, plinth 5.800 (no deduction: no hole in them)
  A run x one storey height formula (GF run 13.00 x (4.00 - 0.60)) = 44.200: -1.400 against the faces, and the
  annex parapet 2.500 m2 would sit in a storey line: both refused by the rules below.
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t337"))

import facade_binding as FB  # noqa: E402

HOUSE = FB.Part("HOUSE", (("GF", 0.60), ("1F", 4.00)), 7.20)
ANNEX = FB.Part("ANNEX", (("GF", 0.20),), 3.70)

# face: (key, part, length, bottom, top, roof the face rises above or None)
FACES = [("A", ANNEX, 5.00, 0.00, 4.20, 3.70), ("B", HOUSE, 8.00, 0.00, 4.00, None),
         ("C", HOUSE, 8.00, 4.00, 8.00, 7.20), ("D", HOUSE, 3.00, 3.70, 7.20, None)]
LINE = {("STOREY", "GF"): "GF", ("STOREY", "1F"): "1F", ("PLINTH", None): "PLINTH"}


def bands(part, b, t, roof):
    cuts = sorted({b, t, part.lowest_ffl(), *(z for _f, z in part.floors), part.top}
                  | ({roof} if roof is not None else set()))
    return [(x, y) for x, y in zip(cuts, cuts[1:]) if x >= b - 1e-9 and y <= t + 1e-9 and y - x > 1e-9]


def scaled(part, k):
    return FB.Part(part.name, tuple((f, z * k) for f, z in part.floors), part.top * k)


def build(order=1):
    bk = FB.Book()
    rows = []
    for key, part, L, b, t, roof in FACES[::order]:
        for (x, y) in bands(part, b, t, roof):
            kind, owner = FB.band_kind(x, y, part, roof=roof)
            ok = FB.owner_of(kind, owner, roof=None if roof is None else f"{part.name}+{roof:.2f}")
            line = LINE.get(ok) or f"PARAPET {ok[1]}"
            m2 = round(L * (y - x), 6)
            bk.line(line, "m2")
            fk = f"{key}/{x:.2f}"
            bk.add_face(fk, line, m2, m2, "DRAWING-CONFIRMED")
            rows.append((fk, line, m2))
    bk.add_opening("W1", "B/0.60", 1.800, None, None, "DRAWING-CONFIRMED")
    bk.add_opening("D1", "A/0.20", 1.890, None, None, "ASSUMED — OWNER-APPROVED")
    bk.add_opening("W2", "C/4.00", 0.0, 0.0, 3.000, "HELD")
    return bk, rows


def test_normal_villa_n_by_hand():
    bk, rows = build()
    assert round(sum(r[2] for r in rows), 6) == 95.5
    gf = bk.totals("GF")
    assert [round(x, 6) for x in gf[:7]] == [45.6, 45.6, 3.69, 0.0, 0.0, 41.91, 41.91]
    f1 = bk.totals("1F")
    assert round(f1[0], 6) == 35.2 and round(f1[5], 6) == 32.2 and round(f1[6], 6) == 35.2
    assert round(bk.totals("PARAPET ANNEX+3.70")[0], 6) == 2.5
    assert round(bk.totals("PARAPET HOUSE+7.20")[0], 6) == 6.4
    assert round(bk.totals("PLINTH")[0], 6) == 5.8
    # the face on the lower roof: its band below the 1F F.F.L. belongs to the GF storey (levels, not outline)
    assert ("D/3.70", "GF", 0.9) in rows
    # run x storey height would give 44.200 on GF: the face rows give 45.600 (+0.900 lower-roof face + 0.500 two F.F.L.s)
    assert round((5.00 + 8.00) * (4.00 - 0.60), 6) == 44.2


def test_two_ffl_ground_floor_is_measured_by_face_not_run_x_height():
    a = FB.band_kind(0.20, 3.70, ANNEX)
    b = FB.band_kind(0.60, 4.00, HOUSE)
    assert a == ("storey", "GF") and b == ("storey", "GF")


def test_reversed_order_and_millimetres_do_not_move_the_result():
    # the rules read levels and run lengths only (no plan coordinates), so a mirrored plan gives the same rows
    base = build()[0]
    rev = build(order=-1)[0]
    for ln in ("GF", "1F", "PLINTH"):
        assert [round(x, 6) for x in base.totals(ln)] == [round(x, 6) for x in rev.totals(ln)]
    assert FB.band_kind(200.0, 3700.0, scaled(ANNEX, 1000.0)) == ("storey", "GF")
    assert FB.band_kind(3700.0, 4200.0, scaled(ANNEX, 1000.0), roof=3700.0) == ("parapet", None)


# ------------------------------------------------------------------------------------------------- adverse cases
def test_adverse_parapet_face_folded_into_a_storey_line_is_refused():
    with pytest.raises(FB.BindingError, match="roof level"):
        FB.band_kind(0.20, 4.20, ANNEX, roof=3.70)          # the storey band run on to the parapet top
    with pytest.raises(FB.BindingError, match="crosses the level"):
        FB.band_kind(0.20, 4.20, ANNEX)                      # no roof named: still beyond the part's top level


def test_adverse_band_across_the_ffl_or_the_next_ffl_is_refused_until_split():
    with pytest.raises(FB.BindingError, match="F.F.L."):
        FB.band_kind(0.00, 4.00, HOUSE)
    with pytest.raises(FB.BindingError, match="crosses the level 4.0"):
        FB.band_kind(0.60, 5.00, HOUSE)
    assert FB.split_at(0.60, 5.00, 4.00) == [(0.60, 4.00), (4.00, 5.00)]


def test_adverse_held_face_as_zero_and_unknown_with_a_number_are_refused():
    bk = FB.Book()
    bk.line("GF", "m2")
    with pytest.raises(FB.BindingError, match="never 0"):
        bk.add_face("X", "GF", 0.0, 0.0, "HELD")
    bk.add_face("Y", "GF", None, None, "HELD")             # blank HELD is accepted (no number, not 0)
    with pytest.raises(FB.BindingError, match="no number"):
        bk.add_item("coping", "COPING", "m.l", 10.0, 10.0, "UNKNOWN")
    with pytest.raises(FB.BindingError, match="HELD, not"):
        bk.add_item("tops", "TOP", "m2", 1.0, 2.0, "DRAWING-CONFIRMED")


def test_adverse_opening_deducted_twice_or_outside_its_band_is_refused():
    bk, _ = build()
    with pytest.raises(FB.BindingError, match="twice"):
        bk.add_opening("W1", "B/0.60", 1.800, None, None, "DRAWING-CONFIRMED")
    with pytest.raises(FB.BindingError, match="leaves its band"):
        FB.hole_on_band(2.50, 3.90, 0.20, 3.70)              # a head above the annex roof
    with pytest.raises(FB.BindingError, match="larger than its band"):
        bk.add_opening("W9", "D/3.70", 1.0, None, None, "DRAWING-CONFIRMED")
    with pytest.raises(FB.BindingError, match="bound"):
        bk.add_opening("W8", "C/4.00", 0.0, 0.0, 0.0, "HELD")


def test_adverse_face_in_two_lines_and_ml_in_an_m2_line_are_refused():
    bk, _ = build()
    with pytest.raises(FB.BindingError, match="already owned"):
        bk.add_face("A/3.70", "GF", 2.5, 2.5, "DRAWING-CONFIRMED")
    bk.add_item("arrises", "CORNERS", "m.l", 12.0, 12.0, "DRAWING-CONFIRMED")
    with pytest.raises(FB.BindingError, match="not an m2 face line"):
        bk.add_face("Z", "CORNERS", 1.0, 1.0, "DRAWING-CONFIRMED")
    with pytest.raises(FB.BindingError, match="is m.l, not m2"):
        bk.add_item("arris as area", "CORNERS", "m2", 6.0, 6.0, "DRAWING-CONFIRMED")
