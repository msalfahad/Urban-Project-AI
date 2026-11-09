# T-575 B11: dome shell, dome ring and lift-pit wall reinforcement measured from the drawings (t)

Worker 1 (lane S, non-candidate, backlog-permitted), 2026-11-06. Research only: no engine module, candidate line, released
line, rule file or method version changed; nothing released. Development villa, not an accuracy claim. ERS s.2 - 4, s.7;
Q-71, OWNER_RULE_REBAR_2026-10-24 s.1 - 5 (kg inside, t once; laps HELD unless printed), Q-29 (S0 keeps the domes),
Q-44 A, Q-61 C(3), R-T560-1.

## 0. Sources (own reads this run; values only)

- Drive 'Alsenan chalet project' / 'ST7757.pdf' (sha256 74da1523..., = T-322 manifest), decoded into `.work/private`:
  p.7 DETAIL OF DOME (N.I.S): chord 4.42 / rise 1.90 / shell 0.10, one mesh d12 at 0.15 in two directions, ring section
  3 d16 top, 3 d18 bottom, 2 d14 per face at 0.20, d8 links 8 per metre, ring depth 'as per arch';
  p.10 simple-beam schedule row B4: 0.20 x 0.50, bottom 4 d16, top 2 d12, d8 6 per metre;
  p.14 lift detail: walls 0.20, horizontals d12 6/m each face (leader to the bar dots), verticals d16 6/m each face
  (leader crossing the vertical lines, drawn down to the raft bottom mat), 2 d12 at the wall top, 2 d16 at the wall foot
  belong to the raft (footing line, not counted here), pit depth 'as per lift manufacturer' (no value).
- Merged geometry (read only): ring positions and in-bay areas `research/alsenan_dome_ring_s8_3/04_RING_GEOMETRY.csv`
  (= T-160); lift ring and columns `research/agents_t322/ALSENAN_LIFT_BASE_INPUT.json`; rows from WIRING MANIFEST V8.
- Code: `t575_rebar.py` (DOME_LIFT_REBAR_V1, R-T575-1 .. 6), `t575_alsenan.py` -> `out/T575_DOME_LIFT_REBAR.json`;
  `.work/venv/bin/python -I research/agents_t575/t575_alsenan.py --check`.

## 1. One row per V8 rebar row (t; unit mass d^2/162)

| V8 row | Concrete line | Status | t low .. high | Bar groups (bounded) | HELD blank (named) |
|---|---|---|---|---|---|
| DOME-A shell | RELEASED 2.540681 m3 | HELD_RANGE | 0.287994 .. 0.425000 | hoops 162.01 .. 183.76 m = 0.144005 .. 0.163344; meridians 161.99 .. 294.36 m = 0.143989 .. 0.261656 | anchorage into the ring; hoop laps (longest hoop 13.85 m > 12 m stock) |
| DOME-B shell | RELEASED 2.540681 m3 | HELD_RANGE | 0.287994 .. 0.425000 | same geometry | same |
| West ring (B4 tag) | RELEASED 0.7552 m3 | HELD_RANGE | 0.061166 .. 0.155966 | mains DETAIL 10.740741 kg/m x 7.5526 .. 14.5210 m; mains B4 8.098765 kg/m x same | links (count 46 .. 117; cover, hooks, detail depth not printed), detail side bars (depth), laps / junctions (14.52 m > 12 m) |
| East ring (no tag) | HELD | HELD_RANGE | 0.096638 .. 0.155966 | mains DETAIL only (Q-61 C(3)) x 8.9974 .. 14.5210 m | links (72 .. 117), side bars, laps / junctions |
| DOME-3 shell | HELD | HELD_BLANK | none | none | no structural drawing (architectural only; CF-S8.3-01): the p.7 detail is not referenced to it and its size differs |
| Lift-pit walls | HELD | HELD_BLANK | none | kg(h) = A h + B: A 0.169284 .. 0.200217 t per m of height, B 0.009778 .. 0.101057 t | wall height h not printed; laps / column junctions |
| **Total** | | 4 ranges + 2 blank | **0.733792 .. 1.161932**, valued 0 | | |

Ranges are never added into a valued figure; no row is VALUED.

## 2. How each bound is made (first principles)

- **Shell** (R-T575-1 .. 3). Cap sphere R = (c^2/4 + h^2)/2h = 2.235289 m, centre a = 0.335289 m below the springing
  (= the concrete basis of the released 2.540681 m3). Bar sphere rho within the concrete, R_in + d/2 .. R_out - d/2 =
  2.141289 .. 2.229289 (cover not printed). Meridian S = rho acos(a/rho) = 3.0269 .. 3.1652 m (never the flat plan).
  Hoops counted along the meridian, n = 1 + floor(S/s): 20 .. 22, lengths 2 pi rho sin(theta); first hoop at the
  springing or at s/2 (no offset printed). Meridians: lower = area/s (the printed maximum spacing needs at least
  circumference/s bars at every height), upper = ceil(2 pi b / s) = 89 .. 93 bars all to the crown. Cross-check: the
  merged S8.3 mid-surface density 169.344 m per direction lies inside both ranges.
- **Rings** (R-T575-4, -5). Layer mean radius = ring centreline; lower = own in-bay length (in-bay area / 0.20, T-160:
  west 1.510513 / east 1.799471 m2 plan reading, 2.284455 / 2.621630 detail reading), upper = closed circle (plan r_c
  2.311092 m: 14.5210 m; detail r_c 2.111092: 13.2644 m). West ring: the plan B4 tag + schedule and the DETAIL OF DOME
  disagree (CF-S8.3-04); Q-44 A chose B4 for a skylight with the dome removed, but S0 keeps the dome (Q-29 refined), so
  both readings are evaluated and the range spans them (designer item Q-S8.3-02, already listed).
- **Lift walls** (R-T575-6). Net walls between the four lift columns N 1.80, S 1.80, W 1.20, E 0.70 = 5.50 m (x 0.20 =
  T-322 ring net 1.100 m2). Verticals 2 faces x (11 + 11 + 8 + 5) = 70 (Q-71, 1 + floor(L/s)); horizontals 6 rows per m,
  per row 11.0 m (stopping at the columns) .. 16.8 m (running through on the outer face line 8.8 + the centreline 8.0).
  B: top bars 2 x 5.5 .. 8.0 m, vertical embedment 0 .. raft 0.55 m + top return 0 .. 0.10 m, one extra row (n = 1 + floor).

## 3. Engine vs freelancer, verdicts

- Freelancer: 44.19 t TYPED_LUMP, no bar row (T-560): NOT_COMPARABLE, no %. His stairs + dome family 3.90 t and walls +
  columns 7.95 t include these elements; this task adds 0.734 .. 1.162 t of bounded HELD range to engine groups G5 / G3
  and the lift-wall kg(h) to G2 (no residual is closed: his basis is not printed).
- Verdict proposals: dome shells and rings ENGINE_OMISSION -> bounded HELD (bars now drawn-derived); DOME-3 UNRESOLVED
  (no structural drawing); lift walls UNRESOLVED (pit depth, designer / lift supplier). No owner question (ERS 2.7 not
  met: each blank is an already-listed designer item).

## 4. Tests, lessons row

`tests/t575_dome_lift_rebar` (14): K575 ring (63.20 kg mains, 50 links x 1.16 x 0.617 = 35.79 kg), hemisphere hoops by
hand (56.607 m), meridional bounds (50.265 .. 81.681 m), pit-wall formula, adverse (flat plan length, unprinted link
path / count, kg as t, missing height, in-bay longer than the circle), development-villa rebuild and three hand checks.

Lessons row (ERS s.7): | 2026-11-06 | dome and lift-pit bars had no line; a dome bar count by plan spacing or a single
number would hide the crown curtailment and the unprinted height | measure on the bar sphere, bound meridians by area/s ..
all-to-crown, ring bars in-bay .. closed circle over every printed position reading, a wall without height as kg(h) |
R-T575-1 .. 6 (every villa) | tests/t575_dome_lift_rebar | PROPOSED |
