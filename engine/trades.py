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
import re
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

# Match modes, strongest first. There is deliberately no "substring" mode:
# "room" is inside BEDROOM, MAID_ROOM, IRON_ROOM and SERVICE_ROOM, and "hall"
# turns up inside unrelated prose. A matcher that returns the first hit on a
# fragment will be confidently wrong on a drawing nobody checks.
EXACT = "EXACT"            # the whole normalised string is the alias
TOKEN = "TOKEN"            # the alias appears as a complete word
PHRASE = "PHRASE"          # the alias appears as a complete word sequence
LEGACY_ONLY = "LEGACY_ONLY"  # kept for old records; never matches new input

UNKNOWN_LABEL = "UNKNOWN"
AMBIGUOUS_LABEL = "AMBIGUOUS"

_TASHKEEL = re.compile(r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]")
_PUNCT = re.compile(r"[.,;:()\[\]{}\-_/\\'\"«»]+")
_WS = re.compile(r"\s+")


def normalize_text(raw: str) -> str:
    """Normalise a drawing label for matching, without translating it.

    Arabic loses its diacritics and its alef/ya variants collapse, because the
    same room is written أ or ا or with tashkeel depending on who typed it. ة is
    deliberately left alone — it distinguishes real words and folding it was not
    tested on this project's vocabulary.
    """
    if not raw:
        return ""
    t = _TASHKEEL.sub("", raw)
    t = t.replace("\u0623", "\u0627").replace("\u0625", "\u0627").replace("\u0622", "\u0627")
    t = t.replace("\u0649", "\u064a")
    t = _PUNCT.sub(" ", t)
    t = _WS.sub(" ", t).strip().lower()
    return t


@dataclass(frozen=True)
class Alias:
    alias: str
    canonical_label: str
    language: str
    match_mode: str
    priority: int = 100

    @property
    def normalized(self) -> str:
        return normalize_text(self.alias)


@dataclass(frozen=True)
class LabelMatch:
    """How a raw label became a canonical one — the whole provenance."""

    input_text: str
    normalized_text: str
    canonical_label: str
    match_method: str
    confidence: str
    matched_alias: str = ""
    source: str = ""
    candidates: tuple[str, ...] = ()

    @property
    def resolved(self) -> bool:
        return self.canonical_label not in (UNKNOWN_LABEL, AMBIGUOUS_LABEL)


@lru_cache(maxsize=1)
def _aliases(path: str | None = None) -> tuple[tuple[Alias, ...], str]:
    data = json.loads(Path(path or ALIAS_PATH).read_text(encoding="utf-8"))
    out = []
    for entry in data["aliases"]:
        out.append(Alias(entry["alias"], entry["canonical_label"], entry["language"],
                         entry["match_mode"], entry.get("priority", 100)))
    return tuple(out), data["alias_version"]


def alias_version() -> str:
    return _aliases()[1]


def _tokens(text: str) -> list[str]:
    return [t for t in text.split(" ") if t]


def match_label(raw: str, *, source: str = "") -> LabelMatch:
    """Resolve a drawing label to a canonical one, or refuse.

    Exact beats token/phrase, and a tie between two DIFFERENT canonical labels is
    AMBIGUOUS rather than a coin flip. Zero matches is UNKNOWN. The first match
    is never simply taken.
    """
    norm = normalize_text(raw)
    if not norm:
        return LabelMatch(raw, norm, UNKNOWN_LABEL, "NO_INPUT", "VERY_LOW", source=source)

    aliases, _ = _aliases()
    live = [a for a in aliases if a.match_mode != LEGACY_ONLY]

    # Every live alias can match exactly; EXACT means "exactly and nothing else".
    exact = {a.canonical_label for a in live if a.normalized == norm}
    if len(exact) == 1:
        hit = next(a for a in live if a.normalized == norm)
        return LabelMatch(raw, norm, hit.canonical_label, "EXACT_ALIAS", "HIGH",
                          hit.alias, source)
    if len(exact) > 1:
        return LabelMatch(raw, norm, AMBIGUOUS_LABEL, "EXACT_ALIAS", "VERY_LOW",
                          source=source, candidates=tuple(sorted(exact)))

    toks = _tokens(norm)
    hits: dict[str, Alias] = {}
    for a in live:
        if a.match_mode not in (TOKEN, PHRASE):
            continue
        at = _tokens(a.normalized)
        if not at:
            continue
        # a complete word sequence, never an arbitrary character run
        found = any(toks[i:i + len(at)] == at for i in range(len(toks) - len(at) + 1))
        if found:
            prev = hits.get(a.canonical_label)
            if prev is None or a.priority < prev.priority:
                hits[a.canonical_label] = a
    if len(hits) == 1:
        label, a = next(iter(hits.items()))
        return LabelMatch(raw, norm, label, f"{a.match_mode}_ALIAS", "MEDIUM",
                          a.alias, source)
    if len(hits) > 1:
        return LabelMatch(raw, norm, AMBIGUOUS_LABEL, "TOKEN_ALIAS", "VERY_LOW",
                          source=source, candidates=tuple(sorted(hits)))
    return LabelMatch(raw, norm, UNKNOWN_LABEL, "NO_MATCH", "VERY_LOW", source=source)


def normalize_label(raw: str) -> str | None:
    """Back-compatible helper: the canonical label, or None if not resolved."""
    m = match_label(raw)
    return m.canonical_label if m.resolved else None
