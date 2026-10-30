# T-373 Binding of F-T366-2: every candidate rebar line that books a lap, development or starter length, bound to its printed authority (development villa; rule for every villa)

Worker 1 (structural lane S), 2026-10-30, run session_01E6cPnex4Xa1iQnnwAPUore, branch `agents/task-T-373`. A binding,
not a takeoff: **no length computed, no candidate line, rule, method or released quantity changed**. It is the input the
Checker needs to issue a DOWNGRADE-ONLY record (owner 2026-10-24 23:57: a record only moves a line to HELD / CONFLICT,
never promotes it, and the candidate's figures stay in the audit trail). Drawings are named by Drive folder and title only.

## 0. Inputs

- Candidate lines: the merged T-297 extract `research/agents_t297/CANDIDATE_V3016_REBAR_LINES.json` (ARCH_TAKEOFF_V3.0.16
  = V3.0.17 line by line, 2,505 reinforcement lines, sha256 in `T373_SUMMARY.json`), re-booked to its **V3.0.27 state**
  with the merged T-318 inputs (`research/agents_t318/t318_inputs.py`, by line id; `rebook_t318` refuses a T-318 'before'
  figure that differs from the bound line, so the 98 slab development lines are proven unchanged from V3.0.16 to V3.0.26).
- Population binding: T-366 `bind()` (merged 51be6eab), unchanged. Authorities: the T-366 census (ST p.8 note 9;
  ST p.13 TYP. DETAIL OF ISOLATED FOOTING '40 ø'; ST p.15 NOTE 1; ST p.15 TYP. SLAB ON BEAMS DETAIL drawn straight
  part, T-307 / T-318). Drive 'Alsenan chalet project': 'ST7757 dxf.dxf' (sha256 9f9d1179..) and
  'P7757_DXF_COMPRESSED.zip' (P7757.dxf ab54dd55..) decoded into the private folder for the reproduction run (s.6).
- Files: `t373_lap_binding.py` (LAP_AUTHORITY_LINE_BINDING_V1, stdlib), outputs `T373_LAP_BINDING.csv` (one row per
  line, acceptance (a)) and `T373_SUMMARY.json` (totals, (b)). Tests `tests/t373_lap_binding` (8). Repeat:
  `python -I research/agents_t373/t373_lap_binding.py research/agents_t297/CANDIDATE_V3016_REBAR_LINES.json --t318
  --csv research/agents_t373/T373_LAP_BINDING.csv --json research/agents_t373/T373_SUMMARY.json`.

## 1. Physical element and method (ERS s.2.1, s.2.3)

A lap is the overlap of two bars of ONE bar group (procurement length, never net); a development / anchorage length is
the extension of a bar past a section into a support; a starter is the column bar left projecting from the footing.
Each is a length whose authority must name the bar group. Only three printed sources exist (T-366): p.8 note 9 (names
STARTER bars: >= 70 d tension / >= 40 d compression, zone not printed), p.13 '40 ø' (starter projection, conflicts with
note 9: F-T366-1), p.15 NOTE 1 (temperature bars 40 x DIA). Owner manual method vs drawing-derived method: the owner's
40 d / 60 d convention is a proposal under assessment (OWNER_RULE_REBAR_2026-10-24 s.2), never applied; owner
2026-10-29 option B: only what the structural drawings write or draw is calculated. Drawing-derived reading: a line
whose figure rests on note 9 but whose bar is not a starter has **no printed authority** and is HELD by name, BLANK.

What counts as "the line's figure rests on": the line's formula, its bound basis, its component and element id; the
notes field is history and is not read (a re-booked T-318 line still mentions note 9 in its notes, refused as basis).
A line with no figure (BLOCKED_RFI / NA) is NOT_BOOKED: nothing to downgrade.

## 2. Result per population (acceptance (a), (b); every row in the CSV)

584 rows: 351 NOTE9_OUTSIDE_GROUP -> **HELD**, 54 NOT_BOOKED, 98 + 59 slab development rows re-booked by T-318
(KEEP, not downgraded twice), 22 pool / stair / tank rows LISTED (T-359 scope).

| Population (T-366 id) | Component / length used now | Authority | Lines | Valued kg now (low .. high) | Proposed | kg after |
|---|---|---|---|---|---|---|
| Simple beams B1 - B29, CA, B.W (BEAM-SIMPLE-MAIN) | bottom / top ends, 40 d .. 70 d per end | NOTE9_OUTSIDE_GROUP | 196 | 1,534.342 .. 2,728.284 | HELD by name | BLANK |
| Continuous-beam bottom (CB-BOTTOM) | bottom ends 40 d .. 70 d | NOTE9_OUTSIDE_GROUP | 29 | 239.868 .. 419.769 | HELD | BLANK |
| Continuous-beam top corner (CB-TOP-THROUGH) | top corner ends 40 d .. 70 d | NOTE9_OUTSIDE_GROUP | 28 | 55.924 .. 97.862 | HELD | BLANK |
| Continuous-beam support top (CB-SUPPORT-TOP) | over-support ends 40 d .. 70 d | NOTE9_OUTSIDE_GROUP | 1 | 7.200 .. 12.600 | HELD | BLANK |
| **Beam ends, subtotal** | | | **254** | **1,837.334 .. 3,258.515** | | |
| Column main bars (COL-MAIN) | LAP at storey bottom 40 d .. 70 d | NOTE9_OUTSIDE_GROUP | 56 | 499.614 .. 874.320 | HELD | BLANK |
| Ground-beam main (GB-MAIN) | BAR ENDS development 40 d .. 70 d | NOTE9_OUTSIDE_GROUP | 36 | 492.588 .. 925.122 | HELD | BLANK |
| Strap beams SB1 - SB3 (STRAP-MAIN) | BAR ENDS development 40 d .. 70 d | NOTE9_OUTSIDE_GROUP | 3 | 153.940 .. 269.395 | HELD | BLANK |
| Ground-beam main, BAR ENDS lines with no figure | (BLOCKED_RFI) | NOT_BOOKED | 23 | blank | KEEP (already blank) | blank |
| Ground-beam procurement laps (GB-MAIN, runs 7D0 / FC, 170 / 7C3) | 1 lap per bar, 40 d .. 70 d | NOTE9_OUTSIDE_GROUP | 2 | 18.204 .. 31.858 | HELD | BLANK |
| Slab development (SLAB-BOTTOM-MAIN), T-318 re-booked | none (note 9 dropped) | REBOOKED_T318 (8 NA, 31 + 59 BLANK) | 98 | blank | KEEP | blank |
| Slab development drawn straight part (T-318 part lines) | p.15 w - 0.040 m, drawn | PRINTED (p.15 drawn bar part, not a lap) | 59 | 136.573 .. 150.695 | KEEP | 136.573 .. 150.695 |
| Neck starters ø16 (NECK-STARTER-*) | neck height + lap | PRINTED (note 9 + p.13 40 ø, F-T366-1 CONFLICT) | 28 | blank (BLOCKED_RFI) | KEEP (no figure) | blank |
| Slab temperature bars | 40 x DIA | PRINTED (p.15 NOTE 1); group blocked (no 160 mm row) | 3 | blank | KEEP | blank |
| Pool / stair / tank (T-359 scope) | 2 x 40 d .. 2 x 70 d | NOTE9_OUTSIDE_GROUP | 22 | 373.390 .. 718.480 | LISTED only (finding F-T373-2) | unchanged here |

**Totals for the downgrade record (released route): 351 lines, valued (BOUNDED_EXPOSURE) kg 3,001.680 .. 5,359.210 ->
BLANK by name.** None of them is RELEASED: the released STR.REBAR 10,250.167987 kg (V3.0.27, T-318) is unchanged. The
candidate's bounded STR.REBAR range 15,250.786488 .. 21,621.544938 kg (V3.0.27) becomes **12,249.106488 ..
16,262.334938 kg** plus 351 more BLANK lines (-19.7 % .. -24.8 % of the bounded range, all of it unsupported basis, not
a measured reduction of steel: the beams, columns and ground beams still need SOME end / lap length, which stays HELD
until an authority is printed or answered). By floor: GF 166 (136 beam + 30 column), 1F 98, 2F 46, FOUNDATION 41.

## 3. Reconciliation to T-366's 470 (acceptance (b))

| T-366 group (V3.0.16) | T-366 count | This binding (V3.0.27 view) | Difference, named |
|---|---|---|---|
| beam ends | 254 | 254 HELD | 0 |
| column storey laps | 56 | 56 HELD | 0 |
| GB bar ends (incl. SB1 - SB3) | 62 | 39 HELD + 23 NOT_BOOKED | the 23 are BLOCKED_RFI lines with no figure: nothing to downgrade |
| slab development | 98 | 0 HELD; 8 NA + 90 BLANK (T-318) + 59 drawn parts KEEP | all 98 re-booked by T-318 (V3.0.27); downgrading them again would be a double record |
| (not in T-366's 470) GB procurement laps | - | 2 HELD | 'laps only' lines also cite note 9 (40 d .. 70 d); T-366 listed them under GB laps (OWNED_ELSEWHERE in T-371) |
| (outside the released route) pool / stair / tank | - | 22 LISTED | T-359 scope; T-366 left them out of the route |
| **Total** | **470** | **351 HELD** = 470 - 23 - 98 + 2 | |

## 4. Cross-check (acceptance (c))

Every T-318 development line id (98) is bound exactly once; each one's V3.0.16 figure equals T-318's 'before' to the
gram (else the build stops); none is proposed HELD. T-318's 98 TOP BARS OVER SUPPORTS lines never cited note 9 (re-based
on note 2 / p.15) and are not in this binding. The binder refuses a line bound twice (tested).

## 5. Rule, tests, verdict proposals

**R-T373-1 (every villa; provenance T-366 F-T366-2, T-373):** a lap, development or starter length is valued only from a
printed authority whose wording names the bar population (sheet / note / detail), or from an answered owner rule; a note
naming another group (note 9: starters) is no authority; the line is HELD by name, BLANK, never 0 and never a borrowed
length; a line already re-booked by an integrated piece is not downgraded twice. Code: `lap_authority`, `bind_candidate`,
`rebook_t318`. Tests `tests/t373_lap_binding`: normal (starter at note 9 KEPT; temperature lap at p.15 NOTE 1 KEPT; owner
rule KEPT; T-318 drawn part KEPT); adverse (beam end at note 9 refused -> HELD; column lap at the temperature note
refused; unknown 'code default' authority refused; line bound twice refused; tonnes refused; HELD never 0); non-Alsenan
villa V373 by hand (Urban bar table): starters 8 ø16 at a printed starter note 50 d = 10.0992 kg KEPT; column lap 4 ø12
at a printed column note 45 d = 1.91808 kg KEPT; beam bottom ends 4 ø14 x 2 at the starter note 40 d .. 70 d = 5.41184 ..
9.47072 kg HELD BLANK; valued 17.42912 .. 21.48800 -> 12.01728 kg.

Verdict proposals: the 351 lines ENGINE_WRONG in basis (note 9 outside its group; bounds only, none released);
freelancer reinforcement is a kg/m3 lump (44.19 t) with no end / lap row: **RULE_DIFFERENCE, no %**.

## 6. Findings and what is missing

- **F-T373-1 (V3.0.27 not re-run end to end in this run).** The V3.0.27 view is the V3.0.16 extract (= V3.0.17, T-297)
  plus the T-318 re-booking by line id. T-318's own validation reports concrete, formwork and every non-rebar line
  byte-identical and STR.REBAR moved only on the 196 slab bar-end lines; T-338 changed printed formulas of VALUED released
  lines only (none of the 351). A reproduction run was started on the Drive copies (s.0); if it completed, its result is
  in the board handoff; otherwise the Checker re-binds on its own V3.0.27 with the same command (the binder reads the
  engine's line form directly) and the counts must equal s.2.
- **F-T373-2 (pool / stair / tank: note 9 outside its group, outside the route).** 22 BOUNDED_EXPOSURE lines,
  373.390 .. 718.480 kg ('2 x 40 d .. 2 x 70 d' development on stair waist / step / landing bars and pool families) rest
  on note 9 too. Same rule applies; T-359 owns them. For the Lead: a row (or T-359 acceptance) for the same record.
- Designer items unchanged from T-366 s.7 (lap / anchorage lengths and zones for beams, columns, ground beams; starter
  zone). No owner question: ERS s.2.7 is not met (a drawing gap, the owner rule is already answered: option B).

## 7. Lessons-register row proposed (ERS s.7)

| 2026-10-30 | 351 candidate rebar lines (3,001.680 .. 5,359.210 kg bounded) carried note 9's starter lap on beam ends, column
storey joints and ground-beam ends since V3.0.5; the slab 98 were re-booked by T-318 only because a slab
task looked at them | the bound text was copied from one ledger family to the next; no check asked whether the cited
note names the bar's group | a length is valued only from an authority naming the bar population; a line's basis is read
from its formula / bound / component, never its notes; an integrated re-booking is never downgraded twice (every villa;
provenance T-373) | tests/t373_lap_binding (beam end at note 9 refused; starter at note 9 kept; twice refused) | PROPOSED |
