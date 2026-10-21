"""R8.0 — the frozen test baseline for the R8 source engine.

Tests first, fixtures first, no production fix. Everything in this package is
test-side: a LibreDWG-shaped input builder, hand-derived geometric truth, an
ezdxf corroboration oracle and a reference realiser used only to prove that
each fixture can detect a deliberate break. Nothing under ``engine/`` may
import it (``test_r8_0_import_boundaries.py`` enforces that).
"""
