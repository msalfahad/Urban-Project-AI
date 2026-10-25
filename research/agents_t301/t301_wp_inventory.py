"""T-301: the WATERPROOFING SCOPE INVENTORY per WP family, element by element and face by face, and its join to the
candidate's waterproofing lines (owner 2026-10-25 11:51 (0); Verifier 11:28 F-REC-02: no waterproofing inventory, so no
WP line can be counted WHOLE). A pure CHECK: it reads plain data, writes nothing, moves no quantity, is wired into no
method; nothing here names a project, a sheet, a layer or a coordinate (the project adapter is t301_alsenan.py).

The physical question (ERS 2026-10-22 s.2.1): which faces does each WP family cover? An inventory element is ONE face of
ONE drawn element for ONE item code and unit (the membrane under a footing and its protection screed are two items on the
same face; the screed m2 and m3 are two rows), read from the drawn elements, never from the engine's lines. Each element
is either
  IN_LINE         one candidate line of the same item code and unit carries it (line id, the line's state); a line in a
                  quantity state is the element's quantity, a held line holds it BLANK with its reason;
  NOT_APPLICABLE  no WP item of this kind is built on that face, with EVIDENCE (the sheet / detail / handle that shows
                  why: a face above the natural ground, a soffit cast on blinding, a face another WP item owns); an NA
                  without evidence is refused;
  MISSING         applicable and in no line: an omission, reported with a BLANK quantity, never a zero.
Refused (InventoryError): a face carried by two lines of the same item code and unit (a double count); a NOT_APPLICABLE
element without evidence or that a line carries; an applicable element whose inventory quantity is 0 (a missing or held
quantity is None, never 0); a MISSING element reported with a quantity; a line key that names no inventory element is
listed REGISTER_ONLY (an inventory gap or a misread, never silently counted).

Per family / item / unit: the inventory quantity of the IN_LINE elements carried by quantity lines vs those lines'
measured net; the residual is reported in the unit (never absorbed). to_t236() gives the same inventory in the merged
T-236 inventory schema (engine/source/trade_completeness_v1.check: inventories / line_links / exclusions), so the T-236 /
T-298 completeness join can count a whole WP line.
"""

from __future__ import annotations

from collections import defaultdict

SCHEMA = "URBAN_WP_SCOPE_INVENTORY_V1"
RULE_ID = "R-T301-WP-INVENTORY-1"
FAMILIES = ("WP.FOUNDATION", "WP.WET_AREA", "WP.ROOF", "WP.POOL_TANK")
APPLICABILITY = ("APPLICABLE", "NOT_APPLICABLE")
QUANTITY_STATES = ("MEASURED", "SOURCE_DERIVED", "PROVISIONAL")
HELD_STATES = ("BOUNDED_EXPOSURE", "BLOCKED_RFI")
TRADE = "WATERPROOFING"            # engine/source/trade_completeness_v1.line_trade of every WP item (trade WATERPROOFING)
TOL = 1e-6


class InventoryError(ValueError):
    """an inventory or a join the check refuses."""


def element_key(e):
    """one key per item code, unit, element and face: '<item>[<unit>]/<element>/<face>'."""
    return f"{e['item_code']}[{e['unit']}]/{e['element']}/{e['face']}"


def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def validate_inventory(elements):
    """the inventory as given, or InventoryError. -> {key: element}"""
    out = {}
    for e in elements:
        for f in ("family", "item_code", "unit", "element", "face", "floor", "applicability", "source"):
            if not e.get(f):
                raise InventoryError(f"inventory element {e}: field {f!r} missing")
        if e["family"] not in FAMILIES:
            raise InventoryError(f"{element_key(e)}: family {e['family']!r} not one of {FAMILIES}")
        if e["applicability"] not in APPLICABILITY:
            raise InventoryError(f"{element_key(e)}: applicability {e['applicability']!r}")
        k = element_key(e)
        if k in out:
            raise InventoryError(f"{k}: listed twice in the inventory (one face, one item, once)")
        q = e.get("qty")
        if e["applicability"] == "NOT_APPLICABLE":
            ev = e.get("evidence") or {}
            if not (ev.get("sheet") and ev.get("ref")):
                raise InventoryError(f"{k}: NOT_APPLICABLE without evidence (sheet and ref / handle required)")
            if q is not None:
                raise InventoryError(f"{k}: a NOT_APPLICABLE element carries no quantity")
        else:
            if q is not None and (not _num(q) or q <= 0):
                raise InventoryError(f"{k}: inventory quantity {q!r}: an applicable face is a positive number or "
                                     "None (held / not established), never 0")
        out[k] = e
    return out


def join(elements, lines, links):
    """elements: inventory rows; lines: [{line_id, item_code, unit, evidence_state, measured_net}]; links: line_id ->
    [key, ...] (the elements the line names). -> report dict."""
    inv = validate_inventory(elements)
    by_line = {}
    for ln in lines:
        if ln["line_id"] in by_line:
            raise InventoryError(f"line {ln['line_id']} given twice")
        by_line[ln["line_id"]] = ln
    carried = defaultdict(list)                   # key -> [line ids]
    register_only = []
    for lid in sorted(links):
        if lid not in by_line:
            raise InventoryError(f"link names an unknown line {lid}")
        ln = by_line[lid]
        for k in links[lid]:
            e = inv.get(k)
            if e is None:
                register_only.append({"line_id": lid, "key": k})
                continue
            if (e["item_code"], e["unit"]) != (ln["item_code"], ln["unit"]):
                raise InventoryError(f"line {lid} ({ln['item_code']} {ln['unit']}) linked to {k}: another item / unit")
            carried[k].append(lid)
    rows = []
    for k in sorted(inv):
        e = inv[k]
        lids = sorted(set(carried.get(k, [])))
        if len(lids) > 1:
            raise InventoryError(f"{k}: carried by {len(lids)} lines {lids} of one item code and unit (double count)")
        if e["applicability"] == "NOT_APPLICABLE":
            if lids:
                raise InventoryError(f"{k}: NOT_APPLICABLE ({e['evidence']['ref']}) but carried by line {lids[0]}")
            status, lid, state = "NOT_APPLICABLE", None, None
        elif lids:
            status, lid, state = "IN_LINE", lids[0], by_line[lids[0]]["evidence_state"]
        else:
            status, lid, state = "MISSING", None, None
        qty = e.get("qty")
        if status == "MISSING" and qty is not None and qty == 0:
            raise InventoryError(f"{k}: MISSING reported as 0 (an omission is blank, never a zero)")
        rows.append({"key": k, "family": e["family"], "item_code": e["item_code"], "unit": e["unit"],
                     "element": e["element"], "face": e["face"], "floor": e["floor"], "status": status,
                     "line_id": lid, "line_state": state,
                     "qty": None if status == "NOT_APPLICABLE" else qty,
                     "evidence": e.get("evidence") if status == "NOT_APPLICABLE" else None,
                     "owner": e.get("owner"), "source": e["source"], "note": e.get("note")})
    # residual per family / item / unit: inventory quantity of the IN_LINE elements on quantity lines vs line net
    fam = defaultdict(lambda: {"elements": 0, "in_line": 0, "in_line_quantity": 0, "in_line_held": 0, "na": 0,
                               "missing": 0, "inventory_qty": 0.0, "inventory_qty_open": 0, "lines": set()})
    for r in rows:
        f = fam[(r["family"], r["item_code"], r["unit"])]
        f["elements"] += 1
        if r["status"] == "NOT_APPLICABLE":
            f["na"] += 1
        elif r["status"] == "MISSING":
            f["missing"] += 1
        else:
            f["in_line"] += 1
            f["lines"].add(r["line_id"])
            if r["line_state"] in QUANTITY_STATES:
                f["in_line_quantity"] += 1
                if r["qty"] is None:
                    f["inventory_qty_open"] += 1
                else:
                    f["inventory_qty"] += r["qty"]
            else:
                f["in_line_held"] += 1
    fam_rows = []
    for (fa, ic, u), f in sorted(fam.items()):
        qlines = sorted(lid for lid in f["lines"] if by_line[lid]["evidence_state"] in QUANTITY_STATES)
        hlines = sorted(lid for lid in f["lines"] if by_line[lid]["evidence_state"] not in QUANTITY_STATES)
        line_qty = sum(by_line[lid]["measured_net"] for lid in qlines) if qlines else None
        inv_q = round(f["inventory_qty"], 6) if f["in_line_quantity"] and not f["inventory_qty_open"] else None
        res = None if (line_qty is None or inv_q is None) else round(inv_q - line_qty, 6)
        fam_rows.append({"family": fa, "item_code": ic, "unit": u, "elements": f["elements"],
                         "in_line": f["in_line"], "in_line_quantity": f["in_line_quantity"],
                         "in_line_held": f["in_line_held"], "not_applicable": f["na"], "missing": f["missing"],
                         "inventory_qty_in_line": inv_q, "line_qty": None if line_qty is None else round(line_qty, 6),
                         "residual": res, "quantity_lines": qlines, "held_lines": hlines,
                         "complete": f["missing"] == 0 and (res is None or abs(res) <= TOL),
                         # a quantity line can count as the WHOLE item only when no element of the item is held or
                         # missing and the inventory closes on it (otherwise it is a COMPONENT of the item)
                         "whole_line_countable": (f["missing"] == 0 and f["in_line_held"] == 0 and bool(qlines)
                                                  and res is not None and abs(res) <= TOL)})
    lines_unlinked = sorted(lid for lid in by_line if not links.get(lid))
    return {"schema": SCHEMA, "rule_id": RULE_ID, "elements": rows, "families": fam_rows,
            "register_only": register_only, "unlinked_lines": lines_unlinked,
            "counts": {s: sum(1 for r in rows if r["status"] == s) for s in ("IN_LINE", "NOT_APPLICABLE", "MISSING")}}


def to_t236(elements, links, source_id, basis="CENSUS"):
    """the inventory in the merged T-236 schema: one inventory (trade WATERPROOFING), NOT_APPLICABLE elements as
    exclusions with this rule id and their evidence, the line links by key. -> (inventories, exclusions, line_links)"""
    inv = validate_inventory(elements)
    els, exc = [], []
    for k, e in sorted(inv.items()):
        lab = k
        els.append({"floor": e["floor"], "label": lab, "ref": e.get("ref") or e["source"]})
        if e["applicability"] == "NOT_APPLICABLE":
            exc.append({"trade": TRADE, "key": f"{e['floor']}:{lab}", "rule_id": RULE_ID,
                        "basis": f"{e['evidence']['sheet']}: {e['evidence']['ref']}"})
    floors = sorted({e["floor"] for e in inv.values()})
    inventories = [{"source": source_id, "basis": basis, "trade": TRADE, "floors": floors, "elements": els}]
    ll = {lid: [f"{inv[k]['floor']}:{k}" if k in inv else k for k in ks] for lid, ks in links.items()}
    return inventories, exc, ll


__all__ = ["SCHEMA", "RULE_ID", "FAMILIES", "InventoryError", "element_key", "validate_inventory", "join", "to_t236"]
