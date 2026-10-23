"""T-212 GUARD PROPERTY: the default-guard safety property checked on the LIVE tree, as a property, not a snapshot.

Why. The T-202 sweep (research/agents_t202/guard_sweep.py) pins a merge window (BASE 15fd9132 .. HEAD d699b650) but
scanned importers on the live tree, so the legitimate unwired producer engine/source/masonry_area_v1.py (T-108 r2,
merge 01eeafd0) turned its snapshot assertion red although no candidate or released method reaches any producer.
T-212 splits the two jobs: the sweep now reads its importers AT its pinned HEAD (reproducible), and this module checks
the property the guard exists for, over the tree as it is now:

  P1  every engine/ or tools/ .py module added or modified after the T-202 HEAD has a default-guard class (one of
      guard_sweep.CLASSES): from guard_sweep.GUARD, from LATER below, or declared in the module itself as a
      module-level string `DEFAULT_GUARD_CLASS = "<class>"` (so a new module classifies itself without editing this
      file; a declared value that is not a class is a problem);
  P2  the importer closure (transitive, engine/ and tools/ only) of every UNWIRED_PRODUCER holds only UNWIRED_PRODUCER
      modules; research/ and tests/ are outside the scan and allowed. An importer that is a candidate or released
      method (arch_v*, route_g*, tools/urban_boq_m9.py, ...) or any other class or no class is a problem, reported
      with its import chain;
  P3  no engine/ or tools/ file loads an unwired producer at run time (importlib / __import__ with the producer's
      dotted name or file stem in a string): the static graph cannot see that edge, so it is refused, not ignored.

Imports are resolved statically, INCLUDING relative imports (`from .x import y`, which the T-202 index skips) and the
bare stem form `import x` used after a sys.path insert (matched conservatively, as guard_sweep does). Limits: imports
built from computed strings are not followed (P3 matches literal names only).

    python3 -I research/agents_t212/guard_property.py check      exit 1 when any problem is found

Standard library only; reads git and the source files; writes nothing.
"""
from __future__ import annotations

import ast
import re
import subprocess
import sys
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t202"))

import guard_sweep as GS  # noqa: E402

SCOPES = ("engine", "tools")
DECL = "DEFAULT_GUARD_CLASS"
METHOD = re.compile(r"(^|/)(arch_v\d+[a-z0-9_]*|route_g[a-z0-9_]*|urban_boq_m9|arch_takeoff[a-z0-9_]*)\.py$")
DYNAMIC = re.compile(r"importlib|__import__")

# Classes for modules merged after the T-202 HEAD (d699b650), with the reason; the Checker re-derives each one from
# the module's docstring and its importers. A later module may instead declare DEFAULT_GUARD_CLASS in its own source.
LATER = {
    "engine/source/masonry_area_v1.py": (GS.UNWIRED_PRODUCER, "block wall m2 / m3 / installed units per run (T-108 r2, "
                                         "merge 01eeafd0); imports OPENING_SCOPE_V1 (also unwired); imported by no "
                                         "method or CLI; DG-1 / DG-3 / DG-5 / DG-6 / DG-8 must run when integrated"),
    "engine/source/element_continuity_v1.py": (GS.CHECK_ONLY, "element inventory / storey continuity finding rows "
                                               "(T-188, merge fb3a4623); stdlib only, writes no BOQ quantity"),
}


# ------------------------------------------------------------------------------------------------ pure core
def module_names(path):
    """dotted name of a file (engine/source/x.py -> engine.source.x; pkg/__init__.py -> pkg)."""
    dotted = path[:-3].replace("/", ".")
    return dotted[:-9] if dotted.endswith(".__init__") else dotted


def declared(src):
    """the module-level string assigned to DEFAULT_GUARD_CLASS, or None."""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return None
    for n in tree.body:
        if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == DECL for t in n.targets):
            if isinstance(n.value, ast.Constant) and isinstance(n.value.value, str):
                return n.value.value
            return "<not a string>"
    return None


def classify(path, src, table):
    """(class, source of the class) or (None, None). The module's own declaration wins over a table row."""
    d = declared(src) if src is not None else None
    if d is not None:
        return d, "declared in module"
    if path in table:
        return table[path][0], "table"
    return None, None


def edges(sources):
    """{file: set of files it imports} over `sources` ({path: text}), relative imports resolved, bare stems matched."""
    by_name = {module_names(p): p for p in sources}
    by_stem = {}
    for p in sources:
        by_stem.setdefault(Path(p).stem, set()).add(p)

    def resolve(name):
        hit = set()
        if name in by_name:
            hit.add(by_name[name])
        if "." not in name:
            hit |= by_stem.get(name, set()) - {p for p in by_stem.get(name, set()) if p.endswith("__init__.py")}
        return hit

    out = {}
    for path, src in sources.items():
        try:
            tree = ast.parse(src)
        except SyntaxError:
            out[path] = set()
            continue
        pkg = module_names(path).split(".")
        if not path.endswith("__init__.py"):
            pkg = pkg[:-1]
        got = set()
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                for a in n.names:
                    got |= resolve(a.name)
            elif isinstance(n, ast.ImportFrom):
                if n.level:
                    base = pkg[:len(pkg) - (n.level - 1)] if n.level - 1 <= len(pkg) else []
                    mod = ".".join(base + ([n.module] if n.module else []))
                else:
                    mod = n.module or ""
                if mod:
                    got |= resolve(mod)
                for a in n.names:
                    got |= resolve(f"{mod}.{a.name}" if mod else a.name)
        got.discard(path)
        out[path] = got
    return out


def check(sources, changed, table):
    """-> (report rows, problems).

    sources: {path: text} of every engine/ and tools/ .py file; changed: [(status, path)] added / modified after the
    T-202 HEAD; table: {path: (class, why)} (guard_sweep.GUARD merged with LATER)."""
    problems, rows = [], []
    cls = {}
    for p, src in sources.items():
        c, how = classify(p, src, table)
        if c is not None:
            cls[p] = (c, how)
            if c not in GS.CLASSES:
                problems.append(f"{p}: default-guard class {c!r} ({how}) is not one of {list(GS.CLASSES)}")
    # P1 every changed module classified
    for st, p in changed:
        c = cls.get(p, (None, None))[0]
        if p not in sources:                        # deleted after the head: nothing left to classify
            continue
        if c is None:
            problems.append(f"{p}: {'added' if st == 'A' else 'modified'} after {GS.HEAD[:8]} and has no "
                            f"default-guard classification (table row in research/agents_t212 or "
                            f"{DECL} in the module)")
        rows.append({"path": p, "status": st, "class": c or "UNCLASSIFIED", "how": cls.get(p, (None, None))[1]})
    # P2 importer closure of every unwired producer
    fwd = edges(sources)
    rev = {}
    for f, ts in fwd.items():
        for t in ts:
            rev.setdefault(t, set()).add(f)
    producers = sorted(p for p, (c, _) in cls.items() if c == GS.UNWIRED_PRODUCER)
    closure = {}
    for prod in producers:
        seen, chain, q = set(), {prod: [prod]}, deque([prod])
        while q:
            cur = q.popleft()
            for imp in sorted(rev.get(cur, ())):
                if imp in seen or imp == prod:
                    continue
                seen.add(imp)
                chain[imp] = chain[cur] + [imp]
                q.append(imp)
        closure[prod] = sorted(seen)
        for imp in sorted(seen):
            c = cls.get(imp, (None, None))[0]
            if c == GS.UNWIRED_PRODUCER:
                continue
            what = "a candidate or released method" if METHOD.search(imp) else f"class {c or 'UNCLASSIFIED'}"
            problems.append(f"{imp} ({what}) reaches the unwired producer {prod}: "
                            f"import chain {' -> '.join(reversed(chain[imp]))}")
    # P3 run-time loading of a producer
    for f, src in sources.items():
        if not DYNAMIC.search(src):
            continue
        strings = {n.value for n in ast.walk(_tree(src)) if isinstance(n, ast.Constant) and isinstance(n.value, str)}
        for prod in producers:
            if f == prod:
                continue
            names = {module_names(prod), Path(prod).stem, prod}
            if any(s in names or s.endswith("/" + Path(prod).name) for s in strings):
                problems.append(f"{f} loads modules at run time and names the unwired producer {prod} in a string")
    return {"changed": rows, "producers": producers, "closure": closure}, problems


def _tree(src):
    try:
        return ast.parse(src)
    except SyntaxError:
        return ast.Module(body=[], type_ignores=[])


# ------------------------------------------------------------------------------------------------ live tree
def live_sources():
    return dict(GS._sources(SCOPES))


def changed_since(base=None):
    """[(A|M, path)] .py files under engine/ and tools/ that differ between `base` (default the T-202 HEAD) and the
    working tree, plus untracked ones (a module not yet committed is already 'new')."""
    base = base or GS.HEAD
    out = []
    for row in GS.git("diff", "--name-status", "--no-renames", base, "--", *[d + "/" for d in SCOPES]).splitlines():
        st, path = row.split("\t", 1)
        if path.endswith(".py") and st[0] in "AM":
            out.append((st[0], path))
    for path in GS.git("ls-files", "--others", "--exclude-standard", "--", *SCOPES).splitlines():
        if path.endswith(".py"):
            out.append(("A", path))
    return sorted(set(out), key=lambda r: r[1])


def table():
    t = dict(GS.GUARD)
    t.update(LATER)
    return t


def run():
    return check(live_sources(), changed_since(), table())


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv != ["check"]:
        print(__doc__)
        return 2
    rep, problems = run()
    print(f"after {GS.HEAD[:8]}: {len(rep['changed'])} engine/tools module(s) added or modified")
    for r in rep["changed"]:
        print(f"  {r['status']} {r['path']}: {r['class']} ({r['how']})")
    for p in rep["producers"]:
        print(f"UNWIRED_PRODUCER {p}: importer closure {rep['closure'][p] or 'none'}")
    for p in problems:
        print("PROBLEM:", p)
    print(f"problems {len(problems)}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
