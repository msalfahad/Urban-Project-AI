# S6 scope recommendation

**Decision: RESTRICTED GO.** S6 may compute kg only for the released components below, each as the state given here,
with the provenance template from `S6_PROVENANCE_TEMPLATES.json` (165 templates). Everything else stays blocked and
must appear in S6 as an unquantified component, never as zero and never as an allowance.

| Subfamily | Component | State | Rows |
|---|---|---|---|
| CONTINUOUS_BEAM | BOTTOM | READY_LOWER_BOUND | 14 |
| CONTINUOUS_BEAM | MID_SUPPORT_TOP | READY | 9 |
| CONTINUOUS_BEAM | STIRRUP_COUNT | READY_LOWER_BOUND | 12 |
| SIMPLE_BEAM | BOTTOM_MAIN | READY_LOWER_BOUND | 71 |
| SIMPLE_BEAM | STIRRUP_COUNT | READY_LOWER_BOUND | 71 |
| SIMPLE_BEAM | TOP_MAIN | READY_LOWER_BOUND | 71 |

## Rules S6 must keep

1. **S5 principle.** A VERIFIED straight run stays VERIFIED; while development / anchorage or hooks are blocked the
   complete bar is a LOWER_BOUND. Do not demote the straight portion and do not add a default anchorage.
2. **Straight runs** are support face to support face (simple beams) or the bound CB bar runs (clear span + support
   width + a bound extension). Never centreline, never min(clear, c/c), never a schedule span.
3. **MID support bars** are complete bars: 0.22 x Ln of each adjacent span from the face + the support width (Ln =
   axis-to-axis as the typical dimensions it; Q5 asks for confirmation).
4. **Stirrups**: count records only (ceil(rate x clear run), no +1). No stirrup mass until Q7 is answered.
5. **Never released**: CB top bars, hangers, side bars, development, hooks, curved ring beams, the cantilever,
   stair-qualified and planted-column spans, every SOURCE_CONFLICT / PROVISIONAL_ONLY / candidate binding, CB
   occurrences with span-count conflicts, untagged geometry, and slab rules (0.25L / 0.30L) applied to beams.
6. **Candidate invariance** decides ambiguous CB reading directions; nothing is chosen.
7. **Firewall**: freeze S6 before any comparison; no reference value enters production.

## What widens S6 later

Q1 (anchorage / hooks) completes 156 lower-bound longitudinal components; Q2 releases CB top bars and hangers;
Q6 side bars; Q7 stirrup mass; R1-R6 move candidates, conflicts and untagged geometry into scope.
