"""T-403 rules (research, every villa): the plot boundary wall BELOW natural ground, component by component, run by run.

Physical element (ERS s.2.1): a boundary wall below N.G. is a composite:
  LOWER_GB    the lower ground beam on the founding level (on blinding), b x d, along the run;
  PADS        one pad under each boundary column (L x W x T; the beam passes through it: a beam share b x L x T that
              belongs to the pad OR the beam, once);
  BLINDING    plain concrete under pads (and under the beam where a section draws it);
  MASONRY     the wall between the lower G.B top and the upper G.B soffit (height 'as per excavation depth');
  COLUMNS     boundary columns below N.G. (from the lower G.B top to N.G.; the upper-G.B joint is the column's);
  UPPER_GB    the upper ground beam, top at N.G., stopping at the column faces (the joint is the column's).
Each component has one owner line; a fact the drawings do not print stays HELD (value None, never 0) with the bound the
printed / drawn geometry gives.

Rules
  R-T403-1  runs: the foundation band is split along its axis into FENCE runs (under the upper G.B footprint) and
            other owners' runs (POOL back, HOUSE sides); the run axes conserve the band axis; only FENCE runs carry the
            boundary-wall components; a POOL or HOUSE run passed as FENCE is refused.
  R-T403-2  section: a run uses the section printed for IT; a typical section is used only when the run has no own
            section; a run with its own printed section given the typical one is refused.
  R-T403-3  lower G.B: printed depth readings that disagree give a RANGE (min .. max), never a mid value; a footing
            crossing is deducted only where the printed levels show the same elevation; unprinted levels: the low end
            deducts, the high end does not. With pads present and the pad / beam share owner not printed, the line's
            low end is NOT ESTABLISHED (the physical total does not move).
  R-T403-4  masonry height h = formation depth - blinding - lower G.B depth - upper G.B depth. The formation depth
            comes only from a print for the boundary wall or a printed general minimum (then AT_LEAST); a depth taken
            from the house footings is refused. Plane = run x h; net = plane - columns x column width x h; unknown
            column count -> net HELD (plane is its at-most bound).
  R-T403-5  upper G.B: net = run x b x d - columns x (b x column width x d); unknown count -> HELD, AT_MOST the gross.
  R-T403-6  pads / columns: count only from a print (schedule, plan, 'n No.'); 'SEE ARCH PLAN' with none drawn -> HELD.
  R-T403-7  totals: any HELD component makes the total HELD (None); a HELD value is never summed as 0.
"""

from __future__ import annotations

HELD = None


class RefusedInput(ValueError):
    pass


def _num(x, what):
    if x is None:
        return None
    if not isinstance(x, (int, float)) or x != x or x < 0:
        raise RefusedInput(f"{what}: not a non-negative number ({x!r})")
    return float(x)


def _r(x, n=6):
    return None if x is None else round(x + 0.0, n)


def check_units(villa):
    if villa.get("unit") != "m":
        raise RefusedInput("unit must be 'm' (a mm / cm input is refused, never rescaled silently)")
    for run in villa["runs"]:
        if run["axis_m"] > 500:
            raise RefusedInput(f"run {run['id']}: {run['axis_m']} m is not a plot run (mm passed as m?)")


def section_for(villa, run):
    """R-T403-2."""
    own = run.get("own_section")
    given = run.get("section_ref")
    if own is not None and given is not None and given != own:
        raise RefusedInput(f"run {run['id']}: typical section '{given}' applied to a run with its own section '{own}'")
    ref = own if own is not None else given
    if ref is None or ref not in villa["sections"]:
        raise RefusedInput(f"run {run['id']}: no printed section")
    return ref, villa["sections"][ref]


def formation(villa, run, sec):
    """R-T403-4 formation depth below N.G.: ('VALUE', d) | ('AT_LEAST', d) | ('HELD', None)."""
    f = run.get("formation") or sec.get("formation") or villa.get("formation") or {}
    src = f.get("source")
    if src == "HOUSE_FOOTING":
        raise RefusedInput(f"run {run['id']}: formation depth borrowed from the house footings")
    if f.get("value") is not None:
        if src not in ("PRINTED_BOUNDARY_SECTION", "PRINTED_LEVEL"):
            raise RefusedInput(f"run {run['id']}: formation value without a printed source")
        return "VALUE", _num(f["value"], "formation")
    if f.get("at_least") is not None:
        if src != "PRINTED_GENERAL_MINIMUM":
            raise RefusedInput(f"run {run['id']}: formation minimum without a printed note")
        return "AT_LEAST", _num(f["at_least"], "formation minimum")
    return "HELD", None


def run_takeoff(villa, run):
    if run["class"] != "FENCE":
        raise RefusedInput(f"run {run['id']}: class {run['class']} is another owner's run, not a boundary-wall run")
    ref, s = section_for(villa, run)
    L = _num(run["axis_m"], "run")
    X = _num(run.get("crossing_m", 0.0), "crossing")
    if X > L:
        raise RefusedInput(f"run {run['id']}: crossing longer than the run")
    b_up, d_up = _num(s["upper_b"], "upper b"), _num(s["upper_d"], "upper d")
    b_lo = _num(s["lower_b"], "lower b")
    dl = sorted({_num(v, "lower d") for v in s["lower_d_readings"]})
    if not dl:
        raise RefusedInput(f"run {run['id']}: lower G.B depth not printed at all")
    t_bl = _num(s.get("blinding_t", 0.0), "blinding")
    n = run.get("columns")
    n = None if n is None else int(n)
    cw = _num(s["column_w"], "column width along the wall")
    ct = _num(s["column_t"], "column thickness")
    pad = s.get("pad")  # (L, W, T) or None
    same_level = run.get("crossing_same_level")  # True / False / None (levels not printed)

    out = {"run": run["id"], "section": ref, "axis_m": _r(L), "crossing_m": _r(X), "columns": n}
    # upper G.B (R-T403-5)
    gross_up = L * b_up * d_up
    out["UPPER_GB_m3"] = {"gross": _r(gross_up),
                          "net": _r(gross_up - n * b_up * cw * d_up) if n is not None else HELD,
                          "at_most": _r(gross_up)}
    # lower G.B (R-T403-3)
    lo_len = L if same_level is False else L - X      # unprinted levels: the low end deducts
    hi_len = L - X if same_level is True else L       # ... the high end does not
    solid_lo, solid_hi = lo_len * b_lo * dl[0], hi_len * b_lo * dl[-1]
    share = None
    if pad is not None:
        pL, pW, pT = (_num(v, "pad") for v in pad)
        share = pL * b_lo * pT
    owner = s.get("pad_share_owner")  # 'PAD' | 'BEAM' | None (not printed)
    line_lo, line_hi, lo_note = solid_lo, solid_hi, None
    if pad is not None:
        if n is None:
            line_lo, lo_note = HELD, "NOT_ESTABLISHED: pad count not printed (pad / beam share open)"
        elif owner == "PAD":
            line_lo, line_hi = solid_lo - n * share, solid_hi - n * share
        elif owner is None:
            line_lo, lo_note = solid_lo - n * share, "pad / beam share owner not printed: low end = beam less every share"
    exact = len(dl) == 1 and lo_len == hi_len and (pad is None or (n is not None and owner is not None))
    out["LOWER_GB_m3"] = {"low": _r(line_lo), "high": _r(line_hi), "solid_low": _r(solid_lo), "solid_high": _r(solid_hi),
                          "value": _r(line_lo) if exact else HELD, "low_note": lo_note, "free_m": _r(L - X)}
    # pads (R-T403-6)
    if pad is not None:
        unit = pL * pW * pT
        out["PADS_m3"] = {"unit_gross": _r(unit), "unit_beam_share": _r(share),
                          "value": _r(n * (unit if owner != "BEAM" else unit - share)) if (n is not None and owner) else HELD}
    # masonry (R-T403-4)
    kind, D = formation(villa, run, s)
    if kind == "HELD":
        h_lo = h_hi = None
    else:
        h_lo, h_hi = D - t_bl - dl[-1] - d_up, D - t_bl - dl[0] - d_up
        if h_lo < 0:
            raise RefusedInput(f"run {run['id']}: beams deeper than the formation depth")
    plane_lo = None if h_lo is None else L * h_lo
    exact = kind == "VALUE" and len(dl) == 1   # one height only when the formation and the beam depth are printed
    out["MASONRY_m2"] = {"formation": kind, "h_low": _r(h_lo), "h_high": _r(h_hi) if kind == "VALUE" else None,
                         "plane_at_least": _r(plane_lo),
                         "plane": _r(plane_lo) if exact else HELD,
                         "net": _r(plane_lo - n * cw * h_lo) if (exact and n is not None) else HELD}
    out["COLUMNS_BELOW_NG_m3"] = {"value": _r(n * cw * ct * (h_lo + d_up)) if (exact and n is not None) else HELD}
    return out


def total(results, comp, key):
    """R-T403-7: None if any component is HELD."""
    s = 0.0
    for r in results:
        v = r[comp][key]
        if v is None:
            return HELD
        s += v
    return _r(s)


def takeoff(villa):
    check_units(villa)
    axes = sum(r["axis_m"] for r in villa["runs"]) + sum(r["axis_m"] for r in villa.get("other_runs", []))
    if villa.get("band_axis_m") is not None and abs(axes - villa["band_axis_m"]) > 1e-6:
        raise RefusedInput(f"runs {axes:.4f} m do not conserve the band axis {villa['band_axis_m']} m (missing run?)")
    res = [run_takeoff(villa, r) for r in sorted(villa["runs"], key=lambda r: r["id"])]
    return {"runs": res,
            "totals": {"UPPER_GB_net_m3": total(res, "UPPER_GB_m3", "net"),
                       "UPPER_GB_at_most_m3": total(res, "UPPER_GB_m3", "at_most"),
                       "LOWER_GB_low_m3": total(res, "LOWER_GB_m3", "low"),
                       "LOWER_GB_high_m3": total(res, "LOWER_GB_m3", "high"),
                       "MASONRY_plane_m2": total(res, "MASONRY_m2", "plane"),
                       "MASONRY_plane_at_least_m2": total(res, "MASONRY_m2", "plane_at_least"),
                       "MASONRY_net_m2": total(res, "MASONRY_m2", "net")}}
