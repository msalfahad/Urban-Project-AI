"""Render a quotation or contract: A7's clauses + E22's figures -> HTML -> PDF.

`build_context` is pure and is where every figure is placed: section ordinals,
the price table and its total in words, the payment schedule, the validity
date. The template only lays out what it is given. Chromium prints the HTML
because it shapes Arabic and lays out right-to-left correctly, which no pure
Python PDF library does without a fight.
"""

from __future__ import annotations

import glob
import json
import os
from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup

from agents.a7_quotation.schema import DocumentInput, DocumentOutput
from engine.documents import (
    amount_in_words_ar, format_kwd, grand_total, ordinal_ar,
    payment_schedule, validity_expiry,
)

HERE = Path(__file__).parent
ROOT = HERE.parent
COMPANY_PATH = HERE / "company.json"
FONT_DIR = ROOT / "assets" / "fonts"

SCOPE_AR = {
    "black_structure": "الهيكل الأسود",
    "basement_waterproofing": "عازل السرداب",
    "plumbing": "الصحي",
    "electrical": "الكهرباء",
    "finishing": "التشطيبات",
    "turnkey": "تسليم المفتاح",
    "pool": "المسبح",
    "fitout": "التجهيز الداخلي",
}

TITLES = {
    "quotation": ("عرض سعر", "QUOTATION"),
    "contract": ("عقد مقاولة", "CONSTRUCTION CONTRACT"),
}

_MONTHS_AR = ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو",
              "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]
_DAYS_AR = ["الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]


def load_company(path: Path | None = None) -> dict:
    data = json.loads((path or COMPANY_PATH).read_text(encoding="utf-8"))
    data.pop("_todo", None)
    return data


def logo_svg(company: dict) -> str:
    """The company logo as inline SVG, or '' when none is configured."""
    rel = company.get("logo")
    if not rel:
        return ""
    path = Path(rel) if Path(rel).is_absolute() else ROOT / rel
    raw = path.read_text(encoding="utf-8")
    return raw[raw.find("<svg"):]


def barcode_svg(text: str) -> str:
    """A Code 128 barcode of the reference, as inline SVG."""
    import barcode
    from barcode.writer import SVGWriter

    raw = barcode.get("code128", text, writer=SVGWriter()).render({
        "module_height": 9.0, "module_width": 0.28, "quiet_zone": 1.0,
        "write_text": False, "font_size": 0, "text_distance": 0,
    }).decode("utf-8")
    # Drop the XML prologue so the SVG can sit inline in HTML.
    start = raw.find("<svg")
    return raw[start:]


def date_ar(d: date) -> str:
    return f"{_DAYS_AR[d.weekday()]} {d.day} {_MONTHS_AR[d.month - 1]} {d.year}"


def date_dmy(d: date) -> str:
    return f"{d.day:02d}/{d.month:02d}/{d.year}"


def _days_ar(n: int) -> str:
    if n == 1:
        return "يوم واحد"
    if n == 2:
        return "يومان"
    if 3 <= n <= 10:
        return f"{n} أيام"
    return f"{n} يوماً"


def build_context(doc: DocumentInput, body: DocumentOutput, company: dict) -> dict:
    """Everything the template needs, with every figure computed here."""
    doc.validate()
    body.validate()
    kind = doc.kind
    title_ar, title_en = TITLES[kind]

    sections: list[dict] = []
    for s in body.sections:
        sections.append({
            "title": s.title_ar,
            "groups": [{"heading": g.heading_ar, "items": list(g.items)} for g in s.groups],
        })

    if body.owner_obligations_intro_ar or doc.owner_materials:
        items = [f"{m.item} — {m.quantity}" for m in doc.owner_materials]
        sections.append({
            "title": "التزامات المالك",
            "intro": body.owner_obligations_intro_ar,
            "groups": [{"heading": "", "items": items}] if items else [],
        })

    exclusions = list(body.exclusions_ar) + list(doc.extra_exclusions)
    if exclusions:
        sections.append({
            "title": "الأعمال غير المشمولة",
            "groups": [{"heading": "", "items": exclusions}],
        })

    if doc.programme:
        items = [
            f"مدة تنفيذ أعمال {SCOPE_AR.get(p.scope, p.scope)}: {_days_ar(p.duration_days)}"
            f" تبدأ من {p.starts_from}."
            for p in doc.programme
        ]
        sections.append({
            "title": "مدة التنفيذ",
            "groups": [{"heading": "", "items": items}],
        })

    total = grand_total(doc.price_lines)
    price = {
        "lines": [
            {"package": l.package, "amount": format_kwd(l.amount_kwd), "note": l.note}
            for l in doc.price_lines
        ],
        "total": format_kwd(total),
        "total_words": amount_in_words_ar(total),
    }
    sections.append({
        "title": "قيمة عرض السعر" if kind == "quotation" else "قيمة العقد",
        "kind": "price",
        "groups": [],
    })

    payment = None
    if kind == "contract":
        payment = [
            {"trigger": r["trigger"], "percent": f"{r['percent']:g}%",
             "amount": format_kwd(r["amount_kwd"])}
            for r in payment_schedule(total, doc.payment_milestones)
        ]
        if body.contract_terms_ar:
            sections.append({
                "title": "الشروط العامة",
                "groups": [{"heading": "", "items": list(body.contract_terms_ar)}],
            })

    for i, s in enumerate(sections, start=1):
        s["ordinal"] = ordinal_ar(i)
        s.setdefault("kind", "text")
        s.setdefault("intro", "")

    p = doc.project
    facts = [
        ("التاريخ", date_dmy(doc.issued)),
        ("الإشارة", doc.reference),
        ("المشروع", f"{p.description} — {p.name}"),
        ("العنوان", p.location + (f" — قسيمة {p.plot}" if p.plot else "")),
        ("الأعمال المطلوبة", body.scope_ar),
    ]
    if p.floors:
        facts.append(("عدد الأدوار", " + ".join(p.floors)))
    if p.built_area_m2 is not None:
        facts.append(("مساحة البناء", f"{p.built_area_m2:,.2f} م2"))

    validity = ""
    if kind == "quotation":
        expiry = validity_expiry(doc.issued, doc.validity_days)
        validity = f"{_days_ar(doc.validity_days)} من تاريخه (حتى {date_dmy(expiry)})"

    capital = company.get("paid_capital_kwd")
    capital_line = f"رأس المال المدفوع {format_kwd(capital)}" if capital else ""

    return {
        "kind": kind,
        "title": title_ar,
        "title_en": title_en,
        "reference": doc.reference,
        "issued": date_dmy(doc.issued),
        "issued_ar": date_ar(doc.issued),
        "client": doc.client,
        "company": company,
        "capital_line": capital_line,
        "body": body,
        "facts": facts,
        "sections": sections,
        "price": price,
        "payment": payment,
        "validity": validity,
        "barcode": Markup(barcode_svg(doc.reference)),
        "logo": Markup(logo_svg(company)),
        "font_regular": (FONT_DIR / "Amiri-Regular.ttf").as_uri(),
        "font_bold": (FONT_DIR / "Amiri-Bold.ttf").as_uri(),
    }


def render_html(doc: DocumentInput, body: DocumentOutput, company: dict | None = None) -> str:
    env = Environment(
        loader=FileSystemLoader(str(HERE)),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("template_ar.html")
    return template.render(**build_context(doc, body, company or load_company()))


def find_chromium() -> str | None:
    """Playwright's own download if present, else the environment's Chromium."""
    explicit = os.environ.get("URBAN_CHROMIUM")
    if explicit:
        return explicit
    root = os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers")
    hits = sorted(glob.glob(f"{root}/chromium-*/chrome-linux/chrome"))
    return hits[-1] if hits else None


FOOTER = (
    '<div style="font-size:8.5pt;width:100%;text-align:center;color:#555;'
    'font-family:Amiri,serif;direction:rtl">'
    'صفحة <span class="pageNumber"></span> من <span class="totalPages"></span></div>'
)


def render_pdf(html: str, out_path: Path, chromium: str | None = None) -> Path:
    """Print the HTML to A4 PDF with Chromium; the letterhead repeats per page."""
    from playwright.sync_api import sync_playwright

    out_path = Path(out_path)
    html_path = out_path.with_suffix(".html")
    html_path.write_text(html, encoding="utf-8")

    launch: dict = {}
    exe = chromium or find_chromium()
    if exe:
        launch["executable_path"] = exe

    with sync_playwright() as p:
        browser = p.chromium.launch(**launch)
        page = browser.new_page()
        page.goto(html_path.resolve().as_uri())
        page.wait_for_timeout(250)
        page.pdf(
            path=str(out_path), format="A4", print_background=True,
            prefer_css_page_size=True, display_header_footer=True,
            header_template="<div></div>", footer_template=FOOTER,
        )
        browser.close()
    return out_path
