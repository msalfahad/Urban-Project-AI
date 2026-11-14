"""ARCH_TAKEOFF_V3.0.87 (T-770 r10, lane I, DELIVERY MODE wiring package): the SAME opt-in BOQ candidate as
ARCH_TAKEOFF_V3.0 .. V3.0.86, extended with FILL_WIRE_V7 = FILL_WIRE_V6 (engine.source.arch_v3086, R-T770-1 .. -7,
unchanged and called as is) + R-T770-8 below. Nothing here measures, invents or chooses a quantity: the
Checker-verified fix-row sets, and the Checker's own finding rows, carry every figure, label and basis.

R-T770-8 (every villa; a fix row that a Checker finding states in its Gate verdict instead of a worker's set):
  (ac) a set with "kind": "CHECKER_FINDING" carries the finding id, the verdict it was written in (task, gate, UTC time)
       and, on every row, the finding id inside the basis and a "hand" list of positive factors whose product is the
       row's after net to 4 decimals (the figure is the Checker's arithmetic restated, never a new measurement); a row
       without them, a factor <= 0, or a product that differs stops the run; "hand" and the set's finding fields are
       dropped before FILL_WIRE_V6 applies the row by line id like any other row;
  (ad) a line that two sets of one package both bind stops the run (one owner per line per round).

Nothing here names a project, a sheet, a layer or a coordinate.
"""

from __future__ import annotations

import copy
import json
import math

from engine.source import arch_v3081 as B
from engine.source import arch_v3086 as A86

METHOD = "ARCH_TAKEOFF_V3.0.87"
EXTENDS = "ARCH_TAKEOFF_V3.0.86"
POLICY_ID = "URBAN_BOQ_T770_ARCH_V3_0_87"
RULE_V8 = "R-T770-8"
RULES = A86.RULES + [RULE_V8]
PACKAGE_SCHEMA = "URBAN_FILL_PACKAGE_V7"
CHECKER_FINDING = "CHECKER_FINDING"
FillError = B.FillError


def _checker_set(doc, name):
    """R-T770-8 (ac) on one set -> the set as FILL_WIRE_V6 reads it."""
    s = copy.deepcopy(doc)
    if s.get("kind") != CHECKER_FINDING:
        return s
    fid = str(s.get("finding") or "").strip()
    ver = s.get("verdict") or {}
    if not fid or not all(str(ver.get(k) or "").strip() for k in ("task", "gate", "utc")):
        raise FillError(f"{name}: a {CHECKER_FINDING} set needs its finding id and verdict task / gate / utc "
                        f"({RULE_V8} ac)")
    for r in s.get("rows") or []:
        tag = f"{name} {r.get('line_id')}"
        if fid not in str(r.get("basis") or ""):
            raise FillError(f"{tag}: the basis does not name the finding {fid} ({RULE_V8} ac)")
        hand = r.get("hand")
        if not isinstance(hand, list) or not hand or not all(B._num(x) and float(x) > 0 for x in hand):
            raise FillError(f"{tag}: a finding row needs a 'hand' list of positive factors ({RULE_V8} ac)")
        a = r.get("after") or {}
        if a.get("class") != "RELEASED" or not B._num(a.get("net")):
            raise FillError(f"{tag}: a finding row releases a figure, got {a} ({RULE_V8} ac)")
        if round(math.prod(float(x) for x in hand), 4) != round(float(a["net"]), 4):
            raise FillError(f"{tag}: hand {hand} = {math.prod(float(x) for x in hand):.6f} is not the after net "
                            f"{a['net']} ({RULE_V8} ac)")
        r.pop("hand")
    for k in ("kind", "finding", "verdict"):
        s.pop(k, None)
    return s


def prepare(pkg, base_lines=None):
    """URBAN_FILL_PACKAGE_V7 -> (URBAN_FILL_PACKAGE_V6 for arch_v3086, report)."""
    if not isinstance(pkg, dict) or pkg.get("schema") != PACKAGE_SCHEMA:
        raise FillError(f"package schema {pkg.get('schema') if isinstance(pkg, dict) else type(pkg)} is not "
                        f"{PACKAGE_SCHEMA}")
    if pkg.get("base") != EXTENDS:
        raise FillError(f"package built for {pkg.get('base')}, base is {EXTENDS}")
    names = list(pkg.get("set_names") or [])
    raw = list(pkg.get("sets") or [])
    if len(names) != len(raw) or len(set(names)) != len(names):
        raise FillError(f"set_names {names} do not name the {len(raw)} sets once each")
    sets, owner, findings = [], {}, []
    for name, doc in zip(names, raw):
        if isinstance(doc, dict) and doc.get("kind") == CHECKER_FINDING:
            findings.append({"set": name, "finding": doc.get("finding"), "verdict": doc.get("verdict"),
                             "rows": len(doc.get("rows") or [])})
        s = _checker_set(doc, name)
        for r in s.get("rows") or []:
            lid = r.get("line_id")
            if lid is None:
                continue
            if lid in owner:
                raise FillError(f"{lid}: bound by {owner[lid]} and {name} in one package ({RULE_V8} ad)")
            owner[lid] = name
        sets.append(s)
    v6 = {k: copy.deepcopy(v) for k, v in pkg.items() if k not in ("schema", "method", "base", "row_bases",
                                                                       "sets", "set_sha256")}
    v6.update(schema=A86.PACKAGE_SCHEMA, method=A86.METHOD, base=A86.EXTENDS,
              row_bases=list(pkg.get("row_bases") or []) + [EXTENDS], set_names=names, sets=sets)
    return v6, {"checker_finding_sets": findings}


def apply_index(index_doc, pkg):
    """the index view: (new index doc, applied rows, late added lines, report)."""
    if index_doc.get("candidate_version") not in (None, EXTENDS):
        raise FillError(f"index is {index_doc.get('candidate_version')}, base is {EXTENDS}")
    v6, rep = prepare(pkg, index_doc["lines"])
    base = copy.deepcopy(index_doc)
    base["candidate_version"] = A86.EXTENDS if index_doc.get("candidate_version") else None
    new, applied, late, rep6 = A86.apply_index(base, v6)
    rep.update(rep6)
    new["candidate_version"], new["extends"] = METHOD, EXTENDS
    new["fill"] = dict(new["fill"], rule=RULES, policy=POLICY_ID,
                       checker_finding_sets=len(rep["checker_finding_sets"]))
    return new, applied, late, rep


def apply_boq_lines(lines, pkg):
    """the BOQ-line view: (new lines, applied rows, added {id: line}, late adds, report)."""
    v6, rep = prepare(pkg, lines)
    new, applied, added, late, rep6 = A86.apply_boq_lines(lines, v6)
    rep.update(rep6)
    for ln in new[len(lines):]:
        ln["rule"] = dict(ln.get("rule") or {}, version=METHOD)
    return new, applied, added, late, rep


def diff_rows(applied, added=(), late=(), report=None):
    return A86.diff_rows(applied, added, late, report)


def write(out, base_lines, pkg):
    """the hub's V3_0_87_* files beside the base candidate's files. -> (file names, identity)."""
    import csv
    import io
    from pathlib import Path
    from engine.source import arch_v30 as A30
    from engine.source import boq_line as BL
    out = Path(out)
    new, applied, added, late, report = apply_boq_lines(base_lines, pkg)
    for ln in new[len(base_lines):]:
        BL.validate(ln)
    d = diff_rows(applied, added, late, report)
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(d[0]), lineterminator="\n")
    w.writeheader()
    w.writerows(d)
    by_set = {}
    for r in applied:
        k = r.get("set_doc") or r.get("set") or "-"
        by_set[k] = by_set.get(k, 0) + 1
    ident = {"base_lines": len(base_lines), "v3_0_87_lines": len(new), "applied": len(applied),
             "added": len(added) + len(late), "by_set": by_set,
             "checker_finding_sets": len(report["checker_finding_sets"]),
             "outside_rows_identical_to_base": True}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "rule": RULES, "released_default": False,
           "identity": ident, "report": report}
    files = {"V3_0_87_BOQ_LINES.json": BL.dumps(new), "V3_0_87_BOQ_LINES.csv": A30._lines_csv(new),
             "V3_0_87_DIFF.csv": buf.getvalue(), "V3_0_87_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident


def policy_record():
    return dict(A86.policy_record(), policy_id=POLICY_ID, method=METHOD, extends=EXTENDS, rule=RULES,
                package_schema=PACKAGE_SCHEMA)


def canon(x):
    return json.dumps(x, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
