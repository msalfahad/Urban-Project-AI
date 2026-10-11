"""M6 completeness in the one-command BOQ (tools/urban_boq_m2, route G): the CLI writes the completeness register,
signals, scope checklist, review page and BOQ section E by default; --no-completeness and the library default
(compute(..., completeness=False)) leave every earlier output exactly as it was; no drawing text in Arabic reaches the
outputs; a finding never enters a total."""

from __future__ import annotations

import csv
import json
import re

import pytest

ezdxf = pytest.importorskip("ezdxf")

from tools import synthetic_villa_m6 as SM6                 # noqa: E402
from tools import urban_boq_m2 as CLI                       # noqa: E402

ARABIC = re.compile(r"[؀-ۿ]{3,}")
FILES = ("COMPLETENESS_FINDINGS.csv", "COMPLETENESS_SIGNALS.csv", "COMPLETENESS_SCOPE.csv", "COMPLETENESS_SUMMARY.json",
         "COMPLETENESS_REVIEW.html")


@pytest.fixture(scope="module")
def villa(tmp_path_factory):
    d = tmp_path_factory.mktemp("cli")
    dxf = SM6.generate(d, 2)                                    # seed 2: Arabic titles, notes, several elements
    return d, dxf


def _run(d, dxf, out, *extra):
    argv = ["run", "--drawings", str(dxf), "--out", str(out), "--profile", str(d / "villa_m6_2.profile.json"),
            "--route", "G", "--no-pdf", "--no-xlsx", "--as-of", "2026-01-01"] + list(extra)
    assert CLI.main(argv) == 0


def test_cli_writes_the_completeness_outputs(villa, tmp_path):
    d, dxf = villa
    _run(d, dxf, tmp_path / "on")
    for name in FILES:
        assert (tmp_path / "on" / name).exists(), name
    assert list((tmp_path / "on" / "completeness").glob("*.svg"))
    rows = list(csv.DictReader(open(tmp_path / "on" / "COMPLETENESS_FINDINGS.csv", encoding="utf-8")))
    assert rows and all(r["ACTION"] for r in rows)
    boq = list(csv.DictReader(open(tmp_path / "on" / "CONTRACTOR_BOQ.csv", encoding="utf-8")))
    e = [r for r in boq if r["SECTION"].startswith("E COMPLETENESS")]
    assert e and all(not r["PLANNING_BASE"] for r in e)              # never in a total
    s = json.loads((tmp_path / "on" / "SUMMARY.json").read_text(encoding="utf-8"))
    assert s["completeness"]["policy"] == "CONCRETE_COMPLETENESS_V1"
    for name in FILES + ("CONTRACTOR_BOQ.csv",):
        assert not ARABIC.search((tmp_path / "on" / name).read_text(encoding="utf-8")), name


def test_no_completeness_leaves_the_outputs_as_they_were(villa, tmp_path):
    d, dxf = villa
    _run(d, dxf, tmp_path / "off", "--no-completeness")
    for name in FILES:
        assert not (tmp_path / "off" / name).exists(), name
    s = json.loads((tmp_path / "off" / "SUMMARY.json").read_text(encoding="utf-8"))
    assert "completeness" not in s
    boq = list(csv.DictReader(open(tmp_path / "off" / "CONTRACTOR_BOQ.csv", encoding="utf-8")))
    assert not [r for r in boq if r["SECTION"].startswith("E COMPLETENESS")]
    R = CLI.compute([str(dxf)], profile=str(d / "villa_m6_2.profile.json"), route="G")
    assert "completeness" not in R["summary"] and "completeness" not in R["generic"]


def test_completeness_changes_no_quantity(villa):
    d, dxf = villa
    a = CLI.compute([str(dxf)], profile=str(d / "villa_m6_2.profile.json"), route="G")
    b = CLI.compute([str(dxf)], profile=str(d / "villa_m6_2.profile.json"), route="G", completeness=True)
    assert [(i["item_id"], i["base"]) for i in a["items"]] == [(i["item_id"], i["base"]) for i in b["items"]]
    assert a["summary"]["totals"] == b["summary"]["totals"]
