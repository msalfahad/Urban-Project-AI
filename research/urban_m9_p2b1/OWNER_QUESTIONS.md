# Outstanding genuine owner questions only (deliverable 15)

Four questions remain that only the owner can answer. Each was checked against the registry, the project
decisions, the drawings and the earlier owner answers before being listed (UP-KB-QUES-001). The approved door
dimensions are **not** re-asked. Work continues safely on every one of them: the affected quantity is either
PROVISIONAL, ASSUMED or withheld, and named.

| Id | Raised on | Question | Recommendation (used meanwhile) |
|---|---|---|---|
| OQ-01 | registered; not triggered on the regression drawings (no enclosed pantry with a door) | **Pantry doorway: marble threshold or floor porcelain?** | marble threshold, measured PROVISIONAL |
| OQ-02 | every drawing with a door below the owner standard (villa, reference plan) - once per run | **Head height of an enlarged wall opening?** | the door height, ASSUMED |
| OQ-03 | every drawing with a stair enclosure (villa: 3 items, reference plan: 6) | **Stair-hall wall finishes and skirting?** | dry-room treatment with the stair skirting along the stair |
| OQ-04 | the reference plan (1 exterior space) | **Exterior finish scope beyond waterproofing?** | keep the areas as information |

## OQ-01 - pantry doorway threshold (C_RULE_CONFLICT, conflict CF-03)

- **Found**: an enclosed pantry with a door is a wet area under the master program (UP-WET-001), but the Urban-wide
  marble-threshold rule (URBAN-WET-SERVICE-MARBLE-THRESHOLD) lists the pantry as not applicable.
- **Rules checked**: UP-WET-001, UP-THR-001, URBAN-WET-SERVICE-MARBLE-THRESHOLD.
- **Why it is unresolved**: two approved owner statements disagree for the same doorway, and neither states which one
  prevails.
- **Alternatives**: (a) a marble threshold at pantry doorways; (b) the pantry floor porcelain continues through the
  doorway (no threshold).
- **Affects**: FIN.MARBLE.THRESHOLD and the doorway-strip floor porcelain of pantry doors (small areas).
- **Meanwhile**: (a), PROVISIONAL, flagged PANTRY_THRESHOLD_RULE_CONFLICT.

## OQ-02 - head of an enlarged wall opening (D_MISSING_OWNER_POLICY, conflict CF-11)

- **Found**: the owner correction adds 0.10 m to the width of the architectural wall opening; it does not say whether
  the opening head also needs an allowance above the door height.
- **Rules checked**: UP-DOOR-OPEN-002, UP-DOOR-HGT-001.
- **Why it is unresolved**: no approved rule gives the wall-opening head allowance.
- **Alternatives**: (a) wall-opening head = door height; (b) door height + an owner allowance.
- **Affects**: the OWNER_REQUIRED wall-opening areas (and through them the blockwork, plaster and paint deductions of
  an enlargement) - a proposal view, not released quantities.
- **Meanwhile**: (a), ASSUMED. Raised once per run, never per door.

## OQ-03 - stair-hall finishes (D_MISSING_OWNER_POLICY; earlier Q-S6-4, O6, OD-10)

- **Found**: stair enclosures have plaster, paint and skirting items with no rule.
- **Rules checked**: UP-STAIR-001 .. 014, UP-VOCAB-004 / 005.
- **Why it is unresolved**: the stair rules cover treads, risers, landings, stair skirting and railings - not the
  enclosure walls.
- **Alternatives**: (a) dry-room treatment (plaster + paint + stair skirting); (b) a specified wall finish.
- **Affects**: FIN.PLASTER / FIN.PAINT / FIN.SKIRTING of stair halls (withheld meanwhile).

## OQ-04 - exterior scope (D_MISSING_OWNER_POLICY; earlier Q1, O7)

- **Found**: exterior spaces (garden, terrace, hardscape) carry an area only.
- **Rules checked**: UP-WP-ROOF-001; no approved external interlock / paving record was found.
- **Why it is unresolved**: no approved exterior finish scope exists beyond waterproofing.
- **Alternatives**: (a) interlock / external tiles by specification; (b) excluded from the architectural BOQ.
- **Affects**: ARCH.EXTERIOR (information only meanwhile).

## Not owner questions (for completeness)

- **Document requests (B)** - sections and finish heights, window schedule / sill types, door schedule, room labels,
  lift label or schedule, block specification, tile sizes, the kitchen zone of an open plan, the laundry's finish
  schedule, the balcony membrane specification. They go to the design team; the rule exists, the drawing evidence
  does not.
- **Engineering backlog (E)** - reader limits (entity kinds not read, nested hatches, unread frames) and doorway strips
  the engine cannot attribute to one opening. They are the engine's to fix.
- **Resolved by precedence (C without a question)** - a project's explicit wall-tile height below the owner
  full-height rule: the project source governs and the difference is flagged.
