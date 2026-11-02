"""Git history facts for shallow clones (T-463; owner directive 2026-11-02 D2).

Tests that prove a freeze or a merged package look up OLD commits (``merge-base --is-ancestor``, ``show C:path``,
``ls-tree C``, ``diff C -- dir``). In a shallow clone (``git clone --depth 50``) those commits are absent and the tests
failed although nothing was wrong. This module answers the same questions:

1. with the real git history whenever the objects are present (a full clone behaves exactly as before: no fallback is
   ever taken when the repository is not shallow);
2. only in a SHALLOW repository and only for an object that is missing: from the in-repo fact file
   ``research/agents_t463/GIT_FACTS.json``, written from a full clone by ``python3 -I tools/git_history.py write`` and
   re-proved against the real history by ``check`` (tests/t463_git_history, full clone).

What the fact file holds (nothing is a copy of a file's content; file bytes are always read from git objects):
- ``ancestors``: every commit reachable from the recorded head (``git rev-list``); a commit is an ancestor of HEAD
  when it is listed AND the recorded head is itself an ancestor of HEAD (or lies beyond the shallow boundary);
- ``trees``: per requested ``commit:dir``, the blob id of every file under it at that commit. ``show C:path`` then
  reads the blob by its id (present in a shallow clone whenever the file is unchanged since, which is what a freeze
  asserts); ``ls-tree`` and ``diff C -- dir`` compare the recorded blob ids with the files of the working tree.

A question the facts cannot answer raises ``HistoryUnavailable`` (never a silent True / empty diff).
"""

from __future__ import annotations

import base64
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FACTS_REL = "research/agents_t463/GIT_FACTS.json"
SCHEMA = "URBAN_GIT_FACTS_V1"
DEFAULT_GUARD_CLASS = "TOOLING"        # T-212: test / history tooling; it produces no quantity, so no guard to run


class HistoryUnavailable(RuntimeError):
    """The git objects are absent (shallow clone) and the recorded facts do not answer the question."""


def _run(root, *args, data=None):
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, input=data)


def _out(root, *args):
    p = _run(root, *args)
    if p.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {p.stderr.decode(errors='replace').strip()}")
    return p.stdout.decode("utf-8")


def is_shallow(root=ROOT) -> bool:
    p = _run(root, "rev-parse", "--is-shallow-repository")
    return p.returncode == 0 and p.stdout.strip() == b"true"


def has_commit(commit, root=ROOT) -> bool:
    return _run(root, "cat-file", "-e", f"{commit}^{{commit}}").returncode == 0


def _resolve(commit, root=ROOT):
    """Full sha of a present commit (any ref / prefix), else None."""
    p = _run(root, "rev-parse", "--verify", "-q", f"{commit}^{{commit}}")
    return p.stdout.decode().strip() if p.returncode == 0 else None


_FACTS = {}


def load_facts(root=ROOT, path=None) -> dict:
    f = Path(path) if path else Path(root) / FACTS_REL
    key = str(f)
    if key not in _FACTS:
        if not f.exists():
            raise HistoryUnavailable(f"shallow clone and no git fact file {FACTS_REL}")
        doc = json.loads(f.read_text(encoding="utf-8"))
        if doc.get("schema") != SCHEMA:
            raise HistoryUnavailable(f"{FACTS_REL}: schema {doc.get('schema')!r} is not {SCHEMA}")
        _FACTS[key] = doc
    return _FACTS[key]


def _recorded_full(commit, facts):
    """Full sha of a recorded commit from a full sha or a unique prefix (>= 7 hex), else None."""
    c = str(commit).strip().lower()
    if len(c) < 7 or any(ch not in "0123456789abcdef" for ch in c):
        return None
    hits = [a for a in facts["ancestors"] if a.startswith(c)]
    return hits[0] if len(hits) == 1 else None


def _fallback_allowed(root):
    if not is_shallow(root):
        return False
    return True


def rev_parse(commit, root=ROOT, facts_path=None) -> str:
    """Full sha of `commit` (git rev-parse); in a shallow clone a missing old commit is resolved from the facts."""
    full = _resolve(commit, root)
    if full:
        return full
    if _fallback_allowed(root):
        full = _recorded_full(commit, load_facts(root, facts_path))
        if full:
            return full
        raise HistoryUnavailable(f"{commit}: not in this shallow clone and not a recorded commit")
    raise RuntimeError(f"git rev-parse {commit}: unknown revision")


def is_ancestor(commit, head="HEAD", root=ROOT, facts_path=None) -> bool:
    """git merge-base --is-ancestor commit head; in a shallow clone a commit beyond the boundary is answered by the
    recorded ancestry (the recorded head must itself be an ancestor of head, or beyond the boundary)."""
    p = _run(root, "merge-base", "--is-ancestor", str(commit), str(head))
    if p.returncode == 0:
        return True
    if p.returncode == 1 and has_commit(commit, root):
        return False                                   # both present: git is authoritative
    if not _fallback_allowed(root):
        return False                                   # full clone: unknown commit = not an ancestor (as before)
    facts = load_facts(root, facts_path)
    full = _recorded_full(commit, facts)
    if not full:
        return False                                   # never recorded: not proved, refused as before
    rec = facts["recorded_head"]
    if has_commit(rec, root):
        if _run(root, "merge-base", "--is-ancestor", rec, str(head)).returncode != 0:
            return False                               # head does not descend from the recorded history
    return True


def _tree_facts(commit, path, root, facts_path):
    facts = load_facts(root, facts_path)
    full = _recorded_full(commit, facts) or commit
    key = f"{full}:{str(path).strip('/')}"
    if key in facts["trees"]:
        return facts["trees"][key], ""
    # a file inside a recorded directory
    for k, files in facts["trees"].items():
        c, d = k.split(":", 1)
        if c == full and str(path).startswith(d.rstrip("/") + "/") and str(path) in files:
            return {str(path): files[str(path)]}, str(path)
    raise HistoryUnavailable(f"{commit}:{path}: not in this shallow clone and not recorded in {FACTS_REL}")


def show_bytes(commit, path, root=ROOT, facts_path=None) -> bytes:
    """The bytes of `path` at `commit` (git show C:path); in a shallow clone read by the recorded blob id."""
    p = _run(root, "show", f"{commit}:{path}")
    if p.returncode == 0:
        return p.stdout
    if not _fallback_allowed(root):
        raise RuntimeError(f"git show {commit}:{path}: {p.stderr.decode(errors='replace').strip()}")
    files, _ = _tree_facts(commit, path, root, facts_path)
    blob = files.get(str(path))
    if not blob:
        raise HistoryUnavailable(f"{commit}:{path}: recorded directory has no such file")
    q = _run(root, "cat-file", "blob", blob)
    if q.returncode == 0:
        return q.stdout
    stored = load_facts(root, facts_path).get("blobs", {}).get(blob)
    if stored is not None:
        data = _stored_bytes(stored)
        if blob_id(data) == blob:
            return data
    raise HistoryUnavailable(f"{commit}:{path}: blob {blob} is not in this shallow clone nor stored")


def sha256_at(commit, path, root=ROOT, facts_path=None) -> str:
    """sha256 of `path` at `commit`: from the git bytes when they are readable (full clone, or the blob is still in the
    shallow clone); otherwise, in a shallow clone, the recorded sha256 (proved against git by `check`)."""
    try:
        return hashlib.sha256(show_bytes(commit, path, root, facts_path)).hexdigest()
    except HistoryUnavailable:
        facts = load_facts(root, facts_path)
        full = _recorded_full(commit, facts) or commit
        h = facts.get("sha256", {}).get(f"{full}:{path}")
        if not h:
            raise
        return h


def ls_tree_names(commit, prefix, root=ROOT, facts_path=None) -> list:
    """git ls-tree -r --name-only commit prefix (sorted file paths)."""
    p = _run(root, "ls-tree", "-r", "--name-only", str(commit), str(prefix))
    if p.returncode == 0:
        return p.stdout.decode("utf-8").split()
    if not _fallback_allowed(root):
        raise RuntimeError(f"git ls-tree {commit} {prefix}: {p.stderr.decode(errors='replace').strip()}")
    files, _ = _tree_facts(commit, str(prefix).rstrip("/"), root, facts_path)
    return sorted(files)


def _worktree_blob(root, rel):
    f = Path(root) / rel
    if not f.is_file():
        return None
    return _out(root, "hash-object", "--", rel).strip()


def changed_since(commit, path, root=ROOT, diff_filter=None, facts_path=None) -> list:
    """Paths under `path` that differ between `commit` and the working tree (git diff --name-only [--diff-filter]
    commit -- path). Empty = unchanged. Shallow fallback: recorded blob ids vs the working-tree files; additions are
    reported unless the filter excludes 'A'."""
    args = ["diff", "--name-only", "--no-renames"] + ([f"--diff-filter={diff_filter}"] if diff_filter else [])
    p = _run(root, *args, str(commit), "--", str(path))
    if p.returncode == 0:
        return p.stdout.decode("utf-8").split()
    if not _fallback_allowed(root):
        raise RuntimeError(f"git diff {commit} -- {path}: {p.stderr.decode(errors='replace').strip()}")
    files, _ = _tree_facts(commit, str(path).rstrip("/"), root, facts_path)
    flt = set(diff_filter) if diff_filter else set("ACDMRTUXB")
    out = []
    for rel, blob in sorted(files.items()):
        now = _worktree_blob(root, rel)
        if now is None and "D" in flt:
            out.append(rel)
        elif now is not None and now != blob and "M" in flt:
            out.append(rel)
    if "A" in flt:
        cur = set(_out(root, "ls-files", "-co", "--exclude-standard", "--", str(path)).split())
        out += sorted(cur - set(files))
    return sorted(set(out))


def name_status_since(commit, paths, root=ROOT, facts_path=None) -> list:
    """[(A|M|D, path)] between `commit` and the working tree under `paths` (git diff --name-status --no-renames commit
    -- paths, tracked files). Shallow fallback: recorded blob ids vs the working tree (tracked files only)."""
    p = _run(root, "diff", "--name-status", "--no-renames", str(commit), "--", *map(str, paths))
    if p.returncode == 0:
        return [tuple(r.split("\t", 1)) for r in p.stdout.decode("utf-8").splitlines() if r]
    if not _fallback_allowed(root):
        raise RuntimeError(f"git diff {commit}: {p.stderr.decode(errors='replace').strip()}")
    old = {}
    for d in paths:
        files, _ = _tree_facts(commit, str(d).rstrip("/"), root, facts_path)
        old.update(files)
    tracked = set(_out(root, "ls-files", "--", *map(str, paths)).split())
    out = []
    for rel in sorted(set(old) | tracked):
        now = _worktree_blob(root, rel) if rel in tracked else None
        if rel not in old:
            out.append(("A", rel))
        elif now is None:
            out.append(("D", rel))
        elif now != old[rel]:
            out.append(("M", rel))
    return out


def git_text(root, *args) -> str:
    """stdout of `git -C root args` (text). On failure: CalledProcessError, except in a shallow clone, where a
    recorded output of exactly these arguments (immutable history only, proved by `check`) is returned, and
    `diff --name-status --no-renames C -- paths` (C vs the working tree) is answered from the recorded trees."""
    p = _run(root, *args)
    if p.returncode == 0:
        return p.stdout.decode("utf-8")
    if not _fallback_allowed(root):
        raise subprocess.CalledProcessError(p.returncode, ["git", "-C", str(root), *args], p.stdout, p.stderr)
    outs = load_facts(root).get("outputs", {})
    if _key(args) in outs:
        return outs[_key(args)]
    a = list(args)
    if a[:3] == ["diff", "--name-status", "--no-renames"] and len(a) > 5 and a[4] == "--":
        return "".join(f"{st}\t{rel}\n" for st, rel in name_status_since(a[3], a[5:], root))
    raise HistoryUnavailable(f"git {' '.join(map(str, args))}: not in this shallow clone and not recorded")


def _boundary(root) -> set:
    p = _run(root, "rev-parse", "--git-path", "shallow")
    f = Path(p.stdout.decode().strip()) if p.returncode == 0 else None
    if f is not None and not f.is_absolute():
        f = Path(root) / f
    return set(f.read_text().split()) if f is not None and f.is_file() else set()


def last_commit(path, root=ROOT, facts_path=None) -> str:
    """Full sha of the last commit touching `path` (git log -1 -- path), '' when none. A shallow clone answers a
    grafted BOUNDARY commit for every file older than its depth (a wrong answer, not a failure); then the recorded
    last commit is used, valid only while the recorded head is inside this clone (so no newer touch can be hidden)."""
    out = _out(root, "log", "-1", "--format=%H", "--", str(path)).strip()
    if not out or not is_shallow(root) or out not in _boundary(root):
        return out
    facts = load_facts(root, facts_path)
    rec = facts.get("last_touch", {}).get(str(path))
    if not rec:
        raise HistoryUnavailable(f"{path}: last commit is beyond this shallow clone and not recorded")
    if not has_commit(facts["recorded_head"], root):
        raise HistoryUnavailable(f"{path}: recorded head {facts['recorded_head'][:8]} is beyond this shallow clone; "
                                 f"a newer touch could be hidden (rewrite the facts in a full clone)")
    return rec


def git_bytes(root, *args) -> bytes:
    """stdout of `git -C root args` (bytes). On failure: CalledProcessError, except in a shallow clone, where
    `cat-file blob <id>` is answered from the stored blobs (each verified against its own id) and an exactly recorded
    command from the recorded outputs; a blob that is neither present nor stored still raises CalledProcessError."""
    p = _run(root, *args)
    if p.returncode == 0:
        return p.stdout
    err = subprocess.CalledProcessError(p.returncode, ["git", "-C", str(root), *args], p.stdout, p.stderr)
    if not _fallback_allowed(root):
        raise err
    facts = load_facts(root)
    a = list(args)
    if a[:2] == ["cat-file", "blob"] and len(a) == 3:
        data = facts.get("blobs", {}).get(a[2])
        if data is None:
            raise err
        data = _stored_bytes(data)
        if blob_id(data) != a[2]:
            raise HistoryUnavailable(f"stored blob {a[2]} does not hash to its id")
        return data
    if _key(args) in facts.get("outputs", {}):
        return facts["outputs"][_key(args)].encode("utf-8")
    raise err


# ------------------------------------------------------------------ write / check (full clone only)
def build(requests, root=ROOT, head="HEAD") -> dict:
    """The fact document for `requests` = {"trees": ["<commit>:<dir>", ...]} from the real history at `head`."""
    if is_shallow(root):
        raise RuntimeError("write the git facts from a full clone, not a shallow one")
    rec = _out(root, "rev-parse", head).strip()
    trees = {}
    for item in requests.get("trees", []):
        c, d = item.split(":", 1)
        full = _out(root, "rev-parse", f"{c}^{{commit}}").strip()
        rows = _out(root, "ls-tree", "-r", full, "--", d.rstrip("/")).splitlines()
        trees[f"{full}:{d.strip('/')}"] = {ln.split("\t", 1)[1]: ln.split()[2] for ln in rows if " blob " in ln}
        if not trees[f"{full}:{d.strip('/')}"]:
            raise RuntimeError(f"{item}: no file at that commit")
    sha = {f"{k.split(':', 1)[0]}:{path}": hashlib.sha256(_run(root, "cat-file", "blob", blob).stdout).hexdigest()
           for k, files in trees.items() for path, blob in files.items()}
    return {"schema": SCHEMA, "task": "T-463", "recorded_head": rec, "sha256": dict(sorted(sha.items())),
            "how": "python3 -I tools/git_history.py write (full clone); check proves every fact against git",
            "requests": requests,
            "ancestors": sorted(_out(root, "rev-list", rec).split()),
            "trees": dict(sorted(trees.items())),
            "outputs": {_key(a): _out(root, *a) for a in requests.get("outputs", [])},
            "last_touch": {f: _out(root, "log", "-1", "--format=%H", rec, "--", f).strip()
                           for f in sorted(set(requests.get("last_touch", [])))},
            "blobs": {b: _store(_blob_from_git(root, b))
                      for b in sorted(set(requests.get("blobs", [])))}}


def _blob_from_git(root, blob):
    p = _run(root, "cat-file", "blob", blob)
    if p.returncode != 0:
        raise RuntimeError(f"git cat-file blob {blob}: not in this repository")
    return p.stdout


def _store(data: bytes):
    """A stored blob: its UTF-8 text when it is text (readable and visible to the hygiene scans), else base64."""
    try:
        return {"text": data.decode("utf-8")}
    except UnicodeDecodeError:
        return {"base64": base64.b64encode(data).decode("ascii")}


def _stored_bytes(stored) -> bytes:
    if isinstance(stored, dict) and "text" in stored:
        return stored["text"].encode("utf-8")
    if isinstance(stored, dict) and "base64" in stored:
        return base64.b64decode(stored["base64"])
    raise HistoryUnavailable("stored blob has neither 'text' nor 'base64'")


def blob_id(data: bytes) -> str:
    """The git blob id of `data` (sha1 of 'blob <len>\\0' + data): a stored blob proves its own content."""
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def _key(args):
    return json.dumps(list(args), separators=(",", ":"))


def check(doc, root=ROOT) -> list:
    """Problems (empty = every fact holds against the real history at root). Full clone only."""
    if is_shallow(root):
        raise RuntimeError("check the git facts in a full clone")
    bad = []
    if doc.get("schema") != SCHEMA:
        bad.append(f"schema {doc.get('schema')!r}")
    rec = doc.get("recorded_head", "")
    if not has_commit(rec, root):
        return bad + [f"recorded head {rec} is not in this repository"]
    if _run(root, "merge-base", "--is-ancestor", rec, "HEAD").returncode != 0:
        bad.append(f"recorded head {rec} is not an ancestor of HEAD")
    real = set(_out(root, "rev-list", rec).split())
    got = set(doc.get("ancestors", []))
    if got != real:
        bad.append(f"ancestors differ from git rev-list {rec[:8]}: {len(got - real)} extra, {len(real - got)} missing")
    want = set()
    for item in doc.get("requests", {}).get("trees", []):
        c, d = item.split(":", 1)
        want.add(f"{_out(root, 'rev-parse', c + '^{commit}').strip()}:{d.strip('/')}")
    if set(doc.get("trees", {})) != want:
        bad.append("trees keys differ from the requests")
    for key, files in doc.get("trees", {}).items():
        c, d = key.split(":", 1)
        rows = _out(root, "ls-tree", "-r", c, "--", d).splitlines()
        real_files = {ln.split("\t", 1)[1]: ln.split()[2] for ln in rows if " blob " in ln}
        if real_files != files:
            bad.append(f"{c[:8]}:{d}: recorded blob ids differ from git")
        for path in real_files:
            real_sha = hashlib.sha256(_run(root, "show", f"{c}:{path}").stdout).hexdigest()
            if doc.get("sha256", {}).get(f"{c}:{path}") != real_sha:
                bad.append(f"{c[:8]}:{path}: recorded sha256 differs from git")
    outs = doc.get("outputs", {})
    if set(outs) != {_key(a) for a in doc.get("requests", {}).get("outputs", [])}:
        bad.append("outputs keys differ from the requests")
    for k, text in outs.items():
        if _out(root, *json.loads(k)) != text:
            bad.append(f"git {' '.join(json.loads(k))[:80]}: recorded output differs from git")
    lt = doc.get("last_touch", {})
    if set(lt) != set(doc.get("requests", {}).get("last_touch", [])):
        bad.append("last_touch keys differ from the requests")
    for f, c in lt.items():
        if _out(root, "log", "-1", "--format=%H", rec, "--", f).strip() != c or not c:
            bad.append(f"{f}: recorded last commit differs from git log at the recorded head")
    blobs = doc.get("blobs", {})
    if set(blobs) != set(doc.get("requests", {}).get("blobs", [])):
        bad.append("blobs keys differ from the requests")
    for b, data in blobs.items():
        if blob_id(_stored_bytes(data)) != b:
            bad.append(f"blob {b}: stored bytes do not hash to their id")
    nsha = sum(len(v) for v in doc.get("trees", {}).values())
    if len(doc.get("sha256", {})) != nsha:
        bad.append(f"sha256 entries {len(doc.get('sha256', {}))} != recorded files {nsha}")
    return bad


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    f = ROOT / FACTS_REL
    if argv[:1] == ["write"]:
        req = json.loads(f.read_text(encoding="utf-8"))["requests"] if f.exists() else {"trees": []}
        if len(argv) > 1:
            req = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps(build(req), indent=1, sort_keys=True) + "\n", encoding="utf-8")
        print(f"wrote {FACTS_REL}")
        return 0
    if argv[:1] == ["check"]:
        bad = check(json.loads(f.read_text(encoding="utf-8")))
        print("\n".join(bad) if bad else "git facts hold: 0 problems")
        return 1 if bad else 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
