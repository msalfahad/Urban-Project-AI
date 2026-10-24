"""T-264 formwork r4 (research only, NOT engine code, nothing wired or released): the formwork contact areas of the
concrete components that changed or were added since formwork r3 (T-163 MERGED 659f889f, 2026-10-23 00:09), as a delta
ledger r3 -> r4 on the merged r3 ledger, every other r3 line carried unchanged.

Physical element (ENGINEERING_REASONING_STANDARD s.2.1): the contact area of a formwork face = the concrete surface
cast against a form, from the SAME drawn geometry as the concrete line that owns the element: a curved member's faces
along its own arcs (R x sweep, never chords); a beam ending on an oblique carrier stops at the carrier face on each of
its own edges; a buried face is cast against a form or against the ground (owner question OQ-10, carried as the two
alternatives FORMED / EARTH_CAST, never summed, never chosen); a face is EARTH_CAST as a fact only where a printed
section shows it so; a face that stands above the outer natural ground (p.13 exterior ground beam: soffit on the
"Outer Normal ground level", T-253) has nothing to be cast against and is formed (CALCULATED, outside OQ-10).
Soffits / sides / edges / joints are kept apart; a column-beam intersection is counted once (the column owns it,
R-CONC-OWN-1) and D-N10-04 stays named where the framing is not in the register.

Changes since r3, each a row of the delta (source of each: the merged ledger named):
  1. GF void ring B7 (T-252 MERGED b37be82d, R-BEAM-CURVED-AREA-2): ring soffit 0.666406 m2 from its own arcs; its
     outer arcs to the slab at D - t, its inner (void) arcs at the full depth (D - t below the slab line + the t band:
     one owner for the opening face, r3 rule D-T163-3), the CB1 face the void reaches (2A9) at full depth; r3's held
     RING_MIX rows and the HELD pool-court slab band leave (the band is now measured on the ring).
  2. B4 / CB4 ends on the oblique B27 face (T-252 R-BEAM-END-OBLIQUE-2): r3's drawing-face walk already ended both
     edges on the carrier face (T-139 faces GF-153 / GF-129 carry both full edges): delta 0, cited.
  3. Ground beams (T-242 MERGED 9455a63d + T-253 MERGED dff9cb79, lengths from T-230): every run re-based: interior
     runs at their p.13 class (OQ-10 pair), main-house exterior runs at D 0.95 (outer face above N.G. formed, inner
     face OQ-10), the ring ARC:157+158 on its arcs, annex runs CONFLICT (no value), court runs HELD, tee covers per
     carrier; the boundary G.B 44.07 m x 0.40 (OQ-10 pair, its 810 west end face HELD).
  4. Straps on their axis length (T-174 MERGED 984ebbe1, Q-74) and the footing faces they cover (chord x min(D, H)).
  5. Footings (T-233 MERGED 2ecb5bf0, T-239 MERGED 3c9b1484): FN / F9 notch faces settled (one bottom stack, F9 owns),
     F10 + F (1B1B) range = exactly its two recomputed readings.
  6. Columns (T-248 MERGED 13aa1e2c line, T-256 MERGED 74c966b1): the 5 NOT_PRESENT upper lines leave with their
     source (no 0 line); 15 section CONFLICT columns carry the drawn and the printed perimeter as a range (shaft and
     joint); planted COL-1F-57 measured from the slab top it stands on; the 2F shafts HELD on the roof datum (D-39).

Usage:
  python3 -I research/agents_t264/formwork_r4.py --check          synthetic villa W (not Alsenan): hand values asserted
  python3 -I research/agents_t264/formwork_r4.py <out_dir>        Alsenan r4 from committed inputs only
No drawing content, coordinate or client text is written: element ids, handles, lengths and m2 only."""
from __future__ import annotations

import csv
import json
import math
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.dirname(HERE)

CALC, HELD, ALT, NA, OWNED, INFO = ("CALCULATED", "HELD", "ALTERNATIVE", "NOT_APPLICABLE", "OWNED_BY_OTHER_LINE",
                                    "INFO")
T_SLAB = 0.16              # ST p.8 note 18 (GF roof slab panels round the ring: T-139 PANELS, 0.16 each)
B_GB = 0.30                # ST p.13 ground-beam width (every titled section)
P13 = {"GB-LT2_5M": 0.30, "GB-LT5M": 0.40, "GB-GT5M": 0.60}
D_EXT_MAIN = 0.95          # T-253: main-house exterior G.B = structural top +0.95 - outer N.G. +-0.00 (DRAWING-CONFIRMED)
BELOW = {"FOOTING", "NECK", "GROUND_BEAM", "STRAP", "BOUNDARY", "LIFT"}


class Refused(ValueError):
    """an input the rules do not accept (a chord for an arc, formwork on a NOT_PRESENT member, an earth-cast face
    without a printed detail, a held line written as 0, a planted column taken to the foundation)."""


# ------------------------------------------------------------------------------------------------ the rules (pure)

def held_range(lo, hi):
    """a HELD range: lo may be None (no low end: an upper bound only), hi may not be None; never (0, 0)."""
    if hi is None:
        raise Refused("a held range needs its upper end (an unquantified line is HELD without a range)")
    if lo is not None and lo > hi + 1e-12:
        raise Refused("held range %r .. %r is reversed" % (lo, hi))
    if (lo or 0.0) == 0.0 and hi == 0.0:
        raise Refused("a held quantity is never written as 0")
    return (None if lo is None else round(lo, 6), round(hi, 6))


def arc_length(R, sweep_deg):
    if R <= 0 or not 0 < sweep_deg <= 360:
        raise Refused("arc R %r sweep %r" % (R, sweep_deg))
    return R * math.radians(sweep_deg)


def piece_length(piece):
    """one drawn edge piece of a member: {'source': 'ARC'|'LINE', 'R', 'sweep_deg'} or {'source': 'LINE', 'length'}.
    An ARC is measured as an arc; offering its chord (a 'length' for an ARC source) is refused."""
    if piece["source"] == "ARC":
        if "R" not in piece or "sweep_deg" not in piece:
            raise Refused("arc piece %s offered without R / sweep (a chord is never an arc's face)" % piece.get("id"))
        return arc_length(piece["R"], piece["sweep_deg"])
    if piece["source"] == "LINE":
        return float(piece["length"])
    raise Refused("unknown piece source %r" % piece["source"])


def face_contact(L, D, beyond, t=T_SLAB, D2=None):
    """contact area of one side piece of a beam whose top is the slab top (total depth D, ST p.14):
    -> (side_m2 below the slab line, band_m2 of the slab thickness at a free edge).
    SLAB beyond: L (D - t), no band. VOID / OUT (opening, outside): L (D - t) + L t (one owner for the full face).
    BEAM beyond: L max(0, D - D2) (equal or deeper covers it). COLUMN: 0 (the column owns the intersection)."""
    if beyond == "SLAB":
        return L * (D - t), 0.0
    if beyond in ("VOID", "OUT"):
        return L * (D - t), L * t
    if beyond == "BEAM":
        if D2 is None:
            raise Refused("beam beyond without its depth: HELD, never 0")
        return L * max(0.0, D - D2), 0.0
    if beyond == "COLUMN":
        return 0.0, 0.0
    raise Refused("unknown neighbour %r" % beyond)


def curved_member(pieces, D, plan_m2, t=T_SLAB):
    """a curved member (ring) from its own drawn edge pieces: soffit = its plan area between its own edges; each piece's
    face by what lies beyond it. -> dict(soffit, side, band, by_piece)."""
    side = band = 0.0
    rows = []
    for p in pieces:
        L = piece_length(p)
        s, b = face_contact(L, D, p["beyond"], t, p.get("D2"))
        side += s
        band += b
        rows.append(dict(id=p.get("id"), L=L, beyond=p["beyond"], side=s, band=b))
    return dict(soffit=plan_m2, side=side, band=band, by_piece=rows)


def oblique_end(La, Lb, b, D, t=T_SLAB):
    """a beam band ending on an oblique carrier: each of its two side faces runs to the carrier face on its own edge
    (La, Lb); the soffit is the trapezoid b (La + Lb) / 2; the end face is cast against the carrier (0)."""
    return dict(soffit=b * (La + Lb) / 2.0, sides=(La + Lb) * (D - t))


def check_oblique_billed(billed_sides, La, Lb, D, t=T_SLAB, tol=1e-6):
    """refuse a one-face end: both sides billed at the shorter edge (or any length other than the drawn edges)."""
    want = (La + Lb) * (D - t)
    if abs(billed_sides - want) > tol:
        raise Refused("billed sides %.6f differ from the two drawn edges %.6f (one-face end)" % (billed_sides, want))
    return True


def ground_beam_faces(L, D, faces):
    """one ground-beam run, face by face: faces = [(name, exposure)] with exposure
       'ABOVE_GROUND'          the face stands above the outer natural ground (nothing to cast against): CALCULATED
       'BURIED'                against fill / excavation: OQ-10 pair FORMED L D / EARTH_CAST 0
       'BURIED_EARTH_UNKNOWN'  the panel beside it is not established (floored or open): FORMED L D, EARTH_CAST HELD
       ('EARTH_CAST', ref)     earth-cast as a printed fact: only with the printed detail named in ref
    -> list of (name, kind, value or held range) with kind in CALC / FORMED / EARTH_CAST / EARTH_CAST_HELD."""
    out = []
    for name, exp in faces:
        a = L * D
        if exp == "ABOVE_GROUND":
            out.append((name, "CALC", a))
        elif exp == "BURIED":
            out.append((name, "FORMED", a))
            out.append((name, "EARTH_CAST", 0.0))
        elif exp == "BURIED_EARTH_UNKNOWN":
            out.append((name, "FORMED", a))
            out.append((name, "EARTH_CAST_HELD", held_range(0.0, a)))
        elif isinstance(exp, tuple) and exp[0] == "EARTH_CAST":
            if not exp[1]:
                raise Refused("face %s taken as earth-cast without a printed detail" % name)
            out.append((name, "EARTH_CAST_PRINTED", 0.0))
        elif exp == "EARTH_CAST":
            raise Refused("face %s taken as earth-cast without a printed detail" % name)
        else:
            raise Refused("unknown exposure %r" % (exp,))
    return out


def tee_cover(b_in, D_in, D_car):
    """the end of an incoming beam cast against a carrier's side covers b_in x min(D_in, D_car) of it; D_in is a
    single value (exact) or a tuple of candidates (a HELD range)."""
    if isinstance(D_in, (tuple, list)):
        vals = sorted(b_in * min(d, D_car) for d in D_in)
        return vals[0], vals[-1]
    v = b_in * min(D_in, D_car)
    return v, v


def column_shaft(perimeters, h, existence="DRAWN", base="SLAB_TOP", planted=False):
    """a column shaft: perimeter x height to the controlling soffit. existence NOT_PRESENT -> refused (the line
    leaves with its source, never a 0 line); a planted column starts on the slab top it stands on (base 'FOUNDATION'
    refused); two perimeter readings (section CONFLICT) -> HELD range, never the larger end."""
    if existence == "NOT_PRESENT":
        raise Refused("formwork on a NOT_PRESENT member")
    if planted and base != "SLAB_TOP":
        raise Refused("a planted column is not taken to the foundation")
    ps = sorted(set(round(p, 9) for p in perimeters))
    if len(ps) == 1:
        return CALC, ps[0] * h
    return HELD, held_range(ps[0] * h, ps[-1] * h)


# --------------------------------------------------------------------------------------- synthetic villa W (--check)

def check():
    """villa W (not Alsenan; every value by hand in the comments)."""
    def close(a, b, tol=1e-6):
        assert abs(a - b) <= tol, (a, b)

    # (1) a curved ring beam 0.20 x 0.60 round a void, slab 0.15: outer arc R 2.00 over 90 deg to the slab, inner arc
    #     R 1.80 over 90 deg to the void, two 0.20 line ends against beams 0.60 deep
    pcs = [dict(id="o", source="ARC", R=2.0, sweep_deg=90, beyond="SLAB"),
           dict(id="i", source="ARC", R=1.8, sweep_deg=90, beyond="VOID"),
           dict(id="e1", source="LINE", length=0.2, beyond="BEAM", D2=0.60),
           dict(id="e2", source="LINE", length=0.2, beyond="BEAM", D2=0.60)]
    plan = math.pi / 4 * (2.0 ** 2 - 1.8 ** 2)                      # 0.596903
    r = curved_member(pcs, 0.60, plan, t=0.15)
    close(r["soffit"], 0.596903, 1e-6)
    close(r["side"], math.pi * 2.0 / 2 * 0.45 + math.pi * 1.8 / 2 * 0.45)   # 3.141593 x 0.45 + 2.827433 x 0.45 = 2.686062
    close(r["band"], math.pi * 1.8 / 2 * 0.15)                              # 0.424115
    # adverse: the inner arc offered as its chord (2 x 1.8 x sin 45 = 2.545584) is refused
    try:
        curved_member([dict(id="i", source="ARC", length=2.545584, beyond="VOID")], 0.60, plan)
        raise AssertionError("chord accepted")
    except Refused:
        pass
    # (2) a 0.20 x 0.50 beam ending on a 30-degree carrier: edges 3.000 / 3.11547 (0.20 tan 30 = 0.11547)
    o = oblique_end(3.0, 3.11547, 0.20, 0.50, t=0.15)
    close(o["soffit"], 0.611547)
    close(o["sides"], 6.11547 * 0.35)                                  # 2.140415
    check_oblique_billed(2.140415, 3.0, 3.11547, 0.50, t=0.15, tol=1e-6)
    try:                                                                 # one-face end: 2 x 3.000 x 0.35 = 2.100
        check_oblique_billed(2.100, 3.0, 3.11547, 0.50, t=0.15)
        raise AssertionError("one-face end accepted")
    except Refused:
        pass
    # (3) an exterior ground beam 0.30 x 0.90, run 4.00 m: outer face above N.G. 3.600 CALC; inner face against fill
    #     OQ-10 pair 3.600 / 0; an interior beam 0.30 x 0.40 ends on the inner face: cover 0.120
    g = ground_beam_faces(4.0, 0.90, [("outer", "ABOVE_GROUND"), ("inner", "BURIED")])
    assert g == [("outer", "CALC", 3.6), ("inner", "FORMED", 3.6), ("inner", "EARTH_CAST", 0.0)], g
    assert tee_cover(0.30, 0.40, 0.90) == (0.12, 0.12)
    lo, hi = tee_cover(0.30, (0.30, 0.40), 0.90)
    close(lo, 0.09)
    close(hi, 0.12)
    try:                                                                 # earth-cast without a printed detail
        ground_beam_faces(4.0, 0.90, [("inner", "EARTH_CAST")])
        raise AssertionError("earth-cast face accepted without a printed detail")
    except Refused:
        pass
    assert ground_beam_faces(4.0, 0.90, [("inner", ("EARTH_CAST", "sheet S-5 detail 3"))]) == \
        [("inner", "EARTH_CAST_PRINTED", 0.0)]
    # (4) columns: section CONFLICT 0.20 x 0.50 printed vs 0.25 x 0.50 drawn, h 3.00: HELD 4.200 .. 4.500
    st, v = column_shaft([1.4, 1.5], 3.0)
    assert st == HELD and v == (4.2, 4.5), (st, v)
    try:
        column_shaft([1.4], 3.0, existence="NOT_PRESENT")
        raise AssertionError("formwork on a NOT_PRESENT member accepted")
    except Refused:
        pass
    try:
        column_shaft([1.8], 4.5, planted=True, base="FOUNDATION")
        raise AssertionError("planted column taken to the foundation")
    except Refused:
        pass
    st, v = column_shaft([1.8], 3.45, planted=True)
    assert st == CALC and abs(v - 6.21) < 1e-9
    # (5) held never 0
    for bad in ((0.0, 0.0), (None, None), (0.5, 0.2)):
        try:
            held_range(*bad)
            raise AssertionError("held range %r accepted" % (bad,))
        except Refused:
            pass
    assert held_range(None, 4.83) == (None, 4.83)
    print("formwork_r4 --check: villa W OK (ring, oblique end, ground faces, tee cover, columns, held never 0)")
    return True


# ------------------------------------------------------------------------------------------------ Alsenan inputs

def rd(rel):
    with open(os.path.join(RES, rel), newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _f(v):
    return None if v in ("", None) else float(v)


def r3_lines():
    out = []
    for r in rd("agents_t163/FORMWORK_LINES.csv"):
        r = dict(r)
        for k in ("m2", "held_lo", "held_hi"):
            r[k] = _f(r[k])
        out.append(r)
    return out


def row(element, floor, item, method, m2, status, basis, held=None, change="NEW", cause="", refs="",
        freelancer="no formwork row", verdict="FREELANCER_NO_ROW"):
    if status == HELD and held is None and m2 is not None:
        raise Refused("a HELD row carries a range or nothing, never a value: %s" % item)
    return dict(element=element, floor=floor, item=item, method=method,
                m2=None if m2 is None else round(m2, 6),
                held_lo=None if not held else held[0], held_hi=None if not held else held[1],
                status=status, basis=basis, freelancer=freelancer, verdict=verdict, change=change, cause=cause,
                refs=refs)


def _key(r):
    return (r["element"], r["floor"], r["item"], r["method"])


# ------------------------------------------------------------------------------------------------ 1. ring B7

def ring_delta(inp):
    ring = inp["void_ring"]
    D = 0.75                                                  # B7 20 x 75 (marks 46E / 46F / 470 / 471; T-110)
    pieces = []
    for key in ("outer", "void"):
        for p in ring["pieces"][key]:
            if key == "void" and p["kind"] == "line":
                continue                                       # the CB1 face the void reaches: CB1's own face (below)
            beyond = {"SLAB": "SLAB", "VOID": "VOID", "BEAM": "BEAM"}[p["beyond_kind"]]
            pc = dict(id=p["handle"], beyond=beyond, D2=p["beyond_D"])
            if p["kind"] == "arc":
                pc.update(source="ARC", R=p["R_m"], sweep_deg=p["sweep_deg"])
            else:
                # an outer straight piece runs along another beam's face; the part of it the void reaches is the
                # void's own line piece (CB1 below), so only the ring's contact with that beam is listed here
                L = p["length_m"]
                if p["handle"] == "2A9":
                    L -= next(q["length_m"] for q in ring["pieces"]["void"] if q["kind"] == "line")
                pc.update(source="LINE", length=L)
            pieces.append(pc)
    r = curved_member(pieces, D, 0.666406)                    # T-252 plan between the ring's own edges (MERGED)
    cb1 = next(q for q in ring["pieces"]["void"] if q["kind"] == "line")
    cb1_side, cb1_band = face_contact(cb1["length_m"], cb1["beyond_D"], "VOID")
    r3 = ring["r3"]
    r3_soffit = sum(r3["soffit_m2"].values())
    r3_side = sum(r3["side_m2"].values())
    return dict(D=D, ring=r, cb1=dict(L=cb1["length_m"], member=cb1["beyond_member"], D=cb1["beyond_D"],
                                       side=cb1_side, band=cb1_band),
                d_soffit=r["soffit"] - r3_soffit, d_side=r["side"] + cb1_side - r3_side,
                d_band=r["band"] + cb1_band, r3_soffit=r3_soffit, r3_side=r3_side,
                ring_mix_len=r3["ring_mix_len_by_face"],
                void_arcs=sum(piece_length(p) for p in pieces if p["beyond"] == "VOID"),
                outer_slab_arcs=sum(piece_length(p) for p in pieces if p["beyond"] == "SLAB"))


# ------------------------------------------------------------------------------------------------ 3. ground beams

T253_EXT_MAIN = {"107+7CE#1", "109+7CB#2", "109+7CB#3", "10A+7C9#1", "114+115+7DF#2", "145+7CA#1", "170+7C3#1",
                 "170+7C3#2", "170+7C3#3", "170+7C3#4", "7D0+FC#1", "7D0+FC#2", "7D0+FC#3", "7D0+FC#4", "7E0+FD#1",
                 "7E0+FD#2", "ARC:157+158"}
T253_COURT = {"178+7DB#1": (0.40, 0.95), "185+7C7#1": (0.30, 0.40, 0.95), "1811+1812#1": (0.30, 0.40)}
PANELS_NOT_ESTABLISHED = {"GS-12": "T-242: 'Garden / yard / court', whether it is floored is not printed",
                          "GS-16": "T-242 / T-253: enclosed, in no GF room, no floor level (outdoor stair court side)"}


def ground_inputs():
    led = {r["run"]: r for r in rd("agents_t242/LEDGER_T242.csv")}
    t253 = {r["item"]: r for r in rd("agents_t253/LEDGER_T253.csv")}
    with open(os.path.join(RES, "agents_t242", "ALSENAN_GROUND_INPUT.json"), encoding="utf-8") as fh:
        gi = json.load(fh)
    spans = {s["span_id"]: s for s in gi["spans"]}
    arcs = {a["arc_band"]: a for a in gi["arc_bands"]}
    return led, t253, spans, arcs


def depth_readings(run, led):
    """-> (status, depths tuple, why). CALC: one p.13 class; HELD: the candidates or the one printed class."""
    r = led[run]
    titles = [t for t in r["titles"].split("+") if t in P13]
    reasons = r["reasons"]
    if run in T253_EXT_MAIN:
        return CALC, (D_EXT_MAIN,), "T-253 exterior main: D = +0.95 - outer N.G. +-0.00 (DRAWING-CONFIRMED)"
    if run in T253_COURT:
        return HELD, T253_COURT[run], "T-253 court run: section not established, candidates " + \
            " / ".join("%.2f" % d for d in T253_COURT[run])
    if r["part"] == "ANNEX" and r["component"].startswith("GB-EXTERIOR"):
        return "CONFLICT", (), "T-253 annex exterior CONFLICT: literal 0.25 (levels) vs the printed section (no " \
            "depth): no value adopted"
    if r["status"] == "CALCULATED":
        assert len(titles) == 1, run
        return CALC, (P13[titles[0]],), "p.13 title from the face-to-face length, one section (T-242)"
    if "D-34" in reasons:
        m = reasons.split("D-34 title / length basis: ")[1].split(" ")[0:3]
        cands = tuple(sorted({float(m[0]), float(m[2])}))
        return HELD, cands, "D-34 title / length basis %s" % " / ".join("%.2f" % c for c in cands) + \
            ("; D-33 concentrated load" if "D-33" in reasons else "")
    if "D-33" in reasons:
        return HELD, tuple(sorted({P13[t] for t in titles})), "D-33: printed class only (the section 'with " \
            "concentrated load' is not printed)"
    if r["status"] == "CONFLICT":
        return HELD, tuple(sorted({P13[t] for t in titles})), "end piece at the neck depends on a printed section " \
            "conflict (T-217): " + r["end_adjust_m2"]
    raise Refused("run %s: no depth rule (%s)" % (run, reasons))


def incoming(carrier_run, band, spans):
    """the span of `band` that ends (start or end) on the carrier's band as a BEAM_JUNCTION."""
    cb = carrier_run.split("#")[0]
    hits = [s for s in spans.values() if s["band_id"] == band and any(
        e["kind"] == "BEAM_JUNCTION" and any(x.split("/")[0] == cb for x in e.get("refs", []))
        for e in (s["start"], s["end"]))]
    if len(hits) != 1:
        raise Refused("tee %s on %s: %d incoming spans" % (band, carrier_run, len(hits)))
    return hits[0]["span_id"]


def ground_block(inp):
    led, t253, spans, arcs = ground_inputs()
    out = []
    covers = []
    for run, r in led.items():
        if not r["component"].startswith("GB-"):
            continue
        st, ds, why = depth_readings(run, led)
        L = float(r["L_m"])
        refs = "T-242 run %s (handles %s)" % (run, run.split("#")[0].replace("ARC:", ""))
        if run == "ARC:157+158":
            a = inp["arc_ground_beam"]
            inner = a["inner"]["length_m"]                     # court side (the pool court inside the ring): above N.G.
            outer = a["outer"]["length_m"] - sum(a["outer"]["inside_columns_m"].values())
            Lin = arc_length(a["inner"]["R_m"], a["inner"]["sweep_deg"])
            assert abs(Lin - inner) < 1e-5
            out.append(row("GROUND_BEAM", "GF", "ARC:157+158 inner face (pool-court side, R 2.25 x 167.236 deg), "
                           "above N.G.", "G", inner * D_EXT_MAIN, CALC,
                           "arc length %.4f x D 0.95 (T-253); the court inside the ring is outside ground +0.15 paving "
                           "on N.G. (T-242 panels GS-10 / GS-23 lie on the outer side)" % inner,
                           cause="T-242 / T-253 ring on its arcs", refs="ARC 157 (R 2.25); " + refs))
            out.append(row("GROUND_BEAM", "GF", "ARC:157+158 outer face (rooms side, R 2.55 x 150.086 deg net of "
                           "the column outlines 17BA 0.300 / 17BD 0.102) FORMED", "G", outer * D_EXT_MAIN, ALT,
                           "OQ-10 FORMED: arc length %.4f x 0.95; against the fill under the GF slab" % outer,
                           cause="T-242 / T-253 ring on its arcs", refs="ARC 158 (R 2.55), columns 17BA / 17BD"))
            out.append(row("GROUND_BEAM", "GF", "ARC:157+158 outer face EARTH_CAST", "G", 0.0, ALT,
                           "OQ-10 EARTH_CAST (alternative, never summed with FORMED)", cause="T-242 / T-253"))
            sid = "177+7CD#2"                                  # ends on the ring (T-242 end ARC:157+158/2)
            st_in, d_in, _w = depth_readings(sid, led)
            covers.append(("ARC:157+158", "outer", sid, tee_cover(B_GB, d_in, D_EXT_MAIN), st_in))
            continue
        if run in T253_EXT_MAIN:
            sp = spans[run]
            sides = sp["panels_by_side_m2"]
            ext = [k for k, v in sides.items() if not v]
            hold_side = [k for k, v in sides.items() if any(p in PANELS_NOT_ESTABLISHED for p in v)]
            faces = []
            for k in ("A", "B"):
                if k in ext:
                    faces.append((k, "ABOVE_GROUND"))
                elif k in hold_side:
                    faces.append((k, "BURIED_EARTH_UNKNOWN"))
                else:
                    faces.append((k, "BURIED"))
            for k, kind, v in ground_beam_faces(L, D_EXT_MAIN, faces):
                pan = ", ".join(sides[k]) or "outside"
                if kind == "CALC":
                    out.append(row("GROUND_BEAM", "GF", "span %s L %.4f side %s (%s) above N.G." % (run, L, k, pan),
                                   "E=G", v, CALC, "exterior face from the outer N.G. (soffit, p.13 'Outer Normal "
                                   "ground level') to the top +0.95: nothing to cast against", cause=why, refs=refs))
                elif kind == "FORMED":
                    out.append(row("GROUND_BEAM", "GF", "span %s L %.4f side %s (%s) FORMED" % (run, L, k, pan),
                                   "E=G", v, ALT, "OQ-10 FORMED: L x 0.95" + (
                                       "; the panel beside it is not established: " + "; ".join(
                                           PANELS_NOT_ESTABLISHED[p] for p in sides[k] if p in PANELS_NOT_ESTABLISHED)
                                       if k in hold_side else ""), cause=why, refs=refs))
                elif kind == "EARTH_CAST":
                    out.append(row("GROUND_BEAM", "GF", "span %s side %s EARTH_CAST" % (run, k), "E=G", 0.0, ALT,
                                   "OQ-10 EARTH_CAST (alternative)", cause=why, refs=refs))
                else:
                    out.append(row("GROUND_BEAM", "GF", "span %s side %s EARTH_CAST (panel not established)" % (run, k),
                                   "E=G", None, HELD, "in the EARTH_CAST alternative this face is earth-cast if the "
                                   "panel is floored (fill), formed if it is open: " + "; ".join(
                                       PANELS_NOT_ESTABLISHED[p] for p in sides[k] if p in PANELS_NOT_ESTABLISHED),
                                   held=v, cause=why, refs=refs))
            for t in sp["tees_mid_span"]:
                sid = incoming(run, t["band_id"], spans)
                st_in, d_in, _w = depth_readings(sid, led)
                pin = spans[sid]["panels_by_side_m2"] if sid in spans else {}
                pin_all = set(sum(pin.values(), []))
                side = next((k for k in ("A", "B") if set(sides[k]) & pin_all), None)
                covers.append((run, side, sid, tee_cover(B_GB, d_in if len(d_in) > 1 else d_in[0], D_EXT_MAIN),
                               st_in))
            continue
        if st == "CONFLICT":
            lit = 2 * L * 0.25
            out.append(row("GROUND_BEAM", "GF", "span %s L %.4f sides (annex exterior)" % (run, L), "E=G", None, HELD,
                           why + "; literal reading 2 x L x 0.25 = %.4f shown, never adopted" % lit, cause=why,
                           refs=refs))
            continue
        lo, hi = 2 * L * min(ds), 2 * L * max(ds)
        if run in ("184+7CF#1", "184+7CF#2"):
            a_lo, a_hi = (float(x) for x in r["end_adjust_m2"].replace("+", "").split(".."))
            lo, hi = 2 * (L + a_lo / B_GB) * ds[0], 2 * (L + a_hi / B_GB) * ds[0]
        if st == CALC:
            out.append(row("GROUND_BEAM", "GF", "span %s L %.4f D %.2f sides FORMED" % (run, L, ds[0]), "E=G",
                           2 * L * ds[0], ALT, "OQ-10 FORMED: 2 L D (T-242 face to face, p.13 title); base on "
                           "blinding", cause=why, refs=refs))
            out.append(row("GROUND_BEAM", "GF", "span %s sides EARTH_CAST" % run, "E=G", 0.0, ALT,
                           "OQ-10 EARTH_CAST (alternative)", cause=why, refs=refs))
        else:
            out.append(row("GROUND_BEAM", "GF", "span %s L %.4f sides FORMED" % (run, L), "E=G", None, HELD,
                           why + ("; court run: faces formed if above ground" if run in T253_COURT else ""),
                           held=held_range(lo, hi), cause=why, refs=refs))
        for band in [b.strip() for b in r["d33_tees"].split(";") if b.strip()]:
            sid = incoming(run, band, spans)
            st_in, d_in, _w = depth_readings(sid, led)
            covers.append((run, "", sid, tee_cover(B_GB, d_in if len(d_in) > 1 else d_in[0],
                                                   max(ds) if ds else None), st_in))
    for car, side, sid, (lo, hi), st_in in covers:
        nm = "tee: %s ends on %s%s (cover 0.30 x min(D_in, D))" % (sid, car, " side " + side if side else "")
        if st_in == CALC and lo == hi and car in T253_EXT_MAIN | {"ARC:157+158"}:
            out.append(row("GROUND_BEAM", "GF", nm + " FORMED", "G", -lo, ALT,
                           "the incoming end is cast against this face (FORMED alternative only)",
                           cause="tee cover", refs="T-242 tees_mid_span / span ends"))
        else:
            out.append(row("GROUND_BEAM", "GF", nm + " FORMED", "G", None, HELD,
                           "cover range from the incoming / carrier depth candidates (FORMED alternative only)",
                           held=held_range(-hi, -lo), cause="tee cover", refs="T-242 tees_mid_span / span ends"))
    # boundary G.B (T-253): solid 44.07 x 0.20 x 0.40 at N.G.; top at N.G., body below: buried both faces
    bl = [r for r in rd("agents_t253/LEDGER_T253.csv") if r["component"] == "BOUNDARY-GB at N.G."]
    Lb = sum(float(r["L_m"]) for r in bl)
    assert abs(Lb - 44.07) < 1e-9
    for k, kind, v in ground_beam_faces(Lb, 0.40, [("both sides", "BURIED")]):
        out.append(row("BOUNDARY", "GF", "boundary G.B 20 x 40 at N.G., 5 runs %.2f m, two faces %s" % (Lb, kind),
                       "E=G", 2 * v, ALT, "OQ-10 %s: 2 x 44.07 x 0.40 (corner squares once: inner + outer face = 2 x "
                       "band length, T-253 area conserved 8.814 = 44.07 x 0.20); soffit on the brick wall below (p.14 "
                       "A-A), top at N.G. under the 15 plain-concrete paving: no form" % kind,
                       cause="T-253 DRAWING-CONFIRMED", refs="S-BOUN 7FE / 7FC / 810; ST p.14 A-A"))
    out.append(row("BOUNDARY", "GF", "boundary G.B run 810#1 west end face (against annex beam 10B or the brick under "
                   "it)", "G", None, HELD, "the 3-D member at 10B is the annex beam only if it is deeper than 0.25 m "
                   "(annex CONFLICT, T-253 s.3): end face 0 .. 0.20 x 0.40", held=held_range(0.0, 0.08),
                   cause="T-253 810#1 end HELD", refs="810; 10B"))
    out.append(row("BOUNDARY", "GF", "boundary columns 20 x 30 through the G.B: line split only", "G", None, INFO,
                   "R-CONC-OWN-1: each column passing through owns 2 x 0.30 x 0.40 = 0.24 m2 of the formed faces; count "
                   "not printed (M4): moves m2 between the beam and column lines, not the physical total",
                   cause="T-253 M4", refs="ST p.14 'SEE ARCH PLAN'"))
    return out


# ------------------------------------------------------------------------------------------------ 6. columns

def column_inputs():
    t248 = {r["owner_t119_id"]: r for r in rd("agents_t248/LEDGER_T248.csv") if r["owner_t119_id"]}
    t256 = {r["member"]: r for r in rd("agents_t256/LEDGER_T256.csv")}
    joints = {r["column"]: r for r in rd("agents_t163/JOINT_BY_COLUMN.csv")}
    return t248, t256, joints


def _dims(txt, unit):
    a, b = (float(v) for v in txt.lower().replace(" ", "").split("x"))
    return (a / 1000.0, b / 1000.0) if unit == "mm" else (a / 100.0, b / 100.0)


def section_perimeters(t256_row):
    d = _dims(t256_row["drawn_mm"], "mm")
    s = _dims(t256_row["schedule_cm"].split()[-1], "cm")
    return 2 * (d[0] + d[1]), 2 * (s[0] + s[1])


# ------------------------------------------------------------------------------------------------ the ledger

def build():
    with open(os.path.join(HERE, "ALSENAN_R4_INPUT.json"), encoding="utf-8") as fh:
        inp = json.load(fh)
    r3 = r3_lines()
    t248, t256, joints = column_inputs()
    rg = ring_delta(inp)
    delta = []          # (r3 row or None, r4 row or None, cause)
    r4 = []

    def keep(r):
        x = dict(r)
        x.update(change="UNCHANGED", cause="", refs="")
        r4.append(x)

    def change(r, new, cause):
        new = dict(new)
        new.setdefault("change", "CHANGED")
        new["change"] = "CHANGED"
        new["cause"] = cause
        r4.append(new)
        delta.append((r, new, cause))

    def remove(r, cause):
        delta.append((r, None, cause))

    conflict = {}
    for tid, r in t248.items():
        if r["status"] == "CONFLICT" or "SECTION_CONFLICT" in r["causes"]:
            if r["member"] in t256:
                conflict[tid] = (r["member"],) + section_perimeters(t256[r["member"]])
    roof_held = {tid for tid, r in t248.items() if r["storey"] == "2F" and "D-39_ROOF_DATUM" in r["causes"]}
    j_out = defaultdict(lambda: [0.0, 0.0, 0.0, []])        # storey -> [calc removed, held lo, held hi, ids]
    ground_done = boundary_done = strap_done = False

    for r in r3:
        el, it, st = r["element"], r["item"], r["status"]
        cid = it.split()[0]
        # ---- 1. ring B7 -------------------------------------------------------------------------------------
        if el == "BEAM" and r["floor"] == "GF" and r["method"] == "G" and it.endswith("beam soffits"):
            n = dict(r)
            n["m2"] = round(r["m2"] + rg["d_soffit"], 6)
            n["basis"] = r["basis"] + "; r4: GF void ring B7 soffit from its own arcs 0.666406 m2 (T-252) replaces " \
                "the two pieces r3 bound (%.6f)" % rg["r3_soffit"]
            change(r, n, "T-252 R-BEAM-CURVED-AREA-2: ring B7 soffit")
            continue
        if el == "BEAM" and r["floor"] == "GF" and r["method"] == "G" and it.endswith("beam sides below the slab"):
            n = dict(r)
            n["m2"] = round(r["m2"] + rg["d_side"], 6)
            n["basis"] = r["basis"] + "; r4: ring B7 faces on its arcs (outer arcs to the slab x 0.59, void arcs x " \
                "0.59 + band) and the CB1 face the void reaches (2A9) replace r3's two bound pieces (%.6f)" % \
                rg["r3_side"]
            change(r, n, "T-252 ring B7 sides on its arcs")
            continue
        if el == "SLAB_EDGE" and r["floor"] == "GF" and "every free edge" in it:
            n = dict(r)
            n["m2"] = round(r["m2"] + rg["d_band"], 6)
            n["basis"] = r["basis"] + "; r4: + the slab-thickness band of the pool-court void, measured on the ring " \
                "(void arcs) and CB1 (2A9): one owner per face (D-T163-3)"
            change(r, n, "T-252 void band owned by the ring / CB1")
            continue
        if r["floor"] == "GF" and "next to RING_MIX" in it:
            remove(r, "T-252: the RING_MIX face is split into ring (B7, measured) and void; nothing held")
            continue
        if el == "SLAB_EDGE" and "pool-court void" in it:
            n = dict(r)
            n.update(status=OWNED, m2=None, held_lo=None, held_hi=None,
                     basis="measured on the ring line (B7 void arcs %.4f m x 0.75) and on CB1 (2A9 %.4f m x 0.75): "
                           "the slab band is part of those full-depth faces (D-T163-3)" % (rg["void_arcs"],
                                                                                           rg["cb1"]["L"]))
            change(r, n, "T-252: pool-court band owned by the ring / CB1")
            continue
        # ---- 3. ground beams, boundary ----------------------------------------------------------------------
        if el == "GROUND_BEAM":
            if not ground_done:
                for n in ground_block(inp):
                    if n["element"] == "GROUND_BEAM":
                        r4.append(n)
                        delta.append((None, n, n["cause"]))
                ground_done = True
            remove(r, "T-242 / T-253 / T-230: ground-beam runs re-based (lengths, classes, exterior D 0.95, arcs)")
            continue
        if el == "BOUNDARY" and it.startswith("M3"):
            if not boundary_done:
                for n in ground_block(inp):
                    if n["element"] == "BOUNDARY":
                        r4.append(n)
                        delta.append((None, n, n["cause"]))
                boundary_done = True
            remove(r, "T-253: boundary G.B concrete DRAWING-CONFIRMED -> OQ-10 pair")
            continue
        # ---- 4. straps --------------------------------------------------------------------------------------
        if el == "STRAP" or (el == "FOOTING" and " ends against " in it):
            if not strap_done:
                with open(os.path.join(RES, "agents_t174", "T174_STRAPS.json"), encoding="utf-8") as fh:
                    straps = json.load(fh)
                for s in straps:
                    fw = s["formwork"]
                    for kind in ("FORMED", "EARTH_CAST"):
                        n = row("STRAP", "FDN", "%s %d x %d sides %s (axis length, Q-74)" % (
                            s["mark"], round(s["B_m"] * 100), round(s["D_m"] * 100), kind), "E=G",
                            fw["below_ground"][kind + "_m2"], ALT,
                            "T-174: 2 x %.4f x %.2f between the footing faces" % (fw["side_runs_m"][0], s["D_m"]),
                            cause="T-174 MERGED 984ebbe1", refs="ST p.10 %s; T-174" % s["mark"])
                        r4.append(n)
                        delta.append((None, n, n["cause"]))
                    sl = fw["soffit"]["candidates_m2"]
                    n = row("STRAP", "FDN", "%s soffit" % s["mark"], "E=G", None, HELD, fw["soffit"]["note"],
                            held=held_range(min(sl), max(sl)), cause="T-174", refs="T-174")
                    r4.append(n)
                    delta.append((None, n, n["cause"]))
                    for c in s["footing_face_covered"]:
                        if c["covered_m2"] is not None:
                            n = row("FOOTING", "FDN", "%s side covered by %s (chord %.4f x min(D, H)) FORMED" % (
                                c["footing"], s["mark"], c["chord_on_face_m"]), "G", -c["covered_m2"], ALT,
                                "T-174 chord on the face x min(D, H): deduction from the footing sides (FORMED only)",
                                cause="T-174", refs=c["footing"])
                        else:
                            n = row("FOOTING", "FDN", "%s side covered by %s (chord %.4f) FORMED" % (
                                c["footing"], s["mark"], c["chord_on_face_m"]), "G", None, HELD,
                                "the 1B1B outline is a CONFLICT (T-239): cover <= 0.70 x 0.50", held=held_range(
                                    -c["chord_on_face_m"] * s["D_m"], -c["chord_on_face_m"] * 0.30),
                                cause="T-174 / T-239", refs=c["footing"])
                        r4.append(n)
                        delta.append((None, n, n["cause"]))
                strap_done = True
            remove(r, "T-174: straps on their axis length; covered footing faces by chord")
            continue
        # ---- 5. footings ------------------------------------------------------------------------------------
        if el == "FOOTING" and it.startswith("F10 "):
            n = dict(r)
            rows_sep = 2 * (2.80 + 1.40) * 0.50 + 2 * (0.90 + 0.80) * 0.30
            outline = 2 * (3.25 + 1.40) * 0.50
            n["held_lo"], n["held_hi"] = held_range(min(rows_sep, outline), max(rows_sep, outline))
            n["basis"] = "T-239 CONFLICT, range = exactly its two readings: ROWS_SEPARATELY F10 2(2.80 + 1.40) 0.50 + " \
                "F 2(0.90 + 0.80) 0.30 = 5.220; OUTLINE 1B1B 3.25 x 1.40 at F10's 0.50 = 4.650 (the F10-alone 4.200 " \
                "is not a reading); the SB1 opening cover is on its own line"
            change(r, n, "T-239 multi-tag outline range")
            continue
        if el == "FOOTING" and it.startswith("FN / F9 overlap"):
            n = dict(r)
            n.update(item="FN 180C / F9 notch (0.40 x 0.35): faces cast against each other FORMED", m2=-0.45,
                     held_lo=None, held_hi=None, status=ALT,
                     basis="T-233 / T-206: every footing bottom on one stack (formation + 0.17), F9 owns the "
                           "overlap, FN drawn notched: FN notch faces (0.40 + 0.35) x 0.30 = 0.225 and F9's faces "
                           "along them (0.40 + 0.35) x 0.30 = 0.225 are cast against each other (FORMED only)")
            change(r, n, "T-233 notch settled")
            continue
        # ---- 6. columns -------------------------------------------------------------------------------------
        if el == "COLUMN" and it.startswith("undrawn column"):
            remove(r, "T-256 NOT_PRESENT (R-COLUMN-EVIDENCE-1): the line leaves with its source, never a 0 line")
            continue
        if el == "COLUMN" and cid.startswith("COL-"):
            if cid in conflict:
                member, Pd, Ps = conflict[cid]
                h = (r["m2"] if st == CALC else r["held_hi"]) / Ps
                n = dict(r)
                if st == CALC:
                    s_, v = column_shaft([Pd, Ps], h)
                else:
                    lo_h, hi_h = r["held_lo"] / Ps, r["held_hi"] / Ps
                    v = held_range(min(Pd, Ps) * lo_h, max(Pd, Ps) * hi_h)
                    s_ = HELD
                n.update(status=s_, m2=None, held_lo=v[0], held_hi=v[1],
                         basis=r["basis"] + "; r4: section CONFLICT (T-256 %s): drawn perimeter %.2f vs printed %.2f "
                         "-> range, never the larger end" % (member, Pd, Ps))
                change(r, n, "T-248 / T-256 section CONFLICT")
                continue
            if cid in roof_held and st == CALC:
                n = dict(r)
                n.update(status=HELD, m2=None, held_lo=None, held_hi=r["m2"],
                         basis=r["basis"] + "; r4: 2F roof structural top HELD (D-39, T-248): only the finished "
                         "+13.90 is printed; shaft <= the r3 value, no low end")
                change(r, n, "T-248 D-39 roof datum")
                continue
            if cid == "COL-1F-57":
                n = dict(r)
                s_, v = column_shaft([2 * (0.20 + 0.70)], 3.45, planted=True)
                assert abs(v - r["held_hi"]) < 1e-9
                n.update(status=s_, m2=v, held_lo=None, held_hi=None,
                         basis="perimeter 1.80 x (interval 4.20 - D_ctrl 0.75) = 6.210: planted on B27, from the slab "
                               "top it stands on (T-248 DRAWING-CONFIRMED, lessons row 2026-10-24 T-248; the T-151 "
                               "'planted stay HELD' rule superseded)")
                change(r, n, "T-248 planted column from its slab top")
                continue
            if cid in ("COL-1F-58", "COL-2F-59"):
                n = dict(r)
                n["basis"] = r["basis"].replace("PLANTED_COLUMN (T-151: the 3 planted columns stay HELD) ", "") + \
                    ("; r4: planted hold superseded (T-248); HELD on the framing depth only" if cid == "COL-1F-58" else
                     "; r4: T-248 HELD on D-39 and section CONFLICT (drawn 0.20 x 0.40 vs P.C 20x50): reading 1.20 x "
                     "3.45 = 4.140 .. 4.830, both under the roof datum")
                if cid == "COL-2F-59":
                    n["held_lo"], n["held_hi"] = held_range(1.20 * 3.45, 1.40 * 3.45)
                change(r, n, "T-248 cause updated")
                continue
        if el == "JOINT" and r["status"] == CALC and "at the STATED section" in it:
            sto = r["floor"]
            rem = 0.0
            for cid_, (member, Pd, Ps) in conflict.items():
                j = joints.get(cid_)
                if j and j["storey"] == sto and j["status"] == CALC and j["stated_status"] == CALC:
                    rem += float(j["joint_stated_lo"])
                    vals = [float(j["joint_m2"]), float(j["joint_stated_lo"])]
                    j_out[sto][1] += min(vals)
                    j_out[sto][2] += max(vals)
                    j_out[sto][3].append(cid_)
            add57 = inp["planted_col_1f_57"]["joint_stated_lo"] if sto == "1F" else 0.0
            if rem or add57:
                n = dict(r)
                n["m2"] = round(r["m2"] - rem + add57, 6)
                n["basis"] = r["basis"] + "; r4: %d section-CONFLICT columns moved to a HELD joint line (-%.4f)%s" % (
                    len(j_out[sto][3]), rem, "; + planted COL-1F-57 0.766928 (stated = drawn 0.20 x 0.70)" if add57
                    else "")
                change(r, n, "T-248 / T-256 joints")
                if j_out[sto][3]:
                    m = row("JOINT", sto, "%s column joint faces of %d section-CONFLICT columns (%s)" % (
                        sto, len(j_out[sto][3]), ", ".join(sorted(j_out[sto][3]))), "G", None, HELD,
                        "range = the drawn-outline joint and the stated-section joint of each column (r3 "
                        "JOINT_BY_COLUMN), never the larger end", held=held_range(j_out[sto][1], j_out[sto][2]),
                        cause="T-248 / T-256 section CONFLICT")
                    r4.append(m)
                    delta.append((None, m, m["cause"]))
            else:
                keep(r)
            continue
        if el == "JOINT" and "whose stated section cannot be placed" in it:
            lo = hi = 0.0
            for cid_ in ("COL-GF-14", "COL-GF-24", "COL-GF-30"):
                j = joints[cid_]
                lo += min(float(j["joint_m2"]), float(j["joint_stated_lo"]))
                hi += max(float(j["joint_m2"]), float(j["joint_stated_hi"]))
            n = dict(r)
            n["held_lo"], n["held_hi"] = held_range(lo, hi)
            n["basis"] = r["basis"] + "; r4: the three are also section CONFLICT (T-256): the drawn-outline joint is " \
                "the other reading"
            change(r, n, "T-256 section CONFLICT joints")
            continue
        if el == "JOINT" and r["floor"] == "1F" and it.endswith("joint faces of HELD columns"):
            n = dict(r)
            v = inp["planted_col_1f_57"]["r3_walk_acc"]
            j57 = sum(x for k, x in v.items() if k.startswith("JOINT_FACE"))
            n["held_lo"], n["held_hi"] = held_range(r["held_lo"] - j57, r["held_hi"] - j57)
            n["basis"] = r["basis"] + "; r4: COL-1F-57 (%.6f) moved to the CALCULATED joint line" % j57
            change(r, n, "T-248 planted column released from the held joints")
            continue
        keep(r)
    return r4, delta, inp, rg


def totals(lines):
    tot = defaultdict(float)
    for r in lines:
        grp = "BELOW_" if r["element"] in BELOW else "ABOVE_"
        st = r["status"]
        if st == HELD:
            if r["held_hi"] is None:
                tot[grp + "HELD_UNQUANTIFIED_LINES"] += 1
            elif r["held_lo"] is None:
                tot[grp + "HELD_HI"] += r["held_hi"]
                tot[grp + "HELD_NO_LOW_END_LINES"] += 1
            else:
                tot[grp + "HELD_LO"] += r["held_lo"]
                tot[grp + "HELD_HI"] += r["held_hi"]
            continue
        if st == CALC and r["m2"] is not None and r["method"] in ("E=G", "G"):
            tot[("G_CALCULATED" if grp == "ABOVE_" else "BELOW_CALCULATED")] += r["m2"]
        if st == CALC and r["m2"] is not None and r["method"] in ("E=G", "E") and grp == "ABOVE_":
            tot["E_CALCULATED"] += r["m2"]
        if st == ALT and r["m2"] is not None:
            k = "FORMED" if ("FORMED" in r["item"] or "tee" in r["item"]) else "EARTH_CAST"
            tot["OQ10_" + k] += r["m2"]
    return {k: round(v, 3) for k, v in sorted(tot.items())}


def write(outdir):
    os.makedirs(outdir, exist_ok=True)
    r4, delta, inp, rg = build()
    keys = ["element", "floor", "item", "method", "m2", "held_lo", "held_hi", "status", "basis", "freelancer",
            "verdict", "change", "cause", "refs"]

    def fmt(v):
        return "" if v is None else (round(v, 6) if isinstance(v, float) else v)
    with open(os.path.join(outdir, "FORMWORK_LINES_R4.csv"), "w", newline="", encoding="utf-8") as fh:
        wr = csv.DictWriter(fh, fieldnames=keys)
        wr.writeheader()
        for r in r4:
            wr.writerow({k: fmt(r.get(k)) for k in keys})
    dk = ["change", "element", "floor", "item", "r3_status", "r3_m2", "r3_held", "r4_status", "r4_m2", "r4_held",
          "calc_delta_m2", "cause", "refs"]

    def hr(r):
        if r is None or r.get("held_hi") is None:
            return ""
        return "%s .. %s" % ("" if r["held_lo"] is None else "%.3f" % r["held_lo"], "%.3f" % r["held_hi"])
    with open(os.path.join(outdir, "FORMWORK_DELTA_R3_R4.csv"), "w", newline="", encoding="utf-8") as fh:
        wr = csv.DictWriter(fh, fieldnames=dk)
        wr.writeheader()
        for a, b, cause in delta:
            ref = b or a
            m3 = a["m2"] if a and a["status"] in (CALC, ALT) else None
            m4 = b["m2"] if b and b["status"] in (CALC, ALT) else None
            wr.writerow(dict(change="REMOVED" if b is None else ("NEW" if a is None else "CHANGED"),
                             element=ref["element"], floor=ref["floor"], item=ref["item"],
                             r3_status=a["status"] if a else "", r3_m2=fmt(a["m2"]) if a else "", r3_held=hr(a),
                             r4_status=b["status"] if b else "", r4_m2=fmt(b["m2"]) if b else "", r4_held=hr(b),
                             calc_delta_m2=fmt(round((m4 or 0.0) - (m3 or 0.0), 6)), cause=cause,
                             refs=(b or {}).get("refs", "")))
    t3 = totals([dict(r, held_lo=r["held_lo"], held_hi=r["held_hi"]) for r in r3_lines()])
    t4 = totals(r4)
    summary = dict(schema="T264_FORMWORK_R4", rule="r4 = r3 (T-163 MERGED 659f889f) + the delta of FORMWORK_DELTA_R3_R4",
                   totals_r3=t3, totals_r4=t4,
                   delta={k: round(t4.get(k, 0.0) - t3.get(k, 0.0), 3) for k in sorted(set(t3) | set(t4))},
                   ring_b7=dict(soffit=0.666406, d_soffit=round(rg["d_soffit"], 6), d_side=round(rg["d_side"], 6),
                                d_band=round(rg["d_band"], 6), void_arcs_m=round(rg["void_arcs"], 6),
                                outer_slab_arcs_m=round(rg["outer_slab_arcs"], 6), cb1_void_face_m=rg["cb1"]["L"],
                                r3_soffit=round(rg["r3_soffit"], 6), r3_side=round(rg["r3_side"], 6)),
                   oblique_ends={k: dict(face=[f for f, v in o["faces"].items() if v["kind"] == "BEAM" and
                                               v["member"] and k.startswith(v["member"]) and min(
                                                   v["on_edge_m"].values()) > 2.0],
                                         edges=o["edge_len_m"]) for k, o in inp["oblique_ends"].items()},
                   counts=dict(r3=len(r3_lines()), r4=len(r4), delta=len(delta)))
    with open(os.path.join(outdir, "summary_r4.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=1, sort_keys=True)
    print(json.dumps(dict(totals_r3=t3, totals_r4=t4, delta=summary["delta"]), indent=1, sort_keys=True))
    return summary


if __name__ == "__main__":
    if sys.argv[1:2] == ["--check"]:
        check()
    else:
        write(sys.argv[1] if len(sys.argv) > 1 else HERE)
