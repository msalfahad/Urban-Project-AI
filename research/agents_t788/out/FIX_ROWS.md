# T-788 F-22 CORNICE vs FREELANCER (worker 2, 2026-11-14, r2 after the Checker REJECTED r1; base ARCH_TAKEOFF_V3.0.86, line unchanged 302.88)

PHYSICAL ELEMENT: the gypsum cornice at the junction of the decor (false) ceiling and the wall faces, per room. The
freelancer's two cornice lines (halls / rooms 282.85 lm, wet rooms 144.61 lm = 427.46 lm) are column G of his 'decor'
sheet, one perimeter per decor piece; no facade or parapet cornice is billed under this title (his facade items sit in
the external finish trade), so the whole -124.58 lm is interior.

## Fix row (one line, unwired; T-770 wires it)

| line | item | before | after | label | basis |
|---|---|---|---|---|---|
| L-33d272f5b4d7b33767b6 | FIN.CEILING.CORNICE lm | 302.88 | **426.31** | ESTIMATE (lengths MEASURED from the arch DXF faces; the run itself has no printed detail, Q-57 A mod) | R-T788-1 / -3: closed rooms (T-147) + the open zones' wall runs on their room side only; dry 264.91 + wet 161.40 |

Engine vs freelancer: 302.88 vs 427.46 (-124.58, -29.1 %) -> **426.31 vs 427.46 (-1.15 lm, -0.27 %)** (r1 430.44 counted the outdoor pocket beyond the GF curved glazing: -4.13).

## The -124.58 lm split into causes (all one engine defect: T-147 / T-771 left every open zone out, "run not closed")

| zone (drawing: arch DXF, GF / 1F / 2F plans) | run added, lm | how |
|---|---|---|
| GF open room (dining / entrance / reception / hall) | 54.455 | wall faces 52.899 + gaps inside wall lines 1.556 (south window 0.285, wash-lobby opening 1.271); pantry side 4.50 no wall; R-T788-3: the outdoor pocket beyond the NE curved glazing (outer glazing face W 280 1.772, clip cuts 1.475 + 0.891 OPEN_SIDE) not counted |
| 1F living zone (living + corridor + landing + light well) | 39.440 | face 52.44 - stair-box walls 13.00; box line 2.50 open, not counted (the earlier 57.339 polygon length carried a clip sliver) |
| GF wash lobby (2 basins) incl. its niche face (T-147 union) | 12.558 | walls 7.434 + opening 1.271 + niche 3.853 |
| GF pantry (wet, owner Q-37 A) | 10.480 | walls 7.690 + south window gap 2.790; dining side 4.50 open |
| 2F stair lobby + shaft-box top (one ceiling under the 2F roof slab) | +6.500 | face 22.00 replaces the ST-2F 15.50 T-147 already carried |
| **total added** | **123.433** | 302.88 + 123.433 = 426.313 -> 426.31 |

Verdict proposal: **FREELANCER_RIGHT** on the 123.43 lm (open zones have walls, so they have a cornice run).

## Residual -1.15 lm (-0.27 %, under the 1 % = 4.3 lm limit), named by room

| group | ours | freelancer | diff | cause / label |
|---|---|---|---|---|
| GF dry + pantry (he puts the pantry in 'reception + dining') | 119.10 | 127.13 | -8.03 | -3.90: he splits the entrance off as its own decor piece (14.76), counting the entrance / reception line twice: RULE_DIFFERENCE (decor-piece perimeter vs wall run); -4.13: his decor-piece outline of the open room is not printed, UNRESOLVED (< 1 %) |
| GF wet without pantry | 83.44 | 77.33 | +6.11 | wash lobby 12.56 vs 7.20 (niche 3.85 + opening 1.27 + angled walls); master bath 10.76 vs 7.50; 4 W.C.s 25.32 vs 27.90: UNRESOLVED per room, all < 1 % each |
| 1F dry | 115.39 | 122.82 | -7.43 | living 39.44 vs 43.78 (-4.34, his decor-piece outline is not printed); bedrooms 75.95 vs 79.04 (-3.09): UNRESOLVED, each < 1 % |
| 1F wet | 57.78 | 57.53 | +0.25 | agree (+0.4 %) |
| 2F dry | 40.90 | 32.90 | +8.00 | shaft-box top 13.00 that he does not ceil (T-147 own line: ENGINE_RIGHT if the stair hall takes the decor ceiling, Q-48 A no exception), lobby 9.00 vs his corridor 13.60 |
| 2F wet | 9.70 | 9.75 | -0.05 | agree |
| **total** | **426.31** | **427.46** | **-1.15** | -0.27 % |

## Rules, tests, repeat
- R-T788-1 cornice run, R-T788-2 perimeter partition, R-T788-3 room side only (outdoor pockets of a clip by ray enclosure test, their cuts OPEN_SIDE): `research/agents_t788/t788_rules.py` (every villa).
- Tests r2: `tests/t788/test_t788_room_side.py` (synthetic chamfered glazing: normal closed room inner face only; adverse clip pocket beyond the glazing adds 0; mirror, rotation; no barrier lines -> error, never assumed indoor).
- Tests: `tests/t788/test_t788_rules.py` (synthetic open plan, hand-calculated: normal, door gap, open side, mirror,
  rotation, clip sliver, mm units, missing ceiling type -> error never 0).
- Repeat: `research/agents_t788/t788_fill.py` header (private DXF faces only in .work/private; nothing private written).
- Not done: the cove / drop edges at slab openings (47.00 m, own HELD line) and the cornice profile (no detail printed)
  stay as they are; per-room residuals are below 1 % each and not re-measured further.
- Lessons-register proposal (r2, Checker): "leaking face + clip region: classify every clip cut on the drawing; a cut inside an outdoor pocket is not an opening" (scope every villa, source T-788 Checker).
- Lessons-register proposal (r1): "an open zone is not a missing run: measure the wall faces of every zone and drop only the
  sides with no wall" (scope every villa, source T-788).
