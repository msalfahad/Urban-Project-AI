# T-260 Aluminium doors: class and opening-width evidence for the 4 held candidates (Alsenan; every villa)

Worker 1, 2026-10-24. Lane A row (lane S had no claimable TODO). Research only: new unwired module
`door_evidence.py` (DOOR_CLASS_WIDTH_EVIDENCE_V1, stdlib), values-only input, ledger, extractor, 3 test files. Nothing is
applied to any BOQ line; the released default (V2.9 + route G) and the candidate are unchanged. ERS read: s.2 steps 1-4,
s.3 (opening vs frame, notation before arithmetic), s.4 A/B/C, s.7 row proposed.

## 1. Result (engine candidate vs freelancer, aluminium doors, m2)

| | pcs | m2 | status |
|---|---|---|---|
| Candidate V3.0.10 / V3.0.11 before | 2 released + [1, 4] held | 4.180 released + 1.980 .. 8.800 HELD | line HELD |
| Settled here (for the Checker's ruling) | +4 | +8.580 (D-GF-01 2.200, D-GF-05 2.200, D-GF-06 2.200, D-GF-09 1.980) | class + width DRAWING-CONFIRMED, head ASSUMED - OWNER-APPROVED (Q-55 C) |
| Line if ruled | 6 | **12.760** | no aluminium door left held |
| Freelancer (ALU rows 14 + 51) | 5 | 12.000 (5 x 1.00 x 2.40) | |
| Difference | +1 | **+0.760 (+6.33 %)** | |

Reconciliation his -> ours (ERS s.2.4): heights 5 x 1.00 x (2.20 - 2.40) = -1.000 (RULE_DIFFERENCE: his 2.40 is printed
nowhere, owner Q-55 C 2.20); widths D-GF-03 and D-GF-09 drawn 0.90 jamb to jamb vs his 1.00: 2 x -0.10 x 2.20 = -0.440
(ENGINE_RIGHT on the drawn jambs, both faces); count: the drawing has 5 GF external doors (D-GF-01 / -03 / -05 / -06 / -09),
his GF row has 4: +1.00 x 2.20 = +2.200 (ENGINE_RIGHT on the count; which door his row omits is not identifiable from a
single 4-piece row: identity UNRESOLVED, quantity unaffected). Residual 0.000.

Other lines the same ruling moves (each class candidate was held from 0, T-232 rule 4): PVC GF held 4.554 .. 9.680 ->
4.554 .. 5.280 m2 (D-GF-05 / -06 leave it); MAIN ENTRANCE 5.000 .. 7.200 -> 5.000 m2 and 1 pc (D-GF-01 leaves it; D-GF-07
stays HELD on F07c / D-53). Cross-trade: the four widths equal the census T-198 (1.00 / 1.00 / 1.00 / 0.90), so the block,
plaster and paint deductions (T-175, T-228 GF-W10 at 0.90) do not change: nothing to flag.

## 2. Per door: physical element, evidence, ruling proposal

Source: Drive "Alsenan chalet project" / P7757_DXF_COMPRESSED.zip -> P7757.dxf (sha256 ab54dd55), p7757_arch_sheet03.pdf
(GF plan), Alsenan_Architectural_P7757_Pages_07-08 p.7 (SOUTH WEST ELEVATION). Width = gap between the collinear wall-face
line ends on BOTH faces, read in the door block's own frame (`t260_extract.py`; control D-GF-03 121 / 122 and 11D / 11E =
0.900 / 0.900 = Checker 02:44).

| Door | Physical element | Width (both faces) | Class evidence | Proposal |
|---|---|---|---|---|
| D-GF-01 | dewaneya (annex) -> open court, D120 insert 15E | 1.000 (10A / 10C court face, 138 / 139 room face) | court side: 'COURT' label block 193, level 394 '+0.15', nothing but the boundary-wall line 10F and a level marker to the plot line; UP-DOOR-CLS-002 lists 'diwaniya access from outdoors'. Main entrance? UP-DOOR-CLS-004 needs entrance evidence: none (no label, schedule or elevation mark; the only door of an annex room; a single D120 leaf like the ordinary doors); the house's entrance is D-GF-07 (D200 insert 281, double 2.00) on the +1.00 landing at the top of the outside steps. The engine's MAIN_ENTRANCE_CANDIDATE comes from exterior adjacency only (defect O-P8-01 family) | ALUMINIUM, 2.200 m2 |
| D-GF-05 | kitchen (annex, +0.30) -> side passage 1.20 x 4.70 (+0.15), D120 insert 192 | 1.000 (A3 / A2, A5 / A4) | Q-67 A (owner): external open-air IF the drawings confirm it is open to outside air without enclosing doors or glazing. Plan: nothing inside the 1.200 m court mouth band or the passage (extractor: `passage_mouth_band` [] and `passage_interior` []; the only lines are the two face lines 9F / A0 house side and A2 / A4 annex side); far end closed by the boundary wall 105 / 106 (two layer-5 lines 0.20 apart, T-109 CLOSED_BY_ELEMENT). Sheet03: no door, leaf, glazing or wall across the mouth. Second sheet, SW elevation p.7: the mouth between the annex end and the outside steps is a plain recess with one horizontal line (soffit edge), no leaf, frame, glazing or grille, while the doors on the same sheet are drawn with leaves and knobs and the screens with X bracing. Condition met -> exterior; the UP-DOOR-CLS-002 exception (kitchen door into an ENCLOSED interior corridor) does not apply | ALUMINIUM, 2.200 m2 |
| D-GF-06 | pantry (+1.00) -> entrance landing +1.00 at the top of the outside steps, D120 insert 33E (drawn on layer S-COL.BON) | 1.000 (15B / 15A, 159 / 158) | the step lines 30A / 30C / 30D start 0.059 m past the door jamb and run the 2.80 m flight width (DIMENSION A06 2800) down to the court; inside the steps + landing window only step lines and the arrow block AR1 373: no wall (layer 1), glazing (layer W) or door block across them; the only doors on the landing are this one and the main entrance 281. UP-DOOR-CLS-002 'pantry external access' | ALUMINIUM, 2.200 m2 |
| D-GF-09 | GF stair hall (+0.30) -> side court / side walk, D120 insert 3FF (layer S-COL.BON) | **0.900** (2B9 / 2B8 court face, 26F / 26E hall face; duplicate 2AC / 2AB identical) | class already DRAWING-CONFIRMED (census). The 1.00 is the D120 block frame, drawn overlapping the masonry ends by 0.047 / 0.053 m: a symbol, not the opening (ERS s.3; same reading as D-GF-03 0.90, released). No printed door-width dimension near it (DIMENSIONs 732 2500 / 73E 200 / 749 1350 are the hall and its walls) | width 0.90, 1.980 m2 |

Owner manual method vs drawing-derived method, side by side: the owner's QS schedule counts a door per drawn door and
takes width x 2.20 (Q-55 C) per door; the drawing-derived method takes the structural opening between the jambs on both
faces and the class from the side spaces under UP-DOOR-CLS-001 .. 005. They agree on all four doors (same widths, same
head); they differ only from the freelancer (heights, two widths, one count) as reconciled above.

Not needed for the class and left as it is: designer item D-48 (whether the passage's last 1.56 m2 is open to the sky or
under the GF roof-slab panel) affects the passage floor / soffit finishes, not the door class: the owner's Q-67 A
condition is about enclosing doors or glazing, and he answered it knowing the passage is roofed (Q-67 problem text).

## 3. General rule (any villa; proposed for lane I, DOOR_CLASS_WIDTH_EVIDENCE_V1)

R-DOOR-EVID-1: a held door is released only with (a) its opening read between the wall-face line ends on BOTH faces
(agree within 5 mm, else CONFLICT range; one face -> HELD; a block frame, leaf or fabrication frame is never the opening;
a second sheet that prints a different opening -> CONFLICT) and (b) its class from the side spaces: EXTERIOR only by
drawing evidence (exterior-coded space, nothing drawn to the plot line, an outdoor stair / landing reached with nothing
across, a passage whose mouth is open on the plan AND on a second sheet) or an owner decision; MAIN only with entrance
evidence (label, entrance sequence, schedule, elevation), never by exterior adjacency; an unknown side -> HELD, never PVC by
default; a freelancer row is never class evidence; a held area is None, never 0.

## 4. Tests

`tests/t260_alu_door_evidence/` (30): Villa C hand fixture (not Alsenan; 9 doors: main entrance by label, aluminium with
frame != jamb, adjacency-only candidate, open passage on two sheets, pantry into a glazed-closed corridor = PVC, open mouth
on one sheet only = HELD, no class note = HELD, faces 0.90 / 0.95 = CONFLICT 1.980 .. 2.090, plan 0.90 vs elevation 1.00 =
CONFLICT; line 5.940 m2 by hand); adverse: class from the freelancer refused, freelancer-only exterior = UNKNOWN, one-face
width HELD, block / elevation frame / leaf as the opening refused, held shown as 0 refused, exterior without evidence =
UNKNOWN, lift excluded; extractor on synthetic DXF: rotation 0 / 37 / 90, mirror, mm and m units give 0.900 / 0.900, faces
0.90 / 0.95 both reported, a missing face line gives None (never 0); Alsenan ledger pinned and reproduced byte for byte.

## 5. For the Checker (re-measure)

On P7757.dxf: the face-line ends of the four inserts (15E, 192, 33E, 3FF) on both faces (handles in section 2;
`python3 -I research/agents_t260/t260_extract.py <P7757.dxf>`); the passage mouth band (nothing drawn); sheet03 at the
passage mouth and the landing; Pages_07-08 p.7 at the passage mouth. Rule each door: class (D-GF-01 / -05 / -06), width
(D-GF-09).

## 6. Lessons row (proposed, ERS s.7)

| 2026-10-24 | Four drawn aluminium doors (8.580 m2) stayed held in the candidate although the census had their widths and the drawings decide their class (T-260) | The engine's class came from space typing (a dewaneya door to the court flagged a main-entrance candidate by exterior adjacency; a landing and a roofed passage typed UNKNOWN), and the Q-67 A condition was never tested on the drawings | A door's class is decided from its side spaces by drawing evidence (an open mouth needs the plan AND a second sheet), a main entrance only by entrance evidence; its width between the wall-face line ends on both faces (any villa) | tests/t260_alu_door_evidence (normal + adverse: adjacency-only main entrance, one-face width, frame as opening, freelancer class, held as 0) | PROPOSED |
