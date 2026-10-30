# T-362: masonry accessories, the parts T-355 left open: white AAC courses, lintel bearings, unknown walls (development villa; every villa by R-T362-1 .. 4)

Worker 3 (lane A row, lane I had no claimable TODO), claim 2026-10-30 07:03 UTC, base working head e157c2d1. Research
only: a new unwired module, an application script, tests and generated maps; T-355's module and outputs are imported,
never edited; no engine, rule, knowledge or registry file changed; no block, plaster or concrete quantity moves;
released default stays V2.9 + route G; nothing here is released. No drawing was opened this run: every input is a
MERGED ledger of this repository (list in t362_alsenan.py). ERS read: s.2.1, s.2.2, s.2.4, s.3, s.4, s.7.

## 1. Physical elements (ERS s.2.1)

Same items as T-355 (bed-joint MESH STRIP m.l at every third course, SHARMAT pcs per third course at each wall-to-column
junction; optional, blocks section, never in the block m2). New here:

- A WHITE (AAC) wall is laid with thin-bed adhesive, not a 10 mm cement-sand joint (owner 2026-10-29: the 10 mm is for
  mortared blocks, NOT AAC thin-bed). Its course = the BLOCK HEIGHT + an adhesive bed of a few mm; course 1 sits on a
  levelling bed. The block height is a property of the supplier family actually laid.
- A LINTEL BEARING is the part of the lintel inside the masonry beyond each jamb. Where the lintel crosses a mesh
  level, the bearing is concrete, not block: the strip is interrupted over span + both bearings.

## 2. Evidence for the white course (owner method and drawing-derived method side by side)

| Source | What it gives | Status |
|---|---|---|
| Drawings (T-107 / T-117 / T-143 / T-176 census, merged) | white vs black by wall; NO block face or height printed | DRAWING-CONFIRMED type, size NOT PRINTED |
| Owner Q-60 answer (2026-10-20 10:45) | supplier pallet list: family A 62.5 x 25 face (10 .. 30 cm, every pallet volume closes on 0.625 x 0.25), family B 60 x 20 face (15 / 20 cm) | product data, two families, no choice |
| Owner's stored takeoff notes (quantity-takeoff-rules s.2.2) | thin-bed glue "about 2 mm"; first course on a levelled cement bed "at least 1 cm"; his 2025 invoice closes exactly on family A pallets (8.25 m3 = 4 x 2.0625; 30.000 m3 = 15 x 2.000) | the invoice is a PURCHASE RECORD of another job, not a project specification |
| Merged precedent T-143 / T-176 | white units reported for both faces, "neither chosen: no drawing names the face" | followed |

So the white course module is UNKNOWN between two families (0.250 or 0.200 m block). Following the T-176 precedent and
R-T362-1, both are computed, NEITHER IS CHOSEN, and the white quantity stays HELD (CONDITIONAL on the family). The 2025
invoice points to family A as the owner's usual purchase; that is for the owner / supplier to confirm (supplier
question proposed in section 6), never a reason to pick it here.

Level position (R-T362-2): level k = first bed + 3k block heights + (3k - 1) adhesive beds. Band: adhesive 1 .. 3 mm
(the owner's "about 2 mm"), first bed 10 mm (his "at least 1 cm") .. 20 mm (SENSITIVITY WINDOW ONLY, not a sourced
value: a level that moves inside it is held, never counted). A level counts only for the length that is the same at
both band corners.

## 3. Results (development villa)

**White walls, mesh strip (24 white walls; 17 with levels, 7 HELD: annex datum Q-54 B x 5, no block top x 2):**

| Floor | Family A certain m.l | A band-held | A other held | Family B certain m.l | B band-held | B other held |
|---|---|---|---|---|---|---|
| GF | 107.7786 | 0 | 40.5216 | 138.6265 | 0 | 55.2424 |
| 1F | 137.3732 | 2.7000 | 46.2510 | 185.9181 | 0 | 61.0021 |
| 2F | 65.6794 | 7.3000 | 36.4956 | 87.8742 | 0 | 48.4508 |
| **White** | **310.8312** (74 levels) | **10.0000** | **123.2683** | **412.4188** (95 levels) | **0** | **164.6952** |

Family B over family A: +101.5876 m.l (+32.7 %): a 0.20 m block puts a strip every 0.60 m, a 0.25 m block every 0.75 m.
Band-held (A only): 1F-W04 and 2F-W03 level 5 (3.774 .. 3.812 m) under the 3.80 m piece tops: exists at the low corner
only (2.70 + 7.30 m.l). Other holds by cause, A / B: block top not established 91.1441 / 118.4481, opening not tied to a
piece of known top 25.7491 / 37.7972, opening extent not established 6.375 / 7.65, lintel bearing not tied 0 / 0.80.

**White walls, sharmat:** 66 white junctions (T-355 held all 66): 26 measured per family, 40 HELD (annex datum, T-261
piece heights not tied to the column stations, block top beside the column). Family A **111 ties**, family B **142
ties**; band-held 0 (every tie count is the same at both corners).

**Lintel bearings (R-T362-3), per opening (LINTEL_BEARINGS_T362.csv):** jamb stations from the merged T-274 opening
scan on the same V2 run coordinates as the run pieces; masonry to the next column, opening or run end per side.

| Opening | Wall | Masonry left / right (m) | Bearing concrete at the lintel level (m) | Status |
|---|---|---|---|---|
| D-GF-13 | GF-W28 | 1.5034 / 1.2609 | 0.40 + 0.40 = 0.80 | CUT |
| D-1F-02 | 1F-W23 | 1.3950 / 1.0050 | 0.80 | CUT |
| D-1F-05 | 1F-W07 | 0.1850 / 0.3350 (column at 2.15, run end) | 0.185 + 0.335 = 0.52 | CUT |
| D-1F-06 | 1F-W16 | 0.5967 / 2.5233 | 0.80 | CUT |
| D-1F-07 | 1F-W19 | 0.1093 (run start) / 0.8907 | 0.5093 | CUT |
| D-2F-03 | 2F-W08 | 0.2493 (run start) / 1.9507 | 0.6493 | CUT |
| D-GF-10 | GF-W29 | no V2 run in T-175 | 0.55 (T-355, capped to the block) | HELD |
| D-1F-03 | 1F-W12 | no V2 run in T-175 | 0.80 | HELD |
| D-1F-04 | 1F-W23 | no V2 run in T-175 | 0.80 | HELD |
| D-GF-06 (white, B only) | GF-W05 | sub-run '#2' offset not recorded | 0.80 | HELD |

Three of the six tied openings have less than 0.40 of masonry on one side: T-355's 0.80 hold overstated their bearing
(the lintel cannot be longer than the masonry before the column or the run end). Per end the cut is
min(0.40 printed minimum, masonry), the same rule the merged lintel concrete line books (S8.6 PROJECT_BASIS_QTO), so
the two trades partition the run.

**Black walls restated under R-T362-3 (BLACK_RESTATED_T362.csv, 17 levels change):**

| | T-355 r2 | T-362 | Change |
|---|---|---|---|
| Net installed m.l | 543.4739 | **545.3060** | +1.8321 (+0.34 %) |
| HELD m.l | 164.4612 | **158.5505** | -5.9107 |
| Lintel cut m.l | 7.9000 | 11.9786 | +4.0786 (the six tied bearings) |
| Levels | 212 | 212 | 0 |

Every level conserves: gross = opening cut + lintel cut + held + net, the same as T-355 per level (asserted in code).
The +1.8321 net comes from: 1F-W19 +0.2907 and 2F-W08 +0.1507 (short bearings), and held openings whose maximal
footprint (width + per-end bearings) is now bounded by the masonry: lift door L-2F-01 (2F-W00, 6 levels x 0.10),
L-1F-01 (1F-W07, 5 levels x 0.10), D-1F-10 (1F-W17 level 2.40, +0.2907). Held lintel bearings now 2.15 m.l (from 6.95).
The T-355 residual at 1F-W07 level 3.60 (0.5948, lift door L-1F-01 extent) is unchanged and still HELD.

**The 7 walls outside the register runs (UNKNOWN_WALLS_T362.csv), all HELD by name, never 0:** GF-W30 (black 0.15,
1.525 m, held opening, no pieces), GF-W37 (white, 0.100 m, glazed line / held strip), GF-H01 and GF-H02 (block type
not established, 0.600 / 0.900 m: designer), 1F-W25 (white, 0.415 m, area 1.490 m2 established but no run pieces),
1F-W00/W01 BAY-ENDS (white, 0.166 m, 0.572 m2), GF P-GF-05 ABOVE-LINTEL (white, 1.200 m, 2.640 m2; its course datum is
the lintel top). No census types the two '-' walls; no owner answer does; they stay HELD.

**Villa, conditional on the white family (summary.json; HELD separately, unknown walls blank):**

| | if family A | if family B |
|---|---|---|
| Mesh strip net m.l (black 545.3060 + white certain) | 856.1372 | 957.7248 |
| Mesh strip HELD m.l | 291.8188 | 323.2457 |
| Sharmat ties (black 182 + white) | 293 | 324 |
| Junctions HELD | 60 | 60 |

**Against the freelancer:** no mesh-strip or sharmat line in his workbooks (T-317 / T-355 census): NOT COMPARED in %.
Verdict proposal RULE_DIFFERENCE (owner-added optional items, Q-77), as T-355.

## 4. Rules, code, tests

- research/agents_t362/t362_masonry_white.py: R-T362-1 thin-bed course (family with a source, adhesive band, a bed
  above 5 mm refused); R-T362-2 level band (certain = the smaller net over the band corners, rest HELD); R-T362-3
  lintel bearing per end (cut where both jamb stations are tied; untied openings keep T-355's hold; the same per-end
  pair bounds the footprint of a held opening); R-T362-4 one junction, one wall.
- research/agents_t362/t362_alsenan.py (`--write`, `--check` reproduces every output byte for byte).
- tests/t362_masonry_white/test_t362_masonry_white.py (13): NON-Alsenan hand fixture (5.00 m white wall, door 0.90 x
  2.30, lintel 0.20, jambs 1.00 / 2.50 from the columns): family A 14.90 m.l / 8 ties, family B 17.60 m.l / 10 ties
  (hand in the docstring); mirror and mm identical; adverse: 10 mm joint on AAC refused, AAC height without a source
  refused, mm read as m refused, a junction counted from two walls refused, families summed refused, a level at one
  band corner held (10.50 certain + 4.40 held), unknown top HELD never 0, untied opening keeps its 0.80 hold, a pier of
  0.15 gives a 0.55 bearing pair, a station outside the run refused, no printed minimum refused, per-level conservation.
- tests/t362_masonry_white/test_t362_alsenan_pins.py (8): outputs reproduce; black conservation vs T-355; the six cut
  and four held bearings; 66 white junctions (26 measured, held never 0); headlines; GF-W11 and 1F-W08 by hand.

## 5. For the Checker (re-measure)

1. White course evidence: Q-60 answer text (OWNER_QUESTIONS_ANSWERED.md, pallet list), the takeoff notes s.2.2, T-176
   "neither chosen"; confirm no drawing prints the AAC face (T-107 / T-143 census).
2. Two white walls by hand: GF-W11 (7.00 m, top 3.75: A 4 levels 0.762 .. 3.021 -> 28.00; B 6 levels 0.612 .. 3.627 ->
   42.00) and 1F-W08 (3.60 m, top 3.45: A 14.40, B 18.00).
3. Bearings: T274_OPENING_GAPS.csv + T274_RUN_PIECES.csv for D-1F-05 (WB-FL0016-FL0018: jambs 2.335 .. 3.235, column
   1.90 .. 2.15, run end 3.57 -> 0.185 / 0.335) and D-1F-07 (WB-FL0050-FL0051: 0.1093 .. 0.9093 on a 1.80 run).
4. Black restated: BLACK_RESTATED_T362.csv, 17 levels; per-level conservation against MESH_LEVELS_T355.csv.

## 6. Findings, open items, proposals

- F-T362-1 (supplier, for the Lead's CLARIFICATIONS_SUPPLIER list; not an owner question: a supplier data item, as
  Q-75 classed the black block size): which AAC face (62.5 x 25 or 60 x 20) and adhesive bed thickness will be laid on
  this project; it decides white mesh 310.8312 vs 412.4188 m.l and 111 vs 142 ties.
- F-T362-2: a bearing whose run ends before 0.40 (D-1F-07 start, D-2F-03 start, D-1F-05 end) may continue into the
  crossing wall; that wall's strip at the lintel level is not cut there (named, not quantified: the crossing wall's
  junction station is not tied).
- F-T362-3: the S8.6 lintel census cannot be bound to the register openings by floor + width + thickness (ambiguous
  for 9 of 10 openings; candidates shown in LINTEL_BEARINGS_T362.csv); a crosswalk needs the S8.6 band geometry.
- F-T362-4: owner Q-60 says the precast atab lintel is "only for white blocks"; the white-wall lintel depth here is the
  ST p.13 schedule's (as T-355). If white openings carry precast atab lintels instead, their depth (0.15 / 0.20 flipped)
  could move the lintel level on 20 cm walls: named, no quantity changes here.
- Still HELD: three black bearings without tied stations (2.15 m.l), D-GF-06 (white), the 7 unknown walls, the white
  family itself.

Proposed lessons row (ERS s.7): *Problem*: a lintel bearing was held as two printed minimums (0.80 m) on walls whose
masonry beside the jamb is shorter than 0.40. *Root cause*: the bearing was taken from the note alone, not from the
masonry that physically exists beside the jamb. *Rule*: per end min(printed minimum, masonry to the next column /
opening / run end), only with tied jamb stations; and a thin-bed course is block height + adhesive, never a mortar
joint, with the family named or HELD (R-T362-1 .. 3, every villa). *Test*: tests/t362_masonry_white. *Status*: PROPOSED.
