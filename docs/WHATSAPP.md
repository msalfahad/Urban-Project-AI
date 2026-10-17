# WhatsApp bridge (Twilio → A5 / A3)

Connects an inbound Twilio WhatsApp message to the agents and replies in Arabic.

```
WhatsApp user ──▶ Twilio ──(signed POST)──▶ bridge ──▶ A5 (FAQ) or A3 (conversation) ──▶ TwiML reply ──▶ Twilio ──▶ user
```

- **A5 (FAQ)** answers plain questions (timeline, permits, payments, warranty).
- **A3 (conversation)** qualifies a lead (area, floors, contract form) and hands off
  to a human when unsure.
- No price is ever quoted or computed here — that stays with A7 and your approval.
- Signature verification rejects any request that isn't really from Twilio.

## Why it can't run from the build session
This repo's session has **no public URL** (Twilio needs a callback address) and its
**egress to `api.twilio.com` is blocked** by the org policy. So the bridge is built
and tested here, and **deployed** to a public endpoint — ideally on the same
Firebase/Google Cloud project your data already lives in.

## Configuration (environment only — nothing hard-coded)
| Var | Purpose |
|-----|---------|
| `ANTHROPIC_API_KEY` | model key — store in Secret Manager, not in code |
| `TWILIO_AUTH_TOKEN` | account Auth Token — verifies inbound signatures |
| `WHATSAPP_PUBLIC_URL` | the exact public URL Twilio POSTs to (used in the signature) |
| `WHATSAPP_MODEL` | optional model id (default `claude-haiku-4-5`, the cheap tier) |
| `WHATSAPP_VALIDATE` | `0` disables signature checks — local testing only |

> Sending replies via TwiML uses your API key implicitly through Twilio; if you later
> switch to the REST API for outbound (media, templates), you'll also need
> `TWILIO_ACCOUNT_SID` (`AC…`) and the API key SID/secret already stored in `.secrets/`.

## Deploy (Cloud Run / Cloud Functions gen2)
From the repo root (so `agents/` and `engine/` ship with it):

```bash
gcloud functions deploy urban-whatsapp \
  --gen2 --runtime=python311 --region=us-central1 \
  --source=. --entry-point=whatsapp --trigger-http --allow-unauthenticated \
  --set-secrets=ANTHROPIC_API_KEY=ANTHROPIC_API_KEY:latest,TWILIO_AUTH_TOKEN=TWILIO_AUTH_TOKEN:latest \
  --set-env-vars=WHATSAPP_PUBLIC_URL=https://REGION-PROJECT.cloudfunctions.net/urban-whatsapp
```
`entry-point` is `whatsapp` in `integrations/whatsapp/app.py`. (Requires the Blaze
plan / active billing — the same billing that must be re-enabled for Storage.)

Local smoke test with the functions framework:
```bash
pip install -r integrations/whatsapp/requirements.txt
WHATSAPP_VALIDATE=0 functions-framework --target=whatsapp --source=integrations/whatsapp/app.py
curl -X POST localhost:8080 -d 'Body=كم المدة؟' -d 'From=whatsapp:+96599999999'
```

## Point Twilio at it
1. Twilio Console → **Messaging → Try it out → WhatsApp Sandbox** (fastest), or your
   approved WhatsApp Business sender.
2. Set **"When a message comes in"** to the deployed URL, method **HTTP POST**.
3. Sandbox only: join by sending the `join <code>` word from your phone first.
4. Send a message; the bridge replies in Arabic.

## Security
- Signatures are verified with `TWILIO_AUTH_TOKEN` — forged posts get `403`.
- Keys live in Secret Manager / `.secrets/` (gitignored), never in the repo.
- The API key/secret shared during setup was exposed in chat — rotate it in the
  Twilio Console once deployment is confirmed.
