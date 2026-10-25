# T-293 Formwork face-to-member ledger, part 1: foundations, ground beams, columns (lane S; Alsenan; every villa)

Worker 1, 2026-10-25 10:25 .. UTC, run session_01N8jsp5pQjoXTiFTHVcu8UM, branch `agents/task-T-293`. Research ledger:
nothing wired, no candidate or released line changed, no method version, no quantity released. Integration dependency of
T-199 (formwork is a BOQ category the candidate lacks). Development villa, not an accuracy claim. ERS s.2.1 - 2.6, s.3,
s.4 applied.

## 0. Run, identity, sources

Own run, Python 3.11.17, Drive copies "Alsenan chalet project" / 'ST7757 dxf.dxf' (`9f9d1179`) and P7757.dxf from
P7757_DXF_COMPRESSED.zip (`ab54dd55`): `research/agents_t167/v304_run.py` then `research/agents_t245/v3016_run.py`
(ARCH_TAKEOFF_V3.0.16, 3,699 lines; lines csv `a4dc01dd` = the T-270 / T-289 csv, json `3181cf12`; project identity
`development-villa-t131` / revision set `5e369075`, structural route `297e913d`). Extract:
`python3 -I research/agents_t293/t293_extract.py <run>/v3016 <ST7757 dxf.dxf> --out research/agents_t293`; ledger:
`python3 -I research/agents_t293/t293_alsenan.py --write` (committed outputs = a fresh build, tested).

Face source (each row names the REVISION it reads): formwork r4 `FORMWORK_LINES_R4.csv` (T-264 MERGED 90203feb, 361
rows; its totals re-computed from the csv: G CALCULATED 1,015.963, below N.G. CALCULATED 47.663, OQ-10 FORMED 209.112,
EARTH_CAST 0.000 m2, = summary_r4) + the 21 changing rows of the ground-beam edge fixes r3
`DELTA_T282_GROUND_BEAM_SIDES.csv` (T-282 MERGED aa3a7bb4; the 106 AGREES rows change nothing). Bindings: T-289 band
pairing and basis ledger (MERGED 455c93c4), T-248 column register, T-220 planted-column records (MERGED 579e613d),
T-253 boundary runs (MERGED c2d5b3cd).

## 1. Physical element and the question (ERS s.2.1)

A formed face is a concrete surface cast against a form; it bounds ONE member, and the candidate line that owns that
member's concrete is the line its formwork is reported beside (one element, several geometries). Question: for every
formed face in the merged formwork ledgers, which candidate concrete line id owns it, on which depth / height, with
which status. Earth faces stay apart: below N.G. the OQ-10 pair (FORMED / EARTH_CAST) is carried as two alternatives,
never summed, never chosen; a face above the outer N.G. (exterior ground beams, p.13 soffit at 'Outer Normal ground
level') has nothing to be cast against (R-FW-GB-EXPOSED-1, r4). Ground-beam soffits and footing bases sit on blinding:
no form (no row). Buried faces for waterproofing are the WP ledger's (T-276), a different trade: no double count.

## 2. Result: every face once, residual 0.000 m2 (382 source rows -> 412 face records)

| Element (part 1) | Faces tied | Candidate lines | Tied m2 by status (never summed across) |
|---|---|---|---|
| Ground beams | 155 | 56 STR.CONC.GROUND_BEAM (bands) | CALCULATED (above N.G.) **47.948** (r4 47.663 + T-282 170+7C3#4 B +0.285); OQ-10 FORMED **74.360**, EARTH_CAST 0.000; HELD FORMED 65.762 .. 78.485; HELD EARTH_CAST 0 .. 17.475; 13 annex CONFLICT rows m only |
| Footings | 59 | 26 STR.CONC.FOOTING (one per footing) | OQ-10 FORMED **90.047** (r4 type rows split per footing + covers + notch); EARTH_CAST 0.000; HELD 4.300 .. 5.010 (1B1B F10 + F CONFLICT line) |
| Columns (incl. 3 planted) | 59 | 59 STR.CONC.COLUMN | CALCULATED **117.461**; HELD 219.571 .. 249.781 (section CONFLICT, D-39 roof datum, annex datum) |
| Straps SB1 / SB2 / SB3 | 9 | 3 HL:STRAP_CONCRETE:SBn:CONCRETE | OQ-10 FORMED **9.449** (axis length, Q-74); soffits HELD 0 .. 7.107 |
| Boundary M1 foundation strip | 1 | STR.CONC.BOUNDARY_WALL | HELD 56.392 .. 110.328 (Q-28 provisional) |
| Pool walls / floor edges | 2 | HL:POOL_CONCRETE:POOL-1 WALLS / BASE | HELD unquantified (r4: no merged wall ledger at r4 time) |

Closure (R-FW-LINE-6, `summary_t293.json` `closure`): per (r4 / T-282 status, alternative, method) the tied + untied
records reproduce the source m2, low and high to 0.000000; a source row split per member counts once.

**Splits (each from the row's own printed basis, never a guess):** footing type rows 'X xN' -> N footings of that
schedule size, 1 / N each (e.g. F x4 sides 4.080 -> 4 x 1.020 on the four F lines); the FN 180C / F9 notch -0.450 ->
FN -0.225 + F9 -0.225 (the r4 basis prints both); the boundary G.B 35.256 -> 5 runs 2 x L x 0.40 (T-253 lengths 1.15 /
31.37 / 8.10 / 2.25 / 1.20 = 44.07 m); the pool row -> wall faces / floor edges.

**Binding evidence:** ground-beam run -> band by T-289's pairing (58 runs); the three 45-degree bands T-289's X / Y test
skipped are paired here by band centroid vs the run's face-line midpoints: BAND0037.1 -> 17E+17F#1 (3.9 mm; next
1,339.8 mm), BAND0038 -> 180+181#1 (25.5 mm), BAND0039 -> 182+183#1 (17.2 mm). Columns: formwork id = T-248
owner_t119_id -> engine column id after one frame translation (dx 75,968 / dy 14,448 mm, 32 votes, every bind <= 2 mm,
one line each); planted COL-1F-57 / -58 / COL-2F-59 -> PC-1F-A / PC-1F-B / PC-2F (T-220 rows 18 - 20). Footings named by
handle (covers, notch) -> the footing line whose element-id position is the outline's lower-left corner + the same
frame translation (166B F3, 1B2A F15, 1B07 F11, 1B19 F6, 1B24 F8, 180C FN: mark agrees on all six); 1B1B -> the CONFLICT
line whose notes name 'outline 1B1B carries tags F+F10'. Lines in state NOT_APPLICABLE_WITH_EVIDENCE (superseded or
undrawn) own no face.

## 3. Findings (engineering, for lane I and the Checker)

1. **Missing concrete line, boundary ground beam at N.G.** The 5 boundary runs 20 x 40 (T-253 DRAWING-CONFIRMED,
   44.07 m, 3.5256 m3) have NO candidate concrete line; their formed faces 35.256 m2 (OQ-10 FORMED alternative; EARTH_CAST
   0) and the 810#1 end face (HELD 0 .. 0.08) are listed NO_CANDIDATE_LINE. The only boundary line is the foundation strip
   M1 (STR.CONC.BOUNDARY_WALL 7.2204 m3), another member. A missing concrete scope, not a formwork question.
2. **Cross-trade basis conflict on 3 ground-beam lines.** BAND0006.2 / BAND0005.1 / BAND0043 (main-house exterior runs
   109+7CB#2, 145+7CA#1, ring ARC:157+158 the candidate typed interior; T-289 group GB_MAIN_EXTERIOR_IN_INTERIOR_LINES)
   carry concrete at the interior class depth while their formwork faces rest on the printed D 0.95: 6.239 CALCULATED +
   17.934 OQ-10 FORMED. Both readings travel with each face (`concrete_basis_t289`); lane I must re-base the concrete
   (T-254) before these faces and their line are shown together. Same for the 13 GB_EXTERIOR_24 lines (41.709 CALCULATED
   + 41.304 FORMED on D 0.95, concrete still at 0.30 / 0.40 in the candidate).
3. **One drawn member in two candidate lines.** Annex arc ARC:139+13A lies in BAND0013.1 (0.009 m3 sliver) and BAND0042;
   no length per line is printed: SPLIT_UNRESOLVED, HELD by name (its faces are annex CONFLICT, no value anyway).
4. **No formwork line exists in V3.0.16** (census: 0 lines of any formwork trade or item code): T-199 adds the family;
   `T199_FORMWORK_BY_LINE_T293.json` is its input (per concrete line: faces, status, alternative, method, totals per
   status|alternative|method; untied rows by reason; scenario S1 never a candidate face).
5. **Members with no concrete line, kept:** lift-pit walls (HELD, no pit-wall concrete line), boundary pads (count not
   printed), the 35 necks (one HELD unquantified r4 row of 35 members: per-neck rows need the founding level, Q-21 C),
   F7 (scheduled, not drawn).

**T-289 basis (acceptance 2):** applied only because T-289 is MERGED (455c93c4): the main-house exterior faces on D 0.95
are DEPTH_PRINTED; annex CONFLICT and court HELD stay HELD; interior runs on the p.13 class depth (D-33 / D-34 named).
**T-290 readings (acceptance, Lead 10:15):** T-290 is READY, not merged: 'MS2-LD landing soffit' 3.000 and 'RS-A riser
forms' 1.004 are PENDING-VERIFICATION, blank (source value kept); 'E1 waist soffit' NOT_APPLICABLE vs concrete HELD G2-w
stays CONFLICT (named). They are part-2 rows.

## 4. Part 2 (named, not tied in this run; every row listed with its quantity)

Slab-level rows (GF / 1F / 2F slab soffits, beam soffits and sides by method E and G, slab-edge bands, column joints,
upstands, held-edge pieces: 40 CALCULATED rows 1,319.708 m2 across methods E and G, never summed; 52 HELD rows 50.465 ..
98.762), stairs, domes and the tank are per-slab-level aggregates of the T-139 face walk: each must be split per member
(T-139 faces carry the member id) before it can be tied to the 191 STR.CONC.BEAM / 75 STR.CONC.SLAB / stair / dome
lines. Scenario S1 (7 rows, 8.783) is never a candidate face. Size rule of the row: ground beams and columns handed in,
slabs / stairs named.

## 5. Verdict proposals

- Bindings: ENGINE_RIGHT on plan identity (every band / column / footing found once, frame translation one value);
  ENGINE_WRONG basis on the 16 main-house exterior ground-beam lines (concrete depth; T-289) - formwork already on the
  drawn D 0.95.
- Boundary G.B at N.G.: ENGINE_WRONG (scope omitted: a drawn, DRAWING-CONFIRMED member with no concrete line).
- Freelancer: no formwork row in any workbook (r3 / r4): FREELANCER_NO_ROW, no %. Owner manual method: none on record
  for formwork; the two drawing-derived methods E (element faces) and G (drawing faces) stay side by side.

## 6. Rule, tests, lesson

Rules R-FW-LINE-1 .. -6 (`face_line_ledger.py`, research scope, any villa; provenance T-293 on T-163 / T-264 / T-282 /
T-289): one face once on one line; a face booked to two members refused; a member in no line or in two lines listed,
never dropped, divided or zeroed; an earth face booked FORMED refused (OQ-10 alternatives excepted); an unprinted depth
-> HELD blank, an unmerged basis -> PENDING blank; closure per status / alternative / method to 0.000.
Tests `tests/t293_formwork_face_line`: villa V293 by hand (NORMAL: beam side to its own line 1.600, tee cover -0.120 on
the CARRIER's line, exterior face on a verified depth 4.750, column 3.600, footing 2.400; ADVERSE: unprinted depth ->
HELD blank, face booked to two members refused, earth face as FORMED refused, duplicate / HELD-with-number / reversed
range / m3 refused, member in no line or two lines listed, unmerged basis PENDING, dropped or altered row fails the
closure, mirror + reorder invariant) and Alsenan pinned (source = r4, identity, closure, per-element ties, oblique bands,
footing splits / handles, planted columns, named gaps, T-290 pending, committed outputs = fresh build).

Lessons row (proposed, ERS s.7): 2026-10-25 | Formwork r4 rows are keyed by run / type / slab level, the candidate by
band / footing / column position; 3 oblique bands, 3 planted columns and the boundary ground beam fell outside a
key-by-key match, and one row ('F x4', 'boundary 5 runs', the notch) holds several members | A derived trade was built
on its own member ids and never bound to the concrete lines that will carry it | Before a derived-trade family enters a
candidate, bind every face to one concrete line id with a closure per status; split only by the row's own printed
basis; a member with no line is a scope finding, not a dropped face (PROJECT-INDEPENDENT) | tests/t293_formwork_face_line
(villa V293 + Alsenan) | OPEN (T-293 READY).

## 7. Checker re-measure

(a) one oblique band: BAND0037.1 centroid vs LINES 17E / 17F midpoints on 'ST7757 dxf.dxf' (3.9 mm) and its line
`T199_FORMWORK_BY_LINE_T293.json` (17E+17F#1 faces HELD 0.30 / 0.40 + the T-282 +0.260 / +0.340 m rows);
(b) one footing handle: 1B07 lower-left corner + (75,968, 14,448) = candidate F11@209785,50796 and its line
L-5d3e72daa69dc769ca5e (sides 2 (3.50 + 1.50) 0.50 = 5.000 FORMED alternative less the SB2 cover -0.5095);
(c) one exterior run: 7D0+FC#3 outer face 6.35 x 0.95 = 6.0325 CALCULATED on L-e9a885323ad6ec3ea32b (BAND0011.3,
T-289 Checker line); (d) the boundary: no STR.CONC line names S-BOUN 7FE / 7FC / 810 in the candidate.
