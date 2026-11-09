# T-572 Structural HELD bounds (B10 concrete, B1 earthworks) on V3.0.58, for the 12-13 Nov scorecard

Worker 1 (lane S, non-candidate, backlog-permitted), 2026-11-06, run session_01E6cPndGuHx7pcYCjVxeQj7, branch
`agents/task-T-572`. Research only: no engine module, candidate line, released line, rule file or method version
changed; nothing released. Development villa, not an accuracy claim. ERS s.2 - 4 and s.7 applied; R-T547-1 (bound
every HELD element before any %), R-T551-1 .. 4, R-T565-1 .. 4, R-T566-1 .. 5, R-NECK-ENDS-1, MISSION no-assumptions.

## 0. Sources and run

- Engine lines: `research/agents_t507/out/LINE_INDEX_V3_0_57.json` (structural lines of V3.0.58, R-T507-1 (e)).
- Per-element drawing facts, all from merged, sha-pinned committed files (no drawing re-opened here): T-205 neck input
  (section candidates, footing type / H per neck), T-566 position register (neck position -> GF member), T-394 member
  base datums (T-287 annex +0.25), T-449 column hold items, T-233 / T-065 footing and band readings, T-350 / T-350 r2 /
  T-565 earthworks zones. The neck join (36 / 36 by one translation, the T-350 r2 frame offset) is checked by rebuilding
  the merged T-565 S01 term: 29 pit necks x printed section x (1.50 - H) = **5.154000 m3 exactly** (test).
- Freelancer: Drive "Alsenan chalet project", the concrete + rebar workbook (sha256 `ae608411`, = the B1 manifest),
  downloaded this run, decoded into `.work/private` only, read through the merged `t551_alsenan.build` in memory.
  Tracked output carries his family totals (already tracked by T-551) and measured-set sums only.
- Code: `t572_rules.py` (R-T572-1 .. 4), `t572_alsenan.py` -> `out/T572_HELD_BOUNDS.json` (every component with its
  bound + basis or its blocking item).

## 1. The physical elements and the datums (ERS s.2.1)

Neck: column below the GF, from the footing TOP (the footing owns its depth) to the GF column base (same datum,
R-NECK-ENDS-1). Printed / drawing-confirmed datums only: footing underside >= 0.17 above the formation (underlay 0.07
T-206 + blinding 0.10 ST p.13); formation at least 1.50 below the plot level EG +-0.00 (ST p.9 note 1 prints a MINIMUM,
T-357 EG); GF base +0.95 (T-214) or +0.25 (annex, T-287). So **h >= top + 1.33 - H** (valid under both readings of
note 1: excavation level, and S01 footing underside -1.50, which gives 1.50 - H + top); the deeper end has no printed
maximum: the upper bound stays open on the formation (Q-21 C / T-042 B4). Where two readings exist the bound takes the
one that keeps it valid: lowest top (annex members: T-394 +0.95 vs annex FFL +0.30 - 0.05), largest H (F10 + F: 0.50
vs 0.30, Q-31 C), smallest section (D-16 / D-63 conflicts, drawn 25 x 50 at C4 108D, 30 x 40 at C 10B7).

## 2. Result per family (V3.0.58; m3; n bounded / m held)

| Family | Valued | Held m | Both ends drawn | One end drawn | No drawn bound (item) | Bounded part | Family total stateable |
|---|---|---|---|---|---|---|---|
| B10 columns | 19.7765 | 29 (+5 NOT_PRESENT) | 15 (section CONFLICT) 8.034 .. 10.119 | 0 | 14: 5 GF annex Q-54B / D-39, 9 2F D-39 (+D-44, section) | 8.034 .. 10.119 | no: D-39 / Q-54B |
| B10 necks | 0 | 36 | 0 | **36 lower, 9.7239** (32 drawn + 4 lift flagged) | upper: Q-21 C formation | >= 9.7239 | lower only: **>= 9.7239** |
| B10 lift | 0 | 2 | 0 | pit walls >= 1.903 (flagged) | tie beam D-43 | >= 1.903 | no: D-43 |
| B10 footing line | 67.6945 | 5 | 4: F10 + F 2.176 .. 2.275, band 5.639 .. 11.033, SB1 0 .. 0.385, SB3 0.0295 .. 0.2683 | 0 | band pads (count not printed, Q-28 A) | 7.8445 .. 13.9613 | no: pad count |
| B10 blinding (plain, never structural) | 12.734438 | 6 | 5: 7.640374 .. 13.466198 | 0 | boundary-wall base (pad count) | 7.640 .. 13.466 | no |
| B1-02 excavation (in situ) | 225.941333 | 10 | 1 (ext GB trench 1.069 .. 1.176) | 4: PIT-FF >= 31.05 (flagged), PIT-F10F >= 6.525, ZERO >= 0, LOWER-GB-ROW >= 0 | 5: annex D-33/34/35, court, straps D-15, boundary Q-28 A, D-33 | >= 38.644 on 5 | no |
| B1-03 backfill (compacted) | 0 | 7 | 0 | 3: **PITS-24 >= 99.645011**, POOL >= 0, EXT-GB >= 0 | 4: other trenches, F10F, FF, Z2 | >= 99.645 on 3 | no |
| B1-04 disposal | 0 | 1 | 0 | 0 | densities not sourced, Z2 draw | none | no |

Count: 96 held components: 25 bounded on both ends, 44 with a drawn lower end only (36 necks + 8), 27 with no drawn
bound (each item named); plus 5 NOT_PRESENT_PROPOSED. Nothing is summed as 0; a family total is stated only where every held component carries
that end (necks, lower end only).

### Findings

1. **The candidate's neck range is not drawn.** Every neck line carries 0.50 .. 2.50 m x section (T-167 'generic neck
   height'). The drawings support a LOWER bound per neck of 1.08 .. 1.98 m (36 lines, 9.7239 m3 against the
   candidate's 3.075); no printed maximum exists, so the 2.50 m upper end (15.375) has no drawing basis. Each drawn
   lower bound lies inside the candidate range (no contradiction, test); the candidate range is reported beside as
   CANDIDATE_RANGE_NOT_DRAWN, never as the bound.
2. **The 5 'CN columns' are not elements.** The schedule CN row prints FOUNDATION 30 x 30 only, GF / 1F / 2F struck
   (T-075, T-042): the plan symbols are the CN necks. Their candidate exposure (3 x 0.378 .. 1.161) is not a bound:
   NOT_PRESENT_PROPOSED, carried apart (wiring is lane I: 5 held lines -> 0 lines, never 0 m3 of a held line).
3. **Pits backfill: drawn lower end 99.645011 m3** = printed-minimum excavation 186.974333 (T-565) - verified buried
   71.925255 - 29 necks below EG at formation -1.50 (5.154 - 0.17 x 4.86 = 4.3278) - C8 conflict 0.2241 - strap ends
   0.179618 - ground-beam solids, deepest reading 10.672549. Backfill rises with the formation depth (plan 124.65 m2 >
   neck sections 5.13 m2), so the printed minimum is its least value. The line's 119.963 .. 128.644 rests on S01
   (owner-accepted ESTIMATED footing underside -1.50): shown beside, not a drawn bound.
4. **F10F excavation**: the candidate range 7.2645 .. 8.39175 is S01 x 1.67; drawn lower end = smallest in-plot plan
   4.350 m2 x 1.50 = 6.525.
5. **Flagged NOTE1_ON_LIFT_RAFT (Checker)**: PIT-FF excavation >= 20.700 x 1.50 = 31.05, lift pit walls >= 1.10 x 1.73 =
   1.903 and the 4 lift necks (1.73 m) apply ST p.9 note 1 to the lift raft FF (a foundation, so the minimum founding
   depth applies); T-205 / T-350 gave no form because the pit floor is 'as per lift manufacturer' (D-43). If the Checker
   rejects the scope, these 6 return to UNBOUNDED and the neck lower end falls to 8.7724.
6. Boundary band: the line's 7.2204 is one reading (Q-28 A provisional, side 1 lost, T-065); the drawn range 5.639 ..
   11.033 (T-065 / T-233) is the bound; 11.033 is gross of 21.45 m inside 9 footing outlines (2.574 owned by the pads):
   8.459 net, for the Checker.

## 3. Like-for-like on the measured set (R-T572-4; engine - his, m3)

| Family | Measured set | Engine | His | Diff | % | Split |
|---|---|---|---|---|---|---|
| GF columns | 9 marks fully valued, row of his | 12.705 | 11.53125 | +1.17375 | +10.18 | JOINT_HEAD +1.884 (RULE_DIFFERENCE), COUNT -1.031, BASE +0.105, GLOBAL_DEPTH +0.066, HEIGHT_OPEN +0.150; **net of the rule difference -0.710 (-6.2 %)** |
| 1F columns | 4 marks | 3.108 | 2.553 | +0.555 | +21.74 | JOINT_HEAD +0.385, GLOBAL_DEPTH +0.095, HEIGHT_OPEN +0.075; net of JOINT_HEAD +0.170 (+6.7 %, ENGINE_RIGHT global depth + split open) |
| footing pads + straps | 18 marks | 67.6945 | 67.0665 | +0.628 | +0.94 | COUNT F3 +0.672, OVERLAP FN -0.042, LENGTH -0.002 (T-551, ENGINE_RIGHT) |
| necks (held) | his 34 necks / 13 marks vs the his_n smallest drawn lower bounds per mark | >= 8.8695 | 8.805 | his >= 0.0645 below | n/a (held) | **BELOW_DRAWN_LOWER**: 8 of 13 marks below; his flat 1.50 m (the note-1 number) is shorter than 2.28 - H for every main-house neck on a footing shallower than 0.78 m |
| lift pit walls (held) | his net share 1.650 | >= 1.903 (flagged) | 1.650 | | n/a | BELOW_DRAWN_LOWER (if note 1 applies to FF) |
| F10 + F (held) | his 1.960 | 2.176 .. 2.275 | 1.960 | | n/a | BELOW_DRAWN_LOWER (T-233) |
| boundary band (held) | his 8.604 | 5.639 .. 11.033 | 8.604 | | n/a | WITHIN |
| blinding | his one plate 47.055 | | | | none | NOT_LIKE_FOR_LIKE (T-478 RULE_DIFFERENCE) |
| B1 earthworks | NO_ROW (T-565: 0 hits in 885 rows) | | | | none | NOT_COMPARABLE |

No percentage is stated for a held family; m3 is never compared with m2; NO_ROW is never 0.

## 4. Who is right (proposals), what is open

- ENGINE_RIGHT (proposal): necks are at least 1.08 .. 1.98 m long (drawn datums), so the freelancer's flat 1.50 m
  understates the main-house necks (his total is at or below the drawn minimum on his own count); the 5 CN 'columns'
  are NOT_PRESENT (printed schedule). RULE_DIFFERENCE: column JOINT_HEAD (ownership, T-551).
- HELD (never 0), item named, no owner question (ERS s.2.7 not met: unprinted design values on the designer lists
  D-14 / D-15 / D-33 / D-34 / D-35 / D-39 / D-40 / D-43 / D-63, Q-21 C, Q-28 A, Q-31 C, Q-54 B, OQ-13).
- Uncertain (Checker): NOTE1_ON_LIFT_RAFT (6 components); TOP_TWO_READINGS (5 annex necks take +0.25); TOP_LOWEST_DRAWN
  (6 CN necks take +0.25); the boundary band upper end gross vs net.
- No ENGINE_WRONG found, no quantity changed, nothing released.

## 5. Rules, tests, lessons row (proposed)

R-T572-1 .. 4 (`t572_rules.py`). `tests/t572_held_bounds` (12): hand villa V572 (neck 0.40 x 0.40 between printed -1.20
.. -0.30 = 0.144 BOUNDED; neck on a printed minimum only = LOWER_ONLY 0.297; no founding note = UNBOUNDED with its item;
rotation, candidate sections / depths / tops), adverse (default depth refused, generic / freelancer basis refused, HELD
as 0 refused, low 0 only with existence open, NOT_PRESENT apart, mm, m3 vs m2, % input), development villa from
committed files (rebuild = committed, every component bound or item, counts, S01 join 5.154, key bounds) and the
private measured set.

Lessons row (ERS s.7): | 2026-11-06 | the structural HELD lines carried ranges built from a generic neck height 0.50 ..
2.50 m and an S01 estimate, so the scorecard could quote neither a drawn bound nor a like-for-like % | a held range was
recorded without its basis, and a printed MINIMUM (note 1) was not used as a one-sided bound | every held component
carries each end as a number with its drawn basis or the named item; a printed minimum gives a one-sided bound; generic,
default or estimated ranges are reported beside, never as the bound; totals and % only where every component carries
that end (every villa; provenance T-572, R-T572-1 .. 4) | tests/t572_held_bounds | PROPOSED |

## 6. Checker re-measure list

- ST p.9 note 1 wording ('excavation' vs 'founding') and whether it governs the lift raft FF (finding 5).
- Annex GF member bases at 10B1 / 10AE / 10A8 / 10AB / 10B4 (+0.25 or +0.95).
- `test_private_measured_set_equals_committed` with `.work/private/concrete_rebar.xlsx`.
