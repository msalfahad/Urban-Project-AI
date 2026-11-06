"""T-553 floor tile reconciliation, room by room and by tile size class, engine candidate lines vs a freelancer's
per-room floor rows (any villa; research, unwired, measures nothing).

R-T553-1 (proposed, every villa). The physical element is the INSTALLED finished floor area of every tiled room
(dry porcelain, wet tile, or a floor whose finish is not established), net of what another trade owns (stair
footprint and landings: B7 marble; door thresholds: B3-04 marble; lift thresholds: B6) and of what is not floor
(walls, columns inside his gross outline). The table is reconciled room by room, delta = engine - freelancer, exact:
  (a) SCOPE OF LINES: an engine side holds only floor tile lines (FIN.FLOOR.PORCELAIN, FIN.FLOOR.WET_TILE,
      FIN.FLOOR.FINISH_HELD). A stair / marble line (FIN.MARBLE.*, FIN.STAIR.*) never enters the floor table: its
      area appears only as a component naming that line ('owned by B7 / B3-04 / B6'), and one owning line is named at
      most once in the whole table (stair marble owned once);
  (b) INSTALLED ONLY: every engine line and every freelancer cell declares its quantity basis; only 'installed'
      enters. A procurement figure (waste, packaging, spare inside) is refused (adverse case), so waste is never inside
      the installed comparison; a freelancer cell with a multiplier other than 1 or a waste column is refused;
  (c) TILE SIZE CLASS: each row carries the tile size key ('60x60', '120x60', '160x80', or another 'L x W' cm key) with
      its source (printed note, project document, owner project decision) or TILE_SIZE_NOT_GIVEN. A size without a
      source is refused; the two sides of a row must carry the same size key (a 60x60 room is never compared with a
      120x60 cell); the table is subtotalled by size key. Areas never depend on the size; adhesive / box quantities do
      (UPC-ADHESIVE-001, FINISH_MATERIALS_TABLE_V4) and stay HELD where the size is not given;
  (d) components (qty >= 0, sign, cause, basis) sum EXACTLY to the row delta. Causes: ENGINE_RIGHT, ENGINE_WRONG,
      RULE_DIFFERENCE, HELD (an engine HELD part against his figure, with its bound), TOLERANCE (only < 0.010: his
      2-dp truncation), UNRESOLVED (a NAMED remainder with what was tried; never absorbed into another cause). A
      freelancer figure is never a basis;
  (e) an engine line valued None is HELD: listed outside both totals with its bound, never 0; a HELD line valued 0 is
      refused;
  (f) the engine side sums to the valued candidate lines of the three floor tile codes (computed from the line index,
      never typed: no stale total) and the freelancer side to his printed total cell; the class split (dry / wet /
      finish held) is reported per side, and a room whose class differs between the sides (his dry row, our wet line)
      is a CLASS MOVE with zero area effect, listed, never a quantity cause;
  (g) COMPLETENESS JOIN: a released interior space that carries a ceiling line but no floor tile line (valued or
      HELD) is a missing floor item (ENGINE_WRONG with its corrected area), never silently absent.
"""
from __future__ import annotations

from decimal import Decimal
import re

FLOOR_CODES = ("FIN.FLOOR.PORCELAIN", "FIN.FLOOR.WET_TILE", "FIN.FLOOR.FINISH_HELD")
CLASS_OF = {"FIN.FLOOR.PORCELAIN": "DRY", "FIN.FLOOR.WET_TILE": "WET", "FIN.FLOOR.FINISH_HELD": "FINISH_HELD"}
OWNER_PREFIXES = ("FIN.MARBLE.", "FIN.STAIR.")
CAUSES = ("ENGINE_RIGHT", "ENGINE_WRONG", "RULE_DIFFERENCE", "HELD", "TOLERANCE", "UNRESOLVED")
TOL_MAX = Decimal("0.010")
NO_SIZE = "TILE_SIZE_NOT_GIVEN"
_SIZE_RE = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*[xX]\s*(\d+(?:\.\d+)?)\s*$")


class TileTableError(ValueError):
    pass


def D(x) -> Decimal:
    if x is None:
        raise TileTableError("quantity unknown (None) is never 0")
    if isinstance(x, float):
        return Decimal(repr(x))
    return Decimal(str(x))


def size_key(size, source) -> str:
    """'120x60' from a sourced size, NO_SIZE when none is given; a size without a source is refused."""
    if size is None:
        return NO_SIZE
    if not str(source or "").strip():
        raise TileTableError(f"tile size {size!r} has no source (printed note, project document or owner decision)")
    m = _SIZE_RE.match(str(size))
    if not m:
        raise TileTableError(f"tile size {size!r} is not 'L x W' in cm")
    a, b = sorted((Decimal(m.group(1)), Decimal(m.group(2))), reverse=True)
    return f"{a.normalize():f}x{b.normalize():f}"


def _engine_side(r: dict, index: dict | None):
    tot, held, classes = Decimal(0), [], {}
    for ln in r.get("engine_lines") or []:
        code = ln.get("item_code")
        if code is None or code.startswith(OWNER_PREFIXES) or code not in FLOOR_CODES:
            raise TileTableError(f"room {r['room']}: line {ln.get('line_id')} code {code!r} is not a floor tile line "
                                 f"(stair / marble is owned by its own line and named as a component only)")
        if ln.get("basis", "installed") != "installed":
            raise TileTableError(f"room {r['room']}: line {ln.get('line_id')} basis {ln.get('basis')!r}: only "
                                 f"installed m2 enters (waste / procurement never inside the comparison)")
        if index is not None:
            rec = index.get(ln["line_id"])
            if rec is None or rec["item_code"] != code:
                raise TileTableError(f"room {r['room']}: line {ln['line_id']} not in the candidate index as {code}")
            if (rec["measured_net"] is None) != (ln.get("qty") is None) or (
                    ln.get("qty") is not None and D(rec["measured_net"]) != D(ln["qty"])):
                raise TileTableError(f"room {r['room']}: line {ln['line_id']} value differs from the index (stale)")
        classes.setdefault(CLASS_OF[code], Decimal(0))
        if ln.get("qty") is None:
            held.append(ln)
            continue
        if ln.get("state") == "HELD":
            if D(ln["qty"]) == 0:
                raise TileTableError(f"line {ln.get('line_id')}: HELD valued 0 refused (never 0)")
            raise TileTableError(f"line {ln.get('line_id')}: HELD with a value refused")
        tot += D(ln["qty"])
        classes[CLASS_OF[code]] += D(ln["qty"])
    valued = len(r.get("engine_lines") or []) - len(held)
    return (tot if valued else None), held, classes


def _fl_side(r: dict):
    cells = r.get("freelancer") or []
    if not cells:
        return None
    tot = Decimal(0)
    for c in cells:
        if c.get("basis", "installed") != "installed":
            raise TileTableError(f"room {r['room']}: his cell row {c.get('row')} basis {c.get('basis')!r}: a "
                                 f"procurement figure is never compared with installed m2")
        if D(c.get("multiplier", 1)) != 1 or c.get("waste"):
            raise TileTableError(f"room {r['room']}: his cell row {c.get('row')} carries a multiplier / waste: "
                                 f"restate it as installed m2 first")
        tot += D(c["m2"])
    return tot


def reconcile(*, rows: list[dict], freelancer_total, index: dict | None = None, engine_total=None) -> dict:
    out, eng, fl, owners, held_lines = [], Decimal(0), Decimal(0), {}, []
    by_size, by_cause = {}, {}
    cls_eng, cls_fl, moves = {}, {}, []
    for r in rows:
        sk = size_key(r.get("tile_size"), r.get("tile_size_source"))
        fsk = size_key(r.get("freelancer_tile_size"), r.get("freelancer_tile_size_source"))
        if sk != fsk:
            raise TileTableError(f"room {r['room']}: tile size {sk} against his {fsk}: different products are never "
                                 f"one row")
        e, held, classes = _engine_side(r, index)
        f = _fl_side(r)
        for h in held:
            held_lines.append({"room": r["room"], "line_id": h["line_id"], "bound": h.get("bound"),
                               "note": h.get("note", "")})
        if e is None and f is None:
            if held:
                out.append({"room": r["room"], "size": sk, "engine": None, "freelancer": None, "delta": "0",
                            "state": "HELD", "components": []})
                continue
            raise TileTableError(f"room {r['room']}: no side")
        delta = (e or Decimal(0)) - (f or Decimal(0))
        comps, acc = [], Decimal(0)
        for c in r.get("components", []):
            cause = c.get("cause")
            if cause not in CAUSES:
                raise TileTableError(f"room {r['room']}: cause {cause!r} not in {CAUSES}")
            if not c.get("basis"):
                raise TileTableError(f"room {r['room']}: component {c.get('name')!r} has no basis")
            if str(c["basis"]).lower().startswith("freelancer"):
                raise TileTableError(f"room {r['room']}: a freelancer figure is never a component basis")
            if c.get("sign") not in (1, -1):
                raise TileTableError(f"room {r['room']}: sign must be +1 or -1")
            q = D(c.get("qty"))
            if q < 0:
                raise TileTableError(f"room {r['room']}: negative quantity; use the sign")
            if cause == "TOLERANCE" and q >= TOL_MAX:
                raise TileTableError(f"room {r['room']}: TOLERANCE {q} >= {TOL_MAX}: name the cause")
            own = c.get("owned_by")
            if own:
                if not str(own).startswith("L-") or c.get("owned_by_code", "").startswith(FLOOR_CODES):
                    raise TileTableError(f"room {r['room']}: owner line {own!r} must be another trade's line id")
                if own in owners:
                    raise TileTableError(f"line {own} owns an area in rows {owners[own]!r} and {r['room']!r}: "
                                         f"owned once")
                owners[own] = r["room"]
            acc += q * c["sign"]
            comps.append({"name": c["name"], "qty": str(q), "delta": str(q * c["sign"]), "cause": cause,
                          "basis": c["basis"], **({"owned_by": own} if own else {})})
            by_cause[cause] = by_cause.get(cause, Decimal(0)) + q * c["sign"]
        if (e is None or f is None) and (not comps or any(x["cause"] == "TOLERANCE" for x in comps)):
            raise TileTableError(f"room {r['room']}: a one-side (scope) row needs a named non-tolerance cause")
        if acc != delta:
            raise TileTableError(f"room {r['room']}: components sum {acc} != row delta {delta}")
        if e is not None:
            eng += e
            for ec, q in classes.items():
                cls_eng[ec] = cls_eng.get(ec, Decimal(0)) + q
        if f is not None:
            fl += f
            fc = r.get("freelancer_class", "?")
            cls_fl[fc] = cls_fl.get(fc, Decimal(0)) + f
            for mv in r.get("class_moves", []):
                moves.append({"room": r["room"], **mv})
        s = by_size.setdefault(sk, {"engine": Decimal(0), "freelancer": Decimal(0)})
        s["engine"] += e or Decimal(0)
        s["freelancer"] += f or Decimal(0)
        out.append({"room": r["room"], "size": sk, "engine": None if e is None else str(e),
                    "freelancer": None if f is None else str(f), "delta": str(delta), "state": "VALUED",
                    "engine_class": "/".join(sorted(classes)) or None, "freelancer_class": r.get("freelancer_class"),
                    "components": comps, "note": r.get("note", "")})
    if index is not None:
        idx_total = sum((D(v["measured_net"]) for v in index.values()
                         if v["item_code"] in FLOOR_CODES and v["measured_net"] is not None), Decimal(0))
        if engine_total is not None and D(engine_total) != idx_total:
            raise TileTableError(f"engine total {engine_total} != candidate floor tile lines {idx_total} (stale)")
        engine_total = idx_total
    if engine_total is None:
        raise TileTableError("engine total not given and no index to compute it")
    if eng != D(engine_total):
        raise TileTableError(f"engine rows sum {eng} != candidate floor tile total {engine_total}: a line is "
                             f"missing from the table or counted twice")
    if fl != D(freelancer_total):
        raise TileTableError(f"freelancer rows sum {fl} != his printed total {freelancer_total}")
    gap = eng - fl
    assert sum(by_cause.values(), Decimal(0)) == gap
    return {"engine_total": str(eng), "freelancer_total": str(fl), "gap_engine_minus_freelancer": str(gap),
            "gap_pct_of_freelancer": f"{(gap / fl * 100):.2f}" if fl else None,
            "by_cause": {k: str(v) for k, v in sorted(by_cause.items())},
            "by_size": {k: {"engine": str(v["engine"]), "freelancer": str(v["freelancer"]),
                            "delta": str(v["engine"] - v["freelancer"])} for k, v in by_size.items()},
            "class_split_engine": {k: str(v) for k, v in sorted(cls_eng.items())},
            "class_split_freelancer": {k: str(v) for k, v in sorted(cls_fl.items())},
            "class_moves": moves, "held_lines": held_lines, "rows": out}


def missing_floor_lines(index_lines: list[dict]) -> list[dict]:
    """R-T553-1 (g): released interior ARCH.SPACE elements with a FIN.CEILING line and no floor tile line."""
    def base(e):
        return (e or "").split(":")[0]
    floors = {base(v["element_id"]) for v in index_lines if v["item_code"] in FLOOR_CODES}
    ceilings = {base(v["element_id"]) for v in index_lines if v["item_code"] == "FIN.CEILING" and v["class"] == "RELEASED"}
    out = []
    for v in index_lines:
        if v["item_code"] == "ARCH.SPACE" and v["class"] == "RELEASED":
            b = base(v["element_id"])
            if b in ceilings and b not in floors:
                out.append({"element": b, "space_line": v["line_id"], "area": v["measured_net"]})
    return out
