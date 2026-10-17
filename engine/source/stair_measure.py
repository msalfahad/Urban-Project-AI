"""STAIR MEASURE (M4) - structural stair quantities from the drawn treads of a stair zone (generic; stdlib +
engine.source geometry). Nothing here takes a dimension from a project register or from finishing preferences.

A slab plan draws a stair as tread lines inside the cell the slab engine classifies STAIR_ZONE. From them:

    flight(segments, unit_m)    the run of parallel tread lines: FLIGHT (straight, regular pitch) or WINDER (lines
                                fanning about one centre): line count, going (straight: the pitch; winder: the pitch
                                on the walking line at mid width), width (the tread length), plan area of the run
    risers(n_lines, rule)       risers from the drawn lines: a line is a nosing, so a run of n lines has n treads and
                                n + 1 risers (LINES_PLUS_ONE), or n risers (LINES) - a named convention
    quantities(zone, rise_m, waist, rule)
                                riser height R = rise / risers (a diagnostic band 0.14 - 0.20 m: outside it the zone
                                holds only part of the stair and nothing is measured); concrete of the run
                                    straight: stair_geometry.straight_flight (waist under the step roots + steps)
                                    winder:   plan area x (waist / cos(pitch) + R / 2), an approximation labelled so
                                the flight's plan is risers - 1 treads (the drawn lines span one tread fewer when the
                                riser rule adds a riser), the rest of the zone (landings) a plate of the waist
                                thickness - the two never overlap (overflow_m2 > 0 means the flight outgrew the zone); finishes
                                (tread / riser areas) are returned for the finishing trades only
Every value carries its basis; the waist comes from the caller (printed, or a range for the exposure).
"""

from __future__ import annotations

import math

from engine.source import stair_geometry as SG

POLICY_ID = "STAIR_MEASURE_V1"
RISER_BAND_M = (0.14, 0.20)


def flight(segments, unit_m, *, pitch_m=(0.18, 0.40), min_lines=5):
    """segments: [{'a', 'b'}] tread lines inside the zone (drawing units). -> {kind, n_lines, going_m, width_m,
    run_m, plan_m2, centre?} or None."""
    segs = [s for s in segments if math.dist(s["a"], s["b"]) * unit_m >= 0.4]
    if len(segs) < min_lines:
        return None
    angs = [math.degrees(math.atan2(s["b"][1] - s["a"][1], s["b"][0] - s["a"][0])) % 180.0 for s in segs]
    spread = max(_ang_diff(a, angs[0]) for a in angs)
    if spread <= 3.0:                                         # parallel: a straight run
        ux, uy = math.cos(math.radians(angs[0])), math.sin(math.radians(angs[0]))
        nx, ny = -uy, ux
        offs = sorted(((s["a"][0] + s["b"][0]) / 2 * nx + (s["a"][1] + s["b"][1]) / 2 * ny) * unit_m for s in segs)
        gaps = [b - a for a, b in zip(offs, offs[1:]) if pitch_m[0] <= b - a <= pitch_m[1]]
        if len(gaps) + 1 < min_lines:
            return None
        going = sorted(gaps)[len(gaps) // 2]
        width = sorted(math.dist(s["a"], s["b"]) * unit_m for s in segs)[len(segs) // 2]
        n = len(gaps) + 1
        return {"kind": "FLIGHT", "n_lines": n, "going_m": going, "width_m": width, "run_m": (n - 1) * going,
                "plan_m2": (n - 1) * going * width, "basis": "parallel tread lines at a regular pitch"}
    try:
        (cx, cy), miss = SG.fan_centre([(i, s["a"], s["b"]) for i, s in enumerate(segs)])
    except SG.StairGeometryError:
        return None
    if miss * unit_m > 0.2:                                  # the lines do not fan about one point
        return None
    rs = [r for s in segs for r in (math.dist(s["a"], (cx, cy)), math.dist(s["b"], (cx, cy)))]
    r_in, r_out = min(rs) * unit_m, max(rs) * unit_m
    th = sorted(math.atan2((s["a"][1] + s["b"][1]) / 2 - cy, (s["a"][0] + s["b"][0]) / 2 - cx) for s in segs)
    gaps = [b - a for a, b in zip(th, th[1:])] + [th[0] + 2 * math.pi - th[-1]]
    span = 2 * math.pi - max(gaps)                           # the swept angle: the circle less its largest gap
    walk = (r_in + r_out) / 2
    n = len(segs)
    going = walk * span / max(1, n - 1)
    plan = 0.5 * span * (r_out ** 2 - r_in ** 2)
    if not (pitch_m[0] <= going <= pitch_m[1] * 1.5):
        return None
    return {"kind": "WINDER", "n_lines": n, "going_m": going, "width_m": r_out - r_in, "run_m": walk * span,
            "plan_m2": plan, "r_in_m": r_in, "r_out_m": r_out, "sweep_deg": math.degrees(span),
            "basis": "tread lines fanning about one centre; going on the walking line at mid width"}


def _ang_diff(a, b):
    d = abs(a - b) % 180.0
    return min(d, 180.0 - d)


def risers(n_lines, rule="LINES_PLUS_ONE"):
    return n_lines + 1 if rule == "LINES_PLUS_ONE" else n_lines


def quantities(zone_area_m2, run, rise_m, waist_m, *, riser_rule="LINES_PLUS_ONE"):
    """-> {state, risers, riser_m, flight_m3, landing_m3, total_m3, tread_m2, riser_m2, basis} for one waist value.
    state MEASURED or PARTIAL_STAIR (riser height outside the diagnostic band: the zone holds part of the stair)."""
    n_r = risers(run["n_lines"], riser_rule)
    R = rise_m / n_r if n_r else None
    out = {"risers": n_r, "riser_m": R, "kind": run["kind"]}
    if R is None or not (RISER_BAND_M[0] <= R <= RISER_BAND_M[1]):
        return dict(out, state="PARTIAL_STAIR", why=f"riser {R:.3f} m from rise {rise_m:.2f} m over {n_r} risers "
                                                     "lies outside 0.14 - 0.20 m" if R else "no risers")
    g, w = run["going_m"], run["width_m"]
    # the flight's plan: risers - 1 treads, each one drawn gap of the run (the drawn lines span n_lines - 1 gaps; a
    # riser rule that adds a riser adds its tread, which the landing must not count again); a winder never exceeds a
    # full turn
    plan = run["plan_m2"] * (n_r - 1) / max(1, run["n_lines"] - 1)
    if run["kind"] == "WINDER":
        plan = min(plan, math.pi * (run["r_out_m"] ** 2 - run["r_in_m"] ** 2))
    if run["kind"] == "FLIGHT":
        f = SG.straight_flight(n_r, R, g, w, waist_m)
        vf = f["STAIR_CONCRETE_VOLUME"]
        basis = "stair_geometry.straight_flight (waist under the step roots + steps)"
    else:
        theta = math.atan2(R, g)
        vf = plan * (waist_m / math.cos(theta) + R / 2.0)
        basis = "winder approximation: plan area x (waist / cos(pitch) + R / 2)"
    landing = max(zone_area_m2 - plan, 0.0)
    vl = landing * waist_m
    return dict(out, state="MEASURED", flight_m3=vf, flight_plan_m2=plan, landing_m2=landing, landing_m3=vl,
                total_m3=vf + vl, tread_m2=plan, riser_face_m2=n_r * R * w, basis=basis,
                overflow_m2=max(plan - zone_area_m2, 0.0))


def policy_record():
    return {"policy": POLICY_ID, "rule": "stair concrete from drawn treads, the storey rise and a waist the caller "
                                         "supplies (printed, or a range as exposure); a zone whose riser height "
                                         "falls outside 0.14 - 0.20 m holds part of a stair and is not measured"}
