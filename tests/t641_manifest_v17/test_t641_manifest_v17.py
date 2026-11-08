"""T-641: WIRING MANIFEST V17 + OVERLAY DRY RUN (R-T641-1).

Synthetic villa K641 (not the training villa; hand values):
  floor K-R1: porcelain 50.000000 m2, bed 50.000000 m2, bed mortar 1.500000 .. 2.000000 m3 (x 0.03 / 0.04). The finish
    steps -0.010000 (footprint) then -0.200000 (range low end) with a companion HELD 0 .. 0.200000: the bed takes 49.990000
    then 49.790000 + HELD 0 .. 0.200000; the mortar 1.499700 .. 1.999600 then 1.493700 .. 1.991600 + HELD 0 .. 0.008000
    (0.2 x 0.04). Floor K-R2: finish and bed 20.000000, mortar 0.6 .. 0.8, finish companion 0 .. 0.100000 only: bed
    companions 0 .. 0.100000 m2 / 0 .. 0.004000 m3 with a ruling, bed and mortar lines unchanged.
  band: held 7.0 .. 7.0 (unsupported) -> free 60.0 x 0.20 x 0.40 = 4.8 .. centre line 80.0 x 0.20 x 0.60 = 9.6 m3.
  formwork: shaft 0.25 x 0.50 column perimeter 1.50 x (4.50 - 0.75) = 5.625 (method 5.626) + joint companion HELD 0.3 ..
    0.3; split face 0.5 m2 on a member whose two concrete lines are RELEASED.
  rebar: 8 T16 x 4.50 m x 256 / 162 = 56.888889 kg.
  finish: a return paint line 0 .. plaster face 0.78 (plaster RELEASED 0.78), chained in RETURN_PAINT_FACES.
Adverse: a finish moved without its bed (refused by the acceptance); a bed not equal to its finish before; a mortar
range that is not the bed x 0.03 / 0.04; a bed line another package writes; a stale band; a band range that is not the
drawing product; a face whose concrete is HELD; a shaft without its companion; a bar row whose kg is not n x L x d^2/162;
a return paint whose high end is not its plaster face; an unmerged source; a 'not merged' task that carries a merge.
Then the training-villa build must be the committed rebuild and close by hand."""

import copy
import os
from decimal import Decimal
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research/agents_t641"))
import manifest_v17 as M          # noqa: E402

M9, OV = M.M9, M.OV
MK = {t: {"merge": "k" + t[-3:], "verdict": f"K641 {t} verdict"}
      for t in ("T-625", "T-628", "T-638", "T-639", "T-640")}
F1, F2 = "L-" + "a" * 20, "L-" + "b" * 20
B1, B1M, B2, B2M = "L-" + "c" * 20, "L-" + "d" * 20, "L-" + "e" * 20, "L-" + "f" * 20


def _line(lid, code, unit, elem, cls="RELEASED", v=None, lo=None, hi=None):
    return {"line_id": lid, "item_code": code, "unit": unit, "element_id": elem, "class": cls, "measured_net": v,
            "held_low": lo, "held_high": hi}


# ---- bed follows finish -------------------------------------------------------------------------------------------

def _floor_idx(bed1=50.0, mortar1=(1.5, 2.0)):
    L = [_line(F1, "FIN.FLOOR.PORCELAIN", "m2", "K-R1:floor", v=50.0),
         _line(B1, "FIN.FLOOR.BED.DRY", "m2", "K-R1:floor:bed", v=bed1),
         _line(B1M, "FIN.FLOOR.BED.DRY", "m3", "K-R1:floor:bed", "HELD", lo=mortar1[0], hi=mortar1[1]),
         _line(F2, "FIN.FLOOR.PORCELAIN", "m2", "K-R2:floor", v=20.0),
         _line(B2, "FIN.FLOOR.BED.DRY", "m2", "K-R2:floor:bed", v=20.0),
         _line(B2M, "FIN.FLOOR.BED.DRY", "m3", "K-R2:floor:bed", "HELD", lo=0.6, hi=0.8)]
    return {l["line_id"]: l for l in L}


def _stair_rows():
    P = M.P_STAIR
    r = [M9.row(P, "FR-K-1", "SET", F1, M9.released(50.0), M9.released(49.99), "VERIFIED", "v"),
         M9.row(P, "FR-K-2", "SET", F1, M9.released(49.99), M9.released(49.79), "HELD", "v"),
         M9.row(P, "FR-K-2", "ADD", "NEW:K1", None, M9.held(0.0, 0.2), "HELD", "v", code="FIN.FLOOR.PORCELAIN",
                unit="m2", elem="K-R1:floor#FR-K-2:RANGE", beside={"range_of": F1}),
         M9.row(P, "FR-K-3", "ADD", "NEW:K2", None, M9.held(0.0, 0.1), "HELD", "v", code="FIN.FLOOR.PORCELAIN",
                unit="m2", elem="K-R2:floor#FR-K-3:RANGE", beside={"range_of": F2})]
    return r


def _floor_run(idx=None, order=()):
    idx = idx or _floor_idx()
    stair = _stair_rows()
    moves = M.finish_moves(stair, (F1, F2))
    rows, rulings, hand = M.bed_rows(idx, idx, list(order), moves, merged=MK)
    return idx, stair, rows, rulings, hand


def test_bed_follows_normal():
    idx, stair, rows, rulings, hand = _floor_run()
    fin_rule = {"layer": "FIN.FLOOR", "host_re": "^K-R2:floor$", "sources": ["CANDIDATE", M.P_STAIR], "ruling": "k",
                "fix_row": "FR-K-3"}
    after, rep = OV.apply(idx, [(M.P_STAIR, stair), (M.P_BED, rows)], rulings + [fin_rule])
    assert after[B1]["measured_net"] == 49.79 and after[B2]["measured_net"] == 20.0
    assert (after[B1M]["held_low"], after[B1M]["held_high"]) == (1.4937, 1.9916)          # 49.79 x 0.03 / 0.04
    comp = sorted((l["unit"], l["held_high"]) for l in after.values() if l["element_id"].startswith("K-R")
                  and ":bed#" in l["element_id"])
    assert comp == [("m2", 0.1), ("m2", 0.2), ("m3", 0.004), ("m3", 0.008)]
    assert all(c["status"] == "EXPLAINED" for c in rep["conflicts"]) and len(rulings) == 1
    ok = M.bed_follows(after, (F1, F2))
    assert ok[0]["bed"] == "49.79" and ok[0]["mortar_m3"] == ["1.4937", "1.9916"]
    mid = [r for r in rows if r["row"] == "FR-K-1/MORTAR"][0]["after"]
    assert (mid["held_low"], mid["held_high"]) == (1.4997, 1.9996)                         # 49.99 x 0.03 / 0.04


def test_finish_moved_without_its_bed_is_refused():
    idx, stair, rows, rulings, _ = _floor_run()
    after, _ = OV.apply(idx, [(M.P_STAIR, stair)], [])
    with pytest.raises(M.ManifestError, match="moved without its bed"):
        M.bed_follows(after, (F1, F2))
    only_line = [r for r in rows if r["kind"] == "SET"]                                  # bed moved, companions not
    after2, _ = OV.apply(idx, [(M.P_STAIR, stair), (M.P_BED, only_line)], [])
    with pytest.raises(M.ManifestError, match="companions"):
        M.bed_follows(after2, (F1, F2))


def test_bed_refuses_unequal_bed_wrong_thickness_and_r1():
    with pytest.raises(M.ManifestError, match="is not the finish"):
        _floor_run(_floor_idx(bed1=49.5, mortar1=(1.485, 1.98)))
    with pytest.raises(M.ManifestError, match="Q-45"):
        _floor_run(_floor_idx(mortar1=(1.0, 2.5)))                                       # 0.02 .. 0.05: not the line's
    with pytest.raises(M.ManifestError, match="R1"):
        _floor_run(order=[("OTHER", [{"line_id": B1}])])
    idx = _floor_idx()
    with pytest.raises(M.ManifestError, match="not MERGED"):
        M.bed_rows(idx, idx, [], M.finish_moves(_stair_rows(), (F1, F2)), merged={})


# ---- band -----------------------------------------------------------------------------------------------------------

def _band(old=7.0, lo="4.8", hi="9.6"):
    t628 = {"fix_rows": [{"id": "F-T628-1", "statement_engine_bounded": ["77.1204", "77.8432"],
                          "corrected_engine_bounded": [str(Decimal("77.1204") - Decimal(str(old)) + Decimal(lo)),
                                                       str(Decimal("77.8432") - Decimal(str(old)) + Decimal(hi))]}],
            "lines": {"T-551/footing-line": {"rows": [{"evidence": {
                "held_line": M.BAND_LINE, "held_line_bound_m3": str(old), "free_m": "60.0", "centre_line_m": "80.0",
                "downgrade": "DG-k", "crossings": "k", "quoted_bound": {"bound": [lo, hi], "replaced": str(old),
                                                                        "basis": "k"}}}]}}}
    idx = {M.BAND_LINE: _line(M.BAND_LINE, *M.BAND, "K:BAND", "HELD", lo=7.0, hi=7.0)}
    return t628, idx


def test_band_normal_and_adverse():
    t628, idx = _band()
    r, out = M.band_row(t628, idx, [], merged=MK)
    assert (r["after"]["held_low"], r["after"]["held_high"]) == (4.8, 9.6) and r["after"]["class"] == "HELD"
    assert out["footing_line"] == ["74.9204", "80.4432"]
    with pytest.raises(M.ManifestError, match="not free x 0.20"):
        M.band_row(_band(lo="5.0")[0], idx, [], merged=MK)
    stale = copy.deepcopy(idx)
    stale[M.BAND_LINE]["held_high"] = 7.5
    with pytest.raises(M.ManifestError, match="stale"):
        M.band_row(t628, stale, [], merged=MK)


# ---- formwork, rebar, finish ----------------------------------------------------------------------------------------

FW1, FW2, C1, C2, C3 = ("L-" + c * 20 for c in "12345")


def _fw(c_class="RELEASED", companion=True):
    blank = {"class": "HELD", "measured_net": None, "held_low": None, "held_high": None}
    shaft = {"class": "A_FIX", "line_id": FW1, "concrete_line": C1, "checks": [{"method_m2": "5.626", "hand_m2": "5.625"}],
             "fix": {"id": "FR-K-1", "kind": "RELEASE_LOW_END", "before": blank, "basis": "k",
                     "after": {"class": "RELEASED", "measured_net": "5.626"},
                     "companion": {"class": "HELD", "held_low": "0.3", "held_high": "0.3", "faces": ["J"], "cause": "k"}
                     if companion else None}}
    split = {"class": "A_FIX", "line_id": FW2, "concrete_line": None, "member": "BEAM:K", "member_lines": [C2, C3],
             "fix": {"id": "FR-K-2", "kind": "RELEASE", "before": blank, "basis": "k", "companion": None,
                     "after": {"class": "RELEASED", "measured_net": "0.5"}}}
    t638 = {"lines": [shaft, split], "counts": {"by_class": {"A_FIX": 2}, "fix_rows": 2, "released_m2": "6.126000"}}
    idx = {FW1: _line(FW1, "STR.FORMWORK", "m2", "FW:K1", "HELD"), FW2: _line(FW2, "STR.FORMWORK", "m2", "FW:K2", "HELD"),
           C1: _line(C1, "STR.CONC.COLUMN", "m3", "K:C1", v=0.5), C2: _line(C2, "STR.CONC.BEAM", "m3", "K:B", v=1.0),
           C3: _line(C3, "STR.CONC.BEAM", "m3", "K:B2", c_class, v=1.0 if c_class == "RELEASED" else None)}
    return t638, idx


def test_formwork_normal_and_adverse():
    t638, idx = _fw()
    rows, out = M.formwork_rows(t638, idx, [], merged=MK)
    assert out == {"shafts_m2": "5.626", "split_m2": "0.5", "total_m2": "6.126"}
    assert [r["evidence"]["status"] for r in rows] == ["VERIFIED", "HELD", "PARTIALLY VERIFIED"]
    after, _ = OV.apply(idx, [(M.P_FW, rows)])
    assert OV.totals(after)["STR.FORMWORK|m2"]["released"] == "6.126"
    with pytest.raises(M.ManifestError, match="not RELEASED"):
        M.formwork_rows(*_fw(c_class="HELD"), [], merged=MK)
    with pytest.raises(M.ManifestError, match="companion"):
        M.formwork_rows(*_fw(companion=False), [], merged=MK)


def _bars(kg="56.888889"):
    lid = "L-" + "9" * 20
    rows = [{"fix_row": f"FR-T639-{i}", "line_id": lid if i == 1 else f"L-{i}" + "8" * 19, "count": 8, "dia_mm": 16,
             "length_m": "4.50", "kg": kg, "kg_per_m": "1.580247", "element_id": f"K:COL{i}", "column": f"C{i}",
             "mark": "C4", "printed": "k", "formula": "8 x 4.50 x 1.580247"} for i in range(1, 7)]
    idx = {r["line_id"]: _line(r["line_id"], "STR.REBAR", "kg", r["element_id"], "HELD") for r in rows}
    return {"fix_rows": rows}, idx


def test_bars_normal_and_adverse():
    t639, idx = _bars()
    rows, out = M.bars_rows(t639, idx, [], merged=MK)
    assert out["kg"] == "341.333334" and rows[0]["after"]["measured_net"] == 56.888889       # 6 x 56.888889
    with pytest.raises(M.ManifestError, match="d\\^2/162"):
        M.bars_rows(_bars(kg="57.0")[0], _bars(kg="57.0")[1], [], merged=MK)


def _fin(high="0.78", plaster=0.78):
    PL, PT = "L-" + "7" * 20, "NEW:FIN.PAINT:K-OP:RETURN_PAINT"
    rec = {"class": "A_BOUND", "line_id": PT, "cause": "k", "family": "B4-06",
           "fix": {"id": "FR-K-1", "kind": "SET", "before": {"class": "HELD"}, "basis": f"0 .. plaster face ({PL})",
                   "after": {"class": "HELD", "held_low": "0", "held_high": high}}}
    t640 = {"lines": [rec], "counts": {"by_class": {"A_BOUND": 1}}, "fix_bound_total_m2": ["0", high]}
    idx = {PT: _line(PT, "FIN.PAINT", "m2", "K-OP:RETURN_PAINT", "HELD"),
           PL: _line(PL, "FIN.PLASTER", "m2", "K-OP:RETURN", v=plaster)}
    order = [(M.P_RET, [{"line_id": PT}])]
    return t640, idx, order


def test_finish_normal_and_adverse():
    own, chained, listed, out = M.finish_rows(*_fin(), merged=MK)
    assert not own and chained[0]["package"] == M.P_RET and out == {"low": "0", "high": "0.78"}
    with pytest.raises(M.ManifestError, match="plaster face"):
        M.finish_rows(*_fin(plaster=0.70), merged=MK)


def test_not_merged_listed_by_name_and_refused_when_merged():
    _, refused = M.no_row_sources(merged={"T-1": {"merge": "x", "verdict": "y"}}, no_row={"T-1": "k"},
                                  not_merged={"T-2": "READY"})
    assert refused["T-2"]["refusal"].startswith("T-2 is not MERGED")
    with pytest.raises(M.ManifestError, match="carries a merge"):
        M.no_row_sources(merged={"T-2": {"merge": "x", "verdict": "y"}}, no_row={}, not_merged={"T-2": "READY"})


# ---- training villa -------------------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def built():
    return M.build()


def test_training_villa_is_the_committed_rebuild(built):
    assert M.OUT_JSON.read_text(encoding="utf-8") == M.dumps(built)


def test_training_villa_closes_by_hand(built):
    o = built["overlay"]
    assert o["lines"] == {"base": 4999, "after_v16": 5143, "after_v17": 5151}               # + 4 bed + 4 joint companions
    assert o["stale"] == 0 and o["unexplained_conflicts"] == 0 and o["other_lines_changed_vs_v16_overlay"] == []
    bed = built["bed"]["totals"]["FIN.FLOOR.BED.DRY|m2"]
    assert bed["v16"]["released"] == "304.488472" and bed["v17"]["released"] == "304.081357"  # - 0.013272 - 0.393843
    assert bed["v17"]["held_high"] == "0.769843"                                              # 0.393843 + 0.376
    m3 = built["bed"]["totals"]["FIN.FLOOR.BED.DRY|m3"]
    assert m3["v17"]["held_low"] == "9.12244" and m3["v17"]["held_high"] == "12.194048"
    assert [b["bed"] for b in built["bed"]["after_v17"]] == ["109.071302", "33.411036"]
    assert built["band"]["range"] == ["5.6392", "11.0328"] and built["band"]["footing_line"] == ["75.5392", "81.6556"]
    fw = built["formwork"]
    assert (fw["shafts_m2"], fw["split_m2"], fw["total_m2"]) == ("27.002", "6.125058", "33.127058")
    assert fw["totals"]["STR.FORMWORK|m2"]["v17"]["released"] == "1061.104461"
    rb = built["rebar"]["totals"]["STR.REBAR|kg"]
    assert rb["v16"]["released"] == "9375.30576" and rb["v17"]["released"] == "9787.750205"  # 6 lines at 6 dp
    assert built["finish_bounds"]["low"] == "87.234" and built["finish_bounds"]["high"] == "138.53962"
    assert built["rows_by_evidence"] == {"HELD": 45, "PARTIALLY VERIFIED": 51, "VERIFIED": 10}
    assert built["candidate_files_touched"] == 0 and built["released_quantities_changed"] == 0
    assert built["stair_edge_census_after_v17"]["doubles"] == 0


@pytest.mark.skipif(os.environ.get("URBAN_T641_WRITE") != "1", reason="writer: URBAN_T641_WRITE=1 only")
def test_write_outputs():
    b = M.write_outputs()
    assert M.OUT_JSON.exists() and b["overlay"]["lines"]["after_v17"] == 5151
