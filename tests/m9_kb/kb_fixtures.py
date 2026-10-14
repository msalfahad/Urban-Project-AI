"""Phase 2B-1 synthetic plans and runners (synthetic geometry only; truth written by hand from the coordinates).

    door_floor(words=..., *, decisions=None, facts=None)  the Phase 2B-0 door-guard floor (tests/m9_p2b0) run through
                                                          the ARCH_TAKEOFF_V2.3 per-floor pieces: the owner finish scope,
                                                          the door model with the V2.3 heights and project decisions,
                                                          the door scenarios, the space model, the elevator schedule
    villa_run(tmp, method, *, facts=None)                 the synthetic two-storey villa (tools/arch_synth) through the
                                                          CLI's arch_compute
    space(...) / door(...)                                hand-made space-model inputs for unit tests

The door-guard floor (mm, wall 200): HALL (ENTRANCE HALL word) with the main entrance D1 1.00 m; LOBBY unlabelled with a
1.40 m doorless opening P1 to the outside; LIVING with D3 0.90 m to the outside; BEDROOM; KITCHEN with D2 0.90 m into
the LOBBY; a 1.6 x 1.6 m stacked shaft with a 0.80 m access opening P2 from the kitchen; STORE | CORRIDOR D5 0.90 m."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests" / "m9_p2b0"))

import p2b0_fixtures as FX                                    # noqa: E402
from engine.source import arch_measure as AM                  # noqa: E402
from engine.source import arch_rooms as AR                    # noqa: E402
from engine.source import door_model as DM                    # noqa: E402
from engine.source import door_standards as DSTD              # noqa: E402
from engine.source import robust_geometry as RG               # noqa: E402
from engine.source import space_model as SMOD                 # noqa: E402
from tools import arch_synth as AS                            # noqa: E402

U = 1e-3
LOBBY_POINT_M = (5.1, 1.6)                                    # inside the unlabelled lobby (4.2 .. 6.0 x 0.2 .. 3.0)
SHAFT_BOX = (8200, 3200, 9800, 4800)


def decisions(*items):
    return {"schema": SMOD.DECISIONS_SCHEMA, "decisions": [
        {"id": i, "floor": "GF", "point_m": list(p), "set": {"interior_status": st}, "rule_id": "UP-SPACE-002",
         "statement": f"synthetic project decision: the space is {st.lower()}"} for i, p, st in items]}


def door_floor(words=FX.DOOR_WORDS, *, decisions=None, facts=None):
    ents = AS._s4_ents(FX.DOOR_ROOMS, FX.DOOR_OUTER, FX.DOOR_OPENINGS, texts=words, swings=FX.DOOR_SWINGS,
                       extra_segments=FX.DOOR_FRAME + tuple((a, b, layer, path) for (a, b), layer, path
                                                            in FX.SHAFT_HEADS))
    roles = dict(FX.DOOR_ROLES, **{"A-THIN": "OTHER"})
    S = AR.spaces(ents, roles, U, region_id="R", tol="UNIT_RELATIVE", geom=RG.Geometry(U))
    FX.mark_stacked_shaft(S, SHAFT_BOX)
    M = AM.measure(S, floor="GF", project_id="P", revision_set_sha256="0" * 64, documents=[], facts=facts,
                   owner_scope=True, door_height=lambda o_: DSTD.door_height(DSTD.INTERNAL, facts))
    walls = [k for k, v in roles.items() if v == "WALL"]
    dec = SMOD.decided_faces(S, "GF", decisions)
    fm = DM.floor_model(S, M["rooms"], ents, U, "GF", wall_layers=walls, facts=DSTD.door_model_facts(facts),
                        guards=True, **({"decided_exterior": dec} if dec else {}))
    texts = {t["id"]: t for t in ents["texts"]}
    ft = {f["face_id"]: [texts[i] for i in f.get("label_text_ids") or () if i in texts] for f in S["faces"]}
    model = DM.building_model([("GF", fm)], {"GF": ents["texts"]}, {"GF": ft}, U, entrance_floor="GF", facts=facts,
                              guards=True)
    shaft = next(f for f in S["faces"] if f.get("label_source") == "STACKED_FOOTPRINT")
    sm = SMOD.build(M["rooms"], model["elements"], possibly_external=DM.possibly_external_faces(S, M["rooms"]),
                    decisions_by_face=dec)
    return {"S": S, "M": M, "model": model, "decided": dec, "space_model": sm,
            "scenarios": DSTD.door_scenarios(model, facts, openings=M["openings"], rooms=M["rooms"]),
            "elevators": DSTD.elevator_schedule(model, M["rooms"], [{"floors": ["GF"], "face_ids": [shaft["face_id"]],
                                                                       "area_m2": shaft["area_m2"]}])}


def room_of(run, code):
    return next(r for r in run["M"]["rooms"] if code in (r.get("codes") or ()))


def door_between(run, code_a, code_b=None):
    """the door element with a space of code_a on one side and code_b (None: the facade / an exterior space) on the
    other."""
    for el in run["model"]["elements"]:
        codes = [set(sd.get("codes") or ()) for sd in el["sides"]]
        kinds = [sd["kind"] for sd in el["sides"]]
        if not any(code_a in c for c in codes):
            continue
        other = [c for c in codes if code_a not in c] or [set()]
        if code_b is None and any(k in ("FACADE", "EXTERIOR_SPACE") for k in kinds):
            return el
        if code_b is not None and code_b in other[0]:
            return el
    raise AssertionError(f"no door {code_a} | {code_b}")


def row_of(run, el):
    return next(r for r in run["scenarios"]["rows"] if r["element_id"] == el["element_id"])


# ---- hand-made space-model inputs (unit tests): rooms and door elements as arch_measure / door_model shape them
def space(face_id, *, codes=(), kind=None, cls="ROOM", passages=(), floor="GF", area=10.0):
    return {"room_id": f"{floor}-{face_id}", "face_id": face_id, "floor": floor, "class": cls,
            "codes": list(codes), "kind": kind, "passages": list(passages), "area_m2": area, "level_m": 0.0}


def door(element_id, side_a, side_b, *, floor="GF", cls=DM.PVC, state=DM.CONFIRMED):
    def sd(x):
        if x in ("FACADE", "EXTERIOR_SPACE"):
            return {"kind": x, "evidence": "synthetic"}
        return {"kind": "SPACE", "face_id": x}
    return {"element_id": element_id, "floor": floor, "sides": [sd(side_a), sd(side_b)], "state": state,
            "boq_class": cls, "class": cls}


def villa_run(tmp, method, *, facts=None, decisions=None):
    from tools import urban_boq_m9 as M9
    dxf = Path(tmp) / "villa.dxf"
    if not dxf.exists():
        AS.villa(dxf)
    kw = {"facts": facts} if facts else {}
    if decisions:
        kw["decisions"] = decisions
    try:
        room, arch = M9.arch_compute(str(dxf), method=method, **kw)[:2]
    except M9.CompletenessFailed as ex:                         # the run's outputs are still inspected
        room, arch = ex.room_boq, ex.arch
    return room, arch


def dry_passage(path):
    """a 5.0 x 4.0 m LIVING and a 3.8 x 4.0 m DINING joined by a 1.20 m doorless passage in their 0.20 m party wall
    (both dry rooms: the passage jambs are skirted, 2 x 0.20 m)."""
    rooms = {"LIVING": [(200, 200), (5200, 200), (5200, 4200), (200, 4200)],
             "DINING": [(5400, 200), (9200, 200), (9200, 4200), (5400, 4200)]}
    outer = [(0, 0), (9400, 0), (9400, 4400), (0, 4400)]
    ops = [("PASSAGE", "x", 5200, 5400, 1000, 2200, None)]
    doc, msp = FX._doc()
    return FX._save(doc, msp, path, rooms=rooms, outer=outer, labels={"LIVING": (2500, 3000), "DINING": (7000, 3000)},
                    words={"LIVING": "LIVING", "DINING": "DINING"}, openings=ops)


def drawing_run(path, method, *, facts=None):
    from tools import urban_boq_m9 as M9
    try:
        room, arch = M9.arch_compute(str(path), method=method, **({"facts": facts} if facts else {}))[:2]
    except M9.CompletenessFailed as ex:
        room, arch = ex.room_boq, ex.arch
    return room, arch
