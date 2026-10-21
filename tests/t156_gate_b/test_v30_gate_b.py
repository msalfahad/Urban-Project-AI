"""T-156: Gate B automated checks (tools/v30_gate_b.py) on a hand-made NON-Alsenan two-run fixture (synthetic villa
SYN-GB-01; readable line ids; no client drawing). Every flag below is known by hand before the tool runs.

Trade totals per trade AND unit (quantity lines only):
  PLASTER m2        before = after = 2.00 + 1.99 + 95.51 + 0.50 = 100.00
                    L-PL-1 2.00 / 100 = 2.00 %  -> SHARE_2PCT (exactly at the threshold)
                    L-PL-2 1.99 / 100 = 1.99 %  -> no flag
                    L-PL-3 95.51 % -> SHARE_2PCT; L-PL-4 0.50 % with rule v1 -> v2 -> NEW_METHOD only
  PAINT m2          before 100 + 100 + 9000 + 3 (dropped) = 9203; after 105 + 104.99 + 9000 = 9209.99
                    L-PT-1 100 -> 105: +5.00 % -> MOVED_5PCT (share 1.14 %); L-PT-2 100 -> 104.99: +4.99 % -> none;
                    L-PT-3 9000 -> SHARE_2PCT; L-DROP-1 3.0 before only -> DROPPED_LINE (0.03 %)
  FLOOR_FINISH m2   860 + 4 x 10 + 4 (landing porcelain) = 904 both runs (R03 porcelain -> wet tile, same 10 m2)
                    L-FL-0 860 -> SHARE; L-FL-1/2/4 10 / 904 = 1.11 % -> none; L-FL-3 -> L-FL-3W: SURFACE pairing,
                    CLASS_CHANGE (item FIN.FLOOR.PORCELAIN -> FIN.FLOOR.WET_TILE), delta 0
  FLOOR_FINISH lm   skirting 1.5 + 58.5 = 60 lm, kept apart from the m2 total: L-SK-1 1.5 / 60 = 2.5 % -> SHARE
                    (mixed with 904 m2 it would read 0.16 %, no flag)
  STAIR_FINISH m2   landing marble L-LD-1 4.0 = 100 % -> SHARE + DOUBLE_FINISH; landing porcelain L-LD-2 4.0 / 904 =
                    0.44 % -> DOUBLE_FINISH only (the register's landing element has both as PRIMARY floor finishes);
                    the room element R05 with PRIMARY porcelain + HOST wet tile is NOT a double finish
  CEILING m2        L-CE-0 800 both -> SHARE; L-NEW-1 12.0 after only (12 / 813 = 1.48 %) -> NEW_LINE;
                    L-NEW-2 1.0 after only with a rule no before line uses -> NEW_LINE + NEW_METHOD
  MASONRY m2 / m    before L-MS-0 2000 m2 + L-MB-1 30 m2 (element GF/W12); after L-MS-0 2000 m2 + L-MB-1M 12 m (same
                    element) and L-MS-1 1000 m both: L-MB-1 -> L-MB-1M ELEMENT pairing, UNIT_CHANGE, no delta (30 m2
                    vs 12 m never compared); shares 30 / 2030 = 1.48 %, 12 / 1012 = 1.19 %
  WATERPROOFING m2  L-WP-0 300 both; L-HD-2 6.0 MEASURED -> 5 .. 7 BOUNDED: STATE_CHANGE (6 / 307.5 = 1.95 %), no
                    delta; L-HD-1 BLOCKED both -> no flag, listed not compared; L-CX-1 1.0 never additive with
                    L-CX-2 0.5 -> both CROSS_DEPENDENCY (0.33 %, 0.16 %)
  CONCRETE m3       footing 4.0 + column 20.0 + blinding 0.2 + slab 200.0 = 224.2: L-ST-1 footing 1.78 % ->
                    STRUCTURAL only; L-ST-3 blinding 0.09 % -> no flag (plain blinding is not a safety element)
  REINFORCEMENT kg  L-ST-2 rebar 900 -> STRUCTURAL + SHARE

Remaining (unflagged) rows sorted: L-FL-1, L-FL-2, L-FL-4, L-HD-1, L-PL-2, L-PT-2, L-ST-3 (L = 7).
sha a1b2c3d4...: N = 0xa1b2c3d4 = 161 x 2^24 + 178 x 2^16 + 195 x 256 + 212 = 2,712,847,316;
N mod 7 = 2,712,847,316 - 7 x 387,549,616 = 4 -> L-PL-2; N div 7 = 387,549,616, mod 7 = 387,549,616 - 7 x 55,364,230
= 6 -> L-ST-3.
Picker fixture (ids P-00 .. P-09, L = 10): sha 0000002a -> N 42 -> 2, 4; sha 00000021 -> N 33 -> 3, 3 collision -> 3,
4; sha 00000063 -> N 99 -> 9, 9 collision -> 9, 0 (wraps).
"""

from __future__ import annotations

import copy
import json

import pytest

from engine.source import boq_line as BL
from tools import v30_gate_b as G

PID = "SYN-GB-01"
REV = "0" * 64


def ln(lid, item, unit, net=None, *, state="MEASURED", floor="GF", room=None, element=None, rule=("UP-SYN-001", "1"),
       low=None, high=None, never=(), trade=None):
    kw = dict(project_id=PID, revision_set_sha256=REV, item_code=item, unit=unit, evidence_state=state,
              measured_net=net if state in BL.QUANTITY_STATES else None, element_id=element or lid, floor=floor,
              room_id=room, formula="synthetic", rule_id=rule[0], rule_version=rule[1], never_additive_with=never)
    if state == "BOUNDED_EXPOSURE":
        kw["bounded_range"] = {"low": low, "high": high, "basis": "synthetic"}
        kw["rfi"] = {"question": "synthetic hold"}
    if state == "BLOCKED_RFI":
        kw["rfi"] = {"question": "synthetic block"}
    if trade:
        kw["trade"] = trade
    line = BL.make_line(**kw)
    line["line_id"] = lid
    return line


def runs():
    common = [ln("L-PL-1", "FIN.PLASTER", "m2", 2.00), ln("L-PL-2", "FIN.PLASTER", "m2", 1.99),
              ln("L-PL-3", "FIN.PLASTER", "m2", 95.51),
              ln("L-PT-3", "FIN.PAINT", "m2", 9000.0),
              ln("L-FL-0", "FIN.FLOOR.PORCELAIN", "m2", 860.0, room="R00", element="R00"),
              ln("L-FL-1", "FIN.FLOOR.PORCELAIN", "m2", 10.0, room="R01", element="R01"),
              ln("L-FL-2", "FIN.FLOOR.PORCELAIN", "m2", 10.0, room="R02", element="R02"),
              ln("L-FL-4", "FIN.FLOOR.PORCELAIN", "m2", 10.0, room="R04", element="R04"),
              ln("L-SK-1", "FIN.SKIRTING", "lm", 1.5), ln("L-SK-2", "FIN.SKIRTING", "lm", 58.5),
              ln("L-LD-1", "FIN.MARBLE.LANDING", "m2", 4.0, floor="1F", element="LD1"),
              ln("L-LD-2", "FIN.FLOOR.PORCELAIN", "m2", 4.0, floor="1F", element="LD1-FLOOR"),
              ln("L-CE-0", "FIN.CEILING", "m2", 800.0),
              ln("L-MS-0", "MAS.BLOCK", "m2", 2000.0), ln("L-MS-1", "MAS.BLOCK", "m", 1000.0),
              ln("L-WP-0", "FIN.WP.FLOOR", "m2", 300.0),
              ln("L-HD-1", "FIN.WP.FLOOR", "m2", state="BLOCKED_RFI"),
              ln("L-CX-1", "FIN.WP.UPTURN", "m2", 1.0, never=("L-CX-2",)),
              ln("L-CX-2", "FIN.WP.DOORWAY", "m2", 0.5),
              ln("L-ST-1", "STR.CONC.FOOTING", "m3", 4.0), ln("L-ST-4", "STR.CONC.COLUMN", "m3", 20.0),
              ln("L-ST-3", "STR.CONC.BLINDING", "m3", 0.2), ln("L-ST-5", "STR.CONC.SLAB", "m3", 200.0),
              ln("L-ST-2", "STR.REBAR", "kg", 900.0)]
    before = copy.deepcopy(common) + [
        ln("L-PL-4", "FIN.PLASTER", "m2", 0.50, rule=("UP-SYN-PLASTER", "1")),
        ln("L-PT-1", "FIN.PAINT", "m2", 100.0), ln("L-PT-2", "FIN.PAINT", "m2", 100.0),
        ln("L-DROP-1", "FIN.PAINT", "m2", 3.0),
        ln("L-FL-3", "FIN.FLOOR.PORCELAIN", "m2", 10.0, room="R03", element="R03"),
        ln("L-MB-1", "MAS.BLOCK", "m2", 30.0, element="GF/W12"),
        ln("L-HD-2", "FIN.WP.FLOOR", "m2", 6.0)]
    after = copy.deepcopy(common) + [
        ln("L-PL-4", "FIN.PLASTER", "m2", 0.50, rule=("UP-SYN-PLASTER", "2")),
        ln("L-PT-1", "FIN.PAINT", "m2", 105.0), ln("L-PT-2", "FIN.PAINT", "m2", 104.99),
        ln("L-FL-3W", "FIN.FLOOR.WET_TILE", "m2", 10.0, room="R03", element="R03"),
        ln("L-MB-1M", "MAS.BLOCK", "m", 12.0, element="GF/W12"),
        ln("L-HD-2", "FIN.WP.FLOOR", "m2", state="BOUNDED_EXPOSURE", low=5.0, high=7.0),
        ln("L-NEW-1", "FIN.CEILING", "m2", 12.0),
        ln("L-NEW-2", "FIN.CEILING", "m2", 1.0, rule=("UP-SYN-CEIL", "2"))]
    return before, after


REGISTER = {"schema": "URBAN_ELEMENT_REGISTER_V0", "elements": [
    {"id": "SYN-GB-01/r/1F/LANDING/LD1", "kind": "LANDING", "boq_lines": [
        {"line_id": "L-LD-1", "item_code": "FIN.MARBLE.LANDING", "role": "PRIMARY"},
        {"line_id": "L-LD-2", "item_code": "FIN.FLOOR.PORCELAIN", "role": "PRIMARY"}]},
    {"id": "SYN-GB-01/r/GF/ROOM/R05", "kind": "ROOM", "boq_lines": [
        {"line_id": "L-FL-1", "item_code": "FIN.FLOOR.PORCELAIN", "role": "PRIMARY"},
        {"line_id": "L-SK-2", "item_code": "FIN.SKIRTING", "role": "PRIMARY"},
        {"line_id": "L-X-HOST", "item_code": "FIN.FLOOR.WET_TILE", "role": "HOST"}]}]}

EXPECTED = {
    "L-PL-1": {"SHARE_2PCT"}, "L-PL-2": set(), "L-PL-3": {"SHARE_2PCT"}, "L-PL-4": {"NEW_METHOD"},
    "L-PT-1": {"MOVED_5PCT"}, "L-PT-2": set(), "L-PT-3": {"SHARE_2PCT"}, "L-DROP-1": {"DROPPED_LINE"},
    "L-FL-0": {"SHARE_2PCT"}, "L-FL-1": set(), "L-FL-2": set(), "L-FL-4": set(), "L-FL-3W": {"CLASS_CHANGE"},
    "L-SK-1": {"SHARE_2PCT"}, "L-SK-2": {"SHARE_2PCT"},
    "L-LD-1": {"SHARE_2PCT", "DOUBLE_FINISH"}, "L-LD-2": {"DOUBLE_FINISH"},
    "L-CE-0": {"SHARE_2PCT"}, "L-NEW-1": {"NEW_LINE"}, "L-NEW-2": {"NEW_LINE", "NEW_METHOD"},
    "L-MS-0": {"SHARE_2PCT"}, "L-MS-1": {"SHARE_2PCT"}, "L-MB-1M": {"UNIT_CHANGE"},
    "L-WP-0": {"SHARE_2PCT"}, "L-HD-1": set(), "L-HD-2": {"STATE_CHANGE"},
    "L-CX-1": {"CROSS_DEPENDENCY"}, "L-CX-2": {"CROSS_DEPENDENCY"},
    "L-ST-1": {"STRUCTURAL"}, "L-ST-4": {"STRUCTURAL", "SHARE_2PCT"}, "L-ST-3": set(),
    "L-ST-5": {"STRUCTURAL", "SHARE_2PCT"}, "L-ST-2": {"STRUCTURAL", "SHARE_2PCT"}}
POOL = ["L-FL-1", "L-FL-2", "L-FL-4", "L-HD-1", "L-PL-2", "L-PT-2", "L-ST-3"]
SHA = "a1b2c3d4" + "0" * 32


def _flags(doc):
    return {r["row_id"]: set(r["flags"]) for r in doc["rows"]}


def run(**kw):
    b, a = runs()
    return G.diff(b, a, register=REGISTER, **kw)


def test_every_flag_matches_the_hand_table():
    assert _flags(run()) == EXPECTED


def test_pairings_and_no_cross_unit_delta():
    rows = {r["row_id"]: r for r in run()["rows"]}
    assert rows["L-MB-1M"]["pairing"] == "ELEMENT" and rows["L-MB-1M"]["before_line_id"] == "L-MB-1"
    assert rows["L-MB-1M"]["unit"] == "m2->m" and rows["L-MB-1M"]["delta"] is None
    assert rows["L-FL-3W"]["pairing"] == "SURFACE" and rows["L-FL-3W"]["delta"] == 0.0
    assert rows["L-FL-3W"]["item_code"] == "FIN.FLOOR.PORCELAIN->FIN.FLOOR.WET_TILE"
    assert rows["L-PT-1"]["delta"] == 5.0 and rows["L-PT-1"]["delta_pct"] == 5.0
    assert rows["L-PL-1"]["after_share_pct"] == 2.0 and rows["L-PL-2"]["after_share_pct"] == 1.99
    assert rows["L-DROP-1"]["after_line_id"] is None and rows["L-NEW-1"]["before_line_id"] is None


def test_held_lines_are_listed_never_zero():
    doc = run()
    rows = {r["row_id"]: r for r in doc["rows"]}
    assert rows["L-HD-2"]["delta"] is None and rows["L-HD-2"]["after"]["value"] is None
    assert rows["L-HD-2"]["after"]["low"] == 5.0 and rows["L-HD-2"]["after"]["high"] == 7.0
    assert {x["row_id"] for x in doc["not_compared"]} == {"L-HD-1", "L-HD-2"}
    assert doc["trade_totals"]["after"]["WATERPROOFING|m2"] == 301.5          # 300 + 1.0 + 0.5, held lines not summed
    assert doc["trade_totals"]["before"]["WATERPROOFING|m2"] == 307.5


def test_units_never_mixed_in_one_trade():
    tot = run()["trade_totals"]["after"]
    assert tot["FLOOR_FINISH|m2"] == 904.0 and tot["FLOOR_FINISH|lm"] == 60.0
    assert tot["MASONRY|m2"] == 2000.0 and tot["MASONRY|m"] == 1012.0


def test_summary_counts_per_rule():
    s = run()["summary"]
    want = {}
    for fl in EXPECTED.values():
        for x in fl:
            want[x] = want.get(x, 0) + 1
    assert {k: v["caught"] for k, v in s["per_rule"].items() if v["caught"]} == want
    assert s["per_rule"]["DOUBLE_FINISH"]["only_this_rule"] == 1                 # L-LD-2
    # PL-1, PL-3, PT-3, FL-0, SK-1, SK-2, CE-0, MS-0, MS-1, WP-0
    assert s["per_rule"]["SHARE_2PCT"]["only_this_rule"] == 10
    assert s["rows"] == len(EXPECTED) and s["unflagged"] == len(POOL)


def test_random_picks_on_the_diff_fixture():
    doc = run()
    assert sorted(G.remaining(doc)) == POOL
    p = G.pick(G.remaining(doc), SHA)
    assert p["n"] == 2712847316 and p["L"] == 7 and p["positions"] == [4, 6] and p["ids"] == ["L-PL-2", "L-ST-3"]


@pytest.mark.parametrize("sha,positions", [("0000002a", [2, 4]), ("00000021", [3, 4]), ("00000063", [9, 0]),
                                           ("0000002A" + "f" * 32, [2, 4])])
def test_picker_by_hand(sha, positions):
    ids = [f"P-{i:02d}" for i in range(9, -1, -1)]                               # given unsorted
    p = G.pick(ids, sha)
    assert p["L"] == 10 and p["positions"] == positions and p["ids"] == [f"P-{i:02d}" for i in positions]


def test_picker_edges_and_refusals():
    assert G.pick([], "deadbeef")["ids"] == []
    assert G.pick(["only"], "deadbeef")["ids"] == ["only"]
    assert G.pick(["b", "a"], "00000000")["ids"] == ["a", "b"]                 # N 0: 0, 0 -> 0, 1
    for bad in ("abc", "xyz12345", ""):
        with pytest.raises(ValueError):
            G.pick(["a", "b"], bad)
    with pytest.raises(ValueError):
        G.pick(["a", "a"], "deadbeef")


def test_ambiguous_group_never_pairs_and_duplicates_refused():
    b = [ln("B1", "FIN.PAINT", "m2", 1.0, element="E1"), ln("B2", "FIN.PLASTER", "m2", 1.0, element="E1")]
    a = [ln("A1", "FIN.CEILING", "m2", 1.0, element="E1"), ln("A2", "FIN.WALL.TILE", "m2", 1.0, element="E1")]
    rows = G.diff(b, a)["rows"]
    assert all(r["pairing"] == "NONE" for r in rows) and len(rows) == 4
    with pytest.raises(ValueError):
        G.diff(b + [copy.deepcopy(b[0])], a)


def test_ledger_pairs_a_replaced_line():
    b = [ln("OLD", "STR.CONC.STRAP", "m3", 2.0, element=None)]
    a = [ln("NEW", "STR.CONC.STRAP", "m3", 2.2, element="STRAP-1")]
    assert G.diff(b, a)["rows"][0]["pairing"] == "NONE"
    led = {"rows": [{"line_id": "OLD", "line_ids": ["NEW", "OLD"]}]}
    r = G.diff(b, a, ledgers=[led])["rows"]
    assert len(r) == 1 and r[0]["pairing"] == "LEDGER" and r[0]["delta"] == pytest.approx(0.2)
    assert set(r[0]["flags"]) == {"MOVED_5PCT", "STRUCTURAL", "SHARE_2PCT"}


def test_changed_rows_and_counts_on_changed():
    doc = run()
    ch = {r["row_id"] for r in doc["rows"] if r["changed"]}
    # by hand: rule v1 -> v2, 100 -> 105, 100 -> 104.99, dropped, porcelain -> wet tile, m2 -> m, measured -> held,
    # two new ceiling lines
    assert ch == {"L-PL-4", "L-PT-1", "L-PT-2", "L-DROP-1", "L-FL-3W", "L-MB-1M", "L-HD-2", "L-NEW-1", "L-NEW-2"}
    s = doc["summary"]
    assert s["changed_rows"] == 9 and s["changed_rows_unflagged"] == 1                # L-PT-2 (+4.99 %)
    assert s["per_rule"]["SHARE_2PCT"]["caught_on_changed"] == 0
    assert s["per_rule"]["NEW_LINE"]["caught_on_changed"] == 2
    rows = {r["row_id"]: r for r in doc["rows"]}
    assert rows["L-PL-4"]["changed_fields"] == ["rule"] and rows["L-NEW-1"]["changed_fields"] == ["*"]


def test_text_only_change_is_visible_without_a_flag():
    b = [ln("M1", "FIN.PAINT", "m2", 1.0), ln("M2", "FIN.PAINT", "m2", 99.0)]
    a = copy.deepcopy(b)
    a[0]["notes"] = "evidence attached"
    r = {x["row_id"]: x for x in G.diff(b, a)["rows"]}
    assert r["M1"]["changed"] and r["M1"]["changed_fields"] == ["notes"] and r["M1"]["flags"] == []


def test_ledger_downstream_lines_are_cross_dependencies():
    b = [ln("C1", "STR.CONC.COLUMN", "m3", 0.42), ln("S1", "STR.REBAR", "kg", 10.0), ln("P1", "FIN.PAINT", "m2", 1.0),
         ln("P2", "FIN.PAINT", "m2", 99.0)]
    a = copy.deepcopy(b)
    led = {"rows": [{"line_id": "P1", "line_ids": ["P1"], "downstream": [{"line_id": "P2", "item_code": "FIN.PAINT"}]},
                    {"line_id": "C1", "line_ids": ["C1"], "downstream": []}]}
    f = _flags(G.diff(b, a, ledgers=[led]))
    assert "CROSS_DEPENDENCY" in f["P1"] and "CROSS_DEPENDENCY" in f["P2"]
    assert "CROSS_DEPENDENCY" not in f["C1"] and "CROSS_DEPENDENCY" not in f["S1"]


# ---------------------------------------------------------------------------------------- mutations (must be caught)
@pytest.mark.parametrize("kw,row,flag,present", [
    ({"share_pct": 2.01}, "L-PL-1", "SHARE_2PCT", False),       # threshold one step up loses the 2.00 % line
    ({"share_pct": 1.98}, "L-PL-2", "SHARE_2PCT", True),        # one step down catches the 1.99 % line
    ({"move_pct": 5.01}, "L-PT-1", "MOVED_5PCT", False),
    ({"move_pct": 4.98}, "L-PT-2", "MOVED_5PCT", True)])
def test_threshold_mutations_change_the_hand_table(kw, row, flag, present):
    f = _flags(run(**kw))
    assert (flag in f[row]) is present and f != EXPECTED


def test_strict_comparison_mutation_is_caught(monkeypatch):
    monkeypatch.setattr(G, "_at_least", lambda pct, t: pct > t + G.PCT_EPS)
    assert _flags(run()) != EXPECTED


def test_mixed_unit_total_mutation_is_caught(monkeypatch):
    def mixed(recs):
        t = {}
        for r in recs.values():
            if r["value"] is not None:
                t[r["trade"]] = t.get(r["trade"], 0.0) + r["value"]
        return {(tr, u): t[tr] for tr in t for u in {r["unit"] for r in recs.values() if r["trade"] == tr}}
    monkeypatch.setattr(G, "trade_totals", mixed)
    assert "SHARE_2PCT" not in _flags(run())["L-SK-1"]


def test_without_register_no_double_finish_and_without_unit_pairing_new_dropped(monkeypatch):
    b, a = runs()
    f = _flags(G.diff(b, a))
    assert "DOUBLE_FINISH" not in f["L-LD-2"] and f["L-LD-2"] == set()
    monkeypatch.setattr(G, "_unique_groups", lambda recs, key: {})
    f = _flags(G.diff(b, a, register=REGISTER))
    assert f["L-MB-1M"] == {"NEW_LINE"} and f["L-MB-1"] == {"DROPPED_LINE"}


def test_cli_writes_both_files(tmp_path):
    b, a = runs()
    (tmp_path / "b.json").write_text(json.dumps(b), encoding="utf-8")
    (tmp_path / "a.json").write_text(json.dumps(a), encoding="utf-8")
    (tmp_path / "reg.json").write_text(json.dumps(REGISTER), encoding="utf-8")
    assert G.main(["diff", str(tmp_path / "b.json"), str(tmp_path / "a.json"), "--out", str(tmp_path / "o"),
                   "--sha", SHA, "--register", str(tmp_path / "reg.json")]) == 0
    doc = json.loads((tmp_path / "o" / "GATE_B_DIFF.json").read_text(encoding="utf-8"))
    assert doc["random_picks"]["ids"] == ["L-PL-2", "L-ST-3"]
    csv_text = (tmp_path / "o" / "GATE_B_DIFF.csv").read_text(encoding="utf-8")
    assert csv_text.count("\n") == len(EXPECTED) + 1 and "MOVED_5PCT" in csv_text
