"""T-338: the V3.0.24 project inputs come ONLY from the merged T-334 findings file, pinned by sha256 (engine ids and
quantities only, no private data). Normal: 366 fixes = 350 REBAR_FORMULA (8,311.066 kg) + 1 NA_GROSS (7.6 lm) + 15
FORMULA_END, the inputs load; adverse: an edited findings file stops the build, an unknown category stops the build."""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t338"))

import t338_inputs as L  # noqa: E402
from engine.source import arch_v3024 as A  # noqa: E402


def test_inputs_from_the_merged_findings():
    d = L.build("p")
    assert len(d["fixes"]) == 366
    assert d["declared"] == {"REBAR_FORMULA": {"lines": 350, "kg": 8311.066}, "NA_GROSS": {"lines": 1, "gross": 7.6},
                             "FORMULA_END": {"lines": 15}}
    assert d["sources"][0]["merge_commit"].startswith("39092d8d") and d["sources"][0]["sha256"] == L._PIN
    assert d["unit_mass"]["method"] == "D2_OVER_162" and d["for_lead"] == []
    assert A.load_inputs(d, "p") is d


def test_adverse_an_edited_findings_file_stops_the_build(tmp_path, monkeypatch):
    p = tmp_path / L.FINDINGS.name
    shutil.copy(L.FINDINGS, p)
    p.write_text(p.read_text(encoding="utf-8").replace("18.133", "18.134", 1) + "\n", encoding="utf-8")
    monkeypatch.setattr(L, "FINDINGS", p)
    with pytest.raises(SystemExit, match="edited findings file"):
        L.build("p")


def test_adverse_an_unknown_category_stops_the_build(monkeypatch):
    rows = L._rows()
    rows[0] = dict(rows[0], category="RANGE_EXCLUDES_NET")
    monkeypatch.setattr(L, "_rows", lambda: rows)
    with pytest.raises(SystemExit, match="no V3.0.24 kind"):
        L.build("p")
