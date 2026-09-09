# Alsenan / Alsnyan Villa (ST7757) — findings

The first real project run through the system. Recorded so the analysis isn't
lost between sessions.

## Identity — open question resolved

The project overview asked: *"Is drawing set ST7757 the same job as the Alsenan
Chalet budget?"* **Yes.** The ST7757 structural drawings are the **Alsnyan
(السنيان) residential villa** — client on the title block, plot 3700 / A5,
**Sabah Al-Ahmad Sea City (صباح الأحمد البحرية)**, the same location as every
takeoff workbook. (Note: the drawings say *villa*, not *chalet*.)

## The takeoff set (حصر) — all audited

| Trade | File | Quantity | Audit |
|-------|------|----------|-------|
| Reinforced concrete | خرسانة مسلحة | 352.44 m³ (+47.06 lean) | 🔴 `#REF!` in pool cross-total; lean excluded |
| Reinforcement steel | (on concrete cover) | 44.19 t → **125 kg/m³** overall | ✅ healthy |
| Aluminium | الالمونيوم | 128.9 m² | 🟡 voids unused (expected) |
| Blockwork | مبانى الطابوق | ~1,260 m² gross | 🟡 confirm opening deductions |
| Finishing | ارضيات/عازل/ديكور | ceramic 409.58 m², walls 433.83 m², skirting 282.85 m.l | 🔴 **295.44 mixed-measure defect** |
| Paint / Plaster | صبغ / مساح (legacy .xls) | — | ⏳ needs .xlsx to audit formulas |

## Drawing ↔ takeoff cross-checks (the Phase 1 loop, demonstrated)

Reading ST7757 page 1 (Column & Axis Plan) and comparing to the takeoff:

- Slab thickness note **16 cm** ↔ `بلاطات S.S 16 CM` (0.16 m). ✓
- Plot dimension **31.37 m** ↔ `العاديه` lean row (15 × 31.37). ✓
- Column schedule (C1 20×50, C2 30×50, C5 30×60, C6 30×70, C7 30×80,
  C8 30×80/90, C9 25×100/30×100, C11 30×110, CN 30×30 …) ↔ `الحوائط + الأعمدة`. ✓

## Schedule constraints found on the drawings

- Slabs/beams: **do not strike formwork before 21 days** (feeds A6/E12).
- External tie beams cast neighbour-side, above/below black block from
  foundation level (sequence constraint).

## The two blocking defects to fix before this takeoff is "approved"

1. **Concrete** — the broken `#REF!` grand total in `حمام السباحة` D19 (an
   abandoned cross-sheet formula). Clean it up.
2. **Finishing** — the `295.44` stairs total (`رخام+حوش` row 44) mixes step
   *linear* metres with landing/courtyard *areas*. Separate steps (m.l) from
   areas (m²).

## Still needed

- **Pricing/units** for Alsenan from Urban Projects Manager (owner will export
  the project's BOQ) — to seed the Rate Library and price the حصر with the
  owner's real rates.
- Paint/plaster workbooks re-saved as **.xlsx** for formula-level audit.
