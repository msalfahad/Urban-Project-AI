"""Phase 2B-1 WP-4: finish eligibility under the owner wet-area scope (ARCH_TAKEOFF_V2.3; engine.source.
owner_finish_scope) - UP-WET-001, UP-FIN-WALL-001, UP-FIN-PAINT-001, UP-FIN-PLASTER-001, UP-SKIRT-001, UP-THR-001,
UP-WP-ROOF-001.

Hand truth (tools/arch_synth villa, mm, wall 200): GF bath 2.8 x 2.4 (door 0.80), kitchen 2.8 x 6.4 (door 0.90 to the
living room), bedroom door 0.90, entrance 1.00 to the outside; 1F bath 2.8 x 2.4 (door 0.80), master door 0.90, a 1.00 m
passage stair | lobby. A doorway strip is the opening width x the 0.20 m wall."""

from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import kb_fixtures as KF                                      # noqa: E402
from engine.source import arch_measure as AM                  # noqa: E402
from engine.source import arch_rooms as AR                    # noqa: E402
from engine.source import owner_finish_scope as OFS           # noqa: E402

V22, V23 = "ARCH_TAKEOFF_V2.2", "ARCH_TAKEOFF_V2.3"
HEIGHTS = KF.FX.HEIGHT_FACTS                                   # plaster / paint 3.0 m, wall tile 2.4 m, door 2.1 m
FULL = copy.deepcopy(HEIGHTS)
del FULL["wall_heights"]["*"]["WALL_TILE"]                    # no wall-tile height given: full height by the rule


@pytest.fixture(scope="module")
def runs(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("villa")
    return {"v22": KF.villa_run(tmp, V22), "v23": KF.villa_run(tmp, V23),
            "v23_tile": KF.villa_run(tmp, V23, facts=HEIGHTS), "v23_full": KF.villa_run(tmp, V23, facts=FULL),
            "v22_full": KF.villa_run(tmp, V22, facts=FULL)}


def _rooms(arch, code):
    return [r for r in arch["rooms"] if code in (r.get("codes") or ())]


def _lines(run, code, item, element=None):
    room, arch = run
    ids = {r["room_id"] for r in _rooms(arch, code)}
    return [ln for ln in room["lines"] if ln["location"].get("room_id") in ids and ln["item_code"] == item
            and (element is None or ln.get("physical_element") == element)]


def _qty(lines):
    return round(sum(ln["measured_net"] or 0.0 for ln in lines if ln["evidence_state"] in (
        "SOURCE_DERIVED", "MEASURED", "PROVISIONAL")), 6)


def test_kitchen_pantry_and_ironing_rooms_take_the_wet_scope(runs):
    """UP-WET-001: bathrooms, kitchens, pantries and ironing rooms are wet areas (a laundry is, with a project
    confirmation flag); the villa kitchen gets wall tile and waterproofing and loses its skirting and paint band."""
    def room(*codes, kind=AR.SERVICE):
        return {"class": "ROOM", "codes": list(codes), "kind": kind}
    for code in ("BATHROOM", "KITCHEN", "PANTRY", "IRONING"):
        sc = OFS.finish_scope(room(code))
        assert sc["scope"] == OFS.WET and sc["flags"] == [], code
    lau = OFS.finish_scope(room("LAUNDRY", kind=AR.WET))
    assert lau["scope"] == OFS.WET and lau["flags"][0].startswith("WET_SCOPE_PROJECT_CONFIRMATION")
    assert OFS.finish_scope(room("BEDROOM", kind=AR.DRY))["scope"] == OFS.DRY
    v22, v23 = runs["v22_full"], runs["v23_full"]
    assert not _lines(v22, "KITCHEN", "FIN.WALL.TILE") and not _lines(v22, "KITCHEN", "FIN.WP.FLOOR")
    tile = _lines(v23, "KITCHEN", "FIN.WALL.TILE")
    assert tile and tile[0]["evidence_state"] == "SOURCE_DERIVED"
    assert _qty(_lines(v23, "KITCHEN", "FIN.WP.FLOOR")) == pytest.approx(2.8 * 6.4)
    assert _qty(_lines(v23, "KITCHEN", "FIN.WP.UPTURN")) == pytest.approx(2 * (2.8 + 6.4) * 0.20)
    (sk,) = _lines(v23, "KITCHEN", "FIN.SKIRTING")
    assert sk["evidence_state"] == "NOT_APPLICABLE_WITH_EVIDENCE" and _qty(_lines(v22, "KITCHEN", "FIN.SKIRTING")) > 0
    # the floor stays the measured floor (one finish, the same area)
    assert _qty(_lines(v23, "KITCHEN", "FIN.FLOOR.PORCELAIN", "floor")) == pytest.approx(2.8 * 6.4)


def test_wet_scope_never_spreads_to_an_open_plan_dry_space(runs):
    """an open plan of a kitchen and a living room keeps the dry treatment and says why (the wet zone is not drawn);
    the villa living room next to the kitchen stays dry; an unlabelled or merged face never takes the wet scope."""
    mixed = OFS.finish_scope({"class": "MIXED", "codes": ["KITCHEN", "LIVING"], "kind": AR.DRY})
    assert mixed["scope"] == OFS.REVIEW and mixed["flags"][0].startswith("OPEN_PLAN_WET_SCOPE_EXTENT")
    for cls in ("UNLABELLED", "MERGED"):
        assert OFS.finish_scope({"class": cls, "codes": [], "kind": None})["scope"] != OFS.WET
    v23 = runs["v23_full"]
    assert [r["finish_scope"]["scope"] for r in _rooms(v23[1], "LIVING")] == [OFS.DRY]
    assert _qty(_lines(v23, "LIVING", "FIN.SKIRTING")) == _qty(_lines(runs["v22_full"], "LIVING", "FIN.SKIRTING"))
    assert not _lines(v23, "LIVING", "FIN.WALL.TILE") and _qty(_lines(v23, "LIVING", "FIN.PAINT")) > 0


def test_wall_porcelain_runs_full_height_and_no_paint_band_is_asked(runs):
    """UP-FIN-WALL-001 / UP-FIN-PAINT-001: with no explicit wall-tile height the tile of every wet room runs to the
    clear height (3.0 m here); the band above it is NOT_APPLICABLE with evidence, never a question."""
    room, arch = runs["v23_full"]
    for code in ("BATHROOM", "KITCHEN"):
        for t in _lines(runs["v23_full"], code, "FIN.WALL.TILE"):
            assert t["calculation"]["inputs"]["height_m"] == pytest.approx(3.0)
        bands = _lines(runs["v23_full"], code, "FIN.PAINT")
        assert bands and all(b["evidence_state"] == "NOT_APPLICABLE_WITH_EVIDENCE" and
                             b["rule"]["rule_id"] == "UP-FIN-PAINT-001" for b in bands)
    assert not [u for u in room["unresolved"] if "WALL_TILE" in str(u.get("reason")) or
                str(u.get("reason")).startswith(("FINISH_ABOVE_WALL_TILE", "WALL_BAND_ABOVE"))]
    assert arch["owner_questions"]["summary"]["established_but_still_raised"] == 0
    # before (V2.2, the same drawing and heights): the bathroom tile, its skirting and the band above were blocked
    for item in ("FIN.WALL.TILE", "FIN.SKIRTING", "FIN.PAINT"):
        assert {ln["evidence_state"] for ln in _lines(runs["v22_full"], "BATHROOM", item)} == {"BLOCKED_RFI"}, item
    for item in ("FIN.SKIRTING", "FIN.PAINT"):
        assert {ln["evidence_state"] for ln in _lines(runs["v23_full"], "BATHROOM", item)} == {
            "NOT_APPLICABLE_WITH_EVIDENCE"}, item


def test_an_explicit_lower_tile_height_wins_and_is_flagged(runs):
    """a project wall-tile height (2.4 m) below the clear height governs (precedence over the owner rule), is
    flagged WALL_TILE_BELOW_OWNER_FULL_HEIGHT, and the band above it joins the same C group; the skirting of a wet
    room whose tile is not full height stays (UP-CER-004 exception)."""
    room, arch = runs["v23_tile"]
    for code in ("BATHROOM", "KITCHEN"):
        tiles = _lines(runs["v23_tile"], code, "FIN.WALL.TILE")
        assert tiles and all(t["calculation"]["inputs"]["height_m"] == pytest.approx(2.4) for t in tiles)
        assert all(s["evidence_state"] == "SOURCE_DERIVED" for s in _lines(runs["v23_tile"], code, "FIN.SKIRTING"))
    flags = [u for u in room["unresolved"] if str(u.get("reason")).startswith("WALL_TILE_BELOW_OWNER_FULL_HEIGHT")]
    bands = [u for u in room["unresolved"] if str(u.get("reason")).startswith("WALL_BAND_ABOVE_EXPLICIT_TILE")]
    assert len(flags) == len(bands) == 3                         # two bathrooms and the kitchen
    c = arch["owner_questions"]["by_category"]["C_RULE_CONFLICT"]
    assert [(g["group"], g["instances"]) for g in c] == [("WET_ROOM_WALL_TILE_HEIGHT", 6)]
    assert arch["owner_questions"]["summary"]["established_but_still_raised"] == 0


def test_wet_doorways_take_a_marble_threshold_from_geometry(runs):
    """UP-THR-001: the doorway strip of a door next to a wet room is a marble threshold, measured from the strip
    (width x wall thickness); the strip is in neither room floor, so it is counted once."""
    room, arch = runs["v23"]
    thr = sorted(round(ln["measured_net"], 6) for ln in room["lines"] if ln["item_code"] == "FIN.MARBLE.THRESHOLD")
    assert thr == pytest.approx(sorted([0.8 * 0.2, 0.9 * 0.2, 0.8 * 0.2]))
    for ln in room["lines"]:
        if ln["item_code"] == "FIN.MARBLE.THRESHOLD":
            assert ln["evidence_state"] == "SOURCE_DERIVED" and ln["rule"]["rule_id"] == "UP-THR-001"
            assert ln["calculation"]["inputs"]["strips"]
    assert _qty(_lines(runs["v23"], "BATHROOM", "FIN.FLOOR.WET_TILE")) == pytest.approx(2 * 2.8 * 2.4)
    assert not [ln for ln in room["lines"] if ln["item_code"] == "ARCH.THRESHOLD"]
    assert not [ln for ln in runs["v22"][0]["lines"] if ln["item_code"] == "FIN.MARBLE.THRESHOLD"]


def test_dry_doorways_continue_the_floor_porcelain_once(runs):
    """any other doorway: the floor porcelain continues through it, one line per opening, each strip in exactly one
    line; the external doorway is PROVISIONAL (an exterior sill is by specification)."""
    room, arch = runs["v23"]
    strips = [ln for ln in room["lines"] if ln["item_code"] == "FIN.FLOOR.PORCELAIN"
              and ln.get("physical_element") == "doorway strip"]
    by_w = sorted((round(ln["measured_net"], 6), ln["evidence_state"]) for ln in strips)
    assert by_w == [(0.18, "SOURCE_DERIVED"), (0.18, "SOURCE_DERIVED"), (0.2, "PROVISIONAL"), (0.2, "SOURCE_DERIVED")]
    ids = [s for ln in strips for s in ln["calculation"]["inputs"]["strips"]]
    assert len(ids) == len(set(ids))
    every = [ln["line_id"] for ln in room["lines"]]
    assert len(every) == len(set(every))
    assert arch["ledger"]["summary"]["conservation"]["ok"]


def test_door_jamb_plaster_is_measured_and_provisional(runs):
    """UP-FIN-PLASTER-001: 2 x wall thickness x door height + wall thickness x opening width, PROVISIONAL (the frame
    detail decides); the height is the owner fallback (HEIGHT_ASSUMED) or the source height when given."""
    for key, h, state in (("v23", 2.2, "ASSUMED"), ("v23_tile", 2.1, "SOURCE")):
        room, _arch = runs[key]
        jp = [ln for ln in room["lines"] if ln.get("physical_element") == "door jambs and head"]
        assert len(jp) == 6                                        # every door opening of the two plans
        for ln in jp:
            i = ln["calculation"]["inputs"]
            assert ln["evidence_state"] == "PROVISIONAL" and i["height_m"] == h and i["height_state"] == state
            assert ln["measured_net"] == pytest.approx(2 * i["wall_t_m"] * h + i["wall_t_m"] * i["width_m"])
        assert sorted(round(ln["calculation"]["inputs"]["width_m"], 3) for ln in jp) == [0.8, 0.8, 0.9, 0.9, 0.9, 1.0]


def test_passage_jambs_are_skirted_provisionally(tmp_path):
    """UP-SKIRT-001: the two jambs of a doorless opening between two dry rooms are skirted (2 x 0.20 m),
    PROVISIONAL; the room skirting runs keep their own lengths; a passage touching a stair / wet room gets none."""
    p = KF.dry_passage(tmp_path / "passage.dxf")
    room, _arch = KF.drawing_run(p, V23)
    (j,) = [ln for ln in room["lines"] if ln.get("physical_element") == "passage jambs"]
    assert j["measured_net"] == pytest.approx(0.40) and j["evidence_state"] == "PROVISIONAL"
    v22, _ = KF.drawing_run(p, V22)
    key = lambda r: sorted(round(ln["measured_net"], 6) for ln in r["lines"]                     # noqa: E731
                           if ln["item_code"] == "FIN.SKIRTING" and ln.get("physical_element") == "skirting")
    assert key(room) == key(v22) == [14.4, 16.8]
    rooms = [{"room_id": "A", "doors": [], "passages": ["OP-1"], "class": "ROOM", "codes": ["STAIR"],
              "kind": AR.STAIR}, {"room_id": "B", "doors": [], "passages": ["OP-1"], "class": "ROOM",
                                  "codes": ["LOBBY"], "kind": AR.CIRCULATION}]
    ops = [{"opening_id": "OP-1", "kind": "PASSAGE", "wall_t_m": 0.2, "width_m": 1.0}]
    assert OFS.passage_jamb_skirting({}, ops, rooms, "GF", line=AM._line) == []


def test_balconies_get_provisional_waterproofing():
    """UP-WP-ROOF-001: a balcony drawn as a space gets PROVISIONAL floor waterproofing; its upturn is by
    specification (a question, no quantity); a roof gets the 0.20 m upturn on its perimeter."""
    ctx = {"project_id": "P", "revision_set_sha256": "0" * 64, "documents": []}
    bal = {"room_id": "1F-BAL", "floor": "1F", "name_en": "balcony", "name_ar": "-", "codes": ["BALCONY"]}
    lines = OFS.exterior_wp_lines(ctx, bal, 6.0, 10.0, line=AM._line)
    (fl,) = [ln for ln in lines if ln["item_code"] == "FIN.WP.FLOOR"]
    (up,) = [ln for ln in lines if ln["item_code"] == "FIN.WP.UPTURN"]
    assert fl["measured_net"] == 6.0 and fl["evidence_state"] == "PROVISIONAL"
    assert up["measured_net"] is None and up["rfi"]["question"].startswith("EXTERIOR_WP_UPTURN_BY_SPECIFICATION")
    roof = dict(bal, room_id="RF-ROOF", codes=["ROOF"])
    (ru,) = [ln for ln in OFS.exterior_wp_lines(ctx, roof, 50.0, 30.0, line=AM._line)
             if ln["item_code"] == "FIN.WP.UPTURN"]
    assert ru["measured_net"] == pytest.approx(6.0) and ru["evidence_state"] == "PROVISIONAL"
    assert OFS.exterior_wp_lines(ctx, dict(bal, codes=["GARDEN"]), 6.0, 10.0, line=AM._line) == []


def test_a_dry_room_keeps_its_skirting(runs):
    """UP-SKIRT-001: a dry room keeps its measured skirting, unchanged from V2.2."""
    for code in ("BEDROOM", "LIVING", "MASTER_BEDROOM"):
        a, b = _lines(runs["v22"], code, "FIN.SKIRTING", "skirting"), _lines(runs["v23"], code, "FIN.SKIRTING",
                                                                            "skirting")
        assert a and [(x["measured_net"], x["evidence_state"]) for x in a] == \
            [(x["measured_net"], x["evidence_state"]) for x in b]
