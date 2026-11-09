"""T-631: WIRING MANIFEST V16 + OVERLAY DRY RUN (R-T631-1).

Synthetic villa K631 (not the training villa; hand values):
  beam KB1 (depth 0.80) has a drawn wedge 0.0050 m2 at column KC1, billed by no line: 0.0050 x 0.80 = 0.0040 m3,
    line 2.0000 -> 2.0040; beam KB2 (depth 0.60) wedge 0.0020 m2 -> 0.0012 m3, line 1.5000 -> 1.5012;
  beam KB3 end gap 0.0040 m2 x 0.75 = 0.0030 m3 on a line the crossing-zone package already writes: chained there,
    0.5000 -> 0.5030; the companion HELD 0 .. 0.0010 of a range closed by 'billed once' leaves as EXCLUDED;
  wash lobby face chain 8.0000 m x 3.65 - 2 doors 0.80 x 2.20 = 29.20 - 3.52 = 25.68 m2 (line 25.75 -> 25.68);
  round stair footprint F1 4.000000 + F2 2.137684 = 6.137684 vs engine 6.124412: the host floor 100.000000 ->
    99.986728; strings 0.1 + 0.1 + 0.193843 = 0.393843 -> low end 99.592885 + companion HELD 0 .. 0.393843; the 1F
    margin (5.87 + 1.6) x 0.05 = 0.3735 <= bound 0.376: companion HELD 0 .. 0.376 beside the 1F line, which stays.
Adverse: an unmerged source; a wedge billed by another line; a change that is not wedge x depth; a line another package
writes (R1); the gap line written by a package other than the crossing-zone one; a range not closed as billed once; a
stale companion; a stale GF-14 line; openings that are not the two doors; strings that do not re-add; a margin beyond
its bound; a floor line another package writes; a 'not merged' task that carries a merge. Then the training-villa build
must be the committed rebuild and close by hand."""

import copy
import os
from decimal import Decimal
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research/agents_t631"))
import manifest_v16 as M          # noqa: E402

M9, OV = M.M9, M.OV
MK = {t: {"merge": "k" + t[-3:], "verdict": f"K631 {t} verdict"} for t in ("T-622", "T-624", "T-625")}
KB1, KB2, KB3 = "L-" + "1" * 20, "L-" + "2" * 20, "L-" + "3" * 20


def _line(lid, code, unit, elem, cls="RELEASED", v=None, lo=None, hi=None):
    return {"line_id": lid, "item_code": code, "unit": unit, "element_id": elem, "class": cls, "measured_net": v,
            "held_low": lo, "held_high": hi}


# ---- T-624 --------------------------------------------------------------------------------------------------------

def _beam_idx(comp_hi=0.001295):
    L = [_line(KB1, "STR.CONC.BEAM", "m3", "HL:BEAM_LEDGER:GF:K-1#BAND1.1", v=2.0),
         _line(KB2, "STR.CONC.BEAM", "m3", "HL:BEAM_LEDGER:1F:K-2#BAND2.1", v=1.5),
         _line(KB3, "STR.CONC.BEAM", "m3", "HL:BEAM_LEDGER:GF:K-3#BAND3", v=0.5),
         _line(M.COMPANION, "STR.CONC.BEAM", "m3", "K#RANGE", "HELD", lo=0.0, hi=comp_hi)]
    return {l["line_id"]: l for l in L}


def _beam_order(gap_pkg=None):
    return [(gap_pkg or M.P_OVER, [{"line_id": KB3}, {"line_id": M.COMPANION}]), ("OTHER", [{"line_id": "L-x"}])]


def _pair(lid, col, wedge, depth, om, billed=0.0, region=0.0):
    return {"line_id": lid, "column": col, "verdict": "ENGINE_WRONG_OMISSION", "wedge_class": "DRAWN_WEDGE",
            "wedge_billed_by_any_line_m2": billed, "wedge_in_any_t229_region_m2": region, "omission_m3": om,
            "wedge_m2": wedge, "depth_m": depth, "wedge_sides_on": ["k1", "k2"]}


def _t624():
    return {
        "fix_rows": [
            {"id": "FR-T624-1", "line_id": KB1, "at": "KC1 (k)", "change_m3": 0.004, "mark": "KB1", "storey": "GF",
             "cause": "DRAWN_WEDGE (d)"},
            {"id": "FR-T624-2", "line_id": KB2, "at": "KC2 (k)", "change_m3": 0.0012, "mark": "KB2", "storey": "1F",
             "cause": "DRAWN_WEDGE (d)"},
            {"id": "FR-T624-3", "line_id": KB3, "at": "KC3 gap", "change_m3": 0.003, "mark": "KB3", "storey": "GF",
             "cause": "END_GAP (c)"}],
        "b_pairs": [_pair(KB1, "KC1", 0.005, 0.8, 0.004), _pair(KB2, "KC2", 0.002, 0.6, 0.0012)],
        "d_H1": {"line_id": KB3, "verdict": "ENGINE_WRONG_OMISSION", "held_row": "FR-T614-H1",
                 "billed_by_any_line_m2": 0.0, "m3": 0.003, "end_gap_m": 0.02, "region_m2": 0.004, "depth_m": 0.75},
        "c_B27_tip": {"state": "BILLED_ONCE_BY_OWNER", "verdict": "ENGINE_RIGHT", "companion_m3": 0.0,
                      "B27_line_id": M.B27_LINE, "tip_m2": 0.0015, "tip_in_B27_rectangle_m2": 0.0015,
                      "B27_rectangle_m2": 2.9}}


def test_t624_normal():
    wedge, chained, rulings, tot = M.t624_rows(_t624(), _beam_idx(), _beam_order(), merged=MK)
    assert [(r["line_id"], r["after"]["measured_net"]) for r in wedge] == [(KB1, 2.004), (KB2, 1.5012)]
    assert all(r["package"] == M.P_WEDGE for r in wedge) and all(r["package"] == M.P_OVER for r in chained)
    assert chained[0]["after"]["measured_net"] == 0.503 and chained[1]["after"] == M9.excluded()
    assert tot == Decimal("0.0082") and len(rulings) == 2


def test_t624_refuses_unmerged_billed_and_wrong_product():
    with pytest.raises(M.ManifestError, match="not MERGED"):
        M.t624_rows(_t624(), _beam_idx(), _beam_order(), merged={"T-622": MK["T-622"]})
    t = _t624()
    t["b_pairs"][0]["wedge_billed_by_any_line_m2"] = 0.001
    with pytest.raises(M.ManifestError, match="billed elsewhere"):
        M.t624_rows(t, _beam_idx(), _beam_order(), merged=MK)
    t = _t624()
    t["fix_rows"][0]["change_m3"] = t["b_pairs"][0]["omission_m3"] = 0.0041
    with pytest.raises(M.ManifestError, match="wedge"):
        M.t624_rows(t, _beam_idx(), _beam_order(), merged=MK)


def test_t624_refuses_r1_and_wrong_gap_writer():
    order = _beam_order() + [("SOMEONE", [{"line_id": KB1}])]
    with pytest.raises(M.ManifestError, match="chain it there"):
        M.t624_rows(_t624(), _beam_idx(), order, merged=MK)
    with pytest.raises(M.ManifestError, match="not the T-610 package"):
        M.t624_rows(_t624(), _beam_idx(), _beam_order(gap_pkg="ELSE"), merged=MK)


def test_t624_closure_needs_billed_once_and_a_live_companion():
    t = _t624()
    t["c_B27_tip"]["companion_m3"] = 0.0002
    with pytest.raises(M.ManifestError, match="billed once"):
        M.t624_rows(t, _beam_idx(), _beam_order(), merged=MK)
    with pytest.raises(M.ManifestError, match="stale"):
        M.t624_rows(_t624(), _beam_idx(comp_hi=0.0009), _beam_order(), merged=MK)


# ---- T-622 GF-14 ---------------------------------------------------------------------------------------------------

def _t622(line="25.7500", face="8.000000", own="25.680000", doors=None):
    ops = doors or [{"id": "D-GF-11", "w": "0.8", "head": "2.20"}, {"id": "D-GF-12", "w": "0.8", "head": "2.20"}]
    return {"rooms": [{"room": "GF-14", "line_id": M.GF14_LINE, "line": line, "face_lm": face, "H": "3.65",
                       "openings": ops, "own_net": own, "chain": ["k"], "open": [],
                       "line_minus_own": format(Decimal(line) - Decimal(own), "f")}]}


def _tile_idx(v=25.75):
    return {M.GF14_LINE: _line(M.GF14_LINE, "FIN.WALL.TILE", "m2", "K:wall_tile", v=v)}


def test_gf14_normal():
    r = M.gf14_row(_t622(), _tile_idx(), [], merged=MK)
    assert r["after"] == M9.released(25.68) and r["evidence"]["status"] == "DRAWING-CONFIRMED"
    assert r["beside"]["change_m2"] == "-0.07"


def test_gf14_refuses_stale_taken_and_wrong_openings():
    with pytest.raises(M.ManifestError, match="stale"):
        M.gf14_row(_t622(), _tile_idx(25.68), [], merged=MK)
    with pytest.raises(M.ManifestError, match="R1"):
        M.gf14_row(_t622(), _tile_idx(), [("P", [{"line_id": M.GF14_LINE}])], merged=MK)
    with pytest.raises(M.ManifestError, match="two 0.80"):
        M.gf14_row(_t622(doors=[{"id": "D-GF-11", "w": "0.8", "head": "2.20"}]), _tile_idx(), [], merged=MK)
    with pytest.raises(M.ManifestError, match="hand"):
        M.gf14_row(_t622(own="25.700000"), _tile_idx(), [], merged=MK)


# ---- T-625 ---------------------------------------------------------------------------------------------------------

def _t625(strings=("0.1", "0.1", "0.193843"), north="5.87"):
    parts = {"F1 band": {"area": "4.000000"}, "F2 run": {"area": "2.137684"}}
    for i, a in enumerate(strings):
        parts[f"inner string band {i}"] = {"area": a}
    return {"row0": {"own": "6.137684", "F1": "4.000000", "F2": "2.137684", "difference": "0.013272",
                     "engine_split_reproduced": {"engine_F1_F2": ["4.0", "2.124412"]},
                     "effect_if_adopted": "GF porcelain L-7625f35c -0.013272 (band)", "cause": "chords",
                     "class_proposal": {"strings": "UNRESOLVED 0 .. 0.393843 m2: k"}, "parts": parts},
            "first_floor_readings": {"slab_edge_margin": {"class_proposal": "UNRESOLVED 0 .. 0.376 m2, k",
                                                          "bound_m2": "0.376", "north_len": north,
                                                          "east_len_to_band_top": "1.6", "north_offset": "0.05"}}}


def _floor_idx():
    return {M.GF_PORC: _line(M.GF_PORC, "FIN.FLOOR.PORCELAIN", "m2", "KG:floor", v=100.0),
            M.F1_PORC: _line(M.F1_PORC, "FIN.FLOOR.PORCELAIN", "m2", "K1:floor", v=30.0)}


def test_t625_normal():
    rows, rulings, out, listed = M.t625_rows(_t625(), _floor_idx(), [], merged=MK)
    assert [r["after"] for r in rows[:2]] == [M9.released(99.986728), M9.released(99.592885)]
    assert rows[2]["after"] == M9.held(0.0, 0.393843) and rows[2]["beside"]["range_of"] == M.GF_PORC
    assert rows[3]["after"] == M9.held(0.0, 0.376) and rows[3]["beside"]["range_of"] == M.F1_PORC
    assert rows[0]["evidence"]["status"] == "VERIFIED" and rows[1]["evidence"]["status"] == "HELD"
    assert out["gf_after_low"] == "99.592885" and len(rulings) == 1 and len(listed) == 2
    after, rep = OV.apply(_floor_idx(), [(M.P_STAIR, rows)], rulings)
    assert all(r["status"] == "APPLIED" for r in rep["rows"])
    assert all(c["status"] == "EXPLAINED" for c in rep["conflicts"])


def test_t625_refuses_bad_strings_margin_and_taken_line():
    with pytest.raises(M.ManifestError, match="string bands"):
        M.t625_rows(_t625(strings=("0.1", "0.1")), _floor_idx(), [], merged=MK)
    with pytest.raises(M.ManifestError, match="exceeds its bound"):
        M.t625_rows(_t625(north="6.00"), _floor_idx(), [], merged=MK)
    with pytest.raises(M.ManifestError, match="R1"):
        M.t625_rows(_t625(), _floor_idx(), [("P", [{"line_id": M.F1_PORC}])], merged=MK)
    with pytest.raises(M.ManifestError, match="not MERGED"):
        M.t625_rows(_t625(), _floor_idx(), [], merged={"T-624": MK["T-624"]})


def test_not_merged_listed_by_name_and_refused_when_merged():
    s, refused = M.no_row_sources()
    assert set(refused) == {"T-627", "T-628"} and all(v["rows"] == 0 for v in s.values())
    with pytest.raises(M.ManifestError, match="listed as not merged"):
        M.no_row_sources(not_merged={"T-626": "x"})


# ---- training villa ------------------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def built():
    return M.build()


def test_training_villa_is_the_committed_rebuild(built):
    assert M.OUT_JSON.read_text(encoding="utf-8") == M.dumps(built)


def test_training_villa_closes_by_hand(built):
    b = built["beam_b10"]["STR.CONC.BEAM|m3"]
    assert b["v15"]["released"] == "66.392081" and b["v16"]["released"] == "66.401795"   # + 0.005245 + 0.001064 + 0.003405
    assert Decimal(b["v15"]["held_high"]) - Decimal(b["v16"]["held_high"]) == Decimal("0.001295")
    assert built["wall_tile"]["FIN.WALL.TILE|m2"]["v16"]["released"] == "340.249891"     # 340.3366 - 0.086709
    p = built["floor_porcelain"]["FIN.FLOOR.PORCELAIN|m2"]
    assert p["v15"]["released"] == "295.390972" and p["v16"]["released"] == "294.983857"  # - 0.013272 - 0.393843
    assert p["v16"]["held_high"] == "0.769843" and p["v16"]["held_n"] == 2                 # 0.393843 + 0.376
    o = built["overlay"]
    assert o["lines"] == {"base": 4999, "after_v15": 5141, "after_v16": 5143}
    assert o["stale"] == 0 and o["unexplained_conflicts"] == 0 and o["other_lines_changed_vs_v15_overlay"] == []
    assert set(o["v16_vs_v15_totals"]) == M.WRITES
    assert built["candidate_files_touched"] == 0 and built["released_quantities_changed"] == 0
    assert built["stair_edge_census_after_v16"]["doubles"] == 0


@pytest.mark.skipif(os.environ.get("URBAN_T631_WRITE") != "1", reason="writer: URBAN_T631_WRITE=1 only")
def test_write_outputs():
    b = M.write_outputs()
    assert M.OUT_JSON.exists() and b["overlay"]["lines"]["after_v16"] == 5143
