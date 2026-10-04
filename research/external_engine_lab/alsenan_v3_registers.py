"""ALSENAN V3 registers - one canonical BOQ model (BOQ_LINES) plus the supporting registers. Every workbook and both
PDFs render from BOQ_LINES; nothing downstream computes a quantity.

Line: {trade, level, group, code, desc_en, desc_ar, unit, qty, status, formula, authority, trace, details[]}
  status COMPUTED (in totals) | PARTIAL (computed part in totals, the rest listed) | REVIEW (shown, not in totals) |
         BLOCKED (no quantity; reason) | NOT_IN_SOURCE (evidence that the scope does not exist)
Levels: GF (incl. substructure) | 1F | 2F_ROOF | OTHER_EXTERNAL.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict

LEVELS = ("GF", "1F", "2F_ROOF", "OTHER_EXTERNAL")
LEVEL_NAME = {"GF": ("GROUND FLOOR (incl. substructure)", "الدور الأرضي (مع الأساسات)"),
              "1F": ("FIRST FLOOR", "الدور الأول"), "2F_ROOF": ("SECOND FLOOR + ROOF", "الدور الثاني والسطح"),
              "OTHER_EXTERNAL": ("OTHER + EXTERNAL", "أخرى وخارجي")}
TRADES = [
    ("01", "CONCRETE", "الخرسانة", "m3"), ("02", "REBAR", "حديد التسليح", "kg"),
    ("03", "BLOCKWORK", "الطابوق", "m2"), ("04", "PLASTER_PAINT", "اللياسة والدهان", "m2"),
    ("05", "FLOORING_PORCELAIN", "الأرضيات (بورسلان)", "m2"), ("06", "CEILINGS", "الأسقف", "m2"),
    ("07", "WALL_TILE_WATERPROOFING", "تكسيات الجدران والعزل المائي", "m2"),
    ("08", "ALUMINIUM_OPENINGS", "الألمنيوم والفتحات", "nr"), ("09", "STAIRS_RAILINGS", "الدرج والدرابزين", "lm")]
IN_TOTAL = ("COMPUTED", "PARTIAL")
FL2LV = {"GF": "GF", "1F": "1F", "2F": "2F_ROOF", "FOUNDATION": "GF"}


def _r(v, n=3):
    return None if v is None else round(float(v), n)


def strip(o):
    if isinstance(o, dict):
        return {k: strip(v) for k, v in o.items() if not str(k).startswith("_")}
    if isinstance(o, (list, tuple)):
        return [strip(v) for v in o]
    if isinstance(o, float):
        return round(o, 6)
    return o


def line(trade, level, group, code, en, ar, unit, qty, status, formula="", authority="", trace="", details=None):
    if status in ("BLOCKED", "NOT_IN_SOURCE"):
        qty = None
    return {"trade": trade, "level": level, "group": group, "code": code, "desc_en": en, "desc_ar": ar, "unit": unit,
            "qty": _r(qty), "status": status, "formula": formula, "authority": authority, "trace": trace,
            "details": details or []}


def _det(ref, formula, qty, status, **kw):
    d = {"ref": ref, "formula": formula, "qty": _r(qty), "status": status}
    d.update(kw)
    return d


# ================================================================== trade lines
def concrete(ctx, L) -> list:
    b = ctx["b2a"]
    items = {i["item"]: i for i in b["structural_items"]}
    out = []
    T = "CONCRETE"
    ft = items["FOOTINGS"]
    fo = [f for f in ctx["a3"]["footings"]["rows"] if str(f.get("status", "")).startswith("COMPUTED")]
    out.append(line(T, "GF", "SUBSTRUCTURE", "C-FTG", "Isolated footings (reinforced concrete)", "قواعد منفصلة خرسانة مسلحة",
                    "m3", ft["volume_m3"], "PARTIAL" if ft["blocked"] else "COMPUTED",
                    f"sum of {ft['computed']} footings (L x W x H from SCHEDULE OF FOOTINGS); {len(ft['blocked'])} blocked",
                    "SOURCE (schedule + plan)", "A3 footing occurrence rows",
                    [_det(f"{f['type']}", f"{f['dims']['L']['m']:.2f} x {f['dims']['W']['m']:.2f} x {f['dims']['H']['m']:.2f}",
                          f["qty"], "COMPUTED") for f in fo] +
                    [_det(k.split("|")[1], "F / F10 source conflict (OQ3-S1)", None, "BLOCKED") for k in ft["blocked"]]))
    out.append(line(T, "GF", "SUBSTRUCTURE", "C-BLD-F", "Plain concrete blinding under footings (10 cm, 10 cm beyond)",
                    "خرسانة عادية تحت القواعد 10 سم", "m3", items["BLINDING (under computed footings)"]["volume_m3"], "COMPUTED",
                    "(L + 0.20) x (W + 0.20) x 0.10 per footing", "SOURCE (p.13 typical footing)"))
    out.append(line(T, "GF", "SUBSTRUCTURE", "C-STR", "Strap beams", "ميد رابطة", "m3", items["STRAPS"]["volume_m3"],
                    "COMPUTED", "A3 strap bands", "SOURCE"))
    out.append(line(T, "GF", "SUBSTRUCTURE", "C-NECK", "Column necks", "رقاب الأعمدة", "m3", None, "BLOCKED",
                    items["COLUMN NECKS"]["why"]))
    gi = L["ground_items"]
    gbi = [x for x in gi["beams"] if x["kind"] == "INTERIOR"]
    gbe = [x for x in gi["beams"] if x["kind"] == "EXTERIOR"]
    out.append(line(T, "GF", "SUBSTRUCTURE", "C-GB-INT", "Ground beams - interior (section by length, p.13)",
                    "ميد أرضية داخلية", "m3", sum(x["volume_m3"] for x in gbi), "COMPUTED",
                    "length x B x D per span; > 5 m 30x60, 2.5-5 m 30x40, < 2.5 m 30x30", "SOURCE (p.3 plan + p.13 sections)",
                    "GROUND_STRUCTURE_REGISTER", [_det(x["id"], x["formula"], x["volume_m3"], "COMPUTED") for x in gbi]))
    out.append(line(T, "GF", "SUBSTRUCTURE", "C-GB-EXT", "Ground beams - exterior (depth 'follow arch.')", "ميد أرضية خارجية",
                    "m3", None, "BLOCKED", f"{len(gbe)} spans, {sum(x['length_m'] for x in gbe):.2f} m measured; depth not printed",
                    "BLOCKED (owner / engineer: depth from outer ground to GF slab)", "",
                    [_det(x["id"], x["formula"], None, "BLOCKED", length_m=x["length_m"]) for x in gbe]))
    out.append(line(T, "GF", "SUBSTRUCTURE", "C-BLD-GB", "Plain concrete blinding under interior ground beams",
                    "خرسانة عادية تحت الميد", "m3", L["substructure"]["ground_beam_blinding_m3"], "COMPUTED",
                    "length x (B + 0.20) x 0.10", "SOURCE (p.13 sections)"))
    for s in gi["slabs"]:
        out.append(line(T, "GF", "SUBSTRUCTURE", f"C-GSLAB-{s['id']}", f"Ground slab {s['id']} (T = 10 cm)", "بلاطة أرضية",
                        "m3", s.get("volume_m3"), s["status"], s.get("formula", s.get("why", "")),
                        "SOURCE (p.3 'T=10cm' + '5Ø10/m E.W.')" if s["status"] == "COMPUTED" else
                        "BLOCKED (zone outline not closed by layer-1 beam bands)"))
    for fl, lv in (("GF", "GF"), ("1F", "1F"), ("2F", "2F_ROOF")):
        c = items[f"COLUMNS {fl}"]
        out.append(line(T, lv, "SUPERSTRUCTURE", f"C-COL-{fl}", f"Columns {fl}", f"أعمدة {fl}", "m3", c["volume_m3"],
                        "PARTIAL" if c["blocked"] else "COMPUTED", f"{c['computed']} computed, {c['blocked']} blocked",
                        "SOURCE (schedule + plan)"))
        out.append(line(T, lv, "SUPERSTRUCTURE", f"C-JNT-{fl}", f"Column-beam joint zones {fl}", "تقاطعات الأعمدة والجسور",
                        "m3", c["joint_m3"], "COMPUTED", "column section x beam depth below the slab", "SOURCE"))
        bm = items[f"BEAMS {fl} (downstand)"]
        out.append(line(T, lv, "SUPERSTRUCTURE", f"C-BEAM-{fl}", f"Beams {fl} roof (downstand)", f"جسور ساقطة سقف {fl}",
                        "m3", bm["volume_m3"], "PARTIAL" if bm["blocked"] else "COMPUTED",
                        f"clear length x B x (D - t); {bm['computed']} computed, {bm['blocked']} blocked", "SOURCE"))
        sl = items[f"SLAB {fl} ROOF"]
        out.append(line(T, lv, "SUPERSTRUCTURE", f"C-SLAB-{fl}", f"Roof slab over {fl}", f"بلاطة سقف {fl}", "m3",
                        sl["volume_m3"], "COMPUTED", f"net plate {sl['net_area_m2']:.3f} m2 x t", "SOURCE (slab sheet)"))
        li = [x for x in L["openings"]["lintels"] if x.get("floor") == fl]
        ok = [x for x in li if x["status"] == "COMPUTED"]
        out.append(line(T, lv, "SUPERSTRUCTURE", f"C-LINT-{fl}", f"Lintels over openings {fl} (p.13 LINTEL SCHEDULE)",
                        f"أعتاب الفتحات {fl}", "m3", sum(x["volume_m3"] for x in ok),
                        "COMPUTED" if len(ok) == len(li) else "PARTIAL", "(opening + 2 x 0.40) x wall t x schedule depth",
                        "SOURCE (p.13 lintel schedule + plan opening widths)", "OPENING_LINTEL_REGISTER",
                        [_det(x["opening"], x["formula"], x.get("volume_m3"), x["status"]) for x in li]))
    out.append(line(T, "GF", "SUPERSTRUCTURE", "C-STAIR", "Stairs (waist slab, steps, landings)", "الدرج", "m3", None,
                    "BLOCKED", items["STAIRS"]["why"]))
    d = L["substructure"]["dome"]
    out.append(line(T, "OTHER_EXTERNAL", "OTHER", "C-DOME", "Dome shell 10 cm (p.7 detail; location / number to confirm)",
                    "قبة خرسانية", "m3", d["concrete_m3"], "REVIEW", d["formula"], "SOURCE detail N.T.S. - REVIEW"))
    out.append(line(T, "OTHER_EXTERNAL", "OTHER", "C-POOL", "Swimming pool (walls 20, base 40)", "المسبح", "m3", None, "BLOCKED",
                    L["substructure"]["pool"]["why"]))
    out.append(line(T, "OTHER_EXTERNAL", "OTHER", "C-SWALL", "Structural walls", "جدران خرسانية", "m3", None, "BLOCKED",
                    items["STRUCTURAL WALLS"]["why"]))
    out.append(line(T, "OTHER_EXTERNAL", "EXTERNAL", "C-BWALL", "Boundary wall beam (B.W 20x60) and footings",
                    "سور خارجي", "m3", None, "BLOCKED", "p.14 typical boundary wall; the B.W schedule row is bound to no plan run"))
    return out


def rebar(L) -> list:
    out = []
    T = "REBAR"
    groups = defaultdict(list)
    for el, sets in L["rebar"].items():
        if not isinstance(sets, list):
            continue
        for s in sets:
            groups[(FL2LV.get(s.get("floor"), "GF"), s["element"])].append(s)
    for (lv, el), sets in sorted(groups.items()):
        comp = [s for s in sets if s["status"] == "COMPUTED"]
        part = [s for s in sets if s["status"] == "PARTIAL"]
        blk = [s for s in sets if s["status"] == "BLOCKED"]
        net = sum(s["net_design_weight_kg"] for s in comp)
        proc = sum(s["procurement_weight_kg"] for s in comp)
        straight = sum(s["straight_weight_kg"] for s in part)
        code = f"R-{el}-{lv}"
        det = [_det(s["ref"], s.get("formula", ""), s.get("net_design_weight_kg"), s["status"],
                    dia_mm=s.get("dia_mm"), count=s.get("count"), straight_length_m=s.get("straight_length_m"),
                    hook_bend_addition_m=s.get("hook_bend_addition_m"), lap_addition_m=s.get("lap_addition_m"),
                    total_bar_length_m=s.get("total_bar_length_m"), kg_per_m=s.get("kg_per_m"),
                    straight_weight_kg=s.get("straight_weight_kg"),
                    procurement_weight_kg=s.get("procurement_weight_kg")) for s in sets if s["status"] != "BLOCKED"]
        if comp:
            out.append(line(T, lv, el, code + "-NET", f"{el.title()} - NET design weight (complete bar sets)",
                            "الوزن الصافي التصميمي", "kg", net, "COMPUTED", "sum(count x total length x kg/m)",
                            "SOURCE (schedules / details / notes) + URBAN-REBAR-NET-AND-PROCUREMENT@v1", "REBAR_REGISTER",
                            [d for d in det if d["status"] == "COMPUTED"]))
            out.append(line(T, lv, el, code + "-PROC", f"{el.title()} - PROCUREMENT weight incl. laps (complete sets)",
                            "وزن التوريد شامل الوصلات", "kg", proc, "COMPUTED",
                            "net + laps where a continuous bar exceeds 12 m (70Ø / 40Ø)", "URBAN-REBAR-NET-AND-PROCUREMENT@v1"))
        if part:
            out.append(line(T, lv, el, code + "-STRAIGHT", f"{el.title()} - straight weight of sets with hooks / closing "
                            "not detailed (BLOCKED_DETAILING)", "وزن الأسياخ المستقيمة (التكريبات غير مفصلة)", "kg", straight,
                            "PARTIAL", "count x straight length x kg/m; hook / bend addition BLOCKED_DETAILING",
                            "SOURCE straight lengths; hooks not in source", "REBAR_REGISTER",
                            [d for d in det if d["status"] == "PARTIAL"]))
        if blk:
            whys = sorted({s.get("why", "") for s in blk})
            out.append(line(T, lv, el, code + "-BLK", f"{el.title()} - {len(blk)} bar set(s) not computable", "غير محسوب",
                            "kg", None, "BLOCKED", "; ".join(whys), "", "REBAR_REGISTER",
                            [_det(s["ref"], s.get("why", ""), None, "BLOCKED") for s in blk]))
    out.append(line(T, "GF", "SLAB", "R-SLAB-ALL", "Suspended slab reinforcement (all roof slabs)", "تسليح البلاطات", "kg",
                    None, "BLOCKED", L["rebar"]["slabs"]["why"]))
    out.append(line(T, "GF", "COLUMN", "R-COL-FDN", "Column starter bars (foundation band)", "أشاير الأعمدة", "kg", None,
                    "BLOCKED", "length depends on the neck height (founding level not printed)"))
    return out


def blockwork(L) -> list:
    out = []
    T = "BLOCKWORK"
    agg = defaultdict(lambda: {"area": 0.0, "len": 0.0, "blk": 0.0, "rows": []})
    for r in L["blockwork"]["rows"]:
        if r["status"] == "EXCLUDED":
            continue
        k = (FL2LV[r["floor"]], r["thickness_mm"], r["position"])
        a = agg[k]
        a["area"] += r["area_m2"] or 0.0
        a["len"] += r["length_m"] or 0.0
        a["blk"] += r["blocked_length_m"] or 0.0
        a["rows"].append(r)
    for (lv, t, pos), a in sorted(agg.items()):
        st = "COMPUTED" if a["blk"] < 1e-6 else "PARTIAL"
        ar = {"EXTERNAL": "خارجي", "INTERNAL": "داخلي", "UNRESOLVED_SIDES": "غير محدد"}[pos]
        out.append(line(T, lv, f"{t} mm", f"B-{t}-{pos[:3]}-{lv}", f"Blockwork {t} mm - {pos.lower().replace('_', ' ')}",
                        f"طابوق {t} مم {ar}", "m2", a["area"], st,
                        f"length {a['len']:.2f} m x height per piece (interval - member depth); blocked {a['blk']:.2f} m",
                        "SOURCE (plan bands + structural interval + beam / slab termination)", "BLOCKWORK_REGISTER",
                        [_det(r["band"], r["formula"], r["area_m2"], r["status"], length_m=r["length_m"]) for r in a["rows"]]))
    for p in L["blockwork"]["parapets"]:
        out.append(line(T, "2F_ROOF", "PARAPET", f"B-PAR-{p['region'][:2]}", f"Parapet - {p['region']} (h 0.50 m)",
                        "دروة السطح", "m2", p["area_m2"], p["status"], p.get("formula") or "", "SOURCE (sections + slab plates)"))
    out.append(line(T, "GF", "OVER OPENINGS", "B-OVER-OPEN", "Blockwork over door / window openings (above lintel)",
                    "طابوق فوق الفتحات", "m2", None, "BLOCKED", "opening heights not printed (no door / window schedule)"))
    out.append(line(T, "OTHER_EXTERNAL", "EXTERNAL", "B-BWALL", "Boundary wall blockwork", "طابوق السور", "m2", None, "BLOCKED",
                    "boundary wall height / extent: p.14 typical only, plan run not bound"))
    return out


def plaster_paint(L) -> list:
    out = []
    T = "PLASTER_PAINT"
    for r in L["finishes"]["rows"]:
        lv = FL2LV[r["floor"]]
        st = "COMPUTED" if r["faces_blocked_length_m"] < 1e-6 else "PARTIAL"
        out.append(line(T, lv, "INTERNAL PLASTER", f"P-PL-{r['room']}", f"Internal plaster - {r['name_en'] or 'UNKNOWN'}",
                        f"لياسة داخلية - {r['name_ar']}", "m2", r["plaster_gross_m2"], st,
                        "wall length x (interval - member depth) per piece, gross of openings",
                        "SOURCE geometry + structural interval", r["room"]))
        if r["paint_gross_m2"] is not None:
            out.append(line(T, lv, "PAINT", f"P-PA-{r['room']}", f"Internal paint - {r['name_en'] or 'UNKNOWN'}",
                            f"دهان داخلي - {r['name_ar']}", "m2", r["paint_gross_m2"],
                            "COMPUTED" if r["paint_blocked_length_m"] < 1e-6 else "PARTIAL",
                            "wall length x (interval - 0.10 build-up - controlling soffit - 0.15)",
                            "URBAN_FALLBACK build-up 0.10 m (OD-V3-1)", r["room"]))
        elif r["room_class"] not in ("WET", "SERVICE"):
            out.append(line(T, lv, "PAINT", f"P-PA-{r['room']}", f"Internal paint - {r['name_en'] or 'UNKNOWN'}",
                            f"دهان داخلي - {r['name_ar']}", "m2", None, "BLOCKED",
                            "room controlling soffit unknown (an unbound beam band over the room)"))
        out.append(line(T, lv, "EXTRAS", f"P-CB-{r['room']}", f"Plaster corner beads - {r['name_en'] or 'UNKNOWN'}",
                        "زوايا لياسة", "lm", r["corner_bead_m"], "REVIEW",
                        f"{r['corner_beads_nr']} projecting corners x plaster height (coverage rule by owner)",
                        "geometry SOURCE; scope OD-V3-4 (separate item)", r["room"]))
        out.append(line(T, lv, "EXTRAS", f"P-SD-{r['room']}", f"Spatter dash (طرطشة) - {r['name_en'] or 'UNKNOWN'}",
                        "طرطشة", "m2", r["spatter_dash_m2"], "REVIEW", "= plastered surface (coverage rule by owner)",
                        "geometry SOURCE; scope OD-V3-4", r["room"]))
    out.append(line(T, "OTHER_EXTERNAL", "EXTERNAL", "P-EXT", "External plaster / paint (facades)", "لياسة ودهان خارجي", "m2",
                    None, "BLOCKED", "facade heights from elevations not read this round (SW / NE raster only)"))
    out.append(line(T, "OTHER_EXTERNAL", "EXTRAS", "P-REVEAL", "Door / window reveals (شرشوب)", "شرشوب الفتحات", "m2", None,
                    "BLOCKED", "opening heights not printed"))
    return out


def flooring(L) -> list:
    out = []
    T = "FLOORING_PORCELAIN"
    for r in L["finishes"]["rows"]:
        lv = FL2LV[r["floor"]]
        out.append(line(T, lv, "FLOOR FINISH", f"F-FL-{r['room']}", f"Floor finish - {r['name_en'] or 'UNKNOWN'} ({r['floor_material']})",
                        f"أرضيات - {r['name_ar']}", "m2", r["floor_area_m2"],
                        "COMPUTED" if r["status"] == "COMPUTED" else "COMPUTED", r["floor_formula"],
                        r["floor_material_authority"], r["room"]))
        if r["skirting_m"] is not None:
            out.append(line(T, lv, "SKIRTING", f"F-SK-{r['room']}", f"Skirting - {r['name_en'] or 'UNKNOWN'}", "نعلات",
                            "lm", r["skirting_m"], "COMPUTED", "wall edges of the room boundary; openings excluded",
                            "SOURCE geometry", r["room"]))
    for r in L["rooms"]["rows"]:
        if r["class"] == "OPENING_STRIP":
            out.append(line(T, FL2LV[r["floor"]], "THRESHOLDS", f"F-TH-{r['id']}", "Door threshold strip", "عتبة باب", "m2",
                            r["area_m2"], "COMPUTED", "site between the two door closures", "SOURCE geometry", r["id"]))
    out.append(line(T, "GF", "STAIRS", "F-STAIR", "Stair treads / risers finish", "تكسية الدرج", "m2", None, "BLOCKED",
                    "riser count / height not proved"))
    out.append(line(T, "OTHER_EXTERNAL", "EXTERNAL", "F-COURT", "Courtyard paving", "تبليط الحوش", "m2", None, "BLOCKED",
                    "external works extent not measured this round"))
    return out


def ceilings(L) -> list:
    out = []
    T = "CEILINGS"
    for r in L["finishes"]["rows"]:
        lv = FL2LV[r["floor"]]
        out.append(line(T, lv, "CEILING", f"CE-{r['room']}", f"Ceiling - {r['name_en'] or 'UNKNOWN'} (material BY_SPEC)",
                        f"سقف - {r['name_ar']}", "m2", r["ceiling_area_m2"], "COMPUTED", r["ceiling_formula"],
                        "URBAN-CEILING-QUANTITY-WITHOUT-MATERIAL@v1", r["room"]))
        out.append(line(T, lv, "CORNICE", f"CE-CO-{r['room']}", f"Cornice (perimeter) - {r['name_en'] or 'UNKNOWN'}",
                        "كرانيش", "lm", r["cornice_m"], "REVIEW", "room perimeter; cornice existence by specification",
                        "geometry SOURCE; scope OD-V3-4", r["room"]))
    out.append(line(T, "GF", "DECOR", "CE-DECOR", "Gypsum decor / cove light", "ديكور جبس وإضاءة مخفية", "m2", None,
                    "NOT_IN_SOURCE", "no reflected ceiling plan in the supplied files"))
    return out


def tile_wp(ctx, L) -> list:
    from engine.source import waterproofing_policy as WP
    out = []
    T = "WALL_TILE_WATERPROOFING"
    for r in L["finishes"]["rows"]:
        if r["room_class"] not in ("WET", "SERVICE"):
            continue
        lv = FL2LV[r["floor"]]
        out.append(line(T, lv, "WALL TILE", f"T-WT-{r['room']}", f"Wall tile full height - {r['name_en']}",
                        f"سيراميك جدران - {r['name_ar']}", "m2", r["wall_tile_gross_m2"],
                        "COMPUTED" if r["wall_tile_gross_m2"] is not None and r["paint_blocked_length_m"] < 1e-6 else
                        ("PARTIAL" if r["wall_tile_gross_m2"] else "BLOCKED"),
                        "wall length x (interval - 0.10 build-up - soffit - 0.15), gross of openings",
                        "URBAN-WET-WALL-TILE-FULL-HEIGHT@v1 + URBAN_FALLBACK build-up", r["room"]))
        w = WP.wet(floor_m2=r["floor_area_m2"], perimeter_m=_perim(L, r["room"]),
                   door_widths_m=[r["opening_widths_m"]] if r["opening_widths_m"] else None, room=r["room"])
        out.append(line(T, lv, "WET ROOM WATERPROOFING", f"T-WP-{r['room']}", f"Floor waterproofing + upturn - {r['name_en']}",
                        "عزل مائي للأرضية", "m2", w.get("physical_m2"), "COMPUTED" if w.get("physical_m2") else "BLOCKED",
                        f"floor {w.get('floor_m2')} + upturn {w.get('upturn_length_m')} x {w.get('upturn_m')}",
                        "URBAN-WET-ROOM-WP method (waterproofing_policy)", r["room"]))
    for rf in ctx["b2a"]["architecture"]["waterproofing"]["roof"]:
        lv = "2F_ROOF"
        out.append(line(T, lv, "ROOF WATERPROOFING", "T-RWP-" + rf["region"][:2], f"Roof waterproofing - {rf['region']}",
                        "عزل الأسطح", "m2", rf.get("physical_m2"), "COMPUTED" if rf.get("physical_m2") else "BLOCKED",
                        f"flat {rf.get('flat_m2')} + upturn {rf.get('upturn_m2')}", rf.get("method", "")))
    sb = L["substructure"]
    out.append(line(T, "GF", "FOUNDATION WATERPROOFING", "T-FWP-FTG", "Liquid waterproofing 2 layers - footings",
                    "عزل القواعد", "m2", sb["footing_wp_m2"], "COMPUTED", "2 (L + W) H + L W per footing", "SOURCE (p.13)"))
    out.append(line(T, "GF", "FOUNDATION WATERPROOFING", "T-FWP-GB", "Liquid waterproofing 2 layers - interior ground beam sides",
                    "عزل الميد", "m2", sb["ground_beam_wp_m2"], "COMPUTED", "2 x D x length", "SOURCE (p.13)"))
    out.append(line(T, "GF", "FOUNDATION WATERPROOFING", "T-FMEM", "Insulation membrane under footings", "عازل تحت القواعد",
                    "m2", sb["footing_membrane_m2"], "COMPUTED", "(L + 0.20) (W + 0.20)", "SOURCE (p.13)"))
    return out


def _perim(L, rid):
    r = next(x for x in L["rooms"]["rows"] if x["id"] == rid)
    return r["perimeter_m"]


def openings(ctx, L) -> list:
    out = []
    T = "ALUMINIUM_OPENINGS"
    rows = L["openings"]["rows"]
    for fl in ("GF", "1F", "2F"):
        lv = FL2LV[fl]
        for kind, en, ar in (("DOOR", "Doors (single leaf)", "أبواب"), ("DOUBLE_LEAF_DOOR", "Doors (double leaf)", "أبواب ضلفتين"),
                             ("WINDOW", "Windows / glazed openings", "نوافذ")):
            xs = [o for o in rows if o["floor"] == fl and o["kind"] == kind]
            if not xs:
                continue
            ok = [o for o in xs if o.get("width_m")]
            by = Counter(round(o["width_m"], 2) for o in ok)
            out.append(line(T, lv, kind, f"O-{kind[:3]}-{fl}", f"{en} {fl}", f"{ar} {fl}", "nr", len(xs),
                            "COMPUTED", "count; widths " + ", ".join(f"{k:.2f} m x {v}" for k, v in sorted(by.items())),
                            "SOURCE plan", "OPENING_LINTEL_REGISTER",
                            [_det(o["id"], f"width {o.get('width_m')} m, wall {o.get('wall_t_m')} m; height BLOCKED", 1,
                                  o["status"]) for o in xs]))
            out.append(line(T, lv, kind, f"O-{kind[:3]}-{fl}-W", f"{en} {fl} - total opening width", f"عرض {ar}", "lm",
                            sum(o["width_m"] for o in ok), "COMPUTED", "sum of widths", "SOURCE plan"))
            out.append(line(T, lv, kind, f"O-{kind[:3]}-{fl}-A", f"{en} {fl} - area", f"مساحة {ar}", "m2", None, "BLOCKED",
                            "head / sill heights not printed (no schedule; SW / NE elevations raster)"))
    s = ctx["a3"]["architecture"]["salon_glazing"]
    out.append(line(T, "GF", "GLAZING", "O-SALON", "Salon glazing (aluminium + glass)", "واجهة زجاج الصالون", "m2",
                    s["width_m"] * s["height_m"] if s.get("height_m") else None, "COMPUTED", f"{s['width_m']} x {s['height_m']}",
                    "width SOURCE + height PROJECT_OWNER_FACT (OF-A3-SALON-HEIGHT)"))
    m = ctx["a3"]["architecture"]["curved_glazing"]["master_bedroom"]
    out.append(line(T, "GF", "GLAZING", "O-CURVED-L", "Master bedroom curved glazing - developed length", "زجاج منحني",
                    "lm", m.get("developed_length_m"), "COMPUTED", "mid-band arc length", "SOURCE (concentric arcs)"))
    out.append(line(T, "GF", "GLAZING", "O-CURVED-A", "Master bedroom curved glazing - area", "مساحة الزجاج المنحني", "m2",
                    None, "BLOCKED", "height not printed"))
    return out


def stairs(ctx, L) -> list:
    out = []
    T = "STAIRS_RAILINGS"
    for r in L["railings"]:
        out.append(line(T, FL2LV[r["floor"]], "RAILING", f"S-RL-{r['void']}", f"Gallery railing at void {r['void']}",
                        "درابزين حول المنور", "lm", r["length_m"], "COMPUTED", r["rule"], "SOURCE geometry; material BY_SPEC"))
    st = ctx["b2a"]["stairs"]
    out.append(line(T, "GF", "STAIRS", "S-GOING", "Stair going (tread depth)", "عرض النائمة", "m",
                    st["known_inputs"]["tread_going_m"]["value"], "COMPUTED", "p.16 typical section", "SOURCE"))
    out.append(line(T, "GF", "STAIRS", "S-RAIL", "Stair handrail / balustrade", "درابزين الدرج", "lm", None, "BLOCKED",
                    "flight lengths need the riser count per flight (not proved)"))
    out.append(line(T, "GF", "STAIRS", "S-TREAD", "Stair treads and risers (marble)", "رخام الدرج", "m2", None, "BLOCKED",
                    "riser count / height not proved"))
    return out


# ================================================================== registers
def sumrow(ln):
    """The master-summary row a line adds into (like items only); None = informational, never added."""
    t, g, c = ln["trade"], ln["group"], ln["code"]
    if t == "CONCRETE":
        return ("Plain concrete (blinding)", "خرسانة عادية") if c.startswith("C-BLD") else ("Reinforced concrete", "خرسانة مسلحة")
    if t == "REBAR":
        if c.endswith("-PROC"):
            return ("Procurement weight incl. laps (complete sets)", "وزن التوريد")
        if c.endswith("-STRAIGHT"):
            return ("Straight weight - sets with hooks not detailed", "وزن مستقيم")
        if ln["status"] == "BLOCKED":
            return ("Bar sets / members not computable", "تسليح غير قابل للحساب")
        return ("Net design weight (complete sets)", "الوزن الصافي")
    if t == "BLOCKWORK":
        if g == "EXTERNAL":
            return ("Boundary wall blockwork", "طابوق السور")
        return ("Parapet blockwork", "طابوق الدروة") if g == "PARAPET" else (f"Blockwork {g}", f"طابوق {g}")
    if t == "PLASTER_PAINT":
        return {"INTERNAL PLASTER": ("Internal plaster", "لياسة داخلية"), "PAINT": ("Internal paint", "دهان داخلي"),
                "EXTRAS": ("Extras (review)", "إضافات"), "EXTERNAL": ("External plaster / paint", "لياسة خارجية")}.get(g)
    if t == "FLOORING_PORCELAIN":
        return {"FLOOR FINISH": ("Floor finish", "أرضيات"), "SKIRTING": ("Skirting", "نعلات"),
                "THRESHOLDS": ("Door thresholds", "عتبات")}.get(g)
    if t == "CEILINGS":
        return {"CEILING": ("Ceiling area", "مساحة الأسقف"), "CORNICE": ("Cornice (review)", "كرانيش")}.get(g)
    if t == "WALL_TILE_WATERPROOFING":
        return {"WALL TILE": ("Wall tile", "سيراميك جدران"), "WET ROOM WATERPROOFING": ("Wet-room waterproofing", "عزل الحمامات"),
                "ROOF WATERPROOFING": ("Roof waterproofing", "عزل الأسطح"),
                "FOUNDATION WATERPROOFING": ("Foundation waterproofing / membrane", "عزل الأساسات")}.get(g)
    if t == "ALUMINIUM_OPENINGS":
        if c.endswith("-W"):
            return ("Opening widths", "عروض الفتحات")
        if g == "GLAZING":
            return {"O-SALON": ("Salon glazing", "زجاج الصالون"), "O-CURVED-L": ("Curved glazing length", "طول الزجاج المنحني"),
                    "O-CURVED-A": ("Curved glazing area", "مساحة الزجاج المنحني")}[c]
        return {"DOOR": ("Doors single leaf", "أبواب"), "DOUBLE_LEAF_DOOR": ("Doors double leaf", "أبواب ضلفتين"),
                "WINDOW": ("Windows / glazed openings", "نوافذ")}.get(g)
    if t == "STAIRS_RAILINGS":
        return ("Gallery railing", "درابزين") if g == "RAILING" else None
    return None


def lines(ctx) -> list:
    L = ctx["v3"]
    out = (concrete(ctx, L) + rebar(L) + blockwork(L) + plaster_paint(L) + flooring(L) + ceilings(L) + tile_wp(ctx, L)
           + openings(ctx, L) + stairs(ctx, L))
    for i, ln in enumerate(out):
        ln["line_id"] = f"L{i + 1:04d}"
        sr = sumrow(ln)
        ln["sumrow"], ln["sumrow_ar"] = sr if sr else (None, None)
    return out


def matrix(boq) -> dict:
    m = defaultdict(lambda: defaultdict(float))
    st = defaultdict(set)
    ar = {}
    order = {t[1]: i for i, t in enumerate(TRADES)}
    for ln in boq:
        if not ln["sumrow"]:
            continue
        k = (ln["trade"], ln["sumrow"], ln["unit"])
        ar[k] = ln["sumrow_ar"]
        if ln["status"] in IN_TOTAL and ln["qty"] is not None:
            m[k][ln["level"]] += ln["qty"]
        else:
            m[k]
        st[k].add(ln["status"])
    rows = []
    for k in sorted(m, key=lambda z: (order[z[0]], z[1], z[2])):
        t, srow, u = k
        v = m[k]
        rows.append({"trade": t, "item": srow, "item_ar": ar[k], "unit": u, **{lv: _r(v.get(lv, 0.0)) for lv in LEVELS},
                     "total": _r(sum(v.values())), "statuses": sorted(st[k]),
                     "status": ("REVIEW" if "REVIEW" in st[k] else "BLOCKED") if not v else
                     ("PARTIAL" if st[k] - {"COMPUTED"} else "COMPUTED")})
    return {"rows": rows, "rule": "only COMPUTED and PARTIAL quantities of one unit per trade are added; REVIEW / BLOCKED "
                                  "lines are listed in the trade workbooks, never in a total"}


def completeness(boq) -> dict:
    rows = []
    for code, t, ar, _ in TRADES:
        xs = [x for x in boq if x["trade"] == t]
        c = Counter(x["status"] for x in xs)
        n = len(xs)
        reasons = sorted({x["formula"] if x["status"] == "BLOCKED" else "" for x in xs} - {""})[:6]
        core = [x for x in xs if x["group"] not in ("EXTRAS", "CORNICE", "DECOR")]
        cc = Counter(x["status"] for x in core)
        rows.append({"trade": t, "trade_ar": ar, "expected_items": n, "computed": c["COMPUTED"], "partial": c["PARTIAL"],
                     "core_items": len(core),
                     "core_coverage_pct": round(100.0 * (cc["COMPUTED"] + 0.5 * cc["PARTIAL"]) / len(core), 1) if core else 0.0,
                     "review": c["REVIEW"], "blocked": c["BLOCKED"], "not_in_source": c["NOT_IN_SOURCE"],
                     "coverage_pct": round(100.0 * (c["COMPUTED"] + 0.5 * c["PARTIAL"]) / n, 1) if n else 0.0,
                     "remaining_reasons": reasons})
    return {"SCHEMA": "URBAN_BOQ_COMPLETENESS_MATRIX_V3", "rows": rows,
            "rule": "coverage = (computed + 0.5 x partial) / expected items, by item count; review and blocked items count "
                    "as not covered; not-in-source items stay in the denominator with their evidence"}


BLOCKERS = [
    ("B01", "STRUCTURE", "Exterior ground-beam depth ('follow arch.')", "C-GB-EXT", "D", "outer ground level to GF slab level not printed"),
    ("B02", "STRUCTURE", "Column necks / founding level", "C-NECK, R-COL-FDN", "D", "founding level left to site and soil (note 12)"),
    ("B03", "STRUCTURE", "Stairs: riser count / waist thickness", "C-STAIR, F-STAIR, S-RAIL", "B + D", "waist drawn THICK without value"),
    ("B04", "STRUCTURE", "Pool depths", "C-POOL", "D", "'as per arch.' - not in the architectural set"),
    ("B05", "STRUCTURE", "Dome location / number", "C-DOME", "D", "p.7 detail N.T.S., not bound to a plan"),
    ("B06", "STRUCTURE", "F / F10 footing conflict", "C-FTG", "D", "genuine drawing conflict (OQ3-S1)"),
    ("B07", "STRUCTURE", "Beam / column occurrences not bound", "C-BEAM, C-COL", "B then D", "tag binding residue"),
    ("B08", "REBAR", "Hooks / bends / anchorage / stirrup closing", "R-*-STRAIGHT", "F", "no bar-bending detail; OD-V3-3 forbids invention"),
    ("B09", "REBAR", "Slab panel bar extents", "R-SLAB-ALL", "B", "per-panel annotations not bound to distribution extents"),
    ("B10", "STRUCTURE", "Annex ground-slab zone outline", "C-GSLAB-ZONE-2", "B", "west exterior beam drawn on another layer"),
    ("B11", "OPENINGS", "Door / window heights", "O-*-A, B-OVER-OPEN, P-REVEAL", "D / E", "no schedule; SW / NE elevations raster"),
    ("B12", "FINISHES", "Room soffit under unbound beams (paint)", "P-PA-*", "B", "beam band type conflict over the room"),
    ("B13", "FINISHES", "Extras coverage rules (beads, spatter dash, cornice)", "P-CB-*, P-SD-*, CE-CO-*", "F", "OD-V3-4 scope, coverage rule"),
    ("B14", "EXTERNAL", "Facades, boundary wall, courtyard", "P-EXT, B-BWALL, F-COURT, C-BWALL", "A + E", "not measured this round"),
    ("B15", "TOPOLOGY", "Lift shaft confirmation", "rooms 3.24 m2 x 3 storeys", "D", "repeated 1.8 x 1.8 m site; p.14 typical lift"),
]


def blockers(boq) -> dict:
    rows = []
    for bid, area, what, lines_, cls, why in BLOCKERS:
        rows.append({"id": bid, "area": area, "blocker": what, "lines": lines_, "class": cls, "why": why})
    return {"SCHEMA": "URBAN_FINAL_BLOCKER_REGISTER_V3", "rows": rows,
            "blocked_lines": sum(1 for x in boq if x["status"] == "BLOCKED")}


QUESTIONS = [
    ("STRUCTURE", "Q-S1", "Exterior ground beams are 'follow arch.': confirm the depth from outer ground to the GF slab level "
                          "(main house +1.00, annex +0.30)."),
    ("STRUCTURE", "Q-S2", "Founding level (bottom of footings) - needed for column necks and starter bars."),
    ("STRUCTURE", "Q-S3", "Stair waist thickness and riser height (or the number of risers per flight)."),
    ("STRUCTURE", "Q-S4", "Swimming pool depths (shallow / deep) - the detail says 'as per arch.'."),
    ("STRUCTURE", "Q-S5", "Is the p.7 dome built? Where, and how many?"),
    ("STRUCTURE", "Q-S6", "F / F10 footing conflict (OQ3-S1, still open)."),
    ("STRUCTURE", "Q-S7", "Bar bending: adopt a standard for hooks / bends / stirrup closing, or supply the bending schedule."),
    ("ARCHITECTURE", "Q-A1", "Confirm the 1.8 x 1.8 m repeated space on all storeys is the lift shaft."),
    ("ARCHITECTURE", "Q-A2", "GF entrance / open zone: is the hall-dining-reception zone one open space (no screen)?"),
    ("OPENINGS", "Q-O1", "Door and window head heights (and sills), or a door / window schedule."),
    ("FINISHES", "Q-F1", "Extras: measure corner beads / spatter dash on all plastered walls? Cornice in which rooms?"),
    ("FINISHES", "Q-F2", "Ceiling material per room (gypsum board / plaster / decor) - no reflected ceiling plan."),
]


def questions() -> dict:
    return {"SCHEMA": "URBAN_FINAL_OWNER_QUESTION_REGISTER_V3",
            "rows": [{"group": g, "id": i, "question": q} for g, i, q in QUESTIONS],
            "rule": "batched once, after the source was exhausted (OD-V3-9); F / F10 stays blocked until answered"}


def registers(ctx) -> dict:
    L = ctx["v3"]
    boq = lines(ctx)
    regs = {
        "V3_TOPOLOGY_REGISTER": dict({"SCHEMA": "URBAN_ALSENAN_V3_TOPOLOGY_V1"}, **strip(ctx["v3_topology"])),
        "ROOM_REGISTER_V3": {"SCHEMA": "URBAN_ALSENAN_V3_ROOMS_V1", **strip(L["rooms"])},
        "VOID_REGISTER": {"SCHEMA": "URBAN_ALSENAN_V3_VOIDS_V1", **strip(L["voids"])},
        "FINISH_REGISTER": {"SCHEMA": "URBAN_ALSENAN_V3_FINISHES_V1", **strip(L["finishes"])},
        "BLOCKWORK_REGISTER": {"SCHEMA": "URBAN_ALSENAN_V3_BLOCKWORK_V1", **strip(L["blockwork"])},
        "GROUND_STRUCTURE_REGISTER": {"SCHEMA": "URBAN_ALSENAN_V3_GROUND_V1", "ground": strip(L["ground"]),
                                      "items": strip({k: v for k, v in L["ground_items"].items() if k != "rebar"})},
        "OPENING_LINTEL_REGISTER": {"SCHEMA": "URBAN_ALSENAN_V3_OPENINGS_V1", **strip(L["openings"])},
        "REBAR_REGISTER": {"SCHEMA": "URBAN_ALSENAN_V3_REBAR_V1", **strip(L["rebar"])},
        "SUBSTRUCTURE_REGISTER": {"SCHEMA": "URBAN_ALSENAN_V3_SUBSTRUCTURE_V1", **strip(L["substructure"])},
        "URBAN_METHOD_REGISTER_V3": strip(L["methods"]),
        "BOQ_LINES": {"SCHEMA": "URBAN_ALSENAN_V3_BOQ_LINES_V1", "levels": list(LEVELS), "level_names": LEVEL_NAME,
                      "trades": [list(t) for t in TRADES], "lines": strip(boq)},
        "MASTER_MATRIX": strip(matrix(boq)),
        "BOQ_COMPLETENESS_MATRIX": completeness(boq),
        "FINAL_BLOCKER_REGISTER": blockers(boq),
        "FINAL_OWNER_QUESTION_REGISTER": questions(),
    }
    regs["FINAL_QA"] = qa(ctx, regs)
    regs["FINAL_FREEZE"] = freeze(ctx, regs)
    return regs


def qa(ctx, regs) -> dict:
    boq = regs["BOQ_LINES"]["lines"]
    checks = {
        "no_blocked_quantity": all(x["qty"] is None for x in boq if x["status"] in ("BLOCKED", "NOT_IN_SOURCE")),
        "every_line_has_status": all(x["status"] for x in boq),
        "units_known": all(x["unit"] in ("m3", "m2", "lm", "m", "nr", "kg") for x in boq),
        "line_ids_unique": len({x["line_id"] for x in boq}) == len(boq),
        "matrix_equals_lines": all(abs(r["total"] - sum(x["qty"] for x in boq if x["trade"] == r["trade"] and
                                                        x["sumrow"] == r["item"] and x["unit"] == r["unit"]
                                                        and x["status"] in IN_TOTAL)) < 1e-6
                                   for r in regs["MASTER_MATRIX"]["rows"]),
        "closures_zero_material": all(not r.get("affects_wall_quantity") for fl in ctx["v3_topology"]["floors"].values()
                                      for r in fl["drafting_gaps"]),
        "benchmark_not_read": not any("benchmark" in m.lower() and "firewall" not in m.lower()
                                      for m in ctx.get("firewall", {}).get("modules_loaded_during_build", [])),
        "fallback_labelled": all("URBAN_FALLBACK" in x["authority"] for x in boq if x["code"].startswith("P-PA-")
                                 and x["status"] in IN_TOTAL),
    }
    return {"SCHEMA": "URBAN_ALSENAN_V3_FINAL_QA_V1", "checks": checks, "state": "PASS" if all(checks.values()) else "FAIL",
            "firewall_audit": sorted({str(x) for x in (ctx.get("firewall", {}).get("audit") or [])
                                      if "__pycache__" not in str(x) and not str(x).endswith((".py", ".pyc"))}),
            "firewall_rule": "files opened during the build (code files omitted); none is a benchmark file"}


def _digest(o):
    return hashlib.sha256(json.dumps(o, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def freeze(ctx, regs) -> dict:
    return {"SCHEMA": "URBAN_ALSENAN_V3_FREEZE_V1", "phase": "V3a",
            "register_digests": {k: _digest(v) for k, v in sorted(regs.items()) if k not in ("FINAL_FREEZE",)},
            "boq_digest": _digest(regs["BOQ_LINES"]["lines"]),
            "code_commit": ctx.get("code_commit"),
            "rule": "benchmark evaluation only after this freeze; the frozen quantities never change from a comparison"}


def summary(regs) -> dict:
    c = Counter(x["status"] for x in regs["BOQ_LINES"]["lines"])
    return {"lines": len(regs["BOQ_LINES"]["lines"]), "statuses": dict(c), "qa": regs["FINAL_QA"]["state"],
            "matrix": [(r["trade"], r["item"], r["unit"], r["total"]) for r in regs["MASTER_MATRIX"]["rows"]],
            "completeness": [(r["trade"], r["coverage_pct"]) for r in regs["BOQ_COMPLETENESS_MATRIX"]["rows"]]}
