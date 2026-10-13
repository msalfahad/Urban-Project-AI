"""P2-00 Stage 1 - the freeze verifier on a small synthetic repository (no project data).

The synthetic repository has two frozen packages built the way the historical ones are:
  pkg   its builder writes out.csv (a quantity), README.md (a '+code:' engine stamp) and its own freeze manifest;
        its rebuild test runs the builder IN PLACE and compares the outputs with the manifest (the F-1 pattern)
  pkg2  its builder first verifies pkg's manifest, code pins included (the downstream pattern), then writes out2.csv

What must hold:
  - a clean rebuild is BYTE_IDENTICAL, and the repository is unchanged by the verifier;
  - a comment-only engine change is BEHAVIOUR_IDENTICAL_PROVENANCE_DIFFERS for pkg (only the stamp differs) and
    REFUSED_BY_SOURCE_PIN for pkg2, unless the pins are re-pinned in the worktree (then BYTE_IDENTICAL);
  - a behaviour change is BEHAVIOUR_CHANGED and the run FAILS;
  - the F-1 self-heal happens with the historical in-place test pattern, and the baseline index catches it."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools import freeze_verify as FV              # noqa: E402

pytestmark = pytest.mark.skipif(subprocess.run(["git", "--version"], capture_output=True).returncode != 0,
                                reason="git is required")

ENGINE = "def area(a, b):\n    return a * b\n"
BUILD = textwrap.dedent('''
    import hashlib, json, sys
    from pathlib import Path
    ROOT = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(ROOT))
    from engine import calc
    PKG = Path(__file__).resolve().parent
    CODE = ["engine/calc.py", "research/pkg/build.py"]
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    stamp = "base000+code:" + hashlib.sha256("".join(sha(ROOT / c) for c in CODE).encode()).hexdigest()[:16]
    (PKG / "out.csv").write_text("item,qty\\nslab," + repr(calc.area(2.0, 3.0)) + "\\n")
    (PKG / "README.md").write_text("# pkg\\n\\nengine stamp `" + stamp + "`\\n")
    m = {"round": "PKG", "state": "FROZEN_BEFORE_COMPARISON", "engine_commit_stamp": stamp,
         "code": {c: sha(ROOT / c) for c in CODE},
         "outputs": {o: sha(PKG / o) for o in ("out.csv", "README.md")}}
    (PKG / "01_PKG_FREEZE_MANIFEST.json").write_text(json.dumps(m, indent=1, sort_keys=True) + "\\n")
''')
BUILD2 = textwrap.dedent('''
    import hashlib, json, sys
    from pathlib import Path
    ROOT = Path(__file__).resolve().parents[2]
    PKG = Path(__file__).resolve().parent
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    up = json.loads((ROOT / "research/pkg/01_PKG_FREEZE_MANIFEST.json").read_text())
    for rel, h in up["code"].items():
        if sha(ROOT / rel) != h:
            raise SystemExit("frozen baseline altered: code " + rel)
    rows = (ROOT / "research/pkg/out.csv").read_text().splitlines()[1:]
    (PKG / "out2.csv").write_text("item,qty_x2\\n" + "".join(r.split(",")[0] + "," +
                                  repr(2 * float(r.split(",")[1])) + "\\n" for r in rows))
    m = {"round": "PKG2", "state": "FROZEN_BEFORE_COMPARISON", "code": {"research/pkg2/build.py": sha(PKG / "build.py")},
         "inputs": {"research/pkg/out.csv": sha(ROOT / "research/pkg/out.csv")}, "outputs": {"out2.csv": sha(PKG / "out2.csv")}}
    (PKG / "01_PKG2_FREEZE_MANIFEST.json").write_text(json.dumps(m, indent=1, sort_keys=True) + "\\n")
''')
REBUILD_TEST = textwrap.dedent('''
    import hashlib, json, subprocess, sys
    from pathlib import Path
    ROOT = Path(__file__).resolve().parents[2]

    def _check(pkg, manifest):
        m = json.loads((ROOT / "research" / pkg / manifest).read_text())
        subprocess.run([sys.executable, str(ROOT / "research" / pkg / "build.py")], check=True, capture_output=True)
        for o, h in m["outputs"].items():
            assert hashlib.sha256((ROOT / "research" / pkg / o).read_bytes()).hexdigest() == h, o

    def test_pkg_rebuild_is_byte_identical():
        _check("pkg", "01_PKG_FREEZE_MANIFEST.json")

    def test_pkg2_rebuild_is_byte_identical():
        _check("pkg2", "01_PKG2_FREEZE_MANIFEST.json")
''')


def _git(repo, *a):
    return subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", *a], check=True,
                          capture_output=True, text=True).stdout


@pytest.fixture
def repo(tmp_path):
    r = tmp_path / "repo"
    for rel, text in {"engine/__init__.py": "", "engine/calc.py": ENGINE, "research/pkg/build.py": BUILD,
                      "research/pkg2/build.py": BUILD2, "tests/__init__.py": "", "tests/pkg/__init__.py": "",
                      "tests/pkg/test_pkg_rebuild.py": REBUILD_TEST, ".gitignore": "__pycache__/\n",
                      "pytest.ini": "[pytest]\naddopts = -q\n"}.items():          # as in the real repository
        (r / rel).parent.mkdir(parents=True, exist_ok=True)
        (r / rel).write_text(text)
    subprocess.run([sys.executable, str(r / "research/pkg/build.py")], check=True)
    subprocess.run([sys.executable, str(r / "research/pkg2/build.py")], check=True)
    _git(r, "init", "-q")
    _git(r, "add", "-A")
    _git(r, "commit", "-qm", "freeze")
    return r


@pytest.fixture(scope="module")
def lock(tmp_path_factory):
    p = tmp_path_factory.mktemp("lock") / "LOCK.json"
    p.write_text(json.dumps(dict(schema=FV.LOCK_SCHEMA, **FV.current_env())))
    return p


def _patch(tmp_path, repo, new_engine, name):
    (repo / "engine/calc.py").write_text(new_engine)
    d = subprocess.run(["git", "-C", str(repo), "diff"], capture_output=True, text=True, check=True).stdout
    _git(repo, "checkout", "--", "engine/calc.py")
    p = tmp_path / name
    p.write_text(d)
    return p


def _run(repo, out, lock, **kw):
    return FV.rebuild(repo, "HEAD", out, select="rebuild", extra_tests=(), lock=lock, **kw)


def test_manifest_discovery_and_index(repo):
    ms = {m["path"]: m for m in FV.manifests(repo)}
    assert set(ms) == {"research/pkg/01_PKG_FREEZE_MANIFEST.json", "research/pkg2/01_PKG2_FREEZE_MANIFEST.json"}
    e = {x["path"]: x for x in FV.index_entries(repo)}
    assert set(e["research/pkg/01_PKG_FREEZE_MANIFEST.json"]["artefacts"]) == {"research/pkg/out.csv", "research/pkg/README.md"}
    assert e["research/pkg/01_PKG_FREEZE_MANIFEST.json"]["pinned_code"] == ["engine/calc.py", "research/pkg/build.py"]


def test_clean_rebuild_is_byte_identical_and_leaves_the_repository_alone(repo, tmp_path, lock):
    before = (_git(repo, "status", "--porcelain"), _git(repo, "rev-parse", "HEAD"))
    r = _run(repo, tmp_path / "out", lock)
    assert r["overall"] == "PASS" and r["repository_unchanged"]
    assert set(r["counts"]) == {"BYTE_IDENTICAL"} and r["tests_selected"] == 2
    assert (_git(repo, "status", "--porcelain"), _git(repo, "rev-parse", "HEAD")) == before
    assert not _git(repo, "worktree", "list").strip().count("\n")            # the disposable worktree is gone
    assert (tmp_path / "out" / "FREEZE_VERIFY_REPORT.json").exists()


def test_a_run_that_selects_no_test_is_not_a_pass(repo, tmp_path, lock):
    r = FV.rebuild(repo, "HEAD", tmp_path / "out", select="no_such_keyword", extra_tests=(), lock=lock)
    assert r["tests_selected"] == 0 and r["overall"] == "FAIL"


def test_output_folder_inside_the_repository_is_refused(repo, lock):
    with pytest.raises(ValueError):
        _run(repo, repo / "verify_out", lock)


def test_provenance_only_change_is_behaviour_identical_and_downstream_is_refused_by_the_pin(repo, tmp_path, lock):
    p = _patch(tmp_path, repo, ENGINE + "# a comment-only change\n", "comment.diff")
    r = _run(repo, tmp_path / "out", lock, patches=[p])
    g = {x["file"].rsplit("::", 1)[-1]: x for x in r["groups"]}
    pkg, pkg2 = g["test_pkg_rebuild_is_byte_identical"], g["test_pkg2_rebuild_is_byte_identical"]
    ch = {c["path"]: c for c in pkg["changes"]}
    assert ch["research/pkg/README.md"]["raw"] == "DIFFERENT" and ch["research/pkg/README.md"]["behaviour"] == "EQUAL"
    assert ch["research/pkg/README.md"]["masks"] == ["M1_CODE_STAMP"]
    assert "research/pkg/out.csv" not in ch                                  # the quantity is byte-identical
    assert pkg["verdict"] == "BEHAVIOUR_IDENTICAL_PROVENANCE_DIFFERS"
    # each test ran alone from the pristine tree: pkg2 checks pkg's committed manifest, whose code pin no longer holds
    assert pkg2["verdict"] == "REFUSED_BY_SOURCE_PIN" and pkg2["builder_errors"]
    assert r["overall"] == "FAIL" and r["repository_unchanged"]


def test_repin_in_the_worktree_only_makes_the_downstream_rebuild_byte_identical(repo, tmp_path, lock):
    p = _patch(tmp_path, repo, ENGINE + "# a comment-only change\n", "comment.diff")
    manifest_before = (repo / "research/pkg/01_PKG_FREEZE_MANIFEST.json").read_bytes()
    r = _run(repo, tmp_path / "out", lock, patches=[p], repin=True)
    assert [x["file"] for x in r["repins"]] == ["engine/calc.py"]
    assert (repo / "research/pkg/01_PKG_FREEZE_MANIFEST.json").read_bytes() == manifest_before    # never in the repo
    g = {x["file"].rsplit("::", 1)[-1]: x for x in r["groups"]}
    pkg, pkg2 = g["test_pkg_rebuild_is_byte_identical"], g["test_pkg2_rebuild_is_byte_identical"]
    assert pkg["verdict"] == "BEHAVIOUR_IDENTICAL_PROVENANCE_DIFFERS"
    assert {c["path"]: c["behaviour"] for c in pkg["changes"]} == {"research/pkg/README.md": "EQUAL",
                                                                    "research/pkg/01_PKG_FREEZE_MANIFEST.json": "EQUAL"}
    assert pkg2["verdict"] == "BYTE_IDENTICAL"
    assert r["overall"] == "PASS" and r["repository_unchanged"]


def test_behaviour_change_is_detected_and_fails(repo, tmp_path, lock):
    p = _patch(tmp_path, repo, "def area(a, b):\n    return a * b + 0.5\n", "behaviour.diff")
    r = _run(repo, tmp_path / "out", lock, patches=[p], repin=True)
    g = {x["file"].rsplit("::", 1)[-1]: x for x in r["groups"]}
    pkg = g["test_pkg_rebuild_is_byte_identical"]
    assert pkg["verdict"] == "BEHAVIOUR_CHANGED" and r["overall"] == "FAIL"
    ch = {c["path"]: c for c in pkg["changes"]}
    assert ch["research/pkg/out.csv"]["behaviour"] == "DIFFERENT"            # the quantity moved
    # pkg2 rebuilt alone reads pkg's committed (immutable) out.csv, so it is unaffected here
    assert g["test_pkg2_rebuild_is_byte_identical"]["verdict"] == "BYTE_IDENTICAL"


def test_outside_the_lock_nothing_is_a_pass(repo, tmp_path):
    bad = tmp_path / "OTHER_LOCK.json"
    env = FV.current_env()
    bad.write_text(json.dumps(dict(schema=FV.LOCK_SCHEMA, python={"version": "0.0.0", "implementation": "X"},
                                   packages=env["packages"])))
    r = _run(repo, tmp_path / "out", bad)
    assert set(r["counts"]) == {"BYTE_IDENTICAL"} and r["overall"] == "NOT_A_PASS_OUTSIDE_THE_LOCKED_ENVIRONMENT"


def test_f1_self_heal_happens_with_the_in_place_pattern_and_the_index_catches_it(repo, tmp_path):
    idx = tmp_path / "INDEX.jsonl"
    FV.write_index(repo, idx)
    assert FV.check_index(repo, idx) == []
    (repo / "engine/calc.py").write_text(ENGINE + "# a comment-only change\n")
    run = lambda: subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                                  "tests/pkg/test_pkg_rebuild.py::test_pkg_rebuild_is_byte_identical"],
                                 cwd=repo, capture_output=True, text=True).returncode
    assert run() != 0                      # first run: fails, and the builder has rewritten the manifest in place
    assert run() == 0                      # second run: passes against the rewritten manifest (F-1)
    bad = {p for p, _, _ in FV.check_index(repo, idx)}
    assert bad == {"research/pkg/01_PKG_FREEZE_MANIFEST.json", "research/pkg/README.md"}


def test_masks_hide_provenance_only_never_a_quantity():
    a = b'{"engine_commit": "818321e+code:6629546ee8609d25", "volume_m3": 1.25, "manifest_sha256": "' + b"a" * 64 + b'"}'
    b = b'{"engine_commit": "818321e+code:0addf3f3d78ef48e", "volume_m3": 1.25, "manifest_sha256": "' + b"b" * 64 + b'"}'
    c = b'{"engine_commit": "818321e+code:0addf3f3d78ef48e", "volume_m3": 1.26, "manifest_sha256": "' + b"b" * 64 + b'"}'
    assert FV.compare("x.json", a, b)["behaviour"] == "EQUAL"
    assert FV.compare("x.json", a, c)["behaviour"] == "DIFFERENT"
    h1, h2 = "1" * 64, "2" * 64
    m1 = json.dumps({"code": {"e.py": h1}, "inputs": {"i.csv": h1}, "outputs": {"o.csv": h1}}).encode()
    m2 = json.dumps({"code": {"e.py": h2}, "inputs": {"i.csv": h1}, "outputs": {"o.csv": h2}}).encode()
    m3 = json.dumps({"code": {"e.py": h2}, "inputs": {"i.csv": h2}, "outputs": {"o.csv": h2}}).encode()
    assert FV.compare("M.json", m1, m2, manifest=True)["behaviour"] == "EQUAL"
    assert FV.compare("M.json", m1, m3, manifest=True)["behaviour"] == "DIFFERENT"          # inputs are never masked
    assert FV.compare("M.json", m1, m2, manifest=False)["behaviour"] == "DIFFERENT"         # outputs map: manifests only
    md1, md2 = b"baseline (sha `0d63015a1995`, 12.5 m3)", b"baseline (sha `cfc96955c021`, 12.5 m3)"
    assert FV.compare("C.md", md1, md2)["behaviour"] == "EQUAL"
    assert FV.compare("C.md", md1, md2.replace(b"12.5", b"12.6"))["behaviour"] == "DIFFERENT"
    assert FV.compare("C.csv", b"1234567890ab,+code:aaaaaaaa", b"1234567890ab,+code:bbbbbbbb")["behaviour"] == "EQUAL"
    assert FV.compare("C.csv", b"1234567890ab,+code:aaaaaaaa", b"1234567890ac,+code:bbbbbbbb")["behaviour"] == "DIFFERENT"


def test_chain_detects_edit_reorder_and_history_detects_truncation(tmp_path):
    p = tmp_path / "R.jsonl"
    FV.append_chain(p, [{"id": "A"}, {"id": "B"}, {"id": "C"}])
    assert [e["id"] for e in FV.read_chain(p)] == ["A", "B", "C"]
    lines = p.read_bytes().splitlines(keepends=True)
    for broken in (lines[0].replace(b'"A"', b'"Z"') + b"".join(lines[1:]),       # an edited line
                   lines[1] + lines[0] + lines[2]):                              # reordered
        p.write_bytes(broken)
        with pytest.raises(ValueError):
            FV.read_chain(p)
    r = tmp_path / "hist"
    r.mkdir()
    q = r / "R.jsonl"
    FV.append_chain(q, [{"id": "A"}, {"id": "B"}])
    _git(r, "init", "-q")
    _git(r, "add", "-A")
    _git(r, "commit", "-qm", "1")
    FV.append_chain(q, [{"id": "C"}])
    assert FV.append_only_history(r, "R.jsonl") == []
    q.write_bytes(b"".join(q.read_bytes().splitlines(keepends=True)[:1]))       # the last lines removed
    FV.read_chain(q)                                                             # a chain alone cannot see it ...
    assert FV.append_only_history(r, "R.jsonl")                                  # ... the history can
