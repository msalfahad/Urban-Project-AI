# T-252 CONC.BEAM ledger r2: oblique-carrier member ends and the GF void ring from its own drawn edges (Alsenan; every villa)

Worker 1 (lane S), 2026-10-24, run session_01DqwKa5WgwqQVRPFAreCNYW. Research piece, not wired: no engine, candidate or
released line changes; the merged T-241 files are untouched (r1 rows are carried and marked SUPERSEDED_R2, never edited).
Integration: lane I (T-247 takes r2, not r1) after the Checker's verdict. Development villa, not an accuracy claim.
Drawings named by Drive folder and title; entities by DXF handle; lengths, areas, volumes only.

## 0. Inputs (own, this task)

| Input (Drive "Alsenan chalet project") | sha256 | Read for |
|---|---|---|
| "ST7757 dxf.dxf" | 9f9d1179...38079 (= manifest) | GF roof slab sheet (ST p.4): B27 S-BEAM faces 325 / 326, member edges, the B7 ring arcs, the closing faces, S-COL.BON outlines; T-139 faces (`research/agents_t139/slab_faces.py`) and route G bands (`research/agents_t110/scripts/bands.py`, fit 0.6 mm) re-run on this copy |
| merged ledgers | committed | `research/agents_t241/LEDGER_T241.csv` (r1, 140 runs, 66.0161 m3), `research/agents_t234/LEDGER_T234.csv` (slab panels), freelancer cells (`tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json`, sheet 'كمرات') |

Files: `beam_ledger_r2.py` (BEAM_LEDGER_R2, stdlib rules: R-BEAM-END-OBLIQUE-2, R-BEAM-CURVED-AREA-2, ledger revision),
`t252_extract.py` (private DXF -> `ALSENAN_R2_INPUT.json`: handles, lengths, widths, areas; no coordinates),
`t252_alsenan_check.py` -> `LEDGER_T252.csv` (143 rows = 140 r1 carried incl. 6 SUPERSEDED_R2 + 3 r2 rows; 137 live),
`BY_MARK_T252.csv`, `summary.json`; tests `tests/t252_beam_ledger_r2` (41).

## 1. Correction (a): a member ending on an OBLIQUE carrier (B27 east face)

**Physical element.** B27 (90 x 85, ST p.10) runs obliquely across the GF roof between S-BEAM lines 326 (west face) and
325 (east face). Two members stop on its EAST face 325: CB4 span 1 (20 x 50, p.11; edges 288 / 285, from the south side
of column 362) and B4 BM-GF-017 (20 x 50, p.10; edges 27D / 282, from the B22 face 460). Each side face of the member
meets the oblique carrier face at its own point, so the run's plan is a trapezoid, not a rectangle to the nearer corner.
Both members are shallower than B27 (50 < 85), so they physically meet its face in 3-D (T-230).

**From first principles (own, DXF handles).** Each drawn edge ends ON line 325 (offset < 0.01 mm):

| Run | Edge lengths start face -> 325 (m) | Trapezoid plan (m2) | m3 at b 0.20 x D 0.50 | r1 billed | Delta |
|---|---|---|---|---|---|
| CB4 span 1 BM-GF-021#BAND0021.1 | 288: 2.37438, 285: 2.64537 (mean 2.50988) | 0.501975 | **0.250988** | 2.3744 m -> 0.2374 | **+0.013548** |
| B4 BM-GF-017#BAND0018 | 27D: 2.89066, 282: 3.03827 (mean 2.96446) | 0.592893 | **0.296446** | 2.8907 m -> 0.2891 | **+0.007376** |
| | | | | | **+0.020924 m3** |

Checker 02:02 own: 0.25099 / 0.29645 (+0.0209): agree to 0.00004 m3.

**Root cause.** The T-229 end check (`beam_support.classify_end`) measured the drawn-edge cover of each beam side BEYOND
the billed end. On a triangle the side at the apex has zero length beyond the face, its cover read 0 (< EDGE_NONE) and
the end was classed 'the drawn beam ends at the billed face' (census rows `GF,end 0,GF:BAND0018` and
`GF:BAND0021.1`, END_AT_BEAM PASS). On the WEST face the band ended square at the far corner, both sides had positive
cover and the triangle was added (B5 +0.0074). R2 measures each edge to the face: an apex edge is simply already there.

**Completeness scan (every oblique carrier, all three slab sheets).** Every pair of parallel layer-1 / S-BEAM edges
0.09 .. 0.95 m apart ending on one of the 15 oblique lines of the DXF, checked against the route G bands, the column
outlines and the T-229 additions: 10 pairs; 6 triangles already added by T-229 (GF B1 BAND0009 +0.0016, B11 BAND0001
+0.0034, B29 BAND0008 +0.0024, B4 BAND0010 +0.0016; 1F B1 BAND0008 +0.0011, B25 BAND0032 +0.0139), 1 covered by its
band (1F B6 on 6B2, 0.0006 m2 fit), 1 square pair on a non-slab sheet (no triangle), and **only the two runs above
uncorrected**. No other member in the line ends on one face of an oblique carrier.

## 2. Correction (b): the GF void ring B7 from its own drawn edges

**Physical element.** A B7 (20 x 75, ST p.10) ring beam round the pool-court void of the GF roof, four printed marks
46E / 46F / 470 / 471 around it. Its edges are two concentric pairs of drawn arcs: west 2EE / 2EF (R 1.935) with
2F0 (R 1.735), east 312 / 313 (R 1.750) with 310 / 311 (R 1.550): drawn width 0.200 on both = schedule b (two sources).
It is closed by the faces of the members that own the crossings: B8 face 46D, B17 face 42D, CB1 face 2A9, B7 face 437
(each closing piece checked to lie on its face line, < 3 mm); the void is bounded by 2F0, 318, 310, the CB1 face, 311,
317 (junction gaps <= 0.01 mm). The void touches the B8 face (tangent), the CB1 face (a segment), the B7 and B17 faces
(caps 317 / 318 tangent), so the ring is three pieces: west 0.39135, east-north (face GF-035) 0.14633, east-south
(GF-060) 0.12873 m2. No column outline lies in the ring (no column joint to deduct; T-229 joint list unchanged).

**From first principles.** Exact loop areas, arcs as arcs (shoelace of the piece ends + R^2/2 (theta - sin theta) per
arc): outer 4.356522 - void 3.690116 = **0.666406 m2** (densified-polygon cross-check 0.666408). x D 0.75 =
**0.499805 m3**. Checker 02:08 own 0.66676 m2 / 0.5001 m3: -0.00035 m2 (-0.05 %), within 1 %; cause not isolated (the
Checker's junction closure is not in the verdict text): named residual.

**Reconciliation, ring once (m2).** Route G bands inside the ring: B7 BAND0050 0.12295 + BAND0051 0.09480 (west) +
BAND0052 0.06943 (east-south) + BAND0053 0.08710 (east-north, route G 'UNBOUND', r1 HELD 'contested' D-04) = 0.37428;
**missed by the band set 0.29213 m2** (west 0.17360, east-north 0.05923, east-south 0.05930; Checker 0.29248). Other
beams' bands in the ring: B8 0.00178, CB1 0.00117, the straight B7 BAND0006 0.00047 = 0.00342 m2 (0.5 % of the ring,
band fit at the shared faces): named residual, not deducted. **Slab: the T-234 slab ledger bills none of the ring**
(faces GF-035 / GF-060 are T-139 class BEAM; the west crescent sits inside face GF-040 'OPENING+RING', which T-234
excludes as the pool-court void): the ring is counted once, by the beam (C1, R-CONC-OWN-1). Note for lane I: released A
bills 0.0322 m3 of the band-53 piece as SLAB (T-234 s.4); the integration that takes this ring row must drop that slab
piece in the same package (T-234's ledger already omits it).

Why r1 missed it: the west crescent's uncovered 0.1736 m2 lay inside the T-139 face GF-040, which merges the void with
the west crescent at the tangent pinch, so the T-241 partition counted it as 'opening' (its 'uncovered 3.85853' on
GF-040); only the east faces GF-035 / GF-060 were named (0.1171 m2 'short of the arc bands').

| Rows | r1 | r2 |
|---|---|---|
| BM-GF-050 / 051 / 052 (bands 50 / 51 / 52, CALCULATED) | 0.0924 + 0.0715 + 0.0523 = 0.2162 m3 | SUPERSEDED_R2 |
| BM-GF-060 (band 53, HELD D-04 'contested') | HELD 0.035 .. 0.105 | SUPERSEDED_R2 (inside the same ring between the same B7 edges: identified by the four B7 marks; no longer contested) |
| BM-GF-050.r2#RING-B7 | - | **0.499805 m3 CALCULATED** (+0.283605 measured; HELD range -0.035 .. -0.105) |

## 3. Line totals r1 -> r2 (m3; C1 stated on every side)

| Storey | r1 measured | r2 measured | Change, named causes (residual) | CONFLICT | HELD (never 0) | Freelancer | r2 - freelancer |
|---|---|---|---|---|---|---|---|
| GF roof | 39.026985 | **39.331525** | +0.304540 = CB4 span 1 +0.013548, B4 GF-017 +0.007376, ring B7 +0.283605; residual +0.000011 (r1 m3 rounded to 4 dp) | 3.9585 .. 4.6653 (unchanged) | 6 runs 0.909 .. 1.926 + 1 no value (was 7, 0.944 .. 2.031) | 42.8829 | -3.5514 (was -3.8559) |
| 1F roof | 22.690573 | 22.690573 | 0 | 1.1864 .. 1.4457 | 2.6567 .. 4.9552 + 2 | 17.0270 | +5.6636 |
| 2F roof | 4.2985 | 4.2985 | 0 | 0 | 0.562 .. 1.687 + 1 | 6.0560 | -1.7575 |
| **CONC.BEAM** | **66.016058** | **66.320598** | **+0.304540 (+0.46 %)** | **5.1448 .. 6.1110** | **4.1277 .. 8.5682** + 4 no value | **65.9659** | **+0.3547 (+0.54 %)** |

Released A 64.8196 (b96185d4, T-241 own run): r2 - released = +1.5010 = T-241's +1.1965 + this task's +0.3045.
Candidate V3.0.9a 65.2937 (merged package reports, not an own run): r2 - candidate = +1.0269.

**By storey and mark (only three marks move; BY_MARK_T252.csv):**

| GF mark | r1 (m3) | r2 | Freelancer (rows, length) | r2 - his | Reading |
|---|---|---|---|---|---|
| B4 | 2.1000 (6 runs) | 2.1073 | 2.1450 (5 rows, 21.45 m) | -0.0377 | his lengths run through the supports (T-241 RULE_DIFFERENCE) |
| CB4 | 0.5574 (2) | 0.5710 | 0.6550 (1 row, 6.55 m) | -0.0840 | his single 6.55 m through column 362 vs faces 2.510 + 3.200 = 5.710 m: RULE_DIFFERENCE (through-support length) |
| B7 | 0.9339 (4 live + HELD) | 1.2175 (4 live) | 1.5720 (2 rows: 3.10 m + 7.38 m) | -0.3545 | his 7.38 m row cannot be assigned to the ring or to the straight B7 runs from the sheet text (no location): UNRESOLVED per row; the ring is now measured from the drawing, not banded |

The +0.54 % against the freelancer total is still not agreement (T-241: his omitted labelled marks 9.883 offset by
through-support lengths); compared by storey and mark only.

## 4. Verdict proposals (Checker)

| Item | Proposal |
|---|---|
| CB4 span 1 0.250988, B4 GF-017 0.296446 | ENGINE_WRONG (released A and r1: short edge only, -0.020924 m3); DRAWING-CONFIRMED geometry, both edges on S-BEAM 325 |
| GF void ring B7 0.499805 | ENGINE_WRONG (route G bands under-cover the drawn ring by 0.29213 m2; released A bills 0.2161 m3 + 0.0322 as slab); DRAWING-CONFIRMED, widths two-sourced |
| freelancer GF B7 / CB4 / B4 | RULE_DIFFERENCE (through-support lengths) on CB4 / B4; UNRESOLVED per row on B7 (his 7.38 m row has no location) |

Checker re-measure list (handles on Drive "ST7757 dxf.dxf"): (1) edges 288 / 285 from the south side of S-COL.BON 362
to S-BEAM 325, and 27D / 282 from line 460 to 325 (both ends ON 325); (2) the ring: arcs 2EE / 2EF / 312 / 313 (outer),
2F0 / 318 / 310 / 311 / 317 (void), faces 46D / 42D / 2A9 / 437; exact area 0.666406 m2; (3) T-139 faces GF-035 /
GF-060 / GF-040 against LEDGER_T234 (none billed as slab). Re-run: `python3 -I research/agents_t139/slab_faces.py <dxf>
faces.json`, `python3 -I research/agents_t110/scripts/bands.py research/urban_engine_m4_correctness/st7757_route_g
bands.json`, `python3 -I research/agents_t252/t252_extract.py <dxf> faces.json bands.json`, `python3 -I
research/agents_t252/t252_alsenan_check.py`.

## 5. Rules, tests, lessons row (ERS s.4, s.7)

- **R-BEAM-END-OBLIQUE-2** (new rule version beside the T-229 end check; every villa; provenance Checker 02:02 + this
  task): a member that stops on the face of an oblique carrier is measured to that face on BOTH of its edges
  (trapezoid b (La + Lb) / 2), on either face of the carrier; a drawn edge that does not reach the face is refused
  (the end is not this rule's); a billed length equal to one edge while the edges differ is ONE_FACE_END (refused as a
  measure, corrected by (mean - billed) x b x D); any other difference is a MISMATCH, investigated, never corrected
  silently.
- **R-BEAM-CURVED-AREA-2** (every villa; provenance Checker 02:08 + this task): a curved member's plan area is taken
  between its own drawn edges, arcs as arcs, closed only by the faces of the members owning the crossings, less the
  void it surrounds; never chords or band pieces (refused); the drawn width of each arc pair is checked against the
  schedule; the ring is reconciled once: the slab ledger may hold none of it (refused), other beams' bands only fit
  slivers <= 1 % of the ring (named residual), the replaced bands never exceed it.
- Tests `tests/t252_beam_ledger_r2` (41): Villa Q (not Alsenan): a beam ending on the lower face of a 30-degree carrier
  (hand: La 4.000 / Lb 4.144338, plan 1.018042 m2, 0.610825 m3) and one on its upper face (3.653590 / 3.509252); units
  m / cm / mm x rotation 0 / 30 / -47.5 mirrored / 90 / 180 mirrored; adverse: one-face end (short or long edge)
  refused, unexplained length not corrected, an edge stopping short of the face refused, non-parallel edges, an edge
  parallel to the face, a width conflict; quarter ring R 1.25 / 1.00 = 0.441786 m2 (m / cm / mm, either loop sense),
  full annulus 2.387610 m2; adverse: ring given as chords refused (and shown short by 0.005029 m2), ring area also in
  the slab ledger refused, another beam's band in the ring refused above 1 %, bands exceeding the ring refused, open
  loop, inverted annulus, width conflict, void outside, unknown unit; ledger revision: r1 rows superseded never edited,
  a correction on a HELD run refused, a run twice refused, a HELD shown as 0 refused. Alsenan pinned: both one-face
  ends, ring 0.666406 / missed 0.29213 / slab 0, totals 66.320598, HELD 4.1277 .. 8.5682, r1 file untouched, only
  three marks move.
- **Lessons row** (the main chat's register already carries the Checker's proposal; this task's addition): 2026-10-24 |
  a curved ring beam banded as chords (0.3743 vs drawn 0.6664 m2) and two member ends closed on one face of an oblique
  carrier (CB4 / B4 on the B27 east face, 0.0209 m3) | (1) band polygons built from straight run axes; (2) the T-229
  end check measured edge cover beyond the billed end, which is zero on the apex side of a triangle; (3) the west
  crescent hid inside a T-139 face merged with the void at a tangent pinch, so the partition read it as opening | plan
  area between the member's own drawn edges, arcs as arcs; ends measured on each edge to the carrier face; a face that
  merges a void with a member at a tangent is split before it is classed (every villa) | tests/t252_beam_ledger_r2
  (quarter ring + 30-degree carrier both faces; adverse: chords, one-face end, ring also in slab) | PROPOSED (T-252).

## 6. Not done / uncertain

- The Checker's ring area is 0.00035 m2 larger than mine (0.05 %); its junction closure is not in the verdict text.
- The freelancer's GF B7 7.38 m row has no location in his sheet: not assigned to the ring (UNRESOLVED per row).
- Formwork and reinforcement of the changed runs (the ring's curved faces, the trapezoid ends): other tasks.
- Nothing is wired: lane I (T-247) takes r2 and must drop released A's 0.0322 m3 slab piece of band 53 with it.
