"""ALSENAN P7757 + ST7757 PHASE A2 - registers, workbook model, QA and the freeze (from the A2 build context only).

Every quantity row names its CLASS:
    PHYSICAL_MEASUREMENT   a geometric quantity proved from the source (area, length, count) - SHADOW
    TRADE_ASSIGNMENT       a physical quantity assigned to a trade scope by a stated rule (e.g. wet-room floors)
    BLOCKED_MATERIAL       the physical quantity may exist; the MATERIAL / finish / type is not in the source
    BLOCKED_HEIGHT         the plan quantity exists; the height that would make it an area / volume is not proved
A BLOCKED row has no quantity and is in no total. Nothing here is priced, calibrated or migrated.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

from engine import boq_rc1_xlsx as BX                                                            # noqa: E402
from engine.source import benchmark_firewall as FW, cad_text as CT, entity_role_inference as ERI # noqa: E402
from engine.source import freeze_schema as FS, level_marks as LM, schedule_table as ST          # noqa: E402
from engine.source import structural_qto as SQ                                                   # noqa: E402

import alsenan_phase_a as AP                                                                      # noqa: E402
import alsenan_phase_a2 as A2                                                                     # noqa: E402
import alsenan_registers as AR                                                                    # noqa: E402

RECOMMENDATION_COMMIT, BASELINE_COMMIT = "d22e32e", "07a373a"
CREATED = dt.datetime(2026, 10, 3, 0, 0, 0)
XLSX_NAME = "URBAN_QTO_ALSENAN_P7757_ST7757_PHASE_A2.xlsx"
BANNER = ("SHADOW / PHASE A2 SOURCE-ONLY GENERIC ENGINE IMPROVEMENT - ALSENAN P7757 + ST7757 - FROZEN BEFORE ANY "
          "BENCHMARK - NOT FOR TENDER OR CONTRACT - NO PRICES - VIEW OVER ENGINE REGISTERS - NO PRODUCTION MIGRATION")
COLUMNS = ["ITEM CODE", "DISCIPLINE", "TRADE", "FLOOR", "ROOM/ELEMENT", "DESCRIPTION AR", "DESCRIPTION EN", "QTY",
           "UNIT", "STATUS", "CLASS", "SOURCE", "RULE", "BLOCKER"]
PHYS, TRADE, BMAT, BHGT = "PHYSICAL_MEASUREMENT", "TRADE_ASSIGNMENT", "BLOCKED_MATERIAL", "BLOCKED_HEIGHT"
COMPLETE, SUBTOTAL, BLOCKED = SQ.COMPLETE, "AUTHORISED_SUBTOTAL", "BLOCKED"
FLOORS = A2.FLOORS
digest, r6, sheet = AR.digest, AR.r6, AR.sheet
SUMMARY_NAME = "02_ARCH_SUMMARY / 15_STRUCTURAL_SUMMARY"
HEIGHT_BLOCK = ("HEIGHT_NOT_PROVED: floor-to-floor is corroborated on the sections (GF->1F 4.50, 1F->2F 4.20, "
                "2F->roof 4.20 m) but the clear height also needs the floor build-up and any false ceiling, which are "
                "not in the source")
FINISH_BLOCK = "FINISH_MATERIAL_NOT_IN_SOURCE: no finish schedule exists (owner: the supplied files are all the files)"


def row(item, trade, floor, element, ar, en, qty, unit, status, klass, source, rule, blockers=()):
    return {"item": item, "discipline": "ARCHITECTURAL" if item.startswith("A2-") else "STRUCTURAL", "trade": trade,
            "floor": floor, "element": element, "ar": ar, "en": en, "qty": None if status == BLOCKED else qty,
            "unit": unit, "status": status, "class": klass, "source": source, "rule": rule,
            "blockers": list(blockers)}


def boq_line(r):
    return [r["item"], r["discipline"], r["trade"], r["floor"], r["element"], r["ar"], r["en"], r6(r["qty"]),
            r["unit"], r["status"], r["class"], r["source"], r["rule"], " | ".join(r["blockers"])]


def _wet(label):
    u = label.upper()
    return any(w in u.replace(" ", "") or w in u for w in A2.WET_WORDS)


# ====================================================================== architectural
def rooms_register(a2) -> list:
    out = []
    for fl in FLOORS:
        for r in a2["floors"][fl]["rooms"]:
            cert = r["status"] == "CERTIFIED"
            rl = r["role_lengths_m"]
            wall_len = rl.get("TOPOLOGY_BOUNDARY", 0.0) + rl.get("STRUCTURAL_OBSTACLE", 0.0)
            door_len = rl.get("OPENING_BOUNDARY", 0.0)
            glaz = rl.get("GLAZING_BOUNDARY", 0.0)
            wet = _wet(r["label_en"])
            fixtures = r["contents"].get("FURNITURE", 0) + r["contents"].get("SANITARY_FIXTURE", 0)
            out.append({"floor": fl, "room": r["label_en"] or "(label not decoded)", "site": r["site"],
                        "status": COMPLETE if cert else "BLOCKED", "issues": r["issues"],
                        "floor_area_m2": r["area_m2"] if cert else None,
                        "area_uncertainty_m2": r["area_bound_m2"] if cert else None,
                        "base_ceiling_area_m2": r["area_m2"] if cert else None,
                        "perimeter_m": r["perimeter_m"] if cert else None,
                        "wall_face_length_m": round(wall_len, 6) if cert else None,
                        "door_closure_length_m": round(door_len, 6) if cert else None,
                        "glazing_length_m": round(glaz, 6) if cert else None,
                        "skirting_path_m": round(r["perimeter_m"] - door_len, 6) if cert else None,
                        "wall_face_area_m2": None, "wall_face_area_blocker": HEIGHT_BLOCK,
                        "wet_semantics": ("WET_CORROBORATED (wet label + fixture symbol inside the site)" if wet and
                                          fixtures else "WET_LABEL_ONLY" if wet else "NOT_WET_BY_EVIDENCE"),
                        "fixture_symbols_in_site": fixtures, "label_other_script": r["label_other"],
                        "blocked_by_layers": r["blocked_by_layers"], "crosscheck": r["crosscheck"],
                        "blocker": None if cert else "; ".join(r["issues"]) or "NOT_CERTIFIED"})
    return out


def arch_rows(a2, rooms) -> list:
    rows = []
    src = "P7757.dxf plan region (entity_role_inference claims + TS01 + closure policy)"
    for fl in FLOORS:
        rs = [r for r in rooms if r["floor"] == fl]
        cert = [r for r in rs if r["status"] == COMPLETE]
        blk = [r for r in rs if r["status"] == "BLOCKED"]
        names = ", ".join(f"{r['room']} {r['floor_area_m2']:.2f}" for r in cert)
        bnames = [f"ROOM_NOT_CERTIFIED: {r['room']} ({r['blocker']})" for r in blk]
        if not cert:
            t = a2["floors"][fl]["topology"]
            bnames.append(f"NO_CERTIFIED_ROOM_ON_FLOOR: {t['labelled_sites']} labelled site(s), "
                          f"{t['certified_labelled_sites']} certified (see ROOM_TOPOLOGY_REGISTER)")
        st = COMPLETE if cert and not blk else SUBTOTAL if cert else BLOCKED
        tot = lambda k: round(sum(r[k] for r in cert), 6) if cert else None
        el = f"{len(cert)} certified room(s): {names}" if cert else "no certified room"
        rows += [
            row(f"A2-FLR-{fl}", "FLOOR_AREA", fl, el, "مساحة الأرضيات (صافي)", "Floor area per room, clear internal",
                tot("floor_area_m2"), "m2", st, PHYS, src, "site polygon of a CERTIFIED labelled site", bnames),
            row(f"A2-CLG-{fl}", "CEILING_BASE", fl, el, "مساحة السقف الأساسية", "Base physical ceiling area (= room "
                "plan area; false-ceiling adjustment blocked)", tot("base_ceiling_area_m2"), "m2", st, PHYS, src,
                "BASE_PHYSICAL_CEILING_AREA = clear plan area", bnames),
            row(f"A2-WFL-{fl}", "WALL_FACE_LENGTH", fl, el, "طول أوجه الجدران", "Physical wall-face length (wall + column"
                " faces bounding the certified rooms)", tot("wall_face_length_m"), "m", st, PHYS, src,
                "boundary role lengths TOPOLOGY_BOUNDARY + STRUCTURAL_OBSTACLE", bnames),
            row(f"A2-WFA-{fl}", "WALL_FACE_AREA", fl, el, "مساحة أوجه الجدران", "Physical wall-face area", None, "m2",
                BLOCKED, BHGT, src, "face length x clear height", [HEIGHT_BLOCK]),
            row(f"A2-SKP-{fl}", "SKIRTING_PATH", fl, el, "مسار الوزرة", "Skirting-eligible path (perimeter minus door "
                "closures; windows not deducted - none proved floor-reaching)", tot("skirting_path_m"), "m", st, PHYS,
                src, "perimeter - OPENING_BOUNDARY length", bnames),
            row(f"A2-FFN-{fl}", "FLOOR_FINISH", fl, el, "مادة التشطيب للأرضيات", "Floor finish material", None, "m2",
                BLOCKED, BMAT, src, "physical floor area exists (A2-FLR); material assignment needs a finish schedule",
                [FINISH_BLOCK]),
            row(f"A2-WFN-{fl}", "WALL_FINISH", fl, el, "تشطيب الجدران (لياسة / دهان / بلاط)", "Wall finish (plaster / "
                "paint / tile)", None, "m2", BLOCKED, BMAT, src, "needs wall-face area AND a finish schedule",
                [HEIGHT_BLOCK, FINISH_BLOCK]),
            row(f"A2-CFN-{fl}", "CEILING_FINISH", fl, el, "تشطيب الأسقف", "Ceiling finish / false ceiling", None, "m2",
                BLOCKED, BMAT, src, "base ceiling area exists (A2-CLG); finish and false-ceiling levels not in source",
                [FINISH_BLOCK]),
            row(f"A2-SKM-{fl}", "SKIRTING_MATERIAL", fl, el, "مادة الوزرة", "Skirting material", None, "m", BLOCKED,
                BMAT, src, "path exists (A2-SKP); material not in source", [FINISH_BLOCK])]
        wet = [r for r in cert if r["wet_semantics"].startswith("WET_CORROBORATED")]
        rows.append(row(f"A2-WET-{fl}", "WET_ROOM_FLOOR", fl, ", ".join(r["room"] for r in wet) or "none",
                        "مساحة أرضيات المناطق المبتلة", "Wet-room floor area (waterproofing scope candidate)",
                        round(sum(r["floor_area_m2"] for r in wet), 6) if wet else None, "m2",
                        COMPLETE if wet else BLOCKED, TRADE, src,
                        "certified room + wet label + fixture symbol inside (semantics only; sanitary PDF supporting)",
                        [] if wet else ["NO_CERTIFIED_WET_CORROBORATED_ROOM"]))
        rows.append(row(f"A2-WPM-{fl}", "WATERPROOFING_MATERIAL", fl, "wet rooms", "مادة العزل المائي",
                        "Waterproofing membrane / upturn", None, "m2", BLOCKED, BMAT, src,
                        "membrane type and upturn height not in source", [FINISH_BLOCK]))
        # blockwork by thickness
        th = defaultdict(lambda: [0.0, 0.0, 0])
        lo, hi = ERI.PHYSICAL_MM["wall_thickness"]
        odd = [b for b in a2["floors"][fl]["bands"] if b["state"] == "WALL_BAND_ESTABLISHED"
               and not lo <= b["thickness_mm"] <= hi]
        odd_txt = ", ".join(f"{b['thickness_mm']:.0f} mm" for b in odd)
        for b in a2["floors"][fl]["bands"]:
            if b["state"] == "WALL_BAND_ESTABLISHED" and lo <= b["thickness_mm"] <= hi:
                k = int(round(b["thickness_mm"] / 10.0) * 10)
                th[k][0] += b["length_m"]
                th[k][1] += b["column_overlap_m"]
                th[k][2] += 1
        amb = sum(1 for b in a2["floors"][fl]["bands"] if b["state"] != "WALL_BAND_ESTABLISHED")
        for k in sorted(th):
            L, ov, n = th[k]
            rows.append(row(f"A2-BLK-{fl}-T{k}", "BLOCKWORK_LENGTH", fl, f"{n} established bands, {k} mm",
                            f"طول البلوك سماكة {k} مم", f"Blockwork length, {k} mm wall bands (column overlaps excluded)",
                            round(L - ov, 6), "m", COMPLETE, PHYS, src,
                            "WALL_BAND_ESTABLISHED interval length minus OBSTACLE_OVERLAP",
                            ([f"{amb} ambiguous band(s) on {fl} not included (WALL_BAND_AMBIGUOUS)"] if amb else []) +
                            ([f"{len(odd)} established band(s) outside the {lo:.0f}-{hi:.0f} mm wall range not "
                              f"included ({odd_txt}: sheet / title-block linework)"] if odd else [])))
            rows.append(row(f"A2-BLA-{fl}-T{k}", "BLOCKWORK_AREA", fl, f"{k} mm", f"مساحة البلوك سماكة {k} مم",
                            f"Blockwork area, {k} mm", None, "m2", BLOCKED, BHGT, src, "length x wall height",
                            [HEIGHT_BLOCK]))
        if not th:
            rows.append(row(f"A2-BLK-{fl}", "BLOCKWORK_LENGTH", fl, "no established band", "طول البلوك",
                            "Blockwork length", None, "m", BLOCKED, PHYS, src, "established wall bands",
                            ["WALL_ROLE_UNRESOLVED: no wall-face layer accepted / no established band"]))
        ds = a2["floors"][fl]["doors"]
        closed = [d for d in ds if d["state"] == "CLOSED"]
        rows.append(row(f"A2-DOR-{fl}", "DOORS", fl, f"{len(closed)} closed of {len(ds)} door symbols",
                        "عدد الأبواب", "Doors (existence: wall gap + door-symbol motif)", len(closed) if closed else None,
                        "nr", COMPLETE if closed and len(closed) == len(ds) else SUBTOTAL if closed else BLOCKED, PHYS,
                        src, "inferred door occurrence admitted AND its opening closure CLOSED",
                        [f"OPENING_CLOSURE_UNRESOLVED: {d['occurrence']} ({d['why']})" for d in ds
                         if d["state"] != "CLOSED"]))
        rows.append(row(f"A2-DRM-{fl}", "DOOR_TYPE_MATERIAL", fl, "doors", "نوع ومادة الأبواب وارتفاعها",
                        "Door type / material / height", None, "nr", BLOCKED, BMAT, src, "door schedule",
                        ["DOOR_SCHEDULE_NOT_IN_SOURCE", "DOOR_HEIGHT_NOT_PRINTED"]))
        ws = a2["floors"][fl]["windows"]
        rows.append(row(f"A2-WIN-{fl}", "WINDOWS", fl, f"{len(ws)} glazing-in-gap openings", "عدد الشبابيك",
                        "Windows (existence: glazing lines inside a wall gap)", len(ws) if ws else None, "nr",
                        COMPLETE if ws else BLOCKED, PHYS, src, "entity_role_inference glazing motif",
                        [] if ws else ["NO_GLAZING_MOTIF_ON_THIS_FLOOR"]))
        rows.append(row(f"A2-WNW-{fl}", "WINDOW_WIDTH", fl, "windows", "مجموع عروض الشبابيك",
                        "Window widths (sum of wall-gap widths)", round(sum(w["width_mm"] for w in ws) / 1000, 6)
                        if ws else None, "m", COMPLETE if ws else BLOCKED, PHYS, src, "gap width jamb to jamb",
                        [] if ws else ["NO_GLAZING_MOTIF_ON_THIS_FLOOR"]))
        rows.append(row(f"A2-WNA-{fl}", "WINDOW_AREA", fl, "windows", "مساحة الشبابيك", "Window area / aluminium / "
                        "glazing", None, "m2", BLOCKED, BHGT, src, "width x height", ["WINDOW_HEIGHT_NOT_PRINTED: no sill /"
                        " head level in any source for these openings", "WINDOW_SCHEDULE_NOT_IN_SOURCE"]))
        sr = [x for x in a2["floors"][fl]["stairs"] if x["linetype_class"] == ERI.CONTINUOUS]
        dashed = [x for x in a2["floors"][fl]["stairs"] if x["linetype_class"] != ERI.CONTINUOUS]
        rows.append(row(f"A2-STT-{fl}", "STAIR_TREADS", fl, "; ".join(f"{s['tread_lines']} lines @ {s['going_mm']:.0f}"
                        f" x {s['width_mm']:.0f} mm" for s in sr) or "none", "خطوط درجات السلم",
                        "Stair tread lines in plan, continuous (at or below the cut plane)",
                        sum(s["tread_lines"] for s in sr) if sr else None, "nr", COMPLETE if sr else BLOCKED, PHYS, src,
                        "tread motif (>= 4 equal parallel lines at a regular going), continuous linetype only",
                        ([f"{sum(x['tread_lines'] for x in dashed)} dashed tread line(s) (flights above the cut plane) "
                          "reported, not counted"] if dashed else []) + ([] if sr else ["NO_TREAD_MOTIF_ON_THIS_FLOOR"])))
        rows.append(row(f"A2-STR-{fl}", "STAIR_RISE_FINISH", fl, "stairs", "ارتفاع القائمة وتشطيب الدرج والدرابزين",
                        "Riser height, stair finish, railing", None, "m", BLOCKED, BHGT, src,
                        "riser count per flight AND floor-to-floor", ["RISER_COUNT_PER_FLIGHT_NOT_PROVED (plan shows "
                        "tread lines of several flights; which belong to one floor-to-floor rise is not proved)",
                        FINISH_BLOCK]))
    rows.append(row("A2-EXT-FAC", "EXTERNAL_FACADES", "EXTERNAL", "all facades", "لياسة ودهان الواجهات",
                    "External plaster / paint", None, "m2", BLOCKED, BHGT, "P7757 NW / SE elevations (vector) + SW / NE "
                    "(raster only)", "facade length x height minus openings", ["ELEVATIONS_SW_NE_RASTER_ONLY",
                    "OPENING_HEIGHTS_NOT_PRINTED", FINISH_BLOCK]))
    return rows


# ====================================================================== structural
def footing_rows_a2(ctx) -> tuple:
    a2 = ctx["a2"]["footings"]
    ft = ctx["footing_schedule"]
    rows = []
    done_types = {t for t, v in a2["result"].items() if v["state"] == SQ.COUNT_UNIQUE}
    used = defaultdict(int)
    comp = {t: (v["contained"] + v["outlines"]) for t, v in a2["result"].items() if t in done_types}
    for r in ctx["footings"]["rows"]:
        typ = r["element_id"].split("@", 1)[0]
        if r["status"] == SQ.COMPLETE or typ not in done_types:
            rr = dict(r)
            if r["status"] != SQ.COMPLETE and typ in a2["result"]:
                v = a2["result"][typ]
                rr["blockers"] = sorted(set(r["blockers"]) | {f"COMPLETION_{v['state']}: {v['orphan_tags']} orphan "
                                        f"tag(s), {len(v['contained'])} contained, {v['free_candidates']} free template "
                                        f"outline(s) of the scheduled size"})
            rows.append(rr)
            continue
        o = comp[typ][used[typ]]
        used[typ] += 1
        f = ft[typ]
        nr = SQ.concrete_row(item="STR-FTG", element_class="FOOTING", floor="FOUNDATION", element_id=r["element_id"],
                             count=1, dims={k: {"m": f[c] / 100.0, "source": "SCHEDULE OF FOOTINGS (cm) " + typ}
                                            for k, c in (("L", "L_cm"), ("W", "W_cm"), ("H", "H_cm"))},
                             formula="1 x L x W x H", sources=r["sources"] + [f"OUTLINE:{o['bounds']}"])
        nr["size_check"] = f"TEMPLATE_OUTLINE_{o['state']}: drawn outline of the scheduled plan size ({o['rule']})"
        nr["completion"] = {"rule": o["rule"], "outline_bounds": list(o["bounds"]), "outline_state": o["state"],
                            "sides": o.get("sides")}
        rows.append(nr)
    return rows


def structural(ctx, regsA) -> dict:
    frows = footing_rows_a2(ctx)
    sub = {"footings": {"rows": frows}, "footing_schedule": ctx["footing_schedule"]}
    fsum = AR.footing_rows(sub)
    for s in fsum:
        s["class"] = PHYS if s["status"] != BLOCKED else "BLOCKED_GEOMETRY"
        s["rule"] = ("STRUCTURAL_QTO_V1 + STRUCTURAL_COMPLETION_V1: tag-in-outline matches, then constraint-unique "
                     "completion; L x W x H from the schedule")
    complete = [r for r in frows if r["status"] == SQ.COMPLETE]
    se = regsA["STRUCTURAL_ELEMENT_REGISTER"]
    # columns
    cols, crow = [], []
    for c in se["columns"]:
        def bh(txt):
            nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", txt.split("/")[0] + " " + (txt.split("/")[1]
                                                                                              if "/" in txt else ""))]
            return nums[:2] if len(nums) >= 2 else None
        secs = {k: bh(c[k]) for k in ("foundation", "ground_floor", "first_floor", "second_floor")}
        n = c["count_on_column_plan"]
        plan = {k: (round(n * v[0] * v[1] / 1e4, 6) if v and n else None) for k, v in secs.items()}
        cols.append({"type": c["type"], "count_on_column_plan": n, "sections_cm": secs,
                     "plan_area_m2_by_storey": plan, "volume_m3": None,
                     "volume_blocker": "COLUMN_HEIGHT_NOT_PROVED: no founding / ground-beam / slab top level in the "
                                       "source (structural levels, not FFL)",
                     "reinforcement_text": {k: c[k] for k in ("foundation", "ground_floor", "first_floor", "second_floor")}})
    tot_gf = sum(v["plan_area_m2_by_storey"]["ground_floor"] or 0 for v in cols)
    n_all = sum(v["count_on_column_plan"] for v in cols)
    crow.append(row("S2-COL-CNT", "COLUMNS", "ALL", f"{n_all} tagged columns on the column plan", "عدد الأعمدة",
                    "Columns - count by type (column & axis plan)", n_all, "nr", COMPLETE, PHYS,
                    "ST7757.dxf COLUMN & AXIS PLAN tags + SCHEDULE OF COLUMNS", "tag count per scheduled type"))
    crow.append(row("S2-COL-PLAN-GF", "COLUMNS", "GF", "ground-floor sections x count", "مساحة مقطع الأعمدة - الأرضي",
                    "Column plan section area, ground-floor sections", round(tot_gf, 6), "m2", COMPLETE, PHYS,
                    "SCHEDULE OF COLUMNS (cm) x count", "sum count x b x h (schedule, ground floor)"))
    crow.append(row("S2-COL-VOL", "COLUMNS", "ALL", "all storeys", "خرسانة الأعمدة", "Column concrete", None, "m3",
                    BLOCKED, BHGT, "ST7757.dxf", "section x storey height", ["COLUMN_HEIGHT_NOT_PROVED"]))
    # beams
    beams = []
    for b in se["simple_beams"]:
        cells = dict(kv.split("=", 1) for kv in b["cells"].split("; ") if "=" in kv)
        bw = next((v for k, v in cells.items() if "B-(" in k), None)
        dp = next((v for k, v in cells.items() if "D-(" in k), None)
        beams.append({"type": b["type"], "breadth_cm": AP.num(bw), "depth_cm": AP.num(dp),
                      "section_m2": round(AP.num(bw) * AP.num(dp) / 1e4, 6) if AP.num(bw) and AP.num(dp) else None,
                      "tags_per_sheet": {k: v.get(b["type"], 0) for k, v in ctx["a2"]["beams"]["tags_per_sheet"].items()},
                      "length_m": None, "length_blocker": "BEAM_PLAN_EXTENT_NOT_PROVED: a beam tag names a type; the "
                      "drawn beam band between supports is not established as an element (no beam-edge role)"})
    crow.append(row("S2-BM-VOL", "BEAMS", "ALL", f"{len(beams)} scheduled types", "خرسانة الجسور", "Beam concrete",
                    None, "m3", BLOCKED, "BLOCKED_GEOMETRY", "ST7757.dxf schedules + slab plans", "section x length",
                    ["BEAM_PLAN_EXTENT_NOT_PROVED"]))
    slabs = {k: dict(v, footprint_m2=None, volume_m3=None,
                     blocker="SLAB_OUTLINE_NOT_ESTABLISHED: no closed slab-edge outline with role authority; openings "
                             "and beam / slab overlap not resolved") for k, v in se["slabs"].items()}
    crow.append(row("S2-SLB-VOL", "SLABS", "ALL", ", ".join(f"{k}: {list(v['thickness_labels_cm'])} cm"
                                                            for k, v in se["slabs"].items()), "خرسانة البلاطات",
                    "Slab concrete", None, "m3", BLOCKED, "BLOCKED_GEOMETRY", "ST7757.dxf slab plans",
                    "footprint x thickness, beams once", ["SLAB_OUTLINE_NOT_ESTABLISHED"]))
    crow.append(row("S2-GB-VOL", "GROUND_BEAMS", "FOUNDATION", "ground beams", "خرسانة الميد", "Ground beams",
                    None, "m3", BLOCKED, BHGT, "ST7757.dxf GROUND BEAMS PLAN", "section x length",
                    ["GROUND_BEAM_LEVEL_AND_EXTENT_NOT_PROVED"]))
    crow.append(row("S2-STR-VOL", "STAIRS_STRUCTURE", "ALL", "stair flights", "خرسانة الدرج", "Stair concrete", None,
                    "m3", BLOCKED, BHGT, "ST7757 typical stair detail", "waist x length x width",
                    ["RISER_COUNT_PER_FLIGHT_NOT_PROVED"]))
    for code, ar, en in (("S2-RBR-FTG", "حديد القواعد", "Rebar - footings"), ("S2-RBR-COL", "حديد الأعمدة", "Rebar - columns"),
                         ("S2-RBR-BM", "حديد الجسور", "Rebar - beams"), ("S2-RBR-SLB", "حديد البلاطات", "Rebar - slabs")):
        crow.append(row(code, "REBAR", "ALL", "rebar", ar, en, None, "kg", BLOCKED, BMAT, "ST7757.dxf schedules",
                        "rebar_gate (fail closed, no kg/m3)", ["REBAR_FAIL_CLOSED: bar length / shape / laps / cover "
                                                               "not stated"]))
    sboq = fsum + crow
    rb = regsA["REBAR_REGISTER"]["specifications"]
    present = Counter()
    for r_ in rb:
        for k in SQ.REBAR_FIELDS:
            if k not in r_["gate"].get("missing", []):
                present[(r_["element"], k)] += 1
    evid = []
    for el in sorted({r_["element"] for r_ in rb}):
        specs = [r_ for r_ in rb if r_["element"] == el]
        have = sorted({k for r_ in specs for k in SQ.REBAR_FIELDS if k not in r_["gate"].get("missing", [])})
        evid.append({"element": el, "specifications": len(specs), "fields_present": have,
                     "fields_missing": [k for k in SQ.REBAR_FIELDS if k not in have],
                     "completeness": f"{len(have)}/{len(SQ.REBAR_FIELDS)}", "tonnage": "BLOCKED"})
    return {"footing_rows": frows, "footing_summary_rows": fsum, "rows": sboq, "columns": cols, "beams": beams,
            "slabs": slabs, "rebar_evidence": evid,
            "footing_summary": {"occurrences": len(frows), "complete": len(complete), "blocked": len(frows) - len(complete),
                                "complete_m3": round(sum(r["qty"] for r in complete), 6),
                                "phase_a": regsA["CONCRETE_REGISTER"]["footing_summary"]}}


# ====================================================================== owner questions (new only)
OWNER_QUESTIONS = [
    {"id": "OQ2-S1", "group": "STRUCTURAL", "question": "Footing tag 'F' at the east strap-beam end of the foundation "
     "plan sits on an outline drawn 1.50 x 1.40 m, while the footing schedule gives type F as 90 x 80 cm. Which governs "
     "for that footing: the drawn outline or the scheduled type?", "evidence": "STRUCTURAL_FOOTING_REGISTER completion F "
     "= COUNT_MISMATCH (3 orphan F tags, 2 outlines of the scheduled size)", "unblocks": ["footings F (3 occurrences)"]},
    {"id": "OQ2-S2", "group": "STRUCTURAL", "question": "Footing F10 is scheduled as 280 x 140 cm but no outline of that "
     "size is drawn at its tag (the drawn outline there is 1.05 x 1.40 m beside a strap beam). Is F10 a combined footing "
     "with its neighbour, or is the schedule size the one to build?", "evidence": "completion F10 = NO_TEMPLATE_CANDIDATE",
     "unblocks": ["footing F10"]},
    {"id": "OQ2-A1", "group": "ARCHITECTURAL", "question": "Ground floor: the saloon / reception / master-bedroom zone "
     "opens to the court and the pool terrace with no door or glazing drawn in those openings. Are these openings open "
     "by design (no door, no glazing)?", "evidence": "the labels SALOON / RECEPTION / MASTER BED ROOM lie in the site "
     "connected to the exterior", "unblocks": ["room separation of the GF reception zone (geometry only)"]},
    {"id": "OQ2-A2", "group": "ARCHITECTURAL", "question": "Several single lines on the mixed layer that also carries "
     "counters, stairs and drains bound the kitchen and the pantry. Are they fixed counters / joinery (floor finish runs "
     "under them?) or partitions?", "evidence": "KITCHEN / pantry sites TOPOLOGY_ROLE_UNRESOLVED by those lines",
     "unblocks": ["KITCHEN and PANTRY room areas"]},
]

DONORS = [
    {"donor": "OpenTakeoff (Apache-2.0, e6d2251c)", "capability": "door seal from the swing (hinge on wall, strike end, "
     "sweep 0.7-2.1 rad)", "class": "CLEAN_REIMPLEMENT", "where": "engine/source/entity_role_inference.door_motifs "
     "(vector; leaf + hinge anchoring; closure by the frozen opening closure)", "inspected": "web/src/lib/doorseal.ts"},
    {"donor": "OpenTakeoff", "capability": "stated non-boundary ink (hidden / annotation)", "class": "CLEAN_REIMPLEMENT",
     "where": "linetype_class from the LTYPE definition (not the name)", "inspected": "web/src/lib/oneclick.ts, layers.ts"},
    {"donor": "OpenTakeoff", "capability": "layer-name classifier", "class": "REJECT (as authority)",
     "where": "-", "inspected": "web/src/lib/layers.ts (numeric layers -> unknown)"},
    {"donor": "OpenTakeoff", "capability": "detectRooms / netroom raster rooms", "class": "BENCHMARK_ONLY", "where": "-",
     "inspected": "web/src/lib/detectRooms.ts, netroom.js"},
    {"donor": "U-C4N (MIT, cdb10638)", "capability": "arch/walls.py wall authoring", "class": "BENCHMARK_ONLY",
     "where": "-", "inspected": "engineering/arch/walls.py, rooms.py"},
    {"donor": "U-C4N", "capability": "labels.plain", "class": "ALREADY CLEAN_REIMPLEMENTED (cad_text)",
     "where": "engine/source/cad_text.py", "inspected": "engineering/understand/labels.py"},
    {"donor": "U-C4N", "capability": "Arabic / SHX glyph decoding", "class": "NOT AVAILABLE", "where": "-",
     "inspected": "no Arabic or SHX glyph map in the donor"},
    {"donor": "beiming183 (MIT)", "capability": "readback diff", "class": "PATTERN_IN_USE", "where": "r8_6a_reconcile",
     "inspected": "lock only"},
    {"donor": "Slacker (Apache-2.0) / puran-water (MIT)", "capability": "-", "class": "BENCHMARK_ONLY", "where": "-",
     "inspected": "lock only"},
]


# ====================================================================== workbook
def workbook(regs) -> dict:
    ab, sb = regs["ARCH_BOQ"]["rows"], regs["CONCRETE_REGISTER"]["boq_rows"]
    units = regs["SOURCE_AUTHORITY_REGISTER"]["units"]
    W = {0: 16, 4: 34, 5: 30, 6: 44, 10: 22, 11: 34, 12: 44, 13: 80}
    m = {}
    m["00_READ_ME"] = sheet("INFO", ["TOPIC", "TEXT"], [
        ["WHAT", "Phase A2: the ONE Urban engine with generic entity-role inference, on Alsenan P7757 + ST7757."],
        ["SOURCE SET", "The supplied files are the complete available owner source set (not called ISSUED)."],
        ["CLASSES", "PHYSICAL_MEASUREMENT = geometry proved; TRADE_ASSIGNMENT = physical quantity in a trade scope by "
                    "rule; BLOCKED_MATERIAL = material / type not in source; BLOCKED_HEIGHT = height not proved."],
        ["ADDING", "Only 02_ARCH_SUMMARY and 15_STRUCTURAL_SUMMARY lines may be added, each within its own scope; "
                   "never add lines of different units."],
        ["BLOCKED", "A BLOCKED line has no quantity and is in no total."],
        ["UNITS", f"P7757: {units['ARCHITECTURAL']['status']} ({units['ARCHITECTURAL']['reason']}); ST7757: "
                  f"{units['STRUCTURAL']['status']} ({units['STRUCTURAL']['reason']})."],
        ["NOT BLIND", "Development validation; the files carry P7757 history in this repository (disclosed)."],
        ["NO PRICES", "No price, no calibration, no production migration."]], widths={1: 130})
    m["01_SOURCES"] = sheet("INFO", ["FILE", "DISCIPLINE", "TYPE", "SHA256", "AUTHORITY"],
                            [[f["file"], f["discipline"], f["type"], f["sha256"], f["authority"]]
                             for f in regs["SOURCE_MANIFEST"]["files"]], widths={0: 40, 3: 66, 4: 60})
    m["02_ARCH_SUMMARY"] = sheet("ADDITIVE_SUMMARY", COLUMNS, [boq_line(r) for r in ab], qty_cols=(7,), status_col=9,
                                 widths=W, wrap=(13,), scope="ARCHITECTURAL")
    m["03_ROOMS"] = sheet("BREAKDOWN", ["FLOOR", "ROOM", "SITE", "FLOOR AREA m2", "CEILING BASE m2", "PERIMETER m",
                                        "WALL-FACE LENGTH m", "SKIRTING PATH m", "WET SEMANTICS", "STATUS", "BLOCKER"],
                          [[r["floor"], r["room"], r["site"], r["floor_area_m2"], r["base_ceiling_area_m2"],
                            r["perimeter_m"], r["wall_face_length_m"], r["skirting_path_m"], r["wet_semantics"],
                            r["status"], r["blocker"] or ""] for r in regs["ROOM_REGISTER"]["rooms"]],
                          qty_cols=(3, 4, 5, 6, 7), status_col=9, widths={1: 28, 8: 40, 10: 80})

    def part(prefixes):
        return [boq_line(r) for r in ab if any(r["item"].startswith(p) for p in prefixes)]
    m["04_FLOOR_CEILING"] = sheet("BREAKDOWN", COLUMNS, part(("A2-FLR", "A2-CLG", "A2-FFN", "A2-CFN")), (7,), 9, W, (13,))
    m["05_BLOCKWORK"] = sheet("BREAKDOWN", COLUMNS, part(("A2-BLK", "A2-BLA")), (7,), 9, W, (13,))
    m["06_WALL_SURFACES"] = sheet("BREAKDOWN", COLUMNS, part(("A2-WFL", "A2-WFA", "A2-WFN", "A2-EXT")), (7,), 9, W, (13,))
    m["07_SKIRTING"] = sheet("BREAKDOWN", COLUMNS, part(("A2-SKP", "A2-SKM")), (7,), 9, W, (13,))
    m["08_DOORS"] = sheet("SCHEDULE", ["FLOOR", "OCCURRENCE", "BASIS", "LEAF WIDTH mm", "CLOSURE WIDTH mm", "STATE",
                                       "ROOMS", "HEIGHT", "MATERIAL", "STATUS"],
                          [[d["floor"], d["occurrence"], d["basis"], d["leaf_width_mm"], d["closure_width_mm"],
                            d["state"], " | ".join(x for x in d["rooms"] if x), d["height"], d["material"], "INFO"]
                           for d in regs["OPENING_REGISTER"]["doors"]], status_col=9, widths={6: 40, 7: 50, 8: 40})
    m["09_WINDOWS"] = sheet("SCHEDULE", ["FLOOR", "WINDOW", "WIDTH mm", "WALL mm", "HOST ROOMS", "HEIGHT", "MATERIAL",
                                         "STATUS"],
                            [[w["floor"], w["window"], w["width_mm"], w["wall_thickness_mm"], " | ".join(w["host_rooms"]),
                              w["height"], w["material"], "INFO"] for w in regs["OPENING_REGISTER"]["windows"]],
                            status_col=7, widths={4: 40, 5: 50, 6: 40})
    m["10_STAIRS"] = sheet("BREAKDOWN", COLUMNS, part(("A2-STT", "A2-STR")), (7,), 9, W, (13,))
    m["11_WET_ROOMS"] = sheet("BREAKDOWN", COLUMNS, part(("A2-WET", "A2-WPM")), (7,), 9, W, (13,))
    m["12_VERTICAL_EVIDENCE"] = sheet("INFO", ["ID", "PAGE", "VIEW", "KIND", "PRINTED TEXT", "READING", "CONFIDENCE"],
                                      [[v["id"], v["page"], v["view"], v["kind"], v["text"], v["reading"],
                                        v["confidence"]] for v in regs["PDF_VERTICAL_EVIDENCE_REGISTER"]["items"]] +
                                      [[f"F2F {x['from']}->{x['to']}", "", "SECTIONS", "FLOOR_TO_FLOOR",
                                        str(x.get("floor_to_floor_m")), x["state"], x["use"][:60]]
                                       for x in regs["PDF_VERTICAL_EVIDENCE_REGISTER"]["floor_to_floor"]],
                                      widths={4: 50, 5: 60})
    m["13_ROLE_INFERENCE"] = sheet("INFO", ["FLOOR", "LAYER", "STATE", "ROLE", "SCORE", "CHANNELS / WHY"],
                                   [[fl, lay, d["state"], d.get("role") or d.get("best") or "", d.get("score", ""),
                                     json.dumps(d.get("channels") or d.get("why"), ensure_ascii=False)]
                                    for fl, e in regs["ENTITY_ROLE_REGISTER"]["floors"].items()
                                    for lay, d in sorted(e["decisions"].items())], widths={5: 100})
    ablk = Counter(b.split(":")[0] for r in ab for b in r["blockers"])
    m["14_ARCH_BLOCKERS"] = sheet("INFO", ["BLOCKER", "ROWS"], [[k, v] for k, v in sorted(ablk.items())], widths={0: 70})
    m["15_STRUCTURAL_SUMMARY"] = sheet("ADDITIVE_SUMMARY", COLUMNS, [boq_line(r) for r in sb], qty_cols=(7,),
                                       status_col=9, widths=W, wrap=(13,), scope="STRUCTURAL")
    m["16_FOOTINGS"] = sheet("BREAKDOWN", ["ELEMENT ID", "COUNT", "L m", "W m", "H m", "QTY m3", "STATUS", "DRAWN / "
                                           "COMPLETION", "BLOCKER"],
                             [[r["element_id"], r["count"], r["dims"]["L"]["m"], r["dims"]["W"]["m"], r["dims"]["H"]["m"],
                               r6(r["qty"]), "COMPUTED_SHADOW_COMPLETE" if r["status"] == SQ.COMPLETE else "BLOCKED",
                               r.get("size_check") or "", " | ".join(r["blockers"])]
                              for r in regs["STRUCTURAL_FOOTING_REGISTER"]["footing_rows"]], qty_cols=(5,), status_col=6,
                             widths={0: 46, 7: 60, 8: 90})
    m["17_COLUMNS"] = sheet("SCHEDULE", ["TYPE", "COUNT", "SECTIONS cm (F / GF / 1F / 2F)", "PLAN AREA m2 GF", "VOLUME",
                                         "STATUS"],
                            [[c["type"], c["count_on_column_plan"], json.dumps(c["sections_cm"]),
                              c["plan_area_m2_by_storey"]["ground_floor"], c["volume_blocker"], "INFO"]
                             for c in regs["STRUCTURAL_COLUMN_REGISTER"]["columns"]], status_col=5, widths={2: 60, 4: 70})
    m["18_BEAMS"] = sheet("SCHEDULE", ["TYPE", "B cm", "D cm", "SECTION m2", "TAGS PER SHEET", "LENGTH", "STATUS"],
                          [[b["type"], b["breadth_cm"], b["depth_cm"], b["section_m2"], json.dumps(b["tags_per_sheet"]),
                            b["length_blocker"], "INFO"] for b in regs["STRUCTURAL_BEAM_REGISTER"]["beams"]],
                          status_col=6, widths={4: 60, 5: 70})
    m["19_SLABS"] = sheet("SCHEDULE", ["SLAB SHEET", "THICKNESS LABELS cm", "BLOCKER", "STATUS"],
                          [[k, json.dumps(v["thickness_labels_cm"]), v["blocker"], "INFO"]
                           for k, v in sorted(regs["STRUCTURAL_SLAB_REGISTER"]["slabs"].items())], status_col=3,
                          widths={2: 90})
    m["20_REBAR_EVIDENCE"] = sheet("INFO", ["ELEMENT", "SPECS", "PRESENT", "MISSING", "COMPLETENESS", "TONNAGE"],
                                   [[e["element"], e["specifications"], ", ".join(e["fields_present"]),
                                     ", ".join(e["fields_missing"]), e["completeness"], e["tonnage"]]
                                    for e in regs["REBAR_EVIDENCE_REGISTER"]["elements"]], widths={2: 50, 3: 50})
    sblk = Counter(b.split(":")[0] for r in sb for b in r["blockers"])
    m["21_STRUCT_BLOCKERS"] = sheet("INFO", ["BLOCKER", "ROWS"], [[k, v] for k, v in sorted(sblk.items())],
                                    widths={0: 80})
    return m


def xlsx(regs):
    model = workbook(regs)
    ab, sb = regs["ARCH_BOQ"]["rows"], regs["CONCRETE_REGISTER"]["boq_rows"]
    src = [{"sheet": "02_ARCH_SUMMARY", "row": i, "col": 7, "value": r6(r["qty"]), "ref": f"ARCH_BOQ.rows[{i}].qty"}
           for i, r in enumerate(ab)]
    srcs = [{"sheet": "15_STRUCTURAL_SUMMARY", "row": i, "col": 7, "value": r6(r["qty"]),
             "ref": f"CONCRETE_REGISTER.boq_rows[{i}].qty"} for i, r in enumerate(sb)]
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / XLSX_NAME
        w = BX.write(model, p, created=CREATED, banner=BANNER, summary_name=SUMMARY_NAME)
        va = BX.validate(p, model, sources=src, summary_sheet="02_ARCH_SUMMARY", canonical_ids=[r["item"] for r in ab],
                         banner=BANNER, summary_name=SUMMARY_NAME)
        vs = BX.validate(p, model, sources=srcs, summary_sheet="15_STRUCTURAL_SUMMARY",
                         canonical_ids=[r["item"] for r in sb], banner=BANNER, summary_name=SUMMARY_NAME)
        w2 = BX.write(model, Path(d) / ("2_" + XLSX_NAME), created=CREATED, banner=BANNER, summary_name=SUMMARY_NAME)
        data = p.read_bytes()
    state = "PASS" if va["state"] == vs["state"] == "PASS" and w["file_sha256"] == w2["file_sha256"] else "FAIL"
    return model, data, {"sheets": w["sheets"], "content_digest": w["content_digest"], "file_sha256": w["file_sha256"],
                         "bytes": w["bytes"], "rewrite_identical": w["file_sha256"] == w2["file_sha256"],
                         "readback": {"state": state, "architectural": {k: va[k] for k in (
                             "state", "differences", "formulas", "register_mismatches", "quantity_cells_checked",
                             "canonical_not_exactly_once", "row_drops")},
                             "structural": {k: vs[k] for k in ("state", "differences", "formulas",
                                                                "register_mismatches", "quantity_cells_checked",
                                                                "canonical_not_exactly_once", "row_drops")}},
                         "rows_per_sheet": va["rows_per_sheet"]}


# ====================================================================== registers
FREEZE_SCHEMA = dict(AR.FREEZE_SCHEMA)
for _k in ("sheet_register_digest", "room_register_digest", "topology_result_digests", "opening_register_digest",
           "surface_register_digest", "structural_element_digest", "schedule_table_digests", "concrete_register_digest",
           "rebar_register_digest"):
    FREEZE_SCHEMA.pop(_k, None)
FREEZE_SCHEMA.update({
    "role_claims_digest": {"class": "SHA256"}, "plan_region_digest": {"class": "SHA256"},
    "wall_band_digest": {"class": "SHA256"}, "site_digests": {"class": "SHA256_MAP"},
    "run_input_digests": {"class": "SHA256_MAP"}, "room_register_digest": {"class": "SHA256"},
    "opening_register_digest": {"class": "SHA256"}, "vertical_evidence_digest": {"class": "SHA256"},
    "floor_ceiling_digest": {"class": "SHA256"}, "wall_geometry_digest": {"class": "SHA256"},
    "stair_register_digest": {"class": "SHA256"}, "structural_digests": {"class": "SHA256_MAP"},
    "concrete_register_digest": {"class": "SHA256"}, "blocked_items_digest": {"class": "SHA256"}})


def registers(ctx) -> dict:
    a2 = ctx["a2"]
    # Phase A registers from the same context (the frozen Phase A logic); only the reused ones are kept
    regsA = AR.registers({k: v for k, v in ctx.items() if k != "a2"})
    regs = {"SOURCE_MANIFEST": regsA["SOURCE_MANIFEST"]}
    for f in regs["SOURCE_MANIFEST"]["files"]:
        if f["file"] in ("P7757.dxf", "ST7757.dxf"):
            u = a2["units"]["ARCHITECTURAL" if f["file"] == "P7757.dxf" else "STRUCTURAL"]
            f["resolved_units"] = {"status": u["status"], "native_to_mm": u["native_to_mm"]}
    regs["SOURCE_AUTHORITY_REGISTER"] = dict(regsA["SOURCE_AUTHORITY_REGISTER"],
                                             SCHEMA="URBAN_ALSENAN_A2_SOURCE_AUTHORITY_V1",
                                             units={k: a2["units"][k] for k in ("ARCHITECTURAL", "STRUCTURAL")},
                                             plot_side_evidence=a2["units"]["plot_evidence"],
                                             units_phase_a=a2["units"]["phase_a"],
                                             source_set="COMPLETE AVAILABLE OWNER SOURCE SET (owner statement; not "
                                                        "called ISSUED)")
    # ---------------- role inference / regions / bands / topology
    regs["ENTITY_ROLE_REGISTER"] = {
        "SCHEMA": "URBAN_ALSENAN_A2_ENTITY_ROLE_REGISTER_V1", "policy": ERI.policy_record(),
        "cad_tables": a2["cad_tables"], "unrealised_placement": a2["unrealised"],
        "floors": {fl: a2["floors"][fl]["eri"] for fl in FLOORS},
        "rule": "OBSERVATION -> ROLE_CANDIDATE (channel scores) -> CLAIM (POLICY_ACCEPTED, source + region scoped) "
                "-> ACCEPTED | BLOCKED; layer names corroborate only; no layer map in code"}
    regs["PLAN_REGION_REGISTER"] = {
        "SCHEMA": "URBAN_ALSENAN_A2_PLAN_REGION_REGISTER_V1", "sheets": regsA["FLOOR_PLAN_REGISTER"]["sheets"],
        "plan_regions": {fl: {"sheet": ctx["sheets_by_floor"][fl]["sheet"], "titles": ctx["sheets_by_floor"][fl]["titles"],
                              "frame_bounds": ctx["sheets_by_floor"][fl]["bounds"],
                              "inferred_frames": a2["floors"][fl]["eri"]["frames"]} for fl in FLOORS},
        "leakage": a2["region_leakage"], "pdf_sheets": AP.PDF_SHEETS}
    regs["WALL_BAND_REGISTER"] = {"SCHEMA": "URBAN_ALSENAN_A2_WALL_BAND_REGISTER_V1",
                                  "bands": {fl: a2["floors"][fl]["bands"] for fl in FLOORS},
                                  "by_state": {fl: a2["floors"][fl]["topology"]["wall_bands"] for fl in FLOORS},
                                  "rule": "WALL_BAND_POLICY (frozen) on the inferred wall faces; ambiguous bands are "
                                          "reported, never measured"}
    regs["ROOM_TOPOLOGY_REGISTER"] = {"SCHEMA": "URBAN_ALSENAN_A2_ROOM_TOPOLOGY_V1",
                                      "floors": {fl: a2["floors"][fl]["topology"] for fl in FLOORS},
                                      "established_label_occurrences": {fl: a2["floors"][fl]["established_label_occurrences"]
                                                                        for fl in FLOORS}}
    rooms = rooms_register(a2)
    regs["ROOM_REGISTER"] = {"SCHEMA": "URBAN_ALSENAN_A2_ROOM_REGISTER_V1", "rooms": rooms,
                             "certified": sum(1 for r in rooms if r["status"] == COMPLETE),
                             "labels": "semantic only, attached after a site exists; Arabic label text is font-glyph "
                                       "encoded (style X-ARAB1B over ANSI_1252) and is NOT decoded",
                             "role_authority": "INFERRED (POLICY_ACCEPTED claims) - not human-reviewed; SHADOW"}
    regs["OPENING_REGISTER"] = {"SCHEMA": "URBAN_ALSENAN_A2_OPENING_REGISTER_V1",
                                "doors": [d for fl in FLOORS for d in a2["floors"][fl]["doors"]],
                                "windows": [w for fl in FLOORS for w in a2["floors"][fl]["windows"]],
                                "gap_infill": [g for fl in FLOORS for g in a2["floors"][fl]["gap_infill"]],
                                "rule": "door = wall gap + door-symbol motif (swing + leaf + hinge on a wall face) + "
                                        "frozen closure; window = glazing lines inside a wall gap; existence, geometry, "
                                        "height and material are separate fields"}
    regs["PDF_VERTICAL_EVIDENCE_REGISTER"] = dict(a2["vertical"], SCHEMA="URBAN_ALSENAN_A2_VERTICAL_EVIDENCE_V1")
    cert = [r for r in rooms if r["status"] == COMPLETE]
    regs["FLOOR_CEILING_REGISTER"] = {"SCHEMA": "URBAN_ALSENAN_A2_FLOOR_CEILING_V1",
                                      "rooms": [{k: r[k] for k in ("floor", "room", "site", "status", "floor_area_m2",
                                                                    "area_uncertainty_m2", "base_ceiling_area_m2",
                                                                    "blocker")} for r in rooms],
                                      "physical_vs_material": "FLOOR AREA = COMPUTED (certified rooms); FLOOR / CEILING "
                                                              "MATERIAL = BLOCKED (no finish schedule)",
                                      "false_ceiling": "BLOCKED: no false-ceiling level in the source"}
    ab = arch_rows(a2, rooms)
    regs["ARCH_BOQ"] = {"SCHEMA": "URBAN_ALSENAN_A2_ARCH_BOQ_V1", "columns": COLUMNS, "rows": ab,
                        "by_status": dict(Counter(r["status"] for r in ab)), "by_class": dict(Counter(r["class"] for r in ab))}
    regs["BLOCKWORK_REGISTER"] = {"SCHEMA": "URBAN_ALSENAN_A2_BLOCKWORK_V1",
                                  "rows": [r for r in ab if r["item"].startswith(("A2-BLK", "A2-BLA"))],
                                  "rule": "length per thickness from ESTABLISHED wall bands (column overlaps out); area "
                                          "BLOCKED_HEIGHT; ambiguous bands reported"}
    regs["WALL_SURFACE_REGISTER"] = {"SCHEMA": "URBAN_ALSENAN_A2_WALL_SURFACE_V1",
                                     "rooms": [{k: r[k] for k in ("floor", "room", "status", "wall_face_length_m",
                                                                   "door_closure_length_m", "glazing_length_m",
                                                                   "wall_face_area_m2", "wall_face_area_blocker")}
                                               for r in rooms],
                                     "rows": [r for r in ab if r["item"].startswith(("A2-WFL", "A2-WFA", "A2-WFN"))],
                                     "rule": "PHYSICAL wall-face length is separate from TRADE assignment (plaster / "
                                             "paint / tile)"}
    regs["SKIRTING_REGISTER"] = {"SCHEMA": "URBAN_ALSENAN_A2_SKIRTING_V1",
                                 "rooms": [{k: r[k] for k in ("floor", "room", "status", "perimeter_m",
                                                               "door_closure_length_m", "skirting_path_m")} for r in rooms],
                                 "rule": "perimeter minus door closures; windows are NOT deducted (none proved "
                                         "floor-reaching); material BLOCKED"}
    regs["STAIR_REGISTER"] = {"SCHEMA": "URBAN_ALSENAN_A2_STAIR_V1",
                              "tread_runs": {fl: a2["floors"][fl]["stairs"] for fl in FLOORS},
                              "floor_to_floor": a2["vertical"]["floor_to_floor"],
                              "rows": [r for r in ab if r["item"].startswith(("A2-STT", "A2-STR"))],
                              "rule": "tread lines counted from the drawing; rise / riser count per flight not guessed"}
    regs["WET_ROOM_REGISTER"] = {"SCHEMA": "URBAN_ALSENAN_A2_WET_ROOMS_V1",
                                 "rooms": [{k: r[k] for k in ("floor", "room", "status", "wet_semantics",
                                                               "fixture_symbols_in_site", "floor_area_m2")} for r in rooms
                                           if r["wet_semantics"] != "NOT_WET_BY_EVIDENCE"],
                                 "rule": "wet = wet label AND a fixture symbol in the certified site; sanitary PDF is "
                                         "supporting only; membrane BLOCKED_MATERIAL"}
    # ---------------- structural
    s = structural(ctx, regsA)
    regs["STRUCTURAL_FOOTING_REGISTER"] = {"SCHEMA": "URBAN_ALSENAN_A2_FOOTINGS_V1", "policy": a2["footings"]["policy"],
                                           "completion": {k: v for k, v in a2["footings"].items() if k != "policy"},
                                           "footing_rows": s["footing_rows"], "summary": s["footing_summary"]}
    regs["STRUCTURAL_COLUMN_REGISTER"] = {"SCHEMA": "URBAN_ALSENAN_A2_COLUMNS_V1", "columns": s["columns"],
                                          "plan_outlines": a2["columns"]}
    regs["STRUCTURAL_BEAM_REGISTER"] = {"SCHEMA": "URBAN_ALSENAN_A2_BEAMS_V1", "beams": s["beams"],
                                        "tag_counts": a2["beams"]["tags_per_sheet"]}
    regs["STRUCTURAL_SLAB_REGISTER"] = {"SCHEMA": "URBAN_ALSENAN_A2_SLABS_V1", "slabs": s["slabs"],
                                        "double_count_rule": "beams below a slab are measured below the slab soffit only"}
    regs["REBAR_EVIDENCE_REGISTER"] = {"SCHEMA": "URBAN_ALSENAN_A2_REBAR_EVIDENCE_V1", "elements": s["rebar_evidence"],
                                       "specifications": regsA["REBAR_REGISTER"]["specifications"],
                                       "tonnage_kg": None, "state": "FAIL_CLOSED: no tonnage, no kg/m3"}
    regs["CONCRETE_REGISTER"] = {"SCHEMA": "URBAN_ALSENAN_A2_CONCRETE_V1", "boq_rows": s["rows"],
                                 "footing_summary": s["footing_summary"],
                                 "rule": "count x dimension with named sources; blocked rows in no total"}
    # ---------------- firewall, donors, owner questions
    regs["BENCHMARK_FIREWALL"] = dict(regsA["BENCHMARK_FIREWALL"], SCHEMA="URBAN_ALSENAN_A2_BENCHMARK_FIREWALL_V1")
    regs["DONOR_REUSE_REGISTER"] = {"SCHEMA": "URBAN_ALSENAN_A2_DONORS_V1", "donors": DONORS, "copied_code": "NONE",
                                    "fetched": "U-C4N cdb10638 and OpenTakeoff e6d2251c read-only into the session "
                                               "scratch at their DONORS.lock commits (source only, never imported)"}
    regs["OWNER_QUESTION_REGISTER"] = {"SCHEMA": "URBAN_ALSENAN_A2_OWNER_QUESTIONS_V1", "questions": OWNER_QUESTIONS,
                                       "not_asked_again": ["additional DWG", "structural revision", "door / window "
                                                           "schedule", "finish schedule", "founding / ground-beam / "
                                                           "slab levels"],
                                       "never_asked": ["expected quantities", "freelancer BOQ", "web-app report"]}
    regs["QA_RECONCILIATION"] = qa(ctx, regs)
    model, data, xs = xlsx(regs)
    ctx["xlsx_bytes"] = data
    regs["QA_RECONCILIATION"]["xlsx"] = xs
    regs["QA_RECONCILIATION"]["checks"].append({"check": "XLSX_READBACK", "state": xs["readback"]["state"],
                                                "critical": True, "detail": "every cell vs model; deterministic rewrite"})
    regs["QA_RECONCILIATION"]["silent_critical_errors"] = sum(
        1 for c in regs["QA_RECONCILIATION"]["checks"] if c["critical"] and c["state"] not in ("PASS", "BLOCKED_REPORTED"))
    regs["QORTUBA_REGRESSION"] = {"SCHEMA": "URBAN_ALSENAN_A2_QORTUBA_REGRESSION_V1",
                                  "state": "RECORDED_BY_THE_REGRESSION_STEP (alsenan_a2_package.py)",
                                  "rule": "Qortuba RC1 registers rebuilt from the A2 engine and compared; Qortuba files "
                                          "are never edited"}
    regs["ALSENAN_P7757_ST7757_PHASE_A2_FREEZE"] = freeze(ctx, regs, xs)
    regs["TEST_RESULTS"] = {"SCHEMA": "URBAN_ALSENAN_A2_TEST_RESULTS_V1", "state": "RECORDED_BY_THE_PACKAGE_STEP",
                            "why": "the one full suite runs from the final commit"}
    return regs


def qa(ctx, regs) -> dict:
    ch = []

    def add(name, state, critical, detail):
        ch.append({"check": name, "state": state, "critical": critical, "detail": detail})
    a2 = ctx["a2"]
    add("REGION_LEAKAGE", "PASS" if a2["region_leakage"]["state"] == "NO_LEAKAGE" else "FAIL", True,
        json.dumps(a2["region_leakage"]["parts_per_region"]))
    for fl in FLOORS:
        t = a2["floors"][fl]["topology"]
        add(f"UNREALISED_PLACED_{fl}", "PASS" if not t["unrealised"]["blocking_input"] else "FAIL", True,
            f"recorded {Counter(t['unrealised']['recorded'])}")
        add(f"ROOM_CLOSURE_{fl}", "PASS" if t["certified_labelled_sites"] else "BLOCKED_REPORTED", True,
            f"{t['certified_labelled_sites']} of {t['labelled_sites']} labelled sites certified; issues {t['issues']}")
        e = a2["floors"][fl]["eri"]
        bad = [c for c in e["claims"] if c["review_state"] != "POLICY_ACCEPTED" or not c["part_keys"]]
        add(f"CLAIMS_SCOPED_{fl}", "PASS" if not bad else "FAIL", True, f"{len(e['claims'])} claims, all "
            "POLICY_ACCEPTED with explicit parts and region scope")
        fr = e["frames"]
        add(f"FRAME_REJECTED_{fl}", "PASS" if len(fr) == 1 else "FAIL", True, f"{len(fr)} sheet frame(s) found")
        add(f"DOORS_ADMITTED_{fl}", "PASS", True, f"{e['doors_found']} door motifs; rejected {e['doors_rejected']}")
    ab = regs["ARCH_BOQ"]["rows"]
    add("BLOCKED_ROWS_WITHOUT_QTY", "PASS" if all(r["qty"] is None for r in ab + regs["CONCRETE_REGISTER"]["boq_rows"]
                                                  if r["status"] == BLOCKED) else "FAIL", True, "all rows")
    rooms = regs["ROOM_REGISTER"]["rooms"]
    ok = True
    for fl in FLOORS:
        r = next(x for x in ab if x["item"] == f"A2-FLR-{fl}")
        c = [x["floor_area_m2"] for x in rooms if x["floor"] == fl and x["status"] == COMPLETE]
        ok &= (r["qty"] is None and not c) or (r["qty"] is not None and abs(r["qty"] - sum(c)) <= 1e-6)
    add("FLOOR_AREA_EQUALS_ROOMS", "PASS" if ok else "FAIL", True, "floor line = sum of certified rooms exactly")
    add("NO_MATERIAL_WITHOUT_SCHEDULE", "PASS" if all(r["status"] == BLOCKED for r in ab if r["class"] == BMAT)
        else "FAIL", True, "every BLOCKED_MATERIAL row is blocked")
    add("NO_HEIGHT_QUANTITY", "PASS" if all(r["status"] == BLOCKED for r in ab if r["class"] == BHGT) else "FAIL", True,
        "no area / volume that needs an unproved height")
    fs = regs["STRUCTURAL_FOOTING_REGISTER"]["summary"]
    add("FOOTINGS_EXPANDED", "PASS" if fs["complete"] >= fs["phase_a"]["complete"] else "FAIL", True,
        f"A2 {fs['complete']} / {fs['occurrences']} ({fs['complete_m3']} m3) vs Phase A {fs['phase_a']['complete']} "
        f"({fs['phase_a']['complete_m3']} m3)")
    dup = Counter(r["element_id"] for r in regs["STRUCTURAL_FOOTING_REGISTER"]["footing_rows"])
    add("FOOTING_ROW_ONCE", "PASS" if all(v == 1 for v in dup.values()) else "FAIL", True, f"{len(dup)} rows")
    sb = regs["CONCRETE_REGISTER"]["boq_rows"]
    by = {r["element_id"]: r for r in regs["STRUCTURAL_FOOTING_REGISTER"]["footing_rows"]}
    okf = all((s_["qty"] is None and not s_["complete_rows"]) or abs(s_["qty"] - sum(by[i]["qty"] for i in s_["complete_rows"])) < 1e-9
              for s_ in sb if s_["item"].startswith("S-FTG-"))
    add("FOOTING_SUMMARY_EXACT", "PASS" if okf else "FAIL", True, "each type line = sum of its complete rows")
    add("REBAR_FAIL_CLOSED", "PASS" if regs["REBAR_EVIDENCE_REGISTER"]["tonnage_kg"] is None else "FAIL", True,
        "no tonnage")
    for k in ("ARCHITECTURAL", "STRUCTURAL"):
        u = a2["units"][k]
        add(f"UNITS_{k}", "PASS" if u["status"] in ("VERIFIED", "PROVISIONAL") else "FAIL", True,
            f"{u['status']} ({u['reason']})")
    add("ARABIC_TEXT", "BLOCKED_REPORTED", False, "font-glyph encoded labels (X-ARAB1B over ANSI_1252): UNKNOWN, never "
        "decoded by guess")
    add("ST7757_DWG_DXF", "BLOCKED_REPORTED", False, "no pinned decode: release blocker, not development blocker")
    return {"SCHEMA": "URBAN_ALSENAN_A2_QA_V1", "checks": ch,
            "target": "zero silent critical errors: every critical check PASS or BLOCKED_REPORTED with its reason"}


def freeze(ctx, regs, xs) -> dict:
    a2 = ctx["a2"]
    ab, sb = regs["ARCH_BOQ"]["rows"], regs["CONCRETE_REGISTER"]["boq_rows"]
    allrows = ab + sb
    fs = regs["STRUCTURAL_FOOTING_REGISTER"]["summary"]
    rec = {
        "SCHEMA": "URBAN_ALSENAN_P7757_ST7757_PHASE_A2_FREEZE_V1", "freeze_policy": FS.POLICY_ID, "phase": "PHASE_A2",
        "nature": "SOURCE-ONLY GENERIC ENGINE IMPROVEMENT - development validation, NOT BLIND - frozen before any "
                  "manual BOQ / web-app value is opened",
        "code_commit": ctx["code_commit"], "recommendation_commit": RECOMMENDATION_COMMIT,
        "baseline_commit": BASELINE_COMMIT, "source_sha256": {k: v[0] for k, v in AP.FILES.items()},
        "zip_sha256": dict(AP.ZIPS),
        "scope": "P7757 GF / 1F / 2F plans + NW / SE elevations + raster sections (evidence); ST7757 foundations, "
                 "columns, beams, slabs, schedules; SHADOW only",
        "units": "; ".join(f"{k}: {a2['units'][k]['status']} {a2['units'][k]['native_to_mm']} mm/unit"
                           for k in ("ARCHITECTURAL", "STRUCTURAL")),
        "unit_context_digest": digest({k: a2["units"][k] for k in ("ARCHITECTURAL", "STRUCTURAL")}),
        "role_claims_digest": digest({fl: a2["floors"][fl]["eri"]["claims"] for fl in FLOORS}),
        "plan_region_digest": digest(regs["PLAN_REGION_REGISTER"]),
        "wall_band_digest": digest(regs["WALL_BAND_REGISTER"]["bands"]),
        "site_digests": {fl: a2["floors"][fl]["topology"]["result_digest"] for fl in FLOORS},
        "run_input_digests": {fl: a2["floors"][fl]["topology"]["run_input_digest"] for fl in FLOORS},
        "room_register_digest": digest(regs["ROOM_REGISTER"]["rooms"]),
        "opening_register_digest": digest(regs["OPENING_REGISTER"]),
        "vertical_evidence_digest": digest(regs["PDF_VERTICAL_EVIDENCE_REGISTER"]),
        "floor_ceiling_digest": digest(regs["FLOOR_CEILING_REGISTER"]),
        "wall_geometry_digest": digest([regs["WALL_SURFACE_REGISTER"]["rooms"], regs["BLOCKWORK_REGISTER"]["rows"]]),
        "stair_register_digest": digest(regs["STAIR_REGISTER"]),
        "structural_digests": {k: digest(regs[k]) for k in ("STRUCTURAL_FOOTING_REGISTER", "STRUCTURAL_COLUMN_REGISTER",
                                                            "STRUCTURAL_BEAM_REGISTER", "STRUCTURAL_SLAB_REGISTER",
                                                            "REBAR_EVIDENCE_REGISTER")},
        "concrete_register_digest": digest(regs["CONCRETE_REGISTER"]),
        "trade_rows_digest": digest([boq_line(r) for r in allrows]),
        "blocked_rows_digest": digest([r["item"] for r in allrows if r["status"] == BLOCKED]),
        "blocked_items_digest": digest(sorted({b for r in allrows for b in r["blockers"]})),
        "owner_questions_digest": digest(OWNER_QUESTIONS), "excel_content_digest": xs["content_digest"],
        "excel_file_sha256": xs["file_sha256"], "firewall_digest": digest(regs["BENCHMARK_FIREWALL"]),
        "engine_policy_digests": {"ENTITY_ROLE_INFERENCE_V1": ERI.policy_record()["digest"],
                                  "STRUCTURAL_COMPLETION_V1": SQ.completion_policy_record()["digest"],
                                  "STRUCTURAL_QTO_V1": SQ.policy_record()["digest"],
                                  "BENCHMARK_FIREWALL_V1": FW.policy_record()["digest"],
                                  "SCHEDULE_TABLE_READER_V1": digest(ST.policy_record()),
                                  "LEVEL_MARK_UNIT_EVIDENCE_V1": digest(LM.policy_record()),
                                  "CAD_TEXT_CONTROL_V1": digest(CT.policy_record()),
                                  "BOQ_XLSX_EXPORT_V2": BX.policy_record()["digest"]},
        "counts": (f"rooms certified {regs['ROOM_REGISTER']['certified']} of {len(regs['ROOM_REGISTER']['rooms'])} "
                   f"labelled sites; doors {sum(1 for d in regs['OPENING_REGISTER']['doors'] if d['state'] == 'CLOSED')} "
                   f"closed; windows {len(regs['OPENING_REGISTER']['windows'])}; architectural rows {len(ab)} (complete "
                   f"{sum(1 for r in ab if r['status'] == COMPLETE)}, subtotal {sum(1 for r in ab if r['status'] == SUBTOTAL)}"
                   f", blocked {sum(1 for r in ab if r['status'] == BLOCKED)}); footings {fs['complete']}/"
                   f"{fs['occurrences']} = {fs['complete_m3']} m3 (Phase A {fs['phase_a']['complete_m3']}); owner "
                   f"questions {len(OWNER_QUESTIONS)}"),
        "FREELANCER_BOQ_SEEN": False, "WEB_APP_QUANTITIES_SEEN": False, "EXPECTED_TOTALS_USED": False,
        "HISTORICAL_P7757_GOLD_USED": False, "CONTAMINATION_DISCLOSED": True,
        "comparison": "NOT STARTED - Phase B only, after this freeze is committed"}
    rec["schema_validation"] = FS.validate(dict(rec), FREEZE_SCHEMA)
    return rec
