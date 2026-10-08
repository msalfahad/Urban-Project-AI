"""BEAM_REBAR_READINESS (pre-S6) - the safe occurrence / detail / component input layer for superstructure beam rebar
(simple beams + continuous beams). Generic, stdlib only, project-agnostic. NO kg is computed here.

What it decides (each function returns a state AND the evidence for it; nothing is chosen silently):

  width_match()          drawn width vs schedule width -> MATCH / MINOR_DRAFTING_DIFFERENCE / SOURCE_CONFLICT /
                         UNRESOLVED. A mismatch is evidence: it never changes the geometry or the mark.
  binding_decision()     one beam tag against EVERY candidate member: hard gates (orientation against the member's own
                         direction / tangent, within extent, distance window, schedule width, the span not already
                         carrying another mark). Distance is a gate, never a tie-break: no nearest-label binding, no
                         text-rotation-only binding, no leftover sharing.
  terminate()            occurrence conservation: every physical member / tag terminates exactly once.
  span_sequence()        ordered physical CB spans against the schedule spans; SPAN_LENGTH_SOURCE_CONFLICT /
                         SPAN_COUNT_CONFLICT preserve both sides; schedule lengths are never shared out arithmetically
                         and physical geometry is never capped to agree.
  bind_dimension_rule()  a parametric typical-detail dimension ('0.22 Ln', '7.5cm', ...) is bound to a bar end and a
                         support face only when its defpoints coincide with them (tolerance); otherwise UNRESOLVED.
  cb_bar_runs()          continuous-beam bar runs from the schedule frame topology (spans crossed, straddled supports,
                         legs) + bound typical rules: a bar crossing a support is ONE run, never duplicated per span.
  simple_bar_run()       a simple-beam bar family between support faces (straight run) with development / hooks kept
                         as separate components.
  stirrup_readiness()    diameter / rate / count / path / legs / hooks / end zones / first-last rule, separately:
                         a count may release while the mass stays blocked.
  side_rebar_readiness() REMARKS / MIDDLE REINT. side-steel semantics (faces, vertical arrangement, length, ends).
  candidate_invariant()  a component releases from a candidate set only when every candidate defines it identically.
  component_status()     STRAIGHT_RUN state x additions -> READY / READY_LOWER_BOUND / ... (the S5 principle: a
                         verified straight run stays verified while development is blocked; the COMPLETE bar is then a
                         LOWER_BOUND, the straight portion is not demoted).
  provenance_template() / provenance_ready()   the fields every future S6 component must carry (generic ELEMENT_*
                         identity, BAR_RUN_ID for continuous bars).
"""

from __future__ import annotations

import math

POLICY_ID = "BEAM_REBAR_READINESS_PRE_S6_V1"

STATUSES = ("READY", "READY_LOWER_BOUND", "PROVISIONAL_ONLY", "BLOCKED_COMPONENT", "NO_APPLICABLE_DETAIL",
            "SOURCE_CONFLICT", "NOT_APPLICABLE")
RELEASABLE = ("READY", "READY_LOWER_BOUND")
TAG_TERMINALS = ("BOUND_VERIFIED", "BOUND_SOURCE_CONFLICT", "BOUND_CANDIDATE", "DUPLICATE_TAG",
                 "TAG_WITHOUT_GEOMETRY", "BLOCKED_BINDING", "NOT_BEAM", "OUT_OF_SCOPE_FAMILY")
GEOMETRY_TERMINALS = ("BOUND_VERIFIED", "BOUND_SOURCE_CONFLICT", "BOUND_CANDIDATE", "GEOMETRY_WITHOUT_TAG",
                      "BLOCKED_BINDING", "NOT_BEAM", "OUT_OF_SCOPE_FAMILY")
WIDTH_STATES = ("MATCH", "MINOR_DRAFTING_DIFFERENCE", "SOURCE_CONFLICT", "UNRESOLVED")
RULE_AUTHORITIES = ("SOURCE_EXPLICIT", "SOURCE_DERIVED_HIGH_CONFIDENCE", "PROJECT_PATTERN_ONLY", "UNRESOLVED")
FEEDS_S6 = ("SOURCE_EXPLICIT", "SOURCE_DERIVED_HIGH_CONFIDENCE")      # only these may feed S6 automatically
RUN_STATES = ("VERIFIED", "LOWER_BOUND", "BLOCKED_UNQUANTIFIED", "BAR_RUN_GEOMETRY_CONFLICT", "NOT_APPLICABLE")
COMPONENT_STATES = ("KNOWN", "VERIFIED", "LOWER_BOUND", "PROVISIONAL", "BLOCKED_UNQUANTIFIED", "NOT_APPLICABLE",
                    "SOURCE_CONFLICT", "NOT_STATED")
OPENING_STATES = ("PRESENT", "NOT_APPLICABLE", "CANDIDATE")
PROVENANCE_FIELDS = ("PROJECT_ID", "DRAWING_ID", "DRAWING_SHA", "SOURCE_HANDLES", "SCHEDULE_HANDLES",
                     "GEOMETRY_HANDLES", "SUPPORT_IDS", "DETAIL_ID", "RULE_ID", "CONVENTION_ID", "AUTHORITY_STATE",
                     "RELEASE_STATE", "ENGINE_COMMIT", "REGISTER_VERSION", "CALCULATION_ROUND",
                     "ELEMENT_OCCURRENCE_ID", "ELEMENT_MARK", "ELEMENT_FAMILY")


class BeamReadinessError(ValueError):
    pass


# ------------------------------------------------------------------------------------------------------- widths
def width_match(drawn_mm, schedule_mm, *, match_mm: float = 10.0, minor_mm: float = 30.0) -> dict:
    """Drawn vs scheduled breadth. The state is evidence only - the caller keeps the drawn geometry and the plan
    mark."""
    if drawn_mm is None or schedule_mm is None:
        return {"DRAWN_WIDTH": drawn_mm, "SCHEDULE_WIDTH": schedule_mm, "DELTA": None,
                "TOLERANCE": [match_mm, minor_mm], "WIDTH_MATCH_STATE": "UNRESOLVED"}
    d = float(drawn_mm) - float(schedule_mm)
    st = ("MATCH" if abs(d) <= match_mm else "MINOR_DRAFTING_DIFFERENCE" if abs(d) <= minor_mm else
          "SOURCE_CONFLICT")
    return {"DRAWN_WIDTH": float(drawn_mm), "SCHEDULE_WIDTH": float(schedule_mm), "DELTA": round(d, 1),
            "TOLERANCE": [match_mm, minor_mm], "WIDTH_MATCH_STATE": st}


# ------------------------------------------------------------------------------------------------------ binding
def _angle_diff(a, b):
    """Smallest difference between two undirected directions in degrees (0..90)."""
    d = abs((a - b) % 180.0)
    return min(d, 180.0 - d)


def binding_decision(tag: dict, candidates: list, *, schedule_width_mm=None, angle_tol_deg: float = 10.0,
                     max_distance_mm: float = 950.0, width_match_mm: float = 10.0,
                     width_minor_mm: float = 30.0) -> dict:
    """Evaluate ONE tag against ALL candidate members (every alternative is returned with its gate results).

    tag        {handle, mark, rotation_deg}
    candidates [{member_id, kind (LINE | ARC), distance_mm, distance_limit_mm (optional), within_extent (bool),
                 member_dir_deg (member direction, or the arc tangent at the tag's angle), width_mm,
                 span_other_marks [marks bound by OTHER tags on the span the tag would land on],
                 same_mark_adjacent (bool: the same mark is bound on an adjacent span of this member),
                 same_mark_on_span (bool: another tag of the SAME mark already holds the span the tag would land on),
                 inside_physical_extent (bool | None: the tag projects inside the member's drawn extent, not only
                 inside the extent tolerance), supported_both_ends (bool | None)}]

    Evidence ladder (distance is a WINDOW, never a ranking; text rotation is never used alone):
      1. geometric exclusion - a candidate is DECISIVELY excluded when it is outside the extent or the distance window,
         when its span already carries a DIFFERENT mark, or when its direction / arc tangent is more than 2 x tol off;
      2. one geometric survivor -> bound; BOUND_VERIFIED when its own orientation is within tol, else BOUND_CANDIDATE;
      3. several survivors -> the schedule-width gate (a SOURCE_CONFLICT width excludes); one survivor ->
         BOUND_VERIFIED when its width MATCHes and its orientation is within tol, else BOUND_CANDIDATE;
      4. still several -> same-mark continuity on an adjacent span singles one out -> BOUND_CANDIDATE (positive
         evidence, but the alternatives are not excluded); otherwise BLOCKED_BINDING;
      5. no survivor: when exactly one candidate is excluded ONLY because another mark holds the span ->
         BOUND_SOURCE_CONFLICT (the geometry is known, two marks claim it); otherwise BLOCKED_BINDING
         (TAG_WITHOUT_GEOMETRY when there is no candidate at all).
    A winner is never BOUND_VERIFIED while an alternative is excluded by text rotation alone: it becomes BOUND_CANDIDATE
    and the alternative is listed in rotation_only_alternatives.
    A survivor whose width conflicts with the schedule stays bound; the caller terminates it BOUND_SOURCE_CONFLICT."""
    rows = []
    rot = (tag.get("rotation_deg") or 0.0) % 180.0
    for c in candidates:
        ang = None if c.get("member_dir_deg") is None else _angle_diff(rot, c["member_dir_deg"])
        w = width_match(c.get("width_mm"), schedule_width_mm, match_mm=width_match_mm, minor_mm=width_minor_mm)
        others = sorted({m for m in (c.get("span_other_marks") or []) if m != tag.get("mark")})
        lim = c.get("distance_limit_mm") or max_distance_mm
        excl = []
        if not c.get("within_extent"):
            excl.append("EXTENT")
        if c.get("distance_mm") is None or c["distance_mm"] > lim:
            excl.append("DISTANCE")
        if others:
            excl.append("SPAN_TAKEN")
        if ang is None or ang > 2 * angle_tol_deg:
            excl.append("ORIENTATION")
        rows.append({"member_id": c["member_id"], "kind": c.get("kind"), "distance_mm": c.get("distance_mm"),
                     "distance_limit_mm": lim, "orientation_diff_deg": None if ang is None else round(ang, 2),
                     "orientation_within_tol": ang is not None and ang <= angle_tol_deg, "width": w,
                     "span_other_marks": others, "same_mark_adjacent": bool(c.get("same_mark_adjacent")),
                     "supported_both_ends": c.get("supported_both_ends"),
                     "inside_physical_extent": c.get("inside_physical_extent"),
                     "same_mark_on_span": bool(c.get("same_mark_on_span")), "decisive_exclusions": excl})

    def rotation_only(r):
        # alternatives that only text rotation separates from the winner (a width conflict the winner does not share
        # is independent evidence, so it does not count as rotation-only)
        wc = r["width"]["WIDTH_MATCH_STATE"] == "SOURCE_CONFLICT"
        # an alternative the tag lies off the end of (outside its physical extent), or whose span already carries the
        # same mark from another tag (binding there would duplicate), is separated by drawing-position / coverage
        # evidence as well, so rotation is not alone
        return [a["member_id"] for a in rows if a is not r and a["decisive_exclusions"] == ["ORIENTATION"]
                and (wc or a["width"]["WIDTH_MATCH_STATE"] != "SOURCE_CONFLICT")
                and a["inside_physical_extent"] is not False and not a["same_mark_on_span"]]

    def out(decision, r, stage, why):
        alt = rotation_only(r) if r else []
        if decision == "BOUND_VERIFIED" and alt:
            decision, why = "BOUND_CANDIDATE", why + f"; {alt} excluded by text rotation alone (never decisive)"
        return {"decision": decision, "member_id": r["member_id"] if r else None, "stage": stage,
                "width_state": r["width"]["WIDTH_MATCH_STATE"] if r else None, "why": why,
                "rotation_only_alternatives": alt, "candidates": rows}
    if not rows:
        return out("TAG_WITHOUT_GEOMETRY", None, 1, "no member in reach")
    surv = [r for r in rows if not r["decisive_exclusions"]]
    if len(surv) == 1:
        r = surv[0]
        return out("BOUND_VERIFIED" if r["orientation_within_tol"] else "BOUND_CANDIDATE", r, 1,
                   "the only candidate not decisively excluded" +
                   ("" if r["orientation_within_tol"] else " (its own orientation is outside the tolerance)"))
    if len(surv) > 1:
        w_ok = [r for r in surv if r["width"]["WIDTH_MATCH_STATE"] != "SOURCE_CONFLICT"]
        if len(w_ok) == 1:
            r = w_ok[0]
            ver = r["width"]["WIDTH_MATCH_STATE"] == "MATCH" and r["orientation_within_tol"]
            return out("BOUND_VERIFIED" if ver else "BOUND_CANDIDATE", r, 2,
                       f"{len(surv)} geometric survivors; the schedule-width gate excludes all but one")
        pool = w_ok or surv
        cont = [r for r in pool if r["same_mark_adjacent"]]
        if len(cont) == 1:
            return out("BOUND_CANDIDATE", cont[0], 3,
                       f"{len(pool)} survivors after the width gate; same-mark continuity singles one out (the "
                       "alternatives are not excluded)")
        return out("BLOCKED_BINDING", None, 3, f"{len(pool)} candidates survive every gate "
                   f"({[r['member_id'] for r in pool]}) - not decided by distance")
    only_taken = [r for r in rows if r["decisive_exclusions"] == ["SPAN_TAKEN"]]
    if len(only_taken) == 1:
        return out("BOUND_SOURCE_CONFLICT", only_taken[0], 1,
                   f"the member span is claimed by another mark ({only_taken[0]['span_other_marks']})")
    return out("BLOCKED_BINDING", None, 1, "every candidate is decisively excluded")


# --------------------------------------------------------------------------------------------------- conservation
def terminate(objects: list) -> dict:
    """objects [{object_id, kind (TAG | MEMBER_SPAN | ARC_BAND | FRAGMENT | RULE_POPULATION), terminal}] -> every object
    exactly once with a terminal of its kind's vocabulary."""
    seen, dup, bad = set(), [], []
    for o in objects:
        if o["object_id"] in seen:
            dup.append(o["object_id"])
        seen.add(o["object_id"])
        allowed = TAG_TERMINALS if o["kind"] == "TAG" else GEOMETRY_TERMINALS
        if o.get("terminal") not in allowed:
            bad.append((o["object_id"], o.get("terminal")))
    by = {}
    for o in objects:
        by.setdefault(o["kind"], {}).setdefault(o["terminal"], 0)
        by[o["kind"]][o["terminal"]] += 1
    return {"objects": len(objects), "unique": len(seen), "duplicates": dup, "invalid_terminals": bad,
            "by_kind_terminal": by, "all_terminate_once": not dup and not bad}


def span_tag_terminals(tags: list) -> dict:
    """tags bound to ONE physical span / arc: [{handle, mark, decision, width_state, why}] (any order) ->
    {terminals: {handle: (terminal, why)}, geometry: (terminal, why)}. The first tag of a mark (handle order) holds the
    span; a later tag of the same mark is a DUPLICATE_TAG; two different marks make every tag and the span
    BOUND_SOURCE_CONFLICT; a width conflict keeps the binding and makes it BOUND_SOURCE_CONFLICT. No tag ->
    GEOMETRY_WITHOUT_TAG."""
    if not tags:
        return {"terminals": {}, "geometry": ("GEOMETRY_WITHOUT_TAG", "no tag binds this span")}

    def key(h):
        try:
            return (0, int(str(h).split(":")[0], 16), str(h))
        except ValueError:
            return (1, 0, str(h))
    tags = sorted(tags, key=lambda t: key(t["handle"]))
    marks = sorted({t["mark"] for t in tags})
    out, seen = {}, set()
    for t in tags:
        if t["mark"] in seen:
            out[t["handle"]] = ("DUPLICATE_TAG", f"another {t['mark']} tag already holds this span")
            continue
        seen.add(t["mark"])
        if len(marks) > 1:
            out[t["handle"]] = ("BOUND_SOURCE_CONFLICT", f"the span carries {marks}")
        elif t["decision"] == "BOUND_SOURCE_CONFLICT":
            out[t["handle"]] = ("BOUND_SOURCE_CONFLICT", t.get("why"))
        elif t.get("width_state") == "SOURCE_CONFLICT":
            out[t["handle"]] = ("BOUND_SOURCE_CONFLICT", "drawn width conflicts with the schedule width")
        else:
            out[t["handle"]] = (t["decision"], t.get("why"))
    prim = [v[0] for v in out.values() if v[0] != "DUPLICATE_TAG"]
    if len(marks) > 1:
        geo = ("BOUND_SOURCE_CONFLICT", f"two marks claim the same physical span: {marks}")
    else:
        geo = ("BOUND_SOURCE_CONFLICT" if "BOUND_SOURCE_CONFLICT" in prim else
               "BOUND_CANDIDATE" if "BOUND_CANDIDATE" in prim else "BOUND_VERIFIED", None)
    return {"terminals": out, "geometry": geo}


def hanger_readiness(*, scheduled: dict | None, detailed: dict | None) -> dict:
    """scheduled {count, dia_mm, handle} | None (a hanger field in the schedule); detailed {count, dia_mm, extent,
    handle} | None (a hanger drawn in a typical / frame). Never invents a hanger: EXPLICITLY_SCHEDULED or DETAILED
    release a count only when count and diameter are printed; DETAILED_UNLABELLED and ABSENT never do."""
    if scheduled and scheduled.get("count") and scheduled.get("dia_mm"):
        return {"state": "EXPLICITLY_SCHEDULED", "count": scheduled["count"], "dia_mm": scheduled["dia_mm"],
                "extent": (detailed or {}).get("extent")}
    if detailed:
        if detailed.get("count") and detailed.get("dia_mm"):
            return {"state": "DETAILED", "count": detailed["count"], "dia_mm": detailed["dia_mm"],
                    "extent": detailed.get("extent")}
        return {"state": "DETAILED_UNLABELLED", "count": None, "dia_mm": None, "extent": None,
                "why": "drawn without count / diameter"}
    return {"state": "ABSENT", "count": None, "dia_mm": None, "extent": None,
            "why": "no hanger field and no hanger detail"}


def opening_components(relations: list) -> list:
    """relations [{member, relation (INSIDE_BAND | ON_FACE | LINEWORK_ENTERS_BAND)}] of source-identified openings for
    one beam. Only an opening outline INSIDE the band triggers the opening extras; anything else is NOT_APPLICABLE."""
    inside = [r for r in relations if r.get("relation") == "INSIDE_BAND"]
    fams = ("OPENING_EXTRA_TOP", "OPENING_EXTRA_BOTTOM", "OPENING_EXTRA_SIDE", "STIRRUP_EXTRA")
    if not inside:
        return [{"COMPONENT_FAMILY": "OPENING_EXTRA", "STATE": "NOT_APPLICABLE"}]
    return [{"COMPONENT_FAMILY": f, "STATE": "CANDIDATE", "openings": inside} for f in fams]


# ------------------------------------------------------------------------------------------------- CB span sequence
def span_sequence(plan_spans: list, schedule_spans: list, *, tol_m: float = 0.25, tol_rel: float = 0.08) -> dict:
    """plan_spans [{cc_m, clear_m, ...}] in plan order along the member; schedule_spans [m] in frame order (left to
    right). The plan drawing direction is not known, so both readings are tested:
      FORWARD / REVERSED   exactly one reading matches -> rows in schedule order (plan spans re-ordered);
      AMBIGUOUS            both readings match (the span-to-schedule mapping is not decided);
      NONE                 neither matches -> SPAN_LENGTH_SOURCE_CONFLICT (forward rows, both deltas kept).
    Never shares a schedule length across spans, never caps the plan."""
    n_p, n_s = len(plan_spans), len(schedule_spans)
    tot_p = sum(p["cc_m"] for p in plan_spans if p.get("cc_m") is not None)
    tot_s = sum(schedule_spans)

    def ok(seq):
        return all(p.get("cc_m") is not None and abs(p["cc_m"] - s) <= max(tol_m, tol_rel * s)
                   for p, s in zip(seq, schedule_spans))
    out = {"plan_total_cc_m": round(tot_p, 3), "schedule_total_m": round(tot_s, 3),
           "total_delta_m": round(tot_p - tot_s, 3), "never_shared": True, "never_capped": True}
    if n_p != n_s:
        rows = [{"SPAN_INDEX": i + 1, "PLAN": plan_spans[i] if i < n_p else None,
                 "SCHEDULE_SPAN_M": schedule_spans[i] if i < n_s else None, "DELTA_CC_M": None,
                 "DELTA_CC_M_REVERSED": None, "SPAN_STATE": "SPAN_COUNT_CONFLICT"} for i in range(max(n_p, n_s))]
        return dict(out, rows=rows, state="SPAN_COUNT_CONFLICT", orientation="NONE", plan_order=list(range(n_p)))
    fwd, rev = ok(plan_spans), ok(list(reversed(plan_spans)))
    orientation = ("AMBIGUOUS" if fwd and rev and n_p > 1 else "FORWARD" if fwd else "REVERSED" if rev else "NONE")
    order = list(range(n_p))[::-1] if orientation == "REVERSED" else list(range(n_p))
    rows = []
    for i, j in enumerate(order):
        p, s = plan_spans[j], schedule_spans[i]
        pr = plan_spans[n_p - 1 - i]
        d = None if p.get("cc_m") is None else round(p["cc_m"] - s, 3)
        dr = None if pr.get("cc_m") is None else round(pr["cc_m"] - s, 3)
        st = "MATCH" if d is not None and abs(d) <= max(tol_m, tol_rel * s) else "SPAN_LENGTH_SOURCE_CONFLICT"
        rows.append({"SPAN_INDEX": i + 1, "PLAN": p, "PLAN_POSITION": j + 1, "SCHEDULE_SPAN_M": s, "DELTA_CC_M": d,
                     "DELTA_CC_M_REVERSED": dr, "SPAN_STATE": st})
    state = "MATCH" if orientation in ("FORWARD", "REVERSED", "AMBIGUOUS") else "SPAN_LENGTH_SOURCE_CONFLICT"
    return dict(out, rows=rows, state=state, orientation=orientation, plan_order=order)


# ------------------------------------------------------------------------------------------- typical-detail rules
def bind_dimension_rule(dim: dict, *, bar_ends: list, faces: list, axes: list = (), tol_mm: float = 15.0) -> dict:
    """dim {handle, text, p2 (x), p3 (x)} (the two extension points along the beam axis); bar_ends [{bar, x}];
    faces [x]; axes [x]. Bound when one extension point is a support face (or an axis) and the other a bar end."""
    hits = {}
    for key in ("p2", "p3"):
        x = dim[key]
        hits[key] = {"bar_end": [b["bar"] for b in bar_ends if abs(b["x"] - x) <= tol_mm],
                     "face": [f for f in faces if abs(f - x) <= tol_mm],
                     "axis": [a for a in axes if abs(a - x) <= tol_mm]}
    ok = any(hits[a]["bar_end"] and (hits[b]["face"] or hits[b]["axis"]) for a, b in (("p2", "p3"), ("p3", "p2")))
    bar = next((hits[a]["bar_end"][0] for a, b in (("p2", "p3"), ("p3", "p2"))
                if hits[a]["bar_end"] and (hits[b]["face"] or hits[b]["axis"])), None)
    ref = next(("FACE" if hits[b]["face"] else "AXIS" for a, b in (("p2", "p3"), ("p3", "p2"))
                if hits[a]["bar_end"] and (hits[b]["face"] or hits[b]["axis"])), None)
    return {"handle": dim.get("handle"), "text": dim.get("text"), "bound": ok, "bar": bar, "measured_from": ref,
            "hits": hits, "state": "SOURCE_DERIVED_HIGH_CONFIDENCE" if ok else "UNRESOLVED"}


# -------------------------------------------------------------------------------------------------------- bar runs
def simple_bar_run(*, family_id: str, face_to_face_m, start_support: dict, end_support: dict, geometry_state: str,
                   extent_rule: dict) -> dict:
    """A simple-beam bar family between support faces. geometry_state: CONSISTENT | BAR_RUN_GEOMETRY_CONFLICT |
    UNRESOLVED. extent_rule {authority, rule_id, why}: the source authority that the family runs support to support."""
    run_ok = geometry_state == "CONSISTENT" and face_to_face_m is not None and face_to_face_m > 0 and \
        extent_rule.get("authority") in FEEDS_S6
    st = ("BAR_RUN_GEOMETRY_CONFLICT" if geometry_state == "BAR_RUN_GEOMETRY_CONFLICT" else
          "VERIFIED" if run_ok else "BLOCKED_UNQUANTIFIED")
    return {"BAR_RUN_ID": family_id, "START_LOCATION": {"support": start_support, "at": "FACE"},
            "INTERMEDIATE_SUPPORTS": [], "END_LOCATION": {"support": end_support, "at": "FACE"},
            "SPANS_CROSSED": [1], "STRAIGHT_SEGMENTS": ([{"from": "SUPPORT_1_FACE", "to": "SUPPORT_2_FACE",
                                                         "length_m": face_to_face_m, "state": st}] if run_ok else []),
            "SOURCE_EXTENT": extent_rule, "STRAIGHT_RUN_STATE": st,
            "STRAIGHT_RUN_M": face_to_face_m if run_ok else None}


def cb_bar_runs(*, occurrence_id: str, frame_bars: list, spans: list, supports: list, rules: dict) -> list:
    """Continuous-beam bar runs.

    frame_bars [{handle, role (BOTTOM | SUPPORT_TOP | CONTINUOUS_TOP | SPAN_TOP), u_start, u_end, straddles [k],
                 start_at_support, end_at_support, legs [x], label {count, dia, tag, kind} | None, binding}]
               (u = normalised span coordinate of the N.T.S. schedule frame: support k at u = k)
    spans      [{index (1..n), clear_m, cc_m, schedule_m}] physical spans in order
    supports   [{index (0..n), width_m, kind, ref}] the support at each u = k (width along the beam)
    rules      {bottom_extension: {authority, value_m, rule_id}, support_bar_each_side_factor: {authority, value,
                rule_id, span_basis}} - typical-detail rules already bound (bind_dimension_rule);
               optional per-bar overrides {by_bar: {handle: {bottom_extension | support_bar_each_side_factor: rule}}}
               (a rule bound for one bar topology is never applied to another, e.g. an edited frame bar)
    A bar crossing a support is ONE run with its spans crossed - never duplicated at the support."""
    out = []
    n = len(spans)
    sp = {s["index"]: s for s in spans}
    su = {s["index"]: s for s in supports}
    for b in frame_bars:
        brules = dict(rules, **((rules.get("by_bar") or {}).get(b["handle"]) or {}))
        lab = b.get("label") or {}
        cnt, dia = lab.get("count"), lab.get("dia")
        known = bool(cnt) and bool(dia) and b.get("binding") == "ONE_TO_ONE_PRINTED"
        k0 = int(math.floor(b["u_start"] + 1e-9))
        k1 = int(math.ceil(b["u_end"] - 1e-9))
        crossed = list(range(k0 + 1, k1 + 1)) if b["role"] != "SUPPORT_TOP" else []
        inter = list(b.get("straddles") or [])
        segs, missing, run_state = [], [], "BLOCKED_UNQUANTIFIED"
        role = b["role"]
        rid = f"{occurrence_id}:{role}:{b['handle']}"
        if role == "BOTTOM":
            full = [i for i in range(1, n + 1) if b["u_start"] <= i - 1 + 1e-6 and b["u_end"] >= i - 1e-6]
            ok = bool(full) and all(sp.get(i, {}).get("clear_m") for i in full) and \
                all(su.get(k, {}).get("width_m") is not None for k in inter)
            if ok:
                for i in full:
                    segs.append({"kind": "CLEAR_SPAN", "span": i, "length_m": sp[i]["clear_m"], "state": "VERIFIED"})
                for k in inter:
                    segs.append({"kind": "THROUGH_SUPPORT", "support": k, "length_m": su[k]["width_m"],
                                 "state": "VERIFIED"})
                ext = brules.get("bottom_extension") or {}
                for k in inter:
                    if ext.get("authority") in FEEDS_S6:
                        segs.append({"kind": "BEYOND_FAR_FACE", "support": k, "length_m": ext["value_m"],
                                     "state": "VERIFIED", "rule_id": ext.get("rule_id")})
                    else:
                        missing.append(f"extension beyond the far face of support {k} (no bound rule"
                                       + (f": {ext.get('why')}" if ext.get("why") else "") + ")")
                run_state = "LOWER_BOUND"
            else:
                missing.append("a crossed span or support width is not established")
            if b.get("start_at_support") and k0 == 0:
                missing.append("anchorage / development into end support 0")
            if b.get("end_at_support") and k1 == n:
                missing.append(f"anchorage / development into end support {n}")
        elif role == "SUPPORT_TOP":
            fac = brules.get("support_bar_each_side_factor") or {}
            k = inter[0] if len(inter) == 1 else None
            left, right = sp.get(k), sp.get(k + 1) if k is not None else None
            basis = fac.get("span_basis", "schedule_m")
            if k is not None and fac.get("authority") in FEEDS_S6 and left and right and \
                    left.get(basis) and right.get(basis) and su.get(k, {}).get("width_m") is not None:
                segs = [{"kind": "INTO_SPAN_LEFT", "span": k, "length_m": round(fac["value"] * left[basis], 4),
                         "state": "VERIFIED", "rule_id": fac.get("rule_id")},
                        {"kind": "THROUGH_SUPPORT", "support": k, "length_m": su[k]["width_m"], "state": "VERIFIED"},
                        {"kind": "INTO_SPAN_RIGHT", "span": k + 1, "length_m": round(fac["value"] * right[basis], 4),
                         "state": "VERIFIED", "rule_id": fac.get("rule_id")}]
                run_state = "VERIFIED"
            else:
                missing.append("support-bar extent not established (no bound typical rule / span / support width"
                               + (f": {fac.get('why')}" if fac.get("why") else "") + ")")
            crossed = [k] if k is not None else []
        else:   # CONTINUOUS_TOP / SPAN_TOP: interior end drawn N.T.S., no bound extent rule
            missing.append("interior end drawn N.T.S. (schedule frame); no bound extent rule")
            if b.get("legs"):
                missing.append("end leg drawn at the outer support, length not dimensioned (hook)")
        if not known:
            run_state = "BLOCKED_UNQUANTIFIED"
            missing.insert(0, f"count / diameter not bound one-to-one ({b.get('binding')})")
        out.append({"BAR_RUN_ID": rid, "ROLE": role, "COUNT": cnt or None, "DIA_MM": dia or None,
                    "LABEL": lab.get("tag"), "LABEL_KIND": lab.get("kind"), "START_LOCATION": {
                        "u": round(b["u_start"], 4), "at_support": b.get("start_at_support")},
                    "INTERMEDIATE_SUPPORTS": inter, "END_LOCATION": {"u": round(b["u_end"], 4),
                                                                     "at_support": b.get("end_at_support")},
                    "SPANS_CROSSED": crossed, "STRAIGHT_SEGMENTS": segs,
                    "STRAIGHT_RUN_M": round(sum(s["length_m"] for s in segs), 4) if segs else None,
                    "STRAIGHT_RUN_STATE": run_state, "MISSING": missing, "SOURCE_HANDLE": b["handle"],
                    "LEGS": b.get("legs") or []})
    return out


# ------------------------------------------------------------------------------------------------------- stirrups
def stirrup_readiness(*, dia_mm, rate_per_m, rate_state: str, distribution_m, width_state: str, depth_known: bool,
                      cover_known: bool, topology: dict, hooks_state: str, end_zone: dict, first_last: dict) -> dict:
    """Every stirrup facet separately. A count is a lower bound ceil(rate x distribution) (no +1 end bar, no end-zone
    densification); mass needs width, depth, cover, legs / topology, path and hooks - all of them."""
    out = {"DIAMETER": {"value": dia_mm,
                        "state": "KNOWN" if dia_mm and rate_state in FEEDS_S6 else "BLOCKED_UNQUANTIFIED"},
           "SPACING_OR_RATE": {"value": rate_per_m, "unit": "per m",
                               "state": "KNOWN" if rate_per_m and rate_state in FEEDS_S6 else "BLOCKED_UNQUANTIFIED"}}
    if out["SPACING_OR_RATE"]["state"] == "KNOWN" and distribution_m:
        n = math.ceil(rate_per_m * distribution_m - 1e-9)
        out["COUNT"] = {"value": n, "state": "LOWER_BOUND", "distribution_m": distribution_m,
                        "formula": f"ceil({rate_per_m:g}/m x {distribution_m:.3f} m) = {n}"}
    else:
        out["COUNT"] = {"value": None, "state": "BLOCKED_UNQUANTIFIED",
                        "why": "rate or distribution length not established"}
    out["NUMBER_OF_LEGS"] = dict(topology)
    out["HOOKS"] = {"state": hooks_state}
    out["END_ZONES"] = dict(end_zone)
    out["FIRST_LAST_STIRRUP_RULE"] = dict(first_last)
    facets = []
    if width_state not in ("MATCH", "MINOR_DRAFTING_DIFFERENCE"):
        facets.append(f"WIDTH {width_state}")
    if not depth_known:
        facets.append("DEPTH")
    if not cover_known:
        facets.append("COVER")
    if topology.get("state") != "KNOWN":
        facets.append(f"LEGS / TOPOLOGY {topology.get('state')}")
    if hooks_state != "KNOWN":
        facets.append(f"HOOKS {hooks_state}")
    out["SECTION_PATH"] = {"state": "BLOCKED_UNQUANTIFIED" if facets else "KNOWN", "missing": facets}
    out["MASS"] = {"state": "BLOCKED_UNQUANTIFIED" if facets else "RELEASABLE", "missing": facets}
    return out


# ---------------------------------------------------------------------------------------------------- side rebar
def side_rebar_readiness(*, token: dict | None, depth_cm, note_threshold_cm=None,
                         note_authority: str = "UNRESOLVED") -> dict:
    """token {raw, count, dia_mm, spacing_cm, text_handle, column} | None. '/xx cm' is NOT interpreted as vertical or
    longitudinal spacing without a source that says which; faces / vertical arrangement / length / ends are reported
    separately and only a fully source-stated combination may release."""
    if token is None:
        if note_threshold_cm is not None and depth_cm is not None and depth_cm > note_threshold_cm:
            return {"state": "BLOCKED_COMPONENT", "applicability": "NOTE_REQUIRES_SIDE_BARS_BUT_NONE_SCHEDULED",
                    "why": f"depth {depth_cm} cm > {note_threshold_cm} cm (general note, {note_authority}) but the "
                           "schedule row prints no side bars", "faces": "NOT_STATED",
                    "vertical_arrangement": "NOT_STATED", "bar_length": "NOT_STATED", "end_treatment": "NOT_STATED"}
        return {"state": "NOT_APPLICABLE", "applicability": "NONE_PRINTED_AND_NOTE_NOT_TRIGGERED",
                "why": f"no side bars printed; depth {depth_cm} cm"}
    return {"state": "BLOCKED_COMPONENT", "applicability": "PRINTED",
            "token": token, "dia_known": bool(token.get("dia_mm")),
            "count_semantics": "AMBIGUOUS: '{}' may be count per face per level at {} cm vertical spacing, or count "
                               "per {} cm of depth; the faces are not stated".format(token.get("raw"),
                                                                                    token.get("spacing_cm"),
                                                                                    token.get("spacing_cm")),
            "faces": "NOT_STATED", "vertical_arrangement": "NOT_STATED (spacing direction not stated)",
            "bar_length": "NOT_STATED", "end_treatment": "NOT_STATED",
            "why": "side-bar count per beam is not source-quantified"}


# ----------------------------------------------------------------------------------------- candidate invariance
def candidate_invariant(values_by_candidate: dict) -> dict:
    """{candidate: value | None (undefined)} -> INVARIANT (every candidate defines the identical value) / DIFFERENT /
    UNDEFINED (a candidate has no definition) / NONE (no candidate defines it)."""
    if not values_by_candidate:
        return {"state": "UNDEFINED", "value": None}
    if any(v == "UNDEFINED" for v in values_by_candidate.values()):
        return {"state": "UNDEFINED", "value": None}
    vals = set(map(lambda v: repr(v), values_by_candidate.values()))
    if len(vals) > 1:
        return {"state": "DIFFERENT", "value": None}
    v = next(iter(values_by_candidate.values()))
    return {"state": "NONE" if v is None else "INVARIANT", "value": v}


# ------------------------------------------------------------------------------------------------- status mapping
def component_status(*, applicability: str, count_dia_known: bool, run_state: str, additions_blocked: bool,
                     provisional: bool = False) -> str:
    """S5 principle. applicability: OK | SOURCE_CONFLICT | NO_APPLICABLE_DETAIL | NOT_APPLICABLE | BLOCKED.
    run VERIFIED + nothing blocked -> READY; run VERIFIED / LOWER_BOUND + blocked additions (development, hooks,
    extension) -> READY_LOWER_BOUND (the straight portion keeps its state); otherwise BLOCKED_COMPONENT."""
    if applicability in ("SOURCE_CONFLICT", "NO_APPLICABLE_DETAIL", "NOT_APPLICABLE"):
        return applicability
    if applicability != "OK" or not count_dia_known:
        return "BLOCKED_COMPONENT"
    if run_state not in ("VERIFIED", "LOWER_BOUND"):
        return "BLOCKED_COMPONENT"
    if provisional:
        return "PROVISIONAL_ONLY"
    if run_state == "VERIFIED" and not additions_blocked:
        return "READY"
    return "READY_LOWER_BOUND"


def occurrence_status(statuses: list) -> str:
    """Occurrence roll-up: READY when every applicable component is READY; LOWER_BOUND when some longitudinal component
    releases; BLOCKED otherwise."""
    app = [s for s in statuses if s not in ("NOT_APPLICABLE",)]
    if app and all(s == "READY" for s in app):
        return "READY"
    if any(s in RELEASABLE for s in app):
        return "LOWER_BOUND"
    return "BLOCKED"


# ---------------------------------------------------------------------------------------------------- provenance
def provenance_template(*, context: dict, occurrence_id: str, mark: str, subfamily: str, source_handles,
                        schedule_handles, geometry_handles, support_ids, detail_id, rule_id: str, convention_id: str,
                        authority: str, release_state: str, bar_run_id: str | None = None) -> dict:
    """The fields every future S6 beam component must carry. ELEMENT_FAMILY is the generic BEAM family of
    rebar_provenance; the simple / continuous split is ELEMENT_SUBFAMILY."""
    t = {k: context.get(k) for k in ("PROJECT_ID", "DRAWING_ID", "DRAWING_SHA", "ENGINE_COMMIT", "REGISTER_VERSION",
                                     "CALCULATION_ROUND")}
    t.update(ELEMENT_OCCURRENCE_ID=occurrence_id, ELEMENT_MARK=mark, ELEMENT_FAMILY="BEAM",
             ELEMENT_SUBFAMILY=subfamily, SOURCE_HANDLES=list(source_handles), SCHEDULE_HANDLES=list(schedule_handles),
             GEOMETRY_HANDLES=list(geometry_handles), SUPPORT_IDS=list(support_ids), DETAIL_ID=detail_id,
             RULE_ID=rule_id, CONVENTION_ID=convention_id, AUTHORITY_STATE=authority, RELEASE_STATE=release_state)
    if bar_run_id is not None:
        t["BAR_RUN_ID"] = bar_run_id
    return t


def provenance_ready(t: dict) -> bool:
    if any(k.startswith("FOOTING_") for k in t) or t.get("ELEMENT_FAMILY") != "BEAM":
        return False
    if t.get("ELEMENT_SUBFAMILY") == "CONTINUOUS_BEAM" and not t.get("BAR_RUN_ID"):
        return False
    return all(t.get(k) not in (None, "", []) for k in PROVENANCE_FIELDS if k != "SUPPORT_IDS") and \
        isinstance(t.get("SUPPORT_IDS"), list) and t.get("RELEASE_STATE") in STATUSES


def policy_record() -> dict:
    return {"policy_id": POLICY_ID, "statuses": list(STATUSES), "tag_terminals": list(TAG_TERMINALS),
            "geometry_terminals": list(GEOMETRY_TERMINALS), "width_states": list(WIDTH_STATES),
            "rule_authorities": list(RULE_AUTHORITIES), "feeds_s6": list(FEEDS_S6),
            "rules": ["no kg in this round",
                      "a width mismatch is evidence; it never changes geometry or mark",
                      "binding by hard gates on every candidate; distance is a gate, never a tie-break",
                      "every member span and every tag terminates exactly once",
                      "CB schedule spans are never shared out; plan geometry is never capped",
                      "a parametric typical dimension binds only when its defpoints hit a bar end and a face / axis",
                      "a continuous bar crossing a support is ONE bar run",
                      "slab 0.25L / 0.30L rules are never borrowed for beams",
                      "side-bar '/xx cm' is not interpreted without a source naming its direction",
                      "a stirrup count may release while the mass stays blocked",
                      "a straight run keeps its own state; the complete bar is LOWER_BOUND while development is "
                      "blocked"]}
