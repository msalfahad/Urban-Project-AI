"""T-619: WIRING MANIFEST V14 + OVERLAY DRY RUN (R-T619-1).

Synthetic villa K619 (not the training villa; hand values):
  passages: 4 RELEASED 1 pcs, one of them (K-P3) a lift landing door -> EXCLUDED, family 4 -> 3 pcs; one HELD-blank
    DOOR.LIFT_LANDING line added on K-P3's element (count 1 beside);
  crossing zone Z1 between beam A (0.40 deep, RELEASED 1.000 m3) and beam B (0.80 deep, RELEASED 2.000 m3), zone 0.0200
    m2: physical 0.0200 x 0.80 = 0.016000 m3; A bills 0.0150 m2 x 0.40 = 0.006000 (-> 0), B may bill 0.0050 m2 x 0.80
    = 0.004000 of it (Checker range): B change +0.012000 .. +0.016000, net +0.006000 .. +0.010000 m3;
    -> A 0.994000, B 2.012000 + companion HELD 0 .. 0.004000; B10 released 3.000 -> 3.006000 .. 3.010000;
  zone Z2 (B x C): B +0.001000, C (1.000) -0.000600: B chains 2.012000 -> 2.013000 in the SAME package;
  end piece E1 on beam D (1.500 m3): 0.10 x 0.20 = 0.02 m2 x 0.75 = +0.015000 m3 -> 1.515000.
Adverse: an unmerged source; a withdrawn row offered; a range collapsed to a point (hi = lo, or no companion, or the SET
at another point); line changes that do not re-add; a stale family base; openings that do not pair; a negative 'omission';
an end piece on a line another package writes; a host-sharing run that bills beyond its rectangle; a held piece that names
a line; a lintel cause on a released line. Then the training-villa build must be the rebuild and close by hand."""

import copy
from decimal import Decimal
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research/agents_t619"))
import manifest_v14 as M          # noqa: E402

M9, OV = M.M9, M.OV
MK = {t: {"merge": "k" + t[-3:], "verdict": f"K619 {t} verdict"} for t in ("T-608", "T-610", "T-614", "T-616")}
A, B, C, DL = ("L-" + c * 20 for c in "abcd")
P = ["L-p%019d" % i for i in range(4)]


def _line(lid, code, unit, elem, cls="RELEASED", v=None):
    return {"line_id": lid, "item_code": code, "unit": unit, "element_id": elem, "class": cls, "measured_net": v,
            "held_low": None, "held_high": None}


def _idx():
    L = [_line(p, "ARCH.PASSAGE", "pcs", f"K-GF:OP-{i}", v=1.0) for i, p in enumerate(P)]
    L += [_line(A, "STR.CONC.BEAM", "m3", "K:BEAMS:GF:A", v=1.0), _line(B, "STR.CONC.BEAM", "m3", "K:LEDGER:GF:B#1", v=2.0),
          _line(C, "STR.CONC.BEAM", "m3", "K:BEAMS:GF:C", v=1.0), _line(DL, "STR.CONC.BEAM", "m3", "K:LEDGER:GF:D#1", v=1.5),
          _line("L-" + "e" * 20, "STR.CONC.LINTEL", "m3", "LINTEL:K-01", cls="HELD")]
    return {l["line_id"]: l for l in L}


def _t608(before="4", after="3"):
    return {"fix_rows": [
        {"id": "FR-T608-1", "kind": "SET", "lines": [P[3]], "openings": ["GF OP-3"],
         "family_total": {"before": before, "after": after, "delta": "-1", "unit": "pcs"}},
        {"id": "FR-T608-2", "kind": "ADD", "lines": ["new: GF OP-3"]}]}


def _t610():
    z1 = {"zone_m2": 0.02, "owner_deeper": {"owner": B, "lines": {
        A: {"change_m3": -0.006, "engine_in_zone_m3": 0.006, "should_m3": 0.0},
        B: {"change_m3": 0.012, "engine_in_zone_m3": 0.004, "should_m3": 0.016}}}}
    return {"zones": [z1], "fix_rows": [
        {"id": "FR-K-1", "pair": "A x B", "storey": "GF", "zone_m2": 0.02, "verdict": "ENGINE_WRONG_UNDER",
         "owner_deeper": B, "engine_minus_physical_m3": -0.006, "line_changes_m3": {A: -0.006, B: 0.012}},
        {"id": "FR-K-2", "pair": "B x C", "storey": "GF", "zone_m2": 0.002, "verdict": "ENGINE_WRONG_UNDER",
         "owner_deeper": B, "engine_minus_physical_m3": -0.0004, "line_changes_m3": {B: 0.001, C: -0.0006}},
        {"id": "FR-K-3", "pair": "B x C", "storey": "GF", "zone_m2": 0.001, "verdict": "ENGINE_WRONG_DOUBLE_COUNT",
         "owner_deeper": B, "engine_minus_physical_m3": 0.0005, "line_changes_m3": {C: -0.0005}}]}


def _t614():
    return {"t610_fix_rows_r2": [{"id": "FR-K-3", "changed_by_r2": True, "zone_m2": 0.001,
                                  "billed_r2_m2": {B: 0.001, C: 0.0}, "line_changes_t610_m3": {C: -0.0005}}],
            "F_C_P02_5_r2": {"FR_K_3": {"id": "FR-K-3", "restated": "WITHDRAWN: C bills 0 of the zone"}},
            "fix_rows": [{"id": "FR-KE-1", "line_id": DL, "change_m3": 0.015, "mark": "D", "storey": "GF",
                          "column": "C9", "position": "END_LO", "piece_m2": 0.02, "depth_m": 0.75, "since": "r2"}],
            "held_rows": [{"id": "FR-KE-H1", "storey": "GF", "marks": ["D"], "column": "C8", "bound_m3": 0.002,
                           "undrawn_unbilled_m2": 0.0027, "state": "HELD"}],
            "ledger_extents": [{"line_id": "L-" + "f" * 20, "run": "D#2", "length_m": 2.0, "rect_m2": 0.6,
                                "ext_state": "NONE", "add_state": "NONE"}]}


RANGES = {"FR-K-1": B}
WD = {"FR-K-3": {"by": "T-614", "why": "K withdrawn"}}


def _over(idx=None, **kw):
    return M.overlap_rows(_t610(), _t614(), _idx() if idx is None else idx, merged=MK, ranges=RANGES, withdrawn=WD,
                          **kw)


# ---- normal --------------------------------------------------------------------------------------------------------

def test_lift_exclusion_and_held_blank_door():
    idx = _idx()
    rows = M.lift_rows(_t608(), idx, merged=MK)
    assert [(r["row"], r["kind"]) for r in rows] == [("FR-T608-1", "SET"), ("FR-T608-2", "ADD")]
    assert rows[0]["after"]["class"] == "EXCLUDED" and rows[0]["evidence"]["status"] == "DRAWING-CONFIRMED"
    assert rows[1]["after"] == M9.held() and rows[1]["element_id"] == "K-GF:OP-3" and rows[1]["unit"] == "pcs"
    after, rep = OV.apply(idx, [(M.P_LIFT, rows)])
    assert all(r["status"] == "APPLIED" for r in rep["rows"])
    t = OV.totals(after)
    assert (t["ARCH.PASSAGE|pcs"]["released"], t["ARCH.PASSAGE|pcs"]["excluded_n"]) == ("3", 1)
    assert (t["DOOR.LIFT_LANDING|pcs"]["held_blank_n"], t["DOOR.LIFT_LANDING|pcs"]["released"]) == (1, "0")


def test_range_low_end_plus_companion_and_chain():
    idx = _idx()
    rows, checks = _over(idx)
    assert [(r["row"], r["kind"], r["line_id"]) for r in rows][:3] == [("FR-K-1", "SET", A), ("FR-K-1", "SET", B),
                                                                       ("FR-K-1", "ADD", rows[2]["line_id"])]
    comp = rows[2]
    assert comp["after"]["class"] == "HELD" and Decimal(str(comp["after"]["held_high"])) == Decimal("0.004")
    b2 = [r for r in rows if r["row"] == "FR-K-2" and r["line_id"] == B][0]
    assert Decimal(str(b2["before"]["measured_net"])) == Decimal("2.012")       # chained on FR-K-1's after
    after, rep = OV.apply(idx, [(M.P_OVER, rows)])
    assert all(r["status"] == "APPLIED" for r in rep["rows"])
    assert [Decimal(str(after[k]["measured_net"])) for k in (A, B, C)] == [Decimal("0.994"), Decimal("2.013"),
                                                                           Decimal("0.9994")]
    t = OV.totals(after)["STR.CONC.BEAM|m3"]
    # 5.500 + 0.006 (Z1 low) + 0.0004 (Z2) = 5.5064 released; range companion 0 .. 0.004
    assert (t["released"], t["held_low"], t["held_high"]) == ("5.5064", "0", "0.004")
    assert [c["fix_row"] for c in checks] == ["FR-K-1", "FR-K-2"]                    # FR-K-3 withdrawn: 0 rows


def test_end_piece_and_ruling_and_held_listing():
    idx = _idx()
    idx["L-" + "f" * 20] = _line("L-" + "f" * 20, "STR.CONC.BEAM", "m3", "K:LEDGER:GF:D#2", v=0.45)
    rows, tot = M.end_rows(_t614(), idx, merged=MK)
    assert tot == Decimal("0.015") and Decimal(str(rows[0]["after"]["measured_net"])) == Decimal("1.515")
    rul = M.end_rulings(_t614(), idx, rows)
    after, rep = OV.apply(idx, [(M.P_END, rows)], rul)
    assert [c["status"] for c in rep["conflicts"]] == ["EXPLAINED"]
    _, rep0 = OV.apply(idx, [(M.P_END, rows)])
    assert [c["status"] for c in rep0["conflicts"]] == ["UNEXPLAINED"]                 # without the ruling
    h = M.held_not_wired(_t614())
    assert h[0]["bound_m3"] == "0 .. 0.002" and h[0]["wired"].startswith("NO")


def test_withdrawn_listing():
    w = M.withdrawn_check(_t614(), WD)
    assert w["FR-K-3"]["rows"] == 0 and w["FR-K-3"]["by"] == "T-614"


# ---- adverse --------------------------------------------------------------------------------------------------------

def test_unmerged_source_refused():
    with pytest.raises(M.ManifestError, match="not MERGED"):
        M.lift_rows(_t608(), _idx(), merged={})
    with pytest.raises(M.ManifestError, match="not MERGED"):
        M.overlap_rows(_t610(), _t614(), _idx(), merged={}, ranges=RANGES, withdrawn=WD)
    with pytest.raises(M.ManifestError, match="not MERGED"):
        M.end_rows(_t614(), _idx(), merged={})
    with pytest.raises(M.ManifestError, match="not MERGED"):
        M.lintel_rows(_idx(), merged={})


def test_withdrawn_row_offered_refused():
    t = _t610()
    with pytest.raises(M.ManifestError, match="withdrawn by T-614"):
        _over(offered=t["fix_rows"])
    with pytest.raises(M.ManifestError, match="not in the withdrawn list"):
        M.overlap_rows(t, _t614(), _idx(), merged=MK, ranges=RANGES, withdrawn={})
    t14 = _t614()
    t14["F_C_P02_5_r2"]["FR_K_3"]["restated"] = "kept"
    with pytest.raises(M.ManifestError, match="does not withdraw"):
        M.withdrawn_check(t14, WD)


def test_range_collapsed_to_point_refused():
    t = _t610()
    t["zones"][0]["owner_deeper"]["lines"][B].update(should_m3=0.012, engine_in_zone_m3=0.0)
    with pytest.raises(M.ManifestError, match="a point or reversed"):
        M.overlap_rows(t, _t614(), _idx(), merged=MK, ranges=RANGES, withdrawn=WD)
    rows, _ = _over()
    no_comp = [r for r in rows if r["kind"] != "ADD"]
    with pytest.raises(M.ManifestError, match="collapsed to a point"):
        M.validate_ranges(no_comp, RANGES)
    moved = copy.deepcopy(rows)
    s = next(r for r in moved if r["row"] == "FR-K-1" and r["line_id"] == B)
    s["after"]["measured_net"] = 2.016                                              # the high end as a point
    with pytest.raises(M.ManifestError, match="not by the low end"):
        M.validate_ranges(moved, RANGES)
    wide = copy.deepcopy(rows)
    next(r for r in wide if r["kind"] == "ADD")["after"]["held_high"] = 0.0
    with pytest.raises(M.ManifestError, match="companion is not HELD"):
        M.validate_ranges(wide, RANGES)


def test_line_changes_must_re_add():
    t = _t610()
    t["fix_rows"][1]["line_changes_m3"][C] = -0.0005
    with pytest.raises(M.ManifestError, match="re-add"):
        M.overlap_rows(t, _t614(), _idx(), merged=MK, ranges=RANGES, withdrawn=WD)


def test_lift_adverse():
    with pytest.raises(M.ManifestError, match="stale"):
        M.lift_rows(_t608(before="5", after="4"), _idx(), merged=MK)
    with pytest.raises(M.ManifestError, match="!= the source's after"):
        M.lift_rows(_t608(after="2"), _idx(), merged=MK)
    t = _t608()
    t["fix_rows"][1]["lines"] = ["new: GF OP-2"]
    with pytest.raises(M.ManifestError, match="one landing door per excluded line"):
        M.lift_rows(t, _idx(), merged=MK)
    idx = _idx()
    idx[P[3]]["measured_net"] = 2.0
    with pytest.raises(M.ManifestError, match="counts 1 pcs"):
        M.lift_rows(_t608(), idx, merged=MK)


def test_end_adverse():
    t = _t614()
    t["fix_rows"][0]["change_m3"] = -0.015
    with pytest.raises(M.ManifestError, match="not an add"):
        M.end_rows(t, _idx(), merged=MK)
    with pytest.raises(M.ManifestError, match="another package"):
        M.end_rows(_t614(), _idx(), merged=MK, taken={DL})
    idx = _idx()
    idx["L-" + "f" * 20] = _line("L-" + "f" * 20, "STR.CONC.BEAM", "m3", "K:LEDGER:GF:D#2", v=0.45)
    rows, _ = M.end_rows(_t614(), idx, merged=MK)
    t = _t614()
    t["ledger_extents"][0]["add_state"] = "MATCHED"
    with pytest.raises(M.ManifestError, match="not its own rectangle"):
        M.end_rulings(t, idx, rows)
    t = _t614()
    t["held_rows"][0]["line_id"] = DL
    with pytest.raises(M.ManifestError, match="names an owning line"):
        M.held_not_wired(t)


def test_lintel_adverse(monkeypatch):
    monkeypatch.setattr(M, "LINTEL_LINE", "L-" + "e" * 20)
    with pytest.raises(M.ManifestError, match="not the P-GF-01"):
        M.lintel_rows(_idx(), merged=MK)


# ---- training villa: rebuild + hand closure ------------------------------------------------------------------------

@pytest.fixture(scope="module")
def built():
    return M.build()


def test_committed_output_is_the_rebuild(built):
    assert M.OUT_JSON.read_text(encoding="utf-8") == M.dumps(built)


def test_overlay_clean(built):
    o = built["overlay"]
    assert o["lines"] == {"base": 4999, "after_v13": 5125, "after_v14": 5129}
    assert o["stale"] == 0 and o["unexplained_conflicts"] == 0 and o["other_lines_changed_vs_v13_overlay"] == []
    assert [f["package"] for f in o["flagged_rows"]] == ["T-498"]          # T-580's own NO_BEFORE, not a V14 row
    assert sorted(o["v14_vs_v13_totals"]) == ["ARCH.PASSAGE|pcs", "DOOR.LIFT_LANDING|pcs", "STR.CONC.BEAM|m3"]
    assert built["stair_edge_census_after_v14"] == {"edges": 89, "doubles": 0, "orphans": 0}


def test_acceptance_by_hand(built):
    assert built["passage"]["ARCH.PASSAGE|pcs"]["v14"]["released"] == "6"
    assert built["skirting"]["FIN.SKIRTING|lm"]["released"] == "198.558592"
    b = built["beam_b10"]
    t610 = (Decimal("-0.005295") + Decimal("0.011252")) + (Decimal("0.003137") - Decimal("0.002768")) + \
        (Decimal("0.009375") - Decimal("0.00625"))
    t614 = Decimal("0.002137") + Decimal("0.01875") + Decimal("0.002309") + Decimal("0.0375") + Decimal("0.00088")
    assert (t610, t614) == (Decimal("0.009451"), Decimal("0.061576"))
    rel = Decimal("66.321054") + t610 + t614
    assert b["STR.CONC.BEAM|m3"]["v14"]["released"] == format(rel, "f") == "66.392081"
    assert Decimal("0.014761") * Decimal("0.85") - Decimal("0.011252") == Decimal("0.00129485")   # width 0.001295
    assert b["after_total_range_m3"].startswith("66.392081 .. 66.393376")
    assert Decimal(b["STR.CONC.BEAM|m3"]["v14"]["held_high"]) - Decimal(b["STR.CONC.BEAM|m3"]["v13"]["held_high"]) \
        == Decimal("0.001295")


def test_rows_sources(built):
    assert [r["row"] for r in built["rows"]] == ["FR-T608-1"] * 3 + ["FR-T608-2"] * 3 + \
        ["FR-T610-1"] * 3 + ["FR-T610-2"] * 2 + ["FR-T610-4"] * 2 + \
        ["FR-T614-1", "FR-T614-2", "FR-T614-3", "FR-T614-4", "FR-T614-5", "FR-T616-1"]
    assert set(built["sources_no_row"]) == {"T-612", "T-617"} and built["sources_refused"] == {}
    assert list(built["withdrawn"]) == ["FR-T610-3"]
    assert [h["id"] for h in built["held_not_wired"]] == ["FR-T614-H1"]
    assert built["candidate_files_touched"] == 0 and built["released_quantities_changed"] == 0
