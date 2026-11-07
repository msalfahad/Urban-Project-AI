"""T-590 RULE_DIFF provenance audit, structural (B10 concrete, B11 reinforcement, B1 earthworks): rule R-T590-1.

R-T590-1 (proposed, every villa) = R-T591-1 (research/agents_t591/t591_rules.py, merged, read only) plus four clauses
that the structural rows need:

 (g) METHOD REGISTER. A method of the versioned Urban method register (rules/methods/URBAN_METHOD_REGISTER_V3.json, an
     `id` with an owner decision `OD-*`) is an accepted source on our side (kind METHOD_REGISTER). An id that is not in
     the register is refused.
 (h) REQUIREMENT ONLY. An owner rule that REQUIRES a property of every convention without choosing the convention
     (e.g. Q-62: 'the same concrete is measured once ... assign it under the chosen convention ... one convention for
     the whole project') is valid but does not source a CHOICE between two conventions that both satisfy it. Such a
     source is recorded with kind REQUIREMENT and does not count as a rule for the row.
 (i) CHOICE RECORD. The choice itself is sourced only by an accepted rule (R-T591-1 (a) or (g)). A choice recorded only
     in worker method records or Lead registers is NONE (R-T591-1 (b)); where two Lead / worker records state OPPOSITE
     choices for the same junction the row also carries CONVENTION_RECORD_CONFLICT (the owner's 'one convention for
     the whole project' is then not even established in the records).
 (j) HIS SIDE NOT READABLE. A RULE_DIFFERENCE needs a convention read from his own figures. A reference that is a
     TYPED_LUMP (a typed constant with no formula and no row of its own) shows no convention: the row is reclassed
     UNRESOLVED with reason HIS_SIDE_UNREADABLE whatever our side is (our side is still recorded). Never 0, delta
     unchanged.

Outcomes per row: SOURCED, SOURCED_RECITE (R-T591-1 (d)), NONE (-> UNRESOLVED), HIS_SIDE_UNREADABLE (-> UNRESOLVED).
Per-unit sums only; a section NESTED in another section (a measured subset of the same members) is reported beside and
never added to the parent's unit total (one physical joint counted once in the audit totals too).
"""
from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "research" / "agents_t591"))
import t591_rules as R591  # noqa: E402  (merged T-591, read only)

D = Decimal
ProvenanceError = R591.ProvenanceError
RULE_KINDS = set(R591.RULE_KINDS) | {"METHOD_REGISTER"}
OUTCOMES = ("SOURCED", "SOURCED_RECITE", "NONE", "HIS_SIDE_UNREADABLE")


def method_register(path: Path | None = None) -> dict[str, str]:
    """method id -> owner decision id, from the versioned method register."""
    d = json.loads((path or ROOT / "rules" / "methods" / "URBAN_METHOD_REGISTER_V3.json").read_text("utf-8"))
    return {m["id"]: str(m.get("decision") or "") for m in d["methods"]}


class Registers(R591.Registers):
    def __init__(self, rules=None, book=None, methods=None, families=None, method_reg=None, requirement_only=None):
        super().__init__(rules=rules, book=book, methods=methods, families=families)
        self.method_reg = method_reg if method_reg is not None else method_register()
        # source -> what it requires (clause (h)); the source itself must still pass judge()
        self.requirement_only = dict(requirement_only or {})

    def judge(self, src: str) -> tuple[str, str]:
        if "@v" in src and src.startswith("URBAN-"):
            dec = self.method_reg.get(src)
            if dec is None:
                raise ProvenanceError(f"{src}: not in the Urban method register")
            if not dec.startswith("OD-"):
                raise ProvenanceError(f"{src}: method register entry without an owner decision")
            return "METHOD_REGISTER", "OWNER_DECISION:" + dec
        kind, status = super().judge(src)
        if src in self.requirement_only:
            return "REQUIREMENT", status
        return kind, status


def classify(reg: Registers, row: dict, traced: list[str], his: str | None, *, his_readable: bool = True,
             miscited: dict | None = None, conflict: str | None = None) -> dict:
    """One RULE_DIFFERENCE row -> its provenance record (R-T590-1)."""
    if row.get("class") != "RULE_DIFFERENCE":
        raise ProvenanceError("only a RULE_DIFFERENCE row is audited")
    if his_readable and (not his or not his.strip()):
        raise ProvenanceError("his convention missing (read it from his own figures, or mark his side unreadable)")
    if not his_readable and not (his and his.strip()):
        raise ProvenanceError("an unreadable his side still states what his reference is (e.g. a typed lump)")
    miscited = miscited or {}
    judged = []
    for s in traced:
        kind, status = reg.judge(s)                       # raises on a refused source
        judged.append({"source": s, "kind": kind, "status": status})
    rule_ok = [j for j in judged if j["kind"] in RULE_KINDS]
    cited = R591.cited_ids(row)
    cited_valid, cited_bad = [], {}
    for c in cited:
        if c in miscited:
            cited_bad[c] = miscited[c]
            continue
        try:
            kind, _ = reg.judge(c)
        except ProvenanceError as e:
            cited_bad[c] = str(e)
            continue
        if kind in RULE_KINDS and c in traced:
            cited_valid.append(c)
        elif kind in ("METHOD_RECORD", "REGISTER"):
            cited_bad[c] = "a worker method record / Lead register ruling: records how we measured, not a rule"
    if not rule_ok:
        our = "NONE"
    elif cited_valid and not cited_bad:
        our = "SOURCED"
    else:
        our = "SOURCED_RECITE"
    outcome = our if his_readable else "HIS_SIDE_UNREADABLE"
    provisional = bool(rule_ok) and all(j["status"].startswith("PROVISIONAL") for j in rule_ok)
    reclass = outcome in ("NONE", "HIS_SIDE_UNREADABLE")
    return {"outcome": outcome, "our_side_outcome": our, "provisional": provisional, "sources": judged,
            "requirements": [j for j in judged if j["kind"] == "REQUIREMENT"],
            "cited_in_row": cited, "cited_valid": cited_valid, "cited_not_governing": cited_bad,
            "his_convention": (his or "").strip(), "his_readable": his_readable,
            "convention_record_conflict": conflict,
            "class_after": "UNRESOLVED" if reclass else "RULE_DIFFERENCE"}


def reclass_section(rows: list[dict], records: dict[int, dict]) -> dict:
    return R591.reclass_section(rows, records)


def per_unit(items: list[tuple[str, str, D]]) -> dict:
    for _, oc, _ in items:
        if oc not in OUTCOMES:
            raise ProvenanceError(f"unknown outcome {oc}")
    return R591.per_unit(items)

