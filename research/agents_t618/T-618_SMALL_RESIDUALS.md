# T-618: five small finishes residuals to a cause, or UNRESOLVED with what closes them (R-T618-1)

Worker 2, 2026-11-08, lane A, non-candidate, backlog-permitted (research only: no engine, rule / knowledge version,
registry, frozen or candidate file changed; nothing released; released default V2.9 + route G unchanged). Files:
research/agents_t618/* and tests/t618_residual_closure/* only (plus the regenerated docs/CODEMAP.md). Training villa;
not an accuracy claim. ERS read: s.2.1 (element first), 2.2 (notation before arithmetic), 2.3 (own drawing read), 2.4,
2.7 (no owner question: nothing here is a contradiction in the drawings or a missing safety-critical design; the porch
skirting scope is named for the Lead), s.3 (no number chosen by figure), s.4, s.7.

Build: `t618_extract.py --dxf <P7757.dxf> --write` (own read by handle of Drive 'Alsenan chalet project' /
P7757_DXF_COMPRESSED.zip, decoded into `.work/private` only) -> `T618_DRAWN.json` (handles, roles, lengths; no
coordinate, no drawing text); `t618_alsenan.py [--check]` -> `out/T618_RESIDUALS.json` (inputs pinned in `PINS.json`:
T618_DRAWN, his raw rows, T-574 / T-578 / T-602 / T-606 outputs). Sign: **his - ours** throughout (the statement prints
the two room rows as ours - his: -0.73933 / -0.70).

## 1. Summary

| Row (statement) | his - ours | cause found | verdict proposal |
|---|---|---|---|
| Stair skirting 0.710951 lm | range (-inf, 0.710951] | ARITHMETIC: upper end of a range built from HELD lower bounds (ORR-007), and a net of three stairs +2.899456 / -0.038505 / -2.150; NOTATION: his flights are his per-step pieces (nr), his lm row is level skirting | UNRESOLVED as a range; point 0.710951 refused; ST-02 landing ENGINE_RIGHT as drawn; E1 porch ENGINE_OMISSION CANDIDATE (scope HELD) |
| Rails 0.226 lm | range (-inf, 0.226] | ARITHMETIC: hypothesis A's own scope holds RL-09 (ST-02 RS-C outer band, HELD 0 .. unbounded) | UNRESOLVED as a range; point 0.226 refused |
| Door steps 0.40 lm | +0.40 | one uniform reading reproduces all six of his pieces: door-leaf block width at the house doors (D-GF-09 +0.10) + sea gate at its elevation panel 1.30 (+0.30) | UNRESOLVED (no ids, R-T602-1 (d)); CANDIDATE cause RULE_DIFFERENCE |
| 1F curved room +0.73933 lm | dP +0.73933, dA -1.726592 | every uniform offset REFUTED by sign; the one-notch shape (0.369665 x 4.670694) has no drawn edge | UNRESOLVED |
| 2F corridor +0.70 lm | dP +0.70, dA +0.325 | uniform offset REFUTED (t from dP gives dA 1.159375; t from dA gives dP 0.20); the one-pocket shape (0.35 x 0.928571) has no drawn edge | UNRESOLVED |

No ENGINE_WRONG found; no candidate quantity moves.

## 2. Stair skirting 0.710951 lm

**Notation first.** His marble sheet books each stair as four rows: steps (count x width), landing (m2), skirting (one
lm row) and per-step side pieces (nr). On all three stairs the piece count equals his step count (E1 5 = 5, main
63 = 63, inner 28 = 28): the per-step row is his flight-side skirting, the lm row his level skirting (R-T618-1 (e)).
T-574 compared his lm row with our level lines **and** our flight HELD lower bound (and his nr row with our flights
again, UNIT): the flight bound sits against both rows.

**Arithmetic.** The 0.710951 = his 29.87 - ours valued 12.15 - the flight HELD lower bounds 17.009049. A HELD flight
is a form range (ORR-007: zigzag vs sloped, never summed as a point) and two of the three stairs have unbounded pieces,
so the true residual is a range (R-T618-1 (a)):

| Stair | his | ours valued (level) | HELD bounds | his - ours range | lower-bound point |
|---|---|---|---|---|---|
| ST-03 E1 | 4.37 | 0 | flight 1.470544 .. 2.05 | [2.32, 2.899456] | +2.899456 |
| ST-01 main | 23.10 | 10.90 | flight 12.238505 .. unbounded + 7 level faces 0 .. 7.45 | (-inf, -0.038505] | -0.038505 |
| ST-02 round | 2.40 | 1.25 | flight 3.30 .. unbounded | (-inf, -2.15] | -2.150 |
| **Total** | 29.87 | 12.15 | | **(-inf, 0.710951]** | 0.710951 |

**Drawing reads (own, by handle).**
- ST-02 corner landing (W riser 141, N riser 144, E flight edge 4B6 / hidden 4AF, S wall 336 + column 2FC6):
  1.20 x 1.45 = 1.74 m2. Walled: S 1.20 + column face 0.05 = **1.25 = our RS-LD 1.25 (ENGINE_RIGHT as drawn)**; W and N
  are risers, E is the open edge (the RL-05 'corner landing' balustrade piece stands there). His 2.40 is 1.15 above
  the walled bound, all on faces with no wall base. His landing figures (1.44 m2, 2.40 lm) both fit a notional 1.20 x
  1.20 landing walled on two sides, but the drawn landing is 1.74 m2: CANDIDATE only; if established, ENGINE_RIGHT on
  1.15 lm.
- ST-03 E1 +1.00 porch landing (W top nosing 30A, N wall 34C, E wall 9D / main door / 9E, S wall 15A / pantry door /
  15B): 1.40 x 3.70 = 5.18 m2; walled N 1.40 + E 1.70 + S 0.40 = **3.50 lm**, and **no candidate skirting line** covers
  it: ENGINE_OMISSION CANDIDATE, scope HELD (an exterior porch base is not printed and no owner rule names it; the
  same question as his yard skirting row). His 4.37 is 0.87 above the walled bound and his landing 5.1 m2 is not the
  drawn 5.18: no reading established.
- ST-01: not re-read this run (4 flights, two winder turns HELD); his 23.10 sits 0.038505 (0.17 %) below our valued +
  smallest flight form.

Closes it: the flight form (ORR-007 / S-9) closes the ranges; his per-stair split closes level vs flight; the owner's
porch-skirting scope closes E1 (3.50 lm).

## 3. Rails 0.226 lm

His railing is one typed constant 18.95 (F-T578-1). Hypothesis A (his = ST-02 system RL-05 16.324 + D-23 RL-06 2.400 =
18.724) leaves 0.226, but the ST-02 system also contains **RL-09**, the RS-C outer band of the same round stair, HELD
0 .. unbounded (balustrade or string not established; band end differs between the plans). Under hypothesis A the
residual is therefore (-inf, 0.226]: 0.226 is the range's upper end, not a quantity (R-T618-1 (a)). Closes it: RL-09's
role (designer RFI, T-398 / RFI-S27); his figure has no breakdown to read.

## 4. Door steps 0.40 lm

His six pieces (no ids): 1.30, 2.50, 1.00, 1.00, 0.90, 1.00 = 7.70. Our census (T-602, wall gap): 1.00, 0.90, 1.00,
0.90, 1.00, 2.50 = 7.30. As multisets they share 2.50, 1.00 x3, 0.90; his 1.30 vs our 0.90 differ.

| Reading (one basis for every census opening) | pieces | sum | test |
|---|---|---|---|
| wall gap (ours, T-592 / UP-THR-001) | 1.0 / 0.9 / 1.0 / 0.9 / 1.0 / 2.5 | 7.30 | REFUTED |
| door-leaf block width (own read: 15E 1.000, 1B5 0.900, 192 1.000, 3FF 1.000, 2D8 1.000; street gap 2.50) | | 7.40 | REFUTED |
| block width, sea gate at its elevation panel 27FA 1.30 | 1.0 / 0.9 / 1.0 / 1.0 / 1.3 / 2.5 | 7.70 | **CANDIDATE** (all six pieces) |

The candidate parts are D-GF-09 +0.10 (block 1.000 drawn over its 0.900 masonry gap, T-592 conflict) and the sea gate
+0.30 (elevation 1.30 vs plan gap 1.000). Our basis is the stone's physical length (the wall gap, T-592), so the
proposal is RULE_DIFFERENCE on his basis, not ENGINE_WRONG. It is a CANDIDATE, not ESTABLISHED: his rows carry no
opening id (R-T602-1 (d) kept). Closes it: an id on his rows, or the owner on the paid length (already the T-592 gap).

## 5. 1F curved room +0.73933 and 2F corridor +0.70

R-T618-1 (c), offset coefficient k measured on the T-606 handle chains (shapely, +-1 mm mitred offset): 1F curved
k = 5.0193 (one arc), 2F corridor k = 4.0 (orthogonal).
- 1F curved: his - ours dP +0.73933, dA -1.726592. Every uniform face offset (centreline, plaster face, outer face)
  moves P and A the same way: **REFUTED by sign** (with T-612's arc-vs-chord sign test and T-606's reveal readings,
  every one-basis reading is now refused). The only one-shape reading, a rectangular notch walked round, needs 0.369665
  x 4.670694: none of the 32 lines in the cell is of either size: NOT_DRAWN.
- 2F corridor: dP +0.70, dA +0.325. t from dP = 0.0875 gives dA 1.159375; t from dA = 0.025 gives dP 0.20: **REFUTED**.
  A pocket walked round needs 0.35 x 0.928571: none of the 17 lines in the cell: NOT_DRAWN.

Closes them: his room sides (per-side figures or a dimensioned sketch). Without them, a wider search only finds figure
coincidences (ERS s.3).

## 6. Fix rows (manifest style; nothing wired)

- FR-T618-1 (lane I, statement V-next, no quantity): restate 'stair skirting UNRESOLVED 0.710951' as (-inf, 0.710951]
  by stair (E1 [2.32, 2.899456], ST-01 (-inf, -0.038505], ST-02 (-inf, -2.15]) and 'rails UNRESOLVED 0.226' as
  (-inf, 0.226] with RL-09 named; a HELD range's lower bound is never subtracted into a point residual.
- FR-T618-2 (Lead, scope): E1 +1.00 porch landing skirting, 3.50 lm walled faces, no candidate line: ENGINE_OMISSION
  candidate, HELD on the porch / outdoor skirting scope (never 0).

## 7. Rule, tests, lesson, missing

- R-T618-1 (`t618_rules.py` docstring, every villa, provenance T-618): (a) residual against a HELD range is a range;
  (b) piece multiset readings, sum-only match refused; (c) uniform offset test (sign, then both directions);
  (d) landing level skirting bounded by its walled sides; (e) notation: a per-step piece row whose count equals the
  step count is the flight side; (f) units apart, HELD never 0, VERIFIED the Checker's.
- Tests `tests/t618_residual_closure` (31 PASS): Villa K618 (not Alsenan) hand cases for ranges (bounded / unbounded,
  point refused, sums end by end), multiset (block reading CANDIDATE, gap REFUTED, sum-only refused, count differs),
  offset (4.00 x 3.00 room, t 0.10: dP 0.80 / dA 1.44 CANDIDATE; opposite signs and wrong ratio REFUTED; k <= 0
  refused; notch / pocket sizes), the outline chain read back at 0 / 37 / 90 / 211 deg, mirrored, k = 4, P 14, A 12;
  walled-side reader (wall, far face, column overlap); landing bound and excess; adverse walled > side, VERIFIED /
  unknown verdict refused, None never 0; Alsenan rebuild byte-identical, five rows, point residuals refused, RS-LD
  walled = engine, no coordinate, no workbook text, edited input stops the build. T-574 / T-578 / T-602 / T-606 /
  T-612 tests still pass (L2: 132 PASS).
- Lesson proposal (ERS s.7): "2026-11-08 | two residuals (stair skirting 0.71, rails 0.226 lm) were carried as UNRESOLVED
  quantities | each was the upper end of a range: a HELD lower bound subtracted, or a HELD piece inside the compared
  scope left out | report a residual against a HELD range as a range by group, and read a reference's row structure
  (per-step pieces vs lm) before deciding which of our elements a row compares with | tests/t618_residual_closure |
  PROPOSED".
- Missing: his room sides (curved room, corridor); ids on his door-step rows; his stair rows' split; the porch skirting
  scope; RL-09's role; the ST-01 landings not re-read here.

## 8. For the Checker (re-read 2 rows)

1. `python3 -I research/agents_t618/t618_alsenan.py --check` (byte-identical); with the private DXF:
   `.work/venv/bin/python -I research/agents_t618/t618_extract.py --dxf <P7757.dxf>` (re-read identical).
2. ST-02 landing: riser 141 to the flight edge (4B6 west end) = 1.20; wall 336 line to riser 144 = 1.45; layer-1 /
   column faces on its sides: S 336 (0.65) + 2FC6 (0.55) = 1.20, E column face 0.05, N and W none -> 1.25 = RS-LD.
3. Door blocks: insert 3FF (D120, D-GF-09) line extent 1.000 x |xscale 1| against the 0.900 gap of T-592; 27FA on the
   NW elevation 1.30.
