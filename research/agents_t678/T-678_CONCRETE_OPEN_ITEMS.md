# T-678: concrete open items after V3.0.65: the 22 OPEN BOUND lintel lines, outline 778, annex C3 lower end

Worker 1, lane S, claim 2026-11-10 17:22 UTC, engine base 707c624e. Research only, unwired: no engine, rule, knowledge,
registry, master, frozen or candidate file changed; V2.9 + route G and V3.0.65 untouched. Files: `t678_rules.py`
(R-T678-1 / -2 / -3, project-agnostic, built on t673_rules unedited), `t678_alsenan.py` (committed inputs only),
`out/T678_LEDGER.json` + `out/T678_CENSUS.md`, `tests/t678_open_items` (30 tests). Drawing cited by Drive folder and
title only: 'Alsenan chalet project' / 'ST7757 dxf.dxf' (sha 9f9d1179), decoded into the private folder; only relative
metres committed. Development villa, not an accuracy claim. Nothing VERIFIED.

## 1. Physical elements (ERS s.2.1)

- Lintel (B9-02 STR.CONC.LINTEL): one RC cast lintel over a masonry opening, required only where masonry is built above
  the head (R-T453-4). The question is physical (is there room for masonry between head + D + bed and the soffit?),
  not whether the host wall's AREA is measured.
- 778: a 0.20 x 0.40 S-COL.BON outline on SECOND FLOOR ROOF SLAB, solid column hatch 777, B7 band edges running
  through it; on FIRST FLOOR ROOF SLAB the same outline 77B with ANSI35 hatch (= starts here, ST legend) and text
  'P.C 20x50' / '8ø16'; nothing at the position on GROUND FLOOR ROOF SLAB. It is the planted column PC-2F (T-220,
  COL-2F-59): base on B19 top +9.65, top at the B7 soffit (B7 20x75 billed through it owns the joint).
- Annex C3: GF annex column, base 0.25 APPROVED, top = annex roof slab top (UP-CONC-JOINT-001).

## 2. The engineering finding

T-673 held 18 of these lintels because the host wall was ON_HELD_WALL / IN_HELD_PIECE in the merged fill. That state
says the wall's NET AREA is not closed (another opening's width not drawn: L-1F-01, A-1F-01, D-GF-07; or the annex
datum Q-54 B), not that the masonry above the head is unknown. R-T678-1 decides existence on a LOWER BOUND of the
soffit over the opening, and on the pieces over the opening's own extent where the run carries positions:

| opening | host | head (source) | soffit lower bound (clear above FFL) | spare | m3 lo .. hi |
|---|---|---|---|---|---|
| D-GF-07 | GF-W15 | 2.50 PRINTED | min T-274 piece 3.75 (B20 0.75) | 0.99 | 0.096 .. 0.108 (START 0.30 deficit) |
| W01 | GF-W15 | 3.00 PRINTED | 3.75 | 0.49 | 0.080 .. 0.108 |
| W13 | 1F-W04 | 3.30 PRINTED | B2 0.40 over its own extent 2.15 .. 3.35 m of WB-FL0074-FL0076: 3.80 | 0.24 | 0.080 .. 0.108 |
| D-1F-05 | 1F-W07 | 2.20 OWNER-APPROVED | 3.45 (B7 / B19 0.75) | 0.99 | 0.036 .. 0.0628 (both ends < 0.40) |
| D-1F-06 | 1F-W16 | 2.20 OWNER-APPROVED | 3.70 (B6 0.50) | 1.24 | 0.036 .. OPEN (END crossing wall, R-T678-3) |
| D-GF-01 | GF-W06 annex | 2.20 OA, FFL +0.30 | 3.544 - 0.40 (B2) - 0.30 = 2.844 | 0.384 | 0.056 .. 0.066716 |
| D-GF-02 | GF-W27 annex | 2.20 OA | slab piece: 3.544 - 0.75 - 0.30 = 2.494 | 0.034 | 0.036 .. 0.042708 |
| D-GF-03 | GF-W04 annex | 2.20 OA | CB6: 2.494 | 0.034 | 0.052 .. 0.058 (pier 0.15 to W04, full) |
| D-GF-04 | GF-W24 annex | 2.20 OA | slab piece: 2.494 | 0.034 | 0.048 .. OPEN (END search limit 3.0, no extension) |
| **9 lines** | | | | | **0.520 .. OPEN (closed lines' high 0.554224)** |

Annex datum (R-T678-2): the annex roof slab top is not printed (Q-54 B / D-39), but W08's head is DRAWN at +2.80
(T-201 SW, tol 0.006) directly under CB6 20x75 (GF-W04 is CB6 over its whole 5.85 m): s >= 2.80 - 0.006 + 0.75 =
**3.544** (W04 gives 3.531). One plane: the arch prints one finished +4.30 over the whole annex roof (T-321 ROOF-430),
the ST GFRS annex part prints no level, step or thickness (own read), and the only GFRS beams deeper than 0.75 (B26 /
B27 0.85) carry the planted columns at +5.45 (main plane). Slab-only pieces take D_max 0.75 (a drawn down-stand beam
is deeper than its slab). Owner beside: the four annex doors carry the owner door-height fallback 2.20 (Q-55 C),
labelled ASSUMED - OWNER-APPROVED in each row; the spare 0.034 m holds for any annex slab top in 3.544 .. 4.30.

## 3. The 13 lines still OPEN, each with its missing datum (row by row in `out/T678_CENSUS.md`)

W04 / W08 (CB6 over the head: lintel only if the annex slab top >= +3.829 / +3.816; Q-54 B decides), W11 / W12 (sill
level not drawn), W25 / W27 (stair-shaft member level not printed, R-T228-3), D-2F-02 (BM-2F-017 depth, D-04: required
for any depth <= 0.52 m), D-GF-05 (side-passage FFL + an unrecorded START stopper), D-GF-08 (unsized lift tie beam,
ST p.8 n.19), D-GF-14 (GF-W30 has no run / jamb record), D-1F-01 / D-1F-09 (dome opening, wall top not drawn, T-227),
A-GF-01 (arched crown not printed; a curved head is never a straight-lintel m3). OPEN BOUND 22 -> 13.

## 4. 778 and annex C3

| item | line | before (V3.0.65) | after (HELD, bounded) | basis |
|---|---|---|---|---|
| 778 = PC-2F | L-541c7e565bb93ecdb78b (HL:PLANTED_COLUMN:PC-2F:CONCRETE) | HELD blank; T-671 'owned by no line' | **0.1824 .. 0.350 m3** | area 0.08 (drawn 20x40) .. 0.10 (text 20x50), CONFLICT range; height (12.68 - 0.75 - 9.65) 2.28 .. (13.90 - 0.75 - 9.65) 3.50 m; slab top 12.68 = R-T669-2 on the same plate (778 inside the one SFRS outline, east face on its edge) |
| annex C3 | L-fad18af6 | <= 0.50625, low open | **0.41175 .. 0.50625 m3** | 0.125 x (3.544 - 0.25) = 0.125 x 3.294 .. 0.125 x 4.05 |

778 correction: the V3.0.64 / V3.0.65 index already holds its line (T-220 PC-2F); T-671 compared it only with the 2F
column lines of the schedule. Follow-up (not done): the same annex height bound 3.294 .. 4.05 m gives a low to the 4
other GF annex column lines (L-694a75c8, L-c0b3340a, L-e6c1c9a7, L-9f5a6470) once D-66 settles their section.

## 5. Owner manual method beside, freelancer, verdicts

Owner lintel rule (2026-11-02, precast, 15 cm bearing, shortest standard piece) is shown per row (e.g. D-GF-07 2.00 ->
2.50 m piece, doors 0.8 / 0.9 -> 1.20 m, W01 / W13 1.20 -> 1.50 m); the drawing (ST p.13 schedule, R-T650-1) makes all
60 RC cast, so the drawn method governs the m3. Freelancer: no lintel concrete row (T-571), PC-2F inside his column
count by type: NOT_COMPARABLE; no 'within 95 %' claim. Verdict proposals: 9 lintels ENGINE_RIGHT on existence (hand
calculations above), quantity HELD bounded; 778 ENGINE_RIGHT that it is a member (T-220 evidence), section UNRESOLVED
(drawn vs text).

## 6. Rules, tests, lessons

R-T678-1 / -2 / -3 1.0.0 (`t678_rules.py`, scope every villa). Tests (30): villa V678 by hand (slab bound 3.19 from a
drawn head under a 0.60 beam; door under a bounded soffit spare 0.28; slab piece at D_max; threshold named; member
serves -> FLAGGED; no head / no bound HELD; refusals: plain ASSUMED head, mm, bool, NaN, two planes, unprinted beam
depth; bound above the finished mark FLAGGED; position-resolved piece, normal and mirrored; open end: lo only, high
OPEN, never 0 - the adverse case 'a lintel with no printed bearing stays HELD'; planted column to a beam soffit 0.132 ..
0.232; column refusals) + development rebuild (22 rows once, 13 OPEN each naming its datum, totals, 778, C3, no
absolute coordinate). Lessons row (proposed, ERS s.7):

| 2026-11-10 | 18 lintels held because the host wall's fill was HELD, and outline 778 reported 'owned by no line' though its line existed | a ledger used a wall-AREA state as the physical existence test; a census matched an outline only against schedule column lines | existence of masonry over a head is decided on a lower bound of the soffit over the opening's own extent; an unprinted slab top is bounded below by a drawn head under a printed beam on one plane; an outline is matched against every element line (planted columns, stubs) before 'no owner' | tests/t678_open_items | PROPOSED |

## 7. For the Checker (re-measure)

1. 'ST7757 dxf.dxf' SFRS 778 + hatch 777 + B7 edges 39A / 39B; FFRS 77B + hatch 77A (ANSI35) + texts 77C / 77D; GFRS
   nothing at the position. 2. W13 on run 1F|WB-FL0074-FL0076: B2 1.40 .. 4.10 between the two columns, jambs 0.75 each.
3. W08 drawn head +2.80 (T-201 SW) under CB6 (GF-W04 = CB6 5.85 m); GFRS annex part: no level / step / thickness.
4. One annex door (D-GF-03) and D-GF-07 by hand from the rows above.
