# S5 scope recommendation (safe scope only)

## Recommendation

Build S5 as a generic strap / ground-beam rebar engine on the S4 pattern:
- occurrence by occurrence and component by component;
- the S4 states;
- the S4 provenance contract extended by `ground_system_provenance`;
- freeze before any reference;
- net only, with the BBS firewall.

S5 must consume this round's registers and never re-parse the drawing.

## May be quantified in S5

| Scope | Members | State S5 may give |
|---|---|---|
| Ground-beam longitudinal bars (TOP_MAIN, BOTTOM_ROW_1, BOTTOM_ROW_2 as separate components), straight run = `BAR_RUN_LOWER_BOUND_M` | 46 spans with `MAY_RELEASE = True`: 20 PROJECT_GENERAL_DETAIL, 16 EXPLICIT_LENGTH_CONDITION, 10 CANDIDATE_DETAIL that are candidate-invariant | LOWER_BOUND (development blocked) |
| Ground-beam stirrup count | 43 spans with a single Ø8 / 150 callout | count LOWER_BOUND; mass needs the core path, so a kg is released only where the core path is established (none yet) |
| Strap longitudinal bars (TOP, BOTTOM as one schedule total), straight run ≥ clear length between footing faces | SB1, SB3 | LOWER_BOUND |
| Strap stirrup count | SB1, SB3 | count LOWER_BOUND (rate × clear length); mass blocked (no topology) |

## Must stay blocked or unquantified

- **Ground beams:**
  - longitudinal bars of the 13 spans whose candidate details disagree (S5-Q2);
  - side bars of every exterior candidate (S5-Q1);
  - the stirrup core path where the depth is unknown or differs (47), and hooks (all, S5-Q6);
  - development / anchorage and end treatment (all, S5-Q7).
- **Straps:**
  - everything in SB2 (S5-Q8);
  - strap stirrup mass, hooks and development.
- **Provisional at most:** the stirrup core path of the 12 interior spans with a single cross-verified section. The link shape is drawn but is not a verified facet.

## Rules for S5

1. **Lengths:**
   - Concrete keeps the clear length.
   - Bars use the source-supported straight run plus separately named components: DEVELOPMENT_INTO_SUPPORT_1/2, HOOK_1/2, LAP, OTHER_END_TREATMENT.
   - Neither the Urban clear length nor a full support length is chosen because it matches a reference.
2. **Bottom rows:** the two lower rows of the p.13 sections are two components and are never merged.
3. **Applicability:**
   - A CANDIDATE_DETAIL component releases only when it is identical in every candidate (`CANDIDATE_INVARIANT`).
   - A SOURCE_CONFLICT never releases.
4. **Geometry and freeze:**
   - Use the network from `engine/source/ground_beam_network.py`: multi-partner pairing and arc overlap. The V3 lab functions are not used for S5.
   - Re-run its conservation before S5 freezes.
5. **Out of scope until asked:** lintels, the boundary wall, lift-pit walls, the pool and the ground slab.
