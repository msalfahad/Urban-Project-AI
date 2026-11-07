# T-583 B11: dome / ring / lift-wall bar components (laps, links, side bars, anchorage) and the strict lift-wall low

Worker 3 (taken from lane S; non-candidate, backlog-permitted), 2026-11-07. Research only: no engine module, candidate
line, released line, rule file or method version changed; nothing valued or released. Development villa, not an
accuracy claim. ERS s.2 - 4, s.7; Q-71 (both answers), OWNER_RULE_REBAR_2026-10-24 s.1 - 6, owner 2026-10-29 (bar
parts counted only where drawn / printed), R-T575-1 .. 6, G-T371-0, T-366.

## 0. Sources (own reads this run; sheet / detail references and values only)

Drive 'Alsenan chalet project' / 'ST7757.pdf' (sha256 74da1523..., the T-575 file), rendered into `.work/private`:
p.7 dome detail ring section (each shell bar drawn down through the ring past both layers with a foot along the
bottom; side bars labelled as a count at a spacing; links per metre; ring depth not printed), p.8 notes 9 (starter
development minimum, 70 d tension / 40 d compression), 21 (side bars only in beams above a printed depth) and 22
(minimum cover 0.025 for columns, beams, slabs; 0.07 against soil), p.10 row B4, p.14 lift detail (verticals straight
down to the raft bottom mat, the two face bars joined in a U over the wall top, no foot bend). No lap length is printed
for shell, ring or wall bars (consistent with the T-366 census). Geometry and mains from the merged T-575 build.

## 1. Restated rows (t; d^2/162; nothing valued)

| V8 row | T-575 | T-583 low | bounded high part | HELD by name (high open) |
|---|---|---|---|---|
| DOME-A / DOME-B shell, each | 0.287994 .. 0.425000 | **0.290684** | 0.425000 | anchorage high (ring depth), hoop laps (>= 24 joints, length not printed) |
| West ring (B4 vs detail) | 0.061166 .. 0.155966 | **0.063897** | 0.158208 (B4 reading) | detail-reading links / side bars (depth), link hooks, main laps / anchorage |
| East ring (detail) | 0.096638 .. 0.155966 | **0.122518** | 0.155966 | links / side bars high (depth), hooks, laps / anchorage |
| DOME-3 | HELD | HELD | - | no structural drawing (unchanged) |
| Lift-pit walls kg(h) = A h + B | A 0.169284 .. 0.200217 t/m, B 0.009778 .. 0.101057 t | **A 0.156642** .. 0.212859, **B 0.000000** .. 0.123221 | - | h not printed; laps (none while h <= 11.358 m for verticals) |
| **Total of bounded rows** | 0.733792 .. 1.161932 (mains) | **0.767783** | 1.164174 | the high is HELD: not a total |

Components added (low .. high): shell anchorage 89 .. 93 bars x leg floor 0.034 m = 2.690 kg .. HELD; ring links
(count by drawn in-bay segments ceil(L/s) - 1 .. closed circle ceil(C/s)): east 50 .. 117 x path floor 0.208 m =
4.109 kg .. HELD; west B4 32 .. 88 x 0.216 .. 1.168 m = 2.731 .. 40.606 kg; detail side bars >= 2 x d14 over the in-bay
length (east 21.771 kg, west 18.275 kg) .. HELD; B4 side bars 0 by p.10 + note 21; every lap low 0 .. HELD.
Scenario only (owner proposal 60 d, not in any bound): shell hoops 24 joints 15.36 kg each dome; ring closed-circle
reading 12 joints 22.06 kg (detail) / 14.70 kg (B4).

## 2. How each bound is made

- **F-C-T575-1 closed**: per face the admissible vertical counts are ceil(L/s) - 1 / ceil(L/s) / ceil(L/s) + 1 (bars at
  neither / one / both column faces, spacing <= 1/6 m); N 10..12, S 10..12, W 7..9, E 4..6: 62 .. 78 bars. 1 + floor(L/s)
  (T-575, 70) is not the low and is not the high either: 1 + floor leaves the last gap > s (1.80 m: 11 bars, gaps
  0.18 > 0.1667), so the T-575 HIGH was also not strict. A low 0.156642 (= the Checker's floor reading), A high 0.212859.
- **Rows over h**: ceil(6h) - 1 .. ceil(6h) + 1, so B low takes one row off (11.0 m x 0.888889 = 9.778 kg) which equals
  the two top bars (2 x 5.5 m): B low 0 is computed, not a missing value; B high = top 2 x 8.0 m + 78 x (raft leg 0.55
  + U leg 0.092) x 1.580247 + two rows x 16.8 m.
- **Cover is one-sided** (note 22): it caps highs only (ring link 0.20 x 0.50 at 0.025: 1.168 m); walls / raft / shell
  are not named in it, so their highs take cover >= 0; lows use the geometric floor (bars in contact), never a cover.
- **Joints**: physically certain counts only (closed loop >= 1, > 12 m stock >= 2); lap length printed nowhere for these
  groups -> mass low 0 (coupler or unknown overlap admissible), high HELD; the 40 d / 60 d proposal is a scenario.

## 3. Findings, verdicts

- F-T583-1 (designer, no quantity): if the lift verticals are read as starters, note 9 needs >= 1.12 m (tension) /
  0.64 m (compression) for d16; the drawn straight leg fits only the 0.55 m raft and no foot is drawn: add to the
  RFI-B-S21 family (bend / anchorage of drawn legs). Not an owner question (ERS 2.7 not met).
- F-T583-2 (method): the T-575 lift-wall high (70 bars) was below the both-faces reading (78): widened here.
- F-T583-3 (shell, not applied): note 22 does not name shells; if it governed, the bar sphere narrows to
  R_in + 0.031 .. R_out - 0.031 and the shell mains range narrows; kept at T-575 bounds, listed for the Checker.
- Freelancer: 44.19 t TYPED_LUMP (T-560): NOT_COMPARABLE, no %. Verdict proposals: dome shells / rings
  ENGINE_OMISSION -> bounded HELD with every component named; lift walls UNRESOLVED (h, designer).

## 4. Tests, lessons row

`tests/t583_dome_lift_components` (16): K583 wall 2.00 m / s 0.20 -> 9 / 10 / 11, 1.80 m at 6/m -> 10 .. 12, link path
1.168 m and floors by hand, joints 12.00 / 12.01 / 24.5 m, printed lap 3 x 40 d12 = 1.28 kg; adverse: non-strict low
refused, lap without printed / adopted length refused (owner proposal = scenario only), cover in mm refused, kg as t
refused, component without a low refused; development rebuild + strict lows. Run:
`.work/venv/bin/python -I research/agents_t583/t583_alsenan.py --check`.

Lessons row (ERS s.7): | 2026-11-07 | a 'n per metre' bar count taken with one end convention (1 + floor) was neither
a strict low nor a strict high; cover and lap lengths absent from the notes were at risk of a typical value | count
ceil(L/s) - 1 .. ceil(L/s) + 1, printed minimum cover caps highs only, joints only where physically certain, lap length
only from a printed or adopted source, a row whose components are HELD reports its high as HELD | R-T583-1 .. 6
(every villa) | tests/t583_dome_lift_components | PROPOSED |
