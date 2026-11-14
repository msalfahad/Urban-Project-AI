"""ARCH_TAKEOFF_V3.0.82 (T-770 r5, lane I, DELIVERY MODE wiring package): the SAME opt-in BOQ candidate as
ARCH_TAKEOFF_V3.0 .. V3.0.81, extended with FILL_WIRE_V2 = FILL_WIRE_V1 (engine.source.arch_v3081, R-T770-1 /
R-T770-2, unchanged and called as is) + R-T770-3 below. Nothing here measures, invents or chooses a quantity: the
Checker-verified fix-row sets carry every figure, label and basis.

R-T770-3 (every villa; T-776 restates lines that T-764 / T-767 / T-769 / T-761 / T-762 / T-757 filled first):
  (h) a STACKED row (its before names the fix row it restates: {"fix_row": <task>, "net": x, "label": L}) binds
      either (1) to the row of that task for the same line in the SAME package: the earlier row's after must be
      RELEASED with net x and label L; the two compose into ONE row (the earlier row's before, the stacked row's
      after / label / basis, the basis naming the restated row) and the earlier row leaves its set (never applied
      twice, never two rows for one line), or (2) to the base line when the base already carries that figure: class
      RELEASED, measured_net x, method_label L; the row then binds the base state. Anything else (the restated task's
      row neither in the package nor in the base) stops the run unless the package DEFERS that line by name with a
      reason (a deferred row is never applied; its line stays exactly as the base has it);
  (i) an ADDED line is accepted in either row shape (line_id or proposed_id = "NEW:..."; after or net); a set's added
      line without an alias takes "NEW:<item code>"; an added entry labelled NOT_APPLICABLE with no figure is RECORDED
      in the package (not_applicable) and never written as a line or as 0; any other added entry without a figure
      stops the run;
  (j) in the BOQ-line view an added line takes the shape of the first base line of the same item code, else of the
      same unit (it is a new line: evidence PROVISIONAL unless MEASURED, its own element id, no room, no inputs).

Added-line ids keep the FILL_WIRE_V1 id rule (arch_v3081.new_line_id), so a line keeps its id in later V3.0.x rounds.
Nothing here names a project, a sheet, a layer or a coordinate.
"""

from __future__ import annotations

import copy
import json

from engine.source import arch_v3081 as B

METHOD = "ARCH_TAKEOFF_V3.0.82"
EXTENDS = "ARCH_TAKEOFF_V3.0.81"
POLICY_ID = "URBAN_BOQ_T770_ARCH_V3_0_82"
RULE_STACK = "R-T770-3"
RULES = [B.RULE, B.RULE_NET, RULE_STACK]
PACKAGE_SCHEMA = "URBAN_FILL_PACKAGE_V2"
NOT_APPLICABLE = "NOT_APPLICABLE"
FillError = B.FillError


def _is_stacked(r):
    b = r.get("before") or {}
    return isinstance(b, dict) and "fix_row" in b


def _added(n, set_name):
    """R-T770-3 (i): one added entry -> the FILL_WIRE_V1 shape, or None for a recorded NOT_APPLICABLE."""
    n = copy.deepcopy(n)
    alias = n.get("line_id") or n.get("proposed_id") or f"NEW:{n.get('item_code')}"
    if "after" not in n:
        net = n.get("net")
        if net is None:
            if n.get("label") == NOT_APPLICABLE:
                return None
            raise FillError(f"{set_name} {alias}: an added line without a figure is not NOT_APPLICABLE")
        n["after"] = {"class": "RELEASED", "net": net}
    out = {k: n[k] for k in ("item_code", "unit", "after", "label", "basis") if k in n}
    out["line_id"] = alias
    if n.get("family"):
        out["family"] = n["family"]
    return out


def _base_state(ln, view):
    if view == "index":
        return {"class": ln["class"], "net": ln.get("measured_net"), "low": ln.get("held_low"),
                "high": ln.get("held_high"), "label": ln.get("method_label")}
    c = B.line_class(ln)
    return {"class": c, "net": ln.get("measured_net") if c == "RELEASED" else None, "low": None, "high": None,
            "label": ln.get("method_label")}


def stack_package(pkg, base_lines, view="index"):
    """URBAN_FILL_PACKAGE_V2 -> (an URBAN_FILL_PACKAGE_V1 package arch_v3081 applies as is, report). R-T770-3 h / i."""
    if not isinstance(pkg, dict) or pkg.get("schema") != PACKAGE_SCHEMA:
        raise FillError(f"package schema {pkg.get('schema') if isinstance(pkg, dict) else type(pkg)} is not "
                        f"{PACKAGE_SCHEMA}")
    if pkg.get("base") != EXTENDS:
        raise FillError(f"package built for {pkg.get('base')}, base is {EXTENDS}")
    defer = dict(pkg.get("defer") or {})
    for lid, why in defer.items():
        if not str(why or "").strip():
            raise FillError(f"{lid}: a deferred line needs a reason")
    by = {ln["line_id"]: ln for ln in base_lines}
    sets = [copy.deepcopy(s) for s in pkg.get("sets") or []]
    names = [s.get("task") or s.get("set") or "-" for s in sets]
    if len(set(names)) != len(names):
        raise FillError(f"two sets with one name: {names}")
    report = {"stacked_on_row": [], "stacked_on_base": [], "deferred": [], "not_applicable": []}
    for i, s in enumerate(sets):
        keep = []
        for r in s.get("rows") or []:
            if not _is_stacked(r):
                keep.append(r)
                continue
            lid, b = r.get("line_id"), r["before"]
            if lid in defer:
                report["deferred"].append({"set": names[i], "line_id": lid, "item_code": r.get("item_code"),
                                           "restates": b.get("fix_row"), "reason": defer[lid]})
                continue
            prior = [(j, x) for j, t in enumerate(sets) if j != i and names[j] == b.get("fix_row")
                     for x in (t.get("rows") or []) if x.get("line_id") == lid]
            if prior:
                j, x = prior[0]
                xa = x.get("after") or {}
                if _is_stacked(x) or xa.get("class") != "RELEASED" or not B._same(xa.get("net"), b.get("net")) \
                        or x.get("label") != b.get("label"):
                    raise FillError(f"{lid}: stacked on {b.get('fix_row')} {b.get('net')} {b.get('label')}, that row "
                                    f"reads {xa.get('class')} {xa.get('net')} {x.get('label')} (stale)")
                sets[j]["rows"] = [y for y in sets[j]["rows"] if y is not x]
                r = dict(r, before=copy.deepcopy(x["before"]),
                         basis=f"{r['basis']} [restates {b['fix_row']} {b['net']} {b['label']}, {RULE_STACK} h]")
                report["stacked_on_row"].append({"set": names[i], "line_id": lid, "restates": b["fix_row"],
                                                 "restated_net": b["net"], "after": r["after"].get("net")})
                keep.append(r)
                continue
            ln = by.get(lid)
            st = _base_state(ln, view) if ln is not None else None
            if st and st["class"] == "RELEASED" and B._same(st["net"], b.get("net")) and st["label"] == b.get("label"):
                r = dict(r, before={"class": "RELEASED", "net": st["net"], "low": None, "high": None},
                         basis=f"{r['basis']} [restates {b['fix_row']} {b['net']} {b['label']} already in the base, "
                               f"{RULE_STACK} h]")
                report["stacked_on_base"].append({"set": names[i], "line_id": lid, "restates": b["fix_row"],
                                                  "restated_net": b["net"], "after": r["after"].get("net")})
                keep.append(r)
                continue
            raise FillError(f"{lid}: stacked on {b.get('fix_row')} {b.get('net')} {b.get('label')}, neither in the "
                            f"package nor in the base ({st}); defer it by name or wire {b.get('fix_row')} first")
        s["rows"] = keep
    for i, s in enumerate(sets):
        adds = []
        for n in list(s.get("new_lines") or []):
            x = _added(n, names[i])
            if x is None:
                report["not_applicable"].append({"set": names[i], "item_code": n.get("item_code"),
                                                 "unit": n.get("unit"), "basis": n.get("basis")})
            else:
                adds.append(x)
        s["new_lines"] = adds
    missing = sorted(set(defer) - {d["line_id"] for d in report["deferred"]})
    if missing:
        raise FillError(f"deferred line(s) no row names: {missing}")
    v1 = {"schema": B.PACKAGE_SCHEMA, "method": METHOD, "base": EXTENDS, "row_bases": list(pkg.get("row_bases") or []),
          "sets": sets}
    return v1, report


def apply_index(index_doc, pkg):
    """the index view: (new index doc, applied rows, report). Base lines not named stay byte-identical."""
    v1, report = stack_package(pkg, index_doc["lines"], "index")
    new, applied = B.apply_index(index_doc, v1, EXTENDS, METHOD)
    new["fill"] = dict(new["fill"], rule=RULES, policy=POLICY_ID, deferred=len(report["deferred"]),
                       not_applicable=len(report["not_applicable"]))
    return new, applied, report


def _template(lines, item_code, unit):
    for ln in lines:
        if ln["item_code"] == item_code:
            return ln
    for ln in lines:
        if ln["unit"] == unit:
            return ln
    raise FillError(f"{item_code} [{unit}]: no base line of that item code or unit to shape an added line on")


def _boq_added(x, lid, template):
    ln = B._boq_added(x, lid, template)
    ln["evidence_state"] = "MEASURED" if x["label"] == "MEASURED" else B.PROVISIONAL
    ln["item_en"] = template.get("item_en") if template["item_code"] == x["item_code"] else x["item_code"]
    ln["rule"] = dict(ln.get("rule") or {}, rule_id=RULE_STACK, version=METHOD)
    return ln


def apply_boq_lines(lines, pkg):
    """the BOQ-line view: (new lines, applied rows, added {id: line}, report)."""
    v1, report = stack_package(pkg, lines, "boq")
    rows, added = B.check_package(v1, EXTENDS)
    safety = {lid for lid, x in added.items()
              if any(r["after"]["class"] == "IGNORED_SMALL" and r["after"].get("covered_by_line_id") == lid
                     for r in rows.values())}
    if safety:
        raise FillError("a V3.0.82 package carries no ignored-small safety line (the one safety line is V3.0.81's)")
    plain = copy.deepcopy(v1)
    for s in plain["sets"]:
        s["new_lines"] = []
        s.pop("safety_line", None)
    new, applied = B.apply_boq_lines(lines, plain, EXTENDS)
    seen = {ln["line_id"] for ln in new}
    clash = sorted(set(added) & seen)
    if clash:
        raise FillError(f"added line id already in the base: {clash[:3]}")
    for lid, x in sorted(added.items()):
        new.append(_boq_added(x, lid, _template(lines, x["item_code"], x["unit"])))
    if len(new) != len(lines) + len(added):
        raise FillError("line count changed")
    return new, applied, added, report


def write(out, base_lines, pkg):
    """the hub's V3_0_82_* files beside the base candidate's files. -> (file names, identity)."""
    import csv
    import io
    from pathlib import Path
    from engine.source import arch_v30 as A30
    from engine.source import boq_line as BL
    out = Path(out)
    new, applied, added, report = apply_boq_lines(base_lines, pkg)
    for ln in new[len(base_lines):]:
        BL.validate(ln)
    d = B.diff_rows(applied, added)
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(d[0]), lineterminator="\n")
    w.writeheader()
    w.writerows(d)
    by_set = {}
    for r in applied:
        by_set[r.get("set") or "-"] = by_set.get(r.get("set") or "-", 0) + 1
    ident = {"base_lines": len(base_lines), "v3_0_82_lines": len(new), "applied": len(applied), "added": len(added),
             "by_set": by_set, "deferred": len(report["deferred"]), "not_applicable": len(report["not_applicable"]),
             "outside_rows_identical_to_base": True}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "rule": RULES, "released_default": False,
           "identity": ident, "stack_report": report}
    files = {"V3_0_82_BOQ_LINES.json": BL.dumps(new), "V3_0_82_BOQ_LINES.csv": A30._lines_csv(new),
             "V3_0_82_DIFF.csv": buf.getvalue(), "V3_0_82_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident


def policy_record():
    return dict(B.policy_record(), policy_id=POLICY_ID, method=METHOD, extends=EXTENDS, rule=RULES,
                package_schema=PACKAGE_SCHEMA)


def canon(x):
    return json.dumps(x, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
