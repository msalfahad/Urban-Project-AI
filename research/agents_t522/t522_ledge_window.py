"""T-522: the HELD parts of an exposed-slab waterproofing zone (window run under a sill, a covered ledge and its
bounding face), measured from the drawings or narrowed to their physical cause. Rules R-T522-1 .. 4, any villa.

Research piece, unwired: it prepares zone inputs for WP_APPLICABILITY_RULES_V1.component_rows (engine/source/
wp_applicability_rules_v1.py, read only) and adds nothing that rule does not already state, except the one thing the
rule leaves to "a printed project detail" (the upturn height) and the evidence each run must carry.

  R-T522-1  WINDOW RUN BY THE PRINTED SILL. The sill height above the slab top under a window that sits on the zone's
            boundary is taken only from a printed dimension in an elevation or section that shows the window over that
            slab (source = drawing + view + dimension id). With it the run is an UPTURN (sill >= 0.20 m) or a
            WINDOW_TRANSITION (sill below) by R-WP-APPL-UPTURN-1; a sill without a cited source is refused; no source
            -> sill None -> the run stays HELD with its length shown (never 0, never a default sill).
  R-T522-2  A BOUNDING FACE IS SPLIT BY WHAT STANDS ON THE EDGE. A face drawn as one run (e.g. a curved bay) is split
            piece by piece by the element that stands on it: SOLID wall -> UPTURN; glazing whose frame stands on the
            slab (sill 0, from the elevation / section) -> WINDOW_TRANSITION (UP-WP-DOOR-001), never an upturn; glazing
            on a KERB at least the upturn height, with the section cited -> the kerb face carries the UPTURN and no
            transition is needed (NOT_APPLICABLE, section cited); a kerb without a cited section is refused. The pieces
            must sum to the run's length (residual stated, tolerance 1 mm).
  R-T522-3  A PRINTED UPTURN HEIGHT OVERRIDES UP-WP-003. Only with a cited detail; the m2 is recomputed with the printed
            height and the row records both the source and the 0.20 m it replaced. No detail -> 0.20 m (UP-WP-003).
  R-T522-4  A COVERED STRIP OPEN AT A SIDE IS NARROWED BY ITS GEOMETRY, NOT DECIDED. For a slab strip under a cover of
            clear height h whose open boundary is a straight cover edge, the strip's farthest point lies d_max behind
            that edge: any driven rain more than theta_c = atan(d_max / h) off vertical reaches all of it, rain at
            theta < theta_c wets the part within h tan(theta) of the edge. The table is evidence for the HELD row
            (cause: one exposure decision, binary above theta_c); it never becomes a quantity and the bound is the
            strip's measured area (never 0). Deciding the exposure needs a rule or a printed detail, not this table.

Units: metres in, m2 / lm / degrees out. Geometry for R-T522-4 is a shapely polygon in metres.
"""
from __future__ import annotations

import math

UPTURN_H_M = 0.20          # UP-WP-003 (owner Q-03 / Q-24); equals WP_APPLICABILITY_RULES_V1.UPTURN_H_M (asserted in tests)
TOL_LM = 0.001             # R-T522-2: pieces of one run reconcile to 1 mm


def _src_ok(src):
    return isinstance(src, dict) and bool(src.get("drawing")) and bool(src.get("view")) and bool(src.get("dimension"))


def window_run(run, lm, sill_m=None, source=None, evidence=None):
    """R-T522-1 -> one UNDER_WINDOW upturn run for component_rows. sill_m in metres above the slab TOP."""
    if sill_m is not None:
        if not _src_ok(source):
            raise ValueError(f"{run}: a sill height needs its printed source (drawing, view, dimension)")
        if sill_m < 0 or sill_m > 5.0:
            raise ValueError(f"{run}: sill {sill_m} m is not a sill height in metres")
    u = {"run": run, "lm": lm, "kind": "UNDER_WINDOW", "sill_above_slab_m": sill_m}
    if sill_m is not None:
        u["sill_source"] = dict(source)
    if evidence:
        u["evidence"] = list(evidence)
    return u


def split_face(run, lm_total, pieces):
    """R-T522-2. pieces: [{piece, lm, stands: SOLID | GLAZING_ON_SLAB | GLAZING_ON_KERB, kerb_m?, source?}] ->
    (upturn_runs for component_rows, extra rows NOT_APPLICABLE for kerbs, reconciliation)."""
    runs, na, s = [], [], 0.0
    for p in pieces:
        lm, st = p.get("lm"), p.get("stands")
        if lm is None or lm < 0:
            raise ValueError(f"{run}/{p.get('piece')}: piece length not measured")
        s += lm
        name = f"{run}:{p['piece']}"
        if st == "SOLID":
            runs.append({"run": name, "lm": lm, "kind": "SOLID"})
        elif st == "GLAZING_ON_SLAB":
            if not _src_ok(p.get("source")):
                raise ValueError(f"{name}: a frame on the slab needs the elevation / section cited")
            runs.append(window_run(name, lm, 0.0, p["source"]))
        elif st == "GLAZING_ON_KERB":
            k = p.get("kerb_m")
            if k is None or not _src_ok(p.get("source")):
                raise ValueError(f"{name}: a kerb needs its printed height and the section cited")
            if k >= UPTURN_H_M:
                runs.append({"run": name + ":kerb_face", "lm": lm, "kind": "SOLID"})
                na.append({"run": name, "component": "WINDOW_TRANSITION", "unit": "lm", "qty": 0.0,
                           "status": "NOT_APPLICABLE", "rule_basis": "R-T522-2 (frame on a kerb >= upturn height)",
                           "source": dict(p["source"]), "kerb_m": k})
            else:
                runs.append(window_run(name, lm, k, p["source"]))
        else:
            raise ValueError(f"{name}: unknown stand kind {st!r}")
    res = round(lm_total - s, 6)
    if abs(res) > TOL_LM:
        raise ValueError(f"{run}: pieces {s:.6f} lm do not reconcile to the run {lm_total:.6f} lm (residual {res})")
    return runs, na, {"run": run, "run_lm": round(lm_total, 6), "pieces_lm": round(s, 6), "residual_lm": res}


def apply_printed_upturn(rows, height_m=None, source=None):
    """R-T522-3: rows from component_rows; UPTURN rows re-heighted only with a cited detail."""
    if height_m is None:
        return [dict(r) for r in rows]
    if not _src_ok(source):
        raise ValueError("a printed upturn height needs its detail cited (drawing, view, dimension)")
    if not 0.0 < height_m < 1.0:
        raise ValueError(f"upturn height {height_m} m out of range")
    out = []
    for r in rows:
        r = dict(r)
        if r["component"] == "UPTURN" and r.get("length_lm") is not None:
            m2 = round(r["length_lm"] * height_m, 6)
            if r.get("qty") is not None:
                r["qty"] = m2
            if r.get("held_bound") is not None:
                r["held_bound"] = m2
            r["height_m"], r["height_replaced_m"], r["height_source"] = height_m, UPTURN_H_M, dict(source)
        out.append(r)
    return out


def covered_strip_exposure(strip, cover_edge, h_m, angles_deg=(0.0, 5.0, 10.0, 15.0, 30.0, 45.0)):
    """R-T522-4. strip: shapely Polygon (m); cover_edge: shapely LineString (the open boundary of the cover, m);
    h_m: clear height from the strip to the cover edge (m). Returns the narrowing table (never a quantity)."""
    if h_m is None or h_m <= 0:
        raise ValueError("cover height not established: no narrowing (the row stays HELD with its bound)")
    if strip is None or strip.is_empty or strip.area <= 0:
        raise ValueError("strip area not measured")
    pts = list(strip.exterior.coords)
    from shapely.geometry import Point
    dmax = max(cover_edge.distance(Point(p)) for p in pts)
    theta_c = math.degrees(math.atan2(dmax, h_m))
    tab = []
    for a in angles_deg:
        d = h_m * math.tan(math.radians(a))
        wet = strip.intersection(cover_edge.buffer(d, cap_style="flat")).area if d > 0 else 0.0
        tab.append({"theta_deg": a, "reach_m": round(d, 6), "wetted_m2": round(min(wet, strip.area), 6)})
    return {"area_m2": round(strip.area, 6), "h_m": h_m, "d_max_m": round(dmax, 6),
            "theta_c_deg": round(theta_c, 4), "table": tab, "status": "HELD",
            "cause": "one exposure decision (driven rain under the cover): above theta_c the whole strip is wetted",
            "never_a_quantity": True}


__all__ = ["window_run", "split_face", "apply_printed_upturn", "covered_strip_exposure", "UPTURN_H_M"]
