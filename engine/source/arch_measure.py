"""ARCHITECTURAL MEASUREMENT (M9 S2) - canonical BOQ lines per room from the spaces of arch_rooms (generic, stdlib).

    measure(floor_result, *, floor, project_id, revision_set_sha256, facts=None, floor_above_level_m=None, documents=())
        -> {"rooms": [...], "lines": [...], "openings": [...], "unresolved": [...]}
    validate_facts(facts) -> the facts, or FactsError

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

from engine.source import arch_rooms as AR
from engine.source import boq_line as BL
from engine.source import plane_poly as PP
from engine.source import rule_store as RS
from engine.source import tile_layout as TL
from engine.source import wall_height as WH

POLICY_ID = "ARCH_MEASURE_V1"
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
    return RS.rule_ref(rule_id, RULE_SET)


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


def measure(fr, *, floor, project_id, revision_set_sha256, facts=None, floor_above_level_m=None, documents=(),
            floor_level_m=None):
    facts = validate_facts(facts) or {}
    ctx = {"project_id": project_id, "revision_set_sha256": revision_set_sha256, "documents": list(documents)}
    rooms, lines, unresolved = [], [], []
    ops = fr["openings_by_id"]
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
                "evidence": sp.get("evidence") or {}, "fixture_conflict": sp.get("fixture_conflict")}
        typed_by_evidence = sp.get("label_source") not in (None, "TEXT")
        rooms.append(room)
        ded = [{"what": "obstructions inside the room (columns / shafts)", "m2": round(sp["hole_area_m2"], 6)}] \
            if sp["holes"] else []
        flights = (sp.get("symbols_inside") or {}).get("stair_flights") or ()
        for k, fl in enumerate(flights, 1):
            sl, su = _stair_lines(ctx, room, rid, floor, k, fl, facts)
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
        if kind in NO_FINISH:
            ec = "ARCH.EXTERIOR" if kind == AR.EXTERIOR else "ARCH.SPACE"
            lines.append(_line(ctx, item_code=ec, room=room, element="space", unit="m2", net=sp["area_m2"],
                               gross=round(sp["gross_outer_m2"], 6), deductions=ded, rule_id="UP-CER-001",
                               formula="face area (TS01)", inputs={"dims": room["dims"]},
                               notes=f"{kind} space: no internal floor / ceiling finish line"))
            continue
        stair_m2 = _stair_in_room(sp, flights, fr["unit_m"]) if flights else 0.0
        if stair_m2 > 1e-6:
            ded = ded + [{"what": "stair treads drawn inside the room (marble: UP-STAIR-005, never also porcelain)",
                          "m2": round(stair_m2, 6)}]
        fk = FINISH_KIND[kind]
        wet = fk == "WET"
        lines.append(_line(ctx, item_code="FIN.FLOOR.WET_TILE" if wet else "FIN.FLOOR.PORCELAIN", room=room,
                           element="floor", unit="m2", net=round(sp["area_m2"] - stair_m2, 6),
                           gross=round(sp["gross_outer_m2"], 6), deductions=ded,
                           formula="face area (TS01), obstructions deducted" +
                                   (", stair treads deducted (UP-STAIR-005)" if stair_m2 > 1e-6 else ""),
                           inputs={"dims": room["dims"]}, rule_id="UP-CER-001",
                           ev="PROVISIONAL" if typed_by_evidence else None,
                           notes="; ".join(x for x in [
                               ("OPEN_PLAN: " + " + ".join(sp["codes"]) + " share one face (no partition between them); "
                                "one dry floor finish assumed for the whole space - split it if the finishes differ")
                               if open_plan else "", sp.get("issue") or "", sp.get("fixture_conflict") or ""] if x)))
        lines.append(_line(ctx, item_code="FIN.CEILING", room=room, element="ceiling", unit="m2", net=sp["area_m2"],
                           ev="PROVISIONAL", gross=round(sp["gross_outer_m2"], 6),
                           deductions=[d for d in ded if not d["what"].startswith("stair")],
                           formula="plan area of the room (the floor face)", inputs={"dims": room["dims"]},
                           rule_id=None, notes="ceiling type, bulkheads and coves are not in a plan; material BY_SPEC"))
        skirt = runs["wall"] + runs["column"] + runs["window_threshold"]
        sk_notes = (f"door / passage openings not skirted ({runs['door'] + runs['passage']:.2f} m); "
                    f"sill windows skirted ({runs['window_threshold']:.2f} m) - deduct any floor-level glazing")
        if runs["glazing_edge"] > 1e-6:
            sk_notes += f"; glazing edge {runs['glazing_edge']:.2f} m not skirted"
        if wet:
            hs0 = heights(floor, lvl, floor_above_level_m, facts)
            tile_h, clear_h = hs0["WALL_TILE"], hs0["PAINT"]
            full = None
            if tile_h["state"] == WH.ESTABLISHED and tile_h["governing"] == "DERIVED_CLEAR_HEIGHT":
                full = True                               # derived to the ceiling: the tile is full height
            elif tile_h["state"] == WH.ESTABLISHED and clear_h["state"] == WH.ESTABLISHED:
                full = tile_h["value_m"] >= clear_h["value_m"] - 1e-6
            if full is None:
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
        if wet:
            wp_floor = round(sp["area_m2"] - stair_m2, 6)
            lines.append(_line(ctx, item_code="FIN.WP.FLOOR", room=room, element="wp_floor", unit="m2", net=wp_floor,
                               formula="room floor face", inputs={"dims": room["dims"]}, rule_id="UP-WP-001",
                               ev="PROVISIONAL" if typed_by_evidence else None,
                               notes=sp.get("issue") if typed_by_evidence else ""))
            for d in doors:
                lines.append(_line(ctx, item_code="FIN.WP.DOORWAY", room=room, element=f"doorway {d['opening_id']}",
                                   unit="m2", net=round(d["width_m"] * d["wall_t_m"], 6),
                                   formula="door width x wall thickness", rule_id="UP-WP-003",
                                   inputs={"width_m": round(d["width_m"], 4), "depth_m": round(d["wall_t_m"], 4)},
                                   notes="DOORWAY_UPTURN_DETAIL_REQUIRED; DOORWAY_DOUBLE_COVERAGE_REVIEW"))
            if sp["closure_ids"]:
                q = (f"{len(sp['closure_ids'])} door(s) closed by a door-symbol closure: the doorway depth (wall "
                     "thickness) is not established for their doorway pieces")
                unresolved.append({"room_id": rid, "floor": floor, "item": "FIN.WP.DOORWAY", "reason": q})
            up = RS.rule("UP-WP-002", RULE_SET)["value"]
            lines.append(_line(ctx, item_code="FIN.WP.UPTURN", room=room, element="wp_upturn", unit="m2",
                               net=round(runs["perimeter"] * up, 6),
                               formula=f"one-sided boundary incl. doorways x {up:g} m (no door deduction)",
                               inputs={"perimeter_lm": round(runs["perimeter"], 6), "upturn_h_m": up},
                               rule_id="UP-WP-002", notes="DOORWAY_UPTURN_DETAIL_REQUIRED" if doors or sp["closure_ids"]
                               else ""))
        hs = heights(floor, lvl, floor_above_level_m, facts)
        oh = (facts or {}).get("opening_heights") or {}
        run = runs["perimeter"]
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
    if fr.get("walls"):
        sl, su = _wall_lines(ctx, floor, fr["walls"], facts)
        lines += sl
        unresolved += su
    openings = []
    for o in fr["openings"]:
        code = {"DOOR": "ARCH.DOOR", "WINDOW": "ARCH.WINDOW", "PASSAGE": "ARCH.PASSAGE"}[o["kind"]]
        host = [r["room_id"] for r in rooms if o["opening_id"] in r["doors"] + r["windows"] + r["passages"]]
        rec = {"opening_id": o["opening_id"], "floor": floor, "kind": o["kind"], "width_m": round(o["width_m"], 4),
               "wall_t_m": round(o["wall_t_m"], 4), "rooms": host, "door_symbol": o.get("door_symbol"),
               "jambs": [o["start_jamb"], o["end_jamb"]]}
        openings.append(rec)
        pseudo = {"room_id": host[0] if host else f"{floor}-EXT", "floor": floor,
                  "name_en": " | ".join(r["name_en"] for r in rooms if r["room_id"] in host) or "exterior",
                  "name_ar": " | ".join(r["name_ar"] for r in rooms if r["room_id"] in host) or "خارجي"}
        hh = ((facts or {}).get("opening_heights") or {}).get(o["kind"])
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
            "unresolved": unresolved, "counts": dict(Counter(r["class"] for r in rooms))}


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


def _stair_lines(ctx, room, rid, floor, k, fl, facts):
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
    else:
        q = (f"STAIR_RISER_NOT_ESTABLISHED: flight {k} ({fl['kind'].lower()}, {fl['tread_lines']} tread lines, going "
             f"{fl['going_m']:.3f} m, width {fl['width_m']:.2f} m, run {fl['run_m']:.2f} m) - the visible riser and the "
             "sloping length need the riser height (section / riser count of every flight between the two levels)")
        for code, unit, f_ in (("FIN.MARBLE.RISER", "m2", "sum of riser widths x (riser height - tread marble thickness)"),
                               ("FIN.STAIR.FLIGHT", "lm", "pitch line nosing to nosing: hypot(run, treads x riser)")):
            lines.append(_line(ctx, item_code=code, room=room, element=el, unit=unit, net=None, formula=f_,
                               inputs=inp, rule_id="UP-STAIR-003" if code == "FIN.MARBLE.RISER" else None,
                               rfi={"question": q, "unlocks": rid}))
        unresolved.append({"room_id": rid, "floor": floor, "item": f"FIN.MARBLE.RISER / FIN.STAIR.FLIGHT {el}",
                           "reason": q})
    return lines, unresolved


def _treads_in(poly_m, holes_m, fl, u):
    return sum(PP.region_area_in_convex(poly_m, holes_m, [(x * u, y * u) for x, y in q]) for q in fl["tread_quads"])


def _stair_in_room(sp, flights, u):
    """plan area of the drawn treads inside the room (m2): deducted from its floor finish (UP-STAIR-005)."""
    return sum(_treads_in(sp["polygon_m"], sp["hole_polygons_m"], fl, u) for fl in flights
               if not fl.get("drawn_on_plan_below"))


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
    (r"^STAIR_LANDING_POLYGON_NOT_ESTABLISHED", "SOURCE", "arch_measure._landing",
     "draw / give the landing outline (or the stair-well outline) of the stair enclosure"),
    (r"^BLOCK_WALL_NOT_ESTABLISHED", "SOURCE", "arch_measure._wall_lines",
     "give the wall material by thickness (legend / specification) and the block height (slab soffit / beam depth)"),
    (r"^MERGED_SPACE", "REVIEW", "arch_rooms.spaces",
     "draw the missing partition / door closure between the spaces, or confirm the open space and its finishes"),
    (r"^MIXED_SPACE", "REVIEW", "arch_rooms.spaces", "confirm one finish for the open plan, or draw the split"),
    (r"^UNLABELLED_SPACE.*SHX font", "SOFTWARE", "tools.arch_intake.decode_text",
     "decode the SHX big-font text (font file or code map), or label the space for review"),
    (r"^UNLABELLED_SPACE", "SOURCE", "arch_rooms.spaces / arch_rooms._evidence",
     "name the space (room word, room-tag block or fixtures), or confirm it is not a room (shaft, duct, void)"),
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
            "never": ["a wall height from a floor-to-floor interval alone", "a constant wall-tile height",
                      "a finish on a merged / unlabelled space", "an opening height that is not sourced"]}


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
