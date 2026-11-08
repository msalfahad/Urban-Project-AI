# T-628 B10 footing line and lift pit walls: the 7 residual rows re-measured from ST7757

Worker 1 (lane S, non-candidate, backlog-permitted), 2026-11-08. Research only: no engine, candidate, released line,
rule file or method version changed; nothing released. Development villa, not an accuracy claim. ERS s.2.1 - 2.6, s.3,
s.4, s.7 applied.

## 0. Sources and run

- Drawing: Drive "Alsenan chalet project" / "ST7757 dxf.dxf" (sha256 9f9d1179..38079), downloaded this run, decoded into
  `.work/private` only. OWN read by `t628_alsenan.py` (ezdxf, hex handles): FOUNDATION PLAN frame = plot polyline 1658
  +/- 3 m; footing outlines (12 scaled unit-square F inserts, 11 S-FOOTINGS polylines, 3 four-LINE squares = 26);
  tags (S-TEXT + CF / F11 inserts); schedule FT / FTB attributes (L, W, DEPHT); strap schedule SBT attributes; S-BOUN
  1658 / 1659; S-BW 10EB / 10EA; S-COL.BON. No route G, no engine module, no earlier worker number used as input.
- Reference: the concrete + rebar workbook (Drive, same folder), footings and walls + columns sheets, read with openpyxl
  (each row re-added b x c x h x n = his cell). His rows stay private; tracked JSON holds own m2 / m3, handles, deltas.
- Engine: statement V11 `research/agents_t620/out/RECONCILED_STATEMENT_T620.json` (engine 67.6945 / 0 m3), held lines from
  `research/agents_t507/out/LINE_INDEX_V3_0_57.json`, band downgrade DG-6dd9f1caba1ca77d (T-374 V2).

## 1. Physical elements (ERS s.2.1)

Footing pad = drawn outline x schedule depth, each outline once (all footing bottoms on one stack, T-206). Strap = schedule
width x schedule depth x clear axis length between the footing outlines it joins. Boundary band = the 0.20 m ring between
S-BOUN 1658 / 1659 (section 20 x 60 schedule B.W vs typical A-A 20 x 40: Q-28). Lift pit wall = pit outline 10EB less shaft
10EA less the column outlines in the ring (the necks own them), height not printed (D-43).

## 2. Rows (reference - engine, m3; statement sign)

| # | Row | Own measure (handles) | Own delta | Stmt | Class / status |
|---|---|---|---|---|---|
| F0 | COUNT F3 | outlines 166B, 166C (1.60 x 1.40, schedule 1CA0 H 0.30), tags 168E / 168F each inside its outline: 2 x 0.672 = 1.344; reference counts 1 | -0.672000 | -0.672 | ENGINE_RIGHT, RE-MEASURED |
| F1 | F10 + F outline | 1B1B one outline 3.25 x 1.40 = 4.55 m2, open at S.B1 faces 1689 / 1B1C, tags 168B (F10) + 10A5 (F): reading A schedule rows 1.96 + 0.216 = 2.176, reading B outline x 0.50 = 2.275 = held line bound; reference has F10 alone, BELOW the bound | +1.960000 | 1.96 | HELD (Q-31 C), CONFLICT kept |
| F2 | boundary band | ring 18.388 m2 = 91.94 m centre line; 4.29 m2 = 21.45 m inside 9 outlines (1100, 1668, 1669, 166A, 1B07, 1B1A, 1B1B, 1B24, 1B2A); free 70.49 m. Range 5.6392 (70.49 x 0.20 x 0.40) .. 11.0328 (91.94 x 0.20 x 0.60); owner provisional A 8.4588 | +8.604000 | 8.604 | HELD (Q-28 A provisional); reference INSIDE the range, +0.1452 over A |
| F3 | FN notch | FN outlines 10F0, 10F8, 1100 (1.00 x 1.00) + 180C (0.86 m2: its missing 0.40 x 0.35 lies in F9 180F) x 0.30 = 1.158; notch 0.14 x 0.30 = 0.042 owned by F9 | +0.042000 | 0.042 | ENGINE_RIGHT, RE-MEASURED |
| F4 | strap LENGTH | SB1 1689 / 1B1C w 0.700, axis 4.550, 70 x 50 (1FB0) = 1.5925; SB2 1B08 / 1B09 w 0.997, axis 2.292707, two schedule rows 80 x 50 (1FBB) / 100 x 50 (2ABA): the drawn width selects 100 x 50 = 1.146354; SB3 1B26 / 1B27 w 0.505, axis 3.257962, 50 x 40 (2B06) = 0.651592; own 3.390446 | +0.002054 | 0.002 | ENGINE_RIGHT, RE-MEASURED (drift +0.000054 = engine lengths / line at 4 dp, TOLERANCE) |
| L0 | lift SCOPE_DOUBLE | gross ring 1.600 m2 (= his 8 x 0.20); columns 1090 (0.20), 1093, 1096, 1099 (0.10 each) = 0.500 m2 in the ring x his 1.50; the same four marks are in his neck rows | +0.750000 | 0.75 | ENGINE_RIGHT, RE-MEASURED |
| L1 | lift HELD | net ring 1.100 m2 x his uniform 1.50 (no printed pit depth) | +1.650000 | 1.65 | HELD (D-43) |

Split, footing line +9.936 = -0.672 (COUNT) + 1.960 (HELD F10 + F) + 8.604 (HELD band) + 0.042 (OVERLAP) + 0.002054
(LENGTH) - 0.000054 (engine length precision, TOLERANCE); lift walls +2.400 = 0.750 + 1.650. Both exact (Decimal 6 dp).
Pads: own 64.304 = engine pads to the m3 (15 marks, 25 outlines; 1B1B held); no two of the 26 outlines overlap.

## 3. Methods side by side (ERS s.2.2)

| Element | Owner manual method | Drawing-derived (this task) | Engine | Freelancer |
|---|---|---|---|---|
| F3 | count x schedule | 2 outlines x 0.672 | 1.344 | 0.672 |
| F10 + F | HOLD + RFI, bigger area if a provisional figure is needed (Q-31 C) | 2.176 .. 2.275 | HELD | 1.96 (F pad in no row) |
| band | A provisional: free length x 0.20 x 0.60 = 8.4588, deduct only where levels share (Q-28) | 5.6392 .. 11.0328 (section + crossing levels unprinted) | HELD (bound 7.2204 UNSUPPORTED) | 8.604 |
| FN | each region once (R-CONC-OWN-1) | 1.158 | 1.158 | 1.200 |
| straps | width x depth x clear length | 3.390446 | 3.3905 | 3.3925 |
| pit walls | column > wall; printed heights only (Q-21 C) | 1.100 m2 x H, HELD | HELD | 2.400 |

## 4. Findings, fix row, who is right

- No ENGINE_WRONG quantity: every valued row is ENGINE_RIGHT on own calculation; no candidate quantity moves.
- **F-T628-1 (fix row, statement, for the Lead)**: the band row quotes the held line's 7.2204 m3 (60.17 m, one plot side
  lost: T-065 / T-356), a bound the downgrade record DG-6dd9f1caba1ca77d marks UNSUPPORTED BASIS. Quote instead the
  drawing range 5.6392 .. 11.0328 (reference INSIDE, +0.1452 over the owner's provisional A): the section's
  engine_bounded becomes 75.5392 .. 81.6556 (was 77.1204 .. 77.8432; low end NOT ESTABLISHED by the T-356 pad split).
  Class HELD and the blank line are unchanged (R-T628-4).
- SB2 two schedule rows (80 x 50 insert 1FBB, 100 x 50 insert 2ABA): the drawn face spacing 0.997 m selects 100 x 50
  alone (R-T628-3); engine and reference agree; no owner item.
- HELD stay HELD by name, never 0: F10 + F (Q-31 C, CONFLICT), band (Q-28: section and crossing levels), pit height (D-43).
  ERS s.2.7 not met: no owner question.
- Beside (no row of his): SB1 inside 1B1B = strap faces 1689 / 1B1C clipped to the outline 0.805036 m2 less column C10
  10E8 0.035 = 0.770036 m2 x 0.50 = 0.385018 m3: AGREE the held line L-abd65e1b745315dd17c2 high end 0.385 (+0.000018,
  drawing precision); T-233's 0.4025 included the column plan. SB3 inside F3 (0.0295 .. 0.2683, T-230 level model) and the
  blinding were not re-measured.

## 5. Rules, tests, lessons row (proposed)

R-T628-1 .. 5 in `t628_rules.py`. `tests/t628` (18): V628 hand villa (FA 2.00 x 2.00 x 0.50 + FB 1.50 x 2.00 x 0.40 sharing
the edge x = 2: 3.200; ground beam 0.30 over both: on the tops 4.010, cast 0.20 / 0.10 into them 4.115 with the footings
owning 0.165), adverse (overlap billed twice, crossing level missing, notch with no owner, COUNT on a size mismatch,
CONFLICT as 0, SECTION_CONFLICT, balancing class, open sum, kg, HELD as 0, missing depth, outline twice), mirror /
rotation, strap axis, pit ring, unsupported bound; development villa from the committed JSON; private rebuild.

Lessons row (ERS s.7): | 2026-11-08 | the statement compared the freelancer's band row with a held bound that a downgrade
record had already marked UNSUPPORTED (a lost plot side) | a held line keeps its old number after its basis is
downgraded | a HELD row quotes a bound only from a basis not marked UNSUPPORTED; otherwise the drawing range with its
source (every villa; provenance T-628, R-T628-4) | tests/t628 | PROPOSED |

## 6. Checker re-measure list (2 largest rows)

- Band: S-BOUN 1658 / 1659 ring 18.388 m2, 21.45 m inside the 9 outlines named in F2, free 70.49 m; DG-6dd9f1caba1ca77d.
- F10 + F: 1B1B 4.55 m2, tags 168B / 10A5, schedule 1CE2 / 1C79; readings 2.176 / 2.275.
- Rebuild: `tests/t628::test_private_rebuild_equals_committed` with `.work/private/ST7757.dxf` + `concrete_rebar.xlsx`.
