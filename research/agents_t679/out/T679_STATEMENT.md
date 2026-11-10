# T-679 Concrete reconciliation statement (R-T679-1)

Candidate ARCH_TAKEOFF_V3.0.65: `research/agents_t671/out/LINE_INDEX_V3_0_65.json` sha256 e1887c34362b..., lines sha 38af7909; master `rules/coverage/BOQ_FAMILY_MASTER_1.66.0.json` census agrees on 14 families. development villa; not an accuracy claim; nothing released (the released default V2.9 + route G is unchanged); no quantity changed; the reference is never a quantity and agreement is never proof.

## Engine side: family subtotal -> trade total (m3; buckets never summed together)

| Family | Item | Lines | Released n / m3 | Held bounded n / low .. high | Held blank n (DESIGNER / OPEN BOUND / MEASURABLE NOW) | Excluded n | Engine range | Verified whole / component |
|---|---|---|---|---|---|---|---|---|
| B7-12 | Stair concrete | 12 | 6 / 5.368881 | 0 / 0 .. 0 | 5 (4 / 0 / 1) | 1 | 5.368881 .. OPEN | 0 / 11 (0) / 0 / 11 (0) |
| B9-02 | Lintels | 60 | 16 / 1.016 | 0 / 0 .. 0 | 44 (6 / 13 / 25) | 0 | 1.016 .. OPEN | 0 / 60 (0) / 0 / 60 (0) |
| B10-01 | Blinding | 8 | 1 / 12.734438 | 5 / 7.640374 .. 13.466198 | 2 (2 / 0 / 0) | 0 | 20.374812 .. OPEN | 0 / 8 (0) / 0 / 8 (0) |
| B10-02 | Isolated / combined footings | 26 | 25 / 64.3040 | 1 / 2.176 .. 2.275 | 0 (0 / 0 / 0) | 0 | 66.4800 .. 66.5790 | 0 / 26 (0) / 0 / 26 (0) |
| B10-03 | Necks | 36 | 0 / 0 | 32 / 8.7724 .. 11.3460 | 4 (4 / 0 / 0) | 0 | 8.7724 .. OPEN | 0 / 36 (0) / 0 / 36 (0) |
| B10-04 | Strap / ground beams | 71 | 35 / 27.151055 | 11 / 1.20291 .. 5.750071 | 20 (19 / 1 / 0) | 5 | 28.353965 .. OPEN | 0 / 66 (0) / 1 / 66 (1.746943) |
| B10-05 | Ground slab | 26 | 26 / 21.638458 | 0 / 0 .. 0 | 0 (0 / 0 / 0) | 0 | 21.638458 .. 21.638458 | 0 / 26 (0) / 0 / 26 (0) |
| B10-06 | Columns | 72 | 30 / 19.7765 | 20 / 9.6702 .. 12.4140 | 9 (7 / 0 / 2) | 13 | 29.4467 .. OPEN | 0 / 59 (0) / 0 / 59 (0) |
| B10-07 | Beams | 192 | 112 / 66.920678 | 14 / 5.983229 .. 8.412710 | 12 (12 / 0 / 0) | 54 | 72.903907 .. OPEN | 0 / 138 (0) / 0 / 138 (0) |
| B10-08 | Suspended slabs | 75 | 62 / 60.280155 | 0 / 0 .. 0 | 0 (0 / 0 / 0) | 13 | 60.280155 .. 60.280155 | 62 / 62 (60.280155) / 0 / 62 (0) |
| B10-09 | Domes / rings | 5 | 2 / 5.081362 | 0 / 0 .. 0 | 1 (1 / 0 / 0) | 2 | 5.081362 .. OPEN | 0 / 3 (0) / 0 / 3 (0) |
| B10-10 | Pool / tank / lift pit / pump room | 7 | 2 / 7.202297 | 0 / 0 .. 0 | 3 (3 / 0 / 0) | 2 | 7.202297 .. OPEN | 0 / 5 (0) / 0 / 5 (0) |
| B10-11 | Boundary wall concrete | 2 | 0 / 0 | 1 / 5.6392 .. 11.0328 | 1 (1 / 0 / 0) | 0 | 5.6392 .. OPEN | 0 / 2 (0) / 0 / 2 (0) |
| B10-12 | RC parapets | 4 | 0 / 0 | 0 / 0 .. 0 | 4 (4 / 0 / 0) | 0 | 0 .. OPEN | 0 / 4 (0) / 0 / 4 (0) |
| **TRADE** | all STR.CONC | 596 | 317 / 291.473824 | 84 / 41.084313 .. 64.696779 | 105 (63 / 14 / 28) | 90 | 332.558137 .. OPEN | 62 / 506 (60.280155) / 1 / 506 (1.746943) |

## Reference comparison, apart (freelancer cover totals, key map T001B)

Reference and difference shown at 6 dp; the JSON keeps the stored value exactly. The difference is reference - engine RELEASED only; the engine range is printed beside it, never netted into it.

| Key | Reference m3 | Engine released m3 | Engine range m3 | Held (bounded + blank) | Ref - released m3 | % | Verified whole |
|---|---|---|---|---|---|---|---|
| CONC.BLINDING (STR.CONC.BLINDING) | 47.055000 | 12.734438 | 20.374812 .. OPEN | 5 + 2 | 34.320562 | suppressed | 0 / 8 |
| CONC.FOOTING (STR.CONC.FOOTING, STR.CONC.STRAP, STR.CONC.BOUNDARY_WALL) | 77.630500 | 67.6945 | 75.5392 .. 81.6556 | 4 + 0 | 9.936000 | suppressed | 0 / 32 |
| CONC.GROUND (STR.CONC.GROUND_BEAM, STR.CONC.GROUND_SLAB) | 75.090000 | 45.399013 | 46.572423 .. OPEN | 9 + 20 | 29.690987 | suppressed | 0 / 87 |
| CONC.COLUMN (STR.CONC.NECK, STR.CONC.COLUMN) | 39.751500 | 19.7765 | 38.2191 .. OPEN | 52 + 13 | 19.975000 | suppressed | 0 / 95 |
| CONC.BEAM (STR.CONC.BEAM) | 65.965875 | 66.920678 | 72.903907 .. OPEN | 14 + 12 | -0.954803 | suppressed | 0 / 138 |
| CONC.SLAB (STR.CONC.SLAB) | 59.817400 | 60.280155 | 60.280155 .. 60.280155 | 0 + 0 | -0.462755 | -0.77 | 62 / 62 |
| CONC.STAIR_DOME (STR.CONC.STAIR, STR.CONC.DOME) | 21.832800 | 10.450243 | 10.450243 .. OPEN | 0 + 6 | 11.382557 | suppressed | 0 / 14 |
| CONC.POOL (STR.CONC.POOL) | 12.348000 | 7.202297 | 7.202297 .. OPEN | 0 + 1 | 5.145703 | suppressed | 0 / 3 |

Causes (quoted from the merged scorecard V12 sections, each scored on its own candidate; m3 by class):

- CONC.BLINDING <- T-551/blinding (ref 47.055, engine 12.734438): HELD 34.320562
- CONC.FOOTING <- T-551/footing-line@V12 (ref 77.6305, engine 67.6945): ENGINE_RIGHT -0.628, HELD 10.564
- CONC.GROUND: UNRESOLVED: no merged reconciliation section for this key (scorecard V12 has none); nothing classed here
- CONC.COLUMN <- T-551/columns@V12 (ref 28.5465, engine 19.7765): ENGINE_RIGHT 1.52200, RULE_DIFFERENCE -2.66625, HELD 10.34925, UNRESOLVED -0.435
- CONC.COLUMN <- T-551/necks (ref 8.805, engine 0): HELD 8.805
- CONC.COLUMN <- T-551/lift-walls@V12 (ref 2.4, engine 0): ENGINE_RIGHT 0.75, HELD 1.65
- CONC.BEAM <- T-545/beams@V12 (ref 66.093875, engine 66.321054): ENGINE_RIGHT -12.639125, RULE_DIFFERENCE 2.66625, HELD 7.376418, UNRESOLVED 2.369278
- CONC.SLAB: UNRESOLVED: no merged reconciliation section for this key (scorecard V12 has none); nothing classed here
- CONC.STAIR_DOME: UNRESOLVED: no merged reconciliation section for this key (scorecard V12 has none); nothing classed here
- CONC.POOL: UNRESOLVED: no merged reconciliation section for this key (scorecard V12 has none); nothing classed here

Not keyed (no reference row): STR.CONC.LINTEL, STR.CONC.PARAPET, STR.CONC.LIFT, STR.CONC.BOUNDARY_PAD.

- F-T679-2 (CONC.COLUMN): the reference row 'total walls and columns' carries the lift pit walls (T-551/lift-walls: 2.4 m3 of it), the key map's engine side does not hold STR.CONC.LIFT (B10-10): the key is not like for like by that scope; shown beside, the key map is not changed here
- F-T679-3 (CONC.BEAM): cover total 65.965875 m3 (key map) vs the T-545 section reference 66.093875 m3: the merged beam section reconciles a reference that is not the cover total; its class split is quoted against its own reference

## HELD lines (189), each with its cause

| Family | Line | Code | Bound m3 | Cause class | Cause | Source |
|---|---|---|---|---|---|---|
| B10-01 | L-080c97f5 | BLINDING | 0.435 .. 0.59 | DESIGNER ITEM | Q-31 C (F10 + F readings A / B) | T-669 census (V3.0.63) |
| B10-01 | L-10032bf9 | BLINDING | 0.0 .. 0.189 | DESIGNER ITEM | D-14 (blinding beyond the plot line) | T-669 census (V3.0.63) |
| B10-01 | L-16b95607 | BLINDING | 2.256 .. 2.352 | OPEN BOUND | FF lift-raft blinding projection drawn, not dimensioned (ST p.14) | T-669 census (V3.0.63) |
| B10-01 | L-35382b18 | BLINDING | 0.0 .. 0.912684 | DESIGNER ITEM | D-15 (blinding under straps) | T-669 census (V3.0.63) |
| B10-01 | L-7a5214a3 | BLINDING | 4.949374 .. 9.422514 | DESIGNER ITEM | D-33 / D-35 (ground-beam sections under the blinding) | T-669 census (V3.0.63) |
| B10-01 | L-893c3db1 | BLINDING | blank | DESIGNER ITEM | pool blinding HELD LOWER_ONLY >= 0.915529 (T-667 MERGED; wired T-668 ADD_LOWER_ONLY): projection beyond the wrap drawn, not dimensioned (C4) and F8 / F4 / FN fo | T-667 / T-668 (classed by T-679 from the merged text; no census row) |
| B10-01 | L-d0313e5d | BLINDING | blank | DESIGNER ITEM | Q-28 (pad count; pad blinding projections not dimensioned) | T-669 census (V3.0.63) |
| B10-02 | L-164ae9d3 | FOOTING | 2.176 .. 2.275 | DESIGNER ITEM | Q-31 C readings under the V3.0.11 conflict record (F10 + F); T-595 third reading named WAITING | T-669 census (V3.0.63) |
| B10-03 | L-05a99150 | NECK | 0.235 .. 0.315 | OPEN BOUND | founding level not printed (ST p.9 note 1 minimum, p.13 'LESS THAN 2.5m'; Q-21 C: decided on site with engineering approval) | T-669 census (V3.0.63) |
| B10-03 | L-12f3d8b9 | NECK | blank | DESIGNER ITEM | D-43 / D-63 (lift raft depth, lift necks) | T-669 census (V3.0.63) |
| B10-03 | L-132cf605 | NECK | 0.5874 .. 0.66 | OPEN BOUND | founding level not printed (ST p.9 note 1 minimum, p.13 'LESS THAN 2.5m'; Q-21 C: decided on site with engineering approval) | T-669 census (V3.0.63) |
| B10-03 | L-15b8ad39 | NECK | 0.4272 .. 0.54 | OPEN BOUND | founding level not printed (ST p.9 note 1 minimum, p.13 'LESS THAN 2.5m'; Q-21 C: decided on site with engineering approval) | T-669 census (V3.0.63) |
| B10-03 | L-15d9da9b | NECK | 0.0972 .. 0.18 | OPEN BOUND | founding level not printed (ST p.9 note 1 minimum, p.13 'LESS THAN 2.5m'; Q-21 C: decided on site with engineering approval) | T-669 census (V3.0.63) |
| B10-03 | L-1a9e4696 | NECK | 0.1152 .. 0.198 | OPEN BOUND | founding level not printed (ST p.9 note 1 minimum, p.13 'LESS THAN 2.5m'; Q-21 C: decided on site with engineering approval) | T-669 census (V3.0.63) |
| B10-03 | L-31494639 | NECK | 0.267 .. 0.33 | OPEN BOUND | founding level not printed (ST p.9 note 1 minimum, p.13 'LESS THAN 2.5m'; Q-21 C: decided on site with engineering approval) | T-669 census (V3.0.63) |
| B10-03 | L-34346cb4 | NECK | 0.1152 .. 0.198 | OPEN BOUND | founding level not printed (ST p.9 note 1 minimum, p.13 'LESS THAN 2.5m'; Q-21 C: decided on site with engineering approval) | T-669 census (V3.0.63) |
| B10-03 | L-3f7b9501 | NECK | 0.2895 .. 0.3225 | OPEN BOUND | founding level not printed (ST p.9 note 1 minimum, p.13 'LESS THAN 2.5m'; Q-21 C: decided on site with engineering approval) | T-669 census (V3.0.63) |
| B10-03 | L-46f2b702 | NECK | 0.282 .. 0.315 | OPEN BOUND | founding level not printed (ST p.9 note 1 minimum, p.13 'LESS THAN 2.5m'; Q-21 C: decided on site with engineering approval) | T-669 census (V3.0.63) |
| B10-03 | L-486cd9a0 | NECK | 0.3384 .. 0.378 | OPEN BOUND | founding level not printed (ST p.9 note 1 minimum, p.13 'LESS THAN 2.5m'; Q-21 C: decided on site with engineering approval) | T-669 census (V3.0.63) |
| B10-03 | L-48f2e06e | NECK | 0.267 .. 0.3 | OPEN BOUND | founding level not printed (ST p.9 note 1 minimum, p.13 'LESS THAN 2.5m'; Q-21 C: decided on site with engineering approval) | T-669 census (V3.0.63) |
| B10-03 | L-4ec473f7 | NECK | 0.192 .. 0.33 | OPEN BOUND | founding level not printed (ST p.9 note 1 minimum, p.13 'LESS THAN 2.5m'; Q-21 C: decided on site with engineering approval) | T-669 census (V3.0.63) |
| B10-03 | L-4ef35980 | NECK | 0.1062 .. 0.189 | OPEN BOUND | founding level not printed (ST p.9 note 1 minimum, p.13 'LESS THAN 2.5m'; Q-21 C: decided on site with engineering approval) | T-669 census (V3.0.63) |
| B10-03 | L-516989b8 | NECK | 0.267 .. 0.3 | OPEN BOUND | founding level not printed (ST p.9 note 1 minimum, p.13 'LESS THAN 2.5m'; Q-21 C: decided on site with engineering approval) | T-669 census (V3.0.63) |
| B10-03 | L-53d0b6af | NECK | 0.192 .. 0.33 | OPEN BOUND | founding level not printed (ST p.9 note 1 minimum, p.13 'LESS THAN 2.5m'; Q-21 C: decided on site with engineering approval) | T-669 census (V3.0.63) |
| B10-03 | L-5aec8a00 | NECK | 0.2895 .. 0.3225 | OPEN BOUND | founding level not printed (ST p.9 note 1 minimum, p.13 'LESS THAN 2.5m'; Q-21 C: decided on site with engineering approval) | T-669 census (V3.0.63) |
| B10-03 | L-5efd9ac6 | NECK | 0.3384 .. 0.378 | OPEN BOUND | founding level not printed (ST p.9 note 1 minimum, p.13 'LESS THAN 2.5m'; Q-21 C: decided on site with engineering approval) | T-669 census (V3.0.63) |
| B10-03 | L-6a2040e0 | NECK | 0.1152 .. 0.198 | OPEN BOUND | founding level not printed (ST p.9 note 1 minimum, p.13 'LESS THAN 2.5m'; Q-21 C: decided on site with engineering approval) | T-669 census (V3.0.63) |
| B10-03 | L-734ff1a7 | NECK | 0.192 .. 0.33 | OPEN BOUND | founding level not printed (ST p.9 note 1 minimum, p.13 'LESS THAN 2.5m'; Q-21 C: decided on site with engineering approval) | T-669 census (V3.0.63) |
| B10-03 | L-85df35f1 | NECK | 0.192 .. 0.33 | OPEN BOUND | founding level not printed (ST p.9 note 1 minimum, p.13 'LESS THAN 2.5m'; Q-21 C: decided on site with engineering approval) | T-669 census (V3.0.63) |
| B10-03 | L-8eb74a02 | NECK | blank | DESIGNER ITEM | D-43 / D-63 (lift raft depth, lift necks) | T-669 census (V3.0.63) |
| B10-03 | L-953e87a3 | NECK | blank | DESIGNER ITEM | D-43 / D-63 (lift raft depth, lift necks) | T-669 census (V3.0.63) |
| B10-03 | L-995eca94 | NECK | 0.3792 .. 0.432 | OPEN BOUND | founding level not printed (ST p.9 note 1 minimum, p.13 'LESS THAN 2.5m'; Q-21 C: decided on site with engineering approval) | T-669 census (V3.0.63) |
| B10-03 | L-ae1bd9cb | NECK | 0.237 .. 0.27 | OPEN BOUND | founding level not printed (ST p.9 note 1 minimum, p.13 'LESS THAN 2.5m'; Q-21 C: decided on site with engineering approval) | T-669 census (V3.0.63) |
| B10-03 | L-b21cbf65 | NECK | 0.519 .. 0.585 | OPEN BOUND | founding level not printed (ST p.9 note 1 minimum, p.13 'LESS THAN 2.5m'; Q-21 C: decided on site with engineering approval) | T-669 census (V3.0.63) |
| B10-03 | L-b4c234c8 | NECK | 0.5874 .. 0.66 | OPEN BOUND | founding level not printed (ST p.9 note 1 minimum, p.13 'LESS THAN 2.5m'; Q-21 C: decided on site with engineering approval) | T-669 census (V3.0.63) |
| B10-03 | L-bbad8cdb | NECK | 0.3738 .. 0.462 | OPEN BOUND | founding level not printed (ST p.9 note 1 minimum, p.13 'LESS THAN 2.5m'; Q-21 C: decided on site with engineering approval) | T-669 census (V3.0.63) |
| B10-03 | L-bd741a3f | NECK | 0.2376 .. 0.33 | OPEN BOUND | founding level not printed (ST p.9 note 1 minimum, p.13 'LESS THAN 2.5m'; Q-21 C: decided on site with engineering approval) | T-669 census (V3.0.63) |
| B10-03 | L-c1e80218 | NECK | 0.1944 .. 0.36 | OPEN BOUND | founding level not printed (ST p.9 note 1 minimum, p.13 'LESS THAN 2.5m'; Q-21 C: decided on site with engineering approval) | T-669 census (V3.0.63) |
| B10-03 | L-c8c07db4 | NECK | 0.1152 .. 0.198 | OPEN BOUND | founding level not printed (ST p.9 note 1 minimum, p.13 'LESS THAN 2.5m'; Q-21 C: decided on site with engineering approval) | T-669 census (V3.0.63) |
| B10-03 | L-dd3c32e4 | NECK | 0.177 .. 0.315 | OPEN BOUND | founding level not printed (ST p.9 note 1 minimum, p.13 'LESS THAN 2.5m'; Q-21 C: decided on site with engineering approval) | T-669 census (V3.0.63) |
| B10-03 | L-dd6d1141 | NECK | blank | DESIGNER ITEM | D-43 / D-63 (lift raft depth, lift necks) | T-669 census (V3.0.63) |
| B10-03 | L-efe50185 | NECK | 0.3738 .. 0.42 | OPEN BOUND | founding level not printed (ST p.9 note 1 minimum, p.13 'LESS THAN 2.5m'; Q-21 C: decided on site with engineering approval) | T-669 census (V3.0.63) |
| B10-03 | L-f54b7b2a | NECK | 0.192 .. 0.33 | OPEN BOUND | founding level not printed (ST p.9 note 1 minimum, p.13 'LESS THAN 2.5m'; Q-21 C: decided on site with engineering approval) | T-669 census (V3.0.63) |
| B10-03 | L-fc622ff3 | NECK | 0.4806 .. 0.54 | OPEN BOUND | founding level not printed (ST p.9 note 1 minimum, p.13 'LESS THAN 2.5m'; Q-21 C: decided on site with engineering approval) | T-669 census (V3.0.63) |
| B10-04 | L-00465df9 | GROUND_BEAM | blank | DESIGNER ITEM | D-35 | T-669 census (V3.0.63) |
| B10-04 | L-0bb78acc | GROUND_BEAM | blank | DESIGNER ITEM | D-33 | T-669 census (V3.0.63) |
| B10-04 | L-0c5ede7f | GROUND_BEAM | 0.1125 .. 0.15 | DESIGNER ITEM | D-34 (title precedence, 30x30 .. 30x40) | T-669 census (V3.0.63) |
| B10-04 | L-0e852cca | GROUND_BEAM | 0.216 .. 0.288 | DESIGNER ITEM | D-34 (title precedence, 30x30 .. 30x40) | T-669 census (V3.0.63) |
| B10-04 | L-1487bdda | GROUND_BEAM | blank | DESIGNER ITEM | D-33 | T-669 census (V3.0.63) |
| B10-04 | L-21795b35 | GROUND_BEAM | blank | DESIGNER ITEM | D-35 (court G.B depth basis; court structural top / ground level unprinted) | T-669 census (V3.0.63) |
| B10-04 | L-3284f440 | GROUND_BEAM | blank | DESIGNER ITEM | D-35 | T-669 census (V3.0.63) |
| B10-04 | L-402dbe61 | GROUND_BEAM | blank | DESIGNER ITEM | D-35 | T-669 census (V3.0.63) |
| B10-04 | L-4783c6e1 | GROUND_BEAM | blank | DESIGNER ITEM | D-35 | T-669 census (V3.0.63) |
| B10-04 | L-5af89b9f | GROUND_BEAM | blank | DESIGNER ITEM | D-33 | T-669 census (V3.0.63) |
| B10-04 | L-62243c74 | GROUND_BEAM | blank | DESIGNER ITEM | D-35 (court G.B depth basis; court structural top / ground level unprinted) | T-669 census (V3.0.63) |
| B10-04 | L-6bf14711 | GROUND_BEAM | blank | DESIGNER ITEM | D-35 | T-669 census (V3.0.63) |
| B10-04 | L-81444e22 | GROUND_BEAM | 0.1305 .. 0.174 | DESIGNER ITEM | D-34 (title precedence, 30x30 .. 30x40) | T-669 census (V3.0.63) |
| B10-04 | L-95a1f198 | GROUND_BEAM | blank | DESIGNER ITEM | D-33 | T-669 census (V3.0.63) |
| B10-04 | L-970bac56 | GROUND_BEAM | 0.09304 .. 0.130678 | DESIGNER ITEM | D-34 (title precedence, 30x30 .. 30x40) | T-669 census (V3.0.63) |
| B10-04 | L-a55bfa01 | GROUND_BEAM | blank | DESIGNER ITEM | D-35 (court G.B depth basis; court structural top / ground level unprinted) | T-669 census (V3.0.63) |
| B10-04 | L-a8c5c32c | GROUND_BEAM | blank | DESIGNER ITEM | D-33 | T-669 census (V3.0.63) |
| B10-04 | L-b4a13a43 | GROUND_BEAM | blank | DESIGNER ITEM | D-35 | T-669 census (V3.0.63) |
| B10-04 | L-be6708e0 | GROUND_BEAM | blank | OPEN BOUND | neck-cut sliver section not printed (R-GB-NECK-CUT-1) | T-669 census (V3.0.63) |
| B10-04 | L-c0b7102a | GROUND_BEAM | 0.20925 .. 0.279 | DESIGNER ITEM | D-34 (title precedence, 30x30 .. 30x40) | T-669 census (V3.0.63) |
| B10-04 | L-cfb4555c | GROUND_BEAM | blank | DESIGNER ITEM | D-33 | T-669 census (V3.0.63) |
| B10-04 | L-d53e5eb0 | GROUND_BEAM | blank | DESIGNER ITEM | D-33 | T-669 census (V3.0.63) |
| B10-04 | L-d8b98b14 | GROUND_BEAM | blank | DESIGNER ITEM | D-35 | T-669 census (V3.0.63) |
| B10-04 | L-e16c9807 | GROUND_BEAM | blank | DESIGNER ITEM | D-35 | T-669 census (V3.0.63) |
| B10-04 | L-e2134034 | GROUND_BEAM | 0.108 .. 0.144 | DESIGNER ITEM | D-34 (title precedence, 30x30 .. 30x40) | T-669 census (V3.0.63) |
| B10-04 | L-e24946df | GROUND_BEAM | blank | DESIGNER ITEM | D-33 | T-669 census (V3.0.63) |
| B10-04 | L-f0e25ad2 | GROUND_BEAM | 0.108 .. 0.144 | DESIGNER ITEM | D-34 (title precedence, 30x30 .. 30x40) | T-669 census (V3.0.63) |
| B10-04 | L-f24cf117 | GROUND_BEAM | 0.19612 .. 0.261493 | DESIGNER ITEM | D-34 (title precedence, 30x30 .. 30x40) | T-669 census (V3.0.63) |
| B10-04 | L-fb7a6431 | GROUND_BEAM | 0.0 .. 3.5256 | DESIGNER ITEM | Q-28 (RFI) | T-669 census (V3.0.63) |
| B10-04 | L-abd65e1b | STRAP | 0.0 .. 0.385 | DESIGNER ITEM | Q-31 C (SB1 end inside F10 + F) | T-669 census (V3.0.63) |
| B10-04 | L-c823e0db | STRAP | 0.0295 .. 0.2683 | DESIGNER ITEM | D-15 (strap soffit) | T-669 census (V3.0.63) |
| B10-06 | L-0ede77cf | COLUMN | blank | DESIGNER ITEM | D-39 / D-44 | T-669 census (V3.0.63) |
| B10-06 | L-1dc713c8 | COLUMN | 0.756 .. 0.84 | DESIGNER ITEM | D-66 (schedule vs drawn outline CONFLICT, held member by member) | T-669 census (V3.0.63) |
| B10-06 | L-26f6b6f2 | COLUMN | 0.303 .. 0.425 | DESIGNER ITEM | D-39 | T-669 census (V3.0.63) |
| B10-06 | L-291ba2dd | COLUMN | 0.42 .. 0.504 | DESIGNER ITEM | D-66 (schedule vs drawn outline CONFLICT, held member by member) | T-669 census (V3.0.63) |
| B10-06 | L-33a9b772 | COLUMN | 0.303 .. 0.425 | DESIGNER ITEM | D-39 | T-669 census (V3.0.63) |
| B10-06 | L-43dae3d6 | COLUMN | 0.36 .. 0.45 | DESIGNER ITEM | D-66 (schedule vs drawn outline CONFLICT, held member by member) | T-669 census (V3.0.63) |
| B10-06 | L-4aed92c1 | COLUMN | 0.756 .. 0.84 | DESIGNER ITEM | D-66 (schedule vs drawn outline CONFLICT, held member by member) | T-669 census (V3.0.63) |
| B10-06 | L-4c449657 | COLUMN | 0.9 .. 1.0125 | DESIGNER ITEM | D-66 (schedule vs drawn outline CONFLICT, held member by member) | T-669 census (V3.0.63) |
| B10-06 | L-53f223b0 | COLUMN | 0.4242 .. 0.595 | DESIGNER ITEM | D-39 | T-669 census (V3.0.63) |
| B10-06 | L-541c7e56 | COLUMN | blank | MEASURABLE NOW | T-678 outline_778: bounded in research, wiring pending (lane I) | T-678 (V3.0.65, merged f8515d4b, unwired) |
| B10-06 | L-694a75c8 | COLUMN | blank | DESIGNER ITEM | D-39 / Q-54B / D-66 | T-669 census (V3.0.63) |
| B10-06 | L-755eb56b | COLUMN | 0.756 .. 1.05 | DESIGNER ITEM | D-66 (schedule vs drawn outline CONFLICT, held member by member) | T-669 census (V3.0.63) |
| B10-06 | L-831f6fe3 | COLUMN | 0.42 .. 0.63 | DESIGNER ITEM | D-66 (schedule vs drawn outline CONFLICT, held member by member) | T-669 census (V3.0.63) |
| B10-06 | L-85809d3d | COLUMN | 0.672 .. 0.84 | DESIGNER ITEM | D-66 (schedule vs drawn outline CONFLICT, held member by member) | T-669 census (V3.0.63) |
| B10-06 | L-8de64040 | COLUMN | 0.45 .. 0.5625 | DESIGNER ITEM | D-66 (schedule vs drawn outline CONFLICT, held member by member) | T-669 census (V3.0.63) |
| B10-06 | L-8f8ad257 | COLUMN | 0.42 .. 0.525 | DESIGNER ITEM | D-66 (schedule vs drawn outline CONFLICT, held member by member) | T-669 census (V3.0.63) |
| B10-06 | L-919a5749 | COLUMN | 0.303 .. 0.425 | DESIGNER ITEM | D-39 | T-669 census (V3.0.63) |
| B10-06 | L-9cb26d86 | COLUMN | 0.36 .. 0.45 | DESIGNER ITEM | D-66 (schedule vs drawn outline CONFLICT, held member by member) | T-669 census (V3.0.63) |
| B10-06 | L-9f5a6470 | COLUMN | blank | DESIGNER ITEM | D-39 / Q-54B / D-66 | T-669 census (V3.0.63) |
| B10-06 | L-a87ea657 | COLUMN | 0.504 .. 0.735 | DESIGNER ITEM | D-66 (schedule vs drawn outline CONFLICT, held member by member) | T-669 census (V3.0.63) |
| B10-06 | L-bc01297b | COLUMN | blank | DESIGNER ITEM | D-39 / D-66 | T-669 census (V3.0.63) |
| B10-06 | L-c0b3340a | COLUMN | blank | DESIGNER ITEM | D-39 / Q-54B / D-66 | T-669 census (V3.0.63) |
| B10-06 | L-c10e2945 | COLUMN | blank | DESIGNER ITEM | D-39 / D-44 / D-66 | T-669 census (V3.0.63) |
| B10-06 | L-c677b628 | COLUMN | 0.42 .. 0.63 | DESIGNER ITEM | D-66 (schedule vs drawn outline CONFLICT, held member by member) | T-669 census (V3.0.63) |
| B10-06 | L-cc702b85 | COLUMN | 0.42 .. 0.525 | DESIGNER ITEM | D-66 (schedule vs drawn outline CONFLICT, held member by member) | T-669 census (V3.0.63) |
| B10-06 | L-d79d17d1 | COLUMN | 0.303 .. 0.425 | DESIGNER ITEM | D-39 | T-669 census (V3.0.63) |
| B10-06 | L-e112e2ad | COLUMN | 0.42 .. 0.525 | DESIGNER ITEM | D-66 (schedule vs drawn outline CONFLICT, held member by member) | T-669 census (V3.0.63) |
| B10-06 | L-e6c1c9a7 | COLUMN | blank | DESIGNER ITEM | D-39 / Q-54B / D-66 | T-669 census (V3.0.63) |
| B10-06 | L-fad18af6 | COLUMN | blank | MEASURABLE NOW | T-678 annex_C3: bounded in research, wiring pending (lane I) | T-678 (V3.0.65, merged f8515d4b, unwired) |
| B10-07 | L-17c4238c | BEAM | blank | DESIGNER ITEM | D-26 (PROJECTION) | T-669 census (V3.0.63) |
| B10-07 | L-1fd49f3e | BEAM | 2.262872 .. 2.545691 | DESIGNER ITEM | D-27 (WIDTH) | T-669 census (V3.0.63) |
| B10-07 | L-2c7b0b1e | BEAM | 0.347 .. 0.4338 | DESIGNER ITEM | D-27 (WIDTH) | T-669 census (V3.0.63) |
| B10-07 | L-331d4bbe | BEAM | blank | DESIGNER ITEM | D-05/D-26 (PROJECTION) | T-669 census (V3.0.63) |
| B10-07 | L-377cb988 | BEAM | blank | DESIGNER ITEM | D-26 (PROJECTION) | T-669 census (V3.0.63) |
| B10-07 | L-39ca5340 | BEAM | 0.44255 .. 0.55323 | DESIGNER ITEM | D-27 (WIDTH) | T-669 census (V3.0.63) |
| B10-07 | L-43e804ba | BEAM | 0.4563 .. 0.5475 | DESIGNER ITEM | D-02 (WIDTH) | T-669 census (V3.0.63) |
| B10-07 | L-50667f69 | BEAM | 0.2875 .. 0.345 | DESIGNER ITEM | D-02 (WIDTH) | T-669 census (V3.0.63) |
| B10-07 | L-54e397fe | BEAM | blank | DESIGNER ITEM | D-05/D-26 (PROJECTION) | T-669 census (V3.0.63) |
| B10-07 | L-56d278be | BEAM | blank | DESIGNER ITEM | D-05/D-26 (PROJECTION) | T-669 census (V3.0.63) |
| B10-07 | L-60f09eec | BEAM | 0.335 .. 0.4188 | DESIGNER ITEM | D-27 (WIDTH) | T-669 census (V3.0.63) |
| B10-07 | L-634cefe5 | BEAM | blank | DESIGNER ITEM | D-05/D-26 (PROJECTION) | T-669 census (V3.0.63) |
| B10-07 | L-67f3d325 | BEAM | blank | DESIGNER ITEM | D-05/D-26 (PROJECTION) | T-669 census (V3.0.63) |
| B10-07 | L-7c3edce2 | BEAM | 0.112 .. 0.336 | DESIGNER ITEM | D-04 (UNLABELLED) | T-669 census (V3.0.63) |
| B10-07 | L-88ccf8d4 | BEAM | 0.212 .. 0.3975 | DESIGNER ITEM | D-03 (TWO_MARKS) | T-669 census (V3.0.63) |
| B10-07 | L-8d031491 | BEAM | 0.0904 .. 0.2712 | DESIGNER ITEM | D-04 (UNLABELLED) | T-669 census (V3.0.63) |
| B10-07 | L-9e489566 | BEAM | 1.013607 .. 1.266989 | DESIGNER ITEM | D-27 (WIDTH) | T-669 census (V3.0.63) |
| B10-07 | L-a9d5e7dc | BEAM | blank | DESIGNER ITEM | D-05/D-26 (PROJECTION) | T-669 census (V3.0.63) |
| B10-07 | L-ab37afa1 | BEAM | blank | DESIGNER ITEM | D-28 (RING) | T-669 census (V3.0.63) |
| B10-07 | L-aba59a21 | BEAM | blank | DESIGNER ITEM | D-26 (PROJECTION) | T-669 census (V3.0.63) |
| B10-07 | L-bb49e831 | BEAM | blank | DESIGNER ITEM | D-05/D-26 (PROJECTION) | T-669 census (V3.0.63) |
| B10-07 | L-bef35462 | BEAM | 0.0 .. 0.025 | DESIGNER ITEM | BAND0030.2 depth companion 0 .. 0.025: strip depth B4 0.50 vs B7 0.75, no mark printed on the strip (T-642 FR-T642-2; wired T-671 ADD_COMPANION) | T-642 / T-671 (classed by T-679 from the merged text; no census row) |
| B10-07 | L-d62d2fcf | BEAM | 0.248 .. 0.744 | DESIGNER ITEM | D-04 (UNLABELLED) | T-669 census (V3.0.63) |
| B10-07 | L-dc8cbfc1 | BEAM | 0.112 .. 0.336 | DESIGNER ITEM | D-04 (UNLABELLED) | T-669 census (V3.0.63) |
| B10-07 | L-f83c4a46 | BEAM | 0.064 .. 0.192 | DESIGNER ITEM | D-04 (UNLABELLED) | T-669 census (V3.0.63) |
| B10-07 | L-fbb65dfd | BEAM | blank | DESIGNER ITEM | D-26 (PROJECTION) | T-669 census (V3.0.63) |
| B10-09 | L-d5401fa8 | DOME | blank | DESIGNER ITEM | consultant 2026-10-24 G3 (upper-roof dome: no structural detail) | T-669 census (V3.0.63) |
| B10-10 | L-5ae06fda | LIFT | blank | DESIGNER ITEM | D-43 (lift tie beam section not printed) | T-669 census (V3.0.63) |
| B10-10 | L-684fcad3 | LIFT | blank | DESIGNER ITEM | D-43 (lift pit depth 'as per manufacturer') | T-669 census (V3.0.63) |
| B10-10 | L-b62a7065 | POOL | blank | DESIGNER ITEM | consultant 2026-10-23 row 3 / P-2 (pool steps not drawn) | T-669 census (V3.0.63) |
| B10-11 | L-cda8f415 | BOUNDARY_PAD | blank | DESIGNER ITEM | Q-28 (boundary columns 'SEE ARCH PLAN', none drawn: pad count) | T-669 census (V3.0.63) |
| B10-11 | L-6290a9f3 | BOUNDARY_WALL | 5.6392 .. 11.0328 | MEASURABLE NOW | T-659 bound 5.6392 .. 11.0328 merged (T-666 confirmed, residual 0): wire in T-668; then Q-28 (B.W 20x60 vs 20x40) keeps it bounded | T-669 census (V3.0.63) |
| B10-12 | L-030538dd | PARAPET | blank | DESIGNER ITEM | Q-65 C + D-39 (parapet material above the upstand; roof build-up) | T-669 census (V3.0.63) |
| B10-12 | L-1d419b64 | PARAPET | blank | DESIGNER ITEM | Q-65 C + D-39 (parapet material above the upstand; roof build-up) | T-669 census (V3.0.63) |
| B10-12 | L-9a2c8116 | PARAPET | blank | DESIGNER ITEM | Q-65 C + D-39 (parapet material above the upstand; roof build-up) | T-669 census (V3.0.63) |
| B10-12 | L-b5ffc172 | PARAPET | blank | DESIGNER ITEM | Q-65 C + D-39 (parapet material above the upstand; roof build-up) | T-669 census (V3.0.63) |
| B7-12 | L-061e18cf | STAIR | blank | MEASURABLE NOW | steps: T-258 ST03-E1-STEPS DRAWING-CONFIRMED (5 riser lines ST p.3 / arch GF / B-B); waist S-9; riser 0.170 confirmation D-56 (beside) | T-673 census (V3.0.64) |
| B7-12 | L-659243ed | STAIR | blank | DESIGNER ITEM | C-ST-3 (junction section of the two plates 0.168 apart not drawn) | T-673 census (V3.0.64) |
| B7-12 | L-7863355d | STAIR | blank | DESIGNER ITEM | C-ST-4 / RFI-A04 (MS1-L: arch 10 fronts vs ST p.4 12; owner 2026-10-22 'MS1-L HELD'), D-67 / C-ST-3 (winder, turn soffit not drawn) | T-673 census (V3.0.64) |
| B7-12 | L-821032bc | STAIR | blank | DESIGNER ITEM | S-9 (waist thickness / support not printed) | T-673 census (V3.0.64) |
| B7-12 | L-b6b0354b | STAIR | blank | DESIGNER ITEM | D-08 / owner Q-50 / Q-51 (curved parts HELD), C-ST-3; CA level not stated (0 .. 0.09) | T-673 census (V3.0.64) |
| B9-02 | L-005334b6 | LINTEL | blank | MEASURABLE NOW | R-T673-1 existence on the merged drawn head (T-201 / T-238) + R-T673-3 range on the T-644 jamb evidence | T-673 census (V3.0.64) |
| B9-02 | L-072bc37c | LINTEL | blank | DESIGNER ITEM | D-GF-09 (T-581 DRAWING CONFLICT: D120 1.00 frame in a 0.90 gap) | T-673 census (V3.0.64) |
| B9-02 | L-0d5e2e3a | LINTEL | blank | OPEN BOUND | the lift tie beam depth and level (D-43) | T-678 (V3.0.65, merged f8515d4b, unwired) |
| B9-02 | L-1313767d | LINTEL | blank | OPEN BOUND | annex roof slab top (Q-54 B / D-39) | T-678 (V3.0.65, merged f8515d4b, unwired) |
| B9-02 | L-17953d78 | LINTEL | blank | OPEN BOUND | the GF-W30 run (band) and its jamb evidence | T-678 (V3.0.65, merged f8515d4b, unwired) |
| B9-02 | L-1a078491 | LINTEL | blank | MEASURABLE NOW | HELD bounded (existence REQUIRED, quantity a range) | T-678 (V3.0.65, merged f8515d4b, unwired) |
| B9-02 | L-1c0e7646 | LINTEL | blank | OPEN BOUND | BM-2F-017 depth: REQUIRED for any depth <= 0.52 m on the drawn 2F slab-top bound (12.68 - 9.70 - D >= 2.20 + 0.20 + 0.06); above that the D-39 slab top decides | T-678 (V3.0.65, merged f8515d4b, unwired) |
| B9-02 | L-274b1125 | LINTEL | blank | MEASURABLE NOW | HELD bounded (existence REQUIRED, quantity a range) | T-678 (V3.0.65, merged f8515d4b, unwired) |
| B9-02 | L-2c1c49db | LINTEL | blank | OPEN BOUND | dome ring soffit over 1F-W11 (T-227, designer) | T-678 (V3.0.65, merged f8515d4b, unwired) |
| B9-02 | L-2efe4809 | LINTEL | blank | MEASURABLE NOW | R-T650-1 BOUNDED (T-650 MERGED 2a2e28ca; Checker 07:06 arithmetic AGREE, A-1F-01 width engine-read only) | T-673 census (V3.0.64) |
| B9-02 | L-3af715c6 | LINTEL | blank | MEASURABLE NOW | HELD bounded (existence REQUIRED, quantity a range) | T-678 (V3.0.65, merged f8515d4b, unwired) |
| B9-02 | L-40e8c259 | LINTEL | blank | MEASURABLE NOW | R-T673-1 existence on the merged drawn head (T-201 / T-238) + R-T673-3 range on the T-644 jamb evidence | T-673 census (V3.0.64) |
| B9-02 | L-441ae5fe | LINTEL | blank | MEASURABLE NOW | R-T673-1 existence on the merged drawn head (T-201 / T-238) + R-T673-3 range on the T-644 jamb evidence | T-673 census (V3.0.64) |
| B9-02 | L-47882fa3 | LINTEL | blank | MEASURABLE NOW | HELD bounded (existence REQUIRED, quantity a range) | T-678 (V3.0.65, merged f8515d4b, unwired) |
| B9-02 | L-4a12b894 | LINTEL | blank | MEASURABLE NOW | R-T650-1 BOUNDED (T-650 MERGED 2a2e28ca; Checker 07:06 arithmetic AGREE, A-1F-01 width engine-read only) | T-673 census (V3.0.64) |
| B9-02 | L-53ef44d8 | LINTEL | blank | MEASURABLE NOW | R-T673-1 existence on the merged drawn head (T-201 / T-238) + R-T673-3 range on the T-644 jamb evidence | T-673 census (V3.0.64) |
| B9-02 | L-6057028f | LINTEL | blank | MEASURABLE NOW | R-T673-1 existence on the merged drawn head (T-201 / T-238) + R-T673-3 range on the T-644 jamb evidence | T-673 census (V3.0.64) |
| B9-02 | L-6692d02c | LINTEL | blank | MEASURABLE NOW | R-T673-1 existence on the merged drawn head (T-201 / T-238) + R-T673-3 range on the T-644 jamb evidence | T-673 census (V3.0.64) |
| B9-02 | L-71998da6 | LINTEL | blank | MEASURABLE NOW | HELD bounded (existence REQUIRED, quantity a range) | T-678 (V3.0.65, merged f8515d4b, unwired) |
| B9-02 | L-78634467 | LINTEL | blank | MEASURABLE NOW | R-T673-1 existence on the merged drawn head (T-201 / T-238) + R-T673-3 range on the T-644 jamb evidence | T-673 census (V3.0.64) |
| B9-02 | L-7f9eb7cc | LINTEL | blank | OPEN BOUND | annex roof slab top (Q-54 B / D-39) | T-678 (V3.0.65, merged f8515d4b, unwired) |
| B9-02 | L-882717b0 | LINTEL | blank | MEASURABLE NOW | R-T673-1 existence on the merged drawn head (T-201 / T-238) + R-T673-3 range on the T-644 jamb evidence | T-673 census (V3.0.64) |
| B9-02 | L-8f69c407 | LINTEL | blank | DESIGNER ITEM | D-45 / register LIFT LANDING DOOR LINTEL | T-673 census (V3.0.64) |
| B9-02 | L-96160886 | LINTEL | blank | OPEN BOUND | T-227 (designer) | T-678 (V3.0.65, merged f8515d4b, unwired) |
| B9-02 | L-9ec762c0 | LINTEL | blank | MEASURABLE NOW | HELD bounded (existence REQUIRED, quantity a range) | T-678 (V3.0.65, merged f8515d4b, unwired) |
| B9-02 | L-a500f10e | LINTEL | blank | DESIGNER ITEM | D-45 / register LIFT LANDING DOOR LINTEL | T-673 census (V3.0.64) |
| B9-02 | L-a7848a35 | LINTEL | blank | MEASURABLE NOW | HELD bounded (existence REQUIRED, quantity a range) | T-678 (V3.0.65, merged f8515d4b, unwired) |
| B9-02 | L-a7b8b292 | LINTEL | blank | MEASURABLE NOW | HELD bounded (existence REQUIRED, quantity a range) | T-678 (V3.0.65, merged f8515d4b, unwired) |
| B9-02 | L-aca2db3c | LINTEL | blank | MEASURABLE NOW | R-T673-1 existence on the merged drawn head (T-201 / T-238) + R-T673-3 range on the T-644 jamb evidence | T-673 census (V3.0.64) |
| B9-02 | L-b699ce0d | LINTEL | blank | DESIGNER ITEM | D-39 (2F roof datum / build-up) | T-673 census (V3.0.64) |
| B9-02 | L-b729bd63 | LINTEL | blank | OPEN BOUND | the A-GF-01 crown level (with the annex bound c_lo 2.744 above +0.30 under B4: REQUIRED if crown <= 2.484 above FFL) and its width | T-678 (V3.0.65, merged f8515d4b, unwired) |
| B9-02 | L-bf76c173 | LINTEL | blank | MEASURABLE NOW | R-T673-1 existence on the merged drawn head (T-201 / T-238) + R-T673-3 range on the T-644 jamb evidence | T-673 census (V3.0.64) |
| B9-02 | L-bf88bf6f | LINTEL | blank | OPEN BOUND | the 1F stair-shaft landing member level / depth over W25 | T-678 (V3.0.65, merged f8515d4b, unwired) |
| B9-02 | L-c1e57b06 | LINTEL | blank | OPEN BOUND | W11 sill level (REQUIRED if head <= 2.234 above +0.30 under B9 0.75) | T-678 (V3.0.65, merged f8515d4b, unwired) |
| B9-02 | L-d887eecf | LINTEL | blank | DESIGNER ITEM | D-45 | T-673 census (V3.0.64) |
| B9-02 | L-dd5b41a7 | LINTEL | blank | MEASURABLE NOW | R-T673-1 existence on the merged drawn head (T-201 / T-238) + R-T673-3 range on the T-644 jamb evidence | T-673 census (V3.0.64) |
| B9-02 | L-df32d6f4 | LINTEL | blank | OPEN BOUND | side-passage FFL (REQUIRED if <= +0.30: CB7 bound c_lo 2.494, spare 0.034) and the START jamb stopper | T-678 (V3.0.65, merged f8515d4b, unwired) |
| B9-02 | L-e3917519 | LINTEL | blank | OPEN BOUND | W12 sill level (as W11) | T-678 (V3.0.65, merged f8515d4b, unwired) |
| B9-02 | L-ed7aadd0 | LINTEL | blank | MEASURABLE NOW | R-T673-1 existence on the merged drawn head (T-201 / T-238) + R-T673-3 range on the T-644 jamb evidence | T-673 census (V3.0.64) |
| B9-02 | L-f269fabb | LINTEL | blank | MEASURABLE NOW | R-T673-1 existence on the merged drawn head (T-201 / T-238) + R-T673-3 range on the T-644 jamb evidence | T-673 census (V3.0.64) |
| B9-02 | L-f68444ed | LINTEL | blank | MEASURABLE NOW | R-T673-1 existence on the merged drawn head (T-201 / T-238) + R-T673-3 range on the T-644 jamb evidence | T-673 census (V3.0.64) |
| B9-02 | L-f892163c | LINTEL | blank | OPEN BOUND | the 2F stair-shaft member level / depth over W27 | T-678 (V3.0.65, merged f8515d4b, unwired) |
| B9-02 | L-fd68db05 | LINTEL | blank | MEASURABLE NOW | HELD bounded (existence REQUIRED, quantity a range) | T-678 (V3.0.65, merged f8515d4b, unwired) |
| B9-02 | L-fd8aaedc | LINTEL | blank | DESIGNER ITEM | D-45 / register LIFT LANDING DOOR LINTEL | T-673 census (V3.0.64) |
