# S6 test run

**Targeted (at `0dea403`).**

```
python3 -m pytest -q -p no:cacheprovider tests/superstructure_beam_rebar_s6 tests/pre_s6_superstructure_beam \
    tests/ground_system_rebar_s5 tests/footing_rebar_s4 tests/structural_comparison_engine/test_rebar_product_firewall.py
```

gave **216 passed**. The S4, S5 and S6 freeze-manifest tests are among them and all still match.

- `tests/superstructure_beam_rebar_s6/test_superstructure_beam_rebar_engine.py`: 31 synthetic cases covering the
  S6 brief section 31 list - simple top / bottom bars (never merged by diameter), blocked and candidate simple
  beams, CB ordered / reversed / bidirectional readings, candidate-invariant release and candidate-different block
  (no averaging), one bar run across a support (duplicates and splits refused), MID 0.22 x Ln from the face, the
  drawing's own Ln definition, edited and empty MID cells, the 7.5 cm extension only on its bound bar role,
  unresolved 0.15L and 0.3 Ln2, hangers blocked, T/M never steel, width conflicts (geometry and mark unchanged),
  stirrup count lower bound with no +1, stirrup kg blocked, side-bar text kept with kg blocked, no opening /
  a real synthetic opening (through the PRE-S6 classifier), untagged geometry conserved, development and hooks
  blocked (no code default in the engine), D^2/162 and kg tampering, mass conservation, provenance.
- `tests/superstructure_beam_rebar_s6/test_alsenan_s6_package.py`: 17 package checks - freeze manifest, blind
  builder, byte-identical rebuild, population and frozen scope (71 / 18, 7 / 6), never wider than PRE-S6, golden
  B1 / CB11 / CB9 values re-derived from PRE-S6, CB7 invariant / CB13 different, totals equal an independent sum of
  the PRE-S6 READY runs, T/M excluded, blocked components kept with no kg, width conflicts, CB3 / CB8 MID cells,
  83 stirrup counts with no +1, 39 side-bar texts, object / tag / untagged conservation, provenance.
- `tests/superstructure_beam_rebar_s6/test_s6_post_freeze.py`: 2 checks - the comparison runs only after the freeze,
  is downstream only, uses the brief's classes and leaves no UNKNOWN.
- The RF.1 firewall test covers the S6 engine, builder and comparison script (registry extended).

**Full suite at `0dea403`.** `python3 -m pytest -o addopts="" -q -p no:cacheprovider` gave
**6601 passed, 4 skipped, 100 xfailed, 2 warnings in 395.36 s, exit 0** - PRE-S6's 6551 plus the 50 new S6 tests.
The run used the clean committed tree; no file was edited during it.
