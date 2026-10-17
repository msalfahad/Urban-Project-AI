"""Phase 2B-1 WP-2: the space connectivity model (UP-SPACE-001 / UP-SPACE-002; engine.source.space_model) - every
space a node with independently supported attributes, every door and doorless passage an edge; a label alone never
types an unlabelled corridor, and a project decision binds the one space that contains its point."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import kb_fixtures as KF                                      # noqa: E402
from engine.source import arch_rooms as AR                    # noqa: E402
from engine.source import space_model as SMOD                 # noqa: E402

S_, D_ = KF.space, KF.door


def _by_id(model):
    return {s["face_id"]: s for s in model["spaces"]}


def _two_wings(possibly_external=True):
    """wing 1: BEDROOM - CORRIDOR (labelled, an indoor corridor); wing 2: KITCHEN - STORE; between them X, an
    unlabelled space with a doorless opening to the facade (P-OUT) and a door to each wing."""
    rooms = [S_("BED", codes=["BEDROOM"], kind=AR.DRY), S_("COR", codes=["CORRIDOR"], kind=AR.CIRCULATION),
             S_("KIT", codes=["KITCHEN"], kind=AR.SERVICE), S_("STO", codes=["STORE"], kind=AR.SERVICE),
             S_("X", cls="UNLABELLED", passages=["P-OUT"])]
    doors = [D_("D1", "BED", "COR"), D_("D2", "COR", "X"), D_("D3", "X", "KIT"), D_("D4", "KIT", "STO")]
    ext = {"X": "GF-X: doorless opening(s) P-OUT 1.40 m to the facade"} if possibly_external else {}
    return rooms, doors, ext


def test_indoor_and_outdoor_corridors_are_told_apart():
    """the labelled corridor is INTERIOR by its word; the unlabelled space with a facade opening is POSSIBLY_EXTERIOR
    and, because it joins two otherwise separate interior wings, it is reported as a connecting space - evidence for
    a project decision, never applied automatically."""
    rooms, doors, ext = _two_wings()
    m = SMOD.build(rooms, doors, possibly_external=ext)
    sp = _by_id(m)
    assert sp["COR"]["interior_status"] == SMOD.INTERIOR and sp["COR"]["status_basis"] == "LABEL"
    assert sp["X"]["interior_status"] == SMOD.POSSIBLY_EXTERIOR and sp["X"]["status_basis"] == "FACADE_OPENING"
    assert sp["BED"]["building_part"] == sp["COR"]["building_part"] != sp["KIT"]["building_part"]
    assert sp["X"]["building_part"] is None and sp["X"]["connects_parts"] == sorted(
        {sp["COR"]["building_part"], sp["KIT"]["building_part"]})
    (c,) = m["candidates"]
    assert c["space_id"] == "GF-X" and "never applied automatically" in c["use"]
    assert m["summary"]["by_status"] == {SMOD.INTERIOR: 4, SMOD.POSSIBLY_EXTERIOR: 1}


def test_an_unlabelled_space_is_never_assumed_interior():
    """no room word: interior only by enclosure (every connection leads to an interior space and no facade door);
    a facade door or no connection at all leaves it UNKNOWN - never interior by default."""
    rooms = [S_("LIV", codes=["LIVING"], kind=AR.DRY), S_("BED", codes=["BEDROOM"], kind=AR.DRY),
             S_("HALL", cls="UNLABELLED"), S_("PORCH", cls="UNLABELLED"), S_("ISLAND", cls="UNLABELLED")]
    doors = [D_("D1", "LIV", "HALL"), D_("D2", "HALL", "BED"), D_("D3", "LIV", "PORCH"), D_("D4", "PORCH", "FACADE")]
    sp = _by_id(SMOD.build(rooms, doors))
    assert sp["HALL"]["interior_status"] == SMOD.INTERIOR and sp["HALL"]["status_basis"] == "ENCLOSURE"
    assert sp["HALL"]["confidence"] == "MEDIUM"
    assert sp["PORCH"]["interior_status"] == SMOD.UNKNOWN and sp["PORCH"]["facade_doors"] == 1
    assert sp["ISLAND"]["interior_status"] == SMOD.UNKNOWN and sp["ISLAND"]["evidence"] == ["no room word"]
    # the real door-guard floor: the unlabelled lobby with a 1.40 m doorless opening to the outside
    run = KF.door_floor()
    lobby = [s for s in run["space_model"]["spaces"] if s["function"] == "UNLABELLED"]
    assert [s["interior_status"] for s in lobby] == [SMOD.POSSIBLY_EXTERIOR]


def test_a_project_decision_binds_one_space_only():
    """UP-SPACE-002: a decision names its floor and a point; it binds the one space containing the point and nothing
    else. A point in no space, another floor, or a malformed decision binds nothing and is reported unbound."""
    dec = KF.decisions(("PD-1", KF.LOBBY_POINT_M, "EXTERIOR"), ("PD-2", (50.0, 50.0), "EXTERIOR"),
                       ("PD-3", KF.LOBBY_POINT_M, "INTERIOR"))
    dec["decisions"][2]["floor"] = "1F"
    dec["decisions"].append({"id": "PD-4", "floor": "GF", "point_m": list(KF.LOBBY_POINT_M), "set": {}})
    run = KF.door_floor(decisions={"schema": dec["schema"], "decisions": dec["decisions"]})
    assert [d["id"] for d in run["decided"].values()] == ["PD-1"]
    (fid,) = run["decided"]
    assert sorted(d["id"] for d in SMOD.unbound(dec, {"PD-1"})) == ["PD-2", "PD-3", "PD-4"]
    changed = [s for s in run["space_model"]["spaces"] if s["status_basis"] == "PROJECT_DECISION"]
    assert [s["face_id"] for s in changed] == [fid] and changed[0]["interior_status"] == SMOD.EXTERIOR
    # every other space keeps the status the drawing gives it
    base = {s["face_id"]: s["interior_status"] for s in KF.door_floor()["space_model"]["spaces"]}
    after = {s["face_id"]: s["interior_status"] for s in run["space_model"]["spaces"]}
    assert {k for k in base if base[k] != after[k]} == {fid}
    # apply_decisions on a built model changes only the bound space
    rooms, doors, ext = _two_wings()
    m = SMOD.build(rooms, doors, possibly_external=ext)
    m = SMOD.apply_decisions(m, {"X": {"id": "PD-9", "set": {"interior_status": SMOD.EXTERIOR}, "statement": "s"}})
    sp = _by_id(m)
    assert sp["X"]["interior_status"] == SMOD.EXTERIOR and sp["COR"]["interior_status"] == SMOD.INTERIOR
