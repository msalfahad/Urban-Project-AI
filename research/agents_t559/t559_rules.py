"""T-559 rules (any villa; research, unwired): an opening census matched opening by opening, and the ownership check of
the concrete edge member under a parapet.

R-T559-1 (proposed, every villa; refines R-T543-1 row l 'openings census', provenance T-559):
  (a) PHYSICAL ELEMENT FIRST. A masonry deduction is one actual opening (Q-73) in one wall. The freelancer's opening
      rows carry no opening id, so his rows are matched to the engine's openings by floor, wall section and size
      class; every match is stated (consistent, not proven) and the census is closed exactly (Decimal):
        engine deductions - his deductions = sum over pairs + engine-only openings - his-only units.
  (b) PER PAIR (engine opening e with width w_e and deduction E; his unit w_h x h_h):
        E - w_h h_h = (w_e - w_h) h_h      width term  (TOLERANCE when |w_e - w_h| <= 5 mm, else UNRESOLVED)
                    + (E - w_e h_h)        height term, classed by the engine's height basis:
                                             Q55C      owner fallback door head 2.20 where none is printed (Q-55 C)
                                                       -> RULE_DIFFERENCE (his flat door height is not the rule)
                                             PRINTED   printed sill / head (or drawing-confirmed height) -> ENGINE_RIGHT
      An engine opening deducted by its TRUE OUTLINE (arched: UP-OPEN-ARCH-001) has no width / height split: the whole
      E - w_h h_h is ENGINE_RIGHT (the void is the outline, not his rectangle).
      A HELD engine opening (not deducted; its wall or height held) paired with his unit: the whole -w_h h_h is HELD
      (never 0, never agreement).
  (c) UNPAIRED: an engine opening he does not deduct (+E) or a unit of his with no engine opening (-w_h h_h) is
      UNRESOLVED (count), named by id / size; never folded into a pair.
  (d) REFUSALS: an engine opening or a unit of his used twice; a HELD opening classed other than HELD; None as a number;
      mm (a width over 20 or a height over 10 'm'); a census that does not close exactly.

R-T559-2 (proposed, every villa; the register ruling PARAPET EDGE DOWNSTAND MEMBER applied, provenance T-559):
  (a) the parapet's masonry is its printed height above the slab FINISH x its length; the drawn edge member under it
      (a beam band of the structural roof-slab plan whose plan carries the parapet line) is beam concrete b x D x L,
      owned by the B10 beam family; masonry measured from the slab soffit (or the member soffit) where a downstand is
      drawn is refused;
  (b) every structural band under a parapet run is carried by EXACTLY ONE beam line that is not EXCLUDED (RELEASED or
      HELD); zero = OMITTED (a concrete scope gap, never blockwork), two = DOUBLE (refused).
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
CAUSES = ("ENGINE_RIGHT", "ENGINE_WRONG", "RULE_DIFFERENCE", "HELD", "TOLERANCE", "UNRESOLVED")
H_BASIS = ("Q55C", "PRINTED", "OUTLINE", "HELD")
WIDTH_TOL_M = Decimal("0.005")


class RuleError(ValueError):
    pass


def D(x) -> Decimal:
    if x is None:
        raise RuleError("quantity unknown (None) used as a number: HELD / UNKNOWN is never 0")
    if isinstance(x, float):
        return Decimal(repr(x))
    return Decimal(str(x))


def _size(w, h=None, what=""):
    w = D(w)
    if w <= 0 or w > 20:
        raise RuleError(f"{what}: width {w} not a width in metres (mm?)")
    if h is not None:
        h = D(h)
        if h <= 0 or h > 10:
            raise RuleError(f"{what}: height {h} not a height in metres (mm?)")
    return w, h


def opening_census(*, floor: str, engine: list[dict], his: list[dict], pairs: list[tuple],
                   engine_census_m2, his_census_m2) -> dict:
    """engine: [{id, w_m, ded_m2 (None when HELD), h_basis in H_BASIS}]
    his: [{uid, w_m, h_m}] one record per unit (a row 'n x w x h' is n units)
    pairs: [(engine id, his uid, note)]. Returns {rows, delta}; rows sum exactly to engine_census - his_census."""
    E = {}
    for e in engine:
        if e["id"] in E:
            raise RuleError(f"{floor}: engine opening {e['id']} listed twice")
        if e["h_basis"] not in H_BASIS:
            raise RuleError(f"{floor}: {e['id']} height basis {e['h_basis']!r} not in {H_BASIS}")
        held = e["h_basis"] == "HELD"
        if held != (e.get("ded_m2") is None):
            raise RuleError(f"{floor}: {e['id']}: a HELD opening has no deduction, a deducted one is not HELD")
        if not (e["h_basis"] == "OUTLINE" and e.get("w_m") is None):   # an outline needs no width
            _size(e["w_m"], what=e["id"])
        E[e["id"]] = e
    U = {}
    for u in his:
        if u["uid"] in U:
            raise RuleError(f"{floor}: his unit {u['uid']} listed twice")
        _size(u["w_m"], u["h_m"], u["uid"])
        U[u["uid"]] = u
    used_e, used_u, rows = set(), set(), []
    for eid, uid, note in pairs:
        if eid in used_e:
            raise RuleError(f"{floor}: engine opening {eid} paired twice")
        if uid in used_u:
            raise RuleError(f"{floor}: his unit {uid} paired twice")
        if eid not in E or uid not in U:
            raise RuleError(f"{floor}: pair ({eid}, {uid}) names an unknown opening")
        used_e.add(eid)
        used_u.add(uid)
        e, u = E[eid], U[uid]
        wh, hh = _size(u["w_m"], u["h_m"])
        his_m2 = wh * hh
        name = f"{floor} {eid} vs his {wh} x {hh}"
        if e["h_basis"] == "HELD":
            rows.append({"name": name, "term": "held opening", "delta": str(-his_m2), "cause": "HELD", "note": note})
            continue
        Em = D(e["ded_m2"])
        if e["h_basis"] == "OUTLINE":
            rows.append({"name": name, "term": "true outline vs his rectangle", "delta": str(Em - his_m2),
                         "cause": "ENGINE_RIGHT", "note": note})
            continue
        we = D(e["w_m"])
        wt = (we - wh) * hh
        if wt != 0:
            rows.append({"name": name, "term": "width", "delta": str(wt),
                         "cause": "TOLERANCE" if abs(we - wh) <= WIDTH_TOL_M else "UNRESOLVED", "note": note})
        ht = Em - we * hh
        if ht != 0:
            rows.append({"name": name, "term": "height", "delta": str(ht),
                         "cause": "RULE_DIFFERENCE" if e["h_basis"] == "Q55C" else "ENGINE_RIGHT", "note": note})
    for eid, e in E.items():
        if eid in used_e or e["h_basis"] == "HELD":
            continue                                   # an unpaired HELD opening is not deducted on either side
        rows.append({"name": f"{floor} {eid} (engine deducts; no unit of his)", "term": "count",
                     "delta": str(D(e["ded_m2"])), "cause": "UNRESOLVED", "note": "engine-only opening"})
    for uid, u in U.items():
        if uid in used_u:
            continue
        rows.append({"name": f"{floor} his {u['w_m']} x {u['h_m']} (no engine opening)", "term": "count",
                     "delta": str(-D(u["w_m"]) * D(u["h_m"])), "cause": "UNRESOLVED", "note": "his-only unit"})
    eng = sum((D(e["ded_m2"]) for e in E.values() if e["h_basis"] != "HELD"), Decimal(0))
    hs = sum((D(u["w_m"]) * D(u["h_m"]) for u in U.values()), Decimal(0))
    if eng != D(engine_census_m2):
        raise RuleError(f"{floor}: engine openings sum {eng} != engine census {engine_census_m2}")
    if hs != D(his_census_m2):
        raise RuleError(f"{floor}: his units sum {hs} != his census {his_census_m2}")
    total = sum((D(r["delta"]) for r in rows), Decimal(0))
    if total != eng - hs:
        raise RuleError(f"{floor}: rows {total} do not close engine - his {eng - hs}")
    return {"floor": floor, "rows": rows, "delta": str(total), "engine_m2": str(eng), "his_m2": str(hs)}


def by_cause(rows: list[dict]) -> dict:
    out: dict[str, Decimal] = {}
    for r in rows:
        if r["cause"] not in CAUSES:
            raise RuleError(f"cause {r['cause']!r}")
        out[r["cause"]] = out.get(r["cause"], Decimal(0)) + D(r["delta"])
    return {k: str(v) for k, v in sorted(out.items())}


# ---- R-T559-2 ---------------------------------------------------------------------------------------------------
def parapet_on_edge_member(*, length_m, h_above_finish_m, edge_b_m, edge_depth_below_slab_top_m,
                           masonry_datum: str = "FINISH", downstand_drawn: bool = True) -> dict:
    """masonry = L x h above the finish; edge member concrete = L x b x D (B10 beam family)."""
    L, h = D(length_m), D(h_above_finish_m)
    b, dep = D(edge_b_m), D(edge_depth_below_slab_top_m)
    for v, n in ((L, "length"), (h, "height"), (b, "edge width"), (dep, "edge depth")):
        if v <= 0:
            raise RuleError(f"{n} must be positive")
    if L > 500 or h > 10 or b > 3 or dep > 5:
        raise RuleError("value looks like mm (metres only)")
    if masonry_datum != "FINISH":
        if downstand_drawn:
            raise RuleError(f"masonry measured from {masonry_datum} where a downstand edge member is drawn: the "
                            "member is beam concrete (B10); parapet masonry starts at the slab finish")
        raise RuleError(f"masonry datum {masonry_datum!r}: only a height above the finish is a parapet height")
    return {"masonry_m2": str(L * h), "edge_beam_m3": str(L * b * dep), "edge_owner": "B10 beam concrete"}


def edge_member_carriage(bands: list[dict], lines: list[dict]) -> list[dict]:
    """bands: [{storey, band, run, mark}]; lines: line-index records {item_code, element_id, class, line_id, ...}.
    A band is carried when exactly one STR.CONC.BEAM line that is not EXCLUDED names it (element id ends in the band
    id on that storey)."""
    out = []
    for b in bands:
        tag = f":{b['storey']}:"
        hits = [ln for ln in lines if ln["item_code"] == "STR.CONC.BEAM" and tag in ln["element_id"]
                and (ln["element_id"].split("#")[-1] == b["band"] or ln["element_id"].split(":")[-1] == b["band"])]
        live = [ln for ln in hits if ln["class"] != "EXCLUDED"]
        state = "CARRIED_ONCE" if len(live) == 1 else ("OMITTED" if not live else "DOUBLE")
        if state == "DOUBLE":
            raise RuleError(f"{b['storey']} {b['band']}: carried by {len(live)} live beam lines (double count)")
        rec = dict(b, state=state, excluded_twins=len(hits) - len(live))
        if live:
            ln = live[0]
            rec.update(line_id=ln["line_id"], line_class=ln["class"], element_id=ln["element_id"],
                       measured_m3=None if ln.get("measured_net") is None else str(ln["measured_net"]),
                       held_m3=None if ln.get("held_low") is None else f"{ln['held_low']} .. {ln['held_high']}")
        out.append(rec)
    return out


in_prec40(globals())   # T-653: every function of this module runs in a local 40-digit context
