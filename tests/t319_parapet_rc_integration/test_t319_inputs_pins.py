"""T-319: the development villa's V3.0.23 inputs are re-read from the checker-merged T-311 / T-324 ledgers and pinned
(an edited ledger stops the build); they load through the module's own checks; hand checks of the published bound."""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t319"))

from engine.source import arch_v3023 as A  # noqa: E402


@pytest.fixture(scope="module")
def built():
    import t319_inputs as L
    return L, L.build("development-villa-t131")


def test_inputs_load_and_pin(built):
    L, d = built
    A.load_inputs(d, "development-villa-t131")
    assert [c["chain"] for c in d["chains"]] == ["ANNEX", "GF", "1F", "2F"]
    assert sum(len(c["runs"]) for c in d["chains"]) == 25                     # 24 T-311 runs + the T-324 C5 run
    assert d["declared"]["floor_m3"] == pytest.approx(8.0509428, abs=1e-6)
    assert d["declared"]["all_rc_printed_lo_m3"] == pytest.approx(18.980938, abs=1e-5)
    assert d["declared"]["all_rc_printed_hi_m3"] == pytest.approx(20.095345, abs=1e-5)
    assert all(u["material"] == "HELD" for c in d["chains"] for u in c["runs"])
    assert d["upstand"]["status"] == A.DC and "F-T311-C1" in d["upstand"]["checker_run"]


def test_hand_checks_2f_and_annex_extension(built):
    _L, d = built
    by = {c["chain"]: c for c in d["chains"]}
    _runs, b2 = A.chain_bound(by["2F"], 0.30)
    # 2F ring (Checker's own re-measure): top 55.080 - 7.700 x 6.450 = 5.415 m2; floor 0.30 x 5.415 = 1.6245 m3;
    # all RC at b_edge 0: 5.415 x 0.50 = 2.7075 m3
    assert b2["top_m2"] == [5.415, 5.415]
    assert b2["floor_at_least_m3"] == pytest.approx(1.6245, abs=1e-6)
    assert b2["all_rc_printed_part_m3"] == [pytest.approx(2.7075), pytest.approx(2.7075)]
    ext = [u for u in by["ANNEX"]["runs"] if u["run"] == "NE-6x"]
    # C5: centreline 1.300 x 0.200 = 0.260 m2 (T-324 0.259990), h 0.50; floor 0.078 m3; block not booked (named)
    assert len(ext) == 1 and ext[0]["top_lo_m2"] == pytest.approx(0.26, abs=2e-5)
    assert ext[0]["block_alt_m2"] is None and ext[0]["block_alt_note"]


def test_strip_and_divider_excluded_by_name(built):
    _L, d = built
    what = " ".join(e["what"] for e in d["excluded"])
    assert "F-T311-C2" in what and "divider" in what
    assert all("never 0" in e["status"] for e in d["excluded"])


def test_edited_ledger_stops_the_build(built, tmp_path, monkeypatch):
    L, _d = built
    p = tmp_path / "COMPONENT_LEDGER_T324.csv"
    shutil.copy(L.COMP, p)
    txt = p.read_text(encoding="utf-8").replace("2F/SW-1/TOP_SURFACE,TOP_SURFACE,m2,1.580000,1.580000",
                                                "2F/SW-1/TOP_SURFACE,TOP_SURFACE,m2,1.680000,1.680000")
    p.write_text(txt, encoding="utf-8")
    monkeypatch.setattr(L, "COMP", p)
    with pytest.raises(SystemExit, match="pinned"):
        L.build("development-villa-t131")
