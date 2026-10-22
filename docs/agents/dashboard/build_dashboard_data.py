"""Build the dashboard datasets that come from the board files.

usage: python3 -I build_dashboard_data.py <docs/agents dir> <out dir> [<board commit>]

Reads BOARD.md (and BOARD_ARCHIVE.md), PLAN.md, SCOREBOARD.md, OWNER_QUESTIONS.md, RUN_LOG.md (+ archive) and RUN_LEDGER.md;
writes tasks.json, milestones.json, targets.json, indicators.json (WORKFLOW_CONTROLS section 6),
owner_questions.json. Stdlib only. Nothing here is estimated: a value the board does not state is written as null.
The agents table (agents.json) and refresh.json are written by the refresher from list_triggers and the clock.
"""
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

SRC, OUT = Path(sys.argv[1]), Path(sys.argv[2])
COMMIT = sys.argv[3] if len(sys.argv) > 3 else ""
OUT.mkdir(parents=True, exist_ok=True)

ALSENAN, APT, ENGINE = "Alsenan Chalet", "Apartment (development project 2)", "Engine (all projects)"


def cells(line):
    parts = [c.strip() for c in line.strip().strip("|").split("|")]
    return parts


def project_of(text):
    t = text.lower()
    if "villa 2" in t or "development project 2" in t or "apartment" in t:
        return APT
    if "alsenan" in t or "p7757" in t or "st7757" in t or "real plan" in t or "real drawing" in t:
        return ALSENAN
    return ENGINE


def agent_of(status, branch):
    m = re.search(r"worker\s*(\d)", status, re.I)
    if m:
        return "Worker " + m.group(1)
    if re.search(r"verifier", status, re.I):
        return "Verifier"
    if re.search(r"\blead\b", status, re.I):
        return "Lead"
    if re.search(r"owner session", status, re.I):
        return "Owner session"
    return ""


# ---- tasks ------------------------------------------------------------------------------------------------------
tasks = []
BOARD_LINES = (SRC / "BOARD.md").read_text().splitlines()
if (SRC / "BOARD_ARCHIVE.md").exists():  # closed rows moved out of BOARD.md by the Lead (2026-10-20)
    BOARD_LINES += (SRC / "BOARD_ARCHIVE.md").read_text().splitlines()
for line in BOARD_LINES:
    if not re.match(r"\|\s*T-\d", line):
        continue
    c = cells(line)
    if len(c) < 5:
        continue
    tid, gate, trade, task, status = c[:5]
    branch = c[5] if len(c) > 5 else ""
    word = re.match(r"[A-Z][A-Z-]+", status)
    st = word.group(0) if word else status.split()[0]
    short = re.split(r"(?<=[.:;])\s", task)[0][:160]
    tasks.append({
        "id": tid, "project": project_of(task + " " + trade), "gate": gate, "trade": trade, "task": short,
        "status": st, "agent": agent_of(status, branch), "branch": branch if branch.startswith("agents/") else "",
        "note": status[:140],
    })
(OUT / "tasks.json").write_text(json.dumps(tasks, indent=1, ensure_ascii=False))

# ---- milestones -------------------------------------------------------------------------------------------------
GATE_OF = {"M1": "0", "M2": "1", "M3": "2", "M4": "3", "M5": "4"}
today = datetime.now(timezone.utc).date()
ms = []
for line in (SRC / "PLAN.md").read_text().splitlines():
    m = re.match(r"\|\s*(M\d)\s*\|", line)
    if not m:
        continue
    c = cells(line)
    mid, by, gate, exit_, status = c[:5]
    g = GATE_OF.get(mid, gate)
    mine = [t for t in tasks if t["gate"] == g]
    done = sum(t["status"] in ("MERGED", "DONE") for t in mine)
    row = {
        "id": mid, "due": by, "gate": g, "exit": exit_[:220], "status_note": status[:220],
        "tasks_total": len(mine), "tasks_done": done,
        "tasks_ready": sum(t["status"] == "READY" for t in mine),
        "tasks_active": sum(t["status"] in ("CLAIMED", "VERIFYING") for t in mine),
        "tasks_todo": sum(t["status"] == "TODO" for t in mine),
        "tasks_queued": sum(t["status"] == "QUEUED" for t in mine),
        "days_left": (datetime.strptime(by, "%Y-%m-%d").date() - today).days,
    }
    low = status.lower()
    row["state"] = "late" if "late" in low else ("done" if low.startswith("done") else (
        "not started" if "not started" in low else "on track"))
    ms.append(row)
(OUT / "milestones.json").write_text(json.dumps(ms, indent=1, ensure_ascii=False))

# ---- targets (scoreboard) ---------------------------------------------------------------------------------------
tg = []
in_table = False
for line in (SRC / "SCOREBOARD.md").read_text().splitlines():
    if line.startswith("| Trade"):
        in_table = True
        continue
    if in_table and line.startswith("|---"):
        continue
    if in_table and line.startswith("|"):
        c = cells(line)
        trade, unit, cov, silent, wape, signed, target, source, status = c[:9]
        measured = status.lower().startswith("measured")
        tg.append({"project": ALSENAN, "trade": trade, "unit": unit, "target": target,
                   "current": signed if signed != "-" else (wape if wape != "-" else None),
                   "basis": "measured" if measured else ("reported, not measured" if "reported" in status.lower()
                                                         else "not measured"),
                   "source": source})
    elif in_table:
        in_table = False
# Development project 2 covers finishes only (PLAN.md); nothing is measured on it yet.
for trade, unit, target in (("Floor area", "m2", "<= 1-2 %, no room lost"), ("Plaster, paint", "m2", "<= 3 %"),
                            ("Wall tile", "m2", "<= 3 %"), ("Wet-area waterproofing", "m2", "<= 2-3 %"),
                            ("Doors, windows", "nr", "exact count")):
    tg.append({"project": APT, "trade": trade, "unit": unit, "target": target, "current": None,
               "basis": "not measured", "source": "PLAN.md development set 1b"})
(OUT / "targets.json").write_text(json.dumps(tg, indent=1, ensure_ascii=False))

# ---- owner questions --------------------------------------------------------------------------------------------
text = (SRC / "OWNER_QUESTIONS.md").read_text()
open_part = re.search(r"^## Open\s*(.*?)^## Answered", text, re.S | re.M)
qs = []
if open_part:
    for m in re.finditer(r"^### (Q-\d+)\s+(.*?)\n(.*?)(?=^### |\Z)", open_part.group(1), re.S | re.M):
        inv = re.search(r"^STATUS[^\n]*INVESTIGATION (T-\d+)", m.group(3), re.M)  # reopened as a team task (owner 2026-10-22)
        qs.append({"id": m.group(1), "title": m.group(2).strip()[:140], "text": " ".join(m.group(3).split())[:500],
                   "waits_on": ("team investigation " + inv.group(1)) if inv else "owner decision"})
# an empty file cannot be read by the dashboard, so "nothing open" is one placeholder row with id "-"
written = qs or [{"id": "-", "title": "No open questions", "text": ""}]
(OUT / "owner_questions.json").write_text(json.dumps(written, indent=1, ensure_ascii=False))

# ---- indicators (WORKFLOW_CONTROLS_2026-10-21.md section 6) -----------------------------------------------------
# Five indicators, each from its own source. A value the sources do not measure is "NOT YET MEASURED", never estimated.
NYM = "NOT YET MEASURED"
now = datetime.now(timezone.utc)
status_of = {t["id"]: t["status"] for t in tasks}
sb2 = status_of.get("T-132", "not on the board")
ind = []
# SCOREBOARD v2 (T-132): the newest "## SCOREBOARD v2 <time>" heading and the table under it (format fixed on the board,
# owner session 2026-10-22 07:30). Indicators 1, 2 and 4 come from it; without it they stay NOT YET MEASURED.
sbt = (SRC / "SCOREBOARD.md").read_text()
v2 = re.search(r"^## SCOREBOARD v2 ([^\n]*)\n(.*?)(?=^## |\Z)", sbt, re.S | re.M)
v2rows, v2when = [], ""
if v2:
    v2when = v2.group(1).strip()
    head = None
    for line in v2.group(2).splitlines():
        if not line.startswith("|"):
            if head is not None:
                break  # the first table under the heading only
            continue
        if line.startswith("|---"):
            continue
        c = cells(line)
        if head is None:
            head = c
            continue
        v2rows.append(dict(zip(head, c)))


def per_trade(col):
    def base(r):
        b = r.get("Baseline", "").split(" ")[0]
        return "released" if b == "A" else b.replace("ARCH_TAKEOFF_", "")
    vals = [(r.get("Trade", ""), r.get("Unit", ""), base(r), r.get(col, "")) for r in v2rows]
    vals = [v for v in vals if v[3] and v[3] != NYM and v[3] != "-"]
    return "; ".join(t + " (" + u + ", " + b + ") " + x for t, u, b, x in vals)


for name, col, what in (("BOQ coverage", "Coverage %", "reference lines covered, by trade and unit"),
                        ("Independent verification share", "Verified share %",
                         "reference lines the checker re-measured from the drawing, by trade and unit")):
    got = per_trade(col) if v2rows else ""
    ind.append({"indicator": name, "value": got or NYM, "unit": "% by trade and unit" if got else "",
                "basis": "measured" if got else NYM,
                "source": ("SCOREBOARD v2 " + v2when) if v2rows else "SCOREBOARD v2 (T-132, status " + sb2 + ")",
                "detail": what})

pk = [t for t in tasks if "lane I" in t["trade"] and "integration (" in t["trade"]]
merged = [t["id"] for t in pk if t["status"] in ("MERGED", "DONE")]
waiting = [t["id"] + " " + t["status"] for t in pk if t["status"] not in ("MERGED", "DONE")]
ind.append({"indicator": "Integration into V3.0", "value": str(len(merged)) if pk else NYM,
            "unit": "packages merged through Gate B", "basis": "measured" if pk else NYM,
            "source": "BOARD.md lane I integration rows",
            "detail": ("merged: " + ", ".join(merged) if merged else "none merged")
                      + ("; open: " + ", ".join(waiting) if waiting else "")})
held = per_trade("Held or UNKNOWN") if v2rows else ""
ind.append({"indicator": "Unresolved scope", "value": held or NYM, "unit": "HELD + UNKNOWN by trade and unit" if held else "",
            "basis": "measured" if held else NYM,
            "source": ("SCOREBOARD v2 " + v2when) if v2rows else "HELD + UNKNOWN by trade and unit (SCOREBOARD v2, T-132, status " + sb2 + ")",
            "detail": "held is never shown as 0"})

# run reliability, last 48 h: STARTED lines and whether the same agent wrote a final line before its next start
logs = [SRC / "RUN_LOG.md"] + sorted((SRC / "archive").glob("RUN_LOG_*.md"))
ev = []
for f in logs:
    for line in f.read_text().splitlines():
        m = re.match(r"-\s*(\d{4}-\d{2}-\d{2})[ T](\d{2}:\d{2})(?::\d{2})?(?: UTC|Z)?\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|", line)
        if not m:
            continue
        at = datetime.strptime(m.group(1) + " " + m.group(2), "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        if (now - at).total_seconds() <= 48 * 3600:
            ev.append((at, m.group(3), m.group(4).split()[0].upper()))
ev.sort()
started = closed = 0
for i, (at, agent, word) in enumerate(ev):
    if word != "STARTED":
        continue
    started += 1
    for at2, agent2, word2 in ev[i + 1:]:
        if agent2 == agent:
            closed += word2 != "STARTED"
            break
ledger = (SRC / "RUN_LEDGER.md").read_text() if (SRC / "RUN_LEDGER.md").exists() else ""
tot = re.findall(r"\*\*Totals, (\d+) slots[^*]*\*\*\s*\n\s*\n\|[^\n]*\n\|[^\n]*\n\| SUCCESS \| (\d+) \|", ledger)
last = ("last daily ledger: " + tot[-1][1] + " of " + tot[-1][0] + " slots SUCCESS") if tot else "no daily ledger total"
ind.append({"indicator": "Autonomous run reliability", "value": (str(round(100 * closed / started)) + " %") if started else NYM,
            "unit": "runs with STARTED + final line, last 48 h", "basis": "measured" if started else NYM,
            "source": "RUN_LOG.md + archive, RUN_LEDGER.md",
            "detail": str(closed) + " of " + str(started) + " started runs closed; " + last
                      + "; slots with no line at all are counted only in the ledger"})
(OUT / "indicators.json").write_text(json.dumps(ind, indent=1, ensure_ascii=False))

# ---- performance, before / after (owner approval 2026-10-22 "faster execution", WORKFLOW_CONTROLS section 10) ---------
# BEFORE = the 24 h before the change, AFTER = from the change to now, both scaled to a day. Events come from the final
# RUN_LOG lines only: a worker line whose task field says READY is a completion; the task ids in a Verifier line's task
# field are its verdicts (MERGED, or REJECTED when the id follows the word REJECTED before any later MERGED).
CUT = datetime(2026, 10, 22, 15, 0, tzinfo=timezone.utc)
TID = r"T-\d+(?:\s*r\d+)?"


def norm(t):
    return re.sub(r"\s+", " ", t)


finals = []  # (time, agent, word, task field, message)
for f in logs:
    for line in f.read_text().splitlines():
        m = re.match(r"-\s*(\d{4}-\d{2}-\d{2})[ T](\d{2}:\d{2})(?::\d{2})?(?: UTC|Z)?\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|"
                     r"\s*([^|]*?)\s*\|(.*)", line)
        if m:
            at = datetime.strptime(m.group(1) + " " + m.group(2), "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            finals.append((at, m.group(3), m.group(4).split()[0].upper().strip("(),"), m.group(5), m.group(6)))
finals.sort(key=lambda e: e[0])
ready_at, verdicts = {}, []  # task id -> latest completion time; (time, id, MERGED / REJECTED)
for at, agent, word, field, msg in finals:
    if agent.startswith("Worker") and word in ("SUCCESS", "OK") and "READY" in field:
        for tid in re.findall(TID + r"(?=[^|]*?READY)", field):
            ready_at[norm(tid)] = at
    if agent == "Verifier" and word in ("SUCCESS", "OK", "BLOCKED", "INCOMPLETE"):
        for tid in dict.fromkeys(norm(t) for t in re.findall(TID, field)):
            pos = msg.find(tid.split(" ")[0])
            before = msg[:pos] if pos >= 0 else ""
            r, g = before.rfind("REJECT"), before.rfind("MERGED")
            kind = "REJECTED" if r > g else ("MERGED" if g > r else "CHECKED")  # CHECKED: no merge / reject word before it
            verdicts.append((at, tid, kind, ready_at.get(tid) or ready_at.get(tid.split(" ")[0])))
runs = [(at, agent, word) for at, agent, word, _, _ in finals]


def window(lo, hi):
    days = max((hi - lo).total_seconds() / 86400, 1e-9)
    comp = [1 for at, agent, word, field, _ in finals if lo <= at < hi and agent.startswith("Worker")
            and word in ("SUCCESS", "OK") and "READY" in field]
    ver = [v for v in verdicts if lo <= v[0] < hi]
    merged = [v for v in ver if v[2] == "MERGED"]
    rejected = [v for v in ver if v[2] == "REJECTED"]
    lag = [(v[0] - v[3]).total_seconds() / 3600 for v in ver if v[3] and v[3] <= v[0]]
    st = [r for r in runs if lo <= r[0] < hi and r[2] == "STARTED"]
    ok = [r for r in runs if lo <= r[0] < hi and r[2] in ("SUCCESS", "OK")]
    bad = [r for r in runs if lo <= r[0] < hi and r[2] in ("BLOCKED", "FAILED", "INCOMPLETE")]
    return {"from": lo.strftime("%Y-%m-%d %H:%M"), "to": hi.strftime("%Y-%m-%d %H:%M"), "days": round(days, 2),
            "completed_per_day": round(len(comp) / days, 1), "verdicts_per_day": round(len(ver) / days, 1),
            "verified_merged_per_day": round(len(merged) / days, 1),
            "rejected": len(rejected), "checked_other": len(ver) - len(merged) - len(rejected),
            "hours_completion_to_verdict_avg": round(sum(lag) / len(lag), 1) if lag else NYM,
            "runs_started": len(st), "runs_success": len(ok), "runs_failed_or_blocked": len(bad),
            "runs_started_without_final": max(len(st) - len(ok) - len(bad), 0)}


# backlog now: READY rows, age from the worker's READY line (or the time in the status cell)
backlog = []
for line in BOARD_LINES:
    c = cells(line) if re.match(r"\|\s*T-\d", line) else []
    if len(c) > 4 and c[4].startswith("READY"):
        tid = c[0] + (" " + re.search(r"\b(r\d+)\b", c[4]).group(1) if re.search(r"^READY\s*(\[[^\]]*\]\s*)*r\d+", c[4]) else "")
        at = ready_at.get(tid) or ready_at.get(c[0])
        if not at:
            m = re.search(r"(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}) UTC\)", c[4])
            at = datetime.strptime(m.group(1) + " " + m.group(2), "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc) if m else None
        backlog.append({"id": tid, "gate_b": "Gate B" in c[4],
                        "age_h": round((now - at).total_seconds() / 3600, 1) if at else None})
ages = [b["age_h"] for b in backlog if b["age_h"] is not None]
owner_blocked = [t["id"] for t in tasks if t["status"] not in ("MERGED", "DONE", "SUPERSEDED", "REJECTED")
                 and re.search(r"owner decision|waits? (?:on|for) the owner|BLOCKED \(owner", t["note"], re.I)]
owner_decisions_open = [q["id"] for q in qs if q["waits_on"] == "owner decision"]
perf = {
    "change": CUT.strftime("%Y-%m-%d %H:%M UTC") + " (one extra Checker run a day, overlap guard, batching; WORKFLOW_CONTROLS section 10)",
    "before": window(CUT.replace(day=CUT.day - 1), CUT),
    "after": window(CUT, now) if now > CUT else NYM,
    "backlog_now": len(backlog), "backlog_oldest_h": max(ages) if ages else None, "backlog": backlog,
    "verification_to_integration": NYM + " (needs 'integrates: T-...' in each Gate B package row, section 10 rule 6)",
    "owner_blocked_tasks": owner_blocked, "owner_decisions_open": owner_decisions_open,
    "team_investigations": [q["id"] + " " + q["waits_on"] for q in qs if q["waits_on"] != "owner decision"],
    "scope_and_verified_coverage": {"coverage": per_trade("Coverage %") or NYM,
                                    "verified_share": per_trade("Verified share %") or NYM,
                                    "source": ("SCOREBOARD v2 " + v2when) if v2rows else NYM},
}
(OUT / "performance.json").write_text(json.dumps(perf, indent=1, ensure_ascii=False))

print(json.dumps({"tasks": len(tasks), "milestones": len(ms), "targets": len(tg), "open_questions": len(qs),
                  "indicators": len(ind), "backlog": len(backlog), "board_commit": COMMIT}))
