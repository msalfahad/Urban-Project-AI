# T-150: Alsenan doors and windows as BOQ lines, by hand (count, class, size, m2 per type and floor)

Worker 2, 2026-10-21 17:40 - 18:45 UTC. Lane A. NO REPO CODE: research files only (this folder); no engine module, rule,
knowledge version, key map, test or released quantity changed. Development villa (Alsenan), not an accuracy claim. No
client name, image, coordinate or personal data is committed; sheets are cited by Drive title and page; door elements
by the engine's own ids.

Files: `OPENINGS_T150.csv` (one row per physical opening: 28 door elements, 29 windows, 2 pool-court wall openings,
2 leafless arches, 3 lift-shaft candidates, 1 unresolved census item = 65 rows; class, width + source, height + source,
material + source, wall, room on each side, engine id, earlier task reference, the freelancer's row, verdict),
`calc.py` (standard library; `python3 -I calc.py OPENINGS_T150.csv summary.json` reproduces every total below;
`python3 -I calc.py --check` runs the synthetic non-Alsenan fixture), `summary.json`.

Rules: UP-DOOR-CLS-001 .. 006, UP-DOOR-AREA-001, UP-DOOR-HGT-001 + owner Q-55 C (2.20 m only where every sheet is
silent, ASSUMED; main entrance printed 2.50), UP-DOOR-MIN-001 (DEPRECATED, not applied) / Q-04 (owner minimum view:
ordinary 1.00 nominal = 1.10 wall to wall, bathroom 0.90 = 1.00, drawn size when wider; a CONDITIONAL scenario, never
added to AS_DRAWN), UP-OPEN-SCHED-001 (no printed height: width kept, area HELD), UP-OPEN-CURVED-001 with owner Q-38 A /
Q-39 C, Q-32 A (arched: enclosing rectangle to the crown), Q-33 (windows aluminium by default), Q-17 (INFERRED kept
apart), UP-QTY-STATUS-001 and WORKFLOW_CONTROLS section 5 (evidence status per quantity; HELD never 0). Printed note N09
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

## 2. BOQ lines (house; site gate, lift candidates, leafless openings and the unresolved item listed apart)

| Line | Floor | Count | Widths m | m2 DRAWING-CONFIRMED | m2 ASSUMED (Q-55 C height) | Held | Owner-minimum view (CONDITIONAL, never added) |
|---|---|---|---|---|---|---|---|
| DOOR.EXTERNAL.ALUMINIUM | GF | 4 | 1.00 + 0.90 + 1.00 + 0.90 | - | 8.360 | - | 9.680 |
| DOOR.EXTERNAL.ALUMINIUM | 2F | 1 | 1.00 | - | 2.200 | - | 2.420 |
| **ALU doors, house** | | **5** | **4.80** | **0** | **10.560** | 0 | 12.100 |
| DOOR.INTERNAL.PVC (2 internal + 6 bathroom) | GF | 8 | 6.80 (one of them 0.69 .. 0.80) | - | 13.200 (7) | master bath door: width 0.69 .. 0.80, ASSUMED range 1.518 .. 1.760 | 18.040 |
| DOOR.INTERNAL.PVC (5 internal + 5 bathroom) | 1F | 10 | 8.70 | - | 19.140 | - | 23.100 |
| DOOR.INTERNAL.PVC (1 internal + 1 bathroom) | 2F | 2 | 1.70 | - | 3.740 | - | 4.620 |
| **PVC doors, house** | | **20** (12 bathroom, 8 internal) | 17.20 | **0** | **36.080** + range 1.518 .. 1.760 | 1 width range | 45.760 |
| DOOR.MAIN_ENTRANCE (double, 2 leaves, 1 set) | GF | 1 | 2.00 printed | **5.000** (2.00 x 2.50 printed) | - | material HELD (UP-DOOR-CLS-004: no sheet prints it) | not applied (CLS-004) |
| DOOR.CLASS_HELD (kitchen to the side passage) | GF | 1 | 1.00 | - | 2.200 (class HELD) | class HELD on Q-67 A's condition / D-48 | - |
| WINDOW.ALUMINIUM | GF | 12 | 24.40 | **30.651** (2: W01, W03) | - | 10 (16.63 m of width) | - |
| WINDOW.ALUMINIUM | 1F | 13 | 16.09 (W17 on its outer arc) | **24.080** (5: W13, W14, W15, W17, W18) | - | 7 (5.55 m) + W16 INFERRED 4.805 | - |
| WINDOW.ALUMINIUM | 2F | 4 | 4.00 | **2.040** (1: W26) | - | 3 (2.80 m) | - |
| **Windows, house** | | **29** | 44.49 | **56.771** (8) | - | **20 HELD (24.98 m of width) + 1 INFERRED** | - |

Per opening (sheet + reading) in `OPENINGS_T150.csv`. The eight measured windows: W01 1.20 x 2.00 = 2.400; W03 6.57 x
4.30 = 28.251 (Q-38 A); W13 1.20 x 2.30 = 2.760; W14 2.45 x 1.60 = 3.920; W15 1.55 x 3.10 = 4.805 (crown, Q-32 A); W17
3.29 x 3.50 = 11.515 (outer arc Q-39 C, crown Q-32 A); W18 0.50 x 2.16 = 1.080; W26 1.20 x 1.70 = 2.040 (crown).
Sum 56.771 m2. Every door except the main entrance carries the Q-55 C height 2.20 ASSUMED: no plan, elevation, section
or schedule prints a door height (T-083 / T-144 census, re-checked on the elevations' chains), so no ordinary door m2 is
DRAWING-CONFIRMED.

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
| ARCH.WINDOW | 27 pcs, 0 m2 (heights not read; area null on all 27) | 29 pcs; 56.771 m2 confirmed on 8; 20 held; 1 inferred | +2 windows V2.9 misses (W03 curved pool glazing 6.57, W18 bath 0.50; T-040 G4 / G7); first window m2 |
| DOOR.EXTERNAL.ALUMINIUM | 2 pcs released (driver, roof), 3 more held as class review / width review | 5 pcs, 10.560 m2 ASSUMED | diwaniya door (court side), pantry door (entrance landing) and stair-hall north door classed from the plan; driver-side 0.90 vs frame review kept AS_DRAWN |
| DOOR.INTERNAL.PVC | 15 pcs released, 5 held (provisional closures) | 20 pcs, 36.080 m2 ASSUMED + 1 width range | the 5 closure-derived doors bound to their rooms (all real doors, each with its own block except the GF master bath's loose arc) |
| DOOR.MAIN_ENTRANCE | held (2 candidates, MAIN_ENTRANCE_UNRESOLVED) | 1 set, 5.000 m2 confirmed | bound to the double door at the top of the entrance steps (printed 200 x 250); the other "candidate" is the pantry's outside door |
| door / window m2 lines | none (T-040 G1) | per line above | the BOQ category now exists as hand lines for V3.0 (lane I) |

## 4. Against the freelancer (aluminium workbook; doors 12.0 m2 + windows 116.9 m2 = 128.9 m2)

| Item | This package | Freelancer, same openings | Difference | Verdict proposal |
|---|---|---|---|---|
| Windows, count | 29 | 29 (GF 12, 1F 13, 2F 4) | 0 | AGREE (both include W03 and W18, which V2.9 misses) |
| Windows m2, the 8 measured | **56.771** | 54.931 | **+1.840 m2 (+3.3 %)** | per window below |
| GF (W01, W03) | 30.651 | 30.651 | 0.000 (0.0 %) | AGREE |
| 1F (W13, W14, W15, W17, W18) | 24.080 | 21.880 | +2.200 (+10.1 %) | W13 +0.360 ENGINE_RIGHT (2.30 printed); W14 -0.980 ENGINE_RIGHT (1.60 printed); W15 +0.155 ENGINE_RIGHT (crown 3.10); W17 +2.065 RULE_DIFFERENCE (owner Q-39 C / Q-32 A vs his 3.15 x 3.00); W18 +0.600 ENGINE_RIGHT (0.50 x 2.16 printed vs his 0.60 x 0.80) |
| 2F (W26) | 2.040 | 2.400 | -0.360 (-15.0 %) | ENGINE_RIGHT (1.70 to the crown printed; his own finishes sheet also uses 1.70) |
| Windows m2, the other 21 | HELD (20, 24.98 m of width) + W16 INFERRED 4.805 | 61.969 m2 at flat 2.00 / 0.80 / 4.30 | not comparable | UNRESOLVED: no sheet prints their heights (designer D-45) |
| ALU doors, count | 5 (GF diwaniya, driver, pantry, stair north; 2F roof) + 1 class HELD (kitchen) | 5 (GF 4 x 1.00, roof 1 x 1.00) | 0 (+1 held) | AGREE on count if the side passage is not open-air; if it is (Q-67 A condition), the house has 6 |
| ALU doors, m2 | 10.560 ASSUMED (widths 4.80 x 2.20); owner-minimum view 12.100 | 12.000 (1.00 x 2.40 each) | -1.440 (-12.0 %) AS_DRAWN; +0.100 (+0.8 %) owner view | widths: RULE_DIFFERENCE on the two 0.90 doors (AS_DRAWN vs the owner minimum 1.00); heights: UNRESOLVED (2.20 Q-55 C vs his 2.40, neither printed; Q-55 forbids his 2.40 without evidence) |
| Main entrance | 1 set, 5.000 m2 | not in his aluminium workbook | - | UNRESOLVED scope (another trade or missing) |
| PVC doors | 20 sets, 36.080 m2 ASSUMED | no supply line (his plaster sheet only deducts 26 x 1.00 x 2.10) | - | UNRESOLVED scope: not in his BOQ |

Aluminium total on the freelancer's basis: drawing-confirmed windows 56.771 + ALU doors 10.560 ASSUMED = 67.331 m2
measured / assumed, against his 128.9 m2; the remaining 61.969 m2 of his rows sit on openings whose heights no sheet
prints. This is not a product accuracy figure.

## 5. Synthetic check (`calc.py --check`, not Alsenan): PASS

Nine made-up openings with hand expectations: single PVC 0.90 ASSUMED 1.980 (owner view 2.420); double main entrance
1.60 x 2.40 printed = 3.840, one set; sliding glazed door given in millimetres 2400 x 2200 = 5.280 (owner view keeps the
wider drawn size); window curved on plan (outer arc 2.80, chord 2.40) with an arched head (crown 2.60, springing 2.20) =
7.280 against a chord x springing row 5.280; window with no height: width kept, area HELD (not 0); bathroom 0.80 ASSUMED
1.760 (owner view 2.200); width range 0.69 .. 0.80 -> 1.518 .. 1.760; mirrored twin with an INFERRED height kept out of
the confirmed total; gate with no width HELD. Guards: no held opening becomes 0, no ASSUMED area reaches the confirmed
total, a duplicate opening id is refused, every per-line total re-adds to the per-opening sums.

## 6. Learned

- The plan settles door classes the engine left in review: the diwaniya and stair-hall doors open onto the court, the
  pantry door onto the same +1.00 landing as the main entrance. The class rule needs which side is outdoors, and the
  plan shows it even where the engine's side detector reads UNKNOWN.
- The engine's "provisional" interior doors are real doors (each has its own door block); they are provisional only
  because the width came from a closure, not a jamb-to-jamb band. Only the GF master bath door (loose arc, no block)
  has a truly uncertain width.
- Door and window counts already agree with the freelancer (29 windows, 5 aluminium doors); the money difference is
  heights: he uses flat 2.00 / 0.80 / 2.40 where 8 windows print other values and no door prints any.
- The 28th engine door element is a gate in the site frontage, not a house door: a site-works item no Urban class names.

## 7. Missing / held

- 20 window heights and the 2 arch heads (designer D-45); W16 twin (RFI-3).
- Every ordinary door height (D-07 door schedule; Q-55 C fallback used, ASSUMED).
- Kitchen door class (Q-67 A condition / D-48); main entrance material; sea-side gate class and width; SX-01 filling and
  height; lift confirmation (UP-DOOR-CLS-005); U-01 identity.
- OQ-05 (which width the owner minimum applies to) stays open: the owner-minimum column is a scenario only.

## 8. Checker re-read (3 openings)

1. Door D-GF-06 (pantry): sheet03, the 1.00 door in the pantry wall opens onto the +1.00 landing at the top of the 280
   steps, the same landing as the double door "200"; V2.9 element DOOR-GF-3a056134 / OP-008, 1.000 jamb to jamb.
2. Window W14: SE elevation (Pages_05-06 p.6) chain 85 / 250 / 55 / 65 / 220 / 160 closing on 14.40; 2.45 x 1.60 = 3.920.
3. Curved W17: NW elevation (Pages_07-08 p.8) chain 430 / 20 / 305 / 45 from the +5.50 floor; outer arc 3.2895 (V2.9
   COP-001; owner example 3.29); 3.29 x 3.50 = 11.515.
