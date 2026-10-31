"""T-388: wall-face consistency across block / plaster / paint / backing / tile / reveal / threshold (R-T388-1).

Hand fixture (NOT the development villa): a bedroom B (dry, 3.00 m owner height) and a bath W (wet, tile to 2.80 =
backing top) share wall X (0.15 m); the door D1 0.80 x 2.10 sits in X; the window N1 1.20 x 1.20 (sill 0.90) sits in
the bedroom's outer wall Y (0.20 m). Hand values:
  D1 hole = 0.80 x 2.10 = 1.680 m2 (block, plaster, paint, tile and backing: 2.10 < 2.80, all inside the band);
  N1 hole = 1.20 x 1.20 = 1.440 m2 (block, plaster, paint);
  D1 reveal: jambs 2 x 0.15 x 2.10 = 0.630 m2 + head 0.15 x 0.80 = 0.120 m2 (its own FIN.PLASTER line);
  bath face X 2.00 m: tile 2.00 x 2.80 - 1.680 = 3.920 m2; a 0.05 m tile-above-backing lifts 0.05 x 2.00 = 0.100 m2.
"""

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t388"


def _load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


FC = _load("face_check")


def fixture(mirror=False):
    # mirror: the same house drawn mirrored (left / right swapped): only labels and order change, not topology
    B, W, X, Y = ("B", "W", "X", "Y") if not mirror else ("Bm", "Wm", "Xm", "Ym")
    faces = [
        {"face_id": f"{B}|{X}", "room": B, "wall": X, "room_class": "DRY", "length_m": 2.0,
         "tops": {"block": 2.85, "plaster": 3.0, "paint": 3.0}, "states": {"plaster": "ASSUMED"}},
        {"face_id": f"{B}|{Y}", "room": B, "wall": Y, "room_class": "DRY", "length_m": 3.0,
         "tops": {"block": 2.85, "plaster": 3.0, "paint": 3.0}, "states": {"plaster": "ASSUMED"}},
        {"face_id": f"{W}|{X}", "room": W, "wall": X, "room_class": "WET", "length_m": 2.0,
         "tops": {"block": 2.85, "tile": 2.8, "backing": 2.8}, "states": {"tile": "ASSUMED", "backing": "ASSUMED"}},
    ]
    ded = []
    for fam in ("plaster", "paint"):
        ded.append({"family": fam, "face_id": f"{B}|{X}", "opening": "D1", "m2": 0.80 * 2.10, "w": 0.8, "kind": "door"})
        ded.append({"family": fam, "face_id": f"{B}|{Y}", "opening": "N1", "m2": 1.20 * 1.20, "w": 1.2,
                    "kind": "window"})
    for fam in ("tile", "backing"):
        ded.append({"family": fam, "face_id": f"{W}|{X}", "opening": "D1", "m2": 0.80 * 2.10, "w": 0.8, "kind": "door"})
    block = [{"wall": X, "opening": "D1", "m2": 1.68}, {"wall": Y, "opening": "N1", "m2": 1.44}]
    reveals = [{"opening": "D1", "room": B, "carrier": "L-door-jambs", "jamb_return_m": 0.0, "h_m": 2.1}]
    thresholds = [{"opening": "D1", "strip_m2": 0.12, "floor_overlap_m2": 0.0}]
    paint = [{"room": W, "state": "NOT_APPLICABLE_WITH_EVIDENCE"}]
    closures = [{"room": W, "family": "tile", "family_length_m": 2.0, "geometric_length_m": 2.0, "top_m": 2.8}]
    return faces, ded, block, reveals, thresholds, paint, closures, (B, W, X, Y)


def run(fx):
    return FC.check(*fx[:7])


def kinds(f):
    return sorted(x["kind"] for x in f)


def test_normal_fixture_is_consistent():
    assert run(fixture()) == []
    faces = fixture()[0]
    # hand: tile net on the bath face = 2.00 x 2.80 - 1.680
    assert round(faces[2]["length_m"] * faces[2]["tops"]["tile"] - 0.80 * 2.10, 4) == 3.92


def test_mirror_gives_the_same_result():
    assert run(fixture(mirror=True)) == []


def test_opening_deducted_twice_on_one_face_is_detected():
    fx = list(fixture())
    B, W, X, Y = fx[7]
    fx[1] = fx[1] + [{"family": "plaster", "face_id": f"{B}|{X}", "opening": "D1", "m2": 1.68, "w": 0.8,
                      "kind": "door"}]
    f = run(fx)
    assert kinds(f) == ["DUPLICATE_DEDUCTION"]
    assert f[0]["m2"] == 1.68 and f[0]["family"] == "plaster"


def test_opening_on_a_third_face_is_detected():
    fx = list(fixture())
    B, W, X, Y = fx[7]
    fx[0] = fx[0] + [{"face_id": f"{B}|Z", "room": B, "wall": "Z", "room_class": "DRY", "length_m": 1.0,
                      "tops": {"plaster": 3.0}, "states": {}}]
    fx[1] = fx[1] + [{"family": "plaster", "face_id": f"{B}|Z", "opening": "N1", "m2": 1.44}]
    # N1 on Y and on Z (two faces of one room, different walls): host mismatch with the block wall Y
    assert kinds(run(fx)) == ["HOST_MISMATCH"]
    fx[1] = fx[1] + [{"family": "plaster", "face_id": f"{W}|X", "opening": "N1", "m2": 1.44}]
    assert "OPENING_ON_TOO_MANY_FACES" in kinds(run(fx))


def test_tile_above_its_backing_is_flagged_with_its_m2():
    fx = list(fixture())
    fx[0] = [dict(f) for f in fx[0]]
    fx[0][2]["tops"] = {"block": 2.85, "tile": 2.85, "backing": 2.8}
    f = run(fx)
    assert kinds(f) == ["TILE_ABOVE_COAT"]
    assert f[0]["m2"] == pytest.approx(0.05 * 2.0, abs=1e-4)


def test_paint_line_on_a_fully_tiled_room():
    fx = list(fixture())
    B, W, X, Y = fx[7]
    fx[5] = [{"room": W, "state": "BLOCKED_RFI"}]
    assert kinds(run(fx)) == ["PAINT_LINE_ON_FULL_TILE"]


def test_held_face_never_summed_as_zero():
    fx = list(fixture())
    fx[0] = [dict(f) for f in fx[0]]
    fx[0][0]["values"] = {"plaster": 0.0}
    fx[0][0]["states"] = {"plaster": "HELD (head not printed)"}
    assert kinds(run(fx)) == ["HELD_AS_ZERO"]
    fx[0][0]["values"] = {"plaster": None}
    fx[0][1]["values"] = {"plaster": 7.56}
    total, held = FC.family_total(fx[0], "plaster")
    assert total == 7.56 and held == [fx[0][0]["face_id"]]


def test_size_mismatch_between_block_and_plaster():
    fx = list(fixture())
    fx[2] = [{"wall": fx[7][2], "opening": "D1", "m2": 0.90 * 2.10}, {"wall": fx[7][3], "opening": "N1", "m2": 1.44}]
    f = run(fx)
    assert kinds(f) == ["SIZE_MISMATCH"]
    assert f[0]["m2"] == pytest.approx(0.10 * 2.10, abs=1e-4)


def test_block_part_explained_is_named_not_a_mismatch():
    fx = list(fixture())
    X, Y = fx[7][2], fx[7][3]
    fx[2] = [{"wall": X, "opening": "D1", "m2": 1.68},
             {"wall": Y, "opening": "N1", "m2": 1.08, "full_hole_m2": 1.44, "reason": "0.30 m of N1 in a column"}]
    f = run(fx)
    assert kinds(f) == ["BLOCK_PART_EXPLAINED"] and f[0]["m2"] == pytest.approx(0.36, abs=1e-4)
    assert set(FC.EXPLAINED) >= {"BLOCK_PART_EXPLAINED"}


def test_band_family_above_the_hole_is_refused():
    fx = list(fixture())
    fx[1] = [dict(d) for d in fx[1]]
    for d in fx[1]:
        if d["family"] == "tile":
            d["m2"] = 1.90
    assert kinds(run(fx)) == ["BAND_ABOVE_HOLE"]


def test_reveal_walked_into_the_face_and_threshold_in_floor():
    fx = list(fixture())
    fx[3] = [{"opening": "D1", "room": fx[7][0], "carrier": "L-door-jambs", "jamb_return_m": 0.30, "h_m": 2.1}]
    fx[4] = [{"opening": "D1", "strip_m2": 0.12, "floor_overlap_m2": 0.12}]
    f = run(fx)
    assert kinds(f) == ["REVEAL_IN_FACE", "THRESHOLD_IN_FLOOR"]
    assert [x["m2"] for x in sorted(f, key=lambda x: x["kind"])] == [pytest.approx(0.63), pytest.approx(0.12)]


def test_split_face_must_close_and_off_line_doorway_attribution():
    fx = list(fixture())
    B, W, X, Y = fx[7]
    fx[0] = fx[0] + [{"face_id": "C|X", "room": "C", "wall": X, "room_class": "DRY", "length_m": 1.0,
                      "tops": {"plaster": 3.0}, "states": {}}]
    # the door's bedroom side split between B (0.50) and corridor C (0.20): 0.70 != 0.80 -> refused
    fx[1] = [d for d in fx[1] if not (d["family"] == "plaster" and d["opening"] == "D1")] + [
        {"family": "plaster", "face_id": f"{B}|{X}", "opening": "D1", "m2": 1.05, "split_w": 0.5, "full_w": 0.8,
         "full_m2": 1.68},
        {"family": "plaster", "face_id": "C|X", "opening": "D1", "m2": 0.42, "split_w": 0.2, "full_w": 0.8,
         "full_m2": 1.68}]
    assert "SPLIT_FACE_DOES_NOT_CLOSE" in kinds(run(fx))
    # off-line doorway: the bath walks the doorway as its own piece, the straight face X carries no drawn door
    fx = list(fixture())
    fx[0] = [dict(f) for f in fx[0]] + [{"face_id": f"{W}|OFF:DOORWAY", "room": W, "wall": "OFF:DOORWAY",
                                         "room_class": "WET", "length_m": 0.8, "tops": {"tile": 2.8, "backing": 2.8},
                                         "states": {"tile": "ASSUMED"}}]
    fx[0][2]["door_m"], fx[0][2]["gap_m"] = 0.0, 0.0
    f = [x for x in run(fx) if x["kind"] == "OPENING_OFF_ITS_FACE"]
    assert len(f) == 2 and all(x["room_total_effect_m2"] == 0.0 for x in f)


def test_units_and_face_closure():
    fx = list(fixture())
    fx[0] = [dict(f) for f in fx[0]]
    fx[0][0]["tops"] = {"plaster": 3000.0}
    with pytest.raises(ValueError):
        run(fx)
    fx = list(fixture())
    fx[6] = [{"room": fx[7][1], "family": "tile", "family_length_m": 1.88, "geometric_length_m": 2.0, "top_m": 2.8}]
    f = run(fx)
    assert kinds(f) == ["FACE_LENGTH_RESIDUAL"] and f[0]["m2"] == pytest.approx(-0.336, abs=1e-4)
    fx[6] = [{"room": fx[7][1], "family": "tile", "family_length_m": 1.88, "geometric_length_m": 2.0, "top_m": None}]
    assert run(fx)[0]["m2"] is None  # a HELD top gives no m2, never 0


def test_missing_data_unknown_face_is_named():
    fx = list(fixture())
    fx[1] = fx[1] + [{"family": "tile", "face_id": "NOWHERE", "opening": "D1", "m2": 1.68}]
    assert kinds(run(fx)) == ["DEDUCTION_ON_UNKNOWN_FACE"]


def test_alsenan_face_table_reproduces():
    al = _load("alsenan_t388")
    d, fnd = al.main([])
    k = {}
    for x in fnd:
        k[x["kind"]] = k.get(x["kind"], 0) + 1
    assert k == {"OPENING_OFF_ITS_FACE": 10, "BLOCK_PART_EXPLAINED": 1, "FACE_LENGTH_RESIDUAL": 6,
                 "PAINT_LINE_ON_FULL_TILE": 1}
    assert not [x for x in fnd if x["kind"] in ("DUPLICATE_DEDUCTION", "OPENING_ON_TOO_MANY_FACES", "SIZE_MISMATCH",
                                                "HOST_MISMATCH", "REVEAL_IN_FACE", "THRESHOLD_IN_FLOOR",
                                                "TILE_ABOVE_COAT", "HELD_AS_ZERO")]
