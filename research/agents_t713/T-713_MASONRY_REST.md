# T-713: MASONRY REST on ARCH_TAKEOFF_V3.0.70: every HELD masonry line by cause, the 7 parents by component, R-T713-1

Worker 2, 2026-11-11. Lane A research piece, non-candidate: `research/agents_t713/*`, `tests/t713_masonry_rest/*` only.
No engine, rule / rulebook / knowledge version, registry or candidate file changed; nothing wired or released. No
drawing, workbook, client name or coordinate here. Script: `bash scripts/agent_env.sh run --tree task-T-713
research/agents_t713/t713_masonry_rest.py [--json OUT] [--candidate <private V3_0_70_BOQ_LINES.json>]`, inputs
sha-pinned (V3.0.70 line index e8e001de, V3.0.68 index, T-696 census, T-449 r3 register, T-670, T-482, rulebook 1.1.0).

## 1. Physical element (ERS s.2.1)

A parent MAS.BLOCK line (`<floor>-WALLS:walls t=<t>`, no colour suffix) is the block face of the held walls / pieces of
that floor and thickness that no colour part line carries (the established parts moved to the part lines; T-488). Its
area is a SUM of components: an upper end exists only if EVERY component has one, a lower end only from components with
a drawn minimum. Its units / mortar / glue / perimeter lines are the materials of the same face: never firmer than it.

## 2. (a) Census on V3.0.70 (95 non-released MAS lines; MAS lines byte-identical to V3.0.68, asserted)

| Code | HELD blank | HELD bounded | N/A (EXCLUDED) | Cause of the HELD state |
|---|---|---|---|---|
| MAS.BLOCK | 15 | 0 | 0 | 7 parents (s.3), 6 2F roof-datum part hosts (D-39; T-696 AT_MOST beside), MAIN_S (AT_LEAST beside, T-696), ANNEX_S (s.5) |
| MAS.UNITS.BLACK | 12 | 1 | 0 | blank: follow their host; bounded L-1e61a4aa: HELD lintel face D-1F-09 in the dome piece (D-42) |
| MAS.UNITS.WHITE | 15 | 0 | 2 | 5 on valued hosts: NEEDS OWNER RULE (AAC face / count, Q-60); 10 follow their host |
| MAS.GLUE.AAC | 10 | 3 | 2 | bounded: HELD lintel faces in the host (W13 / W21-W23 / W25; W16 / W19 ..; D-GF-09, W05-W07): lintel lines held (DESIGNER_QUESTIONS row 2, T-704) |
| MAS.MORTAR.BLACK | 12 | 1 | 0 | as UNITS.BLACK |
| MAS.MORTAR.BLACK.LINTEL_BEARING | 0 | 6 | 0 | built bearing at FLAGGED_DEFICIT lintel ends (T-675 R-T675-2; row 2); D-1F-09 in the dome piece (D-42) |
| MAS.MORTAR.BLACK.PERIMETER | 12 | 4 | 0 | junction bands / range block ends (T-520, T-675; D-42, row 2); blank: follow their host |

Every line is in `out/T713_MASONRY_REST.json` (`census`, by line id, with its cause). The 4 N/A lines are the AAC lines
on MAIN_S / ANNEX_S (black by ST p.1 note 2, R-T675-1), already EXCLUDED on V3.0.70.

## 3. The 7 parents by component (register T-449 r3, T-482 corrections) and R-T713-1

| Parent (line) | Components | Blocking (no drawn upper end) | Result |
|---|---|---|---|
| 2F 0.15 (L-246f3c09) | 3 pieces of 2F-W03 under unlabelled members (D-04): 0.10 m (band BM-2F-016) + 0.20 + 0.20 m (junctions BM-2F-018 / -017 in the 0.40 B1 / B2 band) | none | **AT_MOST 1.965 m2** |
| 2F 0.20 (L-afe984a6) | 5 D-04 pieces (5.208 m, AT_MOST 22.064 m2), 2F-W00 lift wall, 2F-W02 shaft piece 2.50 m, 2F-W02 residual 0.097 m | opening L-2F-01 width not drawn; stair-shaft landing level (D-03 / A-A); residual location (method) | blank |
| 1F 0.20 (L-5ffa7157) | 1F-W04 D-04 piece 0.80 m (AT_MOST 0.8 x 4.20 = 3.36), 1F-W07 lift wall, 1F-W10 shaft piece 2.50 m | lift opening L-1F-01 width; shaft landing level | blank |
| 1F 0.15 (L-c22e3094) | 1F-W11 / W13 / W17 / W24 dome pieces 9.0075 m, 1F-W14+W15 / W16 | D-20 / D-42 wall tops in the dome openings; P-1F-01 / A-1F-01 widths; opening position (W11) | blank |
| GF 0.15 (L-0d9b9e89) | 4 DROP walls (W20 / W31 / W32 / W34: AT_MOST 29.410473 m2), annex pieces W23-W27 16.25 m, GF-W30 | annex datum (D-06 / D-17, owner Q-54 B HOLD); GF-W30 no band (method, T-125); A-GF-01 width | blank |
| GF 0.20 (L-4165954c) | 2 DROP walls (W12 / W16: 17.388626), annex pieces 31.39 m (W00 / W02 / W04 / W06 / W17 / W18 / W35), lift walls W08 / W09 / W13 / W14, W10 shaft 2.50 m, W03 'CB3 and' 2.64 m, W36 member face 0.50 m, W15, glazed / strip GF-H02, GF-W37 | annex datum; D-43 lift tie beam size; L-GF-01 / P-GF-01 / D-GF-07 widths; D-03; GF-H02 / W37 material-base-top (designer, T-228); W36 (method) | blank |
| GF 0.40 (L-ff06449b) | GF-H01 strip (0.60 m) | material / base / top not drawn (T-228 designer) | blank |

**R-T713-1 PARENT_ONE_END_V1** (research rule version, every villa; frozen producers untouched): DROP wall -> AT_MOST
U (d >= 0); a piece under a member whose depth is not printed -> AT_MOST L x (top of the plate above at its physical
maximum - top of the plate below, drawn - printed depth of the deeper KNOWN member it frames into); any other cause ->
no end. Parent AT_MOST = sum only when every component is bounded (rounded UP, R-T696-1); AT_LEAST only from positive
drawn minima; else blank with the blocking components named. Materials follow the parent (never firmer).

Hand check, 2F 0.15 parent (any reviewer): plate below FFRS top +9.65 (2F FFL +9.70, drawn 0.05; T-482 DRAWING-
CONFIRMED); roof +13.90 finished (A-A), structural 13.90 - b_r, b_r >= 0 (D-39) -> gap <= 4.25. West corner piece 0.10 x
4.25 = 0.425; the two junction pieces: soffit the deeper of the 0.40 B1 / B2 band and an unlabelled member, so the
wall top <= 13.90 - 0.40: 2 x 0.20 x 3.85 = 1.54. Sum **1.965 m2 AT_MOST** (lower end open). Colour is not split, so
each colour's material is at most the whole face: UNITS.BLACK L-318e6311 AT_MOST 1.965 x 12.5 = **24.5625 pcs**;
MORTAR.BLACK L-cdb8d543 1.965 x 0.0110625 = 0.0217378125 -> **0.021738 m3**; GLUE.AAC L-d6373b9f 1.965 x 3.5 =
**6.8775 kg**; UNITS.WHITE L-6d9df440 and PERIMETER L-c10db6d6 stay HELD blank (no AAC count rule; no piece ends).
These four figures go BESIDE their HELD blank lines (one-ended, never a range or a point, never 0) via a wiring row.

Why the six other parents stay blank (an open term opens the sum): every one holds at least one component whose drawn
geometry has no upper end. None is blocked by method gaps alone: GF-W30 / GF-W36 / 2F-W02 residual are method gaps
(team-fixable) but each shares its parent with a designer item. Upper ends the drawings DO give are recorded per
component (DROP 46.799099 m2 in all, D-04 pieces 27.389 m2) for the day the blockers clear.

## 4. Designer / owner items holding the masonry (for DESIGNER_QUESTIONS.md, per unit, never summed across units)

| Item | Components | Piece length m | Parents blocked |
|---|---|---|---|
| D-06 / D-17 annex roof datum (owner Q-54 B HOLD) + annex floor build-up | 19 | 47.64 (GF 0.15 16.25, GF 0.20 31.39) | GF 0.15, GF 0.20 + all their materials (10 lines) |
| D-20 / D-42 wall top inside the dome openings | 7 | 9.0075 | 1F 0.15 (+5) |
| opening widths not drawn (L-GF-01, P-GF-01, D-GF-07, A-GF-01, L-1F-01, P-1F-01, A-1F-01, L-2F-01): no D-id yet | 8 | - | GF 0.15, GF 0.20, 1F 0.15, 1F 0.20, 2F 0.20 |
| stair-shaft landing level (D-03 'B3 (With Stair)', A-A) | 3 | 7.50 | GF 0.20, 1F 0.20, 2F 0.20 |
| D-43 lift tie beam size | 4 | - | GF 0.20 |
| glazed line / strip material, base, top (GF-H01, GF-H02, GF-W37; T-228) | 3 | - | GF 0.40, GF 0.20 |
| D-03 'CB3 and' label (GF-W03) | 1 | 2.64 | GF 0.20 |
| D-41 sunken-panel drop (DROP walls; AT_MOST given) | 6 | - | none alone |
| D-04 unlabelled member depth (AT_MOST given) | 9 | 6.508 | none alone |
| D-39 roof datum (2F part hosts, T-696 AT_MOST) | - | - | 6 2F part hosts + 15 material lines |
| D-35 annex exterior ground-beam depth (ANNEX_S) | 1 run | 10.000 net | ANNEX_S + 3 black material lines |
| Q-60 AAC face / count rule (owner) | - | - | 5 UNITS.WHITE on valued hosts |

## 5. (c) ANNEX_S

Correction to the row text: ANNEX_S (block under the annex neighbour-side ground beam, T-407) is NOT held by the annex
roof datum: it is held by **D-35** (annex exterior beam depth; reading L soffit +-0.00, reading S prints no depth but its
three bar zones need more than 0.25 m, so the soffit is at most +-0.00 in both readings) together with the unprinted
formation (p.9 note 1 gives excavation >= 1.5 m only, Q-21 C). h = soffit - foundation top: soffit low end open (beam
depth unbounded) -> no AT_LEAST; foundation top low end open -> no AT_MOST. Run 10.000 m net of columns; the reading-L
figure 7.000 m2 (h >= 0.70) stays shown, not adopted. Its UNITS.BLACK / MORTAR.BLACK / PERIMETER stay blank with the same
cause (lesson T-698). The annex ROOF datum (D-06 / D-17) is what holds the 47.64 m of annex wall pieces in the GF
parents (s.4): m2 = 47.64 x h_annex, h_annex not printed.

## 6. Verdicts, freelancer, lesson

Freelancer: blockwork by m2 with his own 3.45 / 3.70 heights, no units / mortar / glue rows: no like-for-like for the
parent lines (RULE_DIFFERENCE, no %). Proposals: census ENGINE_RIGHT on every hold (each blank line has a named cause; no
bound invented); 2F 0.15 parent AT_MOST 1.965 m2 ENGINE_RIGHT as a one-ended bound, UNRESOLVED as a quantity (D-04,
D-39). Lesson row (ERS s.7, proposed): "a line that is a sum of components is bounded only when every component is;
name the open component instead of dropping the line (every villa; T-713)".

## 7. For the wiring row / held

- Wiring (Gate B, not here; after T-703): the 2F 0.15 parent AT_MOST 1.965 m2 and its 3 material AT_MOST figures beside
  their HELD blank lines; the 6 other parents and their 30 material lines blank with the blocking components named.
- HELD: annex datum, dome tops, opening widths, shaft landings, D-43, glazed strips, D-03, D-35, AAC count, waste.

## 8. Validation

`tests/t713_masonry_rest` (8): hand villa R (pieces 4.38 + 1.60 + drop 7.125 = 13.105 m2; units 163.8125; mortar
0.1449740625 -> 0.144975 UP; glue 45.8675; white / perimeter HELD); mirror order; open component blanks the parent and
every material; AT_LEAST parent -> AT_LEAST materials (30.0 pcs, 0.02655 m3), never a range; adverse (unclassified
cause, empty parent, DROP without U, mm as m, known member deeper than the storey, plate below not drawn, unknown floor,
missing glue rate); development-villa regression from merged files (counts, 2F 0.15 = 1.965 / 24.5625 / 0.021738 /
6.8775, six parents blank with blockers, GF-W34 U per T-482); tampered index refused; global decimal context untouched.
