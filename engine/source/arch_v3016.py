"""ARCH_TAKEOFF_V3.0.16 (T-245): the SAME opt-in BOQ candidate as ARCH_TAKEOFF_V3.0 .. V3.0.15 (engine.source.arch_v30,
arch_v301 .. arch_v3015), with ONE project identity and ONE revision set over every drawing the candidate rests on.
Not a new method family and not the released default (owner management decision 2026-10-20 sections 2 and 5);
rollback is running the released ARCH_TAKEOFF_V2.9. No quantity, state, rule or line id changes here.

The question (lessons 2026-10-24; owner 2026-10-24 23:49 (a), 23:57 (4)): one BOQ is one project, and every drawing it
rests on keeps its own revision inside ONE revision set. Up to V3.0.15 each route stamps its own identity: the
architectural route the run's --project id and the sha256 of the plan file alone, the structural route the project name
of its known-drawing table and the sha256 of the structural file alone, so one candidate carries two project ids and two
revision sets and the export refuses it (probe 10). Relaxing probe 10, or writing one arbitrary id over both, would hide
a genuine mix; instead the project inputs (URBAN_V3016_INPUTS_V1) declare, from source evidence:

  project    {project_id, evidence}: the ONE project id (never "new project");
  documents  [{discipline, title, sheet, revision, revision_state PRINTED | UNCONFIRMED, reason, sha256}]: every
             drawing file of the run, each with its own revision; an UNCONFIRMED revision names why (never an
             invented revision, never "approved set"); the file sha256 proves the file used, not its approval;
  routes     [{route_project_id, documents: [sha256 ..], evidence}]: each route identity that belongs to the project
             and the documents it was computed from.

Refused (InputsError / ValueError, nothing written): two documents of one discipline + sheet with different sha256
(two revisions of one sheet), one sha256 twice, a document no route uses, a route naming an undeclared document, a
route whose documents do not give its revision set sha256 (the route identity is not the declared files), a line whose
(project id, revision set) is no declared route (another project in the run), a line resting on a document outside the
set. Then every line gets the project block {project_id, revision_set_sha256 (of the whole set), route {...}} (the
route identity kept for audit), and the title of each document it rests on is the declared title (CAUSE of the run to
run json difference, T-245 s.1: the local copy's FILE NAME entered source.documents[].file, which no csv column shows;
the sha256 is the identity, the local name is run metadata and goes to V3_0_16_RUN.json). Everything else in every line
is byte-identical to V3.0.15 (asserted on every run), line ids included: a verdict bound to a line id stays on it.

Files: V3_0_16_BOQ_LINES.json / .csv, V3_0_16_IDENTITY.json (the project id, the revision set and its sha256, each
document's revision state: the export states it), V3_0_16_DIFF.csv (every line against V3.0.15 and the released V2.9:
IDENTITY_ONLY / SAME), V3_0_16_RUN.json (run metadata: local file names, counts). Nothing here names a project, a
sheet, a file or a revision: every value comes from the inputs.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re

from engine.source import arch_v30 as A30
from engine.source import arch_v302 as A302
from engine.source import arch_v304 as A304
from engine.source import arch_v305 as A305
from engine.source import arch_v3015 as A3015

DEFAULT_GUARD_CLASS = "TOOLING"          # T-212: identity restamp only; it produces and changes no quantity
METHOD = "ARCH_TAKEOFF_V3.0.16"
EXTENDS = A3015.METHOD
CANDIDATE = A30.METHOD                   # the candidate family this version extends (never a new method family)
POLICY_ID = "URBAN_BOQ_T245_ARCH_V3_0_16"
INPUTS_SCHEMA = "URBAN_V3016_INPUTS_V1"
IDENTITY_SCHEMA = "URBAN_BOQ_PROJECT_IDENTITY_V1"
ROLLBACK = A30.ROLLBACK
DISCIPLINES = ("ARCHITECTURAL", "STRUCTURAL", "SANITARY", "ELECTRICAL", "MECHANICAL", "OTHER")
REVISION_STATES = ("PRINTED", "UNCONFIRMED")
_SHA = re.compile(r"^[0-9a-f]{64}$")


class InputsError(ValueError):
    pass


def revision_set_sha256(shas):
    """the same function as tools/urban_boq_m9.revision_set_sha256 (sorted file sha256 joined by '|')."""
    return hashlib.sha256("|".join(sorted(shas)).encode("utf-8")).hexdigest()


def _text(v):
    return isinstance(v, str) and v.strip() != ""


def load_inputs(doc):
    """-> the checked inputs (copy). Refuses a genuine mix or an identity that is not the declared files."""
    if not isinstance(doc, dict) or doc.get("schema") != INPUTS_SCHEMA:
        raise InputsError(f"{METHOD}: inputs schema must be {INPUTS_SCHEMA}")
    pr = doc.get("project") or {}
    pid = pr.get("project_id")
    if not _text(pid) or pid.strip().lower() == "new project":
        raise InputsError(f"{METHOD}: the project id is missing (a BOQ is one named project)")
    if not _text(pr.get("evidence")):
        raise InputsError(f"{METHOD}: the project id needs its source evidence")
    docs = doc.get("documents") or []
    if not docs:
        raise InputsError(f"{METHOD}: no documents: a revision set names every drawing file of the run")
    by_sha, by_sheet = {}, {}
    for i, d in enumerate(docs):
        for k in ("discipline", "title", "sheet", "revision", "revision_state", "sha256"):
            if not _text(d.get(k)):
                raise InputsError(f"{METHOD}: document #{i}: {k} missing")
        if d["discipline"] not in DISCIPLINES:
            raise InputsError(f"{METHOD}: document #{i}: discipline {d['discipline']!r}")
        if d["revision_state"] not in REVISION_STATES:
            raise InputsError(f"{METHOD}: document #{i}: revision_state {d['revision_state']!r}")
        if d["revision_state"] == "UNCONFIRMED" and not _text(d.get("reason")):
            raise InputsError(f"{METHOD}: document #{i}: an UNCONFIRMED revision names why")
        if not _SHA.match(d["sha256"]):
            raise InputsError(f"{METHOD}: document #{i}: sha256 must be 64 lower-case hex")
        if d["sha256"] in by_sha:
            raise InputsError(f"{METHOD}: document sha256 {d['sha256'][:12]} declared twice")
        key = (d["discipline"], d["sheet"].strip())
        if key in by_sheet:
            raise InputsError(f"{METHOD}: two revisions of one sheet ({key[0]} {key[1]!r}: {by_sheet[key][:12]} and "
                              f"{d['sha256'][:12]}): one revision set holds one revision per sheet (refused)")
        by_sha[d["sha256"]], by_sheet[key] = d, d["sha256"]
    routes = doc.get("routes") or []
    if not routes:
        raise InputsError(f"{METHOD}: no routes: each route identity of the run is declared")
    used, rkeys = set(), {}
    for i, r in enumerate(routes):
        rid = r.get("route_project_id")
        if not _text(rid) or not _text(r.get("evidence")):
            raise InputsError(f"{METHOD}: route #{i}: route_project_id and evidence required")
        rs = list(r.get("documents") or [])
        if not rs:
            raise InputsError(f"{METHOD}: route #{i}: no documents")
        unk = [s for s in rs if s not in by_sha]
        if unk:
            raise InputsError(f"{METHOD}: route #{i} names {len(unk)} document(s) outside the revision set")
        rkey = (rid, revision_set_sha256(rs))
        if rkey in rkeys:
            raise InputsError(f"{METHOD}: route #{i} repeats a route identity")
        rkeys[rkey] = i
        used |= set(rs)
    unused = sorted(set(by_sha) - used)
    if unused:
        raise InputsError(f"{METHOD}: {len(unused)} declared document(s) no route uses (a revision set is the run's "
                          "files, not a list of possible files)")
    out = copy.deepcopy(doc)
    out["revision_set_sha256"] = revision_set_sha256(by_sha)
    out["route_keys"] = sorted([list(k) for k in rkeys])
    return out


def identity_record(inputs):
    """the V3_0_16_IDENTITY.json content: what the export states (project, revision set, each revision state)."""
    docs = sorted(inputs["documents"], key=lambda d: (d["discipline"], d["sheet"], d["sha256"]))
    unconf = [f"{d['discipline']} {d['sheet']}: revision UNCONFIRMED ({d['reason']})" for d in docs
              if d["revision_state"] == "UNCONFIRMED"]
    return {"schema": IDENTITY_SCHEMA, "method": METHOD, "project_id": inputs["project"]["project_id"],
            "project_evidence": inputs["project"]["evidence"],
            "revision_set_sha256": inputs["revision_set_sha256"],
            "revision_set_rule": "sha256 of the sorted file sha256 values joined by '|' (each file pinned by content)",
            "documents": [{k: d.get(k) for k in ("discipline", "title", "sheet", "revision", "revision_state", "reason",
                                                 "sha256")} for d in docs],
            "routes": [{"route_project_id": r["route_project_id"],
                        "route_revision_set_sha256": revision_set_sha256(r["documents"]),
                        "documents": sorted(r["documents"]), "evidence": r["evidence"]}
                       for r in sorted(inputs["routes"], key=lambda r: r["route_project_id"])],
            "disclosures": unconf,
            "provenance_note": "a file sha256 proves the file used, not that it is the latest approved revision"}


def restamp(line, inputs):
    """-> (V3.0.16 line, local file names replaced). Only project and source.documents[].file change."""
    pr = line.get("project") or {}
    key = [pr.get("project_id"), pr.get("revision_set_sha256")]
    if key not in inputs["route_keys"]:
        raise ValueError(f"{METHOD}: line {line['line_id']} carries project id {pr.get('project_id')!r} / revision set "
                         f"{str(pr.get('revision_set_sha256'))[:12]}, which is no declared route of this project: "
                         "another project or an undeclared drawing in the run (refused)")
    titles = {d["sha256"]: d["title"] for d in inputs["documents"]}
    new = copy.deepcopy(line)
    renamed = []
    for d in (new.get("source") or {}).get("documents") or []:
        s = d.get("sha256")
        if s is None:
            continue
        if s not in titles:
            raise ValueError(f"{METHOD}: line {line['line_id']} rests on a document {str(s)[:12]} outside the "
                             "revision set (refused)")
        if d.get("file") != titles[s]:
            renamed.append(d.get("file"))
            d["file"] = titles[s]
    new["project"] = {"project_id": inputs["project"]["project_id"],
                      "revision_set_sha256": inputs["revision_set_sha256"],
                      "route": {"project_id": key[0], "revision_set_sha256": key[1]}}
    return new, renamed


def _body(line):
    """a line without the two fields V3.0.16 restamps (the comparison key of 'everything else byte-identical')."""
    b = copy.deepcopy(line)
    b.pop("project", None)
    for d in (b.get("source") or {}).get("documents") or []:
        d.pop("file", None)
    return b


def integrate(l3015, inputs):
    """-> (V3.0.16 lines, identity, local names). Order, line ids and every other field kept (asserted)."""
    from engine.source import boq_line as BL
    out, local = [], {}
    for ln in l3015:
        n, renamed = restamp(ln, inputs)
        for f in renamed:
            local[f] = local.get(f, 0) + 1
        out.append(BL.validate(n))
    if [x["line_id"] for x in out] != [x["line_id"] for x in l3015]:
        raise ValueError(f"{METHOD}: line ids or order changed")
    bad = [a["line_id"] for a, b in zip(l3015, out)
           if json.dumps(_body(a), sort_keys=True) != json.dumps(_body(b), sort_keys=True)]
    if bad:
        raise ValueError(f"{METHOD}: {len(bad)} line(s) changed outside the identity fields")
    pids = {x["project"]["project_id"] for x in out}
    revs = {x["project"]["revision_set_sha256"] for x in out}
    if len(pids) != 1 or len(revs) != 1:
        raise ValueError(f"{METHOD}: the restamped lines still carry {len(pids)} project ids / {len(revs)} sets")
    by_route = {}
    for x in out:
        k = x["project"]["route"]["project_id"]
        by_route[k] = by_route.get(k, 0) + 1
    ident = {"v3_0_15_lines": len(l3015), "v3_0_16_lines": len(out), "lines_by_route_project": by_route,
             "project_id": next(iter(pids)), "revision_set_sha256": next(iter(revs)),
             "identity_only_changes": sum(1 for a, b in zip(l3015, out) if A30.line_sha(a) != A30.line_sha(b)),
             "body_identical_to_v3_0_15": len(out),
             "body_sha256": hashlib.sha256("".join(
                 hashlib.sha256(json.dumps(_body(x), sort_keys=True).encode()).hexdigest() for x in out
             ).encode()).hexdigest()}
    return out, ident, local


DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_v3_0_15", "vs_released_v2_9", "v2_9",
            "v3_0_15", "v3_0_16", "route_project_id")


def diff_rows(l3015, l3016, released_lines=None):
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    out = []
    for o, ln in zip(l3015, l3016):
        vs = "SAME" if A30.line_sha(o) == A30.line_sha(ln) else "IDENTITY_ONLY"
        r = rel.get(A30._key(ln)) if released_lines is not None else None
        vs29 = None if released_lines is None else ("NOT_IN_RELEASED" if r is None else
                                                    ("SAME_QUANTITY" if A30._qty(r) == A30._qty(ln) else
                                                     "QUANTITY_DIFFERS"))
        out.append({"line_id": ln["line_id"], "item_code": ln["item_code"], "floor": ln["location"].get("floor"),
                    "element_id": ln["location"].get("element_id"), "unit": ln["unit"], "vs_v3_0_15": vs,
                    "vs_released_v2_9": vs29, "v2_9": A302._q(A30._qty(r)) if r else "",
                    "v3_0_15": A302._q(A30._qty(o)), "v3_0_16": A302._q(A30._qty(ln)),
                    "route_project_id": ln["project"]["route"]["project_id"]})
    return out


def write(out, l3015, inputs, released_lines=None):
    """the V3_0_16_* files beside the V3_0_15_* files. -> (file names, identity)."""
    from pathlib import Path
    from engine.source import boq_line as BL
    out = Path(out)
    l3016, ident, local = integrate(l3015, inputs)
    diff = diff_rows(l3015, l3016, released_lines)
    dsum = {}
    for d in diff:
        dsum.setdefault("vs_v3_0_15", {}).setdefault(d["vs_v3_0_15"], 0)
        dsum["vs_v3_0_15"][d["vs_v3_0_15"]] += 1
        if d["vs_released_v2_9"] is not None:
            dsum.setdefault("vs_released_v2_9", {}).setdefault(d["vs_released_v2_9"], 0)
            dsum["vs_released_v2_9"][d["vs_released_v2_9"]] += 1
    t15, t16 = A304.code_totals(l3015), A304.code_totals(l3016)
    moved = {k: [t15.get(k), t16.get(k)] for k in sorted(set(t15) | set(t16)) if t15.get(k) != t16.get(k)}
    if moved:
        raise ValueError(f"{METHOD}: totals moved on {len(moved)} code(s): an identity step moves no quantity")
    ident = dict(ident, diff=dsum, totals_moved_by_code={})
    idrec = identity_record(inputs)
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "project_identity": idrec,
           "run_metadata": {"local_file_names_replaced_by_declared_titles": dict(sorted(local.items())),
                            "note": "local copy names are run metadata, outside the canonical line content"}}
    files = {"V3_0_16_BOQ_LINES.json": BL.dumps(l3016),
             "V3_0_16_BOQ_LINES.csv": A30._lines_csv(l3016),
             "V3_0_16_IDENTITY.json": A30._j(idrec),
             "V3_0_16_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_16_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "inputs_schema": INPUTS_SCHEMA, "identity_schema": IDENTITY_SCHEMA,
            "released_default": False, "rollback": ROLLBACK}


__all__ = ["METHOD", "DEFAULT_GUARD_CLASS", "INPUTS_SCHEMA", "IDENTITY_SCHEMA", "load_inputs", "identity_record",
           "restamp", "integrate", "diff_rows", "write", "revision_set_sha256", "InputsError"]
