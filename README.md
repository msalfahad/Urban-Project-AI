# Urban Projects — AI Operating System

Takes a client from their first WhatsApp message to a **priced, checked,
traceable** quotation, then follows the job through construction to handover.
Drawings in, quantities out, prices applied, a human approves, the project runs.

## The one rule everything follows

> **Agents extract and explain. Code calculates. Humans approve. The database
> remembers.**

An AI may read a drawing or write Arabic to a client. It may **never** compute a
total, apply a rate, or check its own arithmetic. That division of labour is the
whole design: models are good at reading drawings and bad at adding numbers;
code is the reverse.

## Layout

```
engine/     Deterministic code modules (E1–E20). No model, no tokens.
agents/     AI agents (A1–A13). Each is four files: prompt, schema, runner, tests.
tests/      Engine tests.
docs/       Architecture and onboarding.
```

## Engine modules built

E1 Unit Guard · E2 BBS Steel · E4 Rate Library · E5 Audit Log · E6 Alert
Thresholds · E7 Phase 0 Auditor (priced + حصر takeoffs) · E8 Waste Logic ·
E9 Cooling Load · E12 Schedule Engine · E14 PM Sync · E15 Finance & Cost
Control · E17 Preliminaries · E20 Estimate vs Actual. Plus the cost-export
parser and the boq-formula mirror. All deterministic, no model. Remaining:
E3, E10, E11, E13, E16, E18, E19.

## What's built so far

- **Phase 0 — the deterministic BOQ/Excel Auditor** (`engine/audit/`, no LLM):
  Excel in → RED/YELLOW/GREEN report → approve (zero RED) → structured BOQ →
  **test-sandbox** Firestore write. Catches formula errors, skipped SUM rows,
  mixed-unit quantity totals (the 295.44 case), wrong concrete classifications,
  rounded-rate discrepancies, blank prices, `#REF!`, steel-ratio anomalies and
  missing waste. Run: `python3 -m tools.phase0_audit workbook.xlsx`. See
  **`docs/PHASE0.md`**.
- **All 13 AI agents** (`agents/a1_extractor/` … `agents/a13_contract_reader/`) —
  each a real prompt + validated schema + thin runner + offline tests. First
  versions, ready to upgrade by editing prompts. See `agents/README.md`.
- **Shared agent framework** (`agents/base.py`) — one place that calls the Claude
  API (`claude-opus-5`), with the model injectable so the whole roster runs
  offline in tests.
- **E1 Unit Guard** (`engine/unit_guard.py`) — refuses to mix m² / m / count into
  one total. Reproduces and blocks the real "295.44" defect from the audit.
- **Unit algebra core** (`engine/units.py`) — every quantity carries its unit and
  only combines lawfully.
- **E14 PM Sync** (`engine/pm_sync.py`) — writes an approved BOQ into the Urban
  Projects Manager web app's Firestore, in the exact document shape the app reads.
  `engine/boq_formula.py` mirrors the app's quantity formulas to the decimal.
  See **`docs/INTEGRATION.md`**.

50 tests pass with no API key and no network:

```bash
pip install -r requirements.txt
python3 -m pytest
```

To run an agent **live**, set `ANTHROPIC_API_KEY` in the environment (never in
code or chat) and call its `run()` without a `model` argument.

## Where to read next

- **`docs/ARCHITECTURE.md`** — the whole system in plain language.
- **`docs/ONBOARDING.md`** — what the project needs from the owner to move
  forward (credentials, sample files, decisions).

## Build order

Phase 0 (audit) → 1 (takeoff core) → 2 (WhatsApp + leads) → 3 (programme,
quotation, cost control) → 4 (Instagram, preliminaries) → 5 (site, contracts,
learning loop). No phase starts until the previous one has run on a real job
without correction.
