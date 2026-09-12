"""Renderer + intake tests — every figure placed by code, nothing by the model."""

from datetime import date

import pytest

from agents.a7_quotation.schema import (
    DocumentInput, DocumentOutput, OwnerMaterial, Party, ProgrammeLine, ProjectFacts,
)
from documents import render
from documents.intake import (
    document_input_from_draft, price_lines_from_boq_items, price_lines_from_draft,
)
from engine.documents import Milestone, PriceLine
from engine.rate_library import RateCategory, RateItem, RateLibrary
from pipeline.create_project import create_project
from pipeline.end_to_end import TradeLine

COMPANY = {
    "name_ar": "شركة إيربن بروجكتس لتشييد المباني", "name_en": "Urban Projects",
    "paid_capital_kwd": 100000, "commercial_register": "123", "license_number": "",
    "phones": ["+965 90000000"], "email": "info@example.com", "website": "",
    "address_ar": "الكويت", "address_en": "Kuwait", "signatory_name": "م. فهد",
    "signatory_title": "المدير العام",
}


def _doc(kind="quotation", **over):
    base = dict(
        kind=kind, reference="UP/2026-9-001-R01", issued=date(2026, 9, 12),
        client=Party(name="أحمد", title="الدكتور", civil_id="2900", phone="+965 5"),
        project=ProjectFacts(
            name="فيلا العسل", location="جنوب خيطان",
            scopes=["black_structure", "plumbing"],
            floors=["سرداب", "أرضي"], built_area_m2=1632.0, plot="12",
        ),
        price_lines=[PriceLine("أعمال الهيكل الأسود", 93500.0, "بالإضافة إلى المواد المدعومة"),
                     PriceLine("أعمال الصحي", 16900.0)],
        programme=[ProgrammeLine("black_structure", 180, "تاريخ صب اللبشة المسلحة")],
        owner_materials=[OwnerMaterial("حديد تسليح كويتي", "50 طن")],
        payment_milestones=[Milestone("عند توقيع العقد", 30), Milestone("عند التسليم", 70)],
        extra_exclusions=["أعمال الكهرباء"],
    )
    base.update(over)
    return DocumentInput(**base)


def _body(**over):
    data = {
        "intro_ar": "يسر شركة إيربن بروجكتس أن تقدم لكم عرض سعر.",
        "scope_ar": "هيكل أسود + صحي",
        "sections": [
            {"title_ar": "التجهيزات الموقعية", "groups": [{"heading_ar": "", "items": ["توفير مهندس موقع."]}]},
            {"title_ar": "أعمال الهيكل الإنشائي", "groups": [
                {"heading_ar": "المواصفات الفنية للمواد", "items": ["حديد كويتي الصنع."]},
                {"heading_ar": "مواصفات الأعمال", "items": ["مراجعة المخططات."]}]},
        ],
        "exclusions_ar": ["أعمال التشطيبات"],
        "owner_obligations_intro_ar": "يتعهد الطرف الأول بتسليم المواد المدعومة.",
        "contract_terms_ar": ["تُدفع قيمة العقد حسب جدول الدفعات."],
        "closing_ar": "آملين أن ينال عرضنا رضاكم",
    }
    data.update(over)
    return DocumentOutput.from_dict(data)


# ---- numbering ----------------------------------------------------------------
def test_sections_numbered_in_order_with_appended_sections():
    ctx = render.build_context(_doc(), _body(), COMPANY)
    titles = [(s["ordinal"], s["title"]) for s in ctx["sections"]]
    assert titles == [
        ("أولاً", "التجهيزات الموقعية"),
        ("ثانياً", "أعمال الهيكل الإنشائي"),
        ("ثالثاً", "التزامات المالك"),
        ("رابعاً", "الأعمال غير المشمولة"),
        ("خامساً", "مدة التنفيذ"),
        ("سادساً", "قيمة عرض السعر"),
    ]


def test_contract_adds_terms_after_price():
    ctx = render.build_context(_doc("contract"), _body(), COMPANY)
    assert [s["title"] for s in ctx["sections"]][-2:] == ["قيمة العقد", "الشروط العامة"]


# ---- figures come from the engine --------------------------------------------
def test_price_total_and_words():
    ctx = render.build_context(_doc(), _body(), COMPANY)
    assert ctx["price"]["total"] == "110,400.000 د.ك"
    assert ctx["price"]["total_words"] == "فقط مائة وعشرة آلاف وأربعمائة دينار كويتي لا غير"
    assert ctx["price"]["lines"][0]["note"] == "بالإضافة إلى المواد المدعومة"


def test_payment_schedule_only_on_contract():
    assert render.build_context(_doc(), _body(), COMPANY)["payment"] is None
    rows = render.build_context(_doc("contract"), _body(), COMPANY)["payment"]
    assert rows[0] == {"trigger": "عند توقيع العقد", "percent": "30%", "amount": "33,120.000 د.ك"}


def test_validity_only_on_quotation():
    assert "حتى 26/09/2026" in render.build_context(_doc(), _body(), COMPANY)["validity"]
    assert render.build_context(_doc("contract"), _body(), COMPANY)["validity"] == ""


def test_duration_from_programme_not_prose():
    ctx = render.build_context(_doc(), _body(), COMPANY)
    duration = next(s for s in ctx["sections"] if s["title"] == "مدة التنفيذ")
    assert duration["groups"][0]["items"] == [
        "مدة تنفيذ أعمال الهيكل الأسود: 180 يوماً تبدأ من تاريخ صب اللبشة المسلحة."]


def test_exclusions_merge_agent_and_owner():
    ctx = render.build_context(_doc(), _body(), COMPANY)
    excl = next(s for s in ctx["sections"] if s["title"] == "الأعمال غير المشمولة")
    assert excl["groups"][0]["items"] == ["أعمال التشطيبات", "أعمال الكهرباء"]


def test_owner_materials_rendered_with_quantity():
    ctx = render.build_context(_doc(), _body(), COMPANY)
    owner = next(s for s in ctx["sections"] if s["title"] == "التزامات المالك")
    assert owner["intro"].startswith("يتعهد الطرف الأول")
    assert owner["groups"][0]["items"] == ["حديد تسليح كويتي — 50 طن"]


def test_facts_table():
    ctx = render.build_context(_doc(), _body(), COMPANY)
    facts = dict(ctx["facts"])
    assert facts["التاريخ"] == "12/09/2026"
    assert facts["الإشارة"] == "UP/2026-9-001-R01"
    assert facts["عدد الأدوار"] == "سرداب + أرضي"
    assert facts["مساحة البناء"] == "1,632.00 م2"
    assert facts["العنوان"] == "جنوب خيطان — قسيمة 12"


def test_days_grammar():
    assert render._days_ar(1) == "يوم واحد"
    assert render._days_ar(2) == "يومان"
    assert render._days_ar(7) == "7 أيام"
    assert render._days_ar(180) == "180 يوماً"


# ---- html ---------------------------------------------------------------------
def test_html_carries_barcode_letterhead_and_escapes():
    doc = _doc(client=Party(name="<أحمد>", title="السيد"))
    html = render.render_html(doc, _body(), COMPANY)
    assert "<svg" in html
    assert "رأس المال المدفوع 100,000.000 د.ك" in html
    assert "&lt;أحمد&gt;" in html and "<أحمد>" not in html
    assert 'dir="rtl"' in html
    assert "Amiri-Regular.ttf" in html


def test_letterhead_lives_in_a_repeating_thead():
    # Chromium repeats a table <thead> on every printed page; a position:fixed
    # header does not print where CSS says it should. The letterhead must sit
    # inside <thead> or it lands over the body text on every page.
    html = render.render_html(_doc(), _body(), COMPANY)
    head = html.split("</thead>")[0]
    assert "<thead>" in head and 'class="letterhead"' in head and "<svg" in head
    assert "position: fixed" not in html


def test_contract_html_has_parties_and_witnesses():
    html = render.render_html(_doc("contract"), _body(), COMPANY)
    assert "الطرف الأول (المالك)" in html and "الطرف الثاني (المقاول)" in html
    assert "الرقم المدني" in html and "شاهد أول" in html
    assert "صلاحية العرض" not in html


def test_quotation_html_has_salutation_and_validity():
    html = render.render_html(_doc(), _body(), COMPANY)
    assert "الدكتور / أحمد" in html and "المحترم" in html
    assert "صلاحية العرض" in html and "شاهد أول" not in html


def test_find_chromium_env_override(monkeypatch):
    monkeypatch.setenv("URBAN_CHROMIUM", "/x/chrome")
    assert render.find_chromium() == "/x/chrome"


# ---- intake -------------------------------------------------------------------
def test_price_lines_from_boq_items_uses_app_formula():
    items = [
        {"packageName": "أعمال الهيكل الأسود", "formulaType": "volume",
         "measurements": {"length": 10, "width": 2, "height": 0.5}, "sellingRate": 100},
        {"packageName": "أعمال الهيكل الأسود", "formulaType": "simple",
         "measurements": {"qty": 3}, "sellingRate": 500},
        {"packageName": "أعمال الصحي", "formulaType": "area",
         "measurements": {"length": 4, "width": 5}, "sellingRate": 10},
        {"packageName": "محذوف", "formulaType": "simple", "measurements": {"qty": 1},
         "sellingRate": 999, "isDeleted": True},
    ]
    lines = price_lines_from_boq_items(items)
    assert [(l.package, l.amount_kwd) for l in lines] == [
        ("أعمال الهيكل الأسود", 2500.0), ("أعمال الصحي", 200.0)]


def test_price_lines_from_boq_items_refuses_unpriced():
    with pytest.raises(ValueError, match="sellingRate is zero"):
        price_lines_from_boq_items([{"packageName": "x", "formulaType": "simple",
                                     "measurements": {"qty": 1}, "sellingRate": 0}])


def _draft():
    rates = RateLibrary(categories=[RateCategory("c", items=[
        RateItem("خرسانه", "c", qty=380, unit="m3", unit_cost=28, total=10640)])])
    lines = [TradeLine("RC concrete", "p9", 352.44, "m3", "خرسانه", "m3", priced_qty=380)]
    return create_project(client_name="Fatma", project_name="Alsenan Villa",
                          trade_lines=lines, rates=rates, location="Sabah Al-Ahmad",
                          contract_form="black_structure",
                          schedule_quantities={"blockwork_m2": 1260.69})


def test_document_from_pipeline_draft():
    draft = _draft()
    assert price_lines_from_draft(draft)[0].amount_kwd == 28 * 380
    doc = document_input_from_draft(
        draft, kind="quotation", reference="UP/2026-9-002-R01", issued=date(2026, 9, 12),
        client=Party(name="فاطمة", title="السيدة"), floors=["أرضي", "أول"],
    )
    assert doc.project.scopes == ["black_structure"]
    assert doc.project.location == "Sabah Al-Ahmad"
    assert doc.programme[0].duration_days == draft.programme_weeks * 7
    assert doc.programme[0].scope == "black_structure"


def test_contract_from_draft_needs_milestones():
    with pytest.raises(ValueError, match="payment milestones"):
        document_input_from_draft(
            _draft(), kind="contract", reference="r", issued=date(2026, 9, 12),
            client=Party(name="x"))
