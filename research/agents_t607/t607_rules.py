"""T-607 rules (any villa; research, unwired): a stair-piece residual that one reference row feeds into two of our
reconciliation lines (steps lm / nr and the nosing census), settled ONCE by edge id.

R-T607-1 (proposed, every villa; provenance T-607; builds on R-T412-1 (one riser, one nosing), R-T434-1 (a count governs
by the owner rule's source when consistent; checks never choose; never 'best fit'), R-T588-1 (d) (one drawn edge, one
pricing line), R-T584-1 (c) (flight step = per tread; the arrival edge is a nosing), UP-STAIR-008, OWNER_RULE_STAIRS
2026-10-24 S-9 / A8 (winders never generated; missing winder geometry HELD), ERS s.2.1-2.6):

  (a) ONE EDGE, ONE PRICING LINE. Every drawn nosing edge of a stair is claimed by exactly one line: a tread / winder
      edge by its flight's step line (B7-06, the commercial step piece holds its own nosing), a landing / floor
      (arrival) edge by the nosing line (B7-05). Steps and nosing are therefore ONE element on a tread edge and a
      nosing-only element on an arrival edge: never the same edge in both lines, never an edge in two step lines. A
      second reading of a flight (the same edge drawn on another plan: above the cut, below the cut, or a duplicate
      line) claims nothing. A winder front whose subdivision is not drawn is claimed by its HELD line and carries no
      value; a value on it is refused.
  (b) COMPLETENESS BEFORE BLAME. Before a reference's extra pieces are explained, every stair-family line in the stair
      shaft on every plan is classed: CENSUS (an edge of the governing count), DUPLICATE (same plan, same line), SECOND_
      READING (coincides, after the plans are registered on their wall lines, with a census edge of another plan),
      NAMED_OPEN (an open designer item already on the register), UNMATCHED. An UNMATCHED line is a possible piece:
      the extra stays UNRESOLVED (possible ENGINE_OMISSION) until it is classed. Never dropped.
  (c) THE EXTRA PIECES BY MECHANISM. Reference count - governing count = the extra. Each candidate mechanism is
      written with its own pieces and tested for an EXACT reproduction, never a best fit:
        SECOND_READING_SET  a combination of second-reading groups (by edge id) and open drawn items whose piece
                            count sums EXACTLY to the extra; a combination that needs a reading the governing
                            source already rejected (R-T434-1) is listed but not admissible;
        STOREY_ESTIMATE     ceil(storey rise / assumed riser) per storey reproduces the reference count for a
                            riser range (0.5 mm sweep), using printed levels only;
        PHYSICAL            UNMATCHED drawn edges (b) or a NAMED_OPEN item that a governing source admits.
      A reproduction is evidence of the reference's method, not proof: when several reproduce, all are named and none
      is chosen (R-T434-1). VERDICT on the quantity: ENGINE_RIGHT when the governing count is drawn-consistent, the
      sweep has no UNMATCHED line and every exact reproduction is non-physical (the extra pieces are not built under
      any reading); UNRESOLVED when no mechanism reproduces, or an UNMATCHED / admitted NAMED_OPEN piece could carry it.
  (d) SHARED CAUSE. When one reference cell feeds several of our comparison lines (the same count x width compared once
      as steps and once as nosings), its extra is ONE cause with one id: entered once in each line it feeds (each line
      still closes on its own), and counted ONCE in any total across lines; adding it per line is refused.
  (e) UNITS AND STATUS. nr and lm never meet; the reference's lm = his count x his own piece width (never ours); HELD is
      never 0; VERIFIED is the Checker's word; nothing is released here.
"""
from __future__ import annotations

import math
from collections import Counter
from decimal import Decimal, ROUND_CEILING, getcontext
from itertools import product

getcontext().prec = 40

CLASSES = ("CENSUS", "DUPLICATE", "SECOND_READING", "NAMED_OPEN", "UNMATCHED")
EDGE_KINDS = ("TREAD", "WINDER", "LANDING_EDGE", "FLOOR_EDGE")
MECHANISMS = ("SECOND_READING_SET", "STOREY_ESTIMATE", "PHYSICAL")
VERDICTS = ("ENGINE_RIGHT", "UNRESOLVED")


class RuleError(ValueError):
    pass


def D(x) -> Decimal:
    if x is None:
        raise RuleError("quantity unknown (None) used as a number: HELD / UNKNOWN is never 0")
    if isinstance(x, bool):
        raise RuleError("a boolean is not a quantity")
    if isinstance(x, float):
        return Decimal(repr(x))
    return Decimal(str(x))


def count(n, what="count"):
    if isinstance(n, bool) or not isinstance(n, int):
        if isinstance(n, (float, Decimal)) and D(n) == D(n).to_integral_value():
            n = int(n)
        else:
            raise RuleError(f"{what} {n!r} is not a whole number of pieces")
    if n < 0:
        raise RuleError(f"{what} {n} negative")
    return n


# ---- (b) plan registration and coincidence (translation only: plans of one file share an orientation) -----------------
def register(walls_a, walls_b, grid=1.0):
    """walls_*: end points (x, y) in mm of wall lines around the stair on plans a and b. Returns (dx, dy, coincident,
    runner_up): the translation most end-point pairs agree on (votes on a grid-mm lattice of the differences; the
    runner-up is the best translation more than 2 grid steps away), refined to the mean of the voters around it; coincident = end points of a landing within one grid step of an end point of b."""
    if not walls_a or not walls_b:
        raise RuleError("registration needs wall end points on both plans")
    votes = Counter()
    for x, y in walls_a:
        for u, v in walls_b:
            votes[(round((u - x) / grid), round((v - y) / grid))] += 1
    k, n1 = votes.most_common(1)[0]
    near = lambda c: max(abs(c[0] - k[0]), abs(c[1] - k[1])) <= 2      # noqa: E731  (rounding splits one translation)
    n1 = sum(n for c, n in votes.items() if near(c))
    n2 = max([n for c, n in votes.items() if not near(c)], default=0)
    dif = [(u - x, v - y) for x, y in walls_a for u, v in walls_b
           if near((round((u - x) / grid), round((v - y) / grid)))]
    dx = sum(d[0] for d in dif) / len(dif)
    dy = sum(d[1] for d in dif) / len(dif)
    hit = sum(1 for x, y in walls_a if any(math.hypot(x + dx - u, y + dy - v) <= grid for u, v in walls_b))
    if hit < 4 or n1 <= 2 * n2:
        raise RuleError(f"registration not unique (votes {n1} vs runner-up {n2}): plans not registered, nothing "
                        "classed")
    return dx, dy, hit, n1, n2


def seg(p, q):
    (x1, y1), (x2, y2) = p, q
    return {"mx": (x1 + x2) / 2, "my": (y1 + y2) / 2, "len": math.hypot(x2 - x1, y2 - y1),
            "ang": math.degrees(math.atan2(y2 - y1, x2 - x1)) % 180.0}


def coincide(a, b, dx=0.0, dy=0.0, tol_len=3.0, tol_pos=2.0, tol_ang=0.5):
    da = abs(a["ang"] - b["ang"]) % 180.0
    return (abs(a["len"] - b["len"]) <= tol_len and min(da, 180.0 - da) <= tol_ang
            and math.hypot(a["mx"] + dx - b["mx"], a["my"] + dy - b["my"]) <= tol_pos)


def classify(plan_lines, census, shifts, named_open=()):
    """plan_lines: {plan: {handle: seg}}; census: {handle: (edge id, plan)}; shifts: {(p, q): (dx, dy)} (p -> q).
    Returns {plan: {handle: (class, edge id or None)}}; class per R-T607-1 (b)."""
    out = {}
    for p, ls in plan_lines.items():
        out[p] = {}
        for h, s in ls.items():
            if h in census:
                if census[h][1] != p:
                    raise RuleError(f"census handle {h} filed on plan {census[h][1]}, drawn on {p}")
                out[p][h] = ("CENSUS", census[h][0])
                continue
            if h in named_open:
                out[p][h] = ("NAMED_OPEN", None)
                continue
            hit = None
            for k, (eid, q) in sorted(census.items(), key=lambda kv: (kv[1][1] != p, kv[0])):
                dx, dy = (0.0, 0.0) if q == p else shifts[(p, q)]
                if coincide(s, plan_lines[q][k], dx, dy):
                    hit = ("DUPLICATE" if q == p else "SECOND_READING", eid)
                    break
            out[p][h] = hit or ("UNMATCHED", None)
    return out


# ---- (a) one edge, one pricing line ------------------------------------------------------------------------------------
def claims(edges, step_rows, nosing_rows, second_reading_rows=()):
    """edges: {eid: {"kind": EDGE_KINDS, "value": Decimal or None (HELD)}}; step_rows / nosing_rows: {line: [eid, ...]}.
    Returns the shared-edge table {eid: {"line": line, "family": "STEP" | "NOSING"}}; refuses doubles, orphans, a tread
    edge in the nosing line, an arrival edge in a step line, a second reading claiming an edge, a valued HELD winder."""
    table = {}
    for fam, rows in (("STEP", step_rows), ("NOSING", nosing_rows)):
        for line, eids in rows.items():
            for e in eids:
                if e not in edges:
                    raise RuleError(f"{line} claims {e}, not a drawn edge of the governing count")
                if e in table:
                    raise RuleError(f"edge {e} claimed by {table[e]['line']} and {line}: one edge, one pricing line")
                k = edges[e]["kind"]
                if k not in EDGE_KINDS:
                    raise RuleError(f"edge {e}: kind {k!r} unknown")
                if fam == "STEP" and k in ("LANDING_EDGE", "FLOOR_EDGE"):
                    raise RuleError(f"arrival edge {e} in step line {line}: it is a nosing (B7-05), not a step")
                if fam == "NOSING" and k in ("TREAD", "WINDER"):
                    raise RuleError(f"tread edge {e} in nosing line {line}: the step piece holds its nosing")
                table[e] = {"line": line, "family": fam}
    for line, eids in dict(second_reading_rows).items():
        if eids:
            raise RuleError(f"second reading {line} claims {sorted(eids)}: a second reading never claims an edge")
    orphans = sorted(set(edges) - set(table))
    if orphans:
        raise RuleError(f"edges with no pricing line: {orphans}")
    for e, v in edges.items():
        if v["kind"] == "WINDER" and v.get("held") and v.get("value") is not None:
            raise RuleError(f"winder front {e} valued while its subdivision is not drawn (S-9 / A8): HELD, no value")
    return table


# ---- (c) mechanisms of the extra ---------------------------------------------------------------------------------------
OPTION_KINDS = ("NONE", "SECOND_READING", "PHYSICAL_OPEN", "REJECTED_READING")


def reproductions(extra, sources):
    """sources: {name: [(delta pieces, kind)]}, each source taken at exactly one option (a (0, "NONE") option is added
    when missing). kind: SECOND_READING (lines that repeat a census edge: never a built piece), PHYSICAL_OPEN (a drawn
    item still open on the register: could be built), REJECTED_READING (a count reading a governing source already
    rejected, R-T434-1). Returns every combination whose deltas sum EXACTLY to the extra, each with its flags."""
    extra = count(extra, "extra")
    names = sorted(sources)
    opts = []
    for n in names:
        o = []
        for d, k in sources[n]:
            if k not in OPTION_KINDS:
                raise RuleError(f"{n}: option kind {k!r} unknown")
            if not isinstance(d, int) or isinstance(d, bool):
                raise RuleError(f"{n}: delta {d!r} is not a whole number of pieces")
            if (d == 0) != (k == "NONE"):
                raise RuleError(f"{n}: a NONE option is the zero option and only it")
            o.append((d, k))
        if (0, "NONE") not in o:
            o.append((0, "NONE"))
        opts.append(o)
    out = []
    for pick in product(*opts):
        if sum(d for d, _ in pick) != extra:
            continue
        parts = {n: (d, k) for n, (d, k) in zip(names, pick) if k != "NONE"}
        out.append({"parts": {n: f"{'+' if d > 0 else ''}{d} {k}" for n, (d, k) in parts.items()},
                    "admissible": not any(k == "REJECTED_READING" for _, k in parts.values()),
                    "physical": any(k == "PHYSICAL_OPEN" for _, k in parts.values()),
                    "mechanism": "SECOND_READING_SET"})
    return out


def storey_estimate(storeys, his_total, r_lo_mm=140, r_hi_mm=200, step_mm=Decimal("0.5")):
    """storeys: [(name, low level, high level)] printed levels (m). Returns the closed riser ranges (mm) for which
    sum ceil(rise / r) == his_total, and the per-storey counts at each range."""
    his_total = count(his_total, "reference count")
    rows = []
    for name, lo, hi in storeys:
        rise = D(hi) - D(lo)
        if rise <= 0:
            raise RuleError(f"{name}: rise {rise} not positive")
        rows.append((name, rise))
    hits = []
    r = D(r_lo_mm)
    while r <= D(r_hi_mm):
        per = [(n, int((rise * 1000 / r).to_integral_value(rounding=ROUND_CEILING))) for n, rise in rows]
        if sum(c for _, c in per) == his_total:
            if hits and hits[-1]["hi_mm"] + step_mm == r and hits[-1]["per_storey"] == per:
                hits[-1]["hi_mm"] = r
            else:
                hits.append({"lo_mm": r, "hi_mm": r, "per_storey": per})
        r += step_mm
    return hits


def extra_verdict(his_nr, governing_nr, sweep_counts, reproductions):
    """sweep_counts: Counter of R-T607-1 (b) classes over every plan; reproductions: [{"mechanism", "physical": bool,
    ...}] that reproduce the extra EXACTLY. Returns (extra, verdict, reason)."""
    his_nr, governing_nr = count(his_nr, "reference count"), count(governing_nr, "governing count")
    extra = his_nr - governing_nr
    if extra <= 0:
        raise RuleError("no extra pieces: nothing to settle here")
    reproductions = [m for m in reproductions if m.get("admissible", True)]
    for m in reproductions:
        if m["mechanism"] not in MECHANISMS:
            raise RuleError(f"mechanism {m['mechanism']!r} unknown")
        if m["mechanism"] == "PHYSICAL" and not m["physical"]:
            raise RuleError("a PHYSICAL mechanism is physical by definition")
        if m["mechanism"] == "STOREY_ESTIMATE" and m["physical"]:
            raise RuleError("a storey estimate cannot add a built piece")
    if sweep_counts.get("UNMATCHED", 0):
        return extra, "UNRESOLVED", (f"{sweep_counts['UNMATCHED']} drawn stair-family line(s) unclassed: a possible "
                                     "piece (ENGINE_OMISSION candidate); classify them first")
    if not reproductions:
        return extra, "UNRESOLVED", "no mechanism reproduces the extra exactly; the reference's method is unknown"
    if any(m["physical"] for m in reproductions):
        return extra, "UNRESOLVED", "a physical reading reproduces the extra: the pieces may be built"
    names = sorted({m["mechanism"] for m in reproductions})
    return extra, "ENGINE_RIGHT", (f"{len(reproductions)} exact reproduction(s) ({', '.join(names)}), none physical; "
                                   "the extra pieces are not built under any reading; the reference's own mechanism is "
                                   "named, never chosen (R-T434-1)")


# ---- (d) one shared cause ----------------------------------------------------------------------------------------------
def shared_cause(cause_id, his_cell, lines, nr, piece_width):
    """One reference cell feeding several comparison lines {line: unit ('nr' or 'lm')}: the cause is entered once per
    line in that line's own unit (each closes alone) and once in a total. Returns {"per_line": {line: (amount, unit)},
    "total_once": (nr, lm)}."""
    if not lines:
        raise RuleError("a shared cause names the lines it feeds")
    n = count(nr, "pieces")
    w = D(piece_width)
    if w <= 0:
        raise RuleError("piece width must be positive")
    lm = n * w
    per = {}
    for ln, u in lines.items():
        if u not in ("nr", "lm"):
            raise RuleError(f"{ln}: unit {u!r} (nr or lm only; nr and lm never meet)")
        per[ln] = (n if u == "nr" else lm, u)
    return {"cause_id": cause_id, "his_cell": his_cell, "per_line": per, "total_once": (n, lm)}


def total_across_lines(entries):
    """entries: [(cause_id, nr, lm)] collected from several lines. A cause id counted once; a second entry of the same
    id with a different amount is refused (it would not be the same cause)."""
    seen = {}
    for cid, n, lm in entries:
        if cid in seen:
            if seen[cid] != (count(n), D(lm)):
                raise RuleError(f"cause {cid} entered with two amounts {seen[cid]} / {(n, lm)}")
            continue
        seen[cid] = (count(n), D(lm))
    return sum(v[0] for v in seen.values()), sum((v[1] for v in seen.values()), Decimal(0))


def summed_per_line(entries):
    """the refused way (kept so a test can show the double count it would make)"""
    raise RuleError("a shared cause summed once per line it feeds double-counts the residual (R-T607-1 (d))")
