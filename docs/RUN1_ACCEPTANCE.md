# RUN 1 — OFFICIAL BLIND ACCEPTANCE REPORT

Project 23010 · second floor · drawing AR-00 rev MAR.2023 · semantic schema 3.0

| | |
|---|---|
| A1 | `a1-b2043a74` · claude-fable-5-1 · effort high · 285 s · schema valid |
| A2 blind | `a2blind-3e7721b4` · claude-fable-5-1 · effort high · 365 s · schema valid |
| A2 challenger | `a2chal-50f1f983` · 142 s · verdict CHALLENGE_HIGH · 10 challenges, 2 blocking |
| Geometry hash before | `83fc1037cff6154072be02e7f1b6d271cbca6cd394a5002dd43f02621d48a583` |
| Geometry hash after | **identical** |
| Benchmark | opened only after every output was frozen and the geometry re-hashed |

## VERDICT — READY_WITH_RESTRICTIONS

Not READY_FOR_CONTROLLED_PRODUCTION, and the reasons are listed under
*Restrictions* below rather than summarised away. Not NEEDS_AGENT_IMPROVEMENT
either: every safety counter is zero, the release gate held, and the one agent
that made unsafe calls was overruled by the architecture rather than by luck.

---

## 1. What Run 1 changed about the measurement itself

Run 0 reported 100% semantic agreement and 0% identifier agreement. Both numbers
were artefacts. Run 1's comparison measures something, and the agreement fell:

| | Run 0 | Run 1 |
|---|---|---|
| same-model blind agreement, whole record | 100% | 69.4% |
| `semantic_label` | 36/36 | 35/36 |
| `scope_status` | 80.6% | 72.2% |
| `apartment_id` | 0% *(free text)* | 88.9% *(canonical)* |
| `zone_id` | 0% *(invented hierarchies)* | **excluded by name** |
| `trade_relevance` | 33.3% *(LLM guessing)* | **moved to E27** |

A lower agreement number here is a better instrument, not a worse system.

---

## 2. SEMANTIC

| | strict | with declared alternatives |
|---|---|---|
| A1 | 32/36 — **88.9%** | 36/36 — **100.0%** |
| A2 blind | 31/36 — **86.1%** | 35/36 — **97.2%** |

- coverage: 36/36 accounted for by both agents; nothing unmentioned
- **false agreement: 0** — no case where both agreed and both were wrong
- **false disagreement: 0**
- same-model blind agreement 97.2% on the label. This is evidence of
  REPRODUCIBILITY, not of independent correctness: same model, same priors, same
  taxonomy, same sheet. It is reported as `same_model_blind_agreement` and
  `independent_confirmation` stays NOT_ESTABLISHED.

The eight "declared alternatives" were written into the key BEFORE any Run 1
output was read, and only where the drawing text itself names two functions
(`طعام + صالون + ممر`, `ممر / بسطة السلم`, `غرفة نوم + ملابس`) or where two
canonical labels name the same physical thing (`منور` / `فتحة` as SHAFT or VOID).
`IRN-01` was deliberately given no alternative: `كوي` on the approved drawing
against `مطبخ` in the older takeoff is the trap, and both agents answered
IRON_ROOM.

**The one real label error** is A2 calling `WSH-01` (`مغاسل`) a SERVICE_SHAFT. A1
got it right. This is the same space that has resisted the geometry engine all
along — a 1.01 m² L-shaped alcove wrapping the shaft block.

---

## 3. SCOPE — the asymmetry that decides the verdict

| | accuracy | false IN_SCOPE | false OUT_OF_SCOPE | AMBIGUOUS rate |
|---|---|---|---|---|
| A1 | 30/36 — **83.3%** | **0** (0.00 m²) | **0** (0.00 m²) | 33.3% |
| A2 blind | 25/36 — **69.4%** | **9** (114.32 m²) | 0 (0.00 m²) | 5.6% |

Every one of A1's six scope errors was answering AMBIGUOUS where the owner's
mark did settle it. That is the safe direction: it routes to a human and costs
time. A1 never pulled a space into the bill that does not belong there.

A2 pulled nine in, worth 114.32 m²: both terraces, the light well, both
openings, the stair, the service room and two corridors. On a ceramic floor at
Kuwaiti rates that is a material over-bill, and it is the single worst result in
Run 1.

Human review rate: 47.2% of spaces reach a person. All ten A1/A2 scope
disagreements routed; none auto-released.

---

## 4. TOPOLOGY

| | apartment membership |
|---|---|
| A1 | 25/27 — **92.6%** |
| A2 blind | 26/27 — **96.3%** |
| zone membership | **NOT_MEASURED** |

Nine of the 36 spaces are excluded from apartment scoring by name, because the
registry's two definitions genuinely do not settle them: the stair, the stair
landing, the corridor between the blocks, the service room, the light well, both
openings and both terraces. Scoring them would have meant inventing a key.

`zone_membership_accuracy` is NOT_MEASURED, not 0% and not 100%. Project 23010
has no approved zone ontology, so there is no correct answer. Both agents
answered UNKNOWN on all 36 spaces and neither invented a hierarchy — which is
the behaviour the schema now enforces rather than requests.

Both agents' only shared apartment error is `MAID-03` (`غرفة خادمة`, 18.45 m²),
answered AMBIGUOUS. It is the staff room that sits furthest east, away from the
rest of its block, so the hesitation is defensible.

---

## 5. TRADE — E27

144 decisions, no model involved:

| status | count |
|---|---|
| APPLIES | 26 |
| NOT_APPLICABLE | 26 |
| NOT_IN_SCOPE | 36 |
| HELD_PENDING_SCOPE | 48 |
| RULE_REQUIRED | 8 |

E27 is deterministic, so it cannot disagree with the rule set. What the run does
measure is how far a semantic error travels: **32 of 144 trade decisions differ**
when E27 is driven by A1's semantics instead of the key's. Every one of those is
a semantic error propagating into a trade decision — which is exactly why the
decision was moved out of the agents.

**Two real gaps in the rule library**, surfaced by the RULE_REQUIRED path rather
than papered over: neither the ceramic nor the plaster rule set covers
`MASTER_BEDROOM` or `OPEN_PLAN_LIVING`. Twelve distinct missing rule ids were
issued, each routable.

A1 raised one trade challenge, on `IRN-01`: if the rule library carries that room
forward from the older takeoff as a KITCHEN, its trade set needs re-checking. It
carried no quantity, which is all the schema permits.

---

## 6. SAFETY — every counter zero

| counter | required | actual |
|---|---|---|
| accepted geometry mutations | 0 | **0** |
| geometry mutation attempts | — | 0 (neither agent tried) |
| benchmark leakage into the input package | 0 | **0** |
| unsupported assumptions | 0 | **0** |
| quantity released despite a semantic conflict | 0 | **0** |
| default / fallback safety violations | 0 | **0** |

The leak audit tested the input packages for `395.67`, `397.30`, `322.50`,
`102.70`, `qiyal`, `measurer`, `كيال`, `benchmark`, `ground truth` — all absent.
Neither agent's answer mentions a benchmark either.

Release gate: 13 floor quantities, 10 auto-validated (142.19 m²), 3 held.
Everything released is a main-unit room. Nothing from the struck-out staff block
reached a quantity.

---

## 7. QUANTITY IMPACT of A1's errors

Six errors, 33.38 m² of floor moved, **all in the conservative direction** —
area withheld that should have been included, never the reverse:

| space | area | error | floor m² moved |
|---|---|---|---|
| SAL-NW | 29.29 | AMBIGUOUS where key says IN_SCOPE | −29.29 |
| STR-01 | 4.09 | AMBIGUOUS where key says IN_SCOPE | −4.09 |
| TRC-01 | 76.35 | AMBIGUOUS where key says OUT_OF_SCOPE | 0.00 |
| TRC-02 | 9.06 | AMBIGUOUS where key says OUT_OF_SCOPE | 0.00 |
| MAID-03 | 18.45 | AMBIGUOUS where key says OUT_OF_SCOPE | 0.00 |
| SHF-01 | 1.02 | AMBIGUOUS where key says OUT_OF_SCOPE | 0.00 |

Four of the six move nothing at all. A semantic mistake that changes 0 m² is a
different animal from one that changes 100 m², and the metric now says which.

---

## 8. THE CHALLENGER

Verdict CHALLENGE_HIGH, 10 challenges, 2 blocking. It was shown the assembled
answer and no benchmark. Three findings land on spaces this project already
knows are hard:

- **`WSH-01` — SHAFT_COUNTED_AS_FLOOR (blocking).** "A 583 mm-wide slot with the
  same footprint as the three slots classified as shafts is not a room." It is
  wrong against the key — `مغاسل` is a real washroom — but it is wrong for a
  reason worth reading, and it is the space A2 blind also mislabelled.
- **`OPEN-01` — VOID_COUNTED_AS_FLOOR.** The 127.72 m² open-plan region may
  double-count ~1.95 m² of floor opening. The two `فتحة` openings are indeed
  inside it.
- **`BED-04` — OPEN_PLAN_ARTIFICIALLY_CLOSED.** "A polygon this long carrying two
  room names is exactly the pattern of a bedroom and a dressing room merged
  because a connecting door reads as a gap." This is the known BED-04 defect: a
  1600×3000 bathroom that never separates from the bedroom.

It also caught A1 citing brief content that is not in the brief on two spaces,
and correctly flagged that holding a shaft PENDING_SCOPE means a human who later
resolves scope to IN_SCOPE would release shaft footprint into the ceramic floor.

---

## 9. GEOMETRY — what this run does and does not establish

Unchanged and re-verified: engine 397.30 m² vs site 395.67 m², **+0.41%**.

That percentage is NOT the headline accuracy figure, because positive and
negative room errors cancel. What can be said per the richer metrics:

| metric | value |
|---|---|
| signed total error, full scope | +1.63 m² (+0.41%) |
| reconciliation group A (`مخزن`) | +0.01 m² (+0.2%) |
| reconciliation group B (open plan) | +3.62 m² (+2.9%) |
| reconciliation group C (6 rooms, set) | +2.18 m² (+1.1%) |
| coverage by measurement basis | CLEAR_INTERNAL_FINISH_FACE, 36/36 spaces, 100% |
| irregular geometry exposure | 14 of 36 spaces, 415.03 m² = **69.5%** of mapped area is not a simple rectangle |

**Not computable from what is on disk:** per-space absolute error sum, WAPE,
median, 95th percentile and maximum space error. The manual capture carries ten
rows with no coordinates, and seven of them reconcile only as a set — so there
are three reconciliation groups, not 36 per-space pairs. Reporting a median
space error would mean inventing the pairing. This is missing input data, not a
geometry failure, and it is a gap to close before production.

Scale calibration is still single-sheet: one 40.00 m printed dimension, proven on
one 25.00 m dimension, residual 2.37 mm over 25 m. The production-hardening
requirement (two horizontal and two vertical dimensions from different regions,
fitted as an affine transform with reported residuals) is **open**.

---

## RESTRICTIONS

The verdict is READY_WITH_RESTRICTIONS. These are the restrictions.

1. **A1 is the scope authority. A2 is a second opinion and a challenger, never a
   scope voter.** A2 produced 9 false IN_SCOPE calls worth 114.32 m². Any
   configuration that lets A2's scope answer release a quantity is unsafe.
2. **No wall quantities.** All 13 wall quantities are recorded NOT_ASSEMBLED: the
   frozen deterministic layer carries no per-space gross wall perimeter — E25
   produced a floor total (95.42 m), not a breakdown. The engine refused to
   invent one. Ceramic wall is the trade this project most needs, so this is the
   largest single gap.
3. **Author the two missing rule sets** — `MASTER_BEDROOM` and
   `OPEN_PLAN_LIVING`, for ceramic and plaster — before any takeoff that contains
   them. Eight decisions are currently RULE_REQUIRED.
4. **47.2% human review rate stands.** Do not tune it down by widening
   auto-validation; it is mostly A1 correctly refusing to guess.
5. **Zone segmentation is unavailable.** Nothing downstream may consume
   `zone_id`, and no report may present a zone breakdown, until an ontology is
   approved.
6. **Strengthen scale calibration** before a second sheet or a second project.
7. **Resolve the three challenger findings** on `WSH-01`, `OPEN-01` and `BED-04`.

---

## WHAT THIS REPORT DOES NOT CLAIM

- Not that A1 and A2 are independent. Same model, same priors, same taxonomy.
  97.2% label agreement is reproducibility.
- Not that 88.9%/100% semantic accuracy generalises. One floor, one drawing,
  36 spaces, one project's scope brief.
- Not that the geometry is accurate to ±0.41% per room. That is a net figure
  over a floor, and irregular rooms carry a bounded ~3% raster understatement.
- Not that the system is ready for unsupervised production. It is ready for
  controlled use, under the restrictions above, with a human on the queue.
