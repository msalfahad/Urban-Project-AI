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
"""
from __future__ import annotations

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
            return {"result": VALUE, "m3": round(bw[0] * dd[0] * L, 6), "low": None, "high": None, "missing": "",
                    "basis": "R-T402-1 b x D x L face to face"}
        return {"result": BOUNDED, "m3": None, "low": round(bw[0] * dd[0] * L, 6), "high": round(bw[-1] * dd[-1] * L, 6),
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
