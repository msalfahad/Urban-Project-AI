# Control-plane Round 2: test run

**Full suite:** `python3 -m pytest -p no:cacheprovider -rfE --junitxml=…`, run from the repository root on the committed tree. Exit status 0, in 323.8 s.

| | Round 1 (`47dac56`) | Round 2 | Delta |
|---|---|---|---|
| Tests | 5,933 | 5,968 | +35 |
| Passed | 5,815 | 5,869 | +54 |
| Xfailed | 115 | 96 | −19 |
| Skipped | 3 | 3 | 0 (unchanged) |
| Failed / errors | 0 | 0 | 0 |
| Unexpected passes (XPASS) | 0 | 0 | 0 |

**Per suite:**

| Suite | Passed | Failed | Xfailed | Xpassed | Skipped |
|---|---|---|---|---|---|
| Control plane (`tests/alsenan_control_plane`) | 89 | 0 | 4 | 0 | 0 |
| Alsenan (`tests/alsenan`) | 304 | 0 | 0 | 0 | 0 |
| Qortuba RC1 (`tests/rc1`) | 37 | 0 | 0 | 0 | 0 |
| R8 (`tests/r8_*`) | 1,852 | 0 | 92 | 0 | 1 |

**Test files in the control plane:**
- **`test_control_plane_r2_engines.py`** — 35 passed. Covers the generic engines on synthetic input.
- **`test_control_plane_r2_gates.py`** — 37 tests: 33 passed and 4 xfailed with `strict=True`.
  - The xfails are G11, G13, G15 and G23. Each is Round 3 work or waits on an engineer's answer.
  - The file also holds the gates G01–G23, the terminal-record tests, the room-status mutation test, register-hash integrity, the benchmark firewall and the no-gaming checks.
- **`test_control_plane_r1.py`** — 21 passed. These are the frozen-data tests.
  - The 14 characterisation tests that pinned the now-fixed defects, and the 23 R1 gates, are removed.
  - `GATE_TRANSITION_REGISTER.superseded_round1_tests` lists each removed test with the one that replaces it.
