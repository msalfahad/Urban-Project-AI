# T-654 WIRING MANIFEST V20 on V3.0.61 + the 10 Nov TRIAL BOQ r4 (R-T654-1 / R-T654-2; lane I, non-candidate)

Worker 3, claim 2026-11-09T17:00Z (engine e04d99d9). Nothing is wired to the candidate; V3.0.61 (NOT RELEASED) and
V2.9 + route G are untouched. Outputs: `out/WIRING_MANIFEST_V20.json`, `out/TRIAL_BOQ_R4_T654.{json,md}`,
`out/TRIAL_BOQ_R4_T654_LINES.csv` (rebuilt by `tests/t654_manifest_v20` with `URBAN_T654_WRITE=1`; the tests assert
committed == rebuild). No drawing, workbook, client name or coordinate here; nothing read from Drive this run (every
figure comes from merged, Checker-verdicted files, each sha-pinned in `manifest_v20.PINS`).

Master: BOQ_FAMILY_MASTER **1.61.0** (newest merged at claim; T-655 / 1.62.0 was CLAIMED by worker 2, not merged).
1.62.0 promotes registry status only; the next revision re-pins.

## 1. Base move V3.0.59 -> ARCH_TAKEOFF_V3.0.61 (R-T654-1 (a) / (b))

- V19 base (T-498 stage on the V3.0.58 copy) = the merged T-651 `LINE_INDEX_V3_0_59.json` on every line and field
  (asserted: 5,073 / 5,073).
- V3.0.60 (T-423 r3, 62e18eed): 22 text-only lines (5 FIN.CEILING dome lists, 1F-02 tile + backing face move D-1F-04,
  14 FIN.MARBLE.THRESHOLD, the D-1F-03 dry strip) + 2 named set-asides; each line's class / net / bound asserted equal
  to the state the merged module binds (`t423_inputs.build()` expect). No index line moves.
- V3.0.61 (T-563, e04d99d9): the 11 FIN.PLASTER lines restated from `summary_t563.json` (merged before = base line,
  asserted). Base totals moved: FIN.PLASTER|m2 only, released 580.5819 -> 363.3738, held 488.201 .. 544.0606 ->
  932.72581 .. 1,006.77641 = the merged summary.
- Overlay rows that carried these merges before they merged leave the overlay **only by equality**: 17 `T-423 r2`
  TEXT_ONLY (package emptied, removed), 11 `T-563|PLASTER_HEIGHT_V1` SET (before / after = merged before / after),
  11 `T-563|PAINT_UNCHANGED` TEXT_ONLY (paint byte-identical in the merged package) = **39**. `FR-T617-1` (T-617
  Checker AGREE, door-head band w x (D - t), not in the merged module) stays chained in `T-563` on GF-08 / 1F-13 /
  2F-01 (+0.59 / +0.59 / +0.24 m2 on the low end) and still applies (0 STALE). The rebased V19 re-applied on V3.0.61
  is byte-equal to V19 on all 5,152 lines. Conflicts: 0 unexplained, no new ruling needed.

| Room | Line | V3.0.60 | V3.0.61 (merged) | after V20 overlay |
|---|---|---|---|---|
| GF-01 | L-b1529955 | HELD blank | 61.46433 .. 65.25433 | = merged |
| GF-04 | L-1ddc23d5 | HELD blank | 43.155 .. 43.155 | = merged |
| GF-15 | L-0d93f220 | 56.0131 REL | 66.52899 | = merged |
| GF-08 | L-8cecb1d0 | 152.0505 .. 178.805 | 178.22057 .. 211.80527 | 178.81057 .. (FR-T617-1) |
| 1F-01 | L-af9621f4 | 51.415 REL | 62.573 .. 62.607 | = merged |
| 1F-04 | L-971f0bda | 52.005 REL | 63.141 | = merged |
| 1F-10 | L-2ba8077b | 48.94 .. 52.29 | 58.026 .. 62.05 | = merged |
| 1F-11 | L-31db3c83 | 61.4626 .. 61.7177 | 74.77651 .. 80.19841 | = merged |
| 1F-13 | L-9b4a7bab | 111.0177 .. 114.3677 | 135.6255 .. 139.6155 | 136.2155 .. (FR-T617-1) |
| 2F-03 | L-4ce74fc3 | 57.775 REL | 69.775 | = merged |
| 2F-01 | L-ae0cdd79 | 22.6502 .. 26.0002 | 27.35991 .. 31.76591 | 27.59991 .. (FR-T617-1) |

## 2. V20 row: F-T652-1 (R-T654-1 (c))

Physical element: the RC lintel over D-1F-07 (0.15 m wall 1F-W19, host `L-a56a8add` = 1F walls t=0.15 ASSUMED, 58.2529
m2 contract net). T-615 deducted its face as (0.80 + 2 x 0.40) x 0.20 = 0.32 m2. Checker re-measure (T-650, 07:06):
0.036 .. 0.04377 m3 = 0.15 x 0.20 x 1.20 .. 1.459 m (START available 0.259 < printed MIN 0.40, designer item) -> face
= m3 / 0.15 = **0.240 .. 0.2918 m2**. Owner manual method (net wall m2 x 12.5, Q-80 A) and drawing method (RC lintel
faces are concrete, Q-73; T-615 Checker AGREE) side by side as in T-652 s.3:

| | base m2 | units pcs (x 12.5) | panel mortar m3 (x 0.0110625) |
|---|---|---|---|
| V19 (face 0.32; D-1F-09 0.34 at its max, line at low end) | 58.2529 - 2.02 - 0.34 = 55.8929 | RELEASED 698.66125 | RELEASED 0.618315 |
| V20 low (face 0.2918) | 58.2529 - 1.70 - 0.2918 - 0.34 = 55.9211 | 699.01375 | 0.618627 |
| V20 high (face 0.240) | 58.2529 - 1.70 - 0.240 - 0.34 = 55.9729 | 699.66125 | 0.619200 |

Both lines -> **HELD 699.01375 .. 699.66125 pcs / 0.618627 .. 0.619200 m3** (cause F-T652-1 + D-1F-07 bearing,
designer item; never a point, never 0). The old point lies below the bound, so R-T652-1 (d) (released value = low
end) does not apply: new rule R-T654-1 (c). Envelope with the D-1F-09 companion: 699.01375 .. 703.91125 pcs (beside).
Residual named, not wired: the START bearing beyond the own band (0.109 .. 0.259) sits in the cross wall; if that wall
belongs to another host the 0.03 m2 extra face is that host's (0.375 pcs), not this one's (Checker to confirm by handle).

## 3. Trial BOQ r4 (master 1.61.0) and the diff r3 -> r4

- Line diff r3 -> r4 (R-T654-2 (a), refused otherwise): **13 lines, 2 with a quantity** (the F-T652-1 pair). 11
  plaster lines move cause (and 8 of them origin overlay op -> candidate V3.0.61): the merged record (T-563 why_held +
  RFI D-39 / DCR-6) is now the chosen cause (R-T654-2 (b)); older causes kept as also-stated. The 22 T-423 lines, 2
  set-asides and 11 paint pairs show no column / cause / quantity change (labels WIRED IN V3.0.59 -> V3.0.61 only).
- HELD with cause 2,728 / 2,740 -> **2,730 / 2,742** (F-T636-1 12 -> 12, the register lines); released lines 1,565 ->
  1,563; excluded 847.
- By hand: B9 pcs released 3,269.9375 -> **2,571.27625** = WIRED 1,075.80 + OVERLAY (2,194.1375 - 698.66125 =)
  1,495.47625; HELD 30 -> 31 lines (+ 699.01375 .. 699.66125). B9 m3 released 3.387982 -> **2.769667** = WIRED 1.269444
  + OVERLAY (2.020393 - 0.618315 =) 1.402078 + UNVERIFIED 0.098145. B4 FIN.PLASTER: unchanged from r3 (the merge was
  already in the overlay): released 363.3738 in the candidate. B11 kg 9,628.462205 unchanged. No unit grand is a total.
- What the 10 Nov BOQ contains and does not: section 'contains' of the JSON / md (unchanged structure; 38 MISSING
  families named; FIN.EXT -> T-314 r3 open).

## 4. Freelancer, verdicts, lessons

Freelancer: blockwork in m2 only, no unit / mortar row -> no comparison for F-T652-1. Plaster (T-563 s.5, reference
only): engine 1,006.05 vs freelancer 924.205 m2 gross on the 11 rooms (+8.9 %, his flat heights stop below the soffit:
RULE_DIFFERENCE under Q-72). Verdict proposal F-T652-1: ENGINE_WRONG at the point 698.66125 (face 0.32 assumed a
0.40 bearing the drawing cannot give), corrected to HELD on the Checker's bound.

Proposed lessons row (ERS s.7): "a pre-merge overlay carrier leaves the overlay only by equality with the merged line,
and a Checker bound on an element another trade deducts is carried into that trade's lines as a bound at both ends |
base move after a Gate B merge; cross-trade re-measure | R-T654-1 (b) / (c) (every villa) | tests/t654_manifest_v20 |
PROPOSED".
