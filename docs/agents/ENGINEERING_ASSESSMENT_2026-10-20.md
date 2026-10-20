# Urban Project AI: Engineering and Autonomous Operations Assessment

Written by the owner's main chat on 2026-10-20 at about 20:00 UTC, in answer to the owner's Master Directive of the same
day.

**What it rests on:**

- working branch `claude/access-permissions-setup-ii24ws` @ 2264938;
- board `agents/control` @ 1fba9b2;
- the scheduled-task records (list_triggers / get_trigger);
- docs/agents/* (BOARD, SCOREBOARD, PROGRESS, RUN_LOG, RUN_LEDGER, MISSION, PLAN, TEAM, OWNER_QUESTIONS);
- rules/coverage/BOQ_FAMILY_MASTER_1.0.0.json;
- tools/urban_boq_m9.py;
- a full test collection on 2264938 (Python 3.11.17).

**What it could not inspect:**

- the transcripts of scheduled runs (not readable from this chat);
- the sealed benchmark URBAN_BLIND_V2 (deliberately not opened);
- the private repositories (not attached).

Every percentage below is an estimate. Each one carries its method and uncertainty, and none is a measured product
accuracy.

## 1. Executive assessment

1. **The engine is not yet a usable BOQ product.**
   - The only quantities measured against a reference are 3 concrete lines on Alsenan: 92.77 against 111.81 m3,
     -17.03 % (SCOREBOARD.md, 19th verifier run, commit 8774071).
   - Plaster, paint and floor area are HELD. Doors and windows are refused on units.
   - Rebar, formwork, excavation and most finishes have no released line.
   - **No quantity has been independently verified on a held-out villa.** Alsenan is a development set: tuning is
     allowed there, so it can never prove accuracy (MISSION.md).
2. **The main problem is integration, not effort.**
   - 77 tasks were merged in 3 days: 7 on 10-18, 41 on 10-19, 29 on 10-20 (`git log --merges`).
   - Yet the measured, released BOQ has not changed since 2026-10-19 12:10.
   - The checker states this for almost every merge: "imported only by its own tests and research scripts ... the scored
     ARCH_TAKEOFF_V2.9 + route G run is identical by construction" (SCOREBOARD header, 30th to 44th runs).
   - The work lands as:
     - standalone modules that are "not wired";
     - opt-in method versions, of which there are 16 (`ARCH_TAKEOFF_V1` to `V2.13` in tools/urban_boq_m9.py; the
       released default is V2.9);
     - hand tables marked NO REPO CODE.
   - The pipeline rewards READY → MERGED, not "a released BOQ line got closer to the truth".
3. **Execution reliability is the second blocker.**
   - Today 17 of 36 scheduled code-agent runs succeeded (47 %), 6 were BLOCKED and 12 were silent (RUN_LEDGER.md).
   - Root cause, found and documented: the scheduled tasks have no repository attached. The auto-mode safety check
     therefore treats the agents' own clone, installs and tests as external code
     (code.claude.com/docs/en/auto-mode-config: "trusts only the working directory and the current repo's configured
     remotes").
   - A fix is built and partly tested (section 8).
4. **The organisation spends a large share of its effort on coordination and reporting:**
   - 4 reporting channels: the Lead's report, this auditor every hour, a second "hub report" chat twice a day, and the
     dashboard refresher;
   - 70 owner questions in about 3 days;
   - workers that are not specialised;
   - a second track of 17 "product agents", mostly marketing and social content (agents/a10_content, a14_ig_analyst,
     a15_marketing, a16_post_designer, a17_campaign), which does not serve BOQ accuracy.
5. **What is genuinely strong:**
   - a disciplined freeze and verification culture: 10,689 collected tests, a freeze index, checker hand re-measures
     (for example the 39-piece roll re-placement for the 2F roof, and the pool-court void re-measure 3.689 against
     4.373 m2);
   - owner methods are preserved;
   - held quantities are never shown as 0;
   - a real structural route (route G) with integrated concrete;
   - a waterproofing roll optimiser that is close to correct.

   The foundations are sound. The missing piece is the path from verified pieces to released, measured BOQ lines.

**Estimated real product completion: about 20 % (range 15–30 %).** Method:

- the 94 non-MEP BOQ families in BOQ_FAMILY_MASTER (audit of 10-12), weighted as integrated = 1, partial = 0.5,
  implemented-not-integrated = 0.25, experimental = 0.1, others = 0;
- adjusted for what was released since (roof waterproofing and rolls in V2.11, skirting);
- independent validation (M5) counts 0.

The registry itself is 8 days old and needs a refresh (first 7-day task).

## 2. Agent responsibility matrix (actual, from the trigger records)

| Agent | Schedule | Actual mission | Can modify | Merge | Release | Reality today |
|---|---|---|---|---|---|---|
| Lead (trig_01K5WMma…) | every 2 h at :09 | plans the board, owner questions, FEEDBACK, RESEARCH_REQUESTS, PROGRESS, LEAD_REPORT, dashboard agents.json | docs/agents only | no | no | runs reliably (no code needed); about 60 % of its prompt is reporting duties; does not run the engine |
| Worker 1 / 2 / 3 (trig_015Ks…, 01JHWB…, 019Mc…) | hourly :19 / :39 / :59 | claim the highest TODO, one 50-minute package, own task branch | engine on own branch; board | no | no | **not specialised**: the same worker moves between stairs, waterproofing, facade, blockwork; Worker 1 had 4 silent runs in a row today; Worker 2 is the most reliable |
| Verifier / Checker (trig_01LLL9…) | hourly :49 | gates a–e, who-is-right verdicts, merges verified work, scoreboard | docs/agents; merge into the working branch | **yes** | no (releases need owner approval for a default switch) | strong when it can execute (full suite, hand re-measures); 2 of 9 runs silent; scoreboard **not re-run since 10-19 12:10** because nothing reached the scored method |
| Auditor (this chat, trig_01QAPf5…) | hourly :28 | run ledger, audit findings, owner report | docs/agents | no | no | useful findings (sign errors, double-counted offcuts, Q-69 arithmetic) but **hourly reports are noise** to the owner |
| Hub report (another chat, chained send_later reminders) | about 04:52 and 16:52 UTC | a second owner report from the same board | owner answers only | no | no | **duplicates** the Lead's and auditor's reports |
| Dashboard refresher (trig_01BHYvj…) | hourly :54 | copies board data to the dashboard | dashboard only | no | no | reliable, low value per run |
| Research scout (trig_01D94Cw…) | **disabled since 10-18** | web research | RESEARCH_LOG | no | no | inactive; the Lead still writes RESEARCH_REQUESTS for it |

**Assessment.** The current organisation is not the best way to build an accurate BOQ engine:

- Workers claim whatever is on top, so no one owns a discipline end to end.
- No agent owns the release path, meaning wiring verified pieces into the scored method.
- Five reporting surfaces exist for one owner.
- No single agent can both invent a quantity and declare it verified, which is good, but nobody is accountable for the
  released number moving.

## 3. The Lead: what it actually does (18-step check)

Legend: **I** = through agent instructions; **M** = performed by the Lead manually from documents; **N** = not
implemented; **C** = in code.

| Step | Status | Evidence / gap |
|---|---|---|
| 1. Understands the objective | I | MISSION.md and gates 0–4; but optimises board throughput, not released accuracy |
| 2. Finds incomplete BOQ coverage | M (partial) | PROGRESS.md table; no refreshed family registry since 10-12; the Lead never runs the engine |
| 3. Analyses drawings | N | the Lead does not read drawings; workers do |
| 4. Finds project-specific rules | M | from owner answers; asks the owner instead of searching the sheets first (70 questions) |
| 5. Applies owner manual methods | I | method guard after 12:15; dual-method tables appear |
| 6. Finds conflicts with drawings | M | through worker handoffs |
| 7. Prioritises | I | "lowest gate first, then money at risk"; money at risk is not computed anywhere |
| 8. Creates tasks | M | yes, 8–12 TODO kept |
| 9. Assigns work | N | workers self-claim; no assignment by specialisation |
| 10. Coordinates parallel work | I | "Files:" column, after-T rule; works |
| 11. Reviews outputs | M | FEEDBACK.md classification |
| 12. Sends to verification | I | READY → checker; works |
| 13. Resolves failed verification | M | rework tasks; works |
| 14. Manages integration | **N** | no integration lane; pieces stay "not wired" |
| 15. Controls releases | **N** | release = owner switch of the default method; four candidates waiting |
| 16. Tracks progress to 95 % | **N** | no accuracy metric beyond 3 concrete lines; scoreboard frozen |
| 17. Plans next stages | M | PLAN.md milestones M1–M5; dates not derived from throughput |
| 18. Escalates only owner decisions | **weak** | 70 questions; several answerable from drawings or existing rules (e.g. door 2.20 m fallback already in knowledge 1.5.0, column-height rule already existing) |

The Lead works as a dispatcher and reporter. It is not yet a senior QS plus engineering lead, because it never
measures, never runs the engine and never owns the release path.

## 4. Engine architecture and integration map

| Stage | Exists (module) | Connected to the released run? | Reliability / gap |
|---|---|---|---|
| Intake: DXF | ezdxf 1.4.4; engine/source CAD readers, units authority, OCS / blocks | yes | strong on synthetic benchmarks (16 plans, 100 % recall); real-plan quirks still found |
| Intake: DWG | tools/dwg_adapter.py (LibreDWG dwg2dxf or ODA converter, run separately) | through conversion | depends on an external converter in the environment; not routinely exercised by the agents |
| Intake: vector PDF | pymupdf (13 engine modules), section_binding, opening_height_pdf | partly (evidence pieces, not the released run) | used for heights and sections by hand-assisted tasks |
| Intake: scanned PDF / images | vision prototype (research), plan-reader census tasks | **no** | experimental; 23 of 29 Alsenan window heights held for that reason |
| Interpretation: architectural | ARCH_TAKEOFF_V2.9 (released) plus V2.10–V2.13 opt-in; topology, room roles, openings, walls | V2.9 only | 11 labelled spaces HELD; wet / dry review sets HELD |
| Interpretation: structural | route G (tools/urban_boq_m2.py): schedules, beams, slabs, footings, columns, stairs, pool, domes | yes | concrete -17 % on 3 compared lines; known gaps: blinding -52.9 % (cause found), columns +28.6 %, pool -8.85 m3 |
| Building model | **no single model**: architectural and structural routes and per-trade ledgers are separate (concrete_ledger_v2, membrane tables, masonry_centreline) | n/a | the largest architectural weakness: levels, rooms, walls, openings and structure are not one consistent model, so cross-trade checks are hand work |
| Quantities | canonical BOQ line schema (S1.2), 1455 lines on Alsenan | yes | many lines HELD by design |
| Verification | freeze_verify, codemap impact, independent reader (tools/indep_reader.py), proof library, checker hand calcs | process, not code | strong process; no held-out accuracy run |
| Export | xlsx room-by-room workbook, BOQ_LINES.csv, PDF | yes | traceable; not yet a commercial BOQ format |

**Drawing understanding** (quantities, schedules, stairs, waterproofing, pools and domes):

| Can do | Partly | Not yet |
|---|---|---|
| plans with layered DXF; room labels Arabic and English (SHX handled); door blocks; footing, column and beam schedules (route G); stairs (riser schedules, landings); roofs and wet-room waterproofing; pools and domes (structural) | sections and elevations (binding exists, heights mostly by hand); door / window schedules (6 of 29 printed heights) | revisions and conflicting sheets; reinforcement details beyond schedules (rebar by bar population not started); ceiling plans; scanned sheets |

## 5. BOQ coverage matrix (MEP excluded, as directed)

Capability is taken from BOQ_FAMILY_MASTER 1.0.0 (10-12), corrected from PROGRESS.md and SCOREBOARD.md where later
evidence exists.

**Effort scale:**

| Code | Size |
|---|---|
| S | 1–2 tasks |
| M | 3–5 tasks |
| L | 6 or more tasks |

**Priority:**

| Code | Meaning |
|---|---|
| P1 | financially material, or blocks other work |
| P2 | other quantities |

| Category | Status | Released / measured quantity (Alsenan) | Verification | Main gap | Priority / effort |
|---|---|---|---|---|---|
| Excavation, backfill, disposal | NOT_IMPLEMENTED | none | none | build from footing / GB geometry plus levels | P1 / M |
| Blinding | INTEGRATED (route G) | 22.155 m3 typed values vs freelancer 47.055 (-52.9 %); cause found (under ground beams / straps) | hand range 20.71–26.37 | wire the corrected scope | P1 / S |
| Footings | INTEGRATED | 64.346 vs 65.634 m3 (-2.0 %), engine right (freelancer double count); F10 HELD | checker hand | F10 designer answer | P1 / S |
| Ground beams / straps | INTEGRATED | straps piece 3.390 vs 3.3925 (engine right) but released run 3.781 | checker | wire the piece | P1 / S |
| Columns | INTEGRATED | 36.711 vs 28.547 (+28.6 %); hand 34.446 | hand | 5 phantom columns plus controlling-member height | P1 / S |
| Beams | INTEGRATED | 68.84 released + 18 pieces HELD vs 65.97 | partial | held pieces | P1 / M |
| Slabs | INTEGRATED | in the concrete total; no separate comparison | none | per-element comparison | P1 / M |
| Stairs and landings (concrete) | INTEGRATED | main stair 5.011 (owner manual) / 4.951 (corrected, conditional) | hand | 3-D overlap proof | P2 / S |
| Pool, domes | PARTIAL | pool 3.50 vs 12.35 m3; domes are a rule difference (owner: not concrete) | — | pool walls / floor from printed sizes | P1 / S |
| Rebar | PARTIAL (bar models), **not by bar population** | not re-measured; earlier 26.24 vs 44.19 t | none | the biggest money item with no measured line | **P1 / L** |
| Formwork | NOT_IMPLEMENTED | none | none | faces from the element model | P1 / M |
| Blockwork | EXPERIMENTAL (pieces, hand) | hand GF 143.16 / 1F 120.75 / 2F 39.78 m vs 134.28 / 120.31 / 39.10; owner Q-69 B: physical 131.88 m candidate; m2 not released | hand | wire centreline V2 + block types (Q-60) + m2 deductions | **P1 / M** |
| Boundary walls | PARTIAL | — | — | Q-65 material HELD | P2 / S |
| Floor finishes by room | piece merged, not released | dry rooms 194.98 vs 189.61 m2 (+2.83 %); 1F porcelain 33.594–33.711 range | hand | release path; Q-70 | P1 / S |
| Wet-area floors | piece | waterproofing floor 72.12 vs 72.01 (+0.16 %) | hand | wire | P1 / S |
| Wall tiles | not measured | hand 447–473 m2 | — | tile height rule applied (Q-48 answered) | P1 / M |
| Plaster | HELD | none (freelancer 1151.14); dry-room hand 321–337 vs 375.40 | hand sample | release with owner manual heights plus drawing-derived | **P1 / M** |
| Interior / exterior paint | HELD | none (1191.13) | — | same walls; ceilings | P1 / M |
| Ceilings / soffits | hand census | 46.316 m2 soffits after the checker's correction; finish HELD (Q-68 C) | checker rejected the first census | finish rule | P2 / S |
| Skirting | released run | gross 262.56 vs 282.85 (-7.2 %); rule difference (door deduction) | audit piece | — | P2 / S |
| Waterproofing floors / upturns / roofs | partly released (V2.11) | roof 204.11 m2 + 2F roof HELD vs 285.00; upturn 181.59 vs 194.00 | checker | 2F roof release (candidate V2.13) | P1 / S |
| Membrane procurement (rolls) | released (V2.11) + candidate (V2.13) | 19 rolls wet areas (21 with pantry), 8 + 6 roofs, 2F roof 17 proven | checker re-placement | owner release decision | P2 / S |
| Stair marble / risers / treads | piece | 39.49 → 44.365 m2 with the landing (Q-66 B) | hand | Q-70; release | P2 / S |
| Handrails | NOT_IMPLEMENTED | none | — | path length from stair geometry | P2 / S |
| Internal / external doors | NOT_IMPLEMENTED as BOQ lines | main entrance 5.00 m2 only | — | door schedule plus 2.20 m fallback (knowledge 1.5.0) | P1 / M |
| Windows / glazing | PARTIAL | 6 of 29 heights: 26.485 vs 24.280 m2 | hand | scanned heights | P1 / M |
| Facade finishes | piece | GF 105.887 geometric / 105.787 billable; HELD range until Q-67 is applied | checker | apply Q-67 A conditional | P1 / S |
| Interlock, roof build-up, screed | NOT_IMPLEMENTED | none | — | — | P2 / M |

## 6. Accuracy and verification framework (proposal)

1. **Reference sets:**
   - **Development**: Alsenan, where tuning is allowed.
   - **Held-out**: URBAN_BLIND_V2 sealed, and Qortuba QS01 (research/external_engine_lab: round-1 rows rebuilt in
     r8_6).
   - **Proof**: a villa measured by an independent QS before engine output exists.
   - "95 % achieved" may be claimed only on held-out or proof sets.
2. **Independent reference per line:**
   - a hand measurement from the drawing by the checker, or by an independent QS;
   - never the engine's own output, and never the freelancer's figure taken alone;
   - the freelancer is a comparison column with a who-is-right verdict.
3. **Error metrics (no cancellation):**
   - per line, absolute error |e − r| / r;
   - per trade, WAPE = Σ|e−r| / Σr;
   - a missing line counts as 100 % error, not as 0;
   - a HELD line is reported separately as UNKNOWN share, never as correct.
4. **Materiality tiers instead of prices:**
   - T1 (weight 3): concrete, rebar, blockwork, plaster, tiles, waterproofing;
   - T2 (weight 2): paint, doors, windows, marble, ceilings;
   - T3 (weight 1): skirting, profiles, minor items.

   Weighted accuracy = 1 − Σ w·WAPE_t / Σ w, over the trades present in the reference.
5. **Separate layers**, each with its own figure:
   1. interpretation (rooms, openings and structural elements found: recall and precision against the hand census);
   2. calculation (error on correctly interpreted elements);
   3. scope completeness (share of reference lines present);
   4. classification (right material / finish);
   5. room-by-room and floor-by-floor error;
   6. structural element error;
   7. procurement (rolls / bags against the hand-optimal count);
   8. software reliability (run success, crash-free, deterministic);
   9. traceability (share of lines with a drawing reference plus rule id).
6. **Verified share** = Σ reference quantity of lines independently verified / Σ reference quantity, reported by tier.
   **Today:** about 3 concrete lines plus a handful of hand-verified pieces. The verified share of the full Alsenan BOQ
   is well under 10 %; it is not computed yet, which is a 7-day task.

## 7. Alsenan case study (status per known issue)

| Issue | State | Verified? | Merged? | Released? |
|---|---|---|---|---|
| Concrete 92.77 vs 111.81 m3 | causes found per element (footing double count by freelancer, stairs + dome rule, pool, blinding scope, phantom columns) | partly (hand) | pieces merged | no change since 10-19 |
| GF facade and passage | Q-64 B, Q-67 A conditional answered; checker confirmed the passage is roofed | yes (checker) | yes | HELD range 98.887–105.887 m |
| GF blockwork and glazing | hand vs freelancer +8.88 m; Q-69 B answered; arithmetic error (8.28 not 8.88) to correct | hand | pieces | no |
| Stair landing porcelain vs marble | Q-66 B; porcelain 33.594–33.711 range; Q-70 open for 2F | candidate | READY | no |
| Stair concrete overlap | 5.011 manual vs 4.951 corrected; 3-D proof pending (G5) | no | hand | no |
| Roof membrane rolls | 2F roof 17 rolls proven by checker re-placement | **yes** | V2.13 opt-in | **no (owner decision)** |
| Pantry waterproofing | 13.50 m2, 2 rolls; upturn HELD | yes | V2.13 opt-in | no |
| Beam / footing schedule conflicts | F10 HELD with designer request; 18 beam pieces HELD | partial | — | held |
| Annex heights | owner G2: 3.15 m manual provisional; slab datum requested | n/a | — | held |
| Exterior soffits and pool void | census rejected (void 3.689 vs 4.373); 46.316 m2 corrected; finish HELD | checker | rejected, rework | no |
| Wet-room classification | 17 areas measured; pantry released only in the candidate | hand | pieces | partly (V2.11) |

**Last 15 merged tasks:**

- Measurable released-BOQ change: none.
- Hand-verified findings: 6 (2F roof 17 rolls; pantry 2 rolls; passage roofed; blockwork per floor; 1F living traced;
  blinding cause).
- New opt-in method versions: 2 (V2.13; facade piece).
- Audits: 4.
- Census / hand tables: 3.

Source: `git log --merges` on 2264938 (2264938, bc21314, 4fddf74, 5592692, 8c23eea, a703655, a51bdca, c1f0467,
5fe31ca, 60f1d8d, 2dc1657, 5476226, 795d660, 79bd397, 6319aca).

## 8. Agent productivity and bottlenecks

1. **Runs today** (RUN_LEDGER.md): 36 finished code-agent slots:

   | Status | Runs | Share |
   |---|---|---|
   | SUCCESS | 17 | 47 % |
   | BLOCKED | 6 | 17 % |
   | FAILED | 1 | 3 % |
   | INCOMPLETE (silent) | 12 | 33 % |

   Silent runs end after 2–6 minutes with nothing written. Their cause is NOT KNOWN, because transcripts can't be read
   from here. The STARTED line (live since 19:19, first written by Worker 1) will expose where they stop.
2. **Refusal causes seen** (exact tags): [Code from External], [Untrusted Code Integration], [Modify Shared Resources],
   [Auto-Mode Bypass], [Sensitive-Source Provenance], [PII Data Handling], [External System Writes].
   - All are consistent with sessions that have no attached repository.
   - The "authorization" paragraphs cannot fix this: a scheduled task's saved prompt "can't act as approval or consent"
     (code.claude.com/docs/en/routines).
3. **Fix status:**
   - Candidate branch `agents/config-candidate` (3 files, 345 lines; `main` untouched).
   - Local simulation: PASS.
   - Cloud Test A in Manual mode: 8/8 PASS with no prompts, which shows the allow rule and startup hook work.
   - Test B in Auto mode (Drive decode, denials, board push) is **waiting for the owner to start it** (this chat can't
     start an auto-mode session).
4. **Throughput vs value:**
   - About 25–40 merges a day, but 0 released-line changes in 32 hours.
   - The checker is not the bottleneck: it merges 3–4 per run.
   - The bottleneck is (a) no integration lane and (b) owner release decisions on candidates.
5. **Duplicated or administrative work:**
   - the Lead's reporting set: PROGRESS, LEAD_REPORT, FEEDBACK, RESEARCH_REQUESTS for a disabled scout, agents.json;
   - hourly auditor reports;
   - hub reports.
6. **Track B dilution:** 17 product agents, mostly marketing and social, sit on the same board (up to 2 TODO slots).

## 9. Recommended organisation

| Role | Change | Why |
|---|---|---|
| Lead | Objective = released, verified BOQ coverage and accuracy (section 6 metrics), not task count. Keeps priorities, the dependency map and the release plan; drops FEEDBACK / RESEARCH_REQUESTS / agents.json duties; one daily owner report | it is a dispatcher today |
| Worker 1 → **Structural** | owns route G: concrete per element, rebar by bar population, formwork, excavation, blinding | rebar and formwork are the largest unmeasured money; one owner per module set |
| Worker 2 → **Architectural finishes** | rooms, floors, walls, plaster, paint, tiles, ceilings, openings, stairs finishes | most PROGRESS rows are here |
| Worker 3 → **Integration and release** | wires verified pieces into the next candidate method, regenerates the BOQ, runs the scoreboard, refreshes the family registry, keeps exports | the missing role (section 1.2) |
| Checker | unchanged gates; adds "re-run the scoreboard on every integration merge" and the verified-share report | measurement exists only when someone runs it |
| Auditor (this chat) | one daily executive report plus alerts only (owner's section 16); hourly ledger kept silently in RUN_LEDGER.md | owner asked for no noise |
| Hub report chain | retire (owner OK needed: it lives in another chat) | duplicate |
| Research scout | stays off; the Lead stops writing RESEARCH_REQUESTS | inactive |
| Track B product agents | pause, except a1 extractor, a2 reviewer and a7 quotation, which touch the BOQ | focus |

**Guards:**

- file ownership by module set (the "Files:" column plus specialisation);
- WIP limit of 3 READY at a time;
- no agent verifies its own work;
- the integration worker never invents quantities: it only wires checker-verified pieces.

## 10. Completion timelines (to M7, an owner-ready pilot)

**Basis:**

- 94 non-MEP families, of which about 8 are integrated and verified, about 30 have pieces, and about 56 have little
  or nothing;
- current integrated-and-verified throughput is about 0 families a week;
- the assumed throughput with an integration lane is 2–4 families a week.

| Scenario | Calendar | Assumptions | Confidence |
|---|---|---|---|
| Optimistic | 10–12 weeks (mid-January 2027) | M0 fixed this week; integration lane live in week 1; owner answers within 1 day; held-out villa available by week 6 | low |
| Base | 4–6 months (February–April 2027) | about 2.5 families a week; 1–2 owner decision packages a week; one rework cycle per family | medium |
| Conservative | 8–10 months | silent runs persist; scanned-drawing intake stays manual; no independent QS villa until late | medium |

**Effort split, base case:**

| Work | Share |
|---|---|
| Coding | about 45 % |
| Engineering reading and hand reference | about 35 % |
| Verification | about 20 % |

## 11. Milestones (current completion = estimate, with evidence)

| M | Now | Remaining / acceptance test | Main dependency | Fails if |
|---|---|---|---|---|
| M0 Reliable operation | ~40 % (cause found; fix tested in Manual mode) | Test B pass; 5 repo-attached tasks; ≥ 90 % SUCCESS over 48 h with STARTED and final lines | owner Test B plus task creation | auto mode still refuses the decode or pushes |
| M1 Drawing understanding | ~35 % (DXF strong; rooms 11 HELD; scans no) | 0 lost rooms or openings on two villas; heights from sections; scanned schedules read | plan reader | scans remain manual |
| M2 Structural BOQ | ~35 % (concrete integrated, -17 % on 3 lines; rebar, formwork, excavation absent) | concrete per element within 2 % of hand; rebar by bar population within 3 %; formwork and excavation lines | structural worker | rebar schedules unreadable |
| M3 Architectural BOQ | ~15 % (pieces; plaster / paint HELD) | room-by-room ledger for floors, walls, plaster, paint, tiles, ceilings, openings within 3 % of hand | owner heights (answered), integration | release path missing |
| M4 Waterproofing / procurement | ~55 % (floor +0.16 %; roofs released; rolls proven) | all areas plus upturns released; rolls equal to the hand-optimal count | owner release of the candidate | — |
| M5 Independent validation | ~5 % | held-out run (sealed benchmark / Qortuba / independent QS villa) with the section 6 metrics | owner provides the proof villa | no held-out data |
| M6 Integrated BOQ delivery | ~25 % (1455 lines, xlsx / pdf export) | one command → full BOQ with held items and evidence, all T1 trades present | M2–M4 | — |
| M7 Pilot | ~0 % | a real villa processed with ≤ 1 owner session, accuracy report attached | M5, M6 | — |

## 12. Plan for the next 7, 14 and 30 days

Plan items P-xx are converted by the Lead into board T- numbers. None needs an owner answer unless marked.

| Item | Agent | Objective | Deliverable / acceptance | Effort | Owner? |
|---|---|---|---|---|---|
| **7 days** | | | | | |
| P-01 | owner + auditor | M0: Test B, `main` config, Worker 1 migrated, then the rest | ≥ 90 % SUCCESS over 48 h | 1 day | **yes** |
| P-02 | integration (W3) | refresh BOQ_FAMILY_MASTER from code and releases (new version 1.1.0) | registry with evidence per family; the checker spot-checks 10 | M | no |
| P-03 | integration (W3) | build the candidate release V3.0 that wires every checker-verified piece (straps 3.390, dry floors, wet floors 72.12, skirting audit, facade run under Q-64/Q-67, pantry, 2F roof) | one opt-in method, scoreboard re-run, per-line before / after | M | release switch **yes** (one decision) |
| P-04 | checker | verified-share and weighted-accuracy report (section 6) on Alsenan | SCOREBOARD v2 with UNKNOWN share | S | no |
| P-05 | structural (W1) | blinding scope and phantom columns into route G (new method version) | blinding within hand range; columns −2.27 m3 | M | no |
| P-06 | Lead | one owner decision package a week; search drawings and rules before asking | ≤ 5 questions a week | — | — |
| **14 days** | | | | | |
| P-07 | structural | rebar by bar population from schedules (first footings / columns) | rebar lines with bar marks; hand check of 10 bars | L | no |
| P-08 | architectural (W2) | plaster and paint released by both methods (owner manual heights plus drawing-derived) | room table, both results, difference explained | M | no |
| P-09 | architectural | blockwork m2 by type (Q-60 / Q-69) | GF / 1F / 2F m2 and blocks; hand check | M | no |
| P-10 | structural | formwork and excavation lines from the element model | new lines, hand check on 5 elements | M | no |
| **30 days** | | | | | |
| P-11 | architectural | doors and windows as BOQ lines (schedule plus 2.20 m fallback) | doors / windows m2 and pcs | M | no |
| P-12 | integration | V3.x release with all T1 trades present; owner switch | full T1 BOQ | M | release **yes** |
| P-13 | checker + owner | held-out run on URBAN_BLIND_V2 or Qortuba, or an independent QS villa | first real accuracy figure | M | **yes** (authorise the sealed run / provide the villa) |

The parallel work is sized to the checker: at most 3 READY at once.

## 13. Top ten risks

1. Verified work never reaches the released method. This is happening now.
2. Silent scheduled runs persist after the repository fix.
3. No held-out accuracy data, so 95 % stays unprovable.
4. Rebar (the largest money item) is still unmeasured.
5. Method-version sprawl (16 versions) makes the "released" BOQ hard to reason about.
6. Owner-question load: 70 questions in about 3 days.
7. No single building model: cross-trade consistency is hand work.
8. Scanned and PDF-only drawings are not machine-read (window heights, schedules).
9. 396 baseline test failures (3.7 % of 10,689) mask real regressions, if they are not triaged.
10. Track B and reporting overhead dilute effort.

## 14. Owner decisions required (one package)

1. **Run Test B** (TEST_B_PROMPT.md) and, if it passes, approve the `main` configuration.
2. **Approve the reorganisation in section 9:**
   - specialise the workers;
   - move the auditor to daily reports;
   - retire the hub report chain;
   - pause Track B except a1, a2 and a7.

   This changes agent prompts, so it needs your word.
3. **Release policy:** may checker-verified pieces be wired automatically into one opt-in candidate (V3.0), with you
   approving only the switch of the default, at most weekly?
4. **Held-out data:** authorise a sealed-benchmark run (URBAN_BLIND_V2 / Qortuba), or provide one villa measured by an
   independent QS.
5. **Q-70** (2F stair arrival 4.875 m2: marble or porcelain).

Development continues meanwhile within existing authority (section 12, items P-02, P-04, P-05).
