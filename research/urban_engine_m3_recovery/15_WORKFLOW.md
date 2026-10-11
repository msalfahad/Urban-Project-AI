# Workflow: from a drawing set to a provisional BOQ (M3)

**Setup**
- All commands run from the repository root with Python 3.11+ and `ezdxf` installed.
- Always use `python3 -I` on drawings and PDFs that came from outside.
- Keep inputs under `data/inputs/` (git-ignored).

**Optional tools**
- PDF evidence: `pymupdf` and the local `tesseract` binary. Without OCR the pages are recorded as `OCR_UNAVAILABLE`, and the manual pathway (step 3) applies.
- PDFs of the BOQ and overlays: Chromium. Pass `--no-pdf` without it.

## 1. One command: the BOQ from the structural DXF

```bash
python3 -I tools/urban_boq_m2.py run --drawings NEW_STRUCTURAL.dxf --route G --out OUT --cache .cache
```

**Outputs** (all listed in `OUT/run_log.json`):

| Group | Files |
|---|---|
| Workbook and report | `STRUCTURAL_BOQ.xlsx` (sheet `MISSING_STEEL` included), `BOQ_REPORT.pdf` / `.html` |
| Overlays | `VISUAL_QA_OVERLAYS.pdf`, `overlays/*.svg`, region colours with a legend |
| BOQ | `CONTRACTOR_BOQ.csv`: A concrete, B reinforcement by diameter, C not detected / family coverage, D missing steel by family and storey |
| Registers | `PROVISIONAL_REGISTER.csv`, `UNRESOLVED_REGISTER.csv`, `VERIFIED_REGISTER.csv` (empty on a new project) |
| Coverage and completeness | `COVERAGE_RISK.csv`, `FAMILY_COVERAGE.csv`, `REBAR_COMPLETENESS.csv`, `MISSING_STEEL_BY_FAMILY_STOREY.csv` |
| Assumptions and checks | `ASSUMPTIONS.csv`, `SENSITIVITY.csv`, `EXCEPTIONS.csv`, `BLOCKERS.csv` |
| Summaries | `FAMILY_SUMMARY.csv`, `FLOOR_SUMMARY.csv`, `STEEL_BY_DIAMETER.csv`, `SUMMARY.json` |

Every quantity is in one of four categories:

| Category | Meaning |
|---|---|
| **Verified** | Never on a new project. |
| **Provisional** | low / base / high, with its blocker and the convention it rests on. |
| **Unresolved** | An exposure range, never added to a total. |
| **Not detected** | The family coverage records. `NO_EVIDENCE_FOUND` means "confirm absent", not "absent". |

## 2. Typical-detail evidence from the PDF set (ground-beam bars, blinding note)

```bash
python3 -I tools/pdf_evidence.py extract --pdf SET.pdf --out EVID --pages 13 --dpi 300 --redact 'OWNER WORDS'
python3 -I tools/pdf_evidence.py check --evidence EVID/DETAIL_EVIDENCE.json
```

**Reading order on every page:** native text, then the vector check, then OCR.

**On a vector-glyph page:**
- Every drawn glyph is classed by shape.
- A page-wide OCR vote assigns a character to each glyph class.
- A bar notation is accepted (`OCR_UNREVIEWED`) only when:
  - its four reads (page plus three crop reads at twice the resolution) agree with the glyph check (`VECTOR_GLYPH_CONSENSUS`), or
  - the reads are unanimous and no glyph contradicts them.
- Anything else is `OCR_REJECTED_*`. It is kept in the file and never used.

**What gets written:**
- Every record carries its page, region (points and pixels), raw text, confidence, the reads and its crop file name.
- Crops go to `EVID/crops/` and are never committed.
- Owner, title-block and file-path text is dropped before recording; only the count is kept.

**Using the evidence:** pass it to the BOQ run:

```bash
python3 -I tools/urban_boq_m2.py run --drawings NEW.dxf --route G --profile my_profile.json \
        --evidence EVID/DETAIL_EVIDENCE.json --out OUT --cache .cache
```

**How the BOQ treats it:**
- Bars from OCR records are **PROVISIONAL**, confidence **LOW**, blocker `OCR_DERIVED_UNREVIEWED`. They are never verified.
- A role the detail does not show, or whose read was rejected, becomes an UNRESOLVED steel item. The component is then `PARTIAL_MISSING`, never 0 kg.

## 3. Review and manual transcription (what OCR cannot settle)

**Confirming a record OCR read correctly**
1. Open its crop (`EVID/crops/<record>.png`) next to the PDF.
2. In `DETAIL_EVIDENCE.json`, set the record's state to `MANUALLY_CONFIRMED`, with who and when:

   ```json
   {"record_id": "EV-0003", "state": "MANUALLY_CONFIRMED", "confirmed_by": "J. Engineer", "confirmed_on": "2026-10-12"}
   ```

3. Run `pdf_evidence.py check`. It refuses a confirmation without `confirmed_by` and `confirmed_on`.

On the next run the blocker of those bars changes from `OCR_DERIVED_UNREVIEWED` to the ordinary bar-model blocker. They stay PROVISIONAL.

**Transcribing a rejected or missing record** (for example EV-0007, the less-than-5 m class link) uses the same schema:

```python
from engine.source import detail_evidence as DE
r = DE.manual_record("EV-M001", page=13, region=(x0, y0, x1, y1), text="Ø8/20cm", by="J. Engineer", on="2026-10-12")
ev["records"].append(r)
# add the bar to the detail it belongs to:
ev["details"][k]["bars"].append({"role": "LINKS", "count": None, "dia_mm": r["parsed"]["dia_mm"],
                                 "spacing_m": r["parsed"]["spacing_m"], "record_id": r["record_id"],
                                 "role_basis": "MANUAL_TRANSCRIPTION"})
# or a whole detail:
ev["details"].append(DE.manual_detail("DET-M01", "GROUND BEAM less than 5m length", [("LINKS", r)], page=13))
assert not DE.validate(ev)
```

**Printed values the DXF does not carry go into the project profile.** These include storey heights, levels, the blinding thickness and the typical ground-beam classes. Each entry carries `provenance` and `source`:

| Provenance | Use it for |
|---|---|
| `PRINTED_VALUE` | A value a person read on the drawing. |
| `READING_OF_PRINTED_VALUE` | A machine or OCR reading not yet confirmed. |
| `ENGINEERING_JUDGEMENT` | Never for a printed value. |

The ST7757 profile, `profile_st7757_m3.json`, is the worked example.

## 4. Change one assumption (incremental recalculation)

```bash
python3 -I tools/urban_boq_m2.py run --drawings NEW.dxf --route G --out OUT2 --cache .cache \
        --set BEAM_DEPTH_READING=BELOW_SLAB --set GB_EXTERIOR_BUILDUP_M=0.15
```

- With `--cache` the DXF is not read again: the intake is keyed by the drawing's sha256 and the intake code digest.
- Detection runs once per command. On ST7757 that is 0.9 s from a warm cache, against 2.1 s cold.
- Within one run, every alternative in `SENSITIVITY.csv` is re-priced from the detected model, without re-reading or re-detecting.
- Timings are in `OUT/run_log.json` (see `14_PERFORMANCE.json`).

## 5. Reproduce this package

```bash
SP=/path/to/scratch
git worktree add $SP/m2wt c5123a7                                   # the M2 engine, for before/after
python3 -I tools/urban_boq_m2.py run --drawings data/inputs/by_sha256/9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079.dxf \
        --profile research/urban_engine_m3_recovery/profile_st7757_m3.json --route G \
        --evidence research/urban_engine_m3_recovery/evidence/DETAIL_EVIDENCE.json \
        --out research/urban_engine_m3_recovery/st7757_route_g --as-of 2026-10-11 --cache $SP/cache
# held-out sets and scores: 13_HELDOUT_EVALUATION.md
python3 -I research/urban_engine_m3_recovery/build_m3_reports.py --m2-root $SP/m2wt --heldout $SP/res \
        --runlog-cold COLD/run_log.json --runlog-warm WARM/run_log.json
python3 -m pytest -q tests/m3_recovery tests/m2_generic_engine
```

**Builder guards.** `build_m3_reports.py` refuses to write any output that carries:
- owner text, Arabic source text or a file path;
- a firewalled benchmark number.

External estimates appear as positions only.

## Never commit

- client drawings (dxf / dwg / pdf);
- OCR crops and page renders;
- `.xlsx` workbooks, review PDFs, `.secrets/`, credentials.

The `.gitignore` already excludes the generated PDFs, workbooks, crops and renders of this package.
