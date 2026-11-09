"""T-545: B10-07 beam concrete reconciled against a freelancer by component (research/agents_t545, R-T545-1 .. 3).
Hand villa "V545" (not the training villa) with both conventions; adverse cases; then the committed development-villa
table, checked from merged repository files (the rebuild from the private workbook runs only when it is present)."""
from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t545"))
import t545_rules as R  # noqa: E402

OUT = ROOT / "research" / "agents_t545" / "out" / "T545_BEAM_RECONCILE.json"
LINE_INDEX = ROOT / "research" / "agents_t507" / "out" / "LINE_INDEX_V3_0_57.json"
V3021 = ROOT / "research" / "agents_t332" / "CANDIDATE_V3021_CONCRETE_LINES.json"
PRIVATE_WB = ROOT.parent / "private" / "concrete_rebar.xlsx"
PRIVATE_BANDS = ROOT.parent / "private" / "t545" / "bands.json"

# ---- villa "V545" (hand) ----------------------------------------------------------------------------------------
# Beam B1 0.25 x 0.60 between two columns 0.40 along x 0.25 across, face to face 5.00 m; columns 2.90 m floor to the
# beam soffit; slab 0.15 thick over a gross 30.00 m2 panel.
# ENGINE (columns own the joint to the slab top): beam 0.25 x 5.00 x 0.60 = 0.750; columns 2 x 0.40 x 0.25 x 3.50 =
#   0.700; slab (30.00 - 1.25 - 0.20) x 0.15 = 4.2825; total 5.7325.
# THROUGH (his reading): beam 0.25 x 5.80 x 0.60 = 0.870; columns 2 x 0.10 x 2.90 = 0.580; slab 4.2825; total 5.7325.
# Same solid; beam difference -0.120 = THROUGH_SUPPORT.
# Beam / slab alone: FULL + NET 0.750 + 28.75 x 0.15 = 5.0625 = DOWNSTAND + GROSS 0.5625 + 4.500.
# Component table: engine B1 0.750 + B2 0.20 x 0.40 x 3.00 = 0.240 (no row of his) ; B3 HELD (drawn 2.00 m, his row
#   0.20 x 0.50 x 2.00 = 0.200); his rows B1 0.870 + B3 0.200 = 1.070. Residual 0.990 - 1.070 = -0.080 =
#   COUNT +0.240 + THROUGH_SUPPORT -0.120 + HELD -0.200.
FIX = dict(b=0.25, D=0.60, L_f2f=5.00, col_along=0.40, col_across=0.25, col_height_to_soffit=2.90, t=0.15,
           slab_area_gross=30.00)


def test_hand_fixture_both_conventions_same_solid():
    r = R.beam_between_columns(**FIX)
    assert r["engine"] == {"beam": Decimal("0.750000"), "columns": Decimal("0.700000"), "slab": Decimal("4.282500")}
    assert r["through"]["beam"] == Decimal("0.870000") and r["through"]["columns"] == Decimal("0.580000")
    assert r["total"] == Decimal("5.7325") and r["beam_difference"] == Decimal("-0.120")


def test_hand_fixture_mirror_and_rotation_invariant():
    # mirror (columns swapped) / rotation (plan axes swapped) do not change any length or section of the fixture
    a = R.beam_between_columns(**FIX)
    b = R.beam_between_columns(**{**FIX, "col_along": 0.40, "col_across": 0.25})
    assert a == b


def test_beam_slab_pairings():
    kw = dict(b=0.25, L=5.0, D=0.60, t=0.15, slab_area_gross=30.0)
    fn = R.beam_slab_volumes(**kw, depth_basis="FULL", slab_basis="NET")
    dg = R.beam_slab_volumes(**kw, depth_basis="DOWNSTAND", slab_basis="GROSS")
    assert fn[2] == dg[2] == Decimal("5.0625")
    assert fn[0] == Decimal("0.75") and dg[0] == Decimal("0.5625")


@pytest.mark.parametrize("pair", [("FULL", "GROSS"), ("DOWNSTAND", "NET")])
def test_adverse_overlap_twice_or_nowhere_refused(pair):
    with pytest.raises(R.Refused):
        R.beam_slab_volumes(b=0.25, L=5.0, D=0.60, t=0.15, slab_area_gross=30.0, depth_basis=pair[0],
                            slab_basis=pair[1])


def test_adverse_mm_refused():
    with pytest.raises(R.Refused):
        R.beam_slab_volumes(b=250, L=5.0, D=600, t=150, slab_area_gross=30.0, depth_basis="FULL", slab_basis="NET")
    with pytest.raises(R.Refused):
        R.beam_between_columns(**{**FIX, "b": 250, "col_across": 250})


def test_adverse_missing_dimension_refused():
    with pytest.raises(R.Refused):
        R.beam_between_columns(**{**FIX, "col_height_to_soffit": 0})


def test_component_table_hand():
    t = R.component_table("0.990", "1.070", {"COUNT": "0.240", "THROUGH_SUPPORT": "-0.120", "HELD": "-0.200"},
                          held_his_share="0.200")
    assert t["residual_m3"] == "-0.080000"
    assert t["components"]["COUNT"]["verdict"] == "ENGINE_RIGHT"
    assert t["components"]["THROUGH_SUPPORT"]["verdict"] == "RULE_DIFFERENCE"


def test_adverse_component_table_open_sum_refused():
    with pytest.raises(R.Refused):
        R.component_table("0.990", "1.070", {"COUNT": "0.240", "THROUGH_SUPPORT": "-0.120"})


def test_adverse_held_closed_as_zero_refused():
    with pytest.raises(R.Refused):
        R.component_table("0.990", "0.870", {"COUNT": "0.240", "THROUGH_SUPPORT": "-0.120", "HELD": "0"},
                          held_his_share="0.200")
    with pytest.raises(R.Refused):
        R.held_value(0)


def test_adverse_percent_and_missing_refused():
    with pytest.raises(R.Refused):
        R.component_table("0.990", "1.070", {"COUNT": "22%", "THROUGH_SUPPORT": "-0.120", "HELD": "-0.200"})
    with pytest.raises(R.Refused):
        R.d6(None)


def test_adverse_joint_billed_twice_refused():
    ok = R.joints_once([{"line_id": "L1", "owns": ["B1#P1", "JOINT:C1"]}, {"line_id": "L2", "owns": ["C1"]}])
    assert ok == {"elements": 3, "lines": 2}
    with pytest.raises(R.Refused):
        R.joints_once([{"line_id": "L1", "owns": ["B1#P1", "JOINT:C1"]}, {"line_id": "L2", "owns": ["JOINT:C1"]}])


def test_held_bound_class():
    assert R.held_bound_class("0.30", "0.20", "0.40") == "INSIDE"
    assert R.held_bound_class("0.10", "0.20", "0.40") == "BELOW"
    assert R.held_bound_class("0.50", "0.20", "0.40") == "ABOVE"
    assert R.held_bound_class("0.50", None, None) == "UNBOUNDED"
    with pytest.raises(R.Refused):
        R.held_bound_class("0.30", "0.40", "0.20")


# ---- development villa: committed table, merged repository files ------------------------------------------------
@pytest.fixture(scope="module")
def doc():
    return json.loads(OUT.read_text(encoding="utf-8"))


def _beam_lines():
    d = json.loads(LINE_INDEX.read_text(encoding="utf-8"))
    return [ln for ln in d["lines"] if ln["item_code"] == "STR.CONC.BEAM"]


def test_dev_engine_figures_from_line_index(doc):
    L = _beam_lines()
    rel = sum((Decimal(str(x["measured_net"])) for x in L if x["class"] == "RELEASED"), Decimal(0))
    lo = sum((Decimal(str(x["held_low"])) for x in L if x["held_low"] is not None), Decimal(0))
    hi = sum((Decimal(str(x["held_high"])) for x in L if x["held_high"] is not None), Decimal(0))
    e = doc["engine"]
    assert Decimal(e["released_m3"]) == rel == Decimal("66.321054")
    assert [Decimal(v) for v in e["held_bound_m3"]] == [lo, hi]
    assert e["released_lines"] == 110 and e["held_lines"] == 27 and e["held_unknown_lines"] == 5
    assert e["excluded_lines"] == 54


def test_dev_since_t395_delta_from_committed_files(doc):
    a = {x["line_id"]: x for x in json.loads(V3021.read_text(encoding="utf-8"))["lines"]
         if x["item_code"] == "STR.CONC.BEAM"}
    q = Decimal("0.000001")
    delta = sum((Decimal(str(x["measured_net"])).quantize(q) - Decimal(str(a[x["line_id"]]["measured_net"])).quantize(q)
                 for x in _beam_lines() if x["class"] == "RELEASED"), Decimal(0))
    assert delta == Decimal(doc["engine"]["since_T395_V3_0_29_m3"]) == Decimal("0.003174")


def test_dev_tables_close_exactly(doc):
    for tbl in list(doc["floors"].values()) + [doc["total"]]:
        s = sum((Decimal(c["m3"]) for c in tbl["components"].values()), Decimal(0))
        assert s == Decimal(tbl["residual_m3"]) == Decimal(tbl["engine_m3"]) - Decimal(tbl["his_m3"])
    for k in ("engine_m3", "his_m3", "residual_m3"):
        assert sum(Decimal(f[k]) for f in doc["floors"].values()) == Decimal(doc["total"][k])
    comp = {k: Decimal(c["m3"]) for k, c in doc["total"]["components"].items()}
    for k in comp:
        assert comp[k] == sum((Decimal(f["components"][k]["m3"]) for f in doc["floors"].values()
                               if k in f["components"]), Decimal(0))


def test_dev_held_lines_each_once_never_zero(doc):
    held = {x["line_id"] for x in _beam_lines() if x["class"] == "HELD"}
    rows = doc["held_beside_his"]
    assert {h["line_id"] for h in rows} == held and len(rows) == len(held)
    for h in rows:
        for k in ("engine_low_m3", "engine_high_m3"):
            assert h[k] is None or Decimal(h[k]) > 0
    roll = doc["total"]["held_rollup"]
    assert Decimal(roll["with_his_row"]["his_share_m3"]) == -Decimal(doc["total"]["components"]["HELD"]["m3"])
    assert sum(r["lines"] for r in roll.values()) == 27


def test_dev_overlap_once(doc):
    ov = doc["overlap"]
    cols = [j["column_handle"] for j in ov["beam_column_joints_deducted"]]
    assert len(cols) == len(set(cols))
    for f in ("GF", "1F", "2F"):
        b = ov["beam_slab_basis"][f]
        assert b["his_slab_basis"] == "NET" and b["depth_basis_term_m3"] == 0.0


def test_dev_no_freelancer_rows_tracked(doc):
    txt = OUT.read_text(encoding="utf-8")
    assert "his_rows" not in txt and "\"row\"" not in txt


@pytest.mark.skipif(not (PRIVATE_WB.exists() and PRIVATE_BANDS.exists()), reason="private workbook / bands absent")
def test_dev_rebuild_equals_committed(doc):
    sys.path.insert(0, str(ROOT / "research" / "agents_t545"))
    import t545_alsenan as A
    new, *_ = A.build(str(PRIVATE_WB), str(PRIVATE_BANDS))
    assert json.loads(json.dumps(new, ensure_ascii=False)) == doc
