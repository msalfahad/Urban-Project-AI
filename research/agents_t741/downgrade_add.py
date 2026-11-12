"""T-741: the Checker's issue path for one URBAN_CHECKER_DOWNGRADE_V1 record (downgrade only).

The wrapper `bash scripts/agent_env.sh run` allows research/agents_t*/*.py scripts only, so the Checker could not run
`tools/boq_export_v1.py downgrade-add` (T-734: 'AGENT_ENV FAIL: run allows only ...'). This thin entry runs THAT
action and nothing else, after the merge, as

    bash scripts/agent_env.sh run --tree engine research/agents_t741/downgrade_add.py [downgrade-add] \
        --lines <V3_0_x_BOQ_LINES.json> --candidate-version ARCH_TAKEOFF_V3.0.x --line-ids L-... --state HELD \
        [--basis-label "UNSUPPORTED BASIS"] --reason "..." --evidence "SHEET=PRINTED VALUE" [--evidence ...] \
        (--lock-file <board>/docs/agents/locks/checker.lock | --run-token T --routine Checker) --verdict-commit SHA \
        [--time ISO-UTC] [--downgrade-id DG-...] --out <board>/docs/agents/verdicts/V3.0.x/DOWNGRADES.json [--dry-run]

Rule (owner 2026-10-24 23:57; UP-QTY-STATUS-001): a downgrade-only record is Checker-issued, line-bound, may only move
a line to HELD / CONFLICT, never promotes and carries no Checker measurement. The record itself is built, validated and
appended by tools/boq_export_v1.py main_downgrade_add (downgrade_add / validate_downgrade): no copy of its logic here,
the frozen tool untouched. This entry only REFUSES, before the tool runs:
  - any action other than downgrade-add (verdict-add, verdict-rebind, an export ...) and any option the tool's
    downgrade-add does not take (no abbreviation: an abbreviated option is refused, never widened);
  - a state other than HELD / CONFLICT (a promotion: VERIFIED, RELEASED, MEASURED, ... is never a downgrade);
  - an --out that is not a downgrade record file: <...>/docs/agents/verdicts/V<n>.<n>.<n>/DOWNGRADES.json, given
    without '..', with no symlink on its path and an existing verdicts folder (no other file is ever written);
  - (by the tool) a line id that is not in the named candidate lines, lines of two units, a non-Checker routine.
--dry-run runs the same tool call on a temporary copy of the record file, prints the record it would add and writes
nothing (the record file is hashed before and after: any change fails the run).
Exit: 0 written / dry run printed; 2 refused (one line 'T741 REFUSED: ...').
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import boq_export_v1 as T  # noqa: E402  (read only: main_downgrade_add, DOWNGRADE_STATES)

ACTION = "downgrade-add"
OTHER_ACTIONS = ("verdict-add", "verdict-validate", "verdict-rebind")
RECORD_FILE = "DOWNGRADES.json"
VERSION_DIR_RE = re.compile(r"^V\d+\.\d+\.\d+$")
TAIL = ("docs", "agents", "verdicts")


class Refused(ValueError):
    pass


def parser():
    """the tool's downgrade-add options, exactly (allow_abbrev off), plus --dry-run; argparse errors become Refused."""
    class _P(argparse.ArgumentParser):
        def error(self, message):
            raise Refused(f"arguments: {message}")

    ap = _P(prog="downgrade_add.py", allow_abbrev=False,
            description="T-741: issue one downgrade-only record with tools/boq_export_v1.py downgrade-add")
    ap.add_argument("--lines", required=True)
    ap.add_argument("--candidate-version", required=True)
    ap.add_argument("--line-ids", required=True)
    ap.add_argument("--state", required=True)            # checked by refuse_state (a clear refusal, not a usage error)
    ap.add_argument("--basis-label")
    ap.add_argument("--reason", required=True)
    ap.add_argument("--evidence", action="append", required=True)
    ap.add_argument("--lock-file")
    ap.add_argument("--run-token")
    ap.add_argument("--routine")
    ap.add_argument("--verdict-commit", required=True)
    ap.add_argument("--time")
    ap.add_argument("--downgrade-id")
    ap.add_argument("--out", required=True)
    ap.add_argument("--dry-run", action="store_true")
    return ap


def refuse_action(argv):
    """-> argv without the optional leading action word; any other action word or positional is refused."""
    argv = list(argv)
    if argv and argv[0] == ACTION:
        return argv[1:]
    if argv and argv[0] in OTHER_ACTIONS:
        raise Refused(f"action {argv[0]!r}: this entry issues {ACTION} records only")
    if argv and not argv[0].startswith("-"):
        raise Refused(f"action {argv[0]!r}: this entry issues {ACTION} records only")
    return argv


def refuse_state(state):
    if state not in T.DOWNGRADE_STATES:
        raise Refused(f"state {state!r}: a record may only downgrade a line to {' / '.join(T.DOWNGRADE_STATES)} "
                      "(a promotion is never issued here)")


def record_path(out):
    """-> the absolute record file path, or Refused: <...>/docs/agents/verdicts/V<n>.<n>.<n>/DOWNGRADES.json, no '..',
    no symlink on any existing part, the verdicts folder present."""
    raw = str(out)
    if not raw or "\x00" in raw:
        raise Refused("--out: empty path")
    if ".." in Path(raw).parts or ".." in raw.replace("\\", "/").split("/"):
        raise Refused(f"--out {raw!r}: '..' is not allowed (path traversal)")
    p = Path(os.path.abspath(raw))
    parts = p.parts
    if p.name != RECORD_FILE or len(parts) < 6 or tuple(parts[-5:-2]) != TAIL or not VERSION_DIR_RE.match(parts[-2]):
        raise Refused(f"--out {raw!r}: not a downgrade record file (<...>/docs/agents/verdicts/V<n>.<n>.<n>/"
                      f"{RECORD_FILE})")
    verdicts = p.parent.parent
    if not verdicts.is_dir():
        raise Refused(f"--out {raw!r}: the verdicts folder does not exist")
    q = p
    while True:
        if q.is_symlink():
            raise Refused(f"--out {raw!r}: symlink on the path ({q.name or q})")
        if q.parent == q:
            break
        q = q.parent
    if p.exists() and not p.is_file():
        raise Refused(f"--out {raw!r}: not a regular file")
    if Path(os.path.realpath(p)) != p:
        raise Refused(f"--out {raw!r}: resolves elsewhere")
    return p


def tool_argv(a, out):
    """the canonical argv of the tool's downgrade-add for the parsed arguments (full option names only)."""
    av = ["--lines", a.lines, "--candidate-version", a.candidate_version, "--line-ids", a.line_ids,
          "--state", a.state]
    if a.basis_label is not None:
        av += ["--basis-label", a.basis_label]
    av += ["--reason", a.reason]
    for e in a.evidence:
        av += ["--evidence", e]
    for opt, v in (("--lock-file", a.lock_file), ("--run-token", a.run_token), ("--routine", a.routine)):
        if v is not None:
            av += [opt, v]
    av += ["--verdict-commit", a.verdict_commit]
    for opt, v in (("--time", a.time), ("--downgrade-id", a.downgrade_id)):
        if v is not None:
            av += [opt, v]
    return av + ["--out", str(out)]


def _sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def run(argv, stdout=None):
    """-> exit code. Refusals raise Refused; the tool's own refusals (ExportError) are re-raised as Refused."""
    stdout = stdout or sys.stdout
    a = parser().parse_args(refuse_action(argv))
    refuse_state(a.state)
    out = record_path(a.out)
    if not a.dry_run:
        made = not out.parent.exists()
        out.parent.mkdir(exist_ok=True)              # only the one version folder under an existing verdicts folder
        try:
            with contextlib.redirect_stdout(stdout):
                return T.main_downgrade_add(tool_argv(a, out))
        except T.ExportError as e:
            if made and not any(out.parent.iterdir()):
                out.parent.rmdir()                   # a refused record leaves nothing behind
            raise Refused(str(e)) from e
    before = _sha(out)
    with tempfile.TemporaryDirectory(prefix="t741_dry_") as td:
        tmp = Path(td) / RECORD_FILE
        if out.exists():
            shutil.copyfile(out, tmp)
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                rc = T.main_downgrade_add(tool_argv(a, tmp))
        except T.ExportError as e:
            raise Refused(str(e)) from e
    if _sha(out) != before:
        raise RuntimeError(f"dry run changed {out}: stop and report")
    stdout.write(buf.getvalue())
    stdout.write(f"T741 DRY RUN: nothing written ({out} {'unchanged' if before else 'absent, not created'})\n")
    return rc


def main(argv=None):
    try:
        return run(sys.argv[1:] if argv is None else argv)
    except Refused as e:
        print(f"T741 REFUSED: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
