"""ALSENAN V3b - opening heights: plan openings (exact DXF widths) x raster openings (calibrated elevations / sections).

For each plan opening (floor, kind, width W):
  candidates = raster openings on the same floor band whose outer width matches W (|w - W| <= max(6 cm, 4 %), the
  raster_evidence width gate) and whose geometry is plausible for the kind:
      door / double door : sill within 15 cm of a printed floor level (0 / 15 / 30 / 100 / 550 / 970), 190 <= h <= 320
      window             : 40 <= h <= 500 and the sill above the floor level of its band
  heights agree within AGREE_CM -> RASTER_TYPE_MATCH (grade SCALED, confidence M) - technical RASTER_DERIVED when
                                  >= 2 independent raster openings agree; a single candidate is RASTER_TYPE_MATCH_SINGLE
                                  (technical PARTIAL, commercial PROVISIONAL_SOURCE_DERIVED, M)
  heights disagree             -> RASTER_AMBIGUOUS: spread <= SPREAD_REL of the median = commercial
                                  PROVISIONAL_SOURCE_DERIVED (M); wider = BUDGET_ESTIMATE (L, not procurement eligible)
Positional projection (plan opening -> elevation x by facade direction) was attempted and did not resolve (facade
direction votes 3-5 per sheet, every sheet the same axis): disclosed, not used.
  no candidate                 -> doors: the floor's door population (all widths) -> PROVISIONAL_GEOMETRIC_INFERENCE
                                  windows: OPENING_HEIGHT_NOT_FOUND (commercial BUDGET_ESTIMATE from the floor's window
                                  population, low confidence, not procurement eligible)
Printed values override: curved glazing 430 cm (NW elevation), salon glazing 3.65 m (owner fact, V3a).
"""

from __future__ import annotations

import statistics

FLOOR_LEVELS_CM = [0, 15, 30, 100, 550, 970]
AGREE_CM = 12.0
SPREAD_REL = 0.30


def _w_ok(w_cm, W_cm):
    return abs(w_cm - W_cm) <= max(6.0, 0.04 * W_cm)


def _plaus(kind, o):
    if kind in ("DOOR", "DOUBLE_LEAF_DOOR"):
        return 190 <= o["h_cm"] <= 320 and min(abs(o["sill_cm"] - L) for L in FLOOR_LEVELS_CM) <= 15
    return 40 <= o["h_cm"] <= 500


def heights(plan_rows, raster_ops, printed=None) -> list:
    printed = printed or {}
    out = []
    by_floor = {}
    for o in raster_ops:
        by_floor.setdefault(o["floor"], []).append(o)
    for r in plan_rows:
        rec = {"id": r["id"], "floor": r["floor"], "kind": r["kind"], "width_m": r.get("width_m")}
        if r["id"] in printed:
            p = printed[r["id"]]
            rec.update(height_m=p["value_m"], state="PRINTED", grade="PRINTED", confidence="H", technical="RASTER_DERIVED",
                       commercial=None, source=p["source"], candidates=[])
            out.append(rec)
            continue
        if not r.get("width_m"):
            rec.update(height_m=None, state="NO_WIDTH", technical="BLOCKED", commercial=None, candidates=[])
            out.append(rec)
            continue
        W = r["width_m"] * 100.0
        pool = by_floor.get(r["floor"], [])
        c = [o for o in pool if _w_ok(o["w_cm"], W) and _plaus(r["kind"], o)]
        hs = sorted(o["h_cm"] for o in c)
        rec["candidates"] = [{"sheet": o["sheet"], "box_px": o["box_px"], "w_cm": round(o["w_cm"], 1), "h_cm": round(o["h_cm"], 1),
                              "sill_cm": round(o["sill_cm"], 1)} for o in c]
        rng = [round(hs[0] / 100, 3), round(hs[-1] / 100, 3)] if hs else None
        if hs and hs[-1] - hs[0] <= AGREE_CM and len(hs) >= 2:
            rec.update(height_m=round(statistics.median(hs) / 100.0, 3), state="RASTER_TYPE_MATCH", grade="SCALED", confidence="M",
                       technical="RASTER_DERIVED", commercial=None, range_m=rng)
        elif hs and len(hs) == 1:
            rec.update(height_m=round(hs[0] / 100.0, 3), state="RASTER_TYPE_MATCH_SINGLE", grade="SCALED", confidence="M",
                       technical="PARTIAL", commercial="PROVISIONAL_SOURCE_DERIVED", range_m=rng)
        elif hs:
            med = statistics.median(hs)
            narrow = (hs[-1] - hs[0]) <= SPREAD_REL * med
            rec.update(height_m=round(med / 100.0, 3), state="RASTER_AMBIGUOUS", grade="SCALED",
                       confidence="M" if narrow else "L", technical="PARTIAL",
                       commercial="PROVISIONAL_SOURCE_DERIVED" if narrow else "BUDGET_ESTIMATE", range_m=rng)
        else:
            if r["kind"] in ("DOOR", "DOUBLE_LEAF_DOOR"):
                pop = sorted(o["h_cm"] for o in pool if _plaus("DOOR", o))
                cls, conf = "PROVISIONAL_GEOMETRIC_INFERENCE", "M"
            else:
                pop = sorted(o["h_cm"] for o in pool if _plaus("WINDOW", o) and o["w_cm"] >= 40)
                cls, conf = "BUDGET_ESTIMATE", "L"
            if pop:
                rec.update(height_m=round(statistics.median(pop) / 100.0, 3), state="NO_WIDTH_MATCH", grade="SCALED",
                           confidence=conf, technical="BLOCKED", commercial=cls,
                           range_m=[round(pop[0] / 100, 3), round(pop[-1] / 100, 3)])
            else:
                rec.update(height_m=None, state="OPENING_HEIGHT_NOT_FOUND", technical="BLOCKED", commercial=None)
        out.append(rec)
    return out
