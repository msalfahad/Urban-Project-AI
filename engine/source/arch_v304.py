"""ARCH_TAKEOFF_V3.0.4 (T-167): the SAME opt-in BOQ candidate as ARCH_TAKEOFF_V3.0 .. V3.0.3 (engine.source.arch_v30,
arch_v301, arch_v302, arch_v303), with a no-assumptions audit of the route G profile the candidate runs on. Not a new
method family and not the released default (owner management decision 2026-10-20 sections 2 and 5); rollback is
running the released ARCH_TAKEOFF_V2.9.

Why: the candidate runs route G with a typed drawing profile (storey heights, levels, typical sections, ...). Owner
Q-17 A (2026-10-19): a value typed in from a drawing may feed a quantity only through a controlled project data file
(engine.source.project_data_file, URBAN_PROJECT_DATA_FILE_V1) whose record for it has a usable status
(DRAWING-VERIFIED, OWNER-CONFIRMED, DESIGNER-CONFIRMED, INFERRED); an ASSUMED or HELD value, or a value the file does
not hold, makes every dependent quantity HELD (MISSION.md no assumptions; WORKFLOW_CONTROLS 2026-10-21 s.4-5;
UP-QTY-STATUS-001: held is a range or blocked, never 0).

How it is built (tools/urban_boq_m9.py `arch --method ARCH_TAKEOFF_V3.0.4`):
  1. the run is the V3.0.3 candidate exactly: its V3_0_* .. V3_0_3_* files are written unchanged (arch_v30 .. arch_v303
     are not edited);
  2. the project inputs (URBAN_V304_PROFILE_AUDIT_V1) carry the project data file and one or more COMPARISON RUNS: the
     same V3.0.3 candidate on the same drawings with the profile values the data file does not make usable removed.
     The RESTRICTED run removes exactly that set (it is the candidate a Q-17 A profile gives); further runs remove one
     value each and only name the cause of a moved line (attribution);
  3. the profile of the run is checked against the data file: every profile value is a data-file record of the same
     project, a usable record carries the profile's value, and the restricted run removes exactly the non-usable ones;
     otherwise the run is refused (never a silent pass);
  4. PROFILE_AUDIT: every V3.0.3 line whose quantity state (evidence state, value, range) differs from the same line of
     the restricted run (or which the restricted run does not have) rests on a non-usable profile value. It becomes
     HELD:
        restricted line BOUNDED_EXPOSURE      -> BOUNDED_EXPOSURE over the restricted run's own range (the range the
                                                 drawings support without the value); the V3.0.3 figure kept in the
                                                 inputs as information
        anything else (blocked, absent, not applicable, a different released value)
                                              -> BLOCKED_RFI; the V3.0.3 figure and the restricted figure kept in the
                                                 inputs as information, never as a quantity
     its cause names the removed value(s), the data-file status and hold reason; the single-value runs name which value
     moves it (NO_SINGLE_VALUE when none alone does). A line of the restricted run that the V3.0.3 run does not have
     is listed (RESTRICTED_ONLY), never added;
  5. the V3_0_4_* files are written beside them: every line outside the V3.0.4 rows is byte-identical to the V3.0.3
     line (asserted on every run), and V3_0_4_DIFF.csv lists every line against V3.0.3 and against the released V2.9.

Nothing here names a project, a sheet, a key value or a coordinate; every number comes from the runs or the inputs.
"""

from __future__ import annotations

import copy
import csv
import hashlib
import io

from engine.source import arch_v30 as A30
from engine.source import arch_v302 as A302
from engine.source import arch_v303 as A303

METHOD = "ARCH_TAKEOFF_V3.0.4"
EXTENDS = A303.METHOD
CANDIDATE = A30.METHOD                  # the candidate family this version extends (never a new method family)
POLICY_ID = "URBAN_BOQ_T167_ARCH_V3_0_4"
LEDGER_SCHEMA = "URBAN_V304_INTEGRATION_LEDGER_V1"
INPUTS_SCHEMA = "URBAN_V304_PROFILE_AUDIT_V1"
ROLLBACK = A30.ROLLBACK
PIECE = "PROFILE_AUDIT"
RESTRICTED = "RESTRICTED"
NO_SINGLE_VALUE = "NO_SINGLE_VALUE"
EVIDENCE_STATUS = A302.EVIDENCE_STATUS
NUM_TOL = 1e-9

PIECES = {
    PIECE: {
        "module": "engine/source/arch_v304.py", "policy": "PROFILE_VALUE_Q17A_AUDIT_V1",
        "owner_rules": ["Q-17 A (typed drawing values only through a controlled project data file)",
                        "Q-21 C (founding datum unresolved: necks not computed on it)",
                        "UP-QTY-STATUS-001 (held is a range or blocked, never 0)",
                        "WORKFLOW_CONTROLS 2026-10-21 s.4-5"],
        "owner_manual_method": "manual QS take-off uses only printed dimensions and levels; a value the sheets do not "
                               "print (or print differently) is asked of the designer, never assumed",
        "drawing_method": "the same candidate re-run with every profile value the Q-17 A data file does not make "
                          "usable removed; a line that moves rests on that value and is held"},
}
WAITING = dict(A303.WAITING)
WAITING.pop("SLAB_STEEL", None)
WAITING.update({
    "SLAB_STEEL": "suspended-slab steel (T-152) and stair / landing steel (T-166), dome ring in-bay concrete (T-160): "
                  "V3.0.5 (T-179), branched from this candidate",
    "V6_CONVENTIONS": "lines resting on unprinted generic route G conventions (not profile values: e.g. ground-beam "
                      "length basis, exterior build-up, stair riser / waist) are outside this audit (T-044 bucket C)",
})


class InputsError(ValueError):
    pass


# ================================================================================================ helpers
def _r(x, n=6):
    return None if x is None else round(float(x), n)


def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and x == x


def _same_value(a, b):
    if _num(a) and _num(b):
        return abs(float(a) - float(b)) <= NUM_TOL
    return a == b


_UNIT_M = {"m": 1.0, "cm": 0.01, "mm": 0.001}


def _in_m(v, unit):
    """a number in metres for a length unit; other units (fraction, count, none) as given."""
    if not _num(v):
        return v
    return round(float(v) * _UNIT_M[unit], 9) if unit in _UNIT_M else float(v)


def qstate(ln):
    """the quantity state of a line (None = absent): evidence state, value, low, high (6 decimals)."""
    if ln is None:
        return None
    q = A30._qty(ln)
    return (q["state"], q["value"], q["low"], q["high"])


def _fig(ln):
    if ln is None:
        return {"state": "ABSENT", "value": None, "low": None, "high": None}
    return A30._qty(ln)


# ================================================================================================ inputs
def load_inputs(doc, project_id=None):
    """URBAN_V304_PROFILE_AUDIT_V1 or None:
        {"schema", "project",
         "data_file": {"file", "sha256", "doc": <URBAN_PROJECT_DATA_FILE_V1>},
         "audit_classes": {KEY: "<class from the printed-value audit, e.g. PRINTED / DIFFERENT / NOT_PRINTED>"},
         "runs": [{"id", "removed_keys": [...], "profile_sha256", "lines_sha256", "lines": [<BOQ lines>]}]}
    The data file is validated by engine.source.project_data_file (every fault refuses the inputs)."""
    from engine.source import project_data_file as PDF
    if doc is None:
        return None
    if doc.get("schema") != INPUTS_SCHEMA:
        raise InputsError(f"project inputs: schema must be {INPUTS_SCHEMA}")
    if project_id and doc.get("project") not in (None, project_id):
        raise InputsError(f"project inputs are for {doc.get('project')!r}, the run is {project_id!r}")
    df = doc.get("data_file") or {}
    for k in ("file", "sha256", "doc"):
        if not df.get(k):
            raise InputsError(f"data_file.{k} is required (owner Q-17 A: the controlled project data file)")
    try:
        PDF.load(df["doc"])
    except PDF.ProjectDataFileError as e:
        raise InputsError(f"data_file: {e}") from None
    runs = doc.get("runs") or []
    ids = set()
    for r in runs:
        if not r.get("id") or r["id"] in ids:
            raise InputsError(f"every comparison run has a unique id: {r.get('id')!r}")
        ids.add(r["id"])
        if not r.get("removed_keys") or not isinstance(r["removed_keys"], list):
            raise InputsError(f"run {r['id']}: removed_keys (the profile values it runs without) is required")
        for k in ("profile_sha256", "lines_sha256"):
            if not r.get(k):
                raise InputsError(f"run {r['id']}: {k} is required (the run must be reproducible)")
        if not isinstance(r.get("lines"), list):
            raise InputsError(f"run {r['id']}: its BOQ lines are required")
    if RESTRICTED not in ids:
        raise InputsError(f"a comparison run with id {RESTRICTED!r} (every non-usable value removed) is required")
    return doc


def lines_sha256(lines):
    return hashlib.sha256("".join(A30.line_sha(x) for x in lines).encode()).hexdigest()


def check_profile(inputs, profile):
    """the run's route G profile against the data file. -> {"usable": [...], "not_usable": {key: record}, ...}.
    Refuses: a profile value without a data-file record, a usable record whose value differs from the profile, a
    restricted run that does not remove exactly the non-usable values, a run removing a value the profile does not have,
    a run whose lines do not match their recorded sha256."""
    from engine.source import project_data_file as PDF
    if not profile or not profile.get("conventions"):
        raise InputsError(f"{METHOD} audits the route G profile of the run: run it with --profile")
    recs = {r["key"]: r for r in inputs["data_file"]["doc"]["records"]}
    conv = {c["id"]: c for c in profile["conventions"]}
    missing = sorted(set(conv) - set(recs))
    if missing:
        raise InputsError(f"profile value(s) with no project data file record: {missing} (owner Q-17 A)")
    usable, not_usable = [], {}
    for k, c in sorted(conv.items()):
        r = recs[k]
        if r["status"] not in PDF.USABLE:
            not_usable[k] = r
            continue
        if r["kind"] == "number":
            # every number the profile can use (base, low, high) must be the record's value or a usable printed
            # alternative of it, compared in metres for lengths (units: m / cm / mm)
            ok = [_in_m(r["value"], r["unit"])] + [_in_m(x.get("value"), x.get("unit") or r["unit"])
                                                   for x in r.get("alternatives") or ()
                                                   if x.get("status") in PDF.USABLE and _num(x.get("value"))]
            for part in ("base", "low", "high"):
                pv = c.get(part)
                if pv is None:
                    continue
                pm = _in_m(pv, c.get("unit") or r["unit"])
                if not any(_same_value(pm, x) for x in ok):
                    raise InputsError(f"{k}: the profile {part} {pv!r} {c.get('unit') or ''} is neither the project "
                                      f"data file value {r['value']!r} {r['unit']} nor a usable printed alternative")
        elif r["kind"] == "choice":
            if c.get("base") != r["value"]:
                raise InputsError(f"{k}: the profile choice {c.get('base')!r} differs from the project data file "
                                  f"{r['value']!r}")
        else:
            tabs = [c.get(t) for t in ("classes", "rows", "value", "table") if c.get(t) is not None]
            if r["value"] not in tabs:
                raise InputsError(f"{k}: the profile table differs from the project data file table")
        usable.append(k)
    runs = {r["id"]: r for r in inputs["runs"]}
    if set(runs[RESTRICTED]["removed_keys"]) != set(not_usable):
        raise InputsError(f"the {RESTRICTED} run removes {sorted(runs[RESTRICTED]['removed_keys'])}, the data file makes "
                          f"{sorted(not_usable)} not usable: they must be the same set")
    for r in inputs["runs"]:
        extra = set(r["removed_keys"]) - set(conv)
        if extra:
            raise InputsError(f"run {r['id']} removes {sorted(extra)}, which the profile of this run does not have")
        if lines_sha256(r["lines"]) != r["lines_sha256"]:
            raise InputsError(f"run {r['id']}: its lines do not match lines_sha256")
    return {"usable": usable, "not_usable": sorted(not_usable), "records": recs}


# ================================================================================================ the audit
def _cause(lid, l303, runs, restricted_keys):
    """which removed value(s) move this line: the single-value runs that change it, else NO_SINGLE_VALUE."""
    moved = []
    for r in runs:
        if r["id"] == RESTRICTED:
            continue
        o = r["by_id"].get(lid)
        if qstate(o) != qstate(l303):
            moved.append(r)
    keys = sorted({k for r in moved for k in r["removed_keys"]})
    return (keys or [NO_SINGLE_VALUE]), [r["id"] for r in moved]


def audit_changes(inputs, lines, profile, audit_classes=None):
    """PROFILE_AUDIT on the V3.0.3 lines. -> (changes, log)."""
    log = {"piece": PIECE, "state": "NOT_RUN"}
    if inputs is None:
        log["state"] = "NO_PROJECT_INPUT"
        return [], log
    chk = check_profile(inputs, profile)
    classes = dict(inputs.get("audit_classes") or {}, **(audit_classes or {}))
    runs = [dict(r, by_id={x["line_id"]: x for x in r["lines"]}) for r in inputs["runs"]]
    rr = next(r for r in runs if r["id"] == RESTRICTED)
    have = {x["line_id"] for x in lines}
    keys_r = sorted(rr["removed_keys"])
    recs = chk["records"]
    df = inputs["data_file"]
    changes, rows, by_cause, kept_out = [], [], {}, []
    for ln in lines:
        o = rr["by_id"].get(ln["line_id"])
        if qstate(o) == qstate(ln):
            continue
        if ln["evidence_state"] in ("NOT_APPLICABLE_WITH_EVIDENCE", "EXCLUDED_WITH_REASON"):
            # no quantity rests on it in the candidate (superseded / excluded): listed, never re-held
            kept_out.append({"line_id": ln["line_id"], "item_code": ln["item_code"], "state": ln["evidence_state"],
                             "restricted_run": _fig(o)})
            continue
        before = ln
        cause, moved_by = _cause(ln["line_id"], ln, runs, keys_r)
        why = "; ".join(f"{k} (project data file status {recs[k]['status']}"
                        + (f", audit class {classes[k]}" if classes.get(k) else "")
                        + (f": {recs[k].get('hold_reason')}" if recs[k].get("hold_reason") else "") + ")"
                        for k in (cause if cause != [NO_SINGLE_VALUE] else keys_r))
        lead = (f"PROFILE_VALUE_NOT_USABLE: this quantity moves when the profile value(s) the Q-17 A project data file "
                f"({df['file']}) does not make usable are removed"
                + (" (no single value moves it alone: NO_SINGLE_VALUE)" if cause == [NO_SINGLE_VALUE] else "")
                + f": {why}")
        after = copy.deepcopy(ln)
        if after.get("approval_state") not in ("MACHINE_ONLY", "REVIEWED"):
            raise ValueError(f"{METHOD}: line {ln['line_id']} is {after.get('approval_state')}: an approved line is "
                             "never re-held by the candidate")
        fo = _fig(o)
        info = {"policy": PIECES[PIECE]["policy"], "candidate_v3_0_3": A30._qty(ln), "restricted_run": fo,
                "removed_keys": keys_r, "moved_by": cause, "moved_by_runs": moved_by,
                "data_file": df["file"], "data_file_sha256": df["sha256"]}
        if fo["state"] == "BOUNDED_EXPOSURE":
            after.update(evidence_state="BOUNDED_EXPOSURE", measured_net=None,
                         bounded_range={"low": fo["low"], "high": fo["high"],
                                        "basis": f"{METHOD}: the range of the same line without the non-usable "
                                                 f"profile value(s) {keys_r}"})
            st = "HELD"
        else:
            after.update(evidence_state="BLOCKED_RFI", measured_net=None, bounded_range=None)
            st = "UNKNOWN" if fo["state"] in ("ABSENT", "NOT_APPLICABLE_WITH_EVIDENCE") else "HELD"
        after["gross"] = None
        after["rfi"] = {"question": lead[:900], "unlocks": (ln.get("location") or {}).get("element_id")}
        after["calculation"] = dict(after["calculation"],
                                    inputs=dict(after["calculation"].get("inputs") or {}, profile_audit=info))
        A303._note(after, f"{METHOD}: HELD - rests on a profile value the project data file does not make usable "
                          f"({', '.join(cause)}); V3.0.3 figure {A302._q(A30._qty(ln))} kept as information")
        changes.append(A303._change(PIECE, "REPLACE", before, after,
                                    drawing_reference="; ".join(f"{k}: {recs[k]['drawing_number']} {recs[k]['sheet']}"
                                                                for k in keys_r)[:600],
                                    held=[{"what": f"{ln['item_code']} {(ln.get('location') or {}).get('element_id')}",
                                           "why": lead,
                                           "range": [after["bounded_range"]["low"], after["bounded_range"]["high"]]
                                           if after.get("bounded_range") else None}],
                                    downstream=[], evidence_status=st, cause=cause,
                                    verification={"task": "T-167", "merge_commit": "this candidate",
                                                  "verifier_run": "Gate B on V3.0.4 (pending)"}))
        k = "|".join(cause)
        c = by_cause.setdefault(k, {"lines": 0, "by_code": {}})
        c["lines"] += 1
        code = c["by_code"].setdefault(f"{ln['item_code']}|{ln['unit']}", {"lines": 0, "v3_0_3_released": 0.0,
                                                                            "to_bounded": 0, "to_blocked": 0})
        code["lines"] += 1
        q = A30._qty(ln)
        if q["value"] is not None and ln["evidence_state"] in ("MEASURED", "SOURCE_DERIVED", "PROVISIONAL"):
            code["v3_0_3_released"] = _r(code["v3_0_3_released"] + q["value"])
        code["to_bounded" if after["evidence_state"] == "BOUNDED_EXPOSURE" else "to_blocked"] += 1
        rows.append(ln["line_id"])
    only = sorted(set(rr["by_id"]) - have)
    log.update(state="RUN", removed_keys=keys_r, usable_keys=chk["usable"], lines_held=len(changes),
               by_cause=by_cause, no_quantity_in_v3_0_3=kept_out, restricted_only=[{"line_id": x, "item_code": rr["by_id"][x]["item_code"],
                                                    "quantity": A30._qty(rr["by_id"][x])} for x in only],
               runs=[{"id": r["id"], "removed_keys": r["removed_keys"], "profile_sha256": r["profile_sha256"],
                      "lines_sha256": r["lines_sha256"], "lines": len(r["lines"])} for r in inputs["runs"]],
               data_file={"file": df["file"], "sha256": df["sha256"]})
    return changes, log


# ================================================================================================ integrate / ledger
def integrate(l303, v304_changes):
    """-> (V3.0.4 lines, identity). Every line outside the V3.0.4 rows is byte-identical to the V3.0.3 line; a line two
    V3.0.4 rows change, or a row naming a line V3.0.3 does not have, is refused."""
    from engine.source import boq_line as BL
    sid = {ln["line_id"] for ln in l303}
    rep = {}
    for c in v304_changes:
        if c["action"] != "REPLACE":
            raise ValueError(f"{METHOD}: action {c['action']} (V3.0.4 only re-holds V3.0.3 lines)")
        lid = c["before"]["line_id"]
        if lid in rep:
            raise ValueError(f"{METHOD}: line {lid} changed twice")
        if lid not in sid:
            raise ValueError(f"{METHOD}: a change names a line the V3.0.3 run does not have")
        if c["after"]["line_id"] != lid:
            raise ValueError(f"{METHOD}: a re-held line keeps its line id")
        rep[lid] = c["after"]
    out = [rep.get(ln["line_id"], ln) for ln in l303]
    for ln in out:
        BL.validate(ln)
    by303 = {ln["line_id"]: ln for ln in l303}
    outside = [ln for ln in out if ln["line_id"] not in rep]
    bad = [ln["line_id"] for ln in outside if A30.line_sha(by303[ln["line_id"]]) != A30.line_sha(ln)]
    if bad or len(outside) + len(rep) != len(l303):
        raise ValueError(f"{METHOD}: {len(bad)} line(s) outside the V3.0.4 rows differ from {EXTENDS}")
    ident = {"v3_0_3_lines": len(l303), "v3_0_4_lines": len(out), "v3_0_4_rows": len(v304_changes),
             "replaced": len(rep), "added": 0, "outside_rows": len(outside),
             "outside_rows_identical_to_v3_0_3": len(outside),
             "outside_rows_sha256": hashlib.sha256("".join(A30.line_sha(x) for x in outside).encode()).hexdigest()}
    return out, ident


def ledger_rows(changes, released_lines=None):
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    rows = []
    for c in changes:
        ref = c["before"]
        b303, aft = A30._qty(c["before"]), A30._qty(c["after"])
        b29 = None
        if released_lines is not None:
            b29 = A30._qty(rel[A30._key(ref)]) if A30._key(ref) in rel else dict(A30._qty(None),
                                                                                 state="NOT_IN_RELEASED")
        loc = ref.get("location") or {}
        p = PIECES[c["piece"]]
        rows.append({"version": METHOD, "piece": c["piece"], "action": c["action"], "line_id": ref["line_id"],
                     "item_code": ref["item_code"], "floor": loc.get("floor"), "element_id": loc.get("element_id"),
                     "unit": ref["unit"], "before_released_v2_9": b29, "before_v3_0_3": b303, "after_v3_0_4": aft,
                     "cause": c.get("cause"), "evidence_status": c.get("evidence_status") or "HELD",
                     "release_status": "NOT RELEASED", "drawing_reference": c.get("drawing_reference"),
                     "owner_manual_method": p["owner_manual_method"], "drawing_method": p["drawing_method"],
                     "owner_rules": p["owner_rules"],
                     "verification": dict(c.get("verification") or {}, module=p["module"], policy=p["policy"]),
                     "held": c.get("held") or [], "downstream": c.get("downstream") or [], "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "piece", "action", "line_id", "item_code", "floor", "element_id", "unit", "v2_9", "v3_0_3",
              "v3_0_4", "cause", "evidence_status", "release_status", "drawing_reference", "held")


def _csv(rows, cols):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=cols, lineterminator="\n", extrasaction="ignore")
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue()


def ledger_csv(rows):
    return _csv([{"version": r["version"], "piece": r["piece"], "action": r["action"], "line_id": r["line_id"],
                  "item_code": r["item_code"], "floor": r["floor"], "element_id": r["element_id"], "unit": r["unit"],
                  "v2_9": A302._q(r["before_released_v2_9"]), "v3_0_3": A302._q(r["before_v3_0_3"]),
                  "v3_0_4": A302._q(r["after_v3_0_4"]), "cause": "|".join(r["cause"] or ()),
                  "evidence_status": r["evidence_status"], "release_status": r["release_status"],
                  "drawing_reference": r["drawing_reference"],
                  "held": "; ".join(str(h.get("why") or h.get("what")) for h in r["held"])[:600]} for r in rows],
                LEDGER_CSV)


DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_v3_0_3", "vs_released_v2_9", "v2_9", "v3_0_3",
            "v3_0_4")


def diff_rows(l303, l304, released_lines=None):
    b303 = {ln["line_id"]: ln for ln in l303}
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    out = []
    for ln in l304:
        o = b303.get(ln["line_id"])
        vs = "ADDED" if o is None else ("SAME" if A30.line_sha(o) == A30.line_sha(ln) else "CHANGED")
        r = rel.get(A30._key(ln)) if released_lines is not None else None
        vs29 = None if released_lines is None else ("NOT_IN_RELEASED" if r is None else
                                                    ("SAME_QUANTITY" if A30._qty(r) == A30._qty(ln) else
                                                     "QUANTITY_DIFFERS"))
        out.append({"line_id": ln["line_id"], "item_code": ln["item_code"], "floor": ln["location"].get("floor"),
                    "element_id": ln["location"].get("element_id"), "unit": ln["unit"], "vs_v3_0_3": vs,
                    "vs_released_v2_9": vs29, "v2_9": A302._q(A30._qty(r)) if r else "",
                    "v3_0_3": A302._q(A30._qty(o)) if o else "", "v3_0_4": A302._q(A30._qty(ln))})
    return out


def code_totals(lines):
    """per item code and unit: released quantity, held range (bounded lines), blocked lines (no quantity)."""
    out = {}
    for ln in lines:
        if ln["evidence_state"] in ("NOT_APPLICABLE_WITH_EVIDENCE", "EXCLUDED_WITH_REASON"):
            continue
        k = out.setdefault(f"{ln['item_code']}|{ln['unit']}", {"lines": 0, "released": 0.0, "held_low": 0.0,
                                                                "held_high": 0.0, "bounded_lines": 0,
                                                                "blocked_lines": 0})
        k["lines"] += 1
        q = A30._qty(ln)
        if q["value"] is not None and ln["evidence_state"] != "BLOCKED_RFI":
            k["released"] += q["value"]
        elif q["low"] is not None:
            k["held_low"] += q["low"]
            k["held_high"] += q["high"]
            k["bounded_lines"] += 1
        else:
            k["blocked_lines"] += 1
    return {k: {a: _r(b) if isinstance(b, float) else b for a, b in v.items()} for k, v in sorted(out.items())}


def write(out, l303, v304_changes, log, inputs, released_lines=None):
    """the V3_0_4_* files beside the V3_0_3_* files. -> (file names, identity, ledger)."""
    from pathlib import Path
    from engine.source import boq_line as BL
    out = Path(out)
    l304, ident = integrate(l303, v304_changes)
    rows = ledger_rows(v304_changes, released_lines)
    diff = diff_rows(l303, l304, released_lines)
    dsum = {}
    for d in diff:
        dsum.setdefault("vs_v3_0_3", {}).setdefault(d["vs_v3_0_3"], 0)
        dsum["vs_v3_0_3"][d["vs_v3_0_3"]] += 1
        if d["vs_released_v2_9"] is not None:
            dsum.setdefault("vs_released_v2_9", {}).setdefault(d["vs_released_v2_9"], 0)
            dsum["vs_released_v2_9"][d["vs_released_v2_9"]] += 1
    ident = dict(ident, diff=dsum)
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "waiting_pieces": WAITING, "integration_package": True}
    t303, t304 = code_totals(l303), code_totals(l304)
    moved = {k: {"v3_0_3": t303.get(k), "v3_0_4": t304.get(k)} for k in sorted(set(t303) | set(t304))
             if t303.get(k) != t304.get(k)}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_logs": [log],
           "inputs": {"data_file": (inputs or {}).get("data_file", {}).get("file"),
                      "data_file_sha256": (inputs or {}).get("data_file", {}).get("sha256"),
                      "audit_classes": (inputs or {}).get("audit_classes")},
           "totals_moved_by_code": moved, "waiting_pieces": WAITING,
           "evidence_status_counts": A302._count(r["evidence_status"] for r in rows)}
    files = {"V3_0_4_BOQ_LINES.json": BL.dumps(l304),
             "V3_0_4_BOQ_LINES.csv": A30._lines_csv(l304),
             "V3_0_4_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_4_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_4_DIFF.csv": _csv(diff, DIFF_CSV),
             "V3_0_4_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK}


__all__ = ["METHOD", "PIECES", "WAITING", "load_inputs", "check_profile", "audit_changes", "integrate", "ledger_rows",
           "diff_rows", "code_totals", "write", "lines_sha256", "InputsError"]
