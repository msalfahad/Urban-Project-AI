"""T-702 rules (research, unwired; every villa; no project value in this module).

R-T702-1 BEAM CROSSING ON A ROOM'S FACE WALK (provenance T-690 'beam-end count 0 .. 2', closed by an overlay of the
  structural slab plan on the architectural plan).
  (a) ELEMENT: where a downstand beam's plan footprint meets a room's face walk, the wall face above the finished
      ceiling H is replaced over the beam's depth by the beam (its end, or its passage over the wall line).
  (b) LENGTH: the length of the face walk inside the beam footprint, measured from the beam's two drawn edges: a
      square crossing gives b, an oblique one b / sin(theta), a crossing at a corner or a column face takes every face
      piece inside the footprint (column face, return, the adjacent wall). An over-door / over-window wall counts (the
      wall above the head exists); an open edge counts 0. Never 'ends x b'.
  (c) BAND TERM per stretch: band = length x max(0, (S - H) - (h - slab)) where the beam is shallower than the band,
      0 where it fills it; S is the stretch's own soffit (R-T702-2).
  (d) COUNT: established only from an overlay whose fit is checked on other members (count matched, residual); without
      it the T-690 bound (0 .. 2 ends) stands.

R-T702-2 SOFFIT UNDER A SUNKEN SLAB PANEL (provenance D-41 / T-213: drop d printed nowhere).
  A face under a sunken panel has S = S_flat - d with d HELD; the band on it is bounded by 0 (d = S_flat - H, the
  ceiling cannot lie above the soffit) .. length x (S_flat - H) (d = 0). A face is 'under' the panel by the plan
  overlap of the face line with the panel hatch; the boundary beam between two panels is under neither.

R-T702-3 ROOF BUILD-UP LAYER ROW. A roof layer exists in the BOQ by a print or an owner rule only (else UNKNOWN: a HELD
  row with its designer item, never 0); its area is measured to its own drawn edge (finish -> finish hatch, screed /
  membrane -> wall and parapet faces); a thickness or a volume comes only from a print: a screed m3 is AT_LEAST (the
  falls wedge above the t0 plane) .. OPEN unless a printed cap is LOCATED (sheet + entity or dimension); a cap cited
  but not located is not used. The falls volume is carried once (FIN.ROOF.SCREED), never also as a tile bed.

R-T702-4 ONE OWNER PER STAIR-CORE FLOOR SURFACE (OWNER_RULE_STAIRS A6, ELEMENT_REGISTER 'one finish line per surface').
  A surface is claimed by exactly one of: floor finish (a floor-level landing, the hall / lobby at a flight end),
  B7-04 landing marble (an intermediate landing, an arrival where Q-66 B / Q-70 A applies) or a tread. Two claims of
  one surface are refused; a bound that holds no landing is NOT_APPLICABLE as a landing bound.

R-T702-5 WALL TILE FOLLOWS ITS BACKING. In a fully tiled wet room the wall-tile m2 and its backing render m2 are one
  face to one top (tile top = finished ceiling, Q-48 A) less the same openings: a blank wall-tile line takes its
  backing line's bound (same status) unless a print gives the tile a different top.
"""
from __future__ import annotations

from decimal import Decimal, localcontext

Q6 = Decimal("0.000001")


class RuleError(ValueError):
    pass


class Held(RuleError):
    pass


def D(x):
    if x is None:
        raise Held("term missing: HELD by name, never 0")
    if isinstance(x, float):
        raise RuleError("float refused: pass a decimal string")
    v = Decimal(str(x))
    if v.is_nan():
        raise Held("term not a number: HELD")
    return v


def q(x):
    with localcontext() as c:
        c.prec = 40
        return D(x).quantize(Q6)


# ------------------------------------------------------------------ R-T702-1 / -2

def crossing_length(b, sin_theta):
    """R-T702-1 (b): face length inside a beam footprint of width b crossing a straight face at angle theta."""
    b, s = D(b), D(sin_theta)
    if b <= 0:
        raise RuleError("beam width not positive")
    if not (0 < s <= 1):
        raise RuleError("crossing angle refused (beam parallel to the face, or sin > 1)")
    with localcontext() as c:
        c.prec = 40
        return b / s


def band_on_stretch(length, S, H, beam_h=None, slab=None):
    """R-T702-1 (c): band m2 on one stretch at one datum point; beam_h / slab given where a beam crosses it."""
    L, S, H = D(length), D(S), D(H)
    if L < 0:
        raise RuleError("negative length")
    if S < H:
        raise RuleError(f"soffit {S} below the tile top {H}: data conflict, refused")
    band = S - H
    if beam_h is not None:
        depth = D(beam_h) - D(slab)
        if depth <= 0:
            raise RuleError("beam depth not below the slab")
        band = max(Decimal(0), band - depth)
    return L * band


def room_band(free, beam_stretches, panel_faces, roof_faces, S_flat, H, roof_S=None):
    """R-T702-1 / -2 for one room -> (low, high).
    free: face length under the flat floor slab with no beam; beam_stretches: [(length, h, slab, sunk)] where sunk
    marks a stretch whose beam top is unprinted (between sunken panels: its strip 0 .. flat value); panel_faces: face
    length under sunken panels (0 .. flat); roof_faces: face length under a roof whose soffit runs roof_S = (lo, hi)."""
    S_flat, H = D(S_flat), D(H)
    lo = hi = band_on_stretch(free, S_flat, H)
    for length, h, slab, sunk in beam_stretches:
        v = band_on_stretch(length, S_flat, H, h, slab)
        lo, hi = lo + (0 if sunk else v), hi + v
    if D(panel_faces) > 0:
        hi += band_on_stretch(panel_faces, S_flat, H)  # d = 0; low end d = S_flat - H gives 0
    if D(roof_faces) > 0:
        if roof_S is None:
            raise Held("roof soffit bound missing: HELD")
        rlo, rhi = sorted(max(D(x), H) for x in roof_S)
        lo, hi = lo + band_on_stretch(roof_faces, rlo, H), hi + band_on_stretch(roof_faces, rhi, H)
    return q(lo), q(hi)


# ------------------------------------------------------------------ R-T702-3

LAYERS = ("FALLS_SCREED", "INSULATION", "PROTECTION", "FINISH")


def layer_row(zone, layer, *, area=None, area_edge=None, printed_thickness=None, owner_rule=None, at_least_m3=None,
              cap=None, designer_item=None):
    """R-T702-3 -> dict(state, quantity, why). cap = (value, located: bool, source)."""
    if layer not in LAYERS:
        raise RuleError(f"unknown layer {layer}")
    exists = printed_thickness is not None or owner_rule is not None or layer == "FINISH" and area is not None
    if not exists:
        return {"zone": zone, "layer": layer, "state": "UNKNOWN", "quantity": None,
                "why": f"no print and no owner rule; designer item {designer_item or 'D-39'}: HELD blank, never 0"}
    if layer == "FINISH":
        if area is None or area_edge is None:
            raise Held("finish area without its own edge: HELD")
        return {"zone": zone, "layer": layer, "state": "MEASURED (area); material HELD", "quantity": q(area),
                "unit": "m2", "why": f"to its own edge: {area_edge}"}
    if layer == "FALLS_SCREED":
        if printed_thickness is not None:
            if area is None:
                raise Held("screed area missing")
            return {"zone": zone, "layer": layer, "state": "MEASURED", "quantity": q(D(area) * D(printed_thickness)),
                    "unit": "m3", "why": "area x printed thickness"}
        hi = None
        if cap is not None:
            val, located, src = cap
            if not located:
                raise RuleError(f"cap {val} from '{src}' is cited but not located on a sheet: refused as a bound")
            if area is None:
                raise Held("screed area missing for the cap")
            hi = q(D(area) * D(val))
        lo = q(at_least_m3) if at_least_m3 is not None else None
        if lo is not None and hi is not None and lo > hi:
            raise RuleError("AT_LEAST above the cap: data conflict")
        return {"zone": zone, "layer": layer, "state": "HELD", "quantity": None, "low": lo, "high": hi,
                "unit": "m3", "why": f"scope {owner_rule}; t0 unprinted ({designer_item or 'D-39'}): "
                                     f"{'AT_LEAST' if lo is not None else 'blank'} .. {'cap' if hi else 'OPEN'}"}
    # INSULATION / PROTECTION: a printed layer is measured on its own edge; else carried by an owner rule elsewhere
    if printed_thickness is not None:
        if area is None or area_edge is None:
            raise Held(f"{layer}: printed but its own edge / area missing: HELD")
        return {"zone": zone, "layer": layer, "state": "MEASURED", "quantity": q(area), "unit": "m2",
                "why": f"printed {printed_thickness} m; to its own edge: {area_edge}"}
    return {"zone": zone, "layer": layer, "state": "CARRIED_BY", "quantity": None, "why": owner_rule}


# ------------------------------------------------------------------ R-T702-4

def single_owner(surfaces):
    """surfaces: [(surface_id, trade, line_or_None)] -> {surface: trade}; two trades on one surface refused."""
    out = {}
    for sid, trade, _line in surfaces:
        if trade not in ("FLOOR", "B7-04", "TREAD"):
            raise RuleError(f"{sid}: unknown trade {trade}")
        if sid in out and out[sid] != trade:
            raise RuleError(f"{sid}: claimed by {out[sid]} and {trade}: refused (one surface, one finish line)")
        out[sid] = trade
    return out


# ------------------------------------------------------------------ R-T702-5

def tile_follows_backing(backing, printed_tile_top=None):
    """backing: dict(class, held_low, held_high, measured_net) -> the wall-tile bound (same status)."""
    if printed_tile_top is not None:
        raise Held("a printed tile top differs from the backing top: measure the tile on its own top")
    if backing.get("measured_net") is not None:
        return {"class": backing["class"], "measured_net": q(backing["measured_net"])}
    lo, hi = backing.get("held_low"), backing.get("held_high")
    if lo is None or hi is None:
        raise Held("backing line blank: the tile line stays blank (HELD, never 0)")
    return {"class": "HELD", "held_low": q(lo), "held_high": q(hi)}
