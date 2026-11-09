"""R-T646-1 ROOF BUILD-UP LAYERS + FENCE FINISHES HELD-BLANK CENSUS (every villa; research provenance, proposed).

Every HELD-blank roof-layer line (FIN.ROOF.INSULATION / PROTECTION m2, FIN.ROOF.SCREED m3, FIN.ROOF.FINISH m2) and
fence-finish line (EXT.FENCE.FACE / PLASTER / PAINT m2) gets exactly one class, a named cause and, where the evidence
allows it, a fix row. Nothing is wired; no new rule value is introduced (register ROOF BUILD-UP LAYERS, Lead
2026-11-08 20:15: every layer over one roof uses ONE roof plan area, a difference only by a named drawn cause).

Classes:
  R_LAYER_UNPRINTED  a roof layer (insulation, a separate protection layer) printed on no sheet and given by no owner
                     rule: its EXISTENCE is not established, so the line stays HELD blank; the roof plan area it would
                     take is shown beside (never a bound, never 0)
  R_SCREED_BOUNDED   the falls screed: scope by owner rule (Q-41 'roof -> screed', own line), fall printed, outlets
                     drawn, minimum thickness t0 at the outlet unprinted (designer D-39): HELD with an AT_LEAST bound =
                     the screed above the t0 plane on the roof plan area (lowest rise model), high end OPEN
  R_ZONE_HELD        the whole zone is held (owner-parked roof, a covered ledge with no finish edge, no outlet drawn
                     so no fall can be built): blank, cause named
  F_FACE_HELD        a fence face whose geometry is not printed (undimensioned top profile, element held by the owner,
                     no height printed): blank, an at-most figure only where the drawing bounds it
  F_LAYER_HELD       a finish layer on a fence face: no sheet prints a finish and the owner's finish scope for the site
                     wall is open: HELD, at most the face; never the house facade system by default

Physical rules (generic, every villa):
  layer quantity      a layer is valued only when a drawing prints it or an owner rule establishes it; a thickness
                      only from a printed source; an unprinted thickness is refused (HELD, never a default)
  constant layer      volume = roof plan area x printed thickness
  falls screed bound  above-t0 volume over the falls outline V, outline area A, roof plan area B <= A, highest rise
                      on the removed part r_max: AT_LEAST = V - (A - B) x r_max (the removed strip can hold at most
                      its area x the largest rise); V from the lowest rise model under the printed fall
  fence layer         released only with a printed finish (or an owner scope naming the faces); else HELD at most the
                      face; a face released as 0 or a layer above its face is refused
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
CLASSES = ("R_LAYER_UNPRINTED", "R_SCREED_BOUNDED", "R_ZONE_HELD", "F_FACE_HELD", "F_LAYER_HELD")
STATUSES = ("VERIFIED", "PARTIALLY VERIFIED", "DRAWING-CONFIRMED", "ASSUMED - OWNER-APPROVED", "HELD", "UNKNOWN")
LAYERS = ("FALLS_SCREED", "SCREED", "INSULATION", "PROTECTION", "FINISH", "MEMBRANE")
B13_LAYERS = ("FALLS_SCREED", "SCREED", "INSULATION", "PROTECTION", "FINISH")   # the membrane is B8-06 (T-626)
FENCE_LAYERS = ("PLASTER", "PAINT")
Q6 = Decimal("0.000001")


class RuleError(Exception):
    pass


def D(x):
    return None if x is None else Decimal(str(x))


def q(x):
    return D(x).quantize(Q6)


def S(x):
    if x is None:
        return None
    s = format(D(x).normalize(), "f")
    return "0" if s in ("-0", "0.0") else s


def _pos(x, what):
    v = D(x)
    if v is None:
        raise RuleError(f"{what} missing (held is never 0)")
    if v <= 0:
        raise RuleError(f"{what} {v} <= 0 (held is never 0)")
    return v


def layer_quantity(layer, area_m2, printed=False, owner_rule=None, thickness_m=None, thickness_source=""):
    """the quantity a roof layer may carry: {'class','value','unit','status'}. A layer printed nowhere and given by no
    owner rule is HELD blank (its area beside). The membrane is never a B13 layer (double count with B8-06)."""
    if layer not in LAYERS:
        raise RuleError(f"unknown layer {layer!r}")
    if layer == "MEMBRANE":
        raise RuleError("MEMBRANE is the waterproofing line (B8-06): never a B13 roof-layer row")
    a = _pos(area_m2, f"{layer} roof plan area")
    if thickness_m is not None and not thickness_source:
        raise RuleError(f"{layer}: thickness {thickness_m} has no printed source: unprinted thickness refused (HELD)")
    if thickness_m is not None and D(thickness_m) > 1:
        raise RuleError(f"{layer}: thickness {thickness_m} m: mm read as m refused")
    if not printed and not owner_rule:
        return {"class": "HELD", "value": None, "beside_area_m2": q(a), "status": "UNKNOWN",
                "cause": "layer printed on no sheet and given by no owner rule"}
    status = "DRAWING-CONFIRMED" if printed else "ASSUMED - OWNER-APPROVED"
    if layer in ("FALLS_SCREED", "SCREED"):
        if thickness_m is None:
            return {"class": "HELD", "value": None, "beside_area_m2": q(a), "status": "HELD",
                    "cause": "screed scope established, thickness unprinted"}
        return {"class": "RELEASED", "value": q(a * _pos(thickness_m, "thickness")), "unit": "m3", "status": status}
    return {"class": "RELEASED", "value": q(a), "unit": "m2", "status": status}


def screed_at_least(v_above_t0, outline_m2, basis_m2, rise_max_m, fall=None, outlets=None):
    """AT_LEAST bound of the falls screed on the roof plan area basis (the part above the t0 plane only)."""
    if fall is None:
        raise RuleError("no printed fall: the falls screed cannot be bounded")
    if not outlets:
        raise RuleError("no outlet drawn: the falls screed cannot be bounded")
    v = _pos(v_above_t0, "above-t0 volume")
    a = _pos(outline_m2, "falls outline area")
    b = _pos(basis_m2, "roof plan area basis")
    r = _pos(rise_max_m, "highest rise")
    if b > a:
        raise RuleError(f"roof plan area {b} > falls outline {a}: the bound would invent screed")
    if r > 1:
        raise RuleError(f"highest rise {r} m: mm read as m refused")
    low = v - (a - b) * r
    if low <= 0:
        raise RuleError(f"bound {low} <= 0: no usable lower bound (held, never 0)")
    return q(low)


def fence_layer(face_at_most_m2, finish_printed=False, owner_scope_faces=None, face_key=None, house_system=False):
    """a fence finish layer: released only with a printed finish or an owner scope naming this face."""
    if house_system and not (finish_printed or owner_scope_faces):
        raise RuleError("house facade finish system carried to a site wall by default: refused")
    named = bool(owner_scope_faces) and face_key in owner_scope_faces
    if face_at_most_m2 is None:
        return {"class": "HELD", "held_low": None, "held_high": None, "cause": "face itself HELD"}
    f = _pos(face_at_most_m2, "face")
    if finish_printed or named:
        return {"class": "RELEASED", "measured_net": q(f)}
    return {"class": "HELD", "held_low": None, "held_high": q(f),
            "cause": "no finish printed and the owner's finish scope for the site wall open"}


def one_area(layer_area, finish_area, cause=None):
    """register ROOF BUILD-UP LAYERS: a layer's area equals the roof finish area unless a named drawn cause."""
    la, fa = D(layer_area), D(finish_area)
    if la != fa and not cause:
        raise RuleError(f"layer area {la} differs from the roof finish area {fa} with no named cause")
    return la - fa


def check_entry(e):
    if e.get("class") not in CLASSES:
        raise RuleError(f"{e.get('line_id')}: class {e.get('class')!r}")
    if not e.get("cause"):
        raise RuleError(f"{e.get('line_id')}: no named cause")
    fx = e.get("fix")
    if fx:
        a = fx["after"]
        if a["class"] == "RELEASED":
            if a.get("measured_net") is None or D(a["measured_net"]) <= 0:
                raise RuleError(f"{e['line_id']}: released as 0 / blank")
            if a.get("evidence") not in STATUSES[:4]:
                raise RuleError(f"{e['line_id']}: released without an evidence status")
        else:
            lo, hi = D(a.get("held_low")), D(a.get("held_high"))
            if lo is None and hi is None:
                raise RuleError(f"{e['line_id']}: a fix row with no bound")
            for v in (lo, hi):
                if v is not None and v <= 0:
                    raise RuleError(f"{e['line_id']}: bound {v} <= 0 (held is never 0)")
            if lo is not None and hi is not None and lo > hi:
                raise RuleError(f"{e['line_id']}: low {lo} > high {hi}")
            if a.get("measured_net") is not None:
                raise RuleError(f"{e['line_id']}: HELD with a value")
    return True


def census_counts(entries):
    by = {}
    for e in entries:
        check_entry(e)
        by[e["class"]] = by.get(e["class"], 0) + 1
    fixes = [e for e in entries if e.get("fix")]
    return {"lines": len(entries), "by_class": dict(sorted(by.items())), "fix_rows": len(fixes),
            "released_rows": sum(1 for e in fixes if e["fix"]["after"]["class"] == "RELEASED"),
            "bounded_rows": sum(1 for e in fixes if e["fix"]["after"]["class"] == "HELD"),
            "stay_held_blank": len(entries) - len(fixes)}


in_prec40(globals())   # T-653: every function of this module runs in a local 40-digit context
