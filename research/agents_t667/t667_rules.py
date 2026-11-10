"""T-667 rules (research, unwired): the blinding (plain concrete) under a swimming pool, and its held steps, for any villa.

The physical element (ERS s.2.1): a pool detail draws, under the RC base, from the base down: protection screed,
membrane, then the plain-concrete blinding; screed and membrane also run up the outer wall faces and stand on the
blinding. So the blinding covers at least the base's outer footprint GROWN by the printed thickness of the layers that
wrap the outer wall face (screed + membrane). Any further projection beyond those layers is a separate dimension.

R-T667-1 PLAN OF THE POOL BLINDING. core = the outer footprint of the RC base (the outline the walls stand on, never the
    water outline); apron = that footprint grown by the printed wrap (sum of the printed layer thicknesses on the outer
    wall face), mitred at straight corners, true offset along arcs:
        grown = A + P d + n_corners d^2 + (arc_turn / 2) d^2       (convex outline; arc_turn in radians)
    A further projection p beyond the wrap is added only when printed; when the detail draws it but does not
    dimension it, the line is LOWER_ONLY: the grown plan is the drawn minimum, the upper end stays open (named item).
R-T667-2 FLOOR PROFILE BEFORE AREA. A flat base (or an owner decision setting the drawn slope aside) takes the plan
    area. A sloped base takes width x the TRUE length of each section segment, sqrt(h^2 + v^2); every segment needs its
    printed horizontal length AND drop, the horizontals must close on the plan length; a segment with no printed drop
    ('AS PER ARCH', missing) holds the line (HELD, never the plan area as a stand-in, never 0).
R-T667-3 THE PLOT LINE. A pool edge that lies on the plot line (the back wall is the boundary wall) carries no apron
    inside the plot; the strip beyond it (edge + its mitred end squares) x d is reported separately, existence open
    (whether anything is cast beyond the plot line is the same designer item as other blinding there, D-14), never
    folded into the in-plot figure and never 0 by default.
R-T667-4 ONE ELEMENT ONCE, BY LAYER. Where another blinding layer already counted (footing pits grown by their
    projection) shares plan with the pool blinding and the founding levels are not printed, the two readings are kept
    side by side and never merged silently: plan-distinct (one layer in plan: pool net of the counted layer; the
    lower end) and own layer (both cast, at different levels: the gross pool plan). The counted line is never changed
    by the pool line. A clash of the footing OUTLINE itself with the pool (concrete in the pool's formation) is a
    designer interface, reported in m2.
R-T667-5 STEPS ONLY WHEN DRAWN. Pool steps, benches or a ladder recess are concrete only where a drawing dimensions
    them; none drawn -> the steps line stays HELD blank with the item named (never 0, never a freelancer or typical
    size).

Provenance: T-667 (2026-11-10), Alsenan development villa (ST p.7 '5cm SECREED / 5cm INSULATION MEMBRANE / 10cm PLAIN
CONCRETE', owner Q-26 A flat floor), on T-183 (R-POOL-3, R-POOL-5), T-445 / T-478 (mitred projection, merged vs own
layer), T-597 (pool envelope 11.851050 m2, Checker re-measured), T-659 (R-T659-1 .. 5). Scope: every villa.
"""
from __future__ import annotations

import math
from decimal import Decimal, ROUND_HALF_UP

Q6 = Decimal("0.000001")
PI = Decimal(str(math.pi))
UNPRINTED = ("AS PER ARCH", "SEE ARCH", "AS PER SCHEDULE", "NOT PRINTED", "N.I.S")
REFUSED_BASIS = ("GENERIC", "DEFAULT", "ASSUMED", "BORROWED", "FREELANCER", "TYPICAL VALUE")
MAX_M = Decimal("100")


class Refused(ValueError):
    """A reading the rules refuse (the caller carries the quantity HELD with its item)."""


def q6(x) -> Decimal:
    return Decimal(x).quantize(Q6, rounding=ROUND_HALF_UP)


def dim(x, source: str, *, allow_zero: bool = False) -> Decimal:
    """A printed dimension in metres with its source."""
    if x is None:
        raise Refused("missing value: HELD with its item, never 0")
    if not source or not str(source).strip():
        raise Refused("a dimension without its printed source")
    up = str(source).upper()
    if any(m in up for m in UNPRINTED):
        raise Refused(f"not a printed figure: {source}")
    if any(b in up for b in REFUSED_BASIS):
        raise Refused(f"refused basis: {source}")
    if isinstance(x, bool):
        raise Refused("not a quantity")
    if isinstance(x, str) and x.strip().lower().endswith(("mm", "cm", "%")):
        raise Refused("metres only")
    v = Decimal(str(x))
    if v < 0 or (v == 0 and not allow_zero):
        raise Refused("a zero or negative dimension")
    if v > MAX_M:
        raise Refused(f"{v} m is not a pool dimension (mm slip?)")
    return v


# ---- outlines (analytic, convex) ------------------------------------------------------------------------------------
def outline(kind: str, **d) -> dict:
    """Outer footprint of the RC base. 'rect': L, W. 'D': r (half circle), b (straight depth behind the circle's
    diameter), back = 2r. Returns area, perimeter, mitred straight corners, arc turning (rad), named edges."""
    if kind == "rect":
        L, W = d["L"], d["W"]
        return {"kind": kind, "A": L * W, "P": 2 * (L + W), "n_corners": 4, "arc_turn": Decimal(0),
                "edges": {"L1": L, "L2": L, "W1": W, "W2": W}}
    if kind == "D":
        r, b = d["r"], d["b"]
        return {"kind": kind, "A": 2 * r * b + PI * r * r / 2, "P": 2 * r + 2 * b + PI * r, "n_corners": 2,
                "arc_turn": PI, "edges": {"back": 2 * r, "side1": b, "side2": b, "arc": PI * r}}
    raise Refused(f"outline kind {kind}: measure it from the drawn polygon")


def grown(o: dict, d: Decimal) -> Decimal:
    """R-T667-1: convex outline grown by d (mitred corners, true offset along arcs)."""
    return o["A"] + o["P"] * d + o["n_corners"] * d * d + o["arc_turn"] / 2 * d * d


def wrap(layers) -> Decimal:
    """The printed layers on the outer wall face that stand on the blinding: [(name, t, source), ...]."""
    if not layers:
        raise Refused("no wrap layers printed: the apron is not established")
    return sum((dim(t, s) for _n, t, s in layers), Decimal(0))


def beyond_plot(o: dict, edges_on_plot, d: Decimal) -> Decimal:
    """R-T667-3: strip beyond the plot line for each straight edge on it (edge + 2 mitred end squares) x d."""
    tot = Decimal(0)
    for e in edges_on_plot:
        if e not in o["edges"] or e == "arc":
            raise Refused(f"edge {e} is not a straight edge of the outline")
        tot += (o["edges"][e] + 2 * d) * d
    return tot


def core_area(o: dict, floor: dict) -> tuple[Decimal, str]:
    """R-T667-2: the area under the base: plan for a flat floor; true sloped length x width for a sloped one."""
    kind = floor.get("kind")
    if kind == "flat":
        return o["A"], floor.get("basis", "flat floor")
    if kind == "sloped":
        if o["kind"] != "rect":
            raise Refused("a sloped floor is measured on a rectangular outline with the section along L")
        segs = floor.get("segments") or []
        if not segs:
            raise Refused("sloped floor without its section segments")
        h_sum, true_len = Decimal(0), Decimal(0)
        for h, v, src in segs:
            hh = dim(h, src)
            if v is None:
                raise Refused("segment drop not printed: the sloped blinding stays HELD")
            vv = dim(v, src, allow_zero=True)
            h_sum += hh
            true_len += Decimal(str(math.sqrt(float(hh * hh + vv * vv))))
        if abs(h_sum - o["edges"]["L1"]) > Decimal("0.001"):
            raise Refused(f"section horizontals {h_sum} do not close on the plan length {o['edges']['L1']}")
        # the sloped core replaces the plan core over the outline; the apron stays a plan strip
        return o["edges"]["W1"] * true_len, "sloped: W x sum of true segment lengths"
    raise Refused("floor profile not established: HELD")


def pool_blinding(o: dict, t: Decimal, layers, floor: dict, *, edges_on_plot=(), projection=None,
                  counted_overlap_m2=None, counted_line=None, outline_clash_m2=None) -> dict:
    """The pool blinding ledger piece (m2 and m3, 6 dp) under R-T667-1 .. 4."""
    d = wrap(layers)
    core, core_basis = core_area(o, floor)
    apron_all = grown(o, d) - o["A"]
    out_strip = beyond_plot(o, edges_on_plot, d)
    apron_in = apron_all - out_strip
    if apron_in < 0:
        raise Refused("apron inside the plot negative: edges on the plot line overstated")
    plan_in = core + apron_in
    res = {"wrap_d_m": str(q6(d)), "core_m2": str(q6(core)), "core_basis": core_basis,
           "apron_in_plot_m2": str(q6(apron_in)), "own_layer_in_plot_m2": str(q6(plan_in)),
           "own_layer_in_plot_m3": str(q6(plan_in * t)), "beyond_plot_m2": str(q6(out_strip)),
           "beyond_plot_m3": str(q6(out_strip * t)), "t_m": str(q6(t))}
    if counted_overlap_m2 is not None:
        ov = Decimal(str(counted_overlap_m2))
        if ov < 0 or ov > plan_in:
            raise Refused("overlap with the counted layer outside 0 .. the pool plan")
        if not counted_line:
            raise Refused("an overlap names the counted line it is netted against (R-T667-4)")
        res.update({"counted_line": counted_line, "counted_overlap_m2": str(q6(ov)),
                    "plan_distinct_m2": str(q6(plan_in - ov)), "plan_distinct_m3": str(q6((plan_in - ov) * t))})
    if outline_clash_m2 is not None:
        res["footing_outline_clash_m2"] = str(q6(Decimal(str(outline_clash_m2))))
    if projection is None:
        res["status"] = "LOWER_ONLY"
        res["open_item"] = "projection of the blinding beyond the wrap layers drawn but not dimensioned"
    else:
        p = dim(projection[0], projection[1])
        extra = grown(o, d + p) - grown(o, d) - (beyond_plot(o, edges_on_plot, d + p) - out_strip)
        res["status"] = "VALUED_GEOMETRY"
        res["projection_m"] = str(q6(p))
        res["own_layer_in_plot_m3"] = str(q6((plan_in + extra) * t))
        res["own_layer_in_plot_m2"] = str(q6(plan_in + extra))
        if "plan_distinct_m2" in res:
            res["plan_distinct_note"] = "the counted overlap was measured at the wrap growth; re-measure at d + p"
    return res


def steps_line(drawn_steps) -> dict:
    """R-T667-5: concrete only for drawn and dimensioned steps."""
    if not drawn_steps:
        return {"status": "HELD_BLANK", "value": None,
                "item": "no step drawn or dimensioned on the pool detail, plan or section: designer item (access to "
                        "the water)"}
    tot = Decimal(0)
    for s in drawn_steps:
        tot += dim(s["L"], s["source"]) * dim(s["W"], s["source"]) * dim(s["H"], s["source"])
    return {"status": "VALUED", "value": str(q6(tot)), "item": None}
