"""T-747 exterior paint faces (R-T747-1 .. -3): synthetic villa V747 by hand (normal + adverse) and the development
villa pinned to the committed outputs.

Villa V747 (synthetic, not the development villa), by hand. Box 10.00 x 8.00 m, one storey band +0.30 .. +3.30 (3.00):
  N 10 x 3 = 30.00, a CLAD panel printed 2.00 x 3.00 = 6.00          -> render 30.00, paint 24.00
  E  8 x 3 = 24.00, window W2 1.00 x 1.00 = 1.00                     -> render 23.00, paint 23.00
  S 10 x 3 = 30.00, window W1 1.20 x 1.50 = 1.80                     -> render 28.20, paint 28.20
  W  8 x 3 = 24.00                                                    -> render 24.00, paint 24.00
  totals: render 105.20, paint 99.20, deducted 6.00, residual 0 (holes are NOT deducted again from the paint)
  adverse: the boundary wall face (Q-65) is refused; a mirrored box (E <-> W) gives the same totals; a face read in mm2
  is refused; a deduction larger than its face is refused; a HELD face 10 .. 12 stays a bound; a blank face stays blank
  (never 0); a drawn stone zone 1.00 of unprinted material on W gives paint 23.00 .. 24.00.
  edges: W1 rectangle 2 x 1.50 + 1.20 = 4.20 lm; an arched window 1.00 wide, 2.00 high: rectangle 5.00 vs developed
  2 x 1.50 + pi x 0.50 = 4.570796 -> the developed outline governs; a door whose frame is drawn over the jambs: 0 .. w.
"""
import json
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t747"
sys.path.insert(0, str(HERE))
import t747_rules as R  # noqa: E402

OUT = HERE / "out" / "T747_EXT_PAINT.json"
D = Decimal


def p(f):
    return None if f["paint"] is None else (str(f["paint"][0]), str(f["paint"][1]))


def box(mirror=False):
    faces = [("N", 30, [{"kind": "CLAD", "m2": "6.00", "why": "clad panel hatched 2.00 x 3.00 on the N elevation"}],
              0), ("E", 24, [], 1.0), ("S", 30, [], 1.8), ("W", 24, [], 0)]
    if mirror:
        faces = [(("W" if s == "E" else "E" if s == "W" else s), a, d, h) for s, a, d, h in faces]
    return [R.paint_face(f"GF/{s}-1/EDGE/storey", "STOREY", (D(a) - D(str(h)), D(a) - D(str(h))), deductions=d)
            for s, a, d, h in faces]


# ---------------------------------------------------------------- R-T747-1 / -2 normal
def test_box_faces_by_hand():
    fs = {f["face_id"].split("/")[1]: f for f in box()}
    assert p(fs["N-1"]) == ("24.000000", "24.000000")
    assert p(fs["E-1"]) == ("23.000000", "23.000000")
    assert p(fs["S-1"]) == ("28.200000", "28.200000")
    assert p(fs["W-1"]) == ("24.000000", "24.000000")


def test_box_totals_residual_zero():
    r = R.roll_up(box())
    assert [str(x) for x in r["render"]] == ["105.200000", "105.200000"]
    assert [str(x) for x in r["paint"]] == ["99.200000", "99.200000"]
    assert [str(x) for x in r["deducted"]] == ["6.000000", "6.000000"]
    assert [str(x) for x in r["residual"]] == ["0.000000", "0.000000"]
    assert r["state"] == "POINT"


def test_mirror_same_totals():
    a, b = R.roll_up(box()), R.roll_up(box(mirror=True))
    assert a["paint"] == b["paint"] and a["render"] == b["render"]


def test_holes_not_deducted_twice():
    f = R.paint_face("GF/S-1/EDGE/storey", "STOREY", ("28.2", "28.2"))
    assert p(f) == ("28.200000", "28.200000") and f["deductions"] == []


def test_held_face_stays_bound():
    f = R.paint_face("GF/NW-7/EDGE/storey", "STOREY", ("10", "12"))
    assert f["state"] == "BOUNDED" and p(f) == ("10.000000", "12.000000")


def test_blank_face_never_zero():
    f = R.paint_face("1F/NE-1/SLAB_EDGE_BELOW/slab_edge", "SLAB_EDGE", None)
    assert f["paint"] is None and f["state"] == "BLANK"
    r = R.roll_up([f, R.paint_face("1F/NW-1/X/slab_edge", "SLAB_EDGE", ("0.5", "2"))])
    assert r["state"] == "BLANK_PART" and r["blank_faces"] == ["1F/NE-1/SLAB_EDGE_BELOW/slab_edge"]
    assert R.roll_up([f])["paint"] is None


def test_unprinted_zone_lowers_low_end_only():
    f = R.paint_face("GF/W-1/EDGE/storey", "STOREY", ("24", "24"),
                     deductions=[{"kind": "NOT_PRINTED_FINISH", "m2": "1.00", "why": "stone outlines, no material"}])
    assert p(f) == ("23.000000", "24.000000") and f["state"] == "BOUNDED"
    assert [str(x) for x in f["residual"]] == ["0.000000", "0.000000"]


# ---------------------------------------------------------------- R-T747-1 adverse
def test_boundary_wall_face_refused():
    with pytest.raises(R.RuleError, match="boundary"):
        R.paint_face("FENCE:F-NORTH:FACE:OUTSIDE", "STOREY", ("83.1305", "83.1305"), boundary=True)


@pytest.mark.parametrize("render", [("30000000", "30000000"), ("-1", "2"), ("5", "4")])
def test_units_negative_inverted_refused(render):
    with pytest.raises(R.RuleError):
        R.paint_face("GF/N-1/EDGE/storey", "STOREY", render)


def test_unit_not_m2_refused():
    with pytest.raises(R.RuleError, match="unit"):
        R.paint_face("GF/N-1/EDGE/storey", "STOREY", ("30", "30"), unit="mm2")


def test_deduction_larger_than_face_refused():
    with pytest.raises(R.RuleError, match="exceed"):
        R.paint_face("GF/N-1/EDGE/storey", "STOREY", ("3", "3"),
                     deductions=[{"kind": "CLAD", "m2": "6", "why": "hatch"}])


@pytest.mark.parametrize("d", [{"kind": "MAYBE_CLAD", "m2": "1", "why": "guess"}, {"kind": "CLAD", "m2": "1"},
                               {"kind": "CLAD", "m2": "0", "why": "hatch"}, {"kind": "CLAD", "m2": None, "why": "x"}])
def test_bad_deductions_refused(d):
    with pytest.raises(R.RuleError):
        R.paint_face("GF/N-1/EDGE/storey", "STOREY", ("30", "30"), deductions=[d])


def test_unknown_element_refused():
    with pytest.raises(R.RuleError):
        R.paint_face("GF/N-1/EDGE/cornice", "CORNICE", ("3", "3"))


# ---------------------------------------------------------------- R-T747-3 edges
def test_arched_developed_outline_governs():
    dev = str(R.q6(D(2) * D("1.5") + D("3.14159265358979") * D("0.5")))
    e = R.opening_edge("WA", {"rect": {"lm": ("5.0", "5.0"), "basis": "RECTANGLE"},
                              "arc": {"lm": (dev, dev), "basis": "ARC_DEVELOPED"}})
    assert e["source"] == "arc" and [str(x) for x in e["lm"]] == ["4.570796", "4.570796"]
    assert [str(x) for x in e["others"][0]["diff"]] == ["0.429204", "0.429204"]


def test_door_frame_governs_ring():
    e = R.opening_edge("D1", {"ring": {"lm": ("5.1", "5.1"), "basis": "RECTANGLE"},
                              "frame": {"lm": ("0", "0.9"), "basis": "DRAWN_FRAME"}})
    assert e["source"] == "frame" and e["state"] == "BOUNDED"


def test_edge_held_never_zero():
    e = R.opening_edge("W3", {"t": {"lm": None, "basis": "RECTANGLE"}})
    assert e["lm"] is None and e["state"] == "HELD"
    s = R.sum_lm([e, R.opening_edge("W1", {"t": {"lm": ("4.2", "4.2"), "basis": "RECTANGLE"}})])
    assert s["held"] == ["W3"] and [str(x) for x in s["lm"]] == ["4.200000", "4.200000"]


def test_unknown_edge_basis_refused():
    with pytest.raises(R.RuleError):
        R.opening_edge("W1", {"t": {"lm": ("4.2", "4.2"), "basis": "GUESS"}})


# ---------------------------------------------------------------- development villa (pinned)
@pytest.fixture(scope="module")
def out():
    return json.loads(OUT.read_text(encoding="utf-8"))


def test_rebuild_equals_committed():
    r = subprocess.run([sys.executable, "-I", str(HERE / "t747_alsenan.py"), "--check"], capture_output=True,
                       text=True, cwd=ROOT)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "AGREE" in r.stdout


def test_every_line_render_equals_stage(out):
    assert len(out["lines"]) == 18
    assert all(x["render_equals_stage"] for x in out["lines"])
    assert all(x["residual_m2"] is None or x["residual_m2"] == ["0.000000", "0.000000"] for x in out["lines"])


def test_face_residual_zero_and_once(out):
    ids = [f["face_id"] for f in out["faces"]]
    assert len(ids) == 126 == len(set(ids))
    for f in out["faces"]:
        if f["paint"] is not None:
            assert f["residual"] == ["0.000000", "0.000000"]


def test_totals_pinned(out):
    t = out["total"]
    assert t["render"] == ["1008.466427", "1087.619176"]
    assert t["paint"] == ["1007.168044", "1087.619176"]
    assert t["deducted"] == ["1.298383", "0.000000"]
    assert len(t["blank_faces"]) == 6


def test_line_paint_excludes_blank_line(out):
    lo = sum(D(x["line_paint"][0]) for x in out["lines"] if x["line_paint"])
    hi = sum(D(x["line_paint"][1]) for x in out["lines"] if x["line_paint"])
    assert (str(lo), str(hi)) == ("1006.633044", "1085.612926")
    blank = [x["line_key"] for x in out["lines"] if x["line_paint"] is None]
    assert blank == ["NEW FIN.EXT.FINISH SLAB-EDGE 1F"]


def test_2f_sides_by_hand(out):
    s = {(x["floor"], x["side"], x["element"]): x["paint_m2"] for x in out["sides"]}
    # 8.10 x 4.20 = 34.02 - D-2F-01 2.20 = 31.82; 6.80 x 4.20 = 28.56; 28.56 - W26 1.875 = 26.685;
    # 34.02 - W27 1.50 - W28 0.48 - W29 1.80 = 30.24; sum 117.305 = the 2F storey line
    assert s[("2F", "NE", "STOREY")] == ["31.820000", "31.820000"]
    assert s[("2F", "NW", "STOREY")] == ["28.560000", "28.560000"]
    assert s[("2F", "SE", "STOREY")] == ["26.685000", "26.685000"]
    assert s[("2F", "SW", "STOREY")] == ["30.240000", "30.240000"]


def test_surround_zone_only_on_its_two_faces(out):
    ded = {f["face_id"]: f["deductions"] for f in out["faces"] if f["deductions"]}
    assert ded == {"GF/SE-2/COVERED/plinth": [{"kind": "NOT_PRINTED_FINISH", "m2": "0.222500"}],
                   "GF/SE-2/COVERED/storey": [{"kind": "NOT_PRINTED_FINISH", "m2": "1.075883"}]}
    assert out["evidence"]["elevations"]["dxf_finish_words"] == 0
    assert out["evidence"]["elevations"]["material_hatch_on_facade_faces"] == 0


def test_window_edges_reconcile_to_t746(out):
    r = out["edges"]["summary"]["reconciliation"]
    assert r["t746_outside_edge_lm_all"] == "106.020000"
    assert r["arched_rectangle_over_developed"] == "2.336900"
    assert r["governing_window_edge_lm"] == "103.683100" and r["check"] == "0.000000"
    assert sorted(out["edges"]["summary"]["windows"]["held"]) == ["W02", "W03", "W17"]


def test_corners_pinned(out):
    c = out["edges"]["corners"]
    assert c["total_lm"] == ["168.500000", "182.050000"]
    assert any("NO_HOST" in "".join(v["rows"]) or v["no_host"] for v in c["by_host"].values())


def test_fence_refused_unchanged(out):
    f = out["index_census"]
    assert f["fence_lines"] == 16 and f["facade_paint_lines_now"] == 0
    assert len(f["fin_ext_finish_lines_now"]) == 3
