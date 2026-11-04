# T-495 Outdoor floor finish-HELD material rows (tile purchase ledger V2)

Tool: `research/agents_t495/t495_finish_held_ledger.py` -> `out/TILE_PURCHASE_LEDGER_V2.{json,csv}`. Ledger V2 =
the T-455 ledger (URBAN_T455_TILE_PURCHASE_V1, files untouched, reproduced on this input) + finish-held outdoor rows +
a scope guard. FINISH_MATERIALS_TABLE_V4 / V1 are called, never edited. No candidate, released or registry line moves.

## Finding addressed (F-C-T455-1)

EXT.FLOOR.OUTDOOR carries two HELD lines (finish undecided, area measured) that sat outside the T-455 ledger scope, so
no adhesive / bed bound named them. Every other floor-surface code was in scope or, for the court interlock, unnamed.

## Physical element and rules

An outdoor floor whose area is drawn but whose finish is one of several the sources allow. Its materials depend on the
finish, so each option is its own HELD row with its own bound; options are never summed (one floor, one finish).

| Rule | What it does |
|---|---|
| R-T495-1 SCOPE | every FIN.FLOOR.* (not the beds FIN.FLOOR.BED.*), EXT.FLOOR.*, EXT.PAVING.* line is in the ledger or DECLARED_OUT with its reason; a new code, or a HELD line of a declared-out code, fails |
| R-T495-2 OPTIONS | only finish options a source names, with the source; never added or picked by the agent |
| R-T495-3 BOUND | porcelain / ceramic adhesive area_low / 5 .. area_high / 3 bags (UPC-ADHESIVE-001, size not given); stone adhesive HELD (Q-45); bed Q-45 B regular floor 0.03 .. 0.04 m 1:4 +5 %, 8 bags cement + 1.1 m3 sand per m3 (PROVISIONAL); timber / interlock: no owner rule, HELD, no bound, never 0 |
| R-T495-4 AREA | the candidate's held range copied, not re-measured; evidence UNKNOWN (no VERIFIED_WHOLE binding) |

## Training villa (V3.0.46 index = V3.0.47 floor lines; T-443 moved FIN.SKIRTING only)

| Line | Area m2 | Option (source) | Adhesive 20 kg bags | Bed mortar m3 | Cement 50 kg | Sand m3 |
|---|---|---|---|---|---|---|
| GF porch L-dd6e3728 | 10.6785 | timber (owner 20:45) | HELD, no rule | HELD | HELD | HELD |
| | | porcelain / ceramic (owner 20:45) | 2.1357 .. 3.5595 | 0.3364 .. 0.4485 | 2.691 .. 3.588 | 0.370 .. 0.493 |
| | | marble with the stairs (owner 20:45) | HELD (Q-45 stone) | 0.3364 .. 0.4485 | 2.691 .. 3.588 | 0.370 .. 0.493 |
| Pool deck L-1c51d1e7 | 6.548912 | interlock (OD-1 frame) | HELD, no rule | HELD | HELD | HELD |
| | | porcelain / ceramic (OD-1 frame) | 1.3098 .. 2.1830 | 0.2063 .. 0.2751 | 1.650 .. 2.200 | 0.227 .. 0.303 |

If both lines are porcelain: 17.227412 m2 -> 3.445 .. 5.742 adhesive bags, 0.543 .. 0.724 m3 mortar. Every figure is
a BOUND under a HELD finish. Marble bed: the porch is a floor at court level (owner 23:20), so the Q-45 regular-floor
bed is used; the Q-45 stair bed (3 cm 1:3, cement / sand HELD) is the stair value, not this floor's.

Scope census on the candidate: FIN.FLOOR.PORCELAIN 35, WET_TILE 20, FINISH_HELD 3, EXT.FLOOR.PORCELAIN 1 (T-455 scope),
EXT.FLOOR.OUTDOOR 2 (finish-held rows), EXT.PAVING.INTERLOCK 1 DECLARED_OUT (no paver / sand-bed rule): 0 gaps.

## Verdict proposal, missing, lesson

NOT COMPARED (freelancer has no adhesive / bed line for porch or deck; his yard row has no pool deck). Missing: the
owner's porch and deck finish (OD-1, already with the owner; not re-asked), tile size, interlock / timber material
rules. Lesson (s.7 proposal): "a HELD finish is a set of sourced options, each bounded by its own rules; a material
ledger's scope is guarded by item-code family, so a new held floor line fails loudly instead of falling outside".
Tests: tests/t495_finish_held_ledger (fixture villa P495 by hand: equal and unequal held ranges, open range; adverse:
new held outdoor code, held declared-out line, invented option, unsourced line, released or wrong-unit line).
