"""ARCH_TAKEOFF_V3.0.88 (T-770 r11, lane I, DELIVERY MODE wiring package): the SAME opt-in BOQ candidate as
ARCH_TAKEOFF_V3.0 .. V3.0.87, one version step on: FILL_WIRE_V7 (engine.source.arch_v3087, R-T770-1 .. -8) unchanged
and called as is, with no new wiring rule. Nothing here measures, invents or chooses a quantity: the Checker-verified
fix-row sets carry every figure, label and basis.

The only thing this module adds is the version step itself (URBAN_FILL_PACKAGE_V8 = an URBAN_FILL_PACKAGE_V7 built
for the V3.0.87 base): the package is re-addressed to FILL_WIRE_V7 with V3.0.86 appended to its row bases, so every
FILL_WIRE_V1 .. V7 check (binding by line id, the before read on the base line, one owner per line, labels, no 0
written, added lines validated) runs unchanged on the V3.0.87 lines.

Nothing here names a project, a sheet, a layer or a coordinate.
"""

from __future__ import annotations

import copy
import json

from engine.source import arch_v3081 as B
from engine.source import arch_v3087 as A87

METHOD = "ARCH_TAKEOFF_V3.0.88"
EXTENDS = "ARCH_TAKEOFF_V3.0.87"
POLICY_ID = "URBAN_BOQ_T770_ARCH_V3_0_88"
RULES = list(A87.RULES)
PACKAGE_SCHEMA = "URBAN_FILL_PACKAGE_V8"
FillError = B.FillError


def prepare(pkg, base_lines=None):
    """URBAN_FILL_PACKAGE_V8 -> (URBAN_FILL_PACKAGE_V7 for arch_v3087, report)."""
    if not isinstance(pkg, dict) or pkg.get("schema") != PACKAGE_SCHEMA:
        raise FillError(f"package schema {pkg.get('schema') if isinstance(pkg, dict) else type(pkg)} is not "
                        f"{PACKAGE_SCHEMA}")
    if pkg.get("base") != EXTENDS:
        raise FillError(f"package built for {pkg.get('base')}, base is {EXTENDS}")
    v7 = {k: copy.deepcopy(v) for k, v in pkg.items() if k not in ("schema", "method", "base", "row_bases")}
    v7.update(schema=A87.PACKAGE_SCHEMA, method=A87.METHOD, base=A87.EXTENDS,
              row_bases=list(pkg.get("row_bases") or []) + [A87.EXTENDS])
    return v7, {}


def apply_index(index_doc, pkg):
    """the index view: (new index doc, applied rows, late added lines, report)."""
    if index_doc.get("candidate_version") not in (None, EXTENDS):
        raise FillError(f"index is {index_doc.get('candidate_version')}, base is {EXTENDS}")
    v7, rep = prepare(pkg, index_doc["lines"])
    base = copy.deepcopy(index_doc)
    base["candidate_version"] = A87.EXTENDS if index_doc.get("candidate_version") else None
    new, applied, late, rep7 = A87.apply_index(base, v7)
    rep.update(rep7)
    new["candidate_version"], new["extends"] = METHOD, EXTENDS
    new["fill"] = dict(new["fill"], rule=RULES, policy=POLICY_ID)
    return new, applied, late, rep


def apply_boq_lines(lines, pkg):
    """the BOQ-line view: (new lines, applied rows, added {id: line}, late adds, report)."""
    v7, rep = prepare(pkg, lines)
    new, applied, added, late, rep7 = A87.apply_boq_lines(lines, v7)
    rep.update(rep7)
    for ln in new[len(lines):]:
        ln["rule"] = dict(ln.get("rule") or {}, version=METHOD)
    return new, applied, added, late, rep


def diff_rows(applied, added=(), late=(), report=None):
    return A87.diff_rows(applied, added, late, report)


def write(out, base_lines, pkg):
    """the hub's V3_0_88_* files beside the base candidate's files. -> (file names, identity)."""
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
    ident = {"base_lines": len(base_lines), "v3_0_88_lines": len(new), "applied": len(applied),
             "added": len(added) + len(late), "by_set": by_set,
             "outside_rows_identical_to_base": True}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "rule": RULES, "released_default": False,
           "identity": ident, "report": report}
    files = {"V3_0_88_BOQ_LINES.json": BL.dumps(new), "V3_0_88_BOQ_LINES.csv": A30._lines_csv(new),
             "V3_0_88_DIFF.csv": buf.getvalue(), "V3_0_88_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident


def policy_record():
    return dict(A87.policy_record(), policy_id=POLICY_ID, method=METHOD, extends=EXTENDS, rule=RULES,
                package_schema=PACKAGE_SCHEMA)


def canon(x):
    return json.dumps(x, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
