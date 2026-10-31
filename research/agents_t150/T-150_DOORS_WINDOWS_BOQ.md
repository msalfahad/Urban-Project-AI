# T-150: Alsenan doors and windows as BOQ lines, by hand (count, class, size, m2 per type and floor)

Worker 2, 2026-10-21 17:40 - 18:45 UTC. Lane A. NO REPO CODE: research files only (this folder); no engine module, rule,
knowledge version, key map, test or released quantity changed. Development villa (Alsenan), not an accuracy claim. No
client name, image, coordinate or personal data is committed; sheets are cited by Drive title and page; door elements
by the engine's own ids.

**Rework r2 (worker 2, 2026-10-22 05:50 - 06:40 UTC)** after the checker's rejection of 2026-10-22 04:05 (gate f +
WORKFLOW_CONTROLS s.8) and the Lead's four exact faults of 04:20. Only these changed; every width, printed height,
class and the eight measured windows are byte-for-byte the r1 values. Section 0 lists the changes; sections 2, 4, 5 and
7 are re-stated.

## 0. What r2 changed (and nothing else)

| # | Fault (Lead 04:20) | r1 | r2 | Effect |
|---|---|---|---|---|
| 1 | W16 kept as a quantity with a non-s.5 status | W16 1.55 x 3.10 = 4.805 m2 "INFERRED" (twin of W15); calc.py n_inferred / m2_inferred buckets | W16 **HELD on designer D-45**, width 1.55 m only, **no area**; the INFERRED status and both buckets are deleted; calc.py refuses any height status other than PRINTED / ASSUMED / HELD | windows: 8 measured 56.771 m2 unchanged; HELD 20 -> **21** (width 24.98 -> **26.53 m**); 4.805 m2 candidate removed |
| 2 | Main entrance not held after the render finding | D-GF-07 2.00 x 2.50 = 5.000 m2 DRAWING-CONFIRMED | **HELD**, cause T-161 F07c (renders show a single leaf; plan / SE print a 2.00 x 2.50 double), designer D-53; **5.000 m2 kept as the candidate only** (new column HOLD_CAUSE; calc.py puts a caused row in the held bucket with its candidate, never in a measured total) | main entrance confirmed 5.000 -> **0** + HELD candidate 5.000 m2 |
| 3 | Door-height verdict | 2.20 vs his 2.40 UNRESOLVED | 2.20 = **ASSUMED — OWNER-APPROVED** (Q-55 C / UP-DOOR-HGT-001), verdict **RULE_DIFFERENCE** on every door that has a freelancer row (D-GF-01, -03, -06, -09, D-2F-01); D-GF-05 stays UNRESOLVED (its class is HELD on Q-67 A / D-48) | no m2 change; ALU doors 10.560 m2 ASSUMED — OWNER-APPROVED |
| 4 | Scope verdict | PVC doors and the main door UNRESOLVED | **NOT COMPARABLE** (no freelancer supply line: scope of his workbook); the same verdict for the other rows with no freelancer row (gate, SX-01, SX-03, 2 arches, 3 lift candidates, U-01), whose own quantities stay HELD by their causes | no m2 change |

New guards in `calc.py --check` (one per fault): (1) an INFERRED height is refused (ValueError), and the made-up twin
S8 is HELD with no candidate; (2) a printed double door with a photo cause (S10, 1.80 x 2.40) is HELD with the
candidate 4.320 and, with the cause removed, returns to a confirmed 4.320, so the hold comes from the cause alone; (3)
a Q-55 C door against a freelancer 2.40 labelled UNRESOLVED is flagged; (4) a row with no freelancer line labelled
UNRESOLVED is flagged. The Alsenan run applies guards 3 and 4 to every row before it totals (exit 2 on a breach); the
table was mutation-tested (W16 set back to INFERRED -> refused; D-GF-01 back to UNRESOLVED -> refused; the D-GF-07
cause removed -> 5.000 confirmed, proving the hold is carried by the cause column).

Also recorded (no status change; both rows were already HELD): W02 gains the cause T-161 F23 (rendered as two windows
with a pier) and SX-01 the cause T-161 F09 (rendered as an arch over a low wall with a railing), both on designer D-53
as the Lead's register line says. D-GF-06 notes T-161 F22 (a render shows an arched head over a door on the +1.00
landing; identity PROBABLE only, not in the drawing): listed for the designer, its ASSUMED — OWNER-APPROVED 2.200 m2 not moved
(question for the Lead below).

Files: `OPENINGS_T150.csv` (one row per physical opening: 28 door elements, 29 windows, 2 pool-court wall openings,
2 leafless arches, 3 lift-shaft candidates, 1 unresolved census item = 65 rows; class, width + source, height + source,
material + source, wall, room on each side, engine id, earlier task reference, the freelancer's row, verdict),
`calc.py` (standard library; `python3 -I calc.py OPENINGS_T150.csv summary.json` reproduces every total below;
`python3 -I calc.py --check` runs the synthetic non-Alsenan fixture), `summary.json`.

Rules: UP-DOOR-CLS-001 .. 006, UP-DOOR-AREA-001, UP-DOOR-HGT-001 + owner Q-55 C (2.20 m only where every sheet is
silent, ASSUMED; main entrance printed 2.50), UP-DOOR-MIN-001 (DEPRECATED, not applied) / Q-04 (owner minimum view:
ordinary 1.00 nominal = 1.10 wall to wall, bathroom 0.90 = 1.00, drawn size when wider; a CONDITIONAL scenario, never
added to AS_DRAWN), UP-OPEN-SCHED-001 (no printed height: width kept, area HELD), UP-OPEN-CURVED-001 with owner Q-38 A /
Q-39 C, Q-32 A (arched: enclosing rectangle to the crown), Q-33 (windows aluminium by default), UP-QTY-STATUS-001 and
WORKFLOW_CONTROLS section 5 (evidence status per quantity, only the five s.5 statuses; HELD never 0) and section 8 (a
photo DIFFERS finding that affects a quantity holds the line; the drawing value stays as the candidate). Printed note N09
(work to stated dimensions, not to scale): nothing here is scaled off a print; widths are printed values or the DXF's
own jamb-to-jamb geometry.

## 1. What was read this run (Drive "Alsenan chalet project")

| Source | How | Used for |
|---|---|---|
| P7757_DXF_COMPRESSED.zip / P7757.dxf | ARCH_TAKEOFF_V2.9 run on it (working head 967d6d5, scratchpad output, exit 0): DOOR_SCHEDULE.json (28 door elements with both sides), ARCH_OPENINGS.json (60 band openings); door blocks and loose arcs read around the two unclear elements with ezdxf | door widths jamb to jamb, sides, wall thickness, block / leaf, window CAD widths |
| p7757_arch_sheet03 (GF plan) | 100 and 300 dpi renders; crops of the annex, the pantry / entrance landing, the stair / W.C. core and the pool corner | door classes (which side is outdoors), main entrance, the sea-side gate, the lift shaft symbol, printed widths 195 / 200 / 633 / 657 |
| p7757_arch_sheet04 (1F plan) | 100 dpi render | 1F door set (10, all interior), sea-side chain 49 / 155 / 109 / 101 / 50 |
| T-144 (agents/task-T-144 cf6b0c9, READY), T-083 (merged) | read, not copied | sills / heads / crowns of the 9 printed openings (incl. T-144's W14 / W17 corrections and W26 RFI-1 closure) |
| freelancer aluminium workbook ("الالومنيوم.xlsx", sheets "الغلاف" and "الكميات") | every row | comparison only: doors 12.0 m2, windows 116.9 m2 |

## 2. BOQ lines (house; site gate, lift candidates, leafless openings and the unresolved item listed apart) - r2

| Line | Floor | Count | Widths m | m2 DRAWING-CONFIRMED | m2 ASSUMED — OWNER-APPROVED (Q-55 C height 2.20) | HELD | Owner-minimum view (CONDITIONAL, never added) |
|---|---|---|---|---|---|---|---|
| DOOR.EXTERNAL.ALUMINIUM | GF | 4 | 1.00 + 0.90 + 1.00 + 0.90 | - | 8.360 | - | 9.680 |
| DOOR.EXTERNAL.ALUMINIUM | 2F | 1 | 1.00 | - | 2.200 | - | 2.420 |
| **ALU doors, house** | | **5** | **4.80** | **0** | **10.560** | 0 | 12.100 |
| DOOR.INTERNAL.PVC (2 internal + 6 bathroom) | GF | 8 | 6.80 (one of them 0.69 .. 0.80) | - | 13.200 (7) | 1: master bath door, width 0.69 .. 0.80, candidate 1.518 .. 1.760 | 18.040 |
| DOOR.INTERNAL.PVC (5 internal + 5 bathroom) | 1F | 10 | 8.70 | - | 19.140 | - | 23.100 |
| DOOR.INTERNAL.PVC (1 internal + 1 bathroom) | 2F | 2 | 1.70 | - | 3.740 | - | 4.620 |
| **PVC doors, house** | | **20** (12 bathroom, 8 internal) | 17.20 | **0** | **36.080** (19) | 1 (candidate 1.518 .. 1.760) | 45.760 |
| DOOR.MAIN_ENTRANCE (double, 2 leaves, 1 set) | GF | 1 | 2.00 printed | **0** (r1 5.000) | - | **1: candidate 5.000 (2.00 x 2.50 printed)**, cause T-161 F07c / D-53; material HELD (UP-DOOR-CLS-004) | not applied (CLS-004) |
| DOOR.CLASS_HELD (kitchen to the side passage) | GF | 1 | 1.00 | - | 2.200 (class HELD) | class HELD on Q-67 A's condition / D-48 | - |
| WINDOW.ALUMINIUM | GF | 12 | 24.40 | **30.651** (2: W01, W03) | - | 10 (16.63 m of width) | - |
| WINDOW.ALUMINIUM | 1F | 13 | 16.09 (W17 on its outer arc) | **24.080** (5: W13, W14, W15, W17, W18) | - | **8 (7.10 m of width, W16 included)** | - |
| WINDOW.ALUMINIUM | 2F | 4 | 4.00 | **2.040** (1: W26) | - | 3 (2.80 m) | - |
| **Windows, house** | | **29** | 44.49 | **56.771** (8) | - | **21 HELD (26.53 m of width), no area** | - |

House by evidence status (supply lines): DRAWING-CONFIRMED 56.771 m2 (8 windows); ASSUMED — OWNER-APPROVED 46.640 m2
(5 ALU doors 10.560 + 19 PVC doors 36.080; plus the class-held kitchen door 2.200 on the same height basis, listed
apart); HELD: 21 windows (26.53 m of width, no area), the main entrance (candidate 5.000 m2), the GF master bath door
(candidate 1.518 .. 1.760 m2). No HELD item counts as 0 or enters a measured total.

Per opening (sheet + reading) in `OPENINGS_T150.csv`. The eight measured windows: W01 1.20 x 2.00 = 2.400; W03 6.57 x
4.30 = 28.251 (Q-38 A); W13 1.20 x 2.30 = 2.760; W14 2.45 x 1.60 = 3.920; W15 1.55 x 3.10 = 4.805 (crown, Q-32 A); W17
3.29 x 3.50 = 11.515 (outer arc Q-39 C, crown Q-32 A); W18 0.50 x 2.16 = 1.080; W26 1.20 x 1.70 = 2.040 (crown).
Sum 56.771 m2. Every door except the main entrance carries the Q-55 C height 2.20, ASSUMED — OWNER-APPROVED: no plan,
elevation, section or schedule prints a door height (T-083 / T-144 census, re-checked on the elevations' chains), so no
ordinary door m2 is DRAWING-CONFIRMED. W16 is HELD with its width only: no chain passes through it, and being drawn as
W15's twin is not an Urban rule (D-45, RFI-3).

Other openings (not supply lines, kept so nothing is lost; all HELD):

| Row | What | Width | Why held |
|---|---|---|---|
| D-GF-15 | single-leaf gate in the sea-side frontage of the 1.50 m court strip beside the pool court (block D120, leaf 0.89) | not established | not a building door: no Urban class for a boundary / court gate; V2.9 finds no walls at its ends |
| SX-01 | 4.521 m opening in the east (sea-side) wall of the pool court, under CB1; ends on the door / window layer | 4.521 printed | filling (glazing / railing / open) and height not printed (T-154 finding; new to the opening census) |
| SX-03 | 1.00 m leafless doorway in the north wall of the pool court, under B24 | 1.000 CAD | no head printed; no door drawn: reveals and head soffit only |
| A-GF-01, A-1F-01 | leafless arches dewaneya / wash and 1F 380 x 430 bed room / dressing | 1.00 each | arch head not printed (D-45); finishes only |
| L-GF / 1F / 2F-01 | openings into the stacked 1.80 x 1.80 shaft drawn with the lift cross | 1.00 each | UP-DOOR-CLS-005: lift CANDIDATE (no lift word / schedule / block); EXCLUDED from door lines until confirmed |
| U-01 | "other glazing (plan) 0.93" on the open-room face in T-128 / T-144 | 0.93 | no engine opening, no W01-W29 window, no freelancer row: identity not established |

## 3. Against the released engine (ARCH_TAKEOFF_V2.9, same DXF, this run)

| Line | V2.9 | This package | What changed |
|---|---|---|---|
| ARCH.WINDOW | 27 pcs, 0 m2 (heights not read; area null on all 27) | 29 pcs; 56.771 m2 confirmed on 8; 21 held | +2 windows V2.9 misses (W03 curved pool glazing 6.57, W18 bath 0.50; T-040 G4 / G7); first window m2 |
| DOOR.EXTERNAL.ALUMINIUM | 2 pcs released (driver, roof), 3 more held as class review / width review | 5 pcs, 10.560 m2 ASSUMED — OWNER-APPROVED | diwaniya door (court side), pantry door (entrance landing) and stair-hall north door classed from the plan; driver-side 0.90 vs frame review kept AS_DRAWN |
| DOOR.INTERNAL.PVC | 15 pcs released, 5 held (provisional closures) | 20 pcs, 36.080 m2 ASSUMED — OWNER-APPROVED + 1 HELD (width range) | the 5 closure-derived doors bound to their rooms (all real doors, each with its own block except the GF master bath's loose arc) |
| DOOR.MAIN_ENTRANCE | held (2 candidates, MAIN_ENTRANCE_UNRESOLVED) | 1 set, HELD, candidate 5.000 m2 (r2: T-161 F07c) | bound to the double door at the top of the entrance steps (printed 200 x 250); the other "candidate" is the pantry's outside door |
| door / window m2 lines | none (T-040 G1) | per line above | the BOQ category now exists as hand lines for V3.0 (lane I) |

## 4. Against the freelancer (aluminium workbook; doors 12.0 m2 + windows 116.9 m2 = 128.9 m2)

| Item | This package | Freelancer, same openings | Difference | Verdict proposal |
|---|---|---|---|---|
| Windows, count | 29 | 29 (GF 12, 1F 13, 2F 4) | 0 | AGREE (both include W03 and W18, which V2.9 misses) |
| Windows m2, the 8 measured | **56.771** | 54.931 | **+1.840 m2 (+3.3 %)** | per window below |
| GF (W01, W03) | 30.651 | 30.651 | 0.000 (0.0 %) | AGREE |
| 1F (W13, W14, W15, W17, W18) | 24.080 | 21.880 | +2.200 (+10.1 %) | W13 +0.360 ENGINE_RIGHT (2.30 printed); W14 -0.980 ENGINE_RIGHT (1.60 printed); W15 +0.155 ENGINE_RIGHT (crown 3.10); W17 +2.065 RULE_DIFFERENCE (owner Q-39 C / Q-32 A vs his 3.15 x 3.00); W18 +0.600 ENGINE_RIGHT (0.50 x 2.16 printed vs his 0.60 x 0.80) |
| 2F (W26) | 2.040 | 2.400 | -0.360 (-15.0 %) | ENGINE_RIGHT (1.70 to the crown printed; his own finishes sheet also uses 1.70) |
| Windows m2, the other 21 | HELD (21, 26.53 m of width, no area; W16 included) | 61.969 m2 at flat 2.00 / 0.80 / 3.00 / 4.30 | not comparable | UNRESOLVED: no sheet prints their heights (designer D-45) |
| ALU doors, count | 5 (GF diwaniya, driver, pantry, stair north; 2F roof) + 1 class HELD (kitchen) | 5 (GF 4 x 1.00, roof 1 x 1.00) | 0 (+1 held) | AGREE on count if the side passage is not open-air; if it is (Q-67 A condition), the house has 6 |
| ALU doors, m2 | 10.560 ASSUMED — OWNER-APPROVED (widths 4.80 x 2.20); owner-minimum view 12.100 | 12.000 (1.00 x 2.40 each) | -1.440 (-12.0 %) AS_DRAWN; +0.100 (+0.8 %) owner view | widths: RULE_DIFFERENCE on the two 0.90 doors (AS_DRAWN vs the owner minimum 1.00); heights: **RULE_DIFFERENCE** (2.20 owner fallback Q-55 C vs his 2.40, printed nowhere; Q-55 forbids his 2.40 without evidence) |
| Main entrance | 1 set, HELD (candidate 5.000 m2, T-161 F07c / D-53) | not in his aluminium workbook | - | **NOT COMPARABLE** (no supply line in his workbook) |
| PVC doors | 20 sets, 36.080 m2 ASSUMED — OWNER-APPROVED + 1 HELD | no supply line (his plaster sheet only deducts 26 x 1.00 x 2.10) | - | **NOT COMPARABLE** (no supply line in his workbook) |

Aluminium total on the freelancer's basis: drawing-confirmed windows 56.771 + ALU doors 10.560 ASSUMED — OWNER-APPROVED =
67.331 m2 (each status kept apart), against his 128.9 m2 (unchanged by r2); the remaining 61.969 m2 of his rows sit on openings whose heights no sheet
prints. This is not a product accuracy figure.

## 5. Synthetic check (`calc.py --check`, not Alsenan): PASS (r2: 11 openings, 8 guards)

Eleven made-up openings with hand expectations: single PVC 0.90 on the Q-55 C height = 1.980 ASSUMED — OWNER-APPROVED
(owner view 2.420); double main entrance 1.60 x 2.40 printed = 3.840, one set; sliding glazed door given in millimetres
2400 x 2200 = 5.280 (owner view keeps the wider drawn size); window curved on plan (outer arc 2.80, chord 2.40) with an
arched head (crown 2.60, springing 2.20) = 7.280 against a chord x springing row 5.280; window with no height: width
kept, area HELD (not 0); bathroom 0.80 = 1.760 (owner view 2.200); width range 0.69 .. 0.80 -> HELD, candidate 1.518 ..
1.760; mirrored twin with no chain -> HELD, width only, no candidate; gate with no width HELD; printed double door 1.80 x
2.40 with a photo cause -> HELD, candidate 4.320; external door 1.00 on 2.20 vs a freelancer 1.00 x 2.40 -> 2.200
ASSUMED — OWNER-APPROVED, RULE_DIFFERENCE. Guards: no held opening becomes 0, no ASSUMED — OWNER-APPROVED area reaches the confirmed
total, a duplicate opening id is refused, every per-line total re-adds to the per-opening sums, and the four r2 guards
of section 0.

## 6. Learned

- The plan settles door classes the engine left in review: the diwaniya and stair-hall doors open onto the court, the
  pantry door onto the same +1.00 landing as the main entrance. The class rule needs which side is outdoors, and the
  plan shows it even where the engine's side detector reads UNKNOWN.
- The engine's "provisional" interior doors are real doors (each has its own door block); they are provisional only
  because the width came from a closure, not a jamb-to-jamb band. Only the GF master bath door (loose arc, no block)
  has a truly uncertain width.
- Door and window counts already agree with the freelancer (29 windows, 5 aluminium doors); the money difference is
  heights: he uses flat 2.00 / 0.80 / 2.40 where 8 windows print other values and no door prints any.
  (Superseded by T-198, T-389 note: agreement with the freelancer is not proof (ERS s.2.4); merged T-198 settles the
  windows from the drawing, W02 HELD, freelancer shown beside the range only: tests/t198_census_r3/test_alsenan_ledger.py:56.)
- The 28th engine door element is a gate in the site frontage, not a house door: a site-works item no Urban class names.
- (r2) A geometric twin is not evidence: only a printed chain, an answered owner decision or the rule library gives a
  height, and a status outside WORKFLOW_CONTROLS s.5 must be impossible in the tool, not only avoided in the table. A
  photo can hold a printed quantity (s.8) but never replaces it: the printed value stays visible as the candidate.

## 7. Missing / held

- 21 window heights incl. W16 and the 2 arch heads (designer D-45; RFI-3 for W16).
- Main entrance: one leaf or two, and its material (designer D-53; candidate 5.000 m2 kept).
- Every ordinary door height (D-07 door schedule; Q-55 C fallback used, ASSUMED — OWNER-APPROVED).
- Kitchen door class (Q-67 A condition / D-48); main entrance material; sea-side gate class and width; SX-01 filling and
  height; lift confirmation (UP-DOOR-CLS-005); U-01 identity.
- OQ-05 (which width the owner minimum applies to) stays open: the owner-minimum column is a scenario only.

## 8. Checker re-read (3 openings)

1. Door D-GF-06 (pantry): sheet03, the 1.00 door in the pantry wall opens onto the +1.00 landing at the top of the 280
   steps, the same landing as the double door "200"; V2.9 element DOOR-GF-3a056134 / OP-008, 1.000 jamb to jamb.
2. Window W14: SE elevation (Pages_05-06 p.6) chain 85 / 250 / 55 / 65 / 220 / 160 closing on 14.40; 2.45 x 1.60 = 3.920.
3. Curved W17: NW elevation (Pages_07-08 p.8) chain 430 / 20 / 305 / 45 from the +5.50 floor; outer arc 3.2895 (V2.9
   COP-001; owner example 3.29); 3.29 x 3.50 = 11.515.

## 9. For the Lead (r2)

D-GF-06 (pantry door onto the +1.00 landing, 1.00 x 2.20 = 2.200 m2 ASSUMED — OWNER-APPROVED): T-161 F22 records a render
showing an arched head with a blue reveal over a door on that landing, NOT IN THE DRAWING, identity PROBABLE only, and
T-161 (merged) moved no quantity for it. Strictly read, s.8 holds a line when a NOT IN THE DRAWING finding affects its
quantity; r2 leaves D-GF-06 unchanged because the Lead's 04:20 fault list names the main entrance only and the photo
cannot yet be tied to this door. If the Lead rules that F22 holds it, the change is one HOLD_CAUSE cell (ALU doors
10.560 -> 8.360 m2 ASSUMED — OWNER-APPROVED + 1 HELD, candidate 2.200).
