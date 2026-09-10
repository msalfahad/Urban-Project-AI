# Go-live checklist — Urban Projects AI office

Status as of the live test (see `tools/live_smoke.py`): **14 of 14 agents run live** on
real Alsenan / Urban inputs (A1 + A7 earlier in the session; the rest in one batch).

## Blocking (owner)
| # | Item | Why it matters | Where |
|---|------|----------------|-------|
| 1 | **Re-enable Firebase billing** | Storage returns `402 billing account disabled` → no project photos; Cloud Functions can't deploy; Secret Manager blocked | console.cloud.google.com/billing/linkedaccount?project=urbanprojectsmanager |
| 2 | **Twilio: Account SID (`AC…`), WhatsApp sender, Auth Token** | Bridge is built + tested (`integrations/whatsapp`, 11 tests); these are deploy-time values | Twilio Console home |
| 3 | **Instagram (Meta)** | The Graph API needs a **Facebook Page linked to @Upc.kw** (Business account) and a Meta developer app with `instagram_basic`, `instagram_manage_insights`, `pages_read_engagement` | developers.facebook.com → My Apps |
| 4 | **Rotate exposed keys** | The Claude key and the Twilio API key/secret were pasted in chat | console.anthropic.com · Twilio Console → API keys |

Manual start for Instagram today: export Insights screenshots; A14 reads the same fields
the live test used (`likes, comments, saves, shares, reach, posted`).

## Claude will do once 1–2 are done
- Deploy `integrations/whatsapp` as a gen-2 Cloud Function; point Twilio's inbound webhook at it.
- Move all secrets to Secret Manager; agents read them at runtime.
- Cloud Scheduler: daily brief (A8), follow-ups (A4), weekly Instagram analysis (A14 → A15).
- Enable Firestore Point-in-Time Recovery (7-day undo) before agents write to production.
- Host the console on Firebase Hosting under your domain (same data, your login).
- Approval gate stays: quotations, first replies to new leads, and posts wait for **Do now**.

## Agents you don't have yet (recommended, in order)
1. **Procurement** — approved BOQ → supplier RFQs → compare against your rate library → POs.
2. **Collections** — milestone/payment due tracking, reminders, weekly receivables.
3. **Safety & Quality** — site photos → PPE/scaffold/curing flags; spec check before payment.
4. **Client Reporting** — weekly client update (photos, next steps, money) after your approval.
5. **Tender Finder** — scans Kuwait tenders, scores fit, pre-fills submissions.
6. **Permits & Documents** — licence/insurance/permit expiry; municipality file per project.
7. **Workforce** — contractor scorecards, attendance from daily reports, pay-vs-progress.

## Model policy in force
Haiku 4.5 for chat/classification (A3, A4, A5, A9, A10, A11, A12, A14, A16); Sonnet 5 for
reasoning (A6, A8, A13, A15); Opus 5 for drawing vision (A1, A2) and the client-facing
quotation (A7). The costing engine never calls a model.
