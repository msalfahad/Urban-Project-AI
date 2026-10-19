"""POOL CHECK LIST V1 (T-057) - for every villa with a pool: is a pool pump room drawn, where are the main manholes,
what pool type is drawn. Generic, bilingual (Arabic / English), stdlib only; ezdxf only in the optional DXF intake.

Rule: owner answer Q-19 (2026-10-19, docs/agents/OWNER_QUESTIONS.md "Answered"): "whenever there is a pool, always
check for the pool pump room, and check where the house's main manholes are". UP-QTY-STATUS-001: every checked item
is reported once (FOUND, HELD or NOT_ESTABLISHED), never silently absent. UP-KB-PREC-001: only what the drawing
shows is read; nothing is guessed. This is a CHECK, not a quantity: it releases no BOQ line and no number.

    check(texts, blocks=(), pool_elements=())  -> result dict (see below)
    census_rows(result)                        -> flat rows, one per checked item, for a census / report
    items_from_dxf(doc, sheet_of=None)         -> (texts, blocks) from an ezdxf document (TEXT, MTEXT, ATTRIB,
                                                  INSERT names, labels inside blocks at their world position)

Inputs (plain dicts, so any intake can feed it)
    texts          {"text", "sheet", "handle"?, "x"?, "y"?}       decoded Unicode text (Arabic SHX is decoded
                                                                   upstream, T-047; Latin SHX codes match nothing)
    blocks         {"name", "sheet", "handle"?, "x"?, "y"?}       block insert names
    pool_elements  {"sheet", "id"?, "kind"?}                       pool elements of a structural route (route G)

Pool present when a short label types as POOL in ROOM_VOCAB_V2 (engine.source.room_vocab.classify: 'حمام سباحة' is
a pool, 'POOL PUMP ROOM' is a plant room, not a pool) or a route pool element is passed. No pool -> no records
(nothing to check), result["pool"]["status"] = "NOT_DRAWN".

Records when a pool is present (item -> status, reason)
    POOL_PUMP_ROOM   FOUND (each pump-room label or pump block with its sheet) | HELD POOL_PUMP_ROOM_NOT_FOUND
    MAIN_MANHOLES    FOUND (manholes labelled main / final / last) | HELD MAIN_MANHOLE_NOT_IDENTIFIED (manholes
                     drawn, none labelled main: all are listed, none is picked) | HELD MAIN_MANHOLES_NOT_FOUND
    POOL_TYPE        OVERFLOW (an overflow channel, balance tank or infinity edge drawn) | NORMAL (a skimmer drawn) |
                     HELD POOL_TYPE_CONFLICT (both drawn) | NOT_ESTABLISHED (no type drawn; never a default)

A label longer than MAX_LABEL_CHARS (a general note, e.g. a specification sentence that mentions manholes) is not a
drawn item: it is kept under "notes" of its record so a reviewer sees it, but never makes an item FOUND.
"""

from __future__ import annotations

import re

from engine.source import drawing_model as DM
from engine.source import room_vocab as RV

CHECKLIST_ID = "POOL_CHECKLIST_V1"
RULES = ("OWNER Q-19 (2026-10-19)", "UP-QTY-STATUS-001", "UP-KB-PREC-001")
MAX_LABEL_CHARS = RV.MAX_LABEL_CHARS           # a note / title / sentence is not a tag (as the room vocabulary)
_AL = r"(?:ال)?"                               # optional Arabic definite article
_E = r"(?:^|[^A-Z])"                           # an English word starts here (no letter before it)
_Z = r"(?=$|[^A-Z])"                           # ... and ends here

# Reviewed vocabulary tables (generic Kuwait villa vocabulary; no project names). Patterns run on
# drawing_model.normalize(text).upper(); Arabic ة / ه and the definite article are both accepted.
POOL_WORDS = (rf"{_E}POOL{_Z}", r"SWIMMING", rf"{_AL}مسبح", rf"سباح[ةه]")

PUMP_ROOM_LABELS = (
    (rf"{_E}PUMPS?{_Z}", "pump / pump room / pump house"),
    (rf"{_E}(POOL|SWIMMING\s*POOL)\s*(PLANT|FILTERS?|FILTRATION|MACHINE(RY)?|EQUIPMENT|MECH(ANICAL)?){_Z}",
     "pool plant / filter / machine room"),
    (rf"{_E}FILTRATION\s*(ROOM|PLANT){_Z}", "filtration room"),
    (r"مضخ(ة|ه|ات)", "pump (Arabic)"),
    (rf"(غرف[ةه]|حجر[ةه])\s*{_AL}(فلاتر|فلتر|معدات|مكائن|ماكينات|تشغيل)\s*({_AL}(حمام|حوض|بركة|بركه)\s*)?"
     rf"{_AL}(مسبح|سباح[ةه])", "pool filter / equipment / plant room (Arabic)"),
)
PUMP_BLOCKS = (
    (rf"{_E}PUMPS?{_Z}", "pump block"),
    (r"POOLPUMPS?|PUMPSET", "pool pump block"),
    (rf"{_E}(POOL|SWIM(MING)?)\s*(FILTERS?|PLANT|EQUIP(MENT)?){_Z}", "pool filter / plant block"),
    (r"مضخ(ة|ه|ات)", "pump block (Arabic)"),
)
MANHOLE_LABELS = (
    (r"MAN\s*-?\s*HOLES?", "manhole"),
    (r"(?:^|[^A-Z0-9])M\.?H\.?(?=$|[^A-Z])", "MH tag"),
    (r"INSPECTION\s*(CHAMBER|PIT)S?", "inspection chamber"),
    (rf"(غرف[ةه]|غرف)\s*{_AL}تفتيش", "inspection chamber (Arabic)"),
    (r"م[اآ]?ن\s*هول|منهول", "manhole (Arabic)"),
)
MANHOLE_BLOCKS = (
    (r"MAN\s*HOLES?|MANHOLES?", "manhole block"),
    (rf"{_E}MH{_Z}|^MH\d", "MH block"),
    (r"INSPECTION\s*CHAMBER|{0}IC\s*CHAMBER".format(_E), "inspection chamber block"),
    (rf"(غرف[ةه])\s*{_AL}تفتيش|منهول", "manhole block (Arabic)"),
)
MAIN_WORDS = (rf"{_E}(MAIN|FINAL|LAST){_Z}", rf"{_E}M\.?\s?M\.?\s?H{_Z}", r"رئيسي(ة|ه)?",
              rf"{_AL}(أخير|اخير|آخر|اخر)(ة|ه)?", r"نهائي(ة|ه)?")
OVERFLOW_WORDS = (r"OVER\s*-?\s*FLOW", r"BALANC(E|ING)\s*TANK", r"SURGE\s*TANK", rf"{_E}INFINITY{_Z}",
                  r"VANISHING\s*EDGE", r"خزان\s*{0}(موازن[ةه]|توازن|تعادل)".format(_AL), r"فائض|فيضان", r"طفح")
NORMAL_WORDS = (r"SKIMMERS?", r"سكيمر|كاشط")


def _norm(text):
    return DM.normalize(text or "").upper()


def _first(patterns, u):
    """-> (pattern text or phrase, matched text) of the first matching entry, else (None, None)."""
    for entry in patterns:
        p, why = entry if isinstance(entry, tuple) else (entry, entry)
        m = re.search(p, u)
        if m:
            return why, m.group(0).strip()
    return None, None


def _evidence(kind, src, value, why, matched):
    rec = {"kind": kind, "value": value, "sheet": src.get("sheet"), "handle": src.get("handle"),
           "x": src.get("x"), "y": src.get("y"), "basis": why, "matched": matched}
    return rec


def _block_text(name):
    """block names use _ - . as separators ('POOL_PUMP-01'); they count as spaces for the word tests."""
    return re.sub(r"[_\-.$|]+", " ", _norm(name))


def check(texts, blocks=(), pool_elements=()):
    texts = [t for t in (texts or ()) if (t.get("text") or "").strip()]
    blocks = [b for b in (blocks or ()) if (b.get("name") or "").strip()]
    pool_ev, pump, notes = [], [], {"POOL_PUMP_ROOM": [], "MAIN_MANHOLES": [], "POOL_TYPE": []}
    manholes, overflow, normal = [], [], []

    for t in texts:
        u = _norm(t["text"])
        short = len(u) <= MAX_LABEL_CHARS
        if short:
            c = RV.classify(t["text"])
            if c.get("code") == "POOL":
                pool_ev.append(_evidence("LABEL", t, t["text"], f"{RV.VOCAB_ID}: {c['basis']}", c["matched"]))
        for item, table, sink in (("POOL_PUMP_ROOM", PUMP_ROOM_LABELS, pump),
                                  ("MAIN_MANHOLES", MANHOLE_LABELS, manholes),
                                  ("POOL_TYPE", OVERFLOW_WORDS, overflow), ("POOL_TYPE", NORMAL_WORDS, normal)):
            why, m = _first(table, u)
            if not why:
                continue
            ev = _evidence("LABEL", t, t["text"], why, m)
            if not short:
                ev["basis"] = f"note longer than {MAX_LABEL_CHARS} characters (not a drawn item): {why}"
                notes[item].append(ev)
                continue
            if item == "POOL_PUMP_ROOM":
                ev["pool_specific"] = _first(POOL_WORDS, u)[0] is not None
            if item == "MAIN_MANHOLES":
                ev["main"] = _first(MAIN_WORDS, u)[0] is not None
            sink.append(ev)

    for b in blocks:
        u = _block_text(b["name"])
        for item, table, sink in (("POOL_PUMP_ROOM", PUMP_BLOCKS, pump), ("MAIN_MANHOLES", MANHOLE_BLOCKS, manholes),
                                  ("POOL_TYPE", OVERFLOW_WORDS, overflow), ("POOL_TYPE", NORMAL_WORDS, normal)):
            why, m = _first(table, u)
            if not why:
                continue
            ev = _evidence("BLOCK", b, b["name"], why, m)
            if item == "POOL_PUMP_ROOM":
                ev["pool_specific"] = re.search(r"POOL|SWIM|مسبح|سباح", u) is not None
            if item == "MAIN_MANHOLES":
                ev["main"] = _first(MAIN_WORDS, u)[0] is not None
            sink.append(ev)

    for e in pool_elements or ():
        pool_ev.append({"kind": "ROUTE_ELEMENT", "value": e.get("id") or e.get("kind"), "sheet": e.get("sheet"),
                        "handle": e.get("handle"), "x": None, "y": None, "basis": "pool element of a structural route",
                        "matched": e.get("kind")})

    result = {"checklist": CHECKLIST_ID, "rules": list(RULES),
              "pool": {"status": "DRAWN" if pool_ev else "NOT_DRAWN", "evidence": pool_ev,
                       "sheets": sorted({str(e["sheet"]) for e in pool_ev if e["sheet"] is not None})},
              "records": []}
    if not pool_ev:
        return result                          # no pool: the owner's pool checks do not apply (no records)

    recs = result["records"]
    if pump:
        recs.append({"item": "POOL_PUMP_ROOM", "status": "FOUND", "reason": None, "found": pump,
                     "notes": notes["POOL_PUMP_ROOM"]})
    else:
        recs.append({"item": "POOL_PUMP_ROOM", "status": "HELD", "reason": "POOL_PUMP_ROOM_NOT_FOUND", "found": [],
                     "notes": notes["POOL_PUMP_ROOM"],
                     "basis": "a pool is drawn; no pump-room label and no pump block on any sheet passed"})
    mains = [m for m in manholes if m["main"]]
    if mains:
        recs.append({"item": "MAIN_MANHOLES", "status": "FOUND", "reason": None, "found": mains,
                     "other_manholes": [m for m in manholes if not m["main"]], "notes": notes["MAIN_MANHOLES"]})
    elif manholes:
        recs.append({"item": "MAIN_MANHOLES", "status": "HELD", "reason": "MAIN_MANHOLE_NOT_IDENTIFIED", "found": [],
                     "other_manholes": manholes, "notes": notes["MAIN_MANHOLES"],
                     "basis": "manholes are drawn but none is labelled main / final / last: none is picked"})
    else:
        recs.append({"item": "MAIN_MANHOLES", "status": "HELD", "reason": "MAIN_MANHOLES_NOT_FOUND", "found": [],
                     "other_manholes": [], "notes": notes["MAIN_MANHOLES"],
                     "basis": "a pool is drawn; no manhole label and no manhole block on any sheet passed"})
    if overflow and normal:
        recs.append({"item": "POOL_TYPE", "status": "HELD", "reason": "POOL_TYPE_CONFLICT", "value": None,
                     "found": overflow + normal, "notes": notes["POOL_TYPE"],
                     "basis": "both an overflow sign and a skimmer are drawn"})
    elif overflow:
        recs.append({"item": "POOL_TYPE", "status": "FOUND", "reason": None, "value": "OVERFLOW", "found": overflow,
                     "notes": notes["POOL_TYPE"]})
    elif normal:
        recs.append({"item": "POOL_TYPE", "status": "FOUND", "reason": None, "value": "NORMAL", "found": normal,
                     "notes": notes["POOL_TYPE"]})
    else:
        recs.append({"item": "POOL_TYPE", "status": "NOT_ESTABLISHED", "reason": "POOL_TYPE_NOT_DRAWN", "value": None,
                     "found": [], "notes": notes["POOL_TYPE"],
                     "basis": "no overflow channel, balance tank or skimmer drawn: no type is assumed"})
    return result


def census_rows(result):
    """one flat row per checked item (none when no pool is drawn)."""
    rows = []
    for r in result.get("records", ()):
        found = r.get("found") or []
        rows.append({"checklist": result["checklist"], "item": r["item"], "status": r["status"],
                     "reason": r.get("reason"), "value": r.get("value"),
                     "sheets": sorted({str(f["sheet"]) for f in found if f.get("sheet") is not None}),
                     "count": len(found), "other": len(r.get("other_manholes") or []),
                     "notes": len(r.get("notes") or [])})
    return rows


def items_from_dxf(doc, sheet_of=None):
    """(texts, blocks) of an ezdxf document. Every layout is read (model space and paper spaces); a label inside a
    block insert is read at its world position (rotation, mirror and scale applied by ezdxf virtual entities), nested
    blocks included. sheet_of(layout_name, x, y) -> sheet id (default: the layout name)."""
    texts, blocks = [], []

    def sheet(layout, x, y):
        return sheet_of(layout, x, y) if sheet_of else layout

    def add_text(e, layout, handle):
        t = e.dxftype()
        if t == "MTEXT":
            s, p = e.plain_text(), e.dxf.insert
        elif t in ("TEXT", "ATTRIB", "ATTDEF"):
            if t == "ATTDEF":
                return
            s, p = e.dxf.text, e.ocs().to_wcs(e.dxf.insert)   # TEXT insert is in OCS: a mirrored text has -Z
        else:
            return
        texts.append({"text": s, "sheet": sheet(layout, p[0], p[1]), "handle": handle, "x": p[0], "y": p[1]})

    def walk(entities, layout, depth, root_handle):
        for e in entities:
            h = root_handle or e.dxf.handle
            if e.dxftype() == "INSERT":
                p = e.ocs().to_wcs(e.dxf.insert)               # INSERT insert is in OCS too
                blocks.append({"name": e.dxf.name, "sheet": sheet(layout, p[0], p[1]), "handle": h,
                               "x": p[0], "y": p[1]})
                for a in e.attribs:
                    add_text(a, layout, h)
                if depth < 8:
                    try:
                        walk(list(e.virtual_entities()), layout, depth + 1, h)
                    except Exception:          # a block ezdxf cannot explode keeps its name record only
                        pass
            else:
                add_text(e, layout, h)

    for layout in doc.layouts:
        walk(layout, layout.name, 0, None)
    return texts, blocks
