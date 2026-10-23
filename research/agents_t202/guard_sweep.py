"""T-202 GUARD SWEEP: every engine/ and tools/ module added or changed by a merge on the working branch inside a fixed
window, checked against the rebar product firewall registry (tests/structural_comparison_engine/rebar_product_registry.py)
and the default guard (engine/source/default_guard.py, T-186; wired only in ARCH_TAKEOFF_V3.0.6, T-187).

Reads git and the source files; writes nothing unless --out is given. Standard library only.

    python3 -I research/agents_t202/guard_sweep.py table [--base SHA] [--head SHA] [--out FILE.md]

The window is first-parent history BASE..HEAD of the working branch (defaults: the T-202 window below). Exit 1 when
  * a swept module has no default-guard classification in GUARD below (the sweep is incomplete), or
  * a swept engine/ module names reinforcement ("rebar", "bbs", "reinforc", the firewall test's own words) and is not
    declared in the registry (the firewall definition, test_every_rebar_module_in_engine_is_declared), or
  * a first-parent commit in the window that is not a merge touches engine/ or tools/ (work outside the merge flow).

Registry class is read from the registry tuples, never typed here. The default-guard column is a judgement per module,
stated with its reason in GUARD; the Checker re-derives it from each module's docstring and importers.
"""
from __future__ import annotations

import ast
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "tests" / "structural_comparison_engine" / "rebar_product_registry.py"

# T-202 window: 2026-10-22 00:00 UTC (the first-parent commit before it) .. the working head when the sweep was taken
BASE = "15fd9132a7b753dc8b5e7d8922b20a57efb4cba8"   # Merge T-155, 2026-10-21 23:53:39 UTC, last merge before 10-22 00:00
HEAD = "d699b650af7c63f85fc8b0bf5cedb037fa9848cb"   # Merge T-200, 2026-10-23 07:00:07 UTC
SCOPES = ("engine/", "tools/")
WORDS = ("rebar", "bbs", "reinforc")                # test_rebar_product_firewall.test_every_rebar_module_in_engine_is_declared

# Default-guard classes
GUARD_HOST = "GUARD_HOST"                 # runs the guard or is the guard
GUARDED_VIA_V306 = "GUARDED_VIA_V3.0.6"   # its lines reach the candidate; DG runs over them only in a V3.0.6 run
UNWIRED_PRODUCER = "UNWIRED_PRODUCER"     # computes quantities / deductions but is wired nowhere: guard due AT integration
CHECK_ONLY = "CHECK_ONLY"                 # emits issue / evidence rows, never a BOQ quantity: guard not applicable
TOOLING = "TOOLING"                       # CLI / scoring / manifest; emits no BOQ quantity of its own
CLASSES = (GUARD_HOST, GUARDED_VIA_V306, UNWIRED_PRODUCER, CHECK_ONLY, TOOLING)

GUARD = {
    "engine/source/default_guard.py": (GUARD_HOST, "the guard itself (T-186); unwired on its own, run by arch_v306"),
    "engine/source/arch_v306.py": (GUARD_HOST, "ARCH_TAKEOFF_V3.0.6 runs DG.guard over every V3.0.5 line + the lines it "
                                   "adds (guard_changes); a guard finding on an ADDED line refuses the integration; "
                                   "with no project guard input the guard is NOT run and only the run log says so "
                                   "(state NO_PROJECT_INPUT, guard_changes line 396)"),
    "tools/urban_boq_m9.py": (GUARD_HOST, "CLI: the guard runs only under --method ARCH_TAKEOFF_V3.0.6 --v306-inputs; "
                              "--method ARCH_TAKEOFF_V3.0.2 .. V3.0.5 still run UNGUARDED (superseded candidate "
                              "versions); released V2.9 + route G is not guarded (opt-in candidate only)"),
    "engine/source/arch_v302.py": (GUARDED_VIA_V306, "V3.0.2 lines (footing steel population) inherited by V3.0.6"),
    "engine/source/arch_v303.py": (GUARDED_VIA_V306, "V3.0.3 ledger steel lines inherited by V3.0.6"),
    "engine/source/arch_v304.py": (GUARDED_VIA_V306, "V3.0.4 no-assumptions audit labels inherited by V3.0.6"),
    "engine/source/arch_v305.py": (GUARDED_VIA_V306, "V3.0.5 ledger lines (slab / stair / pool / tank steel, dome ring) "
                                   "inherited by V3.0.6"),
    "engine/source/route_g_scope_v1.py": (GUARDED_VIA_V306, "route-G occurrence / blinding scope read by arch_v301 / "
                                          "arch_v302 only (not by the released route); its effect reaches the "
                                          "candidate lines that V3.0.6 guards"),
    "engine/source/masonry_centreline_v2.py": (UNWIRED_PRODUCER, "wall-run lengths per thickness (Q-69 B); imported by "
                                               "no method or CLI; DG-1 / DG-3 / DG-5 / DG-6 must run when it is "
                                               "integrated"),
    "engine/source/opening_scope_v1.py": (UNWIRED_PRODUCER, "opening deductions by physical scope; imported by no "
                                          "method; DG-8 DEDUCTION_EXCEEDS_MEMBER and DG-6 apply at integration"),
    "engine/source/stair_rule_calculator.py": (UNWIRED_PRODUCER, "riser / tread counts and required length under "
                                               "UP-STAIR-015; a design check today, imported by no method; any "
                                               "quantity it feeds into a line is guarded at integration (DG-1 / DG-5)"),
    "engine/source/concrete_overlap_ownership.py": (CHECK_ONLY, "states whether lines bill an intersection once; "
                                                    "produces no BOQ quantity (complements DG-6)"),
    "engine/source/opening_consistency_v1.py": (CHECK_ONLY, "plan = elevation = section = schedule issue rows"),
    "engine/source/document_register_v1.py": (CHECK_ONLY, "sheet register + citation check; a source of the guard's "
                                              "`documents` evidence, not a guarded line"),
    "engine/source/curved_geometry_check_v1.py": (CHECK_ONLY, "curved / partial footprint issue rows (complements DG-3)"),
    "engine/source/scope_crosswalk_v1.py": (CHECK_ONLY, "freelancer row / candidate line / drawn element crosswalk "
                                            "(complements DG-5)"),
    "engine/source/level_chain_v1.py": (CHECK_ONLY, "datum / link / issue rows (complements DG-4 finished vs "
                                        "structural)"),
    "engine/source/coverage_census_v2.py": (CHECK_ONLY, "terminal state per BOQ family; reads lines, writes no "
                                            "quantity"),
    "tools/release_baseline.py": (TOOLING, "pins a released baseline run (V2.9 + route G) for Gate B diffs"),
    "tools/alsenan_keymap.py": (TOOLING, "maps engine lines to scorer rows; comparison only, never upstream of a "
                                "quantity"),
    "tools/scoreboard_v2.py": (TOOLING, "SCOREBOARD v2 by script; comparison only"),
    "tools/m9_rules_manifest.py": (TOOLING, "rule store manifest build / check"),
}


def git(*args):
    return subprocess.run(["git", "-C", str(ROOT), *args], check=True, capture_output=True, text=True).stdout


def window(base=BASE, head=HEAD):
    """[(sha, iso time, subject, is_merge, [(status, path)])] for first-parent commits base..head, oldest first."""
    out = []
    for ln in git("log", "--first-parent", "--reverse", "--format=%H%x09%P%x09%cI%x09%s", f"{base}..{head}").splitlines():
        sha, parents, when, subj = ln.split("\t", 3)
        first = parents.split()[0]
        files = []
        for row in git("diff", "--name-status", "--no-renames", first, sha, "--", *SCOPES).splitlines():
            st, path = row.split("\t", 1)
            if path.endswith(".py"):
                files.append((st, path))
        out.append((sha, when, subj, len(parents.split()) > 1, files))
    return out


def task_of(subject):
    m = re.match(r"Merge agents/task-(T-[0-9]+(?:-r[0-9]+)?)", subject)
    return m.group(1) if m else subject[:40]


def registry():
    """{path: class name} from the registry tuples (parsed, not imported: the file is declarations only)."""
    tree = ast.parse(REGISTRY.read_text(encoding="utf-8"))
    cls = {}
    for n in tree.body:
        if isinstance(n, ast.Assign) and isinstance(n.value, ast.Tuple):
            name = n.targets[0].id
            for e in n.value.elts:
                if isinstance(e, ast.Constant) and isinstance(e.value, str):
                    cls[e.value] = name
    return cls


def names_rebar(path):
    p = ROOT / path
    return p.exists() and any(w in p.read_text(encoding="utf-8", errors="ignore").lower() for w in WORDS)


def _module_names(path):
    """dotted and bare names under which a file can be imported (engine.source.x / tools.x / x)."""
    dotted = path[:-3].replace("/", ".")
    return {dotted, dotted.rsplit(".", 1)[-1]}


_INDEX = {}


def _sources(scopes, rev=None):
    """[(file, source text)] of every .py file under `scopes`: the live tree when rev is None, else the files as they
    are AT commit `rev` (git ls-tree + one `git cat-file --batch`), so a pinned window stays reproducible after later
    merges (T-212: the T-202 snapshot read the live tree and went red when T-108 r2 added a legitimate importer)."""
    if rev is None:
        return [(str(f.relative_to(ROOT)), f.read_text(encoding="utf-8", errors="ignore"))
                for d in scopes for f in sorted((ROOT / d).rglob("*.py"))]
    files = [p for p in git("ls-tree", "-r", "--name-only", rev, "--", *scopes).splitlines() if p.endswith(".py")]
    if not files:
        return []
    blob = subprocess.run(["git", "-C", str(ROOT), "cat-file", "--batch"], check=True, capture_output=True,
                          input="".join(f"{rev}:{p}\n" for p in files).encode("utf-8")).stdout
    out, i = [], 0
    for p in files:
        nl = blob.index(b"\n", i)
        head = blob[i:nl].split()
        if len(head) != 3 or head[1] != b"blob":
            raise RuntimeError(f"git cat-file: unexpected header {blob[i:nl]!r} for {rev}:{p}")
        size = int(head[2])
        out.append((p, blob[nl + 1:nl + 1 + size].decode("utf-8", errors="ignore")))
        i = nl + 1 + size + 1
    return out


def import_index(scopes=("engine", "tools"), rev=None):
    """{file: set of imported names} for every engine/ and tools/ file; `import a.b` -> 'a.b', `from a import b` ->
    'a' and 'a.b' (absolute imports only). rev=None reads the live tree, a commit reads the tree at that commit.
    Parsed once per process and rev."""
    key = (tuple(scopes), rev)
    if key not in _INDEX:
        idx = {}
        for f, src in _sources(scopes, rev):
            if "import" not in src:
                continue
            try:
                tree = ast.parse(src)
            except SyntaxError:
                continue
            names = set()
            for n in ast.walk(tree):
                if isinstance(n, ast.Import):
                    names |= {a.name for a in n.names}
                elif isinstance(n, ast.ImportFrom) and not n.level and n.module:
                    names.add(n.module)
                    names |= {f"{n.module}.{a.name}" for a in n.names}
            idx[f] = names
        _INDEX[key] = idx
    return _INDEX[key]


def importers(path, scopes=("engine", "tools"), rev=None):
    """engine/ and tools/ files that import `path` (static AST: import x / from pkg import x / from x import ...), on
    the live tree (rev=None) or on the tree at commit `rev`."""
    target = _module_names(path)
    return sorted(f for f, names in import_index(scopes, rev).items() if f != path and names & target)


def sweep(base=BASE, head=HEAD):
    """-> (rows, problems). One row per module (latest merge that touched it last), merges listed per module.
    Importers are read on the tree AT `head` (T-212), so the window's table does not change with later merges."""
    reg = registry()
    mods, problems = {}, []
    for sha, when, subj, is_merge, files in window(base, head):
        if not is_merge and files:
            problems.append(f"non-merge first-parent commit {sha[:8]} touches {[p for _, p in files]}")
        for st, path in files:
            m = mods.setdefault(path, {"path": path, "touched": []})
            m["touched"].append((task_of(subj), st, sha[:8], when))
    rows = []
    for path in sorted(mods):
        m = mods[path]
        exists = (ROOT / path).exists()
        rebar = names_rebar(path) if exists else False
        rc = reg.get(path)
        if rc is None:
            rc_txt = "not declared; names no rebar word: not required" if not rebar else "UNDECLARED (names rebar)"
            if rebar and path.startswith("engine/"):
                problems.append(f"{path}: names reinforcement and is not declared in the registry")
            elif rebar:
                rc_txt = "not declared; tools/ is outside the firewall scan (engine/ only)"
        else:
            rc_txt = rc
        g = GUARD.get(path)
        if g is None:
            problems.append(f"{path}: no default-guard classification in GUARD")
        rows.append({"path": path, "touched": m["touched"], "exists": exists, "names_rebar": rebar,
                     "registry": rc_txt, "importers": importers(path, rev=head) if exists else [],
                     "guard": g[0] if g else "UNCLASSIFIED", "guard_why": g[1] if g else ""})
    stale = sorted(set(GUARD) - set(mods))
    if stale:
        problems.append(f"GUARD names modules outside the window: {stale}")
    return rows, problems


def markdown(rows, base=BASE, head=HEAD):
    out = [f"Window: first-parent `{base[:8]}..{head[:8]}` (engine/ and tools/ .py files; A = added, M = modified).",
           "",
           "| # | Module | Merges (task status sha) | Names rebar | Registry class | Importers (engine/ tools/) | "
           "Default guard | Why |",
           "|---|---|---|---|---|---|---|---|"]
    for i, r in enumerate(rows, 1):
        t = "; ".join(f"{a} {s} {c}" for a, s, c, _ in r["touched"])
        imp = ", ".join(Path(p).stem for p in r["importers"]) or "none"
        out.append(f"| {i} | `{r['path']}` | {t} | {'yes' if r['names_rebar'] else 'no'} | {r['registry']} | {imp} | "
                   f"{r['guard']} | {r['guard_why']} |")
    return "\n".join(out) + "\n"


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] != "table":
        print(__doc__)
        return 2
    base, head, out = BASE, HEAD, None
    it = iter(argv[1:])
    for a in it:
        if a == "--base":
            base = next(it)
        elif a == "--head":
            head = next(it)
        elif a == "--out":
            out = next(it)
        else:
            print(f"unknown option {a}")
            return 2
    rows, problems = sweep(base, head)
    md = markdown(rows, base, head)
    if out:
        Path(out).write_text(md, encoding="utf-8")
    else:
        print(md)
    for p in problems:
        print("PROBLEM:", p)
    print(f"modules {len(rows)}; problems {len(problems)}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
