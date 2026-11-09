# T-644: B9-02 lintels as precast pieces by the owner lintel rule, 60 / 60 openings classed (R-T644-1 1.0.0)

Worker 2, lane A, claim 2026-11-08T20:41Z, engine base 52230429 (candidate ARCH_TAKEOFF_V3.0.58). Research only, unwired:
no engine module, method, rule / knowledge version, registry, frozen, candidate or statement file changed; nothing
released; V2.9 + route G untouched. Files: `t644_extract.py` (jamb reader: the merged T-527 LINTEL_BEARING_V3 run with the
T-516 case table widened in memory to the 60 openings; the 16 T-527 openings are a byte-for-byte control),
`t644_lintel_pieces.py` (rule R-T644-1 + training-villa builder), `out/JAMB_EVIDENCE_T644.csv` (numbers only: lengths
from a jamb, wall / gap ids), `out/T644_LINTEL_PIECES.json`, `tests/t644/` (22 tests). Drawing read this run: Drive
'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip -> P7757.dxf (sha ab54dd55), decoded by the wrapper into the private
folder; the masonry capture rebuilt there (research/agents_t125). Development villa; not an accuracy claim.

## 1. Physical element and question (ERS s.2.1)

One precast lintel over one masonry opening, resting on BUILT masonry at both ends. Owner rule 2026-11-02: stock 1.20 /
1.50 / 2.50 / 3.00 / 4.00 m, >= 0.15 m bearing each side, shortest stock >= opening + 0.30, one per opening, in pieces;
> 4.00 m FLAGGED. The rule gives a LENGTH; whether that piece can physically sit depends on the masonry the drawing
builds beside each jamb (a column face, a cross wall end or a neighbouring opening stops it). T-571 counted pieces from
widths only (60 AT_MOST, 16 established) and T-516 checked bearings on the 16 REQUIRED only. This run measures both
ends of all 59 openings with a masonry capture (D-GF-14 has none) and applies the rule to the built masonry.

| | owner manual method | drawing-derived (this record) |
|---|---|---|
| length | shortest stock >= w + 0.30 | same (UPC-LINTEL-001, read only) |
| bearing | 0.15 m minimum each side | the piece's overhangs o_s + o_e = P - w, each 0.15 <= o <= a (a = built masonry beside the jamb, V3 reader); a shared pier carries both neighbours' overhangs |
| existence | one per opening | T-453 r2 ledger decision (head / host), T-616 drawn-evidence REQUIRED (A-1F-01, P-1F-01), register holds |

## 2. Result: pieces by stock length (nr; lm beside, never mixed)

| stock | ESTABLISHED GF / 1F / 2F | nr | AT_MOST (if every HELD one is built) GF / 1F / 2F | nr |
|---|---|---|---|---|
| 1.20 | 1 / 3 / 1 | 5 | 5 / 10 / 3 | 18 |
| 1.50 | 1 / 3 / 1 | 5 | 5 / 3 / 1 | 9 |
| 2.50 | 0 / 2 / 0 | 2 | 5 / 4 / 0 | 9 |
| 3.00 | 0 / 1 / 0 | 1 | 0 / 1 / 0 | 1 |
| 4.00 | 0 | 0 | 0 | 0 |
| total | | **13 pcs (21.5 lm)** | | **37 pcs (60.6 lm)** |

Classes (60 / 60, re-add asserted): PIECE 13, PIECE_IF_BUILT 24, FLAGGED_NO_BEARING 13, FLAGGED_SHARED_PIER 4,
FLAGGED_HEAD_ROOM 2, HELD_ENDS 1, HELD_REGISTER 3; FLAGGED_OVER_4M 0, HELD_WIDTH 0. Outside the 60: W17 NO_STOCK_PIECE
(register CURVED-BAND OPENING HEAD); W02, W03, SX-01, SX-03, U-01, D-GF-15, P-GF-05 not in a masonry wall (T-453 ledger).

- PIECE: 1.20 D-1F-07 / D-1F-08 / D-1F-10 / D-2F-03 / D-GF-10; 1.50 A-1F-01 / D-1F-02 / D-1F-03 / D-2F-01 / D-GF-13;
  2.50 P-1F-01 (1.30 + 0.30 = 1.60, no 2.00 stock) / W15; 3.00 W14.
- PIECE_IF_BUILT (piece fits; existence HELD with the ledger cause: head not established / on a held wall / in a held
  piece): 1.20 D-1F-01, D-1F-05, D-1F-09, D-2F-02, D-GF-02, D-GF-04, W05, W07, W19, W20, W21, W23, W28; 1.50 A-GF-01,
  D-GF-01, D-GF-05 (overhang 0.300 + 0.200 = 0.500 exactly: 0 mm spare), W01; 2.50 D-GF-07, W08, W09, W11, W12, W16, W24.
- FLAGGED_NO_BEARING (an end < 0.15 m: the owner minimum cannot be met; head owned by the structural line, register
  PAYABLE FORM): D-1F-04 0.079 column, D-1F-06 0.073 crossing wall, D-GF-06 0.140 column, D-GF-08 0.100 column, D-GF-09
  0.147 column, P-GF-01 0.000 column, W06 / W22 / W29 0.000 column, W10 / W25 / W27 0.100 column, W18 0.000 column.
- FLAGGED_SHARED_PIER: D-GF-11 / D-GF-12 (pier 0.238 < 0.15 + 0.15); W04 / D-GF-03 (pier 0.150 < 0.30).
- FLAGGED_HEAD_ROOM: W13, W26 (ledger: the head leaves no room for a 0.20 piece under some soffits; piers fit).
- HELD_ENDS: D-GF-14 (no V2 band, T-125 MISSING GF-W30): piece 1.20 beside, never counted.
- HELD_REGISTER: L-GF / 1F / 2F-01 (register LIFT LANDING DOOR LINTEL): piece 1.50 beside (ends 0.400 / 0.400 fit).

D-GF-09 (width UNRESOLVED 0.90 .. 1.00, R-T581-1): FLAGGED at both widths (END 0.1469 m to a column; at 1.00 the pier
would be shorter still), so the conflict no longer changes the precast count: no stock piece either way.

## 3. Evidence and checks

- Control: the 16 T-527 openings reproduce its committed rows field by field (asserted in the extractor and in
  test_jamb_rerun_equals_committed_evidence; the T-527 DXF re-run test, which this run's private drawing un-skips, also
  passes). The 44 new openings use the same reader unchanged.
- Second method (scratch, not committed): column outlines and neighbouring gaps projected on the band axis, no masonry
  union: D-GF-03 0.150 / 0.850, W04 1.300 / 0.150, D-GF-08 END 0.100, W06 END 0.000, D-GF-09 1.4531 / 0.1469, W25 END
  0.100, P-1F-01 START 0.450, D-GF-05 END 0.200: AGREE to 0.1 mm with the V3 reader.
- Width basis: the measured gap gives the same piece as the census width on all 58 measured openings with a census width
  (W11 / W12 1.9549, W14 2.4498, W15 / W16 / W24 1.5523 / 1.5524, D-GF-10 0.797).
- Against T-516 (precast beside, 16 REQUIRED): AGREE on D-1F-04 / D-GF-06 / W18 NO; T-516 'D-GF-11 FITS' did not charge
  the shared 0.238 m pier (D-GF-12 was HELD there): with both doors drawn, both FLAGGED.

## 4. The m3 lines (60 STR.CONC.LINTEL, all HELD; 54 blank + 6 bounded 0.502 .. OPEN)

Per opening in `out/T644_LINTEL_PIECES.json` (m3_lines): for the 37 PIECE / PIECE_IF_BUILT openings the proposed cause
is 'precast piece governs the payable form (owner lintel rule 2026-11-02, register PRECAST LINTEL PAYABLE FORM)'; for the
23 others the cause is the FLAGGED / HELD class and its reason. Never 0, never re-added with the pcs. Proposed wiring for
Worker 3: a B9-02 pcs line per stock length (ESTABLISHED released only after the Checker; AT_MOST beside).

**F-T644-1 (system, for the Lead; no owner question): the 20:15 register ruling PRECAST LINTEL PAYABLE FORM says the owner
precast piece is the payable form on every opening. The earlier register ruling RC LINTEL (2026-11-03), the
Checker-ENDORSED R-T519-1 and T-571 ('governing precast NOT_APPLICABLE') hold that on this villa the printed ST7757 p.13
LINTEL SCHEDULE (cast-in-situ RC, B = block wall width, MIN 40 cm) governs every block-wall lintel, and MISSION
'Lintels' says black-block lintels are precast or cast-in-situ 'as the drawings require'. Both rulings cannot stand. This
record delivers the piece table the 20:15 ruling asks for and labels it so; it does not decide the system. The owner's own
words (drawings first) settle it without a question; the Lead should restate one ruling.**

F-T644-2: 19 openings take no stock piece on the drawn masonry (13 no bearing, 4 shared piers, 2 head room). Whatever
system governs, their heads need a designed element (RC lintel with a designed column connection, a combined lintel over
two openings, or the beam above): designer items, named; they are not a lower quantity.

F-T644-3: the task row's fixture expected 3.80 m -> 4.00; by the owner rule 3.80 + 0.30 = 4.10 > 4.00 -> FLAGGED (a 4.00
piece would bear 0.10 m). The fixture follows the rule.

## 5. Freelancer (appendix only; he has no lintel row: his 54 deducted openings through the same rule, T-571, implied)

His implied 54 pcs (1.20 x27, 1.50 x17, 2.50 x8, 3.00 x1, 4.00 x1; 84.9 lm) vs ours AT_MOST 37 (60.6 lm), ESTABLISHED 13
(21.5 lm). Closure in nr (ours AT_MOST minus his): -17 = +6 one-list openings (T-616: AT_MOST basis ENGINE_RIGHT) - 19
FLAGGED (no stock piece fits the drawn masonry) - 4 HELD (D-GF-14 ends, 3 lift doors). Verdict proposals: the 19
FLAGGED: ENGINE_RIGHT on the precast rule (drawn masonry, measured, both faces of the band); the 4 HELD: UNRESOLVED;
'within 95 %' is not claimable for lintels (no freelancer lintel figure).

## 6. Tests (`tests/t644`, 22; with t571 / t616 / t516 / t519 / t527 / t544 / t581: all pass)

Villa Y by hand (0.90 / 1.20 / 2.70 / 3.80 / 4.20 / 3.60 -> 1.20 / 1.50 / 3.00 / FLAGGED / FLAGGED / 4.00); exact
overhang fits and 1 mm less is SHORT; shared pier 0.30 fits / 0.29 flags both; a short outer end raises the pier share;
a neighbour without a stock piece leaves the pier whole; mirror (START / END swapped) and reorder invariance; width bound
FLAGGED at both ends -> FLAGGED, else HELD_WIDTH; head-room and register holds carry no piece. Adverse: bearing omitted
-> HELD_ENDS and a piece for it refused; > 4.00 m given a piece refused; wrong piece, lm, 2 pcs refused; mm / cm / 0 /
negative / NaN / bool widths refused; duplicate id, unknown existence, one-sided or doubly-measured pier, end in mm
refused; a piece on a FLAGGED record refused by the tables; stale ledger refused. Training villa rebuild byte-identical
(class counts, tables, lm, gap check, the 60 lines all HELD). Jamb re-run == committed CSV when the private DXF exists.

## 7. For the Checker (re-measure 5 openings on P7757.dxf)

D-GF-11 / D-GF-12 (GF WB-FL0048-FL0049, pier 0.238); W04 / D-GF-03 (GF WB-FL0017-FL0018, pier 0.150); W25 (1F
WB-FL0030-FL0031, END 0.100 to a column); P-1F-01 (1F WB-FL0022-FL0023, 1.30, ends 0.450 / 2.266 -> 2.50); D-GF-05 (GF
WB-FL0083-FL0084, 0.300 + 0.200 = 0.500 exactly for the 1.50 piece). Run: `python3 -I research/agents_t644/t644_lintel_pieces.py`.

## 8. Lesson row (proposed, ERS s.7)

| 2026-11-08 | the precast count (T-571) took one stock piece per masonry opening from its width alone | the rule's length was treated as buildable; the masonry beside the jambs (columns, cross walls, shared piers) was checked on 16 of 60 openings only, and a shared pier was not charged to both neighbours | measure both ends of every opening; a piece counts only if 0.15 m fits at both ends and a shared pier carries both neighbours' minima; otherwise FLAGGED by name | tests/t644 | PROPOSED |
