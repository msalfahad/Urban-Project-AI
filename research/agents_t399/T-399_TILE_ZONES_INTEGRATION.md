# T-399: B4-02 kitchen / laundry / pantry tiled zones into the SAME candidate (ARCH_TAKEOFF_V3.0.34; integration package, Gate B)

Worker 3 (lane I), claim 2026-10-31 21:00 UTC. Development villa, not an accuracy claim; NOTHING RELEASED; the released
default stays ARCH_TAKEOFF_V2.9 + route G (rollback: run V2.9). Drawings named by Drive folder and title only.
integrates: T-351 (MERGED f0bd9f3c), T-388 (MERGED df170b8d). Candidate of record at claim: V3.0.33 (T-397 MERGED
4492fd59), reproduced here byte for byte (V3_0_33_BOQ_LINES.json `a545c5b3`, csv `ba95c03d`).

## 0. Sources and runs

Drive folder "Alsenan chalet project": 'ST7757 dxf.dxf' (sha256 `9f9d1179`), P7757_DXF_COMPRESSED.zip -> P7757.dxf
(`ab54dd55`), decoded into `.work/private` only. Own chain run on the task head (Python 3.11.18):

```
python3 -I research/agents_t167/v304_run.py <P7757.dxf> <ST7757 dxf.dxf> --out <private>/t167
python3 -I research/agents_t399/v3034_run.py <P7757.dxf> <ST7757 dxf.dxf> --out <private>/t399 --t167 <private>/t167
python3 -I research/agents_t399/t399_summary.py <private>/t399/v3034 --write
```

Inputs: `t399_inputs.py` builds URBAN_V3034_INPUTS_V1 ONLY from merged files pinned by sha256 (T-351
CROSSCHECK_T351.csv `76f6fd4c`, ZONE_LEDGER_T351.csv `51ad2903`; T-388 report `e3d569fb`); it refuses a zone face that
is not full-height / host-wall bound to a wall-tile line, face lengths that do not close to the cross-check, and any
B4-02 face or overlap in the table. The module refuses a carrier that does not stand in V3.0.33 as bound (stale).

## 1. The physical element and what the candidate now says (ERS s.2.1)

B4-02 is porcelain / ceramic on the WALL FACES of a kitchen, laundry or pantry. Two physical readings exist (T-351 s.2):
full-height wall tile, or a splashback band behind the counter. The owner rules decide which is built: UP-WET-001 1.1.0
(wet codes KITCHEN / PANTRY / LAUNDRY: full-height wall porcelain, paint none), UP-FIN-WALL-001 1.8.0, Q-37 A, Q-48 A,
UP-PANTRY-001 .. 004. Under them the zone of these three rooms IS the full-height wall tile, which the candidate already
carries once per room as a FIN.WALL.TILE line (B4-01). **A B4-02 line on top would count the same tile twice**, so the
integration is a coverage binding, not a new quantity (R-T351-2, R-T399-1).

| Room (engine room) | Zone faces (T-351, Checker re-measured) | Carrier FIN.WALL.TILE line, V3.0.33 = V3.0.34 | Own table | Backing (plaster) | Paint lines of the room | Evidence status |
|---|---|---|---|---|---|---|
| Kitchen GF-06 (GF-RA3AD49) | 9 faces, 14.500 m | L-c330b8dc BLOCKED_RFI blank | HELD | L-595181aa BLOCKED_RFI blank | L-5587711f NA (unchanged) | HELD: annex owner height G2 / Q-54 B, D-39 |
| Laundry 1F-07 (1F-R26FA0D) | 9 faces, 16.940 m | L-b2077eee **52.5290 m2** | 52.5290 (residual 0.0000) | L-2948639f 52.5290 | L-7878bf61 NA (unchanged) | ASSUMED — OWNER-APPROVED (Q-48 A) |
| Pantry GF-07 (GF-RC06FED), open | 5 host faces 10.500 m + open edge 4.500 m (nothing) | L-f5c5a1a9 **32.3422 m2** | 32.3750 (**+0.0328 m2, +0.10 %**, named F-T351-1) | L-721a0f14 32.3422 | L-d2134def NA (unchanged); **L-c3f7e68c BLOCKED_RFI -> NOT_APPLICABLE_WITH_EVIDENCE** | ASSUMED — OWNER-APPROVED (Q-37 A, Q-48 A, UP-PANTRY-003) |

Zone total on the carriers: 52.5290 + 32.3422 = **84.8712 m2** valued (unchanged), kitchen HELD (never 0). B4-02 lines
added: **0**. Faces in a B4-02 zone and in a second tile line: **0 (0.0000 m2)**.

The one line change: the pantry paint line HL:WALL_FINISH:GF_07:PAINT stood BLOCKED_RFI blank with the V3.0.9 hold "whether
plaster is laid under that tile is not an owner rule yet". That question was settled by T-329 / T-331 (the backing
line under the tile, V3.0.22); for paint the owner method itself reads "WET room: tile, not plaster / paint", the tile
reaches the coat top on every host face (Q-43 = Q-48 A: band above the tile 0, T-329), the open edge carries nothing
(UP-PANTRY-003) and the dining-side lines stop at the VIRTUAL edge (T-351 check c, 0 pantry faces in the GF-08 lines).
The paint under the zone is therefore reduced by exactly the zone, i.e. to nothing: NOT_APPLICABLE_WITH_EVIDENCE, the
same state the kitchen's and laundry's 'paint above wall tile' lines already carry. No quantity appears or disappears
(the line was blank); T-388 named it as finding (d).

## 2. Methods side by side (ERS s.2.2)

| Room | Owner manual method | Drawing-derived method | V3.0.34 |
|---|---|---|---|
| Kitchen | full-height wall tile, 14.500 m x owner height (annex height not established) | splashback behind the drawn L counter, host 5.150 m, band not printed | HELD (both) |
| Laundry | 16.940 x 3.35 - D-1F-05 1.980 - D-1F-06 1.760 - W21 0.480 = 52.5290 m2 | nothing drawn to host a band (0.000 m) | 52.5290 on the wall-tile line |
| Pantry | host walls whole: 10.500 x 3.65 - 5.950 = 32.3750 m2 (own); line 32.3422 (walk 10.491 m) | counter backs 5.916 m, band not printed | 32.3422 on the wall-tile line, residual named |

The difference between the two methods is a different physical element (full wall vs band), not a measurement error;
the owner rule names these rooms and no sheet prints a band (T-091), so ERS s.2.7 is not met: no owner question.

## 3. The pantry residual F-T351-1 (not applied, and why)

The Checker confirmed the own vector reading 10.500 m against the line basis 10.491 m (+0.009 m x 3.65 = +0.0328 m2,
+0.10 %) "for the integration row". It is **not applied** here, by decision:

- the tile line and its backing are composed face by face from the T-250 walk (six pieces: GF-W01 2.995, GF-W05 1.955,
  GF-W16 4.475, OFF:COLUMN 0.900, OFF:WALL 0.165, residual 0.001 m), each with its own openings; the T-351 reading splits
  the room differently (west 4.450, column 0.900 + 0.050, north 2.100, south 3.000). A room-level +0.0328 m2 has no face
  to land on without re-walking the faces, and per-face ledgers downstream (T-349 spatter binding, T-368 edges) cite the
  walk pieces;
- T-388 (d') names a second, opposite pantry residual on the open side (-0.120 m -> -0.438 m2, T-390 traced);
- the residual is under the Gate B 1 % rule and the module refuses a residual above 1 % of the line.

So the binding carries the residual by name (ledger column residual_m2, WAITING PANTRY_FACE_REWALK_F_T351_1) and
proposes a face-by-face re-walk for the Lead; the line stays at its verified V3.0.33 figure.

## 4. Engine vs freelancer (his figures stay private; from the merged T-351 reconciliation)

| Item | Freelancer | V3.0.34 | Difference |
|---|---|---|---|
| Laundry wall tile (his 'wet rooms and kitchens' row) | 50.550 m2 | 52.5290 m2 | +1.979 m2 (+3.91 %): length +0.270, height (Q-48 A 3.35 vs his 3.00) +5.929, openings -4.220; residual 0.000 |
| Kitchen wall tile | 43.050 m2 | HELD | not compared (annex height) |
| Pantry wall tile | no row | 32.3422 m2 | ENGINE_RIGHT on scope (Q-37 A + UP-PANTRY-003) |
| Splashback / B4-02 band | no row | no line | AGREE (both carry these rooms as tiled walls) |
| Pantry paint | (not his item) | NA (was blank) | no quantity effect |

Verdict proposals: B4-02 scope AGREE (no separate band item); laundry height RULE_DIFFERENCE; openings ENGINE_RIGHT;
pantry scope ENGINE_RIGHT; pantry paint NOT_APPLICABLE ENGINE_RIGHT (UP-WET-001 paint none).

## 5. Gate B data (WORKFLOW_CONTROLS s.1)

- Run of record (task head 1c4a7fba code; the later commits are the registry, summary, maps and a research-only merge):
  V3_0_33 json `a545c5b3` / csv `ba95c03d` (= the T-397 Gate B candidate of record, REPRODUCED); V3_0_34 json `4c7f581c`
  / csv `4ba5bbe1`, DIFF `3b6caeee`, LEDGER json `80d1954b`; the committed module re-applied to the run's V3.0.33
  lines gives `4c7f581c` again. Lines 4,690 -> 4,690: **SAME 4,689 (byte-identical), CHANGED 1, ADDED 0, REMOVED 0**.
- Totals: every valued and held total identical; only FIN.PAINT|m2 counts move (lines 15 -> 14, blocked 4 -> 3: an NA
  line leaves the code totals); released 217.2081 m2, held 487.121 .. 542.8606 m2 unchanged (asserted by the module).
- vs released V2.9: the changed line is NOT_IN_RELEASED (V2.9 has no HL room-face lines); V2.9 unchanged (owner only).
- Always-hand-check set (s.1 rule 2): the pantry paint line (material / state classification change); the three zone
  bindings (new scope mapping: carrier, backing, paint per room); the pantry residual (unit / dimensional basis).
  No line moved by 5 % or more; no quantity moved at all.
- Re-measure list (sources): laundry contour B0F / B12 / B14 / B07 / ACF / D315 / d220 C1A (16.940 m); pantry host faces
  AE / AF / B0 / 2FAE / 158 / 159 / A6 (10.500 m), DIMENSIONS 5D5 3000 / 5C9 4500; pantry window heads W09 / W10 2.50 <
  3.65 (tile top) so no band above the tile (P7757.dxf; T-201 heads).
- Regression: see section 8 (L4).

## 6. Downstream and double count

- Plaster: the only valued FIN.PLASTER line on each zone room is its tile backing (same faces, same figure as the
  carrier; asserted); the pantry's base plaster L-6470c6f2 and paint L-d2134def stay NOT_APPLICABLE (V3.0.9).
- Paint: no valued paint line on any zone room (asserted); one blank line closed as NA.
- Waterproofing (FIN.WP.*), skirting (NA), floors, ceilings: no line names a zone face; unchanged.
- Coverage registry: BOQ_FAMILY_MASTER 1.29.0 = 1.28.0 + pending V3.0.34 + B4-02 `coverage_in_candidate` =
  COVERED_BY_B4-01 (pending, file:line evidence engine/source/arch_v3034.py:243-297 and :300-349). Released capability
  stays NOT_IMPLEMENTED and the candidate state NOT_IN_CANDIDATE until the merge (rule r3); a printed band or a kitchen
  open to a dry plan stays a real B4-02 line to build.

## 7. Rule and lessons row (proposed, ERS s.7)

R-T399-1 (engine/source/arch_v3034.py). | 2026-10-31 | A 'missing' family (B4-02) whose physical layer the owner wet
scope gives to B4-01 could have been integrated as a second quantity (84.87 m2 valued + the held kitchen twice), and a
paint line under a full-height zone stayed held after its cause was settled | the family list names an estimating item;
a hold reason outlives the rule that settles it | integrate such a family as a COVERAGE binding by room / face id to the
carrier line (stale carrier, unnamed residual or residual > 1 % stops; held stays blank); the paint and plaster of zone
faces are reduced by exactly the zone: paint NA only when the zone reaches the coat top on every face of that line,
plaster only as the backing (scope every villa; provenance T-399) | tests/t399_tile_zones (hand villa V399: kitchen
14.40 x 3.35 - 1.98 - 1.44 = 44.820 m2, open pantry 4.40 x 3.65 = 16.060 m2 with a named 0.0100 residual, held laundry;
adverse: stale carrier, unnamed / material residual, printed band, held zone valued, held carrier with a figure, valued
paint or ordinary plaster on a zone, second tile line, backing not the carrier, paint row on a dry room, plaster row,
valued paint row, stale paint binding, unmerged source, room in two zones, band above the tile, applied twice, change
outside the rows, a B4-02-like line present) | PROPOSED |

## 8. Validation

- tests/t399_tile_zones: 25 (module) + 9 (registry 1.29.0) pass; t397 (incl. the 1.28.0 stale-drop test, now accepting
  a newer registry that carries the dropped entry unchanged, the 1.26.0 / 1.27.0 pattern), t284, t328, t130, t203, t315,
  t351, t388 pass on the task head.
- L4 full suite: (result added below).
- selfcheck PASS (codemap, t061, freeze 0) at run start; freeze and codemap check on the final head: (below).

## 9. Not done / uncertain

- F-T351-1 pantry +0.0328 m2: named, not applied (section 3); proposal: a face-by-face re-walk task binding the six walk
  pieces to the drawn handles, then one restatement of tile + backing together.
- The kitchen stays HELD (annex height). The drawing-derived splashback stays HELD TILE_BAND_NOT_PRINTED on all rooms.
- A real B4-02 band line (printed band / dry open kitchen) has no code yet: not reachable on this villa.
