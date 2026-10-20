# T-121 Soffits and slabs over open air (development villa; NO REPO CODE)

Worker 2, 2026-10-20. Gate 2 (architectural coverage: ceilings) with a gate 3 check (concrete: is every slab piece over
outside air in the concrete route). Rules: directive 2026-10-20 2.2 (statuses) and 5.1 (missing scope is never zero),
UP-QTY-STATUS-001, owner Q-20 (no concrete counted twice), Q-17 A (DRAWING-VERIFIED values). The soffit FINISH has no
Urban rule: every area below is a CALCULATED geometry, the finish stays HELD (one owner question for the Lead, all places).
Data: Drive "Alsenan chalet project" / P7757_DXF_COMPRESSED.zip (plan DXF sha256 ab54dd55...31cc4), "ST7757 dxf.dxf"
(sha256 9f9d1179...38079), p7757_arch_sheet09.pdf (elevation) and p7757_arch_sheet10.pdf (section A-A), read in the
scratchpad, never copied here. Per-place table: `PLACES.csv`. Reproduce: `slab_over_air_census.py` (see its docstring).

## Method (engineering calculation from the drawn faces, no assumed value)

1. Route G (the scored basis: `tools/urban_boq_m2.compute`, conventions V6) on the structural DXF gives every slab-plan
   face with its class (PANEL, BEAM strip, COLUMN, OPENING) and the STR.CONC.SLAB line that measures each panel.
2. Each slab sheet is placed on the architectural plan of the storey under it by the translation that the column
   outlines agree on: GROUND FLOOR ROOF SLAB on the GF plan (13 columns of equal size coincide exactly), FIRST FLOOR ROOF
   SLAB on the 1F plan (15), SECOND FLOOR ROOF SLAB on the 2F plan (5); one translation per sheet, no rotation, no scale.
3. Outside air under a slab = outside the storey's facade outline (ARCH_TAKEOFF_V2.9), plus the GF open-air side passage
   that the outline bridges (T-109, 1.20 x 4.70 m), less that storey's columns. Soffit = slab panels + beam strips over it;
   faces labelled VOID are open, never soffit; strips narrower than 0.10 m are offsets between the slab edge line and the
   facade line (listed apart, not counted).
4. Above each piece: the next storey's rooms (wet / dry), its walls, or nothing (roof / outside its outline).
5. Every printed dimension near each place was read on the plans (GF and 1F) to hand-check the CAD area where the
   outline is straight.

## Result: five places, 45.632 m2 of soffit over outside air (CALCULATED), finish HELD

| Place | Soffit m2 | Hand check | Above it | Slab concrete over air (in route G?) | Freelancer |
|---|---|---|---|---|---|
| PL-01 GF entrance porch (+0.15, entrance steps), under the 1F master-bedroom block | 19.181 | 4.60 x 4.096 + 4.40 x 0.20 + 0.02 - 1.40 x 0.40 = 19.182 | 1F master bedroom (dry) 16.084, 1F walls 1.379, 0.20 m slab edge beyond the 1F walls 1.718 | panels 17.003 m2 = 2.721 m3, 5 STR.CONC.SLAB GF lines (PROVISIONAL, sheet-uniform 0.16): included | no row |
| PL-02 GF open-air side passage (T-109) | 5.640 | 1.20 x 4.70 = 5.640 | 1F bathroom (WET) 2.940, bedroom corner 0.724, 1F walls 0.420 (= T-109's 4.084), GF roof slab with no room above 1.556 | panels 5.160 m2 = 0.826 m3 (1 line SOURCE_DERIVED, printed T 16; 2 PROVISIONAL): included | no row |
| PL-03 GF pool court (deck +0.15 and pool) east of the curved bedroom glazing | 14.020 | CAD (curved edges): gross 18.393 - printed VOID 4.373 | 1F master bedroom (dry) 5.787, 1F bathroom (WET) 0.986, 1F walls 1.111, 1F roof strip at +5.50 round the void 6.136 | panels 9.017 m2 = 1.443 m3, 9 lines PROVISIONAL: included; the void face is not a beam line (no 4.37 m2 band exists) | exterior plaster "ceiling above the swimming pool" 2 x 3.14 x 3.05 = 19.154 |
| PL-04 1F roof slab east edge (strips 0.29-0.40 m beyond CB12, slab round the 1F curved glazing) over the 1F roof strip / pool void | 4.374 | CAD 3.189 + 0.873 + 0.312 | nothing (outside the 2F) | panels 1.958 m2 = 0.313 m3, 3 lines PROVISIONAL: included | no row |
| PL-05 1F roof slab west and north edge band 0.20 m beyond the 1F bedroom walls | 2.417 | about 12 m x 0.20 | nothing | panels 0.014 m2; the band is a BEAM-strip face (2.402 m2): concrete only through a beam band line, not traced here | no row |
| **Total** | **45.632** | | rooms 26.521 (wet 3.926, dry 22.595), walls 2.910, open 16.201 | panels 33.152 m2 = **5.304 m3, all in STR.CONC.SLAB lines**; beam strips 12.478 m2 | 19.154 (pool only) |

Places looked for and NOT found over outside air: the second-floor roof (no piece wider than 0.10 m), balconies (none
drawn on any plan), the annex roof (+4.30, inside the GF outline), the court (no slab over it), the south indoor garden
strip of the GF living area (inside the house: no wall or glazing between it and the living, label GARDEN on layer 2
planter lines; the GF roof slab over it is a roof over interior, not a soffit). Edge offsets narrower than 0.10 m
(not counted): GF roof 0.182, 1F roof 0.227, 2F roof 0.355 m2 (slab edge line up to 0.075 m off the facade line).

## Concrete: no silent omission, but the beam strips are not traced

Every slab panel over outside air is measured by a STR.CONC.SLAB line of the scored V2.9 run (route G, conventions V6):
5.304 m3 (GF 4.989, 1F 0.316), inside the GF roof slab 33.353 m3 (freelancer GF slab 207 m2 x 0.16 = 33.12 m3, one lump
area; +0.23 m3, +0.7 %: his lump is consistent with the porch and pool-court pieces being included, not provable). The
12.478 m2 of beam-strip faces under these soffits are measured as beam bands (length x width x depth), not as faces;
which band covers which face is the beam register's work (T-110), not redone here. CONCRETE_LEDGER_V3 is not on the
working branch (T-097 REJECTED, rework T-105 TODO), so it cannot be checked; CONCRETE_LEDGER_V2 changes only
BOUNDARY_WALL / POOL strips, so slab inclusion is the same as the scored run. The 1F roof edge bands (PL-04 strips
0.29-0.40 m, PL-05 0.20 m) are drawn beyond the walls on the slab plan and on the 1F plan: what they are (slab edge,
beam, decorative band) decides their concrete class -> designer D-25.

## Who is right (pool court) and what neither BOQ has

- Pool-court soffit: hand 14.020 m2 vs freelancer 19.154 m2: +5.134 m2 (+36.6 % on hand). Against the gross area with
  the void (18.393 m2) his figure is +0.761 (+4.1 %). His 2 x 3.14 x 3.05 is not read on any drawing; the void is
  printed on the GF roof slab plan (VOID, B7 ring) and on the 1F plan (elliptical VOID, 306): if his figure is the gross,
  HAND_RIGHT by 4.373 m2. Proposal UNRESOLVED until the verifier reads his basis.
- Porch 19.181 + passage 5.640 + 1F roof edges 6.791 = 31.612 m2 of soffit: no engine line and no freelancer row (his
  decor ceilings 337.57 + 72.01 m2 and the decor paint 452.33 m2 are named interior rooms only; his exterior plaster
  lists elevations and the pool ceiling only). Missing scope in both, kept visible: M-08, M-09, M-10.
- No sheet read draws insulation, waterproofing, a drip or a finish under any of these slabs (plans, section A-A on
  sheet 10, elevation on sheet 9, structural details: the only insulation note is the pool tank's 5 cm membrane). Two
  WET floors stand over outside air: the 1F bathroom over the side passage (2.940 m2) and the 1F bathroom over the pool
  court (0.986 m2) -> designer D-24 (no owner question: a detail, not a choice).

## Finding for the verifier on T-109 (READY, not changed here)

T-109 reads the passage as 4.08 m2 under the 1F and 1.56 m2 "open to the sky", taking the 1F outline as the plate above.
The GF roof slab plan draws a slab panel (5 T10 / m both ways) over the whole south end of the passage up to the
boundary beam, and the 1F plan draws the roof hatch there: all 5.640 m2 are roofed (4.084 under 1F rooms and walls,
1.556 under the GF roof). By T-109's own rule 5 (fully covered, one open mouth -> HELD with both runs) its GF facade run
would be HELD 98.887 .. 105.887 m instead of RESOLVED 105.887 m, unless the verifier decides that the mouth open to the
porch (itself open to the court) makes the space outside air. Not decided here.

## What is learned / missing

- The architectural plan's facade outline is not the plate above: the structural slab plan is. A plan-only reading
  misses slabs over outside air (T-109's 1.56 m2) and cannot see edge bands.
- A void drawn inside a beam ring becomes a BEAM-strip face in route G ("inside a beam band"); it carries no beam line,
  so no concrete is added, but any face-area reading (soffit, formwork) must drop VOID-labelled faces.
- Missing: the soffit finish (HELD 45.632 m2, one owner question for the Lead); designer D-24 (build-up under slabs
  over air, wet floors over air) and D-25 (edge bands); beam-strip face to band tracing (T-110); ledger V3 (T-105).
