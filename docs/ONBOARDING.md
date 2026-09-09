# What I need from you

You said you're clueless and want to give me "full access." Thank you — but the
honest truth is I don't need broad access to *everything*. I need a few specific
things, and some of them should **never** be pasted into a chat. This page lists
exactly what unblocks the work, in order, and how to hand each one over safely.

Nothing here is urgent all at once. We build one phase at a time. This is the
shopping list for the first two phases.

---

## Rule zero: how to share secrets safely

Some items below are passwords/keys. **Do not paste them into the chat.** Anything
in a chat can be logged. Instead:

- Put keys and credentials into the project's **environment variables / secrets**
  (I'll tell you the exact names to use, e.g. `ANTHROPIC_API_KEY`).
- Share credential *files* (like a Firebase service-account JSON) by placing them
  in the environment as a secret, not by uploading them into the conversation.
- If you're unsure whether something is a secret: if it's a long random string or
  a password, treat it as one and don't paste it.

Everything is already set up so secret files never get committed to the repo
(see `.gitignore`).

---

## 1. To make the takeoff core real (Phase 1) — highest value

Right now the engine works but has no real data to chew on. To turn it from a
demo into something that prices your actual jobs:

| # | What | Why | How to share |
|---|------|-----|--------------|
| 1a | **2–3 sample drawing sets** (PDF **and** the AutoCAD DWG/DXF) from real jobs | So A1/A2 (extractors) have real drawings to read. | Upload the files, or drop them in an environment folder. Not secret. |
| 1b | **The current takeoff Excel files** (the QS workbooks) | To rebuild the Phase 0 Auditor against your real formats and reproduce the 49 defects. | Upload. Not secret, but keep to a few examples. |
| 1c | **The rate library** — your material, installed and selling rates | So the engine can price. Even a rough spreadsheet is fine to start. | Upload a spreadsheet. |
| 1d | **The audit report** that found the 15,181 KWD / 49 defects | So I can match my checks to what you already found. | Upload. |

If you can only send **one** thing first, send **1a + 1b for a single job** —
that unblocks the most.

---

## 2. To wire in the AI agents

| # | What | Why | How to share |
|---|------|-----|--------------|
| 2a | **Anthropic API key** | So agents can actually call a model. | Environment secret named `ANTHROPIC_API_KEY`. **Never** in chat. |
| 2b | **Firebase / Firestore project** — the "centre" the doc describes | Every agent and module reads/writes here. | Service-account JSON as an environment secret. **Never** in chat. Tell me the project ID. |

If you don't have a Firebase project yet, tell me and I'll give you click-by-click
steps to create one — it's free to start.

---

## 3. To answer WhatsApp and Instagram (Phase 2 / 4)

These need business accounts and approvals that take time, so start them early
but they don't block Phase 1:

- **WhatsApp Business API** access (via Meta, or a provider like Twilio/360dialog).
  Tell me which, if any, you already use.
- **Instagram** business account details for A10 / E16.

I'll write you a separate step-by-step for whichever you choose — this is the
fiddliest part and I don't expect you to know it.

---

## 4. The "Urban Project Manager" web app

The doc says a web app already exists and runs on Firebase. To let E14 write the
approved BOQ into it, I need to know:

- Where its code lives (a repo? tell me the name and I'll request access).
- Or, if it's a no-code/hosted app, what it's built with.

---

## 5. Four questions only you can answer

These are the open questions from your own project document. Short answers are
fine:

1. **Is drawing set `ST7757` the same job as the "Alsenan Chalet" budget?** The
   title block and the budget name disagree, and verified numbers depend on it.
2. **What share of your work is black structure vs finishing vs turnkey?** This
   sets what the client agent optimises for.
3. **Roughly how many enquiries a month, and how many become contracts?** Even a
   guess gives the funnel a baseline.
4. **Which live project should go into Urban Project Manager first?**

---

## What I'll do without waiting for any of the above

I can keep building the deterministic engine modules that need no external
access — the Calculator (E3), Rate Library structure (E4), Audit Log (E5),
Alert Thresholds (E6) — and the agent scaffolding with offline tests. So the
core keeps growing while you gather the items above.

**The single best first move:** send me one real job's drawings (PDF + DWG) and
its takeoff Excel. Everything in Phase 1 gets real the moment you do.
