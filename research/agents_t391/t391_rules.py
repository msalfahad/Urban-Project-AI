"""T-391 rules (pure, stdlib): ground slab and ground-beam residuals split into named causes in m3 (every villa).

R-T391-1  ONE PLAN, EACH PIECE ONCE. The ground plan inside the ground-beam network is partitioned into slab panels,
          beam strips, column pieces and shaft / pit pieces; each piece belongs to one member. A slab panel stops at the
          beam faces (convention C1: the ground beam is billed full depth from the slab top and owns its strip). A slab
          area that covers a beam strip as well as the beam's own line is DOUBLE and is refused here (check_partition).
R-T391-2  A BEAM DEPTH IS TAKEN ONCE. A ground-beam depth measured from the slab top already contains the slab
          thickness over the strip; booking the slab over that strip again is refused (beam_depth_basis).
R-T391-3  SLAB CAUSE SPLIT. engine_valued - other = (engine - own on the faces the engine values) - own panels inside a
          HELD engine cell x t (HELD named) - own panels the engine routes to another family x t (UNRESOLVED, named) -
          strips the other plate covers x t (the other side's double count) - the other area beyond the whole drawn
          network x t (unexplained). Every term is an area of the own partition times the printed thickness; the terms
          sum to the residual within 0.001 m3 or the remainder is printed (never absorbed).
R-T391-4  BEAM CAUSE SPLIT. With the other side measured as one section b x D over one lump length L:
          engine_valued - other = sum over valued runs of [(A_i - b_i L_i) D_i  (plan / end adjustments)
          + b_i L_i D_i - b L_i D  (section)] - b D sum(L_held)  (HELD named) - b D (L - sum L_engine)  (length basis).
          A lump length that cannot be split run by run is an UNTRACED remainder (unexplained), with the drawn bounds
          it lies between printed beside it; it is never closed as a rule difference by its sign alone.
R-T391-5  HELD NEVER 0. A held engine part adds nothing to the engine side, is printed with its bound and is never an
          agreement; a held value typed as 0 is refused. A held cell's bound covers only the slab panels inside it: a
          shaft, a pit or a beam strip inside the cell is not slab (bound_of_held_cell).
"""

from __future__ import annotations

TOL_M3 = 0.001


class RefusedT391(ValueError):
    pass


def _r6(x):
    return round(float(x) + 0.0, 6)


def check_partition(pieces):
    """pieces: [{"id", "kind": PANEL|BEAM|COLUMN|LIFT, "area_m2", "owner": line id or None}]; returns totals by kind.
    A piece with two owners, or a PANEL owned by a beam line, is refused (R-T391-1)."""
    seen, tot = {}, {}
    for p in pieces:
        if p["area_m2"] is None or p["area_m2"] < 0:
            raise RefusedT391(f"{p['id']}: area missing")
        if p["id"] in seen:
            raise RefusedT391(f"{p['id']}: piece counted twice (DOUBLE)")
        seen[p["id"]] = p
        owners = p.get("owners") or ([p["owner"]] if p.get("owner") else [])
        if len(owners) > 1:
            raise RefusedT391(f"{p['id']}: owned by {owners} (DOUBLE)")
        tot[p["kind"]] = tot.get(p["kind"], 0.0) + p["area_m2"]
    return {k: _r6(v) for k, v in tot.items()}


def slab_over_beam_overlap(slab_area_m2, beam_strip_m2, union_m2):
    """shared plan area = slab + strip - union; > 0 means the slab line also covers the beam's strip (DOUBLE)."""
    shared = slab_area_m2 + beam_strip_m2 - union_m2
    if shared > 1e-6:
        raise RefusedT391(f"slab over a beam strip not deducted: {shared:.4f} m2 counted twice (DOUBLE)")
    return 0.0


def beam_depth_basis(depth_from, slab_over_strip):
    """depth_from: 'SLAB_TOP' (the printed section from the slab top) or 'SLAB_SOFFIT'. R-T391-2."""
    if depth_from not in ("SLAB_TOP", "SLAB_SOFFIT"):
        raise RefusedT391(f"depth basis {depth_from!r} not printed")
    if depth_from == "SLAB_TOP" and slab_over_strip:
        raise RefusedT391("beam depth taken from the slab top and the slab booked over its strip: slab thickness twice")
    if depth_from == "SLAB_SOFFIT" and not slab_over_strip:
        raise RefusedT391("beam depth below the soffit and no slab over the strip: the strip's slab thickness is lost")
    return depth_from


def bound_of_held_cell(own_pieces_in_cell, t_m):
    """R-T391-5: the held cell's high bound = its own slab panels x t; shaft / beam / column pieces excluded."""
    if t_m is None or t_m <= 0:
        raise RefusedT391("thickness not printed: no bound")
    slab = sum(p["area_m2"] for p in own_pieces_in_cell if p["kind"] == "PANEL")
    other = sum(p["area_m2"] for p in own_pieces_in_cell if p["kind"] != "PANEL")
    return {"slab_m2": _r6(slab), "not_slab_m2": _r6(other), "high_m3": _r6(slab * t_m)}


def _held_guard(v, what):
    if v == 0 or v == 0.0:
        raise RefusedT391(f"{what}: a held part typed as 0 (HELD is blank, never 0)")


def slab_cause_split(*, t_m, engine_valued_m3, other_m3, own_valued_m2, engine_valued_m2, own_held_panels_m2,
                     own_other_family_m2, own_strips_m2, own_network_m2, other_area_m2):
    """R-T391-3. Areas from the own partition; returns the named terms (m3, engine - other) and the remainder."""
    if t_m is None or t_m <= 0:
        raise RefusedT391("thickness not printed")
    if own_held_panels_m2 is not None:
        if own_held_panels_m2 < 0:
            raise RefusedT391("negative held area")
    net = own_valued_m2 + (own_held_panels_m2 or 0) + own_other_family_m2 + own_strips_m2
    if abs(net - own_network_m2) > 1e-3:
        raise RefusedT391(f"own partition does not close: {net:.4f} vs network {own_network_m2:.4f} m2")
    if own_strips_m2 > 0 and other_area_m2 < own_network_m2 - 1e-6:
        # a plate smaller than the whole drawn network may stop at some beam faces: which strips it covers is not
        # established, so the strip term cannot be named
        raise RefusedT391("the other area is below the drawn network: strip double count not established")
    terms = {
        "engine_vs_own_on_valued_faces": _r6((engine_valued_m2 - own_valued_m2) * t_m),
        "held_cell_panels": _r6(-(own_held_panels_m2 or 0) * t_m),
        "panels_routed_to_other_family": _r6(-own_other_family_m2 * t_m),
        "strips_under_other_plate": _r6(-own_strips_m2 * t_m),
        "other_beyond_drawn_network": _r6(-(other_area_m2 - own_network_m2) * t_m),
    }
    residual = _r6(engine_valued_m3 - other_m3)
    rem = _r6(residual - sum(terms.values()))
    return {"residual_m3": residual, "terms_m3": terms, "remainder_m3": rem, "closes": abs(rem) <= TOL_M3}


def beam_cause_split(*, runs, other_b, other_d, other_length_m, drawn_bounds_m=None):
    """R-T391-4. runs: [{"id", "state": VALUED|HELD, "L_m", "b_m", "A_m2", "D_m", "value_m3", "group"}] (A = net plan,
    D = depth of a valued run; a HELD run has value None and no D). other_* = his one section and lump length."""
    plan = section = 0.0
    by_group = {}
    held_L = eng_L = valued = 0.0
    for r in runs:
        eng_L += r["L_m"]
        if r["state"] == "HELD":
            if r.get("value_m3") is not None:
                _held_guard(r["value_m3"], r["id"])
                raise RefusedT391(f"{r['id']}: a HELD run carries a value")
            held_L += r["L_m"]
            continue
        p = (r["A_m2"] - r["b_m"] * r["L_m"]) * r["D_m"]
        s = r["b_m"] * r["L_m"] * r["D_m"] - other_b * r["L_m"] * other_d
        if abs(r["A_m2"] * r["D_m"] - r["value_m3"]) > 1e-4:
            raise RefusedT391(f"{r['id']}: value {r['value_m3']} is not net plan x depth")
        plan += p
        section += s
        valued += r["value_m3"]
        g = by_group.setdefault(r.get("group", ""), {"runs": 0, "L_m": 0.0, "section_m3": 0.0, "plan_m3": 0.0})
        g["runs"] += 1
        g["L_m"] += r["L_m"]
        g["section_m3"] += s
        g["plan_m3"] += p
    other = other_b * other_d * other_length_m
    terms = {"plan_end_adjustments": _r6(plan), "section_on_valued_runs": _r6(section),
             "held_runs": _r6(-other_b * other_d * held_L),
             "length_basis_untraced": _r6(-other_b * other_d * (other_length_m - eng_L))}
    residual = _r6(valued - other)
    rem = _r6(residual - sum(terms.values()))
    out = {"residual_m3": residual, "terms_m3": terms, "remainder_m3": rem, "closes": abs(rem) <= TOL_M3,
           "engine_length_m": _r6(eng_L), "held_length_m": _r6(held_L),
           "groups": {k: {kk: (_r6(vv) if isinstance(vv, float) else vv) for kk, vv in v.items()}
                      for k, v in sorted(by_group.items())}}
    if drawn_bounds_m:
        lo, hi = drawn_bounds_m
        out["length_inside_drawn_bounds"] = lo - 1e-6 <= other_length_m <= hi + 1e-6
        out["drawn_bounds_m"] = [_r6(lo), _r6(hi)]
    return out
