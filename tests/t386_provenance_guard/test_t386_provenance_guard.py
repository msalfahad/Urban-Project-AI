"""T-386: an Urban cost-record figure is never attributed to the freelancer, and a figure of undefined basis is compared
as UNRESOLVED scope, never as an engine residual (ERS s.2.4; Checker O-T384-C1).

Normal: a line saying the cost record is NOT the freelancer's, a genuine freelancer row (his wet-room table) and a
quantity line pass. Adverse: 'freelancer' beside the cost-record workbook or beside the label of a cost-record row with
no freelancer item is found; a NEW file carrying it is refused unless classified; a cost-record row offered as a
freelancer figure is refused; an unknown source kind is refused, never guessed. Then the repository: no unlisted hit,
T-380 corrected, the register anchors every token. Text is assembled at run time where it would match itself.
"""

import importlib.util
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _load(name, folder):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, "research", folder, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


G = _load("provenance_guard", "agents_t386")
FL = "free" + "lancer"
BYCAT = "Villa_by" + "_category.xlsx"
SHOWER_AR = "شا" + "ور"


def test_normal_lines_pass():
    text = "\n".join([
        "'" + BYCAT + "' is Urban Projects' own cost record, not the " + FL + "'s",
        "the " + FL + "'s wet-room table: GF bath rows 6, 1F 5, 2F 1",
        "drawn shower positions 6 pcs DRAWING-CONFIRMED",
        "cost record row '" + SHOWER_AR + "' (NO_" + FL.upper() + "_ITEM): UNRESOLVED scope",
    ])
    assert G.scan_text(text) == []


def test_adverse_cost_record_attributed_to_the_freelancer():
    lines = [
        "The only " + FL + " file with sanitary content is '" + BYCAT + "'",
        "| " + FL + " shower ('" + SHOWER_AR + "') | 7 qty | 4 drawn | -3 |",
        FL.upper() + " = Drive 'Villa' / 'Villa Cost By Category.pdf'",
        "his tiling labour 'تركيب " + "صفايات' counted by the " + FL,
    ]
    hits = G.scan_text("\n".join(lines))
    assert [n for n, _ in hits] == [1, 2, 3, 4]
    assert {k for _, k in hits} == {"COST_RECORD_FILE_AS_FREELANCER", "COST_RECORD_ROW_AS_FREELANCER"}


def test_new_file_is_refused_until_classified(tmp_path):
    (tmp_path / "research" / "agents_t999").mkdir(parents=True)
    (tmp_path / "tests" / "t999_x").mkdir(parents=True)
    (tmp_path / "research" / "agents_t999" / "r.md").write_text(FL + " residual: '" + SHOWER_AR + "' 7 vs 4\n", "utf-8")
    (tmp_path / "tests" / "t999_x" / "t.py").write_text("DRAWN = 4  # " + FL + " has no such row\n", "utf-8")
    found = G.scan_tree(str(tmp_path))
    assert list(found) == ["research/agents_t999/r.md"]
    assert G.unlisted(found, {"files": {}}) == ["research/agents_t999/r.md"]
    assert G.unlisted(found, {"files": {"research/agents_t999/r.md": {"class": ""}}}) == ["research/agents_t999/r.md"]
    assert G.unlisted(found, {"files": {"research/agents_t999/r.md": {"class": "PROVENANCE_MISLABEL"}}}) == []


def test_comparison_class_normal_and_adverse():
    fl_row = {"id": "X-1", "mapping_class": "FREELANCER_QTY", "source_freelancer_items": ["FIN:s:1"]}
    web_only = {"id": "X-2", "mapping_class": "NO_FREELANCER_ITEM", "source_freelancer_items": []}
    assert G.comparison_class("FREELANCER", fl_row, basis_known=True) == "RECONCILE"
    assert G.comparison_class("URBAN_COST_RECORD", web_only, basis_known=False) == "UNRESOLVED_SCOPE"
    assert G.comparison_class("FREELANCER", None, basis_known=False) == "UNRESOLVED_SCOPE"
    with pytest.raises(ValueError):
        G.comparison_class("FREELANCER", web_only, basis_known=True)       # a cost-record row offered as his
    assert G.source_class("FREELANCER_MANUAL_QS") == "FREELANCER"
    assert G.source_class("WEB_APP_COMMERCIAL_REPORT") == "URBAN_COST_RECORD"
    for bad in (None, "", "freelancer", "WEB"):
        with pytest.raises(ValueError):
            G.source_class(bad)


def test_register_anchors_the_tokens_and_the_alsenan_rows():
    rows = G.register_rows()
    for tok, rid in G.COST_RECORD_ONLY_TOKENS.items():
        r = rows[rid]
        assert tok in r["description_nfkc"] and r["mapping_class"] == "NO_FREELANCER_ITEM"
        assert r["source_freelancer_items"] == [] and r["freelancer_qty"] is None
    # the six sanitary rows T-380 compared + the shower row: none has a freelancer source cell
    for rid in ("WEB-018", "WEB-055", "WEB-056", "WEB-057", "WEB-058", "WEB-059", "WEB-060"):
        assert rows[rid]["source_freelancer_items"] == []
    with open(os.path.join(ROOT, G.MANIFEST), encoding="utf-8") as fh:
        kinds = {f["key"]: f["kind"] for f in json.load(fh)["files"]}
    assert G.source_class(kinds["WEB"]) == "URBAN_COST_RECORD"
    assert {G.source_class(k) for key, k in kinds.items() if key != "WEB"} == {"FREELANCER"}


def test_t380_is_corrected():
    A = _load("t380_alsenan", "agents_t380")
    src = A.COST_RECORD_SHOWER_SOURCE
    assert src["register_id"] == "WEB-018" and src["source_class"] == "URBAN_COST_RECORD"
    assert src["comparison"] == "UNRESOLVED_SCOPE"
    assert A.COST_RECORD_SHOWER == A.FREELANCER_SHOWER        # alias only; the quantity is unchanged
    assert not hasattr(A, "FREELANCER_SANITARY") and len(A.COST_RECORD_SANITARY) == 6
    with open(os.path.join(ROOT, "research", "agents_t380", "summary.json"), encoding="utf-8") as fh:
        s = json.load(fh)
    assert "freelancer" not in s and s["benchmark"]["freelancer"]["rows"] == 0
    assert s["benchmark"]["urban_cost_record"]["shower"]["comparison"].startswith("UNRESOLVED_SCOPE")
    with open(os.path.join(ROOT, "research", "agents_t380", "T-380_DRAINAGE_SOURCE_CENSUS.md"), encoding="utf-8") as fh:
        md = fh.read()
    assert (FL + "'s shower residual") not in md and "shower residual" not in md
    for rel in ("research/agents_t380/T-380_DRAINAGE_SOURCE_CENSUS.md", "research/agents_t380/t380_alsenan.py",
                "research/agents_t380/summary.json"):
        assert G.scan_file(os.path.join(ROOT, rel)) == []


def test_repository_has_no_unlisted_provenance_hit():
    base = G.load_baseline()
    found = G.scan_tree(ROOT)
    assert G.unlisted(found, base) == [], "cost-record figure attributed to the " + FL + ": fix it or classify it"
    # a listed file must still carry a hit: a fixed file is removed from the baseline, not left stale
    assert sorted(found) == sorted(base["files"])
    assert all(v["class"] == "PROVENANCE_MISLABEL" for v in base["files"].values())
