# Owner management decision, 2026-10-20 (about 20:10 UTC)

The owner gave this decision in his main chat after reviewing ENGINEERING_ASSESSMENT_2026-10-20.md. It is recorded in
his words, shortened only in layout, and binds every agent.

## 1. Roles

| Role | Owns |
|---|---|
| **Lead: Engineering & Delivery Manager** | The engineering roadmap, the drawing-interpretation strategy, the shared project element register, cross-trade dependencies, task allocation, integration priorities, accuracy reporting and delivery milestones. It is technically accountable for the complete BOQ engine, not simply the board. |
| **Worker 1: Structural engineering** | Concrete, structural element geometry, reinforcement by actual bar population, formwork, excavation, backfilling and related structural takeoff. Missing high-materiality structural categories come first. |
| **Worker 2: Architectural & finishing engineering** | Room geometry, wall finishes, plaster, paint, tiles, ceilings, skirting, openings, glazing, stair finishes, waterproofing and architectural takeoff. |
| **Worker 3: Engine integration** | Integration of checker-verified calculations into the main BOQ pipeline, version management, BOQ regeneration, the coverage registry, downstream consistency checks and export. Worker 3 must not independently invent or approve engineering quantities. |
| **Checker: independent engineering verification** | Software testing and frozen-method checks continue, strengthened by independent drawing re-measurement, geometry validation, scope completeness and cross-trade reconciliation. It must not merely repeat a worker's assumptions. |
| **Auditor: independent oversight** | Process integrity, run reliability, missing scope, verification quality and measurable engineering progress. One daily executive report plus critical alerts only; detailed logs stay in the repository. |

## 2. Integration policy

**APPROVED.** Checker-verified pieces may be integrated automatically into a versioned, opt-in BOQ candidate, through
the authorised development workflow.

**NOT APPROVED.** Changing the released default automatically, merely because code was merged or tests passed.

Each candidate shows:

- before and after quantities;
- source drawing references;
- the owner manual method;
- the drawing-derived method;
- independent verification evidence;
- missing or held items;
- downstream BOQ impacts;
- regression results.

Do not create a new method version for every small task when one candidate can safely consolidate the work. Keep
rollback capability.

## 3. Accuracy

The 95 % target stays. It is never claimed without independent evidence. Track separately:

1. quantity accuracy by trade and unit;
2. scope completeness;
3. independently verified coverage;
4. classification accuracy;
5. commercial materiality, where reliable unit rates exist;
6. software and agent reliability.

Rules:

- Never combine unrelated physical units into one metric.
- Held quantities are never counted as correct.
- Freelancer agreement alone is never proof.
- The sealed benchmark is preserved for formal evaluation.

## 4. Architecture

Prioritise a shared, stable element register linking:

- project and drawing revisions;
- floors and levels;
- rooms;
- walls and openings;
- structural elements;
- stairs and landings;
- roofs and external areas;
- finish and waterproofing zones.

Each element has a stable ID, drawing evidence, and links to the BOQ quantities derived from it. Build it incrementally,
without rewriting working modules unnecessarily.

## 5. Owner methods

Owner manual methods stay active, controlled and auditable. Drawing-derived calculations are kept separately and the
differences are explained. Frozen methods stay protected.

## 6. Q-70

A, CONDITIONAL. The answer is recorded in OWNER_QUESTIONS.md.

## 7. Operational reliability

- Complete the repository-attached migration through the approved least-privilege process.
- Auto-mode Test B must pass before the configuration goes to main.
- One concise owner instruction package if a one-time owner action is needed.

## 8. Focus

- **Paused:** marketing and social-media tasks within the BOQ programme (product agents a10–a17 and similar). Nothing is
  deleted.
- **Retired:** duplicate owner reporting, through the scheduling controls only.
- **Priority order:**
  1. integration of already verified quantities;
  2. missing BOQ categories;
  3. drawing interpretation accuracy;
  4. structural and architectural completeness;
  5. independent verification;
  6. end-to-end BOQ generation.

## 9. Thirty-day delivery targets

| By | Target |
|---|---|
| Day 7 | At least one meaningful, independently verified improvement flows through the integrated BOQ pipeline |
| Day 14 | Measurable improvement in verified BOQ coverage |
| Day 30 | A reproducible full-villa BOQ candidate covering the principal trades, with every unknown and held item disclosed |

These are targets, never permission to fabricate or bypass verification. Re-estimate the roadmap from actual
milestones.

## 10. Autonomy

- Ordinary development, task assignment, testing, documentation, non-production integration and verification proceed
  without the owner.
- Never re-ask answered questions. Search drawings, schedules, sections and rules first.
- Bundle genuine owner decisions into one package, and keep independent work moving while they are pending.

## 11. Reporting

One daily executive report, covering:

- new integrated capabilities;
- quantities independently verified;
- coverage and accuracy changes;
- major risks;
- run reliability;
- critical-path progress;
- time to the next milestone;
- genuine owner decisions.

No hourly reports.

## 12. Limits

This decision does **not** authorise:

- changing platform permissions;
- pushing unreviewed configuration to main;
- modifying frozen owner methods;
- exposing private client data;
- releasing unverified quantities.

No new lengthy assessment unless evidence shows the plan is failing.
