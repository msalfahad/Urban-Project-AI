# T-366 Lap-length authority census for B11-04 (net vs procurement): released rebar route (development villa; rules for every villa)

Worker 3 (taking a lane S row: lane I had no claimable TODO, READY 4 > 3, row backlog-permitted), 2026-10-30, run
session_01E6cPneUgzTK2MvcFqkG6Wt. A source census, not a takeoff: **no kg computed, no lap applied, no candidate line,
rule, method or released quantity changed** (owner 2026-10-25 10:33; OWNER_RULE_REBAR_2026-10-24). B11-04 stays
IMPLEMENTED_NOT_INTEGRATED. Drawings named by Drive folder and title only.

## 0. Sources read this run

Drive "Alsenan chalet project" (read-only; private copies in the git-excluded folder, never committed):
'ST7757 dxf.dxf' (sha256 9f9d1179..) and 'ST7757.pdf' (sha256 74da1523.., 16 pages, no text layer, read by eye at
100 / 200 / 400 dpi). DXF: **all 1,934 TEXT / MTEXT / ATTRIB entities** (model space and every block) dumped by handle
and searched for lap / splice / overlap / dia / anchor / develop / stock / length and the Arabic تشريك / رباط / اشاير /
طول / وصل / تراكب: one hit only, 1BA9 '* L=LENGTH OF COLUMN.' (p.9 link-band notation, not a lap). PDF by eye: p.8
general notes 1 - 24; p.9 schedules (columns 1B3A, footings 1C32, column details 1BA5 / 1BA9 / 1BAA); p.10 simple beams
(1E47); p.11 / p.12 continuous beams (206B, 272B, 2035) and their typical span diagram; p.13 - p.15 details (PDF only,
not in the DXF). p.16 (stairs) and the p.7 pool / dome are T-359's scope (outside the released route).
Merged ledgers built on, cited, not re-derived (WORKFLOW_CONTROLS s.10.5): T-273 r2 (laps, column lap / starter
reconciliation), T-148 (columns), T-149 (beams), T-265 / T-138 (ground beams), T-299 (route G items), T-297 (the
candidate's 2,505 reinforcement lines, V3.0.16 = V3.0.17), T-307 / T-318 (slab bar ends), T-359 (outside the route).

Files: `t366_lap_census.py` (LAP_AUTHORITY_CENSUS_V1, stdlib: authority reading, refusals, owner splice formula vs the
frozen form), `t366_alsenan_input.py` -> `ALSENAN_LAP_AUTHORITY_INPUT.json` (printed readings only) + `LINE_BINDING_T366.json`
(every candidate reinforcement line -> its population), outputs `T366_MATRIX.csv`, `T366_SUMMARY.json`. Tests
`tests/t366_lap_census` (23). Repeat: `python -I research/agents_t366/t366_alsenan_input.py --check`, then
`python -I research/agents_t366/t366_lap_census.py research/agents_t366/ALSENAN_LAP_AUTHORITY_INPUT.json --csv ... --json ...`.

## 1. Engineering question and method (ERS s.2.1: notation before arithmetic)

Physical element: a lap splice is the overlap of two bars of ONE bar group where the bar run is longer than the stock
bar, or where the detail draws two bars overlapping. It is installed steel, but a BBS / procurement length, never part
of the net (owner 15:31). Its two facets are separate: the splice NEED (run vs stock, or a drawn overlap) and the lap
LENGTH (authority). The census answers, per population: does any note or detail print a lap length for THAT group
(sheet, handle or position, value in d, EXACT or 'not less than' MINIMUM, zone printed or not), and is a splice needed
at all. Rules (code-enforced, `classify`): a note is an authority only for the groups its wording names; categories
LAP_SPLICE / STARTER_BARS / ANCHORAGE_DEVELOPMENT / HOOK_BEND / MECHANICAL_COUPLER stay apart (owner s.6 (1)); a
tension / compression note needs a printed zone for the population, else the lap is HELD with both minimums listed
(never a range, never a pick); two authorities that disagree are a CONFLICT; no kg field and no lap inside a net.
Owner manual method vs drawing-derived method: the owner's 40 d / 60 d convention is a proposal under assessment
(OWNER_RULE_REBAR s.2), never applied here; the drawing-derived reading is the only one, shown in full in the matrix.

## 2. Result: 27 released-route populations (acceptance (a))

Authority: **3 with a printed source, 24 NOT PRINTED**. Lap status: 1 PRINTED, 1 CONFLICT, 1 HELD (zone), 12 HELD (no
authority), 12 NOT_REQUIRED (every run shorter than the stock).

| Population | Printed lap source (sheet, handle / position) | Value, kind, zone | Splice need (basis) | Lap status | Candidate lines (V3.0.16) |
|---|---|---|---|---|---|
| Slab temperature bars | p.15 NOTE 1 'LAP LENGTH FOR ALL TEMPERATURE BARS SHALL BE 40xDIA' (PDF only) | 40 d, EXACT, zone n/a | not established: the group itself is blocked (no 16 cm row in the p.15 table, T-273) | **PRINTED** (mm waits on the diameter) | 3 |
| Starter -> column splice, shallow footing (upper G.B < 2.5 m above) | **p.13 TYP. DETAIL OF ISOLATED FOOTING (right): dimension '40 ø' from the footing top to the starter's end crank** + p.8 note 9 (starter bars) | 40 ø EXACT (typical) vs note 9 >= 70 d tension / >= 40 d compression | drawn overlap | **CONFLICT_ZONE_NOT_PRINTED** (F-T366-1) | 28 route neck lines shared with the deep case |
| Starter -> column splice, deep footing (p.13 left, with a lower G.B) | p.8 note 9 only (the splice cranks are drawn, no dimension) | >= 70 d tension / >= 40 d compression, zone not printed | drawn overlap | HELD_ZONE_NOT_PRINTED | (shared, above) |
| Column main bars at storey joints | none (p.9 schedule changes the bar count per storey; note 9 names starter bars only) | - | REQUIRED (stack 12.90 m > 12 m, T-148; bar changes at joints) | HELD_NO_AUTHORITY (F-T366-2) | 266 |
| Column links | none (1BAA '6ø8/m'; closure = HOOK_BEND) | - | not required (closed link < 12 m) | NOT_REQUIRED | 207 |
| Twisted-column extra 4 ø16 + spiral (p.15) | none | - | not established | HELD_NO_AUTHORITY | 4 |
| Footing bottom mesh / top mesh | none (p.9, p.13) | - | not required (largest side 4.60 m, FF) | NOT_REQUIRED | 51 / 14 |
| Footing boxed bars | none | - | not established (closure is a shape question, T-371) | HELD_NO_AUTHORITY | 20 |
| Ground-beam main bars | none (p.13 sections) | - | REQUIRED (7D0 / FC 18.570 m, 170 / 7C3 13.770 m, T-273) | HELD_NO_AUTHORITY | 177 |
| Ground-beam side bars 2 ø12/30cm | none | - | not established (continuity through columns not printed) | HELD_NO_AUTHORITY | 30 |
| Ground-beam stirrups | none | - | not required | NOT_REQUIRED | 62 |
| Strap beams SB1 - SB3 | none (p.10) | - | not required (<= 7.14 m, T-299) | NOT_REQUIRED | 21 |
| Simple beams B1 - B29, CA, B.W main bars | none (p.10) | - | not required (longest 7.80 m, T-149) | NOT_REQUIRED | 404 (+200 route G items shared with the CB groups: mark not on the item id) |
| Beam side bars / beam links / planted-column beam 4 ø16 | none | - | not required | NOT_REQUIRED | 61 / 243 / 2 |
| Continuous-beam bottom bars | none: the overlap of the two spans' bottom bars across the interior support is DRAWN (typical diagram and every CB row), not dimensioned ('0.15 L' drawn, tied to no bar, T-149) | - | drawn overlap | HELD_NO_AUTHORITY (F-T366-3) | 58 (+200 shared) |
| Continuous-beam top through / support bars | none | - | not required (route G longest 8.708 m) | NOT_REQUIRED | 115 / 46 (+200 shared) |
| Slab bottom mesh | none (p.15 prints 'STOP 50% OF BOT. REINF. BALANCE CONTINUOUS', no lap) | - | not established | HELD_NO_AUTHORITY | 268 |
| Slab top bars over supports | none (p.15 'EXTEND 50% OF TOP REINF. INTO ADJACENT SLAB WHERE POSSIBLE') | - | not established | HELD_NO_AUTHORITY | 98 |
| Slab extra bars (corner, second-bar zones) | none | - | not established | HELD_NO_AUTHORITY | 15 |
| Ground slab mesh | none | - | not established | HELD_NO_AUTHORITY | 24 |
| Boundary-wall G.B 2 ø14 / 3 ø16 (T&B) (p.14) | none | - | REQUIRED (7FE#1 31.370 m, T-273) | HELD_NO_AUTHORITY | none in the candidate |
| Boundary-wall columns 4 ø14 / pad 7 ø12 (p.14) | none | - | not established / not required (pad 1.30 m) | HELD / NOT_REQUIRED | none |

Every one of the 2,505 candidate reinforcement lines is bound (LINE_BINDING_T366.json; the binding refuses an unbound
line); 88 pool / stair / tank lines are left to T-359. Each population appears once (the census refuses a missing or
duplicated population).

## 3. Stock length (acceptance (b))

**Not printed** on any sheet (the DXF search of s.0 and p.8, p.13 - p.16 by eye). An owner-approved value exists: 12.0 m,
URBAN-REBAR-NET-AND-PROCUREMENT@v1 (owner decision OD-V3-3) and the same 12 m in OWNER_RULE_REBAR s.2. Status
**ASSUMED — OWNER-APPROVED** with that source (WORKFLOW_CONTROLS s.4, which wins over the row's "printed or HELD": an
approved fallback is not HELD); it stays visible as such and is never written as printed.

## 4. Findings for the Checker / Lead (no quantity changed)

- **F-T366-1 (new printed lap source: starter projection 40 ø, p.13).** The right-hand TYP. DETAIL OF ISOLATED FOOTING
  (footings whose upper G.B is less than 2.5 m above) dimensions the starter projection above the footing top as
  '40 ø'; the left-hand (deeper) detail draws the splice cranks without a dimension. T-273 r1 / r2 and the d1_1 source
  audit record p.15 NOTE 1 as "the only lap print in the set"; the column ledger's starter projection (40 D, 278.836 kg
  on 31 chains, T-273 r2 s.9.2) was attributed to note 9's compression minimum. Its printed basis is this detail, but
  note 9 also names starter bars and asks for at least 70 d in tension zones; the zone is not printed. Verdict proposal
  **UNRESOLVED**: the value is printed (typical), its governing of a tension-zone starter is a designer item (which
  detail applies to which footing also depends on the held upper-G.B-to-footing level difference, the T-206 datum).
  Effect: none on any line now (starters PROVISIONAL); a future starter line must cite p.13, not note 9 alone.
- **F-T366-2 (note 9 used outside its named group).** In V3.0.16 470 BOUNDED_EXPOSURE / BLOCKED lines of the released-
  route populations carry note 9 (a STARTER_BARS note) as the basis of a lap, an end or a development length: beams
  254 ('bottom / top / top corner / support ends (note 9, 40d..70d)'), column storey laps 56, ground-beam bar ends 62,
  slab 'DEVELOPMENT / ANCHORAGE' 98 (T-318 later re-based the slab ends: check those 98 on the current candidate).
  None is released; owner 2026-10-24 s.4 (3) / s.6 (1) already forbid this use. Listed so lane I does not carry the
  basis forward.
- **F-T366-3 (continuous-beam bottom overlap drawn, undimensioned).** p.11 / p.12 draw the bottom bars of two spans
  overlapping across the interior support; no length is printed. A drawn overlap is a splice NEED with no LENGTH: HELD.
- **F-T366-4 (basis of the owner proposal).** OWNER_RULE_REBAR s.2 states 40 d / 60 d "for fc = 250 kg/cm2 and Grade
  60"; p.8 note 6 prints f'c >= 300 kg/cm2 for this project (note 8: fy >= 4200 kg/cm2 = Grade 60 agrees). The
  convention's stated basis is not this project's concrete. For the main chat's assessment; no quantity uses it.
- **F-T366-5 (register wording).** OD-V3-3 (research/external_engine_lab/alsenan_v3_owner_decisions.json) lists
  note 9 as "lap_tension 70 x dia / lap_compression 40 x dia" accepted evidence, and the method register statement says
  "cover and laps from the structural notes". Since 2026-10-24 note 9 is a starter-bar note only. A reader of the
  register can still apply it as a lap: a wording item for the Lead (a new rule version if changed; nothing edited).

## 5. The frozen route G count (acceptance (c)): `continuous_beams._with_laps`

Frozen code (engine/source/continuous_beams.py lines 451 - 455, read only): `n = ceil(L / S) - 1`, independent of the
lap. Owner formula (OWNER_RULE_REBAR s.2; bbs_optimiser.split_run): `n = ceil((L - S) / (S - lap))`. S = 12 m (s.3). Lap
taken from the two lengths the drawings print as 40 x d (p.15 temperature bars; p.13 starter projection); both counts
checked against the frozen code itself by import (test) and split_run:

| Run L | Lap | Owner: (L - S) / (S - lap) | Owner laps | Frozen laps | Bar length owner / frozen | Physical check |
|---|---|---|---|---|---|---|
| 23.8 m | 40 x 12 mm = 0.48 m | 11.8 / 11.52 = 1.024 | **2** | 1 | 24.76 / 24.28 m (frozen 0.48 m short) | 2 pieces cover 2 x 12 - 0.48 = 23.52 m < 23.8: 1 lap cannot close the run |
| 35.0 m | 0.48 m | 23 / 11.52 = 1.997 | 2 | 2 | 35.96 / 35.96 m (agree) | 3 pieces cover 36 - 0.96 = 35.04 m >= 35 |
| 23.8 m | 40 x 16 mm = 0.64 m | 11.8 / 11.36 = 1.039 | **2** | 1 | 25.08 / 24.44 m | 2 pieces cover 23.36 m < 23.8 |
| 35.0 m | 0.64 m | 23 / 11.36 = 2.025 | **3** | 2 | 36.92 / 36.28 m | 3 pieces cover 34.72 m < 35 |

General statement (proved in `frozen_safe_lap_max`, tested): the frozen count equals the owner count exactly when
lap <= S - (L - S) / n0 with n0 = ceil(L / S) - 1: 0.20 m for 23.8 m, 0.50 m for 35 m. So the defect is real for every
lap above that window, but its trigger depends on the lap: the record "35 m gets 2 instead of 3" (OWNER_RULE_REBAR
s.3) holds only for laps above 0.50 m (e.g. 40 d at ø16, 60 d at ø14); at the only printed lap on Alsenan's temperature
bars (Y12, 0.48 m) a 35 m run is counted right. Alsenan magnitude unchanged: 0.000 kg (no route G run over 12 m, s.5 of
the owner rule). Finding only; the frozen module is not edited (freeze 0).

## 6. Engine vs freelancer; verdict proposals

No BOQ line moves. The freelancer's reinforcement is a kg/m3 lump (44.19 t) with no lap row: **RULE_DIFFERENCE, no %**
(URBAN-REBAR-NET-AND-PROCUREMENT@v1). Engine lap lines: none released before or after. Verdict proposals: F-T366-1
UNRESOLVED (designer); F-T366-2 ENGINE_WRONG in basis (bounds only, not released); F-T366-3 UNRESOLVED (designer: lap
length at the CB support); frozen count ENGINE_WRONG for runs in the stated windows (0 effect on Alsenan).

## 7. Designer items (no owner question: ERS s.2.7 not met, each is a drawing gap)

Proposed for the Lead's RFI lists: (1) lap length and permitted splice zones for column, ground-beam, boundary-G.B and
slab main bars (none printed; ground beams and boundary G.B need splices); (2) tension / compression zone of the
starter splices, and whether the p.13 40 ø applies regardless of zone; (3) overlap length of the continuous-beam bottom
bars at interior supports; (4) stock length if the designer requires other than 12 m.

## 8. Rule proposed (every villa; provenance T-366; a new rule version only when adopted)

**R-LAP-AUTH-1**: before any lap or procurement line, census every bar population of the route: per population the
printed lap source (sheet, handle or position), its value in d, EXACT or MINIMUM, and the zone printed or not; a note
counts only for the groups its wording names and only in its own detailing category; a zone-split minimum with no
printed zone is HELD with both minimums; two disagreeing authorities are a CONFLICT; splice NEED (run vs stock, a
drawn overlap) is stated apart from lap LENGTH; the stock length is printed, owner-approved with its source, or HELD.

## 9. Lessons-register row (proposed, ERS s.7)

| 2026-10-30 | A dimensioned starter projection (p.13 '40 ø') was missed while every source audit said the only lap print was
the p.15 temperature note, and 470 candidate lines took note 9 (a starter-bar note) as the basis of beam, column,
ground-beam and slab laps / ends | sources were searched by text (the DXF has no p.13 - p.16), and a note was applied by
its numbers, not by the group its wording names | census every population against every sheet, PDF-only sheets by eye;
a note is an authority only for the groups it names (every villa, T-366) | tests/t366_lap_census (40 d temperature note
on beam bars refused; guessed zone refused; lap in the net refused; disagreeing authorities = CONFLICT) | PROPOSED |

## 10. Self-gate and not done

self-gate: a c d f h PASS (a: real code + tests; c: non-Alsenan villa K366 hand fixture + adverse; d: no historical
regression, research files only, freeze 0; f: held stays held, never 0, no kg; h: every population and every candidate
line bound). Not done: the binding uses the V3.0.16 extract (= V3.0.17, T-297); later integrations (T-318 slab ends,
V3.0.2x) changed slab end lines, so the 98 slab-development count must be re-read on the current candidate by lane I.
Route G beam items (200) carry no mark in their id and are bound jointly to the simple / continuous beam populations.
