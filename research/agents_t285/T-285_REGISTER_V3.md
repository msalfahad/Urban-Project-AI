# T-285: blockwork wall register v3, one established register revision (development villa; every villa by R-T285-1)

Worker 2, claim 2026-10-25 00:45 UTC, lane A, gate 2. Base: working head aba9399a (T-274 MERGED). Read-only over the
merged ledgers: register v2 (T-228 r2, MERGED bf4dd2a9), T-274 (MERGED aba9399a), T-261 r3 (MERGED 164b189f), T-277
(MERGED 9446dfcb) and the Checker's whole-wall re-measures (SCOREBOARD BLOCKWORK row restated 2026-10-25 00:06). No
engine module, rule or knowledge file changed; no BOQ line moves; released default stays V2.9 + route G. The register
is a research revision for lane I (T-279) to carry, NOT RELEASED. Drawings behind every figure: Drive 'Alsenan chalet
project' / P7757_DXF_COMPRESSED.zip (P7757.dxf, sha ab54dd55) and 'ST7757 dxf.dxf' (sha 9f9d1179); no coordinate,
image or client name is committed.

ERS read: s.2.1 (physical element: the net installed block of one wall = block built under the members drawn over its
census length less the openings physically piercing it), s.2.4 (reconcile in m2 to named causes, residual named),
s.3 (build before deduct; installed vs procurement: block units / mortar stay T-176, not here), s.4 (rule + test),
s.7 row below.

## 1. The engineering question and the answer

Which net does each established wall carry once its height pieces close its census length, and does the whole register
move only by named causes? **Yes, it does: residual 0.0000 m2 on both steps.**

| Step | Net installed blockwork m2 | m3 (net x t) | Walls with a figure | Cause |
|---|---|---|---|---|
| Register v2 (T-228 r2) | 449.2600 | 80.674 | 37 | as merged |
| **v3 basis A** = v2 + T-274 piece closure | **449.5934** | 80.7296 | 37 | 15 walls, each by a named cause (table 2), +0.3334 |
| **v3 basis B** = A + T-261 r3 established parts | **625.8957** | 112.3571 | 48 | 11 v2-HELD walls get their drawn-extent established part, +176.3023 |

T-274 proposed 449.5651; the corrected figure is **449.5934 (+0.0283)**: GF-W22 and GF-W34 were left at register v2
by T-274 ("stay on their T-215 bounded range"), but register v2's figure for both lies BELOW every reading of the CB2
width conflict, so it is not a reading at all (section 3).

By evidence status (WORKFLOW_CONTROLS s.5; HELD never counted):

| Status (owner class) | basis A m2 | basis B m2 |
|---|---|---|
| VERIFIED (13 walls, Checker's own value) | **106.004** | 106.004 |
| DRAWING-CONFIRMED (SOURCE-SUPPORTED PENDING INDEPENDENT CHECK) | 258.2413 | 434.5436 |
| ASSUMED — OWNER-APPROVED (PROJECT-SPECIFIC: Q-55 C door head etc.) | 85.3481 | 85.3481 |
| HELD | 39 walls, no number | 28 walls no number + 10 walls with a HELD increment beside their established part |

**Finding for the Checker (arithmetic, SCOREBOARD BLOCKWORK row 00:06):** the VERIFIED share is **106.004 m2, not
105.004**. 95.633 (10 walls) + GF-W33 5.586 + 1F-W01 2.832 + GF-W12 1.953 = 106.004; the same row's split does not close
with 105.004 (SS 258.112 + 105.004 + PS 85.144 = 448.260 = 449.260 - 1.000) and closes with 106.004. All 13 Checker
values equal register v2's figures (no wall moved by the verification itself). Cause: a 1.000 m2 addition slip, not a
measurement; the register-wide identity VERIFIED + SS + PS = established is now asserted by a test.

## 2. Wall-by-wall changes, basis A (RECONCILIATION_V3.csv; before -> after m2, cause)

| Wall | v2 | v3 | Change | Cause |
|---|---|---|---|---|
| GF-W28 | 20.016 | 20.1384 | +0.1224 | exact pieces (B11 0.2006 drawn, not 0.26 sampled; slab / B13 / B17) (R-T274-1); Checker own gross 22.3386 (T-274 Gate A), net PROJECT-SPECIFIC (door 2.20 Q-55 C) |
| 1F-W00 | 12.863 | 12.9336 | +0.0706 | W18 deducted by its 0.4673 m inside the masonry x 2.160 = 1.0094, not 0.500 (R-T274-1 rule 5); deductions 9.806 -> 9.7354; Checker own 12.935 (0.0013 = census 6.571 vs run 6.5708 + rounding) |
| GF-W32 | 9.066 | 9.1294 | +0.0634 | exact pieces |
| GF-W16 | 15.404 | 15.4356 | +0.0316 | exact pieces (Checker own 15.436) |
| 1F-W20 | 24.477 | 24.5068 | +0.0298 | exact pieces: slab 1F-063 1.3062 + B19 0.4037 + slab 1F-023 4.4152 (Checker own 24.507) |
| 1F-W23 | 19.639 | 19.6578 | +0.0188 | exact pieces |
| **GF-W34** | 10.380 | **10.3982** | **+0.0182** | exact pieces (this task, section 3) |
| GF-W31 | 5.634 | 5.6455 | +0.0115 | exact pieces |
| **GF-W22** | 12.921 | **12.9311** | **+0.0101** | exact pieces (this task, section 3) |
| 1F-W06 | 54.487 | 54.4897 | +0.0027 | exact pieces |
| 1F-W12 | 11.582 | 11.5815 | -0.0005 | exact pieces |
| GF-W11 | 2.506 | 2.5050 | -0.0010 | exact pieces |
| GF-W19 | 8.605 | 8.5950 | -0.0100 | exact pieces (Checker 18:04: 8.595 drawn .. 8.612 schedule) |
| GF-W20 | 4.256 | 4.2398 | -0.0162 | exact pieces + T-215 junction close |
| 1F-W22 | 20.419 | 20.4010 | -0.0180 | exact pieces: CB11 0.1004 + slab 1F-084 4.8488 + the missed B4 0.1258 strip at 3.70 (Checker own 20.402) |
| **Total** | **449.260** | **449.5934** | **+0.3334** | residual 0.0000 |

By floor x thickness x type (BEFORE_AFTER_V3.csv), basis A: GF 0.15 black 84.872 -> 85.0431 (+0.1711); GF 0.20 white
32.551 -> 32.5816; 1F 0.15 black 89.039 -> 89.0691; 1F 0.20 white 103.967 -> 104.0403; every other group unchanged.
Basis B adds the T-261 parts: GF 0.20 white +39.1525, 1F 0.15 black +46.7743, 1F 0.20 white +44.774, 2F 0.15 white
+25.885, 2F 0.20 black +3.800, 2F 0.20 white +15.9165.

VERIFIED walls kept at the Checker's value even where T-274's exact pieces differ by a rounding (rule 2; listed, not
applied): GF-W07 4.458 (exact 4.4575), GF-W21 4.309 (4.3092), 1F-W01 2.832 (2.8316), 2F-W04 21.476 (21.4763); and the
VERIFIED gross of GF-W01 62.155 (T-143; exact 62.1541 + a 0.0026 m HELD alignment strip, at most 0.011 m2) and 1F-W05
23.223 (exact 23.2228). None exceeds 0.0009 m2.

## 3. GF-W22 and GF-W34: why register v2's figure is not a reading of the CB2 conflict

Physical element: two 0.15 black partitions that meet the north wall at junction J-A (T-215, G-T108-1); the last
0.0952 m (GF-W22) / 0.0596 m (GF-W34) of each run lies where the GF CB2 band (BM-GF-055) ends, drawn 0.250 wide,
scheduled W 20 (C-BEAM2 28C7; D-27 CONFLICT). Under the drawn width the junction piece stands partly under CB2 (h 4.00),
under the schedule width under the slab (h 4.34).

| Wall | Register v2 | Exact pieces (T-274 + T-215 merged junction bound) | Drawn reading | Schedule reading |
|---|---|---|---|---|
| GF-W22 | 2.982 x weighted 4.333 = 12.921 (= sampled base 12.521 + T-215 minimum 0.4003; base had a 0.04 m B1 'piece' from the 3 cm halo) | slab GF-027 2.8873 x 4.34 = 12.5309 + junction 0.4003 .. 0.4131 | **12.9311** | 12.9439 |
| GF-W34 | 10.380 (= sampled base 10.1352 + 0.2448; B3 sampled 0.36 m) | slab GF-015 1.7231 x 4.34 + B3 0.2846 x 4.10 + slab GF-027 0.3475 x 4.34 = 10.1534 + junction 0.2448 .. 0.2587 | **10.3982** | 10.4121 |

Register v2's figures (12.921, 10.380) lie below BOTH readings: the conflict does not explain them; the sampled base
does (the same defect T-274 found on 40 walls). v3 carries the part present in EVERY reading (the drawn reading here)
and the CB2 increment 0.0128 / 0.0139 m2 as a named CONFLICT, never added. Hand check for the Checker: GF-W34
1.7231 x 4.34 = 7.47825, 0.2846 x 4.10 = 1.16686, 0.3475 x 4.34 = 1.50815 -> 10.15326 + 0.2448 = 10.3981 (+ 0.0001
rounding of T-274's 4-decimal pieces) .. 10.4120.

## 4. Width CONFLICTs carried with both readings (T-277; R-T285-1 rule 3)

| Wall | Band (designer item) | Readings m2 (figure) | Established (every reading) | CONFLICT increment |
|---|---|---|---|---|
| GF-W19 | CB2 drawn 0.25 / W 20 (D-27) | drawn 8.5950; schedule, face kept 8.5950; face moved 8.6120 | 8.5950 | 0.0170 |
| GF-W20 | CB2 (D-27) | 4.2398 / 4.2398 / 4.2568 | 4.2398 | 0.0170 |
| GF-W22 | CB2 junction (D-27) | 12.9311 / 12.9439 | 12.9311 | 0.0128 |
| GF-W34 | CB2 junction (D-27) | 10.3982 / 10.4121 | 10.3982 | 0.0139 |
| 1F-W16 (HELD wall: B6 depth, A-1F-01 head) | B6 drawn 0.20 / W 25 (D-27) | gross figure drawn 21.8288; schedule 21.8118 | figure only | 0.0170 |
| 1F-W11 (HELD wall: dome opening 1F-073) | CB10 drawn 0.30 or 0.20 / W 25 (D-02) | established-part figure 0.6432 / 0.6432 / 0.6602 | figure only | 0.0170 |

On established walls the CONFLICT increments total **0.0607 m2** (not in the 449.5934); T-277's -0.017 .. +0.034 m2 was
stated against register v2's sampled pieces; on the exact-piece basis the drawn reading is the lower one on the GF CB2
walls and the higher one on 1F-W16 (B6 drawn narrower than scheduled), so the established figure is never the reading
that adds block the other reading does not have. Rule: established = the part in every reading (no reading chosen, the
increment is carried by name; a reading alone or two unnamed readings are refused).

## 5. T-261 r3 established parts (basis B; T261_SPLIT.csv, Checker 18:56 11 / 11 own-agreed)

GF-W10 39.1525 (+ stair-foot piece 2.500 m HELD, W.C. 0 .. 0.945), 1F-W10 36.929 (+ B3 shaft piece HELD), 2F-W02
9.6915 (+ 3 HELD), 1F-W04 7.845 (+ BM-1F-032 0.800 m HELD, D-04), 2F-W03 25.885 (+ 3 HELD), 2F-W07 6.225 (+ 2 HELD),
2F-W05 3.800 (+ 2 HELD), 1F-W18 19.7326 (whole, nothing held), 1F-W24 5.5401 (+ dome opening 1.05766 m HELD), 1F-W13
16.8073 (+ 3 HELD), 1F-W17 4.6943 (+ 2 HELD) = 176.3023 m2. Each wall carries its established part and its HELD
pieces by name (state ESTABLISHED_PART_PLUS_HELD), never the gross figure. Status SOURCE-SUPPORTED (the Checker agreed
the figures at Gate A but has not entered them in the VERIFIED share; this register does not promote them).

## 6. What lane I gets (REGISTER_V3_EXPORT.json)

One record per wall (76): wall id, floor, block type, thickness, state (ESTABLISHED / ESTABLISHED_PART_PLUS_HELD /
HELD), owner class and evidence status, basis (A / B), net m2 and m3 (null when HELD), held items by name, the CONFLICT
text and increment, the Checker run for VERIFIED walls; declared totals for both bases by class; the sha256 of the
register CSV. Values only; the item-code mapping, scope accounting and Gate B stay with T-279. Procurement (block units,
mortar) is not in the register (installed vs procurement, ERS s.3; T-176 PROVISIONAL).

## 7. Engine vs freelancer (comparison only, programme s.5)

The freelancer has no per-wall row (one height per floor, parapets / fence / projections inside his sections), so no
total verdict while 28 walls are wholly HELD. Section level as T-228 / T-261 stated (engine basis B vs his net):
1F internal 0.15 135.843 vs 195.098 m2 (-59.255, -30.4 %; 3 walls still HELD, his 66.00 parapet in the section);
GF external 0.20 white + black not like for like (10 walls HELD). WHO IS RIGHT on the 15 changed walls: RULE_DIFFERENCE
(piece heights by the printed member, Q-60 A, vs his one height per floor); GF-W22 / GF-W34 / GF-W19 / GF-W20 CONFLICT
increments UNRESOLVED (designer D-27), never chosen.

## 8. Rule, tests, lessons row

- **R-T285-1** (register_v3.py, any villa): (1) a figure from pieces only when they close the census (R-T274-1);
  (2) a Checker-VERIFIED value is never replaced by a lower class (difference listed; explicit replace refused);
  (3) a width CONFLICT carries every reading by name, established = the part in every reading, increment by name;
  (4) HELD carries no number, never 0, always named; (5) register after - before = sum of named causes, residual
  <= 0.00005 m2; (6) one wall once.
- **tests/t285_register_v3** (23): villa R (not Alsenan) hand truth: R-W1 exact pieces 17.115, jamb 0.04 m inside the
  column -> 0.86 x 1.20 = 1.032 deducted -> 16.083 (mirror equal); R-W2 drawn 10.2625 / schedule 10.2800 -> 10.2625 +
  CONFLICT 0.0175; R-W3 VERIFIED 13.800 kept over 13.795; register 40.0495 -> 40.1455 = +0.027 +0.048 +0.021, residual 0.
  Adverse: piece list not closing, sampled pieces over the census, millimetres, VERIFIED overwrite, conflict collapsed /
  unnamed, held as 0 / unnamed / as a number, established 0, unnamed / duplicate cause, wall twice: all refused.
  Alsenan: --check reproduces; totals and residuals; 13 VERIFIED walls at the Checker's values = 106.004; named walls;
  every CONFLICT wall has a drawn and a schedule reading; HELD never 0; export = register; no coordinates.
- Lessons row (proposed, ERS s.7): 2026-10-25 | A register correction was proposed but left two walls on a figure
  below every reading of their own width conflict (GF-W22 / GF-W34, +0.0283 m2) and a status total was mis-added by
  1.000 m2 (VERIFIED 105.004 for 106.004) | a bounded wall was skipped as 'range, not moved' without testing whether the
  register figure is one of the readings; class totals were kept by hand | a register revision applies every closed
  piece list; a figure outside all readings of a conflict is a defect, not a range; established = part in every
  reading, increment by name; VERIFIED + SS + PS = established is asserted (any villa; blockwork, plaster, paint
  registers) | tests/t285_register_v3 | PROPOSED.

## 9. Still HELD (by name) and what is missing

28 walls wholly HELD (annex datum Q-54 B / D-39, lift tie beam ST p.8 n.19 / D-43, undrawn opening heads, unprinted
member depths D-03 / D-04, dome opening 1F-073, the glazed strips GF-W37 / GF-H01 / GF-H02, GF-W36 face GF-112) and the
HELD pieces of the 10 split walls: unchanged from register v2 / T-261 / T-274, named on each row. The Checker may
promote to VERIFIED, after its own wall-by-wall re-measure, the walls whose own figure already agrees: 1F-W20 24.507,
1F-W22 20.402, GF-W16 15.436, 1F-W00 12.935 (register 24.5068 / 20.4010 / 15.4356 / 12.9336); this register does not.

Reproduce: `python3 -I research/agents_t285/build_t285.py --check`.
