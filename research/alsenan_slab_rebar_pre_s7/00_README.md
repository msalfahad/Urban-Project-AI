# PRE-S7: elevated slab rebar readiness / source exhaustion

**Round:** `PRE-S7` · **Policy:** `ELEVATED_SLAB_REBAR_READINESS_V1` · **Baseline:** HEAD `44f693e` · **Built by** `build_pre_s7.py` (blind, byte-identical rebuild) · **No kg is calculated.**

S4 to D1.2 are unchanged: all nine freeze manifests were hash-checked before anything was read. S7 was not started.

## Scope

- Floors in scope: 1F_ROOF_SLAB, 2F_ROOF_SLAB, GF_ROOF_SLAB.
- Geometries: 76 (CLASSIFICATION_BLOCKED 11, EXCLUDED_SPECIAL_STRUCTURE 11, IN_SCOPE_S7 47, NOT_SLAB 4, VOID_OR_OPENING 3).
- In-scope slab panels: 47 (1F_ROOF_SLAB 14, 2F_ROOF_SLAB 5, GF_ROOF_SLAB 28); area 356.866 m².
- Excluded to the special-structures round (stairs, domes): 11. Classification blocked: SP-GF_ROOF_SLAB-21, SP-2F_ROOF_SLAB-01, SP-2F_ROOF_SLAB-02, HZ-GFRS-273, HZ-GFRS-2B1, HZ-GFRS-2B4, HZ-SFRS-38C, HZ-SFRS-390, HZ-SFRS-391, HZ-GFRS-54D, HZ-FFRS-5E0.

## What the source settles

- **L is the clear span.** The p.15 slab-on-beams detail labels L1 and L2 CLEAR SPAN, face to face.
- **The rules are measured from the support face:** 0.25 L1 (non-continuous), 0.30 max(L1, L2) (continuous), 50% of the bottom bars stop 0.125 L short of a continuous support, the balance runs through.
- **Thickness:** 160 mm default (p.8 note 18 + p.1 note); local T marks override (T 18 on two panels; T 16 marks confirm the default). No floor rule. No conflict.
- **Cover:** 25 mm is a minimum (note 22, D1.2): straight runs at 25 mm are maxima, never exact.
- **Temperature table:** no 160 / 180 row. Nothing is interpolated.

## What blocks S7

- 11 source conflicts (11_SOURCE_CONFLICTS.csv), 12 items expected and not located (12), 21 engineer questions (15).
- Every rate callout needs a count rule (first bar, edge bars): none is stated.
- Top bars over beams: plan note 2 says 5Ø10/m, 'one third of the span', both directions; p.15 says 0.25 L1 / 0.30 max(L1, L2). They disagree and the note does not define its span.
- Components: 440; S7 release candidates 0; conditional on owner decisions 242; blocked 198.

## Files

| File | Content |
|---|---|
| 01_SLAB_PANEL_CENSUS.csv | every slab-plan face and dense-hatch strip, one scope each |
| 02_THICKNESS_REGISTER.csv | local / floor / default ladder per slab face |
| 03_SLAB_REBAR_TOKENS.csv | every rebar notation on the slab sheets, one terminal state each |
| 04_COMPONENT_READINESS.csv | instantiated components, blockers, readiness (no kg) |
| 05_SUPPORT_REGISTER.csv | one row per support (shared edges counted once) |
| 06_SUPPORT_RULES.csv | the p.15 and plan-note rules with their gates |
| 07_BAR_RUN_REGISTER.csv | bottom runs (balance continuous) and top-support runs |
| 08_OPENING_REGISTER.csv | voids, shafts, opening strips, void labels |
| 09_TEMPERATURE_REBAR_REGISTER.csv | thickness vs the p.15 table (exact rows only) |
| 10_COUNT_RULE_REGISTER.csv | rate, distribution width and count rule kept apart |
| 11 / 12 / 15 | conflicts, expected-not-located, engineer questions |
| 13_PROVENANCE.jsonl | one line per record |
| 14_S7_RELEASE_CANDIDATES.csv | candidates and the decisions they wait for |
| PRE_S7_SUMMARY.json | counts, gates, flags |
| source_search_inputs/PRE_S7_VISUAL_READING.json | p.15 / pp.4-6 visual reading (render hashes only) |
