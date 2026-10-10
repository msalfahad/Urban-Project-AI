# PRE-S6 test run

**Targeted (at `524453a`).**

```
python3 -m pytest -o addopts="" -p no:cacheprovider -q tests/pre_s6_superstructure_beam \
    tests/structural_comparison_engine/test_rebar_product_firewall.py tests/ground_system_rebar_s5 \
    tests/footing_rebar_s4 tests/pre_s5_1_source_resolution tests/pre_s5_ground_system tests/alsenan_structural_census
```

gave **289 passed**. The S4 and S5 freeze-manifest tests are among them and still match.

- `tests/pre_s6_superstructure_beam/test_beam_rebar_readiness.py`: 38 synthetic cases.
  - **Binding:** simple binding; every alternative is returned; distance never ranks; text rotation alone never
    verifies; the width gate; same-mark continuity gives only a candidate; tag without band; a span claimed by
    another mark.
  - **Width and terminals:** width states; a width conflict keeps the binding; duplicate tag and band without tag;
    two marks on one span; conservation, including duplicate and invalid terminals.
  - **CB spans:** forward, reversed and ambiguous reading directions; physical total differs from the schedule total
    and both are kept; span-count conflict.
  - **CB bar runs:** a bar crossing two supports is one run; a bottom extension needs a bound rule; MID is released
    with a bound rule; MID with a known count and unknown length stays BLOCKED_UNQUANTIFIED; an empty cell never
    releases; top bars stay blocked; an unresolved rule is never applied.
  - **Simple bar runs:** face-to-face run and the S5 principle; geometry conflict; pattern-only authority; a
    candidate is PROVISIONAL_ONLY.
  - **Other components:** candidate-invariant and candidate-different; hanger absent or unlabelled; side-bar
    '/30cm' not interpreted; stirrup count known with the path blocked; opening absent and present.
  - **Rules and provenance:** dimension binding by defpoints; generic provenance (CB needs BAR_RUN_ID, no
    FOOTING_*); slab rules never borrowed.
- `tests/pre_s6_superstructure_beam/test_pre_s6_package.py`: 26 package checks.
  - **Integrity:** INDEX hashes; byte-identical rebuild; every object terminates once; 146 S1 rows mapped; tags and
    spans reconcile; silently dropped spans now terminate.
  - **Binding:** all alternatives listed; rotation-only alternatives leave a candidate; S1 changes listed;
    candidates never release.
  - **Schedule semantics:** width conflicts; CB span conflicts keep both values; CB9 read in reverse; conflicted CB
    never releases; T/M is NOT_REBAR; SBT fields are not collapsed; token terminals.
  - **Bar runs and components:** MID needs a count and a bound rule; one run per CB bar; straight run kept while
    development is blocked; never-released families; stirrup counts are lower bounds only; untagged geometry.
  - **Package-level:** no beam opening; provenance covers exactly the released components; no kg; the builder is
    blind; RESTRICTED GO.
- The firewall test (30 cases) covers the new module and builder.

**Full suite at `524453a`.** `python3 -m pytest -o addopts="" -q -p no:cacheprovider` gave
**6551 passed, 4 skipped, 100 xfailed, 2 warnings in 319.40 s, exit 0**. That is S5's 6487 plus the 64 new
PRE-S6 tests. The run used the clean committed tree; no file was edited during it.
