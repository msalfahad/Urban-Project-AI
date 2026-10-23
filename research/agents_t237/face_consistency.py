"""T-237: cross-trade wall-face consistency (blockwork / plaster / paint), stdlib only, every villa.

Physical element (ERS s.2 step 1): one wall FACE = the surface of one wall seen from one room. Three trades measure it:
  blockwork  - the block panel: structural floor top -> soffit of the member that sits on the wall (beam or slab);
  plaster    - the whole face: block panel + the concrete band of a beam that projects below the slab (its side
               face), up to the slab soffit (drawing-derived method; the owner manual method uses his room heights);
  paint      - the plastered face below the ceiling line.
So, on one face, with a common datum (structural floor top):
  plaster_top = storey - slab_t                                   (slab soffit)
  block_h     = storey - member_depth   (member = beam of depth d, or the slab itself, d = slab_t)
  plaster_top - block_h = d - slab_t    (the beam band; 0 under a slab)
A difference that the members over the wall do not explain is a datum residual (named, never 'rounding').

Rules (proposed R-T237-1, any villa):
  (a) one opening id is deducted at most once per face; an id may appear on at most two faces (its two sides) and
      a split opening (one id shared by two room regions on the same side) must sum to the opening width;
  (b) a plaster / paint height above the block top is accepted only with a named member over that face whose band
      explains it; otherwise it is refused (PLASTER_ABOVE_BLOCK_NO_MEMBER);
  (c) a block height that is HELD is never carried as a plaster / paint number (HELD_BLOCK_CARRIED refused);
  (d) the same opening carries the same w x h in every ledger that deducts it; a mismatch is named with its m2.
Missing values stay None (HELD), never 0.
"""
from __future__ import annotations

import re

TOL_M = 0.02          # height / width agreement tolerance (m); drawn-geometry reading tolerance of the merged ledgers
TOL_M2 = 0.01

PIECE_RE = re.compile(r"\((?:h|slab t) ([0-9.]+)[^)]*\): ([0-9.]+) m -> h ([0-9.]+)")


class ConsistencyRefused(ValueError):
    """A face record that breaks rule (a), (b) or (c)."""


def member_pieces(evidence: str):
    """[(depth_m, length_m, block_h_m)] of the members printed in a wall-register evidence text
    ('CB8 BM-GF-041 (h 0.75 CALCULATED): 6.34 m -> h 3.75', 'slab GF-139 (slab t 0.16): 1.64 m -> h 3.84')."""
    return [(float(d), float(L), float(h)) for d, L, h in PIECE_RE.findall(evidence or "")]


def weighted(pieces, f):
    tot = sum(p[1] for p in pieces)
    if tot <= 0:
        return None
    return sum(f(p) * p[1] for p in pieces) / tot


def height_check(plaster_top_m, slab_t_m, block_h_m, block_status, pieces, plaster_from_block=False, void=False):
    """Compare the plaster top and the block height on one face.

    Returns a dict: delta_m (plaster_top - block_h), band_m (explained by the members, d - slab_t, length-weighted),
    residual_m (delta - band), storey_plaster_m / storey_block_m, code.
    void=True: the face rises through a void (stair shaft): there is no slab soffit at the face, the plaster runs
    floor to floor, so the member's FULL depth (beam side + slab edge) is the concrete band (band = d) and the
    plaster top is the storey itself.
    Raises ConsistencyRefused for rule (b) and (c)."""
    for v in (plaster_top_m, block_h_m):
        if v is not None and not (0.0 < v < 20.0):
            raise ConsistencyRefused(f"UNITS: a face height of {v} is not a storey height in metres")
    if void:
        slab_t_m = 0.0
    held_block = block_h_m is None or str(block_status).startswith("HELD")
    if plaster_from_block and held_block:
        raise ConsistencyRefused("HELD_BLOCK_CARRIED: the block height is HELD; a plaster number derived from it is refused")
    if plaster_top_m is None:
        return dict(code="PLASTER_HELD", delta_m=None, band_m=None, residual_m=None,
                    storey_plaster_m=None, storey_block_m=None)
    if block_h_m is None:
        return dict(code="BLOCK_HELD", delta_m=None, band_m=None, residual_m=None,
                    storey_plaster_m=round(plaster_top_m + slab_t_m, 4), storey_block_m=None)
    delta = plaster_top_m - block_h_m
    if not pieces:
        if delta > TOL_M:
            raise ConsistencyRefused(
                f"PLASTER_ABOVE_BLOCK_NO_MEMBER: plaster top {plaster_top_m:.3f} is {delta:.3f} m above the block top "
                f"{block_h_m:.3f} and no member over the face is named")
        return dict(code="AGREES" if abs(delta) <= TOL_M else "PLASTER_BELOW_BLOCK", delta_m=round(delta, 4),
                    band_m=0.0, residual_m=round(delta, 4), storey_plaster_m=round(plaster_top_m + slab_t_m, 4),
                    storey_block_m=None)
    band = weighted(pieces, lambda p: p[0] - slab_t_m)
    storey_b = weighted(pieces, lambda p: p[2] + p[0])
    if delta > TOL_M and band <= TOL_M:
        raise ConsistencyRefused(
            f"PLASTER_ABOVE_BLOCK_NO_MEMBER: plaster top {plaster_top_m:.3f} is {delta:.3f} m above the block top "
            f"and the named members are slab-only (band {band:.3f})")
    resid = delta - band
    code = "AGREES" if abs(delta) <= TOL_M else ("BAND_EXPLAINED" if abs(resid) <= TOL_M else "DATUM_RESIDUAL")
    return dict(code=code, delta_m=round(delta, 4), band_m=round(band, 4), residual_m=round(resid, 4),
                storey_plaster_m=round(plaster_top_m + slab_t_m, 4), storey_block_m=round(storey_b, 4))


def check_deductions(face_rows):
    """Rule (a) on one face: face_rows = [{'id': census id, 'w': width}] deducted on that face. Raises on a repeat."""
    seen = {}
    for r in face_rows:
        if r["id"] is None:
            continue
        if r["id"] in seen:
            raise ConsistencyRefused(f"DOUBLE_DEDUCTION: opening {r['id']} deducted twice on one face")
        seen[r["id"]] = r
    return True


def check_id_population(matches, width_of):
    """Rule (a) across faces: matches = [(room, wall_id, census_id, w)]. Returns findings (list of dicts)."""
    out = []
    by_id = {}
    for room, wall, cid, w in matches:
        if cid:
            by_id.setdefault(cid, []).append((room, wall, w))
    for cid, rows in sorted(by_id.items()):
        rooms = [r[0] for r in rows]
        if len(set(rooms)) != len(rooms):
            out.append(dict(id=cid, code="DOUBLE_DEDUCTION", rooms=rooms))
        W = width_of.get(cid)
        parts = [r for r in rows if W is not None and r[2] is not None and r[2] < W - 3 * TOL_M]
        if len(parts) >= 2:
            # a split face (one side shared by two regions) is accepted only when the split parts sum to the width
            tot = sum(r[2] for r in parts)
            d = round(tot - W, 4)
            out.append(dict(id=cid, code="SPLIT_FACE_SUMS" if abs(d) <= TOL_M else "SPLIT_FACE_SUM_DIFFERS",
                            rooms=rooms, d_w_m=d))
        elif len(rows) > 2:
            out.append(dict(id=cid, code="ID_ON_MORE_THAN_TWO_FACES", rooms=rooms, d_w_m=None))
    return out


def size_check(cid, w_a, h_a, w_b, h_b):
    """Rule (d): the same opening in two ledgers. Returns (code, d_w, d_h, d_m2) - None where a side is HELD."""
    if None in (w_a, w_b):
        return ("WIDTH_HELD", None, None, None)
    dw = w_a - w_b
    if h_a is None or h_b is None:
        return ("AGREES_WIDTH_HEIGHT_HELD" if abs(dw) <= TOL_M else "WIDTH_DIFFERS", round(dw, 4), None, None)
    dh = h_a - h_b
    dm2 = w_a * h_a - w_b * h_b
    ok = abs(dw) <= TOL_M and abs(dh) <= TOL_M
    return ("AGREES" if ok else "SIZE_DIFFERS", round(dw, 4), round(dh, 4), round(dm2, 4))


def band_deduction(w, sill, head, H):
    """Face deduction of a rectangular opening below a plastered / painted height H (T-128 convention)."""
    if None in (w, sill, head, H):
        return None
    return w * max(0.0, min(head, H) - max(sill, 0.0))


def net_bounds(gross_lo, gross_hi, H_lo, H_hi, openings):
    """Net face m2 as (lo, hi) with HELD openings as bounds (lo: full w x H; hi: no deduction).
    openings: [{'w','sill','head', 'fixed_m2' (a merged non-rectangular deduction, e.g. an arched outline)}]."""
    if gross_lo is None:
        return None, None, []
    k_lo = k_hi = 0.0
    held = []
    for o in openings:
        if o.get("fixed_m2") is not None:
            k_lo += o["fixed_m2"]; k_hi += o["fixed_m2"]
            continue
        d_lo = band_deduction(o["w"], o.get("sill"), o.get("head"), H_lo)
        d_hi = band_deduction(o["w"], o.get("sill"), o.get("head"), H_hi)
        if d_lo is None:
            held.append(o.get("id"))
            k_lo += o["w"] * H_lo
        else:
            k_lo += d_lo; k_hi += d_hi
    return gross_lo - k_lo, gross_hi - k_hi, held
