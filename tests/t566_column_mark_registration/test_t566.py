"""T-566: column mark registration per position from the drawings alone (R-T566-1 .. 4) and the naming of the T-545 beam
UNTRACED residual (R-T566-5). Hand villa "V566" (a 3 x 2 grid, not the training villa), adverse cases, then the
development villa from committed files; the rebuilds from the private DXF / workbook run only when those are present."""
from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t566"))
import t566_rules as R  # noqa: E402

OUT = ROOT / "research" / "agents_t566" / "out" / "T566_REGISTRATION.json"
INPUT = ROOT / "research" / "agents_t566" / "POSITION_INPUT_T566.json"
T551 = ROOT / "research" / "agents_t551" / "out" / "T551_COLUMN_FOOTING_RECONCILE.json"
PRIVATE = ROOT.parent / "private"
D = Decimal


def lab(t):
    return {"text": t, "kind": "PRINTED_LABEL"}


# ---- villa "V566" (hand) -----------------------------------------------------------------------------------------
# Grid A..C x 1..2 (six positions). Two foundation sheets print labels (N1 = foundation plan, N2 = column plan); the GF
# and 1F slab plans draw SOLID outlines and print no label. Schedule (cm): K1 FOU 30x50, GR 25x50, 1ST 20x50;
# K2 FOU 30x60, GR 25x60, 1ST none (a GF-only column).
SCHED = {"K1": {"FOUNDATION": (30, 50), "GF": (25, 50), "1F": (20, 50)},
         "K2": {"FOUNDATION": (30, 60), "GF": (25, 60), "1F": None}}
V566 = {
    "A1": ({"N1": lab("K1"), "N2": lab("K1/F1")}, {"GF": (250, 500), "1F": (200, 500)}),   # 1F section change
    "B1": ({"N1": lab("K1"), "N2": lab("K1")}, {"GF": (500, 250), "1F": None}),             # rotated outline
    "C1": ({"N1": lab("K2"), "N2": lab("K2")}, {"GF": (250, 600), "1F": None}),
    "A2": ({"N1": lab("K1"), "N2": lab("K1")}, {"GF": (250, 500), "1F": (200, 500)}),
    "B2": ({"N1": lab("K1"), "N2": lab("K2")}, {"GF": (250, 600), "1F": None}),             # the two sheets differ
    "C2": ({"N1": lab("K2"), "N2": None}, {"GF": (250, 600), "1F": (200, 500)}),            # N2 prints no label
}


def test_hand_registration_by_position_and_continuity():
    got = {p: R.register_position(l, prefixes=("K",)) for p, (l, _) in V566.items()}
    assert {p: g["class"] for p, g in got.items()} == {"A1": "REGISTERED", "B1": "REGISTERED", "C1": "REGISTERED",
                                                       "A2": "REGISTERED", "B2": "CONFLICT", "C2": "REGISTERED"}
    assert got["A1"]["mark"] == "K1" and got["A1"]["support"] == "2/2"
    assert got["C2"]["mark"] == "K2" and got["C2"]["support"] == "1/2"
    assert got["B2"]["candidates"] == {"K1": ["N1"], "K2": ["N2"]}
    # continuity: the label-free GF / 1F members carry the position's mark; A1's 1F section change is the schedule
    # band of K1 (25x50 -> 20x50), not a different mark
    assert R.continuity(got["A1"]["mark"], {"GF": (250, 500), "1F": (200, 500)}) == {"GF": "K1", "1F": "K1"}
    v = R.section_vector({"K1": SCHED["K1"]}, {"GF": (250, 500), "1F": (200, 500)})
    assert v == {"K1": {"GF": "AGREE", "1F": "AGREE"}}
    # marks by continuity: GF K1 x3 (A1, B1, A2), K2 x2 (C1, C2), one CONFLICT (B2)
    gf = [g["mark"] for p, g in got.items() if g["class"] == "REGISTERED"]
    assert sorted(gf) == ["K1", "K1", "K1", "K2", "K2"]


def test_hand_rotation_mirror_and_units_do_not_change_the_vector():
    a = R.section_vector({"K1": SCHED["K1"]}, {"GF": (500, 250)}, unit="mm")
    b = R.section_vector({"K1": SCHED["K1"]}, {"GF": (0.25, 0.50)}, unit="m")
    c = R.section_vector({"K1": SCHED["K1"]}, {"GF": (25, 50)}, unit="cm")
    assert a == b == c == {"K1": {"GF": "AGREE"}}
    # mirrored grid: the same labels at mirrored positions give the same classes
    mirror = {p[0].translate(str.maketrans("AC", "CA")) + p[1]: v for p, v in V566.items()}
    assert sorted(R.register_position(l, prefixes=("K",))["class"] for l, _ in mirror.values()) == \
        sorted(R.register_position(l, prefixes=("K",))["class"] for l, _ in V566.values())


def test_hand_conflict_is_bounded_and_evidence_does_not_resolve_it():
    l, dr = V566["B2"]
    reg = R.register_position(l, prefixes=("K",))
    vec = R.section_vector(SCHED, {"GF": dr["GF"]})
    assert vec["K2"]["GF"] == "AGREE" and vec["K1"]["GF"] == "DIFFERS"
    assert reg["class"] == "CONFLICT" and reg["mark"] is None          # a section match never resolves the conflict
    b = R.conflict_area_bound(SCHED, "GF", (0.25, 0.60), height_m=3.0)
    assert (b["low_m2"], b["high_m2"]) == (D("0.125000"), D("0.150000"))
    assert (b["low_m3"], b["high_m3"]) == (D("0.375000"), D("0.450000"))
    # 1F: K2 has no band; reported, never taken as 0
    b1 = R.conflict_area_bound(SCHED, "1F", None)
    assert b1["no_band"] == ["K2"] and b1["low_m2"] == b1["high_m2"] == D("0.100000")    # K1 1ST 20 x 50 only


def test_no_band_where_a_member_is_drawn():
    assert R.section_vector({"K2": SCHED["K2"]}, {"1F": (200, 500)}) == {"K2": {"1F": "NO_BAND"}}
    assert R.section_vector({"K2": SCHED["K2"]}, {"1F": None}) == {"K2": {"1F": "NOT_DRAWN"}}


# ---- adverse --------------------------------------------------------------------------------------------------------
def test_mark_from_label_count_refused():
    with pytest.raises(R.Refused):
        R.register_by_label_count({"N1": {"K1": 3, "K2": 2}})


def test_freelancer_count_refused():
    with pytest.raises(R.Refused):
        R.register_from_freelancer({"K1": 4})
    with pytest.raises(R.Refused):
        R.register_position({"N1": {"text": "K1", "kind": "FREELANCER_ROW"}}, prefixes=("K",))


def test_no_label_is_held_never_a_default():
    g = R.register_position({"N1": None, "N2": None}, prefixes=("K",))
    assert g["class"] == "HELD" and g["mark"] is None


def test_non_label_text_refused():
    for t in ("B7", "F3", "30X50", ""):
        with pytest.raises(R.Refused):
            R.norm_mark(t)
    assert [R.norm_mark(t) for t in ("C3/F3", "CN/FN", "C/F", "c11")] == ["C3", "CN", "C", "C11"]


def test_units_and_bad_sections_refused():
    with pytest.raises(R.Refused):
        R.section_vector(SCHED, {"GF": (250, 500)}, unit="inch")
    with pytest.raises(R.Refused):
        R.conflict_area_bound(SCHED, "GF", (0, 0.5))
    with pytest.raises(R.Refused):
        R.conflict_area_bound(SCHED, "GF", None, height_m=0)


def test_named_untraced_rules():
    with pytest.raises(R.Refused):
        R.name_untraced("X", "0", "UNRESOLVED", "UNRESOLVED", "e")       # never closed as 0
    with pytest.raises(R.Refused):
        R.name_untraced("X", "-0.1", "GUESS", "?", "e")
    with pytest.raises(R.Refused):
        R.name_untraced("X", "-0.1", "COUNT", "ENGINE_RIGHT", "")
    a = R.name_untraced("A", "-0.10", "COUNT", "ENGINE_RIGHT", "e")
    b = R.name_untraced("B", "0.02", "DRAWING_PRECISION", "ENGINE_RIGHT", "e")
    assert R.close_named("-0.08", [a, b])["by_cause"] == {"COUNT": "-0.100000", "DRAWING_PRECISION": "0.020000"}
    with pytest.raises(R.Refused):
        R.close_named("-0.09", [a, b])


def test_precision_class_metres_only():
    assert R.precision_class(4.55, 4.577) and not R.precision_class(4.50, 4.577)
    with pytest.raises(R.Refused):
        R.precision_class(4550, 4577)                                     # millimetres refused
    with pytest.raises(R.Refused):
        R.precision_class(-1, 2)


def test_label_assignment_is_min_total_not_nearest_first():
    sys.path.insert(0, str(ROOT / "research" / "agents_t566"))
    import t566_extract as X
    # label a sits 0.9 from outline 0 and 1.0 from outline 1; label b sits 1.0 from 0 and 3.0 from 1. Nearest-first binds
    # a->0 and leaves b->1 (total 3.9); the minimum-total assignment binds a->1, b->0 (total 2.0).
    dist = {(0, 0): 0.9, (0, 1): 1.0, (1, 0): 1.0, (1, 1): 3.0}
    m = X._assign([0, 1], [0, 1], lambda i, j: dist[(i, j)])
    assert {i: j for i, (j, _) in m.items()} == {0: 1, 1: 0}


# ---- development villa (committed files) ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def doc():
    import t566_alsenan as A
    return A.build()


def test_dev_registration(doc):
    cls = [r["class"] for r in doc["positions"]]
    assert len(cls) == 36 and cls.count("REGISTERED") == 34 and cls.count("CONFLICT") == 2
    ag = doc["agreement_with_merged_T205"]
    assert ag["fp_label_equal"] == 36 and ag["registered_equal"] == 34 and ag["conflict_here"] == ["10AE", "10E0"]
    c = {r["position"]: r for r in doc["positions"] if r["class"] == "CONFLICT"}
    assert c["10AE"]["candidates"] == {"C": ["GBP"], "C3": ["CAP", "FP"]}
    assert c["10E0"]["candidates"] == {"C7": ["GBP"], "C8": ["CAP", "FP"]}
    # evidence beside the conflict (information only): every printed / drawn section at 10E0 fits C7, not C8
    v = c["10E0"]["section_vs_schedule"]
    assert v["C7"]["FOU_size_text"] == "AGREE" and v["C7"]["GF"] == "AGREE" and v["C8"]["GF"] == "DIFFERS"
    assert c["10E0"]["mark"] is None and c["10AE"]["mark"] is None
    # both conflict members are HELD lines: no released quantity moves
    assert all(m["line_class"] == "HELD" for r in c.values() for m in r["members"].values())


def test_dev_gf_counts_and_bounds(doc):
    g = doc["gf_counts"]
    assert g["registered"]["C3"] == 5 and g["registered"]["C8"] == 1 and g["registered"]["C"] == 5
    assert sum(g["registered"].values()) + len(g["conflict_positions"]) == 30     # 30 GF members over necks
    b = {(x["position"], x["storey"]): x for x in doc["conflict_bounds"]}
    assert (b[("10AE", "GF")]["low_m2"], b[("10AE", "GF")]["high_m2"]) == ("0.080000", "0.125000")
    assert (b[("10E0", "GF")]["low_m2"], b[("10E0", "GF")]["high_m2"]) == ("0.200000", "0.225000")
    assert (b[("10E0", "1F")]["low_m2"], b[("10E0", "1F")]["high_m2"]) == ("0.160000", "0.200000")


def test_dev_slab_frames_print_no_column_label(doc):
    t = doc["slab_frame_mark_like_texts"]
    assert t["FFRS"] == [] and t["SFRS"] == [] and [x["layer"] for x in t["GFRS"]] == ["S-SEC-TEXT"]


def test_dev_beam_untraced_named_exactly(doc):
    b = doc["beam_untraced"]
    assert b["untraced_total_m3"] == "-0.365289"
    assert b["closure"]["by_cause"] == {"DRAWING_PRECISION": "0.014517", "COUNT": "-0.087240",
                                        "MARK_BOUNDARY": "-0.011152", "BEYOND_EXTENT": "-0.160962",
                                        "UNRESOLVED": "-0.120452"}
    b2 = [n for n in b["named"] if n["mark"] == "2F B2"][0]
    assert b2["mark_residual_m3"] == "-0.200000" and b2["reclassed_from_THROUGH_SUPPORT_m3"] == "-0.112760"


def test_dev_committed_output_equals_rebuild(doc):
    c = json.loads(OUT.read_text(encoding="utf-8"))
    for k in ("positions", "gf_counts", "conflict_bounds", "agreement_with_merged_T205", "beam_untraced"):
        assert c[k] == json.loads(json.dumps(doc[k])), k
    # the base reading (merged marks C3 at 10AE, C8 at 10E0) reproduces the merged T-551 storey split exactly
    t551 = json.loads(T551.read_text(encoding="utf-8"))["columns"]
    base = [x for x in c["t551_resplit"] if x["reading"] == {"10AE": "C3", "10E0": "C8"}][0]["tables"]
    for st in ("GF", "1F"):
        assert base[st]["components"] == {k: v["m3"] for k, v in t551[st]["components"].items()}
        assert base[st]["residual_m3"] == t551[st]["residual_m3"]
    # every reading keeps the storey residual: the conflict moves m3 between COUNT and HELD only
    for x in c["t551_resplit"]:
        for st in ("GF", "1F"):
            t = x["tables"][st]
            assert t["residual_m3"] == t551[st]["residual_m3"]
            assert D(t["components"]["COUNT"]) + D(t["components"]["HELD"]) == \
                D(t551[st]["components"]["COUNT"]["m3"]) + D(t551[st]["components"]["HELD"]["m3"])


def test_no_freelancer_values_tracked():
    s = OUT.read_text(encoding="utf-8") + INPUT.read_text(encoding="utf-8")
    assert "his_rows" not in s and '"L_his"' not in s


# ---- private rebuilds (only where the private copies are present) ---------------------------------------------------
@pytest.mark.skipif(not (PRIVATE / "ST7757.dxf").exists(), reason="private DXF absent")
def test_private_extract_equals_committed_input():
    import t566_extract as X
    assert json.loads(json.dumps(X.build(PRIVATE / "ST7757.dxf"))) == json.loads(INPUT.read_text(encoding="utf-8"))


@pytest.mark.skipif(not (PRIVATE / "concrete_rebar.xlsx").exists() or not (PRIVATE / "t566" / "bands.json").exists(),
                    reason="private workbook / bands absent")
def test_private_rebuild_equals_committed():
    import t566_alsenan as A
    d = A.build(str(PRIVATE / "concrete_rebar.xlsx"), str(PRIVATE / "t566" / "bands.json"))
    c = json.loads(OUT.read_text(encoding="utf-8"))
    assert json.loads(json.dumps(d["t551_resplit"])) == c["t551_resplit"]
    assert all(d["beam_row_checks_private_run"].values()) and d["beam_row_checks_private_run"] == \
        c["beam_row_checks_private_run"]
