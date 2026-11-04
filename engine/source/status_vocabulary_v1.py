"""STATUS VOCABULARY V1 (T-468; owner directive 2026-11-02 E2, follow-up and gate of the same day): ONE status vocabulary
for every BOQ quantity, with every other status word in use mapped to it, and the ACCEPTANCE RECORD kept beside MERGED.

    map_word(vocabulary, word)        -> {"vocabulary", "word", "axis", "canonical", "quantity", "note"}; an unlisted
                                         word raises StatusError (never defaulted, never guessed)
    quantity_of_line(line, ...)       -> one QUANTITY state for a canonical BOQ line (engine/source/boq_line.py) from its
                                         evidence state and the Checker records bound to it
    acceptance_problems(record)       -> [problem text] for one URBAN_ACCEPTANCE_RECORD_V1 (empty: well formed)
    accepted_state(record)            -> the QUANTITY state a well-formed record supports (VERIFIED needs BOTH proofs)
    words_in_master(master)           -> {(vocabulary, word)} of every state word one BOQ_FAMILY_MASTER file uses
    table_rows() / markdown()         -> the mapping table (research/agents_t468/STATUS_VOCABULARY_V1.md is its copy)

THE CHOICE. The quantity vocabulary is the one the BOQ export already writes per row (tools/boq_export_v1.py QSTATES,
T-245 / T-294 / T-298): VERIFIED, VERIFIED ZERO, VERIFIED COMPONENT, MEASURED UNVERIFIED, HELD, UNMEASURED, EXCLUDED.
It is the only one of the vocabularies in use that already separates the owner's words (VERIFIED line / VERIFIED
COMPONENT / VERIFIED ZERO / HELD / EXCLUDED / UNMEASURED) and reaches VERIFIED only through a bound Checker record.
Two words the owner named are not quantity states and get their own axis, so one word never carries two meanings:
    PRICING       UNPRICED (every line today: boq_line refuses any money field; T-469 (8)); PRICED is reserved for the
                  pricing framework (T-472, paused) and is refused here until a dated, approved rate record exists.
    COMPLETENESS  the five component states of T-471 (research/agents_t471/t471_completeness.STATES), verbatim.

The other vocabularies keep their own words (no stored field is renamed); each word is mapped once:
    axis       QUANTITY / COMPLETENESS / PRICING (canonical) or EVIDENCE, APPROVAL, CODE_CAPABILITY, CANDIDATE, WORKFLOW,
               RUN, GATE, CHECKER_VERDICT, CHECKER_DOWNGRADE, ELEMENT_INVENTORY, OWNER_CLASS (mapped)
    quantity   the QUANTITY state the word establishes BY ITSELF for the thing it labels, or None when the word says
               nothing about a quantity (a task, a run, code). Invariant (tested): no word outside a Checker verdict
               record establishes any VERIFIED state; MERGED, INTEGRATED_AND_TESTED, a legacy 'VERIFIED' or
               'INDEPENDENTLY_CHECKED' evidence word, a gate PASS or an owner_status_class 'VERIFIED' never do.

The ACCEPTANCE RECORD (owner gate 2026-11-02) sits beside MERGED: MERGED says code or research entered the working branch;
the record says a quantity was accepted. It holds two proofs (owner instruction 2026-11-02): MEASUREMENT (an independent
re-measure: a bound URBAN_CHECKER_VERDICT_V2 / the T-180 re-measure) and AGGREGATION (component -> line -> subtotal ->
total: T-469 scoreboard / T-471 completeness matrix / the export's completeness record). VERIFIED for a LINE, a TRADE
or the BOQ needs both; a COMPONENT needs the measurement proof; VERIFIED ZERO needs an absence proof read from the
drawings. The board workflow and the dashboard are unchanged: nothing here reads or writes the board.

Check-only module: it writes no BOQ quantity, changes no line, reads no project file. Stdlib + boq_line only.
"""

from __future__ import annotations

import re

from engine.source import boq_line as BL

SCHEMA = "URBAN_STATUS_VOCABULARY_V1"
POLICY_ID = "STATUS_VOCABULARY_V1"
DEFAULT_GUARD_CLASS = "CHECK_ONLY"     # T-212 property P1: a check module; writes no BOQ quantity
ACCEPTANCE_SCHEMA = "URBAN_ACCEPTANCE_RECORD_V1"


class StatusError(ValueError):
    pass


# ---- the canonical axes ---------------------------------------------------------------------------------------------
# QUANTITY: the words of tools/boq_export_v1.py QSTATES (spelling identical; pinned by a test, never imported here so
# this module stays importable without tools/)
VERIFIED, VERIFIED_ZERO, VERIFIED_COMPONENT = "VERIFIED", "VERIFIED ZERO", "VERIFIED COMPONENT"
MEASURED_UNVERIFIED, HELD, UNMEASURED, EXCLUDED = "MEASURED UNVERIFIED", "HELD", "UNMEASURED", "EXCLUDED"
QUANTITY = (VERIFIED, VERIFIED_ZERO, VERIFIED_COMPONENT, MEASURED_UNVERIFIED, HELD, UNMEASURED, EXCLUDED)
VERIFIED_STATES = (VERIFIED, VERIFIED_ZERO, VERIFIED_COMPONENT)
QUANTITY_MEANING = {
    VERIFIED: "the WHOLE line re-measured independently by the Checker within 1 % (bound URBAN_CHECKER_VERDICT_V2, "
              "scope WHOLE, status COUNTED) AND its completeness / aggregation record passes; not downgraded",
    VERIFIED_ZERO: "evidence of absence verified: a 0 or not-applicable line inside a passing WHOLE verdict; the zero "
                   "is a checked fact, never a missing quantity",
    VERIFIED_COMPONENT: "a component (element) of the line re-measured by the Checker (scope COMPONENT, COUNTED); the "
                        "line as a whole is NOT verified (PARTIAL n/m)",
    MEASURED_UNVERIFIED: "a released quantity (evidence MEASURED / SOURCE_DERIVED / PROVISIONAL with a value) not yet "
                         "independently verified; MEASURED is never VERIFIED",
    HELD: "applicable, quantity not released: bounded, blocked on an RFI / owner question, applicability unsettled, "
          "existence in conflict, or downgraded by the Checker; never 0 and never summed into a released figure",
    UNMEASURED: "applicable and established by the drawings or an inventory, but no line measures it (T-471 MISSING)",
    EXCLUDED: "no quantity by a stated reason: an exclusion with its rule, or not-applicable with evidence that no "
              "Checker has yet confirmed (it becomes VERIFIED ZERO only under a passing WHOLE verdict)",
}
QUANTITY_RANK = {VERIFIED: 6, VERIFIED_ZERO: 6, VERIFIED_COMPONENT: 5, MEASURED_UNVERIFIED: 4, HELD: 2,
                 UNMEASURED: 1, EXCLUDED: 0}

UNPRICED, PRICED = "UNPRICED", "PRICED"
PRICING = (UNPRICED, PRICED)
PRICING_MEANING = {UNPRICED: "no approved, dated rate applied (every canonical line today: boq_line refuses money "
                             "fields)",
                   PRICED: "RESERVED for the pricing framework (T-472, paused): refused until a rate record exists"}

COMPLETENESS = ("NOT_APPLICABLE", "APPLICABLE_VERIFIED", "APPLICABLE_HELD", "APPLICABLE_UNMEASURED",
                "POSSIBLY_APPLICABLE")              # research/agents_t471/t471_completeness.STATES, pinned by a test
COMPLETENESS_QUANTITY = {"NOT_APPLICABLE": EXCLUDED, "APPLICABLE_VERIFIED": VERIFIED, "APPLICABLE_HELD": HELD,
                         "APPLICABLE_UNMEASURED": UNMEASURED, "POSSIBLY_APPLICABLE": HELD}

CANONICAL_AXES = {"QUANTITY": QUANTITY, "PRICING": PRICING, "COMPLETENESS": COMPLETENESS}

# ---- the mapped vocabularies ----------------------------------------------------------------------------------------
# vocabulary -> (axis, source, {word: (quantity or None, note)})
_E = "evidence state alone; VERIFIED needs a bound Checker WHOLE verdict + completeness (quantity_of_line)"
_W = "task workflow only: says nothing about any quantity; acceptance is the separate ACCEPTANCE RECORD"
_C = "code capability of the family in the RELEASED configuration; never a measurement or verification claim"
_K = "family state in the opt-in candidate; the Gate B byte-identity of a line is regression, not verification"

VOCABULARIES = {
    "boq_line.EVIDENCE": ("EVIDENCE", "engine/source/boq_line.py EVIDENCE", {
        "MEASURED": (MEASURED_UNVERIFIED, _E + "; HELD when measured_net is missing"),
        "SOURCE_DERIVED": (MEASURED_UNVERIFIED, _E + "; HELD when measured_net is missing"),
        "PROVISIONAL": (MEASURED_UNVERIFIED, _E + "; HELD when measured_net is missing"),
        "BOUNDED_EXPOSURE": (HELD, "a range, not a released quantity; low .. high kept, never 0"),
        "BLOCKED_RFI": (HELD, "blocked on a question; never 0"),
        "EXCLUDED_WITH_REASON": (EXCLUDED, "excluded with its reason (notes required by boq_line)"),
        "NOT_APPLICABLE_WITH_EVIDENCE": (EXCLUDED, "absence claimed with evidence; VERIFIED ZERO only under a passing "
                                                   "WHOLE verdict (tools/boq_export_v1 build)"),
    }),
    "boq_line.APPROVAL": ("APPROVAL", "engine/source/boq_line.py APPROVAL", {
        "MACHINE_ONLY": (None, "approval axis, independent of the quantity state"),
        "REVIEWED": (None, "approval axis; a review is not an independent re-measure"),
        "APPROVED": (None, "approval axis; an approval is not an independent re-measure"),
        "RELEASED_FOR_PRICING": (None, "approval axis; release for pricing is not verification"),
        "INVALIDATED": (HELD, "a revision change invalidated the line: its quantity is held until re-measured"),
    }),
    "export.quantity_state": ("QUANTITY", "tools/boq_export_v1.py QSTATES (the canonical words)",
                              {q: (q, "canonical") for q in QUANTITY}),
    "export.owner_status_class": ("OWNER_CLASS", "tools/boq_export_v1.py CLS_*", {
        "VERIFIED": (None, "AMBIGUOUS: the export writes it for VERIFIED, VERIFIED ZERO and VERIFIED COMPONENT alike; "
                           "read quantity_state, never this class, for verification"),
        "SOURCE-SUPPORTED PENDING INDEPENDENT CHECK": (MEASURED_UNVERIFIED, "released, not checked"),
        "PROJECT-SPECIFIC": (MEASURED_UNVERIFIED, "released on a project / owner fact, not checked"),
        "OWNER DECISION REQUIRED": (HELD, "held on an owner decision"),
        "HELD": (HELD, "held"),
        "EXCLUDED": (EXCLUDED, "excluded"),
    }),
    "family_master.capability": ("CODE_CAPABILITY", "rules/coverage/BOQ_FAMILY_MASTER_*.json capability_states", {
        "INTEGRATED_AND_TESTED": (None, _C + " (tested code is not a verified quantity)"),
        "PARTIAL": (None, _C),
        "IMPLEMENTED_NOT_INTEGRATED": (None, _C + " (opt-in only: the released BOQ has no line from it)"),
        "EXPERIMENTAL": (None, _C + " (research code, read by no method)"),
        "BLOCKED_BY_SOURCE": (None, _C + " (needs documents the engine does not read)"),
        "NOT_IMPLEMENTED": (None, _C + " (no code measures it; an applicable component is UNMEASURED by T-471)"),
    }),
    "family_master.candidate": ("CANDIDATE", "rules/coverage/BOQ_FAMILY_MASTER_*.json candidate_states", {
        "INTEGRATED_IN_CANDIDATE_AND_TESTED": (None, _K + "; HELD / UNKNOWN lines may remain ('open')"),
        "HELD_IN_CANDIDATE": (HELD, _K + "; the candidate releases no quantity of the family"),
        "IN_CANDIDATE_BASE_LINES": (None, _K + "; lines exactly as the base run"),
        "NOT_IN_CANDIDATE": (None, _K + "; no line (UNMEASURED only where T-471 finds the component applicable)"),
    }),
    "family_master.coverage_in_candidate": ("CANDIDATE", "BOQ_FAMILY_MASTER_1.29.0+ families[].coverage_in_candidate", {
        "COVERED_BY_<family code>": (None, "this family's faces are carried on another family's lines (pattern; the "
                                           "family code must be a registry code such as B4-01); no line of its own"),
    }),
    "board.workflow": ("WORKFLOW", "docs/agents/BOARD.md Status column (agents/control) + BOARD_ARCHIVE.md", {
        w: (None, _W) for w in ("QUEUED", "TODO", "CLAIMED", "IN PROGRESS", "READY", "HANDOFF", "MERGED", "REJECTED",
                                "BLOCKED", "BLOCKED-DATA", "BLOCKED-OWNER", "PAUSED", "SUPERSEDED", "CANCELLED",
                                "CLOSED", "DONE")}),
    "run_log.final": ("RUN", "docs/agents/RUN_LOG.md final lines (CLAUDE.md 'Run records')", {
        w: (None, "a run's outcome; a successful run is not an engineering verification")
        for w in ("STARTED", "SUCCESS", "BLOCKED", "FAILED", "INCOMPLETE", "IDLE")}),
    "checker.gate": ("GATE", "Checker gates (AGENT_BRIEF 'Checker gates')", {
        "GATE A PASS": (None, "a piece may merge; its quantities stay unverified until a verdict record binds them"),
        "GATE A FAIL": (None, "the piece does not merge"),
        "GATE B PASS": (None, "an integration package may merge; every other line byte-identical (regression)"),
        "GATE B FAIL": (None, "the package does not merge"),
    }),
    "checker.verdict_scope": ("CHECKER_VERDICT", "tools/boq_export_v1.py V2_SCOPES (status COUNTED, bound)", {
        "WHOLE": (VERIFIED, "COUNTED within 1 %, bound to the line content, completeness record passing; a 0 or "
                            "not-applicable line under it is VERIFIED ZERO"),
        "COMPONENT": (VERIFIED_COMPONENT, "the named components only; the line stays PARTIAL n/m"),
        "PARTIAL": (VERIFIED_COMPONENT, "part of the line only; never verifies the line (T-469 / T-471)"),
    }),
    "checker.downgrade": ("CHECKER_DOWNGRADE", "tools/boq_export_v1.py DOWNGRADE_STATES", {
        "HELD": (HELD, "a binding downgrade; it outranks any verdict on the line"),
        "CONFLICT": (HELD, "a binding downgrade on conflicting sources; held, never 0"),
    }),
    "t469.line_class": ("QUANTITY_CLASS", "research/agents_t469/t469_trade_scoreboard.py line_class", {
        "RELEASED": (MEASURED_UNVERIFIED, "a quantity state with a value; VERIFIED only under a WHOLE verdict"),
        "HELD": (HELD, "held"),
        "EXCLUDED": (EXCLUDED, "excluded / not applicable"),
    }),
    "t471.owner_gate": ("COMPLETENESS_GATE", "research/agents_t471/t471_completeness.py GATES", {
        "VERIFIED": (VERIFIED, "every non-excluded line of the component VERIFIED"),
        "MEASURED": (MEASURED_UNVERIFIED, "released, not verified"),
        "HELD": (HELD, "held"),
        "MISSING": (UNMEASURED, "applicable, no line"),
        "NOT_APPLICABLE": (EXCLUDED, "not applicable by drawing evidence; VERIFIED ZERO needs a Checker absence proof"),
        "POSSIBLY_APPLICABLE": (HELD, "applicability unsettled: held, never 0"),
    }),
    "t471.state": ("COMPLETENESS", "research/agents_t471/t471_completeness.py STATES (the canonical words)", {
        s: (COMPLETENESS_QUANTITY[s], "canonical completeness state") for s in COMPLETENESS}),
    "trade_completeness.element": ("ELEMENT_INVENTORY", "engine/source/trade_completeness_v1.py ELEMENT_STATUSES", {
        "EXCLUDED": (EXCLUDED, "exclusion with its rule, or every line excluded / not applicable"),
        "VERIFIED": (VERIFIED_COMPONENT, "an ELEMENT with a COUNTED verdict: a component, not the whole line"),
        "MEASURED": (MEASURED_UNVERIFIED, "a quantity line, not verified"),
        "HELD": (HELD, "held with a reason"),
        "UNRESOLVED": (HELD, "held without a reason: still held, never 0"),
        "INVENTORY_GEOMETRY_ONLY": (UNMEASURED, "drawn, untagged, no line links it"),
        "CONFLICT": (HELD, "inventories disagree on its existence: held, never 0"),
        "MISSING": (UNMEASURED, "an inventory element with no line and no hold"),
        "REGISTER_ONLY": (None, "an inventory disagreement flag; the element's 'measurement' field gives the quantity"),
        "OUT_OF_INVENTORY_SCOPE": (None, "no inventory covers the storey; the 'measurement' field gives the quantity"),
    }),
}
# the older vocabularies boq_line.LEGACY already maps to an evidence state; they reach QUANTITY through it
for _voc, _m in BL.LEGACY.items():
    VOCABULARIES[f"legacy.{_voc}"] = ("EVIDENCE", f"engine/source/boq_line.py LEGACY['{_voc}'] -> EVIDENCE", {
        w: ((VOCABULARIES["boq_line.EVIDENCE"][2][ev][0] if ev else None),
            (f"-> evidence {ev}" if ev else "-> approval axis (boq_line.APPROVAL_FROM)")
            + ("; a legacy 'verified' word is NOT a bound Checker verdict" if "VERIF" in w or "CHECKED" in w
               or w in ("RELEASED", "COMPUTED_SHADOW_COMPLETE") else ""))
        for w, ev in _m.items()})

# vocabularies whose VERIFIED words are derived ONLY from bound Checker verdict records (the export binds them; T-471
# and trade_completeness_v1 read the same records); every other vocabulary is tested never to establish VERIFIED
CHECKER_VOCABULARIES = ("checker.verdict_scope", "export.quantity_state", "t471.state", "t471.owner_gate",
                        "trade_completeness.element")
_COVERED_RE = re.compile(r"^COVERED_BY_(B\d{1,2}-\d{2})$")


def map_word(vocabulary, word):
    """-> the mapping of one status word; StatusError for an unknown vocabulary or an unlisted word."""
    if vocabulary not in VOCABULARIES:
        raise StatusError(f"vocabulary {vocabulary!r} is not mapped (known: {sorted(VOCABULARIES)})")
    axis, _src, words = VOCABULARIES[vocabulary]
    key = word
    if vocabulary == "family_master.coverage_in_candidate":
        m = _COVERED_RE.match(str(word))
        if not m:
            raise StatusError(f"{vocabulary}: {word!r} is not COVERED_BY_<family code> (refused, never defaulted)")
        key = "COVERED_BY_<family code>"
    if key not in words:
        raise StatusError(f"{vocabulary}: status {word!r} is not mapped (refused, never defaulted)")
    q, note = words[key]
    canonical = word if axis in CANONICAL_AXES else q
    return {"vocabulary": vocabulary, "word": word, "axis": axis, "canonical": canonical, "quantity": q, "note": note}


# ---- a line's quantity state ----------------------------------------------------------------------------------------

def quantity_of_line(line, *, whole=False, component=False, downgraded=False, completeness_passes=False):
    """-> one QUANTITY state for a canonical line. The Checker facts are given, already bound (tools/boq_export_v1
    bind_verdict / apply_downgrades): whole = a COUNTED WHOLE verdict, component = a COUNTED COMPONENT / PARTIAL one,
    downgraded = a binding downgrade, completeness_passes = the trade's completeness record passes. A downgrade wins;
    WHOLE without a passing completeness record does not verify (the export's rule)."""
    ev = line.get("evidence_state")
    if ev not in BL.EVIDENCE:
        raise StatusError(f"evidence_state {ev!r} is not one of {BL.EVIDENCE} (refused)")
    if downgraded:
        return HELD
    if ev in ("EXCLUDED_WITH_REASON", "NOT_APPLICABLE_WITH_EVIDENCE"):
        if ev == "NOT_APPLICABLE_WITH_EVIDENCE" and whole and completeness_passes:
            return VERIFIED_ZERO
        return EXCLUDED
    if ev not in BL.QUANTITY_STATES or line.get("measured_net") is None:
        return HELD
    if whole and completeness_passes:
        return VERIFIED_ZERO if float(line["measured_net"]) == 0.0 else VERIFIED
    if component:
        return VERIFIED_COMPONENT
    return MEASURED_UNVERIFIED


def pricing_of_line(line):
    """-> UNPRICED; PRICED is refused until the pricing framework exists (boq_line refuses any money key)."""
    if not isinstance(line, dict):
        raise StatusError("a line is an object")
    return UNPRICED


# ---- the acceptance record (beside MERGED) --------------------------------------------------------------------------
SUBJECT_KINDS = ("LINE", "COMPONENT", "TRADE", "BOQ")
MEASUREMENT_PROOFS = ("CHECKER_VERDICT_V2", "T180_REMEASURE", "ABSENCE_FROM_DRAWINGS")
AGGREGATION_PROOFS = ("T469_SCOREBOARD", "T471_COMPLETENESS", "EXPORT_COMPLETENESS_RECORD")
ACCEPTANCE_STATES = (VERIFIED, VERIFIED_ZERO, VERIFIED_COMPONENT)
CHECKER_ROUTINES = ("CHECKER", "VERIFIER")        # tools/boq_export_v1.py CHECKER_ROUTINES
ACCEPTANCE_REQUIRED = ("schema", "acceptance_id", "subject_kind", "subject_id", "task", "candidate_version", "state",
                       "measurement_proof", "checker", "time")
_TIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2})?Z$")
_COMMIT_RE = re.compile(r"^[0-9a-f]{6,40}$")
_TASK_RE = re.compile(r"^T-\d{3}$")


def _proof_problems(name, proof, kinds):
    if not isinstance(proof, dict):
        return [f"{name}: an object with kind, ref and commit"]
    p = []
    if proof.get("kind") not in kinds:
        p.append(f"{name}.kind: {proof.get('kind')!r} is not one of {kinds}")
    if not (isinstance(proof.get("ref"), str) and proof["ref"].strip()):
        p.append(f"{name}.ref: the record id / file the proof is (required)")
    if not (isinstance(proof.get("commit"), str) and _COMMIT_RE.match(proof["commit"])):
        p.append(f"{name}.commit: the commit that holds it (6 to 40 hex characters)")
    return p


def acceptance_problems(rec):
    """-> [problem text] for one URBAN_ACCEPTANCE_RECORD_V1 (empty: well formed and sufficient for its state)."""
    if not isinstance(rec, dict):
        return ["record: not an object"]
    p = [f"{k}: required" for k in ACCEPTANCE_REQUIRED if rec.get(k) in (None, "", [], {})]
    if rec.get("schema") not in (None, "") and rec["schema"] != ACCEPTANCE_SCHEMA:
        p.append(f"schema: {rec['schema']!r} is not {ACCEPTANCE_SCHEMA}")
    kind, state = rec.get("subject_kind"), rec.get("state")
    if kind not in (None, "") and kind not in SUBJECT_KINDS:
        p.append(f"subject_kind: {kind!r} is not one of {SUBJECT_KINDS}")
    if state not in (None, "") and state not in ACCEPTANCE_STATES:
        p.append(f"state: {state!r} is not one of {ACCEPTANCE_STATES} (an acceptance record only accepts)")
    if rec.get("task") not in (None, "") and not (isinstance(rec["task"], str) and _TASK_RE.match(rec["task"])):
        p.append("task: a board task id such as T-180")
    if rec.get("time") not in (None, "") and not (isinstance(rec["time"], str) and _TIME_RE.match(rec["time"])):
        p.append("time: ISO 8601 UTC from `date -u`, e.g. 2026-11-04T15:00Z")
    mp, ap = rec.get("measurement_proof"), rec.get("aggregation_proof")
    if mp not in (None, {}):
        p += _proof_problems("measurement_proof", mp, MEASUREMENT_PROOFS)
    if ap not in (None, {}):
        p += _proof_problems("aggregation_proof", ap, AGGREGATION_PROOFS)
    ch = rec.get("checker")
    if ch not in (None, {}):
        if not (isinstance(ch, dict) and isinstance(ch.get("routine"), str)
                and any(ch["routine"].strip().upper().startswith(r) for r in CHECKER_ROUTINES)):
            p.append("checker.routine: the Checker / Verifier alone accepts a quantity")
        elif isinstance(rec.get("author"), str) and rec["author"].strip().upper() == ch["routine"].strip().upper():
            p.append("checker: the author of the measured work cannot accept it")
    if rec.get("merge") is not None and not (isinstance(rec["merge"], str) and _COMMIT_RE.match(rec["merge"])):
        p.append("merge: the MERGED commit this record sits beside (optional; never a proof by itself)")
    # sufficiency: which proofs each accepted state needs
    mk = mp.get("kind") if isinstance(mp, dict) else None
    if state == VERIFIED_COMPONENT and kind not in (None, "", "COMPONENT", "LINE"):
        p.append(f"state VERIFIED COMPONENT is for a COMPONENT (or a line's components), not a {kind}")
    if state == VERIFIED_COMPONENT and mk == "ABSENCE_FROM_DRAWINGS":
        p.append("VERIFIED COMPONENT needs a re-measure, not an absence proof")
    if state in (VERIFIED, VERIFIED_ZERO) and kind in ("LINE", "TRADE", "BOQ") and ap in (None, {}):
        p.append(f"aggregation_proof: required: {state} for a {kind} needs both proofs (measurement AND aggregation; "
                 "owner 2026-11-02)")
    if state == VERIFIED and mk == "ABSENCE_FROM_DRAWINGS":
        p.append("VERIFIED needs a re-measure; an absence proof supports VERIFIED ZERO only")
    if state == VERIFIED_ZERO and mk not in (None, "ABSENCE_FROM_DRAWINGS", "CHECKER_VERDICT_V2"):
        p.append("VERIFIED ZERO needs an absence proof from the drawings or a WHOLE Checker verdict")
    if state == VERIFIED and kind == "COMPONENT":
        p.append("a COMPONENT is VERIFIED COMPONENT; VERIFIED is a whole line, trade or BOQ")
    return p


def accepted_state(rec):
    """-> the QUANTITY state the record supports; StatusError when it is malformed or insufficient (never promoted)."""
    p = acceptance_problems(rec)
    if p:
        raise StatusError("acceptance record refused: " + "; ".join(p))
    return rec["state"]


def trade_state(line_states, acceptance=None):
    """-> VERIFIED for a trade only when every line is VERIFIED / VERIFIED ZERO / EXCLUDED, at least one is verified,
    and a well-formed TRADE acceptance record with both proofs is given; otherwise the weakest line state."""
    states = list(line_states)
    for s in states:
        if s not in QUANTITY:
            raise StatusError(f"line state {s!r} is not a QUANTITY state")
    if not states:
        return UNMEASURED
    if all(s == EXCLUDED for s in states):
        return EXCLUDED
    if all(s in (VERIFIED, VERIFIED_ZERO, EXCLUDED) for s in states):
        want = VERIFIED if VERIFIED in states else VERIFIED_ZERO
        if acceptance is not None and acceptance.get("subject_kind") in ("TRADE", "BOQ") \
                and accepted_state(acceptance) == want:
            return want
        return MEASURED_UNVERIFIED          # lines verified, the trade's aggregation not accepted yet
    order = (UNMEASURED, HELD, MEASURED_UNVERIFIED, VERIFIED_COMPONENT)
    for s in order:
        if s in states:
            return s if s != VERIFIED_COMPONENT else MEASURED_UNVERIFIED
    return MEASURED_UNVERIFIED


# ---- census of words in use -----------------------------------------------------------------------------------------

def words_in_master(master):
    """-> {(vocabulary, word)} of every state word one BOQ_FAMILY_MASTER document declares or uses."""
    out = set()
    for w in master.get("capability_states") or ():
        out.add(("family_master.capability", w))
    for w in master.get("candidate_states") or ():
        out.add(("family_master.candidate", w))
    for f in master.get("families") or ():
        if f.get("capability"):
            out.add(("family_master.capability", f["capability"]))
        c = f.get("candidate")
        if isinstance(c, dict) and c.get("state"):
            out.add(("family_master.candidate", c["state"]))
        cov = f.get("coverage_in_candidate")
        if isinstance(cov, dict) and cov.get("state"):
            out.add(("family_master.coverage_in_candidate", cov["state"]))
    return out


def table_rows():
    rows = []
    for voc in sorted(VOCABULARIES):
        axis, src, words = VOCABULARIES[voc]
        for w in sorted(words):
            q, note = words[w]
            rows.append({"vocabulary": voc, "source": src, "axis": axis, "word": w, "quantity": q, "note": note})
    return rows


def markdown():
    out = [f"# {SCHEMA}: the one status vocabulary (T-468)", "",
           "Generated by `python3 -I research/agents_t468/build_status_table.py`; tests/t468_status_vocabulary "
           "pins this file to the module. No quantity, line or stored field changes.", "",
           "## Canonical axes", "", "| axis | word | meaning |", "|---|---|---|"]
    out += [f"| QUANTITY | {q} | {QUANTITY_MEANING[q]} |" for q in QUANTITY]
    out += [f"| PRICING | {q} | {PRICING_MEANING[q]} |" for q in PRICING]
    out += [f"| COMPLETENESS | {s} | T-471 component state; quantity reading {COMPLETENESS_QUANTITY[s]} |"
            for s in COMPLETENESS]
    out += ["", "## Every mapped word", "",
            "`quantity` = the QUANTITY state the word establishes by itself; `-` = it says nothing about a quantity.",
            "", "| vocabulary | axis | word | quantity | note |", "|---|---|---|---|---|"]
    out += [f"| {r['vocabulary']} | {r['axis']} | {r['word']} | {r['quantity'] or '-'} | {r['note']} |"
            for r in table_rows()]
    out += ["", "## Acceptance record (beside MERGED)", "",
            f"Schema `{ACCEPTANCE_SCHEMA}`; required: {', '.join(ACCEPTANCE_REQUIRED)}; optional: aggregation_proof "
            "(required for VERIFIED / VERIFIED ZERO of a LINE, TRADE or BOQ), merge, author, notes.",
            f"Subject kinds {', '.join(SUBJECT_KINDS)}; states {', '.join(ACCEPTANCE_STATES)}; measurement proofs "
            f"{', '.join(MEASUREMENT_PROOFS)}; aggregation proofs {', '.join(AGGREGATION_PROOFS)}.",
            "MERGED (board) is never a proof; the Checker / Verifier alone accepts; the author cannot accept."]
    return "\n".join(out) + "\n"

