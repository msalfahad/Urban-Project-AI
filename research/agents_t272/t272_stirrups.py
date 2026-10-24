"""T-272 STIRRUP_CLOSURE_V1: closed links (stirrups) of a beam run, shape / count / mass, every facet from a print or
HELD (research, unwired; stdlib + engine.source.rebar_unit_mass; every villa).

The physical element first. A stirrup is one bent bar: straight legs and sides set by the beam section less the cover
on each face, bends of a radius, and a closure (two hooks of a stated angle with straight tails, or an overlap). Its
cut length needs EVERY one of these. Its count needs the spacing, the meaning of the spacing notation (an exact
pitch or a maximum c/c) and the END RULE (where the first and last stirrup sit relative to the supporting faces).

Rules (no exceptions):
  * A facet is PRINTED (value + drawing reference + a quantity provenance: the project drawing, a project-engineer
    claim or an owner-approved fallback), DRAWN_SHAPE_ONLY (drawn, not dimensioned), MINIMUM_ONLY (a printed lower
    limit such as 'cover >= 2.5 cm') or NOT_PRINTED. A code / textbook / practice value is never a quantity (owner
    AD-4: code hook values QA only; defect B20: no code edition may be assumed); offering one is refused.
  * A MINIMUM_ONLY cover makes b - 2c an UPPER envelope of the link, never its size: the cut length stays HELD.
  * A sharp-corner perimeter is not a bound of the bent link (a bend of radius R shortens each corner by
    (2 - pi/2) R, the hooks add an unknown length): it is reported only as a QA reading, never as kg.
  * Count over the clear span between the supporting faces, zone by zone. With the end rule printed and the spacing
    meaning established the count is exact. Otherwise it is HELD with its envelope:
        low  = the faces themselves act as the end ties and every gap <= its zone spacing (first stirrup at up to a
               full spacing from the face): single zone ceil(L / s) - 1;
        high = a stirrup at each face and every gap <= its zone spacing: ceil(L / s) + 1;
        the 'half-spacing' reading ceil(L / s) (first stirrup within s / 2 of the face; the frozen S5 'lower bound',
        T-265 A) is reported beside, as a reading of an unprinted end rule, not a bound.
  * A curved run is counted on the arc of the leg the spacing is measured on; if that is not printed the envelope
    runs from the inner-face arc (low) to the outer-face arc (high).
  * Unit mass from engine/source/rebar_unit_mass (project method). Mass = count x cut length x kg/m only when the
    count AND the cut length are established; otherwise HELD (never 0, never a range in the BOQ).
  * Design flags (designer items, never resolved by choosing a value): a printed minimum cover that leaves no core
    (2c + 2d_link >= b), and a closed link drawn with no closure (no hook, no overlap).
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from engine.source import rebar_unit_mass as UM  # noqa: E402

POLICY_ID = "STIRRUP_CLOSURE_V1"
PRINTED, SHAPE_ONLY, MINIMUM_ONLY, NOT_PRINTED = "PRINTED", "DRAWN_SHAPE_ONLY", "MINIMUM_ONLY", "NOT_PRINTED"
FACET_STATES = (PRINTED, SHAPE_ONLY, MINIMUM_ONLY, NOT_PRINTED)
QUANTITY_PROVENANCE = ("PROJECT_SOURCE", "PROJECT_ENGINEER_CLAIM", "OWNER_APPROVED_FALLBACK")
REFUSED_PROVENANCE = ("CODE_OR_EXTERNAL", "PRACTICE_DEFAULT", "CLAUDE_ENGINEERING_ANALYSIS", "FREELANCER")
REFUSED_KEYS = ("kg_per_m3", "kg_m3", "steel_rate", "rate_kg", "hook_default", "default_hook_d", "waste_pct")
HELD, CONFIRMED, QA_ONLY = "HELD", "DRAWING-CONFIRMED", "QA_ONLY (not a quantity, not a bound)"
EXACT, MAXIMUM = "EXACT", "MAXIMUM"
UNIT_MASS_CFG = {"method": UM.D2_OVER_162, "authority": "project unit-mass method (engine D2_OVER_162)"}
EPS = 1e-9


class StirrupInputError(ValueError):
    pass


# ----------------------------------------------------------------------------------------------- facets
def facet(state, value=None, ref=None, provenance="PROJECT_SOURCE", unit="m"):
    """One shape facet. PRINTED and MINIMUM_ONLY carry a value and a reference; a refused provenance raises."""
    if state not in FACET_STATES:
        raise StirrupInputError(f"facet state must be one of {FACET_STATES}, got {state!r}")
    if provenance in REFUSED_PROVENANCE:
        raise StirrupInputError(f"a {provenance} value is never a quantity input (owner AD-4, defect B20)")
    if state in (PRINTED, MINIMUM_ONLY):
        if value is None or ref is None:
            raise StirrupInputError(f"a {state} facet needs a value and its drawing reference")
        if provenance not in QUANTITY_PROVENANCE:
            raise StirrupInputError(f"provenance {provenance!r} cannot carry a quantity; use one of {QUANTITY_PROVENANCE}")
        if unit not in ("m", "cm", "mm", "d", "deg"):
            raise StirrupInputError(f"facet unit must be declared (m / cm / mm / d / deg), got {unit!r}")
    return {"state": state, "value": value, "ref": ref, "provenance": provenance, "unit": unit}


def _to_m(f, d_mm):
    """A PRINTED / MINIMUM_ONLY length facet in metres ('d' = multiples of the link diameter)."""
    v, u = f["value"], f["unit"]
    if u == "m":
        return float(v)
    if u == "cm":
        return float(v) / 100.0
    if u == "mm":
        return float(v) / 1000.0
    if u == "d":
        return float(v) * d_mm / 1000.0
    raise StirrupInputError(f"a length facet cannot be in {u!r}")


def _check_refused(obj):
    bad = [k for k in obj if k in REFUSED_KEYS]
    if bad:
        raise StirrupInputError(f"refused inputs (steel comes from bars and printed facets only): {bad}")


# ----------------------------------------------------------------------------------------------- count
def _zone_at(zones, x):
    """Spacing of the zone containing x (zones: [(length, spacing)], consecutive from 0)."""
    a = 0.0
    for length, s in zones:
        if x < a + length - EPS:
            return s, a + length
        a += length
    return zones[-1][1], a


def _admissible(zones, x, y):
    """A gap [x, y] is admissible when it does not exceed the spacing of any zone it lies in."""
    a = 0.0
    for length, s in zones:
        za, zb = a, a + length
        if zb > x + EPS and za < y - EPS and y - x > s + EPS:
            return False
        a = zb
    return True


def _next(zones, x):
    """Farthest admissible next stirrup position from x (a gap entering a finer zone is limited by its spacing; it
    may instead stop at that zone's start)."""
    s_here, _ = _zone_at(zones, x)
    cand = x + s_here
    a = 0.0
    for length, s in zones:
        za = a
        if x + EPS < za < cand - EPS and s < cand - x - EPS:
            cand = max(za, x + s)
        a += length
    return cand


def _min_points(zones, start, end):
    """Fewest stirrups strictly between anchors at `start` and `end` (a face or a fixed stirrup) so that no gap
    exceeds its zone spacing. Greedy farthest step is optimal for this interval cover."""
    total = sum(z[0] for z in zones)
    if end > total + EPS or start < -EPS or end < start:
        raise StirrupInputError("anchors outside the run")
    n, x = 0, start
    while not _admissible(zones, x, end):
        x = _next(zones, x)
        n += 1
    return n


def count_envelope(zones, end_offset=None, spacing_meaning=None):
    """Stirrup count over a clear span made of consecutive spacing zones [(length_m, spacing_m)].

    end_offset: a PRINTED facet (first / last stirrup from the face, same at both ends) or None.
    spacing_meaning: EXACT, MAXIMUM, or None (not established for this element type).
    Returns {'status', 'count' (only when established), 'low', 'half_spacing_reading', 'high', 'basis'}.
    """
    if not zones:
        raise StirrupInputError("no spacing zone")
    for length, s in zones:
        if not (isinstance(length, (int, float)) and length > 0 and isinstance(s, (int, float)) and s > 0):
            raise StirrupInputError(f"zone length and spacing must be positive, got {(length, s)!r}")
    L = sum(z[0] for z in zones)
    low = _min_points(zones, 0.0, L)
    high = _min_points(zones, 0.0, L) + 2 if L > EPS else 0
    single = len(zones) == 1
    half = math.ceil(L / zones[0][1] - EPS) if single else None
    out = {"length_m": round(L, 6), "zones": [list(z) for z in zones], "low": low, "half_spacing_reading": half,
           "high": high, "count": None, "status": HELD}
    if end_offset is None or end_offset.get("state") != PRINTED:
        out["basis"] = "end rule (first stirrup from the face) not printed: count HELD inside [low, high]"
        return out
    e = _to_m(end_offset, 8)
    if 2 * e >= L - EPS:
        out["basis"] = f"printed end offset {e} m leaves no room for two end stirrups on {L} m: designer item"
        return out
    if spacing_meaning == MAXIMUM:
        n = 2 + _min_points(zones, e, L - e)
    elif spacing_meaning == EXACT and single:
        n = math.floor((L - 2 * e) / zones[0][1] + EPS) + 1
    else:
        out["basis"] = ("end offset printed but the spacing meaning is not established for this element type "
                        "(exact pitch or maximum c/c): count HELD inside [low, high]")
        return out
    out.update(count=n, status=CONFIRMED, basis=f"end offset {e} m ({end_offset['ref']}), spacing {spacing_meaning}")
    return out


def curved_count_envelope(theta_rad, r_in, r_out, spacing, spacing_radius=None):
    """A circular run of sweep theta between the inner and outer faces. With the radius the spacing is measured on
    printed, the run is counted on that arc (end rule still applies); else low on the inner-face arc and high on the
    outer-face arc."""
    if not (0 < r_in < r_out) or theta_rad <= 0:
        raise StirrupInputError("curved run needs 0 < r_in < r_out and a positive sweep")
    if spacing_radius is not None:
        if not (r_in <= spacing_radius <= r_out):
            raise StirrupInputError("the spacing radius must lie inside the section")
        env = count_envelope([(theta_rad * spacing_radius, spacing)])
        env["basis"] = f"spacing on r = {spacing_radius} m; " + env["basis"]
        return env
    inner = count_envelope([(theta_rad * r_in, spacing)])
    outer = count_envelope([(theta_rad * r_out, spacing)])
    return {"length_m": None, "low": inner["low"], "high": outer["high"], "count": None, "status": HELD,
            "half_spacing_reading": None, "inner_arc_m": round(theta_rad * r_in, 6),
            "outer_arc_m": round(theta_rad * r_out, 6),
            "basis": "curved run: radius the spacing is measured on not printed and end rule not printed: count HELD "
                     "from the inner-face arc (low) to the outer-face arc (high)"}


# ----------------------------------------------------------------------------------------------- cut length
def cut_length(shape):
    """Cut length (m) of one closed rectangular link, or None with the HELD facets named.

    shape: {'b_m', 'h_m' (section, printed), 'd_mm' (link bar), 'cover': facet, 'bend_radius': facet (centreline,
    or unit 'd' for multiples of d), 'hook_angle': facet (deg), 'hook_ext': facet (straight tail each end),
    'closure': 'HOOKS' | 'NONE_DRAWN'}.
    L = 2a + 2c' - 8R + R (3 pi / 2 + 2 theta) + 2e, a / c' = centreline side lengths (outer link size - d),
    R = centreline bend radius, theta = hook angle in rad, e = tail. 135-degree hooks: 2a + 2c' + (3 pi - 8) R + 2e.
    """
    _check_refused(shape)
    held = []
    d = shape["d_mm"]
    cov, rad, ang, ext = shape["cover"], shape["bend_radius"], shape["hook_angle"], shape["hook_ext"]
    if shape.get("closure") != "HOOKS":
        held.append("closure: no hook or overlap drawn on the closed link (designer item)")
    if cov["state"] != PRINTED:
        held.append("cover printed as a minimum only: b - 2c is an upper envelope of the link, not its size"
                    if cov["state"] == MINIMUM_ONLY else "cover not printed")
    if rad["state"] != PRINTED:
        held.append("bend radius / mandrel not printed")
    if ang["state"] != PRINTED:
        held.append("hook angle drawn, not printed" if ang["state"] == SHAPE_ONLY else "hook angle not printed")
    if ext["state"] != PRINTED:
        held.append("hook extension (tail) not printed (owner AD-4: blocked unless the project dimensions it)")
    if held:
        return None, held
    c = _to_m(cov, d)
    a = shape["b_m"] - 2 * c - d / 1000.0
    cc = shape["h_m"] - 2 * c - d / 1000.0
    if a <= 0 or cc <= 0:
        return None, ["printed cover leaves no link core: designer item"]
    R = _to_m(rad, d)
    theta = math.radians(float(ang["value"]))
    e = _to_m(ext, d)
    L = 2 * a + 2 * cc - 8 * R + R * (1.5 * math.pi + 2 * theta) + 2 * e
    return L, []


def sharp_perimeter_qa(b_m, h_m, d_mm, cover_m):
    """QA reading only: centreline sharp-corner perimeter at a given cover, no hooks. Not a bound of the bent link."""
    a = b_m - 2 * cover_m - d_mm / 1000.0
    c = h_m - 2 * cover_m - d_mm / 1000.0
    if a <= 0 or c <= 0:
        return None
    return 2 * (a + c)


def design_flags(shape, cover_cases_m):
    """Designer flags: for each printed minimum cover case, does a link core remain?"""
    flags = []
    d = shape["d_mm"] / 1000.0
    for label, c in cover_cases_m.items():
        core = shape["b_m"] - 2 * c - 2 * d
        if core <= EPS:
            flags.append(f"cover {label} {c} m leaves no core in b {shape['b_m']} m (2c + 2d_link >= b): designer item")
    if shape.get("closure") != "HOOKS":
        flags.append("closed link drawn with no closure (no hook, no overlap): designer item")
    return flags


# ----------------------------------------------------------------------------------------------- mass
def stirrup_run(run_id, family, count_env, shape, qa_cover_m=None):
    """One run's stirrup record: count, cut length, mass (kg only when count and cut length are established)."""
    d = shape["d_mm"]
    kgm = UM.kg_per_m(d, UNIT_MASS_CFG)
    L, held = cut_length(shape)
    rec = {"run": run_id, "family": family, "d_mm": d, "kg_per_m": round(kgm, 6),
           "count_low": count_env["low"], "count_half_spacing_reading": count_env.get("half_spacing_reading"),
           "count_high": count_env["high"], "count": count_env["count"], "count_status": count_env["status"],
           "count_basis": count_env["basis"], "cut_length_m": None if L is None else round(L, 6),
           "cut_length_status": HELD if L is None else CONFIRMED, "cut_length_held": held,
           "kg": None, "kg_status": HELD}
    if L is not None and count_env["count"] is not None:
        rec["kg"] = round(count_env["count"] * L * kgm, 6)
        rec["kg_status"] = CONFIRMED
    if qa_cover_m is not None:
        p = sharp_perimeter_qa(shape["b_m"], shape["h_m"], d, qa_cover_m)
        rec["qa_sharp_perimeter_m"] = None if p is None else round(p, 6)
        rec["qa_kg_at_high_count_no_hooks"] = None if p is None else round(count_env["high"] * p * kgm, 6)
        rec["qa_status"] = QA_ONLY
    return rec
