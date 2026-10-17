"""§1, §2. An export says where it came from, or it is not exported.

The audit of the Round 6C and 6D bundles could not tell which code had
produced them. The manifests carried a short commit and a pile of
hashes, and none of it answered the two questions an auditor actually
asks: WAS THIS BUILT FROM COMMITTED CODE, and IS THIS FILE THE FILE
THAT COMMIT PRODUCES.

So an export is gated. Before a single table is written:

    the worktree is CLEAN          — nothing uncommitted went into it;
    HEAD is recorded in full       — the commit, not an abbreviation;
    the TREE hash is recorded      — what the commit's content IS,
                                     which a rebase or a rewritten
                                     message cannot change;
    the tests are recorded PASSED  — by count, from a real run;
    the INPUT source is hashed     — the drawing, by its own bytes.

And §2, the hashing itself, which the audit found ambiguous. Every file
in a bundle carries TWO hashes and they answer different questions:

    RAW_FILE_SHA256            the bytes on disk. Change the indent, the
                               line ending or the key order and this
                               changes. It answers: is this the same
                               FILE?
    CANONICAL_CONTENT_SHA256   the content, serialised one way: sorted
                               keys, no insignificant whitespace, UTF-8.
                               Re-indent the file and this does NOT
                               change; change a number and it does. It
                               answers: is this the same ANSWER?

A bundle whose canonical hashes match an earlier bundle carries the
same answers however it was written out. A bundle whose raw hashes
match is byte-for-byte the same file. Neither is the other, and a
manifest that gives one hash and calls it "the hash" is the thing this
module exists to stop.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

MODEL = "AN_EXPORT_CARRIES_WHERE_IT_CAME_FROM_V1"

CLEAN = "CLEAN"
DIRTY = "DIRTY"
NOT_A_REPOSITORY = "NOT_A_GIT_REPOSITORY"

TESTS_PASSED = "PASSED"
TESTS_NOT_RUN = "NOT_RUN"

# The fields §1 requires. An export that cannot fill one of these does
# not go out with the field missing; it does not go out.
REQUIRED = ("SOURCE_COMMIT", "GIT_TREE_HASH", "WORKTREE_STATUS",
            "INPUT_SOURCE_HASH", "ENGINE_HASHES", "EXPORT_HASHES")

RAW = "RAW_FILE_SHA256"
CANONICAL = "CANONICAL_CONTENT_SHA256"


class ExportRefused(RuntimeError):
    """The gate said no. Nothing was written."""


def _git(*args) -> str:
    try:
        return subprocess.run(["git", *args], capture_output=True,
                              text=True, check=True).stdout.strip()
    except Exception:      # noqa: BLE001
        return ""


def head_commit() -> str:
    return _git("rev-parse", "HEAD")


def tree_hash() -> str:
    """What the commit's CONTENT is, which a rewritten commit keeps."""
    return _git("rev-parse", "HEAD^{tree}")


def worktree_status() -> dict:
    """CLEAN only when git reports nothing at all, tracked or not."""
    inside = _git("rev-parse", "--is-inside-work-tree")
    if inside != "true":
        return {"status": NOT_A_REPOSITORY, "changed": []}
    out = _git("status", "--porcelain")
    changed = [line[3:] for line in out.splitlines() if line.strip()]
    return {"status": (CLEAN if not changed else DIRTY), "changed": changed}


def canonical_text(obj) -> str:
    """One serialisation, so that one content has one hash."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), default=str)


def canonical_sha256(obj) -> str:
    return hashlib.sha256(canonical_text(obj).encode("utf-8")).hexdigest()


def raw_sha256(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _rows_from_csv(path) -> list:
    import csv

    with open(path, newline="", encoding="utf-8") as fh:
        return [dict(r) for r in csv.DictReader(fh)]


def file_hashes(path, content=None) -> dict:
    """Both hashes of one exported file, and what each one means.

    `content` is the object the file was written FROM. Without it the
    canonical content is read back off disk — JSON parsed, CSV read as
    rows — so that a reader who only has the bundle gets the same
    canonical hash as the writer who made it.
    """
    p = Path(path)
    if content is None:
        if p.suffix.lower() == ".json":
            content = json.loads(p.read_text(encoding="utf-8"))
        elif p.suffix.lower() == ".csv":
            content = _rows_from_csv(p)
        else:
            content = p.read_text(encoding="utf-8", errors="replace")
    return {
        "file": p.name,
        "bytes": p.stat().st_size,
        RAW: raw_sha256(p),
        CANONICAL: canonical_sha256(content),
        "what_each_hash_answers": {
            RAW: "is this the same FILE, byte for byte",
            CANONICAL: ("is this the same ANSWER, however it was "
                        "written out"),
        },
    }


def input_source_hash(paths) -> list:
    """The drawing this run measured, by its own bytes."""
    out = []
    for p in paths:
        path = Path(p)
        if not path.exists():
            out.append({"file": str(p), "status": "MISSING"})
            continue
        out.append({"file": path.name, "path": str(path),
                    "bytes": path.stat().st_size,
                    RAW: raw_sha256(path)})
    return out


def gate(*, input_sources, engine_hashes, tests, allow_dirty=False,
         why_dirty_is_allowed="") -> dict:
    """§1. The provenance block, or ExportRefused and nothing written.

    `tests` is {"passed": int, "failed": int, "command": str} from a run
    that actually happened. A bundle that says PASSED without a count
    is a bundle that says nothing.
    """
    wt = worktree_status()
    if wt["status"] != CLEAN and not allow_dirty:
        raise ExportRefused(
            "the worktree is not clean, and an export from an unclean "
            "worktree cannot be reproduced from its commit. Uncommitted: "
            + ", ".join(wt["changed"][:20]))
    passed = int((tests or {}).get("passed", 0) or 0)
    failed = int((tests or {}).get("failed", 0) or 0)
    if failed or not passed:
        raise ExportRefused(
            f"the tests are not passing ({passed} passed, {failed} "
            "failed). An export is a claim that the engine works")
    head = head_commit()
    tree = tree_hash()
    if not head or not tree:
        raise ExportRefused("there is no commit to export from")
    block = {
        "model": MODEL,
        "SOURCE_COMMIT": head,
        "GIT_TREE_HASH": tree,
        "WORKTREE_STATUS": wt["status"],
        "WORKTREE_CHANGED": wt["changed"],
        "INPUT_SOURCE_HASH": input_source_hash(input_sources),
        "ENGINE_HASHES": dict(engine_hashes),
        "TESTS": {"status": TESTS_PASSED, "passed": passed,
                  "failed": failed,
                  "command": (tests or {}).get("command", "")},
        "EXPORT_HASHES": [],      # filled as the files are written
        "why_dirty_is_allowed": why_dirty_is_allowed,
        "what_this_promises": (
            "this bundle was written by this commit's code, from this "
            "drawing, with these tests passing. Check out the commit, "
            "run the exporter and the canonical hashes come back"),
    }
    return block


def seal(block: dict, files) -> dict:
    """Close the provenance block over the files that were written."""
    block = dict(block)
    block["EXPORT_HASHES"] = list(files)
    missing = [k for k in REQUIRED if not block.get(k)]
    if missing:
        raise ExportRefused(
            "the provenance block is missing " + ", ".join(missing))
    block["PROVENANCE_HASH"] = canonical_sha256(
        {k: block[k] for k in REQUIRED})[:24]
    return block


def verify(block: dict, directory) -> dict:
    """Re-hash a bundle on disk against what its manifest claims."""
    root = Path(directory)
    rows = []
    for entry in block.get("EXPORT_HASHES", ()):
        p = root / entry["file"]
        if not p.exists():
            rows.append({"file": entry["file"], "status": "MISSING"})
            continue
        now = file_hashes(p)
        rows.append({
            "file": entry["file"],
            "raw_matches": now[RAW] == entry.get(RAW),
            "canonical_matches": now[CANONICAL] == entry.get(CANONICAL),
            "status": ("SAME_FILE" if now[RAW] == entry.get(RAW)
                       else ("SAME_ANSWER_DIFFERENT_FILE"
                             if now[CANONICAL] == entry.get(CANONICAL)
                             else "DIFFERENT")),
        })
    return {
        "model": MODEL,
        "files": rows,
        "all_raw_match": all(r.get("raw_matches") for r in rows),
        "all_canonical_match": all(r.get("canonical_matches") for r in rows),
    }


def model_hash() -> str:
    parts = ([MODEL] + list(REQUIRED) + [RAW, CANONICAL, CLEAN, DIRTY,
                                         TESTS_PASSED, TESTS_NOT_RUN])
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]
