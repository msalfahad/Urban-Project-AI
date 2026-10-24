"""T-210 (a): K1 BOUNDARY DECISION RECORD check. Standard library only; reads files, writes nothing.

The K1 boundary tests (tests/r8_1/test_r8_1_boundaries.py::test_k1_is_stdlib_only_in_r8_1, and the two "K1 does not
import ezdxf" tests in tests/r8_1/test_r8_1_kernel_ocs.py and tests/r8_2/test_r8_2_k2.py) assert on the FIRST offending
file, so while they are red a new offender is invisible (T-202 SWEEP.md s.3). This tool lists EVERY engine/source module
that imports a third-party package outside the K1 test's own `by_design` exceptions (read from the test itself, never
copied), and compares that list with the decision record K1_DECISIONS.json beside this file: one record per module,
with the packages it imports, the decision and the fix proposal. The K1 tests are not changed (never weaken a test).

    python3 -I research/agents_t210/k1_boundary.py check [--root R] [--record F]   exit 1 on any problem
    python3 -I research/agents_t210/k1_boundary.py table [--root R] [--record F]   markdown table of the record + facts

Problems (check): UNRECORDED (an offender with no record), STALE (a record for a module that no longer offends),
PACKAGES_DIFFER (record packages != imported packages), FIELD_MISSING, BAD_DECISION, NOT_REGISTERED_BUT_ALLOWED (a
decision of ALLOWED_* for a package outside the B-5 dependency register), K1_CORE_REACHES_OFFENDER (a module of the
K1 core list of tests/r8_1 imports an offender, statically and transitively).
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RECORD = HERE / "K1_DECISIONS.json"
SCHEMA = "URBAN_K1_BOUNDARY_DECISIONS_V1"
K1_TEST = "tests/r8_1/test_r8_1_boundaries.py"
K1_FUNC = "test_k1_is_stdlib_only_in_r8_1"
REGISTER = "tests/r8_0/registers/R8_0_SOURCE_DEPENDENCY_REGISTER.json"
RELEASED = "engine/source/arch_v29.py"           # ARCH_TAKEOFF_V2.9, the released default's architectural method
DECISIONS = {
    "ALLOWED_OUTSIDE_K1": "registered (B-5) package in a module that is not K1 and not reached from the K1 core; "
                          "the stdlib-only assertion names it only because its scope is all of engine/source",
    "OUTSIDE_K2_GATE": "registered (B-5) ezdxf in a module other than the K2 route kernel_ezdxf.py; K1 is still "
                       "independent of it (the K1 core reaches no such module) but the register's role for ezdxf "
                       "('D2/K2 route only') is not kept",
    "NOT_REGISTERED_HOLD": "package outside the B-5 dependency register; registering it needs a decision the record "
                           "names (here: licence), so the two B-5 / B-6 ids stay failing until a fix",
}
FIELDS = ("module", "packages", "import_style", "role", "decision", "why", "fix_proposal")


def _stdlib():
    return set(sys.stdlib_module_names) | {"__future__"}


def _files(root, sub):
    return sorted(p for p in (root / sub).rglob("*.py") if "__pycache__" not in p.parts)


def k1_test_facts(root):
    """(by_design {file name: None | set}, K1 core module list) read from the K1 test file as written."""
    tree = ast.parse((root / K1_TEST).read_text(encoding="utf-8"))
    by_design, core = None, None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == K1_FUNC:
            for sub in ast.walk(node):
                if isinstance(sub, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "by_design"
                                                       for t in sub.targets):
                    by_design = ast.literal_eval(sub.value)
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "EXPECTED_MODULES"
                                                for t in node.targets):
            core = sorted(ast.literal_eval(node.value))
    if by_design is None or core is None:
        raise ValueError(f"{K1_TEST}: by_design in {K1_FUNC} or EXPECTED_MODULES not found")
    return by_design, core


def _imports(path, root):
    """[(absolute module name, line, 'top' | 'nested')] of one file; relative imports resolved against root."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    top_ids = {id(n) for n in tree.body}
    pkg = list(path.relative_to(root).with_suffix("").parts)[:-1]
    out = []
    for node in ast.walk(tree):
        names = []
        if isinstance(node, ast.Import):
            names = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base = pkg[: len(pkg) - (node.level - 1)] if node.level > 1 else pkg
                mod = ".".join(base + ([node.module] if node.module else []))
            else:
                mod = node.module or ""
            names = [mod] + [f"{mod}.{a.name}" for a in node.names]
        for nm in names:
            out.append((nm, node.lineno, "top" if id(node) in top_ids else "nested"))
    return out


def offenders(root):
    """{engine/source/<file>: {"packages": [...], "lines": [...], "import_style": top | nested | mixed}}."""
    root = Path(root).resolve()
    by_design, _ = k1_test_facts(root)
    std = _stdlib()
    out = {}
    for p in _files(root, "engine/source"):
        allow = by_design.get(p.name, set()) if p.name in by_design else set()
        if p.name in by_design and allow is None:
            continue
        hits = {}
        for nm, line, style in _imports(p, root):
            top = nm.split(".")[0]
            if not top or top in std or top == "engine" or top in allow:
                continue
            hits.setdefault(top, []).append((line, style))
        if hits:
            styles = {s for v in hits.values() for _, s in v}
            out[str(p.relative_to(root))] = {
                "packages": sorted(hits),
                "lines": sorted({ln for v in hits.values() for ln, _ in v}),
                "import_style": styles.pop() if len(styles) == 1 else "mixed"}
    return out


def _graph(root):
    files = {str(p.relative_to(root)): p for sub in ("engine", "tools") for p in _files(root, sub)}

    def to_file(nm):
        for cand in (nm.replace(".", "/") + ".py", nm.replace(".", "/") + "/__init__.py"):
            if cand in files:
                return cand
        return None

    return {k: {f for f in (to_file(n) for n, _, _ in _imports(p, root)) if f} for k, p in files.items()}


def closure(graph, start):
    seen, todo = set(), [start]
    while todo:
        for y in graph.get(todo.pop(), ()):
            if y not in seen:
                seen.add(y)
                todo.append(y)
    return seen


def facts(root):
    root = Path(root).resolve()
    off = offenders(root)
    graph = _graph(root)
    _, core = k1_test_facts(root)
    reg = json.loads((root / REGISTER).read_text(encoding="utf-8"))
    core_hits = {c: sorted(closure(graph, c) & set(off)) for c in core}
    released = sorted(closure(graph, RELEASED) & set(off)) if RELEASED in graph else None
    importers = {m: sorted(k for k, v in graph.items() if m in v) for m in off}
    return {"offenders": off, "core_hits": core_hits, "released_reaches": released, "importers": importers,
            "registered": sorted(reg["third_party_allowed"]), "forbidden": sorted(reg["forbidden"])}


def load_record(path=RECORD):
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    if doc.get("schema") != SCHEMA:
        raise ValueError(f"record schema must be {SCHEMA}")
    mods = [r.get("module") for r in doc["records"]]
    if len(mods) != len(set(mods)):
        raise ValueError("one record per module")
    return doc


def check(root, record):
    f = facts(root)
    off, problems = f["offenders"], []
    recs = {r.get("module"): r for r in record["records"]}
    for m in sorted(set(off) - set(recs)):
        problems.append(("UNRECORDED", m, f"imports {off[m]['packages']} (lines {off[m]['lines']}); add a record"))
    for m in sorted(set(recs) - set(off)):
        problems.append(("STALE", m, "no longer imports a third-party package outside by_design; remove its record"))
    for m in sorted(set(recs) & set(off)):
        r = recs[m]
        for k in FIELDS:
            if not r.get(k):
                problems.append(("FIELD_MISSING", m, k))
        if sorted(r.get("packages") or ()) != off[m]["packages"]:
            problems.append(("PACKAGES_DIFFER", m, f"record {r.get('packages')} vs imported {off[m]['packages']}"))
        if r.get("decision") not in DECISIONS:
            problems.append(("BAD_DECISION", m, str(r.get("decision"))))
        if r.get("decision") in ("ALLOWED_OUTSIDE_K1", "OUTSIDE_K2_GATE") and \
                set(off[m]["packages"]) - set(f["registered"]):
            problems.append(("NOT_REGISTERED_BUT_ALLOWED", m, str(sorted(set(off[m]["packages"]) -
                                                                          set(f["registered"])))))
    for c, hits in f["core_hits"].items():
        if hits:
            problems.append(("K1_CORE_REACHES_OFFENDER", c, str(hits)))
    return problems, f


def table(root, record):
    _, f = check(root, record)
    recs = {r["module"]: r for r in record["records"]}
    rows = ["| # | Module | Packages (lines, style) | Registered (B-5) | Importers | Role | Decision | Fix proposal |",
            "|---|---|---|---|---|---|---|---|"]
    for i, (m, o) in enumerate(sorted(f["offenders"].items()), 1):
        r = recs.get(m, {})
        reg = "yes" if set(o["packages"]) <= set(f["registered"]) else "NO"
        imp = ", ".join(x.replace("engine/source/", "").replace(".py", "") for x in f["importers"][m]) or "none"
        rows.append(f"| {i} | `{m.replace('engine/source/', '')}` | {', '.join(o['packages'])} ({', '.join(map(str, o['lines']))}; "
                    f"{o['import_style']}) | {reg} | {imp} | {r.get('role', '-')} | {r.get('decision', 'UNRECORDED')} | "
                    f"{r.get('fix_proposal', '-')} |")
    return "\n".join(rows)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] not in ("check", "table"):
        print(__doc__)
        return 2
    root = Path(argv[argv.index("--root") + 1]) if "--root" in argv else Path.cwd()
    rec = load_record(Path(argv[argv.index("--record") + 1]) if "--record" in argv else RECORD)
    if argv[0] == "table":
        print(table(root, rec))
        return 0
    problems, f = check(root, rec)
    print(f"offenders {len(f['offenders'])}; records {len(rec['records'])}; K1 core modules reaching one: "
          f"{sum(1 for v in f['core_hits'].values() if v)}; released {RELEASED} reaches: {f['released_reaches']}")
    for p in problems:
        print("  " + " | ".join(p))
    print(f"problems {len(problems)}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
