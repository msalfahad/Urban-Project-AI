"""Documents CLI — job round-trip, write with a stubbed writer, re-render."""

import json

import pytest

from agents.a7_quotation.schema import DocumentOutput
from tools import documents as cli

BODY = {
    "intro_ar": "يسر شركة إيربن بروجكتس أن تقدم لكم عرض سعر.",
    "scope_ar": "هيكل أسود + عازل سرداب + صحي",
    "sections": [{"title_ar": "التجهيزات الموقعية",
                  "groups": [{"heading_ar": "", "items": ["توفير مهندس موقع."]}]}],
    "exclusions_ar": ["أعمال التشطيبات"],
    "owner_obligations_intro_ar": "يتعهد الطرف الأول بتسليم المواد المدعومة.",
    "contract_terms_ar": ["تُدفع قيمة العقد حسب جدول الدفعات."],
    "closing_ar": "آملين أن ينال عرضنا رضاكم",
}


@pytest.fixture
def job(tmp_path):
    path = tmp_path / "job.json"
    path.write_text(json.dumps(cli.EXAMPLE_JOB, ensure_ascii=False), encoding="utf-8")
    return path


@pytest.fixture(autouse=True)
def stub_writer(monkeypatch):
    monkeypatch.setattr(cli, "a7", lambda doc, model=None: DocumentOutput.from_dict(BODY))


def test_example_job_prints_valid_json(capsys):
    cli.main(["example-job", "--kind", "contract"])
    data = json.loads(capsys.readouterr().out)
    assert data["kind"] == "contract" and data["price_lines"]


def test_load_job_builds_reference_from_sequence(job):
    doc = cli.load_job(job)
    assert doc.reference.startswith("UP/") and doc.reference.endswith("-001-R01")
    assert doc.project.scopes == ["black_structure", "basement_waterproofing", "plumbing"]


def test_load_job_keeps_explicit_reference(tmp_path):
    data = dict(cli.EXAMPLE_JOB, reference="UP/2026-9-077-R03")
    path = tmp_path / "j.json"
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    assert cli.load_job(path).reference == "UP/2026-9-077-R03"


def test_write_saves_body_and_html(job, tmp_path, capsys):
    out = tmp_path / "out"
    cli.main(["write", "--job", str(job), "--out", str(out), "--no-pdf"])
    files = {p.name for p in out.iterdir()}
    stem = cli.load_job(job).reference.replace("/", "-")
    assert f"{stem}.body.json" in files and f"{stem}.html" in files
    html = (out / f"{stem}.html").read_text(encoding="utf-8")
    assert "110,400.000 د.ك" in html
    assert "فقط مائة وعشرة آلاف وأربعمائة دينار كويتي لا غير" in html
    assert "html" in capsys.readouterr().out


def test_render_reprints_an_edited_body(job, tmp_path):
    out = tmp_path / "out"
    cli.main(["write", "--job", str(job), "--out", str(out), "--no-pdf"])
    stem = cli.load_job(job).reference.replace("/", "-")
    body_path = out / f"{stem}.body.json"

    body = json.loads(body_path.read_text(encoding="utf-8"))
    body["closing_ar"] = "نأمل أن ينال عرضنا رضاكم — نسخة معدلة"
    body_path.write_text(json.dumps(body, ensure_ascii=False), encoding="utf-8")

    cli.main(["render", "--job", str(job), "--body", str(body_path), "--out", str(out), "--no-pdf"])
    html = (out / f"{stem}.html").read_text(encoding="utf-8")
    assert "نسخة معدلة" in html
    assert "110,400.000 د.ك" in html          # editing words cannot move the price


def test_kind_override_renders_contract(job, tmp_path):
    out = tmp_path / "out"
    cli.main(["write", "--job", str(job), "--out", str(out), "--kind", "contract", "--no-pdf"])
    stem = cli.load_job(job).reference.replace("/", "-")
    html = (out / f"{stem}.html").read_text(encoding="utf-8")
    assert "عقد مقاولة" in html and "جدول الدفعات" in html and "شاهد أول" in html


def test_edited_body_with_money_is_refused(job, tmp_path):
    out = tmp_path / "out"
    cli.main(["write", "--job", str(job), "--out", str(out), "--no-pdf"])
    stem = cli.load_job(job).reference.replace("/", "-")
    body_path = out / f"{stem}.body.json"
    body = json.loads(body_path.read_text(encoding="utf-8"))
    body["closing_ar"] = "الإجمالي 99,000 د.ك"
    body_path.write_text(json.dumps(body, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValueError, match="money in prose"):
        cli.main(["render", "--job", str(job), "--body", str(body_path), "--out", str(out), "--no-pdf"])
