"""T-568 rules (any villa; research, unwired): doors and windows reconciled against a reference takeoff BY TYPE, count
(nr) and opening area (m2) kept apart, every opening once by id.

R-T568-1 (proposed, every villa; provenance T-568; refines R-T559-1 for supply lines):
  (a) PHYSICAL ELEMENT FIRST. One opening = one id on ONE storey, with a type class (DOOR.EXTERNAL.ALUMINIUM,
      DOOR.INTERNAL.PVC, DOOR.MAIN_ENTRANCE, WINDOW.ALUMINIUM, ...), a width and an opening area with its basis:
        PRINTED / DRAWING_CONFIRMED  a printed or drawing-confirmed width x height
        Q32A                         arched: the enclosing rectangle to the top of the OPENING arch (owner Q-32 A)
        Q76A                         the curved 1F window over the pool, 3.29 x 3.00 (owner Q-76 A; band is wall)
        Q55C                         door width x the owner fallback height 2.20 (ASSUMED - OWNER-APPROVED, Q-55 C)
        HELD                         no area (count may be settled or a range); bounds beside, never 0
      The same id read on two plans (a plan and an elevation, a floor plan and the stair sheet) is ONE opening when the
      storey agrees, and is refused when the storeys differ (counted on two storeys).
  (b) TYPE TABLE. Per class and unit separately: ours (settled, HELD count / bounds), his, his - ours. nr and m2 are
      never mixed: a comparison that asks for an m2 key from nr values (or the reverse) is refused.
  (c) CAUSES (signed, his minus ours never; we report ours minus his, as R-T559-1) closing EXACTLY per class and unit:
        pair, both settled:   E - n_h w_h h_h split per unit into width (w_e - w_h) h_h and height E - w_e h_h;
                              width: TOLERANCE <= 5 mm, else the pair's stated verdict (default UNRESOLVED);
                              height: Q55C -> RULE_DIFFERENCE; PRINTED / DRAWING_CONFIRMED / Q32A / Q76A -> ENGINE_RIGHT
        pair, ours HELD:      - w_h h_h  HELD (nr: 0, the count is HELD when ours is a range)
        ours only (unpaired): + E (m2) and + 1 (nr), classed by its own evidence verdict (ENGINE_RIGHT only when the
                              drawn leaf / glazing is read independently; else UNRESOLVED)
        his only:             - w_h h_h and - 1, UNRESOLVED
  (d) PAIRING INVARIANCE. His rows carry no id, so a pairing is a stated, consistent match, not proof. The class total
      ours - his does not depend on the pairing; a different pairing only moves m2 between width and count terms of
      the same class. When two pairings are consistent, both are run and the move is reported by name, never a residual.
  (e) REFUSALS: an id twice on two storeys; a unit of his used twice; a row whose n x w x h does not equal its printed
      m2; a HELD opening with an area or a settled one without; None as a number; mm as metres; a class that does not
      close exactly.
"""
from __future__ import annotations

import functools
import inspect
import types
from decimal import Context, Decimal, localcontext

# T-653 (F-T648-2): 40 digits are used only INSIDE this module's functions, through a local Decimal context; importing
# this module never changes the process-global context (it used to set getcontext().prec = 40 at import, which changed
# every later Decimal result in the same process). in_prec40() at the end of the module applies the local context.
PREC = 40


def ctx40():
    """a local 40-digit Decimal context: `with ctx40(): ...`; the caller's context is restored on exit."""
    return localcontext(Context(prec=PREC))


def in_prec40(namespace: dict) -> None:
    """run every plain function DEFINED in the module of `namespace` (its globals()) inside ctx40(); generator
    functions, classes and names imported from other modules are left as they are. Marks each wrapper
    `_t653_prec40 = True`. Called once, at the end of the module (here and in its builder)."""
    mod = namespace["__name__"]
    for name, fn in list(namespace.items()):
        if (isinstance(fn, types.FunctionType) and fn.__module__ == mod and not getattr(fn, "_t653_prec40", False)
                and not inspect.isgeneratorfunction(fn) and name not in ("ctx40", "in_prec40")):
            namespace[name] = _wrap40(fn)


def _wrap40(fn):
    @functools.wraps(fn)
    def run40(*args, **kwargs):
        with ctx40():
            return fn(*args, **kwargs)
    run40._t653_prec40 = True
    return run40
BASES = ("PRINTED", "DRAWING_CONFIRMED", "Q32A", "Q76A", "Q55C", "HELD")
CAUSES = ("ENGINE_RIGHT", "ENGINE_WRONG", "RULE_DIFFERENCE", "HELD", "TOLERANCE", "UNRESOLVED", "AGREE")
UNITS = ("nr", "m2")
WIDTH_TOL_M = Decimal("0.005")


class RuleError(ValueError):
    pass


def D(x) -> Decimal:
    if x is None:
        raise RuleError("quantity unknown (None) used as a number: HELD / UNKNOWN is never 0")
    if isinstance(x, float):
        return Decimal(repr(x))
    return Decimal(str(x))


def _m(v, what, hi):
    v = D(v)
    if v <= 0 or v > hi:
        raise RuleError(f"{what}: {v} is not a size in metres (mm?)")
    return v


def openings_once(records: list[dict]) -> dict:
    """records: [{id, storey, cls, w_m, area_m2 (None = HELD), basis, source}] possibly the same id read on several
    plans. Returns {id: record} with one record per id; refuses an id on two storeys or with differing sizes."""
    out: dict[str, dict] = {}
    for r in records:
        if r["basis"] not in BASES:
            raise RuleError(f"{r['id']}: area basis {r['basis']!r} not in {BASES}")
        held = r["basis"] == "HELD"
        if held != (r.get("area_m2") is None):
            raise RuleError(f"{r['id']}: a HELD opening has no area, a settled one has an area")
        if r.get("w_m") is not None:
            _m(r["w_m"], f"{r['id']} width", 20)
        if not held:
            _m(r["area_m2"], f"{r['id']} area", 200)
        prev = out.get(r["id"])
        if prev is None:
            out[r["id"]] = dict(r, sources=[r.get("source", "")])
            continue
        if prev["storey"] != r["storey"]:
            raise RuleError(f"{r['id']}: counted on two storeys ({prev['storey']} and {r['storey']})")
        for k in ("cls", "w_m", "area_m2", "basis"):
            if prev.get(k) != r.get(k):
                raise RuleError(f"{r['id']}: two readings differ on {k} ({prev.get(k)} vs {r.get(k)})")
        prev["sources"].append(r.get("source", ""))
    return out


def his_units(rows: list[dict]) -> list[dict]:
    """rows: [{row, storey, cls, n, w_m, h_m, m2}] -> one unit per counted piece; n x w x h must equal m2."""
    units = []
    for r in rows:
        n = D(r["n"])
        if n != n.to_integral_value() or n <= 0:
            raise RuleError(f"his row {r['row']}: count {n} is not a whole number of pieces")
        w, h = _m(r["w_m"], f"his row {r['row']} width", 20), _m(r["h_m"], f"his row {r['row']} height", 10)
        if n * w * h != D(r["m2"]):
            raise RuleError(f"his row {r['row']}: {n} x {w} x {h} != printed {r['m2']}")
        for i in range(int(n)):
            units.append({"uid": f"{r['row']}#{i + 1}", "row": r["row"], "storey": r["storey"], "cls": r["cls"],
                          "w_m": w, "h_m": h})
    return units


def type_table(*, openings: dict, units: list[dict], pairs: list[tuple], verdicts: dict | None = None) -> dict:
    """openings: openings_once() output; units: his_units() output; pairs: [(opening id, his row, note)] each
    consuming the next free unit of that row; verdicts: {opening id: {"count": cause, "width": cause}} for unpaired
    ours and width terms (default UNRESOLVED). Returns {cls: {"nr": {...}, "m2": {...}, "rows": [...]}}."""
    verdicts = verdicts or {}
    free: dict[str, list[dict]] = {}
    for u in units:
        free.setdefault(u["row"], []).append(u)
    used_o: set[str] = set()
    rows: list[dict] = []

    def add(cls, unit, term, delta, cause, name, note=""):
        if unit not in UNITS:
            raise RuleError(f"unit {unit!r}")
        if cause not in CAUSES:
            raise RuleError(f"cause {cause!r}")
        if delta != 0 or cause in ("HELD",):
            rows.append({"cls": cls, "unit": unit, "term": term, "delta": str(delta), "cause": cause, "name": name,
                         "note": note})

    for oid, row, note in pairs:
        if oid in used_o:
            raise RuleError(f"opening {oid} paired twice")
        if oid not in openings:
            raise RuleError(f"pair names unknown opening {oid}")
        if not free.get(row):
            raise RuleError(f"his row {row}: no free unit left for {oid} (a unit used twice)")
        o, u = openings[oid], free[row].pop(0)
        if o["cls"] != u["cls"]:
            raise RuleError(f"{oid} ({o['cls']}) paired with his row {row} ({u['cls']}): classes differ")
        if u["storey"] is not None and o["storey"] != u["storey"]:
            raise RuleError(f"{oid} ({o['storey']}) paired with his row {row} on {u['storey']}")
        used_o.add(oid)
        cls, wh, hh = o["cls"], u["w_m"], u["h_m"]
        his = wh * hh
        name = f"{o['storey']} {oid} vs his {wh} x {hh}"
        if o["basis"] == "HELD":
            add(cls, "m2", "ours HELD", -his, "HELD", name, note)
            if o.get("count_held"):
                add(cls, "nr", "count HELD", Decimal(-1), "HELD", name, note)
            continue
        E = D(o["area_m2"])
        if E == his and (o.get("w_m") is None or D(o["w_m"]) == wh):
            add(cls, "m2", "equal", Decimal(0), "AGREE", name, note)
            continue
        we = D(o["w_m"]) if o.get("w_m") is not None else None
        if we is None:
            raise RuleError(f"{oid}: a settled opening needs its width for the width / height split")
        wt = (we - wh) * hh
        if wt != 0:
            wc = "TOLERANCE" if abs(we - wh) <= WIDTH_TOL_M else verdicts.get(oid, {}).get("width", "UNRESOLVED")
            add(cls, "m2", "width", wt, wc, name, note)
        ht = E - we * hh
        if ht != 0:
            add(cls, "m2", "height", ht, "RULE_DIFFERENCE" if o["basis"] == "Q55C" else "ENGINE_RIGHT", name, note)
    for oid, o in openings.items():
        if oid in used_o:
            continue
        cause = verdicts.get(oid, {}).get("count", "UNRESOLVED")
        nm = f"{o['storey']} {oid} (no unit of his)"
        if o.get("count_held"):
            add(o["cls"], "nr", "ours only, count HELD", Decimal(0), "HELD", nm)
        else:
            add(o["cls"], "nr", "ours only", Decimal(1), cause, nm)
        if o["basis"] == "HELD":
            add(o["cls"], "m2", "ours only, area HELD", Decimal(0), "HELD", nm)
        else:
            add(o["cls"], "m2", "ours only", D(o["area_m2"]), cause, nm)
    for row, left in free.items():
        for u in left:
            add(u["cls"], "nr", "his only", Decimal(-1), "UNRESOLVED", f"{u['storey']} his {u['w_m']} x {u['h_m']}")
            add(u["cls"], "m2", "his only", -u["w_m"] * u["h_m"], "UNRESOLVED",
                f"{u['storey']} his {u['w_m']} x {u['h_m']}")

    classes = sorted({o["cls"] for o in openings.values()} | {u["cls"] for u in units})
    out = {}
    for cls in classes:
        os_ = [o for o in openings.values() if o["cls"] == cls]
        us = [u for u in units if u["cls"] == cls]
        settled = [o for o in os_ if o["basis"] != "HELD"]
        nr_ours = sum(1 for o in os_ if not o.get("count_held"))
        nr_held = [o["id"] for o in os_ if o.get("count_held")]
        m2_ours = sum((D(o["area_m2"]) for o in settled), Decimal(0))
        m2_his = sum((u["w_m"] * u["h_m"] for u in us), Decimal(0))
        crow = [r for r in rows if r["cls"] == cls]
        rec = {"nr": {"ours_settled": nr_ours, "ours_count_held": nr_held, "his": len(us),
                      "ours_minus_his": nr_ours - len(us)},
               "m2": {"ours_settled": str(m2_ours), "ours_held": [o["id"] for o in os_ if o["basis"] == "HELD"],
                      "ours_held_bounds": {o["id"]: o.get("bounds") for o in os_ if o["basis"] == "HELD"},
                      "his": str(m2_his), "ours_minus_his": str(m2_ours - m2_his)},
               "rows": crow}
        # closure, unit by unit (nr: HELD-count openings are outside ours_settled and carry 0 rows)
        nsum = sum((D(r["delta"]) for r in crow if r["unit"] == "nr"), Decimal(0))
        msum = sum((D(r["delta"]) for r in crow if r["unit"] == "m2"), Decimal(0))
        if nsum != D(nr_ours - len(us)):
            raise RuleError(f"{cls}: nr causes {nsum} do not close ours - his {nr_ours - len(us)}")
        if msum != m2_ours - m2_his:
            raise RuleError(f"{cls}: m2 causes {msum} do not close ours - his {m2_ours - m2_his}")
        rec["nr"]["by_cause"] = by_cause(crow, "nr")
        rec["m2"]["by_cause"] = by_cause(crow, "m2")
        out[cls] = rec
    return out


def by_cause(rows: list[dict], unit: str) -> dict:
    out: dict[str, Decimal] = {}
    for r in rows:
        if r["unit"] != unit:
            continue
        out[r["cause"]] = out.get(r["cause"], Decimal(0)) + D(r["delta"])
    return {k: str(v) for k, v in sorted(out.items())}


def compare(table: dict, cls: str, unit: str, value_unit: str) -> dict:
    """The only way to read a comparison out of a type table: unit must match the value's unit (nr never m2)."""
    if unit not in UNITS or value_unit not in UNITS:
        raise RuleError(f"unit {unit!r} / {value_unit!r}")
    if unit != value_unit:
        raise RuleError(f"{cls}: an {value_unit} value compared as {unit}: nr and m2 are never mixed")
    return table[cls][unit]


def pairing_move(t_a: dict, t_b: dict, cls: str) -> dict:
    """R-T568-1 (d): two consistent pairings give the same class totals; return the per-cause move in m2 and nr."""
    for u in UNITS:
        if t_a[cls][u]["ours_minus_his"] != t_b[cls][u]["ours_minus_his"]:
            raise RuleError(f"{cls} {u}: two pairings change the class total (a pairing must not change it)")
    move = {}
    for u in UNITS:
        a, b = t_a[cls][u]["by_cause"], t_b[cls][u]["by_cause"]
        move[u] = {k: str(D(b.get(k, 0)) - D(a.get(k, 0))) for k in sorted(set(a) | set(b))
                   if D(b.get(k, 0)) != D(a.get(k, 0))}
    return move


in_prec40(globals())   # T-653: every function of this module runs in a local 40-digit context
