"""FINISH HEIGHT V3 - wall-face termination split by beam coverage (generic fix for blocker #16).

finish_height.termination (frozen) returns UNKNOWN for a whole wall face when a beam band covers only PART of the face
line. A wall built under a beam for half its length and under the slab for the other half has two terminations, so
V3 splits the face at the band ends:

    pieces(length, cover, inside, plate_t_cm) -> [{"t0", "t1", "length", "termination"}]

Each piece is a sub-interval of the face line; its termination comes from the bands covering the WHOLE piece
(deepest bound band -> BEAM_SOFFIT; an unbound band -> UNKNOWN), else the slab plate (SLAB_SOFFIT) when the piece lies
inside the closed plate, else UNKNOWN. finish_height.wall_heights then gives each piece its heights; the face's area
is the sum of its pieces (length x height), and any UNKNOWN piece is reported, never filled.

Pure 1-D interval logic, stdlib only (engine/source rule): the caller projects each band onto the face line
(cover = [(s0, s1, band record)]) and answers whether a piece lies inside the closed plate. Project-agnostic.
"""

from __future__ import annotations

import hashlib
import json


from . import finish_height as FH

POLICY_ID = "FINISH_HEIGHT_SPLIT_TERMINATION_V1"


def pieces(length, cover, inside=None, plate_t_cm=None, eps=1.0, min_piece=1.0) -> list:
    """length: face line length; cover: [(s0, s1, record {"type", "D_cm", "bound"})] stations along the line where a
    band lies over it; inside(t0, t1) -> bool: the piece lies inside the closed slab plate (None = no plate)."""
    L = float(length)
    if L <= 0:
        return []
    cov = []
    for s0, s1, rec in cover:
        s0, s1 = max(0.0, s0), min(L, s1)
        if s1 - s0 > eps:
            cov.append((s0, s1, rec))
    cuts = sorted({0.0, L} | {s for c in cov for s in c[:2]})
    out = []
    for t0, t1 in zip(cuts, cuts[1:]):
        if t1 - t0 < min_piece and out:              # a sliver joins the piece before it (no length is lost)
            out[-1]["t1"] = t1
            out[-1]["length"] = out[-1]["t1"] - out[-1]["t0"]
            continue
        over = [r for s0, s1, r in cov if s0 <= t0 + eps and s1 >= t1 - eps]
        term = FH.termination(covering_bands=[dict(r, coverage=1.0) for r in over],
                              inside_plate=bool(inside and inside(t0, t1)), plate_t_cm=plate_t_cm)
        if out and out[-1]["termination"] == term and abs(out[-1]["t1"] - t0) <= eps:
            out[-1]["t1"] = t1
            out[-1]["length"] = out[-1]["t1"] - out[-1]["t0"]
            continue
        out.append({"t0": t0, "t1": t1, "length": t1 - t0, "termination": term})
    return out


def policy_record() -> dict:
    rec = {"policy_id": POLICY_ID, "base": FH.POLICY_ID,
           "rule": "a wall face is split at the ends of the beam bands over it; each piece takes the deepest bound band "
                   "covering the whole piece, else the closed slab plate, else UNKNOWN (reported, never filled)",
           "never": ["one termination for a partly covered face", "an UNKNOWN piece measured at an assumed height"]}
    rec["digest"] = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()
    return rec
