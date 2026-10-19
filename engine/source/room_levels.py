"""ROOM LEVELS V1 (T-081) - each room's finished floor level from the level mark printed INSIDE it, and the storey's
level zones built only from those rooms. Read-only, additive: no method version reads this module yet, so no quantity
changes; a later method version wires it (UP-HGT-001 rank 1 / 3 evidence, owner answer Q-14).

Why: the released route takes a plan's floor level from arch_rooms.dominant_level (the most frequent level text of the
whole plan frame). On a real ground-floor plan the plot / site corner marks (+-0.00) can outnumber the floor's own
marks, so the storey gets the plot level although every room prints its own level (+1.00 main, +0.30 annex: a split
level). A floor-to-next taken from that wrong level is wrong by the step (5.50 - 0.00 instead of 5.50 - 1.00).

Rules (owner Q-14: every level keeps its kind and source; drawing-first directive; no assumptions):
  * a level text is a finished-floor level (F.F.L. label) or a bare signed level mark (+1.00, %%p0.00, -0.20)
    (section_binding.level_of); a ceiling, soffit, slab-top or parapet level is never a floor level (kept apart);
  * a level text belongs to the room whose outline contains it (outside its holes; nested outlines -> the smallest);
  * a text in no room outline is an OUTSIDE_ROOM_MARK and never a room's floor level (plot corners, street,
    neighbour, an unenclosed terrace or roof);
  * a text inside a space that is not a room (EXTERIOR yard / court / roof / pool, VOID, SHAFT or an unidentified
    space) is an EXTERIOR_OR_NON_ROOM_LEVEL and never a floor level;
  * a room with exactly one printed value -> PRINTED (its level, every source text);
  * a STAIR with two or more values -> HELD (STAIR_LINKS_LEVELS: the stair joins the zones, it has no one floor level);
  * any other room with two values -> HELD (TWO_LEVELS_IN_ROOM, both kept, a finding);
  * a room with no printed value -> HELD (UNLEVELLED_ROOM); it never takes the storey's level or another zone's
    level by guess, not even on a storey whose printed levels all agree (that is reported as storey context only);
  * the storey's zones = the distinct PRINTED room levels (one zone: SINGLE_LEVEL; two or more: SPLIT_LEVEL; none:
    NOT_PRINTED); the old plan-dominant level is compared and a disagreement is the finding
    PLAN_DOMINANT_LEVEL_IS_NOT_A_ROOM_LEVEL.
Project-agnostic: no layer names, coordinates or project values; the drawing unit only scales the geometry (the level
values are printed metres). Stdlib only (plus the engine's own text / geometry helpers).

    room_levels(texts, rooms, floor=None, box=None) -> {"floor", "rooms", "zones", "storey", "outside_marks",
                                                         "non_room_levels", "findings", "policy"}
    zone_of(room_record, floor_report)          -> the section_binding zone report of the room's level, or a HELD record
rooms: [{"room_id", "kind", "polygon", "holes"?: [polygon, ...], "codes"?: [...]}] in drawing units;
kind None / EXTERIOR / VOID / SHAFT = not a room (section_binding.NOT_A_ROOM).
"""

from __future__ import annotations

from engine.source import arch_rooms as AR
from engine.source import arch_v28 as V28
from engine.source import section_binding as SB

POLICY_ID = "ROOM_LEVELS_V1"
FLOOR_LEVEL_KINDS = ("FFL", "MARK")
NOT_A_ROOM = SB.NOT_A_ROOM
STAIR = "STAIR"
AGREE_M = SB.AGREE_M
PRINTED, HELD = "PRINTED", "HELD"


def _area(poly):
    s = 0.0
    for i in range(len(poly)):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % len(poly)]
        s += x1 * y2 - x2 * y1
    return abs(s) / 2.0


def _contains(room, p):
    if not V28._inside(p, room["polygon"]):
        return False
    return not any(V28._inside(p, h) for h in room.get("holes") or ())


def _src(t, **kw):
    return dict({"text_id": t.get("id"), "text": t.get("value"), "layer": t.get("layer")}, **kw)


def _distinct(values):
    out = []
    for v in sorted(values):
        if not out or abs(v - out[-1]) > AGREE_M:
            out.append(round(v, 3))
    return out


def room_levels(texts, rooms, floor=None, box=None):
    rooms = list(rooms or ())
    in_box = [t for t in texts if box is None or V28._in_box((t["x"], t["y"]), box)]
    by_room = {r["room_id"]: [] for r in rooms}
    other_by_room = {r["room_id"]: [] for r in rooms}
    site, non_room, findings = [], [], []
    order = sorted(rooms, key=lambda r: _area(r["polygon"]))          # nested outlines: the smallest first
    for t in in_box:
        lv = SB.level_of(t["value"])
        if not lv:
            continue
        kind, value = lv
        host = next((r for r in order if _contains(r, (t["x"], t["y"]))), None)
        if kind not in FLOOR_LEVEL_KINDS:
            if host is not None:
                other_by_room[host["room_id"]].append(_src(t, level_kind=kind, value_m=value))
            continue
        if host is None:
            site.append(_src(t, level_kind=kind, value_m=value,
                             why="OUTSIDE_ROOM_MARK: in no room outline (plot, street, terrace or roof mark); never "
                                 "a room's floor level"))
        elif host.get("kind") in NOT_A_ROOM:
            non_room.append(_src(t, level_kind=kind, value_m=value, room_id=host["room_id"],
                                 room_kind=host.get("kind"),
                                 why="EXTERIOR_OR_NON_ROOM_LEVEL: inside a space that is not a room; never a floor "
                                     "level"))
        else:
            by_room[host["room_id"]].append((value, _src(t, level_kind=kind, value_m=value)))
    recs, zones = [], {}
    for r in rooms:
        rid, kind = r["room_id"], r.get("kind")
        base = {"room_id": rid, "kind": kind, "codes": list(r.get("codes") or ()),
                "other_levels": other_by_room[rid]}
        if kind in NOT_A_ROOM:
            recs.append(dict(base, state="NOT_A_FLOOR_ROOM", level_m=None,
                             why="not a room (exterior, void, shaft or unidentified space): no floor level is taken"))
            continue
        hits = by_room[rid]
        vals = _distinct(v for v, _ in hits)
        src = [s for _, s in hits]
        if len(vals) == 1:
            rec = dict(base, state=PRINTED, level_m=vals[0], level_kind=sorted({s["level_kind"] for s in src}),
                       source=src)
            z = zones.setdefault(vals[0], {"level_m": vals[0], "rooms": [], "source": []})
            z["rooms"].append(rid)
            z["source"] += [dict(s, room_id=rid) for s in src]
        elif not vals:
            rec = dict(base, state=HELD, level_m=None,
                       why="UNLEVELLED_ROOM: no level is printed inside the room; the storey's or another zone's "
                           "level is never taken by guess")
        elif kind == STAIR:
            rec = dict(base, state=HELD, level_m=None, printed_levels_m=vals, source=src,
                       why="STAIR_LINKS_LEVELS: the stair joins the printed levels; it has no single floor level")
        else:
            rec = dict(base, state=HELD, level_m=None, printed_levels_m=vals, source=src,
                       why="TWO_LEVELS_IN_ROOM: two different levels are printed inside one room")
            findings.append({"code": "TWO_LEVELS_IN_ROOM", "floor": floor, "room_id": rid, "levels_m": vals})
        recs.append(rec)
    zl = [zones[k] for k in sorted(zones)]
    how = "NOT_PRINTED" if not zl else "SINGLE_LEVEL" if len(zl) == 1 else "SPLIT_LEVEL"
    links = sorted({tuple(r["printed_levels_m"]) for r in recs if r.get("why", "").startswith("STAIR_LINKS")})
    dom = AR.dominant_level(in_box)
    storey = {"floor": floor, "how": how, "levels_m": [z["level_m"] for z in zl],
              "stair_links_m": [list(x) for x in links], "plan_dominant_level_m": dom,
              "rooms_printed": sum(1 for r in recs if r["state"] == PRINTED),
              "rooms_held": sum(1 for r in recs if r["state"] == HELD),
              "never": ["a mark outside every room as a floor level", "an unlevelled room given a zone by guess",
                        "a missing level as 0"]}
    if not zl:
        findings.append({"code": "FLOOR_LEVEL_NOT_PRINTED_IN_ANY_ROOM", "floor": floor,
                         "plan_dominant_level_m": dom})
    elif dom is not None and all(abs(dom - z["level_m"]) > AGREE_M for z in zl):
        findings.append({"code": "PLAN_DOMINANT_LEVEL_IS_NOT_A_ROOM_LEVEL", "floor": floor,
                         "plan_dominant_level_m": dom, "room_levels_m": storey["levels_m"],
                         "outside_marks_at_dominant": sum(1 for s in site if abs(s["value_m"] - dom) <= AGREE_M)})
    for lk in links:
        missing = [v for v in lk if all(abs(v - z["level_m"]) > AGREE_M for z in zl)]
        if missing:
            findings.append({"code": "STAIR_LEVEL_IN_NO_ROOM", "floor": floor, "levels_m": missing})
    return {"policy": policy_record(), "floor": floor, "rooms": recs, "zones": zl, "storey": storey,
            "outside_marks": site, "non_room_levels": non_room, "findings": findings}


def zone_of(room, floor_report):
    """the section_binding._floor_report zone of a PRINTED room's level; else a HELD record (never another zone)."""
    if room.get("state") != PRINTED:
        return {"state": HELD, "why": "ROOM_LEVEL_HELD: " + str(room.get("why"))}
    for z in (floor_report or {}).get("zones") or ():
        if abs(z["ffl"]["value_m"] - room["level_m"]) <= AGREE_M:
            return dict(z, state="BOUND")
    return {"state": HELD, "why": f"ZONE_NOT_REPORTED: the floor report has no zone at {room['level_m']:+.2f}"}


def policy_record():
    return {"policy_id": POLICY_ID, "floor_level_kinds": list(FLOOR_LEVEL_KINDS), "agree_m": AGREE_M,
            "not_a_room": [str(k) for k in NOT_A_ROOM],
            "states": [PRINTED, HELD, "NOT_A_FLOOR_ROOM"],
            "held_reasons": ["UNLEVELLED_ROOM", "STAIR_LINKS_LEVELS", "TWO_LEVELS_IN_ROOM"],
            "rules": ["owner Q-14", "UP-HGT-001", "UP-QA-001", "drawing-first directive (MISSION.md)"],
            "never": ["a mark outside every room as a floor level", "the plan's most frequent level as a room level",
                      "an unlevelled room given the storey's or another zone's level", "a missing level as 0"]}


# ================================================================================================ ROOM LEVELS V2
# T-081 rework (owner answer Q-43, 2026-10-19 21:40, docs/agents/OWNER_QUESTIONS.md; registry UP-HGT-001 1.8.0
# room_level): V1 above is unchanged. V2 adds ONE step for the rooms V1 holds as UNLEVELLED_ROOM:
#   * a floor whose printed room levels are all the same (SINGLE_LEVEL, no room with two levels): every unmarked room
#     takes that level (state FLOOR_LEVEL, source: the printed marks of the floor; "floor level, not printed in the
#     room"); an unmarked STAIR stays HELD (STAIR_UNMARKED: a stair joins levels);
#   * a split floor (SPLIT_LEVEL): a room takes a level only from what is drawn:
#       DRAWN       a level read for that room on a section / from a drawn step count (caller evidence, with source);
#       OPENS_INTO  the level of a levelled room it opens into, through an opening where NOTHING is drawn across the
#                   doorway (doorway_reading NONE_DRAWN: no step, sill or head line besides the door symbol itself);
#                   repeated room by room (a bathroom off a bedroom that opens into the hall), each hop recorded;
#     otherwise HELD with the reason: OPENS_INTO_TWO_LEVELS, DOORWAY_LINES_DRAWN (a line across the doorway may be a
#     step: not read as one), DOORWAY_NOT_READ, NO_OPENING_TO_A_LEVELLED_ROOM, DRAWN_LEVELS_DISAGREE;
#   * a floor with no printed room level, or a room with two printed levels: unchanged (HELD).
# Never: a level by guess, the plot / court marks as a room level, a missing level as 0.
POLICY_ID_V2 = "ROOM_LEVELS_V2"
FLOOR_LEVEL, DRAWN, OPENS_INTO = "FLOOR_LEVEL", "DRAWN", "OPENS_INTO"
LEVELLED = (PRINTED, FLOOR_LEVEL, DRAWN, OPENS_INTO)
NONE_DRAWN, LINES_DRAWN, NOT_READ = "NONE_DRAWN", "LINES_DRAWN", "NOT_READ"
DOORWAY_TOL_M = 0.02
DOORWAY_SPAN_SHARE = 0.8                       # a line across the doorway spans at least 80 % of its width
Q43 = "owner Q-43 answer 2026-10-19 21:40 (docs/agents/OWNER_QUESTIONS.md); UP-HGT-001 1.8.0 room_level"


def doorway_reading(opening, segments, unit_m, skip_layers=()):
    """what is drawn ACROSS one doorway (a line along the wall axis, inside the wall band, spanning most of the
    opening), besides the door symbol's own lines (its block) and the layers in skip_layers (door / window layers).
    opening: {"centre_m": (x, y), "axis": (ux, uy), "width_m", "wall_t_m", "symbol_blocks": [...]} in drawing metres.
    -> {"state": NONE_DRAWN | LINES_DRAWN | NOT_READ, "lines": [segment ids]}. A line there may be a step, a sill or
    a head line: it is never read as a level, only as 'something is drawn'."""
    try:
        cx, cy = (v / unit_m for v in opening["centre_m"])
        ux, uy = opening["axis"]
        w, t = opening["width_m"] / unit_m, opening["wall_t_m"] / unit_m
    except (KeyError, TypeError, ValueError):
        return {"state": NOT_READ, "lines": [], "why": "opening geometry missing"}
    n = (ux * ux + uy * uy) ** 0.5
    if not n or w <= 0 or t <= 0:
        return {"state": NOT_READ, "lines": [], "why": "opening geometry missing"}
    ux, uy = ux / n, uy / n
    nx, ny = -uy, ux
    tol = DOORWAY_TOL_M / unit_m
    blocks = set(opening.get("symbol_blocks") or ())
    hits = []
    for s in segments:
        if s.get("layer") in skip_layers or blocks.intersection(s.get("path") or ()):
            continue
        pa = [((p[0] - cx) * ux + (p[1] - cy) * uy, (p[0] - cx) * nx + (p[1] - cy) * ny) for p in (s["a"], s["b"])]
        if any(abs(o) > t / 2 + tol for _, o in pa):
            continue
        lo, hi = sorted(a for a, _ in pa)
        if min(hi, w / 2) - max(lo, -w / 2) >= DOORWAY_SPAN_SHARE * w:
            hits.append(s.get("id"))
    return {"state": LINES_DRAWN if hits else NONE_DRAWN, "lines": hits}


def room_levels_v2(texts, rooms, floor=None, box=None, links=(), drawn=()):
    """V1 + the Q-43 step for unmarked rooms. links: [{"opening_id", "rooms": [room_id, ...], "doorway": NONE_DRAWN |
    LINES_DRAWN | NOT_READ}] (doorway_reading of each opening); drawn: [{"room_id", "level_m", "kind", "source"}]
    (a section cutting the room, a drawn step count from a known level), each with its source."""
    rep = room_levels(texts, rooms, floor=floor, box=box)
    recs = {r["room_id"]: r for r in rep["rooms"]}
    st = rep["storey"]
    two = any(f["code"] == "TWO_LEVELS_IN_ROOM" for f in rep["findings"])
    unmarked = [r for r in rep["rooms"] if r["state"] == HELD and r["why"].startswith("UNLEVELLED_ROOM")]
    steps = []
    if st["how"] == "SINGLE_LEVEL" and not two:
        z = rep["zones"][0]
        for r in unmarked:
            if r["kind"] == STAIR:
                r["why"] = "STAIR_UNMARKED: a stair joins levels; it does not take the floor's level"
                continue
            r.update(state=FLOOR_LEVEL, level_m=z["level_m"], source=[dict(s) for s in z["source"]],
                     rule=Q43, why="FLOOR_LEVEL: floor level, not printed in the room (one level on this floor)")
            z.setdefault("rooms_by_rule", []).append(r["room_id"])
    elif st["how"] == "SPLIT_LEVEL":
        by_room = {}
        for d in drawn or ():
            if d.get("room_id") in recs and d.get("level_m") is not None and d.get("source"):
                by_room.setdefault(d["room_id"], []).append(d)
        for r in unmarked:
            ds = by_room.get(r["room_id"])
            if not ds:
                continue
            vals = _distinct(d["level_m"] for d in ds)
            if len(vals) == 1:
                r.update(state=DRAWN, level_m=vals[0], source=ds, rule=Q43,
                         why="DRAWN: the level read for this room on a drawing view (" +
                             ", ".join(sorted({str(d.get('kind')) for d in ds})) + ")")
            else:
                r.update(why=f"DRAWN_LEVELS_DISAGREE: {vals}", printed_levels_m=vals)
        changed = True
        while changed:
            changed = False
            for r in unmarked:
                if r["state"] != HELD or r["kind"] == STAIR or r["why"].startswith("DRAWN_LEVELS_DISAGREE"):
                    continue
                cand, reasons, seen = [], [], []
                for lk in links or ():
                    if r["room_id"] not in (lk.get("rooms") or ()):
                        continue
                    for other in lk["rooms"]:
                        o = recs.get(other)
                        if other == r["room_id"]:
                            continue
                        if o is None or o["state"] not in LEVELLED:
                            seen.append(f"{lk.get('opening_id')} to {other} (" +
                                        ("no level" if o is None or o["state"] == HELD else "not a room") + ")")
                            continue
                        if lk.get("doorway") == NONE_DRAWN:
                            cand.append((o["level_m"], lk["opening_id"], other, o["state"]))
                        else:
                            reasons.append(("DOORWAY_LINES_DRAWN" if lk.get("doorway") == LINES_DRAWN
                                            else "DOORWAY_NOT_READ") + f" at {lk.get('opening_id')} to {other}")
                vals = _distinct(c[0] for c in cand)
                if len(vals) == 1:
                    r.update(state=OPENS_INTO, level_m=vals[0], rule=Q43,
                             source=[{"opening_id": c[1], "room_id": c[2], "room_state": c[3], "level_m": c[0]}
                                     for c in cand],
                             why="OPENS_INTO: the level of the room it opens into; nothing is drawn across that "
                                 "doorway (no step, sill or head line)")
                    steps.append(r["room_id"])
                    changed = True
                elif len(vals) > 1:
                    r["why"] = f"OPENS_INTO_TWO_LEVELS: it opens into rooms at {vals}"
                    r["printed_levels_m"] = vals
                elif reasons:
                    r["why"] = "; ".join(sorted(set(reasons)))
                else:
                    r["why"] = ("NO_OPENING_TO_A_LEVELLED_ROOM: no opening joins it to a room with a level "
                                "(UNLEVELLED_ROOM)" + ("; openings: " + ", ".join(sorted(set(seen))) if seen else ""))
    for r in rep["rooms"]:
        if r["state"] in (FLOOR_LEVEL, DRAWN, OPENS_INTO):
            for z in rep["zones"]:
                if abs(z["level_m"] - r["level_m"]) <= AGREE_M and r["room_id"] not in z.get("rooms_by_rule", ()):
                    z.setdefault("rooms_by_rule", []).append(r["room_id"])
    st["rooms_held"] = sum(1 for r in rep["rooms"] if r["state"] == HELD)
    st["rooms_by_rule"] = {k: sum(1 for r in rep["rooms"] if r["state"] == k) for k in (FLOOR_LEVEL, DRAWN, OPENS_INTO)}
    rep["policy"] = policy_record_v2()
    rep["opens_into_order"] = steps
    return rep


def zone_of_v2(room, floor_report):
    """zone_of for every levelled state of V2 (PRINTED, FLOOR_LEVEL, DRAWN, OPENS_INTO); a HELD room stays HELD."""
    if room.get("state") not in LEVELLED:
        return {"state": HELD, "why": "ROOM_LEVEL_HELD: " + str(room.get("why"))}
    return zone_of(dict(room, state=PRINTED), floor_report)


def policy_record_v2():
    rec = policy_record()
    rec.update(policy_id=POLICY_ID_V2, extends="ROOM_LEVELS_V1",
               states=[PRINTED, FLOOR_LEVEL, DRAWN, OPENS_INTO, HELD, "NOT_A_FLOOR_ROOM"],
               held_reasons=rec["held_reasons"] + ["STAIR_UNMARKED", "OPENS_INTO_TWO_LEVELS", "DOORWAY_LINES_DRAWN",
                                                   "DOORWAY_NOT_READ", "NO_OPENING_TO_A_LEVELLED_ROOM",
                                                   "DRAWN_LEVELS_DISAGREE"],
               rules=rec["rules"] + [Q43],
               doorway={"tol_m": DOORWAY_TOL_M, "span_share": DOORWAY_SPAN_SHARE,
                        "states": [NONE_DRAWN, LINES_DRAWN, NOT_READ]})
    rec["never"] = [x for x in rec["never"] if not x.startswith("an unlevelled room")] + [
        "an unmarked room on a split floor given a level that nothing drawn supports",
        "a line across a doorway read as a step height"]
    return rec
