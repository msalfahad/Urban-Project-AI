# T-200 Level chain, run 1 (residential review R5): every level a named physical datum

Worker 1 (lane S), 2026-10-23, run session_01WrV9qErm9oTivPi8KTrJrp. New UNWIRED check module
`engine/source/level_chain_v1.py` (stdlib only; no method version, route G, rule / knowledge version or released quantity
changed), hand fixture + adverse tests `tests/t200_level_chain/` (26 pass), development-villa input
`ALSENAN_LEVEL_INPUT.json` (values, Drive file titles, layers and handles only), runner `t200_alsenan_check.py`, output
`summary.json`. Development villa, not an accuracy claim. ERS s.2-4 and s.7 applied.

## 1. The physical question

A height in a BOQ is the vertical distance between two named physical surfaces. Four errors on the development villa came
from taking whichever level was nearest: the pool's finished water depth used as the RC wall height (T-183 r1), the
W01 / W03 sills measured from the court ground line (T-194 before T-198), necks run to the finished floor on an
unprinted founding depth (T-167 / Q-21 C), and stair heads placed against B20 / B23 with the beam top taken at the
finished floor (T-189 / T-192). Excavation (T-170) cannot be measured until the chain existing ground -> formation ->
blinding -> footing -> ground beam -> slab -> floor is named and sourced.

Chain per storey / element family (module TEMPLATES; a project can give its own links):

| Family | Links (upper -> lower : layer) |
|---|---|
| FLOOR | FFL -> SLAB_TOP : FLOOR_BUILD_UP; SLAB_TOP -> SLAB_SOFFIT : SLAB_THICKNESS; SLAB_TOP -> BEAM_BOTTOM : BEAM_DEPTH |
| ROOF | FINISHED_ROOF -> SLAB_TOP : ROOF_BUILD_UP; slab / beam as FLOOR; PARAPET_TOP -> FINISHED_ROOF : PARAPET_HEIGHT |
| FOUNDATION | FFL -> SLAB_TOP; SLAB_TOP -> GB_TOP; GB_TOP -> GB_BOTTOM; GB_TOP -> FOOTING_TOP : NECK_RUN; FOOTING_TOP -> FOOTING_BOTTOM; FOOTING_BOTTOM -> BLINDING_TOP : UNDERLAY; BLINDING_TOP -> FORMATION; EXISTING_GROUND -> FORMATION : EXCAVATION_DEPTH |
| POOL | RIM -> FINISHED_FLOOR : FINISHED_DEPTH; FINISHED_FLOOR -> BASE_TOP : FLOOR_BUILD_UP; RIM -> BASE_TOP : RC_WALL_HEIGHT; BASE_TOP -> BASE_UNDERSIDE; -> BLINDING_TOP : UNDERLAY; -> FORMATION; EXISTING_GROUND -> FORMATION |

Every datum is FINISHED (FFL, finished roof, finished ground, finished pool floor, parapet top), STRUCTURAL (slab top /
soffit, beam bottom, ground-beam top / bottom, footing top / bottom, pool rim / base) or SUBSTRATE (blinding top,
formation, existing ground). A link is VERIFIED / DRAWING-CONFIRMED / ASSUMED — OWNER-APPROVED (weakest input), HELD
(missing datum or layer NAMED, value None, never 0, never a convention) or CONFLICT (two printed values for one datum,
or two printed datums contradicting the printed layer between them; every value DERIVED through such a datum becomes
CONFLICT too). Printed limits ("not less than 1.5 m") stay limits (SATISFIED / VIOLATED / OPEN), never values. Owner
manual layers (Q-43 0.10 floor finishing) are listed beside the chain and never used to derive a structural datum.
Uses of a level by a quantity are checked: FINISHED_AS_STRUCTURAL, STRUCTURAL_AS_FINISHED, WRONG_REFERENCE,
VALUE_NOT_FROM_DRAWINGS, NEEDS_HELD, OK (with the use's own stated margin, if any). Two zero systems are one datum only
when `zero_relation_from_marks` fits the marks both sets print (one translation, same texts, same offset).

## 2. What the development villa's drawings print (read this run)

Sources (Drive "Alsenan chalet project"): ST7757 dxf.dxf (level texts, all 22: ezdxf, nested inserts), P7757 DXF
(level texts, 39, and every vertical DIMENSION chain), p7757_arch_sheet10.pdf SECTION A-A and p7757_arch_sheet09.pdf
NORTH EAST ELEVATION (raster, rendered at 200 dpi and read visually), ST7757.pdf notes via T-042 / T-044 / T-183 / T-189
(merged, Checker-verified source references; their quantities are not used as proof).

| Datum | Value | Evidence | Status |
|---|---|---|---|
| Existing plot level | +-0.00 | P7757 block LEL x6; ST SH08 the same 6; SECTION A-A both ends | DRAWING-CONFIRMED |
| Court finished ground | +0.15 | P7757 LEVEL x6; ST SH08 x6; elevation chain base (DIMENSION 2A72) | DRAWING-CONFIRMED |
| Annex FFL / entrance | +0.30 | P7757 401, 403, 405, 4AC; ST SH08 1B0, 1B2, 1B4, 1C9 | DRAWING-CONFIRMED |
| GF FFL | +1.00 | P7757 A74, 411, 40F, 413; ST SH08 1CD, 1C0, 1BE, 1C2; SECTION A-A; NE elevation cut | DRAWING-CONFIRMED |
| Annex roof (finished) | +4.30, parapet +4.80 | P7757 D20 / 244B, DIMENSION 24AE 4000, 24BC 500 | DRAWING-CONFIRMED |
| 1F FFL | +5.50 | P7757 D1B, D16, D1D, D18, 1251; DIMENSION 29D0 5500; SECTION A-A | DRAWING-CONFIRMED |
| 2F FFL / 1F-roof terrace | +9.70 | P7757 1352, 134E, 1350; DIMENSION 29FC 8700 above +1.00; SECTION A-A; ST SH02 3F6, 3F4 (placed on the terrace beside the penthouse slab, rendered) | DRAWING-CONFIRMED |
| 2F roof (finished) | +13.90, parapet +14.40 | SECTION A-A marker '+13.90'; DIMENSION 2A0A 4200, 2A18 500 (no level text in the DXF) | DRAWING-CONFIRMED |
| Storey heights FFL -> FFL | GF 4.50, 1F 4.20, 2F 4.20 | the same chains; the chain total 1440 = 100 + 870 + 420 + 50 (SECTION A-A, NE elevation) | DRAWING-CONFIRMED |
| Any STRUCTURAL slab / beam top, soffit | none | **no sheet of either set prints one**: ST7757 prints only the architectural values (+-0.00 / +0.15 / +0.30 / +1.00 on SH08, +9.70 on SH02); the architectural cuts draw one slab band per floor with the FFL marker on its top line and no floor build-up | HELD |
| Slab thickness | 0.16 suspended ("unless stated otherwise"), 0.10 ground slab (T=10cm, main house and annex) | ST SH12 S-NOTE / PDF p.8 note 18; SH08 callouts | DRAWING-CONFIRMED (layers only) |
| B20 / B23 depth | 0.75 | ST PDF p.10 schedule (T-189) | DRAWING-CONFIRMED (layer) |
| Footing underside (founding level) | none | PDF p.8 note 12 leaves it to the site (contractor + supervising engineer); owner Q-21 C | HELD |
| Formation | AT_MOST -1.50 (limit) | SH11 boxed note 1: excavation not less than 1.5 m below the existing plot level | OPEN (limit, no value) |
| Under footings | blinding 0.10; '5cm Screed' + membrane + an unread '2' | PDF p.13 (T-042) | blinding DRAWING-CONFIRMED; UNDERLAY HELD |
| Exterior ground-beam top | "Ground Floor slab level" (a name) | PDF p.13 exterior detail | layer 0.00 to the (HELD) slab top |
| Pool rim / finished floor / structure line | +0.30 / -0.85 / -0.90 | P7757 NW elevation cut (T-183 r2) | VERIFIED (Checker 2026-10-22 16:14) |
| Pool base | 0.40 (ST detail) vs 0.15 drawn in the architectural cut (-0.90 .. -1.05) | ST SH01 / PDF p.7; P7757 cut | CONFLICT as printed; T-183 r2 ruling: the structural detail governs the RC thickness, the architectural cut the levels |

**Is the architectural +-0.00 the structural +-0.00?** Yes, DRAWING-CONFIRMED: one plan translation puts 19 of the 20
level marks of ST7757 SH08 on P7757 GF-plan marks with the same text (the 20th is a plot-boundary +-0.00 with no
partner); every matched pair gives offset 0.000. The finding behind it matters more: the structural set has **no
structural datum of its own**; its level marks are the architect's finished levels copied.

## 3. Result on the development villa (`summary.json`, run "with_t183_ruling"; 33 links)

| Chain | Links | Result |
|---|---|---|
| GF / 1F / 2F floors, 2F roof, annex floor / roof | 20 | every FFL -> slab top link HELD (build-up printed nowhere); therefore every slab top, soffit and beam-bottom LEVEL HELD; slab thickness and beam depth printed as layers only; parapets 0.50 / 0.50 DRAWING-CONFIRMED |
| Foundation (exterior ground beam over F8) | 8 | all HELD: slab top (build-up), ground-beam top (follows the slab top), founding level (Q-21 C), screed / membrane stack (the '2' unread); formation limit -1.50 OPEN |
| Pool | 7 | rim -> structure 1.20 VERIFIED, finished depth 1.15 VERIFIED, build-up 0.05 VERIFIED, base 0.40 VERIFIED -> underside -1.30, underlay 0.10 + blinding 0.10 -> formation **-1.50**, excavation from the plot level 1.50 DRAWING-CONFIRMED (= T-183 r2 -1.50). As printed (without the ruling) the base link is a CONFLICT (0.15 vs 0.40) and the formation is CONFLICT, never -1.25 |

The four known cases, found from the drawings (uses in the input, each with the ledger it came from):

| Case | Use | Code | Size |
|---|---|---|---|
| Pool wall (T-183 r1) | rim -> finished pool floor as the RC wall height | FINISHED_AS_STRUCTURAL | +0.050 m (1.15 vs 1.20; 2.710 vs 2.828 m3 in r1); r2 OK |
| W01 / W03 sills (T-194) | chain 2A72 read from the +0.15 court line | WRONG_REFERENCE | -0.850 m on every sill / head (1.85 / 3.85 vs 1.00 / 3.00); T-198 r3 OK |
| Necks (route G profile NECK_TOP_LEVEL_M 1.00) | neck top = GF FFL +1.00 | FINISHED_AS_STRUCTURAL; footing end NEEDS_HELD | the neck runs to the ground-beam top, a structural surface below the FFL by the (unprinted) build-up; even with a printed founding level the released V2.9 necks (10.855 m3, PROVISIONAL, h = 1.00 + 1.50 - H) would be long by that build-up x each neck section; amount not measured |
| Stair heads in B20 / B23 (T-189) | beam top = FFL +5.50 / +9.70 | FINISHED_AS_STRUCTURAL | T-189's own margin (0.289 m down, 0.167 m up) covers any build-up up to 0.289 m (the owner's manual 0.10 would give +5.40 / +9.60, inside it), but no structural level is printed, so the T-189 ledger is "unchanged if the build-up <= 0.289 m", not proven |

## 4. Engine vs freelancer (what this changes): nothing released, nothing re-measured

No quantity changes in this run (a check module). Affected lines, for the integration lane: necks (released V2.9 10.855
m3 PROVISIONAL vs freelancer 8.805 m3 at an unprinted 1.50 m; V3.0.4+ HELD 3.075 .. 15.375 m3): UNRESOLVED (founding
level and slab build-up both unprinted); every column / wall / plaster height that takes FFL -> FFL is unaffected only
while the build-up is the same on both floors (GF slab on ground vs suspended slabs: not printed, not proven);
excavation / backfill (T-170): blocked by the HELD foundation chain except the pool (formation -1.50 established).

## 5. Rule, lessons row, verdict proposals

Proposed rule UP-LEVEL-DATUM-001 (any villa, provenance: T-200 + the four cases): every height used by a quantity is the
difference of two NAMED datums of the right class (finished vs structural vs substrate) with a printed source each; a
relative height is measured from the datum of the floor / element it belongs to; a structural level is never taken from
a finished level without a printed build-up; when no sheet prints the structural level, the dependent quantity is HELD
(or carried with the use's own stated margin as information), never defaulted; a printed limit is not a value.

Lessons-register row (ERS s.7) proposed:
| 2026-10-23 | Four heights taken from the nearest level (pool finished depth, sills from the ground line, necks and stair-head beams to the FFL) | Levels used without naming which physical surface each one is, and the structural set prints no structural level (it copies the architect's finished levels, 19 / 20 marks identical) | UP-LEVEL-DATUM-001: every height = two named datums of the right class with printed sources; structural from finished only through a printed build-up; else HELD (any villa) | tests/t200_level_chain (normal: hand chain; adverse: conflict, mismatch with derived values, finished-as-structural, wrong reference, missing datum, limit, zero systems) | rule proposed; module READY |

Verdict proposals: pool wall height ENGINE_RIGHT after T-183 r2 (1.20 from the structure line, drawing); sills
ENGINE_RIGHT after T-198; necks UNRESOLVED (both ends unprinted; designer RFI already proposed in T-042 B4); stair /
beam ownership: T-189 rev2 stands within its stated margin, proof waits on a printed structural level (no new owner
question: the gap is a designer item, ERS 2.7 does not call for the owner).

## 6. For the Checker (re-measure from the drawings, not from this file)

1. ST7757 dxf.dxf SH02: the two '+9.70' LEVEL texts (handles 3F6, 3F4) lie on the 1F-roof terrace outside the
   penthouse slab, i.e. the architectural 2F level, not the 2F roof.
2. p7757_arch_sheet10.pdf SECTION A-A: markers +1.00 / +5.50 / +9.70 / +13.90 sit on the top line of a single drawn slab
   band; no floor build-up drawn; chain 100 / 870 / 420 / 50 = 1440.
3. Zero fit: ST SH08 vs P7757 GF plan level marks, 19 of 20 coincide by one translation with the same text.
4. Pool chain -0.90 / -1.30 / -1.50 against T-183 r2's sources (P7757 NW cut, ST p.7).

## 7. Not done / uncertain (run 2 of R5)

- Not read: ST7757 PDF slab sections (whether any detail prints a T.O.S.), the sanitary drawing (falls, sunken wet
  slabs), the stair section's landing levels; the '2' under the footings.
- Per-footing chains (14 footing types, depths 0.30 .. 0.70) and per-room wet-slab chains are not entered; one typical
  footing (F8) and one chain per storey only.
- The module is unwired: wiring (default guard companion, a HELD reason LEVEL_NOT_PRINTED on neck / excavation /
  stair-head lines) is lane I work.
