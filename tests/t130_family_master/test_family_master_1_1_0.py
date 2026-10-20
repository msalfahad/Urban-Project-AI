"""T-130: BOQ_FAMILY_MASTER 1.1.0 (rules/coverage/) - the family registry re-derived from the code and the runs.

Checks the file only (it is read by no engine module yet: the census and rule_store keep 1.0.0, so no run changes):
the same 99 families as 1.0.0 with their names / units untouched, every status in the registry's own vocabulary,
every status change carrying a file:line that resolves or a merge commit, every file:line in the evidence resolving
to an existing line, the V3.0 field in its vocabulary, development-villa figures that never turn a held line into a
quantity, and no benchmark (freelancer) number or client name in the rule store."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.1.0.json"
OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.0.0.json"
REF = re.compile(r"((?:engine|tools|tests|research|rules|knowledge)/[\w/.]+\.(?:py|json|md))(?::(\d+)(?:-(\d+))?)?")
COMMIT = re.compile(r"\b[0-9a-f]{7}\b")
UNITS = {"m", "m2", "m3", "lm", "pcs", "kg", "t", "nr", "item", "-"}


@pytest.fixture(scope="module")
def new():
    return json.loads(NEW.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def old():
    return json.loads(OLD.read_text(encoding="utf-8"))


def test_same_families_names_and_units_as_1_0_0(new, old):
    assert new["master"] == old["master"] and new["version"] == "1.1.0"
    assert new["capability_states"] == old["capability_states"]
    assert [f["code"] for f in new["families"]] == [f["code"] for f in old["families"]]
    for a, b in zip(new["families"], old["families"]):
        for k in ("group", "item_en", "item_ar", "unit", "source_needed", "next_slice"):
            assert a[k] == b[k], (a["code"], k)
        assert a["capability_1_0_0"] == b["capability"], a["code"]


def test_status_vocabulary_and_change_direction(new):
    rank = {s: i for i, s in enumerate(new["capability_states"])}
    assert set(new["capability_definitions"]) == set(rank)
    for f in new["families"]:
        assert f["capability"] in rank, f["code"]
        c0, c1 = rank[f["capability_1_0_0"]], rank[f["capability"]]
        want = "UNCHANGED" if c0 == c1 else ("RAISED" if c1 < c0 else "LOWERED")
        assert f["capability_change"] == want, f["code"]


def _resolves(m):
    p = ROOT / m.group(1)
    if not p.exists():
        return False
    if m.group(2):
        last = int(m.group(3) or m.group(2))
        return int(m.group(2)) >= 1 and last <= len(p.read_text(encoding="utf-8").splitlines())
    return True


def test_every_file_line_in_the_evidence_resolves(new):
    bad = []
    for f in new["families"]:
        for text in f["evidence"] + [f["missing"], f.get("note", "")]:
            bad += [(f["code"], m.group(0)) for m in REF.finditer(text) if not _resolves(m)]
    for text in new["census_gaps"] + [new["loaded_by"], new["released_configuration"]]:
        bad += [("top", m.group(0)) for m in REF.finditer(text) if not _resolves(m)]
    assert not bad


def test_no_status_changes_without_a_file_line_or_a_commit(new):
    for f in new["families"]:
        if f["capability_change"] == "UNCHANGED":
            continue
        assert any(REF.search(e) and ":" in REF.search(e).group(0) or COMMIT.search(e) for e in f["evidence"]), f["code"]


def test_v3_0_field(new):
    for f in new["families"]:
        assert f["in_v3_0_candidate"] in ("yes", "no"), f["code"]
        assert all(re.fullmatch(r"T-\d{3}", t) for t in f["v3_0_planned_tasks"]), f["code"]
        if f["capability"] in ("NOT_IMPLEMENTED", "BLOCKED_BY_SOURCE", "EXPERIMENTAL"):
            assert f["in_v3_0_candidate"] == "no", f["code"]


def test_development_villa_figures_never_turn_held_into_a_quantity(new):
    for f in new["families"]:
        for run in ("released_run", "candidate_run_v2_13"):
            for r in f["development_villa"][run]:
                assert r["unit"] in UNITS and "," not in r["unit"], (f["code"], r)   # one unit per row, never mixed
                assert r["released_lines"] + r["held_lines"] + r["not_applicable_lines"] == r["lines"], (f["code"], r)
                if r["released_lines"] == 0:
                    assert r["released_qty"] == 0, (f["code"], r)                    # held lines add nothing
                lo, hi = r["held_bounded_low"], r["held_bounded_high"]
                assert (lo is None) == (hi is None) and (lo is None or 0 <= lo <= hi), (f["code"], r)


def test_status_and_run_agree_where_the_released_run_releases(new):
    """a family with released lines in the released run is at least PARTIAL; one the released route never reads is
    at most IMPLEMENTED_NOT_INTEGRATED"""
    rank = {s: i for i, s in enumerate(new["capability_states"])}
    for f in new["families"]:
        if any(r["released_lines"] for r in f["development_villa"]["released_run"]):
            assert rank[f["capability"]] <= rank["PARTIAL"], f["code"]
        if f["released_method_reads"].startswith("none") and f["code"] not in ("B9-05", "B11-02"):
            assert rank[f["capability"]] >= rank["IMPLEMENTED_NOT_INTEGRATED"], f["code"]


def test_the_engine_still_reads_1_0_0(new):
    from engine.source import rule_store as RS
    assert RS.family_master()["version"] == "1.0.0"          # adopting 1.1.0 is a census version of its own
    assert "1.0.0" in new["loaded_by"]


def test_no_benchmark_number_or_client_name_in_the_rule_store():
    text = NEW.read_text(encoding="utf-8")
    assert not re.search(r"(?i:als[ey]?n[ya]?an)|YEARS 2013|7757-[A-Z]", text)
    for n in ("44.19", "352.436075", "77.6305", "75.09", "39.7515", "65.965875", "59.8174", "21.8328", "12.348",
              "337.812", "333.173", "22.619", "22.916"):
        assert n not in text
