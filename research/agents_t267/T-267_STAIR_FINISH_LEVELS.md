# T-267 Stair finish-level method (UP-STAIR-016) as an opt-in module, with coordination checks and design scenarios

Worker 1 (lane S), 2026-10-24, run session_01UTP2un2EKpPY2haakGttzN. Development villa, not an accuracy claim. ERS read;
s.2 steps 1-4, s.3 (finished vs structural datum; one element, several geometries), s.4, s.7 applied. Files:
engine/source/stair_finish_levels_v1.py (new, UNWIRED_PRODUCER), rules/owner_decisions/URBAN_RULES_1.7.0.json (new),
tests/t267_stair_finish_levels/*, research/agents_t267/*. No frozen module, rule / knowledge version, registry, candidate
or released quantity changed. Drawings cited by Drive title / sheet only; no coordinate or client data committed.

## 1. Result in engineering terms

- The owner's construction method is now one generic function chain: per-surface finishes (F0, every tread / landing
  S_i, F1) -> concrete level under every surface -> every structural riser (R + S(i-1) - S(i)); first = R + F0 - S1, last
  = R + S(last) - F1; the closure (sum of structural risers + any same-level concrete step = slab-to-slab) is checked; the
  frozen closed form stair_riser_schedule.first_last is called as a cross-check where the stair finish is uniform.
- Riser and going counts per flight come from the drawn surfaces (configuration evidence returned: LAST_RISER_ONTO_NEXT_LEVEL
  = N risers / N - 1 goings, LAST_TREAD_AT_LANDING_LEVEL = N / N); a riser between two landings is a TRANSITION riser.
- Going alternatives are continuous intervals (S-6) on the ACTUAL going count: 25 goings 300 -> 280 = -0.50 m; 24 goings
  = -0.48 m (owner example reproduced). Undrawn stairs: riser counts in 150 - 170, going intervals in 280 - 300 for a
  FIXED or MAXIMUM run, RUN_TYPE_UNKNOWN gives scenarios only (A12b); headroom gives exact going sub-intervals (the tread
  set under a member changes only at k x g = edge, so the test is exact between breakpoints). Only a single straight
  flight is enumerated; any landing configuration needs drawn polygons and winders are never generated (UNSUPPORTED).
- Findings, never changes: PROJECTION, MISALIGNED_TOP, EXTRA_OR_MISSING_STEP (a count conflict HOLDS every level unless an
  owner decision names the governing reading), LANDING_DEPTH, HEADROOM (only a VERIFIED limit eliminates or flags;
  otherwise CODE_NOT_VERIFIED), ARCH_STRUCT_DISAGREE, OUTSIDE_OWNER_PREFERENCE, UNEQUAL_FINISHED_RISERS (drawn concrete
  risers that look plausible but give unequal finished ones), LEVEL_INCONSISTENT, SURFACE_OVERLAP, CONCRETE_STEP_AT_SAME_LEVEL.
- Quantities from ONE record, each component on its own evidence (A15 / A16): CONCRETE per flight (section between plumb
  cuts, soffit parallel to the step-root line, equal to the frozen straight_flight for a uniform flight) and per landing
  (drawn polygon x plate); MARBLE_TREAD (drawn outline, or drawn going x width for a straight tread), MARBLE_RISER (visible
  riser = R - build-up of the surface it rises onto, UP-STAIR-003; the arrival riser needs the finish thickness at the
  arrival edge, HELD otherwise), MARBLE_LANDING (drawn polygon, arcs exact by bulge), NOSING only where specified, HANDRAIL
  per side = horizontal run / cos(pitch) per straight flight (over winders UNSUPPORTED), BARS always HELD here (the bar
  takeoff belongs to the printed detail). HELD = blank, never 0, never a range; scenario ranges only in the
  STAIR_SCENARIO_REPORT_V1 report, which the measured loader refuses.
- Code: per source, CODE_NOT_VERIFIED; Universal Design Code NOT_APPLICABLE for a private house (s.4 scope statement),
  "may apply, public areas only" for a dwelling development, applicability not decided when the manifest has no building
  type; the word COMPLIANT is never emitted.

## 2. Development villa, ST-01 (the dog-leg stair GF -> 1F -> 2F), its drawing facts only

Input: research/agents_t267/ALSENAN_ST01_INPUT.json (values already in merged T-184 / T-214 / T-258 research). Output:
summary.json. Two runs side by side (ERS s.2 step 2): DRAWING (the stair finish build-up is printed nowhere: HELD) and
OWNER_RULE_UP_STAIR_006 (0.030 m tread finish, ASSUMED - OWNER-APPROVED, marble per the owner's Q-53 / Q-66).

| Item | DRAWING | OWNER RULE (S = 30) | Basis |
|---|---|---|---|
| GF -> 1F risers | 27 x 166.667 (finished) | same | section A-A (Q-46 A governs); structural plan 28 = C-ST-4 CONFLICT listed |
| first / last structural riser GF -> 1F | HELD / HELD (tread finish) | 186.667 / 146.667 mm | F0 = F1 = 50 (T-214) |
| 1F -> 2F risers | 25 x 168.000 | same | section A-A |
| first / last structural riser 1F -> 2F | HELD / HELD | 188.000 / 148.000 mm | |
| closure slab-to-slab | not computable | 4500 / 4200 mm, closes | sum of structural risers |
| MS1-U / MS2-L / MS2-U flight concrete (gross, plumb cuts) | HELD (finish) | 1.054812 / 1.058824 / 1.058824 m3 | = T-258 net + parts owned by B20 / B23 to 0.000001 / 0.000068 / 0.000000 m3 |
| MS1-L | HELD (C-ST-4) | HELD (C-ST-4) | designer item, unchanged |
| MS1-T winders | HELD (no soffit, no outline) | HELD; rail UNSUPPORTED | S-9 |
| landings concrete | 0.2304 / 0.2392 / 0.2304 m3 | same | = T-258 VERIFIED / DRAWING-CONFIRMED |
| split-level half landing 1F -> 2F | +7.516 / +7.684, transition riser 13 | structural 168 | T-258 |
| going alternatives | MS2-L, MS2-U: 11 goings, run change -0.220 .. 0 m | same | 11 x (280 .. 300 - 300) |
| rails, nosing, bars | HELD / NOT_SPECIFIED / HELD | same | rail sides not established; bar detail ST p.16 not taken off here |
| code | CODE_NOT_VERIFIED, applicability not decided | same | no building type in a manifest |

Reconciliation (ERS s.2 step 4): the module's gross flight sections equal the frozen straight_flight on the same inputs
and equal T-258's net flight + the head / foot parts T-258 assigned to the beams (R-CONC-OWN-1); residual on MS2-L
-0.000068 m3 (-0.006 %), not explained here (T-258 cut the foot at the B20 band face; below the reading precision; named,
not closed). No candidate or released line is read or changed: this is a check, not a re-release.

What the owner method adds on this stair (physical meaning): the structural first riser is 20 mm taller and the last 20 mm
shorter than the finished riser (F0 = F1 = 50 vs S = 30). The released / candidate flight volumes are unaffected (a uniform
tread finish shifts the flight, it does not change its section between plumb cuts); what changes is the setting-out of the
first and last concrete risers, and that depends on a stair finish thickness the drawings do not print.

## 3. Verdict proposals and what is missing

- No freelancer quantity is compared (the module adds no BOQ line; the freelancer prices stairs as m3 lumps): no verdict.
- HELD: the stair finish build-up (drawing), the arrival-edge finish thickness, rail sides, winder outlines and soffit
  (MS1-T), MS1-L (C-ST-4), bars (ST p.16 detail; the bar takeoff is a separate package), building type in the manifest.
- Not done here (integration is a later lane I package after MERGED): rule_store / RULES_MANIFEST registration of 1.7.0;
  wiring into a candidate. Kuwait code clauses: none verified (owner register, 10:56).

## 4. Proposed lessons-register row (ERS s.7)

| Date | Problem | Root cause | General rule (scope) | Regression test | Status |
|---|---|---|---|---|---|
| 2026-10-24 | The flights' structural risers were taken equal to the finished riser (r = 4.50 / 27) while the floors carry 50 mm and the treads an unprinted finish: the first and last concrete risers were never stated | The finish build-ups of the floors and of the stair are two separate inputs; the uniform finished riser was used as the concrete riser | Every concrete riser = R + S(i-1) - S(i) from the finish of each surface (F0 / S_i / F1); an unknown finish holds the risers it touches, never 10 cm or 0; the flight section between plumb cuts is unaffected by a uniform tread finish (any villa) | tests/t267_stair_finish_levels (owner 15 + A1 - A23 + A12b; adverse: hardcoded N - 1, width x width landing, winder generation, scenario leak, 0 on HELD) | PROPOSED (T-267 READY) |
