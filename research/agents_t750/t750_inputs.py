"""T-750 (lane I, hub H4, owner gap order 2026-11-13: waterproofing + roof): the inputs of ARCH_TAKEOFF_V3.0.80
(URBAN_V3080_INPUTS_V1), built ONLY from Checker-merged ledgers (sha256-pinned below) as mapped by the merged T-748
readiness round 6 (R-T748-1, hub H4, package NO_PACKAGE_ROW), checked against the line index of the candidate it stacks
on: ARCH_TAKEOFF_V3.0.79 (T-314 r3, READY Gate B on 597d2820, itself on T-738 r2 V3.0.78). Nothing here opens a drawing
or forms a quantity: every figure is a merged ledger's, and each is asserted equal to the T-748 map's after-text.

  WP_WIRE    T-691 (MERGED 5e4fdc33) penetrations (17 lines: 5 points, 12 bounds; and the pantry's own), the pantry wall
             upturn bound, the three pantry pieces no line carries; T-734 (MERGED 3d8185fe) re-states the five firm
             counts and the four pantry MISSING rows on V3.0.73 (same figures, asserted); T-710 (MERGED 4a34ced0) /
             T-734 name the pantry doorway transition m2 DESIGNER (printed nowhere): added HELD blank.
  ROOF_WIRE  T-702 part (a) (MERGED b90d85af): the three falls-screed lower ends beside, the insulation (D-39) and
             protection (carried by the Q-41 screed) causes, and the four 2F top roof lines held on owner Q-34.

The rows of the H4 map this package does NOT wire are statements (every one named, nothing dropped): T-710 duplicates
of the T-691 rows, T-710 / T-691 state-only rows (DESIGNER / NEEDS_OWNER_RULE / NO_PHYSICAL_ELEMENT), the T-702 KEEP
finish rows (released), the roof membrane downgrade (carried by V3.0.76: the line is HELD at its band on V3.0.79), the
roof upturn raise and the pool-court ledge / upturn rows below the owner's 1 % materiality (IGNORED_SMALL with size).

    python3 -I research/agents_t750/t750_inputs.py [--check] [--write]
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = HERE / "out" / "T750_WIRE_TABLE.json"
SCHEMA = "URBAN_V3080_INPUTS_V1"
PID = "development-villa-t131"
INDEX = "research/agents_t314/out/LINE_INDEX_V3_0_79.json"
T748 = "research/agents_t748/out/T748_ROWS.csv"
T691 = "research/agents_t691/out/T691_WP_ROUND2.json"
T702 = "research/agents_t702/out/T702_TILES_ROUND3.json"
T710 = "research/agents_t710/out/T710_WP_ROUND3.json"
T734 = "research/agents_t734/out/T734_WP_H4_EVIDENCE.json"
PINS = {INDEX: "0582aac58defff74", T748: "f403d34bac956720", T691: "2e190feefd0bd16c", T702: "ae5b37e75a1635cb",
        T710: "9aa528c5d47b115c", T734: "d39d93fd0eda7554"}
SOURCES = {
    "T-691": {"file": T691, "merge_commit": "5e4fdc33",
              "checker_run": "Verifier 2026-11-11T04:56Z GATE A PASS (session_01E6cPnbaQxGo5z2sdX4XzTJ)"},
    "T-702": {"file": T702, "merge_commit": "b90d85af",
              "checker_run": "Verifier 2026-11-11T12:01Z GATE A PASS (session_01E6cPncdZEPbJjz2ey34pSg)"},
    "T-710": {"file": T710, "merge_commit": "4a34ced0",
              "checker_run": "Verifier 2026-11-11T16:00Z GATE A PASS (session_01E6cPnbetLVMWhmyYGDMXxx)"},
    "T-734": {"file": T734, "merge_commit": "3d8185fe", "checker_run": "Verifier 2026-11-12T09:58Z GATE A PASS"},
    "T-748": {"file": T748, "merge_commit": "071dc837", "checker_run": "Verifier 2026-11-12T17:58Z GATE A PASS on aa09b3ff"},
}
PANTRY, PANTRY_FLOOR = "GF-RC99C2A", "GF"
# template lines of the same code (never summed into; the added line is its own room's): a GF line of each code
HOSTS = {"FIN.WP.DOORWAY": "L-e18901e01bc3d7a3fbd4", "FIN.WP.DOORWAY_TRANSITION_NR": "L-926a7a01b22bb6dba63e",
         "FIN.WP.TERMINATION": "L-9592048116294937ab6f", "FIN.WP.PENETRATION": "L-6375385673176b8b2c9c",
         "FIN.WP.DOORWAY_TRANSITION": "L-65194e5d4497f0882024"}
N_PEN, N_ROOF = 17, 13
# owner materiality 2026-11-13 (Lead row: 'rows whose change is below 1 % of their line are NOT worked')
IGNORED_SMALL = {
    "L-5ce5ba49792e8f9d1f6f": "roof upturn 2F 92.922 -> 92.925396 lm (+0.003396 lm, 0.004 %; a raise of a released "
                              "value, no record): stays RELEASED 92.922",
    "L-2361d6ec13c952bd2ae3": "pool-court ledge membrane 0 .. 0.639573 m2 (T-529 0.639573): left as it is",
    "L-d7d1bf8c5991ccf69ea2": "pool-court ledge upturn 0 .. 3.528277 lm (T-522 / T-529 0.551614): left as it is",
    "L-1954878bb02c91139e1b": "pool-court window-run upturn 0 .. 0.500002 lm (T-522 0.500002): left as it is",
}
T734_ADD_KEYS = {"MISSING:FIN.WP.DOORWAY[m2]/DOOR:D-GF-07-PANTRY/THRESHOLD_FLOOR": "0.200",
                 "MISSING:FIN.WP.DOORWAY_TRANSITION_NR[pcs]/DOOR:D-GF-07-PANTRY/TRANSITION": "1",
                 "MISSING:FIN.WP.TERMINATION[lm]/GF-07:OPEN_SIDE_DINING/MEMBRANE_EDGE": "4.500",
                 "MISSING:FIN.WP.PENETRATION[pcs]/GF-07/FLOOR_PENETRATIONS": "1 .. 1"}
D = Decimal


class InputsError(ValueError):
    pass


def sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def load(p):
    got = sha(p)
    if not got.startswith(PINS[p]):
        raise InputsError(f"{p}: sha256 {got[:16]} is not the pinned {PINS[p]} (stale input)")
    t = (ROOT / p).read_text(encoding="utf-8")
    return json.loads(t) if p.endswith(".json") else list(csv.DictReader(t.splitlines()))


def _expect(x):
    if x is None:
        raise InputsError("a mapped line is not in the V3.0.79 index (stale)")
    if x["class"] != "HELD" or x["measured_net"] is not None:
        raise InputsError(f"{x['line_id']}: {x['class']} on V3.0.79, not a HELD line (stale or released)")
    return {"item_code": x["item_code"], "element_id": x["element_id"], "unit": x["unit"], "class": "HELD",
            "low": x["held_low"], "high": x["held_high"]}


def _after(text):
    """T-748 'after' text -> (kind, numbers)"""
    t = (text or "").split()
    if not t:
        return None, []
    if t[0] == "VALUE":
        return "VALUE", [D(t[2])]
    if t[0] == "BOUND":
        return "BOUND", ([D(t[2]), D(t[4])] if len(t) > 4 and t[3] == "high" else [D(t[2])])
    return t[0], []


def h4_rows():
    rs = [r for r in load(T748) if r["hub"] == "H4" and r["package"] == "NO_PACKAGE_ROW"]
    if len(rs) != 113:
        raise InputsError(f"T-748 H4 rows {len(rs)}, expected 113")
    return rs


def build():
    ix = {x["line_id"]: x for x in load(INDEX)["lines"]}
    t691, t702, t734 = load(T691), load(T702), load(T734)
    load(T710)                                                              # pinned: the DESIGNER transition row
    rows = h4_rows()
    live = {}
    for r in rows:
        if r["live"] == "LIVE" and r["action"] in ("CHANGE", "ADD", "TEXT", "KEEP"):
            live.setdefault(r["host_line_id"] or r["target"], []).append(r)
    entries, statements, used = [], [], set()

    def mark(key, piece):
        rs = [r for r in live.get(key, []) if r["piece"].startswith(piece)]
        if not rs:
            raise InputsError(f"{key}: no live T-748 H4 row of {piece} (map and ledger disagree)")
        for r in rs:
            used.add(r["row"])
        return rs

    # ---- WP: penetrations (T-691 rows; T-734 re-states the five firm counts)
    pens = [r for r in t691["penetrations"]["rows"] if r["line"].startswith("L-")]
    if len(pens) != N_PEN:
        raise InputsError(f"{len(pens)} T-691 penetration lines, expected {N_PEN}")
    for r in pens:
        lid, lo, hi = r["line"], D(str(r["after_low"])), D(str(r["after_high"]))
        x = ix.get(lid)
        ex = _expect(x)
        if ex["item_code"] != "FIN.WP.PENETRATION" or not ex["element_id"].startswith(r["room"] + ":"):
            raise InputsError(f"{lid}: V3.0.79 {ex} is not T-691's {r['room']} penetration line")
        m = mark(lid, "T-691")[0]
        kind, nums = _after(m["after"])
        if (kind == "VALUE" and nums != [lo]) or (kind == "BOUND" and nums != [lo, hi]) or lo > hi:
            raise InputsError(f"{lid}: T-748 map {m['after']} is not T-691 {lo} .. {hi}")
        tasks = ["T-691", "T-748"]
        if lid in {rr["host_line_id"] for rr in live.get(lid, []) if rr["piece"] == "T-734"}:
            mark(lid, "T-734")
            tasks.append("T-734")
        why = (f"{r['fd_printed']} floor drain(s) printed, {r['wc_drawn']} W.C. pan(s) drawn ({r['note'] or 'T-691'})"
               if r["status"] == "MEASURED" else
               f"{r['fd_printed']} floor drain(s) printed + {r['wc_drawn']} W.C. pan outlet(s) open")
        e = {"piece": "WP_WIRE", "line_id": lid, "expect": ex, "source_tasks": tasks, "rule": "R-T691-3",
             "why": why[:400]}
        if lo == hi:
            e.update(action="POINT", value=float(lo), status="DRAWING-CONFIRMED", open="held until a Checker record "
                     "releases it (MEASURED count, T-691)")
        else:
            e.update(action="BOUND", low=float(lo), high=float(hi), status="HELD",
                     open=f"{r['open_term']}: {t691['penetrations']['missing_datum']}"[:400])
        entries.append(e)
    # ---- WP: measurable-now rows (the pantry wall upturn + three MISSING pieces)
    mn = {r["line"]: r for r in t691["measurable_now"]}
    up = mn["L-8090ff20f2b547d1bc96"]
    ex = _expect(ix.get("L-8090ff20f2b547d1bc96"))
    lo, hi = (D(v) for v in up["after"].split(" .. "))
    m = mark("L-8090ff20f2b547d1bc96", "T-691")[0]
    if _after(m["after"])[1] != [lo, hi]:
        raise InputsError("pantry wall upturn: T-748 map is not T-691")
    mark("L-8090ff20f2b547d1bc96", "T-734")
    entries.append({"piece": "WP_WIRE", "action": "BOUND", "line_id": "L-8090ff20f2b547d1bc96", "expect": ex,
                    "low": float(lo), "high": float(hi), "source_tasks": ["T-691", "T-734", "T-748"],
                    "rule": "R-T691-2", "status": "HELD", "why": up["source"][:400],
                    "open": up["status"]})
    adds = [("DOORWAY", "FIN.WP.DOORWAY", "m2", mn["MISSING FIN.WP.DOORWAY D-GF-07"], "R-T691-2"),
            ("TRANSITION_NR", "FIN.WP.DOORWAY_TRANSITION_NR", "pcs",
             mn["MISSING FIN.WP.DOORWAY_TRANSITION_NR D-GF-07"], "R-T691-2 (Q-35 C)"),
            ("TERMINATION", "FIN.WP.TERMINATION", "lm", mn["MISSING FIN.WP.TERMINATION GF-07 open side"],
             "R-T691-2 (Q-37 A)")]
    for key, code, unit, r, rule in adds:
        st = r["status"]
        status = ("ASSUMED — OWNER-APPROVED" if st.startswith("ASSUMED") else
                  "DRAWING-CONFIRMED" if st.startswith("DRAWING-CONFIRMED") else "HELD")
        for rr in mark(r["line"], "T-691"):
            if _after(rr["after"])[1] != [D(r["after"])]:
                raise InputsError(f"{r['line']}: T-748 map {rr['after']} is not T-691 {r['after']}")
        entries.append({"piece": "WP_WIRE", "action": "ADD_POINT", "add_key": key, "host_line_id": HOSTS[code],
                        "item_code": code, "unit": unit, "value": float(D(r["after"])), "room": PANTRY,
                        "floor": PANTRY_FLOOR, "item": f"{r['item']} of the GF pantry wet room (D-GF-07)",
                        "source_tasks": ["T-691", "T-734", "T-748"], "rule": rule, "status": status,
                        "status_text": st if status != "HELD" else None, "why": r["source"][:400],
                        "open": "held until a Checker record releases it"})
    pp = next(r for r in t691["penetrations"]["rows"] if r["room"] == PANTRY)
    for rr in mark("MISSING FIN.WP.PENETRATION GF-07", "T-691"):
        if _after(rr["after"])[1] != [D(str(pp["after_low"]))] or pp["after_low"] != pp["after_high"]:
            raise InputsError("pantry penetration: T-748 map is not T-691")
    entries.append({"piece": "WP_WIRE", "action": "ADD_POINT", "add_key": "PENETRATION",
                    "host_line_id": HOSTS["FIN.WP.PENETRATION"], "item_code": "FIN.WP.PENETRATION", "unit": "pcs",
                    "value": float(pp["after_low"]), "room": PANTRY, "floor": PANTRY_FLOOR,
                    "item": "floor penetration(s) of the GF pantry wet room", "source_tasks": ["T-691", "T-734", "T-748"],
                    "rule": "R-T691-3", "status": "DRAWING-CONFIRMED",
                    "why": f"{pp['fd_printed']} floor drain printed, {pp['wc_drawn']} W.C. drawn",
                    "open": "held until a Checker record releases it (MEASURED count, T-691)"})
    # T-734 re-states the four pantry MISSING rows on V3.0.73 under its own keys: same figures (asserted)
    for k, want in T734_ADD_KEYS.items():
        for rr in mark(k, "T-734"):
            if not rr["after"].startswith(f"MEASURABLE_NOW: {want}"):
                raise InputsError(f"{k}: T-734 row {rr['after']} is not T-691 {want}")
    tk = "MISSING:FIN.WP.DOORWAY_TRANSITION[m2]/DOOR:D-GF-07-PANTRY/TRANSITION"
    mark(tk, "T-710")
    entries.append({"piece": "WP_WIRE", "action": "ADD_NAMED", "add_key": "TRANSITION",
                    "host_line_id": HOSTS["FIN.WP.DOORWAY_TRANSITION"], "item_code": "FIN.WP.DOORWAY_TRANSITION",
                    "unit": "m2", "room": PANTRY, "floor": PANTRY_FLOOR,
                    "item": "doorway transition (m2) at the GF pantry door D-GF-07", "source_tasks": ["T-710", "T-734"],
                    "rule": "Q-35 C (R-T734-3)", "status": "HELD",
                    "why": "NOT PRINTED: no wet-room / threshold detail issued (T-195 register); cause DESIGNER",
                    "open": "the threshold / wet-room detail at D-GF-07 (designer)"})
    # ---- ROOF: T-702 part (a)
    nroof = 0
    for r in t702["a_roof_layers"]["rows"]:
        lid, layer = r["line_id"], r["layer"]
        x = ix.get(lid)
        if x["class"] == "RELEASED":                                        # KEEP finish rows (released)
            for rr in mark(lid, "T-702"):
                if rr["action"] != "KEEP":
                    raise InputsError(f"{lid}: a released finish row that is not KEEP")
            statements.append({"line_id": lid, "action": "KEEP", "why": "T-702 finish area MEASURED, released"})
            continue
        ex = _expect(x)
        t = r["t702"]
        rr = mark(lid, "T-702")[0]
        base = {"piece": "ROOF_WIRE", "line_id": lid, "expect": ex, "source_tasks": ["T-702", "T-748"],
                "rule": "R-T702-3"}
        if not isinstance(t, dict):
            raise InputsError(f"{lid}: T-702 row is not a record")
        if layer == "FALLS_SCREED" and t.get("low") is not None:
            low = D(str(t["low"]))
            if _after(rr["after"])[1] != [low]:
                raise InputsError(f"{lid}: T-748 map {rr['after']} is not T-702 low {low}")
            entries.append(dict(base, action="AT_LEAST", value=float(low), status="ASSUMED — OWNER-APPROVED",
                                status_text="ASSUMED — OWNER-APPROVED (scope Q-41 'roof -> screed'); t0 unprinted "
                                            "(D-39): AT_LEAST .. OPEN",
                                why=f"falls volume over the membrane face {r['membrane_face_basis_m2']}"[:400],
                                open="minimum screed t0 printed nowhere (D-39): upper end open"))
        else:
            why = f"{t.get('state')}: {t.get('why')}"
            entries.append(dict(base, action="NAMED", status="HELD", why=why[:400],
                                open=("owner Q-34 PARKED (top roof; no roof plan D-62)" if "Q-34" in why else
                                      why)[:400]))
        nroof += 1
    if nroof != N_ROOF:
        raise InputsError(f"{nroof} roof-layer entries, expected {N_ROOF}")
    # ---- every other live H4 row: a statement, named
    for r in rows:
        if r["row"] in used:
            continue
        lid = r["host_line_id"]
        if lid in IGNORED_SMALL:
            statements.append({"line_id": lid, "action": "IGNORED_SMALL", "row": r["row"], "why": IGNORED_SMALL[lid]})
        elif r["action"] == "DOWNGRADE":
            x = ix[lid]
            if x["class"] != "HELD" or x["held_low"] is None:
                raise InputsError(f"{lid}: the downgrade is not carried on V3.0.79")
            statements.append({"line_id": lid, "action": "CARRIED", "row": r["row"],
                               "why": f"Checker downgrade record carried by V3.0.76: HELD {x['held_low']} .. "
                                      f"{x['held_high']} m2 on V3.0.79 (T-691 band)"})
        elif lid == "L-636fd3ff1784a12e653b":
            statements.append({"line_id": lid, "action": "CARRIED", "row": r["row"],
                               "why": "T-691 band already on V3.0.79 (V3.0.76 carried it)"})
        else:
            statements.append({"line_id": lid or r["target"], "action": f"{r['action']}/{r['live']}", "row": r["row"],
                               "why": (r["after"] or "state only")[:200]})
    srcs = [dict(SOURCES[t], task=t, sha256=sha(SOURCES[t]["file"])) for t in SOURCES]
    return {"schema": SCHEMA, "project_id": PID, "sources": srcs, "entries": entries, "statements": statements,
            "d41": t734.get("d41")}


def inputs():
    d = build()
    d.pop("d41", None)
    return d


def wire_table(doc):
    ix = {x["line_id"]: x for x in load(INDEX)["lines"]}
    out = []
    for e in doc["entries"]:
        x = ix.get(e.get("line_id"))
        before = None if x is None else (None if x["held_low"] is None else [x["held_low"], x["held_high"]])
        after = ([e["value"]] * 2 if e["action"] in ("POINT", "ADD_POINT") else [e["low"], e["high"]]
                 if e["action"] == "BOUND" else None)
        out.append({"line": e.get("line_id") or f"ADD {e['item_code']} {e['room']}#{e['add_key']}",
                    "item_code": e["expect"]["item_code"] if "expect" in e else e["item_code"],
                    "unit": e["expect"]["unit"] if "expect" in e else e["unit"], "action": e["action"],
                    "before": before, "after": after,
                    "beside_at_least": e["value"] if e["action"] == "AT_LEAST" else None,
                    "status": e["status"], "rule": e["rule"], "sources": e["source_tasks"]})
    return out


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    doc = build()
    from engine.source import arch_v3080 as A
    d = A.load_inputs(inputs(), PID)
    acts = {}
    for e in d["_entries"]:
        acts[e["action"]] = acts.get(e["action"], 0) + 1
    pen = [e for e in d["_entries"] if (e.get("expect") or {}).get("item_code", e.get("item_code")) ==
           "FIN.WP.PENETRATION"]
    lo = sum(float(e.get("_value", e.get("_low", 0))) for e in pen)
    hi = sum(float(e.get("_value", e.get("_high", 0))) for e in pen)
    scr = sum(float(e["_value"]) for e in d["_entries"] if e["action"] == "AT_LEAST")
    summ = {"entries": len(d["_entries"]), "by_action": dict(sorted(acts.items())),
            "statements": len(doc["statements"]),
            "statements_by_action": {k: sum(1 for s in doc["statements"] if s["action"] == k)
                                     for k in sorted({s["action"] for s in doc["statements"]})},
            "penetration_pcs": [round(lo, 6), round(hi, 6)], "screed_at_least_m3": round(scr, 6)}
    print(json.dumps(summ))
    payload = {"schema": "URBAN_T750_WIRE_TABLE_V1", "candidate_index": INDEX, "summary": summ,
               "rows": wire_table(doc), "statements": doc["statements"], "d41": doc["d41"],
               "pins": {k: sha(k) for k in PINS}}
    text = json.dumps(payload, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    if "--check" in argv:
        if OUT.read_text(encoding="utf-8") != text:
            print("T750_WIRE_TABLE.json differs from a rebuild")
            return 1
    if "--write" in argv:
        OUT.parent.mkdir(exist_ok=True)
        OUT.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    sys.exit(main())
