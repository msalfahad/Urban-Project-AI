"""T-274: a block wall's height pieces close its census length (rule R-T274-1, research/agents_t274/piece_close.py).

Fixture villa P (NOT Alsenan), storey basis 3.80 m (slab top above every piece), hand truth:
  P1 0.20 wall, census 6.000 m from a column face to a column face, normal to nothing:
     a 2.500 m under slab panel t 0.16           -> h 3.80 - 0.16 = 3.64 -> 9.100000
     b a beam 30x60 crossing at 30 deg from the wall normal: extent along the centreline 0.30 / cos 30 = 0.346410 m
                                                 -> h 3.80 - 0.60 = 3.20 -> 1.108513
     c 6.000 - 2.500 - 0.346410 = 3.153590 m under slab t 0.16 -> 3.64 -> 11.479067
     gross = 21.687580 m2 (mirror: same pieces in reverse order, same gross)
  adverse: b taken at its normal width 0.30 -> pieces 5.953590 m, missed strip 0.046410 m -> NOT_CLOSED, gross refused;
     a 2.55 m piece (sampled with a 0.03 m tolerance band) -> 6.050 m on a 6.000 m wall -> OVER_CENSUS;
     a weighted mean over non-closing pieces (register v2 form) -> WEIGHTED_MEAN_NOT_CLOSED;
     the 0.046410 m residual has no member drawn over it -> its own HELD piece by name: established 21.539067 + HELD,
     never 0; an unnamed HELD piece refused; pieces in millimetres (6000) on a census in metres -> OVER_CENSUS.
  P2 slivers: 0.0006 m between a slab face and a beam band joins the beam (rule 4).
  P3 opening W in a wall whose run stops on a column face at station 0: gap 0.00 .. 0.50 m (jamb on the face) -> 0.500
     deducted; adverse: gap -0.03 .. 0.47 (jamb 0.03 m inside the column, already cut from the length) -> 0.47 deducted,
     never the schedule 0.50 (the 1F-W00 W18 pattern: 0.4673 of 0.500).
  P4 corner square shared by a printed beam 20x75 and an undepthed band: candidates 0.40 / 0.75 -> h = storey - 0.75;
     a candidate 0.90 deeper than the printed member -> HELD; no candidate -> HELD.
Alsenan (Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip, ST7757 dxf.dxf): the committed outputs reproduce
from the committed piece table; 1F-W20 / 1F-W22 = the Checker's own 24.507 / 20.402 m2, 1F-W08 12.420; every cut wall
closes its census (or carries a HELD piece by name); W18 inside the masonry 0.4673 m; no coordinate in the outputs.
"""
import csv
import json
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research/agents_t274"
sys.path.insert(0, str(HERE))
import piece_close as PC  # noqa: E402

B = 0.30 / math.cos(math.radians(30))


def p1(b_len=B, a_len=2.5):
    return [{"length_m": a_len, "height_m": 3.64, "kind": "FACE"},
            {"length_m": b_len, "height_m": 3.20, "kind": "BEAM"},
            {"length_m": 6.0 - 2.5 - B, "height_m": 3.64, "kind": "FACE"}]


def test_skew_extent_hand():
    assert PC.skew_extent(0.30, 30) == pytest.approx(0.346410, abs=1e-6)
    assert PC.skew_extent(0.40, 6.91) == pytest.approx(0.4029, abs=1e-4)      # Alsenan B19 over 1F-W20 (Checker 0.403)
    with pytest.raises(PC.PieceError, match="BAD_SKEW"):
        PC.skew_extent(0.30, 89)


def test_normal_closes_and_gross():
    c = PC.close(6.0, p1())
    assert c["status"] == "CLOSED" and abs(c["residual_m"]) < 1e-9
    g = PC.gross(6.0, p1())
    assert g["status"] == "ESTABLISHED"
    assert g["established_m2"] == pytest.approx(21.687580, abs=1e-6)
    assert PC.weighted_mean_gross(6.0, p1()) == pytest.approx(21.687580, abs=1e-6)


def test_mirror_same_gross():
    assert PC.gross(6.0, list(reversed(p1())))["established_m2"] == pytest.approx(21.687580, abs=1e-6)


def test_missed_strip_found_normal_width_refused():
    ps = p1(b_len=0.30)                            # the skewed band taken at its normal width
    c = PC.close(6.0, ps)
    assert c["status"] == "NOT_CLOSED" and c["residual_m"] == pytest.approx(0.046410, abs=1e-6)
    with pytest.raises(PC.PieceError, match="NOT_CLOSED"):
        PC.gross(6.0, ps)


def test_pieces_longer_than_wall_refused():
    with pytest.raises(PC.PieceError, match="OVER_CENSUS"):
        PC.close(6.0, p1(a_len=2.55))


def test_weighted_mean_over_non_closing_refused():
    with pytest.raises(PC.PieceError, match="WEIGHTED_MEAN_NOT_CLOSED"):
        PC.weighted_mean_gross(6.0, p1(b_len=0.30))


def test_residual_without_member_held_never_zero():
    ps = p1(b_len=0.30) + [{"length_m": B - 0.30, "height_m": None, "held_item": "strip with no member drawn above"}]
    g = PC.gross(6.0, ps)
    assert g["status"] == "ESTABLISHED_PART_PLUS_HELD"
    assert g["established_m2"] == pytest.approx(9.1 + 0.96 + (6.0 - 2.5 - B) * 3.64, abs=1e-6)
    assert g["established_m2"] > 0 and g["held"][0]["length_m"] == pytest.approx(0.046410, abs=1e-6)
    ps[-1]["held_item"] = None
    with pytest.raises(PC.PieceError, match="HELD_UNNAMED"):
        PC.gross(6.0, ps)


def test_units_millimetres_refused():
    ps = [dict(p, length_m=p["length_m"] * 1000) for p in p1()]
    with pytest.raises(PC.PieceError, match="OVER_CENSUS"):
        PC.close(6.0, ps)
    with pytest.raises(PC.PieceError, match="NO_CENSUS"):
        PC.close(None, p1())


def test_slivers_join_beam():
    ps = [{"length_m": 2.0, "kind": "FACE", "height_m": 3.64}, {"length_m": 0.0006, "kind": "FACE", "height_m": None},
          {"length_m": 0.4, "kind": "BEAM", "height_m": 3.2}]
    out = PC.join_slivers(ps)
    assert len(out) == 2 and out[1]["length_m"] == pytest.approx(0.4006) and out[0]["length_m"] == 2.0


def test_opening_in_masonry_normal_and_adverse():
    assert PC.opening_in_masonry(0.0, 0.5, (0.0, 6.0), [(-0.2, 0.0)]) == pytest.approx(0.5)
    inside = PC.opening_in_masonry(-0.03, 0.47, (0.0, 6.0), [(-0.2, 0.0)])
    assert inside == pytest.approx(0.47) and inside != pytest.approx(0.5)
    # the Alsenan pattern: the drawn 0.500 gap with 0.0327 m inside the column outline -> 0.4673
    assert PC.opening_in_masonry(0.0, 0.5, (0.0, 0.5), [(0.0, 0.0327)]) == pytest.approx(0.4673)


def test_shared_corner_rule():
    assert PC.shared_corner_height(4.20, 0.75, [0.40, 0.75]) == pytest.approx(3.45)
    assert PC.shared_corner_height(4.20, 0.75, [0.40, 0.90]) is None
    assert PC.shared_corner_height(4.20, 0.75, []) is None


# ---- Alsenan (development villa) -------------------------------------------------------------------------------------
def sib():
    return {x["wall_id"]: x for x in csv.DictReader(open(HERE / "T274_SIBLING_CHECK.csv"))}


def test_outputs_reproduce():
    sys.path.insert(0, str(HERE))
    import build_t274 as BT
    o = BT.outputs()
    for k, v in o.items():
        assert (HERE / k).read_text() == v, k


def test_checker_walls_reproduced():
    s = sib()
    assert float(s["1F-W20"]["exact_gross_m2"]) == pytest.approx(24.507, abs=0.0006)     # Checker own 24.507
    assert float(s["1F-W22"]["exact_gross_m2"]) == pytest.approx(20.402, abs=0.0015)     # Checker own 20.402
    assert float(s["1F-W08"]["exact_gross_m2"]) == pytest.approx(12.420, abs=1e-4)       # uniform height
    assert float(s["GF-W07"]["exact_gross_m2"]) == pytest.approx(4.458, abs=0.0006)      # Checker VERIFIED
    for w in ("1F-W20", "1F-W22", "1F-W08"):
        assert s[w]["register_closes"] == "NO" and s[w]["exact_closes"] == "YES"


def test_every_cut_wall_closes_or_holds_by_name():
    for w, x in sib().items():
        if x["status"] in ("NOT CUT", "CLOSED (T-261)"):
            continue
        assert x["exact_closes"] == "YES", w
        assert x["status"] in ("CLOSED", "CLOSED WITH HELD PIECES"), w
        if x["status"] == "CLOSED WITH HELD PIECES":
            assert "HELD" in x["exact_gross_m2"], w


def test_w18_in_masonry_and_summary():
    s = json.loads((HERE / "summary.json").read_text())
    assert s["w18"]["in_masonry_m"] == pytest.approx(0.4673, abs=1e-4)
    assert s["w18"]["net_change_m2"] == pytest.approx(0.0706, abs=1e-4)
    assert s["applied_to_register"] is False
    assert s["opening_scan_findings"] == 1


def test_no_coordinates_in_outputs():
    for p in HERE.glob("*.csv"):
        for row in csv.reader(open(p)):
            for cell in row:
                for tok in cell.replace(";", " ").split():
                    try:
                        v = float(tok)
                    except ValueError:
                        continue
                    assert abs(v) < 100, (p.name, tok)        # drawing coordinates are hundreds of metres
