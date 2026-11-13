"""T-755 designer-list re-census: rules (pure functions, every villa; no drawing content, no client data).

R-T755-1 = R-T716-1 (research/agents_t716/t716_rules.py, imported read-only, unchanged) with two additions:

  (a) NAMED designer items. The Lead's list (DESIGNER_QUESTIONS.md) also gives items an alphanumeric id (D-GF-07,
      D-BAND, D-DRAIN, D-M1, D-J1 .. D-J3). R-T716-1 reads only D-<digits>. An id is read as a designer item ONLY when
      it is in the closed list `named` handed in by the caller (the Lead's list of the day), matched as a whole token.
      A pattern such as D-GF-nn is NOT read generally: door marks print the same shape (D-GF-04, D-1F-06; T-716 test
      `test_identifiers_that_are_not_items`). A named id is a DESIGNER id like a numbered one (rule 1 of R-T716-1).
  (b) ITEM view. Each D-id belongs to one or more items of the Lead's list (`item_of`: D-id -> item labels, data handed
      in; the list itself puts D-44 under items 1 and 3, D-63 under 3 and 6). A HELD line is SOLE under an item when
      that item is the only one its D-ids reach and every D-id it cites is listed; SHARED under each item it reaches
      otherwise. A D-id in no item is reported (UNLISTED_D_ID), never dropped. Counted once per view, never twice.

Everything else is R-T716-1 unchanged: one bucket per HELD line, first match DESIGNER > RFI > OWNER > DEPENDENT (host)
> REASON_CODE > DESIGNER_TAG > METHOD_GAP > NOT_PRINTED > NAMED_TEXT > UNNAMED; per family and unit only, never summed
across units; one-sided bounds on their side; a line with no bound is BLANK, counted, never 0.
"""
from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "agents_t716"))
import t716_rules as R  # noqa: E402

side, add, canonical = R.side, R.add, R.canonical


def _named_re(named):
    if not named:
        return None
    alts = "|".join(re.escape(n) for n in sorted(named, key=len, reverse=True))
    return re.compile(r"(?<![A-Za-z0-9-])(" + alts + r")(?![0-9A-Za-z-])")


def classify_own(line: dict, named=()) -> dict:
    """R-T716-1 rules 1-3 and 5-10 on the line's own text, with the named ids of (a) read as designer ids."""
    own = R.classify_own(line)
    rx = _named_re(named)
    extra = sorted(set(rx.findall(R.cause_text(line)))) if rx else []
    if not extra:
        return own
    d = sorted(set(own["d_ids"]) | set(extra), key=_dkey)
    return {"kind": "DESIGNER", "bucket": "+".join(d), "d_ids": d}


def _dkey(d: str):
    m = re.fullmatch(r"D-(\d+)", d)
    return (0, int(m.group(1)), d) if m else (1, 0, d)


def classify(lid, records, held, element_ids=None, named=(), _seen=None) -> dict:
    """R-T716-1 rule order: own ids (1-3) first, then a HELD host to the root (4), then own text (5-10)."""
    rec = records[lid]
    own = classify_own(rec, named)
    if own["kind"] in ("DESIGNER", "RFI", "OWNER"):
        return dict(own, dependent=False, host=None, root=lid)
    seen = (_seen or set()) | {lid}
    h = R.host_of(rec, (element_ids or {}).get(lid))
    if h and h in held and h in records and h not in seen:
        up = classify(h, records, held, element_ids, named, seen)
        return dict(up, dependent=True, host=h)
    return dict(own, dependent=False, host=None, root=lid)


def census(index_lines: list, records: dict, named=(), item_of=None) -> dict:
    """index_lines: LINE_INDEX rows; records: line_id -> line record. Only class HELD lines are counted.

    item_of: D-id -> list of item labels of the Lead's list (optional). -> buckets, per D-id, per item, assignment, unlisted."""
    item_of = item_of or {}
    held_ix = [i for i in index_lines if i["class"] == "HELD"]
    held = {i["line_id"] for i in held_ix}
    eids = {i["line_id"]: i["element_id"] for i in index_lines}
    buckets = defaultdict(lambda: {"kind": None, "lines": [], "by": defaultdict(R._acc)})
    per_d = defaultdict(lambda: {"sole": defaultdict(R._acc), "shared": defaultdict(R._acc), "sole_ids": [],
                                 "shared_ids": []})
    per_item = defaultdict(lambda: {"sole": defaultdict(R._acc), "shared": defaultdict(R._acc), "sole_ids": [],
                                    "shared_ids": []})
    unlisted = defaultdict(list)
    assign = {}
    for i in held_ix:
        lid = i["line_id"]
        assert lid not in assign, f"line {lid} twice"
        c = classify(lid, records, held, eids, named)
        assign[lid] = {"kind": c["kind"], "bucket": c["bucket"], "dependent": c["dependent"], "host": c["host"],
                       "item_code": i["item_code"], "unit": i["unit"], "side": side(i), "d_ids": c["d_ids"]}
        key = (i["item_code"], i["unit"])
        b = buckets[(c["kind"], c["bucket"])]
        b["kind"] = c["kind"]
        b["lines"].append(lid)
        add(b["by"][key], i, c["dependent"])
        for d in c["d_ids"]:
            view = "sole" if len(c["d_ids"]) == 1 else "shared"
            add(per_d[d][view][key], i, c["dependent"])
            per_d[d][view + "_ids"].append(lid)
        items = sorted({it for d in c["d_ids"] for it in item_of.get(d, ())}, key=str)
        for d in c["d_ids"]:
            if d not in item_of:
                unlisted[d].append(lid)
        for it in items:
            view = "sole" if len(items) == 1 and all(d in item_of for d in c["d_ids"]) else "shared"
            add(per_item[it][view][key], i, c["dependent"])
            per_item[it][view + "_ids"].append(lid)
    out_b = [{"kind": k, "bucket": n, "finding": k in R.FINDING_KINDS, "lines": len(b["lines"]),
              "line_ids": sorted(b["lines"]), "by_family_unit": R._rows(b["by"])}
             for (k, n), b in sorted(buckets.items(), key=lambda kv: (R.BUCKET_ORDER.index(kv[0][0]), kv[0][1]))]

    def view(v):
        return {"sole_lines": len(v["sole_ids"]), "shared_lines": len(v["shared_ids"]),
                "sole_line_ids": sorted(v["sole_ids"]), "shared_line_ids": sorted(v["shared_ids"]),
                "sole": R._rows(v["sole"]), "shared": R._rows(v["shared"])}
    out_d = {d: view(v) for d, v in sorted(per_d.items(), key=lambda kv: _dkey(kv[0]))}
    out_i = {it: view(v) for it, v in sorted(per_item.items(), key=lambda kv: str(kv[0]))}
    assert sum(b["lines"] for b in out_b) == len(held_ix) == len(assign)
    return {"held_lines": len(held_ix), "buckets": out_b, "per_d_id": out_d, "per_item": out_i,
            "unlisted_d_ids": {d: sorted(v) for d, v in sorted(unlisted.items())}, "assignment": assign}


def state(ix_row: dict | None, a: dict | None) -> tuple | None:
    """the comparable state of one line in one version: None if absent or not HELD; else (bucket, side, low, high)."""
    if ix_row is None or ix_row["class"] != "HELD":
        return None
    return (a["bucket"] if a else None, side(ix_row), ix_row.get("held_low"), ix_row.get("held_high"))


def transitions(chain: list) -> dict:
    """chain: [(version, {line_id: index_row}, {line_id: assignment})...] in version order.

    -> per line whose state differs between the first and last version: the list of steps where it changed
       ({'step': 'a->b', 'from': state, 'to': state}). A line that changes and changes back is listed with both steps.
    Reconciliation identity (asserted by the caller): first + sum(step deltas) = last, per bucket."""
    out = {}
    ids = set()
    for _, ix, _ in chain:
        ids |= set(ix)
    for lid in sorted(ids):
        steps = []
        prev = None
        for n, (v, ix, a) in enumerate(chain):
            s = state(ix.get(lid), a.get(lid))
            if n and s != prev:
                steps.append({"step": f"{chain[n - 1][0]}->{v}", "from": prev, "to": s})
            prev = s
        if steps:
            out[lid] = steps
    return out


def bucket_delta(first: dict, last: dict, trans: dict) -> dict:
    """per bucket: lines in first, in last, and the step attribution of every in / out move. Residual must be 0."""
    res = defaultdict(lambda: {"first": 0, "last": 0, "in": defaultdict(int), "out": defaultdict(int)})
    for a in first.values():
        res[a["bucket"]]["first"] += 1
    for a in last.values():
        res[a["bucket"]]["last"] += 1
    for lid, steps in trans.items():
        for s in steps:
            fb = s["from"][0] if s["from"] else None
            tb = s["to"][0] if s["to"] else None
            if fb == tb:
                continue
            if fb is not None:
                res[fb]["out"][s["step"]] += 1
            if tb is not None:
                res[tb]["in"][s["step"]] += 1
    out = {}
    for b, r in sorted(res.items()):
        resid = r["last"] - r["first"] - sum(r["in"].values()) + sum(r["out"].values())
        out[b] = {"first": r["first"], "last": r["last"], "in": dict(sorted(r["in"].items())),
                  "out": dict(sorted(r["out"].items())), "residual": resid}
    return out
