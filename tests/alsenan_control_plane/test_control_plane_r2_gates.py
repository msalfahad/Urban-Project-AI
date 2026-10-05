"""ALSENAN CONTROL-PLANE ROUND 2 - control gates G01-G23 against production behaviour and the frozen R2 registers.

Each gate has two kinds of proof:
  * BEHAVIOUR - the production function is called on a synthetic input and its output is asserted (the gate passes
    only because the code changed, not because a register was redefined);
  * REAL EVIDENCE - the committed R2 registers (research/alsenan_control_plane_02/registers, hash-frozen in INDEX.json)
    show the same behaviour on Alsenan.
G15 and G23 stay xfail(strict=True) (engineer answers needed); G11 / G13 were promoted in Round 3 with their consumers,
so an XPASS turns red. A no-gaming group pins the raw counts that must NOT have been zeroed (46.63 m ambiguous wall,
187.82 m unpaired boundary, 35 wet labels, 26 D5 occurrences) and a firewall group proves the builders never read a
benchmark.
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
LAB = ROOT / "research" / "external_engine_lab"
CP2 = ROOT / "research" / "alsenan_control_plane_02"
REGS = CP2 / "registers"
for p in (str(LAB), str(CP2), str(ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

import alsenan_v3_layers as V3L  # noqa: E402
import alsenan_v3_registers as V3R  # noqa: E402
import alsenan_v3_structure as V3S  # noqa: E402
import static_registers as STATIC  # noqa: E402
from engine.source import opening_evidence as OE  # noqa: E402
from engine.source import release_model_v2 as R  # noqa: E402
from engine.source import schedule_grammar as SG  # noqa: E402
from engine.source import trade_dependency as TD  # noqa: E402

VERIFIED_STATES = (R.VERIFIED_COMPLETE, R.LOWER_BOUND)


def _reg(name):
    return json.loads((REGS / f"{name}.json").read_text())


def _spaces():
    return {r["room"]: r for r in _reg("ROOM_SPACES_V2")["rows"]}


def _migration():
    return _reg("RELEASE_V2_MIGRATION_REGISTER")["rows"]


def _candidate():
    return {(x["code"], x["line_id"]): x for x in _reg("ALSENAN_CONTROL_V2_CANDIDATE")["lines"]}


# =============================================================================================== synthetic builders
def _finish_row(room, status, area=10.0, cls="DRY", name="ROOM", skirting=12.0, zone_classes=None):
    return {"room": room, "floor": "GF", "name_en": name, "name_ar": "", "room_class": cls, "status": status,
            "zone_classes": zone_classes or [cls], "floor_area_m2": area, "floor_formula": "f",
            "floor_material": "PORCELAIN", "floor_material_authority": "A", "skirting_m": skirting,
            "ceiling_area_m2": area, "ceiling_formula": "c", "cornice_m": 12.0, "wall_tile_gross_m2": 20.0,
            "paint_blocked_length_m": 0.0}


def _L(rows):
    return {"finishes": {"rows": rows}, "rooms": {"rows": []}}


def _footing_ctx(defn, L=4.0, W=3.6, status="COMPUTED_SHADOW_COMPLETE", typ="FX"):
    defn = dict(defn, element="FOOTING", type=typ)
    return {"a3": {"rebar": {"definitions": [defn]},
                   "footings": {"rows": [{"type": typ, "status": status, "dims": {"L": {"m": L}, "W": {"m": W}}}]}}}


def _beam_ctx(defs, occ):
    sheets = {fl: {"occurrences": []} for fl in V3S.FLOORS}
    sheets["GF"]["occurrences"] = occ
    return {"a3": {"rebar": {"definitions": defs}}, "b2a": {"sheets": sheets}}


def _occ(typ, state="MEASURED", B=30, D=50, Ls=5.0, Lc=4.6):
    return {"type": typ, "state": state, "B_cm": B, "D_cm": D, "tags": [f"X|H{typ}|"],
            "lengths": {"SUPPORT_CENTRELINE_LENGTH": Ls, "CLEAR_FACE_TO_FACE_LENGTH": Lc}}


BEAM_DEF = {"element": "BEAM", "type": "B1", "bars": {"top": [{"count": 2, "dia_mm": 12, "per_m": False}],
                                                      "bottom": [{"count": 3, "dia_mm": 16, "per_m": False}],
                                                      "stirrups": [{"count": 6, "dia_mm": 8, "per_m": False}]}}
PER_M_DEF = {"bars": {"long_bars": [{"count": 6, "dia_mm": 14, "per_m": True}],
                      "short_bars": [{"count": 6, "dia_mm": 14, "per_m": True}]}, "boxed": ["9 Ø 14/m"]}


def _column_ctx(volume_m3, state="NOT_DRAWN_ON_STOREY_SHEET"):
    defn = {"element": "COLUMN", "type": "C1", "bars": {"GROUND FLOOR": [{"count": 8, "dia_mm": 16}]}}
    row = {"type": "C1", "B_cm": 20.0, "D_cm": 50.0, "storey_band": "GROUND FLOOR", "floor": "GF",
           "tag_key": "X|H1|", "state": state, "volume_m3": volume_m3}
    return {"a3": {"rebar": {"definitions": [defn]}}, "b2a": {"intervals": [{"from": "GF", "interval_m": 4.5}],
                                                              "columns": {"rows": [row]}}}


def _barsets(out):
    return [x for x in out if x.get("status") != "BLOCKED"]


# =============================================================================================== gates
def test_G01_review_room_floor_never_verified():
    fl = [x for x in V3R.flooring(_L([_finish_row("R1", "COMPUTED_REVIEW"), _finish_row("R2", "BLOCKED"),
                                      _finish_row("R3", "COMPUTED")])) if x["code"].startswith("F-FL-")]
    assert [x["status"] for x in fl] == ["REVIEW", "BLOCKED", "COMPUTED"]
    v = R.release_v2(technical_class="DERIVED", measured_qty=10.0, components={"geometry": (R.HIGH, "g"),
                     "upstream_status": (R.MEDIUM, "review")}, upstream_status="REVIEW")
    assert v["release_state"] == R.PROVISIONAL and v["qty_verified"] is None
    sp = _spaces()
    floor = [r for r in _migration() if r["code"].startswith("F-FL-") and r["room"]]
    review = [r for r in floor if sp[r["room"]]["upstream_status"] != "COMPUTED"]
    assert review and not [r for r in review if r["v2_release_state"] in VERIFIED_STATES or r["v2_in_verified_total"]]
    # the 325.251 m2 the round-1 audit found as COMPUTED is now wholly outside the verified total
    assert round(sum(r["new_measured_qty"] or 0.0 for r in review), 3) == pytest.approx(325.251, abs=0.01)


def test_G02_unresolved_semantic_space_never_released_as_one_clean_zone():
    mixed = {"semantic_state": "MULTI_UNRESOLVED", "zone_classes": ["DRY", "WET"], "upstream_status": "COMPUTED"}
    ev = TD.evaluate("FLOOR_FINISH", mixed)
    assert TD.BLOCKED_SPLIT in ev["blocking"]
    v = R.release_v2(technical_class="DERIVED", measured_qty=24.94, components=ev["components"])
    assert v["release_state"] == R.BLOCKED and v["qty_audit"] == 24.94
    assert not TD.evaluate("CEILING", mixed)["blocking"]                   # same treatment for both zones
    void = dict(mixed, zone_classes=["DRY", "VOID"], void_split_resolved=True)
    assert not TD.evaluate("FLOOR_FINISH", void)["blocking"]               # established void outline
    sp = _spaces()
    multi = {k for k, s in sp.items() if s["semantic_state"] == "MULTI_UNRESOLVED"}
    assert multi == {"GF-Z04", "GF-Z06", "1F-Z06"}
    lines = [r for r in _migration() if r["room"] in multi]
    assert lines and not [r for r in lines if r["v2_release_state"] == R.VERIFIED_COMPLETE]
    for z in ("GF-Z04", "GF-Z06"):
        st = {r["code"].split("-")[0] + "-" + r["code"].split("-")[1]: r["v2_release_state"]
              for r in lines if r["room"] == z}
        assert st["F-FL"] == st["T-WT"] == st["T-WP"] == R.BLOCKED


def test_G03_dry_wins_removed():
    assert V3L._room_class("DEWANEYA / Wash", "") == V3L.MIXED_SEMANTIC_ZONE
    assert V3L._room_class("PANTRY / SALOON / RECEPTION / Wash / DINING / GARDEN", "") == V3L.MIXED_SEMANTIC_ZONE
    assert V3L._room_class("SALOON / DINING", "") == "DRY"                 # one class -> that class
    assert V3L._room_class("Wash", "") == "WET"
    rng = random.Random(7757)
    names = ["PANTRY", "SALOON", "Wash", "DINING", "GARDEN", "BATH", "KITCHEN", "W.C", "LIVING AREA"]
    for _ in range(60):
        pick = rng.sample(names, rng.randint(2, 5))
        base = V3L._room_class(" / ".join(pick), "")
        rng.shuffle(pick)
        assert V3L._room_class(" / ".join(pick), "") == base
        if any(n in pick for n in ("Wash", "BATH", "W.C")) and base != "WET":
            assert base == V3L.MIXED_SEMANTIC_ZONE                        # a wet zone is never absorbed as DRY


def test_G04_every_wet_label_accounted():
    mixed = _finish_row("Z", "COMPUTED_REVIEW", cls=V3L.MIXED_SEMANTIC_ZONE, name="DEWANEYA / Wash",
                        zone_classes=["DRY", "WET"])
    ctx = {"b2a": {"architecture": {"waterproofing": {"roof": []}}}}
    L = dict(_L([mixed]), substructure={"footing_wp_m2": 1.0, "ground_beam_wp_m2": 1.0, "footing_membrane_m2": 1.0})
    out = [x for x in V3R.tile_wp(ctx, L) if x.get("trace") == "Z"]
    assert {x["code"] for x in out} == {"T-WT-Z", "T-WP-Z"}
    assert all(x["status"] == "BLOCKED" and "BLOCKED_SEMANTIC_TRADE_BOUNDARY" in x["formula"] for x in out)
    w = _reg("WET_LABEL_ACCOUNTING_REGISTER")
    allowed = {"WET_LABEL_BOUND_TO_REGION", "WET_LABEL_BLOCKED_NO_PHYSICAL_SITE",
               "WET_LABEL_BLOCKED_SEMANTIC_TRADE_BOUNDARY", "WET_LABEL_SOURCE_CONFLICT", "WET_LABEL_NOT_IN_SCOPE"}
    assert w["unaccounted_wet_labels"] == [] and len(w["rows"]) == 35
    assert all(r["terminal_state"] in allowed for r in w["rows"])
    assert w["wet_trade_population_complete"] is False                     # blocked labels keep the trade open
    cand = _candidate()
    for z in ("GF-Z04", "GF-Z06"):
        assert {cand[k]["new_release_state"] for k in cand if k[0] in (f"T-WT-{z}", f"T-WP-{z}")} == {R.BLOCKED}


def test_G05_skirting_status_propagates():
    for st, want in (("COMPUTED", "COMPUTED"), ("COMPUTED_REVIEW", "REVIEW"), ("BLOCKED", "BLOCKED"),
                     ("SOMETHING_NEW", "BLOCKED")):
        sk = [x for x in V3R.flooring(_L([_finish_row("R1", st)])) if x["code"].startswith("F-SK-")]
        assert sk[0]["status"] == want, st
    sp = _spaces()
    sk = [r for r in _migration() if r["code"].startswith("F-SK-") and r["room"]
          and sp[r["room"]]["upstream_status"] != "COMPUTED"]
    assert sk and not [r for r in sk if r["v2_release_state"] in VERIFIED_STATES]


def test_G06_ceiling_status_propagates():
    for st, want in (("COMPUTED", "COMPUTED"), ("COMPUTED_REVIEW", "REVIEW"), ("BLOCKED", "BLOCKED")):
        ce = [x for x in V3R.ceilings(_L([_finish_row("R1", st)])) if x["code"] == "CE-R1"]
        assert ce[0]["status"] == want, st
    sp = _spaces()
    ce = [r for r in _migration() if r["code"].startswith("CE-") and r["room"]
          and sp[r["room"]]["upstream_status"] != "COMPUTED"]
    assert ce and not [r for r in ce if r["v2_release_state"] in VERIFIED_STATES]


def test_G07_partial_never_procurement_eligible_v2():
    ok = {"geometry": (R.HIGH, "g"), "upstream_status": (R.HIGH, "u")}
    assert not R.release_v2(technical_class="PARTIAL", measured_qty=10.0, components=ok)["procurement_eligible_v2"]
    assert R.release_v2(technical_class="PARTIAL", measured_qty=10.0, components=ok,
                        owner_approved_procurement=True)["procurement_eligible_v2"]
    rows = _migration()
    assert not [r for r in rows if r["v2_release_state"] != R.VERIFIED_COMPLETE and r["v2_procurement_eligible"]]
    lb = [r for r in rows if r["v2_release_state"] == R.LOWER_BOUND]
    assert len(lb) == 43 and [r for r in lb if r["old_procurement_eligible"]]   # V1 still says eligible; V2 says no


def test_G08_every_structural_source_object_has_a_terminal_state():
    import alsenan_structural_source_v2 as SRC
    cov = _reg("STRUCTURAL_SOURCE_COVERAGE_V2")
    states = set(cov["terminal_states"])
    assert len(cov["rows"]) == cov["accounted"] == 332 and cov["unaccounted"] == []
    assert all(r["coverage_state"] in states for r in cov["rows"])
    assert len({r["object_id"] for r in cov["rows"]}) == 332
    # accounting is not interpretation: the separate metric stays honest (well below 100 %)
    assert cov["structural_source_accounting_pct"] == 100.0
    assert cov["structural_source_interpretation_completion_pct"] < 60.0
    assert cov["counts"]["BLOCKED_UNREAD"] == 7 and cov["counts"]["SOURCE_CONFLICT"] == 2
    # every schedule block INSERT in the DXF has exactly one coverage row (re-read from the source, not the register)
    src = SRC.read()
    inserts = [f"ST7757.dxf:{b['block']}:{b['handle']}" for rows in src["blocks"].values() for b in rows]
    assert len(inserts) == 77 and set(inserts) <= {r["object_id"] for r in cov["rows"]}


def test_G09_every_structural_population_has_a_terminal_state():
    led = _reg("TERMINAL_OBJECT_LEDGER")["check"]
    assert led["conserved"] and led["admitted"] == led["terminated"]
    assert led["unterminated"] == led["double_terminations"] == led["unknown_terminations"] == []
    pop = _reg("STRUCTURAL_POPULATION_COVERAGE_V2")
    assert all(r.get("terminal_state") or r.get("release_state") for r in pop["rows"])
    bp = pop["by_population"]
    assert bp["CONTINUOUS_BEAM"] == {"BLOCKED": 11} and bp["STRAP_BEAM"] == {"BLOCKED": 3}   # D1, D4 explicit
    assert bp["COLUMN"]["BLOCKED"] == 26 and bp["POPULATION:STAIRS"] == {"BLOCKED": 1}
    assert led["by_terminal_state"]["REBAR_BLOCKED_PER_METRE_PENDING_CONSUMER_V2"] == 4         # D2 explicit
    assert led["by_terminal_state"]["REBAR_BLOCKED_SCHEDULE_CELL_UNREAD"] == 1                  # D3 explicit


def test_G10_cb_definitions_captured_from_source():
    d = _reg("STRUCTURAL_DEFINITION_REGISTER_V2")
    cbs = [x for x in d["definitions"] if x["element"] == "CONTINUOUS_BEAM"]
    assert sorted(int(x["type"][2:]) for x in cbs) == list(range(1, 14))
    for x in cbs:
        assert x["block"] in ("C-BEAM2", "C-BEAM3") and x["insert_handle"]
        assert x["fields"]["bottom_bars_per_span"] and x["fields"]["design_load_t_per_m"]
        # T/M is a design load: it is never a reinforcement field
        assert not [t for b in x["fields"]["bottom_bars_per_span"] for t in b["tags"] if t.startswith("T/M")]
    cov = {r["object"]: r for r in _reg("STRUCTURAL_SOURCE_COVERAGE_V2")["rows"]}
    assert all(cov[f"CONTINUOUS_BEAM CB{i}"]["consumer_state"] == "PENDING_REBAR_CONSUMER_V2" for i in range(1, 14))


def test_G11_two_layer_footing_quantity_consumer():
    """Round 3 consumer (alsenan_rebar_v3): per-metre counts over side - 2 x cover, both layers; the V3a function
    keeps its BLOCKED terminal records (V3b is frozen and not re-run)."""
    import alsenan_rebar_v3 as R3
    from engine.source import rebar_model as RM
    b = R3.Build.__new__(R3.Build)
    b.sha = "f" * 64
    df = {"element": "FOOTING_2_LAYER", "type": "FX", "block": "FTB", "insert_handle": "H", "page": 9,
          "raw_attributes": {}, "fields": {k: {"count": 6, "dia_mm": 14, "per_m": True} for k in
                                           ("TOP_short", "TOP_long", "BOTTOM_short", "BOTTOM_long")}}
    out = b._ftb("P", "O", df, 4.0, 3.6, 0.5, 0.07)
    mesh = [c for c in out if c["bar_role"] in ("TOP_SHORT", "TOP_LONG", "BOTTOM_SHORT", "BOTTOM_LONG")]
    assert len(mesh) == 4 and all(c["count_mode"] == "BARS_PER_METRE" for c in mesh)
    assert min(c["count"]["verified"] for c in mesh) > 6 and all(c["state"] != RM.BLOCKED for c in mesh)


def test_G12_ff_emits_a_blocked_population():
    out = V3S.footing_rebar(_footing_ctx({"bars": {}, "boxed": None, "fields": {"FO-TY": "FF"}}, typ="FF"))
    assert len(out) == 1 and out[0]["status"] == "BLOCKED"
    assert out[0]["terminal_state"] == "REBAR_BLOCKED_SCHEDULE_CELL_UNREAD"
    rows = [r for r in _reg("TERMINAL_OBJECT_LEDGER")["rows"]
            if r["terminal_state"] == "REBAR_BLOCKED_SCHEDULE_CELL_UNREAD"]
    assert len(rows) == 1 and "FF" in json.dumps(rows[0])


def test_G13_strap_rebar_quantity_consumer():
    """Round 3 consumer (alsenan_rebar_v3.Build.straps): SB1 / SB3 bars and stirrups; SB2 stays a BLOCKED conflict."""
    import alsenan_rebar_v3 as R3
    from engine.source import rebar_model as RM
    from collections import defaultdict
    b = R3.Build.__new__(R3.Build)
    b.sha, b.comps, b.pops, b.rc_occ, b.registers = "f" * 64, [], [], [], defaultdict(list)
    bar = lambda n, d, **k: dict({"count": n, "dia_mm": d, "per_m": False, "tags": ["A", "B"]}, **k)
    sb = lambda h, B, n1: {"element": "STRAP_BEAM", "type": "SB2" if h != "H1" else "SB1", "block": "SBT",
                           "insert_handle": h, "page": 10, "raw_attributes": {"W": str(B)},
                           "fields": {"B_cm": B, "H_cm": 50.0, "bottom": bar(n1, 16), "top": bar(5, 18),
                                      "stirrups_per_m": bar(8, 8, semantics="STIRRUPS_PER_METRE")}}
    b.dmap = defaultdict(list)
    for d in (sb("H1", 70.0, 7), sb("H2", 100.0, 10), sb("H3", 80.0, 10)):
        b.dmap[(d["element"], d["type"])].append(d)
    b.ctx = {"a3": {"straps": {"rows": [{"type": "SB1", "mark_key": "X|H9|", "length_m": 4.0},
                                        {"type": "SB2", "mark_key": "X|H8|", "length_m": 2.0}]}}}
    b.straps()
    st = {p["occurrence_id"].split(":")[1]: p["release_state"] for p in b.pops}
    assert st == {"SB1": RM.LB, "SB2": RM.BLK}
    assert len(b.registers["STRAP_CONFLICTS"][0]["candidates"]) == 2


def test_G14_no_verified_rebar_without_an_established_occurrence():
    out = V3S.column_rebar(_column_ctx(None))
    assert _barsets(out) == []
    assert out[0]["terminal_state"] == "REBAR_BLOCKED_OCCURRENCE_NOT_ESTABLISHED"
    assert out[0]["audit"]["vertical_straight_kg"] > 0 and out[0]["audit"]["ties_straight_kg"] > 0
    est = V3S.column_rebar(_column_ctx(0.45, state="MEASURED"))
    assert {x["ref"].split()[-1] for x in _barsets(est)} == {"vertical", "ties"}
    d5 = _reg("STRUCTURAL_POPULATION_COVERAGE_V2")["d5_excluded_from_verified"]
    assert d5["occurrences"] == 26 and d5["audit_kg"] == pytest.approx(1739.7, abs=0.2)
    mig = {r["code"]: r for r in _migration() if r["code"].startswith("R-COLUMNS-")}
    drop = sum(r["old_qty"] - r["new_measured_qty"] for r in mig.values())
    assert drop == pytest.approx(d5["audit_kg"], abs=0.05)                  # exactly the D5 sets left the total
    assert {r["v2_release_state"] for r in mig.values()} == {R.LOWER_BOUND}


@pytest.mark.xfail(strict=True, reason="D6 ground-zone binding needs engineer answer Q-S4; unchanged this round")
def test_G15_ground_zone_not_bound_by_minimum_area():
    assert "min(hit, key=lambda p: p.area)" not in (LAB / "alsenan_v3_structure.py").read_text()


def test_G16_ambiguous_wall_length_accounted_not_erased():
    w = _reg("WALL_LENGTH_CONSERVATION_V2")
    t = w["totals"]
    assert t["raw_ambiguous_m"] == t["accounted_ambiguous_m"] == 46.63 and t["unaccounted_ambiguous_m"] == 0.0
    for r in w["rows"]:
        if r["raw_ambiguous_m"] > 0:
            assert r["blockwork_release"] in (R.LOWER_BOUND, R.BLOCKED)
    bw = [r for r in _migration() if r["code"].startswith("B-") and "-UNR-" not in r["code"]]
    assert not [r for r in bw if r["v2_release_state"] == R.VERIFIED_COMPLETE and r["level"] in
                {x["floor"] if x["floor"] != "2F" else "2F_ROOF" for x in w["rows"] if x["raw_ambiguous_m"] > 0}]
    assert _reg("TERMINAL_OBJECT_LEDGER")["check"]["by_type"]["WALL_BAND"] == 137


def test_G17_unpaired_boundary_accounted():
    t = _reg("WALL_LENGTH_CONSERVATION_V2")["totals"]
    assert t["raw_unpaired_boundary_m"] == t["blocked_unpaired_m"] == 187.82
    assert t["unaccounted_unpaired_m"] == 0.0 and t["classified_unpaired_m"] >= t["raw_unpaired_boundary_m"]
    assert _reg("TERMINAL_OBJECT_LEDGER")["check"]["by_type"]["UNPAIRED_BOUNDARY"] == 772


def test_G18_opening_area_never_computed_with_blocked_height():
    e = OE.evaluate({"kind": "DOOR", "width_m": 0.9, "height_m": None, "height_class": None})
    assert e["height"]["state"] == "BLOCKED" and e["area"]["state"] == "BLOCKED"
    p = OE.evaluate({"kind": "DOOR", "width_m": 0.9, "height_m": 2.1, "height_class": "PROVISIONAL_GEOMETRIC"})
    assert p["area"]["state"] == "PROVISIONAL"
    g = OE.evaluate({"kind": "WINDOW", "width_m": 1.5, "height_m": 2.2, "height_class": "RASTER_DERIVED",
                     "sill_m": 0.05})
    assert "GLAZED_DOOR_CANDIDATE" in g["flags"] and g["function"]["state"] == "BLOCKED"
    reg = _reg("OPENING_EVIDENCE_REGISTER_V2")
    assert reg["v3a_computed_with_blocked_height"] == [] and len(reg["rows"]) == 60
    order = {"VERIFIED": 0, "PROVISIONAL": 1, "BLOCKED": 2}
    for r in reg["rows"]:
        assert order[r["area"]["state"]] >= max(order[r["width"]["state"]], order[r["height"]["state"]]), r["id"]
        assert r["v3a_attribute_states"]["area_state"] != "COMPUTED" or r["height"]["state"] == "VERIFIED"
    assert len(reg["glazed_door_candidates"]) == 24


def test_G19_duplicate_sb2_is_an_explicit_conflict():
    recs = [{"handle": "a", "BEAM": "SB2", "attributes": {"W": "100"}},
            {"handle": "b", "BEAM": "SB2", "attributes": {"W": "80"}},
            {"handle": "c", "BEAM": "SB1", "attributes": {"W": "60"}}]
    c = SG.key_conflicts(recs, "BEAM")
    assert len(c) == 1 and c[0]["key"] == "SB2" and c[0]["rows"] == ["a", "b"]
    d = _reg("STRUCTURAL_DEFINITION_REGISTER_V2")
    conf = [x for x in d["conflicts"] if x["key"] == "SB2"]
    assert len(conf) == 1 and sorted(v["W"] for v in conf[0]["variants"]) == ["100", "80"]
    sb2 = [x for x in d["definitions"] if x["type"] == "SB2"]
    assert len(sb2) == 2 and {x["interpretation_state"] for x in sb2} == {"CONFLICT"}     # neither row chosen


def test_G20_boxed_captured_and_accounted():
    rows = [r for r in _reg("STRUCTURAL_SOURCE_COVERAGE_V2")["rows"]
            if r.get("block") == "FT" and "BOXED" in r.get("fields_blocked_semantics", [])]
    assert sorted(r["row_ids"][0] for r in rows) == sorted(
        ["F", "F2", "F3", "F4", "F5", "F6", "F7", "F9", "F10", "F11", "F15"])
    assert all(r["coverage_state"] == "CONSUMED_PARTIAL" and r["interpretation_state"] == "PARTIALLY_INTERPRETED"
               for r in rows)
    defs = {(x["block"], x["type"]): x for x in _reg("STRUCTURAL_DEFINITION_REGISTER_V2")["definitions"]}
    assert all("BOXED" in json.dumps(defs[("FT", t)], ensure_ascii=False) for t in ("F2", "F10"))


def test_G21_side_bar_remarks_accounted():
    rows = [r for r in _reg("STRUCTURAL_SOURCE_COVERAGE_V2")["rows"] if r.get("population") == "BEAM_SIDE_BARS"]
    assert len(rows) == 23
    assert all(r["interpretation_state"] == "TOKENS_PARSED_SEMANTICS_CANDIDATE" and
               r["consumer_state"] == "PENDING_REBAR_CONSUMER_V2" for r in rows)
    bar = SG.parse_bar("2%%C12/30cm")
    assert bar["grammar"] == "COUNT_DIA_AT_SPACING" and bar["count"] == 2 and bar["dia_mm"] == 12


def test_G22_user_cli_legacy_adapter_guarded():
    reg = _reg("LEGACY_CAD_MIGRATION_REGISTER")
    assert reg["user_cli_total"] == reg["user_cli_guarded"] == 17
    clis = [r["entry_point"] for r in reg["rows"] if r["kind"] == "USER_CLI"]
    for c in clis:
        assert "require_legacy_opt_in(" in (ROOT / c).read_text(), c
    env = {k: v for k, v in os.environ.items() if k != "URBAN_ALLOW_LEGACY_CAD_ADAPTER"}
    env["PYTHONPATH"] = str(ROOT)
    p = subprocess.run([sys.executable, str(ROOT / "tools" / "run_cad_pipeline.py")], cwd=ROOT, env=env,
                       capture_output=True, text=True, timeout=120)
    assert p.returncode == 2 and "allow-legacy-cad-adapter" in (p.stderr + p.stdout)


@pytest.mark.xfail(strict=True, reason="SD-17 page-16 stair layout is vector glyphs; applicability unproved")
def test_G23_stair_rebar_bound_to_typical_layout():
    assert _reg("STRUCTURAL_POPULATION_COVERAGE_V2")["by_population"]["POPULATION:STAIRS"] != {"BLOCKED": 1}


# =============================================================================================== terminal records
def test_terminal_records_footing_blocked_concrete():
    d = {"bars": {"long_bars": [{"count": 6, "dia_mm": 12, "per_m": False}]}, "boxed": None}
    out = V3S.footing_rebar(_footing_ctx(d, status="BLOCKED"))
    assert len(out) == 1 and out[0]["terminal_state"] == "REBAR_BLOCKED_CONCRETE_NOT_ESTABLISHED"
    out = V3S.footing_rebar(_footing_ctx(PER_M_DEF))
    st = [x.get("terminal_state") for x in out]
    assert st.count("REBAR_BLOCKED_PER_METRE_PENDING_CONSUMER_V2") == 3 and _barsets(out) == []


def test_terminal_records_beams():
    out = V3S.beam_rebar(_beam_ctx([BEAM_DEF], [_occ("CB1"), _occ("B9"), _occ("B1", state="NOT_MEASURED"),
                                                _occ("B1", Ls=None)]))
    assert [x["terminal_state"] for x in out] == [
        "REBAR_BLOCKED_PENDING_REBAR_CONSUMER_V2", "REBAR_BLOCKED_NO_DEFINITION",
        "REBAR_BLOCKED_OCCURRENCE_NOT_MEASURED", "REBAR_BLOCKED_LENGTH_MISSING"]
    led = _reg("TERMINAL_OBJECT_LEDGER")["check"]["by_terminal_state"]
    assert led["REBAR_BLOCKED_PENDING_REBAR_CONSUMER_V2"] == 11 and led["REBAR_BLOCKED_LENGTH_MISSING"] == 8


def test_terminal_records_straps():
    ctx = {"a3": {"straps": {"rows": [{"type": "SB1", "mark_key": "X|H1|", "status": "COMPUTED"},
                                      {"type": "SB2", "mark_key": "X|H2|", "status": "BLOCKED"}]}}}
    out = V3S.strap_rebar(ctx)
    assert [x["terminal_state"] for x in out] == ["REBAR_BLOCKED_NO_CONSUMER"] * 2
    assert _reg("TERMINAL_OBJECT_LEDGER")["check"]["by_type"]["STRAP_BEAM"] == 3


def test_mutation_room_status_reaches_lines():
    """Metamorphic: every room status mutation must reach the floor / skirting / ceiling line status."""
    rng = random.Random(1)
    statuses = ["COMPUTED", "COMPUTED_REVIEW", "BLOCKED"]
    rows = [_finish_row(f"R{i}", rng.choice(statuses)) for i in range(30)]
    want = [V3R.ROOM_STATUS_CAP[r["status"]] or "COMPUTED" for r in rows]
    for fn, pre in ((V3R.flooring, "F-FL-"), (V3R.flooring, "F-SK-"), (V3R.ceilings, "CE-R")):
        got = [x["status"] for x in fn(_L(rows)) if x["code"].startswith(pre)]
        assert got == want, pre
    for r in rows:
        r["status"] = "BLOCKED"
    assert {x["status"] for x in V3R.flooring(_L(rows)) if x["code"].startswith("F-FL-")} == {"BLOCKED"}


# =============================================================================================== integrity, firewall
def test_register_index_hashes_hold():
    idx = json.loads((REGS / "INDEX.json").read_text())
    assert idx["built_twice_identical"] is True and idx["v3b_rebuilt_qa"] == "PASS"
    for name, h in idx["registers"].items():
        assert hashlib.sha256((REGS / f"{name}.json").read_bytes()).hexdigest() == h, name
    frozen = ROOT / "tests/alsenan/registers_v3b/BOQ_LINES_V3B.json"
    assert hashlib.sha256(frozen.read_bytes()).hexdigest() == idx["frozen_v3b_lines_sha256"]


def test_gate_register_matches_static_definition():
    g = _reg("GATE_TRANSITION_REGISTER")
    assert json.loads(json.dumps(STATIC.gates(), ensure_ascii=False)) == g
    names = {r["proving_test"].split("::")[-1] for r in g["rows"]}
    here = Path(__file__).read_text()
    assert all(f"def {n}(" in here for n in names)
    xfail = {r["gate"] for r in g["rows"] if r["final_state"].startswith("XFAIL")}
    assert xfail == {"G11", "G13", "G15", "G23"}          # frozen round-2 record
    r3 = json.loads((ROOT / "research/alsenan_rebar_truth_03/registers/REBAR_GATE_TRANSITIONS.json").read_text())
    r3x = {r["gate"] for r in r3["rows"] if r["final_state"] == "XFAIL"}
    assert r3x == {"G15", "G23"}                          # round 3 promoted G11 / G13 with their consumers


@pytest.mark.parametrize("path", ["research/external_engine_lab/alsenan_control_v2.py",
                                  "research/external_engine_lab/alsenan_structural_source_v2.py",
                                  "research/alsenan_control_plane_02/build_control_v2.py",
                                  "research/alsenan_control_plane_02/static_registers.py"])
def test_benchmark_firewall(path):
    src = (ROOT / path).read_text()
    for banned in ("registers_v3b_eval", "BENCHMARK_EVALUATION", "registers_b1", "benchmark_qty",
                   "alsenan_v3b_evaluation", ".xlsx"):
        assert banned not in src, (path, banned)


def test_post_freeze_comparison_ran_after_the_freeze():
    out = json.loads((CP2 / "POST_FREEZE_BENCHMARK_COMPARISON.json").read_text())
    assert out["frozen_index_sha256"] == hashlib.sha256((REGS / "INDEX.json").read_bytes()).hexdigest()
    assert all(r["use"] == "FINDING_ONLY" and r["line_selection_identical_to_v3b_eval"] for r in out["rows"])


# =============================================================================================== no gaming
def test_no_gaming_raw_counts_preserved():
    w = _reg("WALL_LENGTH_CONSERVATION_V2")["totals"]
    assert w["raw_ambiguous_m"] == 46.63 and w["raw_unpaired_boundary_m"] == 187.82
    assert len(_reg("WET_LABEL_ACCOUNTING_REGISTER")["rows"]) == 35
    assert _reg("STRUCTURAL_POPULATION_COVERAGE_V2")["d5_excluded_from_verified"]["occurrences"] == 26
    led = _reg("TERMINAL_OBJECT_LEDGER")["check"]
    assert led["by_type"]["STRUCTURAL_SOURCE_OBJECT"] == 332 and led["by_type"]["WET_LABEL"] == 35


def test_no_gaming_geometry_identical_to_frozen_v3a():
    """Round 2 changes release, not measurement: every V3a quantity that existed is unchanged, except the column /
    footing rebar lines whose D5 / per-metre sets moved to explicit BLOCKED lines (reconciled exactly)."""
    ident = _reg("RELEASE_V2_MIGRATION_REGISTER")["v3a_measurement_identity"]
    changed = {r["code"] for r in ident["number_changed"]}
    assert changed <= {f"R-COLUMN-{lv}-{k}" for lv in ("GF", "1F", "2F_ROOF") for k in ("NET", "PROC", "STRAIGHT")} | {
        "R-FOOTING-GF-NET", "R-FOOTING-GF-PROC"}
    assert ident["counts"]["IDENTICAL"] == 254
    for r in ident["rows"]:
        if r["kind"] == "STATUS_ONLY":
            assert r["frozen_v3a_qty"] == r["rebuilt_v3a_qty"]


def test_no_gaming_lower_verified_is_reported_not_hidden():
    rows = _migration()
    changed = [r for r in rows if r["release_changed"]]
    assert changed and all(r["v2_release_reason"] for r in changed)
    c = _reg("RELEASE_V2_MIGRATION_REGISTER")["counts"]
    assert sum(c.values()) == len(rows) == 395
