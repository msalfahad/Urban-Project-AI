"""ALSENAN ROUND 3 - structural rebar truth engine.

1. KNOWN-ANSWER fixtures: the expected values are hand-derived (count x length x D^2/162 written out in the test),
   never produced by calling the production code.
2. MUTATIONS: each corrupts one thing in a small synthetic build and must trip one named invariant.
3. GATES (G11, G13, G24-G31; G15 / G23 stay strict XFAIL) on the frozen Round-3 registers.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
LAB = ROOT / "research" / "external_engine_lab"
R3DIR = ROOT / "research" / "alsenan_rebar_truth_03"
REGS = R3DIR / "registers"
for p in (str(LAB), str(ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

import alsenan_rebar_v3 as R3  # noqa: E402
from engine.source import rebar_model as RM  # noqa: E402

K8, K12, K14, K16, K18 = 64 / 162, 144 / 162, 196 / 162, 256 / 162, 324 / 162


def _reg(n):
    return json.loads((REGS / f"{n}.json").read_text())


# =============================================================================================== synthetic build
def _bar(n, d, per_m=False, tags=("A-B", "A-D"), semantics=None):
    b = {"count": n, "dia_mm": d, "per_m": per_m, "grammar": "COUNT_DIA_PER_M" if per_m else "COUNT_DIA",
         "tags": list(tags), "raw": [str(n), str(d)]}
    if semantics:
        b["semantics"] = semantics
    return b


def _df(element, typ, fields, raw=None, block="X", handle="H1"):
    return {"element": element, "type": typ, "block": block, "insert_handle": handle, "page": 9,
            "raw_attributes": raw or {}, "fields": fields, "interpretation_state": "INTERPRETED"}


STIR = "STIRRUPS_PER_METRE (schedule header)"
F8 = _df("FOOTING_2_LAYER", "F8", {"L_cm": 400.0, "W_cm": 360.0, "D_cm": 50.0,
                                   "TOP_short": _bar(6, 14, True), "TOP_long": _bar(6, 14, True),
                                   "BOTTOM_short": _bar(9, 14, True), "BOTTOM_long": _bar(9, 14, True)},
         {"SH-T-B": "6", "SH-T-D": "14/m", "LO-T-B": "6", "LO-T-D": "14/m", "SH-B-B": "9", "SH-B-D": "14/m",
          "LO-B-B": "9", "LO-B-D": "14/m", "BOXED-T": "TOP"}, block="FTB")
FF = _df("FOOTING_2_LAYER", "FF", {"L_cm": 460.0, "W_cm": 450.0, "D_cm": 55.0,
                                   "TOP_short": _bar(6, 14, True), "TOP_long": _bar(6, 14, True),
                                   "BOTTOM_short": _bar(9, 14, True), "BOTTOM_long": _bar(9, 14, True)}, block="FTB",
         handle="H2")
FT = _df("FOOTING", "F", {"L_cm": 90.0, "W_cm": 80.0, "D_cm": 30.0, "short_bars": _bar(8, 12), "long_bars": _bar(7, 12),
                          "boxed": {"raw_boxed_value": "3+4", "interpretation": "BLOCKED_SEMANTICS"}},
         {"SH-B": "8", "SH-D": "12", "LO-B": "7", "LO-D": "12", "BOXED": "3+4"}, block="FT", handle="H3")
SB1 = _df("STRAP_BEAM", "SB1", {"B_cm": 70.0, "H_cm": 50.0, "bottom": _bar(7, 16), "top": _bar(13, 18),
                                "stirrups_per_m": _bar(8, 8, semantics=STIR)}, block="SBT", handle="H4")
SB2a = _df("STRAP_BEAM", "SB2", {"B_cm": 100.0, "H_cm": 50.0, "bottom": _bar(10, 16), "top": _bar(20, 18),
                                 "stirrups_per_m": _bar(10, 8, semantics=STIR)}, block="SBT", handle="H5")
SB2b = _df("STRAP_BEAM", "SB2", {"B_cm": 80.0, "H_cm": 50.0, "bottom": _bar(10, 18), "top": _bar(10, 18),
                                 "stirrups_per_m": _bar(10, 8, semantics=STIR)}, block="SBT", handle="H6")
B1 = _df("SIMPLE_BEAM", "B1", {"B_cm": 20.0, "H_cm": 40.0, "bottom": _bar(2, 14), "top": _bar(2, 12),
                               "stirrups_per_m": _bar(6, 8, semantics=STIR)}, block="SBT", handle="H7")
B7 = _df("SIMPLE_BEAM", "B7", {"B_cm": 20.0, "H_cm": 75.0, "bottom": _bar(3, 16), "top": _bar(2, 12),
                               "stirrups_per_m": _bar(6, 8, semantics=STIR)}, block="SBT", handle="H8")
CB1 = _df("CONTINUOUS_BEAM", "CB1", {"B_cm": 20.0, "H_cm": 50.0, "spans_m": [6.0, 4.0],
                                     "stirrups_per_span": [_bar(7, 8, semantics=STIR), _bar(6, 8, semantics=STIR)]},
          {"BOT1-B": "3", "BOT1-D": "16", "BOT2-B": "3", "BOT2-D": "16", "MID-B": "4", "MID-D": "16"}, block="C-BEAM2",
          handle="H9")
COL = _df("COLUMN", "C", {"bands": {"GR": {"B_cm": 20.0, "H_cm": 50.0, "bars": _bar(8, 16, tags=("GR.R", "GR.D"))}}},
          {"GR.R": "8", "GR.D": "16"}, block="CGT", handle="H10")


def _lab(tag, count, dia, x, kind="ATTRIBUTE", **kw):
    return dict({"tag": tag, "count": count, "dia": dia, "x": x, "kind": kind}, **kw)


def _gbar(h, ua, ub, role, label, legs=(), straddle=()):
    return {"handle": h, "u_start": ua, "u_end": ub, "start_at_support": ua == int(ua), "end_at_support": ub == int(ub),
            "row": "BOTTOM" if role == "BOTTOM" else "TOP_ROW", "straddles_supports": list(straddle), "role": role,
            "legs": [{"x": 0, "drawn_length": 300}] * len(legs), "label": label,
            "binding": "ONE_TO_ONE_PRINTED"}


CB1_FRAME = {"block": "C-BEAM2", "insert_handle": "H9", "support_lines": [0, 1000, 2000], "spans_drawn": [1000, 1000],
             "stirrup_zone_dims": [], "unbound_printed_labels": [],
             "bars": [_gbar("b1", 0.0, 1.1, "BOTTOM", _lab("BOT1", "3", "16", 500)),
                      _gbar("b2", 0.9, 2.0, "BOTTOM", _lab("BOT2", "3", "16", 1500)),
                      _gbar("s1", 0.7, 1.3, "SUPPORT_TOP", _lab("MID", "4", "16", 1000), straddle=(1,)),
                      _gbar("t1", 0.0, 0.9, "CONTINUOUS_TOP", _lab("CALLOUT@1", "2", "12", 400, "LOOSE_CALLOUT",
                                                                   handles=["a", "b", "c"]), legs=(1,)),
                      _gbar("t2", 1.1, 2.0, "CONTINUOUS_TOP", _lab("CALLOUT@2", "2", "12", 1500, "LOOSE_CALLOUT",
                                                                   handles=["d", "e", "f"]), legs=(1,))]}


def _bare(defs, ctx, conflicts=()):
    b = R3.Build.__new__(R3.Build)
    b.ctx, b.sha = ctx, "f" * 64
    b.comps, b.pops, b.rc_occ = [], [], []
    b.registers = defaultdict(list)
    b.dmap = defaultdict(list)
    for d in defs:
        b.dmap[(d["element"], d["type"])].append(d)
    b.defs = {"definitions": list(defs), "conflicts": [{"key": k} for k in conflicts]}
    b.src = {"loose": [{"handle": "T1", "raw": "ST. OF COLUMN 6%%C8/m"}]}
    b.cbg = {"frames": {"CB1": CB1_FRAME}}
    return b


def _occ(typ, Ls, Lc, tag="H100", state="MEASURED"):
    return {"type": typ, "state": state, "tags": [f"X|{tag}|"], "B_cm": 20, "D_cm": 40,
            "lengths": {"SUPPORT_CENTRELINE_LENGTH": Ls, "CLEAR_FACE_TO_FACE_LENGTH": Lc}}


def _ctx():
    return {"a3": {"footings": {"rows": [{"type": "F8", "status": "COMPUTED_SHADOW_COMPLETE", "mark_key": "X|H20|"},
                                         {"type": "F", "status": "COMPUTED_SHADOW_COMPLETE", "mark_key": "X|H21|"}]},
                   "straps": {"rows": [{"type": "SB1", "mark_key": "X|H30|", "length_m": 4.0},
                                       {"type": "SB2", "mark_key": "X|H31|", "length_m": 2.0}]}},
            "b2a": {"sheets": {"GF": {"occurrences": [_occ("B1", 4.2, 4.0), _occ("B7", 5.2, 5.0, tag="H101"),
                                                      _occ("CB1", 10.0, 9.6, tag="H102")]}},
                    "columns": {"rows": [{"floor": "GF", "storey_band": "GROUND FLOOR", "type": "C",
                                          "tag_key": "X|H40|", "state": "PROVEN", "volume_m3": 0.375, "height_m": 3.75},
                                         {"floor": "GF", "storey_band": "GROUND FLOOR", "type": "C",
                                          "tag_key": "X|H41|", "state": "NOT_DRAWN_ON_STOREY_SHEET", "volume_m3": None}]},
                    "intervals": [{"from": "GF", "interval_m": 4.5}]},
            "v3b": {"struct": {"slab": {"rows": [{"floor": "GF", "annotation": "A1", "text": "6%%c12/m", "state": "BOUND",
                                                  "dia_mm": 12, "n": 6, "kind": "PER_M", "top": False, "count": 19,
                                                  "length_mm": 3500.0, "width_mm": 3000.0}]}}}}


def _mini():
    b = _bare([F8, FT, SB1, SB2a, SB2b, B1, B7, CB1, COL], _ctx(), conflicts=("SB2",))
    b._tb_binding = lambda: {"bound": {"A1": {"qualifier": "Q1"}}, "rows": [], "dedupe_audit": []}
    b.footings()
    b.straps()
    b.simple_beams()
    b.continuous_beams()
    b.columns()
    b.slabs()
    return b


def _comp(b, suffix):
    return next(c for c in b.comps if c["comp_id"].endswith(suffix))


def _inv(b):
    v = R3.project_invariants(b)
    v["completeness"] = RM.check_completeness(b.rc_occ, b.pops, b.comps)
    v["duplicates"] = RM.check_duplicates(b.comps, b.pops)
    v["provenance"] = RM.check_provenance(b.comps)
    return v


def _codes(v):
    return {x[0] for vs in v.values() for x in vs}


# =============================================================================================== 1. known answers
def test_unit_weights_d2_over_162_and_density_qa_only():
    for d, want in ((8, 0.395062), (10, 0.617284), (12, 0.888889), (14, 1.209877), (16, 1.580247), (18, 2.0),
                    (20, 2.469136), (25, 3.858025)):
        assert RM.kgm(d) == pytest.approx(want, abs=1e-6)
    assert RM.kgm_density_qa(8) == pytest.approx(0.394584, abs=1e-6)
    assert RM.ratio_qa(100.0, volume_m3=2.0)["use"] == "QA_ONLY"


def test_ka01_single_layer_footing():
    b = _bare([FT], {})
    cs = b._ft("P", "O", FT, 0.9, 0.8, 0.07)
    ver = sum(c["verified_kg"] for c in cs)
    assert ver == pytest.approx((8 * 0.66 + 7 * 0.76) * K12)          # 9.422222
    assert ver == pytest.approx(9.422222, abs=1e-6)
    assert _comp_role(cs, "BOXED_COMPONENT_UNKNOWN_SEMANTICS")["state"] == "BLOCKED"


def _comp_role(cs, role):
    return next(c for c in cs if c["bar_role"] == role)


def test_ka02_two_layer_footing_bars_per_metre():
    b = _bare([F8], {})
    cs = b._ftb("P", "O", F8, 4.0, 3.6, 0.5, 0.07)
    want = {"TOP_SHORT": (24, 25, 100.468148), "TOP_LONG": (21, 22, 98.072593), "BOTTOM_SHORT": (35, 36, 146.516049),
            "BOTTOM_LONG": (32, 33, 149.443951)}
    for role, (n, nc, kg) in want.items():
        c = _comp_role(cs, role)
        assert c["count_mode"] == "BARS_PER_METRE"
        assert (c["count"]["verified"], c["count"]["convention"]) == (n, nc)
        assert c["verified_kg"] == pytest.approx(kg, abs=1e-5)
    assert sum(c["verified_kg"] for c in cs) == pytest.approx(494.500741, abs=1e-5)


def test_ka03_ff_straight_mesh_lower_bound_with_blocked_pit():
    b = _bare([FF], {})
    cs = b._ftb("P", "O", FF, 4.6, 4.5, 0.55, 0.07, lift=True)
    mesh = sum(c["verified_kg"] for c in cs if c["bar_role"] in ("TOP_SHORT", "TOP_LONG", "BOTTOM_SHORT", "BOTTOM_LONG"))
    assert mesh == pytest.approx((27 * 4.36 + 27 * 4.46 + 41 * 4.36 + 40 * 4.46) * K14)   # 720.239506
    assert _comp_role(cs, "LIFT_PIT_WALLS")["state"] == "BLOCKED"
    assert _comp_role(cs, "PERIMETER_CLOSURE_LEGS")["state"] == "PROVISIONAL"
    p = RM.population(pop_id="P", element_type="FOOTING_LIFT", occurrence_id="O", level="F",
                      occurrence_state="ESTABLISHED", components=cs)
    assert p["release_state"] == RM.LB


def test_ka04_strap_sb1():
    b = _bare([SB1], {"a3": {"straps": {"rows": [{"type": "SB1", "mark_key": "X|H1|", "length_m": 4.0}]}}})
    b.straps()
    cs = b.comps
    assert _comp_role(cs, "BOTTOM")["verified_kg"] == pytest.approx(7 * 4 * K16)          # 44.246914
    assert _comp_role(cs, "TOP")["verified_kg"] == pytest.approx(13 * 4 * K18)             # 104.0
    st = _comp_role(cs, "STIRRUPS")
    assert (st["count"]["verified"], st["count"]["convention"]) == (32, 33)
    assert st["verified_kg"] == pytest.approx(32 * 1.84 * K8)                               # 23.261235
    assert b.pops[0]["lower_bound_kg"] == pytest.approx(171.508148, abs=1e-5)


def test_ka05_simple_beam():
    b = _bare([B1], {"b2a": {"sheets": {"GF": {"occurrences": [_occ("B1", 4.2, 4.0)]}}}})
    b.simple_beams()
    assert b.pops[0]["lower_bound_kg"] == pytest.approx(2 * 4 * K14 + 2 * 4 * K12 + 24 * 1.0 * K8)   # 26.271605
    assert _comp_role(b.comps, "SIDE_BARS")["state"] == "NOT_REQUIRED"


def test_ka06_two_span_continuous_beam():
    b = _bare([CB1], {"b2a": {"sheets": {"GF": {"occurrences": [_occ("CB1", 10.0, 9.6, tag="H102")]}}}})
    b.continuous_beams()
    p = b.pops[0]
    assert p["occurrence_state"] == "ESTABLISHED" and p["release_state"] == RM.LB
    cs = {c["comp_id"].rsplit("|", 1)[1]: c for c in b.comps}
    assert cs["b1"]["verified_kg"] == pytest.approx(3 * 6.0 * K16) and cs["b1"]["provisional_kg"] == pytest.approx(3 * 0.4 * K16)
    assert cs["b2"]["verified_kg"] == pytest.approx(3 * 4.0 * K16) and cs["b2"]["provisional_kg"] == pytest.approx(3 * 0.6 * K16)
    assert cs["s1"]["provisional_kg"] == pytest.approx(4 * 3.0 * K16) and cs["s1"]["verified_kg"] == 0
    assert cs["t1"]["provisional_kg"] == pytest.approx(2 * 5.4 * K12) and cs["t1"]["state"] == "PROVISIONAL"
    stir = [c for c in b.comps if c["bar_role"] == "STIRRUPS"]
    assert [c["count"]["verified"] for c in stir] == [40, 22]                               # zones 5.6 m / 3.6 m
    assert p["lower_bound_kg"] == pytest.approx(76.8, abs=1e-6)


def test_ka07_three_span_normalised_geometry():
    core, ext, pieces = R3.span_split(0.933, 2.195, [3.4, 3.3, 3.8])
    assert core == pytest.approx(3.3) and ext == pytest.approx(0.067 * 3.4 + 0.195 * 3.8)   # 0.9688
    assert [p["kind"] for p in pieces] == ["EXTENSION", "CORE", "EXTENSION"]


def test_ka08_column():
    b = _bare([COL], {"b2a": {"columns": {"rows": [_ctx()["b2a"]["columns"]["rows"][0]]},
                              "intervals": [{"from": "GF", "interval_m": 4.5}]}})
    b.columns()
    assert _comp_role(b.comps, "VERTICAL")["verified_kg"] == pytest.approx(8 * 4.5 * K16)   # 56.888889
    t = _comp_role(b.comps, "TIES")
    assert t["count"]["verified"] == 23 and t["verified_kg"] == pytest.approx(23 * 1.2 * K8)  # 10.903704
    assert _comp_role(b.comps, "VERTICAL")["bbs_addition_m"] == pytest.approx(40 * 16 / 1000)


def test_ka09_slab_annotation_count_split():
    b = _bare([], {})
    r = _ctx()["v3b"]["struct"]["slab"]["rows"][0]
    c = b._slab_comp(r, "P|A1", "BOTTOM", {"drawing": "x", "drawing_sha256": "f", "locator": "TEXT:A1", "raw": "r",
                                           "normalised": {}}, dict(population_id="P", element_type="SLAB",
                                                                    occurrence_id="SLAB:GF", level="GF",
                                                                    cover_rule_id="COVER-MEMBER-25"), {"bound": {}})
    assert (c["count"]["verified"], c["count"]["convention"]) == (18, 19)
    assert c["verified_kg"] == pytest.approx(18 * 3.5 * K12) and c["provisional_kg"] == pytest.approx(3.5 * K12)


def test_ka10_stirrup_count_rule():
    a = RM.bar_count("BARS_PER_METRE", 7, 5.6)
    assert (a["verified"], a["convention"]) == (40, 41)                  # ceil(39.2); ceil(5600 / 142.857) + 1
    e = RM.bar_count("BARS_PER_METRE", 5, 4.0)
    assert (e["verified"], e["convention"]) == (20, 21)
    s = RM.bar_count("SPACING_MM", 200, 3.0)
    assert (s["verified"], s["convention"]) == (15, 16)
    with pytest.raises(ValueError):
        RM.bar_count("ABSOLUTE_COUNT", 2.5)


def test_ka11_bar_longer_than_stock_needs_a_lap_authority():
    lp = RM.lap_parts(15.0, 16, lap_factor=70, lap_rule_id="LAP-TENSION-70D")
    assert lp["state"] == "COMPLETE" and lp["laps"] == 1 and lp["lap_m"] == pytest.approx(1.12)
    assert lp["pieces"] == pytest.approx([12.0, 4.12])
    assert RM.lap_parts(15.0, 16)["state"] == "BLOCKED"                  # no authority -> BLOCKED_LAP_METHOD
    assert RM.lap_parts(11.9, 16)["state"] == "NOT_REQUIRED"


def test_ka12_population_missing_one_component_is_a_lower_bound():
    ok = RM.component(comp_id="a", population_id="P", element_type="X", occurrence_id="O", level="GF",
                      bar_role="MAIN", dia_mm=12, count=RM.bar_count("ABSOLUTE_COUNT", 4),
                      parts=[RM.part("CORE", 3.0, "COMPLETE", "r")], cover_rule_id="C", formula="f")
    miss = RM.blocked_component(comp_id="b", population_id="P", element_type="X", occurrence_id="O", level="GF",
                                bar_role="SIDE", why="not printed")
    p = RM.population(pop_id="P", element_type="X", occurrence_id="O", level="GF", occurrence_state="ESTABLISHED",
                      components=[ok, miss])
    assert p["release_state"] == RM.LB and p["lower_bound_kg"] == pytest.approx(4 * 3 * K12)
    assert p["verified_complete_kg"] == 0 and p["missing_components"] == ["b"]
    full = RM.population(pop_id="P", element_type="X", occurrence_id="O", level="GF", occurrence_state="ESTABLISHED",
                         components=[ok])
    assert full["release_state"] == RM.VC


# =============================================================================================== 2. mutations
def test_mini_build_is_clean():
    v = _inv(_mini())
    assert not any(v.values()), {k: x for k, x in v.items() if x}


def test_mut01_remove_cb_support_bar():
    b = _mini()
    b.comps = [c for c in b.comps if not (c["element_type"] == "CONTINUOUS_BEAM" and c["bar_role"] == "SUPPORT_TOP")]
    assert "CB_BAR_NOT_ACCOUNTED_ONCE" in _codes(_inv(b))


def test_mut02_diameter_changed():
    b = _mini()
    next(c for c in b.comps if c["comp_id"].endswith("STRAP:SB1:H30|TOP"))["dia_mm"] = 16
    assert "DIAMETER_DIFFERS_FROM_SOURCE" in _codes(_inv(b))


def test_mut03_per_metre_read_as_absolute():
    b = _mini()
    _comp(b, "|TOP_SHORT")["count_mode"] = "ABSOLUTE_COUNT"
    assert "PER_METRE_READ_AS_COUNT" in _codes(_inv(b))


def test_mut04_swap_footing_layers():
    b = _mini()
    t, bo = _comp(b, "|TOP_SHORT"), _comp(b, "|BOTTOM_SHORT")
    t["source"], bo["source"] = bo["source"], t["source"]
    assert "FTB_LAYER_DIFFERS_FROM_SOURCE_TAG" in _codes(_inv(b))


def test_mut05_drop_one_ftb_layer():
    b = _mini()
    b.comps = [c for c in b.comps if not c["comp_id"].endswith("|BOTTOM_LONG")]
    assert "FTB_LAYER_MISSING" in _codes(_inv(b))


def test_mut06_duplicate_beam_occurrence():
    b = _mini()
    b.pops.append(copy.deepcopy(next(p for p in b.pops if p["element_type"] == "BEAM")))
    assert "DUPLICATE_OCCURRENCE" in _codes(_inv(b))


def test_mut07_duplicate_bar_component():
    b = _mini()
    b.comps.append(copy.deepcopy(_comp(b, "STRAP:SB1:H30|BOTTOM")))
    assert {"DUPLICATE_COMPONENT_ID", "DUPLICATE_COMPONENT"} <= _codes(_inv(b))


def test_mut08_shorten_one_span():
    b = _mini()
    c = next(c for c in b.comps if c["element_type"] == "CONTINUOUS_BEAM" and c["bar_role"] == "BOTTOM")
    c["verified_length_m"] -= 0.5
    assert "CB_CORE_DIFFERS_FROM_SPANS" in _codes(_inv(b))


def test_mut09_remove_cover_authority():
    b = _mini()
    _comp(b, "STRAP:SB1:H30|TOP")["cover_rule_id"] = None
    assert "MISSING_COVER_RULE" in _codes(_inv(b))


def test_mut10_remove_lap_authority():
    c = RM.component(comp_id="long", population_id="P", element_type="X", occurrence_id="O", level="GF",
                     bar_role="MAIN", dia_mm=16, count=RM.bar_count("ABSOLUTE_COUNT", 2),
                     parts=[RM.part("CORE", 15.0, "COMPLETE", "r")], cover_rule_id="C", formula="f")
    with_lap = RM.bbs([c], {"P": RM.LB}, lap_factor=70, lap_rule_id="LAP-TENSION-70D")
    without = RM.bbs([c], {"P": RM.LB})
    assert with_lap["included"] == ["long"] and with_lap["total"]["used_kg"] > with_lap["total"]["net_kg"]
    assert without["included"] == [] and without["excluded"][0]["state"] == "BLOCKED_LAP_METHOD"


def test_mut11_blocked_side_bars_marked_complete():
    b = _mini()
    c = next(c for c in b.comps if c["bar_role"] == "SIDE_BARS" and c["state"] == "BLOCKED")
    c["state"] = "COMPLETE"
    assert "COMPLETE_WITHOUT_QUANTITY" in _codes(_inv(b))


def test_mut12_sb2_selects_one_row():
    b = _mini()
    next(p for p in b.pops if p["occurrence_id"].startswith("STRAP:SB2"))["release_state"] = RM.LB
    assert "CONFLICT_KEY_RELEASED" in _codes(_inv(b))


def test_mut13_readd_d5_column_without_concrete():
    b = _mini()
    p = next(p for p in b.pops if p["occurrence_id"] == "COLUMN:GF:C:H41")
    assert p["release_state"] == RM.BLK
    p["lower_bound_kg"] = 50.0
    assert "D5_COLUMN_RELEASED_WITHOUT_CONCRETE" in _codes(_inv(b))


def test_mut14_collapse_t_and_b():
    b = _mini()
    b.comps = [c for c in b.comps if not c["comp_id"].endswith("|T&B_TOP")]
    assert "T_AND_B_LAYER_COLLAPSED" in _codes(_inv(b))


def test_mut15_blocked_population_in_bbs():
    b = _mini()
    ps = {p["pop_id"]: p["release_state"] for p in b.pops}
    bb = RM.bbs(b.comps, ps, lap_factor=70, lap_rule_id="L")
    assert RM.check_bbs_eligibility(bb, b.comps, ps) == []
    blocked = next(c for c in b.comps if ps[c["population_id"]] == RM.BLK)
    bb["included"].append(blocked["comp_id"])
    assert RM.check_bbs_eligibility(bb, b.comps, ps)


def test_mut16_incomplete_population_marked_complete():
    b = _mini()
    p = next(p for p in b.pops if p["release_state"] == RM.LB)
    p["release_state"] = RM.VC
    assert "INCOMPLETE_POPULATION_MARKED_COMPLETE" in _codes(_inv(b))


# =============================================================================================== 3. gates (frozen R3)
def test_G11_two_layer_footing_quantity_consumer():
    rows = {r["type"]: r for r in _reg("FOOTING_REBAR_REGISTER_V3")["rows"]}
    for t in ("F8", "F12", "F13", "F14", "FF"):
        r = rows[t]
        mesh = [c for c in r["components"] if c["role"] in ("TOP_SHORT", "TOP_LONG", "BOTTOM_SHORT", "BOTTOM_LONG")]
        assert len(mesh) == 4, t
        for c in mesh:
            other = r["L_m"] if c["role"].endswith("SHORT") else r["W_m"]
            assert c["count_mode"] == "BARS_PER_METRE" and c["distribution_m"] == pytest.approx(other - 0.14)
            assert c["count_verified"] == math.ceil(c["rate_per_m"] * (other - 0.14) - 1e-9) > c["rate_per_m"]
        assert r["new_verified_kg"] > 0 and r["release_state"] == RM.LB


def test_G13_strap_rebar_quantity_consumer():
    reg = _reg("BEAM_REBAR_REGISTER_V3")
    rows = {r["occurrence"].split(":")[1]: r for r in reg["rows"] if r["element_type"] == "STRAP_BEAM"}
    for t in ("SB1", "SB3"):
        roles = {c["role"]: c for c in rows[t]["components"]}
        assert all((roles[k]["verified_kg"] + roles[k]["provisional_kg"]) > 0 for k in ("BOTTOM", "TOP", "STIRRUPS"))
    assert rows["SB2"]["release_state"] == RM.BLK
    c = reg["strap_conflicts"][0]
    assert c["state"] == "SOURCE_CONFLICT_DUPLICATE_SCHEDULE_KEY" and c["selected"] is None
    assert sorted(x["B_cm"] for x in c["candidates"]) == [80.0, 100.0]


@pytest.mark.xfail(strict=True, reason="Q-S4 ground-slab scope still open (nested candidate cells)")
def test_G15_ground_zone_not_bound_by_minimum_area():
    assert all(z["scope"] == "ESTABLISHED_SOLE_CANDIDATE" for z in _reg("SLAB_REBAR_AUDIT")["ground_slab_scope"])


@pytest.mark.xfail(strict=True, reason="p.16 stair detail applicability not proved")
def test_G23_stair_rebar_bound_to_typical_layout():
    assert _reg("SLAB_REBAR_AUDIT")["stairs"][0]["state"] != "BLOCKED_DETAIL_APPLICABILITY"


def test_G24_cb_component_accounting():
    reg = _reg("CONTINUOUS_BEAM_BAR_GEOMETRY_REGISTER")
    geo = {g["type"]: g for g in reg["geometry"]}
    assert len(geo) == 13 and len(reg["occurrences"]) == 11
    assert {d["type"] for d in reg["definitions_without_occurrence"]} == {"CB2", "CB10"}
    for o in reg["occurrences"]:
        typ = o["occurrence"].split(":")[2]
        comps = [m["component"] for m in o["component_matrix"]]
        n_sp = len(geo[typ]["spans_m"])
        assert sum(c.startswith("STIRRUPS") for c in comps) == n_sp
        assert len([c for c in comps if not c.startswith(("STIRRUPS", "SIDE_BARS"))]) == len(geo[typ]["bars"])
        assert any(c.startswith("SIDE_BARS") for c in comps)
        assert all(m["state"] in RM.COMPONENT_STATES for m in o["component_matrix"])
        assert o["release_state"] != RM.VC
    checks = _reg("REBAR_MASS_CONSERVATION_REGISTER")["checks"]
    assert checks["cb_accounting"]["pass"] and checks["cb_span_cores"]["pass"]


def test_G25_rebar_mass_conservation():
    m = _reg("REBAR_MASS_CONSERVATION_REGISTER")
    assert all(v["pass"] for v in m["checks"].values()), {k: v for k, v in m["checks"].items() if not v["pass"]}
    ck, pk = m["component_kg"], m["population_kg"]
    assert m["released_component_verified_kg"] == pytest.approx(pk["verified_complete_kg"] + pk["lower_bound_kg"],
                                                                rel=1e-9)
    assert ck["verified_kg"] + ck["provisional_kg"] + ck["audit_kg"] == pytest.approx(sum(pk.values()), rel=1e-9)
    b = m["bbs_total"]
    assert b["purchased_kg"] >= b["used_kg"] >= b["net_kg"] > 0
    assert b["waste_kg"] == pytest.approx(b["purchased_kg"] - b["used_kg"], abs=1e-3)
    assert b["net_kg"] == pytest.approx(pk["verified_complete_kg"] + pk["lower_bound_kg"], rel=1e-9)


def test_G26_rebar_source_provenance():
    reg = _reg("REBAR_PROVENANCE_REGISTER")
    assert reg["violations"] == []
    idx = json.loads((REGS / "INDEX.json").read_text())
    for r in reg["rows"]:
        if r["verified_kg"] + r["provisional_kg"] > 0:
            s = r["source"]
            assert s["drawing_sha256"] == idx["st7757_sha256"] and s["locator"] and s["raw"] and r["formula"], r["comp_id"]
            assert r["cover_rule_id"] and r["weight_formula"] == RM.KG_FORMULA


@pytest.mark.parametrize("path", ["research/external_engine_lab/alsenan_rebar_v3.py", "engine/source/rebar_model.py",
                                  "research/alsenan_rebar_truth_03/build_rebar_v3.py"])
def test_G27_no_benchmark_leakage(path):
    src = (ROOT / path).read_text()
    for banned in ("registers_v3b_eval", "BENCHMARK_EVALUATION", "44.19", "benchmark_qty", "registers_b1", ".xlsx",
                   "alsenan_v3b_evaluation", "freelancer"):
        assert banned not in src, (path, banned)


def test_G28_no_ratio_quantity():
    for path in ("research/external_engine_lab/alsenan_rebar_v3.py", "research/alsenan_rebar_truth_03/build_rebar_v3.py"):
        src = (ROOT / path).read_text()
        assert "ratio_qa(" not in src                      # the QA-only ratio helper never sits on a quantity path
    for r in _reg("REBAR_PROVENANCE_REGISTER")["rows"]:
        if r["verified_kg"] + r["provisional_kg"] > 0:
            assert "m3" not in (r["formula"] or "") and "/162" in (r["formula"] or "") + r["weight_formula"].replace(" ", "")
    rows = _reg("FOOTING_REBAR_REGISTER_V3")["rows"] + []
    for r in rows:
        for c in r["components"]:
            if c["verified_kg"] and c["count_verified"]:
                assert c["verified_kg"] == pytest.approx(c["count_verified"] * c["bar_length_m"] * c["dia_mm"] ** 2 / 162,
                                                         abs=1e-5)


def test_G29_no_duplicate_component():
    assert _reg("REBAR_MASS_CONSERVATION_REGISTER")["checks"]["duplicates"]["pass"]
    ids = [r["comp_id"] for r in _reg("REBAR_PROVENANCE_REGISTER")["rows"]]
    assert len(ids) == len(set(ids))


def test_G30_no_incomplete_population_complete():
    c = _reg("REBAR_COMPONENT_COMPLETENESS_REGISTER")
    assert c["invariant_violations"] == []
    for p in c["populations"]:
        if p["release_state"] == RM.VC:
            assert not p["missing_components"]
            assert all(x["state"] in ("COMPLETE", "NOT_REQUIRED") for x in p["components"] if x["required"])


def test_G31_every_rc_occurrence_has_rebar():
    o = _reg("REBAR_OCCURRENCE_REGISTER")
    occ = {r["occurrence_id"] for r in o["rows"]}
    assert len(o["rows"]) == o["rc_occurrences"] == len(occ)
    assert _reg("REBAR_MASS_CONSERVATION_REGISTER")["checks"]["completeness"]["pass"]


# =============================================================================================== 4. integrity, no gaming
def test_index_hashes_hold_and_twice_identical():
    idx = json.loads((REGS / "INDEX.json").read_text())
    assert idx["built_twice_identical"] is True
    for n, h in idx["registers"].items():
        assert hashlib.sha256((REGS / f"{n}.json").read_bytes()).hexdigest() == h, n
    assert hashlib.sha256((R3DIR / "REBAR_BAR_BY_BAR_AUDIT.md").read_bytes()).hexdigest() == idx["audit_md_sha256"]


def test_post_freeze_comparison_after_the_freeze():
    out = json.loads((R3DIR / "POST_FREEZE_REBAR_BENCHMARK.json").read_text())
    assert out["frozen_index_sha256"] == hashlib.sha256((REGS / "INDEX.json").read_bytes()).hexdigest()
    assert out["use"] == "FINDING_ONLY" and out["round3_t"]["project_final_rebar_total"] == "NOT YET ESTABLISHED"


def test_no_gaming_d5_stairs_sb2_and_no_single_total():
    col = _reg("COLUMN_REBAR_RECONCILIATION")["d5_blocked"]
    assert col["occurrences"] == 26 and col["audit_kg_verified_equivalent"] == pytest.approx(1739.65, abs=0.05)
    t = _reg("REBAR_OCCURRENCE_REGISTER")["trade_totals"]
    assert t["project_final_rebar_total"] == "NOT YET ESTABLISHED"
    assert _reg("SLAB_REBAR_AUDIT")["stairs"][0]["state"] == "BLOCKED_DETAIL_APPLICABILITY"
    v3b = ROOT / "tests/alsenan/registers_v3b/BOQ_LINES_V3B.json"
    r2 = json.loads((ROOT / "research/alsenan_control_plane_02/registers/INDEX.json").read_text())
    assert hashlib.sha256(v3b.read_bytes()).hexdigest() == r2["frozen_v3b_lines_sha256"]


def test_t_and_b_binding_is_positional_and_strong():
    tb = _reg("SLAB_REBAR_AUDIT")["t_and_b"]
    assert len(tb["rows"]) == 4 and all(r["binding"] == "STRONG_POSITIONAL" for r in tb["rows"])
    assert all(r["d1_mm"] <= 600 and r["d2_mm"] >= 2 * r["d1_mm"] for r in tb["rows"])
    assert _reg("SLAB_REBAR_AUDIT")["t_and_b_top_layer_added_kg"] > 0
