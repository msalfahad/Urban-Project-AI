# LEAD STATE (at most 5 KB; the Lead rewrites it at the end of every run)

Next Lead run: read this file, then only what changed since the commits below (`git -C .work/engine log 4aaa9be0..`,
`git -C .work/board log <board commit of this run>..`, RUN_LOG lines after 12:24Z, rows changed since), then rewrite.

## Last seen
- engine: 4aaa9be0 (candidate of record ARCH_TAKEOFF_V3.0.42 json 1793266d; released V2.9 + route G unchanged)
- board: this run's final commit (Lead 2026-11-02 12:35, after b138050a)
- last Lead run: 2026-11-02 12:24-12:40 UTC (session_01E6cPndAGwkDktsTpnqxF4W)

## Live rows (READY 0, CLAIMED 0 at 12:35)
- TODO 9: worker 1 (stream F) T-422, T-475, T-445; worker 2 T-477 (gate fix), T-471 (EIMP part 2), T-465 r3, T-464;
  worker 3 (stream S) T-350, T-474 (part 1)
- IN PROGRESS: T-180 (Checker standing slot)
- PAUSED: T-450 part 2, T-451, T-472 (recovery plan)
- MERGED rows kept open for acceptance: T-449 (wiring, round 3), T-459 (wiring in T-382)
- Lane order (board note 12:30): W1 T-422, T-475, T-445, T-443, T-476, T-423, T-424, T-310, T-314, T-364, T-363,
  T-372, T-452, T-449, T-457 | W2 T-477, T-471, T-465, T-464, T-466, T-383, T-461, T-460, T-448, T-453..T-455 |
  W3 T-350, T-474, T-353, T-419, T-382, T-468

## Top 5 priorities
1. T-471 EIMP part 2 on EIMP_SCOPE_2026-11-02.md (worker 2; Checker-validated by 8 Nov).
2. Stream S T-350 earthworks Gate B, then T-353 / T-419 / T-382 (+T-459 lap rule) / T-474 part 2.
3. Stream F T-422 skirting release (rebases after T-350 merges), then T-443 ...; re-check on 4 Nov whether to pull the
   missing categories (T-314, T-364, T-363, T-372) ahead of T-423 / T-424.
4. T-477 gate fix (firewall declarations) so the working head is green.
5. T-180 closures (concrete -> rebar -> blockwork) with independent sums; restate T-132 after the next quantity merge.

## Rules decided this run (keep)
- Shared files (tools/urban_boq_m9.py, BOQ_FAMILY_MASTER next version, BOQ export) are held by T-350 until it merges;
  stream F builds without them and adds its registration in the rebase commit. Version number allotted at merge.
- Queue check reads 'after T-nnn' anywhere in the status cell (history too): write history as 'behind T-nnn'.
- Write stamps from `date -u` at the moment of writing (two slips this run, corrected before commit).

## Blockers
- None from the owner. Designer items keep lines HELD, never block integration.

## Open owner items
- Repository privacy switch; released-path PyMuPDF decision (after T-465 r3); PR #3 / merged-branch clean-up.
- Stage 2 of the token plan after 10 Nov.
