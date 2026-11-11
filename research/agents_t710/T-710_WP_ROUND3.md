# T-710 waterproofing round 3: census by cause, the D-41 sunken wet-room panels, the W.C. outlet datum

Worker 2, 2026-11-11 (lane A, research, unwired). Candidate ARCH_TAKEOFF_V3.0.70: its 160 FIN.WP.* / WP.* lines are
byte-identical to V3.0.66 (own check), so the T-685 census keys hold. Nothing wired or released; V2.9 + route G
unchanged; no engine module, rule / knowledge version, registry or frozen file touched. Rules R-T710-1 .. -3 in
`t710_rules.py`; builder `t710_alsenan.py` (`--check`); probe `t710_probe.py` (stages 1-5, own overlay); outputs
`out/T710_WP_ROUND3.{json,md}`; tests `tests/t710_wp_round3` (synthetic villa W710 + development villa pinned).
Drawings by Drive title only: "Alsenan chalet project" / P7757_DXF_COMPRESSED.zip -> P7757.dxf (sha256 ab54dd55) and
'ST7757 dxf.dxf' (sha256 9f9d1179), own decode this run.

## (a) Census: 58 = 53 HELD + 5 MISSING, one cause each (R-T710-3)

| cause | n | what it is |
|---|---|---|
| DESIGNER | 46 | 14 + 1 doorway transitions (Q-35 C detail not issued), 17 penetrations (W.C. outlet type), 3 terminations at openings (stop detail), 11 foundation lines (Q-21 C / Q-31 C / D-43 / product) |
| MEASURABLE_NOW | 8 | measured, waiting for wiring: pantry upturn 1.40 .. 1.90 m2, edge 4.50 lm, doorway 0.20 m2 + 1 pcs, pantry penetration 1 pcs (T-685 / T-691); pool-court ledge 0.639573 m2 + upturns 0.551614 / 0.500002 lm (T-522 / T-529, overlay only) |
| NEEDS_OWNER_RULE | 3 | 2F top roof membrane / upturn / rolls: Q-34 parked by the owner (not re-asked) |
| NO_PHYSICAL_ELEMENT | 1 | GF-RB28769 'termination other' 0 .. 0.004711 lm: the face is WALL (T-303 finding 5): proposed EXCLUDED with reason, never a 0 |

Every row names its drawing basis (out/T710_WP_ROUND3.md table a). No census row is MEASURABLE from the issued sheets
beyond the 8 already measured: the remaining 46 + 3 wait on the designer or Q-34.

## (b) The six suspended wet rooms and the sunken panels (D-41)

**Physical element (ERS s.2.1).** A 'Sunken slab.' panel is lowered at full thickness (T-213: 'T 16' printed for 280)
by an unprinted drop d. A membrane laid on the structural slab (a tray) lines the recess: plan area unchanged, plus
vertical faces = recess loop x d (the boundary of panel n room: along a wall face the upturn starts d lower; at a free
panel edge it is a step face). A membrane laid on the fill under the tile gains nothing. The membrane position is
printed nowhere (system HELD, UP-WP-MAT-001), so the low end is 0, never a choice.

**Own overlay.** ST 35C -> arch 2FAE (T-702 GF fit), then the arch plan-to-plan shifts found by column votes;
checked 18 of 27 ST columns -> 1F plan (worst 0.3 mm), 7 of 21 -> 2F plan (worst 0.1 mm). Each room cell by its four
face lines; door / window gaps read on the face walk.

| room | box (own) | floor own = engine | upturn run x 0.20 own = engine | panel cover | recess loop | d_max | extra WP HELD m2 |
|---|---|---|---|---|---|---|---|
| 1F-RED23B8 | 2.00 x 1.80 - column 0.0225 | 3.5775 | 6.80 -> 1.360 | 275: 93.1 % | 7.3121 | 0.24 | 0 .. 1.754904 |
| 1F-R52AC05 | 1.47 x 1.80 | 2.646 | 5.74 -> 1.148 | 276: 97.2 % | 6.4400 | 0.24 | 0 .. 1.545600 |
| 1F-R48AA46 | 2.05 x 2.45 | 5.0225 | 8.20 -> 1.640 | 280: 98.7 % | 8.7884 | 0.24 | 0 .. 2.109216 |
| 1F-R8BDA49 | 2.05 x 2.45 | 5.0225 | 8.20 -> 1.640 | 280 + 287: 49.9 % (B27 strip between) | 10.9625 | 0.24 | 0 .. 2.631000 |
| 1F-R48CDA5 | 2.25 x 2.10 | 4.725 | 7.90 -> 1.580 | 298: 87.0 % | 8.7952 | 0.34 | 0 .. 2.990368 |
| 2F-RE83BED | 1.85 x 3.00 | 5.55 | 8.90 -> 1.780 | 5BF: 97.3 % | 9.5998 | 0.24 | 0 .. 2.303952 |

Total recess loop 51.898 m; extra membrane HELD **0 .. 13.335 m2** (+0 .. +52.9 % on the released 25.214585 m2 wall
upturn; floor m2 unchanged). d_max = min boundary beam h - 0.16 (B1 / B2 / CB5 20 x 40 -> 0.24; 298 on B4 20 x 50
-> 0.34): a full-thickness panel cannot hang below the beams that carry it. Floors and upturns of all six rooms
re-measured by face line: AGREE to the digit (one 0.80 door each; windows above the upturn). The 1F laundry
(R26FA0D) has no panel.

**F-T710-1 (cross-trade).** Panels 280 / 287 run 0.40 m north past the twin cells' north wall into the dry cell
B3F / C1F / C29 / C24 (box 4.25 x 4.50): 0.5831 + 0.6419 = 1.225 m2 of sunken slab under a DRY room. Not waterproofing
scope (R-T710-1); its floor bed is d deeper there (HELD, floor-bed lane). Engine room id of that cell not bound here.

**F-T710-2.** 1F-R8BDA49 sits only half over panels: the 0.90 B27 strip (its top unprinted, T-213 s.4) crosses the
room between 280 and 287, so its floor has two recesses and 5.35 m of free step inside the room.

## (c) The 5 MISSING families (all GF-07 pantry, merged T-336 rows never wired)

| family | element | unit | printed? | value |
|---|---|---|---|---|
| FIN.WP.DOORWAY | floor piece through door D-GF-07 over the wall thickness | m2 | yes: gap 1.000 x wall 0.200 | 0.200 DRAWING-CONFIRMED |
| FIN.WP.DOORWAY_TRANSITION_NR | one transition per door | pcs | yes: D120 33E | 1 DRAWING-CONFIRMED |
| FIN.WP.DOORWAY_TRANSITION | the transition built to its detail | m2 | no detail issued | HELD (Q-35 C) |
| FIN.WP.TERMINATION | membrane edge on the open dining side | lm | box line yes (DIM 5E1 4500); stop by Q-37 A | 4.500 ASSUMED - OWNER-APPROVED |
| FIN.WP.PENETRATION | floor drain through the membrane | pcs | yes: 1 FD, no W.C. | 1 MEASURED |

## (d) Penetrations: 19 .. 31 pcs, datum the W.C. pan outlet

Settled only by a wet-room / W.C. installation detail or a fixture schedule giving the pan outlet; the issued
sanitary-7757 sheets are plans (no section, no trap detail). New evidence: all 6 W.C. rooms on suspended floors lie
over sunken panels and the only suspended wet room without a W.C. has none: consistent with floor-outlet pans drained
through the recess, NOT proof (a recess also serves the floor falls). High ends stay open; designer item, ERS s.2.7
not met (no owner question).

## Engine vs freelancer; who is right

No released quantity moved. Wet-room floors / upturns of the six suspended rooms: ENGINE_RIGHT on the flat geometry
(own re-measure AGREE); recess faces: ENGINE_OMISSION as a HELD component (0 .. 13.335 m2, D-41), not a released
error. Freelancer rows not re-read this run (T-321 note: workbook over the connector limit): UNRESOLVED vs freelancer.

## Lessons-register row (proposed, ERS s.7)

2026-11-11 | the wet-room membrane was measured flat at the FFL while every suspended W.C. room sits on a sunken panel
| the WP takeoff read the architectural plan only; the structural 'Sunken slab.' hatches were not laid over it | lay
the slab plan over every wet room; a recess adds loop x d of membrane when the tray is on the slab; d bounded by the
boundary beams (h - t), HELD while unprinted; a panel outside wet rooms is floor-bed scope (every villa) |
tests/t710_wp_round3 (normal: loop, d_max, printed d + tray; adverse: no upturn height HELD, unknown beam -> high
OPEN, mm as m, NaN / negative, panel outside the room, census count / cause / HELD-as-0) | PROPOSED.

## Not done / uncertain

- Hatch residuals of the own read vs T-213 (275 +0.0066, 276 +0.0323, 287 +0.0652, 298 +0.0020 m2: edge-path corners
  squared) reach no WP quantity (the in-room parts are used); the Checker may re-read 287 by loop.
- Membrane position, d, beam-top level over shared edges: D-41 (designer). Dry-cell room id: for lane I.
