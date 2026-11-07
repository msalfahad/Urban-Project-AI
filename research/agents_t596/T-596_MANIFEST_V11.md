# T-596 WIRING MANIFEST V11 + OVERLAY DRY RUN on ARCH_TAKEOFF_V3.0.58

Worker 3 (lane I, non-candidate), 2026-11-07. Not an integration package: nothing is wired; no candidate, released
(V2.9 + route G), rule, knowledge or registry file is touched; no drawing read (every figure from the committed,
Checker-merged outputs of T-595 (568ce15e), T-598 (78196c45), T-434 (a6b325b3), T-572, T-412 and the V9 / V10
manifests, sha256-pinned). Files: `manifest_v11.py` (R-T596-1), `out/WIRING_MANIFEST_V11.json`,
`tests/t596_manifest_v11/` (29). Rebuild: `python3 -I research/agents_t596/manifest_v11.py` (`--check`).

## 1. Overlay (R-T580-1 / R-T588-1 / R-T593-1 code, read only)

A COPY of the V3.0.58 index (4,999 lines) takes V2 .. V10 in the T-593 order (rebuilt; 5,124 lines = the committed V10),
with V9 REBAR_COMPONENTS replaced BY NAME on the same 6 line ids by REBAR_COMPONENTS_V2, then FOOTING_S02_BOUND:
**5,124 lines, 0 STALE, 0 two-package lines, 0 unexplained conflicts; every line V11 does not write is identical to the
V10 overlay.** The one flagged row is T-580's own NO_BEFORE (L-4ccc5dc2, T-498), not a V11 row. Totals move on two keys
only: STR.REBAR|kg held low 15,109.095712 -> 15,130.867712 (+21.772), STR.CONC.FOOTING|m3 held low 2.176 -> 1.960
(-0.216); every held high, open-high count and released total unchanged.

## 2. Rows (before = the V10 overlay)

| Package | Line | Before | After | Evidence |
|---|---|---|---|---|
| REBAR_COMPONENTS_V2 (supersedes V9 by name) | east dome ring NEW:STR.REBAR:HL:DOME_RING:DOME-1F-E... | HELD >= 122.518 kg, high open | **HELD >= 144.290 kg**, high open by name | PARTIALLY VERIFIED (T-595 09:56 (e)) |
| | 5 other lines (dome-3 shell, west ring, shells A / B, lift-pit walls) | as V9 | byte-equal | as V9 |
| FOOTING_S02_BOUND (R-T596-1 (c)) | L-164ae9d3 F10 + F (10A5) | HELD 2.176 .. 2.275 m3 (T-572 V1) | **HELD 1.960 .. 2.275 m3** | HELD (ESTIMATED, owner PROVISIONAL) |

Hand: (4 - 2) x 8.99725 m x 1.209877 kg/m = 21.771 kg; 122.518 + 21.771 = 144.289 (T-595 row 144.29, rounding).
Bounded rebar low 767.783 -> 789.555 kg (board 0.789554 t = rounding of parts, 1 g). F10 alone 2.80 x 1.40 x 0.50 =
1.960; outline 3.25 x 1.40 x 0.50 = 2.275 (high unchanged). B10 footing-line bounded part on the T-572 basis
7.8445 .. 13.9613 -> **7.6285 .. 13.9613 m3** (= T-595); family total still not stateable (boundary pads, Q-28 A).

## 3. Nosing ledger by edge id (Lead amendment; no B7-05 line in V3.0.58, T-424 wires it)

The 89 T-412 census edges, statuses superseded by id: 69 T-412 DC + N05 (T-434) + 19 by T-598 with F-C-T598-1 (MS2-U
floor edge ASSUMED - OWNER-APPROVED, Q-46 A) and RS-C 12 (Q-50 A cond). **Valued 107.371440 lm on 85 edges**
(DRAWING-CONFIRMED 90.800, ASSUMED - OWNER-APPROVED 16.571440); **HELD by name: N01 .. N04 4.600 .. 6.942620 + RS-C N01
band 0 .. 0.050 = 4.600 .. 6.992620**, never 0. Owner split: step lines (B7-06, in step basis) 93.750; nosing line
(B7-05) 13.621440 = 12.000 off-step edges + curtail sub-rows 0.949440 + 0.672000. Census after V11: 0 doubles / 0
orphans (89 edges). His 123.20 - ours 107.371440 = +15.828560 lm = count 8.400 + held 4.800 + width 4.000 + notches
0.250 - curtail 1.621440, residual 0 (no %).

## 4. Findings

- F-T596-1: curtail parts (RS-C N01 0.949440, N02 0.672000 lm) belong to the B7-05 line, not the step line
  (UP-STAIR-008, T-598 s.6): T-424 must carry them as sub-rows or they are orphaned.
- F-T596-2: RS-C N01's T-412 1.200 = 1.150 valued + 0.050 band HELD sub-row; the 0.050 is never valued with the edge.
- F-T596-3: 0.789554 vs 0.789555 t is rounding of parts; V11 carries T-595's row values.
- F-T596-4: the boundary-wall foundation beam L-6290a9f3 holds 7.2204 .. 7.2204 on the candidate (T-572 flag
  LINE_POINT_7.2204_IS_Q-28A_READING) vs T-572's 5.639 .. 11.033: the family bounded part is printed on the T-572 basis
  with the difference named; V11 does not move that line (no merged row targets it).

## 5. Lesson proposal (ERS s.7)

"A restatement supersedes by name on the same ids and moves only the low it restates: the high, the other rows and
every other line stay byte-equal, a lowered low needs the named accepted scenario set, and a row from an unmerged task
is refused" (any villa on the line-index scheme; T-595 / T-596; tests/t596_manifest_v11).
