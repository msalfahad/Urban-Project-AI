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
        qs.append({"id": m.group(1), "title": m.group(2).strip()[:140], "text": " ".join(m.group(3).split())[:500]})
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

print(json.dumps({"tasks": len(tasks), "milestones": len(ms), "targets": len(tg), "open_questions": len(qs),
                  "indicators": len(ind), "board_commit": COMMIT}))
