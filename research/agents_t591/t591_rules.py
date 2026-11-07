"""T-591 RULE_DIFF provenance audit, architectural and finishes: the classification rule R-T591-1 (every villa).

A RULE_DIFFERENCE row in a reconciled statement says "both sides measured the same element; the gap is a convention".
That claim is only honest when OUR convention is a recorded Urban rule. This module decides, per row, whether it is.

R-T591-1 (proposed, every villa):
 (a) Accepted sources on OUR side, and only these: an engineering-knowledge / rule-store rule listed in
     docs/RULES_INDEX.md and not DEPRECATED; a company-rulebook record (rules/rulebook, UPC-*, OWNER_CONFIRMED); an
     owner method rule (data/registry/URBAN_OWNER_METHOD_RULES.json, URBAN-*); an ANSWERED and binding owner question
     (Q-nn); an owner rule / notes file on the board, named with its item; a BOQ family code of the versioned family
     master (placement only).
 (b) Refused as a source: an id that is in none of those registers; a DEPRECATED rule; an OPEN or WITHDRAWN owner
     question; an answered question whose answer is not a rule (cancelled, deferred, ignore); a scenario-only reading
     (e.g. Q-29 S1, project-specific); a worker method record (R-Txxx-n) or a Lead register ruling ALONE (they record
     how we measured, not the owner's convention).
 (c) A rule whose status is REQUIRES_CONFIRMATION or REFERENCE_ONLY counts, labelled PROVISIONAL, and is listed.
 (d) Outcome per row: SOURCED (cited in the row and valid), SOURCED_RECITE (valid source found by tracing, but the
     row cites none, cites only a method record, or cites a rule that does not govern that trade: the citation must be
     corrected, no number moves), NONE -> the row is reclassed UNRESOLVED with its delta unchanged (never 0, never
     dropped); the section's difference is unchanged and its classes re-add exactly.
 (e) His side: a convention read from his own figures only (non-empty); never from our rule.
 (f) Units stay apart: per-unit sums only (m2, lm, nr), no % anywhere.
"""
from __future__ import annotations

import json
import re
from decimal import Decimal
from pathlib import Path

D = Decimal
ROOT = Path(__file__).resolve().parents[2]


class ProvenanceError(ValueError):
    """A provenance claim the rule refuses."""


# --------------------------------------------------------------------------------------------- registers --------
# Owner questions: the board's index (OWNER_QUESTIONS.md, agents/control @189683b3, read 2026-11-07T08:40Z). The board
# is not in the engine tree, so the snapshot is pinned here; a later answer changes this table in a new version.
Q_ANSWERED = {f"Q-{n:02d}" for n in range(1, 79)}
Q_NOT_A_RULE = {"Q-23": "cancelled by the owner", "Q-34": "deferred ('ask me later'): HELD until a milestone",
                "Q-36": "ignore (a Drive folder, not a rule)"}
Q_OPEN = {"Q-80"}
Q_WITHDRAWN = {"Q-79"}
Q_SCENARIO_ONLY = {"Q-29": "the skylight reading is scenario S1 only (owner 2026-10-22): the approved design keeps "
                           "the three concrete domes; project-specific"}
OWNER_FILES = {
    "OWNER_NOTES_SIGMA_2026-10-21": {"item 1", "item 2", "item 3", "item 4"},
    "OWNER_RULE_OUTDOOR_FLOORS_2026-10-21": {"all"},
    "OWNER_RULE_STAIRS_2026-10-21": {"all"},
    "OWNER_RULE_STAIRS_2026-10-24": {"all"},
    "OWNER_RULE_REBAR_2026-10-24": {"all"},
}
RE_ID = re.compile(r"\b(Q-\d{2}|UPC-[A-Z0-9-]+-\d{3}|UP-[A-Z0-9-]+-\d{3}|PS-[A-Z0-9-]+-\d{3}|URBAN-[A-Z0-9-]+|"
                   r"R-T\d{3}-\d+)\b")
STATUS_PROVISIONAL = {"REQUIRES_CONFIRMATION", "REFERENCE_ONLY"}


def rules_index(path: Path | None = None) -> dict[str, str]:
    """rule id -> status, from the generated docs/RULES_INDEX.md (knowledge rules: their status column; rule-store
    rows: RULE_STORE_<MANDATORY|DEFAULT>). A rule in both keeps the knowledge status."""
    text = (path or ROOT / "docs" / "RULES_INDEX.md").read_text(encoding="utf-8")
    out: dict[str, str] = {}
    section = ""
    for line in text.splitlines():
        if line.startswith("## "):
            section = line
            continue
        m = re.match(r"^\| ((?:UP|PS)-[A-Z0-9-]+-\d{3}) \|(.*)$", line)
        if not m:
            continue
        cells = [c.strip() for c in m.group(2).split("|")]
        if section.startswith("## Engineering knowledge"):
            out[m.group(1)] = cells[1]
        elif section.startswith("## Rule store"):
            out.setdefault(m.group(1), "RULE_STORE_" + cells[4])
    return out


def rulebook(path: Path | None = None) -> dict[str, str]:
    d = json.loads((path or ROOT / "rules" / "rulebook" / "URBAN_COMPANY_RULEBOOK_1.0.0.json").read_text("utf-8"))
    out: dict[str, str] = {}

    def walk(o):
        if isinstance(o, dict):
            rid = o.get("rule_id") or o.get("id")
            if isinstance(rid, str) and rid.startswith("UPC-"):
                out[rid] = str(o.get("status") or "")
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(d)
    return out


def owner_methods(path: Path | None = None) -> set[str]:
    d = json.loads((path or ROOT / "data" / "registry" / "URBAN_OWNER_METHOD_RULES.json").read_text("utf-8"))
    return {r["rule_id"] for r in d["rules"]}


def family_codes(path: Path | None = None) -> set[str]:
    p = path or ROOT / "rules" / "coverage" / "BOQ_FAMILY_MASTER_1.55.0.json"
    return set(re.findall(r'"([A-Z]{2,5}(?:\.[A-Z0-9_]+){1,4})"', p.read_text(encoding="utf-8")))


class Registers:
    def __init__(self, rules=None, book=None, methods=None, families=None):
        self.rules = rules if rules is not None else rules_index()
        self.book = book if book is not None else rulebook()
        self.methods = methods if methods is not None else owner_methods()
        self.families = families if families is not None else family_codes()

    def judge(self, src: str) -> tuple[str, str]:
        """One source string -> (kind, status). Raises ProvenanceError when the rule refuses it as a source.
        Forms: 'UP-...', 'UPC-...', 'URBAN-...', 'Q-nn', 'OWNER_FILE:<name>#<item>', 'FAMILY:<code>',
        'R-Txxx-n' and 'REGISTER:<entry>' (accepted only as companions, never alone: see classify)."""
        if src.startswith("OWNER_FILE:"):
            name, _, item = src[len("OWNER_FILE:"):].partition("#")
            items = OWNER_FILES.get(name)
            if items is None or not (item in items or "all" in items):
                raise ProvenanceError(f"{src}: not an owner rule / notes file with that item")
            return "OWNER_FILE", "OWNER"
        if src.startswith("FAMILY:"):
            code = src[len("FAMILY:"):]
            if code not in self.families:
                raise ProvenanceError(f"{src}: not a family code of the family master")
            return "FAMILY", "PLACEMENT"
        if src.startswith("REGISTER:"):
            return "REGISTER", "LEAD_RULING"
        if re.fullmatch(r"R-T\d{3}-\d+", src):
            return "METHOD_RECORD", "WORKER"
        if src.startswith("Q-"):
            if src in Q_OPEN:
                raise ProvenanceError(f"{src}: OPEN owner question cited as a rule")
            if src in Q_WITHDRAWN:
                raise ProvenanceError(f"{src}: WITHDRAWN owner question cited as a rule")
            if src in Q_NOT_A_RULE:
                raise ProvenanceError(f"{src}: answered, but the answer is not a rule ({Q_NOT_A_RULE[src]})")
            if src in Q_SCENARIO_ONLY:
                return "Q_SCENARIO", "SCENARIO_ONLY"
            if src not in Q_ANSWERED:
                raise ProvenanceError(f"{src}: not an answered owner question")
            return "Q", "ANSWERED"
        if src.startswith("UPC-"):
            st = self.book.get(src)
            if st is None:
                raise ProvenanceError(f"{src}: not in the company rulebook")
            if st != "OWNER_CONFIRMED":
                return "RULEBOOK", "PROVISIONAL:" + st
            return "RULEBOOK", st
        if src.startswith("URBAN-"):
            if src not in self.methods:
                raise ProvenanceError(f"{src}: not an owner method rule")
            return "OWNER_METHOD", "OWNER"
        if re.fullmatch(r"(UP|PS)-[A-Z0-9-]+-\d{3}", src):
            st = self.rules.get(src)
            if st is None:
                raise ProvenanceError(f"{src}: not in docs/RULES_INDEX.md")
            if st == "DEPRECATED":
                raise ProvenanceError(f"{src}: DEPRECATED rule cited as a source")
            if st in STATUS_PROVISIONAL:
                return "RULE", "PROVISIONAL:" + st
            return "RULE", st
        raise ProvenanceError(f"{src}: unknown source form")


def cited_ids(row: dict) -> list[str]:
    """Rule-like ids the row's own text cites (name, note, source, reclass reason), in order, unique."""
    text = " ".join(str(row.get(k, "")) for k in ("name", "note", "source"))
    for k in ("reclass_t579",):
        if isinstance(row.get(k), dict):
            text += " " + str(row[k].get("why", ""))
    seen: list[str] = []
    for m in RE_ID.findall(text):
        if m not in seen:
            seen.append(m)
    return seen


RULE_KINDS = {"RULE", "RULEBOOK", "OWNER_METHOD", "Q", "OWNER_FILE", "FAMILY"}


def classify(reg: Registers, row: dict, traced: list[str], his: str, miscited: dict | None = None) -> dict:
    """One RULE_DIFFERENCE row -> its provenance record. `traced` are the sources the auditor found to govern the
    cause (each judged); `miscited` maps a cited id to why it does not govern this cause."""
    if row.get("class") != "RULE_DIFFERENCE":
        raise ProvenanceError("only a RULE_DIFFERENCE row is audited")
    if not his or not his.strip():
        raise ProvenanceError("his convention missing (read it from his own figures)")
    miscited = miscited or {}
    judged = []
    for s in traced:
        kind, status = reg.judge(s)          # raises on a refused source
        judged.append({"source": s, "kind": kind, "status": status})
    rule_ok = [j for j in judged if j["kind"] in RULE_KINDS]
    cited = cited_ids(row)
    cited_valid = []
    cited_bad = {}
    for c in cited:
        if c in miscited:
            cited_bad[c] = miscited[c]
            continue
        try:
            kind, status = reg.judge(c)
        except ProvenanceError as e:
            cited_bad[c] = str(e)
            continue
        if kind in RULE_KINDS and c in traced:
            cited_valid.append(c)
    provisional = bool(rule_ok) and all(j["status"].startswith("PROVISIONAL") for j in rule_ok)
    if not rule_ok:
        outcome = "NONE"
    elif cited_valid and not cited_bad:
        outcome = "SOURCED"
    else:
        outcome = "SOURCED_RECITE"
    return {"outcome": outcome, "provisional": provisional, "sources": judged, "cited_in_row": cited,
            "cited_valid": cited_valid, "cited_not_governing": cited_bad, "his_convention": his.strip(),
            "class_after": "UNRESOLVED" if outcome == "NONE" else "RULE_DIFFERENCE"}


def reclass_section(rows: list[dict], records: dict[int, dict]) -> dict:
    """Apply NONE -> UNRESOLVED on a copy of a section's rows; return by-class sums before / after and assert the
    section difference is unchanged (each row keeps its delta; a reclassed row is never 0)."""
    before: dict[str, D] = {}
    after: dict[str, D] = {}
    for i, r in enumerate(rows):
        c0 = r["class"]
        c1 = records[i]["class_after"] if i in records else c0
        d = D(str(r["delta"]))
        before[c0] = before.get(c0, D(0)) + d
        after[c1] = after.get(c1, D(0)) + d
    if sum(before.values(), D(0)) != sum(after.values(), D(0)):
        raise ProvenanceError("section difference changed by a reclass")
    return {"before": before, "after": after}


def per_unit(items: list[tuple[str, str, D]]) -> dict:
    """(unit, outcome, delta) -> {unit: {outcome: {'n', 'signed', 'gross'}}}; units never mixed."""
    out: dict = {}
    for unit, outcome, d in items:
        if unit not in {"m2", "lm", "nr", "m3", "t"}:
            raise ProvenanceError(f"unknown unit {unit}")
        b = out.setdefault(unit, {}).setdefault(outcome, {"n": 0, "signed": D(0), "gross": D(0)})
        b["n"] += 1
        b["signed"] += d
        b["gross"] += abs(d)
    return out
