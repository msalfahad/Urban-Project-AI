"""T-447 / STAIR_ROOM_HELD_FACES_V1 (R-T447-1 .. 5): settling held stair-room skirting faces.

Hand villa K447 (not Alsenan). A stair hall at +0.60 beside a straight flight with a 0.15 m divider band, a doorless
opening to a basin niche, and an 'L' corridor at +6.80 at the top of a flight.
By hand:
  divider band faces 2.10 + 0.15 (end): section shows posts + top / mid rail, flight visible below -> NOT_APPLICABLE
  same band where a section draws a solid upstand to the floor -> FACE 2.10 lm
  niche opening P-K2, jambs 2 x 0.25: reveal floor = niche threshold, niche fully wall-tiled -> NOT_APPLICABLE;
  ordinary dry passage with all five conditions true -> 0.50 lm INCLUDED (PROVISIONAL); one unknown -> HELD
  strip 0.15 x 0.80 with the +0.10 level mark inside and nothing drawn -> FLOOR 0.120 m2
  corridor outline: 3.0 x 1.8 + 2.0 x 1.0 -> perimeter 2 x 5.0 + 1.8 + 1.0 + 0.8 (step) = 13.600, area 7.400;
    with a 0.40 top-going strip over x 1.0 .. 2.0 -> + 2 x 0.40 = 14.400
"""
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RES = ROOT / "research" / "agents_t447"
sys.path.insert(0, str(RES))
import held_faces_v1 as H  # noqa: E402

BALUSTRADE = {"wall_cut": False, "section_balustrade_open_below_rail": True}
SOLID = {"wall_cut": False, "section_solid_to_floor": True}


def test_balustrade_edge_not_applicable():
    r = H.guard_edge({"id": "K-BAND-E", "length": 2.10, "refs": ["K section B-B"], "evidence": BALUSTRADE})
    assert r["status"] == H.NOT_APPLICABLE and r["lm"] is None
    assert H.check_guard(dict(r, kind="GUARD"))


def test_solid_upstand_is_face():
    r = H.guard_edge({"id": "K-BAND-E", "length": 2.10, "refs": ["K section B-B"], "evidence": SOLID})
    assert r["status"] == H.FACE and r["lm"] == pytest.approx(2.10)


def test_adverse_balustrade_edge_skirted_as_wall_face():
    r = H.guard_edge({"id": "K-BAND-E", "length": 2.10, "refs": ["K"], "evidence": BALUSTRADE})
    r["lm"] = 2.10                                    # someone skirts the guard edge
    with pytest.raises(H.Refused, match="balustrade edge skirted"):
        H.check_guard(r)


def test_guard_without_evidence_is_held_blank_never_zero():
    r = H.guard_edge({"id": "K-BAND-E", "length": 2.10, "evidence": {}})
    assert r["status"] == H.HELD and r["lm"] is None and r["candidate_lm"] == pytest.approx(2.10)
    r["lm"] = 0
    with pytest.raises(H.Refused, match="never 0"):
        H.check_guard(r)


def test_guard_contradictory_and_unreferenced():
    with pytest.raises(H.Refused):
        H.guard_edge({"id": "x", "length": 1.0, "refs": ["a"], "evidence": dict(SOLID, **BALUSTRADE)})
    with pytest.raises(H.Refused, match="without a drawing reference"):
        H.guard_edge({"id": "x", "length": 1.0, "evidence": BALUSTRADE})


def test_units_slip_refused():
    with pytest.raises(H.Refused, match="unit slip"):
        H.guard_edge({"id": "x", "length": 2100.0, "refs": ["a"], "evidence": BALUSTRADE})
    with pytest.raises(H.Refused, match="unit slip"):
        H.doorless_jambs({"opening_id": "P", "jambs": [250.0], "conditions": {c: True for c in H.JAMB_CONDITIONS}})


def _jamb(**cond):
    c = {k: True for k in H.JAMB_CONDITIONS}
    c.update(cond)
    ev = {k: "drawn / owner evidence" for k, v in c.items() if v is False}
    return {"opening_id": "P-K2", "jambs": [0.25, 0.25], "conditions": c, "evidence": ev}


def test_jambs_all_true_included_provisional():
    r = H.doorless_jambs(_jamb())
    assert r["status"] == H.INCLUDED_PROVISIONAL and r["lm"] == pytest.approx(0.50)


def test_jambs_wet_niche_not_applicable():
    r = H.doorless_jambs(_jamb(floor_finish_reaches_jamb=False, not_full_wall_tile_room=False))
    assert r["status"] == H.NOT_APPLICABLE and r["lm"] is None
    assert set(r["failed"]) == {"floor_finish_reaches_jamb", "not_full_wall_tile_room"}


def test_jambs_unknown_held_and_false_needs_evidence():
    r = H.doorless_jambs(_jamb(not_full_wall_tile_room=None))
    assert r["status"] == H.HELD and r["lm"] is None and r["candidate_lm"] == pytest.approx(0.50)
    bad = _jamb(no_door=False)
    bad["evidence"] = {}
    with pytest.raises(H.Refused, match="without evidence"):
        H.doorless_jambs(bad)
    with pytest.raises(H.Refused, match="not stated"):
        H.doorless_jambs({"opening_id": "P", "jambs": [0.2], "conditions": {"no_door": True}})
    with pytest.raises(H.Refused, match="opening id"):
        H.doorless_jambs({"opening_id": "", "jambs": [0.2], "conditions": {}})


def test_strip_with_level_mark_is_floor():
    r = H.strip_class({"id": "K-STRIP", "w": 0.15, "d": 0.80, "visible_elements": [], "level_mark_inside": 0.10})
    assert r["class"] == "FLOOR" and r["m2"] == pytest.approx(0.12) and r["level"] == 0.10


def test_strip_solid_and_held():
    r = H.strip_class({"id": "K", "w": 0.15, "d": 0.80,
                       "visible_elements": [{"handle": "k9", "closed_outline": True}], "level_mark_inside": 0.10})
    assert r["class"] == "SOLID"
    r = H.strip_class({"id": "K", "w": 0.15, "d": 0.80, "visible_elements": []})
    assert r["class"] == H.HELD and r["m2"] is None
    r = H.strip_class({"id": "K", "w": 0.15, "d": 0.80, "visible_elements": [], "section_flat": True,
                       "adjacent_level": 0.6, "step_line": True})
    assert r["class"] == H.HELD


def test_histogram_perimeter_and_trace():
    base = [(0.0, 3.0, 1.8), (3.0, 5.0, 1.0)]
    assert H.histogram_perimeter(base) == pytest.approx(13.6)
    assert H.histogram_area(base) == pytest.approx(7.4)
    ext = [(0.0, 1.0, 1.8), (1.0, 2.0, 2.2), (2.0, 3.0, 1.8), (3.0, 5.0, 1.0)]
    assert H.histogram_perimeter(ext) == pytest.approx(14.4)
    t = H.trace(14.4, {"base": base, "ext": ext})
    assert [x["matches"] for x in t] == [False, True]
    # mirror: the same outline reversed in x has the same perimeter
    mir = [(5.0 - b, 5.0 - a, h) for a, b, h in ext]
    assert H.histogram_perimeter(mir) == pytest.approx(14.4)
    with pytest.raises(H.Refused, match="contiguous"):
        H.histogram_perimeter([(0, 1, 1), (1.5, 2, 1)])


def test_classify_added():
    t = H.classify_added([{"id": "a", "lm": 0.4, "cls": "STAIR_SIDE", "owner": "F-K"},
                          {"id": "b", "lm": 0.4, "cls": "GUARD"}])
    assert t == {"ROOM_FACE": 0.0, "STAIR_SIDE": 0.4, "GUARD": 0.4}
    with pytest.raises(H.Refused, match="owning stair"):
        H.classify_added([{"id": "a", "lm": 0.4, "cls": "STAIR_SIDE"}])


def test_settle_overlap_level_aware():
    face = {"id": "F1", "kind": "FACE", "status": H.FACE, "lm": 0.2, "line": "K:y=5", "t0": 1.0, "t1": 1.2,
            "level": 0.1}
    above = {"id": "winders", "line": "K:y=5", "t0": 0.0, "t1": 1.2, "lo": 2.0, "hi": 3.0}
    assert H.settle([face], [above])["confirmed_lm"] == pytest.approx(0.2)
    same = {"id": "room", "line": "K:y=5", "t0": 1.1, "t1": 2.0, "level": 0.1}
    with pytest.raises(H.Refused, match="shared"):
        H.settle([face], [same])
    with pytest.raises(H.Refused, match="held row carries"):
        H.settle([{"id": "h", "status": H.HELD, "lm": 0.3}])


# ------------------------------------------------------------------------------------------------ Alsenan pins
def test_alsenan_rebuild_and_pins():
    sys.path.insert(0, str(RES))
    import t447_alsenan as A
    x = json.loads(A.EXTRACT.read_text(encoding="utf-8"))
    faces, summ = A.write_outputs(x)
    assert A.FACES.read_text(encoding="utf-8") == faces
    assert A.SUMMARY.read_text(encoding="utf-8") == summ
    s = json.loads(summ)
    assert s["skirting_lm"]["gf_task_total_after"] == pytest.approx(6.25)
    assert s["finding_a_strip"]["class"] == "FLOOR" and s["finding_a_strip"]["m2"] == pytest.approx(0.12)
    assert s["item3_strip"]["class"] == "FLOOR" and s["item3_strip"]["m2"] == pytest.approx(0.23)
    assert [t["matches"] for t in s["finding_b_trace"]] == [False, True]
    assert s["finding_b_added"]["STAIR_SIDE"] == pytest.approx(0.35)
    assert s["finding_b_added"]["GUARD"] == pytest.approx(0.35)
    assert s["finding_c"]["drawn_face_m"] == pytest.approx(2.0)
    assert s["finding_c"]["split_128A_m"] == {"on_column_2F72": 0.2, "on_wall_run": 0.4}
    assert s["finding_c"]["diff_m"] == pytest.approx(0.006)
    st = {r["id"]: r for r in csv_rows(faces)}
    for bid in ("BAND-E", "BAND-W", "BAND-END", "OP-020-JAMBS"):
        assert st[bid]["status"] == "NOT_APPLICABLE" and st[bid]["lm"] == ""
    assert st["UNDER-WINDERS"]["status"] == "UNKNOWN" and st["UNDER-WINDERS"]["lm"] == ""
    assert all(c["layer_ok"] and c["points_ok"] for c in x["handle_checks"])
    assert {m["handle"]: m["inside"] for m in x["level_marks"]} == {"4AB": True, "412": True}
    assert x["sweeps"]["strip_GF_ST_CN"]["hits"] == []


def csv_rows(text):
    import csv
    import io
    return list(csv.DictReader(io.StringIO(text)))
