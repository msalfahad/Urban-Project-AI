# Engineering questions (final, pre-S5.1)

These are only questions that ST7757, P7757, the registers, the geometry and the notes cannot answer.

| # | Class | Question | Members affected | Sources exhausted |
|---|---|---|---|---|
| Q-L1 | SOURCE_EXHAUSTED_ENGINEER_REQUIRED | **Concentrated load.** Does a ground beam ending on another ground beam mid-span (or the reception stair start) count as a 'concentrated load' for the p.13 sections titled 'without concentrated load'? | 31 spans UNKNOWN; 15 interior spans blocked by it: 109-7CB-1, 13E-7D6-1, 13F-7D3-1, 140-7D7-1, 15E-15F-1, 175-7DE-1, 176-7E6-1, 177-7CD-1, 17D-7E4-1, 17E-17F-1, 184-7CF-1, 184-7CF-3 (+3) | p.13 titles, GBP texts / symbols, S1 column chains (no planted column on a GB), junction geometry |
| Q-D1 | SOURCE_EXHAUSTED_ENGINEER_REQUIRED | **Exterior ground-beam depth.** The section draws GF slab level to outer natural ground (±0.00). The floor build-up is not printed, so D <= 1.00 m (main block) / <= 0.30 m (annex at +0.30). What is the depth (or the build-up)? The annex bound cannot hold the drawn section. | 30 exterior candidates ({'BOUNDED': 26, 'UNRESOLVED': 4}); annex: 10B-7D1-1, 10B-7D1-2, 136-7D5-1, 137-138-1, 13D-7D2-1, 7D4-F8-1, 7D4-F8-2, A-139-13A-1 | p.13 exterior crop, A-A / B-B section levels, P7757 GF level marks, S1 level register |
| Q-B1 | SOURCE_EXHAUSTED_ENGINEER_REQUIRED | **Length basis of the p.13 titles:** clear span between support faces, or centreline? | 11 spans change detail: 10B-7D1-1, 10B-7D1-2, 137-138-1, 142-7D8-1, 145-7CA-2, 15C-7CC-1, 15D-7C8-1, 17C-7E3-1, 1811-1812-1, 182-183-1, A-157-158-1 | p.13 titles, GBP dimensions (axis chains only), CB figure (Ln and L), lintel schedule |
| Q-N1 | SOURCE_EXHAUSTED_ENGINEER_REQUIRED | **Below 2.5 m both 'Less than 2.5m' and 'Less than 5m' hold.** Which governs, and what are the 2.5 m section's link size and spacing? | 23 spans: longitudinal released (identical), stirrups blocked | p.13 crop LT2_5M (no callout), R4 claims, S1 / R4 rule registers |
| Q-S2 | SOURCE_EXHAUSTED_ENGINEER_REQUIRED | **SB2 governing schedule row:** 80x50 (10Ø18 / 10Ø18) or 100x50 (20Ø18 / 10Ø16)? | SB2 longitudinal bars and link path | SBT inserts 1FBB / 2ABA, FP plan (drawn width 987) |
| Q-E1 | SOURCE_EXHAUSTED_ENGINEER_REQUIRED | **Partly exterior / mixed spans.** Which section applies to a span whose wall above is partly exterior, or which sits on the slab edge with no wall? | 8 spans: 109-7CB-1, 10B-7D1-1, 114-115-7DF-1, 145-7CA-1, 145-7CA-2, 178-7DB-1, 180D-180E-1, 1811-1812-1 | P7757 GF walls, S1 slab panels |
| Q-T1 | SOURCE_EXHAUSTED_ENGINEER_REQUIRED | **Link topology and hooks.** Legs, hook angle and extension of the ground-beam and strap links. The strap schedule gives Ø and count per metre only. | every stirrup core path; all hooks | p.13 sections, SBT, R4 HOOKS_AND_BENDS = NO_PROJECT_SOURCE |
| Q-A1 | GENERIC_CODE_QUESTION | **Development / anchorage** of ground-beam bars into columns, beams and footings, and of strap bars into footings. The p.8 70Ø / 40Ø note is for starters only. A code value needs the project's code and grades (a project decision). | all DEVELOPMENT_INTO_SUPPORT components | P8-N09 claim, R4 rule DEVELOPMENT_STARTER_70D_40D |
| Q-G1 | PROJECT_DECISION_REQUIRED | **Bar run where the drawn band and the support faces disagree.** A column narrower than the beam, oblique and arc-trimmed ends: should bars be measured to the support face plane, and the concrete piece corrected? | 7 spans: 136-7D5-1, 177-7CD-2, 17E-17F-1, 180-181-1, 182-183-1, 7E0-FD-1, A-157-158-1 | GBP geometry (no source states a method) |
| Q-F1 | SOURCE_EXHAUSTED_ENGINEER_REQUIRED | **1811-1812 east end** lies on the plot-boundary line with no column or footing. What supports it? | 1 span (bar run unresolved) | GBP S-BOUN, S-COL.BON, FP footings |
| Q-X1 | SOURCE_EXHAUSTED_ENGINEER_REQUIRED | **Meaning of the two '******' marks** on the GBP sheet (S-TEXT, 300 mm, no legend). | spans near them are load-UNKNOWN | GBP texts, all ST7757 '*' texts |

## Classified NOT_REQUIRED (resolved this round)

| Item | Resolution |
|---|---|
| Exterior / interior of the 19 proxy-disagreement spans | 16 resolved by the architectural overlay |
| Outer normal ground level | ±0.00 (sections A-A, B-B) |
| Free ends | 7/7 classified ({'FOOTING': 2, 'COLUMN': 4, 'BOUNDARY': 1}); one boundary end remains (Q-F1) |
| Planted columns on ground beams | none (S1 chains) |
| SB2 stirrups | identical in both rows: candidate-invariant |
| Beam provenance identity | generic ELEMENT_* contract |
