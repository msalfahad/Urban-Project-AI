"""T-742 B9-05 PARAPET BLOCK WALLS, missing family draft (research only, not a method, not wired). Every villa.

R-T742-1 (masonry body of one parapet run). The physical element is the block body standing on a roof / terrace edge,
from where the masonry starts to the coping underside, over the run's centreline. Its datum (ELEMENT_REGISTER
'PARAPET EDGE DOWNSTAND MEMBER', T-550): masonry starts at the SLAB FINISH unless the drawing shows something else
below it; the edge member below the finish is beam concrete (B10), never B9. Where the keyed detail prints an RC
upstand above the slab top (a P1-type 'brick on upstand'), the masonry starts at the upstand top:
    start above finish = max(0, upstand_above_slab_top - b_edge)         (b_edge = finish minus slab top)
    block height       = h_above_finish - start - cap                     (cap = coping / RC cap under the top)
    net m2             = centreline x block height - every actual opening in full (Q-73)
A run is ONE element with ONE owner trade (ELEMENT_REGISTER 'PARAPETS ... CONCRETE vs MASONRY'):
    material BLOCK  -> this family (MAS.*), measured when every input is printed, else HELD with its interval;
    material RC     -> NOT_APPLICABLE here (STR.CONC.PARAPET, lane S); never measured in both;
    material UNKEYED-> HELD: interval 0 (the RC reading) .. the block reading; the designer item is named; never 0.
An unprinted height, upstand, cap or b_edge is never defaulted: it enters as a HELD interval (lo, hi) or the line is
HELD blank. Block count for procurement is separate from net m2 and applies only to a block type whose count is
owner-confirmed (black block 12.5 per m2, Q-75 / Q-80); any other or unkeyed type: procurement HELD.

R-T742-2 (one physical run, two trades: length reconciliation). The exterior finish measures the OUTER arris length,
the masonry the CENTRELINE. For a straight run of thickness t, outer - centreline = (outer - inner) / 2, which is
+t/2 per convex corner end and -t/2 per concave corner end; summed over a chain the faces and the masonry close
exactly, so a corner is counted once in each trade (centreline vertices are shared) and the two lengths never agree
by number: the difference is the corner term, named, not a residual.

R-T742-3 (census status of a run on the plan that draws the roof). DRAWN when entities on the outer and the inner
arris lines cover the run (to the tolerance); PARTLY_DRAWN with the drawn lengths when not; NOT_ON_ROOF_PLAN when the
outline side carries no entity there (the roof plan draws another profile: the run's length and thickness stay what
the merged ledger holds, the difference is named, never silently replaced).
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

RULE = "R-T742-1..3 1.0.0"
Q6 = Decimal("0.000001")
BLACK_BLOCKS_PER_M2 = Decimal("12.5")       # Q-75 / Q-80 (owner 2026-11-07), 40 x 20 face, 20 cm and 15 cm


class RuleError(ValueError):
    pass


def D(x) -> Decimal:
    if x is None:
        raise RuleError("missing value (never defaulted, never 0)")
    if isinstance(x, float):
        raise RuleError("floats are refused: pass str / int / Decimal (units in metres)")
    return Decimal(str(x))


def q(x: Decimal) -> Decimal:
    return x.quantize(Q6, rounding=ROUND_HALF_UP)


def interval(v, name):
    """A printed value 'x', or a HELD interval (lo, hi). Metres only: a value above 50 is refused as millimetres."""
    if v is None:
        raise RuleError(f"{name}: missing (HELD needs an interval, never a default)")
    lo, hi = (D(v[0]), D(v[1])) if isinstance(v, (tuple, list)) else (D(v), D(v))
    if lo > hi or lo < 0:
        raise RuleError(f"{name}: bad interval {lo} .. {hi}")
    if hi > 50:
        raise RuleError(f"{name}: {hi} looks like millimetres; pass metres")
    return lo, hi


def block_body(run: dict) -> dict:
    """R-T742-1 for one run. run keys: id, centreline_m, h_above_finish_m, t_m, material (BLOCK / RC / UNKEYED),
    upstand_above_slab_top_m (None = no upstand printed in the keyed detail), b_edge_m, cap_m, openings_m2 (list),
    designer_item (required when anything is HELD). Values: str / Decimal, or (lo, hi) for a HELD interval."""
    rid = run.get("id") or "?"
    mat = run.get("material")
    if mat not in ("BLOCK", "RC", "UNKEYED"):
        raise RuleError(f"{rid}: material must be BLOCK, RC or UNKEYED (got {mat!r})")
    if mat == "RC":
        return {"id": rid, "status": "NOT_APPLICABLE", "owner_trade": "STR.CONC.PARAPET (lane S)",
                "net_m2": None, "m3": None, "note": "one element, one trade: the RC run is concrete, never B9"}
    L = interval(run.get("centreline_m"), f"{rid} centreline")
    h = interval(run.get("h_above_finish_m"), f"{rid} height above finish")
    t = interval(run.get("t_m"), f"{rid} thickness")
    cap = interval(run.get("cap_m"), f"{rid} cap")
    up = run.get("upstand_above_slab_top_m")
    if up is None:
        s_lo = s_hi = Decimal(0)
    else:
        u = interval(up, f"{rid} upstand")
        b = interval(run.get("b_edge_m"), f"{rid} b_edge")
        s_lo, s_hi = max(Decimal(0), u[0] - b[1]), max(Decimal(0), u[1] - b[0])
    hb_lo, hb_hi = h[0] - s_hi - cap[1], h[1] - s_lo - cap[0]
    if hb_hi <= 0:
        raise RuleError(f"{rid}: no masonry above the upstand / under the cap (check the datum)")
    hb_lo = max(Decimal(0), hb_lo)
    op = sum((D(x) for x in run.get("openings_m2") or []), Decimal(0))
    gross_lo, gross_hi = L[0] * hb_lo, L[1] * hb_hi
    if op > gross_lo and mat == "BLOCK" and (L[0], h[0]) == (L[1], h[1]):
        raise RuleError(f"{rid}: openings {op} exceed the gross face")
    net_lo, net_hi = max(Decimal(0), gross_lo - op), gross_hi - op
    held = not (net_lo == net_hi and mat == "BLOCK")
    if held and not run.get("designer_item"):
        raise RuleError(f"{rid}: HELD without a named designer item / cause")
    if mat == "UNKEYED":
        net_lo = Decimal(0)                       # the RC reading of the same element
    out = {"id": rid, "owner_trade": "MAS.BLOCK (B9-05)", "status": "HELD" if held else "MEASURED",
           "net_m2": (q(net_lo), q(net_hi)), "m3": (q(net_lo * t[0]), q(net_hi * t[1])),
           "block_height_m": (q(hb_lo), q(hb_hi)), "designer_item": run.get("designer_item")}
    out["procurement_blocks"] = procurement(run.get("block_type"), out["net_m2"], held)
    return out


def procurement(block_type, net_m2, held):
    """Block count = net m2 x owner count; waste separate. Only black block has an owner-confirmed count."""
    if block_type != "BLACK":
        return {"status": "HELD", "cause": "block type not keyed or no owner-confirmed count (Q-65 C)"}
    lo, hi = net_m2
    return {"status": "HELD" if held else "MEASURED", "per_m2": str(BLACK_BLOCKS_PER_M2),
            "count": (q(lo * BLACK_BLOCKS_PER_M2), q(hi * BLACK_BLOCKS_PER_M2)), "waste": "separate"}


def family_line(chain: str, runs: list[dict]) -> dict:
    """One B9-05 line per roof chain: the runs summed (each run once), status the weakest of its runs."""
    rows = [block_body(r) for r in runs]
    ids = [r["id"] for r in rows]
    if len(set(ids)) != len(ids):
        raise RuleError(f"{chain}: a run is listed twice")
    live = [r for r in rows if r["status"] != "NOT_APPLICABLE"]
    if not live:
        return {"chain": chain, "status": "NOT_APPLICABLE", "runs": rows, "net_m2": None, "m3": None}
    lo = sum((r["net_m2"][0] for r in live), Decimal(0))
    hi = sum((r["net_m2"][1] for r in live), Decimal(0))
    m3 = (sum((r["m3"][0] for r in live), Decimal(0)), sum((r["m3"][1] for r in live), Decimal(0)))
    st = "MEASURED" if all(r["status"] == "MEASURED" for r in live) else "HELD"
    return {"chain": chain, "status": st, "runs": rows, "net_m2": (q(lo), q(hi)), "m3": (q(m3[0]), q(m3[1]))}


def corner_term(outer_m, inner_m) -> Decimal:
    """R-T742-2: outer arris minus centreline of a straight run = (outer - inner) / 2."""
    return q((D(outer_m) - D(inner_m)) / 2)


def reconcile_lengths(runs: list[dict], face_length_m) -> dict:
    """R-T742-2 over a chain: centreline = (outer + inner) / 2 per run; the face trade's outer length must equal
    sum(outer); the masonry centreline differs from it by the named corner term only. runs: outer_m, inner_m."""
    So = sum((D(r["outer_m"]) for r in runs), Decimal(0))
    Sc = sum(((D(r["outer_m"]) + D(r["inner_m"])) / 2 for r in runs), Decimal(0))
    corner = sum((corner_term(r["outer_m"], r["inner_m"]) for r in runs), Decimal(0))
    face = D(face_length_m)
    return {"outer_sum_m": q(So), "centreline_sum_m": q(Sc), "corner_term_m": q(corner),
            "face_length_m": q(face), "face_vs_outer_m": q(face - So),
            "face_vs_centreline_m": q(face - Sc), "closes": abs(face - So) <= Decimal("0.01")
            and abs((face - Sc) - corner) <= Decimal("0.01")}


def census_status(outer_line_m, outer_drawn_m, inner_drawn_m, inner_expected_m, tol="0.005") -> str:
    """R-T742-3."""
    tl = D(tol)
    if D(outer_drawn_m) == 0 and D(inner_drawn_m) == 0:
        return "NOT_ON_ROOF_PLAN"
    if D(outer_drawn_m) == 0:
        return "NOT_ON_ROOF_PLAN (outer)"
    if D(outer_line_m) - D(outer_drawn_m) <= tl and D(inner_drawn_m) >= D(inner_expected_m) - tl:
        return "DRAWN"
    return "PARTLY_DRAWN"
