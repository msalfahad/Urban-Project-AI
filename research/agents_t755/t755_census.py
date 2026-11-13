"""T-755 designer-list re-census of the HELD lines of ARCH_TAKEOFF_V3.0.77 (research only; nothing wired).

    bash scripts/agent_env.sh run --tree task-T-755 research/agents_t755/t755_census.py <private out dir of v3077_run>

<dir> is the --out folder of a private run of research/agents_t749/v3077_run.py (it runs the whole chain). Every file
V3_0_70_BOQ_LINES.json .. V3_0_77_BOQ_LINES.json found under it must hash to the 'lines' input of the merged line index
of its version (asserted; the indexes are the runs of record). The cause of a HELD line comes from its own record
(R-T755-1 = R-T716-1 + the Lead's named designer ids; t755_rules.py). The V3.0.70 classification is re-derived and
compared with the merged T-716 census (research/agents_t716/out/T716_CENSUS.json): every line must land in the same
bucket (asserted), so the delta to V3.0.77 is the rules applied to the moved lines only, attributed version step by
version step to the merged package that made the version (residual 0, asserted).

Writes research/agents_t755/out/T755_CENSUS.json and T755_CENSUS.md: engine ids, item codes, units, counts, bounds and
printed identifiers only. No cause text, no coordinates, no names.
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

import t755_rules as R  # noqa: E402

OUT = HERE / "out"
PARKED = ("STR.REBAR",)  # owner 2026-11-11 15:30 (1): rebar parked; counted, reported apart
# version -> (merged line index, package that made the version)
CHAIN = {
    "70": ("research/agents_t693/out/LINE_INDEX_V3_0_70.json", "T-693"),
    "71": ("research/agents_t704/out/LINE_INDEX_V3_0_71.json", "T-704"),
    "72": ("research/agents_t703/out/LINE_INDEX_V3_0_72.json", "T-703"),
    "73": ("research/agents_t722/out/LINE_INDEX_V3_0_73.json", "T-722"),
    "74": ("research/agents_t717/out/LINE_INDEX_V3_0_74.json", "T-717"),
    "75": ("research/agents_t729/out/LINE_INDEX_V3_0_75.json", "T-729"),
    "76": ("research/agents_t736/out/LINE_INDEX_V3_0_76.json", "T-736"),
    "77": ("research/agents_t749/out/LINE_INDEX_V3_0_77.json", "T-749"),
}
T716 = ROOT / "research/agents_t716/out/T716_CENSUS.json"
# The Lead's ONE list (board DESIGNER_QUESTIONS.md, version Lead 2026-11-13 04:15): item -> D-ids, as printed there.
ITEMS = {
    "1": ["D-02", "D-03", "D-04", "D-27", "D-30", "D-44"],
    "2": ["D-45", "D-58", "D-60", "D-64"],
    "3": ["D-16", "D-46", "D-63", "D-65", "D-66", "D-44"],
    "4": ["D-33", "D-34", "D-35"],
    "5": ["D-06", "D-17", "D-39", "D-62"],
    "6": ["D-43", "D-63"],
    "7": ["D-08", "D-13", "D-29", "D-56", "D-67", "D-68"],
    "8": ["D-09", "D-22", "D-24", "D-40", "D-47"],
    "9": ["D-41"],
    "10": [],
    "11": ["D-20", "D-42"],
    "12": ["D-45"],
    "13": ["D-62"],
    "14": ["D-GF-07"],
    "15": ["D-BAND"],
    "16": ["D-DRAIN"],
    "17": ["D-M1"],
    "18": ["D-J1", "D-J2", "D-J3"],
}
NAMED = ("D-BAND", "D-DRAIN", "D-M1", "D-J1", "D-J2", "D-J3")
# Item 14's id D-GF-07 is ALSO the drawing's mark of the ground-floor main entrance door (door schedule; T-737 F-T737-2
# found a second element under the same mark). A line that prints 'D-GF-07' names the door, not the list item, so the
# id is NOT read as a designer id (R-T755-1 (a)); the lines printing it are reported (finding UNREADABLE_LIST_ID).
UNREADABLE = ("D-GF-07",)
D_STAY_OUT = ("D-13", "D-23", "D-29", "D-30", "D-32", "D-56", "D-60", "D-65")   # as T-716 (D_REMOVED_REVISED s.2)


def item_of() -> dict:
    m = defaultdict(list)
    for it, ds in ITEMS.items():
        for d in ds:
            m[d].append(it)
    return dict(m)


def load(out_dir: Path) -> list:
    files = {}
    for f in out_dir.rglob("V3_0_7?_BOQ_LINES.json"):
        v = f.name[5:7]
        if v in CHAIN:
            files.setdefault(v, []).append(f)
    chain = []
    for v, (ixp, pkg) in CHAIN.items():
        ix = json.loads((ROOT / ixp).read_text(encoding="utf-8"))
        want = ix["inputs"]["lines"]
        hit = [f for f in files.get(v, []) if hashlib.sha256(f.read_bytes()).hexdigest() == want]
        if not hit:
            raise SystemExit(f"V3_0_{v}: no line file under {out_dir} hashes to the run of record {want[:8]}")
        recs = {ln["line_id"]: ln for ln in json.loads(hit[0].read_bytes())}
        if set(recs) != {r["line_id"] for r in ix["lines"]}:
            raise SystemExit(f"V3_0_{v}: index and line file disagree on the line set")
        chain.append({"v": v, "pkg": pkg, "index": ix, "records": recs, "sha": want, "index_file": ixp,
                      "index_sha": hashlib.sha256((ROOT / ixp).read_bytes()).hexdigest()})
    return chain


def concrete_rows(c77: dict, ix77: dict) -> list:
    rows = []
    for lid, a in sorted(c77["assignment"].items()):
        if not a["item_code"].startswith("STR.CONC."):
            continue
        r = ix77[lid]
        rows.append({"line_id": lid, "item_code": a["item_code"], "unit": a["unit"], "element_id": r["element_id"],
                     "side": a["side"], "low": r["held_low"], "high": r["held_high"], "kind": a["kind"],
                     "bucket": a["bucket"], "dependent": a["dependent"], "host": a["host"]})
    return rows


def build(out_dir: Path) -> dict:
    chain = load(out_dir)
    imap = item_of()
    cens = {}
    for k in chain:
        cens[k["v"]] = R.census(k["index"]["lines"], k["records"], NAMED, imap)
    # the V3.0.70 classification must equal the merged T-716 census line by line (same rules on the same lines)
    t716 = json.loads(T716.read_text(encoding="utf-8"))
    a70 = cens["70"]["assignment"]
    diff70 = sorted(l for l, a in t716["assignment"].items() if a70.get(l, {}).get("bucket") != a["bucket"])
    assert set(a70) == set(t716["assignment"]), "V3.0.70 HELD line set differs from T-716"
    # R-T755-1 v2: T-716 read retired causes too; the ONLY allowed difference is a line whose (own or host's) retired
    # identifier was dropped. Every other line must land in the T-716 bucket (asserted).
    other = [l for l in diff70 if not a70[l]["retired_hits"]]
    assert not other, f"V3.0.70 re-derivation differs from T-716 on {len(other)} lines without a retired id: {other[:5]}"
    t716_diff = {l: {"t716": t716["assignment"][l]["bucket"], "v2": a70[l]["bucket"],
                     "retired": a70[l]["retired_hits"]} for l in diff70}
    tr = R.transitions([(k["v"], {r["line_id"]: r for r in k["index"]["lines"]}, cens[k["v"]]["assignment"])
                        for k in chain])
    delta = R.bucket_delta(a70, cens["77"]["assignment"], tr)
    assert all(d["residual"] == 0 for d in delta.values())
    # per D-id delta 70 -> 77 (sole + shared line counts), each move attributed to its step
    pkg = {f"{chain[n - 1]['v']}->{k['v']}": k["pkg"] for n, k in enumerate(chain) if n}
    per_d_delta = {}
    ds = set(cens["70"]["per_d_id"]) | set(cens["77"]["per_d_id"])
    for d in sorted(ds, key=R._dkey):
        f = cens["70"]["per_d_id"].get(d, {"sole_lines": 0, "shared_lines": 0})
        t = cens["77"]["per_d_id"].get(d, {"sole_lines": 0, "shared_lines": 0})
        moves = Counter()
        for lid, steps in tr.items():
            for s in steps:
                fb = s["from"][0] if s["from"] else ""
                tb = s["to"][0] if s["to"] else ""
                inf, intt = d in fb.split("+"), d in tb.split("+")
                if inf != intt:
                    moves[(pkg[s["step"]], "in" if intt else "out")] += 1
                elif inf and (fb.count("+") == 0) != (tb.count("+") == 0):
                    moves[(pkg[s["step"]], "sole->shared" if tb.count("+") else "shared->sole")] += 1
        net = sum(n if io == "in" else -n for (_, io), n in moves.items() if io in ("in", "out"))
        tot_f, tot_t = f["sole_lines"] + f["shared_lines"], t["sole_lines"] + t["shared_lines"]
        assert tot_t - tot_f == net, (d, tot_f, tot_t, net)
        per_d_delta[d] = {"v70": [f["sole_lines"], f["shared_lines"]], "v77": [t["sole_lines"], t["shared_lines"]],
                          "moves": {f"{p} {io}": n for (p, io), n in sorted(moves.items())}, "residual": 0}
    c77 = cens["77"]
    ix77 = {r["line_id"]: r for r in chain[-1]["index"]["lines"]}
    kinds = Counter((v["kind"], "PARKED_REBAR" if v["item_code"] in PARKED else "ACTIVE")
                    for v in c77["assignment"].values())
    findings = []
    for d in D_STAY_OUT:
        if d in c77["per_d_id"]:
            v = c77["per_d_id"][d]
            findings.append({"finding": "HELD_LINE_CITES_A_STAY_OUT_D_ID", "d_id": d,
                             "line_ids": v["sole_line_ids"] + v["shared_line_ids"]})
    for d, lids in c77["unlisted_d_ids"].items():
        act = [l for l in lids if c77["assignment"][l]["item_code"] not in PARKED]
        findings.append({"finding": "D_ID_IN_NO_LIST_ITEM", "d_id": d, "lines": len(lids), "active_lines": len(act),
                         "active_line_ids": act})
    for it, ds_ in ITEMS.items():
        if it not in c77["per_item"]:
            findings.append({"finding": "LIST_ITEM_CITED_BY_NO_HELD_LINE", "item": it, "d_ids": ds_})
    for n in UNREADABLE:
        rx = R._named_re((n,))
        hit = sorted(l for l in c77["assignment"] if rx.search(R.R.cause_text(chain[-1]["records"][l])))
        findings.append({"finding": "UNREADABLE_LIST_ID", "d_id": n, "held_lines_printing_it": hit,
                         "their_buckets": dict(sorted(Counter(c77["assignment"][l]["bucket"] for l in hit).items())),
                         "families": sorted({c77["assignment"][l]["item_code"] for l in hit})})
    cited = set(c77["per_d_id"])
    findings.append({"finding": "LIST_D_IDS_CITED_BY_NO_HELD_LINE",
                     "d_ids": sorted({d for ds_ in ITEMS.values() for d in ds_} - cited, key=R._dkey)})
    for b in c77["buckets"]:
        if b["finding"]:
            findings.append({"finding": f"{b['kind']}_NO_ITEM_NUMBER" if b["kind"] != "UNNAMED" else "UNNAMED",
                             "bucket": b["bucket"], "lines": b["lines"],
                             "families": sorted({(r["item_code"], r["unit"]) for r in b["by_family_unit"]})})
    return {
        "schema": "URBAN_T755_DESIGNER_RECENSUS_V1",
        "rule": "R-T755-1 (research/agents_t755/t755_rules.py) = R-T716-1 + named ids + item view",
        "candidate": chain[-1]["index"]["candidate_version"],
        "inputs": {k["v"]: {"lines_sha256": k["sha"], "index_file": k["index_file"], "index_sha256": k["index_sha"],
                            "package": k["pkg"]} for k in chain},
        "t716_rederived_identical_except_retired": True,
        "t716_differences_v3070": t716_diff,
        "retired_hits_v3077": {l: {"bucket": a["bucket"], "retired": a["retired_hits"], "item_code": a["item_code"],
                                   "dependent": a["dependent"], "host": a["host"]}
                               for l, a in sorted(c77["assignment"].items()) if a["retired_hits"]},
        "held_lines": {k["v"]: cens[k["v"]]["held_lines"] for k in chain},
        "held_by_kind": {f"{k}|{p}": n for (k, p), n in sorted(kinds.items())},
        "dependent_lines": sum(1 for v in c77["assignment"].values() if v["dependent"]),
        "buckets": c77["buckets"],
        "per_d_id": c77["per_d_id"],
        "per_item": c77["per_item"],
        "per_d_id_delta_70_77": per_d_delta,
        "bucket_delta_70_77": delta,
        "line_transitions": tr,
        "assignment": {lid: {k: v[k] for k in ("kind", "bucket", "dependent", "host", "item_code", "unit", "side")}
                       for lid, v in sorted(c77["assignment"].items())},
        "concrete_held": concrete_rows(c77, ix77),
        "findings": findings,
    }


def _fmt(r: dict) -> str:
    p = [f"{r['lines']} lines"]
    if r["range"]:
        p.append(f"{r['range']} bounded {r['range_low']:.6g} .. {r['range_high']:.6g}")
    if r["at_least"]:
        p.append(f"{r['at_least']} AT_LEAST {r['at_least_sum']:.6g}")
    if r["at_most"]:
        p.append(f"{r['at_most']} AT_MOST {r['at_most_sum']:.6g}")
    if r["blank"]:
        p.append(f"{r['blank']} blank")
    if r["dependent"]:
        p.append(f"{r['dependent']} dependent")
    return "; ".join(p)


def _per_unit(rows):
    t = defaultdict(R.R._acc)
    for r in rows:
        if r["item_code"] in PARKED:
            continue
        for k in t[r["unit"]]:
            t[r["unit"]][k] += r[k]
    return "<br>".join(f"{u}: {_fmt(a)}" for u, a in sorted(t.items()))


def markdown(s: dict) -> str:
    o = [f"# T-755 census of the HELD lines of {s['candidate']} by cause (R-T755-1)", "",
         "Inputs (runs of record, sha256 of each line file = its merged line index): "
         + ", ".join(f"V3.0.{v} {i['lines_sha256'][:8]} ({i['package']})" for v, i in s["inputs"].items()) + ".",
         f"HELD lines per version: {s['held_lines']}. V3.0.70 re-derived identical to T-716 line by line EXCEPT "
         f"{len(s['t716_differences_v3070'])} lines where T-716 read a retired / superseded cause from the notes "
         f"history (R-T755-1 v2; listed below). Dependent "
         f"lines on V3.0.77: {s['dependent_lines']}. Per family and unit only; blank never 0; STR.REBAR kg PARKED.", "",
         "## Lines per cause kind (V3.0.77)", "", "| kind | active | parked rebar |", "|---|---|---|"]
    k = defaultdict(lambda: [0, 0])
    for key, n in s["held_by_kind"].items():
        a, p = key.split("|")
        k[a][p == "PARKED_REBAR"] += n
    for a in R.R.BUCKET_ORDER:
        if a in k:
            o.append(f"| {a} | {k[a][0]} | {k[a][1]} |")
    o += ["", "## Per list item (SOLE = only this item holds the line; SHARED = with another item; rebar apart)", "",
          "| item | D-ids | sole | shared | sole, per unit (active) | shared, per unit (active) |",
          "|---|---|---|---|---|---|"]
    for it, ds in ITEMS.items():
        v = s["per_item"].get(it)
        if not v:
            o.append(f"| {it} | {', '.join(ds) or '-'} | 0 | 0 | - | - |")
            continue
        o.append(f"| {it} | {', '.join(ds)} | {v['sole_lines']} | {v['shared_lines']} | {_per_unit(v['sole'])} | "
                 f"{_per_unit(v['shared'])} |")
    o += ["", "## Per D-id: V3.0.70 -> V3.0.77 (sole / shared lines) and the packages that moved them", "",
          "| D-id | V3.0.70 | V3.0.77 | moves | sole on V3.0.77, per family and unit |", "|---|---|---|---|---|"]
    for d, v in s["per_d_id_delta_70_77"].items():
        now = s["per_d_id"].get(d, {"sole": []})
        fam = "<br>".join(f"{r['item_code']} {r['unit']}: {_fmt(r)}" for r in now["sole"])
        mv = ", ".join(f"{k} {n}" for k, n in v["moves"].items()) or "none"
        o.append(f"| {d} | {v['v70'][0]} / {v['v70'][1]} | {v['v77'][0]} / {v['v77'][1]} | {mv} | {fam} |")
    o += ["", "## Bucket delta V3.0.70 -> V3.0.77 (residual 0 per bucket)", "",
          "| bucket | V3.0.70 | V3.0.77 | in (step: n) | out (step: n) |", "|---|---|---|---|---|"]
    for b, v in s["bucket_delta_70_77"].items():
        if v["first"] != v["last"] or v["in"] or v["out"]:
            o.append(f"| {b} | {v['first']} | {v['last']} | {v['in'] or '-'} | {v['out'] or '-'} |")
    o += ["", "## HELD concrete lines on V3.0.77 (input to the sweep in T-755_DESIGNER_RECENSUS.md)", "",
          "| line | family | element | side | low | high | cause |", "|---|---|---|---|---|---|---|"]
    for r in s["concrete_held"]:
        o.append(f"| {r['line_id']} | {r['item_code'][9:]} | {r['element_id']} | {r['side']} | "
                 f"{'' if r['low'] is None else r['low']} | {'' if r['high'] is None else r['high']} | "
                 f"{r['bucket']}{' (dep.)' if r['dependent'] else ''} |")
    o += ["", "## R-T755-1 v2: lines whose notes history printed an id the live cause does not (not read)", "",
          f"V3.0.70 vs T-716: {len(s['t716_differences_v3070'])} lines change bucket; V3.0.77: "
          f"{len(s['retired_hits_v3077'])} lines carry an id in history only.", "",
          "| line | family | live bucket (V3.0.77) | history-only ids | dependent on |", "|---|---|---|---|---|"]
    for lid, v in s["retired_hits_v3077"].items():
        o.append(f"| {lid} | {v['item_code']} | {v['bucket']} | {', '.join(v['retired'])} | {v['host'] or '-'} |")
    o += ["", "| line | T-716 bucket (V3.0.70) | v2 bucket (V3.0.70) |", "|---|---|---|"]
    for lid, v in sorted(s["t716_differences_v3070"].items()):
        o.append(f"| {lid} | {v['t716']} | {v['v2']} |")
    o += ["", "## Findings for the Lead", ""]
    for f in s["findings"]:
        if f["finding"] == "HELD_LINE_CITES_A_STAY_OUT_D_ID":
            o.append(f"- {f['d_id']} is out of the designer package but HELD lines cite it: {', '.join(f['line_ids'])}")
        elif f["finding"] == "D_ID_IN_NO_LIST_ITEM":
            o.append(f"- {f['d_id']} is in no list item: {f['lines']} lines ({f['active_lines']} active"
                     + (f": {', '.join(f['active_line_ids'])}" if f["active_line_ids"] else "") + ")")
        elif f["finding"] == "UNREADABLE_LIST_ID":
            o.append(f"- {f['d_id']} is also a drawing mark (main entrance door): not read as an item; HELD lines "
                     f"printing it {len(f['held_lines_printing_it'])} ({', '.join(f['held_lines_printing_it'])}; "
                     f"buckets {f['their_buckets']}; families {', '.join(f['families'])})")
        elif f["finding"] == "LIST_ITEM_CITED_BY_NO_HELD_LINE":
            o.append(f"- list item {f['item']} ({', '.join(f['d_ids']) or 'no D-id'}) is cited by no HELD line")
        elif f["finding"] == "LIST_D_IDS_CITED_BY_NO_HELD_LINE":
            o.append(f"- list D-ids cited by no HELD line: {', '.join(f['d_ids'])}")
        else:
            fams = ", ".join(f"{c} {u}" for c, u in f["families"])
            o.append(f"- {f['finding']} [{f['bucket']}]: {f['lines']} lines ({fams})")
    return "\n".join(o) + "\n"


def main(argv):
    if len(argv) != 2:
        raise SystemExit(__doc__)
    s = build(Path(argv[1]))
    OUT.mkdir(exist_ok=True)
    (OUT / "T755_CENSUS.json").write_bytes(R.canonical(s))
    (OUT / "T755_CENSUS.md").write_text(markdown(s), encoding="utf-8")
    print("held", s["held_lines"], "dependent", s["dependent_lines"])
    print(json.dumps(s["held_by_kind"], indent=1))
    print("items", {k: (v["sole_lines"], v["shared_lines"]) for k, v in s["per_item"].items()})
    print("findings", len(s["findings"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
