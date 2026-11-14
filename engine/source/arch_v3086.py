"""ARCH_TAKEOFF_V3.0.86 (T-770 r9, lane I, DELIVERY MODE wiring package): the SAME opt-in BOQ candidate as
ARCH_TAKEOFF_V3.0 .. V3.0.85, extended with FILL_WIRE_V6 = FILL_WIRE_V5 (engine.source.arch_v3085, R-T770-1 .. -6,
unchanged and called as is) + R-T770-7 below. Nothing here measures, invents or chooses a quantity: the
Checker-verified fix-row sets carry every figure, label and basis.

R-T770-7 (every villa; the T-787 / T-789 / T-790 set shapes and the Checker's basis-text finding F-V770r8-1):
  (x) a set that names its base as "base": "<METHOD> (<index file>)" and no candidate_version is read as built on
      <METHOD> (the first token); a set with both that disagree, or a base that is not a method name, stops the run;
  (y) a row that carries its label inside after ({"class": .., "net": .., "label": L}) and none of its own takes L as
      the row label (after keeps class / net only); a row with two labels that differ stops the run;
  (z) a NO_LINE row (line_id null, action NO_LINE: the set closes an element the candidate never carried as a line)
      is RECORDED, never written as a line and never as 0: its after must be RELEASED 0, its basis must name the
      complement line(s) that already bill the element whole (line ids "L-" + 20 hex) and each named line must be
      RELEASED with a figure > 0 in the base; a base line of the same item code and element id (the row should have
      bound it by line id) stops the run; a NO_LINE row with any other after stops the run;
  (aa) a BASIS_TEXT row (action starting BASIS_TEXT) restates only the basis: its after must equal its before (class,
      net) and its label the base line's label; it binds and applies as R-T770-1 does (the figure is unchanged);
  (ab) a BASE BASIS CORRECTION named by the package (line id, old text, new text, source) on a line the base already
      carries (wired by an earlier round, not a row of this package): the old text must occur exactly once in that
      line's fill_basis; only the text changes (class, figure, range and label are untouched) and the line is listed
      in the diff as a basis-only change.

Nothing here names a project, a sheet, a layer or a coordinate.
"""

from __future__ import annotations

import copy
import json
import re

from engine.source import arch_v3081 as B
from engine.source import arch_v3085 as A85

METHOD = "ARCH_TAKEOFF_V3.0.86"
EXTENDS = "ARCH_TAKEOFF_V3.0.85"
POLICY_ID = "URBAN_BOQ_T770_ARCH_V3_0_86"
RULE_V7 = "R-T770-7"
RULES = A85.RULES + [RULE_V7]
PACKAGE_SCHEMA = "URBAN_FILL_PACKAGE_V6"
NO_LINE = "NO_LINE"
BASIS_TEXT = "BASIS_TEXT"
FillError = B.FillError
_LID = re.compile(r"\bL-[0-9a-f]{20}\b")
_METHOD = re.compile(r"^ARCH_TAKEOFF_V\d+(\.\d+)*$")


def _set_base(s, name):
    """R-T770-7 (x)."""
    b = s.get("base")
    if b is None:
        return
    tok = str(b).split()[0] if str(b).strip() else ""
    if not _METHOD.match(tok):
        raise FillError(f"{name}: set base {b!r} does not name a method ({RULE_V7} x)")
    cv = s.get("candidate_version")
    if cv is not None and cv != tok:
        raise FillError(f"{name}: candidate_version {cv} and base {tok} disagree ({RULE_V7} x)")
    s["candidate_version"] = tok


def _label(r, name):
    """R-T770-7 (y)."""
    a = r.get("after") or {}
    if "label" not in a:
        return
    al = a.get("label")
    if r.get("label") not in (None, "", al):
        raise FillError(f"{name} {r.get('line_id') or r.get('element_id')}: row label {r['label']} and after label "
                        f"{al} differ ({RULE_V7} y)")
    r["label"] = al
    r["after"] = {k: v for k, v in a.items() if k != "label"}


def _base_state(ln, view):
    if view == "index":
        return {"class": ln["class"], "net": ln.get("measured_net"), "element_id": ln.get("element_id")}
    st = B._boq_before(ln)
    return {"class": st["class"], "net": st["net"], "element_id": st["element_id"]}


def _no_line(r, name, by_id, by_code_el, view):
    """R-T770-7 (z) -> the record of one NO_LINE row."""
    a = r.get("after") or {}
    tag = f"{name} {r.get('element_id')}"
    if a.get("class") != "RELEASED" or not B._num(a.get("net")) or float(a["net"]) != 0.0:
        raise FillError(f"{tag}: a NO_LINE row closes an element at RELEASED 0 only, got {a} ({RULE_V7} z)")
    for k in ("item_code", "unit", "element_id", "label", "basis"):
        if not str(r.get(k) or "").strip():
            raise FillError(f"{tag}: a NO_LINE row lacks {k} ({RULE_V7} z)")
    if r["label"] not in B.LABELS:
        raise FillError(f"{tag}: label {r['label']} not one of {B.LABELS}")
    if (r["item_code"], r["unit"], str(r["element_id"])) in by_code_el:
        raise FillError(f"{tag}: the base carries a {r['item_code']} line for this element; bind it by line id "
                        f"({RULE_V7} z)")
    comp = sorted(set(_LID.findall(str(r["basis"]))))
    if not comp:
        raise FillError(f"{tag}: a NO_LINE row names no complement line in its basis ({RULE_V7} z)")
    got = []
    for lid in comp:
        ln = by_id.get(lid)
        if ln is None:
            raise FillError(f"{tag}: complement line {lid} is not in the base ({RULE_V7} z)")
        st = _base_state(ln, view)
        if st["class"] != "RELEASED" or not B._num(st["net"]) or float(st["net"]) <= 0:
            raise FillError(f"{tag}: complement line {lid} is {st['class']} {st['net']}, not a released figure "
                            f"({RULE_V7} z)")
        got.append({"line_id": lid, "item_code": ln["item_code"], "unit": ln["unit"], "net": float(st["net"])})
    return {"set": name, "id": r.get("id"), "item_code": r["item_code"], "unit": r["unit"],
            "element_id": r["element_id"], "label": r["label"], "basis": r["basis"], "complement": got}


def prepare(pkg, base_lines, view="index"):
    """URBAN_FILL_PACKAGE_V6 -> (URBAN_FILL_PACKAGE_V5 for arch_v3085, report)."""
    if not isinstance(pkg, dict) or pkg.get("schema") != PACKAGE_SCHEMA:
        raise FillError(f"package schema {pkg.get('schema') if isinstance(pkg, dict) else type(pkg)} is not "
                        f"{PACKAGE_SCHEMA}")
    if pkg.get("base") != EXTENDS:
        raise FillError(f"package built for {pkg.get('base')}, base is {EXTENDS}")
    names = list(pkg.get("set_names") or [])
    raw = list(pkg.get("sets") or [])
    if len(names) != len(raw) or len(set(names)) != len(names):
        raise FillError(f"set_names {names} do not name the {len(raw)} sets once each")
    by_id = {ln["line_id"]: ln for ln in base_lines}
    by_code_el = {(ln["item_code"], ln["unit"], str(_base_state(ln, view)["element_id"])) for ln in base_lines}
    report = {"set_base_read": [], "no_line_rows": [], "basis_text_rows": [], "base_basis_corrections": []}
    sets = []
    for name, doc in zip(names, raw):
        s = copy.deepcopy(doc)
        if "base" in s:
            _set_base(s, name)
            report["set_base_read"].append({"set": name, "candidate_version": s["candidate_version"]})
            s.pop("base")
        keep = []
        for r in s.get("rows") or []:
            r = copy.deepcopy(r)
            _label(r, name)
            act = str(r.get("action") or "")
            if act == NO_LINE or (r.get("line_id") is None and act.startswith(NO_LINE)):
                if r.get("line_id") is not None:
                    raise FillError(f"{name} {r['line_id']}: a NO_LINE row names a line ({RULE_V7} z)")
                report["no_line_rows"].append(_no_line(r, name, by_id, by_code_el, view))
                continue
            if r.get("line_id") is None:
                raise FillError(f"{name} {r.get('element_id')}: a row without a line id is only a NO_LINE row")
            if act.startswith(BASIS_TEXT):
                b, a = r.get("before") or {}, r.get("after") or {}
                ln = by_id.get(r["line_id"])
                if b.get("class") != a.get("class") or not B._same(b.get("net"), a.get("net")):
                    raise FillError(f"{r['line_id']}: a BASIS_TEXT row moves the figure {b} -> {a} ({RULE_V7} aa)")
                if ln is not None and ln.get("method_label") not in (None, r.get("label")):
                    raise FillError(f"{r['line_id']}: a BASIS_TEXT row relabels {ln.get('method_label')} -> "
                                    f"{r.get('label')} ({RULE_V7} aa)")
                report["basis_text_rows"].append({"set": name, "line_id": r["line_id"], "item_code": r["item_code"]})
            for k in ("action", "id"):
                r.pop(k, None)
            keep.append(r)
        s["rows"] = keep
        sets.append(s)
    v5 = {"schema": A85.PACKAGE_SCHEMA, "method": A85.METHOD, "base": A85.EXTENDS,
          "row_bases": list(pkg.get("row_bases") or []) + [EXTENDS], "set_names": names, "sets": sets}
    for k in ("carriers", "defer_added", "carry", "basis_corrections", "defer", "recall", "recall_sets"):
        if pkg.get(k):
            v5[k] = copy.deepcopy(pkg[k])
    fixes = dict(pkg.get("base_basis_corrections") or {})
    rowed = {r["line_id"] for s in sets for r in s["rows"]}
    for lid, f in sorted(fixes.items()):
        if lid in rowed:
            raise FillError(f"{lid}: a base basis correction on a row of this package ({RULE_V7} ab)")
        ln = by_id.get(lid)
        if ln is None:
            raise FillError(f"{lid}: a base basis correction names no base line ({RULE_V7} ab)")
        if not str(f.get("source") or "").strip() or not str(f.get("new") or "").strip() \
                or str(ln.get("fill_basis") or "").count(str(f.get("old") or "\0")) != 1:
            raise FillError(f"{lid}: a base basis correction needs a source, a new text and its old text once in the "
                            f"line's basis ({RULE_V7} ab)")
        report["base_basis_corrections"].append({"line_id": lid, "item_code": ln["item_code"], "unit": ln["unit"],
                                                 "old": f["old"], "new": f["new"], "source": f["source"]})
    return v5, report


def _fix_text(ln, f):
    return ln["fill_basis"].replace(f["old"], f["new"]) + f" [basis text corrected: {f['source']}, {RULE_V7} ab]"


def apply_index(index_doc, pkg):
    """the index view: (new index doc, applied rows, late added lines, report)."""
    if index_doc.get("candidate_version") not in (None, EXTENDS):
        raise FillError(f"index is {index_doc.get('candidate_version')}, base is {EXTENDS}")
    v5, rep = prepare(pkg, index_doc["lines"], "index")
    base = copy.deepcopy(index_doc)
    base["candidate_version"] = A85.EXTENDS if index_doc.get("candidate_version") else None
    new, applied, late, rep5 = A85.apply_index(base, v5)
    rep["v5"] = rep5
    fixed = {x["line_id"]: x for x in rep["base_basis_corrections"]}
    for ln in new["lines"]:
        if ln["line_id"] in fixed:
            ln["fill_basis"] = _fix_text(ln, fixed[ln["line_id"]])
    names = {r["line_id"] for r in applied} | set(fixed)
    B._assert_outside(index_doc["lines"], new["lines"], names, len(new["lines"]) - len(index_doc["lines"]))
    new["candidate_version"], new["extends"] = METHOD, EXTENDS
    new["fill"] = dict(new["fill"], rule=RULES, policy=POLICY_ID, no_line_rows=len(rep["no_line_rows"]),
                       basis_text_rows=len(rep["basis_text_rows"]),
                       base_basis_corrections=len(rep["base_basis_corrections"]))
    return new, applied, late, rep


def apply_boq_lines(lines, pkg):
    """the BOQ-line view: (new lines, applied rows, added {id: line}, late adds, report)."""
    v5, rep = prepare(pkg, lines, "boq")
    new, applied, added, late, rep5 = A85.apply_boq_lines(lines, v5)
    rep["v5"] = rep5
    fixed = {x["line_id"]: x for x in rep["base_basis_corrections"]}
    for ln in new:
        if ln["line_id"] in fixed:
            if str(ln.get("fill_basis") or "").count(fixed[ln["line_id"]]["old"]) != 1:
                raise FillError(f"{ln['line_id']}: old basis text not once in the BOQ line ({RULE_V7} ab)")
            ln["fill_basis"] = _fix_text(ln, fixed[ln["line_id"]])
    names = {r["line_id"] for r in applied} | set(fixed)
    B._assert_outside(lines, new, names, len(new) - len(lines))
    for ln in new[len(lines):]:
        ln["rule"] = dict(ln.get("rule") or {}, version=METHOD)
    return new, applied, added, late, rep


def diff_rows(applied, added=(), late=(), report=None):
    out = A85.diff_rows(applied, added, late)
    keys = list(out[0]) if out else ["line_id", "set", "item_code", "unit", "element_id", "before_class",
                                     "before_net", "before_low", "before_high", "after_class", "after_net",
                                     "after_low", "after_high", "label", "basis"]
    for x in (report or {}).get("base_basis_corrections") or []:
        d = {k: None for k in keys}
        d.update(line_id=x["line_id"], set="BASIS_TEXT", item_code=x["item_code"], unit=x["unit"],
                 label="(unchanged)", basis=f"basis only ({RULE_V7} ab): '{x['old']}' -> '{x['new']}' ({x['source']})")
        out.append(d)
    return sorted(out, key=lambda d: d["line_id"])


def write(out, base_lines, pkg):
    """the hub's V3_0_86_* files beside the base candidate's files. -> (file names, identity)."""
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
    ident = {"base_lines": len(base_lines), "v3_0_86_lines": len(new), "applied": len(applied),
             "added": len(added) + len(late), "by_set": by_set, "no_line_rows": len(report["no_line_rows"]),
             "basis_text_rows": len(report["basis_text_rows"]),
             "base_basis_corrections": len(report["base_basis_corrections"]),
             "outside_rows_identical_to_base": True}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "rule": RULES, "released_default": False,
           "identity": ident, "report": report}
    files = {"V3_0_86_BOQ_LINES.json": BL.dumps(new), "V3_0_86_BOQ_LINES.csv": A30._lines_csv(new),
             "V3_0_86_DIFF.csv": buf.getvalue(), "V3_0_86_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident


def policy_record():
    return dict(A85.policy_record(), policy_id=POLICY_ID, method=METHOD, extends=EXTENDS, rule=RULES,
                package_schema=PACKAGE_SCHEMA)


def canon(x):
    return json.dumps(x, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
