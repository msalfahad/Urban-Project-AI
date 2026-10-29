"""Development villa pinned: the committed T-340 outputs rebuild byte for byte from the committed inputs (the merged
T-313 r2 / T-325 / T-336 / T-312 / T-329 ledgers and the V3.0.22 extract), and the engineering results the handoff
states hold (no drawing is read here)."""
import csv
import io
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t340"))
import t340_alsenan as T  # noqa: E402
import t340_binding as B  # noqa: E402


@pytest.fixture(scope="module")
def out():
    return T.outputs()


@pytest.fixture(scope="module")
def s(out):
    return json.loads(out["summary"])


def rows(out, k):
    return list(csv.DictReader(io.StringIO(out[k])))


def test_outputs_rebuild_byte_identical(out):
    for k, txt in out.items():
        assert T.OUT[k].read_text(encoding="utf-8") == txt, k


def test_candidate_of_record(s):
    assert s["candidate"]["lines_json_sha8"] == {"V3_0_20": "097a80b6", "V3_0_21": "be22a4e4", "V3_0_22": "7199c8b6"}
    assert s["rebind"]["changed"] == [] and s["rebind"]["same"] == s["rebind"]["lines"] == 92


def test_every_census_opening_once_one_owner_per_component(out, s):
    o = rows(out, "owners")
    assert s["openings"] == 59
    keys = [(r["opening"], r["comp"]) for r in o]
    assert len(keys) == len(set(keys)) == s["components"]


def test_reveal_totals(s):
    t = s["t326_reveals"]
    assert t["in_line_kept_m2"] == pytest.approx(20.22)          # 22 doors already in FIN.PLASTER (incl. D-GF-07 1.40)
    assert t["narrowed"] == ["L-2f94dca4dd5f2ec05822"]           # D-GF-07 at the printed 2.50
    assert t["new_door_rows_m2"] == pytest.approx(3.93)          # the 5 no-line doors
    assert t["new_window_out_rows_m2"] == pytest.approx(9.667)   # window outside jambs + heads
    assert "NEW:REVEAL.WINDOW_OUT|window jambs and head|W02" in t["held_beside"]


def test_sill_threshold_totals(s):
    t = s["t327_sills_thresholds"]
    assert t["filled_m2"] == pytest.approx(3.0794)       # 22 sills 2.5214 + 4 floor-level 0.408 + A-GF-01 0.150
    assert t["retyped_filled_m2"] == pytest.approx(0.63)  # 4 marble closures 0.480 + D-1F-03 porcelain 0.150
    assert t["kept_m2"] == pytest.approx(3.75)
    assert t["new_rows_m2"] == pytest.approx(0.04)        # W18 external sill


def test_twenty_door_reveals_only_in_fin_plaster(out):
    o = rows(out, "owners")
    through = [r for r in o if r["comp"].startswith("REVEAL_THROUGH") and r["owner"].startswith("L-")]
    assert {r["owner_item"] for r in through} == {"FIN.PLASTER"}
    assert len({r["opening"] for r in through}) == 22
    new = {r["opening"] for r in o if r["comp"].startswith("REVEAL_THROUGH") and r["action"] == "ADD_ROW"}
    assert new == {"D-GF-02", "D-GF-10", "D-GF-14", "D-1F-03", "D-1F-04"}
    assert not new & {r["opening"] for r in through}


def test_threshold_corrections_carried_never_the_superseded(out):
    t = {r["opening"]: r for r in rows(out, "t327") if "THRESHOLD" in r["components"]}
    assert float(t["D-GF-14"]["m2"]) == pytest.approx(0.12) and float(t["D-1F-04"]["m2"]) == pytest.approx(0.12)
    for d, old in (("D-GF-14", 0.218846), ("D-1F-04", 0.131977), ("D-GF-02", 0.153542), ("D-GF-10", 0.1575),
                   ("D-1F-03", 0.185778)):
        assert abs(float(t[d]["m2"]) - old) > 1e-4
    lay = {r["door"]: r for r in rows(out, "layers")}
    assert float(lay["D-GF-06"]["wp_m2"]) == pytest.approx(0.2)          # T-336 pantry D120 = census D-GF-06
    assert lay["D-GF-10"]["result"].startswith("DIFFERS") and float(lay["D-GF-10"]["difference_m2"]) == pytest.approx(
        -0.000444)


def test_closure_trace_residuals_named(out):
    tr = {r["door"]: r for r in rows(out, "trace")}
    assert set(tr) == {"D-GF-02", "D-GF-10", "D-GF-14", "D-1F-03", "D-1F-04"}
    assert all(abs(float(r["residual_m2"])) < 1e-5 for r in tr.values())
    assert all(r["cause"].startswith("TRACED") for r in tr.values())


def test_wet_cross_check_zero_overlap(out, s):
    w = s["wet_cross_check"]
    assert w["overlap_m2"] == 0 and w["max_abs_face_residual_m2"] <= 0.0001
    assert w["backing_lines"] == {"filled_equal": 12, "held_blank": 6, "filled_m2": 340.3038}
    for r in rows(out, "wet"):
        assert r["owner_item"] not in ("FIN.WALL.TILE",)
    assert {r["owner_item"] for r in rows(out, "wet") if r["component"].startswith("REVEAL_THROUGH")} <= {"FIN.PLASTER", "REVEAL.ARCH"}


def test_held_never_zero(out):
    for k in ("owners", "t326", "t327"):
        for r in rows(out, k):
            if r.get("status") in ("HELD", "UNKNOWN") or r.get("action") in ("HOLD", "ADD_HELD_ROW"):
                assert r["m2"] == "", (k, r)


def test_tampered_ledger_stops_the_build(monkeypatch):
    real = T._csvr

    def fake(p):
        r = real(p)
        if Path(p).name == "SILL_THRESHOLD_LEDGER_T325.csv":
            for x in r:
                if x["opening"] == "W04" and x["component"] == "SILL_OUT":
                    x["m2"] = "0.05"
        return r
    monkeypatch.setattr(T, "_csvr", fake)
    with pytest.raises(B.BindingError, match="disagree"):
        T.build()
