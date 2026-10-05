# Round 5 — test run record

## Full suite

Command:

```
python3 -m pytest -p no:cacheprovider -rfE -q --junitxml=<scratch>/r5_full.xml
```

Run against the working tree that became commit `8f44252`.

Result: exit code 0 — **6,015 passed, 100 xfailed, 3 skipped, 0 failed, 0 errors**.

This equals the previous baseline plus the new Round 5 tests:

| | Passed | XFAIL | Skipped |
|---|---|---|---|
| Previous baseline | 5,961 | 98 | 3 |
| Round 5 | +54 | +2 | – |
| Total | 6,015 | 100 | 3 |

## Per suite (JUnit classname)

| Suite | Passed | XFAIL | Skipped |
|---|---|---|---|
| R5 architectural (`tests/alsenan_arch_truth`) | 54 | 2 (strict: GF-Z04 wash zone, 1F W.C) | 0 |
| R8 | 1,852 | 92 | 1 |
| Qortuba (classname match) | 289 | 0 | 0 |
| Alsenan (`tests/alsenan`) | 304 | 0 | 0 |
| Control plane | 91 | 2 | 0 |
| Rebar R3 | 46 | 2 | 0 |
| Rebar R4 | 44 | 2 | 0 |
| Other | 3,335 | 0 | 2 |

## Regression
- R8, Alsenan, control, rebar R3 and rebar R4 counts are unchanged.
- The Qortuba and other suites are unchanged in total (the suite total moved only by the Round 5 additions).
- Rebar R3 and R4 INDEX hashes are unchanged (`test_rebar_untouched`).
