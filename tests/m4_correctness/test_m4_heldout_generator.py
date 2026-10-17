"""The M4 variant of the synthetic generator: an untagged span of a different beam (odd seeds), a continuous beam
whose schedule prints the span sequence, and a different beam continuing the line past the printed spans (seeds 2, 3
mod 4). The other variants draw exactly as before; the M4 engine never gives an unlabelled span a wrong section and
holds what it cannot evidence with an exposure that contains the truth (seeds outside the held-out range 601-640)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

pytest.importorskip("ezdxf")

from tools import synthetic_villa as SV                     # noqa: E402

ROOT = Path(__file__).resolve().parents[2]


def _entities(text):
    i = text.index("ENTITIES")
    return text[i:text.index("ENDSEC", i)]


def _ev():
    spec = importlib.util.spec_from_file_location("m4ho", ROOT / "research/urban_engine_m4_correctness/"
                                                           "evaluate_heldout_m4.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_m4_variant_changes_only_its_own_drawings(tmp_path):
    a = SV.generate(tmp_path / "a", 11).read_text()
    b = SV.generate(tmp_path / "b", 11, m4=False).read_text()
    assert _entities(a) == _entities(b)
    t0 = json.loads((tmp_path / "a/villa_11.truth.json").read_text())
    m = SV.generate(tmp_path / "m", 11, m4=True)
    t1 = json.loads(m.with_name("villa_11.truth.json").read_text())
    assert "CB_CONCRETE" not in t0["quantities"] and t1["quantities"]["CB_SPANS"] >= 2
    assert any(b.get("type") == "B7" and not b["tagged"] for b in t1["component_list"]["beams"])
    assert "BEAM-NAME" in m.read_text() and "L1-M" in m.read_text()


@pytest.mark.parametrize("seed", [11, 14])
def test_m4_engine_never_assigns_a_wrong_section(tmp_path, seed):
    SV.generate(tmp_path, seed, m4=True)
    E = _ev()
    rec = E.score(ROOT, "V3", tmp_path, [seed])[0]
    assert rec["ok"]
    out = {x["outcome"] for x in rec["unlabelled_spans"]}
    assert rec["unlabelled_spans"] and out <= {"CORRECT", "UNRESOLVED_COVERS"}
    assert rec["cb_concrete"]["engine"] == pytest.approx(rec["cb_concrete"]["truth"], rel=1e-6)
    r = rec["beams_range"]
    assert r["low"] - 1e-6 <= r["truth"] <= r["high"] + 1e-6
