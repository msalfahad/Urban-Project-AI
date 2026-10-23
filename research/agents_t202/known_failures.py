"""T-202 KNOWN FAILURES CHECK: compare a pytest run with the known-failures ledger, so that workers and the Checker
stop re-diagnosing failures that are already explained. Standard library only; reads files, writes nothing.

    bash scripts/agent_env.sh pytest --tree task-<ID> tests/<folders> > RUN.txt 2>&1
    python3 -I research/agents_t202/known_failures.py check RUN.txt [--ledger research/agents_t202/known_failures.json]

Prints three lists and exits 1 when NEW is not empty:
  NEW      failing / erroring test ids that are not in the ledger: these are the run's own failures (gate b);
  KNOWN    failing ids that are in the ledger, with the ledger's cause and owner;
  ABSENT   ledger ids not failing in this run (fixed, or not collected by this run: the output cannot tell which).
A known failure is never a pass: a run with KNOWN entries is "green except the ledger", said that way in the handoff.

The parser reads pytest's short summary lines (`FAILED <id> - ...`, `ERROR <id> - ...`), which `-q` prints by default
(report chars fE). Ids are compared exactly (node id incl. parameters).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LEDGER = HERE / "known_failures.json"
SUMMARY = re.compile(r"^(FAILED|ERROR) (\S+?)(?: - .*)?$")


def parse(text):
    """{node id: FAILED | ERROR} from pytest output text."""
    out = {}
    for ln in text.splitlines():
        m = SUMMARY.match(ln.strip())
        if m:                     # FAILED <file>::<test>, ERROR <file>::<test> or ERROR <file> (collection error)
            out[m.group(2)] = m.group(1)
    return out


def load_ledger(path=LEDGER):
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    if doc.get("schema") != "URBAN_KNOWN_FAILURES_V1":
        raise ValueError("ledger schema must be URBAN_KNOWN_FAILURES_V1")
    ids = [e["id"] for e in doc["failures"]]
    if len(ids) != len(set(ids)):
        raise ValueError("ledger ids must be unique")
    for e in doc["failures"]:
        for k in ("id", "kind", "first_failing", "cause", "owner"):
            if not e.get(k):
                raise ValueError(f"ledger entry {e.get('id')!r}: {k} is required")
    return doc


def compare(failing, ledger):
    known = {e["id"]: e for e in ledger["failures"]}
    new = sorted(i for i in failing if i not in known)
    hit = sorted(i for i in failing if i in known)
    absent = sorted(i for i in known if i not in failing)
    return new, [known[i] for i in hit], absent


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) < 2 or argv[0] != "check":
        print(__doc__)
        return 2
    ledger_path = LEDGER
    if "--ledger" in argv:
        ledger_path = Path(argv[argv.index("--ledger") + 1])
    failing = parse(Path(argv[1]).read_text(encoding="utf-8", errors="replace"))
    new, hit, absent = compare(failing, load_ledger(ledger_path))
    print(f"NEW ({len(new)}): the run's own failures")
    for i in new:
        print(f"  {failing[i]} {i}")
    print(f"KNOWN ({len(hit)}): in the ledger (still failing; never a pass)")
    for e in hit:
        print(f"  {e['id']}  [{e['owner']}] {e['cause']}")
    print(f"ABSENT ({len(absent)}): ledger ids not failing here (fixed, or not run)")
    for i in absent[:20]:
        print(f"  {i}")
    if len(absent) > 20:
        print(f"  ... {len(absent) - 20} more (a partial run leaves most of the ledger ABSENT)")
    return 1 if new else 0


if __name__ == "__main__":
    sys.exit(main())
