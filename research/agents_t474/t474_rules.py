"""T-474 part 1: FORMWORK PIECE CENSUS rules (every villa; research only, wired by no method).

Physical element first (ERS s.2.1). A formwork piece is ONE concrete surface cast against a temporary form. It bounds
one member and belongs beside the candidate line that carries that member's concrete, never inside its m3. A surface
cast against blinding, masonry, an earlier-cast member, screed / fill, or against earth where a detail prints it, has no
form and is no piece. Below the existing ground the FORMED / EARTH_CAST reading is the open owner question OQ-10: both
readings travel together on one blank piece, never summed, never chosen.

Rules (proposed, PROJECT-INDEPENDENT; provenance: T-163 r3 / T-264 r4 / T-293 / T-308 r5 / T-332 r2 / T-352 ledgers,
the T-199 R-T199-1 booking rule and UP-QTY-STATUS-001; this file adds the census, not a new measuring method):

  R-T474-1  PIECE CLASSES: each structural element class has a fixed list of candidate faces (PIECE_CLASSES); a face
            the list does not name for its class is refused (no invented face kind).
  R-T474-2  NO FORM where the face is cast against NO_FORM_CONTACTS (blinding, masonry, an earlier-cast member, screed
            or fill, earth printed by a detail): such a face carries no m2 and is never a piece (a figure is refused).
  R-T474-3  A piece on a member that is NOT_PRESENT / NOT_APPLICABLE / EXCLUDED is refused (its formwork leaves with
            the member; it is never a 0 line).
  R-T474-4  HELD is blank: a held piece carries m2 None with its bounds or held_from beside; a 0.0 on a held piece is
            refused; held pieces are never summed.
  R-T474-5  ONE SURFACE ONCE: two pieces on the same edge whose vertical intervals overlap describe one form surface;
            the overlap is booked once, on the member whose concrete owns it (a slab owns its thickness band at a
            free edge; a parapet face starts at the slab top). A parapet face given from the slab soffit is netted.
  R-T474-6  BASIS: a CALCULATED piece is labelled VERIFIED_GEOMETRY only when (a) its concrete line is in a Checker
            VERIFIED record (verdict id carried) and (b) the piece is that verified geometry itself (slab soffit =
            the verified net panel area, within TOL_GEOM 0.001 m2, the residual named); the piece is still
            CALCULATED formwork (no formwork re-measure yet), never VERIFIED. Every other valued piece is
            CALCULATED in its concrete line's state; a piece on a held concrete line is HELD with that line's reason.
  R-T474-7  UNITS: lengths in m only (a 'mm' piece is refused); m2 = length x height of the formed face; geometry is
            rotation / mirror invariant (lengths from point pairs).
"""

from __future__ import annotations

import math

NO_FORM_CONTACTS = ("BLINDING", "MASONRY", "EARLIER_MEMBER", "SCREED_OR_FILL", "EARTH_PRINTED")
FORM_CONTACTS = ("FORM", "OQ10")            # OQ10: below the existing ground, FORMED / EARTH_CAST pair (owner question)
DEAD_MEMBER_STATES = ("NOT_PRESENT", "NOT_APPLICABLE", "NOT_APPLICABLE_WITH_EVIDENCE", "EXCLUDED",
                      "EXCLUDED_WITH_REASON")
LIVE_STATES = ("SOURCE_DERIVED", "PROVISIONAL", "MEASURED")
TOL = 1e-6
TOL_GEOM = 1e-3     # m2: two independent 4-dp ledger roundings / split halves; 1 mm on a 1 m edge (R-T474-6)

# element class -> {face kind: definition}. The face kinds are those the merged ledgers use.
PIECE_CLASSES = {
    "FOOTING": {"SIDE": "the four vertical faces; base on blinding (no form), top cast free (no form); below EG OQ-10",
                "COVER": "the face band above the footing top up to EG where the footing is cast higher (OQ-10)",
                "NOTCH": "re-entrant faces of a notched footing outline (OQ-10)"},
    "NECK": {"SIDE": "the four faces of the column neck from the footing top to the ground-beam soffit (OQ-10)"},
    "GROUND_BEAM": {"SIDE": "both vertical faces; above N.G. FORMED, below EG OQ-10; base on blinding (no form)",
                    "ARC_FACE": "curved vertical face of a ring beam, on its drawn arc length",
                    "END": "a free end only; an end closing on a drawn member face is no face",
                    "COVER": "the band above the beam top to the slab-on-grade where cast higher (OQ-10)"},
    "STRAP": {"SIDE": "both faces (OQ-10)", "SOFFIT": "soffit where not on blinding (OQ-10)"},
    "BOUNDARY": {"SIDE": "boundary wall / beam faces", "END": "free ends", "EDGE_BAND": "exposed edge band"},
    "COLUMN": {"SOFFIT": "the shaft faces from floor to the controlling soffit, joint faces at framing beams apart",
               "SIDE": "information rows of the shaft (not a quantity)"},
    "JOINT": {"JOINT": "the column face strip inside the beam / slab depth where no beam frames in"},
    "BEAM": {"BEAM": "soffit (width x clear span) and the sides below the slab (depth - slab) x span; a side cast "
                     "against a wall or an earlier member has no form"},
    "SLAB": {"SLAB": "soffit: the net panel between member faces (beam / column faces), openings deducted",
             "SOFFIT": "soffit of a panel with no member walk (held)"},
    "SLAB_EDGE": {"SLAB_EDGE": "slab-thickness band at a free edge (plate perimeter, openings, steps); booked on the "
                               "member line the ledger binds it to"},
    "STAIR": {"SOFFIT": "waist / landing soffit on its sloping length", "RISER": "riser forms",
              "SIDE": "open sides (strings) where the flight is not cast against a wall",
              "FLIGHT_SIDE": "a flight's open side face (T-352), on its profile", "LANDING_EDGE": "landing edge band",
              "JUNCTION_STRIP": "strip where a flight meets a landing / slab (held where not drawn)"},
    "LIFT": {"SIDE": "lift-pit wall faces per metre of pit height (inner FORMED, outer OQ-10)"},
    "PARAPET": {"SIDE": "both faces of the RC part from the slab top"},
    "DOME": {"SOFFIT": "shell soffit forms", "SIDE": "drum / edge faces"},
    "POOL": {"SIDE": "water face and outer face above EG; below EG OQ-10", "SOFFIT": "none: the base is on blinding"},
}


class PieceError(ValueError):
    pass


def _r(x):
    return None if x is None else round(x + 0.0, 6)


def length(p, q):
    """distance between two plan points (m); rotation / mirror invariant."""
    return math.hypot(q[0] - p[0], q[1] - p[1])


def piece(*, member, cls, kind, contact, length_m=None, height_m=None, m2=None, unit="m", held=None, lo=None, hi=None,
          z=None, ref=""):
    """-> one piece record, or None for a NO_FORM face (R-T474-2). held: reason string (R-T474-4)."""
    if unit != "m":
        raise PieceError(f"{member} {kind}: unit {unit!r} (lengths in m only, R-T474-7)")
    if cls not in PIECE_CLASSES or kind not in PIECE_CLASSES[cls]:
        raise PieceError(f"{member}: face kind {kind!r} is not a face of class {cls} (R-T474-1)")
    if contact in NO_FORM_CONTACTS:
        if m2 not in (None, 0) or (length_m and height_m):
            raise PieceError(f"{member} {kind}: cast against {contact}: no form, a figure is refused (R-T474-2)")
        return None
    if contact not in FORM_CONTACTS:
        raise PieceError(f"{member} {kind}: unknown contact {contact!r}")
    if held is not None:
        if m2 is not None:
            raise PieceError(f"{member} {kind}: held piece carries {m2} (held is blank, never 0, R-T474-4)")
        return {"member": member, "class": cls, "kind": kind, "contact": contact, "m2": None, "held": held,
                "lo": _r(lo), "hi": _r(hi), "z": z, "ref": ref}
    if contact == "OQ10":
        raise PieceError(f"{member} {kind}: below EG the FORMED / EARTH_CAST pair is open (OQ-10): held, not valued")
    if m2 is None:
        if length_m is None or height_m is None:
            raise PieceError(f"{member} {kind}: no area and no length x height")
        m2 = length_m * height_m
    if not m2 > 0:
        raise PieceError(f"{member} {kind}: area {m2} must be positive")
    return {"member": member, "class": cls, "kind": kind, "contact": contact, "m2": _r(m2), "held": None,
            "lo": None, "hi": None, "z": z, "ref": ref}


def net_edge_overlap(owner, other):
    """R-T474-5: owner (e.g. slab edge, z=(soffit, top)) keeps its band; other (e.g. parapet face, z=(base, top)) is
    cut to the part above the owner's band on the same edge length. -> the netted other piece."""
    (a0, a1), (b0, b1) = owner["z"], other["z"]
    ov = max(0.0, min(a1, b1) - max(a0, b0))
    if ov <= TOL:
        return other
    h = (b1 - b0) - ov
    if h <= TOL:
        raise PieceError(f"{other['member']}: face lies wholly inside {owner['member']}'s band (one surface twice)")
    L = other["m2"] / (b1 - b0)
    return dict(other, m2=_r(L * h), z=(max(b0, a1), b1), netted=_r(L * ov),
                ref=(other.get("ref") or "") + f"; {ov:.3f} m overlap with {owner['member']} booked once there")


def census(pieces, members, verified=None):
    """pieces: piece records (None entries = NO_FORM faces, dropped); members: {member: {"state", "reason",
    "verified_area_m2" (optional)}}; verified: {member: verdict id}. -> {"pieces": [...], "by_class": {...}}."""
    verified = verified or {}
    out, by = [], {}
    for p in pieces:
        if p is None:
            continue
        m = members.get(p["member"])
        if m is None:
            raise PieceError(f"{p['member']}: no concrete member carries this piece")
        if m["state"] in DEAD_MEMBER_STATES:
            raise PieceError(f"{p['member']} is {m['state']}: its formwork leaves with it (R-T474-3)")
        q = dict(p)
        if q["m2"] is None:
            q["basis"] = f"HELD: {q['held']}"
        elif m["state"] not in LIVE_STATES:
            q.update(m2=None, held=f"concrete line {m['state']}: {m.get('reason') or ''}".strip(),
                     held_from=p["m2"], basis=f"HELD with its concrete line ({m['state']})")
        elif p["member"] in verified and m.get("verified_area_m2") is not None and \
                abs(m["verified_area_m2"] - q["m2"]) <= TOL_GEOM and q["kind"] in ("SLAB",):
            q["basis"] = f"VERIFIED_GEOMETRY {verified[p['member']]}"
        else:
            q["basis"] = f"CALCULATED ({m['state']})"
        out.append(q)
        b = by.setdefault(q["class"], {"pieces": 0, "valued_m2": 0.0, "held": 0, "verified_geometry_m2": 0.0})
        b["pieces"] += 1
        if q["m2"] is None:
            b["held"] += 1
        else:
            b["valued_m2"] = _r(b["valued_m2"] + q["m2"])
            if q["basis"].startswith("VERIFIED_GEOMETRY"):
                b["verified_geometry_m2"] = _r(b["verified_geometry_m2"] + q["m2"])
    return {"pieces": out, "by_class": dict(sorted(by.items()))}
