"""T-289 structural BASIS LEDGER (research, read-only; any villa).

One row per candidate BOQ line whose quantity rests on a depth / height: the engine quantity, the depth / height it
was computed on, what the drawings print for THAT element (sheet, note, handle) and either a drawing-derived quantity
with its status or HELD (blank) with the named item. It is the input lane I (T-254 / T-266) consumes and that a
Checker-issued downgrade record (T-245 (f)) cites; it writes no candidate line, no released quantity, no V2 record.

Physical elements (ERS s.2.1):
- a ground beam is the concrete between its drawn faces from its printed soffit to its printed top: depth = the
  depth printed for that beam's own class / section (or derived from two printed levels of that element); a depth
  borrowed from another class, a neighbour or a convention is refused (lessons 2026-10-24, T-242 / T-248);
- a column runs from the top of the member under it to the soffit of the member over it; a top at a finished level
  (FFL, finished roof) is refused (UP-LEVEL-DATUM lesson 2026-10-23); an unprinted top keeps the column HELD;
- a stair flight's waist and riser are printed or HELD (OWNER_RULE_STAIRS_2026-10-24 s.4, S-9).
Unresolved stays HELD and BLANK, never 0 (owner no-assumptions rule).
"""

from __future__ import annotations

import csv
import math
from pathlib import Path

SCHEMA = "T289_STRUCTURAL_BASIS_LEDGER_V1"
TOL_M3 = 5e-4                               # residual tolerance between a named total and its line-id sum (0.000 m3)

DRAWING_DERIVED = "DRAWING-DERIVED"         # quantity from the element's own printed dimensions (not VERIFIED)
DRAWING_DERIVED_DC = "DRAWING-CONFIRMED"    # carried from a merged, Checker-checked ledger at its recorded status
HELD = "HELD"
CONFLICT = "CONFLICT"
PENDING = "PENDING-VERIFICATION"            # a drawing-derived value from an unmerged task: never carried as a quantity

OWN_PRINT = "OWN_PRINT"                     # the depth / level is printed for this element (or its own class)
STRUCTURAL_TOPS = ("SLAB_SOFFIT", "BEAM_SOFFIT")
STRUCTURAL_BASES = ("FOOTING_TOP", "NECK_TOP", "GROUND_BEAM_TOP", "SLAB_TOP")
FINISHED = ("FFL", "FINISHED_LEVEL", "FINISHED_ROOF")

COLUMNS = ["schema", "project_id", "revision_set_sha256", "candidate", "group", "line_id", "item_code", "element_id",
           "physical_element", "engine_qty_m3", "engine_basis", "printed_support", "sheets_searched",
           "drawing_qty_m3", "drawing_low_m3", "drawing_high_m3", "status", "held_item", "delta_m3", "reason",
           "evidence"]


class BasisError(ValueError):
    """a ledger row or a ledger that must be refused"""


def _num(v):
    return None if v is None or v == "" else float(v)


def _need(rec, *keys):
    for k in keys:
        if rec.get(k) in (None, ""):
            raise BasisError(f"{rec.get('line_id')}: '{k}' missing")


def _held(rec, item, reason):
    if not item:
        raise BasisError(f"{rec.get('line_id')}: a HELD row names its item")
    return dict(drawing_qty_m3=None, drawing_low_m3=_num(rec.get("low_m3")), drawing_high_m3=_num(rec.get("high_m3")),
                status=rec.get("status_if_held") or HELD, held_item=item, reason=reason)


def ground_beam(rec: dict) -> dict:
    """rec: line_id, element_id, engine_qty_m3, engine_basis, net_plan_m2 (the line's own plan area, faces to faces),
    depth = {"value_m", "source", "sheet", "note"} or None, held_item (when no own print).
    -> the row's drawing columns. A depth whose source is not OWN_PRINT is refused; no depth -> HELD, never 0."""
    _need(rec, "line_id", "element_id", "engine_qty_m3", "net_plan_m2")
    d = rec.get("depth")
    if d is None:
        return _held(rec, rec.get("held_item"), rec.get("reason") or "no depth printed for this beam's class")
    if d.get("source") != OWN_PRINT:
        raise BasisError(f"{rec['line_id']}: depth from '{d.get('source')}' (not printed for this beam) refused")
    v = _num(d.get("value_m"))
    if v is None or v <= 0:
        raise BasisError(f"{rec['line_id']}: a printed depth is a positive value; missing is HELD, never 0")
    if not d.get("sheet"):
        raise BasisError(f"{rec['line_id']}: a printed depth names its sheet")
    q = float(rec["net_plan_m2"]) * v
    return dict(drawing_qty_m3=q, drawing_low_m3=None, drawing_high_m3=None,
                status=rec.get("status") or DRAWING_DERIVED, held_item="",
                reason=rec.get("reason") or f"net plan {float(rec['net_plan_m2']):.4f} m2 x printed depth {v:g} m")


def column(rec: dict) -> dict:
    """rec: line_id, element_id, engine_qty_m3, area_m2, base = {"level_m", "kind", "sheet"},
    top = {"level_m", "kind", "sheet"} or None, held_item.
    The column runs from the top of the member under it to the soffit of the member over it."""
    _need(rec, "line_id", "element_id", "engine_qty_m3", "area_m2")
    top, base = rec.get("top"), rec.get("base")
    for end, allowed in ((top, STRUCTURAL_TOPS), (base, STRUCTURAL_BASES)):
        if end is not None and end.get("kind") in FINISHED:
            raise BasisError(f"{rec['line_id']}: column end at a finished level ({end.get('kind')}) refused")
        if end is not None and end.get("kind") not in allowed:
            raise BasisError(f"{rec['line_id']}: column end kind '{end.get('kind')}' is not a structural datum")
    if top is None or base is None or _num(top.get("level_m")) is None or _num(base.get("level_m")) is None:
        return _held(rec, rec.get("held_item"), rec.get("reason") or "column top or base not printed")
    h = float(top["level_m"]) - float(base["level_m"])
    if h <= 0:
        raise BasisError(f"{rec['line_id']}: column height {h:.3f} m is not positive")
    q = float(rec["area_m2"]) * h
    return dict(drawing_qty_m3=q, drawing_low_m3=None, drawing_high_m3=None,
                status=rec.get("status") or DRAWING_DERIVED, held_item="",
                reason=rec.get("reason") or f"area {float(rec['area_m2']):.4f} m2 x ({top['level_m']} - {base['level_m']}) m")


def carried(rec: dict) -> dict:
    """a row whose drawing quantity comes from a merged, Checker-checked ledger (value + status + the ledger named);
    a value from an unmerged task is never carried: it stays PENDING with its quantity blank."""
    _need(rec, "line_id", "element_id", "engine_qty_m3", "source_ledger")
    if rec.get("source_merged") is not True:
        return dict(drawing_qty_m3=None, drawing_low_m3=_num(rec.get("low_m3")), drawing_high_m3=_num(rec.get("high_m3")),
                    status=PENDING, held_item=rec.get("held_item") or f"verdict on {rec['source_ledger']}",
                    reason=rec.get("reason") or "drawing-derived value of an unmerged task: not carried")
    if rec.get("value_m3") is None:
        return _held(rec, rec.get("held_item"), rec.get("reason") or f"{rec['source_ledger']}: HELD")
    return dict(drawing_qty_m3=float(rec["value_m3"]), drawing_low_m3=None, drawing_high_m3=None,
                status=rec.get("status") or DRAWING_DERIVED_DC, held_item=rec.get("held_item") or "",
                reason=rec.get("reason") or f"carried from {rec['source_ledger']}")


KINDS = {"GROUND_BEAM": ground_beam, "COLUMN": column, "CARRIED": carried}


def row(rec: dict, ctx: dict) -> dict:
    out = {"schema": SCHEMA, "project_id": ctx["project_id"], "revision_set_sha256": ctx["revision_set_sha256"],
           "candidate": ctx["candidate"]}
    for k in ("group", "line_id", "item_code", "element_id", "physical_element", "engine_basis", "printed_support",
              "sheets_searched", "evidence"):
        out[k] = rec.get(k, "")
    out["engine_qty_m3"] = float(rec["engine_qty_m3"])
    out.update(KINDS[rec["kind"]](rec))
    q = out["drawing_qty_m3"]
    out["delta_m3"] = None if q is None else q - out["engine_qty_m3"]
    if out["status"] in (HELD, CONFLICT, PENDING) and q is not None:
        raise BasisError(f"{rec['line_id']}: a {out['status']} row carries no quantity")
    return out


def ledger(groups: dict, records: list, ctx: dict) -> list:
    """groups: {name: named total m3}; every record names its group. Refused: a duplicated line id, a record of an
    unnamed group, a group with no record, a group whose line-id sum differs from its named total (> 0.0005 m3)."""
    for k in ("project_id", "revision_set_sha256", "candidate"):
        if not ctx.get(k):
            raise BasisError(f"ledger context '{k}' missing (one project, one revision set, one candidate)")
    ids = [r["line_id"] for r in records]
    if len(ids) != len(set(ids)):
        raise BasisError("a line id appears twice")
    rows = [row(r, ctx) for r in records]
    for g, total in groups.items():
        s = math.fsum(r["engine_qty_m3"] for r in rows if r["group"] == g)
        if not any(r["group"] == g for r in rows):
            raise BasisError(f"group {g}: no line")
        if abs(s - total) > TOL_M3:
            raise BasisError(f"group {g}: line-id sum {s:.4f} differs from the named total {total:.4f} m3")
    extra = {r["group"] for r in rows} - set(groups)
    if extra:
        raise BasisError(f"rows of unnamed groups {sorted(extra)}")
    return rows


def residuals(groups: dict, rows: list) -> dict:
    return {g: round(math.fsum(r["engine_qty_m3"] for r in rows if r["group"] == g) - t, 6) for g, t in groups.items()}


def totals(rows: list) -> dict:
    out = {}
    for r in rows:
        t = out.setdefault(r["group"], {"lines": 0, "engine_m3": 0.0, "by_status": {}})
        t["lines"] += 1
        t["engine_m3"] = round(t["engine_m3"] + r["engine_qty_m3"], 6)
        s = t["by_status"].setdefault(r["status"], [0, 0.0])
        s[0] += 1
        if r["drawing_qty_m3"] is not None:
            s[1] = round(s[1] + r["drawing_qty_m3"], 6)
    return out


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
