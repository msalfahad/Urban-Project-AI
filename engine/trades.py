"""Canonical trade registry.

trade_relevance feeds trade rules, then quantities, then a BOQ, then money. A
free-text trade label breaks that chain the first time someone writes "ceramic"
where the rules say ARCHITECTURAL_FLOOR_FINISH — so the vocabulary is a registry
with IDs, loaded from data, and a trade that is not in it does not exist.

An unrecognised trade is not an error in the drawing; it is OTHER plus a note,
so the work is still visible and someone can decide whether the registry needs a
new entry. New trades are added centrally, never invented in a prompt.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

REGISTRY_PATH = Path(__file__).resolve().parent.parent / "data/registry/trades.json"
UNKNOWN_TRADE = "OTHER"

# A trade whose applicability depends on a finish schedule or project rule that
# has not been supplied. Not a guess, not a default — a routed question.
RULE_REQUIRED = "RULE_REQUIRED"


class TradeError(ValueError):
    """A trade id that is not in the registry."""


@dataclass(frozen=True)
class Trade:
    trade_id: str
    display_name_ar: str
    display_name_en: str
    active: bool
    quantity_unit: str
    rule_set_id: str | None = None


@lru_cache(maxsize=1)
def registry(path: str | None = None) -> dict[str, Trade]:
    data = json.loads(Path(path or REGISTRY_PATH).read_text(encoding="utf-8"))
    return {t["trade_id"]: Trade(**t) for t in data["trades"]}


def registry_version(path: str | None = None) -> str:
    return json.loads(Path(path or REGISTRY_PATH).read_text(encoding="utf-8"))["registry_version"]


def is_trade(trade_id: str) -> bool:
    return trade_id in registry()


def resolve(trade_id: str) -> Trade:
    reg = registry()
    if trade_id not in reg:
        raise TradeError(
            f"{trade_id!r} is not a canonical trade. Use {UNKNOWN_TRADE} with a "
            f"trade_note, or add it to {REGISTRY_PATH.name}.")
    return reg[trade_id]


def validate_all(trade_ids: list[str]) -> None:
    for t in trade_ids:
        if t == RULE_REQUIRED:
            continue
        resolve(t)


# ------------------------------------------------------------ space aliases
ALIAS_PATH = Path(__file__).resolve().parent.parent / "data/registry/space_aliases.json"


@lru_cache(maxsize=1)
def _alias_index(path: str | None = None) -> tuple[dict[str, str], str]:
    data = json.loads(Path(path or ALIAS_PATH).read_text(encoding="utf-8"))
    idx: dict[str, str] = {}
    for label, terms in data["aliases"].items():
        for t in terms:
            idx[t.strip().upper()] = label
    return idx, data["alias_version"]


def alias_version() -> str:
    return _alias_index()[1]


def normalize_label(raw: str) -> str | None:
    """Map a raw drawing label onto a canonical semantic label, or None.

    Drawings say كوي, غرفة كوي, IRON, IRONING or UTILITY for the same room. The
    normalisation lives in data so a new spelling is a data edit, not a code
    change. The raw label is never destroyed — it stays on the record as
    original_drawing_label, because the word the engineer actually wrote is
    evidence and a normaliser can be wrong.

    Returns None when nothing matches, which is a finding rather than a default.
    """
    if not raw or not raw.strip():
        return None
    idx, _ = _alias_index()
    up = raw.strip().upper()
    if up in idx:
        return idx[up]
    # a label printed as "غرفة نوم BED ROOM" carries both languages
    hits = {lab for term, lab in idx.items() if term in up}
    return hits.pop() if len(hits) == 1 else None
