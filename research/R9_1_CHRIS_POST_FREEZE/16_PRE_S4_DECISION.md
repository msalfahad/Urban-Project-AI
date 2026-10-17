# 16 Pre-S4 reassessment (S4 = accurate footing rebar)

This reassessment is conservative: no large refactor, and no production change in this round. The evidence for each rating is in this package. Ratings that change from R9 (`2c00561`, `R9_GAP_STUDY.md` §14) say so.

## What the christiannp rerun changes about S4 inputs

**The footing objects are already settled.**
- 26 / 26 outlines are identical by handle; 25 occurrences have the same mark and schedule size (08).
- The one conflict, F / F10 on outline 1B1B, is a SOURCE_CONFLICT in both systems.
- christiannp adds no footing Urban lacks, and no route Urban needs before S4.

**The footing rebar tokens are not where the parsers disagree** (11). Corpus: 507 christiannp evidence rows, 86 distinct raw tokens.
- **Footing tokens:** every FT / FTB count/diameter cell pair (`8 / 12`, `13 / 12`, `24 / 14` …) has one consumer route in Urban, `schedule_grammar.bar_from_cells`, and it parses all of them.
- **Where the three Urban parsers do disagree:** 6 patterns, 52 rows, all of them notes or detail texts:
  - the column-tie note `* ST. OF COLUMN- 6%%C8/m`;
  - `%%c10/20cm`, `%%c12/20cm`, `%%C12MM/15cm` (diameter at spacing: only `parse_bar` reads it);
  - `2%%c14/20cm` (`bar_spec` drops the spacing);
  - `T=10cm / 5%%c10/m E.W.` (only `bar_spec` reads it inside the sentence).
- **What blocks footing rebar is the meaning of BOXED `3+4` / `3+5` / `3+6` / `3+8`** (11 rows). No parser can fix that; it needs a source or an owner claim (U04 in christiannp, `BLOCKED_SEMANTICS` in S1).

**christiannp's own footing kg is not a target.** Its 3,863.5 kg of footing components uses bar length = footing dimension (A05) and FT mesh = bottom (A07). It is component evidence only.

## Ratings

| Item | R9 rating | R9.1 rating | Why (evidence) |
|---|---|---|---|
| A. One canonical bar grammar | REQUIRED_BEFORE_S4 (P0) | **HELPFUL_BEFORE_S4**, narrowed: a parser-parity test over the S4 token corpus is REQUIRED; full grammar unification moves AFTER_S4 | the empirical corpus shows no footing token on which the parsers disagree; the 6 disagreeing patterns are slab, column-tie and detail notes outside S4. A parity test (11 corpus → expected normalised form → every applicable parser) fails if S4 starts reading a token class the parsers split on |
| B. Full annotation / token census with conservation | REQUIRED_BEFORE_S4 | **REQUIRED_BEFORE_S4** (for the footing schedule and footing plan only) | christiannp's REBAR_EVIDENCE shows the value of one table where every token has handle → component → terminal state (INCLUDED / EXCLUDED + why). S4 must be able to prove that every FT / FTB ATTRIB cell, including BOXED and blank cells, ends in exactly one terminal state |
| C. Structural provenance receipt | REQUIRED_BEFORE_S4 | **REQUIRED_BEFORE_S4** (S4 output format) | unchanged. This round needed `scripts/extract_urban_geometry.py` just to recover handles and coordinates Urban had computed but not stored. S4 lines must carry insert / attrib handles, the drawing sha and the rule id from the start |
| D. Convention ID on quantity records | AFTER_S4 (emit from the start) | **HELPFUL_BEFORE_S4** (S4 emits a CONVENTION_ID field; the profile machinery stays AFTER_S4) | this round's dominant difference class is SAME_GEOMETRY_DIFFERENT_CONVENTION: GB column split, strap clear length, column storey rule, wall opening split, beam full or below-slab depth. Footing rebar has its own conventions (cover, lap, hook source); stamping them costs nothing now and is expensive later |
| E. Drawing hash on every record | REQUIRED (part of C) | **REQUIRED_BEFORE_S4** (part of C) | both systems measured the same sha; that check was possible only because christiannp hashed its inputs and Urban decodes by sha |
| F. Engine / version stamp | AFTER_S4 (S4 emits it) | **HELPFUL_BEFORE_S4** (one field) | comparisons in this round carry `URBAN_ENGINE_COMMIT` / `CHRIS_MANIFEST_SHA256` / `CALCULATION_ROUND`; S4 should write the same stamp |

## Does any new christiannp technique have to come before S4?

**No.** Every christiannp technique that beats Urban affects other trades and can wait until after S4:
- multi-partner GB pairing (1.000 m);
- the arc angular overlap (0.718 m);
- S-OPENING edges as slab barriers (the GF void face);
- S-BW pit boxes in the ground slab (lift pit);
- width-agnostic wall pairing (2 pairs, 2.485 m);
- an orientation + width tie-break for 6 AMBIGUOUS beam tags.

Two items are worth doing before S4 because they are cheap and S4-adjacent. Both are tests, not production changes:
1. **The footing rejected-candidate log as a regression fixture.** christiannp logs 34 rejected tag → outline candidates. A fixture with two footing tags in one outline and one tag without geometry (17, F-01 / F-02) makes S4 fail closed on the F / F10 case.
2. **The header-position ATTRIB binding check (MD02) as a test on the FT block.** The FT tags W / H / DEPHT print under the L / W / H headers. S4 reads the same block, so a test that derives the binding from header geometry and compares it with `rules_s1`'s fixed table protects S4 from a silent column swap.

## PyMuPDF

This rating is unchanged from R9-LIC-01. It is a separate commercial / licence decision and does **not** block S4, which reads DXF only. This round made no change to the PDF stack.

## Exact pre-S4 list

1. **S4 token-parity test.** Build the FT / FTB / footing-plan token corpus from S1. For each token, assert the expected normalised form through every applicable Urban parser. Fail on any split.
2. **Footing annotation census with conservation.** Every FT / FTB ATTRIB cell and every footing-plan tag ends in exactly one terminal state. BOXED stays BLOCKED_SEMANTICS.
3. **S4 receipt fields:** insert / attrib handles, drawing sha256, rule id, CONVENTION_ID and the engine stamp on every S4 line.
4. **Fixtures:** two tags in one outline, tag without outline, outline without tag, and FT header binding.
