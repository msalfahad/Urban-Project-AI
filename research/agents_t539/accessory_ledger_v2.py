"""T-539 (research, unwired): masonry ACCESSORY LEDGERS V2 that read COLUMN_END_CENSUS_V3 (R-T532-1) as well as the
interior junctions of T-355 / T-317, so a block run that ENDS on an RC column face gets its ties and its joint mesh.

PHYSICAL ELEMENTS (ERS s.2.1; owner Q-77 answer 2026-10-29: three separate optional items, never in the block m2)
- SHARMAT tie (pcs): one metal tie per tie level at every physical block-end-to-column-face junction; a tie level is
  the bed joint over every third course (R-T355-1). It depends on the COURSE HEIGHT of the block actually laid.
- BED-JOINT MESH STRIP (m.l): a strip in the bed joint over every third course ALONG the wall, over the block present.
  It ends at a column face; it does not run up the joint. A run end that stops on a column face with the run's clear
  length unchanged (gap within one joint) adds NO strip: the strip length is the block run, which did not move.
- PLASTER-STAGE JOINT MESH (B9-03, m.l): a vertical strip over the block-to-column joint inside each finished side, the
  joint clipped to the finished band (R-T317-4); owner band and drawing-derived band side by side (R-T317-5). It does
  NOT depend on the course module (it is a height, not a course count).
The '+40.90 m.l' carried on the board from T-526 is this third item (V joints, T-317), not the bed-joint strip.

RULE R-T539-1 COLUMN_END_ACCESSORY_LEDGER_V2 (every villa; provenance F-T536-1, T-539)
1. Junction population = the merged interior junctions (one per block-segment / column boundary, R-T355-3) PLUS every
   END junction of R-T532-1 / R-T526-1; a key (wall, column, face) twice is refused. An END junction that is HELD in the
   census (partial or gapped contact, unknown piece kind) is HELD here by the same name, never 0.
2. Course module from R-T533-1 (block type, thickness) only: the sourced register entry gives block height + bed joint;
   no entry -> every tie and every strip level of that wall HELD by name, never 0 and never the module of another
   thickness; the named what-if modules are shown beside (figures, not quantities). WHITE (thin-bed AAC) HELD (Q-60).
3. Ties per junction = R-T355-1 levels on the block beside the column; block top unknown -> HELD.
4. Strip at an END junction: 0 m.l added when the run's clear length is unchanged (d_length 0, gap <= one joint);
   any other end is refused here (its length effect belongs to the census, not to this ledger).
5. V-joint mesh at an END junction, per finished side: owner band = min(block top, band top) - band bottom; drawing
   band = block top - FFL; an EXTERIOR (Sigma) side carries one band (owner = drawing, R-T355-4 table convention).
   A side whose finish or band is unknown, or a block top unknown -> HELD.
6. No head from a sliver (F-C-T532-1): when the masonry piece at the run end is shorter than SLIVER_M (5 mm) its own
   head is never used. If the next piece inward lies under the SAME member with the same top (the sliver is a cut of
   that member's own band: one beam spans the column face), the head is that member's soffit; under any other member
   or face the head beside the column is HELD by name (ties and V joints), never borrowed from the neighbour.
7. One proposed BOQ line family per item (id, unit, status, owner trade); the three are never summed together.

Units: metres; a thickness or top given in millimetres is refused by the imported validators.
"""

from __future__ import annotations

from dataclasses import dataclass

TOL = 1e-6
RULE = "R-T539-1 COLUMN_END_ACCESSORY_LEDGER_V2"
SCHEMA = "T539_ACCESSORY_LEDGER_V2"
WHITE_HELD = "WHITE (AAC) block, thin-bed adhesive: no adhesive specification, two face families (Q-60): course HELD"


SLIVER_M = 0.005
SLIVER_HELD = "end piece is a sub-5 mm sliver: the head beside the column is not taken from it (F-C-T532-1)"


class LedgerV2Error(ValueError):
    pass


def end_head(end_piece, next_piece=None):
    """R-T539-1 item 6: (top, held, sliver) of the block beside an END column. Each piece is (length, top, member);
    next_piece is the piece inward of the end piece (None when the run has one piece)."""
    L, top, mem = end_piece
    if L is None or L <= 0:
        raise LedgerV2Error(f"end piece length {L}")
    if L >= SLIVER_M - TOL:
        return (top, "" if top is not None else "block top beside the column not established", "")
    if next_piece is not None:
        L2, top2, mem2 = next_piece
        if L2 >= SLIVER_M - TOL and mem and mem == mem2 and top == top2:
            return (top2, "" if top2 is not None else "block top beside the column not established",
                    f"SAME_MEMBER ({mem}): sliver {L:.6f} m is a cut of the member over the next piece")
    return None, SLIVER_HELD, f"OTHER_MEMBER: sliver {L:.6f} m ({mem or 'no member'})"


@dataclass(frozen=True)
class Course:
    block_h: float
    joint: float
    source: str
    status: str

    @property
    def module(self):
        return self.block_h + self.joint


def course(block_h, joint, source, status):
    if not source:
        raise LedgerV2Error("a course needs its source")
    if not (0.05 <= block_h <= 0.40) or not (0.0 < joint <= 0.03):
        raise LedgerV2Error(f"course {block_h} + {joint} m outside the metre ranges (units?)")
    return Course(float(block_h), float(joint), source, status)


def levels(c: Course, top: float):
    """R-T355-1: tie / strip levels (joint over course 3k) on a block of the given top above the wall base."""
    if top is None:
        return None
    if not (0.5 <= top <= 10.0):
        raise LedgerV2Error(f"block top {top} m outside 0.5 .. 10.0 m (units?)")
    out, k = [], 1
    while True:
        z = 3 * k * c.module
        if z + c.joint >= top - TOL:
            return out
        out.append(round(z, 6))
        k += 1


def course_for(resolve, register, block_type, t_m):
    """R-T539-1 item 2 through R-T533-1: (Course, None) or (None, held text). `resolve` is block_module_v1.resolve."""
    if block_type == "WHITE":
        return None, WHITE_HELD
    if block_type != "BLACK":
        raise LedgerV2Error(f"block type {block_type!r}")
    r = resolve(register, block_type, t_m)
    if r["status"] != "RESOLVED":
        return None, f"{r['status']}: {r['held']}"
    e = r["entry"]
    return course(e.face_h_m, e.bed_joint_m, e.citation, e.status), None


def tie_record(junction_state, junction_held, c, course_held, top, scenarios=()):
    """ties at one junction. scenarios: [(sid, Course)] what-if modules shown beside a HELD module (never summed)."""
    fig = {sid: (None if top is None else len(levels(sc, top))) for sid, sc in scenarios}
    if junction_state != "LISTED":
        return {"state": "HELD", "ties": None, "held": junction_held or "junction HELD in the census", "figures": fig}
    if c is None:
        return {"state": "HELD", "ties": None, "held": course_held, "figures": fig}
    if top is None:
        return {"state": "HELD", "ties": None, "held": "block top beside the column not established", "figures": fig}
    return {"state": "MEASURED", "ties": len(levels(c, top)), "held": "", "figures": fig}


def tie_range(c, top_lo, top_hi):
    """ties at both bounds of a block top known only as a range (e.g. a storey datum not printed)."""
    a, b = len(levels(c, top_lo)), len(levels(c, top_hi))
    return (min(a, b), max(a, b))


def end_strip_delta(d_length_m, gap_m, joint_m):
    """R-T539-1 item 4: the strip added by an END junction."""
    if gap_m is None or d_length_m is None:
        raise LedgerV2Error("end strip: gap / length change not established")
    if gap_m > joint_m + TOL:
        raise LedgerV2Error(f"end gap {gap_m} m beyond one joint {joint_m} m: length effect belongs to the census")
    if abs(d_length_m) > TOL:
        raise LedgerV2Error(f"end moves the run length by {d_length_m} m: not evaluated here")
    return 0.0


@dataclass(frozen=True)
class FinishedSide:
    side: str                 # INT / INT-A / INT-B / EXT
    finish: str               # PLASTER / TILE / SIGMA / CLADDING / NONE / HIDDEN
    band_bottom: float | None
    band_top: float | None


def end_vjoint(sides, top, ffl):
    """R-T539-1 item 5: per finished side the V joint at one end junction, owner band and drawing band."""
    out = []
    if len({s.side for s in sides}) != len(sides):
        raise LedgerV2Error("a side listed twice")
    for s in sides:
        if s.finish in ("NONE", "HIDDEN"):
            continue
        rec = {"side": s.side, "finish": s.finish}
        if top is None or s.band_top is None or s.band_bottom is None:
            out.append({**rec, "owner_m": None, "drawing_m": None, "state": "HELD",
                        "held": "block top or finished band not established"})
            continue
        own = max(0.0, min(top, s.band_top) - s.band_bottom)
        drw = own if s.side == "EXT" else top - ffl
        out.append({**rec, "owner_m": round(own, 6), "drawing_m": round(drw, 6), "state": "MEASURED", "held": ""})
    return out


def merge_population(interior, ends):
    """R-T539-1 item 1: one key (wall, column, face) once over the interior + end populations."""
    seen, out = set(), []
    for src, rows in (("INTERIOR", interior), ("END", ends)):
        for r in rows:
            k = (r["wall_id"], r["column_at"], r["face"])
            if k in seen:
                raise LedgerV2Error(f"junction {k} counted twice")
            seen.add(k)
            out.append(dict(r, population=src))
    return out


def no_zero_held(rows, qty_keys):
    for r in rows:
        if str(r.get("state", "")).startswith("HELD"):
            for k in qty_keys:
                if r.get(k) not in (None, ""):
                    raise LedgerV2Error(f"{r.get('wall_id')}: a HELD record carries {k}={r.get(k)!r}")


def tie_totals(rows):
    m = [r for r in rows if r["state"] == "MEASURED"]
    h = [r for r in rows if r["state"] != "MEASURED"]
    return {"junctions": len(rows), "measured_junctions": len(m), "ties_measured": sum(r["ties"] for r in m),
            "held_junctions": len(h)}


def line_families():
    """R-T539-1 item 6: proposed BOQ lines, one per item, never summed with each other or with the block m2."""
    return [
        {"proposed_code": "MAS.TIE.SHARMAT", "family": "B9-06 (proposed, missing category)",
         "item_en": "Wall-to-column ties (sharmat), one per 3 courses at every block-to-column junction",
         "item_ar": "شرمات", "unit": "pcs", "owner_trade": "masonry (blocks section, optional, priced by quality)",
         "status": "PROPOSED: measured part ASSUMED — OWNER-APPROVED (Q-77, Q-75 0.20 m module); 0.15 m and white "
                   "walls HELD (R-T533-1 / Q-60); SPECIFICATION HELD (material, size, embedment, fixing; structural "
                   "consultant RFI, never a design approval)",
         "source": "Q-77 answer 2026-10-29 21:22; R-T355-1/-3; R-T532-1; R-T539-1"},
        {"proposed_code": "MAS.MESH.BED_JOINT", "family": "B9-07 (proposed, missing category)",
         "item_en": "Bed-joint mesh strip every 3 courses along the wall (net installed)", "item_ar": "شبك مونة",
         "unit": "m.l", "owner_trade": "masonry (blocks section, optional, priced by quality)",
         "status": "PROPOSED: 0.20 m black walls ASSUMED — OWNER-APPROVED; 0.15 m black walls HELD (R-T533-1); white "
                   "HELD (Q-60); lap / waste procurement, apart",
         "source": "Q-77 answer 2026-10-29 21:22; R-T355-1/-2/-6/-7; R-T539-1"},
        {"proposed_code": "MAS.MESH.JOINT", "family": "B9-03 (existing family, NOT_IMPLEMENTED)",
         "item_en": "Plaster-stage mesh over block-to-concrete joints, by face class (A plastered, B tiled, C exterior "
                    "Sigma) as separate lines; MIXED / UNKNOWN sides HELD", "item_ar": "شبك فواصل",
         "unit": "m.l", "owner_trade": "plaster stage (separate calculated item, Q-77)",
         "status": "PROPOSED: owner band and drawing-derived band both shown, neither chosen (Q-77); class D excluded",
         "source": "Q-77 answer; R-T317-4/-5; R-T355-4; R-T539-1"},
    ]
