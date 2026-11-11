# T-699: the 21 blank STR.CONC.LINTEL lines: one-sided drawn bounds (R-T699-1) or the exact missing datum

Worker 1 (lane S), 2026-11-11, branch `agents/task-T-699`. Research piece, unwired: `research/agents_t699/*` and
`tests/t699_lintel_bounds/*` only. No engine, rule / knowledge version, registry, master, frozen or candidate file
changed; V2.9 + route G and the candidate untouched; every blank line stays blank, its bound sits BESIDE it. Inputs are
the merged ledgers only (no drawing opened this run; T-650 / T-644 / T-544 / T-673 / T-678 already carry the drawn
reads). Development villa, not an accuracy claim. Nothing VERIFIED.

## 1. Physical element (ERS s.2.1)

One cast lintel over one masonry opening: B (host wall thickness) x D (ST p.13 schedule depth, 0.20 on every one of
the 21) x length (clear width + the bearing taken at each end). The line's quantity is **0** (no masonry over the head,
or a member soffit serves the opening) **or** a value in [lo, hi] of R-T673-3 on the same jambs. That is the whole
argument of R-T699-1:

- **AT_MOST = hi** holds in both cases, so it is stated even when existence is open, provided every end has a recorded
  stopper and the head is straight. It is the same hi the candidate would print once existence is decided (R-T673-3
  conventions, shared piers split by the neighbour's state, R-T696-1 ceiling).
- **AT_LEAST = lo** only when existence is REQUIRED (R-T678-1). With existence open the lo is shown beside as
  "if REQUIRED", never as a bound: the line may be 0.
- A head that reaches a member soffit is no lintel (the member owns it): stated as CONDITIONAL EXCLUSION with the
  member while that soffit is open.
- Bearing: the printed schedule bearing 0.40 (ST p.13) governs; the owner minimum 0.15 (T-448 rule) is the bearing
  only where a drawing prints none (the V699 fixture). The owner manual method (shortest precast piece) stays beside.

## 2. Result (full table: `out/T699_CENSUS.md`, ledger `out/T699_LEDGER.json`)

Candidate index V3.0.69: 61 lintel lines = 16 released, 24 bounded, **21 blank** (asserted).

| class | lines | m3 beside the blank line |
|---|---|---|
| AT_MOST, existence open (9 OPEN + 7 CONDITIONAL_EXCLUSION by a member) | 16 | family **AT_MOST 1.321826** (sum 1.367666 - W11 / W12 shared pier 1.146 counted once 0.045840) |
| AT_LEAST, existence REQUIRED, one end open (T-678) | 2 (D-GF-04, D-1F-06) | **AT_LEAST 0.084** (0.048 + 0.036), high OPEN |
| no one-sided bound, datum named | 3 (A-GF-01 curved head; D-GF-05 START stopper unrecorded; D-GF-14 no jamb / run) | conditional lo beside: D-GF-05 0.040, D-GF-14 0.024 |

Hand checks (any reviewer; m3 = B x D x length):

| line | ends (stopper, available m) | AT_MOST | if REQUIRED |
|---|---|---|---|
| W08 | START pier to D-GF-03 0.85 (D-GF-03 MIN_BEARING keeps 0.40 -> 0.45), END column 0.55 | 0.04 x (1.50 + 0.45 + 0.55) = **0.100** | 0.04 x 2.30 = 0.092 |
| W04 | START column 1.30, END pier 0.15 (wholly inside D-GF-03's high) -> 0, deficit | 0.04 x (0.60 + 0.40) = **0.040** | 0.040 |
| W11 / W12 | column 0.633 / 0.4121, shared pier 1.1451 (both HELD: full pier each, once in the family) | **0.149160 / 0.140360** | 0.110 each |
| W25 / W27 | column 1.40, column 0.10 (deficit) | 0.04 x 1.50 = **0.060** each | 0.056 |
| W26 | columns 0.75 / 0.75 | 0.04 x 2.70 = **0.108** | 0.080 |
| D-GF-08 | end of masonry 1.60, column 0.10 | 0.04 x 1.50 = **0.060** | 0.056 |
| D-GF-09 | columns 1.4531 / 0.1469; width 0.90 drawn vs 1.00 frame (T-581) | w 1.00, END kept 0.1469: 0.04 x 1.5469 = **0.061876** | 0.04 x 1.30 = 0.052 |
| D-1F-01 | end of masonry 1.3728 / 2.4272 (CEILING, mm up) | 0.03 x 4.601 = **0.138030** | 0.048 |
| D-1F-09 | pier to released D-1F-08 0.8445 - 0.40 = 0.4445, end of masonry 2.8627 | 0.03 x 4.208 = **0.126240** | 0.051 |
| D-2F-02 | end of masonry 0.2516, column 0.2484 (both deficit) | 0.04 x 1.40 = **0.056** | 0.036 |
| L-GF-01 / L-1F-01 / L-2F-01 | columns 0.40 / 0.40 | 0.04 x 1.80 = **0.072** each (= lo: if it exists it is exactly this) | 0.072 |
| P-GF-01 | column 0.00, column 1.80 | 0.04 x (0.90 + 0.40 + 0) = **0.052** (= lo) | 0.052 |

Existence and cause per line (deciding datum named in the census): 18 DESIGNER ITEM (D-39 / Q-54 B annex slab top:
W04 >= +3.829, W08 >= +3.816; T-207 sill: W11 / W12 only if sill <= 0.034 under B9; R-T228-3 stair-shaft members W25 /
W27; D-39 W26 soffit 3.00 vs 3.06; Q-67 passage FFL D-GF-05; D-43 lift tie beam D-GF-08; T-581 width D-GF-09; T-227
dome D-1F-01 / D-1F-09; D-04 BM-2F-017 depth D-2F-02 (REQUIRED for d <= 0.52, beam serves for d > 0.58); T-238 arch
A-GF-01; D-45 lift landing doors and P-GF-01), 2 METHOD GAP (D-GF-04 END: run continues 3.2703 m to a T-junction;
D-1F-06 END: crossing wall at 0.0733 m: no merged rule caps a junction end; a Lead / Checker ruling, not an owner
question, ERS s.2.7), 1 MEASURABLE NOW (D-GF-14: read the GF-W30 run and jambs from the architectural DXF). CONDITIONAL
EXCLUSION by member: W04 / W08 (CB6), W11 / W12 (B9), W26 (stair-roof piece), D-GF-08 (lift tie beam), D-2F-02
(BM-2F-017). No line is excluded outright: no head is shown to reach a soffit on the drawn data.

## 3. Owner manual method beside, freelancer, verdicts

Owner precast rule per row in the census (e.g. W08 1.5 -> 2.50 m piece, doors 0.8 / 0.9 -> 1.20 m); the drawing makes
every lintel RC cast (ST p.13), so the drawn method governs the m3. Freelancer: no lintel concrete row (T-571):
NOT_COMPARABLE. Verdict proposals: 16 AT_MOST ENGINE_RIGHT as bounds (hand rows above), existence UNRESOLVED (designer
data); D-GF-04 / D-1F-06 unchanged from T-678.

Note for the Checker: T-650's `end_hi_m` prints 0.399 for one end of L-1F-01 / L-2F-01 and 0.549 for W08 END, while
the merged T-644 v3 availability is 0.400000 / 0.550000; this census uses T-644 (as T-678 did): at 1 mm (R-T673-2)
both ends are BOUNDED.

## 4. Rules, tests, lessons

R-T699-1 1.0.0 (`t699_rules.py`, scope every villa). Tests `tests/t699_lintel_bounds` (19): V699 by hand (normal
AT_LEAST 0.060 = (1.20 + 0.30) x 0.04 and AT_MOST 0.078; existence open -> AT_MOST only; mirror; deficit end; R-T696-1
ceiling 0.037500003 -> 0.037501; shared pier HELD vs RELEASED; width conflict; family pier once) + adverse (head at a
beam soffit -> EXCLUDED, no quantity, an exclusion without its member refused; missing depth -> HELD, never 0; open
crossing end; search limit lo-only then extended; unrecorded pier neighbour; curved head; no jambs; mm passed as m) +
the development rebuild (21 lines, counts, hand rows, family sums, no name). Also run: tests/t678_open_items,
tests/t696_bound_rounding (pass).

Lessons row (ERS s.7, PROPOSED): | 2026-11-11 | 21 lintel lines were blank because existence was open, though 16 had
both ends and the section drawn | a blank line was read as "no figure at all"; a quantity that is 0 or in [lo, hi] has
an unconditional upper bound | state AT_MOST beside every blank line whose jambs and section are drawn; AT_LEAST only
with existence REQUIRED | tests/t699_lintel_bounds | PROPOSED |

## 5. For the Checker (re-measure 3 lines)

1. W08: T-644 jambs (pier 0.85 to D-GF-03, column 0.55) and D-GF-03's MIN_BEARING split -> 0.100.
2. D-2F-02: both deficit ends 0.2516 / 0.2484 -> 0.056; the BM-2F-017 threshold 0.52 / 0.58 on the 12.68 bound.
3. L-GF-01: columns 0.40 / 0.40 at 1 mm -> 0.072 (= lo).
