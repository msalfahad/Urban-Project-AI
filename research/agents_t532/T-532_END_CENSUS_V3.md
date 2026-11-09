# T-532: END_CENSUS_V3, the column junction census on the T-274 piece kinds (F-C-T526-1), rule R-T532-1

Worker 1, lane S, claim 2026-11-05 19:20 UTC, base engine c4a34358 (candidate of record unchanged; released default
V2.9 + route G untouched). Research only: `end_census_v3.py` (project-agnostic rule; V2 imported, never edited),
`t532_alsenan.py` (training-villa check on committed ids / numbers, `--check` reproduces), `out/`,
`tests/t532_end_census_v3/` (fixture P532 + Alsenan pins). No drawing read in this task: the end classes are the
drawing-derived T-526 census (Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip and 'ST7757 dxf.dxf').

## 1. Physical element and engineering question (ERS s.2.1)

The vertical block-to-RC-column joint (perimeter mortar R-T520-1, sharmat ties R-T355-1/-3, crack-mesh strip T-317).
Question (F-C-T526-1): which T-274 piece kinds are masonry and which are concrete, and is a BEAM-kind piece inside a
masonry run a band / lintel course (masonry trade) or structure?

## 2. Answer, from the code that cut the pieces (t274_geom.py `key = {...}` branch)

A T-274 piece is a PLAN stretch of the masonry census run, named by what its mid-point lies in:

| kind | plan role | masonry head | source |
|---|---|---|---|
| COLUMN | concrete | - | mid-point in an architectural column outline |
| ST_COLUMN | concrete | - | mid-point in a structural column outline (none on Alsenan's census runs) |
| BEAM | masonry | beam soffit (storey - printed depth; HELD unprinted) | mid-point in a route G beam band over the wall; build_t274 h = basis - depth; T-317 maps it to BLOCK under BEAM |
| FACE | masonry | slab soffit if SLAB with printed t, else HELD | mid-point in a structural slab-plan face (no band, no column outline) |
| NONE | masonry | HELD | mid-point under nothing drawn |
| other | UNKNOWN | - | HELD by name at every boundary it touches |

So a BEAM piece is neither a band course nor a lintel: it is masonry whose head meets a beam drawn over it (the beam is
structure, measured on its own line; lintels are over openings, T-453 / T-516, never a T-274 piece). The merged T-317 /
T-355 builders already apply exactly this mapping (t317_alsenan.run_pieces); only V2's `end_junctions` took the raw kinds.

## 3. Rule R-T532-1 (new version of the junction census; every villa; provenance F-C-T526-1, T-532)

V3 junctions = one INTERIOR junction at every boundary of a masonry kind and a concrete kind (class '<kind>-<kind>',
column face named), none at masonry-masonry (head change) or concrete-concrete; plus R-T526-1's END junction where the
end piece is masonry. UNKNOWN kinds: HELD by name (interior and end). A column beyond a concrete end piece, or
COLUMN_PIECE_IN_RUN on a masonry end piece, raises (drawing contradiction). V2 stays the rule for BLOCK / COLUMN lists.

## 4. Alsenan (out/SUMMARY_T532.json, JUNCTIONS_V3_T532.csv: 70 straight runs, 349 pieces)

- Before (V2 on the raw kinds): RAISES on 11 runs (the 12 COLUMN ends; GF-W03 has two) and silently lists 0 of the
  118 interior junctions on the other 59 runs (no piece is BLOCK).
- After (V3): end junctions BEAM-END_COLUMN 11 + FACE-END_COLUMN 1 (GF-W10 end 1, white: the Verifier's "all 12 inner
  BEAM" is 11 of 12) + BEAM-PARTIAL_COLUMN 1 HELD (GF-W20 end 1): **the same 12 + 1 ends as T-526, set-equal**, so its
  per-end effects stand unchanged: length / m2 / blocks 0 / 0 / 0, perimeter +0.007021 m3 on 1F-W09 (0.003334 ->
  0.010355), mesh +40.90 m.l owner / +44.10 m.l drawing band, ties +30 nr; the other ends HELD as T-526 names them.
- Interior: BEAM-COLUMN 57, COLUMN-BEAM 52, COLUMN-FACE 5, FACE-COLUMN 3, COLUMN-NONE 1 = 118 LISTED, 0 HELD.
  117 are on ledger runs and match SHARMAT_T355 (117 rows) and the T-317 V-joint columns ONE TO ONE (0 missing either
  way); the 118th is GF|WB-FL0028-FL0029 (t 0.40, no register wall; T-526 named it outside the masonry census).
- Quantity effect of T-532 itself: none new (0 m, 0 m2, 0 nr, 0 m3 vs T-526); it makes the 12 ends wireable on the
  T-274 pieces without raising and proves no interior tie / mesh junction is lost or doubled when it is.

## 5. Verdicts

Freelancer: no tie, mesh or perimeter-mortar row -> RULE_DIFFERENCE (unchanged from T-355 / T-367 / T-526).
V2 on T-274 kinds -> ENGINE_WRONG (raises / skips) -> V3 proposal; V3 vs merged T-355 / T-317 interior junctions AGREE
117 / 117; V3 vs T-526 ends AGREE 12 + 1.

## 6. Lessons row (ERS s.7, proposed)

| 2026-11-05 | a junction census written for BLOCK / COLUMN pieces raised or silently skipped every junction on a ledger whose
pieces are named by what lies ABOVE them (BEAM / FACE / NONE) | a piece kind was read as a material without its
definition | map every ledger kind to its plan role from the code that cut it, with the source named; an unmapped kind
HELD by name (every villa; R-T532-1) | tests/t532_end_census_v3 (P532: FACE / BEAM run ending on a structural-only
column, ties 5 + 4, mesh 3.20 / 2.80 m per side, perimeter +0.005353725 m3; unknown kind HELD; reversal / rotation /
mirror) | PROPOSED |

## 7. For the Checker (re-measure 2 ends)

- 1F-W09 end 0 (1F|WB-FL0024-FL0025, piece 0 BEAM): END junction, column COL-1F-37 C1; perimeter (3.80 - 0.01) x
  0.0018525 = 0.007021 m3.
- GF-W10 end 1 (GF|WB-FL0041-FL0042, last piece FACE, white): END junction FACE-END_COLUMN, COL-GF-01 C4; ties /
  perimeter HELD (Q-60), mesh HELD as T-526.

Reproduce: `python3 -I research/agents_t532/t532_alsenan.py --check`.
