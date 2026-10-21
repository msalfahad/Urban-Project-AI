# PRE-S7.1 / AD2: slab QTO authority / readiness resolution

**Round:** `PRE-S7.1` · **Decisions:** `AD2` (17) · **Policy:** `AD2_SLAB_QTO_AUTHORITY_V1` · **Baseline:** HEAD `9f89ab6` · built by `build_pre_s7_1.py` (blind, byte-identical rebuild) · **No kg, no bar-length total, S7 not started.**

A delta over frozen PRE-S7. PRE-S7 is not edited: its freeze manifest and the nine before it (S4 ... D1.2) were hash-checked before anything was read. Every PRE-S7 component terminates exactly once here.

## Lanes

- `SOURCE_DERIVED_PHYSICAL`: the source gives count, extent and role.
- `PROJECT_BASIS_QTO`: the source gives specification / rate / role; Urban measures with a declared rule (rate density N x W unrounded, the 0.5 / 0.5 curtailment density, 1/3 x local clear span from the support face, local bar lines). Never VERIFIED_PHYSICAL or AS_BUILT.
- `BLOCKED_UNQUANTIFIED`: the bar, its applicability, extent or classification is not established.

## Result

- PRE-S7: 0 release candidates, 242 conditional on owner decisions, 198 blocked.
- PRE-S7.1 components: BLOCKED 113, RELEASED_ALL 38, RELEASED_PARTIAL 271, TRANSFERRED_S8 18 (+ 42 new blocked components). 309 PRE-S7 components release quantity.
- Released items: 476 (PROJECT_BASIS_QTO 476); source-derived counts released with blocked lengths: 5. Blocked items: 687.
- Rate components unlocked 309 / 432; 50% components unlocked 140 / 142.
- Top bars over beams: plan note 2 and the p.15 top bars are one physical family (p.15 defers size and spacing to the plan). The floor plan note governs; p.15's 0.25 L1 / 0.30 max L / 'extend 50%' are OVERRIDDEN_PROJECT_SOURCE. The extent is the Urban rule 1/3 x local clear span from the support face (URBAN_OWNER_MEASUREMENT_RULE). The bound '/Top' callout overrides note 2 at its own support.
- Mismatched continuous supports split left / right: 31 supports (32 panel pairs); continuous supports with a released one-run crossing: 24.
- Irregular panels recovered 16 / 16 (local bar lines); sunken panels recovered 6 / 6 (mesh kept, step extras blocked).
- Temperature components blocked: 94 (160 mm, no table row); they block nothing else.
- S8 transfers: 60 records (water tank, light well, special-structure sides of supports).
- Topology corrections found by geometry (the face beyond each bar line, not the S1 edge neighbour): 8 supports (09_REMAINING_CONFLICTS.csv, G-rows).
- Remaining true source conflicts: C-01 PANEL_VOID_CONFLICT, C-03 MULTIPLE_CANDIDATE_BINDINGS, C-04 COUNT_NOTATION_CONFLICT, C-06 COVER_DIMENSION_BINDING, C-09 TOP_BAR_BINDING.

## Files

| File | Content |
|---|---|
| 01_AD2_DECISIONS.json | the 17 owner decisions and the two Urban rules |
| 02_OWNERSHIP_TRANSFERS.csv | S7 -> S8 transfers (panels, tokens, marks, components, support sides) |
| 03_RATE_QTO_REGISTER.csv | every rate-based item: N, fraction, W, N x W (unrounded), BBS count unresolved |
| 04_50_PERCENT_CURTAILMENT_REGISTER.csv | 0.5 / 0.5 density split per family |
| 05_TOP_RULE_IDENTITY.csv | bar-role identity, precedence, the Urban extent rule, the local override |
| 06_SUPPORT_MISMATCH_SPLITS.csv | left / right runs to the face; transitions blocked |
| 07_LOCAL_BAR_STRIPS.csv | local bar-line strips per panel and direction, with what lies beyond each end |
| 08_UPDATED_COMPONENT_READINESS.csv | every PRE-S7 component (+ new blocked components), one state each |
| 09_REMAINING_CONFLICTS.csv | PRE-S7 conflicts re-evaluated + topology corrections by geometry |
| 10_REMAINING_BLOCKERS.csv | blocked items with their question |
| 11_S7_RELEASE_CANDIDATES.csv | released items: lane, density, width, equivalent bars, mean local run |
| 12_PROVENANCE.jsonl | one line per record |
| PRE_S7_1_SUMMARY.json | counts, gates, flags |
