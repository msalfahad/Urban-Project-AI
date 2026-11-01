"""T-433 rules: split a reconciliation roll-up's HELD figure by the item that holds it (every villa).

R-T433-1  SPLIT EXACT. The blocker items re-add to the roll-up HELD figure within 0.000002 m3; a split that does not
          re-add is refused (never closed into a 'rest' item).
R-T433-2  ONE ITEM PER PART. Every HELD part (component part of the roll-up, by its id) goes to exactly one blocker item;
          a part in two items or in none is refused. A part held by several facts at once, whose comparison term is not
          separable (one lump on the other side), goes to ONE JOINT item that names every fact; it is never split by a
          ratio, a share or a guess.
R-T433-3  ONE ITEM PER LINE. An engine line id appears in at most one blocker item; a held engine line with no comparison
          term (no part of the HELD figure) is listed BESIDE, with its blocker, never inside an item and never as 0.
R-T433-4  HELD NEVER 0. An item of 0 m3 or a positive HELD item (HELD is engine 0 against the other side) is refused.
R-T433-5  SETTLEMENT TEST WRITTEN OUT (ERS s.2.7). Every item states the drawings searched (sheet / page) and one route:
          DRAWING (a drawing in the set settles it: the drawing is named) -> an investigation task; ENGINE (the evidence
          is already settled by a merged verdict, the engine has not taken it) -> an investigation / lane I task;
          DESIGNER or SUPPLIER (no drawing in the set settles it: ERS s.2.7 'drawings and approved rules cannot resolve
          it') -> the RFI list, with the RFI id when one exists, else RFI_MISSING. An item with no drawing searched,
          or a DRAWING route without a named drawing, is refused.
R-T433-6  NO VALUE. A blocker split never values a held line: engine ranges are printed beside, never chosen.
R-T433-7  RANKING. Investigation list (DRAWING + ENGINE) and RFI list (DESIGNER + SUPPLIER) are each ranked by |m3|
          descending, ties by item id; an RFI id shared by several items is ranked by the sum of its items.
"""

from __future__ import annotations

TOL = 2e-6
ROUTES = ("DRAWING", "ENGINE", "DESIGNER", "SUPPLIER")


class SplitError(ValueError):
    pass


def check_items(items, parts, held_total, beside=()):
    """items: [{id, m3, parts:[part ids], lines:[line ids], blockers:[...], route, drawings_searched:[...],
    settle_drawing?, rfi?}]; parts: {part id: m3} (every HELD part of the roll-up); held_total: the roll-up HELD m3.
    beside: [{line_id, blocker}] held lines with no comparison term."""
    seen_part, seen_line = {}, {}
    for it in items:
        if not it.get("parts"):
            raise SplitError(f"{it['id']}: no part")
        m = round(sum(parts[p] if p in parts else _missing(it, p) for p in it["parts"]), 6)
        if abs(m - it["m3"]) > TOL:
            raise SplitError(f"{it['id']}: parts re-add to {m}, item says {it['m3']}")
        if it["m3"] >= 0 or abs(it["m3"]) < TOL:
            raise SplitError(f"{it['id']}: HELD item must be negative and non-zero (R-T433-4)")
        for p in it["parts"]:
            if p in seen_part:
                raise SplitError(f"part {p} in {seen_part[p]} and {it['id']} (R-T433-2)")
            seen_part[p] = it["id"]
        for ln in it.get("lines", []):
            if ln in seen_line:
                raise SplitError(f"line {ln} in {seen_line[ln]} and {it['id']} (R-T433-3)")
            seen_line[ln] = it["id"]
        if it.get("route") not in ROUTES:
            raise SplitError(f"{it['id']}: route {it.get('route')} unknown")
        if not it.get("drawings_searched"):
            raise SplitError(f"{it['id']}: no drawing searched (R-T433-5)")
        if it["route"] == "DRAWING" and not it.get("settle_drawing"):
            raise SplitError(f"{it['id']}: DRAWING route without the drawing that settles it")
        if it["route"] in ("DESIGNER", "SUPPLIER") and not it.get("rfi"):
            raise SplitError(f"{it['id']}: designer route without an RFI id or RFI_MISSING")
        if len(it.get("blockers", [])) > 1 and not it.get("joint"):
            raise SplitError(f"{it['id']}: several blockers on one item must be a JOINT item (R-T433-2)")
        if "value" in it or "chosen" in it:
            raise SplitError(f"{it['id']}: a blocker item never values a held line (R-T433-6)")
    left = sorted(set(parts) - set(seen_part))
    if left:
        raise SplitError(f"parts in no item: {left} (R-T433-2)")
    for b in beside:
        if b["line_id"] in seen_line:
            raise SplitError(f"beside line {b['line_id']} also in {seen_line[b['line_id']]} (R-T433-3)")
        if not b.get("blocker"):
            raise SplitError(f"beside line {b['line_id']} has no blocker")
    tot = round(sum(it["m3"] for it in items), 6)
    if abs(tot - held_total) > TOL:
        raise SplitError(f"items re-add to {tot}, roll-up HELD is {held_total} (R-T433-1)")
    return tot


def _missing(it, p):
    raise SplitError(f"{it['id']}: part {p} is not a HELD part of the roll-up")


def ranked(items):
    inv = sorted((i for i in items if i["route"] in ("DRAWING", "ENGINE")), key=lambda i: (i["m3"], i["id"]))
    rfi = sorted((i for i in items if i["route"] in ("DESIGNER", "SUPPLIER")), key=lambda i: (i["m3"], i["id"]))
    by_rfi = {}
    for i in rfi:
        for r in i["rfi"]:
            # an item answered only by several RFIs together counts in full under each (it unlocks only when all are
            # answered); the per-RFI sums are therefore a ranking aid, never re-added to a total
            by_rfi[r] = round(by_rfi.get(r, 0.0) + i["m3"], 6)
    rfi_rank = sorted(by_rfi.items(), key=lambda kv: (kv[1], kv[0]))
    return inv, rfi, rfi_rank
