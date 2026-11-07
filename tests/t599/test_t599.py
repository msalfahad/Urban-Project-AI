"""T-599: column-beam joint ownership UP-CONC-JOINT-001 1.0.0 (rules/conventions/URBAN_CONVENTIONS_1.0.0.json,
LEAD_ADOPTED under Q-62 A). Synthetic villa "K599" (not the training villa), hand-calculated: two columns, three beams
(one straight, one oblique at 45 degrees, one transfer beam carrying a planted column) -> every joint owned once by the
column, beams net, billed = union. Adverse: joint in both lines / in neither refused; rule id absent from RULES_INDEX
(or at another version) refused; slab top missing -> HELD (refused, never 0); beam-beam overlap outside a column refused;
mirror / rotation invariant. Then the committed T-590 restatement rebuilt from committed outputs (no private input)."""
from __future__ import annotations

import json
import math
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t599"))
import t599_joint_rule as J  # noqa: E402

Dd = Decimal
E = J.JointRuleError
S2 = math.sqrt(2.0)


def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def strip(p, q, w):
    """plan rectangle of width w along the axis p -> q"""
    dx, dy = q[0] - p[0], q[1] - p[1]
    L = math.hypot(dx, dy)
    nx, ny = -dy / L * w / 2, dx / L * w / 2
    return [(p[0] + nx, p[1] + ny), (q[0] + nx, q[1] + ny), (q[0] - nx, q[1] - ny), (p[0] - nx, p[1] - ny)]


# K599: storey base 0.00, slab top +3.50 (column heads to the slab top, UP-CONC-JOINT-001)
#  C1 0.30 x 0.30 at (0, 0); C2 0.30 x 0.40 at (5, 0); both 0.00 -> 3.50
#  B1 0.20 x 0.60 C1 -> C2 centre to centre (x 0..5), soffit 2.90, top 3.50
#  B2 0.20 x 0.50 oblique 45 deg from C2 centre (5, 0) to (8, 3), soffit 3.00, top 3.50
#  B3 0.20 x 0.70 transfer beam from C1 centre along +y to (0, 4), soffit 2.80, top 3.50
#  PC 0.20 x 0.20 planted column on B3 at (0, 3.0), from B3 top 3.50 to the upper slab top 6.80
COLS = [{"id": "C1", "outline": rect(-0.15, -0.15, 0.15, 0.15), "z0": 0.0, "z1": 3.50},
        {"id": "C2", "outline": rect(4.85, -0.20, 5.15, 0.20), "z0": 0.0, "z1": 3.50},
        {"id": "PC", "outline": rect(-0.10, 2.90, 0.10, 3.10), "z0": 3.50, "z1": 6.80}]
BEAMS = [{"id": "B1", "outline": strip((0, 0), (5, 0), 0.20), "z0": 2.90, "z1": 3.50},
         {"id": "B2", "outline": strip((5, 0), (8, 3), 0.20), "z0": 3.00, "z1": 3.50},
         {"id": "B3", "outline": strip((0, 0), (0, 4), 0.20), "z0": 2.80, "z1": 3.50}]


def hand_b2_c2_plan():
    """B2 (u along the 45-degree axis from C2's centre, |v| <= 0.10) inside C2 (x <= 5.15, y <= 0.20):
    u <= a + v (a = 0.15 sqrt2) and u <= b - v (b = 0.20 sqrt2); the bounds cross at vc = (b - a) / 2."""
    a, b = 0.15 * S2, 0.20 * S2
    vc = (b - a) / 2
    first = a * (vc + 0.10) + (vc ** 2 - 0.10 ** 2) / 2
    second = b * (0.10 - vc) - (0.10 ** 2 - vc ** 2) / 2
    return first + second                                             # = 0.038247 m2


def test_k599_hand_calculation():
    led = J.joint_ledger(COLS, BEAMS)
    j = {x["joint"]: x for x in led["joints"]}
    # C1 x B1: x 0..0.15, y -0.10..0.10 = 0.03 m2 x 0.60 = 0.018 m3; C2 x B1 the same
    assert j["C1xB1"]["m3"] == pytest.approx(0.15 * 0.20 * 0.60, abs=1e-9)
    assert j["C2xB1"]["m3"] == pytest.approx(0.15 * 0.20 * 0.60, abs=1e-9)
    # C2 x B2 oblique: 0.038247 m2 x 0.50 = 0.019124 m3 (not the axis length to the face x width)
    assert hand_b2_c2_plan() == pytest.approx(0.038247, abs=1e-6)
    assert j["C2xB2"]["m3"] == pytest.approx(hand_b2_c2_plan() * 0.50, abs=1e-9)
    assert j["C2xB2"]["m3"] != pytest.approx(0.15 * S2 * 0.20 * 0.50, abs=1e-4)
    # C1 x B3: x -0.10..0.10, y 0..0.15 = 0.03 m2 x 0.70 = 0.021 m3
    assert j["C1xB3"]["m3"] == pytest.approx(0.20 * 0.15 * 0.70, abs=1e-9)
    # planted column on B3: plan overlap 0.04 m2 but no vertical overlap -> not a joint, nothing deducted
    assert j["PCxB3"]["m3"] == 0 and j["PCxB3"]["owner"] is None
    for k in ("C1xB1", "C2xB1", "C2xB2", "C1xB3"):
        assert j[k]["owner"] == j[k]["column"]                         # the column owns every joint
    L = led["lines"]
    assert L["C1"]["m3"] == pytest.approx(0.09 * 3.50) and L["C2"]["m3"] == pytest.approx(0.12 * 3.50)
    assert L["PC"]["m3"] == pytest.approx(0.04 * 3.30) and L["PC"]["owns"] == []
    assert L["B1"]["m3"] == pytest.approx(4.70 * 0.20 * 0.60, abs=1e-9)            # face to face 0.564
    assert L["B3"]["m3"] == pytest.approx(4.00 * 0.20 * 0.70 - 0.021, abs=1e-9)     # through under PC: 0.539
    assert L["B2"]["m3"] == pytest.approx(3 * S2 * 0.20 * 0.50 - hand_b2_c2_plan() * 0.50, abs=1e-9)
    # billed = union of the solids (each joint once); the joints are carried by the columns
    gross = 0.09 * 3.5 + 0.12 * 3.5 + 0.04 * 3.3 + 5 * 0.2 * 0.6 + 3 * S2 * 0.2 * 0.5 + 4 * 0.2 * 0.7
    assert led["billed_m3"] == pytest.approx(gross - led["joint_m3"], abs=1e-9)
    assert led["billed_m3"] == pytest.approx(led["union_m3"], abs=1e-9)
    assert sorted(L["C2"]["owns"]) == ["C2xB1", "C2xB2"] and sorted(L["C1"]["owns"]) == ["C1xB1", "C1xB3"]


def _transform(pts, f):
    return [f(x, y) for x, y in pts]


@pytest.mark.parametrize("name,f", [
    ("mirror", lambda x, y: (-x, y)),
    ("rotate30", lambda x, y: (x * math.cos(0.5236) - y * math.sin(0.5236), x * math.sin(0.5236) + y * math.cos(0.5236))),
    ("shift", lambda x, y: (x + 1000.0, y - 250.0))])
def test_mirror_rotation_shift_invariant(name, f):
    base = J.joint_ledger(COLS, BEAMS)
    moved = J.joint_ledger([dict(c, outline=_transform(c["outline"], f)) for c in COLS],
                           [dict(b, outline=_transform(b["outline"], f)) for b in BEAMS])
    for k, v in base["lines"].items():
        assert moved["lines"][k]["m3"] == pytest.approx(v["m3"], abs=1e-7), (name, k)


def test_adverse_joint_in_both_lines_refused():
    with pytest.raises(E, match="billed in both"):
        J.check_claims(["C1xB1"], {"C1": {"C1xB1"}, "B1": {"C1xB1"}})


def test_adverse_joint_in_neither_line_refused():
    with pytest.raises(E, match="billed in neither"):
        J.check_claims(["C1xB1", "C2xB1"], {"C1": {"C1xB1"}, "B1": set()})


def test_adverse_unknown_joint_claimed_refused():
    with pytest.raises(E, match="not a joint"):
        J.check_claims(["C1xB1"], {"C1": {"C1xB1", "C9xB9"}})


def test_adverse_slab_top_missing_is_held_never_zero():
    cols = [dict(COLS[0], z1=None)] + COLS[1:]
    with pytest.raises(E, match="not established"):
        J.joint_ledger(cols, BEAMS)


def test_adverse_beam_beam_overlap_outside_columns_refused():
    beams = BEAMS + [{"id": "B4", "outline": strip((2.0, -1.0), (2.0, 1.0), 0.20), "z0": 2.90, "z1": 3.50}]
    with pytest.raises(E, match="outside UP-CONC-JOINT-001"):
        J.joint_ledger(COLS, beams)


def test_adverse_duplicate_member_refused():
    with pytest.raises(E, match="listed twice"):
        J.joint_ledger(COLS + [COLS[0]], BEAMS)


# ----------------------------------------------------------------------------------- the recorded rule ---------
def test_rule_is_in_rules_index_at_its_version():
    idx = J.convention_index()
    assert idx["UP-CONC-JOINT-001"]["version"] == "1.0.0"
    assert idx["UP-CONC-JOINT-001"]["status"] == "LEAD_ADOPTED"
    rec = J.load_rule()
    assert rec["owner_approved"] is False and "Q-62" in rec["delegation"]["owner_requirement"]
    assert rec["convention"]["owner_element"] == "COLUMN"


def test_adverse_rule_absent_from_rules_index_refused(tmp_path):
    p = tmp_path / "RULES_INDEX.md"
    p.write_text("# Rules index\n\n## Engineering knowledge 1.7.0 (0 rules)\n\n| UP-CONC-JOINT-001 | 1.0.0 | X |\n",
                 encoding="utf-8")
    idx = J.convention_index(p)
    assert idx == {}                                       # a row outside a convention section is not a record
    with pytest.raises(E, match="not in docs/RULES_INDEX.md"):
        J.require_indexed("UP-CONC-JOINT-001", "1.0.0", idx)
    with pytest.raises(E, match="lists 1.0.0, the row cites 1.1.0"):
        J.require_indexed("UP-CONC-JOINT-001", "1.1.0", J.convention_index())
    reg = J.Registers(rules={}, book={}, methods=set(), families=set(), method_reg={}, conventions={})
    with pytest.raises(J.R590.ProvenanceError, match="not in docs/RULES_INDEX.md"):
        reg.judge("UP-CONC-JOINT-001")
    t590 = json.loads(J.T590_OUT.read_text(encoding="utf-8"))
    with pytest.raises(E, match="not in docs/RULES_INDEX.md"):
        J.restate(t590, reg, {})


def test_adverse_rule_record_must_stay_lead_adopted(tmp_path):
    d = json.loads(J.RULE_FILE.read_text(encoding="utf-8"))
    d["records"][0]["status"] = "OWNER_APPROVED"
    p = tmp_path / "c.json"
    p.write_text(json.dumps(d), encoding="utf-8")
    with pytest.raises(E, match="LEAD_ADOPTED"):
        J.load_rule(p)


# ------------------------------------------------------------------------------- T-590 restatement -------------
def test_t590_rows_restated():
    o = J.build()
    assert o["rows_m3"] == 38 and o["sub_rows_m3"] == 42 and o["sub_rows_sourced"] == 35
    assert o["unresolved_apart"] == ["T-545/beams@V7 row 7 0.120452 m3"]
    assert o["matched_joint_m3_by_storey"] == {"GF": "2.28125", "1F": "0.385", "2F": "0"}
    assert o["headline_before"]["m3"] == {"UNRESOLVED": {"n": 6, "signed": "2.369278", "gross": "7.701778"}}
    a = o["headline_after"]["m3"]
    # Checker r1 fix: only the matched joint is RULE_DIFFERENCE (signed 0, gross 2 x (2.28125 + 0.385)); the beam
    # residuals GF 0.620464 / 1F 1.208362 / 2F 0.42 and the untraced 0.120452 stay UNRESOLVED
    assert a["RULE_DIFFERENCE"]["n"] == 4 and Dd(a["RULE_DIFFERENCE"]["signed"]) == 0
    assert Dd(a["RULE_DIFFERENCE"]["gross"]) == Dd("5.3325")
    assert a["UNRESOLVED"]["n"] == 4 and Dd(a["UNRESOLVED"]["signed"]) == Dd("2.248826") + Dd("0.120452")
    assert Dd(a["RULE_DIFFERENCE"]["signed"]) + Dd(a["UNRESOLVED"]["signed"]) == Dd("2.369278")
    assert Dd(a["RULE_DIFFERENCE"]["gross"]) + Dd(a["UNRESOLVED"]["gross"]) == Dd("7.701778")
    c = o["headline_by_cause_m3"]
    assert Dd(c["RULE_DIFFERENCE_SOURCED_matched_joint"]["signed"]) == 0
    assert Dd(c["RULE_DIFFERENCE_SOURCED_matched_joint"]["gross"]) == Dd("2") * (Dd("2.28125") + Dd("0.385"))
    assert Dd(c["UNRESOLVED_pair_residual_T600"]["signed"]) == Dd("0.620464") + Dd("1.208362") + Dd("0.42")
    assert Dd(c["check_signed_total"]) == Dd("2.369278")
    p = o["column_beam_pair_V7_m3_reference_minus_engine"]
    assert (p["GF"]["net_m3"], p["1F"]["net_m3"], p["2F"]["net_m3"]) == ("0.620464", "1.208362", "0.42")
    # every row's sub-rows sum back to the T-590 row; no beam row is SOURCED beyond its matched joint
    by_row = {}
    for r in o["rows"]:
        by_row.setdefault((r["section_id"], r["row"]), [Dd(r["parent_delta_m3"]), Dd(0)])[1] += Dd(r["delta_m3"])
        if r["outcome"] == "SOURCED":
            assert r["cited"] == ["UP-CONC-JOINT-001"] and r["class_after"] == "RULE_DIFFERENCE"
            assert r["basis_label"].startswith("LEAD_ADOPTED")
            if "THROUGH_SUPPORT" in r["name"]:
                assert r["sub"] == "matched" and Dd(r["delta_m3"]) == Dd(r["matched_joint_m3"])
        if r["outcome"] == "UNRESOLVED_RESIDUAL":
            assert r["pointer"] == "T-600" and r["class_after"] == "UNRESOLVED"
    assert len(by_row) == 38 and all(v[0] == v[1] for v in by_row.values())
    # 2F has no column joint of record: its beam row is wholly residual, never sourced
    assert [r["outcome"] for r in o["rows"] if r["section_id"] == "T-545/beams@V7" and r["row"] == 19] == \
        ["UNRESOLVED_RESIDUAL"]
    # alternative column readings named with their difference to T-551, never chosen
    alt = o["alternative_column_readings_m3"]
    assert alt["GF"]["T-572"] == {"joint_m3": "1.883750", "minus_record_m3": "-0.397500"}
    assert Dd(alt["GF"]["T-576"]["joint_m3"]) == Dd("2.03375") and Dd(alt["GF"]["T-576/10E0-C7"]["joint_m3"]) == Dd("2.075")
    assert o["released_quantities_changed"] == 0


def test_split_beam_row_normal():
    # K599-style storey: beam through-support 0.90 m3 against a column joint of record 0.60 m3
    assert J.split_beam_row(Dd("0.90"), Dd("0.60")) == [("matched", Dd("0.60")), ("residual", Dd("0.30"))]
    assert J.split_beam_row(Dd("0.60"), Dd("0.60")) == [("matched", Dd("0.60"))]          # fully explained
    assert J.split_beam_row(Dd("0.42"), Dd("0")) == [("residual", Dd("0.42"))]            # no joint: all residual


def test_adverse_row_exceeding_its_matched_joint_refused_as_wholly_sourced():
    with pytest.raises(E, match="refused as wholly SOURCED"):
        J.source_whole(Dd("2.901714"), Dd("2.28125"))
    assert J.source_whole(Dd("2.28125"), Dd("2.28125")) == Dd("2.28125")
    # a restatement row promoting the whole GF beam row (the r1 defect) is refused by the guard
    bad = [{"outcome": "SOURCED", "name": "GF: THROUGH_SUPPORT", "delta_m3": "2.901714", "matched_joint_m3": "2.28125"}]
    with pytest.raises(E, match="refused as wholly SOURCED"):
        J.guard_sourced(bad)
    with pytest.raises(E, match="exceeds the beam row"):
        J.split_beam_row(Dd("0.30"), Dd("0.60"))
    with pytest.raises(E, match="signs not beam"):
        J.split_beam_row(Dd("-0.30"), Dd("0.60"))


def test_adverse_tampered_t590_whole_row_cannot_be_sourced():
    t590 = json.loads(J.T590_OUT.read_text(encoding="utf-8"))
    # drop the GF column joint of record: the GF beam row must then be wholly residual, not sourced
    t590["rows"] = [r for r in t590["rows"] if not (r["section_id"] == J.RECORD_SECTION and "GF" in r["name"])]
    o = J.restate(t590, J.Registers(requirement_only=J.REQUIREMENT_ONLY), J.convention_index())
    gf = [r for r in o["rows"] if r["section_id"] == "T-545/beams@V7" and r["row"] == 2]
    assert [(r["outcome"], r["delta_m3"]) for r in gf] == [("UNRESOLVED_RESIDUAL", "2.901714")]
    assert Dd(o["headline_after"]["m3"]["RULE_DIFFERENCE"]["gross"]) == Dd("0.77")      # 1F matched only


def test_committed_outputs_current():
    r = subprocess.run([sys.executable, "-I", str(ROOT / "research/agents_t599/t599_joint_rule.py"), "--check"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
