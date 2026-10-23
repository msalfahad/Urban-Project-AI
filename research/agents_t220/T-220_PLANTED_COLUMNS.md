# T-220 Planted columns (P.C) and the released upper column lines with no member

Worker 1 (lane S), 2026-10-23, run started 15:23 UTC. Development villa, not an accuracy claim. ERS read; s.2 steps 1-5,
s.3 (one element, several geometries; a notation's meaning first; never the larger end), s.4 and s.7 applied. Files:
`research/agents_t220/*`, `tests/t220_planted_columns/*` only. No engine module, method version, route G, rule /
knowledge file, registry or released quantity changed. Sources (Drive "Alsenan chalet project"): 'ST7757 dxf.dxf'
(sha256 9f9d1179...38079, route G input), 'ST7757.pdf' p.4 / p.5 / p.6 (slab plans) and p.15 (details) at 300 dpi,
'Alsenan_Architectural_P7757_Pages_05-06.pdf' p.5 (2nd floor plan) and 'p7757_arch_sheet04.pdf' (1st floor plan) at
200 dpi. Committed: values, DXF handles and BOQ ids only (no coordinates, no images).

## 1. Result in engineering terms

Concrete, columns, Alsenan (m3). The released V2.9 + route G and V3.0.x have no line for the three planted columns; the
column reference ledger (T-119 r2, research, not released) has them as COL-1F-57 / -58 / COL-2F-59.

| Element | Section | Stands on (base) | Top | Physical solid (drawing-derived) | Owner method (T-119 rule) beside | Status |
|---|---|---|---|---|---|---|
| PC-1F-A (GFRS 329 -> FFRS 66A; T-119 COL-1F-57) | 0.20 x 0.70 AGREE (text 544 'P.C 20x70', both outlines) | B27 90x85, top +5.45 | 1F roof slab top +9.65 (B4, CB13, CB11 framing in are all billed net of it: the column owns the joint) | **0.14 x 4.20 = 0.588** | column 0.14 x (4.20 - 0.75 CB11) = 0.483 + joint 0.14 x 0.59 = 0.0826 + slab part 0.0224 = 0.588 | DRAWING-CONFIRMED, NOT RELEASED |
| PC-1F-B (GFRS 386 -> FFRS 69D; COL-1F-58) | 0.20 x 0.50 AGREE (text 548) | B26 65x85, top +5.45 | +9.65 (CB12 / CB11 net of it) | **0.10 x 4.20 = 0.420** | column <= 0.345 (D_ctrl >= 0.75: two unlabelled projections of unprinted depth touch it, D-26), joint >= 0.059 | solid DRAWING-CONFIRMED; owner split HELD (D-26) |
| PC-2F (FFRS 77B -> SFRS 778; COL-2F-59) | **CONFLICT 0.08 .. 0.10** (text 77C 'P.C 20x50' vs drawn 0.20 x 0.40 on both sheets, no dimension chain, no schedule row) | B19 40x75 (billed through it), top +9.65 | **soffit of B7 20x75**: B7 is billed THROUGH the column footprint (route G BAND0009 6.6 m, overlap 0.999), so B7 owns the joint; the roof structural top is HELD (D-39) | HELD; <= 0.10 x (13.90 - 0.75 - 9.65) = **0.350** | column 0.08 .. 0.10 x (4.20 - 0.75) = **0.276 .. 0.345**, joint 0 (B7 owns it) | HELD (section + roof datum) |

Against the carry in the row (T-217: 1.344 .. 1.428 m3 at the 4.20 m convention): 0.588 + 0.420 + 0.276 .. 0.345 =
**1.284 .. 1.353 m3** on the same interval, -0.060 .. -0.075 m3 = A x 0.75 of PC-2F inside B7 (already billed in the
B7 line). Freelancer: he prices columns by type at (interval - 0.75) (T-119), the planted columns inside his 1F / 2F
counts; no separate line to compare (not compared).

Missing scope closed in the ledger sense: each P.C now has an element record with its start / stop member, section
range, solid, owner split, ownership checks and status; the line itself is for lane I (V3.0 candidate), not released.

## 2. Physical element and evidence (ERS s.2.1-2.3)

- **What a P.C is on this set.** Legend p.3-p.6: hatched 'Planted column (P.C)'; on the slab plan of the storey BELOW,
  the column outline carries the ANSI35 pattern (it STARTS there), on its own storey's slab plan the outline is SOLID
  (T-217 s.2). ST7757.pdf p.15 'BEAM CARRYING PLANTED COL. DETAIL' (read at 300 dpi this run): the beam runs
  continuous under the column at full depth; the column bars go down into the beam and are bent at its bottom; the
  beam carries 4 ø16 extra and stirrups at 10 cm under the column; a 100 cm dimension runs from the beam top to the
  crank of the column bars. So the column concrete starts on the **beam top**; the beam keeps its full section under it.
- **Base level.** Beam top = the slab top of that floor: +5.45 (GF roof slab = 1F floor), +9.65 (1F roof slab = 2F floor),
  T-214 (MERGED b29060c2, DRAWING-CONFIRMED). The p.15 detail draws the slab flush with the beam top on both sides.
  Residual named: PC-1F-A stands where B27 separates the two sunken wet panels 280 / 287 (T-213); the top of a beam
  between two sunken panels is unprinted (T-213 s.4). The column sits on the B4 / B5 line whose south side is the normal
  slab, and p.15 draws one level; if the designer lowered B27 with the panels the base would drop by the unprinted d.
- **Top level.** 1F roof slab: one 0.16 plate on p.5 (FFRS), no step or sunken mark between the 2F interior and the
  +9.70 terrace bays where 66A / 69D stand (the 2F block on p.6 is the central core only; the architectural 2F plan p.5
  shows both positions on the +9.70 terrace). Top +9.65 on this one-plate reading, the same basis every released and
  ledger 1F column uses (T-214 s.4). 2F roof: finished +13.90, structural top HELD (D-39), so PC-2F is HELD with an
  upper bound only.
- **Who owns each junction (R-CONC-OWN-1, proposed T-189).** Overlap of the column footprint with each billed beam piece
  (route G overlays fitted to drawing metres, max error 0.0006 m; module `overlap_share`, stdlib):

| Junction | Reference beam register (T-110, merged) | Released route G | Result |
|---|---|---|---|
| B27 under PC-1F-A | BM-GF-048 one span 4.9505 x 0.90 x 0.85 = 3.7872 'P.C carried' (through) | BAND0048.1 / .2 overlap 0.000 / 0.000: the band is cut 0.521 m2 at the column (0.140 under it, 0.381 beside it) | reference PASS; route G **BEAM_LINE_SHORT** 0.14 x 0.85 = **0.119** under the column (+0.381 x 0.85 = 0.324 beside it): T-110's known one-span difference, not a column item |
| B26 under PC-1F-B | BM-GF-047 one span 3.9048 (through) | BAND0047.1 / .2 overlap 0.000 / 0.002; cut 0.142 m2 (0.100 under) | reference PASS; route G short **0.085** (+0.036 beside) |
| B19 under PC-2F | BM-1F-025 1.6012 | BAND0030.1 overlap 0.978 (DXF edges 6B1 / 6B2: 0.973; the orthogonal column overhangs the 6.9-degree beam by <= 21.5 mm at one corner, 0.0022 m2, over the slab at the same level) | PASS |
| B4 / CB13 / CB11 at the top of PC-1F-A | stop at its faces | overlap 0.000 / 0.001 / 0.000 | column owns the joint: PASS with the T-119 joint 0.0826 |
| CB12 / CB11 at the top of PC-1F-B | stop at its faces | 0.0011 / 0.0004 | PASS |
| **B7 over PC-2F** | BM-2F-011 0.20 x 6.6 x 0.75 = 0.990 | BAND0009 overlap **0.999** (lines 39A / 39B run through the column) | **DOUBLE 0.059 m3**: B7 bills the joint and T-119 COL-2F-59 also carries a joint 0.10 x 0.59 = 0.059; by R-CONC-OWN-1 B7 owns it; the column stops at the B7 soffit |

Side finding (not quantified, for the beam register): south of PC-2F the B7 band carries the 'Bearing wall (B.W)' hatch
(SFRS HATCH 391, S-HAT.BAT, 0.20 x 1.782 m; legend p.6); route G and T-110 bill that stretch as B7 20x75.

- **Bars.** Main bars ARE printed for all three (T-217 s.8 and D-46 said none for 329 / 386): GFRS 543 '10ø16' (PC-1F-A),
  547 '8ø16' (PC-1F-B), FFRS 77D '8ø16' (PC-2F). Links, anchorage and lap lengths are not printed (p.15 draws the bars
  bent in the beam and a 100 cm dimension to the crank, no link spacing): steel stays HELD; D-46 narrows to links and
  bar lengths. No kg computed (no approximate steel rate).

## 3. The five released lines on members their slab plan does not draw (2.268 m3)

| Released line | Storey | m3 | What is under / over the position | Searched (format) | Class |
|---|---|---|---|---|---|
| C3 on FP 10C5 | 2F | 0.420 | 1F column FFRS 68B ends under the 1F roof; no 2F roof slab there | DXF SFRS (no outline within 1.5 m: dome radials, boundary), PDF p.6 300 dpi at the member, architectural 2F plan (terrace, parapet) | NOT_DRAWN |
| C3 on FP 10E4 | 1F | 0.420 | GF column GFRS 383 under the GF roof; the position is 1.45 m outside the CB11 slab edge of the 1F roof | DXF FFRS (nothing), PDF p.5 300 dpi (outside the slab edge), architectural 1F plan (+5.50 terrace strip, parapet) | NOT_DRAWN |
| C3 on FP 10E4 | 2F | 0.420 | no 1F member either | DXF SFRS, PDF p.6, architectural 2F plan | NOT_DRAWN |
| C5 on FP 10BD | 2F | 0.420 | 1F column FFRS 685 | as 10C5 | NOT_DRAWN |
| C8 on FP 10E0 | 2F | 0.588 | 1F column FFRS 69A | DXF SFRS (2 entities in a 6 m window), PDF p.6 (building edge line only), architectural 2F plan | NOT_DRAWN |

Each released line is the schedule band of its type carried to a storey where the structural roof-slab plan of that
storey has no slab over the position (a column there would carry nothing) and the architectural plan of the storey
shows a terrace with a parapet. Class NOT_DRAWN = a consultant item (proposed D-65 kept), never a verified 0: the general
note on p.4-p.6 'CHECK ARCHITECTURAL DETAIL OF PARAPET BEFORE CASTING' leaves open a parapet stub, whose height is printed
nowhere. Verdict proposal: ENGINE_RIGHT for the candidate scope of T-126 (NOT_PRESENT, 2.268 m3 out); the released
V2.9 lines carry 2.268 m3 with no drawn member (a released-line defect for lane I, not a freelancer difference); the T-217 UNKNOWN is closed to NOT_DRAWN with the PDF
read at each member (the gap T-217 s.8 named).

## 4. CONC.COLUMN components still blocked (T-119 ledger, 59 columns)

Before: 27 / 59 HELD (10 HELD with D_ctrl settled, 6 framing depth open, 7 annex level Q-54 B, 2 C8 section D-16, 2 tank
B15 D-44). This task: COL-1F-57 stays DRAWING-CONFIRMED (both bases checked, solid = owner split); COL-1F-58 stays HELD
(D-26, solid now DRAWING-CONFIRMED 0.420); **COL-2F-59 moves to HELD** (section CONFLICT 0.08 .. 0.10, roof datum, and
its 0.059 joint is DOUBLE with B7). After: **28 / 59 HELD, 18 with the quantity open**. The T-217 26 section-conflict
member-storeys are not re-counted here.

## 5. Rule, module, tests

Rule proposal **R-PLANTED-COL-1** (any villa; provenance ST p.15 typical detail, R-CONC-OWN-1, R-SECTION-CONFLICT-1, owner
X6, URBAN-COLUMN-HEIGHT-TO-CONTROLLING-MEMBER@v1): a planted column starts on the TOP of the beam that carries it (never
the storey level below the beam, never the beam bottom); the supporting beam is billed through under it, and a beam line
cut at the column is SHORT by A x D (the beam keeps it); at the top the column runs to the slab top when every framing
member is billed net of it, and stops at the soffit of a member billed through it (that member owns the joint, so a
column-ledger joint is DOUBLE); the owner split (column to D_ctrl, joint, slab part) is reported beside the solid and must
re-add to it; a released storey line with no drawn member is NOT_DRAWN only after the storey's structural slab plan (both
formats, at the member) and its architectural plan were read, else UNKNOWN; it is never kept as built and never 0.
Adoption = a new rule version (Lead / lane I).

Module `planted_columns.py` (PLANTED_COLUMN_V1, stdlib, unwired): section sources by kind (AGREE / DRAFTING_NOTE only
with text AND dimensions / CONFLICT range / HELD), convex footprint-in-member overlap (rotation, mirror), base / top /
solid / upper bound, owner split, ownership results (PASS / BEAM_LINE_SHORT / DOUBLE / UNDETERMINED), `single_value`
(refuses held, range, unconfirmed), `check_claim` (refuses above-physical = full storey through the beam or the larger
end, and missing-as-0), existence classifier. `t220_alsenan_check.py` -> `summary.json`; `t220_extract.py` re-reads
every DXF fact and overlap for the Checker.

Tests `tests/t220_planted_columns` (22): synthetic Villa P (transfer beam TB1 0.40 x 0.90; normal 0.495 = 0.405 + 0.0675
+ 0.0225; adverse full storey through the beam 0.630 refused; beam cut at the column -> short 0.135, column unchanged;
beam billed through at the top -> top at its soffit, ledger joint DOUBLE; section 20x50 vs 20x40 -> 0.264 .. 0.330, ends
refused; drafting note only with text + dims; slab top missing -> HELD, bound 0.5025, 0 refused; drawn-only HELD; held
framing depth; m / cm / mm and unknown unit; rotation 0 / 30 / -47.5 deg, mirrored; partial overlap undetermined;
existence NOT_DRAWN / UNKNOWN / BUILT and convention-as-built refused) + the development villa (values above).

## 6. For the Checker (re-measure from the drawing)

1. PC-1F-A: GFRS outline 329 (ANSI35) 0.70 x 0.20, text 544 'P.C 20x70', 543 '10ø16'; FFRS 66A SOLID 0.70 x 0.20;
   B27 BM-GF-048 / route G BAND0048.1 / .2; top framing B4 BAND0002.1, CB13 BAND0024.1, CB11 BAND0027.1 (stop at the faces).
2. PC-2F: FFRS 77B (ANSI35, hatch 77A) 0.20 x 0.40, text 77C 'P.C 20x50', 77D '8ø16'; SFRS 778 (hatch 777 SOLID) on B7
   lines 39A / 39B (6.80 / 6.60 m, through the column); B19 edges 6B1 / 6B2; PDF p.5 'P.C 20x50 8ø16'.
3. One released line: C8 2F on FP 10E0 (0.588) on ST7757.pdf p.6 at the member and on the architectural 2F plan.
4. ST7757.pdf p.15 'BEAM CARRYING PLANTED COL. DETAIL'.
5. Re-run: `python3 -I research/agents_t220/t220_extract.py <ST7757 dxf> <bands.json>` (bands.json from
   `research/agents_t110/scripts/bands.py research/urban_engine_m4_correctness/st7757_route_g <out>`).

## 7. Lessons row (proposed)

| Date | Problem | Root cause | General rule (scope) | Regression test | Status |
|---|---|---|---|---|---|
| 2026-10-23 | Three planted columns had no line in any state, the 2F one sits under a beam billed through it (its ledger joint 0.059 m3 DOUBLE with B7), and the two 1F ones stand on beams the released route G cuts at the column (B27 / B26 short 0.119 / 0.085 m3 under them) | Route G takes every S-COL.BON outline as a column footprint (cuts the beam under a planted column) but reads columns only from the column plan, so the P.C gets neither a line nor the volume under it; the column ledger used the storey rule without checking which line bills each junction | A planted column starts on the top of its carrying beam (the beam is billed through under it); at the top it runs to the slab top only when every framing member is net of it, else to the soffit of the member billed through it; every junction gets one owner from the line bases, and the owner split must re-add to the solid (every villa) | tests/t220_planted_columns (adverse: full storey through the beam, the larger section end, a ledger joint under a through beam, a released convention line kept as built, missing as 0) | proposed |

## 8. Not done / uncertain

- Steel of the three P.C (links and bar lengths unprinted; D-46 narrowed); the B27 / B26 extra 4 ø16 and 10 cm stirrups
  of p.15 (beam steel, lane S later).
- Formwork of the three P.C (faces = perimeter x the solid height; follows once lane I takes the records).
- The B.W stretch of B7 (side finding).
- The 1F roof slab top at the terrace bays rests on the one-plate reading (same for every 1F column there); the 2F roof
  top stays HELD (D-39).
