# T-540: sand load size and bulk density (research, unwired)

Worker 2, 2026-11-05. `t540_sand_load_density.py` + `out/SAND_LOAD_DENSITY_T540.json` + `tests/t540_sand_load_density/`
(26 tests). No engine, rule, knowledge, registry or candidate file changed; no candidate or released (V2.9 + route G)
line moves. Input sha256-pinned in the output (T-535 JSON). Rebuild:
`python3 -I research/agents_t540/t540_sand_load_density.py` (`--check`: byte-identical, 0 failures).

## 1. Physical element
Washed building sand as delivered: a loose, moist, uncompacted heap. Mass per m3 depends on moisture (adds mass; at
low moisture it also bulks the loose volume) and on compaction (rodded > loose). The owner rates (Q-45 B, Q-53 C,
Q-78 A) are 'm3 of loose sand per m3 of mortar' for purchasing (Q-45 request), so the m3 a density may multiply is
LOOSE_AS_BOUGHT. A density in any other state (loose-dry, compacted, oven-dry particle) is a different physical
quantity: never applied, and no unsourced bulking factor converts it.

## 2. Source census (resolution order of AGENT_BRIEF)
| source | load size | bulk density | note |
|---|---|---|---|
| owner register Q-45 / Q-53 / Q-78, AGENT_BRIEF | none | none | unit loose m3 |
| CLARIFICATIONS_SUPPLIER_2026-10-23 rows 2-3 | none | none | sand only HELD |
| skill quantity-takeoff-rules (supplier data 2025) | none | none | cement 1440 kg/m3, block delivery per trip only |
| Drive 01 / MPW general specification 1990 | none | none in readable part | text read ends in division 2 (soil compaction); file over download limit |
| Drive 01 / KSE 'bait al-omr' 2023 | none | none | |
| Drive 02 / 'supervisor's eye' | none | none | readable part |
| Drive 02 / 'finishes', 'mistakes' | unreadable | unreadable | scanned, over limit |
| Drive 04 / Saudi code summary 2021, SBC 1101 Table 3-D-1 | none | none for sand | concrete, RC, brick, sand-lime brick, wet clay only |
| Drive 04 / QCS 2014 | not searchable | not searchable | 86 MB |
| Drive 03 / IBC, IPC, ACI | none | none | no material weight table hit |
| engine V6:91, T-523, T-535 | HELD | HELD | agree |

Result: both data HELD by name (`SAND_LOAD_SIZE_NOT_SOURCED`, `SAND_BULK_DENSITY_NOT_SOURCED`). No typical value is used:
a book figure found later would be ESTIMATED with its page (REFERENCE_SOURCES: evidence, not an Urban rule).

## 3. Training villa restated (T-535 group, m3 unchanged)
| group / trade | loose m3 | status | t | loads |
|---|---|---|---|---|
| villa group SAND_LOOSE | >= 17.746996 .. 23.449040 | AT_LEAST | HELD (density) | HELD (load size; group also AT_LEAST) |
| tile bed | 14.401213 .. 19.860543 | COMPUTED | HELD | not a purchasing group |
| outdoor bed | 0.728142 .. 0.970856 | COMPUTED | HELD | not a purchasing group |
| stone / stair bed | >= 1.113294 | AT_LEAST | HELD | not a purchasing group |
| block mortar | >= 1.396388 | AT_LEAST | HELD | not a purchasing group |
| perimeter joint | >= 0.107959 | AT_LEAST | HELD | not a purchasing group |
| plaster coats | none known | HELD | HELD (never 0) | HELD |

Engine vs freelancer: no freelancer basis (he prints no sand). Effect on quantities: 0 (m3 restated; t and loads stay
HELD).

## 4. Rules (every villa, PROPOSED)
R-T540-1 tonnes = loose m3 x a sourced density in the same state (LOOSE_AS_BOUGHT); other states refused; range end
to end. R-T540-2 load used in its own unit; a tonne load needs R-T540-1 first. R-T540-3 one ceiling per complete
villa group; AT_LEAST -> t AT_LEAST, loads HELD; no m3 -> HELD never 0; a trade subtotal never gets its own ceiling.
R-T540-4 t and loads beside the m3.

## 5. Fixture FX-540 (synthetic, by hand)
10 m3; 1.50 .. 1.70 t/m3 -> 15 .. 17 t; 6 m3 load -> 2 loads (12 m3); 20 t load -> 1 load; 8 t load -> 2 .. 3 loads.
Adverse: no density -> HELD; dry / compacted / particle density refused; unsourced refused; tonne load without density
HELD; AT_LEAST group; no m3; trade subtotal.

## 6. What would close it
One supplier datum: the delivery load (m3 per load, or t per load with the supplier's loose density as delivered) and
the minimum order. Non-critical procurement (MISSION): no owner question raised (Q-79 lesson); it fits the supplier
clarification list (CLARIFICATIONS_SUPPLIER) when the Lead next sends it.

## 7. Lessons-register row (proposed)
| 2026-11-05 | a sand tonne / load conversion could silently mix a dry or compacted density with the owner's loose m3 | density state not recorded with the value | density accepted only with source + moisture / compaction state equal to the m3 state; loads in their own unit, one ceiling per complete villa group | tests/t540_sand_load_density (FX-540 normal + state mismatch, unsourced, tonne load without density, AT_LEAST, no m3) | proposed |
