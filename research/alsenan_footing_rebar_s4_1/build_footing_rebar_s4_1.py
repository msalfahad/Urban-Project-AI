"""ALSENAN S4.1 - footing rebar DELTA release over the frozen S4 baseline (source-recovery graphics).

    python3 -I research/alsenan_footing_rebar_s4_1/build_footing_rebar_s4_1.py

S4 stays frozen: its manifest is hash-checked before anything is read, and no S4 file is written. This round writes
BASELINE + DELTA only (engine.source.delta_release), with every graphic reading classified by
engine.source.graphic_evidence:
  * single-layer long bars: re-modelled as STRAIGHT_RUN + UPTURN_LEG_1/2 + END_HOOK_1/2 + BEND_ARC_1/2. The frozen
    straight length stays known steel (KNOWN_STRAIGHT_SEGMENT, complete bar LOWER_BOUND); legs, hooks and bends are
    shape-only (no dimension, no deterministic top endpoint), so they carry no kg;
  * single-layer short bars: the U shape is NOT copied; straight portion = lower bound, end treatment blocked;
  * two-layer bottom bars: the 'straight' basis is withdrawn -> END_TREATMENT_NOT_ESTABLISHED facet;
  * BOXED: existence (printed cell) and shape (inverted U) recorded; meaning of 3+n, diameter, count blocked;
  * FF '2 Ø16': wall-base bars inside the pit-wall band -> ownership transfer to LIFT_PIT / SPECIAL_STRUCTURE (S8).
Blind: reads only the frozen S4 package and the source-recovery evidence (issued-set readings). Deterministic.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.source import delta_release as DR  # noqa: E402
from engine.source import graphic_evidence as GE  # noqa: E402

ROUND = "S4.1"
POLICY = "FOOTING_REBAR_S4_1_DELTA_V1"
S4 = ROOT / "research/alsenan_footing_rebar_s4"
SRD = ROOT / "research/source_recovery_delta"
CODE = ["engine/source/graphic_evidence.py", "engine/source/delta_release.py",
        "research/alsenan_footing_rebar_s4_1/build_footing_rebar_s4_1.py"]
INPUTS = ["research/alsenan_footing_rebar_s4/S4_FREEZE_MANIFEST.json",
          "research/source_recovery_delta/13_GRAPHIC_EVIDENCE.json",
          "research/source_recovery_delta/02_UNRESOLVED_MASTER_REGISTER.csv",
          "research/source_recovery_delta/07_S4_1_CANDIDATES.csv"]
OUTPUTS = ["S4_1_DELTA_COMPONENTS.csv", "S4_1_RELEASE_SUMMARY.json", "S4_1_OWNERSHIP_TRANSFERS.csv",
           "S4_1_UNRESOLVED.csv", "S4_1_PROVENANCE.jsonl", "S4_1_CHANGELOG.md"]
PDF_SHA = "74da1523f05eb3c6a4fe3ddebaef2c3d841891f003efc03bc32a3fb4553337e3"
LONG_PORTIONS = ("STRAIGHT_RUN", "UPTURN_LEG_1", "UPTURN_LEG_2", "END_HOOK_1", "END_HOOK_2", "BEND_ARC_1",
                 "BEND_ARC_2")
END_PORTIONS = ("STRAIGHT_RUN", "END_TREATMENT_1", "END_TREATMENT_2")
COMPONENT_ORDER = ("BOTTOM_LONG", "BOTTOM_SHORT", "TOP_LONG", "TOP_SHORT", "BOXED", "OTHER_EXPLICIT_EXTRA",
                   "STARTER_DOWEL_REFERENCE")
PENDING_ENGINEER = ("F|F10",)
P13 = "ST7757.pdf p.13 'TYP. DETAIL OF ISOLATED FOOTING' (both variants)"
P14 = "ST7757.pdf p.14 'DETAIL OF LIFT WITH ISOLATED FOOTING (WITHOUT BASEMENT)'"


class Stop(SystemExit):
    pass


def check(cond, what):
    if not cond:
        raise Stop(f"S4.1 evidence check failed: {what}")


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _j(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _rows(p):
    return list(csv.DictReader(open(p, encoding="utf-8")))


def _csv(path, rows, fields):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow({k: (json.dumps(r.get(k), sort_keys=True, ensure_ascii=False) if isinstance(r.get(k), (list, dict))
                        else ("" if r.get(k) is None else (round(r[k], 6) if isinstance(r.get(k), float) else r[k])))
                    for k in fields})
    path.write_text(buf.getvalue(), encoding="utf-8")


def _json(path, obj):
    path.write_text(json.dumps(obj, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def code_digest():
    h = hashlib.sha256()
    for c in CODE:
        h.update(c.encode() + b"\0" + (ROOT / c).read_bytes() + b"\0")
    return h.hexdigest()


# ------------------------------------------------------------------ evidence (issued-set readings, re-asserted)
def evidence():
    ge = _j(SRD / "13_GRAPHIC_EVIDENCE.json")
    check(ge["inputs"]["ST7757.pdf"] == PDF_SHA, "graphic evidence read from the issued PDF")
    ev = ge["evidence"]
    e1, e3, e5 = ev["E-PDF-01"], ev["E-PDF-03"], ev["E-DXF-05"]
    details = {}
    for name in ("SHALLOW", "DEEP"):
        d = e1["facts"][name]
        u, box = d["long_bar_U"], d["boxed_inverted_U"]
        base_level = u["base"][0][0]
        check(len(u["legs"]) == 2 and len(u["hooks_45deg"]) == 2, f"{name}: U = base + 2 legs + 2 hooks")
        check(all(abs(min(p[0] for p in leg) - base_level) < 0.2 for leg in u["legs"]),
              f"{name}: legs rise from the bottom-run level")
        leg_top = max(max(p[0] for p in leg) for leg in u["legs"])
        boxed_top = box["top"][0][0]
        gap = round(boxed_top - leg_top, 1)
        # the leg top is NOT on the boxed bar, NOT on a cover line: it is a free end under the boxed top run
        check(gap > 1.0, f"{name}: leg top stops below the boxed top run (no shared level)")
        check(len(d["leader_on_long_bar"]) == 1 and len(d["leader_on_boxed_bar"]) == 1, f"{name}: one leader each")
        check(box["hooks"] == 0 and len(box["legs"]) == 2, f"{name}: boxed = inverted U, no hooks")
        details[name] = {"base_level_pt": base_level, "leg_top_pt": leg_top, "boxed_top_pt": boxed_top,
                         "leg_top_gap_to_boxed_run_pt": gap, "leg_length_pt": u["leg_length_pt"],
                         "hooks_45deg": u["hooks_45deg"], "leader_on_long_bar": d["leader_on_long_bar"][0]["end"],
                         "short_bar_dots": d["bottom_bar_dots_in_section"]}
    walls = e3["facts"]["bars_per_cut_wall"]
    check(len(walls) == 2 and all(w["top"] == 2 and w["bottom"] == 2 for w in walls), "FF: 2 + 2 bars per cut wall")
    lo, hi = walls[1]["wall_band_y"]          # the labelled wall: one leader on its top pair, one on its bottom pair
    check(all(lo <= p[1] <= hi for leader in e3["facts"]["two_16_leaders"] for p in leader),
          "FF: both '2 Ø16' leaders end inside the cut pit-wall band")
    check(e5["facts"]["walls"] == 4, "FF: pit = four walls on plan")
    return {"E-PDF-01": details, "E-PDF-03": {"bars_per_cut_wall": walls, "leaders": e3["facts"]["two_16_leaders"],
                                             "ocr_raw": e3["facts"]["ocr_raw"]},
            "E-DXF-05": e5["facts"], "pdf_sha": PDF_SHA}


def srd_items():
    reg = {r["ITEM_ID"]: r for r in _rows(SRD / "02_UNRESOLVED_MASTER_REGISTER.csv")}
    cand = {r["CANDIDATE_ID"]: r for r in _rows(SRD / "07_S4_1_CANDIDATES.csv")}
    for i, st in (("S4-03", "SOURCE_FOUND_DERIVED"), ("S4-07", "SOURCE_FOUND_DERIVED"),
                  ("S4-12", "SOURCE_FOUND_DERIVED"), ("S4-13", "SOURCE_EXPECTED_NOT_LOCATED"),
                  ("S4-14", "SOURCE_EXPECTED_NOT_LOCATED"), ("S4-01", "SOURCE_EXPECTED_NOT_LOCATED"),
                  ("S4-02", "SOURCE_EXPECTED_NOT_LOCATED"), ("S4-05", "SOURCE_EXPECTED_NOT_LOCATED"),
                  ("S4-08", "SOURCE_EXPECTED_NOT_LOCATED"), ("S4-09", "PENDING_ENGINEER_CLARIFICATION")):
        check(reg[i]["TERMINAL_STATE"] == st, f"SRD item {i} is {st}")
    check(set(cand) == {"S4.1-C01", "S4.1-C02", "S4.1-C03", "S4.1-C04", "S4.1-C05"}, "five S4.1 candidates")
    return reg, cand


# ------------------------------------------------------------------ delta model
def leg_derivation(occ, comp, ev):
    """Document the attempted rule-B derivation of an upturn leg from footing depth, cover and bar levels."""
    sr = occ["schedule_row"]
    d = float(comp["dia_mm"])
    cover = float(comp["cover_1_mm"])
    return {"footing_depth_D_mm": sr["D_mm"], "D_source": f"schedule row {sr['insert_handle']} ({sr['mark']})",
            "cover_bottom_mm": cover, "cover_source": "COVER_AGAINST_SOIL_70MM (P8-N22)",
            "bottom_run_level_mm": cover + d / 2.0,
            "top_endpoint": "drawn just under the boxed bar's top run (p.13: gap "
                            f"{ev['E-PDF-01']['SHALLOW']['leg_top_gap_to_boxed_run_pt']} / "
                            f"{ev['E-PDF-01']['DEEP']['leg_top_gap_to_boxed_run_pt']} pt plotted, not dimensioned); "
                            "not on the top cover line, not on any dimensioned level; the boxed bar's own level "
                            "depends on its diameter (S4-02, not located)",
            "conditions": {GE.ENDPOINTS_DETERMINISTIC: False, GE.DIMENSIONS_FROM_PROJECT_SOURCE: True,
                           GE.DERIVATION_REPRODUCIBLE: False, GE.NO_CONTRADICTING_PROJECT_SOURCE: True},
            "result": "rule B fails (top endpoint not deterministic) -> GRAPHIC_EXPLICIT_SHAPE_ONLY, length blocked; "
                      "the plotted leg length is not used"}


def build(frozen, ev, occ_by):
    base = DR.baseline_label(frozen)
    comps = _rows(S4 / "FOOTING_REBAR_COMPONENTS.csv")
    order = {c: i for i, c in enumerate(COMPONENT_ORDER)}
    comps.sort(key=lambda c: (c["occurrence_id"], order[c["component"]]))
    recs, prov, transfers = [], [], []
    # full-precision frozen kg per part (the CSV rounds to 6 decimals)
    part_kg = {}
    for line in (S4 / "FOOTING_REBAR_PROVENANCE.jsonl").read_text(encoding="utf-8").splitlines():
        p = json.loads(line)
        part_kg[p["part_id"]] = p["kg"]

    def kg(c):
        if not c["kg"]:
            return 0.0
        v = part_kg[f"{c['occurrence_id']}:{c['component']}"]
        check(abs(v - float(c["kg"])) < 1e-5, f"provenance kg matches the component row {c['occurrence_id']}")
        return v

    def add(c, change, portion, cls, model, state, portion_state, why, blocked=(), facets=None, evid=(),
            page="", handles="", source="", derivation=None):
        cid = f"{c['occurrence_id']}:{c['component']}"
        known_here = kg(c) if portion in ("STRAIGHT_RUN", "WHOLE_COMPONENT") else 0.0
        r = DR.record(delta_id=f"S4.1-D{len(recs) + 1:04d}", change_kind=change, frozen_baseline=base,
                      baseline_component_id=cid, old_state=c["state"], old_known_quantity=known_here,
                      new_project_source=source, source_page=page, source_handles=handles,
                      graphic_evidence_class=cls, new_component_model=model, delta_known_quantity=0.0,
                      new_blocked_components=list(blocked), new_release_state=state, portion=portion,
                      portion_state=portion_state, quantity_basis=DR.BASIS_FROZEN if known_here else DR.BASIS_NONE,
                      why=why, OCCURRENCE_ID=c["occurrence_id"], MARK=c["mark"], COMPONENT=c["component"],
                      ACCURATE_COMPONENT=c["accurate_component"], DIA_MM=c["dia_mm"], COUNT=c["count"],
                      FROZEN_NET_STRAIGHT_MM=c["net_straight_mm"], FACETS=facets or {}, EVIDENCE_IDS=list(evid),
                      COMPLETE_BAR=(state if c["state"] not in ("NOT_APPLICABLE",) else "NOT_APPLICABLE"))
        recs.append(r)
        prov.append({"delta_id": r["DELTA_ID"], "baseline_component_id": cid, "portion": portion,
                     "frozen_baseline": {"manifest": frozen["manifest"], "sha256": frozen["manifest_sha256"],
                                         "engine_commit_stamp": frozen["engine_commit_stamp"]},
                     "frozen_row": {k: c[k] for k in ("state", "kg", "net_straight_mm", "end_treatment", "count",
                                                      "dia_mm")},
                     "graphic_evidence_class": cls, "evidence_ids": list(evid), "source_page": page,
                     "source_handles": handles, "pdf_sha256": PDF_SHA if page.startswith("ST7757.pdf") else None,
                     "derivation": derivation, "change_kind": change, "portion_state": portion_state,
                     "delta_kg": 0.0, "round": ROUND})
        return r

    for c in comps:
        occ = occ_by[c["occurrence_id"]]
        layers = (occ["schedule_row"] or {}).get("layers")
        comp, st = c["component"], c["state"]
        pending = c["mark"] in PENDING_ENGINEER
        if st == "NOT_APPLICABLE":
            add(c, DR.NO_CHANGE, "WHOLE_COMPONENT", GE.NO_GRAPHIC_EVIDENCE, "unchanged (frozen NOT_APPLICABLE)",
                DR.NOT_APPLICABLE, "", "frozen NOT_APPLICABLE carried")
            continue
        if pending:
            add(c, DR.NO_CHANGE, "WHOLE_COMPONENT", GE.NO_GRAPHIC_EVIDENCE,
                "unchanged: F / F10 occurrence conflict awaits the engineer (S4-09); not resolved by inference",
                DR.BLOCKED_UNQUANTIFIED, "", "PENDING_ENGINEER_CLARIFICATION (brief §20)", evid=("E-DXF-10",))
            continue
        if comp == "BOTTOM_LONG" and layers == "SINGLE_LAYER":
            check(st == "VERIFIED" and c["end_treatment"] == "STRAIGHT_SOURCE_SUPPORTED", f"{c['occurrence_id']} long")
            blocked = [f"{c['occurrence_id']}:{comp}:{p}" for p in LONG_PORTIONS[1:]]
            model = ("U BAR = STRAIGHT_RUN + LEFT/RIGHT_UPTURN_LEG + LEFT/RIGHT_45_DEG_END (+2 bends); frozen "
                     "straight length kept as KNOWN_STRAIGHT_SEGMENT; COMPLETE_BAR = LOWER_BOUND")
            facets = {"SHAPE": "SOURCE_FOUND_EXPLICIT (U with 45° ends)", "STRAIGHT_RUN": GE.KNOWN_STRAIGHT_SEGMENT,
                      "UPTURN_LEG": GE.SHAPE_FOUND_LENGTH_BLOCKED, "END_HOOK_45": GE.SHAPE_FOUND_LENGTH_BLOCKED,
                      "BEND_ARC": GE.SHAPE_FOUND_LENGTH_BLOCKED, "COMPLETE_BAR": DR.LOWER_BOUND}
            der = leg_derivation(occ, c, ev)
            for p in LONG_PORTIONS:
                if p == "STRAIGHT_RUN":
                    pr = GE.portion(p, GE.GRAPHIC_EXPLICIT_SHAPE_ONLY, shape_found=True,
                                    length_mm=float(c["net_straight_mm"]), known_segment=True)
                    why = ("frozen straight length (schedule span - 2 x 70 mm cover) stays valid known steel; the "
                           "p.13 drawing shows this run as the base of a U, so the complete bar is longer: "
                           "VERIFIED (complete straight bar) -> KNOWN_STRAIGHT_SEGMENT, COMPLETE_BAR LOWER_BOUND")
                    change, derivation = DR.SEMANTIC_CORRECTION, None
                elif p.startswith("UPTURN"):
                    pr = GE.portion(p, GE.GRAPHIC_EXPLICIT_SHAPE_ONLY, shape_found=True)
                    why = ("leg drawn (shares the bottom-run vertex) but its top endpoint is not bound to a "
                           "dimensioned level: rule-B derivation from D, cover and bar levels fails "
                           "(ENDPOINTS_DETERMINISTIC); no length by scale")
                    change, derivation = DR.PORTION_DECOMPOSITION, der
                elif p.startswith("END_HOOK"):
                    pr = GE.portion(p, GE.GRAPHIC_EXPLICIT_SHAPE_ONLY, shape_found=True)
                    why = "45° end drawn at the leg top (SHAPE_FOUND); hook length not dimensioned or noted"
                    change, derivation = DR.PORTION_DECOMPOSITION, None
                else:
                    pr = GE.portion(p, GE.GRAPHIC_EXPLICIT_SHAPE_ONLY, shape_found=True)
                    why = "bend at the base / leg corner exists (shared vertex); bend radius not drawn or noted"
                    change, derivation = DR.PORTION_DECOMPOSITION, None
                add(c, change, p, pr["graphic_evidence_class"], model, DR.LOWER_BOUND, pr["state"], why,
                    blocked=blocked, facets=facets, evid=("E-PDF-01",), page="ST7757.pdf p.13",
                    handles="p13:S-REIN.D long_bar_U (SHALLOW + DEEP)", source=P13, derivation=derivation)
            continue
        if comp == "BOTTOM_SHORT" and layers == "SINGLE_LAYER":
            check(st == "VERIFIED", f"{c['occurrence_id']} short")
            blocked = [f"{c['occurrence_id']}:{comp}:{p}" for p in END_PORTIONS[1:]]
            model = ("STRAIGHT_RUN (frozen, KNOWN_STRAIGHT_SEGMENT) + END_TREATMENT_1/2 (not drawn); the long-bar U "
                     "is NOT copied; COMPLETE_BAR = LOWER_BOUND")
            facets = {"SHAPE": "NOT_DRAWN (dots in section only)", "STRAIGHT_RUN": GE.KNOWN_STRAIGHT_SEGMENT,
                      "END_TREATMENT": GE.BLOCKED_UNQUANTIFIED, "COMPLETE_BAR": DR.LOWER_BOUND}
            for p in END_PORTIONS:
                if p == "STRAIGHT_RUN":
                    pr = GE.portion(p, GE.GRAPHIC_NTS_OR_UNDIMENSIONED, shape_found=False,
                                    length_mm=float(c["net_straight_mm"]), known_segment=True)
                    why = ("frozen straight length stays valid known steel; the p.13 detail shows short bars only as "
                           "dots, so 'straight' is not supported: VERIFIED -> KNOWN_STRAIGHT_SEGMENT, COMPLETE_BAR "
                           "LOWER_BOUND")
                    change = DR.SEMANTIC_CORRECTION
                else:
                    pr = GE.portion(p, GE.NO_GRAPHIC_EVIDENCE, shape_found=False)
                    why = "end shape not drawn anywhere in the set (S4-13); the long-bar U is not copied (brief §4)"
                    change = DR.PORTION_DECOMPOSITION
                add(c, change, p, pr["graphic_evidence_class"], model, DR.LOWER_BOUND, pr["state"], why,
                    blocked=blocked, facets=facets, evid=("E-PDF-01",), page="ST7757.pdf p.13",
                    handles="p13:S-REIN.D dots in section", source=P13)
            continue
        if comp in ("BOTTOM_LONG", "BOTTOM_SHORT") and layers == "TWO_LAYER":
            check(st == "LOWER_BOUND" and c["end_treatment"] == "STRAIGHT_SOURCE_SUPPORTED", f"{c['occurrence_id']}")
            blocked = [f"{c['occurrence_id']}:{comp}:{p}" for p in END_PORTIONS[1:]]
            ff = c["mark"] == "FF"
            cls = GE.GRAPHIC_NTS_OR_UNDIMENSIONED if ff else GE.NO_GRAPHIC_EVIDENCE
            model = ("STRAIGHT_RUN (frozen lower bound) + END_TREATMENT_1/2: the 'straight' basis came from the "
                     "single-layer detail, now withdrawn -> END_TREATMENT_NOT_ESTABLISHED")
            facets = {"END_TREATMENT": "END_TREATMENT_NOT_ESTABLISHED (was STRAIGHT_SOURCE_SUPPORTED)",
                      "EDGE_BAR_CONVENTION": "carried (S4-10)", "COMPLETE_BAR": DR.LOWER_BOUND}
            for p in END_PORTIONS:
                if p == "STRAIGHT_RUN":
                    pr = GE.portion(p, cls, shape_found=False, length_mm=float(c["net_straight_mm"]),
                                    known_segment=True)
                    why = "frozen lower-bound straight run kept; end facet changed (no kg change)"
                else:
                    pr = GE.portion(p, cls, shape_found=False)
                    why = ("FF: the p.14 loop cannot pair 6/m top with 9/m bottom bars (QA only, S4-11)" if ff else
                           "no two-layer detail for this mark (S4-14)")
                add(c, DR.FACET_ADDED, p, pr["graphic_evidence_class"], model, DR.LOWER_BOUND, pr["state"], why,
                    blocked=blocked, facets=facets, evid=("E-PDF-01", "E-PDF-03"),
                    page="ST7757.pdf p.14" if ff else "", handles="p14:S-REIN.D footing loop" if ff else "",
                    source=P14 if ff else "basis withdrawn (S4-12 / S4-14)")
            continue
        if comp in ("TOP_LONG", "TOP_SHORT"):
            check(st == "LOWER_BOUND" and c["end_treatment"] == "END_TREATMENT_NOT_ESTABLISHED", c["occurrence_id"])
            add(c, DR.NO_CHANGE, "WHOLE_COMPONENT", GE.NO_GRAPHIC_EVIDENCE,
                "unchanged: frozen lower bound, END_TREATMENT_NOT_ESTABLISHED (S4-11)", DR.LOWER_BOUND, "",
                "already END_TREATMENT_NOT_ESTABLISHED", blocked=[f"{c['occurrence_id']}:{comp}:END_TREATMENT"],
                facets={"END_TREATMENT": "END_TREATMENT_NOT_ESTABLISHED", "COMPLETE_BAR": DR.LOWER_BOUND})
            continue
        if comp == "BOXED":
            check(st == "BLOCKED_UNQUANTIFIED", f"{c['occurrence_id']} boxed")
            printed = bool(c["raw_value"])
            existence = ("SOURCE_FOUND_EXPLICIT (schedule cell '%s')" % c["raw_value"] if printed else
                         "SOURCE_EXPECTED_NOT_LOCATED (FN cell blank, S4-05)")
            facets = {"EXISTENCE": existence, "SHAPE": "SOURCE_FOUND_EXPLICIT (inverted U, legs to the bottom-bar "
                                                       "level, no hooks)",
                      "MEANING_OF_3_PLUS_N": "SOURCE_EXPECTED_NOT_LOCATED (S4-01)",
                      "DIAMETER": "SOURCE_EXPECTED_NOT_LOCATED (S4-02)", "COUNT": "BLOCKED (3+n unresolved)",
                      "ORIENTATION": "SOURCE_EXPECTED_NOT_LOCATED (S4-04)", "BOXED_KG": DR.BLOCKED_UNQUANTIFIED}
            add(c, DR.FACET_ADDED, "WHOLE_COMPONENT", GE.GRAPHIC_EXPLICIT_SHAPE_ONLY,
                "BOXED = inverted U (shape recorded); quantity blocked: no external diameter, no reading of 3+n",
                DR.BLOCKED_UNQUANTIFIED, GE.SHAPE_FOUND_LENGTH_BLOCKED,
                "shape facet found; count, diameter and orientation still not located", facets=facets,
                blocked=[f"{c['occurrence_id']}:BOXED"], evid=("E-PDF-01", "E-DXF-01"), page="ST7757.pdf p.13",
                handles="p13:S-REIN.D boxed_inverted_U (SHALLOW + DEEP)", source=P13)
            continue
        if comp == "OTHER_EXPLICIT_EXTRA" and c["mark"] == "FF":
            check(st == "BLOCKED_UNQUANTIFIED" and not c["kg"], "FF extra carries no frozen kg")
            r = add(c, DR.OWNERSHIP_TRANSFER, "WHOLE_COMPONENT", GE.GRAPHIC_EXPLICIT_SHAPE_ONLY,
                    "PIT_WALL / WALL_BASE bars (2 top + 2 bottom Ø16 per cut wall) -> LIFT_PIT / SPECIAL_STRUCTURE "
                    "(future S8); not FOOTING_REBAR", DR.TRANSFERRED_OUT, "",
                    "the '2 Ø16' leaders end on bars inside the cut pit-wall band: wall-base bars, not footing "
                    "reinforcement; no kg in S4.1", facets={"OWNER": "LIFT_PIT / SPECIAL_STRUCTURE",
                                                             "ASSIGNMENT": "SOURCE_FOUND_DERIVED (S4-07)",
                                                             "LENGTH_AND_WALL_COUNT": "SOURCE_EXPECTED_NOT_LOCATED "
                                                                                      "(S4-08)"},
                    evid=("E-PDF-03", "E-DXF-05"), page="ST7757.pdf p.14",
                    handles="p14:S-REIN.D dots + '2 Ø16' leaders; ST7757.dxf S-BW 10EA / 10EB", source=P14)
            transfers.append({
                "TRANSFER_ID": "S4.1-T01", "DELTA_ID": r["DELTA_ID"], "FROZEN_BASELINE": base,
                "BASELINE_COMPONENT_ID": r["BASELINE_COMPONENT_ID"], "OCCURRENCE_ID": c["occurrence_id"],
                "MARK": c["mark"], "FROZEN_STATE": st, "FROZEN_KG": 0.0,
                "OLD_UNRESOLVED_OWNER": "FOOTING_CANDIDATE", "NEW_OWNER": "LIFT_PIT / SPECIAL_STRUCTURE",
                "TARGET_STAGE": "S8", "COMPONENT_ROLE": "PIT_WALL / WALL_BASE",
                "SOURCE_PAGE": "ST7757.pdf p.14", "EVIDENCE_IDS": ["E-PDF-03", "E-DXF-05"],
                "EVIDENCE": "both '2 Ø16' leaders end on bar pairs inside the cut pit-wall band (y "
                            f"{ev['E-PDF-03']['bars_per_cut_wall'][1]['wall_band_y']}); the other cut wall repeats "
                            "2 top + 2 bottom; plan pit = 4 walls of 20 cm (1.80 / 2.20 m)",
                "FACTS_FOUND": "2 top + 2 bottom Ø16 per cut wall (SOURCE_FOUND_DERIVED, S4-07)",
                "STILL_MISSING": "bar length / corner laps and whether all four walls carry them (S4-08)",
                "KG_IN_S4_1": 0.0, "WHY_NOT_FOOTING_REBAR": "the source draws them as wall-base bars; no source "
                                                            "calls them footing reinforcement"})
            continue
        raise Stop(f"unmodelled frozen component {c['occurrence_id']}:{comp} ({st})")
    return comps, recs, prov, transfers


def srd_item_of(u):
    if u["mark"] in PENDING_ENGINEER:
        return "S4-09"
    if u["component"] == "BOXED":
        return "S4-01;S4-02;S4-04;S4-05" if not u["raw_value"] else "S4-01;S4-02;S4-04"
    if u["component"] == "OTHER_EXPLICIT_EXTRA":
        return "S4-07;S4-08"
    return "S4-10;S4-11" if u["component"].startswith("TOP") else "S4-10;S4-14"


def unresolved(recs):
    frozen_unres = _rows(S4 / "FOOTING_REBAR_UNRESOLVED.csv")
    by_cid = {}
    for r in recs:
        by_cid.setdefault(r["BASELINE_COMPONENT_ID"], []).append(r)
    out = []
    for u in frozen_unres:
        cid = f"{u['occurrence_id']}:{u['component']}"
        rs = by_cid[cid]
        state = rs[0]["NEW_RELEASE_STATE"]
        out.append({"UNRESOLVED_ID": f"S4.1-U{len(out) + 1:03d}", "ORIGIN": "CARRIED_FROM_S4",
                    "BASELINE_COMPONENT_ID": cid, "PORTION": "WHOLE_COMPONENT", "S4_1_STATE": state,
                    "OWNER": "S8 LIFT_PIT / SPECIAL_STRUCTURE" if state == DR.TRANSFERRED_OUT else "S4.1 FOOTING",
                    "WHAT_IS_MISSING": u["what_is_missing"], "QUESTION_ID": u["question_id"],
                    "SRD_ITEMS": srd_item_of(u),
                    "SOURCE_EXPECTED_NOT_LOCATED": "PENDING_ENGINEER" if u["mark"] in PENDING_ENGINEER else "YES",
                    "KNOWN_KG": float(u["known_kg"]) if u["known_kg"] else 0.0})
    for r in recs:
        if r["PORTION_STATE"] in (GE.SHAPE_FOUND_LENGTH_BLOCKED, GE.BLOCKED_UNQUANTIFIED) and \
                r["PORTION"] != "WHOLE_COMPONENT":
            item = {"BOTTOM_LONG": "S4-12", "BOTTOM_SHORT": "S4-13"}[r["COMPONENT"]]
            if r["FACETS"].get("END_TREATMENT", "").startswith("END_TREATMENT_NOT_ESTABLISHED (was"):
                item = "S4-14" if r["MARK"] != "FF" else "S4-11;S4-14"
            out.append({"UNRESOLVED_ID": f"S4.1-U{len(out) + 1:03d}", "ORIGIN": "NEW_IN_S4_1",
                        "BASELINE_COMPONENT_ID": r["BASELINE_COMPONENT_ID"], "PORTION": r["PORTION"],
                        "S4_1_STATE": r["PORTION_STATE"], "OWNER": "S4.1 FOOTING",
                        "WHAT_IS_MISSING": r["WHY"], "QUESTION_ID": "",
                        "SRD_ITEMS": item, "SOURCE_EXPECTED_NOT_LOCATED": "YES", "KNOWN_KG": 0.0})
    return out


CHANGELOG = """# S4.1 CHANGELOG: footing rebar delta release over frozen S4

**Round:** `S4.1` · **Policy:** `{policy}` · **Frozen baseline:** `{manifest}` (sha `{msha12}`, stamp `{stamp}`)
**Built by** `build_footing_rebar_s4_1.py` (blind, byte-identical rebuild) · **Graphic policy:** `GRAPHIC_EVIDENCE_POLICY_V1`

S4 is unchanged. Every S4 code, input and output hash was checked before this round read anything, and no S4 file
was written. This file is BASELINE + DELTA. It does not rewrite the historical S4 result.

## Headline

| | kg |
|---|---|
| Frozen S4 known (verified + lower bound) | {frozen_known:.4f} |
| S4.1 delta known | {delta:.4f} |
| **S4.1 known** | **{new_known:.4f}** |
| of which complete bars VERIFIED | {verified:.4f} (was {frozen_verified:.4f}) |
| of which complete bars LOWER_BOUND | {lower:.4f} |
| of which known straight segments of single-layer bars (former VERIFIED) | {kss:.4f} |

The delta is **0 kg** because no bar portion found in the issued set carries a dimension or a deterministic
project-source endpoint. The semantic corrections below are still real. A zero delta hides none of them.

## What changed (state and model; no kg)

1. **Single-layer long bars ({n_long} components): VERIFIED → KNOWN_STRAIGHT_SEGMENT, COMPLETE_BAR = LOWER_BOUND.**
   - p.13 draws "Long bars" as one U (E-PDF-01, both details). The model is now STRAIGHT_RUN + UPTURN_LEG_1/2 +
     END_HOOK_1/2 + BEND_ARC_1/2.
   - The frozen straight length stays known steel. It was not subtracted.
   - **Upturn legs:** `GRAPHIC_EXPLICIT_SHAPE_ONLY`, `SHAPE_FOUND_LENGTH_BLOCKED`. A derivation from footing depth D,
     the 70 mm cover and the bar levels was attempted. Rule B fails because the leg top is a free end, drawn
     {gap_s} / {gap_d} pt under the boxed bar's top run (shallow / deep detail). That point lies on no cover line and
     no dimensioned level, and the boxed bar's own level depends on its unlocated diameter. The plotted length was
     not used.
   - **45° hooks:** SHAPE_FOUND + LENGTH_BLOCKED.
   - **Bend arcs:** SHAPE_FOUND (shared vertex) + radius blocked.
2. **Single-layer short bars ({n_short} components): VERIFIED → KNOWN_STRAIGHT_SEGMENT, COMPLETE_BAR = LOWER_BOUND.**
   - They are drawn only as dots. The U shape is NOT copied onto them.
   - END_TREATMENT_1/2 are blocked (no graphic evidence).
3. **Two-layer bottom bars ({n_ftb} components): FACET_ADDED.** The "straight" basis is withdrawn, so these carry
   END_TREATMENT_NOT_ESTABLISHED. They stay LOWER_BOUND.
4. **BOXED ({n_boxed_facet} components): FACET_ADDED.**
   - {n_boxed_explicit} have EXISTENCE = SOURCE_FOUND_EXPLICIT (printed cell). For the 4 FN rows, existence is
     still SOURCE_EXPECTED_NOT_LOCATED (blank cell).
   - SHAPE = SOURCE_FOUND_EXPLICIT (inverted U).
   - The meaning of 3+n, the diameter and the count are not located, so BOXED_KG = BLOCKED_UNQUANTIFIED. No
     external diameter was used and "3+4" was not interpreted.
5. **FF "2 Ø16": OWNERSHIP_TRANSFER.**
   - FOOTING_CANDIDATE → LIFT_PIT / SPECIAL_STRUCTURE (future S8); see `S4_1_OWNERSHIP_TRANSFERS.csv`.
   - The leaders end on bars inside the cut pit-wall band, so these are wall-base bars, not footing reinforcement.
   - No kg.

Carried unchanged:
- F / F10 (pending the engineer, brief §20);
- the two-layer top bars (already END_TREATMENT_NOT_ESTABLISHED);
- {n_na} NOT_APPLICABLE components.

## Counts

- Delta rows: {n_rows}, covering every one of the {n_frozen} frozen components.
- Components by S4.1 state: {by_state}.
- Long-bar portions by state: {portions}.
- Remaining BOXED blocked: {boxed_blocked}
  - {n_boxed_explicit} existence explicit + shape found;
  - 4 FN existence not located;
  - 1 F / F10 pending.
- Transferred to S8: {n_transfer}.
- Unresolved register: {n_unres} rows ({n_unres_carried} carried from S4, {n_unres_new} new portion rows).

## Files

| File | Content |
|---|---|
| `S4_1_DELTA_COMPONENTS.csv` | one row per frozen component (or per portion of a re-modelled bar), with all brief §2 fields |
| `S4_1_RELEASE_SUMMARY.json` | baseline, delta and new totals, states, conservation, policy, flags |
| `S4_1_OWNERSHIP_TRANSFERS.csv` | FF wall-base bars → LIFT_PIT / SPECIAL_STRUCTURE |
| `S4_1_UNRESOLVED.csv` | carried S4 unresolved rows plus the new blocked portions |
| `S4_1_PROVENANCE.jsonl` | per delta row: frozen row, evidence ids, page / handles, graphic class, derivation attempt |
| `S4_1_FREEZE_MANIFEST.json` | S4.1 frozen before S6.1 |
"""


def main():
    frozen = DR.verify_frozen(S4 / "S4_FREEZE_MANIFEST.json", ROOT)
    ev = evidence()
    srd_items()
    reg = _j(S4 / "FOOTING_REBAR_OCCURRENCE_REGISTER.json")
    occ_by = {o["occurrence_id"]: o for o in reg["occurrences"]}
    s4 = _j(S4 / "FOOTING_REBAR_RELEASE_SUMMARY.json")
    frozen_known = s4["verified_kg"] + s4["lower_bound_known_kg"]
    comps, recs, prov, transfers = build(frozen, ev, occ_by)
    new_known = sum(r["NEW_KNOWN_QUANTITY"] for r in recs)
    cons = DR.conservation(frozen_known, recs, new_known)
    check(cons["all_pass"], f"conservation {cons}")
    check({r["BASELINE_COMPONENT_ID"] for r in recs} == {f"{c['occurrence_id']}:{c['component']}" for c in comps},
          "every frozen component appears in the delta")

    comp_state = {}
    for r in recs:
        comp_state.setdefault(r["BASELINE_COMPONENT_ID"], r["NEW_RELEASE_STATE"])
    by_state = dict(sorted(Counter(comp_state.values()).items()))
    old_state = {f"{c['occurrence_id']}:{c['component']}": c["state"] for c in comps}
    transitions = Counter(f"{old_state[k]} -> {v}" for k, v in comp_state.items() if old_state[k] != v)
    kind_by_comp = {}
    for r in recs:
        kind_by_comp.setdefault(r["BASELINE_COMPONENT_ID"], set()).add(r["CHANGE_KIND"])
    long_rows = [r for r in recs if r["COMPONENT"] == "BOTTOM_LONG" and r["PORTION"] != "WHOLE_COMPONENT"]
    portions = dict(sorted(Counter(f"{r['PORTION']}:{r['PORTION_STATE']}" for r in long_rows).items()))
    kss = sum(r["NEW_KNOWN_QUANTITY"] for r in recs if r["PORTION_STATE"] == GE.KNOWN_STRAIGHT_SEGMENT
              and r["OLD_STATE"] == "VERIFIED")
    verified = sum((r["NEW_KNOWN_QUANTITY"] for r in recs if r["NEW_RELEASE_STATE"] == DR.VERIFIED), 0.0)
    lower = sum(r["NEW_KNOWN_QUANTITY"] for r in recs if r["NEW_RELEASE_STATE"] == DR.LOWER_BOUND)
    boxed = [r for r in recs if r["COMPONENT"] == "BOXED"]
    boxed_blocked = sum(1 for r in boxed if r["NEW_RELEASE_STATE"] == DR.BLOCKED_UNQUANTIFIED)
    boxed_facet = [r for r in boxed if r["CHANGE_KIND"] == DR.FACET_ADDED]
    boxed_explicit = [r for r in boxed_facet if r["FACETS"]["EXISTENCE"].startswith("SOURCE_FOUND_EXPLICIT")]
    by_acc = {}
    for r in recs:
        if r["NEW_KNOWN_QUANTITY"]:
            d = by_acc.setdefault(r["ACCURATE_COMPONENT"], {})
            d[r["NEW_RELEASE_STATE"]] = d.get(r["NEW_RELEASE_STATE"], 0.0) + r["NEW_KNOWN_QUANTITY"]
    unres = unresolved(recs)
    n_long = sum(1 for k, v in comp_state.items() if k.endswith(":BOTTOM_LONG") and old_state[k] == "VERIFIED")
    n_short = sum(1 for k, v in comp_state.items() if k.endswith(":BOTTOM_SHORT") and old_state[k] == "VERIFIED")
    n_ftb = sum(1 for k, kinds in kind_by_comp.items() if DR.FACET_ADDED in kinds and ":BOTTOM_" in k)

    ctx = {"ROUND": ROUND, "POLICY": POLICY, "ENGINE_COMMIT": f"{frozen['engine_commit_stamp']}+delta:"
                                                             f"{code_digest()[:16]}",
           "FROZEN_BASELINE": frozen, "PDF_SHA": PDF_SHA}
    summary = {
        "round": ROUND, "policy": POLICY, "context": ctx, "graphic_evidence_policy": GE.policy_record(),
        "frozen_s4": {"verified_kg": s4["verified_kg"], "lower_bound_known_kg": s4["lower_bound_known_kg"],
                      "known_kg": frozen_known, "components_by_state": s4["components_by_state"]},
        "delta_known_kg": cons["delta_known"], "s4_1_known_kg": new_known,
        "s4_1_complete_bar_kg": {"VERIFIED": verified, "LOWER_BOUND": lower},
        "s4_1_known_straight_segment_kg_formerly_verified": kss,
        "s4_1_kg_by_component_and_state": by_acc,
        "s4_1_components_by_state": by_state, "state_transitions": dict(sorted(transitions.items())),
        "state_only_changes": {"VERIFIED_to_LOWER_BOUND_long": n_long, "VERIFIED_to_LOWER_BOUND_short": n_short,
                               "two_layer_bottom_end_treatment_facet": n_ftb,
                               "boxed_shape_facet": len(boxed_facet), "ownership_transfers": len(transfers)},
        "long_bar_portions": portions,
        "boxed": {"blocked": boxed_blocked, "existence_explicit_shape_found": len(boxed_explicit),
                  "fn_existence_not_located": len(boxed_facet) - len(boxed_explicit),
                  "pending_engineer": boxed_blocked - len(boxed_facet), "boxed_kg": DR.BLOCKED_UNQUANTIFIED},
        "transfers_to_s8": [t["BASELINE_COMPONENT_ID"] for t in transfers],
        "unresolved": {"rows": len(unres), "carried_from_s4": sum(1 for u in unres if u["ORIGIN"] ==
                                                                  "CARRIED_FROM_S4"),
                       "new_portion_rows": sum(1 for u in unres if u["ORIGIN"] == "NEW_IN_S4_1")},
        "delta_rows": len(recs), "frozen_components": len(comps), "conservation": cons,
        "evidence": {"leg_top_gap_to_boxed_run_pt": {k: v["leg_top_gap_to_boxed_run_pt"]
                                                     for k, v in ev["E-PDF-01"].items()}},
        "flags": {"frozen_outputs_changed": False, "plotted_scale_used": False, "kg_from_shape_only_graphic": False,
                  "verified_created": False, "pre_s7_started": False, "references_read": []},
        "headline": "S4.1 KNOWN FOOTING REBAR = FROZEN S4 KNOWN + 0 (state corrections only)"}

    fields = ["DELTA_ID", "CHANGE_KIND", "FROZEN_BASELINE", "BASELINE_COMPONENT_ID", "OCCURRENCE_ID", "MARK",
              "COMPONENT", "ACCURATE_COMPONENT", "PORTION", "OLD_STATE", "OLD_KNOWN_QUANTITY", "NEW_PROJECT_SOURCE",
              "SOURCE_PAGE", "SOURCE_HANDLES", "GRAPHIC_EVIDENCE_CLASS", "NEW_COMPONENT_MODEL", "PORTION_STATE",
              "QUANTITY_BASIS", "DELTA_KNOWN_QUANTITY", "NEW_KNOWN_QUANTITY", "NEW_BLOCKED_COMPONENTS",
              "NEW_RELEASE_STATE", "COMPLETE_BAR", "DIA_MM", "COUNT", "FROZEN_NET_STRAIGHT_MM", "FACETS",
              "EVIDENCE_IDS", "WHY"]
    _csv(HERE / "S4_1_DELTA_COMPONENTS.csv", recs, fields)
    _csv(HERE / "S4_1_OWNERSHIP_TRANSFERS.csv", transfers, list(transfers[0].keys()))
    _csv(HERE / "S4_1_UNRESOLVED.csv", unres, list(unres[0].keys()))
    with open(HERE / "S4_1_PROVENANCE.jsonl", "w", encoding="utf-8") as f:
        for p in prov:
            f.write(json.dumps(p, sort_keys=True, ensure_ascii=False) + "\n")
    _json(HERE / "S4_1_RELEASE_SUMMARY.json", summary)
    (HERE / "S4_1_CHANGELOG.md").write_text(CHANGELOG.format(
        policy=POLICY, manifest=frozen["manifest"], msha12=frozen["manifest_sha256"][:12],
        stamp=frozen["engine_commit_stamp"], frozen_known=frozen_known, delta=cons["delta_known"],
        new_known=new_known, verified=verified, frozen_verified=s4["verified_kg"], lower=lower, kss=kss,
        n_long=n_long, n_short=n_short, n_ftb=n_ftb, n_boxed_facet=len(boxed_facet),
        n_boxed_explicit=len(boxed_explicit), gap_s=ev["E-PDF-01"]["SHALLOW"]["leg_top_gap_to_boxed_run_pt"],
        gap_d=ev["E-PDF-01"]["DEEP"]["leg_top_gap_to_boxed_run_pt"],
        n_na=by_state.get("NOT_APPLICABLE", 0), n_rows=len(recs), n_frozen=len(comps),
        by_state=", ".join(f"{k} {v}" for k, v in by_state.items()),
        portions=", ".join(f"{k} {v}" for k, v in portions.items()), boxed_blocked=boxed_blocked,
        n_transfer=len(transfers), n_unres=len(unres), n_unres_carried=summary["unresolved"]["carried_from_s4"],
        n_unres_new=summary["unresolved"]["new_portion_rows"]), encoding="utf-8")
    manifest = {"round": ROUND, "state": "FROZEN_BEFORE_S6_1", "baseline_round": "S4",
                "frozen_baseline": frozen, "code": {c: _sha(ROOT / c) for c in CODE},
                "inputs": {i: _sha(ROOT / i) for i in INPUTS}, "outputs": {o: _sha(HERE / o) for o in OUTPUTS},
                "engine_commit_stamp": ctx["ENGINE_COMMIT"], "references_read_before_freeze": [],
                "rule": "S4.1 is a delta over frozen S4; a correction needs a new delta round, never an edit of S4 "
                        "or of these outputs"}
    _json(HERE / "S4_1_FREEZE_MANIFEST.json", manifest)
    print(json.dumps({k: summary[k] for k in ("delta_known_kg", "s4_1_known_kg", "s4_1_complete_bar_kg",
                                              "s4_1_components_by_state", "state_only_changes", "boxed",
                                              "transfers_to_s8", "unresolved")}, indent=1))


if __name__ == "__main__":
    main()
