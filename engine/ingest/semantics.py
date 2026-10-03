"""Semantic identity ontology, Arabic and English (PA06 WS7).

Text never creates geometry.  A label becomes an anchor attached to an
existing cell; its canonical class comes from a bilingual dictionary that
keeps the raw label; garbled (SHX) text is LANGUAGE = UNDECODABLE and
stays UNRESOLVED.  A physical region may hold several functional zones.
"""

from __future__ import annotations

import math
import re
import unicodedata

from engine.ingest import ids
from engine.ingest.spaces_v2 import _label_at

CLASSES = ("BEDROOM", "MASTER_BEDROOM", "BATHROOM", "WC", "KITCHEN", "PANTRY", "LAUNDRY", "IRON_ROOM", "WASHROOM", "LIVING", "DINING", "RECEPTION", "SALOON", "DEWANEYA",
           "MAID_ROOM", "DRIVER_ROOM", "STAIR", "CORRIDOR", "VOID", "ROOF", "COURT", "GARDEN", "POOL", "ELEVATOR", "STORE", "OFFICE", "ENTRANCE", "BALCONY", "TERRACE", "UNKNOWN")
WET = ("BATHROOM", "WC", "KITCHEN", "LAUNDRY", "WASHROOM", "POOL")
# classes that are interior rooms whose floor / ceiling area is a take-off item (exterior, circulation shafts and unknown are not)
INTERIOR_ROOM_CLASSES = ("BEDROOM", "MASTER_BEDROOM", "BATHROOM", "WC", "KITCHEN", "PANTRY", "LAUNDRY", "IRON_ROOM", "WASHROOM", "LIVING", "DINING", "RECEPTION", "SALOON", "DEWANEYA",
                         "MAID_ROOM", "DRIVER_ROOM", "CORRIDOR", "STORE", "OFFICE", "ENTRANCE")
# classes whose ceiling height is not the normal storey height without a section or an owner scope (double height, wells, shafts, exterior)
HEIGHT_NOT_NORMAL = ("STAIR", "VOID", "ELEVATOR", "RECEPTION", "SALOON", "ROOF", "COURT", "GARDEN", "POOL", "BALCONY", "TERRACE", "UNKNOWN")
EN = {
    "MASTER BED": "MASTER_BEDROOM", "M.BED": "MASTER_BEDROOM", "MASTER": "MASTER_BEDROOM", "BED ROOM": "BEDROOM", "BEDROOM": "BEDROOM", "BED": "BEDROOM",
    "BATH ROOM": "BATHROOM", "BATHROOM": "BATHROOM", "BATH": "BATHROOM", "TOILET": "WC", "W.C": "WC", "WC": "WC", "KITCHEN": "KITCHEN", "PANTRY": "PANTRY", "LAUNDRY": "LAUNDRY",
    "IRON": "IRON_ROOM", "WASH": "WASHROOM", "LIVING": "LIVING", "FAMILY": "LIVING", "DINING": "DINING", "RECEPTION": "RECEPTION", "SALOON": "SALOON", "SALON": "SALOON",
    "DEWANEYA": "DEWANEYA", "DIWANIYA": "DEWANEYA", "DIWANIA": "DEWANEYA", "MAJLIS": "DEWANEYA", "MAID": "MAID_ROOM", "SERVANT": "MAID_ROOM", "DRIVER": "DRIVER_ROOM",
    "STAIR": "STAIR", "CORRIDOR": "CORRIDOR", "LOBBY": "CORRIDOR", "HALL": "CORRIDOR", "PASSAGE": "CORRIDOR", "VOID": "VOID", "ROOF": "ROOF", "COURT": "COURT",
    "GARDEN": "GARDEN", "POOL": "POOL", "LIFT": "ELEVATOR", "ELEVATOR": "ELEVATOR", "STORE": "STORE", "OFFICE": "OFFICE", "ENTRANCE": "ENTRANCE", "ENTRY": "ENTRANCE",
    "BALCONY": "BALCONY", "TERRACE": "TERRACE",
}
AR = {
    "غرفة نوم رئيسية": "MASTER_BEDROOM", "نوم رئيسية": "MASTER_BEDROOM", "غرفة نوم": "BEDROOM", "نوم": "BEDROOM", "حمام": "BATHROOM", "دورة مياه": "WC", "مرحاض": "WC",
    "مطبخ": "KITCHEN", "مخزن مطبخ": "PANTRY", "مؤن": "PANTRY", "غسيل": "LAUNDRY", "مغسلة": "LAUNDRY", "كوي": "IRON_ROOM", "معيشة": "LIVING", "صالة": "LIVING", "طعام": "DINING",
    "سفرة": "DINING", "استقبال": "RECEPTION", "صالون": "SALOON", "ديوانية": "DEWANEYA", "مجلس": "DEWANEYA", "خادمة": "MAID_ROOM", "سائق": "DRIVER_ROOM", "درج": "STAIR",
    "سلم": "STAIR", "ممر": "CORRIDOR", "فراغ": "VOID", "سطح": "ROOF", "حوش": "COURT", "فناء": "COURT", "حديقة": "GARDEN", "مسبح": "POOL", "مصعد": "ELEVATOR",
    "مخزن": "STORE", "مكتب": "OFFICE", "مدخل": "ENTRANCE", "بلكونة": "BALCONY", "شرفة": "BALCONY", "تراس": "TERRACE",
}
LEVEL_RE = re.compile(r"^(?:%%p|±|\+|-)\s*\d{1,2}[.,]\d{2}\s*$")
NUMBER_RE = re.compile(r"^[\d.,\s%x×X-]+$")
SITE_WORDS = ("NEIGHBOUR", "NEIGHBOR", "STREET", "SEA", "ROAD", "PLOT", "SITE", "NORTH", "SOUTH", "EAST", "WEST", "جار", "شارع", "طريق", "بحر")


def _language(raw):
    letters = [c for c in raw if c.isalpha()]
    if not letters:
        return "NONE"
    arabic = sum(1 for c in letters if "ARABIC" in unicodedata.name(c, ""))
    latin = sum(1 for c in letters if "LATIN" in unicodedata.name(c, ""))
    if arabic and arabic >= latin:
        return "AR"
    # SHX-garbled Arabic shows as Latin letters mixed with symbols / mixed case runs with no dictionary word
    return "EN" if latin else "UNKNOWN"


def classify_text(raw):
    """Text role + canonical class for one label.  Raw text is preserved."""
    s = raw.strip()
    up = s.upper()
    if LEVEL_RE.match(s.replace(" ", "")):
        return {"TEXT_ROLE": "LEVEL_MARK", "CANONICAL_CLASS": None, "LANGUAGE": "NONE"}
    if NUMBER_RE.match(s):
        return {"TEXT_ROLE": "DIMENSION_OR_NUMBER", "CANONICAL_CLASS": None, "LANGUAGE": "NONE"}
    words = re.sub(r"[^A-Z\u0600-\u06FF ]", " ", up).split()
    if words and all(w in SITE_WORDS or w in ("VIEW",) for w in words) and any(w in SITE_WORDS for w in words):
        return {"TEXT_ROLE": "SITE_LABEL", "CANONICAL_CLASS": None, "LANGUAGE": _language(s)}      # the whole label is a site phrase (NEIGHBOUR, STREET, SEA VIEW), never a substring
    lang = _language(s)
    if lang == "AR":
        for k in sorted(AR, key=len, reverse=True):
            if k in s:
                return {"TEXT_ROLE": "ROOM_NAME", "CANONICAL_CLASS": AR[k], "LANGUAGE": "AR", "MATCHED": k}
        return {"TEXT_ROLE": "UNCLASSIFIED_TEXT", "CANONICAL_CLASS": "UNKNOWN", "LANGUAGE": "AR"}
    if lang == "EN":
        for k in sorted(EN, key=len, reverse=True):
            if re.search(r"(?<![A-Z])" + re.escape(k) + r"(?![A-Z])", up):
                return {"TEXT_ROLE": "ROOM_NAME", "CANONICAL_CLASS": EN[k], "LANGUAGE": "EN", "MATCHED": k}
        # mixed-case runs with symbols and no dictionary hit: an undecodable SHX rendering
        symbols = sum(1 for c in s if not c.isalnum() and not c.isspace() and c not in ".-/")
        if symbols >= 1 or (s != up and s != s.title() and s != s.lower()):
            return {"TEXT_ROLE": "UNDECODABLE_TEXT", "CANONICAL_CLASS": "UNKNOWN", "LANGUAGE": "UNDECODABLE"}
        return {"TEXT_ROLE": "UNCLASSIFIED_TEXT", "CANONICAL_CLASS": "UNKNOWN", "LANGUAGE": "EN"}
    return {"TEXT_ROLE": "UNDECODABLE_TEXT", "CANONICAL_CLASS": "UNKNOWN", "LANGUAGE": "UNDECODABLE"}


def anchors(view, cells, regions, grids, texts, owner_labels=(), ai_labels=()):
    """SEMANTIC_ANCHOR_REGISTER rows; attaches FUNCTIONAL_ZONES to regions without renaming geometry."""
    label, meta, cell = grids["cell_label"], grids["meta"], grids["cell"]
    cell_of = {c["RUN_LABEL_NOT_A_KEY"]: c for c in cells}
    rows = []
    def place(raw, x, y, source, status_if_room, method):
        cls = classify_text(raw)
        lab = _label_at(label, meta, x, y, cell)
        c = cell_of.get(lab)
        attached = c["CELL_ID"] if c else None
        region = c.get("PHYSICAL_SPACE_ID") if c else None
        role = cls["TEXT_ROLE"]
        if role == "ROOM_NAME":
            status = status_if_room if attached else "UNRESOLVED"
        elif role in ("UNDECODABLE_TEXT", "UNCLASSIFIED_TEXT"):
            status = "UNRESOLVED"
        else:
            status = "NOT_APPLICABLE"
        rows.append({"ANCHOR_ID": ids.anchor_id(view["VIEW_ID"], role, raw, (x, y)), "RAW_TEXT": raw, "LANGUAGE": cls["LANGUAGE"], "TEXT_ROLE": role, "CANONICAL_CLASS": cls["CANONICAL_CLASS"],
                     "SEMANTIC_ROLE": ("WET_ROOM" if cls["CANONICAL_CLASS"] in WET else ("CIRCULATION" if cls["CANONICAL_CLASS"] in ("STAIR", "CORRIDOR", "ELEVATOR", "ENTRANCE") else
                                       ("EXTERIOR" if cls["CANONICAL_CLASS"] in ("ROOF", "COURT", "GARDEN", "POOL", "BALCONY", "TERRACE") else ("DRY_ROOM" if role == "ROOM_NAME" else None)))),
                     "POSITION_MM": [round(x, 1), round(y, 1)], "SOURCE": source, "ATTACHED_SPACE_ID": attached, "ATTACHED_PHYSICAL_SPACE_ID": region, "ATTACHMENT_METHOD": method,
                     "IDENTITY_STATUS": status, "CONFLICT_GROUP": None, "CREATES_GEOMETRY": False})
    for t in texts:
        place(t.value, t.x, t.y, {"KIND": "CAD_TEXT", "LAYER": t.provenance.layer, "HANDLE": t.provenance.handle}, "SOURCE_TEXT_ESTABLISHED", "TEXT_INSERTION_INSIDE_CELL")
    for o in owner_labels:
        place(o["TEXT"], o["X"], o["Y"], {"KIND": "OWNER_PROJECT_INPUT", "ID": o.get("ID")}, "OWNER_CONFIRMED", "OWNER_POINT_INSIDE_CELL")
    for a in ai_labels:
        place(a["TEXT"], a["X"], a["Y"], {"KIND": "AI_VISUAL_READ", "MODEL": a.get("MODEL"), "PAGE": a.get("PAGE")}, "AI_INTERPRETED", "TRANSFORMED_RASTER_POINT_INSIDE_CELL")
    # functional zones per cell: several labels in one cell are several zones (open plan), never a pick and never a conflict by themselves;
    # a CONFLICT is two anchors at the same place (within 500 mm) that name different classes
    by_cell = {}
    for r in rows:
        if r["TEXT_ROLE"] == "ROOM_NAME" and r["ATTACHED_SPACE_ID"]:
            by_cell.setdefault(r["ATTACHED_SPACE_ID"], []).append(r)
    zones = []
    for cid, al in by_cell.items():
        for i, a in enumerate(al):
            for b in al[i + 1:]:
                if a["CANONICAL_CLASS"] != b["CANONICAL_CLASS"] and math.hypot(a["POSITION_MM"][0] - b["POSITION_MM"][0], a["POSITION_MM"][1] - b["POSITION_MM"][1]) <= 500:
                    g = ids.make_id("FUNCTIONAL_ZONE", cid, "CONFLICT", a["ANCHOR_ID"], b["ANCHOR_ID"])
                    a["CONFLICT_GROUP"] = b["CONFLICT_GROUP"] = g; a["IDENTITY_STATUS"] = b["IDENTITY_STATUS"] = "CONFLICT"
        classes = sorted({a["CANONICAL_CLASS"] for a in al})
        for cls in classes:
            members = [a for a in al if a["CANONICAL_CLASS"] == cls]
            st = "CONFLICT" if any(a["IDENTITY_STATUS"] == "CONFLICT" for a in members) else ("OWNER_CONFIRMED" if any(a["IDENTITY_STATUS"] == "OWNER_CONFIRMED" for a in members) else
                                                                                               ("SOURCE_TEXT_ESTABLISHED" if any(a["IDENTITY_STATUS"] == "SOURCE_TEXT_ESTABLISHED" for a in members) else members[0]["IDENTITY_STATUS"]))
            zones.append({"FUNCTIONAL_ZONE_ID": ids.make_id("FUNCTIONAL_ZONE", cid, cls), "CELL_ID": cid, "PHYSICAL_SPACE_ID": next(a["ATTACHED_PHYSICAL_SPACE_ID"] for a in al),
                          "CANONICAL_CLASS": cls, "ANCHORS": [a["ANCHOR_ID"] for a in members], "IDENTITY_STATUS": st, "RAW_LABELS": [a["RAW_TEXT"] for a in members],
                          "SHARES_CELL_WITH": [c for c in classes if c != cls]})
    site_hits = {}
    for r in rows:
        if r["TEXT_ROLE"] == "SITE_LABEL" and r["ATTACHED_SPACE_ID"]:
            site_hits[r["ATTACHED_SPACE_ID"]] = site_hits.get(r["ATTACHED_SPACE_ID"], 0) + 1
    for c in cells:
        c["SITE_LABELS_INSIDE"] = site_hits.get(c["CELL_ID"], 0)
    for reg in regions:
        zs = [z for z in zones if z["PHYSICAL_SPACE_ID"] == reg["PHYSICAL_SPACE_ID"]]
        reg["FUNCTIONAL_ZONES"] = [z["FUNCTIONAL_ZONE_ID"] for z in zs]
        undec = [r for r in rows if r["ATTACHED_PHYSICAL_SPACE_ID"] == reg["PHYSICAL_SPACE_ID"] and r["TEXT_ROLE"] == "UNDECODABLE_TEXT"]
        reg["SEMANTIC_IDENTITY"] = {"ZONES": [(z["CANONICAL_CLASS"], z["IDENTITY_STATUS"]) for z in zs], "UNDECODABLE_LABELS": len(undec),
                                    "STATUS": "NONE" if not zs and not undec else ("UNRESOLVED" if not zs else ("SINGLE" if len(zs) == 1 else "MULTIPLE_FUNCTIONAL_ZONES_ONE_PHYSICAL_REGION"))}
    return rows, zones
