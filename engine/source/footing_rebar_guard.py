"""FOOTING_REBAR_GUARD (pre-S4) - what Accurate Footing Rebar (S4) may consume, and how it fails closed.

No kg and no bar lengths. These are the gates S4 calls before it computes anything:

1. TOKEN PARITY   admit_token(raw) / admit_cells(count, dia)
       Every bar token is put in one TOKEN CLASS. Each class has ONE parser route (ROUTES) and a list of every
       Urban parser that accepts that class (APPLICABLE). The three parsers are not unified here:
           schedule_grammar.parse_bar   structural_schedule.bar_spec   slab_rebar_binding.parse
       (and schedule_grammar.bar_from_cells for split count / diameter cells).
       S4 may consume a token only when its class has a route and the class is not one where the parsers are
       known to disagree (KNOWN_DISAGREEMENT_CLASSES, from the R9.1 corpus). Every applicable parser is re-run
       live, and they must give the same normalised form. Anything else is FAIL_CLOSED.
       A BOXED pair ("3+4") is never a bar token: it has no route and ends BLOCKED_SEMANTICS.
2. CONSERVATION   Census
       Every footing-source item (schedule cells, rows and headers, plan tags, outlines, notes and details) is
       admitted once and terminates once, in one of TERMINALS. A BLOCKED item never carries a zero quantity.
       Built on terminal_ledger.
3. OCCURRENCE TERMINALS   occurrence_terminals(...)
       Maps the plan-mark rows of structural_schedule.footing_occurrences to terminals, and adds the outline side
       that function does not report: an outline that holds no mark is OUTLINE_WITHOUT_TAG. A count query raised
       by review on a type (one that names a question, never a quantity) makes every occurrence of the type an
       OCCURRENCE_COUNT_CONFLICT. The plan count is kept, and the conflict survives into the release state.
4. HEADER BINDING   header_binding(...)
       A schedule value belongs to the column header it is DRAWN under (schedule_table). The binding derived from
       the drawn header is compared with the adapter's fixed tag -> field table. A difference is a
       HEADER_BINDING_CONFLICT, never a silent column swap.
5. BOXED / RELEASE   boxed_part(...) / footing_release(...)
       A component whose semantics are not SOURCE_EXPLICIT or SOURCE_DERIVED_HIGH_CONFIDENCE becomes
       BLOCKED_UNQUANTIFIED. The footing is released as REBAR_LOWER_BOUND with that component listed. One
       unresolved component never blocks the whole footing; an occurrence-level conflict does.

Project-agnostic; stdlib + engine.source only.
"""

from __future__ import annotations

import re
from collections import Counter

from engine.source import accurate_boq_rebar as AR
from engine.source import schedule_grammar as SG
from engine.source import slab_rebar_binding as SRB
from engine.source import structural_schedule as SS
from engine.source import terminal_ledger as TL

POLICY_ID = "FOOTING_REBAR_GUARD_V1"

# ------------------------------------------------------------------ 1. token parity
EMPTY = "EMPTY"
BOXED_PAIR = "BOXED_PAIR"
SPLIT_CELLS = "COUNT_DIA_SPLIT_CELLS"
SPLIT_CELLS_PER_M = "COUNT_DIA_SPLIT_CELLS_PER_M"
COUNT_DIA = "COUNT_DIA"
COUNT_DIA_PER_M = "COUNT_DIA_PER_M"
COUNT_DIA_POSITION = "COUNT_DIA_POSITION"
DIA_AT_SPACING = "DIA_AT_SPACING"
COUNT_DIA_AT_SPACING = "COUNT_DIA_AT_SPACING"
SENTENCE_EMBEDDED = "BAR_IN_SENTENCE"
LAYER_LABEL = "LAYER_LABEL"
UNSUPPORTED = "UNSUPPORTED"
TOKEN_CLASSES = (EMPTY, BOXED_PAIR, SPLIT_CELLS, SPLIT_CELLS_PER_M, COUNT_DIA, COUNT_DIA_PER_M, COUNT_DIA_POSITION,
                 DIA_AT_SPACING, COUNT_DIA_AT_SPACING, SENTENCE_EMBEDDED, LAYER_LABEL, UNSUPPORTED)

P_PARSE_BAR = "schedule_grammar.parse_bar"
P_CELLS = "schedule_grammar.bar_from_cells"
P_BAR_SPEC = "structural_schedule.bar_spec"
P_SLAB = "slab_rebar_binding.parse"

# the one route S4 uses per class (None = no route: the class is never a bar quantity)
ROUTES = {EMPTY: None, BOXED_PAIR: None, LAYER_LABEL: None, UNSUPPORTED: None,
          SPLIT_CELLS: P_CELLS, SPLIT_CELLS_PER_M: P_CELLS,
          COUNT_DIA: P_PARSE_BAR, COUNT_DIA_PER_M: P_PARSE_BAR, COUNT_DIA_POSITION: P_PARSE_BAR,
          DIA_AT_SPACING: P_PARSE_BAR, COUNT_DIA_AT_SPACING: P_PARSE_BAR, SENTENCE_EMBEDDED: None}
# every Urban parser that ACCEPTS the class (all of them are re-run; they must agree)
APPLICABLE = {SPLIT_CELLS: (P_CELLS,), SPLIT_CELLS_PER_M: (P_CELLS,),
              COUNT_DIA: (P_PARSE_BAR, P_BAR_SPEC, P_SLAB), COUNT_DIA_PER_M: (P_PARSE_BAR, P_BAR_SPEC, P_SLAB),
              COUNT_DIA_POSITION: (P_PARSE_BAR, P_SLAB), DIA_AT_SPACING: (P_PARSE_BAR, P_BAR_SPEC, P_SLAB),
              COUNT_DIA_AT_SPACING: (P_PARSE_BAR, P_BAR_SPEC, P_SLAB),
              SENTENCE_EMBEDDED: (P_PARSE_BAR, P_BAR_SPEC, P_SLAB)}
# classes on which the Urban parsers split (R9.1 11_REBAR_TOKEN_CORPUS: 6 patterns, 52 rows). S4 fails closed on
# them even when one parser happens to read a token: the split is in the class, not the token.
KNOWN_DISAGREEMENT_CLASSES = {
    DIA_AT_SPACING: "only parse_bar reads a diameter at a spacing; bar_spec and slab parse reject it",
    COUNT_DIA_AT_SPACING: "bar_spec drops the spacing; slab parse rejects the token",
    SENTENCE_EMBEDDED: "a bar inside a note / sentence: bar_spec finds it, parse_bar and slab parse reject it",
}
ADMITTED, FAIL_CLOSED = "ADMITTED", "FAIL_CLOSED"

_RE_BOXED = re.compile(r"^\s*\d+\s*\+\s*\d+\s*$")
_RE_LAYER = re.compile(r"^\s*(TOP|BOT|BOTTOM)\s*$", re.I)
_RE_BAR_ANY = re.compile(r"\d*\s*Ø\s*\d+", re.I)


def token_class(raw) -> str:
    """The class of one single-text token (CAD codes normalised first)."""
    n = SG.normalise(raw)
    if not n:
        return EMPTY
    if _RE_BOXED.match(n):
        return BOXED_PAIR
    if _RE_LAYER.match(n):
        return LAYER_LABEL
    g = SG.parse_bar(n)["grammar"]
    if g in (COUNT_DIA, COUNT_DIA_PER_M, COUNT_DIA_POSITION, DIA_AT_SPACING, COUNT_DIA_AT_SPACING):
        return g
    if _RE_BAR_ANY.search(n):
        return SENTENCE_EMBEDDED
    return UNSUPPORTED


def _norm(count, dia, per_m=False, spacing=None, position=None):
    return {"count": count, "dia_mm": dia, "per_m": bool(per_m), "spacing_cm": spacing, "position": position}


def _run(parser, raw):
    """One parser on one token -> a normalised form, or None (the parser rejects the token)."""
    if parser == P_PARSE_BAR:
        r = SG.parse_bar(raw)
        if r["grammar"] == "UNPARSED":
            return None
        return _norm(r["count"], r["dia_mm"], r["per_m"], r["spacing_cm"], r["position"])
    if parser == P_BAR_SPEC:
        r = SS.bar_spec(raw)
        if len(r) != 1:
            return None if not r else {"multiple": [_norm(x["count"], x["dia_mm"], x["per_m"]) for x in r]}
        return _norm(r[0]["count"], r[0]["dia_mm"], r[0]["per_m"])
    if parser == P_SLAB:
        r = SRB.parse(raw)
        if r is None:
            return None
        return _norm(r["n"], r["dia_mm"], r["kind"] == "PER_M", None, "TOP" if r["top"] else None)
    raise ValueError(f"unknown parser {parser}")


def _compare(outputs):
    """Field-wise agreement of the accepting parsers; a field a parser cannot express (None) is a disagreement
    unless every parser leaves it None."""
    acc = {k: v for k, v in outputs.items() if v is not None}
    rej = sorted(k for k, v in outputs.items() if v is None)
    if not acc:
        return False, "ALL_APPLICABLE_PARSERS_REJECT", rej
    if rej:
        return False, f"SPLIT: rejected by {rej}", rej
    forms = {repr(sorted(v.items())) for v in acc.values()}
    if len(forms) > 1:
        return False, "VALUES_DIFFER", rej
    return True, "ALL_APPLICABLE_PARSERS_AGREE", rej


def admit_token(raw) -> dict:
    """Admission of one single-text token for S4."""
    cls = token_class(raw)
    route = ROUTES[cls]
    out = {"raw": raw, "normalised": SG.normalise(raw), "token_class": cls, "route": route,
           "parsers": {}, "parity": None, "decision": FAIL_CLOSED, "form": None, "reason": None}
    if cls == BOXED_PAIR:
        out["reason"] = "BLOCKED_SEMANTICS: a boxed pair is not a bar token (no parser may read it)"
        return out
    if route is None:
        out["reason"] = {EMPTY: "EMPTY_CELL", LAYER_LABEL: "NOT_REBAR: layer label",
                         SENTENCE_EMBEDDED: "KNOWN_DISAGREEMENT_CLASS: " + KNOWN_DISAGREEMENT_CLASSES.get(cls, ""),
                         UNSUPPORTED: "UNSUPPORTED_TOKEN: no grammar"}[cls]
        out["parsers"] = {p: _run(p, raw) for p in APPLICABLE.get(cls, ())}
        return out
    outs = {p: _run(p, raw) for p in APPLICABLE[cls]}
    ok, why, _ = _compare(outs)
    out["parsers"], out["parity"] = outs, why
    if cls in KNOWN_DISAGREEMENT_CLASSES:
        out["reason"] = "KNOWN_DISAGREEMENT_CLASS: " + KNOWN_DISAGREEMENT_CLASSES[cls]
        return out
    if not ok:
        out["reason"] = f"LIVE_PARSER_DISAGREEMENT: {why}"
        return out
    out.update(decision=ADMITTED, form=outs[route], reason="route defined; all applicable parsers agree")
    return out


def admit_cells(count_raw, dia_raw) -> dict:
    """Admission of a bar split over a count cell and a diameter cell (schedule ATTRIBs)."""
    c, d = SG.normalise(count_raw), SG.normalise(dia_raw)
    out = {"raw": [count_raw, dia_raw], "token_class": None, "route": P_CELLS, "parsers": {}, "parity": None,
           "decision": FAIL_CLOSED, "form": None, "reason": None}
    if not c and not d:
        out.update(token_class=EMPTY, route=None, reason="EMPTY_CELL")
        return out
    r = SG.bar_from_cells(count_raw, dia_raw)
    out["token_class"] = SPLIT_CELLS_PER_M if r.get("per_m") else SPLIT_CELLS
    if r["grammar"] in ("UNPARSED", "EMPTY") or r.get("count") is None:
        out.update(token_class=UNSUPPORTED, parsers={P_CELLS: None}, parity="ALL_APPLICABLE_PARSERS_REJECT",
                   reason="UNREADABLE: the cell pair is not count + diameter")
        return out
    form = _norm(r["count"], r["dia_mm"], r["per_m"])
    out.update(parsers={P_CELLS: form}, parity="ALL_APPLICABLE_PARSERS_AGREE", decision=ADMITTED, form=form,
               reason="route defined (bar_from_cells is the only parser for split cells)")
    return out


def joined_form(count_raw, dia_raw) -> str:
    """The single-text form of a split-cell bar (for the parity register only, never a quantity route)."""
    c, d = SG.normalise(count_raw), SG.normalise(dia_raw)
    return f"{c}Ø{d}"


# ------------------------------------------------------------------ 2. conservation census
PARSED_BOUND = "PARSED_BOUND"
PARSED_SOURCE_CONFLICT = "PARSED_SOURCE_CONFLICT"
PARSED_AMBIGUOUS = "PARSED_AMBIGUOUS"
NOT_REBAR = "NOT_REBAR"
DUPLICATE_SOURCE = "DUPLICATE_SOURCE"
BLOCKED_SEMANTICS = "BLOCKED_SEMANTICS"
BLOCKED_GEOMETRY = "BLOCKED_GEOMETRY"
UNREADABLE = "UNREADABLE"
UNSUPPORTED_TOKEN = "UNSUPPORTED_TOKEN"
TERMINALS = (PARSED_BOUND, PARSED_SOURCE_CONFLICT, PARSED_AMBIGUOUS, NOT_REBAR, DUPLICATE_SOURCE, BLOCKED_SEMANTICS,
             BLOCKED_GEOMETRY, UNREADABLE, UNSUPPORTED_TOKEN)
BLOCKED_TERMINALS = (PARSED_SOURCE_CONFLICT, PARSED_AMBIGUOUS, BLOCKED_SEMANTICS, BLOCKED_GEOMETRY, UNREADABLE,
                     UNSUPPORTED_TOKEN)


class GuardError(ValueError):
    pass


class Census:
    """Footing-source conservation: SOURCE_ITEMS == TERMINAL_ITEMS, each item exactly once, and a blocked item
    never carries a quantity (not even zero)."""

    def __init__(self):
        self._led = TL.Ledger()
        self._qty = {}

    def admit(self, item_id, item_type, source_ref, **extra):
        self._led.admit(item_id, item_type, source_ref, **extra)

    def terminate(self, item_id, terminal, reason, *, quantity=None, consumer=None, **extra):
        if terminal not in TERMINALS:
            raise GuardError(f"{item_id}: terminal {terminal} is not one of {TERMINALS}")
        if terminal in BLOCKED_TERMINALS and quantity is not None:
            raise GuardError(f"{item_id}: a {terminal} item carries no quantity (got {quantity!r}); blocked is never "
                             "zero")
        self._qty[item_id] = quantity
        self._led.terminate(item_id, terminal, "BLOCKED" if terminal in BLOCKED_TERMINALS else "RESOLVED",
                            blocking_reason=reason if terminal in BLOCKED_TERMINALS else None,
                            downstream_trade=consumer, reason=reason, **extra)

    def rows(self):
        return self._led.rows()

    def check(self) -> dict:
        c = self._led.check()
        c["source_items"] = c["admitted"]
        c["terminal_items"] = c["terminated"]
        c["blocked_with_quantity"] = sorted(k for k, q in self._qty.items() if q is not None and any(
            r["object_id"] == k and r["terminal_state"] in BLOCKED_TERMINALS for r in self._led.rows()))
        c["conserved"] = c["conserved"] and c["source_items"] == c["terminal_items"] and not c["blocked_with_quantity"]
        return c


# ------------------------------------------------------------------ 3. occurrence terminals
OUTLINE_WITHOUT_TAG = "OUTLINE_WITHOUT_TAG"
TAG_WITHOUT_OUTLINE = "TAG_WITHOUT_OUTLINE"
OCCURRENCE_COUNT_CONFLICT = "OCCURRENCE_COUNT_CONFLICT"
OCC_RELEASED, OCC_PROVISIONAL, OCC_BLOCKED = "OCCURRENCE_ESTABLISHED", "OCCURRENCE_PROVISIONAL", "OCCURRENCE_BLOCKED"


def occurrence_terminals(result, outlines, *, count_queries=None) -> dict:
    """result: structural_schedule.footing_occurrences(...) output; outlines: the candidate outlines passed to it
    ([{"id", ...}]); count_queries {type: question_id} - a review record naming a disputed count. It carries a
    question, never a number, so no external count can enter.
    Returns {"marks": [...], "outlines": [...]}: one terminal per mark and one per outline."""
    count_queries = count_queries or {}
    for t, q in count_queries.items():
        if not isinstance(q, str) or not q.strip() or re.fullmatch(r"\s*[\d.]+\s*", q):
            raise GuardError(f"count query for {t} must be a question id, never a count ({q!r})")
    marks = []
    for r in result["rows"]:
        st = r["geometry_state"]
        if st in SS.COMPUTED_STATES:
            term, occ = PARSED_BOUND, OCC_RELEASED
        elif st == SS.COMBINED:
            term, occ = PARSED_SOURCE_CONFLICT, OCC_BLOCKED
        elif st == SS.DRAWN_SIZE:
            term, occ = PARSED_SOURCE_CONFLICT, OCC_BLOCKED
        elif st == SS.UNBOUND:
            term, occ = BLOCKED_GEOMETRY, OCC_BLOCKED
        else:  # TYPE_NOT_IN_SCHEDULE
            term, occ = BLOCKED_SEMANTICS, OCC_BLOCKED
        row = {"mark_key": r["mark_key"], "type": r["type"], "geometry_state": st, "terminal": term,
               "occurrence_state": occ, "why": r.get("why"), "issues": [],
               "hypotheses": None}
        if st == SS.UNBOUND:
            row["issues"].append(TAG_WITHOUT_OUTLINE)
        if st == SS.COMBINED:
            # the conflict carries its hypotheses; no mark is chosen by distance or order
            row["hypotheses"] = {"tags_in_outline": sorted([r["mark_value"]] + [
                x["mark_value"] for x in result["rows"] if x["mark_key"] in r.get("shared_with", [])]),
                "drawn_outline_mm": r["geometry"]["drawn_mm"]}
        if r["type"] in count_queries and occ == OCC_RELEASED:
            row["issues"].append(OCCURRENCE_COUNT_CONFLICT)
            row["count_query"] = count_queries[r["type"]]
            row["occurrence_state"] = OCC_PROVISIONAL
        marks.append(row)
    outs = []
    for o in sorted(outlines, key=lambda z: z["id"]):
        holders = sorted(k for k, v in result.get("bindings", {}).items() if v == o["id"])
        if not holders:
            outs.append({"outline": o["id"], "terminal": BLOCKED_SEMANTICS, "issues": [OUTLINE_WITHOUT_TAG],
                         "why": "drawn footing outline with no mark: measured, type unresolved", "marks": []})
        elif len(holders) > 1:
            outs.append({"outline": o["id"], "terminal": PARSED_SOURCE_CONFLICT, "issues": ["COMBINED_OUTLINE"],
                         "why": f"{len(holders)} marks in one outline", "marks": holders})
        else:
            m = next(x for x in marks if x["mark_key"] == holders[0])
            outs.append({"outline": o["id"], "terminal": m["terminal"], "issues": list(m["issues"]),
                         "why": "bound to one mark", "marks": holders})
    return {"marks": marks, "outlines": outs,
            "summary": {"marks": len(marks), "outlines": len(outs),
                        "by_mark_terminal": dict(sorted(Counter(m["terminal"] for m in marks).items())),
                        "by_outline_terminal": dict(sorted(Counter(o["terminal"] for o in outs).items()))}}


# ------------------------------------------------------------------ 4. header binding
HEADER_BINDING_CONFLICT = "HEADER_BINDING_CONFLICT"


def header_binding(table, header_bands, data_band, fixed) -> dict:
    """table: schedule_table.read(...); header_bands: indices of the header bands; data_band: one data band.
    fixed {attribute tag: expected header label}: the adapter's table. For each attribute value in the data band,
    the binding is the header path of the leaf column it is DRAWN in. Returns per-tag bindings and conflicts."""
    from engine.source import schedule_table as ST
    leaves = ST.header_paths(table, header_bands)
    rec = ST.record(table, data_band, leaves)
    derived = {}
    for leaf in rec:
        for tag in leaf["tags"]:
            if tag:
                derived.setdefault(tag, []).append(" / ".join(leaf["path"]))
    conflicts = []
    for tag, want in sorted(fixed.items()):
        got = derived.get(tag)
        if not got:
            conflicts.append({"tag": tag, "expected": want, "derived": None, "kind": "TAG_NOT_PLACED"})
        elif len(set(got)) > 1 or got[0].split(" / ")[-1] != want:
            conflicts.append({"tag": tag, "expected": want, "derived": got, "kind": HEADER_BINDING_CONFLICT})
    return {"derived": {k: v[0] if len(set(v)) == 1 else v for k, v in sorted(derived.items())},
            "conflicts": conflicts, "state": "BOUND_BY_HEADER" if not conflicts else HEADER_BINDING_CONFLICT,
            "unplaced": table.get("unplaced", [])}


# ------------------------------------------------------------------ 5. BOXED semantics and footing release
SOURCE_EXPLICIT = "SOURCE_EXPLICIT"
SOURCE_DERIVED_HIGH_CONFIDENCE = "SOURCE_DERIVED_HIGH_CONFIDENCE"
PROJECT_PATTERN_ONLY = "PROJECT_PATTERN_ONLY"
GENERIC_HYPOTHESIS = "GENERIC_HYPOTHESIS"
UNRESOLVED = "UNRESOLVED"
SEMANTIC_CLASSES = (SOURCE_EXPLICIT, SOURCE_DERIVED_HIGH_CONFIDENCE, PROJECT_PATTERN_ONLY, GENERIC_HYPOTHESIS,
                    UNRESOLVED)
QUANTIFIABLE_SEMANTICS = (SOURCE_EXPLICIT, SOURCE_DERIVED_HIGH_CONFIDENCE)

REBAR_VERIFIED, REBAR_LOWER_BOUND = "REBAR_VERIFIED", "REBAR_LOWER_BOUND"
REBAR_PROVISIONAL, REBAR_BLOCKED = "REBAR_PROVISIONAL", "REBAR_BLOCKED"
FOOTING_RELEASE_STATES = (REBAR_VERIFIED, REBAR_LOWER_BOUND, REBAR_PROVISIONAL, REBAR_BLOCKED)


def may_quantify(semantics_class) -> bool:
    if semantics_class not in SEMANTIC_CLASSES:
        raise GuardError(f"unknown semantics class {semantics_class}")
    return semantics_class in QUANTIFIABLE_SEMANTICS


def boxed_part(*, part_id, semantics_class, raw_value, provenance=None, why=None) -> dict:
    """The accurate part for a BOXED component. Below SOURCE_DERIVED_HIGH_CONFIDENCE it is BLOCKED_UNQUANTIFIED
    (no kg, not even zero). S4 builds a quantified part itself only once the semantics are quantifiable; this
    function refuses to."""
    if may_quantify(semantics_class):
        raise GuardError(f"{part_id}: BOXED semantics {semantics_class} are quantifiable - S4 must compute the part "
                         "from the stated semantics, not from this placeholder")
    p = {"part_id": part_id, "category": "FOUNDATIONS", "component": "BOXED_REBAR", "state": AR.BLOCKED_UNQUANTIFIED,
         "kg": None, "basis": ["SCHEDULE", "STRUCTURAL_DETAIL"], "semantics_class": semantics_class,
         "raw_value": raw_value, "why": why or f"BOXED '{raw_value}': semantics {semantics_class}"}
    if provenance is not None:
        p["provenance"] = provenance
    return AR.validate_part(p)


def footing_release(parts, *, occurrence_state=OCC_RELEASED) -> dict:
    """Release state of ONE footing occurrence from its accurate parts (all FOUNDATIONS parts of the occurrence).
    A blocked occurrence blocks every part. Otherwise any unquantified / lower-bound / provisional component
    caps the footing below VERIFIED; the released components stay released."""
    states = Counter(p["state"] for p in parts)
    unq = sorted(p["component"] for p in parts if p["state"] == AR.BLOCKED_UNQUANTIFIED)
    released_kg = sum(p["kg"] for p in parts if p["state"] in AR.RELEASED_STATES)
    if occurrence_state not in (OCC_RELEASED, OCC_PROVISIONAL, OCC_BLOCKED):
        raise GuardError(f"unknown occurrence state {occurrence_state}")
    if occurrence_state == OCC_BLOCKED or not parts:
        st = REBAR_BLOCKED
    elif states[AR.VERIFIED] + states[AR.LOWER_BOUND] == 0:
        st = REBAR_PROVISIONAL if states[AR.PROVISIONAL] else REBAR_BLOCKED
    elif occurrence_state == OCC_PROVISIONAL:
        st = REBAR_PROVISIONAL          # an open occurrence query: never VERIFIED, never silently resolved
    elif unq or states[AR.LOWER_BOUND] or states[AR.PROVISIONAL] or states[AR.BLOCKED_MODELLED]:
        st = REBAR_LOWER_BOUND
    else:
        st = REBAR_VERIFIED
    return {"release_state": st, "occurrence_state": occurrence_state,
            "released_kg": None if st == REBAR_BLOCKED else released_kg,
            "unquantified_components": unq, "parts_by_state": dict(sorted(states.items()))}


def policy_record() -> dict:
    return {"policy_id": POLICY_ID, "token_classes": list(TOKEN_CLASSES),
            "routes": {k: v for k, v in ROUTES.items()},
            "applicable_parsers": {k: list(v) for k, v in APPLICABLE.items()},
            "known_disagreement_classes": dict(KNOWN_DISAGREEMENT_CLASSES),
            "terminals": list(TERMINALS), "blocked_terminals": list(BLOCKED_TERMINALS),
            "semantic_classes": list(SEMANTIC_CLASSES), "quantifiable_semantics": list(QUANTIFIABLE_SEMANTICS),
            "footing_release_states": list(FOOTING_RELEASE_STATES),
            "never": ["a boxed pair parsed as a bar", "a known-disagreement class consumed",
                      "a blocked item carrying a quantity", "an outline or tag dropped",
                      "a count taken from outside the source", "nearest-wins between two tags in one outline",
                      "a column bound by attribute tag against the drawn header"]}
