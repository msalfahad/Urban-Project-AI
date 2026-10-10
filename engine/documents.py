"""E22 — Document Numbers.

Everything numeric that appears on a quotation or contract is produced here,
never by the model: the reference number, the price table and its total, the
payment schedule, the validity date, the section ordinals, and the amount
written out in Arabic words. A7 writes the clauses; this module writes every
figure between them.

KWD is 1000 fils, so money rounds to 3 decimals and a split's rounding residual
goes to the largest share so the parts always equal the whole.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

FILS = 3

ORDINALS_AR = [
    "أولاً", "ثانياً", "ثالثاً", "رابعاً", "خامساً", "سادساً", "سابعاً",
    "ثامناً", "تاسعاً", "عاشراً", "حادي عشر", "ثاني عشر", "ثالث عشر",
    "رابع عشر", "خامس عشر", "سادس عشر", "سابع عشر", "ثامن عشر", "تاسع عشر",
    "عشرون",
]


def ordinal_ar(n: int) -> str:
    """1 -> أولاً, 2 -> ثانياً … for numbering document sections."""
    if not 1 <= n <= len(ORDINALS_AR):
        raise ValueError(f"no Arabic ordinal for section {n}")
    return ORDINALS_AR[n - 1]


def format_kwd(amount: float) -> str:
    """93500 -> '93,500.000 د.ك'."""
    return f"{amount:,.{FILS}f} د.ك"


def reference_number(issued: date, sequence: int, revision: int = 1, prefix: str = "UP") -> str:
    """UP/2026-9-001-R01 — year-month, running number, revision."""
    if sequence < 1 or revision < 1:
        raise ValueError("sequence and revision start at 1")
    return f"{prefix}/{issued.year}-{issued.month}-{sequence:03d}-R{revision:02d}"


def validity_expiry(issued: date, days: int) -> date:
    if days < 1:
        raise ValueError("validity must be at least one day")
    return issued + timedelta(days=days)


# ---- price table ---------------------------------------------------------------
@dataclass
class PriceLine:
    package: str            # Arabic package name, e.g. أعمال الهيكل الأسود
    amount_kwd: float
    note: str = ""          # e.g. بالإضافة إلى المواد المدعومة


def summarise_by_package(rows: list[tuple[str, float]]) -> list[PriceLine]:
    """Collapse priced BOQ rows (package, amount) into one line per package.

    Keeps first-seen order so the table reads in the order the BOQ was built.
    """
    totals: dict[str, float] = {}
    for package, amount in rows:
        if not package.strip():
            raise ValueError("every priced row needs a package name")
        if amount < 0:
            raise ValueError(f"negative amount for {package!r}")
        totals[package] = totals.get(package, 0.0) + amount
    return [PriceLine(p, round(a, FILS)) for p, a in totals.items()]


def grand_total(lines: list[PriceLine]) -> float:
    if not lines:
        raise ValueError("a price table needs at least one line")
    for line in lines:
        if line.amount_kwd < 0:
            raise ValueError(f"negative amount for {line.package!r}")
    return round(sum(l.amount_kwd for l in lines), FILS)


# ---- payment schedule ----------------------------------------------------------
@dataclass
class Milestone:
    trigger: str            # Arabic, e.g. عند توقيع العقد
    percent: float


def payment_schedule(total_kwd: float, milestones: list[Milestone]) -> list[dict]:
    """Turn percentage milestones into KWD amounts that sum to the total exactly."""
    if total_kwd < 0:
        raise ValueError("total_kwd must not be negative")
    if not milestones:
        raise ValueError("a payment schedule needs at least one milestone")
    for m in milestones:
        if not m.trigger.strip():
            raise ValueError("every milestone needs a trigger")
        if m.percent <= 0:
            raise ValueError(f"milestone {m.trigger!r} must have a positive percent")
    if abs(sum(m.percent for m in milestones) - 100.0) > 1e-6:
        raise ValueError("milestone percentages must sum to 100")

    amounts = [round(total_kwd * m.percent / 100.0, FILS) for m in milestones]
    residual = round(total_kwd - sum(amounts), FILS)
    if residual:
        biggest = max(range(len(amounts)), key=lambda i: (amounts[i], -i))
        amounts[biggest] = round(amounts[biggest] + residual, FILS)
    return [
        {"trigger": m.trigger, "percent": m.percent, "amount_kwd": a}
        for m, a in zip(milestones, amounts)
    ]


# ---- amount in words -----------------------------------------------------------
_UNITS = ["", "واحد", "اثنان", "ثلاثة", "أربعة", "خمسة", "ستة", "سبعة", "ثمانية", "تسعة",
          "عشرة", "أحد عشر", "اثنا عشر", "ثلاثة عشر", "أربعة عشر", "خمسة عشر",
          "ستة عشر", "سبعة عشر", "ثمانية عشر", "تسعة عشر"]
_TENS = ["", "", "عشرون", "ثلاثون", "أربعون", "خمسون", "ستون", "سبعون", "ثمانون", "تسعون"]
_HUNDREDS = ["", "مائة", "مائتان", "ثلاثمائة", "أربعمائة", "خمسمائة", "ستمائة",
             "سبعمائة", "ثمانمائة", "تسعمائة"]

# (one, two, 3-10 plural, 11-99 accusative singular)
_THOUSAND = ("ألف", "ألفان", "آلاف", "ألفاً")
_MILLION = ("مليون", "مليونان", "ملايين", "مليوناً")
_DINAR = ("دينار كويتي", "ديناران كويتيان", "دنانير كويتية", "ديناراً كويتياً")
_FILS = ("فلس", "فلسان", "فلوس", "فلساً")


def _below_1000(n: int) -> str:
    parts = []
    if n >= 100:
        parts.append(_HUNDREDS[n // 100])
        n %= 100
    if n >= 20:
        if n % 10:
            parts.append(f"{_UNITS[n % 10]} و{_TENS[n // 10]}")
        else:
            parts.append(_TENS[n // 10])
    elif n:
        parts.append(_UNITS[n])
    return " و".join(parts)


def _counted(n: int, forms: tuple[str, str, str, str], number_words: bool = True) -> str:
    """Attach a counted noun to n with the right Arabic form.

    1 and 2 use the noun alone (ألف, ألفان); 3-10 take the plural; 11-99 take
    the accusative singular; above 100 the last two digits decide.
    """
    one, two, plural, accusative = forms
    if n == 1:
        return one
    if n == 2:
        return two
    words = _below_1000(n) if number_words else ""
    last2 = n % 100
    if 3 <= last2 <= 10:
        noun = plural
    elif 11 <= last2 <= 99:
        noun = accusative
    else:
        noun = one
    return f"{words} {noun}".strip()


def _currency(n: int, forms: tuple[str, str, str, str]) -> str:
    """The noun for a whole amount already spelled out: 93,500 -> دينار كويتي."""
    one, two, plural, accusative = forms
    if n == 1:
        return f"{one} واحد"
    if n == 2:
        return two
    last2 = n % 100
    if 3 <= last2 <= 10:
        return plural
    if 11 <= last2 <= 99:
        return accusative
    return one


def _integer_words(n: int) -> str:
    if n == 0:
        return "صفر"
    if n >= 1_000_000_000:
        raise ValueError("amounts of a billion dinars or more are not supported")
    groups = []
    millions, rest = divmod(n, 1_000_000)
    thousands, units = divmod(rest, 1000)
    if millions:
        groups.append(_counted(millions, _MILLION))
    if thousands:
        groups.append(_counted(thousands, _THOUSAND))
    if units:
        groups.append(_below_1000(units))
    return " و".join(groups)


def amount_in_words_ar(amount: float) -> str:
    """110400 -> 'فقط مائة وعشرة آلاف وأربعمائة دينار كويتي لا غير'.

    The phrase a Kuwaiti contract puts beside the figure, so a mistyped digit
    cannot change the price unnoticed.
    """
    if amount < 0:
        raise ValueError("amount must not be negative")
    fils_total = round(amount * 1000)
    dinars, fils = divmod(fils_total, 1000)

    if dinars in (1, 2):
        text = _currency(dinars, _DINAR)
    else:
        text = f"{_integer_words(dinars)} {_currency(dinars, _DINAR)}"

    if fils:
        if fils in (1, 2):
            fils_text = _currency(fils, _FILS)
        else:
            fils_text = f"{_integer_words(fils)} {_currency(fils, _FILS)}"
        text = f"{text} و{fils_text}"
    return f"فقط {text} لا غير"
