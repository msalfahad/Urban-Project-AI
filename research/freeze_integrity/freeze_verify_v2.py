"""Freeze integrity verifier V2 (T-467, owner directive 2026-11-02 E1). Stdlib only; it never writes into the repository
except `index --write FILE` (an append to a hash-chained JSONL file).

Why a V2: the V1 baseline index (research/freeze_integrity/FREEZE_BASELINE_INDEX.jsonl, 42 entries) pins the frozen
research manifests and the owner rule files, but no code of the RELEASED method (ARCH_TAKEOFF_V2.9 + route G): neither
tools/urban_boq_m9.py nor any engine/source/arch_v* module. The V2 index is a NEW file; V1 and tools/freeze_verify.py are
not edited. The V2 index starts with the V1 index bytes unchanged (so every V1 entry stays checked, and `check` refuses a
V2 index whose head is not the current V1 file) and appends, from a declared released-path spec
(research/freeze_integrity/RELEASED_PATH_V2_9_ROUTE_G.json):

  RELEASED_CODE          a whole .py file of the released path (sha256 of its bytes): one changed byte is a difference
  RELEASED_DATA          a versioned rule / knowledge / profile file the released code reads (sha256 of its bytes)
  RELEASED_CODE_SYMBOLS  a shared registration hub (tools/urban_boq_m9.py): every top-level statement that existed at
                         indexing time, by name (def / class / assignment: the sha256 of its full source lines, decorators
                         included) or, for an unnamed statement (import, if, docstring), by its own text. The integration
                         lane must keep adding methods to this file, so: NEW top-level statements are allowed as long as
                         they bind no frozen name; a changed, removed, or re-bound frozen statement is a difference. The
                         two declared hub functions (cmd_arch, main) are listed and NOT hashed: every method registration
                         edits them. Their released behaviour is guarded by the golden run (tests/t467_released_freeze).

Subcommands
  index   --spec SPEC [--v1 V1] [--write FILE]   the V2 entries at the working tree (print), or append them to FILE (a new
                                                 FILE starts as a byte copy of V1); entries already in FILE must match
  check   --index FILE [--v1 V1]                 exit 1 if any indexed artefact, released file or frozen symbol differs;
                                                 prints `frozen artefacts differing from the index: N` (V1 wording)
  trace   --out JSON -- M9_ARGS...               run tools/urban_boq_m9.py in a child interpreter and record every repository
                                                 module it imported and every repository file it opened
  coverage --spec SPEC --trace JSON ...          traced repository modules that the spec does not protect (exit 1 if any)

usage: python3 -I research/freeze_integrity/freeze_verify_v2.py SUBCOMMAND [options]

It lives here, not in tools/, because tests/zz_freeze_integrity requires that nothing under engine/, tools/, agents/
or pipeline/ names the verifier (production never imports it); it is stdlib only, like V1."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from tools import freeze_verify as V1                         # noqa: E402  (V1 is imported, never edited)

INDEX_SCHEMA_V2 = "URBAN_FREEZE_BASELINE_INDEX_V2"
SPEC_SCHEMA = "URBAN_RELEASED_PATH_SPEC_V1"
V1_INDEX = "research/freeze_integrity/FREEZE_BASELINE_INDEX.jsonl"
V1_KINDS = ("FREEZE_MANIFEST", "BASELINE")
WHOLE_FILE_KINDS = V1_KINDS + ("RELEASED_CODE", "RELEASED_DATA")
SYMBOL_KIND = "RELEASED_CODE_SYMBOLS"


def sha(b):
    return hashlib.sha256(b).hexdigest()


# ------------------------------------------------------------------ top-level statements of a hub module
def _bound_names(node):
    """the module-level names a top-level statement binds (def / class / assignment targets / imports / names stored
    anywhere inside an if / try / for / with block at module level)."""
    out = set()
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return {node.name}
    if isinstance(node, (ast.Import, ast.ImportFrom)):
        return {(a.asname or a.name).split(".")[0] for a in node.names if a.name != "*"}
    for n in ast.walk(node):
        if isinstance(n, ast.Name) and isinstance(n.ctx, (ast.Store, ast.Del)):
            out.add(n.id)
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n is not node:
            out.add(n.name)
        elif isinstance(n, (ast.Import, ast.ImportFrom)):
            out |= {(a.asname or a.name).split(".")[0] for a in n.names if a.name != "*"}
    return out


def _key(node):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return node.name
    if isinstance(node, ast.Assign) and all(isinstance(t, ast.Name) for t in node.targets):
        return ",".join(t.id for t in node.targets)
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        return node.target.id
    return None


def top_level(source):
    """[(key, sha256 of the statement's full source lines, names it binds)] in file order. A named statement's key is
    its name (a repeated name gets '#2', '#3' ...); an unnamed statement's key is 'stmt:' + the sha of its own text."""
    lines = source.splitlines(keepends=True)
    out, seen = [], {}
    for n in ast.parse(source).body:
        start = min([n.lineno] + [d.lineno for d in getattr(n, "decorator_list", [])])
        text = "".join(lines[start - 1:n.end_lineno])
        h = sha(text.encode("utf-8"))
        k = _key(n)
        if k is None:
            k = "stmt:" + h
        seen[k] = seen.get(k, 0) + 1
        if seen[k] > 1:
            k = f"{k}#{seen[k]}"
        out.append((k, h, _bound_names(n)))
    return out


def symbol_entry(repo, path, hubs):
    src = (Path(repo) / path).read_text(encoding="utf-8")
    stmts = top_level(src)
    names = {k for k, _, _ in stmts}
    missing = sorted(set(hubs) - names)
    if missing:
        raise ValueError(f"{path}: declared hub symbols not found: {missing}")
    return {"kind": SYMBOL_KIND, "path": path, "hubs_not_hashed": sorted(hubs),
            "symbols": {k: h for k, h, _ in stmts if k not in hubs},
            "file_sha256_at_index": sha((Path(repo) / path).read_bytes())}


def check_symbols(repo, entry):
    """[(label, recorded, now)] for every frozen statement of ENTRY that changed, vanished or is re-bound."""
    f = Path(repo) / entry["path"]
    if not f.is_file():
        return [(entry["path"], "file", None)]
    try:
        stmts = top_level(f.read_text(encoding="utf-8"))
    except SyntaxError as ex:
        return [(entry["path"], "parse", f"syntax error line {ex.lineno}")]
    frozen, hubs = entry["symbols"], set(entry["hubs_not_hashed"])
    now = {k: h for k, h, _ in stmts}
    bad = []
    for k, h in sorted(frozen.items()):
        if now.get(k) != h:
            bad.append((f"{entry['path']}::{k}", h, now.get(k)))
    frozen_names = {k.split("#")[0] for k in frozen if not k.startswith("stmt:")} | hubs
    for k, h, bound in stmts:
        if k in frozen or k in hubs:
            continue
        hit = sorted(bound & frozen_names)                      # a NEW statement may not re-bind a frozen name
        if hit:
            bad.append((f"{entry['path']}::{k} rebinds {','.join(hit)}", "absent", h))
    return bad


# ------------------------------------------------------------------ the released-path spec and the V2 entries
def load_spec(path):
    s = json.loads(Path(path).read_text(encoding="utf-8"))
    if s.get("schema") != SPEC_SCHEMA:
        raise ValueError(f"{path}: schema is not {SPEC_SCHEMA}")
    for k in ("released_method", "code", "data", "hubs"):
        if k not in s:
            raise ValueError(f"{path}: key {k!r} missing")
    dup = {p for p in s["code"] if s["code"].count(p) > 1} | (set(s["code"]) & set(s["data"])) | \
          (set(s["code"]) & {h["path"] for h in s["hubs"]})
    if dup:
        raise ValueError(f"{path}: a file is declared twice: {sorted(dup)}")
    return s


def v2_entries(repo, spec):
    repo = Path(repo)
    out = []
    for kind, paths in (("RELEASED_CODE", spec["code"]), ("RELEASED_DATA", spec["data"])):
        for p in sorted(paths):
            f = repo / p
            if not f.is_file():
                raise ValueError(f"declared released file missing: {p}")
            out.append({"kind": kind, "path": p, "sha256": sha(f.read_bytes()), "artefacts": {},
                        "released_method": spec["released_method"]})
    for h in spec["hubs"]:
        out.append(dict(symbol_entry(repo, h["path"], h["not_hashed"]), released_method=spec["released_method"]))
    return out


def _commit(repo):
    try:
        return V1.git(repo, "rev-parse", "--short", "HEAD", text=True).strip()
    except RuntimeError:
        return None


def write_index(repo, path, spec, v1=V1_INDEX):
    """append the spec's V2 entries to PATH (a new PATH starts as a byte copy of the V1 index). -> (kept, appended)."""
    repo, path = Path(repo), Path(path)
    v1b = (repo / v1).read_bytes()
    if not path.exists():
        path.write_bytes(v1b)
    elif not path.read_bytes().startswith(v1b):
        raise ValueError(f"{path} does not start with the V1 index bytes (nothing written)")
    old = {(e["kind"], e["path"]): e for e in V1.read_chain(path)}
    new = v2_entries(repo, spec)
    keys = ("sha256", "symbols", "hubs_not_hashed")
    bad = [e["path"] for e in new if (e["kind"], e["path"]) in old
           and any(old[(e["kind"], e["path"])].get(k) != e.get(k) for k in keys)]
    if bad:
        raise ValueError(f"released file changed since it was indexed (nothing written): {bad}")
    add = [dict(e, schema=INDEX_SCHEMA_V2, indexed_at_commit=_commit(repo)) for e in new if (e["kind"], e["path"]) not in old]
    V1.append_chain(path, add)
    return len(old), len(add)


def check_index(repo, path, v1=V1_INDEX):
    """[(label, recorded, now)] for every difference: the V1 head, whole files, and frozen hub statements."""
    repo = Path(repo)
    bad = []
    v1f = repo / v1
    if not v1f.is_file() or not Path(path).read_bytes().startswith(v1f.read_bytes()):
        bad.append((f"V1_PREFIX {v1}", "prefix of the V2 index", "differs" if v1f.is_file() else None))
    for e in V1.read_chain(path):
        if e["kind"] == SYMBOL_KIND:
            bad += check_symbols(repo, e)
            continue
        if e["kind"] not in WHOLE_FILE_KINDS:
            bad.append((f"{e['path']} (unknown kind {e['kind']})", e["kind"], None))
            continue
        for p, h in [(e["path"], e["sha256"])] + sorted(e.get("artefacts", {}).items()):
            f = repo / p
            now = sha(f.read_bytes()) if f.is_file() else None
            if now != h:
                bad.append((p, h, now))
    return bad


# ------------------------------------------------------------------ trace and coverage
_CHILD = r"""
import json, os, sys
from pathlib import Path
repo, out = Path(sys.argv[1]).resolve(), Path(sys.argv[2])
sys.path.insert(0, str(repo))
opened = set()
def hook(ev, args):
    if ev == "open" and args and isinstance(args[0], (str, bytes, os.PathLike)):
        try:
            p = Path(os.fsdecode(args[0])).resolve()
        except Exception:
            return
        if repo in p.parents:
            opened.add(str(p.relative_to(repo)))
sys.addaudithook(hook)
from tools import urban_boq_m9 as M
try:
    rc = M.main(sys.argv[3:])
except SystemExit as ex:
    rc = ex.code
mods = set()
for m in list(sys.modules.values()):
    f = getattr(m, "__file__", None)
    if f:
        p = Path(f).resolve()
        if repo in p.parents:
            mods.add(str(p.relative_to(repo)))
out.write_text(json.dumps({"exit": rc if isinstance(rc, int) or rc is None else 1, "modules": sorted(mods),
                           "opened": sorted(o for o in opened if "__pycache__" not in o and not o.endswith(".py"))},
                          indent=1), encoding="utf-8")
"""


def trace(repo, out, m9_args, python=sys.executable):
    out = Path(out).resolve()
    p = subprocess.run([python, "-I", "-c", _CHILD, str(Path(repo).resolve()), str(out), *m9_args], cwd=str(repo),
                       capture_output=True, text=True, env=V1._env())
    if p.returncode or not out.is_file():
        raise RuntimeError(f"trace run failed (exit {p.returncode}): {p.stderr[-1500:]}")
    return json.loads(out.read_text(encoding="utf-8"))


def uncovered(spec, traced):
    """traced repository modules (package __init__ files included) that the spec protects neither whole nor as a hub."""
    covered = set(spec["code"]) | {h["path"] for h in spec["hubs"]}
    return sorted(set(traced["modules"]) - covered)


# ------------------------------------------------------------------ CLI
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--repo", default=str(REPO))
    sp = ap.add_subparsers(dest="cmd", required=True)
    a = sp.add_parser("index")
    a.add_argument("--spec", required=True)
    a.add_argument("--v1", default=V1_INDEX)
    a.add_argument("--write")
    a = sp.add_parser("check")
    a.add_argument("--index", required=True)
    a.add_argument("--v1", default=V1_INDEX)
    a = sp.add_parser("trace")
    a.add_argument("--out", required=True)
    a.add_argument("m9_args", nargs=argparse.REMAINDER)
    a = sp.add_parser("coverage")
    a.add_argument("--spec", required=True)
    a.add_argument("--trace", required=True, action="append")
    o = ap.parse_args(argv)
    repo = Path(o.repo)
    if o.cmd == "index":
        spec = load_spec(o.spec)
        if o.write:
            print("entries kept / appended:", write_index(repo, o.write, spec, o.v1))
        else:
            print(json.dumps(v2_entries(repo, spec), indent=1))
    elif o.cmd == "check":
        bad = check_index(repo, o.index, o.v1)
        for p, h, now in bad:
            print("DIFFERS", p, str(h)[:12], (now or "missing")[:12])
        print("frozen artefacts differing from the index:", len(bad))
        return 1 if bad else 0
    elif o.cmd == "trace":
        args = o.m9_args[1:] if o.m9_args[:1] == ["--"] else o.m9_args
        t = trace(repo, o.out, args)
        print("exit", t["exit"], "repository modules", len(t["modules"]), "repository files opened", len(t["opened"]))
        return 0 if t["exit"] in (0, None) else 1
    elif o.cmd == "coverage":
        spec = load_spec(o.spec)
        miss = sorted({m for t in o.trace for m in uncovered(spec, json.loads(Path(t).read_text(encoding="utf-8")))})
        for m in miss:
            print("NOT PROTECTED", m)
        print("traced repository modules not protected by the spec:", len(miss))
        return 1 if miss else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
