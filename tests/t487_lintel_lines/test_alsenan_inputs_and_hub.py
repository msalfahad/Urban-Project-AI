"""T-487: the development-villa inputs (research/agents_t487/t487_inputs.py, read from the sha-pinned merged T-453 r2
ledger and the printed schedule transcription; no private file needed) reproduce the merged ledger's totals and the
Checker's own re-measures by recomputation; the hub names ARCH_TAKEOFF_V3.0.53, runs it after the V3.0.50 step and
refuses it without its inputs (no data needed)."""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t487"))

import t487_inputs as T  # noqa: E402
from engine.source import arch_v3050 as A50  # noqa: E402
from engine.source import arch_v3053 as A  # noqa: E402
from tools import urban_boq_m9 as M  # noqa: E402


@pytest.fixture(scope="module")
def d():
    return A.load_inputs(T.build("p"), "p")


def by(d):
    return {x["opening_id"]: x for x in d["_lintels"]}


def test_decisions_and_totals_are_the_merged_ledger(d):
    assert Counter(x["decision"] for x in d["_lintels"]) == {"REQUIRED": 16, "HELD": 42, "FLAGGED": 2}
    req = [x for x in d["_lintels"] if x["decision"] == "REQUIRED"]
    assert round(sum(x["_v"] for x in req), 6) == 1.016                      # T-453 r1 / r2 summary
    assert round(sum(x["_fw"] for x in req), 6) == 14.845
    assert {x["opening_id"] for x in d["_lintels"] if x["decision"] == "FLAGGED"} == {"W13", "W26"}


def test_checker_remeasures_recomputed(d):
    """Verifier 2026-11-03 07:58 / 08:55: W14 L3 0.20 x 0.30 x 3.25 = 0.195 m3 / 2.44 m2; D-GF-06 L1 0.20 x 0.20 x 1.80 =
    0.072 m3 / 0.92 m2; faces W14 0.975 + W15 0.470 + W18 0.260 = 1.705 m2"""
    b = by(d)
    assert (b["W14"]["_v"], b["W14"]["_fw"]) == (0.195, 2.44)
    assert (b["D-GF-06"]["_v"], b["D-GF-06"]["_fw"]) == (0.072, 0.92)
    assert round(b["W14"]["_face"] + b["W15"]["_face"] + b["W18"]["_face"], 6) == 1.705
    assert all(b[k]["checker_remeasured"] for k in ("W14", "W15", "W18", "D-GF-06"))


def test_schedule_is_the_printed_one(d):
    s = d["_schedule"]
    assert s["bearing_m"] == 0.4
    assert [(r["row"], r["d_m"]) for r in s["rows"]] == [("L1", 0.2), ("L2", 0.2), ("L3", 0.3), ("L4", 0.4),
                                                         ("L5", 0.55)]


def test_evidence_status_from_the_ledger_bases(d):
    b = by(d)
    assert {k for k, x in b.items() if x["evidence_status"] == "DRAWING-CONFIRMED"} == {"W14", "W15", "W18"}
    doors = [x for x in d["_lintels"] if x["decision"] == "REQUIRED" and x["kind"] == "DOOR"]
    assert len(doors) == 13 and all(x["evidence_status"] == "ASSUMED - OWNER-APPROVED" for x in doors)
    assert all(x["evidence_status"] == "HELD" for x in d["_lintels"] if x["decision"] != "REQUIRED")


def test_host_lines_from_the_reconciliation(d):
    hosted = [x for x in d["_lintels"] if x["host_line"]]
    assert len(hosted) == 33
    assert by(d)["W14"]["host_line"] == "L-2fdc0f971a94348ec855" and by(d)["W14"]["host_net_m2"] == 101.976
    assert by(d)["D-GF-11"]["host_line"] is None                              # host wall HELD ON DROP: no line


def test_edited_input_refused(monkeypatch):
    monkeypatch.setitem(T.PINS, T.LEDGER, "0" * 64)
    with pytest.raises(SystemExit, match="sha256"):
        T.build()


FLAGS = [x for n in list(range(302, 310)) + list(range(3010, 3049)) for x in (f"--v{n}-inputs", "x.json")]


def _exit(argv, tmp_path):
    with pytest.raises(SystemExit) as e:
        M.main(["arch", "--drawings", str(tmp_path / "none.dxf"), "--out", str(tmp_path / "o")] + argv + FLAGS
               + ["--v3050-inputs", "y.json"])
    return str(e.value.code)


def test_v3053_needs_its_inputs(tmp_path):
    assert "--v3053-inputs and --method ARCH_TAKEOFF_V3.0.53 go together" in _exit(["--method", A.METHOD], tmp_path)


def test_v3053_inputs_refused_on_v3050(tmp_path):
    assert "go together" in _exit(["--method", A50.METHOD, "--v3053-inputs", "a.json"], tmp_path)


def test_hub_chains_v3053_after_v3050():
    src = (ROOT / "tools/urban_boq_m9.py").read_text(encoding="utf-8")
    i50, i53 = src.index("A3050.write("), src.index("A3053.write(")
    assert i50 < i53 and "l3050 = A3050.integrate(l3048, ch_v50, fl24)[0]" in src
    assert '("ARCH_TAKEOFF_V3.0.53",)' in src
    # a V3.0.53 run is a V3.0.50 run first: rewritten before the V3.0.50 rewrite and every stage list
    assert src.index('a.method = "ARCH_TAKEOFF_V3.0.50" if a.v3053') < src.index(
        'a.method = "ARCH_TAKEOFF_V3.0.48" if a.v3050') < src.index("v3044 = a.method in (")
