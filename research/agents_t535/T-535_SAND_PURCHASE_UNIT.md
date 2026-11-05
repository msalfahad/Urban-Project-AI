# T-535: sand purchase unit for the merged mortar producers (research, unwired)

Worker 2, 2026-11-05. `t535_sand_procurement.py` + `out/SAND_PROCUREMENT_T535.json` + `tests/t535_sand_procurement/`
(18 tests). No engine, rule, knowledge, registry or candidate file changed; no candidate or released (V2.9 + route G)
line moves. Inputs sha256-recorded in the output (T-523 map, T-520 summary, FINISH V6 / V7). Rebuild:
`python3 -I research/agents_t535/t535_sand_procurement.py` (`--check`: byte-identical, 0 failures).

## 1. Physical element
The sand delivered to site for site-mixed cement : sand layers (block mortar, block perimeter joint, plaster coats,
tile / stone / outdoor beds, screeds), as sold. Kept apart: INSTALLED (mortar m3 x owner loose-sand rate), LOSS (own
account, named), PROCUREMENT (installed + sourced losses), TO-BUY (procurement in the supplier's pack, one ceiling per
villa), CONVERSION (m3 -> t only with a sourced bulk density).

## 2. Evidence (nothing borrowed)
| source | what it states for sand |
|---|---|
| Q-45 (owner request + answer B) | 'sand (m3)'; 1.1 m3 LOOSE sand per m3 of 1:4 mortar; 5 % mortar loss |
| Q-53 C | 0.9975 m3 loose per m3 of 1:3 ('about 1.00 m3 for preliminary purchasing') |
| Q-78 A | 1:4 block mortar, 1.1 m3 loose sand per m3 |
| MISSION 'Cement-based materials' | 'cement bags, sand m3' |
| CLARIFICATIONS_SUPPLIER_2026-10-23 | sand only listed as HELD; no load, bag, tonne, density |
| REFERENCE_SOURCES.md, Drive reference folders (read-only search) | no sand supply unit, load size or bulk density found |
| engine FINISH V6:91, T-523 GROUPS | 'SAND_PACK_NOT_ESTABLISHED', pack None (agree) |

## 3. The table (one key)
| key | unit | pack | conversion | source | status |
|---|---|---|---|---|---|
| SAND_LOOSE | m3 loose | HELD SAND_LOAD_SIZE_NOT_SOURCED | t: HELD SAND_BULK_DENSITY_NOT_SOURCED; bulking not applied (SAND_BULKING_NOT_SOURCED) | Q-45 / Q-53 / Q-78 / MISSION | unit OWNER-CONFIRMED; rates PROVISIONAL / CALCULATED PROVISIONAL |

Missing datum to leave HELD (non-critical procurement, MISSION: never blocks the BOQ; no owner question raised, per the
Q-79 lesson): the supplier's delivery load size or order increment (m3 per load) and, only if sand is bought by weight,
a sourced bulk density.

## 4. Merged keys restated (training villa, one villa group, R-T523-1 + R-T535-1..4)
| trade (producer) | installed m3 | procurement m3 | status | open |
|---|---|---|---|---|
| tile bed (T-500) | 13.715435 .. 18.914801 | 14.401213 .. 19.860543 | COMPUTED | 0 |
| outdoor bed (T-514) | 0.693469 .. 0.924625 | 0.728142 .. 0.970856 | COMPUTED | 0 |
| stone / stair bed 1:3 (V7) | 1.060280 | >= 1.113294 | HELD | 20 |
| block mortar (T-453) | >= 1.396388 | >= 1.396388 (loss HELD) | HELD | 11 |
| perimeter joint (T-520) | >= 0.107959 | >= 0.107959 (loss HELD) | HELD | 7 |
| plaster coats (T-489) | none known | none | HELD | 156 |
| **villa group** | **>= 16.973531 .. 22.404053** | **>= 17.746996 .. 23.449040** | **HELD** | 194 of 250 |

To-buy loads: HELD (pack unsourced) and also because the group is HELD. Sand stays fractional loose m3.

## 5. Finding F-T535-1 (R-T535-2) and the delta vs the T-523 print
The T-511 / T-523 stair members bind the Q-53 'preliminary purchasing' figure (1.00 m3 per m3 = 1.062939 m3) as
PROCUREMENT. Physically that figure is the theoretical rate 0.9975 rounded ('about'), not a loss: merged FINISH V7
(R-T528-1, ALLOWANCE_LABEL) keeps it as a separate layer and computes procurement = installed x (1 + Q-45 5 %) =
1.06028 x 1.05 = 1.113294 m3 (+0.050355). With the T-520 perimeter key (0.107959 m3, own key, absent from T-523), the
villa known part moves 17.588682 .. 23.290726 -> 17.746996 .. 23.449040 m3 (+0.158314 m3, +0.90 % .. +0.68 %).
Verdict proposal: ENGINE_WRONG (staging in the T-523 binding, not a quantity in the candidate); no freelancer basis
(the freelancer prints no sand).

## 6. Rules (every villa, PROPOSED)
R-T535-1 sand unit loose m3; loads only from a sourced pack, one ceiling per villa; tonnes only from a sourced density.
R-T535-2 rounded-rate allowance is a layer, never procurement. R-T535-3 two villas never share a group or ceiling.
R-T535-4 unsourced loss -> installed into AT_LEAST, procurement HELD; no installed -> open, never 0.

## 7. Lessons-register row (proposed)
| 2026-11-05 | the stair sand 'preliminary purchasing' figure (a rounded rate) was bound as procurement; sand had no stated purchase unit | a rate rounding read as a purchasing stage; unit never recorded with its source | sand procurement in loose m3 (owner unit), allowance beside, loads / tonnes only from a sourced pack / density, one ceiling per villa | tests/t535_sand_procurement (FX-535 normal + unsourced loss / pack / density, two villas, open member) | proposed |
