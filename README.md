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

## What's built so far

- **E1 Unit Guard** (`engine/unit_guard.py`) — refuses to mix m² / m / count into
  one total. Reproduces and blocks the real "295.44" defect from the audit.
- **Unit algebra core** (`engine/units.py`) — every quantity carries its unit and
  only combines lawfully.
- **Agent template** (`agents/_template/`) — the four-file pattern, runnable
  offline with a fake model.

Run the tests:

```bash
pip install -r requirements.txt
python3 -m pytest
```

## Where to read next

- **`docs/ARCHITECTURE.md`** — the whole system in plain language.
- **`docs/ONBOARDING.md`** — what the project needs from the owner to move
  forward (credentials, sample files, decisions).

## Build order

Phase 0 (audit) → 1 (takeoff core) → 2 (WhatsApp + leads) → 3 (programme,
quotation, cost control) → 4 (Instagram, preliminaries) → 5 (site, contracts,
learning loop). No phase starts until the previous one has run on a real job
without correction.
