"""T-738 (lane I, hubs H3 / H3S, owner order step 5): the live after-state of every line the TILES + STAIR FINISHES
package wires, built from Checker-merged ledgers only (sha256-pinned below) as mapped by the merged T-730 readiness
(R-T730-1, hubs H3 and H3S), checked against the candidate of record ARCH_TAKEOFF_V3.0.77 (T-749, merge 8dc7c0f6 /
c2106988; line index of record research/agents_t749/out/LINE_INDEX_V3_0_77.json). Nothing here opens a drawing or forms
a quantity: every figure is a merged ledger's.

  TILE_BOUND   T-702 part (b): the two GF stair-core wall tile lines (GF-10 / GF-11) HELD blank -> BOUND.
  STAIR_WIRE   T-715 (R-T715-1..4) with T-718 (R-T718-1..3) declaring its restatements of four lines (two turn / curved
               risers, two nosing lines; T-718 over T-715, the T-715 figure carried as superseded) and T-733 closing the
               PENDING_ON of the two 1F tread exposure lines (ENGINE_RIGHT on one step-line set; R-T715-3 then excludes
               them as duplicate readings of the GF carriers): POINT (MEASURED), BOUND (RANGE), EXCLUDE (NOT_APPLICABLE:
               the carrier line found by code + the element the ledger names; no carrier = no physical element),
               AT_LEAST / AT_MOST / CONDITIONAL (ORR-007) beside, NAMED (BLANK_NAMED), ADD_POINT (the MS2-TR closing
               riser, the one new line T-715 proposes). KEEP (2F landing, WIRING_GAP T-493), SUPERSEDED and DUPLICATE map
               rows move nothing and are carried as statements.

    python3 -I research/agents_t738/t738_inputs.py [--check] [--write]
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
OUT = HERE / "out" / "T738_ENTRIES.json"
SCHEMA = "URBAN_T738_ENTRIES_V1"
INDEX = "research/agents_t749/out/LINE_INDEX_V3_0_77.json"
T730 = "research/agents_t730/out/T730_ROWS.csv"
T715 = "research/agents_t715/out/T715_LEDGER.json"
T718 = "research/agents_t718/out/T718_LEDGER.json"
T702 = "research/agents_t702/out/T702_TILES_ROUND3.json"
T733 = "research/agents_t733/out/T733_H3_READINESS.json"
D = Decimal

PINS = {INDEX: "60982bb727c89369", T730: "737bdb55966b6ebd", T715: "740ba1827841a6e7", T718: "f50b734d79959a2e",
        T702: "ae5b37e75a1635cb", T733: "17cd75642a32fefb"}
SOURCES = {
    "T-702": {"file": T702, "merge_commit": "b90d85af",
              "checker_run": "Verifier 2026-11-11T12:01Z Gate A PASS (session_01E6cPncdZEPbJjz2ey34pSg)"},
    "T-715": {"file": T715, "merge_commit": "a4e4277a",
              "checker_run": "Verifier 2026-11-11T20:02Z Gate A PASS (session_01E6cPnej1TbCEeJXkapQmje)"},
    "T-718": {"file": T718, "merge_commit": "8052ca51",
              "checker_run": "Verifier 2026-11-11T22:12Z Gate A PASS (lock checker; F-V715-1 closed)"},
    "T-733": {"file": T733, "merge_commit": "7146583d",
              "checker_run": "Verifier 2026-11-12T07:58Z Gate A PASS on 272d7ae5 (session_01E6cPneP2vRoV5ySBhUeVJ5)"},
    "T-730": {"file": T730, "merge_commit": "6143f30d",
              "checker_run": "Verifier 2026-11-12T07:58Z Gate A PASS on 7d5efd9d (session_01E6cPneP2vRoV5ySBhUeVJ5)"},
}
HUBS = ("H3", "H3S")
ROWS_N = 94
ADD_HOST = "L-12f56cbfe750f8b30c41"      # ST-01 2F riser line (MS2-U, 2F-R4D1B62:flight 2): the closing riser's stair
PENDING_CLOSED_BY = {"L-6cf11c2d30387d0942b9": "T-733", "L-ea55ed317bc4de89aec1": "T-733"}
SKIRT = ("FIN.STAIR.SKIRTING.SLOPED", "FIN.STAIR.SKIRTING.ZIGZAG")


class InputsError(ValueError):
    pass


def sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def load(p):
    want, got = PINS.get(p), sha(p)
    if want is not None and not got.startswith(want):
        raise InputsError(f"{p}: sha256 {got[:16]} is not the pinned {want} (stale input)")
    return json.loads((ROOT / p).read_text(encoding="utf-8")) if p.endswith(".json") else \
        list(csv.DictReader((ROOT / p).read_text(encoding="utf-8").splitlines()))


def status_of(text):
    """WORKFLOW_CONTROLS s.5 status of a ledger statement: the weakest named component governs."""
    t = str(text or "")
    if "VERIFIED" in t.replace("UNVERIFIED", ""):
        raise InputsError(f"status {t!r}: nothing is VERIFIED by a research ledger")
    if "ASSUMED" in t:
        return "ASSUMED — OWNER-APPROVED"
    if t.startswith("DRAWING-CONFIRMED"):
        return "DRAWING-CONFIRMED"
    return "HELD"


def _expect(ln):
    if ln is None:
        raise InputsError("a mapped line is not in the V3.0.77 index (stale)")
    return {"item_code": ln["item_code"], "element_id": ln["element_id"], "unit": ln["unit"], "class": ln["class"],
            "low": ln["held_low"], "high": ln["held_high"]}


def _f(x):
    return None if x in (None, "") else float(D(str(x)))


def _after(text):
    """T-730 'after' text -> (kind, numbers)"""
    t = text.split()
    if t[0] == "VALUE":
        return "VALUE", [D(t[1])]
    if t[0] == "BOUND":
        return "BOUND", [D(t[1]), D(t[3])]
    if t[0] == "ONE_SIDED":
        return t[1], [D(t[2])]
    return t[0], []


RULE_BY_CLASS = {"RANGE": "R-T715-4", "AT_MOST": "R-T715-4", "CONDITIONAL_ON_FORM": "R-T715-4 (ORR-007)",
                 "AT_LEAST": "T-715 (merged T-281 / T-684 figure)", "BLANK_NAMED": "T-715 BLANK_NAMED",
                 "NOT_APPLICABLE": "T-715 (merged T-493 / T-690 finding)"}


def rule_of(piece, a):
    """(rule id, why) of a ledger statement: the rule the cause opens with (then dropped from the why), else the rule of
    its class; T-718 rows R-T718-2 / R-T718-3."""
    cause = str(a.get("cause") or "")
    head = cause.split(":")[0]
    if head.startswith("R-T") and " " not in head.strip():
        return head.strip(), cause[len(head) + 1:].strip()
    if piece == "T-718":
        return "R-T718-2 / R-T718-3", cause
    if a["class"] == "NOT_APPLICABLE" and a.get("carrier"):
        return "R-T715-3", cause
    return RULE_BY_CLASS.get(a["class"], "T-715"), cause


def rows():
    rs = [r for r in load(T730) if r["hub"] in HUBS]
    if len(rs) != ROWS_N:
        raise InputsError(f"T-730 H3 / H3S rows {len(rs)}, expected {ROWS_N}")
    return rs


def build():
    ix = {ln["line_id"]: ln for ln in load(INDEX)["lines"]}
    l715 = {x["line_id"]: x for x in load(T715)["lines"]}
    l718 = {x["line_id"]: x for x in load(T718)["lines"]}
    tile = {x["line_id"]: x for x in load(T702)["b_stair_core"]["wall_tile"]}
    t733 = {x["line_id"]: x for x in load(T733)["a_tread_highs"]["lines"]}
    by_elem = {(ln["item_code"], ln["element_id"]): ln for ln in ix.values()}
    entries, statements = [], []
    for r in rows():
        lid, act, live = r["host_line_id"], r["action"], r["live"]
        kind, nums = _after(r["after"]) if r["after"] else (None, [])
        base = {"map_row": r["row"], "map_action": act, "map_after": r["after"]}
        if live in ("SUPERSEDED", "DUPLICATE", "STATEMENT") or act == "KEEP":
            statements.append(dict(base, line_id=lid or None, live=live, piece=r["piece"],
                                   why=r["action_reason"] or r["reason"]))
            continue
        if live != "LIVE":
            raise InputsError(f"{r['row']}: live {live!r}")
        if r["blockers"] and not (r["blockers"].startswith("RULING ORR-007") and kind == "CONDITIONAL"):
            closer = PENDING_CLOSED_BY.get(lid)
            if closer is None or "T-733" not in r["blockers"]:
                raise InputsError(f"{r['row']}: blocked ({r['blockers']}) and no merged piece closes it")
            v = t733.get(lid)
            if v is None or v["verdict"] != "ENGINE_RIGHT":
                raise InputsError(f"{lid}: T-733 gives no ENGINE_RIGHT verdict for the pending line")
        if act == "ADD":
            v715 = load(T715)["new_lines_proposed"]
            if len(v715) != 1 or D(v715[0]["value_m2"]) != nums[0]:
                raise InputsError("the T-715 new line is not the map's")
            n = v715[0]
            entries.append(dict(base, piece="STAIR_WIRE", action="ADD_POINT", add_key="MS2-TR-closing-riser",
                                host_line_id=ADD_HOST, item_code="FIN.MARBLE.RISER", unit="m2", value=_f(nums[0]),
                                item=n["proposed"], element="ST-01 MS2-TR closing riser (one riser, section A-A)",
                                source_tasks=["T-715", "T-730"], rule="R-T715-1", status=status_of(n["status"]),
                                status_text=n["status"], why=n["basis"]))
            continue
        b = ix.get(lid)
        ex = _expect(b)
        if r["piece"] == "T-702":
            t = tile[lid]
            if kind != "BOUND" or [D(t["after"]["held_low"]), D(t["after"]["held_high"])] != nums:
                raise InputsError(f"{lid}: T-702 after {t['after']} is not the map's {r['after']}")
            entries.append(dict(base, piece="TILE_BOUND", action="BOUND", line_id=lid, expect=ex, low=_f(nums[0]),
                                high=_f(nums[1]), source_tasks=["T-702", "T-730"], rule="R-T686-3 / T-702 (b)",
                                status=status_of(t["status"]), status_text=t["status"],
                                why=f"{t['room']}: {t['basis']}", open="floor level C-SH-2 (designer item) holds the "
                                "range; tile top Q-55 C / Q-48 A owner-approved"))
            continue
        src = l718 if r["piece"] == "T-718" else l715
        led = src[lid]
        a = led["after"]
        if (led["item_code"], led["element_id"], led["unit"]) != (ex["item_code"], ex["element_id"], ex["unit"]):
            raise InputsError(f"{lid}: ledger line {led['item_code']} {led['element_id']} is not the index's")
        tasks = [r["piece"], "T-730"] + (["T-733"] if lid in PENDING_CLOSED_BY else [])
        rule, why = rule_of(r["piece"], a)
        e = dict(base, piece="STAIR_WIRE", line_id=lid, expect=ex, source_tasks=tasks, rule=rule,
                 status=status_of(a.get("status")), status_text=a.get("status"), why=why,
                 open=a.get("item") or None)
        if r["piece"] == "T-718":
            prev = l715[lid]["after"]
            e["supersedes"] = {"task": "T-715", "class": prev["class"], "low": prev.get("low"),
                               "why": "T-718 declares the restatement (floor kept, ceiling added)"}
        if act == "CHANGE" and kind == "VALUE":
            if a["class"] != "MEASURED" or D(a["value"]) != nums[0]:
                raise InputsError(f"{lid}: ledger {a['class']} {a.get('value')} is not the map's {r['after']}")
            e.update(action="POINT", value=_f(nums[0]),
                     open=f"not released: a drawn figure, released only by a Checker record ({a.get('status')})")
        elif act == "CHANGE" and kind == "BOUND":
            if a["class"] != "RANGE" or [D(a["low"]), D(a["high"])] != nums:
                raise InputsError(f"{lid}: ledger {a['class']} {a.get('low')} .. {a.get('high')} is not the map's")
            e.update(action="BOUND", low=_f(nums[0]), high=_f(nums[1]))
        elif act == "CHANGE" and kind == "EXCLUDED":
            if a["class"] != "NOT_APPLICABLE":
                raise InputsError(f"{lid}: ledger {a['class']} is not NOT_APPLICABLE")
            if a.get("carrier"):
                c = by_elem.get((ex["item_code"], a["carrier"]))
                if c is None or c["class"] == "EXCLUDED":
                    raise InputsError(f"{lid}: carrier {a['carrier']} {ex['item_code']} is not a live index line")
                e.update(action="EXCLUDE", cause="DUPLICATE_READING", carrier_line_id=c["line_id"],
                         carrier_element_id=a["carrier"])
            else:
                e.update(action="EXCLUDE", cause="NO_PHYSICAL_ELEMENT")
            e.pop("open")
        elif act == "BESIDE" and kind in ("AT_LEAST", "AT_MOST", "CONDITIONAL"):
            want = {"AT_LEAST": ("AT_LEAST",), "AT_MOST": ("AT_MOST",), "CONDITIONAL": ("CONDITIONAL_ON_FORM",)}[kind]
            got = a.get("low") if kind == "AT_LEAST" else a.get("high") if kind == "AT_MOST" else a.get("value")
            if a["class"] not in want or D(got) != nums[0]:
                raise InputsError(f"{lid}: ledger {a['class']} {got} is not the map's {r['after']}")
            e.update(action=kind, value=_f(nums[0]))
            if kind == "CONDITIONAL":
                if "ORR-007" not in r["blockers"]:
                    raise InputsError(f"{lid}: a form figure off ruling ORR-007")
                sib = by_elem.get((SKIRT[1 - SKIRT.index(ex["item_code"])], ex["element_id"]))
                e.update(ruling="ORR-007", sibling_line_id=sib["line_id"] if sib else None,
                         open="ORR-007: payable stair skirting form (zigzag or sloped) not ruled; one form only")
        elif act == "TEXT":
            if a["class"] != "BLANK_NAMED":
                raise InputsError(f"{lid}: ledger {a['class']} is not BLANK_NAMED")
            e.update(action="NAMED")
        else:
            raise InputsError(f"{r['row']}: map action {act} {r['after']} has no wiring form")
        entries.append(e)
    # a CONDITIONAL sibling must itself be wired; a sibling that is not (MS2-TR sloped = AT_LEAST) is named, not bound
    named = {e.get("line_id") for e in entries}
    for e in entries:
        if e.get("action") == "CONDITIONAL" and e.get("sibling_line_id") not in named:
            e["sibling_line_id"] = None
    return {"schema": SCHEMA, "candidate": "ARCH_TAKEOFF_V3.0.77", "index": INDEX,
            "sources": [dict(task=t, sha256=sha(s["file"]), **s) for t, s in SOURCES.items()],
            "entries": entries, "statements": statements}


def inputs():
    d = build()
    clean = []
    for e in d["entries"]:
        clean.append({k: v for k, v in e.items() if k not in ("map_row", "map_action", "map_after")})
    return {"schema": "URBAN_V3078_INPUTS_V1", "project_id": None, "sources": d["sources"], "entries": clean,
            "statements": d["statements"]}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    d = build()
    text = json.dumps(d, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    if "--check" in argv:
        if OUT.read_text(encoding="utf-8") != text:
            raise SystemExit(f"{OUT.name} differs from a rebuild")
        print("check: equal")
    if "--write" in argv:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(text, encoding="utf-8")
    from collections import Counter
    print(json.dumps({"entries": len(d["entries"]), "statements": len(d["statements"]),
                      "by_action": dict(Counter(f"{e['piece']}:{e['action']}" for e in d["entries"]))},
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    main()
