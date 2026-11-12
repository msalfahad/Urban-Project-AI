# T-732 formwork of the moved concrete: the 7 column lines restated on V3.0.73, 4 strip children named (research, unwired)

Worker 1, lane S, 2026-11-12, branch `agents/task-T-732`. Files: `t732_rules.py` (R-T732-1 / R-T732-2 1.0.0, every
villa), `t732_alsenan.py` (builder, committed inputs sha256-pinned in `PINS.json`, `--check` rebuilds byte for byte),
`out/T732_FORMWORK_MOVED.json`, `out/T732_CENSUS.md`, `out/T732_OWN_READ.json`, tests `tests/t732_moved_formwork` (16).
No engine, candidate, rule / knowledge version, registry or frozen file changed; nothing wired, released or VERIFIED;
R-T714-1 / R-T707-1 / -2 / T-119 not edited. Own read this run: Drive 'Alsenan chalet project' / 'ST7757 dxf.dxf'
(sha256 9f9d1179 = manifest), decoded by the wrapper into the private folder only; sizes and handles only recorded.

## 1. Physical element and the two methods (ERS s.2.1 / 2.2)

A column's formwork is its cast faces from the top of what it stands on up to the slab soffit, less the faces the
framing members cover (R-CONC-OWN-1). The concrete line holds the column on section x height-to-slab-top; the formwork
needs one more dimension, D_ctrl (the deepest member framing in, T-119), which the concrete line does not contain. So one
member has two geometries: concrete A x h, formwork SHAFT P x (h - D_ctrl) + JOINT strips (D_ctrl - t, D_ctrl - D_beam,
measured by the released walk) + EDGE bands.

| | Owner manual method | Drawing-derived method (R-T732-1) |
|---|---|---|
| shaft | perimeter x storey height to the beam soffit, member by member; unprinted datum held (no storey value) | P_min x (least panel top bound - base - D_max) .. P_max x (h_hi - D_min); tops from R-T707-1 by panel |
| joints | contact strips above the soffit | walk records: INDEPENDENT when section single and D settled; 0 .. fig when D open (record at D_min); else DEPENDENT |
| why the least panel top | - | the column top follows the HIGHEST member (concrete); the deepest soffit may hang from a member on the LOWEST panel |

## 2. Census (R-T732-2): which members moved since T-714

Rebuilt by line id over all 370 T-714 lines (V3.0.70 + T-711 / T-712 / T-721 ledgers vs V3.0.73 + T-707 tank floors,
every T-722 AT_LEAST figure asserted equal to its ledger): **7 lines moved, 7 restated, 0 MOVED_NOT_RESTATED**. Index
diff V3.0.70 -> V3.0.73 on concrete: exactly the 5 plate columns (T-707 NARROW); the 2 tank columns gained a floor
(T-722 beside). Lift pit (1.903), east ring (0.115155) and GB L-fb7a6431 (capped 0 .. 3.5256) were already in T-714's
basis: their 6 formwork lines are unchanged (named in the census with the reason). T-724 (2) restated soffits carried.

## 3. Lines (formwork m2; beside, never summed into a released total)

| Line | Column (handle, own read) | Concrete m3 V3.0.70 -> V3.0.73 | D_ctrl | T-714 | **T-732** |
|---|---|---|---|---|---|
| L-fa037ca1 | 418 C9 COL-2F-55, 200 x 700 | 0.4242 .. 0.595 -> 0.45738 .. 0.595 | 0.40 .. 1.20 (BM-2F-017, D-04) | BLANK | **BOUNDED 3.720600 .. 7.218122** |
| L-5c555f96 | 41E C2 COL-2F-56, 200 x 500 | 0.303 .. 0.425 -> 0.3267 .. 0.425 | 0.40 .. 1.20 (BM-2F-018, D-04) | BLANK | **BOUNDED 2.893800 .. 5.630111** |
| L-8029c283 | 41B C2 COL-2F-54, 200 x 500 | 0.303 .. 0.425 -> 0.3287 .. 0.425 | 0.40 settled | BLANK | **BOUNDED 4.206000 .. 5.582200** |
| L-f2f2781a | 421 C1 COL-2F-53, 200 x 500 | 0.303 .. 0.425 -> 0.3287 .. 0.425 | 0.40 settled | BLANK | **BOUNDED 4.152000 .. 5.528200** |
| L-fcb1852c | 778 PC-2F COL-2F-59, 200 x 400 drawn / 20x50 text | 0.1824 .. 0.35 -> 0.20136 .. 0.35 | 0.75 settled (B7) | BLANK | **AT_LEAST 3.020400** |
| L-8c96ce0b | 40F C2 tank COL-2F-50, 200 x 500 | blank -> AT_LEAST 0.3287 | 0.40 .. 1.20 (B15, D-44) | BLANK | **AT_LEAST 2.921800** |
| L-7f7fa7a8 | 424 C3 tank COL-2F-52, 250 x 500 drawn / 20x50 sched. | blank -> AT_LEAST 0.3287 | 0.40 .. 1.20 (B15 D-44, BM-2F-016) | BLANK | **AT_LEAST 2.893800** |

Family B10-13 (beside): BOUNDED 26 -> **30, 102.914777 .. 127.151372 m2** (T-714 87.941284 .. 103.192739; T-724
+0.001093 on the low; T-732 +14.9724 .. +23.958633); AT_LEAST 32 -> **35, >= 107.379697** (+8.836); BLANK_NAMED 258 ->
251; fix rows 54 unchanged. Released 1,027.977403 and the T-638 fix rows 33.127058 untouched.

Hand check 41B (Checker pick): base +9.65; panels P1 (t 0.18, top >= 12.937), P3 / P4 (0.16, top >= 12.917): shaft
floor 1.40 x (12.917 - 9.65 - 0.40) = 1.40 x 2.867 = 4.0138; high 1.40 x (4.25 - 0.40) = 5.39; joint R4-309 0.1922
(stated section, D settled: no storey height in it) -> 4.2060 .. 5.5822. Envelope 1.40 x (4.25 - 0.16) = 5.726 above.
Hand check 418: D open to 1.20 by the unmarked 0.20 piece below the column (own read: band 39C / 399, no text inside):
floor 1.80 x (3.267 - 1.20) = 3.7206; high at D_min 1.80 x 3.85 + 0.240222 + 0.0479 = 7.218122 (as D grows the shaft
loses P x dD and the joints gain at most P x dD).

## 4. Reconciliation (units, named causes)

- vs T-707 s.4 beside figures (UP-FW-001, P x (h - t)): 41B 4.3498 -> 4.2060 = -0.1438 = zone allowance 1.40 x 0.02
  (0.028, least panel top) + beam-covered strip 1.40 x (0.40 - 0.18) - 0.1922 (0.1158, faces under framing beams,
  D-N10-04). 418 5.5926 -> 3.7206 = -1.872 = 1.80 x (1.20 - 0.16): D-04 open depth. **F-T732-1**: T-707's 'low' is the
  UP-FW-001 upper-bound method, not a floor (at D 0.40 the true 418 total 5.4008 is below it). **F-T732-2**: T-707's
  PC-2F 2.8284 .. 4.676 deducts t from a height already net of B7 0.75 (double deduction): 3.0204 floor here.
- vs T-638 shaft records: the 5.32 / 6.84 m2 caps rest on the 4.20 finished interval (h 3.80); the member's own high is
  4.25 (+9.65 to finished +13.90, D-39): shaft high 5.39 / 6.93. **F-T732-3**: R-T714-1 'never tighter than the member'.
- **F-T732-4**: T-714 printed the tank shaft faces R4-239 / R4-241 (cause D-44 stand) with the C_SECTION block text
  'dome ring, D-28' (its BLOCK_KINDS key): cause label wrong on those 2 lines; re-derived here with D-44.

## 5. T-724 strip children: NAMED blank (no formwork figure)

Concrete children are named blanks under D-05 / D-26 (no section / mark / bars / material): whether a formed face exists
is open, so no floor. Per-unit beside: GF / 1F strip at columns 366 / 68C soffit 0.16 m2, outer edge 0.80 m2 per m depth
(south on the column, ends on the two strip lines); GF / 1F NW corners soffit 0.029309 m2, edge 0.304315 m2 per m depth
(T-724 fillet geometry; east / south faces on the neighbouring strips).

## 6. Held, verdicts, lesson

Held: highs of 778 (D-66 section, joint / edge at one reading), 40F / 424 (D-44 stand); lows of 418 / 41E / 424 widened by
D-04 (unmarked depth). Designer list: D-04 (BM-2F-016 / -017 / -018 depth) now moves the formwork floor by 1.80 x 0.80 = 1.44 m2 (418) and 1.40 x 0.80 = 1.12 m2 (41E).
Verdicts: NOT_COMPARABLE (no freelancer formwork row); ENGINE (T-707 beside) WRONG as a floor (F-T732-1 / -2), corrected.

| date | discrepancy | cause | rule | regression | status |
|---|---|---|---|---|---|
| 2026-11-12 | column formwork lows taken from P x (h - t) and a moved concrete low left 7 lines blank | concrete holds A x h, formwork also holds D_ctrl; the shaft soffit hangs from the lowest panel | R-T732-1 / -2 (every villa) | tests/t732_moved_formwork (V732 normal: settled 5.48 .. 6.71, open D 4.23, planted 3.30, tank >= 3.96; adverse: undecomposable bound, no top, mm, missing figure, D reaches base, envelope, blank member) | PROPOSED |

Checker re-measure: outlines 418 / 41B (S-COL.BON 200 x 700 / 200 x 500), the unmarked piece below 418 (39C / 399 to
394), T-119 rows COL-2F-54 / -55, T-707 panel tops.
