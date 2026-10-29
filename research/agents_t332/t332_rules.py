"""T-332 formwork face -> concrete line binding on a newer candidate (research scope, any villa; stdlib only).

Provenance: T-332 (lane S) on the merged formwork r5 rows (T-308 MERGED efb38618), which are formwork r3 (T-163) + r4
(T-264) + the T-293 face-to-line parts + the r5 rules. Unwired: nothing in engine/ imports it.

Physical element (ERS s.2.1). A formed face is a concrete surface cast against a form. It bounds ONE member and is
reported beside the candidate line that carries that member's concrete (one element, several geometries). A face cast
against ground, blinding, screed or masonry has no form. Below the natural ground the owner question OQ-10 (formed or
earth-cast sides) is open: the two alternatives travel together, never summed, never chosen.

Rules (each guarded below; a refusal raises BindError):
  R-T332-1 REBIND. A face keeps its line when the newer candidate carries the same line id with the same element id
           (SAME). A line id that is gone is looked up by its element id: exactly one line -> REBOUND (old and new id
           kept); none -> NO_LINE with the reason; two or more -> refused (one face, one line).
  R-T332-2 STATE. A measured face (CALCULATED / ALTERNATIVE with a value) on a line whose concrete carries no
           quantity becomes HELD with held_from = its value (R-FW-P3-1 = R-T308-5); it is never shown as a measured
           element beside a blank line. A HELD face never gains a value from its line's state; only its own
           re-measure can free it. A face on a NOT_APPLICABLE line is refused.
  R-T332-3 RE-MEASURE. A face changed by a merge after the source ledger is re-measured from the drawing: each delta
           names the face, the kind (REPLACE / ADD / REMOVE), before and after, the cause (the merge) and the source
           (sheet, entity handle). A delta without cause or source, a REPLACE / REMOVE of an unknown face and an ADD of
           an existing face id are refused.
  R-T332-4 CONTACT. A face whose contact is EARTH (cast against ground, blinding, screed or masonry) is never FORMED or
           CALCULATED with a value; it is the EARTH_CAST alternative (value 0) or carries no row. A buried face of the
           OQ-10 pair carries both alternatives on the same line.
  R-T332-5 HELD IS BLANK. A HELD face has no value (blank), optionally a range lo <= hi with its cause, or one bound
           only (AT_MOST: a held datum with no low end; AT_LEAST); a HELD face with a value (0 included) is refused; a
           value is never negative except a named deduction row (cover / notch / a piece that leaves for another
           member's line).
  R-T332-6 SCENARIO. A scenario row (S1_NOT_RELEASED) is never tied to a candidate line and never in a total
           (ScenarioLeak).
  R-T332-7 CLOSURE. Totals per (status, alternative, method) after binding = source totals + the named deltas, residual
           0.000000; a face counts once (a face id on two lines is refused).
  R-T332-8 FILL AGGREGATE (rework r2, D-T332-1). A FILL row never prints a number no face carries: a HELD row's m2
           is blank; lo / hi only when every bounded face of the row carries that end (an AT_MOST / AT_LEAST /
           UNBOUNDED face blanks the end it lacks), held_from only over HELD_FROM faces; bound_classes counts the
           faces per class. check_fill_row refuses a written row that breaks this (held printed as 0).
"""

from __future__ import annotations

from collections import defaultdict

STATUSES = {"CALCULATED", "ALTERNATIVE", "HELD", "NOT_APPLICABLE", "INFO", "OWNED_BY_OTHER_LINE", "S1_NOT_RELEASED"}
VALUED = {"CALCULATED", "ALTERNATIVE"}
DEDUCTION_KINDS = {"COVER", "NOTCH", "TEE_COVER"}
EPS = 1e-9


class BindError(ValueError):
    pass


class ScenarioLeak(BindError):
    pass


def _num(v):
    return None if v is None or v == "" else float(v)


def check_face(f):
    """R-T332-4 / -5 / -6 on one face record (dict). Returns the face unchanged."""
    st = f.get("status")
    if st not in STATUSES:
        raise BindError(f"{f.get('face_id')}: unknown status {st!r}")
    if f.get("unit", "m2") != "m2":
        raise BindError(f"{f.get('face_id')}: unit {f.get('unit')!r}, formwork is m2 only")
    m2, lo, hi = _num(f.get("m2")), _num(f.get("lo")), _num(f.get("hi"))
    if st == "HELD":
        if m2 is not None:
            raise BindError(f"{f.get('face_id')}: HELD face carries a value {m2} (held is blank, never 0)")
        if lo is not None and hi is not None and lo > hi + EPS:
            raise BindError(f"{f.get('face_id')}: HELD range reversed {lo} > {hi}")
    if st in VALUED:
        if m2 is None:
            raise BindError(f"{f.get('face_id')}: {st} face without a value")
        named = (str(f.get("item", "")) + " " + str(f.get("basis_note", ""))).lower()
        if m2 < -EPS and f.get("face_kind") not in DEDUCTION_KINDS and not any(
                w in named for w in ("cover", "notch", "leaves", "deduct")):
            raise BindError(f"{f.get('face_id')}: negative face {m2} that is not a named deduction")
    alt = f.get("alternative") or ""
    if f.get("contact") == "EARTH":
        if st == "CALCULATED" or alt == "OQ10_FORMED":
            raise BindError(f"{f.get('face_id')}: an EARTH (ground-cast) face booked as formed")
        if st == "ALTERNATIVE" and alt != "OQ10_EARTH_CAST":
            raise BindError(f"{f.get('face_id')}: an EARTH face outside the EARTH_CAST alternative")
        if st == "ALTERNATIVE" and abs(m2) > EPS:
            raise BindError(f"{f.get('face_id')}: an EARTH_CAST alternative carries no form area ({m2})")
    if st == "S1_NOT_RELEASED" and f.get("line_id"):
        raise ScenarioLeak(f"{f.get('face_id')}: scenario row tied to line {f.get('line_id')}")
    return f


def has_quantity(line):
    return line.get("quantity") is not None


def rebind(faces, new_lines):
    """R-T332-1 / -2. faces: dicts with face_id, line_id (old), element_id (old line's), values. new_lines: dicts
    with line_id, element_id, item_code, state, quantity. Returns new face dicts with tie / new line / state."""
    by_id = {l["line_id"]: l for l in new_lines}
    by_el = defaultdict(list)
    for l in new_lines:
        by_el[l["element_id"]].append(l)
    seen = {}
    out = []
    for f in faces:
        fid = f["face_id"]
        if fid in seen:
            raise BindError(f"{fid}: one face on two lines ({seen[fid]} and {f.get('line_id')})")
        seen[fid] = f.get("line_id")
        g = dict(f)
        check_face(g)
        old = f.get("line_id")
        if not old:
            g.update(tie="NO_LINE", new_line_id="", new_state="", tie_reason=f.get("tie_reason") or "no line in source")
            out.append(g)
            continue
        line = by_id.get(old)
        if line is not None and line["element_id"] == f.get("element_id", line["element_id"]):
            g["tie"] = "SAME"
        else:
            cands = by_el.get(f.get("element_id"), [])
            if len(cands) > 1:
                raise BindError(f"{fid}: element {f.get('element_id')} is carried by {len(cands)} lines")
            if not cands:
                g.update(tie="NO_LINE", new_line_id="", new_state="",
                         tie_reason=f"line {old} (element {f.get('element_id')}) not in the newer candidate")
                out.append(g)
                continue
            line = cands[0]
            g["tie"] = "REBOUND"
        g["new_line_id"] = line["line_id"]
        g["new_state"] = line["state"]
        g["new_item_code"] = line["item_code"]
        if line["state"] == "NOT_APPLICABLE_WITH_EVIDENCE" or line["state"] == "NOT_APPLICABLE":
            raise BindError(f"{fid}: face on a NOT_APPLICABLE line {line['line_id']}")
        if g["status"] in VALUED and not has_quantity(line) and abs(_num(g.get("m2")) or 0.0) > EPS:
            g["held_from"] = _num(g["m2"])
            g["status_before_hold"] = g["status"]
            g["status"] = "HELD"
            g["m2"] = None
            g["rule"] = (g.get("rule") + " + " if g.get("rule") else "") + "R-T332-2"
        out.append(g)
    return out


def apply_deltas(rows, deltas):
    """R-T332-3. rows: bound faces; deltas: dicts face_id, kind, cause, source, and for REPLACE / ADD the new face
    fields. Returns (rows, applied) with a 'before' / 'after' pair per delta."""
    idx = {r["face_id"]: i for i, r in enumerate(rows)}
    rows = [dict(r) for r in rows]
    applied = []
    for d in deltas:
        if not d.get("cause") or not d.get("source"):
            raise BindError(f"delta {d.get('face_id')}: cause and drawing source are required")
        kind = d.get("kind")
        fid = d["face_id"]
        if kind == "ADD":
            if fid in idx:
                raise BindError(f"delta {fid}: ADD of an existing face")
            new = dict(d["face"])
            new["face_id"] = fid
            check_face(new)
            rows.append(new)
            idx[fid] = len(rows) - 1
            applied.append({"face_id": fid, "kind": kind, "before": None, "after": _snap(new), "cause": d["cause"],
                            "source": d["source"]})
        elif kind in ("REPLACE", "REMOVE"):
            if fid not in idx:
                raise BindError(f"delta {fid}: {kind} of an unknown face")
            old = rows[idx[fid]]
            if kind == "REMOVE":
                new = dict(old)
                new["status"] = "REMOVED"
                new["m2"] = None
                new["lo"] = new["hi"] = None
            else:
                new = dict(old)
                new.update(d["face"])
                check_face(new)
            new["delta_cause"] = d["cause"]
            new["delta_source"] = d["source"]
            rows[idx[fid]] = new
            applied.append({"face_id": fid, "kind": kind, "before": _snap(old), "after": _snap(new),
                            "cause": d["cause"], "source": d["source"]})
        else:
            raise BindError(f"delta {fid}: kind {kind!r}")
    return rows, applied


def _snap(f):
    return {k: f.get(k) for k in ("status", "alternative", "method", "m2", "lo", "hi", "held_from",
                                  "new_line_id", "line_id")}


def key(f):
    return f"{f.get('status')}|{f.get('alternative') or ''}|{f.get('method')}"


def totals(rows):
    """Per (status, alternative, method): count, m2, lo, hi, held_from. S1 rows refused in a total."""
    t = defaultdict(lambda: {"faces": 0, "m2": 0.0, "lo": 0.0, "hi": 0.0, "held_from": 0.0})
    for r in rows:
        if r.get("status") == "S1_NOT_RELEASED":
            if r.get("new_line_id") or r.get("tie") in ("SAME", "REBOUND"):
                raise ScenarioLeak(f"{r.get('face_id')}: scenario row tied to a line")
            continue                    # listed beside, never in a total
        if r.get("status") == "REMOVED":
            continue
        k = key(r)
        t[k]["faces"] += 1
        t[k]["m2"] += _num(r.get("m2")) or 0.0
        t[k]["lo"] += _num(r.get("lo")) or 0.0
        t[k]["hi"] += _num(r.get("hi")) or 0.0
        t[k]["held_from"] += _num(r.get("held_from")) or 0.0
    return {k: {kk: (round(vv, 6) if isinstance(vv, float) else vv) for kk, vv in v.items()} for k, v in sorted(t.items())}


def closure(source_rows, bound_rows):
    """R-T332-7: per key, bound = source + delta named per face (the delta of a face is bound - source on that face).
    Returns {key: {source, bound, named, residual}}; every residual must be 0.000000."""
    src = {r["face_id"]: r for r in source_rows}
    out = defaultdict(lambda: {"source_m2": 0.0, "bound_m2": 0.0})
    for r in source_rows:
        if r.get("status") in ("S1_NOT_RELEASED",):
            continue
        out[key(r)]["source_m2"] += _num(r.get("m2")) or 0.0
    for r in bound_rows:
        if r.get("status") in ("REMOVED", "S1_NOT_RELEASED"):
            continue
        out[key(r)]["bound_m2"] += _num(r.get("m2")) or 0.0
    named = defaultdict(float)
    for r in bound_rows:
        s = src.get(r["face_id"])
        before = 0.0 if s is None else (_num(s.get("m2")) or 0.0)
        bkey = None if s is None else key(s)
        after = 0.0 if r.get("status") == "REMOVED" else (_num(r.get("m2")) or 0.0)
        akey = key(r)
        if bkey == akey:
            named[akey] += after - before
        else:
            if bkey is not None:
                named[bkey] -= before
            if r.get("status") != "REMOVED":
                named[akey] += after
    res = {}
    for k in sorted(set(out) | set(named)):
        s, b, n = out[k]["source_m2"], out[k]["bound_m2"], named.get(k, 0.0)
        res[k] = {"source_m2": round(s, 6), "bound_m2": round(b, 6), "named_m2": round(n, 6),
                  "residual_m2": round(b - s - n, 6)}
        if abs(b - s - n) > 1e-6:
            raise BindError(f"closure {k}: residual {b - s - n}")
    return res


BOUND_CLASSES = ("VALUE", "RANGE", "AT_MOST", "AT_LEAST", "HELD_FROM", "UNBOUNDED")


def bound_class(f):
    """R-T332-8: what one face carries. VALUE (m2), RANGE (lo and hi), AT_MOST (hi only), AT_LEAST (lo only),
    HELD_FROM (a measured value held by its line's state, R-T332-2), UNBOUNDED (nothing: blank)."""
    if _num(f.get("m2")) is not None:
        return "VALUE"
    lo, hi = _num(f.get("lo")), _num(f.get("hi"))
    if lo is not None and hi is not None:
        return "RANGE"
    if hi is not None:
        return "AT_MOST"
    if lo is not None:
        return "AT_LEAST"
    if _num(f.get("held_from")) is not None:
        return "HELD_FROM"
    return "UNBOUNDED"


def _aggregate(faces):
    """R-T332-8 FILL AGGREGATE (rework r2 of D-T332-1: missing never becomes 0). One FILL row = the faces of one line
    under one (status, alternative, method) key.
      m2        : the sum when every face carries m2; BLANK (None) when none does (a HELD row is always blank);
                  a key mixing valued and blank faces is refused.
      lo        : the sum of the faces' low ends, printed only when every non-HELD_FROM face carries one (a face with no
                  low end, AT_MOST or UNBOUNDED, makes the row's low end unknown: never read as 0); else BLANK.
      hi        : likewise, printed only when every non-HELD_FROM face carries a high end (an AT_LEAST or UNBOUNDED face
                  makes the row unbounded above: a partial sum would understate it); else BLANK.
      held_from : the sum over the HELD_FROM faces; BLANK when the row has none.
      bound_classes : the count of faces per class, so a partial row is visible without the face ledger."""
    cls = [bound_class(f) for f in faces]
    n = {c: cls.count(c) for c in BOUND_CLASSES if cls.count(c)}
    vals = [_num(f.get("m2")) for f in faces]
    if any(v is None for v in vals) and any(v is not None for v in vals):
        raise BindError("one FILL row mixes valued and blank faces: " + " ".join(str(f.get("face_id")) for f in faces))
    m2 = None if vals and vals[0] is None else round(sum(vals), 6)
    rest = [f for f, c in zip(faces, cls) if c not in ("VALUE", "HELD_FROM")]
    lo = hi = None
    if rest and all(_num(f.get("lo")) is not None for f in rest):
        lo = round(sum(_num(f.get("lo")) for f in rest), 6)
    if rest and all(_num(f.get("hi")) is not None for f in rest):
        hi = round(sum(_num(f.get("hi")) for f in rest), 6)
    hf = [_num(f.get("held_from")) for f, c in zip(faces, cls) if c == "HELD_FROM"]
    held_from = round(sum(hf), 6) if hf else None
    return {"faces": len(faces), "m2": m2, "lo": lo, "hi": hi, "held_from": held_from,
            "bound_classes": "; ".join(f"{c} {k}" for c, k in n.items())}


def check_fill_row(row, faces):
    """R-T332-8 guard on one written FILL row (the writer calls it before printing): a HELD / NOT_APPLICABLE row with a
    number in m2, a number in lo / hi / held_from that no face of the row carries, or a numeric bound while a face of
    the row has no such bound, is refused (a consumer wiring the table unchanged must never read a held face as 0)."""
    lid = row.get("line_id")
    if row.get("status") in ("HELD", "NOT_APPLICABLE") and _num(row.get("m2")) is not None:
        raise BindError(f"FILL {lid}: {row.get('status')} row prints m2 {row.get('m2')} (held is blank, never 0)")
    cls = [bound_class(f) for f in faces]
    rest = [f for f, c in zip(faces, cls) if c not in ("VALUE", "HELD_FROM")]
    for kk in ("lo", "hi"):
        if _num(row.get(kk)) is not None and (not rest or any(_num(f.get(kk)) is None for f in rest)):
            raise BindError(f"FILL {lid}: {kk} {row.get(kk)} printed while a face of the row carries no {kk}")
    if _num(row.get("held_from")) is not None and "HELD_FROM" not in cls:
        raise BindError(f"FILL {lid}: held_from {row.get('held_from')} printed while no face carries one")
    if _num(row.get("m2")) is not None and any(_num(f.get("m2")) is None for f in faces):
        raise BindError(f"FILL {lid}: m2 {row.get('m2')} printed while a face of the row is blank")
    return row


def fill_table(rows):
    """Per new line id: face ids and totals per key (R-T332-8 aggregate). Only tied (SAME / REBOUND) rows; REMOVED
    excluded."""
    t = {}
    grp = defaultdict(list)
    for r in rows:
        if r.get("tie") not in ("SAME", "REBOUND") or r.get("status") in ("REMOVED",):
            continue
        lid = r["new_line_id"]
        e = t.setdefault(lid, {"line_id": lid, "item_code": r.get("new_item_code", ""), "line_state": r.get("new_state", ""),
                               "faces": [], "totals": {}})
        e["faces"].append(r["face_id"])
        grp[(lid, key(r))].append(r)
    for (lid, k), fs in grp.items():
        t[lid]["totals"][k] = _aggregate(fs)
    for e in t.values():
        e["faces"].sort()
        e["totals"] = dict(sorted(e["totals"].items()))
    return dict(sorted(t.items()))
