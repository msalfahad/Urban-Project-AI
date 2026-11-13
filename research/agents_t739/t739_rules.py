"""R-T739-1 ALL-TRADE AGGREGATION STATEMENT (T-739, research; every villa on the engine's line-index scheme).

Pure functions over a committed line index (URBAN_T479_LINE_INDEX_V1 rows: line_id, item_code, unit, class,
measured_net, held_low, held_high). Nothing here reads a drawing, writes a candidate or changes a quantity.

The rule (each clause is a test in tests/t739_aggregation):
  (a) ONE STATE PER LINE. RELEASED = class RELEASED with a measured_net and no bound; EXCLUDED = class EXCLUDED with no
      quantity; a HELD line is BOUNDED (low and high), AT_LEAST (low only), AT_MOST (high only) or BLANK (neither).
      Any other combination (a HELD line with a measured_net, a RELEASED line without one or with a bound, low > high,
      an EXCLUDED line with a quantity, an unknown class) is refused (AggregationError), never repaired.
  (b) NEVER ACROSS STATES OR UNITS. A subtotal is (trade, unit, state); released, bound lows, bound highs, AT_LEAST
      lows and AT_MOST highs are separate sums; a BLANK line is counted, never summed, never 0. A trade x unit with any
      HELD line prints no single total, only 'released + held low .. released + held high' and the open counts.
  (c) EXACT RE-ADD. Every subtotal is computed twice in Decimal (from the lines directly, and from per-item-code
      subtotals) and the two must be equal; a difference refuses the statement.
  (d) CHAIN RE-ADD (component -> line). Where a committed record states a line's components (before / after of an
      integration package), the index must equal the record's 'after' and the predecessor index its 'before';
      every line no record names must be byte-equal between the two indexes. Lines with no committed component record
      are counted per trade and named as such (their gross / deductions / additions live only in the private run
      output), never treated as checked.
  (e) A HELD LINE CARRIES A CAUSE OR A FINDING. The cause is the record of the LATEST task (task number) that names the
      line id (full id, or a unique prefix of at least 10 characters) with a cause text; an APPLIED Checker downgrade
      on the index comes next; then a merged whole-candidate cause-class census (one bucket per HELD line: a D-id, an
      owner question, a method gap ...); a HELD line with none is a finding (F-T739-1), listed by id, never given a
      cause. The census bucket is also printed beside every HELD line as its cause class.
  (f) BESIDE, NEVER MIXED. The released V2.9 + route G figures and the freelancer reference are printed in their own
      columns / sections; the freelancer is compared only through the declared key map, in the same unit, as a range;
      a key with a BLANK answer gives 'at least x %, upper end open', never a single %.
"""
from __future__ import annotations

import re
from collections import defaultdict
from decimal import Decimal

RULE_ID, RULE_VERSION = "R-T739-1", "1.0.0"
RELEASED, BOUNDED, AT_LEAST, AT_MOST, BLANK, EXCLUDED = "RELEASED", "BOUNDED", "AT_LEAST", "AT_MOST", "BLANK", "EXCLUDED"
STATES = (RELEASED, BOUNDED, AT_LEAST, AT_MOST, BLANK, EXCLUDED)
HELD_STATES = (BOUNDED, AT_LEAST, AT_MOST, BLANK)
FULL_ID = re.compile(r"^L-[0-9a-f]{20}$")
PREFIX_ID = re.compile(r"^L-[0-9a-f]{8,19}$")


class AggregationError(ValueError):
    pass


def D(x) -> Decimal:
    """exact decimal of a JSON number (repr keeps the shortest round-trip digits)."""
    if isinstance(x, bool) or not isinstance(x, (int, float, str, Decimal)):
        raise AggregationError(f"not a number: {x!r}")
    return Decimal(repr(x)) if isinstance(x, float) else Decimal(str(x))


def fmt(x: Decimal) -> str:
    return format(x.normalize(), "f") if x != 0 else "0"


def state_of(ln: dict) -> str:
    """(a) the one state of a line, or AggregationError."""
    c, q, lo, hi = ln.get("class"), ln.get("measured_net"), ln.get("held_low"), ln.get("held_high")
    lid = ln.get("line_id")
    if c == "RELEASED":
        if q is None or lo is not None or hi is not None:
            raise AggregationError(f"{lid}: RELEASED needs a measured_net and no bound")
        return RELEASED
    if c == "EXCLUDED":
        if q is not None or lo is not None or hi is not None:
            raise AggregationError(f"{lid}: EXCLUDED carries a quantity")
        return EXCLUDED
    if c == "HELD":
        if q is not None:
            raise AggregationError(f"{lid}: HELD line with a measured_net (a held quantity is never released)")
        if lo is not None and hi is not None:
            if D(lo) > D(hi):
                raise AggregationError(f"{lid}: held low > high")
            return BOUNDED
        if lo is not None:
            return AT_LEAST
        if hi is not None:
            return AT_MOST
        return BLANK
    raise AggregationError(f"{lid}: unknown class {c!r}")


def _cell():
    return {"n": 0, "released": Decimal(0), "low": Decimal(0), "high": Decimal(0), "lines": []}


def _add(cell, ln, st):
    cell["n"] += 1
    cell["lines"].append(ln["line_id"])
    if st == RELEASED:
        cell["released"] += D(ln["measured_net"])
    elif st == BOUNDED:
        cell["low"] += D(ln["held_low"])
        cell["high"] += D(ln["held_high"])
    elif st == AT_LEAST:
        cell["low"] += D(ln["held_low"])
    elif st == AT_MOST:
        cell["high"] += D(ln["held_high"])


def aggregate(lines: list, trade_of) -> dict:
    """(b) + (c): {(trade, unit): {state: cell}} with the exact second-path re-add. trade_of(item_code) -> trade."""
    seen = set()
    direct = defaultdict(lambda: {s: _cell() for s in STATES})
    by_code = defaultdict(lambda: {s: _cell() for s in STATES})
    for ln in lines:
        lid = ln["line_id"]
        if lid in seen:
            raise AggregationError(f"{lid}: line listed twice (one line, one count)")
        seen.add(lid)
        st = state_of(ln)
        unit = ln.get("unit")
        if not unit:
            raise AggregationError(f"{lid}: no unit (a quantity without a unit is never summed)")
        t = trade_of(ln["item_code"])
        _add(direct[(t, unit)][st], ln, st)
        _add(by_code[(t, ln["item_code"], unit)][st], ln, st)
    # second path: trade x unit re-added from its item-code subtotals
    for (t, unit), cells in direct.items():
        for st in STATES:
            agg = {"n": 0, "released": Decimal(0), "low": Decimal(0), "high": Decimal(0)}
            for (t2, _code, u2), cc in by_code.items():
                if (t2, u2) == (t, unit):
                    for k in agg:
                        agg[k] += cc[st][k]
            for k in agg:
                if agg[k] != cells[st][k]:
                    raise AggregationError(f"re-add differs: {t} {unit} {st} {k} {cells[st][k]} != {agg[k]}")
    return {"trade_unit": dict(direct), "code_unit": dict(by_code)}


def range_text(cells: dict, unit: str) -> dict:
    """(b) what a trade x unit may print: a single total only when nothing is held."""
    rel = cells[RELEASED]["released"]
    held_n = sum(cells[s]["n"] for s in HELD_STATES)
    if held_n == 0:
        return {"total": fmt(rel), "text": f"{fmt(rel)} {unit} (all released)"}
    lo = rel + cells[BOUNDED]["low"]
    hi = rel + cells[BOUNDED]["high"]
    parts = [f"released {fmt(rel)} ({cells[RELEASED]['n']})" if cells[RELEASED]["n"] else "released none"]
    if cells[BOUNDED]["n"]:
        parts.append(f"+ bounded {fmt(cells[BOUNDED]['low'])} .. {fmt(cells[BOUNDED]['high'])} ({cells[BOUNDED]['n']})"
                     f" = {fmt(lo)} .. {fmt(hi)} {unit}")
    if cells[AT_LEAST]["n"]:
        parts.append(f"+ {cells[AT_LEAST]['n']} AT_LEAST (>= {fmt(cells[AT_LEAST]['low'])})")
    if cells[AT_MOST]["n"]:
        parts.append(f"+ {cells[AT_MOST]['n']} AT_MOST (<= {fmt(cells[AT_MOST]['high'])})")
    if cells[BLANK]["n"]:
        parts.append(f"+ {cells[BLANK]['n']} BLANK (no bound: upper end open)")
    return {"total": None, "text": "NO SINGLE TOTAL: " + " ".join(parts)}


def resolve_prefix(lid: str, index_ids: set, by_prefix: dict):
    if FULL_ID.match(lid):
        return lid if lid in index_ids else None
    if PREFIX_ID.match(lid):
        hits = by_prefix.get(lid[:10], [])
        hits = [h for h in hits if h.startswith(lid)]
        return hits[0] if len(hits) == 1 else None
    return None


def resolve_causes(held_ids: list, records: list, downgrades: dict, census: dict | None = None) -> tuple[dict, list]:
    """(e) records: [(task_number, task_label, line_id, cause_text)], already resolved to full ids.
    downgrades: {line_id: 'DG-... reason'} (APPLIED on the index); census: {line_id: (label, text)} a whole-candidate
    cause-class census used only when no detailed record or downgrade states the line. Returns ({line_id: cause}, findings)."""
    census = census or {}
    by_line = defaultdict(list)
    for tn, label, lid, text in records:
        if text and str(text).strip():
            by_line[lid].append((tn, label, str(text).strip()))
    out, findings = {}, []
    for lid in held_ids:
        recs = sorted(by_line.get(lid, []), key=lambda r: -r[0])
        if recs:
            tn, label, text = recs[0]
            also = sorted({r[1] for r in recs[1:]} - {label})
            out[lid] = {"cause": text, "source": label, "also_stated_by": also}
        elif lid in downgrades:
            out[lid] = {"cause": downgrades[lid], "source": "Checker downgrade (APPLIED on the index)",
                        "also_stated_by": []}
        elif lid in census:
            label, text = census[lid]
            out[lid] = {"cause": text, "source": label, "also_stated_by": []}
        else:
            findings.append(lid)
    return out, findings


def pct_range(rel: Decimal, lo: Decimal, hi: Decimal, ref: Decimal, open_upper: bool) -> str:
    """(f) freelancer diagnostic: (engine - ref) / ref as a range; open when a BLANK / AT_LEAST answer exists."""
    if ref == 0:
        return "reference 0: no %"
    a = (rel + lo - ref) / ref * 100
    b = (rel + hi - ref) / ref * 100
    qa, qb = a.quantize(Decimal("0.01")), b.quantize(Decimal("0.01"))
    if open_upper:
        return f"at least {qa:+} %, upper end open"
    return f"{qa:+} %" if qa == qb else f"{qa:+} .. {qb:+} %"
