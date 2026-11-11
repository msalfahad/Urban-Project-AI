"""T-692 keyword text census of the two DXF drawings (counts only; no drawing text is written anywhere).

Reads the private copies at run time (decoded into .work/private, outside every worktree) and returns, per keyword group,
the number of TEXT / MTEXT / ATTRIB entities (model, paper and block definitions) whose plain text matches. Limitation:
Arabic labels drawn in SHX fonts do not decode to Arabic, so a 0 is evidence of no English / decodable note only, never
proof of absence; it complements the sheet-by-sheet reading of T-357 / T-317 / T-360 and does not replace it.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

KEYWORDS = {
    "clearance": r"clear|demol|تنظيف|إزالة|ازالة",
    "termite": r"termit|anti.?t|نمل|مبيد|soil treat",
    "dewater": r"dewater|ground ?water|shoring|مياه جوفية",
    "rooms": r"bed ?room|living|majlis|diwan|toilet|bath|kitchen|غرفة|صالة",
    "kitchen": r"kitchen|مطبخ|laundry|غسيل|pantry|splash",
    "marble": r"marble|رخام|granite|جرانيت",
    "profile": r"profile|transition|بروفايل",
    "facade": r"facade|elevation|واجهة",
    "spatter": r"spatter|dash|طرطشة|رشة",
    "bead": r"\bbead|زاوية",
    "edge": r"\bedge|mitre|miter",
    "cladding": r"clad|stone|حجر|كلادينج",
    "ceiling": r"gyps|جبس|ceiling|سقف مستعار|decor|ديكور|false",
    "cornice": r"cornice|\bcove|كرانيش",
    "access": r"access panel|فتحة صيانة",
    "lift": r"\blift|elevator|مصعد",
    "nosing": r"nosing|\bnose",
    "glass": r"glass|زجاج|\bpost|handrail|درابزين|railing",
    "shower": r"shower|دش|tanking",
    "balcony": r"balcon|بلكون|terrace|تراس|planter|شرفة",
    "mesh": r"\bmesh|شبك|شرمات",
    "parapet": r"parapet|دروة",
    "sanitary": r"\bw\.?c\b|basin|floor drain|\bf\.?d\b|بالوعة|مغسلة",
    "electrical": r"electric|كهرب|socket|\bD\.?B\b",
    "hvac": r"\bduct|hvac|تكييف|split unit",
    "lv": r"cctv|intercom|\bdata\b",
    "garden": r"garden|حديقة|landscap|grass|irrig",
    "expansion": r"expansion|movement joint|فاصل|sealant",
    "joinery": r"wardrobe|cabinet|دولاب|كبت|joinery",
    "metalwork": r"pergola|canopy|مظلة|برجول",
}


def texts(path: Path) -> list[str]:
    import ezdxf  # pinned 1.4.4 in the venv

    doc = ezdxf.readfile(str(path))
    out: list[str] = []

    def walk(layout):
        for e in layout:
            t = e.dxftype()
            if t == "MTEXT":
                out.append(e.plain_text())
            elif t in ("TEXT", "ATTRIB"):
                out.append(e.dxf.text)
            elif t == "INSERT":
                out.extend(a.dxf.text for a in e.attribs)

    for lay in doc.layouts:
        walk(lay)
    for blk in doc.blocks:
        if not blk.name.startswith("*"):
            walk(blk)
    return out


def count(strings: list[str], keywords: dict | None = None) -> dict:
    keywords = KEYWORDS if keywords is None else keywords
    return {k: sum(1 for s in strings if re.search(p, s or "", re.I)) for k, p in keywords.items()}


def census(paths: list[Path]) -> dict:
    per = {}
    total = {k: 0 for k in KEYWORDS}
    n = 0
    for p in paths:
        s = texts(p)
        n += len(s)
        c = count(s)
        per[p.name] = {"texts": len(s), "hits": c}
        for k, v in c.items():
            total[k] += v
    return {"texts": n, "files": per, "hits": total}


if __name__ == "__main__":
    import json

    print(json.dumps(census([Path(a) for a in sys.argv[1:]]), indent=1))
