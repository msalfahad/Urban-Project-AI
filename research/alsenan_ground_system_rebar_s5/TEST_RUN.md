# S5 test run

**Targeted (at the freeze, `627c823`).** `python3 -m pytest -o addopts="" -q tests/ground_system_rebar_s5 tests/structural_comparison_engine/test_rebar_product_firewall.py tests/footing_rebar_s4 tests/pre_s5_1_source_resolution tests/pre_s5_ground_system`
gave 163 passed.

- `tests/ground_system_rebar_s5/test_ground_system_rebar_engine.py`: 23 synthetic engine cases. They cover:
  - spans of >5 m, <5 m and <2.5 m, and exterior spans;
  - candidate details that are identical and that differ;
  - a concentrated load that is unknown, and an unknown depth with the longitudinal steel still released;
  - a known stirrup count with the stirrup mass blocked, and two distinct lower rows;
  - the support-face run, and a bar-run conflict;
  - a free end left unresolved;
  - SB1, SB2 and SB3 analogues;
  - development and hooks blocked, with no default accepted;
  - contract mutations and conservation mutations;
  - the rough-engine firewall.
- `tests/ground_system_rebar_s5/test_alsenan_s5_package.py`: the freeze manifest still matches; the builder is blind; a rebuild is byte-identical. The package tests also check:
  - population 59 / 3, and the frozen scope 31 / 28;
  - no widening beyond PRE-S5.1;
  - SB1, SB3 and one explicit-span golden value, re-derived from the source;
  - the SB2 conflict, and the depth never being given a value;
  - <2.5 m spans with no stirrup;
  - the 1811-1812 end, and development and hooks blocked everywhere;
  - conservation and provenance;
  - the split views;
  - the comparison running downstream only.

**Post-comparison (`b7d0807`).** S5 + firewall: 70 passed.

**Full suite at `b7d0807`.** `python3 -m pytest -o addopts="" -q -p no:cacheprovider` gave
**6487 passed, 4 skipped, 100 xfailed, 2 warnings in 300.79 s, exit 0**.

An earlier full run returned 6486 passed with exit 1. The determinism guard had flagged
`tests/ground_system_rebar_s5/test_alsenan_s5_package.py`, which I edited while that run was in progress. That was not a test failure. The run above is on the clean committed tree.
