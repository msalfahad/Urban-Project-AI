# R9.1 christiannp post-freeze object-level comparison: executive summary

**What this is:**
- **Basis:** Urban HEAD `2c00561` against the frozen christiannp forensic re-run (`CHRISTIANNP_FORENSIC_RERUN_2026_10_07.zip`, sha256 `fcaff770…7b80`; manifest `af2d3441…97bf2`).
- **Scope:** research only. No AutoCAD or MCP call, no donor rerun, no christiannp script executed, no production change, no S4.
- **Firewall:** no christiannp, U-C4N or freelancer value enters an Urban register. Comparison happens only after Urban's freeze.

## 1. Freeze verification

- **Hashes:** 188 / 188 manifest files match. 0 are missing or altered. The 5 extra root files are byte-identical copies.
- **Drawings:** christiannp measured the same two drawings Urban decodes (ST7757 `9f9d1179…`, P7757 `ab54dd55…`), unchanged before and after. Disk and memory were handle-identical.
- **One missing expected output:** four MCP raw outputs (C018, C019, C021, C022) exist only inside `MCP_RAW_OUTPUTS_PHASE0-3.md`, not as separate files.
- **Correction to earlier summaries:** the earlier report's "85 lines → 42 strips, 200.036 m" was the straight-strip length only. The frozen network is 44 strips, 208.129 m.

## 2. Headline

**The two systems find almost the same physical objects. They differ mainly in conventions and source routes, not in extraction.**

| Trade | Object agreement | Real differences |
|---|---|---|
| Ground beams | 43 / 44 face-handle pairs identical, 0 mm offset | **Urban misses 1 strip** (fragmented mate, 1.000 m); Urban arc rule +0.718 m; column split is a convention (9.05 against 16.26 m); depth is a source-route difference (Urban p.13 sections) |
| Ground slab | 22 of the 23 non-sliver Urban cells = one christiannp face each; 217.012 against 217.683 m² (0.31 %) | **Urban counts the lift pit (S-BW 7BE) inside a slab cell**; thickness 0.10 m both |
| Footings | 26 / 26 outlines identical, 25 identical occurrences | the same F / F10 SOURCE_CONFLICT; different hypothesis sets |
| Columns | 41 christiannp positions → 39 Urban chains, all matched by handle | christiannp counts 3 planted / shifted columns in the storey below (DONOR_FALSE_POSITIVE); splits 2 turned chains |
| Structural beams | 119 / 119 tags matched (115 by handle, 4 tag blocks by mark); 98 same binding | 6 Urban AMBIGUOUS tags christiannp resolves; 8 oblique / wide tags christiannp cannot bind; 7 drawn-width ≠ schedule SOURCE_CONFLICTs |
| Walls | 166 Method-B pairs = christiannp pairs by face handles (270.63 m gross, same) | 2 Urban misses (400 mm wall, fragmented mate: 2.485 m); the per-metre opening definition differs (Urban 53.96 m against christiannp 9.94 m) |
| Slab openings | lift wells and the 4.58 m² void identical | GF void merged with a labelled cell in Urban (S-OPENING not a barrier); stairs and dome fans are assumption differences; **christiannp missed the slab thickness tags** |
| Rebar tokens | 507 rows / 86 tokens: the 3 Urban parsers agree on 74 of 80 bar patterns | 6 split patterns (52 rows), all notes or details; **no footing token splits** |

Gap register (02): 77 non-identical object rows.

| Class | Count |
|---|---|
| SAME_GEOMETRY_DIFFERENT_CONVENTION | 30 |
| SAME_OBJECT_DIFFERENT_SEGMENTATION | 10 |
| SOURCE_CONFLICT | 8 |
| CHRIS_BINDING_FAILURE | 8 |
| URBAN_BINDING_FAILURE | 6 |
| SOURCE_AUTHORITY_DIFFERENCE | 4 |
| ASSUMPTION_DIFFERENCE | 4 |
| URBAN_MISSED_PHYSICAL_OBJECT | 3 |
| DONOR_FALSE_POSITIVE | 3 |
| URBAN_FALSE_POSITIVE | 1 |

The 128 convention-only wall pairs are counted in 07, not in 02.

## 3. Ground slab (§6)

- **Convergence:** the christiannp raster converges. At 10 mm the half-edge figure is within 0.11 % of its vector (217.44 against 217.68 m²), and the two origins differ by ≤ 0.04 m².
- **Raster route: ORACLE_ONLY.**
  - The slab-only raster always under-reads by the edge band (−1.70 m² at 10 mm).
  - It is resolution-dependent and slow.
  - It is an excellent leak / regression oracle and an independent check on Urban's vector cells.
- **Area against thickness authority:** kept separate in both. Thickness is 0.10 m from the TT1 `T=10cm` notes in both systems.
  - Urban publishes the 9 unlabelled cells as CANDIDATE (BEST 217.012 / OFFICIAL 115.275).
  - christiannp applies the note to every cell.
  - The unlabelled cells are legitimate slab geometry (same cells as christiannp). Their thickness scope is an ASSUMPTION_DIFFERENCE, not a geometry gap.
- **Exclusions:** beams, columns and openings are excluded in both, except the lift pit, which Urban's barrier set (layers 1 + 2, columns, single lines) does not exclude.
- **What makes up the remaining −0.671 m²:**
  - same cells −1.161 m² (Urban's single lines are buffered 1 mm);
  - the pit cell +0.880 m²;
  - Urban excluded slivers −0.675 m² against christiannp slivers of +0.23 m² counted.

## 4. Structural beams (§7)

**Urban unresolved, christiannp resolves:** the 6 Urban AMBIGUOUS tags (B1 45D, B8 472, B6 ×4 on FFRS). christiannp's rule is the nearest strip that is parallel, within extent, within 1 m and of schedule width ± 30 mm.

**christiannp unresolved, Urban binds:** 15 tags.
- **8 CHRIS_BINDING_FAILURE.** Horizontal tags on oblique members (B7 ×4, B4 ×2); the 900 mm B27; CA. christiannp's parallel test uses the tag text rotation.
- **7 SOURCE_CONFLICT.** CB2 ×2, B29, B21, B6, CB10 ×2. The drawn width differs from the schedule by 50 mm. christiannp refuses; Urban binds with DRAWN_WIDTH_DIFFERS_FROM_SCHEDULE.

**R1–R5:**
- R4 is safe in all 104 cases (keep it as a gate for tie-breaks, a flag otherwise);
- R3 is safe on one band only;
- R1 is conditional (Urban already raises SPAN_LENGTH / SPAN_COUNT conflicts);
- R2 is unsafe in 2 of 6;
- **R5 is rejected; it is not reintroduced.**

## 5. Rebar (§12): is one canonical bar grammar required before S4?

**No; a narrow parity test is.**
- Every footing token in the christiannp corpus parses identically through the single applicable route (`bar_from_cells`).
- The parser splits are column-tie notes, detail texts and the ground-slab mesh sentence.
- The S4 blocker is BOXED semantics (`3+4` …, 11 rows), which needs a source or a claim.
- christiannp's own kg (13,412.6 kg of INCLUDED components; footings 3,863.5) uses bar length = member dimension (A05). It is evidence, never a target.

## 6. Manual decisions (§13)

Of christiannp's 18 manual decisions, Urban already handles 10 deterministically, 5 partially and 3 not at all.
- **The 3 NO cases:**
  - MD07 junction snapping (NEEDS_NEW_GEOMETRY_ROUTE);
  - MD12 radial fans and MD13 the unmarked stair (both NEEDS_SOURCE_AUTHORITY).
- **Classification:** 12 AUTOMATABLE_NOW, 2 PROJECT_SPECIFIC, 2 NEEDS_SOURCE_AUTHORITY, 1 NEEDS_NEW_GEOMETRY_ROUTE, 1 INHERENT_REVIEW.

## 7. What christiannp does better

- Multi-partner face pairing with a full candidate log and an intervening-face test.
- The arc angular overlap.
- S-OPENING edges as slab barriers.
- S-BW pit boxes treated as voids.
- Width-agnostic wall pairs.
- An orientation + width tie-break for ambiguous beam tags.
- Header-position ATTRIB binding.
- One rebar evidence table with terminal states.
- Free-end and topology QA.
- The raster oracle.

## 8. What Urban does better

- Depth and thickness source routes: p.13 GB sections, stacked `T` / `nn` slab tags.
- Detail-region exclusion by bound beam bands (christiannp's rule removed a real segment, U21).
- Strap clear length (christiannp double-counts 2.64 m³).
- Column chains with planted / turned events.
- Oblique-member beam binding.
- Scenario layers (OFFICIAL / LOWER / BEST / HIGH) instead of assumption-dependent single values.
- No hard-coded project magic numbers (christiannp finds the lift pit by area = 3.24 m² ± 0.01).

## 9. Before S4 (tests and receipts only)

- An S4 token-parity test.
- A footing annotation census with conservation (BOXED stays BLOCKED).
- S4 receipt fields: handles, drawing sha, rule id, CONVENTION_ID and the engine stamp.
- Fixtures FT-01 … FT-04 and RB-01 … RB-03.

Every christiannp-derived geometry fix waits until **after S4** (see 16 and 17).

PyMuPDF remains a separate commercial decision and does not block S4.

## Deliverables

| # | File |
|---|---|
| 00 | this file |
| 01 | `01_CHRIS_FORENSIC_INTAKE.md` |
| 02 | `02_OBJECT_GAP_REGISTER.csv` |
| 03 | `03_GB_OBJECT_CROSSWALK.csv` |
| 04 | `04_GB_TECHNIQUE_ANALYSIS.md` |
| 05 | `05_GROUND_SLAB_ROUTE_COMPARISON.csv` |
| 06 | `06_BEAM_BINDING_CROSSWALK.csv` |
| 07 | `07_WALL_PAIR_CROSSWALK.csv` |
| 08 | `08_FOOTING_OCCURRENCE_CROSSWALK.csv` |
| 09 | `09_COLUMN_CROSSWALK.csv` |
| 10 | `10_SLAB_OPENING_CROSSWALK.csv` |
| 11 | `11_REBAR_TOKEN_CORPUS.csv` |
| 12 | `12_CHRIS_MANUAL_DECISION_GAP.csv` |
| 13 | `13_DONOR_CODE_TECHNIQUES.md` |
| 14 | `14_DONOR_TECHNIQUE_MATRIX_UPDATED.csv` |
| 15 | `15_QUANTITY_RECONCILIATION_UPDATED.csv` / `.json` |
| 16 | `16_PRE_S4_DECISION.md` |
| 17 | `17_TEST_FIXTURE_BACKLOG.md` |

Supporting files:
- `CHRIS_INPUT_LEDGER.json`: every christiannp file read, with its hash.
- `R9_1_SUMMARY.json`: class counts.
- `urban_extract/*.json`: Urban-only geometry re-derived from the frozen K2 decode, each reproducing its frozen register.
- `scripts/`: `extract_urban_geometry.py` and `build_r9_1.py`.
- `INDEX.json`: hashes of every output.

**Rebuild:**

```
python research/R9_1_CHRIS_POST_FREEZE/scripts/extract_urban_geometry.py <k2_9f9d1179a5d2a663.pkl>
python research/R9_1_CHRIS_POST_FREEZE/scripts/build_r9_1.py <extracted CHRISTIANNP_FORENSIC_RERUN_2026_10_07 dir>
```

The christiannp dataset is not committed: it is an external donor dataset of 13 MB of raw dumps. It is identified by its ZIP and manifest hashes. The committed CSVs are the post-freeze comparison products.
