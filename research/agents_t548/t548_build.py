"""T-548: build the reconciled-quantities statement from the merged reconciliation reports (no private input).

  python3 -I research/agents_t548/t548_build.py --write   # write out/
  python3 -I research/agents_t548/t548_build.py --check   # rebuild and compare with out/ (exit 1 on a difference)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import adapters as A  # noqa: E402
import statement as S  # noqa: E402

OUT = HERE / "out"
JSON_OUT = OUT / "RECONCILED_STATEMENT_T548.json"
MD_OUT = OUT / "RECONCILED_STATEMENT_T548.md"
REPORTS_COVERED = ["T-541", "T-534"]
REPORTS_PENDING = ["T-543", "T-545", "T-546", "T-547"]  # add an adapter when each merges


def build() -> dict:
    secs, prov = A.all_sections()
    st = S.build_statement(secs)
    st["provenance"] = prov
    st["reports_covered"] = REPORTS_COVERED
    st["reports_pending"] = REPORTS_PENDING
    return json.loads(json.dumps(st, sort_keys=True))


def main(argv: list[str]) -> int:
    st = build()
    md = ("# T-548 reconciled-quantities statement (generated; reference - engine, + = in the reference only)\n\n"
          + S.to_markdown(st)
          + f"\nReports covered: {', '.join(REPORTS_COVERED)}; pending: {', '.join(REPORTS_PENDING)}.\n")
    if "--write" in argv:
        OUT.mkdir(exist_ok=True)
        JSON_OUT.write_text(json.dumps(st, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        MD_OUT.write_text(md, encoding="utf-8")
    if "--check" in argv:
        old = json.loads(JSON_OUT.read_text(encoding="utf-8"))
        if old != st or MD_OUT.read_text(encoding="utf-8") != md:
            print("T-548 statement differs from out/")
            return 1
        print("T-548 statement reproduces")
    if not argv:
        print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
