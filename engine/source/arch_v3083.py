"""ARCH_TAKEOFF_V3.0.83 (T-770 r6, lane I, DELIVERY MODE wiring package): the SAME opt-in BOQ candidate as
ARCH_TAKEOFF_V3.0 .. V3.0.82, extended with FILL_WIRE_V3 = FILL_WIRE_V2 (engine.source.arch_v3082, R-T770-1 / -2 / -3,
unchanged and called as is) + R-T770-4 below. Nothing here measures, invents or chooses a quantity: the
Checker-verified fix-row sets carry every figure, label and basis.

R-T770-4 (every villa; the T-757 / T-763 / T-765 set shapes and the rows an earlier round already wired):
  (k) a set whose own file names no task, or a worker schema of the row shape (*_FIX_ROWS_V1), is named by the
      package (task = the package's set name) and read under the common row schema; its source schema is kept in the
      set; a schema outside that shape stops the run;
  (l) CARRY: when a set was wired in part by an earlier round, the package names the lines still to wire; only those
      rows of that set are applied and its added lines are not added again (they are in the base); a carried line id
      the set has no row for stops the run;
  (m) a NOT_APPLICABLE row (label NOT_APPLICABLE, after EXCLUDED with reason NOT_APPLICABLE_WITH_EVIDENCE) binds its
      line as R-T770-1 (a) does and is applied only to a HELD line (a figure is never dropped by it): the line becomes
      EXCLUDED with its evidence (index: excluded_reason; BOQ view: evidence_state NOT_APPLICABLE_WITH_EVIDENCE), never
      0; any other EXCLUDED row stops the run;
  (n) a RESTATED SAFETY LINE (a set's safety_line whose before is the figure of the one safety line of that item code
      already in the base) binds that base line (RELEASED, label SAFETY, net = before; exactly one such line) and
      becomes a row on it: after = max(1 m3, the set's ignored_small total), the total equal to the sum of its parts
      (never a second safety line);
  (o) a basis correction named by the package (line id, old text, new text, source) replaces the old text, which must
      occur exactly once in that row's basis; the figure is never touched by it.

Added-line ids keep the FILL_WIRE_V1 id rule (arch_v3081.new_line_id). Nothing here names a project, a sheet, a layer
or a coordinate.
"""

from __future__ import annotations

import copy
import json

from engine.source import arch_v3081 as B
from engine.source import arch_v3082 as A82

METHOD = "ARCH_TAKEOFF_V3.0.83"
EXTENDS = "ARCH_TAKEOFF_V3.0.82"
POLICY_ID = "URBAN_BOQ_T770_ARCH_V3_0_83"
RULE_V3 = "R-T770-4"
RULES = A82.RULES + [RULE_V3]
PACKAGE_SCHEMA = "URBAN_FILL_PACKAGE_V3"
COMMON_ROW_SCHEMA = "URBAN_FIX_ROWS_V1"
NOT_APPLICABLE = "NOT_APPLICABLE"
NA_STATE = "NOT_APPLICABLE_WITH_EVIDENCE"
FillError = B.FillError


def _tol_sum(a, b, tol=1e-4):
    return abs(float(a) - float(b)) <= tol


def _base_view(ln, view):
    if view == "index":
        return {"class": ln["class"], "net": ln.get("measured_net"), "low": ln.get("held_low"),
                "high": ln.get("held_high"), "element_id": ln.get("element_id"), "label": ln.get("method_label")}
    st = B._boq_before(ln)
    st["label"] = ln.get("method_label")
    return st


def _normalise(doc, name):
    """R-T770-4 (k)."""
    s = copy.deepcopy(doc)
    sch = s.get("schema")
    if sch not in B.ROW_SCHEMAS:
        if sch is not None and not str(sch).endswith("_FIX_ROWS_V1"):
            raise FillError(f"{name}: set schema {sch} is not of the fix-row shape")
        s["source_schema"] = sch
        s["schema"] = COMMON_ROW_SCHEMA
    own = s.get("task") or s.get("set")
    if own not in (None, name):
        raise FillError(f"set names {own}, the package names it {name}")
    s["task"] = name
    return s


def _safety_row(s, name, base_lines, view):
    """R-T770-4 (n): a restated safety line -> a row on the base safety line."""
    n = s.pop("safety_line")
    before = n.get("before")
    if not B._num(before):
        s["safety_line"] = n          # a plain added safety line: R-T770-2 (g) as before
        return None
    ig = s.get("ignored_small") or {}
    parts = [v for k, v in ig.items() if k.endswith("_sum_m3")]
    total = ig.get("total_m3")
    if not B._num(total) or not parts or not _tol_sum(sum(parts), total):
        raise FillError(f"{name}: restated safety line needs an ignored_small total equal to its parts "
                        f"({parts} vs {total})")
    want = max(B.SAFETY_MIN_M3, float(total))
    if n.get("unit") != "m3" or n.get("label") != "SAFETY" or not B._same(n.get("after"), round(want, 6)):
        raise FillError(f"{name}: restated safety line {n.get('after')} is not max(1 m3, {total})")
    hits = [ln for ln in base_lines if ln["item_code"] == n["item_code"] and ln["unit"] == "m3"]
    hits = [ln for ln in hits if _base_view(ln, view)["class"] == "RELEASED"
            and _base_view(ln, view)["label"] == "SAFETY"]
    if len(hits) != 1 or not B._same(_base_view(hits[0], view)["net"], before):
        raise FillError(f"{name}: restated safety line before {before} binds {len(hits)} base safety line(s) "
                        f"{[_base_view(h, view)['net'] for h in hits]}")
    ln = hits[0]
    return {"line_id": ln["line_id"], "item_code": n["item_code"], "unit": "m3",
            "element_id": _base_view(ln, view)["element_id"],
            "before": {"class": "RELEASED", "net": before, "low": None, "high": None},
            "after": {"class": "RELEASED", "net": n["after"]}, "label": "SAFETY",
            "basis": f"{n['basis']} [restated safety line, {RULE_V3} n]"}


def prepare(pkg, base_lines, view="index"):
    """URBAN_FILL_PACKAGE_V3 -> (URBAN_FILL_PACKAGE_V1 that arch_v3081 applies, NOT_APPLICABLE rows, report)."""
    if not isinstance(pkg, dict) or pkg.get("schema") != PACKAGE_SCHEMA:
        raise FillError(f"package schema {pkg.get('schema') if isinstance(pkg, dict) else type(pkg)} is not "
                        f"{PACKAGE_SCHEMA}")
    if pkg.get("base") != EXTENDS:
        raise FillError(f"package built for {pkg.get('base')}, base is {EXTENDS}")
    names = list(pkg.get("set_names") or [])
    raw = list(pkg.get("sets") or [])
    if len(names) != len(raw) or len(set(names)) != len(names):
        raise FillError(f"set_names {names} do not name the {len(raw)} sets once each")
    carry = dict(pkg.get("carry") or {})
    fixes = dict(pkg.get("basis_corrections") or {})
    report = {"carried": {}, "not_applicable_rows": [], "restated_safety": [], "basis_corrections": [],
              "source_schemas": {}}
    sets, na = [], []
    for name, doc in zip(names, raw):
        s = _normalise(doc, name)
        report["source_schemas"][name] = s.get("source_schema", s["schema"])
        rows = s.get("rows") or []
        if name in carry:
            want = list(carry[name])
            have = {r.get("line_id") for r in rows}
            if not want or set(want) - have:
                raise FillError(f"{name}: carried line(s) the set has no row for: {sorted(set(want) - have)}")
            rows = [r for r in rows if r.get("line_id") in set(want)]
            s["new_lines"] = []
            s.pop("safety_line", None)
            report["carried"][name] = want
        keep = []
        for r in rows:
            r = copy.deepcopy(r)
            lid = r.get("line_id")
            if lid in fixes:
                f = fixes[lid]
                if not str(f.get("source") or "").strip() or str(r.get("basis", "")).count(f["old"]) != 1:
                    raise FillError(f"{lid}: basis correction needs a source and its old text once in the basis")
                r["basis"] = r["basis"].replace(f["old"], f["new"]) + f" [basis text corrected: {f['source']}, " \
                                                                     f"{RULE_V3} o]"
                report["basis_corrections"].append({"line_id": lid, "old": f["old"], "new": f["new"],
                                                    "source": f["source"]})
            a = r.get("after") or {}
            if a.get("class") == "EXCLUDED":
                if r.get("label") != NOT_APPLICABLE or a.get("reason") != NA_STATE \
                        or not str(r.get("basis") or "").strip():
                    raise FillError(f"{lid}: an EXCLUDED row is only NOT_APPLICABLE with its evidence")
                r["set"] = r.get("set") or name
                r["set_doc"] = name
                na.append(r)
                report["not_applicable_rows"].append({"set": name, "line_id": lid, "item_code": r["item_code"]})
                continue
            keep.append(r)
        s["rows"] = keep
        if s.get("safety_line"):
            sr = _safety_row(s, name, base_lines, view)
            if sr is not None:
                sr["set"] = name
                s["rows"].append(sr)
                report["restated_safety"].append({"set": name, "line_id": sr["line_id"],
                                                  "before": sr["before"]["net"], "after": sr["after"]["net"]})
        sets.append(s)
    missing = sorted(set(fixes) - {x["line_id"] for x in report["basis_corrections"]})
    if missing or set(carry) - set(names):
        raise FillError(f"basis corrections / carries naming no row or set: {missing} {sorted(set(carry) - set(names))}")
    v2 = {"schema": A82.PACKAGE_SCHEMA, "method": A82.METHOD, "base": A82.EXTENDS,
          "row_bases": list(pkg.get("row_bases") or []) + [EXTENDS], "defer": dict(pkg.get("defer") or {}),
          "sets": sets}
    v1, stack = A82.stack_package(v2, base_lines, view)
    v1 = dict(v1, method=METHOD, base=EXTENDS)
    report["stack"] = stack
    na_ids = [r["line_id"] for r in na]
    if len(set(na_ids)) != len(na_ids):
        raise FillError("two NOT_APPLICABLE rows for one line")
    rows, _ = B.check_package(v1, EXTENDS)
    both = sorted(set(na_ids) & set(rows))
    if both:
        raise FillError(f"{both[:3]}: a line with a figure row and a NOT_APPLICABLE row")
    return v1, na, report


def _bind_na(ln, r, view):
    st = _base_view(ln, view)
    if ln["item_code"] != r["item_code"] or ln["unit"] != r["unit"]:
        raise FillError(f"{r['line_id']}: base {ln['item_code']} {ln['unit']}, row {r['item_code']} {r['unit']} (stale)")
    if r.get("element_id") is not None and str(st.get("element_id") or "") != str(r["element_id"]):
        raise FillError(f"{r['line_id']}: base element {st.get('element_id')}, row {r['element_id']} (stale)")
    b = r.get("before") or {}
    if st["class"] != b.get("class") or not all(B._same(st[k], b.get(k)) for k in ("net", "low", "high")):
        raise FillError(f"{r['line_id']}: base {st['class']} {st['net']} {st['low']}..{st['high']}, row read "
                        f"{b.get('class')} {b.get('net')} {b.get('low')}..{b.get('high')} (stale)")
    if st["class"] != "HELD":
        raise FillError(f"{r['line_id']}: NOT_APPLICABLE only on a HELD line, base is {st['class']}")


def _na_reason(r):
    return f"{NA_STATE} ({RULE_V3} m): {r['basis']}"


def apply_index(index_doc, pkg):
    """the index view: (new index doc, applied rows incl. NOT_APPLICABLE, report)."""
    v1, na, report = prepare(pkg, index_doc["lines"], "index")
    new, applied = B.apply_index(index_doc, v1, EXTENDS, METHOD)
    by = {ln["line_id"]: ln for ln in new["lines"]}
    for r in na:
        ln = by.get(r["line_id"])
        if ln is None:
            raise FillError(f"{r['line_id']}: no such line in the base")
        _bind_na(ln, r, "index")
        ln.update({"class": "EXCLUDED", "measured_net": None, "held_low": None, "held_high": None,
                   "excluded_reason": _na_reason(r), "method_label": NOT_APPLICABLE, "fill_basis": r["basis"]})
        applied.append(r)
    names = {r["line_id"] for r in applied}
    B._assert_outside(index_doc["lines"], new["lines"], names, len(new["lines"]) - len(index_doc["lines"]))
    new["fill"] = dict(new["fill"], rule=RULES, policy=POLICY_ID, rows=len(applied), not_applicable_rows=len(na),
                       deferred=len(report["stack"]["deferred"]))
    return new, applied, report


def apply_boq_lines(lines, pkg):
    """the BOQ-line view: (new lines, applied rows incl. NOT_APPLICABLE, added {id: line}, report)."""
    v1, na, report = prepare(pkg, lines, "boq")
    rows, added = B.check_package(v1, EXTENDS)
    if any(r["after"]["class"] == "IGNORED_SMALL" for r in rows.values()):
        raise FillError("a V3.0.83 package carries no ignored-small piece (the one safety line is restated, n)")
    plain = copy.deepcopy(v1)
    for s in plain["sets"]:
        s["new_lines"] = []
        s.pop("safety_line", None)
    new, applied = B.apply_boq_lines(lines, plain, EXTENDS)
    by = {ln["line_id"]: ln for ln in new}
    for r in na:
        ln = by.get(r["line_id"])
        if ln is None:
            raise FillError(f"{r['line_id']}: no such line in the base")
        _bind_na(ln, r, "boq")
        ln["evidence_state"], ln["measured_net"], ln["bounded_range"] = NA_STATE, None, None
        if "gross" in ln:
            ln["gross"] = None
        ln["notes"] = _na_reason(r)
        ln["method_label"], ln["fill_basis"] = NOT_APPLICABLE, r["basis"]
        applied.append(r)
    seen = set(by)
    clash = sorted(set(added) & seen)
    if clash:
        raise FillError(f"added line id already in the base: {clash[:3]}")
    for lid, x in sorted(added.items()):
        ln = A82._boq_added(x, lid, A82._template(lines, x["item_code"], x["unit"]))
        ln["rule"] = dict(ln.get("rule") or {}, rule_id=RULE_V3, version=METHOD)
        new.append(ln)
    B._assert_outside(lines, new, {r["line_id"] for r in applied}, len(added))
    return new, applied, added, report


def diff_rows(applied, added=()):
    figs = [r for r in applied if r["after"].get("class") != "EXCLUDED" or r.get("label") != NOT_APPLICABLE]
    out = B.diff_rows(figs, added)
    for r in sorted((r for r in applied if r not in figs), key=lambda r: r["line_id"]):
        out.append({"line_id": r["line_id"], "set": r.get("set"), "item_code": r["item_code"], "unit": r["unit"],
                    "element_id": r.get("element_id"), "before_class": r["before"].get("class"),
                    "before_net": r["before"].get("net"), "before_low": r["before"].get("low"),
                    "before_high": r["before"].get("high"), "after_class": "EXCLUDED", "after_net": None,
                    "after_low": None, "after_high": None, "label": NOT_APPLICABLE, "basis": _na_reason(r)})
    return sorted(out, key=lambda d: d["line_id"])


def write(out, base_lines, pkg):
    """the hub's V3_0_83_* files beside the base candidate's files. -> (file names, identity)."""
    import csv
    import io
    from pathlib import Path
    from engine.source import arch_v30 as A30
    from engine.source import boq_line as BL
    out = Path(out)
    new, applied, added, report = apply_boq_lines(base_lines, pkg)
    for ln in new[len(base_lines):]:
        BL.validate(ln)
    d = diff_rows(applied, added)
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(d[0]), lineterminator="\n")
    w.writeheader()
    w.writerows(d)
    by_set = {}
    for r in applied:
        k = r.get("set_doc") or r.get("set") or "-"
        by_set[k] = by_set.get(k, 0) + 1
    ident = {"base_lines": len(base_lines), "v3_0_83_lines": len(new), "applied": len(applied), "added": len(added),
             "by_set": by_set, "not_applicable_rows": len(report["not_applicable_rows"]),
             "deferred": len(report["stack"]["deferred"]), "outside_rows_identical_to_base": True}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "rule": RULES, "released_default": False,
           "identity": ident, "report": report}
    files = {"V3_0_83_BOQ_LINES.json": BL.dumps(new), "V3_0_83_BOQ_LINES.csv": A30._lines_csv(new),
             "V3_0_83_DIFF.csv": buf.getvalue(), "V3_0_83_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident


def policy_record():
    return dict(A82.policy_record(), policy_id=POLICY_ID, method=METHOD, extends=EXTENDS, rule=RULES,
                package_schema=PACKAGE_SCHEMA)


def canon(x):
    return json.dumps(x, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
