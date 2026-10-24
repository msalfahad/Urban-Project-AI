"""T-265 GB_BAR_POPULATION_V1: ground-beam reinforcement by bar population from the PRINTED section of each member
(research, unwired; stdlib only; every villa).

The physical element first: a ground-beam RUN is one straight (or circular) concrete member between the faces of the
members it frames into (column / neck, pool or tank wall, beam at the same level). Its bars are those the printed
section names for THAT member family; nothing is borrowed from another family's section.

Rules (no exceptions):
  * A section is applied only to a member family it names (`applies_to`); any other use is refused.
  * Longitudinal steel = bar count x run length x d^2 / 162 (kg/m, the engine's D2_OVER_162 convention,
    engine/source/rebar_unit_mass.py). The run length is face to face: development / anchorage at the ends and bars
    through supports are NOT folded in, so the figure is a lower bound of the installed steel ('LOWER_BOUND').
  * A kg/m3 (or kg/m) allowance is refused as an input: steel comes from bars only.
  * Laps: only from a printed lap rule; a lap length without a source is refused. Without one, splices of bars longer
    than the stock length are listed as HELD procurement items (count only), never in the net.
  * '(T&B)' notation: its meaning is settled before arithmetic. A label set whose bars, as drawn, sit one label per
    layer (leader to that layer, dot count = label count) is read per layer; the literal 'every label in both
    layers' reading is kept only if it fits physically inside the section; otherwise it is refused (REJECTED reading).
  * Side bars 'n ø d / s': n bars per level (the drawn dots decide n per level), levels at a pitch not exceeding s
    between the top layer and the upper bottom row: levels = ceil(gap / s) - 1, computed over the whole envelope of
    unprinted cover and row spacing; released only when the count is the same at every corner of that envelope,
    else HELD with the candidate counts. A member whose depth is not established keeps its side bars HELD.
  * Stirrups 'ø d / s': COUNT range A = ceil(L / s) (the S5 lower bound) .. B = A + 1 (a stirrup at both faces);
    the stirrup MASS is HELD while the hook length is not printed (the loop-only kg at the printed minimum covers is
    reported as a reading, not a quantity).
  * Member states: APPLIES (section printed for it), CONFLICT (two printed readings disagree), NONE_PRINTED (no section
    for it), PLAIN (the drawing prints plain concrete: the member has NO rebar line, stated with its source).
    CONFLICT / NONE_PRINTED keep every component HELD with kg None; nothing is ever 0 by default.
"""
from __future__ import annotations

import math

POLICY_ID = "GB_BAR_POPULATION_V1"
APPLIES, CONFLICT, NONE_PRINTED, PLAIN = "APPLIES", "CONFLICT", "NONE_PRINTED", "PLAIN"
MEMBER_STATES = (APPLIES, CONFLICT, NONE_PRINTED, PLAIN)
RELEASED_LB = "DRAWING-CONFIRMED (LOWER_BOUND)"
CONFIRMED_COUNT = "DRAWING-CONFIRMED (COUNT)"
HELD = "HELD"
NO_REBAR = "NO_REBAR (PLAIN, printed)"
REFUSED_KEYS = ("kg_per_m3", "kg_m3", "steel_rate", "kg_per_m", "rate_kg")


def kg_per_m(d_mm):
    """D2_OVER_162 (engine/source/rebar_unit_mass.py): kg/m = d^2 / 162, d in mm."""
    if not isinstance(d_mm, (int, float)) or d_mm <= 0:
        raise ValueError(f"bar diameter must be a positive number of mm, got {d_mm!r}")
    return d_mm * d_mm / 162.0


UNIT_TO_M = {"m": 1.0, "cm": 0.01, "mm": 0.001}


def length_m(value, unit):
    """A run length in metres from a drawing value and its declared unit; an undeclared unit is refused."""
    if unit not in UNIT_TO_M:
        raise ValueError(f"length unit must be declared as one of {sorted(UNIT_TO_M)}, got {unit!r}")
    if not isinstance(value, (int, float)) or value <= 0:
        raise ValueError(f"length must be positive, got {value!r}")
    return value * UNIT_TO_M[unit]


def _refuse_rates(obj, where):
    for k in REFUSED_KEYS:
        if k in obj:
            raise ValueError(f"{where}: a steel rate ({k}) is refused; steel comes from the printed bars only")


def check_section(sec):
    """A printed section definition. Raises on anything unsourced or rate-based."""
    _refuse_rates(sec, f"section {sec.get('section_id')}")
    for k in ("section_id", "source", "applies_to", "b_m", "top", "bottom_rows", "stirrup"):
        if sec.get(k) in (None, "", []):
            raise ValueError(f"section {sec.get('section_id')!r}: {k} is required")
    if sec.get("lap") is not None and not sec["lap"].get("source"):
        raise ValueError(f"section {sec['section_id']}: a lap length without a printed source is refused")
    for layer in [sec["top"]] + list(sec["bottom_rows"]):
        for n, d in layer:
            if not (isinstance(n, int) and n > 0):
                raise ValueError(f"section {sec['section_id']}: bar count must be a positive integer")
            kg_per_m(d)
    return sec


def tb_reading(labels, drawn_per_layer, b_m, cover_m, stirrup_mm):
    """Meaning of a '(T&B)' label pair before arithmetic.

    labels: [(n, d, layer_pointed_to)] with layer 'TOP' / 'BOTTOM' (where the leader ends);
    drawn_per_layer: {'TOP': dots, 'BOTTOM': dots} counted on the section.
    Returns {'reading', 'top', 'bottom', 'rejected': [(reading, why)]}.
    """
    per_layer = {"TOP": [(n, d) for n, d, lay in labels if lay == "TOP"],
                 "BOTTOM": [(n, d) for n, d, lay in labels if lay == "BOTTOM"]}
    literal = [(n, d) for n, d, _ in labels]
    rejected = []
    fits_literal = layer_fits(literal, b_m, cover_m, stirrup_mm)
    per_ok = all(sum(n for n, _ in per_layer[k]) == drawn_per_layer.get(k) for k in ("TOP", "BOTTOM"))
    lit_ok = all(sum(n for n, _ in literal) == drawn_per_layer.get(k) for k in ("TOP", "BOTTOM"))
    if not fits_literal:
        rejected.append(("LITERAL_BOTH_LAYERS", "every label in both layers does not fit the section width "
                         f"{b_m:.2f} m at cover {cover_m:.3f} m"))
    elif not lit_ok:
        rejected.append(("LITERAL_BOTH_LAYERS", "the drawn dots do not show every label in both layers"))
    if per_ok and all(layer_fits(per_layer[k], b_m, cover_m, stirrup_mm) for k in ("TOP", "BOTTOM")):
        return {"reading": "PER_LAYER_BY_LEADER", "top": per_layer["TOP"], "bottom": per_layer["BOTTOM"],
                "rejected": rejected}
    if lit_ok and fits_literal:
        return {"reading": "LITERAL_BOTH_LAYERS", "top": literal, "bottom": literal, "rejected": rejected}
    return {"reading": CONFLICT, "top": None, "bottom": None,
            "rejected": rejected + [("PER_LAYER_BY_LEADER", "drawn dots or width do not support it")]}


def layer_fits(bars, b_m, cover_m, stirrup_mm, min_clear_mm=25.0):
    """Bars of one layer fit inside the stirrup with a clear spacing of at least max(25 mm, largest d)."""
    if not bars:
        return True
    inside = b_m * 1000.0 - 2 * cover_m * 1000.0 - 2 * stirrup_mm
    count = sum(n for n, _ in bars)
    width = sum(n * d for n, d in bars)
    clear = max(min_clear_mm, max(d for _, d in bars))
    return width + (count - 1) * clear <= inside + 1e-9


def side_levels(depth_m, top_d_mm, bottom_rows, stirrup_mm, pitch_m,
                cover_env=(0.025, 0.10), row_gap_env=(0.025, 0.05)):
    """Number of side-bar levels between the top layer and the upper bottom row at a pitch <= pitch_m, over the
    envelope of unprinted cover and clear row spacing. Returns (count or None, sorted candidate counts, gaps)."""
    if depth_m is None:
        return None, [], []
    db_up = max(d for _, d in bottom_rows[-1]) / 1000.0
    db_low = max(d for _, d in bottom_rows[0]) / 1000.0
    ds, dt = stirrup_mm / 1000.0, top_d_mm / 1000.0
    cands, gaps = set(), []
    for c in cover_env:
        for g_r in (row_gap_env if len(bottom_rows) > 1 else (0.0,)):
            y_top = c + ds + dt / 2
            if len(bottom_rows) > 1:
                y_up = c + ds + db_low + g_r + db_up / 2
            else:
                y_up = c + ds + db_up / 2
            gap = depth_m - y_top - y_up
            if gap <= 0:
                cands.add(0)
                gaps.append(round(gap, 4))
                continue
            cands.add(max(0, math.ceil(gap / pitch_m - 1e-9) - 1))
            gaps.append(round(gap, 4))
    cands = sorted(cands)
    return (cands[0] if len(cands) == 1 else None), cands, sorted(gaps)


def stirrup_counts(length_m, spacing_m):
    a = math.ceil(length_m / spacing_m - 1e-9)
    return a, a + 1


def loop_length(b_m, depth_m, cover_m, stirrup_mm):
    """Closed-loop centreline perimeter of a rectangular stirrup (hooks excluded)."""
    ds = stirrup_mm / 1000.0
    w, h = b_m - 2 * cover_m - ds, depth_m - 2 * cover_m - ds
    if w <= 0 or h <= 0:
        return None
    return 2 * (w + h)


def _row(member, comp, n, d, length, kg, status, basis):
    return {"member": member["member_id"], "family": member["family"], "component": comp, "n_bars": n,
            "dia_mm": d, "length_m": None if length is None else round(length, 4),
            "kg": None if kg is None else round(kg, 3), "status": status, "basis": basis}


def population(member, sec, stock_m=None, loop_covers=(0.07, 0.025)):
    """Component rows for one member. member: {member_id, family, L_m, depth_m (None = not established),
    state, column_zones ('NONE' | 'UNKNOWN_COUNT'), provenance}."""
    _refuse_rates(member, f"member {member.get('member_id')}")
    st = member.get("state")
    if st not in MEMBER_STATES:
        raise ValueError(f"member {member.get('member_id')}: state must be one of {MEMBER_STATES}")
    if st == PLAIN:
        return [_row(member, "ALL", None, None, member.get("L_m"), None, NO_REBAR,
                     member.get("provenance") or "plain concrete printed")]
    if st in (CONFLICT, NONE_PRINTED):
        return [_row(member, "ALL", None, None, member.get("L_m"), None, HELD,
                     f"{st}: {member.get('provenance') or 'no applicable printed section'}")]
    check_section(sec)
    if member["family"] not in sec["applies_to"]:
        raise ValueError(f"section {sec['section_id']} names {sec['applies_to']}, not {member['family']} "
                         f"({member['member_id']}): a typical section is never applied to a member it does not name")
    L = member.get("L_m")
    if not isinstance(L, (int, float)) or L <= 0:
        return [_row(member, "ALL", None, None, None, None, HELD, "run length not established")]
    rows = []
    for n, d in sec["top"]:
        rows.append(_row(member, "TOP", n, d, L, n * L * kg_per_m(d), RELEASED_LB,
                         "printed count x run face to face x d^2/162; ends / through-support lengths not included"))
    for i, layer in enumerate(sec["bottom_rows"], 1):
        for n, d in layer:
            rows.append(_row(member, f"BOTTOM_ROW_{i}", n, d, L, n * L * kg_per_m(d), RELEASED_LB,
                             "printed count x run face to face x d^2/162"))
    side = sec.get("side")
    if side:
        depth = member.get("depth_m")
        cnt, cands, gaps = side_levels(depth, max(d for _, d in sec["top"]), sec["bottom_rows"],
                                       sec["stirrup"][0], side["pitch_m"])
        if cnt is None:
            why = ("depth not established" if depth is None
                   else f"level count not invariant over the cover / row envelope: {cands}")
            rows.append(_row(member, "SIDE", None, side["dia_mm"], L, None, HELD, why))
        else:
            nb = cnt * side["bars_per_level"]
            rows.append(_row(member, "SIDE", nb, side["dia_mm"], L, nb * L * kg_per_m(side["dia_mm"]), RELEASED_LB,
                             f"{cnt} levels x {side['bars_per_level']} bars at pitch <= {side['pitch_m']} m "
                             f"(gaps {gaps[0]:.3f} .. {gaps[-1]:.3f} m, invariant)"))
    ds, s = sec["stirrup"]
    a, b = stirrup_counts(L, s)
    if member.get("column_zones", "NONE") == "UNKNOWN_COUNT":
        rows.append(_row(member, "STIRRUP_COUNT", None, ds, L, None, HELD,
                         f"columns pass through the run, count not printed: at most {a} .. {b} over the full run"))
    else:
        rows.append(_row(member, "STIRRUP_COUNT", f"{a}..{b}", ds, L, None, CONFIRMED_COUNT,
                         f"ceil(L / {s}) .. +1 (stirrup at both faces not printed)"))
    depth = member.get("depth_m", sec.get("depth_m"))
    loops = [loop_length(sec["b_m"], depth, c, ds) if depth else None for c in loop_covers]
    if None in loops:
        rows.append(_row(member, "STIRRUP_MASS", None, ds, None, None, HELD, "depth not established; hooks not printed"))
    else:
        lo = a * min(loops) * kg_per_m(ds)
        hi = b * max(loops) * kg_per_m(ds)       # with UNKNOWN_COUNT columns this is an upper reading only
        span = (f"at most {hi:.2f}" if member.get("column_zones", "NONE") == "UNKNOWN_COUNT"
                else f"{lo:.2f} .. {hi:.2f}")
        rows.append(_row(member, "STIRRUP_MASS", None, ds, None, None, HELD,
                         f"hook length not printed; loop-only reading {span} kg at covers "
                         f"{max(loop_covers)} .. {min(loop_covers)} m (not a quantity)"))
    if stock_m and L > stock_m:
        laps = math.ceil(L / stock_m) - 1
        nbars = sum(n for n, _ in sec["top"]) + sum(n for lay in sec["bottom_rows"] for n, _ in lay)
        rows.append(_row(member, "SPLICES (procurement)", nbars * laps, None, None, None, HELD,
                         f"run {L:.2f} m > stock {stock_m} m: at least {laps} splice(s) per longitudinal bar; "
                         + ("lap per " + sec["lap"]["source"] if sec.get("lap") else "no printed lap rule")
                         + "; never in the net"))
    return rows


def totals(rows):
    rel = sum(r["kg"] for r in rows if r["kg"] is not None and r["status"] == RELEASED_LB)
    held = [r for r in rows if r["status"] == HELD]
    return {"released_lower_bound_kg": round(rel, 3), "held_components": len(held),
            "no_rebar_members": sorted({r["member"] for r in rows if r["status"] == NO_REBAR})}
