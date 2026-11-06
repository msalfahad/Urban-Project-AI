"""T-580: MANIFEST OVERLAY DRY RUN (R-T580-1). Generic overlay on a synthetic 5-line villa (not Alsenan; hand values)
with two manifests applied in order (normal) and the adverse cases: two packages on one line id refused, a stated
before that differs from the index flagged STALE (both values, row not applied), HELD printed as 0 refused, a double
count refused, a recode that moves a quantity refused, a missing before flagged, units kept apart, an open bound never
summed as 0. Then the training-villa dry run (research/agents_t580/out/OVERLAY_T580.json) must be the rebuild and close
by hand on the figures the V6 / V7 / V8 manifests print."""

import copy
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research/agents_t580"))
import overlay as OV              # noqa: E402
import t580_alsenan as T          # noqa: E402


def _l(lid, code, el, cls="RELEASED", net=None, unit="m2", lo=None, hi=None):
    return {"line_id": lid, "item_code": code, "unit": unit, "element_id": el, "class": cls, "measured_net": net,
            "held_low": lo, "held_high": hi}


def _st(cls="RELEASED", net=None, lo=None, hi=None):
    return {"class": cls, "measured_net": net, "held_low": lo, "held_high": hi}


def _op(pkg, row, kind, lid, before=None, after=None, code=None, el=None, unit="m2", src=None):
    o = {"op_id": f"{pkg}|{row}|{lid}", "package": pkg, "row": row, "kind": kind, "line_id": lid, "before": before,
         "after": after, "source": src or pkg}
    if code:
        o.update(item_code=code, element_id=el, unit=unit)
    return o


@pytest.fixture
def villa():
    # synthetic villa V580: one room R1 4.00 x 3.00 m, walls 2 x (4 + 3) x 3.00 = 42.00 m2 plaster, one opening
    return {l["line_id"]: l for l in [
        _l("L-1", "FIN.PLASTER", "R1:plaster", net=42.0),
        _l("L-2", "FIN.PAINT", "R1:paint", net=40.32),                       # 42.00 - 1.20 x 1.40 window
        _l("L-3", "FIN.FLOOR.PORCELAIN", "R1:floor", net=12.0),
        _l("L-4", "ARCH.WINDOW", "R1:OP-1", cls="HELD", lo=1.68, hi=2.10),
        _l("L-5", "STR.REBAR", "R1:slab:REBAR", cls="HELD", unit="kg"),
    ]}


def _two_manifests():
    m1 = [_op("P1", "PLASTER_HEIGHT", "SET", "L-1", _st(net=42.0), _st("HELD", lo=45.6, hi=46.8)),   # 2 x 7 x 3.26 .. 3.34
          _op("P1", "RETURN", "ADD", "NEW:R1:OP-1:RETURN_PAINT", None, _st("HELD"), "FIN.PAINT", "R1:OP-1:RETURN_PAINT")]
    m2 = [_op("P2", "W1", "SET", "L-4", _st("HELD", lo=1.68, hi=2.10), _st(net=1.68)),                 # 1.20 x 1.40
          _op("P2", "RECODE", "RECODE", "L-3", dict(_st(net=12.0), item_code="FIN.FLOOR.PORCELAIN"),
              dict(_st(net=12.0), item_code="FIN.FLOOR.WET_TILE"))]
    return [("P1", m1), ("P2", m2)]


# ---- synthetic: normal ------------------------------------------------------------------------------------------------

def test_normal_two_manifests_apply_in_order(villa):
    before = copy.deepcopy(villa)
    after, rep = OV.apply(villa, _two_manifests())
    assert villa == before                                                   # a COPY is overlaid, never the input
    assert [r["status"] for r in rep["rows"]] == ["APPLIED"] * 4
    assert after["L-1"]["class"] == "HELD" and after["L-1"]["held_low"] == 45.6
    assert after["L-4"]["class"] == "RELEASED" and after["L-4"]["measured_net"] == 1.68
    assert after["L-3"]["item_code"] == "FIN.FLOOR.WET_TILE" and after["L-3"]["measured_net"] == 12.0
    assert after["L-2"] == villa["L-2"] and after["L-5"] == villa["L-5"]      # every other line byte-identical
    t = OV.totals(after)
    assert t["FIN.PLASTER|m2"]["released"] == "0" and t["FIN.PLASTER|m2"]["held_low"] == "45.6"
    assert t["FIN.PAINT|m2"]["released"] == "40.32" and t["FIN.PAINT|m2"]["held_blank_n"] == 1
    assert t["ARCH.WINDOW|m2"]["released"] == "1.68" and t["ARCH.WINDOW|m2"]["held_n"] == 0
    s1 = rep["steps"][0]["totals_changed"]
    assert set(s1) == {"FIN.PLASTER|m2", "FIN.PAINT|m2"}                      # per step: only what that package moves


def test_open_high_counted_open_never_zero_and_units_apart(villa):
    ops = [_op("P", "BARS", "ADD", "NEW:bars", None, _st("HELD", lo=38.761728), "STR.REBAR", "R1:lintel:REBAR", "kg"),
           _op("P", "BARS", "ADD", "NEW:bars-m", None, _st("HELD", lo=1.0), "STR.REBAR", "R1:lintel:REBAR", "m")]
    after, _ = OV.apply(villa, [("P", ops)])
    t = OV.totals(after)
    assert t["STR.REBAR|kg"]["held_high_open_n"] == 1 and t["STR.REBAR|kg"]["held_high"] == "0"
    assert t["STR.REBAR|kg"]["held_blank_n"] == 1 and t["STR.REBAR|m"]["held_n"] == 1   # same code, other unit: apart


# ---- synthetic: adverse ---------------------------------------------------------------------------------------------

def test_adverse_two_rows_on_one_id_refused(villa):
    pk = _two_manifests()
    pk[1][1].append(_op("P2", "LATE", "SET", "L-1", _st("HELD", lo=45.6, hi=46.8), _st("HELD", lo=40.0, hi=41.0)))
    with pytest.raises(OV.OverlayError, match="R1 TWO_ROWS_ONE_LINE"):
        OV.apply(villa, pk)
    pk = _two_manifests()
    pk[0][1].append(copy.deepcopy(pk[0][1][0]))
    with pytest.raises(OV.OverlayError, match="R1"):
        OV.apply(villa, pk)


def test_adverse_before_mismatch_flagged_stale_not_applied(villa):
    pk = _two_manifests()
    pk[0][1][0]["before"] = _st(net=41.5)
    after, rep = OV.apply(villa, pk)
    r = rep["rows"][0]
    assert r["status"] == "STALE" and r["stated_before"]["measured_net"] == 41.5 and r["index"]["measured_net"] == 42.0
    assert after["L-1"] == villa["L-1"] and rep["steps"][0]["stale"] == 1


def test_adverse_held_printed_as_zero_refused(villa):
    for after in (_st("HELD", net=0), _st("HELD", lo=0, hi=0), _st(net=0)):
        pk = [("P", [_op("P", "X", "SET", "L-4", _st("HELD", lo=1.68, hi=2.10), after)])]
        with pytest.raises(OV.OverlayError, match="R2"):
            OV.apply(villa, pk)
    with pytest.raises(OV.OverlayError, match="R2"):
        OV.apply(villa, [("P", [_op("P", "X", "ADD", "NEW:x", None, _st(net=0.0), "STR.REBAR", "R1:x", "kg")])])
    with pytest.raises(OV.OverlayError, match="R2 RELEASED_BLANK"):
        OV.apply(villa, [("P", [_op("P", "X", "ADD", "NEW:x", None, _st(), "STR.REBAR", "R1:x", "kg")])])


def test_held_low_zero_with_a_bound_is_not_zero(villa):
    ok = [("P", [_op("P", "X", "ADD", "NEW:p", None, _st("HELD", lo=0.0, hi=0.78), "FIN.PAINT", "R1:OP-1:J")])]
    after, _ = OV.apply(villa, ok)
    assert after["NEW:p"]["held_high"] == 0.78


def test_adverse_double_count_and_existing_id_refused(villa):
    with pytest.raises(OV.OverlayError, match="R3 DOUBLE_COUNT"):
        OV.apply(villa, [("P", [_op("P", "X", "ADD", "NEW:f", None, _st(net=12.0), "FIN.FLOOR.PORCELAIN",
                                    "R1:floor")])])
    with pytest.raises(OV.OverlayError, match="R3 ADD_EXISTS"):
        OV.apply(villa, [("P", [_op("P", "X", "ADD", "L-2", None, _st(net=1.0), "FIN.PAINT", "R9:paint")])])


def test_adverse_recode_moving_quantity_refused(villa):
    bad = [("P", [_op("P", "R", "RECODE", "L-3", dict(_st(net=12.0), item_code="FIN.FLOOR.PORCELAIN"),
                      dict(_st(net=11.0), item_code="FIN.FLOOR.WET_TILE"))])]
    with pytest.raises(OV.OverlayError, match="RECODE_MOVES_QUANTITY"):
        OV.apply(villa, bad)


def test_missing_before_and_missing_line_flagged(villa):
    pk = [("P", [_op("P", "X", "SET", "L-5", None, _st("HELD", lo=10, hi=20)),
                 _op("P", "Y", "SET", "L-404", _st(net=1.0), _st(net=2.0))])]
    after, rep = OV.apply(villa, pk)
    assert [r["status"] for r in rep["rows"]] == ["NO_BEFORE", "MISSING_LINE"]
    assert after["L-5"] == villa["L-5"]


def test_cross_trade_conflict_needs_a_named_ruling(villa):
    pk = [("A", [_op("A", "M", "ADD", "NEW:m1", None, _st(net=0.5), "MAS.MORTAR.BLACK", "MATERIAL:R1-WALLS:w t=0.20#X",
                     "m3")]),
          ("B", [_op("B", "P", "ADD", "NEW:m2", None, _st(net=0.04), "MAS.MORTAR.BLACK", "R1-WALLS:w t=0.20#Y", "m3")])]
    _, rep = OV.apply(villa, pk)
    assert rep["conflicts"][0]["status"] == "UNEXPLAINED" and rep["conflicts"][0]["sources"] == ["A", "B"]
    rule = {"layer": "MAS.MORTAR", "host_re": r"^R1-WALLS:", "sources": ["A", "B"], "ruling": "own key",
            "fix_row": "B step 1"}
    _, rep = OV.apply(villa, pk, [rule])
    assert rep["conflicts"][0]["status"] == "EXPLAINED" and rep["conflicts"][0]["fix_row"] == "B step 1"


def test_text_only_and_beside_never_move_or_own_a_line(villa):
    pk = [("P", [_op("P", "T", "TEXT_ONLY", "L-2", _st(net=40.32)),
                 _op("P", "B", "BESIDE", "L-5", _st("HELD"))])]
    after, rep = OV.apply(villa, pk)
    assert after == villa and rep["conflicts"] == []


# ---- the training villa (committed output) --------------------------------------------------------------------------

@pytest.fixture(scope="module")
def out():
    return T.build()


@pytest.fixture(scope="module")
def m():
    return T.manifests()


def test_committed_output_is_the_rebuild(out):
    assert T.dumps(out) == T.OUT_JSON.read_text(encoding="utf-8")


def test_edited_manifest_refused(monkeypatch):
    monkeypatch.setitem(T.PINS, T.V["V8"], "0" * 64)
    with pytest.raises(OV.OverlayError, match="PIN"):
        T.manifests()


def test_order_lines_and_flags(out):
    assert [o["package"] for o in out["order"]][:5] == ["T-498", "T-423 r2", "T-563", "T-513",
                                                       "FLOOR_FINISH_COMPLETENESS_WIRING"]
    assert out["lines"] == {"before": 4999, "after": 4999 + 74 + 2 + 2 + 3 + 30 - 1 + 6 + 8}
    assert [r["line_id"] for r in out["flagged_rows"]] == ["L-4ccc5dc26bd2472b03ad"]       # NO_BEFORE, named
    assert out["flagged_rows"][0]["status"] == "NO_BEFORE"
    assert all(s["stale"] == 0 for s in out["steps"]) and out["unexplained_conflicts"] == 0


def test_plaster_paint_window_by_hand(out):
    t = out["totals_changed_overall"]
    assert t["FIN.PLASTER|m2"]["before"]["released"] == "580.5819"
    assert Decimal(t["FIN.PLASTER|m2"]["after"]["released"]) == Decimal("580.5819") - (
        Decimal("56.0131") + Decimal("51.415") + Decimal("52.005") + Decimal("57.775"))      # 363.3738
    assert t["FIN.PAINT|m2"]["before"]["released"] == t["FIN.PAINT|m2"]["after"]["released"] == "217.2081"
    assert t["FIN.PAINT|m2"]["after"]["held_n"] - t["FIN.PAINT|m2"]["before"]["held_n"] == 30
    assert Decimal(t["ARCH.WINDOW|m2"]["after"]["released"]) - Decimal(t["ARCH.WINDOW|m2"]["before"]["released"]) \
        == Decimal("3.29") * Decimal("3.00")


def test_floor_classes_equal_v7_restated(out, m):
    t, r = out["totals_changed_overall"], m["V7"]["fix_rows"]["t553_restated"]
    assert t["FIN.FLOOR.PORCELAIN|m2"]["before"]["released"] == "305.020973"
    assert t["FIN.FLOOR.PORCELAIN|m2"]["after"]["released"] == "295.390972"
    assert t["FIN.FLOOR.WET_TILE|m2"]["after"]["released"] == "85.575578"
    assert t["FIN.FLOOR.FINISH_HELD|m2"]["after"]["released"] == "9.0975"
    assert r["total_after_m2"] == "390.064050"


def test_masonry_mortar_is_stage_plus_perimeter(out):
    t = out["totals_changed_overall"]["MAS.MORTAR.BLACK|m3"]["after"]
    assert Decimal(t["released"]) == Decimal("1.269444") + Decimal("0.039291") + Decimal("0.058854")


def test_lintel_lines_move_to_held_with_their_low_ends(out):
    t = out["totals_changed_overall"]["STR.CONC.LINTEL|m3"]
    assert t["before"]["released"] == "1.016" and t["after"]["released"] == "0"
    assert Decimal(t["after"]["held_low"]) == Decimal("0.054") * 3 + Decimal("0.051") + Decimal("0.195") + \
        Decimal("0.094")                                                                     # the 6 BEARING_OK ends


def test_census_and_bindings_close_on_the_overlaid_index(out, m):
    c = out["census_after"]
    hits = m["V7"]["floor_census"]["after_hits"]
    assert c["C1"] == hits["C1"] and c["C2"] == hits["C2"] == 0 and c["C4"] == 0
    assert {k: v[1] for k, v in c["C3"].items()} == {"1F": "COVERED", "2F": "COVERED", "GF": "COVERED"}
    assert c["return_pairs_ok"] is True
    for b in out["bindings"].values():
        assert b["before_stale"] == [] and b["after_mismatch"] == []
    assert out["bindings"]["T-563 (T-454 / T-489 plaster)"]["rows"] == 132
    assert out["block_module_r_t533_1"]["not_held_blank"] == []


def test_adverse_real_line_written_by_two_packages_refused(m):
    idx, st = T.base_index(), T.stage()
    pk = T.packages(m, idx, st)
    v8 = dict(pk)["W17_Q76A"]
    v8.append(T._op("W17_Q76A", "LATE", "SET", "L-0d93f2209cd9bb827c0a", T.released(56.0131), T.held(60, 70)))
    with pytest.raises(OV.OverlayError, match="R1"):
        OV.apply(idx, pk, T.RULINGS)


def test_adverse_real_stale_before_flagged(m):
    idx, st = T.base_index(), T.stage()
    idx["L-ba28ba2da13f62445c9f"]["measured_net"] = 23.0                                      # index moved under W17
    _, rep = OV.apply(idx, T.packages(m, idx, st), T.RULINGS)
    r = next(x for x in rep["rows"] if x["line_id"] == "L-ba28ba2da13f62445c9f")
    assert r["status"] == "STALE" and r["stated_before"]["measured_net"] == 23.285 and r["index"]["measured_net"] == 23.0


def test_stage_extract_consistent():
    s = T.stage()
    assert len(s["rows"]) == 74 and s["source"]["commit"].startswith("e3e2ebb5")
    for key, v in s["totals_moved_by_code"].items():
        code, unit = key.split("|")
        assert sum(1 for r in s["rows"] if r["item_code"] == code and r["unit"] == unit) == v["v3_0_58"]["lines"]


def test_f_package_roof_membrane_equals_t541_engine(out, m):
    t = out["totals_changed_overall"]["FIN.WP.ROOF|m2"]
    mem = m["V4"]["roof_consistency"]["membrane"]
    assert Decimal(t["before"]["released"]) == Decimal(str(mem["candidate_v3_0_58_released"]))
    assert Decimal(t["after"]["released"]) == Decimal(str(mem["t541_engine"]))        # 209.018867 + 0.639573
