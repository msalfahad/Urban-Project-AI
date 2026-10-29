"""T-332 rules on a hand-calculated villa V332 (not the development villa).

Villa V332 (hand figures, m):
  FT1 footing 2.00 x 1.50 x 0.50 on 0.10 blinding: sides 2 (2.00 + 1.50) 0.50 = 3.500 OQ-10 FORMED / 0 EARTH_CAST;
      base on blinding: no row (contact EARTH, never formed).
  B1 suspended beam 0.20 x 0.60 under a 0.15 slab, clear 4.00: soffit 0.20 x 4.00 = 0.800; sides 2 x 4.00 x 0.45
      = 3.600 (drawing faces, both sides beside slab).
  E1 edge of the slab over the edge beam B2: free edge 6.00 x 0.15 = 0.900, the edge beam's own face (B2's line).
  P1 pit wall ring 1.60 / 1.20 square, 0.20 thick, height not printed: inner face 4 x 1.20 = 4.800 m2 per m HELD;
      outer face 4 x 1.60 = 6.400 m2 per m, OQ-10, HELD.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "research" / "agents_t332"))
import t332_rules as R  # noqa: E402

LINES_OLD = [
    {"line_id": "L-FT1", "element_id": "FTG:FT1", "item_code": "STR.CONC.FOOTING", "state": "SOURCE_DERIVED", "quantity": 1.5},
    {"line_id": "L-B1", "element_id": "BM:B1", "item_code": "STR.CONC.BEAM", "state": "SOURCE_DERIVED", "quantity": 0.48},
    {"line_id": "L-B2", "element_id": "BM:B2", "item_code": "STR.CONC.BEAM", "state": "SOURCE_DERIVED", "quantity": 0.72},
    {"line_id": "L-P1", "element_id": "PIT:P1", "item_code": "STR.CONC.PIT_WALL", "state": "BLOCKED_RFI", "quantity": None},
]


def faces():
    return [
        {"face_id": "FT1-S-F", "line_id": "L-FT1", "element_id": "FTG:FT1", "element": "FOOTING", "face_kind": "SIDE",
         "contact": "OQ10", "alternative": "OQ10_FORMED", "method": "E=G", "status": "ALTERNATIVE", "m2": 2 * (2.00 + 1.50) * 0.50},
        {"face_id": "FT1-S-E", "line_id": "L-FT1", "element_id": "FTG:FT1", "element": "FOOTING", "face_kind": "SIDE",
         "contact": "EARTH", "alternative": "OQ10_EARTH_CAST", "method": "E=G", "status": "ALTERNATIVE", "m2": 0.0},
        {"face_id": "B1-SOF", "line_id": "L-B1", "element_id": "BM:B1", "element": "BEAM", "face_kind": "SOFFIT",
         "contact": "", "alternative": "", "method": "G", "status": "CALCULATED", "m2": 0.20 * 4.00},
        {"face_id": "B1-SID", "line_id": "L-B1", "element_id": "BM:B1", "element": "BEAM", "face_kind": "SIDE",
         "contact": "", "alternative": "", "method": "G", "status": "CALCULATED", "m2": 2 * 4.00 * (0.60 - 0.15)},
        {"face_id": "E1-BAND", "line_id": "L-B2", "element_id": "BM:B2", "element": "SLAB_EDGE", "face_kind": "EDGE_BAND",
         "contact": "", "alternative": "", "method": "G", "status": "CALCULATED", "m2": 6.00 * 0.15},
        {"face_id": "P1-IN", "line_id": "L-P1", "element_id": "PIT:P1", "element": "PIT_WALL", "face_kind": "SIDE",
         "contact": "FORM", "alternative": "", "method": "G", "status": "HELD", "m2": None, "lo": None, "hi": None,
         "basis_note": "4 x 1.20 = 4.800 m2 per m of pit height (height not printed)"},
        {"face_id": "P1-OUT", "line_id": "L-P1", "element_id": "PIT:P1", "element": "PIT_WALL", "face_kind": "SIDE",
         "contact": "OQ10", "alternative": "OQ10_FORMED", "method": "G", "status": "HELD", "m2": None,
         "basis_note": "4 x 1.60 = 6.400 m2 per m (OQ-10)"},
    ]


def test_hand_values():
    f = {x["face_id"]: x for x in faces()}
    assert f["FT1-S-F"]["m2"] == pytest.approx(3.500)
    assert f["B1-SOF"]["m2"] == pytest.approx(0.800)
    assert f["B1-SID"]["m2"] == pytest.approx(3.600)
    assert f["E1-BAND"]["m2"] == pytest.approx(0.900)


def test_normal_rebind_same_lines():
    out = R.rebind(faces(), LINES_OLD)
    assert {r["tie"] for r in out} == {"SAME"}
    t = R.totals(out)
    assert t["CALCULATED||G"]["m2"] == pytest.approx(0.800 + 3.600 + 0.900)
    assert t["ALTERNATIVE|OQ10_FORMED|E=G"]["m2"] == pytest.approx(3.500)
    assert t["ALTERNATIVE|OQ10_EARTH_CAST|E=G"]["m2"] == 0.0
    assert t["HELD||G"]["m2"] == 0.0 and t["HELD||G"]["faces"] == 1
    fill = R.fill_table(out)
    assert fill["L-B2"]["totals"]["CALCULATED||G"]["m2"] == pytest.approx(0.900)  # the edge band on the beam line
    # R-T332-8 (rework r2, D-T332-1): the held pit face is BLANK in the FILL table, never 0 (r1 asserted 0.0 here)
    assert "L-P1" in fill and fill["L-P1"]["totals"]["HELD||G"]["m2"] is None
    assert fill["L-P1"]["totals"]["HELD||G"]["lo"] is None and fill["L-P1"]["totals"]["HELD||G"]["hi"] is None
    assert fill["L-P1"]["totals"]["HELD||G"]["bound_classes"] == "UNBOUNDED 1"
    assert fill["L-B1"]["totals"]["CALCULATED||G"]["lo"] is None      # no face carries a range: blank, not 0


def test_rebind_by_element_and_no_line():
    new = [dict(l) for l in LINES_OLD]
    new[1] = dict(new[1], line_id="L-B1-NEW")           # B1 re-identified
    new = [l for l in new if l["line_id"] != "L-B2"]   # B2's line gone
    out = {r["face_id"]: r for r in R.rebind(faces(), new)}
    assert out["B1-SOF"]["tie"] == "REBOUND" and out["B1-SOF"]["new_line_id"] == "L-B1-NEW"
    assert out["E1-BAND"]["tie"] == "NO_LINE" and "not in the newer candidate" in out["E1-BAND"]["tie_reason"]
    assert out["E1-BAND"]["m2"] == pytest.approx(0.900)   # the face keeps its value, it is only not tied
    assert "L-B2" not in R.fill_table(list(out.values()))


def test_measured_face_on_a_blank_line_is_held_with_its_value():
    new = [dict(l) for l in LINES_OLD]
    new[1] = dict(new[1], state="BLOCKED_RFI", quantity=None)
    out = {r["face_id"]: r for r in R.rebind(faces(), new)}
    assert out["B1-SID"]["status"] == "HELD" and out["B1-SID"]["m2"] is None
    assert out["B1-SID"]["held_from"] == pytest.approx(3.600)
    assert "R-T332-2" in out["B1-SID"]["rule"]


def test_held_face_never_gains_a_value_from_its_line():
    new = [dict(l) for l in LINES_OLD]
    new[3] = dict(new[3], state="SOURCE_DERIVED", quantity=1.1)
    out = {r["face_id"]: r for r in R.rebind(faces(), new)}
    assert out["P1-IN"]["status"] == "HELD" and out["P1-IN"]["m2"] is None


def test_adverse_face_bound_to_two_lines_refused():
    f = faces()
    f.append(dict(f[2], line_id="L-B2", element_id="BM:B2"))
    with pytest.raises(R.BindError, match="two lines"):
        R.rebind(f, LINES_OLD)


def test_adverse_element_on_two_lines_refused():
    new = [dict(l) for l in LINES_OLD] + [dict(LINES_OLD[1], line_id="L-B1-A"), dict(LINES_OLD[1], line_id="L-B1-B")]
    new = [l for l in new if l["line_id"] != "L-B1"]
    with pytest.raises(R.BindError, match="carried by 2 lines"):
        R.rebind(faces(), new)


@pytest.mark.parametrize("change", [
    {"status": "CALCULATED", "alternative": "", "m2": 1.75},          # footing base on blinding booked as a form
    {"status": "ALTERNATIVE", "alternative": "OQ10_FORMED", "m2": 1.75},
    {"status": "ALTERNATIVE", "alternative": "OQ10_EARTH_CAST", "m2": 1.75},
])
def test_adverse_ground_cast_face_formed_refused(change):
    f = dict(faces()[1], face_id="FT1-BASE", face_kind="SOFFIT", **{k: v for k, v in change.items()})
    with pytest.raises(R.BindError, match="EARTH"):
        R.check_face(f)


@pytest.mark.parametrize("m2", [0.0, 4.8])
def test_adverse_held_face_with_a_value_refused(m2):
    f = dict(faces()[5], m2=m2)
    with pytest.raises(R.BindError, match="HELD face carries a value"):
        R.check_face(f)


def test_held_range_and_single_bound():
    R.check_face(dict(faces()[5], lo=0.0, hi=4.8))
    R.check_face(dict(faces()[5], lo=None, hi=4.8))       # AT_MOST: a held datum with no low end
    with pytest.raises(R.BindError, match="reversed"):
        R.check_face(dict(faces()[5], lo=5.0, hi=4.8))


def test_adverse_negative_face_without_a_named_deduction_refused():
    with pytest.raises(R.BindError, match="negative"):
        R.check_face(dict(faces()[2], m2=-0.2))
    R.check_face(dict(faces()[2], m2=-0.12, item="tee cover 0.30 x 0.40"))


def test_adverse_unit_and_status():
    with pytest.raises(R.BindError, match="unit"):
        R.check_face(dict(faces()[2], unit="m"))
    with pytest.raises(R.BindError, match="unknown status"):
        R.check_face(dict(faces()[2], status="MEASURED"))


def test_adverse_face_on_not_applicable_line_refused():
    new = [dict(l) for l in LINES_OLD]
    new[1] = dict(new[1], state="NOT_APPLICABLE_WITH_EVIDENCE")
    with pytest.raises(R.BindError, match="NOT_APPLICABLE"):
        R.rebind(faces(), new)


def test_scenario_leak():
    s1 = dict(faces()[2], face_id="S1-RING", status="S1_NOT_RELEASED")
    with pytest.raises(R.ScenarioLeak):
        R.check_face(s1)
    assert R.totals([dict(s1, line_id="")]) == {}        # listed beside, never in a total
    with pytest.raises(R.ScenarioLeak):
        R.totals([dict(s1, line_id="", tie="SAME", new_line_id="L-B1")])


def test_deltas_replace_add_remove_and_closure():
    src = R.rebind(faces(), LINES_OLD)
    deltas = [
        {"face_id": "B1-SID", "kind": "REPLACE", "face": {"m2": 2 * 3.80 * 0.45}, "cause": "beam shortened by a merge",
         "source": "sheet S2 handle 1A"},
        {"face_id": "P1-IN-LOW", "kind": "ADD", "cause": "pit floor printed", "source": "sheet S3 handle 2B",
         "face": dict(faces()[5], face_id="P1-IN-LOW", status="CALCULATED", m2=4.800 * 1.20, new_line_id="L-P1",
                      tie="SAME", new_state="SOURCE_DERIVED")},
        {"face_id": "E1-BAND", "kind": "REMOVE", "cause": "edge owned by a parapet line", "source": "sheet S2 handle 3C"},
    ]
    out, applied = R.apply_deltas(src, deltas)
    assert [a["kind"] for a in applied] == ["REPLACE", "ADD", "REMOVE"]
    c = R.closure(src, out)
    g = c["CALCULATED||G"]
    assert g["source_m2"] == pytest.approx(5.300)
    assert g["bound_m2"] == pytest.approx(0.800 + 3.420 + 5.760)
    assert g["named_m2"] == pytest.approx(-0.180 + 5.760 - 0.900)
    assert g["residual_m2"] == 0.0


@pytest.mark.parametrize("bad", [
    {"face_id": "B1-SID", "kind": "REPLACE", "face": {"m2": 1.0}, "cause": "", "source": "S2"},
    {"face_id": "B1-SID", "kind": "REPLACE", "face": {"m2": 1.0}, "cause": "x", "source": ""},
    {"face_id": "NOPE", "kind": "REPLACE", "face": {"m2": 1.0}, "cause": "x", "source": "S2"},
    {"face_id": "B1-SID", "kind": "ADD", "face": {}, "cause": "x", "source": "S2"},
    {"face_id": "B1-SID", "kind": "MOVE", "cause": "x", "source": "S2"},
    {"face_id": "P1-IN", "kind": "REPLACE", "face": {"m2": 0.0}, "cause": "x", "source": "S2"},   # held as 0
])
def test_adverse_deltas_refused(bad):
    with pytest.raises(R.BindError):
        R.apply_deltas(R.rebind(faces(), LINES_OLD), [bad])


def test_closure_detects_a_dropped_face():
    src = R.rebind(faces(), LINES_OLD)
    out = [r for r in src if r["face_id"] != "B1-SOF"]
    with pytest.raises(R.BindError, match="residual"):
        R.closure(src, out)


def test_mirror_and_order_invariant():
    a = R.totals(R.rebind(faces(), LINES_OLD))
    b = R.totals(R.rebind(list(reversed(faces())), list(reversed(LINES_OLD))))
    assert a == b
    # mirrored villa (x -> -x): face areas do not depend on orientation
    assert R.fill_table(R.rebind(faces(), LINES_OLD)) == R.fill_table(R.rebind(list(reversed(faces())), LINES_OLD))


# ---- R-T332-8 FILL aggregate (rework r2 of D-T332-1: missing never becomes 0) ----------------------------------------

def _held(fid, **kw):
    return dict({"face_id": fid, "line_id": "L-P1", "element_id": "PIT:P1", "element": "PIT_WALL", "face_kind": "SIDE",
                 "contact": "FORM", "alternative": "", "method": "G", "status": "HELD", "m2": None}, **kw)


def _fill(fs):
    return R.fill_table(R.rebind(fs, LINES_OLD))["L-P1"]["totals"]["HELD||G"]


def test_fill_held_range_rows_sum_their_bounds():
    # P1 inner 4.800 m2/m, two printed candidate heights 1.00 .. 1.50 m -> 4.800 .. 7.200; outer 6.400 .. 9.600
    v = _fill([_held("A", lo=4.800, hi=7.200), _held("B", lo=6.400, hi=9.600)])
    assert v["m2"] is None
    assert v["lo"] == pytest.approx(11.200) and v["hi"] == pytest.approx(16.800)
    assert v["held_from"] is None and v["bound_classes"] == "RANGE 2"


def test_fill_unbounded_face_blanks_the_row_range():
    # adverse: one face of the row has no bound -> the row range is unknown (the old writer printed 4.800 .. 7.200)
    v = _fill([_held("A", lo=4.800, hi=7.200), _held("B")])
    assert v["m2"] is None and v["lo"] is None and v["hi"] is None
    assert v["bound_classes"] == "RANGE 1; UNBOUNDED 1"


def test_fill_single_bound_faces_blank_the_end_they_lack():
    v = _fill([_held("A", lo=4.800, hi=7.200), _held("B", hi=9.600)])          # AT_MOST: no low end
    assert v["lo"] is None and v["hi"] == pytest.approx(16.800)
    v = _fill([_held("A", lo=4.800, hi=7.200), _held("B", lo=6.400)])          # AT_LEAST: no high end
    assert v["lo"] == pytest.approx(11.200) and v["hi"] is None


def test_fill_held_from_kept_apart_from_the_range():
    v = _fill([_held("A", lo=4.800, hi=7.200), _held("B", held_from=0.900)])
    assert (v["lo"], v["hi"], v["held_from"]) == (pytest.approx(4.800), pytest.approx(7.200), pytest.approx(0.900))
    v = _fill([_held("B", held_from=0.900)])
    assert v["lo"] is None and v["hi"] is None and v["held_from"] == pytest.approx(0.900)


@pytest.mark.parametrize("bad", [
    {"m2": 0.0}, {"m2": "0.000000"}, {"lo": 0.0, "hi": 0.0}, {"lo": "0.000000"}, {"hi": "0.000000"},
    {"held_from": "0.000000"},
])
def test_adverse_fill_writer_printing_a_held_unbounded_face_as_zero_refused(bad):
    face = _held("R-UNB")
    row = dict({"line_id": "L-P1", "status": "HELD", "m2": "", "lo": "", "hi": "", "held_from": ""}, **bad)
    with pytest.raises(R.BindError, match="FILL L-P1"):
        R.check_fill_row(row, [face])


def test_fill_writer_accepts_the_correct_rows():
    R.check_fill_row({"line_id": "L-P1", "status": "HELD", "m2": "", "lo": "", "hi": "", "held_from": ""}, [_held("U")])
    R.check_fill_row({"line_id": "L-P1", "status": "HELD", "m2": "", "lo": "0.000000", "hi": "4.800000",
                      "held_from": ""}, [_held("J", lo=0.0, hi=4.8)])      # a face's own printed 0 low end is kept
    R.check_fill_row({"line_id": "L-B1", "status": "CALCULATED", "m2": "0.800000", "lo": "", "hi": "",
                      "held_from": ""}, [faces()[2]])


def test_adverse_fill_row_mixing_valued_and_blank_faces_refused():
    a, b = dict(faces()[2]), dict(faces()[3], m2=None)
    with pytest.raises(R.BindError, match="mixes valued and blank"):
        R._aggregate([a, b])
