"""Reference data for the deterministic auditor.

These are engineering sanity bands and keyword tables, not model output. They
are the checkable knowledge the rules apply. Every band is deliberately wide —
the auditor flags the clearly-wrong, and leaves judgement calls to the engineer.

Tune these to Urban Projects' own practice as real data accrues (E19).
"""

from __future__ import annotations

# --- Concrete ------------------------------------------------------------
# Recognised structural concrete grades used in Kuwait residential/commercial
# work. Lean/blinding concrete is the low-grade layer under foundations and must
# never be priced or classified as structural.
STRUCTURAL_GRADES = {"C25", "C30", "C35", "C40", "C45", "C50"}
LEAN_GRADES = {"C10", "C15", "C20"}
ALL_GRADES = STRUCTURAL_GRADES | LEAN_GRADES

# Keywords (English + Arabic) that identify a concrete line and its intended role.
CONCRETE_KEYWORDS = ["concrete", "خرسانة", "rc ", "r.c", "reinforced"]
LEAN_KEYWORDS = ["lean", "blinding", "نظافة", "عادية", "بلايندنج"]
STRUCTURAL_ELEMENT_KEYWORDS = [
    "column", "beam", "slab", "footing", "foundation", "raft", "wall",
    "عمود", "جسر", "سقف", "بلاطة", "قاعدة", "أساس", "لبشة", "جدار",
]

# --- Steel ratio (kg of reinforcement per m3 of concrete) ----------------
# Below the RED floor or above the RED ceiling is almost certainly an error
# (wrong unit, misplaced decimal, or steel/concrete mismatched). The YELLOW band
# is "unusual, look at it".
STEEL_RATIO_RED_MIN = 40.0
STEEL_RATIO_YELLOW_MIN = 70.0
STEEL_RATIO_YELLOW_MAX = 200.0
STEEL_RATIO_RED_MAX = 300.0

# --- Waste ---------------------------------------------------------------
# Materials that normally carry a cutting/breakage waste allowance. A line in one
# of these families with no waste/order quantity is worth a YELLOW.
WASTE_EXPECTED_KEYWORDS = [
    "tile", "ceramic", "porcelain", "marble", "granite", "block", "cladding",
    "سيراميك", "بورسلان", "رخام", "جرانيت", "بلوك", "طابوق", "كسوة", "بورسيلين",
]

# --- Unit vocabulary -----------------------------------------------------
# Maps many written unit labels (English + Arabic + common misspellings) to a
# canonical dimension so "mixed unit" totals can be detected.
UNIT_CANON = {
    # count
    "no": "count", "nos": "count", "no.": "count", "pcs": "count",
    "pc": "count", "each": "count", "ea": "count", "item": "count",
    "عدد": "count", "قطعة": "count", "حبة": "count",
    # length
    "m": "length", "lm": "length", "l.m": "length", "rm": "length",
    "متر": "length", "م.ط": "length", "مط": "length", "م ط": "length",
    # area
    "m2": "area", "sqm": "area", "sq.m": "area", "m²": "area",
    "م2": "area", "م²": "area", "متر مربع": "area",
    # volume
    "m3": "volume", "cum": "volume", "cu.m": "volume", "m³": "volume",
    "م3": "volume", "م³": "volume", "متر مكعب": "volume",
    # weight
    "kg": "weight", "kgs": "weight", "ton": "weight", "tonne": "weight",
    "كجم": "weight", "كغم": "weight", "طن": "weight",
    # money / lump
    "ls": "lump", "lump": "lump", "l.s": "lump", "مقطوعية": "lump",
}


def canonical_unit(raw: str) -> str:
    """Normalise a written unit to its dimension, or '' if unrecognised."""
    if not raw:
        return ""
    key = raw.strip().lower().replace(" ", "")
    # try direct, then the spaced/dotted originals
    if key in UNIT_CANON:
        return UNIT_CANON[key]
    return UNIT_CANON.get(raw.strip().lower(), "")


def extract_grade(text: str) -> str | None:
    """Pull a concrete grade like C30 out of a description, if present."""
    import re

    m = re.search(r"\bC\s?-?\s?(\d{2})\b", text, re.IGNORECASE)
    if not m:
        return None
    return f"C{m.group(1)}"
