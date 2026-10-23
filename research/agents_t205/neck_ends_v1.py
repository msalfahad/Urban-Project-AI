"""NECK_ENDS_V1 (T-205, worker 1, 2026-10-23): where a column neck physically starts and stops, from the drawings.

UNWIRED research module (stdlib only). It releases nothing, changes no method version, route G, rule / knowledge file
or released quantity. Rollback: delete research/agents_t205 and tests/t205_neck_ends.

Physical element (ERS s.2.1): a neck is the part of a column below the ground floor, from the TOP OF ITS FOOTING to the
datum where the ground-floor column line starts. Its two ends are named STRUCTURAL datums (UP-LEVEL-DATUM-001 proposed,
T-200), never a finished level:

  bottom = FOOTING_TOP = FORMATION + underlay (screed + membrane) + blinding + footing depth H
  top    = GB_TOP when the ground-beam line is billed NET of the column footprint (the column / neck then owns the
           junction through the beam depth, R-CONC-OWN-1 precedence column > beam), GB_BOTTOM (= GB_TOP - beam depth)
           when the ground-beam line is billed THROUGH the column; any other basis -> HELD (OWNER_UNDEFINED).
  GB_TOP = printed GB top, else the printed relation "GB top = ground-floor slab level" applied to a printed STRUCTURAL
           slab top, else FFL - printed floor build-up; else HELD (LEVEL_NOT_PRINTED).

Rules applied: a finished level (FFL) given as the neck top is REFUSED (FINISHED_AS_STRUCTURAL), never used; a missing
formation leaves the footing end HELD (owner Q-21 C) while the printed layer stack is still reported; a printed limit
("not less than 1.5 m below the plot") is a bound, never a value, and a formation shallower than it is VIOLATED; two
printed sections that disagree are a CONFLICT (area range, HELD), never averaged or maximised; a neck on a lift-pit raft
whose pit depth is not printed is HELD (R-LIFT-PIT-1, T-204). The neck top must be the same datum as the bottom of the
column line above (else GAP / DOUBLE, reported with its volume). Missing never becomes 0.

When a length is HELD the module still gives the exact LINEAR FORM of the volume in the unprinted quantities
(V = const + per_m_build_up x b + per_m_below_limit x d), labelled WHAT_IF: information for the designer item, never a
quantity.
"""
from __future__ import annotations

METHOD = "NECK_ENDS_V1"
SCALE = {"m": 1.0, "cm": 0.01, "mm": 0.001}
FINISHED = ("FFL", "FINISHED_ROOF", "FINISHED_GROUND")
STRUCTURAL = ("SLAB_TOP", "GB_TOP", "GB_BOTTOM", "FOOTING_TOP", "FOOTING_BOTTOM")
GB_BASES = ("NET_OF_COLUMN", "THROUGH_COLUMN")
CODES = ("FINISHED_AS_STRUCTURAL", "LEVEL_NOT_PRINTED", "FORMATION_NOT_PRINTED", "FORMATION_LIMIT_VIOLATED",
         "SECTION_CONFLICT", "FOOTING_CONFLICT", "PIT_DEPTH_NOT_PRINTED", "UNDERLAY_NOT_PRINTED", "OWNER_UNDEFINED", "GAP", "DOUBLE",
         "UNIT_UNKNOWN", "BAD_INPUT")
STATUS_HELD = "HELD"
STATUS_OK = "DRAWING-CONFIRMED"
STATUS_REFUSED = "REFUSED"
EPS = 1e-9


def _k(units):
    if units not in SCALE:
        raise ValueError(f"UNIT_UNKNOWN: {units!r} (m, cm or mm)")
    return SCALE[units]


def _val(d, key, k):
    """A printed value of the project dict, scaled to m; None when absent / not printed."""
    if d is None or key not in d or d[key] is None:
        return None
    v = d[key]
    if isinstance(v, dict):
        v = v.get("value")
    if v is None:
        return None
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise ValueError(f"BAD_INPUT: {key} = {v!r} is not a number")
    return float(v) * k


def section(spec, units="m"):
    """Neck plan section from every PRINTED source (schedule band, plan text, drawn outline marked printed=False is
    kept as a drafting note only). One value -> DRAWING-CONFIRMED; disagreement between printed sources -> CONFLICT
    with the area range, HELD."""
    _k(units)
    printed, notes = [], []
    for s in spec.get("sections", []):
        k = _k(s.get("units", units))
        a = round(float(s["W"]) * k * float(s["D"]) * k, 9)
        (printed if s.get("printed", True) else notes).append(dict(s, area_m2=a))
    if not printed:
        return {"status": STATUS_HELD, "area_m2": None, "range_m2": None, "codes": ["LEVEL_NOT_PRINTED"],
                "notes": notes, "why": "no printed section"}
    areas = sorted({p["area_m2"] for p in printed})
    drafting = [n for n in notes if abs(n["area_m2"] - areas[0]) > EPS or len(areas) > 1]
    if len(areas) == 1:
        return {"status": STATUS_OK, "area_m2": areas[0], "range_m2": (areas[0], areas[0]), "codes": [],
                "notes": drafting, "why": "printed sources agree"}
    return {"status": STATUS_HELD, "area_m2": None, "range_m2": (areas[0], areas[-1]), "codes": ["SECTION_CONFLICT"],
            "notes": drafting, "why": "printed sections disagree: " + "; ".join(
                f"{p['source']} {p['W']}x{p['D']}" for p in printed)}


def gb_top(project, units="m"):
    """(value_m or None, status, codes, why). Never derived from a finished level without a printed build-up."""
    k = _k(units)
    d = project.get("datums", {})
    v = _val(d, "GB_TOP", k)
    if v is not None:
        return v, STATUS_OK, [], "GB top printed"
    rel = project.get("gb_top_relation")              # e.g. "SLAB_TOP" (p.13: top = 'Ground Floor slab level')
    if rel == "SLAB_TOP":
        st = _val(d, "SLAB_TOP", k)
        if st is not None:
            return st, STATUS_OK, [], "GB top = printed structural slab top (printed relation)"
        ffl, bu = _val(d, "FFL", k), _val(project.get("layers", {}), "FLOOR_BUILD_UP", k)
        if ffl is not None and bu is not None:
            return ffl - bu, STATUS_OK, [], "GB top = slab top = FFL - printed floor build-up"
        return None, STATUS_HELD, ["LEVEL_NOT_PRINTED"], ("GB top = ground-floor slab top, but neither the slab top "
                                                          "nor the FFL -> slab build-up is printed")
    return None, STATUS_HELD, ["LEVEL_NOT_PRINTED"], "no GB top and no printed relation to the slab"


def neck_top(project, gb_depth_m=None, units="m"):
    """The neck's top datum by the ground-beam line's measurement basis (R-CONC-OWN-1)."""
    req = project.get("neck_top_kind")
    if req in FINISHED:
        return {"kind": req, "value_m": None, "status": STATUS_REFUSED, "codes": ["FINISHED_AS_STRUCTURAL"],
                "why": f"{req} is a finished level; a neck ends on a structural surface"}
    basis = project.get("gb_basis")
    if basis not in GB_BASES:
        return {"kind": None, "value_m": None, "status": STATUS_HELD, "codes": ["OWNER_UNDEFINED"],
                "why": f"ground-beam measurement basis {basis!r} not established: the junction owner is undefined"}
    v, st, codes, why = gb_top(project, units)
    if basis == "NET_OF_COLUMN":
        return {"kind": "GB_TOP", "value_m": v, "status": st, "codes": codes,
                "why": "GB billed net of the column footprint -> the neck owns the junction up to the GB top; " + why}
    if gb_depth_m is None:
        return {"kind": "GB_BOTTOM", "value_m": None, "status": STATUS_HELD, "codes": ["LEVEL_NOT_PRINTED"],
                "why": "GB billed through the column, its depth at this neck not printed"}
    return {"kind": "GB_BOTTOM", "value_m": None if v is None else v - gb_depth_m, "status": st, "codes": codes,
            "why": "GB billed through the column -> the neck stops at its soffit; " + why}


def footing_top(spec, project, units="m"):
    """FOOTING_TOP = FORMATION + underlay + blinding + H; the printed stack is reported even when the formation is not."""
    k = _k(units)
    ftg = spec.get("footing") or {}
    H = _val(ftg, "H", k)
    if ftg.get("conflict"):
        return {"value_m": None, "status": STATUS_HELD, "codes": ["FOOTING_CONFLICT"], "stack_m": None,
                "why": "footing under the neck is a printed conflict: " + str(ftg["conflict"])}
    if H is None:
        return {"value_m": None, "status": STATUS_HELD, "codes": ["LEVEL_NOT_PRINTED"], "stack_m": None,
                "why": "footing depth not printed"}
    if ftg.get("pit_raft") and _val(ftg, "pit_depth", k) is None:
        return {"value_m": None, "status": STATUS_HELD, "codes": ["PIT_DEPTH_NOT_PRINTED"], "stack_m": None,
                "why": "neck on a lift-pit raft: the pit depth (raft top below the slab) is not printed"}
    und, bl = _val(ftg, "underlay", k), _val(ftg, "blinding", k)
    if und is None or bl is None:
        return {"value_m": None, "status": STATUS_HELD, "codes": ["UNDERLAY_NOT_PRINTED"], "stack_m": None,
                "why": "screed / membrane or blinding thickness under this footing not printed"}
    stack = und + bl + H
    d = project.get("datums", {})
    f = _val(d, "FORMATION", k)
    lim = project.get("formation_limit")             # {"bound": "AT_MOST", "value": -1.50}
    limv = None if lim is None else float(lim["value"]) * k
    if f is None:
        return {"value_m": None, "status": STATUS_HELD, "codes": ["FORMATION_NOT_PRINTED"], "stack_m": stack,
                "limit_m": limv, "why": "formation (founding) level not printed; footing top = formation + "
                                        f"{stack:.3f} m (printed stack); the limit is a bound, not a value"}
    if lim is not None and lim.get("bound") == "AT_MOST" and f > limv + EPS:
        return {"value_m": None, "status": STATUS_HELD, "codes": ["FORMATION_LIMIT_VIOLATED"], "stack_m": stack,
                "limit_m": limv, "why": f"printed formation {f:.3f} is above the printed limit {limv:.3f}"}
    return {"value_m": f + stack, "status": STATUS_OK, "codes": [], "stack_m": stack, "limit_m": limv,
            "why": "formation + printed stack"}


def neck(spec, project, units="m"):
    """One neck: section, both ends, length and volume, or HELD with every reason and the linear what-if form."""
    k = _k(units)
    sec = section(spec, units)
    gbd = _val(spec, "gb_depth", k)
    top = neck_top(project, gbd, units)
    bot = footing_top(spec, project, units)
    codes = list(dict.fromkeys(sec["codes"] + top["codes"] + bot["codes"]))
    out = {"id": spec["id"], "type": spec.get("type"), "section": sec, "top": top, "bottom": bot, "codes": codes,
           "length_m": None, "volume_m3": None, "status": STATUS_HELD, "what_if": None}
    if top["status"] == STATUS_REFUSED:
        out["status"] = STATUS_REFUSED
        return out
    if top["value_m"] is not None and bot["value_m"] is not None:
        L = top["value_m"] - bot["value_m"]
        if L <= 0:
            out["codes"].append("BAD_INPUT")
            out["why"] = f"neck top {top['value_m']:.3f} not above the footing top {bot['value_m']:.3f}"
            return out
        out["length_m"] = round(L, 6)
        if sec["status"] == STATUS_OK:
            out["volume_m3"] = round(sec["area_m2"] * L, 6)
            out["status"] = STATUS_OK
        else:
            lo, hi = sec["range_m2"] or (None, None)
            out["volume_range_m3"] = None if lo is None else (round(lo * L, 6), round(hi * L, 6))
    out["what_if"] = what_if(spec, project, sec, units)
    return out


def what_if(spec, project, sec=None, units="m"):
    """Linear form of the neck volume in the two unprinted quantities, for a GB-top neck (NET_OF_COLUMN basis) whose
    top is FFL - b (b = FFL -> structural slab top build-up) and whose formation is limit - d (d = depth below the printed
    limit): V = A x (FFL - limit - stack - b + d). None when anything else is unprinted (section conflict gives a range).
    WHAT_IF, never a quantity."""
    k = _k(units)
    sec = sec or section(spec, units)
    if project.get("gb_basis") != "NET_OF_COLUMN" or project.get("gb_top_relation") != "SLAB_TOP":
        return None
    ffl = _val(project.get("datums", {}), "FFL", k)
    lim = project.get("formation_limit")
    bot = footing_top(spec, dict(project, datums={}), units)
    if ffl is None or lim is None or bot.get("stack_m") is None:
        return None
    c0 = ffl - float(lim["value"]) * k - bot["stack_m"]
    areas = (sec["area_m2"], sec["area_m2"]) if sec["status"] == STATUS_OK else (sec["range_m2"] or (None, None))
    if areas[0] is None:
        return None
    return {"label": "WHAT_IF (not a quantity)", "length_at_b0_d0_m": round(c0, 6),
            "area_m2": areas, "const_m3": tuple(round(a * c0, 6) for a in areas),
            "per_m_build_up_m3": tuple(round(-a, 6) for a in areas),
            "per_m_below_limit_m3": tuple(round(a, 6) for a in areas)}


def stack_check(neck_top_kind, neck_top_m, column_bottom_kind, column_bottom_m, column_area_m2):
    """The neck top and the bottom of the column line above must be ONE datum. A column line starting higher leaves a
    GAP, lower bills it twice (DOUBLE); both with volume = column area x difference. Unknown values -> HELD."""
    if neck_top_kind == column_bottom_kind and neck_top_kind is not None:
        if neck_top_m is None or column_bottom_m is None or abs(neck_top_m - column_bottom_m) < 1e-6:
            return {"code": "PASS", "volume_m3": 0.0, "why": "same datum"}
    if neck_top_m is None or column_bottom_m is None:
        return {"code": STATUS_HELD, "volume_m3": None,
                "why": f"neck top {neck_top_kind} and column bottom {column_bottom_kind} are different datums and at "
                       "least one is not printed: GAP or DOUBLE of column area x the unprinted difference"}
    dz = column_bottom_m - neck_top_m
    if abs(dz) < 1e-6:
        return {"code": "PASS", "volume_m3": 0.0, "why": "different names, same level"}
    return {"code": "GAP" if dz > 0 else "DOUBLE", "volume_m3": round(abs(dz) * column_area_m2, 6),
            "why": f"column line starts {abs(dz):.3f} m {'above' if dz > 0 else 'below'} the neck top"}


def reconcile(freelancer, census, released):
    """Freelancer total -> engine released total in fixed order (ERS s.2.4): scope, section, count, height; residual
    named. freelancer: {type: {"n", "W", "D", "h"}} (his row arithmetic, metres); census: {type: {"area_m2", "drawn",
    "held"}} (printed section, drawn count, of which held by the engine; a freelancer count above the drawn count is
    the step scope_not_drawn); released: list of {"type", "area_m2",
    "length_m"} (one per released line)."""
    F = sum(r["n"] * r["W"] * r["D"] * r["h"] for r in freelancer.values())
    R = sum(x["area_m2"] * x["length_m"] for x in released)
    nr = {}
    for x in released:
        nr[x["type"]] = nr.get(x["type"], 0) + 1
    steps = {"scope_not_drawn": [], "scope_engine_held": [], "scope_engine_only": [], "section": [], "count": [], "height": []}
    for t in sorted(set(freelancer) | set(census) | set(nr)):
        f = freelancer.get(t)
        c = census.get(t, {"area_m2": None, "drawn": 0, "held": 0})
        n_r, n_h = nr.get(t, 0), c.get("held", 0)
        if not f and n_r:
            steps["scope_engine_only"].append({"type": t, "n": n_r, "m3": round(sum(
                x["area_m2"] * x["length_m"] for x in released if x["type"] == t), 6)})
        if f:
            Af, hf, nf = f["W"] * f["D"], f["h"], f["n"]
            extra = max(0, nf - c.get("drawn", 0))          # priced beyond the drawn census of that type
            if extra:
                steps["scope_not_drawn"].append({"type": t, "n": extra, "m3": round(-extra * Af * hf, 6)})
                nf -= extra
            scope = max(0, min(nf - n_r, n_h))
            if scope:
                steps["scope_engine_held"].append({"type": t, "n": scope, "m3": round(-scope * Af * hf, 6)})
            common = min(nf, n_r)
            if common and c["area_m2"] is not None and abs(c["area_m2"] - Af) > EPS:
                steps["section"].append({"type": t, "n": common, "freelancer_m2": round(Af, 6),
                                         "printed_m2": c["area_m2"],
                                         "m3": round(common * (c["area_m2"] - Af) * hf, 6)})
            if n_r > nf:
                steps["count"].append({"type": t, "n": n_r - nf, "m3": round((n_r - nf) * c["area_m2"] * hf, 6)})
            for x in (x for x in released if x["type"] == t):
                steps["height"].append({"type": t, "m3": round(x["area_m2"] * (x["length_m"] - hf), 6)})
    tot = {k: round(sum(s["m3"] for s in v), 6) for k, v in steps.items()}
    explained = round(sum(tot.values()), 6)
    return {"freelancer_m3": round(F, 6), "released_m3": round(R, 6), "difference_m3": round(R - F, 6),
            "steps": steps, "totals_m3": tot, "explained_m3": explained,
            "residual_m3": round(R - F - explained, 6)}
