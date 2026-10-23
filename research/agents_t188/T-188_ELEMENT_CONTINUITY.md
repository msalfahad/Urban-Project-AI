# T-188 Element inventory across disciplines (R2) and storey continuity (R3)

Worker 1 (lane S), 2026-10-23. Residential review R2 + R3 (PROJECT_UNDERSTANDING_ASSESSMENT s.6). A pure CHECK module,
NOT wired into any method version; no engine, rule, knowledge, registry or released quantity changes; released default
stays ARCH_TAKEOFF_V2.9 + route G. Development villa, not an accuracy claim. ERS applied: s.2 step 1 (each element
defined physically before any line is looked at), s.2.2 (evidence hierarchy; absence of evidence kept apart from evidence
of absence), s.3 (geometric scope before numbers; a notation / shape typed from its own evidence), s.7 (lessons row).

Files: `engine/source/element_continuity_v1.py` (stdlib only, imports no engine module), `research/agents_t188/
alsenan_t188.py` (development-villa inventory, three BOQ states), `FINDINGS_T188.csv`, `summary.json`,
`tests/t188_element_continuity/` (villa K synthetic hand truth + adverse cases; development-villa cases), 40 tests.
Repeat: `python3 -I research/agents_t188/alsenan_t188.py [--write]`.

Sources: merged ledgers with checker verdicts, cited per element (T-184 924c2bd stairs, T-183 r2 6380294 pool, T-185
94e39ee6 domes, T-166 tank, T-187 8a6d604a candidate lines and the checker's 06:24 dome identification, T-196 f933ef8a
freelancer row ids, S8.6 / pre-S8 / S8.1A lift evidence) plus this run's own text read of "ST7757 dxf.dxf" (Drive
"Alsenan chalet project", sha 9f9d1179, private copy only): sheet titles (FOUNDATION PLAN, GROUND BEAMS PLAN, GROUND /
FIRST / SECOND FLOOR ROOF SLAB, DETAIL OF SWIMMING POOL, DETAIL OF DOME), the lift footing mark FF (text 1676) under
four column marks C1 / C2 / C2 / C9, and "WATER TANK PLACE" (text 1A85) on the second-floor roof slab. No other text on
the structural set names a lift, pit or tank. Also own read of P7757.dxf (from P7757_DXF_COMPRESSED.zip, sha ab54dd55):
exactly two 'VOID' labels, both on the 1st.FLOOR PLAN; the structural set prints exactly two, both in the GROUND FLOOR
ROOF SLAB frame, with the same spacing (7.745 / 6.369 m vs 7.744 / 6.369 m). Quantities are not re-derived here (none is produced).

## 1. Result in engineering terms (findings, not quantities)

Per element, three BOQ states: A = released V2.9 + route G; V305 = candidate V3.0.5; V306 = candidate V3.0.6 (opt-in).

| Element (physical) | A | V305 | V306 | Meaning for the BOQ |
|---|---|---|---|---|
| ST-01 dog-leg beside the lift, occupies GF and 1F | 1F storey WITHOUT LINE (HELD) | 1F WITHOUT LINE | carried (MS2-L VERIFIED, MS2-U DRAWING-CONFIRMED, MS2-LD HELD, MS2-TR UNKNOWN) | the 1F -> 2F storey (2.598 m3 in the T-184 ledger) is invisible in A and V3.0.5: case 1 reproduced; V3.0.6 fixes it |
| ST-01b lobby flight, GF | GF WITHOUT LINE | GF WITHOUT LINE | placeholder UNKNOWN | drawn flight with no line in A / V3.0.5 (T-184 small omission) |
| ST-02 round stair, occupies GF, arrives 1F | no continuity flag | none | none | ends at 1F with evidence: case 4 (must NOT flag) reproduced |
| ST-03 entrance stair | none | none | none | |
| all four stairs | typical detail only (REVIEW) | same | same | p.16 is N.T.S. (R-STAIR-TYP-1): arrangement, never a project dimension |
| DOME-A west terrace | (convention line, binding ambiguous) | + a STAIR line on DOME-A: KIND_MISMATCH (HELD) | same, line BLOCKED | the 4.451 m3 'winder' is DOME-A (checker 06:24): typed from shape, held, never relabelled |
| DOME-A / DOME-B | 2 convention lines bound to "one of A / B" (REVIEW) | same | same | the route lines carry no place the ledgers cite; which line is which dome is not established |
| DOME-TOWER | no structural counterpart, no detail, NO BOQ LINE (HELD) | same | no structural counterpart, no detail; placeholder line UNKNOWN | case 2 reproduced: the third dome is drawn only in the architecture |
| POOL-01 | steps NOT DRAWN (consultant item) | same | same | owner 16:45: an absence of evidence, never a verified zero |
| pump room (freelancer RC:S17:13 walls, RC:S17:15 floor) | NOT DRAWN | NOT DRAWN | NOT DRAWN | case 3 reproduced: listed, no quantity, never 0 (his 1.080 + 2.400 m3 stay comparison-only) |
| LIFT-01, occupies FDN .. 2F | pit HELD (opening 3.24 m2 and FF base drawn; depth / walls not printed), NO BOQ LINE (HELD), end above 2F not evidenced (REVIEW) | same | same | NEW: the lift has no structural BOQ line in any state while the freelancer prices lift walls (RC:S13:11); pit concrete HELD (designer item) |
| VOID-1F-a / VOID-1F-b, 1F floor openings | none | none | none | both disciplines draw both voids at matching places; neither set prints a void at 2F: they end at 1F (no flag, correct) |
| TANK-01 on the +13.90 roof | NO structural detail, NO BOQ LINE (HELD) | same | same | NEW (confirms T-166): the tank place and its T&B roof panels are drawn; walls / base nowhere; the panels are slab lines, not tank lines |

Counts (summary.json): A 19 findings (HELD 9, REVIEW 7, NOT_DRAWN 3), V305 20 (HELD 10, REVIEW 7, NOT_DRAWN 3), V306 17 (HELD 7, REVIEW 7, NOT_DRAWN 3). No finding carries
a quantity; every line it names keeps its own state.

## 2. What the check does (any villa)

R2: every element kind (STAIR, LIFT, SHAFT, VOID, COLUMN, POOL, TANK, DOME, RAMP, PARAPET) has a rule set: structural
counterpart required, architecture required, structural detail required, required components (LIFT: PIT; POOL: BASE,
WALLS), line requirement (PER_STOREY for stair / shaft / column, ANY for lift / pool / tank / dome / ramp / parapet, none
for a void: a void is measured as deductions of other elements), owner trade and allowed trades (ELEMENT_REGISTER
rulings: stair concrete STRUCTURE, marble / handrails lane A, shaft walls WALL elements, domes STRUCTURE). Reverse: every
line bound to an element (or UNBOUND / BINDING_AMBIGUOUS), every reference row to a drawn element (else NOT_DRAWN).
R3: for spanning kinds, the occupied storeys come from the LEVELS (else from the drawings, basis printed); each occupied
storey needs a drawing (else STOREY_NOT_DRAWN) and, for PER_STOREY kinds, a line of the owner trade (else
STOREY_WITHOUT_LINE, the D-T184-1 pattern); a drawing outside the span is a CONFLICT; flights SEEN through an opening and
a stair's ARRIVAL never make a storey occupied (R-STAIR-CONT-1); plan places across storeys must agree within a stated
tolerance (PLACE_MISMATCH); an end below the top storey without cited evidence is REVIEW only (never a hold).
Absence needs a declared search: without it the finding is NOT_SEARCHED (UNKNOWN), never "not drawn".

## 3. Rules (proposed, general, labelled; a rule change is a new rule version)

- R-INV-1 (any villa): before any quantity, every element is listed once per discipline with the sheet that draws it;
  an element drawn in one discipline only is HELD in the BOQ until the other discipline or a detail fixes it.
- R-INV-2: an absence ("not drawn") is recorded only with the sheets searched; otherwise UNKNOWN.
- R-INV-3: a line is typed by the element at its place, never by the route's shape class; a mismatch is held as a
  misread and the element's own line is measured separately.
- R-CONT-1: an element that spans storeys has a drawing and (where its kind needs one) a line on every storey its levels
  give; a missing storey is HELD, never folded into another storey's line.

## 4. Tests (tests/t188_element_continuity, 40 pass)

Villa K (3 storeys over a foundation, other names, plan places in metres): hand truth of 15 findings (module docstring
of villa_k.py); stair folded storey normal vs adverse; a held placeholder accounts for a storey and keeps its state; a
storey with no drawing; correct end not flagged vs unevidenced end REVIEW only; seen-below never occupies vs a drawn
flight above the span = CONFLICT; occupancy from drawings when no levels; mirror x / y and a 90 deg rotation leave
every finding unchanged; place mismatch 3.000 m; column without its top storey line; dome without structure; absence
without a search = NOT_SEARCHED; lift without pit vs pit drawn vs pit HELD; misread line held, not the element's own
line; trade not allowed; reference row on no drawing; optional vs required component not drawn; ambiguous binding;
void needs no line; 10 input guards (unknown kind / storey / discipline / detail state, missing refs, xy without
tolerance, duplicate id, element and element_any, duplicate storeys). Development villa: the four known cases, the
misread on the candidates only, lift / tank / lobby flight per state, the two voids joined and ending at 1F,
committed CSV current.

## 5. Who is right (verdict proposals)

- ST-01 1F storey: ENGINE (V3.0.6 candidate) RIGHT against A / V3.0.5 on scope (T-184 hand ledger, checker 01:57 / 06:24).
- Pump room: ENGINE RIGHT on scope (no drawing, T-183 item K); freelancer rows NOT DRAWN, comparison-only.
- Tower dome: UNRESOLVED (designer: structural drawing of the tower dome; Q-27 A says three domes).
- Lift: UNRESOLVED / HELD on both sides: the drawings fix the pit opening and the lift base but not the pit depth or
  walls; the freelancer's lift-wall row cannot be judged until the designer prints them.

## 6. Not done / uncertain

Shafts, parapets, ramps and columns are supported by the module and tested on villa K but NOT inventoried on the
development villa this run (the ST-01 shaft walls are lane A WALL elements inside per-floor wall aggregates, not bound per
element; columns wait for the register's one-element-per-storey rework T-196 r2). The voids' end at 1F rests on a label
search of both sets plus the slab panels above (T-139), not on a section cut. Which convention line is DOME-A vs DOME-B is not established (route lines carry no place). The tank's
architectural sheets were not searched (kind does not require them). Pool rows A / V3.0.5 line ids without a route
prefix are descriptors (the ledgers cite those lines by item, floor and figure). Designer items raised: tower dome
structure; lift pit depth / walls / base level; tank walls / base; access to the tank (C-ST-4, T-184).

## 7. Lessons-register row proposed (ERS s.7)

| 2026-10-23 | Four element-level failures found one at a time (a stair storey folded away, a dome typed as a stair, a dome with no structural drawing, a pump room on no drawing); the lift and the tank have no structural line in any state | No inventory across disciplines and storeys before measuring: lines were checked against lines, never against the list of physical elements | Every element is listed per discipline and storey (with the sheets searched) before quantities; a storey or discipline gap is HELD, an unsearched absence is UNKNOWN, a line is typed by the element at its place (any villa) | tests/t188_element_continuity (adverse: folded storey, misread line, unsearched absence, mirrored plan) | READY (T-188) |
