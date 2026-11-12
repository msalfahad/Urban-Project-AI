"""T-746 paint at opening edges as lm (R-T746-1 .. -3): synthetic villa V746 by hand (normal + adverse) and the
development villa pinned to the committed outputs.

Villa V746 (synthetic, not the development villa), by hand:
  D1 (NORMAL door, dry both sides): 0.90 x 2.10 in a 0.15 wall; frame detail not printed
      return lm = 2 x 2.10 + 0.90 = 5.10; plaster 0.15 x 5.10 = 0.765 m2 (unchanged)
      paint: 0 m2 (moved to lm), lm BOUNDED 0 .. 5.10 (low = frame over the whole return, not printed)
  W1 (NORMAL window in a plastered wall): 1.20 x 1.50, frame at the outer face, room-side return 0.15 deep, painted
      lm = 2 x 1.50 + 1.20 = 4.20, paint m2 0; with a painted internal sill 4.20 + 1.20 = 5.40
  W2 (ADVERSE window in a tiled wall): return tiled -> 0 lm, NO_PAINT_EDGE (determined zero, named)
  D2 (ADVERSE door, frame covering the whole jamb PRINTED): 0 lm, NO_PAINT_EDGE FRAME_COVERS_RETURN_DRAWN
  D3 (ADVERSE door between two wet rooms, reveal tile not established): BOUNDED 0 .. 5.10, cause named
  W3 (ADVERSE, height not established): HELD blank, never 0
  totals: paint m2 before 100.00 .. 110.00 with D1 0 .. 0.765 inside -> after 100.00 .. 109.235
"""
import hashlib
import json
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t746"
sys.path.insert(0, str(HERE))
import t746_rules as R  # noqa: E402

OUT = HERE / "out" / "T746_PAINT_EDGES.json"
D = Decimal


def lm(e):
    return None if e["lm"] is None else tuple(str(x) for x in e["lm"])


# ---------------------------------------------------------------- R-T746-1 normal
def test_door_d1_return_is_lm_bounded_by_frame():
    e = R.edge_lm("DOOR", "0.90", "2.10", low_cause="FRAME_COVERAGE_NOT_PRINTED")
    assert e["status"] == "BOUNDED" and lm(e) == ("0.000000", "5.100000") and e["gross_lm"] == D("5.1")


def test_window_in_plastered_wall_gives_lm_and_no_m2():
    e = R.edge_lm("WINDOW", "1.20", "1.50")
    assert e["status"] == "PAINT_LM" and lm(e) == ("4.200000", "4.200000")
    r = R.restate_return_line("0.63", "0.15", e)            # 0.15 x 4.20 = 0.63 plaster
    assert r["paint_m2_after"] == (D("0"), D("0")) and r["lm"] == e["lm"]


def test_painted_internal_sill_adds_its_width():
    e = R.edge_lm("WINDOW", "1.20", "1.50", painted_sill=True)
    assert lm(e) == ("5.400000", "5.400000")


def test_door_d1_line_restated_paint_zero_lm_beside():
    e = R.edge_lm("DOOR", "0.90", "2.10", low_cause="FRAME_COVERAGE_NOT_PRINTED")
    r = R.restate_return_line(("0.765", "0.765"), "0.15", e)
    assert r["paint_m2_after"] == (D("0"), D("0")) and lm(r) == ("0.000000", "5.100000")


def test_mirrored_opening_same_lm():
    a = R.edge_lm("DOOR", "0.90", "2.10", low_cause="FRAME_COVERAGE_NOT_PRINTED")
    b = R.edge_lm("DOOR", D("0.9"), D("2.1"), low_cause="FRAME_COVERAGE_NOT_PRINTED")   # mirrored plan: same w, h
    assert lm(a) == lm(b)


def test_width_and_height_are_not_interchangeable():
    assert lm(R.edge_lm("WINDOW", "1.20", "1.50")) != lm(R.edge_lm("WINDOW", "1.50", "1.20"))


def test_edge_parts_frame_drawn_over_jambs_head_bounded():
    e = R.edge_parts("DOOR", "0.90", "2.10", jambs="FRAME_COVERS_RETURN_DRAWN", head="FRAME_COVERAGE_NOT_PRINTED")
    assert e["status"] == "BOUNDED" and lm(e) == ("0.000000", "0.900000") and e["gross_lm"] == D("5.1")
    r = R.restate_return_line("0.765", "0.15", e)            # identity on the gross 5.10, not on the painted part
    assert r["paint_m2_after"] == (D("0"), D("0"))


def test_edge_parts_all_painted_and_all_zero():
    assert lm(R.edge_parts("WINDOW", "1.20", "1.50")) == ("4.200000", "4.200000")
    assert lm(R.edge_parts("WINDOW", "1.20", "1.50", sill=True)) == ("5.400000", "5.400000")
    z = R.edge_parts("WINDOW", "1.20", "1.50", jambs="TILED_RETURN", head="TILED_RETURN")
    assert z["status"] == "NO_PAINT_EDGE" and lm(z) == ("0.000000", "0.000000")
    with pytest.raises(R.RuleError):
        R.edge_parts("DOOR", "0.9", "2.1", sill=True)
    with pytest.raises(R.RuleError):
        R.edge_parts("DOOR", "0.9", "2.1", head="DEFAULT_DEPTH")
    assert R.edge_parts("DOOR", None, "2.1")["status"] == "HELD"


# ---------------------------------------------------------------- adverse
def test_window_in_tiled_wall_zero_edge():
    e = R.edge_lm("WINDOW", "1.20", "1.50", zero_cause="TILED_RETURN")
    assert e["status"] == "NO_PAINT_EDGE" and lm(e) == ("0.000000", "0.000000") and e["cause"] == "TILED_RETURN"


def test_door_with_frame_covering_jamb_is_named():
    e = R.edge_lm("DOOR", "0.90", "2.10", zero_cause="FRAME_COVERS_RETURN_DRAWN")
    assert e["status"] == "NO_PAINT_EDGE" and e["cause"] == "FRAME_COVERS_RETURN_DRAWN" and e["gross_lm"] == D("5.1")


def test_wet_both_sides_bounded_named():
    e = R.edge_lm("DOOR", "0.90", "2.10", low_cause="WET_BOTH_SIDES_TILE_NOT_ESTABLISHED")
    assert e["status"] == "BOUNDED" and e["cause"] == "WET_BOTH_SIDES_TILE_NOT_ESTABLISHED"


def test_missing_height_is_held_never_zero():
    e = R.edge_lm("WINDOW", "1.20", None)
    assert e["status"] == "HELD" and e["lm"] is None
    assert R.sum_lm([e, R.edge_lm("WINDOW", "1.20", "1.50")]) == {"lm": (D("4.2"), D("4.2")), "held": 1}


@pytest.mark.parametrize("w,h", [("900", "2.10"), ("0.90", "2100"), ("-0.9", "2.1")])
def test_mm_or_negative_refused(w, h):
    with pytest.raises(R.RuleError):
        R.edge_lm("DOOR", w, h)


def test_zero_size_refused():
    with pytest.raises(R.RuleError):
        R.edge_lm("DOOR", "0", "2.10")


def test_door_sill_refused():
    with pytest.raises(R.RuleError):
        R.edge_lm("DOOR", "0.90", "2.10", painted_sill=True)


def test_unknown_or_double_cause_refused():
    with pytest.raises(R.RuleError):
        R.edge_lm("DOOR", "0.9", "2.1", low_cause="GUESS")
    with pytest.raises(R.RuleError):
        R.edge_lm("DOOR", "0.9", "2.1", zero_cause="TILED_RETURN", low_cause="FRAME_COVERAGE_NOT_PRINTED")


def test_plaster_not_matching_depth_x_lm_refused():
    e = R.edge_lm("DOOR", "0.90", "2.10", low_cause="FRAME_COVERAGE_NOT_PRINTED")
    with pytest.raises(R.RuleError):
        R.restate_return_line("0.80", "0.15", e)              # 0.15 x 5.10 = 0.765, not 0.80


def test_blank_plaster_face_stays_held():
    e = R.edge_lm("ARCH", None, None)
    r = R.restate_return_line(None, None, e)
    assert r["status"] == "HELD" and r["paint_m2_after"] is None and r["lm"] is None
    with pytest.raises(R.RuleError):
        R.restate_return_line(None, "0.15", R.edge_lm("DOOR", "0.9", "2.1", low_cause="FRAME_COVERAGE_NOT_PRINTED"))


def test_valued_plaster_with_unknown_edge_refused():
    with pytest.raises(R.RuleError):
        R.restate_return_line("0.765", "0.15", R.edge_lm("DOOR", None, "2.1"))


def test_one_opening_one_line():
    assert R.bind_once([("D1", "L-1"), ("D2", "L-2")])
    with pytest.raises(R.RuleError):
        R.bind_once([("D1", "L-1"), ("D1", "L-2")])
    with pytest.raises(R.RuleError):
        R.bind_once([("D1", "L-1"), ("D2", "L-1")])


def test_totals_after_and_negative_refused():
    t = R.paint_after(("100.00", "110.00"), [("0", "0.765")])
    assert t["after"] == (D("100.000000"), D("109.235000")) and t["removed"] == (D("0.000000"), D("0.765000"))
    with pytest.raises(R.RuleError):
        R.paint_after(("0.5", "0.5"), [("0.765", "0.765")])


# ---------------------------------------------------------------- development villa pins
@pytest.fixture(scope="module")
def out():
    return json.loads(OUT.read_text(encoding="utf-8"))


def test_outputs_rebuild_byte_for_byte():
    r = subprocess.run([sys.executable, "-I", str(HERE / "t746_alsenan.py"), "--check"], capture_output=True, text=True,
                       cwd=ROOT)
    assert r.returncode == 0, r.stdout + r.stderr


def test_rules_module_reads_no_drawing():
    src = (HERE / "t746_rules.py").read_text(encoding="utf-8")
    assert "ezdxf" not in src and "open(" not in src


def test_thirty_return_lines_once_each(out):
    rows = out["return_rows"]
    assert len(rows) == 30 and len({r["paint_line"] for r in rows}) == 30 and len({r["opening"] for r in rows}) == 30
    assert out["return_lines"]["by_status"] == {"BOUNDED": 27, "HELD": 3}
    assert {r["opening"] for r in rows if r["status"] == "HELD"} == {"A-GF-01", "A-1F-01", "D-GF-15"}


def test_every_valued_line_paint_zero_and_plaster_identity(out):
    for r in out["return_rows"]:
        if r["status"] == "HELD":
            assert r["edge_lm_after_B"] is None and r["paint_m2_after_B"] is None
            continue
        assert r["paint_m2_after_B"] == ["0.000000", "0.000000"]
        assert D(r["plaster_m2"][1]) == D(r["depth"]) * D(r["gross_lm"])
        assert D(r["gross_lm"]) == 2 * D(r["height"]) + D(r["width"])
        assert r["edge_lm_after_B"][0] == "0.000000"
        assert D(r["edge_lm_after_B"][1]) == sum(D(p["lm"][1]) for p in r["parts"])
        assert sum(D(p["gross"]) for p in r["parts"]) == D(r["gross_lm"])


def test_door_gross_equals_t313_jambs_plus_heads(out):
    # T-313 r2: 27 doors, jambs 119.400 m.l + heads 25.000 m.l (independent ledger totals)
    bp = out["return_lines"]["by_part"]
    assert (bp["JAMBS"]["gross"], bp["HEAD"]["gross"]) == ("119.400000", "25.000000")


def test_frames_drawn_over_the_jambs_zero_jamb_edge(out):
    # 25 door blocks: posts over the full wall depth at the drawn masonry jambs -> jambs 0; heads 0 .. w (not on plan)
    assert out["return_lines"]["frames_drawn_full_depth"] == 25
    bp = out["return_lines"]["by_part"]
    assert bp["JAMBS"]["lm"] == ["0.000000", "8.800000"]      # D-GF-09 (position conflict) + D-GF-14 (no block): 2 x 4.40
    assert bp["HEAD"]["lm"] == ["0.000000", "25.000000"]
    assert out["return_lines"]["edge_lm"] == ["0.000000", "33.800000"]
    open_j = {r["opening"] for r in out["return_rows"] for p in r["parts"]
              if p["part"] == "JAMBS" and p["lm"][1] != "0.000000"}
    assert open_j == {"D-GF-09", "D-GF-14"}
    r9 = next(r for r in out["return_rows"] if r["opening"] == "D-GF-09")
    assert "POSITION CONFLICT" in r9["frame"]


def test_frame_census_file():
    import csv
    rows = {r["opening"]: r for r in csv.DictReader(open(HERE / "DOOR_FRAMES_T746.csv", encoding="utf-8"))}
    assert len(rows) == 28 and sum(r["frame_at_jambs"] == "True" for r in rows.values()) == 25
    assert rows["D-GF-14"]["entity"] == "ARC" and rows["D-GF-09"]["masonry_w_m"] == "0.900"
    assert all(r["wall_depth_m"] in ("0.150", "0.200") for r in rows.values() if r["entity"] == "INSERT")


def test_frame_census_rebuilds_when_the_drawing_is_present():
    dxf = ROOT.parent / "private" / "P7757_DXF_COMPRESSED" / "P7757.dxf"
    if not dxf.exists():
        pytest.skip("private drawing absent (Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip)")
    r = subprocess.run([sys.executable, "-I", str(HERE / "t746_frames.py"), str(dxf)], capture_output=True, text=True,
                       cwd=ROOT)
    assert r.returncode == 0 and r.stdout == (HERE / "DOOR_FRAMES_T746.csv").read_text(encoding="utf-8")


def test_wet_both_five_named(out):
    wet = [r["opening"] for r in out["return_rows"] if "WET_BOTH_SIDES_TILE_NOT_ESTABLISHED" in (r["cause"] or "")]
    assert sorted(wet) == ["D-1F-06", "D-GF-02", "D-GF-10", "D-GF-11", "D-GF-12"]


def test_d_gf_07_printed_height(out):
    r = next(r for r in out["return_rows"] if r["opening"] == "D-GF-07")
    assert (r["width"], r["height"], r["gross_lm"], r["plaster_m2"]) == ("2.0", "2.5", "7.000000", ["1.400000", "1.400000"])


def test_windows(out):
    w = out["windows"]
    assert w["by_side_status"] == {"IN HELD": 2, "IN NO_PAINT_EDGE": 27, "OUT HELD": 3, "OUT PAINT_LM": 26}
    assert w["outside_edge_lm"] == ["106.020000", "106.020000"] and w["outside_held"] == 3
    held = {x["opening"] for x in out["window_rows"] if x["status"] == "HELD" and x["side"] == "OUT"}
    assert held == {"W02", "W03", "W17"}


def test_paint_totals_and_residual(out):
    p = out["paint_m2"]
    assert p["rule_A_T740"] == ["841.260635", "929.204847"]
    assert p["rule_B_after"] == ["821.010635", "905.054847"]
    assert p["engine_returns_out"] == ["822.198159", "903.064521"]
    assert p["floor_readd_residual"] == ["0.000000", "0.000000"]
    assert out["return_lines"]["paint_m2_removed_rule_A"] == ["20.250000", "24.150000"]


def test_inputs_pinned(out):
    assert out["inputs_sha256_16"]["research/agents_t717/out/LINE_INDEX_V3_0_74.json"] == "6733cbc143cdfffd"
    h = hashlib.sha256((ROOT / "research/agents_t740/out/T740_PAINT_RULE.json").read_bytes()).hexdigest()
    assert out["inputs_sha256_16"]["research/agents_t740/out/T740_PAINT_RULE.json"] == h[:16]
