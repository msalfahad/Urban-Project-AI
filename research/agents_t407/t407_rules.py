"""T-407 rules (research, every villa): masonry below the exterior ground beams of the house, run by run.

Pure functions, stdlib only. Nothing here names a project, a sheet, a layer or a coordinate; every number comes in as
an argument WITH its source (a value without a source is a defaulted value and is refused).

Physical element (ERS s.2.1). Under an exterior ground beam of the house one of three things is built:
  (1) nothing: the beam's own printed section puts its soffit on blinding at the outer ground and no foundation band
      is drawn below it -> masonry NOT_APPLICABLE (drawing evidence, not an absence of evidence);
  (2) masonry printed: a sheet note / section prints block below this beam (e.g. 'neighbour-side ground beams on
      block built from the foundation level') -> the masonry EXISTS; its height runs from the top of the foundation
      member below (band or footing) to the underside of the beam (owner Q-60 A: block to the underside of the beam
      above it), each level only as printed, else bounded;
  (3) a foundation band is drawn below the run but nothing is printed between it and the beam -> existence UNKNOWN:
      HELD by name, a designer item; a conditional bound (IF built) is shown, never a quantity.

R-T407-1 CLASSIFY  a run's class comes only from what is printed for it: a printed masonry note -> PRINTED; a band
                   drawn below with nothing printed between -> UNKNOWN_EXISTENCE; the beam's exterior section with no
                   band below -> NOT_APPLICABLE. A band below is never by itself evidence of masonry; masonry printed
                   for one side (neighbour) is never extended to another side (street, sea) without its own evidence.
R-T407-2 HEIGHT    h >= (beam soffit, lowest reading) - (layer under the beam, max) - (foundation top, highest
                   reading). The foundation top: -formation_min + max over the members along the run of (blinding_max
                   + band depth_max) for a band and (build-up + thickness) for a footing. A printed MINIMUM formation
                   gives AT_LEAST, never a point value and never an upper bound. A beam soffit in CONFLICT (two printed
                   readings, one unbounded) gives NO bound: the per-reading conditional bound is shown beside, never
                   adopted. A non-positive lower bound is refused (the inputs contradict a printed masonry layer).
R-T407-3 NET       plane gross = band-axis length x h; net = (axis - column pieces on the axis) x h; a column cut by
                   two runs (corner) is split along the axis and counted once over the runs.
R-T407-4 ONE LAYER the house masonry runs and the boundary-fence masonry runs are disjoint along the band axis (one
                   physical layer, one owner trade: BLOCKWORK BELOW N.G.); the masonry's vertical extent ends at the
                   beam soffit and at the foundation top, so it shares no volume with the beam or band concrete.
R-T407-5 HELD      the value of a held line is None (blank), never 0; its bound sits beside it (AT_LEAST / conditional).
"""

PRINTED = "MASONRY_PRINTED"
UNKNOWN = "UNKNOWN_EXISTENCE"
NA = "NOT_APPLICABLE"


class RuleError(ValueError):
    pass


def _src(x, what):
    """A sourced number: {'value': float, 'source': 'sheet / note'}; None or a bare number is refused."""
    if not isinstance(x, dict) or "value" not in x or not str(x.get("source", "")).strip():
        raise RuleError(f"{what}: value without a printed source (defaulted value refused)")
    v = x["value"]
    if v is None or isinstance(v, bool) or not isinstance(v, (int, float)):
        raise RuleError(f"{what}: not a number")
    if x.get("unit", "m") != "m":
        raise RuleError(f"{what}: unit {x.get('unit')} (levels and depths in m only)")
    if abs(v) > 50.0:
        raise RuleError(f"{what}: {v} m is not a level in metres (mm passed as m?)")
    return float(v)


def classify(run):
    """R-T407-1. run: {'masonry_note': bool, 'band_below': bool, 'exterior_section_on_ground': bool}."""
    note, band, sec = bool(run.get("masonry_note")), bool(run.get("band_below")), bool(run.get("exterior_section_on_ground"))
    if note:
        return PRINTED
    if band:
        return UNKNOWN
    if sec:
        return NA
    return UNKNOWN


def foundation_top_high(formation_min_depth, members):
    """Highest possible top of the foundation members along a run (m, relative to the ground datum, negative down).

    formation_min_depth: sourced, the printed MINIMUM excavation depth below the datum (positive m).
    members: [{'kind': 'BAND', 'blinding_max': src, 'depth_max': src} | {'kind': 'FOOTING', 'buildup': src, 't': src}]
    """
    f = _src(formation_min_depth, "formation minimum")
    if f <= 0:
        raise RuleError("formation minimum must be a depth below the datum")
    if not members:
        raise RuleError("no foundation member under the run: the masonry has nothing printed to stand on")
    tops = []
    for m in members:
        if m.get("kind") == "BAND":
            tops.append(-f + _src(m["blinding_max"], "band blinding") + _src(m["depth_max"], "band depth"))
        elif m.get("kind") == "FOOTING":
            tops.append(-f + _src(m["buildup"], "footing build-up") + _src(m["t"], "footing thickness"))
        else:
            raise RuleError(f"unknown foundation member {m.get('kind')}")
    return max(tops)


def height_bound(soffit_readings, under_beam_max, formation_min_depth, members):
    """R-T407-2. Returns {'h_at_least': float | None, 'conditional': {reading: h}, 'basis': str}.

    soffit_readings: {name: sourced level of the beam underside | None (a reading with no printed value)}.
    under_beam_max: sourced thickness of the layer printed under the beam (blinding) at its maximum (0 if none printed
    must still be sourced).
    """
    if not soffit_readings:
        raise RuleError("no beam soffit reading")
    top = foundation_top_high(formation_min_depth, members)
    ub = _src(under_beam_max, "layer under the beam")
    cond, unbounded = {}, []
    for name, lv in sorted(soffit_readings.items()):
        if lv is None:
            unbounded.append(name)
            continue
        h = _src(lv, f"soffit {name}") - ub - top
        if h <= 0:
            raise RuleError(f"reading {name}: beam soffit at or below the foundation top (h {h:.3f} m): contradicts the "
                            "printed masonry layer")
        cond[name] = round(h, 6)
    if unbounded:
        return {"h_at_least": None, "conditional": cond,
                "basis": "CONFLICT: reading(s) " + ", ".join(unbounded) + " print no soffit; no bound adopted"}
    return {"h_at_least": round(min(cond.values()), 6), "conditional": cond, "basis": "AT_LEAST (formation printed as a minimum)"}


def run_takeoff(run, h):
    """R-T407-3 / -5. run: {'id', 'axis_m', 'columns_m': [(id, m)], 'class'}; h: height_bound(...) or None."""
    axis = float(run["axis_m"])
    if axis <= 0 or axis > 500:
        raise RuleError(f"{run['id']}: axis {axis} m not a run length in m")
    cols = sum(float(m) for _, m in run.get("columns_m", []))
    if cols > axis + 1e-9:
        raise RuleError(f"{run['id']}: columns longer than the run")
    cls = run["class"]
    out = {"id": run["id"], "class": cls, "axis_m": round(axis, 4), "columns_m": round(cols, 4),
           "net_axis_m": round(axis - cols, 4), "value_m2": None}
    if cls == NA:
        out.update(status="NOT_APPLICABLE", gross_at_least_m2=None, net_at_least_m2=None, conditional_net_m2={})
        return out
    hl = None if h is None else h["h_at_least"]
    cond = {} if h is None else {k: round((axis - cols) * v, 4) for k, v in h["conditional"].items()}
    if cls == PRINTED:
        status = "MISSING_HELD_AT_LEAST" if hl is not None else "MISSING_HELD_UNBOUNDED"
        out.update(status=status,
                   gross_at_least_m2=None if hl is None else round(axis * hl, 4),
                   net_at_least_m2=None if hl is None else round((axis - cols) * hl, 4),
                   conditional_net_m2=cond)
    elif cls == UNKNOWN:
        out.update(status="HELD_EXISTENCE_UNKNOWN", gross_at_least_m2=None, net_at_least_m2=None,
                   conditional_net_m2=cond)
    else:
        raise RuleError(f"unknown class {cls}")
    return out


def check_one_layer(house_runs, fence_runs):
    """R-T407-4: chainage intervals [(id, start_m, end_m)] along the band axis; any overlap is refused."""
    segs = [(a, b, i, "HOUSE") for i, a, b in house_runs] + [(a, b, i, "FENCE") for i, a, b in fence_runs]
    segs.sort()
    for (a1, b1, i1, k1), (a2, b2, i2, k2) in zip(segs, segs[1:]):
        if a2 < b1 - 1e-6:
            raise RuleError(f"{k1} {i1} and {k2} {i2} overlap {min(b1, b2) - a2:.3f} m on the band axis "
                            "(one masonry layer counted twice)")
    return True


def check_held(lines):
    """R-T407-5: a held line carries no value; a value of 0 on a held line is refused."""
    for ln in lines:
        if ln["status"].startswith(("MISSING_HELD", "HELD")) and ln.get("value_m2") is not None:
            raise RuleError(f"{ln['id']}: held line carries a value ({ln['value_m2']}); held stays blank, never 0")
    return True
