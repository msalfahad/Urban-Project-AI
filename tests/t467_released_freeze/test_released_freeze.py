"""T-467 (owner directive 2026-11-02, E1): the V2 freeze index protects the RELEASED method's code path by hash.

Acceptance (board row): the freeze check with the new index prints 0 on HEAD and fails on a one-byte mutation of a
released module. Every mutation is made on a copy of the indexed files in pytest's temporary folder, never in the
repository. Hand-expected outcomes:

  * clean copy                                  -> 0 differing
  * one byte of engine/source/arch_v29.py (and of two more released modules, one data file) -> exactly that file
  * one byte inside a frozen statement of the hub tools/urban_boq_m9.py (_v29_masonry)       -> exactly that symbol
  * the integration lane's normal edit of the hub (a NEW constant + a NEW function + a change inside cmd_arch)
                                                -> 0 (additive registration stays possible: declared residual)
  * a NEW statement re-binding a frozen name (V29 = ...), a deleted frozen symbol, a missing released file,
    a changed V1 index head                     -> each reported
  * the released run on three synthetic drawings (no client drawing) imports only protected modules, and its outputs
    equal the golden hashes recorded in the spec (Python 3.11 only)
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools import freeze_verify as V1  # noqa: E402
sys.path.insert(0, str(ROOT / "research/freeze_integrity"))
import freeze_verify_v2 as V2  # noqa: E402

FI = "research/freeze_integrity"
V2_INDEX = f"{FI}/FREEZE_BASELINE_INDEX_V2.jsonl"
SPEC = f"{FI}/RELEASED_PATH_V2_9_ROUTE_G.json"
HUB = "tools/urban_boq_m9.py"
PY311 = sys.version_info[:2] == (3, 11)


def entries():
    return V1.read_chain(ROOT / V2_INDEX)


def indexed_paths():
    out = {V2.V1_INDEX, V2_INDEX}
    for e in entries():
        out.add(e["path"])
        out |= set(e.get("artefacts", {}))
    return sorted(out)


@pytest.fixture()
def mirror(tmp_path):
    """a copy of every file the V2 index names, at its repository path."""
    for p in indexed_paths():
        t = tmp_path / p
        t.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / p, t)
    return tmp_path


def flip(path, offset=None):
    b = bytearray(path.read_bytes())
    i = len(b) // 2 if offset is None else offset
    b[i] ^= 0x01
    path.write_bytes(bytes(b))


def labels(repo):
    return [p for p, _, _ in V2.check_index(repo, repo / V2_INDEX)]


# ------------------------------------------------------------------ HEAD
def test_head_is_clean():
    assert V2.check_index(ROOT, ROOT / V2_INDEX) == []


def test_cli_prints_v1_wording_and_exit_0():
    p = subprocess.run([sys.executable, "-I", "research/freeze_integrity/freeze_verify_v2.py", "check", "--index", V2_INDEX], cwd=ROOT,
                       capture_output=True, text=True)
    assert p.returncode == 0, p.stdout + p.stderr
    assert "frozen artefacts differing from the index: 0" in p.stdout


def test_v2_starts_with_the_v1_index_unchanged():
    v1 = (ROOT / V2.V1_INDEX).read_bytes()
    assert (ROOT / V2_INDEX).read_bytes().startswith(v1)
    n1 = len(V1.read_chain(ROOT / V2.V1_INDEX))
    assert n1 == 42
    assert [e["kind"] for e in entries()[:n1]] == [e["kind"] for e in V1.read_chain(ROOT / V2.V1_INDEX)]
    assert all(e.get("schema") == V2.INDEX_SCHEMA_V2 for e in entries()[n1:])


@pytest.mark.skipif(not (ROOT / ".git").exists(), reason="prerequisite: the git history")
def test_v2_index_is_append_only_over_history():
    assert V1.append_only_history(ROOT, V2_INDEX) == []


def test_released_modules_are_indexed_by_hash():
    code = {e["path"] for e in entries() if e["kind"] == "RELEASED_CODE"}
    for p in ("engine/source/arch_v27.py", "engine/source/arch_v28.py", "engine/source/arch_v29.py",
              "engine/source/arch_measure.py", "tools/urban_structural_boq.py", "tools/freeze_verify.py",
              "research/freeze_integrity/freeze_verify_v2.py"):
        assert p in code, p
    assert not any(p.startswith("engine/source/arch_v3") for p in code)      # V3.0.x candidates are not released
    hub = [e for e in entries() if e["kind"] == V2.SYMBOL_KIND]
    assert [e["path"] for e in hub] == [HUB]
    assert hub[0]["hubs_not_hashed"] == ["cmd_arch", "main"]
    for s in ("_v29_masonry", "_v29_facade", "_v29_line", "V29", "ARCH_METHODS", "_arch_compute", "arch_compute"):
        assert s in hub[0]["symbols"], s
    assert HUB not in code                                                     # the hub is frozen per statement only


def test_spec_and_index_agree():
    spec = V2.load_spec(ROOT / SPEC)
    got = {(e["kind"], e["path"]) for e in entries()[42:]}
    want = {("RELEASED_CODE", p) for p in spec["code"]} | {("RELEASED_DATA", p) for p in spec["data"]} | \
           {(V2.SYMBOL_KIND, h["path"]) for h in spec["hubs"]}
    assert got == want


# ------------------------------------------------------------------ one-byte mutations (on a copy)
def test_clean_copy_is_clean(mirror):
    assert labels(mirror) == []


@pytest.mark.parametrize("path", ["engine/source/arch_v29.py", "engine/source/arch_v27.py",
                                  "engine/source/knowledge.py", "knowledge/URBAN_ENGINEERING_KNOWLEDGE_1.5.0.json"])
def test_one_byte_in_a_released_file_fails(mirror, path):
    flip(mirror / path)
    assert labels(mirror) == [path]
    p = subprocess.run([sys.executable, "-I", str(ROOT / "research/freeze_integrity/freeze_verify_v2.py"), "--repo", str(mirror), "check",
                        "--index", str(mirror / V2_INDEX)], capture_output=True, text=True)
    assert p.returncode == 1 and "frozen artefacts differing from the index: 1" in p.stdout


def test_one_byte_at_the_first_and_last_byte(mirror):
    f = mirror / "engine/source/arch_v29.py"
    flip(f, 0)
    assert labels(mirror) == ["engine/source/arch_v29.py"]
    flip(f, 0)
    assert labels(mirror) == []
    flip(f, len(f.read_bytes()) - 1)
    assert labels(mirror) == ["engine/source/arch_v29.py"]


def _hub_line(src, needle):
    i = src.index(needle)
    return i + len(needle) // 2


def test_one_byte_inside_a_frozen_hub_statement_fails(mirror):
    f = mirror / HUB
    src = f.read_text(encoding="utf-8")
    body = src.index("def _v29_masonry(")
    i = src.index("UP-MAS-HEIGHT-001", body)                                  # inside its docstring
    b = bytearray(f.read_bytes())
    pos = len(src[:i].encode("utf-8")) + 3
    b[pos] ^= 0x01
    f.write_bytes(bytes(b))
    assert labels(mirror) == [f"{HUB}::_v29_masonry"]


def test_one_byte_in_a_frozen_constant_fails(mirror):
    f = mirror / HUB
    src = f.read_text(encoding="utf-8")
    f.write_text(src.replace('V29 = "ARCH_TAKEOFF_V2.9"', 'V29 = "ARCH_TAKEOFF_V2.8"', 1), encoding="utf-8")
    assert labels(mirror) == [f"{HUB}::V29"]


def test_integration_lane_edit_is_allowed(mirror):
    """the pattern of every lane I registration since 2026-10-20: a new method constant, a new helper, a new branch
    inside cmd_arch; no frozen statement changes."""
    f = mirror / HUB
    src = f.read_text(encoding="utf-8")
    src = src.replace("\ndef cmd_arch(a):\n", '\nV9999 = "ARCH_TAKEOFF_V9.9.99"\nCANDIDATE_EXTENSIONS_V9999 = (V9999,)\n\n\n'
                      "def _v9999_outputs(out):\n    return out\n\n\ndef cmd_arch(a):\n    _t467_probe = 1\n", 1)
    f.write_text(src, encoding="utf-8")
    assert labels(mirror) == []


def test_rebinding_a_frozen_name_fails(mirror):
    f = mirror / HUB
    f.write_text(f.read_text(encoding="utf-8") + '\nV29 = "ARCH_TAKEOFF_V3.0"\n', encoding="utf-8")
    got = labels(mirror)
    assert len(got) == 1 and got[0].startswith(f"{HUB}::V29#2 rebinds V29")


def test_rebinding_inside_a_new_block_fails(mirror):
    f = mirror / HUB
    f.write_text(f.read_text(encoding="utf-8") + "\nif True:\n    def _v29_line(*a, **k):\n        return None\n",
                 encoding="utf-8")
    got = labels(mirror)
    assert len(got) == 1 and "rebinds _v29_line" in got[0]


def test_deleting_a_frozen_symbol_fails(mirror):
    f = mirror / HUB
    src = f.read_text(encoding="utf-8")
    a = src.index("def _v29_facade(")
    b = src.index("\ndef ", a + 10)
    f.write_text(src[:a] + src[b + 1:], encoding="utf-8")
    assert f"{HUB}::_v29_facade" in labels(mirror)


def test_missing_released_file_fails(mirror):
    (mirror / "engine/source/arch_v28.py").unlink()
    assert labels(mirror) == ["engine/source/arch_v28.py"]


def test_hub_syntax_error_fails(mirror):
    f = mirror / HUB
    f.write_text(f.read_text(encoding="utf-8") + "\ndef (:\n", encoding="utf-8")
    assert labels(mirror) == [HUB]


def test_v1_head_changed_fails(mirror):
    v1 = mirror / V2.V1_INDEX
    v1.write_bytes(v1.read_bytes() + b"\n")
    assert labels(mirror) == [f"V1_PREFIX {V2.V1_INDEX}"]


def test_editing_an_earlier_v2_line_breaks_the_chain(mirror):
    f = mirror / V2_INDEX
    lines = f.read_bytes().splitlines(keepends=True)
    lines[50] = lines[50].replace(b'"RELEASED_', b'"RELEASEX_', 1)
    f.write_bytes(b"".join(lines))
    with pytest.raises(ValueError, match="chain broken"):
        V2.check_index(mirror, f)


def test_write_index_refuses_a_changed_released_file(mirror):
    flip(mirror / "engine/source/arch_v29.py")
    with pytest.raises(ValueError, match="changed since it was indexed"):
        V2.write_index(mirror, mirror / V2_INDEX, V2.load_spec(ROOT / SPEC))


def test_write_index_is_idempotent_on_head(tmp_path):
    out = tmp_path / "idx.jsonl"
    shutil.copyfile(ROOT / V2_INDEX, out)
    assert V2.write_index(ROOT, out, V2.load_spec(ROOT / SPEC)) == (len(entries()), 0)
    assert out.read_bytes() == (ROOT / V2_INDEX).read_bytes()


# ------------------------------------------------------------------ the statement parser (synthetic module)
def test_top_level_keys_decorators_duplicates_and_unnamed():
    src = "import os\n\n@staticmethod\ndef f():\n    return 1\n\nX = 1\nX = 2\nif os:\n    Y = 3\n"
    keys = [k for k, _, _ in V2.top_level(src)]
    assert keys[1:4] == ["f", "X", "X#2"] and keys[0].startswith("stmt:") and keys[4].startswith("stmt:")
    a = dict((k, h) for k, h, _ in V2.top_level(src))
    b = dict((k, h) for k, h, _ in V2.top_level(src.replace("@staticmethod", "@classmethod")))
    assert a["f"] != b["f"]                                                    # a decorator is part of the statement
    assert V2.top_level(src)[4][2] == {"Y"}


# ------------------------------------------------------------------ the released run: coverage and golden outputs
@pytest.fixture(scope="module")
def released_runs(tmp_path_factory):
    from engine.source import arch_measure as AM
    from tools import arch_synth as AS
    from tools import synthetic_villa_m8 as SM8
    sys.path.insert(0, str(ROOT / "tests/m9_n10"))
    import n10_fixtures as F
    d = tmp_path_factory.mktemp("t467_runs")
    st = SM8.generate(d, 21)
    plan = d / "villa.dxf"
    AS.villa(plan)
    facts = d / "facts.json"
    facts.write_text(json.dumps({"schema": AM.FACTS_SCHEMA}), encoding="utf-8")
    F.curved_room(d / "curved.dxf")
    F.masonry_room(d / "mas.dxf", column=True, enclosure=True)
    runs = {
        "villa_seed21": ["arch", "--drawings", str(plan), "--out", str(d / "o_villa"), "--method", "ARCH_TAKEOFF_V2.9",
                         "--as-of", "2026-01-01", "--structural", str(st), "--conventions",
                         str(ROOT / "engine/profiles/URBAN_M8_GENERIC_CONVENTIONS_V6.json"), "--profile",
                         str(d / "villa_m8_21.profile.json"), "--facts", str(facts), "--project", "synthetic-villa"],
        "n10_curved_room": ["arch", "--drawings", str(d / "curved.dxf"), "--out", str(d / "o_curved"), "--method",
                            "ARCH_TAKEOFF_V2.9"],
        "n10_masonry_room_column_enclosure": ["arch", "--drawings", str(d / "mas.dxf"), "--out", str(d / "o_mas"),
                                              "--method", "ARCH_TAKEOFF_V2.9"],
    }
    out = {}
    for name, argv in runs.items():
        t = V2.trace(ROOT, d / f"{name}.trace.json", argv)
        out[name] = {"trace": t, "out": Path(argv[argv.index("--out") + 1])}
    return out


def test_released_run_imports_only_protected_modules(released_runs):
    spec = V2.load_spec(ROOT / SPEC)
    for name, r in released_runs.items():
        assert r["trace"]["exit"] in (0, None), name
        assert V2.uncovered(spec, r["trace"]) == [], name
        assert HUB in r["trace"]["modules"]
        assert not any(m.startswith("engine/source/arch_v3") for m in r["trace"]["modules"]), name


def test_coverage_detects_an_unprotected_module(released_runs):
    spec = V2.load_spec(ROOT / SPEC)
    spec = dict(spec, code=[p for p in spec["code"] if p != "engine/source/arch_v29.py"])
    assert V2.uncovered(spec, released_runs["villa_seed21"]["trace"]) == ["engine/source/arch_v29.py"]


@pytest.mark.skipif(not PY311, reason="golden outputs are recorded on Python 3.11 (one-ulp differences on 3.13)")
def test_released_outputs_equal_the_golden_hashes(released_runs):
    golden = V2.load_spec(ROOT / SPEC)["golden"]
    for name, r in released_runs.items():
        for fname, h in golden[name].items():
            assert V2.sha((r["out"] / fname).read_bytes()) == h, f"{name}: {fname}"
