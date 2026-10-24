# T-248 Whole-line closure: CONC.COLUMN (columns + necks), every member once (Alsenan; every villa)

Worker 1 (lane S), 2026-10-24, run unknown. Research piece, not wired: no engine, candidate or released line changed;
integration is a lane I package after the Checker's verdict. Development villa, not an accuracy claim. Drawings named
by Drive folder and title; members by DXF handle; lengths, areas, volumes only (no coordinates committed).

## 0. Inputs and runs (own, this task)

| Input (Drive "Alsenan chalet project") | sha256 | Read for |
|---|---|---|
| "ST7757 dxf.dxf" | 9f9d1179...38079 (= manifest) | the merged T-217 extractor re-run on it: **reproduces the committed member x storey inventory byte for byte** (FP / CAP / GBP / GFRS / FFRS / SFRS outlines, schedule, size texts, dimension chains, P.C / T.C / D.C notes); slab-plan outline centres (to carry the T-119 ids onto the handles, 59 / 59 bound at <= 1 mm); footing outline 1B1B and the tags / necks inside it; the FP positions of the six neck-only CN |
| "P7757_DXF_COMPRESSED.zip" -> P7757.dxf | ab54dd55... (= manifest) | the released baseline run only |
| freelancer RC workbook | committed cells | tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json, sheet 'الحوائط + الأعمدة' rows 11-74 |

Runs: released baseline A `tools/release_baseline.py run research/agents_t165/baselines/V29_ROUTEG_NO_PROFILE.json` on
the working head cebb269b: **REPRODUCED**, 1,455 lines, BOQ_LINES.csv b96185d4 (digest of its column / neck lines:
`RELEASED_A_COLUMN_LINES.json`, values only). Route G provisional register: the committed
research/urban_engine_m4_correctness/st7757_route_g/PROVISIONAL_REGISTER.csv (89 column / neck m3 lines). Candidate:
own run `research/agents_t167/v304_run.py` then `research/agents_t211/v309_run.py` on the same copies: V3_0_8_BOQ_LINES.csv
57fe219a (= the Checker's reproduced V3.0.8) and **V3_0_9_BOQ_LINES.csv 63b350cf** (digest `CANDIDATE_V309_COLUMN_LINES.json`).

Files: `t248_column_line.py` (COLUMN_LINE_V1, pure rules, stdlib), `t248_extract.py` (private DXF -> values-only
`ALSENAN_COLUMN_INPUT.json`), `t248_released_a.py` (run A digest), `t248_alsenan_check.py` -> `LEDGER_T248.csv`
(100 rows: 59 columns, 36 necks, 5 route G lines on members no plan draws), `BY_MARK_T248.csv` (storey x mark vs his
rows), `summary.json`; tests `tests/t248_column_line` (27: Villa K hand fixture + adverse + Alsenan ledger pinned).

## 1. The physical element and the convention (ERS s.2.1, s.3)

- **COLUMN** (STR.CONC.COLUMN): the solid inside one column outline on one storey between two structural datums: its
  base (neck / ground-beam top for a ground-floor column, the slab top below for an upper column, the carrying beam's
  top for a planted column P.C) and its top (the slab top it carries). **NECK** (STR.CONC.NECK): the column below the
  ground floor, footing top -> ground-beam top (R-NECK-ENDS-1, T-205). The keyed reference line CONC.COLUMN
  (T001B_KEY_MAP: freelancer 'ورقة1' row 19 = 'الحوائط + الأعمدة'!B74 = 39.7515 m3) = necks + columns + his lift-pit
  walls row.
- **Convention C1** (stated by T-234 / T-241, every side): slab panels stop at the beam and column faces, beam runs are
  billed b x D x L to the column faces, so the **column line owns its footprint from its base to the slab top**
  (R-CONC-OWN-1: column > beam > slab). Where a beam is billed THROUGH a column the beam owns that piece and the column
  stops at the beam soffit: on this set only PC-2F (SFRS 778) under 2F B7 20x75 (T-220).
- **Owner manual method beside, not instead**: URBAN-COLUMN-HEIGHT-TO-CONTROLLING-MEMBER@v1 + NON-OVERLAPPING model
  (column = A x (interval - D_ctrl), joint = A x (D_ctrl - t), head A x t in the plate; T-119 r2 merged, Checker 0.0 % on
  two columns) is a split of the SAME solid into three lines. Its holds (a framing member's unprinted depth) move
  concrete between the three lines, never the solid. On the 28 closable columns: owner column 15.4455 + joint 2.2899 +
  head 0.6111 = **18.3465 m3 = the solid** (re-added per member).
- **Datums** (each with its source; nothing defaulted):

| Datum | Value | Status | Source |
|---|---|---|---|
| GF slab top = ground-beam top, main house | +0.95 | DRAWING-CONFIRMED | ST p.13 'Ground Floor slab level'; FFL +1.00 - drawn 0.05 (T-214 MERGED b29060c2) |
| annex ground slab top | +0.25 | DRAWING-CONFIRMED | FFL +0.30 - 0.05 (T-214) |
| GF roof = 1F floor slab top | +5.45 | DRAWING-CONFIRMED | FFL +5.50 - 0.05 (T-214); one 0.16 plate on ST p.4 (T-220 reading, merged 579e613d) |
| 1F roof = 2F floor slab top | +9.65 | DRAWING-CONFIRMED | FFL +9.70 - 0.05 (T-214); one plate on ST p.5 (T-220) |
| 2F roof structural top | <= +13.90 | HELD (D-39) | only the finished +13.90 printed; roof build-up / falls unprinted (T-214 refuses the constant 0.05 on a roof) |
| annex roof structural top | <= +4.30 | HELD (Q-54 B, D-39) | only the finished +4.30 printed |
| formation | <= -1.50 | HELD (Q-21 C) | ST p.9 note 1: at least 1.50 below the existing +-0.00, a LIMIT (a bound, never a length) |
| underlay | 0.17 | VERIFIED (T-206) | 0.05 screed + 0.02 membrane + 0.10 blinding, ST p.13 |
| lift-pit raft top | - | HELD (D-43) | ST p.14 'as per lift manufacturer' |

## 2. Inventory (engine-independent) and the line split

Inventory = the T-217 member x storey census re-extracted from the Drive DXF this run (identical to the committed
file), T-220 for the planted columns: **GF 30 / 1F 20 (18 + 2 P.C) / 2F 9 (8 + 1 P.C) = 59 columns, 36 necks**
(30 under GF columns + 6 neck-only CN). Turned columns (T.C at C8 / F8 and C9 / F9) are the 1F members FFRS 664 / 667,
each once. The 5 route G 1F / 2F lines on members no storey plan draws (T-217 / T-220 NOT_DRAWN, D-65) are UNKNOWN.

| Component | Members | m3 | What holds it |
|---|---|---|---|
| **Columns DRAWING-CONFIRMED (closable)** | **28** (GF 19, 1F 9 incl. PC-1F-A / PC-1F-B) | **18.3465** (GF 14.0625, 1F 4.2840) | nothing: one printed section, both datums drawing-confirmed |
| Columns CONFLICT | 15 (GF 4, 1F 11) | **8.034 .. 10.119** (GF 2.070 .. 2.475, 1F 5.964 .. 7.644) | schedule vs slab-plan outline, X6 (T-217): GF C x2 (347 / 359), C3 344, C8 380 (D-16); 1F C3 691, C4 676 / 697, C5 673 / 685 / 694, C6 688, C7 68E, C8 69A (D-16), C9 667 / 679 (D-64 proposed, D-63) |
| Columns HELD, annex roof datum | 5 (34A, 34D, 356 C; 350, 353 C3) | <= 2.2275 (no low end) | Q-54 B / D-39; 34A / 34D / 356 / 350 also section CONFLICT |
| Columns HELD, two ground-slab levels | 2 (35F C5, 365 C3 on the CB5 line) | 1.2375 .. 1.4300 | base +0.25 (annex) or +0.95 (main): the column / neck boundary is not printed where the two slabs meet |
| Columns HELD, 2F roof datum | 9 (all 2F) | <= 3.155 on 7; open on the 2 tank columns | D-39; tank columns 40F / 424 also D-44 (B15 upstand / downstand); PC-2F 778 to the B7 soffit <= 0.350 and section CONFLICT 0.08 .. 0.10 |
| Columns UNKNOWN | 5 route G lines (1F C3 10E4; 2F C3 10C5, C3 10E4, C5 10BD, C8 10E0) | no value (route G 2.268) | D-65: no slab over the position, no outline (T-220 searched DXF + PDF + architectural plans) |
| **Necks HELD** | **36** | **>= 9.2568 on 32**, no upper end; the 4 lift necks no value | formation unprinted (Q-21 C) on all 36; lift necks also pit depth (D-43) and section CONFLICT (D-63); C10 / corner C on 1B1B also Q-31 C; 5 FOUNDATION section CONFLICTs (lift x4, C8 at F14) |
| Lift-pit walls (his row 11) | ring | no value | pit depth (D-43); T-204 ring 1.100 m2 net = 1.100 m3 per m of depth |

Neck height, drawing-derived (R-NECK-ENDS-1 with T-214 b = 0.05): main house **h = 2.28 - H + d**, annex
**h = 1.58 - H + d**, d >= 0 the formation below the printed limit; the lower bound uses d = 0. The two CB5-line necks
carry the annex / main boundary range. The six CN are main-house necks: each lies outside the annex extent with its
three nearest column necks all main-house (0.44 .. 5.44 m; `neck_only_zone`).

Ownership, each intersection once (all PASS, `summary.json`):

| Check | Result |
|---|---|
| slab panels (T-234 C1 partition, T-241 faces) inside a column outline | **0.0000 m2 on all 59 SOLID outlines** |
| beam bands over a column outline | the 7 released double joints (GFRS 347 / 34A / 34D / 350 / 356 / 359, FFRS 667; T-241 polygon 0.4401 + 0.0090 m2) are deducted from the beam runs in the T-241 ledger: the column owns them, once; 2F 778 is B7's (THROUGH), the column stops at the B7 soffit |
| column top vs beam basis (`ownership`) | 0 DOUBLE, 0 GAP |
| neck top = GF column base (`stack_check`, 30 stacks) | 0 differences |
| necks on footings | the neck starts on the footing top; footings billed at full L x W x H (T-233): nothing shared |
| ground beams | T-242 runs end at the neck faces (READY branch, source reference only): the neck owns its footprint through the ground-beam depth |
| outline parts outside the slab-sheet face partition | 21 outlines, 0.3511 m2 of plan: edge columns / turned outlines; no quantity (the solid is from the outline), named |

## 3. Footing identity 1B1B (task item d)

On the FOUNDATION PLAN, S-FOOTINGS polyline 1B1B is ONE open outline 3.25 x 1.40 m (gap 0.70 m where strap SB1 enters);
inside it: the tags 'F10' (TEXT 168B) and 'F' (TEXT 10A5), and the neck outlines 10E8 (C10) and 10A4 (corner C). The
engine's untyped footing line `P-C:FTG:SH10:T652:10A5` is keyed on the tag 10A5: it is **the same physical element**
(identity established: 26 drawn footings = 26 elements; 27 tags because one outline carries two). Its 1.960 m3 equals
the F10 schedule row 2.80 x 1.40 x 0.50 exactly and leaves out the F row 0.90 x 0.80 x 0.30 = 0.216 (reading A, rows
separately 2.176) or the outline extra (reading B, one outline at the deepest tagged depth 2.275): the TYPE stays
UNRESOLVED under owner Q-31 C (HELD 2.176 .. 2.275, T-233), the identity no longer is. Necks there: C10 on the F10 part
(H 0.50 on both readings), the corner C on the F part (H 0.30 or 0.50).

## 4. Line totals vs released A, route G, the candidate and the freelancer (m3)

| Side | Columns | Necks | Lift walls | Line |
|---|---|---|---|---|
| **Drawing (this task)** | 18.3465 closable + CONFLICT 8.034 .. 10.119 + HELD 16 (bounds above) + UNKNOWN 5 | HELD, >= 9.2568 (32) | HELD | closable component 18.3465; nothing else is a value |
| Released A (V29_ROUTEG_NO_PROFILE, b96185d4) | **82 lines, all BLOCKED_RFI, no quantity** (GF 30 / 1F 22 / 2F 22 'STOREY_HEIGHT_NOT_PRINTED'; 5 CN 'TYPE_NOT_IN_SCHEDULE'; 3 P.C 'PLANTED_COLUMN_STOREY') | 35 BOUNDED 3.075 .. 15.375 + 1 BLOCKED | none | HELD (the scoreboard's 'ref line HELD') |
| Route G provisional register (not released) | 61 lines 35.286 (GF 20.250 / 1F 9.660 / 2F 5.376) | 28 lines 10.8555 (high 13.5255) | none | 46.1415 |
| Candidate V3.0.9 (own run, 63b350cf; column / neck lines identical to V3.0.8 57fe219a) | **33.606** PROVISIONAL / SOURCE_DERIVED (GF 30 lines 20.250; 1F 18 lines 9.240 + PC-1F-A 0.588; 2F 8 lines 3.528) + 9 BLOCKED (PC-1F-B, PC-2F, 5 x D-65, 2 CN) + 3 CN BOUNDED 1.134 .. 3.483 | 35 BOUNDED 3.075 .. 15.375 + 1 BLOCKED | none | NOT RELEASED |
| Freelancer | GF 17.4375 / 1F 7.728 / 2F 3.381 = 28.5465 | 8.805 | 2.40 | **39.7515** |

**Drawing vs route G, member by member.** The 28 closable columns equal their route G lines exactly where a line
exists (26 members, 0 differ: the profile's 4.50 / 4.20 m FFL-to-FFL intervals equal the structural intervals because
the drawn build-up is 0.05 on every floor); the two 1F planted columns (0.588 + 0.420 = 1.008) have **no** route G line
(missing scope). The 15 CONFLICT members: route G took the schedule end (GF the upper, 1F the lower end). HELD: route G
carries the annex columns at 4.50 (its annex roof +4.30 is unprinted structurally) and the 2F columns at 4.20 (the roof
top is unprinted). UNKNOWN: route G carries 2.268 on five members no plan draws (V3.0.8 already holds them: ENGINE_RIGHT
for the candidate, T-236 F2). Released A, for its part, inventories 22 1F and 22 2F lines (every schedule type at every
neck) where the plans draw 20 and 9: 4 + 14 BLOCKED lines on members not drawn on that storey (no quantity, but the
count is wrong) and the 3 P.C lines with no storey.

**Drawing vs candidate V3.0.9, by storey** (the candidate = route G less the five D-65 lines, plus PC-1F-A):

| Storey | Candidate | Same members, drawing | Named causes |
|---|---|---|---|
| GF | 20.250 (30) | DC 14.0625 (19, equal) + CONFLICT 2.070 .. 2.475 (4) + HELD 7 | CONFLICT taken at the schedule (upper) end (-0.405 .. 0); the 7 annex / boundary columns PROVISIONAL at 4.50 = 3.7125 on an unprinted annex roof (Q-54 B, D-39) and a two-level base: HELD in the drawing (annex-only <= 2.2275 with no low end, boundary 1.2375 .. 1.4300) |
| 1F | 9.828 (18 + PC-1F-A) | DC 4.284 (9) + CONFLICT 5.964 .. 7.644 (11) | CONFLICT at the schedule (lower) end (0 .. +1.680); PC-1F-B BLOCKED in the candidate (its D-26 hold is the owner split's, T-220) while its solid 0.420 is DRAWING-CONFIRMED |
| 2F | 3.528 (8) | HELD 9 (<= 3.155 on 7; tank columns open) | the candidate's 4.20 m runs FFL +9.70 to the FINISHED roof +13.90: FINISHED_AS_STRUCTURAL at the top; PC-2F BLOCKED in both |
| UNKNOWN storey | 3 CN BOUNDED 1.134 .. 3.483 + 2 BLOCKED | none: CN is a neck-only mark (T-217 / T-075), its six necks are in the neck component | a column line on a mark no slab plan draws (T-236 F3 out of inventory scope): never valued |

**Drawing vs freelancer, by storey and mark** (BY_MARK_T248.csv; he prices type x count x (interval - 0.75)):

| Storey | His | Count step | Section step | Height step | Drawing | Residual |
|---|---|---|---|---|---|---|
| 1F | 7.728 | +0.828 (C6 drawn 1 / his 0; C8 2 / 1; C9 2 / 1; C3 2 / 3; C7 1 / 2) | -0.138 .. +1.242 (CONFLICT sections; his C9 0.20 x 1.00) | +1.830 .. +2.130 (0.75 m x A on every column: his uniform 0.75 soffit, the joint and head under C1 belong to the column) | 10.248 .. 11.928 | **0.000 at both ends** |
| GF | 17.4375 | -0.5625 (C1 1 / 2, C2 4 / 6, C9 2 / 3, C11 2 / 1, C3 6 / 5) | -0.731 .. 0 | <= +3.320 | <= 20.195 (low end open: annex roof) | **0.000 at the high end** |
| 2F | 3.381 | 0 (9 / 9) | -0.207 .. +0.017 | open (roof datum) | <= 3.155 on 7 + 2 open | open |
| Necks | 8.805 | +0.885 (C3 6 / 5, C11 2 / 1) | -0.675 .. -0.330 (his C11 0.40 wide; lift necks) | open (formation) | >= 9.2568 on 32 | open |

The height step is the whole story of the column difference: his 3.75 / 3.45 m are the storey intervals less a uniform
0.75 (an owner-method-like split with a global depth, refused by the Urban method itself: 'never a global depth'),
while his beam sheet runs the beams through the supports (T-241), so part of the joint sits in his beam line: a
RULE_DIFFERENCE across two lines, not a missing quantity. The necks are different: **the lower bound alone (d = 0,
the printed limit) on the 32 non-lift necks, 9.2568, is above his whole neck total 8.805 (which also includes four
lift necks)**: his flat 1.50 (the p.9 excavation-limit number, T-205) cannot be a neck length on this set.

## 5. Verdict proposals (for the Checker)

| Item | Proposal |
|---|---|
| 28 closable columns, 18.3465 m3 | DRAWING-CONFIRMED (inventory re-extracted, sections AGREE on schedule + outline, datums T-214); **CLOSABLE** component once the Checker re-measures the list in section 6 |
| 10 of them held in the owner split (D_ctrl of a held framing member: 6 D_SETTLED, 4 D_OPEN) | ENGINE / ledger: the solid closes, the owner split stays HELD for those 10 (joint vs column line), RULE: R-COLUMN-LINE-1 |
| 15 CONFLICT, 8.034 .. 10.119 | UNRESOLVED (designer D-16, D-63, D-64 proposed): never the schedule end, never the larger end |
| 16 HELD | UNRESOLVED on D-39 (2F roof, annex roof), Q-54 B, D-44, the annex / main boundary (new designer item proposed below) |
| candidate V3.0.9 2F 3.528 (8 lines) and GF annex / boundary 3.7125 (7) | ENGINE_WRONG basis: PROVISIONAL on an unprinted roof top (2F: FFL to the finished +13.90; annex +4.30) and on a two-level base; should be HELD with the bounds above |
| candidate PC-1F-B BLOCKED | ENGINE over-holds: the solid 0.420 is DRAWING-CONFIRMED; only the owner split waits on D-26 |
| 5 route G lines not drawn (2.268) | ENGINE_RIGHT for V3.0.8 (held), route G / released A over-inventory |
| 2 planted columns 1.008 m3 | ENGINE omission in route G (no line); DRAWING-CONFIRMED here |
| necks | UNRESOLVED (formation, Q-21 C); **FREELANCER_WRONG on height**: his 8.805 lies below the drawing's lower bound 9.2568 on 32 necks; released A BOUNDED 3.075 .. 15.375 is consistent with the bound (route G 10.8555 too) |
| freelancer columns 28.5465 | RULE_DIFFERENCE on height (uniform 0.75 soffit vs C1 slab top), FREELANCER count slips by mark (above), 1F reconciled to 0.000 |
| footing 1B1B | identity ESTABLISHED (one element, engine line = it); type UNRESOLVED (Q-31 C) |

No owner question (ERS 2.7 not met: unprinted design levels and conflicting printed sections are designer items).
Designer item proposed (Lead, DESIGNER_CLARIFICATIONS): where the annex ground slab (+0.25) meets the main ground slab
(+0.95) on the CB5 line (GF C5 35F, C3 365; their necks): at which level does the neck end and the GF column start?
(0.1925 m3 between the two readings on the two columns, 1.2375 .. 1.4300.)

## 6. Checker re-measure list (handles on 'ST7757 dxf.dxf')

1. Closable, one per type of evidence: GF C11 GFRS 35C on FP 10BA (schedule CGT 1DFA GR 25 x 110; 0.275 x (5.45 - 0.95)
   = 1.2375); GF C9 lift GFRS 338 on FP 1090 (1DD2 GR 25 x 100; 1.125); 1F C2 FFRS 66D on FP 1084 (1D46 1ST 20 x 50;
   0.10 x 4.20 = 0.420); 1F C8 turned FFRS 664 on FP 10D0 (T.C note 31F; 1DBE 1ST 20 x 90; 0.756); PC-1F-A FFRS 66A
   (start GFRS 329, text 544 'P.C 20x70'; 0.588).
2. The ownership claims: no SLAB face in any SOLID outline (T-241 faces), the 7 joints (347 / 34A / 34D / 350 / 356 /
   359 / 667) deducted in the T-241 beam ledger, SFRS 778 under B7 (BAND0009).
3. 1B1B: polyline vertices (open, 3.25 x 1.40, gap 0.70), TEXT 168B 'F10' and 10A5 'F' inside, neck outlines 10E8 /
   10A4 inside.
4. The annex zone: GFRS 34A / 34D / 350 / 353 / 356 under the annex roof beams only; 35F / 365 on the CB5 line.
5. Re-run: `python3 -I research/agents_t248/t248_extract.py <ST dxf> --write`, `python3 -I
   research/agents_t248/t248_released_a.py <run A dir> --write`, `python3 -I research/agents_t248/t248_alsenan_check.py --write`.

## 7. Rule, test, lessons row

General rule proposed (every villa; provenance T-248; a new rule version when adopted, R-COLUMN-LINE-1): a column line
is closed only when (a) every member of an engine-free inventory (slab-plan SOLID outlines per storey, P.C / T.C
starts, neck outlines) is one row, and every engine / register line on a member no plan draws is UNKNOWN, never a
value; (b) the solid is section x (top datum - base datum), the datums structural and printed (finished levels refused,
limits only bounds), under a stated convention (C1: to the slab top; a beam billed through owns its piece and the
column stops at its soffit); (c) the owner's split (column / joint / head) is carried beside and its holds do not hold
the solid; (d) a section conflict is a range (X6); (e) every intersection is checked once (slab, beams, footings, ground
beams, neck / column stack); (f) a total is compared with another side by storey and mark.
Test: tests/t248_column_line (Villa K: a column between a neck and a beam-framed slab, a planted column on a beam, a
schedule / drawn CONFLICT, a planted column under a beam billed through, an undrawn upper line, a neck on a limit;
adverse: finished level / default datum / limit as a length refused, CONFLICT collapse refused, DOUBLE and GAP at a
through beam refused, undrawn line never valued, held never 0, stack gap flagged; units m / cm / mm, rotated section,
metamorphic order; Alsenan pinned: 59 + 36 + 5 rows, components, route G equality, partition, 1B1B, freelancer 1F
reconciled to 0).
Lessons row (proposed): 2026-10-24 | CONC.COLUMN had 31 / 59 columns own-measured and 'every column HELD that a held
beam frames into' (T-119), while 10 of those close from the drawings | the owner method's split (joint vs column, which
depends on the deepest framing member) was taken as the status of the column's solid, which under C1 depends only on
its section and its two datums | keep the physical solid and the owner's split apart; a hold in the split moves concrete
between lines, never the solid (any villa; columns, beams at joints) | tests/t248_column_line test_owner_split_re_adds,
test_components_split_closable_conflict_held_unknown | PROPOSED. Second row (proposed): his necks 8.805 m3 lie below the
drawing's lower bound 9.257 m3 | a printed limit used as a length | a limit gives a bound, and a bound alone can prove
another side wrong before the value is known (any villa) | test_components (neck lower bound) + T-205 adverse | PROPOSED.

## 8. Not done / uncertain

- The candidate is compared by storey, mark and state (its element ids carry another frame offset than route G's, so
  no member-by-member join was made); the per-storey equalities above are exact.
- The GF / 1F tops under terrace bays rest on the one-plate reading of the slab plans (T-220, merged): D-39 also asks
  whether a roof slab steps down from the adjacent floor slab; a step would change those columns (named, not applied).
- The 21 outline parts outside the slab-sheet face partition (0.3511 m2) are not traced one by one.
- Formwork and rebar of the columns: other tasks (T-163, T-148). Nothing released.
