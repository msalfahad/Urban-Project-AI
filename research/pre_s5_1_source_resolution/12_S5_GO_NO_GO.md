# S5 GO / NO-GO

## Decision: **GO for a restricted S5**; NO-GO for a complete ground-system S5.

### GO: what S5 may quantify (each part LOWER_BOUND or VERIFIED, with the generic provenance)

| Scope | Occurrences | State |
|---|---|---|
| GB longitudinal TOP / BOTTOM_ROW_1 / BOTTOM_ROW_2, straight run = BAR_STRAIGHT_RUN_LOWER_BOUND | 31 spans | LOWER_BOUND (development blocked) |
| GB stirrup count | 25 spans | count LOWER_BOUND (no kg: the link path is not established) |
| Strap longitudinal (SB1, SB3) | 2 | LOWER_BOUND |
| Strap stirrup count (SB1, SB2, SB3) | 3 | count LOWER_BOUND (no kg) |

### NO-GO: what must stay blocked

- GB longitudinal bars of 28 spans:
  - BAR_RUN_LENGTH_GEOMETRY_CONFLICT: 6
  - CANDIDATE_DETAILS_DISAGREE (exterior authority not verified / length basis): 7
  - CONCENTRATED_LOAD_UNRESOLVED (Q-L1): 15
- Side bars of every exterior span: the depth is bounded above only (Q-D1).
- Every stirrup kg: no verified link path (Q-T1); the 2.5 m section has no callout (Q-N1).
- Hooks, end treatment and development everywhere (Q-T1, Q-A1).
- SB2 longitudinal bars (Q-S2).

### Conditions for S5

1. S5 consumes 05 / 10 (no re-parse) and uses `rebar_provenance` / `ground_system_provenance` (ELEMENT_*).
2. Freeze before any comparison.
3. Release only where `MAY_RELEASE` is true.
4. No donor or benchmark value is used to choose a length, detail or depth.
5. An answer to Q-L1 alone moves the concentrated-load-blocked interior spans; Q-B1 / Q-N1 move the
   basis-dependent and nested ones. Re-run this builder after each answer before S5 consumes it.
