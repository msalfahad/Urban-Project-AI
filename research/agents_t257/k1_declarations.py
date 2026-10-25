"""T-257: K1 BOUNDARY DECLARATIONS check (V2 of the T-210 decision-record check). Standard library only; writes nothing.

The K1 test tests/r8_1/test_r8_1_boundaries.py::test_k1_is_stdlib_only_in_r8_1 exempts files through its own
`by_design` dict (file name -> None for the whole module, or the set of third-party packages allowed in it). T-257
adds ONE by_design entry per module whose T-210 record (research/agents_t210/K1_DECISIONS.json) carries the decision
ALLOWED_OUTSIDE_K1 (Checker T-210 verdict, merge dadf8446). The assertion, EXPECTED_MODULES and every threshold of the
K1 test are unchanged.

This check splits the test's by_design into
  R8-era exceptions  the four entries the test carried before any decision record (kernel_ezdxf.py whole module; the
                     shapely-only topology_crosscheck.py, ground_slab_recovery.py, region_recovery.py), each with its
                     addendum in the K1 test's docstring; pinned below and compared with the test as written;
  declarations       every other entry: each must be backed by an ALLOWED_OUTSIDE_K1 record.

It then runs the T-210 record check against the R8-era exceptions only (so every one of the T-210 records keeps
matching a real offender; a declaration never makes its record STALE) and adds the declaration checks:

  DECLARED_WITHOUT_RECORD      a by_design entry (not R8-era) with no T-210 record for its module
  DECLARED_NOT_ALLOWED         a declaration whose record's decision is not ALLOWED_OUTSIDE_K1 (OUTSIDE_K2_GATE: ezdxf
                               outside the K2 route; NOT_REGISTERED_HOLD: pymupdf) - these stay failing until a fix
  DECLARED_WHOLE_MODULE        a declaration of None (whole module exempt): only the R8-era K2 route may be exempt whole
  DECLARATION_PACKAGES_DIFFER  declared package set != the record's packages
  DECLARED_NOT_IMPORTED        a declared package the module does not import (stale declaration)
  NOT_PINNED                   a declared package with no `name==version` line in requirements.txt
  NOT_REGISTERED               a declared package outside the B-5 dependency register
  AMBIGUOUS_FILE_NAME          the K1 test matches by file NAME: a declared name that exists more than once under
                               engine/source would exempt a second module silently
  R8_ERA_CHANGED               the R8-era exceptions in the test differ from the pinned four
  UNDECLARED_ALLOWED           an ALLOWED_OUTSIDE_K1 record with no declaration (the T-257 set is incomplete)
plus every T-210 problem code (UNRECORDED, STALE, PACKAGES_DIFFER, FIELD_MISSING, BAD_DECISION,
NOT_REGISTERED_BUT_ALLOWED, K1_CORE_REACHES_OFFENDER).

    python3 -I research/agents_t257/k1_declarations.py check [--root R] [--record F]   exit 1 on any problem
    python3 -I research/agents_t257/k1_declarations.py remaining [--root R] [--record F]
        the modules the K1 test still fails on after the declarations, in the order the test meets them
"""
from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

if __package__ in (None, ""):                       # run as a script: make `research.` importable from the root
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from research.agents_t210 import k1_boundary as V1   # noqa: E402  (the T-210 tool, read-only reuse)

SCHEMA = "URBAN_K1_DECLARATIONS_CHECK_V2"
R8_ERA = {"kernel_ezdxf.py": None, "topology_crosscheck.py": {"shapely"}, "ground_slab_recovery.py": {"shapely"},
          "region_recovery.py": {"shapely"}}
REQUIREMENTS = "requirements.txt"
_PIN = re.compile(r"^\s*([A-Za-z0-9_.\-]+)\s*==\s*([^\s#;]+)")


def pins(root):
    """{lower-case package name: version} of every `name==version` line of requirements.txt."""
    out = {}
    p = Path(root) / REQUIREMENTS
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            m = _PIN.match(line)
            if m:
                out[m.group(1).lower()] = m.group(2)
    return out


def split_by_design(by_design):
    """(R8-era part as written in the test, declarations) of the test's by_design."""
    r8 = {k: v for k, v in by_design.items() if k in R8_ERA}
    decl = {k: v for k, v in by_design.items() if k not in R8_ERA}
    return r8, decl


def offenders_under(root, allow):
    """the T-210 offender list computed with an explicit by_design `allow` (never the test's own)."""
    root = Path(root).resolve()
    std = V1._stdlib()
    out = {}
    for p in V1._files(root, "engine/source"):
        if p.name in allow and allow[p.name] is None:
            continue
        ok = allow.get(p.name) or set()
        hits = {}
        for nm, line, style in V1._imports(p, root):
            top = nm.split(".")[0]
            if not top or top in std or top == "engine" or top in ok:
                continue
            hits.setdefault(top, []).append((line, style))
        if hits:
            styles = {s for v in hits.values() for _, s in v}
            out[str(p.relative_to(root))] = {
                "packages": sorted(hits),
                "lines": sorted({ln for v in hits.values() for ln, _ in v}),
                "import_style": styles.pop() if len(styles) == 1 else "mixed"}
    return out


def facts(root):
    root = Path(root).resolve()
    by_design, core = V1.k1_test_facts(root)
    r8, decl = split_by_design(by_design)
    base = offenders_under(root, R8_ERA)                 # what the record is about (declarations ignored)
    remaining = offenders_under(root, by_design)         # what the K1 test still meets, test's by_design applied
    graph = V1._graph(root)
    reg = json.loads((root / V1.REGISTER).read_text(encoding="utf-8"))
    names = {}
    for p in V1._files(root, "engine/source"):
        names.setdefault(p.name, []).append(str(p.relative_to(root)))
    return {"by_design": by_design, "r8_era": r8, "declarations": decl, "core": core,
            "offenders": base, "remaining": remaining,
            "core_hits": {c: sorted(V1.closure(graph, c) & set(base)) for c in core},
            "released_reaches": sorted(V1.closure(graph, V1.RELEASED) & set(base)) if V1.RELEASED in graph else None,
            "registered": sorted(reg["third_party_allowed"]), "pins": pins(root), "names": names}


def _v1_problems(f, record):
    """the T-210 check, on the offenders under the R8-era exceptions only (same codes, same rules)."""
    off, problems = f["offenders"], []
    recs = {r.get("module"): r for r in record["records"]}
    for m in sorted(set(off) - set(recs)):
        problems.append(("UNRECORDED", m, f"imports {off[m]['packages']} (lines {off[m]['lines']}); add a record"))
    for m in sorted(set(recs) - set(off)):
        problems.append(("STALE", m, "no longer imports a third-party package outside the R8-era exceptions"))
    for m in sorted(set(recs) & set(off)):
        r = recs[m]
        for k in V1.FIELDS:
            if not r.get(k):
                problems.append(("FIELD_MISSING", m, k))
        if sorted(r.get("packages") or ()) != off[m]["packages"]:
            problems.append(("PACKAGES_DIFFER", m, f"record {r.get('packages')} vs imported {off[m]['packages']}"))
        if r.get("decision") not in V1.DECISIONS:
            problems.append(("BAD_DECISION", m, str(r.get("decision"))))
        if r.get("decision") in ("ALLOWED_OUTSIDE_K1", "OUTSIDE_K2_GATE") and \
                set(off[m]["packages"]) - set(f["registered"]):
            problems.append(("NOT_REGISTERED_BUT_ALLOWED", m,
                             str(sorted(set(off[m]["packages"]) - set(f["registered"])))))
    for c, hits in f["core_hits"].items():
        if hits:
            problems.append(("K1_CORE_REACHES_OFFENDER", c, str(hits)))
    return problems


def check(root, record):
    f = facts(root)
    problems = _v1_problems(f, record)
    if f["r8_era"] != R8_ERA:
        problems.append(("R8_ERA_CHANGED", "by_design", f"test {f['r8_era']} vs pinned {R8_ERA}"))
    by_name = {}
    for r in record["records"]:
        by_name.setdefault(Path(r.get("module") or "").name, []).append(r)
    declared_modules = set()
    for name, allowed in sorted(f["declarations"].items()):
        recs = by_name.get(name, [])
        paths = f["names"].get(name, [])
        if len(paths) > 1:
            problems.append(("AMBIGUOUS_FILE_NAME", name, f"matches {paths}"))
        if not recs:
            problems.append(("DECLARED_WITHOUT_RECORD", name, "no research/agents_t210/K1_DECISIONS.json record"))
            continue
        r = recs[0]
        m = r["module"]
        declared_modules.add(m)
        if allowed is None:
            problems.append(("DECLARED_WHOLE_MODULE", m, "only the R8-era K2 route may be exempt whole"))
            continue
        if r.get("decision") != "ALLOWED_OUTSIDE_K1":
            problems.append(("DECLARED_NOT_ALLOWED", m, f"record decision {r.get('decision')}"))
        if sorted(allowed) != sorted(r.get("packages") or ()):
            problems.append(("DECLARATION_PACKAGES_DIFFER", m, f"declared {sorted(allowed)} vs record {r.get('packages')}"))
        imported = set((f["offenders"].get(m) or {}).get("packages") or ())
        for pkg in sorted(set(allowed) - imported):
            problems.append(("DECLARED_NOT_IMPORTED", m, pkg))
        for pkg in sorted(allowed):
            if pkg.lower() not in f["pins"]:
                problems.append(("NOT_PINNED", m, f"{pkg} has no '{pkg}==<version>' line in {REQUIREMENTS}"))
            if pkg not in f["registered"]:
                problems.append(("NOT_REGISTERED", m, f"{pkg} is not in the B-5 dependency register"))
    for r in record["records"]:
        if r.get("decision") == "ALLOWED_OUTSIDE_K1" and r["module"] not in declared_modules:
            problems.append(("UNDECLARED_ALLOWED", r["module"], "ALLOWED_OUTSIDE_K1 record without a by_design entry"))
    return problems, f


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] not in ("check", "remaining"):
        print(__doc__)
        return 2
    root = Path(argv[argv.index("--root") + 1]) if "--root" in argv else Path.cwd()
    rec = V1.load_record(Path(argv[argv.index("--record") + 1]) if "--record" in argv else V1.RECORD)
    problems, f = check(root, rec)
    if argv[0] == "remaining":
        recs = {r["module"]: r for r in rec["records"]}
        for m, o in sorted(f["remaining"].items()):
            print(f"{m} | {', '.join(o['packages'])} | lines {o['lines']} | {recs.get(m, {}).get('decision', 'UNRECORDED')}")
        return 0
    print(f"offenders under the R8-era exceptions {len(f['offenders'])}; records {len(rec['records'])}; "
          f"declarations {len(f['declarations'])}; K1 test still meets {len(f['remaining'])}; "
          f"K1 core modules reaching one: {sum(1 for v in f['core_hits'].values() if v)}; "
          f"released {V1.RELEASED} reaches: {f['released_reaches']}")
    for p in problems:
        print("  " + " | ".join(p))
    print(f"problems {len(problems)}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
