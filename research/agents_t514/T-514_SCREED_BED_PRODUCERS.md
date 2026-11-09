# T-514: cement / sand producers for the screed, threshold / lift and outdoor bed lines (research, unwired)

Worker 2, 2026-11-05. `t514_screed_bed_producers.py` (rules R-T514-1..6) + `t514_inputs.py` (project declarations) +
`out/SCREED_BED_PRODUCERS_T514.{json,csv}` + `tests/t514_screed_bed_producers/` (21 tests). No engine, rule,
knowledge, registry, hub, master or candidate file changed; no candidate or released (V2.9 + route G) line moves.
Candidate of record ARCH_TAKEOFF_V3.0.58 (c9570e6c) = V3.0.57 (25a8b406) + 5 FIN.WP.ROOF / ROOF_UPTURN lines (NOT_A_KEY,
R-T507-1 (e)): every host here is the V3.0.57 line, cross-checked against the T-507 line index. Rebuild:
`python3 -I research/agents_t514/t514_screed_bed_producers.py` (byte-identical, tested); `--check` exits 1 on a failure.

## 1. Physical element and evidence (ERS s.2.1, hierarchy levels 1-3)

| host (lines) | layer actually built | thickness printed | mix source found |
|---|---|---|---|
| footing protection screed 5.4925 m3 (+ 1B1B HELD) | 'screed' over the footing membrane: product not stated | 5 cm (ST p.13) | none |
| lift-pit base screed 1.035 m3 | 'screed' under the raft, over the membrane | 5 cm (ST p.14; 4.60 x 4.50 = 20.70 m2) | none |
| pool protection screed 1.524503 m3 | 'screed' between shell and membrane, base + outer walls | 5 cm (ST DXF TEXT 1874 '5cm SECREED.') | none |
| roof falls screeds (4, HELD) | falls layer: cement : sand screed or lightweight fill not stated | none (Q-41 / Q-45 falls) | none |
| marble door thresholds (14) + lift thresholds (3) | stone piece in the doorway strip, bedded flush with the floors | none (T-475: 'the bed under the threshold' unsupported) | none |
| lift surrounds (3, HELD area) | marble jambs + head on the wall face: cladding, fixing not printed | none | none |
| north side walk 21.0142 m2 (released) | porcelain on a cement : sand floor bed | none: owner band | UPC-TILE-BED-001 (Q-45 B) |
| interlock court 119.5416 m2 | pavers on a SAND bed (no cement) | none | none (T-495 DECLARED_OUT) |
| porch 10.6785 / pool deck 6.548912 m2 (HELD) | finish not decided (OD-1) | - | - |

Level 1: own scan of every TEXT / MTEXT / ATTRIB entity (model space + blocks) of 'ST7757 dxf.dxf' and
'P7757_DXF_COMPRESSED.zip' (Drive "Alsenan chalet project"): the only layer note is '5cm SECREED.' (x2); no mix, bed,
threshold or marble-fixing note; single sheets 03 / 04 have no text layer (raster). Levels 2-3: Q-45 B / UPC-TILE-BED-001
(beds under floor tiles, regular 0.03-0.04 / wet 0.04-0.06 m, 1:4, 8.0 bags + 1.1 m3), Q-53 C / UP-STAIR-017 (stair
marble 1:3), Q-78 A (block laying 1:4), Q-41 (roofs / balconies carry a 'screed', bathrooms 'cement': the owner keeps
screed and cement mortar apart, no mix, no thickness). No record names a screed, a threshold bed or a cladding fixing.

## 2. Rules R-T514-1..6 (every villa; full text in the module docstring)

1 layer before arithmetic (only a site-mixed cement : sand layer is computed); 2 mix only from a record whose scope names
the physical layer kind (unsourced ratio or out-of-scope record refused); 3 one conversion per ratio (below); 4 a screed
m3 must reproduce m2 partner x printed thickness (or its merged source record), m / cm / mm normalised; 5 the new rows
join the T-511 census, one producer per physical key; 6 HELD names every missing input (LAYER_TYPE, THICKNESS, MIX, AREA,
FINISH), sensitivity beside is NOT A QUANTITY, subtotals by R-T499-1.

**F-T511-4 rule note (R-T514-3).** For 1:4 the owner's per-m3 figure governs: 8.0 bags + 1.1 m3 (Q-45 B, re-given by
the owner for Q-78 A on 2026-11-02, recorded in UPC-TILE-BED-001). The Q-53 C derivation (dry factor 1.33, 1,440 kg/m3)
is the owner's figure only for 1:3 (UP-STAIR-017 = his answer to that question) and a method for a ratio he gave no
figure for. T-489 V2's 1:4 = 7.6608 bags / 1.064 m3 stays BESIDE: wiring it on a 1:4 coat while 8.0 / 1.1 stands would
put two bases on one cement key (-4.24 % cement, -3.27 % sand). Existing versions untouched; a coat wiring row must use
the owner 1:4 figure.

## 3. Result on V3.0.58 (0 failures; 32 hosts)

| group | state | cement bags installed | sand m3 installed | procurement |
|---|---|---|---|---|
| north side walk bed (1) | PRODUCED, ASSUMED - OWNER-APPROVED (UPC-TILE-BED-001 + OWNER_RULE_OUTDOOR_FLOORS: sides porcelain, part of the house) | 5.043408 .. 6.724544 | 0.693469 .. 0.924625 | +5 % (Q-45 B): 5.295578 .. 7.060771 bags |
| released screeds 8.052003 m3 (3) + 1B1B (1) | HELD: LAYER_TYPE + MIX (1B1B also AREA) | HELD | HELD | HELD |
| roof falls screeds (4) | HELD: LAYER_TYPE + THICKNESS + MIX + AREA | HELD | HELD | HELD |
| thresholds + lift thresholds (17) | HELD: MIX + THICKNESS | HELD | HELD | HELD |
| lift surrounds (3) | HELD: LAYER_TYPE + MIX + AREA | HELD | HELD | HELD |
| interlock (1) | HELD: sand-only bed, no owner record (no cement ratio ever) | - | HELD | HELD |
| porch / pool deck (2) | HELD: FINISH (T-495 options beside) | HELD | HELD | HELD |

Project (T-511 census + this table): cement HELD, known part >= **125.126280 .. 164.620992** bags installed (was
120.082872 .. 157.896448, +5.043408 .. 6.724544); sand >= 16.865572 .. 22.296094 m3; procurement known part >= 120.661015
.. 162.130462 bags. Host states 57 -> 58 PRODUCED, 149 -> 148 HELD, 74 NOT_APPLICABLE unchanged. Sensitivity only, NOT A
QUANTITY: the 8.052003 m3 of screed would take 64.416 bags at 1:4 or 77.106 at 1:3; the 17 thresholds 0.797 .. 1.272
bags.

Hand checks: 21.0142 x 0.03 = 0.630426 m3 x 8 = 5.043408 bags, x 1.1 = 0.693469 m3; 21.0142 x 0.04 = 0.840568 x 8 =
6.724544; 109.85 x 0.05 = 5.4925 and 20.70 x 0.05 = 1.035 (reproduced in code); 120.082872 + 5.043408 = 125.126280.
Fixture K514 (hand, not the training villa): 40 m2 x 50 mm screed with a printed 1:4 note -> 2.000 m3, 16.000 bags,
2.200 m3 sand, waste HELD; without the note HELD (LAYER_TYPE, MIX), sensitivity 16.000 / 19.152 bags; threshold 0.18 m2
HELD (MIX, THICKNESS); walk 10 m2 -> 2.40 .. 3.20 bags, procurement 2.52 .. 3.36.

## 4. Findings

- **F-T514-1 display rounding (immaterial).** The T-511 chain applies T-310's ADD row from its 4-decimal display column:
  pool screed 1.5245 vs the candidate line 1.524503 m3 (-0.000003). T-511's '8.0520 m3' is 8.052003. This table reads
  the line index. Rule: figures come from the line index, never a display column.
- **F-T514-2 missing host.** The exposed pool-court slab (B8-06, V3.0.58) is a roof by function; Q-41 puts a screed on
  roofs, but the candidate has no build-up line (T-507: WAITING T507_BUILDUP). Named, not counted.
- Screed mix (64 .. 77 bags at stake) is the largest unsourced cement figure after plaster: no owner record, not asked
  (non-critical procurement parameter; the Lead decides whether it goes in an owner package with the plaster mix).

## 5. Freelancer and verdict proposal

The freelancer workbooks carry no cement / sand rows (T-367, T-420, T-500, T-511): materials are engine-only. Verdict
proposal: RULE_DIFFERENCE (scope); the walk bed is ENGINE_RIGHT by the owner rule (hand check above).

## 6. Lessons row (proposed, ERS s.7)

| Date | Problem | Root cause | General rule (scope) | Regression test | Status |
|---|---|---|---|---|---|
| 2026-11-05 | 32 screed / threshold / outdoor hosts had no producer; one 1:4 cement key had two conversion bases | the bed tables keyed on trade, not on the physical layer and the scope of the owner record; conversions were per table | R-T514-1..6 (every villa): layer first, mix only from a record whose scope names the layer, one figure per ratio (owner figure governs), reproduce before deriving, one producer per key, HELD by name | tests/t514_screed_bed_producers (normal K514 by hand; adverse: unsourced mix, out-of-scope record, second conversion, non-reproducing m3, unknown unit, held area, sand-only bed, two producers, order) | proposed |
