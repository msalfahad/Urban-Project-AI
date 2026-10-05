# Round 4: test run

## Commands

| Step | Command | Result |
|---|---|---|
| Evidence capture | `python3 research/alsenan_rebar_source_exhaustion_04/capture_visual_evidence.py` | 29 crops: hash, OCR (tesseract 5.3.4, ara+eng), vector geometry. The crops stay git-ignored. |
| Build | `PYTHONPATH=.:research/external_engine_lab python3 research/alsenan_rebar_source_exhaustion_04/build_rebar_v4.py <ctx.pkl> --twice` | 16 registers + INDEX.json. Bytes are identical on both builds, and a later rebuild gives the same INDEX. |
| Post-freeze | `python3 research/alsenan_rebar_source_exhaustion_04/post_freeze_rebar_comparison.py` | INDEX hashes are verified first; the result is FINDING_ONLY. |
| New suite | `python3 -m pytest tests/alsenan_rebar_source_exhaustion -q` | 44 passed, 2 xfailed |
| Full suite | `python3 -m pytest -p no:cacheprovider -rfE -q --junitxml=...` | 5,961 passed, 98 xfailed, 3 skipped, 0 failed |

## Per suite (from the JUnit XML of the full run)

| Suite | Passed | XFAIL | Skipped | Failed |
|---|---|---|---|---|
| `tests/alsenan_rebar_source_exhaustion` (new) | 44 | 2 (G15, G23) | 0 | 0 |
| `tests/alsenan_rebar_truth` (R3) | 46 | 2 | 0 | 0 |
| `tests/alsenan_control_plane` | 91 | 2 | 0 | 0 |
| `tests/alsenan` | 304 | 0 | 0 | 0 |
| R8 (`tests/r8_*`) | 1,852 | 92 | 1 | 0 |
| Qortuba RC1 + PA08 | 317 | 0 | 0 | 0 |
| Everything else | 3,307 | 0 | 2 | 0 |
| **Total** | **5,961** | **98** | **3** | **0** |

**Against Round 3** (5,917 passed, 96 xfailed, 3 skipped), the change is +44 passed and +2 xfailed. These come from the 44 new tests and the two new strict XFAILs (G15, G23). Every other suite is unchanged.

**Engine fix found by the new tests:** `visual_source_claim.validate` now derives the expected authority from the *derived* state. Before, it used the stored state, so a hand-edited state + authority pair passed. The registers are unchanged by this fix (the rebuild gives an identical INDEX).

## Gates

- **PASS:** G11, G13, G32–G42.
- **XFAIL (strict):**
  - G15 (ground-slab scope, Q-S4)
  - G23 (stair applicability, Q-R3-10)
