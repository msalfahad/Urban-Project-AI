# Pre-S4 hardening: footing rebar readiness and BOXED source exhaustion

**Baseline:** `445dd1d` (R9.1 accepted as the frozen donor-comparison baseline).

**Purpose:** make Accurate Footing Rebar (S4) safe to start.

**Scope of this round:**
- No S4 and no footing-rebar calculation engine.
- No geometry change: GB pairing, arcs, walls, slab barriers, raster and beam binding are untouched.
- No donor research, no AutoCAD / MCP, and no change to the PDF stack.

**Sources (read-only):**
- ST7757.dxf `9f9d1179…` and ST7757.pdf `74da1523…`;
- the frozen S1 footing registers;
- the frozen R4 visual capture.

## Production changes (guards and contract only)

| File | Change |
|---|---|
| `engine/source/footing_rebar_guard.py` (new) | **token parity gate:** `admit_token` / `admit_cells`, one route per token class, the three parsers re-run live, known-disagreement classes fail closed. **Conservation census:** `Census`, 9 terminals, blocked is never zero. **Occurrence terminals:** `occurrence_terminals`, which adds the outline side and count queries. **Header-position binding:** `header_binding`. **BOXED and release rules:** `boxed_part`, `footing_release`. No kg |
| `engine/source/accurate_boq_rebar.py` | S4 provenance contract: `S4_PROVENANCE_FIELDS`, `S4_BOUND_FIELDS`, `validate_s4_part`, `summarise_s4`. Opt-in; existing parts unchanged |
| `engine/source/comparison_scope.py` | version stamps: `STAMP_FIELDS`, `stamp`, `stamp_relation`, `compare_stamped` |
| `tests/structural_comparison_engine/rebar_product_registry.py` | the guard is declared an ACCURATE module (firewall) |

The three parsers (`schedule_grammar.parse_bar`, `structural_schedule.bar_spec`, `slab_rebar_binding.parse`) are **not** unified or changed.

## Deliverables

| # | File | Content |
|---|---|---|
| 01 | `01_FOOTING_TOKEN_PARITY_REGISTER.csv` | 67 tokens. **45 admitted:** 24 FT and 20 FTB count/diameter cell pairs, plus the p.14 `2Ø16`, which is parity-OK but ambiguous in applicability. **22 fail closed:** 11 BOXED pairs, FN empty, 10 TOP/BOT labels. Joined-form parity: all 44 schedule cell pairs give the same form through all three parsers |
| 02 | `02_FOOTING_ANNOTATION_CENSUS.csv` | 333 source items = 333 terminal items. PARSED_BOUND 226, NOT_REBAR 74, BLOCKED_SEMANTICS 14, PARSED_SOURCE_CONFLICT 12, PARSED_AMBIGUOUS 5, DUPLICATE_SOURCE 2. No blocked item carries a quantity |
| 03 | `03_BOXED_OCCURRENCES.csv` | 22 rows: 11 values, FN empty, 10 FTB layer labels |
| 04 | `04_BOXED_SOURCE_EXHAUSTION.md` | sources searched, schedule layout, details, diagnostics, hypotheses, the decision: **UNRESOLVED** |
| 05 | `05_S4_PROVENANCE_CONTRACT.md` | the minimum S4 record and the release / stamp rules |
| 06 | `06_S4_READINESS_MATRIX.csv` | 18 components: READY 10, READY_LOWER_BOUND 2, PROVISIONAL_ONLY 2, BLOCKED_COMPONENT 1 (BOXED), NOT_APPLICABLE 3 |
| 07 | `07_POST_S4_FROZEN_BACKLOG.md` | R9.1 lessons, frozen for after S4 |
| — | `PRE_S4_SUMMARY.json` | counts, table digest, block templates, header binding (22 / 22), BOXED diagnostics |
| — | `TEST_RUN.md` | test runs |
| — | `scripts/build_pre_s4.py` | deterministic builder; `python3 -I … <ST7757.dxf>` |
| — | `INDEX.json` | sha256 of every file above |

## Key findings

- **Parser disagreements affecting S4: none.**
  - Every footing bar token is a split count/diameter cell pair with one route (`bar_from_cells`).
  - The single-text forms of those pairs agree across all three parsers.
  - The known-disagreement classes (diameter at spacing, count at spacing, bar in a sentence) do not occur in the footing sources; the guard fails closed if S4 ever meets them.
- **Schedule binding:**
  - 22 / 22 (sub-)rows bind by drawn header; `W → L`, `H → W`, `DEPHT → H` is confirmed from geometry.
  - BOXED is a top-level column with no Ø glyph, and its block default is `3+-`.
  - FF has no sub-row rule in the DXF; its TOP/BOT labels align with their bar cells.
- **BOXED: UNRESOLVED after source exhaustion.**
  - The component exists (p.13 "Boxed bars.", header): SOURCE_EXPLICIT.
  - Its numbers are explained nowhere.
  - The second number rises with L (PROJECT_PATTERN_ONLY), and is not promoted.
- **FN changes from R3.** The empty BOXED cell was read as NOT_REQUIRED; it is now UNRESOLVED, and FN becomes REBAR_LOWER_BOUND until it is confirmed.
- **F / F10:** SOURCE_CONFLICT. Outline 1B1B holds tags F and F10, with hypotheses {2 × F, F10, drawn outline}. The occurrence is REBAR_BLOCKED. The conflict survives to the release state (FT-05).
- **F3:**
  - Two independent outlines, each with its own C3/F3 tag at the scheduled 160 × 140, so the plan count is 2.
  - Open owner question OQ-11 asks whether F3 is really tagged twice.
  - The query is carried as a question id only; no external count enters. Both F3 occurrences are OCCURRENCE_PROVISIONAL and can never be VERIFIED while the query is open (FT-06).
- **Bar direction:** "SHORT bars span W, counted along L" is SOURCE_DERIVED_HIGH_CONFIDENCE. Printed counts give equal spacing both ways only in that reading.

## PyMuPDF

- **Status:** `COMMERCIAL_ARCHITECTURE_ACTION_REQUIRED` (licence; R9-LIC-01).
- **Effect on S4:** none. S4 reads the DXF only.
- **This round:** the PDF stack was not modified. PDF pages were rendered read-only, outside the repository, for reading.
