# Phase 0 — the deterministic BOQ/Excel Auditor

The exam every takeoff must pass. **No LLM anywhere in this flow** — it is pure
arithmetic and rules, so it is free to run, instant, and identical every time.
Firestore stays the source of truth; this flow only *reads* an Excel file and,
after human approval, *writes* to a **test sandbox**.

## The flow

```
Excel/BOQ upload
      │
      ▼
deterministic audit  ─────►  RED / YELLOW / GREEN report
      │                       (engine/audit, no model)
      ▼
review & correct  (a human reads the report, fixes the file)
      │
      ▼
approve   ── gated: zero RED + a named approver  (pipeline/phase0.approve)
      │
      ▼
structured BOQ  ─────►  TEST Firestore write  (sandbox/<tag>/boqItems only)
```

## What it catches (the checklist)

| Rule | Defect | Severity |
|------|--------|----------|
| R01 | `#REF!` / `#DIV/0!` / `#VALUE!` … | 🔴 |
| R02 | blank / zero price on a priced line (the سيجما-at-0 case) | 🔴 |
| R03 | amount ≠ quantity × rate (formula error) | 🔴 |
| R04 | rounded unit-rate discrepancy | 🟡 |
| R05 | mixed units summed in a **quantity** total (the 295.44 case) | 🔴 |
| R06 | total ≠ sum of its rows | 🔴 |
| R07 | a SUM range that skips a priced row | 🔴 |
| R08 | concrete classification (lean grade on a structural element, missing/unknown grade) | 🟡 |
| R09 | steel-to-concrete ratio anomaly (kg/m³ outside band) | 🟡/🔴 |
| R10 | material lines with no waste / order quantity | 🟡 |
| R11 | negative / zero quantity | 🟡 |
| R12 | missing / unrecognised unit | 🟡 |
| R13 | duplicated line (possible double count) | 🟡 |
| R14 | unit-rate outlier vs like items | 🟡 |
| R15 | unit doesn't match its dimensions (E1 Unit Guard) | 🔴 |

A key distinction the auditor draws: summing the **money** column across
different-unit lines is normal (that's what a BOQ total is); summing the
**quantity** column across different units is the meaningless-total defect.

## Two workbook shapes, auto-detected

`audit_file()` (and the CLI) auto-detect which auditor to use:

- **Priced BOQ** (description · unit · quantity · rate · amount) → the rule
  auditor above (`engine/audit/rules.py`).
- **Dimension takeoff (حصر)** (width × length × height → volume, or count ×
  length × height → area; concrete, aluminium, blockwork) → the takeoff auditor
  (`engine/audit/takeoff.py`).

### Takeoff (حصر) checks

Because these sheets are formula-driven and auto-recompute, deterministic
auditing reliably confirms **arithmetic integrity** but cannot verify a
*measurement* against the drawing — that is Phase 1 (A1/A2 extract from the
drawing, the engine compares). The takeoff auditor checks:

| Rule | Defect | Severity |
|------|--------|----------|
| T02 | `#REF!` / Excel error in a cell | 🔴 |
| T04 | a SUM whose value ≠ the sum of its range | 🔴 |
| T05 | cover total ≠ sum of the section values | 🔴 |
| T06 | steel-to-concrete ratio out of band | 🟡/🔴 |
| T07 | lean/plain concrete (العاديه) excluded from the RC total | 🟡 |
| T08 | opening-deduction (خصم فراغات) columns present but unused | 🟡 |
| T00 | a data sheet whose layout wasn't recognised — never a silent pass | 🟡 |

It never reports GREEN on a sheet it did not actually parse (T00), and it does
**not** guess at wrong measurements (which it cannot know deterministically).

Legacy `.xls` files should be re-saved as `.xlsx` (one click in Excel, keeps the
formulas) so formula-level checks apply.

## Run it

Audit a workbook (human-readable):

```bash
python3 -m tools.phase0_audit /path/to/alsenan_chalet.xlsx
```

As JSON (for Cowork / further processing):

```bash
python3 -m tools.phase0_audit workbook.xlsx --json
```

Exit code is `0` when approved (no RED), `1` when RED — so it can gate a script.

## Test-only Firestore write

Writes go **only** to `sandbox/<project-tag>/boqItems` — never to the app's
production `projects/{id}/boqItems`. This is enforced in code
(`pipeline.phase0.write_to_sandbox` and `tools.firestore_sandbox` both refuse any
other path), not by convention.

Live sandbox write requires **all** of:

1. `pip install firebase-admin`
2. A Firebase **service-account key** for the `urbanprojectsmanager` project, at
   the path in `URBAN_FIREBASE_SA` (or `GOOGLE_APPLICATION_CREDENTIALS`). Never
   commit it — it is gitignored.
3. `URBAN_ALLOW_SANDBOX_WRITE=1`

```bash
URBAN_ALLOW_SANDBOX_WRITE=1 URBAN_FIREBASE_SA=/path/sa.json \
python3 -m tools.phase0_audit alsenan_chalet.xlsx \
    --write-sandbox --project-tag TEST-alsenan --approver "Eng. Fahad"
```

Without those set, `--write-sandbox` prints a **dry run** of exactly what it
would write. It never writes when any RED issue remains.

### Getting the service-account key (test setup)

In the Firebase console for project **urbanprojectsmanager**:
Project settings → Service accounts → *Generate new private key* → save the JSON.
Put it somewhere outside the repo and point `URBAN_FIREBASE_SA` at it. That key
is only used to write to the `sandbox/` tree; it never touches production BOQs in
this flow.

## Two things I still need from you

1. **The real Alsenan Chalet Excel** (the QS workbook). The auditor is proven
   against a synthetic Alsenan-like file that embeds every defect class above;
   the moment you upload the real one, the same command runs on it and we see the
   actual findings.
2. **A Firebase service-account key** (as above) when you want to see the
   approved sandbox BOQ appear in a test project.
