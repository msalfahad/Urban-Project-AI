"""Private project inputs in tests: SKIP when the named private file is absent, never fail, never hide a defect.

Owner directive 2026-11-02 (D1, board task T-462): a test that needs private project data (git-ignored `data/*`, the
client drawings addressed by sha256 under `data/inputs/by_sha256/`, the experiment outputs of the second and of the
formerly sealed villa under `data/experiments/`, the `data/runs/` reconciliation records, session-upload originals)
must report SKIPPED with ``private data not available: <name>`` in a clean public checkout, so that a red test always
means something is wrong.

Two ways a test declares what it needs (both refuse anything that is not private, see ``private_root``):

1. ``require_private(path, ...)`` at the top of a test (or a fixture): skips when a named file is absent and returns
   the path(s) when present. Use it where the private file is read indirectly, e.g. a rebuild test whose builder
   subprocess opens the drawing.
2. A module-level ``PRIVATE_INPUTS = ("data/experiments/<folder>", ...)`` in a test file: ``tests/conftest.py`` then
   turns a ``FileNotFoundError`` raised during that file's setup or call into a skip, ONLY when the missing file lies
   under one of the declared roots and is still absent after the failure. Any other exception, a missing file outside
   the declared roots, or a private file that is present and fails the assertions, stays a failure.

Strict mode for the machine that holds the private data: ``URBAN_PRIVATE_INPUTS=require`` turns every such skip into a
failure (``private data required but not available: <name>``), so the full private run can never pass silently on a
missing input.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SKIP_PREFIX = "private data not available: "
REQUIRE_PREFIX = "private data required but not available: "
STRICT_ENV = "URBAN_PRIVATE_INPUTS"
# data/ is git-ignored except these two tracked, public subtrees (.gitignore: !/data/trade_rules/, !/data/registry/).
PUBLIC_DATA = ("data/trade_rules", "data/registry")

# The training villa's three hash-addressed private drawings (Drive 'Alsenan chalet project'; never in git).
BY_SHA = "data/inputs/by_sha256"
STRUCT_DXF = f"{BY_SHA}/9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079.dxf"
STRUCT_PDF = f"{BY_SHA}/74da1523f05eb3c6a4fe3ddebaef2c3d841891f003efc03bc32a3fb4553337e3.pdf"
ARCH_DXF = f"{BY_SHA}/ab54dd554c31fe4a6a63ff773dc6d034159a736c7dd78158483b473a4ed31cc4.dxf"


def strict() -> bool:
    return os.environ.get(STRICT_ENV, "").strip().lower() == "require"


def _abs(p, base: Path = ROOT) -> Path:
    p = Path(os.fspath(p)).expanduser()
    return Path(os.path.normpath(p if p.is_absolute() else base / p))


def private_root(p, root: Path = ROOT) -> Path:
    """The absolute path of a declared private input, or ValueError when it is not private.

    Private = under ``data/`` but outside its tracked public subtrees, or outside the repository altogether (a session
    upload). A path anywhere else in the repository (code, tests, research, data/registry ...) is public: a missing
    public file is a defect, never a skip.
    """
    a = _abs(p, root)
    r = Path(os.path.normpath(root))
    try:
        rel = a.relative_to(r)
    except ValueError:
        return a  # outside the repository: a session upload or an external private copy
    parts = rel.parts
    if not parts or parts[0] != "data" or len(parts) < 2:
        raise ValueError(f"not a private input (only data/* or a path outside the repository): {p}")
    if any(rel == Path(pub) or Path(pub) in rel.parents for pub in PUBLIC_DATA):
        raise ValueError(f"not a private input ({'/'.join(parts[:2])} is tracked and public): {p}")
    return a


def display(p, root: Path = ROOT) -> str:
    a = _abs(p, root)
    try:
        return a.relative_to(Path(os.path.normpath(root))).as_posix()
    except ValueError:
        return a.as_posix()


def require_private(*paths, root: Path = ROOT):
    """Skip (or, in strict mode, fail) unless every named private input exists; return the path(s) when they do."""
    if not paths:
        raise ValueError("require_private needs at least one path")
    found = [private_root(p, root) for p in paths]
    missing = [display(a, root) for a in found if not a.exists()]
    if missing:
        names = ", ".join(missing)
        if strict():
            pytest.fail(REQUIRE_PREFIX + names, pytrace=False)
        pytest.skip(SKIP_PREFIX + names)
    return found[0] if len(found) == 1 else found


def declared_roots(module, root: Path = ROOT) -> tuple:
    decl = getattr(module, "PRIVATE_INPUTS", ())
    if isinstance(decl, (str, os.PathLike)):
        decl = (decl,)
    return tuple(private_root(d, root) for d in decl)


def _missing_files(exc: BaseException):
    """FileNotFoundError filenames in the exception and its cause / context chain (bounded, cycle-safe)."""
    seen, out, e = set(), [], exc
    while e is not None and id(e) not in seen and len(seen) < 16:
        seen.add(id(e))
        if isinstance(e, FileNotFoundError) and e.filename:
            out.append(e.filename)
        e = e.__cause__ or e.__context__
    return out


def absent_private_file(exc: BaseException, roots, cwd=None, root: Path = ROOT):
    """The display name of the absent declared private file that caused ``exc``, else None.

    None (the failure stands) when no FileNotFoundError is in the chain, when the missing file is outside every declared
    root, or when the file exists by now (the failure was not caused by its absence).
    """
    if not roots:
        return None
    base = Path(cwd) if cwd else Path(os.getcwd())
    for name in _missing_files(exc):
        a = _abs(name, base)
        if a.exists():
            continue
        if any(a == r or r in a.parents for r in roots):
            return display(a, root)
    return None
