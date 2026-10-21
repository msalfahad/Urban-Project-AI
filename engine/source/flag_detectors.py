"""GENERIC ENGINEERING-FLAG DETECTORS.

Each detector is a condition over one collection of a project-independent REVIEW VIEW (the shapes below). A project
adapter fills the view from its own census; nothing here knows a project's marks, coordinates or answers. Flags come
out of conditions (two equal authorities disagree, a value sits on an uncovered band limit, a schedule key is defined
twice ...), never out of a list of known issues.

View collections (all optional; every item may carry source_refs[], quantity, unit, floor, label):

  type_evidence          {element_type, element_id, evidence[{value, authority, description, source_ref}],
                          current{value, authority}, definitions{value: {field: v}}}
  section_evidence       {element_type, element_id, member_type, evidence[...] (MEMBER_SECTION)}
  band_lookups           {element_type, element_id, member_type, rule_ref, rule_text, value, value_unit, state,
                          bands[{band_id, description, lo?, hi?}]}
  table_lookups          {element_type, element_ids, rule_ref, rule_text, key, key_unit, table_keys[], state}
  minimum_checks         {element_type, element_id, member_type, rule_ref, rule_text, required, provided, unit_value}
  duplicate_definitions  {element_type, key, schedule_ref, variants[{row, values}], element_ids}
  competing_tags         {element_type, element_id, candidates[], context}
  unresolved_semantics   {element_type, field, member_types[], raw_values{type: raw}, element_ids, meaning_options[]}
  span_matches           {element_type, element_id, member_type, schedule_spans[], plan_spans[], state, extension}
  ambiguous_bindings     {element_type, element_id, tag, candidates[]}
  untyped_members        {element_type, element_id, family}
  single_level_members   {element_type, member_type, level, element_ids, peers_continue(bool)}
  presence_gaps          {element_type, element_id, present_on[], missing_on[]}
  required_not_drawn     {element_type, element_id, rule_ref, rule_text, condition}
  rule_dependent_elements{element_type, element_ids, rule_ref, rule_text, rule_status, gap_kind}
  transverse_rules       {element_type, rule_ref, rule_text, per_metre, bands[{band_id, closed_ties_per_set,
                          element_ids}], zone_length_state, element_ids}
  detail_count_mismatches{element_type, member_type, band_id, schedule_count, detail_count, element_ids}
  basis_dependent_class  {element_type, element_id, rule_ref, class_by_basis{basis: class}}
  geometry_overlaps      {element_type, element_ids, overlap, overlap_unit}
  rule_conflicts         {rule_refs[], subject, values[{rule_ref, value, source_ref}], trade}
  blocked_geometry       {element_type, element_id, reason}
  orphan_definitions     {element_type, schedule_ref, key, values}
"""

from __future__ import annotations

from collections import defaultdict

from . import engineering_flags as EF
from . import structural_authority as SA

POLICY_ID = "FLAG_DETECTORS_V1"


class _Ctx:
    def __init__(self, view):
        self.project_id = view["project_id"]
        self.revision = view["drawing_revision"]
        self.discipline = view.get("discipline", "STRUCTURAL")
        self.flags = []

    def add(self, detector, **kw):
        kw.setdefault("discipline", self.discipline)
        self.flags.append(EF.make_flag(project_id=self.project_id, drawing_revision=self.revision,
                                       detector=detector, **kw))


def _refs(*items):
    out = []
    for it in items:
        for r in (it or {}).get("source_refs", []) or []:
            if r not in out:
                out.append(r)
        for ev in (it or {}).get("evidence", []) or []:
            if ev.get("source_ref") and ev["source_ref"] not in out:
                out.append(ev["source_ref"])
    return out


def _qsum(items):
    qs = [i.get("quantity") for i in items if i.get("quantity") is not None]
    units = {i.get("unit") for i in items if i.get("quantity") is not None}
    return (round(sum(qs), 3), units.pop()) if qs and len(units) == 1 else (None, None)


def _nm(et):
    return str(et).lower().replace("_", " ")


def _where(refs):
    return "; ".join(sorted({", ".join(str(x) for x in (r.get("drawing"), r.get("sheet_title"),
                                                        f"p.{r['page']}" if r.get("page") else None) if x)
                             for r in refs})) or None


# ------------------------------------------------------------------------------------------------ detectors
def type_conflicts(cx, items, orders=None):
    for it in items:
        d = SA.resolve("MEMBER_TYPE", it["evidence"], orders=orders)
        if d["state"] != SA.SOURCE_CONFLICT:
            continue
        vals = []
        for c in d["conflicting"]:
            if c["value"] not in vals:
                vals.append(c["value"])
        defs = it.get("definitions") or {}
        fields = set().union(*[set(defs.get(v, {})) for v in vals]) if defs else set()
        shared = {f for f in fields if all(f in defs.get(v, {}) for v in vals)
                  and len({repr(defs[v][f]) for v in vals}) == 1}
        affected = ["member_type"] + [f for f in ("section", "reinforcement") if f not in shared]
        trades = ["REINFORCEMENT"] + (["CONCRETE", "FORMWORK"] if "section" in affected else [])
        support = [c for c in d["candidates"] if SA.tier_of(c["authority"], d["order"]) is not None
                   and SA.tier_of(c["authority"], d["order"]) > d["tier"]]
        cur = it.get("current") or {}
        by_val = {v: [c for c in d["conflicting"] if c["value"] == v] for v in vals}
        cx.add("type_conflicts", trade=trades, element_type=it["element_type"], element_id=it["element_id"],
               element_ids=it.get("element_ids") or [it["element_id"]], subject="MEMBER_TYPE", floor=it.get("floor"),
               issue_type="SOURCE_CONFLICT", severity="HIGH",
               issue_summary=f"{_nm(it['element_type'])} {it.get('label') or it['element_id']}: equal-authority "
                             f"sources give different types ({' vs '.join(map(str, vals))}).",
               source_refs=_refs(it), source_a={"description": by_val[vals[0]][0]["description"], "value": vals[0],
                                                "source_ref": by_val[vals[0]][0].get("source_ref")},
               source_b={"description": by_val[vals[1]][0]["description"], "value": vals[1],
                         "source_ref": by_val[vals[1]][0].get("source_ref")},
               current_interpretation=(f"type {cur['value']} used provisionally" if cur.get("value") else None),
               interpretation_authority=cur.get("authority"), affected_facts=affected,
               release_effect=EF.BLOCKED, quantity_affected=it.get("quantity"), unit=it.get("unit"),
               question_for_engineer=f"Which type is correct for this {_nm(it['element_type'])} "
                                     f"({it.get('label') or it['element_id']}): {' or '.join(map(str, vals))}?",
               where_to_check=_where(_refs(it)),
               answer_options=[{"answer": f"type {v}", "effect": f"section and bars from the {v} schedule row"
                                + ("; the corroborating evidence agrees" if any(s['value'] == v for s in support)
                                   else "")} for v in vals],
               context={"supporting_evidence": support, "shared_definition_fields": sorted(shared)})


def section_overrides(cx, items, orders=None):
    groups = defaultdict(list)
    for it in items:
        d = SA.resolve("MEMBER_SECTION", it["evidence"], orders=orders, tol=it.get("tol", 0.0))
        if d["state"] == SA.SOURCE_CONFLICT:
            groups[(it["element_type"], it.get("member_type"), "CONFLICT", "")].append((it, d))
        elif d["state"] == SA.RESOLVED_WITH_OVERRIDE and d.get("review"):
            groups[(it["element_type"], it.get("member_type"), "OVERRIDE", "")].append((it, d))
    for (et, mt, v, ov), lst in sorted(groups.items(), key=lambda kv: str(kv[0])):
        pairs = sorted({(repr(d["value"]) if d["value"] is not None else "-",
                         " / ".join(sorted({repr(o["value"]) for o in d["overridden"] + d["conflicting"]})))
                        for _, d in lst})
        it0, d0 = lst[0]
        q, u = _qsum([x for x, _ in lst])
        conflict = v == "CONFLICT"
        a = d0["conflicting"][0] if conflict else [c for c in d0["candidates"] if c["authority"] == d0["authority"]][0]
        b = d0["conflicting"][1] if conflict else d0["overridden"][0]
        cx.add("section_overrides", trade=["CONCRETE", "FORMWORK", "REINFORCEMENT"], element_type=et,
               element_id=f"{et}:{mt}:{v}", element_ids=[x["element_id"] for x, _ in lst],
               subject=f"SECTION:{v}", context={"value_pairs": pairs}, floor=it0.get("floor") if len(lst) == 1 else None,
               issue_type="SOURCE_CONFLICT", severity="HIGH" if conflict else "MEDIUM",
               status=EF.OPEN if conflict else EF.PROVISIONAL,
               issue_summary=f"{len(lst)} {_nm(et)} occurrence(s) of type {mt}: {a['description']} differs from "
                             f"{b['description']} ({'; '.join(f'{x} vs {y}' for x, y in pairs)}).",
               source_refs=_refs(*[x for x, _ in lst])[:12], source_a=a, source_b=b,
               current_interpretation=None if conflict else f"{a['value']} ({a['authority']}) used",
               interpretation_authority=None if conflict else a["authority"], affected_facts=["section"],
               release_effect=EF.BLOCKED if conflict else EF.PROVISIONAL_VALUE, quantity_affected=q, unit=u,
               question_for_engineer=f"For {_nm(et)} type {mt}: does the {a['description']} govern, or the "
                                     f"{b['description']} ({'; '.join(f'{x} vs {y}' for x, y in pairs)})?",
               where_to_check=_where(_refs(it0)),
               answer_options=[{"answer": a["description"], "effect": "current quantity stands"},
                               {"answer": b["description"], "effect": "concrete / formwork / bars follow it; the "
                                                                      "other source needs revision"}])


def band_gaps(cx, items):
    groups = defaultdict(list)
    for it in items:
        if it["state"] in ("BOUNDARY_GAP", "OUT_OF_RANGE", "SOURCE_CONFLICT"):
            groups[(it["element_type"], it["rule_ref"], it["value"], it["state"])].append(it)
    for (et, rule, val, st), lst in sorted(groups.items(), key=lambda kv: str(kv[0])):
        it = lst[0]
        q, u = _qsum(lst)
        bands = it.get("bands") or []
        # offer only the bands whose printed limit is the value (when limits are given); else every band
        near = [bd for bd in bands if val in (bd.get("lo"), bd.get("hi"))]
        options = near or bands
        cx.add("band_gaps", trade="REINFORCEMENT", element_type=et, element_id=f"{rule}:{val}",
               element_ids=[x["element_id"] for x in lst], subject=f"BAND:{rule}:{val}", issue_type="RULE_GAP",
               severity="HIGH",
               issue_summary=f"{it['rule_text']}: value {val} {it.get('value_unit', '')} "
                             f"({', '.join(sorted({str(x.get('member_type')) for x in lst}))}) is "
                             f"{'on a limit no band includes' if st == 'BOUNDARY_GAP' else 'outside every band' if st == 'OUT_OF_RANGE' else 'inside two bands'}.",
               source_refs=_refs(*lst)[:8], source_a={"description": "rule bands",
                                                     "value": [b["description"] for b in bands]},
               source_b={"description": "member value", "value": f"{val} {it.get('value_unit', '')}".strip()},
               current_interpretation=None, affected_facts=["transverse_arrangement"], release_effect=EF.BLOCKED,
               quantity_affected=q, unit=u,
               question_for_engineer=f"{it['rule_text']}: which band applies where the value is exactly "
                                     f"{val} {it.get('value_unit', '')}?".replace("  ", " "),
               where_to_check=_where(_refs(*lst)),
               answer_options=[{"answer": b["description"], "effect": f"use band {b['band_id']}"} for b in options],
               generic_rule_candidate="At an exact band limit that no printed band includes, the consultant's "
                                      "answer may be proposed as a generic boundary convention (review required).")


def table_gaps(cx, items):
    for it in items:
        if it["state"] != "RULE_NOT_EXACT_MATCH":
            continue
        keys = sorted(it["table_keys"])
        lo = max([k for k in keys if k < it["key"]], default=None)
        hi = min([k for k in keys if k > it["key"]], default=None)
        cx.add("table_gaps", trade="REINFORCEMENT", element_type=it["element_type"],
               element_id=f"{it['rule_ref']}:{it['key']}", element_ids=it["element_ids"],
               subject=f"TABLE:{it['rule_ref']}:{it['key']}", issue_type="RULE_GAP", severity="MEDIUM",
               issue_summary=f"{it['rule_text']} has no row for {it['key']} {it.get('key_unit', '')} "
                             f"({len(it['element_ids'])} element(s)); rows are {keys}.",
               source_refs=_refs(it), source_a={"description": "table rows", "value": keys},
               source_b={"description": "required key", "value": it["key"]}, current_interpretation=None,
               affected_facts=[it.get("fact", "table_value")], release_effect=EF.BLOCKED,
               quantity_affected=it.get("quantity"), unit=it.get("unit"),
               question_for_engineer=f"{it['rule_text']}: which value applies for {it['key']} "
                                     f"{it.get('key_unit', '')}?".replace("  ", " "),
               where_to_check=_where(_refs(it)),
               answer_options=[o for o in ([{"answer": f"row {lo}", "effect": "use the lower row"}] if lo else [])
                               + ([{"answer": f"row {hi}", "effect": "use the next higher row"}] if hi else [])
                               + [{"answer": "a stated value", "effect": "use the consultant's value"}]])


def minimum_shortfalls(cx, items):
    groups = defaultdict(list)
    for it in items:
        if it["provided"] is not None and it["required"] is not None and it["provided"] < it["required"]:
            groups[(it["element_type"], it["rule_ref"], it.get("floor"), it["required"], it["provided"])].append(it)
    for (et, rule, fl, req, prov), lst in sorted(groups.items(), key=lambda kv: str(kv[0])):
        q, u = _qsum(lst)
        cx.add("minimum_shortfalls", trade=["CONCRETE", "FORMWORK", "REINFORCEMENT"], element_type=et,
               element_id=f"{rule}:{fl}:{prov}", element_ids=[x["element_id"] for x in lst], floor=fl,
               subject=f"MIN:{rule}:{fl}:{prov}", issue_type="SOURCE_CONFLICT", severity="MEDIUM",
               status=EF.PROVISIONAL,
               issue_summary=f"{len(lst)} {_nm(et)} occurrence(s) ({', '.join(sorted({str(x.get('member_type')) for x in lst}))}) "
                             f"at {fl}: schedule gives {prov} {lst[0].get('unit_value', '')} but "
                             f"{lst[0]['rule_text']} requires at least {req}.",
               source_refs=_refs(*lst)[:8], source_a={"description": lst[0]["rule_text"], "value": req},
               source_b={"description": "schedule value", "value": prov},
               current_interpretation="schedule value kept (member-specific design)",
               interpretation_authority=SA.MEMBER_SCHEDULE, affected_facts=["section"],
               release_effect=EF.PROVISIONAL_VALUE, quantity_affected=q, unit=u,
               question_for_engineer=f"The schedule gives {prov} where the general rule asks for at least {req}. "
                                     f"Is the schedule correct, or must the section increase?",
               where_to_check=_where(_refs(*lst)),
               answer_options=[{"answer": "schedule is correct", "effect": "no quantity change"},
                               {"answer": f"increase to {req}", "effect": "concrete, formwork and ties increase"}])


def duplicate_definitions(cx, items):
    for it in items:
        cx.add("duplicate_definitions", trade=["CONCRETE", "FORMWORK", "REINFORCEMENT"],
               element_type=it["element_type"], element_id=f"{it['schedule_ref']}:{it['key']}",
               element_ids=it.get("element_ids") or [it["key"]], subject=f"DUPKEY:{it['key']}",
               issue_type="SOURCE_CONFLICT", severity="HIGH",
               issue_summary=f"Schedule key {it['key']} is defined {len(it['variants'])} times with different "
                             f"values.",
               source_refs=_refs(it), source_a={"description": f"row {it['variants'][0]['row']}",
                                                "value": it["variants"][0]["values"]},
               source_b={"description": f"row {it['variants'][1]['row']}", "value": it["variants"][1]["values"]},
               current_interpretation=it.get("geometry_hint"), affected_facts=["section", "reinforcement"],
               release_effect=EF.BLOCKED, quantity_affected=it.get("quantity"), unit=it.get("unit"),
               question_for_engineer=f"Schedule key {it['key']} appears twice. Which row is valid?",
               where_to_check=_where(_refs(it)),
               answer_options=[{"answer": f"row {v['row']}", "effect": f"use {v['values']}"} for v in it["variants"]])


def competing_tags(cx, items):
    for it in items:
        cx.add("competing_tags", trade=["CONCRETE", "FORMWORK", "REINFORCEMENT"], element_type=it["element_type"],
               element_id=it["element_id"], subject="COMPETING_TAGS", floor=it.get("floor"),
               issue_type="SOURCE_CONFLICT", severity="HIGH",
               issue_summary=f"One drawn {_nm(it['element_type'])} carries {len(it['candidates'])} different "
                             f"type marks ({', '.join(it['candidates'])}){'; ' + it['context'] if it.get('context') else ''}.",
               source_refs=_refs(it), source_a={"description": "mark 1", "value": it["candidates"][0]},
               source_b={"description": "mark 2", "value": it["candidates"][1]}, current_interpretation=None,
               affected_facts=["member_type", "section", "reinforcement"], release_effect=EF.BLOCKED,
               quantity_affected=it.get("quantity"), unit=it.get("unit"),
               question_for_engineer=f"This {_nm(it['element_type'])} is marked {' and '.join(it['candidates'])}. "
                                     f"Which type is it - or is it two members drawn as one?",
               where_to_check=_where(_refs(it)),
               answer_options=[{"answer": c, "effect": f"size and bars from {c}"} for c in it["candidates"]]
               + [{"answer": "two separate members", "effect": "split the outline; both rows apply"}])


def unresolved_semantics(cx, items):
    for it in items:
        cx.add("unresolved_semantics", trade="REINFORCEMENT", element_type=it["element_type"],
               element_id=f"{it['element_type']}:{it['field']}", element_ids=it["element_ids"],
               subject=f"SEMANTICS:{it['field']}", issue_type="AMBIGUOUS_APPLICABILITY", severity="MEDIUM",
               issue_summary=f"The schedule field '{it['field']}' is printed for {len(it['member_types'])} type(s) "
                             f"(e.g. {', '.join(f'{k}={v}' for k, v in list(it['raw_values'].items())[:4])}) but its "
                             f"meaning is not stated.",
               source_refs=_refs(it), source_a={"description": f"field {it['field']}", "value": it["raw_values"]},
               current_interpretation="component held back; other bars of the same members stay releasable",
               affected_facts=[it["field"]], release_effect=EF.BLOCKED, quantity_affected=it.get("quantity"),
               unit=it.get("unit"),
               question_for_engineer=f"What does the schedule field '{it['field']}' mean (bar count, bar size, "
                                     f"shape and position)?", where_to_check=_where(_refs(it)),
               answer_options=it.get("meaning_options") or [])


def span_mismatches(cx, items):
    for it in items:
        if it["state"] == "MATCH_CONFIRMED":
            continue
        cx.add("span_mismatches", trade="REINFORCEMENT", element_type=it["element_type"],
               element_id=it["element_id"], subject="SPANS", floor=it.get("floor"),
               issue_type="SOURCE_CONFLICT" if it["state"] in ("SPAN_LENGTH_CONFLICT", "SPAN_COUNT_CONFLICT")
               else "UNBOUND_OCCURRENCE", severity="MEDIUM",
               issue_summary=f"{_nm(it['element_type'])} {it['member_type']}: schedule spans {it['schedule_spans']} "
                             f"but plan spans {it['plan_spans']} ({it['state']}).",
               source_refs=_refs(it), source_a={"description": "schedule spans", "value": it["schedule_spans"]},
               source_b={"description": "plan spans", "value": it["plan_spans"]},
               current_interpretation=(f"would match if extended: {it['extension']}" if it.get("extension") else None),
               affected_facts=["span_assignment"], release_effect=EF.BLOCKED, quantity_affected=it.get("quantity"),
               unit=it.get("unit"),
               question_for_engineer=f"Which plan members form {it['member_type']} (schedule spans "
                                     f"{it['schedule_spans']})?", where_to_check=_where(_refs(it)),
               answer_options=[{"answer": "the tagged plan spans", "effect": "schedule bars assigned to the drawn "
                                                                             "spans; schedule spans need correction"},
                               {"answer": "include the adjacent span(s)", "effect": "the member is longer than "
                                                                                    "tagged"}]
               + ([{"answer": "extension as computed", "effect": str(it["extension"])}] if it.get("extension") else []))


def ambiguous_bindings(cx, items):
    for it in items:
        cx.add("ambiguous_bindings", trade=["CONCRETE", "FORMWORK", "REINFORCEMENT"],
               element_type=it["element_type"], element_id=it["element_id"], subject="BINDING",
               floor=it.get("floor"), issue_type="UNBOUND_OCCURRENCE", severity="MEDIUM",
               issue_summary=f"Mark {it['tag']} sits between {len(it['candidates'])} members at similar distance; "
                             f"the member it names is not certain.",
               source_refs=_refs(it), source_a={"description": "mark", "value": it["tag"]},
               source_b={"description": "candidate members", "value": it["candidates"]},
               current_interpretation="counted as a mark occurrence; member not assigned",
               affected_facts=["member_assignment", "member_type"], release_effect=EF.AUDIT_ONLY,
               quantity_affected=it.get("quantity"), unit=it.get("unit"),
               question_for_engineer=f"Which member does mark {it['tag']} refer to?",
               where_to_check=_where(_refs(it)),
               answer_options=[{"answer": c, "effect": f"{it['tag']} assigned to {c}"} for c in it["candidates"]])


def untyped_members(cx, items):
    groups = defaultdict(list)
    for it in items:
        groups[(it["element_type"], it.get("floor"), it.get("family"))].append(it)
    for (et, fl, fam), lst in sorted(groups.items(), key=lambda kv: str(kv[0])):
        q, u = _qsum(lst)
        cx.add("untyped_members", trade=["CONCRETE", "FORMWORK", "REINFORCEMENT"], element_type=et,
               element_id=f"{et}:{fl}:{fam}", element_ids=[x["element_id"] for x in lst], floor=fl,
               subject=f"UNTYPED:{fam}", issue_type="MISSING_SCHEDULE", severity="MEDIUM",
               issue_summary=f"{len(lst)} {_nm(et)} member(s) at {fl} are drawn without a type mark"
                             f"{' (' + fam + ')' if fam else ''}.",
               source_refs=_refs(*lst)[:10], current_interpretation="geometry counted; size and bars unknown",
               affected_facts=["member_type", "section", "reinforcement"], release_effect=EF.AUDIT_ONLY,
               quantity_affected=q, unit=u,
               question_for_engineer=f"These {_nm(et)} members at {fl} carry no mark. Which type is each "
                                     f"(or are they not structural members)?", where_to_check=_where(_refs(*lst)),
               answer_options=[{"answer": "a schedule type", "effect": "size and bars from that row"},
                               {"answer": "not a structural member", "effect": "removed from the count"}])


def single_level_members(cx, items):
    for it in items:
        if not it.get("peers_continue", True):
            continue
        cx.add("single_level_members", trade=["CONCRETE", "FORMWORK", "REINFORCEMENT"],
               element_type=it["element_type"], element_id=f"{it['member_type']}:{it['level']}",
               element_ids=it["element_ids"], floor=it["level"], subject="SINGLE_LEVEL",
               issue_type="AMBIGUOUS_APPLICABILITY", severity="LOW", status=EF.PROVISIONAL,
               issue_summary=f"Type {it['member_type']} occurs only at {it['level']} ({len(it['element_ids'])} "
                             f"occurrence(s)) while other {_nm(it['element_type'])}s continue upward.",
               source_refs=_refs(it), current_interpretation=f"counted as {_nm(it['element_type'])} occurrences "
                                                             f"at {it['level']} only",
               interpretation_authority=SA.PLAN_MEMBER_TAG, affected_facts=["boq_item"],
               release_effect=EF.PROVISIONAL_VALUE, quantity_affected=it.get("quantity"), unit=it.get("unit"),
               question_for_engineer=f"Is {it['member_type']} a {_nm(it['element_type'])} that stops at "
                                     f"{it['level']}, or a short stub / pedestal that belongs to the foundation "
                                     f"item?", where_to_check=_where(_refs(it)),
               answer_options=[{"answer": f"{_nm(it['element_type'])} stopping at {it['level']}",
                                "effect": "stays in the column count"},
                               {"answer": "foundation stub / pedestal", "effect": "moves to the foundation item"}])


def presence_gaps(cx, items):
    for it in items:
        cx.add("presence_gaps", trade=["CONCRETE"], element_type=it["element_type"], element_id=it["element_id"],
               subject="PRESENCE", floor=it.get("floor"), issue_type="SOURCE_CONFLICT", severity="LOW",
               status=EF.PROVISIONAL,
               issue_summary=f"{_nm(it['element_type'])} {it.get('label') or it['element_id']} is drawn on "
                             f"{', '.join(it['present_on'])} but not on {', '.join(it['missing_on'])}.",
               source_refs=_refs(it), source_a={"description": "drawn on", "value": it["present_on"]},
               source_b={"description": "missing on", "value": it["missing_on"]},
               current_interpretation="counted (present on the other plans)", interpretation_authority=SA.DRAWN_GEOMETRY,
               affected_facts=["occurrence"], release_effect=EF.PROVISIONAL_VALUE,
               quantity_affected=it.get("quantity"), unit=it.get("unit"),
               question_for_engineer=f"Does this {_nm(it['element_type'])} exist (it is missing on "
                                     f"{', '.join(it['missing_on'])})?", where_to_check=_where(_refs(it)),
               answer_options=[{"answer": "exists", "effect": "keep"}, {"answer": "does not exist",
                                                                        "effect": "remove from the count"}])


def required_not_drawn(cx, items):
    for it in items:
        cx.add("required_not_drawn", trade=["CONCRETE", "FORMWORK", "REINFORCEMENT"],
               element_type=it["element_type"], element_id=it["element_id"], subject="REQUIRED",
               floor=it.get("floor"), issue_type="MISSING_DETAIL", severity="MEDIUM",
               issue_summary=f"{it['rule_text']} requires {_nm(it['element_type'])} ({it['condition']}) but none "
                             f"is drawn.", source_refs=_refs(it),
               source_a={"description": it["rule_ref"], "value": it["rule_text"]},
               current_interpretation="required population recorded; no geometry", affected_facts=["occurrence"],
               release_effect=EF.BLOCKED, quantity_affected=it.get("quantity"), unit=it.get("unit"),
               question_for_engineer=f"{it['rule_text']}: where are these {_nm(it['element_type'])}s, and what "
                                     f"size and bars?", where_to_check=_where(_refs(it)),
               answer_options=[{"answer": "positions + size given", "effect": "occurrences created"},
                               {"answer": "not required here", "effect": "population closed as not applicable"}])


_GAP_KIND = {"METHOD": "ENGINEERING_METHOD_REQUIRED", "APPLICABILITY": "AMBIGUOUS_APPLICABILITY",
             "DIMENSION": "MISSING_DIMENSION", "EXTENT": "MISSING_DIMENSION", "DETAIL": "MISSING_DETAIL"}


def rule_dependent_elements(cx, items):
    for it in items:
        if it["rule_status"] not in ("BLOCKED_METHOD", "CANDIDATE", "SOURCE_CONFLICT"):
            continue
        kind = it.get("gap_kind", "METHOD")
        cx.add("rule_dependent_elements", trade=it.get("trade", ["CONCRETE", "FORMWORK", "REINFORCEMENT"]),
               element_type=it["element_type"], element_id=f"{it['rule_ref']}:{it['element_type']}",
               element_ids=it["element_ids"], subject=f"RULEDEP:{it['rule_ref']}:{kind}", floor=it.get("floor"),
               issue_type=_GAP_KIND[kind], severity="MEDIUM",
               issue_summary=f"{len(it['element_ids'])} {_nm(it['element_type'])} occurrence(s) depend on "
                             f"{it['rule_ref']} ({it['rule_text']}), whose {kind.lower()} is not established "
                             f"({it['rule_status']}).",
               source_refs=_refs(it), source_a={"description": it["rule_ref"], "value": it["rule_text"]},
               current_interpretation="occurrences counted; quantities depending on the rule held back",
               affected_facts=it.get("affected_facts", ["detailing"]),
               release_effect=it.get("release_effect", EF.BLOCKED), quantity_affected=it.get("quantity"),
               unit=it.get("unit"),
               question_for_engineer=it.get("question") or f"How does {it['rule_ref']} apply to these "
                                                           f"{_nm(it['element_type'])}s?",
               where_to_check=_where(_refs(it)), answer_options=it.get("options") or [])


def transverse_rules(cx, items):
    for it in items:
        multi = [b for b in it["bands"] if (b.get("closed_ties_per_set") or 1) > 1 and b.get("element_ids")]
        if it.get("per_metre") and multi:
            ids = sorted({e for b in multi for e in b["element_ids"]})
            cx.add("transverse_rules", trade="REINFORCEMENT", element_type=it["element_type"],
                   element_id=f"{it['rule_ref']}:per_metre", element_ids=ids, subject="PER_METRE_SET",
                   issue_type="AMBIGUOUS_APPLICABILITY", severity="HIGH",
                   issue_summary=f"{it['rule_text']} gives a count per metre, but {len(multi)} band(s) use more than "
                                 f"one closed tie per level; whether the count is of tie SETS or of single ties is "
                                 f"not stated.", source_refs=_refs(it),
                   source_a={"description": "rule", "value": it["rule_text"]},
                   source_b={"description": "ties per level in the multi-tie bands",
                             "value": {b["band_id"]: b["closed_ties_per_set"] for b in multi}},
                   current_interpretation=None, affected_facts=["transverse_count"], release_effect=EF.BLOCKED,
                   quantity_affected=len(ids), unit="nr occurrences",
                   question_for_engineer=f"{it['rule_text']}: is the per-metre count the number of tie sets (all "
                                         f"closed ties at one level) or the number of single ties?",
                   where_to_check=_where(_refs(it)),
                   answer_options=[{"answer": "tie sets per metre", "effect": "each level has all ties of the band"},
                                   {"answer": "single ties per metre", "effect": "the count is shared between the "
                                                                                 "ties of a level"}],
                   generic_rule_candidate="Per-metre transverse counts on multi-tie arrangements: the consultant's "
                                          "reading may become a generic convention after review.")
        if it.get("per_metre") and it.get("zone_length_state") not in (None, "ESTABLISHED"):
            cx.add("transverse_rules", trade="REINFORCEMENT", element_type=it["element_type"],
                   element_id=f"{it['rule_ref']}:zone", element_ids=it["element_ids"], subject="TIE_ZONE",
                   issue_type="ENGINEERING_METHOD_REQUIRED", severity="HIGH",
                   issue_summary=f"{it['rule_text']} gives ties per metre but not over which height: full storey "
                                 f"height, clear height below the beams, or including the joint.",
                   source_refs=_refs(it), source_a={"description": "rule", "value": it["rule_text"]},
                   current_interpretation=None, affected_facts=["transverse_zone"], release_effect=EF.BLOCKED,
                   quantity_affected=len(it["element_ids"]), unit="nr occurrences",
                   question_for_engineer="Over which vertical length are the column ties counted: floor-to-floor, "
                                         "clear height between slab and beam soffit, or clear height plus the "
                                         "beam-column joint?", where_to_check=_where(_refs(it)),
                   answer_options=[{"answer": "floor-to-floor", "effect": "largest tie count"},
                                   {"answer": "clear height", "effect": "fewer ties; needs beam depths per face"},
                                   {"answer": "clear height + joint", "effect": "between the two"}])


def detail_count_mismatches(cx, items):
    groups = defaultdict(list)
    for it in items:
        groups[(it["element_type"], it["band_id"], it["schedule_count"], it["detail_count"])].append(it)
    merged = []
    for (et, band, sc, dc), lst in sorted(groups.items(), key=lambda kv: str(kv[0])):
        merged.append(dict(lst[0], member_type=", ".join(sorted(str(x["member_type"]) for x in lst)),
                           element_ids=[e for x in lst for e in x["element_ids"]],
                           source_refs=_refs(*lst)))
    for it in merged:
        cx.add("detail_count_mismatches", trade="REINFORCEMENT", element_type=it["element_type"],
               element_id=f"{it['band_id']}:{it['schedule_count']}:{it['detail_count']}",
               element_ids=it["element_ids"], subject="DETAIL_COUNT", issue_type="AMBIGUOUS_APPLICABILITY", severity="LOW",
               issue_summary=f"Type {it['member_type']} has {it['schedule_count']} main bars but the detail sketch "
                             f"for its band shows {it['detail_count']}; which bars each tie encloses is not shown.",
               source_refs=_refs(it), source_a={"description": "schedule bars", "value": it["schedule_count"]},
               source_b={"description": "bars in band sketch", "value": it["detail_count"]},
               current_interpretation=None, affected_facts=["tie_size"], release_effect=EF.BLOCKED,
               quantity_affected=len(it["element_ids"]), unit="nr occurrences",
               question_for_engineer=f"For {it['member_type']} ({it['schedule_count']} bars): which bars does each "
                                     f"overlapping tie enclose?", where_to_check=_where(_refs(it)),
               answer_options=[{"answer": "scale the sketch", "effect": "tie sizes from the sketch fractions"},
                               {"answer": "specific bar grouping", "effect": "tie sizes from the stated grouping"}])


def basis_dependent_class(cx, items):
    groups = defaultdict(list)
    for it in items:
        if len(set(it["class_by_basis"].values())) >= 2:
            groups[(it["element_type"], it["rule_ref"])].append(it)
    for (et, rule), lst in sorted(groups.items(), key=lambda kv: str(kv[0])):
        q, u = _qsum(lst)
        bases = list(lst[0]["class_by_basis"])
        cx.add("basis_dependent_class", trade=["CONCRETE", "FORMWORK", "REINFORCEMENT"], element_type=et,
               element_id=f"{rule}:basis", element_ids=[x["element_id"] for x in lst], subject="BASIS",
               issue_type="AMBIGUOUS_APPLICABILITY", severity="MEDIUM",
               issue_summary=f"{rule}: {len(lst)} {_nm(et)}(s) change class depending on the length basis "
                             f"({' / '.join(bases)}).", source_refs=_refs(*lst)[:6], current_interpretation=None,
               affected_facts=["section", "reinforcement"], release_effect=EF.BLOCKED, quantity_affected=q, unit=u,
               question_for_engineer=f"{rule}: is the length measured {' or '.join(bases)}?",
               where_to_check=_where(_refs(*lst)),
               answer_options=[{"answer": b, "effect": "classes: " + ", ".join(f"{x['element_id']}={x['class_by_basis'][b]}"
                                                                              for x in lst)} for b in bases],
               context={"class_by_basis": {x["element_id"]: x["class_by_basis"] for x in lst}},
               generic_rule_candidate="Length basis for length-banded typical details (c/c vs clear).")


def geometry_overlaps(cx, items):
    for it in items:
        cx.add("geometry_overlaps", trade="CONCRETE", element_type=it["element_type"],
               element_id="+".join(it["element_ids"]), element_ids=it["element_ids"], subject="OVERLAP",
               issue_type="SOURCE_CONFLICT", severity="LOW", status=EF.PROVISIONAL,
               issue_summary=f"Two {_nm(it['element_type'])} outlines overlap by {it['overlap']} "
                             f"{it['overlap_unit']}.", source_refs=_refs(it),
               current_interpretation="both counted; overlap volume must not be counted twice",
               affected_facts=["overlap"], release_effect=EF.PROVISIONAL_VALUE, quantity_affected=it["overlap"],
               unit=it["overlap_unit"], question_for_engineer="Are these two separate members or one combined member?",
               where_to_check=_where(_refs(it)),
               answer_options=[{"answer": "separate", "effect": "deduct the overlap once"},
                               {"answer": "combined", "effect": "one member; redefine its size"}])


def rule_conflicts(cx, items):
    for it in items:
        a, b = it["values"][0], it["values"][1]
        cx.add("rule_conflicts", trade=it.get("trade", "OTHER"), element_type="PROJECT_RULE",
               element_id="+".join(it["rule_refs"]), subject=it["subject"], issue_type="SOURCE_CONFLICT",
               severity="LOW", issue_summary=f"{it['subject']}: {a['rule_ref']} says {a['value']}, "
                                             f"{b['rule_ref']} says {b['value']}.",
               source_refs=_refs(it), source_a=a, source_b=b, current_interpretation=None,
               affected_facts=it.get("affected_facts", [it["subject"]]),
               release_effect=it.get("release_effect", EF.NO_QUANTITY_IMPACT), quantity_affected=it.get("quantity"),
               unit=it.get("unit"),
               question_for_engineer=f"{it['subject']}: which value governs, {a['value']} or {b['value']}?",
               where_to_check=_where(_refs(it)),
               answer_options=[{"answer": str(a["value"]), "effect": a["rule_ref"]},
                               {"answer": str(b["value"]), "effect": b["rule_ref"]}])


def blocked_geometry(cx, items):
    groups = defaultdict(list)
    for it in items:
        groups[(it["element_type"], it["reason"])].append(it)
    merged = []
    for (et, reason), lst in sorted(groups.items(), key=lambda kv: str(kv[0])):
        q, u = _qsum(lst)
        merged.append(dict(lst[0], element_id=lst[0]["element_id"] if len(lst) == 1 else f"{et}:{len(lst)}",
                           element_ids=[x["element_id"] for x in lst], quantity=q, unit=u, source_refs=_refs(*lst)))
    for it in merged:
        cx.add("blocked_geometry", trade=["CONCRETE", "FORMWORK", "REINFORCEMENT"], element_type=it["element_type"],
               element_id=it["element_id"], element_ids=it.get("element_ids"), subject="GEOMETRY", floor=it.get("floor"),
               issue_type="MISSING_DIMENSION", severity="LOW",
               issue_summary=(f"{_nm(it['element_type'])} {it['element_id']}: {it['reason']}." if len(it["element_ids"]) == 1
                              else f"{len(it['element_ids'])} {_nm(it['element_type'])}s: {it['reason']}."),
               source_refs=_refs(it), current_interpretation="occurrence counted; measurement held back",
               affected_facts=["geometry"], release_effect=EF.BLOCKED, quantity_affected=it.get("quantity"),
               unit=it.get("unit"), question_for_engineer=it.get("question") or "Please give the missing dimension.",
               where_to_check=_where(_refs(it)), answer_options=it.get("options") or [])


def orphan_definitions(cx, items):
    for it in items:
        cx.add("orphan_definitions", trade=["CONCRETE", "FORMWORK", "REINFORCEMENT"], element_type=it["element_type"],
               element_id=f"{it['schedule_ref']}:{it['key']}", element_ids=[it["key"]], subject="ORPHAN_DEFINITION",
               issue_type="AMBIGUOUS_APPLICABILITY", severity="LOW", status=EF.PROVISIONAL,
               issue_summary=f"Schedule row {it['key']} ({_nm(it['element_type'])}) is defined but no plan "
                             f"occurrence carries this mark.", source_refs=_refs(it),
               source_a={"description": "schedule row", "value": it.get("values")},
               current_interpretation="zero occurrences (a schedule row never creates an occurrence)",
               interpretation_authority=SA.PLAN_MEMBER_TAG, affected_facts=["occurrence"],
               release_effect=EF.NO_QUANTITY_IMPACT,
               question_for_engineer=f"Schedule row {it['key']} has no occurrence on the plans. Is it unused, or "
                                     f"is a mark missing on a plan?", where_to_check=_where(_refs(it)),
               answer_options=[{"answer": "unused", "effect": "no change"},
                               {"answer": "used at a location", "effect": "occurrence(s) added there"}])


DETECTORS = {"type_evidence": type_conflicts, "section_evidence": section_overrides, "band_lookups": band_gaps,
             "table_lookups": table_gaps, "minimum_checks": minimum_shortfalls,
             "duplicate_definitions": duplicate_definitions, "competing_tags": competing_tags,
             "unresolved_semantics": unresolved_semantics, "span_matches": span_mismatches,
             "ambiguous_bindings": ambiguous_bindings, "untyped_members": untyped_members,
             "single_level_members": single_level_members, "presence_gaps": presence_gaps,
             "required_not_drawn": required_not_drawn, "rule_dependent_elements": rule_dependent_elements,
             "transverse_rules": transverse_rules, "detail_count_mismatches": detail_count_mismatches,
             "basis_dependent_class": basis_dependent_class, "geometry_overlaps": geometry_overlaps,
             "rule_conflicts": rule_conflicts, "blocked_geometry": blocked_geometry,
             "orphan_definitions": orphan_definitions}


def detect(view, *, orders=None):
    """Run every detector whose collection is present. Returns numbered flags (deterministic)."""
    cx = _Ctx(view)
    for key, fn in DETECTORS.items():
        items = view.get(key)
        if not items:
            continue
        if key in ("type_evidence", "section_evidence"):
            fn(cx, items, orders=orders)
        else:
            fn(cx, items)
    keys = [f["flag_key"] for f in cx.flags]
    dup = {k for k in keys if keys.count(k) > 1}
    if dup:
        raise ValueError(f"duplicate flag keys (detector subjects must be unique): {sorted(dup)[:5]}")
    return EF.number(cx.flags)
