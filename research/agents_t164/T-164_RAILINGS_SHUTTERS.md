# T-164 Railings / balustrades and shutters: every one the drawings show, as BOQ lines (development villa; any villa)

Worker 2 (lane A), 2026-10-22. Gate 1 (a missing BOQ category is a silent omission). NO REPO CODE: research files in
`research/agents_t164/` and the regression test `tests/t164_railings/` only; no engine, rule, knowledge, method or
registry file is touched; nothing is released. ERS read and applied (s.2.1 physical element first, s.2.2 evidence
hierarchy, s.2.3 first principles, s.2.4 reconciliation, s.3 physical vs payable, s.4 rule + test, s.7 lesson).
Rules: UP-STAIR-012 v2.0.0 (installed 3D path), UP-STAIR-013 v1.0.0 (wall handrail only where shown), UP-STAIR-014
PROPOSED (not applied), WORKFLOW_CONTROLS s.5 / s.8, owner Q-33 (windows aluminium; shutters are not windows: material
HELD), Q-65 C (fence), MISSION drawing-first. No image, client name, plot number or title-strip text is copied here.

## 0. What was read (Drive "Alsenan chalet project", read-only; private copies in .work/private, never committed)

| Source | How | Used for |
|---|---|---|
| P7757_DXF_COMPRESSED.zip (architectural DXF: GF, 1F, 2F plans + SE and NW elevations) | every railing-like entity dumped by layer and handle; regions plotted | plan bands, elevation rails, shutters, lengths |
| p7757_arch_sheet03 (GF), sheet04 (1F), Pages_05-06 (p.5 2F plan, p.6 SE), Pages_07-08 (p.7 SW, p.8 NW), sheet09 (NE), sheet10 (section A-A), Pages_11-12 (p.11 section B-B, p.12 FENCE PLAN / FENCE ELEVATION / SECTION) | rendered 150-400 dpi, read by eye (printed values only; nothing scaled) | heights printed, which faces carry railings, shutters |
| Freelancer: aluminium workbook (sheet "الكميات", 59 rows, all read) | openpyxl | no railing / shutter row |
| Freelancer: FIN workbook (floors / waterproofing / decor / railing, 23.6 MB) | NOT downloadable (connector limit about 6.2 MB); its cover-sheet value is taken from research/external_engine_lab/alsenan_phase_b1_recommendation.json ("railing 18.95 m", "internal railing") and alsenan_control_plane_01 ("typed constant") | reconciliation, labelled secondary |
| research/agents_t184 (MERGED, Checker-verified flights) | flight riser / going counts only (source references, ERS s.10.5) | stair pitch lines |

## 1. Result in engineering terms (railings, lm; shutters, pcs)

| Run | Where (physical) | Installed lm | Status | Height printed | Freelancer |
|---|---|---|---|---|---|
| RL-01 | 1F roof (+9.70), street (SE) edge 3.792 + court (SW) return 2.470, X railing on the low part of the wavy parapet | **6.262** | DRAWING-CONFIRMED (plan bands 12C8, 12A8/12A9; SE p.6 and SW p.7 draw it; DXF SE top rail 3.753) | 1.04 (SE '104', coping line to rail top) | no row |
| RL-02 | 1F roof, sea (NW) edge | **4.921** | DRAWING-CONFIRMED (plan band 1322/1323 = DXF NW top rail 279F, 4.921 both: 0.000 m) | 1.10 (NW '110', +9.70 to rail top) | no row |
| RL-03 | annex (dewaneya) roof (+4.30): street face 4.942 + court face 3.025 | **7.967** | DRAWING-CONFIRMED (1F plan bands B2D/B2E, B27/B28; p.12 FENCE ELEVATION, p.7 SW, p.9 NE draw it) | not printed | no row |
| RL-05 | ST-02 round stair, inner balustrade from the volute (0.811) round the curved + straight flights (6.632, 22 goings per tread), corner landing (0.050), short flight RS-A (1.361), then the 1F void edge as a gallery guard (1.625 + 5.845) | **16.324** | DRAWING-CONFIRMED (one continuous 50 mm band on layer 5, 1F plan; GF plan draws the stair part) | not printed | see s.4 |
| RL-06 | 1F living floor edge beside RS-A and the corner landing (designer item D-23) | **2.400** | DRAWING-CONFIRMED (AF5/AF6, same band graphic as RL-05; GF plan shows it overhead on layer 2) | not printed | see s.4 |
| RL-08 | ST-01b lobby flight D1 (+0.30 -> +1.00), one rail | **1.042** | DRAWING-CONFIRMED (section A-A draws it; second side not drawn, not added) | not printed | see s.4 |
| **Drawing-confirmed total** | | **38.916 lm** | | | |
| RL-07 | ST-01 dog-leg, inner side of each flight: MS1-L 3.089, MS1-U 3.775, MS2-L 3.782, MS2-U 3.782, well-end turns 0.200 + 0.200, 2F floor-edge guard 1.325 | 16.153 measured | **HELD** on two parts: the MS1-T winder turn (5 risers, 0.833 m rise, path round the 0.10 m well not dimensioned) and the MS1-LD turn | not printed (A-A draws the balustrade, no dimension) | see s.4 |
| RL-04 | GF roof strip (+5.50) in front of the sea French windows W15 / W16 | 6.127 (plan band) | **HELD**: the NW elevation draws two end piers and NO infill between them, the plan draws a 50 mm band: plan and elevation disagree on what stands on this edge; T-162 counts a +5.50 -> +6.00 parapet chain here | not printed | no row |
| RL-09 | ST-02 outer 50 mm band (r 2.730 / 2.780) | plan 4.035 .. 4.455 | **UNKNOWN** (guard or string: whether the corner outside the curve is filled is not drawn) | - | - |
| RL-10 | street fence, X railing in the wall's dip (p.12) | none | **HELD** (length not printed; p.12 is not in the DXF; never scaled) | - | - |
| RL-11 | entrance stair ST-03 (+0.15 -> +1.00, 0.85 m rise) and its +1.00 landing edge | none | **HELD**: open edges with NO guard drawn (render T-161 F04 shows a balustrade): designer item, never 0 | - | - |
| RL-12 | wall sides of ST-01 / ST-02 | - | EXCLUDED: WALL_HANDRAIL_NOT_SPECIFIED (UP-STAIR-013) | - | - |

Held measured parts (not in the confirmed total): 22.281 lm (RL-04 6.127 + RL-07 16.153). Plan projection of RL-05 would
be 15.118 lm against the installed 16.324 (-1.206 lm, -7.4 %): UP-STAIR-012 never bills the plan.

**Shutters (louvred, a pair per window):** W14 (1F street, SE p.6 + DXF): 2 leaves, each 0.639 / 0.624 x 1.599 m
outline, louvre panel 0.511 x 1.599 m (window printed 2.45 x 1.40); W11 and W12 (dewaneya street face, p.12 FENCE
ELEVATION): 2 leaves each, size not printed. **6 leaves DRAWING-CONFIRMED (count).** m2 HELD: no owner rule sets the
shutter basis (panel, leaf outline or opening; BOQ family B6-05 NOT_IMPLEMENTED); material HELD (Q-33 covers windows,
not shutters). Not drawn: W02 (rendered with shutters, T-161 F23), W15 / W16 / W17 / W18 / W01 / W13 / W26.

## 2. How each run was established (physical element first, ERS s.2.1)

- The architect draws every railing in plan as a 50 mm band (two parallel lines) on layer 5: inside the parapet line on
  the roofs (RL-01..03), along the inner edge of the stairs and round the void (RL-05 / -07), and at a floor edge
  (RL-06). The elevations draw the same runs as X-braced railings (top rail, mid rail, posts) above the low part of the
  wavy parapets; section A-A draws a top and mid rail on every ST-01 flight and on D1. Where plan and elevation both
  exist they agree: NW 4.921 = 4.921 m; SE street 3.792 (plan, to the corner centre) vs 3.753 (elevation top rail, to
  the corner post face).
- Length = band centreline, corners once (the two lines of a band differ by the band width at a corner: their mean).
- Stairs (UP-STAIR-012): ST-01 flights by the nosing pitch line H = (n-1) g, V = (n-1) r from the merged T-184 counts
  (the plan bands, 3.30 m per flight on 1F and 2F, confirm the extent); ST-02 per tread along the band centreline
  r = 1.5555 m: each riser line of the DXF intersected with the rail circle, sum of sqrt(h_i^2 + r^2), r = 0.160714 m
  (28 risers / 4.50 m, T-184); single-segment formula as a check 6.634 vs 6.632 m.
- Rail height never enters a length (UP-STAIR-012); printed heights are reported for the specification only.

## 3. Render findings of T-161 against the drawings (one row each; s.8)

| T-161 | Render | Drawing (this census) | Status now | BOQ line |
|---|---|---|---|---|
| F13 roof railings, 1F roofs | X railing on the wavy parapets | SE p.6, NW p.8, SW p.7 + plan bands | AGREES | RL-01, RL-02 |
| F13 dewaneya roof | wavy parapet + X railing on the street face and court corner | **p.12 FENCE ELEVATION draws the dewaneya street face with the X railing; 1F plan bands; p.7 / p.9** | **AGREES (T-161 said DIFFERS: p.12 was not read)** | RL-03 |
| F05 street fence | low planter wall + X railing + round-topped number pier | **p.12 FENCE ELEVATION draws exactly this: a low wavy wall with an X railing in the dip and a rounded end carrying the house number; FENCE PLAN 580 + 250; SECTION 265 (50 + 215)** | **AGREES (T-161 said TYPE DIFFERS / pier NOT IN THE DRAWING)** | RL-10 HELD (length); fence block is lane A Q-65 |
| F15 shutters | a pair on most windows | W14 (p.6) and **W11 / W12 (p.12)** drawn; W02 and the rest not | AGREES W14, W11, W12 (T-161 said W11 / W12 NOT IN THE DRAWING); NOT IN THE DRAWING W02 and others | shutters 6 leaves; W02 none |
| F04 porch | raised terrace behind a turned-baluster balustrade | no railing on the porch or the entrance flight | NOT IN THE DRAWING | RL-11 HELD (open edges, designer) |
| F09 pool-court sea front SX-01 | low curved wall + X railing across the pool | none drawn | NOT IN THE DRAWING | none (SX-01 stays HELD, D-53) |
| stairs (I02-I05 views) | not visible in renders | ST-01, ST-01b, ST-02 balustrades drawn | NOT VISIBLE | RL-05 .. RL-08 |

## 4. Reconciliation with the freelancer (units first, ERS s.2.4)

- Freelancer: one row "internal railing" 18.95 lm, a typed constant on the cover sheet of his FIN workbook (no formula,
  no breakdown; per the research record; the workbook itself is over the connector limit and was not re-read this run).
  No roof, balcony, fence or entrance railing and no shutter row in any workbook read (aluminium workbook: 59 rows, none).
- Ours, interior (stairs + void): RL-05 16.324 + RL-06 2.400 + RL-08 1.042 confirmed (19.766) + RL-07 16.153 measured
  and two turns HELD = 35.919 lm + held. Against 18.95: +16.969 lm (+89.5 %) on the measured part.
- Scope reconciliation (what his 18.95 could be, each a candidate, none proven): ST-02 system + D-23 = 18.724 (-0.226);
  ST-01 measured + D1 = 17.195 (-1.755); the old V3b S-RAIL convention 19.124 (flight slope + landing edge per flight). His single number cannot cover BOTH
  staircases: two drawn balustraded stairs plus the 1F gallery give 35.9 m or more. **Residual unexplained: which
  stair(s) his 18.95 m is.**
- Roof and terrace railings: 19.150 lm confirmed (RL-01 6.262 + RL-02 4.921 + RL-03 7.967) + RL-04 6.127 HELD, no
  freelancer row.

Verdict proposals for the Checker: RL-01 / RL-02 / RL-03 HAND_FOUND (drawn, no freelancer row; ENGINE_RIGHT on scope
once wired); interior railings UNRESOLVED on his scope (single typed constant), own figure by UP-STAIR-012 from the
drawing; shutters HAND_FOUND (6 leaves, no freelancer row; m2 HELD).

## 5. Cross-trade findings for the Lead (element register; no quantity of another task changed)

1. RL-04 vs T-162 GF parapet chain (+5.50 -> +6.00, 27.970 / 28.770 m): the sea edge of the GF roof strip (6.127 m band)
   is drawn as a railing band in plan and as end piers with no infill on the NW elevation; a 0.50 m solid parapet there
   would hide the bottom of the French windows W15 / W16, which the elevation draws down to +5.50. Owner trade for this
   edge: open (railing vs parapet); proposal: Lead names it in the register; designer item (what stands on the edge).
2. Street fence (Q-65, blockwork lane): p.12 prints 580 solid + 250 gate = 8.30 m, and the GF DXF draws the fence line
   10F 8.300 m (gate part dashed 2.500 m); Q-65 recorded 5.70 + 2.50 = 8.20 m "subject to verification": the drawing
   gives 5.80 m solid (+0.10 m). p.12 SECTION prints the fence height 265 (50 + 215), which T-161 / Q-65 had as not
   printed. Not changed here (Q-65 owner's geometry line); for the fence owner task.
3. The 0.200 m projecting outline outside the 1F SE face (register row, checker 04:05): layer D lines B3C + B3D and
   layer 5 C49 across W14, 0.200 m outside the 1F street wall over the whole 7.500 m face. It is NOT a railing base and
   NOT a shutter box (the shutters are drawn on the elevation as two 0.64 m leaves beside W14 only; the outline runs the
   full face, and the SE elevation draws the 1F face as one panel with a rounded lower corner). Classification: a
   facade projection (panel / frame) of the facade trade (T-159 / T-162), quantity UNKNOWN until that trade measures it.
   The three 0.30 m projections on layer 2 in front of it are the three timber beam ends of p.6 (T-161 F18): 3 pcs
   DRAWING-CONFIRMED, no BOQ category (listed only). GF SE (dewaneya) face: no 0.200 outline found; two 1.955 m lines
   0.05 m outside it at W11 / W12 (341 / 347), meaning not established.
4. D-23 (designer list, 0.05 m element beside RS-A): classified as a balustrade band (RL-06, same graphic and layer as the
   ST-02 balustrade; GF plan shows it overhead). Its 0.1175 m2 stays outside the 1F floor finish while D-23 is open.

## 6. Rule, test, lesson (ERS s.4 / s.7)

- Rule proposed (any villa; research, not a rule file): **R-RAIL-1** a railing's length is its drawn PLAN band
  centreline (corners once), made 3D per UP-STAIR-012 (per tread where the pitch varies); an elevation or section
  confirms type and height and cross-checks the length, never replaces it; plan vs elevation disagreement -> HELD.
  **R-RAIL-2** a render never makes a railing or shutter; a "NOT IN THE DRAWING" finding is valid only after every sheet
  of the set is read, and lists the sheets read (p.12 held the dewaneya face).
- Regression test: tests/t164_railings (11 pass; synthetic Villa T: two-side roof railing 10.050 lm with the corner
  once (adverse outer-line 10.100); stair pitch line 2.948 vs plan projection 2.520 (adverse); wall handrail not shown
  excluded; helical 2.965; winders per tread 1.277 vs single pitch 1.273; curved treads invariant under rotation /
  mirror / mm; undimensioned railing HELD (None, never 0); shutters counted, m2 HELD; missing values refused).
- Lessons-register row proposed:

| 2026-10-22 | Dewaneya shutters, roof railing and the fence pier reported "NOT IN THE DRAWING" from the renders (T-161 F05 / F13 / F15) | the fence sheet p.12 (FENCE ELEVATION, which draws the dewaneya street face) was not in the sheets read | A render finding "NOT IN THE DRAWING" requires every sheet of the set read and listed (any villa) | tests/t164_railings (census keeps drawn vs not-drawn apart); T-164 s.3 | corrected in T-164 |

## 7. Missing / uncertain

- RL-07 winder turn MS1-T and half-landing MS1-LD: rail path round the 0.10 m well not dimensioned (HELD, never 0).
- RL-09 ST-02 outer band: guard or string (designer). RL-10 fence railing length (not printed). RL-11 entrance stair
  guard (none drawn). RL-04 balcony edge (plan vs elevation).
- Heights not printed for RL-03 .. RL-11; materials of every railing and of the shutters not printed (HELD).
- The FIN workbook could not be re-read (connector size limit); the 18.95 lm is taken from the research record.

Files: `t164_railings.py` (pure functions + `--check`), `t164_alsenan.py` (development-villa census from the private
DXF by handle; `--write`), `RAILINGS_T164.csv`, `SHUTTERS_T164.csv`, `summary.json`. Reproduce:
`python3 -I research/agents_t164/t164_alsenan.py <architectural plan DXF> --write`.
