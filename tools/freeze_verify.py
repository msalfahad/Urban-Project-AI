"""Freeze integrity verifier (P2-00 Stage 1). Stdlib only. It never writes into the repository: every rebuild runs in a
disposable git worktree, and every comparison is made against the committed bytes (git objects, which are immutable),
never against a file a rebuild could have rewritten.

Subcommands
  manifests  the freeze manifests at a git ref and what each pins (code / inputs / outputs)
  index      the baseline index of frozen artefacts: every manifest, every non-code research file it pins, and the
             extra baselines (the V1 snapshot, the owner rule files). --write FILE appends to a hash-chained JSONL file;
             entries already in the file must still match, or nothing is written
  check      the working tree against the committed index: exit 1 if any frozen artefact differs (immutable baseline)
  env        the interpreter and installed packages against ENVIRONMENT_LOCK.json; --write-lock FILE records the lock
  closure    per manifest: the static import closure of its pinned .py files, and the repository files in that closure
             that no pin covers (a change there could alter a frozen output while every source pin still passes)
  rebuild    rebuild every freeze in a disposable worktree of REF, one test at a time from a pristine tree, and
             compare every file a rebuild rewrote with its committed bytes: raw, and after masking the declared
             provenance fields (MASK_RULES). --patch FILE applies a diff in the worktree only. --repin also updates, in
             the worktree only, the code pins of the patched files (it simulates accepting the new source as provenance)

usage: python3 -I tools/freeze_verify.py SUBCOMMAND [options]      (see --help of each subcommand)"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CODE_KEYS = ("code", "code_sha256", "engine_code", "files_sha256")
PIN_KEYS = CODE_KEYS + ("inputs", "outputs")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
EXTRA_BASELINES = ("tests/m9_s6/data/V1_SYNTHETIC_VILLA_SNAPSHOT.json",)
EXTRA_BASELINE_GLOBS = ("rules/owner_decisions/*.json", "rules/owner_library/*.json", "rules/methods/*.json")
DEFAULT_SELECT = "rebuild or rerun or byte_identical"
DEFAULT_EXTRA_TESTS = ("tests/m9_s6", "tests/lintels_s8_6/test_opening_census.py")    # V1 / V2 behaviour, census units
LOCK_SCHEMA = "URBAN_ENVIRONMENT_LOCK_V1"
INDEX_SCHEMA = "URBAN_FREEZE_BASELINE_INDEX_V1"
MASK_RULES = {
    "M1_CODE_STAMP": "the hex digest after '+code:' (an engine stamp written into outputs)",
    "M2_CODE_MAP": "the sha values of a JSON code map (keys code / code_sha256 / engine_code / files_sha256)",
    "M3_UPSTREAM_MANIFEST_SHA": "the value of a 'manifest_sha256' key (an upstream manifest's own hash)",
    "M4_MANIFEST_OUTPUT_HASHES": "in a freeze manifest only: the sha values of its 'outputs' map (each output is "
                                 "compared on its own)",
    "M5_MD_SHA_SNIPPET": "in Markdown: a backticked hex digest written right after 'sha '",
}
_M1 = re.compile(r"(\+code:)[0-9a-f]{8,64}")
_M3T = re.compile(r'("manifest_sha256"\s*:\s*")[0-9a-f]{64}(")')
_M5 = re.compile(r"(sha `)[0-9a-f]{12,64}(`)")


# ------------------------------------------------------------------ git and hashing
def git(repo, *args, check=True, text=False):
    p = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, check=False)
    if check and p.returncode:
        raise RuntimeError(f"git {' '.join(args)}: {p.stderr.decode(errors='replace').strip()}")
    return p.stdout.decode() if text else p.stdout


def sha(b):
    return hashlib.sha256(b).hexdigest()


def tracked(repo, ref, *prefixes):
    return git(repo, "ls-tree", "-r", "--name-only", ref, "--", *prefixes, text=True).splitlines()


def blob(repo, ref, path):
    return git(repo, "show", f"{ref}:{path}")


# ------------------------------------------------------------------ manifests
def _is_pin_map(v):
    return isinstance(v, dict) and v and all(isinstance(h, str) and HEX64.match(h) for h in v.values())


def manifests(repo, ref="HEAD"):
    """[{path, sha256, pins: {group: {resolved path: sha}}, data}] for every tracked research JSON whose name
    contains 'freeze' and that pins files by sha256."""
    files = tracked(repo, ref, "research")
    known = set(files)
    out = []
    for f in files:
        name = f.rsplit("/", 1)[-1]
        if "freeze" not in name.lower() or not name.endswith(".json"):
            continue
        raw = blob(repo, ref, f)
        try:
            d = json.loads(raw)
        except ValueError:
            continue
        if not isinstance(d, dict) or not any(_is_pin_map(d.get(k)) for k in PIN_KEYS):
            continue
        pkg = f.rsplit("/", 1)[0]
        pins = {}
        for k in PIN_KEYS:
            if not _is_pin_map(d.get(k)):
                continue
            g = {}
            for rel, h in d[k].items():
                if k == "outputs":
                    p = f"{pkg}/{rel}"
                else:
                    p = rel if rel in known or not f"{pkg}/{rel}" in known else f"{pkg}/{rel}"
                g[p] = h
            pins[k] = g
        out.append({"path": f, "sha256": sha(raw), "pins": pins, "data": d})
    return out


def is_artefact(path):
    return path.startswith("research/") and not path.endswith(".py")


# ------------------------------------------------------------------ baseline index (append-only, hash-chained)
def index_entries(repo, ref="HEAD"):
    known = set(tracked(repo, ref))
    entries = []
    for m in manifests(repo, ref):
        arts = sorted({p for g in m["pins"].values() for p in g if is_artefact(p) and p in known} - {m["path"]})
        entries.append({"kind": "FREEZE_MANIFEST", "path": m["path"], "sha256": m["sha256"],
                        "artefacts": {p: sha(blob(repo, ref, p)) for p in arts},
                        "pinned_code": sorted(p for k in CODE_KEYS for p in m["pins"].get(k, {}) if p.endswith(".py"))})
    extra = list(EXTRA_BASELINES)
    for g in EXTRA_BASELINE_GLOBS:
        d, pat = g.rsplit("/", 1)
        rx = re.compile("^" + re.escape(d) + "/" + re.escape(pat).replace(r"\*", "[^/]*") + "$")
        extra += [p for p in sorted(known) if rx.match(p)]
    for p in extra:
        if p in known:
            entries.append({"kind": "BASELINE", "path": p, "sha256": sha(blob(repo, ref, p)), "artefacts": {}})
    return entries


def read_chain(path):
    """the entries of a hash-chained JSONL file; raises if any line was edited, removed or reordered."""
    lines = Path(path).read_bytes().splitlines(keepends=True)
    acc, out = b"", []
    for i, ln in enumerate(lines):
        e = json.loads(ln)
        if e.get("prev") != sha(acc) or e.get("seq") != i:
            raise ValueError(f"{path}: chain broken at line {i + 1} (an earlier line was changed, removed or reordered)")
        out.append(e)
        acc += ln
    return out


def append_chain(path, records):
    path = Path(path)
    acc = path.read_bytes() if path.exists() else b""
    n = len(read_chain(path)) if path.exists() else 0
    with path.open("ab") as fh:
        for i, r in enumerate(records):
            ln = (json.dumps(dict(r, seq=n + i, prev=sha(acc)), sort_keys=True, ensure_ascii=False) + "\n").encode()
            fh.write(ln)
            acc += ln


def append_only_history(repo, path):
    """every committed version of PATH, oldest first, must be a prefix of the next one and of the working file
    (a hash chain alone cannot see the last lines being removed). -> [violation, ...]"""
    revs = git(repo, "log", "--format=%H", "--follow", "--", path, text=True).split()[::-1]
    versions = []
    for r in revs:
        try:
            versions.append((r[:12], blob(repo, r, path)))
        except RuntimeError:
            versions.append((r[:12], b""))
    f = Path(repo) / path
    versions.append(("working tree", f.read_bytes() if f.is_file() else b""))
    return [f"{a} -> {b}: not an append" for (a, x), (b, y) in zip(versions, versions[1:]) if not y.startswith(x)]


def write_index(repo, path, ref="HEAD"):
    new = index_entries(repo, ref)
    old = {e["path"]: e for e in read_chain(path)} if Path(path).exists() else {}
    bad = [e["path"] for e in new if e["path"] in old and
           any(old[e["path"]].get(k) != e.get(k) for k in ("kind", "sha256", "artefacts"))]
    if bad:
        raise ValueError(f"baseline changed since it was indexed (nothing written): {bad}")
    add = [dict(e, schema=INDEX_SCHEMA, indexed_at_commit=git(repo, "rev-parse", "--short", ref, text=True).strip())
           for e in new if e["path"] not in old]
    append_chain(path, add)
    return len(old), len(add)


def check_index(repo, path):
    """[(path, recorded sha, working-tree sha or None)] for every indexed artefact that differs."""
    bad = []
    for e in read_chain(path):
        for p, h in [(e["path"], e["sha256"])] + sorted(e.get("artefacts", {}).items()):
            f = Path(repo) / p
            now = sha(f.read_bytes()) if f.is_file() else None
            if now != h:
                bad.append((p, h, now))
    return bad


# ------------------------------------------------------------------ environment lock
def _norm(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def current_env(python=sys.executable):
    info = json.loads(subprocess.run(
        [python, "-I", "-c", "import json, platform, sys; print(json.dumps({'version': platform.python_version(), "
                             "'implementation': platform.python_implementation(), 'executable': sys.executable}))"],
        capture_output=True, text=True, check=True).stdout)
    frz = subprocess.run([python, "-m", "pip", "freeze", "--all"], capture_output=True, text=True, check=True).stdout
    pk = {}
    for ln in frz.splitlines():
        if "==" in ln and not ln.startswith("#"):
            n, v = ln.split("==", 1)
            pk[_norm(n)] = v.strip()
        elif ln.strip():
            pk[_norm(ln.split(" ")[0])] = ln.strip()               # a non-pinned requirement line, recorded verbatim
    return {"python": {k: info[k] for k in ("version", "implementation")}, "packages": dict(sorted(pk.items()))}


def env_status(lock, env):
    want, have = lock["packages"], env["packages"]
    diff = {n: {"lock": want.get(n), "now": have.get(n)} for n in sorted(set(want) | set(have)) if want.get(n) != have.get(n)}
    py_ok = env["python"] == lock["python"]
    return {"in_lock": py_ok and not diff, "python_lock": lock["python"], "python_now": env["python"], "package_differences": diff}


# ------------------------------------------------------------------ static import closure
def _module_file(repo, mod):
    p = Path(repo, *mod.split("."))
    for c in (p.with_suffix(".py"), p / "__init__.py"):
        if c.is_file():
            return c
    return None


def _imports(repo, path, inits=True):
    try:
        tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return set()
    rel = Path(path).relative_to(repo).with_suffix("")
    pkg = list(rel.parts[:-1]) if rel.name != "__init__" else list(rel.parts[:-1])
    found = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names:
                found.add(a.name)
        elif isinstance(n, ast.ImportFrom):
            base = n.module or ""
            if n.level:
                up = pkg[: len(pkg) - (n.level - 1)] if n.level > 1 else pkg
                base = ".".join(up + ([n.module] if n.module else []))
            found.add(base)
            found.update(f"{base}.{a.name}" for a in n.names if base)
    out = set()
    for m in found:
        parts = m.split(".")
        for i in range(len(parts), 0, -1):               # the module itself, and (inits=True) each parent package
            f = _module_file(repo, ".".join(parts[:i]))
            if f is not None and (inits or i == len(parts)):
                out.add(f)
    return out


def closure(repo, seeds, inits=True):
    """the repository .py files reached from SEEDS by static imports. inits=False does not follow the parent-package
    __init__ files an import executes (their fan-out runs at import time but is not on the computation path)."""
    repo = Path(repo)
    todo, seen = [repo / s for s in seeds if (repo / s).is_file()], set()
    while todo:
        f = todo.pop()
        if f in seen:
            continue
        seen.add(f)
        todo.extend(_imports(repo, f, inits) - seen)
    return sorted(str(f.relative_to(repo)) for f in seen)


def closure_report(repo, ref="HEAD"):
    rows = []
    for m in manifests(repo, ref):
        pinned = sorted({p for k in CODE_KEYS for p in m["pins"].get(k, {}) if p.endswith(".py")})
        if not pinned:
            continue
        full = {p for p in closure(repo, pinned) if not p.endswith("__init__.py")}
        func = {p for p in closure(repo, pinned, inits=False) if not p.endswith("__init__.py")}
        rows.append({"manifest": m["path"], "pinned_py": len(pinned), "functional_closure_py": len(func),
                     "unpinned_functional": sorted(func - set(pinned)),
                     "unpinned_package_init_fanout": sorted(full - func - set(pinned))})
    return rows


# ------------------------------------------------------------------ behaviour comparison (declared masks only)
def _mask_text(s, md):
    fired = []
    t = _M1.sub(r"\1<CODE>", s)
    if t != s:
        fired.append("M1_CODE_STAMP")
    u = _M3T.sub(r"\1<SHA>\2", t)
    if u != t:
        fired.append("M3_UPSTREAM_MANIFEST_SHA")
    if md:
        v = _M5.sub(r"\1<SHA>\2", u)
        if v != u:
            fired.append("M5_MD_SHA_SNIPPET")
        u = v
    return u, fired


def _mask_json(o, manifest, fired):
    if isinstance(o, dict):
        out = {}
        for k, v in o.items():
            if k in CODE_KEYS and _is_pin_map(v):
                out[k] = {kk: "<SHA>" for kk in v}
                fired.add("M2_CODE_MAP")
            elif manifest and k == "outputs" and _is_pin_map(v):
                out[k] = {kk: "<SHA>" for kk in v}
                fired.add("M4_MANIFEST_OUTPUT_HASHES")
            elif k == "manifest_sha256" and isinstance(v, str) and HEX64.match(v):
                out[k] = "<SHA>"
                fired.add("M3_UPSTREAM_MANIFEST_SHA")
            else:
                out[k] = _mask_json(v, manifest, fired)
        return out
    if isinstance(o, list):
        return [_mask_json(v, manifest, fired) for v in o]
    if isinstance(o, str):
        t, f = _mask_text(o, False)
        fired.update(f)
        return t
    return o


def masked(path, data, manifest=False):
    """(masked form, rules fired). JSON / JSONL are compared as parsed values (formatting is not behaviour)."""
    fired = set()
    s = data.decode("utf-8", "replace")
    if path.endswith(".json"):
        try:
            return json.dumps(_mask_json(json.loads(s), manifest, fired), sort_keys=True), sorted(fired)
        except ValueError:
            pass
    if path.endswith(".jsonl"):
        try:
            rows = [json.dumps(_mask_json(json.loads(ln), manifest, fired), sort_keys=True) for ln in s.splitlines() if ln.strip()]
            return "\n".join(rows), sorted(fired)
        except ValueError:
            pass
    t, f = _mask_text(s, path.endswith(".md"))
    return t, sorted(f)


def compare(path, baseline, now, manifest=False):
    if baseline == now:
        return {"path": path, "raw": "EQUAL", "behaviour": "EQUAL", "masks": []}
    if baseline is None or now is None:
        return {"path": path, "raw": "NEW" if baseline is None else "DELETED", "behaviour": "DIFFERENT", "masks": []}
    a, fa = masked(path, baseline, manifest)
    b, fb = masked(path, now, manifest)
    return {"path": path, "raw": "DIFFERENT", "behaviour": "EQUAL" if a == b else "DIFFERENT",
            "masks": sorted(set(fa) | set(fb))}


# ------------------------------------------------------------------ rebuild in a disposable worktree
def _link_inputs(repo, wt):
    src = Path(repo) / "data" / "inputs"
    if not src.is_dir():
        return 0
    n = 0
    for f in sorted(src.rglob("*")):
        if f.is_file():
            t = wt / "data" / "inputs" / f.relative_to(src)
            t.parent.mkdir(parents=True, exist_ok=True)
            if not t.exists():
                t.symlink_to(f)
                n += 1
    return n


def _repin(repo, ref, wt, patched):
    """update, in the worktree only, every code pin of a patched file to the file's new sha."""
    done = []
    for m in manifests(repo, ref):
        p = wt / m["path"]
        text = p.read_text(encoding="utf-8")
        new = text
        for k in CODE_KEYS:
            for f, h in m["pins"].get(k, {}).items():
                if f in patched:
                    nh = sha((wt / f).read_bytes())
                    if new.count(h) != 1:
                        raise ValueError(f"cannot repin {f} in {m['path']}: its sha occurs {new.count(h)} times")
                    new = new.replace(h, nh)
                    done.append({"manifest": m["path"], "file": f, "from": h, "to": nh})
        if new != text:
            p.write_text(new, encoding="utf-8")
    return done


def _state(wt):
    st = git(wt, "status", "--porcelain", "--untracked-files=all", text=True).splitlines()
    return sorted(ln[3:] for ln in st)


def _reset(wt, prep):
    git(wt, "checkout", "--", ".")
    git(wt, "clean", "-fdq")
    if prep:
        git(wt, "apply", "--whitespace=nowarn", str(prep))


def _junit(path):
    out = []
    for tc in ET.parse(path).getroot().iter("testcase"):
        r = {"test": f'{tc.get("classname")}::{tc.get("name")}', "outcome": "passed", "message": ""}
        for tag in ("failure", "error", "skipped"):
            e = tc.find(tag)
            if e is not None:
                r["outcome"] = {"failure": "failed", "error": "error", "skipped": "skipped"}[tag]
                r["message"] = ((e.get("message") or "") + "\n" + (e.text or ""))[:4000]
        out.append(r)
    return out


def _classify(results, changes, builder_errors):
    """the verdict of one test. A failing builder is never 'identical', whatever it left behind."""
    msgs = "\n".join(r["message"] for r in results) + "\n" + "\n".join(builder_errors)
    if not results:
        return "NOT_RUN"
    if any(c["behaviour"] == "DIFFERENT" for c in changes):
        return "BEHAVIOUR_CHANGED"
    if all(r["outcome"] == "skipped" for r in results):
        return "SKIPPED"
    failed = [r for r in results if r["outcome"] in ("failed", "error")]
    if not failed and not changes:
        return "BYTE_IDENTICAL"
    if "ModuleNotFoundError" in msgs:
        return "ENV_MISSING_MODULE"
    if "frozen baseline altered: code" in msgs:
        return "REFUSED_BY_SOURCE_PIN"
    if builder_errors or "CalledProcessError" in msgs:
        return "BUILD_FAILED"
    if changes:                                              # every rewritten file is behaviour-equal (checked above)
        return "BEHAVIOUR_IDENTICAL_PROVENANCE_DIFFERS"
    return "TEST_FAILED_NO_OUTPUT_CHANGE"


def _env():
    return dict(os.environ, PYTHONDONTWRITEBYTECODE="1")


def _arch_baseline(wt, tmp, cfg, python):
    """re-run the architectural CLI on a drawing in the worktree and compare every output with recorded hashes.
    CFG = {"name", "drawing", "args": [...], "expected": {file: sha256}} (kept outside the repository: it may name a
    client drawing)."""
    out = tmp / ("arch_" + re.sub(r"[^A-Za-z0-9_]+", "_", cfg["name"]))
    shutil.rmtree(out, ignore_errors=True)
    p = subprocess.run([python, "-I", "tools/urban_boq_m9.py", "arch", "--drawings", cfg["drawing"], "--out", str(out),
                        *cfg.get("args", [])], cwd=wt, capture_output=True, text=True, env=_env())
    got = {f.name: sha(f.read_bytes()) for f in sorted(out.iterdir()) if f.is_file()} if out.is_dir() else {}
    exp = cfg["expected"]
    changes = [{"path": f, "raw": "EQUAL" if got.get(f) == h else ("DELETED" if f not in got else "DIFFERENT"),
                "behaviour": "EQUAL" if got.get(f) == h else "DIFFERENT", "masks": []} for f, h in sorted(exp.items())]
    changes += [{"path": f, "raw": "NEW", "behaviour": "DIFFERENT", "masks": []} for f in sorted(set(got) - set(exp))]
    changes = [c for c in changes if c["raw"] != "EQUAL"]
    res = [{"test": f"ARCH_BASELINE::{cfg['name']}", "outcome": "passed" if p.returncode == 0 else "failed",
            "message": (p.stderr or "")[-400:] if p.returncode else ""}]
    verdict = "BEHAVIOUR_CHANGED" if changes else ("BYTE_IDENTICAL" if p.returncode == 0 else "TEST_FAILED_NO_OUTPUT_CHANGE")
    return {"file": f"ARCH_BASELINE::{cfg['name']}", "tests": res, "changes": changes, "builder_errors": [],
            "verdict": verdict, "files_compared": len(exp)}


def rebuild(repo, ref, out, patches=(), repin=False, select=DEFAULT_SELECT, extra_tests=DEFAULT_EXTRA_TESTS,
            only=None, python=sys.executable, lock=None, keep=False, arch_baselines=()):
    repo, out = Path(repo).resolve(), Path(out).resolve()
    if out == repo or repo in out.parents:
        raise ValueError("the output folder must be outside the repository")
    out.mkdir(parents=True, exist_ok=True)
    # the ref is resolved once: every later read (manifests, committed blobs) uses this commit, even if the
    # repository's HEAD moves while the run is in progress
    ref = git(repo, "rev-parse", "--verify", f"{ref}^{{commit}}", text=True).strip()
    before = {"status": git(repo, "status", "--porcelain", "--untracked-files=no", text=True),
              "head": git(repo, "rev-parse", "HEAD", text=True).strip()}
    env = current_env(python)
    est = env_status(json.loads(Path(lock).read_text()), env) if lock else None
    tmp = Path(tempfile.mkdtemp(prefix="freeze_verify_"))
    wt = tmp / "wt"
    git(repo, "worktree", "add", "--detach", str(wt), ref)
    report = {"ref": ref, "python": python, "environment": env["python"], "environment_status": est,
              "patches": [], "repins": [], "groups": [], "mask_rules": MASK_RULES}
    try:
        report["inputs_linked"] = _link_inputs(repo, wt)
        for p in patches:
            git(wt, "apply", "--whitespace=nowarn", str(Path(p).resolve()))
            report["patches"].append({"file": str(p), "sha256": sha(Path(p).read_bytes())})
        patched = set(git(wt, "diff", "--name-only", text=True).split())
        report["patched_files"] = sorted(patched)
        if repin and patched:
            report["repins"] = _repin(repo, ref, wt, patched)
        prep = None
        if git(wt, "diff", "--name-only", text=True).strip():
            prep = tmp / "prepared.diff"
            prep.write_bytes(git(wt, "diff", "--binary"))
        prepared = {p: (wt / p).read_bytes() for p in git(wt, "diff", "--name-only", text=True).split()}
        mpaths = {m["path"] for m in manifests(repo, ref)}
        nodes, cerr = [], set()
        for args in (["-k", select, "tests"], list(extra_tests)):      # the extra files are taken whole (no -k filter)
            if not args:
                continue
            col = subprocess.run([python, "-m", "pytest", "--collect-only", "-q", "-o", "addopts=", "-p", "no:cacheprovider",
                                  *args], cwd=wt, capture_output=True, text=True, env=_env())
            nodes += [ln for ln in col.stdout.splitlines() if "::" in ln and not ln.startswith(("ERROR", "FAILED"))
                      and ln not in nodes]
            cerr |= {ln.split()[1] for ln in col.stdout.splitlines() if ln.startswith("ERROR ")}
        report["collection_errors"] = sorted(cerr)
        # every test runs alone from a pristine worktree: an earlier rebuild in the same session could otherwise rewrite
        # a manifest that a later test compares against (the F-1 effect, inside one test file)
        groups = {n: [n] for n in nodes if not n.startswith("tests/zz_freeze_integrity/") and (not only or re.search(only, n))}
        for f, ids in groups.items():
            if _state(wt) != sorted(prepared):
                _reset(wt, prep)
            xml = tmp / "junit.xml"
            if xml.exists():
                xml.unlink()
            bt = tmp / "basetemp"                       # its own pytest temp root: never prunes another session's dirs
            shutil.rmtree(bt, ignore_errors=True)
            subprocess.run([python, "-m", "pytest", "-p", "no:cacheprovider", "-q", "-o", "addopts=", f"--junitxml={xml}",
                            f"--basetemp={bt}", *ids], cwd=wt, capture_output=True, text=True, env=_env())
            results = _junit(xml) if xml.exists() else []
            changes = []
            for path in _state(wt):
                cur = (wt / path).read_bytes() if (wt / path).is_file() else None
                if path in prepared and cur == prepared[path]:
                    continue
                base = None
                try:
                    base = blob(repo, ref, path)
                except RuntimeError:
                    pass
                changes.append(compare(path, base, cur, manifest=path in mpaths))
            errs = []
            for r in results:
                m = re.search(r"Command '(\[.*?\])' returned non-zero", r["message"])
                if m:
                    cmd = ast.literal_eval(m.group(1))
                    _reset(wt, prep)
                    q = subprocess.run(cmd, cwd=wt, capture_output=True, text=True, env=_env())
                    tail = [ln for ln in (q.stderr or "").splitlines() if ln.strip()][-1:]
                    errs.append(tail[0][:400] if tail else f"exit {q.returncode}")
            g = {"file": f, "tests": results, "changes": changes, "builder_errors": errs,
                 "verdict": _classify(results, changes, errs)}
            report["groups"].append(g)
            print(f"{g['verdict']:40s} {f}", flush=True)
        for cfg in arch_baselines:
            _reset(wt, prep)
            g = _arch_baseline(wt, tmp, json.loads(Path(cfg).read_text(encoding="utf-8")), python)
            report["groups"].append(g)
            print(f"{g['verdict']:40s} {g['file']}", flush=True)
        _reset(wt, prep)
    finally:
        if not keep:
            git(repo, "worktree", "remove", "--force", str(wt), check=False)
            git(repo, "worktree", "prune", check=False)
            shutil.rmtree(tmp, ignore_errors=True)
    after = {"status": git(repo, "status", "--porcelain", "--untracked-files=no", text=True),
             "head": git(repo, "rev-parse", "HEAD", text=True).strip()}
    report["repository_unchanged"] = before == after
    report["repository_changes"] = {
        "head": None if before["head"] == after["head"] else [before["head"], after["head"]],
        "status": sorted(set(before["status"].splitlines()) ^ set(after["status"].splitlines()))}
    allowed = {"BYTE_IDENTICAL", "SKIPPED"} | ({"BEHAVIOUR_IDENTICAL_PROVENANCE_DIFFERS"} if patches else set())
    v = [g["verdict"] for g in report["groups"]]
    report["counts"] = {k: v.count(k) for k in sorted(set(v))}
    report["tests_selected"] = sum(1 for g in report["groups"] if not g["file"].startswith("ARCH_BASELINE::"))
    ok = (report["repository_unchanged"] and not report["collection_errors"] and set(v) <= allowed
          and (report["tests_selected"] > 0 or only is not None))          # a run that selected nothing is no evidence
    in_lock = bool(est and est["in_lock"])
    report["overall"] = ("PASS" if ok and in_lock else
                         "NOT_A_PASS_OUTSIDE_THE_LOCKED_ENVIRONMENT" if ok else "FAIL")
    (out / "FREEZE_VERIFY_REPORT.json").write_text(json.dumps(report, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    (out / "FREEZE_VERIFY_REPORT.md").write_text(render(report), encoding="utf-8")
    return report


def render(r):
    L = [f"# Freeze verification: {r['overall']}", "",
         f"- ref `{r['ref'][:12]}`; interpreter {r['environment']['implementation']} {r['environment']['version']}",
         f"- environment lock: {'MATCHES' if r['environment_status'] and r['environment_status']['in_lock'] else 'DOES NOT MATCH (no byte-identity claim is valid here)'}",
         f"- patches (worktree only): {[p['file'] for p in r['patches']] or 'none'}; repinned: {len(r['repins'])}",
         f"- repository unchanged by the run: {r['repository_unchanged']}",
         f"- tests run: {r.get('tests_selected')}; collection errors: {r['collection_errors'] or 'none'}", "",
         "| Verdict | Tests |", "|---|---|"]
    L += [f"| {k} | {n} |" for k, n in r["counts"].items()]
    L += ["", "| Test | Verdict | Rewritten files (raw / behaviour / masks) |", "|---|---|---|"]
    for g in r["groups"]:
        ch = "; ".join(f"{c['path'].rsplit('/', 1)[-1]} ({c['raw']}/{c['behaviour']}/{','.join(c['masks']) or '-'})"
                       for c in g["changes"]) or "-"
        L.append(f"| `{g['file']}` | {g['verdict']} | {ch} |")
    return "\n".join(L) + "\n"


# ------------------------------------------------------------------ CLI
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--repo", default=str(REPO))
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("manifests").add_argument("--ref", default="HEAD")
    a = sp.add_parser("index")
    a.add_argument("--ref", default="HEAD")
    a.add_argument("--write")
    sp.add_parser("check").add_argument("--index", required=True)
    a = sp.add_parser("env")
    a.add_argument("--lock")
    a.add_argument("--write-lock")
    a.add_argument("--python", default=sys.executable)
    sp.add_parser("closure").add_argument("--ref", default="HEAD")
    a = sp.add_parser("rebuild")
    a.add_argument("--ref", default="HEAD")
    a.add_argument("--out", required=True)
    a.add_argument("--patch", action="append", default=[])
    a.add_argument("--repin", action="store_true")
    a.add_argument("--select", default=DEFAULT_SELECT)
    a.add_argument("--extra-tests", nargs="*", default=list(DEFAULT_EXTRA_TESTS))
    a.add_argument("--only", help="a regex on test file paths")
    a.add_argument("--lock")
    a.add_argument("--python", default=sys.executable)
    a.add_argument("--keep", action="store_true")
    a.add_argument("--arch-baseline", action="append", default=[],
                   help="a JSON config {name, drawing, args, expected}; kept outside the repository")
    o = ap.parse_args(argv)
    repo = Path(o.repo)
    if o.cmd == "manifests":
        for m in manifests(repo, o.ref):
            print(m["path"], {k: len(v) for k, v in m["pins"].items()})
    elif o.cmd == "index":
        if o.write:
            print("entries kept / appended:", write_index(repo, o.write, o.ref))
        else:
            print(json.dumps(index_entries(repo, o.ref), indent=1))
    elif o.cmd == "check":
        bad = check_index(repo, o.index)
        for p, h, now in bad:
            print("DIFFERS", p, h[:12], (now or "missing")[:12])
        print("frozen artefacts differing from the index:", len(bad))
        return 1 if bad else 0
    elif o.cmd == "env":
        env = current_env(o.python)
        if o.write_lock:
            if Path(o.write_lock).exists():
                raise SystemExit(f"{o.write_lock} exists: a lock is never overwritten")
            Path(o.write_lock).write_text(json.dumps(dict(schema=LOCK_SCHEMA, **env), indent=1, sort_keys=True) + "\n",
                                          encoding="utf-8")
            print("lock written:", o.write_lock)
        st = env_status(json.loads(Path(o.lock or o.write_lock).read_text()), env) if (o.lock or o.write_lock) else None
        print(json.dumps(st or env, indent=1))
        return 0 if (st is None or st["in_lock"]) else 1
    elif o.cmd == "closure":
        print(json.dumps(closure_report(repo, o.ref), indent=1))
    elif o.cmd == "rebuild":
        r = rebuild(repo, o.ref, o.out, o.patch, o.repin, o.select, o.extra_tests, o.only, o.python, o.lock, o.keep,
                    o.arch_baseline)
        print(r["overall"], r["counts"], "repository unchanged:", r["repository_unchanged"])
        return 0 if r["overall"] == "PASS" else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
