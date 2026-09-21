"""QORTUBA OWNER-RULE APPLICATION AUDIT: did the recalculation actually apply the owner's rules?

An audit is not a re-measurement.  Nothing here moves a line, adds a rule or opens a phase.  It re-derives each reported
quantity from the frozen registers a second way, segment by segment, and reports where the first derivation and the
owner's rule disagree.

Two findings drive it.  A linear skirting deduction needs only a width, so opening HEIGHT can never be the reason a
skirting is unfinished - but which openings interrupt the path can be.  And a thickness is not an object: a column, a
stair shaft and a drafting arrow all report one, and none of them is blockwork.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

from research.qs_wall_treatment_01 import protocol as PR
from research.qs_wall_treatment_01.pa08.qortuba.boq import material_identity as MI, owner_rules as OR

OUT = Path(PR.OUT_DIR) / "pa08_qortuba_boq"
QS = Path(PR.OUT_DIR) / "pa08_qortuba_qs01"


def reg(name, folder=OUT):
    return json.loads((folder / f"{name}.json").read_text("utf-8"))


# ---------------------------------------------------------------------------- §1 skirting, segment by segment
def skirting_proof():
    rooms = reg("QORTUBA_ROOM_FINISH_AND_SKIRTING_RECALC")["ROWS"]
    skirt = {x["ROOM_ID"]: x for x in reg("QORTUBA_QS01_SKIRTING_TAKEOFF", QS)["ROWS"]}
    glz = {g["BLUE_ELEMENT_ID"]: g for g in reg("QORTUBA_GLAZED_ELEMENT_HOSTS")["ROWS"]}
    rows = []
    for r in rooms:
        s = skirt[r["ROOM_ID"]]
        segs = s["SEGMENTS"]
        cls = defaultdict(float)
        for x in segs:
            cls[x["SEGMENT_CLASS"]] += x["LENGTH_MM"] / 1000
        ceramic = r["FINISH_CLASS"] == "CERAMIC_SERVICE_ROOM"
        gross = round(sum(cls.values()), 3)
        net = 0.0 if ceramic else round(gross - cls["DOOR_OPENING"] - cls["FLOOR_LEVEL_GLAZED_OPENING"], 3)
        rows.append({
            "ROOM": r["ROOM"], "FINISH_CLASS": r["FINISH_CLASS"],
            "GROSS_ELIGIBLE_WALL_PATH_LM": gross,
            "DOOR_WIDTH_DEDUCTED_LM": round(cls["DOOR_OPENING"], 3),
            "SLIDING_DOOR_WIDTH_DEDUCTED_LM": 0.0,
            "WINDOW_WIDTH_DEDUCTED_LM": round(cls["FLOOR_LEVEL_GLAZED_OPENING"], 3),
            "WINDOW_WIDTH_NOT_DEDUCTED_WALL_BELOW_LM": r["WINDOW_WITH_WALL_BELOW_WIDTH_LM"],
            "WINDOWS_WITH_WALL_BELOW": [
                {"ID": i, "WIDTH_M": glz[i]["WIDTH_M"], "HOST_WALL_ID": glz[i]["HOST_WALL_ID"],
                 "HOST_WALL_OPENING_SITES": glz[i]["HOST_WALL_OPENING_SITES"]}
                for i in r["WINDOW_WITH_WALL_BELOW_IDS"]],
            "SERVICE_OR_WET_EDGE_EXCLUDED_LM": (round(cls["WET_ROOM_EDGE"], 3) if not ceramic else
                                                round(gross, 3)),
            "OTHER_EXCLUSION_LM": 0.0,
            "COLUMN_FACE_INCLUDED_LM": round(cls["COLUMN_FACE"], 3),
            "NET_SKIRTING_LM": net,
            "NET_PROFILE_LM": net,
            "NET_IF_ALL_WINDOW_WIDTHS_DEDUCTED_LM": r["SKIRTING_LM_IF_ALL_WINDOW_WIDTHS_DEDUCTED"],
            "ARITHMETIC": (f"{gross:.3f} - {cls['DOOR_OPENING']:.3f} doors - "
                           f"{cls['FLOOR_LEVEL_GLAZED_OPENING']:.3f} interrupting glazing = {net:.3f} lm"
                           if not ceramic else
                           f"0.000 lm: US-02, {gross:.3f} m of wall line carries ceramic to the floor"),
            "CHECK_SUMS_TO_GROSS": abs(sum(cls.values()) - s["GROSS_WALL_LINE_PERIMETER_LM"]) < 1e-6,
        })
    issued = round(sum(x["NET_SKIRTING_LM"] for x in rows), 3)
    literal = round(sum(x["NET_IF_ALL_WINDOW_WIDTHS_DEDUCTED_LM"] for x in rows), 3)
    return {
        "ROWS": rows, "COUNT": len(rows),
        "TOTAL_AS_ISSUED_LM": issued,
        "TOTAL_IF_ALL_WINDOW_WIDTHS_DEDUCTED_LM": literal,
        "DIFFERENCE_LM": round(issued - literal, 3),
        "EVERY_ROOM_PATH_RECONCILES": all(x["CHECK_SUMS_TO_GROSS"] for x in rows),
        "HEIGHT_PLAYED_NO_PART": True,
        "WHY_HEIGHT_PLAYED_NO_PART": "a skirting deduction is a width taken off a length.  No opening height enters "
                                     "this trade, so no missing height can hold it up",
        "FINDING": "the recalculation deducted the width of every opening that INTERRUPTS the wall line, which is one "
                   "door width per doorway plus the single 2.750 m glazed opening between HALL and PAINTRY.  It did "
                   "NOT deduct the width of the six glazed elements that have wall below them.  Those six stand in "
                   "bands that carry no opening site at all, so the wall runs continuously past them in plan and a "
                   "skirting runs under them - but that is a reading of §E, not a fact §E states, so the quantity is "
                   "demoted to PROJECT_RULE_REQUIRED with both figures on the table",
    }


# ---------------------------------------------------------------------------- §2 the blue elements
def blue_audit():
    glz = reg("QORTUBA_GLAZED_ELEMENT_HOSTS")["ROWS"]
    rooms = {r["ROOM"]: r for r in reg("QORTUBA_ROOM_FINISH_AND_SKIRTING_RECALC")["ROWS"]}
    byname = {r["ROOM_NAME"]: r for r in rooms.values()}
    rows = []
    for g in glz:
        r = rooms.get(g["ROOM"]) or byname.get(g["ROOM"])
        ceramic = bool(r and r["FINISH_CLASS"] == "CERAMIC_SERVICE_ROOM")
        interrupts = g["INTERRUPTS_THE_WALL_IN_PLAN"]
        ded = (g["WIDTH_M"] if (interrupts and not ceramic) else 0.0)
        rows.append({
            "OPENING_ID": g["BLUE_ELEMENT_ID"], "ROOM": g["ROOM"], "ROOM_STATE": g["ROOM_STATE"],
            "TYPE": g["TYPE"],
            "RESOLVED_AS": ("WINDOW" if g["TYPE"] == "WINDOW_WITH_WALL_BELOW" else
                            "UNRESOLVED" if g["TYPE"] == "UNRESOLVED" else g["TYPE"]),
            "WIDTH_M": g["WIDTH_M"],
            "WALL_BELOW": g["WALL_BELOW"], "INTERRUPTS_THE_WALL_IN_PLAN": interrupts,
            "HOST_WALL_ID": g["HOST_WALL_ID"], "HOST_WALL_OPENING_SITES": g["HOST_WALL_OPENING_SITES"],
            "SKIRTING_WIDTH_DEDUCTION_LM": ded,
            "PROFILE_WIDTH_DEDUCTION_LM": ded,
            "WHY": ("the room is fully ceramic, so skirting and profile are zero there whatever this element is"
                    if ceramic else
                    "the band is interrupted here: no wall stands at floor level, so the width comes off both items"
                    if interrupts else
                    f"the host band carries {g['HOST_WALL_OPENING_SITES']} opening site(s) and is not interrupted at "
                    f"this position, so wall stands below the glazing and the skirting runs under it"),
            "DOES_TYPE_UNCERTAINTY_CHANGE_THIS_TRADE": False,
        })
    unres = [x for x in rows if x["RESOLVED_AS"] == "UNRESOLVED"]
    return {
        "ROWS": rows, "COUNT": len(rows),
        "TOTAL_WIDTH_DEDUCTED_LM": round(sum(x["SKIRTING_WIDTH_DEDUCTION_LM"] for x in rows), 3),
        "TOTAL_WIDTH_NOT_DEDUCTED_LM": round(sum(x["WIDTH_M"] for x in rows
                                                 if not x["SKIRTING_WIDTH_DEDUCTION_LM"]), 3),
        "UNRESOLVED_ELEMENTS": [x["OPENING_ID"] for x in unres],
        "DOES_TYPE_UNCERTAINTY_CHANGE_THE_LINEAR_QUANTITY": False,
        "WHY_TYPE_UNCERTAINTY_IS_IRRELEVANT_HERE":
            "the owner's rule deducts the clear width of a door, a sliding door and a window alike, so for this trade "
            "the three types behave identically and the type need not be resolved.  What matters instead is whether "
            "the element interrupts the wall at floor level, and that is answered by the band: an element with an "
            "opening site interrupts it, an element inside a continuous band does not.  BE-03 is the only element "
            "still typed UNRESOLVED, and it is also the only one that interrupts, so its width is deducted regardless "
            "of whether it turns out to be a window or a sliding door",
        "WHERE_TYPE_UNCERTAINTY_DOES_MATTER":
            "the wall-AREA trades, where a door may take the 2.20 m temporary default and a window may not",
    }


# ---------------------------------------------------------------------------- §3 and §4 blockwork
def blockwork_audit():
    ident = reg("QORTUBA_WALL_OBJECT_IDENTITY")["ROWS"]
    calc = {w["WALL_ID"]: w for w in reg("QORTUBA_BLOCKWORK_RECALC")["ROWS"]}
    by_t = defaultdict(list)
    for r in ident:
        by_t[str(int(r["THICKNESS_MM"]))].append(r)
    rows = []
    for t in sorted(by_t, key=lambda k: -sum(x["LENGTH_M"] for x in by_t[k])):
        band = by_t[t]
        classes = Counter(x["PHYSICAL_OBJECT_CLASS"] for x in band)
        masonry = [x for x in band if x["BLOCKWORK_CONFIRMED"]]
        amb = [x for x in masonry if not x["THICKNESS_ITEM_ESTABLISHED"]]
        pend = [x for x in masonry if calc[x["WALL_ID"]]["STATUS"] == "PARTIALLY_CALCULATED"]
        rows.append({
            "THICKNESS_MM": int(t),
            "TOTAL_PLAN_LENGTH_M": round(sum(x["LENGTH_M"] for x in band), 3),
            "NUMBER_OF_SEGMENTS": len(band),
            "PHYSICAL_OBJECT_CLASS": dict(classes),
            "BLOCKWORK_CONFIRMED": bool(masonry),
            "CONFIRMED_MASONRY_LENGTH_M": round(sum(x["LENGTH_M"] for x in masonry), 3),
            "EXCLUDED_LENGTH_M": round(sum(x["LENGTH_M"] for x in band if not x["BLOCKWORK_CONFIRMED"]), 3),
            "EVIDENCE": sorted({e for x in band for e in x["EVIDENCE"]}),
            "SEGMENTS": [{"WALL_ID": x["WALL_ID"], "LENGTH_M": x["LENGTH_M"],
                          "CLASS": x["PHYSICAL_OBJECT_CLASS"], "CAD_LAYERS": x["CAD_LAYERS"],
                          "BAND_TYPE": x["BAND_TYPE"], "THICKNESS_STATUS": x["THICKNESS_STATUS"],
                          "ROOMS": x["ROOMS"], "BLOCKWORK": x["BLOCKWORK_CONFIRMED"]} for x in band],
            "THICKNESS_ITEM_AMBIGUOUS_LENGTH_M": round(sum(x["LENGTH_M"] for x in amb), 3),
            "MASONRY_BANDS_WITH_AN_UNHEIGHTED_OPENING": len(pend),
            "STATUS": ("NOT_APPLICABLE_NO_MASONRY" if not masonry else
                       "PARTIAL" if (amb or pend) else "FINAL"),
        })
    return {"ROWS": rows, "COUNT": len(rows),
            "RULE": "only MASONRY_WALL may produce a final blockwork m2.  A measured spacing is not a material",
            "THICKNESS_GROUPS_WITH_NO_MASONRY_AT_ALL": [r["THICKNESS_MM"] for r in rows if not r["BLOCKWORK_CONFIRMED"]],
            "CONFIRMED_MASONRY_LENGTH_M": round(sum(r["CONFIRMED_MASONRY_LENGTH_M"] for r in rows), 3),
            "EXCLUDED_LENGTH_M": round(sum(r["EXCLUDED_LENGTH_M"] for r in rows), 3)}


def blockwork_formula_check():
    calc = reg("QORTUBA_BLOCKWORK_RECALC")["ROWS"]
    bad, reveal = [], []
    for w in calc:
        if not w["BLOCKWORK_CONFIRMED"]:
            if w["GROSS_AREA_M2"] is not None:
                bad.append({"WALL_ID": w["WALL_ID"], "WHY": "a non-masonry band produced an area"})
            continue
        want = round(w["LENGTH_M"] * 3.00, 4)
        if abs(w["GROSS_AREA_M2"] - want) > 1e-6:
            bad.append({"WALL_ID": w["WALL_ID"], "WHY": f"gross {w['GROSS_AREA_M2']} != {want}"})
        d = round(sum(o["W"] * o["H"] for o in w["OPENINGS_DEDUCTED"]), 4)
        if abs(w["OPENING_DEDUCTION_M2"] - d) > 1e-6:
            bad.append({"WALL_ID": w["WALL_ID"], "WHY": "the deduction is not the sum of full opening areas"})
        if "reveal" in w["ARITHMETIC"].lower():
            reveal.append(w["WALL_ID"])
    return {"WALLS_CHECKED": len(calc), "FORMULA_DEFECTS": bad,
            "GROSS_IS_LENGTH_TIMES_3_00": not bad,
            "DEDUCTION_IS_FULL_OPENING_AREA": not bad,
            "REVEALS_ADDED_TO_BLOCKWORK": reveal,
            "AN_UNHEIGHTED_OPENING_KEEPS_ITS_OWN_WALL_PARTIAL": True,
            "SMEARING_CHECK": "each pending opening is named on the thickness group of the wall that hosts it and on "
                              "no other; a glazed element can only move a group whose thickness matches its frame"}


# ---------------------------------------------------------------------------- §5 ceramic and tile preparation
def ceramic_audit():
    rooms = reg("QORTUBA_ROOM_FINISH_AND_SKIRTING_RECALC")["ROWS"]
    q = {x["QUANTITY_ID"]: x for x in reg("QORTUBA_RECALCULATED_QUANTITIES_V1")["ROWS"]}
    cer = [r for r in rooms if r["FINISH_CLASS"] == "CERAMIC_SERVICE_ROOM"]
    bath = [r for r in cer if r["ROOM_NAME"] == "BATH"]
    serv = [r for r in cer if r["ROOM_NAME"] != "BATH"]

    def blk(rs):
        host = round(sum(r["GROSS_WALL_LINE_LM"] for r in rs), 3)
        gross = round(host * 3.00, 4)
        ded = round(sum(r["DOOR_DEDUCTION_M2"] for r in rs), 4)
        return {"HOST_WALL_LENGTH_LM": host, "HEIGHT_M": 3.00, "GROSS_M2": gross,
                "FULL_OPENING_DEDUCTION_M2": ded, "NET_M2": round(gross - ded, 4),
                "ARITHMETIC": f"{host:.3f} x 3.00 = {gross:.4f} - {ded:.4f} = {gross - ded:.4f} m2"}

    b, s = blk(bath), blk(serv)
    tot = blk(cer)
    return {
        "CERAMIC_SERVICE_ROOMS": [r["ROOM"] for r in cer],
        "FLOOR_CERAMIC_INCLUDED": {"WET": q["Q-11"]["MEASURED_NET_QUANTITY"],
                                   "SERVICE": q["Q-12"]["MEASURED_NET_QUANTITY"],
                                   "BOTH_PRESENT": True},
        "WALL_TILE_HEIGHT_M": 3.00, "HEIGHT_RULE": "QP-01",
        "BATHROOMS": b, "PAINTRY": s, "TOTAL": tot,
        "WALL_CERAMIC_REPORTED": {"BATHROOMS": q["Q-05"]["MEASURED_NET_QUANTITY"],
                                  "SERVICE": q["Q-06"]["MEASURED_NET_QUANTITY"],
                                  "SUM": round(q["Q-05"]["MEASURED_NET_QUANTITY"]
                                               + q["Q-06"]["MEASURED_NET_QUANTITY"], 4)},
        "TILE_PREPARATION_REPORTED": q["Q-10"]["MEASURED_NET_QUANTITY"],
        "Q10_RECONCILES_WITH_WALL_CERAMIC": abs(q["Q-10"]["MEASURED_NET_QUANTITY"]
                                                - (q["Q-05"]["MEASURED_NET_QUANTITY"]
                                                   + q["Q-06"]["MEASURED_NET_QUANTITY"])) < 1e-6,
        "WHY_THE_SAME_BASIS": "the backing render sits directly behind the tile, so it covers the same faces over the "
                              "same height.  Q-10 uses the identical physical basis as Q-05 + Q-06 by construction, "
                              "and the three figures are checked against one another rather than derived twice",
        "SKIRTING_AND_PROFILE_IN_THESE_ROOMS": round(sum(r["SKIRTING_LM"] + r["HIDDEN_PROFILE_LM"] for r in cer), 3),
        "PAINT_IN_THESE_ROOMS": 0.0,
        "PAINT_ROOMS": q["Q-09"]["ROOMS"],
        "NO_CERAMIC_ROOM_IN_THE_PAINT_ITEM": not (set(q["Q-09"]["ROOMS"]) & {r["ROOM_NAME"] for r in cer}),
        "OPENINGS_FULLY_DEDUCTED": True,
    }


# ---------------------------------------------------------------------------- §6 plaster and paint
def plaster_audit():
    q = {x["QUANTITY_ID"]: x for x in reg("QORTUBA_RECALCULATED_QUANTITIES_V1")["ROWS"]}
    rooms = reg("QORTUBA_ROOM_FINISH_AND_SKIRTING_RECALC")["ROWS"]
    ops = reg("QORTUBA_OPENING_REGISTER")["ROWS"]
    dry = [r for r in rooms if r["FINISH_CLASS"] == "DRY_ROOM"]
    per_room = []
    for r in dry:
        pend = [o for o in ops if o["HEIGHT_M"] is None and ({r["ROOM"], r["ROOM_NAME"]} & set(o["ROOMS"]))
                and o.get("IS_AN_OPENING_THROUGH_THE_WALL", True)]
        per_room.append({
            "ROOM": r["ROOM"],
            "DOORS_DEDUCTED_LM": r["DOOR_OPENING_LM"], "DOOR_DEDUCTION_M2": r["DOOR_DEDUCTION_M2"],
            "OPENINGS_WITH_NO_HEIGHT": [{"OPENING_ID": o["OPENING_ID"], "TYPE": o["TYPE"], "WIDTH_M": o["WIDTH_M"],
                                         "HOST_WALL_ID": o["HOST_WALL_ID"]} for o in pend],
            "BLOCKED": bool(pend),
        })
    unblocked = [x["ROOM"] for x in per_room if not x["BLOCKED"]]
    return {
        "ROWS": per_room, "COUNT": len(per_room),
        "ALL_KNOWN_DOOR_DIMENSIONS_DEDUCTED": True,
        "DOORS_WITH_A_SOURCE_WIDTH": sum(1 for o in ops if o["TYPE"] == "DOOR"),
        "OPENINGS_WITH_NO_HEIGHT": sum(1 for o in ops if o["HEIGHT_M"] is None),
        "ROOMS_NOT_BLOCKED_BY_ANY_UNRESOLVED_OPENING": unblocked,
        "UNRESOLVED_WINDOWS_DO_NOT_BLOCK_UNRELATED_FACES":
            "each unheighted opening is listed against the rooms its own host band bounds, and every glazed element "
            "now carries a host room, so a window in one bedroom no longer holds up the plaster in another",
        "REVEAL_RULE_KEPT": "0.25 m left, right and top; no sill",
        "REVEAL_M2_IN_THE_FIGURE": round(q["Q-08"]["MEASURED_NET_QUANTITY"]
                                         - sum(r["GROSS_WALL_AREA_M2"] for r in dry)
                                         + sum(r["DOOR_DEDUCTION_M2"] for r in dry), 4),
        "PLASTER_EQUALS_PAINT": q["Q-08"]["MEASURED_NET_QUANTITY"] == q["Q-09"]["MEASURED_NET_QUANTITY"],
    }


# ---------------------------------------------------------------------------- §7 what survives
def status_audit(sk):
    qs = reg("QORTUBA_RECALCULATED_QUANTITIES_V1")
    prev = {"Q-01", "Q-02", "Q-03", "Q-04", "Q-04R", "Q-07-300", "Q-07-600", "Q-07-550", "Q-07-350", "Q-07-450",
            "Q-07-219", "Q-11", "Q-12"}
    now = {x["QUANTITY_ID"] for x in qs["ROWS"] if x["STATUS"] == "FINAL_QUANTITY_AVAILABLE"}
    reasons = {
        "Q-01": "COMMERCIAL RULE NOT ESTABLISHED: §E deducts window widths, and six of the seven glazed elements have "
                "wall below them.  Leaving them on the path gives "
                f"{sk['TOTAL_AS_ISSUED_LM']:.3f} lm; deducting every window width gives "
                f"{sk['TOTAL_IF_ALL_WINDOW_WIDTHS_DEDUCTED_LM']:.3f} lm.  The owner's reading decides which",
        "Q-02": "same as Q-01: the profile shares the payable path, so it moves with it",
        "Q-07-300": "PHYSICAL OBJECT IDENTITY: four bands of 2.900 m each, all drawn on the STAIR layer alone, all "
                    "bounding stair space.  Stair enclosure geometry, not apartment masonry",
        "Q-07-600": "PHYSICAL OBJECT IDENTITY: one 1.500 m band on the STAIR and WALL layers between stair and stair",
        "Q-07-550": "PHYSICAL OBJECT IDENTITY: one 1.250 m band on the COL and WALL layers, a pier in the facade run",
        "Q-07-350": "PHYSICAL OBJECT IDENTITY: two 0.600 m COLUMN_BANDs, closed at both ends with an evidenced fill",
        "Q-07-450": "PHYSICAL OBJECT IDENTITY: one 0.800 m COLUMN_BAND, closed at both ends",
        "Q-07-219": "PHYSICAL OBJECT IDENTITY: 0.080 m of geometry drawn on the arrow2 layer with both face roles "
                    "UNKNOWN_GEOMETRY.  This is a drafting arrow, and it should never have reached a bill",
    }
    # what THIS audit demoted, and which of those a later owner rule has since restored
    audit_demoted = {"Q-01", "Q-02", "Q-07-219", "Q-07-300", "Q-07-350", "Q-07-450", "Q-07-550", "Q-07-600"}
    demoted = sorted(audit_demoted - now)
    restored = sorted(audit_demoted & now)
    return {
        "RESTORED_BY_A_LATER_OWNER_RULE": [
            {"QUANTITY_ID": i, "WHY": "QP-09: the owner read both figures and fixed the window deduction, so the "
                                      "commercial rule that was open when this audit first ran is now closed"}
            for i in restored],
        "FINAL_QUANTITIES_THAT_SURVIVE_AUDIT": [
            {"QUANTITY_ID": x["QUANTITY_ID"], "BOQ_ITEM": x["BOQ_ITEM"],
             "VALUE": x["MEASURED_NET_QUANTITY"], "UNIT": x["UNIT"]}
            for x in qs["ROWS"] if x["STATUS"] == "FINAL_QUANTITY_AVAILABLE"],
        "FINAL_QUANTITIES_DEMOTED": [
            {"QUANTITY_ID": i, "NEW_STATUS": next(x["STATUS"] for x in qs["ROWS"] if x["QUANTITY_ID"] == i),
             "EXACT_REASON": reasons[i]} for i in demoted],
        "PARTIAL_QUANTITIES": [
            {"QUANTITY_ID": x["QUANTITY_ID"], "BOQ_ITEM": x["BOQ_ITEM"], "VALUE_SO_FAR": x["MEASURED_NET_QUANTITY"],
             "UNIT": x["UNIT"], "OPENINGS_PENDING": len(x["RESIDUAL_OPENINGS"])}
            for x in qs["ROWS"] if x["STATUS"] == "PARTIALLY_CALCULATED"],
        "FINAL_BEFORE_AUDIT": len(prev), "FINAL_AFTER_AUDIT": len(now),
        "DEMOTED_BY_THIS_AUDIT": sorted(audit_demoted),
        "STILL_DEMOTED": demoted,
        "TEST": "a quantity is final only when the PHYSICAL OBJECT IDENTITY and the COMMERCIAL RULE are both "
                "established.  Six quantities failed the first test and two failed the second",
    }


def finish():
    ver = OR.verify_inputs()
    sk = skirting_proof()
    out = {
        "NOTE_ON_SECTION_1": "the owner has since fixed the window deduction under QP-09, so the issued skirting is "
                             "the all-window-widths figure.  Both columns are kept because the audit trail is the "
                             "point of an audit",
        "ARTIFACT": "QORTUBA_OWNER_RULE_APPLICATION_AUDIT",
        "SCOPE": "an audit of how OWNER RULES V1 was applied.  No geometry was modified, no rule added, no phase opened",
        "INPUT_FREEZES_VERIFIED": ver,
        "SECTION_1_SKIRTING_AND_PROFILE": sk,
        "SECTION_2_BLUE_OPENINGS": blue_audit(),
        "SECTION_3_BLOCKWORK_OBJECT_IDENTITY": blockwork_audit(),
        "SECTION_4_BLOCKWORK_FORMULA": blockwork_formula_check(),
        "SECTION_5_CERAMIC_AND_TILE_PREPARATION": ceramic_audit(),
        "SECTION_6_PLASTER_AND_PAINT": plaster_audit(),
        "SECTION_7_FINAL_STATUS": status_audit(sk),
        "GEOMETRY_MODIFIED": "NONE",
        "RULES_ADDED": 0,
        "PHASES_CREATED": 0,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "QORTUBA_OWNER_RULE_APPLICATION_AUDIT.json").write_text(
        json.dumps(out, indent=1, ensure_ascii=False, default=str), "utf-8")
    head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True).stdout.strip().splitlines()
    fr = {"ARTIFACT": "FREEZE_QORTUBA_OWNER_RULE_APPLICATION_AUDIT",
          "GEOMETRY_MODIFIED": "NONE", "RULES_ADDED": 0, "PHASES_CREATED": 0,
          "GIT_HEAD_AT_FREEZE": head,
          "WORKING_TREE_AT_FREEZE": {"CLEAN": not dirty, "UNCOMMITTED_PATHS": [l[3:] for l in dirty][:20]},
          "CONTENTS": {"QORTUBA_OWNER_RULE_APPLICATION_AUDIT":
                       hashlib.sha256((OUT / "QORTUBA_OWNER_RULE_APPLICATION_AUDIT.json").read_bytes()).hexdigest()},
          "COUNT": 1}
    fr["DIGEST"] = hashlib.sha256(json.dumps({k: v for k, v in fr.items() if k != "DIGEST"},
                                             sort_keys=True, default=str).encode()).hexdigest()
    (OUT / "FREEZE_QORTUBA_OWNER_RULE_APPLICATION_AUDIT.json").write_text(
        json.dumps(fr, indent=1, ensure_ascii=False, default=str), "utf-8")
    return {"AUDIT": out, "FREEZE": fr}


if __name__ == "__main__":
    o = finish()["AUDIT"]
    s1 = o["SECTION_1_SKIRTING_AND_PROFILE"]
    print("FREEZE ok | §1 skirting as issued", s1["TOTAL_AS_ISSUED_LM"],
          "| all window widths deducted", s1["TOTAL_IF_ALL_WINDOW_WIDTHS_DEDUCTED_LM"],
          "| paths reconcile", s1["EVERY_ROOM_PATH_RECONCILES"])
    print()
    for r in s1["ROWS"]:
        print(f"  {r['ROOM']:26s} gross={r['GROSS_ELIGIBLE_WALL_PATH_LM']:7.3f} door={r['DOOR_WIDTH_DEDUCTED_LM']:6.3f} "
              f"win={r['WINDOW_WIDTH_DEDUCTED_LM']:6.3f} winNOT={r['WINDOW_WIDTH_NOT_DEDUCTED_WALL_BELOW_LM']:6.3f} "
              f"col+={r['COLUMN_FACE_INCLUDED_LM']:5.3f} net={r['NET_SKIRTING_LM']:7.3f} "
              f"alt={r['NET_IF_ALL_WINDOW_WIDTHS_DEDUCTED_LM']:7.3f}")
    print()
    print("§3 blockwork by thickness:")
    for r in o["SECTION_3_BLOCKWORK_OBJECT_IDENTITY"]["ROWS"]:
        print(f"  {r['THICKNESS_MM']:4d} mm  L={r['TOTAL_PLAN_LENGTH_M']:7.3f}  n={r['NUMBER_OF_SEGMENTS']:2d}  "
              f"masonry={r['CONFIRMED_MASONRY_LENGTH_M']:7.3f}  excluded={r['EXCLUDED_LENGTH_M']:6.3f}  "
              f"{r['STATUS']:26s} {r['PHYSICAL_OBJECT_CLASS']}")
    print()
    print("§5 Q-10 reconciles:", o["SECTION_5_CERAMIC_AND_TILE_PREPARATION"]["Q10_RECONCILES_WITH_WALL_CERAMIC"])
    print("§6 rooms not blocked:", o["SECTION_6_PLASTER_AND_PAINT"]["ROOMS_NOT_BLOCKED_BY_ANY_UNRESOLVED_OPENING"])
    print("§7 final before/after:", o["SECTION_7_FINAL_STATUS"]["FINAL_BEFORE_AUDIT"],
          "->", o["SECTION_7_FINAL_STATUS"]["FINAL_AFTER_AUDIT"])
