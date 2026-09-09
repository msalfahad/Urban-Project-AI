# Agents

Every agent in this system is the **same four files**. Nothing about an agent is
special code — it is a prompt, a contract for what goes in and out, a thin
runner, and tests. Improving an agent means editing a text file and running the
tests, not writing code.

```
agents/<name>/
  prompt.md      the instructions, in plain language
  schema.py      what goes in and what must come out (validated)
  agent.py       ~50 lines: load prompt, call model, validate output, save
  tests/         known input -> known correct output
```

## The one rule these agents obey

An agent may **read** something ambiguous (a drawing, a WhatsApp message) or
**write** something a human reads (an Arabic reply, a quotation). It may **never**
compute a total, apply a rate, or check its own arithmetic. All of that belongs
to the engine (`../engine`), which is plain code.

So an extractor agent emits *records* — "this window is 2.4 m x 1.6 m, from
sheet A-04 rev C" — and never a sum. The engine does the summing.

## The roster

See the project overview for the full schedule. In build order:

| Phase | Agents |
|-------|--------|
| 1 | A1 Extractor, A2 Reviewer |
| 2 | A3 Client, A4 Follow-up, A5 FAQ |
| 3 | A6 Planner, A7 Quotation Writer, A8 Briefer, A9 Orchestrator |
| 4 | A10 Content |
| 5 | A11 Site Progress, A12 Call Summariser, A13 Contract Reader |

Copy `_template/` to start a new one.
