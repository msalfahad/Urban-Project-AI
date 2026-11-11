"""T-697 rules: CORNER BEAD LEDGER BOUND TO THE CANDIDATE (BOQ family B4-09, unit m.l), any villa.

Research module (unwired). Pure functions, no I/O. It restates a merged arris ledger (T-405 R-T405-1 .. 8, which
decides WHICH edges are arrises) on the current candidate: every arris bound to exactly one host line of the candidate
index, the exposed height of every vertical arris, the register exclusions, and HELD rows that are never 0.

Physical element (ERS s.2.1): a galvanised steel angle bead fixed on a CONVEX arris of a plastered surface before the
coats. Its length is the EXPOSED length of that arris where BOTH sides are plastered.

Owner basis (searched first):
  OD-V3B-8 STEEL_PLASTER_ANGLE_BEADS (owner 2026-10-04): beads 'at EXPOSED plaster edges' (door / opening jambs, window
      edges, external plastered corners); never on a hidden or non-plastered edge.
  Heights (owner 2026-11-02, Q-72): plaster to the structural soffit, PAINT TO THE FINISHED CEILING (G1 3.65 GF,
      3.35 1F / 2F, Q-43 / Q-48 A); stair shafts at full exposed height.
  ELEMENT_REGISTER corner-bead ruling (Lead 2026-11-11 04:20): plaster owns B4-09; an entrance / lift surround (B6-06),
      a tiled arris (tile family) and a marble / stone jamb lining own their own arrises; HELD where the face is HELD.

Rules (proposed; scope every villa; provenance T-697):
  R-T697-1 EXPOSED HEIGHT. A vertical arris takes a bead from the floor finish to the lowest thing that hides or ends it:
           the finished (decor) ceiling, or a structural element passing over the arris (landing, flight, beam) when that
           is lower. The band of plaster between the finished ceiling and the structural soffit is plaster (Q-72) but its
           arris is hidden: no bead (OD-V3B-8). Owner method: G1. Drawing-derived method: G1 .. structural soffit (the
           ceiling type is printed on no plan, O-P8-02), shown beside it, never mixed.
  R-T697-2 OVERHEAD ELEMENT. When an overhead element (drawn HIDDEN on the plan) passes over the arris and its soffit is
           below G1, the arris stops at that soffit: HELD low .. high from the element's own levels; G1 is refused there.
  R-T697-3 ONE HOST. Every counted arris names exactly one host line that is present in the candidate index with a
           plaster / render code; two candidate hosts is a named BINDING_OPEN item (length kept, never dropped); a host
           absent from the index is refused.
  R-T697-4 OWNER-TRADE EXCLUSIONS. An arris owned by a surround (B6-06), tile (B4-10) or a marble / stone jamb lining is
           NOT_APPLICABLE to B4-09 with the owning line named; it is never counted in B4-09 and never deleted.
  R-T697-5 HELD NEVER 0. A HELD row carries low .. high or a blank with its cause; a HELD row with a 0 value, or a
           measured row with no length, is refused.
  R-T697-6 SHAFT ARRIS. A column / pier arris inside a stair shaft that runs through the storeys is measured by storey
           band on the shaft's net face (R-T680-2 pier returns: exposed length = return area / return depth), to the
           finished ceiling under the roof (Q-48 A), never at a room G1.
"""

from decimal import Decimal, ROUND_HALF_UP

PLASTER_HOST_CODES = ("FIN.PLASTER", "FIN.EXT.FINISH", "ARCH.FACADE")
OWNER_TRADE_CODES = {"B6-06": "FIN.MARBLE.LIFT_SURROUND", "B4-10": "FIN.WALL.TILE"}
STATUSES = ("ASSUMED — OWNER-APPROVED", "DRAWING-CONFIRMED", "HELD", "NOT_APPLICABLE", "NOT A BEAD")


class BeadRuleError(ValueError):
    """A ledger row that breaks R-T697-1 .. 6."""


def q4(x):
    return float(Decimal(str(x)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP))


def exposed_vertical(g1, soffit, overhead=None):
    """R-T697-1 / -2. Return (owner_m or None, low, high, rule) for ONE vertical arris.

    g1: finished-ceiling height above the floor finish (owner); soffit: structural soffit height above the same floor;
    overhead: None or (low, high) soffit height of an element drawn over the arris."""
    if g1 is None or soffit is None or g1 <= 0 or soffit <= 0:
        raise BeadRuleError("height missing: an arris height is never borrowed or 0 (HELD by name)")
    if soffit < g1:
        raise BeadRuleError("finished ceiling above the structural soffit: impossible geometry, refused")
    if overhead is not None:
        lo, hi = overhead
        if lo is None or hi is None or lo <= 0 or hi < lo:
            raise BeadRuleError("overhead soffit bound missing or not positive")
        if hi < g1:
            return None, q4(lo), q4(hi), "R-T697-2"
    return q4(g1), q4(g1), q4(soffit), "R-T697-1"


def opening_ring(width, head, plastered_sides, flush_sides=0):
    """2 jambs x head + head width on EACH plastered side with a reveal; a flush-frame side has no arris (R-T405-6)."""
    if width is None or head is None or width <= 0 or head <= 0:
        raise BeadRuleError("opening width / head missing: HELD, never 0")
    if plastered_sides < 0 or flush_sides < 0 or flush_sides > plastered_sides:
        raise BeadRuleError("side count invalid")
    return q4((2 * head + width) * (plastered_sides - flush_sides))


def shaft_band_arrises(return_area_lo, return_area_hi, depth):
    """R-T697-6: summed exposed length of the pier-return arrises in one storey band (one arris per return)."""
    if depth is None or depth <= 0 or return_area_lo is None or return_area_hi is None:
        raise BeadRuleError("pier-return depth or area missing (HELD, never 0)")
    return q4(return_area_lo / depth), q4(return_area_hi / depth)


def exclusion(owner_trade, owning_line_id):
    """R-T697-4: a NOT_APPLICABLE row names the trade and the candidate line that owns the arris."""
    if owner_trade not in ("B6-06", "B4-10", "MARBLE_JAMB"):
        raise BeadRuleError("unknown owner trade for an excluded arris: " + str(owner_trade))
    if not owning_line_id and owner_trade != "MARBLE_JAMB":
        raise BeadRuleError("an excluded arris names the line that owns it")
    return {"status": "NOT_APPLICABLE", "owner_trade": owner_trade, "owning_line": owning_line_id}


def bind(host_ids, index):
    """R-T697-3. host_ids: list of candidate line ids. Returns (binding_state, host or '')."""
    ids = [h for h in host_ids if h]
    if not ids:
        return "NO_HOST", ""
    for h in ids:
        line = index.get(h)
        if line is None:
            raise BeadRuleError("host line absent from the candidate index: " + h)
        if line["item_code"] not in PLASTER_HOST_CODES + tuple(OWNER_TRADE_CODES.values()):
            raise BeadRuleError("host line is not a plaster / render / owning line: %s %s" % (h, line["item_code"]))
    if len(ids) == 1:
        return "BOUND", ids[0]
    return "BINDING_OPEN", " | ".join(ids)


def check_row(r):
    """R-T697-5 plus the one-host rule for counted rows."""
    st = r["status"]
    if st not in STATUSES:
        raise BeadRuleError("unknown status " + st)
    if st in ("ASSUMED — OWNER-APPROVED", "DRAWING-CONFIRMED"):
        if r.get("owner_m") in (None, "") or float(r["owner_m"]) <= 0:
            raise BeadRuleError("measured row without a length: " + r["edge_id"])
        if r.get("binding") not in ("BOUND", "BINDING_OPEN"):
            raise BeadRuleError("counted arris without a host line: " + r["edge_id"])
    if st == "HELD":
        if r.get("owner_m") not in (None, ""):
            raise BeadRuleError("HELD row carries a value (it is a bound or a blank): " + r["edge_id"])
        for k in ("held_low", "held_high"):
            if r.get(k) not in (None, "") and float(r[k]) == 0 and k == "held_high":
                raise BeadRuleError("HELD row bounded at 0: " + r["edge_id"])
        if not r.get("cause"):
            raise BeadRuleError("HELD row without its cause: " + r["edge_id"])
    if st == "NOT_APPLICABLE" and not r.get("owner_trade"):
        raise BeadRuleError("NOT_APPLICABLE row without its owning trade")
    return True


def check_ledger(rows):
    seen = set()
    for r in rows:
        if r["edge_id"] in seen:
            raise BeadRuleError("one arris once: duplicate " + r["edge_id"])
        seen.add(r["edge_id"])
        check_row(r)
    return True


def totals(rows):
    """Owner-method m.l by status, drawing-derived low .. high, HELD bounded low .. high, counts by status."""
    out = {"owner_measured_m": 0.0, "by_status_m": {}, "drawing_low_m": 0.0, "drawing_high_m": 0.0,
           "held_bounded_low_m": 0.0, "held_bounded_high_m": 0.0, "held_bounded_rows": 0, "held_blank_rows": 0,
           "rows_by_status": {}}
    for r in rows:
        st = r["status"]
        out["rows_by_status"][st] = out["rows_by_status"].get(st, 0) + 1
        if st in ("ASSUMED — OWNER-APPROVED", "DRAWING-CONFIRMED"):
            v = float(r["owner_m"])
            out["owner_measured_m"] += v
            out["by_status_m"][st] = out["by_status_m"].get(st, 0.0) + v
            out["drawing_low_m"] += float(r.get("dwg_low") or v)
            out["drawing_high_m"] += float(r.get("dwg_high") or v)
        elif st == "HELD":
            if r.get("held_low") not in (None, "") and r.get("held_high") not in (None, ""):
                out["held_bounded_low_m"] += float(r["held_low"])
                out["held_bounded_high_m"] += float(r["held_high"])
                out["held_bounded_rows"] += 1
            else:
                out["held_blank_rows"] += 1
    for k in ("owner_measured_m", "drawing_low_m", "drawing_high_m", "held_bounded_low_m", "held_bounded_high_m"):
        out[k] = q4(out[k])
    out["by_status_m"] = {k: q4(v) for k, v in sorted(out["by_status_m"].items())}
    return out
