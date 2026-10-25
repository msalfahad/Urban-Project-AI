"""T-303: the WATERPROOFING SCOPE INVENTORY for the WET-AREA and ROOF families and the POOL / TANK presence ruling (part 2
of T-301; Verifier 2026-10-25 11:28 F-REC-02: without a face inventory no waterproofing line can be counted WHOLE).

A pure CHECK on plain data: it writes nothing, moves no quantity, is wired into no method; nothing here names a project,
a sheet, a layer or a coordinate (the project adapter is t303_alsenan.py). It builds on the merged T-301 core
(research/agents_t301/t301_wp_inventory.py, imported read-only: schema, statuses, join, residual, T-236 conversion) and
adds only what the wet-area, roof and pool / tank families need:

  check_wet_rooms   every room a wet-area line names is an inventory wet room, and every inventory wet room has a drawn
                    door or a named open edge (open defect D-C3: a doorless cell merged into a wet room must not take wet
                    scope silently) -> refused (InventoryError) otherwise
  walls_only_lm     the upturn length of a wet room under owner Q-35 C (walls only: the boundary less every doorway,
                    leafless opening and open edge; no upturn across any doorway, also between two wet rooms)
  doorway_m2        the threshold floor piece of one doorway (width x wall depth), one per PHYSICAL door
  split_doubles     a face that two lines of one item code and unit carry is a double count: the strict T-301 join
                    refuses it; on a real candidate the double is reported (DOUBLE_CARRIED, never absorbed) and the item
                    can never read WHOLE
  join_family       split_doubles + the T-301 join + the doubles carried into the family rows
  presence_ruling   one pool / tank element: a printed WP layer makes it APPLICABLE (MISSING when no line carries it,
                    never a guessed membrane); a sheet that shows the element without a WP layer makes it NOT_APPLICABLE
                    with that evidence; neither -> refused (presence not established)
  scope_unknown     an element whose applicability the drawings / owner answers do not settle: APPLICABLE with a BLANK
                    quantity, reported MISSING with its reason SCOPE_UNKNOWN (never NOT_APPLICABLE without evidence and
                    never 0)
"""

from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "agents_t301"))

import t301_wp_inventory as W  # noqa: E402  (merged T-301 core, read-only)

RULE_ID = "R-T303-WP-FAMILIES-1"
UPTURN_M = 0.20                       # UP-WP-003 (owner Q-03 / Q-24): 0.20 m upturn on the walls / parapets
InventoryError = W.InventoryError
element_key = W.element_key


def _pos(x, what, hi):
    if not W._num(x) or x <= 0:
        raise InventoryError(f"{what} {x!r}: a positive drawn value is required (missing is HELD, never 0)")
    if x > hi:
        raise InventoryError(f"{what} {x!r} > {hi}: read as millimetres? (metres required)")
    return float(x)


def walls_only_lm(boundary_m, door_widths=(), leafless_widths=(), open_edges=()):
    """walls-only upturn length (Q-35 C): boundary less every doorway, leafless opening and open edge."""
    b = _pos(boundary_m, "wet-room boundary", 500.0)
    gaps = [_pos(w, "opening width", 20.0) for w in (*door_widths, *leafless_widths, *open_edges)]
    lm = b - sum(gaps)
    if lm <= 0:
        raise InventoryError(f"walls-only length {lm:.4f} <= 0: openings exceed the boundary")
    return round(lm, 6)


def doorway_m2(width_m, depth_m):
    """the threshold floor piece of ONE physical doorway."""
    return round(_pos(width_m, "door width", 5.0) * _pos(depth_m, "wall depth", 1.0), 6)


def check_wet_rooms(rooms, line_rooms):
    """rooms: {room: {"doors": [...], "open_edges": [...]}}; line_rooms: rooms named by wet-area lines."""
    for r, x in sorted(rooms.items()):
        if not (x.get("doors") or x.get("open_edges")):
            raise InventoryError(f"wet room {r}: no drawn door and no named open edge (D-C3: a doorless cell must not "
                                 "take wet scope)")
    extra = sorted(set(line_rooms) - set(rooms))
    if extra:
        raise InventoryError(f"wet-area lines on cells that are not inventory wet rooms {extra} (D-C3: a doorless or "
                             "unlisted cell taking wet scope)")
    return True


def split_doubles(links, lines):
    """-> (links with each doubled key kept on the first line only, [{key, lines}]): a double count is reported."""
    item = {ln["line_id"]: (ln["item_code"], ln["unit"]) for ln in lines}
    by_key = defaultdict(list)
    for lid in sorted(links):
        for k in links[lid]:
            by_key[k].append(lid)
    doubles = [{"key": k, "lines": sorted(set(v))} for k, v in sorted(by_key.items()) if len(set(v)) > 1]
    drop = {(d["key"], lid) for d in doubles for lid in d["lines"][1:]}
    clean = {lid: [k for k in ks if (k, lid) not in drop] for lid, ks in links.items()}
    for d in doubles:
        d["item"] = item[d["lines"][0]]
    return clean, doubles


def join_family(elements, lines, links):
    clean, doubles = split_doubles(links, lines)
    rep = W.join(elements, lines, clean)
    rep["double_carried"] = doubles
    hit = defaultdict(list)
    for d in doubles:
        hit[d["item"]].append(d)
    for f in rep["families"]:
        dd = hit.get((f["item_code"], f["unit"]), [])
        f["double_carried"] = len(dd)
        if dd:
            f["complete"] = False
            f["whole_line_countable"] = False
    # a line whose only link was a doubled key is now unlinked in the strict join: it is the double, not a gap
    dbl_lines = {lid for d in doubles for lid in d["lines"][1:]}
    rep["unlinked_lines"] = [lid for lid in rep["unlinked_lines"] if lid not in dbl_lines]
    return rep


def presence_ruling(family, item_code, unit, element, face, floor, source, printed=None, not_printed=None, note=None):
    """one pool / tank presence element (see the module text)."""
    if printed and not_printed:
        raise InventoryError(f"{element}: printed AND not printed: the two sheets disagree (a conflict, not a ruling)")
    if printed:
        if not (printed.get("sheet") and printed.get("ref")):
            raise InventoryError(f"{element}: a printed WP layer needs its sheet and ref / handle")
        return {"family": family, "item_code": item_code, "unit": unit, "element": element, "face": face,
                "floor": floor, "applicability": "APPLICABLE", "qty": None, "source": source,
                "ref": f"{printed['sheet']}: {printed['ref']}", "owner": None,
                "note": "WP layer PRINTED" + (f"; {note}" if note else "")}
    if not_printed:
        if not (not_printed.get("sheet") and not_printed.get("ref")):
            raise InventoryError(f"{element}: NOT_APPLICABLE without evidence (sheet and ref / handle required)")
        return {"family": family, "item_code": item_code, "unit": unit, "element": element, "face": face,
                "floor": floor, "applicability": "NOT_APPLICABLE", "qty": None, "source": source,
                "ref": not_printed["ref"], "owner": None, "evidence": not_printed, "note": note}
    raise InventoryError(f"{element}: presence not established (neither a printed WP layer nor a sheet without one)")


def scope_unknown(family, item_code, unit, element, face, floor, source, reason, scope=None):
    if not reason:
        raise InventoryError(f"{element}: SCOPE_UNKNOWN needs its reason")
    return {"family": family, "item_code": item_code, "unit": unit, "element": element, "face": face, "floor": floor,
            "applicability": "APPLICABLE", "qty": None, "source": source, "ref": None, "owner": scope,
            "note": f"SCOPE_UNKNOWN: {reason}"}


def line_rows(rep, lines, links, scope_of_line, scope_of_element, tol=W.TOL):
    """per line (wet-area and roof lines are one per room / roof, not one per item): the elements it carries, their
    inventory quantity vs the line's net (residual in the unit, never absorbed) and its countability:
      HELD       the line itself is in a held state (its faces are blank)
      WHOLE      every element it carries is quantified, its residual is <= tol, none of its keys is doubled, and no
                 element of the same item in the same scope (room / roof) is MISSING or carried by a held line
      COMPONENT  otherwise, with the reason(s)."""
    el = {r["key"]: r for r in rep["elements"]}
    dbl = {d["key"] for d in rep.get("double_carried", [])}
    open_in_scope = defaultdict(list)
    for r in rep["elements"]:
        if r["status"] == "MISSING" or (r["status"] == "IN_LINE" and r["line_state"] not in W.QUANTITY_STATES):
            open_in_scope[(r["item_code"], r["unit"], scope_of_element(r))].append(r["key"])
    out = []
    for ln in sorted(lines, key=lambda x: (x["item_code"], x["unit"], x["line_id"])):
        ks = links.get(ln["line_id"], [])
        mine = [el[k] for k in ks if k in el and el[k]["line_id"] == ln["line_id"]]
        why = []
        inv = None
        if ln["evidence_state"] not in W.QUANTITY_STATES:
            status = "HELD"
        else:
            if not mine:
                why.append("carries no inventory element")
            q = [r["qty"] for r in mine]
            if mine and all(x is not None for x in q):
                inv = round(sum(q), 6)
            else:
                why.append("an element quantity is open")
            res = None if inv is None or ln["measured_net"] is None else round(inv - ln["measured_net"], 6)
            if res is not None and abs(res) > tol:
                why.append(f"residual {res:+.6f} {ln['unit']}")
            if any(k in dbl for k in ks):
                why.append("a face it carries is carried by another line too (double count)")
            others = [k for k in open_in_scope.get((ln["item_code"], ln["unit"], scope_of_line(ln)), [])]
            if others:
                why.append(f"{len(others)} element(s) of the same item in its scope missing / held")
            if [k for k in ks if k not in el]:
                why.append("names a key in no inventory (REGISTER_ONLY)")
            status = "COMPONENT" if why else "WHOLE"
        out.append({"line_id": ln["line_id"], "item_code": ln["item_code"], "unit": ln["unit"],
                    "scope": scope_of_line(ln), "line_state": ln["evidence_state"], "line_qty": ln["measured_net"],
                    "elements": len(mine), "inventory_qty": inv,
                    "residual": None if inv is None or ln["measured_net"] is None else round(inv - ln["measured_net"], 6),
                    "countability": status, "why": "; ".join(why)})
    return out


__all__ = ["RULE_ID", "UPTURN_M", "InventoryError", "element_key", "walls_only_lm", "doorway_m2", "check_wet_rooms",
           "split_doubles", "join_family", "presence_ruling", "scope_unknown", "line_rows"]
