"""T-246: the V3.0.36 inputs are built only from the Checker-merged T-341 / T-345 / T-296 ledgers (sha256-pinned) and
every line they list closes gross - deductions + additions = net in its own unit (module check, no candidate needed)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t246"))

from engine.source import arch_v3036 as A  # noqa: E402
import t246_inputs as T  # noqa: E402


def test_inputs_build_and_close():
    doc = T.build("p")
    d = A.load_inputs(doc, "p")
    assert len(d["_rows"]) == 39
    fam = {}
    for r in d["_rows"]:
        fam[r["expect"]["item_code"]] = fam.get(r["expect"]["item_code"], 0) + 1
        assert abs(r["_residual"]) <= A.TOL
    assert fam == {"ARCH.WALL_RUN": 7, "FIN.FLOOR.PORCELAIN": 2, "FIN.PAINT": 4, "FIN.PLASTER": 4,
                   "FIN.SKIRTING": 10, "FIN.WALL.TILE": 12}
    assert {x["line_id"] for x in doc["set_aside"]} == set(T.SET_ASIDE)
    assert not set(T.SET_ASIDE) & {r["line_id"] for r in doc["lines"]}


def test_traced_porcelain_and_restated_gross():
    d = T.build()
    one = next(r for r in d["lines"] if r["line_id"] == "L-b06400d46d252f242018")
    assert one["action"] == "GROSS_RESTATE" and one["source_tasks"] == ["T-345"] and len(one["items"]) == 22
    assert one["gross_after"] == 75.983002 and one["expect"]["measured_net"] == 33.711036
    gf = next(r for r in d["lines"] if r["line_id"] == "L-7625f35c503d9f8e6196")
    assert gf["action"] == "GROSS_RESTATE" and gf["gross_after"] == 126.927696


def test_window_halves_flagged_from_t296():
    d = T.build()
    halves = [i for r in d["lines"] for i in r["items"] if "-half" in i["id"]]
    assert halves and all(i.get("physical_check") in ("UNRESOLVED", "CONSISTENT") for i in halves)
    w14 = [i for i in halves if i.get("census_id") == "W14"]
    assert len(w14) == 2 and all(i["physical_check"] == "UNRESOLVED" for i in w14)   # sill 1.40: base continues
    w15 = [i for i in halves if i.get("census_id") == "W15"]
    assert w15 and all(i["physical_check"] == "CONSISTENT" for i in w15)               # floor glazing


def test_edited_ledger_stops(monkeypatch):
    monkeypatch.setitem(T.PINS, T.FT, "0" * 64)
    try:
        T.build()
    except SystemExit as e:
        assert "edited ledger stops" in str(e)
    else:
        raise AssertionError("an edited ledger must stop the build")
