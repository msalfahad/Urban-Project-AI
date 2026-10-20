"""ARCH_TAKEOFF_V2.13 (board task T-120; opt-in, NOT the released default): ARCH_TAKEOFF_V2.12 + two membrane purchase
changes the owner answered, each released only when the drawing or the cutting plan itself proves it.

V2.12 (engine/source/arch_v212.py, never edited) counts the rolls of each wet area and roof alone (owner Q-49 A) on the
MEMBRANE_FOLD_V3 strips and HOLDS an area whose fewest rolls differ between the three readings of owner Q-58 (cut a
piece from the area's own offcut (A), every piece from a roll (B), ready-made pieces (C)). It also holds an open-plan
wet zone (a wet label and a dry one in one face, WET_ZONE_EXTENT_NOT_DRAWN: e.g. a pantry open to the dining room).

What V2.13 changes (everything else is V2.12: same registry 1.7.0, same lines, same ids, same order):

1. Owner Q-58 = A, CONDITIONAL (owner directive 2026-10-20 12:02): "suitable offcuts may be reused within the same
   roof or room ... before approving, PROVE the leftover covers the piece (width, length, overlap, upturn geometry,
   corners and terminations, seam arrangement) ... area alone is no proof". For an area V2.12 holds on Q-58, the
   layout(s) with the fewest rolls under reading A are checked by prove_q58_a(): a PHYSICAL cutting plan of whole
   1.00 x 10.00 m rolls in which
     (a) the layout covers the whole surface (MEMBRANE_FOLD_V3 coverage check: floor + 0.20 m upturn with mitred
         corners, openings' own upturn; residual after strips and patches 0 m2);
     (b) every main strip piece and every piece cut from a roll is packed into the same rolls the fold counts (the
         count re-derived from the pieces, never from net area / 10), every piece at most one roll long and wide;
     (c) every piece taken from an offcut (an upturn-only strip at an outline step, a patch) is placed, with its
         need width (its extent across the strips + the 0.10 m lap on each side that joins a sheet, MEMBRANE_FOLD_V3)
         and its length (incl. end laps), inside a real offcut of THIS area's final rolls: the full-width end left on a
         roll, or the side trim beside a narrower piece of the same roll, at a stated position; no two pieces overlap
         and nothing lies outside its roll; an offcut used once is split, never used twice;
     (d) nothing is carried from another area (Q-49 A).
   Proven -> the rolls line is RELEASED at the A count (SOURCE_DERIVED) with the proof, its cutting plan and the B and
   C counts beside it; not proven -> the line stays HELD and bounded exactly as V2.12 (the reasons listed). Corner
   detail pieces, the upturn's top termination and the factory lap edge are not named by the membrane spec
   (MEM-URBAN-DEFAULT-1x10, corner_treatment null): UNRESOLVED_BY_SYSTEM, the same for every reading, so they are
   listed and do not decide the count. No start offset (no Urban rule) and no new tolerance (MEMBRANE_FOLD_V3 / V2
   limits only).
2. Owner Q-37 A (2026-10-19 16:40: "waterproof the surrounding of the pantry") with the printed size typed into the
   project data file (owner Q-17 A, PROJECT_DATA_FILE_V1): a held wet zone whose wet label (e.g. PANTRY) on its floor is
   covered by ONE usable record WET_ZONE_SIZE* (kind table, value {"length_m", "width_m"} as printed, optional
   "roles_lm" {wall, door, other, ...} typed from the drawing) becomes a wet area of its own: its floor = the printed
   length x width (FIN.WP.FLOOR released, basis TYPED), its membrane by the owner's strip method on that rectangle
   (Q-30 strips both ways, Q-35 C strips 0.20 m longer at both ends whatever is at the edge, Q-37 A upturn round it,
   0.10 m lap, 1.00 x 10.00 m roll) and its own rolls line (each area alone, Q-49 A). Its walls-only upturn line
   (FIN.WP.WALL_UPTURN, Q-35 C) is released only from typed roles; otherwise it is HELD with its reason (never 0).
   A record that is missing, HELD / ASSUMED, for another project, ambiguous (two records, or two held zones with the
   label on one floor) or not a positive length x width leaves the zone held as in V2.12.

Nothing here is the released default: V2.13 runs only when asked for (owner 2026-10-20 12:15: nothing released changes
until the owner confirms the reconciliation). Project-agnostic: no layer, room, project name or size is coded."""

from __future__ import annotations

import math

from shapely.geometry import box

from engine.source import arch_v211 as AV11
from engine.source import arch_v212 as AV
from engine.source import membrane_cutting_plan_v2 as CP
from engine.source import membrane_fold_v3 as F3

# unchanged V2.12 pieces (read, never edited)
capture, wet_classes, decide_review, decided_release = AV.capture, AV.wet_classes, AV.decide_review, AV.decided_release
held_wet, top_roofs, door_transition_lines = AV.held_wet, AV.top_roofs, AV.door_transition_lines
roof_lines, top_roof_lines, held_wet_lines, wet_rows, roof_records = (AV.roof_lines, AV.top_roof_lines,
                                                                      AV.held_wet_lines, AV.wet_rows, AV.roof_records)
ITEMS, SYSTEMS, Q34, WET, HELD = AV.ITEMS, AV.SYSTEMS, AV.Q34, AV.WET, AV.HELD
PURCHASE_COLUMNS = AV.PURCHASE_COLUMNS

METHOD = "ARCH_TAKEOFF_V2.13"
POLICY_ID = "URBAN_BOQ_T120_ARCH_V2_13"
KNOWLEDGE = AV.KNOWLEDGE                                  # registry 1.7.0: owner answers cited, no new rule record
Q49_A = AV.Q49_A
Q58_A = ("owner Q-58 A, CONDITIONAL (owner directive 2026-10-20 12:02): suitable offcuts may be reused within the same "
         "roof or room, never carried to another; the count is released only when the cutting plan proves it")
Q37_A = ("owner Q-37 A (2026-10-19 16:40): the pantry is waterproofed within its printed size with the upturn round it, "
         "the open side a threshold line")
Q17_A = "owner Q-17 A (2026-10-19): a value typed from a drawing enters through the controlled project data file"
RELEASED_A = "RELEASED_Q58_A"
UNRESOLVED_BY_SYSTEM = ["extra corner detail pieces", "top termination of the upturn", "factory lap edge"]
ZONE_KEY = "WET_ZONE_SIZE"


# ------------------------------------------------------------------------------------------------ Q-58 A proof
def _main_pieces(lay):
    return [{"strip": f"S{k}", "kind": s["kind"], "piece": j, "w": s["width_m"], "l": x}
            for k, s in enumerate(lay["strips"], 1) if s["kind"] == "MAIN"
            for j, x in enumerate(s["piece_lengths_m"], 1)]


def prove_q58_a(lay, spec):
    """the physical cutting plan of one layout under owner Q-58 A (each area alone): every piece on a stated roll at a
    stated position, the own-offcut pieces inside real offcuts of those rolls. -> {"proven", "failures", "rolls",
    "plan", "offcut_pieces", "offcuts_left", ...}."""
    from engine.source import membrane_layout as ML
    W, L = spec["roll_width_m"], spec["roll_length_m"]
    c = lay["counts"]["Q58_A"]
    fails = []
    if lay.get("residual_after_m2") != 0.0:
        fails.append(f"COVERAGE: {lay.get('residual_after_m2')} m2 neither covered nor patched")
    main = _main_pieces(lay)
    rest = [{"strip": f"X{k}", "kind": e["what"], "piece": 1, "w": e["w"], "l": e["l"]}
            for k, e in enumerate(c["pieces_from_rolls"], 1)]
    own = [{"strip": f"O{k}", "kind": e["what"], "w": e["w"], "l": e["l"]}
           for k, e in enumerate(c["pieces_from_own_offcuts"], 1)]
    for p in main + rest + own:
        if p["l"] > L + F3.EPS or p["w"] > W + F3.EPS or p["l"] <= 0 or p["w"] <= 0:
            fails.append(f"PIECE_SIZE: {p['strip']} {p['w']} x {p['l']} m does not fit a {W} x {L} m roll")
    pieces = main + rest
    bins, info = ML.pack_rolls([p["l"] for p in pieces], L) if pieces else ([], {"proven": True, "lower_bound": 0})
    if len(bins) != c["rolls"]:
        fails.append(f"COUNT: the pieces pack into {len(bins)} rolls, the fold counts {c['rolls']}")
    # every piece on its roll: along the roll from 0, longest first (the cutting plan order); the side trim beside a
    # narrower piece and the full-width end are the offcuts
    rolls, free = [], []
    for k, b in enumerate(sorted(bins, key=lambda b: min(b)), 1):
        x, cut = 0.0, []
        for i in sorted(b, key=lambda i: (-pieces[i]["l"], i)):
            p = pieces[i]
            cut.append(dict(p, roll=k, x0=round(x, 6), x1=round(x + p["l"], 6), y0=0.0, y1=round(p["w"], 6),
                            source="ROLL"))
            if W - p["w"] > F3.EPS:
                free.append({"roll": k, "kind": "SIDE_TRIM", "of": f"{p['strip']}.{p['piece']}", "x0": x,
                             "x1": x + p["l"], "y0": p["w"], "y1": W})
            x += p["l"]
        if L - x > F3.EPS:
            free.append({"roll": k, "kind": "ROLL_END", "of": f"roll {k}", "x0": x, "x1": L, "y0": 0.0, "y1": W})
        rolls.append({"roll": k, "pieces": cut, "used_m": round(x, 4), "left_m": round(L - x, 4)})
    # the own-offcut pieces: largest first into the smallest offcut that holds it (no turning: the strips' direction
    # is the roll's length); an offcut that takes a piece keeps the length beyond it (full offcut width) and the
    # width beside it (the piece's length)
    placed = []
    for p in sorted(own, key=lambda e: (-e["w"] * e["l"], -e["l"], e["strip"])):
        cand = [o for o in free if p["w"] <= (o["y1"] - o["y0"]) + F3.EPS and p["l"] <= (o["x1"] - o["x0"]) + F3.EPS]
        if not cand:
            fails.append(f"OFFCUT: no offcut of this area holds {p['kind']} {p['w']:.3f} x {p['l']:.3f} m")
            continue
        o = min(cand, key=lambda o: ((o["x1"] - o["x0"]) * (o["y1"] - o["y0"]), o["x1"] - o["x0"], o["roll"], o["x0"]))
        free.remove(o)
        q = dict(p, roll=o["roll"], x0=round(o["x0"], 6), x1=round(o["x0"] + p["l"], 6), y0=round(o["y0"], 6),
                 y1=round(o["y0"] + p["w"], 6), source=f"OWN_{o['kind']} of {o['of']}")
        placed.append(q)
        rolls[o["roll"] - 1]["pieces"].append(q)
        if (o["x1"] - o["x0"]) - p["l"] > F3.EPS:
            free.append(dict(o, x0=o["x0"] + p["l"]))
        if (o["y1"] - o["y0"]) - p["w"] > F3.EPS:
            free.append(dict(o, x1=o["x0"] + p["l"], y0=o["y0"] + p["w"]))
    # no overlap, nothing outside its roll (checked on the geometry itself, not on the bookkeeping above)
    for r in rolls:
        bx = [box(q["x0"], q["y0"], q["x1"], q["y1"]) for q in r["pieces"]]
        for q, g in zip(r["pieces"], bx):
            if q["x0"] < -F3.EPS or q["y0"] < -F3.EPS or q["x1"] > L + F3.EPS or q["y1"] > W + F3.EPS:
                fails.append(f"OUTSIDE_ROLL: {q['strip']} on roll {r['roll']}")
        for i in range(len(bx)):
            for j in range(i + 1, len(bx)):
                if bx[i].intersection(bx[j]).area > F3.NUMERIC_M2 * 1e-4:
                    fails.append(f"OVERLAP: {r['pieces'][i]['strip']} / {r['pieces'][j]['strip']} on roll {r['roll']}")
    left = sorted(({"roll": o["roll"], "kind": o["kind"], "width_m": round(o["y1"] - o["y0"], 4),
                    "length_m": round(o["x1"] - o["x0"], 4)} for o in free
                   if o["x1"] - o["x0"] > F3.EPS and o["y1"] - o["y0"] > F3.EPS),
                  key=lambda o: (o["roll"], o["kind"], -o["length_m"]))
    used = sum(q["w"] * q["l"] for r in rolls for q in r["pieces"])
    return {"rule": Q58_A, "proven": not fails, "failures": fails, "rolls": len(bins),
            "packing_minimal_proven": bool(info.get("proven")), "lower_bound": info.get("lower_bound"),
            "plan": [dict(r, pieces=[{k: (round(v, 4) if isinstance(v, float) else v) for k, v in q.items()}
                                     for q in r["pieces"]]) for r in rolls],
            "offcut_pieces": [{k: (round(v, 4) if isinstance(v, float) else v) for k, v in q.items()} for q in placed],
            "pieces_from_rolls": len(pieces), "pieces_from_own_offcuts": len(placed),
            "cut_from_rolls_m": round(sum(p["l"] for p in pieces), 4), "material_used_m2": round(used, 4),
            "required_surface_m2": lay.get("required_m2"), "offcuts_left": left,
            "offcuts_left_note": "every piece of roll left after cutting, full-width ends and side trims alike; no "
                                 "Urban rule sets a smallest reusable size, so none is called waste or reusable here",
            "unresolved_by_system": list(UNRESOLVED_BY_SYSTEM)}


def purchase(fold):
    """MEMBRANE_CUTTING_PLAN_V2.purchase (V2.12, unchanged for every released area); an area held on owner Q-58 is
    released at its fewest rolls under reading A when a layout reaching that count is proven by prove_q58_a."""
    p = CP.purchase(fold)
    if p["state"] == "RELEASED":
        return p
    sp, lays = fold["spec"], fold["layouts_v3"]
    a = p["rolls_by_reading"]["Q58_A"]["rolls"]
    tried = []
    for i in sorted(range(len(lays)), key=lambda i: CP._key(lays, i, "Q58_A")):
        x = lays[i]
        if x["rolls_by_basis"]["Q58_A"] != a:
            break
        pr = prove_q58_a(x, sp)
        tried.append({"layout": CP.LAYOUT_NAMES[(x["direction"], x["start"])], "proven": pr["proven"],
                      "failures": pr["failures"]})
        if pr["proven"]:
            out = dict(p, state=RELEASED_A, rolls=a, rolls_bounded=None, direction=x["direction"], start=x["start"],
                       strips=len(x["strips"]), upturn_only_strips=x["upturn_strips"],
                       upturn_only_strip_m=x["upturn_strip_m"], strip_length_m=x["strip_metres"], cut_m2=x["cut_m2"],
                       leftover_m=round(sum(r["left_m"] for r in pr["plan"]), 4),
                       side_trim_m2=round(x["strip_metres"] * sp["roll_width_m"] - x["cut_m2"], 4),
                       patches=[{k: q.get(k) for k in ("kind", "m2", "along_m", "across_m", "centre_room_frame_m",
                                                         "centre_drawing_units")} for q in x["patches"]],
                       patch_m2=x["patch_m2"], residual_before_v2_strips_m2=x["residual_before_m2"],
                       residual_after_m2=x["residual_after_m2"], numerical_residual_m2=x["numerical_residual_m2"],
                       cutting_plan=pr["plan"], cutting_plan_reading="Q58_A", proof_q58_a=pr,
                       cutting_plan_q58_b=p["cutting_plan"], layouts_tried_q58_a=tried, owner_answer=Q58_A,
                       flags=list(p["flags"]) + ["RELEASED_ON_Q58_A_PROOF"])
            out.pop("reason", None)
            return out
    return dict(p, layouts_tried_q58_a=tried,
                reason=p["reason"] + "; owner Q-58 A is conditional on a proven cutting plan and no layout with "
                                     f"{a} rolls is proven: " + "; ".join(f for t in tried for f in t["failures"]))


# ------------------------------------------------------------------------------------------------ typed wet zones
def _zone_records(pdf, floor, code):
    out = []
    for k in pdf.keys():
        if not k.startswith(ZONE_KEY):
            continue
        v = pdf.value(k, floor=floor, member=code)
        if v["status"] == "MISSING" or "applies_to does not cover" in (v.get("reason") or ""):
            continue
        r = pdf.records[k]
        if code not in (r["applies_to"].get("members") or ()) or floor not in (r["applies_to"].get("floors") or ()):
            continue                          # a zone record names its floor and its wet label explicitly
        out.append(v)
    return out


def typed_zones(held, project_data, project_id, spec=None):
    """owner Q-37 A + Q-17 A: each held wet zone with exactly one usable typed printed size becomes a wet area row
    (MEMBRANE_FOLD_V3 on the printed rectangle). -> (zone rows, held rows left, records of every zone looked at)."""
    from engine.source import arch_measure as AM          # noqa: F401  (facts schema is checked by the run)
    from engine.source import project_data_file as PD
    from engine.source import wet_room_evidence as WE
    if not held:
        return [], list(held), []
    if not project_data:
        return [], list(held), [{"room_id": h["room_id"], "state": HELD, "reason": "NO_PROJECT_DATA_FILE"}
                                for h in held]
    try:
        pdf = PD.load(project_data)
    except PD.ProjectDataFileError as ex:
        return [], list(held), [{"room_id": h["room_id"], "state": HELD, "reason": f"PROJECT_DATA_FILE_INVALID: {ex}"}
                                for h in held]
    from engine.source import knowledge as K
    with K.using(KNOWLEDGE):
        wet_codes = set(K.wet_codes()) | {WE.HAND_WASH}
    zones, left, log = [], [], []
    for h in held:
        wc = [c for c in h["codes"] if c in wet_codes]
        same = [g for g in held if g["floor"] == h["floor"] and set(wc) & set(g["codes"])]
        rec = {"floor": h["floor"], "room_id": h["room_id"], "codes": h["codes"], "wet_codes": wc}
        if pdf.project != project_id:
            log.append(dict(rec, state=HELD, reason=f"PROJECT_DATA_OTHER_PROJECT ({pdf.project} is not {project_id})"))
            left.append(h)
            continue
        if len(wc) != 1 or len(same) != 1:
            log.append(dict(rec, state=HELD, reason="ZONE_NOT_IDENTIFIED_ONCE: the zone needs one wet label that no "
                                                    "other held zone on its floor carries"))
            left.append(h)
            continue
        vs = _zone_records(pdf, h["floor"], wc[0])
        if len(vs) != 1:
            log.append(dict(rec, state=HELD, reason=f"{len(vs)} {ZONE_KEY} records for {wc[0]} on {h['floor']} "
                                                    "(one is needed)"))
            left.append(h)
            continue
        v = vs[0]
        val = v.get("value") if v["usable"] else None
        ok = isinstance(val, dict) and all(isinstance(val.get(k), (int, float)) and not isinstance(val.get(k), bool)
                                           and math.isfinite(val[k]) and val[k] > 0 for k in ("length_m", "width_m"))
        if not v["usable"] or not ok:
            log.append(dict(rec, state=HELD, reason=v.get("reason") or "the record is not a positive length_m x "
                                                                         "width_m", record=v["key"]))
            left.append(h)
            continue
        Lz, Wz = float(val["length_m"]), float(val["width_m"])
        roles = val.get("roles_lm") if isinstance(val.get("roles_lm"), dict) else None
        row = F3.area(floor=h["floor"], room_id=h["room_id"], name="/".join(h["codes"]),
                      polygon=[(0.0, 0.0), (Lz, 0.0), (Lz, Wz), (0.0, Wz)], roles_lm=roles, spec=spec)
        row.update(system="WET_AREAS", name_en=h.get("name_en"), name_ar=h.get("name_ar"),
                   roles_source="typed in the project data file" if roles else None,
                   evidence="WET_ZONE_TYPED_PRINTED_SIZE", typed={"key": v["key"], "status": v["status"],
                                                                 "source": v["source"], "basis": v["basis"],
                                                                 "value": val, "wet_code": wc[0]},
                   zone_floor_m2=round(Lz * Wz, 6), whole_face_m2=h["area_of_whole_face_m2"])
        zones.append(row)
        log.append(dict(rec, state="TYPED", record=v["key"], status=v["status"], length_m=Lz, width_m=Wz))
    return zones, left, log


def _zline(ctx, *, item_code, unit, floor, room_id, element, ev, net=None, formula, inputs, rule_id, name_en=None,
           name_ar=None, rfi=None):
    """a line of a typed wet zone: geometry from the owner's / designer's printed size (OWNER_FACT basis: typed, never
    automatic extraction)."""
    from engine.source import boq_line as BL
    from engine.source import knowledge as K
    with K.using(KNOWLEDGE):
        ref = K.ref(rule_id)
    return BL.make_line(project_id=ctx["project_id"], revision_set_sha256=ctx["revision_set_sha256"],
                        item_code=item_code, unit=unit, evidence_state=ev,
                        measured_net=net if ev in BL.QUANTITY_STATES else None, element_id=f"{room_id}:{element}",
                        floor=floor, room_id=room_id, room_name_en=name_en, room_name_ar=name_ar,
                        physical_element=element, formula=formula, inputs=inputs, documents=ctx["documents"],
                        geometry_source="OWNER_FACT",
                        geometry_confidence="TYPED_PRINTED_SIZE" if ev in BL.QUANTITY_STATES else "NOT_ESTABLISHED",
                        rule_id=ref["rule_id"], rule_version=ref["version"], rule_set=ref["rule_set"],
                        rule_set_digest=ref["rule_set_digest"], rfi=rfi, material_state="PROJECT_OWNER_FACT")


def zone_lines(ctx, zones):
    """FIN.WP.FLOOR (the printed size, the same line id as V2.12's held line) and FIN.WP.WALL_UPTURN (Q-35 C walls
    only: typed roles, else HELD) of each typed wet zone. Its rolls line is written by rolls_lines."""
    out = []
    for z in zones:
        t = z["typed"]
        nm = {"name_en": z.get("name_en"), "name_ar": z.get("name_ar")}
        inp = {"basis": t["basis"], "record": t["key"], "status": t["status"], "source": t["source"],
               "length_m": t["value"]["length_m"], "width_m": t["value"]["width_m"], "wet_code": t["wet_code"],
               "whole_face_m2": z["whole_face_m2"], "rules": [Q37_A, Q17_A]}
        if z["state"] != "COMPUTED":
            continue
        out.append(_zline(ctx, item_code="FIN.WP.FLOOR", unit="m2", floor=z["floor"], room_id=z["room_id"],
                          element="wp_floor:wet_zone", ev="SOURCE_DERIVED", net=z["zone_floor_m2"],
                          formula="printed length x width of the wet zone (owner Q-37 A; typed, owner Q-17 A)",
                          inputs=inp, rule_id="UP-WET-001", **nm))
        up = z["lines"]["upturn"]
        if up["state"] == "MEASURED":
            out.append(_zline(ctx, item_code="FIN.WP.WALL_UPTURN", unit="m2", floor=z["floor"], room_id=z["room_id"],
                              element="wp_wall_upturn:wet_zone", ev="SOURCE_DERIVED", net=up["m2"],
                              formula="walls-only upturn 0.20 m (owner Q-35 C) on the typed wall runs",
                              inputs=dict(inp, walls_lm=up["lm"], thresholds=z["lines"]["thresholds"]),
                              rule_id="UP-WP-003", **nm))
        else:
            q = ("WET_ZONE_WALLS_NOT_TYPED (owner Q-35 C walls only): the typed printed size gives the floor and the "
                 "membrane strips, not which sides are walls, doors or open; the walls-only upturn needs those runs "
                 "typed from the drawing")
            out.append(_zline(ctx, item_code="FIN.WP.WALL_UPTURN", unit="m2", floor=z["floor"], room_id=z["room_id"],
                              element="wp_wall_upturn:wet_zone", ev="BLOCKED_RFI", formula="walls-only upturn 0.20 m",
                              inputs=inp, rule_id="UP-WP-003", rfi={"question": q, "unlocks": z["room_id"]}, **nm))
    return out


# ------------------------------------------------------------------------------------------------ table, lines
def membrane_table(wet, roofs, held=(), top=()):
    """ARCH_TAKEOFF_V2.12's membrane table on this purchase: an area released on the Q-58 A proof is summed with the
    released areas (its B / C counts shown on its row); every other row, total and held list as V2.12."""
    from engine.source import membrane_fold_v2 as F2
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
        out_rows, buy, q58, hl = [], [], [], list(held_by[name])
        for x in rows:
            tr = AV11._table_row(x)
            if x.get("fold") is not None:
                tr["purchase"] = purchase(x["fold"])
                (buy if tr["purchase"]["state"] in ("RELEASED", RELEASED_A) else q58).append(tr)
            else:
                hl.append({"floor": x["floor"], "room_id": x["room_id"], "name": x.get("name"),
                           "reason": x.get("reason")})
            out_rows.append(tr)
        total = None
        if buy or q58:
            low = sum(r["purchase"]["rolls"] for r in buy) + sum(r["purchase"]["rolls_bounded"]["low"] for r in q58)
            high = sum(r["purchase"]["rolls"] for r in buy) + sum(r["purchase"]["rolls_bounded"]["high"] for r in q58)
            na = [r for r in buy if r["purchase"]["state"] == RELEASED_A]
            total = {"areas": len(buy), "rolls_to_buy": sum(r["purchase"]["rolls"] for r in buy) if buy else None,
                     "cut_m2": round(sum(r["purchase"]["cut_m2"] for r in buy), 4),
                     "strip_length_m": round(sum(r["purchase"]["strip_length_m"] for r in buy), 4),
                     "leftover_m": round(sum(r["purchase"]["leftover_m"] for r in buy), 4),
                     "side_trim_m2": round(sum(r["purchase"]["side_trim_m2"] for r in buy), 4),
                     "patch_m2": round(sum(r["purchase"]["patch_m2"] for r in buy + q58), 6),
                     "held_q58_areas": len(q58), "rolls_with_q58_held_low": low, "rolls_with_q58_held_high": high,
                     "released_on_q58_a_proof": len(na),
                     "rolls_if_q58_b": (sum(r["purchase"]["rolls"] for r in buy if r["purchase"]["state"] == "RELEASED")
                                        + sum(r["purchase"]["rolls_by_reading"]["Q58_B"]["rolls"] for r in na))
                     if buy else None,
                     "held_areas": len(hl), "complete": not hl and not q58,
                     "note": "sum of the released areas, each alone (owner Q-49 A)" + (
                         f"; {len(na)} released on the owner Q-58 A proof (every piece from a roll: rolls_if_q58_b)"
                         if na else "") + (
                         f"; {len(q58)} area(s) wait on owner Q-58: with them {low} - {high} rolls" if q58 else "") + (
                         "; held areas are not in the sum (each has its held rolls line)" if hl else "")}
        systems[name] = {"rows": out_rows, "held": hl, "held_q58": [{"floor": r["floor"], "room_id": r["room_id"],
                                                                    "name": r.get("name"), "rolls_bounded":
                                                                    r["purchase"]["rolls_bounded"]} for r in q58],
                         "purchase_total": total, "project": F2.project(rows) if rows else None,
                         "project_note": "MEMBRANE_FOLD_V2.project packs offcuts across areas (V2 strips): information "
                                         "only, not the purchase (owner Q-49 A: each area alone)"}
    return {"policy": F3.METHOD_ID, "purchase_rule": Q49_A, "open_rule": AV.Q58, "answered_rule": Q58_A,
            "systems": systems,
            "never": ["a total across membrane systems (UP-WP-MAT-001)", "a held area as 0",
                      "an offcut carried from one area to another (owner Q-49 A)",
                      "rolls from net area / roll area (UP-WP-001)", "an uncovered upturn left out of the count",
                      "a count released on owner Q-58 A without a proven cutting plan"]}


def _one(name, row):
    return {"systems": {name: {"rows": [row], "held": []}}}


def _a_inputs(p, name):
    return {"system": name, "method": F3.METHOD_ID, "direction": p["direction"], "start": p["start"],
            "strips": p["strips"], "upturn_only_strips": p["upturn_only_strips"], "strip_length_m": p["strip_length_m"],
            "cut_m2": p["cut_m2"], "leftover_m": p["leftover_m"], "side_trim_m2": p["side_trim_m2"],
            "patches": p["patches"], "patch_m2": p["patch_m2"], "rolls_by_reading": p["rolls_by_reading"],
            "cutting_plan": p["cutting_plan"], "cutting_plan_reading": "Q58_A", "proof_q58_a": p["proof_q58_a"],
            "cutting_plan_q58_b": p["cutting_plan_q58_b"], "owner_answer": Q58_A, "layouts": p["layouts"],
            "flags": p["flags"]}


def rolls_lines(ctx, table, names=None):
    """ARCH_TAKEOFF_V2.12's rolls lines, row by row in the same order; a row released on the Q-58 A proof gets a
    released line (the same line id as V2.12's bounded line) with the proof and the B / C counts beside it."""
    out = []
    for name in SYSTEMS:
        st = table["systems"].get(name) or {}
        for r in st.get("rows") or ():
            p = r.get("purchase")
            if p is None:
                continue
            if p["state"] != RELEASED_A:
                out += AV.rolls_lines(ctx, _one(name, r), names)
                continue
            nm = (names or {}).get((r["floor"], r["room_id"])) or {}
            rd = p["rolls_by_reading"]
            formula = ("this area alone (owner Q-49 A): the layout with the fewest whole 1.00 x 10.00 m rolls under "
                       "owner Q-58 A (pieces the straight strips do not reach cut from this area's own roll ends / side "
                       "trims), released because its physical cutting plan is proven (every piece on a stated roll, "
                       "own-offcut pieces inside real offcuts, no overlap, coverage complete); every piece from a roll "
                       f"(Q-58 B) needs {rd['Q58_B']['rolls']}")
            out.append(AV11._line(ctx, item_code="FIN.WP.MEMBRANE_ROLLS", unit="pcs", floor=r["floor"],
                                  room_id=r["line_room_id"], element="wp_rolls_to_buy", ev="SOURCE_DERIVED",
                                  net=p["rolls"], formula=formula, inputs=_a_inputs(p, name), rule_id="UP-WP-LAY-001",
                                  name_en=nm.get("name_en"), name_ar=nm.get("name_ar")))
        for h in st.get("held") or ():
            out += AV.rolls_lines(ctx, {"systems": {name: {"rows": [], "held": [h]}}}, names)
    return out


def purchase_rows(table):
    """the owner's purchase table (ARCH_TAKEOFF_V2.12 columns): a row released on the Q-58 A proof shows its A count
    as rolls, its proven cutting plan and the B / C counts beside it."""
    out = []
    for name in SYSTEMS:
        st = table["systems"].get(name) or {}
        for r in st.get("rows") or ():
            p = r.get("purchase")
            if p is None:
                continue
            if p["state"] != RELEASED_A:
                out += [x for x in AV.purchase_rows(_one(name, r)) if x.get("room_id") != "TOTAL"]
                continue
            plan = " | ".join(f"roll {x['roll']}: " + " + ".join(f"{q['w']:.2f}x{q['l']:.2f}"
                                                                   + ("" if q["source"] == "ROLL" else "*")
                                                                   for q in x["pieces"]) + f", {x['left_m']:.2f} m left"
                              for x in p["cutting_plan"])
            rd = p["rolls_by_reading"]
            out.append({"system": name, "floor": r["floor"], "room_id": r["room_id"], "name": r.get("name"),
                        "state": "RELEASED", "floor_m2": r["floor_m2"], "layout": f"{p['direction']} / {p['start']}",
                        "strips": p["strips"], "upturn_only_strips": p["upturn_only_strips"], "cutting_plan": plan,
                        "rolls": p["rolls"], "rolls_q58_a": rd["Q58_A"]["rolls"], "rolls_q58_b": rd["Q58_B"]["rolls"],
                        "rolls_q58_c": rd["Q58_C"]["rolls"], "strip_length_m": p["strip_length_m"],
                        "cut_m2": p["cut_m2"], "leftover_m": p["leftover_m"], "side_trim_m2": p["side_trim_m2"],
                        "patch_m2": p["patch_m2"],
                        "reason": "owner Q-58 A proven: pieces marked * are cut from this area's own offcuts"})
        for h in st.get("held") or ():
            out.append({"system": name, "floor": h["floor"], "room_id": h["room_id"], "name": h["name"],
                        "state": "HELD", "reason": h["reason"]})
        t = st.get("purchase_total")
        if t:
            out.append({"system": name, "room_id": "TOTAL", "state": "SUM_OF_AREAS" if t["complete"] else
                        "SUM_OF_RELEASED_AREAS_HELD_EXCLUDED", "rolls": t["rolls_to_buy"],
                        "strip_length_m": t["strip_length_m"], "cut_m2": t["cut_m2"], "leftover_m": t["leftover_m"],
                        "side_trim_m2": t["side_trim_m2"], "patch_m2": t["patch_m2"], "reason": t["note"]})
    return out


def summary(classes, decided, wet, flags, held, roofs, table, lines, zones_log=()):
    s = AV.summary(classes, decided, wet, flags, held, roofs, table, lines)
    s["typed_wet_zones"] = list(zones_log)
    s["released_on_q58_a_proof"] = [{"system": k, "floor": r["floor"], "room_id": r["room_id"],
                                     "rolls": r["purchase"]["rolls"],
                                     "rolls_q58_b": r["purchase"]["rolls_by_reading"]["Q58_B"]["rolls"]}
                                    for k, v in table["systems"].items() for r in v["rows"]
                                    if (r.get("purchase") or {}).get("state") == RELEASED_A]
    return s


def policy_record():
    return {"method": METHOD, "policy": POLICY_ID, "knowledge": KNOWLEDGE,
            "pieces": ["WET_ROOM_EVIDENCE_V1 (T-010)", "EXTERIOR_SPACES_V1 (T-071)", "MEMBRANE_FOLD_V3 (T-096)",
                       "PROJECT_DATA_FILE_V1 (T-064)"],
            "builds_on": AV.METHOD, "released_default": False,
            "owner_answers": ["Q-06 a", "Q-13 B", "Q-17 A", "Q-24", "Q-25", "Q-29", "Q-30 A", "Q-34 parked", "Q-35 C",
                              "Q-37 A", "Q-40 A", "Q-49 A", "Q-58 A conditional (proof)"],
            "open": ["Q-58 counts whose A plan is not proven stay held (bounded)"],
            "purchase_rule": Q49_A, "q58_rule": Q58_A, "zone_record_key": ZONE_KEY,
            "unresolved_by_system": list(UNRESOLVED_BY_SYSTEM), "items": sorted(set(ITEMS) | {"FIN.WP.WALL_UPTURN"}),
            "fold": F3.policy_record()}
