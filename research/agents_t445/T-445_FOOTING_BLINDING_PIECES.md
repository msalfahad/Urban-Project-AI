# T-445 Foundation blinding as pieces; the candidate STR.CONC.BLINDING lines and the -47.055 m3 item reconciled (development villa; method every villa)

Worker 1 (lane S), 2026-11-02, run session_01E6cPnavebCyineE9tQxaNK. Research piece, unwired: no engine, candidate,
released, rule or knowledge file changed; integration is a stream S / lane I package after the Checker's verdict.
Development villa, not an accuracy claim. Drawings named by Drive folder and title; entities by DXF handle; sizes and
areas only (no positions committed).

Files: `blinding_piece_ledger_v1.py` (BLINDING_PIECE_LEDGER_V1, shapely), `t445_extract.py` (own DXF read into
`.work/private`, values only), `t445_alsenan.py` -> `LEDGER_T445.csv`, `summary_t445.json`; input
`ALSENAN_BLINDING_INPUT.json`; tests `tests/t445_blinding_pieces` (16).

## 0. Inputs (own reads this task)

| Input (Drive "Alsenan chalet project") | sha256 | Read for |
|---|---|---|
| "ST7757 dxf.dxf" | 9f9d1179...38079 (= T-233 / T-322) | the 26 FOUNDATION PLAN outlines by handle, the plot line S-BOUN 1658 (31.37 x 15.00); polygons grown 0.10 mitred, union and clip with shapely (`--geometry`): every area below re-derived, AGREE with T-233 per outline to 1e-6 |
| "ST7757.pdf" | 74da1523... | p.13 (60 dpi whole sheet): both typical isolated footings on '10cm Plain con.' ('10 \| L x W \| 10' on the < 2.5 m detail), the four ground-beam sections on a 10 cm base 10 / 30 / 10, 'COMPACTED SOIL' under the ground slab, no strap section; p.14 (60 / 240 dpi): lift detail '10cm Plain con.' with no projection dimension, TYPICAL BOUNDARY WALL SECTION (A-A): blinding 10 thick, '80' + '10' past the toe, flush with the outer face of the lower (G.B) |

Merged, read only: T-233 (outlines, 15.179437 union), T-320 / T-322 (24 pits 12.734438 VERIFIED, FF HELD >= 2.070),
T-347 (candidate line contents), T-433 (item I-01 / BL-1 = the same 4 line ids), T-469 (V3.0.41 keyed row: held 4 lines
21.059 .. 25.964 = the sum of the 4 lines, asserted), DG-3521554d2fd011b9 (whole footing line HELD), RFI register
2026-10-31 and the RFI RE-REVIEW 2026-11-02 (S02 range, S08 ESTIMATED).

## 1. The physical element (ERS s.2.1)

Blinding = plain concrete 0.10 (printed, p.13 / p.14) on the formation, under a member, where a detail draws it: the
24 isolated pit footings (p.13 typical, projection 0.10 printed), the FF lift raft (p.14, its own governing detail, no
projection printed), the F10 + F outline (follows its footing), the ground beams (p.13 sections), the boundary-wall base
(p.14 A-A). NOT under the ground slab ('COMPACTED SOIL', p.13), no strap section on any sheet (D-15). Underlay (screed,
membrane) is another trade. One layer where grown plans overlap; the overlap belongs to the deeper footing.

## 2. Piece table (LEDGER_T445.csv; m2 / m3, t = 0.10)

| Piece | Drawing + handles | Plan m2 | Thickness | m3 | Status | Candidate line |
|---|---|---|---|---|---|---|
| 24 pit footings inside the plot (F x4, F2 x2, F3 x2, F4 x2, F5 x2, F6, F8, F9, F11, F12, F13, F14, F15, FN x4: 165C 1663 1664 1665 1666 1667 1668 1669 166A 166B 166C 166D 180C 180F 1ABF 1ADB 1B07 1B19 1B1A 1B24 1B2A 10F0 10F8 1100) | DXF FOUNDATION PLAN + p.13 '10 \| L x W \| 10' | 129.430 grown - 0.195625 overlap once (180C -> 180F 0.19, 10F0 -> 1B24 0.005625) - 1.890 beyond = **127.344375** | p.13 printed | **12.734438** (exact 12.7344375) | **VERIFIED** (Checker T-322, 2026-10-29) | L-98eb2d58 |
| beyond the plot line at 8 footings (1668 0.11, 1669 0.20, 166A 0.11, 1B07 0.37, 1B1A 0.40, 1B24 0.38, 1B2A 0.20, 1100 0.12) | same | 1.890 | printed | HELD 0 .. 0.189 | HELD (RFI-S06, D-14) | L-98eb2d58 |
| FF lift raft 1B2B | p.14 governing, projection not printed | 20.70 raft; 22.56 (p 0.10) / 23.52 (p 0.15) | printed | HELD 2.256 .. 2.352, AT_LEAST 2.070 (S08 ESTIMATED 2.352 by the 2026-11-02 label) | HELD / ESTIMATED, never VERIFIED | L-98eb2d58 |
| F10 + F outline 1B1B | p.2 / DXF one outline, two tags | scenarios: F10 alone 3.00 x 1.60; F10 + F rows 4.80 + 1.10; drawn outline 3.45 x 1.60 (0.495 beyond) | printed | CONFLICT 0.480 / 0.590 / 0.552 -> **0.480 .. 0.590** | HELD (RFI-S02, owner scenarios) | L-080c97f5 |
| ground beams | p.13 four sections on 10 / 30 / 10 | not re-measured (T-100 reading R 96.91) | printed | HELD 4.949374 .. 9.422514 (candidate) | HELD (RFI-S09 + S11) | L-7a5214a3 |
| straps SB1-SB3 | no section | 9.13 (ledger) | - | HELD 0.377803 .. 0.771877 (candidate); ledger 0 .. 0.913 (F-T347-2, kept) | HELD (RFI-S07, D-15) | L-35382b18 |
| boundary-wall base | p.14 A-A: 0.80 + 0.10 past the toe, under the pads (130 x 80 x 30) | count not printed | printed | **no figure**; AT_LEAST 1.30 x 0.90 x 0.10 = 0.117 per pad | HELD (UNMEASURED; M2 pad count, RFI-S04 column spacing; under the band between pads not drawn) | **MISSING** |
| ground slab | p.13 'COMPACTED SOIL' | - | - | none | NOT_PRESENT (no sheet draws it) | none |

Own test: the 24 pit pieces re-add to 12.7344375 m3 exactly and equal the T-320 / T-322 12.734438; the 180C / 180F and
10F0 / 1B24 overlaps are given to the deeper F9 (0.55) / F8 (0.50); FF clears every pit's grown plan in the 0 / 0.10 /
0.15 readings (F12 1ABF 0.5998 m), so its hold touches no measured piece.

## 3. The candidate lines re-added (V3.0.24 contents = V3.0.41, asserted)

| Line | Candidate | Pieces | Residual | Cause |
|---|---|---|---|---|
| L-98eb2d58 footings PROVISIONAL, HELD whole by DG-3521554d | 15.179437 | 12.7344375 VERIFIED + 2.256 FF at the INHERITED p.13 p = 0.10 + 0.189 beyond the plot line | 0.0000005 (6-dp rounding) | one line mixes a verified layer with two held pieces; a downgrade cannot split a line |
| L-080c97f5 F10 + F BOUNDED | 0.552 .. 0.590 | drawn outline 0.552, rows separately 0.590 | 0.000 | the owner's third scenario (F10 alone 0.480) is outside the line (F-T445-2) |
| L-7a5214a3 ground beams BOUNDED | 4.949374 .. 9.422514 | GB piece (candidate range) | 0.000 | not re-measured here |
| L-35382b18 straps BOUNDED | 0.377803 .. 0.771877 | strap piece (candidate range) | 0.000 | ledger 0 .. 0.913 kept beside (F-T347-2) |

## 4. The roll-up blinding item -47.055 m3 (T-433 I-01 / BL-1) term by term

Residual = engine valued - freelancer = 0 - 47.055 (none of the 4 lines is valued). His figure = 15.00 x 31.37 x 0.10 =
the plot line 1658 rectangle exactly (own read). Each piece inside the plot is one term (engine valued figure - piece);
pieces beyond the plot line are not in his rectangle (0 - 0, listed beside); the remainder is the scope RULE_DIFFERENCE.

| Term | m3 (low .. high) | Cause / blocker |
|---|---|---|
| 24 pits VERIFIED, not valued | **-12.734438** | candidate line held whole by DG-3521554d (VALUE after the split) |
| FF raft | -2.352 .. -2.256 | RFI-S08 (S08 ESTIMATED 2.352) |
| F10 + F | -0.590 .. -0.480 | RFI-S02 (three scenarios) |
| ground beams | -9.422514 .. -4.949374 | RFI-S09 + S11 |
| straps | -0.771877 .. -0.377803 | RFI-S07 |
| boundary-wall base | no figure (inside the remainder) | pad count not printed |
| **RULE_DIFFERENCE**: his one layer over the whole plot (no sheet draws it; 'COMPACTED SOIL' under the slab) | **-26.257386 .. -21.184172** | scope, not a measurement error; survives every RFI answer |
| beside: 0.189 beyond the plot line | (0 - 0) | RFI-S06 |
| **Total** | **-47.055000** at both ends | closes exactly, no piece in two terms |

After the lane I split (proposal A, value only the verified pits): engine 12.734438 vs 47.055 = -34.320562 m3 (-72.94 %),
of which -21.184 .. -26.257 m3 is the RULE_DIFFERENCE (45.0 .. 55.8 % of his figure) and the rest held by S02 / S07 /
S08 / S09 / S11. With FF valued ESTIMATED 2.352 (proposal B): 15.086438, -31.968562 m3 (-67.94 %).

## 5. Lane I proposal per line id (stream S; downgrade-only where noted)

1. **L-98eb2d58 SPLIT** into three lines: (a) VALUE 12.734438 m3 VERIFIED, 24 pits inside the plot, verdict T-322,
   pieces by handle (LEDGER_T445.csv); (b) FF 1B2B HELD 2.256 .. 2.352 (AT_LEAST 2.070), or ESTIMATED 2.352 under the
   S08 label with the range visible, never VERIFIED; (c) beyond the plot line HELD 0 .. 0.189 (S06). DG-3521554d is
   then resolved by the split (its content no longer exists), recorded through the downgrade check, not deleted.
2. **L-080c97f5 HELD, range widened** 0.552 .. 0.590 -> 0.480 .. 0.590 (F10 alone / F10 + F / outline), the same
   scenario as the footing concrete (owner 2026-11-02: never mixed across trades).
3. **L-7a5214a3 HELD unchanged** (S09 / S11). **L-35382b18 HELD unchanged** (S07; the 0 .. 0.913 ledger beside).
4. **NEW held line** (MISSING today): boundary-wall base blinding, UNMEASURED (no figure, never 0) until the pad count
   exists; per pad AT_LEAST 0.117 m3.
5. Never the freelancer's rectangle; no thickness or projection the sheets do not print.

## 6. Findings

- **F-T445-1** the footing-blinding line is the only CONC.BLINDING line with a VERIFIED part (12.734 m3, 27.06 % of his
  figure) and it is valued nowhere: the downgrade that holds it was correct for the FF piece only.
- **F-T445-2** L-080c97f5 excludes the owner's F10-alone scenario (0.480 m3; concrete 1.960 m3 is the owner's stated
  low end): a held-range correction, no released figure moves.
- **F-T445-3** his 47.055 m3 is the plot polygon x 0.10; at most 25.871 m3 of it is blinding any sheet draws (pieces at
  their high ends): the rest is RULE_DIFFERENCE (ENGINE_RIGHT on scope; FREELANCER basis printed nowhere).
- **F-T445-4** the boundary-wall base blinding (p.14 A-A) is printed but carried by no candidate line: a MISSING piece,
  UNMEASURED (pad count not printed, M2).
- **F-T445-5** under S01 ESTIMATED (founding 1.5 m below the plot level) the p.13 '< 2.5 m' typical governs the pits,
  i.e. the detail with the printed 0.10 projection; the two-beam detail (no projection printed) does not apply. The
  ground-beam blinding stays held on S09 / S11 only (not re-measured here).

Verdict proposals: 24 pits ENGINE_RIGHT (Checker-verified layer, unvalued); FF UNRESOLVED (S08); F10 + F UNRESOLVED
(S02); GB / straps UNRESOLVED; whole-plot plate RULE_DIFFERENCE.

## 7. Rule, test, lessons row

R-BLIND-PIECE-1 (proposed, every villa; provenance T-445; a new rule version when adopted): the eight rules in the
module docstring (printed t; printed projection on the governing detail else HELD AT_LEAST; one layer, deeper owner,
ties refused; beyond the boundary its own HELD piece; two-tag outlines a CONFLICT of scenarios; members with no drawn
blinding HELD_RANGE; a plate refused as a piece; every piece on one line, every line re-adds, mixed lines SPLIT).
Tests `tests/t445_blinding_pieces` (16): villa B by hand (3 pits + a raft: 0.698 VERIFIED, raft 1.344 .. 1.419 AT_LEAST
1.200, beyond 0 .. 0.012, line 2.054 SPLIT, plate 24.000 split closing both ends); m / mm, mirror, quarter turn
identical; adverse: one rectangle over the whole footprint counted as drawn (PLATE_COVERS_MEMBERS, PLATE_NOT_DRAWN),
thickness / projection not printed, equal-depth overlap, held with value, 0 piece, held without blocker, VERIFIED
without verdict, beyond without blocker, one-reading conflict, unmeasured valued, estimate without label, plate figure
as the line, piece on an unknown line, line without piece, held raft reading touching a neighbour; Alsenan pins.

Lessons row proposed (ERS s.7): 2026-11-02 | 12.734 m3 of Checker-VERIFIED footing blinding valued in no candidate line
while the roll-up showed one -47.055 m3 blinding lump | a downgrade holds a whole line, so one held piece (FF, inherited
projection) withheld the verified pieces of the same line; the comparison item was never split into pieces | a blinding
line is built from pieces, each with its own status; a line mixing VERIFIED and held pieces is SPLIT, never held whole;
a reference plate is split into one term per piece plus the scope remainder (every villa) | tests/t445_blinding_pieces
(SPLIT proposal; plate refused as a piece; split closes at both ends) | PROPOSED.

## 8. For the Checker (re-measure two pits) and not done

1. F12 1ABF 4.40 x 3.20 -> 4.60 x 3.40 = 15.64 m2 -> 1.564 m3, wholly inside the plot, no overlap.
2. FN 180C (notched 0.86 m2 outline) -> grown 1.30 m2, of which 0.19 m2 lies in F9 180F's grown plan (F9 0.55 deeper
   owns it) -> 1.11 m2 -> 0.111 m3; F9 180F 3.40 x 2.70 -> 10.44 m2 -> 1.044 m3.
3. p.14 A-A blinding 0.80 + 0.10 and the pad note '(130x80x30)'; p.13 'COMPACTED SOIL' under the slab.

Not done: ground-beam blinding not re-measured (the candidate range is carried); strap blinding basis (D-15) and the
pad count are designer items; no candidate line changed; nothing released.
