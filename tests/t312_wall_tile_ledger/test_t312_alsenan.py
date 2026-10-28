"""T-312 Alsenan pins: the committed ledger rebuilds byte for byte from the merged inputs, every wet-room face is
once TILED / NOT_TILED / open edge, every FIN.WALL.TILE line of the V3.0.19 extract once, the pantry by its host walls,
no coordinate in the committed files."""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t312"
sys.path.insert(0, str(HERE))

import t312_alsenan as A        # noqa: E402
import t312_wall_tile_rules as R  # noqa: E402


def _rows(name):
    with open(HERE / name, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def test_rebuild_byte_identical():
    for p, s in A.render().items():
        assert p.read_text(encoding="utf-8") == s, p.name


def test_every_face_once_and_rooms_close():
    faces = _rows("FACE_LEDGER_T312.csv")
    ids = [f["face_id"] for f in faces]
    assert len(ids) == len(set(ids))
    rooms = _rows("ROOM_CLOSURE_T312.csv")
    assert len(rooms) == 18
    assert all(abs(float(r["residual_m"])) < 1e-9 for r in rooms)
    assert {f["scope"] for f in faces} <= {R.TILED, R.NOT_TILED, R.OPEN_EDGE}


def test_every_candidate_tile_line_once_and_pantry_no_line():
    cand = json.loads((HERE / "CANDIDATE_V3019_WALL_TILE_LINES.json").read_text(encoding="utf-8"))
    tile = [ln["line_id"] for ln in cand["lines"] if ln["item_code"] == R.TILE]
    lines = _rows("LINE_SUMMARY_T312.csv")
    assert [l["line_id"] for l in lines if l["line_id"] != R.NO_LINE] == tile
    assert len(tile) == 17
    faces = _rows("FACE_LEDGER_T312.csv")
    nl = [f for f in faces if f["line_id"] == R.NO_LINE]
    assert {f["room"] for f in nl} == {"GF-07"} and len(nl) == 6
    for f in faces:
        if f["scope"] == R.TILED:
            assert f["line_id"], f["face_id"]
        else:
            assert f["line_id"] == "", f["face_id"]


def test_pantry_host_walls_and_open_edge():
    faces = {f["face_id"]: f for f in _rows("FACE_LEDGER_T312.csv") if f["room"] == "GF-07"}
    assert faces["GF-07|OPEN"]["scope"] == R.OPEN_EDGE and faces["GF-07|OPEN"]["length_m"] == "4.4900"
    for k in A.PANTRY_WALL_FACES:
        assert faces[k]["scope"] == R.TILED and float(faces[k]["host_m"]) >= R.HOST_MIN_M
    hosts = json.loads((HERE / "PANTRY_HOSTS_T312.json").read_text(encoding="utf-8"))
    assert hosts["faces"]["GF-07|GF-W16"]["host_m"] == pytest.approx(3.0662)
    assert hosts["faces"]["GF-07|GF-W01"]["host_m"] == pytest.approx(1.4)
    assert hosts["faces"]["GF-07|GF-W05"]["host_m"] == pytest.approx(0.5)
    # every run 0.50 deep from its wall; the north leg 0.45 from the column face it backs onto (0.05 notch)
    assert {k: v["depth_m"] for k, v in hosts["runs"].items()} == {
        "west_counter.west_leg": 0.5, "west_counter.north_leg": 0.45, "east_counter.south_leg": 0.5,
        "east_counter.east_leg": 0.5}


def test_named_values():
    s = json.loads((HERE / "summary.json").read_text(encoding="utf-8"))
    om = s["owner_method"]
    assert om["in_line_m2"] == pytest.approx(307.9616, abs=1e-4)
    assert om["no_line_m2"] == pytest.approx(32.3422, abs=1e-4)
    assert sorted(om["held_rooms"]) == ["GF-02", "GF-03", "GF-05", "GF-06", "GF-10", "GF-11"]
    fr = s["freelancer"]
    assert fr["compared_rooms"] == 11 and fr["fl_m2"] == pytest.approx(295.44)
    assert abs(fr["residual_m2"]) < 1e-3
    # W18 (sill 0.84, head 3.00) lies inside the 3.35 tile band and is deducted once in 1F-12
    ops = [o for o in _rows("OPENINGS_T312.csv") if o["opening_id"] == "W18"]
    assert len(ops) == 1 and ops[0]["band_m2"] == "1.0800"


def test_held_rooms_never_zero():
    for r in _rows("ROOM_CLOSURE_T312.csv"):
        if r["status"] == "HELD":
            assert r["owner_net_m2"] == "" and r["held_item"]
    for f in _rows("FACE_LEDGER_T312.csv"):
        if f["owner_status"] == "HELD":
            assert f["owner_net_m2"] == ""


def test_no_coordinates_committed():
    big = re.compile(r"-?\d{5,}\.\d+")
    for p in HERE.iterdir():
        if p.suffix in (".csv", ".json", ".md"):
            assert not big.search(p.read_text(encoding="utf-8")), p.name
