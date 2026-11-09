"""T-622 / R-T622-1: wet-wall face method and the re-measure of statement V10 T-547/wall-tile (research rule, unwired).

Villa K622 (synthetic, not Alsenan), hand calculation (m, tile top H = 3.00):
  bathroom 2.40 x 1.80, chain perimeter 8.40; door 0.80 head 2.20 -> 1.760; window 0.60 sill 1.70 head 2.50 -> 0.480
  half-height partition 0.90 long x 0.10 thick x 1.10 high, abutting the 1.80 wall:
    room faces: 8.30 x 3.00 = 24.900 + the 0.10 strip behind the partition end, tiled above it 0.10 x 1.90 = 0.190
    partition faces (0.90 + 0.90 + 0.10) x 1.10 = 2.090 ; cap 0.90 x 0.10 HELD (finish not printed), never 0
    net = 24.900 + 0.190 + 2.090 - 1.760 - 0.480 = 24.940
  open-sided wash lobby 2.00 x 1.50 open on one 1.50 side (threshold line T): F = 7.00 - 1.50 = 5.50 -> 16.500
Drawing helpers read the same lobby at 0 / 37 / 211 deg and mirrored, in mm. Adverse: a tiled face also carrying paint
refused; an open side closed by the nearest wall refused; mm heights refused; an opening with no head refused (HELD).
"""
from __future__ import annotations

import json
import math
import os
import sys
from decimal import Decimal as D
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "research" / "agents_t622"))
sys.path.insert(0, str(ROOT / "research" / "agents_t606"))
import t622_rules as R  # noqa: E402
import t606_rules as R6  # noqa: E402


def door(w="0.80"):
    return {"id": "D1", "kind": "door", "w": w, "sill": "0", "head": "2.20"}


def win(w="0.60"):
    return {"id": "W1", "kind": "window", "w": w, "sill": "1.70", "head": "2.50"}


# ---------------------------------------------------------------- rule (normal)
def test_bathroom_with_half_height_wall_hand_calc():
    faces = [{"id": "room", "lm": "8.30"}, {"id": "behind-end", "lm": "0.10", "h_from": "1.10"},
             {"id": "part.a", "lm": "0.90", "h_wall": "1.10", "cap": "0.90"},
             {"id": "part.b", "lm": "0.90", "h_wall": "1.10"}, {"id": "part.end", "lm": "0.10", "h_wall": "1.10"}]
    res = R.room_net(faces=faces, H="3.00", openings=[door(), win()])
    assert res["doors"] == D("1.760") and res["windows"] == D("0.480")
    assert res["gross"] == D("27.180")
    assert res["net"] == D("24.940")
    assert res["held"] == [{"id": "part.a.cap", "lm": "0.90", "state": "HELD",
                            "why": "cap finish not printed (R-T622-1 step 3); never 0"}]


def test_window_above_the_tile_top_deducts_only_its_band_part():
    assert R.opening_part({"id": "W", "kind": "window", "w": "0.5", "sill": "2.80", "head": "3.40"}, "3.00") == D("0.10")
    assert R.opening_part({"id": "W", "kind": "window", "w": "0.5", "sill": "3.10", "head": "3.40"}, "3.00") == D("0")
    assert R.opening_part(door(), "2.00") == D("1.600")      # door head above a low tile top: band part only


def test_open_side_is_its_own_named_line():
    assert R.tiled_length("7.00", [{"handle": "T", "lm": "1.50", "role": "OPEN"}]) == D("5.50")
    res = R.room_net(faces=[{"id": "lobby", "lm": R.tiled_length("7.00", [{"handle": "T", "lm": "1.50"}])}],
                     H="3.00", openings=[])
    assert res["net"] == D("16.500")


def test_evidence_tolerance_and_differs():
    assert R.evidence("0.073995", "0.075") == ("DRAWING-CONFIRMED", D("-0.001005"))
    assert R.evidence("-5.358082", "-5.37355")[0] == "DIFFERS"


# ---------------------------------------------------------------- rule (adverse)
def test_tiled_face_also_carrying_paint_is_refused():
    with pytest.raises(R.RuleError, match="tile and"):
        R.room_net(faces=[{"id": "f", "lm": "2.0", "finishes": ["tile", "paint"]}], H="3.00", openings=[])
    with pytest.raises(R.RuleError, match="tile and"):
        R.room_net(faces=[{"id": "f", "lm": "2.0", "finishes": ["tile", "skirting"]}], H="3.00", openings=[])


def test_open_side_closed_by_a_wall_or_unnamed_is_refused():
    with pytest.raises(R.RuleError, match="closed across"):
        R.tiled_length("7.00", [{"handle": "N", "lm": "1.50", "role": "WALL"}])
    with pytest.raises(R.RuleError, match="named drawn line"):
        R.tiled_length("7.00", [{"lm": "1.50"}])
    with pytest.raises(R.RuleError, match="exceed"):
        R.tiled_length("1.00", [{"handle": "T", "lm": "1.50"}])


def test_units_and_missing_data_are_refused_never_zero():
    with pytest.raises(R.RuleError, match="m expected"):
        R.room_net(faces=[{"id": "f", "lm": "2.0"}], H="3000", openings=[])
    with pytest.raises(R.RuleError, match="m expected"):
        R.room_net(faces=[{"id": "f", "lm": "2400"}], H="3.00", openings=[])
    with pytest.raises(R.RuleError, match="never 0"):
        R.room_net(faces=[{"id": "f", "lm": None}], H="3.00", openings=[])
    with pytest.raises(R.RuleError, match="HELD"):
        R.opening_part({"id": "A", "kind": "arch", "w": "1.0", "head": None}, "3.00")
    with pytest.raises(R.RuleError, match="band"):
        R.room_net(faces=[{"id": "f", "lm": "1.0", "h_wall": "1.10", "h_from": "1.20"}], H="3.00", openings=[])


# ---------------------------------------------------------------- drawing helpers, rotated / mirrored, in mm
def _xf(p, deg, mirror):
    x, y = p
    if mirror:
        x = -x
    a = math.radians(deg)
    return (x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a))


@pytest.mark.parametrize("deg,mirror", [(0, False), (37, False), (211, False), (90, True)])
def test_lobby_faces_openings_and_open_side_from_geometry(deg, mirror):
    import t622_extract as X
    m = 1000.0
    raw = {  # lobby 2.00 x 1.50 (m); south face S1 / S2 with a door gap 0.80, east face E with a window 0.60 framed in
        # layer W, north face N, west side open on threshold T (layer 2)
        "S1": (((0, 0), (0.6, 0)), "1"), "S2": (((1.4, 0), (2.0, 0)), "1"),
        "E1": (((2.0, 0), (2.0, 0.45)), "1"), "WF": (((2.0, 0.45), (2.0, 1.05)), "W"),
        "E2": (((2.0, 1.05), (2.0, 1.5)), "1"), "N": (((2.0, 1.5), (0, 1.5)), "1"),
        "T": (((0, 1.5), (0, 0)), "2"),
    }
    geom, lay = {}, {}
    for h, ((a, b), ly) in raw.items():
        geom[h] = ("LINE", (_xf((a[0] * m, a[1] * m), deg, mirror), _xf((b[0] * m, b[1] * m), deg, mirror)))
        lay[h] = ly
    chain = [("S1", "WALL"), ("E1", "WALL"), ("N", "WALL"), ("T", "ZONE_EDGE")]
    res = R6.outline(geom, chain)
    assert abs(float(res["perimeter"]) - 7.0) < 1e-6
    assert abs(float(res["wall_lm"]) - 5.5) < 1e-6
    verts = X._verts(geom, chain)
    pcs, L = X._pieces(geom, lay, verts[0], verts[1])
    gaps = X._gaps(pcs, L)
    assert [round(b - a) for a, b in gaps] == [800]
    assert not X._filled(pcs, *gaps[0], "W")
    pcs, L = X._pieces(geom, lay, verts[1], verts[2])
    gaps = X._gaps(pcs, L)
    assert [round(b - a) for a, b in gaps] == [600]
    assert X._filled(pcs, *gaps[0], "W")
    F = R.tiled_length(res["perimeter"], [{"handle": "T", "lm": "1.5"}])
    net = R.room_net(faces=[{"id": "lobby", "lm": F}], H="3.00", openings=[door(), win()])
    assert net["net"] == D("16.500") - D("1.760") - D("0.480")


# ---------------------------------------------------------------- development villa (committed JSON, no drawing needed)
def test_alsenan_47_rows_rebuilt_and_split_exact():
    import t622_alsenan as B
    res = B.build()
    assert res["unknown_rows"] == 47 and res["rows_rebuilt"] == 47
    assert res["drawing_confirmed"] == 42 and res["differs"] == 5
    assert res["unknown_signed_stated"] == "-44.86380"
    assert sum(D(v) for v in res["own_split_by_cause"].values()) == D("-44.86380")
    assert sum(D(v) for v in res["stated_split_by_class"].values()) == D("-44.86380")
    assert res["own_split_by_cause"]["ENGINE_WRONG"] == "-0.053909"
    rooms = {r["room"]: r for r in res["rooms"]}
    assert rooms["GF-14"]["face_lm"] == "8.243203" and rooms["GF-14"]["line_minus_own"] == "0.086709"
    assert rooms["GF-07"]["face_lm"] == "10.5" and rooms["GF-07"]["own_net"] == "32.375000"
    differs = sorted(r["row"] for r in res["rows"] if r["evidence"] == "DIFFERS")
    assert differs == [7, 8, 9, 11, 46]
    assert len(res["held_rows"]) == 6 and all(h["waits_on"] for h in res["held_rows"])


def test_alsenan_output_is_reproduced_from_the_builder():
    import t622_alsenan as B
    committed = json.loads(B.OUT.read_text(encoding="utf-8"))
    assert committed == json.loads(json.dumps(B.build(), ensure_ascii=False))


def test_drawn_json_carries_no_coordinates():
    txt = (ROOT / "research" / "agents_t622" / "T622_DRAWN.json").read_text(encoding="utf-8")
    d = json.loads(txt)
    for r in d["rooms"].values():
        for e in r["edges"]:
            assert set(e) == {"handle", "role", "lm"}
    assert "_p" not in txt and "_q" not in txt


DXF = Path(os.environ.get("T622_DXF", ROOT.parents[1] / ".work" / "private" / "P7757_DXF_COMPRESSED" / "P7757.dxf"))


@pytest.mark.skipif(not DXF.exists(), reason="private drawing absent")
def test_private_drawing_reread_is_identical():
    pytest.importorskip("ezdxf")
    import t622_extract as X
    d = X.read(str(DXF))
    assert json.dumps(d, indent=1, sort_keys=True) + "\n" == X.OUT.read_text(encoding="utf-8")
