"""WhatsApp ⇄ agents bridge — framework-neutral core.

Twilio delivers each inbound WhatsApp message as a signed HTTP POST. This module
verifies that signature, routes the text to the right agent (A5 for a plain FAQ,
A3 for a qualifying conversation), and returns the Arabic reply as TwiML.

It follows the house rule: the agents read and write text; no price is computed
here, and A3/A5 hand off to a human when they are unsure. The model calls are the
same injectable seam as everywhere else, so this whole file runs offline in tests
with stub models and no network.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
from dataclasses import dataclass
from typing import Callable
from xml.sax.saxutils import escape

from agents.a3_client.agent import run as run_a3
from agents.a3_client.schema import Message
from agents.a5_faq.agent import run as run_a5
from agents.a5_faq.schema import FAQInput

ModelFn = Callable[[str, str], str]

# When A3/A5 defer to a person, we tell the client plainly rather than guess.
HANDOFF_AR = "شكراً لك 🙏 سيتواصل معك أحد مهندسي أوربان لمتابعة طلبك."

# Words that mark a plain informational question → route to the FAQ agent (A5).
# Anything else is a qualifying conversation → A3.
_FAQ_HINTS_AR = (
    "كم المدة", "مدة", "مدة التنفيذ", "الترخيص", "رخصة", "تصريح",
    "الدفعات", "الدفع", "دفعة", "الضمان", "ضمان", "المستندات", "الأوراق",
    "كيف تبدأ", "الخطوات", "خطوات",
)
_FAQ_HINTS_EN = (
    "how long", "timeline", "duration", "permit", "license", "licence",
    "payment", "instalment", "installment", "warranty", "guarantee",
    "documents", "paperwork", "process", "steps",
)


def verify_twilio_signature(auth_token: str, url: str, params: dict, signature: str) -> bool:
    """Validate Twilio's ``X-Twilio-Signature`` for an inbound webhook.

    Twilio signs ``url`` + every POST parameter sorted by key and concatenated as
    ``key + value`` (no separators), HMAC-SHA1 with the account auth token, then
    base64. See Twilio Security docs. Comparison is constant-time.
    """
    if not auth_token or not signature:
        return False
    payload = url + "".join(f"{k}{params[k]}" for k in sorted(params))
    digest = hmac.new(auth_token.encode("utf-8"), payload.encode("utf-8"), hashlib.sha1).digest()
    expected = base64.b64encode(digest).decode("ascii")
    return hmac.compare_digest(expected, signature)


def is_faq(text: str) -> bool:
    t = (text or "").strip().lower()
    if not t:
        return False
    if any(h in text for h in _FAQ_HINTS_AR):
        return True
    return any(h in t for h in _FAQ_HINTS_EN)


def _looks_arabic(text: str) -> bool:
    return any("؀" <= ch <= "ۿ" for ch in (text or ""))


@dataclass
class Reply:
    text: str
    route: str            # "faq" | "conversation"
    needs_human: bool = False


def reply_for(
    text: str,
    history: list[dict] | None = None,
    *,
    model_faq: ModelFn,
    model_conv: ModelFn,
) -> Reply:
    """Produce the Arabic reply for one inbound message by running the right agent."""
    history = history or []
    if is_faq(text):
        lang = "ar" if _looks_arabic(text) else "en"
        out = run_a5(FAQInput(question=text, language=lang), model=model_faq)
        if out.needs_human:
            return Reply(HANDOFF_AR, "faq", needs_human=True)
        answer = out.answer_ar if lang == "ar" else (out.answer_en or out.answer_ar)
        return Reply(answer or HANDOFF_AR, "faq", needs_human=not answer)
    out = run_a3(Message(text=text, history=history), model=model_conv)
    needs_human = out.stage == "needs_human"
    reply = out.reply_ar
    if needs_human and out.handoff_reason:
        reply = f"{reply}\n\n{HANDOFF_AR}"
    return Reply(reply, "conversation", needs_human=needs_human)


def build_twiml(text: str) -> str:
    """Wrap a reply as a TwiML Messaging response Twilio will deliver back."""
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f"<Response><Message>{escape(text or '')}</Message></Response>"
    )


@dataclass
class HttpResult:
    status: int
    body: str
    content_type: str = "text/xml; charset=utf-8"


def handle_inbound(
    params: dict,
    *,
    url: str,
    signature: str | None,
    auth_token: str | None,
    model_faq: ModelFn,
    model_conv: ModelFn,
    validate: bool = True,
) -> HttpResult:
    """Full inbound flow: verify → run agent → TwiML.

    ``validate`` may be turned off only for local testing; in production always
    pass the account auth token so forged requests are rejected with 403.
    """
    if validate:
        if not verify_twilio_signature(auth_token or "", url, params, signature or ""):
            return HttpResult(403, "signature verification failed", "text/plain; charset=utf-8")
    body = (params.get("Body") or "").strip()
    if not body:
        # Nothing to answer (e.g. a media-only message) — acknowledge quietly.
        return HttpResult(200, build_twiml(""))
    reply = reply_for(body, model_faq=model_faq, model_conv=model_conv)
    return HttpResult(200, build_twiml(reply.text))
