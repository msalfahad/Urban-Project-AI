# T-409: B3-07 hidden profile / transition strips (development villa; rule for every villa)

Research only: no engine, method, rule / knowledge version, registry or candidate quantity changed. Worker 2,
2026-10-31. No private file was read in this run: every input is a committed, Checker-merged ledger, pinned by sha256
(first 8) in `summary.json`: T-325 sill / threshold ledger `ef6f2cb0` and lines `b85feb1a` (MERGED, V3.0.20 line ids;
T-327 retyped the closure strips in place), T-312 face ledger `71ca2ef5`, T-303 WP inventory `9d8ceb61`, T-296 skirting
summary `f1d34633`. Command: `python3 -I research/agents_t409/t409_alsenan.py [--check]`.

## 1. The physical element first (ERS s.2.1): B3-07 is two elements, not one

| Element | What is built | Where it exists | Governing rule |
|---|---|---|---|
| **Hidden profile** (AR 'بروفايل مخفي', the family's own Arabic name) | the aluminium profile of the HIDDEN skirting system, at the wall base | only where the project uses the hidden skirting system; then on the SAME payable path as the skirting, as its own item, never merged | US-08 (Urban standard, rule store `research/qs_wall_treatment_01/pa08/qortuba/boq/owner_rules.py:70`); `data/registry/URBAN_OWNER_METHOD_RULES.json` URBAN-SKIRTING-OPENING-METHOD v1 'trade: SKIRTING (and the hidden profile on the same path, US-08)'; Urban register item A-HPR-01 (`research/external_engine_lab/alsenan_registers.py:59`) |
| **Floor transition profile** | a metal / PVC strip where two floor finishes meet at a doorway or open boundary | only where the finish changes AND no other element owns the interface (marble threshold, external sill, frame, lift sill) | URBAN-FINISH-EXTRAS-SEPARATE-ITEMS v1 (OD-V3-4: 'other finish profiles lm' are separate items wherever source geometry supports them; it does not say every finish change has one); URBAN-WET-SERVICE-MARBLE-THRESHOLD v1 `floor_interfaces` (wet tile ends at the wet-side marble edge, dry porcelain at the dry-side edge, marble owns the footprint: no profile) |

The board row framed B3-07 as the doorway strip only. The family's Arabic name and the Urban rules point first to the
wall-base hidden profile (US-08), so both are measured here, apart.

## 2. Result (engineering terms)

**Floor transition profile: 40 boundaries, each once (`BOUNDARY_TABLE_T409.csv`):**

| Class | Boundaries | Clear width | Profile | Status |
|---|---|---|---|---|
| RULE_INTERFACE: marble threshold owns the strip | 14 wet doors (UP-THR-001 + marble rule) + the 3 basin-space openings A-GF-01 1.000, P-GF-01 0.900, open side GF-14 1.245 (owner Q-06 a) = **17** | 14.645 m (marble edges 29.290 m.l, geometry only) | none: the rule defines both tile edges | NOT_APPLICABLE (rule) |
| NO_FINISH_CHANGE | 7 dry doors D-GF-08, -13, D-1F-02, -03, -08, -09, D-2F-02 | 6.700 m | none: porcelain continues | NOT_APPLICABLE (dry porcelain default, ASSUMED — OWNER-APPROVED URBAN-DRY-FLOOR-PORCELAIN-DEFAULT v1) |
| OTHER_ELEMENT | W15 / W16 floor glazing (frame, 3.100 m); 3 lift landings (1.000 each, sill with the lift) | 6.100 m | none | NOT_APPLICABLE |
| SILL_HELD | 6 external entrances D-GF-01, -03, -06, -07, -09, D-2F-01 | 6.800 m | HELD blank | sill material by specification (none printed): 0, 1 or 2 finish edges -> bound **0 .. 13.600 m.l** |
| INTERFACE_HELD | pantry open side GF-07 4.490 (marble rule names the pantry not_applicable; Q-37 A is a WP answer); arch A-1F-01 1.000 to the dressing (its floor material HELD, T-223) | 5.490 m | HELD blank | bound **0 .. 5.490 m.l** |
| UNRESOLVED | gate D-GF-15 (width HELD), W03 (curved floor glazing), GF OP-007 side-passage mouth (floor beyond not traced) | 1.200 m known | blank | UNKNOWN |

Transition profile: **0 m.l released, 8 rows HELD with bound 0 .. 19.090 m.l, 3 UNKNOWN.** No row counts a strip under a
marble threshold; no HELD row carries a figure; no doorway is counted from both rooms (`check`).

**Hidden profile (US-08): HELD.** Alsenan's skirting system (hidden or normal) is not printed on any sheet and not in
any answered owner question (QP-06 'HIDDEN' is a Qortuba project rule, not transferable). If HIDDEN, the item equals the
skirting payable path: T-296 ledger **179.187 .. 205.150 lm** (candidate net 185.517 lm on V3.0.17); if NORMAL,
NOT_APPLICABLE. Lane I must re-read the path on the candidate of record (T-315 r2 moved the pantry base after V3.0.17).

## 3. Engine vs freelancer (committed FREELANCER_RAW_ROWS.json, 885 rows)

0 rows name a profile, 'بروفايل', a transition, a strip or an aluminium edge. His skirting rows: 282.85 m.l (porcelain
sheet), 81.32 (court), 29.87 (marble). Hidden profile: engine HELD (system unknown) vs freelancer no row: NOT COMPARED
(no counterpart); if the owner states HIDDEN, the freelancer omitted an item of about his own skirting path length.
Transition strips: engine 0 released vs freelancer 0: AGREE on nothing being priced; verdict proposal **RULE_DIFFERENCE
not applicable / UNRESOLVED** until the two held classes are settled.

## 4. Findings (no quantity moved here)

- **F-T409-1 (threshold family B3-04, basin spaces).** Owner Q-06 (a) gives the three basin-only hand-wash spaces
  (GF-02 3.1325 + GF-11 1.485 + GF-14 4.7321 = 9.35 m2, T-303) a MARBLE threshold. Their openings to dry space are
  doorless: A-GF-01 (arch, L-868aee12 BLOCKED, typed 'the floor finish continued' in T-325), P-GF-01 = engine OP-020
  (L-9bcc79e7 BLOCKED 'under wet review'), and the 1.245 m open side of GF-14 (no line; no wall, so no threshold depth
  is drawn). When lane I fills them they are marble thresholds (A-GF-01 1.000 x 0.150 = 0.150 m2, P-GF-01 0.900 x 0.200
  = 0.180 m2, GF-14 depth HELD), never porcelain continued and never a profile.
- **F-T409-2 (T-325 finish-change edge).** T-325 records 1 finish edge per external entrance (6.800 m.l); with the sill
  material unknown the count is 0, 1 or 2 per door (0 .. 13.600 m.l). Geometry only (NOT_AN_ITEM there); no line changes.
- **F-T409-3 (B3-07 scope).** The family master describes B3-07 only through ARCH.THRESHOLD strips; the hidden profile
  (US-08) belongs to it and has no line, no system answer and no candidate carrier.

## 5. Rule, tests, lessons

- **R-T409-1** (research rule, every villa; a rule version only when adopted): B3-07 = two items. (a) Hidden profile:
  only under the hidden skirting system, on the skirting's payable path, its own item; system unknown = HELD with the
  path as bound. (b) Floor transition profile per boundary: no finish change or another element owning the interface =
  NOT_APPLICABLE; a finish change with no rule or printed note = HELD with bound 0 .. width (external sill 0 .. 2 x
  width); never a strip under a marble threshold; one boundary once; HELD blank, never 0.
- Code `research/agents_t409/transition_profiles.py` (generic), `t409_alsenan.py` (development villa).
- Tests `tests/t409_transition_profiles` (19): non-Alsenan Villa T409 hand fixture (bath door marble, dry door,
  open kitchen 3.20 HELD, entrance 0 .. 2.40, floor glazing frame, porcelain / marble majlis 2.00 HELD, gate UNKNOWN;
  held 0 .. 7.60 m.l), metres / millimetres / mirror / rotation; ADVERSE: one doorway counted from both rooms by id and
  by location, strip under a marble threshold, HELD as 0, profile line on a NOT_APPLICABLE boundary, HELD without bound,
  unknown unit / negative width / bad kind, external entrance as marble, unknown skirting system, inverted path;
  development-villa pins (reproduces, 30 census doors / arches once, class counts, held bound, Q-06 openings).
- Lessons row (proposed): 2026-10-31 | B3-07 was scoped as doorway strips although its Arabic name and US-08 define a
  wall-base hidden profile on the skirting path | the family was read from its engine evidence (ARCH.THRESHOLD) instead
  of its physical element | define a family's element from its name in both languages and the Urban rule that names it
  before choosing a carrier; a family that names two elements is split (every villa) | tests/t409_* (hidden profile by
  system; strip under marble refused) | PROPOSED.

## 6. For lane I (proposal, nothing moved)

A row 'B3-07 integration': (1) a HIDDEN_PROFILE line HELD blank with the skirting path bound, pending the skirting
system (owner / designer item for the Lead's C_UNLOCK_MATRIX: 'hidden or normal skirting'); (2) 8 transition-profile
rows HELD blank by boundary id with their bounds (0 .. 19.090 m.l), the rest NOT_APPLICABLE with their class; (3) the
F-T409-1 retypes in the threshold family (B3-04), not in B3-07.
