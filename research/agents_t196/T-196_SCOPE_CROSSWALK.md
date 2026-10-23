# T-196 Residential review R7: scope vs drawings, both directions (scope crosswalk v1)

Worker 3, 2026-10-23. Lane I, backlog-permitted (owner-approved review plan, PROJECT_UNDERSTANDING_ASSESSMENT s.6 R7).
Pure check module, unwired; no quantity, rule, method or released line changes. Released default V2.9 + route G
unchanged; candidates read, both reproduced in this run on the Drive copies P7757.dxf ab54dd55 / ST7757 dxf 9f9d1179:
ARCH_TAKEOFF_V3.0.5 r2 (V3_0_5_BOQ_LINES.csv **76d75bde**, merged 90d0b769: the committed summary.json) and V3.0.4
(**d86de34a**). Rows, elements and findings are identical on both; only the unlinked line count differs (below).

## r2 (checker REJECTED 2026-10-23 02:08, rework items 1-4) - one element per physical member

**Cause (item 1), established from the code and the V3.0.5 lines.** `engine/source/element_register_v0.py` `_structural`
turns a steel key into its concrete key by dropping only the LAST segment (the bar diameter):
`P-S:COL:SH12:C2@x,y|GF:MAIN:D16` -> `COL:SH12:C2@x,y|GF:MAIN`, `...:TIES:D8` -> `...|GF:TIES`. The bar-set segment
(MAIN / TIES) stays, so each column = 3 register elements: the concrete one (`COL:SH12:C2@x,y|GF`, own concrete line)
and two steel-only ones (status basis "only steel lines read this element"). Not sheet outlines and not storeys: the
three keys share sheet, position and storey. V3.0.5 76d75bde: 178 such steel pieces on 89 members (storey columns and
foundation necks, kind COL); none without its concrete member.

**Fix (crosswalk side; register v0 read only, as the row's Files say).** `scope_crosswalk_v1.collapse_pieces`, applied
inside `crosswalk()` before anything is counted: a register element read only by steel lines whose route key extends the
route key of an element of the same kind and floor (trailing segments only; the position segment `@x,y|storey` is never
stripped, so nothing merges across positions or storeys) is a COMPONENT of that element ("concrete", "steel MAIN",
"steel TIES"; as POOL-01 base / walls). Its lines are re-linked to the member. A steel piece without a concrete member
stays its own element with a PIECE_WITHOUT_MEMBER finding (Alsenan: none). A selector also no longer makes a register
element whose own line is NOT_APPLICABLE_WITH_EVIDENCE (a printed mark not built) a member of a reference row: it is
listed on the row (`not_applicable`), never dropped.

**Restated (item 2), V3.0.5 76d75bde and V3.0.4 d86de34a, reproduced in this run from the Drive copies (P7757.dxf
ab54dd55, ST7757 dxf 9f9d1179); rerun identical; both candidates give the same rows / elements / findings.**

| Column row (his) | storey, mark | r1 elements | r2 elements | checker own count / T-119 |
|---|---|---|---|---|
| RC:S13:37 | GF C2 | 12 | **4** | 4 / 4 (his 2.25 = 4 x 0.30 x 0.50 x 3.75) |
| RC:S13:39 | GF C4 | 6 | **2** | 2 / 2 |
| RC:S13:36 | GF C1 | 3 | **1** | 1 / 1 |
| RC:S13:38 | GF C3 | 18 | **6** | 6 / 6 |
| RC:S13:53 | 1F C2 | 12 | **4** | 4 / 4 |
| RC:S13:59 | 1F C9 | 6 | **2** | 2 / 2 |

Every storey-column mark (GF C, C1 .. C11; 1F C1 .. C9; 2F C1, C2, C3, C5, C9) now equals the T-119 column ledger
(MERGED, one row per drawn column; `summary.json` `t119_column_check`). Only spelling differs: the register's `PC`
(1F 2, 2F 1) = T-119 `P.C 20x50` + `P.C 20x70` (1F) and `P.C 20x50` (2F). NOT_APPLICABLE printed marks listed, not
members: 1F C3 x1, 2F C3 x2, 2F C5 x1, 2F C8 x1 = the 5 columns above necks with no column on the slab plan above
(register row "5 columns above the necks", checker VERIFIED 17:40).

Counts after the collapse: freelancer rows DRAWN 28, AGGREGATE 39 (r1 15 / 52: 13 single-column rows were AGGREGATE of
3 pieces), NOT_DRAWN 3, SCOPE_UNKNOWN 3, NOT_MAPPED 421; RC workbook m3: DRAWN 74.164, AGGREGATE 192.929, NOT_DRAWN
3.708, SCOPE_UNKNOWN 2.788, NOT_MAPPED 126.030 (= 399.62). Elements **656** (r1 834 = 656 + 178 pieces): HAS_LINE 642,
MISSING_LINE 14 (unchanged: RL-01 .. RL-10, ST-01 1F -> 2F, ST-01b, DOME-TOWER, one opening). Lines unchanged
(V3.0.5 LINKED 1,733, UNLINKED 1,801). DUPLICATE_ROW: only RC:S15:23 / 24 (slab), as r1; no column duplicate existed or
appears.

**Adverse tests (item 3)** in `tests/t196_scope_crosswalk`: one column with three engine lines (concrete + MAIN + TIES)
-> one element, three components, row DRAWN not AGGREGATE; two storeys of one mark -> two disjoint 3-piece sets, the GF
row takes only the GF one; mirror x -> -x same summary; steel with no concrete line -> PIECE_WITHOUT_MEMBER, kept; a
NOT_APPLICABLE mark listed on the row, not a member.

**Item 4 / register ruling 04:20.** The candidate line `P-C:STAIRS:1F:SITE-b845e1e78b1f74a8` (4.451 m3) is reported
**MISREAD** (a dome outline on the 1F roof, T-187 finding; owner trade DOMES; HELD MISREAD in V3.0.6, retired by T-193),
not as a stair finding. Slab pair RC:S15:23 / 24 and his RC:S14:82 omission stand as findings for the Lead (unchanged).

**New finding (Lead, register).** 5 COL elements `CN` with no storey on the GF column-layout sheet (SH12, keys `U-C:COL:
SH12:CN@...`, 3 BOUNDED_EXPOSURE 0.378 low, 2 BLOCKED_RFI): unlabelled column outlines at positions that are not the 5
labelled GF `C` columns; not in T-119's 59 columns; physical element to establish (no row maps to them; not guessed).

**Data note.** `ROWS_T196.csv` now carries only what the crosswalk needs: row id, status, elements, components,
not-applicable marks, reason; his unit and quantity only on the 3 NOT_DRAWN rows and on the dome row's NOT_DRAWN part
(they ARE the finding). Trade, unit and quantity of the other 491 rows are no longer written.

**Lesson (proposed for ERS s.7).** Problem: register-v0 counted 3 elements per column (checker 02:08). Root cause: a
steel key reduced to its concrete key by dropping only the diameter, leaving the bar-set segment. Rule (any villa): a
member's reinforcement sets are components of the member, never elements; an element count is quoted only after
pieces are collapsed per position and storey. Test: t196 r2 adverse cases above. Status: fixed in the crosswalk; the
register-v0 key reduction itself is lane I tooling for a register v1 (not edited here: it is read-only in this row).

## What was built

| File | What |
|---|---|
| `engine/source/scope_crosswalk_v1.py` | `crosswalk(elements, rows, row_map, lines, line_links, rulings, documents)`: (a) reference rows -> drawn elements DRAWN / AGGREGATE / NOT_DRAWN / SCOPE_UNKNOWN (+ NOT_MAPPED for a join not yet made, never counted as any of the four); (b) candidate lines -> elements LINKED / UNLINKED with reason; (c) reverse: every drawn element HAS_LINE / CARRIED_BY_RULING / MISSING_LINE, and every required sheet NOT_IN_SET -> NOT_ISSUED designer item with its lines and rows, quantity UNKNOWN (never 0). Findings: DUPLICATE_ROW (same element, component and trade; one finding per row group), ROW_WITHOUT_LINE, RULING_CARRIER_WITHOUT_LINE, NOT_DRAWN_SCOPE (per unit), NOT_DRAWN_PART (one discipline does not draw a part of a drawn row). `build_elements` joins an element_register_v0 register with ledger elements (an id given twice is refused); `register_links` reads the register's links (HOST role left out). |
| `tests/t196_scope_crosswalk/` | non-Alsenan hand fixture (11 elements, 10 lines, 10 DETAIL rows + 1 subtotal) and adverse cases, 12 tests (r2: 4) |
| `research/agents_t196/alsenan_t196.py` | the development-villa run (`<run dir> --lines <V3_0_x_BOQ_LINES.json> --commit-csv`): register v0 + T-183 / T-184 / T-185 / T-164 ledger elements, the RC workbook joined in full, the T-195 required-sheet list; prints ids and counts only |
| `research/agents_t196/ROWS_T196.csv`, `summary.json` | per reference row: row id (workbook code : sheet ordinal : row), trade, unit, his quantity, status, element ids, reason. No cell text, no sheet name, no coordinate |

Row ids: `<workbook>:S<n>:<row>` where S<n> is the sheet's ordinal in `tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json`
order (RC workbook = S10 .. S17; S16 = stairs / domes, S17 = pool). The Checker reads a row there by file + ordinal + row.

## Alsenan result r1 (superseded for column counts and element totals by the r2 section above)

**(a) Freelancer rows, 494 DETAIL (the 122 subtotal / cover rows are sums, not scope):** DRAWN 15, AGGREGATE 52,
NOT_DRAWN 3, SCOPE_UNKNOWN 3, NOT_MAPPED 421. The RC workbook (148 DETAIL rows, 399.62 m3 of his) is joined in full:

| RC status | rows | his m3 | what |
|---|---|---|---|
| DRAWN | 15 | 67.347 | single elements (pool base / walls, stairs, footing marks printed once, ...) |
| AGGREGATE | 52 | 199.746 | type-mark rows over every footing / neck / column of the mark, storey slab rows over the panels, blinding over all footings, domes |
| NOT_DRAWN | 3 | 3.708 | pump-room walls 1.080 + floor 2.400, pool steps 0.228 (RC:S17:13 / 15 / 14); searched: ARCH GF plan sheet03, ST p.7 pool detail, NW cut, sanitary-7757 (T-183 items K, E) |
| SCOPE_UNKNOWN | 3 | 2.788 | MAP_MISS: his F10 (1.960; the drawn F10-type footing carries no label in register v0: FOOTING_LABEL_CONFLICT, register row 191) and 1F PC1 / PC2 (0.345 + 0.483; the structure prints `PC` x 2 on 1F, no PC1 / PC2) |
| NOT_MAPPED | 75 | 126.030 | 67 beam rows, 3 strap rows, 4 ground-beam rows, 1 lift-wall row: drawn kinds, but register v0 carries no beam / strap mark (route G bands): join by mark pending |

Plus NOT_DRAWN_PART on the dome row RC:S16:13 (6.780 = 3 x 2.260): the tower dome shell 2.260 m3 has no structural
drawing (searched ST p.5, p.6, p.7 dome detail, ARCH elevations; T-185: drawn architecturally only, HELD).
Total reference concrete on no structural drawing: **5.968 m3** (3.708 + 2.260), all stays visible, none becomes 0.
The other workbooks (FIN 95, BLK 128, PLS 65, PNT 37, ALU 21 DETAIL rows) are NOT_MAPPED: their room / surface join
to register ROOM / WALL / OPEN elements is the next R7 step.

**(b) Candidate lines, V3.0.5: 3,534** (V3.0.4: 3,132): LINKED 1,733 (both), UNLINKED 1,801 (V3.0.4: 1,399).
Unlinked: steel ledger lines 1,771 (BEAM_STEEL 763, COLUMN_STEEL 327, GROUND_SYSTEM_STEEL 281, SLAB_STEEL 312 and
STAIR_POOL_TANK_STEEL 88 new in V3.0.5: register v0 binds steel to its concrete element only through the route G key
families; the ledger families are a later kind), V3.0.5's 2 DOME_RING beam lines (ring = BEAM per the register ruling;
no ring element yet), facade 13 (later kind), thresholds 5, soffit ceilings 5, WP 3, boundary wall 1, and **one stair line: `P-C:STAIRS:1F:SITE-b845...` 4.451 m3 PROVISIONAL** (see below).
Ledger bindings: pool 2 lines -> POOL-01; 2 dome shells -> DOME-A / DOME-B pair; SCOPE:STAIRS:GF flights 2.786 ->
ST-01 GF -> 1F; SCOPE:STAIRS:GROUND flight 0.948 -> ST-03 (E1); `STAIRS:GROUND:SITE` (zone 8.3723 m2) 1.769 -> ST-02.

**(c) Reverse:** drawn elements 834: HAS_LINE 820, MISSING_LINE 14: RL-01 .. RL-10 (10 drawn railing runs of T-164:
roof, balcony, floor-edge, stair and fence guards; the candidate's 14 FIN.RAILING lines are per architectural flight,
BLOCKED_RFI, no quantity, and are not bound to the T-164 runs), ST-01 1F -> 2F, ST-01b (lobby flight 0.126, no line
and no freelancer row), DOME-TOWER (HELD in T-185), one register opening. NOT_ISSUED (T-195): 10 required sheets not in
the set, e.g. reflected ceiling plan (36 candidate lines, 29 of his rows), door / window schedule (71 lines, 21 rows),
stair architectural details (42 lines, 15 rows), roof plan (8 lines); water / electrical / AC have no line and no row.

## The four known cases (acceptance)

| Case | Expected | Crosswalk | |
|---|---|---|---|
| Pump room and pool steps | NOT_DRAWN | RC:S17:13 / 15 / 14 NOT_DRAWN, 3.708 m3 | reproduced |
| Third dome | NOT_DRAWN (structure) | NOT_DRAWN_PART 2.260 m3 (ST) on RC:S16:13; DOME-TOWER MISSING_LINE + ROW_WITHOUT_LINE | reproduced |
| Railings | DRAWN, lines only from T-164 | RL-01 .. RL-10 MISSING_LINE in V3.0.4 (no freelancer row either) | reproduced |
| ST-01 1F -> 2F | DRAWN, no released line (D-T184-1) | ST-01.1F-2F MISSING_LINE + ROW_WITHOUT_LINE (his RC:S16:20 / 21 cover it) | reproduced, with the caveat below |

## Findings for the Lead / Checker (no quantity changed)

1. **Unbound candidate stair line** `P-C:STAIRS:1F:SITE-b845e1e78b1f74a8`, 4.451 m3 PROVISIONAL (CONVENTION_ONLY,
   winder approximation, zone 17.127 m2, width 2.2111 m, 19 risers, storey rise 4.20 m). No T-184 flight matches it by
   geometry (ST-01 1F -> 2F = two straight 1.20 m flights + landing). It is either the ST-01 shaft read as one winder
   region (then D-T184-1 is partly covered in the candidate, by convention) or another drawing (the width equals the
   dome-opening radius r 2.2111 of T-185, possibly coincidence). Physical element to establish before any integration
   touches stairs (T-187 fixes D-T184-1): not bound, not guessed.
2. **DUPLICATE_ROW** RC:S15:23 / RC:S15:24: two unlabelled continuation rows of his top-roof slab (5.094 + 2.403 m3)
   both land on the 9 panels of the 2F slab; his workbook prints no panel split. A split or a double count: to establish
   (Checker, on ST p.6).
3. His 1F beam total (RC:S14:82, 17.027) sums rows 60 .. 78 and leaves out row 59 (0.128 m3, B1) which his carried-forward
   row 79 includes (17.155): a 0.128 m3 arithmetic omission inside his own workbook (from the formulas in
   BENCHMARK_NORMALISED, not a drawing question).
4. His 1F column marks PC1 / PC2 are printed nowhere (structure prints PC); F10 is the known label conflict.

## Validation

r2 (merged with the working branch 57bb0411 first): tests/t196_scope_crosswalk 12 passed (8 r1 + 4 r2 adverse);
tests/t134_element_register, tests/t061_room_label_guard and tests/structural_comparison_engine all passed (the rebar
firewall included: the module names no steel token, pieces are "structural lines that are not concrete"); freeze 0
differing; docs/CODEMAP.md regenerated by the tool as the last commit, `codemap check` stale none.

r1:

- tests/t196_scope_crosswalk 8 passed; tests/t134_element_register passed (module read only);
  tests/structural_comparison_engine/test_rebar_product_firewall.py: 1 failure **pre-existing on the base**
  (`engine/source/default_guard.py` undeclared, T-190 READY fixes it); scope_crosswalk_v1.py is not in the list.
- freeze 0 differing; codemap rebuilt by the tool, stale none.

## Lessons-register row (proposed, ERS s.7)

| Date | Problem | Root cause | General rule (scope) | Regression test | Status |
|---|---|---|---|---|---|
| 2026-10-23 | Invented and missing scope found case by case (pump room, pool steps, third dome, railings, ST-01 upper storey) | no systematic join between reference rows, candidate lines and drawn elements; a reference total was compared to a candidate total | Every reference row is joined to drawn elements (DRAWN / AGGREGATE / NOT_DRAWN with the sheets searched / SCOPE_UNKNOWN) and every drawn element to a line (or a ruling carrier) before quantities are compared; a part of a row one discipline does not draw stays visible as NOT_DRAWN_PART; a join not yet made is NOT_MAPPED, never a verdict (any villa) | tests/t196_scope_crosswalk (normal: hand villa; adverse: duplicate rows, carrier without line, partly drawn row, mirror, refusals) | built, Checker to verify |
