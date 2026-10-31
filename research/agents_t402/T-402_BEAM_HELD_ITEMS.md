# T-402 Beam HELD items resolved one by one (lane S, research only)

Worker 1, 2026-10-31 19:24 .. UTC, branch `agents/task-T-402`. Development villa (Alsenan), not an accuracy claim. No
engine module, candidate line, released quantity, rule or method version changed; nothing released. ERS s.2.1 - 2.6,
s.3, s.4, s.7 applied.

## 0. Sources and runs

Own Drive copies this run (folder "Alsenan chalet project", decoded into `.work/private` only): 'ST7757 dxf.dxf'
(sha256 `9f9d1179`, = manifest), 'ST7757.pdf' (16 pages; p.10 simple-beam schedule, p.11 continuous-beam schedule),
the architectural DXF from 'P7757_DXF_COMPRESSED.zip', 'p7757_arch_sheet10.pdf' (building section) and the concrete +
rebar workbook (`ae608411`, quantities only). Candidate lines: the 27 STR.CONC.BEAM lines with status HELD in the V3.0.29
binding (`research/agents_t387/BINDING_T387.csv`: GF 10, 1F 12, 2F 5), read with their bounds from the committed V3.0.21
file (`research/agents_t332`, asserted equal to V3.0.29 by T-395); V3.0.30 .. V3.0.32 change no beam line (T-284
'every other line byte-identical'; the V3.0.32 chain was not re-run here).

```
python3 -I research/agents_t110/scripts/census.py <private>/ST7757_dxf.dxf <private>/t402/texts.json
python3 -I research/agents_t110/scripts/bands.py research/urban_engine_m4_correctness/st7757_route_g <private>/t402/bands.json
python3 -I research/agents_t402/t402_read.py <private>/ST7757_dxf.dxf <private>/t402/bands.json <private>/t402/texts.json <private>/t402/READ_T402.json
python3 -I research/agents_t402/t402_alsenan.py --read <private>/t402/READ_T402.json --write
```

Outputs (tracked): `HELD_LINES_T402.csv` (one row per held line: line id, mark, designer item, why held, sheets searched,
DXF edge handles, drawn width, face-to-face length, result, value / bound, plan area, missing fact, slab pairing,
candidate bound beside) and `summary_t402.json`. Rules `t402_rules.py` R-T402-1 .. 5; tests `tests/t402_beam_held` (20).

## 1. Result (acceptance a, b)

**No held line is settled by the drawings: 0 VALUE, 8 BOUNDED (two printed / drawn readings of one fact), 19 HELD.**
Every bound below is re-derived from my own edge reading (handles in the CSV), my own schedule read (DXF text = PDF
p.10 / p.11 image, row by row) and face-to-face lengths between the support outlines.

| Class (lines) | Floors | Why held (designer item) | Own result, m3 | Candidate bound, m3 | Missing fact |
|---|---|---|---|---|---|
| Width conflict (7): GF B29, CB2 x2, B21; 1F B6 span, CB10 x2 | GF 4, 1F 3 | schedule width vs drawn edges, no section cuts any of them (D-27, D-02) | **BOUNDED 5.145 .. 6.112** | 5.145 .. 6.111 | which width is the structure |
| Two marks (1): GF CB3 / 'B3 (With Stair)' | GF | CB3 under all spans + its p.11 row 0.20 x 0.75; B3 over span 2, row 0.20 x 0.40 (D-03) | **BOUNDED 0.212 .. 0.397** | 0.212 .. 0.398 | which member; never both (0.610) |
| Unlabelled span past a support (7) | GF 2, 1F 1, 2F 4 | no mark, no printed section (D-04) | **HELD**, bound 0.966 .. 2.898 (SCHEDULE_ENVELOPE 0.40 .. 1.20 m) | 1.041 .. 2.562 | the member's section |
| Slab-edge projection (11) | GF 3, 1F 7, 2F 1 | depth not printed; slab note 1 refers projections to the architectural details (D-05, D-26) | **HELD BLANK**, plan 6.947 m2, no m3 bound | 7 of 11 carry 1.975 .. 4.710 | projection depth / build-up; cast with the slab? |
| East dome ring (1) | 1F | no mark; dome detail depth 'AS PER ARCH' (D-28) | **HELD**, plan 1.799 m2 in its box | blank | ring section (B4 only where identified, Q-61 C(3)) |

Per line, the width conflicts (b x D x L face to face; T-229 oblique-end additions of the merged ledger kept):

| Line | Mark | Schedule b x D | Drawn b (handles) | L f2f | Drawn reading | Schedule reading | Slab pairing (t 0.16) |
|---|---|---|---|---|---|---|---|
| L-9e4895663f76d7f03ac9 | GF B29 | 0.25 x 0.75 | 0.200 (463 / 2CE) | 6.7403 + oblique | 1.013445 | 1.266806 | OVERLAP 0.053922 (0 if the extra 0.05 lies on the opening side: its south face is the opening edge) |
| L-2c7b0b1e1a439d9ffd1e | GF CB2 s1 | 0.20 x 0.50 | 0.250 (274 / 278) | 3.4692 | 0.433997 | 0.346920 | GAP 0.027865 |
| L-60f09eece6568b15f6ce | GF CB2 s2 | 0.20 x 0.50 | 0.250 (274 / 278) | 3.3508 | 0.419185 | 0.335080 | GAP 0.026914 |
| L-1fd49f3e7c5a7dd19d4d | GF B21 | 0.45 x 0.75 | 0.400 square to the inclined axis (433 / 434) | 7.4819 + oblique | 2.263370 | 2.546291 | OVERLAP 0.059855 |
| L-39ca5340879eafc35355 | 1F B6 span | 0.25 x 0.50 | 0.200 (5CC / 5CD); the other four B6 spans drawn 0.25 | 4.4147 + oblique | 0.442270 | 0.552837 | OVERLAP 0.035318 |
| L-50667f69855b6d588011 | 1F CB10 s1 | 0.25 x 0.50 | 0.300 (5E7 / 5E8); mirror CB13 printed 0.30 = drawn | 2.3010 | 0.345150 | 0.287625 | GAP 0.018408 |
| L-43e804ba4a4c07529fd5 | 1F CB10 s2 | 0.25 x 0.50 | 0.300 (5E7 / 5E8) | 3.6506 | 0.547590 | 0.456325 | GAP 0.029205 |

Own bounds agree with the candidate's within 0.0006 m3 per line (the candidate is right on these bounds; no change).
**New finding (R-T402-5)**: the slab lines are net of the DRAWN faces, so the schedule reading of a width is not a
beam-only change: B29 / B21 / B6 wider by 0.05 would overlap the slab by 0.149 m3 (the slab must give it up); CB2 / CB10
narrower by 0.05 leave a 0.102 m3 gap the slab must take. The total concrete moves only by db x L x (D - t) =
**+0.277 m3** net over the 7 lines (+0.495 on B29 / B21 / B6, -0.218 on CB2 / CB10), not by the beam bound's 0.967 m3
width. A beam bound must not be published without its slab pairing.

## 2. What the drawings were searched for (each line; acceptance a)

- **Schedule rows**: DXF text (S-TEXT.SCH) and the PDF images of p.10 / p.11 agree on every mark involved (B6 25 x 50,
  B21 45 x 75, B29 25 x 75, CB2 20 x 50 spans 4.0 / 4.0, CB3 20 x 75, CB10 25 x 50 spans 3.0 / 4.1, CB13 30 x 50): no
  revision split between the two documents. Bars and stirrup counts print no dimension and do not fix a width.
- **Section cuts** (S-SEC.LINE, 14 entities, own intersection with every held band): none cuts a width-conflict member,
  the D-03 span or the 2F / 1F unlabelled pieces. Three cut held bands:
  - A (55A) cuts the GF strip north of B20; section A-A draws B20 1.600 x 3.000 + an upstand 0.800 x 0.800 on its outer
    half = 0.40 x 0.75 + 0.20 x 0.20 at 1:25 (B20's printed 40 x 75), with no slab on either side: it does not show that
    nothing lies north of the beam, so the strip is not excluded (Q-61 C(5)). The plan line inside B20 (layer 2, 0.20 in
    from the outer face) is the upstand's inner face, so the 0.20 strip OUTSIDE B20 is not the upstand.
  - B (76E) cuts the 1F strip north of B23: section B-B the same (beam + upstand only).
  - D (181D) cuts the GF unlabelled piece past column 335 (B24 band continued to the east edge). D-D prints no dimension
    ('AS PER SCH.'); drawn 1.391 x 3.000, which is 0.35 x 0.75 at the 1:25 implied by the three other D cuts on CB1
    (printed 35 x 75). An INDICATION only (a scaled reading, never a quantity), and its width disagrees with the drawn
    0.4996 of the piece. The piece stays HELD.
- **Marks near each band** (beam-mark texts within 1.2 m): none of the 7 unlabelled pieces carries a mark of its own.
- **Edge continuity**: one pair of drawn edge lines often runs through several members of DIFFERENT marks (2F 399 / 39C,
  6.60 m, through B1 and B3; 2F 397 / 3AD through B15 and the unlabelled south piece; 2F 38D / 38E through B8 and its
  piece). Continuity therefore does not bind an unlabelled piece to a mark (R-T402-3).
- **Architectural sheets**: the building section (sheet 10) draws the roof slabs with 0.50 parapets and no projection
  or downstand at its cut edges, and prints no projection depth; its cut is not at the strips, so it settles nothing.
  The architectural DXF carries 276 texts and no projection / parapet detail.

## 3. Intersections, each counted once (acceptance c, T-387 method)

The candidate's slab lines are face areas net of every drawn band (T-395 s.4), the beam pieces end at column / carrier
faces (T-229, T-394 R-T394-1), and T-387 records each held member as a pair UNDETERMINED (no DOUBLE, never netted). The
held pieces lie inside their drawn bands, so their bounds overlap no slab or column in plan **except through a width
alternative** (section 1: OVERLAP 0.149 / GAP 0.102 m3 slab strip, named, not netted here). Columns: the support
outlines at each piece are listed by handle (READ, private); whether an alternative width would pass a column's side
face was NOT checked column by column (open, section 9).

## 4. Methods side by side (ERS s.2.2) and the freelancer (quantities only)

| Item | Owner manual method (Q-61 C, member by member) | Drawing-derived (this task) | Freelancer (his rows read this run) |
|---|---|---|---|
| Width conflicts | CONFLICT, both volumes, never the schedule because it is printed | BOUNDED pair + slab pairing (R-T402-5) | the schedule width on every row read: GF B29 0.25 x 0.75 x 6.75 = 1.2656 (= the schedule end, length 6.75 vs f2f 6.757); GF B21 0.45 x 0.75 x 7.80 = 2.6325 (schedule end 2.5463 + 0.0862 of length through the supports, the T-395 RULE_DIFFERENCE) |
| CB3 / B3 | HOLD, never duplicate | BOUNDED 0.212 .. 0.397 | one row, not bound to this span here |
| Unlabelled pieces | HOLD with location, length, candidate volume | HELD, envelope bound | the neighbour's section continued: 2F B15 0.2 x 1.2 x 6.80 = 1.632 runs over the B15 span 2.70 + the unlabelled 3.10 (= 0.744 at B15) + supports; 2F B8 0.2 x 0.75 x 5.40 = 0.810 over B8 3.47 + column 0.60 + the piece 1.13 (= 0.1695 at B8) + 0.20 |
| Projections / ring | HOLD and investigate | HELD BLANK, plan area | no projection row identified |

Verdict proposals: width conflicts and CB3 / B3 **UNRESOLVED** (designer; his figure is one end of each pair, not a
reason to pick it); unlabelled pieces **RULE_DIFFERENCE** in method (he borrows the neighbour's section, refused by
Q-61 C(4) / R-T402-3), quantity UNRESOLVED; projections and the ring **UNRESOLVED**, not comparable. Against T-395's
named HELD term (-7.376 m3 at his sections over 10 runs): 7.376 lies inside the summed bounds of those runs, so the
HELD term stays a held term, not a residual.

## 5. Proposals for a lane I row (no line edited here)

- **P1 (bound basis, downgrade-only, Checker record)**: the 7 projection lines that carry a bound today
  (GF BM-GF-058 x2; 1F BM-1F-033 x2, BAND0014, BAND0023, BM-1F-036: 1.975 .. 4.710 m3) take it from the beam-schedule
  depth envelope; a projection's depth is not a beam property (R-T402-4): restate them HELD BLANK with their plan area
  (6.947 m2 over the 11 projection lines), as the 4 no-band items already are. No figure changes (all blank today).
- **P2**: GF BM-GF-059 (unlabelled, past column 335) carries 0.375 .. 0.5625 (depth 0.50 .. 0.75) where the 6 other
  unlabelled pieces carry the set envelope 0.40 .. 1.20; no drawing basis is stated for the narrower pair (section D-D
  is a scaled indication). Restate on the envelope: 0.2998 .. 0.8995, D-D cited as INDICATION 0.75.
- **P3**: carry the slab pairing (OVERLAP / GAP, m3) beside each width-conflict bound in the export so a reader never
  adds the schedule reading to the drawn-net slab.
- No VALUE: no quantity of the candidate changes.

## 6. RFI facts for the still-held items (ERS s.6 facts for the RFI register; not owner questions)

- **D-27 / D-02 (7 spans)**: Issue: structural width of GF B29, CB2 (2 spans), B21, 1F B6 (vertical span) and CB10
  (2 spans). Evidence: schedule rows p.10 / p.11 (25, 20, 45, 25, 25) vs drawn edges 0.200 / 0.250 / 0.400 / 0.200 /
  0.300 (handles in the CSV); no section cuts them; PDF = DXF. Quantity impact: 5.145 .. 6.112 m3 beam, +0.277 m3 net
  concrete with the slab paired. Status: BOUNDED, blank in the BOQ.
- **D-03**: Issue: GF band span 2 printed CB3 and 'B3 (With Stair)'. Impact 0.212 (B3) .. 0.397 (CB3) m3, never both.
- **D-04 (7 pieces)**: Issue: section of the beam pieces past a support with no mark (GF 0.50 m and 1.50 m, 1F 0.80 m,
  2F 1.13 / 3.10 / 1.40 / 1.40 m). Evidence: drawn widths 0.20 (one 0.50); no mark; one cut (D) prints no dimension.
  Impact 0.966 .. 2.898 m3 on the set envelope. Status HELD.
- **D-05 / D-26 (11) and D-28 (1)**: Issue: depth / build-up of the slab-edge projections (plan 6.947 m2) and the section
  of the east dome ring (1.799 m2 in its box). Evidence: slab note 1 refers projections to the architectural details;
  sections A-A / B-B show beam + upstand only; dome detail depth 'AS PER ARCH'. Status HELD BLANK.

No owner question (ERS s.2.7 not met: every remaining item is a designer fact already in the register).

## 7. Rules and lessons row (proposed)

R-T402-1 .. 5 (`t402_rules.py`). Lessons row: | 2026-10-31 | 27 held beam lines (about 7.4 m3 of the beam residual)
were carried with bounds of mixed basis: width conflicts bounded beam-only although the slab is net of the drawn faces,
projections bounded by a beam-schedule depth envelope, one unlabelled piece on a narrower pair than the rest (T-402) |
a bound was built per line from the line's own inputs; the neighbouring line that shares the alternative's solid (the
slab strip) and the physical class of the element (projection vs beam) were not checked | a held line is VALUE only
when every input has its own uncontradicted drawing source; BOUNDED is the pair of readings only; an alternative width
is published with its slab pairing (OVERLAP / GAP |db| x L x t); an unlabelled piece never takes a neighbour's section
(edge continuity binds no mark); a projection carries plan area only (every villa; provenance T-402) |
tests/t402_beam_held (Villa Q: width pair, value when readings agree, two marks, envelope, projection, slab pairing
both ways; centre-line span, borrowed section, schedule row on an unlabelled piece, scaled section as value, held as 0,
missing length refused; reader under rotation / mirror, 0.6 deg off-parallel refused) | PROPOSED |

## 8. Checker re-measure list

- B29 edges 463 / 2CE (0.200) and its p.10 row 25 x 75; B21 433 / 434 (0.400 square to the axis); CB10 5E7 / 5E8 (0.300).
- Section D-D outline 1.391 x 3.000 against CB1's printed 35 x 75 (the 1:25 inference) and the cut 181D on the 0.4996
  piece past column 335.
- The slab pairing: slab line of the panel beside B21 / B29 net of the drawn faces (T-395 s.4).

## 9. Not done / uncertain

- V3.0.32 not re-run; the 27 lines are bound through the committed V3.0.21 file proven equal to V3.0.29.
- The architectural detail sheets other than sheet 10 were not read for a projection detail.
- 1F strip outside CB12: plan area 1.544 m2 from two straight faces + a 0.05 step; the rounded corners are not integrated.
- Column outlines at the conflicts were listed, not re-measured one by one against the alternative widths.
