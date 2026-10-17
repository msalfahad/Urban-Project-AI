"""CODE MAP - the navigation layer for Claude Code (and people): where code, rules, tests and known defects live.

    python3 -I tools/codemap.py                 regenerate the four maps (only files under docs/ listed in MAPS are written)
    python3 -I tools/codemap.py check           read-only: exit 1 when a map is stale or a reference is broken (errors)
    python3 -I tools/codemap.py route "<task>"  primary / secondary topics for a task, with modules, rules, defects, tests
    python3 -I tools/codemap.py impact <path>   who imports a module, its risk class, and the tests that reach it

Maps (generated, never edited by hand):
    docs/ROUTE_QUICK.md   one table: task topic -> open first, risk, rules, tests, defects   (read this first)
    docs/ROUTING.md       per topic: modules, dependencies, rules, BOQ capability, defects, validation scope
    docs/CODEMAP.md       every module: lines, risk, importers, purpose; big modules list symbols with line ranges
    docs/RULES_INDEX.md   every rule: version, supersession, code that applies it, tests that prove it

The only hand-kept input is tools/routing_topics.json. Everything else is derived from the repository: git file list,
the Python import graph, the knowledge registry and rule store, the BOQ family master, the freeze baseline index and the
defect registers named in the topic file. Indexes are navigation aids: the code, the approved rule records, the drawings
and the original evidence stay authoritative. Stdlib only; deterministic (no timestamps; a register's date is read from its own text).
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict, deque
from functools import cached_property
from pathlib import Path

DEFAULT_ROOT = Path(__file__).resolve().parents[1]
MAPS = ("docs/ROUTE_QUICK.md", "docs/ROUTING.md", "docs/CODEMAP.md", "docs/RULES_INDEX.md")
TOPICS_FILE = "tools/routing_topics.json"
BIG = 1500
CAPABILITIES = ("INTEGRATED_AND_TESTED", "PARTIAL", "EXPERIMENTAL", "IMPLEMENTED_NOT_INTEGRATED", "BLOCKED_BY_SOURCE",
                "NOT_IMPLEMENTED", "UNKNOWN")
DEFECT_CLASSES = ("VERIFIED_OPEN", "REGRESSION_RISK", "HISTORICAL_UNVERIFIED", "UNKNOWN", "VERIFIED_FIXED", "SUPERSEDED")
UNRESOLVED = {"VERIFIED_OPEN", "HISTORICAL_UNVERIFIED", "UNKNOWN"}
RISKS = ("LOW", "MEDIUM", "HIGH", "CRITICAL")
HIGH_PATH = re.compile(r"(?:/cad/|kernel|/frame\.py$|unit|knowledge\.py$|rule_store\.py$|release|boq_line|boq_report|"
                       r"topology|robust_geometry|arch_rooms|arch_walls|arch_plan|canonical_build|realised\.py$|urban_boq_m9)")
REQUIRED_TOPIC_KEYS = ("id", "title", "keywords", "modules", "tests", "rules", "families", "defect_terms")
DEFECT_ID = re.compile(r"^(?:[A-Z]{1,2}\d+(?: \([A-Z]-?\d+\))?|[A-Z]-[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*)$")
FIXED = re.compile(r"\b(fixed|closed|corrected|resolved)\b", re.I)
SUPERSEDED = re.compile(r"\b(superseded|obsolete|replaced by)\b", re.I)


def cell(x, n=110):
    s = x if isinstance(x, str) else json.dumps(x, ensure_ascii=False)
    s = s.replace("|", "/").replace("\n", " ").strip()
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def first_line(text):
    for ln in (text or "").strip().splitlines():
        ln = ln.strip().strip("#").strip()
        if ln:
            return cell(ln, 140)
    return ""


def module_name(p):
    return p[:-3].replace("/", ".").removesuffix(".__init__")


def rank(items, key):
    """Most common first, ties by name: deterministic regardless of hash seed."""
    return sorted(items, key=lambda kv: (-key(kv), kv[0]))


class Problems:
    def __init__(self):
        self.errors, self.warnings = [], []

    def error(self, msg):
        self.errors.append(msg)

    def warn(self, msg):
        self.warnings.append(msg)


class Repo:
    """Read-only view of the repository. Every derived fact is cached and computed once."""

    def __init__(self, root=DEFAULT_ROOT):
        self.root = Path(root).resolve()

    # ------------------------------------------------------------------ files
    @cached_property
    def files(self):
        out = subprocess.run(["git", "-C", str(self.root), "ls-files", "--cached", "--others", "--exclude-standard"],
                             capture_output=True, text=True, check=True).stdout
        return sorted(p for p in set(out.splitlines()) if p and (self.root / p).is_file())

    def exists(self, p):
        return (self.root / p).is_file()

    def text(self, p):
        return (self.root / p).read_text(encoding="utf-8", errors="replace")

    def json(self, p):
        return json.loads(self.text(p))

    @cached_property
    def pys(self):
        return [p for p in self.files if p.endswith(".py")]

    @cached_property
    def code_modules(self):
        return [p for p in self.pys if p.startswith(("engine/", "tools/")) and not p.endswith("__init__.py")]

    @cached_property
    def test_files(self):
        return [p for p in self.pys if p.startswith("tests/") and p.rsplit("/", 1)[-1].startswith("test_")]

    # ------------------------------------------------------------------ python structure
    @cached_property
    def _graph_files(self):
        return [p for p in self.pys if p.startswith(("engine/", "tools/", "tests/", "pipeline/", "agents/"))]

    @cached_property
    def _parsed(self):
        return {}

    def _tree(self, p):
        if p not in self._parsed:
            try:
                self._parsed[p] = ast.parse(self.text(p))
            except SyntaxError:
                self._parsed[p] = None
        return self._parsed[p]

    def info(self, p):
        """(lines, purpose, [(start, end, 'def name' / 'class name')]) for public top-level symbols."""
        src = self.text(p)
        tree = self._tree(p)
        if tree is None:
            return src.count("\n") + 1, "(does not parse)", []
        tops = [(n.lineno, getattr(n, "end_lineno", n.lineno), ("class " if isinstance(n, ast.ClassDef) else "def ") + n.name)
                for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and not n.name.startswith("_")]
        return src.count("\n") + 1, first_line(ast.get_docstring(tree) or ""), tops

    IMPORT = re.compile(r"^[ \t]*(?:from[ \t]+(\.*[\w.]*)[ \t]+import[ \t]+(\([^)]*\)|[^\n#;]+)|import[ \t]+([^\n#;]+))", re.M)

    @cached_property
    def graph(self):
        """Static import graph read from import statements (top level and inside functions). Not edges: run-time
        loading (importlib, __import__), method dispatch by name, registries and data files (see dynamic_sites,
        string_refs). A docstring line that starts like an import statement can add a spurious edge."""
        by_mod = {module_name(p): p for p in self._graph_files}
        imports, imported_by = defaultdict(set), defaultdict(set)
        for p in self._graph_files:
            pkg = module_name(p) if p.endswith("__init__.py") else module_name(p).rsplit(".", 1)[0]
            src = self.text(p).replace("\\\n", " ").replace(";", "\n")  # backslash continuations; a; b on one line
            for m in self.IMPORT.finditer(src):
                if m.group(3):
                    names = [x.strip().split(" as ")[0].strip() for x in m.group(3).split(",")]
                else:
                    raw = m.group(1)
                    dots = len(raw) - len(raw.lstrip("."))
                    base = raw.lstrip(".")
                    if dots:
                        parts = pkg.split(".")
                        base = ".".join(parts[: len(parts) - (dots - 1)] + ([base] if base else []))
                    subs = [x.strip().split(" as ")[0].strip() for x in m.group(2).strip("() \n").replace("\n", " ").split(",")]
                    names = [base] + [f"{base}.{x}" for x in subs if x]
                for nm in names:
                    t = by_mod.get(nm)
                    if t and t != p and not t.endswith("__init__.py"):
                        imports[p].add(t)
                        imported_by[t].add(p)
        return imports, imported_by

    def importers(self, p, transitive=False):
        _, by = self.graph
        if not transitive:
            return set(by[p])
        seen, todo = set(), deque([p])
        while todo:
            for q in by[todo.popleft()]:
                if q not in seen:
                    seen.add(q)
                    todo.append(q)
        return seen

    @cached_property
    def dynamic_sites(self):
        """Files that load modules at run time (importlib / __import__): edges the static graph cannot see."""
        out = []
        for p in self.code_modules:
            t = self.text(p)
            if re.search(r"importlib\.(import_module|util\.spec_from_file_location)|__import__\(\s*f?[\"'](engine|tools)", t):
                out.append(p)
        return out

    def string_refs(self, p):
        """Code files that mention the module by name in a string (method routing, registries): possible hidden users."""
        dotted, fname = re.escape(module_name(p)), re.escape(p.rsplit("/", 1)[-1])
        pat = re.compile(rf"[\"'][^\"'\n]*(?:{dotted}|{re.escape(p)}|\b{fname})[^\"'\n]*[\"']")
        direct = self.importers(p)
        return sorted(q for q in self.code_modules if q != p and q not in direct and pat.search(self.text(q)))

    # ------------------------------------------------------------------ frozen and risk
    @cached_property
    def frozen(self):
        """Python files pinned by the freeze baseline index or hashed live by engine/freeze_manifest.py."""
        s = set()
        idx = "research/freeze_integrity/FREEZE_BASELINE_INDEX.jsonl"
        if self.exists(idx):
            for ln in self.text(idx).splitlines():
                if ln.strip():
                    pc = json.loads(ln).get("pinned_code") or []
                    s |= {k for k in pc if isinstance(k, str) and k.endswith(".py")}
        if self.exists("engine/freeze_manifest.py"):
            body = self.text("engine/freeze_manifest.py")
            m = re.search(r"def _live\(\).*?(?=\ndef )", body, re.S)
            for mod in re.findall(r"from engine import (\w+)", m.group(0) if m else ""):
                s.add(f"engine/{mod}.py")
        return {p for p in s if self.exists(p)}

    def risk(self, p, shared):
        if p in self.frozen:
            return "CRITICAL"
        if HIGH_PATH.search(p) or len(self.importers(p)) >= shared:
            return "HIGH"
        if p.startswith(("engine/", "tools/")):
            return "MEDIUM"
        return "LOW"

    # ------------------------------------------------------------------ rules and capability
    @cached_property
    def kb_versions(self):
        if not self.exists("engine/source/knowledge.py"):
            return []
        return re.findall(r'"(\d+\.\d+\.\d+)":\s*ROOT[^\n]*?(?:#\s*(.*))?$', self.text("engine/source/knowledge.py"), re.M)

    @cached_property
    def kb_rules(self):
        if not self.kb_versions:
            return []
        p = f"knowledge/URBAN_ENGINEERING_KNOWLEDGE_{self.kb_versions[-1][0]}.json"
        return sorted(self.json(p)["rules"], key=lambda r: r["rule_id"]) if self.exists(p) else []

    @cached_property
    def store_rules(self):
        lib_p = "rules/owner_library/URBAN_PROJECTS_RULE_LIBRARY_1.4.0.json"
        ov_p = "rules/owner_decisions/URBAN_RULES_1.5.0.json"
        eff = {}
        if self.exists(lib_p):
            eff = {r["rule_id"]: dict(r, origin="library 1.4.0") for r in self.json(lib_p)["rules"]}
        proposed = []
        if self.exists(ov_p):
            for r in self.json(ov_p)["records"]:
                if r.get("status") == "OWNER_APPROVED":
                    eff[r["rule_id"]] = dict(r, origin="overlay 1.5.0")
                else:
                    proposed.append(r)
        return eff, proposed

    @cached_property
    def all_rule_ids(self):
        return {r["rule_id"] for r in self.kb_rules} | set(self.store_rules[0])

    @cached_property
    def families(self):
        p = "rules/coverage/BOQ_FAMILY_MASTER_1.0.0.json"
        return self.json(p)["families"] if self.exists(p) else []

    def const(self, rel, name):
        if not self.exists(rel):
            return "?"
        m = re.search(rf"^{name}\s*=\s*(.+)$", self.text(rel), re.M)
        return m.group(1).strip() if m else "?"


# ====================================================================== topics and validation
def load_topics(repo, P):
    if not repo.exists(TOPICS_FILE):
        P.error(f"{TOPICS_FILE} is missing")
        return {"topics": [], "defect_sources": []}
    try:
        cfg = repo.json(TOPICS_FILE)
    except ValueError as e:
        P.error(f"{TOPICS_FILE} is not valid JSON: {e}")
        return {"topics": [], "defect_sources": []}
    seen = set()
    for t in cfg.get("topics", []):
        tid = t.get("id", "?")
        miss = [k for k in REQUIRED_TOPIC_KEYS if k not in t]
        if miss:
            P.error(f"topic {tid}: missing keys {miss}")
            continue
        if tid in seen:
            P.error(f"duplicate topic id {tid}")
        seen.add(tid)
        for key in ("modules", "tests", "rules", "families"):
            for pat in t[key]:
                try:
                    re.compile(pat)
                except re.error as e:
                    P.error(f"topic {tid}: malformed regex in {key}: {pat!r} ({e})")
        for s in t.get("start", []):
            if not repo.exists(s):
                P.error(f"topic {tid}: start module does not exist: {s}")
        for rid in t.get("rule_ids", []):
            if rid not in repo.all_rule_ids:
                P.error(f"topic {tid}: rule id not in the knowledge registry or rule store: {rid}")
        for rel in t.get("related", []):
            if rel not in {x.get("id") for x in cfg["topics"]}:
                P.error(f"topic {tid}: related topic does not exist: {rel}")
    for src in cfg.get("defect_sources", []):
        if not repo.exists(src.partition("#")[0]):
            P.error(f"defect source missing: {src}")
    return cfg


def compiled(t, key):
    out = []
    for pat in t.get(key, []):
        try:
            out.append(re.compile(pat))
        except re.error:
            pass
    return out


# ====================================================================== defects
def read_defects(repo, sources):
    """Every defect row of every register. Returns {id: [records oldest source first]}."""
    rows = defaultdict(list)
    for si, src in enumerate(sources):
        path, _, section = src.partition("#")
        if not repo.exists(path):
            continue
        date = register_date(repo, path)
        heading, active, header, status_i, sev_i = "", not section, None, None, None
        lines = repo.text(path).splitlines()
        for i, ln in enumerate(lines):
            if ln.startswith("#"):
                heading = ln.lstrip("#").strip()
                if section:
                    active = heading.startswith(section) or (active and not ln.startswith("## "))
                header = None
                continue
            if not active or not ln.startswith("|"):
                continue
            cells = [c.strip() for c in ln.strip().strip("|").split("|")]
            if i + 1 < len(lines) and re.match(r"^\|\s*:?-{3}", lines[i + 1]):
                header = [c.lower() for c in cells]
                status_i = next((k for k, h in enumerate(header) if "status" in h), None)
                sev_i = next((k for k, h in enumerate(header) if "severity" in h), None)
                continue
            if header is None or not cells or set(cells[0]) <= set("-: "):
                continue
            ids = [x.strip() for x in re.split(r"[,/]", cells[0].replace("*", "").replace("`", ""))]
            ids = [x for x in ids if DEFECT_ID.match(x) and re.search(r"\d", x) and not x.startswith("T-")]
            if not ids:
                continue
            h = heading.lower()
            if status_i is not None and status_i < len(cells):
                status = cells[status_i]
            elif "limitation" in h:
                status = "limitation (recorded)"
            elif re.search(r"fixed|closed|corrected", h):
                status = "fixed (per section heading)"
            else:
                status = "-"
            body = " ".join(cells[: status_i] if status_i else cells[:3])
            mods = sorted({m for tok in re.findall(r"`([^`]+)`", ln) for m in resolve_module(repo, tok)})
            tests = sorted({t for tok in re.findall(r"(tests/[\w/.-]+|test_\w+\.py)", ln) for t in resolve_test(repo, tok)})
            for did in ids:
                rows[did].append({
                    "id": did, "source_index": si, "summary": cell(cells[1] if len(cells) > 1 else "", 130),
                    "status": cell(status.replace("*", ""), 80), "severity": cell(cells[sev_i], 20) if sev_i is not None and sev_i < len(cells) else "-",
                    "evidence": f"{path} § {heading}", "evidence_date": date, "text": body.lower(), "modules": mods, "tests": tests})
    return rows


def register_date(repo, path):
    """The register's own date (first ISO date in its first 60 lines), else its phase folder. Never git history: a
    shallow clone would give a different answer and make the maps depend on clone depth."""
    head = "\n".join(repo.text(path).splitlines()[:60])
    m = re.search(r"\b(20\d\d-[01]\d-[0-3]\d)\b", head)
    if m:
        return m.group(1)
    parts = path.split("/")
    return f"phase {parts[-2]}" if len(parts) > 1 else "undated"


def resolve_module(repo, tok):
    tok = tok.split(":")[0].split("(")[0].strip()
    if not tok.endswith(".py"):
        return []
    if repo.exists(tok):
        return [tok]
    hits = [p for p in repo.pys if p.endswith("/" + tok)]  # engine/ and tools/ first, then research/ and the rest
    return sorted(hits, key=lambda p: (not p.startswith(("engine/", "tools/")), p))[:2]


def resolve_test(repo, tok):
    tok = tok.rstrip("/.")
    if tok.startswith("tests/"):
        return [tok] if (repo.root / tok).exists() else []
    return [p for p in repo.test_files if p.endswith("/" + tok)][:2]


def classify(records, newest):
    """One class per defect id from its newest record. VERIFIED_* = stated by the newest register (as of its git date),
    not re-tested by this tool; older registers never produce VERIFIED_OPEN."""
    r = dict(max(records, key=lambda x: x["source_index"]))
    st = r["status"]
    if not r["summary"] or r["summary"] == st:  # a carry-forward row with no description: keep the last real one
        older = [x["summary"] for x in sorted(records, key=lambda x: x["source_index"]) if x["summary"] and x["summary"] != x["status"]]
        r["summary"] = older[-1] if older else "(no description in the registers; open the evidence)"
    if SUPERSEDED.search(st):
        c = "SUPERSEDED"
    elif r["source_index"] == newest:
        c = "VERIFIED_FIXED" if FIXED.search(st) else ("UNKNOWN" if st.strip() in ("-", "") else "VERIFIED_OPEN")
    else:
        c = "REGRESSION_RISK" if FIXED.search(st) else ("UNKNOWN" if st.strip() in ("-", "") else "HISTORICAL_UNVERIFIED")
    r["text"] = " ".join(x["text"] for x in records)  # topic matching sees every description the defect ever had
    r["modules"] = sorted({m for x in records for m in x["modules"]})
    r["tests"] = sorted({t for x in records for t in x["tests"]})
    return dict(r, defect_class=c, unresolved=c in UNRESOLVED,
                history=[f"{x['evidence'].split(' § ')[0]}: {x['status']}" for x in sorted(records, key=lambda x: x["source_index"])[:-1]])


def defects_by_topic(repo, cfg):
    rows = read_defects(repo, cfg.get("defect_sources", []))
    newest = len(cfg.get("defect_sources", [])) - 1
    allc = {k: classify(v, newest) for k, v in rows.items()}
    out = {}
    for t in cfg["topics"]:
        mods = set(topic_modules(repo, t))
        out[t["id"]] = sorted((d for d in allc.values()
                               if any(re.search(rf"\b{re.escape(term.strip())}", d["text"]) for term in t["defect_terms"])
                               or mods & set(d["modules"])),
                              key=lambda d: (DEFECT_CLASSES.index(d["defect_class"]), d["id"]))
    return allc, out


# ====================================================================== per-topic facts
def topic_modules(repo, t):
    rx = compiled(t, "modules")
    return [p for p in repo.code_modules if any(r.search(p) for r in rx)]


def topic_facts(repo, cfg, t, shared):
    mods = topic_modules(repo, t)
    rules = [r for r in repo.kb_rules if any(re.search(x, r["rule_id"]) for x in t["rules"])] + \
            [r for r in repo.kb_rules if r["rule_id"] in t.get("rule_ids", []) and not any(re.search(x, r["rule_id"]) for x in t["rules"])]
    srules = [r for k, r in sorted(repo.store_rules[0].items()) if any(re.search(x, k) for x in t["rules"])]
    fams = [f for f in repo.families if any(re.search(x, f["code"]) for x in t["families"])]
    code = []
    for r in rules:
        for c in r.get("code") or []:
            c = c.split("::")[0]
            if c.endswith(".py") and c not in code and repo.exists(c):
                code.append(c)
    hint = [h for h in t.get("start", []) if repo.exists(h)]
    top = sorted((m for m in mods if m.startswith("engine/source/")), key=lambda m: (-len(repo.importers(m)), m))
    start = hint + [c for c in code if c in mods and c not in hint][: max(0, 4 - len(hint))]
    start += [m for m in top if m not in start][: max(0, 3 - len(start))]
    start += [c for c in code if c not in start][: max(0, 6 - len(start))]
    rule_tests = sorted({x.split("::")[0] for r in rules for x in (r.get("tests") or []) if repo.exists(x.split("::")[0])})
    trx = compiled(t, "tests")
    tdirs = Counter(p.rsplit("/", 1)[0] for p in repo.test_files if any(r.search(p) for r in trx))
    importer_tests = Counter()
    for s in start:
        for q in repo.importers(s, transitive=True):
            if q.startswith("tests/"):
                importer_tests[q.rsplit("/", 1)[0]] += 1
    risks = [repo.risk(s, shared) for s in start] + [t.get("risk", "LOW")]
    risk = max(risks, key=RISKS.index) if start or t.get("risk") else "LOW"
    caps = Counter(f.get("capability", "UNKNOWN") for f in fams)
    return {"mods": mods, "rules": rules, "srules": srules, "fams": fams, "caps": caps, "start": start, "rule_tests": rule_tests,
            "tdirs": tdirs, "importer_tests": importer_tests, "risk": risk}


def cap_summary(caps):
    return ", ".join(f"{k} {caps[k]}" for k in CAPABILITIES if caps.get(k)) or "no BOQ family mapped"


def levels(f, risk):
    folders = [d for d, _ in rank(f["tdirs"].items(), lambda kv: kv[1])][:6]
    wider = [d for d, _ in rank(f["importer_tests"].items(), lambda kv: kv[1]) if d not in folders][:6]
    pyt = "PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -p no:cacheprovider -q"
    L1 = f"{pyt} " + " ".join(f["rule_tests"][:6]) if f["rule_tests"] else f"{pyt} " + " ".join(folders[:1]) if folders else "(no test mapped: write a focused test first)"
    L2 = f"{pyt} " + " ".join(folders) if folders else L1
    L3 = (f"{pyt} " + " ".join(folders + wider)) if wider else L2
    rec = {"LOW": "L1", "MEDIUM": "L2", "HIGH": "L3", "CRITICAL": "L4"}[risk]
    return rec, L1, L2, L3


# ====================================================================== renderers
def render_quick(repo, cfg, facts, dmap):
    L = ["# Route quick reference", "",
         "Generated by `tools/codemap.py` (do not edit). Find the task's topic here, then open the first module. For a task in",
         "words run `python3 -I tools/codemap.py route \"<task>\"`; for a file you will change run `... impact <path>`.",
         "Details per topic: `docs/ROUTING.md`. Risk is a validation guide, never a reason to skip a test.", "",
         "| Topic | Ask about | Open first | Risk | Rules | Defects open / regression-risk | BOQ items integrated / mapped |",
         "|---|---|---|---|---|---|---|"]
    for t in cfg["topics"]:
        f = facts[t["id"]]
        ds = dmap[t["id"]]
        op = sum(1 for d in ds if d["unresolved"])
        rr = sum(1 for d in ds if d["defect_class"] == "REGRESSION_RISK")
        first = ", ".join(f"`{s}`" for s in f["start"][:2]) or "**not implemented**"
        L.append(f"| [{t['id']}](ROUTING.md#{t['id']}) | {', '.join(t['keywords'][:5])} | {first} | {f['risk']} | "
                 f"{len(f['rules']) + len(f['srules'])} | {op} / {rr} | {f['caps'].get('INTEGRATED_AND_TESTED', 0)} / {len(f['fams'])} |")
    L += ["", "Risk: CRITICAL = frozen code or engineering authority; HIGH = geometry, CAD, units, rooms, walls, release, aggregation or",
          "widely imported; MEDIUM = local engine logic; LOW = docs and tooling. Validation levels L1-L4 are in `docs/ROUTING.md`."]
    return "\n".join(L) + "\n"


def render_routing(repo, cfg, facts, dmap, P, shared):
    newest = cfg["defect_sources"][-1].partition("#")[0] if cfg.get("defect_sources") else "-"
    L = ["# Task routing index", "",
         "Generated by `tools/codemap.py` from the code, the rule files, the BOQ family master and the defect registers; the only",
         "hand-kept input is `tools/routing_topics.json`. The compact view is `docs/ROUTE_QUICK.md`. Sources stay authoritative.", "",
         "## How to use it", "",
         "1. Find the topic (or run `python3 -I tools/codemap.py route \"<task>\"`). A task may span several topics.",
         "2. Read the topic's rules and unresolved defects, then open the **open first** modules at the symbol you need.",
         "3. Before editing a module run `python3 -I tools/codemap.py impact <path>`; follow its risk class below.",
         "", "## Validation levels (chosen by judgement; nothing is skipped automatically)", "",
         "| Level | When | What |", "|---|---|---|",
         "| L1 | while iterating; LOW risk | `py_compile` of the changed file + the rule tests / one test folder of the topic |",
         "| L2 | MEDIUM: one subsystem | the topic's test folders |",
         "| L3 | HIGH: shared code, geometry, CAD, units, rooms, walls, release | L2 + the test folders that import the changed module (`impact`) + the freeze check |",
         "| L4 | CRITICAL, method-version release, acceptance handoff | full suite on the final commit, compared test by test with the baseline; freeze check; record the commit |",
         "", "The freeze check runs after any change under `engine/`, `tools/`, `rules/`, `knowledge/` or `data/registry/`, at every level:",
         "`PYTHONDONTWRITEBYTECODE=1 python3 -I tools/freeze_verify.py check --index research/freeze_integrity/FREEZE_BASELINE_INDEX.jsonl`.",
         "A full-suite result belongs to the commit it ran on; later changes need their own validation.", "",
         "## Defect classes", "",
         f"VERIFIED_OPEN / VERIFIED_FIXED: as stated by the newest register (`{newest}`), not re-tested by this tool. "
         "REGRESSION_RISK: reported fixed in an older register; only its tests protect it. HISTORICAL_UNVERIFIED: reported open in an "
         "older register and not restated since; confirm before relying on it. UNKNOWN: no status recorded. SUPERSEDED: replaced. "
         "A defect is never marked fixed because a newer report omits it.", "",
         "## Dependency limits", "",
         "Import edges are static. Not visible as edges: run-time loading (" + ", ".join(f"`{p}`" for p in repo.dynamic_sites) +
         "), method selection by name in `tools/urban_boq_m9.py`, rule and knowledge records that name code in strings, and data files. "
         "`impact` lists string references as possible hidden users; treat its importer list as a lower bound.", ""]
    for t in cfg["topics"]:
        f = facts[t["id"]]
        ds = dmap[t["id"]]
        rec, L1, L2, L3 = levels(f, f["risk"])
        L += [f"<a id=\"{t['id']}\"></a>", f"## {t['title']}", "",
              f"Risk **{f['risk']}** (recommended validation {rec}). Ask about: {', '.join(t['keywords'])}." +
              (f" Related topics: {', '.join(t.get('related', []))}." if t.get("related") else "") +
              (f" Note: {t['note']}" if t.get("note") else ""), ""]
        if not f["mods"]:
            gaps = "; ".join(f"{x['code']} {x['item_en']} ({x['capability']})" for x in f["fams"])
            L += [f"**No module implements this topic.** BOQ families: {gaps or 'none mapped'}.", ""]
        else:
            L += ["**Open first:**", ""]
            for s in f["start"]:
                n = len(repo.importers(s))
                nt = len(repo.importers(s, transitive=True))
                L.append(f"- `{s}` ({repo.info(s)[0]} lines, {repo.risk(s, shared)}{', frozen' if s in repo.frozen else ''}; "
                         f"imported by {n} directly, {nt} transitively{', SHARED' if n >= shared else ''})")
            imports, _ = repo.graph
            deps = Counter(d for s in f["start"] for d in imports[s] if d not in f["start"])
            if deps:
                L += ["", "**Depends on:** " + ", ".join(f"`{d}`" for d, _ in rank(deps.items(), lambda kv: kv[1])[:10])]
            cur = [m for m in f["mods"] if m.startswith("engine/source/") and m not in f["start"]]
            old = [m for m in f["mods"] if not m.startswith("engine/source/") and m not in f["start"]]
            if cur:
                L += ["", "**Other current modules:** " + ", ".join(f"`{m.rsplit('/', 1)[1]}`" for m in cur)]
            if old:
                L += ["", "**Earlier generations and tools** (check which method uses them before reuse): " +
                      ", ".join(f"`{m}`" for m in old[:16]) + (f" +{len(old) - 16} more" if len(old) > 16 else "")]
        if f["rules"] or f["srules"]:
            L += ["", "**Rules** (knowledge " + (repo.kb_versions[-1][0] if repo.kb_versions else "?") + "; full records in `docs/RULES_INDEX.md`): " +
                  "; ".join(f"{r['rule_id']} [{r.get('status', '')}] {cell(r.get('title', ''), 60)}" for r in f["rules"]) +
                  ("; rule store (frozen methods): " + ", ".join(r["rule_id"] for r in f["srules"]) if f["srules"] else "")]
        if f["fams"]:
            L += ["", f"**BOQ capability** (exact registry statuses): {cap_summary(f['caps'])}. "
                  "Only INTEGRATED_AND_TESTED counts as supported; a module or a synthetic test is not real-villa validation."]
        L += ["", f"**Validation:** L1 `{L1}`", f"L2 `{L2}`", f"L3 `{L3}` + freeze check", "L4 full suite + freeze check (see above)"]
        if ds:
            L += ["", f"**Known defects** ({sum(1 for d in ds if d['unresolved'])} unresolved of {len(ds)}):", "",
                  "| Id | Class | Reported status | Defect | Modules | Evidence (date) |", "|---|---|---|---|---|---|"]
            for d in ds:
                L.append(f"| {d['id']} | {d['defect_class']} | {d['status']} | {d['summary']} | "
                         f"{', '.join(f'`{m}`' for m in d['modules']) or '-'} | `{d['evidence']}` ({d['evidence_date']}) |")
        L.append("")
    if cfg.get("_unrouted"):
        L += ["## Defects not matched to a topic", "", "Listed so none is hidden; add a defect term to a topic to route them.", "",
              "| Id | Class | Reported status | Defect | Evidence (date) |", "|---|---|---|---|---|"]
        L += [f"| {d['id']} | {d['defect_class']} | {d['status']} | {d['summary']} | `{d['evidence']}` ({d['evidence_date']}) |"
              for d in cfg["_unrouted"]]
        L.append("")
    if P.warnings:
        L += ["## Index warnings", ""] + [f"- {w}" for w in P.warnings]
    return "\n".join(L).rstrip() + "\n"


PURPOSE = {
    "engine": "Quantity engine. `engine/source/` is the current CAD-to-BOQ pipeline; the rest is earlier rounds and shared services.",
    "tools": "Command-line entry points: intake, takeoff routes (`urban_boq_m*.py`), exports, freeze and manifest checks, this map.",
    "rules": "Rule store read by methods V1-V2.2 (library 1.4.0 + owner overlay 1.5.0), materials, BOQ families, method registers.",
    "knowledge": "Engineering knowledge registry: the rules read by ARCH_TAKEOFF_V2.3 and later.",
    "data": "Registries (owner facts, project rules, trades) and trade rules. Large run data is gitignored.",
    "tests": "pytest suites, one folder per round.",
    "research": "Per-phase reports, proofs, defect registers and freeze baselines: the evidence behind decisions.",
    "docs": "Design notes and the generated maps.",
    "agents": "Business agents a1-a17, each with prompt, schema and tests.",
    "pipeline": "Project creation and end-to-end orchestration.",
}
CODE_DIRS = ("engine", "tools", "pipeline", "integrations", "documents", "social")


def render_codemap(repo, shared):
    top = Counter(p.split("/")[0] for p in sorted(set(repo.files) | set(MAPS)) if "/" in p)  # maps counted before they exist
    L = ["# Code map", "",
         "Generated by `tools/codemap.py` (do not edit). Start from `docs/ROUTE_QUICK.md`; use this map to find a module and",
         "the line range of a symbol, then read that range (widen it whenever correctness needs more). Risk: CRITICAL frozen,",
         "HIGH shared or geometry/units/release, MEDIUM engine logic. `Imp` = modules importing it directly.", "",
         "## Top-level folders", "", "| Folder | Files | What lives there |", "|---|---|---|"]
    L += [f"| `{d}/` | {n} | {PURPOSE.get(d, '')} |" for d, n in sorted(top.items())]
    for root in CODE_DIRS:
        groups = defaultdict(list)
        for p in repo.pys:
            if p.startswith(root + "/") and not p.endswith("__init__.py"):
                groups[p.rsplit("/", 1)[0]].append(p)
        for g in sorted(groups):
            L += ["", f"## `{g}/` ({len(groups[g])} modules)", "", "| Module | Lines | Risk | Imp | Purpose |", "|---|---|---|---|---|"]
            bigs = []
            for p in sorted(groups[g]):
                n, doc, tops = repo.info(p)
                L.append(f"| `{p.rsplit('/', 1)[1]}` | {n} | {repo.risk(p, shared)} | {len(repo.importers(p))} | {doc} |")
                if n >= BIG and tops:
                    bigs.append((p, tops))
            for p, tops in bigs:
                L += ["", f"`{p}` symbols: " + ", ".join(f"{name} (L{a}-{b})" for a, b, name in tops[:60])]
    agents = sorted({p.split("/")[1] for p in repo.files if p.startswith("agents/a")})
    L += ["", "## `agents/`", "", "| Agent | Purpose |", "|---|---|"]
    L += [f"| `{a}` | {repo.info(f'agents/{a}/agent.py')[1] if repo.exists(f'agents/{a}/agent.py') else ''} |" for a in agents]
    tdirs = Counter(p.rsplit("/", 1)[0] for p in repo.test_files)
    L += ["", "## `tests/` (test files per folder)", "", "| Folder | Test files |", "|---|---|"]
    L += [f"| `{d}/` | {n} |" for d, n in sorted(tdirs.items())]
    docs = [p for p in repo.files if p.startswith("docs/") and p.endswith(".md") and p not in MAPS]
    L += ["", "## `docs/`", "", "| File | Title |", "|---|---|"]
    L += [f"| `{p[5:]}` | {first_line(repo.text(p)[:2000])} |" for p in docs]
    rs = Counter(p.split("/")[1] for p in repo.files if p.startswith("research/") and p.count("/") >= 2)
    L += ["", "## `research/` (evidence folders)", "", "| Folder | Files |", "|---|---|"]
    L += [f"| `research/{d}/` | {n} |" for d, n in sorted(rs.items())]
    return "\n".join(L) + "\n"


def render_rules(repo, P):
    kv = repo.kb_versions
    latest = kv[-1][0] if kv else "?"
    L = ["# Rules index", "",
         "Generated by `tools/codemap.py` from the rule files (do not edit). The rule records themselves are authoritative.",
         "Rule files are versioned: never edit an existing version; add the next one (see the end of this file).", "",
         "## Which rule set each method reads", "", "| Rule set | Files | Loader | Read by |", "|---|---|---|---|",
         f"| Rule store (library + owner overlay) | `rules/owner_library/`, `rules/owner_decisions/` | `engine/source/rule_store.py` "
         f"(LATEST_APPROVED = {repo.const('engine/source/rule_store.py', 'LATEST_APPROVED')}) | ARCH_TAKEOFF_V1 to V2.2 (frozen) |",
         "| Engineering knowledge registry | `knowledge/URBAN_ENGINEERING_KNOWLEDGE_<v>.json` | `engine/source/knowledge.py` (`using(version)`) | "
         "V2.3 = 1.0.0, V2.4 = 1.1.0" + "".join(f", {c.replace('ARCH_TAKEOFF_', '')} = {v}" for v, c in kv if c) + " |",
         f"| Methods | `tools/urban_boq_m9.py` `ARCH_METHODS` | `arch_compute(method=...)` | CLI route |", ""]
    rules = repo.kb_rules
    L += [f"## Engineering knowledge {latest} ({len(rules)} rules)", "",
          "| Rule | Version | Status | Title | Supersedes / superseded by | Code | Tests |", "|---|---|---|---|---|---|---|"]
    for r in rules:
        sup = ", ".join(r.get("supersedes") or []) + (" / " + (r.get("superseded_by") if isinstance(r.get("superseded_by"), str) else ", ".join(r.get("superseded_by") or [])) if r.get("superseded_by") else "")
        code = []
        for c in (r.get("code") or []):
            path = c.split("::")[0]
            if path.endswith(".py") and not repo.exists(path):
                P.warn(f"rule {r['rule_id']}: code reference does not resolve: {c}")
            code.append(f"`{c}`")
        tests = sorted({x.split("::")[0] for x in (r.get("tests") or [])})
        for x in tests:
            if not repo.exists(x):
                P.warn(f"rule {r['rule_id']}: test reference does not resolve: {x}")
        L.append(f"| {r['rule_id']} | {r.get('effective_version', '')} | {r.get('status', '')} | {cell(r.get('title', ''))} | {sup or '-'} | "
                 f"{', '.join(code[:3])} | {', '.join(f'`{x}`' for x in tests[:2])} |")
    eff, prop = repo.store_rules
    L += ["", f"## Rule store 1.5.0 effective rules ({len(eff)}; library 1.4.0 + approved overlay)", "",
          "| Rule | Trade | Scope | Rule name | Unit | Mandatory | Version | From |", "|---|---|---|---|---|---|---|---|"]
    for k in sorted(eff):
        r = eff[k]
        L.append(f"| {k} | {r.get('trade', '')} | {r.get('scope', '')} | {cell(r.get('rule_name', ''))} | {r.get('unit', '')} | "
                 f"{r.get('default_or_mandatory', '')} | {r.get('version', '')} | {r['origin']} |")
    if prop:
        L += ["", "Proposed, not in force: " + ", ".join(f"{r['rule_id']} ({cell(r.get('rule_name', ''), 70)})" for r in prop)]
    for title, rel, key, cols in (
            ("Method register V3 (`rules/methods/`)", "rules/methods/URBAN_METHOD_REGISTER_V3.json", "methods",
             (("Method id", "id"), ("Applies to", "applies_to"), ("Statement", "statement"))),
            ("Material specs (`rules/materials/`)", "rules/materials/URBAN_MATERIAL_SPECS_1.0.0.json", "specs",
             (("Spec", "spec_id"), ("Kind", "kind"), ("Name", "name_en"))),
            ("BOQ families (`rules/coverage/`, exact capability)", "rules/coverage/BOQ_FAMILY_MASTER_1.0.0.json", "families",
             (("Code", "code"), ("Group", "group"), ("Item", "item_en"), ("Unit", "unit"), ("Capability", "capability"))),
            ("Trades (`data/registry/trades.json`)", "data/registry/trades.json", "trades",
             (("Trade", "trade_id"), ("English", "display_name_en"), ("Arabic", "display_name_ar"), ("Unit", "quantity_unit")))):
        if not repo.exists(rel):
            continue
        items = repo.json(rel)[key]
        L += ["", f"## {title} ({len(items)})", "", "| " + " | ".join(c for c, _ in cols) + " |", "|" + "---|" * len(cols)]
        L += ["| " + " | ".join(cell(", ".join(x[k]) if isinstance(x.get(k), list) else x.get(k, ""), 140) for _, k in cols) + " |" for x in items]
    reg = [p for p in repo.files if p.startswith(("data/registry/", "data/trade_rules/")) and p.endswith(".json")]
    L += ["", "## Owner facts, project rules and trade rules (`data/`)", "", "| File | Top-level keys |", "|---|---|"]
    for p in reg:
        try:
            d = repo.json(p)
            keys = ", ".join(list(d)[:8]) if isinstance(d, dict) else f"list of {len(d)}"
        except ValueError:
            keys = "(not JSON)"
        L.append(f"| `{p}` | {keys} |")
    L += ["", "## How to change a rule", "",
          "1. Find the rule above: its rule set, the code that applies it and its tests.",
          f"2. Methods V2.3+: build the next `knowledge/URBAN_ENGINEERING_KNOWLEDGE_<v>.json` from {latest} (follow the latest "
          "`tools/kb_build_*.py`), register it in `VERSIONS` in `engine/source/knowledge.py`, bind it to a new method version.",
          "3. Frozen V1-V2.2 rule store: a new `rules/owner_decisions/URBAN_RULES_<next>.json` overlay, added to `VERSIONS` in "
          "`engine/source/rule_store.py`; then `python3 -I tools/m9_rules_manifest.py build` and `check`.",
          "4. Run the rule's tests and the freeze check; regenerate the maps (`python3 -I tools/codemap.py`)."]
    return "\n".join(L) + "\n"


# ====================================================================== build / check
def prepare(repo):
    P = Problems()
    cfg = load_topics(repo, P)
    shared = cfg.get("shared_threshold", 10)
    if not cfg.get("topics"):
        P.error("no topics defined")
    facts = {t["id"]: topic_facts(repo, cfg, t, shared) for t in cfg.get("topics", []) if all(k in t for k in REQUIRED_TOPIC_KEYS)}
    cfg["topics"] = [t for t in cfg.get("topics", []) if t.get("id") in facts]
    for t in cfg["topics"]:
        f = facts[t["id"]]
        if not f["mods"] and any(f["caps"].get(c) for c in ("INTEGRATED_AND_TESTED", "PARTIAL", "EXPERIMENTAL")):
            P.warn(f"topic {t['id']}: no module matches although the registry lists implemented BOQ items")
        for pat in t["rules"]:
            if not any(re.search(pat, rid) for rid in repo.all_rule_ids):
                P.error(f"topic {t['id']}: rule pattern {pat!r} matches no rule in the knowledge registry or rule store")
    allc, dmap = defects_by_topic(repo, cfg) if cfg["topics"] else ({}, {})
    routed = {d["id"] for ds in dmap.values() for d in ds}
    cfg["_unrouted"] = sorted((d for k, d in allc.items() if k not in routed), key=lambda d: d["id"])
    return P, cfg, facts, dmap


def build(repo):
    P, cfg, facts, dmap = prepare(repo)
    shared = cfg.get("shared_threshold", 10)
    rules_md = render_rules(repo, P)
    out = {
        "docs/ROUTE_QUICK.md": render_quick(repo, cfg, facts, dmap),
        "docs/CODEMAP.md": render_codemap(repo, shared),
        "docs/RULES_INDEX.md": rules_md,
    }
    out["docs/ROUTING.md"] = render_routing(repo, cfg, facts, dmap, P, shared)
    return out, P, cfg, facts, dmap


def cmd_build(repo, check):
    out, P, *_ = build(repo)
    stale = [k for k, v in out.items() if not repo.exists(k) or repo.text(k) != v]
    for e in P.errors:
        print("error:", e)
    for w in P.warnings:
        print("warning:", w)
    if check:
        print("stale:", ", ".join(stale) if stale else "none")
        return 1 if stale or P.errors else 0
    if P.errors:
        print("not written: fix the errors above")
        return 1
    for k, v in out.items():
        (repo.root / k).parent.mkdir(parents=True, exist_ok=True)
        (repo.root / k).write_text(v, encoding="utf-8")
        print("written", k, v.count("\n"), "lines")
    return 0


# ====================================================================== route / impact
def score_topics(repo, cfg, facts, dmap, task):
    text = task.lower()
    toks = set(re.findall(r"[a-z0-9_]+(?:\.py)?", text))
    ids = set(re.findall(r"\b([A-Z]{1,3}(?:-[A-Z0-9]+)+-?\d*|B\d+(?:-\d+)?)\b", task))
    scores = {}
    for t in cfg["topics"]:
        f = facts[t["id"]]
        why, s = [], 0
        for kw in t["keywords"]:
            if re.search(rf"\b{re.escape(kw.lower())}", text):
                s += 3
                why.append(kw)
        stems = {m.rsplit("/", 1)[1][:-3] for m in f["mods"]}
        for tok in toks:
            if tok.removesuffix(".py") in stems:
                s += 4
                why.append(tok)
        for r in f["rules"] + f["srules"]:
            if r["rule_id"] in ids or r["rule_id"].lower() in text:
                s += 5
                why.append(r["rule_id"])
        for fam in f["fams"]:
            if fam["code"] in ids:
                s += 5
                why.append(fam["code"])
        for d in dmap[t["id"]]:
            if d["id"] in ids or d["id"].split(" ")[0] in ids:
                s += 5
                why.append(d["id"])
        for d in f["tdirs"]:
            if "/" in d and re.search(rf"{re.escape(d.lower())}(?:/|\b)", text):  # a named test folder, not the word "tests"
                s += 4
                why.append(d)
        sym = {name.split(" ", 1)[1] for m in f["start"] for _, _, name in repo.info(m)[2]}
        for tok in toks:
            if "_" in tok and tok in sym:
                s += 2
                why.append(tok + "()")
        if s:
            scores[t["id"]] = (s, sorted(set(why)))
    return scores


def cmd_route(repo, task, as_json=False):
    P, cfg, facts, dmap = prepare(repo)
    scores = score_topics(repo, cfg, facts, dmap, task)
    order = sorted(scores, key=lambda k: (-scores[k][0], k))
    if not order:
        print("No topic matched. Use docs/ROUTE_QUICK.md or docs/CODEMAP.md, or add keywords to tools/routing_topics.json.")
        return 2
    primary = order[0]
    secondary = [k for k in order[1:] if scores[k][0] >= max(3, scores[primary][0] * 0.3)][:3]
    by_id = {t["id"]: t for t in cfg["topics"]}
    related = [r for r in by_id[primary].get("related", []) if r not in secondary][: max(0, 3 - len(secondary))]
    res = {"task": task, "primary": primary, "secondary": secondary, "related": related, "topics": {}}
    for k in [primary] + secondary + related:
        f, t = facts[k], by_id[k]
        rec, L1, L2, L3 = levels(f, f["risk"])
        ds = dmap[k]
        res["topics"][k] = {
            "title": t["title"], "score": scores.get(k, (0, []))[0], "matched": scores.get(k, (0, []))[1], "risk": f["risk"],
            "open_first": f["start"], "rules": [r["rule_id"] for r in f["rules"]] + [r["rule_id"] for r in f["srules"]],
            "capability": dict(f["caps"]),
            "defects_unresolved": [f"{d['id']} {d['defect_class']}: {d['summary']}" +
                                   (f" [{', '.join(d['modules'])}]" if d["modules"] else "") for d in ds if d["unresolved"]],
            "defects_regression_risk": [d["id"] for d in ds if d["defect_class"] == "REGRESSION_RISK"],
            "validation": {"recommended": rec, "L1": L1, "L2": L2, "L3": L3 + " + freeze check"},
            "evidence": f"docs/ROUTING.md#{k}"}
    if as_json:
        print(json.dumps(res, indent=1, ensure_ascii=False))
        return 0
    print(f"Task: {task}")
    print(f"Primary: {primary} (score {scores[primary][0]}: {', '.join(scores[primary][1])})")
    if secondary:
        print("Secondary: " + ", ".join(f"{k} ({scores[k][0]}: {', '.join(scores[k][1][:4])})" for k in secondary))
    if related:
        print("Related (from the topic file): " + ", ".join(related))
    for k, v in res["topics"].items():
        print(f"\n== {k} [{v['risk']}] {v['title']}")
        print("open first: " + ", ".join(v["open_first"][:4]) if v["open_first"] else "open first: NOT IMPLEMENTED (see BOQ capability)")
        if v["rules"]:
            print("rules: " + ", ".join(v["rules"][:14]) + (" ..." if len(v["rules"]) > 14 else ""))
        print("BOQ capability: " + cap_summary(Counter(v["capability"])))
        for d in v["defects_unresolved"][:8]:
            print("defect: " + d)
        if v["defects_regression_risk"]:
            print("regression risk (fixed earlier, tests protect it): " + ", ".join(v["defects_regression_risk"][:10]))
        print(f"validation (recommended {v['validation']['recommended']}): L1 {v['validation']['L1']}")
        if k == primary:
            print(f"  L2 {v['validation']['L2']}\n  L3 {v['validation']['L3']}")
        print(f"details: {v['evidence']}")
    print("\nThe freeze check runs after any engine/tools/rules/knowledge/data change. Nothing above skips a test.")
    return 0


def cmd_impact(repo, path, as_json=False):
    P = Problems()
    cfg = load_topics(repo, P)
    shared = cfg.get("shared_threshold", 10)
    if not repo.exists(path):
        print(f"error: {path} does not exist")
        return 1
    imports, _ = repo.graph
    direct = sorted(repo.importers(path))
    trans = sorted(repo.importers(path, transitive=True))
    tests_direct = sorted({q.rsplit("/", 1)[0] for q in direct if q.startswith("tests/")})
    tests_trans = Counter(q.rsplit("/", 1)[0] for q in trans if q.startswith("tests/"))
    topics = [t["id"] for t in cfg.get("topics", []) if all(k in t for k in REQUIRED_TOPIC_KEYS) and path in topic_modules(repo, t)]
    risk = repo.risk(path, shared) if path.endswith(".py") else ("CRITICAL" if path.startswith(("knowledge/", "rules/")) else "MEDIUM" if path.startswith("data/registry/") else "LOW")
    sref = repo.string_refs(path) if path.endswith(".py") else []
    res = {"path": path, "risk": risk, "frozen": path in repo.frozen, "topics": topics,
           "imports": sorted(imports[path]), "imported_by_direct": direct, "imported_by_transitive_count": len(trans),
           "test_folders_direct": tests_direct,
           "test_folders_transitive": [d for d, _ in rank(tests_trans.items(), lambda kv: kv[1])],
           "possible_hidden_users_by_string": sref,
           "dynamic_loading_sites": repo.dynamic_sites}
    if as_json:
        print(json.dumps(res, indent=1))
        return 0
    print(f"{path}: risk {risk}{' (FROZEN: never edit in place; add a new version)' if res['frozen'] else ''}; topics: {', '.join(topics) or '-'}")
    print(f"imports {len(res['imports'])}; imported by {len(direct)} directly, {len(trans)} transitively{' (SHARED)' if len(direct) >= shared else ''}")
    if tests_direct:
        print("tests importing it directly: " + ", ".join(tests_direct))
    if res["test_folders_transitive"]:
        print("test folders reaching it (most first): " + ", ".join(res["test_folders_transitive"][:12]) +
              (f" +{len(res['test_folders_transitive']) - 12} more" if len(res["test_folders_transitive"]) > 12 else ""))
    if sref:
        print("mentioned by name (possible run-time users, not in the import graph): " + ", ".join(sref[:10]))
    print("limits: static imports only; run-time loading in " + ", ".join(repo.dynamic_sites) + " is not followed.")
    rec = {"LOW": "L1", "MEDIUM": "L2", "HIGH": "L3", "CRITICAL": "L4"}[risk]
    print(f"recommended validation: {rec} (docs/ROUTING.md); freeze check after the change.")
    return 0


def main(argv=None, root=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--root", default=str(root or DEFAULT_ROOT))
    ap.add_argument("--check", action="store_true", help="same as the check command")
    sp = ap.add_subparsers(dest="cmd")
    sp.add_parser("build")
    sp.add_parser("check")
    r = sp.add_parser("route")
    r.add_argument("task")
    r.add_argument("--json", action="store_true")
    i = sp.add_parser("impact")
    i.add_argument("path")
    i.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    repo = Repo(a.root)
    if a.cmd == "route":
        return cmd_route(repo, a.task, a.json)
    if a.cmd == "impact":
        return cmd_impact(repo, a.path, a.json)
    return cmd_build(repo, check=a.check or a.cmd == "check")


if __name__ == "__main__":
    sys.exit(main())
