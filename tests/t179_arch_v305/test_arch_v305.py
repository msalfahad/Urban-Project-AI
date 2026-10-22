"""T-179: ARCH_TAKEOFF_V3.0.5, the SAME opt-in candidate as V3.0 .. V3.0.4 extended (engine.source.arch_v305), and its
ledger typing (research/agents_t179/t179_ledgers.py), on synthetic data only (no client drawing).

VILLA K (not the development villa). Hand calculations, kg/m = d^2 / 162 (ø10: 0.617284 kg/m):

SLAB PANEL K-S1 (GF), bars 6ø10/m along x, clear span 4.00 m face to face, spread 3.00 m, one end on a continuous
beam (0.25 m wide), the other on an edge beam. Typical slab detail: 50 % of the bars stop 0.125 L = 0.50 m short of
the continuous support face (3.50 m); the other half runs on across the beam (crossing half, 0.25 m each).
    count A = ceil(6 x 3.00) = 18, B = A + 1 = 19
    A: 9 x 4.00 + 9 x 3.50 = 67.50 m x 0.617284 = 41.666667 kg; crossing 9 x 0.25 = 2.25 m = 1.388889 kg -> 43.055556
    B: 10 x 4.00 + 9 x 3.50 = 71.50 m          = 44.135802 kg; crossing 10 x 0.25 = 2.50 m = 1.543210 kg -> 45.679012
    -> HELD 43.055556 .. 45.679012 kg (never one value: the count reading is open for slabs)
    adverse (skewed panel): B 40.0 < A 41.0 -> HELD 40.0 .. 41.0 (min .. max, not A .. B)
    adverse (label without '/m'): '5 bars in all' 3.086420 kg (5 x 1.00 m) is the low end

DOME BAY K-D (1F), opening ring r_i 1.80, r_o 2.00 m, depth 0.50 m printed; framing faces W 2.00 (TANGENT to the
outer circle), E 1.90, S 2.50, N 2.50 (both outside the ring).
    seg(r, d) = r^2 acos(d / r) - d sqrt(r^2 - d^2); seg(2.00, 2.00) = 0 (tangent: no segment, not negative)
    seg(2.00, 1.90) = 4 acos(0.95) - 1.9 sqrt(0.39) = 1.270241 - 1.186549 = 0.083692 m2
    inner circle: every face beyond 1.80 -> no segment
    ring in bay = pi (2.00^2 - 1.80^2) - 0.083692 = 2.387610 - 0.083692 = 2.303918 m2 x 0.50 = 1.151959 m3
    route G measured the same ring as two arc bands (0.40 and 0.30 m3): both SUPERSEDED (one ring, measured once)
"""

from __future__ import annotations

import copy
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t179"))
sys.path.insert(0, str(ROOT / "research" / "agents_t160"))

from engine.source import arch_v30 as A30                     # noqa: E402
from engine.source import arch_v304 as A304                   # noqa: E402
from engine.source import arch_v305 as A305                   # noqa: E402
from engine.source import boq_line as BL                      # noqa: E402
from engine.source import provisional_estimate as PE          # noqa: E402
import t179_ledgers as L5                                     # noqa: E402

A = pytest.approx
PID = "synthetic-v305-villa-k"
KG10 = 100 / 162


def to_line(it):
    return BL.from_route_g(it, project_id=PID, revision_set_sha256="0" * 64, conventions_set="SV",
                           conventions_digest="d" * 16)


def route_item(iid, family, storey, q, trade="REINFORCEMENT"):
    return PE.item(item_id=iid, component_id=iid.split(":", 1)[1], trade=trade, family=family, storey=storey,
                   category="PROVISIONAL", low=q, base=q, high=q, dia_mm=10 if trade == "REINFORCEMENT" else None,
                   formula="convention", assumptions=["X"], support="CONVENTION_ONLY", confidence="MEDIUM",
                   blocker="NOT_REVIEWED", source="SV")


def base_lines():
    its = [route_item("P-S:SLABS:GF:S1:BOT:D10", "SLABS", "GF", 40.0),
           route_item("P-S:SLABS:GF:S2:TOP:D10", "SLABS", "GF", 12.0),
           route_item("P-S:SLABS:2F:S9:BOT:D10", "SLABS", "2F", 9.0),
           route_item("P-S:BEAMS:GF:BAND0001:BOT:D16", "BEAMS", "GF", 50.0),
           route_item("P-C:BEAMS:1F:BAND0040", "BEAMS", "1F", 0.40, trade="CONCRETE"),
           route_item("P-C:BEAMS:1F:BAND0041", "BEAMS", "1F", 0.30, trade="CONCRETE"),
           route_item("P-C:BEAMS:1F:BAND0007", "BEAMS", "1F", 1.20, trade="CONCRETE")]
    return [to_line(it) for it in its]


# ------------------------------------------------------------------------------------------------ hand fixtures
def panel_row(**kw):
    """one T-152-format ledger row for the synthetic panel K-S1 (numbers from the module docstring)."""
    a_len, b_len = 9 * 4.00 + 9 * 3.50, 10 * 4.00 + 9 * 3.50
    r = {"panel": "K-S1", "floor": "GF", "area_m2": "12.0", "t_m": "0.16", "direction": "x", "printed": "6ø10/m",
         "d_mm": "10", "layers": "1", "spread_m": "3.0", "bars_A": "18", "bars_B": "19", "ends_continuous": "9/18",
         "len_face_A_m": "72.0", "len_face_B_m": "76.0", "len_p15_A_m": str(a_len), "len_p15_B_m": str(b_len),
         "kg_A": str(round(a_len * KG10, 6)), "kg_B": str(round(b_len * KG10, 6)),
         "kg_cross_A": str(round(9 * 0.25 * KG10, 6)), "kg_cross_B": str(round(10 * 0.25 * KG10, 6)),
         "kg_face_uncurtailed_A": "44.444444", "kg_C_info": "44.444444", "dev_held_kg": "13.333..23.333",
         "top_held_kg": "5.000..12.000 (i 5.000..5.500, ii 10.000..11.000, p15 11.000..12.000; crossing 1.000..1.200)",
         "status": "MEASURED_NET_COUNT_HELD_Q71", "note": ""}
    r.update(kw)
    return r


def seg(r, d):
    return 0.0 if d >= r else r * r * math.acos(d / r) - d * math.sqrt(r * r - d * d)


def tangent_ring_m3():
    faces = {"W": 2.00, "E": 1.90, "S": 2.50, "N": 2.50}
    outer = math.pi * 2.0 ** 2 - sum(seg(2.0, d) for d in faces.values())
    inner = math.pi * 1.8 ** 2 - sum(seg(1.8, d) for d in faces.values())
    return (outer - inner) * 0.50, outer - inner


def src(task):
    return {"file": f"research/{task}.csv", "sha256": "e" * 64, "task": task, "merge_commit": "abc1234",
            "checker_run": f"verifier run for {task} (MERGED abc1234)"}


def inputs(slab_recs=None, ring_lines=None, ring_recs=None, stair_recs=None):
    m3, area = tangent_ring_m3()
    slab = slab_recs if slab_recs is not None else L5.slab_records([panel_row()], [])
    ring = ring_recs if ring_recs is not None else [
        {"element": "DOME-K:RING", "floor": "1F", "component": "RING BEAM IN BAY", "state": "RELEASED",
         "value": round(m3, 6), "verified_by": "checker re-measured (0.0 %)", "geometry_source": "CAD_VECTOR",
         "info": {"in_bay_m2": round(area, 6)}},
        {"element": "DOME-K2:RING", "floor": "1F", "component": "RING BEAM IN BAY", "state": "UNQUANTIFIED",
         "reasons": ["RING_SECTION_NOT_PRINTED"], "info": {"candidate_if_b4_m3": 1.0}}]
    led = [{"piece": "SLAB_STEEL", "item_code": "STR.REBAR", "unit": "kg", "source": src("T-S"),
            "scope": {"physical_element": "SLABS", "floors": ["GF"], "supersede": "ELEMENT_AND_FLOORS"},
            "records": slab},
           {"piece": "DOME_RING", "item_code": "STR.CONC.BEAM", "unit": "m3", "source": src("T-R"),
            "scope": {"physical_element": "BEAMS", "floors": ["1F"], "supersede": "NAMED_LINES",
                      "lines": ring_lines if ring_lines is not None else [
                          {"element_id": "P-C:BEAMS:1F:BAND0040", "floor": "1F", "why": "arc band of ring K-D"},
                          {"element_id": "P-C:BEAMS:1F:BAND0041", "floor": "1F", "why": "arc band of ring K-D"}]},
            "records": ring}]
    if stair_recs is not None:
        led.append({"piece": "STAIR_POOL_TANK_STEEL", "item_code": "STR.REBAR", "unit": "kg", "source": src("T-T"),
                    "scope": {"physical_element": "STAIRS", "floors": ["GROUND", "GF"],
                              "supersede": "ELEMENT_AND_FLOORS"}, "records": stair_recs})
    return {"schema": A305.INPUTS_SCHEMA, "project": PID, "ledgers": led}


def case(doc=None, earlier=()):
    base = base_lines()
    inp = A305.load_inputs(doc or inputs(), PID)
    ch, logs = A305.ledger_changes(inp, base, earlier)
    return base, inp, ch, logs


def added(ch):
    return {(c["after"]["calculation"]["inputs"]["element"], c["after"]["calculation"]["inputs"]["component"],
             c["after"]["calculation"]["inputs"].get("part")): c for c in ch if c["action"] == "ADD"}


# ------------------------------------------------------------------------------------------------ hand values
def test_tangent_ring_by_hand_and_by_the_t160_tool():
    m3, area = tangent_ring_m3()
    assert seg(2.0, 2.0) == 0.0                                     # tangent face: no segment, never negative
    assert seg(2.0, 1.9) == A(0.083692, abs=1e-6)
    assert area == A(2.303918, abs=1e-6) and m3 == A(1.151959, abs=1e-6)
    import dome_ring as DR                                          # the checker-merged T-160 tool, independent code
    faces = {k: {"d_m": d, "far_d_m": d + 0.25} for k, d in {"W": 2.00, "E": 1.90, "S": 2.50, "N": 2.50}.items()}
    out = DR.ring({"r_inner_m": 1.80, "r_outer_m": 2.00, "faces": faces, "columns_rel_m": [], "ring_depth_m": 0.50})
    got = out.get("ring_in_bay_m2", out.get("in_bay_m2"))
    assert got == A(2.303918, abs=1e-5)
    # mirrored bay (W <-> E) and a 90 degree rotation (W, E <-> S, N) give the same in-bay ring
    mir = {"W": faces["E"], "E": faces["W"], "S": faces["S"], "N": faces["N"]}
    rot = {"W": faces["S"], "E": faces["N"], "S": faces["W"], "N": faces["E"]}
    for f in (mir, rot):
        o = DR.ring({"r_inner_m": 1.80, "r_outer_m": 2.00, "faces": f, "columns_rel_m": [], "ring_depth_m": 0.50})
        assert o.get("ring_in_bay_m2", o.get("in_bay_m2")) == A(2.303918, abs=1e-5)


def test_slab_panel_typed_as_a_held_range_by_hand():
    recs = L5.slab_records([panel_row()], [])
    bot = next(r for r in recs if r["component"] == "BOTTOM MESH")
    assert bot["state"] == "HELD_RANGE"
    assert (bot["low"], bot["high"]) == (A(43.055556, abs=1e-5), A(45.679012, abs=1e-5))
    assert "T-171" in bot["reasons"][0] and "footings only" in bot["reasons"][0]
    top = next(r for r in recs if r["component"] == "TOP BARS OVER SUPPORTS")
    assert (top["low"], top["high"]) == (A(5.0), A(13.2))          # reading i .. p.15 12.0 + crossing 1.2
    dev = next(r for r in recs if r["component"] == "DEVELOPMENT / ANCHORAGE")
    assert (dev["low"], dev["high"]) == (A(13.333), A(23.333))


def test_adverse_skewed_panel_and_label_without_per_metre():
    recs = L5.slab_records([panel_row(kg_A="41.0", kg_B="40.0", kg_cross_A="0", kg_cross_B="0")], [])
    bot = next(r for r in recs if r["component"] == "BOTTOM MESH")
    assert (bot["low"], bot["high"]) == (A(40.0), A(41.0))
    lab = panel_row(status="HELD_LABEL", printed="5ø10",
                    note="vertical label prints no '/m': designer item; count reading 5 bars = 3.086420 kg")
    bot = next(r for r in L5.slab_records([lab], []) if r["component"] == "BOTTOM MESH")
    assert bot["low"] == A(3.086420) and bot["high"] == A(45.679012, abs=1e-5)
    with pytest.raises(ValueError):
        L5.slab_records([panel_row(status="SOMETHING_NEW")], [])   # an unmapped ledger state is refused


def test_panels_without_bars_are_unquantified_never_zero():
    recs = L5.slab_records([panel_row()], [{"id": "K-S2", "floor": "GF", "cls": "SLAB", "area": "0.4",
                                            "evidence": "corner outside a ring"},
                                           {"id": "K-B1", "floor": "GF", "cls": "BEAM", "area": "1", "evidence": ""}])
    nob = [r for r in recs if r["element"] == "SLAB:K-S2"]
    assert len(nob) == 1 and nob[0]["state"] == "UNQUANTIFIED" and "NO_BARS_PRINTED" in nob[0]["reasons"][0]
    assert not [r for r in recs if r["element"] == "SLAB:K-B1"]


def test_pool_rows_blocked_on_the_superseded_wall_height_and_strip_owned_once():
    rows = [{"element": "POOL R1 deep-end population", "part": "wall vertical, outer face", "mark": "7ø14/m (p.7)",
             "page": "", "d": "14", "direction": "", "n_A": "88", "n_B": "88", "n_C": "87.5", "length_m": "1.55",
             "m_A": "", "m_B": "", "m_C": "", "kg_A": "165.027", "kg_B": "165.027", "kg_C": "164.06",
             "status": "HELD_DESIGNER (R1 deep-end population)", "dev_held_kg": "59.62..104.34", "note": "x"},
            {"element": "GF-STRIP (MS1-T turn + well + MS1-LD)", "part": "landing strip bottom bars across the stair",
             "mark": "8ø16/m", "page": "", "d": "16", "direction": "", "n_A": "10", "n_B": "11", "n_C": "9.6",
             "length_m": "2.5", "m_A": "", "m_B": "", "m_C": "", "kg_A": "39.506", "kg_B": "43.457", "kg_C": "37.926",
             "status": "MEASURED_NET_COUNT_HELD_Q71", "dev_held_kg": "20.23..35.40", "note": ""}]
    recs = L5.stair_records(rows)
    pool = next(r for r in recs if r["element"] == "POOL:R1")
    assert pool["state"] == "UNQUANTIFIED" and pool["floor"] == "GROUND"
    assert any("1.20" in x and "T-183" in x for x in pool["reasons"])
    assert pool["info"]["A_kg"] == 165.027                         # kept as information, never as a quantity
    strip = [r for r in recs if r["element"] == "ST-01:GF-STRIP"]
    assert [r["state"] for r in strip] == ["HELD_RANGE", "HELD_RANGE"]   # bars + development, one line each
    assert (strip[0]["low"], strip[0]["high"]) == (39.506, 43.457)
    assert "owned once" in strip[0]["info"]["register"]


# ------------------------------------------------------------------------------------------------ integration
def test_route_slab_lines_superseded_and_ledger_lines_added():
    base, inp, ch, logs = case()
    sup = [c for c in ch if c["action"] == "REPLACE" and c["piece"] == "SLAB_STEEL"]
    assert {c["before"]["location"]["element_id"] for c in sup} == {"P-S:SLABS:GF:S1:BOT:D10",
                                                                    "P-S:SLABS:GF:S2:TOP:D10"}
    for c in sup:
        assert c["after"]["evidence_state"] == "NOT_APPLICABLE_WITH_EVIDENCE" and c["after"]["measured_net"] is None
        assert "SUPERSEDED" in c["after"]["notes"]
    lg = {x["piece"]: x for x in logs}
    assert lg["SLAB_STEEL"]["route_value"] == A(52.0) and lg["SLAB_STEEL"]["route_lines"] == 2
    bot = added(ch)[("SLAB:K-S1", "BOTTOM MESH", "x")]
    a = bot["after"]
    assert a["evidence_state"] == "BOUNDED_EXPOSURE" and a["measured_net"] is None
    assert (a["bounded_range"]["low"], a["bounded_range"]["high"]) == (A(43.055556, abs=1e-5), A(45.679012, abs=1e-5))
    assert bot["evidence_status"] == "HELD"
    assert lg["STAIR_POOL_TANK_STEEL"]["state"] == "NO_PROJECT_INPUT"


def test_ring_supersedes_its_route_bands_once_and_is_verified():
    base, inp, ch, logs = case()
    sup = [c for c in ch if c["action"] == "REPLACE" and c["piece"] == "DOME_RING"]
    assert {c["before"]["location"]["element_id"] for c in sup} == {"P-C:BEAMS:1F:BAND0040", "P-C:BEAMS:1F:BAND0041"}
    lg = {x["piece"]: x for x in logs}["DOME_RING"]
    assert lg["route_value"] == A(0.70)
    rg = added(ch)[("DOME-K:RING", "RING BEAM IN BAY", None)]
    assert rg["after"]["evidence_state"] == "SOURCE_DERIVED" and rg["after"]["measured_net"] == A(1.151959, abs=1e-6)
    assert rg["after"]["item_code"] == "STR.CONC.BEAM" and rg["after"]["unit"] == "m3"
    assert rg["evidence_status"] == "VERIFIED"
    e = added(ch)[("DOME-K2:RING", "RING BEAM IN BAY", None)]
    assert e["after"]["evidence_state"] == "BLOCKED_RFI" and e["after"]["measured_net"] is None
    assert e["evidence_status"] == "UNKNOWN"
    l305, ident = A305.integrate(base, ch)
    t = A304.code_totals(l305)
    # the untouched 1F beam 1.20 + the ring 1.151959 (the two bands no longer count): one ring, measured once
    assert t["STR.CONC.BEAM|m3"]["released"] == A(1.20 + 1.151959, abs=1e-6)
    assert t["STR.CONC.BEAM|m3"]["blocked_lines"] == 1


def test_every_other_line_byte_identical_and_diff():
    base, inp, ch, logs = case()
    l305, ident = A305.integrate(base, ch)
    by = {ln["line_id"]: ln for ln in base}
    out = {"P-S:SLABS:2F:S9:BOT:D10", "P-S:BEAMS:GF:BAND0001:BOT:D16", "P-C:BEAMS:1F:BAND0007"}
    same = [ln for ln in l305 if ln["location"]["element_id"] in out]
    assert len(same) == 3 and all(A30.line_sha(ln) == A30.line_sha(by[ln["line_id"]]) for ln in same)
    assert ident["replaced"] == 4 and ident["outside_rows_identical_to_v3_0_4"] == 3
    d = A305.diff_rows(base, l305)
    c = {}
    for x in d:
        c[x["vs_v3_0_4"]] = c.get(x["vs_v3_0_4"], 0) + 1
    assert c == {"SAME": 3, "CHANGED": 4, "ADDED": len([x for x in ch if x["action"] == "ADD"])}


def test_held_never_released_and_never_zero():
    base, inp, ch, logs = case()
    l305, _i = A305.integrate(base, ch)
    for ln in l305:
        if ln["evidence_state"] in ("BLOCKED_RFI", "BOUNDED_EXPOSURE"):
            assert ln["measured_net"] is None
    t = A304.code_totals(l305)["STR.REBAR|kg"]
    # the untouched beam line 50.0 + the 2F slab line outside the ledger's floors 9.0; GF slab steel is held now
    assert t["released"] == A(59.0)
    assert t["held_low"] > 0 and t["held_high"] >= t["held_low"]


# ------------------------------------------------------------------------------------------------ refusals
def test_named_route_line_missing_or_wrong_item_is_refused():
    with pytest.raises(A305.InputsError):
        case(inputs(ring_lines=[{"element_id": "P-C:BEAMS:1F:BAND9999", "floor": "1F", "why": "x"}]))
    with pytest.raises(A305.InputsError):        # the route line exists, but as steel: never superseded by concrete
        case(inputs(ring_lines=[{"element_id": "P-S:BEAMS:GF:BAND0001:BOT:D16", "floor": "GF", "why": "x"}]))


def test_record_outside_scope_missing_source_or_unexplained_hold_is_refused():
    doc = inputs()
    doc["ledgers"][0]["records"][0]["floor"] = "2F"
    with pytest.raises(A305.InputsError):
        A305.load_inputs(doc, PID)
    doc = inputs()
    del doc["ledgers"][1]["source"]["checker_run"]
    with pytest.raises(A305.InputsError):
        A305.load_inputs(doc, PID)
    doc = inputs()
    doc["ledgers"][1]["records"][1]["reasons"] = []
    with pytest.raises(A305.InputsError):
        A305.load_inputs(doc, PID)
    doc = inputs()
    doc["ledgers"][0]["records"][0].update(low=5.0, high=4.0)
    with pytest.raises(A305.InputsError):
        A305.load_inputs(doc, PID)
    with pytest.raises(A305.InputsError):
        A305.load_inputs(inputs(), "another project")


def test_a_line_an_earlier_version_changed_is_never_replaced():
    base = base_lines()
    s1 = next(ln for ln in base if ln["location"]["element_id"] == "P-S:SLABS:GF:S1:BOT:D10")
    with pytest.raises(ValueError):
        case(earlier={s1["line_id"]})


def test_two_ledgers_replacing_one_line_are_refused():
    doc = inputs(stair_recs=[{"element": "ST-K:F1", "floor": "GF", "component": "main", "state": "UNQUANTIFIED",
                              "reasons": ["x"]}])
    doc["ledgers"][2]["scope"] = {"physical_element": "SLABS", "floors": ["GF"], "supersede": "ELEMENT_AND_FLOORS"}
    with pytest.raises(ValueError):
        case(doc)


def test_no_inputs_changes_nothing():
    base = base_lines()
    ch, logs = A305.ledger_changes(None, base)
    assert ch == [] and {x["state"] for x in logs} == {"NO_PROJECT_INPUT"}
    l305, ident = A305.integrate(base, ch)
    assert [A30.line_sha(x) for x in l305] == [A30.line_sha(x) for x in base]


def test_write_files(tmp_path):
    base, inp, ch, logs = case()
    names, ident, led = A305.write(tmp_path, base, ch, logs, inp)
    assert set(names) == {"V3_0_5_BOQ_LINES.json", "V3_0_5_BOQ_LINES.csv", "V3_0_5_INTEGRATION_LEDGER.json",
                          "V3_0_5_INTEGRATION_LEDGER.csv", "V3_0_5_DIFF.csv", "V3_0_5_DOWNSTREAM.json",
                          "V3_0_5_RUN.json"}
    assert led["released_default"] is False and led["integration_package"] is True
    assert all(r["release_status"] == "NOT RELEASED" for r in led["rows"])


def test_cli_refuses_v305_inputs_without_the_method(tmp_path):
    from tools import urban_boq_m9 as M
    with pytest.raises(SystemExit):
        M.main(["arch", "--drawings", str(tmp_path / "x.dxf"), "--out", str(tmp_path), "--method",
                "ARCH_TAKEOFF_V3.0.4", "--v305-inputs", str(tmp_path / "y.json")])
    assert "ARCH_TAKEOFF_V3.0.5" in M.CANDIDATE_EXTENSIONS_V305
