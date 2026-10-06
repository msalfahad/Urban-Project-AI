"""Alsenan / ST7757 adapter for the generic S2 review engine (engineering flags, authority, claims, questions).

    python research/alsenan_structural_s2/build_flags_s2.py

Reads the FROZEN S1 census registers only (sha256 checked against the S1 INDEX), maps them into the generic REVIEW
VIEW (engine.source.flag_detectors), and runs the generic engine. Project facts live here and in the outputs; the
engine modules stay project-free. The S1 census is not modified and no reinforcement weight is calculated.
"""
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
S1 = ROOT / "research" / "alsenan_structural_census_s1"
sys.path.insert(0, str(ROOT))

from engine.source import engineering_flags as EF  # noqa: E402
from engine.source import flag_detectors as FD  # noqa: E402
from engine.source import project_claims as PC  # noqa: E402
from engine.source import question_helper as QH  # noqa: E402
from engine.source import rule_promotion as RP  # noqa: E402
from engine.source import structural_authority as SA  # noqa: E402

PROJECT_ID = "ALSENAN-ST7757"
REVISION = "ST7757.dxf sha256 9f9d1179 (S1 frozen census)"
DRAWING = "ST7757.dxf"
SHEETS = {"CAP": ("COLUMN & AXIS PLAN", 1), "FP": ("FOUNDATION PLAN", 2), "GBP": ("GROUND BEAMS PLAN", 3),
          "GFRS": ("GROUND FLOOR ROOF SLAB", 4), "FFRS": ("FIRST FLOOR ROOF SLAB", 5),
          "SFRS": ("SECOND FLOOR ROOF SLAB", 6), "DET": ("DETAILS (pool / dome)", 7)}
SCHED_PAGE = {"COLUMN": 9, "FOOTING": 9, "SIMPLE_BEAM": 10, "STRAP_BEAM": 10, "CONTINUOUS_BEAM": 11}
FLOOR_SHEET = {"GF_ROOF": "GFRS", "1F_ROOF": "FFRS", "2F_ROOF": "SFRS", "GROUND_BEAMS": "GBP", "FOUNDATION": "FP",
               "GF_ROOF_SLAB": "GFRS", "1F_ROOF_SLAB": "FFRS", "2F_ROOF_SLAB": "SFRS", "GROUND_SLAB_SOG": "GBP"}


def load_s1():
    idx = json.loads((S1 / "INDEX.json").read_text(encoding="utf-8"))
    regs = {}
    for name, v in idx["registers"].items():
        raw = (S1 / v["file"]).read_bytes()
        if hashlib.sha256(raw).hexdigest() != v["sha256"]:
            raise SystemExit(f"S1 register {name} does not match its frozen hash")
        regs[name] = json.loads(raw)
    return idx, regs


def ref(sheet=None, *, page=None, handle=None, text=None, layer=None, xy=None, title=None):
    t, p = SHEETS.get(sheet, (title, page))
    r = {"drawing": DRAWING if not page or page <= 7 or sheet else "ST7757.pdf", "sheet_title": title or t,
         "page": page or p}
    if handle:
        r["handle"] = str(handle).split(">")[0].split(":")[0]
    if text:
        r["text"] = text
    if layer:
        r["layer"] = layer
    if xy:
        r["xy_mm"] = [round(xy[0]), round(xy[1])]
    return r


def sched_ref(kind, row_handle=None, key=None):
    return {"drawing": "ST7757.dxf / ST7757.pdf", "sheet_title": f"schedule ({kind.lower().replace('_', ' ')})",
            "page": SCHED_PAGE.get(kind), **({"handle": row_handle} if row_handle else {}),
            **({"text": key} if key else {})}


def rule_ref(r):
    out = {"drawing": "ST7757.pdf", "sheet_title": f"rule {r['rule_id']}", "page": r["page"]}
    if r.get("dxf_handles"):
        out["handle"] = r["dxf_handles"][0]
    return out


# ============================================================================================ S1 -> generic view
def build_view(regs):
    occ = regs["COLUMN_OCCURRENCE_REGISTER"]["rows"]
    chains = regs["COLUMN_VERTICAL_CHAIN_REGISTER"]["rows"]
    cdef = regs["COLUMN_DEFINITION_REGISTER"]["rows"]
    rules = {r["rule_id"]: r for r in regs["STRUCTURAL_PROJECT_RULE_REGISTER"]["rows"]}
    occ_by_chain = defaultdict(list)
    for r in occ:
        occ_by_chain[r["chain_id"]].append(r)
    fou = {d["column_type"]: d for d in cdef if d["storey_band"] == "FOUNDATION" and d.get("B_cm")}
    V = {"project_id": PROJECT_ID, "drawing_revision": REVISION, "discipline": "STRUCTURAL"}

    # ---- member type evidence (every chain with plan tags)
    te = []
    for ch in chains:
        if len(ch["tags_by_plan"]) < 2:
            continue
        evid = []
        for sh, t in ch["tags_by_plan"].items():
            evid.append({"value": t["tag"], "authority": SA.PLAN_MEMBER_TAG, "description": f"{SHEETS[sh][0]} tag",
                         "source_ref": ref(sh, handle=t["handle"], text=t["tag"], layer="S-TEXT")})
        size = ch.get("axis_plan_size_label")
        if size:
            b, d = sorted(int(v) for v in size.upper().split("X"))
            fits = [t for t, dd in fou.items() if sorted([dd["B_cm"], dd["D_cm"]]) == [b, d]]
            cand = sorted({e["value"] for e in evid})
            fits = [t for t in fits if t in cand]
            if len(fits) == 1:
                evid.append({"value": fits[0], "authority": SA.DRAWN_GEOMETRY,
                             "description": f"axis-plan size label {size} matches the {fits[0]} schedule section",
                             "source_ref": ref("CAP", text=size, layer="S-TEXT")})
        ids = [r["column_id"] for r in occ_by_chain[ch["chain_id"]]]
        te.append({"element_type": "COLUMN", "element_id": ch["chain_id"], "element_ids": ids,
                   "label": f"at grid {ch['grid']['X']}/{ch['grid']['Y']}", "evidence": evid,
                   "current": {"value": ch["column_type"], "authority": ch["type_authority"]},
                   "definitions": {t: {"section": sorted([fou[t]["B_cm"], fou[t]["D_cm"]]),
                                       "reinforcement": fou[t]["longitudinal_bars"]}
                                   for t in {e["value"] for e in evid} if t in fou},
                   "quantity": len(ids), "unit": "nr occurrences"})
    V["type_evidence"] = te

    # ---- section evidence (drawn outline vs schedule) - columns and beams
    se = []
    for r in occ:
        if r["drawn_vs_schedule"] != "MISMATCH" or not r["schedule_section_cm"]:
            continue
        sh = r["plan_source"]["sheets"][0]
        se.append({"element_type": "COLUMN", "element_id": r["column_id"], "member_type": r["column_type"],
                   "floor": r["floor"], "tol": 2.5, "quantity": 1, "unit": "nr occurrences",
                   "evidence": [{"value": sorted(r["schedule_section_cm"]), "authority": SA.MEMBER_SCHEDULE,
                                 "description": "schedule section (storey band)",
                                 "source_ref": sched_ref("COLUMN", key=r["column_type"])},
                                {"value": sorted(r["drawn_section_cm"]), "authority": SA.DRAWN_GEOMETRY,
                                 "description": "drawn outline",
                                 "source_ref": ref(sh, handle=r["plan_source"]["handles"][0], layer="S-COL.BON",
                                                   xy=r["plan_centre_mm"])}]})
    beams = regs["BEAM_OCCURRENCE_REGISTER"]["rows"]
    for b in beams:
        if "DRAWN_WIDTH_DIFFERS_FROM_SCHEDULE" in b["issues"] and b["family"] != "STRAP" and b.get("schedule_B_cm"):
            se.append({"element_type": "BEAM", "element_id": b["beam_id"], "member_type": b["beam_type"],
                       "floor": b["floor"], "tol": 2.5, "quantity": b.get("support_centreline_length_m"),
                       "unit": "m beam", "evidence": [
                           {"value": b["schedule_B_cm"], "authority": SA.MEMBER_SCHEDULE,
                            "description": "schedule width (cm)", "source_ref": sched_ref("SIMPLE_BEAM",
                                                                                         key=b["beam_type"])},
                           {"value": round(b["width_drawn_mm"] / 10, 1), "authority": SA.DRAWN_GEOMETRY,
                            "description": "drawn width (cm)",
                            "source_ref": ref(b["sheet"], handle=b.get("tag_handle"), text=b["beam_type"],
                                              xy=b.get("tag_position_mm"))}]})
    V["section_evidence"] = se

    # ---- tie band lookups
    ties = regs["COLUMN_TIE_TOPOLOGY_RULES"]
    lim = {b["band_id"]: b for b in ties.get("band_limits", [])}
    bands = [{"band_id": b["band_id"], "description": b["printed_condition"],
              "lo": (lim.get(b["band_id"]) or {}).get("lo"), "hi": (lim.get(b["band_id"]) or {}).get("hi")}
             for b in ties["rows"]]
    tie_ref = ref(title="DETAILS OF COLUMN REINFORCEMENT (schedule sheet)", page=9, handle="1BAA",
                  text="ST. OF COLUMN- 6%%c8/m")
    V["band_lookups"] = [{"element_type": "COLUMN", "element_id": r["column_id"], "member_type": r["column_type"],
                          "rule_ref": "P9-COL-BAND", "rule_text": "column tie rule (arrangement by long side L)",
                          "value": max(r["schedule_section_cm"]), "value_unit": "cm",
                          "state": r["tie_topology_band"]["state"], "bands": bands, "quantity": 1,
                          "unit": "nr occurrences", "source_refs": [tie_ref]}
                         for r in occ if r["schedule_section_cm"]
                         and r["tie_topology_band"]["state"] not in ("EXACT_RULE",)]
    # ---- per-metre tie semantics + tie zone
    by_band = defaultdict(list)
    for r in occ:
        b = r["tie_topology_band"].get("band")
        if isinstance(b, str):
            by_band[b].append(r["column_id"])
    zone_states = {i.get("tie_zone_status") for i in regs["STRUCTURAL_LEVEL_REGISTER"]["intervals"]
                   if i["storey"] != "FOUNDATION"}
    V["transverse_rules"] = [{
        "element_type": "COLUMN", "rule_ref": "P9-COL-TIES", "rule_text": "ST. OF COLUMN- 6Ø8/m (column ties)",
        "per_metre": True, "element_ids": [r["column_id"] for r in occ],
        "zone_length_state": "ESTABLISHED" if zone_states == {"ESTABLISHED"} else "NOT_ESTABLISHED",
        "bands": [{"band_id": b["band_id"], "closed_ties_per_set": b["closed_ties_in_section"],
                   "element_ids": by_band.get(b["band_id"], [])} for b in ties["rows"]],
        "source_refs": [tie_ref]}]
    # ---- schedule bars vs detail sketch
    dc = []
    for d in cdef:
        lt = d.get("link_topology") or {}
        if lt.get("bars_in_schedule_vs_detail") == "DIFFERENT_COUNT_DISTRIBUTION_BLOCKED":
            ids = [r["column_id"] for r in occ if r["column_type"] == d["column_type"] and r["floor"] == d["storey_band"]]
            if ids:
                dc.append({"element_type": "COLUMN", "member_type": f"{d['column_type']} ({d['storey_band']})",
                           "band_id": lt["band"], "schedule_count": d["longitudinal_bars"]["count"],
                           "detail_count": lt["bars_drawn_in_detail"], "element_ids": ids, "source_refs": [tie_ref]})
    V["detail_count_mismatches"] = dc
    # ---- Tmin shortfalls
    tmin = rules["P9-COL-TMIN"]
    V["minimum_checks"] = [{"element_type": "COLUMN", "element_id": r["column_id"], "member_type": r["column_type"],
                            "floor": r["floor"], "rule_ref": "P9-COL-TMIN",
                            "rule_text": "minimum column thickness for the storey height (p.9)",
                            "required": r["min_thickness_check"]["t_min_cm"], "provided": min(r["schedule_section_cm"]),
                            "unit_value": "cm", "quantity": 1, "unit": "nr occurrences",
                            "source_refs": [rule_ref(tmin)]}
                           for r in occ if r["min_thickness_check"] and
                           r["min_thickness_check"]["state"].startswith("BELOW_MINIMUM")]
    # ---- single-level members and presence gaps
    sl = defaultdict(list)
    for ch in chains:
        if ch["continues_through"] == ["FOUNDATION"]:
            sl[ch["column_type"]].append(ch)
    peers = any(len(ch["continues_through"]) > 1 for ch in chains)
    V["single_level_members"] = [{"element_type": "COLUMN", "member_type": t, "level": "FOUNDATION",
                                  "element_ids": [o["column_id"] for c in lst for o in occ_by_chain[c["chain_id"]]],
                                  "peers_continue": peers, "quantity": len(lst), "unit": "nr occurrences",
                                  "source_refs": [ref("FP", text=t), sched_ref("COLUMN", key=t)]}
                                 for t, lst in sorted(sl.items())]
    pg = []
    for ch in chains:
        if any(e["event"] in ("GAP_IN_CHAIN", "MISSING_ON_AXIS_PLAN") for e in ch["events"]):
            present = [s for s in ("FP", "CAP", "GBP") if s in ch["members_by_sheet"]]
            missing = [s for s in ("FP", "CAP", "GBP") if s not in ch["members_by_sheet"]]
            ids = [o["column_id"] for o in occ_by_chain[ch["chain_id"]]]
            pg.append({"element_type": "COLUMN", "element_id": ch["chain_id"], "label": f"{ch['column_type']}",
                       "present_on": [SHEETS[s][0] for s in present], "missing_on": [SHEETS[s][0] for s in missing],
                       "quantity": len(ids), "unit": "nr occurrences",
                       "source_refs": [ref(s, handle=ch["members_by_sheet"][s]) for s in present]})
    V["presence_gaps"] = pg

    # ---- footings
    fo = regs["FOOTING_OCCURRENCE_REGISTER"]
    V["competing_tags"] = [{"element_type": "FOOTING", "element_id": r["footing_id"],
                            "candidates": r["candidate_types"], "quantity": 1, "unit": "nr",
                            "context": f"one outline holding columns {', '.join(r['supported_column_types'])}",
                            "source_refs": [ref("FP", handle=r["outline"]["handle"], layer="S-FOOTINGS")]
                            + [ref("FP", handle=t["handle"], text=t["text"]) for t in [r["tag"]] + r["competing_tags"]]}
                           for r in fo["rows"] if r.get("competing_tags")]
    # same beam span carrying two marks
    same = defaultdict(list)
    for b in beams:
        if "SAME_SPAN_CARRIES_TWO_TAGS" in b["issues"]:
            same[(b["sheet"], b["member"], tuple(b.get("span_stations_mm") or []))].append(b)
    for (sh, m, _), lst in sorted(same.items()):
        V["competing_tags"].append({"element_type": "BEAM", "element_id": "+".join(x["beam_id"] for x in lst),
                                    "candidates": [x["beam_type"] for x in lst], "quantity": lst[0].get(
                                        "support_centreline_length_m"), "unit": "m beam",
                                    "context": "both marks sit on the same drawn span",
                                    "source_refs": [ref(sh, handle=x["tag_handle"], text=x["beam_type"],
                                                        xy=x.get("tag_position_mm")) for x in lst]})
    fdefs = regs["FOOTING_DEFINITION_REGISTER"]["rows"]
    boxed = {d["footing_type"]: d["boxed"]["raw_boxed_value"] for d in fdefs
             if d["element"] == "FOOTING" and d["boxed"].get("raw_boxed_value")}
    fids = [r["footing_id"] for r in fo["rows"] if r["type"] in boxed or set(r.get("candidate_types") or []) & set(boxed)]
    V["unresolved_semantics"] = [{"element_type": "FOOTING", "field": "BOXED", "member_types": sorted(boxed),
                                  "raw_values": dict(sorted(boxed.items())), "element_ids": fids,
                                  "quantity": len(fids), "unit": "nr",
                                  "meaning_options": [
                                      {"answer": "box / cage bars: a + b bars in the two directions",
                                       "effect": "extra bar set per footing"},
                                      {"answer": "top mesh counts", "effect": "a top layer is added"},
                                      {"answer": "column starter / dowel count", "effect": "starter bars only"}],
                                  "source_refs": [sched_ref("FOOTING", key="BOXED")]}]
    V["geometry_overlaps"] = [{"element_type": "FOOTING", "element_ids": m["footings"], "overlap": m["overlap_m2"],
                               "overlap_unit": "m2 plan", "source_refs": [ref("FP", handle=f.split(":")[1])
                                                                          for f in m["footings"]]}
                              for m in fo["mismatches"] if m["kind"] == "FOOTING_OUTLINES_OVERLAP"]
    # ---- schedule key duplicates
    straps = [b for b in beams if b["family"] == "STRAP"]
    dd = []
    for c in regs["BEAM_DEFINITION_REGISTER"]["conflicts"]:
        ids = [b["beam_id"] for b in beams if b.get("beam_type") == c["key"]]
        hint = None
        for b in straps:
            if b["beam_type"] == c["key"] and b.get("drawn_width_matches"):
                hint = (f"drawn width {b['width_drawn_mm']:.0f} mm fits B = {b['drawn_width_matches'][0]:g} cm "
                        f"(geometry hint only, not applied)")
        dd.append({"element_type": "BEAM", "key": c["key"], "schedule_ref": "SBT",
                   "variants": [{"row": r, "values": {k: v for k, v in var.items() if k != "BEAM"}}
                                for r, var in zip(c["rows"], c["variants"])],
                   "element_ids": ids, "geometry_hint": hint, "quantity": sum(
                       b.get("drawn_length_m") or 0 for b in beams if b["beam_id"] in ids) or None, "unit": "m beam",
                   "source_refs": [sched_ref("STRAP_BEAM", r, c["key"]) for r in c["rows"]]})
    V["duplicate_definitions"] = dd
    # ---- continuous beams
    V["span_matches"] = [{"element_type": "BEAM", "element_id": c["cb_id"], "member_type": c["type"],
                          "floor": c["floor"], "schedule_spans": c["schedule_spans_m"],
                          "plan_spans": [s["cc_m"] for s in c["plan_spans"]], "state": c["match_state"],
                          "extension": (c["extension_check"] or {}).get("extended_spans_cc_m"),
                          "quantity": round(sum(s["cc_m"] for s in c["plan_spans"]), 3), "unit": "m beam",
                          "source_refs": [ref(c["sheet"], handle=t["handle"], text=c["type"]) for t in c["tags"]]
                          + [sched_ref("CONTINUOUS_BEAM", c["schedule_row"], c["type"])]}
                         for c in regs["CONTINUOUS_BEAM_OCCURRENCE_REGISTER"]["rows"]]
    # ---- beam bindings / untagged / GB basis / curved
    V["ambiguous_bindings"] = [{"element_type": "BEAM", "element_id": b["beam_id"], "floor": b["floor"],
                                "tag": b["beam_type"], "candidates": b.get("member_candidates") or [],
                                "source_refs": [ref(b["sheet"], handle=b["tag_handle"], text=b["beam_type"],
                                                    xy=b.get("tag_position_mm"))]}
                               for b in beams if "TAG_MEMBER_AMBIGUOUS" in b["issues"]]
    V["untyped_members"] = [{"element_type": "BEAM", "element_id": b["beam_id"], "floor": b["floor"],
                             "family": "dome ring (curved)" if b["family"] == "DOME_RING" else "no mark",
                             "quantity": b.get("support_centreline_length_m") or b.get("drawn_length_m"),
                             "unit": "m beam", "source_refs": [ref(b["sheet"], layer="1")]}
                            for b in beams if b.get("binding") == "NO_TAG"]
    V["basis_dependent_class"] = [{"element_type": "BEAM", "element_id": b["beam_id"], "floor": b["floor"],
                                   "rule_ref": "P13 ground-beam typical details (<2.5 / <5 / >5 m)",
                                   "class_by_basis": {"centre-to-centre": b["beam_type"],
                                                      "clear span": b.get("category_clear_basis")},
                                   "quantity": b.get("support_centreline_length_m"), "unit": "m beam",
                                   "source_refs": [ref("GBP", layer="1"), {"drawing": "ST7757.pdf",
                                                                          "sheet_title": "ground beam details",
                                                                          "page": 13}]}
                                  for b in beams if b.get("category_state") == "AMBIGUOUS_LENGTH_BASIS"]
    bg = [{"element_type": "BEAM", "element_id": b["beam_id"], "floor": b["floor"],
           "reason": "curved ground-beam span - support length not measured", "quantity": b.get("drawn_length_m"),
           "unit": "m beam", "question": "Confirm the curved ground beam's supports and length (pool edge).",
           "source_refs": [ref("GBP", layer="1")]} for b in beams if b.get("category_state") == "BLOCKED_CURVED_SPAN"]
    sp = regs["SPECIAL_STRUCTURAL_OCCURRENCE_REGISTER"]["rows"]
    for s in sp:
        if s["kind"] == "PARAPET":
            bg.append({"element_type": "PARAPET", "element_id": s["special_id"], "floor": s["floor"],
                       "reason": "parapet height / length follow the architectural drawings (not on the structural set)",
                       "question": "Give the parapet height and the roof edges that carry a parapet.",
                       "source_refs": [ref(FLOOR_SHEET.get(s["floor"], "GFRS"), text=s.get("raw"))]})
    bg.append({"element_type": "POOL", "element_id": "SPC-POOL", "floor": "GROUND",
               "reason": "pool lengths and depths are 'AS PER ARCH' on the detail",
               "question": "Provide the pool plan and section (lengths, depths, slope) from the architect.",
               "source_refs": [ref("DET", text="DETAIL OF SWIMMING POOL"), ref("GBP", text="swimming pool")]})
    V["blocked_geometry"] = bg
    # ---- required by rule but not drawn
    rnd = []
    for b in beams:
        if b["family"] in ("LIFT_TIE", "LINTEL"):
            r = rules["P8-N19"] if b["family"] == "LIFT_TIE" else rules["P13-LINTEL"]
            rnd.append({"element_type": "LIFT_TIE_BEAM" if b["family"] == "LIFT_TIE" else "LINTEL",
                        "element_id": b["beam_id"], "floor": b["floor"], "rule_ref": r["rule_id"],
                        "rule_text": r["english_interpretation"],
                        "condition": "storey height > 4.30 m" if b["family"] == "LIFT_TIE" else
                        "one lintel per architectural opening, type by opening width",
                        "source_refs": [rule_ref(r)]})
    V["required_not_drawn"] = rnd
    # ---- rule-dependent populations
    panels = regs["SLAB_PANEL_REGISTER"]["rows"]

    def area(lst):
        return round(sum(p["area_m2"] for p in lst), 3)
    stairs = [p for p in panels if p["class"] in ("STAIR_FLIGHT_ZONE", "STAIR_IN_VOID_ZONE")]
    gs = [p for p in panels if p["sheet"] == "GBP" and p["class"] == "SLAB_PANEL"]
    domes = [p for p in panels if p["class"] == "DOME_ZONE"]
    rde = [
        {"element_type": "STAIR", "element_ids": [p["panel_id"] for p in stairs], "rule_ref": "P16-STAIR",
         "rule_text": rules["P16-STAIR"]["english_interpretation"], "rule_status": rules["P16-STAIR"]["status"],
         "gap_kind": "APPLICABILITY", "quantity": area(stairs), "unit": "m2 plan",
         "affected_facts": ["detailing", "geometry"],
         "question": "Does the typical stair detail (p.16) apply to each stair on the plans, including the stair "
                     "inside the void? Please give flight / landing levels and waist thickness.",
         "options": [{"answer": "typical detail applies", "effect": "stair bars from p.16 per flight"},
                     {"answer": "stair-specific detail", "effect": "needs the stair drawing"}],
         "source_refs": [rule_ref(rules["P16-STAIR"])] + [ref(p["sheet"]) for p in stairs[:1]]},
        {"element_type": "GROUND_SLAB", "element_ids": [p["panel_id"] for p in gs], "rule_ref": "P3-GROUND-SLAB",
         "rule_text": rules["P3-GROUND-SLAB"]["english_interpretation"],
         "rule_status": rules["P3-GROUND-SLAB"]["status"], "gap_kind": "EXTENT", "quantity": area(gs),
         "unit": "m2 plan", "affected_facts": ["extent"], "release_effect": EF.LOWER_BOUND,
         "question": "Which areas receive the 10 cm ground slab (5Ø10/m each way): every cell inside the ground "
                     "beams, or only the cells marked with the note?",
         "options": [{"answer": "all cells inside the building", "effect": f"{area(gs)} m2 plan"},
                     {"answer": "only marked cells", "effect": "smaller area"}],
         "source_refs": [rule_ref(rules["P3-GROUND-SLAB"])]},
        {"element_type": "DOME", "element_ids": [p["panel_id"] for p in domes], "rule_ref": "P7-DOME",
         "rule_text": rules["P7-DOME"]["english_interpretation"], "rule_status": rules["P7-DOME"]["status"],
         "gap_kind": "APPLICABILITY", "quantity": area(domes), "unit": "m2 plan", "affected_facts": ["section"],
         "release_effect": EF.PROVISIONAL_VALUE,
         "question": "Does the dome detail (100 mm shell, ring beam) apply to both domes on the first-floor roof?",
         "options": [{"answer": "yes", "effect": "dome zones use 100 mm"}, {"answer": "no", "effect": "per answer"}],
         "source_refs": [ref("DET", text="DETAIL OF DOME"), ref("FFRS", text="SEE DETAIL")]},
    ]
    lift = [s for s in sp if s["kind"] == "LIFT_PIT"]
    if lift:
        rde.append({"element_type": "LIFT_PIT", "element_ids": [s["special_id"] for s in lift], "rule_ref": "P14-LIFT",
                    "rule_text": rules["P14-LIFT"]["english_interpretation"],
                    "rule_status": rules["P14-LIFT"]["status"], "gap_kind": "DIMENSION",
                    "affected_facts": ["geometry"],
                    "question": "What is the lift-pit depth below the lift footing (manufacturer / engineer)?",
                    "options": [{"answer": "depth given", "effect": "pit walls measured"}],
                    "source_refs": [rule_ref(rules["P14-LIFT"])]})
    planted = [s for s in sp if s["kind"] in ("PLANTED_COLUMN", "TURN_COLUMN")]
    for kind, rid in (("PLANTED_COLUMN", "P15-PLANTED"), ("TURN_COLUMN", "P15-TWISTED")):
        lst = [s for s in planted if s["kind"] == kind]
        if lst:
            rde.append({"element_type": kind, "element_ids": [s["special_id"] for s in lst], "rule_ref": rid,
                        "rule_text": rules[rid]["english_interpretation"], "rule_status": rules[rid]["status"],
                        "gap_kind": "APPLICABILITY", "affected_facts": ["detailing"],
                        "release_effect": EF.LOWER_BOUND,
                        "question": f"Does the p.15 detail ({rules[rid]['english_interpretation']}) apply to each of "
                                    f"these columns, and do they use the normal tie bands?",
                        "options": [{"answer": "yes", "effect": "detail extras added"},
                                    {"answer": "no", "effect": "plain column only"}],
                        "source_refs": [rule_ref(rules[rid])]})
    footing_ids = [r["footing_id"] for r in fo["rows"]]
    rde.append({"element_type": "FOOTING", "element_ids": footing_ids, "rule_ref": "P13-FOOTING-DEEP",
                "rule_text": rules["P13-FOOTING-DEEP"]["english_interpretation"],
                "rule_status": rules["P13-FOOTING-DEEP"]["status"], "gap_kind": "DIMENSION",
                "affected_facts": ["lower_ground_beam"], "quantity": len(footing_ids), "unit": "nr",
                "question": "What is the founding level? (A lower ground beam is required where the ground beam is "
                            "more than 2.5 m above the footing.)",
                "options": [{"answer": "difference <= 2.5 m", "effect": "no lower ground beam"},
                            {"answer": "difference > 2.5 m", "effect": "lower ground beams added"}],
                "source_refs": [rule_ref(rules["P13-FOOTING-DEEP"]), rule_ref(rules["P9-SOIL"])]})
    slab_beams = [b for b in beams if b["floor"] in ("GF_ROOF", "1F_ROOF", "2F_ROOF") and b.get("binding") == "BOUND"]
    rde.append({"element_type": "BEAM", "element_ids": [b["beam_id"] for b in slab_beams], "rule_ref": "P8-N11",
                "rule_text": rules["P8-N11"]["english_interpretation"], "rule_status": rules["P8-N11"]["status"],
                "gap_kind": "EXTENT", "affected_facts": ["section"], "release_effect": EF.LOWER_BOUND,
                "quantity": round(sum(b.get("support_centreline_length_m") or 0 for b in slab_beams), 3),
                "unit": "m beam", "trade": ["CONCRETE", "FORMWORK"],
                "question": "Which beams are crossed by service pipes (drainage, water, electrical, AC) and must be "
                            "widened by 5 cm?",
                "options": [{"answer": "none", "effect": "no change"},
                            {"answer": "listed beams", "effect": "+5 cm width on those beams"}],
                "source_refs": [rule_ref(rules["P8-N11"])]})
    deep = {d["beam_type"] for d in regs["BEAM_DEFINITION_REGISTER"]["rows"] if (d.get("H_cm") or 0) > 60
            and not d.get("REMARKS_side_bars") and d["element"] in ("SIMPLE_BEAM", "CONTINUOUS_BEAM", "STRAP_BEAM")}
    deep_ids = [b["beam_id"] for b in beams if b.get("beam_type") in deep]
    if deep_ids:
        rde.append({"element_type": "BEAM", "element_ids": deep_ids, "rule_ref": "P8-N21",
                    "rule_text": rules["P8-N21"]["english_interpretation"], "rule_status": rules["P8-N21"]["status"],
                    "gap_kind": "METHOD", "affected_facts": ["side_bars"], "trade": ["REINFORCEMENT"],
                    "quantity": round(sum(b.get("support_centreline_length_m") or 0 for b in beams
                                          if b["beam_id"] in deep_ids), 3), "unit": "m beam",
                    "question": f"Beams deeper than 60 cm without side bars in their schedule row "
                                f"({', '.join(sorted(deep))}): how many 12 mm side bars per face?",
                    "options": [{"answer": "2Ø12 / 3Ø12 / 4Ø12 per face", "effect": "side bars added"}],
                    "source_refs": [rule_ref(rules["P8-N21"])]})
    slab_panel_ids = [p["panel_id"] for p in panels if p["class"] == "SLAB_PANEL" and p["sheet"] != "GBP"]
    rde.append({"element_type": "SLAB", "element_ids": slab_panel_ids, "rule_ref": "P4-6-NOTE-2",
                "rule_text": rules["P4-6-NOTE-2"]["english_interpretation"],
                "rule_status": rules["P4-6-NOTE-2"]["status"], "gap_kind": "APPLICABILITY",
                "affected_facts": ["top_over_supports"], "trade": ["REINFORCEMENT"],
                "quantity": area([p for p in panels if p["panel_id"] in slab_panel_ids]), "unit": "m2 plan",
                "question": "The plan note asks for 5Ø10/m top bars over beams for one third of the span, and p.15 "
                            "gives top-bar extensions of 0.25L / 0.30L. Is the plan note a minimum where no top bar "
                            "is drawn, or does it replace p.15?",
                "options": [{"answer": "minimum where no top bar drawn", "effect": "added only where missing"},
                            {"answer": "replaces p.15", "effect": "one rule for all supports"},
                            {"answer": "both apply", "effect": "both bar sets"}],
                "source_refs": [rule_ref(rules["P4-6-NOTE-2"]), rule_ref(rules["P15-SLAB-ON-BEAMS"])]})
    V["rule_dependent_elements"] = rde
    # ---- temperature table
    tl = defaultdict(list)
    for m in regs["SLAB_RULE_APPLICATION_MAP"]["rows"]:
        t = m["temperature_steel"]
        if t["state"] == "RULE_NOT_EXACT_MATCH":
            tl[t["thickness_mm"]].append(m["panel_id"])
    pa = {p["panel_id"]: p["area_m2"] for p in panels}
    tt = rules["P15-TEMP-TABLE"]
    V["table_lookups"] = [{"element_type": "SLAB", "element_ids": ids, "rule_ref": "P15-TEMP-TABLE",
                           "rule_text": "temperature reinforcement table (p.15)", "key": k, "key_unit": "mm",
                           "table_keys": sorted(int(x) for x in tt["values"]["rows"]), "state": "RULE_NOT_EXACT_MATCH",
                           "fact": "temperature_steel", "quantity": round(sum(pa[i] for i in ids), 3),
                           "unit": "m2 plan", "source_refs": [rule_ref(tt)]} for k, ids in sorted(tl.items())]
    # ---- rule-vs-rule conflicts (same topic) and rule-vs-schedule
    topics = defaultdict(list)
    for r in rules.values():
        if r["status"] == "SOURCE_CONFLICT":
            topics[r["topic"]].append(r)
    rc = []
    for tpc, lst in sorted(topics.items()):
        if len(lst) >= 2:
            rc.append({"rule_refs": [r["rule_id"] for r in lst], "subject": f"{tpc.lower()} rule",
                       "values": [{"rule_ref": r["rule_id"], "value": r["normalized_rule"],
                                   "source_ref": rule_ref(r)} for r in lst], "source_refs": [rule_ref(r) for r in lst]})
        else:
            r = lst[0]
            bw = [d for d in regs["BEAM_DEFINITION_REGISTER"]["rows"] if d["beam_type"] == "B.W"]
            if r["rule_id"] == "P14-BOUNDARY" and bw:
                rc.append({"rule_refs": [r["rule_id"], "SBT:B.W"], "subject": "boundary wall definition",
                           "trade": ["CONCRETE", "REINFORCEMENT"], "release_effect": EF.BLOCKED,
                           "affected_facts": ["section", "reinforcement"],
                           "values": [{"rule_ref": r["rule_id"], "value": r["raw_text"][:120], "source_ref": rule_ref(r)},
                                      {"rule_ref": "schedule row B.W", "value": f"{bw[0]['B_cm']:g}x{bw[0]['H_cm']:g} "
                                                                                f"{bw[0].get('fields', {}).get('bottom', {}).get('raw')}",
                                       "source_ref": sched_ref("SIMPLE_BEAM", key="B.W")}],
                           "source_refs": [rule_ref(r), sched_ref("SIMPLE_BEAM", key="B.W")]})
    V["rule_conflicts"] = rc
    # ---- schedule rows with no occurrence
    od = []
    for d in regs["FOOTING_DEFINITION_REGISTER"]["rows"]:
        if d["state"] == "SCHEDULE_ROW_WITHOUT_PLAN_OCCURRENCE":
            od.append({"element_type": "FOOTING", "schedule_ref": "FT", "key": d["footing_type"],
                       "values": f"{d['L_cm']:g}x{d['W_cm']:g}x{d['D_cm']:g}",
                       "source_refs": [sched_ref("FOOTING", d["source_row"]["insert_handle"], d["footing_type"])]})
    for d in regs["BEAM_DEFINITION_REGISTER"]["rows"]:
        if d["state"] == "SCHEDULE_ROW_WITHOUT_PLAN_OCCURRENCE":
            od.append({"element_type": "BEAM", "schedule_ref": "SBT", "key": d["beam_type"],
                       "values": f"{d['B_cm']:g}x{d['H_cm']:g}",
                       "source_refs": [sched_ref("SIMPLE_BEAM", d["source_row"]["insert_handle"], d["beam_type"])]})
    V["orphan_definitions"] = od
    return V


# ============================================================================================ component release
def components(regs):
    comps = []
    for r in regs["COLUMN_OCCURRENCE_REGISTER"]["rows"]:
        e = r["column_id"]
        comps += [{"element_id": e, "element_type": "COLUMN", "component": "CONCRETE", "trade": "CONCRETE",
                   "quantity": 1, "unit": "nr occurrences", "depends_on": ["occurrence", "member_type", "section"]},
                  {"element_id": e, "element_type": "COLUMN", "component": "MAIN_BARS", "trade": "REINFORCEMENT",
                   "quantity": 1, "unit": "nr occurrences",
                   "depends_on": ["occurrence", "member_type", "reinforcement", "detailing"]},
                  {"element_id": e, "element_type": "COLUMN", "component": "TIES", "trade": "REINFORCEMENT",
                   "quantity": 1, "unit": "nr occurrences",
                   "depends_on": ["occurrence", "member_type", "transverse_count", "transverse_zone",
                                  "transverse_arrangement", "tie_size", "detailing"]}]
    for r in regs["FOOTING_OCCURRENCE_REGISTER"]["rows"]:
        e = r["footing_id"]
        comps += [{"element_id": e, "element_type": "FOOTING", "component": "CONCRETE", "trade": "CONCRETE",
                   "quantity": 1, "unit": "nr", "depends_on": ["member_type", "section", "overlap"]},
                  {"element_id": e, "element_type": "FOOTING", "component": "MAIN_BARS", "trade": "REINFORCEMENT",
                   "quantity": 1, "unit": "nr", "depends_on": ["member_type", "reinforcement"]},
                  {"element_id": e, "element_type": "FOOTING", "component": "BOXED", "trade": "REINFORCEMENT",
                   "quantity": 1, "unit": "nr", "depends_on": ["BOXED", "member_type"]},
                  {"element_id": e, "element_type": "FOOTING", "component": "LOWER_GROUND_BEAM",
                   "trade": "REINFORCEMENT", "quantity": 1, "unit": "nr", "depends_on": ["lower_ground_beam"]}]
    for b in regs["BEAM_OCCURRENCE_REGISTER"]["rows"]:
        L = b.get("support_centreline_length_m") or b.get("drawn_length_m")
        e = b["beam_id"]
        base = ["occurrence", "member_type", "member_assignment", "geometry"]
        comps += [{"element_id": e, "element_type": "BEAM", "component": "CONCRETE", "trade": "CONCRETE",
                   "quantity": L, "unit": "m beam", "depends_on": base + ["section", "extent"]},
                  {"element_id": e, "element_type": "BEAM", "component": "MAIN_BARS", "trade": "REINFORCEMENT",
                   "quantity": L, "unit": "m beam",
                   "depends_on": base + ["reinforcement", "span_assignment", "detailing"]},
                  {"element_id": e, "element_type": "BEAM", "component": "SIDE_BARS", "trade": "REINFORCEMENT",
                   "quantity": L, "unit": "m beam", "depends_on": base + ["side_bars"]}]
    for p in regs["SLAB_PANEL_REGISTER"]["rows"]:
        if p["terminal_state"] == "NOT_IN_SCOPE":
            continue
        e = p["panel_id"]
        comps += [{"element_id": e, "element_type": "SLAB", "component": "CONCRETE", "trade": "CONCRETE",
                   "quantity": p["area_m2"], "unit": "m2 plan", "depends_on": ["section", "extent", "geometry"]},
                  {"element_id": e, "element_type": "SLAB", "component": "BOTTOM_AND_MAIN_BARS",
                   "trade": "REINFORCEMENT", "quantity": p["area_m2"], "unit": "m2 plan",
                   "depends_on": ["extent", "geometry", "detailing"]},
                  {"element_id": e, "element_type": "SLAB", "component": "TOP_OVER_SUPPORTS", "trade": "REINFORCEMENT",
                   "quantity": p["area_m2"], "unit": "m2 plan", "depends_on": ["top_over_supports", "extent",
                                                                               "geometry"]},
                  {"element_id": e, "element_type": "SLAB", "component": "TEMPERATURE_STEEL",
                   "trade": "REINFORCEMENT", "quantity": p["area_m2"], "unit": "m2 plan",
                   "depends_on": ["temperature_steel", "extent"]}]
    return comps


def fact_classification(regs):
    """Where each S1 register's content sits in the six fact classes (counts)."""
    occ = regs["COLUMN_OCCURRENCE_REGISTER"]["rows"]
    beams = regs["BEAM_OCCURRENCE_REGISTER"]["rows"]
    rows = [
        {"fact": "plan type marks (column / footing / beam tags)", "class": SA.SOURCE_FACT,
         "count": sum(len(c["tags_by_plan"]) for c in regs["COLUMN_VERTICAL_CHAIN_REGISTER"]["rows"])
         + len(regs["FOOTING_OCCURRENCE_REGISTER"]["rows"]) + sum(1 for b in beams if b.get("tag_handle")),
         "registers": ["COLUMN_VERTICAL_CHAIN_REGISTER", "FOOTING_OCCURRENCE_REGISTER", "BEAM_OCCURRENCE_REGISTER"]},
        {"fact": "schedule rows (column, footing, beam, CB)", "class": SA.SOURCE_FACT,
         "count": len(regs["COLUMN_DEFINITION_REGISTER"]["rows"]) + len(regs["FOOTING_DEFINITION_REGISTER"]["rows"])
         + len(regs["BEAM_DEFINITION_REGISTER"]["rows"]),
         "registers": ["COLUMN_DEFINITION_REGISTER", "FOOTING_DEFINITION_REGISTER", "BEAM_DEFINITION_REGISTER"]},
        {"fact": "slab bar texts, T marks, detail texts", "class": SA.SOURCE_FACT,
         "count": len(regs["SLAB_REBAR_SOURCE_REGISTER"]["rows"]) + len(regs["POOL_STRUCTURAL_REGISTER"]["rows"]),
         "registers": ["SLAB_REBAR_SOURCE_REGISTER", "POOL_STRUCTURAL_REGISTER"]},
        {"fact": "column outlines, vertical chains, drawn sections", "class": SA.DERIVED_GEOMETRY,
         "count": len(occ), "registers": ["COLUMN_OCCURRENCE_REGISTER", "COLUMN_VERTICAL_CHAIN_REGISTER"]},
        {"fact": "beam spans, supports, centreline / clear lengths", "class": SA.DERIVED_GEOMETRY,
         "count": len(beams), "registers": ["BEAM_OCCURRENCE_REGISTER"]},
        {"fact": "slab panel polygons, Lx / Ly, edge continuity", "class": SA.DERIVED_GEOMETRY,
         "count": len(regs["SLAB_PANEL_REGISTER"]["rows"]), "registers": ["SLAB_PANEL_REGISTER"]},
        {"fact": "tie-band topology read from the detail geometry", "class": SA.DERIVED_GEOMETRY,
         "count": len(regs["COLUMN_TIE_TOPOLOGY_RULES"]["rows"]), "registers": ["COLUMN_TIE_TOPOLOGY_RULES"]},
        {"fact": "project general notes / typical-detail rules", "class": SA.PROJECT_RULE,
         "count": len(regs["STRUCTURAL_PROJECT_RULE_REGISTER"]["rows"]),
         "registers": ["STRUCTURAL_PROJECT_RULE_REGISTER"]},
        {"fact": "engineering methods (tie zone, side bars, stairs ...)", "class": SA.ENGINEERING_METHOD,
         "count": 0, "note": "none approved yet - each open method is an engineering flag"},
        {"fact": "project human claims", "class": SA.PROJECT_HUMAN_CLAIM, "count": 0,
         "note": "none received yet (claim store empty)"},
        {"fact": "census + review engine logic", "class": SA.GENERIC_ENGINE_RULE, "count": None,
         "note": "engine/source/structural_census.py, structural_authority.py, flag_detectors.py ..."}]
    return rows


# ============================================================================================ outputs
def dumps(o):
    return json.dumps(o, indent=1, sort_keys=True, ensure_ascii=False) + "\n"


def md_questions(qs):
    out = ["# Alsenan - consultant questions (generated from open engineering flags)", "",
           "Each block is generated from the flag's source context. Answers are stored as PROJECT claims "
           "(ALSENAN_PROJECT_CLAIMS.json), never as engine rules.", ""]
    for q in qs:
        out += [f"## {q['flag_id']}", "", f"**Issue:** {q['PLAIN_LANGUAGE_ISSUE']}", "",
                f"**Why it matters:** {q['WHY_IT_MATTERS']}", "", f"**Where to look:** {q['WHERE_TO_LOOK']}", ""]
        if q["WHAT_THE_DRAWING_SAYS"]:
            out += ["**Current evidence:**"] + [f"- {x}" for x in q["WHAT_THE_DRAWING_SAYS"]] + [""]
        out += [f"**Engine's current interpretation:** {q['ENGINE_CURRENT_INTERPRETATION']}", "",
                f"**Question:** \"{q['QUESTION_TO_CONSULTANT']}\"", "",
                f"**Impact:** {q['QUANTITY_BOQ_IMPACT']['release_effect']} - "
                f"{', '.join(q['QUANTITY_BOQ_IMPACT']['trades'])}; "
                f"{len(q['QUANTITY_BOQ_IMPACT']['elements'])} element(s)"
                + (f"; {q['QUANTITY_BOQ_IMPACT']['quantity_affected']} {q['QUANTITY_BOQ_IMPACT']['unit']}"
                   if q['QUANTITY_BOQ_IMPACT']['quantity_affected'] is not None else ""), ""]
    return "\n".join(out) + "\n"


def md_help(hs):
    out = ["# Alsenan - review helper (plain language, for Mohammad)", ""]
    for h in hs:
        out += [f"## {h['flag_id']}", "", f"**What does this mean?** {h['WHAT_DOES_THIS_MEAN']}", ""]
        if h["TERMS_EXPLAINED"]:
            out += ["**Words used here:**"] + [f"- *{k}*: {v}" for k, v in h["TERMS_EXPLAINED"].items()] + [""]
        out += [f"**Why does it matter?** {h['WHY_DOES_IT_MATTER']}", "", "**Where should I look?**"]
        out += [f"- {x}" for x in h["WHERE_SHOULD_I_LOOK"] if x] + ["", "**What should I search in AutoCAD?**"]
        out += [f"- {x}" for x in h["WHAT_TO_SEARCH_IN_AUTOCAD"]] + ["", "**What would each answer change?**"]
        out += [f"- if *{o['if_the_answer_is']}*: {o['then']}" for o in h["WHAT_WOULD_EACH_ANSWER_CHANGE"]]
        out += ["", f"**What should I ask the engineering office?** \"{h['WHAT_TO_ASK_THE_ENGINEERING_OFFICE']}\"", ""]
    return "\n".join(out) + "\n"


def md_summary(s, flags, rel_tot):
    lines = ["# ENGINEERING FLAGS SUMMARY - Alsenan (S2)", "", "Front-summary lines (generated):", ""]
    lines += [f"- {x}" for x in s["front_summary_lines"]] + ["", "| Discipline | Total | Open | Provisional | "
                                                                  "Resolved |", "|---|---|---|---|---|"]
    for d, v in s["by_discipline"].items():
        b = v["by_status"]
        lines.append(f"| {d} | {v['total']} | {b.get('OPEN', 0)} | {b.get('PROVISIONAL', 0)} | {b.get('RESOLVED', 0)} |")
    lines += ["", "Open flags by effect (structural):", ""]
    for k, v in s["by_discipline"]["STRUCTURAL"]["open_by_effect"].items():
        lines.append(f"- {k}: {v}")
    lines += ["", "Open flags by issue type:", ""] + [f"- {k}: {v}" for k, v in sorted(s["open_by_issue_type"].items())]
    lines += ["", "Component release over the census (measured-quantity basis: occurrences / m / m2 - no kg):", "",
              "| Trade / unit | Released | Provisional | Lower bound | Audit only | Blocked |",
              "|---|---|---|---|---|---|"]
    for k, v in rel_tot.items():
        lines.append(f"| {k} | {v.get('released', 0)} | {v.get('released_provisional', 0)} | "
                     f"{v.get('lower_bound', 0)} | {v.get('audit_only', 0)} | {v.get('blocked', 0)} |")
    lines += ["", "| Flag | Issue | Element | Effect | Severity | Status | Summary |", "|---|---|---|---|---|---|---|"]
    for f in flags:
        lines.append(f"| {f['flag_id']} | {f['issue_type']} | {f['element_type']} ({len(f['element_ids'])}) | "
                     f"{f['release_effect']} | {f['severity']} | {f['status']} | "
                     f"{f['issue_summary'].replace('|', '/')[:150]} |")
    lines += ["", "Pricing is not integrated. No reinforcement weight is calculated in S2."]
    return "\n".join(lines) + "\n"


def main():
    idx, regs = load_s1()
    view = build_view(regs)
    flags = FD.detect(view)
    claims = []   # project claim store: empty until Mohammad / the consultant answer
    flags, claim_log = PC.apply_to_flags(flags, claims, project_id=PROJECT_ID, drawing_revision=REVISION)
    open_flags = [f for f in flags if EF.is_open(f)]
    qs = [QH.consultant_question(f) for f in open_flags]
    hs = [QH.help_mode(f) for f in open_flags]
    comps = components(regs)
    rel = EF.component_release(comps, flags)
    rel_tot = EF.release_totals(rel)
    summ = EF.summary(flags)
    by_el = defaultdict(Counter)
    for c in rel:
        by_el[c["element_type"]][f"{c['component']}:{c['release_state']}"] += 1
    promo = {"project_id": PROJECT_ID, "registry": [],
             "proposable_lessons": [{"flag_key": f["flag_key"], "flag_id": f["flag_id"],
                                     "lesson": f["generic_rule_candidate"], "state": RP.PROJECT_ONLY}
                                    for f in flags if f.get("generic_rule_candidate")],
             "note": "nothing is promoted automatically; a lesson becomes GENERIC_CANDIDATE only via "
                     "rule_promotion.propose() after a consultant answer, and GENERIC_APPROVED only after review"}
    out = {
        "ALSENAN_REVIEW_VIEW.json": view,
        "ALSENAN_ENGINEERING_FLAGS.json": {"project_id": PROJECT_ID, "drawing_revision": REVISION,
                                           "flags": flags, "claim_application_log": claim_log},
        "ALSENAN_CONSULTANT_QUESTIONS.json": qs,
        "ALSENAN_REVIEW_HELPER.json": hs,
        "ALSENAN_PROJECT_CLAIMS.json": {"project_id": PROJECT_ID, "drawing_revision": REVISION, "claims": claims,
                                        "schema": "research/structural_engine_s2/PROJECT_CLAIM_SCHEMA.json"},
        "ALSENAN_RULE_PROMOTION_REGISTRY.json": promo,
        "ALSENAN_FACT_CLASSIFICATION.json": fact_classification(regs),
        "ALSENAN_COMPONENT_RELEASE.json": {"basis": "census measured quantities (occurrences, m beam, m2 plan); "
                                                    "no reinforcement weight", "totals": rel_tot,
                                           "by_element_type": {k: dict(v) for k, v in by_el.items()},
                                           "components": rel},
        "ENGINEERING_FLAGS_SUMMARY.json": summ,
    }
    files = {}
    for name, obj in out.items():
        txt = dumps(obj)
        (HERE / name).write_text(txt, encoding="utf-8")
        files[name] = hashlib.sha256(txt.encode()).hexdigest()
    for name, txt in (("ALSENAN_CONSULTANT_QUESTIONS.md", md_questions(qs)), ("ALSENAN_REVIEW_HELPER.md", md_help(hs)),
                      ("ENGINEERING_FLAGS_SUMMARY.md", md_summary(summ, flags, rel_tot))):
        (HERE / name).write_text(txt, encoding="utf-8")
        files[name] = hashlib.sha256(txt.encode()).hexdigest()
    index = {"round": "S2", "project_id": PROJECT_ID, "s1_registers_consumed": {k: v["sha256"] for k, v in
                                                                              idx["registers"].items()},
             "s1_census_modified": False, "rebar_kg_calculated": False, "pricing_integrated": False,
             "flags": len(flags), "open_flags": len(open_flags), "outputs": files}
    (HERE / "INDEX.json").write_text(dumps(index), encoding="utf-8")
    print(json.dumps({"flags": len(flags), "open": len(open_flags),
                      "by_issue": Counter(f["issue_type"] for f in flags),
                      "by_detector": Counter(f["detector"] for f in flags)}, default=dict, indent=0))
    print("\n".join(summ["front_summary_lines"]))


if __name__ == "__main__":
    main()
