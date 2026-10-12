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
    en = " / ".join(AR.LEX[c][0] for c in codes) if codes else AR.UNNAMED[0]
    ar = " / ".join(AR.LEX[c][1] for c in codes) if codes else AR.UNNAMED[1]
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
                "symbols_inside": sp.get("symbols_inside") or {}}
        rooms.append(room)
        ded = [{"what": "obstructions inside the room (columns / shafts)", "m2": round(sp["hole_area_m2"], 6)}] \
            if sp["holes"] else []
        for k, fl in enumerate((sp.get("symbols_inside") or {}).get("stair_flights") or (), 1):
            st = (facts.get("stairs") or {}).get(floor) or (facts.get("stairs") or {}).get("*") or {}
            R = (st.get("riser_m") or {})
            treads = fl["tread_lines"] - 1
            inp = {"tread_lines": fl["tread_lines"], "treads": treads, "going_m": fl["going_m"], "width_m": fl["width_m"],
                   "run_m": fl["run_m"], "layer": fl["layer"], "riser_m": R.get("value_m"),
                   "riser_authority": R.get("authority")}
            if R.get("value_m"):
                L = math.hypot(fl["run_m"], treads * R["value_m"])
                lines.append(_line(ctx, item_code="FIN.STAIR.FLIGHT", room=room, element=f"flight {k}", unit="lm",
                                   net=round(L, 6), formula="pitch line nosing to nosing: hypot(treads x going, treads x "
                                   "riser)", inputs=inp, rule_id=None, ev="PROVISIONAL",
                                   notes="straight flight recognised from its tread lines; the railing / handrail adds "
                                         "its end extensions by detail (not in a plan); STAIR_DRAWN_ON_TWO_PLANS_REVIEW: "
                                         "a flight cut by the plan above is drawn on both plans - count it once"))
            else:
                q = (f"STAIR_RISER_NOT_ESTABLISHED: flight {k} ({fl['tread_lines']} tread lines, going "
                     f"{fl['going_m']:.3f} m, width {fl['width_m']:.2f} m, run {fl['run_m']:.2f} m) - the sloping length "
                     "needs the riser height (section / riser count of every flight between the two levels)")
                lines.append(_line(ctx, item_code="FIN.STAIR.FLIGHT", room=room, element=f"flight {k}", unit="lm",
                                   net=None, formula="pitch line nosing to nosing: hypot(treads x going, treads x riser)",
                                   inputs=inp, rule_id=None, rfi={"question": q, "unlocks": rid}))
                unresolved.append({"room_id": rid, "floor": floor, "item": "FIN.STAIR.FLIGHT", "reason": q})
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
        fk = FINISH_KIND[kind]
        wet = fk == "WET"
        lines.append(_line(ctx, item_code="FIN.FLOOR.WET_TILE" if wet else "FIN.FLOOR.PORCELAIN", room=room,
                           element="floor", unit="m2", net=sp["area_m2"], gross=round(sp["gross_outer_m2"], 6),
                           deductions=ded, formula="face area (TS01), obstructions deducted",
                           inputs={"dims": room["dims"]}, rule_id="UP-CER-001",
                           notes="; ".join(x for x in [
                               ("OPEN_PLAN: " + " + ".join(sp["codes"]) + " share one face (no partition between them); "
                                "one dry floor finish assumed for the whole space - split it if the finishes differ")
                               if open_plan else "", sp.get("issue") or ""] if x)))
        lines.append(_line(ctx, item_code="FIN.CEILING", room=room, element="ceiling", unit="m2", net=sp["area_m2"],
                           ev="PROVISIONAL", gross=round(sp["gross_outer_m2"], 6), deductions=ded,
                           formula="plan area of the room (the floor face)", inputs={"dims": room["dims"]},
                           rule_id=None, notes="ceiling type, bulkheads and coves are not in a plan; material BY_SPEC"))
        skirt = runs["wall"] + runs["column"] + runs["window_threshold"]
        sk_notes = (f"door / passage openings not skirted ({runs['door'] + runs['passage']:.2f} m); "
                    f"sill windows skirted ({runs['window_threshold']:.2f} m) - deduct any floor-level glazing")
        if runs["glazing_edge"] > 1e-6:
            sk_notes += f"; glazing edge {runs['glazing_edge']:.2f} m not skirted"
        if wet:
            tile_h = heights(floor, lvl, floor_above_level_m, facts)["WALL_TILE"]
            q = ("UP-CER-004: no skirting when the wall tile is full height; the wall tile height is not established"
                 f" (run {skirt:.2f} m if it is not full height)")
            lines.append(_line(ctx, item_code="FIN.SKIRTING", room=room, element="skirting", unit="lm", net=None,
                               formula="wall + column faces - door openings", inputs={"run_lm": round(skirt, 6)},
                               rule_id="UP-CER-004", rfi={"question": q, "unlocks": rid}, notes=sk_notes))
            unresolved.append({"room_id": rid, "floor": floor, "item": "FIN.SKIRTING", "reason": q})
        else:
            sk_ded = [{"what": "door / passage openings", "lm": round(runs["door"] + runs["passage"], 6)}]
            if runs["glazing_edge"] > 1e-6:
                sk_ded.append({"what": "glazing edge (floor-level window line)", "lm": round(runs["glazing_edge"], 6)})
            if runs["other"] > 1e-6:
                sk_ded.append({"what": "boundary that is not a wall / column face", "lm": round(runs["other"], 6)})
            lines.append(_line(ctx, item_code="FIN.SKIRTING", room=room, element="skirting", unit="lm",
                               net=round(skirt, 6), formula="room boundary - door / passage openings - glazing edge "
                               "(= wall + column faces + sill-window thresholds)",
                               inputs={k: round(v, 6) for k, v in runs.items()},
                               rule_id="UP-CER-003", gross=round(runs["boundary"], 6), deductions=sk_ded,
                               notes=sk_notes))
        if wet:
            wp_floor = sp["area_m2"]
            lines.append(_line(ctx, item_code="FIN.WP.FLOOR", room=room, element="wp_floor", unit="m2", net=wp_floor,
                               formula="room floor face", inputs={"dims": room["dims"]}, rule_id="UP-WP-001"))
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
                                   formula="wall run x height - openings", inputs=inputs, rule_id="UP-CER-009"))
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
