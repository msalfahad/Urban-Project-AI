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


READINGS = ("STRUCTURAL_OPENING", "DOOR_LEAF", "CLEAR_PASSAGE")


def opening_record_v27(el, category):
    """ARCH_TAKEOFF_V2.7 (UP-DOOR-OPEN-003, knowledge registry 1.2.0): the door's opening values kept apart - the
    CAD-measured structural opening, the door leaf (swing radius, per leaf), the frame span, the finished clear
    passage (not in a plan), the owner minimum (1.00 / 0.90 m) and the frame / installation allowance (only from an
    independently supported source; the 1.1.0 registry's 0.10 m requires confirmation, UP-DOOR-OPEN-002) - and the
    minimum checked against each reading it may refer to. The enlargement is proposed, never applied; which reading
    the owner minimum refers to is owner question OQ-05. Nothing measured is changed."""
    lg = K.rule("UP-DOOR-OPEN-003")["logic"]
    old = K.rule("UP-DOOR-OPEN-002")["logic"]
    cad = el.get("structural_opening_width_m")
    leaves = [round(x, 6) for x in el.get("nominal_leaf_width_m") or ()]
    frame = el.get("frame_width_m")
    mn = lg["owner_minimum_m"].get(category)
    rec = {"rule": "UP-DOOR-OPEN-003", "category": category,
           "structural_opening_m": None if cad is None else round(cad, 6),
           "structural_opening_source": el.get("structural_opening_source"),
           "door_leaf_m": leaves, "door_leaf_source": "the swing radius, one per leaf (the drawn leaf)",
           "frame_m": None if frame is None else round(frame, 6), "frame_source": el.get("frame_source"),
           "clear_passage_m": None, "clear_passage_state": "NOT_ESTABLISHED (a finished clear width is not in a plan)",
           "owner_minimum_m": mn, "minimum_applies_to": lg["applies_to"],
           "allowance": {"value_m": None, "state": "NOT_ESTABLISHED", "supported_by": None,
                         "registry_1_1_0_m": old.get("allowance_registry_1_1_0_m"),
                         "registry_1_1_0_state": "REQUIRES_CONFIRMATION (UP-DOOR-OPEN-002, registry 1.2.0)",
                         "accepted_sources": lg["allowance_sources"]}}
    if category == ELEVATOR:
        return dict(rec, status="EXCLUDED", readings=[], review_status="NO_MODIFICATION", owner_question=None,
                    why="elevator entrance: the elevator schedule (UP-DOOR-CLS-005)")
    if mn is None:
        return dict(rec, status="AS_DRAWN_ONLY", readings=[], review_status="NO_MODIFICATION", owner_question=None,
                    why="no ordinary minimum for this category (main entrance: drawing and specification, "
                        "UP-DOOR-CLS-004; an unsettled class: the class first)")
    reg_alw = old.get("allowance_registry_1_1_0_m") or 0.0
    rd = []
    if cad is None:
        rd.append({"reading": "STRUCTURAL_OPENING", "state": "NOT_ESTABLISHED", "why": "no structural opening"})
    else:
        sh = round(max(0.0, mn - cad), 6)
        rd.append({"reading": "STRUCTURAL_OPENING", "state": "EVALUATED", "value_m": round(cad, 6), "shortfall_m": sh,
                   "proposed_enlargement_m": sh,
                   "meaning": "the minimum is the wall's structural opening (no allowance added)"})
    if not leaves or cad is None:
        rd.append({"reading": "DOOR_LEAF", "state": "NOT_ESTABLISHED", "why": "no leaf drawn" if not leaves else
                   "no structural opening"})
    else:
        lw = round(sum(leaves), 6)
        sh = round(max(0.0, mn - lw), 6)
        rd.append({"reading": "DOOR_LEAF", "state": "EVALUATED", "value_m": lw, "shortfall_m": sh,
                   "proposed_enlargement_m": {"low": round(max(0.0, mn - cad), 6),
                                              "high_with_registry_allowance": round(max(0.0, mn + reg_alw - cad), 6)},
                   "meaning": "the minimum is the door (its leaf); the wall opening then needs the minimum plus the "
                              "frame / installation allowance, which is not established (low: no allowance; high: the "
                              "1.1.0 registry's value, requiring confirmation)"})
    rd.append({"reading": "CLEAR_PASSAGE", "state": "NOT_ESTABLISHED",
               "why": "the finished clear passage (frame stops, leaf thickness) is not in a plan"})
    ev = [r for r in rd if r["state"] == "EVALUATED"]
    below = [r for r in ev if r["shortfall_m"] > TOL_M]
    status = ("NOT_ESTABLISHED" if not ev else "BELOW_MINIMUM_ON_EVERY_READING" if len(below) == len(ev) else
              "COMPLIES_ON_EVERY_READING" if not below else "READINGS_DISAGREE")
    return dict(rec, readings=rd, status=status,
                review_status="MODIFICATION_PROPOSED_NOT_APPROVED" if below else "NO_MODIFICATION",
                owner_question=lg["question"])


def _required_v27(rec, cad_m):
    """the V2.6 row fields of required_opening, from the V2.7 opening record (the structural reading: the lower bound
    of every reading; never the 0.10 m allowance)."""
    st = next((r for r in rec.get("readings") or () if r["reading"] == "STRUCTURAL_OPENING"), None)
    if rec["status"] in ("EXCLUDED",):
        return {"state": "EXCLUDED", "why": rec["why"]}
    if rec["status"] == "AS_DRAWN_ONLY":
        return {"state": "AS_DRAWN_ONLY", "cad_wall_opening_m": cad_m, "owner_required_wall_opening_m": cad_m,
                "enlargement_m": 0.0, "required_nominal_door_m": None, "why": rec["why"], "flags": []}
    if st is None or st["state"] != "EVALUATED":
        return {"state": "BLOCKED", "why": "no CAD wall opening (the door closes no gap)", "flags": []}
    flags = [f"OPENING_BELOW_OWNER_MINIMUM_{r['reading']}" for r in rec["readings"]
             if r["state"] == "EVALUATED" and r["shortfall_m"] > TOL_M]
    flags.append("DOOR_MINIMUM_REFERENCE_UNRESOLVED (OQ-05)")
    return {"state": "ESTABLISHED_ON_THE_STRUCTURAL_READING", "cad_wall_opening_m": cad_m,
            "owner_required_wall_opening_m": round(max(cad_m, rec["owner_minimum_m"]), 6),
            "enlargement_m": st["shortfall_m"], "required_nominal_door_m": None, "nominal_door_for_opening_m": None,
            "nominal_basis": "NOT_ESTABLISHED (the allowance is not established: UP-DOOR-OPEN-003)",
            "why": "the owner minimum on the structural opening, no allowance added; the other readings are in the "
                   "opening record", "rule": K.ref("UP-DOOR-OPEN-003"), "flags": flags}


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


def door_scenarios(model, facts, *, openings, rooms, v27=False):
    """-> {"rows": [...], "views": {...}, "conservation": {...}} for every door element of the building model.
    v27 (ARCH_TAKEOFF_V2.7 only): each row carries its opening_record (opening_record_v27) and the owner-required
    values come from it (the 1.1.0 0.10 m allowance is never applied); False is the V2.3 .. V2.6 path, unchanged."""
    from engine.source import owner_finish_scope as OFS
    op = {(o["floor"], o["opening_id"]): o for o in openings}
    scope_of = {r["room_id"]: OFS.finish_scope(r)["scope"] for r in rooms}
    rows = []
    for el in model["elements"]:
        cat, basis = door_category(el)
        cad = el.get("structural_opening_width_m")
        orec = opening_record_v27(el, cat) if v27 else None
        req = _required_v27(orec, cad) if v27 else required_opening(cat, cad)
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
                                  "head_height_basis": "the door height (no head allowance is established: OQ-02)"
                                  if v27 else "the door height (the 0.10 m rule covers the width only: OQ-02)",
                                  "why": req.get("why"), "candidates": req.get("candidates")},
               "review_status": "MODIFICATION_PROPOSED_NOT_APPROVED" if (req.get("enlargement_m") or 0) > TOL_M else
                                "NO_MODIFICATION",
               "flags": flags, "rules": ["UP-DOOR-OPEN-002", "UP-DOOR-HGT-001", "UP-DOOR-AREA-001"]}
        if v27:
            row["rules"][0] = "UP-DOOR-OPEN-003"
            row["opening_record"] = orec
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


RECON_COLUMNS = ("element_id", "floor", "opening_id", "category", "as_drawn_wall_opening_m", "measured_jamb_span_m",
                 "jamb_basis", "door_leaf_m", "finished_clear_width_m", "owner_minimum_m", "frame_allowance_m",
                 "drawn_symbol_difference_m", "boq_width_m", "enlargement_structural_m", "enlargement_leaf_low_m",
                 "enlargement_leaf_high_m", "within_gap_low", "within_gap_high", "consultant_review",
                 "structural_review", "review_reasons", "status")


def reconciliation_v271(rows, openings):
    """ARCH_TAKEOFF_V2.7.1 (UP-DOOR-OPEN-003 1.3.0): the door-standard reconciliation of every door row of
    door_scenarios(v27=True) - the as-drawn wall opening (the band gap jamb to jamb) and the measured jamb span (the
    door symbol's own jamb lines) apart, the leaf, the finished clear width (not in a plan), the owner minimum, a frame
    allowance only from an accepted source (the drawn leaf-to-opening difference is CAD geometry, reported, never an
    allowance), the proposed enlargement on each reading, whether it fits inside the drawn gap, and the consultant /
    structural review it needs. Nothing is applied: boq_width_m is the width every BOQ line measures.
    -> {"policy", "rule", "doors", "summary", "never"}."""
    lg = K.rule("UP-DOOR-OPEN-003")["logic"]
    reg_alw = (K.rule("UP-DOOR-OPEN-002")["logic"].get("allowance_registry_1_1_0_m") or 0.0)
    op = {(o["floor"], o["opening_id"]): o for o in openings}
    out = []
    for r in rows:
        rec = r.get("opening_record") or {}
        o = op.get((r["floor"], r.get("opening_id"))) or {}
        v = o.get("opening_v27") or {}
        cad = rec.get("structural_opening_m")
        gap = v.get("wall_gap_m") if v.get("wall_gap_m") is not None else cad
        span = v.get("jamb_span_m") if v.get("jamb_span_m") is not None else cad
        leaves = list(rec.get("door_leaf_m") or ())
        mn = rec.get("owner_minimum_m")
        alw = rec.get("allowance") or {}
        d = {"element_id": r["element_id"], "floor": r["floor"], "opening_id": r.get("opening_id"),
             "category": r["category"], "spaces": r.get("spaces"),
             "as_drawn_wall_opening_m": None if gap is None else round(gap, 6),
             "measured_jamb_span_m": None if span is None else round(span, 6),
             "jamb_basis": v.get("decision") or ("NO_JAMB_LINES" if cad is not None else "NOT_ESTABLISHED"),
             "jambs": o.get("jambs"),
             "door_leaf_m": leaves, "door_leaf_state": "DRAWN_LEAF (swing radius)" if leaves else "NOT_ESTABLISHED",
             "finished_clear_width_m": None,
             "finished_clear_width_state": "NOT_ESTABLISHED (frame stops and leaf thickness are not in a plan)",
             "owner_minimum_m": mn,
             "owner_minimum_reference": "UNRESOLVED (D-16 / OQ-05): " + str(lg.get("applies_to")),
             "frame_allowance": {
                 "value_m": alw.get("value_m"), "state": alw.get("state") or "NOT_ESTABLISHED",
                 "supported_by": alw.get("supported_by"), "accepted_sources": alw.get("accepted_sources"),
                 "registry_1_1_0_m": alw.get("registry_1_1_0_m"),
                 "registry_1_1_0_state": alw.get("registry_1_1_0_state"),
                 "drawn_symbol_difference_m": round(cad - sum(leaves), 6) if cad is not None and leaves else None,
                 "drawn_symbol_difference_note": "the structural opening minus the drawn leaf: CAD symbol geometry, "
                                                 "not an accepted allowance source"},
             "boq_width_m": None if cad is None else round(cad, 6),
             "status": rec.get("status") or "NOT_ESTABLISHED", "applied_to_boq": False}
        if mn is None or cad is None:
            d.update(proposed_enlargement={"STRUCTURAL_OPENING": {"m": None, "required_opening_m": None},
                                           "DOOR_LEAF": {"leaf_shortfall_m": None, "low_m": None,
                                                         "high_m_with_unconfirmed_allowance": None},
                                           "CLEAR_PASSAGE": {"state": "NOT_ESTABLISHED"}},
                     wall_remainder_m=None, within_as_drawn_gap=None, remainder_after_m=None,
                     review={"consultant": "NOT_REQUIRED", "structural": "NOT_REQUIRED", "reasons": [],
                             "why": rec.get("why") or "no owner minimum applies (or no structural opening)"})
            out.append(d)
            continue
        lw = sum(leaves) if leaves else None
        low = round(max(0.0, mn - cad), 6)
        high = round(max(0.0, mn + reg_alw - cad), 6) if lw is not None else low
        req_low, req_high = round(cad + low, 6), round(cad + high, 6)
        rem = round(max(0.0, (gap or cad) - (span or cad)), 6)
        within = {"low": req_low <= (gap or cad) + TOL_M, "high": req_high <= (gap or cad) + TOL_M}
        reasons = []
        if low > TOL_M or high > TOL_M:
            if rem > TOL_M and min(req_low, req_high) > (span or cad) + TOL_M:
                reasons.append("WALL_REMAINDER_CUT")
            if not within["low"] or not within["high"]:
                reasons.append("WALL_CUT_BEYOND_DRAWN_OPENING")
            reasons.append("LINTEL_SPAN_INCREASE")
            if "COLUMN_JAMB" in (o.get("jambs") or ()):
                reasons.append("COLUMN_AT_A_JAMB")
        definite = low > TOL_M
        d.update(proposed_enlargement={
            "STRUCTURAL_OPENING": {"m": low, "required_opening_m": req_low,
                                   "meaning": "the minimum is the structural opening (no allowance)"},
            "DOOR_LEAF": {"leaf_shortfall_m": None if lw is None else round(max(0.0, mn - lw), 6),
                          "low_m": low if lw is not None else None,
                          "high_m_with_unconfirmed_allowance": high if lw is not None else None,
                          "meaning": "the minimum is the door leaf: the opening grows by the minimum minus the opening "
                                     "(no allowance) up to the minimum plus the registry 1.1.0 allowance "
                                     f"({reg_alw:g} m, requires confirmation) minus the opening"},
            "CLEAR_PASSAGE": {"state": "NOT_ESTABLISHED", "why": "the finished clear passage is not in a plan"}},
            wall_remainder_m=rem, within_as_drawn_gap=within,
            remainder_after_m={"low": round((gap or cad) - req_low, 6) if within["low"] else None,
                               "high": round((gap or cad) - req_high, 6) if within["high"] else None},
            review={"consultant": "REQUIRED" if definite else ("REQUIRED_UNDER_THE_LEAF_READING" if high > TOL_M
                                                               else "NOT_REQUIRED"),
                    "structural": "REQUIRED" if definite and reasons else (
                        "REQUIRED_UNDER_THE_LEAF_READING" if high > TOL_M else "NOT_REQUIRED"),
                    "reasons": reasons,
                    "why": "a proposed enlargement changes other trades and is never auto-released "
                           "(UP-DOOR-DEP-001); cutting drawn wall or lengthening the lintel needs the structural "
                           "engineer" if reasons else "the door meets the minimum on every reading"})
        out.append(d)
    out.sort(key=lambda d: (d["floor"], str(d["opening_id"]), d["element_id"]))
    below = [d for d in out if (d["proposed_enlargement"]["STRUCTURAL_OPENING"]["m"] or 0) > TOL_M]
    return {"policy": "URBAN_DOOR_STANDARD_RECONCILIATION_V1", "rule": "UP-DOOR-OPEN-003", "doors": out,
            "summary": {"doors": len(out), "below_minimum_structural": len(below),
                        "within_drawn_gap": sum(1 for d in below if d["within_as_drawn_gap"]["low"]),
                        "structural_review": sum(1 for d in out if d["review"]["structural"] == "REQUIRED"),
                        "consultant_review": sum(1 for d in out if d["review"]["consultant"] == "REQUIRED")},
            "never": ["the CAD geometry changed to satisfy the minimum", "an enlargement applied to a quantity",
                      "the registry 1.1.0 allowance imposed", "the drawn symbol difference read as an allowance"]}


def reconciliation_csv_rows(rec):
    rows = []
    for d in rec["doors"]:
        pe = d["proposed_enlargement"]
        rows.append({"element_id": d["element_id"], "floor": d["floor"], "opening_id": d["opening_id"],
                     "category": d["category"], "as_drawn_wall_opening_m": d["as_drawn_wall_opening_m"],
                     "measured_jamb_span_m": d["measured_jamb_span_m"], "jamb_basis": d["jamb_basis"],
                     "door_leaf_m": " + ".join(f"{x:g}" for x in d["door_leaf_m"]),
                     "finished_clear_width_m": d["finished_clear_width_m"], "owner_minimum_m": d["owner_minimum_m"],
                     "frame_allowance_m": d["frame_allowance"]["value_m"],
                     "drawn_symbol_difference_m": d["frame_allowance"]["drawn_symbol_difference_m"],
                     "boq_width_m": d["boq_width_m"], "enlargement_structural_m": pe["STRUCTURAL_OPENING"]["m"],
                     "enlargement_leaf_low_m": pe["DOOR_LEAF"]["low_m"],
                     "enlargement_leaf_high_m": pe["DOOR_LEAF"]["high_m_with_unconfirmed_allowance"],
                     "within_gap_low": (d["within_as_drawn_gap"] or {}).get("low"),
                     "within_gap_high": (d["within_as_drawn_gap"] or {}).get("high"),
                     "consultant_review": d["review"]["consultant"], "structural_review": d["review"]["structural"],
                     "review_reasons": "; ".join(d["review"]["reasons"]), "status": d["status"]})
    return rows


def policy_record():
    return {"policy": POLICY_ID, "rule_set": K.RULE_SET, "rule_set_digest": K.digest(),
            "rules": ["UP-DOOR-CLS-001", "UP-DOOR-CLS-002", "UP-DOOR-CLS-003", "UP-DOOR-CLS-004", "UP-DOOR-CLS-005",
                      "UP-DOOR-OPEN-002", "UP-DOOR-HGT-001", "UP-DOOR-AREA-001", "UP-DOOR-DEP-001", "UP-ELEV-SCHED-001"],
            "tolerance_m": TOL_M}
