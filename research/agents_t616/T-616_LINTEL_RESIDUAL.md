# T-616: lintel / deducted-opening count residual -6 nr closed by opening (statement V10 T-571/lintel-count-implied)

Worker 2, lane A, non-candidate, backlog-permitted, claim 2026-11-08T00:41Z, engine base 3c3aa2f8. Research only, unwired:
no engine module, method, rule / knowledge version, registry, frozen or candidate file changed; nothing released;
released default V2.9 + route G unchanged. Files: `t616_rules.py` (R-T616-1, every villa), `t616_alsenan.py` (the
table, merged inputs pinned by sha), `out/T616_RESIDUAL.json`, `tests/t616/` (15 tests). His deduction list was read
this run from Drive 'Alsenan chalet project' (blockwork workbook, Drive text reader); only counts by width per section
are used, the same figures T-571 / T-559 carry. Training villa; not an accuracy claim.

## 1. Physical element and question (ERS s.2.1)

One lintel over each masonry opening whose head lies below the member above it, bearing on built masonry both ends
(owner rule 2026-11-02: 1.20 / 1.50 / 2.50 / 3.00 / 4.00 m, 0.15 m bearing, shortest that fits). The row compares the
engine's AT_MOST lintel list (60 masonry openings, T-571) with his 54 deducted openings put through the same rule
("implied"; he has no lintel row). Question per opening: is it one list only, and is a lintel physically built there?

## 2. Groups (his sections) and the residual by opening

His list by section: GF ext 15, 1F ext 13, 2F ext 5, 15 cm GF 7 / 1F 8 / 2F 2, 20 cm 4 (= 54). His 20 cm section
repeats the same five wall lengths on GF / 1F / 2F (the stacked lift shaft, T-559): its 3 x 1.00 + 1.10 are the three
landing doors L-GF/1F/2F-01 and the lobby door D-GF-08 in the lift-front GF-W08. External openings pair first by the
census r3 keys (certain keys only; W02 / W03 keys point at his aluminium workbook widths 6.33 / 6.57, absent from his
deduction list: not used, listed). Then same width, then nearest width; every admissible pairing is enumerated
(identical widths and equal distances branch), ids reported FIRM (one list only in every pairing) or POSSIBLE.

| group | engine / his | nr | one-list openings |
|---|---|---|---|
| GF ext | 16 / 15 | +1 | D-GF-05 FIRM (his four 1.00 doors are keyed to D-GF-01 / -03 / -06 / -09; D-GF-05 key '?') |
| GF 15 cm | 9 / 7 | +2 | P-GF-01 FIRM (no 0.90 row of his); 1 of {D-GF-13, A-GF-01} (his single 1.00 row is one of them) |
| 1F 15 cm | 12 / 8 | +4 | P-1F-01 FIRM (1.30, nearest row 0.40 off); 3 of {A-1F-01, D-1F-02, D-1F-03, one 0.80 of D-1F-01 / 04 / 06 / 07 / 10}: his 4th 0.90 is 0.10 from a 0.80 and from a 1.00 (16 admissible sets) |
| 1F ext | 12 (+W17 carried, no lintel) / 13 | -1 | W17: his 3.15 x 3.00 deduction implies a 4.00 m piece; ours none |
| 2F ext, 2F 15, shaft | 5/5, 2/2, 4/4 | 0 | none |
| **total** | **60 / 54** | **+6** | 7 one-list openings of ours (3 FIRM + 4 of named sets), 1 of his (asserted closure) |

T-571 attribution corrected (FR-T616-3): L-GF-01 is NOT one-list (his 20 cm 1.00 x 3 are the stacked landing doors);
P-GF-01 is, and A-1F-01 / D-1F-02 / D-1F-03 / D-GF-13 are POSSIBLE, not identities (T-571's step 'ascending widths'
picked them). Beside: T-571's identity (his 1.10 = P-GF-01 on its 1.10 face, T-175) also closes +6 and gives the same
ENGINE_RIGHT bound 3 .. 5; then the shaft carries one of {D-GF-08, L-GF/1F/2F-01}. Not chosen: GF-W14 is not stacked.

## 3. Is a lintel physically built there (R-T616-1 (1), from drawn evidence in merged records)

| opening | host | evidence | decision |
|---|---|---|---|
| D-GF-13, D-1F-02, D-1F-03, D-1F-04, D-1F-07, D-1F-10 | 0.15 masonry | frame blocks, wall ends at block edges (T-581); ledger clear height: head 2.20 + lintel 0.20 + build-up 0.06 leaves 0.99 .. 1.58 m below the lowest soffit (still >= 0.79 at his 2.40) | REQUIRED |
| A-1F-01 | 0.15 1F-W16 | arch120 BEC; S8.6 LT-OP-1F-018: both bearings drawn masonry >= 400 mm, no beam band | REQUIRED |
| P-1F-01 | 0.15 | header lines; S8.6 LT-OP-1F-021: L2 under no member; T-198: lintel + masonry to the soffit | REQUIRED |
| P-GF-01 | 0.20 GF-W14 | S1 beam band over the whole width, head not printed (S8.6 OP-GF-020); one jamb a column | UNRESOLVED 0 .. 1 (head at the soffit: none) |
| D-GF-05, D-1F-01, D-1F-06 | masonry, host wall HELD | frame drawn; clear height above the head not established (ON_HELD_WALL) | UNRESOLVED 0 .. 1 |
| A-GF-01 | 0.15 GF-W26 | arch drawn (B-B, no dimension); no trace of the member over it | UNRESOLVED 0 .. 1 |
| W17 | curved band R 1.935 .. 2.135 (T-302) | arched head, outer arc 3.2895: a straight piece over the opening + 2 x 0.15 has an outer-face sagitta of 0.711 m in a 0.20 band filled by a 0.20 lintel | NO_STRAIGHT_PIECE: no stock lintel can exist; the spandrel support (CB12 0.75 soffit, DCR-3, or a curved cast element) stays HELD by name |

Own reads this run (P7757.dxf from Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip, decoded into the private
folder only; handles and figures only):
- W17: outer arc BD2 (layer W) R 2135.0 mm, sweep 88.278 deg, arc 3289.5 mm; inner arcs BCD / BCE / BD0 R 1935.0, same
  centre: band 0.200. Sagitta by hand: theta = (3.2895 + 0.30) / 2.135 = 1.6811 rad, 2.135 x (1 - cos 0.8406) =
  0.711 m (0.603 m over the opening alone). AGREES with T-302.
- P-1F-01: jambs C15 / C16 150.0 deep at 1300.0 apart; head lines C13 / C14 (layer 2) 1300.0 across both faces; faces
  C09 / C0B (a 0.500 nib) and C0A. AGREES with T-198 / T-601.
- D-GF-05: D120 insert 192 (rotation 90) in a 0.200 wall (faces x -149439.9 / -149639.9); A2 / A4 end and A3 / A5
  start exactly 1000.0 apart on both faces, at the block edges. AGREES with T-581: DRAWING-CONFIRMED 1.00.

## 4. Verdicts (proposals for the Checker)

- AT_MOST basis: every one-list candidate is a drawn opening in a masonry wall, both faces read: **ENGINE_RIGHT**; W17
  takes no straight piece: **ENGINE_RIGHT**. Residual on the AT_MOST basis **0 nr**.
- ESTABLISHED basis (his minus ours, -6): ENGINE_RIGHT -2 .. -4 nr (3 .. 5 of our one-list openings have a REQUIRED
  lintel, + W17's impossible piece), UNRESOLVED -2 .. -4 nr, each named with 0 .. 1 (P-GF-01 always; D-GF-05 always;
  A-GF-01 when he deducted D-GF-13; D-1F-01 / D-1F-06 when his 0.90 pairs elsewhere). Residual named, never 0.
- Caveat (R-T616-1 (4)): an opening missing from his DEDUCTION list is not proof he omitted it: at P-1F-01 the wall runs
  stop at its jambs (T-198), so he deducts nothing and also measures no masonry above the head. His implied 54 is a
  floor of his openings, labelled implied; "within 95 %" stays unclaimable for lintels (T-571).
- Lintels the engine should drop or add: **none** (its list is the right AT_MOST set).

## 5. Fix rows (statement / records only; no quantity moves)

- FR-T616-1: P-GF-01 lintel HELD cause 'head not established' -> 'HEAD_UNDER_BEAM: S1 band over the full width
  (S8.6 OP-GF-020), lintel 0 .. 1, column jamb gives no masonry bearing'. State unchanged.
- FR-T616-2: W17 NO_LINTEL cause 'not hosted by any masonry wall' (contested by T-302's elevation reading) ->
  'NO_STRAIGHT_PIECE: curved on plan, chord sagitta 0.711 m > 0 m of the band; head support HELD (DCR-3 / T-279)'.
- FR-T616-3: statement row T-571/lintel-count-implied: UNRESOLVED -6 -> ENGINE_RIGHT -2 .. -4 / UNRESOLVED -4 .. -2
  (named, coupled: sum -6); AT_MOST basis residual 0. T-571 s.3 ENGINE_ONLY list restated as section 2 above.

## 6. Rule R-T616-1 1.0.0 (every villa) and tests

(1) physical requirement from drawn evidence: RC / glazing host -> NOT_APPLICABLE (a counted piece refused); curved on
plan -> straight piece only if the outer-face sagitta of (opening + 2 bearings) <= wall t - piece width, else
NO_STRAIGHT_PIECE (a counted piece refused); door frame + clear-height margin >= 0 -> REQUIRED; full-width member and
no printed head -> 0 .. 1; masonry + bounded head + no member -> REQUIRED; else 0 .. 1. (2) residual by opening: one
storey and one group per id (else refused), keys -> same width -> nearest width, every pairing enumerated, the one-list
COUNT unique across pairings (else refused), ids FIRM / POSSIBLE, closure asserted, a non-zero group with no named
opening refused. (3) verdict as a bound over the admissible sets; a one-list opening that takes no lintel refused.
(4) deduction-list absence is not omission.
Tests (`tests/t616`, 15, PASS with tests/t571_lintel_count): villa Z by hand (sagitta 0.2177, closure 4 - 3 = +1 =
+2 - 1, sets {D1, P1} / {D2, P1}, bound 1 / 1), mirrored order, tie branching, gentle curve admitted, stock pieces;
adverse: lintel in an RC wall, straight piece in a curved wall, opening in two storeys, listed twice, one-list opening
without a lintel, 0 / mm / None widths, key to an absent width, unknown vocabulary; training villa rebuild byte-identical.

## 7. For the Checker (re-read 3 openings)

1. `python3 -I research/agents_t616/t616_alsenan.py --check`.
2. P-1F-01 (P7757.dxf faces C09 / C0A / C0B, jambs C15 / C16, head lines C13 / C14): 1.30, 0.15, no leaf.
3. D-GF-05 (D120 insert 192, GF-W17): wall ends at the block edges both faces, 1.000.
4. W17: arcs BCD / BCE / BD0 (outer) and BD1 / BD2 / BD6: R 2.135 / 1.935, outer arc 3.2895; re-do the sagitta.

## 8. Lesson row (proposed, ERS s.7)

| 2026-11-08 | T-571 named six 'engine-only' identities from a pairing that picks among equal widths, and a stacked-shaft door as one-list | ascending-width pairing chose identities the evidence does not separate; his section structure (repeated shaft rows) was not used | group by his own sections, pair keys -> same width -> nearest, enumerate every admissible pairing and report FIRM / POSSIBLE with a verdict bound; never a chosen identity; a straight piece in a curved wall is a geometry check, not a material question | tests/t616 | PROPOSED |

Missing: the member over D-GF-05 / A-GF-01 / D-1F-01 / D-1F-06 (clear height) and P-GF-01's head (designer, D-45 /
Q-HEAD-UNDER-BEAM); W17's spandrel support (DCR-3); his rows carry no id, so the 1 of 2 and 3 of 8 identities stay sets.
