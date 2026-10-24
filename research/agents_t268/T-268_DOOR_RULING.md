# T-268: Doors (aluminium) m2 + pcs closed in the candidate from the Checker's T-260 rulings (ARCH_TAKEOFF_V3.0.13)

Integration package for Checker Gate B (lane I, worker 3). Integrates: T-260 (MERGED c6732efe, Verifier 2026-10-24
11:57 UTC, run session_01LG9LiytEf6dC9TntHiigNK, Gate A PASS a-h). Opt-in candidate only; NOT RELEASED; the released
default stays ARCH_TAKEOFF_V2.9 + route G. ERS 2026-10-22 read and applied (s.2.1 element, s.2.2 hierarchy, s.3, s.7).

## Physical element and the engineering question

A door = ONE structural opening between the masonry ends (wall-face line ends on BOTH faces; the D120 block frame,
the leaf and a fabrication frame are symbols), its class from the two side spaces (UP-DOOR-CLS-001 .. 006; a main
entrance only with entrance evidence), counted once and measured once: width x height, head 2.20 m only where no
sheet prints one (Q-55 C, ASSUMED - OWNER-APPROVED). V3.0.10 (T-232) held four drawn GF doors because the class (D-GF-01
ALU vs MAIN by adjacency; D-GF-05 / D-GF-06 ALU vs PVC) or the width (D-GF-09 0.90 .. 1.00) was open. The question
here: how does a ruled door leave every held line it sat in (each candidate class, both units) and enter ONE settled
class line, without a hand-built line, a double count or a lost door.

## Method (engine/source/arch_v3013.py, piece DOOR_RULING)

1. Reads the candidate's door lines (V3.0.10 opening policy) back into their per-opening tables and REGENERATES each
   from its own table with the V3.0.10 code: every one must be byte-identical (faithfulness check), so every line this
   version writes is the V3.0.10 line of the new membership.
2. Each ruling (inputs URBAN_V3013_INPUTS_V1) carries the door's full V3.0.10 opening record as the Checker ruled it
   (class, width VERIFIED with the checker run, height unchanged), the classes it is held in, and the census width the
   deductions carry. Refused: a door already settled, held-in classes that differ from the candidate, a door the
   candidate does not hold, two classes, a moved head, a width outside the held range without a why, a width != the
   census width without a downstream package named, a unit slip, declared totals that disagree, a tampered line.
3. Lines: unchanged membership byte-identical; changed membership REPLACED (same line id); emptied lines retired
   (NOT_APPLICABLE_WITH_EVIDENCE, figure kept); new groups ADDED. Same-openings rule (pcs ids = m2 ids per code)
   re-checked on the whole output; guard re-check (V3.0.7 inputs) run.

Owner manual method vs drawing-derived method, side by side: manual QS door schedule (per type and floor, number of
doors and width x height, 2.20 where no head printed, class by what the door opens onto) / the Checker's own
re-measure of the face-line ends on both faces at each insert and its plot of both side spaces (T-260 Gate A).

## Per-door ruling applied (the Checker's figures, not the worker's proposal)

| Door | Held in (V3.0.12) | Ruled class (status) | Width (status) | Height | m2 | Deduction change |
|---|---|---|---|---|---|---|
| D-GF-01 | ALU [0, 2.200], MAIN [0, 2.200] | ALUMINIUM (DRAWING-CONFIRMED: court to the plot line, no entrance evidence) | 1.000 both faces (VERIFIED) | 2.20 Q-55 C | 2.200 | none (= census 1.00) |
| D-GF-05 | ALU [0, 2.200], PVC [0, 2.200] | ALUMINIUM (DRAWING-CONFIRMED: passage open at its mouth on the plan + SW elevation, Q-67 A) | 1.000 (VERIFIED) | 2.20 Q-55 C | 2.200 | none |
| D-GF-06 | ALU [0, 2.200], PVC [0, 2.200] | ALUMINIUM (DRAWING-CONFIRMED: open +1.00 entrance landing) | 1.000 (VERIFIED) | 2.20 Q-55 C | 2.200 | none |
| D-GF-09 | ALU [1.980, 2.200] | ALUMINIUM (unchanged) | 0.900 both faces (VERIFIED; the 1.00 is the block frame) | 2.20 Q-55 C | 1.980 | none (= census 0.90, = T-228 GF-W10) |

## BOQ lines: before / after (Alsenan, Drive P7757.dxf sha ab54dd55 + ST7757 dxf 9f9d1179)

| Line (GF) | Released V2.9 | V3.0.12 | V3.0.13 | Evidence status after |
|---|---|---|---|---|
| ALU m2 settled | (no m2 line) | 1.980 (D-GF-03) | 10.560 (D-GF-01 / -03 / -05 / -06 / -09) | ASSUMED - OWNER-APPROVED (heads Q-55 C); widths VERIFIED, classes DRAWING-CONFIRMED |
| ALU pcs settled | (per-door pcs) | 1 | 5 | DRAWING-CONFIRMED count (Checker re-counted) |
| ALU m2 held | - | 1.980 .. 8.800 | retired (0 openings left) | - |
| ALU pcs held | - | 1 .. 4 | retired | - |
| PVC m2 held | - | 4.554 .. 9.680 | 4.554 .. 5.280 (D-GF-02 / -10 / -14 width review) | HELD |
| PVC pcs held | - | 3 .. 5 | 3 .. 3 | HELD |
| MAIN m2 held | - | 5.000 .. 7.200 | 5.000 .. 5.000 (D-GF-07, D-53) | HELD |
| MAIN pcs held | - | 1 .. 2 | 1 .. 1 | HELD |

Whole item, all floors: DOOR.EXTERNAL.ALUMINIUM 12.760 m2 / 6 pcs, nothing HELD (V3.0.12: 4.180 + HELD 1.980 .. 8.800,
2 + HELD 1 .. 4; released V2.9: 2 pcs, no m2). DOOR.INTERNAL.PVC 28.600 m2 / 15 pcs settled unchanged, HELD 8.030 ..
13.640 -> 8.030 .. 9.240, 5 .. 7 -> 5 .. 5 pcs. DOOR.MAIN_ENTRANCE HELD 5.000 .. 7.200 -> 5.000, 1 .. 2 -> 1 pcs.

Run identity: 3,663 lines -> 3,663 (8 replaced, 0 added), 3,655 byte-identical to V3.0.12 (asserted); V3.0.3 5ba4ae93,
V3.0.4 d86de34a, V3.0.11 bb5466b0, V3.0.12 8f80cf5d REPRODUCED (= T-240 WP1's figures); V3.0.13 BOQ csv 6be1bd4e (json
a41d7d75); runner chain = direct step (research/agents_t268/v3013_direct.py) byte-identical; same-openings ALU 6, PVC
20, MAIN 1, windows 29; guard re-check RUN, held_live_new [].

## Complete-line reconciliation (candidate doors line vs the Checker's per-door widths)

4.180 (D-GF-03 0.900 + D-2F-01 1.000, x 2.20; Checker 02:44) + 2.200 x 3 + 1.980 = 12.760 m2 = widths 4 x 1.000 + 2 x
0.900 = 5.800 m x 2.20; residual 0.000. Line status: PARTIALLY VERIFIED 2 / 3 components (pcs and widths VERIFIED by
the Checker, classes DRAWING-CONFIRMED, heights ASSUMED - OWNER-APPROVED Q-55 C: no sheet prints a door head), nothing
HELD. WHOLE VERIFIED it cannot be on assumed heads; that is the owner's approved fallback, shown, not hidden.

## Versus the freelancer (ALU rows 14 + 51: 5 x 1.00 x 2.40 = 12.000 m2)

Engine 12.760, +0.760 m2 (+6.33 %) = heads 5 x 1.00 x (2.20 - 2.40) = -1.000 RULE_DIFFERENCE (Q-55 C) + widths D-GF-03 /
D-GF-09 0.90 vs 1.00 = -0.440 ENGINE_RIGHT (both faces, Checker) + count 6 vs 5 = +2.200 ENGINE_RIGHT (5 drawn GF
exterior doors vs his 4; which door his row omits is not identifiable: identity UNRESOLVED, quantity unaffected);
residual 0.000. Pcs 6 vs 5 (+1, +20 %), ENGINE_RIGHT on the count.

## Downstream / cross-trade

All four ruled widths equal the census T-198 widths that the masonry / plaster / paint deductions already carry (T-175,
T-228 GF-W10 uses D-GF-09 0.90): no deduction change, nothing for T-261 / T-244, nothing applied twice. The PVC and
MAIN held lines shrink only by the doors that left them (no PVC / MAIN quantity released).

## Held / missing / waiting

D-GF-07 main entrance HELD 5.000 (designer D-53); PVC width reviews D-GF-02 / -10 / -14, D-1F-03 / -04 HELD; door heads
printed nowhere (Q-55 C stays). T-240 WP1 (unmerged, also V3.0.13 / BOQ_FAMILY_MASTER 1.8.0 on its branch) renumbers to
ARCH_TAKEOFF_V3.0.14 + master 1.9.0 on its next merge of the working head (its V3.0.12 base lines become this V3.0.13).

## Rule and lessons (ERS s.7, proposed)

General rule (any villa; R-DOOR-RULE-INT-1, provenance T-260 R-DOOR-EVID-1 + this package): a ruled door is integrated
by moving its opening record, never by editing a figure: it leaves every held line of every candidate class in both
units and enters the settled lines of one class, and the integration is refused unless the candidate lines regenerate
byte-identically from their own tables. Tests: tests/t268_door_ruling (K-268 hand fixture + adverse cases).
Lesson: the doors stayed held a whole day after their evidence was complete because a held opening sits in up to four
lines (2 classes x 2 units); closing it by re-deriving each line from its opening table keeps pcs and m2 on one
opening list and makes a partial move (one class or one unit forgotten) impossible.
