"""T-629: WIRING MANIFEST V15 + OVERLAY DRY RUN (R-T629-1).

Synthetic villa K629 (not the training villa; hand values):
  0.15 m black hosts (module 40 x 20 -> 12.5 / m2; panel 0.15 x (1 - 0.39 x 0.19 x 12.5) = 0.0110625 m3 / m2):
    H1 wall K-W1 base 6.00 m2 (low 5.70: a HELD 0.30 m2 face out): units 75.00 (low 71.25), panel 0.066375 (low
      0.063056 at 6 dp), perimeter 0.0020 / 0.0021 / 0.0025 -> units SET 71.25 + companion HELD 0 .. 3.75; panel SET
      0.063056 + companion 0 .. 0.003319; perimeter ADD 0.002 + companion 0 .. 0.0005;
    H2 wall K-W2 base 4.00 m2: units 50, panel 0.04425 (points), perimeter 0.0010 / 0.0010 / 0.0012 with a dome piece
      HELD by name -> perimeter 0.001 + companion HELD 0 .. OPEN.
  landing door under a 0.75 member in a 0.16 slab, face 4.29, width 1.00: band 0.59; T-563 after 100.00 .. 120.00 ->
    101.59 .. 120.00 (deduction 0 .. 4.29 -> 0 .. 3.70).
  pantry line 10.491 walk face 32.3422 -> drawn faces 4.50 + 3.00 + 3.00 = 10.50 x 3.65 - 5.95 = 32.375 (+0.0328).
Adverse: an unmerged source; a wall kept HELD by its own cause offered; a staged line already valued; a printed figure
that does not re-derive from the rule; walls that do not re-add to the host; a summary that does not re-add; the 1.0.0
rule; a reversed perimeter; a zero / reversed range; a deduction already capped; a band at the full face; a T-563 after
off the T-556 frame; a low passing the high; no T-563 op; a stale or taken pantry line; Checker parts that do not re-add;
a chained step outside its package (R1); accessories that do not re-add. Then the training-villa build must be the
rebuild and close by hand."""

import copy
from decimal import Decimal
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research/agents_t629"))
import manifest_v15 as M          # noqa: E402

M9, OV = M.M9, M.OV
MK = {t: {"merge": "k" + t[-3:], "verdict": f"K629 {t} verdict"} for t in ("T-615", "T-617", "T-622")}
H1, H2 = "L-" + "1" * 20, "L-" + "2" * 20
E1, E2 = "GF-WALLS:walls t=0.15#BLOCKWORK:VERIFIED_BLACK", "1F-WALLS:walls t=0.15#BLOCKWORK:VERIFIED_BLACK"
U1, P1, U2, P2 = ("L-u1" + "0" * 16, "L-p1" + "0" * 16, "L-u2" + "0" * 16, "L-p2" + "0" * 16)


def _line(lid, code, unit, elem, cls="RELEASED", v=None, lo=None, hi=None):
    return {"line_id": lid, "item_code": code, "unit": unit, "element_id": elem, "class": cls, "measured_net": v,
            "held_low": lo, "held_high": hi}


def _idx():
    L = [_line(H1, "MAS.BLOCK", "m2", E1, v=6.0), _line(H2, "MAS.BLOCK", "m2", E2, v=4.0),
         _line(U1, "MAS.UNITS.BLACK", "pcs", "MATERIAL:" + E1, "HELD"),
         _line(P1, "MAS.MORTAR.BLACK", "m3", "MATERIAL:" + E1, "HELD"),
         _line(U2, "MAS.UNITS.BLACK", "pcs", "MATERIAL:" + E2, "HELD"),
         _line(P2, "MAS.MORTAR.BLACK", "m3", "MATERIAL:" + E2, "HELD")]
    return {l["line_id"]: l for l in L}


def _v4():
    return {"block_module": {"host_lines": [
        {"host_line": H1, "element_id": E1, "contract_m2": 6.0, "walls": ["K-W1"]},
        {"host_line": H2, "element_id": E2, "contract_m2": 4.0, "walls": ["K-W2"]}]}}


def _walls():
    return [
        {"wall_id": "K-W1", "line_id": H1, "area_status": "VERIFIED", "contract_m2": "6.0000",
         "material_base_m2": "6.0000", "material_base_low_m2": "5.7000", "units_nr": "75.0000", "units_nr_low": "71.2500",
         "panel_mortar_m3": "0.066375", "panel_mortar_m3_low": "0.063056", "perimeter_low_m3": "0.002000",
         "perimeter_figure_m3": "0.002100", "perimeter_high_m3": "0.002500", "perimeter_held_pieces": ""},
        {"wall_id": "K-W2", "line_id": H2, "area_status": "DRAWING-CONFIRMED", "contract_m2": "4.0000",
         "material_base_m2": "4.0000", "material_base_low_m2": "4.0000", "units_nr": "50.0000", "units_nr_low": "50.0000",
         "panel_mortar_m3": "0.044250", "panel_mortar_m3_low": "0.044250", "perimeter_low_m3": "0.001000",
         "perimeter_figure_m3": "0.001000", "perimeter_high_m3": "0.001200",
         "perimeter_held_pieces": "K dome piece: top of wall not drawn"}]


def _t615():
    return {"rule": "UPC-BLACK-BLOCK-001 1.1.0 (supersedes 1.0.0)",
            "module_015": {"installed_m": [0.4, 0.2], "units_per_m2": 12.5},
            "excluded": dict(M.EXCLUDED_WALLS),
            "units_nr": {"theoretical": 125.0, "low": 121.25},
            "panel_mortar_m3": {"material_base": 0.110625, "low": 0.107306},
            "perimeter_mortar_m3": {"low": 0.003, "figure": 0.0031, "high": 0.0037}}


def _blk(**kw):
    a = dict(t615=_t615(), walls=_walls(), v4=_v4(), idx=_idx(), merged=MK)
    a.update(kw)
    return M.block015_rows(a["t615"], a["walls"], a["v4"], a["idx"], merged=a["merged"])


def _get(rows, fix, kind, lid=None, range_of=None):
    out = [r for r in rows if r["row"] == fix and r["kind"] == kind and (lid is None or r["line_id"] == lid)
           and (range_of is None or r.get("beside", {}).get("range_of") == range_of)]
    assert len(out) == 1, (fix, kind, lid, range_of, len(out))
    return out[0]


# ---- T-615: 0.15 m black material lines ---------------------------------------------------------------------------

def test_block_normal_hand_values():
    rows, per_host, tot = _blk()
    assert M.UNITS_PER_M2 == Decimal("12.5") and M.PANEL_M3_PER_M2 == Decimal("0.0110625")
    u1 = _get(rows, "FR-T615-1", "SET", U1)
    assert u1["before"]["class"] == "HELD" and u1["after"] == M9.released(71.25)
    c1 = _get(rows, "FR-T615-1", "ADD", range_of=U1)
    assert c1["after"]["class"] == "HELD" and Decimal(str(c1["after"]["held_low"])) == 0
    assert Decimal(str(c1["after"]["held_high"])) == Decimal("3.75")
    assert _get(rows, "FR-T615-1", "SET", U2)["after"] == M9.released(50.0)
    assert not [r for r in rows if r.get("beside", {}).get("range_of") == U2]           # a point: no companion
    p1 = _get(rows, "FR-T615-2", "SET", P1)
    assert Decimal(str(p1["after"]["measured_net"])) == Decimal("0.063056")
    assert Decimal(str(_get(rows, "FR-T615-2", "ADD", range_of=P1)["after"]["held_high"])) == Decimal("0.003319")
    per1 = _get(rows, "FR-T615-3", "ADD", f"NEW:MAS.MORTAR.BLACK:PERIMETER:{H1}")
    assert Decimal(str(per1["after"]["measured_net"])) == Decimal("0.002") and per1["source"] == "T-498:perimeter"
    pc1 = _get(rows, "FR-T615-3", "ADD", range_of=f"NEW:MAS.MORTAR.BLACK:PERIMETER:{H1}")
    assert Decimal(str(pc1["after"]["held_high"])) == Decimal("0.0005")
    pc2 = _get(rows, "FR-T615-3", "ADD", range_of=f"NEW:MAS.MORTAR.BLACK:PERIMETER:{H2}")
    assert pc2["after"]["held_high"] is None and pc2["beside"]["open"] is True          # named pieces: OPEN
    assert all(r["evidence"]["status"] == M.EVID_ASSUMED for r in rows)
    assert tot["units"] == Decimal("125.0") and tot["units_low"] == Decimal("121.25")


def test_block_rows_apply_on_the_package_and_keep_held_never_zero():
    rows, _, _ = _blk()
    idx = _idx()
    after, rep = OV.apply(idx, [("T-498", rows)], M.RULINGS_V15)
    assert all(r["status"] == "APPLIED" for r in rep["rows"])
    t = OV.totals(after)
    assert t["MAS.UNITS.BLACK|pcs"]["released"] == "121.25" and t["MAS.UNITS.BLACK|pcs"]["held_high"] == "3.75"
    assert t["MAS.MORTAR.BLACK|m3"]["held_high_open_n"] == 1
    assert Decimal(t["MAS.MORTAR.BLACK|m3"]["released"]) == Decimal("0.063056") + Decimal("0.04425") + \
        Decimal("0.002") + Decimal("0.001")


def test_block_mirror_order_invariant():
    """walls listed in the other order (mirror villa): same rows by line."""
    a, _, _ = _blk()
    b, _, _ = _blk(walls=list(reversed(_walls())))
    key = lambda rs: sorted((r["op_id"], str(r["after"])) for r in rs)
    assert key(a) == key(b)


def test_block_refuses_unmerged():
    with pytest.raises(M.ManifestError, match="not MERGED"):
        _blk(merged={k: v for k, v in MK.items() if k != "T-615"})


def test_block_refuses_a_wall_kept_held_by_its_own_cause():
    w = _walls() + [dict(_walls()[0], wall_id="GF-W22")]
    with pytest.raises(M.ManifestError, match="never enters"):
        _blk(walls=w)


def test_block_refuses_a_staged_line_already_valued():
    idx = _idx()
    idx[U1].update(**{"class": "RELEASED", "measured_net": 75.0})
    with pytest.raises(M.ManifestError, match="not HELD blank"):
        _blk(idx=idx)


def test_block_refuses_a_figure_that_does_not_rederive():
    w = _walls()
    w[0]["units_nr"] = "72.0000"                     # 6.00 x 12.0 (another module): not the rule
    with pytest.raises(M.ManifestError, match="does not re-derive"):
        _blk(walls=w)


def test_block_refuses_walls_not_readding_to_the_host():
    v4 = _v4()
    idx = _idx()
    idx[H1]["measured_net"] = 6.5
    v4["block_module"]["host_lines"][0]["contract_m2"] = 6.5
    with pytest.raises(M.ManifestError, match="re-add"):
        _blk(idx=idx, v4=v4)


def test_block_refuses_a_summary_that_does_not_readd():
    t = _t615()
    t["units_nr"]["theoretical"] = 125.5
    with pytest.raises(M.ManifestError, match="the source states"):
        _blk(t615=t)


def test_block_refuses_the_old_rule_and_another_module():
    t = _t615()
    t["rule"] = "UPC-BLACK-BLOCK-001 1.0.0"
    with pytest.raises(M.ManifestError, match="1.1.0"):
        _blk(t615=t)
    t = _t615()
    t["module_015"]["installed_m"] = [0.4, 0.25]
    with pytest.raises(M.ManifestError, match="40 x 20"):
        _blk(t615=t)


def test_block_refuses_a_reversed_perimeter():
    w = _walls()
    w[0]["perimeter_figure_m3"] = "0.001000"
    with pytest.raises(M.ManifestError, match="low <= figure <= high"):
        _blk(walls=w)


def test_range_never_zero_never_reversed():
    with pytest.raises(M.ManifestError, match="positive"):
        M._ranged("P", "FR-X", "NEW:X", None, Decimal(0), Decimal(1), "E", M.MORTAR, "v", {})
    with pytest.raises(M.ManifestError, match="reversed"):
        M._ranged("P", "FR-X", "NEW:X", None, Decimal(2), Decimal(1), "E", M.MORTAR, "v", {})


def test_held_hosts_untouched_refuses_a_moved_line():
    idx = _idx()
    idx["L-x"] = _line("L-x", "MAS.UNITS.BLACK", "pcs", "MATERIAL:2F-WALLS:walls t=0.15", "HELD")
    assert [x["line"] for x in M.held_hosts_untouched(idx, _v4(), set())] == ["L-x"]
    idx["L-x"].update(**{"class": "RELEASED", "measured_net": 3.0})
    with pytest.raises(M.ManifestError, match="moved"):
        M.held_hosts_untouched(idx, _v4(), set())


# ---- FR-T617-1: the (D - t) band ---------------------------------------------------------------------------------

PL = "L-" + "9" * 20


def _t617(face="4.29", band="0.59", cap="3.7000"):
    return {"rows": [{"storey": "GF", "opening": "GF OP-K (L-K-01)",
                      "q72_plaster_for_T558": {"face_h_m": face, "always_plastered_above_head_m2": band,
                                               "check_D_minus_t": band, "deduction_cap_m2": cap},
                      "candidate_faces": {"lines": [{"line_id": PL, "item_code": "FIN.PLASTER"},
                                                    {"line_id": "L-paint", "item_code": "FIN.PAINT"}]},
                      "member_over_door": {"mark": "BK", "depth_m": "0.75"}}]}


def _t556(hi="4.290", lo="100.0", top="120.0"):
    return {"rows": [{"line_id": PL, "new": {"net_lo": lo, "net_hi": top,
                                             "openings": [{"id": "L-K-01", "lo": "0", "hi": hi}]}}]}


def _ops563(lo=100.0, hi=120.0):
    return [{"op_id": f"T-563|PLASTER_HEIGHT_V1|{PL}", "package": "T-563", "row": "PLASTER_HEIGHT_V1",
             "source": "T-563", "kind": "SET", "line_id": PL, "note": "K-08",
             "before": M9.held(90.0, 95.0), "after": M9.held(lo, hi)}]


def test_band_normal():
    rows, out = M.band_rows(_t617(), _t556(), _ops563(), merged=MK)
    r = rows[0]
    assert r["package"] == "T-563" and r["kind"] == "SET"
    assert r["before"] == M9.held(100.0, 120.0)
    assert Decimal(str(r["after"]["held_low"])) == Decimal("100.59") and r["after"]["held_high"] == 120.0
    assert out[0]["band_m2"] == "0.59"
    ops = _ops563()
    idx = {PL: _line(PL, "FIN.PLASTER", "m2", "HL:K", "HELD", lo=90.0, hi=95.0)}
    after, rep = OV.apply(idx, [("T-563", ops + rows)])
    assert all(x["status"] == "APPLIED" for x in rep["rows"])
    assert (after[PL]["held_low"], after[PL]["held_high"]) == (100.59, 120.0)


def test_band_in_another_package_is_refused_R1():
    rows, _ = M.band_rows(_t617(), _t556(), _ops563(), merged=MK)
    idx = {PL: _line(PL, "FIN.PLASTER", "m2", "HL:K", "HELD", lo=90.0, hi=95.0)}
    with pytest.raises(OV.OverlayError, match="R1"):
        OV.apply(idx, [("T-563", _ops563()), ("OTHER", [dict(rows[0], package="OTHER")])])


def test_band_refuses_an_already_capped_deduction():
    with pytest.raises(M.ManifestError, match="does not apply"):
        M.band_rows(_t617(), _t556(hi="3.700"), _ops563(), merged=MK)


def test_band_refuses_a_band_at_the_full_face():
    with pytest.raises(M.ManifestError, match="cap"):
        M.band_rows(_t617(face="0.59", band="0.59", cap="0.0000"), _t556(hi="0.590"), _ops563(), merged=MK)


def test_band_refuses_a_t563_after_off_the_t556_frame():
    with pytest.raises(M.ManifestError, match="frame"):
        M.band_rows(_t617(), _t556(), _ops563(lo=99.0), merged=MK)


def test_band_refuses_a_low_passing_the_high():
    with pytest.raises(M.ManifestError, match="pass the high"):
        M.band_rows(_t617(), _t556(lo="119.8", top="120.0"), _ops563(lo=119.8, hi=120.0), merged=MK)


def test_band_refuses_without_a_t563_op():
    with pytest.raises(M.ManifestError, match="no T-563 SET"):
        M.band_rows(_t617(), _t556(), [], merged=MK)


def test_band_refuses_unmerged():
    with pytest.raises(M.ManifestError, match="not MERGED"):
        M.band_rows(_t617(), _t556(), _ops563(), merged={"T-615": MK["T-615"]})


# ---- T-622 pantry --------------------------------------------------------------------------------------------------

def _pantry_idx(v=32.3422):
    return {M.PANTRY_LINE: _line(M.PANTRY_LINE, "FIN.WALL.TILE", "m2", "K-R#WALL_TILE:GF-07", v=v)}


def _t622(own="-32.375000"):
    return {"rows": [{"row": M.PANTRY_ROW, "stated": "-32.3422", "own": own}]}


def test_pantry_normal():
    r = M.pantry_row(_t622(), _pantry_idx(), merged=MK)
    assert r["after"] == M9.released(32.375) and r["beside"]["change_m2"] == "0.0328"
    assert r["beside"]["hand"] == "10.5 x 3.65 - 5.95 = 32.375" and r["evidence"]["status"] == "VERIFIED"


def test_pantry_refuses_stale_taken_and_unreadded():
    with pytest.raises(M.ManifestError, match="stale"):
        M.pantry_row(_t622(), _pantry_idx(32.375), merged=MK)
    with pytest.raises(M.ManifestError, match="R1"):
        M.pantry_row(_t622(), _pantry_idx(), merged=MK, taken={M.PANTRY_LINE})
    with pytest.raises(M.ManifestError, match="Checker parts"):
        M.pantry_row(_t622(own="-32.400000"), _pantry_idx(), merged=MK)


# ---- chain / listings ----------------------------------------------------------------------------------------------

def test_chain_into_keeps_the_package_and_refuses_a_missing_one():
    order = [("A", [{"op_id": "a"}]), ("B", [])]
    out = M.chain_into(order, "A", [{"op_id": "x", "package": "?"}])
    assert [n for n, _ in out] == ["A", "B"] and [o["op_id"] for o in out[0][1]] == ["a", "x"]
    assert out[0][1][1]["package"] == "A"
    with pytest.raises(M.ManifestError, match="no such package"):
        M.chain_into(order, "Z", [{"op_id": "x"}])


def test_accessories_refuse_counts_that_do_not_readd():
    t = {"ties_pcs": {"end_restated": 6, "interior_restated": 6, "ledger_measured_before": 10,
                      "ledger_measured_after": 22, "still_held_junctions": 1},
         "bed_joint_strip_ml": {"restated": "3.0", "ledger_measured_before": "1.0", "ledger_measured_after": "4.0"}}
    acc = [{"item": "MAS.TIE.SHARMAT", "wall_id": "K-W1", "now": "6"},
           {"item": "MAS.TIE.SHARMAT", "wall_id": "2F-W08", "now": "6"},
           {"item": "MAS.MESH.BED_JOINT", "wall_id": "GF-W22", "now": "3.0"}]
    out = M.accessories_listed(t, acc)
    assert {c["wall"] for c in out["conditional_on_parent_held"]} == {"2F-W08", "GF-W22"}
    bad = copy.deepcopy(t)
    bad["ties_pcs"]["ledger_measured_after"] = 23
    with pytest.raises(M.ManifestError, match="ties"):
        M.accessories_listed(bad, acc)


def test_not_merged_listed_by_name():
    s, refused = M.no_row_sources()
    assert set(refused) == {"T-624", "T-628"} and all(v["rows"] == 0 for v in s.values())


# ---- training villa ------------------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def built():
    return M.build()


def test_training_villa_is_the_committed_rebuild(built):
    assert M.OUT_JSON.read_text(encoding="utf-8") == M.dumps(built)


def test_training_villa_closes_by_hand(built):
    b = built["block_015"]
    assert b["units_pcs"]["v15"]["released"] == "3269.9375"                # 1075.8 + 2194.1375
    assert Decimal(b["units_pcs"]["v15"]["held_high"]) == Decimal("4.25")
    assert b["mortar_m3"]["v15"]["released"] == "3.387982"                 # 1.367589 + 1.941811 + 0.078582
    assert b["mortar_m3"]["v15"]["held_high_open_n"] == 2
    assert len(b["held_hosts_untouched"]) == 8
    assert built["plaster_band"]["FIN.PLASTER|m2"]["v15"]["held_low"] == "934.14581"   # 932.72581 + 1.42
    assert built["pantry"]["FIN.WALL.TILE|m2"]["v15"]["released"] == "340.3366"     # 340.3038 + 0.0328
    o = built["overlay"]
    assert o["lines"] == {"base": 4999, "after_v14": 5129, "after_v15": 5141}
    assert o["stale"] == 0 and o["unexplained_conflicts"] == 0 and o["other_lines_changed_vs_v14_overlay"] == []
    assert set(o["v15_vs_v14_totals"]) == M.WRITES
    assert built["candidate_files_touched"] == 0 and built["released_quantities_changed"] == 0
