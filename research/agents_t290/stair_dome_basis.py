"""T-290 STAIRS AND DOMES BASIS LEDGER (research, read-only; any villa).

One row per candidate BOQ line of the stair / dome concrete items (STR.CONC.STAIR*, STR.CONC.DOME*, m3): the engine
quantity and state, the physical pieces the line measures (flight, landing, steps, waist, winder turn, turn riser,
dome shell, ring, drum) taken from an ENGINE-FREE component inventory, each piece's evidence status with its source
(Checker run, owner rule, drawing sheet), and the line's drawing quantity or HELD / CONFLICT BLANK with the named items.
It is the input lane I (T-266) consumes to correct the stair / dome lines mechanically; it writes no candidate line,
no released quantity, no V2 record. Shape: the T-289 BASIS_LEDGER columns, then the stair-specific columns.

Physical elements and rules (ERS s.2.1; OWNER_RULE_STAIRS_2026-10-24 s.4 / s.6; R-CONC-OWN-1 / -1a):
- a component is ONE physical piece, owned by ONE line; a piece that another line bills (a head in a floor beam, a
  floor-level landing in the slab, a dome ring in the beam line) is OWNED_ELSEWHERE and never bound to a stair line;
- a closable component carries its value and its evidence: VERIFIED names the Checker record, ASSUMED - OWNER-APPROVED
  names the owner rule, DRAWING-CONFIRMED names the sheet; every dimension it rests on is PRINTED, CHECKER-measured or
  OWNER_RULE; a dimension from a CONVENTION is never DRAWING-CONFIRMED (or VERIFIED): the piece is HELD;
- a winder / curved part is measured only when drawn AND dimensioned (S-9): otherwise HELD with a blank value, never
  generated, never a walking-line offset;
- HELD / UNKNOWN carry no value (a bound may be shown); CONFLICT carries its two readings as a range, never one end;
- a line's drawing quantity is the sum of its components only when every component is closable; its status is the
  weakest of theirs (VERIFIED > DRAWING-CONFIRMED > ASSUMED - OWNER-APPROVED). Otherwise the line is HELD (or
  CONFLICT) and BLANK, its closable part listed beside it. Unresolved stays blank, never 0 (owner no-assumptions rule).
- the staircase system as a whole is never labelled VERIFIED (owner 2026-10-22 16:35): the ledger reports by line.
"""

from __future__ import annotations

import csv
import math
from pathlib import Path

SCHEMA = "T290_STAIR_DOME_BASIS_LEDGER_V1"
TOL_M3 = 5e-4

VERIFIED = "VERIFIED"
DC = "DRAWING-CONFIRMED"
AOA = "ASSUMED — OWNER-APPROVED"
HELD = "HELD"
CONFLICT = "CONFLICT"
UNKNOWN = "UNKNOWN"
OWNED_ELSEWHERE = "OWNED_ELSEWHERE"
NOT_APPLICABLE = "NOT_APPLICABLE"          # a retired / superseded engine line with no physical piece of its own
CITED = "CITED"                            # the line's basis row lives in another ledger (named): cited, not re-booked

CLOSABLE = (VERIFIED, DC, AOA)             # strongest first
DIM_SOURCES_OK = {VERIFIED: ("PRINTED", "CHECKER"), DC: ("PRINTED", "CHECKER"),
                  AOA: ("PRINTED", "CHECKER", "OWNER_RULE")}
CURVED_KINDS = ("WINDER", "CURVED")

COLUMNS = ["schema", "project_id", "revision_set_sha256", "candidate", "group", "line_id", "item_code", "element_id",
           "physical_element", "engine_qty_m3", "engine_basis", "printed_support", "sheets_searched",
           "drawing_qty_m3", "drawing_low_m3", "drawing_high_m3", "status", "held_item", "delta_m3", "reason",
           "evidence",
           # T-290 columns (stairs / domes)
           "engine_state", "components", "closable_component_m3", "closable_by_status", "ledger_owner",
           "soffit_rows", "formwork_rows"]


class BasisError(ValueError):
    """a component, a line or a ledger that must be refused"""


def _num(v):
    return None if v is None or v == "" else float(v)


def component(c: dict) -> dict:
    """validate one physical piece. c: id, element, piece, kind (FLIGHT / LANDING / STEPS / WAIST / WINDER / CURVED /
    TURN / SHELL / RING / DRUM / ...), status, value_m3, low_m3, high_m3, dims {name: source}, checker, owner_rule,
    sheet, held_item, owner_line (OWNED_ELSEWHERE), drawn_dimensioned (WINDER / CURVED), soffit_rows, formwork_rows."""
    cid, st = c.get("id"), c.get("status")
    if not cid:
        raise BasisError("a component has an id")
    v = _num(c.get("value_m3"))
    dims = c.get("dims") or {}
    if c.get("kind") in CURVED_KINDS and not c.get("drawn_dimensioned") and st != OWNED_ELSEWHERE:
        if st != HELD or v is not None:
            raise BasisError(f"{cid}: a winder / curved piece that is not drawn and dimensioned is HELD blank "
                             "(S-9: never generated)")
    if st in CLOSABLE:
        if v is None or v <= 0:
            raise BasisError(f"{cid}: a {st} piece carries a positive value; missing is HELD, never 0")
        need = {VERIFIED: "checker", AOA: "owner_rule", DC: "sheet"}[st]
        if not c.get(need):
            raise BasisError(f"{cid}: {st} names its {need}")
        for d, src in dims.items():
            if src not in DIM_SOURCES_OK[st]:
                raise BasisError(f"{cid}: dimension '{d}' from {src} cannot be {st}; the piece is HELD")
    elif st in (HELD, UNKNOWN):
        if v is not None:
            raise BasisError(f"{cid}: a {st} piece carries no value (a bound goes in low / high)")
        if st == HELD and not c.get("held_item"):
            raise BasisError(f"{cid}: a HELD piece names its item")
    elif st == CONFLICT:
        lo, hi = _num(c.get("low_m3")), _num(c.get("high_m3"))
        if v is not None or lo is None or hi is None or not lo < hi:
            raise BasisError(f"{cid}: a CONFLICT carries both readings low < high and no single value")
        if not c.get("held_item"):
            raise BasisError(f"{cid}: a CONFLICT names its item")
    elif st == OWNED_ELSEWHERE:
        if not c.get("owner_line") or c.get("owner_line") in ("STAIR", "DOME"):
            raise BasisError(f"{cid}: OWNED_ELSEWHERE names the other line (not the stair / dome line)")
    else:
        raise BasisError(f"{cid}: unknown status '{st}'")
    return c


def _weakest(statuses):
    return max(statuses, key=CLOSABLE.index)


def line_row(line: dict, comps: dict, ctx: dict) -> dict:
    """line: line_id, item_code, element_id, physical_element, engine_qty_m3 (None for a blocked line), engine_state,
    engine_basis, components [ids], printed_support, sheets_searched, evidence, group, cited (a ledger name) ."""
    lid = line.get("line_id")
    out = {"schema": SCHEMA, "project_id": ctx["project_id"], "revision_set_sha256": ctx["revision_set_sha256"],
           "candidate": ctx["candidate"], "ledger_owner": line.get("cited") or "T-290"}
    for k in ("group", "line_id", "item_code", "element_id", "physical_element", "engine_basis", "printed_support",
              "sheets_searched", "evidence", "engine_state"):
        out[k] = line.get(k, "")
    out["engine_qty_m3"] = _num(line.get("engine_qty_m3"))
    ids = list(line.get("components") or [])
    cs = [comps[i] for i in ids]
    for c in cs:
        if c["status"] == OWNED_ELSEWHERE:
            raise BasisError(f"{lid}: piece {c['id']} is owned by the {c['owner_line']} line, never by this one")
    out["components"] = " + ".join(ids)
    out["soffit_rows"] = " ; ".join(r for c in cs for r in c.get("soffit_rows", []))
    out["formwork_rows"] = " ; ".join(r for c in cs for r in c.get("formwork_rows", []))
    clos = [c for c in cs if c["status"] in CLOSABLE]
    by = {}
    for c in clos:
        by[c["status"]] = by.get(c["status"], 0.0) + float(c["value_m3"])
    out["closable_component_m3"] = math.fsum(float(c["value_m3"]) for c in clos) if clos else None
    out["closable_by_status"] = "; ".join(f"{s} {by[s]:.6f}" for s in CLOSABLE if s in by)
    q = lo = hi = None
    items = [c.get("held_item") for c in cs if c["status"] in (HELD, CONFLICT, UNKNOWN)]
    if line.get("cited"):
        if line.get("drawing_qty_m3") not in (None, ""):
            raise BasisError(f"{lid}: a CITED row books no quantity of its own (it lives in {line['cited']})")
        status, reason = line.get("cited_status") or CITED, f"basis row in {line['cited']} (cited, not re-booked)"
        items = [line.get("cited_item") or ""]
    elif not cs:
        if out["engine_qty_m3"] not in (None, 0.0) or line.get("engine_state") != "NOT_APPLICABLE_WITH_EVIDENCE":
            raise BasisError(f"{lid}: a line with no physical piece must be a retired NOT_APPLICABLE line "
                             "with no quantity")
        if not line.get("reason"):
            raise BasisError(f"{lid}: a retired line names why")
        status, reason = NOT_APPLICABLE, line["reason"]
    elif len(clos) == len(cs):
        q = math.fsum(float(c["value_m3"]) for c in cs)
        status = _weakest([c["status"] for c in cs])
        reason = " + ".join(f"{c['id']} {float(c['value_m3']):.6f} {c['status']}" for c in cs)
    elif any(c["status"] == CONFLICT for c in cs) and all(c["status"] in CLOSABLE + (CONFLICT,) for c in cs):
        conf = [c for c in cs if c["status"] == CONFLICT]
        base = out["closable_component_m3"] or 0.0
        lo = base + math.fsum(float(c["low_m3"]) for c in conf)
        hi = base + math.fsum(float(c["high_m3"]) for c in conf)
        status, reason = CONFLICT, "closable part + CONFLICT reading range (never one end)"
    else:
        status = HELD
        reason = "HELD piece(s) in the line: the line is blank; its closable part is listed beside it"
        open_ = [c for c in cs if c["status"] not in CLOSABLE]
        if all(_num(c.get("low_m3")) is not None and _num(c.get("high_m3")) is not None for c in open_):
            # a bound exists only when EVERY open piece is bounded; one unbounded piece leaves the line unbounded
            base = out["closable_component_m3"] or 0.0
            lo = base + math.fsum(float(c["low_m3"]) for c in open_)
            hi = base + math.fsum(float(c["high_m3"]) for c in open_)
    out.update(drawing_qty_m3=q, drawing_low_m3=lo, drawing_high_m3=hi, status=status,
               held_item=" | ".join(i for i in items if i), reason=line.get("note") or reason)
    out["delta_m3"] = None if q is None or out["engine_qty_m3"] is None else q - out["engine_qty_m3"]
    if status in (HELD, CONFLICT, CITED) and q is not None:
        raise BasisError(f"{lid}: a {status} line carries no quantity")
    return out


def ledger(lines: list, comps: list, ctx: dict, named: dict | None = None) -> list:
    """lines: every stair / dome line of the candidate (once); comps: the engine-free piece inventory.
    named: {group: named engine total m3}. Refused: a context field missing, a duplicated line id or piece id, a piece
    bound to two lines, an unknown piece, a soffit / formwork row given to two pieces, a group sum off its named total."""
    for k in ("project_id", "revision_set_sha256", "candidate"):
        if not ctx.get(k):
            raise BasisError(f"ledger context '{k}' missing (one project, one revision set, one candidate)")
    cmap = {}
    for c in comps:
        component(c)
        if c["id"] in cmap:
            raise BasisError(f"piece {c['id']} appears twice in the inventory")
        cmap[c["id"]] = c
    for key in ("soffit_rows", "formwork_rows"):
        seen = {}
        for c in comps:
            for r in c.get(key, []):
                if r in seen:
                    raise BasisError(f"{key[:-5]} row '{r}' given to two pieces ({seen[r]}, {c['id']}): one owner")
                seen[r] = c["id"]
    ids = [ln["line_id"] for ln in lines]
    if len(ids) != len(set(ids)):
        raise BasisError("a line id appears twice")
    bound = {}
    for ln in lines:
        for i in ln.get("components") or []:
            if i not in cmap:
                raise BasisError(f"{ln['line_id']}: unknown piece {i}")
            if i in bound:
                raise BasisError(f"piece {i} in two lines ({bound[i]}, {ln['line_id']}): the same piece is booked once")
            bound[i] = ln["line_id"]
    rows = [line_row(ln, cmap, ctx) for ln in lines]
    for g, total in (named or {}).items():
        s = math.fsum(r["engine_qty_m3"] or 0.0 for r in rows if r["group"] == g)
        if abs(s - total) > TOL_M3:
            raise BasisError(f"group {g}: line-id sum {s:.6f} differs from the named total {total:.6f} m3")
    return rows


def unbound(rows: list, comps: list) -> list:
    """stair / dome pieces of the inventory that no candidate line measures and no other line owns: an omission."""
    used = {i for r in rows for i in (r["components"].split(" + ") if r["components"] else [])}
    return [c["id"] for c in comps if c["id"] not in used and c["status"] != OWNED_ELSEWHERE]


def flight_owner_method(n_goings: int, riser: float, going: float, width: float, waist: float) -> float:
    """owner method (Q-19 / Q-47 A): n step triangles + the waist along the sloped length of the n goings (m3).
    Every input is a printed value; no default is supplied."""
    for name, v in (("riser", riser), ("going", going), ("width", width), ("waist", waist)):
        if v is None or v <= 0:
            raise BasisError(f"flight {name} missing: HELD, never a default")
    if n_goings <= 0:
        raise BasisError("flight goings missing: HELD")
    steps = n_goings * 0.5 * riser * going * width
    return steps + waist * width * math.hypot(n_goings * going, n_goings * riser)


def _fmt(v):
    if v is None:
        return ""
    if isinstance(v, float):
        return f"{v:.6f}"
    return str(v)


def write_csv(path, rows: list) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: _fmt(r.get(k)) for k in COLUMNS})
