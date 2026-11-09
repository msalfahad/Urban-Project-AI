"""T-556: PLASTER_HEIGHT_METHOD_V1 (research/agents_t556, R-T556-1): dry wall plaster to the slab / roof underside.
Synthetic villa "P556" (not the training villa), hand calculations; adverse cases; then the development-villa pins
(repository inputs only: candidate line index, T-128 r3 / T-292 / T-110 / T-552 merged ledgers, T-214 levels)."""
from __future__ import annotations

import json
import subprocess
import sys
from decimal import Decimal
from itertools import permutations
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t556"))
import t556_plaster_height as M  # noqa: E402

Dc = Decimal
IV = ("3.50", "P556 section S-1: slab-to-slab 3.50")
SLAB = ("0.20", "P556 S-0 note: slab 20 cm")
B = ("0.08", "P556 F-1 floor build-up 8 cm")


def H(**kw):
    a = dict(basis="SLAB_OR_ROOF_UNDERSIDE", interval=IV[0], interval_src=IV[1], slab=SLAB[0], slab_src=SLAB[1],
             buildup=B[0], buildup_src=B[1])
    a.update(kw)
    return M.plaster_height(**a)


# ---- villa "P556" room (hand, from the task row): 4.00 x 5.00 m -> run 18.00 lm; slab-to-slab 3.50, slab 0.20,
# build-up 0.08 -> plaster height 3.50 - 0.20 - 0.08 = 3.22 m; one door 0.90 x 2.20 = 1.98 m2.
# Plaster 18.00 x 3.22 - 1.98 = 55.98 m2; paint (finished ceiling 3.00) 18.00 x 3.00 - 1.98 = 52.02 m2.
DOOR = {"id": "D1", "width": "0.90", "sill": "0", "head": "2.20"}


def test_fixture_height_and_net():
    assert H() == Dc("3.22")
    r = M.restate_line(face_lm="18.00", roof_share="0", H_floor=H(), H_roof_scenario=None, openings=[DOOR], beams=[])
    assert Dc(r["gross"]) == Dc("57.96")
    assert Dc(r["net_lo"]) == Dc(r["net_hi"]) == Dc("55.98")
    paint = Dc("18.00") * Dc("3.00") - Dc("0.90") * Dc("2.20")
    assert paint == Dc("52.02")
    assert Dc(r["net_lo"]) - paint == Dc("3.96")          # = 18.00 x (3.22 - 3.00): the band above the ceiling


def test_paint_height_refused_for_plaster():
    for basis in M.REFUSED_BASES:
        with pytest.raises(M.PlasterHeightError, match="plaster runs to the slab"):
            H(basis=basis)


@pytest.mark.parametrize("missing", ["slab", "buildup", "interval"])
def test_missing_term_is_held_by_name_never_paint_never_0(missing):
    with pytest.raises(M.Held, match="HELD"):
        H(**{missing: None})


def test_term_without_source_refused():
    with pytest.raises(M.PlasterHeightError, match="no source"):
        H(slab_src="")


def test_floor_buildup_never_carried_to_a_roof():
    with pytest.raises(M.PlasterHeightError, match="never carried to a roof"):
        H(segment="ROOF")
    assert H(segment="ROOF", buildup="0.25", buildup_src="P556 roof detail R-2: roof build-up 25 cm") == Dc("3.05")
    with pytest.raises(M.PlasterHeightError, match="not a roof value"):
        H(buildup_src="roof detail R-2")


def test_units_mm_refused():
    with pytest.raises(M.PlasterHeightError, match="units"):
        H(interval="3500")
    with pytest.raises(M.PlasterHeightError, match="units"):
        H(slab="200")


def test_opening_known_hole_height_full_below_soffit_whatever_the_sill():
    # window 1.50 wide, 1.20 high, sill not printed: wholly below the soffit -> 1.80 in full at the plaster height
    lo, hi, st = M.opening_deduction({"id": "W1", "width": "1.50", "height": "1.20"}, "3.22")
    assert lo == hi == Dc("1.80") and st.startswith("HOLE_HEIGHT")


def test_opening_above_the_paint_height_is_deducted_to_its_head():
    # a glazing band sill 0, head 3.20 (above the 3.00 ceiling): 2.00 x 3.20 = 6.40, not 2.00 x 3.00
    lo, hi, _ = M.opening_deduction({"id": "G1", "width": "2.00", "sill": "0", "head": "3.20"}, "3.22")
    assert lo == hi == Dc("6.40")
    # head at the soffit within 10 mm: capped at H
    lo, _, _ = M.opening_deduction({"id": "G2", "width": "2.00", "sill": "0", "head": "3.23"}, "3.22")
    assert lo == Dc("6.44")
    with pytest.raises(M.PlasterHeightError, match="datum conflict"):
        M.opening_deduction({"id": "G3", "width": "2.00", "sill": "0", "head": "3.30"}, "3.22")


def test_opening_without_height_is_a_held_bound_not_a_guess():
    lo, hi, st = M.opening_deduction({"id": "A1", "width": "1.00"}, "3.22")
    assert (lo, hi) == (Dc(0), Dc("3.22")) and st.startswith("HELD")
    lo, hi, st = M.opening_deduction({"id": "W9", "area_range": ("4.4", "9.8")}, "3.22")
    assert (lo, hi) == (Dc("4.4"), Dc("9.8")) and st.startswith("HELD")


def test_beam_ends_closed_and_open_room():
    # beam 0.30 x 0.60 overall, slab 0.20 -> 0.40 below the soffit; closed room: 2 ends = 0.24 m2
    assert M.beam_end_deduction(width="0.30", depth="0.60", slab="0.20", ends=2) == (Dc("0.24"), Dc("0.24"))
    assert M.beam_end_deduction(width="0.30", depth="0.60", slab="0.20", ends=(0, 2)) == (Dc(0), Dc("0.24"))
    with pytest.raises(M.PlasterHeightError):
        M.beam_end_deduction(width="0.30", depth="0.20", slab="0.20", ends=2)
    r = M.restate_line(face_lm="18.00", roof_share="0", H_floor=H(), H_roof_scenario=None, openings=[DOOR],
                       beams=[{"mark": "B1", "width": "0.30", "depth": "0.60", "slab": "0.20", "ends": 2}])
    assert Dc(r["net_lo"]) == Dc("55.74")


def test_roof_part_at_scenario_with_sensitivity():
    # 18.00 lm, 25 % under a roof: floor part 13.50 x 3.22, roof part 4.50 x 3.05 (roof build-up 0.25)
    hr = H(segment="ROOF", buildup="0.25", buildup_src="P556 roof scenario 25 cm")
    r = M.restate_line(face_lm="18.00", roof_share="0.25", H_floor=H(), H_roof_scenario=hr, openings=[DOOR], beams=[])
    assert Dc(r["gross"]) == Dc("13.50") * Dc("3.22") + Dc("4.50") * Dc("3.05")
    assert Dc(r["roof_sensitivity_m2_per_0.01m"]) == Dc("0.045")
    with pytest.raises(M.PlasterHeightError):
        M.restate_line(face_lm="18", roof_share="1.2", H_floor=H(), H_roof_scenario=hr, openings=[], beams=[])


def test_mirror_and_order_invariant():
    ops = [DOOR, {"id": "W1", "width": "1.50", "height": "1.20"}, {"id": "A1", "width": "1.00"}]
    # 57.96 - 1.98 - 1.80 - (0 .. 3.22) = 50.96 .. 54.18
    outs = {(Dc(r["net_lo"]), Dc(r["net_hi"])) for r in (
        M.restate_line(face_lm="18.00", roof_share="0", H_floor=H(), H_roof_scenario=None, openings=list(p), beams=[])
        for p in permutations(ops))}
    assert outs == {(Dc("50.96"), Dc("54.18"))}


def test_none_is_never_zero():
    with pytest.raises(M.Held):
        M.D(None)


def test_equal_by_construction_defect_signal():
    assert M.equal_by_construction({"R1": "56.0131", "R2": "60"}, {"R1": "56.0131", "R2": "52"}) == ["R1"]
    assert M.equal_by_construction({"R1": None}, {"R1": None}) == []


# ---- development villa (repository ledgers only)
OUT = ROOT / "research" / "agents_t556" / "out" / "T556_PLASTER_HEIGHT.json"


@pytest.fixture(scope="module")
def built():
    sys.path.insert(0, str(ROOT / "research" / "agents_t556"))
    import t556_alsenan as A
    return A.build()


def test_builder_byte_identical():
    p = subprocess.run([sys.executable, "-I", str(ROOT / "research/agents_t556/t556_alsenan.py"), "--check"],
                       capture_output=True, text=True)
    assert p.returncode == 0, p.stdout + p.stderr


def test_dev_villa_heights_and_released_lines(built):
    rows = {r["room"]: r for r in built["rows"]}
    assert rows["GF-15"]["H_floor_m"] == "4.29" and rows["1F-10"]["H_floor_m"] == "3.99"
    assert rows["GF-01"]["H_roof_scenario_m"] == "3.79" and rows["2F-03"]["H_roof_scenario_m"] == "3.99"
    # GF-15: 21.537 x 4.29 - (D 1.76 + D 2.20 + W03 5.106 x 4.29) = 66.52899 (W03 head 4.30 is above G1 3.65)
    assert Dc(rows["GF-15"]["new_lo"]) == Dc(rows["GF-15"]["new_hi"]) == Dc("66.52899")
    assert rows["GF-15"]["openings_head_above_G1"] == ["W03"]
    assert Dc(rows["1F-04"]["new_lo"]) == Dc("17.4") * Dc("3.99") - Dc("6.285")
    assert (Dc(rows["1F-01"]["new_lo"]), Dc(rows["1F-01"]["new_hi"])) == (Dc("62.573"), Dc("62.607"))
    assert Dc(rows["2F-03"]["new_lo"]) == Dc("69.775")
    assert built["released_4_lines"] == {"old": "217.2081", "new": ["262.0179900", "262.0519900"]}
    for r in built["rows"]:
        assert r["status"].startswith("HELD")
        assert "EXACT" in r["old_paint_height_basis"]["reproduction"] or r["candidate_class"] == "HELD"


def test_dev_villa_totals_and_no_line_at_paint_height(built):
    assert built["totals"]["new"] == ["840.6458100", "895.8964100"]
    plaster = {r["room"]: r["new_lo"] for r in built["rows"]}
    paint = {r["room"]: (r["old_paint_height_basis"]["value"] or [None])[0] for r in built["rows"]}
    assert M.equal_by_construction(plaster, paint) == []
    assert built["freelancer_same_rooms"]["delta"] == "81.8455000"
