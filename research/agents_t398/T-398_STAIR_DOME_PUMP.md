# T-398 Stair, dome and pool-pump concrete: the T-385 r2 UNRESOLVED components SD-STAIR, SD-DOME, PL-PUMP traced piece by piece (research only)

Worker 1 (lane S), 2026-10-31 15:24 .. UTC, branch `agents/task-T-398`. Development villa, not an accuracy claim. No
engine file, candidate line, released cell, rule or method version is changed; nothing is released. ERS s.2.1 - 2.6,
s.3, s.4, s.7 applied.

## 0. Sources

- Candidate lines: the 22 STR.CONC.STAIR / DOME / POOL lines of the committed V3.0.21 concrete file
  (`research/agents_t332/CANDIDATE_V3021_CONCRETE_LINES.json`), asserted equal (ids, states, valued m3) to the V3.0.29
  binding of record (`research/agents_t387/BINDING_T387.csv`) by the builder; the Lead states V3.0.31 carries the
  V3.0.29 structural lines unchanged. SD-STAIR 12 lines 5.368881 m3, SD-DOME 5 lines 5.081362 m3, PL-PUMP 2 lines
  (both NOT_APPLICABLE) = the T-385 r2 figures.
- Pieces: the merged T-258 r2 ledger (`research/agents_t258/LEDGER_T258.csv`); every closable line = the sum of its
  pieces (asserted to 2e-6 m3).
- Own Drive copies this run (folder "Alsenan chalet project", decoded into `.work/private` only): 'ST7757 dxf.dxf'
  (9f9d1179), ST7757.pdf (p.7 read as an image), P7757_DXF_COMPRESSED.zip (architectural DXF) and the concrete + rebar
  workbook (stairs and pool sheets; quantities only, never rates).
- Freelancer values stay in `.work/private/t398/out/RECON_T398.csv`; this file and the tracked `summary_t398.json`
  carry engine figures, cause terms and verdicts (as the merged T-391 summary does).

```
python3 -I research/agents_t398/t398_alsenan.py --freelancer <private>/concrete_rebar.xlsx --out <private>/t398/out [--write]
```

## 1. Physical elements (ERS s.2.1) and the two methods side by side

| Element | Drawing-derived (engine, owner method) | His method (his rows, read on the row) |
|---|---|---|
| ST-01 flight (MS1-U, MS2-L, MS2-U) | 12 step triangles 1/2 r g w + waist T 16 x sec(pitch) on the drawn 3.300 m run (riser lines 25B .. 459 on p.4; 646 .. 632 and 62F .. 644 on p.5), lane 1.20; heads / foot inside B20 / B23 owned by the beams (R-CONC-OWN-1, T-189), Q-62 A wedges owned by the landing / slab | one plate: width x plan length x one thickness, 4 flights at one unit |
| ST-01 landings | MS1-LD 1.20 x 1.20, MS2-LD two plates 1.495 + 1.44 across both lanes (5E3 -> 5D4 2.50 m), printed T 16; turn slab MS1-T-SLAB and turn riser MS2-TR held (C-ST-3) | 3 landings, one lane, one thickness not printed on any sheet |
| D1 stair-hall flight | 4 riser lines 1C4 .. 1C7 (1.150), steps 0.100286 valued; waist held (RFI-S26) | no row |
| ST-03 E1 entrance | line held (waist not printed; steps 0.355017 named, not booked) | one plate row |
| ST-02 round stair | straight RS-S 3.000 + corner landing RS-LD + RS-A 1.200 valued 1.536225 (Q-50 A cond); curved RS-C (13 radial tread lines 2DF .. 2EA between S-OPENING arcs r 1.531 / 2.781), soffit, CA, 2CC held | one lump row, one length |
| Domes A / B | spherical cap shell above the springing, ST p.7 442 / 190 / 10: R_o 2.235289, V 2.540681 each (equivalent area 25.406807 m2, outer 26.685002); ring in the beam family (DOME-1F-W 0.7552 valued, DOME-1F-E held), drum held (RFI-A05) | 3 domes x one developed area x 0.10 |
| DOME-3 (tower) | held: no structural detail, ST p.6 flat +13.90 slab (Q-27 A, RFI-S28) | counted as the third equal dome |
| Pool pump room | drawn on NO sheet (own search: structural DXF texts / layers / p.7 pool detail, architectural DXF texts in English and Arabic: pump, plant, machine, equipment, filter); not a verified absence: a pool needs plant somewhere | walls + room floor rows |

Rules: `t398_rules.py` R-T398-1 .. 7 (one solid one owner; owner-method flight; plate comparison terms; landing terms;
cap shell; piece-level closure; not-drawn scope). Hand checks: the three flight nets reproduce the ledger to 1e-6
(MS1-U steps 0.360000 + waist 0.724812 - owned 0.087261; MS2-L 0.362880 + 0.726184 - 0.055619; MS2-U 0.362880 +
0.726184 - 0.087691); the cap formula reproduces the shell line 2.540681.

## 2. Result (signs engine - freelancer, m3; the freelancer side by his own printed units)

STAIR_DOME family: engine valued 10.450242, residual **-11.382558** = named (traced) **-0.328145** + HELD
**-5.788000** + unexplained **-5.266413** (UNRESOLVED ST-02 -3.974175 + untraced terms -1.292238). Closes to 1e-6.
Pump part: engine 0 (no line), residual **-3.480** all HELD (named item, not drawn).

| Component | Engine valued | Contribution | Traced terms | Untraced / held | Verdict proposal |
|---|---|---|---|---|---|
| SD-ST01-FLIGHTS (3 flights, 3 of his 4 units) | 3.032369 | -2.310031 | THICKNESS_BASIS -0.063460; OWNERSHIP -0.230571 (heads / foot in B20 / B23 0.140160 + Q-62 wedges 0.090411); WIDTH 0 | LENGTH -2.016000 UNTRACED: his flight length is 2.00 m longer than the drawn 3.300 run and equals no drawn length (run, sloped run 3.782, stair hall 4.30 / 4.75, run + half landing 4.45, run + arrival landing 5.25; no 5300 dimension in either DXF) | ENGINE_RIGHT (hand figures above) |
| SD-ST01-MS1L (1 unit) | 0 | held | - | held 0.983029 .. 1.184813 (CONFLICT C-ST-4 + winder treads) | HELD (RFI-A04, RFI-S24) |
| SD-ST01-LANDINGS (2 of 3 units) | 0.700000 | +0.028000 | THICKNESS_BASIS -0.134400 (T 16 printed, his thickness printed nowhere) | AREA +0.162400 UNTRACED (his landing area equals no drawn plate) | ENGINE_RIGHT |
| SD-ST01-TURNS (1 unit) | 0 | held | - | MS1-T-SLAB 0.2304 .. 0.2496 + MS2-TR unbounded | HELD (RFI-S24, S25) |
| SD-D1-STEPS (no row) | 0.100286 | +0.100286 | SCOPE: drawn element he omits | - | ENGINE_RIGHT |
| SD-D1-WAIST | 0 | 0 | - | unbounded | HELD (RFI-S26) |
| SD-ST03-E1 | 0 | held | - | unbounded (steps 0.355017 named) | HELD (RFI-S26) |
| SD-ST02 | 1.536225 | -3.974175 | - | his lump spans valued and held parts: not split | UNRESOLVED |
| SD-DOMES-AB (2 of 3 units) | 5.081362 | +0.561362 | THICKNESS_BASIS 0 (0.10 both) | AREA +0.561362 UNTRACED: his developed area is below the cap's own (equivalent 25.4068, outer 26.6850 m2); nearest formula 2 pi h^2 = 22.682 (a hemisphere on the rise), not drawn | ENGINE_RIGHT |
| SD-DOME-3 (1 unit) | 0 | held | - | unbounded | HELD (RFI-S28) |
| SD-NA (3 NA lines) | 0 | 0 | - | - | AGREE (scope) |
| PL-PUMP-ROOM | 0 | held -3.480 | - | named item, no line | HELD (not drawn; fact row below) |
| PL-POOL-NA (2 NA lines) | 0 | 0 | - | - | AGREE (scope) |

Findings (engineering):

- **His flight method is right in thickness, wrong in length.** The drawn flight's steps + waist on its own run is
  0.2750 m3 per plan m2 at 1.20 (MS2), his plate thickness differs by only -0.063 m3 over three flights; the gap is his
  flight length, 2.00 m beyond the drawn 3.30 m run on every flight (-2.016 m3 for three), which no drawn length or
  dimension reproduces. The nearest drawn candidate (run + arrival landing 5.25) would put the arrival landings, which
  the 1F / 2F slab panels GF-077 / 1F-062 already carry, into the stair: a DOUBLE if that were his basis. Not proven,
  so printed untraced, not named.
- **Ownership is counted once (acceptance c).** 15 pieces owned elsewhere (beam heads / foot 0.057261 + 0.025448 +
  0.057451, B20 / B23 billed full depth 0.990 / 1.11375 over the flights; arrival landings in slabs; D1 / E1 arrival
  wedges in the ground slab; columns 374 / 691; dome rings in the beam family; B3 'With Stair' in its beam line) each
  with one owner (R-T398-1 census, no DOUBLE); the dome shell starts at the springing, so ring and shell never meet.
- **ST-02 his length is not a length of this stair.** Whole developed length (straight 5.350 + curved centreline 3.286
  = 8.636 m; outer edge 9.385 m) is far below his one length: the 3.974 m3 residual stays UNRESOLVED; it closes only
  when RS-C is drawn (RFI-S27 / A03) and is never closed by re-attributing his lump.
- **Pump room: drawn nowhere** (R-T398-7). Engine HELD named item (proposal for lane I: a DG-5 held placeholder line
  'pool plant room, not drawn', blank, never 0, never valued from his rows).

## 3. F2 settled as a designer fact (T-391 F2; ERS 2.7 not met: no owner question)

Own read this run: the nine layer-2 tread lines 160 .. 168 (1.150 m) and the newel arcs 169 / 16A inside ground-slab
panel OWN-011 (3.020 x 2.772 = 8.3723 m2; edges 17D / 7CF / 7DC / 7E1) on the ground-beam sheet ST p.3 are the LOWER
nine of the thirteen radial tread lines 2DF .. 2EA of the ST-02 curved flight on p.4 (identical geometry at the sheet
offset 38.724 m: 2E2 -> 160 ... 2EA -> 168; newel 2EB / 2EC -> 169 / 16A); the upper four (2DF .. 2E1) are not drawn
on p.3. So F2 is the foot of the round stair's curved part RS-C, on the ground floor; RS-C is already HELD (RFI-S27:
soffit and thickness) and the space under it is RFI-A07.

Proposed row for rfi/B (DRAFT, nothing sent; the Lead places it; send with RFI-S27 and RFI-A07):

> **RFI-B-S35 Round stair ST-02: foot of the curved flight on the ground slab.** Drawing: ST p.3 ground-beam plan,
> panel between beams 17D / 7CF / 7DC / 7E1, nine tread lines and the newel of the ST-02 curved flight; ST p.4 the full
> flight (13 radial tread lines); no section of the curved flight. Missing: whether the 10 cm ground slab is continuous
> under the curved flight (flight built on the slab) or the flight bears on its own base / fill with the slab stopped
> at its outline. Affected: ground slab panel 8.3723 m2 x 0.10 = 0 .. 0.837230 m3 (HELD, T-391 F2); RS-C concrete
> (HELD, RFI-S27). Until answered both stay HELD, never 0.

> **RFI-B-A14 Pool plant (pump) room.** Drawing: ST p.7 DETAIL OF SWIMMING POOL; architectural GF plan; no pump,
> plant or equipment room is drawn or named on any sheet of either set. Missing: location, walls, floor and roof of
> the pool plant space (or confirmation that the plant is not in a concrete room). Affected: no engine line; a pool
> plant-room item HELD (no value); the freelancer's two rows are not adopted.

## 4. Proposed lessons-register row (ERS s.7)

| Date | Problem | Root cause | General rule (scope) | Regression test | Status |
|---|---|---|---|---|---|
| 2026-10-31 | The stair / dome family stood UNRESOLVED as two lumps (T-385 r2) | his rows are plates (width x length x one thickness) and lumps over valued and held pieces, compared total to total | reconcile per physical piece: a flight's plate difference splits into width / length / thickness basis / ownership terms that sum exactly; a term is traced only where his figure is a drawn figure; a row binds to pieces only by his own printed unit; a held piece carries no value; an element drawn on no sheet is a held named item with a designer fact row (scope: every villa, stairs, landings, domes, plant rooms; provenance T-398, R-T398-1 .. 7) | tests/t398_stair_dome_recon (landing in stair and slab refused, waist to the nosing plus steps refused, held as 0 refused, ring in the shell refused, row split by share refused, mm as m refused, rotation / mirror of riser lines) | PROPOSED |

## 5. Not done / uncertain

- His flight length (2.00 m beyond the run), landing area, dome area and ST-02 length are UNTRACED: nothing printed
  reproduces them; only he can say what they are.
- V3.0.30 / V3.0.31 not re-run here (binding asserted against V3.0.21 = V3.0.29).
- The two fact rows are drafts for the Lead; the held placeholder line for the pump room is a lane I proposal.
