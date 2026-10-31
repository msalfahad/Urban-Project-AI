"""T-374 straight-bar (shape 00) cutting schedule: villa V374 by hand (not the development villa), adverse cases, and a
regression on the committed development-villa schedule. Writes only to tmp_path."""
import csv
import importlib.util
import json
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research/agents_t374"


def _load():
    spec = importlib.util.spec_from_file_location("t374", HERE / "t374_straight_bbs.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


B = _load()
NOW = {p: "SCHEDULABLE_NOW" for p in B.POPULATIONS}
LAPS = {
    "FTG-BOTTOM": {"lap_status": "NOT_REQUIRED", "splice_need": "NOT_REQUIRED", "authority": "NOT_PRINTED", "sources": ""},
    "COL-MAIN": {"lap_status": "HELD_NO_AUTHORITY", "splice_need": "REQUIRED", "authority": "NOT_PRINTED", "sources": ""},
    "COL-TWIST-EXTRA": {"lap_status": "HELD_NO_AUTHORITY", "splice_need": "", "authority": "", "sources": ""},
    "CB-BOTTOM": {"lap_status": "HELD_NO_AUTHORITY", "splice_need": "", "authority": "", "sources": ""},
    "CB-SUPPORT-TOP": {"lap_status": "NOT_REQUIRED", "splice_need": "", "authority": "", "sources": ""},
    "GB-MAIN": {"lap_status": "HELD_NO_AUTHORITY", "splice_need": "REQUIRED", "authority": "", "sources": ""},
    "SLAB-TEMPERATURE": {"lap_status": "PRINTED", "splice_need": "", "authority": "GENERAL_NOTE", "sources": "P15N1"},
}


def ftg(lid, side_m, cover_mm, n, d=12, state="SOURCE_DERIVED", count_range=None, kg=None, low=None, high=None):
    L = (Decimal(str(side_m)) * 1000 - 2 * cover_mm) / 1000
    inp = {"policy": "FOOTING_REBAR_POPULATION_V1", "mark": "FA", "component": "BOTTOM_LONG", "count": n,
           "bar_length_m": float(L), "kg_per_m": round(d * d / 162, 6), "reasons": []}
    if count_range:
        inp["count_range"] = count_range
    return {"line_id": lid, "element_id": f"V374:FTG:{lid}:BOTTOM_LONG", "floor": "FOUNDATION",
            "subtrade": f"FOOTINGS / {d} mm", "evidence_state": state, "measured_net": kg,
            "bounded_range": None if low is None else {"low": low, "high": high, "basis": "count readings"},
            "formula": f"n x (side - 2 x {cover_mm} mm) x kg/m", "inputs": inp, "rfi": None}


def hand(lid, element_id, comp, n, L, d, kg, policy="COLUMN_STEEL_HAND_LEDGER_V1", element="C-1", sub="COLUMNS"):
    return {"line_id": lid, "element_id": element_id, "floor": "GF", "subtrade": f"{sub} / {d} mm",
            "evidence_state": "SOURCE_DERIVED", "measured_net": kg, "bounded_range": None, "formula": "held: ",
            "inputs": {"policy": policy, "element": element, "component": comp, "count": float(n), "length_m": L,
                       "printed": "schedule row", "reasons": []}, "rfi": None}


def villa():
    """Villa V374 (hand-built). Footing FA 2.00 m bottom long bars 10 ø12: cover 70 mm on one footing, 75 mm on the
    other (cover change); footing FB a '/m' row with count readings 9 .. 10; column C-1 6 ø16 x 3.60 m; a ground-beam
    band X1-Y1 carried through one interior column: 7.00 + 0.50 + 6.50 = 14.00 m, 3 ø16 top."""
    m12, m16 = Decimal(144) / 162, Decimal(256) / 162
    lines = [
        ftg("V-F1", 2.00, 70, 10, kg=float((10 * Decimal("1.86") * m12).quantize(Decimal("0.000001")))),
        ftg("V-F2", 2.00, 75, 10, kg=float((10 * Decimal("1.85") * m12).quantize(Decimal("0.000001")))),
        ftg("V-F3", 1.50, 70, None, state="BOUNDED_EXPOSURE", count_range=[9, 10],
            low=float((9 * Decimal("1.36") * m12).quantize(Decimal("0.000001"))),
            high=float((10 * Decimal("1.36") * m12).quantize(Decimal("0.000001")))),
        hand("V-C1", "HL:COLUMN_STEEL:C-1:MAIN_BARS_NET", "MAIN BARS net", 6, 3.6, 16,
             float((6 * Decimal("3.6") * m16).quantize(Decimal("0.001")))),
    ]
    for i, (eid, L) in enumerate([("HL:GROUND_SYSTEM_STEEL:GSO-X1-Y1-1:TOP", "7.0"),
                                  ("HL:GROUND_SYSTEM_STEEL:through column K9 (X1-Y1):TOP", "0.5"),
                                  ("HL:GROUND_SYSTEM_STEEL:GSO-X1-Y1-2:TOP", "6.5")]):
        lines.append(hand(f"V-G{i}", eid, "TOP", 3, float(L), 16,
                          float((3 * Decimal(L) * m16).quantize(Decimal("0.001"))),
                          policy="GROUND_SYSTEM_STEEL_HAND_LEDGER_V1", element=eid.split(":")[2], sub="GROUND_BEAMS"))
    pop_of = {"V-F1": "FTG-BOT-MESH", "V-F2": "FTG-BOT-MESH", "V-F3": "FTG-BOT-MESH", "V-C1": "COL-MAIN-BODY",
              "V-G0": "GB-MAIN", "V-G1": "GB-MAIN", "V-G2": "GB-MAIN"}
    return lines, pop_of


def by_id(rows):
    return {r["line_id"]: r for r in rows}


# ---------------------------------------------------------------- normal (hand values)

def test_villa_v374_hand_values_and_cover_change():
    lines, pop_of = villa()
    rows, runs = B.build(lines, pop_of, NOW, LAPS, ledgers={})
    r = by_id(rows)
    # FA, cover 70: 10 x 1.86 m x 0.888889 = 16.533333 kg; cover 75: 10 x 1.85 = 16.444444 kg
    assert r["V-F1"]["cut_length_m"] == "1.86" and r["V-F2"]["cut_length_m"] == "1.85"
    assert B.fmt_kg(r["V-F1"]["net_kg_low"]) == "16.533333"
    assert B.fmt_kg(r["V-F2"]["net_kg_low"]) == "16.444444"
    # procurement: 6 bars of 1.86 per 12 m -> 2 stock bars (6 + 4), offcuts 0.84 m and 4.56 m, 2 x 12 x 0.888889 kg
    assert r["V-F1"]["stock_bars"] == "2" and r["V-F1"]["offcuts"] == "1 x 0.84 m + 1 x 4.56 m"
    assert B.fmt_kg(r["V-F1"]["procurement_kg_low"]) == "21.333333"
    # bounded count 9 .. 10 x 1.36 m: 10.88 .. 12.088889 kg, scheduled as a range, never collapsed
    assert r["V-F3"]["row_status"] == "SCHEDULED_BOUNDED" and r["V-F3"]["n"] == "9..10"
    assert B.fmt_kg(r["V-F3"]["net_kg_low"]) == "10.880000" and B.fmt_kg(r["V-F3"]["net_kg_high"]) == "12.088889"
    # column 6 x 3.60 m x 1.580247 = 34.133333 kg; 3 per stock -> 2 stock bars, offcuts 2 x 1.20 m; lap HELD by name
    assert B.fmt_kg(r["V-C1"]["net_kg_low"]) == "34.133333" and r["V-C1"]["offcuts"] == "2 x 1.2 m"
    assert r["V-C1"]["lap"].startswith("HELD by name")
    # the band is ONE physical bar of 14.00 m: one splice for any lap up to (2 x 12 - 14) / 1 = 10.00 m, cut HELD
    assert len(runs) == 1 and runs[0]["run_length_m"] == "14" and runs[0]["splices_per_bar"] == 1
    assert runs[0]["splice_valid_for_lap_up_to_m"] == "10.0000" and runs[0]["procurement"] is None
    assert {r[k]["row_status"] for k in ("V-G0", "V-G1", "V-G2")} == {"RUN_PART"}
    assert B.fmt_kg(runs[0]["net_kg"]) == "66.370370"   # 3 x 14 x 1.580247


def test_splice_boundaries_owner_t273_from_decimal_text():
    S, lap = B.to_u("12"), B.to_u("1.2")
    assert [B.splices_needed(B.to_u(t), S, lap) for t in ("12.00", "12.01", "22.80", "22.81")] == [0, 1, 1, 2]
    assert B.splice_band(B.to_u("18.57"), S) == {"splices": 1, "valid_for_lap_up_to_m": Decimal("5.4300")}


def test_ffd_nesting_against_the_lower_bound():
    nf = B.nest_ffd([B.to_u("4.5")] * 8 + [B.to_u("3.0")] * 4, B.to_u("12"))
    assert nf["lower_bound_bars"] == 4 and nf["stock_bars"] == 4    # 4.5+4.5+3.0 twice-packed, 48 m of pieces


# ---------------------------------------------------------------- adverse

def test_hooked_bar_presented_as_shape_00_is_refused():
    lines, pop_of = villa()
    bad = dict(lines[3], formula="n x (height + 12 d hook) x kg/m")
    with pytest.raises(B.ScheduleRefused, match="not shape 00"):
        B.schedule_line(bad, "COL-MAIN-BODY", NOW, LAPS)


def test_bend_kept_only_in_the_source_ledger_is_refused():
    lines, pop_of = villa()
    ledgers = {"COLUMN_STEEL_HAND_LEDGER_V1": [{"id": "C-1", "component": "MAIN BARS net",
                                                 "cause": "top bend drawn without length: BLOCKED_DETAILING"}]}
    rows, _ = B.build(lines, pop_of, NOW, LAPS, ledgers=ledgers)
    r = by_id(rows)["V-C1"]
    assert r["row_status"] == "SHAPE_NOT_00" and r["net_kg_low"] is None and r["shape_code"] == ""


def test_lap_borrowed_from_note_9_is_refused_and_a_printed_lap_is_accepted():
    lines, _ = villa()
    with pytest.raises(B.ScheduleRefused, match="refused for COL-MAIN-BODY"):
        B.schedule_line(lines[3], "COL-MAIN-BODY", NOW, LAPS, lap={"value_m": 1.12, "authority": "N9"})
    B.check_lap("SLAB-TEMP", {"value_m": 0.48, "authority": "P15N1"}, LAPS)        # printed for its own group
    with pytest.raises(B.ScheduleRefused):
        B.check_lap("SLAB-TEMP", {"value_m": 0.84, "authority": "N9"}, LAPS)


def test_population_not_schedulable_now_gets_no_row():
    lines, _ = villa()
    with pytest.raises(B.ScheduleRefused, match="no shape-00 row"):
        B.schedule_line(lines[3], "COL-MAIN-BODY", dict(NOW, **{"COL-MAIN-BODY": "GAP"}), LAPS)


def test_held_line_stays_blank_never_zero_and_bad_arithmetic_stops():
    lines, _ = villa()
    held = dict(lines[3], evidence_state="BLOCKED_RFI", measured_net=None,
                inputs=dict(lines[3]["inputs"], reasons=["framing member HELD"], ledger_state="UNQUANTIFIED"))
    r = B.schedule_line(held, "COL-MAIN-BODY", NOW, LAPS)
    assert r["row_status"] == "HELD" and r["net_kg_low"] is None and r["n"] == ""
    wrong = dict(lines[3], measured_net=35.0)
    with pytest.raises(B.ScheduleRefused, match="not a storage effect"):
        B.schedule_line(wrong, "COL-MAIN-BODY", NOW, LAPS)
    frac = dict(lines[3], inputs=dict(lines[3]["inputs"], count=8.8))
    with pytest.raises(B.ScheduleRefused, match="whole number"):
        B.schedule_line(frac, "COL-MAIN-BODY", NOW, LAPS)
    with pytest.raises(B.ScheduleRefused, match="splice"):
        B.cut_from_stock(2, B.to_u("12.01"), B.to_u("12"))


def test_run_with_a_count_change_is_refused():
    lines, pop_of = villa()
    lines[5] = dict(lines[5], inputs=dict(lines[5]["inputs"], count=4.0),
                    measured_net=float((4 * Decimal("0.5") * Decimal(256) / 162).quantize(Decimal("0.001"))))
    with pytest.raises(B.ScheduleRefused, match="change along the run"):
        B.build(lines, pop_of, NOW, LAPS, ledgers={})


# ---------------------------------------------------------------- development villa regression (committed data)

def test_development_villa_schedule_reproduces_the_committed_record(tmp_path):
    lines, pop_of = B.load_candidate()
    rows, runs = B.build(lines, pop_of, B.shape_status(), B.lap_status(), B.t318_line_ids(),
                         downgrades=B.load_snapshot())
    assert len(rows) == 442
    out = tmp_path / "s.csv"
    B.write_csv(rows, out)
    assert out.read_text(encoding="utf-8") == (HERE / "T374_STRAIGHT_BBS.csv").read_text(encoding="utf-8")
    s = B.summarise(rows, runs)
    committed = json.load(open(HERE / "T374_SUMMARY.json", encoding="utf-8"))
    assert s["populations"] == committed["populations"] and s["runs"] == committed["runs"]
    st = {p: v["row_status"] for p, v in s["populations"].items()}
    assert st["COL-TWIST-EXTRA"] == {"HELD": 1, "SHAPE_NOT_00": 1}           # F-T374-1: drawn top bend
    assert st["SLAB-TEMP"] == {"HELD": 3}
    assert st["FTG-BOT-MESH"] == {"HELD": 3, "HELD_DOWNGRADE": 38, "HELD_SAME_BASIS": 10}   # r2: DG-a97ec2ea66e02194
    assert sum(r["row_status"] in ("SCHEDULED", "SCHEDULED_BOUNDED", "RUN_PART") for r in rows) == 157
    exact = sum((r["net_kg_low"] for r in rows if r["row_status"] in ("SCHEDULED", "RUN_PART")), Decimal(0))
    # the Checker's 5,124.317162 - 874.862222 = 4,249.454940 is the sum of the per-population 6 dp figures; the
    # unrounded sum of n x L x d^2/162 (repeating thirds) is 4,249.4549405.. and rounds to ..941 (display only)
    pops = B.summarise(rows, runs)["populations"]
    assert sum(Decimal(v["scheduled_net_kg"]) for v in pops.values()) == Decimal("4249.454940")
    assert abs(exact - Decimal("4249.454940")) < Decimal("0.000001")
    dg = [r for r in rows if r["row_status"] == "HELD_DOWNGRADE"]
    assert {r["downgrade_id"] for r in dg} == {"DG-a97ec2ea66e02194"}
    assert B.fmt_kg(sum((r["audit_kg_low"] for r in dg), Decimal(0))) == "874.862227"   # = the record's engine_qty
    sb = [r for r in rows if r["row_status"] == "HELD_SAME_BASIS"]
    assert B.fmt_kg(sum((r["audit_kg_low"] for r in sb), Decimal(0))) == "1606.069136"
    assert B.fmt_kg(sum((r["audit_kg_high"] for r in sb), Decimal(0))) == "1655.560494"
    for r in dg + sb:
        assert r["cut_length_m"] == r["n"] == r["stock_bars"] == r["procurement"] == "" and r["net_kg_low"] is None
        assert r["audit_basis"].startswith("UNSUPPORTED BASIS (DG-a97ec2ea66e02194)")
    # every scheduled exact row: net within the candidate's storage precision, cause named
    for r in rows:
        if r["row_status"] in ("SCHEDULED", "RUN_PART") and r["evidence_state"] == "SOURCE_DERIVED":
            assert r["diff_cause"] in ("NONE", "KG_STORAGE_ROUNDING", "LENGTH_STORAGE_0.1MM+KG_ROUNDING")
        if r["row_status"] not in ("SCHEDULED", "SCHEDULED_BOUNDED", "RUN_PART"):
            assert r["net_kg_low"] is None and r.get("shape_code", "") == ""
    by_run = {x["run_id"]: x for x in s["runs"]}
    assert by_run["RUN-7D0-FC-BOTTOM"]["run_length_m"] == "18.57" and by_run["RUN-7D0-FC-BOTTOM"]["splices_per_bar"] == 1
    assert by_run["RUN-170-7C3-TOP"]["splice_valid_for_lap_up_to_m"] == "10.2300"
    assert by_run["RUN-7D4-F8-TOP"]["cut_length_m"] == "10.1"


def test_no_line_of_the_schedule_is_rebooked_by_v3027():
    lines, pop_of = B.load_candidate()
    ids = {k for k, v in pop_of.items() if v in B.POPULATIONS}
    assert len(ids) == 442 and not ids & B.t318_line_ids()


# ---------------------------------------------------------------- r2: Checker downgrade records (R-T374-6 / -6b)

def _snap(records):
    return {"records": [dict({"state": "HELD", "resolved": False, "basis_label": "UNSUPPORTED BASIS",
                              "verdict_sets": ["V3.0.9"]}, **r) for r in records]}


def test_line_under_an_unresolved_downgrade_record_is_never_scheduled():
    lines, pop_of = villa()
    snap = _snap([{"downgrade_id": "DG-X1", "line_ids": ["V-C1"]},
                  {"downgrade_id": "DG-X0", "line_ids": ["V-C1"], "verdict_sets": ["V3.0.8"]},   # its re-issue
                  {"downgrade_id": "DG-R", "line_ids": ["V-F1"], "resolved": True}])          # resolved: no hold
    rows, _ = B.build(lines, pop_of, NOW, LAPS, ledgers={}, downgrades=snap)
    r = by_id(rows)
    c = r["V-C1"]
    assert c["row_status"] == "HELD_DOWNGRADE" and c["downgrade_id"] == "DG-X1" and "re-issue of DG-X0" in c["reason"]
    assert c["cut_length_m"] == c["n"] == c["stock_bars"] == c["bar_mark"] == "" and c["net_kg_low"] is None
    assert B.fmt_kg(c["audit_kg_low"]) == "34.133000" and c["audit_basis"].startswith("UNSUPPORTED BASIS (DG-X1)")
    assert r["V-F1"]["row_status"] == "SCHEDULED"                                     # a resolved record holds nothing
    s = B.summarise(rows, _)
    assert s["populations"]["COL-MAIN-BODY"]["scheduled_net_kg"] == "0.000000"
    assert s["populations"]["COL-MAIN-BODY"]["procurement_kg"] == ["0.000000", "0.000000"]


def test_run_member_under_a_downgrade_refuses_the_run():
    lines, pop_of = villa()
    with pytest.raises(B.ScheduleRefused, match="run not schedulable whole"):
        B.build(lines, pop_of, NOW, LAPS, ledgers={}, downgrades=_snap([{"downgrade_id": "DG-G", "line_ids": ["V-G1"]}]))


def test_same_basis_footing_line_is_held_and_the_signature_is_checked_against_the_record():
    lines, pop_of = villa()
    rec = B.FTG_MESH_BASIS_RECORD
    for l in lines[:3]:     # the villa footing lines state the minimum cover as the bar-end position
        l["inputs"]["cover"] = "MINIMUM 70 mm (note: not less than 7 cm)"
        l["formula"] = "n x (side 2000 - 2 x 70 mm) x kg/m"
    rows, _ = B.build(lines, pop_of, NOW, LAPS, ledgers={}, downgrades=_snap([{"downgrade_id": rec, "line_ids": ["V-F1"]}]))
    r = by_id(rows)
    assert r["V-F1"]["row_status"] == "HELD_DOWNGRADE"
    assert r["V-F2"]["row_status"] == r["V-F3"]["row_status"] == "HELD_SAME_BASIS"       # not in the list, same basis
    assert r["V-F3"]["n"] == "" and B.fmt_kg(r["V-F3"]["audit_kg_high"]) == "12.088889"
    # a footing line with a PRINTED (not minimum) bar-end position keeps its row
    lines2, _ = villa()
    for l in lines2[:3]:
        l["inputs"]["cover"] = "MINIMUM 70 mm"
        l["formula"] = "n x (side 2000 - 2 x 70 mm) x kg/m"
    lines2[1]["inputs"]["cover"] = "PRINTED bar length 1.85 m"
    rows2, _ = B.build(lines2, pop_of, NOW, LAPS, ledgers={}, downgrades=_snap([{"downgrade_id": rec, "line_ids": ["V-F1"]}]))
    assert by_id(rows2)["V-F2"]["row_status"] == "SCHEDULED"
    # adverse: the record holds a line WITHOUT its stated basis -> the signature is wrong, the build stops
    with pytest.raises(B.ScheduleRefused, match="without the stated basis"):
        B.build(lines2, pop_of, NOW, LAPS, ledgers={}, downgrades=_snap([{"downgrade_id": rec, "line_ids": ["V-F2"]}]))


def test_committed_schedule_has_no_scheduled_line_under_any_unresolved_record():
    snap = B.load_snapshot()
    held = {lid for r in snap["records"] if not r["resolved"] for lid in r["line_ids"]}
    rows = list(csv.DictReader(open(HERE / "T374_STRAIGHT_BBS.csv", encoding="utf-8")))
    leak = [r["line_id"] for r in rows if r["line_id"] in held and r["row_status"] in ("SCHEDULED", "SCHEDULED_BOUNDED",
                                                                                         "RUN_PART")]
    assert not leak and sum(r["line_id"] in held for r in rows) == 38
    assert "V3.0.29" in snap["source_sha256"] and "V3.0.25" in snap["source_sha256"]


def test_snapshot_equals_the_board_verdict_files_when_the_board_is_present():
    if not B.BOARD_VERDICTS.is_dir():
        pytest.skip("agents/control board worktree not beside this tree")
    assert B.snapshot_downgrades(B.BOARD_VERDICTS) == B.load_snapshot()
