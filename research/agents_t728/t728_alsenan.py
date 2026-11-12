"""T-728 BEAD LEDGER RESTATEMENT on ARCH_TAKEOFF_V3.0.72 (development villa; method R-T728-1 in t728_rules.py, every
villa). Research only: no candidate, released, rule / knowledge version, registry or hub file is touched; no quantity
is measured, changed or wired; no drawing is opened.

The 116 B4-09 bead rows that T-723 flagged RULING_RESTATE (Lead ruling 2026-11-11 16:25, F-T705-1) are restated by line
id on V3.0.72: for each row the host line, the host's state on V3.0.72 (RELEASED / BOUNDED / BLANK), the host's cause
(from the merged hold census that last set the host's index entry), and the bead after-state by the R-T728-1 table.
Every input is a merged repository file, sha256-pinned below.

Rebuild:  bash scripts/agent_env.sh run --tree task-T-728 research/agents_t728/t728_alsenan.py --write
Check:    bash scripts/agent_env.sh run --tree task-T-728 research/agents_t728/t728_alsenan.py --check
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import t728_rules as R  # noqa: E402

SCHEMA = "URBAN_T728_BEAD_RESTATEMENT_V1"
CANDIDATE = "ARCH_TAKEOFF_V3.0.72"
LEDGER = "research/agents_t697/out/T697_BEAD_LEDGER.csv"
T723 = "research/agents_t723/out/T723_ROWS.csv"
IDX72 = "research/agents_t703/out/LINE_INDEX_V3_0_72.json"
IDX71 = "research/agents_t704/out/LINE_INDEX_V3_0_71.json"
IDX69 = "research/agents_t687/out/LINE_INDEX_V3_0_69.json"
IDX64 = "research/agents_t668/out/LINE_INDEX_V3_0_64.json"
T676 = "research/agents_t676/out/T676_PLASTER_PAINT_CENSUS.json"
T687 = "research/agents_t687/summary_t687.json"
PINS = [LEDGER, T723, IDX72, IDX71, IDX69, IDX64, T676, T687]
OUT_JSON = HERE / "out" / "T728_BEAD_RESTATEMENT.json"
OUT_CSV = HERE / "out" / "T728_BEAD_ROWS.csv"
EXPECTED_ROWS = 116
CSV_COLS = ["edge_id", "scope", "floor", "room", "class", "count", "hub", "pending", "host_line", "host_code",
            "host_element", "host_state", "host_bound", "host_cause_source", "ledger_status", "ledger_form", "ledger_m",
            "ledger_low", "ledger_high", "drawing_band", "bead_state", "value", "low", "high", "ledger_ref",
            "owner_trade", "cause"]


def _p(rel):
    return ROOT / rel


def sha(rel):
    return hashlib.sha256(_p(rel).read_bytes()).hexdigest()


def jload(rel):
    return json.loads(_p(rel).read_text(encoding="utf-8"))


def index(rel):
    return {ln["line_id"]: ln for ln in jload(rel)["lines"]}


def num(s):
    s = (s or "").strip()
    return None if s == "" else float(s)


def ruling_rows():
    """the T-723 rows of piece T-697 flagged RULING_RESTATE (edge id -> T-723 row)."""
    out = {}
    with _p(T723).open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["piece"] == "T-697" and "RULING_RESTATE" in r["flags"]:
                eid = r["row"].split(":", 1)[1]
                if eid in out:
                    raise R.BeadStateError(f"T-723 lists {eid} twice")
                out[eid] = r
    return out


def host_causes(i72, i69, i64):
    """host line id -> (cause text, source) from the census that last set its index entry."""
    census = {e["line_id"]: e for e in jload(T676)["entries"]}
    t687 = {r["line_id"]: r for r in jload(T687)["rows"]}
    out = {}
    for lid in i72:
        e = census.get(lid)
        if lid in i64 and i64[lid] == i72[lid] and e:
            ref = f" [{e['designer_ref']}]" if e.get("designer_ref") else ""
            out[lid] = (f"{e['class']}{ref}: {e['cause']}", "T-676 hold census on V3.0.64 (entry unchanged to V3.0.72)")
        elif lid in i69 and i69[lid] == i72[lid] and lid in t687 and e:
            a = t687[lid]["after"]
            out[lid] = (f"{a['state']} {a['low']} .. {a['high']} (T-687 wiring of T-680 shaft round 2, V3.0.69); "
                        f"held items as T-676 {e['class']}: {e['cause']}",
                        "T-687 restatement on V3.0.69 (entry unchanged to V3.0.72) + T-676 cause")
    return out


def build():
    i72, i71, i69, i64 = index(IDX72), index(IDX71), index(IDX69), index(IDX64)
    rr = ruling_rows()
    if len(rr) != EXPECTED_ROWS:
        raise R.BeadStateError(f"T-723 RULING_RESTATE rows {len(rr)} != {EXPECTED_ROWS}")
    causes = host_causes(i72, i69, i64)
    rows = []
    with _p(LEDGER).open(encoding="utf-8") as f:
        ledger = {r["edge_id"]: r for r in csv.DictReader(f)}
    for eid in sorted(rr):
        t = rr[eid]
        b = ledger.get(eid)
        if b is None:
            raise R.BeadStateError(f"{eid}: not in the T-697 ledger")
        host = t["host_line_id"]
        if host != b["host_line"]:
            raise R.BeadStateError(f"{eid}: T-723 host {host} != T-697 host {b['host_line']}")
        line = i72.get(host)
        hs = R.host_state(line)  # STALE / EXCLUDED raise
        if i71.get(host) != line:
            raise R.BeadStateError(f"{eid}: host {host} changed between V3.0.71 (T-723) and V3.0.72")
        if host not in causes:
            raise R.BeadStateError(f"{eid}: no merged hold census names host {host}'s cause")
        hcause, hsrc = causes[host]
        if b["status"] == "HELD":
            form = R.ledger_form(low=num(b["held_low"]), high=num(b["held_high"]))
        else:
            form = R.ledger_form(length=num(b["owner_m"]))
        st = R.bead_state(*form, hs, own_cause=b["cause"] if b["status"] == "HELD" else "", host_cause=hcause)
        lo, hi = num(b["dwg_low"]), num(b["dwg_high"])
        band = "" if lo is None or lo == hi else f"drawing-derived {lo} .. {hi} m (beside, F-T697-1; not the bound)"
        pending = t["reason"].split(": ", 1)[1] if t["class"] == "MAPPED_PENDING_CHANGE" else ""
        rows.append({
            "edge_id": eid, "scope": b["scope"], "floor": b["floor"], "room": b["room"], "class": b["class"],
            "count": b["count"], "hub": t["hub"], "pending": pending, "host_line": host,
            "host_code": line["item_code"], "host_element": line["element_id"], "host_state": hs,
            "host_bound": R.host_bound_text(line, hs), "host_cause_source": hsrc, "ledger_status": b["status"],
            "ledger_form": form[0], "ledger_m": form[1], "ledger_low": form[2], "ledger_high": form[3],
            "drawing_band": band, "bead_state": st["state"], "value": st["value"], "low": st["low"],
            "high": st["high"], "ledger_ref": st["ledger_ref"], "owner_trade": R.OWNER_TRADE, "cause": st["cause"],
        })
    n = R.check_rows(rows)
    return {
        "schema": SCHEMA, "task": "T-728", "rule": [R.RULE_ID, R.RULE_VERSION], "candidate": CANDIDATE,
        "inputs_sha256": {p: sha(p) for p in PINS}, "rows_restated": n, "stale": 0,
        "summary": summarise(rows), "rows": rows,
    }


def _r(x):
    return round(x, 6)


def summarise(rows):
    by = Counter((r["scope"], r["bead_state"]) for r in rows)
    sums = defaultdict(lambda: [0.0, 0.0, 0])
    hosts = defaultdict(lambda: {"rows": 0, "states": Counter(), "low": 0.0, "high": 0.0, "ledger_on_blank": 0.0})
    for r in rows:
        h = hosts[r["host_line"]]
        h["rows"] += 1
        h["states"][r["bead_state"]] += 1
        h["host_state"], h["host_bound"], h["host_element"], h["hub"] = (r["host_state"], r["host_bound"],
                                                                         r["host_element"], r["hub"])
        if r["bead_state"] == R.HELD_BOUND:
            s = sums[r["scope"]]
            s[0] += r["low"]
            s[1] += r["high"]
            s[2] += 1
            h["low"] += r["low"]
            h["high"] += r["high"]
        if r["bead_state"] == R.HELD_BLANK and r["ledger_form"] == R.MEASURED:
            h["ledger_on_blank"] += r["ledger_m"]
    return {
        "rows_by_scope_state": {f"{k[0]}|{k[1]}": v for k, v in sorted(by.items())},
        "held_bound_m_by_scope": {k: {"low": _r(v[0]), "high": _r(v[1]), "rows": v[2]} for k, v in sorted(sums.items())},
        "released_rows": sum(1 for r in rows if r["bead_state"] == R.RELEASED),
        "hosts_by_state": dict(Counter(h["host_state"] for h in hosts.values())),
        "hosts": {k: {"rows": v["rows"], "states": dict(v["states"]), "host_state": v["host_state"],
                      "host_bound": v["host_bound"], "host_element": v["host_element"], "hub": v["hub"],
                      "bead_held_low_m": _r(v["low"]), "bead_held_high_m": _r(v["high"]),
                      "ledger_m_on_blank_host_reference_only": _r(v["ledger_on_blank"])}
                  for k, v in sorted(hosts.items())},
        "pending_rows": dict(Counter(r["pending"] for r in rows if r["pending"])),
    }


def to_csv(d):
    s = io.StringIO()
    w = csv.writer(s, lineterminator="\n")
    w.writerow(CSV_COLS)
    for r in d["rows"]:
        w.writerow(["" if r.get(c) is None else r.get(c) for c in CSV_COLS])
    return s.getvalue()


def dumps(d):
    return json.dumps(d, indent=1, sort_keys=True, ensure_ascii=False) + "\n"


def main(argv):
    d = build()
    if "--write" in argv:
        OUT_JSON.parent.mkdir(exist_ok=True)
        OUT_JSON.write_text(dumps(d), encoding="utf-8")
        OUT_CSV.write_text(to_csv(d), encoding="utf-8")
    elif "--check" in argv:
        ok = OUT_JSON.read_text(encoding="utf-8") == dumps(d) and OUT_CSV.read_text(encoding="utf-8") == to_csv(d)
        print("T-728 check:", "EQUAL" if ok else "DIFFERS")
        return 0 if ok else 1
    print(json.dumps({k: v for k, v in d["summary"].items() if k != "hosts"}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
