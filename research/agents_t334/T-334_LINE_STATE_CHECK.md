# T-334 LINE-STATE CONSISTENCY CHECK (export integrity; no quantity changed)

Tool: `tools/t334_line_state_check.py` (read-only, DEFAULT_GUARD_CLASS TOOLING, imported by nothing in engine/).
Tests: `tests/t334_line_state_check` (synthetic villa VG-334, not the development villa).

## 1. What the check ties together

A canonical line states its state four times: `evidence_state`, `measured_net`, `bounded_range` and the printed
`calculation.formula`. `engine/source/boq_line.validate` (boq_line.py:247-294) ties the state word to the presence of
`measured_net` only; nothing ties the formula text, the gross, or the range cause to the state. Kinds (REFUSED unless
marked): UNKNOWN_STATE, HELD_AS_ZERO, HELD_WITH_FIGURE, VALUED_WITH_HELD_TEXT, RANGE_WITHOUT_CAUSE, RANGE_EXCLUDES_NET,
SOURCE_NOT_NAMED, FORMULA_FIGURE_DISAGREES (FLAG: the formula's concluding figure in the line's own unit is not the
net, or lies outside the held range). Diagnostic, never refused: NOTE_OPEN_RFI_ON_VALUED (owner rule
URBAN-CEILING-QUANTITY-WITHOUT-MATERIAL publishes the area and holds the material). `check` exit 0 / 1 FLAG / 2 REFUSED;
`export` = the guarded export: check first, on any finding NOTHING written (exit 2), else `boq_export_v1.main`
unchanged (test: identical BOQ.csv / BOQ_ENGINE_UNITS.csv bytes).

## 2. Result on the candidate (own run, Python 3.11.18)

Drive 'Alsenan chalet project': P7757.dxf `ab54dd55` (P7757_DXF_COMPRESSED.zip) + 'ST7757 dxf.dxf' `9f9d1179`,
research/agents_t167/v304_run.py then research/agents_t315/v3021_run.py: **V3_0_21_BOQ_LINES.json `be22a4e4`** and
V3_0_20 `097a80b6` reproduced byte for byte.

V3.0.21: 3,706 lines, 3,340 OK, **366 findings: 351 REFUSED + 15 FLAG**; 5 notes. V3.0.20: 3,705 lines, 350 REFUSED +
15 FLAG (the HELD_WITH_FIGURE line is new in V3.0.21). Per family (V3_0_21_LINE_STATE_FINDINGS.csv, summary.json):

| Kind | Family / state | Lines | Quantity carried | Since |
|---|---|---|---|---|
| VALUED_WITH_HELD_TEXT | STR.REBAR kg SOURCE_DERIVED (beams 230 / 5,171.031 kg, ground beams + straps 88 / 1,252.907 kg, columns 32 / 1,887.128 kg) | 350 of 388 | **8,311.066 kg of 9,185.928 kg released (90.5 %) print `held: `** | V3.0.3 |
| HELD_WITH_FIGURE | FIN.SKIRTING lm NOT_APPLICABLE (L-af6fb2d3, GF-RC06FED) | 1 | gross 7.600 lm kept on a taken-off line | V3.0.21 |
| FORMULA_FIGURE_DISAGREES | FIN.PLASTER / FIN.PAINT m2 PROVISIONAL (1F_01, GF_15) | 2 + 2 | net 107.428 m2 per trade; formula concludes the gross (59.295 / 78.610 m2) | V3.0.9 |
| FORMULA_FIGURE_DISAGREES | FIN.PLASTER / FIN.PAINT m2 BOUNDED (1F_10, 1F_11, 1F_13, 2F_01, GF_08) | 5 + 5 | held 396.121 .. 433.181 m2 per trade; formula concludes the gross (sum 484.943 m2) outside the range | V3.0.9 |
| FORMULA_FIGURE_DISAGREES | ARCH.SPACE m2 BOUNDED (L-554a525e) | 1 | held 1.364 .. 1.364 m2; formula concludes 13.986 m2 = another element's area (the garden band) | V3.0.14 |

None found: HELD_AS_ZERO, RANGE_WITHOUT_CAUSE (1,083 bounded + 284 ranged quantity lines all name a basis and,
bounded, a question), RANGE_EXCLUDES_NET (284 / 284 nets inside their range), SOURCE_NOT_NAMED (661 SOURCE_DERIVED all
name a file + sha256), UNKNOWN_STATE. Notes: the 5 FIN.CEILING soffit lines (Q-68 C, finish held, area published).

Verifier's draw reproduced: L-1d50c1dc STR.REBAR 16.751 kg, SOURCE_DERIVED, formula `held: `, inputs count 4 x
length 2.65 m (CB11 span 2 bottom, 16 mm): 16.751 / 10.6 = 1.580 kg/m. On all 350 lines kg / (count x length_m) is the
bar mass of the line's diameter (12 mm 0.889, 14 mm 1.210, 16 mm 1.580, 18 mm 2.000, 20 mm 2.469 kg/m, to the
3-decimal rounding of the net): the QUANTITY agrees with its inputs; only the printed state text is wrong.

## 3. Cause of each kind (code path) and the fix for the lane I package (no line changed here)

1. VALUED_WITH_HELD_TEXT: `engine/source/arch_v303.py:235` (`ledger_record_line`): `formula=r.get("formula") or
   ("held: " + "; ".join(reasons))[:400]` is evaluated for every record; the T-138 r2 / T-148 / T-149 hand-ledger
   RELEASED records carry no `formula` and no reasons, so a released kg prints `held: ` (empty reasons). The same
   expression sits at arch_v302.py:272, arch_v305.py:210, arch_v307.py:324, arch_v308.py:306, arch_v309.py:290
   (latent: on V3.0.21 their released records carry a formula). FIX (new candidate version, never an edit of
   V3.0.3): for a RELEASED record write `count x length_m x <kg/m of the rebar rule table in force> = kg`, from the
   record's own inputs; the `held:` text only when the evidence state has no quantity.
2. HELD_WITH_FIGURE: `engine/source/arch_v3021.py:517-523` (base ownership, NOT_APPLICABLE branch) clears
   measured_net, bounded_range and rfi but not `gross`. FIX: gross None on a NOT_APPLICABLE line (the before-record
   in inputs.base_ownership_v3021 already keeps 7.6).
3. FORMULA_FIGURE_DISAGREES, plaster / paint: `research/agents_t211/t211_inputs.py:180` writes `... = <gross> m2,
   less N opening(s) ...` and stops; `arch_v309.py:290` prints it as the line formula. Two of the six valued lines
   were later suffixed `(net x m2)` by V3.0.20 and pass. FIX: end the formula with the net (`= net x m2`) or, held,
   with `net low .. high m2`. Same 18 faces as T-330 finding (1) (canonical deductions): one fill package can do both.
4. FORMULA_FIGURE_DISAGREES, ARCH.SPACE: `engine/source/arch_v3014.py:837` appends `HELD with <held_with>`, and the
   held_with text (research/agents_t240/t240_inputs.py:178) carries the garden band's own `= 13.986 m2`. FIX: name the
   other element without an `=` result, or put the line's own figure last.

## 4. Lessons-register row (proposed)

| 2026-10-29 | 350 released rebar lines (8,311.066 kg, 90.5 % of released kg) print `held: ` as their formula; a taken-off skirting line keeps its gross; 15 finish lines print the gross as their concluding figure (T-334) | each version writes its formula by a fallback `formula or "held: ..."` and nothing checked the printed text against the state word, the figure and the range | a line's state word, quantity, range and printed formula must agree; the hold text belongs only to a line without a quantity; a line taken off carries no figure; a formula ends with the line's own figure; the export refuses a disagreement (every villa) | tests/t334_line_state_check (normal: villa VG-334 clean; adverse: valued under 'held:', held as 0, gross on NOT_APPLICABLE, range without cause / excluding net, SOURCE_DERIVED without source, formula concluding the gross) | PROPOSED |

Verdict proposal: not a who-is-right item (export integrity; no quantity vs the freelancer changed).
