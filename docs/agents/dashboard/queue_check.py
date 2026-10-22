"""Board-to-agent-queue consistency check (owner 2026-10-22, after T-185 sat on the board without being worked).

usage: python3 -I queue_check.py <docs/agents dir> [--json <out file>]

Every actionable task row on BOARD.md must have a responsible agent, a place in that agent's executable queue, a clear
status, and, when it cannot start, a named dependency or blocker. The queue of a worker is the Lead's newest
"LANE ORDER" note (S = worker 1, A = worker 2, I = worker 3), with any newer owner-session "WORKER n takes T-xxx" put first.
READY rows belong to the Checker (it takes every READY row). Stdlib only; reads the board, writes nothing to it.
FLAG (exit code 1): a structural gap the Lead fixes (NOT_QUEUED, NO_AGENT, NO_BLOCKER, UNCLEAR_STATUS).
STALL_CHECK (owner 2026-10-22: an investigation trigger, never evidence of failure, exit code unchanged): the worker
finished more runs since the task got its place than its position, and at least one of those runs is not explained by
work ahead of it in the queue, rework (rN) or an owner-session priority. A task that names an open dependency
("after T-nnn", "waits for T-nnn") is WAITING and never a stall check.
"""
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

TID = r"T-\d+"
STAMP = r"(\d{4}-\d{2}-\d{2})[ T](\d{2}:\d{2})"
LANE_WORKER = {"S": "Worker 1", "A": "Worker 2", "I": "Worker 3"}
NEEDS_QUEUE = ("TODO", "CLAIMABLE", "REWORK")
DONE = ("MERGED", "DONE", "SUPERSEDED", "PAUSED")
MIN_REASON = 10  # a QUEUED / BLOCKED row must say why (dependency, blocker or the Lead's reason) in at least this many characters


def when(d, t):
    return datetime.strptime(d + " " + t, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)


def rows_of(board_lines):
    out = []
    for line in board_lines:
        if not re.match(r"\|\s*T-\d", line):
            continue
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(c) < 5:
            continue
        status = c[4]
        word = re.match(r"[A-Z][A-Z-]+", status)
        st = word.group(0) if word else (status.split()[0] if status else "")
        if st == "REJECTED" and re.search(r"rework\s+r\d+\s+CLAIMABLE|CLAIMABLE", status):
            st = "CLAIMABLE"
        lane = re.search(r"lane\s+([SAI])\b", c[2])
        out.append({"id": c[0], "lane": lane.group(1) if lane else "", "status": st, "note": status,
                    "checker": c[2].lower().startswith("checker")})
    return out


def queues_of(board_lines):
    """worker -> [task ids] from the newest Lead LANE ORDER note, then newer owner-session 'WORKER n takes' notes;
    placed -> {task id: time of the note that gave it its place} (runs are counted from that time)."""
    lead = []
    for line in board_lines:
        m = re.match(r"Lead " + STAMP + r"\b", line)
        if m and "LANE ORDER" in line:
            lead.append((when(m.group(1), m.group(2)), line))
    queues, since, placed = {w: [] for w in LANE_WORKER.values()}, None, {}
    if lead:
        since, text = max(lead, key=lambda x: x[0])
        seg = text[text.index("LANE ORDER"):]
        for lane, num, body in re.findall(r"\b([SAI])\s*\(worker\s*(\d)[^)]*\)\s*:\s*([^;]*)", seg):
            queues["Worker " + num] = list(dict.fromkeys(re.findall(TID, body)))
            placed.update({t: since for t in queues["Worker " + num]})
    owner = []
    for line in board_lines:
        m = re.match(r"OWNER SESSION " + STAMP, line)
        if m and not (since and when(m.group(1), m.group(2)) <= since):
            owner.append((when(m.group(1), m.group(2)), line))
    for at, line in sorted(owner):  # oldest first, so the newest owner note ends up first in the queue
        for num, tid in re.findall(r"WORKER\s*(\d)\s+takes\s+(" + TID + ")", line):
            q = queues["Worker " + num]
            queues["Worker " + num] = [tid] + [x for x in q if x != tid]
            placed[tid] = at
    return queues, since, placed


def finals(log_lines):
    """(time, worker, task field) of every finished worker run (final lines only, not STARTED)."""
    out = []
    for line in log_lines:
        m = re.match(r"-\s*" + STAMP + r"(?::\d{2})?(?: UTC|Z)?\s*\|\s*(Worker \d)\s*\|\s*([A-Z-]+)[^|]*\|\s*([^|]*)", line)
        if m and m.group(4) != "STARTED":
            out.append((when(m.group(1), m.group(2)), m.group(3), m.group(5)))
    return out


def check(board_lines, log_lines):
    rows = rows_of(board_lines)
    status_of = {r["id"]: r["status"] for r in rows}
    queues, since, placed = queues_of(board_lines)
    owner_placed = {t for t, at in placed.items() if since is None or at > since}
    runs = finals(log_lines)
    result = []
    for r in rows:
        st, flags, checks, agent, place = r["status"], [], [], "", ""
        if st in DONE or st == "REJECTED":
            continue
        if r["checker"]:
            agent, place = "Checker", "checker standing slot"
        elif st in ("READY", "VERIFYING"):
            agent, place = "Checker", "verifier queue (every READY row)"
        elif st == "CLAIMED" or st == "IN":
            m = re.search(r"worker\s*(\d)", r["note"], re.I)
            agent = ("Worker " + m.group(1)) if m else ""
            place = "claimed"
            if not agent:
                flags.append("NO_AGENT: claimed without a worker named")
        elif st in NEEDS_QUEUE:
            owners = [w for w, q in queues.items() if r["id"] in q]
            agent = owners[0] if owners else LANE_WORKER.get(r["lane"], "")
            if not owners:
                flags.append("NOT_QUEUED: in no worker's LANE ORDER" + (" (lane " + r["lane"] + " -> " + agent + ")" if agent else ""))
            else:
                pos = queues[agent].index(r["id"]) + 1
                place = agent + " position " + str(pos)
                t0 = placed.get(r["id"], since)
                mine = [f for at, w, f in runs if w == agent and at > t0]
                ahead = set(queues[agent][:pos - 1])
                unexplained = [f for f in mine if not (set(re.findall(TID, f)) & (ahead | owner_placed)
                                                      or re.search(r"\br\d+\b", f))]
                deps = [d for d in re.findall(r"(?:after|waits? (?:on|for))\s+(" + TID + ")", r["note"])
                        if status_of.get(d, "MERGED") not in DONE]
                if deps:
                    place += " (WAITING on " + ", ".join(deps) + ")"
                elif len(mine) > pos and unexplained:
                    checks.append("STALL_CHECK (investigate, not a failure): " + agent + " finished " + str(len(mine))
                                  + " runs since " + t0.strftime("%H:%M") + " UTC (position " + str(pos) + "), "
                                  + str(len(unexplained)) + " on work not ahead of it, not rework, not owner priority")
            if not agent:
                flags.append("NO_AGENT: no lane and no queue")
        elif st == "QUEUED" or st.startswith("BLOCKED"):
            agent = LANE_WORKER.get(r["lane"], "")
            place = "not yet actionable"
            if len(r["note"][len(st):].strip(" ()[]-:")) < MIN_REASON:
                flags.append("NO_BLOCKER: " + st + " without a named dependency or blocker")
        else:
            flags.append("UNCLEAR_STATUS: '" + st + "'")
        result.append({"id": r["id"], "status": st, "agent": agent, "queue": place, "flags": flags, "checks": checks})
    return result, queues, since


def main(argv):
    src = Path(argv[1])
    board = (src / "BOARD.md").read_text().splitlines()
    log = (src / "RUN_LOG.md").read_text().splitlines()
    res, queues, since = check(board, log)
    flagged = [r for r in res if r["flags"]]
    checked = [r for r in res if r["checks"]]
    print("queue note: " + (since.strftime("%Y-%m-%d %H:%M UTC") if since else "none") + "; "
          + "; ".join(w + ": " + ", ".join(q) for w, q in queues.items()))
    for r in res:
        tag = "FLAG " if r["flags"] else ("CHECK" if r["checks"] else "ok   ")
        print(tag + " " + r["id"] + " | " + r["status"] + " | " + (r["agent"] or "-") + " | " + (r["queue"] or "-")
              + ((" | " + "; ".join(r["flags"] + r["checks"])) if r["flags"] or r["checks"] else ""))
    print("queue check: " + str(len(res)) + " actionable rows, " + str(len(flagged)) + " flagged, "
          + str(len(checked)) + " stall checks to investigate")
    if "--json" in argv:
        Path(argv[argv.index("--json") + 1]).write_text(json.dumps(res, indent=1, ensure_ascii=False))
    return 1 if flagged else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
