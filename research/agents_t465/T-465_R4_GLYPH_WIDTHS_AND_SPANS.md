# T-465 r4: glyph widths as integers, and MuPDF's line / span rules (OPENING_HEIGHT_PDF_V2)

Checker fault (2026-11-02T19:57Z): an embedded simple TrueType font with FRACTIONAL /Widths (DejaVu subset) gave 3 of
15 words a different end (<= 0.0073 pt): the r3 reader summed the widths as given; MuPDF stores each width as an
integer.

## What MuPDF does (each rule measured against the oracle, PyMuPDF 1.28.2; MuPDF 1.28.2 source/fitz/stext-device.c
## and PyMuPDF's JM_make_spanlist read as a behaviour reference only, no code copied)

| Item | MuPDF | r3 | r4 |
|---|---|---|---|
| /Widths, /W, /DW, FirstChar, LastChar | pdf_to_int: single precision, floorf(f + 0.5f): 500.5 -> 501, 499.5 -> 500, -0.5 -> 0, -2.5 -> -2, 333.50001 -> 334 | as given (float) | `_pdf_int` |
| codes outside FirstChar..LastChar | MissingWidth; LastChar missing / > 255 / FirstChar > LastChar -> FirstChar = LastChar = 0; array shorter -> 0 | any array entry | as MuPDF |
| /MissingWidth | real held in an int field: truncated (433.7 -> 433, -433.7 -> -433, 0.9 -> 0) | as given | truncated |
| word space Tw | its own translation step after (w0 x size + Tc) x Th | summed with Tc (1 ulp off) | separate step |
| pen motion back by < 0.8 em | same line, same span | new word | same span |
| synthesized space 0.15 .. 0.3 em | ' ' inside the span | same | same |
| synthesized space > 0.3 em | FZ_STEXT_SYNTHETIC_LARGE: a span of its own -> V1 lists the two sides as two words | one word with a space | two words |
| same character again within 0.1 em | dropped (fake bold), device state unchanged | kept | dropped |
| superscript (line dir exactly (1, 0), origin > 0.1 x size above the line's first glyph) | new span | not split | split |
| line with no glyph extent / empty last span | line skipped / last span dropped (earlier empty spans stay) | kept | as MuPDF |
| Unicode spaces (U+00A0, U+2000..U+200A, ...) | read as U+0020 | kept | U+0020 |

## Named difference (bounded, flagged)

GLYPH_ACROSS_PAGE_EDGE: MuPDF drops a glyph only when its OUTLINE bounds lie wholly outside the page; V2 tests the
advance x ascender..descender box (it reads no glyph outlines). Bound: only a glyph whose box crosses the page edge,
and the word it belongs to, can differ; the page record carries the flag in `reader.limits`. Seeded corpus: 1 of 24
pages flagged, 1 of 192 words affected; the real drawing set has none differing.

## Evidence

- tests/t465_pdf_reader_v2/test_pdf_reader_v2_r4_widths.py: 111 cases, exact equality with the oracle (fractional,
  half, zero, negative widths, horizontal / 90 / -90 / 180 degrees, embedded or not; composite /W both forms + /DW;
  FirstChar / LastChar / MissingWidth; zero-advance lines and spans; pen motion -0.81 .. +0.9 em horizontal and
  vertical; fake bold 30 cases; superscript 14 cases; U+00A0; 24 seeded pages x 8 runs with Tc / Tw / Tz and any
  angle). On the r3 reader (baa3441d) 82 of the 111 fail.
- Checker's class reproduced in scratch (not committed: reportlab is not a dependency): 12 pages x 25 runs with
  DejaVu (fractional /Widths) and Poppins embedded, base-14 fonts, Tc -2 .. 0.5, Tz 80 / 130, any angle: r3 268 of
  300 words differ, r4 0 of 300.
- Real set, Drive 'Alsenan chalet project' / ST7757.pdf (16 pages) and sanitary-7757.pdf (3 pages), decoded to
  .work/private only: words 36 / 36 and segments 499,517 + 160,721 = 660,238 equal to V1 on every page (unchanged
  from r3: the set's fonts have integer widths).
- No BOQ quantity moves: OPENING_HEIGHT_PDF is an unwired producer.

## Proposed lessons-register row (ERS s.7)

"A reader replacement reproduces the old library's STORAGE of the data (integer glyph widths) and its grouping state
machine (pen, line, span, flags), each rule measured against the oracle on a boundary pair (e.g. 0.29 / 0.31 em,
0.099 / 0.101 em); what cannot be reproduced from the file alone (glyph outlines) is a named, flagged difference with
its bound (provenance T-465 r4)."
