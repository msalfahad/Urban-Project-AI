# Questions for the owner (at most 5 open; answer under "Answer:")

Lead adds questions an agent cannot decide from drawings, rules or evidence. Answered questions move to the bottom.
Decisions still queued behind these (from the master study `14_OWNER_DECISIONS_QUEUE.csv`): D-17 review-space wet / dry,
WP-KITCHEN membrane scope, WP-JOINT details, WIN-REVEAL finish, STUB-LIMIT, MEAS-STD, ROOF-FIN, BLIND-AUTH.

## Open

(none; next candidates from the queue above)

## Answered

### Q-01 Plan reader: may Claude look at the drawings? (answered 2026-10-18)
Answer: Yes, always. The visual layer of PLAN_READER.md is on for every project drawing.

### Q-02 Working accuracy targets (answered 2026-10-18)
Answer: The main target is to get everything correct. 95 %+ against the freelancer is a floor, not the goal: the engine
may become more accurate than the freelancer. So a difference from the freelancer is not automatically an engine error;
the verifier decides from the drawing who is right (MISSION.md "Who is right").

### Q-03 Waterproofing upturn (answered 2026-10-18)
Answer: 0.20 m. Already the current rule (knowledge 1.4.0 rules[41], UP-WP-003; 0.15 m is superseded, rules[47]). No change.

### Q-04 Door minimum, D-16 (answered 2026-10-18)
Answer: The minimum is the door opening: ordinary 1.00 m opening = 1.10 m wall to wall. These are minimums: when the plan
is drawn wider, the drawn size is used. The main door is measured as drawn. Matches the registry 1.1.0 reading
"wall opening = nominal + 0.10 m" (owner_questions[4], rules[13]); by the same rule a bathroom 0.90 m opening = 1.00 m
wall to wall (owner confirmed 2026-10-18, also "unless the measurements say more": drawn size when wider). Recorded
as a new knowledge version (task T-011).

### Q-05 Second villa and independent QS (answered 2026-10-18)
Answer: Yes. Other villas exist as AutoCAD and PDF, but without full concrete and rebar drawings. Use them as development
villas for architectural trades, the plan reader and silent-omission checks (Gates 1, 2, 4); not for concrete / rebar,
and not as blind proof until an independent QS measures one (task T-012).

