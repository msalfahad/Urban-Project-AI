# T-629 WIRING MANIFEST V15 + OVERLAY DRY RUN on ARCH_TAKEOFF_V3.0.58

Worker 3 (lane I, non-candidate), 2026-11-08. Not an integration package: nothing is wired; no candidate, released
(V2.9 + route G), rule, knowledge or registry file is touched; no drawing read. Figures come from the committed,
Checker-merged outputs of T-615 (b8265219), T-617 (44ee93d5), T-618 (85a473ce), T-622 (31fe39db), T-556 (the T-563
plaster frame), V4 / V6 and the V14 manifest (T-619), all sha256-pinned, plus the Checkers' verdict lines. Files:
`manifest_v15.py` (R-T629-1), `out/WIRING_MANIFEST_V15.json`, `tests/t629_manifest_v15/`. Rebuild:
`python3 -I research/agents_t629/manifest_v15.py` (`--check`).

## 1. Physical elements and where each fix row goes

- 0.15 m solid black block wall, 39 x 19 face + 10 mm joints = 40 x 20 installed (Q-80 A, UPC-BLACK-BLOCK-001 1.1.0):
  units, panel joint mortar, perimeter joint mortar of the 15 walls on the 6 V4 hosts. The 12 material lines are T-498
  stage lines, so the steps chain INSIDE the T-498 Gate B package (R1: one package per line).
- Lift landing door face under the ring beam (T-617): with plaster to the slab underside (Q-72), the wall band
  w x (D - t) above the door is always plastered whatever the head. The plaster lines are T-563 lines: steps chain
  INSIDE the T-563 package. On the candidate's own G1 faces (and paint) the band moves 0.000 m2 (V14's listing holds
  there only).
- GF-07 open pantry wall tile: drawn faces 4.50 + 3.00 + 3.00 = 10.50 m (the engine walked 10.491); own package.

## 2. Rows (before = the owning package's own after)

| Fix row | Line(s) | Before | After | Evidence |
|---|---|---|---|---|
| FR-T615-1 units | 6 staged MAS.UNITS.BLACK | HELD blank (R-T533-1) | 315.90875 / 653.975 / 123.6875 / 698.66125 (+ HELD 0 .. 4.25) / 294.4675 / 107.4375 pcs | ASSUMED — OWNER-APPROVED |
| FR-T615-2 panel mortar | 6 staged MAS.MORTAR.BLACK | HELD blank | 0.279579 / 0.578768 / 0.109463 / 0.618315 (+ HELD 0 .. 0.003761) / 0.260604 / 0.095082 m3 | ASSUMED — OWNER-APPROVED |
| FR-T615-3 perimeter | 6 NEW perimeter keys | no line | low 0.014744 / 0.018729 / 0.003167 / 0.028344 / 0.010361 / 0.003237 m3; companions 0 .. open (1F DC, 1F ASSUMED hosts: dome pieces HELD by name), 0 .. 0.001167, 0 .. 0.000278 | ASSUMED — OWNER-APPROVED |
| FR-T617-1 | GF-08 / 1F-13 / 2F-01 FIN.PLASTER | 178.22057 / 135.6255 / 27.35991 .. high | low + 0.59 / 0.59 / 0.24 = 178.81057 / 136.2155 / 27.59991, highs unchanged | HELD |
| FR-T622-1 | GF-07 FIN.WALL.TILE L-f5c5a1a9 | 32.3422 | 32.375 m2 (+0.0328) | VERIFIED (Checker re-measure) |

Cement / sand stay beside the mortar lines (x 8 bags, x 1.1 m3 per m3; purchasing keys, waste HELD).

## 3. Listed, not wired (R-T629-1 (f)), and sources with 0 rows

- Ties +61 (ledger 151 -> 212 measured) and bed-joint strip +367.9895 m.l (175.4844 -> 543.4739): no candidate code
  (B9-06 / B9-07 proposed). F-C-T615-1: strip GF-W22 20.2105 and 2F-W08 13.9997 m.l and 2F-W08 ties 6 .. 6 read only
  with the parent's HELD area (D-27 / D-39), never as unconditional points.
- FR-T618-2 porch landing skirting 3.50 lm: no owning line or code; scope for the Lead; never 0.
- T-622 GF-14 +0.086709 m2: worker-only, not named by the Checker as a fix row.
- 0 rows: T-618 FR-T618-1 (statement, V11), T-620, T-621, T-623. Refused by name: T-624, T-628 (TODO at claim).
- The 8 material lines of hosts outside V4 (GF-W22 parent, 2F-W08, unclassed 0.15) stay HELD blank (checked).

## 4. Overlay

V2 .. V14 rebuilt (5,129 lines; every last V14 row state = the committed V14), then V15: **5,141 lines (+6 perimeter
keys, +6 range companions), 0 STALE, 0 two-package lines, 0 unexplained conflicts; every line V15 does not write is
identical to the V14 overlay.** Two MAS.MORTAR host conflicts (GF / 1F t=0.15: panel vs perimeter keys) are EXPLAINED
by the 0.15 m extension of the T-580 'own key' ruling. Totals move on exactly four keys. Stair census 89 edges, 0 / 0.
The T-563 package's V6 binding reads on the 3 plaster lines (36 reads) must re-read the new low end at Gate B
(F-T629-1).

## 5. Acceptance figures (hand)

- MAS.UNITS.BLACK released 1,075.8 + 2,194.1375 = **3,269.9375 pcs** (.. 3,274.1875 with the companion 4.25 = 0.34 m2
  D-1F-09 face x 12.5); per host = base x 12.5 (e.g. 25.2727 x 12.5 = 315.90875).
- MAS.MORTAR.BLACK released 1.367589 + panel 1.941811 + perimeter 0.078582 = **3.387982 m3**; panel exact
  1.9418116875 (per-line 6 dp, -0.0000007 print rounding); perimeter range 0.078582 .. 0.089890 + dome pieces open.
- FIN.PLASTER HELD low 932.72581 + 1.42 = **934.14581 m2**; high 1,006.77641 and released 363.3738 unchanged.
- FIN.WALL.TILE released 340.3038 + 0.0328 = **340.3366 m2** (pantry 10.50 x 3.65 - 2.25 - 1.50 - 2.20 = 32.375).
- Freelancer: blockwork in m2 only, units / mortar UNRESOLVED (no comparison); pantry ENGINE_WRONG -0.0328 m2 fixed.

## 6. Lesson proposal (ERS s.7)

"A merged fix row on a line that a pending Gate B package writes chains inside that package, before = its own after;
an owner answer releases a HELD-by-name material line only through the cited rule version, re-derived exactly, with
the walls re-adding to the host and the excluded walls left HELD" (any villa on the line-index scheme; T-629;
tests/t629_manifest_v15).
