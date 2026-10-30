"""T-377 on the development villa (read-only research run): every merged ledger row and every V3.0.27 candidate line that
measures an edge, head, jamb, perimeter or hole of the T-238 arched set (W15, W16, W26; W17 and the two passage arches
A-GF-01 / A-1F-01 HELD) classified OUTLINE / RECTANGLE / WIDTH_ONLY / RULE RECTANGLE / NOT_APPLICABLE / HELD, with the
value now, the value on the outline and the difference. Nothing is corrected here: each RECTANGLE row names the lane I
row that carries its correction.

    python3 -I research/agents_t377/t377_alsenan.py [--check] [--candidate <run>/v3027/V3_0_27_BOQ_LINES.json]

Inputs: the merged ledgers named per row (read, asserted, never edited); the outline record of T-238 (MERGED, W15 outline
VERIFIED by the Checker under T-227); own re-read this run of the arch chains (Drive "Alsenan chalet project" /
P7757_DXF_COMPRESSED.zip, P7757.dxf sha256 ab54dd55..: NW frame layer 1 jambs 2889 / 288A + chain 299F .. 299E (W15),
2566 / 256A + 274C .. 274B (W16); SE frame jambs 2211 / 2229, sill 2319, chain 1C67 .. 222E (W26)), which gives the
chord of the hole at the bed-joint mesh levels (HOLE_WIDTH_AT). Without --candidate the committed CANDIDATE_T377.csv
(from the V3.0.27 run of this task) is used. No coordinate, image or client name is written.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RES = HERE.parent
sys.path.insert(0, str(HERE))
import t377_arch_audit as A  # noqa: E402

# T-238 CENSUS_T238.csv (merged) outline record; own DXF re-read this run in the comment (agreement shown in summary)
OUT = {
    "W15": A.Outline("W15", 1.5523, 2.1609, 0.8391, 1.0088, 2.5243, band=0.101),   # own 1.0086 / 2.5241 / 4.3629
    "W16": A.Outline("W16", 1.5523, 2.1609, 0.8391, 1.0088, 2.5243, band=0.101),   # own 1.0086 / 2.5241 / 4.3629
    "W26": A.Outline("W26", 1.2000, 1.0500, 0.6500, 0.6147, 1.9709, band=0.0495),  # own 0.6145 / 1.9706 / 1.8745
}
OWN_REREAD = {"W15": (4.3629, 1.0086, 2.5241, 46), "W16": (4.3629, 1.0086, 2.5241, 49), "W26": (1.8745, 0.6145, 1.9706, 29)}
HELD_SET = ("W17", "A-GF-01", "A-1F-01")

# chord of the hole (m) at the bed-joint levels of the merged T-362 white mesh table that fall between springing and
# crown, read on the drawn arch chain (own re-read; wall-base levels: the opening starts at FFL = base + 0.10)
CHORD = {  # (wall, family, k): (opening, level_lo, level_hi, chord_at_lo, chord_at_hi)
    ("1F-W00", "A", "3"): ("W15+W16", 2.268, 2.294, 1.5515, 1.5484),
    ("1F-W00", "A", "4"): ("W15+W16", 3.021, 3.053, 0.6336, 0.4654),
    ("1F-W00", "B", "4"): ("W15+W16", 2.421, 2.453, 1.5244, 1.5121),
    ("1F-W00", "B", "5"): ("W15+W16", 3.024, 3.062, 0.6178, 0.4180),
    ("2F-W07", "A", "3"): ("W26", 2.268, 2.294, 1.1979, 1.1949),
    ("2F-W07", "B", "4"): ("W26", 2.421, 2.453, 1.1671, 1.1520),
}


def rd(rel):
    with open(RES / rel, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def one(rows, **kw):
    hit = [r for r in rows if all(r[k] == v for k, v in kw.items())]
    if len(hit) != 1:
        raise A.AuditError(f"expected one row {kw}, got {len(hit)}")
    return hit[0]


def f4(x):
    return "" if x is None else f"{x:.4f}"


def pct(now, out):
    return "" if now is None or out in (None, 0) else f"{100.0 * (now - out) / out:+.2f}"


ROWS = []
MESH = {}


def row(oid, trade, source, item, kind, unit, basis, now, outline, status, carrier, note):
    d = None if now is None or outline is None else now - outline
    ROWS.append(dict(opening=oid, trade=trade, ledger_or_line=source, item=item, quantity_kind=kind, unit=unit,
                     basis_used=basis, value_now=f4(now), value_on_outline=f4(outline), difference=f4(d),
                     difference_pct=pct(now, outline), status_now=status, correction_carrier=carrier, note=note))


def build():
    ROWS.clear()
    # 1. reveal faces (outside jambs + head) and their edge length: T-313 r2 ledger -> T-340 FILL_T326 (T-326 owns)
    rv = rd("agents_t313/REVEAL_LEDGER_T313.csv")
    fill = rd("agents_t340/FILL_T326_T340.csv")
    for oid in ("W15", "W16", "W26"):
        o = OUT[oid]
        j = one(rv, opening=oid, side="OUT", component="JAMBS")
        h = one(rv, opening=oid, side="OUT", component="HEAD")
        d = float(j["depth_m"])
        now = float(j["m2"]) + float(h["m2"])
        b = A.classify(o, "REVEAL_JAMBS_HEAD", now, depth=d)
        fr = one(fill, opening=oid, item="REVEAL.WINDOW_OUT")
        assert abs(float(fr["m2"]) - now) < 1e-6
        row(oid, "reveal (outside jambs + head)", "T-313 r2 REVEAL_LEDGER_T313.csv OUT JAMBS+HEAD -> T-340 FILL_T326 "
            "(T-326 r1 lines L-bafe1791 / L-f9f1a4cd / L-d9ffbb4e)", "ARCH.WINDOW_REVEAL (NEW)", "REVEAL_JAMBS_HEAD", "m2",
            b, now, o.reveal_jambs_head(d), j["height_status"], "T-326 r2 (own: D-T326-1)",
            f"d {d:.3f}; rectangle 2 x d x {float(j['ml']) / 2:.2f} + d x {float(h['ml']):.2f}; outline 2 x d x "
            f"{o.springing} + d x {o.arch_len} (R-T326-2)")
        ml = float(fr["ml"])
        row(oid, "reveal edge length", "T-340 FILL_T326_T340.csv ml (from T-313 r2)", "ARCH.WINDOW_REVEAL (NEW)",
            "EDGE_JAMBS_HEAD", "m", A.classify(o, "EDGE_JAMBS_HEAD", ml), ml, o.edge_jambs_head(), fr["status"],
            "T-326 r2 (own: D-T326-1)", "the line's m.l column carries the same rectangle as its m2")
    # 2. opening arrises on the facade (T-162 corners, confirmed by T-313 EDGE_RECONCILIATION): exterior / Sigma
    cor = rd("agents_t162/CORNERS_T162.csv")
    edge = rd("agents_t313/EDGE_RECONCILIATION_T313.csv")
    for oid, side in (("W15", "NW-5"), ("W16", "NW-5"), ("W26", "SE-1")):
        o = OUT[oid]
        c = one(cor, GROUP="OPENING_REVEAL", WHERE=f"{oid} on {side}")
        now = float(c["LENGTH_ML"])
        kind = "EDGE_WITH_SILL" if "SILL" in c["KIND"] else "EDGE_JAMBS_HEAD"
        assert abs(float(one(edge, opening=oid)["t313_ml"]) - now) < 1e-6
        out = o.edge_jambs_head() + (o.width if kind == "EDGE_WITH_SILL" else 0.0)
        row(oid, "opening arrises / corner bead (exterior, Sigma)", "T-162 CORNERS_T162.csv OPENING_REVEAL "
            f"({c['KIND']}); T-313 EDGE_RECONCILIATION 'same composition'", "exterior opening arris (T-314 package)",
            kind, "m", A.classify(o, kind, now), now, out, c["STATUS"], "T-314 (EXTERIOR PLASTER / SIGMA integration)",
            "T-238 DELTA recorded only the arc-minus-chord head (+0.972 / +0.771 m) and missed the jambs taken to the "
            "band crown / crown instead of the springing")
    w17 = one(cor, GROUP="OPENING_REVEAL", WHERE="W17 on NW-2")
    row("W17", "opening arrises / corner bead (exterior, Sigma)", "T-162 CORNERS_T162.csv OPENING_REVEAL (HEAD+JAMBS)",
        "exterior opening arris (T-314 package)", "EDGE_JAMBS_HEAD", "m", "RECTANGLE (archivolt 3.50)",
        float(w17["LENGTH_ML"]), None, w17["STATUS"], "T-314 (carry HELD, blank)",
        "R-T377-2: W17's outline is HELD (T-238 A5, archivolt 3.50 is not the opening); a PRINTED 10.290 m figure "
        "breaks the hold")
    # 3. spatter dash bound to the reveal carriers (T-349): follows the reveal rectangle
    sp = rd("agents_t349/PENDING_T349.csv")
    for oid in ("W15", "W16", "W26"):
        o = OUT[oid]
        r = one(sp, opening=oid, item="REVEAL.WINDOW_OUT")
        d = float(one(rv, opening=oid, side="OUT", component="JAMBS")["depth_m"])
        now = float(r["m2"])
        row(oid, "spatter dash on the reveal (B4-05)", "T-349 PENDING_T349.csv / FILL_T349.csv (carrier T-326)",
            "B4-05 SPATTER DASH under REVEAL.WINDOW_OUT", "REVEAL_JAMBS_HEAD", "m2",
            A.classify(o, "REVEAL_JAMBS_HEAD", now, depth=d), now, o.reveal_jambs_head(d), r["status"],
            "T-364 (SPATTER integration), after T-326 r2", "one face one carrier: the spatter row takes the reveal value")
    # 4. bed-joint mesh strip (white walls, T-362): opening cut at levels between springing and crown
    wm = rd("agents_t362/WHITE_MESH_LEVELS_T362.csv")
    tot = MESH
    tot.clear()
    for (wall, fam, k), (ops, lo, hi, c_lo, c_hi) in CHORD.items():
        r = one(wm, wall_id=wall, family=fam, k=k)
        assert abs(float(r["level_lo_m"]) - lo) < 1e-6 and abs(float(r["level_hi_m"]) - hi) < 1e-6
        n = 2 if ops == "W15+W16" else 1
        o = OUT[ops[:3]]
        if wall == "1F-W00":
            cut = float(r["cut_opening_m"])
            w_merged = 1.55                     # T-237 merged_w used by the mesh table (plan symbol 1.5523)
            rect = n * w_merged
            # the cut also carries W18 in masonry (0.4673) beside the two arches; its rectangle is right (not arched)
            assert abs(cut - rect - 0.4673) < 1e-4, (wall, fam, k, cut)
            over_lo, over_hi = n * (w_merged - c_lo), n * (w_merged - c_hi)
            tot.setdefault((wall, fam), [0.0, 0.0])
            tot[(wall, fam)][0] += over_lo
            tot[(wall, fam)][1] += over_hi
            row(ops, "bed-joint mesh strip (white family, B9 accessories)", f"T-362 WHITE_MESH_LEVELS_T362.csv {wall} "
                f"family {fam} k {k} (level {lo:.3f} .. {hi:.3f})", "MESH STRIP (T-363 package)", "HOLE_WIDTH_AT", "m",
                "RECTANGLE (crown)", rect, n * c_lo, r["band"] + " / mesh family CONDITIONAL",
                "T-363 (MASONRY ACCESSORIES integration)",
                f"chord on the drawn arch {n} x {c_lo:.4f} .. {n} x {c_hi:.4f}; the spandrel strip {over_lo:.4f} .. "
                f"{over_hi:.4f} m is masonry in the VERIFIED block deduction (outline) but its arch support is not "
                "established (lintel over an arch HELD, T-355 / lintel matrix BLOCKED_SUPPORT_IDENTITY): HELD by name, "
                "never cut as certain and never counted as certain")
        else:
            held = r["held"]
            assert "POSITION_UNKNOWN 1.2000 (W26" in held
            row("W26", "bed-joint mesh strip (white family, B9 accessories)", f"T-362 WHITE_MESH_LEVELS_T362.csv {wall} "
                f"family {fam} k {k} (level {lo:.3f} .. {hi:.3f})", "MESH STRIP (T-363 package)", "HOLE_WIDTH_AT", "m",
                "RECTANGLE (crown) in a HELD bound", 1.2, c_lo, "HELD (POSITION_UNKNOWN)", "T-363 (bound text only)",
                f"held opening part named at the rectangle 1.2000; on the outline {c_lo:.4f} .. {c_hi:.4f}: nothing valued moves")
    # 5. the opening head as a data field (T-237 merged sizes, consumed by T-355 / T-362 as the hole top)
    sz = [r for r in rd("agents_t237/OPENING_SIZES_T237.csv") if r["census_id"] in ("W15", "W16")]
    for r in sz:
        o = OUT[r["census_id"]]
        row(r["census_id"], "opening size field (head) consumed by course-based accessories",
            "T-237 OPENING_SIZES_T237.csv merged_head", "(data field, no line)", "HOLE_WIDTH_AT", "m",
            "RECTANGLE (band crown)", float(r["merged_head"]), o.crown, r["merged_status"],
            "T-363 input note (no quantity moves: no mesh level lies between 3.10 and 3.20 on 1F-W00)",
            "merged_head 3.10 is the band crown; the opening crown is 3.00 (T-238); merged_fixed_m2 4.363 is right")
    # 6. OUTLINE rows (correct): blockwork, interior plaster / paint, exterior holes
    od = rd("agents_t291/OPENING_DEDUCTIONS_T291.csv")
    for oid in ("W15", "W16", "W26"):
        v = float(one(od, opening_id=oid)["deduction_m2"])
        row(oid, "blockwork deduction", "T-291 OPENING_DEDUCTIONS_T291.csv / T-333 (V3.0.26 T-279)", "MAS.BLOCK",
            "HOLE_AREA", "m2", A.classify(OUT[oid], "HOLE_AREA", v), v, OUT[oid].hole_m2(),
            one(od, opening_id=oid)["state"], "none", "outline (T-227 / T-261)")
    pd = rd("agents_t292/OPENING_DEDUCTIONS_T292.csv")
    for oid in ("W15", "W16"):
        v = float(one(pd, opening_id=oid)["owner_ded_new_m2"])
        row(oid, "interior plaster / paint deduction", "T-292 OPENING_DEDUCTIONS_T292.csv room 1F-13 (V3.0.20 T-244)",
            "FIN.PLASTER / FIN.PAINT", "HOLE_AREA", "m2", A.classify(OUT[oid], "HOLE_AREA", v), v, OUT[oid].hole_m2(),
            "DRAWING-CONFIRMED", "none", "outline")
    w26p = one(pd, opening_id="W26")
    row("W26", "interior plaster / paint deduction", "T-292 OPENING_DEDUCTIONS_T292.csv room ST-2F", "FIN.PLASTER / FIN.PAINT",
        "HOLE_AREA", "m2", "OUTLINE (merged size 1.875, room HELD)", None, OUT["W26"].hole_m2(), w26p["owner_ded_new_m2"],
        "none", "merged size is the outline; the room height is HELD (Q-72)")
    ho = rd("agents_t305/OPENING_HOLES_T305.csv")
    for oid in ("W15", "W16", "W26"):
        r = one(ho, opening=oid)
        v = float(r["deduct_fixed_m2"])
        row(oid, "exterior plaster / Sigma hole", "T-305 OPENING_HOLES_T305.csv / T-337 OPENINGS_T337.csv",
            "exterior plaster face line", "HOLE_AREA", "m2", A.classify(OUT[oid], "HOLE_AREA", v), v, OUT[oid].hole_m2(),
            r["deduct_status"], "none",
            f"information columns head_m {r['head_m']} / window_measure_m2 {r['window_measure_m2']} are not the hole "
            "(band crown / Q-32 A rectangle); not a quantity")
    # 7. WIDTH_ONLY rows (correct): outside thresholds / sill, skirting breaks
    th = rd("agents_t340/FILL_T327_T340.csv")
    for oid in ("W15", "W16", "W26"):
        r = one(th, opening=oid)
        d = float(one(rv, opening=oid, side="OUT", component="JAMBS")["depth_m"])
        v = float(r["m2"])
        row(oid, "outside threshold / sill strip", "T-325 SILL_THRESHOLD_LEDGER / T-340 FILL_T327_T340.csv",
            "ARCH.WINDOW_REVEAL (T-327)", "WIDTH_ONLY", "m2", A.classify(OUT[oid], "WIDTH_ONLY", v, depth=d), v,
            OUT[oid].width * d, r["status"], "none", "below the springing: the arch does not reach the sill")
    sk = rd("agents_t341/FILL_TABLE_T341.csv")
    for oid in ("W15", "W16"):
        r = [x for x in sk if x["census_id"] == oid and x["opening_id"].endswith("#glazing-half")][0]
        v = float(r["amount"])
        row(oid, "skirting break (glazing half)", "T-296 / T-341 FILL_TABLE_T341.csv", "FIN.SKIRTING", "WIDTH_ONLY", "m",
            "WIDTH_ONLY", v, OUT[oid].width / 2, "DRAWING-CONFIRMED", "none", "half the plan width (F-17), width only")
    # 8. RULE rectangle (correct for the window unit only)
    for oid, v in (("W15", 4.650), ("W16", 4.650), ("W26", 2.040)):
        o = OUT[oid]
        q = 1.55 * o.crown if oid != "W26" else o.width * o.crown
        row(oid, "window unit (aluminium)", "T-238 DELTA / T-232 window lines", "WINDOW.ALUMINIUM", "WINDOW_UNIT_Q32A",
            "m2", "RULE RECTANGLE (Q-32 A)", v, q, "DRAWING-CONFIRMED", "none",
            "owner Q-32 A: enclosing rectangle on the opening line (crown); outline area is not the window measure")
    # 9. NOT_APPLICABLE rows
    for oid in ("W15", "W16", "W26"):
        row(oid, "inside reveal (room side)", "T-313 REVEAL_LEDGER IN JAMBS / HEAD", "-", "REVEAL_JAMBS_HEAD", "m2",
            "NOT_APPLICABLE", 0.0, 0.0, "DRAWING-CONFIRMED (no surface)", "none", "frame flush with the room face")
        row(oid, "lintel over the opening", "T-355 / T-362 lintel spans; alsenan_lintels_s8_6 matrix", "concrete lintel",
            "WIDTH_ONLY", "m", "NOT_APPLICABLE (HELD)", None, None, "HELD", "none",
            "a lintel over an arch is not the schedule's straight lintel: span HELD (T-355); matrix BLOCKED_SUPPORT_IDENTITY")
    return ROWS


def held_check():
    """(c) W17, A-GF-01, A-1F-01 stay HELD / blank where T-238 left them UNRESOLVED (R-T377-2)."""
    out = []

    def chk(oid, src, status, value, dev=None):
        try:
            res = A.check_held(oid, status, value, dev)
            ok = "PASS"
        except A.AuditError as e:
            res, ok = str(e), "FINDING"
        out.append(dict(opening=oid, ledger=src, status=status, value=value or "", result=res, verdict=ok))

    for r in rd("agents_t313/REVEAL_LEDGER_T313.csv"):
        if r["opening"] in HELD_SET:
            chk(r["opening"], f"T-313 REVEAL {r['side']} {r['component']}", r["state"], r["m2"] or None)
    for r in rd("agents_t340/OWNERS_T340.csv"):
        if r["opening"] in HELD_SET and r["action"] in ("HOLD", "ADD_HELD_ROW"):
            chk(r["opening"], f"T-340 OWNERS {r['comp']}", r["status"], r["m2"] or None)
    for r in rd("agents_t292/OPENING_DEDUCTIONS_T292.csv"):
        if r["opening_id"] in HELD_SET:
            v = r["owner_ded_new_m2"]
            chk(r["opening_id"], f"T-292 deduction room {r['room']}", "HELD" if "HELD" in v else "",
                v.split(" ")[-2] if "HELD" in v else v)
    for r in rd("agents_t291/OPENING_DEDUCTIONS_T291.csv"):
        if r["opening_id"] in HELD_SET:
            if r["state"] == "NOT_APPLICABLE":
                out.append(dict(opening=r["opening_id"], ledger="T-291 blockwork deduction", status=r["state"], value="",
                                result="host glazed: no masonry hole", verdict="PASS"))
            else:
                chk(r["opening_id"], "T-291 blockwork deduction", r["state"], r["deduction_m2"] or None)
    for r in rd("agents_t305/OPENING_HOLES_T305.csv"):
        if r["opening"] in HELD_SET:
            chk(r["opening"], "T-305 exterior hole", r["deduct_status"], r["deduct_fixed_m2"],
                "T-302 MERGED W17_HOLE_LEDGER: developed hole")
    for r in rd("agents_t162/CORNERS_T162.csv"):
        if r["GROUP"] == "OPENING_REVEAL" and r["WHERE"].split(" ")[0] in HELD_SET:
            chk(r["WHERE"].split(" ")[0], "T-162 CORNERS opening arris", r["STATUS"], r["LENGTH_ML"])
    for r in rd("agents_t355/MESH_LEVELS_T355.csv"):
        if "A-GF-01" in r["held"] or "A-1F-01" in r["held"]:
            oid = "A-GF-01" if "A-GF-01" in r["held"] else "A-1F-01"
            chk(oid, f"T-355 mesh {r['wall_id']} k {r['k']}", "HELD", None)
    for r in rd("agents_t368/EDGE_LEDGER_T368.csv"):
        if "A-GF-01" in r["edge_id"]:
            chk("A-GF-01", "T-368 tile edge", r["status"], r["length_m"] or None)
    return out


LEDGER_LINES = {  # line ids the merged ledgers bind to the arched set (T-305 / T-313 / T-325 / T-296 / T-341)
    "L-8bb83e16cc7b104ab88b": "W15;W16;W17", "L-d52c4f763b19aedf8b8b": "W26", "L-43527ae4e8ec75c56636": "W15;W16;W17",
    "L-348c4d8d32f3f6d35fe5": "W26", "L-ba3599ec2dc82c221617": "W15;W16", "L-309f118f6fce78b6c28e": "W17",
    "L-0e2e7299371efb8338cc": "W15", "L-146170b53ca02c2456f9": "W16", "L-d91627a1feb6dc854723": "W26",
    "L-c90d5d6c06a671fc3b99": "W17", "L-868aee125705bb8d17f6": "A-GF-01", "L-e2eb7cee560d74ae91e4": "A-1F-01",
    "L-4f7b4d60c72563479f49": "A-GF-01", "L-9e954a8e7da9329acc4f": "A-1F-01"}
RX = re.compile(r"(?<![-\w])(W15|W16|W26|W17|A-GF-01|A-1F-01)(?![\w-])")


def _basis(item, unit, state, ops, text):
    """basis of a V3.0.27 line for the arched set (R-T377-1 / -2), with the values it carries checked."""
    held = state in ("BLOCKED_RFI", "BOUNDED_EXPOSURE") and item.startswith(("ARCH.WINDOW_REVEAL", "ARCH.THRESHOLD",
                                                                            "FIN.EXT", "ARCH.FACADE"))
    if unit == "pcs" or item == "ARCH.PASSAGE":
        return "NOT_APPLICABLE (count)", ""
    if held:
        return "BLANK (carrier pending)", "T-326 / T-327 reveal and threshold fill" if "WINDOW_REVEAL" in item or \
            "THRESHOLD" in item else "T-314 exterior plaster / Sigma"
    if item == "ARCH.WINDOW":
        if "W17" in ops:
            return "HELD (Q-76 A bound 9.87 .. 11.515)", ""
        for oid in ops:
            m = re.search(oid + r" ([0-9.]+)", text)
            q = OUT[oid].crown * (1.55 if oid != "W26" else OUT[oid].width)
            if not m or abs(float(m.group(1)) - q) > 0.005:
                raise A.AuditError(f"{oid}: window line value is not the Q-32 A rectangle {q}")
        return "RULE RECTANGLE (Q-32 A)", ""
    if item in ("FIN.PLASTER", "FIN.PAINT"):
        if "W17" in ops:
            if "8.7414" not in text or "8.9965" not in text:
                raise A.AuditError("W17 room-side hole is not the T-302 developed bound")
            return "HELD BOUND (T-302 developed room-side hole 8.7414 .. 8.9965)", ""
        for oid in ops:
            if not re.search(oid + r"[^;]*-> 4\.3629", text):
                raise A.AuditError(f"{oid}: plaster / paint deduction is not the outline 4.3629")
        return "OUTLINE", ""
    if item in ("MAS.BLOCK", "ARCH.WALL_PANEL", "ARCH.WALL_VOLUME"):
        for oid in ops:
            m = re.search(oid + r" ([0-9.]+) DEDUCTED", text)
            if not m or abs(float(m.group(1)) - OUT[oid].hole_m2()) > 0.0005:
                raise A.AuditError(f"{oid}: masonry deduction is not the outline")
        return "OUTLINE", ""
    if item in ("FIN.SKIRTING", "FIN.FLOOR.PORCELAIN"):
        return "WIDTH_ONLY", ""
    return "UNCLASSIFIED", ""


def candidate_rows(path):
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    lines = d if isinstance(d, list) else d["lines"]
    out = []
    for ln in lines:
        txt = json.dumps(ln, ensure_ascii=False)
        ops = sorted(set(RX.findall(txt)))
        lid = ln.get("line_id", "")
        if lid in LEDGER_LINES:
            ops = sorted(set(ops) | set(LEDGER_LINES[lid].split(";")))
        if not ops:
            continue
        item, unit, state = ln.get("item_code", ""), ln.get("unit", ""), ln.get("evidence_state", "")
        basis, carrier = _basis(item, unit, state, ops, txt)
        br = ln.get("bounded_range") or {}
        loc = ln.get("location") or {}

        def n(v):
            return "" if v in (None, "") else f"{float(v):.6f}"
        out.append(dict(line_id=lid, item_code=item, unit=unit, floor=loc.get("floor", ""), state=state,
                        quantity=n(ln.get("measured_net")), low=n(br.get("low")), high=n(br.get("high")),
                        openings=";".join(ops), basis=basis, carrier=carrier))
    return sorted(out, key=lambda r: (r["floor"], r["item_code"], r["line_id"]))


def csv_text(rows):
    if not rows:
        return ""
    b = io.StringIO()
    w = csv.DictWriter(b, fieldnames=list(rows[0]), lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return b.getvalue()


def outputs(cand_rows):
    audit = build()
    held = held_check()
    rect = [r for r in audit if r["basis_used"].startswith("RECTANGLE")]
    tot = {}
    for r in rect:
        if "HELD bound" in r["basis_used"] or r["item"] == "(data field, no line)" or "mesh" in r["trade"]:
            continue
        if r["value_on_outline"] and r["difference"]:
            key = (r["trade"], r["unit"])
            tot[key] = round(tot.get(key, 0.0) + float(r["difference"]), 4)
    summary = dict(
        task="T-377", openings=sorted(OUT) + list(HELD_SET),
        outline_own_reread={k: dict(hole_m2=v[0], segment_m2=v[1], arch_len_m=v[2], segments=v[3])
                            for k, v in OWN_REREAD.items()},
        outline_record_hole_m2={k: round(o.hole_m2(), 4) for k, o in OUT.items()},
        rows=len(audit), by_basis={b: sum(1 for r in audit if r["basis_used"] == b)
                                   for b in sorted({r["basis_used"] for r in audit})},
        rectangle_rows=len(rect),
        rectangle_difference_by_trade={f"{k[0]} ({k[1]})": v for k, v in sorted(tot.items())},
        mesh_spandrel_held_m={f"{w} family {f}": [round(v[0], 4), round(v[1], 4)] for (w, f), v in sorted(MESH.items())},
        carriers=sorted({r["correction_carrier"] for r in rect}),
        held_check=dict(rows=len(held), findings=[f"{h['opening']} {h['ledger']}: {h['result']}"
                                                   for h in held if h["verdict"] != "PASS"]),
        candidate_lines=len(cand_rows),
        candidate_by_basis={b: sum(1 for r in cand_rows if r["basis"] == b) for b in sorted({r["basis"] for r in cand_rows})},
        candidate_rectangle_lines=sum(1 for r in cand_rows if r["basis"].startswith("RECTANGLE")))
    return {"AUDIT_T377.csv": csv_text(audit), "HELD_CHECK_T377.csv": csv_text(held),
            "CANDIDATE_T377.csv": csv_text(cand_rows),
            "summary.json": json.dumps(summary, indent=1, ensure_ascii=False) + "\n"}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--candidate")
    a = ap.parse_args(argv)
    if a.candidate:
        cand = candidate_rows(a.candidate)
    else:
        p = HERE / "CANDIDATE_T377.csv"
        cand = rd("agents_t377/CANDIDATE_T377.csv") if p.exists() else []
    files = outputs(cand)
    bad = 0
    for name, text in files.items():
        p = HERE / name
        if a.check:
            if not p.exists() or p.read_text(encoding="utf-8") != text:
                print(f"DIFFERS {name}")
                bad += 1
        else:
            p.write_text(text, encoding="utf-8")
    print(files["summary.json"])
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
