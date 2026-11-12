"""T-741: the T-734 roof-membrane downgrade (L-636fd3ff1784a12e653b) as a downgrade_add.py DRY RUN on V3.0.74.

    bash scripts/agent_env.sh run --tree engine research/agents_t741/t741_v3074_dryrun.py --out <board>/docs/agents/
        verdicts/V3.0.74/DOWNGRADES.json [--lines <private V3_0_74_BOQ_LINES.json> --run-token T --routine Checker
        --verdict-commit SHA]

Builds the downgrade-add arguments from the committed T-734 draft (research/agents_t734/out/T734_WP_H4_EVIDENCE.json:
line, state HELD, basis label, reason, the three evidence items) for the candidate ARCH_TAKEOFF_V3.0.74, and checks on
the committed V3.0.74 line index (research/agents_t717/out/LINE_INDEX_V3_0_74.json, T-717 run of record) that the line
is in that candidate, RELEASED, 115.832 m2: the engine quantity the record will bind. Without --lines it stops there
and prints the Checker's command (the full canonical lines are a private run output, never in the repository). With
--lines it runs downgrade_add.py --dry-run: the record is printed, nothing is written. A worker never issues it.
"""
from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import downgrade_add as D  # noqa: E402

CANDIDATE = "ARCH_TAKEOFF_V3.0.74"
LINE = "L-636fd3ff1784a12e653b"
RELEASED_M2 = 115.832
T734 = ROOT / "research/agents_t734/out/T734_WP_H4_EVIDENCE.json"
IDX74 = ROOT / "research/agents_t717/out/LINE_INDEX_V3_0_74.json"


def index_entry():
    idx = json.loads(IDX74.read_text(encoding="utf-8"))
    if idx.get("candidate_version") != CANDIDATE:
        raise SystemExit(f"{IDX74.name}: not {CANDIDATE}")
    hits = [x for x in idx["lines"] if x["line_id"] == LINE]
    if len(hits) != 1:
        raise SystemExit(f"{LINE}: not in {CANDIDATE} (a record on it would be refused)")
    e = hits[0]
    if (e["class"], e["unit"], e["measured_net"]) != ("RELEASED", "m2", RELEASED_M2):
        raise SystemExit(f"{LINE}: {e['class']} {e['measured_net']} {e['unit']} on {CANDIDATE}, not RELEASED "
                         f"{RELEASED_M2} m2: the T-734 evidence must be re-read before any record")
    return e


def draft_args(lines, out, *, run_token, routine, verdict_commit):
    dr = json.loads(T734.read_text(encoding="utf-8"))["roof"]["downgrade_record_draft"]
    if dr["line_ids"] != [LINE] or dr["state"] != "HELD" or dr["engine_qty_binding"] != RELEASED_M2:
        raise SystemExit("T-734 draft changed: re-read it")
    av = ["downgrade-add", "--lines", str(lines), "--candidate-version", CANDIDATE, "--line-ids", LINE,
          "--state", dr["state"], "--basis-label", dr["basis_label"], "--reason", dr["reason"]]
    for e in dr["evidence"]:
        av += ["--evidence", e]
    return av + ["--run-token", run_token, "--routine", routine, "--verdict-commit", verdict_commit,
                 "--out", str(out), "--dry-run"]


def main(argv=None):
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--out", required=True)
    ap.add_argument("--lines")
    ap.add_argument("--run-token", default="<checker run token>")
    ap.add_argument("--routine", default="Checker")
    ap.add_argument("--verdict-commit", default="<commit>")
    a = ap.parse_args(argv)
    e = index_entry()
    print(f"T741 V3.0.74 index: {LINE} {e['class']} {e['measured_net']} {e['unit']} ({e['item_code']}): the record "
          "binds this engine quantity and carries none of its own")
    av = draft_args(a.lines or "<private V3_0_74_BOQ_LINES.json>", a.out, run_token=a.run_token,
                    routine=a.routine, verdict_commit=a.verdict_commit)
    D.record_path(a.out)                      # the --out rule, refused here before anything else
    if not a.lines:
        print("T741 Checker command (dry run; drop --dry-run to issue):")
        print("bash scripts/agent_env.sh run --tree engine research/agents_t741/downgrade_add.py "
              + " ".join(shlex.quote(x) for x in av))
        return 0
    return D.main(av)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except D.Refused as exc:
        print(f"T741 REFUSED: {exc}", file=sys.stderr)
        sys.exit(2)
