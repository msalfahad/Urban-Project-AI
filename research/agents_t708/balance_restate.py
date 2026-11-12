"""T-708 (lane S, research, unwired, stdlib only, pure, every villa): two tools over numbers only (no drawing access).
Not a method version: the balance itself stays DISPOSAL_BALANCE_V2 (R-T505-1, research/agents_t505, called unchanged).

1. reconcile_plan_x_depth (rule R-T708-1, PROPOSED): the owner manual method for a placed-fill zone (one plan x one
   depth) against the drawing-derived zone measured per plan column (R-T700-1), TERM BY TERM. Every engine term is
   one drawn element (a slab panel = one candidate ground-slab line, a ground-beam run). For each term i and each end
   (low / high):

       owner_i  = A_i x d_owner        for a term inside the owner plan (a slab panel)
                = 0                    for a term outside it (a beam column under a ground beam; its blinding
                                       projections, negative where they occupy panel fill)
       delta_i  = engine_i - owner_i   = A_i x (d_i - d_owner) for a panel
       cause_i  = the drawn element / printed level that makes d_i differ (named per term, never "other")

   Closure: sum(owner_i) + sum(delta_i) = engine zone end, at each end; the residual is reported and must not exceed
   the rounding of the terms (n_terms x 0.5e-6 m3 + the owner total's own rounding); a larger residual REFUSES (an
   unexplained difference is never absorbed). The owner figure is shown beside, never chosen because it is larger.

2. restate_terms (rule R-T708-2, PROPOSED): the terms of the B1-04 disposal / import balance from a wiring form
   (one row per candidate earthworks line, UP-QTY-STATUS-001 bound classes) instead of the candidate's own states:
       VALUE            closed term low = high = value, status of its source
       RANGE            closed term low .. high (an envelope of admissible readings), status = worst of its sources
       ZERO_BY_GEOMETRY closed term 0 .. 0, status CALCULATED (its geometric proof named)
       AT_LEAST         enters BLANK (the sum stays OPEN); its proven minimum is named BESIDE, never summed
       BLANK            enters BLANK (HELD)
       a row without a candidate line id (a split a lane-I package must mint) never enters; it is listed beside.
   Every row is used once; a line of the candidate that the form omits refuses; a HELD status on a closed term refuses.

3. dry_mass_inputs: per zone of the restated balance, the dry-mass facts the owner rule needs (owner 2026-11-02
   17:45 (4) / 18:00 (3)): in situ (excavated) m3 x rho_insitu, compacted (placed) m3 x rho_target; every density
   HELD with its test named unless a sourced value is passed; the mass is then a VOLUME x DENSITY expression, never a
   figure (no default density, no swell factor, missing never 0).
"""
from __future__ import annotations

import sys
from pathlib import Path

_RES = Path(__file__).resolve().parents[1]
for _p in (_RES / "agents_t505", _RES / "agents_t503"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
import disposal_balance_v2 as B  # noqa: E402

RULES = {"R-T708-1": "1.0.0 PROPOSED", "R-T708-2": "1.0.0 PROPOSED"}
ROUND = 0.5e-6
BOUNDS = ("VALUE", "RANGE", "ZERO_BY_GEOMETRY", "AT_LEAST", "BLANK")


class RestateError(ValueError):
    pass


def _f(x, what):
    if isinstance(x, bool) or not isinstance(x, (int, float)) or x != x or x in (float("inf"), float("-inf")):
        raise RestateError(f"{what}: not a number: {x!r}")
    return float(x)


# ------------------------------------------------------------------------------------------ 1. reconciliation ----

def reconcile_plan_x_depth(terms, owner_depth_m, owner_plan_m2=None, zone_ends=None, unit="m"):
    """terms: [{"id", "kind": "PANEL" | "OUTSIDE_PLAN", "area_m2" (PANEL), "fill_m3": [low, high], "cause"}].
    owner_depth_m: the single depth of the owner manual method (same datum as the terms). owner_plan_m2: the plan
    the owner method uses; when given it must equal the sum of the PANEL areas (the method and the engine read the
    same plan; else REFUSED: a plan difference is a cause of its own, not a residual). zone_ends: the engine zone
    [low, high] as published; the closure is checked against it."""
    if unit != "m":
        raise RestateError(f"unit {unit!r}: depths in metres only")
    d0 = _f(owner_depth_m, "owner depth")
    if not 0.0 < d0 < 30.0:
        raise RestateError(f"owner depth {d0} m outside 0 .. 30 (a mm value?)")
    if not terms:
        raise RestateError("no terms")
    seen, rows = set(), []
    plan = 0.0
    for t in terms:
        tid = t.get("id")
        if not tid or tid in seen:
            raise RestateError(f"term id {tid!r} missing or twice")
        seen.add(tid)
        if t.get("fill_m3") is None or None in t["fill_m3"]:
            raise RestateError(f"{tid}: a HELD (blank) term cannot be reconciled; bound it or leave the zone HELD")
        lo, hi = (_f(x, f"{tid} fill") for x in t["fill_m3"])
        if hi < lo - 1e-9:
            raise RestateError(f"{tid}: low {lo} above high {hi}")
        if not t.get("cause"):
            raise RestateError(f"{tid}: every term names its drawn cause")
        if t["kind"] == "PANEL":
            a = _f(t["area_m2"], f"{tid} area")
            if a <= 0:
                raise RestateError(f"{tid}: area {a}")
            plan += a
            own = a * d0
        elif t["kind"] == "OUTSIDE_PLAN":
            a, own = None, 0.0
        else:
            raise RestateError(f"{tid}: kind {t['kind']!r}")
        rows.append({"id": tid, "kind": t["kind"], "area_m2": a, "owner_m3": round(own, 6),
                     "engine_m3": [round(lo, 6), round(hi, 6)],
                     "delta_m3": [round(lo - own, 6), round(hi - own, 6)], "cause": t["cause"],
                     "class": t.get("class", "")})
    plan = round(plan, 6)
    if owner_plan_m2 is not None and abs(_f(owner_plan_m2, "owner plan") - plan) > 1e-4:
        raise RestateError(f"owner plan {owner_plan_m2} m2 != panel plan {plan} m2: a plan difference is a cause, "
                           f"name it as a term")
    owner_total = round(plan * d0, 6)
    sum_owner = sum(r["owner_m3"] for r in rows)
    out = {"owner_depth_m": d0, "owner_plan_m2": plan, "owner_m3": owner_total, "terms": rows, "ends": {}}
    tol = len(rows) * ROUND + ROUND
    for k, side in ((0, "low"), (1, "high")):
        eng = sum(r["engine_m3"][k] for r in rows)
        dsum = sum(r["delta_m3"][k] for r in rows)
        closure = owner_total + dsum                    # owner + every named cause
        pub = eng if zone_ends is None else _f(zone_ends[k], f"zone {side}")
        if abs(owner_total - sum_owner) > tol:
            raise RestateError(f"owner total {owner_total} != sum of per-term owner figures {sum_owner}")
        if abs(eng - pub) > tol:
            raise RestateError(f"{side}: the published zone {pub} is not the sum of its terms {eng:.6f}: an "
                               f"unexplained difference")
        res_pub = closure - pub
        by = {}
        for r in rows:
            c = r["class"] or r["kind"]
            by[c] = round(by.get(c, 0.0) + r["delta_m3"][k], 6)
        out["ends"][side] = {"engine_m3": round(eng, 6), "owner_m3": owner_total,
                             "difference_engine_minus_owner_m3": round(eng - owner_total, 6),
                             "delta_by_cause_m3": dict(sorted(by.items())),
                             "residual_m3": round(res_pub, 6),
                             "residual_cause": "rounding: per-term figures at 6 decimals vs the owner total "
                                               "rounded once (no physical residual)"}
    return out


# ---------------------------------------------------------------------------------------------- 2. restating ----

def restate_terms(form_rows, candidate_lines, roles, statuses):
    """form_rows: wiring rows (dicts: line_id, element_id, bound, value_m3, low_m3, high_m3, basis, missing_input).
    candidate_lines: {line_id: element_id} of every earthworks line except the disposal line.
    roles: {line_id: B.EXC | B.FILL}. statuses: {line_id: status} for every closed (VALUE / RANGE) row.
    Returns (terms for DISPOSAL_BALANCE_V2, beside) where beside lists the AT_LEAST minima and the id-less rows."""
    terms, beside, used = [], {"at_least": [], "not_entered": []}, set()
    for r in form_rows:
        lid, b = r["line_id"], r["bound"]
        if b not in BOUNDS:
            raise RestateError(f"{lid}: bound {b!r}")
        if not str(lid).startswith("L-"):
            beside["not_entered"].append({"line_id": lid, "element_id": r["element_id"], "bound": b,
                                          "low_m3": r.get("low_m3"), "high_m3": r.get("high_m3"),
                                          "why": "no candidate line id yet (a lane-I package mints it): never "
                                                 "summed"})
            continue
        if lid not in candidate_lines:
            continue                                    # the disposal line itself or a non-earthworks row
        if candidate_lines[lid] != r["element_id"]:
            raise RestateError(f"{lid}: form element {r['element_id']} != candidate {candidate_lines[lid]}")
        if lid in used:
            raise RestateError(f"{lid}: twice in the form")
        used.add(lid)
        zone = r["element_id"].split(":", 2)[2]
        role = roles[lid]
        if b in ("BLANK", "AT_LEAST"):
            parts = [f"{b}: {r.get('missing_input') or r.get('basis')}"]
            terms.append(B.term(lid, role, status=B.HELD, zone=zone, held_parts=parts))
            if b == "AT_LEAST":
                lo = _f(r["low_m3"], f"{lid} at-least")
                beside["at_least"].append({"line_id": lid, "role": role, "zone": zone, "at_least_m3": lo,
                                           "basis": r.get("basis", ""), "missing": r.get("missing_input", ""),
                                           "note": "a proven minimum of a disjoint zone, named beside, never "
                                                   "summed (R-T505-1 / R-T708-2)"})
            continue
        if b == "ZERO_BY_GEOMETRY":
            if _f(r["value_m3"], f"{lid} zero") != 0.0 or not r.get("basis"):
                raise RestateError(f"{lid}: a calculated 0 needs 0.0 and its proof")
            terms.append(B.term(lid, role, 0.0, 0.0, status=B.CALC, zone=zone, held_parts=[]))
            continue
        st = statuses.get(lid)
        if st is None or B.V1._base(st) == B.HELD:
            raise RestateError(f"{lid}: a closed {b} term needs a non-HELD source status, got {st!r}")
        if b == "VALUE":
            v = _f(r["value_m3"], f"{lid} value")
            lo = hi = v
        else:
            lo, hi = _f(r["low_m3"], f"{lid} low"), _f(r["high_m3"], f"{lid} high")
        terms.append(B.term(lid, role, lo, hi, status=st, zone=zone,
                            held_parts=[r["missing_input"]] if r.get("missing_input") else []))
    missing = set(candidate_lines) - used
    if missing:
        raise RestateError(f"candidate lines missing from the form: {sorted(missing)}")
    return terms, beside


def term_diff(before, after):
    """per line: the closed low / high (None = blank) before and after, and the change of each end in m3."""
    a = {t["line_id"]: t for t in after}
    out = []
    for t in before:
        u = a[t["line_id"]]
        d = [None if (x is None or y is None) else round(y - x, 6) for x, y in ((t["low"], u["low"]),
                                                                                  (t["high"], u["high"]))]
        if (t["low"], t["high"], B.V1._base(t["status"])) != (u["low"], u["high"], B.V1._base(u["status"])):
            out.append({"line_id": t["line_id"], "zone": t["zone"], "role": t["role"],
                        "before": [t["low"], t["high"], t["status"]], "after": [u["low"], u["high"], u["status"]],
                        "delta_m3": d})
    return out


def break_even_yield(res):
    """Beside the balance, never a quantity: the in-situ m3 per compacted m3 (k = rho_target / rho_insitu) at which
    the CLOSED excavation exactly covers the CLOSED fill demand, k* = E / D, at the two ends (E low / D high and
    E high / D low). With every excavated m3 suitable (s = 1) the closed parts export soil only for k < k* and import
    only for k > k*. Open (HELD) lines on either side move k* both ways, so it is reported with them named and is
    never used to value a disposal or an import."""
    E, D = res["excavation"], res["fill_demand"]
    if E["low"] is None or not D["low"] or not D["high"]:
        return {"k_star": None, "why": "no closed fill demand: no break-even"}
    return {"k_star": [round(E["low"] / D["high"], 6), round(E["high"] / D["low"], 6)],
            "open_excavation_lines": len(E["held_lines"]), "open_fill_lines": len(D["held_lines"]),
            "note": "closed parts only; HELD lines open on both sides: an indicator, never a quantity"}


# --------------------------------------------------------------------------------------- 3. dry-mass inputs ----

DENSITY_TESTS = {
    "INSITU": "in-situ dry density of the excavated soil (ASTM D6938 or sand cone), MEASURED",
    "PLACEMENT_TARGET": "placement target dry density of the fill (project specification x MDD by ASTM D1557; "
                        "95 % Modified Proctor is PROPOSED-SPEC only, owner 2026-11-02 18:00 (2))",
}


def dry_mass_inputs(zones, rho=None):
    """zones: [{"zone", "line_id", "role": B.EXC | B.FILL, "low_m3", "high_m3", "bound"}]. rho: {"INSITU":
    B.density(...), "PLACEMENT_TARGET": B.density(...)} (HELD when absent). Returns per zone the density it needs
    and either the dry mass range (sourced density) or the expression with the density HELD."""
    rho = rho or {}
    out = []
    for z in zones:
        kind = "INSITU" if z["role"] == B.EXC else "PLACEMENT_TARGET"
        d = rho.get(kind) or B.density(None, B.HELD, kind=kind)
        if d.get("kind") not in (None, kind):
            raise RestateError(f"{z['zone']}: density {d.get('kind')} passed for {kind}")
        lo, hi, bnd = z.get("low_m3"), z.get("high_m3"), z["bound"]
        row = {"zone": z["zone"], "line_id": z["line_id"], "volume_basis": "in situ" if kind == "INSITU" else
               "compacted (placed)", "volume_m3": [lo, hi], "bound": bnd, "density_needed": DENSITY_TESTS[kind]}
        if bnd in ("BLANK",) or lo is None:
            row.update(dry_t=None, state="HELD", missing=["the zone volume (HELD)"] +
                       ([DENSITY_TESTS[kind]] if d["value"] is None else []))
        elif d["value"] is None:
            row.update(dry_t=None, state="HELD", missing=[DENSITY_TESTS[kind]],
                       expression=(f"{lo:.6f}" + ("" if hi is None or hi == lo else f" .. {hi:.6f}") +
                                   (" (at least)" if bnd == "AT_LEAST" else "") + f" m3 x rho_{kind.lower()} t/m3"))
        else:
            row.update(dry_t=[round(lo * d["value"], 6), None if hi is None else round(hi * d["value"], 6)],
                       state="AT_LEAST" if bnd == "AT_LEAST" else "BOUNDED" if hi != lo else "VALUED",
                       density=d, missing=[])
        out.append(row)
    return out
