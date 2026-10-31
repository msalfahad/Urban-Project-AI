"""T-386 provenance guard: a figure from Urban's own cost record is never attributed to the freelancer.

Problem (Checker O-T384-C1): research text called rows of 'Alsenan Chalet_by_category.xlsx' (Urban Projects' own
'Cost By Category' record, the xlsx form of the web-app report hashed as WEB in
tests/alsenan/registers_b1/BENCHMARK_SOURCE_MANIFEST.json, kind WEB_APP_COMMERCIAL_REPORT) "the freelancer's", and
framed one of its counts as an engine-vs-freelancer residual. The register WEB_APP_ROWS.json maps those rows to
NO_FREELANCER_ITEM / LUMP_SUM with no freelancer source cell: the freelancer has no such item.

Rule R-T386-1 (research and tests text, any villa): every compared figure names its source class from the benchmark
manifest (FREELANCER_MANUAL_QS / URBAN_COST_RECORD / DRAWING / OWNER RULE); a row whose register entry has no freelancer
source cell is never labelled the freelancer's; a figure that is not a measured quantity of a known basis is compared as
UNRESOLVED scope, never as a residual of the engine, and agreement with any benchmark is never proof (ERS s.2.4).

This scanner finds the text pattern that broke the rule: a line naming the freelancer together with the cost-record
workbook, or with the label of a cost-record row that has no freelancer item, without saying that it is NOT the
freelancer's. Hits already classified are listed in PROVENANCE_BASELINE_T386.json; any other hit fails the test.
The scanner prints file:line and the pattern only, never a figure.
"""

from __future__ import annotations

import json
import os
import re
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REGISTER = os.path.join("tests", "alsenan", "registers_b1", "WEB_APP_ROWS.json")
MANIFEST = os.path.join("tests", "alsenan", "registers_b1", "BENCHMARK_SOURCE_MANIFEST.json")
BASELINE = os.path.join(HERE, "PROVENANCE_BASELINE_T386.json")

SCAN_DIRS = ("research", "tests")
TEXT_EXT = (".md", ".py", ".json", ".csv", ".txt")
SKIP = ("research/agents_t386/", "tests/t386_", "research/external_engine_lab/alsenan_phase_b1.py")

FREELANCER = re.compile(r"freelancer", re.I)
COST_RECORD_FILE = re.compile(r"by[_ ]category|cost by category", re.I)
# Labels of cost-record rows with NO freelancer item, as substrings of the register's NFKC description (word order in
# the PDF extraction is not reliable, so single words). Each is anchored to its register row by the tests.
COST_RECORD_ONLY_TOKENS = {"شاور": "WEB-018", "صفايات": "WEB-019", "تانكي": "WEB-057"}
# A line that says the source is NOT the freelancer's is the correct statement, not a hit.
NEGATION = re.compile(r"not (the |a )?freelancer|neither the freelancer|no freelancer|NO_FREELANCER|"
                      r"owner cost record|urban cost record|URBAN_COST_RECORD|urban projects' own|not his|no row",
                      re.I)


def _nfkc(s: str) -> str:
    return unicodedata.normalize("NFKC", s)


def scan_text(text: str) -> list[tuple[int, str]]:
    """(line number, pattern) for each line that attributes a cost-record figure to the freelancer."""
    hits = []
    for n, line in enumerate(text.splitlines(), 1):
        if not FREELANCER.search(line) or NEGATION.search(line):
            continue
        norm = _nfkc(line)
        if COST_RECORD_FILE.search(norm):
            hits.append((n, "COST_RECORD_FILE_AS_FREELANCER"))
        elif any(t in norm for t in COST_RECORD_ONLY_TOKENS):
            hits.append((n, "COST_RECORD_ROW_AS_FREELANCER"))
    return hits


def scan_file(path: str) -> list[tuple[int, str]]:
    try:
        with open(path, encoding="utf-8") as fh:
            return scan_text(fh.read())
    except (UnicodeDecodeError, OSError):
        return []


def scan_tree(root: str = ROOT) -> dict[str, list[tuple[int, str]]]:
    found = {}
    for d in SCAN_DIRS:
        for dp, dns, fns in os.walk(os.path.join(root, d)):
            dns[:] = sorted(x for x in dns if not x.startswith(".") and x != "__pycache__")
            for fn in sorted(fns):
                if not fn.endswith(TEXT_EXT):
                    continue
                rel = os.path.relpath(os.path.join(dp, fn), root).replace(os.sep, "/")
                if rel.startswith(SKIP):
                    continue
                h = scan_file(os.path.join(dp, fn))
                if h:
                    found[rel] = h
    return found


def unlisted(found: dict, baseline: dict) -> list[str]:
    files = baseline.get("files", {})
    return sorted(rel for rel in found if rel not in files or not files[rel].get("class"))


def load_baseline(path: str = BASELINE) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def register_rows(root: str = ROOT) -> dict[str, dict]:
    with open(os.path.join(root, REGISTER), encoding="utf-8") as fh:
        return {r["id"]: r for r in json.load(fh)["rows"]}


def source_class(manifest_kind: str | None) -> str:
    """Benchmark manifest kind -> the source class a report must name. Unknown is refused, never guessed."""
    m = {"FREELANCER_MANUAL_QS": "FREELANCER", "WEB_APP_COMMERCIAL_REPORT": "URBAN_COST_RECORD"}
    if manifest_kind not in m:
        raise ValueError(f"source kind {manifest_kind!r} not in the benchmark manifest: name it before comparing")
    return m[manifest_kind]


def comparison_class(source: str, register_row: dict | None, basis_known: bool) -> str:
    """How a benchmark figure may be compared with a drawn / engine quantity (ERS s.2.4).

    FREELANCER with a known basis -> RECONCILE (decompose to named causes; agreement is never proof);
    any figure whose basis or unit is not defined -> UNRESOLVED_SCOPE (never a residual of the engine);
    a cost-record row with no freelancer source cell is never a FREELANCER figure.
    """
    if source == "FREELANCER" and register_row is not None and not register_row.get("source_freelancer_items"):
        raise ValueError(f"{register_row.get('id')}: register maps it to {register_row.get('mapping_class')} with no "
                         "freelancer source cell: it is not the freelancer's figure")
    if not basis_known:
        return "UNRESOLVED_SCOPE"
    return "RECONCILE"


if __name__ == "__main__":
    f = scan_tree()
    b = load_baseline()
    print(json.dumps({"files": len(f), "hits": sum(len(v) for v in f.values()), "unlisted": unlisted(f, b),
                      "by_file": {k: [n for n, _ in v] for k, v in f.items()}}, indent=1))
