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

## The roster — all 13 scaffolded

Every agent below exists as a folder with a real prompt, a validated schema, a
thin runner, and offline tests. They are first versions, ready to be upgraded
(the prompts are where most of the tuning happens — no code change needed).

| Phase | Agents | Folder |
|-------|--------|--------|
| 1 | A1 Extractor · A2 Reviewer | `a1_extractor/` `a2_reviewer/` |
| 2 | A3 Client · A4 Follow-up · A5 FAQ | `a3_client/` `a4_followup/` `a5_faq/` |
| 3 | A6 Planner · A7 Quotation · A8 Briefer · A9 Orchestrator | `a6_planner/` `a7_quotation/` `a8_briefer/` `a9_orchestrator/` |
| 4 | A10 Content | `a10_content/` |
| 5 | A11 Site Progress · A12 Call Summariser · A13 Contract Reader | `a11_site_progress/` `a12_call_summariser/` `a13_contract_reader/` |

Copy `_template/` to start a new one.

## Running an agent

Each agent's `run()` takes a typed input and returns a validated output. In
tests, a stub model is injected — no API key, no network:

```python
from agents.a3_client.agent import run
from agents.a3_client.schema import Message

reply = run(Message("ابغى ابني بيت"), model=my_stub)   # offline
reply = run(Message("ابغى ابني بيت"))                    # live: needs ANTHROPIC_API_KEY
```

Live calls use the shared runner in `base.py`, which calls the Claude API
(`claude-opus-5` by default; per-agent `MODEL`/`EFFORT` constants tune cost).
Credentials come from the environment (`ANTHROPIC_API_KEY` or an `ant auth
login` profile) — never hard-coded.

## To upgrade an agent

1. Edit its `prompt.md`.
2. Add a case to its `tests/` (known input → known correct output).
3. Run `python3 -m pytest agents/<name>` — the tests tell you if you improved it.
