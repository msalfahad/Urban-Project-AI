# S4.1 CHANGELOG: footing rebar delta release over frozen S4

**Round:** `S4.1` · **Policy:** `FOOTING_REBAR_S4_1_DELTA_V1` · **Frozen baseline:** `research/alsenan_footing_rebar_s4/S4_FREEZE_MANIFEST.json` (sha `0d63015a1995`, stamp `e3633af+code:0d11810b780ae8f8`)
**Built by** `build_footing_rebar_s4_1.py` (blind, byte-identical rebuild) · **Graphic policy:** `GRAPHIC_EVIDENCE_POLICY_V1`

S4 is unchanged. Every S4 code, input and output hash was checked before this round read anything, and no S4 file
was written. This file is BASELINE + DELTA. It does not rewrite the historical S4 result.

## Headline

| | kg |
|---|---|
| Frozen S4 known (verified + lower bound) | 3629.5995 |
| S4.1 delta known | 0.0000 |
| **S4.1 known** | **3629.5995** |
| of which complete bars VERIFIED | 0.0000 (was 887.0933) |
| of which complete bars LOWER_BOUND | 3629.5995 |
| of which known straight segments of single-layer bars (former VERIFIED) | 887.0933 |

The delta is **0 kg** because no bar portion found in the issued set carries a dimension or a deterministic
project-source endpoint. The semantic corrections below are still real. A zero delta hides none of them.

## What changed (state and model; no kg)

1. **Single-layer long bars (20 components): VERIFIED → KNOWN_STRAIGHT_SEGMENT, COMPLETE_BAR = LOWER_BOUND.**
   - p.13 draws "Long bars" as one U (E-PDF-01, both details). The model is now STRAIGHT_RUN + UPTURN_LEG_1/2 +
     END_HOOK_1/2 + BEND_ARC_1/2.
   - The frozen straight length stays known steel. It was not subtracted.
   - **Upturn legs:** `GRAPHIC_EXPLICIT_SHAPE_ONLY`, `SHAPE_FOUND_LENGTH_BLOCKED`. A derivation from footing depth D,
     the 70 mm cover and the bar levels was attempted. Rule B fails because the leg top is a free end, drawn
     7.7 / 5.5 pt under the boxed bar's top run (shallow / deep detail). That point lies on no cover line and
     no dimensioned level, and the boxed bar's own level depends on its unlocated diameter. The plotted length was
     not used.
   - **45° hooks:** SHAPE_FOUND + LENGTH_BLOCKED.
   - **Bend arcs:** SHAPE_FOUND (shared vertex) + radius blocked.
2. **Single-layer short bars (20 components): VERIFIED → KNOWN_STRAIGHT_SEGMENT, COMPLETE_BAR = LOWER_BOUND.**
   - They are drawn only as dots. The U shape is NOT copied onto them.
   - END_TREATMENT_1/2 are blocked (no graphic evidence).
3. **Two-layer bottom bars (10 components): FACET_ADDED.** The "straight" basis is withdrawn, so these carry
   END_TREATMENT_NOT_ESTABLISHED. They stay LOWER_BOUND.
4. **BOXED (20 components): FACET_ADDED.**
   - 16 have EXISTENCE = SOURCE_FOUND_EXPLICIT (printed cell). For the 4 FN rows, existence is
     still SOURCE_EXPECTED_NOT_LOCATED (blank cell).
   - SHAPE = SOURCE_FOUND_EXPLICIT (inverted U).
   - The meaning of 3+n, the diameter and the count are not located, so BOXED_KG = BLOCKED_UNQUANTIFIED. No
     external diameter was used and "3+4" was not interpreted.
5. **FF "2 Ø16": OWNERSHIP_TRANSFER.**
   - FOOTING_CANDIDATE → LIFT_PIT / SPECIAL_STRUCTURE (future S8); see `S4_1_OWNERSHIP_TRANSFERS.csv`.
   - The leaders end on bars inside the cut pit-wall band, so these are wall-base bars, not footing reinforcement.
   - No kg.

Carried unchanged:
- F / F10 (pending the engineer, brief §20);
- the two-layer top bars (already END_TREATMENT_NOT_ESTABLISHED);
- 73 NOT_APPLICABLE components.

## Counts

- Delta rows: 337, covering every one of the 157 frozen components.
- Components by S4.1 state: BLOCKED_UNQUANTIFIED 23, LOWER_BOUND 60, NOT_APPLICABLE 73, TRANSFERRED_OUT 1.
- Long-bar portions by state: BEND_ARC_1:SHAPE_FOUND_LENGTH_BLOCKED 20, BEND_ARC_2:SHAPE_FOUND_LENGTH_BLOCKED 20, END_HOOK_1:SHAPE_FOUND_LENGTH_BLOCKED 20, END_HOOK_2:SHAPE_FOUND_LENGTH_BLOCKED 20, END_TREATMENT_1:BLOCKED_UNQUANTIFIED 5, END_TREATMENT_2:BLOCKED_UNQUANTIFIED 5, STRAIGHT_RUN:KNOWN_STRAIGHT_SEGMENT 25, UPTURN_LEG_1:SHAPE_FOUND_LENGTH_BLOCKED 20, UPTURN_LEG_2:SHAPE_FOUND_LENGTH_BLOCKED 20.
- Remaining BOXED blocked: 21
  - 16 existence explicit + shape found;
  - 4 FN existence not located;
  - 1 F / F10 pending.
- Transferred to S8: 1.
- Unresolved register: 224 rows (44 carried from S4, 180 new portion rows).

## Files

| File | Content |
|---|---|
| `S4_1_DELTA_COMPONENTS.csv` | one row per frozen component (or per portion of a re-modelled bar), with all brief §2 fields |
| `S4_1_RELEASE_SUMMARY.json` | baseline, delta and new totals, states, conservation, policy, flags |
| `S4_1_OWNERSHIP_TRANSFERS.csv` | FF wall-base bars → LIFT_PIT / SPECIAL_STRUCTURE |
| `S4_1_UNRESOLVED.csv` | carried S4 unresolved rows plus the new blocked portions |
| `S4_1_PROVENANCE.jsonl` | per delta row: frozen row, evidence ids, page / handles, graphic class, derivation attempt |
| `S4_1_FREEZE_MANIFEST.json` | S4.1 frozen before S6.1 |
