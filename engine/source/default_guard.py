"""DEFAULT GUARD - no convention value where the project documents print one; no partial footprint; no silent
omission, double count, finished-as-structural value, client change as approved design, or over-sized deduction
(generic, every villa).

Why (owner 2026-10-22, pool lesson, ENGINEERING_REASONING_STANDARD.md section 7 "DEFAULT GUARD"): "Before applying any
default, search and reconcile all relevant project drawings, sections, schedules and details. An owner-approved fallback
is only used when the project documents genuinely do not establish the value." The development case: an engine pool line
used the conventions floor 0.25 m / walls 1.60 m while the structural detail printed 0.40 m and the architecture gave the
levels, and it measured only the straight strip of a curved wall ring. Later findings of the same family are guarded too:
a FINISHED water depth taken as the RC wall height (no build-up), a beam running through a column face deducting the full
face width instead of its own width, a staircase or an upper-floor flight missing, a landing or a pool base / wall
junction counted twice, a client-requested change shown as the approved design.

This module is a NEW piece. It is not wired into any released or candidate method and edits no frozen file. It reads
BOQ lines that declare their basis (below) and returns guarded copies: a line that fails a check becomes HELD with every
finding and its citation; its value is kept as information (`info_qty`) and never summed, never set to 0. Nothing here
names a project, a sheet, a layer or a value of one project.

Checks (finding codes; each makes the line HELD unless noted)
  DG-1 CONVENTION_WHERE_PRINTED  a value taken from a convention set while a printed record for the same element (or
                                  element kind) and parameter exists; the printed value(s) are cited. Printed records
                                  that disagree with each other: PRINTED_VALUES_DISAGREE (a conflict, never settled here).
  DG-2 SEARCH_NOT_RECORDED /     a line resting on a convention must list the documents searched; every register
       SEARCH_INCOMPLETE          document of a searchable role (plan, section, structural detail, schedule) must be in
                                  that list, else the convention is not shown to be a genuine fallback.
       FALLBACK_NOT_APPROVED      a convention that survives the search is used only with `approval` (the answered owner
                                  decision or rule-library id, WORKFLOW_CONTROLS s.4); the line is then labelled
                                  ASSUMED - OWNER-APPROVED with that source. No approval: HELD.
  DG-3 PARTIAL_FOOTPRINT /       the plan footprint (area or length) a line measured differs from the drawn footprint of
       FOOTPRINT_EXCEEDS_DRAWN    that element part by more than FOOTPRINT_TOL (e.g. the straight strip of a curved ring).
  DG-4 FINISHED_AS_STRUCTURAL    a structural-trade value (concrete, reinforcement, formwork) taken from a printed record
                                  whose basis is a FINISHED level / depth (no build-up). A value DERIVED from printed
                                  records (finished depth + printed build-up) is accepted when every reference exists and
                                  none is itself FINISHED-only without a build-up partner. Unknown reference: UNSUPPORTED_REF.
  DG-5 SILENT_OMISSION           an element (or element part, e.g. one flight of a stair on an upper storey) of the drawn
                                  inventory that no line carries, measured or HELD. A HELD placeholder line is added.
  DG-6 DOUBLE_COUNT              one physical zone (a landing, the base under a pool wall) declared in `covers` by two
                                  live lines of the same trade and unit. Both lines become HELD, each naming the other.
  DG-7 CLIENT_CHANGE_AS_APPROVED a line of client-requested origin placed in the approved-design baseline (S0);
       REVISION_NOT_ISSUED        a line tagged as consultant revision (S2) with no issued revision record for its
                                  element is moved to the client-request scenario S1 and HELD. Scenario lines (S1) are
                                  returned in their own set, never in the baseline and never deleted.
  DG-8 DEDUCTION_EXCEEDS_MEMBER  a deduction attributed to a framing member wider than that member's own width on the
                                  face (or than the face itself): the covered face is the member's own width (T-163).

Input (plain dicts; lengths in metres)
  documents [{"doc", "role"}]     role: PLAN | SECTION | STRUCTURAL_DETAIL | SCHEDULE | ELEVATION | NOTE | OTHER
  printed   [{"id", "element_kind", "element_id" (None = every element of the kind), "param", "value", "unit",
              "doc", "note", "basis": STRUCTURAL | FINISHED | BUILD_UP | SETTING_OUT,
              "applies_to": [element ids] (optional: a kind-wide record printed for some elements only)}]
  lines     [{"id", "element_id", "element_kind", "part" (default WHOLE), "trade", "unit", "qty",
              "state": RELEASED | PROVISIONAL | HELD | UNKNOWN | SUPERSEDED | EXCLUDED,
              "values": {param: {"value", "source": CONVENTION | PRINTED | DERIVED | DRAWN, "ref": id or [ids]}},
              "searched": [doc], "footprint": {"value", "unit"}, "covers": [zone id],
              "scenario": S0 | S1 | S2 (default S0), "origin": DESIGN | CLIENT_REQUEST | CONSULTANT_REVISION,
              "deductions": [{"member", "width_m", "face_width_m"}]}]
  inventory [{"id", "kind", "parts": {part: {"value", "unit"} or None}}]   the drawn elements (approved design)
  members   [{"id", "width_m"}]
  revisions [{"element_id", "doc"}]   issued consultant revisions

Rules
  OWNER 2026-10-22 DEFAULT GUARD  (ENGINEERING_REASONING_STANDARD.md s.7; WORKFLOW_CONTROLS s.4: a fallback only when
                                  approved and the documents do not establish the value)
  UP-QTY-STATUS-001               missing data never becomes 0; every element reported measured / held / unsupported
  UP-STAIR-002                    drawing first
  Owner Q-29 / s.7 2026-10-22     approved design S0, client request S1, consultant revision S2 kept apart

Stdlib only.
"""

from __future__ import annotations

import copy

FOOTPRINT_TOL = 0.005          # relative; a measured footprint within 0.5 % of the drawn one is the same footprint
DEDUCTION_TOL_M = 0.005        # 5 mm drawing tolerance on a member width
SEARCH_ROLES = ("PLAN", "SECTION", "STRUCTURAL_DETAIL", "SCHEDULE")
STRUCTURAL_TRADES = ("CONCRETE", "REINFORCEMENT", "FORMWORK")
LIVE_STATES = ("RELEASED", "PROVISIONAL")
NOT_SUMMED = ("HELD", "UNKNOWN", "SUPERSEDED", "EXCLUDED")
SCENARIOS = ("S0", "S1", "S2")

CODES = {
    "DG-1": ("CONVENTION_WHERE_PRINTED", "PRINTED_VALUES_DISAGREE"),
    "DG-2": ("SEARCH_NOT_RECORDED", "SEARCH_INCOMPLETE", "FALLBACK_NOT_APPROVED"),
    "DG-3": ("PARTIAL_FOOTPRINT", "FOOTPRINT_EXCEEDS_DRAWN"),
    "DG-4": ("FINISHED_AS_STRUCTURAL", "UNSUPPORTED_REF"),
    "DG-5": ("SILENT_OMISSION",),
    "DG-6": ("DOUBLE_COUNT",),
    "DG-7": ("CLIENT_CHANGE_AS_APPROVED", "REVISION_NOT_ISSUED"),
    "DG-8": ("DEDUCTION_EXCEEDS_MEMBER",),
}


class GuardError(ValueError):
    pass


def _finding(check, code, line_id, element_id, detail, citation=None):
    return {"check": check, "code": code, "line_id": line_id, "element_id": element_id, "detail": detail,
            "citation": citation or []}


def _cite(p):
    return {"printed_id": p["id"], "value": p["value"], "unit": p.get("unit", "m"), "doc": p.get("doc"),
            "note": p.get("note", ""), "basis": p.get("basis", "STRUCTURAL")}


def _printed_for(printed, line, param):
    out = []
    for p in printed:
        if p["param"] != param:
            continue
        if p.get("element_id") not in (None, line.get("element_id")):
            continue
        if p.get("element_kind") not in (None, line.get("element_kind")):
            continue
        if p.get("applies_to") and line.get("element_id") not in p["applies_to"]:
            continue
        out.append(p)
    return out


def _refs(v):
    r = v.get("ref")
    if r is None:
        return []
    return list(r) if isinstance(r, (list, tuple)) else [r]


def _convention_params(line):
    return sorted(k for k, v in (line.get("values") or {}).items() if v.get("source") == "CONVENTION")


# ---------------------------------------------------------------- per-line checks
def check_convention_where_printed(line, ctx):
    out = []
    for param in _convention_params(line):
        found = _printed_for(ctx["printed"], line, param)
        if not found:
            continue
        vals = sorted({round(float(p["value"]), 6) for p in found if p.get("basis", "STRUCTURAL") == "STRUCTURAL"})
        conv = line["values"][param].get("value")
        if len(vals) > 1:
            out.append(_finding("DG-1", "PRINTED_VALUES_DISAGREE", line["id"], line.get("element_id"),
                                f"{param}: convention {conv} used; printed structural values disagree {vals} "
                                f"(conflict register, never settled by the guard)", [_cite(p) for p in found]))
        else:
            out.append(_finding("DG-1", "CONVENTION_WHERE_PRINTED", line["id"], line.get("element_id"),
                                f"{param}: convention {conv} used where the documents print "
                                + ", ".join(f"{p['value']} {p.get('unit', 'm')} ({p.get('basis', 'STRUCTURAL')}, "
                                            f"{p.get('doc')})" for p in found), [_cite(p) for p in found]))
    return out


def check_search_recorded(line, ctx):
    if not _convention_params(line):
        return []
    searched = line.get("searched")
    if not searched:
        return [_finding("DG-2", "SEARCH_NOT_RECORDED", line["id"], line.get("element_id"),
                         f"conventions {_convention_params(line)} used with no record of the documents searched")]
    need = sorted(d["doc"] for d in ctx["documents"] if d.get("role") in SEARCH_ROLES)
    missing = [d for d in need if d not in set(searched)]
    if missing:
        return [_finding("DG-2", "SEARCH_INCOMPLETE", line["id"], line.get("element_id"),
                         f"conventions {_convention_params(line)} used; documents not searched: {missing}")]
    unapproved = [k for k in _convention_params(line) if not line["values"][k].get("approval")]
    if unapproved:
        return [_finding("DG-2", "FALLBACK_NOT_APPROVED", line["id"], line.get("element_id"),
                         f"conventions {unapproved} carry no answered owner decision or rule-library approval")]
    return []


def check_footprint(line, ctx):
    fp = line.get("footprint")
    if not fp or fp.get("value") is None:
        return []
    el = ctx["inventory_by_id"].get(line.get("element_id"))
    if not el:
        return []
    drawn = (el.get("parts") or {}).get(line.get("part", "WHOLE"))
    if not drawn or drawn.get("value") is None:
        return []
    if drawn.get("unit") != fp.get("unit"):
        raise GuardError(f"{line['id']}: footprint unit {fp.get('unit')} vs drawn {drawn.get('unit')}")
    d, m = float(drawn["value"]), float(fp["value"])
    if d <= 0:
        return []
    share = m / d
    if share < 1.0 - FOOTPRINT_TOL:
        return [_finding("DG-3", "PARTIAL_FOOTPRINT", line["id"], line.get("element_id"),
                         f"measured {m:.4f} of drawn {d:.4f} {fp['unit']} ({share:.1%}); missing {d - m:.4f} "
                         f"{fp['unit']}")]
    if share > 1.0 + FOOTPRINT_TOL:
        return [_finding("DG-3", "FOOTPRINT_EXCEEDS_DRAWN", line["id"], line.get("element_id"),
                         f"measured {m:.4f} exceeds drawn {d:.4f} {fp['unit']} ({share:.1%})")]
    return []


def check_finished_as_structural(line, ctx):
    if line.get("trade") not in STRUCTURAL_TRADES:
        return []
    out, by_id = [], ctx["printed_by_id"]
    for param, v in sorted((line.get("values") or {}).items()):
        src = v.get("source")
        if src not in ("PRINTED", "DERIVED"):
            continue
        refs = _refs(v)
        unknown = [r for r in refs if r not in by_id]
        if unknown or not refs:
            out.append(_finding("DG-4", "UNSUPPORTED_REF", line["id"], line.get("element_id"),
                                f"{param}: {src} value cites no known printed record {unknown or refs}"))
            continue
        bases = [by_id[r].get("basis", "STRUCTURAL") for r in refs]
        if src == "PRINTED" and "FINISHED" in bases:
            out.append(_finding("DG-4", "FINISHED_AS_STRUCTURAL", line["id"], line.get("element_id"),
                                f"{param}: {v.get('value')} taken from a FINISHED record as a structural dimension "
                                f"(no build-up to the structure line)", [_cite(by_id[r]) for r in refs]))
        elif src == "DERIVED" and bases and all(b == "FINISHED" for b in bases):
            out.append(_finding("DG-4", "FINISHED_AS_STRUCTURAL", line["id"], line.get("element_id"),
                                f"{param}: derived from FINISHED records only (no build-up record)",
                                [_cite(by_id[r]) for r in refs]))
    return out


def check_deductions(line, ctx):
    out = []
    for d in line.get("deductions") or []:
        mem = ctx["members_by_id"].get(d.get("member"))
        w = float(d.get("width_m", 0.0))
        if mem is None:
            out.append(_finding("DG-8", "DEDUCTION_EXCEEDS_MEMBER", line["id"], line.get("element_id"),
                                f"deduction {w:.3f} m by unknown member {d.get('member')}"))
            continue
        limit = float(mem["width_m"])
        face = d.get("face_width_m")
        if face is not None:
            limit = min(limit, float(face))
        if w > limit + DEDUCTION_TOL_M:
            out.append(_finding("DG-8", "DEDUCTION_EXCEEDS_MEMBER", line["id"], line.get("element_id"),
                                f"member {mem['id']} covers {w:.3f} m of the face but is {float(mem['width_m']):.3f} m "
                                f"wide (face {face}); the remainder stays open"))
    return out


LINE_CHECKS = {"DG-1": check_convention_where_printed, "DG-2": check_search_recorded, "DG-3": check_footprint,
               "DG-4": check_finished_as_structural, "DG-8": check_deductions}


# ---------------------------------------------------------------- set checks
def check_scenarios(lines, ctx):
    out = []
    issued = {r["element_id"] for r in ctx["revisions"]}
    for ln in lines:
        sc, origin = ln.get("scenario", "S0"), ln.get("origin", "DESIGN")
        if sc not in SCENARIOS:
            raise GuardError(f"{ln['id']}: scenario {sc}")
        if sc == "S0" and origin == "CLIENT_REQUEST":
            out.append(_finding("DG-7", "CLIENT_CHANGE_AS_APPROVED", ln["id"], ln.get("element_id"),
                                "client-requested change placed in the approved-design baseline; moved to S1"))
        elif sc == "S2" and ln.get("element_id") not in issued:
            out.append(_finding("DG-7", "REVISION_NOT_ISSUED", ln["id"], ln.get("element_id"),
                                "tagged consultant revision but no issued revision record for the element; moved to S1"))
    return out


def check_double_count(lines, ctx):
    owners = {}
    for ln in lines:
        if ln.get("state") not in LIVE_STATES or ln.get("scenario", "S0") == "S1":
            continue
        for z in ln.get("covers") or []:
            owners.setdefault((ln.get("trade"), ln.get("unit"), z), []).append(ln["id"])
    out = []
    for (trade, unit, z), ids in sorted(owners.items()):
        if len(ids) > 1:
            for i in ids:
                out.append(_finding("DG-6", "DOUBLE_COUNT", i, None,
                                    f"zone {z} ({trade}, {unit}) also counted by {[x for x in ids if x != i]}"))
    return out


def check_omissions(lines, ctx):
    carried = {}
    for ln in lines:
        if ln.get("scenario", "S0") == "S1" or ln.get("state") == "SUPERSEDED":
            continue
        carried.setdefault(ln.get("element_id"), set()).add(ln.get("part", "WHOLE"))
    out = []
    for el in ctx["inventory"]:
        parts = sorted((el.get("parts") or {"WHOLE": None}).keys())
        have = carried.get(el["id"], set())
        for p in parts:
            if p not in have:
                out.append(_finding("DG-5", "SILENT_OMISSION", None, el["id"],
                                    f"drawn element {el['id']} ({el.get('kind')}) part {p} carried by no line"))
    return out


SET_CHECKS = {"DG-5": check_omissions, "DG-6": check_double_count, "DG-7": check_scenarios}


# ---------------------------------------------------------------- driver
def _ctx(documents, printed, inventory, members, revisions):
    ids = [p["id"] for p in printed]
    if len(set(ids)) != len(ids):
        raise GuardError("duplicate printed record ids")
    return {"documents": list(documents or []), "printed": list(printed or []),
            "printed_by_id": {p["id"]: p for p in printed or []}, "inventory": list(inventory or []),
            "inventory_by_id": {e["id"]: e for e in inventory or []},
            "members_by_id": {m["id"]: m for m in members or []}, "revisions": list(revisions or [])}


def guard(lines, *, documents=(), printed=(), inventory=(), members=(), revisions=(), disabled=()):
    """Return {"baseline": [...], "scenarios": {"S1": [...]}, "findings": [...], "summary": {...}}.

    `disabled` names checks to skip (tests only: shows each regression test fails on the unguarded behaviour)."""
    ids = [ln["id"] for ln in lines]
    if len(set(ids)) != len(ids):
        raise GuardError("duplicate line ids")
    ctx = _ctx(documents, printed, inventory, members, revisions)
    findings = []
    for ln in lines:
        for k, fn in LINE_CHECKS.items():
            if k not in disabled:
                findings += fn(ln, ctx)
    for k, fn in SET_CHECKS.items():
        if k not in disabled:
            findings += fn(lines, ctx)

    by_line = {}
    for f in findings:
        if f["line_id"] is not None:
            by_line.setdefault(f["line_id"], []).append(f)
    baseline, s1 = [], []
    for ln in lines:
        g = copy.deepcopy(ln)
        g.setdefault("scenario", "S0")
        fl = by_line.get(ln["id"], [])
        g["guard"] = {"status": "FAIL" if fl else "PASS", "findings": [f["code"] for f in fl]}
        g["evidence_status"] = evidence_status(g, bool(fl))
        if fl and g.get("state") in LIVE_STATES:
            g["info_qty"] = g.get("qty")
            g["state"] = "HELD"
            g["held_cause"] = "; ".join(f"{f['code']}: {f['detail']}" for f in fl)
        if any(f["code"] in ("CLIENT_CHANGE_AS_APPROVED", "REVISION_NOT_ISSUED") for f in fl):
            g["scenario"] = "S1"
        (s1 if g["scenario"] == "S1" else baseline).append(g)
    for f in findings:
        if f["code"] == "SILENT_OMISSION":
            el = ctx["inventory_by_id"][f["element_id"]]
            part = f["detail"].rsplit(" part ", 1)[1].split(" ")[0]
            baseline.append({"id": f"DG5:{el['id']}:{part}", "element_id": el["id"], "element_kind": el.get("kind"),
                             "part": part, "qty": None, "state": "HELD", "scenario": "S0",
                             "held_cause": f"SILENT_OMISSION: {f['detail']}", "evidence_status": "HELD",
                             "guard": {"status": "FAIL", "findings": ["SILENT_OMISSION"]}})
    return {"baseline": baseline, "scenarios": {"S1": s1}, "findings": findings, "summary": summary(baseline, s1,
                                                                                                    findings)}


def evidence_status(line, failed):
    """WORKFLOW_CONTROLS s.5 label from the line's basis (VERIFIED is given only by a Checker verdict, never here)."""
    if failed or line.get("state") in ("HELD",):
        return "HELD"
    if line.get("state") == "UNKNOWN":
        return "UNKNOWN"
    if line.get("evidence_status") == "VERIFIED":
        return "VERIFIED"
    vals = list((line.get("values") or {}).values())
    if any(v.get("source") == "CONVENTION" and not v.get("approval") for v in vals):
        return "UNKNOWN"          # only reachable with DG-2 disabled: an unapproved convention is never ASSUMED
    if any(v.get("source") == "CONVENTION" for v in vals):
        return "ASSUMED - OWNER-APPROVED (" + ", ".join(sorted({v["approval"] for v in vals
                                                                if v.get("source") == "CONVENTION"})) + ")"
    return "DRAWING-CONFIRMED"


def released_total(lines, trade, unit):
    """Sum of live (RELEASED / PROVISIONAL) quantities; HELD and UNKNOWN are never summed and never 0."""
    return round(sum(float(ln["qty"]) for ln in lines if ln.get("trade") == trade and ln.get("unit") == unit
                     and ln.get("state") in LIVE_STATES and ln.get("qty") is not None), 6)


def summary(baseline, s1, findings):
    codes = {}
    for f in findings:
        codes[f["code"]] = codes.get(f["code"], 0) + 1
    held = [ln for ln in baseline if ln.get("state") == "HELD"]
    return {"lines_baseline": len(baseline), "lines_s1": len(s1), "held_baseline": len(held),
            "findings_by_code": dict(sorted(codes.items())),
            "held_info_qty_never_zero": all(ln.get("info_qty") not in (0, 0.0) for ln in held)}


# ---------------------------------------------------------------- adapter: canonical BOQ lines -> guard lines
def lines_from_canonical(boq_lines, conventions, *, mapping=None, doc_alias=None, approvals=None):
    """Turn URBAN_CANONICAL_BOQ_LINE_V1 rows that rest on a convention set into guard lines (read only).

    conventions  the convention set's list ({"id", "kind", "base", ...}); a cited id not in it is kept with value None
    mapping      {engine element_id: {"element_id", "element_kind", "part", "footprint_dim", "footprint_unit"}}: the
                 project's element register entry for an engine element (data, never code); unmapped lines keep the
                 engine element id and kind and carry no footprint
    doc_alias    {source file name as the line cites it: register doc id}
    approvals    {convention id: answered owner decision / rule-library id} (WORKFLOW_CONTROLS s.4); none by default
    Live = evidence state MEASURED / SOURCE_DERIVED / PROVISIONAL with a measured_net; every other row is HELD.
    """
    conv = {c["id"]: c for c in conventions}
    mapping, doc_alias, approvals = mapping or {}, doc_alias or {}, approvals or {}
    out = []
    for ln in boq_lines:
        used = (ln.get("rule") or {}).get("conventions_used") or []
        if not used:
            continue
        eid = (ln.get("location") or {}).get("element_id")
        m = mapping.get(eid, {})
        live = ln.get("evidence_state") in ("MEASURED", "SOURCE_DERIVED", "PROVISIONAL") and ln.get("measured_net") is not None
        values = {}
        for cid in used:
            c = conv.get(cid, {})
            v = {"value": c.get("base"), "source": "CONVENTION", "ref": cid}
            if cid in approvals:
                v["approval"] = approvals[cid]
            values[cid] = v
        g = {"id": ln["line_id"], "element_id": m.get("element_id", eid),
             "element_kind": m.get("element_kind", ln.get("physical_element")), "part": m.get("part", "WHOLE"),
             "trade": ln.get("trade"), "unit": ln.get("unit"), "qty": ln.get("measured_net") if live else None,
             "state": "PROVISIONAL" if live else "HELD", "values": values,
             "searched": sorted({doc_alias.get(d.get("file"), d.get("file"))
                                 for d in (ln.get("source") or {}).get("documents") or []}),
             "item_code": ln.get("item_code"), "engine_element_id": eid}
        dim = m.get("footprint_dim")
        dims = ((ln.get("calculation") or {}).get("inputs") or {}).get("dimensions") or {}
        if dim and dims.get(dim) is not None:
            g["footprint"] = {"value": float(dims[dim]), "unit": m.get("footprint_unit", "m2")}
        out.append(g)
    return out
