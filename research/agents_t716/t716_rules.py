"""T-716 designer-list impact census: rules (pure functions, every villa; no drawing content, no client data).

R-T716-1 (one cause bucket per HELD line; scope: any candidate line file; provenance: T-716, proposed for the Checker).
The cause of a HELD line is read ONLY from its own record: `rfi.question` and `notes` (the cause text) and the host link
of a derived line. Identifiers are taken exactly as printed; nothing is inferred from a quantity or a family name.
Every HELD line lands in exactly ONE bucket, first match in this order:

  1 DESIGNER     a designer item D-nn printed. Bucket = the sorted set ('D-39+D-62'); a line held by two items is
                 counted ONCE in its combined bucket and shown beside each single D-id as SHARED (never added twice).
  2 RFI          an RFI code printed (RFI-S08, RFI S08 / S23, RFI-B-A05 ...). Bucket = the sorted set of codes as printed.
                 NOT mapped to a D-id here: the RFI register was renumbered on 2026-10-31 (old S23 = new RFI-S08) and a
                 bare code does not say which numbering it uses; the Lead maps it (finding).
  3 OWNER        an owner question Q-nn (also printed 'owner question OQ-nn' / 'OQ nn') or an owner open ruling
                 ORR-nnn printed. Bucket = the sorted set.
  4 DEPENDENT    no id of its own, and the record names a HELD host line (element id 'FW:L-<id>:...', or 'waits for',
                 'source', 'with its host', 'beside' + L-<20 hex>): the line takes its host's bucket (followed to the root,
                 cycle-safe) and is flagged DEPENDENT (R-T698-1: derived lines carry HELD). A host that is RELEASED or
                 not HELD gives no inheritance: the line is classified on its own text.
  5 REASON_CODE  an engine reason code printed: UPPER_SNAKE of three or more words with two alphabetic words of three
                 letters (STAIR_RISER_NOT_ESTABLISHED), or a two-word code printed as a label 'SPLIT_UNRESOLVED:'.
                 Bucket = the first such code in the text. A named cause with no item number: the Lead names its item (finding).
  6 DESIGNER_TAG the text says designer / consultant (item, specification, detail) but prints no number (finding).
  7 METHOD_GAP   the text names an engine method gap (METHOD_WORDS): ours to fix, before any designer reading.
  8 NOT_PRINTED  the text says the drawings do not print / draw / dimension / specify it, with no number (finding: a
                 candidate for the designer list; the Lead gives it a D-id or names the item that already covers it).
  9 NAMED_TEXT   a cause text with none of the above (finding: the Lead names its item).
 10 UNNAMED      no cause text at all (finding: a HELD line must say why).
The cause text is the line's rfi.question, its notes and, for a fill line, the items of calculation.inputs.*.still_held.
Quantities: per family and unit only, never summed across units; a bounded line contributes its own low .. high; a
one-sided bound (AT_LEAST / AT_MOST) counts on its side only; a line with no bound is BLANK (counted, never 0).
"""
from __future__ import annotations

import json
import re
from collections import defaultdict

D_RE = re.compile(r"(?<![A-Za-z0-9-])D-(\d{1,3})(?![0-9A-Za-z])")
Q_RE = re.compile(r"(?<![A-Za-z0-9-])Q-(\d{1,3})(?![0-9A-Za-z])")
OQ_RE = re.compile(r"(?<![A-Za-z0-9-])OQ[- ]?(\d{1,3})(?![0-9A-Za-z])")
ORR_RE = re.compile(r"(?<![A-Za-z0-9-])ORR-(\d{1,4})(?![0-9A-Za-z])")
RFI_RE = re.compile(r"RFI[- ]?((?:B-)?[SA]\d{2}|B-SH)((?:\s*/\s*(?:B-)?[SA]\d{2})*)")
RFI_TAIL = re.compile(r"(?:B-)?[SA]\d{2}")
CODE_RE = re.compile(r"(?<![A-Za-z0-9_])([A-Z][A-Z0-9]*(?:_[A-Z0-9]+){2,})(?![A-Za-z0-9_])")
CODE2_RE = re.compile(r"(?:^|(?<=[\s(]))([A-Z]{2,}_[A-Z]{3,})(?=:)")
HOST_RE = re.compile(r"(?:waits? for|source(?: [A-Z][A-Z0-9_.]*)?|with its host|host|beside(?: [A-Z][A-Z0-9_.]*)?)\s+"
                     r"(L-[0-9a-f]{20})")
FW_HOST_RE = re.compile(r"^[A-Z]{2,4}:(L-[0-9a-f]{20})(?::|$)")
METHOD_WORDS = ("method gap", "not implemented", "no method", "unsupported", "not modelled", "not modeled",
                "engine gap", "no engine")
DESIGNER_WORDS = ("(designer)", "designer item", "designer specification", "designer detail", "consultant item",
                  "consultant detail", "designer;", "designer)")
NOT_PRINTED_WORDS = ("not printed", "not drawn", "not dimensioned", "not specified", "none drawn", "no detail",
                     "drawn on no plan", "not shown")
BUCKET_ORDER = ("DESIGNER", "RFI", "OWNER", "REASON_CODE", "DESIGNER_TAG", "METHOD_GAP", "NOT_PRINTED", "NAMED_TEXT",
                "UNNAMED")
FINDING_KINDS = ("RFI", "REASON_CODE", "DESIGNER_TAG", "NOT_PRINTED", "METHOD_GAP", "NAMED_TEXT", "UNNAMED")
CODE_STOP = {"ARCH_TAKEOFF_V3", "NOT_RELEASED", "HELD_WALL", "HELD_PIECE"}


def cause_text(line: dict) -> str:
    """the line's own hold cause: rfi.question (or a plain rfi string) + notes (string or list), joined."""
    parts = []
    rfi = line.get("rfi")
    if isinstance(rfi, dict):
        if rfi.get("question"):
            parts.append(str(rfi["question"]))
    elif isinstance(rfi, str) and rfi.strip():
        parts.append(rfi)
    notes = line.get("notes")
    if isinstance(notes, (list, tuple)):
        parts.extend(str(n) for n in notes if n)
    elif notes:
        parts.append(str(notes))
    inputs = ((line.get("calculation") or {}).get("inputs") or {})
    for blk in (inputs.values() if isinstance(inputs, dict) else ()):
        for it in ((blk or {}).get("still_held") or []) if isinstance(blk, dict) else ():
            if isinstance(it, dict) and it.get("item"):
                parts.append(f"still held {it.get('wall') or ''}: {it['item']}")
    return " | ".join(str(p).strip() for p in parts if str(p).strip())


def _num_sorted(xs, prefix_len):
    return sorted(set(xs), key=lambda s: (int(re.sub(r"\D", "", s[prefix_len:]) or 0), s))


def ids(text: str) -> dict:
    d = _num_sorted([f"D-{int(m):02d}" for m in D_RE.findall(text)], 2)
    q = _num_sorted([f"Q-{int(m)}" for m in Q_RE.findall(text) + OQ_RE.findall(text)], 2)
    orr = _num_sorted([f"ORR-{int(m):03d}" for m in ORR_RE.findall(text)], 4)
    rfi = []
    for head, tail in RFI_RE.findall(text):
        rfi.append("RFI-" + head)
        rfi.extend("RFI-" + t for t in RFI_TAIL.findall(tail))
    rfi = sorted(set(rfi))
    found = sorted([(m.start(1), m.group(1)) for m in CODE_RE.finditer(text)
                    if sum(1 for p in m.group(1).split("_") if p.isalpha() and len(p) >= 3) >= 2]
                   + [(m.start(1), m.group(1)) for m in CODE2_RE.finditer(text)])
    codes = [c for _, c in found if c not in CODE_STOP and not c.startswith("ARCH_TAKEOFF")]
    return {"d": d, "q": q, "orr": orr, "rfi": rfi, "codes": codes}


def host_of(line: dict, element_id: str | None = None):
    """the host line id a derived line names (element id 'FW:L-<id>:...' or a 'waits for / source / beside' link)."""
    m = FW_HOST_RE.match(element_id or (line.get("location") or {}).get("element_id") or "")
    if m:
        return m.group(1)
    m = HOST_RE.search(cause_text(line))
    return m.group(1) if m else None


def classify_own(line: dict) -> dict:
    """the bucket from the line's own text only (rules 1-3 and 5-9)."""
    text = cause_text(line)
    i = ids(text)
    if i["d"]:
        return {"kind": "DESIGNER", "bucket": "+".join(i["d"]), "d_ids": i["d"]}
    if i["rfi"]:
        return {"kind": "RFI", "bucket": "+".join(i["rfi"]), "d_ids": []}
    if i["q"] or i["orr"]:
        return {"kind": "OWNER", "bucket": "+".join(i["q"] + i["orr"]), "d_ids": []}
    if i["codes"]:
        return {"kind": "REASON_CODE", "bucket": i["codes"][0], "d_ids": []}
    low = text.lower()
    if any(w in low for w in DESIGNER_WORDS):
        return {"kind": "DESIGNER_TAG", "bucket": "DESIGNER_TAG", "d_ids": []}
    if any(w in low for w in METHOD_WORDS):
        return {"kind": "METHOD_GAP", "bucket": "METHOD_GAP", "d_ids": []}
    if any(w in low for w in NOT_PRINTED_WORDS):
        return {"kind": "NOT_PRINTED", "bucket": "NOT_PRINTED", "d_ids": []}
    if text:
        return {"kind": "NAMED_TEXT", "bucket": "NAMED_TEXT", "d_ids": []}
    return {"kind": "UNNAMED", "bucket": "UNNAMED", "d_ids": []}


def classify(lid: str, records: dict, held: set, element_ids: dict | None = None, _seen=None) -> dict:
    """full R-T716-1: own ids first (rules 1-3), then a HELD host (rule 4, to the root), then own text (5-9)."""
    rec = records[lid]
    own = classify_own(rec)
    if own["kind"] in ("DESIGNER", "RFI", "OWNER"):
        return dict(own, dependent=False, host=None, root=lid)
    seen = (_seen or set()) | {lid}
    h = host_of(rec, (element_ids or {}).get(lid))
    if h and h in held and h in records and h not in seen:
        up = classify(h, records, held, element_ids, seen)
        return dict(up, dependent=True, host=h)
    return dict(own, dependent=False, host=None, root=lid)


def side(idx: dict) -> str:
    lo, hi = idx.get("held_low"), idx.get("held_high")
    if lo is not None and hi is not None:
        return "RANGE"
    if lo is not None:
        return "AT_LEAST"
    if hi is not None:
        return "AT_MOST"
    return "BLANK"


def _acc():
    return {"lines": 0, "dependent": 0, "range": 0, "range_low": 0.0, "range_high": 0.0, "at_least": 0,
            "at_least_sum": 0.0, "at_most": 0, "at_most_sum": 0.0, "blank": 0}


def add(acc: dict, idx: dict, dependent: bool = False) -> None:
    s = side(idx)
    acc["lines"] += 1
    acc["dependent"] += int(bool(dependent))
    if s == "RANGE":
        acc["range"] += 1
        acc["range_low"] += idx["held_low"]
        acc["range_high"] += idx["held_high"]
    elif s == "AT_LEAST":
        acc["at_least"] += 1
        acc["at_least_sum"] += idx["held_low"]
    elif s == "AT_MOST":
        acc["at_most"] += 1
        acc["at_most_sum"] += idx["held_high"]
    else:
        acc["blank"] += 1


def _rows(by: dict) -> list:
    return [dict(item_code=k[0], unit=k[1], **{a: (round(b, 6) if isinstance(b, float) else b) for a, b in v.items()})
            for k, v in sorted(by.items())]


def census(index_lines: list, records: dict) -> dict:
    """index_lines: the LINE_INDEX rows; records: line_id -> full line record. Only class HELD lines are counted.

    -> buckets (each HELD line in exactly one), per single D-id view (SOLE / SHARED, never re-added), findings."""
    held_ix = [i for i in index_lines if i["class"] == "HELD"]
    held = {i["line_id"] for i in held_ix}
    eids = {i["line_id"]: i["element_id"] for i in index_lines}
    buckets = defaultdict(lambda: {"kind": None, "lines": [], "by": defaultdict(_acc)})
    per_d = defaultdict(lambda: {"sole": defaultdict(_acc), "shared": defaultdict(_acc), "sole_ids": [],
                                 "shared_ids": []})
    assign = {}
    for i in held_ix:
        lid = i["line_id"]
        assert lid not in assign, f"line {lid} twice"
        c = classify(lid, records, held, eids)
        assign[lid] = {"kind": c["kind"], "bucket": c["bucket"], "dependent": c["dependent"], "host": c["host"],
                       "item_code": i["item_code"], "unit": i["unit"], "side": side(i)}
        key = (i["item_code"], i["unit"])
        b = buckets[(c["kind"], c["bucket"])]
        b["kind"] = c["kind"]
        b["lines"].append(lid)
        add(b["by"][key], i, c["dependent"])
        for d in c["d_ids"]:
            view = "sole" if len(c["d_ids"]) == 1 else "shared"
            add(per_d[d][view][key], i, c["dependent"])
            per_d[d][view + "_ids"].append(lid)
    out_b = [{"kind": k, "bucket": n, "finding": k in FINDING_KINDS, "lines": len(b["lines"]),
              "line_ids": sorted(b["lines"]), "by_family_unit": _rows(b["by"])}
             for (k, n), b in sorted(buckets.items(), key=lambda kv: (BUCKET_ORDER.index(kv[0][0]), kv[0][1]))]
    out_d = {d: {"sole_lines": len(v["sole_ids"]), "shared_lines": len(v["shared_ids"]),
                 "sole_line_ids": sorted(v["sole_ids"]), "shared_line_ids": sorted(v["shared_ids"]),
                 "sole": _rows(v["sole"]), "shared": _rows(v["shared"])}
             for d, v in sorted(per_d.items(), key=lambda kv: int(kv[0][2:]))}
    assert sum(b["lines"] for b in out_b) == len(held_ix) == len(assign)
    return {"held_lines": len(held_ix), "buckets": out_b, "per_d_id": out_d, "assignment": assign}


def canonical(obj) -> bytes:
    return json.dumps(obj, ensure_ascii=False, indent=1, sort_keys=True).encode("utf-8")
