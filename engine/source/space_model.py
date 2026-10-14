"""SPACE CONNECTIVITY MODEL (M9 Phase 2B-1, ARCH_TAKEOFF_V2.3 only) - every space a node with independently supported
attributes, every door and doorless passage an edge (rule UP-SPACE-001).

    decided_faces(S, floor, decisions)       -> {face_id: decision} for the project decisions bound to this floor
    build(rooms, doors, *, possibly_external=None, decisions_by_face=None)
        -> {"spaces": [...], "edges": [...], "building_parts": {...}, "candidates": [...], "summary": {...}}
    apply_decisions(model, decisions_by_face) the same model with bound project decisions applied (UP-SPACE-002)

A space carries: floor, function (room code or UNLABELLED), interior status (INTERIOR / EXTERIOR / POSSIBLY_EXTERIOR
/ UNKNOWN) with its evidence and confidence, enclosure, finish scope (owner_finish_scope), building part, level.
Status evidence, in order: a bound project decision; an exterior room word; an interior room word; an unlabelled
space with a doorless facade opening (POSSIBLY_EXTERIOR); an unlabelled space every connection of which leads to
interior spaces and that touches no facade (INTERIOR by enclosure); otherwise UNKNOWN - never assumed interior.
A space that joins two separate interior building parts is reported as a connecting space (evidence only).
Project decisions bind ONE space each, by floor and a point inside it; an unbound decision applies to nothing.
Project-agnostic; stdlib only."""

from __future__ import annotations

from collections import defaultdict

from engine.source import arch_rooms as AR

POLICY_ID = "SPACE_MODEL_V1"
INTERIOR, EXTERIOR, POSSIBLY_EXTERIOR, UNKNOWN = "INTERIOR", "EXTERIOR", "POSSIBLY_EXTERIOR", "UNKNOWN"
DECISIONS_SCHEMA = "URBAN_PROJECT_DECISIONS_V1"


def _inside(p, poly):
    x, y = p
    n = len(poly)
    c = False
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


def decided_faces(S, floor, decisions):
    """the faces of one floor's spaces result bound by project decisions (URBAN_PROJECT_DECISIONS_V1): a decision
    names its floor and a point inside the space (drawing coordinates, m); the face containing that point is bound.
    -> {face_id: decision}; decisions that bind no face are reported by unbound()."""
    out = {}
    if not decisions:
        return out
    u = S["unit_m"]
    faces = [f for f in S.get("faces") or () if f.get("class") not in ("DOORWAY", "WALL", "SLIVER")]
    for d in decisions.get("decisions") or ():
        if d.get("floor") != floor or not d.get("point_m") or \
                (d.get("set") or {}).get("interior_status") not in (INTERIOR, EXTERIOR, POSSIBLY_EXTERIOR, UNKNOWN):
            continue                                # a malformed decision binds nothing (reported by unbound())
        p = (d["point_m"][0] / u, d["point_m"][1] / u)
        hit = [f for f in faces if _inside(p, f["polygon"])]
        if len(hit) == 1:
            out[hit[0]["face_id"]] = d
    return out


def unbound(decisions, bound_ids):
    return [d for d in (decisions or {}).get("decisions") or () if d.get("id") not in bound_ids]


def _status(room, possibly_external, decision):
    codes = room.get("codes") or []
    kind = room.get("kind")
    ev = []
    if decision is not None:
        st = decision["set"]["interior_status"]
        ev.append(f"project decision {decision['id']} ({decision.get('rule_id')}): {decision.get('statement', '')}")
        return st, "PROJECT_DECISION", ev
    if codes and kind == AR.EXTERIOR:
        return EXTERIOR, "LABEL", [f"exterior room word ({'+'.join(codes)})"]
    if codes:
        return INTERIOR, "LABEL", [f"room word ({'+'.join(codes)}): a room function implies an enclosed room"]
    if room["face_id"] in (possibly_external or {}):
        return POSSIBLY_EXTERIOR, "FACADE_OPENING", [possibly_external[room["face_id"]]]
    return UNKNOWN, None, ["no room word"]


def build(rooms, doors, *, possibly_external=None, decisions_by_face=None):
    """rooms: arch_measure rooms of every floor (each with floor, face_id, codes, kind, passages); doors: the door
    model elements (with their typed sides)."""
    from engine.source import owner_finish_scope as OFS
    decisions_by_face = decisions_by_face or {}
    spaces = {}
    for r in rooms:
        st, basis, ev = _status(r, possibly_external, decisions_by_face.get(r["face_id"]))
        spaces[r["face_id"]] = {
            "space_id": r["room_id"], "face_id": r["face_id"], "floor": r["floor"], "class": r["class"],
            "function": "+".join(r.get("codes") or ()) or "UNLABELLED", "kind": r.get("kind"),
            "interior_status": st, "status_basis": basis, "evidence": ev,
            "confidence": {"PROJECT_DECISION": "HIGH", "LABEL": "HIGH", "FACADE_OPENING": "MEDIUM"}.get(basis, "LOW"),
            "enclosed": r.get("kind") != AR.EXTERIOR, "finish_scope": OFS.finish_scope(r)["scope"],
            "level_m": r.get("level_m"), "area_m2": r.get("area_m2"), "doors": [], "passages": list(r.get("passages")
                                                                                                   or ()),
            "facade_doors": 0}
    edges = []
    for el in doors:
        a, b = el["sides"]
        ends = []
        for sd in (a, b):
            if sd.get("face_id") in spaces:
                ends.append(sd["face_id"])
            else:
                ends.append({"FACADE": "OUTSIDE", "EXTERIOR_SPACE": "OUTSIDE"}.get(sd["kind"], sd["kind"]))
        edges.append({"edge_id": el["element_id"], "kind": "DOOR", "floor": el["floor"], "ends": ends,
                      "state": el["state"], "class": el.get("boq_class") or el.get("class")})
        for e in ends:
            if e in spaces:
                spaces[e]["doors"].append(el["element_id"])
                if "OUTSIDE" in ends:
                    spaces[e]["facade_doors"] += 1
    by_passage = defaultdict(list)
    for fid, s in spaces.items():
        for p in s["passages"]:
            by_passage[(s["floor"], p)].append(fid)
    for (floor, p), fids in sorted(by_passage.items()):
        edges.append({"edge_id": p, "kind": "PASSAGE", "floor": floor,
                      "ends": fids if len(fids) > 1 else fids + ["OUTSIDE_OR_UNMODELLED"], "state": "CONFIRMED",
                      "class": "PASSAGE"})
    # an unlabelled space whose every connection leads to interior spaces and that touches no facade: interior by
    # enclosure (a medium-confidence inference, recorded as such)
    for s in spaces.values():
        if s["interior_status"] != UNKNOWN:
            continue
        ends = [e for ed in edges if s["face_id"] in ed["ends"] for e in ed["ends"] if e != s["face_id"]]
        if ends and all(e in spaces and spaces[e]["interior_status"] == INTERIOR for e in ends) and \
                not s["facade_doors"]:
            s.update(interior_status=INTERIOR, status_basis="ENCLOSURE", confidence="MEDIUM")
            s["evidence"].append("every door / passage of the space leads to an interior space; no facade opening")
    model = {"policy": POLICY_ID, "spaces": sorted(spaces.values(), key=lambda s: (s["floor"], s["space_id"])),
             "edges": edges}
    _parts(model)
    return model


def _parts(model):
    """interior building parts per floor (union-find over interior spaces joined by doors / passages) and the
    non-interior spaces that join two of them."""
    sp = {s["face_id"]: s for s in model["spaces"]}
    parent = {f: f for f, s in sp.items() if s["interior_status"] == INTERIOR}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for ed in model["edges"]:
        ins = [e for e in ed["ends"] if e in parent]
        for a, b in zip(ins, ins[1:]):
            parent[find(a)] = find(b)
    roots = sorted({find(f) for f in parent})
    name = {r: f"PART-{i + 1}" for i, r in enumerate(roots)}
    for f, s in sp.items():
        s["building_part"] = name[find(f)] if f in parent else None
    cands = []
    for s in model["spaces"]:
        if s["interior_status"] == INTERIOR:
            continue
        nb = {sp[e]["building_part"] for ed in model["edges"] if s["face_id"] in ed["ends"]
              for e in ed["ends"] if e in sp and sp[e]["building_part"]}
        if len(nb) >= 2:
            s["connects_parts"] = sorted(nb)
            s["evidence"].append(f"joins separate interior building parts {', '.join(sorted(nb))}")
            cands.append({"space_id": s["space_id"], "floor": s["floor"], "function": s["function"],
                          "interior_status": s["interior_status"], "connects_parts": sorted(nb),
                          "use": "evidence for a project decision (e.g. an outdoor service corridor); never applied "
                                 "automatically"})
    model["building_parts"] = {s["floor"]: sorted({x["building_part"] for x in model["spaces"]
                                                   if x["floor"] == s["floor"] and x["building_part"]})
                               for s in model["spaces"]}
    model["candidates"] = cands
    c = defaultdict(int)
    for s in model["spaces"]:
        c[s["interior_status"]] += 1
    model["summary"] = {"spaces": len(model["spaces"]), "edges": len(model["edges"]), "by_status": dict(sorted(c.items())),
                        "connecting_spaces": len(cands)}
    return model


def apply_decisions(model, decisions_by_face):
    """re-derive the statuses with the bound project decisions (UP-SPACE-002); only the bound spaces change."""
    for s in model["spaces"]:
        d = decisions_by_face.get(s["face_id"])
        if d is not None:
            s.update(interior_status=d["set"]["interior_status"], status_basis="PROJECT_DECISION", confidence="HIGH")
            s["evidence"].append(f"project decision {d['id']}: {d.get('statement', '')}")
    return _parts(model)


def policy_record():
    return {"policy": POLICY_ID, "rule": "UP-SPACE-001 / UP-SPACE-002", "decisions_schema": DECISIONS_SCHEMA,
            "statuses": [INTERIOR, EXTERIOR, POSSIBLY_EXTERIOR, UNKNOWN]}
