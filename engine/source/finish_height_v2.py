"""ARCHITECTURAL FINISH HEIGHT V2 (T-081) - plaster, paint and wall-tile heights of ONE room from printed values and
owner rules only. A new version beside finish_height.py (V1, unchanged): V1 subtracts a 0.150 m ceiling allowance
(URBAN-PAINT-TO-FINISHED-CEILING@v1) and register V3 offers a 0.10 m floor build-up fallback
(URBAN-RESIDENTIAL-FLOOR-BUILDUP-FALLBACK@v1); owner answer Q-14 (2026-10-19) refuses both: "Do not subtract an assumed
floor build-up or false-ceiling depth; use elevations and sections. A false ceiling does not mean the wall above gets no
plaster or paint. A missing value holds only the affected quantity." Read-only, additive: no method version reads this
module yet, so no quantity changes.

Inputs (each value a record with its state and source, never a bare number):
  room      room_levels.room_levels() room record (PRINTED level, else every height HELD: ROOM_LEVEL_HELD)
  zone      the section_binding floor-report zone of that level (room_levels.zone_of): ffl, floor_to_floor, soffit,
            false_ceiling, next_slab_top (heights above the F.F.L.), slab_thickness, clear_height
  term      finish_height.termination() of the wall line: SLAB_SOFFIT, BEAM_SOFFIT (D_cm of a bound, scheduled beam,
            measured from the slab top) or UNKNOWN
  texts     the texts printed inside the room (element annotations: PLASTER TO 3.20, C.H. 2.90, TILES TO 2.40 ...)
  buildup_above   the floor build-up of the floor above (F.F.L. above - its slab top), accepted only as PRINTED or a
            PROJECT_FACT with authority and source drawing; an URBAN_FALLBACK / ASSUMED value is refused
Accepted value states: PRINTED, PRINTED_DIMENSION, PRINTED_LEVELS, DERIVED_FROM_PRINTED_LEVELS, PROJECT_FACT (with
authority and source) and OWNER_RULE (the Q-14 0.16 m structural slab only).

Heights (UP-HGT-001 evidence order; same-rank candidates that differ by more than 5 mm -> CONFLICT, no value):
  PLASTER   to the structural soffit (U/S SLAB or beam soffit) above the F.F.L.:
              1 ELEMENT_ANNOTATION  a PLASTER height printed in the room
              3 SECTION             SLAB: the printed soffit; or the printed next slab top - slab thickness
                                    BEAM: the printed next slab top - D (or the printed soffit + slab thickness - D)
              4 DERIVED             floor-to-floor - build-up above - (slab thickness | D); the build-up above must be
                                    printed or a project fact: otherwise HELD (FLOOR_BUILDUP_ABOVE_NOT_PRINTED)
            UNKNOWN termination -> only rank 1, else HELD (TERMINATION_UNKNOWN)
  PAINT     to the finished ceiling:
              1 ELEMENT_ANNOTATION  a ceiling / clear height printed in the room (arch_v28 CEILING_HEIGHT)
              3 SECTION             the printed F.C.L. or CLEAR HEIGHT of the zone
            otherwise HELD (CEILING_LEVEL_NOT_PRINTED): never floor-to-floor - build-up - slab - allowance.
            applies only to dry rooms (UP-FIN-PAINT-001: no paint over full-height wall porcelain)
  WALL_TILE wet rooms: a TILE height printed in the room; else UP-FIN-WALL-001 full height = the paint height
            (HELD when the paint height is held); dry rooms: NOT_APPLICABLE
  ABOVE_CEILING  dry room with both heights: the wall band between the finished ceiling and the soffit; its plaster is
            in PLASTER (owner Q-14); whether it is painted is not settled by a rule -> paint there HELD, band reported
Checks (flag only, never clipped): plaster above the floor-to-floor; paint above plaster.
Never: the V1 0.150 ceiling allowance, the 0.10 build-up fallback, any assumed build-up or ceiling depth, a
floor-to-floor taken as a wall height, a missing height as 0. Project-agnostic; stdlib only.
"""

from __future__ import annotations

import hashlib
import json

from engine.source import arch_v28 as V28

POLICY_ID = "ARCHITECTURAL_FINISH_HEIGHT_V2"
AGREE_M = 0.005
BEAM, SLAB, UNKNOWN = "BEAM_SOFFIT", "SLAB_SOFFIT", "UNKNOWN"
COMPUTED, HELD, CONFLICT = "COMPUTED", "HELD", "CONFLICT"
SOURCE_STATES = ("PRINTED", "PRINTED_DIMENSION", "PRINTED_LEVELS", "DERIVED_FROM_PRINTED_LEVELS", "PROJECT_FACT")
SLAB_STATES = SOURCE_STATES + ("OWNER_RULE",)        # owner Q-14: structural slab 0.16 m unless a drawing says otherwise
REFUSED_PARAMETERS = {
    "ceiling_allowance_m": "finish_height V1 CEILING_ALLOWANCE_M 0.150 (URBAN-PAINT-TO-FINISHED-CEILING@v1): an assumed "
                           "false-ceiling depth, refused by owner Q-14",
    "buildup_fallback_m": "URBAN-RESIDENTIAL-FLOOR-BUILDUP-FALLBACK@v1 0.10 m: an assumed floor build-up, refused by "
                          "owner Q-14"}
RANK = {"ELEMENT_ANNOTATION": 1, "SECTION": 3, "DERIVED": 4}


def accepted(rec, states=SOURCE_STATES):
    """a value record usable as evidence: a value, an accepted state, and (for a project fact) authority + source."""
    if not isinstance(rec, dict) or rec.get("value_m") is None or rec.get("state") not in states:
        return False
    if rec["state"] == "PROJECT_FACT" and not (rec.get("authority") and rec.get("source")):
        return False
    return True


def _cand(rank_kind, value, basis, **kw):
    return dict({"kind": rank_kind, "rank": RANK[rank_kind], "value_m": round(value, 6), "basis": basis}, **kw)


def _resolve(cands, held_why):
    ok = [c for c in cands if c.get("value_m") is not None]
    if not ok:
        return {"height_m": None, "state": HELD, "why": held_why, "candidates": cands}
    best = min(c["rank"] for c in ok)
    top = [c for c in ok if c["rank"] == best]
    vals = sorted({c["value_m"] for c in top})
    if vals[-1] - vals[0] > AGREE_M:
        return {"height_m": None, "state": CONFLICT, "why": "two candidates of the governing rank disagree",
                "candidates": cands}
    g = top[0]
    return {"height_m": g["value_m"], "state": COMPUTED, "governing": g["kind"], "basis": g["basis"],
            "candidates": cands}


def _annotations(texts):
    out = {}
    for t in texts or ():
        raw = t.get("value") if isinstance(t, dict) else t
        for kind, v, how, _ in V28.annotations(raw or ""):
            out.setdefault(kind, []).append({"value_m": v, "how": how, "text": raw,
                                            "text_id": t.get("id") if isinstance(t, dict) else None})
    return out


def _zv(zone, key, states=SOURCE_STATES):
    rec = (zone or {}).get(key)
    return rec if accepted(rec, states) else None


def room_heights(*, room, zone, term, texts=(), wet=False, buildup_above=None, **refused):
    out = {"policy": POLICY_ID, "room_id": room.get("room_id"), "wet": bool(wet), "refused_inputs": [],
           "termination": (term or {}).get("type", UNKNOWN)}
    for k, v in refused.items():
        if k not in REFUSED_PARAMETERS:
            raise TypeError(f"room_heights() got an unexpected keyword argument {k!r}")
        if v is not None:
            out["refused_inputs"].append({"input": k, "value_m": v, "why": REFUSED_PARAMETERS[k]})
    if buildup_above is not None and not accepted(buildup_above):
        out["refused_inputs"].append({"input": "buildup_above", "value_m": buildup_above.get("value_m")
                                      if isinstance(buildup_above, dict) else buildup_above,
                                      "why": "not printed and not a project fact with authority and source "
                                             "(an assumed or fallback build-up is refused, owner Q-14)"})
        buildup_above = None
    if room.get("state") != "PRINTED":
        why = "ROOM_LEVEL_HELD: " + str(room.get("why"))
        for q in ("PLASTER", "PAINT", "WALL_TILE"):
            out[q] = {"height_m": None, "state": HELD, "why": why}
        return out
    if not zone or zone.get("state") == HELD:
        why = "ZONE_HELD: " + str((zone or {}).get("why", "no section-binding zone for the room's level"))
        for q in ("PLASTER", "PAINT", "WALL_TILE"):
            out[q] = {"height_m": None, "state": HELD, "why": why}
        return out
    out["ffl_m"] = room["level_m"]
    ann = _annotations(texts)
    f2f, sof, tos = _zv(zone, "floor_to_floor"), _zv(zone, "soffit"), _zv(zone, "next_slab_top")
    slab = _zv(zone, "slab_thickness", SLAB_STATES)
    tt = (term or {}).get("type", UNKNOWN)
    d_m = (term or {}).get("D_cm") / 100.0 if tt == BEAM and (term or {}).get("D_cm") is not None else None

    # ---------------------------------------------------------------- plaster: to the structural soffit
    pc = [_cand("ELEMENT_ANNOTATION", a["value_m"], f"printed in the room: {a['text']}", how=a["how"])
          for a in ann.get("PLASTER_HEIGHT", ()) if a["value_m"] is not None]
    held = "TERMINATION_UNKNOWN: " + str((term or {}).get("why", "no termination")) if tt == UNKNOWN else None
    if tt == SLAB:
        if sof:
            pc.append(_cand("SECTION", sof["value_m"], "printed U/S SLAB above the F.F.L."))
        if tos and slab:
            pc.append(_cand("SECTION", tos["value_m"] - slab["value_m"],
                            f"printed next T.O.S. - slab {slab['value_m']:.3f} ({slab['state']})"))
    elif tt == BEAM and d_m is not None:
        if tos:
            pc.append(_cand("SECTION", tos["value_m"] - d_m, f"printed next T.O.S. - beam D {d_m:.3f}"))
        elif sof and slab:
            pc.append(_cand("SECTION", sof["value_m"] + slab["value_m"] - d_m,
                            f"printed U/S SLAB + slab {slab['value_m']:.3f} ({slab['state']}) - beam D {d_m:.3f}"))
    if tt in (SLAB, BEAM):
        cut = slab if tt == SLAB else ({"value_m": d_m, "state": "PRINTED"} if d_m is not None else None)
        if f2f and cut and buildup_above:
            pc.append(_cand("DERIVED", f2f["value_m"] - buildup_above["value_m"] - cut["value_m"],
                            f"floor-to-floor {f2f['value_m']:.3f} ({f2f['state']}) - build-up above "
                            f"{buildup_above['value_m']:.3f} ({buildup_above['state']}) - "
                            f"{'slab' if tt == SLAB else 'beam D'} {cut['value_m']:.3f}"))
        elif held is None:
            miss = [n for n, v in (("floor-to-floor", f2f), ("slab thickness / beam D", cut),
                                   ("floor build-up above", buildup_above)) if not v]
            held = ("SOFFIT_NOT_PRINTED: no U/S SLAB or next T.O.S. is printed for this zone and the derivation lacks "
                    + ", ".join(miss) + (" (FLOOR_BUILDUP_ABOVE_NOT_PRINTED: no build-up is assumed, owner Q-14)"
                                         if not buildup_above else ""))
    out["PLASTER"] = _resolve(pc, held or "SOFFIT_NOT_PRINTED")
    out["PLASTER"]["method"] = "UP-HGT-001 PLASTER: F.F.L. to the structural soffit"

    # ---------------------------------------------------------------- paint: to the finished ceiling
    qc = [_cand("ELEMENT_ANNOTATION", a["value_m"], f"printed in the room: {a['text']}", how=a["how"])
          for a in ann.get("CEILING_HEIGHT", ()) if a["value_m"] is not None]
    for key, what in (("false_ceiling", "printed F.C.L. above the F.F.L."), ("clear_height", "printed clear height")):
        v = _zv(zone, key)
        if v:
            qc.append(_cand("SECTION", v["value_m"], what))
    paint = _resolve(qc, "CEILING_LEVEL_NOT_PRINTED: the finished ceiling is not printed in the room or on a bound "
                         "section; no ceiling allowance, false-ceiling depth or build-up is assumed (owner Q-14)")
    out["PAINT"] = dict(paint, applies=not wet, method="UP-HGT-001 PAINT: F.F.L. to the finished ceiling",
                        **({} if not wet else {"note": "no paint over full-height wall porcelain (UP-FIN-PAINT-001)"}))

    # ---------------------------------------------------------------- wall tile (wet rooms)
    if wet:
        tc = [_cand("ELEMENT_ANNOTATION", a["value_m"], f"printed in the room: {a['text']}", how=a["how"])
              for a in ann.get("TILE_HEIGHT", ()) if a["value_m"] is not None]
        if tc:
            out["WALL_TILE"] = dict(_resolve(tc, ""), method="printed tile height")
        else:
            out["WALL_TILE"] = {k: paint[k] for k in ("height_m", "state", "why", "governing", "basis") if k in paint}
            out["WALL_TILE"]["method"] = "UP-FIN-WALL-001: full height to the finished ceiling (the paint height)"
    else:
        out["WALL_TILE"] = {"height_m": None, "state": "NOT_APPLICABLE", "why": "dry room"}

    # ---------------------------------------------------------------- band above the ceiling, checks
    pl, pa = out["PLASTER"]["height_m"], out["PAINT"]["height_m"]
    if not wet and pl is not None and pa is not None:
        out["ABOVE_CEILING"] = {"band_m": round(pl - pa, 6), "plaster": "in PLASTER (owner Q-14)",
                                "paint": HELD, "why": "PAINT_ABOVE_CEILING_NOT_SETTLED: owner Q-14 says a false "
                                "ceiling does not mean the wall above gets no plaster or paint; no rule says whether "
                                "it is painted"}
    checks = []
    if pl is not None and f2f and pl > f2f["value_m"] + AGREE_M:
        checks.append({"code": "PLASTER_ABOVE_FLOOR_TO_FLOOR", "plaster_m": pl, "floor_to_floor_m": f2f["value_m"],
                       "action": "flag only - never clipped"})
    if pl is not None and pa is not None and pa > pl + AGREE_M:
        checks.append({"code": "PAINT_ABOVE_PLASTER", "paint_m": pa, "plaster_m": pl, "action": "flag only"})
    out["checks"] = checks
    return out


def policy_record() -> dict:
    rec = {"policy_id": POLICY_ID, "source_states": list(SOURCE_STATES), "slab_states": list(SLAB_STATES),
           "ranks": RANK, "refused": REFUSED_PARAMETERS,
           "quantities": ["PLASTER", "PAINT", "WALL_TILE", "ABOVE_CEILING"],
           "rules": ["owner Q-14", "UP-HGT-001", "UP-FIN-PAINT-001", "UP-FIN-WALL-001"],
           "never": ["the 0.150 m ceiling allowance", "the 0.10 m floor build-up fallback",
                     "an assumed floor build-up or false-ceiling depth", "a floor-to-floor taken as a wall height",
                     "a missing height as 0", "one height clipped to another"]}
    rec["digest"] = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()
    return rec
