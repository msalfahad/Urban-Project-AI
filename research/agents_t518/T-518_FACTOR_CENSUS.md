# T-518 Materials waste / procurement factor provenance census

Lane I, non-candidate, research only. No producer, candidate line, rule or knowledge file changed; released quantities
changed: 0. Code: `t518_factor_census.py`; output: `out/FACTOR_CENSUS_T518.json` / `.csv`; tests:
`tests/t518_factor_census` (12).

## Physical element and question

Procurement = installed (theoretical) quantity + named losses (cutting, breakage, mixing, spillage), each its own
account, + pack rounding once per purchasing group. Installed never carries a loss. For every merged producer key:
which factor, where applied, which source.

## Census

92 producer keys (table x layer / material x stage; 3,377 rows behind them) from T-511, T-514, T-496, T-500, T-455,
T-453 and T-505 outputs, bound to 13 factor records: read 92, unread 0. Producers: FINISH_MATERIALS_TABLE V1 (V2..V5
inherit), STAIR_BED_V1, T-453, T-454, T-455, T-489, T-495, T-500, T-505, T-514.

| id | producer / keys | factor | placement | source | status |
|---|---|---|---|---|---|
| FX-01 | T-500 tile bed cement / sand | 5 % mortar waste | separate field | Q-45 B + owner correction 2026-10-20 12:15 | ASSUMED - OWNER-APPROVED |
| FX-02 | T-514 floor tile bed (outdoor porcelain) | 5 % | separate field | same | ASSUMED - OWNER-APPROVED |
| FX-03 | T-514 threshold stone bed / screeds | none | HELD | none (Q-41 thickness HELD) | NO SOURCE (held) |
| FX-04 | STAIR_BED_V1 1:3 | purchasing allowance x1.044277 cement, x1.002506 sand | separate layer | Q-53 C / UP-STAIR-017 | ASSUMED - OWNER-APPROVED |
| FX-05 | T-453 black mortar, AAC glue | none | HELD | UPC-BLACK-MORTAR-001 / UPC-AAC-GLUE-001: sourced only | NO SOURCE (held) |
| FX-06 | T-453 block units | none | HELD | UPC-BLACK-BLOCK-001 'never a hardcoded 5 %' | NO SOURCE (held) |
| FX-07 | T-453 lintel concrete | none | - | - | NO FACTOR |
| FX-08 | T-454 / T-489 plaster coats | none | HELD | UPC-CEMENT-LAYERS-METHOD-001 null | NO SOURCE (held) |
| FX-09 | T-455 / T-495 adhesive | none; ceil per product group | HELD | UPC-ADHESIVE-001 | NO SOURCE (held) |
| FX-10 | T-455 tiles / boxes | layout cutting + 1 spare box / product | layout, spare separate | UP-CER-010; owner B3 (board T-455 row) | OWNER-APPROVED |
| FX-11 | FINISH V1 (V2..V5) mortar / cement / sand | 5 % | INSIDE installed | Q-45 B | DEFECT D-T518-1 |
| FX-12 | T-495 outdoor bed options (T-496 binding) | 5 % | INSIDE, bound as INSTALLED | Q-45 B | DEFECT D-T518-2 |
| FX-13 | T-505 disposal losses | loss_reuse / loss_import | HELD | owner 2026-11-02 18:00 (3) | NO SOURCE (held) |

Unsourced factors applied anywhere: 0. Factors inside an installed quantity: 2, both named defects (below).

## Re-derivations (producer code + owner register)

- T-500: 616 checks, 0 fails: installed m3 = area x band, cement / sand = m3 x 8 / 1.1, waste = installed x 0.05,
  procurement = installed + waste (installed carries no waste).
- T-514: 12 checks, 0 fails (21.0142 m2 x 0.03 / 0.04 x 8 = 5.043408 / 6.724544 bags; + 5 % = 5.295578 / 7.060771).
- STAIR_BED_V1: 44 checks, 0 fails: procurement / installed = 10 / 9.576 (cement), 1.00 / 0.9975 (sand).
- FINISH V5 on 10 m2 dry floor: mortar 0.315 / 0.420 m3 = 0.300 / 0.400 x 1.05, no waste field (D-T518-1).
- T-496 T-495 bed bindings: 0.206291 / 0.275054 m3 = 6.548912 m2 x 0.03 / 0.04 x 1.05 at stage INSTALLED; installed
  share 0.196468 / 0.261956 m3 (overstated 0.009823 / 0.013098 m3); line 2: 0.320355 / 0.427140 (0.016018 / 0.021357).

## Findings

- F-T518-1 (resolves F-C-T514-1): the 5 % on the Q-45 tile beds is owner-approved: Q-45 answer B accepted the
  practice values including 'waste 5 %' (PROVISIONAL rate), and the owner's correction of 2026-10-20 12:15 withdrew the
  audit line X3 ('waste 5 % not owner-approved') and kept 'Q-45 values incl. waste 5 %'. T-500 / T-514 apply it in a
  separate field: correct. Status ASSUMED - OWNER-APPROVED, not 'PROVISIONAL from V1 practice'.
- R-T518-3 scope: the 5 % is not borrowed by black-block mortar (UPC-BLACK-MORTAR-001 2026-11-02: mortar waste
  'sourced value only'), blocks, glue, adhesive, plaster or screeds; every producer respects this.
- D-T518-1: FINISH_MATERIALS_TABLE V1 `finish_materials_table.py:213-215` folds the 5 % into mortar_m3 and so into
  cement / sand; V2 (`:47-49`), V3 (all kinds but WET_WALL), V4 (`:198`) and V5 inherit. Unwired; T-511 reads it as a
  PROCUREMENT reader (correct), so no candidate quantity is wrong. Fix: a new version with installed / waste /
  procurement fields (T-500 shape), never an edit of V1..V5.
- D-T518-2: T-496 `t496_binding_map.py:297-300` binds the T-495 bed mortar (5 % folded) at stage INSTALLED; T-511
  classes the same figures PROCUREMENT. HELD rows, never summed; fix in a T-496 successor (stage PROCUREMENT or /1.05).
- F-T518-2: stair 1:3 bed: FINISH V1 applies the Q-45 5 % (Q-45 named the marble stair bed); STAIR_BED_V1 holds
  waste (Q-53 C) and buys at the purchasing allowance. Alsenan 11 computed lines: installed 10.178704 bags / 1.060280
  m3 sand; the 5 % beside = 0.508935 bags / 0.053014 m3. Unresolved scope: stays HELD with the figure beside; the 5 %
  must not be stacked on the purchasing allowance without a ruling (Lead / Checker first; the owner only under s.2.7).
- F-T518-3: cement whole bags are printed at sub-group scopes (T-500 per item code and per table). Summing the
  item-code ceilings gives 105 / 146 bags against 105 / 145 at the T-500 table (fractional 104.736047 / 144.440301):
  +1 bag at the high end. The purchasing group of 50 kg cement is the villa (all trades), HELD today in T-511.
- O-T518-1: `material_result.packaging` sets spare_units 0 when the spare is NOT_SET (state recorded): a missing
  allowance is not a loss, labelled, acceptable.

## Proposed lessons-register row (standard s.7)

'A sourced factor in the wrong place is a defect like an unsourced one: the installed field must be reproducible as
area x thickness x per-m3; any 1.0x left in it is waste folded in.' Rule R-T518-1..3, test tests/t518_factor_census.

## Owner question

None: no factor is applied without a source, and every unsourced loss is HELD per the owner's own 'sourced value only'
rules; the open stair-bed scope is a reconciliation for the Lead / Checker (s.2.7 not met).
