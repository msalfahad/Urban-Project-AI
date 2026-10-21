# Open questions

## For ChatGPT (engineering)

1. **ε for "at least" predicates.**
   - I propose ε = 1e-6 mm, in drawing units: about 4 orders above float noise at site scale, 3 below drafting precision.
   - Would you rather use a drafting-precision tolerance (0.01 mm), or move every threshold off the common drafted modules (100 / 300 / 500 mm) instead?
   - Is there a case where 1e-6 mm admits something it should not?
2. **CLOSED doors.** Should a drawn swing with no measured wall gap become a **PROVISIONAL door line**, with its width from the leaf or swing radius? Or should it stay an RFI until a gap is confirmed? I lean to a PROVISIONAL line plus a REVIEW flag, because the symbol is the drafter's explicit statement.
3. **RFI grouping.** Should the per-element BLOCKED lines stay in `BOQ_LINES`, each pointing to its question id (my proposal, for traceability)? Or should they live only in the register?
4. **NSD-4 wall-face ledger.** Should conservation be per wall-band face (geometric) or per room boundary run (functional)? Per band face catches more, but needs a face-to-space assignment for every piece, caps and column faces included.
5. **Behaviour freezes and environments.** S6-ENV-01: on the synthetic villa, Python 3.11 and 3.13 agree within 1e-9 in value, but not in output bytes. Should a behaviour manifest pin the interpreter, or should outputs be canonicalised (sorted keys, fixed float formatting) so the manifest is portable?
6. **Exit code for element non-conservation.** Exit 3 (completeness failed), or exit 0 with a REVIEW finding? I propose exit 3: a missing door is not a review nicety.
7. **Dimension evidence (P2-09) before the blind round.** Is it worth the parser cost now, or only after the blind round shows self-consistent-but-wrong models?
8. **The redesign of the opening census (answer 2).** Symbol-primary (a door symbol creates the opening; the gap confirms it), or gap-primary with symbol conservation? Symbol-primary is more robust to wall-reader defects; gap-primary is more robust to stray symbols.

## For the owner (decisions only the owner can make)

| # | Decision | Why it is needed | Default if not decided |
|---|---|---|---|
| O1 | Freeze by behaviour (output hashes of pinned runs) instead of source bytes; source digests become recorded provenance; an append-only errata register | Phase 2 must otherwise keep parallel copies of shared modules | parallel modules (more duplication) |
| O2 | `--strict-admission` as the V1 default, with `--legacy-admission` (recorded) | 22 silent V1 failure modes become 0 | V1 stays permissive |
| O3 | Accept that V2.1 differs from V1 on the reference plan (+1 door, +1 window, +0.20 m wall run, the CLOSED doors as lines), the corrected result being versioned and reviewed | R2; Investigation A | V2.1 not started |
| O4 | Q-S6-1: finish and measurement of the floor strip inside a doorway (threshold piece, room floor continued, other; m² or lm) | resolves 24 RFI lines | RFIs stay |
| O5 | Q7 + the conflict S6R-B4: is wet-room wall tile full height by default (method register) or derived per face (UP-CER-009)? And what goes in the band above partial tile? | resolves 16 RFI lines, or closes them as not applicable | RFIs stay; the conflict stays |
| O6 | Q-S6-4: stair-hall wall finishes and raking skirting scope | 6 RFI lines | RFIs stay |
| O7 | Q1: exterior scope (garden, terrace, hardscape) | exterior records | records only |
| O8 | Provide the window schedule / elevations and sections for the reference villa, and make them a required input for new projects | 25 window-reveal RFIs; every finish height | RFIs stay; no plaster / paint quantity |
| O9 | Route-G / M4 lintel evidence: open a versioned structural correction now, or record the errata only (S6R-A2)? | the frozen structural release misses one door and one window on this plan | errata only |
| O10 | Provide two unseen villas from different drafters for the blind round (R8) | the only evidence that generalises | no generalisation claim |
