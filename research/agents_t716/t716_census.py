"""T-716 designer-list impact census on the candidate of record ARCH_TAKEOFF_V3.0.70 (research only; nothing wired).

    bash scripts/agent_env.sh run --tree task-T-716 research/agents_t716/t716_census.py <V3_0_70_BOQ_LINES.json>

<V3_0_70_BOQ_LINES.json> is a private regeneration of the run of record (T-693 chain: research/agents_t693/v3070_run.py
on the Drive copies; sha256 must start e8e001de, asserted). The line classes and bounds come from the merged index
research/agents_t693/out/LINE_INDEX_V3_0_70.json (its 'lines' input hash must equal the file's sha256, asserted); the
cause text of each HELD line comes from the line record (rule R-T716-1, t716_rules.py).

Writes research/agents_t716/out/T716_CENSUS.json and T716_CENSUS.md: engine ids, item codes, units, counts, bounds and
printed identifiers (D / RFI / Q / ORR / reason codes) only. No cause text, no coordinates, no names are written.
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

import t716_rules as R  # noqa: E402

INDEX = ROOT / "research" / "agents_t693" / "out" / "LINE_INDEX_V3_0_70.json"
OUT = HERE / "out"
RUN_OF_RECORD = "e8e001de"
PARKED = ("STR.REBAR",)               # owner 2026-11-11 15:30 (1): rebar parked; counted, reported apart
# D-ids the RFI revision file keeps OUT of the designer package (D_REMOVED_REVISED.md s.2: resolved from the drawings,
# owner decisions, no quantity effect, or a drawing-confirmed absence). A HELD line that still cites one is a finding.
D_STAY_OUT = ("D-13", "D-23", "D-29", "D-30", "D-32", "D-56", "D-60", "D-65")


def _fmt(r: dict) -> str:
    parts = [f"{r['lines']} lines"]
    if r["range"]:
        parts.append(f"{r['range']} bounded {r['range_low']:.6g} .. {r['range_high']:.6g}")
    if r["at_least"]:
        parts.append(f"{r['at_least']} AT_LEAST {r['at_least_sum']:.6g}")
    if r["at_most"]:
        parts.append(f"{r['at_most']} AT_MOST {r['at_most_sum']:.6g}")
    if r["blank"]:
        parts.append(f"{r['blank']} blank")
    if r["dependent"]:
        parts.append(f"{r['dependent']} dependent")
    return f"{r['item_code']} {r['unit']}: " + "; ".join(parts)


def unit_totals(rows: list) -> dict:
    """per unit (never across units): lines, bounded low .. high, one-sided sums, blanks."""
    t = defaultdict(R._acc)
    for r in rows:
        a = t[r["unit"]]
        for k in a:
            a[k] += r[k]
    return {u: {k: (round(v, 6) if isinstance(v, float) else v) for k, v in a.items()} for u, a in sorted(t.items())}


def build(lines_path: Path) -> dict:
    raw = lines_path.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    if not sha.startswith(RUN_OF_RECORD):
        raise SystemExit(f"V3_0_70_BOQ_LINES {sha[:8]} is not the run of record {RUN_OF_RECORD}")
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    if index["inputs"]["lines"] != sha:
        raise SystemExit("the line index was not built on this line file")
    lines = json.loads(raw)
    records = {ln["line_id"]: ln for ln in lines}
    if len(records) != len(index["lines"]) or set(records) != {i["line_id"] for i in index["lines"]}:
        raise SystemExit("index and line file disagree on the line set")
    c = R.census(index["lines"], records)
    a = c["assignment"]
    findings = []
    for d in D_STAY_OUT:
        if d in c["per_d_id"]:
            v = c["per_d_id"][d]
            findings.append({"finding": "HELD_LINE_CITES_A_STAY_OUT_D_ID", "d_id": d,
                             "line_ids": v["sole_line_ids"] + v["shared_line_ids"]})
    dep_host_missing = sorted(lid for lid, v in a.items() if v["dependent"] and v["host"] not in records)
    assert not dep_host_missing
    for b in c["buckets"]:
        if b["finding"]:
            findings.append({"finding": f"{b['kind']}_NO_ITEM_NUMBER" if b["kind"] != "UNNAMED" else "UNNAMED",
                             "bucket": b["bucket"], "lines": b["lines"],
                             "families": sorted({(r["item_code"], r["unit"]) for r in b["by_family_unit"]})})
    kinds = Counter((v["kind"], "PARKED_REBAR" if v["item_code"] in PARKED else "ACTIVE") for v in a.values())
    return {
        "schema": "URBAN_T716_DESIGNER_CENSUS_V1",
        "rule": "R-T716-1 (research/agents_t716/t716_rules.py)",
        "candidate": index["candidate_version"],
        "inputs": {"lines_sha256": sha, "index_file": "research/agents_t693/out/LINE_INDEX_V3_0_70.json",
                   "index_sha256": hashlib.sha256(INDEX.read_bytes()).hexdigest()},
        "held_lines": c["held_lines"],
        "held_by_kind": {f"{k}|{p}": n for (k, p), n in sorted(kinds.items())},
        "dependent_lines": sum(1 for v in a.values() if v["dependent"]),
        "buckets": c["buckets"],
        "per_d_id": c["per_d_id"],
        "assignment": {lid: {k: v[k] for k in ("kind", "bucket", "dependent", "host", "item_code", "unit", "side")}
                       for lid, v in sorted(a.items())},
        "findings": findings,
    }


def markdown(s: dict) -> str:
    out = [f"# T-716 census of the HELD lines of {s['candidate']} by cause (R-T716-1)", "",
           f"Lines file sha256 {s['inputs']['lines_sha256'][:8]} (run of record); index {s['inputs']['index_file']} "
           f"({s['inputs']['index_sha256'][:8]}). HELD lines {s['held_lines']}, of which dependent (cause taken from a "
           f"HELD host) {s['dependent_lines']}. Per family and unit only; never summed across units; a blank line has "
           "no bound and is never 0; STR.REBAR (kg) is PARKED (owner 2026-11-11) and shown apart.", "",
           "## Lines per cause kind", "", "| kind | active lines | parked rebar lines |", "|---|---|---|"]
    kinds = defaultdict(lambda: [0, 0])
    for k, n in s["held_by_kind"].items():
        kind, p = k.split("|")
        kinds[kind][p == "PARKED_REBAR"] += n
    for k in R.BUCKET_ORDER:
        if k in kinds:
            out.append(f"| {k} | {kinds[k][0]} | {kinds[k][1]} |")
    out += ["", "## Per designer item (SOLE = held by this item alone; SHARED = held with another item, listed under "
            "each, never added twice)", "", "| D-id | sole lines | shared lines | sole, per family and unit (rebar "
            "excluded) | sole, per unit |", "|---|---|---|---|---|"]
    for d, v in s["per_d_id"].items():
        act = [r for r in v["sole"] if r["item_code"] not in PARKED]
        reb = sum(r["lines"] for r in v["sole"] if r["item_code"] in PARKED) + \
            sum(r["lines"] for r in v["shared"] if r["item_code"] in PARKED)
        ut = unit_totals(act)
        uts = "; ".join(_fmt(dict(t, item_code="all", unit=u)).replace("all ", "", 1) for u, t in ut.items())
        out.append(f"| {d} | {v['sole_lines']} | {v['shared_lines']} | "
                   + "<br>".join(_fmt(r) for r in act) + (f"<br>STR.REBAR kg: {reb} lines (parked)" if reb else "")
                   + f" | {uts} |")
    out += ["", "## Combined buckets (each HELD line once)", "", "| kind | bucket | lines | per family and unit |",
            "|---|---|---|---|"]
    for b in s["buckets"]:
        out.append(f"| {b['kind']} | {b['bucket']} | {b['lines']} | "
                   + "<br>".join(_fmt(r) for r in b["by_family_unit"]) + " |")
    out += ["", "## Findings for the Lead", ""]
    for f in s["findings"]:
        if f["finding"] == "HELD_LINE_CITES_A_STAY_OUT_D_ID":
            out.append(f"- {f['d_id']} is kept out of the designer package (D_REMOVED_REVISED s.2) but "
                       f"{len(f['line_ids'])} HELD line(s) still cite it: {', '.join(f['line_ids'])}")
        else:
            fams = ", ".join(f"{c} {u}" for c, u in f["families"])
            out.append(f"- {f['finding']} [{f['bucket']}]: {f['lines']} lines ({fams})")
    return "\n".join(out) + "\n"


def main(argv):
    if len(argv) != 2:
        raise SystemExit(__doc__)
    s = build(Path(argv[1]))
    OUT.mkdir(exist_ok=True)
    (OUT / "T716_CENSUS.json").write_bytes(R.canonical(s))
    (OUT / "T716_CENSUS.md").write_text(markdown(s), encoding="utf-8")
    print("held", s["held_lines"], "dependent", s["dependent_lines"])
    print(json.dumps(s["held_by_kind"], indent=1))
    print("D-ids", len(s["per_d_id"]), "findings", len(s["findings"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
