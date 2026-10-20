# Decision register: owner answers Q-50 to Q-63 (Alsenan), directive 2026-10-20 part 5.1

Lead, 2026-10-20 12:20 UTC. Source of every line: OWNER_DIRECTIVE_2026-10-20.md (full reasoning), the "Answer:" lines in
OWNER_QUESTIONS.md (Answered), and the owner's correction of 12:15 (OWNER_SESSION_CHANGES.md). This file records; it does
not add or change a rule. Workers add their evidence references and status changes in their task's handoff; the Lead copies
them here. Quantity statuses are the seven of directive 2.2 (VERIFIED / CALCULATED / PROVISIONAL / ASSUMED / HELD / CONFLICT
/ NOT APPLICABLE).

**Owner correction, 12:15 (binds every line below).** The owner's earlier answers are his deliberate MANUAL BOQ METHOD and are
preserved exactly (Q-43 / Q-48 wall and wet-wall heights, the Q-45 values including waste 5 %, every other owner method).
Where an answer below describes a drawing-derived method, the engine shows BOTH results (owner manual method and
drawing-derived), explains each difference and names the basis that applies. No agent changes the applicability or priority of
an owner method without his confirmation; the main-chat audit lines X1, X3 and X5 are withdrawn. A reconciliation proposal is
with the owner; until he confirms it, nothing released changes.

| Q | Owner answer | Applies to | General rule or project fact | Assumptions left | Designer questions | Status now | Task / verification needed |
|---|---|---|---|---|---|---|---|
| Q-50 | A, conditional: reconstruct the round stair from the plans when no section exists, labelled "reconstructed, no section"; flight by flight | Alsenan round reception stair | reusable method (stairs without a section) | step count 28 not yet proved (landing rise, arrival tread, 12 + 11 + 5 distinct) | stair section / details for the round stair | straight flights CALCULATED after check, curved parts HELD; 0.469 m3 not released | T-111 (hand), verifier re-derives |
| Q-51 | A, conditional: each winder = 0.5 x riser x its own drawn plan area where the wedge geometry holds | every villa | reusable method | 1.44 m2 main-stair corner may be landing or void | - | HELD until each step's area is drawn | T-111 |
| Q-52 | C, modified: per-room heights from levels, build-up, slab underside, crossing beams, ceilings; plaster and paint separately | every villa | drawing-derived method, shown BESIDE the owner manual method of Q-43 (correction 12:15) | unknown finished ceiling levels | ceiling levels where not drawn | both results shown; nothing released changes | T-112 (hand), T-095 queued |
| Q-53 | C, calculated provisional rate: materials from the mix (1:3: about 9.6 bags, about 1.00 m3 sand per m3) | every villa | reusable method; the Q-45 values stay the owner's manual method (correction 12:15) | material densities and dry factor (1.33) are documented assumptions | - | PROVISIONAL | T-115 (queued until the owner confirms) |
| Q-54 | B, hold until the +4.30 datum is verified | Alsenan annex | project drawing issue | what +4.30 denotes | annex roof datum (slab top, finished roof, screed?) | drawing-derived annex heights HELD; owner-method value shown as his method gives it | T-112 reads section B-B |
| Q-55 | C: printed 2.50 m main entrance; other doors searched, else 2.20 m ASSUMED (existing Urban fallback, knowledge 1.5.0 owner_reference_height_m) | every villa (fallback); Alsenan (search) | existing Urban rule, not a Kuwait standard | every door but the main entrance | door schedule | widths measured, heights ASSUMED 2.20 or printed | T-091 found no schedule; door m2 task when wired |
| Q-56 | A, conditional: four separate rows 22.20 + 7.04 + 4.88 + 4.80 = 38.92 m2; trace the engine's 5.95 m2 | Alsenan 1F | project geometry | porcelain finish PROVISIONAL | - | engine 44.87 not explained | T-113 (hand) |
| Q-57 | A, modified: gypsum ceilings take finishing + paint, no cement plaster; surfaces measured separately | every villa | reusable method | ceiling types and cove details not drawn | ceiling layout / cove detail | HELD (no ceiling surface model yet) | ceiling surface task after T-112 |
| Q-58 | A, conditional: offcuts reusable within the same roof / room; prove the 0.70 x 6.97 m trim covers the 4.60 m step before 17 rolls | every villa (rule); Alsenan 2F roof (proof) | reusable rule with a proof condition | whether a patch is allowed at the step | - | 2F roof HELD 17 / 18 | T-114 (hand) |
| Q-59 | B, modified: reuse within the same room, no universal 20 cm minimum; report optimised and conservative counts | every villa | reusable rule | per-position piece limits; no tile size printed on Alsenan | tile sizes per room | counts HELD (no size), optimised PROVISIONAL when sizes exist | tile count V2 after sizes |
| Q-60 | A: block wall to the underside of the beam / slab above; no beam drawn -> HELD; block type from notes (notes override), else outer white / inner black | every villa | owner rule (10:45) | walls without a drawn beam above | - | metres by hand merged; m2 / m3 HELD | T-107, T-108 |
| Q-61 | C, member by member (CB10 CONFLICT, CB3 / B3 HOLD, rings B4 only where identified, 6 unlabelled spans HELD, strips and boxes HELD) | Alsenan beams | project drawing issues; reusable record format | each held member | CB10 width, CB3 / B3, unlabelled spans, strips, SE box, CB12 strip | beams 68.84 m3 released part, rest HELD / CONFLICT | T-110 (hand), T-102 |
| Q-62 | A, conditional: stair / landing overlap measured once (main stair 4.951 m3, 0.163 m3 over all) after the 3-D intersection is verified | every villa | reusable rule | intersection geometry | - | CALCULATED, not released | T-111, then T-105 |
| Q-63 | C, hold: visible unresolved element "Sea-side boundary element, 7.00 m overall" with its unknowns | Alsenan | missing scope (never zero) | material, height, structure, foundation, finishes, railing / glazing, gate | sea-side fence detail | HELD, visible | DESIGNER_CLARIFICATIONS.md D-01 |

Not changed by this register: Q-37 (pantry waterproofed: directive X4 stands, the pantry hold in V2.11 is reviewed by T-114)
and the CB10 conflict rule (X6 stands: a schedule / drawing conflict is a CONFLICT plus a designer request).
