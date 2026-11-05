"""T-534 STAIR_BED_RECONCILE_V1 (research, UNWIRED; every villa): stair marble surfaces, the 1:3 bed under them, and
the reconciliation of two stair-marble figures to their physical causes.

Physical element (ERS s.2.1). Stair marble is three kinds of surface:
  TREAD    the horizontal going of a step, measured front edge to front edge (= riser face to riser face) x the drawn
           front-edge width; the drawn nosing projection overhangs the riser plate below and carries NO bed (it is the
           B7-05 nosing lm, never an m2 here);
  RISER    the vertical plate of a step: width x VISIBLE height = rise - tread marble thickness (UP-STAIR-003; the
           thickness is the caller's value, e.g. UP-STAIR-006 0.030 m DEFAULT); one riser per drawn / sectioned rise;
  LANDING  a flat stair surface (half / quarter / split-level / arrival landing) on its actual polygon (UP-STAIR-005).
A landing is never a tread and a tread is never a landing: the riser onto a landing or floor has no tread above it
(treads come from the drawn fronts, never as 'one tread per riser').

The BED (owner Q-45: stairs 3 cm, 1:3; Q-53 C: theoretical cement / sand per m3) lies under the horizontal stone
(TREAD, LANDING). Behind a RISER plate the setting mortar is a vertical backing: it is a bed of this layer ONLY when
the caller names the source that puts risers in the stair bed scope (on the training villa: Q-45 item 1 'marble
stairs (treads, risers) __ cm', answered B with stairs 3 cm). With no source the riser bed is HELD by name
(RISER_BED_SOURCE_NOT_GIVEN) and the riser MARBLE stays measured: the marble area and the bed area then differ by
exactly the riser m2.

Rules (R-T534-1 .. R-T534-3, every villa; no villa constant in this module):
  R-T534-1 SURFACE PARTS: every flight / landing gives one part per surface kind, each a number (MEASURED or
           CALCULATED) or HELD with its reason and, when known, a beside bound; a HELD part is never 0 and never
           in a determinate sum; a part keyed twice is refused (one surface once).
  R-T534-2 BED SCOPE: TREAD and LANDING parts are bedded; a RISER part is bedded only with a named source; a landing
           whose MATERIAL is held (floor or landing undecided) is not in the stair bed (HELD, named), its area kept.
  R-T534-3 RECONCILIATION: two figures for 'the stair marble' are compared key by key (flight x surface). A key in
           both is decomposed multiplicatively in a fixed order (count, width, depth / height): d_count =
           (n_b - n_a) w_a d_a, d_width = n_b (w_b - w_a) d_a, d_depth = n_b w_b (d_b - d_a), which add exactly to
           b - a; a key in one figure only is a SCOPE difference with its stated cause; an area given without
           components (a polygon line) leaves a POLYGON residual against the printed components, named with its m2.
           The figures reconcile only when the sum of causes equals b - a within 1e-6 m2; any rest is UNEXPLAINED
           and refuses the reconciliation (never absorbed).
"""

from __future__ import annotations

import math

TREAD, RISER, LANDING = "TREAD", "RISER", "LANDING"
SURFACES = (TREAD, RISER, LANDING)
MEASURED, CALCULATED, HELD = "MEASURED", "CALCULATED", "HELD"
TOL = 1e-6


class ReconcileError(ValueError):
    pass


def _r(x, n=6):
    return None if x is None else round(x + 0.0, n)


def _pos(name, v, zero_ok=False):
    if isinstance(v, bool) or not isinstance(v, (int, float)) or math.isnan(v):
        raise ReconcileError(f"{name} must be a number, got {v!r}")
    if v < 0 or (v == 0 and not zero_ok):
        raise ReconcileError(f"{name} must be > 0, got {v!r}")
    return float(v)


def _count(name, v):
    if isinstance(v, bool) or not isinstance(v, int) or v < 0:
        raise ReconcileError(f"{name} must be a whole count >= 0, got {v!r}")
    return v


def part(key, surface, m2, status, basis, reason=None, beside=None, components=None):
    if surface not in SURFACES:
        raise ReconcileError(f"unknown surface {surface!r}")
    if status == HELD:
        if m2 is not None:
            raise ReconcileError(f"{key} {surface}: a HELD part carries no figure (beside only)")
        if not reason:
            raise ReconcileError(f"{key} {surface}: a HELD part needs its reason")
    elif m2 is None:
        raise ReconcileError(f"{key} {surface}: a {status} part needs its m2 (else HELD with a reason)")
    return {"key": key, "surface": surface, "m2": _r(m2), "status": status, "basis": basis, "reason": reason,
            "beside": _r(beside), "components": components}


def flight_parts(f, tread_t):
    """R-T534-1 for one flight. f: id, treads (drawn tread fronts with a drawn going), risers (sectioned / drawn
    rises), going, width, rise (m, or None = not established), unit_m (default 1.0: lengths x unit_m), optional
    treads_held / risers_held (counts whose going or position is not drawn: HELD beside), held (reason: the whole
    flight is held, e.g. a winder turn), status (default CALCULATED). tread_t = tread marble thickness (m)."""
    k = f["id"]
    u = _pos(f"{k} unit_m", f.get("unit_m", 1.0))
    t = _pos("tread marble thickness", tread_t)
    if f.get("held"):
        return [part(k, TREAD, None, HELD, "flight held", f["held"], f.get("beside_tread")),
                part(k, RISER, None, HELD, "flight held", f["held"], f.get("beside_riser"))]
    n_t, n_r = _count(f"{k} treads", f["treads"]), _count(f"{k} risers", f["risers"])
    going, width = _pos(f"{k} going", f["going"]) * u, _pos(f"{k} width", f["width"]) * u
    if n_t > n_r:
        raise ReconcileError(f"{k}: {n_t} treads > {n_r} risers (a tread needs the riser below it)")
    st = f.get("status", CALCULATED)
    out = []
    if n_t:     # a flight with no tread (a closing riser) has no tread part, never a 0
        out.append(part(k, TREAD, n_t * going * width, st, f"{n_t} treads x {going:g} going x {width:g} width",
                        components={"n": n_t, "w": width, "d": going}))
    nh = _count(f"{k} treads_held", f.get("treads_held", 0))
    if nh:
        out.append(part(k + "#held-treads", TREAD, None, HELD, f"{nh} tread(s) with no drawn going",
                        f.get("treads_held_reason") or "TREAD_GOING_NOT_DRAWN", nh * going * width))
    rise = f.get("rise")
    if not n_r:
        pass
    elif rise is None:
        out.append(part(k, RISER, None, HELD, f"{n_r} risers", f.get("rise_reason") or "RISE_NOT_ESTABLISHED"))
    else:
        vis = _pos(f"{k} rise", rise) * u - t
        if vis <= 0:
            raise ReconcileError(f"{k}: visible riser {vis:g} <= 0 (rise {rise:g} x {u:g} - marble {t:g})")
        out.append(part(k, RISER, n_r * width * vis, st,
                        f"{n_r} risers x {width:g} x ({rise * u:g} rise - {t:g} tread marble) (UP-STAIR-003)",
                        components={"n": n_r, "w": width, "d": vis}))
    rh = _count(f"{k} risers_held", f.get("risers_held", 0))
    if rh:
        vis = None if rise is None else rise * u - t
        out.append(part(k + "#held-risers", RISER, None, HELD, f"{rh} riser(s) with no drawn position",
                        f.get("risers_held_reason") or "RISER_POSITION_NOT_DRAWN",
                        None if vis is None else rh * width * vis))
    return out


def shoelace(pts):
    a = 0.0
    for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]):
        a += x1 * y2 - x2 * y1
    return abs(a) / 2.0


def landing_part(l):
    """one landing: area from a polygon (shoelace, any orientation), length x width, or a given area; unit_m scales
    lengths. material_held (reason) keeps the area but marks the part HELD for the stair bed (R-T534-2)."""
    k = l["id"]
    u = _pos(f"{k} unit_m", l.get("unit_m", 1.0))
    if l.get("held"):
        return part(k, LANDING, None, HELD, "landing held", l["held"], l.get("beside"))
    if l.get("polygon"):
        a = shoelace(l["polygon"]) * u * u
        comp, basis = None, "polygon (shoelace)"
    elif l.get("length") is not None:
        ln, wd = _pos(f"{k} length", l["length"]) * u, _pos(f"{k} width", l["width"]) * u
        a, comp, basis = ln * wd, {"n": 1, "w": wd, "d": ln}, f"{ln:g} x {wd:g}"
    else:
        a, comp, basis = _pos(f"{k} area", l["area_m2"]) * u * u, None, "area given"
    if a <= 0:
        raise ReconcileError(f"{k}: landing area {a:g} <= 0")
    if l.get("material_held"):
        return part(k, LANDING, None, HELD, basis, f"MATERIAL_HELD: {l['material_held']}", a)
    return part(k, LANDING, a, l.get("status", CALCULATED), basis, components=comp)


def check_once(parts):
    seen = set()
    for p in parts:
        kk = (p["key"], p["surface"])
        if kk in seen:
            raise ReconcileError(f"surface counted twice: {kk}")
        seen.add(kk)
    return parts


def bed_parts(parts, riser_bed_source=None):
    """R-T534-2: the bed parts from the marble parts. A riser is bedded only with riser_bed_source."""
    out = []
    for p in check_once(parts):
        q = dict(p)
        if p["surface"] == RISER and p["status"] != HELD and not riser_bed_source:
            q.update(m2=None, status=HELD, beside=p["m2"],
                     reason="RISER_BED_SOURCE_NOT_GIVEN (riser marble measured; its backing is not in the stair "
                            "bed without a named source)")
        elif p["surface"] == RISER and p["status"] != HELD:
            q["bed_source"] = riser_bed_source
        out.append(q)
    return out


def totals(parts):
    """determinate m2 per surface + project; any HELD part makes the figure PARTIAL (AT_LEAST), never complete."""
    check_once(parts)
    by = {s: 0.0 for s in SURFACES}
    held = []
    for p in parts:
        if p["status"] == HELD:
            held.append({"key": p["key"], "surface": p["surface"], "reason": p["reason"], "beside": p["beside"]})
        else:
            by[p["surface"]] += p["m2"]
    det = sum(by.values())
    return {"by_surface": {s: _r(v) for s, v in by.items()}, "determinate_m2": _r(det),
            "state": "PARTIAL" if held else "COMPLETE", "held": held,
            "print": f"AT_LEAST {_r(det):.4f} m2 + HELD ({len(held)} parts)" if held else f"{_r(det):.4f} m2"}


def decompose(a, b):
    """R-T534-3 for one key: a, b = components {'n','w','d'} -> causes adding exactly to b - a."""
    da = (b["n"] - a["n"]) * a["w"] * a["d"]
    dw = b["n"] * (b["w"] - a["w"]) * a["d"]
    dd = b["n"] * b["w"] * (b["d"] - a["d"])
    return [("COUNT", da), ("WIDTH", dw), ("DEPTH_OR_HEIGHT", dd)]


def reconcile(fig_a, fig_b, scope_causes, polygon_causes=None):
    """fig_a / fig_b: {(key, surface): {'m2', 'components' or None}} (determinate parts only). scope_causes:
    {(key, surface): cause text} for every key present in one figure only. polygon_causes: {(key, surface): cause
    text} for keys whose area in either figure has no components. Returns rows and totals; raises when a key has no
    stated cause or the causes leave an unexplained rest."""
    polygon_causes = polygon_causes or {}
    rows = []
    for kk in sorted(set(fig_a) | set(fig_b)):
        a, b = fig_a.get(kk), fig_b.get(kk)
        ma = 0.0 if a is None else a["m2"]
        mb = 0.0 if b is None else b["m2"]
        causes = []
        if a is None or b is None:
            if kk not in scope_causes:
                raise ReconcileError(f"{kk}: in one figure only and no scope cause stated")
            causes.append(("SCOPE", mb - ma, scope_causes[kk]))
        elif a.get("components") and b.get("components"):
            ca, cb = a["components"], b["components"]
            causes += [(c, v, None) for c, v in decompose(ca, cb) if abs(v) > TOL]
            # an area line beside its printed components (a polygon): the rest is a named POLYGON residual
            poly = (mb - cb["n"] * cb["w"] * cb["d"]) - (ma - ca["n"] * ca["w"] * ca["d"])
            if abs(poly) > TOL:
                if kk not in polygon_causes:
                    raise ReconcileError(f"{kk}: area differs from its components by {poly:+.6f}, no cause stated")
                causes.append(("POLYGON", poly, polygon_causes[kk]))
        elif abs(mb - ma) > TOL:
            if kk not in polygon_causes:
                raise ReconcileError(f"{kk}: area without components differs by {mb - ma:+.6f} and no cause stated")
            causes.append(("POLYGON", mb - ma, polygon_causes[kk]))
        rest = (mb - ma) - sum(v for _, v, _ in causes)
        if abs(rest) > TOL:
            raise ReconcileError(f"{kk}: UNEXPLAINED {rest:+.6f} m2")
        rows.append({"key": kk[0], "surface": kk[1], "a_m2": _r(ma), "b_m2": _r(mb), "diff_m2": _r(mb - ma),
                     "causes": [{"cause": c, "m2": _r(v), "note": n} for c, v, n in causes]})
    ta = sum(r["a_m2"] for r in rows)
    tb = sum(r["b_m2"] for r in rows)
    by_cause = {}
    for r in rows:
        for c in r["causes"]:
            by_cause[c["cause"]] = by_cause.get(c["cause"], 0.0) + c["m2"]
    rest = (tb - ta) - sum(by_cause.values())
    if abs(rest) > TOL * max(1, len(rows)):
        raise ReconcileError(f"UNEXPLAINED total {rest:+.6f} m2")
    return {"rows": rows, "a_m2": _r(ta), "b_m2": _r(tb), "diff_m2": _r(tb - ta),
            "by_cause": {c: _r(v) for c, v in sorted(by_cause.items())}, "unexplained_m2": 0.0}


def figure(parts):
    """the determinate parts of a parts list as a reconcile figure."""
    return {(p["key"], p["surface"]): {"m2": p["m2"], "components": p["components"]}
            for p in check_once(parts) if p["status"] != HELD}
