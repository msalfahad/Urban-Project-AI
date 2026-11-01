"""T-417 rules: a straight flight's concrete (waist on the inclined length, steps, landings, side projections) and the
reconciliation of a freelancer's 'width x length x one thickness' flight row whose LENGTH differs from the drawn run
(pure, stdlib only; every villa). Research only: no candidate line, quantity or released cell is changed here.

R-T417-1  ONE FLIGHT, SEVERAL GEOMETRIES. A straight flight of n drawn risers on a drawn plan run L (first to last riser
          line), riser r, going g, lane w, printed waist t: steps = n x 1/2 r g w; waist = L x sec(a) x t x w with
          sec(a) = hypot(r, g) / g (the inclined length of the soffit, never the plan run, never run + rise); the
          developed stepped profile L + n r (treads + riser faces) is a FINISH / FORM length and never a concrete length.
R-T417-2  PLATE-EQUIVALENT THICKNESS. A row thickness that already contains the steps ('slab + steps') is a volume per
          PLAN m2 (drawn: (steps + waist) / (L w)); it is applied to the PLAN run only. Such a thickness laid on the
          developed profile L + n r adds n r x w x T of concrete that the drawn solid does not contain (the risers'
          height counted as more plan): refused as an engine method; in a reconciliation it is the term RISE_IN_LENGTH.
R-T417-3  LENGTH TERM SPLIT (extends R-T398-3; signs engine - freelancer). LENGTH = -(L_his - L) x w x T_his is split:
          (a) L_his = L + n r of THIS flight within MATCH_TOL -> RISE_IN_LENGTH = -n r w T_his, TRACED (inferred basis:
              both summands are drawn / section figures, no free parameter);
          (b) else L_his = L' + n' r' of a SIBLING flight bound to the SAME row unit (one length for 'count x unit')
              within MATCH_TOL -> RISE_IN_LENGTH = -n r w T_his of THIS flight + ONE_LENGTH = -(L_his - L - n r) w T_his,
              both TRACED; a sibling from another row is refused;
          (c) else LENGTH stays UNTRACED whole (never forced, never split by sign, never 'closest').
          A run, rise or riser borrowed from another storey / flight for THIS flight is refused (the flight's own count).
R-T417-4  LANDING DEPTH. A landing of his deeper than the drawn plate by exactly the width of a drawn beam band at the
          plate's edge (within MATCH_TOL) carries that band: OWNERSHIP = -(band width x his landing width x t_drawn)
          (the band is the beam's line, R-CONC-OWN-1); a drawn lane plate with no unit of his in the binding is COUNT;
          any other depth difference stays AREA UNTRACED.
R-T417-5  SIDE PROJECTION. A member outline standing proud into the flight lane (read on the SAME plan as the lane, T-412
          lesson) owns its intersection with the flight: exposure = proud plan strip x the flight's own vertical
          thickness integrated over the strip (waist t sec(a) + the step saw-tooth r (1 - frac(s / g))). Where the
          member's section is in CONFLICT (drawn vs schedule) the deduction is a HELD range 0 .. exposure, kept inside
          the flight value until the conflict closes and then deducted once, never in both.
"""

from __future__ import annotations

import math

MATCH_TOL = 0.0005   # m: an inferred basis must reproduce his figure to the half millimetre (no free parameter)
TOL = 1e-6


class Refused(ValueError):
    pass


def r6(x):
    return round(float(x) + 0.0, 6)


def _pos(name, v):
    if v is None or isinstance(v, bool) or not isinstance(v, (int, float)):
        raise Refused(f"{name}: missing or not a number (never defaulted, never 0)")
    if not v > 0:
        raise Refused(f"{name}: must be > 0, got {v}")
    if name.startswith(("riser", "going", "width", "run", "waist", "lane")) and v > 50:
        raise Refused(f"{name} = {v}: millimetres read as metres?")
    return float(v)


# ---------------------------------------------------------------- R-T417-1 flight
def flight(n_risers, riser, going, lane, run, waist, length_basis="INCLINED"):
    n = n_risers
    if not isinstance(n, int) or isinstance(n, bool) or n <= 0:
        raise Refused("the number of risers is a drawn count")
    r, g, w, L = (_pos(k, v) for k, v in (("riser", riser), ("going", going), ("lane", lane), ("run", run)))
    if waist is None:
        return {"steps_m3": r6(n * 0.5 * r * g * w), "waist_m3": None, "gross_m3": None, "state": "HELD",
                "sec": math.hypot(r, g) / g, "profile_m": r6(L + n * r)}
    t = _pos("waist", waist)
    sec = math.hypot(r, g) / g
    if length_basis == "INCLINED":
        Lw = L * sec
    elif length_basis in ("PLAN", "DEVELOPED"):
        raise Refused(f"waist on the {length_basis.lower()} length: the waist lies on the inclined soffit (R-T417-1)")
    else:
        raise Refused(f"unknown length basis {length_basis!r}")
    steps = n * 0.5 * r * g * w
    wst = Lw * t * w
    return {"steps_m3": r6(steps), "waist_m3": r6(wst), "gross_m3": r6(steps + wst), "sec": sec,
            "inclined_m": r6(Lw), "profile_m": r6(L + n * r), "state": "VALUED"}


def developed_profile(run, n_risers, riser):
    """Treads + riser faces of a flight (FINISH / FORM length, R-T417-1)."""
    if not isinstance(n_risers, int) or n_risers <= 0:
        raise Refused("the number of risers is a drawn count")
    return _pos("run", run) + n_risers * _pos("riser", riser)


def plate_equivalent(steps_m3, waist_m3, run, lane):
    """Drawn volume per plan m2 (R-T417-2)."""
    return (float(steps_m3) + float(waist_m3)) / (_pos("run", run) * _pos("lane", lane))


def engine_plate(thk_includes_steps, length_basis, run, n_risers, riser, lane, thk):
    """An engine quantity as one plate: only the plan run with a plate-equivalent thickness (R-T417-2)."""
    if thk_includes_steps and length_basis == "DEVELOPED":
        raise Refused("'slab + steps' thickness on the developed profile: the riser height counted as plan (R-T417-2)")
    if length_basis != "PLAN":
        raise Refused(f"a plate is laid on the plan run, not on the {length_basis!r} length")
    return r6(_pos("run", run) * _pos("lane", lane) * _pos("thickness", thk))


# ---------------------------------------------------------------- R-T417-3 length split
def length_terms(flight_id, row_id, his_len, his_w, his_t, run, n_risers, riser, siblings=()):
    """siblings: [{'id', 'row', 'run', 'n', 'riser'}] flights bound to his rows. Returns terms summing to the
    R-T398-3 LENGTH term -(L_his - run) x w_his x T_his (w = his width here: WIDTH is a separate term)."""
    Lh, w, T = (_pos(k, v) for k, v in (("his length", his_len), ("his width", his_w), ("his thickness", his_t)))
    L = _pos("run", run)
    total = -(Lh - L) * w * T
    rise = n_risers * _pos("riser", riser)
    own = L + rise
    if abs(Lh - own) <= MATCH_TOL:
        terms = [{"term": "RISE_IN_LENGTH", "m3": r6(-rise * w * T), "traced": True, "basis": "own run + rise"},
                 {"term": "ONE_LENGTH", "m3": r6(-(Lh - own) * w * T), "traced": True, "basis": "rounding to own"}]
    else:
        match = None
        for s in siblings:
            if s["id"] == flight_id:
                continue
            p = developed_profile(s["run"], s["n"], s["riser"])
            if abs(Lh - p) <= MATCH_TOL:
                if s.get("row") != row_id:
                    raise Refused(f"{flight_id}: his length matches {s['id']} of another row ({s.get('row')}): "
                                  "a sibling basis is admitted only within the same 'count x unit' row (R-T417-3)")
                match = s
                break
        if match is None:
            terms = [{"term": "LENGTH", "m3": r6(total), "traced": False, "basis": "no drawn basis"}]
        else:
            terms = [{"term": "RISE_IN_LENGTH", "m3": r6(-rise * w * T), "traced": True, "basis": "own run + rise"},
                     {"term": "ONE_LENGTH", "m3": r6(-(Lh - own) * w * T), "traced": True,
                      "basis": f"his one length = run + rise of {match['id']}"}]
    if abs(sum(t["m3"] for t in terms) - total) > 2e-6:
        raise Refused(f"{flight_id}: length terms do not close")
    return terms


def borrowed_check(flight_id, riser_source):
    if riser_source != flight_id:
        raise Refused(f"{flight_id}: riser / run borrowed from {riser_source} (R-T417-3)")
    return True


# ---------------------------------------------------------------- R-T417-4 landing depth
def landing_depth_terms(plate_id, his_depth, his_w, drawn_depth, drawn_w, t_drawn, edge_bands=()):
    """edge_bands: [{'id', 'width', 'owner'}] drawn beam bands at the plate's far edge. Terms of
    (A_drawn - A_his) x t_drawn for one plate bound to one unit of his."""
    Dh, wh, D, w, t = (_pos(k, v) for k, v in (("his depth", his_depth), ("his width", his_w), ("drawn depth",
                                                drawn_depth), ("drawn width", drawn_w), ("thickness", t_drawn)))
    total = (D * w - Dh * wh) * t
    for b in edge_bands:
        if b.get("owner") in (None, "STAIR"):
            raise Refused(f"{plate_id}: band {b.get('id')} owned by the stair: a beam band has its own line")
        if abs(Dh - (D + _pos("band width", b["width"]))) <= MATCH_TOL and abs(wh - w) <= MATCH_TOL:
            terms = [{"term": "OWNERSHIP", "m3": r6(-b["width"] * wh * t), "traced": True,
                      "basis": f"his depth = plate {D:.3f} + band {b['id']} {b['width']:.3f} ({b['owner']})"}]
            break
    else:
        terms = [{"term": "AREA", "m3": r6(total), "traced": False, "basis": "no drawn depth reproduces his"}]
    rest = total - sum(x["m3"] for x in terms)
    if abs(rest) > 2e-6:
        terms.append({"term": "AREA", "m3": r6(rest), "traced": False, "basis": "remainder"})
    return terms


def unbound_plate_term(plate_id, area, t_drawn):
    """A drawn lane plate with no unit of his in the binding (R-T417-4: COUNT)."""
    return {"term": "COUNT", "m3": r6(_pos("area", area) * _pos("thickness", t_drawn)), "traced": True,
            "basis": f"{plate_id}: drawn plate, no unit of his bound"}


# ---------------------------------------------------------------- R-T417-5 side projection
def sawtooth_integral(s0, s1, riser, going):
    """Integral over plan positions s0..s1 (m from the first riser line) of r (1 - frac(s / g))."""
    r, g = _pos("riser", riser), _pos("going", going)
    if s1 < s0:
        raise Refused("strip ends reversed")

    def F(s):                                              # primitive of (1 - frac(u)) du, u = s / g
        u = s / g
        k = math.floor(u)
        v = u - k
        return k * 0.5 + (v - v * v / 2)
    return r * g * (F(s1) - F(s0))


def projection_exposure(proud_w, s0, s1, riser, going, waist, n_risers, run):
    """m3 of the flight inside a member standing proud_w into the lane over plan positions s0 .. s1 (R-T417-5)."""
    pw = _pos("proud width", proud_w)
    if pw > 1.0:
        raise Refused("proud width > 1 m: a member across the lane is not a projection")
    L = _pos("run", run)
    if s0 < 0 or s1 > L + 1e-9:
        raise Refused("projection strip outside the drawn run: read the landing / beam owner instead")
    sec = math.hypot(riser, going) / going
    return r6(pw * ((s1 - s0) * _pos("waist", waist) * sec + sawtooth_integral(s0, s1, riser, going)))


def projection_deduction(exposure, section_state):
    if section_state == "CONFLICT":
        return {"state": "HELD", "low": 0.0, "high": r6(exposure), "in_flight_value": True}
    if section_state == "DRAWN_CONFIRMED":
        return {"state": "DEDUCT", "m3": r6(exposure), "in_flight_value": False}
    if section_state == "FLUSH":
        return {"state": "NONE", "m3": 0.0, "in_flight_value": False}
    raise Refused(f"unknown section state {section_state!r}")


def closure(contribution, terms):
    s = sum(t["m3"] for t in terms)
    if abs(s - contribution) > 2e-6:
        raise Refused(f"terms {s:.6f} != contribution {contribution:.6f}")
    traced = sum(t["m3"] for t in terms if t["traced"])
    return {"contribution_m3": r6(contribution), "traced_m3": r6(traced), "untraced_m3": r6(s - traced)}
