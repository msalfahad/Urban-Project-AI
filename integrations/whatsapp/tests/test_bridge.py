"""Offline tests for the WhatsApp bridge — no network, stub models."""

import json

import pytest

from integrations.whatsapp.bridge import (
    build_twiml,
    handle_inbound,
    is_faq,
    reply_for,
    verify_twilio_signature,
)


# ---- signature (Twilio's own documented vector) -------------------------------
def test_signature_matches_canonical_algorithm():
    # Twilio's documented worked-example input. The expected signature is the
    # canonical RequestValidator output (url + params sorted by key concatenated
    # as key+value, HMAC-SHA1 with the auth token, base64) — the exact steps
    # Twilio's own helper libraries use, so a match proves interop.
    url = "https://mycompany.com/myapp.php?foo=1&bar=2"
    params = {
        "CallSid": "CA1234567890ABCDE",
        "Caller": "+14158675310",
        "Digits": "1234",
        "From": "+14158675310",
        "To": "+18005551212",
    }
    sig = "GvWf1cFY/Q7PnoempGyD5oXAezc="
    assert verify_twilio_signature("12345", url, params, sig) is True
    # a different token must not verify
    assert verify_twilio_signature("wrong", url, params, sig) is False


def test_signature_rejects_tampered_body():
    url = "https://x.example/hook"
    params = {"Body": "hello", "From": "whatsapp:+96599"}
    sig = "0/KCTR6DLpKmkAf8muzZqo1nDgQ="  # wrong for this payload
    assert verify_twilio_signature("token", url, params, sig) is False


def test_signature_requires_token_and_sig():
    assert verify_twilio_signature("", "u", {}, "s") is False
    assert verify_twilio_signature("t", "u", {}, "") is False


# ---- routing ------------------------------------------------------------------
def test_faq_routing():
    assert is_faq("كم مدة تنفيذ الفيلا؟")
    assert is_faq("How long does the permit take?")
    assert not is_faq("أبغى أبني شاليه بمساحة ٤٠٠ متر")


# ---- reply flow with stub models ---------------------------------------------
def _faq_model(needs_human=False):
    return lambda s, u: json.dumps({
        "category": "timeline",
        "answer_ar": "" if needs_human else "مدة الهيكل الأسود تقديرياً من ٦ إلى ٨ أشهر حسب المساحة.",
        "needs_human": needs_human,
        "confidence": "high",
    })


def _conv_model(stage="qualifying"):
    return lambda s, u: json.dumps({
        "reply_ar": "أهلاً بك في أوربان 👋 كم مساحة الأرض وكم عدد الأدوار؟",
        "lead": {"contract_form": "black_structure", "project_type": "chalet"},
        "stage": stage,
        "handoff_reason": "" if stage != "needs_human" else "طلب خاص",
    })


def test_faq_answer_returned():
    r = reply_for("كم المدة؟", model_faq=_faq_model(), model_conv=_conv_model())
    assert r.route == "faq" and "أشهر" in r.text and not r.needs_human


def test_faq_handoff_when_unsure():
    r = reply_for("كم المدة؟", model_faq=_faq_model(needs_human=True), model_conv=_conv_model())
    assert r.needs_human and "أوربان" in r.text


def test_conversation_route_and_handoff():
    r = reply_for("أبغى أبني شاليه", model_faq=_faq_model(), model_conv=_conv_model("needs_human"))
    assert r.route == "conversation" and r.needs_human


# ---- twiml --------------------------------------------------------------------
def test_twiml_escapes_xml():
    xml = build_twiml("A < B & C > D")
    assert "&lt;" in xml and "&amp;" in xml and "<Message>" in xml


# ---- full inbound flow --------------------------------------------------------
def test_handle_inbound_validates_signature():
    res = handle_inbound(
        {"Body": "hi", "From": "whatsapp:+96599"},
        url="https://x/hook", signature="bad", auth_token="tok",
        model_faq=_faq_model(), model_conv=_conv_model(), validate=True,
    )
    assert res.status == 403


def test_handle_inbound_happy_path_no_validate():
    res = handle_inbound(
        {"Body": "كم المدة؟", "From": "whatsapp:+96599"},
        url="https://x/hook", signature=None, auth_token=None,
        model_faq=_faq_model(), model_conv=_conv_model(), validate=False,
    )
    assert res.status == 200 and "أشهر" in res.body and res.content_type.startswith("text/xml")


def test_handle_inbound_empty_body_acknowledges():
    res = handle_inbound(
        {"Body": "  ", "From": "whatsapp:+96599"},
        url="https://x/hook", signature=None, auth_token=None,
        model_faq=_faq_model(), model_conv=_conv_model(), validate=False,
    )
    assert res.status == 200 and "<Response>" in res.body
