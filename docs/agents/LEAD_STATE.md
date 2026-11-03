# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since the commits below (`git -C .work/engine log 8d5612ce..`,
`git -C .work/board log <board commit of this run>..`, RUN_LOG lines after 08:13Z, rows changed since), then rewrite.

## Last seen
- engine: 8d5612ce (candidate of record ARCH_TAKEOFF_V3.0.45 5972888b; released V2.9 + route G unchanged)
- board: this run's final commit (Lead 2026-11-03 08:18, after 5e5d2c5c)
- last Lead run: 2026-11-03 08:13-08:25 UTC (run session_01E6cPnezoUfzNM45hMbnEvy)

## Open runs at 08:18 (check their final lines next run)
- Worker 3 STARTED 07:01 (T-419 CLAIMED 07:00). Worker 1 STARTED 07:20 (T-443 CLAIMED 07:21). No final line = INCOMPLETE.

## Live rows
- READY 0.
- CLAIMED: T-419 (worker 3, stream S), T-443 (worker 1, stream F).
- TODO 7: W1 T-482, T-484; W2 T-453 r2 (exact fix R-T453-5), T-454, T-455, T-486; W3 T-485.
- QUEUED: W1 T-483 (after T-443), T-480, T-423, T-424, T-310, T-314, T-364, T-363, T-372; W2 T-460 (after T-443 + T-483);
  W3 T-350 r3 (wiring, after T-419), T-487 (after T-453 r2 MERGED + T-350 r3), T-382, T-474 p2, T-468.
- IN PROGRESS: T-180 (Checker slot). PAUSED: T-450 part 2, T-451, T-472.
- Lane order: S (worker 1): T-443, T-482, T-484, T-483, T-480, T-423, T-424, T-310, T-314, T-364, T-363, T-372 |
  A (worker 2): T-453, T-454, T-455, T-486, T-460 | I (worker 3): T-419, T-485, T-350, T-487, T-382, T-474, T-468

## Top 5 priorities
1. Stream F: T-443 -> T-483 -> T-480 -> T-423 / T-424; 4 Nov review: if stream F delivered under 2 packages since
   08:18, move one of T-310 / T-314 to worker 2 under the merge-order rule (decide, then record).
2. Stream S: T-419 -> T-350 r3 (earthworks wiring) -> T-487 (lintel lines) -> T-382 -> T-474 p2.
3. Checker: Gate B T-419 / T-443 as they come; T-453 r2 Gate A; T-180 slot otherwise.
4. Materials: T-453 r2, then T-454 / T-455 (T-457 table V3 + UP-STAIR-017 folded into T-455); T-482 before blocks priced.
5. Registry: T-485 (38 unpromoted packages); T-486 balcony WP applicability.

## Rules decided (keep)
- Shared files: packages of different streams build in parallel; whichever is READY second rebases on the first merged
  candidate; version (candidate and BOQ_FAMILY_MASTER) allotted at merge. One package per stream at a time.
- Each worker keeps at least one non-candidate (research / tool) TODO behind its stream package.
- A worker run that skips its first-in-order stream package must state why in its final line (2026-11-03 04:15).
- Queue check treats any 'after T-nnn' / 'behind T-nnn' and list position as WAITING; write 'claimable now' where a row
  has no dependency. Status word first.
- `board check` pulls first: commit the edits before running it.
- Write stamps from `date -u` at the moment of writing (08:20 written ahead of the 08:18 clock this run, corrected to
  08:17 in the files; the two board commit messages keep 08:20).
- Element register rulings 2026-11-03: RC LINTEL vs host masonry (B9-02 owns the lintel; material base excludes
  REQUIRED faces); FOUNDATION BACKFILL displacement (B1-03 owns volume, buried elements only as displacement).

## Blockers
- None from the owner. Designer items keep lines HELD, never block integration.

## Open owner items
- Repository privacy switch; released-path PyMuPDF decision (F-T465-1); PR #3 / merged-branch clean-up.
- Stage 2 of the token plan after 10 Nov. Scout paused (owner cadence 28 Oct).
