"""LIFT_LANDING_CENSUS_V1 (T-475, research only; stdlib): the lift-marble pieces at EVERY landing of a lift, for any
villa. It reuses the T-413 rule module (LIFT_ENTRANCE_MARBLE_V1: band widths, union area, threshold W x D) for the
arithmetic and adds the census around it. Nothing here is wired into a method or edits a released / candidate line.

The physical element (ERS s.2.1). At a landing of a lift shaft there are, per landing DOOR:
  * B6-07 lift threshold: the marble piece across the clear opening, on the landing floor, top flush with the landing
    F.F.L. unless a step is drawn; width = drawn clear width, depth printed else the owner fallback 0.50 (UP-ELEV-005).
  * B6-06 lift surround: marble jambs + head on the landing wall face (UP-ELEV-002 / -003): band widths printed in a
    surround detail, else the owner default 0.50 where the drawn face holds it; area needs the door clear height.
  * The OPENING itself (a hole in the shaft wall): deducted whole from the landing face's skirting and wall finish,
    never a door (UP-DOOR-CLS-005), never jamb skirting (register LIFT DOOR GAP IN SKIRTING, T-441).

Rules (R-T475-1 .. 6):
  R-T475-1 CENSUS BY FLOOR, NOT BY STOREY COUNT. Every floor the shaft passes is surveyed: LANDING when its plan draws
           an opening in the shaft wall (a jamb pair) - one station per opening (R-T413-1); NO_LANDING when the plan
           draws the shaft wall unbroken or the shaft closed by a slab (with that evidence named); UNKNOWN when no plan
           of that floor shows the shaft. UNKNOWN is never copied from the floor below and never counted as 0
           stations: the census total is then HELD (lo = landings found, hi = + the UNKNOWN floors' door count bound).
           A roof is a landing only when a door / opening into an overrun is drawn there.
  R-T475-2 THRESHOLD LEVEL. The threshold top is the landing F.F.L. printed on that landing (FLUSH) when no step or
           level line is drawn across the opening; a printed level difference makes it STEP (the riser is then its own
           edge item, not in this module); no level printed on that landing -> UNKNOWN (no m2 changes, the relation is
           named, never assumed equal to another floor's).
  R-T475-3 THRESHOLD DEPTH MUST FIT THE LANDING. The depth (printed or the UP-ELEV-005 fallback) is checked against the
           landing depth printed / drawn in front of the opening (to the opposite wall or step): a depth larger than
           the landing is INFEASIBLE -> the area is HELD with the bound (0, W x landing depth], never the fallback and
           never 0. Landing depth not drawn (open hall) -> not limiting, recorded as such.
  R-T475-4 SURROUND DETAIL. A surround / landing-door elevation or detail that prints the band widths and the door
           clear height makes the surround DRAWING-CONFIRMED; without it the band widths follow R-T413-3 and the
           area stays HELD on the missing height (R-T413-4). A catalogue / typical value (e.g. a 2.10 m door) is never
           used: a height is accepted only with a drawing or supplier source naming it.
  R-T475-5 OPENING DEDUCTION, ONE OWNER PER PIECE. Per station the deduction matrix is fixed: skirting of the landing
           face - the clear width whole, 0 jamb skirting; landing face wall finish - the opening area AND the surround
           area once established (the surround is not painted); landing floor finish - the threshold's floor part
           (certain part + HELD position part, R-T413-6); door thresholds B3-04 / ARCH.THRESHOLD / profiles B3-07 /
           beads B4-09 - none (refused by R-T413-7).
  R-T475-6 STATION EQUIVALENCE. Stations may be priced as 'typical x n' only when width, band statuses, height status
           and landing depth status are all equal; otherwise every station is kept by id.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "agents_t413"))
import lift_entrance_marble_v1 as LM  # noqa: E402

MODEL = "LIFT_LANDING_CENSUS_V1"
LANDING, NO_LANDING, UNKNOWN = "LANDING", "NO_LANDING", "UNKNOWN"
FLUSH, STEP = "FLUSH", "STEP"
Refused = LM.Refused

CATALOGUE_WORDS = ("typical", "catalogue", "catalog", "standard", "usual", "freelancer")


def _m(name, v):
    return LM._metres(name, v)


def census(floors):
    """R-T475-1. floors: [{floor, state: LANDING|NO_LANDING|UNKNOWN, evidence, openings: [..]}] in vertical order."""
    out, held_floors, n = [], [], 0
    for f in floors:
        st = f.get("state")
        if st not in (LANDING, NO_LANDING, UNKNOWN):
            raise Refused(f"{f.get('floor')}: state {st!r} is not a census state")
        ev = (f.get("evidence") or "").strip()
        ops = f.get("openings") or []
        if st == LANDING:
            if not ops:
                raise Refused(f"{f['floor']}: LANDING with no opening drawn")
            if not ev:
                raise Refused(f"{f['floor']}: LANDING without the drawing evidence (jamb pair) named")
        elif st == NO_LANDING:
            if ops:
                raise Refused(f"{f['floor']}: NO_LANDING but openings are listed")
            if not ev:
                raise Refused(f"{f['floor']}: NO_LANDING needs its evidence (wall unbroken / shaft closed)")
        else:
            if ops:
                raise Refused(f"{f['floor']}: UNKNOWN floors list no openings (never copied from another floor)")
            if f.get("copied_from"):
                raise Refused(f"{f['floor']}: a floor's landing is never copied from {f['copied_from']}")
            held_floors.append(f["floor"])
        n += len(ops)
        out.append({"floor": f["floor"], "state": st, "evidence": ev, "openings": len(ops)})
    ids = LM.stations([{"floor": f["floor"], "doors": f["openings"]} for f in floors if f["state"] == LANDING])
    return {"floors": out, "stations": ids, "station_count": n,
            "status": LM.DRAWING if not held_floors else LM.HELD, "unknown_floors": held_floors}


def level_relation(ffl_printed, step_drawn=False, step_m=None):
    """R-T475-2."""
    if step_drawn:
        if step_m is None:
            return {"relation": STEP, "status": LM.HELD, "note": "step drawn, height not printed"}
        _m("step_m", step_m)
        return {"relation": STEP, "status": LM.DRAWING, "step_m": step_m}
    if ffl_printed is None:
        return {"relation": UNKNOWN, "status": LM.HELD, "note": "no F.F.L. printed on this landing"}
    return {"relation": FLUSH, "status": LM.DRAWING, "ffl": ffl_printed}


def threshold_fit(station_id, thr, landing_depth_m=None, landing_depth_source=None):
    """R-T475-3. thr = LM.threshold(...) record. Returns a copy with the fit applied."""
    _m(f"{station_id} landing_depth_m", landing_depth_m)
    rec = dict(thr)
    if landing_depth_m is None:
        rec["landing_depth"] = {"value": None, "status": "NOT_LIMITING", "source": landing_depth_source or
                                "open landing, no wall / step drawn in front within the depth"}
        return rec
    if landing_depth_m <= 0:
        raise Refused(f"{station_id}: landing depth must be positive")
    rec["landing_depth"] = {"value": landing_depth_m, "status": LM.DRAWING, "source": landing_depth_source}
    d = rec.get("depth_m")
    if d is not None and d > landing_depth_m + 1e-9:
        w = rec["width_m"]
        rec.update(depth_m=None, area_m2=None, status=LM.HELD,
                   missing=[f"INFEASIBLE_DEPTH: {d} m > {landing_depth_m} m landing in front of the opening"],
                   bound_m2=[0.0, LM._r(w * landing_depth_m)], floor_overlap_bound_m2=None)
    return rec


def surround_from_detail(station_id, *, clear_width_m, detail=None, faces=None, storey_height_m=None):
    """R-T475-4. detail: {left, top, right, clear_height_m, source} printed on a surround detail, or None.
    faces: {left, right} landing face available beside each jamb (m)."""
    faces = faces or {}
    if detail:
        src = detail.get("source") or ""
        if not src or any(w in src.lower() for w in CATALOGUE_WORDS):
            raise Refused(f"{station_id}: surround detail without a drawing / supplier source ({src!r})")
        bands = [LM.band_width(s, drawn_m=detail.get(s), available_m=faces.get(s)) if detail.get(s) is not None
                 else LM.band_width(s, available_m=faces.get(s), default_m=LM.SURROUND_DEFAULT_M,
                                    default_source=LM.SURROUND_SOURCE)
                 for s in ("left", "top", "right")]
        h = detail.get("clear_height_m")
    else:
        bands = [LM.band_width(s, available_m=faces.get(s), default_m=LM.SURROUND_DEFAULT_M,
                               default_source=LM.SURROUND_SOURCE) for s in ("left", "top", "right")]
        h = None
    rec = LM.surround(station_id, clear_width_m=clear_width_m, clear_height_m=h, storey_height_m=storey_height_m,
                      left=bands[0], top=bands[1], right=bands[2])
    rec["detail"] = (detail or {}).get("source") or "none printed"
    return rec


def clear_height(value, source):
    """R-T475-4: a door height is accepted only with a drawing / supplier source; a catalogue value is refused."""
    if value is None:
        return None
    _m("clear_height", value)
    if not source or any(w in source.lower() for w in CATALOGUE_WORDS):
        raise Refused(f"door clear height {value} without a drawing / supplier source ({source!r}) is refused")
    return value


def deduction_matrix(station_id, *, clear_width_m, opening_height_m=None, surround=None, thr=None):
    """R-T475-5: what each neighbouring trade takes out at this station (m / m2), held parts named, never 0 for held."""
    sk = {"trade": "SKIRTING (landing face)", "deduct_lm": LM._r(clear_width_m, 3), "jamb_skirting_lm": 0.0,
          "status": LM.DRAWING}
    wall_open = (LM._r(clear_width_m * opening_height_m) if opening_height_m is not None else None)
    wf = {"trade": "WALL FINISH (landing face paint / plaster)",
          "opening_m2": wall_open, "opening_status": LM.DRAWING if wall_open is not None else LM.HELD,
          "surround_m2": None if surround is None else surround.get("area_m2"),
          "surround_bound_m2": None if surround is None else surround.get("bound_m2"),
          "surround_status": None if surround is None else surround.get("status")}
    fl = {"trade": "FLOOR FINISH (landing)",
          "threshold_floor_part_bound_m2": None if thr is None else thr.get("floor_overlap_bound_m2"),
          "status": None if thr is None else thr.get("floor_overlap_status", LM.HELD)}
    none = {"trade": "B3-04 / ARCH.THRESHOLD / B3-07 / B4-09", "deduct": "none: no such piece at a lift opening",
            "status": "NOT_APPLICABLE"}
    return {"station_id": station_id, "rows": [sk, wf, fl, none]}


def equivalent(stations):
    """R-T475-6: True only if every station has the same width, band statuses, height status and depth status."""
    keys = []
    for s in stations:
        sur, thr = s["surround"], s["threshold"]
        keys.append((sur["clear_width_m"], tuple((b["status"], b["width_m"]) for b in sur["bands"]),
                     sur["clear_height_m"] is None, thr.get("landing_depth", {}).get("status"), thr["status"]))
    return len(set(keys)) == 1


def family_totals(stations):
    """Sum per family; a held station contributes its bound, never 0 (LM.totals semantics)."""
    sur = [s["surround"] for s in stations]
    thr = []
    for s in stations:
        t = dict(s["threshold"])
        if t.get("area_m2") is None and t.get("bound_m2"):
            t["floor_overlap_bound_m2"] = t["bound_m2"]
        thr.append(t)
    released_sur = LM._r(sum(r["area_m2"] for r in sur if r.get("area_m2") is not None))
    released_thr = LM._r(sum(r["area_m2"] for r in thr if r.get("area_m2") is not None))
    return {"surround": LM.totals(sur, "area_m2"), "surround_valued_part_m2": released_sur,
            "threshold": LM.totals(thr, "area_m2"), "threshold_valued_part_m2": released_thr,
            "front_edge_lm": LM._r(sum(s["threshold"]["front_edge_lm"] for s in stations), 3),
            "stations": len(stations)}
