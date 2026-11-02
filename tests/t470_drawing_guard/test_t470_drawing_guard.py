"""T-470 (owner 2026-11-02, PRIVACY_MOVE_PLAN step 3): AutoCAD drawings cannot be added to this PUBLIC repository again.

Two layers. (1) Name rules in .gitignore: every DWG / DXF / DWF / DWL / DWL2 / BAK / SV$ suffix in any letter case and
an extensionless file named DXF / DWG at any depth are ignored (git matches case-sensitively, so the old *.dxf missed
DRAWING.DXF and the root file `DXF`); a directory named dxf / dwg (code) is not. Checked with `git check-ignore
--no-index` on paths that do not exist, so nothing is written. (2) Content guard: a drawing under ANY name (a name
rule cannot see an extensionless 'plan_A1') is caught by its bytes: the DWG version header 'AC10xx' / 'AC1.x' /
'AC2.x' at byte 0, the ASCII DXF opening group '0 / SECTION' (optionally after a 999 comment) or the binary DXF
sentinel. Every tracked file is checked; the two drawings already tracked before T-470 are listed by path AND sha256
and stay until the owner decides their move (PRIVACY_MOVE_PLAN step 4: ignore rules never untrack, and no agent
deletes them). The list can only shrink: a third drawing, or a changed byte in a listed one, fails."""
from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

# tracked before T-470; removal waits for the owner (PRIVACY_MOVE_PLAN_2026-11-02 step 1 / step 4). Never add a row.
KNOWN_TRACKED_DRAWINGS = {
    "DXF": "8c1f942267bdf2c80b891a16abb119964e882df01ba9afaf0a19a58a1ee3a52f",
    "research/external_engine_lab/MINSERT_REFLECTION_ORACLE.dxf":
        "93d7b98769de874cf2ac3556305f3bd9d5d0ef03c7caaa509a29f17375115076",
}

_DWG = re.compile(rb"\AAC(?:1\d{3}|1\.\d|2\.\d)")
_DXF_ASCII = re.compile(rb"\A\s*(?:999[ \t]*\r?\n[^\n]*\n\s*)?0[ \t]*\r?\nSECTION\b")
_DXF_BINARY = b"AutoCAD Binary DXF\r\n\x1a\x00"


def drawing_kind(head: bytes) -> str | None:
    """'DWG', 'DXF' or None for the first bytes of a file (a UTF-8 BOM is ignored)."""
    if head.startswith(b"\xef\xbb\xbf"):
        head = head[3:]
    if _DWG.match(head):
        return "DWG"
    if head.startswith(_DXF_BINARY) or _DXF_ASCII.match(head):
        return "DXF"
    return None


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True)


def _need_git() -> None:
    if shutil.which("git") is None or _git("rev-parse", "--is-inside-work-tree").returncode != 0:
        pytest.skip("git or a git checkout not available: T-470 ignore / tracked-file checks need one")


def _ignored(path: str) -> bool:
    r = _git("check-ignore", "--no-index", "-q", path)
    assert r.returncode in (0, 1), r.stderr.decode()
    return r.returncode == 0


# ---- detector, synthetic bytes only (normal and adverse cases) ----

@pytest.mark.parametrize("head,kind", [
    (b"AC1032\x00\x00\x00\x00\x00", "DWG"),           # AutoCAD 2018+
    (b"AC1015\x00\x00", "DWG"),                        # AutoCAD 2000
    (b"AC1.50\x00", "DWG"),                            # R2.05
    (b"AC2.10\x00", "DWG"),                            # R2.10
    (b"  0\nSECTION\n  2\nHEADER\n", "DXF"),           # ezdxf / AutoCAD ASCII, LF
    (b"0\r\nSECTION\r\n2\r\nHEADER\r\n", "DXF"),       # CRLF, no padding
    (b"999\r\nmade by a tool\r\n  0\r\nSECTION\r\n", "DXF"),  # leading 999 comment
    (b"\xef\xbb\xbf  0\nSECTION\n", "DXF"),            # BOM
    (_DXF_BINARY + b"\x00\x00", "DXF"),                # binary DXF
])
def test_detector_finds_drawings(head, kind):
    assert drawing_kind(head) == kind


@pytest.mark.parametrize("head", [
    b"", b"# AC1032 is a DWG version\n", b"ACME report\n", b"AC10", b"AC10xx\n",
    b"  0\nSECTIONS of the report\n", b"0\nSECTIONAL\n", b"PK\x03\x04", b"%PDF-1.7\n",
    b"x = 'AC1032'\n", b"  1\nSECTION\n",
])
def test_detector_leaves_other_files_alone(head):
    assert drawing_kind(head) is None


# ---- .gitignore name rules ----

@pytest.mark.parametrize("path", [
    "DXF", "DWG", "dxf", "Dwg", "sub/dir/DXF", "research/x/DWG",          # extensionless, any depth
    "new.dxf", "new.DXF", "new.Dxf", "new.dwg", "new.DWG", "a/b/plan.DwG",  # case variants
    "plot.dwf", "plot.DWF", "lock.dwl", "lock.DWL", "lock.dwl2", "lock.DWL2",
    "plan.bak", "plan.BAK", "plan.sv$", "plan.SV$",
])
def test_drawing_names_are_ignored(path):
    _need_git()
    assert _ignored(path), path


@pytest.mark.parametrize("path", [
    "engine/dxf/reader.py", "tools/dwg/convert.py", "engine/dxf_io.py", "tests/fixtures/dxf_case.json",
    "README.md", "docs/DXF_NOTES.md", "DXF.md", "tests/t470_drawing_guard/test_t470_drawing_guard.py",
    "data/registry/new_registry.json", "data/trade_rules/new_rule.json",
])
def test_code_and_docs_are_not_ignored(path):
    _need_git()
    assert not _ignored(path), path


def test_existing_rules_kept():
    text = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    for rule in ("*.dwg", "*.dxf", "*.xlsx", "/data/*", "!/data/trade_rules/", "!/data/registry/", ".env"):
        assert rule in text, rule


# ---- content guard over every tracked file ----

def _tracked_drawings() -> dict:
    _need_git()
    r = _git("ls-files", "-z")
    assert r.returncode == 0, r.stderr.decode()
    found = {}
    for raw in r.stdout.split(b"\0"):
        if not raw:
            continue
        rel = raw.decode("utf-8", "surrogateescape")
        p = ROOT / rel
        if not p.is_file():          # deleted in the work tree, or a submodule
            continue
        with open(p, "rb") as h:
            kind = drawing_kind(h.read(64))
        if kind:
            found[rel] = (kind, hashlib.sha256(p.read_bytes()).hexdigest())
    return found


def violations(found: dict) -> list:
    """Every tracked drawing that is not a listed one, and every listed one whose bytes changed."""
    out = [f"new tracked drawing: {k} ({v[0]})" for k, v in sorted(found.items()) if k not in KNOWN_TRACKED_DRAWINGS]
    out += [f"listed drawing changed while its move waits for the owner: {k}"
            for k, v in sorted(found.items()) if k in KNOWN_TRACKED_DRAWINGS and v[1] != KNOWN_TRACKED_DRAWINGS[k]]
    return out


def test_tracked_files_hold_no_new_or_changed_drawing():
    found = _tracked_drawings()
    assert not violations(found), violations(found)


def test_guard_reports_adverse_listings():
    """Not vacuous: an extensionless DWG, a DXF under a .txt name and a one-byte change of a listed file all fail;
    the listed files with their pinned hashes and a listed file already moved out (absent) pass."""
    ok = {k: ("DXF", d) for k, d in KNOWN_TRACKED_DRAWINGS.items()}
    assert violations(ok) == [] and violations({}) == []
    bad = dict(ok, **{"plan_A1": ("DWG", "0" * 64), "notes/site.txt": ("DXF", "1" * 64)})
    bad["DXF"] = ("DXF", "2" * 64)
    assert violations(bad) == ["new tracked drawing: notes/site.txt (DXF)", "new tracked drawing: plan_A1 (DWG)",
                               "listed drawing changed while its move waits for the owner: DXF"]
