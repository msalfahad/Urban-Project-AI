"""ARCH_TAKEOFF_V2.12 (board task T-096): ARCH_TAKEOFF_V2.11 + complete membrane coverage (MEMBRANE_FOLD_V3).

V2.11 (engine/source/arch_v211.py, released, never edited) counts the rolls of each wet area and roof alone (owner Q-49
A) on the strips of MEMBRANE_FOLD_V2. Those strips leave the 0.20 m upturn of an outline STEP uncovered when the step's
edge runs parallel to the strips and its upturn falls in a band where that part of the outline has no floor (found by
the hand cutting plans of T-094 on the development villa: a 4.20 m parapet, 0.84 m2, released 17 rolls, hand 18). V2.11
also left slanted / curved corners and the opening upturn the strips do not reach as an m2 figure outside the count.

What V2.12 changes (everything else is V2.11, same registry 1.7.0, same lines and ids):
1. Each wet area and roof row carries MEMBRANE_FOLD_V3 (engine/source/membrane_fold_v3.py): per layout the V2 strips,
   the UPTURN-ONLY strips that close every strip-shaped residual, and every other residual as a listed PATCH (m2,
   size, position); residual after strips and patches = 0.
2. FIN.WP.MEMBRANE_ROLLS per area alone (owner Q-49 A: fewest rolls, tie the shorter strip metres, then the smaller
   cut m2, then the listed order), counted under the three readings of owner Q-58 (OPEN):
       Q58_A  pieces and patches cut from the area's own leftover / side trim when one is large enough
       Q58_B  every piece and patch cut from a roll (offcuts not reused)
       Q58_C  strips from rolls, patches as ready-made pieces by detail
   When the fewest rolls are the same under all three readings, the count is RELEASED (with the layout that reaches it
   under Q58_B, so the printed cutting plan buys it without reusing any offcut). Otherwise the area's count depends on
   the open owner question: the rolls line is HELD as a bounded line (low = the fewest, high = the most of the three
   readings), every reading shown with its layout, never 0 and never one reading picked.
3. The purchase table and the run record name the method (ARCH_TAKEOFF_V2.12) and MEMBRANE_FOLD_V3.
Rules: Q-24 + addendum, Q-25, Q-29, Q-44 A, Q-49 A, Q-58 (open), UP-WP-001, UP-WP-002, UP-WP-003, UP-WP-ROOF-001,
UP-WP-LAY-001, UP-QTY-STATUS-001. Project-agnostic: no layer, room or project name is coded."""

from __future__ import annotations

from engine.source import arch_v211 as AV
from engine.source import membrane_cutting_plan_v2 as CP
from engine.source import membrane_fold_v3 as F3

# unchanged V2.11 pieces (read, never edited)
capture, wet_classes, decide_review, decided_release = AV.capture, AV.wet_classes, AV.decide_review, AV.decided_release
held_wet, top_roofs, door_transition_lines = AV.held_wet, AV.top_roofs, AV.door_transition_lines
roof_lines, top_roof_lines, held_wet_lines, _line, _table_row = (AV.roof_lines, AV.top_roof_lines, AV.held_wet_lines,
                                                                 AV._line, AV._table_row)
ITEMS, SYSTEMS, Q34, WET, HELD = AV.ITEMS, AV.SYSTEMS, AV.Q34, AV.WET, AV.HELD

METHOD = "ARCH_TAKEOFF_V2.12"
POLICY_ID = "URBAN_BOQ_T096_ARCH_V2_12"
KNOWLEDGE = AV.KNOWLEDGE                                  # registry 1.7.0: no new rule record (Q-58 is open)
Q49_A = AV.Q49_A
Q58 = CP.Q58
LAYOUT_NAMES = CP.LAYOUT_NAMES
purchase = CP.purchase                                    # owner Q-49 A per area alone, read under owner Q-58


# ------------------------------------------------------------------------------------------------ membrane rows
def wet_rows(arch, classes):
    """AV.wet_rows with each row's fold from MEMBRANE_FOLD_V3 (same rows, same roles, same doors)."""
    from engine.source import membrane_fold_v2 as F2
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
            roles = {k: rl.get(k, 0.0) for k in F2.ELIGIBLE + F2.THRESHOLD_ROLES + ("door",)}
        row = F3.area(floor=r["floor"], room_id=r["room_id"], name="/".join(r["codes"]) or "(no label)",
                      polygon=r["polygon_m"], holes=r.get("hole_polygons_m") or (), roles_lm=roles,
                      doors=AV._doors_of(r, arch))
        row.update(system="WET_AREAS", name_en=r.get("name_en"), name_ar=r.get("name_ar"),
                   roles_source="WATERPROOFING_SCHEDULE typed ring" if sched else "room boundary runs",
                   evidence=classes[r["room_id"]]["reason"])
        rows.append(row)
    return rows, flags


def roof_records(cap, floor_of, facts=None):
    """AV.roof_records with each released roof's fold from MEMBRANE_FOLD_V3."""
    from engine.source import exterior_spaces as XS
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
                a = F3.area(floor=row["floor"], room_id=f"{rid}:{rec.get('text_id')}",
                            polygon=list(face.exterior.coords), holes=[list(h.coords) for h in face.interiors],
                            unit_m=c["unit_m"], name=rec["code"])
                a.update(system="ROOFS" if rec["code"] == "ROOF" else "BALCONIES",
                         line_room_id=f"{row['floor']}-{rec['code']}-{rec.get('text_id')}")
                row["fold"] = a
            out.append(row)
    return out


# ------------------------------------------------------------------------------------------------ table, lines
def membrane_table(wet, roofs, held=(), top=()):
    """AV.membrane_table on the V3 purchase: released areas summed, an area whose count waits on owner Q-58 named with
    its bounded count (low / high sums shown beside), held areas named (never 0)."""
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
            tr = _table_row(x)
            if x.get("fold") is not None:
                tr["purchase"] = purchase(x["fold"])
                (buy if tr["purchase"]["state"] == "RELEASED" else q58).append(tr)
            else:
                hl.append({"floor": x["floor"], "room_id": x["room_id"], "name": x.get("name"),
                           "reason": x.get("reason")})
            out_rows.append(tr)
        total = None
        if buy or q58:
            low = sum(r["purchase"]["rolls"] for r in buy) + sum(r["purchase"]["rolls_bounded"]["low"] for r in q58)
            high = sum(r["purchase"]["rolls"] for r in buy) + sum(r["purchase"]["rolls_bounded"]["high"] for r in q58)
            total = {"areas": len(buy), "rolls_to_buy": sum(r["purchase"]["rolls"] for r in buy),
                     "cut_m2": round(sum(r["purchase"]["cut_m2"] for r in buy), 4),
                     "strip_length_m": round(sum(r["purchase"]["strip_length_m"] for r in buy), 4),
                     "leftover_m": round(sum(r["purchase"]["leftover_m"] for r in buy), 4),
                     "side_trim_m2": round(sum(r["purchase"]["side_trim_m2"] for r in buy), 4),
                     "patch_m2": round(sum(r["purchase"]["patch_m2"] for r in buy + q58), 6),
                     "held_q58_areas": len(q58), "rolls_with_q58_held_low": low, "rolls_with_q58_held_high": high,
                     "held_areas": len(hl), "complete": not hl and not q58,
                     "note": "sum of the released areas, each alone (owner Q-49 A)" + (
                         f"; {len(q58)} area(s) wait on owner Q-58: with them {low} - {high} rolls" if q58 else "") + (
                         "; held areas are not in the sum (each has its held rolls line)" if hl else "")}
        systems[name] = {"rows": out_rows, "held": hl, "held_q58": [{"floor": r["floor"], "room_id": r["room_id"],
                                                                    "name": r.get("name"), "rolls_bounded":
                                                                    r["purchase"]["rolls_bounded"]} for r in q58],
                         "purchase_total": total, "project": F2.project(rows) if rows else None,
                         "project_note": "MEMBRANE_FOLD_V2.project packs offcuts across areas (V2 strips): information "
                                         "only, not the purchase (owner Q-49 A: each area alone)"}
    return {"policy": F3.METHOD_ID, "purchase_rule": Q49_A, "open_rule": Q58, "systems": systems,
            "never": ["a total across membrane systems (UP-WP-MAT-001)", "a held area as 0",
                      "an offcut carried from one area to another (owner Q-49 A)",
                      "rolls from net area / roll area (UP-WP-001)", "an uncovered upturn left out of the count",
                      "one reading of owner Q-58 picked while it is open"]}


PURCHASE_COLUMNS = ("system", "floor", "room_id", "name", "state", "floor_m2", "layout", "strips", "upturn_only_strips",
                    "cutting_plan", "rolls", "rolls_q58_a", "rolls_q58_b", "rolls_q58_c", "strip_length_m", "cut_m2",
                    "leftover_m", "side_trim_m2", "patch_m2", "reason")


def purchase_rows(table):
    """the owner's purchase table, one row per wet area / roof (each alone, Q-49 A): released rows with the cutting
    plan, rows waiting on owner Q-58 with the three readings and no single count, held areas with their reason, then
    one total row per system."""
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
            rd = p["rolls_by_reading"]
            out.append({"system": name, "floor": r["floor"], "room_id": r["room_id"], "name": r.get("name"),
                        "state": "RELEASED" if p["state"] == "RELEASED" else "HELD", "floor_m2": r["floor_m2"],
                        "layout": f"{p['direction']} / {p['start']}", "strips": p["strips"],
                        "upturn_only_strips": p["upturn_only_strips"], "cutting_plan": plan, "rolls": p["rolls"],
                        "rolls_q58_a": rd["Q58_A"]["rolls"], "rolls_q58_b": rd["Q58_B"]["rolls"],
                        "rolls_q58_c": rd["Q58_C"]["rolls"], "strip_length_m": p["strip_length_m"],
                        "cut_m2": p["cut_m2"], "leftover_m": p["leftover_m"], "side_trim_m2": p["side_trim_m2"],
                        "patch_m2": p["patch_m2"], "reason": p.get("reason") or ";".join(p["flags"])})
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


def rolls_lines(ctx, table, names=None):
    """owner Q-49 A: one FIN.WP.MEMBRANE_ROLLS line per wet area and per roof, each alone: released (SOURCE_DERIVED)
    when the three readings of owner Q-58 give the same count, else a bounded line (low / high, the readings named);
    one BLOCKED_RFI line per held area or roof (no number, never 0)."""
    out = []
    for name in SYSTEMS:
        st = table["systems"].get(name) or {}
        for r in st.get("rows") or ():
            p = r.get("purchase")
            if p is None:
                continue
            rid = r["line_room_id"]
            nm = (names or {}).get((r["floor"], r["room_id"])) or {}
            inputs = {"system": name, "method": F3.METHOD_ID, "direction": p["direction"], "start": p["start"],
                      "strips": p["strips"], "upturn_only_strips": p["upturn_only_strips"],
                      "strip_length_m": p["strip_length_m"], "cut_m2": p["cut_m2"], "leftover_m": p["leftover_m"],
                      "side_trim_m2": p["side_trim_m2"], "patches": p["patches"], "patch_m2": p["patch_m2"],
                      "rolls_by_reading": p["rolls_by_reading"], "cutting_plan": p["cutting_plan"],
                      "layouts": p["layouts"], "flags": p["flags"]}
            formula = ("this area alone: of the four layouts (2 directions x 2 start walls) the one with the fewest "
                       "whole 1.00 x 10.00 m rolls, tie the shorter strip length (owner Q-49 A); strips by the owner's "
                       "method (Q-30, Q-24 addendum) with every uncovered upturn closed by an upturn-only strip or a "
                       "listed patch (MEMBRANE_FOLD_V3), packed by length into whole rolls (UP-WP-001)")
            if p["state"] == "RELEASED":
                out.append(_line(ctx, item_code="FIN.WP.MEMBRANE_ROLLS", unit="pcs", floor=r["floor"], room_id=rid,
                                 element="wp_rolls_to_buy", ev="SOURCE_DERIVED", net=p["rolls"], formula=formula,
                                 inputs=inputs, rule_id="UP-WP-LAY-001", name_en=nm.get("name_en"),
                                 name_ar=nm.get("name_ar")))
                continue
            b = p["rolls_bounded"]
            q = (f"{p['reason']}. The count depends on how the pieces the straight strips do not reach are cut "
                 "(upturn-only strips at outline steps, patches at corners and openings)")
            out.append(_line(ctx, item_code="FIN.WP.MEMBRANE_ROLLS", unit="pcs", floor=r["floor"], room_id=rid,
                             element="wp_rolls_to_buy", ev="BOUNDED_EXPOSURE", formula=formula, inputs=inputs,
                             rule_id="UP-WP-LAY-001", name_en=nm.get("name_en"), name_ar=nm.get("name_ar"),
                             bounded={"low": b["low"], "high": b["high"], "basis": q},
                             rfi={"question": q, "unlocks": rid}))
        for h in st.get("held") or ():
            q = (f"{h['reason']}: the area's outline is not established, so its membrane rolls are not counted "
                 "(owner Q-49 A counts each area alone; this one is held, not 0)")
            out.append(_line(ctx, item_code="FIN.WP.MEMBRANE_ROLLS", unit="pcs", floor=h["floor"],
                             room_id=h["room_id"], element="wp_rolls_to_buy", ev="BLOCKED_RFI",
                             formula="this area alone (owner Q-49 A)", inputs={"system": name, "name": h["name"]},
                             rule_id="UP-WP-LAY-001", rfi={"question": q, "unlocks": h["room_id"]}))
    return out


def summary(classes, decided, wet, flags, held, roofs, table, lines):
    s = AV.summary(classes, decided, wet, flags, held, roofs, table, lines)
    s["purchase"] = {k: {"total": v["purchase_total"], "held": [h["room_id"] for h in v["held"]],
                         "held_q58": v["held_q58"]} for k, v in table["systems"].items()}
    return s


def policy_record():
    return {"method": METHOD, "policy": POLICY_ID, "knowledge": KNOWLEDGE,
            "pieces": ["WET_ROOM_EVIDENCE_V1 (T-010)", "EXTERIOR_SPACES_V1 (T-071)", "MEMBRANE_FOLD_V3 (T-096)"],
            "builds_on": AV.METHOD,
            "owner_answers": ["Q-06 a", "Q-13 B", "Q-24", "Q-25", "Q-29", "Q-30 A", "Q-34 parked", "Q-35 C",
                              "Q-37 A", "Q-40 A", "Q-49 A"],
            "open": ["Q-58 (counts that depend on it are held, bounded)"],
            "purchase_rule": Q49_A, "items": sorted(ITEMS), "fold": F3.policy_record()}
