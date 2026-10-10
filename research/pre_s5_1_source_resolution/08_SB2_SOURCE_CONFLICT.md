# SB2: two schedule rows for one strap

| Evidence | Row A | Row B |
|---|---|---|
| SCHEDULE_ROW (SBT insert) | 1FBB | 2ABA |
| W x H (cm) | 80 x 50 | 100 x 50 |
| REBAR_VALUES TOP | 10Ø18 | 20Ø18 |
| REBAR_VALUES BOTTOM | 10Ø18 | 10Ø16 |
| STIRRUPS / m | 10Ø8 | 10Ø8 |

| Plan evidence (FP sheet) | Value |
|---|---|
| TAG | SB2, handle 1B12:sb2>v |
| LOCATION | foundation plan, between FOCC-1B19 (F6) and FOCC-1B07 (F11) |
| strap edges | 1B08, 1B09 |
| PLAN_DRAWN_WIDTH | 987.1 mm |
| PLAN_DRAWN_LENGTH | 5.11 m (drawn faces); clear between footing faces 1.829 m |

| Authority (decided separately) | State | Why |
|---|---|---|
| SECTION_AUTHORITY: width | SOURCE_CONFLICT | 80 vs 100 cm. The drawn 987 mm is recorded; the closer width does not adjudicate. |
| SECTION_AUTHORITY: depth | CANDIDATE_INVARIANT (50 cm) | identical in both rows |
| REBAR_AUTHORITY: TOP / BOTTOM | SOURCE_CONFLICT, BLOCKED | the rows give different bars |
| REBAR_AUTHORITY: stirrups | CANDIDATE_INVARIANT | 10Ø8/m in both rows: Ø and rate READY, count LOWER_BOUND (rate x clear length) |
| link path | BLOCKED | the width conflict and no link topology |

This is engineering question Q-S2 (11).
