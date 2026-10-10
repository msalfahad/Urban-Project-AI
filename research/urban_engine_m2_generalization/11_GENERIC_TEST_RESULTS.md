# Generic extraction test results (synthetic villas with independent truth)

## Protocol

**How each drawing is generated.**
- `tools/synthetic_villa.py` draws a villa from a seeded design: a grid, two column types, three beam types, two footing types, two slab storeys, schedules as attribute rows and a curved beam.
- It writes **truth from the design**: quantities and component positions, computed analytically.
- The generator imports no engine module; a test enforces this. Its hook and link formulas are re-derived independently, with no shared code.

**Variants per seed.**
- Units mm / m; titles EN / AR; three layer-name sets and two schedule tag sets.
- Rotated and mirrored column block inserts; combined C/F footing marks.
- An untagged span on a tagged line; a beam drawn narrower than scheduled; a beam type missing from the schedule; a curved beam; an opening bay with a VOID label and an X.

**`--defects` (truth unchanged):**
- faces broken into pieces; duplicated lines;
- face ends stopping 0.5–2 mm short of, or running 2–20 mm into, the column;
- footings as loose lines; grid axes with bubbles; linear dimensions;
- MTEXT tags with formatting codes; tags pushed off the face; solid hatches in columns.

**`--hard-defects`:** as `--defects`, but the end gaps are 6–15 mm, beyond the 5 mm snap. The question is whether any loss is **reported** (coverage risk) or **silent**.

**Protocol.**
- Development used seeds 1–6 only.
- Each held-out set was run **once**, on the commit named in its file name, and recorded untouched.
- After any engine change, a **fresh** seed range was used: sets 1, 2, 3 and 4 never re-use seeds.

## Results (`evaluation/*.json`)

Detection columns are recall / precision. Quantity error is the maximum over the families: footings, columns, beams (total depth), beams (below slab), slabs, footing steel, column main steel and beam steel.

| run | end to end | max abs quantity error | footings | beams | slab panels | silent slab loss m² | max high / base | s / drawing |
|---|---|---|---|---|---|---|---|---|
| `dev_1-6_clean_at_938b0d1` | 6/6 | < 5e-7 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 0.0 | not measured | 0.165 |
| `dev_1-6_defects_at_938b0d1` | 6/6 | < 5e-7 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 0.0 | not measured | 0.2 |
| `dev_1-6_hard_at_938b0d1` | 6/6 | < 5e-7 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 0.0 | not measured | 0.214 |
| `heldout_set1_101-110_clean_at_69f6d8c` | 10/10 | < 5e-7 | 1.000 / 1.000 | 1.000 / 0.979 | 1.000 / 1.000 | not measured | not measured | 0.178 |
| `heldout_set2_201-220_clean_at_2b92e25` | 20/20 | < 5e-7 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | not measured | not measured | 0.18 |
| `heldout_set2_201-220_defects_at_2b92e25` | 20/20 | < 5e-7 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | not measured | not measured | 0.228 |
| `heldout_set3_301-320_clean_at_938b0d1` | 20/20 | < 5e-7 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 0.0 | not measured | 0.153 |
| `heldout_set3_301-320_defects_at_938b0d1` | 20/20 | < 5e-7 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 0.0 | not measured | 0.197 |
| `heldout_set3_301-320_hard_at_938b0d1` | 20/20 | < 5e-7 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 0.0 | not measured | 0.198 |
| `heldout_set4_401-420_clean_at_d23fe92` | 20/20 | < 5e-7 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 0.0 | 1.4 | 0.137 |
| `heldout_set4_401-420_defects_at_d23fe92` | 20/20 | < 5e-7 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 0.0 | 1.4 | 0.21 |
| `heldout_set4_401-420_hard_at_d23fe92` | 20/20 | < 5e-7 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 0.0 | 1.4 | 0.196 |

**Notes**
- Errors are rounded to 6 decimals in the summaries: "< 5e-7" means every family of every drawing is within 0.00005 % of truth.
- Set 1's beam precision of 0.979 is a truth-list omission, not an engine error: the curved beam's position was missing from the generator's component list, although its quantity was in the truth. It was fixed in 2b92e25; sets 2 to 4 include it.
- The *max high / base* of 1.4 is the beam below-slab depth alternative (a named convention), not a polluted range. The metric was added in d23fe92, after a footing outline had inflated a column high bound in the synthetic demo.

## What the defect sets found (all fixed, all with regression tests)

| found by | defect | effect before the fix | fix |
|---|---|---|---|
| defects, dev seed 3 | intake keyed block-layer inheritance by hex handle, while the kernel's ids are decimal | a column block's outline inherited the dimension layer, and slab cells were lost | `_insert_layers` keys by decimal id (2b92e25) |
| defects, dev seeds 1–6 | 0.5–2 mm gaps at beam / column junctions | slab panel recall 0.19, slab error up to 100 % | `cad_heal` merge + snap (2b92e25) |
| hard defects, dev seeds | gaps beyond the snap | 413 m² of slab silently missing over 6 drawings | wide snap (reported) + unenclosed band-side check (938b0d1) |
| geometry fixture | any ELLIPSE crashed the intake (wrong attribute names) | whole drawing refused | ellipse fields (a92ded1) |
| component test | an Arabic "schedule of footings" title read as a foundation plan | wrong sheet role | a title opening with a schedule word is a schedule (a92ded1) |
| synthetic demo (Excel) | a column bound to its footing outline (the combined mark sits in the footing) | column high bound about 25× its base | columns never bind to footing outlines (d23fe92) |

## What this does and does not show

- **It shows:** the generic route works on drawings it has never seen. It survives the listed drafting noise. It loses nothing silently in the stress case, and it is deterministic and fast (0.14–0.23 s per drawing).
- **It does not show:** accuracy on real drawings from other draftsmen. The generator encodes one author's idea of a structural drawing. Real offices differ in ways not modelled here: schedules as exploded lines, beams drawn as single centrelines, beam depths printed on the plan, polyline-width walls, xrefs and many more. The only real villa available is Alsenan; see `04_ALSENAN_GENERIC_VS_FROZEN.md`.
