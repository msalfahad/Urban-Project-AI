# T-377: cross-trade audit of the arched-opening lesson (development villa; rule for every villa)

Worker 2 (lane A), claim 2026-10-30 16:44 UTC, run session_01E6cPnbBsdQH3SQzr7TqWqx, base working head 8f2b0354.
Research only (`research/agents_t377/*`, `tests/t377_arched_audit/*`): no engine module, rule or knowledge file, merged
ledger, candidate line, released line or V2.9 cell changed; nothing corrected here, nothing released, nothing VERIFIED.
ERS applied: s.2.1 (the physical element first), s.2.3 (own re-read of the arch chains), s.2.4 (every difference in
units), s.3 (one element, several trades; build before deduct), s.4 (rule + regression test), s.7 (lesson row, s.8).
Drawings cited by Drive title and DXF handle; no coordinate, image or client name committed.
`python3 -I research/agents_t377/t377_alsenan.py --check` reproduces `AUDIT_T377.csv`, `HELD_CHECK_T377.csv`,
`CANDIDATE_T377.csv` and `summary.json` from repository files.

## 1. Result in engineering terms

The Checker's D-T326-1 (T-326 r1 REJECTED 15:35) is not isolated: the same rectangle sits in **four merged ledgers and
three pending carriers** outside T-326. Masonry, interior plaster / paint and exterior hole deductions are on the outline
(correct, 0.0002 - 0.0003 m2 from it); the sills / thresholds and skirting breaks are WIDTH_ONLY (correct: below the
springing); the window unit keeps the owner's Q-32 A rectangle (a RULE, correct for that line only).

| Trade (ledger -> carrier) | Openings | Basis now | Now | On the outline | Difference |
|---|---|---|---|---|---|
| Outside reveal jambs + head, m2 (T-313 r2 / T-340 -> **T-326 r2**) | W15, W16, W26 | RECTANGLE: band crown 3.10 / crown 1.70 | 0.620 + 0.620 + 0.460 = 1.700 | 0.5477 + 0.5477 + 0.4071 = 1.5025 | **+0.1975 m2 (+13.1 %)** = the Checker's 0.1976 |
| Same reveal, edge m.l column (T-340 FILL_T326 -> **T-326 r2**) | W15, W16, W26 | RECTANGLE | 7.75 + 7.75 + 4.60 = 20.10 | 6.8461 + 6.8461 + 4.0709 = 17.7631 | **+2.3369 m (+13.2 %)**: r2 must correct the m.l as well as the m2 |
| Opening arrises / corner bead, exterior Sigma (T-162 CORNERS, confirmed by T-313 EDGE_RECONCILIATION -> **T-314**) | W15, W16, W26 | RECTANGLE | 7.75 + 7.75 + 5.80 = 21.30 | 6.8461 + 6.8461 + 5.2709 = 18.9631 | **+2.3369 m (+12.3 %)** |
| Same, W17 (T-162) | W17 | RECTANGLE to the archivolt 3.50, status PRINTED | 10.290 m | HELD (T-238 A5) | breaks the hold: **carry HELD, blank** (R-T377-2) |
| Spatter dash bound to the reveal carriers (T-349 -> **T-364**, after T-326 r2) | W15, W16, W26 | follows the reveal rectangle | 1.700 m2 | 1.5025 m2 | **+0.1975 m2** |
| Bed-joint mesh strip, white walls (T-362 1F-W00 -> **T-363**) | W15 + W16 | full width 2 x 1.55 cut at the levels inside the arch | cut 3.10 m at each of 4 levels | chord 2 x 0.4180 .. 1.5515 | spandrel strip 1.8298 .. 2.1724 m (family A) / 1.9156 .. 2.3398 m (family B) cut as certain: **HELD by name** |
| Same, W26 on 2F-W07 (T-362 -> T-363 bound text) | W26 | rectangle 1.20 inside a HELD bound | 1.2000 | 1.1520 .. 1.1979 | none valued (held part only) |
| Opening head field (T-237 OPENING_SIZES, read by T-355 / T-362) | W15, W16 | band crown 3.10 | 3.10 | crown 3.00 | 0 m today (no course level lies between 3.10 and 3.20 above the 1F-W00 base): a T-363 input note |

Net effect on the pending carriers: reveals -0.1975 m2 and -2.3369 m (T-326 r2), exterior opening arrises -2.3369 m
plus W17 10.290 m -> HELD (T-314), spatter -0.1975 m2 (T-364), mesh strip: 1.83 .. 2.34 m per family moves from
"cut" to HELD (T-363). Nothing in the released V2.9 or in the V3.0.27 candidate of record moves (section 4).

## 2. The physical element (ERS s.2.1)

An arched opening is a hole with straight jambs from the sill to the SPRINGING and a curved head from the springing to
the crown. A reveal, an arris, a bead, a return, a spatter coat on the reveal and a bed-joint accessory cut at the hole
follow the hole's edge: 2 x springing + developed arch (+ the sill edge where it is part of the item), and at a height z
the hole is as wide as the chord at z. The size-table rectangle (width x crown, or width x band crown where a surround
band is drawn) is not the hole. Two measures keep the rectangle on purpose and are not errors: the window unit (owner
Q-32 A, enclosing rectangle on the opening line) and everything that depends on the width only (sill, threshold, floor
strip, skirting break), because the arch does not reach the sill.

## 3. Evidence and own re-read (ERS s.2.3)

Outline record: T-238 CENSUS (MERGED; W15 outline VERIFIED by the Checker under T-227, 4.3629 m2). Own re-read this run
(Drive "Alsenan chalet project" / P7757_DXF_COMPRESSED.zip, P7757.dxf sha256 ab54dd55, decoded into the private folder
only): shortest connected path of layer-1 LINEs from jamb top to jamb top, long horizontals / verticals excluded.

| Opening | Jambs / chain (handles) | Width | Springing | Rise | Segment | Arch | Hole | T-238 |
|---|---|---|---|---|---|---|---|---|
| W15 | 2889 / 288A, 299F .. 299E (46 segments) | 1.5523 | 2.1609 | 0.8391 | 1.0086 | 2.5241 | 4.3629 | 4.3632 |
| W16 | 2566 / 256A, 274C .. 274B (49) | 1.5523 | 2.1609 | 0.8391 | 1.0086 | 2.5241 | 4.3629 | 4.3632 |
| W26 | 2211 / 2229, sill 2319, 1C67 .. 222E (29) | 1.2000 | 1.0500 | 0.6500 | 0.6145 | 1.9706 | 1.8745 | 1.8747 |

The audit values use the T-238 record (the merged one); the re-read agrees within 0.0003 m2 / 0.0003 m. The re-read
also gives the chord at the merged T-362 mesh levels (wall-base levels; the opening starts at FFL = base + 0.10):
W15 / W16 springing 2.2609, crown 3.10; W26 (sill 1.10) springing 2.25, crown 2.90.

| Wall, family, course k | Level (m) | Chord (m) | Cut now (m, per opening) |
|---|---|---|---|
| 1F-W00 A 3 | 2.268 .. 2.294 | 1.5515 .. 1.5484 | 1.55 |
| 1F-W00 A 4 | 3.021 .. 3.053 | 0.6336 .. 0.4654 | 1.55 |
| 1F-W00 B 4 | 2.421 .. 2.453 | 1.5244 .. 1.5121 | 1.55 |
| 1F-W00 B 5 | 3.024 .. 3.062 | 0.6178 .. 0.4180 | 1.55 |
| 2F-W07 A 3 / B 4 (W26) | 2.268 .. 2.294 / 2.421 .. 2.453 | 1.1979 .. 1.1949 / 1.1671 .. 1.1520 | 1.20 (inside a HELD bound) |

Why the mesh difference is HELD and not added: the masonry in the spandrels is physically built (the VERIFIED block
deduction is the outline, T-227), so a strip cut at full width there contradicts the block ledger; but what carries the
arch (a cut-block spandrel or a formed arch ring / lintel) is not established (T-355: "a lintel over an arch is not the
schedule's: span HELD"; the lintel matrix: BLOCKED_SUPPORT_IDENTITY under the S1 band). Build before deduct (ERS s.3): the
strip length beside the chord is HELD by name with its bound, never cut as certain and never counted as certain.

## 4. The V3.0.27 candidate of record

`CANDIDATE_T377.csv` lists every V3.0.27 line that cites one of the arched set's engine openings (1F OP-016 / OP-017 /
COP-001 / OP-011, 2F OP-008, GF OP-027), from this task's own V3.0.27 run (section 7; 3,913 lines = T-318's identity count). **33 lines, 0 on a rectangle**:

| Basis | Lines | What |
|---|---|---|
| OUTLINE | 8 | MAS.BLOCK / ARCH.WALL_PANEL / ARCH.WALL_VOLUME 1F (W15 4.3630, W16 4.3630 DEDUCTED) and 2F (W26 1.8750); FIN.PLASTER / FIN.PAINT 1F-13 (W15, W16 -> 4.3629) |
| RULE RECTANGLE (Q-32 A) | 2 | ARCH.WINDOW m2 1F settled 23.285 (W15 4.65 + W16 4.65 + ...), 2F 5.82 (W26 2.04) |
| HELD / HELD BOUND | 3 | ARCH.WINDOW W17 9.87 .. 11.515; FIN.PLASTER / FIN.PAINT 1F-11 61.4626 .. 61.7177 (T-302 developed room-side hole 8.7414 .. 8.9965) |
| WIDTH_ONLY | 3 | FIN.SKIRTING 1F (glazing edges), the A-1F-01 doorway strip 0.15 |
| BLANK (carrier pending) | 9 | ARCH.WINDOW_REVEAL W15 / W16 / W17 / W26 and ARCH.THRESHOLD A-GF-01 (T-326 / T-327); FIN.EXT.FINISH and ARCH.FACADE 1F NW / 2F SE (T-314) |
| NOT_APPLICABLE (count) | 8 | ARCH.WINDOW pcs, ARCH.PASSAGE pcs |

So the candidate of record is clean; every rectangle found sits in a merged ledger or a pending carrier and would enter
the candidate through T-326 r2, T-314, T-363 or T-364 unless corrected there.

## 5. Held set cross-check (acceptance c, R-T377-2)

`HELD_CHECK_T377.csv`, 42 rows over T-313, T-340, T-292, T-291, T-305, T-162, T-355, T-368: W17, A-GF-01 and A-1F-01 are
HELD / blank or a HELD bound everywhere (never 0), with two admissible exceptions: W17's masonry is NOT_APPLICABLE (glazed
host, T-291) and its exterior hole 8.1434 m2 is the merged T-302 developed hole. **One finding: T-162 CORNERS carries
W17's opening arris as 10.290 m PRINTED** (3.29 + 2 x 3.50, the archivolt crown): T-314 must carry it HELD, blank.

## 6. Rules (PROPOSED, every villa; provenance T-377, from D-T326-1 / R-T326-2 and T-238 UP-OPEN-ARCH-001 v1.1 A3)

- **R-T377-1** (`t377_arch_audit.check_value`): on an opening whose outline record is arched, a reveal (d x (2 x
  springing + developed arch)), an edge (2 x springing + arch, + width with the sill), a hole area (width x springing +
  segment) and a hole width at a height (the chord) are valued on the outline; a value equal to the rectangle to the
  crown or the band crown is refused; WIDTH_ONLY items and the Q-32 A window-unit rectangle are accepted; a rectangular
  opening keeps its rectangle.
- **R-T377-2** (`check_held`): an opening whose outline is HELD carries every edge quantity HELD (blank, never 0); a
  figure is admissible only as a HELD bound or from a named merged ledger that developed that very quantity.
- Proposed to the Lead as an extension of UP-OPEN-ARCH-001 (A3 "reveals and arrises follow the arch") to accessories
  cut at the opening and to coats bound to a reveal: a NEW rule version when filed, never an edit in place.

## 7. Run, validation

Own V3.0.27 run on the Drive copies (P7757.dxf `ab54dd55`, ST7757 dxf.dxf `9f9d1179`, the hashes T-318 cites), into the
private folder only: T-151 restricted run, T-167 base run, `research/agents_t318/v3027_run.py`. Tests:
`tests/t377_arched_audit/test_t377.py` (non-Alsenan villa T377-M by hand: semicircular window, segmental passage with an
independent strip integration, rectangular window; adverse: rectangle / band crown refused in reveal, edge, hole and
chord, unmatched value, missing depth, held as 0, a PRINTED figure on a held outline, millimetres, impossible arches,
mirrored profile; development villa: `--check` reproduction, the D-T326-1 values, every RECTANGLE row carried by a named
lane I row, the held-set finding).

## 8. Lessons-register row (proposed, ERS s.7)

| 2026-10-30 | After D-T326-1 the arched rectangle was found in 4 merged ledgers and 3 pending carriers outside T-326: opening
arrises (T-162, +2.3369 m, W17 10.29 m PRINTED on a held outline), the reveal m.l column, the spatter rows bound to the
reveals (+0.1975 m2) and the white mesh strip cut at full width inside the arch (1.83 .. 2.34 m per family) (T-377) | the
outline was applied where a ledger deducted an AREA (masonry, plaster, paint, exterior holes) but every ledger that
walks an EDGE or cuts at a LEVEL took jamb heights and widths from the size table; T-238's own delta recorded only the
arc-minus-chord head for the arrises and missed the jambs | every quantity built on an edge, head, jamb or level of an
opening reads the opening's outline record (springing, developed arch, chord at z); the size-table rectangle is admissible
only for the window unit (Q-32 A) and width-only items; a held outline holds every edge item (scope every villa;
provenance T-377, D-T326-1) | tests/t377_arched_audit (rectangle refused in reveal / edge / hole / chord; held as 0 and
PRINTED on a held outline refused; normal: rectangular opening and the arch by hand) | PROPOSED |

## 9. Held / unknown / missing (never 0)

The mesh strip beside the chord on 1F-W00 (arch support identity); W17's outline and every edge item on it (A5); A-GF-01
(D-45 candidate outline) and A-1F-01 (not drawn); the porch-mouth arch's face / soffit / arrises (T-238 F-PORCH-ARCH,
T-360 C-1); the lintel or arch ring over W15 / W16 / W26 (BLOCKED_SUPPORT_IDENTITY).
