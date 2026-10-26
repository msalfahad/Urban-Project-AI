"""T-305 rules on a hand NON-Alsenan fixture: a two-storey house, GF 10.00 m south face (6.00 m under the set-back 1F,
4.00 m a roof edge with a 0.50 m parapet), 1F 6.00 m south face, the top floor to its parapet.

Levels: ground +0.00, GF F.F.L. +0.50, 1F F.F.L. = GF roof +3.80, GF parapet top +4.30, 1F roof +7.00, 1F parapet
top +8.00. By hand:
  GF plinth 10.00 x 0.50 = 5.000 m2 (geometry line only: no finish line reads it -> plaster NO_LINE)
  GF storey 10.00 x 3.30 = 33.000 m2 (IN_LINE GF finish line)
  GF parapet outer face 4.00 x 0.50 = 2.000 m2 (above the next F.F.L.: NO_LINE, a missing category)
  1F storey + parapet 6.00 x 4.20 = 25.200 m2 (top floor, formula TO_PARAPET +8.00: IN_LINE 1F finish line)
  openings on the GF face: W1 1.20 x (2.50 - 1.00) = 1.800 (drawn); D1 0.90 x 2.20 = 1.980 (owner fallback)
  GF net 33.000 - 1.800 - 1.980 = 29.220 m2; parapet top item 4.00 x 0.20 = 0.800 m2 (own item, never wall m2)
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "research" / "agents_t305"))
import facade_line_ledger as R  # noqa: E402

GF_FFL, ROOF_GF, PAR_GF, PAR_1F = 0.50, 3.80, 4.30, 8.00
FIN = [R.FacadeLine("L-gf-fin", "FIN.EXT.FINISH", "GF", "STOREY", 0.0, ROOF_GF),
       R.FacadeLine("L-1f-fin", "FIN.EXT.FINISH", "1F", "STOREY", 0.0, PAR_1F)]
PLINTH = [R.FacadeLine("L-gf-plinth", "ARCH.FACADE", "GF", "PLINTH", None, None)]
FLOORS = {"GF": (GF_FFL, ROOF_GF), "1F": (ROOF_GF, None)}


def bands_gf():
    """the GF face as the face table gives it: FLUSH 6.00 and EDGE 4.00, each a plinth and a storey band; the EDGE
    storey runs to the parapet top and is cut at the next F.F.L."""
    out = []
    for portion, L, top in (("FLUSH", 6.0, ROOF_GF), ("EDGE", 4.0, PAR_GF)):
        out.append(R.Portion("GF", "S-1", "S", portion, L, 0.0, GF_FFL, L * GF_FFL, "DRAWING-CONFIRMED",
                             band_kind=R.band_kind("GF", 0.0, GF_FFL, GF_FFL, ROOF_GF)))
        for b0, b1 in R.split_at(GF_FFL, top, ROOF_GF):
            out.append(R.Portion("GF", "S-1", "S", portion, L, b0, b1, L * (b1 - b0), "DRAWING-CONFIRMED",
                                 band_kind=R.band_kind("GF", b0, b1, GF_FFL, ROOF_GF)))
    return out


def book_all(portions, floors_of):
    book, tot = R.Book(), {}
    for p in portions:
        st, ln, why = R.owner_of(p, FIN + PLINTH, {p.floor: floors_of[p.floor]}, lowest="GF")
        if st == "IN_LINE" and ln.kind == "PLINTH":
            st, ln = "NO_LINE", None          # geometry only: no finish line reads the plinth
        book.add(f"{p.floor}|{p.side}|{p.portion}|{p.bottom}|{p.top}", st, ln.line_id if ln else None)
        k = ln.line_id if ln else f"{st}:{p.band_kind}"
        tot[k] = tot.get(k, 0.0) + p.area_m2
    return book, tot


def test_normal_two_storey_facade_by_hand():
    one_f = [R.Portion("1F", "S-1", "S", "STOREY+PARAPET", 6.0, ROOF_GF, PAR_1F, 6.0 * 4.2, "DRAWING-CONFIRMED",
                       band_kind="storey")]
    book, tot = book_all(bands_gf() + one_f, {"GF": FLOORS["GF"], "1F": (ROOF_GF, PAR_1F)})
    assert tot["L-gf-fin"] == pytest.approx(33.000, abs=1e-9)
    assert tot["NO_LINE:plinth"] == pytest.approx(5.000, abs=1e-9)
    assert tot["NO_LINE:parapet"] == pytest.approx(2.000, abs=1e-9)
    assert tot["L-1f-fin"] == pytest.approx(25.200, abs=1e-9)
    # every band once: the statuses re-add to the geometric total (residual 0.000)
    assert sum(tot.values()) == pytest.approx(10 * 0.5 + 10 * 3.3 + 4 * 0.5 + 25.2, abs=1e-9)


def test_openings_deducted_once_by_hole():
    band = 33.0
    w1 = R.Opening("W1", "GF", "S-1", 1.2, 1.0, 2.5, 1.2 * 1.5, "DRAWING-CONFIRMED")
    d1 = R.Opening("D1", "GF", "S-1", 0.9, 0.0, 2.2, 0.9 * 2.2, "ASSUMED — OWNER-APPROVED")
    ded = [R.deduction(o, band) for o in (w1, d1)]
    assert band - sum(d["fixed"] for d in ded) == pytest.approx(29.220, abs=1e-9)
    assert ded[1]["status"] == "ASSUMED — OWNER-APPROVED"


def test_held_opening_is_a_range_capped_by_its_band_never_zero():
    o = R.Opening("W9", "GF", "S-1", 2.0, None, None, None, "HELD", cap_m2=2.0 * 3.3)
    d = R.deduction(o, 5.0)                    # cap larger than the band -> the band
    assert (d["fixed"], d["lo"], d["hi"]) == (None, 0.0, 5.0)
    with pytest.raises(R.LedgerError):
        R.deduction(R.Opening("W9", "GF", "S-1", 2.0, None, None, None, "HELD"), 5.0)


def test_hole_is_limited_to_its_face_length():
    # a 0.50 m window symbol in a 0.467 m recess face: the hole on the face is 0.467 x h, the rest is behind the return
    a, over = R.hole_on_face(0.50, 0.84, 3.00, face_width_m=0.467)
    assert a == pytest.approx(0.467 * 2.16, abs=1e-9) and over == pytest.approx(0.033, abs=1e-9)


# ------------------------------------------------------------------------------------------------ adverse cases
def test_face_booked_to_two_lines_refused():
    b = R.Book()
    b.add("GF|S-1|FLUSH|0.5|3.8", "IN_LINE", "L-gf-fin")
    with pytest.raises(R.LedgerError):
        b.add("GF|S-1|FLUSH|0.5|3.8", "IN_LINE", "L-1f-fin")
    with pytest.raises(R.LedgerError):
        b.add("GF|S-2|FLUSH|0.5|3.8", "IN_LINE", None)


def test_window_measure_as_wall_deduction_refused():
    o = R.Opening("W17x", "1F", "N-1", 2.69, None, None, 8.1434, "DRAWING-CONFIRMED", window_measure_m2=9.870)
    with pytest.raises(R.LedgerError):
        R.deduction(o, 30.0, use_window_measure=True)
    assert R.deduction(o, 30.0)["fixed"] == 8.1434
    with pytest.raises(R.LedgerError):                     # a hole larger than its face band
        R.deduction(R.Opening("Wbig", "GF", "S", 3.0, 0.0, 4.0, 12.0, "DRAWING-CONFIRMED"), 10.0)


def test_parapet_top_booked_as_wall_m2_refused():
    with pytest.raises(R.LedgerError):
        R.to_wall_line("PARAPET_TOP", 0.800, "m2", FIN[0])
    with pytest.raises(R.LedgerError):
        R.to_wall_line("CORNER_ML", 23.0, "m.l", FIN[0])
    with pytest.raises(R.LedgerError):
        R.add_to_area(33.0, 23.0, "m.l")
    assert R.item_owner("PARAPET_TOP")[0] == "NO_LINE"
    assert R.to_wall_line("WALL_FACE", 33.0, "m2", FIN[0]) == 33.0


def test_missing_face_reported_as_zero_refused():
    p = R.Portion("GF", "S-9", "S", "EDGE", 3.0, 0.5, None, None, "HELD", band_kind="storey")
    with pytest.raises(R.LedgerError):
        R.owner_of(p, FIN, {"GF": FLOORS["GF"]}, lowest="GF")
    with pytest.raises(R.LedgerError):
        R.to_wall_line("WALL_FACE", None, "m2", FIN[0])
    held = R.Portion("GF", "S-9", "S", "EDGE", 3.0, 0.5, None, None, "HELD", band_kind="storey",
                     held_lo=2.0, held_hi=3.0)
    assert R.owner_of(held, FIN, {"GF": FLOORS["GF"]}, lowest="GF")[0] == "IN_LINE"


def test_band_straddling_the_next_ffl_refused_until_split():
    with pytest.raises(R.LedgerError):
        R.band_kind("GF", GF_FFL, PAR_GF, GF_FFL, ROOF_GF)
    assert [R.band_kind("GF", a, b, GF_FFL, ROOF_GF) for a, b in R.split_at(GF_FFL, PAR_GF, ROOF_GF)] == \
        ["storey", "parapet"]
    with pytest.raises(R.LedgerError):
        R.band_kind("GF", 2.0, 1.0, GF_FFL, ROOF_GF)


def test_upper_floor_face_on_a_lower_roof_and_slab_edge_have_no_line():
    p = R.Portion("1F", "E-1", "E", "OVER_LOWER_ROOF", 3.0, 3.2, ROOF_GF, 1.8, "DRAWING-CONFIRMED",
                  band_kind=R.band_kind("1F", 3.2, ROOF_GF, ROOF_GF, PAR_1F, "OVER_LOWER_ROOF"))
    assert R.owner_of(p, FIN, {"1F": (ROOF_GF, PAR_1F)}, lowest="GF")[0] == "NO_LINE"
    s = R.Portion("1F", "N-1", "N", "SLAB_EDGE_BELOW", 2.0, None, ROOF_GF, None, "HELD", band_kind="slab_edge")
    assert R.owner_of(s, FIN, {"1F": (ROOF_GF, PAR_1F)}, lowest="GF")[0] == "NO_LINE"


def test_no_storey_line_or_two_lines_is_no_line_not_a_guess():
    p = bands_gf()[1]
    assert R.owner_of(p, [], {"GF": FLOORS["GF"]}, lowest="GF")[0] == "NO_LINE"
    two = FIN + [R.FacadeLine("L-gf-fin-2", "FIN.EXT.FINISH", "GF", "STOREY", 0.0, ROOF_GF)]
    assert R.owner_of(p, two, {"GF": FLOORS["GF"]}, lowest="GF")[0] == "NO_LINE"


def test_mirror_rotation_and_units_do_not_move_the_ledger():
    # the ledger reads lengths and printed levels only: a mirrored / rotated outline keeps its side lengths, and a
    # drawing in millimetres gives the same bands once its levels are in metres
    mm = [(int(a * 1000), int(b * 1000)) for a, b in R.split_at(GF_FFL, PAR_GF, ROOF_GF)]
    assert [(a / 1000, b / 1000) for a, b in mm] == R.split_at(GF_FFL, PAR_GF, ROOF_GF)
    _, tot = book_all(list(reversed(bands_gf())), {"GF": FLOORS["GF"]})
    assert tot["L-gf-fin"] == pytest.approx(33.000, abs=1e-9)
