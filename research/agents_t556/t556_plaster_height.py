"""PLASTER_HEIGHT_METHOD_V1 (T-556; research, unwired; any villa): the DRY wall-plaster height and net face of a room
line to the underside of the structural slab / roof (owner 2026-11-02, Q-72; Q-14), not the paint height.

R-T556-1 (proposed rule, every villa; provenance T-552 ENGINE_WRONG, Checker 2026-11-06 05:58):
  (a) PHYSICAL ELEMENT: the plastered dry wall face from the finished floor (FFL) to the soffit of the structural slab
      or roof over it, above any false ceiling (MISSION 'Heights'), net of every opening by its own hole (Q-73) and of
      the end section of every beam that crosses the room (concrete, not wall; the beam's sides and soffit are a
      CEILING item, Q-57). A beam ON the wall line leaves the face continuous (its side is plastered with the wall).
  (b) HEIGHT: H = storey interval (FFL to the FFL / finished mark above) - build-up of the floor above (FFL above ->
      its structural top) - thickness of the slab above. Each term carries its source. The PAINT height, the finished
      ceiling, the owner G1 room formula (interval - beam allowance - decor - floor allowance) and any 'allowance' are
      REFUSED as a plaster height basis; two layers equal by construction (plaster line = paint line) is a defect signal.
  (c) A face segment under a FLOOR slab takes the drawn floor build-up of the floor above (a DRAWING-CONFIRMED value,
      e.g. T-214). A face segment under a ROOF takes the ROOF build-up, which is a different element (falls screed,
      insulation, membrane): the floor build-up is never carried to a roof; an unprinted roof build-up keeps the segment
      HELD, with at most a labelled DRAWN-SECTION SCENARIO (the layer the cut section draws) and its sensitivity per
      0.01 m; never a bound invented from a floor allowance.
  (d) OPENINGS at the plaster height: a hole of known height lies wholly below the soffit, so it is deducted in full
      (w x h), whatever its unknown sill; a hole with sill and head is deducted as w x (min(head, H) - sill); an outline
      area (arched hole) by its area or its HELD (lo, hi); an opening with no established height is a HELD bound
      (0, w x H), never a guess and never 0 silently. A head above H by more than the drawing tolerance is a datum
      conflict, reported.
  (e) BEAM ENDS: width x (overall depth - slab thickness) per crossing; a beam crossing a CLOSED room interrupts two
      wall faces (it must pass the room's boundary twice); an open-sided room gives 0 .. 2 (HELD on the count).
  (f) Missing slab thickness, missing build-up of a floor segment, missing interval -> the line is HELD naming the term
      (never the paint height, never 0).
Exact decimal arithmetic throughout.
"""
from __future__ import annotations

from decimal import Decimal

REFUSED_BASES = ("PAINT_HEIGHT", "FINISHED_CEILING", "OWNER_G1_ROOM_FORMULA", "ALLOWANCE")
SEGMENTS = ("FLOOR_SLAB", "ROOF")
TOL_HEAD = Decimal("0.010")   # drawing tolerance for a head at the soffit (T-214 TOL_DRAWN 10 mm)


class PlasterHeightError(ValueError):
    pass


class Held(PlasterHeightError):
    """A required term is not established: the quantity stays HELD by name."""


def D(x) -> Decimal:
    if x is None:
        raise Held("quantity unknown (None): a HELD term is never 0")
    if isinstance(x, float):
        return Decimal(repr(x))
    return Decimal(str(x))


def _src(name, value, source):
    if value is None:
        raise Held(f"{name} not established: the plaster height stays HELD ({name} named, never a default, never the "
                   "paint height)")
    if not source:
        raise PlasterHeightError(f"{name} has no source")
    return D(value)


def plaster_height(*, basis: str, interval, interval_src, slab, slab_src, buildup, buildup_src,
                   segment: str = "FLOOR_SLAB") -> Decimal:
    """H = interval - build-up above - slab above (R-T556-1 b, c). buildup is the build-up of the FLOOR above for a
    FLOOR_SLAB segment; for a ROOF segment it must be the roof build-up and its source must say so."""
    if basis in REFUSED_BASES:
        raise PlasterHeightError(f"basis {basis!r} is a paint / ceiling / allowance height: plaster runs to the slab or "
                                 "roof underside (owner 2026-11-02, Q-72)")
    if basis != "SLAB_OR_ROOF_UNDERSIDE":
        raise PlasterHeightError(f"basis {basis!r} unknown")
    if segment not in SEGMENTS:
        raise PlasterHeightError(f"segment {segment!r}")
    iv = _src("storey interval", interval, interval_src)
    t = _src("slab thickness", slab, slab_src)
    b = _src("roof build-up" if segment == "ROOF" else "floor build-up", buildup, buildup_src)
    if segment == "ROOF" and "roof" not in str(buildup_src).lower():
        raise PlasterHeightError("a ROOF segment takes the roof build-up: a floor build-up is never carried to a roof")
    if segment == "FLOOR_SLAB" and "roof" in str(buildup_src).lower():
        raise PlasterHeightError("a FLOOR_SLAB segment takes the floor build-up of the floor above, not a roof value")
    if iv > 20 or t > 2 or b > 2:
        raise PlasterHeightError("units: metres expected (interval > 20 m or slab / build-up > 2 m looks like mm)")
    if t <= 0 or b < 0 or iv <= 0:
        raise PlasterHeightError("interval / slab must be positive, build-up not negative")
    h = iv - b - t
    if h <= 0:
        raise PlasterHeightError("plaster height not positive")
    return h


def opening_deduction(op: dict, H) -> tuple:
    """-> (lo, hi, status) m2 of one opening inside the plaster height H (R-T556-1 d)."""
    H = D(H)
    w = op.get("width")
    if op.get("area_range") is not None:
        lo, hi = (D(x) for x in op["area_range"])
        return lo, hi, "HELD (outline area range)" if lo != hi else "AREA"
    if op.get("area") is not None:
        a = D(op["area"])
        return a, a, "AREA"
    w = D(w)
    if op.get("head") is not None and op.get("sill") is not None:
        head, sill = D(op["head"]), D(op["sill"])
        if head - H > TOL_HEAD:
            raise PlasterHeightError(f"opening {op.get('id')}: head {head} above the soffit height {H} by more than "
                                     f"{TOL_HEAD}: datum conflict")
        a = w * (min(head, H) - sill)
        return a, a, "SILL_HEAD"
    if op.get("height") is not None:
        h = D(op["height"])
        if h - H > TOL_HEAD:
            raise PlasterHeightError(f"opening {op.get('id')}: height {h} above the soffit height {H}")
        a = w * min(h, H)
        return a, a, "HOLE_HEIGHT (sill not needed below the soffit)"
    return Decimal(0), w * H, "HELD (no height established)"


def beam_end_deduction(*, width, depth, slab, ends) -> tuple:
    """width: value or (lo, hi); ends: 2 (closed room) or (0, 2) (open-sided room). -> (lo, hi) m2."""
    wl, wh = (D(width[0]), D(width[1])) if isinstance(width, tuple) else (D(width), D(width))
    el, eh = (ends if isinstance(ends, tuple) else (ends, ends))
    below = D(depth) - D(slab)
    if below <= 0:
        raise PlasterHeightError("beam depth not below the slab soffit: no end section")
    return wl * below * el, wh * below * eh


def restate_line(*, face_lm, roof_share, H_floor, H_roof_scenario, openings: list, beams: list) -> dict:
    """Net dry plaster of one room line. The FLOOR part of the face is at H_floor (established); the ROOF part at the
    DRAWN-SECTION scenario H_roof_scenario (HELD). -> lo / hi (opening and beam-end bounds), the face split and the
    sensitivity (m2 per 0.01 m of roof build-up beyond the scenario)."""
    f = D(face_lm)
    s = D(roof_share)
    if not (0 <= s <= 1):
        raise PlasterHeightError("roof share outside 0 .. 1")
    f_roof = f * s
    f_floor = f - f_roof
    Hf = D(H_floor) if f_floor else None
    Hr = D(H_roof_scenario) if f_roof else None
    if f_floor and Hf is None:
        raise Held("floor-part height missing")
    gross = (f_floor * Hf if f_floor else Decimal(0)) + (f_roof * Hr if f_roof else Decimal(0))
    Hmax = max(h for h in (Hf, Hr) if h is not None)
    dlo = dhi = Decimal(0)
    rows = []
    for op in openings:
        lo, hi, st = opening_deduction(op, Hmax)
        dlo += lo
        dhi += hi
        rows.append({"id": op["id"], "lo": str(lo), "hi": str(hi), "basis": st})
    blo = bhi = Decimal(0)
    brows = []
    for b in beams:
        lo, hi = beam_end_deduction(width=b["width"], depth=b["depth"], slab=b["slab"], ends=b["ends"])
        blo += lo
        bhi += hi
        brows.append({"mark": b["mark"], "lo": str(lo), "hi": str(hi), "ends": str(b["ends"])})
    return {"face_floor_lm": str(f_floor), "face_roof_lm": str(f_roof), "gross": str(gross),
            "openings": rows, "openings_lo": str(dlo), "openings_hi": str(dhi),
            "beam_ends": brows, "beam_ends_lo": str(blo), "beam_ends_hi": str(bhi),
            "net_lo": str(gross - dhi - bhi), "net_hi": str(gross - dlo - blo),
            "roof_sensitivity_m2_per_0.01m": str(f_roof * Decimal("0.01"))}


def equal_by_construction(plaster_lines: dict, paint_lines: dict) -> list:
    """Defect signal (R-T556-1 b): room ids whose plaster m2 equals their paint m2 although the plaster height rule
    (slab underside) and the paint rule (finished ceiling) differ. -> the room ids; [] when none."""
    return sorted(k for k, v in plaster_lines.items() if k in paint_lines and v is not None
                  and paint_lines[k] is not None and D(v) == D(paint_lines[k]))
