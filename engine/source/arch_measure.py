"""ARCHITECTURAL MEASUREMENT (M9 S2) - canonical BOQ lines per room from the spaces of arch_rooms (generic, stdlib).

    measure(floor_result, *, floor, project_id, revision_set_sha256, facts=None, floor_above_level_m=None, documents=())
        -> {"rooms": [...], "lines": [...], "openings": [...], "unresolved": [...]}
    validate_facts(facts) -> the facts, or FactsError

S5: zones of open spaces (drawn lines) measured as rooms (PROVISIONAL); shared wet doorways counted once; ceilings
with double height (none under a void above; the ceiling over a void its own line); stair-well ceilings BLOCKED;
guardrails on open flight sides only; an opening inventory with host wall and height state.
Rules (rule set 1.5.0, every line names its rule and version):
    floor finish     UP-CER-001  net = the face area, obstructions inside the room (holes) deducted; gross / deductions
                                 kept. Dry, service and circulation rooms: porcelain; wet rooms: wet-room floor tile
    ceiling          plan area of the room (the same face); the ceiling build-up / bulkheads are not in a plan
                     (PROVISIONAL); stairs, shafts, voids and external spaces carry none
    skirting         UP-CER-002 / -003: the wall and column faces of the room (outer boundary + obstructions); door
                     and passage openings are not skirted (deducted by construction); a sill window is skirted
                     (flagged); a wet room: UP-CER-004 - none when the wall tile is full height, else the run
    waterproofing    UP-WP-001 floor, UP-WP-003 v1.1.0 doorway piece = door width x wall thickness per door,
                     UP-WP-002 v2.0.0 upturn = the full one-sided boundary (doors included) x 0.20 m
    wall finishes    UP-CER-009 heights through the wall_height ladder (a source finish height, an owner project fact,
                     or a derived clear height = the plan-level interval minus every required component, each with
                     its authority); area = wall run x height - openings (door / window widths x their heights); an
                     unknown opening height makes the net a BOUNDED range (no deduction ... full-height deduction)
    openings         each door / window / passage of the floor, with its width; height from the facts or BLOCKED
A MIXED space of one kind (an open plan) is measured as one room; a MIXED space of different kinds, a MERGED space
and an UNLABELLED space carry their area only (ARCH.SPACE) and the question that resolves them.
Project-agnostic; stdlib only.
"""

from __future__ import annotations

import hashlib
import math
from collections import Counter

from engine.source import arch_floor as AF
from engine.source import arch_rooms as AR
from engine.source import boq_line as BL
from engine.source import plane_poly as PP
from engine.source import rule_store as RS
from engine.source import tile_layout as TL
from engine.source import wall_height as WH

POLICY_ID = "ARCH_MEASURE_V3"
RULE_SET = RS.LATEST_APPROVED
FACTS_SCHEMA = "URBAN_ARCH_FACTS_V1"
FINISH_KIND = {AR.DRY: "DRY", AR.SERVICE: "DRY", AR.CIRCULATION: "DRY", AR.WET: "WET"}
NO_FINISH = (AR.STAIR, AR.SHAFT, AR.VOID, AR.EXTERIOR)
TRADES = ("PLASTER", "PAINT", "WALL_TILE")


class FactsError(ValueError):
    pass


def _need_authority(v, where):
    if not isinstance(v, dict) or v.get("value_m") is None or not v.get("authority"):
        raise FactsError(f"{where}: a fact needs value_m and its authority (source)")


def validate_facts(facts):
    if not facts:
        return {}
    if facts.get("schema") != FACTS_SCHEMA:
        raise FactsError(f"facts schema must be {FACTS_SCHEMA}")
    for fl, trades in (facts.get("wall_heights") or {}).items():
        for tr, v in trades.items():
            if tr not in TRADES:
                raise FactsError(f"wall_heights.{fl}: unknown trade {tr}")
            _need_authority(v, f"wall_heights.{fl}.{tr}")
    for fl, comps in (facts.get("height_components") or {}).items():
        for k, v in comps.items():
            _need_authority(v, f"height_components.{fl}.{k}")
    for k, v in (facts.get("opening_heights") or {}).items():
        _need_authority(v, f"opening_heights.{k}")
    for fl, st in (facts.get("stairs") or {}).items():
        if st.get("riser_m") is not None:
            _need_authority(st["riser_m"], f"stairs.{fl}.riser_m")
    return facts


def _ref(rule_id):
    try:
        return RS.rule_ref(rule_id, RULE_SET)
    except KeyError:
        # ARCH_TAKEOFF_V2.3: a rule of the engineering knowledge registry (never reached by V1 .. V2.2, which name
        # rule-store rules only)
        from engine.source import knowledge as K
        return K.ref(rule_id)


def room_id(floor, face_id):
    return f"{floor}-R{hashlib.sha256(face_id.encode()).hexdigest()[:6].upper()}"


def _names(codes):
    en = " + ".join(AR.LEX[c][0] for c in codes) if codes else AR.UNNAMED[0]          # " / " separates AR / EN
    ar = " + ".join(AR.LEX[c][1] for c in codes) if codes else AR.UNNAMED[1]
    return en, ar


def _kind(space):
    """the one finish kind of a space: a single room kind, or an OPEN PLAN of rooms whose kinds all take the dry
    finish (living + dining + pantry + corridor ...: DRY / SERVICE / CIRCULATION); otherwise None (not measured)."""
    kinds = sorted({AR.LEX[c][2] for c in space["codes"]})
    if len(kinds) == 1:
        return kinds[0]
    if kinds and all(FINISH_KIND.get(k) == "DRY" for k in kinds):
        return AR.DRY if AR.DRY in kinds else kinds[0]
    return None


def _run_lengths(space):
    """one-sided boundary lengths of the room by what they are (metres)."""
    o, h = space["outer_role_lm"], space["hole_role_lm"]
    wall = o.get("WALL", 0.0) + h.get("WALL", 0.0) + h.get("WALL_CAP", 0.0)
    col = o.get("COLUMN", 0.0) + h.get("COLUMN", 0.0)
    door = o.get("DOOR_THRESHOLD", 0.0) + o.get("DOOR_CLOSURE", 0.0)
    passage = o.get("PASSAGE_THRESHOLD", 0.0)
    win_thr = o.get("WINDOW_THRESHOLD", 0.0)
    glazing = o.get("WINDOW", 0.0)
    boundary = sum(o.values()) + sum(h.values())
    other = boundary - (wall + col + door + passage + win_thr + glazing)
    return {"wall": wall, "column": col, "door": door, "passage": passage, "window_threshold": win_thr,
            "glazing_edge": glazing, "other": max(other, 0.0), "boundary": boundary, "perimeter": space["perimeter_lm"]}


def _sk_ded(runs):
    out = [{"what": "door / passage openings", "lm": round(runs["door"] + runs["passage"], 6)}]
    if runs["glazing_edge"] > 1e-6:
        out.append({"what": "glazing edge (floor-level window line)", "lm": round(runs["glazing_edge"], 6)})
    if runs["other"] > 1e-6:
        out.append({"what": "boundary that is not a wall / column face", "lm": round(runs["other"], 6)})
    return out


def _rect_dims(space):
    ab = TL.rectangle({"polygon": space["polygon_m"]}) if not space["holes"] else None
    return ab


def _dims_text(space, unit_m=None):
    ab = _rect_dims(space)
    if ab:
        return f"{ab[0]:.2f} x {ab[1]:.2f} m"
    return f"polygon {len(space['polygon_m'])} vertices, perimeter {space['perimeter_lm']:.2f} m" + \
        (f", {space['holes']} obstruction(s)" if space["holes"] else "")


def heights(floor, space_level, floor_above_level, facts):
    """per trade: the governing finish height (wall_height ladder) with every candidate kept."""
    facts = facts or {}
    out = {}
    interval = None
    if space_level is not None and floor_above_level is not None and floor_above_level > space_level:
        interval = {"value_m": round(floor_above_level - space_level, 6),
                    "authority": f"PLAN_LEVEL_TEXTS: floor above {floor_above_level:+.2f} - this room {space_level:+.2f}"}
    comps = (facts.get("height_components") or {}).get(floor) or (facts.get("height_components") or {}).get("*") or {}
    for tr in TRADES:
        cands = []
        src = ((facts.get("wall_heights") or {}).get(floor) or (facts.get("wall_heights") or {}).get("*") or {}).get(tr)
        if src:
            kind = "SOURCE_FINISH_HEIGHT" if src["authority"].upper().startswith("SOURCE") else "OWNER_PROJECT_FACT"
            cands.append(WH.candidate(kind, src["value_m"], src["authority"]))
        if interval:
            need = {"soffit_zone_m": True, "ceiling_zone_m": tr != "PLASTER", "floor_buildup_m": True}
            cc = {k: dict(comps.get(k) or {}, required=req) for k, req in need.items()}
            d = WH.derive(interval["value_m"], interval["authority"], cc)
            cands.append(WH.candidate("DERIVED_CLEAR_HEIGHT", d["value_m"], d["formula"] if d["state"] == WH.ESTABLISHED
                                      else None, missing=d.get("missing")))
        cands.append(WH.candidate("FLOOR_TO_FLOOR", interval and interval["value_m"], interval and interval["authority"]))
        out[tr] = WH.resolve({"floor": floor, "trade": tr}, cands)
    out["_interval"] = interval
    return out


def _line(ctx, *, item_code, room, element, unit, net, formula, inputs, rule_id, ev=None, gross=None,
          deductions=(), rfi=None, notes="", bounded=None):
    ref = _ref(rule_id) if rule_id else {"rule_id": POLICY_ID, "version": "1", "rule_set": RULE_SET,
                                         "rule_set_digest": RS.rule_set(RULE_SET)["digest"]}
    if ev is None:
        ev = "SOURCE_DERIVED" if net is not None else ("BOUNDED_EXPOSURE" if bounded else "BLOCKED_RFI")
    return BL.make_line(project_id=ctx["project_id"], revision_set_sha256=ctx["revision_set_sha256"],
                        item_code=item_code, unit=unit, evidence_state=ev,
                        measured_net=net if ev in BL.QUANTITY_STATES else None,
                        element_id=f"{room['room_id']}:{element}", floor=room["floor"], room_id=room["room_id"],
                        room_name_en=room["name_en"], room_name_ar=room["name_ar"], physical_element=element,
                        gross=gross, deductions=deductions, formula=formula, inputs=inputs,
                        documents=ctx["documents"], geometry_source="CAD_VECTOR",
                        geometry_confidence="EXACT_FACE" if ev in BL.QUANTITY_STATES else "NOT_ESTABLISHED",
                        rule_id=ref["rule_id"], rule_version=ref["version"], rule_set=ref["rule_set"],
                        rule_set_digest=ref["rule_set_digest"], rfi=rfi, notes=notes, bounded_range=bounded)


def _wall_finish_rs(ctx, room, tr, code, run, H, h, openings, oh, sp, floor, unresolved, height_of=None):
    """ARCH_TAKEOFF_V2.2 (finding F-24): one wall-finish line from the room's own boundary (engine.source.release_safety:
    each opening deducted by its length on THIS boundary; checked; a range where a deduction is unknown; REVIEW where
    the boundary does not add up)."""
    from engine.source import release_safety as RSF
    rid = room["room_id"]
    r = RSF.wall_finish(run_lm=run, height_m=H, openings=openings, opening_heights=oh, detail=sp["boundary_detail"],
                        **({"height_of": height_of} if height_of is not None else {}))
    inputs = {"wall_run_lm": round(run, 6), "height_m": H, "height_authority": h["authority"],
              "height_governing": h["governing"], "decomposition": r["decomposition"], "policy": RSF.POLICY_ID}
    dd = [dict(d, what=f"{d['what']}: {d['lm_on_this_boundary']:.3f} m on this boundary x {d['height_m']:.2f} m")
          for d in r["deductions"]]
    formula = "wall run x height - each opening's own length on this boundary x its height (F-24)"
    if r["state"] == RSF.GEOMETRY_INCONSISTENT:
        q = (f"{RSF.GEOMETRY_INCONSISTENT} ({tr}): the room boundary does not add up - " + "; ".join(r["checks"]) +
             " - no quantity is released until the boundary is reviewed")
        unresolved.append({"room_id": rid, "floor": floor, "item": code, "reason": q})
        return _line(ctx, item_code=code, room=room, element=tr.lower(), unit="m2", net=None, gross=round(r["gross"], 6),
                     deductions=dd, formula=formula, inputs=dict(inputs, checks=r["checks"]), rule_id="UP-CER-009",
                     rfi={"question": q, "unlocks": rid})
    if r["state"] == "RANGE":
        parts = []
        if r["missing_heights"]:
            parts.append(f"{len(r['missing_heights'])} opening height(s) not established")
        und = r["decomposition"]["undeducted_opening_lm"]
        if und > RSF.TOL_M:
            parts.append(f"{und:.2f} m of boundary is an opening with no established deduction (a door closed only by "
                         "its leaf, glazing drawn on the room face, or an edge that is wall and something else) - "
                         "low: deducted at the full finish height, high: not deducted")
        q = f"{tr} net is a range: " + "; ".join(parts)
        unresolved.append({"room_id": rid, "floor": floor, "item": code, "reason": q})
        return _line(ctx, item_code=code, room=room, element=tr.lower(), unit="m2", net=None,
                     bounded={"low": round(r["low"], 6), "high": round(r["high"], 6), "basis": q},
                     gross=round(r["gross"], 6), deductions=dd, formula=formula,
                     inputs=dict(inputs, missing_heights=r["missing_heights"]), rule_id="UP-CER-009",
                     rfi={"question": q, "unlocks": rid})
    if height_of is not None:
        # ARCH_TAKEOFF_V2.8: a window is deducted by its own band; only a window without a sill keeps the assumption
        assumed = any("WINDOW_POSITION_ASSUMED" in str(d.get("height_authority")) for d in r["deductions"])
        formula = "wall run x height - each opening's own length on this boundary x its height inside the band " \
                  "[min(head, H) - max(sill, 0)] (F-24, UP-OPEN-SCHED-001)"
    else:
        assumed = any(o["kind"] == "WINDOW" for o in openings)
    return _line(ctx, item_code=code, room=room, element=tr.lower(), unit="m2", net=round(r["net"], 6),
                 gross=round(r["gross"], 6), deductions=dd, formula=formula, inputs=inputs, rule_id="UP-CER-009",
                 notes=("WINDOW_POSITION_ASSUMED: sill / head levels are not in a plan - each window is deducted at "
                        "its full height inside the finish height") if assumed else "")


def measure(fr, *, floor, project_id, revision_set_sha256, facts=None, floor_above_level_m=None, documents=(),
            floor_level_m=None, release_safety=False, owner_scope=False, door_height=None, piece_box=False,
            v28=None):
    """release_safety (ARCH_TAKEOFF_V2.2 only): wall finishes and skirting through engine.source.release_safety (the
    boundary detail of every face is required); False is the V1 / V2 / V2.1 path, unchanged.
    owner_scope (ARCH_TAKEOFF_V2.3 only): the owner wet-area scope and the surfaces an approved rule answers
    (engine.source.owner_finish_scope, knowledge registry 1.0.0); door_height(opening) -> {"value_m", "state"} for the
    door jamb plaster. False is the V1 .. V2.2 path, unchanged.
    piece_box (ARCH_TAKEOFF_V2.6 only, D-V26-07): the doorway piece of a door closed by its leaf and the wall's other
    face is the box between the two closures when its face runs on past them between wall lines
    (arch_completeness.closure_box); False is the V1 .. V2.5 path, unchanged.
    v28 (ARCH_TAKEOFF_V2.8 only): {"evidence": arch_v28.Evidence, "schedule": {opening_id: opening record},
    "height_of": arch_v28.height_of(...)} - the room heights from the drawing's evidence hierarchy, each opening
    deducted by its own band, floor-level glazing not skirted and an unknown sill not skirted with certainty, the
    opening inventory with height / sill / head / class; None is the V1 .. V2.7.1 path, unchanged."""
    if v28:
        from engine.source import arch_v28 as AV28
    if owner_scope:
        from engine.source import owner_finish_scope as OFS
    facts = validate_facts(facts) or {}
    ctx = {"project_id": project_id, "revision_set_sha256": revision_set_sha256, "documents": list(documents)}
    rooms, lines, unresolved = [], [], []
    ops = fr["openings_by_id"]
    closure_pieces = {}                     # door -> its doorway piece face (S4: closed on both wall faces)
    for f in fr.get("faces") or ():
        if f["class"] == "DOORWAY" and len(f.get("closure_ids") or ()) >= 2:
            keys = {c.rsplit("|", 1)[0] for c in f["closure_ids"]}
            if len(keys) == 1:
                closure_pieces[keys.pop()] = f
    done_pieces = set()
    box_recs = []                           # ARCH_TAKEOFF_V2.6 (D-V26-07): the doorway boxes tried, with their outcome
    wp_door_owner = {}                      # S5: a door between two wet spaces has ONE doorway piece (UP-WP-003)
    for sp in sorted(fr["spaces"], key=lambda s: (-s["area_m2"], s["face_id"])):
        rid = room_id(floor, sp["face_id"])
        en, ar = _names(sp["codes"])
        kind = _kind(sp)
        cls = sp["class"]
        measured_as_room = cls == "ROOM" or (cls == "MIXED" and kind is not None)
        open_plan = cls == "MIXED" and kind is not None and len({AR.LEX[c][2] for c in sp["codes"]}) > 1
        lvl = sp["levels_m"][0] if len(sp["levels_m"]) == 1 else floor_level_m
        runs = _run_lengths(sp)
        doors = [ops[i] for i in sp["opening_ids"] if ops[i]["kind"] == "DOOR"]
        windows = [ops[i] for i in sp["opening_ids"] if ops[i]["kind"] == "WINDOW"]
        passages = [ops[i] for i in sp["opening_ids"] if ops[i]["kind"] == "PASSAGE"]
        room = {"room_id": rid, "floor": floor, "face_id": sp["face_id"], "class": cls, "codes": sp["codes"],
                "kind": kind, "name_en": en, "name_ar": ar, "area_m2": round(sp["area_m2"], 6),
                "gross_m2": round(sp["gross_outer_m2"], 6), "obstruction_m2": round(sp["hole_area_m2"], 6),
                "obstructions": sp["holes"], "perimeter_lm": round(sp["perimeter_lm"], 6),
                "runs_lm": {k: round(v, 6) for k, v in runs.items()}, "dims": _dims_text(sp),
                "rect": _rect_dims(sp), "level_m": lvl, "doors": [d["opening_id"] for d in doors],
                "door_closures": len(sp["closure_ids"]), "windows": [w["opening_id"] for w in windows],
                "passages": [p["opening_id"] for p in passages], "issue": sp.get("issue"), "polygon": sp["polygon"],
                "hole_polygons": sp["hole_polygons"], "point": sp.get("point"), "polygon_m": sp["polygon_m"],
                "hole_polygons_m": sp["hole_polygons_m"], "open_plan": open_plan,
                "symbols_inside": sp.get("symbols_inside") or {}, "label_source": sp.get("label_source"),
                "evidence": sp.get("evidence") or {}, "fixture_conflict": sp.get("fixture_conflict"),
                "void_m2": round(sp.get("void_m2") or 0.0, 6), "voids": sp.get("voids") or [],
                "codes_with_void": sp.get("codes_with_void"), "cells": sp.get("cells") or [],
                "attached_cells": sp.get("attached_cells") or [], "zone": sp.get("zone"),
                "double_height_m2": round(sp.get("double_height_m2") or 0.0, 6),
                "double_height": sp.get("double_height") or []}
        typed_by_evidence = sp.get("label_source") not in (None, "TEXT")
        zoned = bool(sp.get("zone"))                # S5: a zone of an open space bounded by drawn lines (inference)
        zone_ln = (sp.get("outer_role_lm") or {}).get("ZONE_LINE", 0.0) + (sp.get("hole_role_lm") or {}).get(
            "ZONE_LINE", 0.0)
        rooms.append(room)
        ded = [{"what": "obstructions inside the room (columns / shafts)", "m2": round(sp["hole_area_m2"], 6)}] \
            if sp["holes"] else []
        flights = (sp.get("symbols_inside") or {}).get("stair_flights") or ()
        for k, fl in enumerate(flights, 1):
            sl, su = _stair_lines(ctx, room, rid, floor, k, fl, facts,
                                  walls=(fr.get("walls") or {}).get("walls") or (), u=fr["unit_m"])
            lines += sl
            unresolved += su
        if flights and measured_as_room and sp["codes"] and AR.LEX[sp["codes"][0]][2] == AR.STAIR:
            sl, su = _landing(ctx, room, rid, floor, sp, flights, fr["unit_m"])
            lines += sl
            unresolved += su
        if not measured_as_room:
            ec = "ARCH.EXTERIOR" if kind == AR.EXTERIOR else "ARCH.SPACE"
            q = sp.get("issue") or ("MIXED_SPACE: rooms of different kinds share one face - " + " + ".join(sp["codes"]))
            lines.append(_line(ctx, item_code=ec, room=room, element="space", unit="m2", net=sp["area_m2"],
                               ev="PROVISIONAL", gross=round(sp["gross_outer_m2"], 6), deductions=ded,
                               formula="face area (TS01), obstructions deducted", inputs={"dims": room["dims"]},
                               rule_id="UP-CER-001", notes=q))
            unresolved.append({"room_id": rid, "floor": floor, "item": ec, "reason": q})
            continue
        if zoned and (measured_as_room or kind in NO_FINISH):
            unresolved.append({"room_id": rid, "floor": floor, "item": "FIN.FLOOR / zone", "reason": sp["zone_note"]})
        if kind == AR.STAIR:
            q = (f"STAIRWELL_CEILING_SCOPE_NOT_ESTABLISHED: the stair enclosure ({sp['area_m2']:.2f} m2) - its ceiling / "
                 "soffit (the flight soffit, the stair-well ceiling, the landing ceilings) is not in a plan; the section "
                 "and the ceiling plan decide it")
            lines.append(_line(ctx, item_code="FIN.CEILING", room=room, element="stairwell ceiling", unit="m2",
                               net=None, formula="stair-well ceiling / soffit (section)",
                               inputs={"enclosure_m2": round(sp["area_m2"], 6), "ceiling_type": "STAIRWELL"},
                               rule_id=None, rfi={"question": q, "unlocks": rid}))
            unresolved.append({"room_id": rid, "floor": floor, "item": "FIN.CEILING", "reason": q})
        if kind in NO_FINISH:
            ec = "ARCH.EXTERIOR" if kind == AR.EXTERIOR else "ARCH.SPACE"
            lines.append(_line(ctx, item_code=ec, room=room, element="space", unit="m2", net=sp["area_m2"],
                               gross=round(sp["gross_outer_m2"], 6), deductions=ded, rule_id="UP-CER-001",
                               formula="face area (TS01)", inputs={"dims": room["dims"]},
                               notes="; ".join(x for x in [f"{kind} space: no internal floor / ceiling finish line",
                                                           sp.get("issue") or ""] if x)))
            if owner_scope and kind == AR.EXTERIOR:
                # ARCH_TAKEOFF_V2.3 (UP-WP-ROOF-001): balconies / roofs are waterproofed under the default scope
                wl_ = OFS.exterior_wp_lines(ctx, room, sp["area_m2"], runs["perimeter"], line=_line)
                lines += wl_
                unresolved += [{"room_id": rid, "floor": floor, "item": ln_["item_code"],
                                "reason": ln_["rfi"]["question"]} for ln_ in wl_ if ln_.get("rfi")]
            if typed_by_evidence and sp.get("issue"):
                unresolved.append({"room_id": rid, "floor": floor, "item": ec, "reason": sp["issue"]})
            continue
        # the floor surface of the face: the same split as the floor reconciliation (arch_floor.split_face), so the
        # finish lines and the floor areas can never disagree
        parts = AF.split_face(sp, fr.get("voids") or (), fr["unit_m"], True)
        stair_m2 = parts.get("STAIR_FLIGHTS", 0.0)
        void_m2 = parts.get("VOID", 0.0)
        below_m2 = parts.get("STAIR_BELOW_SEEN", 0.0)
        if stair_m2 > 1e-6:
            ded = ded + [{"what": "stair treads drawn inside the room (marble: UP-STAIR-005, never also porcelain)",
                          "m2": round(stair_m2, 6)}]
        if void_m2 > 1e-6:
            ded = ded + [{"what": "the outlined void inside the face (open to below: never floor finish)",
                          "m2": round(void_m2, 6)}]
        if below_m2 > 1e-6:
            ded = ded + [{"what": "a flight of the plan below seen through the opening (no floor at this level; the "
                                  "stair is counted once, on the plan below)", "m2": round(below_m2, 6)}]
        att = sp.get("attached_cells") or []
        att_txt = ("ATTACHED_THROUGH_OPEN_PASSAGE: the floor includes " + ", ".join(
            f"{a['area_m2']:.2f} m2 of unlabelled floor reached only through open passage(s) {'/'.join(a['passages'])}"
            for a in att) + " (no door or glazing separates it; confirm it belongs to this room)") if att else ""
        if att:
            unresolved.append({"room_id": rid, "floor": floor, "item": "FIN.FLOOR", "reason": att_txt})
        fk = FINISH_KIND[kind]
        wet = fk == "WET"
        lines.append(_line(ctx, item_code="FIN.FLOOR.WET_TILE" if wet else "FIN.FLOOR.PORCELAIN", room=room,
                           element="floor", unit="m2",
                           net=round(max(sp["area_m2"] - stair_m2 - void_m2 - below_m2, 0.0), 6),
                           gross=round(sp["gross_outer_m2"], 6), deductions=ded,
                           formula="face area (TS01), obstructions deducted" +
                                   (", stair treads deducted (UP-STAIR-005)" if stair_m2 > 1e-6 else "") +
                                   (", outlined void deducted" if void_m2 > 1e-6 else "") +
                                   (", stair below seen through the opening deducted" if below_m2 > 1e-6 else ""),
                           inputs={"dims": room["dims"]}, rule_id="UP-CER-001",
                           ev="PROVISIONAL" if typed_by_evidence or att or zoned else None,
                           notes="; ".join(x for x in [
                               ("OPEN_PLAN: " + " + ".join(sp["codes"]) + " share one face (no partition between them); "
                                "one dry floor finish assumed for the whole space - split it if the finishes differ")
                               if open_plan else "", att_txt, sp.get("issue") or "", sp.get("fixture_conflict") or ""]
                               + ([] if not zoned or sp.get("zone_note") in (sp.get("issue") or "") else [sp["zone_note"]])
                               if x)))
        if owner_scope:
            # ARCH_TAKEOFF_V2.3 (UP-WET-001): kitchens, pantries, ironing and laundry rooms take the wet scope (full-height
            # wall porcelain, no skirting, no paint, waterproofing); an open plan of wet + dry functions keeps the dry
            # treatment and says why
            scope = OFS.finish_scope(room)
            room["finish_scope"] = scope
            if scope["scope"] == OFS.WET:
                wet = True
            for fl_ in scope["flags"]:
                unresolved.append({"room_id": rid, "floor": floor, "item": "FINISH_SCOPE", "reason": fl_})
        # ceilings (S5): one ceiling over every m2 of plan, at the top of the space. The part of the room under the void
        # of the plan above is double height (its ceiling is the one over that void, on the plan above); the room's
        # own outlined void carries the double-height ceiling at this level, as its own line
        dh = sp.get("double_height_m2") or 0.0
        c_ded = [d for d in ded if d["what"].startswith("obstructions")]
        if dh > 1e-6:
            c_ded.append({"what": "under the void of the plan above (double height: its ceiling is the one over the "
                                  "void, measured on that plan)", "m2": round(dh, 6)})
        if void_m2 > 1e-6:
            c_ded.append({"what": "the outlined void of this plan (its double-height ceiling: own line)",
                          "m2": round(void_m2, 6)})
        lines.append(_line(ctx, item_code="FIN.CEILING", room=room, element="ceiling", unit="m2",
                           net=round(max(sp["area_m2"] - void_m2 - dh, 0.0), 6), ev="PROVISIONAL",
                           gross=round(sp["gross_outer_m2"], 6), deductions=c_ded,
                           formula="plan area of the room (the floor face)" +
                                   (" - the part under the void above" if dh > 1e-6 else "") +
                                   (" - its own void (own line)" if void_m2 > 1e-6 else ""),
                           inputs={"dims": room["dims"], "ceiling_type": "NORMAL_LEVEL",
                                   "double_height_below_void_above_m2": round(dh, 6)},
                           rule_id=None, notes="; ".join(x for x in (
                               "ceiling type, bulkheads and coves are not in a plan; material BY_SPEC",
                               "a flight of the plan below seen through the opening: the ceiling over it is this "
                               "plan's (counted here)" if below_m2 > 1e-6 else "",
                               "DOUBLE_HEIGHT: " + ", ".join(f"{x['m2']:.2f} m2 under void {x['void_id']} of "
                                                             f"{x['from_floor']}" for x in sp.get("double_height") or ())
                               if dh > 1e-6 else "") if x)))
        if void_m2 > 1e-6:
            lines.append(_line(ctx, item_code="FIN.CEILING", room=room, element="ceiling over void", unit="m2",
                               net=round(void_m2, 6), ev="PROVISIONAL", formula="the outlined void of the room (the "
                               "ceiling of the double-height space, at this plan's ceiling level)",
                               inputs={"ceiling_type": "DOUBLE_HEIGHT", "voids": sp.get("voids") or []}, rule_id=None,
                               notes="DOUBLE_HEIGHT_CEILING: the ceiling over the void of a double-height space - its "
                                     "height, access and type need the section; material BY_SPEC"))
        skirt = runs["wall"] + runs["column"] + runs["window_threshold"]
        sk_notes = (f"door / passage openings not skirted ({runs['door'] + runs['passage']:.2f} m); "
                    f"sill windows skirted ({runs['window_threshold']:.2f} m) - deduct any floor-level glazing")
        if runs["glazing_edge"] > 1e-6:
            sk_notes += f"; glazing edge {runs['glazing_edge']:.2f} m not skirted"
        sk_open = None
        if release_safety:
            # ARCH_TAKEOFF_V2.2 (F-17): no equal split of an edge that is skirted under one reading and not the other
            from engine.source import release_safety as RSF
            sk_rs = RSF.skirting(skirt, sp["boundary_detail"])
            skirt = sk_rs["certain_lm"]
            if sk_rs["unresolved_lm"] > RSF.TOL_M:
                sk_open = sk_rs
                sk_notes += (f"; {sk_rs['unresolved_lm']:.2f} m of boundary is skirted under one reading and not "
                             "under the other (" + ", ".join(f"{k} {v:.2f} m" for k, v in
                                                            sk_rs["unresolved_by_roles"].items()) +
                             "): not in this line, a separate range line")
        if v28 and windows:
            # ARCH_TAKEOFF_V2.8 (UP-OPEN-SCHED-001): floor-level glazing is never skirted; a window whose sill is not
            # established is skirted under one reading only (a range, never a certain length) - edge by edge against
            # the F-17 reading above, so an edge already held in its range is not moved twice
            adj = AV28.skirting_adjustment(windows, sp["boundary_detail"], v28["schedule"])
            room["skirting_windows_v28"] = adj
            skirt = skirt - adj["floor_glazing_lm"] - adj["to_range_lm"]
            if adj["floor_glazing_lm"] > 1e-9:
                sk_notes += f"; floor-level glazing not skirted ({adj['floor_glazing_lm']:.2f} m)"
            if adj["to_range_lm"] > 1e-9 or adj["floor_glazing_range_lm"] > 1e-9:
                prev = sk_open or {"unresolved_lm": 0.0, "unresolved_by_roles": {}, "legacy_credit_lm": 0.0}
                by = dict(prev["unresolved_by_roles"])
                for k_, v_ in adj["range_out_by_roles"].items():
                    by[k_] = round(by.get(k_, 0.0) - v_, 6)
                    if by[k_] <= 1e-6:
                        del by[k_]
                for k_, v_ in adj["to_range_by"].items():
                    by[k_] = round(by.get(k_, 0.0) + v_, 6)
                un = prev["unresolved_lm"] + adj["to_range_lm"] - adj["floor_glazing_range_lm"]
                sk_open = dict(prev, unresolved_lm=un, unresolved_by_roles=by,
                               legacy_credit_lm=prev["legacy_credit_lm"] - adj["range_out_credit_lm"])
                if adj["to_range_lm"] > 1e-9:
                    sk_notes += (f"; {adj['to_range_lm']:.2f} m of window threshold skirted under one reading only "
                                 "(sill not established / floor glazing on a wall line): not in this line, a separate "
                                 "range line")
                if adj["floor_glazing_range_lm"] > 1e-9:
                    sk_notes += (f"; {adj['floor_glazing_range_lm']:.2f} m of floor-level glazing threshold out of the "
                                 "F-17 range (skirted under no reading)")
                if un <= RSF.TOL_M:
                    sk_open = None
        sk_len0 = len(lines)
        if wet:
            hs0 = heights(floor, lvl, floor_above_level_m, facts)
            if v28:
                hs0 = v28["evidence"].room_heights(floor, rid, hs0)
            tile_h, clear_h = hs0["WALL_TILE"], hs0["PAINT"]
            full = None
            if owner_scope:
                # UP-FIN-WALL-001: full height unless an explicit source / project height says otherwise
                tile_h = OFS.wall_tile_height(hs0)
                full = tile_h["full"]
                if v28:
                    room["wall_tile_v28"] = {k_: tile_h.get(k_) for k_ in ("state", "value_m", "governing",
                                                                         "authority", "why")}
            elif tile_h["state"] == WH.ESTABLISHED and tile_h["governing"] == "DERIVED_CLEAR_HEIGHT":
                full = True                               # derived to the ceiling: the tile is full height
            elif tile_h["state"] == WH.ESTABLISHED and clear_h["state"] == WH.ESTABLISHED:
                full = tile_h["value_m"] >= clear_h["value_m"] - 1e-6
            if owner_scope and full:
                lines.append(_line(ctx, item_code="FIN.SKIRTING", room=room, element="skirting", unit="lm", net=None,
                                   ev="NOT_APPLICABLE_WITH_EVIDENCE",
                                   formula="UP-CER-004 / UP-WET-001: owner wet area, full-height wall porcelain",
                                   inputs={"wall_tile_governing": tile_h.get("governing"), "run_lm": round(skirt, 6)},
                                   rule_id="UP-CER-004",
                                   notes="no conventional skirting: the wall porcelain of an owner wet area runs full "
                                         "height (UP-FIN-WALL-001)"))
            elif full is None:
                q = ("UP-CER-004: no skirting when the wall tile is full height; the wall tile height (or the clear "
                     f"height it is compared with) is not established (run {skirt:.2f} m if it is not full height)")
                lines.append(_line(ctx, item_code="FIN.SKIRTING", room=room, element="skirting", unit="lm", net=None,
                                   formula="wall + column faces - door openings", inputs={"run_lm": round(skirt, 6)},
                                   rule_id="UP-CER-004", rfi={"question": q, "unlocks": rid}, notes=sk_notes))
                unresolved.append({"room_id": rid, "floor": floor, "item": "FIN.SKIRTING", "reason": q})
            elif full:
                lines.append(_line(ctx, item_code="FIN.SKIRTING", room=room, element="skirting", unit="lm", net=None,
                                   ev="NOT_APPLICABLE_WITH_EVIDENCE", formula="UP-CER-004: full-height wall tile",
                                   inputs={"wall_tile_h_m": tile_h["value_m"], "governing": tile_h["governing"],
                                           "clear_h_m": clear_h.get("value_m"), "run_lm": round(skirt, 6)},
                                   rule_id="UP-CER-004",
                                   notes=f"no skirting: the wall tile runs full height ({tile_h['value_m']:.2f} m)"))
            else:
                lines.append(_line(ctx, item_code="FIN.SKIRTING", room=room, element="skirting", unit="lm",
                                   net=round(skirt, 6), formula="room boundary - door / passage openings - glazing edge "
                                   "(the wall tile is not full height: UP-CER-004)",
                                   inputs={k: round(v, 6) for k, v in runs.items()}, rule_id="UP-CER-004",
                                   gross=round(runs["boundary"], 6), deductions=_sk_ded(runs), notes=sk_notes +
                                   f"; wall tile {tile_h['value_m']:.2f} m below the clear height {clear_h['value_m']:.2f} m"))
        else:
            sk_ded = _sk_ded(runs)
            lines.append(_line(ctx, item_code="FIN.SKIRTING", room=room, element="skirting", unit="lm",
                               net=round(skirt, 6), formula="room boundary - door / passage openings - glazing edge "
                               "(= wall + column faces + sill-window thresholds)",
                               inputs={k: round(v, 6) for k, v in runs.items()},
                               rule_id="UP-CER-003", gross=round(runs["boundary"], 6), deductions=sk_ded,
                               notes=sk_notes))
        if sk_open is not None and any(ln["item_code"] == "FIN.SKIRTING" and ln["evidence_state"] in BL.QUANTITY_STATES
                                       for ln in lines[sk_len0:]):
            q = (f"F-17: {sk_open['unresolved_lm']:.2f} m of this room's boundary is skirted under one reading and not "
                 "under the other (" + ", ".join(f"{k} {v:.2f} m" for k, v in sk_open["unresolved_by_roles"].items()) +
                 ") - e.g. a window frame drawn on the room face: floor-level glazing -> no skirting, sill window -> "
                 "skirting; give the window type (schedule / elevation)")
            lines.append(_line(ctx, item_code="FIN.SKIRTING", room=room, element="skirting, boundary role unresolved",
                               unit="lm", net=None, bounded={"low": 0.0, "high": round(sk_open["unresolved_lm"], 6),
                                                             "basis": q},
                               formula="the edges skirted under one reading and not under the other: [0, their length]",
                               inputs={"unresolved_by_roles": sk_open["unresolved_by_roles"],
                                       "v1_equal_split_credit_lm": round(sk_open["legacy_credit_lm"], 6)},
                               rule_id="UP-CER-004" if wet else "UP-CER-003", rfi={"question": q, "unlocks": rid},
                               notes="RANGE_NOT_RELEASED: the released skirting line holds only what both readings "
                                     "agree on"))
            unresolved.append({"room_id": rid, "floor": floor, "item": "FIN.SKIRTING", "reason": q})
        if wet:
            wp_floor = round(sp["area_m2"] - stair_m2, 6)
            lines.append(_line(ctx, item_code="FIN.WP.FLOOR", room=room, element="wp_floor", unit="m2", net=wp_floor,
                               formula="room floor face", inputs={"dims": room["dims"]}, rule_id="UP-WP-001",
                               ev="PROVISIONAL" if typed_by_evidence or zoned else None,
                               notes=sp.get("issue") if typed_by_evidence or zoned else ""))
            shared_doors = []
            for d in doors:
                if d["opening_id"] in wp_door_owner:          # already the doorway piece of the wet space beyond
                    shared_doors.append(f"{d['opening_id']} (counted with {wp_door_owner[d['opening_id']]})")
                    continue
                wp_door_owner[d["opening_id"]] = rid
                held = d.get("door_fit_review")               # ARCH_TAKEOFF_V2.6 (D-V26-06): a door held for review
                lines.append(_line(ctx, item_code="FIN.WP.DOORWAY", room=room, element=f"doorway {d['opening_id']}",
                                   unit="m2", net=round(d["width_m"] * d["wall_t_m"], 6),
                                   formula="door width x wall thickness", rule_id="UP-WP-003",
                                   inputs={"width_m": round(d["width_m"], 4), "depth_m": round(d["wall_t_m"], 4)},
                                   ev="PROVISIONAL" if held else None,
                                   notes="DOORWAY_UPTURN_DETAIL_REQUIRED; DOORWAY_DOUBLE_COVERAGE_REVIEW" +
                                         (f"; DOOR_SYMBOL_FIT_REVIEW: {held}" if held else "")))
            # (S4) a door closed by its leaf and by the wall's other face (closure B) has its doorway piece as a face
            open_doors = []
            for cid in sp["closure_ids"]:
                door_key = cid.rsplit("|", 1)[0]
                piece = closure_pieces.get(door_key)
                if piece is None:
                    open_doors.append(cid)
                    continue
                if door_key in done_pieces:
                    continue
                done_pieces.add(door_key)
                w = (piece["outer_role_lm"].get("DOOR_CLOSURE") or 0.0) / 2.0     # both closures span the door
                m2, note, extra = piece["area_m2"], "", {}
                if piece_box:                                 # ARCH_TAKEOFF_V2.6 (D-V26-07)
                    from engine.source import arch_completeness as AC
                    got = AC.closure_box(piece, fr.get("repairs"), fr["unit_m"])
                    box_recs.append({"floor": floor, "door": door_key, "face_m2": round(piece["area_m2"], 6),
                                     **({"split": False, "reason": got} if isinstance(got, str) else
                                        {"split": True, "box_m2": got[0], "remainder_m2": got[1]})})
                    if not isinstance(got, str):
                        m2, extra = got[0], {"face_m2": round(piece["area_m2"], 6), "remainder_m2": got[1]}
                        note = (f"; STRIP_SPLIT_AT_OPENING_BOX (D-V26-07): the doorway face "
                                f"({piece['area_m2']:.4f} m2) runs on past the jambs between wall lines; the box "
                                f"between the closures is taken, {got[1]:.4f} m2 beyond them is wall")
                lines.append(_line(ctx, item_code="FIN.WP.DOORWAY", room=room, element=f"doorway {door_key}",
                                   unit="m2", net=round(m2, 6),
                                   formula="the doorway piece between the door's two closures (leaf face and the "
                                           "wall's other face)", rule_id="UP-WP-003",
                                   inputs={"width_m": round(w, 4),
                                           "depth_m": round(m2 / w, 4) if w > 0 else None,
                                           "face_id": piece["face_id"], "closures": piece["closure_ids"], **extra},
                                   notes="DOORWAY_UPTURN_DETAIL_REQUIRED; DOORWAY_DOUBLE_COVERAGE_REVIEW" + note))
            if open_doors:
                q = (f"{len(open_doors)} door(s) closed by a door-symbol closure: the doorway depth (wall "
                     "thickness) is not established for their doorway pieces")
                unresolved.append({"room_id": rid, "floor": floor, "item": "FIN.WP.DOORWAY", "reason": q})
            up = RS.rule("UP-WP-002", RULE_SET)["value"]
            lines.append(_line(ctx, item_code="FIN.WP.UPTURN", room=room, element="wp_upturn", unit="m2",
                               net=round(runs["perimeter"] * up, 6),
                               formula=f"one-sided boundary incl. doorways x {up:g} m (no door deduction)",
                               inputs={"perimeter_lm": round(runs["perimeter"], 6), "upturn_h_m": up},
                               rule_id="UP-WP-002", notes="; ".join(x for x in (
                                   "DOORWAY_UPTURN_DETAIL_REQUIRED" if doors or sp["closure_ids"] else "",
                                   ("SHARED_WET_DOORWAY: the doorway piece of door(s) " + ", ".join(shared_doors) +
                                    " is counted once, with the other wet space (UP-WP-003)") if shared_doors else "")
                                   if x)))
        hs = heights(floor, lvl, floor_above_level_m, facts)
        if v28:
            hs = v28["evidence"].room_heights(floor, rid, hs)
            room["heights_v28"] = {tr_: {k_: hs[tr_].get(k_) for k_ in ("state", "value_m", "governing", "authority",
                                                                       "why")} for tr_ in TRADES}
            room["wet_v28"] = bool(wet)
            if room.get("wall_tile_v28"):                # the owner full height applied (UP-FIN-WALL-001)
                room["heights_v28"]["WALL_TILE"] = room["wall_tile_v28"]
        oh = (facts or {}).get("opening_heights") or {}
        run = runs["perimeter"] - zone_ln               # a drawn zone line has no wall: no wall finish along it
        if owner_scope and wet:
            hs = dict(hs, WALL_TILE=OFS.wall_tile_height(hs))
            if hs["WALL_TILE"].get("flag"):
                unresolved.append({"room_id": rid, "floor": floor, "item": "FIN.WALL.TILE",
                                   "reason": hs["WALL_TILE"]["flag"]})
        for tr, code in (("PLASTER", "FIN.PLASTER"), ("PAINT", "FIN.PAINT"), ("WALL_TILE", "FIN.WALL.TILE")):
            if (tr == "WALL_TILE") != wet and tr != "PLASTER":
                continue
            h = hs[tr]
            if h["state"] != WH.ESTABLISHED:
                iv = hs["_interval"]
                q = (f"WALL_FINISH_HEIGHT_NOT_ESTABLISHED (UP-CER-009, {tr}): "
                     + (f"plan-level interval {iv['value_m']:.2f} m ({iv['authority']}) needs the soffit zone, ceiling "
                        "zone and floor build-up, each with its source" if iv else
                        "no level interval on the plans and no finish height in the facts"))
                lines.append(_line(ctx, item_code=code, room=room, element=tr.lower(), unit="m2", net=None,
                                   formula="wall run x finish height - openings", inputs={"wall_run_lm": round(run, 6)},
                                   rule_id="UP-CER-009", rfi={"question": q, "unlocks": rid}))
                unresolved.append({"room_id": rid, "floor": floor, "item": code, "reason": q})
                continue
            H = h["value_m"]
            if release_safety:
                lines.append(_wall_finish_rs(ctx, room, tr, code, run, H, h, doors + windows + passages, oh, sp,
                                             floor, unresolved, **({"height_of": v28["height_of"]} if v28 else {})))
                continue
            gross = run * H
            dd, missing = [], []
            for o, kd in [(d, "DOOR") for d in doors] + [(w, "WINDOW") for w in windows]:
                hh = oh.get(kd)
                if hh:
                    dd.append({"what": f"{kd.lower()} {o['opening_id']}", "m2": round(o["width_m"] * min(hh["value_m"], H), 6)})
                else:
                    missing.append((o, kd))
            dd += [{"what": f"passage {p['opening_id']}", "m2": round(p["width_m"] * H, 6)} for p in passages]
            known = sum(x["m2"] for x in dd)
            inputs = {"wall_run_lm": round(run, 6), "height_m": H, "height_authority": h["authority"],
                      "height_governing": h["governing"]}
            if missing:
                worst = sum(o["width_m"] * H for o, _ in missing)
                br = {"low": round(gross - known - worst, 6), "high": round(gross - known, 6),
                      "basis": f"{len(missing)} opening height(s) unknown: no deduction ... full-height deduction"}
                q = f"opening heights not established for {len(missing)} opening(s) ({tr} net is a range)"
                lines.append(_line(ctx, item_code=code, room=room, element=tr.lower(), unit="m2", net=None,
                                   bounded=br, gross=round(gross, 6), deductions=dd, formula="wall run x height - openings",
                                   inputs=inputs, rule_id="UP-CER-009", rfi={"question": q, "unlocks": rid}))
                unresolved.append({"room_id": rid, "floor": floor, "item": code, "reason": q})
            else:
                lines.append(_line(ctx, item_code=code, room=room, element=tr.lower(), unit="m2",
                                   net=round(gross - known, 6), gross=round(gross, 6), deductions=dd,
                                   formula="wall run x height - openings", inputs=inputs, rule_id="UP-CER-009",
                                   notes=("WINDOW_POSITION_ASSUMED: sill / head levels are not in a plan - each window "
                                          "is deducted at its full height inside the finish height") if windows else ""))
    if owner_scope:
        # ARCH_TAKEOFF_V2.3: door jamb / head plaster (UP-FIN-PLASTER-001) and doorless-opening jamb skirting
        # (UP-SKIRT-001, URBAN-SKIRTING-OPENING-METHOD), both PROVISIONAL
        lines += OFS.jamb_plaster_lines(ctx, fr["openings"], floor, door_height or (lambda o: None), line=_line)
        lines += OFS.passage_jamb_skirting(ctx, fr["openings"], rooms, floor, line=_line)
    if fr.get("walls"):
        sl, su = _wall_lines(ctx, floor, fr["walls"], facts)
        lines += sl
        unresolved += su
    openings = []
    oh_facts = (facts or {}).get("opening_heights") or {}
    for o in fr["openings"]:
        code = {"DOOR": "ARCH.DOOR", "WINDOW": "ARCH.WINDOW", "PASSAGE": "ARCH.PASSAGE"}[o["kind"]]
        host = [r["room_id"] for r in rooms if o["opening_id"] in r["doors"] + r["windows"] + r["passages"]]
        hh0 = oh_facts.get(o["kind"])
        w_id = _host_wall(o, (fr.get("walls") or {}).get("walls") or (), fr["unit_m"])
        rec = {"opening_id": o["opening_id"], "floor": floor, "kind": o["kind"], "width_m": round(o["width_m"], 4),
               "wall_t_m": round(o["wall_t_m"], 4), "rooms": host, "door_symbol": o.get("door_symbol"),
               "jambs": [o["start_jamb"], o["end_jamb"]],
               # S5 inventory: host wall, type, height / area state and the evidence of the kind (a swing gives a
               # width and a hand, never a height)
               "host_wall": w_id, "type": ("DOUBLE_DOOR" if o.get("door_leaves") else "SWING_DOOR") if o["kind"] ==
               "DOOR" else ("WINDOW" if o["kind"] == "WINDOW" else "PASSAGE_OR_ARCHWAY"), "material": "BY_SCHEDULE",
               "height_m": hh0["value_m"] if hh0 else None, "height_state": "FACT" if hh0 else "NOT_ESTABLISHED",
               "area_m2": round(o["width_m"] * hh0["value_m"], 6) if hh0 else None,
               "evidence": {"door_symbol": o.get("door_symbol"), "door_leaves": o.get("door_leaves"),
                            "glazing_lm": o.get("glazing_m"), "marks": o.get("marks")},
               "status": "WIDTH_MEASURED" + ("" if hh0 else "_HEIGHT_NOT_ESTABLISHED")}
        for k in ("door_fit_review", "door_symbol_note"):     # ARCH_TAKEOFF_V2.6 (arch_rooms.match_swings_review)
            if o.get(k):
                rec[k] = o[k]
        if o.get("opening_v27"):                              # ARCH_TAKEOFF_V2.7 (arch_v27.jamb_reconstruction)
            rec["opening_v27"] = o["opening_v27"]
        sch = (v28 or {}).get("schedule", {}).get(o["opening_id"]) if v28 else None
        if sch is not None:                                   # ARCH_TAKEOFF_V2.8 (UP-OPEN-SCHED-001)
            hv = sch["height"].get("value_m")
            rec.update(height_m=hv, height_state=sch["area_state"], area_m2=sch["area_m2"],
                       status="WIDTH_MEASURED" + ("" if hv is not None else "_HEIGHT_NOT_ESTABLISHED"))
            rec["v28"] = {k: sch[k] for k in ("mark", "class", "height", "sill", "head_m", "area_m2", "area_state",
                                              "findings") if k in sch}
        if release_safety:
            # ARCH_TAKEOFF_V2.2: where the opening is (the blind-test scorer matches windows by position, not width)
            um = fr["unit_m"]
            rec["position"] = {"centre_m": [round(o["centre"][0] * um, 4), round(o["centre"][1] * um, 4)],
                               "wall_axis": [round(o["u"][0], 6), round(o["u"][1], 6)],
                               "evidence": "the middle of the band opening between its jambs, at mid wall (drawing "
                                           "coordinates, m)"}
        openings.append(rec)
        pseudo = {"room_id": host[0] if host else f"{floor}-EXT", "floor": floor,
                  "name_en": " | ".join(r["name_en"] for r in rooms if r["room_id"] in host) or "exterior",
                  "name_ar": " | ".join(r["name_ar"] for r in rooms if r["room_id"] in host) or "خارجي"}
        hh = ((facts or {}).get("opening_heights") or {}).get(o["kind"])
        if sch is not None:
            hv, sv = sch["height"].get("value_m"), sch["sill"].get("value_m")
            note = (f"height {hv:g} m ({sch['height'].get('authority')})" if hv is not None else
                    "height NOT ESTABLISHED (" + "; ".join(sch["height"].get("why") or ["schedule / section / "
                                                                                        "elevation needed"]) +
                    "): width released, area held")
            if o["kind"] == "WINDOW":
                note += ("; sill " + (f"{sv:g} m ({sch['sill'].get('authority')})" if sv is not None else
                                      "NOT ESTABLISHED: skirting, reveals and the band deduction stay open") +
                         f"; class {sch['class']}")
            lines.append(_line(ctx, item_code=code, room=pseudo, element=o["opening_id"], unit="pcs", net=1,
                               formula="one opening (jambed wall-band gap)", rule_id=None,
                               inputs={"width_m": rec["width_m"], "wall_t_m": rec["wall_t_m"], "height_m": hv,
                                       "sill_m": sv, "head_m": sch["head_m"], "area_m2": sch["area_m2"],
                                       "class": sch["class"], "mark": (sch.get("mark") or {}).get("mark")},
                               notes=note))
            continue
        lines.append(_line(ctx, item_code=code, room=pseudo, element=o["opening_id"], unit="pcs", net=1,
                           formula="one opening (jambed wall-band gap)", rule_id=None,
                           inputs={"width_m": rec["width_m"], "wall_t_m": rec["wall_t_m"],
                                   "height_m": hh["value_m"] if hh else None},
                           notes=("height " + (f"{hh['value_m']:g} m ({hh['authority']})" if hh else
                                              "NOT ESTABLISHED (schedule / elevation needed)"))))
    for occ, st in fr["door_status"].items():
        if st.get("state") == "OPENING_CLOSURE_UNRESOLVED":
            unresolved.append({"room_id": "-", "floor": floor, "item": "door symbol " + occ.split("|")[-1],
                               "reason": "DOOR_CLOSURE_UNRESOLVED: " + st.get("why", "")})
    return {"policy": POLICY_ID, "floor": floor, "rooms": rooms, "lines": lines, "openings": openings,
            "unresolved": unresolved, "counts": dict(Counter(r["class"] for r in rooms)),
            **({"piece_box": box_recs} if piece_box else {})}


def _host_wall(o, walls, unit_m):
    """the wall band an opening is cut in: the wall whose centreline runs along the opening (parallel) through its
    middle, within half the thicker of the two; None when the gap is not in one band (a wall end, a column)."""
    (ux, uy), (nx, ny) = o["u"], o["n"]
    m = (ux * (o["s0"] + o["s1"]) / 2 + nx * (o["o0"] + o["o1"]) / 2,
         uy * (o["s0"] + o["s1"]) / 2 + ny * (o["o0"] + o["o1"]) / 2)
    best = None
    for w in walls:
        (ax, ay), (bx, by) = w["centreline"]
        L = math.hypot(bx - ax, by - ay)
        if L <= 0 or abs((bx - ax) * uy - (by - ay) * ux) / L > 0.01:
            continue
        reach = max(w["t_m"], abs(o["o1"] - o["o0"]) * unit_m) / 2 / unit_m + 0.005 / unit_m
        d = AR._dist_point_seg(m, (ax, ay), (bx, by))
        if d <= reach and (best is None or d < best[0]):
            best = (d, w["wall_id"])
    return best[1] if best else None


def _wall_lines(ctx, floor, W, facts):
    """per thickness family: the wall run (lm, plan geometry) and the block wall (m2), which needs the material and
    the block height - a band is wall geometry, never a material (engine.qs_core.masonry's two axes)."""
    lines, unresolved = [], []
    walls = {"room_id": f"{floor}-WALLS", "floor": floor, "name_en": "Walls", "name_ar": "الجدران"}
    jm = W["conservation"]["junction_m2"]
    for fam in W["by_thickness"]:
        el = f"walls t={fam['family']}"
        inp = {"thickness_family_m": fam["family"], "walls": fam["walls"], "net_lm": fam["net_lm"],
               "gross_lm": fam["gross_lm"], "external_lm": fam["external_lm"], "internal_lm": fam["internal_lm"],
               "columns_in_wall_lm": fam.get("columns_in_wall_lm", 0.0)}
        lines.append(_line(ctx, item_code="ARCH.WALL_RUN", room=walls, element=el, unit="lm", net=fam["net_lm"],
                           ev="PROVISIONAL", gross=fam["gross_lm"],
                           deductions=[{"what": "openings, wall ends and columns standing in the wall line (lm)",
                                        "lm": round(fam["gross_lm"] - fam["net_lm"], 6)}],
                           formula="sum over the wall bands of this thickness of the run where both wall faces are "
                                   "drawn (arch_walls)", inputs=inp, rule_id=None,
                           notes=f"junction pieces of the floor ({jm:.2f} m2 in plan: corners, T-junctions, wall ends) "
                                 "are not given to a thickness; external / internal by the space on each face"))
        q = (f"BLOCK_WALL_NOT_ESTABLISHED (walls t={fam['family']} m, {fam['net_lm']:.2f} lm): the wall material "
             "(block type / RC / partition: legend or specification) and the block height (slab soffit / beam depth "
             "above each wall) are not in the plan")
        lines.append(_line(ctx, item_code="MAS.BLOCK", room=walls, element=el, unit="m2", net=None,
                           formula="wall run x block height - openings (width x height)", inputs=inp, rule_id=None,
                           rfi={"question": q, "unlocks": walls["room_id"]}))
        unresolved.append({"room_id": walls["room_id"], "floor": floor, "item": f"MAS.BLOCK {el}", "reason": q})
    return lines, unresolved


STAIR_TREAD_T_RULE = "UP-STAIR-006"           # the tread marble thickness the visible riser loses


def _flight_inputs(fl):
    return {"kind": fl["kind"], "flight_id": fl.get("flight_id"), "layer": fl["layer"],
            "also_drawn_on": fl.get("also_drawn_on") or [], "tread_lines": fl["tread_lines"],
            "treads": len(fl["tread_areas_m2"]), "going_m": fl["going_m"], "width_m": fl["width_m"],
            "run_m": fl["run_m"], **({"r_in_m": fl["r_in_m"], "r_out_m": fl["r_out_m"], "sweep_deg": fl["sweep_deg"]}
                                     if fl["kind"] == "RADIAL" else {})}


def _seen_below(fl):
    b = fl.get("drawn_on_plan_below")
    if not b:
        return None
    return (f"STAIR_DRAWN_ON_TWO_PLANS: flight {fl.get('flight_id')} lies over flight {b['flight_id']} of {b['floor']} "
            f"({100 * b['overlap']:.0f} % of its treads after the floor alignment, {b['alignment']}) and a void is marked "
            f"at it: the same steps seen through the void - counted on {b['floor']}, here as exposure only (confirm)")


def _stacked(fl):
    b = fl.get("stacked_over")
    if not b:
        return None
    return (f"STAIR_STACKED_FLIGHT_ASSUMED: flight {fl.get('flight_id')} lies over flight {b['flight_id']} of {b['floor']} "
            f"({100 * b['overlap']:.0f} % of its treads, {b['alignment']}) with no void marked at it: counted as the "
            "next storey's flight (a stair core) - if it is the same stair seen from above, deduct it")


RAIL_WALL_GAP_M = 0.15                # a flight side this close to a wall face (most of its length) is a wall side
RAIL_WALL_SHARE = 0.8


def flight_sides(fl, walls, u):
    """the two long sides of a flight (straight: the stringers from the first to the last tread line; curved: the inner
    and the outer edge) and whether each runs along a wall face (UP-STAIR-012: a guardrail only on an open side).
    -> [{"side", "plan_lm", "kind": WALL | OPEN}]"""
    fp = fl["footprint"]
    if fl["kind"] == "RADIAL":
        n = len(fp) // 2
        paths = [("inner", fp[:n]), ("outer", fp[n:][::-1])]
    else:
        paths = [("side_a", [fp[3], fp[0]]), ("side_b", [fp[1], fp[2]])]
    out = []
    for name, pts in paths:
        plan = sum(math.dist(a, b) for a, b in zip(pts, pts[1:])) * u
        samples = []
        for a, b in zip(pts, pts[1:]):
            samples += [(a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])) for t in (0.1, 0.3, 0.5, 0.7, 0.9)]
        near = 0
        for q in samples:
            if any(AR._dist_point_seg(q, *w["centreline"]) * u <= w["t_m"] / 2 + RAIL_WALL_GAP_M for w in walls):
                near += 1
        kind = "WALL" if samples and near >= RAIL_WALL_SHARE * len(samples) else "OPEN"
        out.append({"side": name, "plan_lm": round(plan, 4), "kind": kind})
    return out


def _stair_lines(ctx, room, rid, floor, k, fl, facts, walls=(), u=1.0):
    """the finish lines of one drawn flight: tread marble (each tread its own polygon), the commercial step basis,
    the visible riser (needs the riser height) and the sloping flight length. A flight that repeats a flight of the
    plan below is exposure (low 0) until a reviewer says which it is."""
    lines, unresolved = [], []
    inp = _flight_inputs(fl)
    el = f"flight {k}"
    dup = _seen_below(fl)
    st = (facts.get("stairs") or {}).get(floor) or (facts.get("stairs") or {}).get("*") or {}
    R = st.get("riser_m") or {}
    conv = ("TREADS_BETWEEN_LINES: the n drawn tread lines bound n - 1 treads; if the top line is a nosing (not the "
            "landing / floor edge) one more tread is not drawn")

    def emit(code, unit, value, formula, rule, extra, notes):
        if dup:
            lines.append(_line(ctx, item_code=code, room=room, element=el, unit=unit, net=None, rule_id=rule,
                               bounded={"low": 0.0, "high": round(value, 6), "basis": dup}, formula=formula,
                               inputs={**inp, **extra}, rfi={"question": dup, "unlocks": rid}, notes=notes))
        else:
            lines.append(_line(ctx, item_code=code, room=room, element=el, unit=unit, net=round(value, 6),
                               ev="PROVISIONAL", formula=formula, inputs={**inp, **extra}, rule_id=rule,
                               notes="; ".join(x for x in (notes, _stacked(fl)) if x)))
    tread = sum(fl["tread_areas_m2"])
    emit("FIN.MARBLE.TREAD", "m2", tread, "sum of the tread polygons between consecutive tread lines (each tread its "
         "own polygon: rectangles on a straight flight, wedges on a curved / winder flight)", "UP-STAIR-003",
         {"tread_areas_m2": fl["tread_areas_m2"]}, conv + "; tread marble covers the nosing projection by detail")
    emit("FIN.STAIR.STEP_LM", "lm", sum(fl["step_widths_m"]), "sum of the width of each physical step of the flight "
         "(never derived from the tread area)", "UP-STAIR-008", {"step_widths_m": fl["step_widths_m"]},
         conv + "; a step drawn on two plans is one step")
    if dup:
        unresolved.append({"room_id": rid, "floor": floor, "item": f"FIN.MARBLE.TREAD / FIN.STAIR.STEP_LM {el}",
                           "reason": dup})
    st_ = _stacked(fl)
    if st_:
        unresolved.append({"room_id": rid, "floor": floor, "item": f"FIN.MARBLE.TREAD / FIN.STAIR.STEP_LM {el}",
                           "reason": st_})
    t = RS.rule(STAIR_TREAD_T_RULE, RULE_SET)["value"]
    if R.get("value_m"):
        vis = R["value_m"] - t
        widths = fl["riser_widths_m"]
        low = sum(widths) * vis
        br = {"low": round(low, 6), "high": round(low + max(widths) * vis, 6),
              "basis": f"{len(widths)} risers (each drawn line over a riser) ... one more at the top of the flight "
                       f"(the riser onto the landing / floor); visible height {R['value_m']:g} - {t:g} m tread marble"}
        q = (f"STAIR_RISER_COUNT_CONVENTION: flight {k} - the drawn lines give {len(widths)} or {len(widths) + 1} "
             "risers (a plan does not say whether the top line is a nosing or the landing edge)")
        lines.append(_line(ctx, item_code="FIN.MARBLE.RISER", room=room, element=el, unit="m2", net=None, bounded=br,
                           formula="sum of riser widths x (riser height - tread marble thickness)",
                           inputs={**inp, "riser_widths_m": widths, "riser_m": R["value_m"],
                                   "riser_authority": R.get("authority"), "tread_t_m": t}, rule_id="UP-STAIR-003",
                           rfi={"question": q, "unlocks": rid}))
        unresolved.append({"room_id": rid, "floor": floor, "item": f"FIN.MARBLE.RISER {el}", "reason": q})
        treads = len(fl["tread_areas_m2"])
        L = math.hypot(fl["run_m"], treads * R["value_m"])
        emit("FIN.STAIR.FLIGHT", "lm", L, "pitch line nosing to nosing: hypot(run, treads x riser)" +
             (" on the walking line (mid radius)" if fl["kind"] == "RADIAL" else ""), None,
             {"riser_m": R["value_m"], "riser_authority": R.get("authority")},
             "the railing / handrail adds its end extensions by detail (not in a plan)")
        sides = flight_sides(fl, walls, u)
        rise = treads * R["value_m"]
        opn = [x for x in sides if x["kind"] == "OPEN"]
        if opn:
            emit("FIN.RAILING", "lm", sum(math.hypot(x["plan_lm"], rise) for x in opn),
                 "per open side: sqrt(plan path^2 + rise^2) (UP-STAIR-012; a curved side along its own radius)",
                 "UP-STAIR-012", {"sides": sides, "rise_m": round(rise, 4)},
                 "end extensions, newels and landing / void-edge rails by detail; a wall side takes no guardrail "
                 "(a wall-mounted handrail only where shown or specified: UP-STAIR-013 - none shown)")
    else:
        q = (f"STAIR_RISER_NOT_ESTABLISHED: flight {k} ({fl['kind'].lower()}, {fl['tread_lines']} tread lines, going "
             f"{fl['going_m']:.3f} m, width {fl['width_m']:.2f} m, run {fl['run_m']:.2f} m) - the visible riser and the "
             "sloping length need the riser height (section / riser count of every flight between the two levels)")
        sides = flight_sides(fl, walls, u)
        rails = [("FIN.RAILING", "lm", "per open side: sqrt(plan path^2 + rise^2) (UP-STAIR-012)")] \
            if any(x["kind"] == "OPEN" for x in sides) else []
        for code, unit, f_ in [("FIN.MARBLE.RISER", "m2", "sum of riser widths x (riser height - tread marble thickness)"),
                               ("FIN.STAIR.FLIGHT", "lm", "pitch line nosing to nosing: hypot(run, treads x riser)")] + rails:
            lines.append(_line(ctx, item_code=code, room=room, element=el, unit=unit, net=None, formula=f_,
                               inputs=dict(inp, sides=sides) if code == "FIN.RAILING" else inp,
                               rule_id={"FIN.MARBLE.RISER": "UP-STAIR-003", "FIN.RAILING": "UP-STAIR-012"}.get(code),
                               rfi={"question": q, "unlocks": rid}))
        unresolved.append({"room_id": rid, "floor": floor, "item": f"FIN.MARBLE.RISER / FIN.STAIR.FLIGHT {el}",
                           "reason": q})
    return lines, unresolved


def _treads_in(poly_m, holes_m, fl, u):
    return sum(PP.region_area_in_convex(poly_m, holes_m, [(x * u, y * u) for x, y in q]) for q in fl["tread_quads"])


def _landing(ctx, room, rid, floor, sp, flights, u):
    """a stair room's landing marble: the plan of a stair enclosure less its drawn treads is an upper bound of the
    landings (it also holds any well / void the walls do not close); the landing polygon itself is not in a plan."""
    treads = sum(_treads_in(sp["polygon_m"], sp["hole_polygons_m"], fl, u) for fl in flights)
    rest = max(sp["area_m2"] - treads, 0.0)
    q = (f"STAIR_LANDING_POLYGON_NOT_ESTABLISHED: the stair enclosure is {sp['area_m2']:.2f} m2 and its drawn treads "
         f"{treads:.2f} m2; the remaining {rest:.2f} m2 holds the landings and any stair well - the landing outline "
         "(or the well) is needed for the landing marble")
    ln = _line(ctx, item_code="FIN.MARBLE.LANDING", room=room, element="landings", unit="m2", net=None,
               bounded={"low": 0.0, "high": round(rest, 6), "basis": "stair enclosure - drawn treads (an upper bound)"},
               formula="landing polygons (UP-STAIR-005)", inputs={"enclosure_m2": round(sp["area_m2"], 6),
                                                                  "treads_m2": round(treads, 6)},
               rule_id="UP-STAIR-005", rfi={"question": q, "unlocks": rid})
    return [ln], [{"room_id": rid, "floor": floor, "item": "FIN.MARBLE.LANDING", "reason": q}]


# every unresolved record of the route gets a terminal classification (M9 S3 Phase F): what stops it, where the
# software or the source is the cause, the module / function that raised it and the action that unlocks it.
#   SOFTWARE  the drawing holds the information and the engine does not read it yet
#   SOURCE    the drawings of this run do not hold it (a section, a schedule, a legend, a specification)
#   REVIEW    the drawing allows several readings; a person decides (the engine never picks one silently)
FLAG_RULES = (
    # ARCH_TAKEOFF_V2.3 (owner_finish_scope; knowledge registry 1.0.0) - prefixes no earlier method emits
    (r"^WALL_TILE_BELOW_OWNER_FULL_HEIGHT", "SOURCE", "owner_finish_scope.wall_tile_height",
     "confirm the project's wall-tile height: it governs the owner full-height rule (UP-FIN-WALL-001), and the band "
     "above it follows the same source"),
    (r"^OPEN_PLAN_WET_SCOPE_EXTENT", "SOURCE", "owner_finish_scope.finish_scope",
     "draw or give the kitchen / pantry zone of the open plan (a finish-plan line or hatch): the wet scope applies "
     "inside it (UP-WET-001)"),
    (r"^WET_SCOPE_PROJECT_CONFIRMATION", "SOURCE", "owner_finish_scope.finish_scope",
     "confirm in the project finish schedule that the room is a wet area (UP-WET-001: project-specific)"),
    (r"^EXTERIOR_WP_UPTURN_BY_SPECIFICATION", "SOURCE", "owner_finish_scope.exterior_wp_lines",
     "give the balcony / terrace membrane system and its upturn height (specification)"),
    (r"^WALL_FINISH_HEIGHT_NOT_ESTABLISHED", "SOURCE", "arch_measure.measure / wall_height.resolve",
     "give the finish height per floor and trade, or the soffit / ceiling / build-up zones, from the sections "
     "(--facts wall_heights / height_components)"),
    (r"^opening heights not established", "SOURCE", "arch_measure.measure",
     "give the door / window heights from the schedule or elevations (--facts opening_heights)"),
    (r"^UP-CER-004", "SOURCE", "arch_measure.measure", "give the wall tile height of wet rooms (--facts wall_heights "
     "WALL_TILE) or the clear height it is compared with"),
    (r"^STAIR_RISER_NOT_ESTABLISHED", "SOURCE", "arch_measure._stair_lines",
     "give the riser height (or the riser count between the two levels) from the section (--facts stairs.riser_m)"),
    (r"^STAIR_RISER_COUNT_CONVENTION", "REVIEW", "arch_measure._stair_lines",
     "confirm whether the top drawn line of each flight is a nosing or the landing edge"),
    (r"^STAIR_DRAWN_ON_TWO_PLANS", "REVIEW", "arch_rooms.cross_plan_flights",
     "confirm that the flight on the upper plan is the stair below seen through the void (counted once)"),
    (r"^STAIR_STACKED_FLIGHT_ASSUMED", "REVIEW", "arch_rooms.cross_plan_flights",
     "confirm that the flight is the next storey's own flight (a stair core), not the stair below seen from above"),
    (r"^STAIRWELL_CEILING_SCOPE_NOT_ESTABLISHED", "SOURCE", "arch_measure.measure",
     "give the stair-well ceiling / soffit scope from the section and the reflected ceiling plan"),
    (r"^STAIR_LANDING_POLYGON_NOT_ESTABLISHED", "SOURCE", "arch_measure._landing",
     "draw / give the landing outline (or the stair-well outline) of the stair enclosure"),
    (r"^BLOCK_WALL_NOT_ESTABLISHED", "SOURCE", "arch_measure._wall_lines",
     "give the wall material by thickness (legend / specification) and the block height (slab soffit / beam depth)"),
    (r"^ZONE_FROM_DRAWN_LINES", "REVIEW", "arch_rooms.zone_partition",
     "confirm that the drawn line(s) bound a floor-finish zone (a finish change, threshold, planter or counter edge), "
     "or draw the boundary as a finish hatch / on a finish layer"),
    (r"^ATTACHED_THROUGH_OPEN_PASSAGE", "REVIEW", "arch_rooms.open_passages",
     "confirm the unlabelled alcove / vestibule belongs to this room's floor, or draw / name its own boundary"),
    (r"^VOID_EXTENT_UNRESOLVED", "SOURCE", "arch_rooms.void_outlines",
     "draw the void outline (an X-marked rectangle or a closed outline around the VOID word), or give its extent"),
    (r"^(VOID_DEDUCTED: .*; )?MERGED_SPACE", "REVIEW", "arch_rooms.spaces",
     "draw the missing partition / door closure between the spaces, or confirm the open space and its finishes"),
    (r"^MERGED_SPACE", "REVIEW", "arch_rooms.spaces",
     "draw the missing partition / door closure between the spaces, or confirm the open space and its finishes"),
    (r"^MIXED_SPACE", "REVIEW", "arch_rooms.spaces", "confirm one finish for the open plan, or draw the split"),
    (r"^UNLABELLED_SPACE.*SHX font", "SOFTWARE", "tools.arch_intake.decode_text",
     "decode the SHX big-font text (font file or code map), or label the space for review"),
    (r"^UNLABELLED_SPACE", "SOURCE", "arch_rooms.spaces / arch_rooms._evidence",
     "name the space (room word, room-tag block or fixtures), or confirm it is not a room (shaft, duct, void)"),
    (r"^ROOM_TYPE_FROM_STACKED_FOOTPRINT", "REVIEW", "arch_rooms.stacked_shafts",
     "confirm the shaft / duct (the same doorless footprint on the other plans), or name the space"),
    (r"^ROOM_TYPE_FROM_", "REVIEW", "arch_rooms._evidence", "confirm the room type proposed from its tag / fixtures"),
    (r"^DOOR_CLOSURE_UNRESOLVED", "SOFTWARE", "topology.opening_closures",
     "the door symbol closes no gap the engine can find: check the swing against the wall linework"),
    (r"door\(s\) closed by a door-symbol closure", "SOFTWARE", "arch_measure.measure",
     "measure the wall thickness at the door-symbol closure (not implemented); or give the doorway depth"),
    (r"^NO_WALL_LAYER", "SOFTWARE", "arch_plan.layer_roles", "name the wall layer (--layer-roles LAYER=WALL)"),
    (r"(selected size|tile size|finishes\.|joint)", "SOURCE", "arch_measure.materials / tile_layout",
     "give the tile size, joint and cut constraints (--facts finishes / tile_constraints)"),
    (r"(membrane|roll)", "SOURCE", "arch_measure.materials / membrane_layout",
     "give the membrane specification (--facts membrane)"),
)


def flag(rec, *, drawing, region=None, room=None):
    """-> the unresolved record with item, location, reason, source_ref, module_function, cause and next_action."""
    import re
    reason = rec.get("reason") or ""
    cause, mod, nxt = "REVIEW", "arch_measure", "review the item against the drawings"
    for pat, c, m, a in FLAG_RULES:
        if re.search(pat, reason, re.I):
            cause, mod, nxt = c, m, a
            break
    loc = {"floor": rec.get("floor"), "room_id": rec.get("room_id")}
    if room:
        loc.update(room_en=room.get("name_en"), room_ar=room.get("name_ar"))
    ref = {"drawing": drawing}
    if region:
        ref.update(region_id=region.get("region_id"), sheet_id=region.get("sheet_id"))
    if room:
        ref["face_id"] = room.get("face_id")
    return dict(rec, location=loc, source_ref=ref, module_function=mod, cause=cause, next_action=nxt)


def policy_record():
    return {"policy_id": POLICY_ID, "rule_set": RULE_SET, "facts_schema": FACTS_SCHEMA,
            "s5": ["a zone of an open space (drawn lines) is measured as a room, PROVISIONAL and flagged; no wall "
                   "finish along a drawn zone line", "a door between two wet spaces has one doorway piece (UP-WP-003)",
                   "ceilings: none under the void of the plan above (double height); the ceiling over this plan's own "
                   "void is its own DOUBLE_HEIGHT line; a stair enclosure's ceiling is BLOCKED until the section",
                   "a guardrail only on a flight's open side (UP-STAIR-012), sloping; no wall handrail unless shown",
                   "every opening names its host wall band, type and height state (a swing never gives a height)"],
            "never": ["a wall height from a floor-to-floor interval alone", "a constant wall-tile height",
                      "a finish on a merged / unlabelled space", "an opening height that is not sourced",
                      "a doorway piece counted twice", "a ceiling counted on two plans"]}


def materials(result, facts=None):
    """tile and membrane material results for the measured rooms, linked to their floor / waterproofing lines.
    A selected size comes only from the facts (finishes.DRY / finishes.WET); without it the material is BLOCKED and
    the owner sizes are still compared (as candidates) once a joint width is given. Rectangular rooms are laid exactly
    (tile_layout.best, membrane_layout.plan); any other room - a polygon, a room with obstructions - by the polygon
    layouts (tile_layout.best_polygon, membrane_layout.plan_polygon), which reproduce the rectangle results exactly
    on a rectangle."""
    from engine.source import material_result as MR
    from engine.source import material_spec as MS
    from engine.source import membrane_layout as ML
    facts = facts or {}
    fin = facts.get("finishes") or {}
    tc = dict(facts.get("tile_constraints") or {})
    mats, comps, unresolved = [], [], []
    by_room = {}
    for ln in result["lines"]:
        by_room.setdefault(ln["location"]["room_id"], []).append(ln)
    for room in result["rooms"]:
        ls = by_room.get(room["room_id"], [])
        floor_ln = next((x for x in ls if x["item_code"] in ("FIN.FLOOR.PORCELAIN", "FIN.FLOOR.WET_TILE")), None)
        if floor_ln is None:
            continue
        wet = floor_ln["item_code"] == "FIN.FLOOR.WET_TILE"
        geo = {"room_id": room["room_id"], "floor": room["floor"], "name_en": room["name_en"],
               "name_ar": room["name_ar"], "line_id": floor_ln["line_id"], "polygon": room["polygon_m"],
               "holes": room["hole_polygons_m"],
               "net_area_m2": room["area_m2"]}
        if room["rect"]:
            geo["length_m"], geo["width_m"] = room["rect"]
            geo.pop("polygon")
        sel = (fin.get("WET" if wet else "DRY") or {}).get("floor")
        c = dict(tc, wet_room=wet, rule_refs=[_ref("UP-CER-010"), _ref("UP-CER-001")])
        loc = {k: geo.get(k) for k in ("room_id", "floor", "name_en", "name_ar")}
        if not sel:
            res = MR.blocked(method=TL.METHOD, spec=None, net_installed_m2=room["area_m2"], line_id=floor_ln["line_id"],
                             location=loc, reason="FLOOR_FINISH_SPEC_NOT_ESTABLISHED: no selected tile size for "
                                                  f"{'wet' if wet else 'dry'} rooms in the facts (finishes)")
        elif c.get("joint_m") is None:
            res = MR.blocked(method=TL.METHOD, spec=MS.tile(sel), net_installed_m2=room["area_m2"],
                             line_id=floor_ln["line_id"], location=loc,
                             reason="JOINT_WIDTH_NOT_ESTABLISHED: tile_constraints.joint_m is a design input")
        else:
            res = TL.best(geo, MS.tile(sel), c)["selected"] if room["rect"] else \
                TL.best_polygon(geo, MS.tile(sel), c)["selected"]
        mats.append(res)
        if res["state"] == "BLOCKED":
            unresolved.append({"room_id": room["room_id"], "floor": room["floor"], "item": floor_ln["item_code"] +
                               " (material)", "reason": res["blocked_by"]})
        if c.get("joint_m") is not None:
            cands = [MS.tile(x) for x in MS.OWNER_TILE_SIZES]
            if sel and sel not in [x["spec_id"] for x in cands]:
                cands.append(MS.tile(sel))
            rows = TL.compare(geo, cands, sel or cands[0]["spec_id"], c, polygon=not room["rect"])
            for x in rows:
                x.pop("result", None)
                x.pop("tried", None)
                if not sel:
                    x["role"] = "CANDIDATE (no size selected in the facts)"
                    x["recommendation"] = ""
                x.update(room_id=room["room_id"], floor=room["floor"], line_id=floor_ln["line_id"])
            comps.extend(rows)
        if wet:
            wl = [x for x in ls if x["item_code"].startswith("FIN.WP.")]
            spec = MS.membrane((facts.get("membrane") or {}).get("spec_id") or MS.DEFAULT_MEMBRANE)
            doors = [{"door_id": x["physical_element"].split()[-1], "width_m": x["calculation"]["inputs"]["width_m"],
                      "depth_m": x["calculation"]["inputs"]["depth_m"]} for x in wl if x["item_code"] == "FIN.WP.DOORWAY"]
            mc = {"upturn_h_m": RS.rule("UP-WP-002", RULE_SET)["value"], "doorways": doors,
                  "doorway_detail": (facts.get("membrane") or {}).get("doorway_detail", "NOT_ESTABLISHED"),
                  "direction": "MIN_MATERIAL", "min_reusable_m": (facts.get("membrane") or {}).get("min_reusable_m"),
                  "rule_refs": [_ref("UP-WP-005"), _ref("UP-WP-002"), _ref("UP-WP-003")]}
            wp_floor = next((x for x in wl if x["item_code"] == "FIN.WP.FLOOR"), None)
            g2 = dict(geo, line_id=wp_floor["line_id"] if wp_floor else None,
                      perimeter_lm=room["runs_lm"]["perimeter"])
            mres = ML.plan(g2, spec, constraints=mc) if room["rect"] else ML.plan_polygon(g2, spec, constraints=mc)
            if mres["state"] != "BLOCKED":
                for comp in mres["components"]:
                    comp["line_ids"] = [x["line_id"] for x in wl if x["item_code"] == comp["item_code"]]
            else:
                unresolved.append({"room_id": room["room_id"], "floor": room["floor"], "item": "FIN.WP (membrane)",
                                   "reason": mres["blocked_by"]})
            mats.append(mres)
    return {"materials": mats, "comparisons": comps, "unresolved": unresolved}
