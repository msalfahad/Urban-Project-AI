"""V3.0 GATE B v2 (T-168): the Gate B diff of tools/v30_gate_b.py (T-156, kept unchanged and still usable) run against
NAMED, PINNED sides, with the owner's 2026-10-23 19:00 / 19:45 regression and provenance checks. A read-only check
tool: it computes, changes and approves no quantity, and nothing in engine/ imports it (rollback: delete this file).

    python3 -I tools/v30_gate_b_v2.py diff BEFORE.json AFTER.json --before-manifest M --after-manifest M --out DIR
            [--before-spec SPEC.json] [--after-spec SPEC.json] [--baseline-a A.json --baseline-a-manifest M]
            [--verdicts VERDICTS_V2.json] [--changes ESTABLISHED_QUANTITY_CHANGES.json] [--register REG.json]
            [--ledger LEDGER.json ...] [--sha SHA] [--new-revision-set] [--sealed-registry R.json]
    python3 -I tools/v30_gate_b_v2.py manifest --lines V3_0_x_BOQ_LINES.json --candidate-version V --code-commit SHA
            --project-id P --drawing ROLE=PATH [--drawing ROLE=PATH ...] [--document-register REGISTER.csv]
            [--verdicts VERDICTS_V2.json] --out CANDIDATE_MANIFEST.json
    python3 -I tools/v30_gate_b_v2.py change-add --log ESTABLISHED_QUANTITY_CHANGES.json --candidate-version V
            --project-id P --line-id ID --element-id E [...] --unit U --old Q|HELD --new Q|HELD --cause TEXT
            --evidence SHEET=VALUE [...] --checker-verdict VERDICT_ID|NONE
    python3 -I tools/v30_gate_b_v2.py pick --sha SHA ID [ID ...]                       (as tools/v30_gate_b.py)

1 PINNED SIDES (refused, exit 2, nothing written, every reason listed). Each side of a diff names its manifest: the
  release manifest of the T-165 baseline runner (URBAN_BASELINE_MANIFEST_V1) or a candidate manifest written by
  `manifest` (URBAN_CANDIDATE_MANIFEST_V1). Refused: a missing manifest (MANIFEST_MISSING); an unknown schema, a
  release run that exited non-zero or did not reproduce (MANIFEST_INVALID); a lines file whose sha256 or line count is
  not the manifest's, a --*-spec file whose sha256 is not the manifest's spec_sha256 (MANIFEST_MISMATCH); two sides of
  different project ids (PROJECT_MIX: line pairing needs one project, T-165); two sides that pin the same drawing
  (same role or same file name) with different sha256, unless --new-revision-set says the after side is a re-measure
  on a new drawing revision (DRAWING_MISMATCH); a sealed input (SEALED, section 5).
2 ONE PROJECT, PINNED REVISION SETS PER SIDE (probes 7, 10). A line carries (project id, revision set). Without a
  manifest a side must carry exactly one of each. With a manifest every line's revision set must be the revision set
  of a non-empty subset of the side's pinned drawings (tools/urban_boq_m9.py revision_set_sha256: sha256 of the sorted
  drawing sha256s joined by '|'; the architectural route hashes the plan, route G the structural drawing, so a real
  candidate carries two), else REVISION_MIX; its project id must be the manifest's (a release run without a project
  id writes the engine's own default 'new project', and a route that is not given the id writes it too: listed as
  an alias), or a route label the candidate manifest declares for that same revision set (an alias), else
  PROJECT_MIX. Identity is by drawing sha256, never by label:
  a line measured on drawings the side does not pin is refused whatever project id it prints.
3 THE DIFF. Rows, pairing and the eleven T-156 flags come from tools/v30_gate_b.py unchanged (its thresholds, its
  picker). One flag is added:
    VERIFIED_CHANGED  the before line is bound by a COUNTED Checker verdict (URBAN_CHECKER_VERDICT_V2, T-235) and its
                      after line is not byte-identical in the quantity fields (unit, evidence state, gross, deductions,
                      additions, measured net, bounded range), the element id, the project id and the revision set,
                      or the line was dropped: any change, however small (a change of 0.0004 is flagged; the row also
                      says whether the scoreboard's 0.0005 tolerance would still count it). Review required.
  Verdict carry (owner 19:45): a verdict carries to the next candidate only when every line it binds is byte-identical
  in those fields; otherwise it is STALE and its lines leave VERIFIED until a new verdict binds the after side
  (REVERIFIED). A verdict binds the before side when its project id, revision set, candidate version (= the before
  spec id) and BOQ_LINES sha256 (= the before file) are the before side's, its lines and element scope are there, its
  engine qty equals theirs within 0.0005 and the checker qty is within 1 % (tools/boq_export_v1.py rules); any
  other record is listed with its status, never counted.
4 ESTABLISHED QUANTITY CHANGES (owner 19:00 (7)). An append-only file per candidate (URBAN_ESTABLISHED_QUANTITY_CHANGES_V1):
  line, element ids, old, new, difference, unit, cause (required; empty refused), evidence (sheet + value), Checker
  verdict id or NONE. `change-add` appends one record (the file's earlier records are kept byte for byte; a changed or
  removed record is refused by check_append_only). Every VERIFIED_CHANGED row names its record or MISSING; a record
  whose verdict is NONE keeps the line STALE (out of VERIFIED); the diff writes the records still required.
5 SEALED GUARD by sha256 and project id (owner 19:45; research/agents_t168/SEALED_REGISTRY.json): every input file is
  hashed and refused when its sha256 is a sealed file's, whatever its name; the registry's names and
  engine/reference_mapping.py's are refused too; a line or manifest whose project id is a SEALED_PROJECT is refused.
6 TWO BASELINES (Lead 2026-10-22 04:20): with --baseline-a the same report also compares the after side element by
  element (floor, element id, item code, unit) with the released run A, whose project id may be absent but whose
  drawings must be pinned by the after side (or --new-revision-set).
7 Freelancer and benchmark totals are never an input: no parameter, threshold or expectation here comes from them.

The verdict JSON (GATE_B_DIFF_V2.json + GATE_B_DIFF_V2.csv; GATE_B_ELEMENT_DIFF_A.json with --baseline-a;
ESTABLISHED_QUANTITY_CHANGES_REQUIRED.json) names, for each side, its spec id, manifest sha256, BOQ_LINES sha256,
project id and identities. Summary status: REVIEW_REQUIRED when any row is VERIFIED_CHANGED, else CHECKS_COMPLETE.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import itertools
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import v30_gate_b as G1  # noqa: E402

DEFAULT_GUARD_CLASS = "TOOLING"        # T-212: a read-only check tool; it produces no quantity

SCHEMA = "URBAN_V30_GATE_B_DIFF_V2"
ELEMENT_SCHEMA = "URBAN_V30_GATE_B_ELEMENT_DIFF_V1"
CANDIDATE_MANIFEST_SCHEMA = "URBAN_CANDIDATE_MANIFEST_V1"
RELEASE_MANIFEST_SCHEMA = "URBAN_BASELINE_MANIFEST_V1"          # the T-165 baseline runner's MANIFEST_SCHEMA
CHANGES_SCHEMA = "URBAN_ESTABLISHED_QUANTITY_CHANGES_V1"
REQUIRED_SCHEMA = "URBAN_ESTABLISHED_QUANTITY_CHANGES_REQUIRED_V1"
SEALED_SCHEMA = "URBAN_SEALED_REGISTRY_V1"
V2_VERDICT_SCHEMA = "URBAN_CHECKER_VERDICT_V2"                  # tools/boq_export_v1.py
V2_SET_SCHEMA = "URBAN_CHECKER_VERDICT_V2_SET"
DEFAULT_SEALED_REGISTRY = ROOT / "research" / "agents_t168" / "SEALED_REGISTRY.json"
RELEASE_DEFAULT_PROJECT = "new project"   # tools/urban_boq_m9.py: the project id a run without --project writes
QTY_MATCH_TOL = 0.0005                    # tools/scoreboard_v2.py / tools/boq_export_v1.py
DISCREPANCY_REL = 0.01                    # WORKFLOW_CONTROLS s.1
FLAGS = G1.FLAGS + ("VERIFIED_CHANGED",)
QUANTITY_FIELDS = ("unit", "evidence_state", "gross", "deductions", "additions", "measured_net", "bounded_range")
REFUSAL_CODES = ("MANIFEST_MISSING", "MANIFEST_INVALID", "MANIFEST_MISMATCH", "PROJECT_MIX", "REVISION_MIX",
                 "DRAWING_MISMATCH", "SEALED", "VERDICTS_INVALID", "CHANGES_INVALID", "INPUT_INVALID")
SHA_RE = re.compile(r"^[0-9a-f]{64}$")
CSV_EXTRA = ("verified_by", "verdict_carry", "change_log", "scoreboard_tolerance_holds")


class Refused(Exception):
    """refused before anything is written; .problems = [(code, text)], .codes = the sorted codes."""

    def __init__(self, problems):
        self.problems = list(problems)
        self.codes = sorted({c for c, _ in self.problems})
        super().__init__("; ".join(f"{c}: {t}" for c, t in self.problems))


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def revision_set_sha256(shas):
    """tools/urban_boq_m9.py revision_set_sha256 over a list of drawing sha256s."""
    return sha256_bytes("|".join(sorted(shas)).encode("utf-8"))


def _canon(x):
    return json.dumps(x, sort_keys=True, ensure_ascii=False, default=str)


# ------------------------------------------------------------------------------------------------------ sealed guard
def load_sealed_registry(path=None):
    p = Path(path) if path else DEFAULT_SEALED_REGISTRY
    doc = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(doc, dict) or doc.get("schema") != SEALED_SCHEMA or not isinstance(doc.get("entries"), list):
        raise Refused([("INPUT_INVALID", f"{p.name} is not a {SEALED_SCHEMA}")])
    for e in doc["entries"]:
        if e.get("kind") not in ("SEALED_FILE", "SEALED_PROJECT") or not e.get("project_id"):
            raise Refused([("INPUT_INVALID", f"{p.name}: an entry needs kind SEALED_FILE / SEALED_PROJECT and project_id")])
        if e.get("sha256") is not None and not SHA_RE.match(str(e["sha256"])):
            raise Refused([("INPUT_INVALID", f"{p.name}: sha256 of {e.get('label')} is not 64 hex")])
    return doc


def _registry(registry):
    return registry if isinstance(registry, dict) else load_sealed_registry(registry)


def sealed_names(registry):
    from engine.reference_mapping import SEALED
    names = set(SEALED)
    for e in registry["entries"]:
        names.update(e.get("names") or ())
    return names


def guard_inputs(paths, registry=None):
    """{role: path} -> {role: sha256}; refused (SEALED) when a file's sha256 is a sealed file's (any name) or its name
    is a sealed name. The bytes are hashed only, never parsed here."""
    reg = _registry(registry)
    by_sha = {e["sha256"]: e for e in reg["entries"] if e.get("sha256")}
    names = sealed_names(reg)
    out, problems = {}, []
    for role, p in sorted(paths.items()):
        if p is None:
            continue
        p = Path(p)
        if p.name in names:
            problems.append(("SEALED", f"{role}: {p.name} is a sealed benchmark name (refused unopened)"))
            continue
        if not p.is_file():
            problems.append(("INPUT_INVALID", f"{role}: {p.name} is not a file"))
            continue
        s = sha256_file(p)
        if s in by_sha:
            e = by_sha[s]
            problems.append(("SEALED", f"{role}: {p.name} has the sha256 of the sealed {e.get('label')} (project "
                                       f"{e['project_id']}): refused whatever its name"))
            continue
        out[role] = s
    if problems:
        raise Refused(problems)
    return out


def guard_projects(project_ids, registry=None, where="input"):
    reg = _registry(registry)
    sealed = {e["project_id"] for e in reg["entries"] if e["kind"] == "SEALED_PROJECT"}
    hit = sorted(set(project_ids) & sealed)
    if hit:
        raise Refused([("SEALED", f"{where}: project id {h} is a sealed project (refused)") for h in hit])


# ------------------------------------------------------------------------------------------------------------ inputs
def read_lines(path):
    """(lines, sha256 of the file bytes): a BOQ_LINES.json list, or {"lines": [...]} as release runs may write."""
    b = Path(path).read_bytes()
    doc = json.loads(b.decode("utf-8"))
    lines = doc.get("lines") if isinstance(doc, dict) else doc
    if not isinstance(lines, list) or not all(isinstance(x, dict) and "line_id" in x for x in lines):
        raise Refused([("INPUT_INVALID", f"{Path(path).name}: not a list of canonical BOQ lines")])
    return lines, sha256_bytes(b)


def identities(lines):
    return sorted({(str((ln.get("project") or {}).get("project_id")),
                    str((ln.get("project") or {}).get("revision_set_sha256"))) for ln in lines})


def manifest_view(m, manifest_sha=None, side="side"):
    """one normalised view of a release or candidate manifest; refused (MANIFEST_INVALID) when it is neither."""
    if not isinstance(m, dict):
        raise Refused([("MANIFEST_INVALID", f"{side}: the manifest is not a JSON object")])
    if m.get("schema") == RELEASE_MANIFEST_SCHEMA:
        run = m.get("run") or {}
        problems = []
        if m.get("status") not in ("REPRODUCED", "RUN_NO_EXPECTED_FIGURES"):
            problems.append(("MANIFEST_INVALID", f"{side}: release run status {m.get('status')} (a baseline must have "
                                                 "run cleanly and, where figures are pinned, reproduced them)"))
        drawings = [{"role": i.get("role"), "file": i.get("file"), "size": i.get("size"), "sha256": i.get("sha256")}
                    for i in m.get("inputs") or ()]
        if not drawings:
            problems.append(("MANIFEST_INVALID", f"{side}: the release manifest pins no drawing"))
        if problems:
            raise Refused(problems)
        return {"kind": "RELEASE", "spec_id": m.get("baseline_id"), "spec_sha256": m.get("spec_sha256"),
                "manifest_sha256": manifest_sha, "project_id": m.get("project"),
                "line_labels": {RELEASE_DEFAULT_PROJECT if m.get("project") is None else m.get("project"),
                                RELEASE_DEFAULT_PROJECT},
                "aliases": {}, "drawings": drawings,
                "boq_lines_sha256": (run.get("outputs_sha256") or {}).get("BOQ_LINES.json"),
                "line_count": run.get("line_count"), "engine_commit": (m.get("engine") or {}).get("commit")}
    if m.get("schema") == CANDIDATE_MANIFEST_SCHEMA:
        need = ("candidate_version", "code_commit", "project_id", "drawings", "line_identities", "boq_lines_sha256",
                "line_count")
        miss = [k for k in need if m.get(k) in (None, "", [])]
        if miss:
            raise Refused([("MANIFEST_INVALID", f"{side}: candidate manifest without {', '.join(miss)}")])
        aliases = {(i["line_project_id"], i["revision_set_sha256"]) for i in m["line_identities"] if i.get("alias")}
        return {"kind": "CANDIDATE", "spec_id": m["candidate_version"], "spec_sha256": None,
                "manifest_sha256": manifest_sha, "project_id": m["project_id"], "line_labels": {m["project_id"]},
                "aliases": aliases, "drawings": list(m["drawings"]), "boq_lines_sha256": m["boq_lines_sha256"],
                "line_count": m["line_count"], "engine_commit": m["code_commit"]}
    raise Refused([("MANIFEST_INVALID", f"{side}: schema {m.get('schema')!r} is neither {RELEASE_MANIFEST_SCHEMA} nor "
                                        f"{CANDIDATE_MANIFEST_SCHEMA}")])


def derive_subset(rev, drawings):
    """the roles of the non-empty subset of drawings whose revision set is rev, or None."""
    for n in range(1, len(drawings) + 1):
        for combo in itertools.combinations(drawings, n):
            if revision_set_sha256([d["sha256"] for d in combo]) == rev:
                return sorted(str(d.get("role") or d.get("file")) for d in combo)
    return None


def check_side(lines, view=None, side="side", lines_sha=None, spec_sha=None, label_free=False):
    """the identity record of one side; raises Refused with every problem (sections 1-2 of the module text)."""
    ids = identities(lines)
    problems = []
    if view is None:
        if len({p for p, _ in ids}) > 1:
            problems.append(("PROJECT_MIX", f"{side}: lines of {len({p for p, _ in ids})} project ids "
                                            f"{sorted({p for p, _ in ids})}: one side is one project"))
        if len({r for _, r in ids}) > 1:
            problems.append(("REVISION_MIX", f"{side}: lines of {len({r for _, r in ids})} revision sets and no "
                                             "manifest pins the drawings they come from"))
        if problems:
            raise Refused(problems)
        return {"identities": [{"line_project_id": p, "revision_set_sha256": r, "drawing_roles": None,
                                "alias": False} for p, r in ids], "project_id": ids[0][0] if ids else None}
    if lines_sha is not None and view["boq_lines_sha256"] != lines_sha:
        problems.append(("MANIFEST_MISMATCH", f"{side}: the lines file sha256 {lines_sha[:12]} is not the manifest's "
                                              f"BOQ_LINES sha256 {str(view['boq_lines_sha256'])[:12]}"))
    if view["line_count"] != len(lines):
        problems.append(("MANIFEST_MISMATCH", f"{side}: {len(lines)} lines, the manifest says {view['line_count']}"))
    if spec_sha is not None and spec_sha != view["spec_sha256"]:
        problems.append(("MANIFEST_MISMATCH", f"{side}: the spec file sha256 {spec_sha[:12]} is not the manifest's "
                                              f"spec_sha256 {str(view['spec_sha256'])[:12]}"))
    out = []
    for p, r in ids:
        roles = derive_subset(r, view["drawings"])
        if roles is None:
            problems.append(("REVISION_MIX", f"{side}: revision set {r[:12]} (project label {p}) is not the revision "
                                             "set of any drawing the manifest pins"))
            continue
        alias = (p, r) in view["aliases"]
        if not label_free and p not in view["line_labels"] and not alias:
            problems.append(("PROJECT_MIX", f"{side}: project id {p} is not the manifest's project "
                                            f"{view['project_id']} nor a route label it declares"))
            continue
        out.append({"line_project_id": p, "revision_set_sha256": r, "drawing_roles": roles,
                    "alias": bool(alias or p != view["project_id"])})
    if problems:
        raise Refused(problems)
    return {"identities": out, "project_id": view["project_id"]}


def drawing_conflicts(views, new_revision_set=False):
    """the same drawing role or file name pinned with two sha256s by two sides -> DRAWING_MISMATCH problems."""
    problems, changes = [], []
    named = [(s, v) for s, v in views if v is not None]
    for (sa, va), (sb, vb) in itertools.combinations(named, 2):
        for da in va["drawings"]:
            for db in vb["drawings"]:
                same = (da.get("role") and da.get("role") == db.get("role")) or \
                       (da.get("file") and da.get("file") == db.get("file"))
                if same and da["sha256"] != db["sha256"]:
                    txt = (f"{sa} pins {da.get('role')} {da.get('file')} {str(da['sha256'])[:12]}, {sb} pins "
                           f"{db.get('role')} {db.get('file')} {str(db['sha256'])[:12]}")
                    (changes if new_revision_set else problems).append(txt)
    return [("DRAWING_MISMATCH", t + " (pass --new-revision-set for a re-measure on a new drawing revision)")
            for t in problems], changes


# ---------------------------------------------------------------------------------------------------------- verdicts
def validate_verdicts(doc):
    from tools import boq_export_v1 as EX
    if isinstance(doc, list):
        doc = {"schema": V2_SET_SCHEMA, "verdicts": doc}
    p = EX.validate_v2_set(doc)
    if p:
        raise Refused([("VERDICTS_INVALID", x) for x in p])
    return doc["verdicts"]


def bind(v, lines_by_id, ident_pairs, spec_id, lines_sha):
    """status of one V2 record against one side: COUNTED, or why not (the tools/boq_export_v1.py rules, any scope)."""
    if (v["project_id"], v["revision_set_sha256"]) not in ident_pairs or v["candidate_version"] != spec_id or \
            v["boq_lines_sha256"] != lines_sha:
        return "NOT_THIS_SIDE"
    lines = [lines_by_id.get(i) for i in v["line_ids"]]
    if any(x is None for x in lines):
        return "STALE"
    if any(x["unit"] != v["unit"] for x in lines):
        return "STALE"
    if sorted(str(x) for x in v["element_scope"]["ids"]) != sorted(str(x["location"]["element_id"]) for x in lines):
        return "SCOPE_DIFFERS"
    if any(x["evidence_state"] not in G1.QUANTITY_STATES + ("NOT_APPLICABLE_WITH_EVIDENCE",) for x in lines):
        return "LINE_NOT_MEASURED"
    eq = sum(float(x["measured_net"] or 0.0) for x in lines)
    if abs(float(v["engine_qty"]) - eq) > QTY_MATCH_TOL:
        return "STALE"
    cq = float(v["checker_qty"])
    if (eq == 0 and abs(cq) > QTY_MATCH_TOL) or (eq != 0 and abs(cq - eq) / abs(eq) > DISCREPANCY_REL):
        return "DISCREPANCY"
    return "COUNTED"


def quantity_key(ln):
    return _canon([ln.get(k) for k in QUANTITY_FIELDS] + [(ln.get("location") or {}).get("element_id"),
                                                           (ln.get("project") or {}).get("project_id"),
                                                           (ln.get("project") or {}).get("revision_set_sha256")])


# ------------------------------------------------------------------------------------------------------- change log
def change_problems(rec):
    p = []
    if not isinstance(rec, dict):
        return ["record: not an object"]
    for k in ("line_id", "unit", "checker_verdict"):
        if not (isinstance(rec.get(k), str) and rec[k].strip()):
            p.append(f"{k}: required text")
    if not (isinstance(rec.get("cause"), str) and rec["cause"].strip()):
        p.append("cause: required (an empty cause is refused)")
    els = rec.get("element_ids")
    if not (isinstance(els, list) and els and all(isinstance(x, str) and x for x in els)):
        p.append("element_ids: a non-empty list of element id texts")
    for k in ("old", "new"):
        if k not in rec or not (rec[k] is None or (isinstance(rec[k], (int, float)) and not isinstance(rec[k], bool))):
            p.append(f"{k}: a number, or null for a held quantity (never 0 for held)")
    ev = rec.get("evidence")
    if not (isinstance(ev, list) and ev and all(isinstance(e, dict) and str(e.get("sheet") or "").strip()
                                                and str(e.get("value") or "").strip() for e in ev)):
        p.append("evidence: every entry names its sheet and the value read there")
    return p


def _difference(old, new):
    return None if old is None or new is None else round(float(new) - float(old), 6)


def new_change(rec, seq):
    """the stored form: sorted keys, the difference computed (never typed), an id from the content."""
    p = change_problems(rec)
    if p:
        raise Refused([("CHANGES_INVALID", x) for x in p])
    out = {"seq": seq, "line_id": rec["line_id"], "element_ids": sorted(rec["element_ids"]), "unit": rec["unit"],
           "old": rec["old"], "new": rec["new"], "difference": _difference(rec["old"], rec["new"]),
           "cause": rec["cause"].strip(), "evidence": [dict(sorted(e.items())) for e in rec["evidence"]],
           "checker_verdict": rec["checker_verdict"].strip()}
    if rec.get("time"):
        out["time"] = rec["time"]
    out["change_id"] = "CH-" + sha256_bytes(_canon(out).encode("utf-8"))[:16]
    return dict(sorted(out.items()))


def validate_changes(doc, candidate_version=None, project_id=None):
    p = []
    if not isinstance(doc, dict) or doc.get("schema") != CHANGES_SCHEMA or not isinstance(doc.get("changes"), list):
        return [f"not a {CHANGES_SCHEMA}"]
    for k, want in (("candidate_version", candidate_version), ("project_id", project_id)):
        if not (isinstance(doc.get(k), str) and doc[k]):
            p.append(f"{k}: required")
        elif want is not None and doc[k] != want:
            p.append(f"{k} {doc[k]} is not {want}")
    seen = set()
    for i, c in enumerate(doc["changes"]):
        cid = c.get("change_id") if isinstance(c, dict) else None
        p += [f"{cid or i}: {x}" for x in change_problems(c)]
        if isinstance(c, dict):
            if c.get("seq") != i + 1:
                p.append(f"{cid or i}: seq {c.get('seq')} is not {i + 1} (append-only order)")
            if c.get("difference") != _difference(c.get("old"), c.get("new")):
                p.append(f"{cid or i}: difference is not new - old")
            body = {k: v for k, v in c.items() if k != "change_id"}
            if cid != "CH-" + sha256_bytes(_canon(body).encode("utf-8"))[:16]:
                p.append(f"{cid or i}: change_id does not match the record (edited after it was written)")
            if cid in seen:
                p.append(f"{cid}: listed twice")
            seen.add(cid)
    return p


def check_append_only(old_doc, new_doc):
    """problems when new_doc does not keep every record of old_doc unchanged and in place (append-only)."""
    p = []
    old, new = old_doc.get("changes") or [], new_doc.get("changes") or []
    for k in ("schema", "candidate_version", "project_id"):
        if old_doc.get(k) != new_doc.get(k):
            p.append(f"{k} changed")
    if len(new) < len(old):
        p.append(f"{len(old) - len(new)} record(s) removed")
    for a, b in zip(old, new):
        if _canon(a) != _canon(b):
            p.append(f"record {a.get('change_id')} changed or moved")
    return p


def changes_append(path, rec, *, candidate_version, project_id):
    """append one record to an ESTABLISHED_QUANTITY_CHANGES file (created when absent); -> the new document."""
    path = Path(path)
    if path.exists():
        doc = json.loads(path.read_text(encoding="utf-8"))
        p = validate_changes(doc, candidate_version, project_id)
        if p:
            raise Refused([("CHANGES_INVALID", f"{path.name}: {x}") for x in p])
    else:
        doc = {"schema": CHANGES_SCHEMA, "candidate_version": candidate_version, "project_id": project_id,
               "changes": []}
    new = {**doc, "changes": doc["changes"] + [new_change(rec, len(doc["changes"]) + 1)]}
    p = check_append_only(doc, new) + validate_changes(new, candidate_version, project_id)
    if p:
        raise Refused([("CHANGES_INVALID", x) for x in p])
    path.write_text(json.dumps(new, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return new


# ------------------------------------------------------------------------------------------------------------- diff
def _summary(rows, base_summary):
    caught = Counter(x for r in rows for x in r["flags"])
    only = Counter(r["flags"][0] for r in rows if len(r["flags"]) == 1)
    on_changed = Counter(x for r in rows if r["changed"] for x in r["flags"])
    s = dict(base_summary)
    s.update({"flagged": sum(1 for r in rows if r["flags"]), "unflagged": sum(1 for r in rows if not r["flags"]),
              "changed_rows_unflagged": sum(1 for r in rows if r["changed"] and not r["flags"]),
              "per_rule": {x: {"caught": caught.get(x, 0), "only_this_rule": only.get(x, 0),
                               "caught_on_changed": on_changed.get(x, 0)} for x in FLAGS}})
    return s


def diff(before, after, *, before_manifest=None, after_manifest=None, before_meta=None, after_meta=None,
         before_sha=None, after_sha=None, before_spec_sha=None, after_spec_sha=None, require_manifests=True,
         verdicts=None, changes=None, register=None, ledgers=None, baseline_a=None, baseline_a_manifest=None,
         baseline_a_sha=None, new_revision_set=False, sealed_registry=None):
    """-> the v2 diff document; raises Refused (every problem found) before anything is computed.
    before_meta / after_meta ({"spec_id", "boq_lines_sha256"}) name a side when no manifest is given (library use and
    tests); the CLI always gives manifests (require_manifests)."""
    reg = _registry(sealed_registry)
    problems = []
    views = {}
    for side, m, msha in (("before", before_manifest, None), ("after", after_manifest, None)):
        if m is None:
            if require_manifests:
                problems.append(("MANIFEST_MISSING", f"{side}: no manifest names this side (a Gate B diff is made "
                                                     "only against a pinned, named run)"))
            views[side] = None
            continue
        try:
            views[side] = manifest_view(m[0] if isinstance(m, tuple) else m,
                                        m[1] if isinstance(m, tuple) else None, side)
        except Refused as ex:
            problems += ex.problems
            views[side] = None
    view_a = None
    if baseline_a is not None:
        if baseline_a_manifest is None and require_manifests:
            problems.append(("MANIFEST_MISSING", "baseline A: no manifest names the released run"))
        elif baseline_a_manifest is not None:
            try:
                m = baseline_a_manifest
                view_a = manifest_view(m[0] if isinstance(m, tuple) else m, m[1] if isinstance(m, tuple) else None,
                                       "baseline A")
            except Refused as ex:
                problems += ex.problems
    if problems:
        raise Refused(problems)
    sides = {}
    for side, lines, sha, spec_sha in (("before", before, before_sha, before_spec_sha),
                                       ("after", after, after_sha, after_spec_sha)):
        try:
            sides[side] = check_side(lines, views[side], side, sha, spec_sha)
        except Refused as ex:
            problems += ex.problems
    ident_a = None
    if baseline_a is not None:
        try:
            ident_a = check_side(baseline_a, view_a, "baseline A", baseline_a_sha, None, label_free=True)
        except Refused as ex:
            problems += ex.problems
    if problems:
        raise Refused(problems)
    pb, pa = sides["before"]["project_id"], sides["after"]["project_id"]
    if pb != pa:
        problems.append(("PROJECT_MIX", f"before is project {pb}, after is project {pa}: one diff, one project"))
    if view_a is not None and view_a["project_id"] is not None and view_a["project_id"] != pa:
        problems.append(("PROJECT_MIX", f"baseline A is project {view_a['project_id']}, after is {pa}"))
    dprob, dchanges = drawing_conflicts([("before", views["before"]), ("after", views["after"]),
                                         ("baseline A", view_a)], new_revision_set)
    problems += dprob
    if view_a is not None and views["after"] is not None and not new_revision_set:
        pinned = {d["sha256"] for d in views["after"]["drawings"]}
        for d in view_a["drawings"]:
            if d["sha256"] not in pinned:
                problems.append(("DRAWING_MISMATCH", f"baseline A drawing {d.get('role')} {str(d['sha256'])[:12]} is "
                                                     "not pinned by the after side"))
    try:
        guard_projects({p for p, _ in identities(before) + identities(after) + identities(baseline_a or [])}
                       | {x for x in (pb, pa) if x}, reg, "lines / manifests")
    except Refused as ex:
        problems += ex.problems
    vlist = []
    if verdicts is not None:
        try:
            vlist = validate_verdicts(verdicts)
        except Refused as ex:
            problems += ex.problems
    if changes is not None:
        p = validate_changes(changes, (after_meta or {}).get("spec_id") or (views["after"] or {}).get("spec_id"), pa)
        problems += [("CHANGES_INVALID", x) for x in p]
    if problems:
        raise Refused(problems)

    doc = G1.diff(before, after, register=register, ledgers=ledgers)
    bmeta = {"spec_id": (views["before"] or {}).get("spec_id"), "boq_lines_sha256": before_sha}
    bmeta.update({k: v for k, v in (before_meta or {}).items() if v is not None})
    ameta = {"spec_id": (views["after"] or {}).get("spec_id"), "boq_lines_sha256": after_sha}
    ameta.update({k: v for k, v in (after_meta or {}).items() if v is not None})
    B = {x["line_id"]: x for x in before}
    A = {x["line_id"]: x for x in after}
    bpairs = {(i["line_project_id"], i["revision_set_sha256"]) for i in sides["before"]["identities"]}
    apairs = {(i["line_project_id"], i["revision_set_sha256"]) for i in sides["after"]["identities"]}
    vstat = []
    counted_before = {}                    # before line id -> [verdict ids]
    counted_after = {}                     # after line id -> [verdict ids]
    for v in vlist:
        sb = bind(v, B, bpairs, bmeta["spec_id"], bmeta["boq_lines_sha256"])
        sa = bind(v, A, apairs, ameta["spec_id"], ameta["boq_lines_sha256"])
        vstat.append({"verdict_id": v["verdict_id"], "scope": v["scope"], "line_ids": v["line_ids"],
                      "before": sb, "after": sa})
        if sb == "COUNTED":
            for i in v["line_ids"]:
                counted_before.setdefault(i, []).append(v["verdict_id"])
        if sa == "COUNTED":
            for i in v["line_ids"]:
                counted_after.setdefault(i, []).append(v["verdict_id"])
    log = {}
    for c in (changes or {}).get("changes") or ():
        log.setdefault(c["line_id"], []).append(c)
    stale_verdicts = set()
    for r in doc["rows"]:
        bid, aid = r["before_line_id"], r["after_line_id"]
        r.update({"verified_by": counted_before.get(bid, []) if bid else [], "verdict_carry": None,
                  "change_log": None, "scoreboard_tolerance_holds": None})
        if not r["verified_by"]:
            continue
        b, a = B[bid], A.get(aid) if aid else None
        if a is not None and quantity_key(a) == quantity_key(b):
            r["verdict_carry"] = "CARRIED"
            continue
        stale_verdicts.update(r["verified_by"])
        r["flags"] = [x for x in FLAGS if x in set(r["flags"]) | {"VERIFIED_CHANGED"}]
        if a is not None and a.get("measured_net") is not None and b.get("measured_net") is not None:
            r["scoreboard_tolerance_holds"] = abs(float(a["measured_net"]) - float(b["measured_net"])) <= QTY_MATCH_TOL
        recs = log.get(aid or bid) or []
        r["change_log"] = recs[-1]["change_id"] if recs else "MISSING"
        rever = [x for x in counted_after.get(aid, []) if aid] if aid else []
        cited = [c["checker_verdict"] for c in recs if c["checker_verdict"] != "NONE"]
        r["verdict_carry"] = "REVERIFIED" if any(x in rever for x in cited) else "STALE"
    for r in doc["rows"]:                  # a verdict is stale as a whole: its unchanged lines leave VERIFIED too
        if r["verdict_carry"] == "CARRIED" and set(r["verified_by"]) & stale_verdicts:
            r["verdict_carry"] = "STALE_WITH_VERDICT"
    for s in vstat:
        s["carry"] = (None if s["before"] != "COUNTED" else
                      "STALE" if s["verdict_id"] in stale_verdicts else "CARRIED")
    vc = [r for r in doc["rows"] if "VERIFIED_CHANGED" in r["flags"]]
    unlogged = [r for r in vc if r["change_log"] == "MISSING"]
    summary = _summary(doc["rows"], doc["summary"])
    summary.update({"verified_changed": len(vc), "verified_changed_unlogged": len(unlogged),
                    "verdicts_given": len(vlist), "verdicts_counted_before": sum(1 for s in vstat
                                                                                if s["before"] == "COUNTED"),
                    "verdicts_carried": sum(1 for s in vstat if s["carry"] == "CARRIED"),
                    "verdicts_stale": sum(1 for s in vstat if s["carry"] == "STALE"),
                    "changes_given": len((changes or {}).get("changes") or ()),
                    "revision_changes": dchanges,
                    "status": "REVIEW_REQUIRED" if vc else "CHECKS_COMPLETE"})
    doc["schema"] = SCHEMA
    doc["summary"] = summary
    doc["verdicts"] = vstat
    doc["changes_required"] = {
        "schema": REQUIRED_SCHEMA, "candidate_version": ameta.get("spec_id"), "project_id": pa,
        "rule": "one record per VERIFIED_CHANGED row without a change-log record: cause and evidence are the "
                "author's to write (change-add); a change without a new Checker verdict keeps the line out of VERIFIED",
        "rows": [{"line_id": r["after_line_id"] or r["before_line_id"], "element_ids": [r["element_id"]],
                  "unit": r["unit"], "old": r["before"]["value"], "new": r["after"]["value"],
                  "difference": r["delta"], "verified_by": r["verified_by"]} for r in unlogged]}
    doc["sides"] = {}
    for side, view, meta, ident in (("before", views["before"], bmeta, sides["before"]),
                                    ("after", views["after"], ameta, sides["after"])):
        doc["sides"][side] = {"kind": (view or {}).get("kind", "UNPINNED"), "spec_id": meta.get("spec_id"),
                              "manifest_sha256": (view or {}).get("manifest_sha256"),
                              "boq_lines_sha256": meta.get("boq_lines_sha256"),
                              "project_id": ident["project_id"], "identities": ident["identities"],
                              "drawings": (view or {}).get("drawings"),
                              "engine_commit": (view or {}).get("engine_commit")}
    if baseline_a is not None:
        doc["element_diff_a"] = element_diff(baseline_a, after)
        doc["sides"]["baseline_a"] = {"kind": (view_a or {}).get("kind", "UNPINNED"),
                                      "spec_id": (view_a or {}).get("spec_id"),
                                      "manifest_sha256": (view_a or {}).get("manifest_sha256"),
                                      "boq_lines_sha256": baseline_a_sha,
                                      "project_id": (view_a or {}).get("project_id"),
                                      "identities": ident_a["identities"], "drawings": (view_a or {}).get("drawings")}
    return doc


# ------------------------------------------------------------------------------------------- element diff (run A)
def _element_groups(lines):
    g = {}
    no_el = 0
    for ln in lines:
        loc = ln.get("location") or {}
        if loc.get("element_id") is None:
            no_el += 1
            continue
        k = (str(loc.get("floor")), str(loc["element_id"]), ln["item_code"], ln["unit"])
        o = g.setdefault(k, {"lines": 0, "qty_lines": 0, "qty": 0.0, "held_lines": 0, "low": None, "high": None,
                             "excluded_lines": 0})
        o["lines"] += 1
        st = ln["evidence_state"]
        if st in G1.QUANTITY_STATES and ln.get("measured_net") is not None:
            o["qty_lines"] += 1
            o["qty"] += float(ln["measured_net"])
        elif st in ("EXCLUDED_WITH_REASON", "NOT_APPLICABLE_WITH_EVIDENCE"):
            o["excluded_lines"] += 1
        else:
            o["held_lines"] += 1
            br = ln.get("bounded_range") or {}
            if br.get("low") is not None and br.get("high") is not None:
                o["low"] = (o["low"] or 0.0) + float(br["low"])
                o["high"] = (o["high"] or 0.0) + float(br["high"])
    for o in g.values():
        o["qty"] = round(o["qty"], 6) if o["qty_lines"] else None
        for k in ("low", "high"):
            o[k] = None if o[k] is None else round(o[k], 6)
    return g, no_el


def element_diff(a_lines, after_lines, move_pct=G1.MOVE_PCT):
    """element by element (floor, element id, item code, unit) against the released run A: SAME, CHANGED (with
    MOVED_5PCT at the T-156 threshold), STATE_CHANGE (quantity <-> held: never compared as 0), NEW, DROPPED.
    Lines without an element id cannot be paired by element and are only counted."""
    ga, na = _element_groups(a_lines)
    gb, nb = _element_groups(after_lines)
    rows = []
    for k in sorted(set(ga) | set(gb)):
        a, b = ga.get(k), gb.get(k)
        delta = pct = None
        flags = []
        if a and b:
            if (a["qty"] is None) != (b["qty"] is None) or (a["low"], a["high"]) != (b["low"], b["high"]) \
                    or (a["held_lines"] > 0) != (b["held_lines"] > 0):
                status = "STATE_CHANGE"
            elif a["qty"] == b["qty"]:
                status = "SAME"
            else:
                status = "CHANGED"
            if a["qty"] is not None and b["qty"] is not None:
                delta = round(b["qty"] - a["qty"], 6)
                if a["qty"] != 0:
                    pct = round(100.0 * delta / a["qty"], 4)
                if (pct is not None and G1._at_least(abs(pct), move_pct)) or (a["qty"] == 0 and b["qty"] != 0):
                    flags.append("MOVED_5PCT")
        else:
            status = "NEW" if b else "DROPPED"
        rows.append({"floor": k[0], "element_id": k[1], "item_code": k[2], "unit": k[3], "status": status,
                     "a": a, "after": b, "delta": delta, "delta_pct": pct, "flags": flags})
    st = Counter(r["status"] for r in rows)
    return {"schema": ELEMENT_SCHEMA, "rows": rows,
            "summary": {"elements": len(rows), "by_status": dict(sorted(st.items())),
                        "moved_5pct": sum(1 for r in rows if r["flags"]),
                        "lines_without_element_id": {"a": na, "after": nb}}}


# ------------------------------------------------------------------------------------------- candidate manifest
def per_code(lines):
    """one figure set per (item code, unit), the T-165 manifest's per_code figures (that runner is imported by nothing,
    its test pins it, so the same rule is written here): released = MEASURED / SOURCE_DERIVED / PROVISIONAL with a
    measured_net; held carries no quantity (bounded low / high only where the line gives both); null, never 0."""
    acc = {}
    for ln in lines:
        k = (ln["item_code"], ln["unit"])
        o = acc.setdefault(k, {"item_code": k[0], "unit": k[1], "lines": 0, "released_lines": 0, "released_qty": 0.0,
                               "held_lines": 0, "held_bounded_lines": 0, "held_low": 0.0, "held_high": 0.0,
                               "excluded_lines": 0, "states": {}})
        o["lines"] += 1
        s = ln.get("evidence_state")
        o["states"][s] = o["states"].get(s, 0) + 1
        if s in G1.QUANTITY_STATES and ln.get("measured_net") is not None:
            o["released_lines"] += 1
            o["released_qty"] += ln["measured_net"]
        elif s in ("EXCLUDED_WITH_REASON", "NOT_APPLICABLE_WITH_EVIDENCE"):
            o["excluded_lines"] += 1
        else:
            o["held_lines"] += 1
            b = ln.get("bounded_range") or {}
            if b.get("low") is not None and b.get("high") is not None:
                o["held_bounded_lines"] += 1
                o["held_low"] += b["low"]
                o["held_high"] += b["high"]
    out = []
    for k in sorted(acc):
        o = acc[k]
        o["released_qty"] = round(o["released_qty"], 3) if o["released_lines"] else None
        if o["held_bounded_lines"]:
            o["held_low"], o["held_high"] = round(o["held_low"], 3), round(o["held_high"], 3)
        else:
            o["held_low"] = o["held_high"] = None
        o["held_unbounded_lines"] = o["held_lines"] - o["held_bounded_lines"]
        o["states"] = dict(sorted(o["states"].items()))
        out.append(o)
    return out


def register_basis(path):
    """the document-register revision basis (T-195 REGISTER csv: sheet_key, revision_basis): counts + per sheet."""
    text = Path(path).read_text(encoding="utf-8")
    rows = list(csv.DictReader(io.StringIO(text)))
    if not rows or "sheet_key" not in rows[0] or "revision_basis" not in rows[0]:
        raise Refused([("INPUT_INVALID", f"{Path(path).name}: a document register needs sheet_key and revision_basis")])
    sheets = sorted([r["sheet_key"], r["revision_basis"]] for r in rows)
    return {"file": Path(path).name, "sha256": sha256_file(path),
            "revision_basis": dict(sorted(Counter(b for _, b in sheets).items())), "sheets": sheets}


def build_candidate_manifest(lines, lines_sha, *, candidate_version, code_commit, project_id, drawings,
                             document_register=None, verdicts=None, verdicts_sha=None, sealed_registry=None):
    """-> URBAN_CANDIDATE_MANIFEST_V1 (owner 19:00 (5) / 19:45). drawings = [{role, file, size, sha256}] (hashes only;
    the drawings stay private). Refused: no drawing, a role twice, a line identity no pinned drawing subset gives
    (REVISION_MIX), a sealed project id."""
    reg = _registry(sealed_registry)
    problems = []
    if not drawings:
        problems.append(("MANIFEST_INVALID", "a candidate manifest pins at least one drawing"))
    roles = [d["role"] for d in drawings]
    if len(set(roles)) != len(roles):
        problems.append(("MANIFEST_INVALID", "a drawing role listed twice"))
    if not (isinstance(project_id, str) and project_id.strip()):
        problems.append(("MANIFEST_INVALID", "project id required"))
    if problems:
        raise Refused(problems)
    guard_projects({project_id} | {p for p, _ in identities(lines)}, reg, "candidate")
    ids = []
    for p, r in identities(lines):
        sub = derive_subset(r, drawings)
        if sub is None:
            problems.append(("REVISION_MIX", f"revision set {r[:12]} (label {p}) is not the revision set of any "
                                             "subset of the given drawings"))
            continue
        ids.append({"line_project_id": p, "revision_set_sha256": r, "drawing_roles": sub,
                    "alias": p != project_id})
    if problems:
        raise Refused(problems)
    vrec = None
    lstat = defaultdict(list)
    if verdicts is not None:
        vl = validate_verdicts(verdicts)
        by_id = {x["line_id"]: x for x in lines}
        pairs = {(i["line_project_id"], i["revision_set_sha256"]) for i in ids}
        recs = []
        for v in vl:
            s = bind(v, by_id, pairs, candidate_version, lines_sha)
            recs.append({"verdict_id": v["verdict_id"], "scope": v["scope"], "status": s})
            for i in v["line_ids"]:
                if i in by_id:
                    lstat[i].append([v["verdict_id"], s])
        vrec = {"sha256": verdicts_sha, "records": sorted(recs, key=lambda x: x["verdict_id"])}
    st = Counter(x["evidence_state"] for x in lines)
    lines_out = []
    for x in sorted(lines, key=lambda x: x["line_id"]):
        br = x.get("bounded_range") or {}
        q = x["evidence_state"] in G1.QUANTITY_STATES
        lines_out.append({"line_id": x["line_id"], "item_code": x["item_code"], "unit": x["unit"],
                          "element_id": (x.get("location") or {}).get("element_id"), "state": x["evidence_state"],
                          "measured_net": x.get("measured_net") if q else None,
                          "low": br.get("low") if not q else None, "high": br.get("high") if not q else None,
                          "quantity_key_sha256": sha256_bytes(quantity_key(x).encode("utf-8")),
                          "verdicts": sorted(lstat.get(x["line_id"], [])),
                          "verification": "COUNTED" if any(s == "COUNTED" for _, s in lstat.get(x["line_id"], []))
                          else "NONE"})
    return {"schema": CANDIDATE_MANIFEST_SCHEMA, "candidate_version": candidate_version, "code_commit": code_commit,
            "project_id": project_id,
            "revision_set_sha256": revision_set_sha256([d["sha256"] for d in drawings]),
            "drawings": sorted(({"role": d["role"], "file": d["file"], "size": d.get("size"), "sha256": d["sha256"]}
                                for d in drawings), key=lambda d: d["role"]),
            "line_identities": ids, "document_register": document_register,
            "boq_lines_sha256": lines_sha, "line_count": len(lines),
            "evidence_states": dict(sorted(st.items())), "baseline_quantities": per_code(lines),
            "verdicts": vrec, "lines": lines_out,
            "rule": "identity by drawing sha256 (every line identity is the revision set of a subset of the pinned "
                    "drawings), never by file name; quantities are the candidate's own, held lines carry no "
                    "quantity (null, never 0); a verdict counts only bound to this candidate (verification COUNTED)"}


# ------------------------------------------------------------------------------------------------------------ output
def to_csv(doc):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(G1.CSV_FIELDS) + list(CSV_EXTRA), lineterminator="\n")
    w.writeheader()
    base = list(csv.DictReader(io.StringIO(G1.to_csv(doc))))
    for r, b in zip(doc["rows"], base):
        b.update({"verified_by": " ".join(r["verified_by"]), "verdict_carry": r["verdict_carry"] or "",
                  "change_log": r["change_log"] or "",
                  "scoreboard_tolerance_holds": "" if r["scoreboard_tolerance_holds"] is None
                  else str(r["scoreboard_tolerance_holds"])})
        w.writerow(b)
    return buf.getvalue()


def _dump(obj):
    return json.dumps(obj, indent=1, sort_keys=True, ensure_ascii=False) + "\n"


def write(out, doc):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    files = {"GATE_B_DIFF_V2.json": _dump({k: v for k, v in doc.items() if k != "element_diff_a"}),
             "GATE_B_DIFF_V2.csv": to_csv(doc),
             "ESTABLISHED_QUANTITY_CHANGES_REQUIRED.json": _dump(doc["changes_required"])}
    if "element_diff_a" in doc:
        files["GATE_B_ELEMENT_DIFF_A.json"] = _dump(doc["element_diff_a"])
    for n, t in files.items():
        (out / n).write_text(t, encoding="utf-8")
    return sorted(files)


def _load(path):
    b = Path(path).read_bytes()
    return json.loads(b.decode("utf-8")), sha256_bytes(b)


def _parse_kv(items, what):
    out = []
    for x in items or ():
        if "=" not in x:
            raise Refused([("INPUT_INVALID", f"{what} {x!r}: write NAME=VALUE")])
        k, v = x.split("=", 1)
        out.append((k.strip(), v.strip()))
    return out


def _qty(x):
    return None if x.strip().upper() == "HELD" else float(x)


def main_diff(a):
    roles = {"before": a.before, "after": a.after, "before_manifest": a.before_manifest,
             "after_manifest": a.after_manifest, "before_spec": a.before_spec, "after_spec": a.after_spec,
             "baseline_a": a.baseline_a, "baseline_a_manifest": a.baseline_a_manifest, "verdicts": a.verdicts,
             "changes": a.changes, "register": a.register}
    roles.update({f"ledger_{i}": p for i, p in enumerate(a.ledger)})
    reg = load_sealed_registry(a.sealed_registry)
    shas = guard_inputs(roles, reg)
    before, bsha = read_lines(a.before)
    after, asha = read_lines(a.after)
    bm = (_load(a.before_manifest)) if a.before_manifest else None
    am = (_load(a.after_manifest)) if a.after_manifest else None
    base_a = read_lines(a.baseline_a) if a.baseline_a else (None, None)
    am_a = _load(a.baseline_a_manifest) if a.baseline_a_manifest else None
    verd = _load(a.verdicts)[0] if a.verdicts else None
    chg = _load(a.changes)[0] if a.changes else None
    regd = _load(a.register)[0] if a.register else None
    leds = [_load(x)[0] for x in a.ledger]
    doc = diff(before, after, before_manifest=bm, after_manifest=am, before_sha=bsha, after_sha=asha,
               before_spec_sha=shas.get("before_spec"), after_spec_sha=shas.get("after_spec"), verdicts=verd,
               changes=chg, register=regd, ledgers=leds, baseline_a=base_a[0], baseline_a_manifest=am_a,
               baseline_a_sha=base_a[1], new_revision_set=a.new_revision_set, sealed_registry=reg)
    doc["inputs_sha256"] = dict(sorted(shas.items()))
    if a.sha:
        doc["random_picks"] = G1.pick(G1.remaining(doc), a.sha)
    files = write(a.out, doc)
    print(json.dumps({"sides": {k: {x: v.get(x) for x in ("kind", "spec_id", "manifest_sha256", "boq_lines_sha256",
                                                              "project_id")} for k, v in doc["sides"].items()},
                      "summary": {k: doc["summary"][k] for k in ("rows", "changed_rows", "changed_rows_unflagged",
                                                                  "verified_changed", "verified_changed_unlogged",
                                                                  "status")},
                      "element_diff_a": (doc.get("element_diff_a") or {}).get("summary"),
                      "random_picks": doc.get("random_picks"), "files": files}, indent=1, sort_keys=True))
    return 0


def main_manifest(a):
    reg = load_sealed_registry(a.sealed_registry)
    dr = _parse_kv(a.drawing, "--drawing")
    roles = {"lines": a.lines, "verdicts": a.verdicts, "document_register": a.document_register}
    roles.update({f"drawing:{k}": v for k, v in dr})
    shas = guard_inputs(roles, reg)
    lines, lsha = read_lines(a.lines)
    drawings = [{"role": k, "file": Path(v).name, "size": Path(v).stat().st_size, "sha256": shas[f"drawing:{k}"]}
                for k, v in dr]
    m = build_candidate_manifest(lines, lsha, candidate_version=a.candidate_version, code_commit=a.code_commit,
                                 project_id=a.project_id, drawings=drawings,
                                 document_register=register_basis(a.document_register) if a.document_register
                                 else None, verdicts=_load(a.verdicts)[0] if a.verdicts else None,
                                 verdicts_sha=shas.get("verdicts"), sealed_registry=reg)
    Path(a.out).write_text(_dump(m), encoding="utf-8")
    print(f"{m['candidate_version']}: {m['line_count']} lines, {len(m['line_identities'])} line identities "
          f"({sum(1 for i in m['line_identities'] if i['alias'])} route labels), revision set "
          f"{m['revision_set_sha256'][:12]}, BOQ_LINES {lsha[:12]} -> {a.out}")
    return 0


def main_change_add(a):
    load_sealed_registry(a.sealed_registry)
    rec = {"line_id": a.line_id, "element_ids": a.element_id, "unit": a.unit, "old": _qty(a.old), "new": _qty(a.new),
           "cause": a.cause, "evidence": [{"sheet": k, "value": v} for k, v in _parse_kv(a.evidence, "--evidence")],
           "checker_verdict": a.checker_verdict}
    if a.time:
        rec["time"] = a.time
    doc = changes_append(a.log, rec, candidate_version=a.candidate_version, project_id=a.project_id)
    print(f"{doc['changes'][-1]['change_id']} appended (record {len(doc['changes'])}) -> {a.log}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("diff")
    d.add_argument("before")
    d.add_argument("after")
    d.add_argument("--out", required=True)
    d.add_argument("--before-manifest")
    d.add_argument("--after-manifest")
    d.add_argument("--before-spec")
    d.add_argument("--after-spec")
    d.add_argument("--baseline-a")
    d.add_argument("--baseline-a-manifest")
    d.add_argument("--verdicts")
    d.add_argument("--changes")
    d.add_argument("--register")
    d.add_argument("--ledger", action="append", default=[])
    d.add_argument("--sha")
    d.add_argument("--new-revision-set", action="store_true")
    d.add_argument("--sealed-registry")
    m = sub.add_parser("manifest")
    m.add_argument("--lines", required=True)
    m.add_argument("--candidate-version", required=True)
    m.add_argument("--code-commit", required=True)
    m.add_argument("--project-id", required=True)
    m.add_argument("--drawing", action="append", default=[], required=True)
    m.add_argument("--document-register")
    m.add_argument("--verdicts")
    m.add_argument("--sealed-registry")
    m.add_argument("--out", required=True)
    c = sub.add_parser("change-add")
    c.add_argument("--log", required=True)
    c.add_argument("--candidate-version", required=True)
    c.add_argument("--project-id", required=True)
    c.add_argument("--line-id", required=True)
    c.add_argument("--element-id", action="append", default=[], required=True)
    c.add_argument("--unit", required=True)
    c.add_argument("--old", required=True)
    c.add_argument("--new", required=True)
    c.add_argument("--cause", required=True)
    c.add_argument("--evidence", action="append", default=[], required=True)
    c.add_argument("--checker-verdict", required=True)
    c.add_argument("--time")
    c.add_argument("--sealed-registry")
    p = sub.add_parser("pick")
    p.add_argument("--sha", required=True)
    p.add_argument("ids", nargs="*")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "pick":
            print(json.dumps(G1.pick(a.ids, a.sha), indent=1))
            return 0
        return {"diff": main_diff, "manifest": main_manifest, "change-add": main_change_add}[a.cmd](a)
    except Refused as ex:
        for code, text in ex.problems:
            print(f"GATE B REFUSED [{code}]: {text}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
