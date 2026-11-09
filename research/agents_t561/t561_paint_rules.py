"""T-561 wall paint reconciliation against a freelancer's paint workbook, by face class (any villa; research, unwired).

R-T561-1 (proposed, every villa). A freelancer's wall-paint total (m2) is reconciled to the candidate's paint lines by
FACE CLASS, in exact decimal arithmetic, on top of R-T552-1 (the plaster bridge, reused unchanged):
  (a) PAINT FACE: a dry wall face from the finished floor to the FINISHED CEILING (owner 2026-11-02 'paint to the
      finished ceiling', Q-72; Q-48 A / Q-52 C: the finished ceiling per room), net of every opening inside that height
      (Q-73, full); a stair shaft at its full exposed height to the decor line under the roof (Q-72 B, T-173);
      a face carrying full-height porcelain is never painted (UP-FIN-PAINT-001; owner wet-area rule 2026-11-02); a
      tile that stops below the ceiling leaves a paint band = ceiling height - tile top, its own face;
  (b) PAINT HEIGHT != PLASTER HEIGHT: a paint height carries its basis; a slab / roof underside basis (the plaster
      height after 2 Nov) is refused for paint where a ceiling exists (`paint_height`). The owner G1 room formula
      (interval - beam - decor - floor) and the drawing-derived height (interval - slab - floor build-up - decor) are
      two methods shown side by side (ERS s.2.2); an unknown term gives a bound, never a value;
  (c) COATS ARE A RATE: the number of coats multiplies material and labour, never the measured area; a component or
      area that carries a coats multiplier is refused (`net_wall_paint`, `bridge`);
  (d) one finish owner per face across his workbooks too: a face he prices as tile AND paint is a RULE_DIFFERENCE row
      of his (UP-FIN-PAINT-001), never an engine omission; a stair / flight soffit is a CEILING-class face (Q-57,
      FIN.STAIR.SOFFIT), never a wall-paint component; returns (jambs / head) are their own class;
  (e) the bridge is R-T552-1 (c)-(f): freelancer GROSS - engine VALUED = signed components + ONE named residual; his
      half-deduction step outside the bridge; HELD lines at their engine-basis gross, never 0.
"""
from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "agents_t552"))
import t552_plaster_rules as P  # noqa: E402

CLASSES = P.CLASSES
PAINT_BASES = ("OWNER_G1_ROOM_FORMULA", "DRAWING_FINISHED_CEILING", "PRINTED_CEILING_LEVEL", "SHAFT_TO_DECOR_UNDER_ROOF")
REFUSED_PAINT_BASES = ("SLAB_UNDERSIDE", "ROOF_UNDERSIDE", "PLASTER_HEIGHT")


class PaintError(ValueError):
    pass


D = P.D


def paint_height(*, basis: str, sources: dict, interval=None, beam=None, decor=None, floor=None, slab=None,
                 buildup=None, level=None) -> tuple:
    """-> (lo, hi) paint height from the finished floor to the finished ceiling.
    OWNER_G1_ROOM_FORMULA: interval - beam - decor - floor (Q-48 A; an approximation under Q-52 C, shown as the owner
    column). DRAWING_FINISHED_CEILING: interval - slab - build-up - decor (a decor ceiling hung its depth under the slab;
    a beam projecting below that plane is a bulkhead, its own ceiling item). PRINTED_CEILING_LEVEL: the level itself.
    A slab / roof underside basis is the plaster height (owner 2026-11-02) and is refused for paint."""
    if basis in REFUSED_PAINT_BASES:
        raise PaintError(f"height basis {basis!r} is the plaster height (slab / roof underside): paint stops at the "
                         "finished ceiling (owner 2026-11-02, Q-72)")
    if basis not in PAINT_BASES:
        raise PaintError(f"height basis {basis!r} not in {PAINT_BASES}")
    terms = {"OWNER_G1_ROOM_FORMULA": ("interval", "beam", "decor", "floor"),
             "DRAWING_FINISHED_CEILING": ("interval", "slab", "buildup", "decor"),
             "SHAFT_TO_DECOR_UNDER_ROOF": ("interval", "slab", "buildup", "decor"),
             "PRINTED_CEILING_LEVEL": ("level",)}[basis]
    vals = {"interval": interval, "beam": beam, "decor": decor, "floor": floor, "slab": slab, "buildup": buildup,
            "level": level}
    for k in terms:
        if vals[k] is None:
            raise PaintError(f"{k} not given: the paint height stays HELD (never a default)")
        if not (sources or {}).get(k):
            raise PaintError(f"{k} has no source")
    if basis == "PRINTED_CEILING_LEVEL":
        lo = hi = D(level)
    elif basis == "OWNER_G1_ROOM_FORMULA":
        lo = hi = D(interval) - D(beam) - D(decor) - D(floor)
    else:
        b_lo, b_hi = buildup if isinstance(buildup, tuple) else (buildup, buildup)
        lo = D(interval) - D(slab) - D(b_hi) - D(decor)
        hi = D(interval) - D(slab) - D(b_lo) - D(decor)
    if lo <= 0 or lo > hi:
        raise PaintError("paint height range not positive / ordered")
    return lo, hi


def net_wall_paint(*, run_lm, height, openings: list[dict], coats=None, tile_top=None, full_height_tile=False,
                   area_multiplier=None) -> dict:
    """Hand-checkable net paint of one room's wall faces: run x height - every opening by its own area inside the
    height (Q-73, full). coats is reported beside as a RATE (never multiplied in). A full-height porcelain face has no
    paint (UP-FIN-PAINT-001); a tile stopping at tile_top leaves the band height - tile_top (openings inside the band
    only). Any area_multiplier (e.g. coats) is refused."""
    if area_multiplier not in (None, 1, "1"):
        raise PaintError("an area multiplier (coats) is refused: coats are a rate, never an area factor")
    if full_height_tile:
        raise PaintError("full-height porcelain face: paint NOT_APPLICABLE_WITH_EVIDENCE (UP-FIN-PAINT-001)")
    H = D(height)
    z0 = Decimal(0) if tile_top is None else D(tile_top)
    if z0 >= H:
        raise PaintError("tile top at or above the finished ceiling: no paint band (UP-FIN-PAINT-001)")
    band = H - z0
    gross = D(run_lm) * band
    ded = Decimal(0)
    for o in openings:
        if o.get("height") is None:
            raise PaintError(f"opening {o.get('id')}: height not established (net is a range, never a guess)")
        if tile_top is not None and o.get("sill") is None:
            raise PaintError(f"opening {o.get('id')}: sill not established, its part inside the paint band is unknown")
        sill = D(o.get("sill") or "0")
        top = min(sill + D(o["height"]), H)
        ded += D(o["width"]) * max(Decimal(0), top - max(sill, z0))
    out = {"gross": gross, "deductions": ded, "net": gross - ded, "band_height": band}
    if coats is not None:
        if int(coats) < 1:
            raise PaintError("coats must be a positive count")
        out["coats_rate"] = int(coats)
    return out


def bridge(*, pair_class: str, freelancer_gross, engine_lines: list[dict], components: list[dict],
           residual_name: str, outside: list[dict] = ()) -> dict:
    """R-T552-1 (c)-(f) plus the paint refusals: a component with a coats multiplier, a plaster height basis, or a
    stair soffit in a wall pair."""
    for c in components:
        if c.get("coats_multiplier") not in (None, 1):
            raise PaintError(f"component {c.get('name')}: coats multiplied into the area (coats are a rate)")
        if c.get("height_basis") in REFUSED_PAINT_BASES:
            raise PaintError(f"component {c.get('name')}: plaster height basis {c['height_basis']!r} in a paint pair")
        if pair_class in ("DRY", "SHAFT", "RETURN", "WET") and c.get("face_class") == "CEILING":
            raise PaintError(f"component {c.get('name')}: a soffit / ceiling face in a {pair_class} wall pair")
    try:
        return P.bridge(pair_class=pair_class, freelancer_gross=freelancer_gross, engine_lines=engine_lines,
                        components=components, residual_name=residual_name, outside=outside)
    except P.PlasterError as e:
        raise PaintError(str(e)) from e


def check_face_classes(faces: list[dict]) -> None:
    """faces: [{face_id, cls, painted?, tiled_full?}] -> one finish owner per face; a full-height tiled face that is
    also painted is refused."""
    for f in faces:
        if f.get("painted") and f.get("tiled_full"):
            raise PaintError(f"face {f['face_id']}: painted and tiled full height (UP-FIN-PAINT-001)")
    try:
        P.check_face_classes(faces)
    except P.PlasterError as e:
        raise PaintError(str(e)) from e
