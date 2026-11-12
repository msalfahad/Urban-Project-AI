"""T-722: the URBAN_V3073_INPUTS_V1 project inputs of ARCH_TAKEOFF_V3.0.73 (engine.source.arch_v3073), built ONLY from
Checker-merged files, each pinned by sha256 (an edited file stops the build) and each ledger REBUILT by its own merged
builder and asserted equal to the committed file:

  research/agents_t707/out/T707_COLUMN_TAIL.json  T-707 (MERGED f34a5baa, Verifier 2026-11-11T15:58Z Gate A PASS, own
      ST re-measure of the B8 plate / panel adjacency): R-T707-1 plate transfer (5 column lows) and R-T707-2 tank
      columns LOWER_ONLY (2 lines);
  research/agents_t711/out/T711_LEDGER.json       T-711 (MERGED 1e06f656, Verifier 2026-11-11T17:58Z Gate A PASS, own
      re-measure of the lift pit / parapets / stairs): the blank concrete tail (11 AT_LEAST, 4 named);
  research/agents_t712/out/T712_LEDGER.json       T-712 (MERGED dfeb0240, Verifier 2026-11-11T20:55Z Gate A PASS, own
      ST re-measure by handle): ground-beam floors (17 AT_LEAST, 3 court lines named);
  research/agents_t721/out/T721_LEDGER.json       T-721 (MERGED 9e1ed6c5, Verifier 2026-11-11T22:05Z Gate A PASS, own
      ST re-measure of the east ring): east dome ring AT_LEAST, 11 edge projections named;
  research/agents_t723/out/T723_READINESS.json    T-723 (MERGED 5d00f738, Verifier 2026-11-11T23:51Z Gate A PASS): the
      line-by-line map of those four ledgers onto the candidate (R-T723-1): CHANGE / BESIDE / RESTATE_BESIDE / TEXT /
      KEEP per line, hub T-722 (54 rows);
  research/agents_t703/out/LINE_INDEX_V3_0_72.json T-703 (Gate B PASS, MERGED da1a8906): class and range of each line on
      the candidate of record V3.0.72 (the binding; asserted again on the live run).

Map (T-723 action -> V3.0.73 action): CHANGE -> NARROW (low recomputed from its terms); BESIDE -> AT_LEAST;
RESTATE_BESIDE -> AT_LEAST with `restates` (the earlier V3.0.63 figure named, F-T723-1); TEXT -> NAMED; KEEP ->
`confirm` (the same figure is already beside: asserted on the live line, never restated).

    python3 -I research/agents_t722/t722_inputs.py [project_id]      # prints the inputs summary
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
for p in (ROOT, HERE):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

R = "research"
F707 = ROOT / R / "agents_t707/out/T707_COLUMN_TAIL.json"
F711 = ROOT / R / "agents_t711/out/T711_LEDGER.json"
F712 = ROOT / R / "agents_t712/out/T712_LEDGER.json"
F721 = ROOT / R / "agents_t721/out/T721_LEDGER.json"
F723 = ROOT / R / "agents_t723/out/T723_READINESS.json"
INDEX = ROOT / R / "agents_t703/out/LINE_INDEX_V3_0_72.json"
PINS = {F707: "f8feb9bfbbc4e96912b735d10e1d786845c1e6aff1776910a13b77fda4134a0c",
        F711: "36cd106334645d92f2d441434201dc99017e879a32656dd39a57494b49deee36",
        F712: "9d2bbd78d5a40b168db557900730e314beafec4c8dd5766234cdf3113d83bcd6",
        F721: "76b09766541b9049ff7d5cb86cd6fc27dba3fc4044a638600971bb0bab36293f",
        F723: "b016f62d0871f085e74f9efe38ef2a146989c18c1b7ca1a971c91fe356adf827",
        INDEX: "8e753204d90ebf75d8fa5fe3de120f235bdb16e06a7d677e6aeb615e84ef5d2b"}
BUILDERS = {"T-707": ("agents_t707", "t707_alsenan", F707), "T-711": ("agents_t711", "t711_alsenan", F711),
            "T-712": ("agents_t712", "t712_alsenan", F712), "T-721": ("agents_t721", "t721_alsenan", F721)}
CHECKER = {
    "T-707": ("f34a5baa", "Verifier 2026-11-11T15:58Z Gate A PASS (own ST decode 9f9d1179: B8 outline, 7 panels, T 18 "
                          "in P1 / P2, column adjacency 418 / 41E / 778 -> 12.917, 41B / 421 / 40F / 424 -> 12.937)"),
    "T-711": ("1e06f656", "Verifier 2026-11-11T17:58Z Gate A PASS (own re-measure: lift pit walls AT_LEAST 1.903 "
                          "AGREE, parapets / stairs / necks by hand; research only, nothing VERIFIED)"),
    "T-712": ("dfeb0240", "Verifier 2026-11-11T20:55Z Gate A PASS (own ST decode 9f9d1179 by handle: L-402dbe61 "
                          "9.700 x 0.300 x 0.25 = 0.727500 AGREE, junction L-be6708e0 0.03 x 0.25 = 0.007500 AGREE)"),
    "T-721": ("9e1ed6c5", "Verifier 2026-11-11T22:05Z Gate A PASS (own ST decode 9f9d1179: east ring 1.799403 m2, "
                          "least 1.7993 x 0.064 = 0.115155 AGREE; 11 projections named)"),
    "T-723": ("5d00f738", "Verifier 2026-11-11T23:51Z Gate A PASS (map rebuilt by --check; 54 T-722 rows; findings "
                          "F-T723-1 .. -3 adopted in the T-722 row by the Lead 2026-11-12 00:16)"),
}
SCHEMA = "URBAN_V3073_INPUTS_V1"
HUB = "T-722"
V63 = "concrete_ledger_v3063"          # the record carrying the T-665 (V3.0.63) figures F-T723-1 names
RESTATE_RE = re.compile(r"^beside AT_LEAST ([0-9.]+) -> AT_LEAST ([0-9.]+)$")
X = Decimal


def _sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _load():
    for p, s in PINS.items():
        if _sha(p) != s:
            raise SystemExit(f"{p.relative_to(ROOT)}: sha256 {_sha(p)[:8]} is not the pinned {s[:8]} (edited file)")
    return {k: json.loads(p.read_text(encoding="utf-8")) for k, p in (("707", F707), ("711", F711), ("712", F712),
                                                                       ("721", F721), ("723", F723),
                                                                       ("index", INDEX))}


def rebuild_ledgers():
    """each merged ledger rebuilt by its own merged builder, equal to the committed file (field by field)"""
    out = {}
    for task, (folder, mod, path) in BUILDERS.items():
        d = str(ROOT / R / folder)
        if d not in sys.path:
            sys.path.insert(0, d)
        m = __import__(mod)
        got = json.loads(json.dumps(m.build(), sort_keys=True, default=str))
        if got != json.loads(json.dumps(json.loads(path.read_text(encoding="utf-8")), sort_keys=True)):
            raise SystemExit(f"{task}: the merged builder does not reproduce {path.name}")
        out[task] = True
    return out


def _sources():
    files = {"T-707": F707, "T-711": F711, "T-712": F712, "T-721": F721, "T-723": F723}
    return {t: {"task": t, "file": str(p.relative_to(ROOT)), "sha256": PINS[p], "merge_commit": CHECKER[t][0],
                "checker_run": CHECKER[t][1]} for t, p in files.items()}


def _expect(x):
    return {"item_code": x["item_code"], "element_id": x["element_id"], "unit": x["unit"], "class": x["class"],
            "low": x["held_low"], "high": x["held_high"]}


def _f(s):
    return None if s is None else float(X(str(s)))


def _ledger_rows(d):
    out = {}
    for k, key in (("707", "lines"), ("711", "lines"), ("712", "lines"), ("721", "rows")):
        for r in d[k][key]:
            if r["line_id"] in out:
                raise SystemExit(f"{r['line_id']}: in two ledgers")
            out[r["line_id"]] = (f"T-{k}", r)
    return out


def _question(item, member):
    return f"DESIGNER ITEM {item} ({member})"[:400]


def build(project_id=None):
    d = _load()
    if d["index"]["candidate_version"] != "ARCH_TAKEOFF_V3.0.72":
        raise SystemExit("candidate of record moved (expected V3.0.72)")
    ix = {r["line_id"]: r for r in d["index"]["lines"]}
    led = _ledger_rows(d)
    rows = [r for r in d["723"]["rows"] if r.get("hub") == HUB]
    if len(rows) != 54:
        raise SystemExit(f"T-723 hub {HUB}: {len(rows)} rows, expected 54")
    if {r["host_line_id"] for r in rows} != set(led):
        raise SystemExit("the T-723 hub rows are not exactly the four ledgers' lines")
    ents, confirm = [], []
    for r in rows:
        lid, act = r["host_line_id"], r["action"]
        task, L = led[lid]
        if r["piece"] != task or r["live"] != "LIVE":
            raise SystemExit(f"{lid}: T-723 row {r['piece']} {r['live']} is not the live {task} row")
        x = ix[lid]
        if x["class"] != "HELD" or x["measured_net"] is not None:
            raise SystemExit(f"{lid}: not HELD on V3.0.72")
        item = L["item"]
        member = L.get("member") or x["element_id"]
        base = {"line_id": lid, "source_tasks": [task, "T-723"], "expect": _expect(x), "member": member,
                "item": item, "question": _question(item, member), "t723_action": act}
        if act == "CHANGE":
            if task != "T-707" or L["kind"] != "PLATE":
                raise SystemExit(f"{lid}: CHANGE only from a T-707 plate row")
            lo0, hi0 = (_f(v) for v in L["before"])
            lo1, hi1 = (_f(v) for v in L["after"])
            if abs(lo0 - x["held_low"]) > 1e-9 or abs(hi0 - x["held_high"]) > 1e-9:
                raise SystemExit(f"{lid}: ledger before {lo0} .. {hi0} is not V3.0.72's {x['held_low']} .. "
                                 f"{x['held_high']}")
            a = r["after"]
            if abs(a["low"] - lo1) > 1e-9 or abs(a["high"] - hi1) > 1e-9:
                raise SystemExit(f"{lid}: T-723 after is not the ledger's")
            ents.append(dict(base, action="NARROW",
                             basis=(f"R-T707-1 plate transfer: slab top >= {L['top_lo']} on one plane (panel "
                                    f"{L['governing_panel']}, panels {', '.join(L['panels_touched'])}); h >= "
                                    f"{L['h_lo']} m x least section {min(_f(v) for v in L['areas_m2']):g} m2"),
                             terms={"kind": L["kind"], "areas_m2": list(L["areas_m2"]), "h_lo_m": L["h_lo"],
                                    "top_lo_m": L["top_lo"], "panel": L["governing_panel"],
                                    "handle": L["handle"]},
                             after={"low": L["after"][0], "high": L["after"][1]},
                             delta_low_m3=L["delta_low_m3"]))
        elif act in ("BESIDE", "RESTATE_BESIDE"):
            if task == "T-707":
                if L["kind"] != "TANK" or L["after"][1] is not None:
                    raise SystemExit(f"{lid}: BESIDE from T-707 only for a LOWER_ONLY tank row")
                v = L["after"][0]
                hand = (f"least section {min(_f(s) for s in L['areas_m2']):g} m2 x h >= {L['h_lo']} m (slab top >= "
                        f"{L['top_lo']}, panel {L['governing_panel']})")
                basis = "R-T707-2: tank column lower end; " + "; ".join(f"{k}: {w}" for k, w in L["beside"].items())
            else:
                if L["bound"] != "AT_LEAST":
                    raise SystemExit(f"{lid}: {task} bound {L['bound']} is not AT_LEAST")
                v = L["at_least_m3"]
                hand = L.get("hand") or ""
                basis = f"{task} {L.get('basis') or 'R-' + task + '-1'}: {item}"
            if abs(_f(v) - r["after"]["value"]) > 1e-9 or r["after"]["side"] != "AT_LEAST":
                raise SystemExit(f"{lid}: T-723 figure {r['after']} is not the ledger's {v}")
            e = dict(base, action="AT_LEAST", basis=basis, beside={"value": v, "basis": basis[:400], "hand": hand})
            if L.get("freelancer"):
                e["freelancer_beside"] = L["freelancer"]
            if act == "RESTATE_BESIDE":
                m = RESTATE_RE.match(r["action_reason"])
                if not m or X(m.group(2)) != X(str(v)):
                    raise SystemExit(f"{lid}: restatement text {r['action_reason']!r}")
                e["restates"] = {"record": V63, "value": m.group(1),
                                 "why": f"F-T723-1: {task} re-measured the same member ({m.group(1)} -> {v} m3; "
                                        f"R-T696-1 floors an AT_LEAST / re-measured area)"}
            ents.append(e)
        elif act == "TEXT":
            if L.get("bound") != "BLANK_NAMED":
                raise SystemExit(f"{lid}: TEXT only from a BLANK_NAMED ledger row")
            pu = L.get("per_unit") or (f"{L['m3_per_m_depth']} m3 per m of depth" if L.get("m3_per_m_depth")
                                       else None)
            if isinstance(L.get("m3_per_m_depth"), list):
                pu = " / ".join(L["m3_per_m_depth"]) + " m3 per m of depth (readings)"
            ents.append(dict(base, action="NAMED", basis=f"{task} {L.get('basis') or 'BLANK_NAMED'}: {item}",
                             why=L.get("why") or f"{item}: no positive drawn minimum (BLANK_NAMED)",
                             per_unit=pu))
        elif act == "KEEP":
            a = r["after"]
            v = L.get("at_least_m3")
            if a["side"] != "AT_LEAST" or v is None or abs(_f(v) - a["value"]) > 1e-9:
                raise SystemExit(f"{lid}: KEEP figure {a} is not the ledger's {v}")
            confirm.append({"line_id": lid, "kind": "AT_LEAST_M3", "value": a["value"], "source_task": task})
        else:
            raise SystemExit(f"{lid}: T-723 action {act!r} is not wired by T-722")
    srcs = _sources()
    return {"schema": SCHEMA, "project_id": project_id, "sources": list(srcs.values()), "entries": ents,
            "confirm": confirm}


def summary(doc):
    by = {}
    for e in doc["entries"]:
        by[e["action"]] = by.get(e["action"], 0) + 1
    return {"entries": len(doc["entries"]), "by_action": by, "confirm": len(doc["confirm"]),
            "restates": [(e["line_id"], e["restates"]["value"], e["beside"]["value"]) for e in doc["entries"]
                         if e.get("restates")]}


if __name__ == "__main__":
    print(json.dumps(rebuild_ledgers()))
    print(json.dumps(summary(build(sys.argv[1] if len(sys.argv) > 1 else None)), indent=1))
