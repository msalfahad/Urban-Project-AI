"""REPORTING V2 - Alsenan adapter: frozen A3 + B2A.1 registers -> REPORTING_MODEL_V2. Maps, never measures.

Authority: the B2A.1 registers supersede the A3 registers wherever ALSENAN_B2A_DELTA lists a change (concrete,
slabs, columns, beams, blinding, opening functions, curved glazing, the GF master bedroom, the Reception region, wall
plaster of terminated faces, waterproofing); everything else is read from the frozen A3 registers (A3 behaviour
preserved by B2A). Superseded A3 rows (window counts / widths, wet-room floor, A3 curved lengths, the A3 Reception zone)
are listed on TECH_SOURCE_HANDLES and never shown as quantities.
"""

from __future__ import annotations

import sys
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.reporting_v2 import layout as L                                                         # noqa: E402
from engine.reporting_v2 import terms as T                                                          # noqa: E402
from engine.reporting_v2.model import (Registers, blocked, col, display_status, dsum, fcell, inp, line, na, part,  # noqa: E402
                                       qsum, ref, rng, row, section, sheet, sub, worst)

B2A1 = ROOT / "tests/alsenan/registers_b2a1"
A3 = ROOT / "tests/alsenan/registers_a3"
B2A1_FILES = ["PHYSICAL_CONCRETE_REGISTER", "STRUCTURAL_VERTICAL_INTERVAL_REGISTER", "BEAM_BINDING_REGISTER",
              "SLAB_REGION_REGISTER", "STAIR_REGISTER", "OPENING_AUTHORITY_REGISTER", "CURVED_OPENING_REGISTER",
              "WALL_HEIGHT_REGISTER", "WATERPROOFING_REGISTER", "REMAINING_BLOCKERS", "OWNER_FACT_REGISTER",
              "URBAN_METHOD_REGISTER", "ALSENAN_B2A_DELTA", "QA_GATES", "ALSENAN_PHASE_B2A1_REGISTER_FREEZE",
              "ALSENAN_REGRESSION", "QORTUBA_REGRESSION"]
A3_FILES = ["ARCH_BOQ", "ROOM_REGISTER", "FOOTING_REGISTER", "STRAP_BEAM_REGISTER", "OWNER_QUESTION_REGISTER", "SOURCE_MANIFEST"]
FLOORS = ("GF", "1F", "2F")
LEVELS = ["FOUNDATION", "GF", "1F", "2F", "ROOF", "EXTERNAL", "UNASSIGNED"]
SUPERSEDED = {"A3-WIN-GF": "OPENING_AUTHORITY functions (B2A)", "A3-WIN-1F": "OPENING_AUTHORITY functions (B2A)",
              "A3-WIN-2F": "OPENING_AUTHORITY functions (B2A)", "A3-WNW-GF": "includes 4 openings now doors (B2A)",
              "A3-WNW-1F": "window widths superseded by OPENING_AUTHORITY rows", "A3-WNW-2F": "window widths superseded by OPENING_AUTHORITY rows",
              "A3-WET-GF": "WATERPROOFING_REGISTER wet rooms (B2A)", "A3-WET-1F": "WATERPROOFING_REGISTER wet rooms (B2A)",
              "A3-WET-2F": "WATERPROOFING_REGISTER wet rooms (B2A)", "A3-WPM-GF": "WATERPROOFING_REGISTER (B2A)",
              "A3-WPM-1F": "WATERPROOFING_REGISTER (B2A)", "A3-WPM-2F": "WATERPROOFING_REGISTER (B2A)",
              "A3-CGL-MB-L": "CURVED_OPENING_REGISTER (MIN_RADIUS_ARC)", "A3-CGL-1F-CG01-L": "CURVED_OPENING_REGISTER (MIN_RADIUS_ARC)",
              "A3-DHZ-RECEPTION": "WALL_HEIGHT_REGISTER reception region (B2A)", "A3-FLR-GF": "room rows + B2A master bedroom",
              "A3-CLG-GF": "room rows", "A3-FLR-1F": "room rows", "A3-CLG-1F": "room rows", "A3-SKP-GF": "room rows",
              "A3-SKP-1F": "room rows", "A3-STT-GF": "STAIR_REGISTER (tread lines are candidates)",
              "A3-STT-1F": "STAIR_REGISTER (tread lines are candidates)", "A3-STT-2F": "STAIR_REGISTER"}


def registers() -> Registers:
    files = {f"B2A1.{n}": B2A1 / f"{n}.json" for n in B2A1_FILES}
    files |= {f"A3.{n}": A3 / f"{n}.json" for n in A3_FILES}
    return Registers(files, ROOT)


def _i(lst, pred):
    hits = [i for i, x in enumerate(lst) if pred(x)]
    if len(hits) != 1:
        raise KeyError(f"expected one match, got {len(hits)}")
    return hits[0]


class A:
    """Alsenan adapter state."""

    def __init__(self, R: Registers):
        self.R = R
        g = R.data
        self.ab = g["A3.ARCH_BOQ"]["rows"]
        self.abi = {r["item"]: i for i, r in enumerate(self.ab)}
        self.pc = g["B2A1.PHYSICAL_CONCRETE_REGISTER"]
        self.sv = g["B2A1.STRUCTURAL_VERTICAL_INTERVAL_REGISTER"]
        self.bb = g["B2A1.BEAM_BINDING_REGISTER"]
        self.op = g["B2A1.OPENING_AUTHORITY_REGISTER"]
        self.cu = g["B2A1.CURVED_OPENING_REGISTER"]
        self.wh = g["B2A1.WALL_HEIGHT_REGISTER"]
        self.wp = g["B2A1.WATERPROOFING_REGISTER"]
        self.rb = g["B2A1.REMAINING_BLOCKERS"]
        self.rr = g["A3.ROOM_REGISTER"]
        self.ft = g["A3.FOOTING_REGISTER"]
        self.sb = g["A3.STRAP_BEAM_REGISTER"]

    # ---------------- register access
    def ab_cell(self, item):
        i = self.abi[item]
        r = self.ab[i]
        ref = f"A3.ARCH_BOQ:/rows/{i}/qty"
        return self.R.q(ref) if r["qty"] is not None else blocked(self.ab_tech(item), ref)

    def ab_tech(self, item):
        r = self.ab[self.abi[item]]
        return r["class"] if r["status"] == "BLOCKED" and r["class"].startswith("BLOCKED") else r["status"]

    def ab_part(self, item, level=None, note=None):
        r = self.ab[self.abi[item]]
        return part(level or r["floor"], self.ab_cell(item), self.ab_tech(item), note)

    def ex(self, name):
        return _i(self.pc["explicit_items"], lambda r: r["item"] == name)

    def ex_part(self, name, level, note=None):
        i = self.ex(name)
        r = self.pc["explicit_items"][i]
        ref = f"B2A1.PHYSICAL_CONCRETE_REGISTER:/explicit_items/{i}/volume_m3"
        cell = self.R.q(ref) if r["volume_m3"] is not None else blocked(r["state"], ref)
        return part(level, cell, r["state"], note or r.get("why") or r.get("basis"))

    def rooms(self, fl):
        """(index, A3 room) on a floor, the GF master bedroom replaced by the B2A certified record."""
        return [(i, r) for i, r in enumerate(self.rr["rooms"]) if r["floor"] == fl]

    def is_mbr(self, r):
        return r["site"] == self.wh["mbr"]["site"]


# ------------------------------------------------------------------ lines
def build_lines(a: A) -> list:
    R, out = a.R, []
    pcs = a.pc["storeys"]
    out.append(line("CON-SUPER", "STRUCTURAL_CONCRETE",
                    "Superstructure concrete per storey - physical model: slab + downstand beams + beam-column joints + columns",
                    "خرسانة الهيكل العلوي لكل دور (بلاطة + جسور ساقطة + عقد + أعمدة)", "m3",
                    [part(fl, R.q(f"B2A1.PHYSICAL_CONCRETE_REGISTER:/storeys/{fl}/model/computed_total_m3"), pcs[fl]["model"]["total_state"],
                          f"storey {fl}: {fl} columns + the slab over {fl} ({pcs[fl]['sheet']})") for fl in FLOORS],
                    note="each m3 in one component; blocked columns / beam occurrences excluded and listed (PARTIAL)"))
    out[-1]["matrix"] = "CONCRETE"
    out.append(line("CON-FOOT", "STRUCTURAL_CONCRETE", "Isolated footings (schedule types x tagged plan occurrences)",
                    "القواعد المنفصلة", "m3", [a.ex_part("FOOTINGS", "FOUNDATION")],
                    note="25 of 27 occurrences; F / F10 SOURCE_CONFLICT excluded"))
    out[-1]["matrix"] = "CONCRETE"
    out.append(line("CON-STRAP", "STRUCTURAL_CONCRETE", "Strap beams (SB1 / SB2 / SB3)", "الميدات الرابطة", "m3",
                    [a.ex_part("STRAPS", "FOUNDATION")]))
    out[-1]["matrix"] = "CONCRETE"
    for lid, name, en, ar, lv in (("CON-GBEAM", "GROUND BEAMS", "Ground beams", "الجسور الأرضية", "FOUNDATION"),
                                  ("CON-GSLAB", "GROUND SLAB", "Ground slab", "البلاطة الأرضية", "FOUNDATION"),
                                  ("CON-NECK", "COLUMN NECKS", "Column necks / pedestals", "رقاب الأعمدة", "FOUNDATION"),
                                  ("CON-STAIR", "STAIRS", "Stair concrete (waist + steps + landings)", "خرسانة الدرج", "UNASSIGNED"),
                                  ("CON-SWALL", "STRUCTURAL WALLS", "Structural walls", "الجدران الإنشائية", "UNASSIGNED"),
                                  ("CON-POOL", "POOL", "Swimming pool structure", "المسبح", "EXTERNAL")):
        out.append(line(lid, "STRUCTURAL_CONCRETE", en, ar, "m3", [a.ex_part(name, lv)]))
        out[-1]["matrix"] = "CONCRETE"
    out.append(line("PCC-BLIND", "PLAIN_CONCRETE", "Blinding under computed footings (10 cm, 10 cm beyond L x W - typical detail)",
                    "خرسانة النظافة تحت القواعد", "m3", [a.ex_part("BLINDING (under computed footings)", "FOUNDATION")],
                    note="blocked footings, straps and ground beams not included"))
    out[-1]["matrix"] = "BLINDING"
    ri = _i(a.rb["rows"], lambda r: r["item"] == "rebar weight")
    out.append(line("REBAR", "REBAR", "Reinforcement weight", "وزن حديد التسليح", "kg",
                    [part("UNASSIGNED", blocked("BLOCKED", f"B2A1.REMAINING_BLOCKERS:/rows/{ri}/state"), "BLOCKED",
                          a.rb["rows"][ri]["why"])], note="no kg/m3 ratio is used; unit kg not released"))
    # masonry
    for t in ("150", "200"):
        out.append(line(f"BLK-{t}", "BLOCKWORK", f"Blockwork length, {t} mm wall bands (column overlaps excluded)",
                        a.ab[a.abi[f"A3-BLK-GF-T{t}"]]["ar"], "m", [a.ab_part(f"A3-BLK-{fl}-T{t}") for fl in FLOORS]))
        out[-1]["matrix"] = f"BLOCKWORK {t}"
        out.append(line(f"BLK-{t}-AREA", "BLOCKWORK", f"Blockwork area, {t} mm", a.ab[a.abi[f"A3-BLA-GF-T{t}"]]["ar"], "m2",
                        [a.ab_part(f"A3-BLA-{fl}-T{t}") for fl in FLOORS], note="wall heights not proved"))
    # plaster (B2A terminated faces, gross)
    parts = []
    for fl in FLOORS:
        rows = [(i, r) for i, r in enumerate(a.wh["rows"]) if r["floor"] == fl]
        if rows:
            parts.append(part(fl, qsum([a.R.q(f"B2A1.WALL_HEIGHT_REGISTER:/rows/{i}/plaster_gross_computed_faces_m2") for i, _ in rows]),
                              rows[0][1]["room_plaster_state"], f"{len(rows)} certified rooms, terminated faces only"))
        else:
            parts.append(a.ab_part(f"A3-WFA-{fl}", note="no certified room"))
    out.append(line("PLS-INT", "PLASTER", "Internal plaster - computed (terminated) wall faces of certified rooms, gross of openings",
                    "لياسة داخلية - أوجه الجدران المحسوبة (إجمالي)", "m2", parts,
                    note="other faces / rooms blocked; openings not deducted (heights blocked)"))
    out[-1]["matrix"] = "PLASTER"
    out.append(line("PLS-EXT", "PLASTER", "External plaster / paint (facades)", a.ab[a.abi["A3-EXT-FAC"]]["ar"], "m2",
                    [a.ab_part("A3-EXT-FAC")]))
    # paint / wall tile (B2A wall-height register: blocked by floor build-up)
    for lid, trade, key, en, ar in (("PNT-INT", "PAINT", "paint", "Internal paint", "دهان داخلي"),
                                    ("WTL", "WALL_TILE", "wall_tile", "Wall tile (wet rooms)", "بلاط جدران المناطق المبتلة")):
        ps = []
        for fl in FLOORS:
            rows = [(i, r) for i, r in enumerate(a.wh["rows"]) if r["floor"] == fl and (key == "paint" or r["wet"])]
            if rows:
                i = rows[0][0]
                ps.append(part(fl, blocked(rows[0][1][key], f"B2A1.WALL_HEIGHT_REGISTER:/rows/{i}/{key}"), rows[0][1][key],
                               "floor build-up above each storey not in the source"))
            else:
                ps.append(a.ab_part(f"A3-WFN-{fl}"))
        out.append(line(lid, trade, en, ar, "m2", ps))
    out.append(line("FLT", "FLOOR_TILE", "Floor finish (tile / porcelain / marble)", a.ab[a.abi["A3-FFN-GF"]]["ar"], "m2",
                    [a.ab_part(f"A3-FFN-{fl}") for fl in FLOORS], note="physical floor area of certified rooms is computed - see PHYSICAL MEASURES"))
    out.append(line("CLG-FIN", "CEILING", "Ceiling finish / false ceiling", a.ab[a.abi["A3-CFN-GF"]]["ar"], "m2",
                    [a.ab_part(f"A3-CFN-{fl}") for fl in FLOORS]))
    out.append(line("SKT-MAT", "SKIRTING", "Skirting (material)", a.ab[a.abi["A3-SKM-GF"]]["ar"], "m",
                    [a.ab_part(f"A3-SKM-{fl}") for fl in FLOORS], note="skirting path is computed - see PHYSICAL MEASURES"))
    # physical measures
    fa, cb, sk = [], [], []
    for fl in FLOORS:
        rows = [(i, r) for i, r in a.rooms(fl) if r["floor_area_m2"] is not None]
        cells = [a.R.q(f"A3.ROOM_REGISTER:/rooms/{i}/floor_area_m2") for i, _ in rows]
        if fl == "GF":
            cells.append(a.R.q("B2A1.WALL_HEIGHT_REGISTER:/mbr/floor_area_m2"))
        if cells:
            fa.append(part(fl, qsum(cells), "AUTHORISED_SUBTOTAL", f"{len(cells)} certified rooms; other rooms blocked"))
            cb.append(part(fl, qsum([a.R.q(f"A3.ROOM_REGISTER:/rooms/{i}/base_ceiling_area_m2") for i, _ in rows]), "AUTHORISED_SUBTOTAL",
                           f"{len(rows)} A3 certified rooms (B2A master bedroom: ceiling base not published)"))
            sk.append(part(fl, qsum([a.R.q(f"A3.ROOM_REGISTER:/rooms/{i}/skirting_path_m") for i, _ in rows]), "AUTHORISED_SUBTOTAL",
                           f"{len(rows)} A3 certified rooms"))
        else:
            fa.append(a.ab_part(f"A3-FLR-{fl}"))
            cb.append(a.ab_part(f"A3-CLG-{fl}"))
            sk.append(a.ab_part(f"A3-SKP-{fl}"))
    out.append(line("PHY-FLOOR", "PHYSICAL_AREA", "Floor area - certified rooms, clear internal (finish not assigned)",
                    a.ab[a.abi["A3-FLR-GF"]]["ar"], "m2", fa))
    out[-1]["matrix"] = "FLOOR AREA (certified rooms)"
    out.append(line("PHY-CEIL", "PHYSICAL_AREA", "Ceiling base area - certified rooms (= room plan area)", a.ab[a.abi["A3-CLG-GF"]]["ar"],
                    "m2", cb))
    out.append(line("PHY-SKP", "PHYSICAL_AREA", "Skirting path - certified rooms (perimeter minus door closures)",
                    a.ab[a.abi["A3-SKP-GF"]]["ar"], "m", sk))
    out.append(line("PHY-WFL", "PHYSICAL_AREA", "Wall-face length - certified A3 rooms", a.ab[a.abi["A3-WFL-GF"]]["ar"], "m",
                    [a.ab_part(f"A3-WFL-{fl}") for fl in FLOORS]))
    # waterproofing
    out.append(line("WP-ROOF", "WATERPROOFING", "Roof waterproofing membrane - flat + 0.20 m upturn (laps not included)",
                    "عزل الأسطح - مسطح + رفرف 20 سم", "m2",
                    [part("ROOF", a.R.q(f"B2A1.WATERPROOFING_REGISTER:/roof/{i}/physical_m2"), r["state"], r["region"])
                     for i, r in enumerate(a.wp["roof"])]))
    out[-1]["matrix"] = "WATERPROOFING ROOF"
    wet = [part(r["room"].split(" ")[0], a.R.q(f"B2A1.WATERPROOFING_REGISTER:/wet/{i}/physical_m2"), r["state"], r["room"])
           for i, r in enumerate(a.wp["wet"])]
    for i, r in enumerate(a.rr["rooms"]):
        if r["status"] == "BLOCKED" and r["wet_semantics"].startswith("WET"):
            wet.append(part(r["floor"], blocked(r["status"], f"A3.ROOM_REGISTER:/rooms/{i}/status"), r["status"],
                            f"{r['room']} ({r['blocker']}) - room not certified"))
    out.append(line("WP-WET", "WATERPROOFING", "Wet-room waterproofing - floor + 0.15 m upturn (gross perimeter; laps not included)",
                    "عزل المناطق المبتلة - أرضية + رفرف 15 سم", "m2", wet))
    out[-1]["matrix"] = "WATERPROOFING WET"
    # aluminium / glazing
    out.append(line("ALU-CURVED", "ALUMINIUM_GLAZING", "Curved aluminium glazing - developed length on MIN_RADIUS_ARC (method)",
                    "زجاج منحني - الطول المطور على القوس الأصغر", "m",
                    [part(r["floor"], a.R.q(f"B2A1.CURVED_OPENING_REGISTER:/rows/{i}/commercial_m"), "COMPUTED", r["id"])
                     for i, r in enumerate(a.cu["rows"])], basis="MIN_RADIUS_ARC"))
    out[-1]["matrix"] = "CURVED GLAZING"
    out.append(line("ALU-CURVED-AREA", "ALUMINIUM_GLAZING", "Curved glazing area", a.ab[a.abi["A3-CGL-MB-A"]]["ar"], "m2",
                    [part(r["floor"], blocked("BLOCKED_HEIGHT", f"B2A1.CURVED_OPENING_REGISTER:/rows/{i}/height"), "BLOCKED_HEIGHT", r["id"])
                     for i, r in enumerate(a.cu["rows"])]))
    out.append(line("ALU-SALON", "ALUMINIUM_GLAZING", "Salon sea-view opening - aluminium + glass (width source x height owner-derived)",
                    a.ab[a.abi["A3-ALU-SALON"]]["ar"], "m2",
                    [part("GF", a.ab_cell("A3-ALU-SALON"), a.op["salon"]["state"], "height 3.65 m provisional (OF-B2A-F)")]))
    out.append(line("ALU-SALON-W", "ALUMINIUM_GLAZING", "Salon sea-view opening - width (same item, linear basis)",
                    a.ab[a.abi["A3-ALU-SALON-W"]]["ar"], "m",
                    [part("GF", a.R.q("B2A1.OPENING_AUTHORITY_REGISTER:/salon/width_m"), "COMPUTED", a.op["salon"]["width_authority"])],
                    cls="ALTERNATIVE_MEASURE", alternative_of="ALU-SALON"))
    out.append(line("ALU-WIN-AREA", "ALUMINIUM_GLAZING", "Window / glazing area (straight openings)", a.ab[a.abi["A3-WNA-GF"]]["ar"], "m2",
                    [a.ab_part(f"A3-WNA-{fl}") for fl in FLOORS], note="no sill / head level or window schedule in the source"))
    # windows / doors
    fn = a.op["functions"]
    out.append(line("WIN-CAND", "WINDOWS", "Window candidates - glazing in a wall gap (function not confirmed)",
                    a.ab[a.abi["A3-WIN-GF"]]["ar"], "nr",
                    [part(fl, a.R.q(f"B2A1.OPENING_AUTHORITY_REGISTER:/functions/{fl}|WINDOW_CANDIDATE"), "WINDOW_CANDIDATE")
                     for fl in FLOORS if f"{fl}|WINDOW_CANDIDATE" in fn]))
    out.append(line("WIN-UNK", "WINDOWS", "Glazed openings - function unknown (not a window, not a door)", "", "nr",
                    [part(fl, a.R.q(f"B2A1.OPENING_AUTHORITY_REGISTER:/functions/{fl}|GLAZED_OPENING_FUNCTION_UNKNOWN"),
                          "GLAZED_OPENING_FUNCTION_UNKNOWN") for fl in FLOORS if f"{fl}|GLAZED_OPENING_FUNCTION_UNKNOWN" in fn]))
    out.append(line("DOOR", "DOORS", "Doors - wall gap + door-symbol motif (incl. the 4 GF glazed gaps re-classified as doors, same occurrences)",
                    a.ab[a.abi["A3-DOR-GF"]]["ar"], "nr", [a.ab_part(f"A3-DOR-{fl}") for fl in FLOORS]))
    out.append(line("DOOR-TYPE", "DOORS", "Door type / material / height", a.ab[a.abi["A3-DRM-GF"]]["ar"], "nr",
                    [a.ab_part(f"A3-DRM-{fl}") for fl in FLOORS]))
    out.append(line("STAIR-FIN", "STAIRS", "Stair finish, risers, railing", a.ab[a.abi["A3-STR-GF"]]["ar"], "m",
                    [a.ab_part(f"A3-STR-{fl}") for fl in FLOORS]))
    out.append(line("JNY", "PHYSICAL_AREA", "Fixed joinery / counter front length (engine inferred)", a.ab[a.abi["A3-JNY-GF"]]["ar"], "m",
                    [a.ab_part("A3-JNY-GF"), a.ab_part("A3-JNY-1F")]))
    return out


GROUPS = {  # line id -> (trade-total group key, EN label, AR label); one group = one kind of item in one unit
    "CON-*": ("CON", "Structural concrete - superstructure + substructure", "الخرسانة الإنشائية"),
    "PCC-BLIND": ("PCC", "Blinding under footings", "خرسانة النظافة"), "REBAR": ("REBAR", "Reinforcement", "حديد التسليح"),
    "BLK-150": ("BLK150", "Blockwork 150 mm - length", "طول البلوك 150 مم"), "BLK-200": ("BLK200", "Blockwork 200 mm - length", "طول البلوك 200 مم"),
    "BLK-150-AREA": ("BLKA", "Blockwork area (150 + 200 mm)", "مساحة البلوك"), "BLK-200-AREA": ("BLKA", "Blockwork area (150 + 200 mm)", "مساحة البلوك"),
    "PLS-INT": ("PLSI", "Internal plaster - computed wall faces (gross)", "لياسة داخلية"), "PLS-EXT": ("PLSE", "External plaster / paint", "لياسة ودهان الواجهات"),
    "PNT-INT": ("PNT", "Internal paint", "دهان داخلي"), "WTL": ("WTL", "Wall tile (wet rooms)", "بلاط الجدران"),
    "FLT": ("FLT", "Floor finish (tile / porcelain / marble)", "بلاط الأرضيات"), "CLG-FIN": ("CLG", "Ceiling finish / false ceiling", "تشطيب الأسقف"),
    "SKT-MAT": ("SKT", "Skirting (material)", "مادة الوزرة"), "PHY-FLOOR": ("PHYF", "Floor area - certified rooms (physical)", "مساحة الأرضيات (صافي)"),
    "PHY-CEIL": ("PHYC", "Ceiling base area - certified rooms", "مساحة السقف الأساسية"), "PHY-SKP": ("PHYS", "Skirting path - certified rooms", "مسار الوزرة"),
    "PHY-WFL": ("PHYW", "Wall-face length - certified rooms", "طول أوجه الجدران"), "JNY": ("JNY", "Fixed joinery front length", "طول واجهات الخزائن الثابتة"),
    "WP-ROOF": ("WPR", "Roof waterproofing (flat + 0.20 m upturn)", "عزل الأسطح"), "WP-WET": ("WPW", "Wet-room waterproofing (floor + 0.15 m upturn)", "عزل المناطق المبتلة"),
    "ALU-CURVED": ("ALUC", "Curved glazing - developed length (MIN_RADIUS_ARC)", "طول الزجاج المنحني"),
    "ALU-SALON": ("ALUS", "Salon sea-view opening (aluminium + glass)", "ألمنيوم وزجاج - واجهة الصالون"),
    "ALU-CURVED-AREA": ("ALUA", "Glazing area (straight + curved)", "مساحة الزجاج"), "ALU-WIN-AREA": ("ALUA", "Glazing area (straight + curved)", "مساحة الزجاج"),
    "WIN-CAND": ("WINC", "Window candidates (count)", "عدد الشبابيك (مرشحة)"), "WIN-UNK": ("WINU", "Glazed openings - function unknown (count)", "فتحات زجاجية غير محددة"),
    "DOOR": ("DOOR", "Doors (count)", "عدد الأبواب"), "DOOR-TYPE": ("DOORT", "Door type / material / height", "نوع ومادة الأبواب"),
    "STAIR-FIN": ("STF", "Stair finish, risers, railing", "تشطيب الدرج والدرابزين"),
}


def set_groups(lines):
    for ln in lines:
        g = GROUPS.get(ln["id"]) or (GROUPS["CON-*"] if ln["id"].startswith("CON-") else None)
        if g is None and ln["cls"] == "ADDITIVE":
            raise KeyError(f"no trade-total group for line {ln['id']}")
        ln["group"] = g


# ------------------------------------------------------------------ floor sheets
def _stc(code):
    return display_status(code)


def room_section(a: A, fl):
    cols = [col("id", "ROOM ID", "", "code", width=12), col("en", "ROOM NAME EN", "", "text", width=24),
            col("ar", "ROOM NAME AR", "اسم الغرفة", "ar", width=14), col("fa", "FLOOR AREA", "مساحة الأرضية", "qty", "m2", 12),
            col("cb", "CEILING BASE", "مساحة السقف", "qty", "m2", 12), col("sk", "SKIRTING PATH", "مسار الوزرة", "qty", "m", 12),
            col("ff", "FLOOR FINISH", "تشطيب الأرضية", "text", width=12), col("wt", "WALL TILE", "بلاط الجدران", "text", width=12),
            col("st", "STATUS", "الحالة", "status", width=11), col("tech", "TECHNICAL CODE / ISSUE", "", "code", width=22)]
    rows, fa_cells = [], []
    for i, r in a.rooms(fl):
        if a.is_mbr(r):
            fa = a.R.q("B2A1.WALL_HEIGHT_REGISTER:/mbr/floor_area_m2")
            fa_cells.append(fa)
            rows.append(row([r["site"][5:13], r["room"] + " (B2A: wardrobe fact OF-B2A-C)", "", fa, na("not published"),
                             na("not published"), "BLOCKED", "BLOCKED", "COMPUTED", a.wh["mbr"]["state"]],
                            cls="BREAKDOWN_ONLY", status="COMPUTED", tech=a.wh["mbr"]["state"], explains=f"PHY-FLOOR@{fl}"))
            continue
        if r["floor_area_m2"] is not None:
            fa = a.R.q(f"A3.ROOM_REGISTER:/rooms/{i}/floor_area_m2")
            fa_cells.append(fa)
            wt = "BLOCKED" if r["wet_semantics"].startswith("WET") else "—"
            rows.append(row([r["site"][5:13], r["room"], "", fa, a.R.q(f"A3.ROOM_REGISTER:/rooms/{i}/base_ceiling_area_m2"),
                             a.R.q(f"A3.ROOM_REGISTER:/rooms/{i}/skirting_path_m"), "BLOCKED", wt, _stc(r["status"]), r["status"]],
                            cls="BREAKDOWN_ONLY", status=_stc(r["status"]), tech=r["status"], explains=f"PHY-FLOOR@{fl}"))
        else:
            rows.append(row([r["site"][5:13], r["room"], "", blocked(r["status"]), blocked(r["status"]), blocked(r["status"]),
                             "BLOCKED", "BLOCKED", "BLOCKED", f"{r['status']}: {r['blocker']}"],
                            cls="BREAKDOWN_ONLY", status="BLOCKED", tech=r["status"], explains=f"PHY-FLOOR@{fl}"))
    if fl == "GF":
        rows.append(row(["RECEPTION", "RECEPTION - double-height region (plan span from the slab opening, OF-B2A-B)", "",
                         a.R.q("B2A1.WALL_HEIGHT_REGISTER:/reception/area_m2"), na("—"), na("—"), "BLOCKED", "—",
                         _stc(a.wh["reception"]["state"]), a.wh["reception"]["state"]],
                        cls="TRACE_ONLY", status=_stc(a.wh["reception"]["state"]), tech=a.wh["reception"]["state"],
                        note="plan span only - not a certified room floor; not in the floor-area line"))
        rows.append(row(["OPEN ZONE", "DINING / RECEPTION / SALON (open to each other, OF-B2A-A)", "", blocked("NOT_CLOSED"),
                         blocked("NOT_CLOSED"), blocked("NOT_CLOSED"), "BLOCKED", "—", "BLOCKED", a.wh["gf_open_site"]["state"]],
                        cls="BREAKDOWN_ONLY", status="BLOCKED", tech="NOT_CLOSED", explains=f"PHY-FLOOR@{fl}"))
    if fa_cells:
        rows.append(row(["SUBTOTAL", "Certified rooms - floor area", "", qsum(fa_cells) if len(fa_cells) > 1 else dict(fa_cells[0]),
                         "", "", "", "", "PARTIAL", "AUTHORISED_SUBTOTAL"], role="SUBTOTAL", status="PARTIAL",
                        tech="AUTHORISED_SUBTOTAL", explains=f"PHY-FLOOR@{fl}"))
    if not rows:
        rows.append(row(["—", "No certified room on this floor (A3 room register)", "", blocked("BLOCKED"), blocked("BLOCKED"),
                         blocked("BLOCKED"), "BLOCKED", "BLOCKED", "BLOCKED", "BLOCKED"], cls="BREAKDOWN_ONLY", status="BLOCKED",
                        tech="BLOCKED", explains=f"PHY-FLOOR@{fl}"))
    return section("ROOMS", T.section("ROOMS"), cols, rows,
                   note="Physical measure (floor area, ceiling base, skirting path) and finish material are separate: a computed "
                        "floor area with a BLOCKED finish means the area is known but the material is not.")


def structure_sections(a: A, fl):
    R = a.R
    st = a.pc["storeys"][fl]
    m = st["model"]
    base = f"B2A1.PHYSICAL_CONCRETE_REGISTER:/storeys/{fl}"
    comp = OrderedDict((k, []) for k in ("SLAB", "DOWNSTAND_BEAM", "BEAM_COLUMN_JOINT", "COLUMN"))
    for k, c in enumerate(m["components"]):
        comp[c["component"]].append(k)
    blk = OrderedDict()
    for b in m["blocked"]:
        blk[b["component"]] = blk.get(b["component"], 0) + 1
    cols = [col("item", "ITEM", "البند", "text", width=26), col("basis", "TYPE / BASIS", "الأساس", "text", width=30),
            col("n", "COUNT (computed / blocked)", "العدد", "text", width=14), col("qty", "QTY", "الكمية", "qty", "m3", 13),
            col("unit", "UNIT", "", "text", width=6), col("st", "STATUS", "الحالة", "status", width=11),
            col("cls", "CLASS", "", "cls", width=14)]
    names = {"SLAB": ("Slab concrete", f"net plate area x t ({st['slab_thickness_cm']} cm); sheet {st['sheet']}"),
             "DOWNSTAND_BEAM": ("Beam downstand", "clear length x B x (D - t)"),
             "BEAM_COLUMN_JOINT": ("Beam-column joints", "column area x (D_ctrl - t)"),
             "COLUMN": ("Column concrete", "column area x (interval - D of the member framing in)")}
    rows = []
    for k, idx in comp.items():
        if not idx:
            continue
        cell = R.q(f"{base}/model/by_component_m3/{k}")
        nb = blk.get(k, 0)
        status = "PARTIAL" if nb else "COMPUTED"
        rows.append(row([names[k][0], names[k][1], f"{len(idx)} / {nb}", cell, "m3", status, "BREAKDOWN_ONLY"],
                        cls="BREAKDOWN_ONLY", status=status, tech="COMPUTED_PARTIAL" if nb else "COMPUTED", explains=f"CON-SUPER@{fl}"))
    rows.append(row([f"STOREY {fl} PHYSICAL TOTAL", "sum of the components above (register total)", "",
                     R.q(f"{base}/model/computed_total_m3"), "m3", _stc(m["total_state"]), "BREAKDOWN_ONLY"],
                    role="SUBTOTAL", status=_stc(m["total_state"]), tech=m["total_state"], explains=f"CON-SUPER@{fl}"))
    rows.append(row(["Gross beam view (not additive)", "beam B x D x clear length incl. the slab depth - overlaps the slab", "",
                     R.q(f"{base}/gross_beam_view_m3"), "m3", "INFO", "ALTERNATIVE_MEASURE"],
                    cls="ALTERNATIVE_MEASURE", status="INFO", tech="INFO", explains=f"CON-SUPER@{fl}"))
    sl = a.R.data["B2A1.SLAB_REGION_REGISTER"]["sheets"][fl]
    rows.append(row(["Slab net plate area", f"gross {sl['gross_outline_area_m2']} - openings {sl['openings_area_m2']} m2 (outline {sl['closure']})",
                     "", R.q(f"B2A1.SLAB_REGION_REGISTER:/sheets/{fl}/net_plate_area_m2") | {"unit": "m2"}, "m2", "INFO", "TRACE_ONLY"],
                    cls="TRACE_ONLY", status="INFO", tech="INFO"))
    sec_main = section("STRUCTURE", T.section("STRUCTURE"), cols, rows,
                       note=f"Storey {fl} = the {fl} columns + the slab over {fl} (register storey); blocked components are excluded and "
                            "listed in the notes.")
    # beams by type
    occ = a.bb["sheets"][fl]["occurrences"]
    types = OrderedDict()
    for k, o in enumerate(occ):
        types.setdefault(o["type"], []).append(k)
    bcols = [col("type", "TYPE", "النوع", "text", width=8), col("ns", "NAMESPACE", "", "text", width=12),
             col("bd", "B x D (cm)", "", "text", width=10), col("n", "OCCURRENCES (measured / found)", "", "text", width=14),
             col("len", "CLEAR LENGTH", "الطول الصافي", "qty", "m", 12), col("vol", "DOWNSTAND", "الحجم", "qty", "m3", 12),
             col("st", "STATUS", "الحالة", "status", width=11)]
    brows = []
    for t, ks in types.items():
        meas = [k for k in ks if occ[k]["state"] == "MEASURED" and (occ[k]["lengths"] or {}).get("CLEAR_FACE_TO_FACE_LENGTH") is not None]
        lens = [R.q(f"B2A1.BEAM_BINDING_REGISTER:/sheets/{fl}/occurrences/{k}/lengths/CLEAR_FACE_TO_FACE_LENGTH") for k in meas]
        vols = [R.q(f"{base}/model/components/{k}/volume_m3") for k, c in enumerate(m["components"])
                if c["component"] == "DOWNSTAND_BEAM" and c["id"].split(":")[0] == t]
        o0 = occ[ks[0]]
        st_ = "COMPUTED" if len(meas) == len(ks) else ("PARTIAL" if meas else "BLOCKED")
        brows.append(row([t, o0["namespace"], f"{o0['B_cm']:g} x {o0['D_cm']:g}", f"{len(meas)} / {len(ks)}",
                          (qsum(lens) if len(lens) > 1 else dict(lens[0])) if lens else blocked("NOT_MEASURED"),
                          (qsum(vols) if len(vols) > 1 else dict(vols[0])) if vols else blocked("NOT_MEASURED"), st_],
                         cls="BREAKDOWN_ONLY", status=st_, tech={"COMPUTED": "COMPUTED", "PARTIAL": "COMPUTED_PARTIAL"}.get(st_, "BLOCKED"),
                         explains=f"CON-SUPER@{fl}"))
    sec_b = section("BEAMS", T.section("BEAMS"), bcols, brows,
                    note="Summary of TECH_BEAM_OCCURRENCES. Unbound beam tags (no plan occurrence) are counted in the notes.")
    # columns by type
    rws = [(k, r) for k, r in enumerate(a.sv["rows"]) if r["floor"] == fl and r["state"] not in ("NOT_IN_STOREY", "NOT_DRAWN_ON_STOREY_SHEET")]
    ct = OrderedDict()
    for k, r in rws:
        ct.setdefault(r["type"], []).append((k, r))
    ccols = [col("type", "TYPE", "النوع", "text", width=8), col("bd", "B x D (cm)", "", "text", width=10),
             col("n", "COUNT (computed / found)", "", "text", width=14),
             col("vol", "COLUMN CONCRETE", "خرسانة الأعمدة", "qty", "m3", 13), col("jt", "JOINTS", "العقد", "qty", "m3", 11),
             col("st", "STATUS", "الحالة", "status", width=11), col("tech", "BLOCKED STATES", "", "code", width=24)]
    crows = []
    for t, ks in ct.items():
        done = [(k, r) for k, r in ks if r.get("volume_m3") is not None]
        vols = [R.q(f"B2A1.STRUCTURAL_VERTICAL_INTERVAL_REGISTER:/rows/{k}/volume_m3") for k, _ in done]
        jts = [R.q(f"B2A1.STRUCTURAL_VERTICAL_INTERVAL_REGISTER:/rows/{k}/joint_m3") for k, r in done if r.get("joint_m3") is not None]
        bad = sorted({r["state"] for _, r in ks if r.get("volume_m3") is None})
        st_ = "COMPUTED" if not bad else ("PARTIAL" if done else "BLOCKED")
        sizes = sorted({f"{r['B_cm']:g} x {r['D_cm']:g}" for _, r in ks if r.get("B_cm")})
        crows.append(row([t, ", ".join(sizes), f"{len(done)} / {len(ks)}",
                          (qsum(vols) if len(vols) > 1 else dict(vols[0])) if vols else blocked(bad[0] if bad else "BLOCKED"),
                          (qsum(jts) if len(jts) > 1 else dict(jts[0])) if jts else na("—"), st_, ", ".join(bad)],
                         cls="BREAKDOWN_ONLY", status=st_, tech=bad[0] if bad else "COMPUTED", explains=f"CON-SUPER@{fl}"))
    sec_c = section("COLUMNS", T.section("COLUMNS"), ccols, crows, note="Summary of TECH_COLUMN_OCCURRENCES (columns present on this storey).")
    return [sec_main, sec_b, sec_c]


def opening_section(a: A, fl, *, all_floors=False):
    cols = [col("id", "OPENING ID", "رقم الفتحة", "code", width=11), col("fl", "FLOOR", "", "text", width=6),
            col("loc", "ROOM / LOCATION", "الموقع", "text", width=24), col("fn", "FUNCTION", "الوظيفة", "text", width=22),
            col("mat", "MATERIAL", "المادة", "text", width=14), col("w", "WIDTH (mm)", "العرض", "num", width=10),
            col("h", "HEIGHT", "الارتفاع", "text", width=14), col("q", "QTY / AREA / LENGTH", "الكمية", "qty", None, 13),
            col("u", "UNIT", "", "text", width=6), col("st", "STATUS", "الحالة", "status", width=11),
            col("basis", "MEASUREMENT BASIS", "أساس القياس", "text", width=28)]
    rows = []
    floors = FLOORS if all_floors else (fl,)
    groups = (("DOOR", "DOORS (re-classified glazed gaps - counted in the door line)"),
              ("WINDOW_CANDIDATE", "WINDOW CANDIDATES"),
              ("GLAZED_OPENING_FUNCTION_UNKNOWN", "GLAZED OPENINGS - FUNCTION UNKNOWN"))
    for f in floors:
        doors = a.ab_part(f"A3-DOR-{f}")
        rows.append(row([f"DOORS {f}", f, "all rooms", "DOOR (count)", "BLOCKED (type / material)", None, "BLOCKED",
                         doors["cell"] | {"unit": "nr"}, "nr", doors["status"], "A3 door register: wall gap + door-symbol motif"],
                        cls="BREAKDOWN_ONLY", status=doors["status"], tech=doors["tech"], explains=f"DOOR@{f}"))
    for fn, title in groups:
        sel = [(k, r) for k, r in enumerate(a.op["rows"]) if r["floor"] in floors and r["function"] == fn]
        if not sel:
            continue
        rows.append(row([title, "", "", "", "", None, "", None, "", None, ""], role="NOTE", note="GROUP"))
        for k, r in sel:
            loc = " / ".join(sorted({lab for s in r["sides"] for lab in s["labels"] if lab})) or "—"
            st_ = _stc(fn)
            basis = "salon: width 6.33 m source, height 3.65 m owner-derived (REVIEW)" if r["id"] == a.op["salon"]["opening"] else \
                r["existence"].split(" (")[0].replace("_", " ").lower()
            rows.append(row([r["id"], r["floor"], loc, fn.replace("_", " "), r["material"].replace("_", " "),
                             r["geometry"]["width_mm"], r["height"].split(" (")[0], na("area blocked"), "", st_, basis],
                            cls="TRACE_ONLY", status=st_, tech=fn))
    cur = [(k, r) for k, r in enumerate(a.cu["rows"]) if r["floor"] in floors]
    if cur:
        rows.append(row(["CURVED GLAZING", "", "", "", "", None, "", None, "", None, ""], role="NOTE", note="GROUP"))
        for k, r in cur:
            rows.append(row([r["id"], r["floor"], " / ".join(r["host_labels"]), "CURVED GLAZING (aluminium)", "aluminium + glass",
                             None, "BLOCKED_HEIGHT", a.R.q(f"B2A1.CURVED_OPENING_REGISTER:/rows/{k}/commercial_m") | {"unit": "m"}, "m",
                             "COMPUTED", f"{r['commercial_basis']} ({r['authority']}); room side {r['orientation'].get('room_side')}"],
                            cls="BREAKDOWN_ONLY", status="COMPUTED", tech="COMPUTED", explains=f"ALU-CURVED@{r['floor']}"))
    if "GF" in floors:
        rows.append(row(["SALON", "GF", "SALOON", "ALUMINIUM + GLASS (sea view)", "aluminium + glass (OF-B2A-D)",
                         None, "3.65 m owner-derived", a.ab_cell("A3-ALU-SALON") | {"unit": "m2"}, "m2", _stc(a.op["salon"]["state"]),
                         "width 6.33 m source x height 3.65 m provisional (OF-B2A-F)"],
                        cls="BREAKDOWN_ONLY", status=_stc(a.op["salon"]["state"]), tech=a.op["salon"]["state"], explains="ALU-SALON@GF"))
    sid = "OPENING_SCHEDULE" if all_floors else "OPENINGS"
    return section(sid, T.section(sid), cols, rows,
                   note="An opening is never published as WINDOW without function authority; window area stays BLOCKED until a "
                        "head / sill height exists. Door count is the door line (the 4 re-classified glazed gaps are the same occurrences).")


def finishes_section(a: A, fl):
    cols = [col("trade", "TRADE", "البند", "text", width=24), col("ar", "", "", "ar", width=22),
            col("loc", "ROOM / AREA", "الموقع", "text", width=20), col("q", "QTY", "الكمية", "qty", None, 13),
            col("u", "UNIT", "", "text", width=6), col("st", "STATUS", "الحالة", "status", width=11),
            col("note", "NOTE", "ملاحظة", "text", width=30)]
    rows = []
    for t in ("150", "200"):
        p = a.ab_part(f"A3-BLK-{fl}-T{t}")
        rows.append(row([f"BLOCKWORK {t} mm (length)", T.trade("BLOCKWORK")[1], "all walls", p["cell"] | {"unit": "m"}, "m", p["status"],
                         a.ab[a.abi[f"A3-BLK-{fl}-T{t}"]]["element"]], cls="BREAKDOWN_ONLY", status=p["status"], tech=p["tech"],
                        explains=f"BLK-{t}@{fl}"))
        p = a.ab_part(f"A3-BLA-{fl}-T{t}")
        rows.append(row([f"BLOCKWORK {t} mm (area)", T.trade("BLOCKWORK")[1], "all walls", p["cell"], "m2", p["status"],
                         "wall heights not proved"], cls="BREAKDOWN_ONLY", status=p["status"], tech=p["tech"],
                        explains=f"BLK-{t}-AREA@{fl}"))
    for k, r in [(k, r) for k, r in enumerate(a.wh["rows"]) if r["floor"] == fl]:
        rows.append(row(["PLASTER (internal, gross)", T.trade("PLASTER")[1], r["room"],
                         a.R.q(f"B2A1.WALL_HEIGHT_REGISTER:/rows/{k}/plaster_gross_computed_faces_m2") | {"unit": "m2"}, "m2", "PARTIAL",
                         f"{r['faces_terminated']} / {r['faces_total']} faces terminated; openings not deducted"],
                        cls="BREAKDOWN_ONLY", status="PARTIAL", tech=r["room_plaster_state"], explains=f"PLS-INT@{fl}"))
    for lid, label in (("PNT-INT", "PAINT"), ("WTL", "WALL TILE"), ("FLT", "FLOOR FINISH"), ("CLG-FIN", "CEILING FINISH"),
                       ("SKT-MAT", "SKIRTING (material)")):
        rows.append(row([label, "", "all rooms", blocked("BLOCKED"), "m2" if lid != "SKT-MAT" else "m", "BLOCKED",
                         T.explain(_line_part_tech(a, lid, fl))["why"]], cls="BREAKDOWN_ONLY", status="BLOCKED",
                        tech=_line_part_tech(a, lid, fl), explains=f"{lid}@{fl}"))
    for k, r in [(k, r) for k, r in enumerate(a.wp["wet"]) if r["room"].startswith(fl + " ")]:
        rows.append(row(["WATERPROOFING (wet room)", T.trade("WATERPROOFING")[1], r["room"][len(fl) + 1:],
                         a.R.q(f"B2A1.WATERPROOFING_REGISTER:/wet/{k}/physical_m2") | {"unit": "m2"}, "m2", _stc(r["state"]),
                         f"floor {r['floor_m2']} + upturn {r['upturn_m']} m x {r['upturn_length_m']} m ({r['upturn_basis']})"],
                        cls="BREAKDOWN_ONLY", status=_stc(r["state"]), tech=r["state"], explains=f"WP-WET@{fl}"))
    if f"A3-STR-{fl}" in a.abi:
        p = a.ab_part(f"A3-STR-{fl}")
        rows.append(row(["STAIR FINISH / RAILING", T.trade("STAIRS")[1], "stairs", p["cell"], "m", p["status"], "riser height not printed"],
                        cls="BREAKDOWN_ONLY", status=p["status"], tech=p["tech"], explains=f"STAIR-FIN@{fl}"))
    if f"A3-JNY-{fl}" in a.abi:
        p = a.ab_part(f"A3-JNY-{fl}")
        rows.append(row(["FIXED JOINERY (front length)", "", a.ab[a.abi[f"A3-JNY-{fl}"]]["element"][:40], p["cell"] | {"unit": "m"}, "m",
                         p["status"], "engine inferred"], cls="BREAKDOWN_ONLY", status=p["status"], tech=p["tech"], explains=f"JNY@{fl}"))
    return section("FINISHES", T.section("FINISHES"), cols, rows)


def _line_part_tech(a, lid, fl):
    for ln in a.lines:
        if ln["id"] == lid:
            for p in ln["parts"]:
                if p["level"] == fl:
                    return p["tech"]
    return "BLOCKED"


def notes_section(a: A, fl):
    cols = [col("item", "ITEM", "البند", "text", width=26), col("st", "STATUS", "الحالة", "status", width=11),
            col("why", "WHY (user-facing)", "السبب", "text", width=30), col("effect", "EFFECT", "الأثر", "text", width=24),
            col("need", "WHAT IS NEEDED", "المطلوب", "text", width=24), col("tech", "TECHNICAL CODE", "", "code", width=22)]
    rows = []
    for r in a.rb["rows"]:
        if not (r["item"].endswith(" " + fl) or f" {fl} " in r["item"] + " "):
            continue
        e = T.explain(r["state"])
        cnt = f" x{r['count']}" if r.get("count") else ""
        rows.append(row([r["item"] + cnt, _stc(r["state"]), e["why"], e["effect"], e["needed"], r["state"]],
                        role="NOTE", status=_stc(r["state"]), tech=r["state"]))
    for i, r in a.rooms(fl):
        if r["status"] == "BLOCKED" and not a.is_mbr(r):
            code = r["blocker"].split(";")[0].strip()
            e = T.explain(code)
            rows.append(row([f"ROOM {r['room']}", "BLOCKED", e["why"], e["effect"], e["needed"], r["blocker"]],
                            role="NOTE", status="BLOCKED", tech="BLOCKED"))
    nb = len(a.pc["storeys"][fl]["model"]["blocked"])
    rows.append(row([f"Concrete components excluded ({fl})", "PARTIAL", f"{nb} beam / column components could not be measured",
                     "excluded from the storey total (never counted as 0)", "see the items above", "COMPUTED_PARTIAL"],
                    role="NOTE", status="PARTIAL", tech="COMPUTED_PARTIAL"))
    return section("NOTES", T.section("NOTES"), cols, rows)


def kpi_section(a: A, fl, lines):
    cols = [col("rooms", "ROOMS CERTIFIED", "الغرف", "count", width=13), col("open", "OPENINGS (register rows)", "الفتحات", "count", width=13),
            col("con", "STRUCTURAL CONCRETE", "الخرسانة", "qty", "m3", 14), col("cs", "CONCRETE STATUS", "", "status", width=12),
            col("fin", "FINISHES STATUS", "التشطيبات", "status", width=12), col("blk", "BLOCKER NOTES", "المعوقات", "count", width=12)]
    rooms = sum(1 for _, r in a.rooms(fl) if r["floor_area_m2"] is not None) + (1 if fl == "GF" else 0)
    opens = sum(1 for r in a.op["rows"] if r["floor"] == fl) + sum(1 for r in a.cu["rows"] if r["floor"] == fl)
    fin = worst([p["status"] for ln in lines if ln["trade"] in ("PLASTER", "PAINT", "FLOOR_TILE", "WALL_TILE", "CEILING", "SKIRTING")
                 for p in ln["parts"] if p["level"] == fl])
    fin = "PARTIAL" if fin == "BLOCKED" and any(p["cell"]["q"] is not None for ln in lines if ln["trade"] == "PLASTER"
                                                for p in ln["parts"] if p["level"] == fl) else fin
    cs = display_status(a.pc["storeys"][fl]["model"]["total_state"])
    nb = len(notes_section(a, fl)["rows"])
    r = row([rooms, opens, a.R.q(f"B2A1.PHYSICAL_CONCRETE_REGISTER:/storeys/{fl}/model/computed_total_m3"), cs, fin, nb],
            cls="BREAKDOWN_ONLY", status=cs, tech=a.pc["storeys"][fl]["model"]["total_state"], explains=f"CON-SUPER@{fl}")
    return section("KPI", T.section("KPI"), cols, [r], kind="kpi",
                   note="Counts are register rows (information); the concrete figure is the storey line on 00_TOTAL_SUMMARY.")


def roof_wp_section(a: A):
    cols = [col("reg", "ROOF REGION", "المنطقة", "text", width=30), col("flat", "NET MEMBRANE (flat)", "مسطح", "qty", "m2", 13),
            col("uh", "UPTURN HEIGHT", "ارتفاع الرفرف", "dim", "m", 10), col("ul", "UPTURN LENGTH", "طول الرفرف", "qty", "m", 11),
            col("ua", "UPTURN AREA", "مساحة الرفرف", "qty", "m2", 11), col("phys", "PHYSICAL MEMBRANE", "الإجمالي", "qty", "m2", 13),
            col("st", "STATUS", "الحالة", "status", width=11), col("m", "METHOD / LAPS", "", "text", width=34)]
    rows = []
    for k, r in enumerate(a.wp["roof"]):
        b = f"B2A1.WATERPROOFING_REGISTER:/roof/{k}"
        rows.append(row([r["region"], a.R.q(f"{b}/flat_m2"), a.R.q(f"{b}/upturn_m"), na("not published"), a.R.q(f"{b}/upturn_m2"),
                         a.R.q(f"{b}/physical_m2"), _stc(r["state"]), f"{r['method']}; laps {r['laps']}"],
                        cls="BREAKDOWN_ONLY", status=_stc(r["state"]), tech=r["state"], explains="WP-ROOF@ROOF"))
    return section("ROOF_WP", T.section("ROOF_WP"), cols, rows,
                   note="Roof membrane only - wet-room waterproofing is reported on each floor sheet. Flat + upturn = physical membrane; "
                        "the upturn length is not published by the register.")


def floor_sheet(a: A, name, fl, lines, *, roof=False):
    title = T.level(fl) if not roof else ("ROOF / SECOND FLOOR", "السطح / الدور الثاني")
    secs = [kpi_section(a, fl, lines), room_section(a, fl)] + structure_sections(a, fl) + \
           [opening_section(a, fl), finishes_section(a, fl)]
    if roof:
        secs.append(roof_wp_section(a))
    secs.append(notes_section(a, fl))
    return sheet(name, title, "BREAKDOWN", secs, level=fl)


# ------------------------------------------------------------------ foundation
def foundation_sheet(a: A):
    R = a.R
    fcols = [col("t", "TYPE", "النوع", "text", width=8), col("nf", "COUNT FOUND", "العدد", "count", width=9),
             col("nc", "COUNT COMPUTED", "المحسوب", "count", width=10), col("l", "SIZE L", "", "dim", "m", 9),
             col("w", "SIZE W", "", "dim", "m", 9), col("h", "SIZE H", "", "dim", "m", 9),
             col("e", "M3 EACH", "للواحدة", "qty", "m3", 10), col("tot", "TOTAL M3", "الإجمالي", "qty", "m3", 11),
             col("st", "STATUS", "الحالة", "status", width=11), col("tech", "TECHNICAL STATUS", "", "code", width=26)]
    frows, cells = [], []
    for k, t in enumerate(a.ft["type_summary"]):
        b = f"A3.FOOTING_REGISTER:/type_summary/{k}"
        tech = t["status"]
        st_ = display_status(tech)
        tot = R.q(f"{b}/m3_total_computed") if t["count_computed"] else (blocked(tech) if t["count_tagged"] else na("not on plan"))
        if t["count_computed"]:
            cells.append(tot)
        frows.append(row([t["type"], t["count_tagged"], t["count_computed"], t["L_m"], t["W_m"], t["H_m"], R.q(f"{b}/m3_each"), tot,
                          st_, tech], cls="BREAKDOWN_ONLY", status=st_, tech=tech, explains="CON-FOOT@FOUNDATION"))
    frows.append(row(["SUBTOTAL", None, None, None, None, None, "", qsum(cells), "PARTIAL", "COMPUTED_PARTIAL"],
                     role="SUBTOTAL", status="PARTIAL", tech="COMPUTED_PARTIAL", explains="CON-FOOT@FOUNDATION"))
    sec_f = section("FOOTINGS", T.section("FOOTINGS"), fcols, frows,
                    note="F / F10: one outline carries two marks (SOURCE_CONFLICT) - excluded until the owner / consultant decides; "
                         "F7 is scheduled but not tagged on the plan. Occurrence detail: TECH_SOURCE_HANDLES.")
    scols = [col("t", "TYPE", "النوع", "text", width=8), col("n", "COUNT", "العدد", "count", width=8),
             col("b", "B (cm)", "", "num", width=8), col("d", "D (cm)", "", "num", width=8),
             col("len", "LENGTH", "الطول", "qty", "m", 11), col("v", "M3", "الحجم", "qty", "m3", 11),
             col("st", "STATUS", "الحالة", "status", width=11), col("tech", "STATE", "", "code", width=30)]
    srows, sv = [], []
    for k, r in enumerate(a.sb["rows"]):
        b = f"A3.STRAP_BEAM_REGISTER:/rows/{k}"
        v = R.q(f"{b}/volume_m3")
        sv.append(v)
        srows.append(row([r["type"], 1, r["B_cm"], r["D_cm"], R.q(f"{b}/length_m"), v, display_status(r["status"]), r["state"]],
                         cls="BREAKDOWN_ONLY", status=display_status(r["status"]), tech=r["status"], explains="CON-STRAP@FOUNDATION"))
    srows.append(row(["SUBTOTAL", None, None, None, "", qsum(sv), "COMPUTED", ""], role="SUBTOTAL", status="COMPUTED", tech="COMPUTED",
                     explains="CON-STRAP@FOUNDATION"))
    sec_s = section("STRAPS", T.section("STRAPS"), scols, srows)
    ocols = [col("item", "ITEM", "البند", "text", width=26), col("q", "QTY", "الكمية", "qty", "m3", 12),
             col("st", "STATUS", "الحالة", "status", width=11), col("why", "BASIS / REASON", "السبب", "text", width=70),
             col("tech", "TECHNICAL STATUS", "", "code", width=24)]
    orows = []
    for name, lid, lv in (("BLINDING (under computed footings)", "PCC-BLIND", "FOUNDATION"), ("GROUND SLAB", "CON-GSLAB", "FOUNDATION"),
                          ("GROUND BEAMS", "CON-GBEAM", "FOUNDATION"), ("COLUMN NECKS", "CON-NECK", "FOUNDATION"),
                          ("STRUCTURAL WALLS", "CON-SWALL", "UNASSIGNED"), ("POOL", "CON-POOL", "EXTERNAL")):
        p = a.ex_part(name, lv)
        orows.append(row([name.title() if name.isupper() else name, p["cell"], p["status"], p["note"] or "", p["tech"]],
                         cls="BREAKDOWN_ONLY", status=p["status"], tech=p["tech"], explains=f"{lid}@{lv}"))
    sec_o = section("SUBSTRUCTURE_OTHER", T.section("SUBSTRUCTURE_OTHER"), ocols, orows,
                    note="Every substructure item is shown: COMPUTED or BLOCKED with its reason - none is silently omitted.")
    return sheet("04_FOUNDATION_SUBSTRUCTURE", T.level("FOUNDATION"), "BREAKDOWN", [sec_f, sec_s, sec_o], level="FOUNDATION")


# ------------------------------------------------------------------ openings / blockers / methods
def openings_sheet(a: A):
    s1 = opening_section(a, None, all_floors=True)
    ccols = [col("id", "ID", "", "code", width=10), col("fl", "FLOOR", "", "text", width=6), col("host", "HOST ROOM", "", "text", width=26),
             col("min", "MIN_RADIUS_ARC", "", "qty", "m", 12), col("mid", "MID_BAND_ARC (alt.)", "", "qty", "m", 12),
             col("max", "MAX_RADIUS_ARC (alt.)", "", "qty", "m", 12), col("ch", "CHORD (alt.)", "", "qty", "m", 11),
             col("side", "ROOM SIDE", "", "text", width=12), col("sel", "SELECTED COMMERCIAL BASIS", "", "text", width=20),
             col("com", "COMMERCIAL LENGTH", "الطول التجاري", "qty", "m", 12), col("st", "STATUS", "", "status", width=11)]
    crows = []
    for k, r in enumerate(a.cu["rows"]):
        b = f"B2A1.CURVED_OPENING_REGISTER:/rows/{k}"
        crows.append(row([r["id"], r["floor"], " / ".join(r["host_labels"]), a.R.q(f"{b}/bases_m/MIN_RADIUS_ARC"),
                          a.R.q(f"{b}/bases_m/MID_BAND_ARC"), a.R.q(f"{b}/bases_m/MAX_RADIUS_ARC"), a.R.q(f"{b}/bases_m/CHORD"),
                          f"{r['orientation'].get('room_side') or '—'} ({r['orientation']['state'].lower()})", r["commercial_basis"],
                          a.R.q(f"{b}/commercial_m"), "COMPUTED"],
                         cls="BREAKDOWN_ONLY", status="COMPUTED", tech="COMPUTED", explains=f"ALU-CURVED@{r['floor']}"))
    s2 = section("CURVED", T.section("CURVED"), ccols, crows,
                 note="MID_BAND / MAX_RADIUS / CHORD are alternative bases of the same glazing (not additive). On both curves the "
                      "probe places the room beyond the largest radius, so MIN_RADIUS_ARC (the method default) is the exterior-side face.")
    return sheet("05_OPENINGS_ALUMINIUM", T.section("OPENINGS"), "SCHEDULE", [s1, s2])


def blockers_sheet(a: A):
    oq = a.R.data["A3.OWNER_QUESTION_REGISTER"]["questions"]
    answered = {"OQ3-A2": "ANSWERED by OF-B2A-C (wardrobe; master bedroom certified)"}
    qcols = [col("n", "#", "", "code", width=8), col("fl", "FLOOR", "", "text", width=8), col("q", "QUESTION", "السؤال", "text", width=70),
             col("unb", "UNBLOCKS", "يفك", "text", width=36), col("st", "STATUS", "الحالة", "status", width=11),
             col("ans", "CURRENT STATE", "", "text", width=30)]
    qrows = []
    for q in oq:
        ok = q["id"] in answered
        qrows.append(row([q["id"], "GF" if q["group"] == "ARCHITECTURAL" else "FOUNDATION", q["question"], "; ".join(q["unblocks"]),
                          "COMPUTED" if ok else "BLOCKED", answered.get(q["id"], "OPEN")], role="NOTE",
                         status="COMPUTED" if ok else "BLOCKED", tech="INFO"))
    for i, (item, need) in enumerate((("floor build-up above each storey", "Provide the floor build-up (screed + tile) per storey."),
                                      ("opening heights", "Provide window / door schedule or head and sill levels."))):
        r = a.rb["rows"][_i(a.rb["rows"], lambda x: x["item"] == item)]
        qrows.append(row([f"Q-{i + 1}", "ALL", need, r["why"], "BLOCKED", "OPEN"], role="NOTE", status="BLOCKED", tech="INFO"))
    sec_q = section("OWNER_QUESTIONS", T.section("OWNER_QUESTIONS"), qcols, qrows,
                    note="Questions come from the frozen registers (A3 owner questions + B2A remaining blockers); an answer becomes an "
                         "owner fact in the next engine round - this report never applies one.")
    bcols = [col("n", "#", "", "count", width=5), col("fl", "FLOOR", "", "text", width=10), col("item", "ITEM", "البند", "text", width=26),
             col("st", "CURRENT STATUS", "الحالة", "status", width=11), col("what", "WHAT IS BLOCKED", "", "text", width=24),
             col("why", "WHY", "السبب", "text", width=40), col("eff", "EFFECT ON QUANTITY", "الأثر", "text", width=30),
             col("need", "WHAT IS NEEDED", "المطلوب", "text", width=32), col("pri", "PRIORITY", "الأولوية", "text", width=9),
             col("tech", "TECHNICAL STATUS CODE", "", "code", width=30)]
    brows = []
    for r in a.rb["rows"]:
        e = T.explain(r["state"])
        fl = next((f for f in FLOORS if r["item"].endswith(" " + f)), "ALL")
        what = r["item"] + (f" (x{r['count']})" if r.get("count") else "")
        why = e["why"] + (f" Register: {r['why']}" if r.get("why") else "")
        brows.append(row([len(brows) + 1, fl, r["item"], _stc(r["state"]), what, why, e["effect"], e["needed"], e["priority"], r["state"]],
                         role="NOTE", status=_stc(r["state"]), tech=r["state"]))
    fam = OrderedDict()
    for r in a.ab:
        if r["status"] == "BLOCKED" and r["item"] not in SUPERSEDED and r["class"].startswith("BLOCKED"):
            fam.setdefault((r["trade"], r["class"]), []).append(r)
    for (tr, cls), rs in fam.items():
        e = T.explain(cls)
        brows.append(row([len(brows) + 1, ", ".join(x["floor"] for x in rs), rs[0]["en"], "BLOCKED", tr.replace("_", " ").lower(),
                          e["why"] + " " + "; ".join(rs[0]["blockers"])[:160], e["effect"], e["needed"], e["priority"], cls],
                         role="NOTE", status="BLOCKED", tech=cls))
    sec_b = section("BLOCKERS", T.section("BLOCKERS"), bcols, brows,
                    note="User-facing reason / effect / need are generic explanations of the technical code (terms.py); the technical "
                         "code is the register's own.")
    return sheet("06_BLOCKERS_OWNER_QUESTIONS", ("BLOCKERS / OWNER QUESTIONS", "المعوقات وأسئلة المالك"), "INFO", [sec_q, sec_b])


def methods_sheet(a: A, model_lines, run):
    R = a.R
    m = R.data["B2A1.URBAN_METHOD_REGISTER"]["methods"]
    mcols = [col("id", "URBAN METHOD", "", "code", width=40), col("v", "VERSION", "", "text", width=8),
             col("s", "DESCRIPTION", "الوصف", "text", width=60), col("sc", "SCOPE", "", "text", width=34)]
    mrows = [row([x["id"].split("@")[0], x["id"].split("@")[1] if "@" in x["id"] else "", x["statement"], ", ".join(x["applies_to"])],
                 role="NOTE") for x in m]
    of = R.data["B2A1.OWNER_FACT_REGISTER"]["facts"]
    fcols = [col("id", "OWNER FACT", "", "code", width=14), col("c", "CLASS", "", "text", width=30),
             col("s", "STATEMENT", "", "text", width=70), col("u", "USE", "", "text", width=40)]
    frows = [row([f["id"], f["class"], f["statement"], f.get("use", "")], role="NOTE") for f in of]
    sm = R.data["A3.SOURCE_MANIFEST"]["files"]
    scols = [col("f", "SOURCE FILE", "", "text", width=34), col("d", "DISCIPLINE", "", "text", width=14),
             col("r", "ROLE", "", "text", width=26), col("sha", "SHA256 (short)", "", "code", width=18), col("t", "TYPE", "", "text", width=10)]
    srows = [row([f["file"], f["discipline"], f.get("declared_role") or "", f["sha256"][:16], f["type"]], role="NOTE") for f in sm]
    rcols = [col("k", "ITEM", "", "text", width=34), col("v", "VALUE", "", "text", width=90)]
    rrows = [row([k, v], role="NOTE") for k, v in run]
    codes = sorted({p["tech"] for ln in model_lines for p in ln["parts"]})
    acols = [col("code", "TECHNICAL CODE", "", "code", width=50), col("d", "DISPLAY STATUS", "", "status", width=12),
             col("how", "ALIAS RULE", "", "text", width=10)]
    from engine.reporting_v2.model import alias_table
    arows = [row([c, d, h], role="NOTE", status=d) for c, d, h in alias_table(codes)]
    ccols = [col("c", "CLASS", "", "code", width=22), col("m", "MEANING", "", "text", width=90)]
    crows = [row(["ADDITIVE", "may be included in the project / trade total (00_TOTAL_SUMMARY only)"], role="NOTE"),
             row(["BREAKDOWN_ONLY", "explains an additive line by floor / room / element - never added again"], role="NOTE"),
             row(["ALTERNATIVE_MEASURE", "the same physical item in another unit / basis - price one basis only"], role="NOTE"),
             row(["TRACE_ONLY", "evidence / QA / counts - no quantity to add"], role="NOTE"),
             row(["SUBTOTAL / TOTAL", "declared sum of ADDITIVE register values of one unit; addends recorded in REPORTING_MODEL_V2.json"], role="NOTE")]
    return sheet("07_METHODS_TRACEABILITY", ("METHODS / TRACEABILITY", "المنهجية والتتبع"), "INFO", [
        section("METHODS", T.section("METHODS"), mcols, mrows),
        section("OWNER_FACTS", T.section("OWNER_FACTS"), fcols, frows),
        section("SOURCES", T.section("SOURCES"), scols, srows),
        section("RUN", T.section("RUN"), rcols, rrows),
        section("STATUS_ALIAS", T.section("STATUS_ALIAS"), acols, arows,
                note="Presentation alias only: every row keeps its technical code; unknown codes fail the build."),
        section("CLASSES", T.section("CLASSES"), ccols, crows)])


# ------------------------------------------------------------------ technical appendix
def tech_sheets(a: A, lines):
    R = a.R
    out = []
    cols = [col("fl", "FLOOR", "", "text", width=6), col("t", "TYPE", "", "text", width=7), col("tag", "TAG (source handle)", "", "code", width=34),
            col("bd", "B x D (cm)", "", "text", width=10), col("st", "STATE", "", "code", width=36), col("m", "CONTROLLING MEMBER", "", "text", width=12),
            col("dc", "D_CTRL (m)", "", "dim", width=9), col("iv", "INTERVAL (m)", "", "dim", width=9), col("h", "HEIGHT (m)", "", "dim", width=9),
            col("v", "VOLUME", "", "qty", "m3", 10), col("j", "JOINT", "", "qty", "m3", 10), col("d", "STATUS", "", "status", width=11)]
    rows = []
    for k, r in enumerate(a.sv["rows"]):
        b = f"B2A1.STRUCTURAL_VERTICAL_INTERVAL_REGISTER:/rows/{k}"
        d = display_status(r["state"])
        rows.append(row([r["floor"], r["type"], r["tag_key"], f"{r['B_cm']:g} x {r['D_cm']:g}" if r.get("B_cm") else "", r["state"],
                         r.get("controlling_member") or "", r.get("controlling_depth_m"), r.get("interval_m"), r.get("height_m"),
                         R.q(f"{b}/volume_m3") if r.get("volume_m3") is not None else na("—"),
                         R.q(f"{b}/joint_m3") if r.get("joint_m3") is not None else na("—"), d],
                        cls="TRACE_ONLY", status=d, tech=r["state"]))
    out.append(sheet("TECH_COLUMN_OCCURRENCES", ("COLUMN OCCURRENCES", "الأعمدة - تفصيلي"), "TECH",
                     [section("TECH", ("STRUCTURAL VERTICAL INTERVAL REGISTER (B2A.1)", ""), cols, rows)]))
    cols = [col("fl", "FLOOR", "", "text", width=6), col("t", "TYPE", "", "text", width=7), col("ns", "NAMESPACE", "", "text", width=11),
            col("bd", "B x D (cm)", "", "text", width=10), col("st", "STATE", "", "code", width=22), col("tags", "TAGS", "", "count", width=6),
            col("dr", "DRAWN", "", "qty", "m", 10), col("cl", "CLEAR (face to face)", "", "qty", "m", 11),
            col("cc", "SUPPORT C/L", "", "qty", "m", 11), col("ss", "SCHEDULE SPANS", "", "qty", "m", 11), col("d", "STATUS", "", "status", width=11)]
    rows = []
    for fl in FLOORS:
        for k, o in enumerate(a.bb["sheets"][fl]["occurrences"]):
            b = f"B2A1.BEAM_BINDING_REGISTER:/sheets/{fl}/occurrences/{k}/lengths"
            Lq = lambda key: R.q(f"{b}/{key}") if (o["lengths"] or {}).get(key) is not None else na("—")
            d = display_status(o["state"])
            rows.append(row([fl, o["type"], o["namespace"], f"{o['B_cm']:g} x {o['D_cm']:g}", o["state"], len(o["tags"]),
                             Lq("PLAN_DRAWN_EXTENT"), Lq("CLEAR_FACE_TO_FACE_LENGTH"), Lq("SUPPORT_CENTRELINE_LENGTH"),
                             Lq("SCHEDULE_SPAN_LENGTH"), d], cls="TRACE_ONLY", status=d, tech=o["state"]))
    out.append(sheet("TECH_BEAM_OCCURRENCES", ("BEAM OCCURRENCES", "الجسور - تفصيلي"), "TECH",
                     [section("TECH", ("BEAM BINDING REGISTER (B2A.1) - four length bases", ""), cols, rows)]))
    cols = [col("fl", "SHEET", "", "text", width=8), col("cl", "CLOSURE", "", "code", width=16), col("g", "GROSS OUTLINE", "", "qty", "m2", 12),
            col("o", "OPENINGS", "", "qty", "m2", 11), col("n", "NET PLATE", "", "qty", "m2", 12), col("t", "THICKNESS TAGS (cm)", "", "text", width=12),
            col("v", "VOLUME", "", "qty", "m3", 11), col("d", "STATUS", "", "status", width=11)]
    rows = []
    for fl in FLOORS:
        s = R.data["B2A1.SLAB_REGION_REGISTER"]["sheets"][fl]
        b = f"B2A1.SLAB_REGION_REGISTER:/sheets/{fl}"
        rows.append(row([fl, s["closure"], R.q(f"{b}/gross_outline_area_m2"), R.q(f"{b}/openings_area_m2"), R.q(f"{b}/net_plate_area_m2"),
                         ", ".join(str(x) for x in s["sheet_thickness_tags_cm"]), R.q(f"{b}/volume_m3"), "COMPUTED"],
                        cls="TRACE_ONLY", status="COMPUTED", tech="COMPUTED"))
    out.append(sheet("TECH_SLAB_REGIONS", ("SLAB REGIONS", "البلاطات - تفصيلي"), "TECH",
                     [section("TECH", ("SLAB REGION REGISTER (B2A.1)", ""), cols, rows)]))
    cols = [col("id", "OPENING", "", "code", width=10), col("fn", "FUNCTION", "", "code", width=30), col("prev", "PREVIOUS (A3)", "", "code", width=12),
            col("ch", "CHANGE", "", "text", width=24), col("ex", "EXISTENCE", "", "text", width=34), col("b", "FUNCTION BASIS", "", "text", width=70)]
    rows = [row([r["id"], r["function"], r.get("previous_function") or "", r.get("function_change") or "", r["existence"], r["function_basis"][:300]],
                role="NOTE", tech=r["function"]) for r in a.op["rows"]]
    out.append(sheet("TECH_OPENING_EVIDENCE", ("OPENING EVIDENCE", "أدلة الفتحات"), "TECH",
                     [section("TECH", ("OPENING AUTHORITY REGISTER (B2A.1)", ""), cols, rows)]))
    cols = [col("line", "LINE / LEVEL", "", "code", width=22), col("ref", "REGISTER VALUE (file:/json pointer)", "", "code", width=90),
            col("st", "TECH STATUS", "", "code", width=34)]
    rows = []
    for ln in lines:
        for p in ln["parts"]:
            refs = p["cell"].get("sum") or [p["cell"].get("src") or "(blocked - no value)"]
            for pointer in refs:
                rows.append(row([f"{ln['id']}@{p['level']}", pointer, p["tech"]], role="NOTE", tech=p["tech"]))
    for item, why in SUPERSEDED.items():
        rows.append(row([f"SUPERSEDED {item}", f"A3.ARCH_BOQ:/rows/{a.abi[item]} -> {why}", "INFO"], role="NOTE", tech="INFO"))
    out.append(sheet("TECH_SOURCE_HANDLES", ("SOURCE HANDLES / VALUE POINTERS", "مصادر القيم"), "TECH",
                     [section("TECH", ("EVERY LINE PART -> REGISTER VALUE", ""), cols, rows,
                              note="Superseded A3 rows are listed and never shown as quantities.")]))
    qa = R.data["B2A1.QA_GATES"]
    cols = [col("g", "GATE", "", "code", width=40), col("v", "VALUE", "", "count", width=10), col("d", "STATUS", "", "status", width=11)]
    rows = [row([g, v, "COMPUTED" if v == 0 else "BLOCKED"], role="NOTE", status="COMPUTED" if v == 0 else "BLOCKED", tech="PASS" if v == 0 else "FAIL")
            for g, v in qa["gates"].items()]
    rows.append(row(["ALSENAN_REGRESSION (B2A.1 vs B2A)", None, display_status("PASS" if R.data["B2A1.ALSENAN_REGRESSION"]["state"] == "PASS" else "FAIL")], role="NOTE",
                    status="COMPUTED", tech="PASS"))
    out.append(sheet("TECH_QA", ("QA", "ضبط الجودة"), "TECH", [section("TECH", ("QA GATES (B2A.1)", ""), cols, rows)]))
    cols = [col("n", "REGISTER", "", "code", width=50), col("f", "FILE", "", "text", width=60), col("s", "SHA256", "", "code", width=66)]
    rows = [row([n, v["file"], v["sha256"]], role="NOTE") for n, v in R.inputs().items()]
    out.append(sheet("TECH_RUN_INFO", ("RUN INFO - REPORT INPUT DIGESTS", "معلومات التشغيل"), "TECH", [section("TECH", ("INPUT REGISTERS", ""), cols, rows)]))
    return out


# ------------------------------------------------------------------ QS reconciliation: structural manual-check blocks
PREFILL = "pre-filled from the source schedule / plan tags - overwrite with your own check"


def _check_rows(sec, rows, unit, keys_by_floor):
    """Close each floor run of ITEM rows with a SUBTOTAL (SUM over the run) and add a TOTAL over the floors."""
    out, subs = [], []
    width = len(rows[0][1]["cells"]) if rows else 0
    for fl, ks in keys_by_floor.items():
        run = [r for k, r in rows if k in ks]
        out += run
        nums = [c["q"] for r in run for c in r["cells"][-8:-7] if c.get("q") is not None]
        if len(keys_by_floor) == 1 and nums:                              # one run: the TOTAL is the SUM over it
            subs.append(((rng(sec, ks[0], ks[-1], "urban"), rng(sec, ks[0], ks[-1], "manual")), dsum(nums)))
        elif len(run) >= 2 and nums:
            k = f"S:{fl}"
            lead = [f"{T.level(fl)[0]} - subtotal"] + [None] * (width - 9)
            out.append(row(lead + L.total_tail(sec, k, unit, [rng(sec, ks[0], ks[-1], "urban")], [rng(sec, ks[0], ks[-1], "manual")],
                                               dsum(nums)) + [""], role="SUBTOTAL", key=k))
            subs.append((k, dsum(nums)))
        elif nums:
            subs.append((ks[0] if len(run) == 1 else None, dsum(nums)))
    if subs:
        lead = ["TOTAL"] + [None] * (width - 9)
        uref = lambda k, c: k[0 if c == "urban" else 1] if isinstance(k, tuple) else ref(sec, k, c)
        out.append(row(lead + L.total_tail(sec, "TOTAL", unit, [uref(k, "urban") for k, _ in subs if k],
                                           [uref(k, "manual") for k, _ in subs if k], dsum(q for _, q in subs)) + [""],
                       role="TOTAL", key="TOTAL"))
    return out


def qs_structural_sections(a: A):
    """Footings / beams / columns / slabs: the Urban m3 (locked register values) beside a manual-check m3 that Excel
    computes from the QS's own count and dimensions (yellow inputs). The check never feeds back into Urban."""
    R = a.R
    notes = col("notes", "CHECK NOTES", "ملاحظات التدقيق", "text", width=22)
    man = ("MANUAL CHECK M3 (formula)", "حجم التدقيق")
    # footings
    sec = "FOOT_CHECK"
    cols = L.recon_cols([col("type", "TYPE", "النوع", "text", width=10), col("n", "COUNT (plan tags)", "العدد", "count", width=9),
                         col("l", "L (m)", "", "dim", width=8), col("w", "W (m)", "", "dim", width=8), col("h", "H (m)", "", "dim", width=8)],
                        man) + [notes]
    rows = []
    for k, t in enumerate(a.ft["type_summary"]):
        b = f"A3.FOOTING_REGISTER:/type_summary/{k}"
        tech = t["status"]
        urban = R.q(f"{b}/m3_total_computed") if t["count_computed"] else (blocked(tech) if t["count_tagged"] else na("NOT ON PLAN"))
        key = f"F:{t['type']}"
        man_f = fcell("PROD", *[ref(sec, key, c) for c in ("n", "l", "w", "h")], 1, fmt="m3")
        rows.append((key, row([t["type"], inp(t["count_tagged"], "num"), inp(t["L_m"], "num"), inp(t["W_m"], "num"), inp(t["H_m"], "num")] +
                              L.recon_tail(sec, key, urban | ({"unit": "m3"} if urban.get("q") is not None else {}), "m3",
                                           display_status(tech), manual=man_f) + [inp(None, "text")],
                              cls="BREAKDOWN_ONLY", status=display_status(tech), tech=tech, explains="CON-FOOT@FOUNDATION", key=key)))
    foot = section(sec, ("FOOTINGS - MANUAL CHECK", "القواعد - التدقيق اليدوي"), cols,
                   _check_rows(sec, rows, "m3", {"FOUNDATION": [k for k, _ in rows]}),
                   note=f"MANUAL CHECK M3 = COUNT x L x W x H (a check view only). COUNT, L, W, H are {PREFILL}. COUNT is the number "
                        "of tags on the plan: Urban computes only geometry-confirmed outlines (F / F10 SOURCE_CONFLICT excluded), so a "
                        "difference there is expected and is the owner question on 06.")
    # beams (downstand below the slab)
    sec = "BEAM_CHECK"
    cols = L.recon_cols([col("type", "FLOOR · TYPE", "النوع", "text", width=12), col("n", "OCCURRENCES (measured / found)", "العدد", "text", width=11),
                         col("b", "B (cm)", "", "num", width=7), col("d", "D (cm)", "", "num", width=7),
                         col("t", "SLAB t (cm)", "", "num", width=7), col("basis", "LENGTH BASIS", "أساس الطول", "text", width=16),
                         col("ulen", "URBAN LENGTH (m)", "طول أوربن", "qty", "m", width=10),
                         col("clen", "CHECK LENGTH (m)", "طول التدقيق", "qty", "m", width=10)], man) + [notes]
    rows, by_fl = [], OrderedDict()
    for fl in FLOORS:
        m = a.pc["storeys"][fl]["model"]
        tcm = a.pc["storeys"][fl]["slab_thickness_cm"]
        occ = a.bb["sheets"][fl]["occurrences"]
        types = OrderedDict()
        for k, o in enumerate(occ):
            types.setdefault(o["type"], []).append(k)
        for t, ks in types.items():
            meas = [k for k in ks if occ[k]["state"] == "MEASURED" and (occ[k]["lengths"] or {}).get("CLEAR_FACE_TO_FACE_LENGTH") is not None]
            lens = [R.q(f"B2A1.BEAM_BINDING_REGISTER:/sheets/{fl}/occurrences/{k}/lengths/CLEAR_FACE_TO_FACE_LENGTH") for k in meas]
            vols = [R.q(f"B2A1.PHYSICAL_CONCRETE_REGISTER:/storeys/{fl}/model/components/{j}/volume_m3")
                    for j, c in enumerate(m["components"]) if c["component"] == "DOWNSTAND_BEAM" and c["id"].split(":")[0] == t]
            o0 = occ[ks[0]]
            st_ = "COMPUTED" if len(meas) == len(ks) else ("PARTIAL" if meas else "BLOCKED")
            tech = {"COMPUTED": "COMPUTED", "PARTIAL": "COMPUTED_PARTIAL"}.get(st_, "BLOCKED")
            key = f"B:{fl}:{t}"
            urban = ((qsum(vols) if len(vols) > 1 else dict(vols[0])) | {"unit": "m3"}) if vols else blocked("NOT_MEASURED")
            ulen = ((qsum(lens) if len(lens) > 1 else dict(lens[0])) | {"unit": "m"}) if lens else blocked("NOT_MEASURED")
            man_b = fcell("PROD", ref(sec, key, "clen"), ref(sec, key, "b"), sub(ref(sec, key, "d"), ref(sec, key, "t")), 10000, fmt="m3")
            rows.append((key, row([f"{fl} · {t}", f"{len(meas)} / {len(ks)}", inp(o0["B_cm"]), inp(o0["D_cm"]), inp(tcm),
                                   "clear face-to-face", ulen, inp(None)] +
                                  L.recon_tail(sec, key, urban, "m3", st_, manual=man_b) + [inp(None, "text")],
                                  cls="BREAKDOWN_ONLY", status=st_, tech=tech, explains=f"CON-SUPER@{fl}", key=key)))
            by_fl.setdefault(fl, []).append(key)
    beams = section(sec, ("BEAMS - MANUAL CHECK (DOWNSTAND)", "الجسور - التدقيق اليدوي"), cols, _check_rows(sec, rows, "m3", by_fl),
                    note="MANUAL CHECK M3 = CHECK LENGTH x B x (D - t) / 10000: the beam below the slab, the Urban basis (the slab "
                         f"depth is in the slab check). B, D and slab t are {PREFILL}; type your own measured clear length per type.")
    # columns (clear height below the controlling member; joints are separate on the floor sheets)
    sec = "COL_CHECK"
    cols = L.recon_cols([col("type", "FLOOR · TYPE", "النوع", "text", width=12), col("n", "COUNT", "العدد", "count", width=8),
                         col("b", "B (cm)", "", "num", width=7), col("d", "D (cm)", "", "num", width=7),
                         col("uh", "URBAN HEIGHT (m)", "ارتفاع أوربن", "qty", "m", width=10),
                         col("ch", "CHECK HEIGHT (m)", "ارتفاع التدقيق", "qty", "m", width=10)], man) + [notes]
    rows, by_fl = [], OrderedDict()
    for fl in FLOORS:
        grp = OrderedDict()
        for k, r in enumerate(a.sv["rows"]):
            if r["floor"] != fl or r["state"] in ("NOT_IN_STOREY", "NOT_DRAWN_ON_STOREY_SHEET"):
                continue
            g = (r["type"], r.get("B_cm"), r.get("D_cm"), r.get("height_m") if r.get("volume_m3") is not None else r["state"])
            grp.setdefault(g, []).append(k)
        for gi, ((t, bcm, dcm, h), ks) in enumerate(grp.items()):
            key = f"C:{fl}:{gi}"
            done = [k for k in ks if a.sv["rows"][k].get("volume_m3") is not None]
            if done:
                vols = [R.q(f"B2A1.STRUCTURAL_VERTICAL_INTERVAL_REGISTER:/rows/{k}/volume_m3") for k in done]
                urban = (qsum(vols) if len(vols) > 1 else dict(vols[0])) | {"unit": "m3"}
                uh = R.q(f"B2A1.STRUCTURAL_VERTICAL_INTERVAL_REGISTER:/rows/{done[0]}/height_m") | {"unit": "m"}
                tech = "COMPUTED"
            else:
                urban, uh, tech = blocked(h), blocked(h), h
            st_ = display_status(tech)
            man_c = fcell("PROD", *[ref(sec, key, c) for c in ("n", "b", "d", "ch")], 10000, fmt="m3")
            rows.append((key, row([f"{fl} · {t}", inp(len(ks)), inp(bcm), inp(dcm), uh, inp(None)] +
                                  L.recon_tail(sec, key, urban, "m3", st_, manual=man_c) + [inp(None, "text")],
                                  cls="BREAKDOWN_ONLY", status=st_, tech=tech, explains=f"CON-SUPER@{fl}", key=key)))
            by_fl.setdefault(fl, []).append(key)
    columns = section(sec, ("COLUMNS - MANUAL CHECK", "الأعمدة - التدقيق اليدوي"), cols, _check_rows(sec, rows, "m3", by_fl),
                      note="One row per floor, type, size and Urban clear height. MANUAL CHECK M3 = COUNT x B x D x CHECK HEIGHT / "
                           f"10000. COUNT, B and D are {PREFILL}; type your own clear height (storey interval minus the depth of "
                           "the member framing in). Beam-column joints are a separate Urban component (floor sheets).")
    # slabs
    sec = "SLAB_CHECK"
    cols = L.recon_cols([col("fl", "FLOOR / SLAB", "الدور", "text", width=16),
                         col("ua", "URBAN NET AREA (m2)", "مساحة أوربن", "qty", "m2", width=11),
                         col("ca", "CHECK AREA (m2)", "مساحة التدقيق", "qty", "m2", width=11),
                         col("t", "THICKNESS (cm)", "السماكة", "num", width=9)], man) + [notes]
    rows = []
    for fl in FLOORS:
        st = a.pc["storeys"][fl]
        key = f"SL:{fl}"
        urban = R.q(f"B2A1.PHYSICAL_CONCRETE_REGISTER:/storeys/{fl}/model/by_component_m3/SLAB") | {"unit": "m3"}
        ua = R.q(f"B2A1.SLAB_REGION_REGISTER:/sheets/{fl}/net_plate_area_m2") | {"unit": "m2"}
        man_s = fcell("PROD", ref(sec, key, "ca"), ref(sec, key, "t"), 100, fmt="m3")
        rows.append((key, row([f"{T.level(fl)[0]} - {st['sheet']}", ua, inp(None), inp(st["slab_thickness_cm"])] +
                              L.recon_tail(sec, key, urban, "m3", "COMPUTED", manual=man_s) + [inp(None, "text")],
                              cls="BREAKDOWN_ONLY", status="COMPUTED", tech="COMPUTED", explains=f"CON-SUPER@{fl}", key=key)))
    slabs = section(sec, ("SLABS - MANUAL CHECK", "البلاطات - التدقيق اليدوي"), cols, _check_rows(sec, rows, "m3", {k: [k] for k, _ in rows}),
                    note=f"MANUAL CHECK M3 = CHECK AREA x THICKNESS / 100 (net plate area: gross outline minus openings). Thickness is "
                         f"{PREFILL}; type your own net slab area.")
    return [foot, beams, columns, slabs]


QS_BLOCKS = [("FOUNDATION", ["FOUNDATION"]), ("GF", ["GF"]), ("1F", ["1F"]), ("2F_ROOF", ["2F", "ROOF"]),
             ("EXT_OTHER", ["EXTERNAL", "UNASSIGNED"])]


# ------------------------------------------------------------------ assemble
def build(run_date: str, registers_commit: str) -> tuple:
    R = registers()
    a = A(R)
    lines = build_lines(a)
    set_groups(lines)
    a.lines = lines
    fz = R.data["B2A1.ALSENAN_PHASE_B2A1_REGISTER_FREEZE"]
    qa = R.data["B2A1.QA_GATES"]["state"]
    proj = {"name_en": "ALSENAN VILLA", "name_ar": "", "phase": "PHASE B2A.1", "release_state": "SHADOW - NOT APPROVED",
            "subtitle": f"Source P7757 (architectural) + ST7757 (structural)  ·  run {run_date}  ·  engine {fz['code_commit']}  ·  "
                        f"registers {registers_commit}  ·  QA {qa}",
            "header": [("Project", "Alsenan villa (P7757 architectural + ST7757 structural)"),
                       ("Source revision", "P7757.dxf / ST7757.dxf / ST7757.pdf - see 07_METHODS_TRACEABILITY (sha256)"),
                       ("Phase", "B2A.1 (generic QA patch on B2A) - SHADOW"),
                       ("Run date", run_date), ("Engine version", f"code {fz['code_commit']} · registers {registers_commit}"),
                       ("QA status", f"QA gates {qa} · Alsenan regression {R.data['B2A1.ALSENAN_REGRESSION']['state']} · "
                                     f"Qortuba {R.data['B2A1.QORTUBA_REGRESSION']['state']}"),
                       ("Status", "SHADOW - NOT APPROVED for tender or contract · no pricing · no benchmark value used")]}
    run = [("Engine code commit", fz["code_commit"]), ("Registers commit", registers_commit),
           ("B2A.1 register freeze", "tests/alsenan/registers_b2a1/ALSENAN_PHASE_B2A1_REGISTER_FREEZE.json"),
           ("Parent B2A freeze sha256", fz["parent_b2a_freeze"]["sha256"]), ("QA gates", qa),
           ("Alsenan regression", R.data["B2A1.ALSENAN_REGRESSION"]["state"]), ("Qortuba regression", R.data["B2A1.QORTUBA_REGRESSION"]["state"]),
           ("Report inputs", f"{len(R.files)} frozen register files (TECH_RUN_INFO)"),
           ("Authority", "B2A.1 supersedes A3 where ALSENAN_B2A_DELTA lists a change; otherwise A3 (preserved)")]
    sheets = [floor_sheet(a, "01_GROUND_FLOOR", "GF", lines), floor_sheet(a, "02_FIRST_FLOOR", "1F", lines),
              floor_sheet(a, "03_ROOF_SECOND_FLOOR", "2F", lines, roof=True), foundation_sheet(a), openings_sheet(a),
              blockers_sheet(a), methods_sheet(a, lines, run),
              L.reconciliation_sheet(lines, LEVELS, qs_structural_sections(a), blocks=QS_BLOCKS)] + tech_sheets(a, lines)
    notes = ["Not measured in this run (no register): marble, railings, hidden profile, external works.",
             "Structural storey = the columns of that storey + the slab over it (register definition).",
             "Curved glazing is measured on MIN_RADIUS_ARC (method default); on Alsenan that face is the exterior side."]
    model = L.assemble(proj, lines, sheets, R, levels=LEVELS,
                       key_notes=notes)
    return model, R
