# T-171 Footing bars printed "n ø d/m": what the notation means, and the bar population that follows (investigation)

Worker 1 (lane S), 2026-10-22, under ENGINEERING_REASONING_STANDARD.md sections 2-4. Research only: nothing in `engine/`
changes, no quantity is released, the frozen footing methods and the released 874.86 kg line are untouched. Footings
ONLY (F8, F12, F13, F14, FF); nothing here is extended to columns, slabs or stairs (each needs its own evidence).
Drawings are cited by Drive folder and title only: Drive "Alsenan chalet project", `ST7757.pdf` (16 pages, read at
160-300 dpi) and `ST7757 dxf.dxf`. Per-cell callouts, dimensions and counts stay in the private folder (public repo).

## 1. The physical element

Five isolated two-layer footings (one occurrence each: one plan label per mark in the DXF model space, one `FTB`
schedule row each). Per footing four bar populations: TOP short / long, BOT short / long. Short bars run along W and
are spread across L; long bars run along L and are spread across W. The BOQ item is the straight core of each
population (kg); the boxed-bar legs, laps and the `3+n` boxed bars of the other footings are separate items, HELD.

## 2. Evidence, in the standard's hierarchy

| # | Evidence | Source | What it settles |
|---|---|---|---|
| E1 | 20 cells printed `n ø d/m` (TOP 6 / 7 / 10 per m ø14, BOT 8 / 9 per m ø14 / ø16); the same set prints counts `n ø d` and spacings `ø d/s cm` with the unit | ST p.9 schedule (PDF 300 dpi = DXF `FTB` attributes, re-read this run); p.13 ground-beam links `ø8/15cm`; p.7 dome `ø12MM/15cm` | `/m` = number of bars per metre run, i.e. a centre-to-centre spacing of 1/n (T-155, Checker-verified; re-confirmed) |
| E2 | Cover "not less than 7 cm" for concrete against soil | ST p.8 note 22 (Arabic; read this run) | edge bars at 7 cm from the face (a minimum) |
| E3 | Both typical isolated-footing sections draw a bar at BOTH ends of the bottom mesh, each edge bar inside the bend of the "Boxed bars" leg; the lift-footing section draws the edge bars of both layers in the corners of the closed cage | ST p.13 (both variants), p.14 | a bar at each edge is DRAWN (the "+1" is geometry, not a convention); the edge bars sit inside the boxed-bar legs |
| E4 | No legend, note or dimension gives the boxed-bar diameter, its legs or whether the TOP layer itself forms the box | ST p.8 (notes 1-24 read in full), p.9, p.13, p.14 | the enclosing-leg diameter is NOT printed |
| E5 | Notes 1-24 on p.8: no note "22B", no rounding or spacing rule. Note 22 is cover only | ST p.8 | the "S3.1 §22B: rate per metre, rounded up" cited by the frozen column route is NOT a drawing note (an unconfirmed study statement, as Q-71 says) |
| E6 | The designer's own count-printed footings (12 rows) do NOT follow any single rate-to-count rule: seven candidate rules (ceil r·S, round r·S, floor r·S + 1, ceil r·(S-2c), ceil r·(S-2c) + 1, floor r·(S-2c) + 1, ceil r·S + 1) each reproduce at most 6 of 12 rows with some integer rate, at most 5 of 12 with one rate per footing | ST p.9 (private scratch fit) | those counts are design counts, not a converted rate: they neither support nor contradict any reading |
| E7 | Practice, not a code clause: printed reinforcement is the designer's required steel; a spacing on a structural drawing is the largest centre-to-centre distance that complies (fewer bars per metre = less steel per metre than printed) | engineering practice (level 4, labelled) | 1/n is a MAXIMUM spacing |

**Meaning established:** `n ø d/m` = bars of ø d at a centre-to-centre spacing not exceeding 1/n m, spread across the
footing, with an edge bar at each side at the cover, inside any enclosing boxed-bar leg (E1 + E2 + E3 + E7). Status:
rate meaning DRAWING-CONFIRMED; "maximum" rests on practice E7 (labelled); edge bars DRAWN.

## 3. First-principles count

    L_eff = S - 2c - 2 d_enc - d          (centre of edge bar to centre of edge bar; c = 70 mm, d = bar, d_enc = leg)
    N     = ceil(L_eff x n / 1 m) + 1     (exact division k -> k + 1; exact arithmetic in mm)
    bar   = other side - 2c - 2 d_enc     (straight core stops inside the legs)
    kg    = N x bar x d^2/162             (Urban project default unit mass R3; exact 7,850 kg/m3 as a check)

Tool: `research/agents_t171/t171_bar_population.py` (pure, not wired). Results (5 footings, one each, straight core):

| Enclosing leg d_enc | Bars | BOT kg | TOP kg | Total kg | Note |
|---|---|---|---|---|---|
| 0 (no leg; physically excluded where a leg is drawn) | 609 | 1,648.99 | 1,180.84 | **2,829.83** | upper bound; exact-density check 2,826.41 |
| 8 mm | 603 | 1,626.41 | 1,163.35 | 2,789.77 | |
| 10 mm | 602 | 1,621.06 | 1,162.06 | 2,783.13 | |
| 12 mm | 601 | 1,614.46 | 1,160.77 | 2,775.23 | |
| 14 mm (if the TOP ø14 bars form the box) | 601 | 1,612.67 | 1,159.48 | 2,772.15 | |
| 16 mm | 601 | 1,610.87 | 1,158.19 | 2,769.06 | |

Per footing, d_enc 0 / 8 / 16 mm: F8 512.21 / 501.15 / 498.94; F12 716.47 / 713.26 / 705.26; F13 420.23 / 415.22 /
409.42; F14 439.33 / 437.26 / 435.19; FF 741.58 / 722.88 / 720.25 kg. Every achieved spacing is at or below 1/n.

**Robustness (the exact unresolved point).** 12 of the 20 populations keep the same count for any leg up to 16 mm
(thresholds: none, or 17 .. 35 mm). 8 lose one bar at a leg of: F8 BOT long and FF BOT short 1 mm (knife edge,
r x L_eff = 31.014 and 40.014), F13 TOP short 2 mm, F8 TOP short, FF TOP long and FF BOT long 7 mm, F13 BOT short
10 mm, F12 BOT short 11 mm. The count part of the range is 2,829.83 -> 2,793.76 kg (8 bars, -36.07 kg); the core
lengths shortening by 2 d_enc give the rest (-24.70 kg at 16 mm).

## 4. Reconciliation (kg, d_enc = 0 unless stated)

| From | To | Cause | kg |
|---|---|---|---|
| Q-71 A 2,742.51 | B 2,836.40 | A has one bar fewer in every population; with the drawn edge bars A's spacing is WIDER than 1/n in 20 of 20 (non-compliant) | +93.89 |
| Q-71 B 2,836.40 | this 2,829.83 | B spreads over S - 2c (bar faces); spacing is centre to centre, S - 2c - d: F13 BOT long 8 x 2.244 = 17.952 -> 19 bars, B gives 20 (one bar of 4.16 m ø16) | -6.57 |
| this 2,829.83 | Q-71 C 2,797.81 | C = n x full side, fractional: counts bars in the cover zone and part-bars; not a whole-bar population | -32.02 |
| this d_enc 0 | d_enc 8 .. 16 | the drawn boxed-bar legs (diameter not printed): 6 .. 8 bars fewer and cores 16 .. 32 mm shorter | -40.06 .. -60.77 |
| area check | | n x full side exceeds the spacing count in 2 populations (F13 BOT long 19.2 vs 19, F14 BOT short 34.2 vs 34): the printed rate times the full width includes the 7 cm cover zones where no bar can stand. Reported, not added (no physical bar) | 1.31 + 0.76 |

Residual unexplained: none. Freelancer: one kg/m3 allowance for all footings, straps and the perimeter beam, no
like-for-like line (T-136 / T-155): RULE_DIFFERENCE, not scored.

## 5. Status

- Notation meaning: DRAWING-CONFIRMED (rate) + practice E7 (maximum spacing), Checker to verify.
- Counts: 12 populations DRAWING-CONFIRMED candidates (independent of the unprinted leg up to 16 mm); 8 HELD at
  count N or N - 1 on the boxed-bar diameter.
- kg: HELD as the bounded range 2,769.06 .. 2,829.83 kg (never one value, never 0); every core length waits on the leg.
- No owner decision is needed for the physical quantity (standard 2.7): what remains is a DESIGNER item (extend the
  existing request "boxed-bar leg dimension + meaning of `3+n`" with: the boxed-bar diameter, and whether the TOP
  layer itself forms the box in F8 / F12 / F13 / F14 / FF). The frozen-route statements (S3.1 "§22B", AD2-D02) stay
  unconfirmed and unused. If the owner keeps a manual BOQ convention for "/m" bars (a contract measurement, not a
  physical count), that is the only owner point; draft in section 7 for the Lead.

## 6. General rule (proposed; scope and provenance labelled; adoption = a NEW rule version, not made here)

FOOTING MESH AT A PRINTED RATE / SPACING (footings only; evidence: Alsenan ST p.8 / 9 / 13 / 14 + practice E7):
"`n ø d/m` and `ø d @ s` are a maximum centre-to-centre spacing s = 1/n. Where the detail draws a bar at each edge,
N = ceil(L_eff / s) + 1 with L_eff = side - 2 cover - 2 d_enclosing - d (exact division k gives k + 1); straight core
= other side - 2 cover - 2 d_enclosing. An unprinted cover or enclosing-bar diameter holds the population (bounded
range), never 0; a printed count is never re-counted." Regression test: `tests/t171_bar_population` (normal square,
exact division, knife edge at 1 mm, odd 75 mm cover, `@` / `/cm` / `mm` spacing, two layers inside 12 mm legs, rotated,
cm / mm / m units, area check reported only, missing leg / cover / count / unit, L_eff <= 0, printed count kept).

## 7. For the Checker (Gate A, standard section 2.5) and the Lead

Re-derive from the drawing, not from this file: (1) p.13 both variants and p.14: edge bars at both ends, inside the
legs; (2) p.8 notes 1-24: no 22B, note 22 = cover only; (3) recount two populations yourself, suggested F13 BOT long
(the B vs centre-to-centre bar) and FF BOT short (the 1 mm knife edge); (4) the threshold list of section 3.
Q-71 in the section 6 format (Lead, only if 2.7 applies): Issue: how many bars a "/m" footing mesh has. Evidence: E1-E7.
Investigation: sections 2-4. Alternatives: none physical; contract convention only if the owner has one. Quantity
impact: 2,769.06 .. 2,829.83 kg (A 2,742.51 is non-compliant, C 2,797.81 is not a whole-bar count). Recommendation:
the physical count of section 3, range closed by the designer's boxed-bar diameter. Status: HELD (range). Next: designer
item; the same method may then be investigated for columns, slabs and stairs, each with its own evidence.

Lesson (proposed for the standard's section 7): the count rule was argued (A / B / C) before the edge-bar position was
established; spacing is centre to centre and the drawn boxed-bar legs move the edge bars, so 9 of 20 populations
depend on geometry that no option looked at.
