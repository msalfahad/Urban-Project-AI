"""T-181: doors and windows like for like (pcs vs pcs, m2 vs m2) on a synthetic villa (NOT the development villa),
plus a read-only run of the committed Alsenan register. Hand calculation written before running the tool:

  Register (8 openings): AD1 aluminium door 1.00 x 2.20 ASSUMED (Q-55 C) = 2.200, AD2 aluminium door 0.90 x 2.20
  ASSUMED = 1.980, W1 window 1.50 x 1.20 PRINTED = 1.800, W2 (mirrored twin, its OWN printed chain) 1.50 x 1.20 =
  1.800, W3 window 2.00 with height HELD (no area), P1 PVC 0.80 x 2.20 ASSUMED = 1.760, P2 PVC width range 0.80 .. 0.90
  x 2.20 (HELD, candidate 1.760 .. 1.980), G1 site gate (no supply class).
  Freelancer rows (count B x width C x height D = area H): 10 ext door 2 x 1.00 x 2.40 = 4.80; 11 window 2 x 1.50 x
  1.20 = 3.60; 12 window 1 x 2.00 x 2.00 = 4.00; cover totals doors 4.80, windows 7.60.
    ALU door  nr: 2 vs 2 -> COMPARED, 0.000            m2: 2.200 + 1.980 = 4.180 vs 4.800 -> -0.620 (-12.92 %)
    window    nr: 3 vs 3 -> COMPARED, 0.000            m2: W3 HELD -> HELD (never 0); same openings W1 + W2:
                                                           3.600 vs 2 x 1.50 x 1.20 = 3.600 -> 0.000
    PVC       NOT COMPARABLE: 2 settled pcs; m2 1.760 ASSUMED — OWNER-APPROVED + P2 HELD (1.760 .. 1.980)
    G1        not a supply class (listed, not lost)
  Adverse: a class-held door with candidates {ALU, PVC} -> ALU nr and m2 HELD; a photo hold cause on W1 -> window nr
  HELD (W1 count unsettled); his area != count x width x height -> refused; rows not re-adding to the cover total ->
  refused; an ASSUMED height without an owner-approved source -> refused; an unknown scope label -> refused; a
  duplicate opening -> refused; a row covering 2 openings where he counts 3 -> scope DIFFERS; units never converted
  (no nr row ever answers an m2 key).
"""

from __future__ import annotations

import copy
import csv
import json
from pathlib import Path

import pytest

from tools import alsenan_keymap as K

ROOT = Path(__file__).resolve().parents[2]
ASSUMED_SRC = "Q-55 C owner fallback 2.20, ASSUMED — OWNER-APPROVED"
COLS = ("ID", "KIND", "FLOOR", "BOQ_LINE", "CLASS_STATUS", "WIDTH_M", "WIDTH_LO_M", "HEIGHT_M", "HEIGHT_STATUS",
        "HEIGHT_SOURCE", "FREELANCER_KEY", "VERDICT", "HOLD_CAUSE")


def op(i, kind, line, w, h, hs, lab="none", lo="", cause="", cls="DRAWING-CONFIRMED", src=None):
    return dict(zip(COLS, (i, kind, "L0", line, cls, w, lo, h, hs,
                           src if src is not None else (ASSUMED_SRC if hs == "ASSUMED" else "printed chain"),
                           lab, "", cause)))


def register():
    return [op("AD1", "DOOR", "DOOR.EXTERNAL.ALUMINIUM", "1.00", "2.20", "ASSUMED", "F-EXT"),
            op("AD2", "DOOR", "DOOR.EXTERNAL.ALUMINIUM", "0.90", "2.20", "ASSUMED", "F-EXT"),
            op("W1", "WINDOW", "WINDOW.ALUMINIUM", "1.50", "1.20", "PRINTED", "F-W150"),
            op("W2", "WINDOW", "WINDOW.ALUMINIUM", "1.50", "1.20", "PRINTED", "F-W150"),
            op("W3", "WINDOW", "WINDOW.ALUMINIUM", "2.00", "", "HELD", "F-W200"),
            op("P1", "DOOR", "DOOR.INTERNAL.PVC", "0.80", "2.20", "ASSUMED"),
            op("P2", "DOOR", "DOOR.INTERNAL.PVC", "0.90", "2.20", "ASSUMED", lo="0.80"),
            op("G1", "GATE", "SITE.GATE_HELD", "", "", "HELD", cls="HELD")]


def raw(rows=((10, 2, 1.00, 2.40, 4.80), (11, 2, 1.50, 1.20, 3.60), (12, 1, 2.00, 2.00, 4.00))):
    return {"rows": [{"file": "F", "sheet": "Q", "row": n, "cells": {f"B{n}": {"v": b}, f"C{n}": {"v": c},
                                                                      f"D{n}": {"v": d}, f"H{n}": {"v": h}}}
                     for n, b, c, d, h in rows]}


def keymap():
    return {"SCHEMA": K.OPENINGS_SCHEMA, "register_side_label": "synthetic register",
            "reference_cells": {"count": "B", "width": "C", "height": "D", "area": "H"},
            "approved_assumption_sources": ["Q-55 C"],
            "classes": [
                {"class": "ALU_DOOR", "trade": "DOORS", "register_boq_lines": ["DOOR.EXTERNAL.ALUMINIUM"],
                 "engine_item_codes": ["DOOR.EXTERNAL.ALUMINIUM"], "reference_rows": ["F:Q:10"],
                 "cover_total": {"ref_id": "F:Q:C1", "m2": 4.80}},
                {"class": "ALU_WINDOW", "trade": "WINDOWS", "register_boq_lines": ["WINDOW.ALUMINIUM"],
                 "engine_item_codes": ["ARCH.WINDOW"], "reference_rows": ["F:Q:11", "F:Q:12"],
                 "cover_total": {"ref_id": "F:Q:C2", "m2": 7.60}},
                {"class": "PVC_DOOR", "trade": "DOORS", "register_boq_lines": ["DOOR.INTERNAL.PVC"],
                 "engine_item_codes": ["DOOR.INTERNAL.PVC"], "reference_rows": [],
                 "not_comparable_reason": "no PVC line in his workbook"}],
            "scope_labels": {"F-EXT": "F:Q:10", "F-W150": "F:Q:11", "F-W200": "F:Q:12"}}


def run(reg=None, rw=None, km=None, lines=None):
    return K.openings_like_for_like(reg if reg is not None else register(), rw if rw is not None else raw(),
                                    km if km is not None else keymap(), lines)


def cls(res, name):
    return next(c for c in res["classes"] if c["class"] == name)


def test_aluminium_doors_both_units():
    c = cls(run(), "ALU_DOOR")
    assert c["lines"]["nr"]["outcome"] == "COMPARED" and c["lines"]["nr"]["engine_qty"] == 2.0
    assert c["lines"]["nr"]["signed_error"] == 0.0
    m2 = c["lines"]["m2"]
    assert m2["outcome"] == "COMPARED" and m2["engine_qty"] == pytest.approx(4.180)
    assert m2["signed_error"] == pytest.approx(-0.620)
    assert 100 * m2["signed_error"] / m2["reference_qty"] == pytest.approx(-12.9167, abs=1e-3)
    assert c["m2_confirmed"] == 0.0 and c["m2_assumed_owner_approved"] == pytest.approx(4.180)


def test_windows_pcs_compared_m2_held_never_zero():
    res = run()
    c = cls(res, "ALU_WINDOW")
    assert c["lines"]["nr"]["outcome"] == "COMPARED" and c["lines"]["nr"]["engine_qty"] == 3.0
    assert c["lines"]["m2"]["outcome"] == "HELD" and c["lines"]["m2"]["engine_qty"] is None
    assert c["m2_held"] == ["W3"] and c["m2_confirmed"] == pytest.approx(3.600)
    s = c["same_openings_m2"]
    assert s["openings"] == ["W1", "W2"] and s["engine"] == pytest.approx(3.6) and s["freelancer"] == pytest.approx(3.6)
    w3 = next(o for o in res["openings"] if o["id"] == "W3")
    assert w3["m2"] is None and w3["m2_status"] == "HELD" and w3["pcs"] == 1.0


def test_pvc_not_comparable_never_a_false_positive():
    res = run()
    c = cls(res, "PVC_DOOR")
    assert not c["comparable"] and c["pcs_settled"] == 2
    assert c["m2_assumed_owner_approved"] == pytest.approx(1.760) and c["m2_held"] == ["P2"]
    assert c["m2_held_candidates_known"] == [(1.76, 1.98)]
    assert res["scored"]["false_positives"] == []
    assert {r["id"] for r in res["not_comparable"]["PVC_DOOR"]} == {"P1:PVC_DOOR[nr]", "P1:PVC_DOOR[m2]",
                                                                     "P2:PVC_DOOR[nr]", "P2:PVC_DOOR[m2]"}
    assert res["not_a_supply_class"] == ["G1"]


def test_units_never_mixed():
    res = run()
    for ln in res["scored"]["lines"]:
        assert ln["key"].endswith(f"[{ln['unit']}]")
        assert ln["refused_engine_ids"] == []
    units = {(b["trade"], b["unit"]) for b in res["scored"]["buckets"]}
    assert units == {("DOORS", "nr"), ("DOORS", "m2"), ("WINDOWS", "nr"), ("WINDOWS", "m2")}


def test_class_held_door_holds_both_candidate_classes():
    reg = register() + [op("AD3", "DOOR", "DOOR.CLASS_HELD", "1.00", "2.20", "ASSUMED", "F-EXT?", cls="HELD")]
    km = keymap()
    km["held_class_candidates"] = {"AD3": {"classes": ["ALU_DOOR", "PVC_DOOR"], "source": "conditional rule"}}
    res = run(reg=reg, km=km)
    c = cls(res, "ALU_DOOR")
    assert c["lines"]["nr"]["outcome"] == "HELD" and c["lines"]["m2"]["outcome"] == "HELD"
    assert c["class_held_candidates"] == ["AD3"]
    assert any(r["id"] == "AD3:PVC_DOOR[nr]" and r["status"] == "HELD" for r in res["not_comparable"]["PVC_DOOR"])
    row = next(s for s in res["scope_rows"] if s["ref_id"] == "F:Q:10")
    assert row["uncertain_openings"] == ["AD3"] and row["scope"] == "AGREES"   # 2 tied openings = his 2


def test_hold_cause_holds_the_count():
    reg = register()
    reg[2]["HOLD_CAUSE"] = "photo: rendered as two windows with a pier"
    res = run(reg=reg)
    c = cls(res, "ALU_WINDOW")
    assert c["lines"]["nr"]["outcome"] == "HELD" and c["pcs_held"] == ["W1"] and c["pcs_settled"] == 2
    w1 = next(o for o in res["openings"] if o["id"] == "W1")
    assert w1["m2"] is None and w1["m2_candidate"] == (1.8, 1.8)
    assert next(s for s in res["scope_rows"] if s["ref_id"] == "F:Q:11")["scope"] == "COUNT HELD"


def test_scope_differs_when_his_count_differs():
    rw = raw(((10, 2, 1.00, 2.40, 4.80), (11, 3, 1.50, 1.20, 5.40), (12, 1, 2.00, 2.00, 4.00)))
    km = keymap()
    km["classes"][1]["cover_total"]["m2"] = 9.40
    res = run(rw=rw, km=km)
    assert next(s for s in res["scope_rows"] if s["ref_id"] == "F:Q:11")["scope"] == "DIFFERS"
    c = cls(res, "ALU_WINDOW")
    assert c["lines"]["nr"]["engine_qty"] == 3.0 and c["lines"]["nr"]["reference_qty"] == 4.0


@pytest.mark.parametrize("mutate, msg", [
    (lambda reg, rw, km: rw["rows"][0]["cells"].update({"H10": {"v": 4.90}}), "count x width x height"),
    (lambda reg, rw, km: km["classes"][0]["cover_total"].update({"m2": 5.0}), "cover total"),
    (lambda reg, rw, km: reg[0].update({"HEIGHT_SOURCE": "typical door height"}), "owner-approved source"),
    (lambda reg, rw, km: reg[0].update({"FREELANCER_KEY": "F-XYZ"}), "scope labels"),
    (lambda reg, rw, km: reg.append(dict(reg[0])), "repeated"),
    (lambda reg, rw, km: reg[0].update({"HEIGHT_STATUS": "INFERRED"}), "PRINTED / ASSUMED / HELD"),
    (lambda reg, rw, km: reg[0].update({"WIDTH_M": "-1"}), "non-negative"),
    (lambda reg, rw, km: km["classes"][2].update({"not_comparable_reason": ""}), "not-comparable reason"),
    (lambda reg, rw, km: km.update({"SCHEMA": "URBAN_ALSENAN_KEY_MAP_V1"}), "schema"),
    (lambda reg, rw, km: rw["rows"][0]["cells"].pop("B10"), "empty"),
])
def test_refusals(mutate, msg):
    reg, rw, km = register(), raw(), keymap()
    mutate(reg, rw, km)
    with pytest.raises(ValueError, match=msg):
        run(reg=reg, rw=rw, km=km)


def test_engine_run_pcs_side():
    lines = [{"line_id": f"E{i}", "item_code": "ARCH.WINDOW", "unit": "pcs", "evidence_state": "MEASURED",
              "measured_net": 1.0, "location": {"element_id": f"OP{i}"}} for i in range(2)]
    lines += [{"line_id": "E9", "item_code": "DOOR.EXTERNAL.ALUMINIUM", "unit": "pcs", "evidence_state": "BLOCKED_RFI",
               "measured_net": None, "location": {"element_id": "OP9"}},
              {"line_id": "E10", "item_code": "DOOR.INTERNAL.PVC", "unit": "pcs", "evidence_state": "MEASURED",
               "measured_net": 1.0}]
    side = run(lines=lines)["engine_run_pcs"]
    by = {ln["key"]: ln for ln in side["lines"]}
    assert by["ALU_WINDOW[nr]"]["outcome"] == "COMPARED" and by["ALU_WINDOW[nr]"]["signed_error"] == -1.0
    assert by["ALU_DOOR[nr]"]["outcome"] == "HELD"
    assert by["ALU_WINDOW[m2]"]["outcome"] == "SILENT_OMISSION"      # the engine has no window m2 line
    assert side["false_positives"] == []                             # PVC has no reference row: not scored


def test_cli_and_v1_cli_untouched(tmp_path):
    reg = tmp_path / "reg.csv"
    with reg.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS)
        w.writeheader()
        w.writerows(register())
    (tmp_path / "raw.json").write_text(json.dumps(raw()), encoding="utf-8")
    (tmp_path / "km.json").write_text(json.dumps(keymap()), encoding="utf-8")
    rc = K.main(["--openings-register", str(reg), "--openings-raw", str(tmp_path / "raw.json"), "--openings-key-map",
                 str(tmp_path / "km.json"), "--openings-out", str(tmp_path / "o.json"),
                 "--openings-markdown", str(tmp_path / "o.md")])
    assert rc == 0 and json.loads((tmp_path / "o.json").read_text())["SCHEMA"] == K.OPENINGS_RESULT_SCHEMA
    assert "NOT COMPARABLE" in (tmp_path / "o.md").read_text(encoding="utf-8")
    with pytest.raises(SystemExit):
        K.main(["--openings-out", "x"])            # without --openings-register the v1 parser runs (needs --run)


def test_alsenan_register_read_only():
    """The committed T-150 r2 register against the freelancer's aluminium rows (development villa; diagnostic)."""
    with (ROOT / "research/agents_t150/OPENINGS_T150.csv").open(encoding="utf-8", newline="") as fh:
        reg = list(csv.DictReader(fh))
    res = K.openings_like_for_like(
        reg, json.loads((ROOT / "tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json").read_text(encoding="utf-8")),
        json.loads((ROOT / "tests/alsenan/T181_OPENINGS_KEY_MAP.json").read_text(encoding="utf-8")))
    w, d = cls(res, "WINDOW.ALUMINIUM"), cls(res, "DOOR.EXTERNAL.ALUMINIUM")
    assert w["reference"] == {"nr": 29.0, "m2": pytest.approx(116.9)}
    assert d["reference"] == {"nr": 5.0, "m2": pytest.approx(12.0)}
    assert w["pcs_settled"] == 28 and w["pcs_held"] == ["W02"] and w["lines"]["nr"]["outcome"] == "HELD"
    assert w["m2_confirmed"] == pytest.approx(56.771) and len(w["m2_held"]) == 21
    assert w["same_openings_m2"]["freelancer"] == pytest.approx(54.931)
    assert d["pcs_settled"] == 5 and d["class_held_candidates"] == ["D-GF-05"]
    assert d["m2_assumed_owner_approved"] == pytest.approx(10.560) and d["m2_confirmed"] == 0.0
    assert cls(res, "DOOR.INTERNAL.PVC")["m2_assumed_owner_approved"] == pytest.approx(36.080)
    assert all(s["scope"] in ("AGREES", "COUNT HELD") for s in res["scope_rows"])
    assert res["scored"]["false_positives"] == [] and res["scored"]["duplicates"] == []
