"""Development villa pinned: the committed T-336 outputs rebuild byte for byte from the committed inputs, and the
engineering results the handoff states hold (no drawing is read here)."""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t336"))
import t336_alsenan as T  # noqa: E402


@pytest.fixture(scope="module")
def out():
    return T.outputs()


def test_outputs_rebuild_byte_identical(out):
    for k, txt in out.items():
        assert T.OUT[k].read_text(encoding="utf-8") == txt, k


def test_results(out):
    s = json.loads(out["summary"])
    ch = {c["piece"]: c for c in s["changes"]}
    assert ch["FIN.WP.WALL_UPTURN[m2]/1F-12/WALLS"]["after"] == pytest.approx(1.58)
    assert ch["FIN.WP.FLOOR[m2]/GF-07/FLOOR"]["after"] == pytest.approx(13.455)
    assert ch["FIN.WP.DOORWAY[m2]/DOOR:D-GF-14/THRESHOLD_FLOOR"]["after"] == pytest.approx(0.12)
    assert ch["FIN.WP.DOORWAY[m2]/DOOR:D-1F-04/THRESHOLD_FLOOR"]["after"] == pytest.approx(0.12)
    assert ch["FIN.WP.DOORWAY[m2]/DOOR:D-GF-07-PANTRY/THRESHOLD_FLOOR"]["after"] == pytest.approx(0.2)
    retired = sorted(c["row"] for c in s["changes"] if c["action"] == "REPLACE_BY_DOOR_ROW")
    assert len(retired) == 4                     # D-GF-02 and D-GF-10, two room-side lines each
    new_doors = sorted(c["piece"] for c in s["changes"] if c["action"] == "ADD_ROW" and "TRANSITION[m2]" in c["piece"])
    assert [p.split("/")[1] for p in new_doors] == ["DOOR:D-1F-06", "DOOR:D-GF-02", "DOOR:D-GF-07-PANTRY",
                                                    "DOOR:D-GF-10", "DOOR:D-GF-11", "DOOR:D-GF-12"]
    na = sorted(c["row"] for c in s["changes"] if c["action"] == "SET_NOT_APPLICABLE")
    assert {"L-0a7238edb9989d99d37a", "L-1ef59757a75524c397d7", "L-8fb80f626889e06f6f97"} <= set(na)
    assert s["pool"] == {"m2": pytest.approx(29.582355), "m3": pytest.approx(1.524503)}
    for c in s["changes"]:                       # held is blank, never 0
        if c["status"] in ("HELD", "UNKNOWN"):
            assert c["after"] is None


def test_every_piece_once(out):
    rows = out["pieces"].splitlines()[1:]
    keys = [r.split(",", 1)[0] for r in rows]
    assert len(keys) == len(set(keys))
