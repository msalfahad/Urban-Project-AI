"""T-512 (b), F-C-T508-1 / F-C-T458-2 class: an item code whose lines are ALL blank (no value, no bound) must print
HELD (n blank lines), never a number such as 'released 0.0'. AGENT_BRIEF 'HELD is never 0'; R-T499-1 (a subtotal over
any HELD row is HELD, the known part AT_LEAST, the held rows listed); UP-QTY-STATUS-001. Research checker only: it
edits no candidate method, hub, master or frozen file, and moves no quantity.

PHYSICAL MEANING. A code subtotal is the sum of the installed quantity of the lines under it. A blank line is a piece
whose quantity is not established (HELD / BLOCKED). With no established line the subtotal is UNKNOWN, not zero; '0.0'
asserts that the pieces measure nothing, which is a different (and wrong) quantity.

    view(entry)          one per-code totals record, of any of the three schemas met in the census:
                           CT   arch_v304.code_totals (every arch_v30xx RUN.json 'totals_moved_by_code' side):
                                lines, released, held_low, held_high, bounded_lines, blocked_lines
                           SB   t469_trade_scoreboard side()['by_item_code'] row:
                                released_qty, released_lines, held_lines, held_low, held_high, held_unknown_lines,
                                excluded_lines
                         -> {'lines', 'valued_lines', 'bounded_lines', 'blank_lines', 'printed_total' (the number
                            the source prints), 'status', 'released' (None when no valued line), 'held_range'
                            (None unless every held line is bounded), 'text'} by R-T499-1:
                              ALL_VALUED   every line valued                    -> the number, unchanged
                              PARTIAL      valued + held lines                  -> 'AT_LEAST x + HELD (n lines)'
                              HELD_BOUNDED no valued line, every one bounded    -> 'HELD range lo..hi (n lines)'
                              HELD         no valued line, any blank line       -> 'HELD (n blank lines)', never 0.0
    zero_printed(entry)  True when the source prints a number for a code with no valued line (the defect).
    census(paths)        rows (path, side, item_code|unit, lines, blank_lines, printed_total, status, defect) over
                         every committed research JSON that carries 'totals_moved_by_code' or 'by_item_code', and the
                         candidate line index (arch_v304.code_totals run on it).

    python3 -I research/agents_t512/t512_held_totals.py census [--md OUT.md]

No project, layer, room or element name is coded. A valued line of 0.0 is a valued line (counted valued), so a code
whose pieces truly measure nothing still prints 0.0.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

POLICY = "T512_HELD_TOTALS_VIEW_V1"
RULES = ("AGENT_BRIEF HELD is never 0", "R-T499-1", "UP-QTY-STATUS-001")
ALL_VALUED, PARTIAL, HELD_BOUNDED, HELD, NO_LINES = "ALL_VALUED", "PARTIAL", "HELD_BOUNDED", "HELD", "NO_LINES"


def _r(x, n=6):
    return None if x is None else round(float(x) + 0.0, n)


def schema_of(e):
    if "blocked_lines" in e and "bounded_lines" in e and "released" in e:
        return "CT"
    if "released_lines" in e and "held_lines" in e and "released_qty" in e:
        return "SB"
    raise ValueError(f"T-512: unknown totals schema {sorted(e)}")


def counts(e):
    """-> (lines, valued, bounded, blank, printed number) of one totals record (excluded lines left out)."""
    s = schema_of(e)
    if s == "CT":
        lines, bounded, blank = e["lines"], e["bounded_lines"], e["blocked_lines"]
        return lines, lines - bounded - blank, bounded, blank, e["released"]
    blank = e.get("held_unknown_lines", 0)
    held = e["held_lines"]
    return e["released_lines"] + held, e["released_lines"], held - blank, blank, e["released_qty"]


def view(e):
    lines, valued, bounded, blank, printed = counts(e)
    if min(lines, valued, bounded, blank) < 0 or valued + bounded + blank != lines:
        raise ValueError(f"T-512: inconsistent line counts {e}")
    lo, hi = e.get("held_low"), e.get("held_high")
    out = {"lines": lines, "valued_lines": valued, "bounded_lines": bounded, "blank_lines": blank,
           "printed_total": printed, "released": None, "held_range": None}
    if lines == 0:
        out.update(status=NO_LINES, text="no lines")
    elif valued == lines:
        out.update(status=ALL_VALUED, released=_r(printed), text=f"{_r(printed)}")
    elif valued:
        out.update(status=PARTIAL, released=_r(printed),
                   text=f"AT_LEAST {_r(printed)} + HELD ({lines - valued} lines: {bounded} bounded, {blank} blank)")
    elif blank == 0:
        out.update(status=HELD_BOUNDED, held_range=[_r(lo), _r(hi)],
                   text=f"HELD range {_r(lo)}..{_r(hi)} ({bounded} bounded lines)")
    else:
        out.update(status=HELD, text=f"HELD ({blank} blank lines" + (f", {bounded} bounded)" if bounded else ")"))
    if bounded and blank and valued:
        out["held_range"] = None          # a range over held lines is a range only when every held line is bounded
    elif bounded and not blank and valued:
        out["held_range"] = [_r(lo), _r(hi)]
    return out


def zero_printed(e):
    """the defect: the source prints a number as the total of a code with no valued line."""
    lines, valued, _, _, printed = counts(e)
    return lines > 0 and valued == 0 and printed is not None


def held_view(totals):
    """{key: totals record} (code_totals output) -> {key: view} (the export view of every code)."""
    return {k: (None if v is None else view(v)) for k, v in sorted(totals.items())}


def check(totals):
    """-> [key] of every code whose source total prints a number with no valued line."""
    return sorted(k for k, v in totals.items() if v is not None and zero_printed(v))


# ---------------------------------------------------------------- census
def index_lines(index):
    """the T-479 line index (class / net / bounds per line) -> pseudo BOQ lines for arch_v304.code_totals."""
    out = []
    for r in index["lines"]:
        if r["class"] == "EXCLUDED":
            ev, net, br = "EXCLUDED_WITH_REASON", None, None
        elif r["class"] == "RELEASED":
            ev, net, br = "MEASURED", r["measured_net"], None
        elif r.get("held_low") is not None and r.get("held_high") is not None:
            ev, net, br = "BOUNDED_EXPOSURE", None, {"low": r["held_low"], "high": r["held_high"]}
        else:
            ev, net, br = "BLOCKED_RFI", None, None
        out.append({"item_code": r["item_code"], "unit": r["unit"], "evidence_state": ev, "measured_net": net,
                    "bounded_range": br})
    return out


def _walk(o, path, found):
    if isinstance(o, dict):
        for k, v in o.items():
            p = f"{path}/{k}"
            if k == "totals_moved_by_code" and isinstance(v, dict):
                for code, sides in v.items():
                    for side, e in (sides or {}).items():
                        if isinstance(e, dict):
                            found.append((p, side, code, e))
            elif k == "by_item_code" and isinstance(v, list):
                for e in v:
                    found.append((p, "-", f"{e['item_code']}|{e['unit']}", e))
            else:
                _walk(v, p, found)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            _walk(v, f"{path}[{i}]", found)


def census_json(path):
    found = []
    _walk(json.loads(Path(path).read_text(encoding="utf-8")), "", found)
    rows = []
    for p, side, code, e in found:
        v = view(e)
        rows.append({"file": str(Path(path).relative_to(ROOT)) if Path(path).is_absolute() else str(path),
                     "where": p, "side": side, "code": code, "lines": v["lines"], "blank_lines": v["blank_lines"],
                     "bounded_lines": v["bounded_lines"], "printed_total": v["printed_total"],
                     "status": v["status"], "defect": zero_printed(e)})
    return rows


def census_index(index_path, moved_path=None):
    """arch_v304.code_totals (the candidate method path) on the committed candidate line index; with moved_path (a
    summary carrying the next version's totals_moved_by_code) the moved codes are replaced by the new side."""
    from engine.source import arch_v304 as A304
    idx = json.loads(Path(index_path).read_text(encoding="utf-8"))
    tot = A304.code_totals(index_lines(idx))
    label = idx.get("candidate_version")
    if moved_path:
        s = json.loads(Path(moved_path).read_text(encoding="utf-8"))
        for code, sides in s["totals_moved_by_code"].items():
            new = [v for k, v in sides.items() if k != "base"]
            if new and new[0] is not None:
                tot[code] = new[0]
            else:
                tot.pop(code, None)
        label = s.get("method", label)
    rows = []
    for code, e in sorted(tot.items()):
        v = view(e)
        rows.append({"file": "arch_v304.code_totals @ " + str(label), "where": "code_totals", "side": "-",
                     "code": code, "lines": v["lines"], "blank_lines": v["blank_lines"],
                     "bounded_lines": v["bounded_lines"], "printed_total": v["printed_total"],
                     "status": v["status"], "defect": zero_printed(e)})
    return rows


INDEX = ROOT / "research/agents_t508/out/LINE_INDEX_V3_0_55.json"
MOVED_V3056 = ROOT / "research/agents_t508/summary_t508.json"


def census(root=ROOT):
    rows = census_index(INDEX) + census_index(INDEX, MOVED_V3056)
    for p in sorted((root / "research").rglob("*.json")):
        t = p.read_text(encoding="utf-8", errors="replace")
        if '"totals_moved_by_code"' in t or '"by_item_code"' in t:
            rows += census_json(p)
    return rows


def summary(rows):
    by = {}
    for r in rows:
        k = (r["file"], r["where"].split("[")[0])
        b = by.setdefault(k, {"codes": 0, "all_held": 0, "defect": 0})
        b["codes"] += 1
        b["all_held"] += r["status"] in (HELD, HELD_BOUNDED)
        b["defect"] += r["defect"]
    return [{"file": f, "where": w, **v} for (f, w), v in sorted(by.items())]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=("census",))
    ap.add_argument("--md")
    ap.add_argument("--json")
    a = ap.parse_args(argv)
    rows = census()
    summ = summary(rows)
    print(json.dumps({"paths": len(summ), "codes": len(rows), "defects": sum(r["defect"] for r in rows)}))
    for s in summ:
        if s["defect"]:
            print(f"{s['defect']:4d} / {s['codes']:4d}  {s['file']}  {s['where']}")
    if a.json:
        Path(a.json).write_text(json.dumps({"summary": summ, "rows": rows}, indent=1, sort_keys=True) + "\n",
                                encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
