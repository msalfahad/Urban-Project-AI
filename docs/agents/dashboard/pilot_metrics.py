"""Pilot metrics with fixed denominators (owner 2026-10-23: accelerated-schedule pilot, reproducible baseline).

usage: python3 -I pilot_metrics.py <docs/agents dir> <window start UTC> <window end UTC> [--json <out file>]
       times as YYYY-MM-DDTHH:MM (UTC)

Every number is computed from the board files only (RUN_LOG.md + archive, BOARD.md + BOARD_ARCHIVE.md, SCOREBOARD.md);
nothing is estimated, a value the files do not give is "NOT YET MEASURED". Denominators, per agent and window:
  slots     scheduled fires from SCHEDULES below (the cron in force at each moment)
  started   STARTED lines;   closed: final lines (any word but STARTED) of that agent
  success   final SUCCESS / OK lines that name work (a task id or a verdict)
  idle      IDLE / NO-CLAIM lines and SUCCESS lines that name no task ("none")
  failed    BLOCKED / FAILED / INCOMPLETE final lines;  unclosed: STARTED with no final line before the agent's next STARTED
Engineering outcomes (primary): verified reference lines (SCOREBOARD v2 "Verified share" n / d, newest section at or
before the window end), checker-verified pieces integrated into the V3.0 candidate (inputs named under "integrates" in
Gate B package rows MERGED in the window), integration latency (package merge time minus each input's merge time),
verdicts and rejection share, READY -> verdict hours, READY queue age at the window end.
"""
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

UTC = timezone.utc
TID = r"T-\d+"
STAMP = re.compile(r"-\s*(\d{4}-\d{2}-\d{2})[ T](\d{2}:\d{2})(?::\d{2})?(?: UTC|Z)?\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|(.*)")


def t(s):
    return datetime.strptime(s.replace("T", " ")[:16], "%Y-%m-%d %H:%M").replace(tzinfo=UTC)


# cron history per agent: (in force from, minute, hours). Hours are explicit lists in UTC.
EVERY = list(range(24))
ODD = list(range(1, 24, 2))
EVEN = list(range(0, 24, 2))
SCHEDULES = {
    "Lead": [(t("2026-10-01T00:00"), 9, list(range(0, 24, 4)))],
    "Worker 1": [(t("2026-10-01T00:00"), 19, EVEN)],
    "Worker 2": [(t("2026-10-01T00:00"), 39, ODD)],
    "Worker 3": [(t("2026-10-01T00:00"), 59, EVEN)],
    "Verifier": [(t("2026-10-01T00:00"), 49, ODD), (t("2026-10-22T15:07"), 49, sorted(ODD + [16]))],
}
PILOT_FILE = "PILOT_SCHEDULE.json"  # written by the main chat when the pilot starts: {"agent": [[from, minute, [hours]]]}


def load_schedules(src):
    sched = {a: list(v) for a, v in SCHEDULES.items()}
    p = src / "dashboard" / PILOT_FILE
    if p.exists():
        for a, rows in json.loads(p.read_text()).items():
            sched.setdefault(a, []).extend((t(f), m, h) for f, m, h in rows)
    for a in sched:
        sched[a].sort(key=lambda r: r[0])
    return sched


def slots(rows, lo, hi):
    n, cur = 0, lo.replace(minute=0, second=0, microsecond=0)
    while cur < hi:
        # the cron in force at the moment it would fire (a schedule change inside an hour applies from its own time)
        active = [r for r in rows if r[0] <= cur.replace(minute=r[1])]
        if active:
            _, minute, hours = active[-1]
            fire = cur.replace(minute=minute)
            if cur.hour in hours and lo <= fire < hi:
                n += 1
        cur += timedelta(hours=1)
    return n


def events(src):
    out = []
    for f in [src / "RUN_LOG.md"] + sorted((src / "archive").glob("RUN_LOG_*.md")):
        for line in f.read_text().splitlines():
            m = STAMP.match(line)
            if m:
                out.append((t(m.group(1) + "T" + m.group(2)), m.group(3), m.group(4).split()[0].upper().strip("(),"),
                            m.group(5), m.group(6)))
    return sorted(set(out), key=lambda e: e[0])


def board_rows(src):
    lines = (src / "BOARD.md").read_text().splitlines()
    if (src / "BOARD_ARCHIVE.md").exists():
        lines += (src / "BOARD_ARCHIVE.md").read_text().splitlines()
    rows = {}
    for line in lines:
        if re.match(r"\|\s*T-\d", line):
            c = [x.strip() for x in line.strip().strip("|").split("|")]
            if len(c) > 4:
                rows.setdefault(c[0], c)
    return rows


def merged_at(cell):
    m = re.search(r"MERGED[^(]*\((?:verifier|checker)[^0-9]*(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2})", cell, re.I)
    return t(m.group(1) + "T" + m.group(2)) if m else None


def coverage(src, hi):
    text = (src / "SCOREBOARD.md").read_text()
    best = None
    for m in re.finditer(r"^## SCOREBOARD v2 ([^\n]*)\n(.*?)(?=^## |\Z)", text, re.S | re.M):
        when = re.match(r"(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2})", m.group(1))
        if when and t(when.group(1) + "T" + when.group(2)) <= hi and (best is None or t(when.group(1) + "T" + when.group(2)) > best[0]):
            best = (t(when.group(1) + "T" + when.group(2)), m.group(2))
    if not best:
        return "NOT YET MEASURED", []
    rows, head = [], None
    for line in best[1].splitlines():
        if not line.startswith("|"):
            if head:
                break
            continue
        if line.startswith("|---"):
            continue
        c = [x.strip() for x in line.strip("|").split("|")]
        if head is None:
            head = c
            continue
        r = dict(zip(head, c))
        nd = re.search(r"\((\d+) / (\d+)", r.get("Verified share %", ""))
        rows.append({"trade": r.get("Trade"), "unit": r.get("Unit"), "baseline": r.get("Baseline", "").split(" (")[0],
                     "verified": int(nd.group(1)) if nd else None, "of": int(nd.group(2)) if nd else None})
    return best[0].strftime("%Y-%m-%d %H:%M"), rows


def measure(src, lo, hi):
    ev = events(src)
    sched = load_schedules(src)
    agents = {}
    for a in sched:
        E = [e for e in ev if e[1] == a]
        win = [e for e in E if lo <= e[0] < hi]
        st = [e for e in win if e[2] == "STARTED"]
        fin = [e for e in win if e[2] != "STARTED"]
        unclosed = 0
        for s in st:
            nxt = [e for e in E if e[0] >= s[0] and e is not s]
            f = next((e for e in nxt if e[2] != "STARTED"), None)
            n = next((e for e in nxt if e[2] == "STARTED"), None)
            if not f or (n and n[0] < f[0]):
                unclosed += 1
        named = lambda e: bool(re.search(TID, e[3])) or e[1] == "Lead"
        idle = [e for e in fin if e[2] in ("IDLE", "NO-CLAIM") or (e[2] in ("SUCCESS", "OK") and not named(e))]
        succ = [e for e in fin if e[2] in ("SUCCESS", "OK") and named(e)]
        failed = [e for e in fin if e[2] in ("BLOCKED", "FAILED", "INCOMPLETE")]
        agents[a] = {"slots": slots(sched[a], lo, hi), "started": len(st), "closed": len(fin), "success": len(succ),
                     "idle": len(idle), "failed": len(failed), "unclosed": unclosed}
    # hand-ins and verdicts
    ready_at, verdicts = {}, []
    for at, agent, word, field, msg in ev:
        if agent.startswith("Worker") and word in ("SUCCESS", "OK") and "READY" in field:
            for tid in re.findall(TID + r"(?:\s*r\d+)?(?=[^|]*?READY)", field):
                ready_at[re.sub(r"\s+", " ", tid)] = at
        if agent == "Verifier" and word in ("SUCCESS", "OK", "BLOCKED") and lo <= at < hi:
            for tid in dict.fromkeys(re.sub(r"\s+", " ", x) for x in re.findall(TID + r"(?:\s*r\d+)?", field)):
                # newer form: the verdict follows the id in the task field ("T-193 Gate B MERGED e866..., T-208 MERGED ...")
                after = re.search(re.escape(tid.split(" ")[0]) + r"\b([^,;]*?)(?=,|;|\bT-\d|$)", field)
                seg = after.group(1) if after else ""
                if "REJECT" in seg or "MERGED" in seg:
                    kind = "REJECTED" if "REJECT" in seg else "MERGED"
                else:  # older form: "MERGED T-137 (...), T-111 (...); REJECTED T-138 (...)" in the message
                    pos = msg.find(tid.split(" ")[0])
                    before = msg[:pos] if pos >= 0 else ""
                    r, g = before.rfind("REJECT"), before.rfind("MERGED")
                    kind = "REJECTED" if r > g else ("MERGED" if g > r else "CHECKED")
                verdicts.append((at, tid, kind, ready_at.get(tid) or ready_at.get(tid.split(" ")[0])))
    handins = sum(1 for at, a, w, f, m in ev if lo <= at < hi and a.startswith("Worker") and w in ("SUCCESS", "OK") and "READY" in f)
    merged = [v for v in verdicts if v[2] == "MERGED"]
    rejected = [v for v in verdicts if v[2] == "REJECTED"]
    waits = [(v[0] - v[3]).total_seconds() / 3600 for v in verdicts if v[3] and v[3] <= v[0]]
    # integration: Gate B packages merged in the window and the checker-verified inputs they integrate
    rows = board_rows(src)
    pk, lat, integrated = [], [], []
    for tid, c in rows.items():
        cell = " ".join(c[2:])
        if not re.search(r"lane I · integration\b", c[2]):  # Gate B package rows (board convention), not tools
            continue
        m_at = merged_at(c[4])
        if not m_at or not (lo <= m_at < hi):
            continue
        ins = []
        im = re.search(r"integrates:?\s*((?:T-\d+[ ,;and]*)+)", cell)
        if im:
            ins = re.findall(TID, im.group(1))
        pk.append(tid)
        for i in ins:
            ia = merged_at(rows.get(i, ["", "", "", "", ""])[4])
            if ia and ia <= m_at:
                lat.append((m_at - ia).total_seconds() / 3600)
                integrated.append(i)
    # queue at the window end: READY rows on the current board (only meaningful when hi is now)
    qwhen, cov = coverage(src, hi)
    days = (hi - lo).total_seconds() / 86400
    tot = {k: sum(a[k] for a in agents.values()) for k in ("slots", "started", "closed", "success", "idle", "failed", "unclosed")}
    return {
        "window": [lo.strftime("%Y-%m-%dT%H:%MZ"), hi.strftime("%Y-%m-%dT%H:%MZ")], "days": round(days, 3),
        "primary": {
            "verified_reference_lines": {"scoreboard_at": qwhen, "rows": cov},
            "verified_pieces_integrated": sorted(set(integrated)), "gate_b_packages_merged": sorted(pk),
            "integration_latency_h_avg": round(sum(lat) / len(lat), 1) if lat else "NOT YET MEASURED",
            "packages_naming_inputs": sum(1 for x in pk if re.search(r"integrates:?\s*T-\d", " ".join(rows[x][2:]))),
        },
        "secondary": {
            "handins": handins, "verdicts": len(verdicts), "merged": len(merged), "rejected": len(rejected),
            "rejection_share": round(len(rejected) / len(verdicts), 3) if verdicts else None,
            "ready_to_verdict_h_avg": round(sum(waits) / len(waits), 1) if waits else "NOT YET MEASURED",
            "per_day": {"handins": round(handins / days, 1), "merged": round(len(merged) / days, 1)},
        },
        "runs": {"agents": agents, "total": tot,
                 "closure_share": round(tot["closed"] / tot["started"], 3) if tot["started"] else None,
                 "success_per_slot": round(tot["success"] / tot["slots"], 3) if tot["slots"] else None,
                 "idle_share_of_closed": round(tot["idle"] / tot["closed"], 3) if tot["closed"] else None},
    }


if __name__ == "__main__":
    src = Path(sys.argv[1])
    res = measure(src, t(sys.argv[2]), t(sys.argv[3]))
    out = json.dumps(res, indent=1)
    if "--json" in sys.argv:
        Path(sys.argv[sys.argv.index("--json") + 1]).write_text(out)
    print(out)
