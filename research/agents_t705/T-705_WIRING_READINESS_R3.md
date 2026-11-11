# T-705 WIRING READINESS ROUND 3 on ARCH_TAKEOFF_V3.0.70 (worker 3, lane I, 2026-11-11; research only)

No quantity is produced, changed or wired. Candidate of record ARCH_TAKEOFF_V3.0.70 (T-693 Gate B PASS, merge 2bfa2fbe;
`research/agents_t693/out/LINE_INDEX_V3_0_70.json` sha256 6c12da07); released default V2.9 + route G untouched. Rule
R-T705-1 1.0.0 (`t705_rules.py`, every villa) on top of R-T698-1 1.1.0 (applied unchanged); application `t705_alsenan.py`
(`--check` rebuilds and compares); outputs `out/T705_READINESS.json` (rows, classes, actions, hub order, line changes,
bead census) and `out/T705_ROWS.csv` (one row per ledger row). Inputs are merged repository files only (sha256 pinned);
the T-314 r2 stage is read through the T-698 pinned extract. No drawing opened. ERS read: s.2.1 (element first), s.2.4
(reconcile by id and unit), s.3 (a notation's meaning before its arithmetic), s.7 (lesson below).

## R-T705-1 (summary)

Short ids resolve only as a unique prefix (>= 8 hex), else STALE / AMBIGUOUS; a two-host row is AMBIGUOUS (split by
carrier); each row states its proposed after-state (VALUE / BOUND lo .. hi or OPEN / BLANK / ZERO_BY_GEOMETRY / no
proposal) and gets KEEP / CHANGE / ADD / NONE against the V3.0.70 line (6 dp); HELD never 0, a 0 only as a calculated
geometric zero; a host another piece of the round changes -> MAPPED_PENDING_CHANGE on that piece; every row names its
owner trade (register), one element one owner, and a face stage may carry no arris length (arris once); package size =
distinct changed lines + added lines.

## Result by piece (rows by class and action, on V3.0.70; stale 0)

| piece (merge) | rows | MAPPED | HOST_CHANGED | PENDING_CHANGE | NO_HOST | AMBIG. | CHANGE | ADD | KEEP | NONE |
|---|---|---|---|---|---|---|---|---|---|---|
| T-697 B4-09 beads (6ed575ad) | 185 | 99 | 20 | 49 | 16 | 1 | 0 | 116 | 0 | 69 |
| T-701 R-T701-2 (65083ee7) | 2 | 2 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 |
| T-702 tiles r3 (b90d85af) | 34 | 29 | 0 | 0 | 5 | 0 | 7 | 0 | 22 | 5 |
| T-691 WP r2 (5e4fdc33) | 25 | 21 | 0 | 0 | 4 | 0 | 20 | 4 | 1 | 0 |
| T-700 earthworks r2 form (8210b549) | 21 | 20 | 0 | 0 | 1 | 0 | 8 | 1 | 12 | 0 |
| T-695 census (bbda7212) | 20 | 20 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 20 |

T-695: all 20 lines are restated in the T-700 form (one count; T-695's census state is the before, T-700's the after);
its strap trench enters through T-700 (B1-02 Z1-TRENCH-STRAPS 9.950299 .. 16.121241 m3 cut, B1-03 split line 6.437519 ..
10.952471 m3 fill). T-702 NO_HOST 5 = stair-core surfaces with no line of their own (MS1-T tread family; MS1-LD 1.4375,
MS2-LD 2.9325, 2F arrival 4.865, RS-LD 1.3525 m2: the T-493 B7-04 proposals, still unwired, outside this round).

## B4-09 corner beads (T-697) -> V3.0.70

- Census (equals the T-697 summary to 6 dp, test): interior 79 bead rows = 285.03 m.l measured (owner method G1,
  F-T697-1 CONFIRMED) + 3 HELD bounded 14.4528 .. 14.8528 + 11 HELD blank; exterior 51 rows = 310.6831 m.l + 3 HELD
  bounded 2.1 .. 15.65 + 11 HELD blank. 52 NOT A BEAD rows and 3 lift arrises (B6-06, owning lines L-b66b8e76 /
  L-d788f643 / L-fdbd9636 present in V3.0.70) yield no B4-09 quantity.
- 116 rows ADD one lm line per host: 14 interior hosts (FIN.PLASTER) + 4 exterior (3 FIN.EXT.FINISH + ARCH.FACADE
  L-c0e9a4c6). 20 interior rows HOST_CHANGED since V3.0.68 (T-687 bounded 9 plaster hosts, e.g. L-0eac839f 42.48 .. 47.67
  -> 45.317 .. 46.564 m2; L-3f7fb1b3 / L-a636dabc blank -> 11.4 .. 25.21 / 7.04 .. 19.555): the bead lm does not move
  (G1 height), only its host's state is restated. 7 interior rows wait on H1 (GF-01 / GF-04 hosts re-bounded by
  R-T701-2); 42 exterior rows wait on T-314 r3 (the 3 facade lines it changes). D-1F-02#1F-13|ST-1F 5.40 m.l names two
  carriers: split before wiring.
- Arris once (ruling 08:25, F-T697-3 CONFIRMED): the T-314 r2 stage (18 rows) carries face m2 only (check PASS); its
  MISSING item 'FIN.EXT.CORNERS (all floors)' 710.171878 .. 821.8588 m.l is the same arrises as B4-09 exterior 310.6831:
  never wired by T-314.

## Ordered hub packages (after T-704 concrete r8 READY and T-703 masonry r4 QUEUED; owner order 2026-11-09)

| # | package | changed + added lines | depends on / restate first |
|---|---|---|---|
| 3 | H1 PLASTER: T-701 GF-01 61.46433 .. 65.25433 -> 47.960668 .. 66.26068, GF-04 43.155 -> 34.33 .. 43.78; T-702 bands GF-07 2.853686 .. 6.918815 -> 0.499037 .. 6.186806, GF-14 5.05488 .. 5.29088 -> 3.892324 .. 5.005988 m2 | 4 + 0 | restate F-T709-1 (GF-01 W12 4.290 -> 4.300824: both ends -0.010824 m2) and F-V702-1 (GF-14 0.282868 -> 0.282843 m) first |
| 4 | H2a B4-09 interior beads, 285.03 m.l + held | 0 + 14 | after H1 (GF-01 / GF-04 hosts) |
| 5 | T-314 r3 exterior faces (m2 only) | 3 + 15 | queued |
| 6 | H2b B4-09 exterior beads, 310.6831 m.l + held | 0 + 4 | after T-314 r3 |
| 7 | H3 TILES: GF-10 blank -> 11.40 .. 25.21, GF-11 blank -> 7.04 .. 19.555 m2 | 2 + 0 | - |
| 8 | H4 WP + roof build-up: roof 2F 115.832 -> 115.65646 .. 115.81396 m2, upturn 92.922 -> 92.925 lm, L-8090ff20 blank -> 1.40 .. 1.90 m2, 17 penetration lines blank -> 18 .. 30 pcs (5 MEASURED 1; + pantry FD = T-691's 19 .. 31), 3 falls screeds blank -> AT_LEAST 3.324832 / 4.791492 / 2.512672 m3; ADD pantry termination 4.50 lm, doorway 0.20 m2, transition 1 pcs, pantry FD 1 pcs | 23 + 4 | Gate B hand-checks the 3 AT_LEAST lows (merged without a Checker re-measure) |
| 9 | H5 EARTHWORKS: T-700 form: lift pit cut >= 31.05 / fill >= 12.688, annex 0.877899 .. 21.407259, straps 9.950299 .. 16.121241, Z2 136.900995 .. 163.479489 m3, 3 lines ZERO_BY_GEOMETRY, B1-03 strap split ADD 6.437519 .. 10.952471 | 8 + 1 | material balance B1-04 stays HELD (5 soil tests named) |

## Findings for the Lead / Checker

- **F-T705-1 (register wording, Lead).** All 116 bead lines rest on HELD hosts (every bead host is HELD bounded on its
  height band, not on its existence). Ruling 04:20 'HELD where the plaster face itself is HELD' read literally would hold
  the whole 595.7131 m.l although the bead length at G1 does not depend on the soffit band (F-T697-1 CONFIRMED). Proposed
  reading: a bead is HELD only where its face's EXISTENCE is held (RFI / no host), not where only the face height is
  bounded; the Lead rules before H2a.
- **F-T705-2 (class, Gate B).** T-691 states the 2F roof membrane as OPEN_BOUND 115.65646 .. 115.81396 (D-band 0.1575 m2
  unprinted), so wiring it as stated moves a RELEASED line (115.832) to HELD; the D-band was already beside the released
  value before T-691, and T-691 corrected only the dome discs (-0.01804 m2). The package must state which class it wires
  and why (released 115.81396 with the D-band beside, or HELD band); this map carries the ledger as stated.

Lessons row (ERS s.7, proposed): 2026-11-11 | a readiness map of several pieces at once | the pieces chain through
shared hosts (beads on plaster lines that a plaster piece re-bounds; beads on facade lines T-314 changes) and a
'missing' item of one stage is another family's element | map all pieces of a round together, mark rows whose host
another piece changes as PENDING on it, and check arris / element ownership across stages before ordering the hub |
tests/t705_wiring_readiness_r3 | PROPOSED.

Tests: tests/t705_wiring_readiness_r3 (synthetic villa W705 by hand: unique / shared / short prefixes, two hosts, every
after-state kind, 6 dp, adverse: value 0, inverted bound, blank with a number, unknown kind, held as 0, bead on a roof
line, element with two owners, arris lm in a face stage; development villa: rebuild equal, stale 0, host-removal guard,
rows once, held without quantity, owners named, bead census = T-697 summary, pending chains, hub sizes, known changes).
