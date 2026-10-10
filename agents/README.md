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

## The roster — all 17 scaffolded

Every agent below exists as a folder with a real prompt, a validated schema, a
thin runner, and offline tests. They are first versions, ready to be upgraded
(the prompts are where most of the tuning happens — no code change needed).

| Phase | Agents | Folder |
|-------|--------|--------|
| 1 | A1 Extractor · A2 Reviewer | `a1_extractor/` `a2_reviewer/` |
| 2 | A3 Client · A4 Follow-up · A5 FAQ | `a3_client/` `a4_followup/` `a5_faq/` |
| 3 | A6 Planner · A7 Quotation & Contracts · A8 Briefer · A9 Orchestrator | `a6_planner/` `a7_quotation/` `a8_briefer/` `a9_orchestrator/` |
| 4 | A10 Content | `a10_content/` |
| 5 | A11 Site Progress · A12 Call Summariser · A13 Contract Reader | `a11_site_progress/` `a12_call_summariser/` `a13_contract_reader/` |
| 6 | A14 IG Analyst · A15 Marketing Strategist · A16 Post Designer · A17 Campaign Manager | `a14_ig_analyst/` `a15_marketing/` `a16_post_designer/` `a17_campaign/` |

### The marketing chain

The phase-6 agents are meant to run in order, each feeding the next:

```
A14 (what actually worked)  ──▶  A15 (the account's posting plan)
                             └─▶  A17 (one project's campaign)  ──▶  A16 / A10 (each post)
```

A15 plans the **account** — the ongoing calendar. A17 plans **one build**: an
objective, phases tied to the construction stage (you cannot film a finished
kitchen at foundations), a week-by-week schedule, and a review date. A17 emits
channel *weights*, never dinars — `engine/campaign.py` turns them into KWD.

Run a campaign with `python -m tools.campaign` (see `--help`); each review
writes a new version under `campaigns/<slug>/`, so the record of what changed
and why survives.

A16 also has a **grid mode**: `run_grid` designs a whole block of tiles
together (a launch grid, a campaign block) — no photo reused, no fact not
supplied by the owner, and a list of questions back. `social/` renders the
tiles to 1080×1080 PNGs with the real logo, Cairo and the brand orange;
`python -m tools.grid plan | render` drives it, and a tile whose photo has not
arrived renders the shoot instructions in its place.

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
(Haiku first, Sonnet automatically if the cheap answer fails validation; A1, A2
and A7 are pinned to Fable because a wrong number there costs real money — see
the model policy in `base.py`).
Credentials come from the environment (`ANTHROPIC_API_KEY` or an `ant auth
login` profile) — never hard-coded.

## To upgrade an agent

1. Edit its `prompt.md`.
2. Add a case to its `tests/` (known input → known correct output).
3. Run `python3 -m pytest agents/<name>` — the tests tell you if you improved it.
