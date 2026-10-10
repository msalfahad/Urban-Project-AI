"""STAIR (M2, generic, light) - one straight flight from a floor-to-floor rise and a COUNTED riser number: geometry,
marble finishes by the Urban Projects library rules, and the concrete as an exposure range while the waist is not
established. Stdlib. Scenarios with different riser counts are reported side by side; nothing here picks one.

    riser R = rise / n (a counted n, never derived from a "typical" rise: UP-STAIR-009 is a diagnostic only)
    treads = n - 1 on a straight flight (the top riser arrives at the landing / floor)
    going total = treads x going
    marble: tread 30 mm (UP-STAIR-006), landing 20 mm (UP-STAIR-007); bedding a range (20-30 mm by default);
            visible riser = R - tread marble thickness (UP-STAIR-003); tread / riser / landing are m2, the commercial
            step basis is lm (UP-STAIR-004 / -008), never summed. The going and the counts come from the drawing or
            the owner (UP-STAIR-002); typical values are diagnostics only.
    concrete per metre of width: waist slab on the inclined length + the step triangles; the waist is a range
            (the exposure), UNRESOLVED until a section prints it
"""

from __future__ import annotations

import math

POLICY_ID = "STAIR_GENERIC_V1"
TREAD_MARBLE_M = 0.030          # UP-STAIR-006
LANDING_MARBLE_M = 0.020        # UP-STAIR-007
SANITY_RISE_M = (0.155, 0.165)  # UP-STAIR-009 - diagnostic only, produces no quantity


def flight(rise_m, n_risers, going_m, *, width_m=1.0, waist_range_m=(0.15, 0.20), bedding_range_m=(0.02, 0.03),
           landing_m2=0.0):
    if n_risers < 2 or rise_m <= 0 or going_m <= 0:
        raise ValueError("a flight needs a positive rise, a positive going and at least two risers")
    R = rise_m / n_risers
    treads = n_risers - 1
    run = treads * going_m
    slope = math.atan2(R, going_m)
    incl = math.hypot(run, treads * R)                       # the soffit line under the treads
    tri = treads * R * going_m / 2.0                         # step triangles, per m of width
    conc = {f"waist_{w:.3f}": width_m * (incl * w + tri) for w in waist_range_m}
    tread_m2 = treads * going_m * width_m
    visible = R - TREAD_MARBLE_M                             # UP-STAIR-003
    riser_m2 = n_risers * visible * width_m
    bed = {f"bedding_{b:.3f}": (tread_m2 + landing_m2) * b for b in bedding_range_m}
    return {
        "policy": POLICY_ID, "rise_m": rise_m, "n_risers": n_risers, "riser_m": R, "treads": treads,
        "going_m": going_m, "run_m": run, "pitch_deg": math.degrees(slope), "inclined_m": incl,
        "sanity": "INSIDE_TYPICAL_RANGE" if SANITY_RISE_M[0] <= R <= SANITY_RISE_M[1] else "OUTSIDE_TYPICAL_RANGE",
        "blondel_2R_plus_G_m": 2 * R + going_m,
        "marble": {"tread_m2": tread_m2, "tread_thickness_m": TREAD_MARBLE_M, "visible_riser_m": visible,
                   "riser_m2": riser_m2,
                   "landing_m2": landing_m2, "landing_thickness_m": LANDING_MARBLE_M,
                   "step_commercial_lm": n_risers * width_m, "bedding_m3": bed},
        "concrete_exposure_m3": {"low": min(conc.values()), "high": max(conc.values()), "by_waist": conc,
                                 "state": "UNRESOLVED_WAIST_NOT_ESTABLISHED"},
        "rules": ["UP-STAIR-002", "UP-STAIR-003", "UP-STAIR-004", "UP-STAIR-006", "UP-STAIR-007", "UP-STAIR-008",
                  "UP-STAIR-009"],
    }


def scenarios(rise_m, counts, going_m, **kw):
    """the same rise under several counted riser numbers, side by side (no choice is made)."""
    return [flight(rise_m, n, going_m, **kw) for n in counts]


def policy_record():
    return {"policy": POLICY_ID, "rule": "riser from a counted number only; scenarios side by side; waist an "
                                         "exposure range until printed; finishes per the rule library"}
