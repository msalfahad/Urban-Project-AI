"""T-402 rules: resolving a HELD beam line one by one (research; every villa; provenance T-402, Alsenan the first run).

R-T402-1 RESULT CLASS. A held beam line is VALUE only when width, depth and face-to-face length each rest on a drawing
         source of their own that no other source of the same set contradicts (a printed schedule row bound to the
         member's own mark AND a drawn width that agrees, or a dimensioned section that cuts the member). BOUNDED when
         two printed / drawn readings of the SAME fact disagree (schedule width vs drawn edges, two marks on one span):
         the bound is the pair of readings only (min, max), never a third value and never 'the larger'. HELD otherwise,
         with the exact missing fact named; a bound is carried only when every input of it is stated with its basis.
R-T402-2 LENGTH. The length of a beam piece is face to face between the members that own the crossings (column to the
         slab top, carrier beam face, T-394 R-T394-1 / T-395 R-T395-2); a centre-line or schedule span is refused.
R-T402-3 NO BORROWED SECTION. An unlabelled piece never takes the section of the neighbour mark it continues: one pair
         of drawn edge lines may run through several members of different marks, so edge continuity does not bind a
         mark. Its depth is a stated bound (the envelope of the printed depths of the set, labelled SCHEDULE_ENVELOPE),
         never a value; a scaled reading of an undimensioned section is an INDICATION, never a quantity.
R-T402-4 NOT A BEAM. A drawn band identified as a slab-edge projection (rounded plan corners, the slab note referring
         its detail to the architectural drawings) carries its plan area only; a beam-schedule depth envelope is not a
         bound for it (its depth is not a beam property). HELD BLANK, never 0.
R-T402-5 (r2) SLAB PAIRING IS A BOUND. Which face an alternative width moves is the designer's: each face sees slab,
         an opening, a held neighbour or nothing drawn. The slab strip given up / taken is |db| x t x Ls, Ls the face
         length that sees slab; over the two faces it is the bound [min Ls_lo, max Ls_hi] (Ls_lo = slab proven by a bar
         or slab text, Ls_hi adds the undetermined / no-evidence length), and the net concrete shift db x (L x D - Ls x t)
         is the matching bound. A single figure only where both faces see the same thing over the same length.
R-T402-6 (r2) A SECTION IS UNDIMENSIONED ONLY AFTER ITS DIMENSIONS ARE LISTED. Before calling a section 'no dimension',
         list its DIMENSION entities with their DIMLFAC (printed value = measurement x DIMLFAC) and their axis (the rotated
         dimension's angle). A vertical chain that closes the outline height prints the depth (DIMENSIONED_SECTION); a
         size not dimensioned stays a scaled INDICATION, never a quantity; a note on a bar leader ('AS PER SCH.') is a bar
         note, not a size note. A rounded corner printed by its own two dimensions (equal horizontal and vertical
         extents) on a drawn arc is part of the section: area b x D - r^2 (1 - pi/4). Provenance: T-402 Checker
         2026-10-31 (section D-D); every villa.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

VALUE, BOUNDED, HELD = "VALUE", "BOUNDED", "HELD"


class RefusedReading(ValueError):
    """A reading the method refuses (centre-line span, borrowed section, held as 0, scaled value)."""


@dataclass
class Reading:
    """One drawing reading of one fact (metres)."""
    value: float | None
    source: str              # 'SCHEDULE_ROW', 'DRAWN_EDGES', 'DIMENSIONED_SECTION', 'SCHEDULE_ENVELOPE', 'SCALED_SECTION',
    #                          'NEIGHBOUR_MARK', 'CENTRE_LINE', 'FACE_TO_FACE'
    ref: str = ""


ADMISSIBLE_SECTION = {"SCHEDULE_ROW", "DRAWN_EDGES", "DIMENSIONED_SECTION"}
ADMISSIBLE_LENGTH = {"FACE_TO_FACE"}


@dataclass
class HeldPiece:
    line_id: str
    mark: str | None                     # None = no label on the piece
    widths: list = field(default_factory=list)   # Readings of b
    depths: list = field(default_factory=list)   # Readings of D
    length: Reading | None = None        # face to face
    projection: bool = False             # R-T402-4
    plan_area_m2: float | None = None
    section_deduct_m2: float = 0.0       # R-T402-6 printed corner round(s) of a dimensioned section


def _check_length(r: Reading | None) -> float:
    if r is None or r.value is None:
        raise RefusedReading("length missing: a piece without a face-to-face length is HELD, never 0")
    if r.source not in ADMISSIBLE_LENGTH:
        raise RefusedReading(f"length from {r.source} refused (R-T402-2: face to face only)")
    if r.value <= 0:
        raise RefusedReading("non-positive length")
    return r.value


def _admissible(readings, kind):
    out = []
    for r in readings:
        if r.source == "NEIGHBOUR_MARK":
            raise RefusedReading(f"{kind} borrowed from a neighbour mark refused (R-T402-3)")
        if r.source == "CENTRE_LINE":
            raise RefusedReading(f"{kind} from a centre line refused")
        if r.source in ADMISSIBLE_SECTION and r.value is not None:
            if r.value <= 0:
                raise RefusedReading(f"{kind} <= 0 refused (held is blank, never 0)")
            out.append(r)
    return out


def resolve(p: HeldPiece) -> dict:
    """Result of one held piece: {'result', 'm3', 'low', 'high', 'missing', 'basis'}; m3 None unless VALUE."""
    if p.projection:
        return {"result": HELD, "m3": None, "low": None, "high": None, "plan_area_m2": p.plan_area_m2,
                "missing": "projection depth / build-up (architectural detail per the slab note); cast with the slab?",
                "basis": "R-T402-4 plan area only"}
    L = _check_length(p.length)
    ws = _admissible(p.widths, "width")
    ds = _admissible(p.depths, "depth")
    envelope = [r for r in p.depths if r.source == "SCHEDULE_ENVELOPE"]
    scaled = [r for r in p.depths + p.widths if r.source == "SCALED_SECTION"]
    if p.mark is None and any(r.source == "SCHEDULE_ROW" for r in p.widths + p.depths):
        raise RefusedReading("a schedule row cannot bind an unlabelled piece (R-T402-3)")
    if not ws:
        return {"result": HELD, "m3": None, "low": None, "high": None, "missing": "width not drawn or printed",
                "basis": "R-T402-1"}
    bw = sorted({round(r.value, 4) for r in ws})
    if ds:
        dd = sorted({round(r.value, 4) for r in ds})
        if len(bw) == 1 and len(dd) == 1:
            a = bw[0] * dd[0] - p.section_deduct_m2
            if a <= 0:
                raise RefusedReading("section deduction exceeds the section")
            return {"result": VALUE, "m3": round(a * L, 6), "low": None, "high": None, "missing": "",
                    "basis": "R-T402-1 b x D x L face to face" + (" - printed round (R-T402-6)" if p.section_deduct_m2 else "")}
        k = p.section_deduct_m2
        return {"result": BOUNDED, "m3": None, "low": round((bw[0] * dd[0] - k) * L, 6), "high": round((bw[-1] * dd[-1] - k) * L, 6),
                "missing": "which printed / drawn reading is the structure (designer)",
                "basis": "R-T402-1 pair of readings"}
    out = {"result": HELD, "m3": None, "low": None, "high": None, "missing": "depth not printed for this piece",
           "basis": "R-T402-3", "indication": [(r.value, r.ref) for r in scaled]}
    if envelope:
        lo, hi = min(r.value for r in envelope), max(r.value for r in envelope)
        out.update(low=round(bw[0] * lo * L, 6), high=round(bw[-1] * hi * L, 6), basis="R-T402-3 SCHEDULE_ENVELOPE")
    return out


def refuse_zero(m3) -> None:
    """A held line written as 0 is refused (blank stays blank)."""
    if m3 is not None and float(m3) == 0.0:
        raise RefusedReading("held line written as 0 refused")


def slab_pairing(b_drawn: float, b_alt: float, length: float, slab_t: float) -> dict:
    """R-T402-5 WIDTH ALTERNATIVE MOVES THE SLAB TOO. The slab line is net of the DRAWN beam faces, so an alternative
    width changes the slab by the strip between the two faces: wider = OVERLAP |db| x L x t that the slab must give up
    (else billed twice), narrower = GAP |db| x L x t the slab must take (else billed nowhere). The total concrete moves
    only by db x L x (D - t); a beam bound is never published without its slab pairing (every villa; provenance T-402)."""
    if min(b_drawn, b_alt, length, slab_t) <= 0:
        raise RefusedReading("non-positive input to the slab pairing")
    db = b_alt - b_drawn
    m3 = round(abs(db) * length * slab_t, 6)
    return {"kind": "OVERLAP" if db > 0 else ("GAP" if db < 0 else "NONE"), "slab_m3": m3}


def slab_pairing_bound(b_drawn: float, b_alt: float, length: float, depth: float, slab_t: float, faces) -> dict:
    """R-T402-5 (r2): faces = [(Ls_lo, Ls_hi), (Ls_lo, Ls_hi)] slab-seeing length of each face (m). Returns the slab strip
    bound (m3, OVERLAP when wider, GAP when narrower) and the net concrete shift bound db x (L x D - Ls x t)."""
    if min(b_drawn, b_alt, length, depth, slab_t) <= 0:
        raise RefusedReading("non-positive input to the slab pairing")
    if len(faces) != 2:
        raise RefusedReading("a beam has two faces: give both (the moved face is not known)")
    for lo, hi in faces:
        if lo is None or hi is None or lo < 0 or hi < lo or hi > length + 0.05:
            raise RefusedReading("face slab length must be 0 <= lo <= hi <= L")
    db = b_alt - b_drawn
    lo = min(f[0] for f in faces)
    hi = min(max(f[1] for f in faces), length)
    lo = min(lo, hi)
    s_lo, s_hi = round(abs(db) * slab_t * lo, 6), round(abs(db) * slab_t * hi, 6)
    t1, t2 = db * (length * depth - hi * slab_t), db * (length * depth - lo * slab_t)
    return {"kind": "OVERLAP" if db > 0 else ("GAP" if db < 0 else "NONE"), "slab_m3_low": s_lo, "slab_m3_high": s_hi,
            "point": s_lo == s_hi, "total_shift_low": round(min(t1, t2), 6), "total_shift_high": round(max(t1, t2), 6)}


def depth_from_chain(v_printed_m, outline_h_m: float, tol: float = 0.01) -> float:
    """R-T402-6: the depth printed by a vertical dimension chain, accepted only when the chain closes the outline height."""
    if not v_printed_m:
        raise RefusedReading("no vertical dimension: the depth is not printed (list the DIMENSION entities first)")
    d = sum(v_printed_m)
    if d <= 0 or abs(d - outline_h_m) > tol * outline_h_m:
        raise RefusedReading(f"vertical chain {d:.4f} does not close the outline height {outline_h_m:.4f}")
    return round(d, 6)


def corner_round_m2(r_h: float | None, r_v: float | None, arc_drawn: bool) -> float:
    """R-T402-6: area removed by a printed rounded corner (both extents printed and equal, arc drawn); else refused."""
    if r_h is None or r_v is None:
        raise RefusedReading("a rounded corner needs both printed extents")
    if not arc_drawn:
        raise RefusedReading("printed round without a drawn arc")
    if r_h <= 0 or abs(r_h - r_v) > 0.005:
        raise RefusedReading("unequal or non-positive round extents: not a circular round")
    r = (r_h + r_v) / 2
    return round(r * r * (1 - math.pi / 4), 8)


def is_size_note(text: str, on_bar_leader: bool) -> bool:
    """R-T402-6: 'AS PER SCH.' on a bar leader refers to the bars; it neither prints nor withholds a size."""
    if on_bar_leader:
        return False
    return bool(text.strip())
