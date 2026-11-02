"""T-463 (owner directive 2026-11-02 D2): tests that look up old commits pass in a shallow clone.

tools/git_history.py answers ancestry / rev-parse / file-at-commit / tree / diff questions from the real git history
and, ONLY in a shallow repository and ONLY for a missing object, from research/agents_t463/GIT_FACTS.json.
Checks:
- live (full clone): every recorded fact equals the real history (ancestors = git rev-list of the recorded head; blob
  ids and sha256 per requested commit:path); the requests cover every freeze the patched tests prove;
- synthetic repository (not the training villa; built in a temp folder, hand-known history), cloned --depth 2 (c3, c4 present; c3 is the grafted boundary):
  normal cases (recorded old commit is an ancestor, short id resolves, a changed file's old sha256 comes from the
  facts, an unchanged file's old bytes come from its blob, ls-tree, diff) and adverse cases (an unrecorded commit is
  refused, a head that does not descend from the recorded history is refused, a missing blob raises, no fact file
  raises, tampered facts are reported by check, a full clone never falls back, writing from a shallow clone refused).
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tools import git_history as GH  # noqa: E402

FACTS = ROOT / GH.FACTS_REL
GIT = shutil.which("git") is not None
ENV = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.invalid", GIT_COMMITTER_NAME="t",
           GIT_COMMITTER_EMAIL="t@example.invalid", GIT_CONFIG_NOSYSTEM="1", HOME=os.environ.get("HOME", "/tmp"))


def _g(repo, *a, check=True):
    p = subprocess.run(["git", "-C", str(repo), *a], capture_output=True, text=True, env=ENV)
    if check and p.returncode != 0:
        raise AssertionError(p.stderr)
    return p.stdout.strip()


def _commit(repo, files, msg):
    for rel, text in files.items():
        f = repo / rel
        if text is None:
            f.unlink()
            continue
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text, encoding="utf-8")
    _g(repo, "add", "-A")
    _g(repo, "commit", "-q", "-m", msg)
    return _g(repo, "rev-parse", "HEAD")


@pytest.fixture(scope="module")
def synth(tmp_path_factory):
    """Villa-free synthetic history: c1 freezes d/a.txt + d/b.txt + e/x.txt; c2 changes d/a.txt; c3, c4 unrelated."""
    if not GIT:
        pytest.skip("git not installed")
    base = tmp_path_factory.mktemp("t463")
    full = base / "full"
    full.mkdir()
    _g(full, "init", "-q", "-b", "main")
    c1 = _commit(full, {"d/a.txt": "slab 0.20 m\n", "d/b.txt": "beam 0.60 m\n", "e/x.txt": "x\n"}, "c1 freeze")
    c2 = _commit(full, {"d/a.txt": "slab 0.25 m\n"}, "c2 change a")
    c3 = _commit(full, {"f/y.txt": "y\n"}, "c3")
    c4 = _commit(full, {"f/z.txt": "z\n"}, "c4")
    a_blob = _g(full, "rev-parse", f"{c1}:d/a.txt")
    req = {"trees": [f"{c1[:7]}:d", f"{c1[:7]}:e"], "outputs": [["log", "--format=%s", f"{c1}..{c3}"]],
           "blobs": [a_blob], "last_touch": ["e/x.txt", "d/b.txt"]}
    doc = GH.build(req, root=full)
    shallow = base / "shallow"
    _g(base, "clone", "-q", "--depth", "2", "--branch", "main", f"file://{full}", str(shallow))
    fact = base / "GIT_FACTS.json"
    fact.write_text(json.dumps(doc), encoding="utf-8")
    GH._FACTS.clear()
    return dict(full=full, shallow=shallow, c1=c1, c2=c2, c3=c3, c4=c4, doc=doc, fact=fact, base=base, a_blob=a_blob)


@pytest.fixture()
def installed(synth):
    """The synthetic fact file at its in-repo path inside the shallow clone (git_text / git_bytes read it there)."""
    dst = synth["shallow"] / GH.FACTS_REL
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(synth["fact"], dst)
    GH._FACTS.clear()
    yield synth
    dst.unlink()
    GH._FACTS.clear()


# ------------------------------------------------------------------ live facts (full clone)
def test_live_facts_hold_against_the_real_history():
    """GIT_FACTS.json and GUARD_IMPORTS_T202_HEAD.json equal what git gives, and their requests are what the tests need
    (research/agents_t463/build_t463_facts.py --check)."""
    if not GIT or not (ROOT / ".git").exists():
        pytest.skip("no git checkout")
    if GH.is_shallow(ROOT):
        pytest.skip("shallow clone: the facts are proved in a full clone (this test is their proof)")
    import importlib.util
    spec = importlib.util.spec_from_file_location("t463_builder", ROOT / "research/agents_t463/build_t463_facts.py")
    B = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(B)
    assert B.check() == []


def test_requests_cover_every_freeze_the_patched_tests_prove():
    doc = json.loads(FACTS.read_text(encoding="utf-8"))
    req = set(doc["requests"]["trees"])
    need = set()
    for c, man in (("090a470", "research/urban_engine_m6_completeness/00_ENGINE_FREEZE.json"),
                   ("6c20879", "research/urban_engine_m6_completeness/02_ENGINE_FREEZE_V2.json")):
        need |= {f"{c}:{f}" for f in json.loads((ROOT / man).read_text(encoding="utf-8"))["files_sha256"]}
    for pkg in ("research/urban_engine_m7_reliability", "research/urban_engine_m8_full_scope"):
        fz = json.loads((ROOT / pkg / "00_ENGINE_FREEZE.json").read_text(encoding="utf-8"))
        need |= {f"{fz['commit']}:{f}" for f in fz["files_sha256"]}
    need |= {"201f441:research/alsenan_ground_slab_s8_1", "16741ec:research/alsenan_slab_rebar_s7",
             "ae6393b:research/alsenan_swimming_pool_s8_2", "e2afb69:tests/alsenan/registers_b2a",
             "e2afb69:tests/alsenan/registers_b2a_eval", "9aa2741:tests/alsenan/registers_a3",
             "f820263:tests/alsenan/registers_b1", "02feef8:engine/source", "02feef8:tests/rc1/registers"}
    assert need <= req, sorted(need - req)[:5]
    # every merge commit a BOQ family master names is in the recorded ancestry
    anc = doc["ancestors"]
    for f in sorted((ROOT / "rules/coverage").glob("BOQ_FAMILY_MASTER_*.json")):
        for pk in json.loads(f.read_text(encoding="utf-8")).get("candidate_packages", []):
            mc = pk.get("merge_commit")
            if mc:
                assert any(a.startswith(mc) for a in anc), (f.name, mc)
    assert len(doc["sha256"]) == sum(len(v) for v in doc["trees"].values())


# ------------------------------------------------------------------ synthetic shallow clone: normal
def test_synthetic_clone_is_shallow_and_lacks_the_old_commits(synth):
    assert GH.is_shallow(synth["shallow"]) and not GH.is_shallow(synth["full"])
    assert not GH.has_commit(synth["c1"], synth["shallow"]) and GH.has_commit(synth["c4"], synth["shallow"])


def test_normal_recorded_old_commit_is_an_ancestor(synth):
    s, f = synth["shallow"], synth["fact"]
    assert GH.is_ancestor(synth["c1"], root=s, facts_path=f)
    assert GH.is_ancestor(synth["c2"][:8], root=s, facts_path=f)
    assert GH.rev_parse(synth["c1"][:7], root=s, facts_path=f) == synth["c1"]
    assert GH.rev_parse("HEAD", root=s, facts_path=f) == synth["c4"]          # present: real git


def test_normal_changed_file_sha_from_facts_unchanged_file_bytes_from_its_blob(synth):
    s, f, c1 = synth["shallow"], synth["fact"], synth["c1"]
    assert GH.sha256_at(c1, "d/a.txt", root=s, facts_path=f) == hashlib.sha256(b"slab 0.20 m\n").hexdigest()
    assert GH.show_bytes(c1, "d/b.txt", root=s, facts_path=f) == b"beam 0.60 m\n"   # blob still in HEAD's tree
    assert GH.ls_tree_names(c1, "d/", root=s, facts_path=f) == ["d/a.txt", "d/b.txt"]
    assert GH.changed_since(c1, "d", root=s, facts_path=f) == ["d/a.txt"]
    assert GH.changed_since(c1, "e", root=s, facts_path=f) == []


def test_normal_same_answers_as_git_in_the_full_clone(synth):
    full, c1 = synth["full"], synth["c1"]
    assert GH.changed_since(c1, "d", root=full) == ["d/a.txt"] and GH.changed_since(c1, "e", root=full) == []
    assert GH.sha256_at(c1, "d/a.txt", root=full) == hashlib.sha256(b"slab 0.20 m\n").hexdigest()
    assert GH.ls_tree_names(c1, "d/", root=full) == ["d/a.txt", "d/b.txt"]


def test_normal_added_file_is_a_change_unless_the_filter_excludes_additions(synth, tmp_path):
    s, f, c1 = synth["shallow"], synth["fact"], synth["c1"]
    extra = s / "e" / "new.txt"
    extra.write_text("new\n", encoding="utf-8")
    try:
        assert GH.changed_since(c1, "e", root=s, facts_path=f) == ["e/new.txt"]
        assert GH.changed_since(c1, "e", root=s, diff_filter="MDRTC", facts_path=f) == []
        (s / "e" / "x.txt").write_text("edited\n", encoding="utf-8")
        assert GH.changed_since(c1, "e", root=s, diff_filter="MDRTC", facts_path=f) == ["e/x.txt"]
    finally:
        extra.unlink()
        _g(s, "checkout", "-q", "--", "e/x.txt")


# ------------------------------------------------------------------ synthetic shallow clone: adverse
def test_adverse_unrecorded_commit_is_refused(synth):
    s, f = synth["shallow"], synth["fact"]
    assert GH.is_ancestor("f" * 40, root=s, facts_path=f) is False
    with pytest.raises(GH.HistoryUnavailable):
        GH.rev_parse("fffffff", root=s, facts_path=f)


def test_adverse_head_not_descending_from_the_recorded_history_is_refused(synth, tmp_path):
    s = synth["shallow"]
    doc = dict(synth["doc"])
    _g(s, "checkout", "-q", "--orphan", "other")
    _g(s, "commit", "-q", "--allow-empty", "-m", "unrelated")
    try:
        other = _g(s, "rev-parse", "HEAD")
        doc["recorded_head"] = synth["c4"]               # present, but HEAD (orphan) does not descend from it
        f = tmp_path / "facts.json"
        f.write_text(json.dumps(doc), encoding="utf-8")
        GH._FACTS.clear()
        assert GH.is_ancestor(synth["c1"], other, root=s, facts_path=f) is False
    finally:
        _g(s, "checkout", "-q", "main")
        GH._FACTS.clear()


def test_adverse_missing_blob_or_unrecorded_path_raises(synth, tmp_path):
    s, f, c1 = synth["shallow"], synth["fact"], synth["c1"]
    assert GH.show_bytes(c1, "d/a.txt", root=s, facts_path=f) == b"slab 0.20 m\n"   # stored blob, id-verified
    doc = dict(synth["doc"], blobs={})
    nostore = tmp_path / "facts_no_blobs.json"
    nostore.write_text(json.dumps(doc), encoding="utf-8")
    GH._FACTS.clear()
    with pytest.raises(GH.HistoryUnavailable):
        GH.show_bytes(c1, "d/a.txt", root=s, facts_path=nostore)  # the 0.20 m blob left with c1 and is not stored
    GH._FACTS.clear()
    with pytest.raises(GH.HistoryUnavailable):
        GH.sha256_at(c1, "f/y.txt", root=s, facts_path=f)         # never requested


def test_adverse_no_fact_file_raises_in_a_shallow_clone(synth, tmp_path):
    with pytest.raises(GH.HistoryUnavailable):
        GH.rev_parse(synth["c1"][:7], root=synth["shallow"], facts_path=tmp_path / "absent.json")


def test_adverse_tampered_facts_are_reported_by_check(synth):
    full, doc = synth["full"], synth["doc"]
    assert GH.check(doc, full) == []
    bad = json.loads(json.dumps(doc))
    bad["ancestors"].append("f" * 40)
    key = next(iter(bad["sha256"]))
    bad["sha256"][key] = "0" * 64
    probs = GH.check(bad, full)
    assert any("ancestors differ" in p for p in probs) and any("recorded sha256 differs" in p for p in probs)


def test_adverse_full_clone_never_falls_back(synth):
    full, f = synth["full"], synth["fact"]
    assert GH.is_ancestor("f" * 40, root=full, facts_path=f) is False
    with pytest.raises(RuntimeError) as e:
        GH.rev_parse("fffffff", root=full, facts_path=f)
    assert not isinstance(e.value, GH.HistoryUnavailable)


def test_adverse_writing_or_checking_from_a_shallow_clone_is_refused(synth):
    with pytest.raises(RuntimeError):
        GH.build({"trees": []}, root=synth["shallow"])
    with pytest.raises(RuntimeError):
        GH.check(synth["doc"], synth["shallow"])


def test_normal_recorded_output_stored_blob_and_boundary_last_commit(installed):
    s, c1, c3 = installed["shallow"], installed["c1"], installed["c3"]
    assert GH.git_text(s, "log", "--format=%s", f"{c1}..{c3}") == "c3\nc2 change a\n"
    assert GH.git_bytes(s, "cat-file", "blob", installed["a_blob"]) == b"slab 0.20 m\n"   # stored, id-verified
    boundary = _g(s, "log", "-1", "--format=%H", "--", "e/x.txt")
    assert boundary == c3                                 # the shallow clone's own (wrong) answer: the graft
    assert GH.last_commit("e/x.txt", root=s) == c1        # recorded, git-proved
    assert GH.last_commit("f/z.txt", root=s) == installed["c4"]   # touched inside the clone: git's answer
    with pytest.raises(GH.HistoryUnavailable):
        GH.last_commit("f/y.txt", root=s)                 # graft answer, not recorded: ambiguous, refused
    assert GH.last_commit("e/x.txt", root=installed["full"]) == c1


def test_normal_name_status_since_against_the_working_tree(installed):
    s, c1 = installed["shallow"], installed["c1"]
    assert GH.name_status_since(c1, ["d/", "e/"], root=s) == [("M", "d/a.txt")]
    assert GH.git_text(s, "diff", "--name-status", "--no-renames", c1, "--", "d/", "e/") == "M\td/a.txt\n"
    assert GH.name_status_since(c1, ["d/", "e/"], root=installed["full"]) == [("M", "d/a.txt")]


def test_adverse_unrecorded_command_or_blob_fails_like_git(installed):
    s, c1, c2 = installed["shallow"], installed["c1"], installed["c2"]
    with pytest.raises(GH.HistoryUnavailable):
        GH.git_text(s, "log", "--format=%s", f"{c1}..{c2}")                   # not the recorded arguments
    with pytest.raises(subprocess.CalledProcessError):
        GH.git_bytes(s, "cat-file", "blob", "0" * 40)                          # neither present nor stored
    with pytest.raises(subprocess.CalledProcessError):
        GH.git_text(installed["full"], "cat-file", "blob", "0" * 40)           # full clone: git's own failure


def test_adverse_tampered_stored_blob_is_refused(installed, tmp_path):
    s = installed["shallow"]
    doc = json.loads((s / GH.FACTS_REL).read_text(encoding="utf-8"))
    import base64
    assert doc["blobs"][installed["a_blob"]] == {"text": "slab 0.20 m\n"}     # stored as readable text
    doc["blobs"][installed["a_blob"]] = {"base64": base64.b64encode(b"slab 0.30 m\n").decode("ascii")}
    (s / GH.FACTS_REL).write_text(json.dumps(doc), encoding="utf-8")
    GH._FACTS.clear()
    with pytest.raises(GH.HistoryUnavailable):
        GH.git_bytes(s, "cat-file", "blob", installed["a_blob"])
    assert any("do not hash to their id" in p for p in GH.check(doc, installed["full"]))


def test_adverse_last_commit_untrusted_when_the_recorded_head_left_the_clone(installed):
    s = installed["shallow"]
    doc = json.loads((s / GH.FACTS_REL).read_text(encoding="utf-8"))
    doc["recorded_head"] = installed["c2"]               # older than this depth-2 clone: a newer touch could hide
    (s / GH.FACTS_REL).write_text(json.dumps(doc), encoding="utf-8")
    GH._FACTS.clear()
    with pytest.raises(GH.HistoryUnavailable):
        GH.last_commit("e/x.txt", root=s)
