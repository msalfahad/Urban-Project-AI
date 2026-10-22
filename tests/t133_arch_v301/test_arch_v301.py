"""T-133: ARCH_TAKEOFF_V3.0.1, the SAME opt-in candidate as V3.0 extended (engine.source.arch_v301), on synthetic
drawings only (no client drawing). Hand calculations:

ROUTE G SCOPE on SV-SCOPE (the T-126 synthetic villa, tests/t126_route_g_scope; storey heights GF 4.00 / 1F 3.50 /
2F 3.50, blinding 0.075 thick with a 0.15 projection; mm, mirrored, a quarter turn, metres):
  columns (m3)  K1 GF 0.25 x 0.30 x 4.00 = 0.300, K1 1F 0.20 x 0.30 x 3.50 = 0.210, K2 GF 0.300, K3 GF 0.25 x 0.60
                x 4.00 = 0.600, K5 GF 0.300: RELEASED, lines unchanged;
                K2 1F 0.210: the 1F roof-slab plan draws nothing at its position (nearest 6.00 m) -> NOT_PRESENT, the
                line becomes NOT_APPLICABLE_WITH_EVIDENCE (a column drawn only on the lower slab plan); its steel line
                (10.0 kg) is NOT changed (rebar outside the candidate) and is listed STALE downstream;
                K1 2F 0.210 and K2 2F 0.210 (no 2F plan), K3 1F 0.20 x 0.50 x 3.50 = 0.350 (two outlines), K4 GF 0.25 x
                0.50 x 4.00 = 0.500 (no anchor): HELD lines 0 .. route value, never 0;
                K5 1F (the route already counts nothing) and K6 GF (the route holds it): no line changes.
  blinding (m3) route lines 1.2810 (footing layer) + 0.3471 (ground-beam layer) ->
                footings released: (5.29 + 1.69 + 6.21 + 1.69 - 0.13) x 0.075 = 14.75 x 0.075 = 1.10625;
                ground beams HELD (Q-21 C): merged 3.60 x 0.075 = 0.270 .. own layer 4.32 x 0.075 = 0.324;
                footing in conflict FX/FY HELD (Q-31 C): 2.34 x 0.075 = 0.1755 .. 3.78 x 0.075 = 0.2835 (a footing
                held with its blinding);
                strap HELD (no section prints it): 1.05 x 0.075 = 0.07875 .. 0.07875.
                Four lines, never summed into one value: released 1.10625 + held 0.52425 .. 0.68625.

MEMBRANE AUDIT (T-124 fixture R, 10.00 x 6.00 less 7.50 x 3.15; roll 1.00 x 10.00): V5 A 5, B 6, C 6 by hand
(T-124 test): a line released at 5 rolls AGREES, a range 5 .. 6 AGREES, a line at 4 DIFFERS (count kept, flag held);
an area the run did not fold is NOT_AUDITED. Fixture X (11.00 x 5.50 less 1.00 x 3.00): V3 claims 8 (INVALID on
its own rolls), V5's own pieces make 8 real: a line at 8 AGREES and the INVALID V3 layout is listed.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests" / "t126_route_g_scope"))
sys.path.insert(0, str(ROOT / "tests" / "t131_arch_v30"))

from engine.source import arch_v30 as A30                     # noqa: E402
from engine.source import arch_v301 as A301                   # noqa: E402
from engine.source import boq_line as BL                      # noqa: E402
from engine.source import membrane_fold_v5 as F5              # noqa: E402
import test_route_g_scope as T126                             # noqa: E402

A = pytest.approx
PID = "synthetic-scope-villa"
ROOF_R = [(0, 0), (10, 0), (10, 6), (7.5, 6), (7.5, 2.85), (0, 2.85)]
ROOF_X = [(0, 0), (11, 0), (11, 5.5), (1, 5.5), (1, 2.5), (0, 2.5)]


def to_line(it):
    return BL.from_route_g(it, project_id=PID, revision_set_sha256="0" * 64, conventions_set="SV-SCOPE",
                           conventions_digest="d" * 16)


def scope_case(frame):
    R, K = T126.villa(T126.FRAMES[frame])
    base = [to_line(it) for it in R["items"]]
    ch, log = A301.scope_changes(R, base, to_line)
    return R, K, base, ch, log


def _el(K, key, st):
    return f"{K[key]['member_id']}|{st}"


def _by_elem(lines):
    return {ln["location"]["element_id"]: ln for ln in lines}


FRAMES = sorted(T126.FRAMES)


# ------------------------------------------------------------------------------------------------ route G scope
@pytest.mark.parametrize("frame", FRAMES)
def test_columns_by_hand(frame):
    R, K, base, ch, log = scope_case(frame)
    rep = {c["before"]["location"]["element_id"]: c for c in ch if c["action"] == "REPLACE"}
    # NOT_PRESENT: a column drawn only on the lower slab plan
    np_ = rep["P-C:" + _el(K, "K2", "1F")]["after"]
    assert np_["evidence_state"] == "NOT_APPLICABLE_WITH_EVIDENCE" and np_["measured_net"] is None
    assert "NOT_PRESENT" in np_["notes"] and "0.21" in np_["notes"]
    # HELD pieces: ranges 0 .. route value, never 0
    for key, st, v in (("K1", "2F", 0.210), ("K2", "2F", 0.210), ("K3", "1F", 0.350), ("K4", "GF", 0.500)):
        a = rep["P-C:" + _el(K, key, st)]["after"]
        assert a["evidence_state"] == "BOUNDED_EXPOSURE" and a["measured_net"] is None
        assert a["bounded_range"]["low"] == A(0.0) and a["bounded_range"]["high"] == A(v)
        assert a["location"]["element_id"] == "U-C:" + _el(K, key, st)
    # released, route-held and route-absent pieces: no change
    for key, st in (("K1", "GF"), ("K1", "1F"), ("K2", "GF"), ("K3", "GF"), ("K5", "GF")):
        assert "P-C:" + _el(K, key, st) not in rep
    assert "U-C:" + _el(K, "K6", "GF") not in rep
    # steel of the NOT_PRESENT piece: unchanged, listed STALE
    steel = "P-S:" + _el(K, "K2", "1F") + ":MAIN:D12"
    assert steel not in rep
    stale = [d for c in ch for d in c["downstream"] if "STALE" in str(d.get("v3_0_1"))]
    assert [d["line_id"] for d in stale] == [_by_elem(base)[steel]["line_id"]]
    assert all(c["after"]["measured_net"] != 0 for c in ch)


@pytest.mark.parametrize("frame", FRAMES)
def test_blinding_families_by_hand(frame):
    R, K, base, ch, log = scope_case(frame)
    bl = [c for c in ch if "BLINDING" in c["after"]["location"]["element_id"]]
    by = {c["after"]["location"]["element_id"]: c for c in bl}
    rel = by["P-C:PLAIN_CONCRETE:FOUNDATION:BLINDING_FOOTINGS_RELEASED"]
    assert rel["action"] == "REPLACE" and rel["before"]["measured_net"] == A(1.2810)
    assert rel["after"]["measured_net"] == A(1.10625)
    gb = by["U-C:PLAIN_CONCRETE:FOUNDATION:BLINDING_GROUND_BEAM"]
    assert gb["action"] == "REPLACE" and gb["before"]["measured_net"] == A(0.3471)
    assert (gb["after"]["bounded_range"]["low"], gb["after"]["bounded_range"]["high"]) == (A(0.270), A(0.324))
    fx = [c for k, c in by.items() if k.startswith("U-C:PLAIN_CONCRETE:FOUNDATION:BLINDING_FOOTING:")]
    assert len(fx) == 1 and fx[0]["action"] == "ADD"
    assert (fx[0]["after"]["bounded_range"]["low"], fx[0]["after"]["bounded_range"]["high"]) == (A(0.1755), A(0.2835))
    st = by["U-C:PLAIN_CONCRETE:FOUNDATION:BLINDING_STRAP"]
    assert st["action"] == "ADD" and st["after"]["bounded_range"]["low"] == A(0.07875) == st["after"]["bounded_range"]["high"]
    assert len(bl) == 4                                  # four lines, never one summed value
    lo = sum(c["after"]["bounded_range"]["low"] for c in bl if c["after"]["evidence_state"] == "BOUNDED_EXPOSURE")
    hi = sum(c["after"]["bounded_range"]["high"] for c in bl if c["after"]["evidence_state"] == "BOUNDED_EXPOSURE")
    assert (lo, hi) == (A(0.52425), A(0.68625))
    assert log["blinding"]["released_m3"] == A(1.10625)


def test_integrate_keeps_every_other_line_byte_identical_and_valid():
    R, K, base, ch, log = scope_case("mm")
    l30, l301, ident = A301.integrate(base, [], ch)
    assert [BL.validate(x) for x in l301]
    touched = {x["line_id"] for c in ch for x in (c["before"], c["after"]) if x is not None}
    by30 = {x["line_id"]: x for x in l30}
    for x in l301:
        if x["line_id"] not in touched:
            assert A30.line_sha(x) == A30.line_sha(by30[x["line_id"]])
    assert ident["outside_rows"] == len(l301) - sum(1 for x in l301 if x["line_id"] in touched)
    assert len(l301) == len(base) + 2                    # two blinding lines added, nothing deleted


def test_a_line_changed_by_v3_0_is_never_changed_again():
    R, K, base, ch, log = scope_case("mm")
    victim = ch[0]["before"]
    v30 = [A30._change("STRAPS", "REPLACE", victim, dict(copy.deepcopy(victim), notes="v3.0 piece"))]
    with pytest.raises(ValueError):
        A301.integrate(base, v30, ch)


def test_ledger_rows_name_the_verification_and_both_befores():
    R, K, base, ch, log = scope_case("mm")
    l30, l301, _ = A301.integrate(base, [], ch)
    rows = A301.ledger_rows(ch, l30)
    assert len(rows) == len(ch)
    for r in rows:
        assert r["verification"]["task"] == "T-126" and r["verification"]["merge_commit"] == "cd34bd0"
        assert r["rollback"].startswith("run the released ARCH_TAKEOFF_V2.9")
        assert r["owner_manual_method"] and r["drawing_method"]
    t = A301.family_totals(rows, "STR.CONC.COLUMN")
    assert t["before_v3_0"] == A(0.210 + 0.210 + 0.210 + 0.350 + 0.500)
    assert t["after_released"] == A(0.0) and t["after_held_high"] == A(0.210 + 0.210 + 0.350 + 0.500)
    assert t["after_not_present_or_superseded"] == 1


def test_no_route_g_result_changes_nothing():
    ch, log = A301.scope_changes(None, [], to_line)
    assert ch == [] and log["state"] == "NO_ROUTE_G_RESULT"


def test_inputs_not_mutated():
    R, K = T126.villa()
    base = [to_line(it) for it in R["items"]]
    snap = json.dumps(base, sort_keys=True, default=str), json.dumps(R["items"], sort_keys=True, default=str)
    A301.scope_changes(R, base, to_line)
    assert (json.dumps(base, sort_keys=True, default=str), json.dumps(R["items"], sort_keys=True, default=str)) == snap


# ------------------------------------------------------------------------------------------------ membrane audit
def roll_line(floor, room, *, value=None, low=None, high=None):
    ev = "SOURCE_DERIVED" if value is not None else "BOUNDED_EXPOSURE"
    return BL.make_line(project_id=PID, revision_set_sha256="0" * 64, item_code="FIN.WP.MEMBRANE_ROLLS", unit="pcs",
                        evidence_state=ev, measured_net=value, element_id="wp_rolls_to_buy", floor=floor,
                        room_id=room, bounded_range=None if value is not None else {"low": low, "high": high,
                                                                                     "basis": "Q-58"},
                        formula="rolls per area alone", rule_id="UP-WP-LAY-001", rule_version="1",
                        rfi=None if value is not None else {"question": "Q-58", "unlocks": room},
                        item_en="Waterproofing membrane rolls", item_ar="لفات العازل", trade="WATERPROOFING")


def area(floor, room, poly, unit_m=1.0):
    return {"floor": floor, "room_id": room, "polygon": poly, "holes": (), "unit_m": unit_m, "name": None,
            "spec": None}


def test_membrane_audit_fixture_r_by_hand():
    lines = [roll_line("2F", "R1", value=5), roll_line("2F", "R2", low=5, high=6), roll_line("2F", "R3", value=4),
             roll_line("1F", "NOPE", value=3)]
    areas = [area("2F", "R1", ROOF_R), area("2F", "R2", ROOF_R), area("2F", "R3", ROOF_R)]
    ch, log = A301.membrane_changes(areas, lines)
    ag = {x["room_id"]: x["agreement"] for x in log["lines"]}
    assert ag == {"R1": "AGREES", "R2": "AGREES", "R3": "DIFFERS", "NOPE": "NOT_COMPARABLE"}
    by = {c["before"]["location"]["room_id"]: c for c in ch}
    au = by["R1"]["after"]["calculation"]["inputs"]["v3_0_1_membrane_audit"]
    assert au["v5_by_reading"] == {"Q58_A": 5, "Q58_B": 6, "Q58_C": 6} and au["v5_state"] == "HELD_Q58"
    assert au["v5_ledger"]["installed_m2"] == A(42.935)
    for c in ch:                                          # counts never change
        assert c["after"]["measured_net"] == c["before"]["measured_net"]
        assert c["after"]["bounded_range"] == c["before"]["bounded_range"]
        assert c["after"]["evidence_state"] == c["before"]["evidence_state"]
    assert by["R3"]["held"] and not by["R1"]["held"]
    assert by["NOPE"]["after"]["calculation"]["inputs"]["v3_0_1_membrane_audit"]["state"] == "NOT_AUDITED"


@pytest.mark.parametrize("variant", [{}, {"mirror": True}, {"deg": 90.0}, {"scale": 1000.0}])
def test_membrane_audit_rotation_mirror_units(variant):
    sys.path.insert(0, str(ROOT / "tests" / "t124_membrane_offcut_once"))
    import test_membrane_offcut_once as T124
    unit = 0.001 if variant.get("scale") else 1.0
    au = A301.audit_area(area("2F", "R", T124._xf(ROOF_R, **variant), unit))
    assert au["v5_by_reading"] == {"Q58_A": 5, "Q58_B": 6, "Q58_C": 6}


def test_membrane_audit_fixture_x_invalid_v3_listed_v5_real():
    au = A301.audit_area(area("2F", "X", ROOF_X))
    assert au["v5_by_reading"]["Q58_A"] == 8
    assert any(x["verdict"] == F5.INVALID and x["claimed_q58_a"] == 8 for x in au["v3_layouts"])
    assert A301.agreement(roll_line("2F", "X", value=8), au) == "AGREES"


def test_roof_line_id_matches_the_area_by_its_text_id():
    a = area("2F", "ROOFX:T77", ROOF_R)
    assert A301._area_for(roll_line("2F", "2F-ROOF-T77", value=5), [a]) is a
    assert A301._area_for(roll_line("1F", "1F-ROOF-T77", value=5), [a]) is None
    two = [a, area("2F", "OTHER:T77", ROOF_X)]
    assert A301._area_for(roll_line("2F", "2F-ROOF-T77", value=5), two) is None   # ambiguous: not audited


def test_capture_returns_results_unchanged():
    from engine.source import membrane_fold_v3 as F3
    ref = F3.area(floor="GF", room_id="WC", polygon=[(0, 0), (2, 0), (2, 1.5), (0, 1.5)])
    with A301.capture() as cap:
        got = F3.area(floor="GF", room_id="WC", polygon=[(0, 0), (2, 0), (2, 1.5), (0, 1.5)])
    assert json.dumps(got, sort_keys=True, default=str) == json.dumps(ref, sort_keys=True, default=str)
    assert len(cap) == 1 and cap[0]["room_id"] == "WC"
    assert F3.area is not None and F3.area.__name__ == "area" and F3.area.__module__ == F3.__name__


# ------------------------------------------------------------------------------------------------ end to end
def test_end_to_end_v3_0_files_unchanged_and_v3_0_1_beside_them(tmp_path):
    import test_arch_v30 as T131
    dxf = T131._passage_villa(tmp_path / "p.dxf")
    dec = T131._decisions(tmp_path / "d.json")
    a = T131._run(dxf, tmp_path / "v30", "ARCH_TAKEOFF_V3.0", "--v30-decisions", str(dec))
    b = T131._run(dxf, tmp_path / "v301", "ARCH_TAKEOFF_V3.0.1", "--v30-decisions", str(dec))
    for name in ("V3_0_BOQ_LINES.json", "V3_0_INTEGRATION_LEDGER.json", "BOQ_LINES.json"):
        assert (a / name).read_bytes() == (b / name).read_bytes()
    l30, l301 = T131._lines(b / "V3_0_BOQ_LINES.json"), T131._lines(b / "V3_0_1_BOQ_LINES.json")
    run = json.loads((b / "V3_0_1_RUN.json").read_text(encoding="utf-8"))
    assert run["released_default"] is False and run["extends"] == "ARCH_TAKEOFF_V3.0"
    assert run["piece_logs"][0]["state"] == "NO_ROUTE_G_RESULT"
    rows = run["identity"]["v3_0_1_rows"]
    assert len(l301) == len(l30) and run["identity"]["outside_rows"] == len(l30) - rows
    led = json.loads((b / "V3_0_1_INTEGRATION_LEDGER.json").read_text(encoding="utf-8"))
    assert {r["version"] for r in led["rows"]} <= {"ARCH_TAKEOFF_V3.0", "ARCH_TAKEOFF_V3.0.1"}
    for x, y in zip(l30, l301):                          # roll lines: same counts; every other line identical
        if x["item_code"] in A30.MEMBRANE_ITEMS:
            assert (x["measured_net"], x["bounded_range"]) == (y["measured_net"], y["bounded_range"])
        else:
            assert A30.line_sha(x) == A30.line_sha(y)


def test_the_v3_0_method_list_is_untouched():
    from tools import urban_boq_m9 as M9
    assert M9.CANDIDATE_METHODS == ("ARCH_TAKEOFF_V3.0",) and M9.V301 not in M9.ARCH_METHODS
    assert M9.CANDIDATE_EXTENSIONS == ("ARCH_TAKEOFF_V3.0.1",)


def test_no_project_constants_in_the_module():
    src = (ROOT / "engine/source/arch_v301.py").read_text(encoding="utf-8")
    for word in ("Alsenan", "ST7757", "P7757", "S-OPENING", "ROOF SLAB"):
        assert word not in src


def test_end_to_end_synthetic_villa_every_roll_line_audited(tmp_path):
    """tools/arch_synth.villa (synthetic, wet rooms): every roll line of the run carries the V5 audit of the very
    area the run folded (captured), and its count is unchanged."""
    import test_arch_v30 as T131
    from tools import arch_synth as AS
    AS.villa(tmp_path / "villa.dxf")
    b = T131._run(tmp_path / "villa.dxf", tmp_path / "v301", "ARCH_TAKEOFF_V3.0.1")
    l30, l301 = T131._lines(b / "V3_0_BOQ_LINES.json"), T131._lines(b / "V3_0_1_BOQ_LINES.json")
    rolls = [y for y in l301 if y["item_code"] in A30.MEMBRANE_ITEMS]
    assert rolls
    by30 = {x["line_id"]: x for x in l30}
    audited = []
    for y in rolls:
        au = y["calculation"]["inputs"]["v3_0_1_membrane_audit"]
        x = by30[y["line_id"]]
        assert (x["measured_net"], x["bounded_range"], x["evidence_state"]) == (
            y["measured_net"], y["bounded_range"], y["evidence_state"])
        if y["measured_net"] is None and not (y.get("bounded_range") or {}).get("high"):
            assert au["state"] == "NOT_AUDITED" and au["why"].startswith("HELD_LINE_NO_AREA_FOLDED")
            continue
        audited.append(y)
        assert au["state"] == "AUDITED" and au["agreement"] == "AGREES", (y["location"], au)
    assert audited                                       # at least one released / ranged count audited end to end
