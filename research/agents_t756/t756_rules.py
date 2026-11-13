"""R-T756-1 .. -4 1.0.0 (every villa): exterior render / paint face ledger re-based onto a candidate line index
(OWNER RULE PAINT 2026-11-12, UP-FIN-PAINT-002: external paint = external plaster of the same faces, edges and corners
are lm; Q-73 A full openings on the face that holds them; R-T305-*, R-T311-*, R-T751-1..4, R-T754-1..4 unchanged and
in force; UP-QTY-STATUS-001 statuses).

Physical element: each external rendered face (storey band, parapet outer / inner / top, plinth, slab-edge band), its
gross m2, its holes by opening id, and the lm arrises it owns, bound to ONE line of the candidate of record.

R-T756-1 RE-BASE BY ID, NEVER BY POSITION. A source row (face, component, opening, edge) names the line it was bound to
  (a line id, or a stage key with its proposed element id and line id). Against the target line index it is:
  LIVE      the named line id is in the index with the same item code, element id and unit as recorded;
  STALE     the named line id is absent, or present with another item / element / unit (stop: never re-bound silently);
  NEW_FREE  a stage key whose proposed element id AND line id are both absent from the index (the line is ADDED at the
            wiring package);
  COLLISION a stage key whose element id or line id is already used by another line (stop);
  NOT_A_FACE / OTHER_TRADE / PARKED  a named, cited reason for no finish line (kept as a row, never dropped);
  MISSING   no line and no stage key: the row is listed by its own id with its quantity, never dropped and never 0.
  Count out = count in (asserted).
R-T756-2 PAINT = RENDER OF THE SAME FACE. Per face: paint m2 = render m2 (net of its holes, holes taken once on the
  render) minus only a part the drawing finishes otherwise (printed cladding / tiling / stone; a material NOT printed
  is not a deduction). A blank render face gives a blank paint face (never 0); a line holding one blank face is blank
  with its valued part shown beside it. Bounds 0 <= lo <= hi with hi > 0 (a lower bound 0 is allowed only as a bound,
  e.g. a face whose owner is another trade); a point 0 is refused (a NOT_A_FACE row holds no area at all).
R-T756-3 EDGE DELTA BY LINE ID. A merged verdict that moves exterior arris lm is applied line by line: each delta
  names the line id, its before (must equal the index value) and after; the sum of (after - before) must equal the
  verdict's stated total move exactly (residual 0); a host change without a quantity change is a re-binding, not a
  delta. A delta on an absent line, a before that differs from the index, or a total that does not close is refused.
R-T756-4 READY-TO-WIRE ROW. One row per target line: CHANGE (live line, new figure), ADD (NEW_FREE key), KEEP (live
  line, unchanged figure), with before / after / status / source verdict. A HELD source never becomes RELEASED or
  VERIFIED here; a blank stays blank; an ADD on a non-free id is refused; every row names its source records.
"""
from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

RULE_IDS = ("R-T756-1", "R-T756-2", "R-T756-3", "R-T756-4")
VERSION = "1.0.0"
Q = Decimal("0.000001")
REASONS = ("NOT_A_FACE", "OTHER_TRADE", "PARKED")
STATES = ("LIVE", "STALE", "NEW_FREE", "COLLISION", "MISSING") + REASONS


class RuleError(ValueError):
    pass


def D(x):
    return None if x is None or x == "" else Decimal(str(x))


def s6(x):
    return "" if x is None else str(D(x).quantize(Q, rounding=ROUND_HALF_UP))


# R-T756-1 ------------------------------------------------------------------------------------------------------
def index_maps(lines):
    """lines: iterable of dicts with line_id, item_code, element_id, unit -> (by_id, by_element)."""
    by_id, by_el = {}, {}
    for l in lines:
        if l["line_id"] in by_id:
            raise RuleError(f"duplicate line id {l['line_id']} in the index")
        by_id[l["line_id"]] = l
        by_el.setdefault(l["element_id"], []).append(l["line_id"])
    return by_id, by_el


def rebase(row_id, ref, maps):
    """ref: {'kind': 'LINE', 'line_id', 'item_code', 'element_id', 'unit'}
           | {'kind': 'NEW', 'line_id', 'element_id'}
           | {'kind': <REASONS>, 'cite'} | {'kind': 'NONE'}.
    -> {'row': row_id, 'state', 'line_id', 'why'}."""
    if not row_id:
        raise RuleError("a source row without its own id cannot be re-based")
    by_id, by_el = maps
    k = ref.get("kind")
    if k == "LINE":
        l = by_id.get(ref["line_id"])
        if l is None:
            return {"row": row_id, "state": "STALE", "line_id": ref["line_id"], "why": "line id absent from the index"}
        diff = [f for f in ("item_code", "element_id", "unit") if ref.get(f) is not None and l[f] != ref[f]]
        if diff:
            return {"row": row_id, "state": "STALE", "line_id": ref["line_id"],
                    "why": "changed: " + ", ".join(f"{f} {ref[f]} -> {l[f]}" for f in diff)}
        return {"row": row_id, "state": "LIVE", "line_id": ref["line_id"], "why": ""}
    if k == "NEW":
        if not ref.get("line_id") or not ref.get("element_id"):
            raise RuleError(f"{row_id}: a NEW key needs its proposed line id and element id")
        hit = []
        if ref["line_id"] in by_id:
            hit.append(f"line id {ref['line_id']} used")
        if ref["element_id"] in by_el:
            hit.append(f"element id {ref['element_id']} used by {','.join(by_el[ref['element_id']])}")
        if hit:
            return {"row": row_id, "state": "COLLISION", "line_id": ref["line_id"], "why": "; ".join(hit)}
        return {"row": row_id, "state": "NEW_FREE", "line_id": ref["line_id"], "why": "added at the wiring package"}
    if k in REASONS:
        if not ref.get("cite"):
            raise RuleError(f"{row_id}: {k} needs its cited record")
        return {"row": row_id, "state": k, "line_id": "", "why": ref["cite"]}
    if k == "NONE":
        return {"row": row_id, "state": "MISSING", "line_id": "", "why": ref.get("cite") or "no line, no stage key"}
    raise RuleError(f"{row_id}: unknown reference kind {k}")


def rebase_all(rows, maps):
    """rows: [(row_id, ref)] -> results; count out = count in, ids unique (never dropped, never doubled)."""
    ids = [r for r, _ in rows]
    if len(ids) != len(set(ids)):
        raise RuleError("a source row id appears twice")
    out = [rebase(r, ref, maps) for r, ref in rows]
    assert len(out) == len(rows)
    return out


# R-T756-2 ------------------------------------------------------------------------------------------------------
def face_paint(face_id, render_lo, render_hi, other_finish_lo=None, other_finish_hi=None, printed=False):
    """-> {'face', 'render': [lo, hi] | None, 'paint': [lo, hi] | None, 'state'}.
    other_finish_*: a part of the face finished otherwise; deducted only when its material is PRINTED."""
    lo, hi = D(render_lo), D(render_hi)
    if (lo is None) != (hi is None):
        raise RuleError(f"{face_id}: half a bound")
    if lo is None:
        return {"face": face_id, "render": None, "paint": None, "state": "BLANK"}
    if lo < 0 or hi < lo or hi <= 0:
        raise RuleError(f"{face_id}: render {lo} .. {hi} refused (lo >= 0, lo <= hi, hi > 0; a point 0 is not a face)")
    flo, fhi = D(other_finish_lo) or Decimal(0), D(other_finish_hi) or Decimal(0)
    if not printed:
        flo = fhi = Decimal(0)
    if flo < 0 or fhi < flo or fhi > lo:
        raise RuleError(f"{face_id}: other finish {flo} .. {fhi} outside the face")
    p = (lo - fhi, hi - flo)
    return {"face": face_id, "render": [s6(lo), s6(hi)], "paint": [s6(p[0]), s6(p[1])],
            "state": "POINT" if lo == hi and flo == fhi else "BOUNDED"}


def line_total(faces):
    """faces: face_paint results of one line -> {'render', 'paint', 'blank_faces', 'valued_part'}."""
    blanks = [f["face"] for f in faces if f["paint"] is None]
    val = [f for f in faces if f["paint"] is not None]
    rl = sum((D(f["render"][0]) for f in val), Decimal(0))
    rh = sum((D(f["render"][1]) for f in val), Decimal(0))
    pl = sum((D(f["paint"][0]) for f in val), Decimal(0))
    ph = sum((D(f["paint"][1]) for f in val), Decimal(0))
    part = {"render": [s6(rl), s6(rh)], "paint": [s6(pl), s6(ph)]}
    if blanks:
        return {"render": None, "paint": None, "blank_faces": blanks, "valued_part": part if val else None}
    return {"render": part["render"], "paint": part["paint"], "blank_faces": [], "valued_part": None}


def corners_in_band(directions_deg, band_h, closed=True, tol_deg=Decimal("0.01")):
    """A plan outline in one height band, as the direction of each successive face (degrees). A junction is a corner
    only where the direction turns (R-T754-3 analogue: coplanar faces carry no arris). -> (count, lm)."""
    h = D(band_h)
    if h is None:
        return None, None
    if h <= 0 or h > 20:
        raise RuleError(f"band height {h} m refused (<= 0, or millimetres read as metres)")
    d = [D(x) for x in directions_deg]
    pairs = list(zip(d, d[1:] + d[:1])) if closed else list(zip(d, d[1:]))
    n = 0
    for a, b in pairs:
        turn = abs((b - a + 180) % 360 - 180)
        if turn > tol_deg:
            n += 1
    return n, s6(h * n)


def band_m2(length, depth):
    """A slab-edge band: depth not printed -> None (HELD blank), never 0."""
    L, t = D(length), D(depth)
    if L is None or L <= 0:
        raise RuleError("band length missing or <= 0")
    if t is None:
        return None
    if t <= 0 or t > 20 or L > 1000:
        raise RuleError(f"band {L} x {t} m refused (<= 0, or millimetres read as metres)")
    return s6(L * t)


# R-T756-3 ------------------------------------------------------------------------------------------------------
def apply_deltas(index_values, deltas, verdict_total):
    """index_values: {line_id: (lo, hi)}; deltas: [{'line_id', 'before': (lo, hi), 'after': (lo, hi)}];
    verdict_total: (dlo, dhi) the merged verdict's stated move. -> {line_id: (lo, hi)} after, residual asserted 0."""
    out = dict(index_values)
    seen = set()
    tl = th = Decimal(0)
    for d in deltas:
        i = d["line_id"]
        if i not in index_values:
            raise RuleError(f"delta on absent line {i}")
        if i in seen:
            raise RuleError(f"two deltas on {i}")
        seen.add(i)
        b = tuple(D(x) for x in d["before"])
        if b != tuple(D(x) for x in index_values[i]):
            raise RuleError(f"{i}: before {b} differs from the index {index_values[i]}")
        a = tuple(D(x) for x in d["after"])
        if a[0] is None or a[1] < a[0] or a[0] < 0:
            raise RuleError(f"{i}: after {a} refused")
        tl += a[0] - b[0]
        th += a[1] - b[1]
        out[i] = a
    vl, vh = (D(x) for x in verdict_total)
    if tl != vl or th != vh:
        raise RuleError(f"deltas {tl} .. {th} do not close the verdict {vl} .. {vh}")
    return out


# R-T756-4 ------------------------------------------------------------------------------------------------------
def wire_row(line_id, state, before, after, evidence, sources, free=None):
    """state: LIVE or NEW_FREE (from R-T756-1). before / after: None (blank) or (lo, hi).
    evidence: the after's status (HELD, DRAWING-CONFIRMED, ...; never VERIFIED / RELEASED here)."""
    if evidence in ("VERIFIED", "RELEASED"):
        raise RuleError(f"{line_id}: {evidence} is not given by a research ledger")
    if not sources:
        raise RuleError(f"{line_id}: a wiring row names its source records")
    if state == "NEW_FREE":
        if free is False:
            raise RuleError(f"{line_id}: ADD on an id that is not free")
        action = "ADD"
        if before is not None:
            raise RuleError(f"{line_id}: an added line has no before")
    elif state == "LIVE":
        nb = None if before is None else tuple(D(x) for x in before)
        na = None if after is None else tuple(D(x) for x in after)
        action = "KEEP" if nb == na else "CHANGE"
    else:
        raise RuleError(f"{line_id}: {state} is not wireable")
    fmt = (lambda v: "" if v is None else f"{s6(v[0])} .. {s6(v[1])}")
    return {"line_id": line_id, "action": action, "before": fmt(before), "after": fmt(after),
            "after_state": "BLANK" if after is None else ("POINT" if D(after[0]) == D(after[1]) else "BOUNDED"),
            "evidence": evidence, "sources": sources}
