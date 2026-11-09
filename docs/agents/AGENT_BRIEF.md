# AGENT BRIEF (every run reads this; everything else is reference only)

Owner directive 2026-11-02 (token plan, Stage 1). This file is at most 6 KB and holds what changes rarely. For the
long documents, grep the section you need; never read one whole. Owner words win over this brief. The authoritative
text is in MISSION.md, OWNER_QUESTIONS.md (answered index) and OWNER_SESSION_CHANGES.md.

## Goal and priorities (owner-approved recovery plan, MISSION top section)
- Goal B: a complete, priced BOQ for ANY Kuwait villa from its drawings, with no freelancer takeoff. The training villa
  is the development benchmark, not the target.
- Delivery first. Critical path:
  1. T-471 EIMP + component register
  2. integration in two streams: S structural (Worker 3), F finishes (assigned by the Lead)
  3. T-469 released-concrete statement + all-trade aggregation
  4. T-180 independent closures
  5. materials (T-448, then T-453..T-455)
  6. T-452 / T-449 for the blind test
- PAUSED: T-451, T-472, T-450 part 2, research-only rows with no line target.
- Milestones:
  - 10 Nov: end-to-end BOQ with every trade.
  - 12-13 Nov: reconciled quantities + scorecard.
  - 19-20 Nov: blind test, only when ready.
  - 25 Nov: earliest production decision, not a release.
- Blind test: a genuinely unseen villa. Its first-pass output is frozen (hash on the board) before any reference is
  opened; it is scored once with no tuning. The exposed benchmark villa is regression-only.

## Hard rules (one line each)
- No assumptions. Resolution order: drawings -> governing revision -> project requirements -> OWNER CONFIRMED company
  rules -> documented estimating method (labelled ESTIMATED) -> escalate only genuine contradictions or missing
  safety-critical design.
- HELD, missing or unresolved is never 0 and never silently dropped. An estimate is never VERIFIED.
- VERIFIED needs an independent re-measure AND aggregation proof (component -> line -> subtotal -> total).
- Never edit a frozen file or an existing rule / knowledge version file; a behaviour change is a new version.
- Never switch the released default (V2.9 + route G). Never release an unverified quantity.
- No client data, names, drawings or personal data in the repo; Drive is read-only.
- Times come from `date -u`, never typed by hand.
- RFIs never block integration; affected lines stay unverified.

## OWNER CONFIRMED rules (id | value | source)
| id | value | source |
|---|---|---|
| Lintels | precast 1.20 / 1.50 / 2.50 / 3.00 / 4.00 m; minimum 15 cm bearing each side; the shortest standard length that fits (masonry opening + 2 x bearing); one per opening, in pieces; an opening needing more than 4.00 m is FLAGGED (cast-in-situ or design) | owner 2026-11-02 |
| Tile adhesive | 20 kg bag: normal tiles incl. 60x60 5 m2; 120x60 3 m2; 160x80 3 m2; ceil per purchasing group; waste separate | Q-45, owner 2026-11-02 |
| White AAC glue | 25 kg bag: 15 cm block 3.5 kg/m2, 20 cm block 4.5 kg/m2 | owner 2026-11-02 |
| Black-block mortar | 1:4 (about 8 x 50 kg cement + 1.1 m3 sand per m3) | Q-78 |
| Plaster / render / spatter mix | internal plaster 1:4, external render 1:4, spatter dash 1:2 (cement : sand) | Q-79, owner 2026-11-09 |
| Rebar by ratio (this BOQ) | member WITHOUT detailed bar takeoff: kg = its concrete m3 x kg/m3 of its element type (footing, tie / ground beam, column, beam, slab, stair, pool / tank wall), + 3-5 % laps and offcuts; kg/m3 owner-given or calibrated from this villa's counted members (counted kg / m3 per type), checked against common ranges and shown; never both ways on one member; label ESTIMATE - owner-approved ratio, never VERIFIED; detailed and ratio subtotals separate | owner 2026-11-09 (overrides "never approximate steel" for this BOQ) |
| Black blocks | 12.5 per m2, 40 x 20 face, for both 20 cm and 15 cm blocks (CONFIRMED); waste separate; report any drawing that shows another face | Q-75, Q-80, owner 2026-11-07 |
| Wet-area walls | spatter dash (plasterer) + levelling render (tiler) + adhesive and porcelain; no second fixing bed; no paint or skirting on tiled faces | owner 2026-11-02 |
| Heights | plaster to the structural slab / roof underside; paint to the finished ceiling; stair shafts at full exposed height | Q-72, owner 2026-11-02 |
| Openings | full deduction of every actual opening from blockwork | Q-73 |
| Tile bed | 3-4 cm floors, 4-6 cm bathrooms, 1:4 | Q-45 |
| Backfill lift | maximum 150 mm finished compacted lift, foundation-adjacent backfill, OWNER-PROVISIONAL; project drawings, geotechnical spec or an approved method govern where they differ; 95 % Modified Proctor is NOT adopted (proposed only) | owner 2026-11-02 18:00 |
| Bars per metre / spacing | drawing-based counting (spacing, first-link offset, support face, zones); also for footings | Q-71 |

This table is a summary, not a source of truth. The authoritative register of every answered owner decision (78,
checked complete 2026-11-02) is OWNER_QUESTIONS_ANSWERED.md: grep your task's topic or Q-id there. Read only the Open
section of OWNER_QUESTIONS.md.

## Checker gates (full text in the Checker prompt)
- Gate A (piece): no frozen or version-file edit, no weakened test, no client data; targeted tests pass; freeze 0;
  codemap clean; an independent re-measure from the drawing.
- Gate B (integration): one package at a time, rebased on the latest candidate, every other line byte-identical,
  plus a hand check of every material line.
- A line is VERIFIED only when every component is re-measured and summed independently; otherwise PARTIAL n/m.

## Lead duties
- Rank work by the recovery plan.
- Write tasks with files and rules already named. Refuse rows that move no BOQ line.
- Run `board check` and fix every flag.
- At the end of every run, rewrite LEAD_STATE.md (at most 5 KB): run time, the engine and board commits seen, live
  rows with age, top 5 priorities, blockers, open owner items. The next run reads LEAD_STATE.md plus only what changed
  since those commits.

## Report limits (owner 2026-11-02, from today)
- Worker handoff: at most 600 characters; full calculations, tests and evidence stay in the task's artifacts. The
  Checker flags a longer handoff; length alone never invalidates verified engineering work.
- Lead report: at most 20 lines.
- Owner package: at most 5 items of at most 10 lines.
- Owner question (only when the resolution order cannot settle it), at most 10 lines: issue, options, recommendation,
  what stays HELD.

## Drive (read-only)
- "Urban BOQ private data": 1d24LO1eVm_g3mMtQzO4j4rzvh0VdPUsm
- Training villa folder: 1pemtCruL2WCXORJxst7Wc2Cesd1C4CXl
- Reference books: 1AHjEuvxGd7DoMSiDs0CRfKVmXtISqmd0 and 1rr88a1tiLBnABebjhuUk_sfNxsYuCaIE
- Decode only with `bash scripts/agent_env.sh decode`.
