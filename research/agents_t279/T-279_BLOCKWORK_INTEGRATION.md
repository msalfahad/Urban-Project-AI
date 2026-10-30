# T-279: the established blockwork walls in the candidate (ARCH_TAKEOFF_V3.0.26), integration package for Gate B

Worker 3 (lane I), 2026-10-30 05:01 - UTC. Development villa, not an accuracy claim. Opt-in candidate only: the
released default stays ARCH_TAKEOFF_V2.9 + route G; nothing is released. No client name, coordinate or image is
committed; drawings are cited by Drive title only.

integrates: T-333 r2 (MERGED bb54c5d6, Verifier 2026-10-29 20:54 Gate A r2: the wall-by-wall FILL on the 28 masonry
line ids, Q-55 door parts ASSUMED - OWNER-APPROVED), T-291 (MERGED 0c6b2ba5, wall -> line binding), T-288 (MERGED
643b310b, register v4), T-261 r3 (MERGED 164b189f, wall-by-wall split), T-274 (MERGED aba9399a, piece closure). The
per-wall VERIFIED statuses are the Checker's own T-180 re-measures (2026-10-24 15:27 .. 2026-10-25 02:09), named per
wall. Inputs: `research/agents_t279/t279_inputs.py` reads FILL_T333.csv, LINE_BEFORE_AFTER_T333.csv,
OPENING_HEIGHT_BASIS_T333.csv and CANDIDATE_V3021_MASONRY_LINES.json, each pinned by sha256; nothing is typed.

## 1. The physical question and the answer (ERS s.2.1)

A block wall is the masonry between its two faces from the structural floor to the underside of the member over it,
less the openings built into it, each opening once by id (Q-60 A, R-T274-1, R-T288-1, R-T261-1 rule 9). The
candidate's masonry lines are per storey x wall thickness x item: MAS.BLOCK m2 (the material line), ARCH.WALL_PANEL m2
(the panel geometry, the SAME area: not additive with MAS.BLOCK) and ARCH.WALL_VOLUME m3 (= m2 x t). Since V3.0.15 the
21 m2 / m3 lines were BLOCKED_RFI with no quantity. A line is the sum of its walls; a wall is released only at the
status of its own evidence; a line whose walls are not all closable stays HELD blank and its closable walls are not
lost (owner 2026-10-22 16:35; the V3.0.18 split convention). So:

- each held parent line stays BLANK in place (same line id) and names every wall still HELD with its item, every
  drop wall with its terms U - L x d (never evaluated, never a range), every held piece of a part-established wall,
  every width-CONFLICT increment (outside every total), and the line ids that now carry its closable walls;
- each (status, block type) group of closable walls becomes its OWN line: VERIFIED / DRAWING-CONFIRMED ->
  SOURCE_DERIVED, ASSUMED - OWNER-APPROVED -> PROVISIONAL with Q-55 C named; each wall is a named piece (WHOLE, or the
  ESTABLISHED_PART of a wall whose other piece is held). Block type is a material classification (white AAC vs black
  cement block, priced apart), so one type per line.

Rule **R-T279-1** (engine/source/arch_v3026.py, every villa): a fill replaces only a HELD blank line; one line per
wall per item; held / drop walls carry no figure; VERIFIED names its checker run, OWNER-APPROVED its answered
decision; m3 = m2 x t and WALL_PANEL = MAS.BLOCK wall by wall; the merged fill's per-line figures are reproduced wall
by wall; a part never sits under a parent with a figure; every other line byte-identical.

## 2. BOQ lines (V3.0.25 -> V3.0.26)

Every line before is BLOCKED_RFI BLANK (V3.0.25 = V3.0.15 for these 21 lines: ids, states and text unchanged, T-333
s.1). After: the parent stays BLANK (text restated: CHANGED_TEXT_ONLY), the parts are 57 new lines (ADDED). Released
V2.9: all 21 lines BLOCKED_RFI blank as well (SAME_QUANTITY: blank); the 57 parts are NOT_IN_RELEASED. Line-by-line
diff: V3_0_26_DIFF.csv (3,775 rows: 3,697 SAME, 21 CHANGED_TEXT_ONLY, 57 ADDED against V3.0.25; against V2.9 2,185
NOT_IN_RELEASED, 899 QUANTITY_DIFFERS, 691 SAME_QUANTITY, of which this package adds only the 57 NOT_IN_RELEASED).

| Parent line | Item | Storey / t | Before | After: part lines (status, type, value) | Released on parts | Drop on parent (blank) | Held items named |
|---|---|---|---|---|---|---|---|
| L-0d9b9e89bb6455da475d | MAS.BLOCK m2 | GF 0.15 | BLANK | VER BLACK 9.895; DC BLACK 21.5261; OA BLACK 24.2374 | 55.6585 | 29.4129 - 4.5131 d | 6 walls, 4 drop, 4 conflict incr. |
| L-4165954ce4871eda30cc | MAS.BLOCK m2 | GF 0.20 | BLANK | VER BLACK 62.164; VER WHITE 4.458; DC WHITE 44.2975; OA WHITE 5.59 | 116.5095 | 17.389 - 3.4 d | 16 walls, 1 piece, 2 drop |
| L-ff06449b7f61f19c418d | MAS.BLOCK m2 | GF 0.40 | BLANK | none | - | - | GF-H01 |
| L-c22e309433e7b671cf2d | MAS.BLOCK m2 | 1F 0.15 | BLANK | VER BLACK 52.318; DC BLACK 25.2727; OA BLACK 58.2529 | 135.8436 | - | 3 walls, 3 pieces, 2 conflict incr. |
| L-5ffa7157a2fe483dd008 | MAS.BLOCK m2 | 1F 0.20 | BLANK | VER BLACK 23.9; VER WHITE 101.976; DC WHITE 46.836 | 172.712 | - | 1 wall, 2 pieces |
| L-246f3c09de4c6b90efe5 | MAS.BLOCK m2 | 2F 0.15 | BLANK | OA BLACK 9.64; OA WHITE 25.885 | 35.525 | - | 1 piece |
| L-afe984a62285e133ec2f | MAS.BLOCK m2 | 2F 0.20 | BLANK | VER BLACK 21.66; VER WHITE 21.476; DC BLACK 3.8; DC WHITE 15.9165 | 62.8525 | - | 1 wall, 3 pieces |
| **MAS.BLOCK total** | | | **BLANK** | **VER 297.847 (18 walls) + DC 157.6488 + OA 123.6053** | **579.1011 m2** | **46.8019 - 7.9131 d** | **28 walls HELD, 10 pieces, 6 drop, 6 incr.** |
| ARCH.WALL_PANEL (7 lines) | m2 | same | BLANK | the same parts and values as MAS.BLOCK, wall by wall | 579.1011 m2 | 46.8019 - 7.9131 d | same |
| ARCH.WALL_VOLUME (7 lines) | m3 | same | BLANK | m2 x t per wall (e.g. GF 0.20 VER BLACK 12.4328 = 62.164 x 0.20) | 104.468865 m3 | 7.889735 - 1.356965 d | same |

Per status (MAS.BLOCK): VERIFIED 297.847 (whole walls only); DRAWING-CONFIRMED 48.4657 whole + 109.1831 established
parts = 157.6488; ASSUMED - OWNER-APPROVED 76.2187 whole + 47.3866 parts = 123.6053 (every one deducts a Q-55 C door
at 2.20 m: D-1F-02 / -03 / -04 / -07 / -08 / -10, D-2F-01 / -03, D-GF-06 / -10 / -13). Per block type: WHITE 0.20
240.5500, BLACK 0.20 111.5240, BLACK 0.15 201.1421, WHITE 0.15 25.8850 m2 (= T-333 TYPE_BEFORE_AFTER determinate +
established parts). Volume: determinate 75.801260 + parts 28.667605 = 104.468865 m3 (m3 never added to m2).

Basis named apart (T-291 s.3): the released parts are **basis B 579.1011** (determinate 422.5314 + the established
parts 156.5697 of the 10 part-established walls, each with its held piece named); basis A 402.7988 (VERIFIED +
OWNER-APPROVED + the 28.7331 DC of basis-A walls) is the narrower register-v4 reading, shown here, never mixed in a
line.

## 3. Owner manual method and drawing-derived method side by side

| | Owner manual method | Drawing-derived (carried) |
|---|---|---|
| Wall area | wall length x one storey height less openings (one height per storey; parapets and fence inside the 15 cm section, as the freelancer's workbook) | per wall: face length x height from the structural floor to the soffit of the drawn member over it, piece by piece; each opening once by id; a piece with no drawn top HELD; under a sunken panel U - L x d |
| Difference | not carried (no answered owner rule measures blockwork by one storey height) | carried: T-333 / T-291 / T-288 per wall |

## 4. Against the freelancer (BLK workbook; not proof)

Freelancer 1,260.69 m2 (exterior 559.80 + 15 cm 617.25 + 20 cm 83.64; one height per storey; parapets and fence in
his 15 cm). Candidate after this package: 579.1011 m2 released on parts + 46.8019 - 7.9131 d on drop walls + 28 walls
HELD blank + parapet block alternative 0 .. 60.5965 m2 (in no line, Q-65 C) + the boundary fence (not in a masonry
line). No total verdict while 28 walls, 10 pieces and d are HELD: **UNRESOLVED** at line level; per wall the T-333 /
T-291 verdict proposals stand (ENGINE_BLOCKED / REGISTER_DETERMINATE; parapet RULE_DIFFERENCE on height). The
released share is 45.9 % of his figure, which is a coverage statement, not an accuracy one.

## 5. Evidence status, missing and held

- VERIFIED 297.847 m2 on 18 walls (each with its Checker run); DRAWING-CONFIRMED 157.6488; ASSUMED - OWNER-APPROVED
  123.6053 (Q-55 C); HELD: 28 walls + 10 pieces BLANK by name; drop 46.8019 - 7.9131 d (D-41) never evaluated;
  width-CONFLICT increments 0.0947 m2 named on the parents, outside every total. UNKNOWN: none in these lines.
- Not in this package: procurement (block units, mortar: PROVISIONAL, T-176), masonry accessories (T-363 after
  T-362), parapet blockwork alternative (Q-65 C, exclusive with the T-319 RC lines), the 7 ARCH.WALL_RUN lm lines
  (unchanged, PROVISIONAL band geometry).
- Plinth course 5.0593 m2 is CONTAINED in the GF 0.20 walls (T-333 s.6): added nowhere.

## 6. Downstream consistency (cross-trade, double count)

- MAS.BLOCK and ARCH.WALL_PANEL carry the same area by construction (material line and geometry line of one element,
  as before V3.0.15): the module asserts their parts equal wall by wall; a priced BOQ prices MAS.BLOCK only.
- Plaster / paint / tiles / skirting lines are measured from faces and rooms (V3.0.19 - V3.0.22), not from these
  lines: no line outside the 21 parents and their parts moves (asserted: totals moved only on MAS.BLOCK,
  ARCH.WALL_PANEL, ARCH.WALL_VOLUME).
- Concrete: walls stop at the soffit of the member over them (beams / bands are concrete lines); W18 is inside VERIFIED
  1F-W00, W03 inside glazed GF-W37: no opening deducted twice (T-291 s.4).

## 7. Validation

- Own Drive copies this run ('Alsenan chalet project': P7757_DXF_COMPRESSED.zip -> P7757.dxf `ab54dd55`, 'ST7757
  dxf.dxf' `9f9d1179`), decoded into the private folder only; fresh T-167 base run, then the full CLI run
  `research/agents_t279/v3026_run.py` (`tools/urban_boq_m9.py arch --method ARCH_TAKEOFF_V3.0.26 --v3026-inputs`):
  **V3_0_24 json 19394733 and V3_0_25 json 3064078a / csv 97d6e749 reproduced (= the candidate of record, T-343 r2
  Gate B)**; V3_0_26 = `v3026_direct.py` on the same V3.0.25 byte for byte (all 7 files). Final hashes in the board
  handoff. Identity: 3,718 -> 3,775 lines, 21 replaced (text / state only, asserted), 57 added, 3,697 byte-identical.
  Totals moved only on MAS.BLOCK m2 (0 -> 579.1011), ARCH.WALL_PANEL m2 (0 -> 579.1011), ARCH.WALL_VOLUME m3 (0 ->
  104.468865); held lines 7 per code stay blank. Line-state check (T-334 tool) over all 3,775 lines: 3,775 OK, flagged 0,
  refused 0 (V3.0.25: 3,718 OK, the same 5 NOTE_OPEN_RFI_ON_VALUED notes).
- tests/t279_blockwork_integration (33): villa P279 by hand (not Alsenan), normal (parts, states, parent held list,
  m3 = m2 x t, panel = block, outside lines byte-identical, order invariance, files / diff / totals) and adverse (held
  wall as 0, drop evaluated, wall in two lines, VERIFIED without run, OA without source, wall at 0, m3 at the wrong t,
  panel != block, declared figure not reproduced, mm thickness, unknown status, parent with a figure, stale line,
  applied twice, part under a parent with a figure, wall released twice); Alsenan pins (merged ledgers, totals, Q-55,
  Checker values, edited ledger stops the build); master 1.21.0 (builder, checks clean, dropping the entry is stale).
- L4 full suite `tests/` on 5c2134c6: 396 failed / error in 43 files = the known private-input / environment set of
  the T-343 r2 base record (396 in 43 files); the two code-level ones (t212 live tree: tools/label_census_v2.py
  unclassified; r8_0 B5/B6 registry) fail identically on the base 90135e91 (messages compared); NEW 0. After the final
  RFI-text change (arch_v3026 only): t279 / t343 folders re-run, freeze 0, codemap stale none.

## 8. For the Checker (Gate B always-checked lines)

Every part line is a new released quantity of a structural-adjacent trade, so every part line >= 2 % of the masonry
total is hand-checked by rule. Suggested re-adds (register v4 / T-333 WALL_TABLE): GF 0.15 VER BLACK 9.895 = GF-W21
4.3090 + GF-W33 5.5860; 1F 0.20 VER WHITE 101.976 = 1F-W00 12.935 + 1F-W01 2.832 + 1F-W05 19.303 + 1F-W06 54.486 + 1F-W08
12.420 (1F 0.20 VER BLACK 23.900 = 1F-W02 2.660 + 1F-W03 14.400 + 1F-W09 6.840; DC WHITE 46.836 = 1F-W00/W01 BAY-ENDS
0.572 + 1F-W04 part 7.845 + 1F-W10 part 36.929 + 1F-W25 1.490); 2F 0.15 OA WHITE 25.885 = 2F-W03 established part (door D-2F-01
1.00 x 2.20 Q-55); the m3 = m2 x t of one line; one parent's held list against FILL_T333.csv.

## 10. Lessons-register row (proposed)

| 2026-10-30 | 21 blockwork lines stayed BLANK in the candidate for six versions while 579 m2 of their walls were measured and Checker-merged wall by wall (T-261 .. T-333) | the fill was a research ledger keyed by line id, and no integration step consumed it; a mixed line (some walls closable, some held) has no single honest figure | a held line with closable walls is split: the parent stays BLANK with every held wall / drop term / piece named, each (status, block type) group of closable walls is its own line, each wall once per item; m3 = m2 x t and the panel = the block wall by wall (every villa) | tests/t279_blockwork_integration (normal: villa P279 parts 12.900 / 22.800 / 7.240 / 11.200; adverse: held wall as 0, drop evaluated, wall in two lines, VERIFIED without run, OA without source, m3 at the wrong t, panel != block, stale / twice / parent with a figure) | PROPOSED |
