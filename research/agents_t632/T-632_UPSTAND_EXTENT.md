# T-632 Beam upstand extent census (Checker F-C-P02-12)

Worker 1 (lane S, non-candidate, evidence row), 2026-11-08, run session_01E6cPneM28THu86UD2qEeSX, branch
`agents/task-T-632`. Research only: no engine module, candidate line, released line, rule register, method version or
frozen file changed; nothing released. Development villa, not an accuracy claim. ERS s.2 - 4, s.7; UP-CONC-JOINT-001
1.0.0; R-T614-1 (g); R-T632-1 .. 3 (new, proposed).

## 0. Sources and run

- Drawing (own read this run): Drive 'Alsenan chalet project' / 'ST7757 dxf.dxf' (sha256 9f9d1179, `.work/private`
  only; the only structural issue on Drive, so no later-dated issue competes). Every length is read from raw entities by
  hex handle: hatch boundaries on S-HAT.BAT, LINEs on layer '2' (linetype HIDDEN), section cut lines (S-SEC.LINE,
  CENTER) and their arrows (tip = zero start width), section outlines on layer '1', DIMENSION block texts. Route G is a
  locator only (band polygons, faces, marks, schedule depth, sheet frames, slab-engine face class).
- Code: `t632_rules.py` (R-T632-1 .. 3), `t632_alsenan.py` -> `out/T632_UPSTAND_CENSUS.json`; tests `tests/t632` (26).

```
.work/venv/bin/python -I research/agents_t632/t632_alsenan.py .work/private/ST7757.dxf --check
```

## 1. B20 settled (GF): 3.000 m, ENGINE_RIGHT, 0.120 m3; the +0.053 m3 reading is refused

Physical element: concrete 0.20 x 0.20 above the slab top on the north half of the 0.40 x 0.75 B20 band (the band stays
with B10-07 beams, UP-CONC-JOINT-001).

| Evidence | Handle | What it says |
|---|---|---|
| Section A-A outline | 560 (title 1727) | printed 40 base, 20 + 20 top, 75 + 20 high (dims 561 / 572 / 58C / 59A / 5A8, 40 units per cm): upstand 0.20 x 0.20 on the section's RIGHT |
| Cut line + arrows | 55A, arrows 553 / 55C | cut 2.051 m from the band's west end; arrow tips point west -> looking west, RIGHT = north (+n) |
| Level-change hatch on the band | 2B4 (ANSI31, S-HAT.BAT) | covers the band exactly, 3.000 m: west end at face 2B5 (band end), east end at column 368's west face |
| Upstand edge, hidden (above-slab) | 55F (layer 2 HIDDEN) | 3.000 m, same two ends, 0.200 m from each band face: bounds the north 0.20 = the section's upstand |
| Band piece the cut crosses | BAND0043.1 (faces 458 / 2C6) | 3.000 m: equal to the drawn extent, so the engine's section-mark span gives the right number here |

East of column 368 (BAND0043.2, 3.300 m) no hatch and no upstand edge is drawn; the two hidden lines in it (459, 45A)
belong to the stair tread series (pitch 0.30, one extent each: 459 / 270 / 264 / 265 / 266 and 45A / 271 / 26C ...),
excluded by rule. Result: B20 upstand 0.20 x 0.20 x 3.000 = **0.120 m3 = engine 0.120 m3 (delta 0)**, ENGINE_RIGHT.

The 0.20 strip north of B20 (faces 2C6 / 2C7, 4.325 m, BAND0031) is **not the upstand** (R-T632-2): its faces are
CONTINUOUS (layer 1, the soffit / edge convention; the above-slab convention on this sheet is HIDDEN), it carries no
hatch, section A-A cuts straight across it and prints only the 0.40 beam (no part north of the beam face), and it is a
piece of the plan outline that turns the NW corner with arc 316 (r 0.231) down to 2B7 (0.20 outside the west beam) and
runs north at 30F along the stair: a slab-edge outline 0.20 beyond the beam faces. The 1F twin (BAND0013, faces
5E1 / 5E6, arc 647) reads the same. So F-C-P02-12's +0.053 m3 (strip as upstand) is refused: class ENGINE_RIGHT on B20.

What the strip leaves open (not this task's quantity, named): the strip is billed by NO line on either storey (slab
engine face class BEAM / BEAM_STRIP, beam binder UNBOUND): plan 0.865 m2 per storey (GF and 1F), thickness not printed
for it: HELD, never 0. Proposed fix row for the slab line (lane S): slab-edge projection beyond edge beams.

## 2. 1F B23: same method, 3.000 m, ENGINE_RIGHT 0.120 m3

Hatch 5E0 and hidden edge 7BC both 3.000 m (west band end to column west face); 7BC lies 0.250 from the south face and
0.200 from the north face; section B-B (16BF: 45 base, 25 + 20, 95 high) cut 76E 1.698 m from the west end, view west
-> upstand on the north 0.20. 0.20 x 0.20 x 3.000 = 0.120 m3 = engine; section-mark span = drawn extent.

## 3. Census: every upstand / level-change strip drawn on a beam band (GF / 1F / 2F; ground-beam plan noted)

| Storey | Mark (band) | Drawn (handle) | Section | Billed | Class |
|---|---|---|---|---|---|
| GF | B20 (0043.1) | 3.000 hatch 2B4 + edge 55F | A-A 20 x 20 | 3.000 / 0.120 m3 | ENGINE_RIGHT |
| 1F | B23 (0031.1) | 3.000 hatch 5E0 + edge 7BC | B-B 20 x 20 | 3.000 / 0.120 m3 | ENGINE_RIGHT |
| GF | B24 (0046.2) | 1.500 hatch 273 (whole piece) | cut 181D is D-D, base 0.348 not the 0.50 band: not this band | none | HELD |
| GF | B4 (0030.2) | 0.500 hatch 2B1 (whole piece) | none | none | HELD |
| GF | CA (0038) | 1.150 hatch 54D (whole piece) | none | none | HELD |
| 2F | B8 (0001.3) | 1.130 hatch 38C (whole piece) | none | none | HELD |
| 2F | B15 (0006.1) | 3.100 hatch 390 (whole piece) | none | none | HELD (already D-44, upstand or downstand) |
| 2F | B7 (0009) | 1.782 hatch 391 (part of a 6.600 band, from its start) | none | none | HELD |
| GF | CB1 (0041.2) | no hatch, no edge | C-C / D-D: 0.348 x 0.75, rounded top corners, no part above D | n/a | NO_UPSTAND_EVIDENCE |
| GF / 1F | strip 0031 / 0013, B6 | none | crossed by A-A / B-B, not printed (other band) | n/a | NO_UPSTAND_EVIDENCE |
| GROUND | 4 bands | hidden lines 146 / 156 / 16D / 179 / 1AE | none | n/a | OUT_OF_SCOPE (ground-beam plan) |

The six HELD rows: the sheet's level-change hatch lies on the band (100 % inside it), but no printed section through
those bands shows the cross-section, so whether it is an upstand or a dropped band and its height are not printed:
drawn length only, **no volume, never 0**, billed by no line today (5 new + B15 on D-44). Total drawn length held:
9.162 m (GF 3.150, 2F 6.012). These are designer items for the RFI list, not owner questions (ERS s.2.7 not met).

Observation (not this task's quantity): CB1's printed sections C-C / D-D are 0.348 x 0.75 with rounded top corners,
area 0.24476 / 0.25229 m2 vs 0.261 m2 for b x D: a profile deduction of 0.0087 .. 0.0162 m2/m whose extent along CB1
is again a drawn-extent question (proposed follow-up row).

## 4. Verdict proposals

B20 ENGINE_RIGHT (0.120 = 0.120 m3; F-C-P02-12's +0.053 refused: the strip is the slab-edge outline, not the upstand);
B23 ENGINE_RIGHT; six hatched bands HELD (length only, no section); the strip 2 x 0.865 m2 billed by no line (HELD,
slab-line follow-up). No ENGINE_WRONG. No owner question.

## 5. Rules, tests, lessons row (proposed)

R-T632-1 (drawn extent governs; section-mark span accepted only when equal; conflict -> range; section only -> HELD
range), R-T632-2 (strip identity before arithmetic), R-T632-3 (section read, view direction to plan side; rounded
profile is not an upstand). Engine note: `engine/source/beam_binding_v2.py:487 upstand_lines` bills the band piece the
cut crosses; it equals the drawn extent on B20 / B23, but a future villa whose upstand stops inside a piece (2F B7
pattern) would be over-billed: proposal for a later method version, not changed here.
`tests/t632` (26): hand villa V632 (0.30 x 0.60 band, 0.15 x 0.25 upstand over 2.40 of a 5.00 piece -> 0.090 m3; the
section-mark span 0.1875 refused), mirror / rotation (5), view-direction side, tread series, strip identity, rounded
profile; adverse (strip runs further than the section-mark span, disagreeing evidence -> range, cut outside extent,
section only -> HELD never 0, missing section, mm outline, bad evidence); development villa from the committed census;
private rebuild equals committed.

Lessons row (ERS s.7): | 2026-11-08 | B20 upstand read as 4.325 m (+0.053 m3) from a 0.20 strip beside the band | a
strip's identity was taken from its position beside the band, not from its line convention, the hatch and the section
that cuts across it | an upstand's extent is the drawn upstand evidence (hatch on the band, above-slab edge line),
checked against every section crossing it; a strip outside the band faces is an upstand only if drawn as one and
printed on a crossing section (every villa; provenance T-632, R-T632-1 / -2) | tests/t632 | PROPOSED |

## 6. Checker re-measure list

B20: hatch 2B4, hidden 55F, section 560 dims, arrows 553 / 55C, strip faces 2C6 / 2C7 layer and arc 316; largest
other drawn length: 2F B15 hatch 390 (3.100) and 2F B7 hatch 391 (1.782 of 6.600).
