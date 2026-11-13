# T-749: PAINT RULE WIRING integration package, ARCH_TAKEOFF_V3.0.77 (lane I, hub H1P; OWNER RULE PAINT 2026-11-12)

Worker 3, 2026-11-13. INTEGRATION PACKAGE for Checker Gate B. Base: the candidate of record V3.0.76 (T-736, Gate B
PASS, merge 166fb1fd, BOQ_FAMILY_MASTER 1.77.0). Released default V2.9 + route G untouched; nothing released, nothing
VERIFIED. No drawing, workbook, client name or coordinate here; Drive files named by folder and title only.

## 1. What is wired (Checker-merged only, sha-pinned in `t749_inputs.py`, `--check` rebuilds `out/T749_ENTRIES.json`)

| source | merge | Checker | wired as |
|---|---|---|---|
| T-740 `out/T740_PAINT_RULE.json` (UP-FIN-PAINT-002 1.0.0, rulebook 1.2.0) | 0f0e0cd0 | Verifier 2026-11-12T14:29Z Gate A PASS | 5 room paint lines restated HELD (PAINT_RESTATE) |
| T-746 `out/T746_PAINT_EDGES.json` (R-T746-1/2, Lead ruling reading B) | faf8afcd | Verifier 17:53Z Gate A PASS | 30 return m2 lines EXCLUDED EDGE_AS_LM + 30 FIN.PAINT.EDGE lm lines |
| T-747 `out/T747_EXT_PAINT.json` (R-T747-1..3) | a3f62c52 | Verifier 20:20Z Gate A PASS | window edges by opening id, corner groups by face key |
| T-751 `out/T751_EDGE_BOUNDS.json` (R-T751-1..4) | 79766703 | Verifier 22:05Z Gate A PASS (partially verified) | arched heads developed, parapet-end / plinth closures, NO_HOST arris, door reveals |
| T-748 `out/T748_ROWS.csv` (readiness R6, hub H1P: CHANGE 5, PENDING 30, KEEP 48, KEEP_RELEASED 1, NONE 21) | 071dc837 | Verifier 17:58Z Gate A PASS | the line-by-line map |

Every entry binds its candidate line as the map read it (item, element, unit, class, range against the V3.0.76 index
184e0e3c): stale = stop. The 48 KEEP rows, the KEEP_RELEASED row (GF_15 released 56.0131, rule 56.01315 = ledger
rounding) and the 21 NONE rows (wet bands above the ceiling, facade with no paint line) move nothing.

## 2. Method (R-T749-1, every villa; module `engine/source/arch_v3077.py`)

- PHYSICAL ELEMENTS: (a) the painted wall face of a room = its plastered face below the finished ceiling, not tiled;
  (b) the painted return of a door / arch / gate (jambs, head, painted sill) and the painted outside edge of a window;
  (c) an outside building corner (vertical arris), exposed height.
- Owner manual method: paint m2 = plaster m2 of the same faces - band above a false ceiling (Q-72) - tiled faces; edges
  and corners are lm items (owner 2026-11-12 'lm for windows doors and corners, so the Area is the same').
  Drawing-derived method: T-740 face ledger (plaster bound from the candidate, band from the reflected-plan ceiling
  height T-709, tiled part T-702); T-746 door blocks' frame posts against the drawn masonry jambs; T-747 / T-751
  elevations: frame lines by handle, printed levels, arched heads by the drawn arc chain.
- PAINT_RESTATE: HELD -> HELD at the rule range, inside its plaster face (asserted), never a released line.
- RETURN_LM: the return m2 line becomes EXCLUDED_WITH_REASON (EDGE_AS_LM, naming its edge line); one FIN.PAINT.EDGE lm
  line per opening, bound to the return's plaster line, HELD bounded (head 0 .. w: no section shows the head member) or
  HELD blank (A-GF-01, A-1F-01, D-GF-15: size / springing not printed). Never valued, never 0.
- EXT_EDGE: one FIN.EXT.PAINT.EDGE lm line per window (26 measured, W02 / W03 / W17 blank) and per corner group (9),
  HELD on the floor's facade line FIN.EXT.FINISH (the only live exterior finish line; HELD blank), the face key named
  so T-314 r3 can re-bind. A DOOR's exterior edge is the same reveal its return line carries (asserted equal per door,
  7 doors 0 .. 12.20 lm): counted once, under FIN.PAINT.EDGE.
- Older state checks (V3.0.64 .. V3.0.76) re-run on the result; a return line this version excludes is shown to them in
  its V3.0.74 form (its record names 0 .. face) and is held by this version's own check (EXCLUDED, edge line named).
- Totals: only FIN.PAINT|m2, FIN.PAINT.EDGE|lm, FIN.EXT.PAINT.EDGE|lm move, each exactly by the changes (asserted).

## 3. Lines (evidence status WORKFLOW_CONTROLS s.5; every line HELD or EXCLUDED; nothing VERIFIED)

Room paint (m2, HELD -> HELD; plaster - band - tiled, the engine line's own difference named):

| line | face | V3.0.76 | V3.0.77 | cause of the move (T-740) |
|---|---|---|---|---|
| L-cdf7f5cd | GF_01 | 36.911738 .. 56.925700 | **36.900914 .. 54.610926** | W11 + W12 opening basis (0.010824 / 2.314774) |
| L-c0ac22c9 | GF_08 | 152.050500 .. 178.805000 | **151.895450 .. 178.804950** | beam ends B26 / B27 below the ceiling 0.155; rounding |
| L-349db74a | 1F_11 | 61.462600 .. 61.717700 | **60.601150 .. 66.023050** | W17 on the pre-Q-76 outline (+0.861450 / -4.305350) |
| L-be48ea84 | 1F_13 | 111.017700 .. 114.367700 | **111.017500 .. 114.367500** | ledger rounding 0.0002 |
| L-c74cfb4e | 2F_01 | 22.650200 .. 26.000200 | **22.490150 .. 26.000150** | beam B15 below the ceiling 0.16; rounding |

Returns (30): m2 line HELD 0 .. face (27) / blank (3) -> EXCLUDED EDGE_AS_LM; edge lm lines 27 HELD bounded
**0 .. 33.800 m.l** (jambs 0 .. 8.80: D-GF-09 position conflict + D-GF-14 arc symbol; heads 0 .. 25.00), 3 HELD blank.
Per opening by line id in `out/` ledger and the run's V3_0_77_INTEGRATION_LEDGER.csv.

Exterior windows (lm, host = the floor facade line): 26 points = **103.682251 m.l** (W15 / W16 6.845844, W26 4.070563
developed arcs, T-751, ENGINE_RIGHT over the T-746 rectangles 106.020: -2.337749); W02 / W03 / W17 blank.

Exterior corners (lm): GF storey 95.10, 1F storey 37.80, 2F storey 16.80, 1F parapet ends **9.185812** (T-751 closure of
0 .. 11.90), 2F parapet 2.00, annex parapet 2.00, GF +5.50 parapet **1.00 .. 2.20** (stop-end 0 .. 1.20 HELD: free or
abutting end on no vector view), plinth **14.25** (T-751 closure 2.10 .. 2.55 -> 2.55), passage-mouth arris NO_HOST
**1.40** (its face line is not in the candidate; on its own line, never dropped). Sum **179.535812 .. 180.735812 m.l** =
T-751 after_physical; hosted part 178.135812 .. 179.335812 = T-751 after (residual 0).

## 4. Hand reconciliation

FIN.PAINT m2 (index convention): before released 4 / 217.2081, bounded 38 / 604.990059 .. 710.006421, blank 3, excluded
31. After: released 4 / 217.2081 (unchanged), bounded 11 / **603.802485 .. 687.846697**, blank 0, excluded 61.
By hand: restatements low -0.010824 -0.155050 -0.861450 -0.000200 -0.160050 = -1.187574; high -2.314774 -0.000050
+4.305350 -0.000200 -0.000050 = +1.990276; returns out low 0, high -24.150000 (27 x their face highs, = T-746
paint_m2_removed_engine). 604.990059 - 1.187574 = 603.802485; 710.006421 + 1.990276 - 24.150000 = 687.846697.
Interior paint after = 217.2081 + 603.802485 .. 687.846697 = **821.010585 .. 905.054797 m2** vs T-746 rule B
821.010635 .. 905.054847: -0.000050 both ends = GF_15 released 56.0131 kept vs rule 56.01315 (released lines move only
by a Checker record): residual 0 after the named item.

## 5. Run of record, census, diff

Drive 'Alsenan chalet project' copies 'P7757_DXF_COMPRESSED.zip' (inner P7757.dxf ab54dd55) and 'ST7757 dxf.dxf'
(9f9d1179), decoded by the wrapper into the private folder only: own fresh t167 `v304_run.py` (exit 0) ->
`v3077_run.py` (exit 0): every earlier version re-run and asserted by its own wrapper, **V3_0_76 9b35725c (asserted =
the T-736 run of record by its line index) -> V3_0_77 b8524d5c**, 5,241 lines; replaced 35, added 68, outside 5,138
byte-identical (asserted); the older checks V3.0.64 .. V3.0.76 pass on the result (30 excluded return lines shown to them
in base form: V3.0.74 finishes BOUND 4 / band 2 / return_bound 27 / return_blank 3, V3.0.76 beads unchanged).
Diff vs V3.0.76: CHANGED 35, ADDED 68, SAME 5,138. vs released V2.9 + route G: NOT_IN_RELEASED 3,649 (+68),
QUANTITY_DIFFERS 1,054, SAME_QUANTITY 538 (unchanged).
Census `t479_registry_census.py` (verdicts V3.0.44 b3b08dd7, downgrades 81732639): on V3_0_76 it reproduces
`research/agents_t736/out/LINE_INDEX_V3_0_76.json` byte for byte; on V3_0_77 -> `out/LINE_INDEX_V3_0_77.json`, issues {},
complete map, stale blocks 0. `t749_package_families.py` (chain 76 -> 77): B4-06 FIN.PAINT changed 35, FIN.PAINT.EDGE
added 30; B4-07 FIN.EXT.PAINT.EDGE added 38. Summary `out/T749_SUMMARY.json`; ledger `out/V3_0_77_INTEGRATION_LEDGER.csv`
(every changed / added line by id, before / after, rule, sources).

| code | V3.0.76 | V3.0.77 |
|---|---|---|
| FIN.PAINT m2 (B4-06) | released 4 / 217.2081; bounded 38 / 604.990059 .. 710.006421; blank 3; excluded 31 | released 4 / 217.2081 (unchanged); bounded 11 / **603.802485 .. 687.846697**; blank 0; excluded **61** |
| FIN.PAINT.EDGE lm (B4-06) | no line | 30 lines: 27 bounded **0 .. 33.80**, 3 blank; released 0 |
| FIN.EXT.PAINT.EDGE lm (B4-07) | no line | 38 lines: 35 bounded **283.218063 .. 284.418063** (windows 103.682251 + corners 179.535812 .. 180.735812), 3 blank; released 0 |

## 6. Engine vs freelancer, findings, held / missing, downstream

- Paint m2 interior: candidate held band 821.011 .. 905.055 m2 vs the freelancer's interior paint (T-561 like for like,
  unchanged): his paint carries 14 door returns as area 15.96 m2 = RULE_DIFFERENCE (owner rule B: 0 m2 + lm); the
  return count 27 drawn vs his 14 = ENGINE_RIGHT (T-746, merged). No other verdict moves with this package.
- Window edges: 103.682251 m.l (arcs developed) ENGINE_RIGHT over 106.020 (T-751, merged).
- F-T749-1 (double count prevented): T-747 / T-751 list 7 exterior door edges 0 .. 12.20 lm; each is the same reveal
  T-746 already carries as that door's return edge (equal per door id, asserted): wired once, under FIN.PAINT.EDGE.
  Rule: an opening's reveal is one lm line whichever face it is listed under.
- F-T749-2 (item codes, for the Checker / Lead): paint edges had no item code; this package opens FIN.PAINT.EDGE (lm,
  B4-06 internal paint) and FIN.EXT.PAINT.EDGE (lm, B4-07 external paint), trade PAINT. A naming decision, no quantity
  rides on it; a rename is a next version.
- F-T749-3 (host binding): 6 of 9 corner groups sit on faces (parapets, plinth, mouth) whose T-314 r3 finish lines are
  not in the candidate; they bind the floor facade line with the face key named; T-314 r3 re-binds by key.
- Held / missing: exterior paint m2 (1,009.110254 .. 1,087.619176 m2 by T-747 / T-751, 6 1F slab-edge faces blank)
  waits its render host T-314 r3 (no m2 line formed before); door heads 0 .. w on 25 doors (no head section); W02 /
  W03 / W17 and A-GF-01 / A-1F-01 / D-GF-15 blank; stop-end 0 .. 1.20; boundary-wall paint (8 lines) refused here
  (Q-65). Horizontal exterior arrises (T-337 FIN.EXT.CORNERS 710.17 .. 821.86 m.l) not restated.
- Downstream: none outside the three codes (asserted); edge lines bind their hosts by id and are never summed into m2.

Lessons row (ERS s.7, proposed): 2026-11-13 | T-749 | two merged ledgers listed the same door reveal under an interior
and an exterior code | a reveal through the wall is one physical surface whichever face lists it | wire an opening's
edge once per opening id across all edge codes, assert equality before dropping the duplicate (R-T749-1 d) |
tests/t749_paint_wiring | PROPOSED.

## 7. Validation

tests/t749_paint_wiring (27): synthetic villa W749 by hand (room paint restated inside its plaster, door return -> EXCLUDED
+ edge 0 .. 0.900, arch blank, windows incl. a half-circle head developed 3.884956, corner groups, totals by hand,
outside byte-identical, mirror order, held never 0, exterior door counted once) and adverse (paint above plaster,
stale range, released paint restated, blank edge numbered, 0 .. 0 edge, exterior DOOR line, one opening on two codes,
a door that is not its return's reveal, host released / not facade, VERIFIED, applied twice, two codes on lines);
development villa (entries rebuild equal, projection = the merged ledgers' totals, openings once, doors under their
returns, index V3.0.77 vs V3.0.76: only the 35 named lines changed, 68 added, released unchanged). L3 on the task
(m9_foundation, m9_p2b0/2/5/7/8/9, m9_s6, m9_p2a, m9_kb, t310, t478, t736, t729, t717 r2, t740, t746, t747, t751, t748)
exit 0; registry folders (t130, t140, t203, t212, t461, t463, t485, t525, t637, t651, t655, m9_kb) pass with the pending
1.78.0; freeze 0; codemap stale none. The Checker runs L4 (Gate B).
