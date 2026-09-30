"""UNIT_CONTEXT + REGION_MEASUREMENT_TRANSFORM + MEASUREMENT_FRAME (R8.3).

UNIT_CONTEXT               what ONE coordinate unit means in ONE coordinate space
                           (model space, a paper layout, a future PDF page, a future raster page).
                           Exactly one per coordinate space (invariant U-1): a detail may not
                           redefine native coordinate meaning.
REGION_MEASUREMENT_TRANSFORM
                           how one drawing region relates to the real building: local scale,
                           rotation, reflection. An enlarged model-space detail is a region
                           scale, never a second native unit.
MEASUREMENT_FRAME          UNIT_CONTEXT + REGION: can this region support a physical
                           measurement, and for what use.

Status is CALCULATED from admitted evidence by the deterministic rule below; no caller,
agent or human sets it. A human may add a HUMAN_CONFIRMATION evidence item (with the exact
source hash); an agent may only add CANDIDATE evidence.

FROZEN RULE (R8 revised spec v1 §5 "Status rules", frozen at R8.0 and re-cited by the
R8.3 brief §19; NOT retuned on any project):
    VERIFIED            >= 2 independent non-plausibility evidence kinds agree within 0.5 %;
                        none disagrees by > 0.5 %; every checked dimension residual
                        <= max(2 mm, 0.2 %); no declaration contradicted
    CONFIRMED_BY_HUMAN  a human confirmation for this exact source, over a non-VERIFIED frame
    PROVISIONAL         one independent non-plausibility class with no contradiction, or
                        >= 2 agreeing classes that contradict a declaration
    UNCONFIRMED         declaration (or medium convention) only
    CONFLICT            two independent kinds (a declaration counts) disagree by > 0.5 %;
                        or one lineage disagrees with itself
    BLOCKED             no admissible evidence; checked-dimension residual failure

    CANDIDATE evidence (agent output, or any item resting on an unresolved ASSUMPTION)
    may LOWER a status to CONFLICT - it can reveal a contradiction - but never raise one.

INDEPENDENCE is formal, never a flag: each item carries its failure-domain lineage
(AUTHORED:<fact>, TRANSCRIPTION:<model/run>, DOCUMENT:<sha>, HUMAN:<who>, PARSER:<lib>,
ASSUMPTION:<what>). Items sharing any relevant lineage element are ONE class. For the unit
and region-scale questions the parser that read an authored fact is not a shared cause
(a parser that misread INSUNITS cannot also make an unrelated dimension agree with it), so
PARSER:* is recorded but ignored; the SAME authored fact read by two parsers is still one
class because it shares AUTHORED:<fact>.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import findings as F
from .findings import SourceFinding

# ---------------------------------------------------------------- statuses and uses
VERIFIED, CONFIRMED_BY_HUMAN, PROVISIONAL = "VERIFIED", "CONFIRMED_BY_HUMAN", "PROVISIONAL"
UNCONFIRMED, CONFLICT, BLOCKED = "UNCONFIRMED", "CONFLICT", "BLOCKED"
STATUSES = (VERIFIED, CONFIRMED_BY_HUMAN, PROVISIONAL, UNCONFIRMED, BLOCKED, CONFLICT)
STRENGTH = {VERIFIED: 5, CONFIRMED_BY_HUMAN: 4, PROVISIONAL: 3, UNCONFIRMED: 2, BLOCKED: 1, CONFLICT: 0}

FINAL_MEASUREMENT, PREVIEW_MEASUREMENT = "FINAL_MEASUREMENT", "PREVIEW_MEASUREMENT"
COUNT_ONLY, ANNOTATION_MAPPING = "COUNT_ONLY", "ANNOTATION_MAPPING"
USES = (FINAL_MEASUREMENT, PREVIEW_MEASUREMENT, COUNT_ONLY, ANNOTATION_MAPPING)

# ---------------------------------------------------------------- frozen thresholds
AGREEMENT_REL = 0.005                 # independent agreement <= 0.5 %; > 0.5 % is a contradiction
CHECKED_DIM_ABS_MM = 2.0              # checked-dimension residual <= max(2 mm, 0.2 %)
CHECKED_DIM_REL = 0.002
THRESHOLD_SOURCE = ("R8 revised spec v1 §5 status rules (frozen R8.0); R8.3 brief §19. Source status "
                    "EXTERNAL_FROZEN_SPEC_NOT_PREVIOUSLY_COMMITTED: the spec lived in the review workspace, not this "
                    "repository; decision record tests/r8_3/registers/R8_3_THRESHOLD_PROVENANCE.json (spec sha256, "
                    "verbatim excerpt). Values preserved unchanged; pinned by tests/r8_3/test_r8_3_frame.py")

# ---------------------------------------------------------------- questions, kinds, producers
NATIVE_UNIT = "NATIVE_UNIT_TO_MM"     # value: millimetres per native coordinate unit
REGION_SCALE = "REGION_LOCAL_SCALE"   # value: dimensionless building units per native unit

UNIT_HEADER_DECLARATION = "UNIT_HEADER_DECLARATION"
DIMENSION_DISPLAY = "DIMENSION_DISPLAY"
DIMENSION_GEOMETRY = "DIMENSION_GEOMETRY"
DIMENSION_STYLE = "DIMENSION_STYLE"
EXPLICIT_SCALE_NOTE = "EXPLICIT_SCALE_NOTE"
EXPLICIT_UNIT_NOTE = "EXPLICIT_UNIT_NOTE"
KNOWN_PLOT_DIMENSION = "KNOWN_PLOT_DIMENSION"
OWNER_PROJECT_INPUT = "OWNER_PROJECT_INPUT"
HUMAN_CONFIRMATION = "HUMAN_CONFIRMATION"
SECTION_ELEVATION_DIMENSION = "SECTION_ELEVATION_DIMENSION"
SCALE_BAR = "SCALE_BAR"
OTHER_SOURCE_DOCUMENT = "OTHER_SOURCE_DOCUMENT"
PAPERSPACE_VIEWPORT_SCALE = "PAPERSPACE_VIEWPORT_SCALE"
MEDIUM_CONVENTION = "MEDIUM_CONVENTION"          # "model space is drawn full size"
GEOMETRY_PLAUSIBILITY = "GEOMETRY_PLAUSIBILITY"  # support only; never verifies
KINDS = (UNIT_HEADER_DECLARATION, DIMENSION_DISPLAY, DIMENSION_GEOMETRY, DIMENSION_STYLE, EXPLICIT_SCALE_NOTE,
         EXPLICIT_UNIT_NOTE, KNOWN_PLOT_DIMENSION, OWNER_PROJECT_INPUT, HUMAN_CONFIRMATION,
         SECTION_ELEVATION_DIMENSION, SCALE_BAR, OTHER_SOURCE_DOCUMENT, PAPERSPACE_VIEWPORT_SCALE,
         MEDIUM_CONVENTION, GEOMETRY_PLAUSIBILITY)
DECLARATION_KINDS = frozenset({UNIT_HEADER_DECLARATION, MEDIUM_CONVENTION, PAPERSPACE_VIEWPORT_SCALE})
SUPPORT_ONLY_KINDS = frozenset({GEOMETRY_PLAUSIBILITY})
# a dimension measured from the very geometry it annotates carries no unit or scale information
CIRCULAR_KINDS = frozenset({DIMENSION_GEOMETRY})

# Failure-domain FAMILIES a producer attaches as lineage ("FAMILY:<name>:<source sha>"), so that
# everything one drafter TYPED into one drawing is one piece of evidence however many styles or
# notes carry it (R8.0 MT-28), while a style factor and a typed note stay separate families (F26).
DOCUMENT_SOURCE, DIMENSION_STYLE_FAMILY = "DOCUMENT_SOURCE", "DIMENSION_STYLE"
SOURCE_GEOMETRY, EXTERNAL_DOCUMENT, DECLARATION_FAMILY, HUMAN_FAMILY = (
    "SOURCE_GEOMETRY", "EXTERNAL_DOCUMENT", "DECLARATION", "HUMAN")
FAMILY_BY_KIND = {EXPLICIT_SCALE_NOTE: DOCUMENT_SOURCE, EXPLICIT_UNIT_NOTE: DOCUMENT_SOURCE,
                  DIMENSION_DISPLAY: DOCUMENT_SOURCE, SCALE_BAR: DOCUMENT_SOURCE,
                  DIMENSION_STYLE: DIMENSION_STYLE_FAMILY, DIMENSION_GEOMETRY: SOURCE_GEOMETRY,
                  SECTION_ELEVATION_DIMENSION: DOCUMENT_SOURCE, KNOWN_PLOT_DIMENSION: EXTERNAL_DOCUMENT,
                  OWNER_PROJECT_INPUT: EXTERNAL_DOCUMENT, OTHER_SOURCE_DOCUMENT: EXTERNAL_DOCUMENT,
                  UNIT_HEADER_DECLARATION: DECLARATION_FAMILY, MEDIUM_CONVENTION: DECLARATION_FAMILY,
                  PAPERSPACE_VIEWPORT_SCALE: DECLARATION_FAMILY, HUMAN_CONFIRMATION: HUMAN_FAMILY,
                  GEOMETRY_PLAUSIBILITY: "PLAUSIBILITY"}


def family_lineage(kind: str, source_sha256: str | None) -> str:
    """The family lineage element a producer attaches for one source."""
    return f"FAMILY:{FAMILY_BY_KIND[kind]}:{source_sha256}"

DECODER, ENGINE, AGENT, HUMAN = "DECODER", "ENGINE", "AGENT", "HUMAN"
PRODUCERS = (DECODER, ENGINE, AGENT, HUMAN)
ADMITTED, CANDIDATE, REJECTED = "ADMITTED", "CANDIDATE", "REJECTED"

INDEPENDENCE_POLICY = {
    NATIVE_UNIT: {"ignore_prefixes": ("PARSER:",),
                  "why": "a parser defect cannot make two different authored facts agree on a unit"},
    REGION_SCALE: {"ignore_prefixes": ("PARSER:",), "why": "as for NATIVE_UNIT"},
}

# DXF / DWG $INSUNITS -> millimetres per unit. 0 = unitless: NO default is inferred.
INSUNITS = {1: ("inch", 25.4), 2: ("foot", 304.8), 3: ("mile", 1609344.0), 4: ("millimetre", 1.0),
            5: ("centimetre", 10.0), 6: ("metre", 1000.0), 7: ("kilometre", 1e6), 8: ("microinch", 2.54e-5),
            9: ("mil", 0.0254), 10: ("yard", 914.4), 11: ("angstrom", 1e-7), 12: ("nanometre", 1e-6),
            13: ("micron", 1e-3), 14: ("decimetre", 100.0), 15: ("decametre", 1e4), 16: ("hectometre", 1e5),
            17: ("gigametre", 1e12), 18: ("astronomical unit", 1.495978707e14),
            19: ("light year", 9.4607304725808e18), 20: ("parsec", 3.0856775814913673e19),
            21: ("US survey foot", 1200.0 / 3937.0 * 1000.0), 22: ("US survey inch", 100.0 / 3937.0 * 1000.0),
            23: ("US survey yard", 3600.0 / 3937.0 * 1000.0), 24: ("US survey mile", 6336000.0 / 3937.0 * 1000.0)}


class FrameStatusError(Exception):
    """Raised when anything tries to SET a frame status instead of letting the policy compute it."""


@dataclass(frozen=True)
class UnitEvidence:
    evidence_id: str
    question: str
    kind: str
    scope: str                                   # coordinate_space_id (NATIVE_UNIT) or region_id (REGION_SCALE)
    lineage: tuple                               # failure-domain lineage ids; never empty
    derived_value: float | None = None           # candidate mm/native (NATIVE_UNIT) or local scale
    observed_value: object = None
    source_ref: str | None = None
    source_sha256: str | None = None
    unit: str | None = None
    producer: str = ENGINE
    review_status: str = ADMITTED
    author: str | None = None                    # HUMAN_CONFIRMATION
    timestamp: str | None = None
    notes: str = ""
    derived_set: tuple = ()                      # CONSTRAINT: the values consistent with this item (it can
                                                 # contradict a value outside the set, never confirm one)

    def __post_init__(self):
        if self.question not in (NATIVE_UNIT, REGION_SCALE):
            raise ValueError(f"unknown question {self.question!r}")
        if self.kind not in KINDS:
            raise ValueError(f"unknown evidence kind {self.kind!r}")
        if self.producer not in PRODUCERS:
            raise ValueError(f"unknown producer {self.producer!r}")
        if self.review_status not in (ADMITTED, CANDIDATE, REJECTED):
            raise ValueError(f"unknown review status {self.review_status!r}")
        if not self.lineage:
            raise ValueError(f"{self.evidence_id}: evidence without failure-domain lineage")
        if self.derived_value is not None and not self.derived_value > 0:
            raise ValueError(f"{self.evidence_id}: non-positive derived value")
        if any(not v > 0 for v in self.derived_set):
            raise ValueError(f"{self.evidence_id}: non-positive value in derived set")

    def as_dict(self):
        return {k: (list(v) if isinstance(v, tuple) else v) for k, v in self.__dict__.items()}


@dataclass(frozen=True)
class CheckedDimension:
    """An authored dimension whose stored measurement is compared with its own geometry."""
    obs_id: str
    geometry_native: float
    measured_native: float

    def residual_ok(self, mm_per_native: float) -> bool:
        res = abs(self.geometry_native - self.measured_native) * mm_per_native
        return res <= max(CHECKED_DIM_ABS_MM, CHECKED_DIM_REL * abs(self.geometry_native) * mm_per_native)


@dataclass(frozen=True)
class Assessment:
    status: str
    value: float | None
    reason: str
    classes: tuple = ()                 # tuple of tuples of evidence ids (independence classes)
    admitted: tuple = ()
    excluded: tuple = ()                # (evidence_id, why)
    contesting_candidates: tuple = ()
    machine_status: str | None = None   # before any human confirmation
    machine_support: str = "NONE"       # AGREEING_PHYSICAL_EVIDENCE / DECLARATION_ONLY / NONE
    confirmation: dict | None = None
    human_basis: str | None = None      # CONSISTENT_WITH_ALL_EVIDENCE / NO_NON_HUMAN_EVIDENCE_AGREES / ...
    findings: tuple = ()


def _agree(a, b):
    return abs(a - b) <= AGREEMENT_REL * max(abs(a), abs(b))


def _relevant(lineage, question):
    ign = INDEPENDENCE_POLICY[question]["ignore_prefixes"]
    return {x for x in lineage if not x.startswith(ign)}


def independence_classes(items, question) -> list:
    """Union-find over shared relevant lineage: items in one class are ONE piece of evidence."""
    parent = list(range(len(items)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    owner = {}
    for i, e in enumerate(items):
        for x in _relevant(e.lineage, question):
            if x in owner:
                parent[find(i)] = find(owner[x])
            else:
                owner[x] = i
    groups = {}
    for i in range(len(items)):
        groups.setdefault(find(i), []).append(items[i])
    return list(groups.values())


def _member(v, values) -> bool:
    return any(_agree(v, x) for x in values)


def _intersect(sets) -> tuple:
    """Tolerant intersection of value sets (agreement within the frozen 0.5 %)."""
    out = tuple(sets[0])
    for s in sets[1:]:
        out = tuple(v for v in out if _member(v, s))
    return tuple(dict.fromkeys(out))


def _two_independent_kinds(classes) -> bool:
    """Two DIFFERENT classes contributing two DIFFERENT kinds."""
    ks = [{x.kind for x in c} for c in classes]
    return any(k1 != k2 for i, a in enumerate(ks) for b in ks[i + 1:] for k1 in a for k2 in b)


def admissibility(e: UnitEvidence, source_sha256: str | None):
    """(admissible, why). Only DECODER / ENGINE / HUMAN items reviewed ADMITTED count."""
    if e.review_status == REJECTED:
        return False, "REJECTED"
    if e.producer == AGENT and e.review_status == ADMITTED:
        return False, "AGENT_CANNOT_ADMIT_EVIDENCE"
    if e.review_status != ADMITTED:
        return False, "CANDIDATE"
    if any(x.startswith("ASSUMPTION:") for x in e.lineage):
        return False, "ASSUMPTION_UNRESOLVED"
    if e.kind in SUPPORT_ONLY_KINDS:
        return False, "PLAUSIBILITY_SUPPORT_ONLY"
    if e.kind in CIRCULAR_KINDS:
        return False, "CIRCULAR_WITH_MEASURED_GEOMETRY"
    if e.kind == HUMAN_CONFIRMATION:
        if e.producer != HUMAN or not e.author or not e.timestamp:
            return False, "HUMAN_CONFIRMATION_INCOMPLETE"
        if source_sha256 is None or e.source_sha256 != source_sha256:
            return False, "HUMAN_CONFIRMATION_SOURCE_MISMATCH"
    if e.derived_value is None and not e.derived_set:
        return False, "NO_DERIVED_VALUE"
    return True, None


def assess(question: str, evidence, source_sha256: str | None, checked_dimensions=(), local_scale: float = 1.0,
           unit_mm: float | None = None, scope: str = "") -> Assessment:
    """The frozen deterministic rule. Pure function of its inputs."""
    evidence = [e for e in evidence if e.question == question]
    adm, excluded, cands, findings = [], [], [], []
    for e in evidence:
        ok, why = admissibility(e, source_sha256)
        if ok:
            adm.append(e)
            continue
        excluded.append((e.evidence_id, why))
        if why == "HUMAN_CONFIRMATION_SOURCE_MISMATCH":
            findings.append(SourceFinding(F.HUMAN_CONFIRMATION_SOURCE_MISMATCH, None, (), f"{scope}: {e.evidence_id}"))
        elif why == "AGENT_CANNOT_ADMIT_EVIDENCE":
            findings.append(SourceFinding(F.AGENT_STATUS_ESCALATION_REJECTED, None, (), f"{scope}: {e.evidence_id}"))
        if why in ("CANDIDATE", "ASSUMPTION_UNRESOLVED", "AGENT_CANNOT_ADMIT_EVIDENCE") and (
                e.derived_value is not None or e.derived_set):
            cands.append(e)
    human = [e for e in adm if e.kind == HUMAN_CONFIRMATION]
    decls = [e for e in adm if e.kind in DECLARATION_KINDS]
    phys = [e for e in adm if e.kind not in DECLARATION_KINDS and e.kind != HUMAN_CONFIRMATION]
    classes = independence_classes(phys, question)
    ids = tuple(tuple(sorted(x.evidence_id for x in c)) for c in classes)
    conflict_code = F.UNIT_EVIDENCE_CONFLICT if question == NATIVE_UNIT else F.REGION_SCALE_CONFLICT

    # ---- machine status
    status = value = None
    reason, support, extra = "", "NONE", []
    # Each class yields (members, value, set): a point value, or the intersection of its members'
    # SETS. A set establishes only the set; it supports a value only once reduced to ONE member
    # (fail closed: an AI never picks the "most plausible" member).
    supporting, constraints, all_sets = [], [], []
    for c in classes:
        pts = [x.derived_value for x in c if x.derived_value is not None]
        sets = [x.derived_set for x in c if x.derived_value is None and x.derived_set]
        all_sets.extend(sets)
        inter = _intersect(sets) if sets else None
        if (any(not _agree(pts[0], v) for v in pts[1:]) or (inter is not None and not inter)
                or (pts and inter is not None and not _member(pts[0], inter))):
            status, reason, extra = CONFLICT, "ONE_LINEAGE_DISAGREES_WITH_ITSELF", [conflict_code]
            continue
        if pts:
            supporting.append((c, pts[0]))
        elif len(inter) == 1:
            supporting.append((c, inter[0]))
        else:
            constraints.append(c)
    G = _intersect(all_sets) if all_sets else None
    if status is None and G is not None and not G:
        status, reason, extra = CONFLICT, "SET_INTERSECTION_EMPTY", [conflict_code]
    if status is None and G is not None and any(not _member(v, G) for _, v in supporting):
        status, reason, extra = CONFLICT, "POINT_VALUE_OUTSIDE_SET_INTERSECTION", [conflict_code]
    if status is None and constraints and G is not None and len(G) == 1 and not any(_agree(v, G[0]) for _, v in supporting):
        # independent sets jointly reduce to ONE interpretation: that joint conclusion is ONE class
        supporting.append(([x for c in constraints for x in c], G[0]))
    cvals = [v for _, v in supporting]
    dvals = [d.derived_value for d in decls]
    if status is None and any(not _agree(a, b) for i, a in enumerate(cvals) for b in cvals[i + 1:]):
        status, reason, extra = CONFLICT, "INDEPENDENT_CLASSES_DISAGREE", [conflict_code]
    if status is None and any(not _agree(a, b) for i, a in enumerate(dvals) for b in dvals[i + 1:]):
        status, reason, extra = CONFLICT, "DECLARATIONS_DISAGREE", [F.UNIT_DECLARATION_CONFLICT]
    if status is None:
        decl_contradicted = (bool(cvals) and any(not _agree(cvals[0], d) for d in dvals)) or (
            G is not None and any(not _member(d, G) for d in dvals))
        if _two_independent_kinds([c for c, _ in supporting]):
            if decl_contradicted:
                status, value, reason, support = (PROVISIONAL, cvals[0],
                                                  "INDEPENDENT_CLASSES_AGREE_BUT_CONTRADICT_DECLARATION",
                                                  "AGREEING_PHYSICAL_EVIDENCE")
                extra = [F.UNIT_DECLARATION_CONTRADICTED]
            else:
                status, value, reason, support = VERIFIED, cvals[0], "TWO_INDEPENDENT_KINDS_AGREE", "AGREEING_PHYSICAL_EVIDENCE"
        elif supporting:
            if decl_contradicted:
                status, reason, extra = CONFLICT, "DECLARATION_CONTRADICTED_BY_ONE_CLASS", [F.UNIT_DECLARATION_CONFLICT]
            else:
                status, value = PROVISIONAL, cvals[0]
                reason = "ONE_INDEPENDENT_CLASS" + ("_SAME_KIND_ONLY" if len(supporting) >= 2 else "")
                support = "AGREEING_PHYSICAL_EVIDENCE"
        elif decls:
            if decl_contradicted:
                status, reason, extra = CONFLICT, "DECLARATION_OUTSIDE_SET_INTERSECTION", [F.UNIT_DECLARATION_CONFLICT]
            else:                          # compatible with a multi-member set: membership is NOT support
                status, value, support = UNCONFIRMED, dvals[0], "DECLARATION_ONLY"
                reason = "DECLARATION_ONLY" + ("_COMPATIBLE_WITH_UNRESOLVED_SET" if G else "")
        elif G is not None:
            status, reason = UNCONFIRMED if len(G) > 1 else BLOCKED, f"UNRESOLVED_SET_OF_{len(G)}_INTERPRETATIONS"
        else:
            status, value, reason, support = BLOCKED, None, "NO_ADMISSIBLE_EVIDENCE", "NONE"
    # ---- plausibility never moves a status; disagreeing plausibility raises a QUESTION
    plaus = [e for e in evidence if e.kind in SUPPORT_ONLY_KINDS and e.derived_value is not None]
    ref_q = value if value is not None else (dvals[0] if dvals else None)
    if plaus and ref_q is not None and any(not _agree(ref_q, e.derived_value) for e in plaus):
        extra.append(F.UNIT_PLAUSIBILITY_QUESTION)
    # ---- checked dimensions (need a value to convert residuals to millimetres)
    if value is not None and checked_dimensions:
        mm = value if question == NATIVE_UNIT else (unit_mm or 0.0) * value
        if mm > 0:
            bad = [d.obs_id for d in checked_dimensions if not d.residual_ok(mm)]
            if bad:
                status, reason = BLOCKED, f"CHECKED_DIMENSION_RESIDUAL_FAILED:{','.join(bad[:10])}"
                extra.append(F.CHECKED_DIMENSION_RESIDUAL_FAILED)
    # ---- candidates may lower, never raise
    contesting = []
    ref = value
    for e in cands:
        allowed = (e.derived_value,) if e.derived_value is not None else e.derived_set
        if ref is not None and not any(_agree(ref, v) for v in allowed):
            contesting.append(e.evidence_id)
    if contesting and status not in (CONFLICT, BLOCKED):
        status, reason = CONFLICT, f"CONTESTED_BY_CANDIDATE_EVIDENCE ({reason})"
        extra.append(F.UNIT_DECLARATION_CONFLICT if support == "DECLARATION_ONLY" else
                     (F.UNIT_EVIDENCE_CONFLICT if question == NATIVE_UNIT else F.REGION_SCALE_CONFLICT))
    machine = status
    # ---- human confirmation: never VERIFIED; may resolve a DECLARATION conflict, never overrides evidence
    confirmation = None
    human_basis = None
    if human:
        h = human[-1]
        confirmation = {"evidence_id": h.evidence_id, "author": h.author, "timestamp": h.timestamp,
                        "value": h.derived_value, "source_sha256": h.source_sha256}
        hv = h.derived_value
        physical_vals = [v for _, v in supporting]
        cand_sets = [(e.derived_value,) if e.derived_value is not None else e.derived_set for e in cands]
        contradicts_physical = (any(not _agree(hv, v) for v in physical_vals) or (G is not None and not _member(hv, G))
                                or reason in ("INDEPENDENT_CLASSES_DISAGREE", "ONE_LINEAGE_DISAGREES_WITH_ITSELF",
                                              "SET_INTERSECTION_EMPTY", "POINT_VALUE_OUTSIDE_SET_INTERSECTION"))
        if contradicts_physical:
            status, value, reason = CONFLICT, None, "HUMAN_CONFIRMATION_CONTRADICTS_ADMITTED_EVIDENCE"
            extra.append(conflict_code)
        elif machine == VERIFIED:
            human_basis = "VERIFIED_UNCHANGED"
        else:
            status, value = CONFIRMED_BY_HUMAN, hv
            support_items = ([v for v in physical_vals if _agree(v, hv)] + [d for d in dvals if _agree(d, hv)]
                             + [1 for c in cand_sets if _member(hv, c)])
            against_candidates = [c for c in cand_sets if not _member(hv, c)]
            if against_candidates:
                human_basis = "CONTRADICTS_CANDIDATE_EVIDENCE"
            elif not support_items:
                human_basis = "NO_NON_HUMAN_EVIDENCE_AGREES"
            else:
                human_basis = "CONSISTENT_WITH_ALL_EVIDENCE"
            support = "AGREEING_PHYSICAL_EVIDENCE" if any(_agree(v, hv) for v in physical_vals) else (
                "DECLARATION_ONLY" if any(_agree(d, hv) for d in dvals) else "NONE")
            reason = f"HUMAN_CONFIRMED_OVER_{machine}"
    code = {UNCONFIRMED: F.UNIT_UNCONFIRMED, BLOCKED: F.UNIT_EVIDENCE_INSUFFICIENT,
            PROVISIONAL: F.UNIT_UNCONFIRMED}.get(status)
    if question == REGION_SCALE:
        code = {UNCONFIRMED: F.REGION_SCALE_UNCONFIRMED, BLOCKED: F.REGION_SCALE_UNCONFIRMED,
                PROVISIONAL: F.REGION_SCALE_UNCONFIRMED}.get(status)
    if code:
        extra.append(code)
    for c in dict.fromkeys(extra):
        findings.append(SourceFinding(c, None, (), f"{scope}: {reason}", scope=scope or None))
    return Assessment(status, value, reason, ids, tuple(e.evidence_id for e in adm), tuple(excluded),
                      tuple(contesting), machine, support, confirmation, human_basis, tuple(findings))


# ---------------------------------------------------------------- release policy (explicit)
@dataclass(frozen=True)
class ReleasePolicy:
    """URBAN_FRAME_RELEASE_V1 — which statuses may support FINAL scale-dependent measurement (§20).

    VERIFIED                FINAL.
    CONFIRMED_BY_HUMAN      FINAL only when the confirmation (a) is for this exact source hash,
                            (b) contradicts no admitted physical evidence and no constraint set,
                            candidate or admitted, and (c) at least one NON-human item agrees
                            with it (a declaration, a physical class or a constraint set).
                            A human may therefore RESOLVE a declaration conflict (INSUNITS says
                            inch, the dimension families exclude inch, the owner confirms
                            metre), but never overrides evidence and never confirms in a vacuum.
    anything else           no FINAL.
    """
    human_confirmed_final: bool = True
    policy_id: str = "URBAN_FRAME_RELEASE_V1"


DEFAULT_POLICY = ReleasePolicy()


def allowed_uses(status: str, human_basis: str | None = None, policy: ReleasePolicy = DEFAULT_POLICY) -> tuple:
    if status == VERIFIED:
        return USES
    if status == CONFIRMED_BY_HUMAN:
        final = policy.human_confirmed_final and human_basis == "CONSISTENT_WITH_ALL_EVIDENCE"
        return ((FINAL_MEASUREMENT,) if final else ()) + (PREVIEW_MEASUREMENT, COUNT_ONLY, ANNOTATION_MAPPING)
    if status in (PROVISIONAL, UNCONFIRMED):
        return (PREVIEW_MEASUREMENT, COUNT_ONLY, ANNOTATION_MAPPING)
    return (COUNT_ONLY,)


def _value_uses(uses, value):
    """No established value -> nothing scale-dependent can even be previewed."""
    return uses if value is not None else tuple(u for u in uses if u not in (FINAL_MEASUREMENT, PREVIEW_MEASUREMENT))


# ---------------------------------------------------------------- records
MODEL_SPACE, PAPER_LAYOUT, PDF_PAGE, RASTER_PAGE = "MODEL_SPACE", "PAPER_LAYOUT", "PDF_PAGE", "RASTER_PAGE"
SPACE_KINDS = (MODEL_SPACE, PAPER_LAYOUT, PDF_PAGE, RASTER_PAGE)

MODEL_SPACE_PLAN, MODEL_SPACE_DETAIL = "MODEL_SPACE_PLAN", "MODEL_SPACE_DETAIL"
PAPER_SPACE_VIEWPORT, PDF_VECTOR_REGION, RASTER_REGION = "PAPER_SPACE_VIEWPORT", "PDF_VECTOR_REGION", "RASTER_REGION"
REGION_KINDS = (MODEL_SPACE_PLAN, MODEL_SPACE_DETAIL, PAPER_SPACE_VIEWPORT, PDF_VECTOR_REGION, RASTER_REGION)
# uses a region kind can ever support, whatever its evidence
REGION_USE_CAP = {
    MODEL_SPACE_PLAN: USES, MODEL_SPACE_DETAIL: USES,
    PAPER_SPACE_VIEWPORT: (COUNT_ONLY, ANNOTATION_MAPPING),                      # never measurement authority
    PDF_VECTOR_REGION: (PREVIEW_MEASUREMENT, COUNT_ONLY, ANNOTATION_MAPPING),    # validation profile not approved
    RASTER_REGION: (PREVIEW_MEASUREMENT,),                                        # preview only
}


MEASUREMENT_REFUSAL = {PAPER_SPACE_VIEWPORT: "MEASURE_IN_MODEL_FRAME", PDF_VECTOR_REGION: "PDF_PROFILE_NOT_APPROVED",
                       RASTER_REGION: "RASTER_PREVIEW_ONLY"}


def measurement_authority(region_kind: str) -> tuple:
    """(may this kind of region ever be FINAL measurement authority, refusal reason)."""
    ok = FINAL_MEASUREMENT in REGION_USE_CAP[region_kind]
    return ok, None if ok else MEASUREMENT_REFUSAL[region_kind]


def independence_report(evidence, question: str = NATIVE_UNIT, source_sha256: str | None = None) -> dict:
    """How many INDEPENDENT pieces of evidence the items are, and why the others are not.
    Values are not needed: this is the independence structure, not the resolution."""
    usable, rejected = [], []
    for e in evidence:
        ok, why = admissibility(e, source_sha256)
        if not ok and why not in ("NO_DERIVED_VALUE",):
            rejected.append({"evidence_id": e.evidence_id, "reason": why})
            continue
        if e.kind in DECLARATION_KINDS or e.kind == HUMAN_CONFIRMATION:
            rejected.append({"evidence_id": e.evidence_id, "reason": "DECLARATION_OR_HUMAN_NOT_PHYSICAL_EVIDENCE"})
            continue
        usable.append(e)
    classes = independence_classes(usable, question)
    members = []
    for ci, c in enumerate(classes):
        for j, e in enumerate(c):
            fam = next((x.split(":")[1] for x in e.lineage if x.startswith("FAMILY:")), FAMILY_BY_KIND.get(e.kind))
            members.append({"evidence_id": e.evidence_id, "family": fam, "class": ci})
            if j:
                shared = _relevant(e.lineage, question) & set().union(*(_relevant(x.lineage, question) for x in c[:j]))
                rejected.append({"evidence_id": e.evidence_id,
                                 "reason": "SHARED_SOURCE_PRIMITIVE" if any(x.startswith("PRIMITIVE:") for x in shared)
                                 else "SAME_FAILURE_FAMILY" if any(x.startswith("FAMILY:") for x in shared)
                                 else "SHARED_LINEAGE"})
    return {"independent_set_size": len(classes), "families": len({m["family"] for m in members}),
            "members": members, "rejected": rejected}


@dataclass(frozen=True)
class UnitContext:
    unit_context_id: str
    source_sha256: str | None
    coordinate_space_id: str
    coordinate_space_kind: str
    declared_unit_code: int | None
    declared_unit_name: str | None
    declared_native_to_mm: float | None
    status: str
    native_to_mm: float | None          # the value the status stands behind (None when not established)
    status_reason: str
    machine_status: str
    machine_support: str
    evidence_ids: tuple
    excluded_evidence: tuple
    contesting_candidates: tuple
    confirmation: dict | None
    allowed_use: tuple
    findings: tuple = ()

    def as_dict(self):
        d = {k: v for k, v in self.__dict__.items() if k != "findings"}
        d["findings"] = [f.as_dict() for f in self.findings]
        return d


@dataclass(frozen=True)
class RegionMeasurementTransform:
    region_transform_id: str
    unit_context_id: str
    region_id: str
    region_kind: str
    parent_region_id: str | None
    bounds: tuple | None                 # native (xmin, ymin, xmax, ymax); None = whole space
    matrix: tuple                        # 2x3 affine native -> building-local (native units)
    local_scale: float | None
    rotation_rad: float
    reflection: bool
    reference: bool
    status: str
    status_reason: str
    machine_status: str
    machine_support: str
    evidence_ids: tuple
    excluded_evidence: tuple
    allowed_use: tuple
    findings: tuple = ()

    def as_dict(self):
        d = {k: v for k, v in self.__dict__.items() if k != "findings"}
        d["findings"] = [f.as_dict() for f in self.findings]
        return d


@dataclass(frozen=True)
class MeasurementFrame:
    frame_id: str
    unit_context_id: str
    region_transform_id: str
    status: str
    unit_status: str
    region_status: str
    native_to_mm: float | None
    local_scale: float | None
    mm_per_native: float | None
    allowed_use: tuple
    blocking_reasons: tuple
    findings: tuple = ()

    def as_dict(self):
        d = {k: v for k, v in self.__dict__.items() if k != "findings"}
        d["findings"] = [f.as_dict() for f in self.findings]
        return d


def declaration_evidence(insunits, space_id: str, source_sha256: str | None, parser: str = "LIBREDWG",
                         source_ref: str = "HEADER.INSUNITS") -> tuple:
    """INSUNITS as declaration evidence (never physical truth). 0 / absent: no default inferred."""
    try:
        code = int(insunits)
    except (TypeError, ValueError):
        code = None
    if code in INSUNITS:
        name, mm = INSUNITS[code]
        return (UnitEvidence(f"{space_id}:INSUNITS:{parser}", NATIVE_UNIT, UNIT_HEADER_DECLARATION, space_id,
                             (f"AUTHORED:{source_sha256}:HEADER.INSUNITS", f"PARSER:{parser}"), mm, code,
                             source_ref, source_sha256, name, DECODER),), None
    return (), SourceFinding(F.UNIT_DECLARATION_UNITLESS, None, (),
                             f"{space_id}: INSUNITS={insunits!r}; no unit is inferred", scope=space_id)


def unit_context(source_sha256, coordinate_space_id, coordinate_space_kind, evidence, insunits=None,
                 checked_dimensions=(), policy: ReleasePolicy = DEFAULT_POLICY, unit_context_id=None) -> UnitContext:
    """ONE unit context for ONE coordinate space. `evidence` may include the declaration
    (see declaration_evidence); evidence scoped to another space is rejected (U-1)."""
    if coordinate_space_kind not in SPACE_KINDS:
        raise ValueError(coordinate_space_kind)
    findings = []
    own = []
    for e in evidence:
        if e.question != NATIVE_UNIT:
            continue
        if e.scope != coordinate_space_id:
            findings.append(SourceFinding(F.UNIT_REDEFINITION_REJECTED, None, (),
                                          f"{e.evidence_id}: scoped to {e.scope}, not {coordinate_space_id} (U-1)",
                                          scope=coordinate_space_id))
            continue
        own.append(e)
    a = assess(NATIVE_UNIT, own, source_sha256, checked_dimensions, scope=coordinate_space_id)
    code = int(insunits) if isinstance(insunits, (int, float)) and int(insunits) in INSUNITS else None
    return UnitContext(unit_context_id or f"UC:{coordinate_space_id}", source_sha256, coordinate_space_id,
                       coordinate_space_kind, code if code is not None else (insunits if insunits is not None else None),
                       INSUNITS[code][0] if code else None, INSUNITS[code][1] if code else None,
                       a.status, a.value if a.status not in (CONFLICT, BLOCKED) else None, a.reason, a.machine_status,
                       a.machine_support, a.admitted, a.excluded, a.contesting_candidates, a.confirmation,
                       _value_uses(allowed_uses(a.status, a.human_basis, policy),
                                   a.value if a.status not in (CONFLICT, BLOCKED) else None),
                       tuple(findings) + a.findings)


def _decompose(m):
    import math
    a, b, c, d = m[0], m[1], m[3], m[4]
    det = a * d - b * c
    sx = math.hypot(a, c)
    sy = abs(det) / sx if sx else 0.0
    return math.atan2(c, a), det < 0, sx, sy


def region_transform(unit: UnitContext, region_id: str, region_kind: str, evidence=(), matrix=(1, 0, 0, 0, 1, 0),
                     reference: bool = False, bounds=None, parent_region_id=None,
                     policy: ReleasePolicy = DEFAULT_POLICY) -> RegionMeasurementTransform:
    """A region's relation to the real building. MODEL_SPACE_PLAN regions carry the medium
    convention (full size) as a DECLARATION; a `reference` plan region is the one the unit
    context is defined through, so its full-size scale is definitional (not re-verified here,
    but still contradicted by any region-scale evidence that disagrees). A detail carries no
    convention: without evidence its scale is BLOCKED."""
    if region_kind not in REGION_KINDS:
        raise ValueError(region_kind)
    if reference and region_kind != MODEL_SPACE_PLAN:
        raise ValueError("only a model-space plan region can be the unit reference region")
    rot, refl, sx, sy = _decompose(matrix)
    findings = []
    if abs(sx - sy) > AGREEMENT_REL * max(sx, sy, 1e-300):
        findings.append(SourceFinding(F.REGION_SCALE_CONFLICT, None, (), f"{region_id}: non-uniform region scale",
                                      scope=region_id))
    ev = [e for e in evidence if e.question == REGION_SCALE and e.scope == region_id]
    if region_kind == MODEL_SPACE_PLAN:
        ev.append(UnitEvidence(f"{region_id}:MODEL_SPACE_FULL_SIZE", REGION_SCALE, MEDIUM_CONVENTION, region_id,
                               (f"CONVENTION:MODEL_SPACE_FULL_SIZE:{region_id}",), 1.0, producer=ENGINE))
    a = assess(REGION_SCALE, ev, unit.source_sha256, scope=region_id, unit_mm=unit.native_to_mm)
    status, reason, machine = a.status, a.reason, a.machine_status
    if region_kind == MODEL_SPACE_DETAIL and status == BLOCKED and not a.admitted:
        reason = "U-2: DETAIL_SCALE_WITHOUT_REGION_EVIDENCE"
    if reference and status == UNCONFIRMED and a.reason == "DECLARATION_ONLY":
        status, reason, machine = VERIFIED, "REFERENCE_REGION_BY_DEFINITION", VERIFIED
    if any(f.code == F.REGION_SCALE_CONFLICT and "non-uniform" in f.detail for f in findings):
        status, reason = CONFLICT, "NON_UNIFORM_REGION_SCALE"
    uses = allowed_uses(status, a.human_basis, policy)
    cap = REGION_USE_CAP[region_kind]
    if region_kind in (PDF_VECTOR_REGION, RASTER_REGION):
        findings.append(SourceFinding(F.REGION_PROFILE_NOT_APPROVED, None, (),
                                      f"{region_id}: {region_kind} validation profile not production-approved",
                                      scope=region_id))
    uses = tuple(u for u in uses if u in cap)
    scale = a.value if status not in (CONFLICT, BLOCKED) else None
    return RegionMeasurementTransform(f"RT:{region_id}", unit.unit_context_id, region_id, region_kind, parent_region_id,
                                      bounds, tuple(matrix), scale, rot, refl, reference, status, reason, machine,
                                      a.machine_support, a.admitted, a.excluded, uses,
                                      tuple(findings) + tuple(f for f in a.findings
                                                              if not (reference and f.code == F.REGION_SCALE_UNCONFIRMED
                                                                      and status == VERIFIED)))


def compose_status(unit_status: str, region_status: str) -> str:
    """The frame is no stronger than its weakest required component. CONFIRMED_BY_HUMAN ranks
    below VERIFIED, so a human-confirmed component is always visible in the frame status."""
    return min((unit_status, region_status), key=lambda s: STRENGTH[s])


def measurement_frame(unit: UnitContext, region: RegionMeasurementTransform,
                      policy: ReleasePolicy = DEFAULT_POLICY) -> MeasurementFrame:
    if region.unit_context_id != unit.unit_context_id:
        raise ValueError("region belongs to another unit context")
    status = compose_status(unit.status, region.status)
    uses = tuple(u for u in USES if u in unit.allowed_use and u in region.allowed_use)
    reasons = []
    for name, st, why in (("UNIT_CONTEXT", unit.status, unit.status_reason),
                          ("REGION_MEASUREMENT_TRANSFORM", region.status, region.status_reason)):
        if FINAL_MEASUREMENT not in (unit.allowed_use if name == "UNIT_CONTEXT" else region.allowed_use):
            reasons.append(f"{name} {st}: {why}")
    findings = list(unit.findings) + list(region.findings)
    if status == CONFLICT:
        findings.append(SourceFinding(F.FRAME_CONFLICT, None, (), f"{region.region_id}: {'; '.join(reasons)}",
                                      scope=region.region_id))
    elif FINAL_MEASUREMENT not in uses:
        findings.append(SourceFinding(F.FRAME_INELIGIBLE, None, (), f"{region.region_id}: {'; '.join(reasons)}",
                                      scope=region.region_id))
    mm = unit.native_to_mm * region.local_scale if unit.native_to_mm and region.local_scale else None
    return MeasurementFrame(f"MF:{region.region_id}", unit.unit_context_id, region.region_transform_id, status,
                            unit.status, region.status, unit.native_to_mm, region.local_scale, mm, uses,
                            tuple(reasons), tuple(findings))


class FrameRegistry:
    """Holds the unit contexts, regions and frames of one source. Enforces U-1 and refuses any
    attempt to set a status directly: status is only ever computed from admitted evidence."""

    def __init__(self, source_sha256: str | None):
        self.source_sha256 = source_sha256
        self.units, self.regions, self.frames = {}, {}, {}

    def add_unit_context(self, uc: UnitContext):
        if uc.source_sha256 != self.source_sha256:
            raise ValueError("unit context for another source")
        if uc.coordinate_space_id in {u.coordinate_space_id for u in self.units.values()}:
            raise ValueError(f"U-1: a second UNIT_CONTEXT for coordinate space {uc.coordinate_space_id}")
        self.units[uc.unit_context_id] = uc
        return uc

    def add_region(self, rt: RegionMeasurementTransform):
        if rt.unit_context_id not in self.units:
            raise ValueError("region without a registered unit context")
        self.regions[rt.region_id] = rt
        self.frames[rt.region_id] = measurement_frame(self.units[rt.unit_context_id], rt)
        return self.frames[rt.region_id]

    def set_status(self, target_id: str, status: str, producer: str):
        """Never allowed. Humans add HUMAN_CONFIRMATION evidence; agents add CANDIDATE evidence."""
        if producer == AGENT:
            raise FrameStatusError(f"AGENT may not set status {status!r} on {target_id}: "
                                   "agent output is candidate evidence only")
        raise FrameStatusError(f"{producer} may not set status {status!r} on {target_id}: status is computed; "
                               "add admitted evidence instead")
