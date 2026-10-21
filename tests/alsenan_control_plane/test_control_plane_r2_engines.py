"""Control-plane round 2 - generic engines (synthetic, no project data): release model V2, trade dependency matrix,
terminal ledger, opening evidence, calibration V2, schedule grammar and the legacy CAD guard."""

from __future__ import annotations

import math
import random

import pytest

from engine import legacy_cad_guard as LG
from engine.source import calibration_v2 as CAL
from engine.source import opening_evidence as OE
from engine.source import release_model_v2 as R
from engine.source import schedule_grammar as SG
from engine.source import terminal_ledger as TL
from engine.source import trade_dependency as TD

OK = {"geometry": (R.HIGH, "g"), "upstream_status": (R.HIGH, "u")}


# ------------------------------------------------------------------ release model V2
def test_partial_is_a_lower_bound_and_never_procurement_eligible_by_default():
    v = R.release_v2(technical_class="PARTIAL", measured_qty=12.0, components=OK)
    assert v["release_state"] == R.LOWER_BOUND and v["qty_lower_bound"] == 12.0 and v["qty_verified"] is None
    assert v["procurement_eligible_v2"] is False and v["display"].startswith(">= 12.0")


def test_owner_approval_is_the_only_override_for_a_lower_bound():
    v = R.release_v2(technical_class="PARTIAL", measured_qty=12.0, components=OK, owner_approved_procurement=True)
    assert v["procurement_eligible_v2"] is True and v["release_state"] == R.LOWER_BOUND


def test_review_upstream_caps_a_measured_quantity_at_provisional():
    v = R.release_v2(technical_class="DERIVED", measured_qty=155.655, components=OK, upstream_status="COMPUTED_REVIEW")
    assert v["release_state"] == R.PROVISIONAL and v["qty_provisional"] == 155.655
    assert not v["procurement_eligible_v2"] and "capped by upstream" in v["release_reason"]


def test_a_blocked_dependency_blocks_and_keeps_the_number_only_in_audit():
    comps = dict(OK, semantic_identity=(R.GRADE_BLOCKED, "BLOCKED_SEMANTIC_TRADE_BOUNDARY"))
    v = R.release_v2(technical_class="DERIVED", measured_qty=24.94, components=comps)
    assert v["release_state"] == R.BLOCKED and v["qty_audit"] == 24.94
    assert v["qty_verified"] is None and v["weakest_dependency"] == "semantic_identity"


def test_confidence_is_derived_never_defaulted_high():
    v = R.release_v2(technical_class="DERIVED", measured_qty=1.0, components=None)
    assert v["release_state"] == R.BLOCKED and v["evidence_grade"] == R.GRADE_BLOCKED
    e = R.evidence({"geometry": (R.HIGH, "g"), "height": (R.LOW, "scaled"), "x": (R.NA, "n/a")})
    assert e["evidence_grade"] == R.LOW and e["weakest_dependency"] == "height" and len(e["confidence_reasons"]) == 1


def test_urban_rule_fixing_the_quantity_is_provisional_but_a_specification_rule_is_not():
    comps = dict(OK, rule_authority=(R.MEDIUM, "Urban rule"))
    q = R.release_v2(technical_class="URBAN_STANDARD", measured_qty=5.0, components=comps)
    s = R.release_v2(technical_class="URBAN_STANDARD", measured_qty=5.0, components=comps,
                     quantity_rule_dependency=False)
    assert q["release_state"] == R.PROVISIONAL
    assert s["release_state"] == R.VERIFIED_COMPLETE and s["specification_authority"]["grade"] == R.MEDIUM


def test_population_incomplete_demotes_verified_to_lower_bound():
    v = R.release_v2(technical_class="DERIVED", measured_qty=10.0, components=OK, population_complete=False)
    assert v["release_state"] == R.LOWER_BOUND


def test_budget_provisional_and_not_in_scope():
    b = R.release_v2(technical_class="BLOCKED", measured_qty=None, components=OK,
                     commercial={"class": "BUDGET_ESTIMATE", "qty": 3.0})
    p = R.release_v2(technical_class="BLOCKED", measured_qty=None, components=OK,
                     commercial={"class": "PROVISIONAL_SOURCE_DERIVED", "qty": 4.0})
    n = R.release_v2(technical_class="DERIVED", measured_qty=4.0, components=OK, not_in_scope=True)
    assert (b["release_state"], b["qty_budget"], b["procurement_eligible_v2"]) == (R.BUDGET, 3.0, False)
    assert (p["release_state"], p["qty_provisional"]) == (R.PROVISIONAL, 4.0)
    assert n["release_state"] == R.NOT_IN_SCOPE and not n["procurement_eligible_v2"]


def test_migration_row_flags_every_v1_to_v2_change():
    v1 = {"technical": {"class": "PARTIAL", "in_total": True},
          "commercial": {"class": "PARTIAL", "procurement_eligible": True, "confidence": "H"}}
    v2 = R.release_v2(technical_class="PARTIAL", measured_qty=1.0, components=OK, v1=v1)
    m = R.migration_row("X", v1, v2)
    assert m["status_changed"] and m["v1_procurement_eligible"] and not m["v2_procurement_eligible"]
    assert v2["procurement_eligible_v1"] is True and v2["confidence_v1"] == "H"


def test_property_v2_never_more_certain_than_its_upstream():
    rng = random.Random(7)
    for _ in range(300):
        cls = rng.choice(R.V1_TECH_MEASURED + R.V1_TECH_RULE + ("PARTIAL",) + R.V1_TECH_OUT)
        up = rng.choice(["COMPUTED", "COMPUTED_REVIEW", "BLOCKED", "UNKNOWN", "PARTIAL"])
        v = R.release_v2(technical_class=cls, measured_qty=rng.choice([None, 3.0]), components=OK,
                         upstream_status=up, population_complete=rng.choice([True, False]))
        if v["release_state"] != R.NOT_IN_SCOPE:
            assert R.ORDER[v["release_state"]] >= R.ORDER[R.upstream_cap(up)]
        assert v["procurement_eligible_v2"] == (v["release_state"] == R.VERIFIED_COMPLETE)


# ------------------------------------------------------------------ trade dependency matrix
def _space(classes, sem="MULTI_UNRESOLVED", up="COMPUTED", void=False):
    return {"upstream_status": up, "semantic_state": sem, "zone_classes": classes, "void_split_resolved": void}


def test_dry_wet_external_zone_blocks_split_dependent_trades_only():
    sp = _space(["DRY", "WET", "SERVICE", "EXTERNAL"])
    for t in ("FLOOR_FINISH", "SKIRTING", "CEILING", "PLASTER", "PAINT", "WALL_TILE", "WATERPROOFING"):
        assert TD.BLOCKED_SPLIT in TD.evaluate(t, sp)["blocking"], t
    assert not TD.evaluate("THRESHOLD", sp)["blocking"]


def test_dry_and_wet_indoor_zone_keeps_ceiling_and_plaster_but_blocks_floor_paint_tile():
    sp = _space(["DRY", "WET"])
    assert TD.evaluate("FLOOR_FINISH", sp)["blocking"] and TD.evaluate("PAINT", sp)["blocking"]
    assert TD.evaluate("WALL_TILE", sp)["blocking"] and TD.evaluate("SKIRTING", sp)["blocking"]
    assert not TD.evaluate("CEILING", sp)["blocking"] and not TD.evaluate("PLASTER", sp)["blocking"]


def test_an_established_void_outline_resolves_the_void_split():
    assert TD.evaluate("FLOOR_FINISH", _space(["DRY", "VOID"]))["blocking"]
    assert not TD.evaluate("FLOOR_FINISH", _space(["DRY", "VOID"], void=True))["blocking"]


def test_single_zone_and_unlabelled_spaces():
    single = TD.evaluate("FLOOR_FINISH", _space(["DRY"], sem="SINGLE"))
    unl = TD.evaluate("FLOOR_FINISH", _space(["UNKNOWN"], sem="UNLABELLED"))
    assert not single["blocking"] and single["components"]["semantic_identity"][0] == R.HIGH
    assert unl["components"]["semantic_identity"][0] == R.MEDIUM
    assert not TD.evaluate("WALL_TILE", _space(["DRY"], sem="SINGLE"))["applicable"]


# ------------------------------------------------------------------ terminal ledger
def test_ledger_conservation_and_failure_modes():
    led = TL.Ledger()
    for i in range(3):
        led.admit(f"o{i}", "T", f"s{i}")
    led.terminate("o0", "BLOCKED_X", "NONE")
    led.terminate("o1", "VERIFIED_COMPLETE", "QTY")
    c = led.check()
    assert not c["conserved"] and c["unterminated"] == ["o2"]
    led.terminate("o2", "AMBIGUOUS_BLOCKED", "NONE")
    led.terminate("o2", "AGAIN", "NONE")
    led.terminate("ghost", "X", "NONE")
    c = led.check()
    assert not c["conserved"] and c["double_terminations"] == ["o2"] and c["unknown_terminations"] == ["ghost"]
    with pytest.raises(ValueError):
        led.admit("o0", "T")


def test_unknown_is_allowed_unaccounted_is_not():
    led = TL.Ledger()
    led.admit("a", "WALL", None)
    led.terminate("a", "AMBIGUOUS_BLOCKED", "BLOCKED")
    assert led.check()["conserved"]


# ------------------------------------------------------------------ opening evidence
def test_area_never_more_certain_than_height_and_no_default_height():
    o = OE.evaluate({"kind": "WINDOW", "width_m": 1.2, "height_m": None, "height_class": None, "sill_m": 0.9})
    assert (o["count"]["state"], o["width"]["state"], o["height"]["state"], o["area"]["state"]) == (
        "VERIFIED", "VERIFIED", "BLOCKED", "BLOCKED")
    p = OE.evaluate({"kind": "DOOR", "width_m": 0.9, "height_m": 2.1, "height_class": "PROVISIONAL_GEOMETRIC_INFERENCE"})
    assert p["area"]["state"] == "PROVISIONAL"


def test_glazed_door_candidate_function_stays_unresolved():
    o = OE.evaluate({"kind": "WINDOW", "width_m": 1.95, "height_m": 2.06, "height_class": "RASTER_DERIVED",
                     "sill_m": 0.0})
    assert "GLAZED_DOOR_CANDIDATE" in o["flags"] and o["function"]["state"] == "BLOCKED"
    assert o["area"]["state"] == "VERIFIED"


def test_count_verified_even_when_width_is_blocked():
    o = OE.evaluate({"kind": "DOOR", "width_m": None})
    assert o["count"]["state"] == "VERIFIED" and o["area"]["state"] == "BLOCKED"


# ------------------------------------------------------------------ calibration V2
def _anchors(sx, sy, rot=0.0, sh=0.0, n=5):
    pts = [(0, 0), (1000, 0), (0, 800), (1000, 800), (500, 300)][:n]
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    out = []
    for u, v in pts:
        x, y = sx * u + sh * v, sy * v
        out.append({"ref": f"{u},{v}", "px": (u, v), "real": (c * x - s * y + 10, s * x + c * y + 20)})
    return out


@pytest.mark.parametrize("args,flag", [((2, 2.1), "ANISOTROPIC"), ((2, 2, 1.0), "ROTATED"),
                                       ((2, 2, 0.0, 0.05), "SHEARED")])
def test_affine_detects_anisotropy_rotation_shear(args, flag):
    a = CAL.affine(_anchors(*args))
    assert a["status"] == "CALIBRATED_WITH_FLAGS" and flag in a["flags"] and a["calibration_id"]


def test_affine_clean_and_insufficient_and_degenerate():
    a = CAL.affine(_anchors(2, 2))
    assert a["status"] == "CALIBRATED" and abs(a["sx"] - 2) < 1e-9 and a["max_residual_mm"] < 1e-6
    assert CAL.affine(_anchors(2, 2, n=3))["status"] == "INSUFFICIENT_ANCHORS"
    col = [{"px": (i, i), "real": (2 * i, 2 * i)} for i in range(5)]
    assert CAL.affine(col)["status"] == "DEGENERATE"


def test_xy_never_fakes_the_unobserved_axis():
    c = CAL.xy([], [{"px": 100, "real_mm": 250}, {"px": 200, "real_mm": 500}])
    assert c["status"] == "AXIS_NOT_OBSERVED" and "X_NOT_OBSERVED" in c["flags"] and c["sx"] is None
    assert CAL.measure(40, c, "x")["state"] == "AXIS_NOT_OBSERVED"
    assert CAL.measure(40, c, "y")["value_mm"] == 100.0
    a = CAL.xy([{"px": 100, "real_mm": 200}], [{"px": 100, "real_mm": 210}])
    assert "ANISOTROPIC" in a["flags"]


# ------------------------------------------------------------------ schedule grammar
@pytest.mark.parametrize("raw,g,cnt,dia,extra", [
    ("4%%C16", "COUNT_DIA", 4, 16, {}), ("6%%c14/m", "COUNT_DIA_PER_M", 6, 14, {"per_m": True}),
    ("2%%C12/30cm", "COUNT_DIA_AT_SPACING", 2, 12, {"spacing_cm": 30}),
    ("%%c10/20cm", "DIA_AT_SPACING", None, 10, {"spacing_cm": 20}),
    ("4%%C16/Top", "COUNT_DIA_POSITION", 4, 16, {"position": "TOP"}),
    ("5%%c10/m E.W.", "COUNT_DIA_PER_M", 5, 10, {"each_way": True}),
    ("(T&B)", "UNPARSED", None, None, {}), ("P.C 20x70", "UNPARSED", None, None, {})])
def test_bar_grammar(raw, g, cnt, dia, extra):
    p = SG.parse_bar(raw)
    assert (p["grammar"], p["count"], p["dia_mm"]) == (g, cnt, dia)
    for k, v in extra.items():
        assert p[k] == v
    assert p["interpretation_state"] == ("BLOCKED_INTERPRETATION" if g == "UNPARSED" else "TOKENS_PARSED")


def test_split_cells_and_conflicting_keys_keep_every_row():
    assert SG.bar_from_cells("9", "16/m")["per_m"] and SG.bar_from_cells("", "")["grammar"] == "EMPTY"
    assert SG.bar_from_cells("x", "16")["interpretation_state"] == "BLOCKED_INTERPRETATION"
    rows = [{"k": "SB2", "handle": "A", "attributes": {"W": "80"}}, {"k": "SB2", "handle": "B", "attributes": {"W": "100"}},
            {"k": "SB1", "handle": "C", "attributes": {"W": "70"}}]
    c = SG.key_conflicts(rows, "k")
    assert len(c) == 1 and c[0]["state"] == SG.CONFLICT and c[0]["rows"] == ["A", "B"] and len(c[0]["variants"]) == 2


# ------------------------------------------------------------------ legacy CAD guard
def test_legacy_guard_refuses_without_opt_in(monkeypatch):
    monkeypatch.delenv(LG.ENV, raising=False)
    with pytest.raises(SystemExit) as e:
        LG.require_legacy_opt_in("tools/x.py", ["a.dwg"])
    assert e.value.code == 2


def test_legacy_guard_opt_in_by_flag_or_environment(monkeypatch):
    monkeypatch.delenv(LG.ENV, raising=False)
    assert LG.require_legacy_opt_in("tools/x.py", ["a.dwg", LG.FLAG]) == ["a.dwg"]
    monkeypatch.setenv(LG.ENV, "1")
    assert LG.require_legacy_opt_in("tools/x.py", ["a.dwg"]) == ["a.dwg"]
