# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since the commits below (`git -C .work/engine log a615fa41..`,
`git -C .work/board log <board commit of this run>..`, RUN_LOG lines after 04:11Z 6 Nov, rows changed since), then rewrite.

## Last seen
- engine: a615fa41 (T-542 / T-543 / T-548 / T-549 / T-544 / T-546 merges; candidate of record
  ARCH_TAKEOFF_V3.0.58 / BOQ_FAMILY_MASTER 1.55.0; released V2.9 + route G unchanged).
- main: eafbb0f6 (wrapper scripts/agent_env.sh UNCHANGED: run allows only the two tools).
- board: this run's final commit (Lead 2026-11-06 04:15)
- last Lead run: 2026-11-06 04:11-04:25 UTC (run session_01E6cPndHqMzEfYvgJfGJAPn)

## Run health
- Since 00:13 every run closed with a final line; 0 empty runs; 6 merged, 0 rejected, 0 blocked.
- CRITICAL (owner, notified 04:15 5 Nov, not re-notified): wrapper refuses research/agents_t*/ scripts -> every Gate B + T-525 blocked.
- tests/t485 still red on the working branch (T-507 stale pending in master 1.55.0).
- Worker 1 03:21: first venv install cut off by a status timeout ('No module named pytest'), re-ran setup: watch.

## Live rows (04:15)
- READY 0.
- TODO: S: T-545 beams vs freelancer, T-550 blockwork UNRESOLVED 101.43 m2 + H1, T-551 columns / footings vs freelancer;
  A: T-547 wet-room wall tile, T-552 plaster vs freelancer, T-553 floor tile vs freelancer; I: T-554 statement adapters
  (T-543 / T-546 / T-542 + F-C-T548-1 / F-C-T543-1 corrections), T-555 manifest V5.
- BLOCKED (wrapper): T-525 (W3), T-498 (W3, staged V3.0.59; resume carries T-507 promotion), T-423 r2 (W1).
- QUEUED: W1 T-424, T-364, T-363, T-372; W2 T-513, T-314, T-502; W3 T-509, T-382, T-474.
- IN PROGRESS: T-180 (Checker slot). PAUSED: T-450 part 2, T-451, T-472.
- Lane order: S (worker 1): T-545, T-550, T-551, T-423, T-424, T-364, T-363, T-372; A (worker 2): T-547, T-552, T-553,
  T-513, T-314, T-502; I (worker 3): T-554, T-555, T-525, T-498, T-509, T-382, T-474 (separator ';' - '|' breaks board check).

## Top 5 priorities
1. Wrapper allow-list (owner). The run after it lands: T-498 (with T-525 promotion) and T-423 r2 FIRST; T-513; wire from manifest V5.
2. 12-13 Nov: closed roof WP, blockwork, wet-room floor WP, stair bed; open beams, wall tile, plaster, floor tile, columns /
   footings, blockwork leftover; T-554 adapters before any milestone text; Q-34 raised with T-541 then.
3. Gate A in READY order, structural first. Next Lead run: if 1 or fewer TODO remain in a lane, add rows (candidates: paint vs
   freelancer, external plaster / facade, excavation / backfill vs freelancer, rebar tonnage vs freelancer, doors / windows count,
   T-474 part 2 scope split, lintel links kg basis).
4. 10 Nov: LOW (about 10 Gate B left in 4 days, none can start before the wrapper item).
5. When a package merges, promote its queued successor in the same Lead run (T-509 after T-498; T-424 after T-423).

## Rules decided (keep)
- Shared files: packages of different streams build in parallel; second READY rebases on the first merged candidate;
  version allotted at merge. One candidate package per worker at a time.
- Each worker keeps at least two non-candidate TODO behind its stream package while Gate B is blocked.
- Status word FIRST in the status cell; 7-cell rows; `board check` pulls first: commit before.
- 'merged' only when the commit reached the working branch through a merge (F-C-T443-1).
- Research scripts only through committed package tests or the wrapper (never bare venv python).
- A Checker finding that blocks a merge gets its fix row in the next Lead run, first in its lane.
- Register rulings: see ELEMENT_REGISTER (WET-ROOM MEMBRANE vs BEDS, MASONRY TIES AT COLUMN ENDS, RC LINTEL, LINTEL
  REINFORCEMENT / END VOLUME, FOUNDATION BACKFILL, TOP-STOREY WALL HEIGHT, STONE FLOOR, STAIR LANDING, POOL-COURT SLAB WP,
  STAIR SKIRTING, EXCAVATION ZONES, SKIRTING BEHIND JOINERY, GUARDRAIL vs BALUSTRADE, BAND-PATH PIER FACE).
- Lessons 06 Nov 04:15 ADOPTED: row unit label before column unit (R-T546-1); shared pier once (R-T544-1); reference-size
  error split from engine error (F-C-T548-1); partition his total by element family + carry datum dependency (R-T543-1).
  PROPOSED still: loss own account, printed values in DIMENSION blocks, end volume owned once, exact owner derivation.
- Materials: FINISH_MATERIALS_TABLE_V7 (stair treads 35.4313 m2; whole stair AT_LEAST 56.3586 m2 per T-542),
  PLASTER_MATERIALS_TABLE_V3; Q-45 5 % own account; sand = loose m3, tonnes / loads HELD (T-540).

## Blockers
- Wrapper allow-list (owner, main scripts/agent_env.sh). Designer items (D-27, D-33, D-35, D-39, D-43, D-45, lintel
  deficit ends, lintel bar ends) keep lines HELD, never block integration.

## Open owner items
- Wrapper allow-list (CRITICAL, notified 04:15 5 Nov).
- Q-80 15 cm black block face size (filed 00:16 6 Nov, owner package; 15 walls 175.9 m2 HELD).
- Kuwait 1990 spec over the connector limit (plastering chapter and 04220 unread) -> a copy under 6 MB.
- Repository privacy switch; released-path PyMuPDF decision (F-T465-1); PR #3 / merged-branch clean-up.
- Q-34 2F top roof: raise only at the 12-13 Nov milestone with T-541's reconciliation.
- Stage 2 of the token plan after 10 Nov. Scout paused (owner cadence 28 Oct).
