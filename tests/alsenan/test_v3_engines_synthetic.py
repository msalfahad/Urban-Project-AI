"""V3 (Alsenan final BOQ round) generic engines - synthetic tests, no project data.

legacy_text (legacy Arabic SHX decode), text_role_v3 (source-scoped tag families, bilingual corroboration),
room_topology_v3 (frozen TS01 + injection points; equal to room_topology.run without injections),
opening_completion (near-collinear door closure, jamb-frame closure B, double-leaf motif, door-in-wall-gap,
drafting-gap join), urban_methods_v3 (authority order, fallbacks)."""

from __future__ import annotations

import math

from engine.source import legacy_text as LT
from engine.source import opening_completion as OC
from engine.source import room_topology as RT
from engine.source import room_topology_v3 as RT3
from engine.source import text_role as TX
from engine.source import text_role_v3 as TR3
from engine.source import topology as T
from engine.source import topology_closures as TC
from engine.source import urban_methods_v3 as UM3
from tests.r8_8 import helpers as H


# ------------------------------------------------------------------ legacy_text
def test_keyboard_101_family_decodes_by_key_and_ignores_case():
    assert LT.font_family("xarb.shx") == LT.ARABIC_KEYBOARD_101
    d = LT.decode("hgfpv", LT.ARABIC_KEYBOARD_101)
    assert d["text"] == "البحر" and d["state"] == LT.DECODED
    assert LT.decode("HGFPV", LT.ARABIC_KEYBOARD_101)["text"] == "البحر"


def test_xarab_family_decodes_glyph_table_and_reports_unknown_code_points():
    assert LT.font_family("X-ARAB1B.SHX") == LT.XARAB_GLYPH
    assert LT.decode("HMam", LT.XARAB_GLYPH)["text"] == "حمام"
    d = LT.decode("HMaK", LT.XARAB_GLYPH)
    assert d["state"] == LT.PARTIAL and d["unknown"] == ["K"] and d["text"].endswith("?")


def test_a_latin_font_is_not_a_legacy_arabic_font():
    assert LT.font_family("romant") is None
    assert LT.decode("BATH", None)["state"] == LT.NOT_LEGACY


def test_corroboration_needs_the_arabic_term_of_the_english_room_word():
    assert LT.corroborate("BATH", "حمام")["state"] == "CORROBORATED"
    assert LT.corroborate("BATH", "مطبخ")["state"] == "NOT_CORROBORATED"
    assert LT.corroborate("XYZ", "حمام")["state"] == "NO_LEXICON_ENTRY"


# ------------------------------------------------------------------ text_role_v3
def _tag(h, words, x, y, occ, layer="1"):
    return [H.text(h + i, w, x, y - 10 * i, path=(occ,), layer=layer) for i, w in enumerate(words)]


def test_a_tag_family_spanning_regions_establishes_the_lone_tag_of_another_region():
    a = H.inp(H.box(1, 0, 0, 100, 100), texts=_tag(10, ["BEDROOM"], 50, 50, "80") + _tag(20, ["KITCHEN"], 20, 20, "81"),
              region_id="R1")
    b = H.inp(H.box(5, 0, 0, 100, 100), texts=_tag(30, ["BATH"], 50, 50, "82"), region_id="R2")
    alone = TX.classify(b)
    assert {r.role for r in alone.values()} == {TX.ROOM_LABEL_CANDIDATE}
    v3 = TR3.classify(b, [a, b])
    assert {r.role for r in v3.values()} == {TX.ROOM_LABEL_ESTABLISHED}
    assert set(v3) == {t.identity.key for t in b.texts}          # roles of the requested region only


def test_a_different_source_revision_is_not_part_of_the_family():
    a = H.inp(texts=_tag(10, ["BEDROOM"], 50, 50, "80") + _tag(20, ["KITCHEN"], 20, 20, "81"), revision=H.rev("REV_B"))
    b = H.inp(texts=_tag(30, ["BATH"], 50, 50, "82"))
    assert {r.role for r in TR3.classify(b, [a, b]).values()} == {TX.ROOM_LABEL_CANDIDATE}


def test_bilingual_corroboration_establishes_a_lone_tag_and_a_mismatch_does_not():
    b = H.inp(texts=[H.text(40, "MAID R.", 50, 50, path=("90",), layer="5"),
                     H.text(41, "O—F_yGa™M_y", 50, 40, path=("90",), layer="ARNOTE")])
    fonts = {"40": "romant", "41": "X-ARAB.shx"}
    assert {r.role for r in TR3.classify(b, [b]).values()} == {TX.ROOM_LABEL_CANDIDATE}
    v3 = TR3.classify(b, [b], font_of_handle=fonts)
    assert {(r.role, r.rule_id) for r in v3.values()} == {(TX.ROOM_LABEL_ESTABLISHED, TR3.BILINGUAL_RULE)}
    wrong = H.inp(texts=[H.text(40, "MAID R.", 50, 50, path=("90",), layer="5"),
                         H.text(41, "HMam", 50, 40, path=("90",), layer="ARNOTE")])
    assert {r.role for r in TR3.classify(wrong, [wrong], font_of_handle=fonts).values()} == {TX.ROOM_LABEL_CANDIDATE}


# ------------------------------------------------------------------ room_topology_v3 equivalence
def _sig(r):
    return sorted((round(s["area"], 6), s["status"], tuple(s["issues"]), tuple(map(str, s["labels"])))
                  for s in r["sites"])


def test_v3_without_injections_equals_the_frozen_run():
    inp = H.inp(H.two_rooms(gap=(150, 250)), texts=[H.text(50, "A", 250, 200), H.text(51, "B", 750, 200)])
    a = RT.run(inp, frame_insert=None, closure_policy=TC.POLICY_ID)
    b = RT3.run(inp, frame_insert=None, closure_policy=TC.POLICY_ID)
    assert _sig(a) == _sig(b) and a["openings"] == b["openings"] and "_items" in b


# ------------------------------------------------------------------ opening_completion
def _door_wall(skew=2e-9, frames=True):
    """Two rooms separated by a 15-unit wall band (y 0..15); a door opening x 400..520 with no caps; the top face
    right of the opening is skewed by a sub-nanometre amount (an export artefact)."""
    p = [H.seg(1, 0, -400, 1000, -400), H.seg(2, 1000, -400, 1000, 400), H.seg(3, 1000, 400, 0, 400),
         H.seg(4, 0, 400, 0, -400),
         H.seg(5, 0, 15, 400, 15), H.seg(6, 1000, 15, 520, 15 + skew),       # drawn from the far end
         H.seg(7, 0, 0, 400, 0), H.seg(8, 520, 0, 1000, 0)]
    door = [H.part(20, "ARC", (400, 15, 100, 0.0, math.pi / 2), layer="DOOR", path=("70",)),
            H.seg(21, 400, 15, 400, 115, layer="DOOR", path=("70",))]
    if frames:
        door += [H.seg(22, 400, 15, 400, 0, layer="DOOR", path=("70",)),
                 H.seg(23, 520, 15, 520, 0, layer="DOOR", path=("70",))]
    return p + door


def _two_pass(inp):
    kw = dict(frame_insert=None, closure_policy=TC.POLICY_ID)
    r1 = RT3.run(inp, **kw)
    oc = OC.derive(r1, inp)
    return r1, oc, RT3.run(inp, extra_closures=oc["closures"], extra_opening_status=oc["opening_status"], **kw)


def _labelled(r):
    return sorted(tuple(map(str, s["labels"])) for s in r["sites"] if s["labels"])


def test_near_collinear_face_leaves_the_frozen_door_unresolved_and_v3_closes_it_with_a_jamb_frame_b():
    inp = H.inp(_door_wall(), texts=[H.text(50, "A", 200, 200), H.text(51, "B", 200, -200)])
    frozen = RT.run(inp, frame_insert=None, closure_policy=TC.POLICY_ID)
    (st,) = frozen["openings"].values()
    assert st["state"] == T.OPENING_CLOSURE_UNRESOLVED
    r1, oc, r2 = _two_pass(inp)
    (rec,) = oc["doors"].values()
    assert rec["state"] == "CLOSED" and rec["rule"] == OC.NEAR_COLLINEAR_RULE
    assert rec["closure_b_rule"] == OC.JAMB_FRAME_B_RULE and abs(rec["closure_b_evidence"]["depth"] - 15) < 1e-6
    assert rec["affects_wall_quantity"] is False and rec["affects_finish_quantity"] is False
    assert len(_labelled(r2)) == 2                                  # the two rooms no longer share a site


def test_an_exactly_collinear_face_is_already_closed_by_the_frozen_rule_and_left_alone():
    inp = H.inp(_door_wall(skew=0.0), texts=[H.text(50, "A", 200, 200), H.text(51, "B", 200, -200)])
    r1, oc, _ = _two_pass(inp)
    (st,) = r1["openings"].values()
    assert st["state"] == "CLOSED" and not [k for k, v in oc["doors"].items() if v.get("rule") == OC.NEAR_COLLINEAR_RULE]


def test_without_frame_lines_no_closure_b_is_invented():
    inp = H.inp(_door_wall(frames=False), texts=[H.text(50, "A", 200, 200), H.text(51, "B", 200, -200)])
    _, oc, _ = _two_pass(inp)
    (rec,) = oc["doors"].values()
    assert rec["state"] == "CLOSED" and rec["closure_b"] is None


def test_jamb_frame_b_needs_a_frame_at_each_end_at_equal_depth():
    a = (0.0, 0.0, 100.0, 0.0)
    g, ev = OC.jamb_frame_b(a, [(0, 0, 0, -20), (100, 0, 100, -20)], [], 0.1, 10.0)
    assert g == (0.0, -20.0, 100.0, -20.0)
    assert OC.jamb_frame_b(a, [(0, 0, 0, -20), (100, 0, 100, -25)], [], 0.1, 10.0)[0] is None
    assert OC.jamb_frame_b(a, [(0, 0, 0, -20)], [], 0.1, 10.0)[0] is None
    blocked = [T.BoundaryItem("X", "SEGMENT", (50, 1, 50, -30), "WALL")]
    assert OC.jamb_frame_b(a, [(0, 0, 0, -20), (100, 0, 100, -20)], blocked, 0.1, 10.0) == (None, "INTERVENING_BOUNDARY")


def _double_leaf(occ="80", r=90.0, hinge_gap=None):
    hg = 2 * r if hinge_gap is None else hinge_gap
    return [H.part(30, "ARC", (310, 10, r, 0.0, math.pi / 2), layer="FURN", path=(occ,)),
            H.part(31, "ARC", (310 + hg, 10, r, math.pi / 2, math.pi), layer="FURN", path=(occ,))]


def test_double_leaf_motif_is_found_from_geometry_only():
    m = OC.double_leaf_doors(H.inp(_double_leaf()))
    assert list(m) == ["80"] and abs(m["80"]["width"] - 180) < 1e-9 and m["80"]["kind"] == OC.DOUBLE_LEAF_DOOR


def test_two_arcs_that_do_not_meet_or_a_single_arc_are_not_a_double_leaf_door():
    assert OC.double_leaf_doors(H.inp(_double_leaf(hinge_gap=260))) == {}
    assert OC.double_leaf_doors(H.inp(_double_leaf()[:1])) == {}
    assert OC.double_leaf_doors(H.inp(_double_leaf(r=20))) == {}          # 200 mm: below a leaf


def _gap_band(a, b):
    return {"band_id": f"WB-{a}", "state": "WALL_BAND_ESTABLISHED", "faces": [f"F{a}", f"G{a}"], "axis": (1.0, 0.0),
            "width": 20.0, "interval": b, "ends": [{"outward": -1, "kind": "CAPPED"}, {"outward": 1, "kind": "CAPPED"}]}


def test_wall_gaps_finds_a_clear_gap_between_collinear_bands_and_reports_what_crosses_it():
    bands = [_gap_band(1, (0.0, 300.0)), _gap_band(2, (500.0, 1000.0))]
    geom = {"F1": (0, 0, 300, 0), "G1": (0, 20, 300, 20), "F2": (500, 0, 1000, 0), "G2": (500, 20, 1000, 20)}
    (g,) = OC.wall_gaps(bands, geom, [], unit_native_to_mm=10.0)
    assert abs(g["gap"] - 200) < 1e-9 and g["blocked_by"] == []
    (g,) = OC.wall_gaps(bands, geom, [(400, -50, 400, 50, ("WALL",))], unit_native_to_mm=10.0)
    assert g["blocked_by"] == ["WALL"]


def test_drafting_gap_join_closes_a_millimetre_miss_and_not_a_real_gap():
    def room(short):
        return [H.seg(1, 0, 0, 1000, 0), H.seg(2, 1000, 0, 1000, 400), H.seg(3, 1000, 400, 0, 400),
                H.seg(4, 0, 400, 0, short), H.seg(5, 0, 0, -500, 0), H.seg(6, -500, 0, -500, 400),
                H.seg(7, -500, 400, 0, 400)]
    for short, joined in ((0.3, True), (3.0, False)):               # 3 mm vs 30 mm (unit = 10 mm)
        inp = H.inp(room(short), texts=[H.text(50, "A", 500, 200), H.text(51, "B", -250, 200)])
        _, oc, r2 = _two_pass(inp)
        assert bool(oc["drafting_gaps"]) is joined
        assert (len(_labelled(r2)) == 2) is joined
        for j in oc["drafting_gaps"]:
            assert j["affects_wall_quantity"] is False and j["class"] == "DRAWING_GAP"


# ------------------------------------------------------------------ urban_methods_v3
def test_authority_order_and_fallback_labelling():
    assert UM3.pick([{"authority": UM3.URBAN_FALLBACK, "value": 0.10},
                     {"authority": UM3.SOURCE, "value": 0.12}])["value"] == 0.12
    assert UM3.pick([{"authority": UM3.URBAN_FALLBACK, "value": None}])["authority"] == UM3.BLOCKED
    r = UM3.resolve("URBAN-RESIDENTIAL-FLOOR-BUILDUP-FALLBACK@v1")
    assert r["authority"] == UM3.URBAN_FALLBACK and r["parameters"]["buildup_m"] == 0.10
    o = UM3.resolve("URBAN-RESIDENTIAL-FLOOR-BUILDUP-FALLBACK@v1", {"id": "PF-1", "parameters": {"buildup_m": 0.08}})
    assert o["authority"].startswith(UM3.PROJECT_OWNER_FACT) and o["parameters"]["buildup_m"] == 0.08
    assert not UM3.applies("URBAN-DRY-FLOOR-PORCELAIN-DEFAULT@v1", "WET_ROOM_FLOOR")
    assert UM3.register()["methods"] and "URBAN-REBAR-NET-AND-PROCUREMENT@v1" in UM3.ALL_METHODS
