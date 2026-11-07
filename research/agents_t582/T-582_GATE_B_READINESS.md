# T-582 GATE B READINESS for T-498 and T-423 r2 (F-T580-1 .. 5)

Worker 3, lane I, 2026-11-07, non-candidate (backlog-permitted). Nothing wired: no candidate, released (V2.9 + route
G), rule, knowledge or registry file touched; no drawing read (every figure from committed, Checker-merged sources).
Files: `t582_readiness.py` (R-T582-1), `out/T582_READINESS.json`, `tests/t582_gate_b_readiness/` (18).
Rebuild: `python3 -I research/agents_t582/t582_readiness.py` (`--check`).

## 1. F-T580-1: a quantity class per lintel row (16 STR.CONC.LINTEL lines, PROJECT_RC)

Physical element: one cast-to-length RC lintel over each of the 16 REQUIRED openings (T-571 count 16 / 16, 1 nr each).
The class is read from the source state (V2 stream_S, i.e. the merged T-516 bearing verdict), one fixed map:
MEASURED / PROVISIONAL -> RELEASED; BOUNDED_MIN_BEARING -> AT_LEAST; HELD_BY_NAME -> HELD. It is not chosen for a
larger or smaller total: T-516 (Gate A, 35db84c3) finds no built bearing printed anywhere (MEASURED never reached), the
printed MIN 0.40 m is the LOW end on the 6 BEARING_OK lintels and not buildable on the 10 deficit ones.

| Class | Lines | On the line | Beside |
|---|---|---|---|
| RELEASED | 0 | - | - |
| AT_LEAST | 6: D-1F-02, D-1F-08, D-2F-01, D-GF-13, W14, W15 | HELD, low 0.502 m3 = B x D x (w + 0.80); high 0.74642 m3 on 5 + D-2F-01 OPEN | - |
| HELD | 10: D-1F-03/04/07/10, D-2F-03, D-GF-06/10/11/12, W18 | HELD blank | T-524 bounds: 8 per lintel + D-GF-11/12 pair once = 0.372692 .. 0.437542 m3 (= T-524 set, residual 0) |

Released lintel concrete 1.016 -> 0.000 m3 (-1.016 m3, -100 %); the 0.502 m3 low is never added to a released total and
no HELD line prints 0. Evidence: AT_LEAST lows DRAWING-CONFIRMED (printed MIN, piers measured), highs pier-bounded;
HELD = designer item (T-516 RFI). Freelancer: no lintel concrete row (T-571 Checker read): NOT_COMPARABLE, no %.
D-GF-11 / 12: V2 carries no per-lintel bound (shared 0.238 m pier); the T-524 pair bound 0.060 .. 0.07914 m3 sits
beside both lines and is summed once.

## 2. F-T580-2: T-498 stage identity on V3.0.58

Branch e3e2ebb5 still prints method V3.0.58 / extends V3.0.57 / base 4,994. Regenerated: ARCH_TAKEOFF_V3.0.59 extends
V3.0.58, base 4,999 (4,994 + 5 T-507), added 74, replaced 0, expected 5,073; the 74 ids are disjoint from the base, all
host lines are on V3.0.58, no T-507 line hosts a stage row, no stage row duplicates a live line. Line ids do not move:
`boq_line.line_id()` hashes project, code, element, rule id / version and unit, never the candidate version.
BLOCKED part: outside_rows_sha256 / the full V3.0.59 run table need the branch runner
`research/agents_t498/v3059_run.py`: `AGENT_ENV FAIL: run allows only tools/alsenan_scoreboard.py or
tools/alsenan_keymap.py`. Left to the T-498 package / the wrapper allow-list (owner item).

## 3. F-T580-3: L-4ccc5dc2 before

2F MAS.GLUE.AAC on host L-bbb82de2 (2F block line HELD, D-39). Before = HELD blank (the T-498 stage row that adds it is
BLOCKED_RFI); after = HELD blank; beside conditional 63.82125 .. 71.62425 kg (V5). Quantity moved 0.

## 4. F-T580-4: T-423 r2

24 lines (22 text-only + 2 set aside), every one addressed by line id AND element id on V3.0.58: 24 SAME_ID, 0
renumbered, 0 NO_LINE. The 6 T-580 could not address: 5 FIN.CEILING dome-deduction lines from the T-335 FILL (gross -
net) and the T-283 dome table (1F-R8BDA49 1.4227 W, 1F-RB72F22 11.5808 W, 1F-R3CFCFD 0.341845 E, 1F-R48AA46 1.2410 W,
1F-R48CDA5 0.4472 E; nets 3.5998 / 7.4692 / 18.6747 / 3.7815 / 4.2778 m2 = the index) and the D-1F-03 strip
L-fcf3a49c (0.150 m2). Slot: r1's arch_v3058.py / master 1.55.0 are T-507's; r2 = V3.0.60, engine/source/arch_v3060.py,
master 1.57.0 after T-498 (V3.0.59 / 1.56.0); r1's T-310 promotion is already in 1.55.0 (same source sha256): drop it.

## 5. Overlay re-run (R-T580-1 code, read only) and F-T580-5

4,999 -> 5,123 lines; 0 STALE, 0 NO_BEFORE, 0 MISSING_LINE, 0 flagged rows; 2 conflicts, both EXPLAINED (perimeter
mortar beside bed-joint mortar, as T-580); T-423 r2 moves no total. The F package (11 ops: 3 SET + 8 ADD, line ids and
before / after in the JSON) applies cleanly and still has no board row: for the Lead.

## 6. Lesson proposal (ERS s.7)

"A line handed to Gate B carries a quantity class read from its source verdict's own state through one fixed map, a
stated before, and an address checked by element id; a bound (AT_LEAST / range) is never a released value and a
renumbered id must point at the same element" (any villa on the line-index scheme; provenance T-516 / T-580 / T-582;
test tests/t582_gate_b_readiness).
