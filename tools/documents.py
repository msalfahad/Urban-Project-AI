"""Write a quotation or contract for a client (A7 + E22 + the renderer).

    python -m tools.documents example-job > job.json         # a filled spec to edit
    python -m tools.documents write  --job job.json --out out/
    python -m tools.documents render --job job.json --body out/UP-2026-9-001-R01.body.json --out out/

`write` calls A7 for the Arabic body, saves it as `<ref>.body.json`, and renders
`<ref>.html` and `<ref>.pdf`. Edit the body file by hand and use `render` to
re-print it without another model call — the figures come from the job file
either way, so editing words can never change a price.

The job file is a `DocumentInput` as JSON; `example-job` prints one.
Live `write` needs ANTHROPIC_API_KEY. PDF needs Chromium (set URBAN_CHROMIUM
if it is not under /opt/pw-browsers); `--no-pdf` stops at HTML.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from datetime import date
from pathlib import Path

from agents.a7_quotation.agent import run as a7
from agents.a7_quotation.schema import (
    DocumentInput, DocumentOutput, OwnerMaterial, Party, ProgrammeLine, ProjectFacts,
)
from documents.render import render_html, render_pdf
from engine.documents import Milestone, PriceLine, reference_number

EXAMPLE_JOB = {
    "kind": "quotation",
    "sequence": 1,
    "revision": 1,
    "issued": date.today().isoformat(),
    "client": {"title": "السيد", "name": "اسم العميل", "civil_id": "", "phone": "", "address": ""},
    "project": {
        "name": "فيلا سكن خاص",
        "description": "فيلا سكن خاص",
        "location": "جنوب خيطان",
        "plot": "",
        "floors": ["سرداب", "أرضي", "ميزانين", "أول", "ثاني", "سطح"],
        "built_area_m2": 1632.0,
        "scopes": ["black_structure", "basement_waterproofing", "plumbing"],
    },
    "price_lines": [
        {"package": "أعمال الهيكل الأسود", "amount_kwd": 93500.0,
         "note": "بالإضافة إلى المواد المدعومة الخاصة بالهيكل الأسود"},
        {"package": "أعمال الصحي", "amount_kwd": 16900.0, "note": ""},
    ],
    "programme": [
        {"scope": "black_structure", "duration_days": 180, "starts_from": "تاريخ صب اللبشة المسلحة"},
        {"scope": "plumbing", "duration_days": 60, "starts_from": "الجدول الزمني المتفق عليه مع العميل"},
    ],
    "owner_materials": [
        {"item": "حديد تسليح كويتي بأقطار مختلفة حسب الحاجة", "quantity": "50 طن"},
        {"item": "خرسانة جاهزة من إحدى الشركات المعتمدة", "quantity": "بقيمة 9,000 د.ك"},
        {"item": "طابوق أسود خرساني", "quantity": "بقيمة 1,350 د.ك"},
        {"item": "طابوق أبيض وارد أسيكو أو الصناعات الوطنية", "quantity": "بقيمة 1,400 د.ك"},
        {"item": "أسمنت أسود", "quantity": "500 كيس"},
    ],
    "payment_milestones": [
        {"trigger": "عند توقيع العقد", "percent": 10},
        {"trigger": "عند إتمام صب اللبشة المسلحة", "percent": 20},
        {"trigger": "عند إتمام صب سقف الدور الأرضي", "percent": 20},
        {"trigger": "عند إتمام صب سقف الدور الأول", "percent": 20},
        {"trigger": "عند إتمام صب سقف السطح", "percent": 15},
        {"trigger": "عند التسليم الابتدائي", "percent": 15},
    ],
    "special_requests": [
        "استخدام الشدة المعدنية في السرداب والأرضي",
        "تدعيم حوائط السرداب بشترات جاهزة",
    ],
    "extra_exclusions": [],
    "validity_days": 14,
}


def load_job(path: Path) -> DocumentInput:
    j = json.loads(Path(path).read_text(encoding="utf-8"))
    issued = date.fromisoformat(j.get("issued") or date.today().isoformat())
    reference = j.get("reference") or reference_number(
        issued, int(j.get("sequence", 1)), int(j.get("revision", 1)))
    doc = DocumentInput(
        kind=j["kind"],
        reference=reference,
        issued=issued,
        client=Party(**j["client"]),
        project=ProjectFacts(**j["project"]),
        price_lines=[PriceLine(**p) for p in j["price_lines"]],
        programme=[ProgrammeLine(**p) for p in j.get("programme", [])],
        owner_materials=[OwnerMaterial(**m) for m in j.get("owner_materials", [])],
        payment_milestones=[Milestone(**m) for m in j.get("payment_milestones", [])],
        special_requests=list(j.get("special_requests", [])),
        extra_exclusions=list(j.get("extra_exclusions", [])),
        validity_days=int(j.get("validity_days", 14)),
    )
    doc.validate()
    return doc


def load_body(path: Path) -> DocumentOutput:
    return DocumentOutput.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


def _stem(reference: str) -> str:
    return reference.replace("/", "-")


def _print(doc: DocumentInput, body: DocumentOutput, out_dir: Path, pdf: bool) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = out_dir / _stem(doc.reference)
    html = render_html(doc, body)
    html_path = stem.with_suffix(".html")
    html_path.write_text(html, encoding="utf-8")
    print(f"html  {html_path}")
    if pdf:
        pdf_path = render_pdf(html, stem.with_suffix(".pdf"))
        print(f"pdf   {pdf_path}")
    if body.missing:
        print("\nreview before sending — the writer flagged:")
        for m in body.missing:
            print(f"  - {m}")


def cmd_write(args: argparse.Namespace) -> None:
    doc = load_job(args.job)
    if args.kind:
        doc.kind = args.kind
        doc.validate()
    body = a7(doc)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    body_path = out_dir / f"{_stem(doc.reference)}.body.json"
    body_path.write_text(json.dumps(asdict(body), ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"body  {body_path}")
    _print(doc, body, out_dir, pdf=not args.no_pdf)


def cmd_render(args: argparse.Namespace) -> None:
    doc = load_job(args.job)
    if args.kind:
        doc.kind = args.kind
        doc.validate()
    _print(doc, load_body(args.body), Path(args.out), pdf=not args.no_pdf)


def cmd_example(args: argparse.Namespace) -> None:
    job = dict(EXAMPLE_JOB)
    if args.kind:
        job["kind"] = args.kind
    print(json.dumps(job, ensure_ascii=False, indent=2))


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="documents", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    w = sub.add_parser("write", help="write the Arabic body with A7 and render it")
    w.add_argument("--job", required=True, type=Path)
    w.add_argument("--out", required=True)
    w.add_argument("--kind", choices=["quotation", "contract"], help="override the job's kind")
    w.add_argument("--no-pdf", action="store_true")
    w.set_defaults(func=cmd_write)

    r = sub.add_parser("render", help="re-render a saved body without calling the model")
    r.add_argument("--job", required=True, type=Path)
    r.add_argument("--body", required=True, type=Path)
    r.add_argument("--out", required=True)
    r.add_argument("--kind", choices=["quotation", "contract"])
    r.add_argument("--no-pdf", action="store_true")
    r.set_defaults(func=cmd_render)

    e = sub.add_parser("example-job", help="print a filled job file to start from")
    e.add_argument("--kind", choices=["quotation", "contract"])
    e.set_defaults(func=cmd_example)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    sys.exit(main())
