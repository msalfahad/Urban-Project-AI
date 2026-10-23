"""T-223: the development villa's ledger reproduces from committed files (input extracted by DXF handle); the curved
room's engine line agrees with the hand reconstruction from the printed dimensions; the freelancer row closes neither
key; the dressing enters the internal floor (DRY, material HELD); the side passage is exterior; the sills leave the
floor line; the floor-area like-for-like residual closes to named parts."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t223"
sys.path.insert(0, str(HERE))

import alsenan_t223 as A                                               # noqa: E402


def _s():
    return json.loads((HERE / "summary.json").read_text(encoding="utf-8"))


def test_committed_files_reproduce():
    assert A.main(["--check"]) == 0


def test_no_coordinates_or_names_in_outputs():
    inp = json.loads((HERE / "ALSENAN_T223_INPUT.json").read_text(encoding="utf-8"))
    vals = []

    def walk(o, key=None):
        if isinstance(o, dict):
            for k, v in o.items():
                walk(v, k)
        elif isinstance(o, list):
            for v in o:
                walk(v, key)
        elif isinstance(o, (int, float)) and key in ("a", "b", "centre", "points", "p2", "p3"):
            vals.append(o)
    walk(inp)
    assert vals and max(abs(v) for v in vals) < 20.0                      # local frames (m) only, no drawing coordinates


def test_curved_room_hand_equals_engine_line():
    c = _s()["curved_room"]
    assert all(c["checks"].values())
    assert abs(c["engine_line_hand_m2"] - 19.0165) <= 0.0003               # mm rounding of the two arc ends
    assert c["parts"]["columns_m2"] == 0.075 and c["parts"]["lobby_m2"] == 3.78 and c["parts"]["strip_m2"] == 0.195
    assert abs(c["arc"]["segment_vs_straight_m2"] - 1.6835) <= 0.0003
    assert c["engine_line_hand_lm"] == 22.151


def test_freelancer_row_closes_neither_key():
    p = _s()["curved_room"]["pairing"]
    assert p["paired"] == [] and not p["closed"]
    a = p["readings"][0]
    assert a["verdict"] == "NOT A PAIRING" and a["d_lm"] == -0.739
    h = p["readings"][-1]
    assert not h["physical"] and abs(h["d_m2"] - 0.0433) < 0.0005 and h["d_lm"] == -0.739


def test_dressing_typed_and_in_the_floor_line():
    d = _s()["dressing"]
    assert d["area_m2"] == 2.97 and d["size_m"] == [1.65, 1.8]
    assert d["op011_width_m"] == 1.0 and d["op019_width_m"] == 0.8 and d["inserts_inside"] == 0
    t = d["typing"]
    assert (t["class"], t["floor_line"], t["wet_dry"], t["material_status"]) == \
        ("INTERIOR", "FLOOR.INTERNAL", "DRY", "HELD")


def test_side_passage_exterior_and_engine_gaps():
    sp = _s()["side_passage"]
    assert sp["area_m2"] == 5.64 and sp["size_m"] == [1.2, 4.7] and sp["mouth_lines_any_layer"] == 0
    assert sp["typing"]["class"] == "EXTERIOR" and sp["typing"]["floor_line"] == "FLOOR.OUTDOOR"
    assert sp["engine_exterior_floor_m2"] == 5.4 and sp["missing_in_engine_m2"] == 0.24
    assert sp["not_floor_in_engine_m2"] == 0.28


def test_sills_and_strips():
    s = _s()
    by = {(x["floor"], x["opening"]): x for x in s["strips"]}
    assert by[("1F", "OP-011")]["proposed_item"].startswith("FIN.FLOOR.PORCELAIN")
    for k in (("1F", "OP-007"), ("2F", "OP-002"), ("2F", "OP-001")):
        assert by[k]["proposed_item"].startswith("ARCH.THRESHOLD") and by[k]["status"] == "HELD"
    assert s["sills_to_threshold_m2"] == 0.55
    assert s["released_duplicate_strip_lines"]["duplicates"][0]["opening_id"] == "GF-OP-001"


def test_floor_key_restated_and_closed():
    k = _s()["floor_key"]
    assert k["closed"] and abs(k["residual_m2"]) <= 0.0002
    assert k["like_for_like_m2"] == 1.9443 and k["before_T218_m2"] == 2.4643
