"""R-T333-1: the BLOCKWORK FILL TABLE on the candidate of record (research rule, any villa; T-333). Pure Python, no
drawing access, no engine import.

Provenance: R-T291-1 (T-291 MERGED 0c6b2ba5: wall-to-line ledger on V3.0.15), register v4 (T-288 MERGED 643b310b),
R-T311-1 .. 4 (T-311 MERGED bd7b8c23: parapet / plinth components, one owner trade each), WORKFLOW_CONTROLS s.5
(evidence statuses; HELD never 0) and ENGINEERING_REASONING_STANDARD s.2.4 / s.3 (reconcile to named causes; build
before deduct; one physical element counted once). Nothing here edits an engine module, a rule or knowledge file, a
candidate line or a released line: lane I (T-279) applies the fill table.

PHYSICAL ELEMENT. A block wall is the masonry between its two faces, from the structural floor to the underside of the
member over it, less the openings built into it. The candidate measures masonry as one line per storey x thickness
family x item (no wall key); line ids change with the candidate version. The fill table states, on the CURRENT
candidate's line ids, which wall goes into which line, at which status and how much, so the integration only wires.

Rules (each refusal code is the first word of the error):
1. REBIND. A ledger line of an earlier candidate maps to the current candidate's line with the same (item code, storey,
   thickness family, unit). Exactly one current line per key (KEY_AMBIGUOUS otherwise); an earlier key with no current
   line is refused (LINE_LOST); a current masonry line with no earlier key is LISTED (LINE_NEW), never filled by
   guess. The current line's state is carried: a blank line (no quantity) is REPLACED, a line with a figure is
   CORRECTED (the before figure is stated); a state the rule does not know is refused (STATE_UNKNOWN).
2. ONCE. Every wall appears once per item code over all lines (its declared shares sum to 1); a wall under two ids for
   one item, or one id twice, is refused (WALL_TWO_IDS). A volume row equals its area row x the wall thickness to
   0.000001 m3 (VOLUME_MISMATCH).
3. HELD. A HELD wall or piece keeps a blank quantity and its named item; a 0 or a figure is refused (HELD_AS_ZERO);
   a drop term is carried as U - L x d and never evaluated (DROP_EVALUATED).
4. COMPONENTS. A component that another element already contains (a wall course inside a wall's height) is bound to
   the containing line with state CONTAINED and adds nothing; adding it again is refused (CONTAINED_ADDED). An
   alternative component (a parapet's part above its RC upstand: RC OR block, material HELD) is bound to NO masonry line
   while its material is HELD, carried by name with its range OUTSIDE every total, and is exclusive with the concrete
   alternative of the same run: a run carried as block AND as RC above the upstand is refused (PARAPET_BOTH); a
   held alternative written as 0 is refused (HELD_AS_ZERO).
5. TOTALS. Per line and per block type (m2 and m3 apart): before (the line's own figure or BLANK) and after (the
   determinate sum + the established parts + the drop term U - L x d + the HELD walls by name). HELD and the drop term
   are never folded into a figure; m2 and m3 are never added.
6. FALLBACK VISIBLE (r2, D-T333-1). A wall's net is built gross minus its DEDUCTED openings, so the net's evidence is
   no stronger than the weakest deduction in it. When any DEDUCTED opening of a wall (or of the established part of a
   wall) rests on an owner-approved fallback height (Q-55: no printed door height, 2.20 m), the label of that net is
   ASSUMED — OWNER-APPROVED, for an established part exactly as for a whole wall (WORKFLOW_CONTROLS s.4 / s.5: the
   fallback stays visible even after an independent check). Window-only and opening-free nets keep their own label.
   A determinate status or a part_status VERIFIED / DRAWING-CONFIRMED over a fallback deduction is refused
   (FALLBACK_HIDDEN); a DEDUCTED opening whose height basis is not established is refused (STATE_UNKNOWN). The
   quantity never changes: only its label.
"""
from __future__ import annotations

RULE_ID = "R-T333-1"
TOL = 0.0000005

KNOWN_STATES = ("BLOCKED_RFI", "BLOCKED", "HELD", "PROVISIONAL", "MEASURED", "SOURCE_DERIVED", "BOUNDED",
                "DRAWING_CONFIRMED", "VERIFIED")
AREA, VOLUME = "m2", "m3"
DETERMINATE = ("VERIFIED", "DRAWING-CONFIRMED", "ASSUMED — OWNER-APPROVED")
HELD_ON_DROP, HELD, PART_PLUS_HELD = "HELD ON DROP", "HELD", "ESTABLISHED PART + HELD"


class FillError(ValueError):
    """a binding, row or component the rule refuses (the code is the first word of the message)."""


def line_key(ln):
    return (ln["item_code"], ln["floor"], ln.get("family"), ln["unit"])


def rebind(old_lines, new_lines):
    """rule 1 -> ({old_id: new_line}, new_unbound [line ids], actions {new_id: 'REPLACE_BLANK' | 'CORRECT_FIGURE'})."""
    by_key = {}
    for ln in new_lines:
        by_key.setdefault(line_key(ln), []).append(ln)
    out, actions = {}, {}
    for ln in old_lines:
        c = by_key.get(line_key(ln), [])
        if not c:
            raise FillError(f"LINE_LOST: {ln['line_id']} {line_key(ln)} has no line in the current candidate")
        if len(c) > 1:
            raise FillError(f"KEY_AMBIGUOUS: {line_key(ln)} -> {[x['line_id'] for x in c]}")
        new = c[0]
        st = new.get("evidence_state")
        if st not in KNOWN_STATES:
            raise FillError(f"STATE_UNKNOWN: {new['line_id']} {st!r}")
        out[ln["line_id"]] = new
        actions[new["line_id"]] = "REPLACE_BLANK" if new.get("measured_net") is None else "CORRECT_FIGURE"
    used = {v["line_id"] for v in out.values()}
    unbound = sorted(ln["line_id"] for ln in new_lines if ln["line_id"] not in used)
    return out, unbound, actions


def check_rows(rows, thickness):
    """rules 2 / 3 over fill rows [{line_id, item_code, unit, wall_id, share, status, carried, upper,
    drop_coefficient, held_item}] ; thickness {wall_id: t_m}."""
    seen = {}
    for r in rows:
        k = (r["wall_id"], r["item_code"])
        ids = seen.setdefault(k, [])
        if r["line_id"] in ids:
            raise FillError(f"WALL_TWO_IDS: {r['wall_id']} twice in {r['line_id']} ({r['item_code']})")
        ids.append(r["line_id"])
        st, q = r["status"], r.get("carried")
        if st == HELD:
            if q is not None:
                raise FillError(f"HELD_AS_ZERO: {r['wall_id']} HELD carries {q!r}; blank with its named item")
            if not r.get("held_item"):
                raise FillError(f"HELD_AS_ZERO: {r['wall_id']} HELD without its named item")
        elif st == HELD_ON_DROP:
            if q is not None:
                raise FillError(f"DROP_EVALUATED: {r['wall_id']} carries {q!r}; U - L x d only")
            if not r.get("upper") or not r.get("drop_coefficient"):
                raise FillError(f"HELD_AS_ZERO: {r['wall_id']} drop wall without U and L")
        elif st in DETERMINATE or st == PART_PLUS_HELD:
            if q is None or q <= 0:
                raise FillError(f"HELD_AS_ZERO: {r['wall_id']} {st} carries {q!r}")
        else:
            raise FillError(f"STATE_UNKNOWN: {r['wall_id']} status {st!r}")
    shares = {}
    for r in rows:
        shares[(r["wall_id"], r["item_code"])] = shares.get((r["wall_id"], r["item_code"]), 0.0) + r["share"]
    for k, s in shares.items():
        if abs(s - 1.0) > 1e-9:
            raise FillError(f"WALL_TWO_IDS: {k[0]} carried {s:g} times in {k[1]}")
    # volume = area x t, wall by wall (both area items carry the same m2; compare against MAS.BLOCK when present)
    by_wall_area = {}
    for r in rows:
        if r["unit"] == AREA:
            by_wall_area.setdefault(r["wall_id"], r)
    for r in rows:
        if r["unit"] != VOLUME:
            continue
        a = by_wall_area.get(r["wall_id"])
        if a is None:
            continue
        t = thickness[r["wall_id"]]
        for fld in ("carried", "upper", "drop_coefficient"):
            va, vv = a.get(fld), r.get(fld)
            if (va is None) != (vv is None):
                raise FillError(f"VOLUME_MISMATCH: {r['wall_id']} {fld} area {va!r} vs volume {vv!r}")
            if va is not None and abs(va * t - vv) > 1e-6:
                raise FillError(f"VOLUME_MISMATCH: {r['wall_id']} {fld} {va} x {t} != {vv}")
    return True


def check_components(components):
    """rule 4 over [{component_id, run_or_zone, kind: CONTAINED | ALTERNATIVE_BLOCK | ALTERNATIVE_RC,
    line_id or None, low, high, material_status, added (bool)}]"""
    by_run = {}
    for c in components:
        if c["kind"] == "CONTAINED":
            if c.get("added"):
                raise FillError(f"CONTAINED_ADDED: {c['component_id']} is inside {c.get('line_id')}; never added again")
            if not c.get("line_id") and not c.get("held_item"):
                raise FillError(f"HELD_AS_ZERO: {c['component_id']} contained in no line and not held")
        elif c["kind"] in ("ALTERNATIVE_BLOCK", "ALTERNATIVE_RC"):
            by_run.setdefault(c["run_or_zone"], []).append(c)
            if c["kind"] == "ALTERNATIVE_BLOCK":
                if c.get("material_status", "").startswith("HELD"):
                    if c.get("line_id"):
                        raise FillError(f"PARAPET_BOTH: {c['component_id']} material HELD but bound to {c['line_id']}")
                    if c.get("low") is None or c.get("high") is None or c["high"] <= 0:
                        raise FillError(f"HELD_AS_ZERO: {c['component_id']} held alternative needs its range")
                    if c.get("added"):
                        raise FillError(f"HELD_AS_ZERO: {c['component_id']} held alternative added to a total")
        else:
            raise FillError(f"STATE_UNKNOWN: {c['component_id']} kind {c['kind']!r}")
    for run, cs in by_run.items():
        blk = [c for c in cs if c["kind"] == "ALTERNATIVE_BLOCK" and (c.get("line_id") or c.get("added"))]
        rc = [c for c in cs if c["kind"] == "ALTERNATIVE_RC" and c.get("above_upstand_carried")]
        if blk and rc:
            raise FillError(f"PARAPET_BOTH: run {run} carried as block and as RC above the upstand")
    return True


OWNER_APPROVED = "ASSUMED — OWNER-APPROVED"
HEIGHT_BASES = ("VERIFIED", "DRAWING-CONFIRMED", OWNER_APPROVED)


def _fallback_ops(wall_id, deducted):
    ops = deducted.get(wall_id, [])
    for o in ops:
        if o.get("height_basis") not in HEIGHT_BASES:
            raise FillError(f"STATE_UNKNOWN: opening {o.get('opening_id')} on {wall_id} is DEDUCTED with height basis "
                            f"{o.get('height_basis')!r}")
    return [o for o in ops if o["height_basis"] == OWNER_APPROVED]


def apply_fallback_labels(rows, deducted):
    """rule 6 -> rows with part_status lifted to ASSUMED — OWNER-APPROVED where a DEDUCTED opening of the wall rests
    on an owner-approved fallback height. deducted: {wall_id: [{opening_id, height_basis}]} (DEDUCTED openings only,
    i.e. those inside the carried net, the established part or the U of a drop wall). Quantities untouched."""
    out = []
    for r in rows:
        r = dict(r)
        if _fallback_ops(r["wall_id"], deducted) and r.get("part_status") is not None:
            r["part_status"] = OWNER_APPROVED
        out.append(r)
    check_fallback_labels(out, deducted)
    return out


def check_fallback_labels(rows, deducted):
    """rule 6: refuse a VERIFIED / DRAWING-CONFIRMED label over a fallback deduction (status or part_status)."""
    for r in rows:
        fb = _fallback_ops(r["wall_id"], deducted)
        if not fb:
            continue
        for fld in ("status", "part_status"):
            if r.get(fld) in ("VERIFIED", "DRAWING-CONFIRMED"):
                raise FillError(f"FALLBACK_HIDDEN: {r['wall_id']} {fld} {r[fld]} but its net deducts "
                                f"{', '.join(o['opening_id'] for o in fb)} at an owner-approved fallback height")
    return True


def line_totals(rows, unit):
    """rule 5 for the rows of one line (or one type): determinate, parts, drop U / coefficient, held names."""
    det = sum(r["carried"] for r in rows if r["status"] in DETERMINATE)
    part = sum(r["carried"] for r in rows if r["status"] == PART_PLUS_HELD)
    up = sum(r["upper"] for r in rows if r["status"] == HELD_ON_DROP)
    co = sum(r["drop_coefficient"] for r in rows if r["status"] == HELD_ON_DROP)
    held = sorted(r["wall_id"] for r in rows if r["status"] in (HELD, PART_PLUS_HELD))
    by = {s: sum(r["carried"] for r in rows if r["status"] == s) for s in DETERMINATE}
    nd = 6 if unit == VOLUME else 4
    expr = f"{det:.{nd}f} determinate"
    if part:
        expr += f" + {part:.{nd}f} established parts"
    if co:
        expr += f" + ({up:.{nd}f} - {co:.{nd}f} x d) drop walls"
    if held:
        expr += f" + HELD [{len(held)} walls / pieces, blank]"
    return {"determinate": round(det, 6), "verified": round(by["VERIFIED"], 6),
            "drawing_confirmed": round(by["DRAWING-CONFIRMED"], 6),
            "owner_approved": round(by["ASSUMED — OWNER-APPROVED"], 6), "established_parts": round(part, 6),
            "drop_upper_at_d0": round(up, 6), "drop_coefficient": round(co, 6), "held": held,
            "expression": expr + f" {unit}"}
