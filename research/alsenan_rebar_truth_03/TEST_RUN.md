# Round 3: test run

## Commands

| Step | Command | Result |
|---|---|---|
| Build | `python3 research/alsenan_rebar_truth_03/build_rebar_v3.py --twice` | 12 registers + INDEX.json + bar-by-bar audit, identical bytes on both builds |
| Post-freeze benchmark | `python3 research/alsenan_rebar_truth_03/post_freeze_rebar_compare.py` | INDEX hashes verified first; FINDING_ONLY |
| New suite | `python3 -m pytest tests/alsenan_rebar_truth -q` | 46 passed, 2 xfailed |
| Full suite | `python3 -m pytest -p no:cacheprovider -rfE` | 5,917 passed, 96 xfailed, 3 skipped, 0 failed (310 s) |

## Per suite (from the JUnit XML of the full run)

| Suite | Passed | XFAIL | Skipped | Failed |
|---|---|---|---|---|
| `tests/alsenan_rebar_truth` (new) | 46 | 2 (G15, G23) | 0 | 0 |
| `tests/alsenan_control_plane` | 91 | 2 | 0 | 0 |
| `tests/alsenan` (frozen V3 / V3b / R1) | 304 | 0 | 0 | 0 |
| R8 (`tests/r8_*`) | 1,852 | 92 | 1 | 0 |
| Qortuba RC1 (`tests/rc1`) | 28 | 0 | 0 | 0 |
| Qortuba PA08 (`tests/test_pa08_qortuba*`) | 289 | 0 | 0 | 0 |
| Everything else | 3,307 | 0 | 2 | 0 |
| **Total** | **5,917** | **96** | **3** | **0** |

**Against the Round-2 baseline** (5,869 passed, 96 xfailed, 3 skipped): +48 passed. That is 46 new rebar tests, plus G11 and G13 moving from XFAIL to PASS in the control plane. The two new strict XFAILs (G15 and G23 in the R3 suite) replace them, so the xfail total is unchanged.

## Gates

- **PASS:** G11, G13, G24–G31.
- **XFAIL (strict):** G15 (ground-slab scope, Q-S4) and G23 (stairs, Q-R3-10).
