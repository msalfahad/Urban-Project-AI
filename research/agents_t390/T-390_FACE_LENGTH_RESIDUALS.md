# T-390: face-length residuals between the T-250 face walk and the T-128 open sides (development villa; method every villa)

Worker 2, 2026-10-31 10:40 UTC onward, run session_01E6cPnaqdDd1awLqouVszh6. Lane A, gate 2, backlog-permitted.
Research + tests only: no engine module, rule / knowledge version, registry, merged ledger or candidate line changed;
**no quantity changes**. Drawing: Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip -> P7757.dxf (sha256
ab54dd55..., INSUNITS 4 = mm), read with the merged T-125 / T-250 capture (the T-128 r3 walk re-executed unchanged and
reproducing walk_r3.json on 32 / 32 rooms, `alsenan_t250.py --check` PASS) plus a direct ezdxf read of the entities
named below. Self-check (codemap check, pytest t061, freeze): PASS. Development villa, not an accuracy claim.

## 1. Physical element (ERS s.2.1)

A room face is the drawn wall / column surface the room touches, between its drawn ends. An open side (the walk's
VIRTUAL class: no drawn line) is not wall and carries no plaster, paint, backing or tile. Where an open side meets a
continuous wall face (T-junction), crosses the line of a captured band that is not built there, or runs on past a drawn
wall end, the wall face stops at the drawn line; nothing physical is added. A short VIRTUAL piece (< 0.10 m) between two
drawn lines at a corner is region / drafting noise on a wall corner and stays face (T-128 r3 merge rule).

## 2. Reconstruction from the drawing (handles on P7757.dxf; coordinates stay in scratch)

| residual (T-388 F2) | where | drawn evidence | cause, in m |
|---|---|---|---|
| GF-07 pantry -0.120 | open side to the dining, 4.490 m (one walk run) | no layer-1 wall line within 0.40 m of the line where the band WB-FL0007-FL0008 would cross the open edge (only LINE B3, layer 5, 4.000 m, along the open edge, and two layer-5 polylines 176 / 177); GF-W01 face LINE A6 (layer 1) 3.000 m, ending at the open edge where it continues collinear as LINE 104 (15.970 m drawn, GF-08's face): one continuous wall | **CROSSING** 0.05 + 0.05 m (the open side passes both face lines of the unbuilt V2 stretch 1.65 .. 14.92 m; +/- 0.025 m face tolerance each) + **T_JUNCTION** 0.02 m (the open side ends perpendicular on the A6 / 104 face; 4 samples within 0.025 m) = 0.120 m |
| GF-08 dining -0.140 | the same pantry open side + the 1.245 m open side to GF-14 | the same stretch and A6 / 104; GF-W13 face LINE 222 (layer 1) where the GF-14 open side ends; GF-W28 end face LINE BC (layer 1, 0.150 m) at the other end, parallel layer-2 lines 2DB / 2DC (0.150 apart) across the opening | CROSSING 0.10 + T_JUNCTION 0.02 (A6 / 104) + T_JUNCTION 0.02 (222) = 0.140 m; the 0.02 m VIRTUAL corner jog at BC is a corner piece (face, both walks) |
| GF-14 wash lobby -0.045 | the 1.245 m open side to the dining | the GF-W28 face LINE D2 (layer 1, 0.794 m) ends at BC; the open side runs on collinear with it | **END_REACH** 0.025 m (5 samples within the 0.03 m end reach past BC) + T_JUNCTION 0.02 m (222) = 0.045 m; the 0.01 m corner piece at BC stays face |
| GF-W01 run #2: 3.015 vs drawn 3.000 (Checker) | GF-07 on GF-W01 | A6 3.000 m | 3.015 = 2.995 WALL (A6 at 5 mm samples: one sample at the corner) + 0.020 T_JUNCTION artefact; the physical face is **3.000 m (A6)**, the walk 2.995 |

Both merged walks read the same open sides: the capture's open-side runs equal walk_r3.json `virtual_m` on all 32 rooms
(guard). T-250 is right in its `finish_m` (WALL + COLUMN, it never counted these metres as finish) but books the VIRTUAL
samples that pass the face tolerance into `face_m`; T-388 (d') then built the geometric face as contour less T-250's
OFF-LINE virtual only, i.e. it counted those samples as face. **The residuals are in the check, not in the candidate.**

## 3. Rule R-T390-1 (proposed; scope every villa; provenance: T-128 r3 merge rule + T-250 tolerances, Checker-merged; this reconciliation) - `face_length_rule.py`

(a) geometric face per room = walked contour - open-side runs (maximal cyclic VIRTUAL runs >= 0.10 m); a shorter
VIRTUAL run between drawn lines is a corner piece and stays face. (b) An open-side sample a crosswalk puts on a band
face line is an artefact, named CROSSING / T_JUNCTION / END_REACH from the run direction against the band;
ON_FACE_PARALLEL (on the face line inside the band span: a band but no drawn line) is never face and is flagged
UNRESOLVED for a drawing check. (c) Per-wall face length = crosswalk face metres - artefact metres; every family closes
on (a). (d) Refused: an open-side piece offered as face; a jamb return counted twice; a face measured past its drawn end
into an open side; mm units; a missing length treated as 0.

## 4. Results (files in this folder; `alsenan_t390.py <t250_capture.pkl> --out . --check`)

| measure | value |
|---|---|
| rooms / family rows re-run (T-388 closures) | 32 / 64 |
| T-388 (d') residuals over 0.025 m | 8 (the 6 F2 + 2 GF-16 already explained) |
| under R-T390-1: OPEN / EXPLAINED / CLOSED | **0** / 2 (GF-16, T-074 VERIFIED outline, -0.544 m) / 62 |
| rooms whose T-388 face moves | 9: GF-07 -0.120, GF-08 -0.140, GF-14 -0.045 (the F2 three) and 1F-13 +0.02, 2F-01 -0.02, GF-15 +0.02, ST-1F -0.02, ST-2F -0.02 (inside 0.025 already), GF-16 |
| band sides carrying VIRTUAL metres (19) | artefact CROSSING 0.230 + T_JUNCTION 0.160 + END_REACH 0.025 = **0.415 m**; corner pieces 0.090 m (face); ON_FACE_PARALLEL **0** |
| T-388 face rows changed (T388_FACES_CORRECTED_T390.csv) | 12 rows, 0.415 m; e.g. GF-07 / GF-W01 3.015 -> 2.995, GF-08 / GF-W01 13.856 -> 13.836, GF-14 / GF-W28 0.830 -> 0.805, the GF-07 stretch row 0.100 -> 0.000; 4 rows unchanged (their VIRTUAL is a corner piece) |

Corrected room face lengths (= the candidate's own): **GF-07 10.491 m, GF-08 53.188 m, GF-14 8.267 m**,
DRAWING-CONFIRMED. Per face, at the owner top, the artefact is 0.067 .. 0.365 m2 of information only: every wall-tile,
backing, plaster and paint line is per room on the T-128 / T-312 / T-329 lengths, which already exclude it.

## 5. Verdict proposals (no freelancer figure is used or needed)

- T-388 F2 FACE_LENGTH_RESIDUAL (pantry tile / backing -0.438 m2 each, GF-14 -0.164 m2 each, GF-08 plaster / paint
  -0.511 m2 each): **ENGINE_RIGHT**: the candidate lengths are the drawn faces; the residual is the T-388 check's
  geometric face (contour less off-line virtual). Nothing to add to any line; pantry tile stays 32.3422 m2 basis.
- T-250 `face_m`: carries 0.415 m of tolerance artefact on 12 faces (its `finish_m` is right). Proposed lane I / T-388
  consumer fix (Lead): use R-T390-1 (a) for the (d') closure and `face_m - artefact` for the T-388 face table lengths;
  no candidate quantity moves (assert totals unchanged).
- Checker's GF-W01 point: the face is A6 **3.000 m**; +0.015 (0.020 sampled) is the T-junction of the pantry open side.

## 6. For the Checker (re-measure on P7757.dxf)

1. LINE A6 (layer 1) 3.000 m and LINE 104 collinear from its east end: one wall face, no wall end at the pantry edge.
2. No layer-1 / column entity where the pantry open side (LINE B3, layer 5) crosses the WB-FL0007-FL0008 line (V2 stretch
   1.65 .. 14.92 m outside every run): the 0.10 m is not a wall.
3. GF-W28: D2 0.794 m ending at BC (0.150 m); the GF-14 open side runs on collinear past BC (0.025 m END_REACH); the
   other end of the opening on LINE 222 (GF-W13 face): T-junction 0.02.
Reproduce: T-125 dump -> `capture_t250.py` -> `alsenan_t390.py <capture> --check` (guards PASS).

## 7. Limits

- The causes are read from the walk samples and the drawn entities around them; the T-147 room regions themselves were
  not re-derived (merged, VERIFIED boundary). LINE B3 (layer 5) along the pantry edge is not interpreted here (beam /
  floor edge line): it is not a wall face either way; any soffit or bulkhead over the open edge is a ceiling item.
- GF-16: R-T390-1 (a) gives 8.169 m from the walk (open side 0.145 m) while ROOMS_T128_R3 lists 0 open side; the
  family length 7.625 follows the T-074 VERIFIED outline (T-312), already explained; unchanged here.

## 8. Lessons-register row proposed (ERS s.7)

| what happened | why | rule |
|---|---|---|
| A face check reported 0.045 .. 0.140 m 'missing face' on three rooms whose ledgers were right | the check took the geometric face as contour less the crosswalk's OFF-LINE open side; the crosswalk had put open-side samples within its 0.025 m face / 0.03 m end tolerance onto band faces | R-T390-1: the geometric face is contour less the open-side RUNS; open-side samples on a face line are named artefacts (crossing / T-junction / end reach), never face; a face stops at its drawn end |

## 9. Tests

`tests/t390_face_length/test_t390_face_length.py` (12): hand fixture NOT the development villa (kitchen 4.00 x 3.00 with
an open side, a continuous wall past it and an unbuilt captured band crossing it; hand values in the docstring:
geometric face 11.00 m, artefact 0.15 m, the old construct's false -0.15 m / -0.45 m2), in plain, mirrored, rotated and
mirrored + rotated positions; END_REACH past a drawn end (0.030 m), corner run kept as face, cyclic run across the ring
start, ON_FACE_PARALLEL flagged; adverse: open side offered as face, face past its drawn end into an open side, jamb
return counted twice, mm units, missing length, HELD top; and the committed development-villa outputs.
