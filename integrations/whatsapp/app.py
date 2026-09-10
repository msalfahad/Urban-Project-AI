"""HTTP entrypoint for the WhatsApp bridge (Cloud Run / Cloud Functions gen2).

Deploy with the `functions-framework` (``functions-framework --target=whatsapp``)
or as a Firebase 2nd-gen Python HTTPS function that calls ``whatsapp(request)``.

Configuration comes only from the environment — nothing is hard-coded:
  ANTHROPIC_API_KEY        the model key (store in Secret Manager)
  TWILIO_AUTH_TOKEN        account auth token, used to verify inbound signatures
  WHATSAPP_PUBLIC_URL      the exact public URL Twilio posts to (for signature)
  WHATSAPP_MODEL           optional model id override (default: cheap Haiku)
  WHATSAPP_VALIDATE        "0" disables signature checks (local testing only)

The reply agents run on the cheap/fast model per the model policy — no effort
knob (Haiku rejects it), no heavy reasoning for a chat turn.
"""

from __future__ import annotations

import os

from agents.base import anthropic_model
from .bridge import handle_inbound

# Cheap, fast model for high-volume chat (extraction/classification tier).
DEFAULT_MODEL = os.environ.get("WHATSAPP_MODEL", "claude-haiku-4-5-20251001")


def _model(system: str, user: str) -> str:
    # effort=None: Haiku-class models don't accept output_config effort.
    return anthropic_model(system, user, model=DEFAULT_MODEL, effort=None)


def whatsapp(request):
    """functions-framework HTTP handler. `request` is a Flask/Werkzeug request."""
    params = request.form.to_dict() if hasattr(request, "form") else dict(request.get("params", {}))
    signature = request.headers.get("X-Twilio-Signature") if hasattr(request, "headers") else None
    url = os.environ.get("WHATSAPP_PUBLIC_URL") or (getattr(request, "url", "") or "")
    validate = os.environ.get("WHATSAPP_VALIDATE", "1") != "0"

    result = handle_inbound(
        params,
        url=url,
        signature=signature,
        auth_token=os.environ.get("TWILIO_AUTH_TOKEN"),
        model_faq=_model,
        model_conv=_model,
        validate=validate,
    )
    return (result.body, result.status, {"Content-Type": result.content_type})
