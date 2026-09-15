# Architecture — in plain language

Written for anyone joining the project, no prior context assumed.

## The problem

Urban Projects prices building work by hand. A quantity surveyor measures
drawings into Excel, line by line; totals are copied into a pricing app, rates
applied, a number goes to the client. It works, but it is slow (days per
takeoff), unverifiable (a number in a cell has no source), and errors survive
silently into prices and payments. An audit of current files found 49 defects,
12 serious, worth ~15,181 KWD on a 120,975 KWD budget.

## The idea

One system, drawings in → checked quotation out, then the job followed to
handover. It rests on a single rule:

> Agents extract and explain. Code calculates. Humans approve. The database
> remembers.

Thirteen AI agents do the reading and writing. Twenty code modules do the
arithmetic. Three humans approve. One database (Firestore) is the centre — every
part reads and writes there, and **no agent ever calls another agent**. Each
writes a record; a database trigger wakes whatever comes next. Every handoff
leaves a row behind, so when a number is wrong you can walk backwards to the
drawing it came from.

```
WhatsApp ─┐
Instagram ─┼─► FIRESTORE ◄─── everything reads and writes here
Drawings ──┘       │
   ┌───────────────┼───────────────┐
   ▼               ▼               ▼
AI AGENTS      ENGINE          APPROVAL QUEUE
read, write    calculates      owner + 2 engineers
                   │
                   ▼
        Urban Project Manager (web app)
```

## The agents (A1–A13)

| ID | Agent | Does | Phase |
|----|-------|------|-------|
| A1 | Extractor | Reads drawings → one record per measurement, with source. Records only, never totals. | 1 |
| A2 | Reviewer | Reads the same drawing blind; engine compares the two. Disagreement → engineer. | 1 |
| A3 | Client | Answers WhatsApp in Kuwaiti Arabic; establishes contract form, area, floors, budget; asks for PDF + DWG. Never quotes. | 2 |
| A4 | Follow-up | Re-engages silent leads at 2/5/10 days with approved templates. | 2 |
| A5 | FAQ | Consistent answers on permits, timelines, finishing options. | 2 |
| A6 | Planner | Builds the work breakdown; hands durations to the schedule engine. | 3 |
| A7 | Quotation & Contract Writer | Writes the Arabic clauses of a quotation or contract per scope, from Urban's clause library. Never a figure — prices, durations, dates and the payment schedule are placed by code (E22 + `documents/`). | 3 |
| A8 | Briefer | Daily/weekly brief (set up in Cowork, not built). | 3 |
| A9 | Orchestrator | Routes events, sets priority, escalates. Never recalculates. | 3 |
| A10 | Content | Instagram captions/hooks, aware of the Kuwait calendar. | 4 |
| A11 | Site Progress | Reads site-WhatsApp photos, logs completion, flags stalls. | 5 |
| A12 | Call Summariser | Call → requirements, objections, next action. | 5 |
| A13 | Contract Reader | Extracts milestones, retention, penalties, notice periods. | 5 |

## The engine (E1–E20)

Arithmetic and rules, so they are code — free to run, instant, identical every
time.

| ID | Module | Does | Phase |
|----|--------|------|-------|
| E1 | Unit Guard | Refuses to add m² to m to pieces. **Built.** | 1 |
| E2 | BBS Steel Engine | Steel from bar schedules; kg/m³ ratios are a sanity check only. | 1 |
| E3 | Calculator | All quantity arithmetic per trade, from A1/A2 records. | 1 |
| E4 | Rate Library | Material/installed/selling rates, each with vendor, date, validity. | 1 |
| E5 | Approval & Audit Log | Append-only: what changed, from/to, who, server time. | 1 |
| E6 | Alert Thresholds | Variance beyond a limit → review; rate >60 days stale blocks pricing. | 1 |
| E7 | Phase 0 Auditor | 17 rules over any takeoff/export. **Built; the permanent exam.** | 0 |
| E8 | Waste Logic | Per material, not one blind percentage. | 2 |
| E9 | Cooling Load | AC sizing per floor (today a 9,750 KWD lump). | 2 |
| E10 | Funnel / CRM | Drop-off: conversations → qualified → drawings → quoted → signed. | 2 |
| E11 | Revision Delta | New drawing revision → change report, not a silent re-price. | 2 |
| E12 | Schedule Engine | Duration = qty ÷ rate; dependencies, critical path, float. | 3 |
| E13 | Schedule Benchmark | Compares a programme against a baseline and your own projects. | 3 |
| E14 | PM Sync | Writes approved BOQ into Urban Project Manager (a write, not an integration). | 3 |
| E15 | Finance & Cost Control | Budget/committed/actual/forecast/margin, with early erosion alerts. | 3 |
| E16 | Instagram Collector | Reach, visits, followers, saves, timing — evidence for A10. | 4 |
| E17 | Preliminaries | Site engineer, scaffolding, power/water, crane, cleaning, waste. | 4 |
| E18 | Subcontractor Scoring | Price vs market, reliability, quality, responsiveness. | 5 |
| E19 | Productivity Benchmarks | Your real production rates, measured from your own sites. | 5 |
| E20 | Estimate vs Actual | The learning loop: estimated vs actual per project. | 5 |
| E21 | Campaign Budget & KPIs | Channel weights → KWD that sums exactly; cost per lead. **Built.** | 4 |
| E22 | Document Numbers | Reference numbers, price totals, payment splits, validity dates, amounts in Arabic words for quotations and contracts. **Built.** | 3 |

## Why this split

An earlier plan made everything an agent — 33 agents. It would have paid tokens
for arithmetic and put hallucination risk into numbers a `SUM()` gets right
every time. So the arithmetic is code (the engine), and the agents only do what
models are genuinely good at.

## The programme piece (sheet 05)

Duration is split three ways for the same reason as everything else — judgement
is AI work, arithmetic is not:

```
Duration   = Quantity ÷ Production rate
Adjusted   = Duration × access × crew × sequence × season
Programme  = activities + dependencies → critical path → float
Committed  = Programme + safety allowance   (float held as its own activity)
```

The reference villa programme (28 activities, 8 stages, ~52 weeks) is a borrowed
template. Until Urban Projects' own production rates exist (E19), every duration
is **PROVISIONAL** and no completion date goes into a contract on its authority
alone.

## Tools

- **Claude Code** — building everything (this repo).
- **Cowork** — running the work: auditing takeoffs, the daily brief, Instagram. No terminal.
- **Claude chat** — deciding and checking: reading a drawing, resolving a variance.
- **Firebase/Firestore** — the centre; already runs the web app.
