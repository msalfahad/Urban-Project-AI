"""T-355 development-villa pins (read-only over merged ledgers; no drawing is read): the committed outputs reproduce
byte for byte, and the three items close against the merged T-317 joint census (independent paths)."""

import csv
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t355"))
import t355_alsenan as A  # noqa: E402

OUT = ROOT / "research" / "agents_t355"


@pytest.fixture(scope="module")
def built():
    return A.outputs()


def test_outputs_reproduce(built):
    txt = built[0]
    for name, t in txt.items():
        assert (OUT / name).read_text(encoding="utf-8") == t, name


def test_junctions_equal_t317_vertical_joints(built):
    """one junction per block-segment / column boundary == T-317's V joints counted on one side of each wall."""
    led = built[2]
    v = 0
    with open(ROOT / "research/agents_t317/JOINTS_T317.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["method"] == "OWNER" and r["dir"] == "V" and r["side"] in ("INT-A", "INT"):
                v += 1
    assert len(led["ties"]) == v == 117


def test_joint_classes_close_to_t317(built):
    S = built[1]
    c = S["joint_mesh_by_class"]
    own = sum(c[k]["owner_band_m"] for k in c if k != "C")
    drw = sum(c[k]["drawing_band_m"] for k in c if k != "C")
    assert abs(own - (2.70 + 278.85)) < 1e-3                  # T-317: H inside 2.70 + V 278.85 + steps 0
    assert abs(drw - (215.1720 + 294.44 + 18.59)) < 1e-3      # T-317: 215.17 + 294.44 + 18.59
    assert abs(c["C"]["owner_band_m"] - (106.1138 + 121.80 + 2.23)) < 1e-3
    assert "D" not in c                                       # no register side without a finish


def test_white_walls_held_by_name_never_zero(built):
    led = built[2]
    for w in led["by_wall"]:
        if w["block_type"] == "WHITE":
            assert w["state"].startswith("HELD") and w["net_m"] is None
    for t in led["ties"]:
        if t["block_type"] == "WHITE":
            assert t["ties"] is None and t["state"] == "HELD"


def test_headline_figures(built):
    S = built[1]
    assert S["junctions_total"] == 117
    assert S["ties_primary_total"] == 182 and S["ties_alt210_total"] == 170
    assert S["mesh_primary_total_net_m"] == 528.0422 and S["mesh_alt210_total_net_m"] == 501.3866
    assert S["course_primary"]["module"] == 0.2


def test_no_block_or_plaster_quantity_written(built):
    txt = built[0]
    assert set(txt) == {"MESH_LEVELS_T355.csv", "MESH_BY_WALL_T355.csv", "SHARMAT_T355.csv",
                        "JOINT_MESH_CLASS_T355.csv", "summary.json"}
