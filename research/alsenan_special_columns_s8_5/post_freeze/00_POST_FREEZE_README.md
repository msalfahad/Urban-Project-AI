# S8.5 post-freeze comparison

Run after the freeze (`17_S8_5_FREEZE_MANIFEST.json` verified before and after, unchanged). Nothing here changes a frozen quantity.

## Special-column components at equal scope

- S8.5 adds **0 kg** and **0 m3**. The special extras already counted are S3.1's 4Ø16 at the two turns (25.284 kg) and S6.1's 548 beam extra (12.009877 kg).
- **V3b has none of them** (0 kg): no turn extra, spiral, planted-column extra or starter. That is a SCOPE difference. V3b's ordinary bars and 40Ø laps for C8 / C9 / C11 equal S3.1's at type level. On the dead column, V3b calls the 0.64 m a floor-splice lap where S3.1 calls it a top anchorage: same kg, LABEL_ONLY.
- **V3b has no planted column at all**: MISSED_OBJECT. S3.1 holds their 268.838 kg of ordinary steel.
- **PRE-S8**: no special-column concrete (agrees with S8.5). Its ownership claims would have re-counted S3.1 / S6.1 roles: OWNERSHIP_CLAIM, corrected by S8.5.
- **Freelancer**: objects only, no special-column steel.
  - It also counts each planted column in the storey below its slab (STOREY_CONVENTION).
  - It splits the 31F turned column into a stopped column and a planted one (SEGMENTATION).
  - C9 / C11 match exactly.
  - Its whole-column counts per storey (33 vs 30 at GF, 21 vs 20 at 1F) are exactly those storey shifts.

## Classes

- LABEL_ONLY: 1
- MISSED_OBJECT: 1
- NOT_COMPARABLE: 2
- NO_DIFFERENCE: 15
- OWNERSHIP_CLAIM: 6
- SCOPE: 6
- SEGMENTATION: 2
- STOREY_CONVENTION: 5

## Outputs

- `01_POST_FREEZE_COMPARISON.csv`
- `02_OBJECT_AND_STOREY_CROSSWALK.csv`
- `03_POST_FREEZE_SUMMARY.json`
- `00_POST_FREEZE_README.md`
