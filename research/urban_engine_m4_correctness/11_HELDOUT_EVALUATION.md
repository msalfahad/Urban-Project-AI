# Held-out evaluation: M3 engine vs M4 engine on unseen synthetic villas

The numbers come from `11_HELDOUT_EVALUATION.json`, written by `evaluate_heldout_m4.py score` with one process per engine.

**Drawings**
- 40 new layouts, seeds 601–640. No earlier stage used these seeds.
- **clean:** the generator's design, drawn as in M2 / M3.
- **m4:** the same design with the M4 source cases from `tools/synthetic_villa.py` (`m4=True`):
  - on odd seeds, the untagged span on line 0 is a different beam of the same width, 0.10 deeper, scheduled but unlabelled;
  - line 1 is a continuous beam, CB1, labelled on its first span only, whose schedule row prints the span sequence;
  - on seeds 2 and 3 mod 4 with three or more spans, a different beam, 0.20 deeper and unlabelled, continues the line past the printed spans.

**Truth**
- Truth comes from the design, never from the DXF.

**Engines**
- **M3:** commit `cbfa13e`, from a separate worktree, conventions V2.
- **M4:** frozen commit `35c0587`, conventions V3.
- Nothing was tuned to these drawings: the M4 rules were frozen before the set was generated.

| Set | Engine | End to end | Beam base MAE (max) | Unlabelled spans: correct / wrong / held | Precision / recall | CB concrete MAE | Truth inside base … base + exposure | Unresolved items |
|---|---|---|---|---|---|---|---|---|
| clean | M3 | 40 / 40 | 0.22 % (8.9 %) | – | – | – | 39 / 40 | 82 |
| clean | M4 | 40 / 40 | 6.1 % (14.1 %) | – | – | – | 39 / 40 | 162 |
| m4 | M3 | 40 / 40 | 1.2 % (8.6 %) | 168 / **72** / 0 | 0.70 / 0.70 | **16.8 %** | **13 / 40** | 82 |
| m4 | M4 | 40 / 40 | 9.1 % (18.0 %) | 128 / **0** / 112 | **1.00** / 0.53 | **0 %** | **39 / 40** | 402 |

Footing, column and slab concrete errors are 0 for both engines in both sets. Mean time per drawing is 0.12–0.13 s.

## Reading the table

**Wrong sections**
- M3 gave 72 unlabelled spans a wrong section:
  - all 40 different beams on line 0;
  - all 32 beams past the CB sequence, where alignment carried CB1's section.
- M4 gave none.

**Spans M4 held**
- M4 held 112 spans unresolved, and every exposure range contains the truth.
- This includes the 40 even-seed untagged spans that were in fact the same beam as their neighbour. M3 was right on those by construction, but alignment is not evidence on a real drawing.

**Continuous beams**
- Both engines are correct on the 128 CB spans.
- M4 gets there through the printed span sequence. M3 gets there by alignment, which also carried CB1 onto the 32 different beams after it, hence its 16.8 % CB concrete error.

**Planning envelope** (base … base + exposure)
- M4 contains the truth on 39 of 40 drawings in both sets. M3 does on 13 of 40 in the m4 set.
- The one miss, seed 636, is the same for both engines on clean drawings: a pre-existing −8.9 % base error that M4 does not change.

**Price of the precision**
- The base MAE rises because a held span leaves the base until a person labels it.
- The unresolved count rises for the same reason. On clean drawings, +80 is the one untagged span per drawing on each of 2 storeys. On m4 drawings, the count adds the 112 held spans and the continuous-beam bar roles the synthetic schedule does not print (top-through bars); each is an UNRESOLVED steel item, never zero.
