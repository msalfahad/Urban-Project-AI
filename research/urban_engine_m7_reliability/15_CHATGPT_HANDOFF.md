# 15 Handoff — what worked, what did not, what to do next

## What worked

1. **Metamorphic testing found real defects fast.** Changing only the drawing (translate, rotate, mirror, explode,
   duplicate text, unrelated layer, units) and requiring identical quantities exposed 13 distinct causes, none of
   which the M1–M6 tests or the synthetic truth had caught: an MTEXT rotation stored as a vector, coordinates far from
   the origin, exact-zero overlap tests on flush faces, a convex clip against arc bands, a furniture square read as a
   column, a fixed 1.0-unit rectangle minimum, minimal cells of crossing lines, a reversed continuous beam, class
   limits at float precision, duplicated annotations, frames drawn as lines. Held-out: V4 69 / 100 → V5 100 / 100.
2. **Evaluating quantities on cluttered drawings** (not only clean ones) exposed the silent errors: 47 / 51 silent
   rows (columns ~15 m³, slabs 125–182 m³ over 40 villas) under the M6 engine, 0 under V5, on seeds generated after
   the freeze.
3. **Gating every change behind a convention** kept the M4–M6 frozen packages byte-identical; two ungated "harmless"
   changes were caught by those packages and withdrawn.
4. **Attribution by ablation** (V5 minus one convention at a time) gives every ST7757 change its basis.
5. **The release policy caught a checker error**: one footing was held UNRESOLVED because the second method
   disagreed; the checker was wrong, the engine right — exactly the failure the policy is meant to have.

## What did not work / is still open

1. **Second villa: blocked** — no second drawing set anywhere reachable. Everything real is still one project,
   post-discovery.
2. **No engineer decisions yet**: 0 m³ released. The policy, decisions bound to revisions and the OCR ledger exist;
   nobody has used them.
3. **"No silent shortfall" is not "no shortfall"**: V5 still misses 255 m³ of 1 455 m³ slab truth on the held-out set
   — reported, but 124 m³ of it (storeys whose plan is missing) has no volume range attached.
4. **Beams are never EXACT** on synthetic villas: untagged spans stay unresolved by convention (31 m³ of 678 m³ inside
   ranges).
5. **Legend from another sheet / the PDF** (M6 W6) — not read; ST7757 fills stay UNKNOWN.
6. **Residual placement sensitivity on ST7757**: exploded copy +0.042 m³ (one clipped footing whose corner a third
   line touches), mirror −0.002 m³, rot180 −0.13 kg; RTEXT not read.
7. **Independent checks** do not cover arc bands, arc-bounded and recovered panels (58 items NOT_COMPARABLE).
8. **Evidence lost when a rule tightens** happened once (P2: two column outlines stopped being reported); fixed, and
   now tested — but it shows every tightening rule needs a "still reported?" test.

## Recommendations (in order)

1. Get a second real villa with an independently prepared BOQ and run it through `tools/urban_project_run.py`
   exactly as `09_SECOND_VILLA_BLIND_TEST.md` describes — blind, frozen, then compared. This is the only evidence that
   can move the verdict.
2. Run an engineer review on ST7757 with the release policy: approve / reject / exclude per item, bound to the
   drawing's sha256; measure how much of the 79.6 m³ machine-supported and 234.3 m³ provisional concrete survives.
3. Attach a volume range to STOREY_PLAN_MISSING (the storey above / below as a bracket) and to the large
   volume-less finding kinds (DRAWN_NOT_MEASURED, STAIR_NOT_MEASURED, REGION_EXCLUDED) so that quotation exposure is
   bounded.
4. Read legends across sheets and from the PDF evidence adapter (W6).
5. Extend the per-item checker to arcs (exact circular segments) and recovered panels.
6. Make item ids frame-free (sheet-relative or content-hashed) so a unit change does not rename items.
7. Keep the metamorphic harness in every milestone's gate: a new rule must pass all ten operations on the held-out
   villas and on the real drawing.

## Do not

- quote from these numbers: they are planning figures, nothing is released;
- read the freelancer / MCP figures to choose a reading — reconcile only after a freeze;
- turn an UNRESOLVED item or a finding into a quantity without drawn geometry and a printed (or explicit convention)
  dimension;
- use a concrete-to-steel ratio.
