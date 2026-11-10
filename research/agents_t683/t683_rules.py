"""T-683 rules (project-agnostic; scope: any candidate line index URBAN_T479_LINE_INDEX_V1 of any villa, any reference
workbook). Research only, unwired: reads committed files (and, for R-T683-3, the private reference workbook copy), computes
no quantity of any element, changes no line. Extends R-T679-1 1.0.0 (research/agents_t679/t679_rules.py), which is used
unchanged.

R-T683-1 1.0.0  STALE CENSUS CLASS. A census cause class 'MEASURABLE NOW' means "a drawn value exists in merged research
    and is not wired". Provenance: T-679 statement on V3.0.65 (the boundary band kept its V3.0.63 class after T-668 wired
    it); T-683 on V3.0.66 (T-677 wired 16 lintels + ST-03 whose T-673 class stayed 'MEASURABLE NOW'); ERS s.3 statuses.
    (a) A HELD line whose latest census class is MEASURABLE NOW and which a merged integration package NEWER than that
        census changed (any wiring action on that line) is STALE: the statement REFUSES it unless a restatement gives the
        residual cause that keeps it HELD after the wiring (class DESIGNER ITEM or OPEN BOUND, the named item, the source).
    (b) A restatement is accepted only for a line that a package wired (no re-classing of a line nobody wired); a
        restatement whose class is MEASURABLE NOW is REFUSED (that is the stale class itself).
    (c) The candidate must carry the package's after-state: a BOUND action's low / high must equal the index bound to the
        stored digit, a LOWER_ONLY / ADD_LOWER_ONLY action leaves the index blank (the floor is beside, never a bound);
        otherwise REFUSED (the package is not the one this candidate was built from).
    (d) A line ADDED by a package (no census row can exist yet) takes its cause from the package row (restatement
        required, same as (a)).
    (e) Floors beside (AT_LEAST values of blank lines) are listed beside the scope with their source and summed only
        among themselves; never into the bounded low, never into the engine range.

R-T683-2 1.0.0  SCOPE BRIDGE OF A REFERENCE KEY. Provenance: F-T679-2 (the column cover total holds lift pit walls that
    the key's engine side does not hold); owner 2026-11-08 12:40 (7) reference apart; R-T679-1 (e).
    (a) The cover total is split by the reference's OWN sub-totals into components that re-add to it exactly (else
        REFUSED); each component names the engine scope that answers it: item codes and, where one item code holds
        two physical elements of which only one is in the reference, the element ids (element-level scope). The
        re-add is exact at 6 dp (a cover total stored as a binary float, e.g. 59.81739999999999, is read at 6 dp).
    (b) Per component: reference, engine released, bounded, blank, and the difference reference - released; the % is
        printed only when the component holds no HELD line (a HELD line inside a component is NEVER agreement, even
        when reference = released).
    (c) A component with no engine line is NO_ENGINE_LINE; an engine element inside the key's item codes with no
        reference component is NOT_COMPARABLE (listed, never folded into another component).
    (d) A key-map change this implies is written only as a PROPOSED new key-map version beside the statement; the key
        map of record is never edited.

R-T683-3 1.0.0  REFERENCE ARITHMETIC. Provenance: F-T679-3 (beam cover total vs the T-545 row sum, 0.128 m3); T-545
    BM-ARITH; ERS s.2.6 (reconcile to the mathematical cause).
    (a) The cell the keyed cover total reads is expanded through its additive chain (sub-totals, carry-forward /
        carry-before cells, SUM ranges) down to the item rows; an item row of the sheet above the cover that the chain
        never reaches is OMITTED_ROW (its value named), one it reaches twice is DOUBLE_ROW.
    (b) The keyed cover total stays the value of record; the corrected row sum is printed beside with the residual
        cover - rows = - sum(omitted) + sum(double), exact; the engine difference is printed against both, labelled.
    (c) Such a residual is REFERENCE ARITHMETIC: it is no engine verdict, moves no quantity and is never used to make the
        engine agree.
"""
from __future__ import annotations

import re
from collections import OrderedDict
from decimal import Decimal

from t679_rules import (CAUSE_CLASSES, HELD, OPEN, D, Refused, add, empty_bucket, merge, pct, s,  # noqa: F401
                        scope_view, sub)

MEASURABLE_NOW = "MEASURABLE NOW"
LOWER_ONLY_ACTIONS = ("LOWER_ONLY", "ADD_LOWER_ONLY")
BOUND_ACTIONS = ("BOUND", "ADD_SHARED", "ADD_COMPANION")


# ------------------------------------------------------------------------------------------------ R-T683-1
def wired_map(packages: list[dict]) -> dict[str, dict]:
    """packages: [{task, base_version, rows: [{line_id, action, after, beside}]}] -> line_id -> the latest wiring row."""
    out: dict[str, dict] = {}
    for p in sorted(packages, key=lambda p: version_key(p["base_version"])):
        for r in p["rows"]:
            out[r["line_id"]] = {"task": p["task"], "base_version": p["base_version"], **r}
    return out


def version_key(v: str) -> tuple:
    m = re.search(r"(\d+)\.(\d+)\.(\d+)$", v)
    if not m:
        raise Refused(f"version {v!r} unreadable")
    return tuple(int(x) for x in m.groups())


def restate(causes: dict[str, dict], census_version: dict[str, str], lines: dict[str, dict],
            packages: list[dict], restatements: dict[str, dict]) -> tuple[dict, list[dict], list[dict]]:
    """Apply R-T683-1. causes: line_id -> {cause_class, named, source}; census_version: line_id -> candidate version the
    census read; lines: line_id -> index line (HELD lines of the trade). Returns (causes', restated rows, floors beside)."""
    wm = wired_map(packages)
    out = dict(causes)
    rows, floors = [], []
    for lid, rs in restatements.items():
        if lid not in wm:
            raise Refused(f"R-T683-1 (b): {lid} restated but no package wired it (no re-classing of an unwired line)")
        if rs.get("cause_class") not in CAUSE_CLASSES or rs["cause_class"] == MEASURABLE_NOW:
            raise Refused(f"R-T683-1 (b): {lid} restated to {rs.get('cause_class')!r}: the residual cause must be "
                          "DESIGNER ITEM or OPEN BOUND")
        if not rs.get("named") or not rs.get("source"):
            raise Refused(f"R-T683-1 (b): {lid} restatement names no item / source")
    for lid, ln in lines.items():
        if ln["class"] != HELD:
            continue
        w = wm.get(lid)
        c = out.get(lid)
        newer = w is not None and (c is None or version_key(w["base_version"]) >= version_key(
            census_version.get(lid, "V0.0.0")))
        stale = w is not None and newer and (c is None or c["cause_class"] == MEASURABLE_NOW)
        if w is not None:
            check_after(lid, ln, w)
            b = w.get("beside")
            if w["action"] in LOWER_ONLY_ACTIONS and b and b.get("kind") == "AT_LEAST_M3":
                floors.append(OrderedDict(line_id=lid, at_least=s(D(b["value"])), source=f"{w['task']} {w['action']}",
                                          basis=b.get("basis")))
        if not stale:
            continue
        rs = restatements.get(lid)
        if rs is None:
            raise Refused(f"R-T683-1 (a): {lid} census class {c['cause_class'] if c else None!r} "
                          f"({c['source'] if c else 'no census'}) is stale: {w['task']} wired it ({w['action']}); "
                          "restate the residual cause")
        before = c["cause_class"] if c else None
        out[lid] = {"cause_class": rs["cause_class"], "named": rs["named"], "source": rs["source"]}
        rows.append(OrderedDict(line_id=lid, element_id=ln.get("element_id"), wired_by=f"{w['task']} {w['action']}",
                                class_before=before, source_before=c["source"] if c else "none (line added)",
                                class_after=rs["cause_class"], residual=rs["named"]))
    unused = [lid for lid in restatements if lid not in {r["line_id"] for r in rows}]
    if unused:
        raise Refused(f"R-T683-1 (b): restatements for lines that are not stale: {unused}")
    return out, rows, floors


def check_after(lid: str, ln: dict, w: dict) -> None:
    lo, hi = ln.get("held_low"), ln.get("held_high")
    a = w.get("after") or {}
    if w["action"] in LOWER_ONLY_ACTIONS:
        if lo is not None or hi is not None:
            raise Refused(f"R-T683-1 (c): {lid}: {w['action']} must leave the index blank (floor beside), index has "
                          f"{lo} .. {hi}")
        return
    if w["action"] in BOUND_ACTIONS:
        if lo is None or hi is None or D(lo) != D(a.get("low")) or D(hi) != D(a.get("high")):
            raise Refused(f"R-T683-1 (c): {lid}: index {lo} .. {hi} != {w['task']} after {a.get('low')} .. "
                          f"{a.get('high')}")


# ------------------------------------------------------------------------------------------------ R-T683-2
def bridge(key: str, reference_total, components: list[dict], lines: list[dict]) -> OrderedDict:
    """components: [{name, reference, engine: {item_codes: [...], element_ids: [...] or None}, note}];
    lines: index lines of the trade (class, item_code, element_id, measured_net, held_low, held_high)."""
    ref = D(reference_total)
    tot = Decimal(0)
    for c in components:
        tot = add(tot, D(c["reference"]))
    q = Decimal("0.000001")  # cover totals are stored as binary floats (59.81739999999999): compared at 6 dp
    if tot.quantize(q) != ref.quantize(q):
        raise Refused(f"R-T683-2 (a): {key} components re-add to {s(tot)}, not the cover total {s(ref)}")
    ref = ref.quantize(q)
    claimed: dict[str, str] = {}
    out_rows = []
    for c in components:
        e = c.get("engine") or {}
        codes, els = e.get("item_codes") or [], e.get("element_ids")
        acc = empty_bucket()
        n = 0
        for ln in lines:
            if ln["item_code"] not in codes or (els is not None and ln["element_id"] not in els):
                continue
            if ln["line_id"] in claimed:
                raise Refused(f"R-T683-2 (a): {ln['line_id']} answers {claimed[ln['line_id']]} and {c['name']}")
            claimed[ln["line_id"]] = c["name"]
            n += 1
            put_line(acc, ln)
        v = scope_view(acc)
        r = D(c["reference"])
        held = acc["held_bounded_lines"] + acc["held_blank_lines"]
        row = OrderedDict(component=c["name"], reference=s(r), engine_scope=e, engine=v,
                          difference_ref_minus_released=s(sub(r, acc["released"])))
        if n == 0:
            row["status"] = "NO_ENGINE_LINE"
            row["pct_of_reference"] = None
        elif held:
            row["status"] = "HELD inside: not agreement"
            row["pct_of_reference"] = None
        else:
            row["status"] = "RELEASED only"
            row["pct_of_reference"] = s(pct(sub(r, acc["released"]), r)) if r != 0 else None
        row["note"] = c.get("note")
        out_rows.append(row)
    return OrderedDict(key=key, reference=s(ref), components=out_rows, claimed_lines=len(claimed))


def not_comparable(lines: list[dict], key_codes: list[str], claimed_bridge: OrderedDict, all_components: list[dict]):
    """(c): engine lines of the key's item codes (plus the bridge's) that no component claims."""
    claimed = set()
    for c in all_components:
        e = c.get("engine") or {}
        for ln in lines:
            if ln["item_code"] in (e.get("item_codes") or []) and (e.get("element_ids") is None
                                                                  or ln["element_id"] in e["element_ids"]):
                claimed.add(ln["line_id"])
    codes = set(key_codes)
    for c in all_components:
        codes |= set((c.get("engine") or {}).get("item_codes") or [])
    return [OrderedDict(line_id=ln["line_id"], item_code=ln["item_code"], element_id=ln["element_id"],
                        cls=ln["class"]) for ln in lines if ln["item_code"] in codes and ln["line_id"] not in claimed
            and ln["class"] != "EXCLUDED"]


def put_line(acc: dict, ln: dict) -> None:
    acc["lines"] += 1
    if ln["class"] == "RELEASED":
        acc["released_lines"] += 1
        acc["released"] = add(acc["released"], D(ln["measured_net"]))
    elif ln["class"] == HELD:
        if ln.get("held_low") is None:
            acc["held_blank_lines"] += 1
        else:
            acc["held_bounded_lines"] += 1
            acc["held_low"] = add(acc["held_low"], D(ln["held_low"]))
            acc["held_high"] = add(acc["held_high"], D(ln["held_high"]))
    else:
        acc["excluded_lines"] += 1


# ------------------------------------------------------------------------------------------------ R-T683-3
TERM = r"(?:SUM\(([A-Z]+)(\d+):([A-Z]+)(\d+)\)|([A-Z]+)(\d+))"
ADDITIVE_RE = re.compile(r"^=" + TERM + r"(?:\+" + TERM + r")*$")
TERM_RE = re.compile(TERM)


def col_no(letters: str) -> int:
    n = 0
    for ch in letters:
        n = n * 26 + ord(ch) - 64
    return n


def refs(f: str) -> list[tuple[int, int]]:
    out = []
    for m in TERM_RE.finditer(f.replace(" ", "")):
        if m.group(1):
            c1, r1, c2, r2 = col_no(m.group(1)), int(m.group(2)), col_no(m.group(3)), int(m.group(4))
            out += [(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)]
        else:
            out.append((int(m.group(6)), col_no(m.group(5))))
    return out


def is_chain(cells: dict, at: tuple[int, int], item_col: int) -> bool:
    """a sub-total / carry cell: purely additive AND (outside the item column, or adding item-column cells). An item-column
    cell that only copies another column (=E14) is an item row, not a chain cell."""
    f = cells.get(at)
    if not (isinstance(f, str) and ADDITIVE_RE.match(f.replace(" ", ""))):
        return False
    return at[1] != item_col or any(c == item_col for (_, c) in refs(f))


def expand(cells: dict, at: tuple[int, int], item_col: int, depth: int = 0) -> dict[tuple[int, int], int]:
    """(a): the item cells a cell adds up, with multiplicity (chain cells expanded, anything else a leaf)."""
    if depth > 50:
        raise Refused(f"R-T683-3: reference chain too deep at {at}")
    if not is_chain(cells, at, item_col):
        return {at: 1}
    out: dict[tuple[int, int], int] = {}
    for t in refs(cells[at]):
        if cells.get(t) is None:
            continue
        for k, n in expand(cells, t, item_col, depth + 1).items():
            out[k] = out.get(k, 0) + n
    return out


def region(reach: dict, cover: tuple[int, int], item_col: int) -> tuple[int, int]:
    rows = [r for (r, c) in reach if c == item_col]
    if not rows:
        return (cover[0], cover[0])
    return (min(rows), cover[0])


def items(cells: dict, values: dict, cover: tuple[int, int], item_col: int) -> list[tuple[int, object]]:
    """item rows of the cover's region: item-column cells from the first row the chain reaches up to the cover row,
    non-zero numbers, not chain cells."""
    reach = expand(cells, cover, item_col)
    lo, hi = region(reach, cover, item_col)
    out = []
    for (r, c), v in sorted(values.items()):
        if c != item_col or not (lo <= r < hi) or isinstance(v, bool) or not isinstance(v, (int, float)) or v == 0:
            continue
        if is_chain(cells, (r, c), item_col):
            continue
        out.append((r, v))
    return out


def audit_cover(cells: dict, values: dict, cover: tuple[int, int], item_col: int) -> list[dict]:
    """cells / values: (row, col) -> formula text / cached value of ONE sheet; cover: the cell the keyed cover total
    reads. OMITTED_ROW: an item row of the region the chain never reaches; DOUBLE_ROW: one it reaches more than once."""
    reach = expand(cells, cover, item_col)
    out = []
    for r, v in items(cells, values, cover, item_col):
        n = reach.get((r, item_col), 0)
        if n == 0:
            out.append({"kind": "OMITTED_ROW", "row": r, "value": v})
        elif n > 1:
            out.append({"kind": "DOUBLE_ROW", "row": r, "times": n, "value": v * (n - 1)})
    return out


def item_values(cells: dict, values: dict, cover: tuple[int, int], item_col: int) -> list:
    """the item-row values of the region (each once): the corrected row sum of (b)."""
    return [v for _, v in items(cells, values, cover, item_col)]


def arithmetic(cover, row_items: list, findings: list[dict]) -> OrderedDict:
    """(b): cover total vs the exact row sum; residual explained by the findings, else REFUSED."""
    rows = Decimal(0)
    for v in row_items:
        rows = add(rows, D(v))
    cov = D(cover)
    expl = Decimal(0)
    for f in findings:
        v = D(f["value"])
        expl = sub(expl, v) if f["kind"] == "OMITTED_ROW" else add(expl, v)
    resid = sub(cov, rows)
    q = Decimal("0.000001")
    if resid.quantize(q) != expl.quantize(q):
        raise Refused(f"R-T683-3 (b): cover - rows = {s(resid)} not explained by the findings ({s(expl)})")
    return OrderedDict(cover_total=s(cov.quantize(q)), row_sum=s(rows.quantize(q)),
                       cover_minus_rows=s(resid.quantize(q)), explained_by=findings,
                       class_="REFERENCE ARITHMETIC (no engine verdict, no quantity moved)")
