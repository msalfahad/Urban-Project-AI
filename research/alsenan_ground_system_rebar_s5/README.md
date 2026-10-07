# S5: Alsenan accurate ground-system rebar (ground beams and strap beams)

**KNOWN SOURCE-DERIVED GROUND-SYSTEM REBAR: 1,458.0 kg (lower bound).**
**FINAL GROUND-SYSTEM REBAR NOT ESTABLISHED.**

```
python3 -I research/alsenan_ground_system_rebar_s5/build_ground_system_rebar_s5.py
```

The package was built blind and frozen before any reference was opened (`S5_FREEZE_MANIFEST.json`, state
`FROZEN_BEFORE_REFERENCE_COMPARISON`). The engine is the generic `engine/source/ground_system_rebar.py`. The builder
reads only these frozen registers:

- the PRE-S5.1 package, checked against its INDEX hashes;
- the PRE-S5 strap registers;
- the R4 p.13 claims and the rule register.

It never reads a drawing.

## Results

| Family | Occurrences | Lower bound | Blocked | Known kg (LB) | Straight length | Stirrup counts | Blocked components |
|---|---|---|---|---|---|---|---|
| GROUND_BEAM | 59 | 31 | 28 | 1,238.56 | 842.74 m | 25 spans, ≥ 587 links | 716 |
| STRAP_BEAM | 3 | 2 (SB1, SB3) | 1 (SB2) | 219.43 | 119.38 m | 3 straps, ≥ 76 links | 23 |

There is no VERIFIED, PROVISIONAL or BLOCKED_MODELLED kg.

Mass by diameter:

| Diameter | Mass |
|---|---|
| Ø14 | 304.38 kg |
| Ø16 | 1,006.94 kg |
| Ø18 | 146.68 kg |

## Rules applied

- **Longitudinal steel.** Every longitudinal bar is `n × BAR_STRAIGHT_RUN_LOWER_BOUND × D²/162`, taken from the PRE-S5.1 length register.
  - It never uses the centreline length, the clear length, `min(clear, centreline)` or the member length.
  - The two lower rows of a ground beam stay separate components.
- **Development, hooks and stirrup mass.** Development and anchorage, bar-end hooks, stirrup hooks and the stirrup mass (core path) are BLOCKED_UNQUANTIFIED for every member.
  - No 40D, 70D, ACI, BS, EC2, Kuwait-practice or Urban default is used.
  - The 70Ø / 40Ø starter note is not generalised.
- **Stirrup records.** Stirrup diameter and spacing are attribute records. The stirrup count is a COUNT record: the lower bound `ceil(rate × run)`, with no +1 end bar. Neither record carries kg.
- **Candidate details.** Candidates are never chosen between.
  - A component releases only when every candidate detail defines it identically (CANDIDATE_INVARIANT).
  - An undefined candidate blocks the component. One example is the concentrated-load case, which has no project detail.
- **Exterior depth and side bars.** The exterior depth is never given a value: D ≤ 1.00 m is only an upper bound, and the annex bound D ≤ 0.30 m is a SOURCE_CONFLICT. Exterior side bars therefore stay blocked.
- **No widening.** S5 releases nothing that PRE-S5.1 did not mark READY. The builder checks this and stops if it would.

## Outputs

`GROUND_SYSTEM_REBAR_OCCURRENCES.csv`, `_COMPONENTS.csv`, `GROUND_SYSTEM_BBS_NET.csv`, `_RELEASE_SUMMARY.json`,
`_UNRESOLVED.csv`, `_PROVENANCE.jsonl` (one record per component, generic ELEMENT_* identity),
`GROUND_SYSTEM_ENGINEERING_FLAGS.csv`, `GROUND_SYSTEM_ENGINEERING_QUESTIONS.csv` (Q1–Q10 + Q3B),
`GROUND_BEAM_REBAR_SUMMARY.csv`, `STRAP_BEAM_REBAR_SUMMARY.csv`, `GROUND_SYSTEM_REBAR_OCCURRENCE_REGISTER.json`.

## Post-freeze comparison

The comparison runs in `post_freeze_comparison.py`, which writes its output to `post_freeze/`. It refuses to run
unless the manifest still matches.
