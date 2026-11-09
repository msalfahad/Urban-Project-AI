# T-558 WIRING MANIFEST V6 on ARCH_TAKEOFF_V3.0.58

Worker 3 (lane I, non-candidate, backlog-permitted), 2026-11-06, engine base 431ac67f. Not an integration package:
nothing is wired; no candidate, released (V2.9 + route G), rule, knowledge or registry file is touched. Files:
`manifest_v6.py` (builder, R-T558-1; V5 builder, T-523 map, T-454 rule read only), `WIRING_MANIFEST_V6.json`,
`tests/t558_wiring_manifest_v6/` (22 tests). Rebuild: `python3 -I research/agents_t558/manifest_v6.py` (`--check`).
Inputs are committed, numbers-only outputs (sha256 in `inputs`); V5 pinned by sha256; no drawing read.

## 1. Coverage (R-T549-1)

Range (V5 base 47d74505, V6 base 431ac67f] on the first-parent line: 5 merges, all covered: T-550 f052dfeb, T-555
e3e0ed0e, T-559 f6636468, T-556 655b9eac, T-557 431ac67f. NO_WIRING: T-550 / T-559 (blockwork to cause, ENGINE_WRONG
none), T-557 (statement adapters; its F-T557-2 ENGINE_WRONG is the T-556 row), T-555 (V5 itself). Source: T-556.

## 2. The wiring row V5 lacked (F-T555-3): PLASTER_HEIGHT_V1_WIRING, Gate B, after T-498

Physical element: the dry plastered wall face, FFL to the structural slab / roof soffit (Q-72); paint stays at the
finished ceiling (G1). Values: T-556 R-T556-1 (Checker 10:20: 1F-04, 2F-03 re-measured from raw DXF, GF-15 by hand).

| Room | line | candidate before | V5 (T-552) | **V6 (T-556), HELD** | V5 -> V6 |
|---|---|---|---|---|---|
| GF-01 | L-b1529955 | HELD blank | 57.625 .. 75.088 | 61.464 .. 65.254 | +3.84 / -9.83 |
| GF-04 | L-1ddc23d5 | HELD blank | 41.115 .. 44.255 | 43.155 | +2.04 / -1.10 |
| GF-15 | L-0d93f220 | 56.0131 REL | 68.720 .. 70.874 | 66.529 | -2.19 / -4.34 |
| GF-08 | L-8cecb1d0 | 152.05 .. 178.81 | 183.431 .. 215.505 | 178.221 .. 211.805 | -5.21 / -3.70 |
| 1F-01 | L-af9621f4 | 51.415 REL | 61.858 .. 63.628 | 62.573 .. 62.607 | +0.72 / -1.02 |
| 1F-04 | L-971f0bda | 52.005 REL | 62.271 .. 64.011 | 63.141 | +0.87 / -0.87 |
| 1F-10 | L-2ba8077b | 48.94 .. 52.29 | 58.498 .. 63.468 | 58.026 .. 62.050 | -0.47 / -1.42 |
| 1F-11 | L-31db3c83 | 61.463 .. 61.718 | 74.531 .. 77.001 | 74.777 .. 80.198 | +0.25 / +3.20 |
| 1F-13 | L-9b4a7bab | 111.018 .. 114.368 | 134.293 .. 141.588 | 135.626 .. 139.616 | +1.33 / -1.97 |
| 2F-03 | L-4ce74fc3 | 57.775 REL | 68.926 .. 70.816 | 69.775 | +0.85 / -1.04 |
| 2F-01 | L-ae0cdd79 | 22.650 .. 26.000 | 27.966 .. 32.216 | 27.360 .. 31.766 | -0.61 / -0.45 |
| **11 lines** | | | 839.23 .. 918.45 | **840.65 .. 895.90** | |

4 RELEASED lines 217.2081 m2 -> HELD (BOUNDED) 262.01799 .. 262.05199 m2 (+20.63 .. +20.65 %); FIN.PLASTER released
580.5819 -> 363.3738 m2. Every line stays HELD (a face under a roof, build-up not printed, D-39 / DCR-6). Checks in the
builder: T-556 'old' = the candidate (released value or held range), T-556 sums = its rows, released plaster = released
paint (the shared-height cause), T-556's T-552 column = the V5 expectation.

## 3. Bindings, one by one (`bindings.rows`, 132)

All 132 T-454 / T-489 bindings of the 11 lines are re-read (class HELD, net none, held range = T-556). 22 change a
figure: the WALL_PLASTER mortar m3 rows get the bound T-454 prints beside a HELD line (held range x 0.020 m, rounded 9;
rule reproduced first on the 16 bounds already printed). On the 4 released lines the level-4 estimate beside
(net x 0.020) is replaced by a bound (GF-15 1.120262 -> 1.3305798 m3). 110 are read-only (bond coat: no thickness;
cement / sand: NEEDS_MIX) and stay HELD blank. Of V5's 58 stale, 18 change a figure and 40 only re-read; 4 figure
changes are new vs V5 (GF-01, GF-04 mortar rows: blank -> bound). Per table: WALL_PLASTER mortar estimate beside
4.344162 -> 0 m3; bound 7.92242 .. 8.663612 -> 16.8129162 .. 17.9179282 m3 (T-489 reads T-454: never added together).
No binding carries a value.

## 4. FIN.PAINT (register 'WALL PLASTER HEIGHT vs PAINT HEIGHT')

All 45 FIN.PAINT lines expected after = before (released 217.2081 m2 unchanged); the 11 paint lines of the moved
rooms listed in `paint.pairs`, each equal to its plaster line before (builder refuses a room where they differ).

## 5. Packages

PLASTER_HEIGHT_V1_WIRING: new (steps in `wiring_row`), Lead to open its board row. T-498, T-509, T-423 r2, T-363 /
T-372 / T-513, F package: no V6 change.

## 6. Findings, lesson

- F-T558-1: V5 named 58 stale plaster bindings and 74 unchanged with no after; on T-556 all 132 are re-read, 22 move.
- F-T558-2: a package built on V5 carries the T-552 bound that T-556 superseded (GF-15 over by 2.19 .. 4.34 m2).
- F-T558-3: F-T555-3 has an owning wiring item now; its board row is still to be opened (Gate B, after T-498).

Lessons row proposed (ERS s.7): | 2026-11-06 | a manifest named stale material bindings by count, with no expected
after, and kept a bound a later method version superseded | the stale set was taken from the source's net read
only; a later method version on the same lines was not re-read | a manifest lists each binding of a moved line with its
expected after from the producing table's own rule (reproduced on its printed rows first) and takes the newest merged
method version | tests/t558_wiring_manifest_v6 | proposed |
