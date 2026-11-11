# T-698 WIRING READINESS of the merged-but-unwired missing families (worker 3, lane I, 2026-11-11; research only)

No quantity is produced, changed or wired. Candidate of record ARCH_TAKEOFF_V3.0.68 (line index d1de50cb, T-672 Gate B
PASS); released default V2.9 + route G untouched. Rule R-T698-1 (`t698_rules.py`, every villa); application
`t698_alsenan.py` (`--check` rebuilds and compares); outputs `out/T698_READINESS.json` (rows, census, membership,
hosts to restate) and `out/T698_ROWS.csv`. Pending packages read only through `in/PENDING_STAGES_T698.json`, which pins
the git blob ids of `agents/task-T-314:research/agents_t314/out/summary_t314.json` (040ed5f9, stage 080ccaa5) and
`agents/task-T-687:research/agents_t687/summary_t687.json` (6252bd8d, a8cf49c8); re-extract with
`t698_extract_pending.py`. ERS read: s.2.1 (element first), s.2.4 (reconcile by id and unit), s.3 (a notation's
meaning before its arithmetic), s.7 (lesson below).

## Rule R-T698-1 (summary)

Each ledger row names its host (line id, pending stage key, or a merged crosswalk key). Classes: MAPPED (host present,
same state as the reference index), HOST_CHANGED (host present, class / value / bound / unit moved: restate before
wiring, before and after quoted), MAPPED_PENDING_CHANGE (a pending package changes the host: wire after it),
MAPPED_PENDING_LINE (host exists only in a pending stage), STALE_ABSENT (id absent: never mapped by guess), WRONG_HOST
(wrong trade's line), AMBIGUOUS_HOST (a crosswalk key hits more than one line: split by carrier), NO_HOST (no line by
design, named with the stage's MISSING entry). Every ledger row in exactly one class (count reconciled); a mapped host
absent from the index fails the build (acceptance guard); HELD never becomes 0.

## Result by family (rows by class)

| family | ledger rows | MAPPED | HOST_CHANGED | PENDING_CHANGE | PENDING_LINE | NO_HOST | AMBIG. | STALE / WRONG |
|---|---|---|---|---|---|---|---|---|
| B4-04 ext. plaster (T-337 binding 109 + items 18) | 127 | 46 | 0 | 0 | 71 | 10 | 0 | 0 |
| B4-04 T-314 r2 stage lines | 18 | 3 | 0 | 0 | 15 | 0 | 0 | 0 |
| B4-05 spatter (T-349 binding 271 + pending 40) | 311 | 129 | 14 | 93 | 71 | 3 | 1 | 0 |
| B9-03 accessories (mesh 69 + sharmat 117 + joint 132) | 318 | 273 | 45 | 0 | 0 | 0 | 0 | 0 |
| B7-01 T-135 flights (disposition check) | 14 | 6 | 8 | 0 | 0 | 0 | 0 | 0 |
| B7-01 T-645 FIN.STAIR.FLIGHT fix rows | 14 | 14 | 0 | 0 | 0 | 0 | 0 | 0 |

## Per family: hosts, what moved, dependencies, census before / after

**B4-04 (T-314 r3).** The 3 FIN.EXT.FINISH hosts (GF / 1F / 2F facade) are byte-equal on V3.0.61 (stage base) and
V3.0.68; the 15 stage lines' ids are free in V3.0.68. V3.0.61 -> V3.0.68 changed 112 lines and added 32, none of them
FIN.EXT.* (masonry materials, concrete): r3 = re-run the stage on V3.0.68 and re-assert its outside rows; no restatement.
Census m2: before 3 lines HELD blank; after (stage) 18 lines = released 152.005 + HELD 855.926427 .. 933.607926
(13 bounded) + 1 blank. 10 item rows have no line by design (T-314 MISSING: corners 710.17 .. 821.86 m HELD, coping /
drip / bead accessory UNKNOWN, frame HELD, divider UNKNOWN, 4 WP upturn-zone faces HELD in the WP trade).

**B4-05 (T-364), after T-314 r3 and T-687.** 71 exterior rows rest on T-314 stage lines and 46 on the 3 facade lines
T-314 changes; 46 interior rows + 1 reveal (A-1F-01) rest on 11 FIN.PLASTER lines that T-687 changes (wire on its
after-state). 11
interior hosts moved since V3.0.45: the 4 dry-plaster lines of T-556 (1F_01, 1F_04, 2F_03, GF_15: RELEASED 217.2081 ->
HELD 262.018 .. 262.052 m2, plaster to the slab underside, Q-72) carry **217.2081 m2 of determinate spatter that must
be restated on the new height** (the spatter coat is under the plaster face, R-T349-2), + 7 HELD hosts whose bounds
moved. 3 window-out reveal carriers now hold less than the ledger (W15 / W16 0.62 -> 0.547688, W26 0.46 -> 0.40709 m2);
W02 out has 2 carriers (0.5064 valued + 1 HELD): split. 3 exterior items (frame / band / divider) have no line (T-314
MISSING). Census m2 (T-349 fill): INT 575.2519 det = 358.0438 ready + 217.2081 restate; EXT 386.530528 det = 351.830528
on T-314-changed hosts + 34.7 on stage lines; PENDING 13.597 = 11.3906 ready + 1.7 restate + 0.5064 split.

**B9-03 (T-363), independent of the plaster packages.** Wall -> MAS.BLOCK line crosswalk from the T-449 round 3
register (part line = parent element + '#BLOCKWORK:' + status + block type, arch_v3026), checked by sum over 19 part
lines: V3.0.45 17 CONFIRMED to 6 dp + 2 residuals named; V3.0.68 10 CONFIRMED, 6 not checkable (the 2F lines went
RELEASED -> HELD blank at V3.0.55, T-488 roof datum: 42 rows HOST_CHANGED, 2F mesh levels depend on the held wall
height), 3 residuals: GF-W22 left the GF 0.15 DC black line (21.5261 -> 8.595 = GF-W19 alone, CONFIRMED without it;
W22 on its HELD parent, CONFLICT D-27: 3 rows HOST_CHANGED) and two DC white lines that also carry register pieces with
no T-355 row (1F bay ends 0.572 + 1F-W25 1.49 = 2.062 m2; P-GF-05 above lintel 2.64 m2; same residual on V3.0.45):
named, no mesh row, their walls' rows stay MAPPED. Census: mesh strip 543.4739 m = 472.763698 ready + 70.710218 restate; sharmat 182 pcs = 152 + 30;
joint mesh owner band 511.6939 m = 442.199025 + 69.494844. All OPTIONAL lines apart from MAS.BLOCK m2.

**B7-01 (stair flight lm).** The T-135 rows map 1:1 to the 14 FIN.STAIR.FLIGHT lines through the T-645 crosswalk
(engine_flight). T-135's own dispositions are superseded on 8 flights by T-425 / T-438 / T-645 (e.g. 2F MS2-U was
SEEN_ABOVE in T-135, a real flight C_OPEN in T-645; GF RS-S split F2 / F3 now one flight 3.45 m2 / 11.5 lm): wire the
**T-645 fix rows**, not T-135 values (T-135 stays the once-only rule they respect). All 14 hosts still HELD blank =
T-645 before-state. Census lm: before 14 blank; after 5 RELEASED 13.36392 + 2 bounded (low 6.527061, MS2-U high OPEN)
+ 5 carried + 2 HELD by cause.

## Build order (by quantity at stake, then dependency; no rate applied)

1. T-314 r3 (B4-04): ready now on V3.0.68, after T-687 / T-693 hub slots (one Gate B at a time).
2. T-364 (B4-05): after T-314 r3 and T-687 MERGED; restate the 11 + 3 hosts first; W02 split.
3. T-363 (B9-03): independent; 273 rows ready; 2F rows stay HELD with their host until the roof datum resolves.
4. B7-01 wiring (new lane I row): 14 T-645 fix rows ready; small (13.4 lm).

## Limitations

The oldest committed line index is V3.0.45: a host change between a ledger's base (T-349: V3.0.24; T-337: V3.0.22)
and V3.0.45 is not visible here and is not claimed absent. The wall statuses come from the V3.0.44 register; where the
V3.0.68 line is HELD blank, membership cannot be checked by sum (stated per line).

## Lessons-register proposal (ERS s.7)

'2026-11-11 | a merged ledger keyed to an older candidate is wired by id without checking that its host kept its
state (T-349 interior spatter sat on 4 plaster lines that T-556 moved from paint height to slab soffit) | map every
ledger row to the target index first and class host moves (R-T698-1) | a readiness map with a test that fails when a
mapped host is absent, before any wiring package'.
