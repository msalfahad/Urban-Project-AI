# T-605 Footing overlap counted once: concrete, blinding, side forms per footing pair

Worker 1 (lane S, non-candidate, backlog-permitted), 2026-11-07, branch `agents/task-T-605`. Research only: no engine
module, candidate line, released line, rule file or method version changed; nothing released. Development villa, not
an accuracy claim. ERS s.2 - 4 applied; ELEMENT_REGISTER 'FOOTING OVERLAP' (Lead 2026-11-07 16:17), Checker
F-C-T597-1, R-T597-1 .. 5, T-233, T-478, T-206 r2, T-551.

## 0. Sources and run

- Drive "Alsenan chalet project" / "ST7757 dxf.dxf", downloaded this run, decoded into `.work/private` only (sha256
  9f9d1179, = the route G input). FOUNDATION PLAN outlines and FT / FTB schedule read with the T-597 reader
  (`research/agents_t597/t597_alsenan.py`, read only), but with the EXACT closed polyline where an outline is not a
  rectangle (T-597 carried FN 180C as its bounding box: harmless for a union, wrong for a per-footing plan).
- Printed relations cited, not re-read: ST p.13 blinding projection 0.10 each side (T-170 / T-206); the common bottom
  stack, footing bottom = formation + 0.10 blinding + 0.07 underlay for every isolated type (T-206 r2 table).
- Engine: candidate of record ARCH_TAKEOFF_V3.0.58 (structural lines = `research/agents_t507/out/LINE_INDEX_V3_0_57.json`,
  unchanged by V3.0.58). Freelancer: his FN rows as read by T-551 (four at 1.00 x 1.00 x 0.30); workbook not re-opened.
- Code: `footing_overlap_v1.py` (FOOTING_OVERLAP_V1, R-T605-1 .. 5, every villa), `t605_alsenan.py` ->
  `out/T605_FOOTING_PAIRS.json` (handles, sizes, m2 / m3 only). Tests: `tests/t605_footing_overlap` (15).
- Run: `.work/venv/bin/python -I research/agents_t605/t605_alsenan.py .work/private/st7757.dxf`.

## 1. The physical element (ERS s.2.1)

Each isolated footing = drawn plan outline x scheduled H, all bottoms on one stack. Its blinding = the drawn outline
grown 0.10 (mitred), one plain layer per plan point. Its side forms = its vertical faces. Where two footings meet the
shared material is one block of concrete, one layer of blinding and one interface, formed at most once.

## 2. Census: every pair within 2p = 0.20 m (25 closed outlines; F10 + F 1B1B open, HELD Q-31 C; FF raft 1B2B no neighbour)

| Pair | Drawn m2 (schedule) | Neat overlap | Shared edge | Grown overlap m2 | Blinding owner |
|---|---|---|---|---|---|
| F9 180F / FN 180C | 9.18 (9.18) / **0.86 (1.00)**, FN notched 0.40 x 0.35 | 0 (the notch gives it up) | 0.75 m (0.40 + 0.35) | **0.190** | F9 (drawn whole; also deeper) |
| F8 1B24 / FN 10F0 | 14.40 / 1.00, both whole | 0; gap 0.175 m | 0 | **0.005625** | F8 (deeper 0.50 vs 0.30, T-478) |

No other pair touches or comes within 0.20 m. Sum of grown outlines 129.43, union 129.234375: overlap 0.195625 m2 (the
Checker's F-C-T597-1 figure; T-597's 0.335625 took FN 180C as its 1.00 x 1.00 box).

## 3. Quantities: own vs engine vs freelancer

| Item | Own (drawing) | Engine V3.0.58 | Delta | Freelancer | Verdict proposal |
|---|---|---|---|---|---|
| F9 + FN 180C concrete | 5.049 + 0.258 = 5.307 m3 | 5.049 + 0.258 (L-35da8866, L-d2c75eb1) | 0 | 5.049 + 0.300 | ENGINE_RIGHT; his FN row bills the 0.40 x 0.35 x 0.30 = **0.042 m3** F9 already holds (same as T-233 / T-551) |
| all 25 pads | 64.304 m3 (schedule rectangles summed 64.346) | 64.304 | 0.000 | (T-551 keyed line) | AGREE; 64.346 refused (piece twice) |
| F8 / FN 10F0 concrete, forms | no common prism | - | 0 | - | NO_COMMON_PRISM |
| footing blinding, 24 pits in plot | 127.344375 m2 = 12.734438 m3 | 12.734438 | 0.000000 | plate (T-478) | AGREE (union); his plate is a RULE_DIFFERENCE (T-478) |
| blinding F9 / FN 180C per footing | 1.044 / 0.111 m3 (FN 1.30 grown L - 0.19) | 1.044 / 0.111 (T-478) | 0 | - | AGREE |
| side forms F9 + FN 180C | 7.46 .. 7.685 m2 (interface none / once) | HELD OQ10 (every footing FW line blank) | n/a | not compared | NO_COMPARISON; summed faces 7.91 refused |

Side forms of the notched pair by hand: F9 12.20 x 0.55 = 6.71; FN perimeter 4.00 (the notch keeps it) x 0.30 = 1.20;
summed 7.91. Along the shared 0.75 m both bottoms are on the stack, so the contact is 0.30 high: 0.225 m2 is the
interface (formed once if F9 / FN are poured in turn, not at all if poured together: pour sequence not printed, the
bound stays open by name), 0.75 x 0.25 = 0.1875 m2 of F9 face above FN is exposed and formed. 7.91 - 2 x 0.225 =
7.46; + 0.225 = 7.685. The scheduled FN rectangle would put 0.75 m of FN face inside F9: refused.

## 4. Reconciliation in units (ERS s.2.4)

Concrete: schedule sum 64.346 - drawn 64.304 = 0.042 m3 = 0.40 x 0.35 x 0.30 (the notch), residual 0. Blinding: sum
129.43 - union 129.234375 = 0.195625 = 0.19 (F9 / FN 180C) + 0.005625 (F8 / FN 10F0), residual 0; in-plot union x
0.10 = engine to 1e-6. Engine vs drawing on every valued line: 0. No line moves.

## 5. Rules, tests, lessons row (proposed)

R-T605-1 .. 5 in `footing_overlap_v1.py`: drawn outline governs, schedule rectangle refused where notched; a common
prism counted once, owned by the containing (deeper) footing, unknown bottom -> HELD; blinding union, overlap to the
whole-drawn footing else the deeper, equal -> SHARED; interface formed at most once, bound [0, c e]; a summed figure
that counts an overlap twice is refused. Tests: E605 (3 footings: one notched round another, one touching) normal +
adverse (rotated 30 / 117 deg, mirrored, mm, summed refused, schedule rectangle refused, missing depth / outline /
level HELD never 0, equal prisms SHARED, partial vertical contact) + the committed statement re-adds.

Learned (code defect caught by the adverse test): an exact boundary intersection misses a shared edge once the
drawing is rotated (float noise), which would form an interface twice; the shared edge is found by snapping within
1e-6 m.

| 2026-11-07 | FN 180C scheduled 1.00 m2, drawn 0.86 notched round F9; freelancer bills the piece twice (+0.042 m3) | a footing drawn notched round its neighbour; schedule L x W ignores the notch | concrete / blinding / forms on the drawn outline; overlap once, owner = whole-drawn (else deeper); interface formed at most once (every villa) | tests/t605_footing_overlap (E605 normal; adverse rotated / mirrored / mm / summed / schedule rectangle / HELD) | PROPOSED |

## 6. Checker re-measure list

- 180C vertices (146 262.2 .. 147 262.2, 46 648.0 .. 47 648.0, notch to 146 662.2 / 46 998.0) against 180F (143 262.2
  .. 146 662.2, 44 298.0 .. 46 998.0): notch = F9's corner exactly, drawn 0.86 m2.
- 10F0 (145 737.2 .. 146 737.2, 41 323.0 .. 42 323.0) to 1B24 (146 912.2 .., 42 298.0 ..): gap 0.175 in x, grown
  overlap 0.025 x 0.225 = 0.005625 m2.
