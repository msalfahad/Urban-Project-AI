# M1 - a usable structural BOQ (ST7757 demonstration)

M1 adds a **provisional estimating layer** beside the strict verified release. It does not discard S1 - S9A or
change them: every frozen stage manifest verifies before the estimate is built, and the verified release is exactly
S9's (158.070256 m3 / 18,845.961347 kg). The gate stays INCOMPLETE. Nothing here is engineering approval.

## The planning estimate

| | Verified | Provisional (base) | Planning low | **Planning base** | Planning high | Unresolved items |
|---|---:|---:|---:|---:|---:|---:|
| Reinforced concrete, m3 | 158.070 | 162.528 | 303.817 | **320.598** | 355.129 | 52 |
| Plain concrete (blinding), m3 | 0.000 | 9.975 | 9.975 | **9.975** | 9.975 | 1 |
| Reinforcement, kg | 18,846.0 | 6,020.6 | 24,533.4 | **24,866.6** | 24,968.7 | 33 |

- **Planning = verified + provisional base.** Each provisional item holds one reading as its base and the
  alternatives as its range; exclusive readings are never added together.
- **Low and high** add each item's own low and high. They are a bracket, not a probability.
- **Unresolved items are in no total.** That is 53 concrete items, 40
  of them with an indicative exposure of 15.7 to 34.4
  m3, and 33 reinforcement items with no bar model. The planning estimate is not complete.
- **Beams** (150 in S9A 05): 63.480 m3 under convention A (H includes the slab),
  79.288 m3 under convention B (H below the slab), difference
  15.808 m3. 27 spans are still unmeasurable. M1's base is A,
  and B is each beam's high end (`02_BEAM_CONVENTIONS.*`).

## Run it

```
python3 -I tools/urban_structural_boq.py run --drawings <ST.dxf> <ST.pdf> --out OUT [--set ID=VALUE ...]
python3 -I tools/urban_structural_boq.py run --drawings NEW.dxf --profile NEW_PROFILE.json --out OUT
python3 -I tools/urban_structural_boq.py inventory --drawings NEW.dxf --out OUT   # writes PROFILE_TEMPLATE.json
python3 -I research/alsenan_m1_usable_boq/build_m1.py                             # this package
```

`--set` changes one assumption, for example `--set BEAM_DEPTH_READING=BELOW_SLAB` or `--set FOUNDING_DEPTH_M=2.0`.
The estimate, the workbook and the PDF are regenerated, and the change is recorded in `SUMMARY.json`.

## Contents

| File | What |
|---|---|
| `conventions_alsenan.json` | Every assumption: base, alternatives, provenance, source, rationale |
| `alsenan_adapter.py` | The frozen S1 - S9A registers as VERIFIED / PROVISIONAL / UNRESOLVED items (route A) |
| `boq/` | The one-command run on ST7757: `VERIFIED_` / `PROVISIONAL_` / `UNRESOLVED_REGISTER.csv`, `CONTRACTOR_BOQ.csv`, `FAMILY_` / `FLOOR_SUMMARY.csv`, `STEEL_BY_DIAMETER.csv`, `SENSITIVITY.csv`, `BLOCKERS.csv`, `EXCEPTIONS.csv`, `COVERAGE.csv`, `ASSUMPTIONS.csv`, `INVENTORY.json`, `BOQ_REPORT.html`. Also `STRUCTURAL_BOQ.xlsx` and `BOQ_REPORT.pdf`, which are git-ignored |
| `01_BOTTLENECK_DIAGNOSIS.md` / `.json` | Measured, convention-blocked, incomplete, undetected, approval-only; the five biggest causes |
| `02_BEAM_CONVENTIONS.csv` / `.json` | Beam totals under A and B, the gaps with their reasons, overlap and ownership |
| `03_LAYER_DETECTION.csv` | Every drawing layer and whether any stage reads it |
| `04_AUTOMATION_AUDIT.csv` | Which pipeline steps run on a new villa |
| `05_USABILITY.json` | Coverage, completeness by family, verified vs provisional, unresolved, the new-villa answer |
| `06_M1_FREEZE_MANIFEST.json` | sha256 of the code, the inputs and every frozen output |
| `post_freeze/` | The external-estimate reconciliation, written after the freeze |

## Limits

- **Route A replays; it does not re-measure.** It runs on the frozen stage registers of this drawing, so it is not
  evidence that the extraction generalises.
- **New villas are only partly covered.** Route B measures footings and columns live, once a person confirms a
  profile. Every other family comes out UNRESOLVED (`05_USABILITY.json`).
- **No blind test on a second villa.** No permitted dataset exists, so no accuracy figure is claimed.
- **Steel ranges are narrow** wherever a frozen bar model exists. The model is taken as is: laps, anchorages and
  starters follow its printed rules, and only the hook allowance is varied.
