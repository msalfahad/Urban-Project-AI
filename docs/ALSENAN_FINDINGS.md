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

## Drawing extraction — Schedule of Footings (ST7757 p9) vs takeoff

Extracted the footing schedule straight from the structural drawing and
cross-checked against the `القواعد` takeoff — **every footing matches**:

| Footing | Drawing (L×W×H cm) | Takeoff (m) |
|---------|--------------------|-------------|
| F | 90×80×30 | 0.9×0.8×0.3 ✓ |
| F2 | 190×170×35 | 1.9×1.7×0.35 ✓ |
| F5 | 240×210×40 | 2.4×2.1×0.4 ✓ |
| F8 | 400×360×50 | 4.0×3.6×0.5 ✓ |
| F9 | 340×270×55 | 3.4×2.7×0.55 ✓ |
| FF (lift, قاعدة مصعد) | 460×450×55 | 4.5×4.6×0.55 ✓ |
| FN | 100×100×30 | 1.0×1.0×0.3 ✓ |

Design data on the same sheet: bearing capacity 2.20 kg/cm², excavation ≥1.5 m,
groundwater at 4.5 m, designed for ground+1st+2nd floors; every footing's rebar
is scheduled (feeds E2 BBS steel).

## End-to-end trace (drawing → takeoff → audit → priced → web app)

Priced with the owner's own rates (from the Cost-By-Category export):

| Trade | Drawing | Takeoff | Priced | Rate | Amount | Var |
|-------|---------|---------|--------|------|--------|-----|
| RC concrete | p9 footings | 352.44 m³ | 380 m³ | 27.5/m³ | 10,450 | +7.8% |
| Lean concrete | p9 notes | 47.06 m³ | 50 m³ | 27.5/m³ | 1,375 | +6.2% |
| Steel | p9 rebar | 44.19 t | 45 t | 206/t | 9,270 | +1.8% |
| Aluminium | arch | 128.9 m² | 1 lump | 5,000 | 5,000 | lump |

Insight: concrete over-ordered ~8% (waste), steel spot-on, aluminium priced as a
lump rather than per-m². All now visible and traceable.

## Still needed

- **Pricing/units** for Alsenan from Urban Projects Manager (owner will export
  the project's BOQ) — to seed the Rate Library and price the حصر with the
  owner's real rates.
- Paint/plaster workbooks re-saved as **.xlsx** for formula-level audit.
