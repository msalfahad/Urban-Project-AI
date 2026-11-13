# T-738: TILES H3 + STAIR FINISHES H3s integration package, ARCH_TAKEOFF_V3.0.78 (lane I; owner order step 5)

Worker 3, 2026-11-13. INTEGRATION PACKAGE for Checker Gate B. Base: the candidate of record V3.0.77 (T-749, Gate B PASS,
merge 8dc7c0f6, BOQ_FAMILY_MASTER 1.78.0 promoted c2106988). Released default V2.9 + route G untouched; nothing released,
nothing VERIFIED. No drawing, workbook, client name or coordinate here; Drive files named by folder and title only.
Reserved: ARCH_TAKEOFF_V3.0.78 + BOQ_FAMILY_MASTER_1.79.0 (pending; promoted IN the merge by `--promote`).

## 1. What is wired (Checker-merged only, sha-pinned in `t738_inputs.py`, `--check` rebuilds `out/T738_ENTRIES.json`)

| source | merge | Checker | wired as |
|---|---|---|---|
| T-702 `out/T702_TILES_ROUND3.json` part (b) | b90d85af | Verifier 2026-11-11T12:01Z Gate A PASS | 2 GF stair-core wall tile lines BOUND |
| T-715 `out/T715_LEDGER.json` (R-T715-1..4) | a4e4277a | Verifier 2026-11-11T20:02Z Gate A PASS | 81 stair finish lines + 1 new line |
| T-718 `out/T718_LEDGER.json` (R-T718-1..3, F-V715-1 closed) | 8052ca51 | Verifier 2026-11-11T22:12Z Gate A PASS | 4 lines restated over T-715 (declared) |
| T-733 `out/T733_H3_READINESS.json` (R-T733-1/-2) | 7146583d | Verifier 2026-11-12T07:58Z Gate A PASS | closes PENDING_ON of the two 1F tread highs (ENGINE_RIGHT) |
| T-730 `out/T730_ROWS.csv` (R-T730-1, hubs H3 2 + H3S 92) | 6143f30d | Verifier 2026-11-12T07:58Z Gate A PASS | the line-by-line map |

94 map rows = 87 entries + 7 statements (KEEP 2F landing L-5d2be30d, WIRING_GAP T-493; 4 T-715 BESIDE rows SUPERSEDED by
T-718; 2 T-718 soffit rows DUPLICATE of T-715's same figure). Every entry binds its V3.0.77 line as the map read it
(item, element, unit, class HELD, blank or range against the index 60982bb7): stale = stop. Stale hosts found: 0.

## 2. Method (R-T738-1, every villa; module `engine/source/arch_v3078.py`)

- PHYSICAL ELEMENTS: (a) the tiled wall face of the stair core, floor finish to the tile top, net of openings; (b) per stair
  flight: the visible riser faces (m2), the tread plan (m2), the nosings (lm), the pitch line (lm), the skirting strip on
  each walled side (lm, one of two payable forms), the soffit (m2). One physical flight is carried ONCE.
- Owner manual method vs drawing-derived method: tile = run x height less openings (UP-CER) vs T-702 (b) drawn run x tile
  top 2.20 (highest head, Q-55 C) .. +4.65 - floor +0.30 (ceiling datum, Q-48 A) less openings; stair = n x width x visible
  riser (UP-STAIR-006 t = 0.030), goings x hypot(going, riser), per walled side vs the drawn front edges / riser lines by
  handle (T-410 / T-412 / T-415 / T-684 / T-690 / T-718), turn regions tiled by area (R-T715-2).
- Forms: POINT (HELD low = high, never released here), BOUND, EXCLUDE (DUPLICATE_READING naming its live carrier of the
  same code, or NO_PHYSICAL_ELEMENT), AT_LEAST / AT_MOST / CONDITIONAL (ORR-007) beside a blank line (never in a total),
  NAMED (cause restated), ADD_POINT (new line beside its host, never summed into it).
- Older checks V3.0.64 .. V3.0.76 re-run on the result; the 30 return-paint lines V3.0.77 excluded are shown to them in
  their V3.0.76 form, rebuilt from the 'was' of their V3.0.77 record (`older_view`); V3.0.77's own check runs on the lines
  as they are. Totals: only the 9 tile / stair codes move, each exactly by the changes (asserted).

## 3. Lines (WORKFLOW_CONTROLS s.5 status per line in the ledger; nothing VERIFIED)

| code (family) | V3.0.77 | V3.0.78 | by hand |
|---|---|---|---|
| FIN.WALL.TILE m2 (B4-01) | released 12 / 340.3038; blank 6 | released unchanged; **bounded 2: 18.44 .. 44.765**; blank 4 | GF-10 6.20 x 2.20 - 2.24 = 11.40 .. 6.20 x 4.35 - 1.76 = 25.21; GF-11 4.90 x 2.20 - 3.74 = 7.04 .. 4.90 x 4.35 - 1.76 = 19.555 (ASSUMED — OWNER-APPROVED Q-55 C / Q-48 A; floor C-SH-2 named) |
| FIN.MARBLE.RISER m2 (B7-03) | released 1 / 1.96; blank 13 | released unchanged; **points 8: 10.497310; bounded 2: 2.589431 .. 3.242513** (held 13.086741 .. 13.739823); excluded +4 | 12 x 1.15 x (4.20/25 - 0.03) = 1.9044 (x2); 12 x 1.15 x 0.136667 = 1.886; 10 x = 1.571667; 4 x 1.15 x 0.145 = 0.667; 11 x 1.15 x (4.50/28 - 0.03) = 1.653536; 5 x = 0.751607; closing riser 1 x 1.15 x 0.138 = 0.1587 (ADD); turn 0.785833 .. 5 x 1.626346 x 0.136667 = 1.111337; curved 13.798023 .. 16.304073 x 0.130714 = 1.803598 .. 2.131176 (T-718) |
| FIN.MARBLE.TREAD m2 (B7-02) | released 8 / 23.3694; bounded 3: 0 .. 8.924413; blank 2 | released unchanged; **point 1.3225**; blank 1 (RS-C, D-08 named); excluded +3 | winders tile the 1.15 x 1.15 turn = 1.3225; 1F exposures 0 .. 4.094413 / 0 .. 3.45 / 0 .. 1.38 = the GF flights seen through the void: EXCLUDED, carriers L-fa534ec5 / L-89c84fdd / its F4 line |
| FIN.STAIR.FLIGHT lm (B7-01) | blank 14 | **points 7: 20.234818**; blank 2 named; excluded 5 | 11 x hypot(0.30, 0.168) = 3.782209 (x2); 11 x hypot(0.30, 0.166667) = 3.775064; 9 x = 3.088689; 3 x hypot(0.30, 0.175) = 1.041933; 10 x hypot(0.30, 0.160714) = 3.403367; 4 x = 1.361347 |
| FIN.STAIR.STEP_LM lm (B7-06) | released 7 / 67.85; bounded 3: 0 .. 29.8964; blank 2 | released unchanged; **bounded 2: 19.55 .. 24.653168**; excluded +3 | winders 5 x 1.15 = 5.75 .. 5 x 1.626346 = 8.131728; RS-C 13.80 .. 16.52144 (T-718) |
| FIN.MARBLE.LANDING m2 (B7-04) | released 2 / 10.1019; bounded 2: 0 .. 12.147501 | released unchanged; bounded 1: 0 .. 9.225001 (2F, KEEP); GF EXCLUDED | GF bound 0 .. 2.9225 holds no landing (T-493): NO_PHYSICAL_ELEMENT |
| FIN.STAIR.SKIRTING.SLOPED lm (B7-08) | blank 22 | **bounded 2: 2.35 .. 2.881166**; blank 18 with beside: CONDITIONAL ORR-007 13 = 17.009045, AT_MOST 4 = 6.545464, AT_LEAST 1 = 0.168; excluded 2 | corner walls plan 1.15 / 1.20 .. R-T715-4 sloped ceilings 1.420192 / 1.460974 |
| FIN.STAIR.SKIRTING.ZIGZAG lm (B7-07) | blank 22 | **bounded 2: 2.35 .. 4.016668**; blank 18 with beside: CONDITIONAL ORR-007 14 = 23.468477, AT_MOST 4 = 8.671486; excluded 2 | 1.15 + 5 x 4.50/27 = 1.983334; 1.20 + 0.833333 = 2.033334; form pair 13 pieces 17.009 (sloped) .. 23.300 (zigzag) + MS2-TR 0.168 |
| FIN.STAIR.SOFFIT m2 (B7-15) | blank 2 | blank 2, AT_LEAST beside 20.423364 + 4.460946 = 24.88431 (never a total) | min(O, D) of the measured rows (T-281); no drawn ceiling (D-67 / D-08) |

Code totals (index convention, released / held) moved only for the codes above, released unchanged in every one
(asserted): RISER held 0 -> 13.086741 .. 13.739823; TREAD held 0 .. 8.924413 -> 1.3225 .. 1.3225; FLIGHT 0 -> 20.234818;
STEP_LM 0 .. 29.8964 -> 19.55 .. 24.653168; LANDING 0 .. 12.147501 -> 0 .. 9.225001; WALL.TILE 0 -> 18.44 .. 44.765;
SLOPED 0 -> 2.35 .. 2.881166; ZIGZAG 0 -> 2.35 .. 4.016668; SOFFIT no total move (figures beside only).
Per line: `out/V3_0_78_INTEGRATION_LEDGER.csv` (before V2.9 / V3.0.77 / after, beside, rule, status, merge commits).

## 4. Run of record, census, diff

Drive 'Alsenan chalet project' copies 'P7757_DXF_COMPRESSED.zip' (inner P7757.dxf ab54dd55) and 'ST7757 dxf.dxf'
(9f9d1179), decoded by the wrapper into the private folder only: own fresh t167 `v304_run.py` (exit 0) -> `v3078_run.py`
(exit 0): every earlier version re-run and asserted by its own wrapper, **V3_0_77 b8524d5c (asserted = the T-749 run of
record by its line index) -> V3_0_78 f0c3a619**, 5,242 lines; replaced 86, added 1, outside 5,155 byte-identical
(asserted); the older checks V3.0.64 .. V3.0.77 pass on the result (V3.0.74 finishes return_bound 27 / blank 3 on the
older view, V3.0.77 paint rule unchanged). Diff vs V3.0.77: CHANGED 86, ADDED 1, SAME 5,155. vs released V2.9 + route G:
NOT_IN_RELEASED 3,650 (+1), QUANTITY_DIFFERS 1,086 (+32), SAME_QUANTITY 506 (-32): 32 lines that carried V2.9's own
state (blank, or the same 0 .. x bound) now carry a held figure or an exclusion.
Census `t479_registry_census.py` (verdicts V3.0.44 b3b08dd7, downgrades 81732639): on V3_0_77 it reproduces
`research/agents_t749/out/LINE_INDEX_V3_0_77.json` byte for byte; on V3_0_78 -> `out/LINE_INDEX_V3_0_78.json`, issues {},
complete map, stale blocks 0; 45 index entries differ from V3.0.77 (all named; the other 41 changed lines are blank ->
blank with a figure or a cause in their record), 1 added; downgrades unchanged; no released entry moved.
`t738_package_families.py` (77 -> 78): B4-01 changed 2; B7-01 12 (+2 record); B7-02 4 (+1 record); B7-03 13 + 1 added;
B7-04 1; B7-06 5; B7-07 4 (+18 record); B7-08 4 (+18 record); B7-15 record 2. Registry 1.79.0 pending (0 problems).

## 5. Engine vs freelancer, verdicts, findings, held / missing, downstream

- Freelancer: steps as PIECES (ST-01 63, ST-02 28, ST-03 5 at 1.20 width) and 96 stair-skirting pieces; his stair marble
  is not itemised by flight and his wet rooms not by room: line level NOT_COMPARABLE; riser / skirting unit RULE_DIFFERENCE
  (pieces vs m2 / lm); width ENGINE_RIGHT 1.150 drawn front edge vs his 1.20 (T-715); duplicate readings were ENGINE_WRONG
  (double count 0 .. 8.924413 m2 tread + 0 .. 29.8964 lm nosing held highs) and are corrected here by exclusion.
- vs released V2.9: winder nosings V2.9 4.7815 lm < 5 x 1.150 floor (R-T715-2) -> V3.0.78 5.75 .. 8.131728: ENGINE_RIGHT
  (candidate); winder treads V2.9 1.495 m2 vs the drawn 1.150 x 1.150 turn 1.3225: the V2.9 figure is 0.1725 m2 (= 0.150 x
  1.150) larger; T-715 R-T715-2 governs (Checker-merged); the released default is not touched.
- F-T738-1 (older checks on a newer base): V3.0.74's check rejects the 30 return lines V3.0.77 excluded when it runs on
  V3.0.77 lines; fixed by showing them in their V3.0.76 form rebuilt from their own record (no older module edited).
- F-T738-2 (statement form): 7 map rows move nothing (KEEP / SUPERSEDED / DUPLICATE); carried on the run record, never wired.
- Held / missing: ORR-007 (27 form figures beside, both forms never summed), D-67 (winder subdivision: walking line,
  per-winder split), D-08 / RFI-S27 (RS-C tread, curved pitch, soffit waist), C-SH-2 (tile floor level), T-493 2F landing
  lines (WIRING_GAP), MS1-U.E3b CONFLICT cap and GF hidden opening sill (AT_MOST caps). No waste factor (materials stage).
- Downstream: none outside the 9 codes (asserted). Tile adhesive / bed quantities (Q-45) are not formed from held lines.

Lessons row (ERS s.7, proposed): 2026-11-13 | T-738 | the V3.0.74 state check refused the return-paint lines V3.0.77 had
excluded once a package built on V3.0.77 re-ran it | an older check knows only the forms of its own time; a later
exclusion is a new form, not a regression | when re-running older checks on a newer base, show each line a later version
changed in the form that version recorded as 'was' (from its own record, never re-derived) and run the later version's
check on the line as it is | tests/t738_tile_stair (older view restored; other lines the same object) | PROPOSED.

## 6. Validation

tests/t738_tile_stair (36): villa W738 by hand (tile bound, riser / pitch points, a flight read twice excluded to its
carrier and counted once, winder bound, ORR-007 siblings beside never summed, AT_MOST / AT_LEAST, landing with no element,
closing riser added, totals by hand, outside byte-identical, mirror order) and adverse (VERIFIED, stale, released restated,
cap 0, conditional off ruling / off skirting, wrong sibling, duplicate without carrier / carrier excluded / other code /
wrong element, applied twice, point 0, bound low > high, add with an own id, named with a figure, line twice, tile piece on
a stair line); development villa (entries rebuild equal, 94 rows once, every point and bound by hand from its basis, T-718
over T-715, carriers live, ORR-007 pairs, stale pin refused); older view. L3 on the task: m9_foundation, m9_kb, m9_p2a,
m9_s6, m9_p2b0 / 2 / 5 / 7 / 8 / 9, t310, t478, t702, t715, t717, t718, t723, t729, t730, t733, t736, t740, t746, t747,
t748, t749, t751, t754 pass; registry folders (t130, t140, t203, t212, t461, t463, t485, t525, t637, t651, t655) pass with
the pending 1.79.0; freeze 0; codemap stale none. The Checker runs L4 (Gate B).
