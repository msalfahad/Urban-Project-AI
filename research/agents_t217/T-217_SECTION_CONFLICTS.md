# T-217 Printed section conflicts at columns and necks as CONFLICT records

Worker 1 (lane S), 2026-10-23, run session_01CF5LLRB8BokMEE3ow6Zbqn. Development villa, not an accuracy claim. ERS s.2
steps 1-5, s.3 and s.7 applied. No engine module, method version, route G, rule / knowledge file or released quantity
changed. New (unwired, stdlib): `section_conflict.py` (SECTION_CONFLICT_V1, rule proposal R-SECTION-CONFLICT-1),
`t217_extract.py` (reads the private DXF, writes `ALSENAN_SECTION_INPUT.json`: marks, sizes, DXF handles; no
coordinates), `t217_alsenan_check.py` -> `summary.json`, `LEDGER_T217.csv` (one row per member x storey). Tests
`tests/t217_section_conflict/` (23 pass: hand fixture Villa S + development-villa checks).

## 1. The physical element and its sources (ERS s.2.1-2.2)

Element: one reinforced-concrete column member on one storey: the neck (FOUNDATION, schedule band FOU) or the storey
column (GF band GR, 1F band 1ST, 2F band 2ND); members = the 36 T-205 neck instances (FP outline handle) plus the
planted columns that stand on a slab. Its SECTION is what is measured here; heights stay with T-205 / T-214 (necks HELD on
unprinted datums; storey columns on the released FFL-to-FFL convention 4.50 / 4.20 / 4.20 m, PROVISIONAL). Sources read
this run (Drive "Alsenan chalet project" / 'ST7757 dxf.dxf', sha256 9f9d1179 = the route G input), each with its KIND:

| Sheet (frame block) | Storey | What it gives | Kind |
|---|---|---|---|
| Schedule of Columns (INSERT CGT, 12 rows C .. C11; CN = text row, T-075) | all | W x D per band FOU / GR / 1ST / 2ND | SCHEDULE |
| COLUMN & AXIS PLAN (CAP) | FOUNDATION | 35 labels, 35 size texts 'WxD' printed under each label (constant offset), locating dimension chains (S-DIM1) spanning each neck on both axes | TEXT, DIM, DRAWN |
| FOUNDATION PLAN (FP) | FOUNDATION | 36 labelled neck outlines (S-COL.BON) | DRAWN |
| GROUND BEAMS PLAN (GBP) | FOUNDATION | 36 neck outlines | DRAWN |
| GROUND / FIRST / SECOND FLOOR ROOF SLAB (GFRS / FFRS / SFRS) | GF / 1F / 2F | column outlines with a S-COL.HAT hatch: SOLID = the column under the slab (the storey's own member); pattern ANSI35 = a column that STARTS on that slab (legend 'Planted column (P.C)', and the turned upper part at a 'T.C'); notes T.C 31F / 324 (C8 at F8, C9 at F9), D.C 38A (C11 at F13: stops), P.C size texts 544 '20x70', 548 '20x50' (GFRS), 77C '20x50' (FFRS); no label and no dimension at any column | DRAWN, TEXT (P.C) |

The six plan frames are one drawing repeated at a fixed pitch (38 724.4 mm in x, 0 in y): every CAP / GBP outline lies on
an FP outline under that one translation (35 / 35, 36 / 36), and every CAP label's mark equals the FP mark of the same
outline (35 / 35, one-to-one assignment). A slab plan's SOLID outline is bound to the neck it stands on within 0.40 m
(offsets 0 / 25 / 50 / 71 mm = half the section change; two at 152 mm). At a T.C two outlines sit on one neck: C9 at F9
37A 0.25 x 1.00 SOLID = the GF column, 322 0.20 x 1.00 ANSI35 = the 1F column turned 90 degrees and starting there (= FFRS
667 SOLID); C8 at F8 likewise (36E GF, 31B -> FFRS 664 1F). Every slab-plan outline is accounted for (0 left over). The
ST7757.pdf slab pages 4-6 (image only) were viewed: plots of the same drawing (same legend and T.C / D.C / P.C symbols;
FFRS 'P.C 20x50 8ø16' with its leader to a hatched column on B19). The CN beside C9 / F9 is not drawn on CAP (T-042).

## 2. Classification rule (R-SECTION-CONFLICT-1, proposed; any villa)

Provenance: owner directive 2026-10-20 X6 (Q-61 (1): a schedule / drawing conflict is a CONFLICT plus a designer request,
never resolved by picking the printed one), ERS s.2.2 / s.3, T-205, D-16 (T-100). Sections orientation-free (sorted
pair), units mm / cm / m normalised.

- HELD: no printed source (schedule, size text or dimension); a drawn outline alone is not a section; never 0.
- AGREE: every source gives the same section.
- DRAFTING_NOTE: every printed source agrees AND the drawing itself prints that section at the member (a size text or a
  dimension chain); only undimensioned drawn lines differ. The drawing's own printed value governs its line; the
  schedule does not 'win' (X6 is not touched: drawing print and schedule agree). The slip is evidence, never a volume end.
- CONFLICT: two printed sources differ (PRINTED_VS_PRINTED), or the only printed value is the schedule while the drawing
  draws another section and prints none (PRINTED_VS_DRAWN, X6). Every candidate section is kept with its sources and the
  area range; never collapsed to one end (not the schedule, not the larger, not the one closer to an estimate); volumes
  per metre of height, or at a given height.
- Slab plans: the storey's own member is the SOLID-hatched outline under the slab; a patterned outline is a member that
  starts on that slab (planted or turned) and belongs to the storey above.

## 3. Results (110 neck-member x storey rows + 3 planted columns; 89 released lines bound: 28 necks + 61 storey columns)

| Storey | AGREE | DRAFTING_NOTE | CONFLICT | not drawn on that storey's plan |
|---|---|---|---|---|
| FOUNDATION | 25 | 6 | 5 | 0 |
| GF | 22 | 0 | 8 | 0 |
| 1F | 7 (+2 planted) | 0 | 11 | 4 (3 type-only; 1 with a released line) |
| 2F | 6 | 0 (+1 planted) | 2 | 14 (4 with a released line) |

### 3.1 The named members (engineering question of the row)

| Member | Storey | Printed | Drawn | Class | Area m2 | At the released height m3 (released) |
|---|---|---|---|---|---|---|
| C8 at F14 (FP 10E0, CAP label 101A, text 101B) | FOUNDATION | CAP text 30X80 + CAP dims FD7 700 + FC8 100 / FE5 150 + FF4 150 = 0.80 x 0.30; schedule CGT 1DBE FOU 30 x 90 | FP 10E0, CAP 886, GBP 24D: 0.30 x 0.80 | CONFLICT P-v-P | 0.24 .. 0.27 | 0.48 .. 0.54 at 2.00 (0.54) |
| C8 at F14 | GF | schedule GR 25 x 90 | GFRS 380 SOLID 0.25 x 0.80 | CONFLICT P-v-D | 0.200 .. 0.225 | **0.900 .. 1.0125 at 4.50 (1.0125)**: the T-180 C8 range, both ends named |
| C8 at F14 | 1F | schedule 1ST 20 x 90 | FFRS 69A 0.25 x 0.80 | CONFLICT P-v-D | 0.180 .. 0.200 | 0.756 .. 0.840 at 4.20 (0.756) |
| C8 at F14 | 2F | schedule 2ND 20 x 70 | not drawn on SFRS | existence UNKNOWN | | released 0.588 |
| Lift C1 (FP 1099; text 107A) | FOUNDATION | CAP text 20X50 + dims E80 100 + E8F 100 / E63 100 + E72 400 = 0.20 x 0.50; schedule CGT 1D32 FOU 30 x 50 | FP / CAP / GBP 0.20 x 0.50 | CONFLICT P-v-P | 0.10 .. 0.15 | 0.195 .. 0.2925 at 1.95 (0.2925) |
| Lift C2 x2 (1093 / 1096; texts 1078 / 107C) | FOUNDATION | texts 20X50 + dims 0.20 x 0.50; schedule 1D46 FOU 30 x 50 | 0.20 x 0.50 on 3 sheets | CONFLICT P-v-P | 0.10 .. 0.15 each | 0.195 .. 0.2925 each |
| Lift C9 (1090; text 1076) | FOUNDATION | text 25X100 + dims F05 150 + EF6 100 / ED9 900 + EE7 100 = 0.25 x 1.00; schedule 1DD2 FOU 30 x 100 | 0.25 x 1.00 on 3 sheets | CONFLICT P-v-P | 0.25 .. 0.30 | 0.4875 .. 0.585 (0.585) |
| Lift group (4) | FOUNDATION | | | CONFLICT | **0.55 .. 0.75 m2 = 0.55 .. 0.75 m3 per m of height** | 1.0725 .. 1.4625 at 1.95 (released 1.4625 = the schedule end on the common -1.50 datum; pit depth HELD, D-43 / T-204, so only per metre is a quantity basis) |
| Lift C1 / C2 / C2 / C9 | GF, 1F (C1 / C2 also 2F) | GR 20 x 50 / 25 x 100 | 0.20 x 0.50 / 0.25 x 1.00 | AGREE (GF; C1 / C2 1F and 2F; C9 2F 0.20 x 0.70 = 2ND); C9 1F CONFLICT (1ST 20 x 90 vs FFRS 679 0.25 x 1.00) | | |
| C at F (FP 10B7) | FOUNDATION | CAP text 100D 30X50 + dims B64 400 + B72 100 / B81 200 + B90 100 = 0.30 x 0.50; schedule 30 x 50 | FP 10B7 0.30 x 0.40; CAP 85B / GBP 218 0.30 x 0.50 | DRAFTING_NOTE | 0.15 | released 0.33 stands |
| C4 at F4 (FP 108D) | FOUNDATION | CAP text 1068 30X50 + dims 898 100 + 8AB 400 / 8B9 100 + 8C8 200 = 0.30 x 0.50 (the chain runs 50 mm past the drawn face); schedule 30 x 50 | FP 108D, CAP 82A, GBP 1E8: 0.25 x 0.50 | DRAFTING_NOTE | 0.15 | released 0.315 stands |

Also DRAFTING_NOTE on the FOUNDATION storey: C at 10A8 / 10AB / 10B4 and C3 at 10AE (GBP draws 0.30 x 0.40; FP / CAP
0.30 x 0.50 and CAP prints 30X50 + dims). T-205's two 'drafting notes' (10B7, 108D) are confirmed, now with the printed
dimension as the evidence.

### 3.2 Every CONFLICT, by storey (impact at the released heights; information on the released lines)

| Storey | n | Members | Released m3 | Range m3 | m3 per m |
|---|---|---|---|---|---|
| FOUNDATION | 5 | lift C1, C2, C2, C9 (FF); C8 at F14 | 2.0025 | 1.5525 .. 2.0025 | 0.79 .. 1.02 |
| GF | 8 | C x5 (all five C drawn 0.20 x 0.40 vs GR 20 x 50); C3 10A0 (0.20 x 0.50 vs 25 x 50) and C3 10AE (0.20 x 0.40); C8 at F14 (0.25 x 0.80 vs 25 x 90) | 4.3875 | 3.510 .. 4.3875 | 0.78 .. 0.975 |
| 1F | 11 | C3 10CC, C4 x2, C5 x3, C6, C7, C8 at F14, C9 x2: FFRS draws 25-wide (GR-deep) outlines where 1ST prints 20-wide; 8 of the 11 drawn sections equal the type's GR band exactly | 5.964 | 5.964 .. 7.644 | 1.42 .. 1.82 |
| 2F | 2 | C3 10CC (0.25 x 0.50 = GR vs 2ND 20 x 50); C5 108A (0.20 x 0.60 vs 20 x 50) | 0.840 | 0.840 .. 1.029 | 0.20 .. 0.245 |
| **All** | **26** | | **13.194** | **11.8665 .. 15.063** (-1.3275 .. +1.869) | |

Pattern (evidence for the designer, not a resolution): on the FOUNDATION storey every conflict is a member printed and
drawn at its type's GR section (lift group) or one consistently 0.80 deep (C8 at F14: FOU text + dims, GF, 1F all 0.80);
on GF the drawn sections are smaller than GR; on 1F they are larger than 1ST and mostly equal GR (the 1F slab plan's
column outlines look copied from the GF ones). Which document governs is not decidable from the set: the schedule pages
are undated with a plot line naming another file and no sheet prints a revision (D-61); X6 forbids picking the schedule.

### 3.3 Planted columns: drawn and printed, no line in any state (missing scope)

| Member | Storey | Start (slab below, ANSI35) | Own outline (SOLID) | Printed | Class | m2 | m3 at 4.20 (released convention) |
|---|---|---|---|---|---|---|---|
| PC:329 | 1F | GFRS 329 0.20 x 0.70 | FFRS 66A 0.20 x 0.70 | GFRS 544 'P.C 20x70' | AGREE | 0.14 | 0.588 |
| PC:386 | 1F | GFRS 386 0.20 x 0.50 | FFRS 69D 0.20 x 0.50 | GFRS 548 'P.C 20x50' | AGREE | 0.10 | 0.420 |
| PC:77B | 2F | FFRS 77B 0.20 x 0.40 | SFRS 778 0.20 x 0.40 | FFRS 77C 'P.C 20x50' (+ '8ø16' on the PDF plot) | DRAFTING_NOTE (one printed source: Checker to judge) | 0.10 (drawn 0.08) | 0.420 |
| **Total** | | | | | | **0.34** | **1.428** (heights not drawing-derived) |

The released V2.9 + route G and V3.0.x have no line for any of the three (no released id binds them; route G reads
columns from the CAP labels, and a planted column has no CAP label). Element continuity rule (T-188): a drawn element
with no line is a finding, never 0. Bars printed for PC:77B only (8ø16).

### 3.4 Existence findings (no quantity; UNKNOWN)

5 released storey lines (2.268 m3) stand on members whose storey slab plan draws no SOLID column there (neither outline
nor hatch, no start symbol on the plan below): C3 10C5 2F 0.42, C3 10E4 1F 0.42 and 2F 0.42, C5 10BD 2F 0.42, C8 10E0 2F
0.588. Searched: the DXF slab-plan frames (S-COL.BON, S-COL.HAT, notes) and the PDF plots p.4-6 at page level (not
zoomed at each member). The route G storey lines come from the schedule band of the type, not from the slab plan, so the
released set may carry members that stop lower (as the D.C at C11 shows the drawing marks some stops). UNKNOWN until the
Checker confirms on the PDF at each member.

## 4. Verdict proposals (for the Checker)

- 6 FOUNDATION DRAFTING_NOTE: **ENGINE_RIGHT** (released section 0.30 x 0.50 = the drawing's printed text and dimension
  chain; the drawn line is a slip). No quantity change.
- 26 CONFLICT member-storeys: **UNRESOLVED** (designer). The released lines all take the schedule section, which is one
  end of each range (GF and FOUNDATION the upper end, 1F / 2F the lower end), so the released 13.194 m3 should carry
  SECTION_CONFLICT with the range 11.8665 .. 15.063 m3 (lane I wiring; neck heights stay HELD under T-205).
- Planted columns: **ENGINE omission** (missing scope 0.34 m2 of section, 1.428 m3 at the 4.20 convention; heights to be
  derived with the storey datums, T-214).
- Existence of the 5 released lines: **UNRESOLVED** (UNKNOWN).
- Freelancer: not reconciled here (he prices per type with his own sections; T-205 did the necks).
- No owner question (ERS 2.7 not met: conflicting printed design documents are a designer item).

## 5. Designer items (for the Lead's DESIGNER_CLARIFICATIONS.md)

- D-16 CONFIRMED and widened: C8 at F14 is printed 30X80 (CAP text) and dimensioned 70 + 10 (CAP), drawn 0.80 deep on FP,
  GBP, GF and 1F slab plans; the schedule gives 90 in every band (FOU 30, GR 25, 1ST 20). Is the C8 at F14 a 0.80-deep
  column (another mark) or a C8 (0.90)?
- D-63 evidence differs from the row: the plan's 20X50 / 25X100 equal the schedule's GR section of the same types,
  printed AND dimensioned on CAP and drawn on FP / GBP. Do the lift columns on the FF pit raft have a FOU-band neck
  (30 x 50 / 30 x 100) or run at their GR section down to the raft? (Pit depth D-43 still HELD.)
- New (proposed D-64): per storey, schedule band or slab-plan outline? 1F: 11 members differ from 1ST, 8 equal GR; GF:
  all five C drawn 0.20 x 0.40 (GR 20 x 50), C3 10A0 / 10AE; 2F: C3 10CC, C5 108A. Also PC:77B printed 20x50, drawn 20x40.
- New (proposed D-65): do C3 at F14 (1F, 2F), C3 at F3 (2F), C5 at F13 (2F) and C8 at F14 (2F) exist (released lines,
  not drawn on their slab plan)?

## 6. Rule and lessons row (proposed)

R-SECTION-CONFLICT-1 as section 2. Adoption = a new rule version (Lead / lane I).

| Date | Problem | Root cause | General rule (scope) | Regression test | Status |
|---|---|---|---|---|---|
| 2026-10-23 | Section conflicts were found one member at a time (D-16 in T-100, D-63 in T-205) while the set holds 26 member-storeys whose printed / drawn sections differ (released 13.194 m3, range 11.8665 .. 15.063) and 3 planted columns with no line (1.428 m3) | The engine takes the schedule band per type and never compares it with the storey plan's outline, the plan's size text or dimension chain; storey columns come from the type, not from the slab plan, so planted columns and stops are invisible; a drawn slip and a real conflict were told apart by judgement | Every member x storey lists its section sources by kind; DRAFTING_NOTE only when the drawing itself prints the agreeing section; otherwise a schedule / drawing difference is a CONFLICT range (X6), never the schedule by default; a slab plan's own member is its SOLID column, a patterned one starts there (P.C / T.C) (every villa) | tests/t217_section_conflict (normal: agree, drafting note with own print, planted columns; adverse: schedule-wins shortcut refused, range collapse refused, drawn-only HELD never 0, the turned pattern outline not taken as the storey's own, mirrored / rotated / mixed units) | proposed |

## 7. For the Checker (re-measure from the drawing)

1. C8 at F14: CAP label 101A, text 101B '30X80', outline 886 and dimensions FC8 / FD7 / FE5 / FF4; FP outline 10E0;
   schedule CGT 1DBE FOU.W 30 / FOU.H 90, GR 25 / 90, 1ST 20 / 90; GFRS outline 380 (0.25 x 0.80), FFRS 69A.
2. Lift: CAP texts 107A / 1078 / 107C '20X50', 1076 '25X100'; dimensions E63 / E72 / E80 / E8F (C1), E28 / E36 / E45 /
   E54, E9E / EAD / EBB / ECA (C2), ED9 / EE7 / EF6 / F05 (C9); FP 1099 / 1096 / 1093 / 1090 in FF 1B2B; schedule rows
   1D32 / 1D46 / 1DD2.
3. C4 at F4: FP 108D 0.25 x 0.50 vs CAP dimension chain 8B9 100 + 8C8 200 = 0.30 (runs past the drawn face) and text 1068.
4. T.C at C9 at F9 (note 324): GFRS 37A SOLID 1.00 x 0.25 and 322 ANSI35 0.20 x 1.00; FFRS 667.
5. Planted: GFRS 544 / 329 -> FFRS 66A; 548 / 386 -> FFRS 69D; FFRS 77C / 77B -> SFRS 778 (PDF p.5 'P.C 20x50 8ø16' on B19).
6. Re-run: `python3 -I research/agents_t217/t217_extract.py <private ST7757 dxf>` reproduces ALSENAN_SECTION_INPUT.json.

## 8. Not done / uncertain

- Bars: a section change alters stirrup lengths and covers, not the longitudinal count; no rebar re-derived (PC:77B prints
  8ø16; 329 / 386 print no bars).
- Formwork faces of the conflicting members follow the same ranges (T-163 r3 lines), not recomputed.
- P.C texts 544 / 548 are bound to their outline by one-to-one nearest assignment (2.9 m away: leaders) and size; the
  sizes agree, the leaders were not traced.
- The PDF slab pages were viewed at page level only; the existence findings stay UNKNOWN.
