"""T-615 fixture (not the training villa): UPC-BLACK-BLOCK-001 1.1.0 gives the 0.15 m black block the Q-80 module
40 x 20 (12.5 / m2); hand-calculated walls, plus adverse cases (no borrowing for an unstated thickness, a printed
different face is a CONFLICT to report and never an override, a HELD record carrying 0 refused, millimetres refused)."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for p in ("agents_t533", "agents_t539", "agents_t615"):
    sys.path.insert(0, str(ROOT / "research" / p))
import block_module_v1 as BM  # noqa: E402
import accessory_ledger_v2 as V  # noqa: E402
import t615_alsenan as T  # noqa: E402

NEW = ROOT / "rules/rulebook/URBAN_COMPANY_RULEBOOK_1.1.0.json"
OLD = ROOT / "rules/rulebook/URBAN_COMPANY_RULEBOOK_1.0.0.json"
MIX = (8.0, 1.1, "UPC-BLACK-MORTAR-001 1.0.0 (Q-78 A)")


def reg_new():
    return T.register(T.RULEBOOK_NEW)[0]


def reg_old():
    return T.register(T.RULEBOOK_OLD)[0]


# ---------------------------------------------------------------- the rule version file

def test_rulebook_110_is_a_new_version_of_100():
    n, o = json.loads(NEW.read_text(encoding="utf-8")), json.loads(OLD.read_text(encoding="utf-8"))
    assert (n["version"], n["supersedes"], o["version"]) == ("1.1.0", "1.0.0", "1.0.0")
    rn = {r["rule_id"]: r for r in n["records"]}
    ro = {r["rule_id"]: r for r in o["records"]}
    assert rn.keys() == ro.keys()
    for k in ro:                                   # only the black-block record changed
        if k != "UPC-BLACK-BLOCK-001":
            assert rn[k] == ro[k]
    b = rn["UPC-BLACK-BLOCK-001"]
    assert (b["version"], b["supersedes"]) == ("1.1.0", "1.0.0")
    assert b["params"]["confirmed_modules_m"]["value"] == {"0.15": [0.40, 0.20], "0.20": [0.40, 0.20]}
    assert b["params"]["blocks_per_m2_40x20_module"]["value"] == 12.5
    assert "Q-80" in b["source"] and "Q-80" in b["scope"]
    assert ro["UPC-BLACK-BLOCK-001"]["params"]["confirmed_modules_m"]["value"] == {"0.20": [0.40, 0.20]}


def test_manifest_pins_both_rulebook_files():
    man = json.loads((ROOT / "rules/RULES_MANIFEST.json").read_text(encoding="utf-8"))["files"]
    for p in (OLD, NEW):
        rec = man[f"rulebook/{p.name}"]
        assert rec["kind"] == "AUTHORED" and rec["sha256"] == hashlib.sha256(p.read_bytes()).hexdigest()


def test_default_reader_unchanged():
    import importlib
    sys.path.insert(0, str(ROOT))
    C = importlib.import_module("engine.source.company_rulebook_v1")
    assert C.REL.endswith("URBAN_COMPANY_RULEBOOK_1.0.0.json")       # nothing switched by this task
    assert C.black_blocks(8.0, 0.15)["status"] != "OK"


# ---------------------------------------------------------------- normal case, by hand

def test_hand_wall_with_opening():
    # wall 6.00 x 3.00 x 0.15 m with one 1.20 x 1.00 window: net 18.00 - 1.20 = 16.80 m2
    q = BM.quantities(16.80, reg_new(), "BLACK", 0.15, *MIX)
    assert q["status"] == "RESOLVED" and q["module_m"] == (0.40, 0.20)
    assert q["units_nr"] == pytest.approx(16.80 * 12.5) == pytest.approx(210.0)
    # kappa = 0.39 x 0.19 / 0.08 = 0.92625; mortar = 0.15 x 0.07375 = 0.0110625 m3 / m2
    assert q["mortar_m3"] == pytest.approx(16.80 * 0.0110625) == pytest.approx(0.18585)
    assert q["cement_bags"] == pytest.approx(0.18585 * 8) and q["sand_m3"] == pytest.approx(0.18585 * 1.1)


def test_course_layout_agrees():
    e = T.module_015(reg_new())
    lay = BM.course_layout(4.00, 2.40, e)          # 10 units per course x 12 courses
    assert lay["units_nr"] == 120
    q = BM.quantities(4.00 * 2.40, reg_new(), "BLACK", 0.15, *MIX)
    assert q["units_nr"] == pytest.approx(120.0)
    assert q["mortar_m3"] == pytest.approx(lay["mortar_m3"]) == pytest.approx(9.6 * 0.15 - 120 * 0.39 * 0.19 * 0.15)


def test_rotated_or_mirrored_wall_same_quantity():
    # the count is a function of laid area only: a wall drawn rotated 30 deg or mirrored has the same area
    a = 5.20 * 2.80
    assert BM.quantities(a, reg_new(), "BLACK", 0.15, *MIX)["units_nr"] == pytest.approx(182.0)


def test_course_and_ties_on_015():
    c, held = V.course_for(BM.resolve, reg_new(), "BLACK", 0.15)
    assert held is None and c.module == pytest.approx(0.200)
    assert V.tie_range(c, 3.75, 3.85) == (6, 6)


# ---------------------------------------------------------------- adverse

def test_old_register_never_lends_020_to_015():
    q = BM.quantities(16.80, reg_old(), "BLACK", 0.15, *MIX)
    assert q["status"] == "HELD" and q["units_nr"] is None and q["mortar_m3"] is None
    with pytest.raises(BM.ModuleError):
        T.module_015(reg_old())


def test_unstated_thickness_held_not_borrowed():
    q = BM.quantities(10.0, reg_new(), "BLACK", 0.25, *MIX)
    assert q["status"] == "HELD" and q["units_nr"] is None


def test_printed_different_face_is_conflict_not_override():
    printed = BM.ModuleEntry("BLACK", 0.15, 0.39, 0.24, 0.01, 0.01, "block schedule sheet X (fixture)", "PROJECT_DOCUMENT")
    q = BM.quantities(16.80, reg_new() + [printed], "BLACK", 0.15, *MIX)
    assert q["status"] == "CONFLICT" and q["units_nr"] is None


def test_held_record_carrying_zero_refused():
    with pytest.raises(V.LedgerV2Error):
        V.no_zero_held([{"wall_id": "X", "state": "HELD", "ties": 0}], ("ties",))
    V.no_zero_held([{"wall_id": "X", "state": "HELD", "ties": None}], ("ties",))


def test_missing_area_held_and_mm_refused():
    assert BM.quantities(None, reg_new(), "BLACK", 0.15, *MIX)["status"] == "HELD"
    with pytest.raises(BM.ModuleError):
        BM.quantities(10.0, reg_new(), "BLACK", 150, *MIX)


def test_module_guard_refuses_other_module():
    bad = [BM.ModuleEntry("BLACK", 0.15, 0.39, 0.24, 0.01, 0.01, "fixture", "OWNER_CONFIRMED")]
    with pytest.raises(BM.ModuleError):
        T.module_015(bad)
