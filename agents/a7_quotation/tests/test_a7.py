"""A7 — Quotation & Contract Writer tests (offline, stub models)."""

import json
from datetime import date

import pytest

from agents.a7_quotation import agent
from agents.a7_quotation.agent import run, system_prompt
from agents.a7_quotation.schema import (
    DocumentInput, DocumentOutput, OwnerMaterial, Party, ProjectFacts,
)
from engine.documents import Milestone, PriceLine


def _input(kind="quotation", **over):
    base = dict(
        kind=kind, reference="UP/2026-9-001-R01", issued=date(2026, 9, 12),
        client=Party(name="أحمد العسل", title="الدكتور"),
        project=ProjectFacts(name="فيلا", location="جنوب خيطان",
                             scopes=["black_structure", "plumbing"], floors=["سرداب", "أرضي"]),
        price_lines=[PriceLine("أعمال الهيكل الأسود", 93500.0)],
        owner_materials=[OwnerMaterial("حديد تسليح كويتي", "50 طن")],
        payment_milestones=[Milestone("عند توقيع العقد", 100)],
        special_requests=["استخدام الشدة المعدنية في السرداب"],
    )
    base.update(over)
    return DocumentInput(**base)


def _body(**over):
    data = {
        "intro_ar": "يسر شركة إيربن بروجكتس لتشييد المباني أن تقدم لكم عرض سعر.",
        "scope_ar": "هيكل أسود + صحي",
        "sections": [
            {"title_ar": "التجهيزات الموقعية", "groups": [{"heading_ar": "", "items": ["توفير مهندس موقع."]}]},
        ],
        "exclusions_ar": ["أعمال التشطيبات"],
        "owner_obligations_intro_ar": "يتعهد الطرف الأول بتسليم المواد المدعومة.",
        "closing_ar": "آملين أن ينال عرضنا رضاكم",
    }
    data.update(over)
    return lambda s, u: json.dumps(data, ensure_ascii=False)


# ---- happy path ---------------------------------------------------------------
def test_writes_a_body():
    out = run(_input(), model=_body())
    assert out.sections[0].title_ar == "التجهيزات الموقعية"
    assert out.exclusions_ar == ["أعمال التشطيبات"]


def test_prompt_carries_facts_but_no_money():
    seen = {}

    def model(system, user):
        seen["system"], seen["user"] = system, user
        return _body()(system, user)

    run(_input(), model=model)
    assert "black_structure" in seen["user"] and "plumbing" in seen["user"]
    assert "استخدام الشدة المعدنية" in seen["user"]
    assert "حديد تسليح كويتي" in seen["user"]
    assert "93500" not in seen["user"] and "93,500" not in seen["user"]
    assert "50 طن" not in seen["user"]          # quantities are rendered by code


def test_system_prompt_includes_clause_library():
    sp = system_prompt()
    assert "مكتبة البنود القياسية" in sp
    assert "## black_structure" in sp and "## plumbing" in sp


def test_example_files_are_appended(tmp_path, monkeypatch):
    (tmp_path / "khaitan.md").write_text("# عرض سابق\nبند مميز جداً", encoding="utf-8")
    monkeypatch.setattr(agent, "EXAMPLES_DIR", tmp_path)
    sp = system_prompt()
    assert "مثال: khaitan" in sp and "بند مميز جداً" in sp


# ---- output validation --------------------------------------------------------
def test_money_in_prose_rejected():
    with pytest.raises(ValueError, match="money in prose"):
        run(_input(), model=_body(sections=[{"title_ar": "قيمة العرض", "groups": [
            {"heading_ar": "", "items": ["إجمالي الأعمال 93,500 د.ك"]}]}]))


@pytest.mark.parametrize("text", ["مبلغ 500 دينار", "KD 100", "100 KWD", "خمسمائة فلس"])
def test_currency_forms_rejected(text):
    with pytest.raises(ValueError, match="money in prose"):
        run(_input(), model=_body(closing_ar=text))


def test_spec_numbers_and_kuwaiti_steel_are_allowed():
    # "حديد كويتي" ends in د and starts the next word with ك — a naive د.ك
    # pattern read it as currency and rejected the most common spec line.
    out = run(_input(), model=_body(sections=[{"title_ar": "المواصفات", "groups": [
        {"heading_ar": "", "items": ["استخدام حديد كويتي الصنع.", "شرمات مجلفنة بسمك 1.5 مم",
                                     "ضغط 16 بار", "كفالة خمس عشرة سنة"]}]}]))
    assert len(out.sections[0].groups[0].items) == 4


def test_other_company_rejected():
    with pytest.raises(ValueError, match="Urban Projects only"):
        run(_input(), model=_body(intro_ar="يسر شركة أوج وشركة إيربن بروجكتس"))
    with pytest.raises(ValueError, match="Urban Projects only"):
        run(_input(), model=_body(intro_ar="AWJ and Urban Projects present"))


def test_empty_section_rejected():
    with pytest.raises(ValueError, match="has no items"):
        run(_input(), model=_body(sections=[{"title_ar": "فارغ", "groups": [{"heading_ar": "", "items": ["  "]}]}]))


def test_missing_intro_or_scope_rejected():
    with pytest.raises(ValueError, match="intro_ar"):
        run(_input(), model=_body(intro_ar=""))
    with pytest.raises(ValueError, match="scope_ar"):
        run(_input(), model=_body(scope_ar=""))


# ---- input validation ---------------------------------------------------------
def test_unknown_scope_rejected():
    with pytest.raises(ValueError, match="unknown scope"):
        run(_input(project=ProjectFacts(name="x", location="y", scopes=["roofing"])), model=_body())


def test_contract_needs_milestones():
    with pytest.raises(ValueError, match="payment milestones"):
        run(_input("contract", payment_milestones=[]), model=_body())


def test_bad_kind_rejected():
    with pytest.raises(ValueError, match="kind"):
        run(_input(kind="invoice"), model=_body())


def test_output_round_trips_through_json():
    out = run(_input(), model=_body())
    again = DocumentOutput.from_dict(json.loads(agent.to_json(out)))
    assert again == out
