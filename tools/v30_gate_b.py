"""V3.0 GATE B AUTOMATED CHECKS (T-156) for the Checker: a line-by-line before / after BOQ diff with the hand-check
flags of WORKFLOW_CONTROLS_2026-10-21.md section 1 Gate B (owner-approved 2026-10-21), and the reproducible picker of
the 2 random lines. It reads two BOQ outputs and writes a table; it computes, changes and approves no quantity, and
nothing in the engine imports it (rollback: delete this file).

    python3 -I tools/v30_gate_b.py diff BEFORE.json AFTER.json --out DIR [--sha SHA] [--register REG.json]
                                        [--ledger LEDGER.json ...] [--before-label X] [--after-label Y]
    python3 -I tools/v30_gate_b.py pick --sha SHA ID [ID ...]

BEFORE / AFTER are BOQ_LINES.json files of canonical lines (engine.source.boq_line, URBAN_CANONICAL_BOQ_LINE_V1): the
previous V3.0 run vs the new V3.0 run (V3_0_BOQ_LINES.json, V3_0_1_BOQ_LINES.json ...), or the released
ARCH_TAKEOFF_V2.9 + route G run (BOQ_LINES.json) vs the V3.0 run. DIR receives GATE_B_DIFF.json and GATE_B_DIFF.csv.

Pairing (the before and after line of one row), in this order, each stage only on lines still unpaired:
  1 ID         the same line_id in both runs;
  2 LEDGER     a V3.0 integration-ledger row (--ledger) whose line_ids are one before-only and one after-only id;
  3 ELEMENT    the same (item_code, floor, room_id, element_id), unit ignored, exactly one line on each side (this is how
               a unit change pairs: the unit is part of the line_id hash);
  4 SURFACE    the same (floor, room_id, element_id, unit), item ignored, exactly one line on each side (how a material
               classification change pairs). Stages 3 and 4 need an element_id; an ambiguous group never pairs.
A line left unpaired is a NEW line (after only) or a DROPPED line (before only).

Flags, one per Gate B "always checked by hand" rule (a row may carry several):
  SHARE_2PCT       the line's quantity is >= 2 % of its trade total in the before or in the after run; the total is
                   per trade AND unit (never mixing units) over the quantity lines (MEASURED, SOURCE_DERIVED,
                   PROVISIONAL) of that run;
  MOVED_5PCT       both sides carry a quantity in the same unit and |after - before| >= 5 % of before (before 0 and
                   after not 0 counts as moved);
  NEW_METHOD       the rule (rule_id, version) differs between the two sides, or a NEW line's rule is in no line of the
                   before run;
  NEW_LINE         after only (newly introduced scope);
  DROPPED_LINE     before only (missing scope);
  STATE_CHANGE     the evidence state differs, or a held range (BOUNDED_EXPOSURE low / high) differs: a quantity that
                   became held, or a held one that became a quantity, is never compared as 0;
  UNIT_CHANGE      the two sides carry different units (no delta is computed across units);
  STRUCTURAL       a structural safety-relevant item: footing, neck, column, strap, ground beam, ground slab, beam,
                   lintel, slab, stair, dome, pool, tank, lift, boundary wall, parapet, other RC and reinforcement
                   (every STR.* item except plain blinding);
  CLASS_CHANGE     the item code, trade or material state differs (a material classification change);
  DOUBLE_FINISH    with --register (an ELEMENT_REGISTER_V0.json beside the run, T-134): one element whose PRIMARY lines
                   carry two different floor-surface finish items (one surface finished twice);
  CROSS_DEPENDENCY the line names another as never additive with it, or is so named (a possible double count).

Lines without a quantity (BOUNDED_EXPOSURE, BLOCKED_RFI, EXCLUDED_WITH_REASON, NOT_APPLICABLE_WITH_EVIDENCE) are
listed with their state and range in "not_compared" and never enter a total, a share or a delta as 0.

Random picker (section 1): the rows with no flag are the remaining lines; their row ids (the after line_id, else the
before line_id) sorted ascending (Python string order); N = int(first 8 hex characters of the merge-candidate commit
sha, 16); L = their number; picks are positions N mod L and (N div L) mod L; when both land on the same line the second
takes the next position (wrapping to 0). L = 1 gives one pick, L = 0 none.

The summary counts, per rule, the rows it caught and the rows only it caught (the Checker's threshold record).
Nothing here names a project, a sheet, a layer or a line: every number comes from the two runs.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

SCHEMA = "URBAN_V30_GATE_B_DIFF_V1"
SHARE_PCT = 2.0
MOVE_PCT = 5.0
PCT_EPS = 1e-9                     # float noise only: 2/100*100 may read 1.9999999999999998
QUANTITY_STATES = ("MEASURED", "SOURCE_DERIVED", "PROVISIONAL")
FLOOR_SURFACE_FINISH = ("FIN.FLOOR.PORCELAIN", "FIN.FLOOR.WET_TILE", "FIN.MARBLE.LANDING", "FIN.MARBLE.TREAD",
                        "FIN.MARBLE.THRESHOLD")
NOT_STRUCTURAL = ("STR.CONC.BLINDING",)
FLAGS = ("SHARE_2PCT", "MOVED_5PCT", "NEW_METHOD", "NEW_LINE", "DROPPED_LINE", "STATE_CHANGE", "UNIT_CHANGE",
         "STRUCTURAL", "CLASS_CHANGE", "DOUBLE_FINISH", "CROSS_DEPENDENCY")
SHA_RE = re.compile(r"^[0-9a-f]{8,40}$")
CSV_FIELDS = ("row_id", "pairing", "before_line_id", "after_line_id", "item_code", "trade", "unit", "floor", "room_id",
              "element_id", "before_state", "before_value", "before_low", "before_high", "after_state", "after_value",
              "after_low", "after_high", "delta", "delta_pct", "before_share_pct", "after_share_pct", "before_method",
              "after_method", "flags")


# ------------------------------------------------------------------------------------------------------------ inputs
def _r(x, n=6):
    return None if x is None else round(float(x), n)


def record(ln):
    """the fields of one canonical line that the diff reads."""
    loc = ln.get("location") or {}
    rule = ln.get("rule") or {}
    br = ln.get("bounded_range") or {}
    st = ln["evidence_state"]
    q = st in QUANTITY_STATES
    return {"line_id": ln["line_id"], "item_code": ln["item_code"], "trade": ln["trade"], "unit": ln["unit"],
            "floor": loc.get("floor"), "room_id": loc.get("room_id"), "element_id": loc.get("element_id"),
            "state": st, "value": float(ln["measured_net"]) if q else None,
            "low": float(br["low"]) if st == "BOUNDED_EXPOSURE" else None,
            "high": float(br["high"]) if st == "BOUNDED_EXPOSURE" else None,
            "method": f"{rule.get('rule_id')}@{rule.get('version')}", "material_state": ln.get("material_state"),
            "never_additive_with": list(ln.get("never_additive_with") or ())}


def load_lines(path):
    lines = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(lines, list):
        raise ValueError(f"{path}: a BOQ_LINES.json file holds a list of lines")
    return lines


def _index(lines, side):
    out = {}
    for ln in lines:
        r = record(ln)
        if r["line_id"] in out:
            raise ValueError(f"{side}: line {r['line_id']} appears twice")
        out[r["line_id"]] = r
    return out


# ----------------------------------------------------------------------------------------------------------- pairing
def ledger_pairs(ledgers):
    """(id_a, id_b) candidate pairs from V3.0 / V3.0.x integration ledgers (rows with two line_ids)."""
    out = []
    for led in ledgers or ():
        for row in led.get("rows") or ():
            ids = row.get("line_ids") or ()
            if len(ids) == 2:
                out.append(tuple(ids))
    return out


def _unique_groups(recs, key):
    g = defaultdict(list)
    for r in recs:
        k = key(r)
        if k is not None:
            g[k].append(r["line_id"])
    return {k: v[0] for k, v in g.items() if len(v) == 1}


def pair(before, after, ledgers=None):
    """-> [(pairing, before_id or None, after_id or None)] in after order, then the dropped lines in before order."""
    pairs = {}                                                   # after id -> (pairing, before id)
    used_b = set()
    for lid in after:
        if lid in before:
            pairs[lid] = ("ID", lid)
            used_b.add(lid)
    for a_, b_ in ledger_pairs(ledgers):
        for bid, aid in ((a_, b_), (b_, a_)):
            if bid in before and bid not in used_b and aid in after and aid not in pairs and aid not in before:
                pairs[aid] = ("LEDGER", bid)
                used_b.add(bid)
    stages = (("ELEMENT", lambda r: (r["item_code"], r["floor"], r["room_id"], r["element_id"])
               if r["element_id"] is not None else None),
              ("SURFACE", lambda r: (r["floor"], r["room_id"], r["element_id"], r["unit"])
               if r["element_id"] is not None else None))
    for name, key in stages:
        ub = _unique_groups([r for i, r in before.items() if i not in used_b], key)
        ua = _unique_groups([r for i, r in after.items() if i not in pairs], key)
        for k, aid in ua.items():
            if k in ub:
                pairs[aid] = (name, ub[k])
                used_b.add(ub[k])
    out = [(pairs[a][0], pairs[a][1], a) if a in pairs else ("NONE", None, a) for a in after]
    out += [("NONE", b, None) for b in before if b not in used_b]
    return out


# ------------------------------------------------------------------------------------------------------------- rules
def _at_least(pct, threshold):
    return pct >= threshold - PCT_EPS


def trade_totals(recs):
    """{(trade, unit): sum of the quantity lines}: never mixes units; held lines are not summed."""
    t = defaultdict(float)
    for r in recs.values():
        if r["value"] is not None:
            t[(r["trade"], r["unit"])] += r["value"]
    return dict(t)


def _share(r, totals):
    if r is None or r["value"] is None:
        return None
    tot = totals.get((r["trade"], r["unit"])) or 0.0
    return 100.0 * r["value"] / tot if tot > 0 else None


def double_finish_lines(register):
    """line ids of the PRIMARY floor-surface finish lines of every element that carries two different such items."""
    out = set()
    for e in (register or {}).get("elements") or ():
        prim = [b for b in e.get("boq_lines") or () if b.get("role") == "PRIMARY"
                and b.get("item_code") in FLOOR_SURFACE_FINISH]
        if len({b["item_code"] for b in prim}) > 1:
            out.update(b["line_id"] for b in prim)
    return out


def structural(item_code):
    return item_code.startswith("STR.") and item_code not in NOT_STRUCTURAL


def diff(before_lines, after_lines, *, register=None, ledgers=None, share_pct=SHARE_PCT, move_pct=MOVE_PCT):
    """-> the diff document (rows with flags, totals per trade and unit, not_compared, summary per rule)."""
    B, A = _index(before_lines, "before"), _index(after_lines, "after")
    tb, ta = trade_totals(B), trade_totals(A)
    before_methods = {r["method"] for r in B.values()}
    dbl = double_finish_lines(register)
    cross = set()
    for recs in (B, A):
        for r in recs.values():
            if r["never_additive_with"]:
                cross.add(r["line_id"])
                cross.update(r["never_additive_with"])
    rows = []
    for how, bid, aid in pair(B, A, ledgers):
        b, a = B.get(bid), A.get(aid)
        ref = a or b
        f = []
        sb, sa = _share(b, tb), _share(a, ta)
        if any(s is not None and _at_least(s, share_pct) for s in (sb, sa)):
            f.append("SHARE_2PCT")
        delta = pct = None
        if b and a and b["unit"] == a["unit"] and b["value"] is not None and a["value"] is not None:
            delta = a["value"] - b["value"]
            if b["value"] != 0:
                pct = 100.0 * delta / b["value"]
            if (pct is not None and _at_least(abs(pct), move_pct)) or (b["value"] == 0 and a["value"] != 0):
                f.append("MOVED_5PCT")
        if b and a and b["method"] != a["method"]:
            f.append("NEW_METHOD")
        if a and not b and a["method"] not in before_methods:
            f.append("NEW_METHOD")
        if a and not b:
            f.append("NEW_LINE")
        if b and not a:
            f.append("DROPPED_LINE")
        if b and a and (b["state"] != a["state"] or (b["low"], b["high"]) != (a["low"], a["high"])):
            f.append("STATE_CHANGE")
        if b and a and b["unit"] != a["unit"]:
            f.append("UNIT_CHANGE")
        if (a and structural(a["item_code"])) or (b and structural(b["item_code"])):
            f.append("STRUCTURAL")
        if b and a and any(b[k] != a[k] for k in ("item_code", "trade", "material_state")):
            f.append("CLASS_CHANGE")
        if (aid in dbl) or (bid in dbl):
            f.append("DOUBLE_FINISH")
        if (aid in cross) or (bid in cross):
            f.append("CROSS_DEPENDENCY")
        unit = ref["unit"] if not (b and a and b["unit"] != a["unit"]) else f"{b['unit']}->{a['unit']}"
        rows.append({"row_id": aid or bid, "pairing": how, "before_line_id": bid, "after_line_id": aid,
                     "item_code": ref["item_code"] if not (b and a and b["item_code"] != a["item_code"])
                     else f"{b['item_code']}->{a['item_code']}",
                     "trade": ref["trade"], "unit": unit, "floor": ref["floor"], "room_id": ref["room_id"],
                     "element_id": ref["element_id"],
                     "before": {k: (b or {}).get(k) for k in ("state", "value", "low", "high")},
                     "after": {k: (a or {}).get(k) for k in ("state", "value", "low", "high")},
                     "delta": _r(delta), "delta_pct": _r(pct, 4), "before_share_pct": _r(sb, 4),
                     "after_share_pct": _r(sa, 4), "before_method": (b or {}).get("method"),
                     "after_method": (a or {}).get("method"), "flags": [x for x in FLAGS if x in f]})
    not_compared = [{"row_id": r["row_id"], "item_code": r["item_code"], "unit": r["unit"], "before": r["before"],
                     "after": r["after"]} for r in rows
                    if (r["before"]["state"] and r["before"]["value"] is None)
                    or (r["after"]["state"] and r["after"]["value"] is None)]
    caught = Counter(x for r in rows for x in r["flags"])
    only = Counter(r["flags"][0] for r in rows if len(r["flags"]) == 1)
    summary = {"rows": len(rows), "flagged": sum(1 for r in rows if r["flags"]),
               "unflagged": sum(1 for r in rows if not r["flags"]),
               "per_rule": {x: {"caught": caught.get(x, 0), "only_this_rule": only.get(x, 0)} for x in FLAGS},
               "pairing": dict(Counter(r["pairing"] for r in rows)), "not_compared": len(not_compared),
               "thresholds": {"share_pct": share_pct, "move_pct": move_pct},
               "register_given": register is not None, "ledgers_given": len(ledgers or ())}
    tot = {"before": {f"{t}|{u}": _r(v) for (t, u), v in sorted(tb.items())},
           "after": {f"{t}|{u}": _r(v) for (t, u), v in sorted(ta.items())}}
    return {"schema": SCHEMA, "rows": rows, "trade_totals": tot, "not_compared": not_compared, "summary": summary}


# ------------------------------------------------------------------------------------------------------------ picker
def pick(ids, sha):
    """the 2 random lines of section 1: -> {"sha", "n", "L", "positions", "ids"}."""
    s = str(sha).strip().lower()
    if not SHA_RE.match(s):
        raise ValueError("the merge-candidate sha must be 8 to 40 hex characters")
    ids = list(ids)
    pool = sorted(set(ids))
    if len(pool) != len(ids):
        raise ValueError("the remaining line ids repeat")
    n = int(s[:8], 16)
    L = len(pool)
    if L == 0:
        pos = []
    elif L == 1:
        pos = [0]
    else:
        p1, p2 = n % L, (n // L) % L
        if p2 == p1:
            p2 = (p1 + 1) % L
        pos = [p1, p2]
    return {"sha": s, "n": n, "L": L, "positions": pos, "ids": [pool[p] for p in pos]}


def remaining(doc):
    return [r["row_id"] for r in doc["rows"] if not r["flags"]]


# ------------------------------------------------------------------------------------------------------------ output
def to_csv(doc):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(CSV_FIELDS), lineterminator="\n")
    w.writeheader()
    for r in doc["rows"]:
        row = {k: r.get(k) for k in CSV_FIELDS if k not in ("flags",)}
        for side in ("before", "after"):
            for k in ("state", "value", "low", "high"):
                row[f"{side}_{k}"] = r[side][k]
        row["flags"] = " ".join(r["flags"])
        w.writerow(row)
    return buf.getvalue()


def write(out, doc):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "GATE_B_DIFF.json").write_text(json.dumps(doc, indent=1, sort_keys=True, ensure_ascii=False) + "\n",
                                          encoding="utf-8")
    (out / "GATE_B_DIFF.csv").write_text(to_csv(doc), encoding="utf-8")
    return ["GATE_B_DIFF.csv", "GATE_B_DIFF.json"]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("diff")
    d.add_argument("before")
    d.add_argument("after")
    d.add_argument("--out", required=True)
    d.add_argument("--sha")
    d.add_argument("--register")
    d.add_argument("--ledger", action="append", default=[])
    d.add_argument("--before-label", default="before")
    d.add_argument("--after-label", default="after")
    p = sub.add_parser("pick")
    p.add_argument("--sha", required=True)
    p.add_argument("ids", nargs="*")
    a = ap.parse_args(argv)
    if a.cmd == "pick":
        print(json.dumps(pick(a.ids, a.sha), indent=1))
        return 0
    reg = json.loads(Path(a.register).read_text(encoding="utf-8")) if a.register else None
    leds = [json.loads(Path(x).read_text(encoding="utf-8")) for x in a.ledger]
    doc = diff(load_lines(a.before), load_lines(a.after), register=reg, ledgers=leds)
    doc["labels"] = {"before": a.before_label, "after": a.after_label}
    if a.sha:
        doc["random_picks"] = pick(remaining(doc), a.sha)
    write(a.out, doc)
    print(json.dumps({"labels": doc["labels"], "summary": doc["summary"],
                      "random_picks": doc.get("random_picks")}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
