"""ARCH_TAKEOFF_V2.11 (board task T-079): ARCH_TAKEOFF_V2.10 + the verified waterproofing pieces wired into a method.

What V2.11 adds (knowledge registry 1.7.0 = 1.5.0 + the owner answers on wet areas, roofs and the membrane; every
other V2.10 quantity is unchanged):

1. Wet / dry evidence (WET_ROOM_EVIDENCE_V1, T-010; owner Q-06 a, Q-13 B, Q-30 A): every space is classed WET / DRY /
   HELD / NONE from its own label first, the drawn fixtures and drains second, the sanitary drawing (an optional
   project reading, never guessed) third. A space the V2.7.1 review holds under two plausible classifications
   (UP-REVIEW-001) is DECIDED when the evidence classes it WET or DRY: the scenario of that class is released for
   the space (its whole finish scope, measured by the scenario run), the conditional set is closed. HELD and NONE
   leave the review as it was. A space V2.10 waterproofs that the evidence does not class WET is flagged, never
   changed here.
2. The membrane table (MEMBRANE_FOLD_V2, T-076; owner Q-24 addendum, Q-30 example, Q-35 C): one row per wet area and
   per roof, the owner's strip method in both directions and from both start walls, the walls-only upturn, the door
   transitions and thresholds, the uncovered upturn of slanted walls; totals only as sums of the areas; one table per
   membrane system (wet areas, roofs), never a total across systems (UP-WP-MAT-001).
3. BOQ lines added (UP-QTY-STATUS-001: every line released, held or excluded, never 0 for a missing number):
   FIN.WP.DOORWAY_TRANSITION_NR  pcs, one per door of a wet area (a door between two wet areas once; Q-35 C)
   FIN.WP.ROOF                    m2, each roof inside its parapet (EXTERIOR_SPACES_V1, T-071; Q-24, Q-25, Q-29);
                                   a roof the drawing does not close is HELD with its reason
   FIN.WP.ROOF_UPTURN             lm, the 0.20 m upturn on the roof boundary and round each skylight opening
   FIN.WP.MEMBRANE_ROLLS          pcs per wet area and per roof, each ALONE (owner Q-49 A, T-093): of the four
                                   layouts (two strip directions x two start walls) the one with the fewest whole
                                   1.00 x 10.00 m rolls (tie: the shorter total strip length, then the smaller cut
                                   m2, then the listed order), with its cutting plan (every strip, which roll it is
                                   cut from), the leftover metres of full-width roll and the side trim; no offcut is
                                   carried from one area to another; the project total is the sum of the areas
                                   (the membrane table); a held area or roof has a held rolls line, never 0
   FIN.WP.FLOOR (held)            a space whose wet label shares a face with a dry one (no drawn wet-zone edge): HELD
   top roof (held, T-093)         the uppermost storey plan that has rooms has no plan drawn above it, so its roof
                                   outline is on no plan: FIN.WP.ROOF, FIN.WP.ROOF_UPTURN and FIN.WP.MEMBRANE_ROLLS
                                   BLOCKED_RFI (UP-WP-ROOF-001, owner Q-34 parked), no number, never 0
   The V2.10 wet-area lines (floor m2, walls-only upturn m2, doorway continuation) are not touched: on the areas V2.10
   measured they already equal the fold's floor and walls-only upturn (Q-35 C).

Never: a held area or roof as 0, rolls from net area / roll area, an offcut shared between areas, a roof outline
assumed, a gap limit assumed (the search reach is the engine's existing wall-thickness limit, arch_rooms.THIN_LIMIT_M).
Project-agnostic: no layer, room or project name is coded."""

from __future__ import annotations

import math
from collections import Counter
from contextlib import contextmanager

METHOD = "ARCH_TAKEOFF_V2.11"
POLICY_ID = "URBAN_BOQ_T079_ARCH_V2_11"
KNOWLEDGE = "1.7.0"
WET, DRY, HELD, NONE = "WET", "DRY", "HELD", "NONE"
SCENARIO_OF_CLASS = {WET: "WET_SCOPE", DRY: "DRY_SCOPE"}       # tools/urban_boq_m9.REVIEW_SCENARIOS names
CLASSED = ("ROOM", "UNLABELLED", "MIXED")                    # MERGED: a zone shared with its parent face
ITEMS = {
    "FIN.WP.DOORWAY_TRANSITION_NR": ("Doorway waterproofing transition, one per door (built to the detail)",
                                     "انتقال العازل عند باب المنطقة الرطبة (عدد)", "WATERPROOFING"),
    "FIN.WP.ROOF": ("Roof waterproofing membrane inside the parapet", "عازل السطح داخل الدروة", "WATERPROOFING"),
    "FIN.WP.ROOF_UPTURN": ("Roof waterproofing upturn 0.20 m (parapet, walls, skylight openings)",
                           "رفعة عازل السطح 20 سم", "WATERPROOFING"),
    "FIN.WP.BALCONY": ("Balcony / terrace waterproofing membrane", "عازل البلكونة / التراس", "WATERPROOFING"),
    "FIN.WP.MEMBRANE_ROLLS": ("Waterproofing membrane rolls to buy (1.00 x 10.00 m), each area alone",
                              "لفات العازل المطلوب شراؤها", "WATERPROOFING"),
    "FIN.WP.FLOOR": ("Wet-room floor waterproofing", "عازل أرضيات الحمامات", "WATERPROOFING"),
}
SYSTEMS = ("WET_AREAS", "ROOFS")
Q49_A = ("owner Q-49 A (2026-10-19 22:35; UP-WP-LAY-001): each wet area and each roof alone, laid in the layout "
         "(two strip directions x two start walls) that needs the fewest whole rolls; tie: the shorter total strip "
         "length, then the smaller cut m2, then the listed order; no offcut carried to another area")
START_LOWER, START_OPPOSITE = "LOWER_EDGE_OF_ROOM_FRAME", "OPPOSITE_EDGE_OF_ROOM_FRAME"
Q34 = ("ROOF_NOT_DRAWN_ON_ANY_PLAN (UP-WP-ROOF-001, owner Q-34 parked: held, no number, never 0)")


# ------------------------------------------------------------------------------------------------ capture
@contextmanager
def capture():
    """what arch_rooms.spaces sees per plan region (its entities, layer roles, the items of its first boundary
    arrangement and its result), read only, for the pieces that need the drawing itself (wet evidence, roof outlines).
    A later run of the same region replaces the earlier capture (the last run is the one whose lines are kept)."""
    from engine.source import arch_rooms as AR
    from engine.source import topology as TP
    cap, cur = {}, [None]
    o_spaces, o_build = AR.spaces, TP.build

    def spaces(ents, roles, unit_m, **kw):
        rid = kw.get("region_id")
        cur[0] = rid
        cap[rid] = {"builds": []}
        try:
            r = o_spaces(ents, roles, unit_m, **kw)
        finally:
            cur[0] = None
        cap[rid].update(ents=ents, roles=roles, unit_m=unit_m, res=r)
        return r

    def build(items, eps):
        if cur[0] is not None and not cap[cur[0]]["builds"]:
            cap[cur[0]]["builds"].append(list(items))
        return o_build(items, eps)
    AR.spaces, TP.build = spaces, build
    try:
        yield cap
    finally:
        AR.spaces, TP.build = o_spaces, o_build


# ------------------------------------------------------------------------------------------------ wet / dry
def wet_classes(rooms, cap, sanitary_by_room=None):
    """WET_ROOM_EVIDENCE_V1 on every classed space: {room_id: record}. sanitary_by_room: {room_id: [kind, ...]} read
    from the sanitary drawing (a project input with its source); a room missing from it has no sanitary reading
    (None), never an empty one."""
    from engine.source import arch_rooms as AR
    from engine.source import wet_room_evidence as W
    out = {}
    for r in rooms:
        if r["class"] not in CLASSED:
            continue
        c = cap.get(r.get("region_id")) or {}
        if "ents" not in c:
            out[r["room_id"]] = {"class": HELD, "reason": "REGION_NOT_CAPTURED", "basis": "the plan region's "
                                 "entities were not read: no evidence", "flags": [], "coordination_checks": []}
            continue
        geo = None
        if r["codes"] and r.get("label_source") not in ("TEXT",) and \
                all(AR.LEX[x][2] in W.NO_FINISH_KINDS for x in r["codes"]):
            geo = AR.LEX[r["codes"][0]][2]                         # stair / shaft typed from geometry
        ev = W.plan_evidence(r["polygon"], c["ents"], c["roles"], c["unit_m"], r.get("hole_polygons") or ())
        san = None
        if sanitary_by_room is not None and r["room_id"] in sanitary_by_room:
            san = [{"kind": k} for k in sanitary_by_room[r["room_id"]]]
        rec = W.classify(ev, san, space_kind=geo)
        out[r["room_id"]] = {"class": rec["class"], "reason": rec["reason"], "basis": rec["basis"],
                             "rules": rec.get("rules"), "flags": rec["flags"],
                             "coordination_checks": rec["coordination_checks"], "labels": ev["labels"]["codes"],
                             "plan_fixtures": sorted({x["kind"] for x in ev["fixtures"]}),
                             "plan_drains": sorted({x["kind"] for x in ev["drains"]}),
                             "sanitary_drawing": None if san is None else sorted(x["kind"] for x in san)}
    return out


def decide_review(targets, classes):
    """{room_id: scenario name} for the review spaces whose evidence classes them WET or DRY (UP-REVIEW-001 closed by
    WET_ROOM_EVIDENCE_V1); a HELD / NONE space stays in review."""
    out = {}
    for tg in targets:
        if not tg.get("plausible"):
            continue
        c = (classes.get(tg["room_id"]) or {}).get("class")
        names = {p["scenario"] for p in tg["plausible"]}
        if c in SCENARIO_OF_CLASS and SCENARIO_OF_CLASS[c] in names:
            out[tg["room_id"]] = SCENARIO_OF_CLASS[c]
    return out


def decided_release(targets, decided, scen):
    """the lines a decided review space takes: its own finish lines (FIN.*) of the chosen scenario run, keyed like the
    V2.7.1 release {(floor, face_id): [line]}; a space whose scenario run failed is not decided. -> (release,
    {room_id: scenario})"""
    rel, done = {}, {}
    for tg in targets:
        name = decided.get(tg["room_id"])
        if name is None or not scen.get(name):
            continue
        # the space's own finish lines; of the waterproofing only the floor line: the final run's waterproofing
        # system schedules every area that has one and writes the area's other membrane lines itself
        mine = [ln for ln in scen[name]["lines"] if (ln.get("location") or {}).get("room_id") == tg["room_id"]
                and ln["item_code"].startswith("FIN.") and
                (not ln["item_code"].startswith("FIN.WP.") or ln["item_code"] == "FIN.WP.FLOOR")]
        rel[(tg["floor"], tg["face_id"])] = mine
        done[tg["room_id"]] = name
    return rel, done


# ------------------------------------------------------------------------------------------------ membrane table
def _doors_of(room, arch):
    ops = {(o["floor"], o["opening_id"]): o for o in arch.get("openings") or ()}
    out = [{"opening_id": d, "width_m": ops[(room["floor"], d)]["width_m"]} for d in room.get("doors") or ()
           if (room["floor"], d) in ops]
    # a door the opening census did not list (a door closure: leaf drawn wall to wall) is a door element with no
    # opening id; its sides name the rooms, so it is one door, identified by its element id
    for e in (arch.get("doors") or {}).get("elements") or ():
        if e.get("opening_id") is None and e.get("floor") == room["floor"] and \
                any(sd.get("room_id") == room["room_id"] for sd in e.get("sides") or ()):
            out.append({"opening_id": e["element_id"], "width_m": e.get("structural_opening_width_m")})
    return out


def wet_rows(arch, classes):
    """one MEMBRANE_FOLD_V2 row per WET space (the waterproofing schedule's typed ring when V2.10 scheduled it, else
    the room's boundary runs), plus the flags where V2.10's schedule and the evidence differ."""
    from engine.source import membrane_fold_v2 as F
    typed = {(w["floor"], w["room_id"]): w["upturn"]["by_role_lm"]
             for w in (arch.get("waterproofing") or {}).get("areas") or ()}
    rows, flags = [], []
    for r in arch["rooms"]:
        c = (classes.get(r["room_id"]) or {}).get("class")
        sched = (r["floor"], r["room_id"]) in typed
        if c != WET:
            if sched:
                flags.append({"floor": r["floor"], "room_id": r["room_id"], "flag": "V2_10_SCHEDULE_NOT_WET_BY_EVIDENCE",
                              "evidence_class": c, "note": "V2.10 waterproofs it; the evidence does not class it WET: "
                                                           "its V2.10 lines are kept, the table does not count it"})
            continue
        roles = typed.get((r["floor"], r["room_id"]))
        rl = r.get("runs_lm")
        if roles is None and rl:
            roles = {k: rl.get(k, 0.0) for k in F.ELIGIBLE + F.THRESHOLD_ROLES + ("door",)}
        row = F.area(floor=r["floor"], room_id=r["room_id"], name="/".join(r["codes"]) or "(no label)",
                     polygon=r["polygon_m"], holes=r.get("hole_polygons_m") or (), roles_lm=roles,
                     doors=_doors_of(r, arch))
        row.update(system="WET_AREAS", name_en=r.get("name_en"), name_ar=r.get("name_ar"),
                   roles_source="WATERPROOFING_SCHEDULE typed ring" if sched else "room boundary runs",
                   evidence=classes[r["room_id"]]["reason"])
        rows.append(row)
    return rows, flags


def held_wet(arch, classes):
    """spaces whose label names a wet function beside a dry one in one face (no drawn wet-zone edge): HELD rows."""
    out = []
    for r in arch["rooms"]:
        c = classes.get(r["room_id"]) or {}
        if c.get("class") == HELD and c.get("reason") == "WET_ZONE_EXTENT_NOT_DRAWN":
            out.append({"floor": r["floor"], "room_id": r["room_id"], "name_en": r.get("name_en"),
                        "name_ar": r.get("name_ar"), "codes": list(r["codes"]), "reason": c["reason"],
                        "basis": c["basis"], "area_of_whole_face_m2": round(r["area_m2"], 4)})
    return out


def roof_records(cap, floor_of, facts=None):
    """EXTERIOR_SPACES_V1 on every exterior label the room-label guard holds, per captured plan region, with the
    fold of each released roof / balcony face."""
    from engine.source import exterior_spaces as XS
    from engine.source import membrane_fold_v2 as F
    from engine.source import room_label_guard as G
    out = []
    for rid, c in sorted(cap.items(), key=lambda kv: str(kv[0])):
        if "ents" not in c or not c["builds"]:
            continue
        faces = [{"face_id": f.get("face_id"), "polygon": f["polygon"], "hole_polygons": f.get("hole_polygons") or ()}
                 for f in (c["res"].get("faces") or ()) if f.get("polygon")]
        texts = c["ents"].get("texts") or []
        g = G.guard(faces, texts, frame=rid, unit_m=c["unit_m"])
        held = {x["text_id"] for x in g["held"]}
        labels = [t for t in texts if t["id"] in held]
        building, layers, openings, _t = XS.inputs_from_spaces(c["ents"], c["roles"], c["builds"][0], c["res"])
        tr = XS.trace(labels, building, layers, c["unit_m"], openings=openings, facts=facts, frame=rid, texts=texts)
        for rec in tr["records"]:
            if rec.get("code") not in ("ROOF", "BALCONY"):
                continue
            row = {"region": rid, "floor": floor_of.get(rid, rid), "text_id": rec.get("text_id"),
                   "code": rec["code"], "status": rec["status"], "reason": rec.get("reason"),
                   "basis": rec.get("basis"), "membrane_m2": rec.get("membrane_m2"), "upturn_lm": rec.get("upturn_lm"),
                   "upturn_round_openings_lm": rec.get("upturn_round_openings_lm"),
                   "held_part_m2": rec.get("held_part_m2"), "held_part_reason": rec.get("held_part_reason"),
                   "counted_with": rec.get("counted_with"), "gap_cover": rec.get("gap_cover") or [],
                   "layer": rec.get("layer"), "fold": None}
            lay = rec.get("layer")
            face = (rec["candidates"].get(lay) or {}).get("face_du") if lay else None
            if face is not None and not rec.get("counted_with") and rec.get("membrane_m2") is not None:
                a = F.area(floor=row["floor"], room_id=f"{rid}:{rec.get('text_id')}", polygon=list(face.exterior.coords),
                           holes=[list(h.coords) for h in face.interiors], unit_m=c["unit_m"],
                           name=rec["code"])
                a.update(system="ROOFS" if rec["code"] == "ROOF" else "BALCONIES",
                         line_room_id=f"{row['floor']}-{rec['code']}-{rec.get('text_id')}")   # = roof_lines' room id
                row["fold"] = a
            out.append(row)
    return out


def _splice(Ls, L, lap):
    """the pieces of one strip of length Ls cut from rolls of length L (a longer strip is spliced with the end lap,
    exactly as MEMBRANE_FOLD_V2.strips does)."""
    if Ls <= L + 1e-9:
        return [round(Ls, 6)]
    k = math.ceil((Ls - L) / (L - lap) - 1e-9) + 1
    return [round(x, 6) for x in [L] * (k - 1) + [Ls - (k - 1) * (L - lap)]]


def layouts(fold):
    """the four layouts MEMBRANE_FOLD_V2 computes for one area: each strip direction laid from the lower and from the
    opposite wall of the room frame. -> [{direction, start, strips [(width, length)], rolls_if_alone,
    roll_length_used_m, cut_m2, upturn_shortfall_m2}] in the listed order (along-lower, along-opposite, across-lower,
    across-opposite)."""
    out = []
    for o in fold["directions"]:
        out.append({"direction": o["direction"], "start": START_LOWER,
                    "strips": [(s["width_m"], s["length_m"]) for s in o["strip_list"]],
                    **{k: o[k] for k in ("rolls_if_alone", "roll_length_used_m", "cut_m2", "upturn_shortfall_m2")}})
        h = o["other_start"]
        out.append({"direction": o["direction"], "start": START_OPPOSITE, "strips": [tuple(x) for x in h["strip_list"]],
                    **{k: h[k] for k in ("rolls_if_alone", "roll_length_used_m", "cut_m2", "upturn_shortfall_m2")}})
    return out


def purchase(fold):
    """owner Q-49 A for one area alone: the layout with the fewest whole rolls (tie: shorter total strip length, then
    smaller cut m2, then the listed order), its cutting plan (each roll: the strips cut from it and the metres left),
    the leftover metres of full-width roll (rolls x roll length - strip length) and the side trim (strip length x roll
    width - cut m2). The cutting plan is packed again from the chosen strips and must give the fold's own count."""
    from engine.source import membrane_layout as ML
    sp = fold["spec"]
    W, L, lap = sp["roll_width_m"], sp["roll_length_m"], sp["lap_m"]
    cands = layouts(fold)
    order = {id(c): i for i, c in enumerate(cands)}
    best = min(cands, key=lambda c: (c["rolls_if_alone"], round(c["roll_length_used_m"], 4), round(c["cut_m2"], 4),
                                     order[id(c)]))
    pieces = []
    for i, (w, ln) in enumerate(best["strips"], 1):
        ps = _splice(ln, L, lap)
        for j, x in enumerate(ps, 1):
            pieces.append({"strip": i, "piece": j, "of": len(ps), "width_m": w, "length_m": x})
    bins, packing = ML.pack_rolls([x["length_m"] for x in pieces], L)
    if len(bins) != best["rolls_if_alone"]:
        raise ValueError(f"cutting plan gives {len(bins)} rolls, the fold {best['rolls_if_alone']}")
    used = sum(x["length_m"] for x in pieces)
    if abs(used - best["roll_length_used_m"]) > 1e-3:
        raise ValueError("the chosen strips do not add up to the fold's roll length")
    plan = []
    for k, b in enumerate(sorted(bins, key=lambda b: min(b)), 1):
        cut = [pieces[i] for i in sorted(b, key=lambda i: (-pieces[i]["length_m"], i))]
        u = sum(x["length_m"] for x in cut)
        plan.append({"roll": k, "pieces": [dict(x) for x in cut], "used_m": round(u, 4), "left_m": round(L - u, 4)})
    rolls = len(bins)
    flags = []
    leftover = rolls * L - used
    patch = None
    if best["upturn_shortfall_m2"]:
        # the upturn the chosen strips do not reach (a slanted wall) is shown in m2, never patched by an assumed piece;
        # the check says only whether this area's own leftover of full-width roll holds at least that area of sheet
        # (laps of a patch are by detail and not counted)
        flags.append("CHOSEN_LAYOUT_UPTURN_SHORTFALL")
        patch = {"uncovered_m2": best["upturn_shortfall_m2"], "leftover_sheet_m2": round(leftover * W, 4),
                 "leftover_holds_it": leftover * W + 1e-9 >= best["upturn_shortfall_m2"],
                 "note": "patch pieces by detail, cut from this area's leftover when it holds them; laps not counted"}
        if not patch["leftover_holds_it"]:
            flags.append("UPTURN_SHORTFALL_EXCEEDS_LEFTOVER")
    if any(c["rolls_if_alone"] < rolls for fr in fold.get("other_frames") or () for c in fr["directions"]):
        flags.append("ANOTHER_WALL_FRAME_NEEDS_FEWER_ROLLS")       # shown, never selected (not one of the four)
    if not packing.get("proven", True):
        flags.append("PACKING_NOT_PROVEN_MINIMAL")
    return {"rule": Q49_A, "direction": best["direction"], "start": best["start"], "strips": len(best["strips"]),
            "rolls": rolls, "strip_length_m": round(used, 4), "cut_m2": round(best["cut_m2"], 4),
            "leftover_m": round(leftover, 4), "side_trim_m2": round(used * W - best["cut_m2"], 4),
            "upturn_shortfall_m2": best["upturn_shortfall_m2"], "shortfall_check": patch, "cutting_plan": plan,
            "roll": {"width_m": W, "length_m": L, "lap_m": lap},
            "layouts": [{k: c[k] for k in ("direction", "start", "rolls_if_alone", "roll_length_used_m", "cut_m2",
                                           "upturn_shortfall_m2")} for c in cands], "flags": flags}


PURCHASE_COLUMNS = ("system", "floor", "room_id", "name", "state", "floor_m2", "layout", "strips", "cutting_plan",
                    "rolls", "strip_length_m", "cut_m2", "leftover_m", "side_trim_m2", "reason")


def purchase_rows(table):
    """the owner's purchase table, one row per wet area / roof (each alone, Q-49 A), each held area with its reason
    (rolls empty, never 0), then one total row per system (the sum of the areas; never a total across systems)."""
    out = []
    for name in SYSTEMS:
        st = table["systems"].get(name) or {}
        for r in st.get("rows") or ():
            p = r.get("purchase")
            if p is None:
                continue
            plan = " | ".join(f"roll {x['roll']}: " + " + ".join(f"{q['width_m']:.2f}x{q['length_m']:.2f}"
                                                                   for q in x["pieces"]) + f", {x['left_m']:.2f} m left"
                              for x in p["cutting_plan"])
            out.append({"system": name, "floor": r["floor"], "room_id": r["room_id"], "name": r.get("name"),
                        "state": "RELEASED", "floor_m2": r["floor_m2"], "layout": f"{p['direction']} / {p['start']}",
                        "strips": p["strips"], "cutting_plan": plan, "rolls": p["rolls"],
                        "strip_length_m": p["strip_length_m"], "cut_m2": p["cut_m2"], "leftover_m": p["leftover_m"],
                        "side_trim_m2": p["side_trim_m2"], "reason": ";".join(p["flags"])})
        for h in st.get("held") or ():
            out.append({"system": name, "floor": h["floor"], "room_id": h["room_id"], "name": h["name"],
                        "state": "HELD", "reason": h["reason"]})
        t = st.get("purchase_total")
        if t:
            out.append({"system": name, "room_id": "TOTAL", "state": "SUM_OF_AREAS" if t["complete"] else
                        "SUM_OF_RELEASED_AREAS_HELD_EXCLUDED", "rolls": t["rolls_to_buy"],
                        "strip_length_m": t["strip_length_m"], "cut_m2": t["cut_m2"], "leftover_m": t["leftover_m"],
                        "side_trim_m2": t["side_trim_m2"], "reason": t["note"]})
    return out


def top_roofs(arch):
    """the roof over the uppermost storey plan: when that plan has rooms, no plan is drawn above it, so its roof
    outline is on no plan (a plan's roof labels are roofs BELOW it). -> [{floor, region, level_m,
    floor_above_level_m, rooms, plate_m2}] (one or none). A plan region with no level and no known floor order is
    not placed: then nothing is claimed. Project-agnostic: the storey order is the bound level, else the floor-title
    order of arch_plan.FLOOR_TITLES."""
    from engine.source import arch_plan as AP
    regs = arch.get("regions") or ()
    order = {fl: o for fl, o, _p in AP.FLOOR_TITLES}
    if not regs:
        return []
    if all(r.get("level_m") is not None for r in regs):
        key = lambda r: (r["level_m"], order.get(r["floor"], -1))
    elif all(r["floor"] in order for r in regs):
        key = lambda r: order[r["floor"]]
    else:
        return []
    top = max(regs, key=key)
    peers = [r for r in regs if key(r) == key(top)]
    if len(peers) > 1:                                   # two plans at the top level: which one is the top is unknown
        return []
    rooms = [r["room_id"] for r in arch.get("rooms") or () if r.get("region_id") == top["region_id"]
             and r["class"] == "ROOM"]
    if not rooms:                                        # a roof plan with no rooms draws its roofs itself
        return []
    return [{"floor": top["floor"], "region": top["region_id"], "level_m": top.get("level_m"),
             "floor_above_level_m": top.get("floor_above_level_m"), "rooms": sorted(rooms),
             "plate_m2": (top.get("plate") or {}).get("largest_m2")}]


def membrane_table(wet, roofs, held=(), top=()):
    """the owner's membrane purchase table: per system the per-area rows, the purchase of each area alone (owner Q-49
    A) and its project total as the sum of the areas, the held areas named with their reason (never 0), and, for
    information only, MEMBRANE_FOLD_V2.project (offcuts shared between areas: NOT the purchase)."""
    from engine.source import membrane_fold_v2 as F
    systems = {}
    roof_rows = [r["fold"] for r in roofs if r["fold"] is not None and r["code"] == "ROOF"]
    held_by = {"WET_AREAS": [{"floor": h["floor"], "room_id": h["room_id"], "name": "/".join(h["codes"]),
                              "reason": h["reason"]} for h in held],
               "ROOFS": [{"floor": r["floor"], "room_id": f"{r['floor']}-ROOF-{r['text_id']}", "name": "ROOF",
                          "reason": r["reason"]} for r in roofs
                         if r["code"] == "ROOF" and r["membrane_m2"] is None and not r.get("counted_with")]
               + [{"floor": t["floor"], "room_id": f"{t['floor']}-ROOF-TOP", "name": "top roof", "reason": Q34}
                  for t in top]}
    for name, rows in (("WET_AREAS", wet), ("ROOFS", roof_rows)):
        out_rows, buy, hl = [], [], list(held_by[name])
        for x in rows:
            tr = _table_row(x)
            if x.get("fold") is not None:
                tr["purchase"] = purchase(x["fold"])
                buy.append(tr)
            else:
                hl.append({"floor": x["floor"], "room_id": x["room_id"], "name": x.get("name"),
                           "reason": x.get("reason")})
            out_rows.append(tr)
        total = None
        if buy:
            total = {"areas": len(buy), "rolls_to_buy": sum(r["purchase"]["rolls"] for r in buy),
                     "cut_m2": round(sum(r["purchase"]["cut_m2"] for r in buy), 4),
                     "strip_length_m": round(sum(r["purchase"]["strip_length_m"] for r in buy), 4),
                     "leftover_m": round(sum(r["purchase"]["leftover_m"] for r in buy), 4),
                     "side_trim_m2": round(sum(r["purchase"]["side_trim_m2"] for r in buy), 4),
                     "held_areas": len(hl), "complete": not hl,
                     "note": "sum of the areas, each alone (owner Q-49 A)" + (
                         "; held areas are not in the sum (each has its held rolls line)" if hl else "")}
        systems[name] = {"rows": out_rows, "held": hl, "purchase_total": total,
                         "project": F.project(rows) if rows else None,
                         "project_note": "MEMBRANE_FOLD_V2.project packs offcuts across areas: information only, "
                                         "not the purchase (owner Q-49 A: each area alone)"}
    return {"policy": F.METHOD_ID, "purchase_rule": Q49_A, "systems": systems,
            "never": ["a total across membrane systems (UP-WP-MAT-001)", "a held area as 0",
                      "an offcut carried from one area to another (owner Q-49 A)",
                      "rolls from net area / roll area (UP-WP-001)"]}


def _table_row(x):
    f = x.get("fold")
    base = {"system": x.get("system"), "floor": x["floor"], "room_id": x["room_id"], "name": x.get("name"),
            "state": x["state"], "line_room_id": x.get("line_room_id") or x["room_id"]}
    if f is None:
        return dict(base, reason=x.get("reason"))
    ln = x["lines"]
    return dict(base, floor_m2=f["floor_m2"], boundary_lm=f["boundary_lm"], shape=f["shape"], flags=f["flags"],
                upturn_walls_lm=ln["upturn"]["lm"], door_transitions=[t["opening_id"] for t in ln["door_transitions"]],
                thresholds=ln["thresholds"], internal_corners=f["internal_corners"],
                directions=[{"direction": o["direction"], "strips": o["strips"], "cut_m2": o["cut_m2"],
                             "roll_length_used_m": o["roll_length_used_m"], "rolls_if_alone": o["rolls_if_alone"],
                             "rolls_by_cut_area": o["rolls_by_cut_area"], "upturn_shortfall_m2": o["upturn_shortfall_m2"],
                             "other_start_cut_m2": o["other_start"]["cut_m2"],
                             "other_start_rolls": o["other_start"]["rolls_if_alone"]} for o in f["directions"]])


# ------------------------------------------------------------------------------------------------ BOQ lines
def _line(ctx, *, item_code, unit, floor, room_id, element, ev, net=None, formula, inputs, rule_id, name_en=None,
          name_ar=None, bounded=None, rfi=None, notes=""):
    from engine.source import boq_line as BL
    from engine.source import knowledge as K
    en, ar, tr = ITEMS[item_code]
    with K.using(KNOWLEDGE):                    # the rule as registry 1.7.0 records it, whatever registry is active
        ref = K.ref(rule_id)
    return BL.make_line(project_id=ctx["project_id"], revision_set_sha256=ctx["revision_set_sha256"],
                        item_code=item_code, unit=unit, evidence_state=ev,
                        measured_net=net if ev in BL.QUANTITY_STATES else None, element_id=f"{room_id}:{element}",
                        floor=floor, room_id=room_id, room_name_en=name_en, room_name_ar=name_ar,
                        physical_element=element, formula=formula, inputs=inputs, documents=ctx["documents"],
                        geometry_source="CAD_VECTOR",
                        geometry_confidence="EXACT_FACE" if ev in BL.QUANTITY_STATES else "NOT_ESTABLISHED",
                        rule_id=ref["rule_id"], rule_version=ref["version"], rule_set=ref["rule_set"],
                        rule_set_digest=ref["rule_set_digest"], rfi=rfi, notes=notes, bounded_range=bounded,
                        item_en=en, item_ar=ar, trade=tr)


def door_transition_lines(ctx, wet, names):
    """one line per door of a wet area (Q-35 C); a door shared by two wet areas once (the first area in floor / room
    order carries it, the other is named); a door edge the opening census did not list is held."""
    out, seen = [], {}
    for x in sorted(wet, key=lambda r: (str(r["floor"]), str(r["room_id"]))):
        if x["state"] != "COMPUTED":
            continue
        for t in x["lines"]["door_transitions"]:
            if t["opening_id"] is None:
                q = (f"DOOR_EDGE_WITHOUT_OPENING_ID (UP-WP-DOOR-001, Q-35 C): a {t['width_m']} m door edge on the "
                     "wet area's ring that the opening census did not list; the count is held (it may be a "
                     "neighbour's door)")
                out.append(_line(ctx, item_code="FIN.WP.DOORWAY_TRANSITION_NR", unit="pcs", floor=x["floor"],
                                 room_id=x["room_id"], element="wp_door_transition:unlisted", ev="BLOCKED_RFI",
                                 formula="one per door, built to the waterproofing detail",
                                 inputs={"width_m": t["width_m"]}, rule_id="UP-WP-003",
                                 rfi={"question": q, "unlocks": x["room_id"]}, **names(x)))
                continue
            k = (x["floor"], t["opening_id"])
            if k in seen:
                seen[k]["inputs"]["wet_areas"].append(x["room_id"])
                continue
            ln = _line(ctx, item_code="FIN.WP.DOORWAY_TRANSITION_NR", unit="pcs", floor=x["floor"],
                       room_id=x["room_id"], element=f"wp_door_transition:{t['opening_id']}", ev="SOURCE_DERIVED",
                       net=1, formula="one transition per door of the wet area (owner Q-35 C); a door between two "
                                      "wet areas once; built to the waterproofing detail (UP-WP-DOOR-001)",
                       inputs={"opening_id": t["opening_id"], "width_m": t["width_m"], "wet_areas": [x["room_id"]]},
                       rule_id="UP-WP-003", **names(x))
            seen[k] = ln["calculation"]
            out.append(ln)
    return out


def roof_lines(ctx, roofs):
    """FIN.WP.ROOF (m2) and FIN.WP.ROOF_UPTURN (lm) per traced roof; a balcony membrane PROVISIONAL (UP-WP-ROOF-001),
    its upturn held; a roof / balcony not closed by the drawing HELD with its reason; a label counted with another
    record of the same face carries no line (the other record does)."""
    out = []
    for r in roofs:
        if r.get("counted_with"):
            continue
        rid = f"{r['floor']}-{r['code']}-{r['text_id']}"
        nm = {"name_en": "Roof" if r["code"] == "ROOF" else "Balcony / terrace", "name_ar": None}
        item = "FIN.WP.ROOF" if r["code"] == "ROOF" else "FIN.WP.BALCONY"
        inp = {"region": r["region"], "layer": r["layer"], "label": r["text_id"], "status": r["status"],
               "gaps_closed": r["gap_cover"], "upturn_round_openings_lm": r["upturn_round_openings_lm"]}
        if r["membrane_m2"] is None:
            q = f"{r['reason']} ({r['code']}, EXTERIOR_SPACES_V1): {r['basis']}"
            out.append(_line(ctx, item_code=item, unit="m2", floor=r["floor"], room_id=rid, element="wp_membrane",
                             ev="BLOCKED_RFI", formula="membrane inside the parapet (owner Q-24)", inputs=inp,
                             rule_id="UP-WP-ROOF-001", rfi={"question": q, "unlocks": rid}, **nm))
            continue
        ev = "SOURCE_DERIVED" if r["code"] == "ROOF" else "PROVISIONAL"
        out.append(_line(ctx, item_code=item, unit="m2", floor=r["floor"], room_id=rid, element="wp_membrane", ev=ev,
                         net=r["membrane_m2"], formula="the area inside the parapet's inner face, every drafting gap "
                         "closed and listed (owner Q-24, Q-25); skylight openings left out (Q-29)", inputs=inp,
                         rule_id="UP-WP-ROOF-001", **nm))
        if r["code"] == "ROOF":
            out.append(_line(ctx, item_code="FIN.WP.ROOF_UPTURN", unit="lm", floor=r["floor"], room_id=rid,
                             element="wp_upturn", ev="SOURCE_DERIVED", net=r["upturn_lm"],
                             formula="0.20 m upturn on the whole boundary inside the parapet (parapet, walls, gap "
                                     "closures) + round each skylight opening (owner Q-24, Q-29; UP-WP-003)",
                             inputs=dict(inp, upturn_h_m=0.20), rule_id="UP-WP-ROOF-001", **nm))
        if r["held_part_m2"]:
            q = (f"{r['held_part_reason']} (EXTERIOR_SPACES_V1): a closed shape inside the roof is neither an opening "
                 "nor a membrane-under area by any label or project fact")
            out.append(_line(ctx, item_code=item, unit="m2", floor=r["floor"], room_id=rid, element="wp_membrane:held",
                             ev="BOUNDED_EXPOSURE", formula="the unidentified inner shape's area (shown, held)",
                             inputs=inp, rule_id="UP-WP-ROOF-001",
                             bounded={"low": 0.0, "high": r["held_part_m2"], "basis": q},
                             rfi={"question": q, "unlocks": rid}, **nm))
    return out


def rolls_lines(ctx, table, names=None):
    """owner Q-49 A: one FIN.WP.MEMBRANE_ROLLS line per wet area and per roof, each alone (the purchase of the table
    row: rolls, cutting plan, leftover metres); one BLOCKED_RFI line per held area or roof (no number, never 0)."""
    out = []
    for name in SYSTEMS:
        st = table["systems"].get(name) or {}
        for r in st.get("rows") or ():
            p = r.get("purchase")
            if p is None:
                continue
            rid = r["line_room_id"]
            nm = (names or {}).get((r["floor"], r["room_id"])) or {}
            out.append(_line(ctx, item_code="FIN.WP.MEMBRANE_ROLLS", unit="pcs", floor=r["floor"], room_id=rid,
                             element="wp_rolls_to_buy", ev="SOURCE_DERIVED", net=p["rolls"],
                             formula="this area alone: of the four layouts (2 directions x 2 start walls) the one "
                                     "with the fewest whole 1.00 x 10.00 m rolls, tie the shorter strip length (owner "
                                     "Q-49 A); strips by the owner's method (Q-30, Q-24 addendum), packed by length "
                                     "into whole rolls (UP-WP-001), never area / roll area",
                             inputs={"system": name, "direction": p["direction"], "start": p["start"],
                                     "strips": p["strips"], "strip_length_m": p["strip_length_m"],
                                     "cut_m2": p["cut_m2"], "leftover_m": p["leftover_m"],
                                     "side_trim_m2": p["side_trim_m2"], "cutting_plan": p["cutting_plan"],
                                     "layouts": p["layouts"], "flags": p["flags"]},
                             rule_id="UP-WP-LAY-001", name_en=nm.get("name_en"), name_ar=nm.get("name_ar")))
        for h in st.get("held") or ():
            q = (f"{h['reason']}: the area's outline is not established, so its membrane rolls are not counted "
                 "(owner Q-49 A counts each area alone; this one is held, not 0)")
            out.append(_line(ctx, item_code="FIN.WP.MEMBRANE_ROLLS", unit="pcs", floor=h["floor"],
                             room_id=h["room_id"], element="wp_rolls_to_buy", ev="BLOCKED_RFI",
                             formula="this area alone (owner Q-49 A)", inputs={"system": name, "name": h["name"]},
                             rule_id="UP-WP-LAY-001", rfi={"question": q, "unlocks": h["room_id"]}))
    return out


def top_roof_lines(ctx, top):
    """FIN.WP.ROOF, FIN.WP.ROOF_UPTURN held for the roof that no plan draws (owner Q-34 parked). Its rolls line is
    written by rolls_lines from the table's held rows."""
    out = []
    for t in top:
        rid = f"{t['floor']}-ROOF-TOP"
        q = (f"{Q34}: storey {t['floor']} (level {t['level_m']}) is the uppermost plan and has rooms; no plan is drawn "
             "above it, so its roof outline (and parapet) is on no plan; the designer's roof plan unlocks it")
        inp = {"storey": t["floor"], "region": t["region"], "storey_level_m": t["level_m"],
               "level_above_m": t["floor_above_level_m"], "rooms_below": t["rooms"],
               "storey_plate_outside_walls_m2": t["plate_m2"],
               "note": "the storey plate is shown for information; it is not the roof area (no outline drawn)"}
        for item, unit, el in (("FIN.WP.ROOF", "m2", "wp_membrane"), ("FIN.WP.ROOF_UPTURN", "lm", "wp_upturn")):
            out.append(_line(ctx, item_code=item, unit=unit, floor=t["floor"], room_id=rid, element=el,
                             ev="BLOCKED_RFI", formula="membrane inside the parapet (owner Q-24): outline not drawn",
                             inputs=inp, rule_id="UP-WP-ROOF-001", rfi={"question": q, "unlocks": rid},
                             name_en="Top roof (no plan)", name_ar=None))
    return out


def held_wet_lines(ctx, held, existing):
    """FIN.WP.FLOOR held for a wet label sharing a face with a dry one, unless the run already has a FIN.WP.FLOOR
    line at that space."""
    out = []
    for h in held:
        if (h["room_id"], "FIN.WP.FLOOR") in existing:
            continue
        q = (f"WET_ZONE_EXTENT_NOT_DRAWN (UP-WET-001, owner Q-37 / Q-13): {h['basis']}; the wet zone needs its drawn "
             "edge or its printed size as a project data value")
        out.append(_line(ctx, item_code="FIN.WP.FLOOR", unit="m2", floor=h["floor"], room_id=h["room_id"],
                         element="wp_floor:wet_zone", ev="BLOCKED_RFI", formula="the wet zone's floor",
                         inputs={"codes": h["codes"], "area_of_whole_face_m2": h["area_of_whole_face_m2"]},
                         rule_id="UP-WET-001", rfi={"question": q, "unlocks": h["room_id"]},
                         name_en=h["name_en"], name_ar=h["name_ar"]))
    return out


def summary(classes, decided, wet, flags, held, roofs, table, lines):
    return {"classes": dict(Counter(c["class"] for c in classes.values())),
            "review_spaces_decided": dict(sorted(decided.items())),
            "wet_areas": len(wet), "wet_areas_computed": sum(1 for x in wet if x["state"] == "COMPUTED"),
            "wet_schedule_flags": flags, "wet_zones_held": [h["room_id"] for h in held],
            "roofs": [{k: r[k] for k in ("floor", "code", "status", "reason", "membrane_m2", "upturn_lm",
                                         "counted_with")} for r in roofs],
            "purchase": {k: {"total": v["purchase_total"], "held": [h["room_id"] for h in v["held"]]}
                         for k, v in table["systems"].items()},
            "offcuts_shared_information_only": {k: (v["project"] or {}).get("direction_sets")
                                                for k, v in table["systems"].items()},
            "lines_added": dict(Counter(f"{ln['item_code']} [{ln['evidence_state']}]" for ln in lines))}


def policy_record():
    return {"method": METHOD, "policy": POLICY_ID, "knowledge": KNOWLEDGE,
            "pieces": ["WET_ROOM_EVIDENCE_V1 (T-010)", "EXTERIOR_SPACES_V1 (T-071)", "MEMBRANE_FOLD_V2 (T-076)"],
            "owner_answers": ["Q-06 a", "Q-13 B", "Q-24", "Q-25", "Q-29", "Q-30 A", "Q-34 parked", "Q-35 C",
                              "Q-37 A", "Q-40 A", "Q-49 A"],
            "purchase_rule": Q49_A, "open": [], "items": sorted(ITEMS)}
