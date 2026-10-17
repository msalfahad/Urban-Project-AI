"""Parse a Urban Projects Manager "Cost By Category" PDF into a RateLibrary.

Deterministic — no model. Reads the PDF's word coordinates, reconstructs the
table by column x-position, and self-checks by comparing the parsed item sums to
the stated category and grand totals. If those reconcile, the parse is trusted.

Column x-bands (from the export layout):
  description  x < 300     (Arabic desc with the qty glued on the end)
  contractor   150–260     (optional)
  unit         300–380     (item | qty | m3 | ton | m2 | KWD)
  unit cost    400–470     (number, then "KWD")
  total        500–560     (number, then "KWD")
"""

from __future__ import annotations

import re
import sys
import unicodedata

from engine.rate_library import RateLibrary, RateCategory, RateItem

_NUM = re.compile(r"-?[\d,]+(?:\.\d+)?")
_UNITS = {"item", "qty", "m3", "m2", "ton", "kg", "no", "KWD"}
_TYPES_EN = {"General", "Labor", "Material", "Logistics"}


def _num(s: str) -> float | None:
    m = _NUM.search(s.replace(",", "") if s else "")
    if not m:
        return None
    try:
        return float(m.group().replace(",", ""))
    except ValueError:
        return None


def _trailing_qty(text: str) -> float | None:
    """The number glued to the end of a description/contractor cell."""
    m = re.search(r"([\d,]+(?:\.\d+)?)\s*$", text)
    return float(m.group(1).replace(",", "")) if m else None


def _norm(s: str) -> str:
    return unicodedata.normalize("NFKC", s)


def parse_cost_export(pdf_path: str) -> RateLibrary:
    import pymupdf

    doc = pymupdf.open(pdf_path)
    lib = RateLibrary()
    current: RateCategory | None = None
    current_type = ""

    for page in doc:
        # cluster words into rows by y
        rows: dict[int, list[tuple[float, str]]] = {}
        for x0, y0, x1, y1, word, *_ in page.get_text("words"):
            rows.setdefault(round(y0), []).append((x0, word))

        for y in sorted(rows):
            cells = sorted(rows[y])
            joined = _norm(" ".join(w for _, w in cells))

            # skip page furniture
            if joined.startswith("Alsenan") or joined.startswith("Cost By") \
               or joined.startswith("Page") or re.match(r"^\d{2}/\d{2}/\d{4}", joined):
                if lib.project == "" and joined.startswith("Alsenan"):
                    lib.project = "Alsenan Chalet"
                continue
            if "Description" in joined and "Contractor" in joined:
                continue

            # grand total
            if joined.startswith("Grand Total"):
                current = None
                continue
            if joined.replace(" ", "").endswith("KWD") and current is None and lib.grand_total is None \
               and _num(joined) and "Total" not in joined and len(cells) <= 2:
                lib.grand_total = _num(joined)
                continue

            # category total  (e.g. "Category Total:<name><number> KWD")
            if "Category" in joined and "Total:" in joined:
                if current is not None:
                    current.stated_total = _num(joined.split("Total:")[-1])
                continue
            # type total
            if joined.startswith("Type") and "Total:" in joined:
                continue

            # type header
            plain = joined.strip()
            if plain in _TYPES_EN or "مقطوعيه" in plain.replace(" ", ""):
                current_type = plain
                continue

            # is this an item row? needs a unit cell and a total number on the right
            unit = ""
            unit_cost = total = None
            desc_parts, contractor = [], ""
            for x, w in cells:
                wn = _norm(w)
                if x < 150:
                    desc_parts.append(wn)
                elif 150 <= x < 270:
                    contractor += wn
                elif 300 <= x < 390 and wn.strip() in _UNITS:
                    unit = wn.strip()
                elif 400 <= x < 480:
                    v = _num(wn)
                    if v is not None:
                        unit_cost = v
                elif x >= 500:
                    v = _num(wn)
                    if v is not None:
                        total = v

            if unit and total is not None:
                desc = "".join(desc_parts)
                qty = _trailing_qty(contractor) or _trailing_qty(desc)
                desc_clean = re.sub(r"[\d,]+(?:\.\d+)?\s*$", "", desc).strip()
                if current is None:
                    current = RateCategory(name="(uncategorised)")
                    lib.categories.append(current)
                current.items.append(RateItem(
                    description=desc_clean or desc,
                    category=current.name,
                    type=current_type,
                    contractor=re.sub(r"[\d,]+(?:\.\d+)?\s*$", "", contractor).strip(),
                    qty=qty,
                    unit=unit if unit != "KWD" else "",
                    unit_cost=unit_cost,
                    total=total,
                ))
                continue

            # otherwise: a lone Arabic line = a new category name
            if plain and not any(ch.isascii() and ch.isalpha() for ch in plain):
                current = RateCategory(name=plain)
                current_type = ""
                lib.categories.append(current)

    return lib


if __name__ == "__main__":
    lib = parse_cost_export(sys.argv[1])
    print(f"project: {lib.project}   categories: {len(lib.categories)}   "
          f"items: {len(lib.all_items())}")
    print(f"computed grand total: {lib.computed_grand_total():,.0f}   "
          f"stated: {lib.grand_total}")
    problems = lib.reconciliation_report()
    print("reconciles!" if not problems else "MISMATCHES:")
    for p in problems:
        print("  -", p)
