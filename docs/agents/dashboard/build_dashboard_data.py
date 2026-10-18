"""Build the dashboard datasets that come from the board files.

usage: python3 -I build_dashboard_data.py <docs/agents dir> <out dir> [<board commit>]

Reads BOARD.md, PLAN.md, SCOREBOARD.md and OWNER_QUESTIONS.md; writes tasks.json, milestones.json, targets.json,
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
for line in (SRC / "BOARD.md").read_text().splitlines():
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

print(json.dumps({"tasks": len(tasks), "milestones": len(ms), "targets": len(tg), "open_questions": len(qs),
                  "board_commit": COMMIT}))
