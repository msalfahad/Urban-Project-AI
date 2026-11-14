"""ARCH_TAKEOFF_V3.0.84 (T-770 r7, lane I, DELIVERY MODE wiring package): the SAME opt-in BOQ candidate as
ARCH_TAKEOFF_V3.0 .. V3.0.83, extended with FILL_WIRE_V4 = FILL_WIRE_V3 (engine.source.arch_v3083, R-T770-1 .. -4,
unchanged and called as is) + R-T770-5 below. Nothing here measures, invents or chooses a quantity: the
Checker-verified fix-row sets carry every figure, label and basis; a carrier-derived line is the sum the set's own
basis names, taken on the wired candidate (the Checker's 'recompute at wiring').

R-T770-5 (every villa; the T-766 / T-768 / T-771 set shapes):
  (p) a set that lists its rows under rows_detail (rows = their count) is read as rows = rows_detail; the count must
      agree; a rows_detail entry with action ADD and no before is an ADDED line of that set;
  (q) an added entry without an alias takes "NEW:<element id>" (so two added lines of one item code in one set keep
      two ids); the FILL_WIRE_V1 id rule (arch_v3081.new_line_id) is kept;
  (r) a NOT_APPLICABLE row whose after is EXCLUDED with a reason other than NOT_APPLICABLE_WITH_EVIDENCE (a form
      alternative, 'not a threshold', 'carried by <line>', ...) binds its line as R-T770-4 (m) does (HELD lines only,
      before re-read) and makes it EXCLUDED_WITH_REASON with that reason and its basis: never 0, never additive with
      the form it is the alternative of; a row without a reason or a basis stops the run;
  (s) an added entry with low .. high and no figure (a range the set could not close) is added as a HELD line with
      that range (BOUNDED_EXPOSURE in the BOQ view), never 0; an OPTIONAL entry says so in its basis and stays a range;
  (t) a CARRIER line named by the package (element id -> carrier item code, unit, an optional printed addition and its
      source) takes the sum of the carrier's RELEASED lines in the wired candidate (+ the addition): computed after
      every row of the package is applied, so a carrier the same package fills counts with its new figures; a carrier
      with a HELD line stops the run (the line is deferred by name instead); the set's own figure is kept in the
      basis beside the recomputed one;
  (u) an added entry the package DEFERS by element id with a reason is recorded and never written as a line or as 0.

Nothing here names a project, a sheet, a layer or a coordinate.
"""

from __future__ import annotations

import copy
import json

from engine.source import arch_v3081 as B
from engine.source import arch_v3082 as A82
from engine.source import arch_v3083 as A83

METHOD = "ARCH_TAKEOFF_V3.0.84"
EXTENDS = "ARCH_TAKEOFF_V3.0.83"
POLICY_ID = "URBAN_BOQ_T770_ARCH_V3_0_84"
RULE_V5 = "R-T770-5"
RULES = A83.RULES + [RULE_V5]
PACKAGE_SCHEMA = "URBAN_FILL_PACKAGE_V4"
NA_STATE = A83.NA_STATE
EXCLUDED_STATE = "EXCLUDED_WITH_REASON"
NOT_APPLICABLE = A83.NOT_APPLICABLE
FillError = B.FillError


def _alias(n):
    if n.get("line_id") or n.get("proposed_id"):
        return n.get("line_id") or n.get("proposed_id")
    if not str(n.get("element_id") or "").strip():
        raise FillError(f"{n.get('item_code')}: an added entry without an alias needs an element id ({RULE_V5} q)")
    return f"NEW:{n['element_id']}"


def _rows_detail(doc, name):
    """R-T770-5 (p)."""
    s = copy.deepcopy(doc)
    if "rows_detail" not in s:
        return s
    det = list(s.pop("rows_detail") or [])
    n = s.get("rows")
    if not isinstance(n, int) or n != len(det):
        raise FillError(f"{name}: rows count {n} does not match {len(det)} rows_detail entries")
    rows, adds = [], list(s.get("new_lines") or [])
    for r in det:
        if r.get("action") == "ADD":
            if r.get("before") is not None:
                raise FillError(f"{name}: an ADD entry reads a before ({r.get('element_id')})")
            x = {k: r[k] for k in ("item_code", "unit", "element_id", "after", "label", "basis") if k in r}
            adds.append(x)
        elif r.get("action") is not None:
            raise FillError(f"{name}: rows_detail action {r.get('action')} is not ADD")
        else:
            rows.append(r)
    s["rows"], s["new_lines"] = rows, adds
    return s


def _late(n, name, kind, extra=None):
    alias = _alias(n)
    x = {"set": name, "line_id": alias, "item_code": n["item_code"], "unit": n["unit"], "label": n["label"],
         "basis": n["basis"], "element_id": n.get("element_id"), "kind": kind,
         "new_line_id": B.new_line_id(name, alias, n["item_code"], n["unit"])}
    if n.get("label") not in B.LABELS or not str(n.get("basis") or "").strip():
        raise FillError(f"{name} {alias}: label {n.get('label')} / empty basis")
    if extra:
        x.update(extra)
    return x


def prepare(pkg, base_lines, view="index"):
    """URBAN_FILL_PACKAGE_V4 -> (URBAN_FILL_PACKAGE_V3 for arch_v3083, excluded-with-reason rows, late adds, report)."""
    if not isinstance(pkg, dict) or pkg.get("schema") != PACKAGE_SCHEMA:
        raise FillError(f"package schema {pkg.get('schema') if isinstance(pkg, dict) else type(pkg)} is not "
                        f"{PACKAGE_SCHEMA}")
    if pkg.get("base") != EXTENDS:
        raise FillError(f"package built for {pkg.get('base')}, base is {EXTENDS}")
    names = list(pkg.get("set_names") or [])
    raw = list(pkg.get("sets") or [])
    if len(names) != len(raw) or len(set(names)) != len(names):
        raise FillError(f"set_names {names} do not name the {len(raw)} sets once each")
    carriers = dict(pkg.get("carriers") or {})
    defer_added = dict(pkg.get("defer_added") or {})
    for el, why in defer_added.items():
        if not str(why or "").strip():
            raise FillError(f"{el}: a deferred added line needs a reason ({RULE_V5} u)")
    report = {"rows_detail_sets": [], "excluded_with_reason": [], "ranged_added": [], "carrier_added": [],
              "deferred_added": []}
    sets, xr, late = [], [], []
    for name, doc in zip(names, raw):
        s = _rows_detail(doc, name)
        if "rows_detail" in doc:
            report["rows_detail_sets"].append(name)
        keep = []
        for r in s.get("rows") or []:
            a = r.get("after") or {}
            if a.get("class") == "EXCLUDED" and a.get("reason") != NA_STATE:
                reason = str(a.get("reason") or "").strip()
                if r.get("label") != NOT_APPLICABLE or not reason or not str(r.get("basis") or "").strip():
                    raise FillError(f"{r.get('line_id')}: an EXCLUDED row needs label NOT_APPLICABLE, a reason and "
                                    f"a basis ({RULE_V5} r)")
                r = dict(copy.deepcopy(r), set=r.get("set") or name, set_doc=name)
                xr.append(r)
                report["excluded_with_reason"].append({"set": name, "line_id": r["line_id"],
                                                       "item_code": r["item_code"], "reason": reason})
                continue
            keep.append(r)
        s["rows"] = keep
        adds = []
        for n in s.get("new_lines") or []:
            n = copy.deepcopy(n)
            el = n.get("element_id")
            if el in defer_added:
                report["deferred_added"].append({"set": name, "element_id": el, "item_code": n.get("item_code"),
                                                 "set_figure": n.get("net"), "reason": defer_added[el]})
                continue
            if el in carriers:
                c = carriers[el]
                if not (isinstance(c.get("carrier"), list) and len(c["carrier"]) == 2) or c["carrier"][1] != n["unit"]:
                    raise FillError(f"{el}: carrier {c.get('carrier')} is not [item code, {n.get('unit')}]")
                plus = c.get("plus", 0.0)
                if not B._num(plus) or plus < 0 or (plus and not str(c.get("plus_source") or "").strip()):
                    raise FillError(f"{el}: a carrier addition needs a figure >= 0 and its source")
                late.append(_late(n, name, "carrier", {"carrier": list(c["carrier"]), "plus": float(plus),
                                                       "plus_source": c.get("plus_source"),
                                                       "set_figure": n.get("net")}))
                continue
            if "after" not in n and n.get("net") is None and ("low" in n or "high" in n):
                lo, hi = n.get("low"), n.get("high")
                if not (B._num(lo) and B._num(hi)) or lo < 0 or lo > hi:
                    raise FillError(f"{el}: a ranged added entry needs 0 <= low <= high, got {lo} .. {hi}")
                late.append(_late(n, name, "ranged", {"low": float(lo), "high": float(hi),
                                                      "optional": bool(n.get("optional"))}))
                continue
            if not (n.get("line_id") or n.get("proposed_id")):
                n["line_id"] = _alias(n)
            adds.append(n)
        s["new_lines"] = adds
        sets.append(s)
    for k, what in ((set(carriers), "carrier"), (set(defer_added), "deferred added line")):
        seen = {x["element_id"] for x in late if x["kind"] == "carrier"} if what == "carrier" else \
            {d["element_id"] for d in report["deferred_added"]}
        if k - seen:
            raise FillError(f"{what}(s) naming no added entry: {sorted(k - seen)}")
    for x in late:
        report[f"{x['kind']}_added"].append({"set": x["set"], "element_id": x["element_id"], "item_code": x["item_code"],
                                             "line_id": x["new_line_id"]})
    ids = [x["new_line_id"] for x in late]
    if len(set(ids)) != len(ids):
        raise FillError("two late added lines with one id")
    v3 = {"schema": A83.PACKAGE_SCHEMA, "method": A83.METHOD, "base": A83.EXTENDS,
          "row_bases": list(pkg.get("row_bases") or []) + [EXTENDS], "set_names": names,
          "carry": dict(pkg.get("carry") or {}), "basis_corrections": dict(pkg.get("basis_corrections") or {}),
          "defer": dict(pkg.get("defer") or {}), "sets": sets}
    xr_ids = [r["line_id"] for r in xr]
    if len(set(xr_ids)) != len(xr_ids):
        raise FillError("two EXCLUDED rows for one line")
    return v3, xr, late, report


def _xr_reason(r):
    return f"{EXCLUDED_STATE} ({r['after']['reason']}, {RULE_V5} r): {r['basis']}"


def _carrier_sum(lines, code, unit, view):
    tot, held = 0.0, []
    for ln in lines:
        if ln["item_code"] != code or ln["unit"] != unit:
            continue
        c = ln["class"] if view == "index" else B.line_class(ln)
        if c == "RELEASED":
            tot += float(ln["measured_net"])
        elif c == "HELD":
            held.append(ln["line_id"])
    if held:
        raise FillError(f"carrier {code} [{unit}] has {len(held)} HELD line(s) {held[:3]}: not closed, defer the "
                        f"carrier-derived line by name ({RULE_V5} t / u)")
    return B._r(tot)


def _resolve_late(late, lines, view):
    out = []
    for x in late:
        x = dict(x)
        if x["kind"] == "carrier":
            code, unit = x["carrier"]
            tot = _carrier_sum(lines, code, unit, view)
            x["net"] = B._r(tot + x["plus"])
            add = f" + {x['plus']} ({x['plus_source']})" if x["plus"] else ""
            x["basis"] = (f"{x['basis']} [recomputed at wiring ({RULE_V5} t): carrier {code} [{unit}] RELEASED sum "
                          f"{tot}{add} = {x['net']} on {METHOD}; set figure {x['set_figure']}]")
        else:
            x["basis"] = (f"{x['basis']} [range {x['low']} .. {x['high']} kept HELD ({RULE_V5} s)"
                          + ("; OPTIONAL item" if x["optional"] else "") + "]")
        out.append(x)
    return out


def apply_index(index_doc, pkg):
    """the index view: (new index doc, applied rows, late added lines, report)."""
    v3, xr, late, report = prepare(pkg, index_doc["lines"], "index")
    new, applied, rep3 = A83.apply_index(index_doc, v3)
    report["v3"] = rep3
    by = {ln["line_id"]: ln for ln in new["lines"]}
    for r in xr:
        ln = by.get(r["line_id"])
        if ln is None:
            raise FillError(f"{r['line_id']}: no such line in the base")
        A83._bind_na(ln, r, "index")
        ln.update({"class": "EXCLUDED", "measured_net": None, "held_low": None, "held_high": None,
                   "excluded_reason": _xr_reason(r), "method_label": NOT_APPLICABLE, "fill_basis": r["basis"]})
        applied.append(r)
    late = _resolve_late(late, new["lines"], "index")
    clash = sorted({x["new_line_id"] for x in late} & set(by))
    if clash:
        raise FillError(f"added line id already in the candidate: {clash[:3]}")
    for x in late:
        ranged = x["kind"] == "ranged"
        new["lines"].append({"binding": None, "class": "HELD" if ranged else "RELEASED",
                             "element_id": f"{x['set']}:{x['line_id']}",
                             "held_high": B._r(x["high"]) if ranged else None,
                             "held_low": B._r(x["low"]) if ranged else None, "item_code": x["item_code"],
                             "line_id": x["new_line_id"], "measured_net": None if ranged else x["net"],
                             "unbound_records": [], "unit": x["unit"], "method_label": x["label"],
                             "fill_basis": x["basis"], "added_by": RULE_V5})
    n_added = len(new["lines"]) - len(index_doc["lines"])
    B._assert_outside(index_doc["lines"], new["lines"], {r["line_id"] for r in applied}, n_added)
    new["candidate_version"], new["extends"] = METHOD, EXTENDS
    new["fill"] = dict(new["fill"], rule=RULES, policy=POLICY_ID, rows=len(applied),
                       excluded_with_reason=len(xr), late_added=len(late))
    return new, applied, late, report


def apply_boq_lines(lines, pkg):
    """the BOQ-line view: (new lines, applied rows, added {id: line} (FILL_WIRE_V3 adds), late adds, report)."""
    v3, xr, late, report = prepare(pkg, lines, "boq")
    new, applied, added, rep3 = A83.apply_boq_lines(lines, v3)
    report["v3"] = rep3
    for ln in new[len(lines):]:
        ln["rule"] = dict(ln.get("rule") or {}, rule_id=RULE_V5, version=METHOD)
    by = {ln["line_id"]: ln for ln in new}
    for r in xr:
        ln = by.get(r["line_id"])
        if ln is None:
            raise FillError(f"{r['line_id']}: no such line in the base")
        A83._bind_na(ln, r, "boq")
        ln["evidence_state"], ln["measured_net"], ln["bounded_range"] = EXCLUDED_STATE, None, None
        if "gross" in ln:
            ln["gross"] = None
        ln["notes"] = _xr_reason(r)
        ln["method_label"], ln["fill_basis"] = NOT_APPLICABLE, r["basis"]
        applied.append(r)
    late = _resolve_late(late, new, "boq")
    clash = sorted({x["new_line_id"] for x in late} & set(by))
    if clash:
        raise FillError(f"added line id already in the candidate: {clash[:3]}")
    for x in late:
        ranged = x["kind"] == "ranged"
        y = {"set": x["set"], "line_id": x["line_id"], "item_code": x["item_code"], "unit": x["unit"],
             "label": x["label"], "basis": x["basis"], "after": {"class": "RELEASED", "net": 0.0 if ranged else x["net"]}}
        ln = A82._boq_added(y, x["new_line_id"], A82._template(lines, x["item_code"], x["unit"]))
        if ranged:
            ln["evidence_state"], ln["measured_net"] = B.BOUNDED, None
            ln["bounded_range"] = {"low": B._r(x["low"]), "high": B._r(x["high"]), "rule": RULE_V5}
        ln["rule"] = dict(ln.get("rule") or {}, rule_id=RULE_V5, version=METHOD)
        new.append(ln)
    B._assert_outside(lines, new, {r["line_id"] for r in applied}, len(new) - len(lines))
    return new, applied, added, late, report


def diff_rows(applied, added=(), late=()):
    xr = [r for r in applied if (r.get("after") or {}).get("class") == "EXCLUDED"
          and (r["after"].get("reason") or NA_STATE) != NA_STATE]
    out = A83.diff_rows([r for r in applied if r not in xr], added)
    for r in sorted(xr, key=lambda r: r["line_id"]):
        out.append({"line_id": r["line_id"], "set": r.get("set"), "item_code": r["item_code"], "unit": r["unit"],
                    "element_id": r.get("element_id"), "before_class": r["before"].get("class"),
                    "before_net": r["before"].get("net"), "before_low": r["before"].get("low"),
                    "before_high": r["before"].get("high"), "after_class": "EXCLUDED", "after_net": None,
                    "after_low": None, "after_high": None, "label": NOT_APPLICABLE, "basis": _xr_reason(r)})
    for x in late:
        ranged = x["kind"] == "ranged"
        out.append({"line_id": x["new_line_id"], "set": x["set"], "item_code": x["item_code"], "unit": x["unit"],
                    "element_id": f"{x['set']}:{x['line_id']}", "before_class": "ADDED", "before_net": None,
                    "before_low": None, "before_high": None, "after_class": "HELD" if ranged else "RELEASED",
                    "after_net": None if ranged else x["net"], "after_low": x.get("low") if ranged else None,
                    "after_high": x.get("high") if ranged else None, "label": x["label"], "basis": x["basis"]})
    return sorted(out, key=lambda d: d["line_id"])


def write(out, base_lines, pkg):
    """the hub's V3_0_84_* files beside the base candidate's files. -> (file names, identity)."""
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
    ident = {"base_lines": len(base_lines), "v3_0_84_lines": len(new), "applied": len(applied),
             "added": len(added) + len(late), "by_set": by_set,
             "excluded_with_reason": len(report["excluded_with_reason"]),
             "deferred_added": len(report["deferred_added"]), "outside_rows_identical_to_base": True}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "rule": RULES, "released_default": False,
           "identity": ident, "report": report}
    files = {"V3_0_84_BOQ_LINES.json": BL.dumps(new), "V3_0_84_BOQ_LINES.csv": A30._lines_csv(new),
             "V3_0_84_DIFF.csv": buf.getvalue(), "V3_0_84_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident


def policy_record():
    return dict(A83.policy_record(), policy_id=POLICY_ID, method=METHOD, extends=EXTENDS, rule=RULES,
                package_schema=PACKAGE_SCHEMA)


def canon(x):
    return json.dumps(x, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
