"""T-419 inputs (URBAN_V3046_INPUTS_V1) for the development villa: the GF LIFT TIE BEAM (T-408, merged e3d9a092, Gate
A PASS with own re-measure of the 5.500 m runs) and the HOUSE BELOW-GROUND MASONRY (T-407, merged 8c0e8349, Gate A
PASS with own re-measure). Reads ONLY merged files pinned by sha256 (their summaries); every figure below is taken from
them and asserted against them. No drawing content, no position, no name.

    build(project_id) -> the inputs document
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
S408 = ROOT / "research/agents_t408/summary_t408.json"
S407 = ROOT / "research/agents_t407/summary_t407.json"
PINS = {S408: "9c5c41d25e05c470323d1ba608f35c79bdb0ca78033ad33b87be94b75fd56edc",
        S407: "4dda3ee1e210dcc90765ed40277f7a14f4487ec02a19bf862ac9084f0c7c4e41"}

# candidate lines (V3.0.45 ids, re-bound this run; T-408 bound them on V3.0.34, T-407 on V3.0.33)
L_PIT_WALL = "L-684fcad323adc0c8a267"          # STR.CONC.LIFT pit walls, BLOCKED_RFI (V3.0.33)
L_PIT_MEMB, L_PIT_BOARD = "L-302b401eff698289c54e", "L-f0aadf70513eb21d5671"
L_PIT_FORM = ("L-6d72f51dfe7ec1097f00", "L-e3eb00574a3c1c605077")
L_GF_BLOCK = {"MAS.BLOCK": "L-4165954ce4871eda30cc", "ARCH.WALL_VOLUME": "L-4423d85b72b4b4c3e87e",
              "ARCH.WALL_PANEL": "L-63fa78622c74a1c30a1e"}
# template only (project identity, documents, trade text; nothing of its quantity is read): a held GF STR.REBAR line
L_REBAR_TPL = "L-8eac9e46e0d35cc7aed1"

PIT_DEPTH = "pit depth below the GF lift landing F.F.L. (lift supplier; L-1 / D-63)"
BUILD_UP = "GF build-up F.F.L. +1.00 -> slab-on-grade top (structural / architect; RFI-S09)"
SECTION = "lift tie-beam section b x d printed nowhere (ST p.8 note 19 gives the level only; D-43, RFI-B-S14)"
SHEETS = ["ST GF roof slab plan S-COL.BON 33E / 341 / 33B / 338", "ST p.1 column plan 834 / 837 / 831 / 82E",
          "ST ground-beams plan 1096 / 1099 / 1093 / 1090"]


def _load(p):
    b = p.read_bytes()
    h = hashlib.sha256(b).hexdigest()
    if h != PINS[p]:
        raise SystemExit(f"{p.name}: sha256 {h[:8]} is not the merged {PINS[p][:8]}")
    return json.loads(b)


def sources():
    return [{"task": "T-408", "file": "research/agents_t408/summary_t408.json", "sha256": PINS[S408],
             "merge_commit": "e3d9a092bad89fc2ab8edf51bd6e427355400534",
             "checker_run": "Verifier 2026-11-01T05:37Z, Gate A PASS on f5e4022a (own re-measure: GF runs 1.80 / "
                            "1.80 / 1.20 / 0.70 = 5.500 m, band closure 1.600 m2)"},
            {"task": "T-407", "file": "research/agents_t407/summary_t407.json", "sha256": PINS[S407],
             "merge_commit": "8c0e83490cd3823de77b1e42e5277febc1b242cc",
             "checker_run": "Verifier 2026-11-01 00:57 UTC, Gate A PASS on 9667ad1b (own read of ST p.1 note 2, "
                            "runs and levels)"}]


def facts():
    """the merged figures this package carries, asserted against the pinned summaries."""
    s8, s7 = _load(S408), _load(S407)
    gf = s8["storeys"][0]
    tie = {c["id"]: c for c in gf["components"]}
    assert gf["clear_runs_m"] == 5.5 and tie["TIE_BEAM:GF"]["length_m"] == 5.5, "tie length drift"
    assert s8["gf_band_closure"] == {"closes": True, "columns_in_band_m2": 0.5, "gross_band_m2": 1.6,
                                     "runs_x_band_m2": 1.1}, "band closure drift"
    assert s8["ring_all_bound"] and abs(s8["ring_beams_m3"] - 1.764) < 1e-9 and s8["cap_bound"], "ring / cap drift"
    rings = [b["line_id"] for b in s8["binding"] if b["component"].startswith("RING_BEAM:")]
    cap = [b["line_id"] for b in s8["binding"] if b["component"] == "SHAFT_SLAB:2F"]
    raft = [b["line_id"] for b in s8["binding"] if b["component"] == "RAFT"]
    assert len(rings) == 12 and len(cap) == 1 and len(raft) == 1
    assert set(s8["gf_lift_block_lines"]) == set(L_GF_BLOCK.values())
    lift = {x["line_id"]: x for x in s8["lift_lines_v3034"]}
    assert set(lift) == {L_PIT_WALL, L_PIT_MEMB, L_PIT_BOARD, *L_PIT_FORM}
    runs = {r["id"]: r for r in s7["runs"]}
    m, a = runs["MAIN_S"], runs["ANNEX_S"]
    assert (m["net_axis_m"], m["h"]["h_at_least"], m["net_at_least_m2"], m["gross_at_least_m2"]) == \
        (16.27, 0.7, 11.389, 13.4897), "MAIN_S drift"
    assert (a["net_axis_m"], a["h"]["h_at_least"], a["net_at_least_m2"]) == (10.0, None, None), "ANNEX_S drift"
    assert s7["totals"]["existence_unknown_runs"] == ["MAIN_E_SEA", "ANNEX_W_STREET"]
    ol = s7["one_layer"]
    assert (ol["house_axis_m"], ol["fence_axis_m_T403"], ol["pool_axis_m_T403"], ol["band_axis_total_m"]) == \
        (44.37, 44.07, 3.5, 91.94) and ol["partition_residual_m"] == 0.0
    return {"rings": rings, "cap": cap[0], "cap_m3": s8["cap_m3"], "raft": raft[0],
            "raft_m3": next(b["value"] for b in s8["binding"] if b["component"] == "RAFT"),
            "main_s": m, "annex_s": a, "e_w": {r: runs[r]["net_axis_m"] for r in ("MAIN_E_SEA", "ANNEX_W_STREET")},
            "one_layer": ol, "gb_main_s": [g["line_id"] for g in m["gb_runs_over"]]}


def build(project_id):
    f = facts()
    m = f["main_s"]
    common_tie = {"piece": "LIFT_TIE_BEAM", "floor": "GF", "owner_trade": "STRUCTURE", "source_tasks": ["T-408"]}
    length = {"kind": "LENGTH", "length_m": 5.5, "sheets": SHEETS}
    add = [
        dict(common_tie, key="TIE", item_code="STR.CONC.LIFT", unit="m3", element_id="LIFT_TIE_BEAM:GF",
             template_line=L_PIT_WALL, beside=dict(length, note="concrete = 5.500 x b x d once the section is printed"),
             item_en="Lift structure concrete (GF tie beam)", item_ar="خرسانة كمرة ربط المصعد",
             physical_element="GF lift tie beam (RC beam between the four GF lift columns at +3.00 above the GF "
                              "F.F.L.; GF storey 4.50 > 4.30, ST p.8 note 19)",
             missing_facts=[SECTION], tied_to=None,
             basis="runs between the GF storey's own column faces S 1.80 / N 1.80 / W 1.20 / E 0.70 (band closure "
                   "1.100 + columns 0.500 = 1.600 m2, 0 overlap; invariant under both D-63 column readings); never "
                   "inside a column or ring-beam line"),
        dict(common_tie, key="TIE_SIDES", item_code="STR.FORMWORK", unit="m2", element_id="LIFT_TIE_BEAM:GF:SIDES",
             template_line=L_PIT_FORM[0], owner_trade="FORMWORK",
             beside=dict(length, note="side forms = 2 x 5.500 x d (shaft face + outer face)"),
             physical_element="GF lift tie beam side forms (shaft face + outer face)",
             missing_facts=["tie-beam depth d (" + SECTION + ")"], tied_to="TIE",
             basis="two faces over the clear runs; the column faces bound the ends"),
        dict(common_tie, key="TIE_SOFFIT", item_code="STR.FORMWORK", unit="m2", element_id="LIFT_TIE_BEAM:GF:SOFFIT",
             template_line=L_PIT_FORM[0], owner_trade="FORMWORK",
             beside=dict(length, note="soffit form = 5.500 x b"),
             physical_element="GF lift tie beam soffit form", missing_facts=["tie-beam width b (" + SECTION + ")"],
             tied_to="TIE", basis="one soffit over the clear runs"),
        dict(common_tie, key="TIE_REBAR", item_code="STR.REBAR", unit="kg",
             element_id="LIFT_TIE_BEAM:GF:REBAR", template_line=L_REBAR_TPL,
             beside=dict(length, note="bars over the clear runs + anchorage into the columns, by the bar detail"),
             physical_element="GF lift tie beam bars",
             missing_facts=["bar detail of the tie beam (no schedule row, no section; never a kg / m3 rate)", SECTION],
             tied_to="TIE", basis="counted from the printed bar detail only (Q-71 drawing-based counting)"),
        {"key": "MAIN_S", "piece": "HOUSE_BELOW_NG_MASONRY", "item_code": "MAS.BLOCK", "unit": "m2",
         "item_en": "Block walls below N.G. (under the house ground beams)",
         "element_id": "HOUSE_BELOW_NG:MAIN_S", "floor": "FOUNDATION", "template_line": L_GF_BLOCK["MAS.BLOCK"],
         "owner_trade": "BLOCKWORK BELOW N.G.", "source_tasks": ["T-407"], "tied_to": None,
         "physical_element": "black block under the neighbour-side main-house exterior ground beams (S run), from the "
                             "foundation top to the beam soffit (ST p.1 note 2)",
         "beside": {"kind": "AT_LEAST_AREA", "run_m": m["net_axis_m"], "height_at_least_m": m["h"]["h_at_least"],
                    "area_m2": m["net_at_least_m2"], "gross_area_m2": m["gross_at_least_m2"]},
         "missing_facts": ["formation (foundation) level under the neighbour-side beams (designer; Q-21 C: 1.50 m is "
                           "a minimum)", "blinding under the beam / on the band 0 .. 0.10 m (designer)",
                           "block thickness under the 0.30 beam on the 0.20 band (designer)",
                           "block product / density (Q-65 C)"],
         "basis": "axis 19.271 m on the 0.20 lower band less columns 3.001 m (corner columns split once) = 16.270 m "
                  "net (= the beam ff 16.27); h >= soffit +-0.00 - 0.10 blinding max - highest foundation top -0.80; "
                  "black block by the note (owner block rule 2026-10-20 10:45); never inside the fence masonry, the "
                  "ground-beam concrete (" + ", ".join(f["gb_main_s"]) + ") or the band"},
        {"key": "ANNEX_S", "piece": "HOUSE_BELOW_NG_MASONRY", "item_code": "MAS.BLOCK", "unit": "m2",
         "item_en": "Block walls below N.G. (under the house ground beams)",
         "element_id": "HOUSE_BELOW_NG:ANNEX_S", "floor": "FOUNDATION", "template_line": L_GF_BLOCK["MAS.BLOCK"],
         "owner_trade": "BLOCKWORK BELOW N.G.", "source_tasks": ["T-407"], "tied_to": None,
         "physical_element": "black block under the neighbour-side annex exterior ground beams (S run), from the "
                             "foundation top to the beam soffit (ST p.1 note 2)",
         "beside": {"kind": "NO_BOUND", "why": "annex beam soffit CONFLICT (D-35, RFI-S09): no bound; net run 10.000 m "
                                              "(axis 10.701 less columns 0.701); reading L (7.000 m2) shown in T-407, "
                                              "not adopted"},
         "missing_facts": ["annex exterior beam depth / soffit (D-35 CONFLICT, RFI-S09)",
                           "formation (foundation) level (designer; Q-21 C)", "block thickness (designer)",
                           "block product / density (Q-65 C)"],
         "basis": "printed run (p.1 note 2), height unbounded while the soffit is in CONFLICT; never inside the fence "
                  "masonry, the ground-beam concrete (L-402dbe61) or the band"},
    ]
    restate = [{"line_id": lid, "expect": {"item_code": code, "evidence_state": "BLOCKED_RFI"},
                "facts": [PIT_DEPTH, BUILD_UP], "source_tasks": ["T-408"],
                "tie_to": L_PIT_WALL if code == "STR.FORMWORK" else None,
                "why": ("F-T408-1: pit-wall height = raft top -> slab-on-grade top depends on both facts" if code in
                        ("STR.CONC.LIFT", "WP.FOUNDATION.LIFT_PIT_MEMBRANE", "WP.FOUNDATION.LIFT_PIT_BOARD") else
                        "F-T408-2: the pit-wall form faces are tied to the pit-wall line " + L_PIT_WALL +
                        " (exists since V3.0.33) and depend on the same two facts")}
               for lid, code in ((L_PIT_WALL, "STR.CONC.LIFT"), (L_PIT_MEMB, "WP.FOUNDATION.LIFT_PIT_MEMBRANE"),
                                 (L_PIT_BOARD, "WP.FOUNDATION.LIFT_PIT_BOARD"), (L_PIT_FORM[0], "STR.FORMWORK"),
                                 (L_PIT_FORM[1], "STR.FORMWORK"))]
    bind = [{"what": "12 lift ring beams GF / 1F / 2F roof", "line_ids": f["rings"], "source_tasks": ["T-408"],
             "expect": {"item_code": "STR.CONC.BEAM", "total": 1.764}},
            {"what": "lift shaft cap (+13.90 roof panel)", "line_ids": [f["cap"]], "source_tasks": ["T-408"],
             "expect": {"item_code": "STR.CONC.SLAB", "total": f["cap_m3"]}},
            {"what": "lift raft FF", "line_ids": [f["raft"]], "source_tasks": ["T-408"],
             "expect": {"item_code": "STR.CONC.FOOTING", "total": f["raft_m3"]}}] + [
            {"what": f"GF lift block line {code} paired with the tie (holds GF-W08 / W09 / W13 / W14)",
             "line_ids": [lid], "source_tasks": ["T-408"],
             "expect": {"item_code": code, "evidence_state": "BLOCKED_RFI", "text": "tie beam"}}
            for code, lid in L_GF_BLOCK.items()] + [
            {"what": "MAIN_S ground-beam concrete over the run (masonry ends at their soffit)", "line_ids":
             f["gb_main_s"], "source_tasks": ["T-407"], "expect": {"item_code": "STR.CONC.GROUND_BEAM"}}]
    ol = f["one_layer"]
    return {"schema": "URBAN_V3046_INPUTS_V1", "project_id": project_id, "sources": sources(), "add": add,
            "restate": restate, "bind": bind,
            "partition": {"house_m": ol["house_axis_m"], "fence_m": ol["fence_axis_m_T403"],
                          "pool_m": ol["pool_axis_m_T403"], "band_m": ol["band_axis_total_m"],
                          "source_tasks": ["T-407"]},
            "register_only": [{"key": k, "net_run_m": v,
                               "why": "band drawn, nothing printed between it and the beam: existence UNKNOWN "
                                      "(designer item 3); no line until printed, never 0"}
                              for k, v in f["e_w"].items()]}
