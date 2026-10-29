"""T-329 Alsenan pins: the committed ledger rebuilds byte for byte from the merged T-312 / T-311 inputs, every tiled
face carries one backing face, every room closes to its tile faces (0.0000 m2) and to its walked contour, every
wet-room FIN.PLASTER line of the V3.0.19 extract is mapped once, the six held rooms stay HELD, no coordinate."""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t329"
T312 = ROOT / "research" / "agents_t312"
sys.path.insert(0, str(HERE))

import t329_alsenan as A           # noqa: E402
import t329_backing_rules as R     # noqa: E402


def _rows(p):
    with open(p, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def test_rebuild_byte_identical():
    for p, s in A.render().items():
        assert p.read_text(encoding="utf-8") == s, p.name


def test_every_tiled_face_has_one_backing_face():
    faces = _rows(HERE / "BACKING_FACE_LEDGER_T329.csv")
    tiles = _rows(T312 / "FACE_LEDGER_T312.csv")
    assert [f["face_id"] for f in faces] == [t["face_id"] for t in tiles]
    for f, t in zip(faces, tiles):
        assert f["backing"].startswith("YES") == (t["scope"] == "TILED")
        if f["backing_owner_m2"]:
            assert f["backing_owner_m2"] == f["tile_owner_m2"] == t["owner_net_m2"]
            assert f["band_owner_m2"] == "0.0000"
            assert f["closure_m2"] == "0.0000"


def test_rooms_close_to_tile_and_contour():
    rooms = _rows(HERE / "ROOM_BACKING_T329.csv")
    assert len(rooms) == 18
    assert all(r["contour_residual_m"] == "0.0000" for r in rooms)
    det = [r for r in rooms if r["status"] != "HELD"]
    assert len(det) == 12 and all(r["closure_to_tile_m2"] == "0.0000" for r in det)
    held = sorted(r["room"] for r in rooms if r["status"] == "HELD")
    assert held == ["GF-02", "GF-03", "GF-05", "GF-06", "GF-10", "GF-11"]
    assert all(r["backing_owner_m2"] == "" and r["held_item"] for r in rooms if r["status"] == "HELD")


def test_hand_room_1f12():
    r = next(x for x in _rows(HERE / "ROOM_BACKING_T329.csv") if x["room"] == "1F-12")
    hand = 8.70 * 3.35 - 0.80 * 2.20 - 0.50 * (3.00 - 0.84)
    assert abs(float(r["backing_owner_m2"]) - hand) < 1e-3


def test_line_map_every_wet_plaster_line_once():
    lines = _rows(HERE / "PLASTER_LINE_MAP_T329.csv")
    ids = [x["line_id"] for x in lines]
    assert len(ids) == len(set(ids)) == 19
    tile = {t["rooms"]: t for t in _rows(T312 / "LINE_SUMMARY_T312.csv")}
    wet = [x for x in lines if x["element_id"].endswith(":plaster") and x["engine_room"] != "GF-RC06FED"]
    assert len(wet) == 17 and all(x["candidate_state"] == "BLOCKED_RFI" for x in wet)
    for x in lines:
        if x["proposal"] == "FILL":
            assert x["proposed_m2"] == tile[x["room"]]["ledger_owner_m2"]
        if x["proposal"].startswith("HELD"):
            assert x["proposed_m2"] == "" and tile[x["room"]]["ledger_status"] == "HELD"
    assert sum(1 for x in lines if x["proposal"] == "FILL") == 12
    assert sum(1 for x in lines if x["proposal"].startswith("HELD")) == 6


def test_named_totals():
    s = json.loads((HERE / "summary.json").read_text(encoding="utf-8"))
    o = s["owner_method"]
    assert o["in_wet_lines_m2"] == 307.9616 and o["pantry_m2"] == 32.3422 and o["backing_m2"] == 340.3038
    assert o["band_above_tile_m2"] == 0.0 and o["closure_to_tile_max_abs_m2"] == 0.0
    assert s["faces"] == {"backing": 115, "open_sides": 2}
    assert s["freelancer"]["diff_m2"] == 12.5216 and s["freelancer"]["rooms"] == 11
    assert s["inputs"]["candidate"]["json_sha256_8"] == "b35475bf"


def test_adverse_band_booked_in_the_dry_open_room_refused():
    # the pantry backing belongs to the pantry's own line; booking its band in the dining room's dry line too is refused
    claims = [(R.PLASTER, "L-721a0f1441436193978c", "PANTRY_OPEN", "GF-07|GF-W16", "BACKING"),
              (R.PLASTER, "L-721a0f1441436193978c", "PANTRY_OPEN", "GF-07|GF-W16", "ABOVE_TILE"),
              (R.PLASTER, "L-8cecb1d010d5aafbf25d", "DRY", "GF-07|GF-W16", "ABOVE_TILE")]
    try:
        R.check_claims(claims)
    except R.BackingError as e:
        assert str(e).startswith("BAND_TWICE")
    else:
        raise AssertionError("band in two lines accepted")


def test_no_coordinates_committed():
    big = re.compile(r"-?\d{5,}\.\d+")
    for p in HERE.iterdir():
        if p.suffix in (".csv", ".json", ".md"):
            assert not big.search(p.read_text(encoding="utf-8")), p.name
