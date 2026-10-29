# T-333: BLOCKWORK FILL TABLE on the candidate of record V3.0.21 (development villa; every villa by R-T333-1)

Worker 3, claim 2026-10-29 11:01 UTC (date -u), lane S row taken because lane I was idle (T-331 READY, T-319 waits on
its merge). Integration dependency of T-279. Research only: no engine module, rule or knowledge file, registry file,
candidate line or released line changed; released default stays V2.9 + route G; nothing here is released. ERS read:
s.2.1 (physical element first), s.2.4 (reconcile to named causes), s.3 (one element counted once; build before deduct),
s.4 (rule + test, normal and adverse), s.7 (lesson row).

## 1. Run and identity

Own run on the Drive copies ('Alsenan chalet project': P7757_DXF_COMPRESSED.zip -> P7757.dxf `ab54dd55`;
'ST7757 dxf.dxf' `9f9d1179`), decoded into the private folder only: research/agents_t167/v304_run.py, then
research/agents_t315/v3021_run.py on engine head 16fa5f72. Reproduced on the way: V3_0_15 csv `a4dc01dd` (T-291's
base) and V3_0_20 csv `ca90351b`; **V3_0_21 json `be22a4e4` / csv `3548e39c`, 3,706 lines = the T-315 r2 Gate B
candidate of record**. Extract: `python3 -I research/agents_t333/t333_alsenan.py --extract <run>/t315/v3021` ->
CANDIDATE_V3021_MASONRY_LINES.json (28 masonry lines: id, item, storey, element, unit, state, quantity, RFI text; no
coordinate, no name). Fill: `--write`; `--check` rebuilds byte-identical.

**V3.0.22 (T-331, MERGED 15ac21f7 during this run) changes no masonry line:** own run of
research/agents_t331/v3022_direct.py on the V3.0.21 run above reproduces V3_0_22 json `7199c8b6` / csv `924a60b4` (the
T-331 record, 3,706 lines), and each of the 28 masonry line objects is byte-identical (sorted JSON) between V3.0.21 and
V3.0.22. The FILL therefore applies unchanged to the candidate of record V3.0.22; T-279 wires it there.

## 2. Physical element and what the candidate carries today

A block wall is the masonry between its two faces, from the structural floor to the underside of the member over it,
less the openings built into it (Q-60 A, R-T274-1, R-T288-1). The register (v4, T-288 MERGED 643b310b) measures it wall
by wall; T-291 (MERGED 0c6b2ba5) bound every register wall to the candidate's masonry lines (storey x thickness family
x item, no wall key) on V3.0.15.

**Finding 1: the 28 masonry line ids are the same in V3.0.21 as in V3.0.15** (the line id does not carry the
candidate version). Field by field the 28 lines are equal (item, storey, element, unit, state, quantity, range, formula,
walls, RFI text, project id) except the revision-set identity: `db7b3eb8...` -> `5e369075...` (the one-identity fix of
T-245 r2); the FILL carries the V3.0.21 identity. LINE_REBIND_T333.csv: 28 / 28 same id, 0 lost, 0 new.
**Finding 2: all 21 m2 / m3 masonry lines are still BLOCKED_RFI with no quantity** ('MASONRY_HEIGHT_NOT_IN_THE_DRAWING'
/ MAS.BLOCK 'BLOCK_WALL_NOT_ESTABLISHED'); the 7 ARCH.WALL_RUN lines carry lm figures (PROVISIONAL) and are not filled
(they are the band geometry, compared in T-291 s.5). So T-279 **replaces 21 blanks; it corrects no engine figure**.

## 3. The fill (FILL_T333.csv, 228 rows = 76 walls x 3 items, T-279 consumer shape)

Same columns as T-291's ledger plus `line_id_v3015`; one row per (V3.0.21 line, wall). Every wall once per item
(R-T333-1 rule 2), m3 = m2 x t on every row (checked), closure register - fill = 0.0000 on every status, U, L and
conflict increment for each item (summary.json `closures`).

MAS.BLOCK (m2) after the fill, per line (ARCH.WALL_PANEL carries the same m2 on its own line id; ARCH.WALL_VOLUME the
m3, LINE_BEFORE_AFTER_T333.csv):

| V3.0.21 line | Storey / t | Before | Walls | VERIFIED | DRAW.-CONF. | OWNER-APPR. | Determinate | Est. parts | Drop U - L x d | HELD (blank) |
|---|---|---|---|---|---|---|---|---|---|---|
| L-0d9b9e89bb6455da475d | GF 0.15 | BLANK | 16 | 9.8950 | 21.5261 | 24.2374 | 55.6585 | 0 | 29.4129 - 4.5131 d | 6 |
| L-4165954ce4871eda30cc | GF 0.20 | BLANK | 24 | 66.6220 | 5.1450 | 5.5900 | 77.3570 | 39.1525 | 17.3890 - 3.4000 d | 17 |
| L-ff06449b7f61f19c418d | GF 0.40 | BLANK | 1 | 0 | 0 | 0 | 0 | 0 | - | 1 (GF-H01) |
| L-c22e309433e7b671cf2d | 1F 0.15 | BLANK | 13 | 52.3180 | 19.7326 | 36.7513 | 108.8019 | 27.0417 | - | 6 |
| L-5ffa7157a2fe483dd008 | 1F 0.20 | BLANK | 13 | 125.8760 | 2.0620 | 0 | 127.9380 | 44.7740 | - | 3 |
| L-246f3c09de4c6b90efe5 | 2F 0.15 | BLANK | 2 | 0 | 0 | 9.6400 | 9.6400 | 25.8850 | - | 1 |
| L-afe984a62285e133ec2f | 2F 0.20 | BLANK | 7 | 43.1360 | 0 | 0 | 43.1360 | 19.7165 | - | 4 |
| **Total** | | **BLANK** | **76** | **297.847** | **48.4657** | **76.2187** | **422.5314** | **156.5697** | **46.8019 - 7.9131 d** | 28 HELD + 10 part + held |

(HELD column = walls HELD plus walls carried as ESTABLISHED PART + HELD, each with its held piece named.) Volume after
(m3, never added to m2): determinate 75.801260, established parts 28.667605, drop 7.889735 - 1.356965 d.
Width-CONFLICT increments 0.0947 m2 (GF-W19 / W20 / W22 / W34, 1F-W11 / W16) stay outside every total.

Per block type and thickness (TYPE_BEFORE_AFTER_T333.csv; before BLANK on every line):

| Type / t | Walls | Determinate m2 | Est. parts m2 | Drop m2 | Determinate m3 | Est. parts m3 | Drop m3 |
|---|---|---|---|---|---|---|---|
| WHITE 0.20 | 27 | 140.7070 | 99.8430 | 17.3890 - 3.4000 d | 28.141400 | 19.968600 | 3.477800 - 0.680000 d |
| BLACK 0.20 | 16 | 107.7240 | 3.8000 | - | 21.544800 | 0.760000 | - |
| BLACK 0.15 | 30 | 174.1004 | 27.0417 | 29.4129 - 4.5131 d | 26.115060 | 4.056255 | 4.411935 - 0.676965 d |
| WHITE 0.15 | 1 | 0 | 25.8850 | - | 0 | 3.882750 | - |
| unclassed (GF-H01 0.40, GF-H02 0.20) | 2 | HELD | | | HELD | | |

Hand re-add (one line): GF 0.15 determinate 55.6585 = GF-W19 8.5950 + GF-W21 4.3090 + GF-W22 12.9311 + GF-W28
20.1384 + GF-W29 4.0990 + GF-W33 5.5860 (register v4) = 55.6585. Engine line before: BLANK.

## 4. Per wall (WALL_TABLE_T333.csv; acceptance (a))

Per wall: register id, V3.0.21 MAS.BLOCK line id, candidate before (BLANK: the line has no quantity and no wall key),
register v2 / v3 net, established v4 net (or U and L for a drop wall), v4 - v3 to 0.0001 m2 with the cause T-288
recorded, type / thickness, opening ids with their state, status and the Checker run. 'Current vs established' is
therefore BLANK -> established on every wall (nothing to subtract), with the register history v2 -> v3 -> v4 beside it.

The three walls the Checker corrected are carried at the Checker's own values (CHECKER_VALUES_T333.csv; the build
refuses a difference above 0.0005 m2 or a status mismatch):

| Wall | Checker own | Fill | Diff. | Cause |
|---|---|---|---|---|
| 1F-W20 | 24.5073 VERIFIED (02:00) | 24.5070 VERIFIED | -0.0003 | the Checker reported 24.507 (its rounding) |
| 1F-W22 | 20.401 VERIFIED (01:43 whole wall) | 20.4010 VERIFIED | 0 | the 01:43 whole-wall value supersedes the 15:59 piece value 20.402 the row quotes (B4 0.1245 read at 01:43) |
| GF-W16 | 15.4356 - 2.950 d (02:00) | 15.4360 - 2.9500 d HELD ON DROP | +0.0004 | drawn B5 band edge (T-288 s.3, Gate A PASS); the d = 0 bound is never a quantity |

## 5. Openings once by id (R-T261-1 rule 9)

The 71 opening ids of T-291 (OPENING_DEDUCTIONS_T291.csv) ride with their host wall unchanged: 32 DEDUCTED, 14
ON_HELD_WALL, 5 IN_HELD_PIECE, 9 HELD, 3 NOT_APPLICABLE (W02 / W03 / W17 glazed hosts), 8 NO_HOST; each FILL row lists
its wall's openings. Nothing is deducted twice: W18 is inside VERIFIED 1F-W00 by its 1.0094 m2 part in the masonry; W03
sits in glazed GF-W37 (no masonry built).

## 6. Parapet and plinth placed once (COMPONENTS_T333.csv; acceptance (c))

- **Parapet blockwork alternative, 24 runs: 0 .. 60.5965 m2 (0 .. 12.040291 m3; 2F NE-1 is 0.15 thick), + 135.981 m2
  per m of b_edge (D-39 HELD)**: bound to **NO masonry line** (every wall of the run's network bounds a room; no roof
  masonry line exists), material HELD (Q-65 C, designer: P1 block above a 0.30 RC upstand OR all RC), carried by name
  outside every total, never 0. Each run is EXCLUSIVE with its RC alternative above the upstand, which T-319 (the
  CONCRETE owner) carries; the 0.30 RC upstand is RC in every alternative. A run carried as block AND as RC above the
  upstand is refused (PARAPET_BOTH). Freelancer: 172.93 m2 of parapet blockwork (heights 1.0 / 1.8 / 1.0 vs printed
  0.50 / 1.30 / 0.50 above finish): RULE_DIFFERENCE on height, UNRESOLVED on material (T-311).
- **Plinth wall course 5.0593 m2 (29 segments)**: CONTAINED in the GF 0.20 MAS.BLOCK line L-4165954ce4871eda30cc (the GF
  wall starts at the structural top: house +0.95, annex beam +0.25; the course up to the F.F.L. is inside each wall's
  height), so it **adds nothing** and is never a second row (CONTAINED_ADDED refused). House zone 3.5822 m2 rides with
  its walls' own statuses (T-311 gives no per-wall split); annex zone 1.4771 m2 sits inside annex walls HELD on the
  annex datum (Q-54 B), blank with them; passage segment P-1 HELD (no beam top read).

## 7. Engine vs freelancer (engineering terms)

Blockwork m2: the candidate V3.0.21 gives **nothing** (21 lines BLOCKED, unchanged since V3.0.15); after T-279 wires
this fill: 422.5314 m2 determinate (VERIFIED 297.847 on 18 walls, DRAWING-CONFIRMED 48.4657, ASSUMED - OWNER-APPROVED
76.2187) + 156.5697 m2 established parts + 46.8019 - 7.9131 d m2 drop walls + 28 walls HELD by name. Freelancer 1,260.69
m2 total (exterior 559.80 + 15 cm 617.25 + 20 cm 83.64, one height per storey, parapets and fence inside his 15 cm
section); no total verdict while 28 walls, 10 held pieces and d are HELD. Verdict proposal per line: **ENGINE_BLOCKED /
REGISTER_DETERMINATE** (UNRESOLVED on the held walls); parapet: RULE_DIFFERENCE (height) / UNRESOLVED (material).

## 8. Rule, tests, lesson

- **R-T333-1** (binding_fill.py, PROJECT-INDEPENDENT; provenance T-291 / T-288 / T-311): rebind by (item, storey,
  family, unit), one current line per key, lost / ambiguous / unknown state refused, new lines listed, the line's own
  state carried (blank replaced, figure corrected, both stated); every wall once per item; m3 = m2 x t; held blank and
  named, drop never evaluated; contained components never added; a held alternative in no line, outside totals,
  exclusive with its RC twin.
- **tests/t333_blockwork_fill** (27): villa M hand truth (M-W1 5.000 x 3.000 - 1.000 x 2.100 = 12.900 m2 / 2.580 m3
  VERIFIED; M-W3 6.000 - 2.000 d; M-W4 9.000 DRAWING-CONFIRMED; parapet P-1 0 .. 5.000 m2; plinth 0.500 m2 contained),
  rebinding to new ids, a new line listed, a line with a figure CORRECTED, order / mirror invariance; adverse: a wall
  under two ids, one id twice, a held wall as 0 or unnamed, a drop term evaluated, a volume at the wrong thickness, a
  parapet run as block and RC, a held parapet in a wall line or as 0, the plinth course added again, a lost / ambiguous
  line, an unknown state, millimetres; Alsenan: byte-identical rebuild, V3.0.21 json be22a4e4 / csv 3548e39c, 28 ids
  stable, 21 blanks replaced, closures 0, register v4 totals, Checker values, m3 = m2 x t, held blank, 24 parapet runs
  in no line, plinth 5.059 contained in the GF 0.20 line, no coordinates.
- **Lessons register row (s.7, proposed):** 2026-10-29 | a binding table was asked 'on the V3.0.21 line ids' as if the
  ids moved with each candidate | the line id is content-derived (storey, element, item), not versioned; an earlier
  ledger stays valid while the key and state are unchanged | before re-deriving a ledger for a new candidate, rebind it
  by key and prove the ids, states and quantities unchanged; re-derive only what moved | tests/t333_blockwork_fill
  (normal: ids rebound and states carried; adverse: a lost or ambiguous key refused) | OPEN (T-333 READY).

## 9. For the Checker (re-measure / re-derive)

1. Re-extract the 28 masonry lines from your own V3.0.21 run (json be22a4e4 / csv 3548e39c): ids equal to T-291's
   V3.0.15 ids, all 21 m2 / m3 lines BLOCKED_RFI with no quantity.
2. Re-add one line by hand from register v4: GF 0.15 MAS.BLOCK 55.6585 (s.3), or 2F 0.20 43.1360 VERIFIED.
3. Re-check one wall's binding: 1F-W06 (1F, 0.20, VERIFIED 54.4860, Checker 02:03) -> L-5ffa7157a2fe483dd008; its
   m3 row 10.897200 = 54.4860 x 0.20.
4. The plinth containment: the GF wall course 0.05 m (+0.95 -> +1.00) inside the GF wall heights (T-311 s.4).
5. One parapet run's exclusivity: 1F NE-2 block 0 .. 19.0700 m2 in no line, RC part with T-319.

## 10. Rework r2 (D-T333-1, Checker 2026-10-29 13:30; worker 3 2026-10-29 19:03 UTC)

Defect: three ESTABLISHED PART + HELD walls carried part_status DRAWING-CONFIRMED although their established net
deducts a door at the Q-55 fallback height 2.20 m (no Alsenan sheet prints a door height except the main entrance;
OWNER_QUESTIONS_ANSWERED Q-55), while every whole wall with such a door was already ASSUMED — OWNER-APPROVED. Cause:
the label was inherited from the merged T-291 ledger, which takes part_status from the register v4 class of the wall,
not from the evidence of the deductions inside the part.

Physical reasoning: net = gross panel - DEDUCTED openings; the net's evidence is no stronger than its weakest term. A
door height that is an owner fallback makes the deducted area, and so the net, rest on that fallback.

Fix (R-T333-1 rule 6, binding_fill.py `apply_fallback_labels` / `check_fallback_labels`): every DEDUCTED opening of the
T-291 table gets a height basis (OPENING_HEIGHT_BASIS_T333.csv, 32 openings): ASSUMED — OWNER-APPROVED when T-175 gives
its height that status AND T-291 still deducts width x 2.20 (13 doors); otherwise the later drawing reading T-291 cites
(T-227 s.6 heights, T-261 split, T-274 / T-288 jambs) = DRAWING-CONFIRMED (19 windows; T-175 HELD heights there are
superseded and named). A part_status over a fallback deduction is lifted to ASSUMED — OWNER-APPROVED; a VERIFIED or
DRAWING-CONFIRMED status or part_status over one is refused (FALLBACK_HIDDEN); a DEDUCTED opening with no established
basis is refused (STATE_UNKNOWN).

| wall | established part m2 | door | deduction | part_status r1 -> r2 |
|---|---|---|---|---|
| 1F-W13 | 16.8073 | D-1F-08 | 0.90 x 2.20 = 1.9800 | DRAWING-CONFIRMED -> ASSUMED — OWNER-APPROVED |
| 1F-W17 | 4.6943 | D-1F-10 | 0.80 x 2.20 = 1.7600 | DRAWING-CONFIRMED -> ASSUMED — OWNER-APPROVED |
| 2F-W03 | 25.8850 | D-2F-01 | 1.00 x 2.20 = 2.2000 | DRAWING-CONFIRMED -> ASSUMED — OWNER-APPROVED |

Established parts by part_status after r2: ASSUMED — OWNER-APPROVED 47.3866 m2 (3 walls) + DRAWING-CONFIRMED 109.1831
m2 (7 walls, window-only or no opening) = 156.5697 m2 unchanged. Every m2 / m3 figure of r1 is unchanged: FILL_T333.csv
differs from r1 in 9 rows (3 walls x MAS.BLOCK / WALL_PANEL / WALL_VOLUME), column part_status only; WALL_TABLE in the
same 3 rows; LINE_BEFORE_AFTER, TYPE_BEFORE_AFTER, LINE_REBIND, COMPONENTS, CHECKER_VALUES byte-identical; the FILL
columns T-279 consumes are unchanged. Consistency now holds across the table: all 11 walls that deduct a Q-55 door
carry ASSUMED — OWNER-APPROVED in status or part_status.

Tests: villa M (normal: window-only part stays DRAWING-CONFIRMED, quantity 10.800; adverse: Q-55 door part 10.020 m2
labelled DRAWING-CONFIRMED or VERIFIED refused; whole wall VERIFIED over a Q-55 door refused; DEDUCTED opening with
basis None / HELD / UNKNOWN refused) and an Alsenan pin (the 3 walls, 47.3866 / 109.1831, all 11 Q-55 hosts labelled).

Lesson row (s.7, as the Checker proposed): 2026-10-29 | a deduction resting on an owner fallback height makes the net
ASSUMED — OWNER-APPROVED for a part as for a whole wall | normal: window-only part stays DRAWING-CONFIRMED; adverse: Q-55
door part labelled DRAWING-CONFIRMED -> refused.
