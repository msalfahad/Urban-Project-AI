# T-673: concrete outside B10 (F-C-T669-2): census and drawn measure of the 49 HELD blank STR.CONC lines in V3.0.64

Worker 1, lane S, claim 2026-11-10 13:28 UTC, engine base 0ed807c3. Research only, unwired: no engine, rule, knowledge,
registry, master, frozen or candidate file changed; V2.9 + route G and V3.0.64 untouched. Files:
`t673_rules.py` (R-T673-1 / -2 / -3, project-agnostic), `t673_alsenan.py` (development-villa builder, committed inputs
only), `out/T673_LEDGER.json` + `out/T673_CENSUS.md` (line ids, causes, m3), `tests/t673_lintel_stair_census` (35 tests).
Drawing cited by Drive folder and title only: 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip -> P7757.dxf (sha
ab54dd55), decoded by the wrapper into the private folder; only derived lengths are committed.

## 1. Physical elements (ERS s.2.1)

- B9-02: one cast-in-situ RC lintel over each masonry opening (ST p.13 LINTEL SCHEDULE: B = wall width, D by width band,
  MIN 40 cm bearing; R-T650-1: 60 / 60 openings RC cast on this villa). It exists only where masonry is built above the
  head (R-T453-4). Concrete m3 owned by STR.CONC.LINTEL; masonry deducts only its face (register 2026-11-10).
- B7-12: the stair flights / landings / turns owned by STR.CONC.STAIR; floor-arrival landings are slab (T-258).

## 2. Census (count 49 = the V3.0.64 index: 44 STR.CONC.LINTEL + 5 STR.CONC.STAIR HELD blank, every id once)

| cause | lintel | stair | total |
|---|---|---|---|
| MEASURABLE NOW | 16 | 1 | 17 |
| DESIGNER ITEM | 6 (P-GF-01 D-45; 3 lift doors D-45 / LIFT LANDING DOOR LINTEL; D-GF-09 width conflict; W26 D-39) | 4 | 10 |
| OPEN BOUND | 22 (20 host wall / piece HELD in the merged fill; W11 / W12 sill datum; W13 beam piece over the head not read) | 0 | 22 |

Row by row: `out/T673_CENSUS.md`.

## 3. The engineering finding: 14 lintel heads were already drawn

T-453 (R-T453-4) read heads only from census r3, which never took the T-201 / T-207 / T-238 drawn heads (merged 23 Oct,
DRAWING-CONFIRMED from vector DWF / P7757.dxf). So 20 windows sat HELD as 'head not established' although their heads
were drawn. Re-running T-453's own decision with those heads (R-T673-1: robust within each read's measured tolerance):

| opening | host | head above datum | lowest piece | spare after D + 0.06 bed + tol | decision |
|---|---|---|---|---|---|
| W05 / W06 / W07 | GF-W10 | 2.50 (W05: +3.50 on the +1.00 run datum; worst datum +0.30 same decision) | 3.75 | 0.984 | REQUIRED |
| W09 / W10 | GF-W16 | 2.50 | 3.75 | 0.984 | REQUIRED |
| W16 | 1F-W00 | 3.000 .. 3.101 (arched; own DXF read 3.101) | 3.45 | 0.088 | REQUIRED |
| W19 / W20 / W24 | 1F-W06 | 2.50 | 3.45 | 0.658 .. 0.671 | REQUIRED |
| W21 / W22 / W23 | 1F-W10 | 2.50 | 3.70 | 0.927 | REQUIRED |
| W28 / W29 | 2F-W02 | 2.50 | 3.45 | 0.671 .. 0.677 | REQUIRED |
| W04 / W08, W25 / W27 | GF-W04 / 1F-W10 / 2F-W02 | drawn | - | host ON_HELD_WALL / IN_HELD_PIECE | HELD (OPEN BOUND) |

Quantities (R-T673-3 on the merged T-644 jamb evidence, T-544 extended W24 end; 2 ends >= 0.40: lo = B D (w + 0.80),
hi = B D (w + both end ceilings); an end < 0.40: R-T524-1 MIN-BEARING range; a shared pier is occupied once):

| lintel | lo m3 | hi m3 | basis |
|---|---|---|---|
| W07 / W23 | 0.056 | 0.134 | 0.04 x 1.40 / 0.04 x (0.60 + 0.400 + 2.350); W23 0.39996 -> 0.400 at printed precision (R-T673-2, F-T650-3) |
| W24 | 0.094 | 0.268280 | 0.04 x 2.35 / 0.04 x (1.55 + 0.938 + 4.219) |
| W19 / W20 | 0.056 / 0.056 | 0.069 / 0.08048 | pier 0.875: each 0.40 + remainder 0.075 once (0.003 m3) |
| W09 / W10 | 0.092 / 0.056 | 0.118 / 0.060 | W10 START 0.100 at a column (deficit); pier 1.05 = W10 0.40 + W09 0.65 |
| W05 / W06, W21 / W22, W28 / W29 | 0.040 each, W29 0.064 | 0.055 / 0.040, 0.055 / 0.040, 0.055 / 0.064 | one end at a column face (0.375 or 0.000): R-T524-1 |
| W16 | 0.078 | 0.081732 | pier 0.4933 shared with RELEASED W15 (0.40 of it): START 0.0933 deficit |
| A-1F-01, P-1F-01 | 0.054, 0.063 | 0.1185, 0.12042 | T-650 BOUNDED (merged, unwired) |
| **16 lines** | **0.925000** | **1.496412** | B9-02 today: 16 released lines; these 16 are blank |

Status: existence DRAWING-CONFIRMED (drawn, not printed heads, N09 'not to scale' stands), quantity HELD bounded; the
deficit ends' column / cross-wall connection is a designer item (T-516 RFI), never blocking. Nothing VERIFIED.

## 4. Stairs (5 lines; owner 2026-10-22: the staircase system is never VERIFIED)

| line | element | cause | m3 |
|---|---|---|---|
| L-061e18cf | ST-03 entrance E1 | MEASURABLE NOW (part): steps DRAWING-CONFIRMED 5 x 1/2 x 0.30 x 0.17 x 2.80 = 0.357 - slab wedge 0.001983 = 0.355017; waist S-9 HELD; riser D-56 beside | 0.355017 .. OPEN |
| L-7863355d | ST-01 GF -> 1F remainder | DESIGNER C-ST-4 / RFI-A04 (MS1-L), D-67 / C-ST-3 (winder, turn slab) | 1.213429 .. 1.434413 (held) |
| L-659243ed | ST-01 MS2 turn riser | DESIGNER C-ST-3 | blank |
| L-b6b0354b | ST-02 curved remainder | DESIGNER D-08 / Q-50 / Q-51, CA 0 .. 0.09, 2CC | blank |
| L-821032bc | ST-01b D1 waist | DESIGNER S-9 | blank |

Proposed wiring (lane I): split ST-03 like the V3.0.18 ST-01b split (steps part line 0.355017 m3 DRAWING-CONFIRMED, waist
remainder blank); no other stair line moves.

## 5. Own drawing read (P7757.dxf, NW ELEVATION)

W16 jambs 2566 / 256A 1.5523 m apart, +5.50 .. +7.661; highest layer-1 point over the opening 3.101 above +5.50 (band
crown; T-238 opening crown 3.000); above it only the layer-1 facade lines +9.60 / +9.80 and layer-5 +10.16 / +10.595:
plain masonry face between the crown and the facade band, consistent with a lintel under the 3.45 piece soffit. The
P7757.dxf holds only the SE / NW elevations: the SW / NE heads (W05-W07, W19-W29) rest on the merged T-201 vector DWF
reads (Checker-verified 23 Oct); the Checker should re-read 2 of them.

## 6. Freelancer

He has no lintel concrete row and no stair waist split (T-571 / T-258): NOT_COMPARABLE; 'within 95 %' is not claimable.

## 7. Rules and lessons

R-T673-1 / -2 / -3 1.0.0 (scope every villa; text in `t673_rules.py`). Tests: villa V673 by hand (normal 0.068 .. 0.106;
flip inside tolerance HELD_BY_NAME; member serves FLAGGED; deficit end = R-T524-1 code (second route); ceiling pair pier
once 0.158; released neighbour; capped end OPEN / extended; mirror); adverse: a door wider than its schedule mark re-banded
(L2 D 0.25, never the mark's D), unprinted band gap, above last band and curved head refused, mm / cm, bool, NaN,
unrecorded neighbour, 0 for HELD, designer without id. Lessons row (proposed, ERS s.7):

| 2026-11-10 | 14 lintels sat HELD 'head not established' while their heads were DRAWING-CONFIRMED on merged reads (T-201 / T-238) | the lintel ledger read only the opening census r3, which never received the later head reads | a downstream ledger reads every merged evidence source for its input (census + head reads), and a drawn head decides existence only when the decision holds within the read's own tolerance | tests/t673_lintel_stair_census | PROPOSED |
