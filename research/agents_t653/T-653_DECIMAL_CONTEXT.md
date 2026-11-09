# T-653: no process-global Decimal precision in merged research modules (F-T648-2)

Defect: 17 research modules set `getcontext().prec = 40` at import and the S6 review script `eval_fixtures.py` set 50.
Whichever was imported last changed every later Decimal result in the same process: in one pytest session with
t645 / t646 before t647 / t649, `t647::test_outputs_current` and `t649::test_training_villa_is_the_committed_rebuild`
fail (reproduced on the base 2e80c03f: 2 F; 0 F after this change, both orders).

Change (no quantity moves; method R-T653-1):
- each of the 17 modules: the import-time assignment is replaced by `ctx40()` (a local `Context(prec=40)`, the T-648 r2
  pattern) and `in_prec40(globals())` at the end of the module, which runs every plain function DEFINED in the module
  inside that local context (generators, classes and imported names untouched; each wrapper is marked
  `_t653_prec40`);
- each of their 16 builders (`*_alsenan.py`; t598_alsenan has no Decimal arithmetic) calls `R.in_prec40(globals())`:
  their own arithmetic ran at 40 before only through the rules import, and now runs at 40 explicitly;
- `eval_fixtures.py`: the one 50-digit expression moved into `exact_length()` under a local `Context(prec=50)`; the
  review package `SHA256SUMS.txt` line for that script updated to the new file hash (no other line).

Evidence (`t653_rebuild.py`, each builder in its own fresh process, default prec 28 and adverse prec 6 set before the
import): `out/T653_LEDGER_BEFORE_2e80c03f.json` vs `out/T653_LEDGER_AFTER.json`: 23 outputs, every sha256 identical in
both modes; every output with a public committed file equals it (t559 / t568 freelancer tables need private inputs and
are compared before / after only); the global precision after each build is now the caller's own (28 / 6; it was 40 /
50).

Finding F-T653-1 (not changed, outside the file list): `research/agents_t627/t627_alsenan.py` sets no context and
computed at 40 only through `t568_alsenan`'s import side effect. At the default context its JSON / MD are
byte-identical; with a caller at prec 6 its own arithmetic raises InvalidOperation. Fix row proposal: give t627 the same
local context (one line), every villa.

Lessons-register row (ERS s.7) proposed: "Module-level `getcontext().prec = n` in research code (T-543 .. T-646, S6
review) made results depend on import order (F-T648-2, T-653). Rule: no process-global numeric state; a module that
needs more digits uses a local context inside its own functions; guard `tests/t653` scans research/, engine/, tools/."
