# T-730 WIRING READINESS ROUND 5 on ARCH_TAKEOFF_V3.0.73 (worker 3, lane I, 2026-11-12; research only)

No quantity is produced, changed or wired; no candidate, hub, registry, rule / knowledge version file is touched; no
drawing opened. Candidate of record ARCH_TAKEOFF_V3.0.73 (T-722 Gate B PASS, merge 931dc8d9,
`research/agents_t722/out/LINE_INDEX_V3_0_73.json`); released default V2.9 + route G untouched. Rule R-T730-1 1.0.0
(`t730_rules.py`, every villa) on R-T723-1 / R-T705-1 / R-T698-1 (applied unchanged); application `t730_alsenan.py`
(`--check` rebuilds and compares); outputs `out/T730_READINESS.json` (rows, classes, actions, blockers, hub order,
formwork / concrete census) and `out/T730_ROWS.csv` (1,174 rows). Inputs: merged repository files only, sha256-pinned,
plus `in/T717_PENDING.json`, the pinned extract of the READY T-717 package (`t730_extract_t717.py`, commit 9b998fc8:
4 lines changed, 32 added on V3.0.74). Beside register rebuilt: concrete rounds 1 .. 8 (T-723 replay) + round 9
(merged `t722_inputs.build()`: 10 AT_LEAST, 5 NARROW, 18 NAMED, 21 confirms incl. 3 V3.0.23 parapet figures) + the
18 masonry one-ended figures of T-703 (`t703_inputs.build()`): 40 lines on V3.0.71 -> 68 on V3.0.73.
ERS read: s.2.1 (element first), s.2.4 (reconcile by id and unit), s.3 (a cap is not a range), s.7 (lesson below).

## R-T730-1 (summary; full text in the module)

(1) WIRED: a restated row whose after-state the candidate now carries (index; beside register; a merged package's named
record for a cause-only row) moves nothing and is never wired again. (2) CONFLICT carried: two merged pieces, different
after-states, no supersession declared -> every row on the line CONFLICT with a named decider, only when the line is in
the declared register (else the build fails, R-T723-1 rule 4). (3) FORM RESTATE: a cap on a 0 .. x line is a CHANGE only
under a merged rule saying a 0 low is no floor (R-T724-3). (4) CAP: a capped blank is ONE_SIDED AT_MOST; a cap of 0 is
refused (BLANK + CAP_ZERO). (5) ARRIS restatement: a derived ledger supersedes the earlier one arris by arris (same arris,
same host, none lost / added). (6) BLOCKERS per row; a designer item under a HELD-blank add is its cause, not a blocker.
(7) IDS: unique prefix >= 8 hex or full id; an absent id fails, never re-mapped to a neighbour.

## (1) T-723 map restated on V3.0.73 (633 rows; stale 0)

Line ids of V3.0.71 / .72 / .73 are the same 5,123 (asserted). Classes: MAPPED 521, HOST_CHANGED 66 (index entry 15 =
T-703 10 masonry ranges + T-722 5 column lows; beside record 31), PENDING on T-717 11, NO_HOST 34, AMBIGUOUS 1.
**36 rows WIRED by T-722** (18 moving + 18 cause-only; still moving on that hub: none); the 95 T-713 rows no longer pend
on T-703 (KEEP / statements); 116 T-697 bead ADD rows SUPERSEDED by T-728 (the RULING_RESTATE flag is closed).

## (2) Pieces merged since T-723 (541 rows; stale 0)

| piece (merge) | rows | actions | live | hub |
|---|---|---|---|---|
| T-714 formwork bounds (e6ebe28a) | 370 | CHANGE 80 (26 BOUND + 54 fix-row values), BESIDE 90 (32 AT_LEAST + 58 caps), TEXT 200 | 353 (13 CONFLICT, 4 SUPERSEDED by T-724) | T-729 |
| T-724 Checker findings (cfca9394) | 10 | CHANGE 5 (4 soffits + L-fb7a6431 form), ADD 4 strip children, KEEP 1 (ring) | 9 | T-729 / C10 |
| T-725 stair formwork (b20fe25c) | 20 | CHANGE 2, BESIDE 14, TEXT 4 | 18 (2 SUPERSEDED by T-731) | T-729 |
| T-726 shaft residual (63720169) | 15 | 14 statements (lines carried ONCE), 1 no-line (his 13.50) | - | - |
| T-727 V-01 (8ea912b5) | 6 | CHANGE 1 (L-35341ff2 EXCLUDED DUPLICATE_FACE), 5 statements | 1 | H1R |
| T-728 beads (80e27c10) | 116 | ADD 116 (73 interior -> 14 lines, 43 exterior -> 4 lines) | 116 | H2a / H2b |
| T-731 MS1-L (e9878f39) | 4 | RESTATE_BESIDE 1, CHANGE 1, BESIDE 2 | 3 (1 DUPLICATE of T-725) | C10 / T-729 |

T-719 (void register: the band prerequisite T-717 consumed; its two findings closed by T-727) and T-720 (gross area
B2-03: GF 278.266291, 1F 209.839104, 2F 55.08 m2) carry no candidate line.

## (3) Hub order (owner order 2026-11-09: concrete first; one Gate B package at a time)

| # | package | rows | changed | text | added | state |
|---|---|---|---|---|---|---|
| 1 | T-717 plaster / paint H1 (READY, V3.0.74) | 36 | 4 | 0 | 32 | Gate B pending; nothing else to add |
| 2 | C10 concrete round 10 (no row) | 7 | 2 | 0 | 4 | **buildable in one run**: L-fb7a6431 capped blank 3.5256, L-7863355d 1.213429 -> 1.213428, 4 strip children HELD blank |
| 3 | T-729 formwork H5f (QUEUED) | 410 | 186 | 191 | 0 | BLOCKED: 13 lines CONFLICT (decider T-732) + 39 rows on 34 moved members WAIT T-732 |
| 4 | H1R ceiling round 3 (no row) | 1 | 1 | 0 | 0 | buildable (one EXCLUDED; fold into the next finish package) |
| 5 | H2a interior beads (no row) | 207 | 0 | 0 | 14 | buildable after T-717 (4 rows on GF-01 / GF-04 hosts) |
| 6 | H2b exterior beads | 94 | 0 | 0 | 4 | BLOCKED: 42 rows WAIT T-314 r3; 1 plinth row HELD blank (D-62) |
| 7 | H3 tiles (T-702) | 2 | 2 | 0 | 0 | buildable; T-733 (READY) may restate the tile list |
| 8 | H3s stair finishes | 92 | 81 | 3 | 1 | 27 rows RULING ORR-007; 2 tread lines PENDING T-733 |
| 9 | H4 WP + roof | 99 | 26 | 10 | 5 | BLOCKED: WAITS T-734 |
| 10 | H5 earthworks | 41 | 8 | 7 | 1 | BLOCKED: WAITS T-708 |

Census projections (run-record only; sums per state, never across states). STR.FORMWORK (614 lines) after T-729 as
mapped: released 1,027.977403 -> **1,061.104461 m2** (+33.127058 = T-714 fix rows exactly), bounded 26 lines **87.942377
.. 103.192739** (T-714 + T-724 +0.001093), AT_LEAST beside 32 lines 98.543697, caps beside 58 lines 59.379875, blank 200
(13 conflict lines stay blank). STR.FORMWORK.STAIR: released 36.927436 unchanged; bounded 2.583193 .. 3.223465;
AT_LEAST 7.872094 (lows 10.455287 = T-725); caps 12 lines 6.261899. Concrete after C10: GROUND_BEAM bounded 9 -> 8,
high 5.096771 -> **1.571171 m3**, cap 3.5256 beside (= T-724 / T-704 code form); STAIR AT_LEAST 1.568446 -> 1.568445;
released m3 moves on no code.

## Findings for the Lead / Checker

- **F-T730-1 (conflict, 13 column formwork lines).** T-707 (merged first) bounds them by perimeter x h (e.g.
  L-fa037ca1 5.5926 .. 7.362 m2); T-714 (merged later, built on V3.0.70) states 'no positive floor' (BLANK) and
  declares no restatement of T-707. Neither is picked: CONFLICT, decider T-732 (its scope covers all 13). T-729 wires
  them only after T-732 states the face-by-face form.
- **F-T730-2 (cap 0).** T-714 L-867e155d (1F-072 beam side, one face 0 .. 0) carries cap 0.000000: a 0 cap states the
  quantity as 0. Carried BLANK + CAP_ZERO; T-729 states ZERO_BY_GEOMETRY with the drawing evidence (no downstand) or
  re-measures.
- **F-T730-3 (tread lines).** T-715 proposes EXCLUDED for L-6cf11c2d / L-ea55ed31 while T-727 names a 0.057439 m2
  double count in their highs (7.544413 vs union 7.486974); consistent only if EXCLUDED holds; T-733 (READY) closes it.
- **F-T730-4 (moved members).** 34 concrete members moved since V3.0.70 (T-707 / T-722 lows, T-711 / T-712 / T-721
  floors, parapets): 39 T-714 formwork rows rest on them = T-732's scope; T-729 should not wire those before T-732.
- **F-T730-5 (B2-03).** T-720 has no line target: a coverage-registry denominator (lane I); the Lead decides whether
  BOQ_FAMILY_MASTER records B2-03 as a family without a BOQ line.

## Checker Gate A sample (10 rows by id; expected on an own V3.0.73 run)

T-724:L-fb7a6431 CHANGE (FORM_RESTATE, cap 3.5256) | T-731:L-7863355d RESTATE_BESIDE 1.213429 -> 1.213428 |
T-731:L-9c3643da CHANGE 0.679193 .. 0.843465 (T-725 SUPERSEDED) | T-731:L-d9790e45 BESIDE cap 0.862807 |
T-724:L-3280c42c CHANGE 3.559782 .. 3.733233 | T-727:L-35341ff2 CHANGE EXCLUDED | T-707:L-fa037ca1 CONFLICT (T-732) |
T-714:L-867e155d TEXT, CAP_ZERO | T-707:L-53f223b0 WIRED (index 0.45738 .. 0.595) | T-728:D-GF-01#GF-01 ADD
B4-09@L-b1529955, PENDING_ON T-717.

Lessons row (ERS s.7, proposed): 2026-11-12 | a later merged piece restated 13 lines an earlier merged piece had bounded,
without declaring it, and a cap of 0 entered a ledger | a map that keeps 'one live row per line' by failing could not be
built at all; a cap of 0 reads as a quantity of 0 | carry an undeclared conflict as CONFLICT with a named decider (never
pick), refuse a 0 cap as a cap, and mark rows a merged package already wired so no package wires them twice (R-T730-1,
every villa) | tests/t730_wiring_readiness_r5 | PROPOSED.

Tests: tests/t730_wiring_readiness_r5 (44): synthetic villa W730 by hand (wired by index / beside / named record, keep and
statements never wired, form restate with / without rule, adverse non-zero low; caps incl. 0 and negative; ids: unique
prefix, adverse missing id with a same-element neighbour, short, ambiguous; carried conflict, adverse unlisted / untrue
conflict, supersession in mirror order; arris restatement with adverse lost / added / moved / doubled arris; blockers;
buildable; package size) and the development villa (rebuild equal, pins, stale 0, rows once, piece counts, T-722 rows
wired, hub sizes and blockers, census deltas = ledger totals, supersessions, the carried conflict, form restate, cap 0,
held never 0, adverse missing id and unregistered conflict on real rows).
