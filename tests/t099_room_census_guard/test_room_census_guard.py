"""T-099: every face of a plan reported once - labelled faces under the space threshold and unlabelled rooms are HELD,
never silently lost (engine/source/room_census_guard.py), against hand truth.

Hand truth (plan_fixtures.py, written from the coordinates, not from engine output):
    BED 16.00 and BATH 5.04 m2      labelled rooms           -> LABELLED, passed through unchanged
    WC08 'W.C.' 1.00 x 0.80 = 0.80  under 1 m2 and thin      -> HELD SUB_THRESHOLD_LABELLED, wet
    STORE09 'STORE' 0.95 x 0.95     0.9025 m2, a SLIVER      -> HELD SUB_THRESHOLD_LABELLED, dry
    DUCT 'DUCT' 0.40 x 3.85 = 1.54  thin (2A/P 0.362)        -> HELD THIN_FACE_LABELLED (shaft: no room finish)
    SHAFT09 0.95 x 0.95, no label   0.9025 m2, nothing in it -> SLIVER (unchanged)
    UBLOCK 4.40, a WC block         no label                 -> TYPED_BY_EVIDENCE WET (Q-13 B: a toilet block)
    ULOOSE 5.60, WC as loose lines  on a furniture layer     -> HELD UNLABELLED_ROOM (Q-13 B); on a sanitary layer: WET
    UNONE 8.00, nothing             no label                 -> HELD UNLABELLED_ROOM (never a dry default)
    wall faces 54.3525 - 43.185 = 11.1675 m2                 -> THIN_FACE
Owner rules: UP-QTY-STATUS-001, UP-WET-001 / 002, Q-06 (a), Q-13 (B). Every case runs in mm, rotated 30 degrees,
mirrored, in metres, and all three together. SV-A / SV-C (tools/synth_villa, T-019) through ARCH_TAKEOFF_V2.11: SV-C's
unlabelled dining room (3.80 x 3.80 = 14.44 m2) HELD, every labelled room unchanged. Tests write only under tmp_path.
"""

from __future__ import annotations

import copy

import pytest

ezdxf = pytest.importorskip("ezdxf")

from engine.source import room_census_guard as G          # noqa: E402

from . import plan_fixtures as F                           # noqa: E402

TRANSFORMS = ["none", "rot30", "mirror", "metres", "rot30_mirror_metres"]
TOL = 1e-6


def _run(tmp_path, transform="none", **kw):
    p = tmp_path / f"t099_{transform}.dxf"
    centres = F.plan_dxf(p, transform=transform, **kw)
    ents = F.read_plan(p)
    S = F.spaces_v211(ents)
    before = copy.deepcopy(S["faces"])
    res = G.census(S["faces"], ents, F.ROLES, ents["unit_m"], frame="T099")
    assert S["faces"] == before                                   # the guard changes no face
    rec = {r["face_id"]: r for r in res["records"]}
    by_room = {}
    for k, (x, y) in centres.items():
        hit = [f for f in S["faces"] if G._inside_face(x, y, f)]
        assert len(hit) == 1, (k, len(hit))
        by_room[k] = (hit[0], rec[hit[0]["face_id"]])
    return S, res, by_room


# ------------------------------------------------------------------------------------------------ hand literals
def test_hand_literals():
    assert F.HAND_M2 == pytest.approx(F.HAND_LITERALS, abs=1e-12)
    assert F.HAND_OUTER_M2 == pytest.approx(54.3525, abs=1e-12)
    assert sum(F.HAND_LITERALS.values()) == pytest.approx(43.185, abs=1e-12)
    assert F.HAND_WALL_MASS == pytest.approx(11.1675, abs=1e-12)
    assert G.THRESHOLD_M2 == 1.0                                  # read from arch_rooms.MIN_SPACE_M2, never restated


# ------------------------------------------------------------------------------------------------ the hand plan
@pytest.mark.parametrize("transform", TRANSFORMS)
def test_every_room_has_its_hand_status_and_area(tmp_path, transform):
    S, res, by_room = _run(tmp_path, transform)
    for k, (status, reason, wet_dry) in F.EXPECT.items():
        f, r = by_room[k]
        assert (r["status"], r.get("reason"), r.get("wet_dry")) == (status, reason, wet_dry), k
        assert r["area_m2"] == pytest.approx(F.HAND_LITERALS[k], abs=TOL), k
        if status == "HELD":
            assert r["area_m2"] > 0 and r["basis"]                # a held space is never 0 and says why
    s = res["summary"]
    assert s["every_face_once"] and s["faces"] == len(S["faces"]) and s["held_without_area"] == []
    assert sum(r["area_m2"] for r in res["records"]) == pytest.approx(F.HAND_OUTER_M2, abs=TOL)
    assert s["by_status"]["THIN_FACE"]["m2"] == pytest.approx(F.HAND_WALL_MASS, abs=TOL)
    assert s["by_status"]["HELD:SUB_THRESHOLD_LABELLED"] == {"faces": 2, "m2": pytest.approx(1.7025, abs=TOL)}
    assert s["by_status"]["HELD:UNLABELLED_ROOM"] == {"faces": 2, "m2": pytest.approx(13.6, abs=TOL)}
    assert s["held"] == 5


@pytest.mark.parametrize("transform", ["none", "rot30_mirror_metres"])
def test_labelled_small_faces_carry_their_words_and_neighbours(tmp_path, transform):
    _S, _res, by_room = _run(tmp_path, transform)
    f, r = by_room["WC08"]
    assert f["class"] in ("WALL", "DOORWAY")                       # the room builder drops it: 2A/P = 0.444 < 0.45
    assert [(x["text"], x["code"], x["status"]) for x in r["labels"]] == [("W.C.", "BATHROOM", "TYPED")]
    assert r["differs_from_engine"] is True and r["neighbours"]   # it touches the wall faces round it
    f, r = by_room["STORE09"]
    assert f["class"] == "SLIVER" and r["labels"][0]["code"] == "STORE" and r["wet_dry"] == "DRY"
    f, r = by_room["DUCT"]
    assert r["labels"][0]["code"] == "SHAFT" and r["reason"] == "THIN_FACE_LABELLED"


@pytest.mark.parametrize("transform", ["none", "rot30", "mirror", "rot30_mirror_metres"])
def test_loose_wc_on_a_sanitary_layer_types_the_room_wet(tmp_path, transform):
    _S, _res, by_room = _run(tmp_path, transform, wc_layer=F.SAN)
    _f, r = by_room["ULOOSE"]
    assert (r["status"], r["reason"], r["wet_dry"]) == ("TYPED_BY_EVIDENCE", "FIXTURES_TOILET", "WET")
    assert r["area_m2"] == pytest.approx(5.6, abs=TOL)
    assert any(w["on_sanitary_layer"] for w in r["evidence"]["wc_linework"])


def test_loose_wc_on_a_furniture_layer_is_held_with_its_reason(tmp_path):
    _S, _res, by_room = _run(tmp_path)
    _f, r = by_room["ULOOSE"]
    assert r["evidence_reason"] == "WET_DRY_NOT_ESTABLISHED" and "Q-13" in r["rules"]
    assert r["evidence"]["wc_linework"] and not r["evidence"]["wc_linework"][0]["on_sanitary_layer"]
    _f, r = by_room["UNONE"]
    assert r["evidence_reason"] == "NO_LABEL_NO_EVIDENCE"
    _f, r = by_room["UBLOCK"]
    assert r["evidence"]["fixtures"] == ["WC"]


def test_engine_typed_by_an_appliance_block_is_held_and_flagged(tmp_path):
    """V2.11 names UNONE a KITCHEN from a cooker block alone (arch_rooms._evidence, label_source FIXTURES); under
    Q-13 B an appliance alone does not say which room it is: HELD, differs_from_engine."""
    _S, _res, by_room = _run(tmp_path, cooker_in_unone=True)
    f, r = by_room["UNONE"]
    assert f["class"] == "ROOM" and f["codes"] == ["KITCHEN"] and f["label_source"] == "FIXTURES"
    assert (r["status"], r["reason"], r["evidence_reason"]) == ("HELD", "UNLABELLED_ROOM", "WET_DRY_NOT_ESTABLISHED")
    assert r["differs_from_engine"] is True and r["area_m2"] == pytest.approx(8.0, abs=TOL)


def test_a_dropped_label_leaves_a_plain_thin_face(tmp_path):
    """the 0.80 m2 W.C. without its label: an unlabelled thin face with nothing inside is not a space."""
    _S, _res, by_room = _run(tmp_path, drop=("WC08", "BED"))
    assert by_room["WC08"][1]["status"] == "THIN_FACE"
    _f, r = by_room["BED"]                                          # a 16 m2 room losing its label is HELD, not lost
    assert (r["status"], r["reason"]) == ("HELD", "UNLABELLED_ROOM") and r["area_m2"] == pytest.approx(16.0)


# ------------------------------------------------------------------------------------------------ missing data
def test_without_entities_nothing_is_typed_and_labelled_slivers_still_held(tmp_path):
    S, _res, by_room = _run(tmp_path)
    res = G.census(S["faces"], frame="T099")
    rec = {r["face_id"]: r for r in res["records"]}
    for k in ("UBLOCK", "ULOOSE", "UNONE"):
        assert (rec[by_room[k][0]["face_id"]]["status"], rec[by_room[k][0]["face_id"]]["reason"]) == \
            ("HELD", "UNLABELLED_ROOM"), k
    for k in ("WC08", "STORE09"):                                   # the room builder's own codes still hold them
        assert rec[by_room[k][0]["face_id"]]["reason"] == "SUB_THRESHOLD_LABELLED", k
    assert rec[by_room["BED"][0]["face_id"]]["status"] == "LABELLED"
    assert res["summary"]["every_face_once"] and not res["summary"]["held_without_area"]


def test_entities_without_roles_or_units_are_refused():
    with pytest.raises(ValueError):
        G.census([], {"texts": []}, None, 0.001)
    with pytest.raises(ValueError):
        G.census([], {"texts": []}, {}, None)


def test_texts_without_a_position_and_degenerate_faces():
    sq = [(0, 0), (900, 0), (900, 950), (0, 950)]
    faces = [{"face_id": "A", "class": "SLIVER", "codes": [], "area_m2": 0.855, "polygon": sq, "hole_polygons": []},
             {"face_id": "B", "class": "WALL", "codes": [], "area_m2": 0.0, "polygon": [(0, 0), (1, 1)],
              "hole_polygons": []}]
    ents = {"texts": [{"id": "t1", "value": "W.C.", "x": None, "y": None}, {"id": "t2", "value": "1:50", "x": 450,
                                                                            "y": 450}],
            "segments": [], "arcs": [], "inserts": []}
    res = G.census(faces, ents, {}, 0.001)
    assert [r["status"] for r in res["records"]] == ["SLIVER", "THIN_FACE"]   # no label position, no room word
    assert res["summary"]["texts_without_position"] == ["t1"]


def test_label_in_a_hole_of_a_face_is_not_inside_it():
    outer = [(0, 0), (4000, 0), (4000, 4000), (0, 4000)]
    hole = [(1000, 1000), (1900, 1000), (1900, 1900), (1000, 1900)]
    faces = [{"face_id": "R", "class": "UNLABELLED", "codes": [], "area_m2": 15.19, "polygon": outer,
              "hole_polygons": [hole]},
             {"face_id": "S", "class": "SLIVER", "codes": ["BATHROOM"], "area_m2": 0.81, "polygon": hole,
              "hole_polygons": []}]
    ents = {"texts": [{"id": "t", "value": "حمام", "x": 1450, "y": 1450}], "segments": [], "arcs": [], "inserts": []}
    rec = {r["face_id"]: r for r in G.census(faces, ents, {}, 0.001)["records"]}
    assert rec["S"]["reason"] == "SUB_THRESHOLD_LABELLED" and rec["S"]["wet_dry"] == "WET"
    assert rec["R"]["reason"] == "UNLABELLED_ROOM" and rec["R"]["labels"] == []
    assert [n["face_id"] for n in rec["S"]["neighbours"]] == ["R"]


def test_held_compound_label_holds_the_room():
    sq = [(0, 0), (3000, 0), (3000, 2000), (0, 2000)]
    faces = [{"face_id": "C", "class": "UNLABELLED", "codes": [], "area_m2": 6.0, "polygon": sq, "hole_polygons": []}]
    ents = {"texts": [{"id": "t", "value": "مغسلة سيارات", "x": 1500, "y": 1000}], "segments": [], "arcs": [],
            "inserts": [{"id": "i", "name": "WC-01", "x": 1500, "y": 1800, "layer": "F"}]}
    r = G.census(faces, ents, {}, 0.001)["records"][0]
    assert (r["status"], r["reason"], r["wet_dry"]) == ("HELD", "UNLABELLED_ROOM", "REVIEW")   # the label decides


def test_policy_and_not_wired():
    p = G.policy_record()
    assert p["policy"] == "ROOM_CENSUS_GUARD_V1" and "UP-QTY-STATUS-001" in p["rules"] and "Q-13" in p["rules"]
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    users = [q for q in list((root / "engine").rglob("*.py")) + list((root / "tools").rglob("*.py"))
             if "room_census_guard" in q.read_text(encoding="utf-8") and q.name != "room_census_guard.py"]
    assert users == []                                              # read by no method (a later version wires it)


# ------------------------------------------------------------------------------------------------ SV-A / SV-C
def _villa(tmp_path, vid):
    from engine.source import arch_rooms as AR
    from tools.synth_villa import build as B
    from tools.synth_villa import compare as C
    from tools.synth_villa import villas as V
    var = V.FIRST_RUN[vid]
    p = tmp_path / f"{vid}.dxf"
    B.write_villa(vid, p, **var)
    cap, orig = [], AR.spaces

    def wrap(ents, roles, unit_m, **kw):
        S = orig(ents, roles, unit_m, **kw)
        cap.append((S, ents, roles, unit_m))
        return S
    AR.spaces = wrap
    try:
        C.run_engine(p, method="ARCH_TAKEOFF_V2.11")
    finally:
        AR.spaces = orig
    return B.truth_of(vid, **var), cap


@pytest.mark.parametrize("vid", ["SV-A", "SV-C"])
def test_synthetic_villas_labelled_rooms_unchanged_and_the_unlabelled_room_held(tmp_path, vid):
    truth, cap = _villa(tmp_path, vid)
    S, ents, roles, u = cap[0]
    before = copy.deepcopy(S["faces"])
    res = G.census(S["faces"], ents, roles, u, frame="GF")
    assert S["faces"] == before and res["summary"]["every_face_once"]
    rec = {r["face_id"]: r for r in res["records"]}
    for room in truth["floors"]["GF"]["rooms"]:
        x, y = room["point_m"]
        hit = [f for f in S["faces"] if G._inside_face(x / u, y / u, f)]
        assert len(hit) == 1, room["room_id"]
        f, r = hit[0], rec[hit[0]["face_id"]]
        assert r["area_m2"] == pytest.approx(room["area_m2"], abs=1e-4), room["room_id"]
        if room["labelled"]:
            assert r["status"] == "LABELLED" and r["engine_codes"] == f["codes"], room["room_id"]
        else:                                                      # SV-C dining room: drawn with no label
            assert (vid, room["room_id"]) == ("SV-C", "C-DIN")
            assert (r["status"], r["reason"], r["wet_dry"]) == ("HELD", "UNLABELLED_ROOM", "REVIEW")
            assert r["area_m2"] == pytest.approx(14.44, abs=1e-4)
    held = [r for r in res["records"] if r["status"] == "HELD"]
    assert len(held) == (1 if vid == "SV-C" else 0)


def test_an_unreadable_text_holds_a_small_face_and_is_noted_on_a_space():
    """an Arabic label in an unmapped SHX font arrives as mojibake (encoding SHX_UNMAPPED): in a 0.95 x 0.95 sliver it
    may be the room's label -> HELD UNDECODED_TEXT_INSIDE; in an unlabelled 3.00 x 2.00 space it is noted, the space
    stays HELD UNLABELLED_ROOM; one in no face is listed in the summary."""
    sl = [(0, 0), (950, 0), (950, 950), (0, 950)]
    sp = [(2000, 0), (5000, 0), (5000, 2000), (2000, 2000)]
    faces = [{"face_id": "S", "class": "SLIVER", "codes": [], "area_m2": 0.9025, "polygon": sl, "hole_polygons": []},
             {"face_id": "U", "class": "UNLABELLED", "codes": [], "area_m2": 6.0, "polygon": sp, "hole_polygons": []}]
    ents = {"texts": [{"id": "a", "value": "M—HAe", "x": 475, "y": 475, "encoding": "SHX_UNMAPPED"},
                      {"id": "b", "value": "MOSLy", "x": 3500, "y": 1000, "encoding": "SHX_UNMAPPED"},
                      {"id": "c", "value": "Ja—", "x": 9000, "y": 9000, "encoding": "SHX_UNMAPPED"}],
            "segments": [], "arcs": [], "inserts": []}
    res = G.census(faces, ents, {}, 0.001)
    rec = {r["face_id"]: r for r in res["records"]}
    assert (rec["S"]["status"], rec["S"]["reason"]) == ("HELD", "UNDECODED_TEXT_INSIDE") and \
        rec["S"]["undecoded_texts"] == ["a"]
    assert (rec["U"]["status"], rec["U"]["reason"]) == ("HELD", "UNLABELLED_ROOM") and rec["U"]["undecoded_texts"] == ["b"]
    assert res["summary"]["undecoded_texts_in_no_face"] == ["c"]
