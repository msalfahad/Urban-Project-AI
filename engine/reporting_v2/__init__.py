"""URBAN QTO REPORTING V2 - presentation layer over frozen engine registers (project-agnostic).

model.py    presentation model, row classes, status aliases, declared sums, validation
terms.py    bilingual glossary + user-facing explanations of technical codes
layout.py   standard assembly: 00_TOTAL_SUMMARY + the adapter's sheets
xlsx.py     Excel renderer (no formulas, print-ready, deterministic bytes)
pdf.py      PDF renderer (HTML -> Chromium, same sections, deterministic metadata)
readback.py XLSX readback validation

It measures nothing and imports no QTO engine; per-project adapters map registers into the model.
"""
