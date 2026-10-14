"""DOOR STANDARDS AND SCENARIOS (M9 Phase 2B-1, ARCH_TAKEOFF_V2.3 only) - the owner door rules of the knowledge
registry applied to the door model's elements, without changing any drawn dimension.

    door_category(el)                -> (category, basis): INTERNAL_PVC | BATHROOM_PVC | EXTERNAL_ALUMINIUM |
                                        MAIN_ENTRANCE | MAIN_ENTRANCE_CANDIDATE | ELEVATOR | CLASS_REVIEW |
                                        CLASS_UNRESOLVED (UP-DOOR-CLS-001 .. -005)
    required_opening(category, cad_m) -> UP-DOOR-OPEN-002: required nominal door opening, owner-required wall opening
                                        = max(CAD, nominal + 0.10 m), enlargement, OPENING_BELOW_OWNER_STANDARD
    door_height(category, facts)     -> UP-DOOR-HGT-001: schedule / section / elevation / dimension (facts with their
                                        authority), project fallback, owner reference height (HEIGHT_ASSUMED)
    door_scenarios(model, facts, *, openings, rooms) -> per element the AS_DRAWN and OWNER_REQUIRED values side by
                                        side, the views (AS_DRAWN / OWNER_REQUIRED / UNRESOLVED / EXCLUDED) and their
                                        totals; the two scenarios are never added together
    dependency_impacts(...)          -> UP-DOOR-DEP-001: what an enlargement touches (indicative, REVIEW_REQUIRED)
    elevator_schedule(...)           -> UP-ELEV-SCHED-001: the separate elevator quotation schedule

The CAD wall opening is the door model's structural opening (jamb to jamb; wall to wall for a provisional door). The
frame span, the nominal leaf (swing radius) and the finished clear passage are kept apart and never substituted.
Project-agnostic; stdlib only."""

from __future__ import annotations

from collections import Counter, defaultdict

from engine.source import door_model as DM
from engine.source import knowledge as K

POLICY_ID = "DOOR_STANDARDS_V1"
TOL_M = 0.001
INTERNAL, BATH, EXTERNAL = "INTERNAL_PVC", "BATHROOM_PVC", "EXTERNAL_ALUMINIUM"
MAIN, MAIN_CAND, ELEVATOR = "MAIN_ENTRANCE", "MAIN_ENTRANCE_CANDIDATE", "ELEVATOR"
REVIEW, UNRESOLVED = "CLASS_REVIEW", "CLASS_UNRESOLVED"
BATH_CODES = ("BATHROOM",)


def door_category(el):
    cls = el.get("boq_class") or el.get("class")
    codes = {c for sd in el.get("sides") or () for c in sd.get("codes") or ()}
    if cls == DM.LIFT:
        return ELEVATOR, "a lift space or a lift door block (UP-DOOR-CLS-005)"
    if cls == DM.MAIN:
        return MAIN, "the identified main entrance (UP-DOOR-CLS-004)"
    if cls == "MAIN_ENTRANCE_CANDIDATE":
        return MAIN_CAND, "a main-entrance candidate (UP-DOOR-CLS-004): not identified"
    if cls == DM.PVC:
        if codes & set(BATH_CODES):
            return BATH, "internal door with a bathroom on one side (UP-DOOR-CLS-003)"
        return INTERNAL, "interior spaces on both sides (UP-DOOR-CLS-001)"
    if cls == DM.ALU:
        return EXTERNAL, "an exterior space or the facade on one side (UP-DOOR-CLS-002)"
    if cls == DM.CLASS_REVIEW:
        return REVIEW, el.get("class_evidence") or "class review"
    return UNRESOLVED, el.get("class_evidence") or "class not established"


def required_opening(category, cad_m):
    """UP-DOOR-OPEN-002 for one door. The main entrance keeps its drawn width (no ordinary standard); an elevator
    entrance is excluded; a door of unsettled class takes the standard every candidate class shares, or a range."""
    if cad_m is None:
        return {"state": "BLOCKED", "why": "no CAD wall opening (the door closes no gap)"}
    if category == MAIN:
        return {"state": "AS_DRAWN_ONLY", "cad_wall_opening_m": cad_m, "owner_required_wall_opening_m": cad_m,
                "enlargement_m": 0.0, "required_nominal_door_m": None,
                "why": "main entrance: actual drawing dimensions and approved specifications (UP-DOOR-CLS-004); the "
                       "ordinary opening standard is never applied"}
    if category == ELEVATOR:
        return {"state": "EXCLUDED", "why": "elevator entrance: quoted on the elevator schedule (UP-DOOR-CLS-005)"}
    if category in (MAIN_CAND,):
        return {"state": "AS_DRAWN_ONLY", "cad_wall_opening_m": cad_m, "owner_required_wall_opening_m": cad_m,
                "enlargement_m": 0.0, "required_nominal_door_m": None,
                "why": "a main-entrance candidate: measured as drawn until the main entrance is identified"}
    cands = [category] if category in (INTERNAL, BATH, EXTERNAL) else [INTERNAL, EXTERNAL]
    rows = []
    for c in cands:
        s = K.door_standard(c)
        req = max(cad_m, s["required_wall_opening_m"])
        enl = req - cad_m
        nominal_fit = cad_m - s["allowance_m"] if cad_m > s["required_wall_opening_m"] + TOL_M else \
            s["required_nominal_door_m"]
        rows.append({"category": c, "required_nominal_door_m": s["required_nominal_door_m"],
                     "architectural_wall_opening_m": s["required_wall_opening_m"],
                     "owner_required_wall_opening_m": round(req, 6), "enlargement_m": round(enl, 6),
                     "nominal_door_for_opening_m": round(nominal_fit, 6),
                     "nominal_basis": "RULE_DERIVED (CAD opening - 0.10 m; a schedule overrides it)"
                     if cad_m > s["required_wall_opening_m"] + TOL_M else "OWNER_REQUIRED_NOMINAL"})
    req = {round(r["owner_required_wall_opening_m"], 6) for r in rows}
    out = dict(rows[0], state="ESTABLISHED" if len(req) == 1 else "RANGE", cad_wall_opening_m=cad_m,
               rule=K.ref("UP-DOOR-OPEN-002"), candidates=rows if len(rows) > 1 else None)
    out["flags"] = []
    if rows[0]["enlargement_m"] > TOL_M:
        out["flags"].append("OPENING_BELOW_OWNER_STANDARD")
    if len(rows) > 1:
        out["flags"].append("CLASS_NOT_SETTLED_SAME_STANDARD" if len(req) == 1 else "CLASS_NOT_SETTLED_RANGE")
        if len(req) > 1:
            out["owner_required_wall_opening_m"] = {"low": min(req), "high": max(req)}
    return out


def door_height(category, facts):
    """UP-DOOR-HGT-001: a facts height with its authority (schedule / section / elevation / dimension: SOURCE ...;
    an owner project fact), then the project fallback DOOR_ASSUMED, then the owner reference height (ASSUMED)."""
    if category == ELEVATOR:
        return {"value_m": None, "state": "NOT_APPLICABLE", "source": "elevator entrance (not measured)"}
    oh = (facts or {}).get("opening_heights") or {}
    item = {INTERNAL: DM.PVC, BATH: DM.PVC, EXTERNAL: DM.ALU, MAIN: DM.MAIN}.get(category)
    for key in [k for k in (item, category, "DOOR") if k]:
        h = oh.get(key)
        if h and h.get("value_m") is not None:
            src = str(h.get("authority") or "")
            return {"value_m": h["value_m"], "state": "SOURCE", "source": f"facts opening_heights.{key}",
                    "authority": src, "precedence": "APPROVED_DRAWING" if src.upper().startswith("SOURCE")
                    else "PROJECT_DECISION"}
    if oh.get("DOOR_ASSUMED"):
        return {"value_m": oh["DOOR_ASSUMED"]["value_m"], "state": "ASSUMED",
                "source": "facts opening_heights.DOOR_ASSUMED (project fallback)",
                "authority": oh["DOOR_ASSUMED"].get("authority"), "precedence": "PROJECT_DECISION",
                "flags": ["HEIGHT_ASSUMED"]}
    ref_cat = category if category in (INTERNAL, BATH, EXTERNAL, MAIN) else INTERNAL
    h = K.reference_height(ref_cat)
    flags = ["HEIGHT_ASSUMED"]
    if ref_cat == MAIN:
        flags.append("MAIN_ENTRANCE_FALLBACK_SUBJECT_TO_PROJECT_CONTEXT")
    return {"value_m": h, "state": "ASSUMED", "source": f"owner reference height {ref_cat} (UP-DOOR-HGT-001)",
            "authority": "UP-DOOR-HGT-001", "precedence": "OWNER_RULE", "flags": flags}


def door_model_facts(facts):
    """the facts handed to the door model under ARCH_TAKEOFF_V2.3: the given facts plus the owner reference height of
    each released class as '<class>_ASSUMED' (UP-DOOR-HGT-001), read by the door model after any source height and
    after the project fallback DOOR_ASSUMED - so a verified height always wins and a fallback stays ASSUMED."""
    import copy
    f = copy.deepcopy(facts) if facts else {}
    oh = f.setdefault("opening_heights", {})
    for cls, cat in ((DM.PVC, INTERNAL), (DM.ALU, EXTERNAL), (DM.MAIN, MAIN)):
        oh.setdefault(cls + "_ASSUMED", {"value_m": K.reference_height(cat),
                                         "authority": f"ASSUMED: owner reference height {cat} (UP-DOOR-HGT-001)"})
    return f


def dependency_impacts(enlargement_m, height, wall_t_m, jambs, side_scopes):
    """UP-DOOR-DEP-001: indicative impacts of an enlargement (never BOQ lines; REVIEW_REQUIRED)."""
    d, t = enlargement_m, wall_t_m or 0.0
    h = (height or {}).get("value_m")
    out = {"release": "REVIEW_REQUIRED", "enlargement_m": round(d, 6), "height_basis": (height or {}).get("state"),
           "impacts": []}

    def add(trade, what, qty, unit):
        out["impacts"].append({"trade": trade, "what": what, "delta": None if qty is None else round(qty, 6),
                               "unit": unit})
    add("OPENINGS", "wall opening area", None if h is None else d * h, "m2")
    add("MASONRY", "blockwork deduction", None if h is None else d * h, "m2")
    for i, sc in enumerate(side_scopes):
        fin = "plaster + wall tile" if sc == "WET" else "plaster + paint" if sc == "DRY" else None
        if fin:
            add("WALL_FINISH", f"side {i + 1} ({sc}): {fin} deduction", None if h is None else d * h, "m2 per trade")
        if sc == "DRY":
            add("FLOOR_FINISH", f"side {i + 1}: skirting (stops at the wider opening)", -d, "lm")
    add("PLASTER", "head soffit / reveals", d * t, "m2")
    wet = "WET" in side_scopes
    add("MARBLE" if wet else "FLOOR_FINISH", "threshold / doorway strip", d * t, "m2")
    if wet:
        add("WATERPROOFING", "doorway membrane continuation", d * t, "m2")
    add("CONCRETE", "lintel span", d, "m (span; bearing to check)")
    kinds = [str(j or "") for j in jambs or ()]
    cols = sum(1 for k in kinds if k.startswith("COLUMN"))
    out["structural"] = ("STRUCTURAL_INTERFACE_BLOCKS_ENLARGEMENT: both jambs are columns" if cols == 2 else
                         "STRUCTURAL_INTERFACE_REVIEW: one jamb is a column - the enlargement can only go to the "
                         "masonry side" if cols == 1 else
                         "JAMB_POSITION_NOT_DRAWN: a wall-to-wall closure" if any(k.startswith("CLOSURE") for k in kinds)
                         else "masonry jambs: no structural interface found in the plan")
    out["never"] = "an enlarged opening declared buildable, or any downstream quantity released automatically"
    return out


def _view(el):
    if el.get("boq_class") == DM.LIFT:
        return "EXCLUDED"
    return "AS_DRAWN" if el.get("released") else "UNRESOLVED"


def door_scenarios(model, facts, *, openings, rooms):
    """-> {"rows": [...], "views": {...}, "conservation": {...}} for every door element of the building model."""
    from engine.source import owner_finish_scope as OFS
    op = {(o["floor"], o["opening_id"]): o for o in openings}
    scope_of = {r["room_id"]: OFS.finish_scope(r)["scope"] for r in rooms}
    rows = []
    for el in model["elements"]:
        cat, basis = door_category(el)
        cad = el.get("structural_opening_width_m")
        req = required_opening(cat, cad)
        h = door_height(cat, facts)
        o = op.get((el["floor"], el.get("opening_id"))) or {}
        width_state = "CONFIRMED" if el["state"] == DM.CONFIRMED else el["state"]
        flags = list(req.get("flags") or []) + list(h.get("flags") or [])
        if el["state"] == DM.PROVISIONAL:
            flags.append("PROVISIONAL_WIDTH: the wall-to-wall closure of a door with no band opening")
        if el.get("hold"):
            flags.append("WIDTH_HELD: " + el["hold"])
        hv = h.get("value_m")

        def area(w, state_w):
            if w is None or hv is None:
                return {"m2": None, "state": "BLOCKED"}
            st = "CONFIRMED" if state_w == "CONFIRMED" and h["state"] == "SOURCE" else \
                "ASSUMED" if state_w == "CONFIRMED" else "PROVISIONAL"
            return {"m2": round(w * hv, 6), "state": st}
        req_w = req.get("owner_required_wall_opening_m")
        req_w_num = req_w["high"] if isinstance(req_w, dict) else req_w
        row = {"element_id": el["element_id"], "floor": el["floor"], "opening_id": el.get("opening_id"),
               "state": el["state"], "boq_class": el.get("boq_class"), "category": cat, "category_basis": basis,
               "released_as_drawn": bool(el.get("released")), "view": _view(el),
               "spaces": [sd.get("room_name") or sd.get("kind") for sd in el.get("sides") or ()],
               "as_drawn": {"cad_wall_opening_m": cad, "width_source": el.get("structural_opening_source"),
                            "width_state": width_state, "frame_width_m": el.get("frame_width_m"),
                            "nominal_leaf_width_m": el.get("nominal_leaf_width_m"),
                            "clear_passage_m": "NOT_MEASURED (finished clear width is not in a plan)",
                            "height": h, "wall_opening_area": area(cad, width_state)},
               "owner_required": {"state": req["state"],
                                  "required_nominal_door_m": req.get("required_nominal_door_m"),
                                  "owner_required_wall_opening_m": req_w,
                                  "enlargement_m": req.get("enlargement_m"),
                                  "nominal_door_for_opening_m": req.get("nominal_door_for_opening_m"),
                                  "nominal_basis": req.get("nominal_basis"),
                                  "wall_opening_area": area(req_w_num, width_state) if req_w_num is not None else
                                  {"m2": None, "state": "BLOCKED"},
                                  "nominal_door_area": area(req.get("nominal_door_for_opening_m"), width_state)
                                  if req.get("nominal_door_for_opening_m") is not None else
                                  {"m2": None, "state": "NOT_APPLICABLE"},
                                  "head_height_basis": "the door height (the 0.10 m rule covers the width only: OQ-02)",
                                  "why": req.get("why"), "candidates": req.get("candidates")},
               "review_status": "MODIFICATION_PROPOSED_NOT_APPROVED" if (req.get("enlargement_m") or 0) > TOL_M else
                                "NO_MODIFICATION",
               "flags": flags, "rules": ["UP-DOOR-OPEN-002", "UP-DOOR-HGT-001", "UP-DOOR-AREA-001"]}
        if (req.get("enlargement_m") or 0) > TOL_M:
            sides = [scope_of.get(sd.get("room_id")) for sd in el.get("sides") or ()]
            row["dependency_impacts"] = dependency_impacts(req["enlargement_m"], h, el.get("wall_t_m"),
                                                           o.get("jambs"), sides)
        rows.append(row)
    return {"policy": POLICY_ID, "rule_set": K.RULE_SET, "rule_set_digest": K.digest(), "rows": rows,
            "views": _views(rows), "conservation": _conservation(rows, model),
            "never": ["the AS_DRAWN and OWNER_REQUIRED scenarios added together",
                      "a drawn width overwritten by an owner value", "an assumed area in a confirmed total"]}


def _views(rows):
    v = {"AS_DRAWN": defaultdict(lambda: {"count": 0, "width_m": 0.0, "area_confirmed_m2": 0.0,
                                          "area_assumed_m2": 0.0, "area_blocked": 0}),
         "OWNER_REQUIRED": defaultdict(lambda: {"count": 0, "below_standard": 0, "enlargement_m": 0.0,
                                                "wall_opening_m": 0.0, "wall_opening_area_assumed_m2": 0.0,
                                                "wall_opening_area_confirmed_m2": 0.0}),
         "UNRESOLVED": Counter(), "EXCLUDED": Counter()}
    for r in rows:
        if r["view"] == "EXCLUDED":
            v["EXCLUDED"][r["category"]] += 1
            continue
        if r["view"] == "UNRESOLVED":
            v["UNRESOLVED"][f"{r['category']} / {r['state']}"] += 1
            continue
        a = v["AS_DRAWN"][r["boq_class"]]
        a["count"] += 1
        a["width_m"] += r["as_drawn"]["cad_wall_opening_m"] or 0.0
        ar = r["as_drawn"]["wall_opening_area"]
        if ar["state"] == "CONFIRMED":
            a["area_confirmed_m2"] += ar["m2"]
        elif ar["state"] in ("ASSUMED", "PROVISIONAL"):
            a["area_assumed_m2"] += ar["m2"]
        else:
            a["area_blocked"] += 1
        o = v["OWNER_REQUIRED"][r["category"]]
        q = r["owner_required"]
        o["count"] += 1
        if "OPENING_BELOW_OWNER_STANDARD" in r["flags"]:
            o["below_standard"] += 1
        o["enlargement_m"] += q.get("enlargement_m") or 0.0
        w = q.get("owner_required_wall_opening_m")
        o["wall_opening_m"] += (w["high"] if isinstance(w, dict) else w) or 0.0
        wa = q["wall_opening_area"]
        if wa["state"] == "CONFIRMED":
            o["wall_opening_area_confirmed_m2"] += wa["m2"]
        elif wa["m2"] is not None:
            o["wall_opening_area_assumed_m2"] += wa["m2"]
    rnd = lambda d: {k: {kk: round(vv, 6) if isinstance(vv, float) else vv for kk, vv in x.items()}
                     for k, x in sorted(d.items())}
    return {"AS_DRAWN": rnd(v["AS_DRAWN"]), "OWNER_REQUIRED": rnd(v["OWNER_REQUIRED"]),
            "UNRESOLVED": dict(sorted(v["UNRESOLVED"].items())), "EXCLUDED": dict(sorted(v["EXCLUDED"].items())),
            "note": "AS_DRAWN = what the drawing establishes (released doors); OWNER_REQUIRED = the same doors under "
                    "the owner standard (a proposed modification, not approved); never added together"}


def _conservation(rows, model):
    ids = [r["element_id"] for r in rows]
    by = Counter(r["view"] for r in rows)
    return {"elements": len(model["elements"]), "rows": len(rows), "by_view": dict(by),
            "ok": len(ids) == len(set(ids)) == len(model["elements"])}


def _dims(room):
    if room.get("rect"):
        a, b = room["rect"]
        return round(min(a, b), 4), round(max(a, b), 4)
    xs = [p[0] for p in room.get("polygon_m") or ()]
    ys = [p[1] for p in room.get("polygon_m") or ()]
    return (round(min(max(xs) - min(xs), max(ys) - min(ys)), 4), round(max(max(xs) - min(xs), max(ys) - min(ys)), 4)) \
        if xs else (None, None)


def elevator_schedule(model, rooms, stacked_shafts):
    """UP-ELEV-SCHED-001: one row per shaft (a stacked shaft footprint, or a LIFT-labelled space): CAD dimensions,
    landings with their opening widths, floors served, status (CONFIRMED_LIFT / CANDIDATE) and what is missing."""
    by_face = {(r["floor"], r["face_id"]): r for r in rooms}
    groups = []
    seen = set()
    for i, sh in enumerate(stacked_shafts or ()):
        faces = list(zip(sh["floors"], sh["face_ids"]))
        groups.append({"shaft_id": f"SHAFT-{i + 1}", "faces": faces, "basis": "STACKED_FOOTPRINT"})
        seen |= set(faces)
    for r in rooms:
        if "LIFT" in (r.get("codes") or ()) and (r["floor"], r["face_id"]) not in seen:
            groups.append({"shaft_id": f"LIFT-{r['room_id']}", "faces": [(r["floor"], r["face_id"])],
                           "basis": "LIFT_LABEL"})
    out = []
    lift_doors = [el for el in model["elements"] if el.get("boq_class") == DM.LIFT]
    for g in groups:
        landings = []
        for fl, fid in g["faces"]:
            for c in model.get("lift_candidates") or ():
                if c["floor"] == fl and c.get("shaft_face_id") == fid:
                    landings.append({"floor": fl, "opening_id": c["opening_id"], "width_m": round(c["width_m"], 4),
                                     "status": "CANDIDATE", "evidence": c["evidence"]})
            # a lift opening record names its floor, not its shaft face: it is attached when this group is the
            # only lift-labelled space of the floor (otherwise it is listed as unassigned)
            lifts_here = [x for x in groups if x["basis"] == "LIFT_LABEL" and any(f == fl for f, _ in x["faces"])]
            if len(lifts_here) == 1 and lifts_here[0] is g:
                for o in model.get("lift_openings") or ():
                    if o.get("floor") == fl:
                        landings.append({"floor": fl, "opening_id": o.get("opening_id"),
                                         "width_m": round(o.get("width_m") or 0.0, 4), "status": "CONFIRMED_LIFT",
                                         "evidence": "an opening into a lift space"})
            for el in lift_doors:
                if el["floor"] == fl and any(sd.get("face_id") == fid for sd in el["sides"]):
                    landings.append({"floor": fl, "opening_id": el.get("opening_id"),
                                     "width_m": el.get("structural_opening_width_m"), "status": "CONFIRMED_LIFT",
                                     "evidence": el.get("class_evidence")})
        rm = [by_face[f] for f in g["faces"] if f in by_face]
        dims = sorted({_dims(r) for r in rm})
        labelled = any("LIFT" in (r.get("codes") or ()) for r in rm)
        status = "CONFIRMED_LIFT" if labelled or any(x["status"] == "CONFIRMED_LIFT" for x in landings) else \
            "CANDIDATE" if landings else "SHAFT_WITHOUT_LANDING"
        ref = K.rule("UP-ELEV-SCHED-001")["logic"]["reference_shaft_m"]
        out.append({"shaft_id": g["shaft_id"], "basis": g["basis"], "status": status,
                    "floors": sorted({f for f, _ in g["faces"]}),
                    "shaft_dimensions_m": [list(d) for d in dims],
                    "shaft_area_m2": [round(r["area_m2"], 4) for r in rm],
                    "reference_comparison": [{"reference_m": ref, "differs_m": [round(d[0] - ref[0], 4),
                                                                               round(d[1] - ref[1], 4)]}
                                             for d in dims if d[0] is not None],
                    "landings": landings, "number_of_landings": len(landings),
                    "floors_served": sorted({x["floor"] for x in landings}),
                    "number_of_elevators": 1 if landings else 0,
                    "missing": ["car size and capacity", "landing door height and type", "pit depth",
                                "overrun / headroom", "machine room or machine-room-less", "manufacturer data"] +
                               ([] if labelled else ["a lift label or lift schedule confirming the shaft is a lift"]),
                    "in_door_boq": False})
    return {"policy": POLICY_ID, "rule": "UP-ELEV-SCHED-001", "shafts": out,
            "note": "elevator landing doors are supplied by the elevator company: never in the architectural door "
                    "quantities (UP-DOOR-CLS-005)"}


def policy_record():
    return {"policy": POLICY_ID, "rule_set": K.RULE_SET, "rule_set_digest": K.digest(),
            "rules": ["UP-DOOR-CLS-001", "UP-DOOR-CLS-002", "UP-DOOR-CLS-003", "UP-DOOR-CLS-004", "UP-DOOR-CLS-005",
                      "UP-DOOR-OPEN-002", "UP-DOOR-HGT-001", "UP-DOOR-AREA-001", "UP-DOOR-DEP-001", "UP-ELEV-SCHED-001"],
            "tolerance_m": TOL_M}
