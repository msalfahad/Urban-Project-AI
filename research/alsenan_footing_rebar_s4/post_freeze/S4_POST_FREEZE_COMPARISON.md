# S4 post-freeze comparison (footing rebar)

**Run:**

```
python3 -I research/alsenan_footing_rebar_s4/post_freeze_comparison.py <CHRISTIANNP_FORENSIC_RERUN dir>
```

The script first checks `S4_FREEZE_MANIFEST.json` and refuses to run if any frozen code, input or output hash has changed. The frozen engine stamp is `e3633af+code:0d11810b780ae8f8`; the S4 freeze commit is `50c546b`. No S4 output was changed after this comparison, and nothing in S4 was tuned.

**Outputs:**
- `S4_POST_FREEZE_COMPONENT_COMPARISON.csv`: one row per mark × component, with one class for each reference.
- `S4_POST_FREEZE_OCCURRENCE_COMPARISON.csv`: per-mark occurrence counts for S4, the freelancer, christiannp and old Urban.
- `S4_POST_FREEZE_SUMMARY.json`: totals, decompositions, class counts, and reference hashes.

## Headline

| Reference | Its footing figure | Relation to S4 known 3629.60 kg | Class |
|---|---|---|---|
| christiannp (13_rebar) | 3863.41 kg (BOXED excluded) | +233.81 kg: cover convention **+176.39** + count convention **+57.42** + rounding −0.006 | COVER_CONVENTION (40 rows) |
| old Urban R3 (FOOTING_REBAR_REGISTER_V3) | verified 3629.60 kg, provisional 149.45 kg | verified = S4 known **exactly**. Provisional: 93.89 kg is the +1 edge bar, which equals S4 BEST − LOW exactly. The other 55.56 kg is FF perimeter closure legs. | SAME / ASSUMED_COMPONENT |
| freelancer QS | 5.8 t lump, hard-typed. Covers footings + STB1–3 straps + perimeter ground beam, with no component or diameter split. | not comparable; no difference reported | SCOPE_DIFFERENCE + INCOMPLETE_REFERENCE |
| U-C4N | project net rebar 22.619 t, KNOWN_INCOMPLETE, no footing split | not comparable | INCOMPLETE_REFERENCE |

The christiannp figure is reproduced to 0.006 kg when S4's own frozen source facts are re-measured with christiannp's two conventions:

1. **Bar length = full footing dimension.** christiannp's assumption A05 uses no 2 × 70 mm soil-contact cover. S4 uses `COVER_AGAINST_SOIL_70MM` (claim P8-N22, cross-verified).
2. **Two-layer and FF counts = rate × full perpendicular dimension**, keeping fractional bars (for example "27.6 bars"). S4 uses `ceil(rate × (dimension − 2 × 70))` as the verified count and keeps the +1 edge bar for BEST only.

Neither convention is a source fact that S4 is missing; each is a measurement-convention choice. S4 is therefore **not** changed. The remaining christiannp difference sits entirely in components that both sides leave unquantified.

## Differences by class

| Class | Where | Cause | kg effect |
|---|---|---|---|
| COVER_CONVENTION | every FT / FTB / FF mesh component (40 rows) | full dimension vs span − 70 − 70 (plus the count convention on the 5 per-metre footings) | +233.81 (christiannp) |
| MISSING_COMPONENT | BOXED × 20 FT occurrences + the F / F10 outline | BOXED unquantified on every side (S4 Q-R3-6; christiannp EXCLUDED; old Urban BLOCKED) | unknown on every side |
| MISSING_COMPONENT | FF 2Ø16 (S4-Q1) | S4 blocks the printed label; christiannp has no row; old Urban blocked it ("length follows the pit walls") | unknown |
| ASSUMED_COMPONENT | FN BOXED (old Urban) | R3 read FN's empty BOXED cell as "not required" and released FN as VERIFIED_COMPLETE. S4 keeps it BLOCKED_UNQUANTIFIED (pre-S4 decision: an empty cell is not evidence of absence). | 0 kg; it is a release-state difference |
| ASSUMED_COMPONENT | FF PERIMETER_CLOSURE_LEGS (old Urban) | R3 booked 54–56 legs × 2 × 0.41 m as PROVISIONAL; S4 has no source for them | old +55.56 provisional |
| SCOPE_DIFFERENCE | FF LIFT_PIT_WALLS (old Urban) | old Urban carried the pit walls as a blocked FF component; S4 footing scope excludes walls | 0 / 0 |
| SOURCE_CONFLICT | F / F10 outline 1B1B | **S4:** one SOURCE_CONFLICT occurrence, BLOCKED. **christiannp:** F × 4, F10 × 0, so the outline carries no steel. **Old Urban:** two BLOCKED tag rows, F#1 (tag 0x10A5) and F10#19 (tag 0x168B), for the same outline. **Freelancer:** books it as F10. | 0 kg on S4 / christiannp / old Urban |
| OCCURRENCE_DIFFERENCE | F3 (freelancer only) | the reference counts 1; the plan has two outlines (166B / 166C) with two tags. F3 = 2 is SOURCE_VERIFIED (§0, `F3_AUTHORITY_DECISION.json`). | not quantified (lump) |
| SAME | 39 rows (christiannp) / 78 rows (old Urban) | identical, or not applicable / no occurrence on both sides | — |
| UNKNOWN / BAR_LENGTH_CONVENTION / INCOMPLETE_REFERENCE (component level) | — | none occurred | — |

## Occurrences

| Source | Count |
|---|---|
| S4 | 26 (25 established + 1 conflict) |
| christiannp | 25 (it drops the conflict outline) |
| old Urban R3 | 27 rows (25 established + 2 blocked tag rows for one outline) |
| freelancer | 25 (F3 × 1 instead of 2; books the conflict outline as F10 × 1) |

All agree on F7 = 0 occurrences: the schedule row has no plan outline.

## Conclusions

- S4 is a **source-derived lower bound** that agrees exactly with the previous Urban verified figure and with christiannp once two named conventions are applied. No unexplained (UNKNOWN) difference remains.
- The open items are the same on every side: BOXED (Q-R3-6), the F / F10 identity, the FF 2Ø16 length (S4-Q1) and the two-layer top-bar ends. They need engineering answers, not a re-tuned engine.
- Any correction to S4 needs a new issue, new source evidence, a new regression and a new version. Nothing here feeds back into S4.
