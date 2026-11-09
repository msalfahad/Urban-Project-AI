# T-571: precast lintel count by standard length per storey vs the freelancer (owner lintel rule, V3.0.58)

Worker 1, lane S, non-candidate, claim 2026-11-06 21:22 UTC (run session_01E6cPnd1GiA5u8SQXPLNr4N), engine base 587e47f9.
Files: `t571_lintel_count.py` (rule R-T571-1: count table + reconciliation, project-agnostic; training-villa builder),
`out/T571_LINTEL_COUNT.json` (numbers and opening ids only), `tests/t571_lintel_count/` (39 tests). Nothing in engine/,
rules/, knowledge/, registry or any candidate / released method changed; V2.9 + route G and V3.0.58 untouched; the rule
arithmetic is `company_rulebook_v1.lintel` (UPC-LINTEL-001) read-only. Inputs: the V3.0.58 lintel lines' ledger (T-453 r2,
sha ad9bceee3bfdbc12) and the census r3 (T-198, sha d79e6aa5d23edc0e); the freelancer list was read from Drive folder
'Alsenan chalet project' (blockwork workbook, RC workbook, category cost sheet) into the git-excluded private folder
(sha a9fec5ac837fb7f0); only counts and ids are written here.

## 1. Physical element and the engineering question (ERS s.2.1)

One precast lintel over each masonry opening, resting on built masonry at both ends; length from the masonry opening
(printed over drawn, Q-32 A); openings in RC walls, on glazing lines or under a beam take none.

Freelancer evidence (checked this run, all three workbooks): **he has no lintel row** - no count, no length, no nr or
lm cell. The RC workbook keys one rebar total and no lintel concrete; the category cost sheet has one MONEY line for
external door / window lintels (a lump sum, no quantity: a rate / payable figure, never a count). What he does have is a
masonry opening-deduction list per storey and wall class (count x width x height, 54 openings; his printed group totals
34.52 / 34.03 / 9.68 / 34.32 / 9.84 m2 re-added exactly). So the comparable cell is built, not read: **his opening list
put through the owner rule** ("freelancer-implied count"), labelled as such. It is not his lintel figure.

| | owner manual method | drawing-derived method (governs on this villa) |
|---|---|---|
| system | precast atab, stock 1.20 / 1.50 / 2.50 / 3.00 / 4.00 m | printed LINTEL SCHEDULE: cast-in-situ RC, cast to length (R-T487-1 (1), R-T519-1) |
| bearing | 0.15 m minimum each side | detail MIN 40 cm (a minimum, not the built bearing) |
| piece | shortest stock >= w + 0.30; > 4.00 m FLAGGED | B x D x (w + b_s + b_e), no stock length |
| result here | count BESIDE (this record) | 16 REQUIRED lines (1.016 m3) + 44 HELD / FLAGGED by name (V3.0.58) |

Governing precast count on this villa: **NOT_APPLICABLE (not 0)**.

## 2. Count tables (nr by stock length x storey; lm beside, never mixed)

Engine, owner rule b = 0.15 (60 masonry openings of the V3.0.58 lintel lines; AT_MOST = if every held lintel is built;
ESTABLISHED = the 16 REQUIRED):

| length | GF | 1F | 2F | AT_MOST nr | ESTABLISHED nr | lm (AT_MOST) |
|---|---|---|---|---|---|---|
| 1.20 | 13 | 14 | 3 | 30 | 9 | 36.0 |
| 1.50 | 9 | 6 | 5 | 20 | 5 | 30.0 |
| 2.50 | 5 | 4 | 0 | 9 | 1 | 22.5 |
| 3.00 | 0 | 1 | 0 | 1 | 1 | 3.0 |
| 4.00 | 0 | 0 | 0 | 0 | 0 | 0 |
| total | 27 | 25 | 8 | **60** | **16** (23.8 lm) | **91.5** |

FLAGGED > 4.00 m: none. NO_LINTEL by name (not in a masonry wall): W02, W03, W17, SX-01, SX-03, P-GF-05, U-01, D-GF-15.
Cross-check: the merged T-516 company-0.15 pieces on the five white REQUIRED lintels equal this table's (D-2F-01 1.50,
D-GF-06 1.50, W14 3.00, W15 2.50, W18 1.20).

Freelancer-implied (his 54 deducted openings through the same rule; his 20 cm internal rows are not split by storey):

| length | GF | 1F | 2F | unsplit | total nr | lm |
|---|---|---|---|---|---|---|
| 1.20 | 10 | 14 | 3 | 0 | 27 | 32.4 |
| 1.50 | 7 | 2 | 4 | 4 | 17 | 25.5 |
| 2.50 | 5 | 3 | 0 | 0 | 8 | 20.0 |
| 3.00 | 0 | 1 | 0 | 0 | 1 | 3.0 |
| 4.00 | 0 | 1 | 0 | 0 | 1 | 4.0 |
| total | 22 | 21 | 7 | 4 | **54** | **84.9** |

Beside (bearing convention, RULE_DIFFERENCE, not a result): at the project MIN 0.40 the engine list gives 1.50 x11 /
2.50 x45 / 3.00 x3 / 4.00 x1 = 60 nr, 142.0 lm (+50.5 lm, +55 % vs 0.15); his list 1.50 x11 / 2.50 x38 / 3.00 x3 /
4.00 x2 = 54 nr, 128.5 lm.

## 3. Reconciliation in nr to the cause (ours minus his, AT_MOST, b = 0.15)

Difference: **+6 nr (+11.1 % on his 54)**: +3 @1.20, +3 @1.50, +1 @2.50, 0 @3.00, -1 @4.00; lm 91.5 vs 84.9 (+6.6 lm,
+7.8 %). Every engine opening and every freelancer row carried once (68 / 54). Pairing order R-T571-1 (2): census key
(32 openings, verified census r3 keys with width and height), same width same storey, same width unsplit row,
ascending widths. Causes sum exactly to the difference, length by length (asserted):

| cause | 1.20 | 1.50 | 2.50 | 3.00 | 4.00 | nr | openings / verdict proposal |
|---|---|---|---|---|---|---|---|
| WIDTH_READ | +3 | -3 | | | | 0 | D-GF-03, D-GF-09: 0.90 jamb to jamb (DXF) vs his 1.00 (census: owner minimum view Q-04): RULE_DIFFERENCE. P-GF-01: 0.90 between the two jambs vs his 1.10 on the face where a 0.20 cross wall ends: UNRESOLVED (which face the lintel must span) |
| NOT_IN_MASONRY | | | | | -1 | -1 | W17 (his 3.15 x 3.00): no masonry host in the merged fill, he deducts it from block: UNRESOLVED (the curved wall's material is not established here; ENGINE_RIGHT only if the curved bay is glazing / RC) |
| ENGINE_ONLY | | +6 | +1 | | | +7 | D-GF-05 (5th external door; census '?', his 4 external 1.00 x 2.40 doors are taken by D-GF-01 / -03 / -06 / -09); internal, among identical widths (attribution, not identity): A-1F-01 (archway), P-1F-01 (passage 1.30 -> 2.50), D-1F-02, D-1F-03, D-GF-13 (doors 1.00), L-GF-01 (lift door). His internal list has 21 openings for our 27: no-leaf openings (2 archways, 2 passages) are not in his deductions; UNRESOLVED until his door list keys exist |
| OTHER_ONLY | | | | | | 0 | none |
| SAME_PIECE | | | | | | 0 | 50 pairs (D-1F-10 0.80 vs his 0.90 and L-1F-01 1.00 vs his 1.10 change no piece) |

Established basis: of his 54, 13 pair with a REQUIRED engine lintel, 40 with a HELD / FLAGGED one (head not
established 24, on a held wall 9, in a held piece 3, held in the fill 2, FLAGGED head room 2) and 1 is W17. The
established engine count is 16 (those 13 + D-1F-02, D-1F-03, D-GF-13) against his implied 54 (-38 nr): the cause is
HELD on our side (designer items D-45 heads, held walls), never a lower quantity; those lintels stay HELD by name,
never 0.

At b = 0.40 the width reads vanish (0.90 and 1.00 both -> 2.50) and the difference is +7 @2.50, -1 @4.00 (same openings).

## 4. Rule R-T571-1 1.0.0 (scope: every villa, comparing two opening lists through the owner precast rule)

1. One opening id once per side; lm where nr is counted, a fractional count, a piece other than the rule's, or a 4.00 m
   piece for a FLAGGED opening -> refused. Held width -> listed, never 0. NO_LINTEL -> listed by cause.
2. Pairing: census key (certain, then '?') -> same width same storey -> same width unsplit -> ascending widths; each step
   first where the wall thickness agrees. Pairing is attribution only; it never changes a count.
3. One signed cause per pair / leftover in nr per stock length; causes close the table difference exactly.
4. Where a project lintel schedule is printed the count is BESIDE (owner manual method) and the governing precast count
   is NOT_APPLICABLE.

Tests (`tests/t571_lintel_count`, 39): non-Alsenan villa Y by hand (0.90 -> 1.20; 1.25 -> 1.55 -> 2.50; 3.80 -> 4.10 ->
FLAGGED; every stock length hit; held at most only; lm beside 14.90), reconciliation closure with WIDTH_READ /
NOT_IN_MASONRY / FLAGGED / ONE_LIST_ONLY, thickness preference, storey relabel and order invariance; adverse: lm as nr,
fractional count, FLAGGED given 4.00 m, wrong piece, mm / cm widths, duplicate id, unknown state / storey, project
bearing without source, bearing below 0.15 (CONFLICT), stale ledger sha. Training villa: by-hand tables above.

## 5. Open / not done

- His lintel figure does not exist: the comparison is to his opening list, so "within 95 %" is not claimable for lintels.
- W17 masonry, P-GF-01 face, the 6 internal engine-only identities: UNRESOLVED (named above).
- No fit test on measured piers here (T-519 / T-544 own it); no capacity check (UPC-LINTEL-001 'NOT_PERFORMED').
- Not wired: research only; a later integration may carry the BESIDE table on the B9-02 lines.

## 6. Lessons row (proposed, ERS s.7)

| 2026-11-06 | a task asked for 'the freelancer's lintel rows' and the comparison was framed as count vs count | none exists in any of his workbooks; a lump-sum money line is not a quantity | check every workbook for the row first; when only his opening list exists, put it through the same rule, label it 'implied', and reconcile per opening to cause with a closure assertion | tests/t571_lintel_count | T-571 |
