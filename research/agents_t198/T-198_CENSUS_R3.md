# T-198: doors / windows census r3 from the R6 findings (development villa; rule for every villa)

Worker 2, 2026-10-23 01:45 - 02:05 UTC, run session_01Hq4z6mDEJGVBWuTofmVwzF. Lane A, gate 1, backlog-permitted. A NEW
census version (`OPENINGS_T198.csv`; the merged `research/agents_t150/OPENINGS_T150.csv` is untouched) and the downstream
deltas it causes (`DOWNSTREAM_T198.csv`), built by `alsenan_t198.py` from repository files only (`--check` reproduces).
Generic functions in `census_r3.py` (re-datum, consequences per opening, wall net before / after, census revision).
No engine file, rule file, registry, frozen method or released quantity changed. ERS: read; s.2 steps 1-4, s.3 (build
before deduct, a notation's datum before its arithmetic, installed vs physical), s.4 (rule + test), s.7 row below.
Development villa, not an accuracy claim. Drawings cited by Drive title; no coordinate, image or client name committed.

## 1. Result in engineering terms

| Change | Opening | What moves | Status |
|---|---|---|---|
| C1 added | P-GF-01 0.90 doorless, GF stair hall -> basin space, inside GF-W14's gross | nothing established: GF-W14 net stays HELD 12.181 .. 15.556 m2 (T-175 had it); NEW head soffit 0.180 m2 (0.90 x 0.20) | width DRAWING-CONFIRMED, head HELD |
| C2 added | P-1F-01 1.30 doorless, 1F east master bed -> its entry, OUTSIDE the hand runs | no deduction (nothing in the gross); lintel 2.10 m already RELEASED in S8.6 (0.063 m3; 1.30 + 2 x 0.40 reproduces it); **two scope gaps**: masonry above the lintel (black 0.15) in no T-143 row, 0 .. 4.992 m2 (0 .. 0.749 m3), and the two plaster / paint faces above the head in no T-128 room face, 0 .. 8.710 m2 (owner H 3.35) / 0 .. 10.504 m2 (drawing H 4.04); head soffit 0.195 m2 | width DC, head HELD, gaps HELD (bounds, never a quantity) |
| C3 added | P-GF-05 1.20, mouth of the side passage in the court wall line, both sides outdoors at +0.15 | no deduction (open side, in no run); head soffit 0.240 m2 (Sigma); Sigma reveal head 1.20 + jambs HELD (absent from the T-162 facade list); face above the head UNKNOWN; **threshold 1.200 m.l -> UNKNOWN** (no door, no level change): established thresholds 42.22 -> 41.02 m.l | width DC, head HELD, plan vs elevation DIFFER on the head |
| C4 re-datum | W01 | SILL_M 1.85 -> 1.00 above the +1.00 hall floor, head 3.85 -> 3.00; absolute +2.00 / +4.00 now in the census; area 2.400 m2, block 2.400 m2 (T-175), T-128 band 1.0 / 3.0 unchanged | DRAWING-CONFIRMED (own read) |
| C5 re-datum | W03 | SILL_M 1.00 -> 0.00, head 5.30 -> 4.30 above FFL; area 28.251 m2 unchanged; glazed line, no masonry | DRAWING-CONFIRMED (own read) |
| C6 pcs | windows | WINDOW.ALUMINIUM[nr]: r2 "29 vs 29 AGREE" -> 28 settled + W02 HELD (1 or 2 windows, T-161 F23 / D-53) = 29 .. 30 vs his 29: line HELD (T-181 verdict faa04202) | HELD |
| C7 | 9 small squares (SE above W14; fence elevation above W11 / W12) | listed UNKNOWN in `ELEVATION_ONLY_T198.csv`, no line (<= 0.09 m2 if through-wall) | UNKNOWN |

Established block m2: **0.000 change** (T-176 can proceed on T-175's nets). Engine vs freelancer: no compared quantity
moves (windows m2 on the same 8: 56.771 vs 54.931, +3.35 %, T-181); the additions have no freelancer row (he prices no
leafless openings) -> NOT COMPARABLE, verdict proposals unchanged.

## 2. The physical element (standard s.2 step 1) and what each addition is

- **P-GF-01** (engine GF OP-020): a doorway with no leaf in a 0.20 black block wall, column / masonry jambs, two head lines
  on the plan, an S1 beam band over the whole width (S8.6 OP-GF-020). Floor +1.00 both sides (LEVEL mark in the hall;
  the basin space prints none of its own). Head: no sheet prints it; S8.6 cannot tell head-at-beam-soffit (no lintel)
  from a lintel below the beam (Q-HEAD-UNDER-BEAM).
- **P-1F-01** (engine 1F OP-009 = S8.6 OP-1F-021 = T-128's "1.29 m doorless opening", the mouth strip at the same plan
  point): a doorway with no leaf in a 0.15 black block wall, head lines drawn, a schedule lintel L2 150 x 200 under no
  structural member (released). Physically built above it: lintel + masonry up to the slab soffit (T-143: 4.04 above
  the +5.50 floor). The hand runs 1F-W14 / 1F-W15 stop at its jambs (L1 = L2b), so that masonry is in no run, and T-128
  joins both sides into one room, so the two faces above the head are in no room face.
- **P-GF-05** (engine GF OP-007 = S8.6 OP-GF-012): the passage mouth between two column jambs, no leaf, no glazing; the
  plan draws NO head line, the SW elevation (re-read this run on Pages_07-08 p.7, rotated, 300 dpi) draws two vertical
  lines with a horizontal head line across and a face above it up to the top band; S8.6 puts an S1 beam (400) over the
  whole opening. Both sides outdoors at +0.15 (LEVEL marks 1.9 m outside in the court, 3.5 m inside in the passage).
  Kind = passage: not a window (no glazing on any sheet), so the windows count does not change.
- Open sides P-GF-02 / 03 / 04 stay out of the census (T-175, T-194: not building openings).

## 3. Own reads this run (acceptance), Drive "Alsenan chalet project", read-only

1. **W01 on the SE elevation** (P7757.dxf, from P7757_DXF_COMPRESSED.zip): the level-marker block A$C4EB10A95 with the
   text "+0.15" is the chain base; the frame's "+0.30" / "+4.30" markers are 4000 units apart (1 unit = 1 mm) and
   DIMENSION 245B 1000.0 runs +-0.00 -> +1.00. Chain DIMENSION 2A72 1850.0 (+0.15 -> +2.00) and 2A80 2000.0 (+2.00 ->
   +4.00), printed 185 / 200 (Pages_05-06 p.6). Floor: the plan's "+1.00" LEVEL mark lies inside W01's wall, "+0.15"
   outside. So sill 1.00 / head 3.00 above the hall floor; level and chain agree to 0 mm (`redatum` checks both).
   Note: W01 stands beside the stair flights, so the floor under it is not one level; band / soffit checks must read the
   absolute +2.00 / +4.00 (now in the census).
2. **W03 on the NW elevation**: DIMENSION 29EE 1000.0 (+-0.00 -> +1.00, marker "+1.00"), 2E5E 1150.0, 2E6C 700.0, 2E7A
   4300.0 (+1.00 -> +5.30), 2E88 200.0 (-> +5.50 = 1F FFL): sill 0.00 / head 4.30 above the +1.00 floor.
3. **P-GF-05 on the SW elevation** (Pages_07-08 p.7): bound by T-194 at facade position 22.95; at the print scale the
   opening is about 1.2 m wide and its head line about 2.5 m above the drawn ground line; these scaled values are
   identity only (note N09 "not to scale"), never a quantity. AGREES on existence and kind with the plan; DIFFERS on the
   head (plan none). Plan context also re-drawn from the DXF (engine record head_lines 0, both jambs column).
4. Plan check of the whole opening list: the 60 engine openings of an ARCH_TAKEOFF_V2.12 run (scratchpad) all bind to a
   census row or a T-175 open side; the GF wash-lobby niche (1.9 m gap, T-128 fix b) carries no head line and lies
   inside one space: not an opening.

## 4. Reconciliation (standard s.2 step 4)

- Freelancer: no row for any of the three leafless openings; his block deductions (122.39 m2) contain no passage
  deduction; nothing to reconcile in units here beyond T-175 s.5 (unchanged).
- Merged ledgers: T-175 already carried P-GF-01 / P-1F-01 / P-GF-05 and the W01 / W03 sill corrections; T-128 already
  carried P-GF-01 and the corrected W01 / W03 bands; S8.6 already carried all three for the lintel line. What the census
  omission DID hide is scope above and around the openings that no ledger owns: P-1F-01's masonry and faces above the
  head, three head soffits (0.615 m2 together), P-GF-05's Sigma reveal. And one T-175 line counts an edge that is not
  established: the P-GF-05 threshold (1.20 m.l). The same question applies to the open sides P-GF-02 / 03 / 04 (13.62
  m.l in T-175's 42.22 thresholds): flagged for the T-175 owner, not re-derived here.

## 5. General rule (proposed, any villa; provenance: standard s.3 + Q-73 + UP-OPEN-CONSIST-001 proposal; new, not a project fact)

A census omission is corrected in a new census version, and every consequence of the added opening is traced in its own
unit before anything is released: masonry deduction only inside a measured run of built masonry; for an opening OUTSIDE
the run, the masonry above its head (lintel underside to the member soffit) and the finish faces above the head are a
scope item of the run / room ledgers (never netted, never 0, bounded while the head is held); the head soffit (width x
wall thickness) exists wherever a member spans the opening, independent of the head level; a threshold exists only where
a door or a floor change makes one; a list sill / head carries its datum (absolute level + FFL), and a value that cannot
be bound to a sheet's marker or chain base is refused. Proposed to the Lead as UP-OPEN-CENSUS-001 v1.0.0 (new file).

## 6. Tests

`tests/t198_census_r3/test_census_r3.py` (non-Alsenan villa T198-B, hand truth in the docstring: 18.000 m2 wall, the
omitted 1.20 x 2.40 opening -> net 16.200 -> 13.320, -2.880 m2 / -0.576 m3, lintel 1.600 m, reveal 6.000 m.l, soffit
0.240 m2; adverse: head not printed -> HELD with bounds 12.600 .. 16.200, elevation-only feature not measured, list level
on a raw chain part re-datumed only with its chain base, level vs chain conflict refused, millimetres refused, head above
the soffit refused, outside-the-run opening not deducted but its masonry above the lintel a scope gap 0.780 m2, glazed
line / open side build-before-deduct, census revision never edits the old rows, duplicate / unknown ids refused) and
`test_alsenan_ledger.py` (byte-for-byte reproduction, r2 untouched, 68 rows, W01 / W03 values, windows pcs HELD, no
released quantity moves, held never 0, P-1F-01 lintel length reproduces S8.6).

## 7. Lessons-register row (proposed, s.7)

2026-10-23 | A doorless opening missing from the census (P-1F-01) hid the masonry and the plaster faces above its head:
the block runs stopped at its jambs and the plaster walk joined both rooms through it, so no ledger owned what is built
above it | consequences traced from the ledgers that knew the opening (deductions) but not from the physical element
(what spans it and what is built above) | for every opening, list what is physically built above and around it and the
ledger that owns each piece before netting anything; an opening outside a run makes the masonry above it a scope item
(any villa) | t198 `test_outside_run_not_deducted_but_masonry_above_is_a_scope_gap` (normal: inside-run opening has no
such line; adverse: outside-run opening, held head -> bounds) | READY (T-198), Checker to verify.

## 8. Held / unknown / missing (never 0)

Heads of P-GF-01, P-1F-01, P-GF-05 (designer list, D-45 family; S8.6 Q-HEAD-UNDER-BEAM for P-GF-01 / P-GF-05); P-GF-05
face above the head and its material; who owns the three head soffits (T-128 has no soffit line; Sigma for P-GF-05);
whether T-162's column arrises already include P-GF-05's jambs; the 9 elevation-only squares; the threshold classification
of the open sides P-GF-02 / 03 / 04 (T-175 owner).
