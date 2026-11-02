# T-465 r3: OPENING_HEIGHT_PDF_V2 glyph boxes equal to the V1 (PyMuPDF) reader

Checker fault (2026-11-02T12:04Z): on the real drawing set the r2 reader's words differed from V1 on the cross-axis
(x0 / x1 of vertical text), 36 of 36 words, up to 9.27 pt, for simple TrueType fonts (one non-embedded, one embedded).

## Cause (measured against PyMuPDF 1.28.2 on synthetic pages, then on the real set)

1. MuPDF reads a FontDescriptor whether or not the program is embedded, and ignores the program's hhea / OS/2 values:
   Ascent <= 0 -> (0.8, -0.2); otherwise (Ascent / 1000, -|Descent| / 1000). A POSITIVE /Descent (the embedded font of
   the real set: Ascent 760, Descent +240) is read as below the baseline. r2 kept the sign: its box spanned
   0.76 - 0.24 = 0.52 em instead of 1.00 em.
2. PyMuPDF (JM_char_quad) rescales a glyph box when ascender - descender (+ FLT_EPSILON) < 1 em: the box height
   becomes the font size, ascender and descender in proportion (the non-embedded font of the real set: 728 / -210 =
   0.938 em -> 1 em). r2 had no such step.
3. A standard-font name WITH a descriptor uses the descriptor (r2 used the built-in values); a font with NO descriptor
   uses MuPDF's built-in font by exact /BaseFont name (subset prefix kept), Times-Roman for any other name.
4. Found while testing (not in the Checker's list): r2 normalised the line direction in double precision; MuPDF does it
   in single precision, so at arbitrary angles "dir" differed in the 6th decimal. r3 uses single precision.

## Change

engine/source/opening_height_pdf_v2.py: `_Font` metrics (rules 1 and 3, `BUILTIN_NAMES`), `_quad_correction` (rule 2,
single precision step by step as PyMuPDF), `_normalize` / `_expansion` (MuPDF's fz_normalize_vector /
fz_matrix_expansion), word `dir` from the single-precision direction. View binding and measure_pdf stay V1's.
Known limit, flagged in `reader.limits` when hit: a zero-width glyph under the correction is not widened from the font
program's advance (PyMuPDF does; the PDF alone does not carry it).

## Evidence

- tests/t465_pdf_reader_v2/test_pdf_reader_v2_r3_metrics.py: 54 cases, exact equality with the oracle: embedded
  TrueType whose descriptor differs from hhea and OS/2; non-embedded ArialMT, horizontal / 90 / 180 / 270 / 45 degrees
  / mirrored, Tz, Ts, Tc, TJ, a scaled (mm) user space; 20 descriptor value pairs; a standard font with a descriptor;
  every BUILTIN_NAMES entry plus 5 unknown / prefixed names; ZapfDingbats (built-in, 0.963 em); 30 seeded random pages
  (any angle, mirror, 4 sizes, 6 x 6 descriptor values, embedded or not). On the r2 reader 44 of these fail.
- Real set, Drive 'Alsenan chalet project' / ST7757.pdf (16 pages) and sanitary-7757.pdf (3 pages), decoded to
  .work/private only: before r3 36 / 36 words differ (max 9.2736 pt); after r3 36 / 36 words and 660,238 / 660,238
  segments equal to V1, every page's width, height, state and image flag equal. Identity therefore also holds for
  measure_pdf, which consumes only these records.

## Proposed lessons-register row (ERS s.7)

"A reader replacement is proved against the old reader on every page of the real drawing set and on one synthetic case
per font class present there (embedded / substituted simple TrueType, descriptor sign and sum below 1 em), not only on
library-built pages; floating-point steps are emulated at the oracle's precision, including normalisation (T-465 r3)."
