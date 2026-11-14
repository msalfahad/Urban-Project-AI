"""T-768 F-09 OPENINGS, CEILINGS, DOMES to figures (DELIVERY MODE fix-row set; worker 2, 2026-11-14).

Reads the candidate line index ARCH_TAKEOFF_V3.0.81 (agents/task-T-770, sha16 3976b262611bc3bd) and writes
out/FIX_ROWS.json + out/FIX_ROWS.md: one row per HELD line of ARCH.WINDOW, ARCH.SHUTTER, DOOR.INTERNAL.PVC,
DOOR.MAIN_ENTRANCE, ARCH.THRESHOLD, ARCH.WINDOW_REVEAL, FIN.CEILING, FIN.CEILING.BULKHEAD, FIN.DOME.SOFFIT and
FIN.MARBLE.LIFT_SURROUND (left to this row by T-766). Nothing else is touched. W17 m2 (L-0392d37452e98050dd1b) is
already carried by MAIN_FILL_4 (owner Q-76 A, 9.870 m2) and is skipped here (overlap 0).

Inputs (merged files on the working branch, read as data): T-198 opening census (widths, printed heights, freelancer
sizes), T-232 opening inputs (engine-held doors, W02 head 2.20 from T-201 section B-B, W11 / W12 head 2.20 T-207),
T-313 reveal ledger (W02 frame band 0.120 flush with the room face, OUT depth 0.080), T-302 W17 developed hole (radial
jambs, jamb tops 2.2190 / 2.1676, centreline developed 3.1331, glass on the room face BD2), T-325 sill / threshold
ledger (width x wall depth per opening), T-475 lift landing census (bands 0.50, 2F right face 0.400, A(h) formula),
T-640 / T-573 ceiling bounds, T-193 dome shell (printed 442 / 190 / 10, concentric, VERIFIED 2.540681 m3), Q-63 C
(sea-side gate 1.00 in a 0.20 band).

Choices (each labelled on its row):
  doors held in the engine schedule: the closure (jamb to jamb) width, as every released PVC line already uses
    (GF released 9.68 = 4.40 x 2.20 closure); D-GF-14 has no jamb band, leaf r 0.69 + Q-04 +0.10 = 0.80; height Q-55 C
    2.20 -> DEFAULT.
  main entrance D-GF-07 and W02: the plan / elevations print one opening (2.00 x 2.50; 6.33 x 2.20 by section B-B);
    the renders differ (D-53): drawings govern -> DRAWING-READ, replaced if the designer answers D-53 otherwise.
  shutters W11 / W12 / W14: the shutter covers its window opening (area allowance, DELIVERY_MODE s.3 step 4):
    1.95 x 2.20 (T-207 head between the leaves) and 2.45 x 1.60 (printed) -> ESTIMATE (no shutter schedule, D-54).
  lift surround (B6-06): landing door h = company default 2.10 (lift landing door 1.00 x 2.10 unless printed);
    A = h (L + R) + T (W + L + R), bands 0.50 (UP-ELEV-002), 2F right face drawn 0.400 (T-475) -> DEFAULT.
  external entrance thresholds: T-325 width x wall depth (DRAWING-CONFIRMED geometry), finish unprinted -> DEFAULT;
    OP-027 arch strip printed both terms -> DRAWING-READ; OP-020 passage into the GF W.C.: 0.90 x 0.20 wet threshold
    -> DEFAULT; sea gate D-GF-15: 1.00 gate in the 0.20 band (Q-63 C element) -> ESTIMATE; the five unattributed
    strips are wall bodies, not thresholds (T-325, Checker-merged) -> EXCLUDED NOT_APPLICABLE.
  reveals: W02 OUT jambs 2 x 0.080 x 2.20 (T-313 depth, T-201 height) DRAWING-READ. W03 curved floor glazing: no frame
    read; same saloon wall and aluminium system as W02 (frame band 0.120 flush with the room face) -> OUT 0.080 deep,
    IN no surface -> ESTIMATE / NOT_APPLICABLE. W17: glass on the room face BD2 (T-302 s.1) -> IN no surface; OUT full
    radial 0.20 along jambs 2.2190 + 2.1676 and the head arc (centreline chord 3.1331, crown 3.00) -> ESTIMATE.
  ceilings: stair box tops 12.9742 (2F) / 1.750 (GF) and the GF west strip 0.760 at their drawn areas (T-640 high ends)
    finished as a ceiling (company default) -> DEFAULT; the 1F living parent line is carried whole by the decor group
    line L-43bf1f869e1588f1d3bd (R-T284-1) -> EXCLUDED CARRIED (a figure would count it twice); bulkhead GF-RFD4E1D
    free beam edge 6.5428 x 0.15 owner-method drop -> DEFAULT.
  domes (west / east): intrados = inner spherical cap of the printed shell (outer D 4.42, rise 1.90, t 0.10,
    concentric): R = (a^2 + h^2) / 2h, inner R - 0.10, inner cap height 1.80, area 2 pi Ri hi; open to the 1F rooms
    through the drawn slab voids V-05 / V-06 (T-719); closure D-20 unanswered -> DEFAULT.

  python3 -I research/agents_t768/t768_fill.py <LINE_INDEX_V3_0_81.json> [--check]
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(HERE, "out", "FIX_ROWS.json")
OUT_MD = os.path.join(HERE, "out", "FIX_ROWS.md")
T198 = os.path.join(ROOT, "research", "agents_t198", "OPENINGS_T198.csv")
INDEX_SHA16 = "3976b262611bc3bd"
FAMILIES = ("ARCH.WINDOW", "ARCH.SHUTTER", "DOOR.INTERNAL.PVC", "DOOR.MAIN_ENTRANCE", "ARCH.THRESHOLD",
            "ARCH.WINDOW_REVEAL", "FIN.CEILING", "FIN.CEILING.BULKHEAD", "FIN.DOME.SOFFIT", "FIN.MARBLE.LIFT_SURROUND")
SKIP = {"L-0392d37452e98050dd1b": "W17 m2 carried by MAIN_FILL_4 (owner Q-76 A 9.870)"}
LABELS = ("MEASURED", "DRAWING-READ", "DEFAULT", "ESTIMATE", "SAFETY")
r6 = lambda x: round(x + 0.0, 6)

DOOR_H = 2.20                      # Q-55 C
LIFT_H, BAND = 2.10, 0.50          # company default lift landing door; UP-ELEV-002


def surround(w, left, right, h=LIFT_H, top=BAND):
    return h * (left + right) + top * (w + left + right)


def dome_intrados(d_out=4.42, rise=1.90, t=0.10):
    a = d_out / 2
    r_out = (a * a + rise * rise) / (2 * rise)
    r_in = r_out - t
    h_in = rise - t                # concentric: the base plane cuts both spheres at the same centre offset
    return 2 * math.pi * r_in * h_in


def arc_len(chord, rise):
    r = (chord * chord / 4 + rise * rise) / (2 * rise)
    return 2 * r * math.asin(chord / 2 / r)


W17_JAMBS = 2.2190 + 2.1676
W17_CHORD = 3.1331                 # centreline developed jamb to jamb (T-302)
W17_RISE = 3.00 - W17_JAMBS / 2
W17_HEAD = arc_len(W17_CHORD, W17_RISE)
DOME = dome_intrados()

FIG = {
    # windows / doors
    "L-cdf1a9e6bcb2e00c3098": (6.33 * 2.20, "DRAWING-READ", "W02 GF saloon: plan '633' x head 2.20 (T-201 section B-B +1.00 .. +3.20); one window on every drawing, the render's pier (D-53) not printed"),
    "L-dd2ecc97cf3f9dcd86c3": (1, "DRAWING-READ", "W02: 1 opening on plan, section and elevation (render shows 2, D-53; drawings govern)"),
    "L-ac8a0ea9174f53a359dd": (3 * 0.80 * DOOR_H, "DEFAULT", "D-GF-02 0.80 + D-GF-10 0.80 (closure jamb hits, DXF 0.797) + D-GF-14 0.80 (leaf r 0.69 + Q-04 0.10) x 2.20 Q-55 C; closure width as the released PVC lines"),
    "L-236f7aba1ca49962667a": (3, "DRAWING-READ", "D-GF-02 / D-GF-10 / D-GF-14: 3 doors drawn (T-198 census)"),
    "L-f4a12cd20b0f5e173430": ((1.00 + 0.80) * DOOR_H, "DEFAULT", "D-1F-03 1.00 + D-1F-04 0.80 (closure jamb hits, T-198) x 2.20 Q-55 C"),
    "L-5fa8e384af588d638eb4": (2, "DRAWING-READ", "D-1F-03 / D-1F-04: 2 doors drawn (T-198 census)"),
    "L-6f06f2eaa7ab76256979": (2.00 * 2.50, "DRAWING-READ", "D-GF-07 printed 2.00 (sheet03 chain 80 / 200 / 90) x 2.50 (SE elevation chain 85 / 250); render single leaf (D-53) not printed"),
    "L-8ee14244d410e740c706": (1, "DRAWING-READ", "D-GF-07: one double-leaf opening (a double leaf is one opening, T-232)"),
    "L-1cb158e866920455812a": (1.95 * 2.20, "ESTIMATE", "shutter W11 covers its opening: 1.95 printed (sheet03 chain) x 2.20 between the louvred leaves (T-207); no shutter schedule (D-54)"),
    "L-87d822fcabc5b52241d9": (1.95 * 2.20, "ESTIMATE", "shutter W12 as W11: 1.95 x 2.20 (T-207); D-54"),
    "L-9d0c79baa4fe0e9d95c8": (2.45 * 1.60, "ESTIMATE", "shutter W14 covers its opening: 2.45 x 1.60 printed (SE elevation +6.90 .. +8.50); D-54"),
    # lift surround
    "L-b66b8e76425d81ff9f19": (surround(1.0, 0.5, 0.5), "DEFAULT", "ELV-01-GF: h 2.10 default x (0.50 + 0.50) + top 0.50 x (1.00 + 0.50 + 0.50); faces 0.70 / 0.65 hold the bands (T-475)"),
    "L-d788f643b290e8f92558": (surround(1.0, 0.5, 0.5), "DEFAULT", "ELV-01-1F: h 2.10 default x (0.50 + 0.50) + 0.50 x 2.00; faces 0.60 / 0.935 hold the bands (T-475)"),
    "L-fdbd9636828f045aae5a": (surround(1.0, 0.5, 0.4), "DEFAULT", "ELV-01-2F: right face 0.400 to the internal corner (DXF + PDF, T-475): h 2.10 x (0.50 + 0.40) + 0.50 x 1.90"),
    # thresholds
    "L-3e5c6b7af8dd06b2836c": (0.15, "DEFAULT", "D-2F-01 external entrance: width x wall depth 0.15 (T-325 ledger, drawn); sill finish unprinted -> company marble threshold"),
    "L-74cd61b430eec9933d15": (0.18, "DEFAULT", "D-GF-03 external entrance 0.90 x 0.20 (T-325); finish unprinted"),
    "L-8111095f6db78f0e674b": (0.18, "DEFAULT", "D-GF-09 external entrance 0.90 x 0.20 (T-325); finish unprinted"),
    "L-9fa69ef1a11ef9987967": (0.20, "DEFAULT", "D-GF-06 external entrance 1.00 x 0.20 (T-325); finish unprinted"),
    "L-b3933a51bd95e9bc542b": (0.20, "DEFAULT", "D-GF-01 external entrance 1.00 x 0.20 (T-325); finish unprinted"),
    "L-ad41b065d825c0190b7d": (0.40, "DEFAULT", "D-GF-07 main entrance 2.00 x 0.20 (T-325); finish unprinted"),
    "L-868aee125705bb8d17f6": (0.15, "DRAWING-READ", "A-GF-01 arch OP-027: floor continues (UP-THR-001) 1.000 x 0.150 (T-340 FILL, T-648 fix row)"),
    "L-9bcc79e76f84667b244a": (0.9 * 0.2, "DEFAULT", "OP-020 leafless passage into the GF W.C.: wet threshold 0.90 x 0.20 (T-325 geometry); treatment default = wet threshold"),
    "L-56acf34557c315f65bb1": (1.00 * 0.20, "ESTIMATE", "sea-side gate D-GF-15 (G-02): 1.00 gate in the 0.20 band (Q-63 C element, GF plan); designer clarification replaces it"),
    # reveals
    "L-bcc55693d203e384d46e": (2 * 0.08 * 2.20, "DRAWING-READ", "W02 OUT jambs: 2 x 0.080 (T-313: wall 0.200 - frame band 0.120 flush with the room face) x 2.20 (T-201); head 0.5064 already on L-429605a88ef09abda085"),
    "L-e44e09189fe2941f2d21": (0.08 * (2 * 4.30 + 6.57), "ESTIMATE", "W03 OUT jambs + head: 0.080 (frame as W02, same saloon wall and system) x (2 x 4.30 printed + 6.57 printed)"),
    "L-30133ea5a4fb6847c519": (0.08 * 6.57, "ESTIMATE", "W03 OUT floor strip: 0.080 x 6.57 (frame as W02)"),
    "L-ee6793c9a96916a5a7c9": (0.20 * (W17_JAMBS + W17_HEAD), "ESTIMATE", f"W17 OUT: glass on the room face BD2 (T-302 s.1) -> full radial 0.20 x (jambs 2.2190 + 2.1676 + head arc {W17_HEAD:.4f}: centreline chord 3.1331, rise to the 3.00 crown)"),
    "L-c90d5d6c06a671fc3b99": (0.20 * W17_CHORD, "ESTIMATE", "W17 sill strip (OUT side; IN has no surface): 0.20 x centreline developed 3.1331 (T-302)"),
    # ceilings
    "L-dd6930fd19ca1b908c56": (12.9742, "DEFAULT", "2F stair box top under the roof slab 12.9742 drawn (T-271 / T-283 r3, T-640 high end); finished as a ceiling (company default; Q-72 / O-P8-02)"),
    "L-2175a965bb7c48a50e6c": (1.75, "DEFAULT", "GF stair top under the 1F slab 1.750 drawn (T-283 r3, T-640 high end); flight soffits stay in the stair soffit lines"),
    "L-4b41debf41fff9e3faae": (3.80 * 0.20, "DEFAULT", "GF-RFD4E1D west strip OP-003 3.80 x 0.20 drawn (T-431 / T-640); ceiling as the room"),
    "L-31f9b7008ea883f1b78d": (6.5428 * 0.15, "DEFAULT", "GF-RFD4E1D bulkhead: free beam edge 6.5428 x owner-method drop 0.15 (T-431 / T-640 high end)"),
    "L-cf3e2b55648f676ffb1d": (DOME, "DEFAULT", f"west dome intrados: printed 442 / 190 / 10 concentric (T-193): Ri {(4.42**2/4 + 1.9**2) / 3.8 - 0.1:.4f}, hi 1.80, 2 pi Ri hi = {DOME:.4f}; open over void V-05 (T-719); closure D-20 open"),
    "L-f74c0fc7f78b579e6097": (DOME, "DEFAULT", f"east dome intrados as west (twin shell, T-193): {DOME:.4f}; open over void V-06 (T-719); closure D-20 open"),
}
EXCL = {
    "L-1c71cd45a5116bdc5260": ("NOT_A_THRESHOLD_T-325", "STRIP_NOT_ATTRIBUTED wall body 0.188 m2 (T-325 Checker-merged): not a threshold piece"),
    "L-2991f35326b961a6d238": ("NOT_A_THRESHOLD_T-325", "WALL_BAND_REMAINDER 0.036 m2 (D-V26-07, T-325): part of a doorway face, not a threshold"),
    "L-44b8dcf4b30e11a464f5": ("NOT_A_THRESHOLD_T-325", "WALL_BAND_REMAINDER 0.034 m2 (D-V26-07, T-325): not a threshold"),
    "L-479acdcb1e5e01bf3957": ("NOT_A_THRESHOLD_T-325", "WALL_BAND_REMAINDER 0.031 m2 (D-V26-07, T-325): not a threshold"),
    "L-f4cfd731c98468026078": ("NOT_A_THRESHOLD_T-325", "WALL_BAND_REMAINDER 0.041 m2 (D-V26-07, T-325): not a threshold"),
    "L-e21b84e60826b8be59fa": ("NO_SURFACE_FRAME_ON_ROOM_FACE", "W03 IN jambs / head: frame flush with the room face (as W02, T-313) -> no inside reveal; revert if the frame is read deeper"),
    "L-29637dbaa9fe1acc7b82": ("NO_SURFACE_FRAME_ON_ROOM_FACE", "W03 IN floor strip: frame on the room face (as W02) -> the room floor runs to the frame"),
    "L-3e3a3bf8e2fd272a4c8e": ("NO_SURFACE_FRAME_ON_ROOM_FACE", "W17 IN jambs / head: glass line on the room face BD2 (T-302 s.1, T-250) -> no inside reveal"),
    "L-fc116bb666b184740090": ("CARRIED_BY_L-43bf1f869e1588f1d3bd", "1F living parent: board carried whole by the decor group line 51.0496 (R-T284-1, T-573); a figure would count it twice"),
}


def freelancer_windows():
    """Windows m2 from the T-198 freelancer columns (W x H per census row; W15 / W16 share one x2 key)."""
    tot, seen = 0.0, set()
    for r in csv.DictReader(open(T198, encoding="utf-8")):
        if r["KIND"] != "WINDOW" or not r["FREELANCER_W"]:
            continue
        tot += float(r["FREELANCER_W"]) * float(r["FREELANCER_H"])
        seen.add(r["ID"])
    return round(tot, 2), len(seen)


def build(index_path):
    raw = open(index_path, "rb").read()
    if hashlib.sha256(raw).hexdigest()[:16] != INDEX_SHA16:
        raise SystemExit("index is not V3.0.81 3976b262611bc3bd")
    lines = json.loads(raw)["lines"]
    rows, seen = [], set()
    for l in lines:
        ic, lid = l["item_code"], l["line_id"]
        if ic not in FAMILIES or l["class"] in ("RELEASED", "EXCLUDED") or lid in SKIP:
            continue
        before = {"class": l["class"], "net": l["measured_net"], "low": l["held_low"], "high": l["held_high"]}
        base = dict(line_id=lid, item_code=ic, unit=l["unit"], element_id=l["element_id"], before=before, set="OPENINGS_CEILINGS")
        if lid in EXCL:
            reason, why = EXCL[lid]
            base.update(after={"class": "EXCLUDED", "net": None, "reason": reason}, label="NOT_APPLICABLE", basis=why)
        else:
            if lid not in FIG:
                raise SystemExit(f"{lid} {ic}: no figure")
            val, lab, why = FIG[lid]
            if not val or val <= 0:
                raise SystemExit(f"{lid}: figure missing -> never 0")
            lo, hi = before["low"], before["high"]
            if lo is not None and val < lo - 1e-6 or hi is not None and val > hi + 1e-6:
                raise SystemExit(f"{lid}: {val} outside the held bound {lo} .. {hi}")
            if lab not in LABELS:
                raise SystemExit(lid)
            base.update(after={"class": "RELEASED", "net": r6(val)}, label=lab, basis=why)
        seen.add(lid)
        rows.append(base)
    unused = (set(FIG) | set(EXCL)) - seen
    if unused:
        raise SystemExit(f"figures for lines not in the index: {sorted(unused)}")
    rows.sort(key=lambda r: (r["item_code"], r["unit"], r["element_id"]))
    return rows


def summarise(rows, lines):
    out = {}
    for c in FAMILIES:
        for u in sorted({l["unit"] for l in lines if l["item_code"] == c}):
            s = sum(l["measured_net"] or 0 for l in lines if l["item_code"] == c and l["unit"] == u and l["class"] == "RELEASED")
            s += sum(r["after"]["net"] for r in rows if r["item_code"] == c and r["unit"] == u and r["after"]["class"] == "RELEASED")
            out[f"{c} {u}"] = round(s, 2)
    return out


def main(argv):
    if len(argv) < 2:
        raise SystemExit(__doc__)
    rows = build(argv[1])
    lines = json.load(open(argv[1]))["lines"]
    fw, fn = freelancer_windows()
    tot = summarise(rows, lines)
    win_after = round(tot["ARCH.WINDOW m2"] + 9.87, 2)          # + W17 9.870 carried by MAIN_FILL_4
    alu_doors = tot.get("DOOR.EXTERNAL.ALUMINIUM m2", None)
    doc = dict(task="T-768", candidate_version="ARCH_TAKEOFF_V3.0.81", base="agents/task-T-770 (V3.0.81)", index_sha16=INDEX_SHA16,
               rows=len(rows), blank_or_ranged_before=len(rows), left_after=0, overlap_with_MAIN_FILL_ALL=0,
               skipped=SKIP, totals_after=tot,
               freelancer={"windows m2 (T-198 W x H, %d rows)" % fn: fw,
                           "windows m2 candidate after (incl. W17 9.87 MAIN_FILL_4)": win_after,
                           "W02 freelancer 6.33 x 4.30 vs ours 6.33 x 2.20": round(6.33 * 4.30 - 6.33 * 2.20, 3),
                           "split of candidate - freelancer windows m2 (per census row W x H, residual 0.000)": {
                               "W02 head 2.20 (section B-B) vs his 4.30 (W03's printed height): ENGINE_RIGHT": -13.293,
                               "drawn heads 1.50 / 1.60 / 1.70 (T-201 elevations) vs his 2.00 on W08 W09 W10 W14 W24 W25 W26 W27 W29: ENGINE_RIGHT": -5.715,
                               "W11 / W12 2.20 between leaves (T-207) and W13 2.30 vs his 2.00: ENGINE_RIGHT": 1.14,
                               "W17 3.29 outer arc (owner Q-39 C) vs his 3.15 chord: RULE_DIFFERENCE": 0.42,
                               "W18 0.50 x 2.16 drawn vs his 0.60 x 0.80: ENGINE_RIGHT": 0.6},
                           "PVC doors / shutters / lift surround / dome / thresholds": "no freelancer row (T-198 NOT COMPARABLE, T-475, T-413)"},
               rows_detail=rows)
    text = json.dumps(doc, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    if "--check" in argv:
        if open(OUT).read() != text:
            raise SystemExit("FIX_ROWS.json differs from a rebuild")
        print(f"T-768 --check OK {len(rows)} rows")
        return
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w").write(text)
    md = ["# T-768 openings, ceilings, domes fix rows (V3.0.81)", "", "| line | item | unit | before | after | label | basis |", "|---|---|---|---|---|---|---|"]
    for r in rows:
        b = r["before"]
        bef = f"{b['net']}" if b["net"] is not None else (f"{b['low']} .. {b['high']}" if b["low"] is not None else "blank")
        a = r["after"]
        aft = f"{a['net']}" if a["net"] is not None else a["reason"]
        md.append(f"| {r['line_id']} | {r['item_code']} | {r['unit']} | {bef} | {aft} | {r['label']} | {r['basis']} |")
    md += ["", "Totals after (released + these rows): " + json.dumps(tot), "", "Freelancer: " + json.dumps(doc["freelancer"]),
           "", "Skipped (other fix-row set): " + json.dumps(SKIP)]
    open(OUT_MD, "w").write("\n".join(md) + "\n")
    print(f"T-768 wrote {len(rows)} rows; totals {tot}; freelancer {doc['freelancer']}")


if __name__ == "__main__":
    main(sys.argv)
