"""ARCH_TAKEOFF_V3.0.85 (T-770 r8, lane I, DELIVERY MODE wiring package): the SAME opt-in BOQ candidate as
ARCH_TAKEOFF_V3.0 .. V3.0.84, extended with FILL_WIRE_V5 = FILL_WIRE_V4 (engine.source.arch_v3084, R-T770-1 .. -5,
unchanged and called as is) + R-T770-6 below. Nothing here measures, invents or chooses a quantity: the
Checker-verified fix-row sets carry every figure, label and basis.

R-T770-6 (every villa; the T-760 / T-771 set shapes):
  (v) a row labelled NOT_APPLICABLE_WITH_EVIDENCE (the evidence state written as the label) with after RELEASED 0 is
      the R-T770-4 (m) NOT_APPLICABLE row: label NOT_APPLICABLE, after EXCLUDED with reason
      NOT_APPLICABLE_WITH_EVIDENCE, HELD lines only, never written as 0; that label with a figure other than 0, or a
      row without a basis, stops the run;
  (w) a RECALL names, by element id, added entries of a set an earlier package already wired (and deferred by name,
      R-T770-5 u): only those entries are read (no row of the recalled set is applied again), each must occur exactly
      once in the pinned set, the recalled set is not also a set of this package, and each entry goes through the
      R-T770-5 s / t handling (a carrier-derived entry is recomputed from its carrier on the wired candidate; a carrier
      still HELD stops the run); its basis says it was recalled and why. The added line keeps the FILL_WIRE_V1 id
      (arch_v3081.new_line_id of its own set name and alias), so a recalled line has the id it would have had.

Nothing here names a project, a sheet, a layer or a coordinate.
"""

from __future__ import annotations

import copy
import json

from engine.source import arch_v3081 as B
from engine.source import arch_v3084 as A84

METHOD = "ARCH_TAKEOFF_V3.0.85"
EXTENDS = "ARCH_TAKEOFF_V3.0.84"
POLICY_ID = "URBAN_BOQ_T770_ARCH_V3_0_85"
RULE_V6 = "R-T770-6"
RULES = A84.RULES + [RULE_V6]
PACKAGE_SCHEMA = "URBAN_FILL_PACKAGE_V5"
NA_STATE = A84.NA_STATE
NOT_APPLICABLE = A84.NOT_APPLICABLE
FillError = B.FillError


def _na_label_rows(doc, name):
    """R-T770-6 (v) on one set -> (set copy, number of rows read as NOT_APPLICABLE)."""
    s = copy.deepcopy(doc)
    n = 0
    for r in s.get("rows") or []:
        if r.get("label") != NA_STATE:
            continue
        a = r.get("after") or {}
        if a.get("class") != "RELEASED" or not B._num(a.get("net")) or float(a["net"]) != 0.0:
            raise FillError(f"{name} {r.get('line_id')}: label {NA_STATE} with after {a} (only a RELEASED 0 is the "
                            f"NOT_APPLICABLE row, {RULE_V6} v)")
        if not str(r.get("basis") or "").strip():
            raise FillError(f"{name} {r.get('line_id')}: a NOT_APPLICABLE row needs its evidence basis ({RULE_V6} v)")
        r["label"] = NOT_APPLICABLE
        r["after"] = {"class": "EXCLUDED", "reason": NA_STATE}
        r["basis"] = f"{r['basis']} [label {NA_STATE} read as the R-T770-4 m row, {RULE_V6} v]"
        n += 1
    return s, n


def _recall_set(name, spec, doc):
    """R-T770-6 (w): the named added entries of an already-wired set -> a set with no rows."""
    els = list(spec.get("element_ids") or [])
    why = str(spec.get("reason") or "").strip()
    if not els or not why:
        raise FillError(f"recall {name}: needs element ids and a reason ({RULE_V6} w)")
    if len(set(els)) != len(els):
        raise FillError(f"recall {name}: an element id named twice")
    pool = list(doc.get("new_lines") or []) + [r for r in doc.get("rows_detail") or [] if r.get("action") == "ADD"]
    picked = []
    for el in els:
        hits = [n for n in pool if n.get("element_id") == el]
        if len(hits) != 1:
            raise FillError(f"recall {name}: element {el} occurs {len(hits)} times among its added entries")
        n = {k: v for k, v in copy.deepcopy(hits[0]).items() if k != "action"}
        n["basis"] = f"{n.get('basis')} [recalled from {name} ({RULE_V6} w): {why}]"
        picked.append(n)
    out = {k: copy.deepcopy(doc[k]) for k in ("schema", "candidate_version") if k in doc}
    out.update(task=name, rows=[], new_lines=picked)
    return out


def prepare(pkg, base_lines=None, view="index"):
    """URBAN_FILL_PACKAGE_V5 -> (URBAN_FILL_PACKAGE_V4 for arch_v3084, report)."""
    if not isinstance(pkg, dict) or pkg.get("schema") != PACKAGE_SCHEMA:
        raise FillError(f"package schema {pkg.get('schema') if isinstance(pkg, dict) else type(pkg)} is not "
                        f"{PACKAGE_SCHEMA}")
    if pkg.get("base") != EXTENDS:
        raise FillError(f"package built for {pkg.get('base')}, base is {EXTENDS}")
    names = list(pkg.get("set_names") or [])
    raw = list(pkg.get("sets") or [])
    if len(names) != len(raw) or len(set(names)) != len(names):
        raise FillError(f"set_names {names} do not name the {len(raw)} sets once each")
    recall = dict(pkg.get("recall") or {})
    recall_sets = dict(pkg.get("recall_sets") or {})
    if set(recall) != set(recall_sets):
        raise FillError(f"recall {sorted(recall)} and recall_sets {sorted(recall_sets)} differ")
    both = sorted(set(recall) & set(names))
    if both:
        raise FillError(f"{both}: a recalled set is also a set of this package ({RULE_V6} w)")
    report = {"na_label_rows": {}, "recalled": []}
    sets = []
    for name, doc in zip(names, raw):
        s, n = _na_label_rows(doc, name)
        if n:
            report["na_label_rows"][name] = n
        sets.append(s)
    for name in sorted(recall):
        sets.append(_recall_set(name, recall[name], recall_sets[name]))
        names.append(name)
        report["recalled"] += [{"set": name, "element_id": el, "reason": recall[name]["reason"]}
                               for el in recall[name]["element_ids"]]
    v4 = {"schema": A84.PACKAGE_SCHEMA, "method": A84.METHOD, "base": A84.EXTENDS,
          "row_bases": list(pkg.get("row_bases") or []) + [EXTENDS], "set_names": names, "sets": sets}
    for k in ("carriers", "defer_added", "carry", "basis_corrections", "defer"):
        if pkg.get(k):
            v4[k] = copy.deepcopy(pkg[k])
    return v4, report


def _recalled_ids(report):
    return {(x["set"], x["element_id"]) for x in report["recalled"]}


def apply_index(index_doc, pkg):
    """the index view: (new index doc, applied rows, late added lines, report)."""
    if index_doc.get("candidate_version") not in (None, EXTENDS):
        raise FillError(f"index is {index_doc.get('candidate_version')}, base is {EXTENDS}")
    v4, rep = prepare(pkg, index_doc["lines"], "index")
    new, applied, late, rep4 = A84.apply_index(index_doc, v4)
    rep["v4"] = rep4
    rc = {x["new_line_id"] for x in late if (x["set"], x["element_id"]) in _recalled_ids(rep)}
    for ln in new["lines"][len(index_doc["lines"]):]:
        if ln["line_id"] in rc:
            ln["added_by"] = RULE_V6
    new["candidate_version"], new["extends"] = METHOD, EXTENDS
    new["fill"] = dict(new["fill"], rule=RULES, policy=POLICY_ID, na_label_rows=sum(rep["na_label_rows"].values()),
                       recalled=len(rep["recalled"]))
    return new, applied, late, rep


def apply_boq_lines(lines, pkg):
    """the BOQ-line view: (new lines, applied rows, added {id: line}, late adds, report)."""
    v4, rep = prepare(pkg, lines, "boq")
    new, applied, added, late, rep4 = A84.apply_boq_lines(lines, v4)
    rep["v4"] = rep4
    rc = {x["new_line_id"] for x in late if (x["set"], x["element_id"]) in _recalled_ids(rep)}
    for ln in new[len(lines):]:
        rid = RULE_V6 if ln["line_id"] in rc else (ln.get("rule") or {}).get("rule_id")
        ln["rule"] = dict(ln.get("rule") or {}, rule_id=rid, version=METHOD)
    return new, applied, added, late, rep


def diff_rows(applied, added=(), late=()):
    return A84.diff_rows(applied, added, late)


def write(out, base_lines, pkg):
    """the hub's V3_0_85_* files beside the base candidate's files. -> (file names, identity)."""
    import csv
    import io
    from pathlib import Path
    from engine.source import arch_v30 as A30
    from engine.source import boq_line as BL
    out = Path(out)
    new, applied, added, late, report = apply_boq_lines(base_lines, pkg)
    for ln in new[len(base_lines):]:
        BL.validate(ln)
    d = diff_rows(applied, added, late)
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(d[0]), lineterminator="\n")
    w.writeheader()
    w.writerows(d)
    by_set = {}
    for r in applied:
        k = r.get("set_doc") or r.get("set") or "-"
        by_set[k] = by_set.get(k, 0) + 1
    ident = {"base_lines": len(base_lines), "v3_0_85_lines": len(new), "applied": len(applied),
             "added": len(added) + len(late), "by_set": by_set,
             "na_label_rows": sum(report["na_label_rows"].values()), "recalled": len(report["recalled"]),
             "outside_rows_identical_to_base": True}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "rule": RULES, "released_default": False,
           "identity": ident, "report": report}
    files = {"V3_0_85_BOQ_LINES.json": BL.dumps(new), "V3_0_85_BOQ_LINES.csv": A30._lines_csv(new),
             "V3_0_85_DIFF.csv": buf.getvalue(), "V3_0_85_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident


def policy_record():
    return dict(A84.policy_record(), policy_id=POLICY_ID, method=METHOD, extends=EXTENDS, rule=RULES,
                package_schema=PACKAGE_SCHEMA)


def canon(x):
    return json.dumps(x, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
