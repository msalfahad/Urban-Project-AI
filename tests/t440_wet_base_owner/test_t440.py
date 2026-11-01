"""T-440 / R-T440-1: one owner per wall base where an open-plan skirting line runs into a room tiled full height.

Hand villa K440 (not Alsenan): an open living room (engine room) holds, in part, a kitchenette box 2.40 x 3.00 m tiled
full height (owner rule, class source cited). Its faces inside the living room's skirting line, by hand:
  north wall 2.40 = wall 0.60 + door 0.90 (no base) + wall 0.90
  NW column 0.40 + its return 0.05
  west wall 3.00 = wall 1.00 + window 1.20 (sill window; base under it tiled) + wall 0.80
  east side open (no wall, no base); the zone line to the living room (no base)
  base-bearing faces 0.60 + 0.90 + 0.40 + 0.05 + 1.00 + 0.80 = 3.75 lm
plus two dry living-room faces 4.00 + 2.50 (kept).
"""
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "research" / "agents_t440"))
import wet_base_owner_v1 as W  # noqa: E402

LINE = "L-K440-LIVING"
TILE = "L-K440-KIT-TILE"
ROOMS = {
    "K-KIT": {"finish_class": W.TILED, "tile_line": TILE, "class_source": "owner rule: kitchenette tiled full height"},
    "K-LIV": {"finish_class": W.DRY, "tile_line": None, "class_source": "dry living"},
}


def faces(carry_kit=True):
    k = (lambda ln: ln) if carry_kit else (lambda ln: 0.0)
    fs = [
        ("n1", "K-KIT", "WALL", 0.60), ("door", "K-KIT", "DOOR", 0.90), ("n2", "K-KIT", "WALL", 0.90),
        ("col", "K-KIT", "COLUMN", 0.40), ("colret", "K-KIT", "COLUMN", 0.05),
        ("w1", "K-KIT", "WALL", 1.00), ("win", "K-KIT", "WINDOW", 1.20), ("w2", "K-KIT", "WALL", 0.80),
        ("zone", "K-KIT", "ZONE", 2.40), ("open", "K-KIT", "OPEN", 3.00),
        ("liv1", "K-LIV", "WALL", 4.00), ("liv2", "K-LIV", "WALL", 2.50),
    ]
    out = []
    for fid, room, role, ln in fs:
        if role in W.BASE_ROLES:
            car = k(ln) if room == "K-KIT" else ln
        else:
            car = 0.0
        out.append({"face_id": fid, "line_id": LINE, "room": room, "role": role, "length_m": ln, "carried_lm": car})
    return out


def test_normal_line_still_carries_the_tiled_base():
    a = W.audit(faces(True), ROOMS)
    assert a["over_count_lm"] == pytest.approx(3.75, abs=1e-9)
    assert a["tiled_base_lm"] == pytest.approx(3.75, abs=1e-9)
    assert a["kept_lm"] == pytest.approx(6.50, abs=1e-9)
    st = {r["face_id"]: r["status"] for r in a["rows"]}
    assert st["n1"] == "OVER_COUNT" and st["door"] == "NO_BASE" and st["win"] == "WINDOW_BASE_TILED"
    assert st["liv1"] == "KEPT" and st["zone"] == "NO_BASE" and st["open"] == "NO_BASE"
    assert {r["owner"] for r in a["rows"] if r["status"] == "OVER_COUNT"} == {TILE}


def test_normal_part_already_off_gives_zero_with_proof():
    a = W.audit(faces(False), ROOMS)
    assert a["over_count_lm"] == 0.0 and a["unknown_faces"] == []
    assert {r["status"] for r in a["rows"] if r["room"] == "K-KIT" and r["role"] in W.BASE_ROLES} == {"TILE_OWNS"}
    assert a["tiled_base_lm"] == pytest.approx(3.75, abs=1e-9)


def test_adverse_tiled_wet_face_given_skirting_as_well():
    fs = faces(False)
    fs[0]["carried_lm"] = 0.60          # the tiled face carried by the skirting line too
    a = W.audit(fs, ROOMS)
    assert a["over_count_lm"] == pytest.approx(0.60, abs=1e-9)
    assert [r["face_id"] for r in a["rows"] if r["status"] == "OVER_COUNT"] == ["n1"]


def test_order_mirror_and_rotation_do_not_change_the_audit():
    # the audit takes no coordinate: a mirrored or rotated plan gives the same faces in another order
    a = W.audit(faces(True), ROOMS)
    b = W.audit(list(reversed(faces(True))), ROOMS)
    assert a["over_count_lm"] == b["over_count_lm"] and a["kept_lm"] == b["kept_lm"]


def test_missing_carried_length_is_unknown_never_zero():
    fs = faces(True)
    fs[2]["carried_lm"] = None
    a = W.audit(fs, ROOMS)
    assert a["over_count_lm"] is None and a["unknown_faces"] == ["n2"]
    assert a["over_count_known_lm"] == pytest.approx(2.85, abs=1e-9)


def test_tiled_room_without_a_tile_line_is_unresolved():
    rooms = dict(ROOMS, **{"K-KIT": dict(ROOMS["K-KIT"], tile_line=None)})
    a = W.audit(faces(True), rooms)
    assert a["over_count_lm"] is None
    assert {r["status"] for r in a["rows"] if r["room"] == "K-KIT" and r["role"] in W.BASE_ROLES} == {"UNRESOLVED"}


def test_unknown_room_is_unresolved_not_kept():
    fs = faces(True)
    fs[10]["room"] = "K-NOWHERE"
    a = W.audit(fs, ROOMS)
    row = next(r for r in a["rows"] if r["face_id"] == "liv1")
    assert row["status"] == "UNRESOLVED" and row["over_lm"] is None and a["over_count_lm"] is None


@pytest.mark.parametrize("mut, msg", [
    (lambda f: f[0].update(unit="mm", length_m=600), "unit"),
    (lambda f: f[0].update(carried_lm=0.9), "carries"),
    (lambda f: f.append(dict(f[0])), "twice"),
    (lambda f: f[0].update(role="SKIRT"), "role"),
    (lambda f: f[0].update(length_m=-0.6), "negative"),
    (lambda f: f[0].update(length_m="0.6"), "number"),
])
def test_bad_inputs_refused(mut, msg):
    fs = faces(True)
    mut(fs)
    with pytest.raises(W.AuditError, match=msg):
        W.audit(fs, ROOMS)


def test_tiled_class_needs_its_source():
    rooms = dict(ROOMS, **{"K-KIT": dict(ROOMS["K-KIT"], class_source="")})
    with pytest.raises(W.AuditError, match="source"):
        W.audit(faces(True), rooms)


def test_closure_of_the_tiled_base():
    c = W.closure(4.95, {"other engine room": 1.20, "this line": 3.75})
    assert c["closes"] and c["residual_lm"] == 0.0
    c2 = W.closure(4.95, {"other engine room": None, "this line": 3.75})
    assert c2["residual_lm"] is None and not c2["closes"]
    assert not W.closure(5.00, {"this line": 3.75})["closes"]


def test_addition_to_the_same_line_must_not_land_on_a_tiled_face():
    ok = [{"face_id": "dining-south", "room": "K-LIV", "role": "WALL"}]
    assert W.additions_clear(ok, ROOMS) == []
    bad = [{"face_id": "kit-west", "room": "K-KIT", "role": "WALL"}, {"face_id": "x", "room": None, "role": "WALL"}]
    assert [b["face_id"] for b in W.additions_clear(bad, ROOMS)] == ["kit-west", "x"]


# ------------------------------------------------------------------------------- committed Alsenan result (no data)
def test_committed_alsenan_summary_is_consistent():
    s = json.loads((ROOT / "research" / "agents_t440" / "summary.json").read_text())
    assert s["rule"] == W.RULE_ID and s["pantry_base_in_host_lm"] == pytest.approx(3.5, abs=1e-6)
    assert s["pantry_part_off_in_candidate"] is True and s["over_count_lm"] == 0.0
    assert s["candidate_host_net_lm"] == pytest.approx(s["v29_net_minus_pantry_base_lm"], abs=1e-6)
    assert s["closure_gf07_base"]["closes"] is True
    assert s["t431_addition"]["edges_inside_pantry_box"] == 0 and s["t431_addition"]["flags"] == []
    assert [c["engine_room"] for c in s["census_partial_tiled_engine_rooms"]] == ["GF-RC99C2A"]


def test_committed_alsenan_rebuild_matches():
    sys.path.insert(0, str(ROOT / "research" / "agents_t440"))
    import t440_alsenan as T
    x = json.loads(T.EXTRACT.read_text())
    table, summ = T.build(x)
    assert T.FACES.read_text() == table and T.SUMMARY.read_text() == summ
