"""T-748 (a) WIRING READINESS ROUND 6 on ARCH_TAKEOFF_V3.0.75 (R-T748-1; lane I, research, no quantity).

(1) the merged T-730 map (1,174 rows, V3.0.73) restated on V3.0.75 by line id (stale 0, host moved or not, rows the
merged T-717 / T-729 packages wired, blockers refreshed against the board);
(2) the pieces merged since T-730 mapped by line id to their hub (T-733, T-734 + its issued downgrade record, T-735,
T-737, T-708, T-740, T-742, T-743);
(3) one hub per target across both, the queued Gate B packages (T-736, T-738, T-314 r3, T-509, T-749) sized so each
runs in one Checker run, and the Gate A sample.

Reads only committed, sha-pinned files (plus in/T748_BOARD_DOWNGRADES.json, the Checker record copied from the board);
writes only research/agents_t748/out/. Nothing wired; V3.0.75 NOT RELEASED; V2.9 + route G untouched.

  python3 -I research/agents_t748/t748_alsenan.py --write | --check
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
import t748_rules as R  # noqa: E402

OUT = HERE / "out"
JSON_OUT, CSV_OUT = OUT / "T748_READINESS.json", OUT / "T748_ROWS.csv"
PIN = {
    "index73": ("research/agents_t722/out/LINE_INDEX_V3_0_73.json",
                "af8d567d8a8ae8288ddf3c4c8207d2cbfcf2f322513af84e63a4448898ad7b23"),
    "index74": ("research/agents_t717/out/LINE_INDEX_V3_0_74.json",
                "6733cbc143cdfffd82eeaee54457f97bbfa7b91b541f648a411825887b8b3bca"),
    "index75": ("research/agents_t729/out/LINE_INDEX_V3_0_75.json",
                "498c36bc6647a853a51feba83ce3bf2817d206f84911b8a27e025daab920b4c2"),
    "t730": ("research/agents_t730/out/T730_READINESS.json",
             "ebad37d279dfbd7301d7dd02a411f08433bb93b47f480608e6fcff73d7e0cd65"),
    "t717": ("research/agents_t717/out/T717_SUMMARY.json",
             "ec817f34969da526fa8b0a5a84ab18f6ba94616d63bf421cf51b1290b059ab3b"),
    "t729": ("research/agents_t729/out/T729_SUMMARY.json",
             "736436227b537327ada1b91d8c88fc3deb39f4ed2bfb40e8fee188a897dde4c1"),
    "t733": ("research/agents_t733/out/T733_H3_READINESS.json",
             "17cd75642a32fefb7eb89443cd99b97bf85e03a3984574a25be57698f6e2dc76"),
    "t734": ("research/agents_t734/out/T734_WP_H4_EVIDENCE.json",
             "d39d93fd0eda75549cfbb5893e86192c10055c78011e420a212e3b596ab2bf13"),
    "t735": ("research/agents_t735/out/T735_DECIDER.json",
             "086954846170f59c871431f4262eed513022586baab1be0c8aea698f40b388d3"),
    "t737": ("research/agents_t737/out/T737_READINESS.json",
             "d31c39adec8b3d848b8a43239f31f385b25e0fe812e27b15933abcbf886db02e"),
    "t708": ("research/agents_t708/WIRING_T708.csv",
             "98f603fc48724f831e0e320255b6276ba7022bc50d4a05f1809728923e4d4b9c"),
    "t740": ("research/agents_t740/out/T740_PAINT_RULE.json",
             "3918f7e4382728ea990b900cce5bdda059ede9d9356b4f24c7a24f6835efaff8"),
    "t742": ("research/agents_t742/out/T742_PARAPET_BLOCKS.json",
             "1ad56da3fa1be1d8d86d3b0f05fe6d8de86bbb92d490531be8745505fab97c98"),
    "t743": ("research/agents_t743/out/T743_ALSENAN_COUNTS.json",
             "0b23ac3d07d0f60a1df84fe08d41e4761bcf2ca462cf39537d03201693defc04"),
    "board_dg": ("research/agents_t748/in/T748_BOARD_DOWNGRADES.json",
                 "76109859d28d64f9534da62937a786b6ff514e4c93ed40cfe7022b3e3ea88046"),
}
# board states read on agents/control @ 1abebbb8 (2026-11-12 17:00Z, after the T-748 claim); a row not listed here
# that a blocker names fails the build (rule 3)
BOARD = {"T-717": "MERGED", "T-729": "MERGED", "T-732": "MERGED", "T-733": "MERGED", "T-734": "MERGED",
         "T-735": "MERGED", "T-708": "MERGED", "T-493": "MERGED", "T-743": "MERGED", "T-746": "READY",
         "T-314": "QUEUED", "T-736": "QUEUED", "T-738": "QUEUED", "T-509": "QUEUED", "T-749": "QUEUED",
         "T-744": "TODO", "T-747": "TODO"}
# hub -> the board row that wires it (T-730 hub names; new hubs of this round in capitals)
HUB_PACKAGE = {"H1R": "T-736", "H2a": "T-736", "H2b": "T-314 r3", "H3": "T-738", "H3S": "T-738", "H4": "NO_PACKAGE_ROW",
               "H5": "T-509", "H1P": "T-749", "FACADE": "T-314 r3", "B9-05": "NO_PACKAGE_ROW",
               "B12-01": "NO_PACKAGE_ROW", "T-717": "T-717 (MERGED V3.0.74)", "T-729": "T-729 (MERGED V3.0.75)",
               "C10": "T-729 (MERGED V3.0.75)", "T-703": "T-703 (MERGED V3.0.72)", "T-722": "T-722 (MERGED V3.0.73)",
               "": "no hub (statement / no line)"}
MERGED_PACKAGE_HUBS = {"T-717": "t717", "T-729": "t729", "C10": "t729"}
CITED_DG_IDS = ("DG-a429c160",)     # the id the board text (Verifier 15:12, Lead 16:20, LEAD_STATE, FEEDBACK) cites


def load(key, raw=False):
    rel, want = PIN[key]
    b = (ROOT / rel).read_bytes()
    got = hashlib.sha256(b).hexdigest()
    if got != want:
        raise R.ReadinessError(f"{rel}: sha256 {got[:8]} != pinned {want[:8]}")
    return b.decode("utf-8") if raw else json.loads(b.decode("utf-8"))


def _r(x):
    return None if x is None else round(float(x), 6)


def after_text(a):
    if not a:
        return ""
    if isinstance(a, str):
        return a
    parts = [str(a.get(k)) for k in ("kind", "state") if a.get(k)]
    for k in ("value", "low", "high"):
        if a.get(k) is not None:
            parts.append(f"{k} {a[k]}")
    if a.get("note"):
        parts.append(str(a["note"])[:100])
    return " ".join(parts)


def restate_t730(t730, i73, i75, movers, pkg_lines):
    rows = []
    for r in t730["rows"]:
        host = r.get("host_line_id")
        out = {"source": "T-730", "piece": r["piece"], "row": r["row"], "hub": r["hub"] or "",
               "package": HUB_PACKAGE[r["hub"] or ""], "action_t730": r["action"], "live": r["live"] or "",
               "unit": r.get("unit") or "", "target": r.get("new_line_key") or host or "",
               "host_line_id": host or "", "after": after_text(r.get("after"))}
        if host:
            st, who = R.host_status(R.resolve(host, i75.keys()), i73, i75, movers)
        else:
            st, who = "NO_HOST", []
        out["host_status"], out["moved_by"] = st, who
        open_, cleared = R.refresh_blockers(r.get("blockers") or [], BOARD)
        out["blockers"], out["cleared"] = open_, cleared
        action = r["action"]
        if r["hub"] in MERGED_PACKAGE_HUBS:
            named = pkg_lines[MERGED_PACKAGE_HUBS[r["hub"]]]
            keyed = pkg_lines[MERGED_PACKAGE_HUBS[r["hub"]] + "_keys"]
            if r["action"] == "ADD" and (r["row"] in keyed or (r.get("new_line_key") or "").split(":")[-1] in keyed):
                action = "WIRED_ADDED"
            elif host and host in named and r["action"] != "ADD":
                a = r.get("after") or {}
                ln = i75[host]
                same = (a.get("kind") in ("VALUE", "BOUND", "EXCLUDED") and
                        (_r(a.get("value")), _r(a.get("low")), _r(a.get("high"))) ==
                        (_r(ln["measured_net"]), _r(ln["held_low"]), _r(ln["held_high"])))
                action = "WIRED_SAME" if same else "WIRED_RESTATED"
            elif r["action"] in R.MOVING and r["live"] == "LIVE":
                action = "UNWIRED_AFTER_MERGE"
        elif r["action"] == "WIRED":
            action = "WIRED"
        out["action"] = action
        rows.append(out)
    return rows


def piece_t740(t740, i75):
    rows = []
    for f in t740["faces"]:
        base = {"source": "T-740", "piece": "T-740", "row": f"T-740:{f['paint_element'] or f['plaster_element']}", "hub": "H1P",
                "package": HUB_PACKAGE["H1P"], "unit": "m2", "live": "LIVE", "blockers": [], "cleared": []}
        lid = f["paint_line"]
        rp = f["rule_paint"]
        if rp == "EXCLUDED":
            lid = R.resolve(lid, i75.keys()) if lid else None
            ex = bool(lid) and i75[lid]["class"] == "EXCLUDED"
            rows.append({**base, "target": lid or "", "host_line_id": lid or "", "moved_by": [],
                         "host_status": "UNCHANGED" if lid else "NO_HOST", "action": "KEEP" if ex else "CHANGE",
                         "after": f"EXCLUDED (class {f['class']}): {f['note'][:80]}"})
            continue
        lo, hi = rp or (None, None)
        named = "; ".join(f"{n['end']} {n['cause']} {n['m2']} ({n['what']})" for n in f["named"])
        base["after"] = (f"rule paint {lo} .. {hi} m2" if lo is not None else "rule paint BLANK (held, never 0)") + (
            f" (UP-FIN-PAINT-002 1.0.0); class {f['class']}") + (
            f"; named: {named}" if named else "")
        if lid is None:
            rows.append({**base, "target": "", "host_line_id": "", "host_status": "NO_HOST", "moved_by": [],
                         "action": "NONE", "after": base["after"] + "; no paint line (" + f["note"][:80] + ")"})
            continue
        lid = R.resolve(lid, i75.keys())
        ln = i75[lid]
        if "PAINT" not in ln["item_code"]:
            raise R.ReadinessError(f"{lid}: T-740 paint face on a {ln['item_code']} line")
        if f["class"] == "RETURN":
            act, bl = "PENDING", ["PENDING_ON T-746 (READY): opening edges lm, reading B (owner paint rule)"]
        elif lo is None:
            blank = ln["class"] == "HELD" and ln["held_low"] is None and ln["held_high"] is None
            act, bl = ("KEEP" if blank or ln["class"] == "EXCLUDED" else "CHANGE"), []
        elif ln["class"] == "RELEASED":
            if lo != hi:
                act = "CHANGE_RELEASED"
            else:
                act, _ = R.released_action(ln["measured_net"], lo,
                                           any(n["cause"] == "LEDGER_ROUNDING" for n in f["named"]))
            bl = []
        elif ln["class"] == "EXCLUDED":
            act, bl = ("KEEP" if float(hi) == 0 else "CHANGE"), []
        else:
            same = (_r(ln["held_low"]), _r(ln["held_high"])) == (_r(lo), _r(hi))
            act, bl = ("KEEP" if same else "CHANGE"), []
        rows.append({**base, "target": lid, "host_line_id": lid, "host_status": "UNCHANGED", "moved_by": [],
                     "action": act, "blockers": bl,
                     "index": f"{ln['class']} {ln['measured_net'] if ln['measured_net'] is not None else ''}"
                              f"{'' if ln['held_low'] is None else ln['held_low']} .. "
                              f"{'' if ln['held_high'] is None else ln['held_high']}"})
    return rows


def piece_t742(t742, i75):
    rows = []
    for x in t742["runs"]:
        lid = R.resolve(x["candidate_line"], i75.keys())
        if i75[lid]["item_code"] != "STR.CONC.PARAPET":
            raise R.ReadinessError(f"{lid}: T-742 run not on a parapet line")
        rows.append({"source": "T-742", "piece": "T-742", "row": f"T-742:{x['chain']}:{x['run']}", "hub": "",
                     "package": HUB_PACKAGE[""], "unit": "m", "live": "LIVE", "target": lid, "host_line_id": lid,
                     "host_status": "UNCHANGED", "moved_by": [], "action": "STATEMENT", "blockers": [],
                     "cleared": [], "after": f"run census {x['census']}; centreline {x['centreline_m']} m; "
                                             f"h {x['h_above_finish_m']} ({x['h_status']}); RC reading stays on "
                                             "the concrete line (never in both trades)"})
    for chain, v in sorted(t742["family_lines"].items()):
        lo, hi = (s.strip() for s in v["net_m2"].split(".."))
        R.add_family("B9-05", chain, None, True, lo, hi)
        rows.append({"source": "T-742", "piece": "T-742", "row": f"T-742:B9-05:{chain}", "hub": "B9-05",
                     "package": HUB_PACKAGE["B9-05"], "unit": "m2", "live": "LIVE", "target": f"B9-05@{chain}",
                     "host_line_id": "", "host_status": "NO_HOST", "moved_by": [], "action": "ADD_FAMILY",
                     "blockers": [], "cleared": [],
                     "after": f"HELD {lo} .. {hi} m2 ({v['runs']} runs; m3 {v['m3']}); held on {v['designer_item']}"})
    return rows


def piece_t733(t733, i75):
    rows = []
    for x in t733["a_tread_highs"]["lines"]:
        lid = R.resolve(x["line_id"], i75.keys())
        rows.append({"source": "T-733", "piece": "T-733", "row": f"T-733:{x['element_id']}", "hub": "H3S",
                     "package": HUB_PACKAGE["H3S"], "unit": "m2", "live": "LIVE", "target": lid,
                     "host_line_id": lid, "host_status": "UNCHANGED", "moved_by": [],
                     "action": "KEEP" if x["change"] == "none" else "CHANGE", "blockers": [], "cleared": [],
                     "after": f"{x['verdict']}: own one set {x['own_one_set_m2']} vs candidate {x['candidate_m2']} m2"})
    return rows


def piece_t734(t734, dg_doc, i75, applied):
    rows = []
    for x in t734["census"]["measurable_now"]:
        missing = str(x["key"]).startswith("MISSING:")
        lid = None if missing else R.resolve(x["key"], i75.keys())
        rows.append({"source": "T-734", "piece": "T-734", "row": f"T-734:{x['element']}", "hub": "H4",
                     "package": HUB_PACKAGE["H4"], "unit": x["unit"], "live": "LIVE", "target": lid or x["key"],
                     "host_line_id": lid or "", "host_status": "NO_HOST" if missing else "UNCHANGED", "moved_by": [],
                     "action": "ADD" if missing else "CHANGE",
                     "blockers": [], "cleared": [], "after": f"MEASURABLE_NOW: {str(x['after'])[:140]}"})
    dgr, findings = R.downgrade_rows(dg_doc["downgrades"], i75, applied, CITED_DG_IDS)
    for d in dgr:
        rows.append({"source": "T-734", "piece": "T-734 / Checker record", "row": f"{d['downgrade_id']}:{d['line_id']}",
                     "hub": "H4", "package": HUB_PACKAGE["H4"], "unit": d["unit"], "live": "LIVE",
                     "target": d["line_id"], "host_line_id": d["line_id"], "host_status": "UNCHANGED", "moved_by": [],
                     "action": "DOWNGRADE", "blockers": [], "cleared": [],
                     "after": f"{d['index_class']} {d['engine_qty']} -> {d['state']} ({d['status']})"})
    return rows, findings


def piece_t735(t735, i75, pkg):
    ids = set()

    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k in ("line_id", "line") and isinstance(v, str) and v.startswith("L-"):
                    ids.add(v)
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(t735)
    rows = []
    for c in sorted(ids):
        lid = R.resolve(c, i75.keys())
        rows.append({"source": "T-735", "piece": "T-735", "row": f"T-735:{lid}", "hub": "T-729",
                     "package": HUB_PACKAGE["T-729"], "unit": i75[lid]["unit"], "live": "LIVE", "target": lid,
                     "host_line_id": lid, "host_status": "UNCHANGED", "moved_by": [],
                     "action": "WIRED_RESTATED" if lid in pkg else "UNWIRED_AFTER_MERGE", "blockers": [],
                     "cleared": [], "after": "decider form (R-T735-1 / -2), carried by T-729 by declared precedence"})
    return rows


def piece_t737(t737, i75):
    rows = []
    for x in t737["line_census"]:
        new = x["action"] == "ADD"
        lid = None if new else R.resolve(x["key"], i75.keys())
        if new and x["key"] in i75:
            raise R.ReadinessError(f"{x['key']}: T-737 ADD key already a candidate line")
        rows.append({"source": "T-737", "piece": "T-737", "row": f"T-737:{x['element_id']}", "hub": "FACADE",
                     "package": HUB_PACKAGE["FACADE"], "unit": (x.get("host_now") or {}).get("unit") or "m2",
                     "live": "LIVE", "target": x["key"], "host_line_id": lid or "",
                     "host_status": "UNCHANGED" if lid else "NO_HOST", "moved_by": [], "action": x["action"],
                     "blockers": ["WAITS T-314 (QUEUED): T-314 r3 stage carries the face rows (renumbered at claim)"],
                     "cleared": [], "after": after_text(x.get("after"))})
    return rows


def piece_t708(text, i75):
    rows = []
    for n, x in enumerate(csv.DictReader(io.StringIO(text)), 1):
        cited = x["line_id"]
        if cited.startswith("NEW (split of "):          # a new line split from a named parent: parent must exist
            R.resolve(cited[len("NEW (split of "):].rstrip(")"), i75.keys())
            cited = ""
        lid = R.resolve(cited, i75.keys()) if cited else None
        rows.append({"source": "T-708", "piece": "T-708", "row": f"T-708:{x['scenario']}:{n}:{x['element_id']}",
                     "hub": "H5", "package": HUB_PACKAGE["H5"], "unit": "m3", "live": "LIVE",
                     "target": lid or f"{x['family']}@{x['element_id']}", "host_line_id": lid or "",
                     "host_status": "UNCHANGED" if lid else "NO_HOST", "moved_by": [],
                     "action": ("CHANGE" if lid else "BESIDE") if x["scenario"] == "A" else "SCENARIO",
                     "blockers": [], "cleared": [],
                     "after": f"scenario {x['scenario']}: {x['state']} {x['high_qualifier']} {x['high_end_m3']} "
                              f"m3 ({x['quantity'][:60]})"})
    return rows


def piece_t743(t743):
    rows = []
    for kind, n in sorted(t743["totals_measured"].items()):
        rows.append({"source": "T-743", "piece": "T-743", "row": f"T-743:B12-01:{kind}", "hub": "B12-01",
                     "package": HUB_PACKAGE["B12-01"], "unit": "pcs", "live": "LIVE", "target": f"B12-01@{kind}",
                     "host_line_id": "", "host_status": "NO_HOST", "moved_by": [], "action": "ADD_FAMILY",
                     "blockers": ["OWNER ORDER 2026-11-09: MEP last"], "cleared": [], "after": f"MEASURED {n} pcs"})
    for kind, n in sorted(t743["held"].items()):
        rows.append({"source": "T-743", "piece": "T-743", "row": f"T-743:B12-01:{kind}", "hub": "B12-01",
                     "package": HUB_PACKAGE["B12-01"], "unit": "pcs", "live": "LIVE", "target": f"B12-01@{kind}",
                     "host_line_id": "", "host_status": "NO_HOST", "moved_by": [], "action": "ADD_FAMILY",
                     "blockers": ["OWNER ORDER 2026-11-09: MEP last"], "cleared": [],
                     "after": f"HELD BLANK ({n} named, not counted)"})
    return rows


def build():
    i73 = {l["line_id"]: l for l in load("index73")["lines"]}
    i74doc, i75doc = load("index74"), load("index75")
    i74 = {l["line_id"]: l for l in i74doc["lines"]}
    i75 = {l["line_id"]: l for l in i75doc["lines"]}
    if i75doc["candidate_version"] != "ARCH_TAKEOFF_V3.0.75":
        raise R.ReadinessError("not the candidate of record")
    t717, t729 = load("t717"), load("t729")
    pkg = {"t717": {r["line_id"] for r in t717["rows"]}, "t729": {r["line_id"] for r in t729["rows"]}}
    # ADD rows are wired by key: T-717 rows carry the T-730 row id as map_row; T-729 C10 children carry the strip
    # name after '#' in their index element id (a key is matched exactly, never by a neighbour)
    pkg["t717_keys"] = {r["map_row"] for r in t717["rows"] if r["change"] == "ADD"}
    added729 = {r["line_id"] for r in t729["rows"] if r["change"] == "ADD"}
    pkg["t729_keys"] = {i75[l]["element_id"].split("#")[-1] for l in added729}
    movers = defaultdict(set)
    for k, rows in (("T-717", t717["rows"]), ("T-729", t729["rows"])):
        for r in rows:
            movers[r["line_id"]].add(k)
    # every line moved V3.0.73 -> V3.0.75 is named by one of the two packages (else host_status fails per row)
    for lid, ln in i75.items():
        if lid in i73 and i73[lid] != ln and lid not in movers:
            raise R.ReadinessError(f"{lid}: moved V3.0.73 -> V3.0.75 with no package row")
    applied = {x["downgrade_id"] for x in i75doc["downgrades"] if x["status"] == "APPLIED"}

    old = restate_t730(load("t730"), i73, i75, movers, pkg)
    dg_rows, dg_findings = piece_t734(load("t734"), load("board_dg"), i75, applied)
    new = (piece_t740(load("t740"), i75) + piece_t742(load("t742"), i75) + piece_t733(load("t733"), i75) +
           dg_rows + piece_t735(load("t735"), i75, pkg["t729"]) + piece_t737(load("t737"), i75) +
           piece_t708(load("t708", raw=True), i75) + piece_t743(load("t743")))
    rows = old + new
    keys = Counter((r["source"], r["row"]) for r in rows)
    dup = [k for k, n in keys.items() if n > 1]
    if dup:
        raise R.ReadinessError(f"row listed twice: {dup[:3]}")

    # rule 6 over every row that still moves something (wired / merged-hub rows excluded)
    live_moving = [r for r in rows if r["action"] in R.MOVING and r["live"] == "LIVE"
                   and r["hub"] not in MERGED_PACKAGE_HUBS and r["target"]]
    own = R.one_hub_per_target([{"target": r["target"], "hub": r["package"], "action": r["action"]}
                                for r in live_moving])
    shared_lines = defaultdict(set)     # same target, same package, two pieces: listed for the package (not a fault)
    for r in live_moving:
        shared_lines[r["target"]].add(r["piece"])
    shared = {t: sorted(p) for t, p in shared_lines.items() if len(p) > 1}

    # packages
    pk = defaultdict(lambda: {"rows": 0, "moving": 0, "targets": set(), "by_action": Counter(), "blockers": Counter(),
                              "host_changed": 0, "pieces": Counter()})
    for r in rows:
        p = pk[r["package"]]
        p["rows"] += 1
        p["by_action"][r["action"]] += 1
        p["pieces"][r["piece"]] += 1
        if r in live_moving:
            p["moving"] += 1
            p["targets"].add(r["target"])
            for b in r["blockers"]:
                p["blockers"][b.split(" (")[0].split(":")[0]] += 1
        if r["host_status"] == "HOST_CHANGED":
            p["host_changed"] += 1
    packages = {k: {"rows": v["rows"], "moving_live_rows": v["moving"], "targets": len(v["targets"]),
                    "by_action": dict(sorted(v["by_action"].items())), "open_blockers": dict(sorted(v["blockers"].items())),
                    "host_changed": v["host_changed"], "pieces": dict(sorted(v["pieces"].items()))}
                for k, v in sorted(pk.items())}
    findings = {
        "F-T748-1": "issued Checker record not applied by the index of record: " + "; ".join(
            f"{r['row']} {r['after']}" for r in dg_rows if r["action"] == "DOWNGRADE" and "NOT_APPLIED" in r["after"]),
        "F-T748-2": dg_findings,
        "unwired_after_merge": [f"{r['source']}:{r['row']}" for r in rows if r["action"] == "UNWIRED_AFTER_MERGE"],
        "host_changed": [f"{r['source']}:{r['row']} {r['host_line_id']} by {','.join(r['moved_by'])}"
                         for r in rows if r["host_status"] == "HOST_CHANGED" and r["hub"] not in MERGED_PACKAGE_HUBS],
        "released_changes": [f"{r['row']} {r.get('index', '')} -> {r['after'][:60]}" for r in rows
                             if r["action"] == "CHANGE_RELEASED"],
        "no_package_row": sorted({r["hub"] for r in live_moving if r["package"] == "NO_PACKAGE_ROW"}),
    }
    return {
        "schema": "URBAN_T748_READINESS_V1", "task": "T-748 (a)", "rule": f"{R.RULE_ID} {R.RULE_VERSION}",
        "base_rules": [f"{a} {b}" for a, b in R.BASE_RULES],
        "candidate": "ARCH_TAKEOFF_V3.0.75 (NOT RELEASED), lines sha " + t729["lines_sha256"]["75"][:8],
        "inputs": {k: {"path": v[0], "sha256": v[1]} for k, v in PIN.items()}, "board_states": BOARD,
        "hub_package": HUB_PACKAGE,
        "stale": 0, "rows": len(rows), "rows_t730_restated": len(old), "rows_new_pieces": len(new),
        "by_source_action": {f"{s} {a}": n for (s, a), n in sorted(Counter((r["source"], r["action"]) for r in rows).items())},
        "host_status": dict(sorted(Counter(r["host_status"] for r in rows).items())),
        "blockers_cleared": sum(len(r["cleared"]) for r in rows),
        "one_hub_per_target": {"targets": len(own), "double_count_across_hubs": 0,
                               "same_package_two_pieces": shared},
        "packages": packages, "findings": findings,
        "not_claimed": "readiness map only: nothing wired, released or measured; development villa",
        "row_list": rows,
    }


FIELDS = ("source", "piece", "row", "hub", "package", "action", "action_t730", "live", "unit", "target",
          "host_line_id", "host_status", "moved_by", "blockers", "cleared", "after")


def to_csv(rows):
    s = io.StringIO()
    w = csv.DictWriter(s, fieldnames=FIELDS, extrasaction="ignore", lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: ("; ".join(r.get(k) or []) if isinstance(r.get(k), list) else r.get(k, "")) for k in FIELDS})
    return s.getvalue()


def dumps(b):
    return json.dumps(b, ensure_ascii=False, indent=1, sort_keys=True) + "\n"


def main(argv):
    b = build()
    j, c = dumps(b), to_csv(b["row_list"])
    if "--write" in argv:
        OUT.mkdir(exist_ok=True)
        JSON_OUT.write_text(j, encoding="utf-8")
        CSV_OUT.write_text(c, encoding="utf-8")
        print("written", JSON_OUT.name, CSV_OUT.name)
        return 0
    if "--check" in argv:
        ok = JSON_OUT.read_text(encoding="utf-8") == j and CSV_OUT.read_text(encoding="utf-8") == c
        print("check", "OK" if ok else "DIFFERS")
        return 0 if ok else 1
    print(json.dumps({k: v for k, v in b.items() if k not in ("row_list", "inputs")}, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
