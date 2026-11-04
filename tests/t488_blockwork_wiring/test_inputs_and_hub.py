"""T-488: the V3.0.55 inputs are built only from the pinned merged files (T-482 conditions, T-449 r3 register) and load
cleanly; the hub accepts ARCH_TAKEOFF_V3.0.55 only with --v3055-inputs (a V3.0.54 run first)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t488"))

import t488_inputs as T  # noqa: E402
from engine.source import arch_v3055 as A  # noqa: E402


def test_inputs_from_the_pinned_files_load():
    d = A.load_inputs(T.build("p"), "p")
    assert [w["wall_id"] for w in d["_roof"]["walls"]] == [f"2F-W0{k}" for k in range(1, 9)]
    assert {w["evidence_status"] for w in d["_roof"]["walls"]} <= set(A.EVIDENCE)
    assert [(c["wall_id"], c["range_m2"]) for c in d["_conflicts"]] == [("GF-W22", [12.9311, 12.9439])]
    assert [(x["wall_id"], x["upper_m2"]) for x in d["_drops"]] == [("GF-W34", 10.4121)]
    assert [p["run"] for p in d["_parapets"]] == ["NW-2", "NE-6x"]
    assert set(d["_sources"]) == {"T-482", "T-449R3"}


def test_an_edited_input_stops_the_build(monkeypatch):
    monkeypatch.setitem(T.PINS, T.COND, "0" * 64)
    with pytest.raises(SystemExit, match="sha256"):
        T.build("p")


def test_hub_method_and_inputs_go_together():
    src = (ROOT / "tools/urban_boq_m9.py").read_text(encoding="utf-8")
    assert '("ARCH_TAKEOFF_V3.0.55",)' in src                                    # a method choice
    assert ('a.v3055 = getattr(a, "method", None) == "ARCH_TAKEOFF_V3.0.55"; a.method = "ARCH_TAKEOFF_V3.0.54" if '
            'a.v3055 else a.method; a.v3054 = ') in src                          # rewritten BEFORE the V3.0.54 test
    assert ('if bool(getattr(a, "v3055_inputs", None)) != a.v3055: raise SystemExit("--v3055-inputs and --method '
            'ARCH_TAKEOFF_V3.0.55 go together') in src
    i, j = src.index("if a.v3054:"), src.index("if a.v3055:")
    assert i < j and "A3055.changes_for(inp55, l3054)" in src[j:j + 4000]       # on the integrated V3.0.54 lines
