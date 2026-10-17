# Detail precedence: "Less than 2.5m" vs "Less than 5m", and the 2.5 m stirrup

## Precedence (§8)

**The literal titles (p.13):**
- P13-GB-LT5M: "Less than 5m length (1:20) without concentrated load"
- P13-GB-LT2_5M: "Less than 2.5m length (1:20)"

A span shorter than 2.5 m meets both conditions literally.

**Sources searched for an order between them:**
- the p.13 titles and their layout. The LT2_5M section is drawn under GT5M; LT5M stands apart. Nothing groups LT2_5M
  as a subset of LT5M or a range "2.5 to 5";
- the p.8 general notes;
- the ST7757.dxf texts. The details are not in the DXF; there are only plan / schedule texts.

None states an order.

| RULE_PRECEDENCE_SOURCE | Spans |
|---|---|
| SPECIFICITY_CANDIDATE | 23 |

- "The narrower condition wins" is a SPECIFICITY_CANDIDATE, not a source.
- Both details are preserved as candidates, and a component releases only if it is identical in both.

| Facet | LT2_5M | LT5M | Same? |
|---|---|---|---|
| top | (3, 14) | (3, 14) | True |
| lower rows | [(3, 14), (3, 14)] | [(3, 14), (3, 14)] | True |
| section | 30 x 300 (AI_VISUAL_TRANSCRIPTION) | 30 x 400 | no |
| stirrup | none printed | (8, 150) | no |

## The 2.5 m stirrup (§9)

**Sources exhausted:**
- **The P13_GB_LT2_5M crop:** a closed link with a hook is drawn; no size or spacing is printed.
- **The R4 claim register:** "no stirrup callout printed".
- **The S1 project rule register:**
  - P9-COL-TIES is for columns only;
  - P11-12-CB-TYPICAL is for continuous beams (first stirrup 7.5 cm);
  - no ground-beam link rule exists.
- **The p.8 notes:** nothing on links.

**Result:** STIRRUP = **BLOCKED_COMPONENT** wherever the 2.5 m section is a candidate. Ø8/150 from the 5 m sections
is not inherited. Longitudinal bars still release (identical 3Ø14).

| Span | Clear basis | Centreline basis | Applicability | Longitudinal | Stirrup |
|---|---|---|---|---|---|
| 107-7CE-1 | ['P13-GB-LT2_5M', 'P13-GB-LT5M'] | ['P13-GB-LT2_5M', 'P13-GB-LT5M'] | PROJECT_GENERAL_DETAIL | READY_LOWER_BOUND | READY |
| 10B-7D1-1 | ['P13-GB-LT2_5M', 'P13-GB-LT5M'] | None | CANDIDATE_DETAIL | BLOCKED_COMPONENT | BLOCKED_COMPONENT |
| 10B-7D1-2 | ['P13-GB-LT2_5M', 'P13-GB-LT5M'] | ['P13-GB-LT5M'] | PROJECT_GENERAL_DETAIL | READY_LOWER_BOUND | READY |
| 114-115-7DF-2 | ['P13-GB-LT2_5M', 'P13-GB-LT5M'] | ['P13-GB-LT2_5M', 'P13-GB-LT5M'] | PROJECT_GENERAL_DETAIL | READY_LOWER_BOUND | READY |
| 137-138-1 | ['P13-GB-LT2_5M', 'P13-GB-LT5M'] | ['P13-GB-LT5M'] | PROJECT_GENERAL_DETAIL | READY_LOWER_BOUND | READY |
| 13C-7D9-1 | ['P13-GB-LT2_5M', 'P13-GB-LT5M'] | ['P13-GB-LT2_5M', 'P13-GB-LT5M'] | CANDIDATE_DETAIL | READY_LOWER_BOUND | BLOCKED_COMPONENT |
| 141-7DA-1 | ['P13-GB-LT2_5M', 'P13-GB-LT5M'] | ['P13-GB-LT2_5M', 'P13-GB-LT5M'] | CANDIDATE_DETAIL | READY_LOWER_BOUND | BLOCKED_COMPONENT |
| 142-7D8-1 | ['P13-GB-LT2_5M', 'P13-GB-LT5M'] | ['P13-GB-LT5M'] | CANDIDATE_DETAIL | READY_LOWER_BOUND | BLOCKED_COMPONENT |
| 145-7CA-1 | ['P13-GB-LT2_5M', 'P13-GB-LT5M'] | ['P13-GB-LT2_5M', 'P13-GB-LT5M'] | CANDIDATE_DETAIL | BLOCKED_COMPONENT | BLOCKED_COMPONENT |
| 145-7CA-2 | ['P13-GB-LT2_5M', 'P13-GB-LT5M'] | ['P13-GB-LT5M'] | SOURCE_CONFLICT | BLOCKED_COMPONENT | BLOCKED_COMPONENT |
| 15C-7CC-1 | ['P13-GB-LT2_5M', 'P13-GB-LT5M'] | ['P13-GB-LT5M'] | CANDIDATE_DETAIL | READY_LOWER_BOUND | BLOCKED_COMPONENT |
| 15D-7C8-1 | ['P13-GB-LT2_5M', 'P13-GB-LT5M'] | ['P13-GB-LT5M'] | CANDIDATE_DETAIL | READY_LOWER_BOUND | BLOCKED_COMPONENT |
| 16F-7FF-1 | ['P13-GB-LT2_5M', 'P13-GB-LT5M'] | ['P13-GB-LT2_5M', 'P13-GB-LT5M'] | CANDIDATE_DETAIL | READY_LOWER_BOUND | BLOCKED_COMPONENT |
| 177-7CD-2 | ['P13-GB-LT2_5M', 'P13-GB-LT5M'] | ['P13-GB-LT2_5M', 'P13-GB-LT5M'] | CANDIDATE_DETAIL | BLOCKED_COMPONENT | BLOCKED_COMPONENT |
| 17B-7E5-1 | ['P13-GB-LT2_5M', 'P13-GB-LT5M'] | ['P13-GB-LT2_5M', 'P13-GB-LT5M'] | CANDIDATE_DETAIL | READY_LOWER_BOUND | BLOCKED_COMPONENT |
| 17C-7E3-1 | ['P13-GB-LT2_5M', 'P13-GB-LT5M'] | ['P13-GB-LT5M'] | CANDIDATE_DETAIL | READY_LOWER_BOUND | BLOCKED_COMPONENT |
| 180-181-1 | ['P13-GB-LT2_5M', 'P13-GB-LT5M'] | ['P13-GB-LT2_5M', 'P13-GB-LT5M'] | CANDIDATE_DETAIL | BLOCKED_COMPONENT | BLOCKED_COMPONENT |
| 180D-180E-1 | ['P13-GB-LT2_5M', 'P13-GB-LT5M'] | ['P13-GB-LT2_5M', 'P13-GB-LT5M'] | CANDIDATE_DETAIL | BLOCKED_COMPONENT | BLOCKED_COMPONENT |
| 1811-1812-1 | ['P13-GB-LT2_5M', 'P13-GB-LT5M'] | None | CANDIDATE_DETAIL | BLOCKED_COMPONENT | BLOCKED_COMPONENT |
| 182-183-1 | ['P13-GB-LT2_5M', 'P13-GB-LT5M'] | ['P13-GB-LT5M'] | CANDIDATE_DETAIL | BLOCKED_COMPONENT | BLOCKED_COMPONENT |
| 185-7C7-1 | ['P13-GB-LT2_5M', 'P13-GB-LT5M'] | ['P13-GB-LT2_5M', 'P13-GB-LT5M'] | PROJECT_GENERAL_DETAIL | READY_LOWER_BOUND | READY |
| 7D0-FC-4 | ['P13-GB-LT2_5M', 'P13-GB-LT5M'] | ['P13-GB-LT2_5M', 'P13-GB-LT5M'] | PROJECT_GENERAL_DETAIL | READY_LOWER_BOUND | READY |
| A-139-13A-1 | ['P13-GB-LT2_5M', 'P13-GB-LT5M'] | ['P13-GB-LT2_5M', 'P13-GB-LT5M'] | PROJECT_GENERAL_DETAIL | READY_LOWER_BOUND | READY |
