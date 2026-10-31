"""T-388: finishes face consistency across the wall-face families of a candidate (any villa; stdlib only).

The physical element (ERS 2026-10-22 s.2.1): one wall FACE = one side of one wall seen from one room. On it the
families stack: the block panel (the wall itself, both sides at once), the plaster coat (dry rooms) or the backing coat
(wet rooms, under the tile), the paint (dry rooms, below the ceiling line) or the wall tile (wet rooms), and at each
opening the reveal (the wall-thickness faces: jambs, head) and the sill / threshold (the floor-level face through the
wall). Each opening is ONE hole: every family that deducts it deducts it once per face, on the faces of its host wall,
and with one size (a band family deducts only the part inside its band). A reveal is a surface of its own and is never
also inside a room face; a threshold is never also inside a room floor.

Rule R-T388-1 (proposed, every villa; research, no method version):
  (a) per family, one opening id at most once per face and on at most two faces (the two sides of its host wall);
  (b) every family that deducts an opening deducts it on the same host wall (the block wall carrying its deduction);
      a door the room contour walks as an off-line doorway piece is deducted on that piece, not on a straight face
      whose drawn line carries no doorway (OPENING_OFF_ITS_FACE: room total unchanged, face attribution named);
  (c) full-height families (block, plaster, paint) deduct one m2 per opening within TOL_M2; a band family (tile,
      backing) deducts at most the full-height m2 (more is refused: BAND_ABOVE_HOLE);
  (d) on a face, the tile top never exceeds the coat top under it (backing / plaster): TILE_ABOVE_COAT, m2 named;
      a fully tiled room (every face TILED to the coat top) carries no paint line other than NOT_APPLICABLE;
  (d') per room, each family's face length equals the geometric face length (contour less open sides) within
      TOL_LEN_M, or the difference is named in m2 (FACE_LENGTH_RESIDUAL) unless a merged ledger explains it;
  (e) a reveal carried by its own line is never also walked into the room face (the face's jamb-return metres x the
      opening height are named in m2: REVEAL_IN_FACE);
  (f) a threshold strip overlapping a room floor by more than TOL_M2 is named (THRESHOLD_IN_FLOOR);
  (g) HELD stays blank: a family value of 0 on a HELD face is refused (HELD_AS_ZERO); totals report the determinate sum
      and the HELD faces apart, never a HELD value as 0.
Every finding is a named item with its m2; nothing here changes a quantity. EXPLAINED kinds (BLOCK_PART_EXPLAINED:
the hole runs past the masonry into a column / beam the block panel excludes, the cause cited) are named differences,
not defects; a split face (one wall side shared by two room regions) deducts part widths that must close on the opening.
"""

from __future__ import annotations

from collections import defaultdict

TOL_M2 = 0.01
TOL_LEN_M = 0.025  # five 5 mm contour samples (the walk-class artefact seen on Checker-verified rooms)
FULL = ("block", "plaster", "paint")
BAND = ("tile", "backing")
FAMILIES = FULL + BAND
DOORWAY_KINDS = ("door", "doorway", "arch", "gate")


def _num(x):
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return float(x)
    s = str(x).strip()
    if not s or s.upper().startswith("HELD"):
        return None
    return float(s)


def _check_height(h, where):
    if h is not None and not (0.0 <= h <= 20.0):
        raise ValueError(f"{where}: height {h} m outside 0 .. 20 m (units?)")


def finding(kind, m2=None, **kw):
    d = {"kind": kind, "m2": None if m2 is None else round(m2, 4)}
    d.update(kw)
    return d


def check(faces, deductions, block=(), reveals=(), thresholds=(), paint_lines=(), closures=()):
    """faces: [{face_id, room, wall, room_class, length_m, tops: {family: m or None}, states: {family: status}}]
    deductions: [{family, face_id, opening, m2 (None = HELD)}]; block: [{wall, opening, m2}];
    reveals: [{opening, room, face_id, carrier, jamb_return_m, h_m}]  (jamb_return_m: walked into the room face);
    thresholds: [{opening, strip_m2, floor_overlap_m2}]; paint_lines: [{room, state}].
    Returns the list of findings (empty = consistent)."""
    out = []
    fidx = {}
    for f in faces:
        if f["face_id"] in fidx:
            out.append(finding("FACE_TWICE", face_id=f["face_id"]))
        fidx[f["face_id"]] = f
        for fam, h in (f.get("tops") or {}).items():
            _check_height(_num(h), f"{f['face_id']} {fam}")
        for fam, st in (f.get("states") or {}).items():
            v = (f.get("values") or {}).get(fam)
            if st and str(st).upper().startswith("HELD") and v is not None and _num(v) == 0.0:
                out.append(finding("HELD_AS_ZERO", face_id=f["face_id"], family=fam))

    # (a) once per face, at most two faces
    seen = defaultdict(list)
    for d in deductions:
        if d["face_id"] not in fidx:
            out.append(finding("DEDUCTION_ON_UNKNOWN_FACE", family=d["family"], face_id=d["face_id"],
                               opening=d["opening"]))
            continue
        seen[(d["family"], d["opening"])].append(d)
    for (fam, op), ds in sorted(seen.items()):
        per_face = defaultdict(list)
        for d in ds:
            per_face[d["face_id"]].append(d)
        for fid, dd in per_face.items():
            if len(dd) > 1:
                extra = sum((_num(x["m2"]) or 0.0) for x in dd[1:])
                out.append(finding("DUPLICATE_DEDUCTION", extra, family=fam, opening=op, face_id=fid, times=len(dd)))
        split = [d for d in ds if d.get("split_w") is not None]
        sides = len({d["face_id"] for d in ds if d.get("split_w") is None}) + (1 if split else 0)
        if split:
            full_w = _num(split[0].get("full_w"))
            got = sum(_num(d["split_w"]) for d in split)
            if full_w is None or abs(got - full_w) > 0.01:
                out.append(finding("SPLIT_FACE_DOES_NOT_CLOSE", opening=op, family=fam, split_sum_w=round(got, 4),
                                   full_w=full_w, faces=sorted(d["face_id"] for d in split)))
        if sides > 2:
            out.append(finding("OPENING_ON_TOO_MANY_FACES", family=fam, opening=op, faces=sorted(per_face)))

    # (b) host wall
    bwall = {}
    explained = {}
    for b in block:
        if b.get("full_hole_m2") is not None and b.get("reason"):
            explained[b["opening"]] = (_num(b["full_hole_m2"]), _num(b["m2"]), b["reason"])
        if b["opening"] in bwall and bwall[b["opening"]][0] != b["wall"]:
            out.append(finding("BLOCK_DEDUCTS_ON_TWO_WALLS", opening=b["opening"],
                               walls=[bwall[b["opening"]][0], b["wall"]]))
        bwall.setdefault(b["opening"], (b["wall"], _num(b["m2"])))
    for (fam, op), ds in sorted(seen.items()):
        if op not in bwall:
            continue
        walls = {fidx[d["face_id"]]["wall"] for d in ds if not str(fidx[d["face_id"]]["wall"]).startswith("OFF:")}
        if walls - {bwall[op][0]}:
            out.append(finding("HOST_MISMATCH", family=fam, opening=op, block_wall=bwall[op][0],
                               face_walls=sorted(walls)))

    # (b2) a door / doorway deducted on a straight face whose drawn line carries no doorway, while the same room walks
    #      the doorway as an off-line piece: the room total is right, the face attribution is not (w x h moves)
    off_rooms = {f["room"] for f in faces if str(f["wall"]).startswith("OFF:DOORWAY")}
    for (fam, op), ds in sorted(seen.items()):
        for d in ds:
            f = fidx[d["face_id"]]
            w = _num(d.get("w"))
            if (d.get("kind") in DOORWAY_KINDS and f["room"] in off_rooms and not str(f["wall"]).startswith("OFF:") and w is not None
                    and f.get("door_m") is not None and (_num(f["door_m"]) or 0.0) + (_num(f.get("gap_m")) or 0.0)
                    < w - 0.05):
                out.append(finding("OPENING_OFF_ITS_FACE", _num(d["m2"]), family=fam, opening=op,
                                   face_id=d["face_id"], drawn_door_on_face_m=_num(f["door_m"]),
                                   room_off_line_face=f"{f['room']}|OFF:DOORWAY", room_total_effect_m2=0.0))

    # (c) one size per opening
    size = defaultdict(dict)
    for (fam, op), ds in seen.items():
        if any(d.get("split_w") is not None for d in ds):
            vals = [_num(d.get("full_m2")) for d in ds if _num(d.get("full_m2")) is not None]
        else:
            vals = [_num(d["m2"]) for d in ds if _num(d["m2"]) is not None]
        if vals:
            size[op][fam] = max(vals)
    for op, (w, m2) in bwall.items():
        if m2 is not None:
            if op in explained:
                full, part, why = explained[op]
                out.append(finding("BLOCK_PART_EXPLAINED", full - part, opening=op, block_m2=part, hole_m2=full,
                                   reason=why))
                m2 = full
            size[op].setdefault("block", m2)
    for op, fams in sorted(size.items()):
        full = {k: v for k, v in fams.items() if k in FULL}
        if len(full) > 1 and max(full.values()) - min(full.values()) > TOL_M2:
            out.append(finding("SIZE_MISMATCH", max(full.values()) - min(full.values()), opening=op,
                               sizes={k: round(v, 4) for k, v in sorted(full.items())}))
        if full:
            ref = max(full.values())
            for k in BAND:
                if k in fams and fams[k] - ref > TOL_M2:
                    out.append(finding("BAND_ABOVE_HOLE", fams[k] - ref, opening=op, family=k,
                                       band_m2=round(fams[k], 4), hole_m2=round(ref, 4)))

    # (d) tile above its coat; paint on a fully tiled room
    tiled_rooms = defaultdict(lambda: [0, 0])
    for f in faces:
        tops = f.get("tops") or {}
        t = _num(tops.get("tile"))
        coat = _num(tops.get("backing", tops.get("plaster")))
        if t is not None and coat is not None and t - coat > 1e-6:
            L = _num(f.get("length_m"))
            out.append(finding("TILE_ABOVE_COAT", None if L is None else (t - coat) * L, face_id=f["face_id"],
                               tile_top=t, coat_top=coat))
        if f.get("room_class") == "WET" and (f.get("states") or {}).get("tile", "NO_TILE_FACE") != "NO_TILE_FACE":
            tiled_rooms[f["room"]][0] += 1
            if t is not None and coat is not None and abs(t - coat) <= 1e-6:
                tiled_rooms[f["room"]][1] += 1
    full_tiled = {r for r, (n, k) in tiled_rooms.items() if n and n == k}
    for p in paint_lines:
        if p["room"] in full_tiled and str(p.get("state", "")).upper() not in ("NOT_APPLICABLE",
                                                                                "NOT_APPLICABLE_WITH_EVIDENCE"):
            out.append(finding("PAINT_LINE_ON_FULL_TILE", room=p["room"], state=p.get("state")))

    # (e) reveal also in the face
    for r in reveals:
        j, h = _num(r.get("jamb_return_m")), _num(r.get("h_m"))
        if r.get("carrier") and j and j > 1e-6:
            out.append(finding("REVEAL_IN_FACE", None if h is None else j * h, opening=r["opening"],
                               room=r.get("room"), carrier=r["carrier"], jamb_return_m=j))

    # (d2) a family's face length per room against the geometric face length of the same room
    for c in closures:
        d = _num(c["family_length_m"]) - _num(c["geometric_length_m"])
        if abs(d) > TOL_LEN_M and not c.get("explained"):
            top = _num(c.get("top_m"))
            out.append(finding("FACE_LENGTH_RESIDUAL", None if top is None else d * top, room=c["room"],
                               family=c["family"], residual_m=round(d, 4), top_m=top, cause=c.get("cause")))

    # (f) threshold in the floor
    for t in thresholds:
        ov = _num(t.get("floor_overlap_m2")) or 0.0
        if ov > TOL_M2:
            out.append(finding("THRESHOLD_IN_FLOOR", ov, opening=t["opening"]))
    return out


EXPLAINED = ("BLOCK_PART_EXPLAINED", "ROOM_SIDE_WIDTH_RULE_DIFFERENCE")


def family_total(faces, family):
    """Determinate sum of a family's face values and the HELD faces apart (a HELD value is never 0)."""
    s, held = 0.0, []
    for f in faces:
        v = _num((f.get("values") or {}).get(family))
        st = str((f.get("states") or {}).get(family, ""))
        if v is None or st.upper().startswith("HELD"):
            if family in (f.get("values") or {}) or family in (f.get("states") or {}):
                held.append(f["face_id"])
            continue
        s += v
    return round(s, 4), held
