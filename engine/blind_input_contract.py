"""A18 and every blind visual pass: what may be handed to it, and nothing else.

A blind interpretation pass exists to answer one question: CAN THIS AGENT
SEE THE DRAWING. It is not a test of whether the agent can find, in this
repository, an answer somebody has already worked out. The two look
identical from the outside — both produce a number that agrees with the
benchmark — and only one of them is evidence that the engine can read a
building.

So the input side is a CONTRACT rather than an intention. A blind pass
receives:

    THE IMAGE          the selected source drawing image, a whole-floor
                       image, and crops generated from it
    WHAT SHEET IT IS   enough drawing metadata to say which sheet and
                       which floor this is
    THE RULES          approved Urban Projects GENERAL construction rules
    THE SPEC           project specifications that would be on the desk of
                       anybody doing this take-off for real

and never:

    a reconciliation file, a human benchmark workbook, a manually
    reconstructed quantity, a correction note, a known target area, a
    previous agent's answer, an owner rule request whose text reveals the
    geometry it is asking about, a benchmark-informed hypothesis, or any
    previously corrected geometry for the spaces under test

Four gates stand between an input and the pass, because a declared kind
is only as honest as the caller:

    KIND        the declared kind is one of the allowed kinds. An
                UNDECLARED KIND IS REFUSED — a missing rule is not a
                permissive rule
    PATH        the file does not sit anywhere prohibited information
                lives, whatever it has been called
    CONTENT     for anything with readable content, the bytes are scanned
                for benchmark-shaped keys and text
    CROP BASIS  a crop says what decided its box. A CROP DRAWN AROUND THE
                ANSWER IS THE ANSWER: a box chosen from a known target
                dimension hands the agent the reading it was meant to
                find, in a form no content scan would catch

A refusal AT THE DOOR is not a contaminated run: the information never
reached the agent, the refusal is recorded, and the pass continues. When
prohibited information is found to have ENTERED the context, the run is
`BLIND_TEST_INVALID` and it stops — there is no partial credit, because
a pass that has seen the answer cannot un-see it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from engine import benchmark_protection as bp
from engine import export_provenance as prov
from engine import reference_mapping as refmap

MODEL = "A_BLIND_PASS_RECEIVES_THE_DRAWING_AND_NOTHING_ELSE_V1"

MANIFEST_NAME = "A18_INPUT_MANIFEST.json"

# --- what a blind pass MAY receive ---------------------------------------
SOURCE_DRAWING_IMAGE = "THE_SELECTED_SOURCE_DRAWING_IMAGE"
WHOLE_FLOOR_IMAGE = "A_WHOLE_FLOOR_IMAGE"
LOCAL_CROP = "A_GENERATED_LOCAL_CROP"
SHEET_METADATA = "DRAWING_METADATA_THAT_IDENTIFIES_THE_SHEET"
GENERAL_RULE = "AN_APPROVED_URBAN_PROJECTS_GENERAL_RULE"
PROJECT_SPECIFICATION = "A_PROJECT_SPECIFICATION"
ALLOWED_KINDS = (SOURCE_DRAWING_IMAGE, WHOLE_FLOOR_IMAGE, LOCAL_CROP,
                 SHEET_METADATA, GENERAL_RULE, PROJECT_SPECIFICATION)

# --- and what it may NEVER receive ---------------------------------------
RECONCILIATION_FILE = "A_RECONCILIATION_FILE"
HUMAN_WORKBOOK = "A_HUMAN_BENCHMARK_WORKBOOK"
RECONSTRUCTED_QUANTITY = "A_MANUALLY_RECONSTRUCTED_QUANTITY"
CORRECTION_NOTE = "A_CORRECTION_NOTE"
KNOWN_TARGET_AREA = "A_KNOWN_TARGET_AREA"
PREVIOUS_AGENT_ANSWER = "A_PREVIOUS_AGENT_ANSWER"
REVEALING_RULE_REQUEST = "AN_OWNER_RULE_REQUEST_THAT_REVEALS_GEOMETRY"
BENCHMARK_HYPOTHESIS = "A_BENCHMARK_INFORMED_HYPOTHESIS"
PRIOR_CORRECTED_GEOMETRY = "PREVIOUSLY_CORRECTED_GEOMETRY_FOR_THESE_SPACES"
PROHIBITED_KINDS = (RECONCILIATION_FILE, HUMAN_WORKBOOK,
                    RECONSTRUCTED_QUANTITY, CORRECTION_NOTE,
                    KNOWN_TARGET_AREA, PREVIOUS_AGENT_ANSWER,
                    REVEALING_RULE_REQUEST, BENCHMARK_HYPOTHESIS,
                    PRIOR_CORRECTED_GEOMETRY)

# --- where prohibited information lives, by the shape of the path --------
#
# Matched on the path, not on the declared kind, so that relabelling a
# file does not get it through. The drawing itself lives under an inputs
# directory and is not caught by any of these.
# Each row is (pattern, what it would be, answer_files_only).
#
# Matched on the path, not on the declared kind, so that relabelling a
# file does not get it through. The last row is a heuristic about THIS
# repository — a previous agent's answer is a WRITTEN answer — so it
# applies only to files that carry writing. A drawing, a scan and an
# image rendered from one are not previous answers, and the rows above it
# catch a sealed take-off whatever its extension.
PROHIBITED_PATHS = (
    (re.compile(r"reconcil", re.I), RECONCILIATION_FILE, False),
    (re.compile(r"(^|[/_-])sealed([/_-]|$)", re.I), KNOWN_TARGET_AREA, False),
    (re.compile(r"benchmark|qiyal|known_?total|take_?off_?total", re.I),
     KNOWN_TARGET_AREA, False),
    (re.compile(r"\.xlsx?$|workbook|excel", re.I), HUMAN_WORKBOOK, False),
    (re.compile(r"owner_rule_request", re.I), REVEALING_RULE_REQUEST, False),
    (re.compile(r"correction|corrected", re.I), CORRECTION_NOTE, False),
    (re.compile(r"hypothes", re.I), BENCHMARK_HYPOTHESIS, False),
    (re.compile(r"manual|reconstruct", re.I), RECONSTRUCTED_QUANTITY, False),
    (re.compile(r"(export|report|register|round\d|geometry|takeoff)", re.I),
     PREVIOUS_AGENT_ANSWER, True),
)

# What counts as a file that carries writing rather than a picture.
ANSWER_SUFFIXES = (".json", ".csv", ".md", ".txt", ".yaml", ".yml", ".tsv")

# --- what may decide a crop box ------------------------------------------
CROP_FROM_SHEET_TILING = "A_UNIFORM_TILING_OF_THE_SHEET"
CROP_FROM_DRAWING_COORDINATES = "COORDINATES_READ_OFF_THE_DRAWING_ITSELF"
CROP_REQUESTED_BY_THE_AGENT = "THE_AGENT_ASKED_TO_LOOK_THERE"
CROP_BASES = (CROP_FROM_SHEET_TILING, CROP_FROM_DRAWING_COORDINATES,
              CROP_REQUESTED_BY_THE_AGENT)
CROP_FROM_A_TARGET = "A_BOX_DERIVED_FROM_A_KNOWN_TARGET"

# --- the gates ------------------------------------------------------------
DECLARED_GATE = "DECLARED_GATE"
KIND_GATE = "KIND_GATE"
PATH_GATE = "PATH_GATE"
CONTENT_GATE = "CONTENT_GATE"
CROP_BASIS_GATE = "CROP_BASIS_GATE"
EXISTS_GATE = "EXISTS_GATE"
# In this order. A prohibited path is answered BEFORE the file is looked
# for on disk, so that naming a reconciliation file is refused as what it
# is rather than as a typo.
GATES = (DECLARED_GATE, KIND_GATE, PATH_GATE, CROP_BASIS_GATE, EXISTS_GATE,
         CONTENT_GATE)

ADMITTED = "ADMITTED"
REFUSED = "REFUSED_AT_THE_DOOR"

# --- the run --------------------------------------------------------------
VALID = "BLIND_RUN_VALID"
INVALID = "BLIND_TEST_INVALID"

A_CROP_AROUND_THE_ANSWER_IS_THE_ANSWER = (
    "a crop box chosen from a known target hands the agent the reading it "
    "was meant to find, in a form no content scan can catch. A crop says "
    "what decided its box, or it is refused")

A_REFUSAL_IS_NOT_A_CONTAMINATION = (
    "an input refused at the door never reached the agent. The refusal is "
    "recorded and the run stays valid. A run is invalid only where "
    "prohibited information ENTERED the context")


class BlindTestInvalid(RuntimeError):
    """Prohibited information reached a pass that had to be blind."""


def model_hash() -> str:
    import hashlib

    parts = ([MODEL] + list(ALLOWED_KINDS) + list(PROHIBITED_KINDS)
             + list(CROP_BASES) + list(GATES) + [VALID, INVALID])
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


def frozen_parameters() -> dict:
    return {
        "MODEL": MODEL,
        "ALLOWED_KINDS": list(ALLOWED_KINDS),
        "PROHIBITED_KINDS": list(PROHIBITED_KINDS),
        "CROP_BASES": list(CROP_BASES),
        "GATES": list(GATES),
        "why": {
            "an_undeclared_kind_is_refused": (
                "a missing rule is not a permissive rule. An input whose "
                "kind is not one of the allowed kinds does not reach the "
                "pass, however harmless it looks"),
            "a_path_is_checked_as_well_as_a_kind": (
                "a declared kind is only as honest as the caller, and "
                "renaming a reconciliation file does not make it one of "
                "the drawings"),
            "a_crop_says_what_decided_its_box":
                A_CROP_AROUND_THE_ANSWER_IS_THE_ANSWER,
            "a_refusal_is_not_a_contamination":
                A_REFUSAL_IS_NOT_A_CONTAMINATION,
        },
    }


# ------------------------------------------------------------- an input

@dataclass
class Input:
    """One thing a blind pass is being offered, before any gate runs."""

    input_id: str = ""
    kind: str = ""
    what_it_is: str = ""
    path: str = ""            # a file on disk
    content: object = None    # a projection handed straight in
    media_type: str = ""
    origin: str = ""          # the drawing an image was rendered from
    derived_from: str = ""    # the input_id a crop was cut from
    crop_basis: str = ""
    crop_box_px: tuple = ()
    supplied_by: str = ""

    def identity(self) -> dict:
        """Hashes and identifiers — what the manifest has to carry."""
        out = {"input_id": self.input_id, "kind": self.kind,
               "what_it_is": self.what_it_is,
               "media_type": self.media_type or _media_type(self.path)}
        if self.path:
            p = Path(self.path)
            out["path"] = _rel(self.path)
            if p.exists():
                out["bytes"] = p.stat().st_size
                out[prov.RAW] = prov.raw_sha256(p)
        if self.content is not None:
            out[prov.CANONICAL] = prov.canonical_sha256(self.content)
            out["content_fields"] = (sorted(self.content)
                                     if isinstance(self.content, dict)
                                     else [])
        if self.origin:
            out["rendered_from"] = _rel(self.origin)
        if self.derived_from:
            out["derived_from"] = self.derived_from
        if self.crop_basis:
            out["crop_basis"] = self.crop_basis
            out["crop_box_px"] = list(self.crop_box_px)
        if self.supplied_by:
            out["supplied_by"] = self.supplied_by
        return out


@dataclass
class Decision:
    input_id: str = ""
    kind: str = ""
    status: str = ADMITTED
    gates_passed: tuple = ()
    refused_by: str = ""
    would_be: str = ""
    why: str = ""
    identity: dict = field(default_factory=dict)

    @property
    def admitted(self) -> bool:
        return self.status == ADMITTED

    def record(self) -> dict:
        out = {"status": self.status,
               "gates_passed": list(self.gates_passed)}
        out.update(self.identity)
        if not self.admitted:
            out["refused_by"] = self.refused_by
            out["it_would_have_been"] = self.would_be
        out["why"] = self.why
        return out


# ------------------------------------------------------------- the gates

def _rel(path) -> str:
    """Repo-relative where possible, so a manifest is readable anywhere."""
    s = str(path).replace("\\", "/")
    for marker in ("/data/", "/engine/", "/tools/", "/tests/", "/docs/"):
        if marker in s:
            return s[s.index(marker) + 1:]
    return s


def _media_type(path) -> str:
    return Path(path).suffix.lower().lstrip(".") if path else ""


def check_path(path) -> tuple:
    """(prohibited_kind, the pattern that caught it) or ("", "")."""
    s = _rel(path).lower()
    answer_file = Path(s).suffix in ANSWER_SUFFIXES
    for pattern, kind, answers_only in PROHIBITED_PATHS:
        if answers_only and not answer_file:
            continue
        hit = pattern.search(s)
        if hit:
            return kind, hit.group(0)
    return "", ""


def _gate_declared(item) -> tuple:
    if not item.input_id or not item.kind:
        return (DECLARED_GATE, "", "an input carries an id and a declared "
                "kind before anything else is asked about it")
    if not item.path and item.content is None:
        return (DECLARED_GATE, "", f"{item.input_id} names neither a file "
                "nor content, so there is nothing to hash and nothing to "
                "check")
    return ()


def _gate_exists(item) -> tuple:
    if item.path and not Path(item.path).exists():
        return (EXISTS_GATE, "", f"{_rel(item.path)} does not exist. A "
                "manifest records what was supplied, and a missing file "
                "was not supplied")
    return ()


def _gate_kind(item) -> tuple:
    if item.kind in PROHIBITED_KINDS:
        return (KIND_GATE, item.kind,
                f"{item.kind} is named in the contract as something a "
                "blind pass never receives")
    if item.kind not in ALLOWED_KINDS:
        return (KIND_GATE, "AN_UNDECLARED_KIND",
                f"{item.kind!r} is not one of the allowed kinds. A "
                "missing rule is not a permissive rule, so it is refused "
                "rather than let through as harmless")
    return ()


def _gate_path(item) -> tuple:
    if not item.path:
        return ()
    try:
        refmap.refuse_if_sealed(item.path)
    except refmap.SealedReferenceError as exc:
        return (PATH_GATE, KNOWN_TARGET_AREA, str(exc))
    kind, hit = check_path(item.path)
    if kind:
        return (PATH_GATE, kind,
                f"{_rel(item.path)} matches {hit!r}, which is where "
                f"{kind} lives in this repository. The path is checked as "
                "well as the declared kind because renaming a file does "
                "not change what is in it")
    for other in (item.origin, item.derived_from):
        if other and "/" in str(other):
            kind, hit = check_path(other)
            if kind:
                return (PATH_GATE, kind,
                        f"it was made from {_rel(other)}, which matches "
                        f"{hit!r}. An image inherits what it was rendered "
                        "from")
    return ()


def _gate_crop(item) -> tuple:
    if item.kind != LOCAL_CROP:
        return ()
    if not item.derived_from:
        return (CROP_BASIS_GATE, "", f"{item.input_id} is a crop that "
                "does not say which image it was cut from")
    if item.crop_basis not in CROP_BASES:
        return (CROP_BASIS_GATE, KNOWN_TARGET_AREA,
                f"{item.crop_basis or 'no basis'} does not say what "
                "decided this box. " + A_CROP_AROUND_THE_ANSWER_IS_THE_ANSWER)
    return ()


def _gate_content(item) -> tuple:
    payload = item.content
    if payload is None and item.path and Path(item.path).suffix.lower() in (
            ".json", ".md", ".txt", ".csv"):
        payload = Path(item.path).read_text(encoding="utf-8",
                                            errors="replace")
    if payload is None:
        return ()
    leaks = bp.scan(payload)
    if leaks:
        where = ", ".join(sorted({x["at"] or x["key"] for x in leaks})[:4])
        return (CONTENT_GATE, KNOWN_TARGET_AREA,
                f"the content carries benchmark-shaped keys or text at "
                f"{where}. " + bp.A_COINCIDENCE_IS_NOT_EVIDENCE)
    return ()


_GATES = ((DECLARED_GATE, _gate_declared), (KIND_GATE, _gate_kind),
          (PATH_GATE, _gate_path), (CROP_BASIS_GATE, _gate_crop),
          (EXISTS_GATE, _gate_exists), (CONTENT_GATE, _gate_content))


def screen(item: Input) -> Decision:
    """Run every gate in order and say what happened, without side effects."""
    passed = []
    for name, fn in _GATES:
        failure = fn(item)
        if failure:
            gate, would_be, why = failure
            return Decision(input_id=item.input_id, kind=item.kind,
                            status=REFUSED, gates_passed=tuple(passed),
                            refused_by=gate, would_be=would_be, why=why,
                            identity=item.identity())
        passed.append(name)
    return Decision(input_id=item.input_id, kind=item.kind,
                    status=ADMITTED, gates_passed=tuple(passed),
                    why=(f"{item.input_id} is {item.kind}, it passed every "
                         "gate, and it is recorded in the manifest by its "
                         "hash"),
                    identity=item.identity())


# --------------------------------------------------------------- the run

@dataclass
class BlindRun:
    """One blind pass, and the record of everything it was handed."""

    run_id: str = ""
    pass_id: str = "A18"
    subject: str = ""          # what was being interpreted
    floor: str = ""
    phase: str = bp.BLIND
    status: str = VALID
    stopped: bool = False
    decisions: list = field(default_factory=list)
    violations: list = field(default_factory=list)
    notes: dict = field(default_factory=dict)

    # -- offering something to the pass ----------------------------------
    def offer(self, item: Input) -> Decision:
        """Screen one input and record the decision either way."""
        self.assert_running()
        decision = screen(item)
        self.decisions.append(decision)
        return decision

    def offer_all(self, items) -> list:
        return [self.offer(i) for i in items]

    @property
    def admitted(self) -> list:
        return [d for d in self.decisions if d.admitted]

    @property
    def refused(self) -> list:
        return [d for d in self.decisions if not d.admitted]

    # -- finding that something already got in ---------------------------
    def in_context(self, *, what: str, where: str = "",
                   detail: str = "") -> None:
        """Prohibited information is IN the context. The run is over.

        This is the other half of the contract. A gate refuses at the
        door; this is what a caller uses when it discovers that the
        answer reached the pass anyway — pasted into a prompt, carried in
        a previous turn, or read from a file nobody screened.
        """
        self.violations.append({
            "what": what, "where": where, "detail": detail,
            "found": "IN_THE_CONTEXT_OF_THE_PASS"})
        self.status = INVALID
        self.stopped = True

    def check_context(self, payload, *, where: str = "") -> bool:
        """Scan an assembled context and invalidate the run if it leaks."""
        leaks = bp.scan(payload)
        if not leaks:
            return True
        self.in_context(
            what=KNOWN_TARGET_AREA, where=where,
            detail="; ".join(sorted({x["at"] or x["key"]
                                     for x in leaks})[:6]))
        return False

    def assert_running(self) -> None:
        if self.stopped or self.status == INVALID:
            raise BlindTestInvalid(
                f"{self.pass_id} run {self.run_id} is {INVALID}: "
                + (self.violations[-1]["what"] if self.violations
                   else "the run was stopped")
                + ". A pass that has seen the answer cannot un-see it, so "
                  "the run stops rather than continuing with what is left")

    # -- the manifest ----------------------------------------------------
    def manifest(self) -> dict:
        body = {
            "MODEL": MODEL,
            "MODEL_HASH": model_hash(),
            "manifest": MANIFEST_NAME.removesuffix(".json"),
            "pass_id": self.pass_id,
            "run_id": self.run_id,
            "subject": self.subject,
            "floor": self.floor,
            "phase": self.phase,
            "status": self.status,
            "run_stopped": self.stopped,
            "counts": {
                "offered": len(self.decisions),
                "admitted": len(self.admitted),
                "refused_at_the_door": len(self.refused),
                "in_context_violations": len(self.violations),
            },
            "inputs_made_available": [d.record() for d in self.admitted],
            "refused_at_the_door": [d.record() for d in self.refused],
            "in_context_violations": list(self.violations),
            "contract": frozen_parameters(),
            "what_this_manifest_is": (
                "every file and every projection made available to "
                f"{self.pass_id} on this run, by hash. A blind run is "
                "reproducible from this list and from nothing else"),
            "a_refusal_is_not_a_contamination":
                A_REFUSAL_IS_NOT_A_CONTAMINATION,
            "notes": dict(self.notes),
        }
        body["MANIFEST_HASH"] = prov.canonical_sha256(body)
        return body


# ------------------------------------------------------- the projections
#
# A prior artifact may hold one fact a blind pass is allowed — which sheet
# is the ground floor — inside a document full of facts it is not. The
# answer is never to hand over the document. It is to project the allowed
# fields out of it, hash the projection, and put THAT in the manifest.

def project(source, keep, *, drop=()) -> dict:
    """A whitelist projection: the named fields, and nothing else.

    A whitelist rather than a blacklist, because a document grows fields
    after the blacklist is written and a blind pass is not the place to
    discover that.
    """
    if not isinstance(source, dict):
        return {}
    return {k: v for k, v in source.items()
            if k in set(keep) and k not in set(drop)}


# The fields of a rule that say what the rule IS. `notes` and `source`
# are dropped: they are where a rule records the argument that produced
# it, and that argument can carry the very numbers under test.
RULE_FIELDS = ("rule_id", "rule_name", "trade", "scope", "rule_kind",
               "country_context", "default_or_mandatory", "unit", "value",
               "required_geometry", "calculation_method", "exceptions",
               "unknown_behavior")


def general_rules(library, *, scopes=()) -> dict:
    """The approved GENERAL rules, projected, with leaky rules withheld.

    A rule that trips the benchmark scan is dropped individually and
    named, so that one rule carrying a number does not cost the pass the
    whole rule book — and so that nobody has to wonder which rules the
    agent actually had.
    """
    rules, withheld = [], []
    for rule in (library or {}).get("rules", ()):
        if scopes and rule.get("scope") not in scopes:
            continue
        projected = project(rule, RULE_FIELDS)
        if bp.scan(projected):
            withheld.append(rule.get("rule_id", ""))
            continue
        rules.append(projected)
    return {
        "library": (library or {}).get("library", ""),
        "library_version": (library or {}).get("library_version", ""),
        "rules": rules,
        # Ids only. The REASON a rule was withheld is itself about the
        # thing being withheld, so it stays in the manifest note and out
        # of the payload the pass receives.
        "withheld_rule_ids": withheld,
        "withheld_by": "THE_CONTENT_GATE",
        "fields_kept": list(RULE_FIELDS),
        "why_notes_and_source_are_dropped": (
            "a rule's notes are where it records the argument that "
            "produced it, and that argument can carry the numbers under "
            "test"),
    }


A_SPEC_ABOUT_THE_SUBJECT_IS_THE_ANSWER = (
    "a specification that describes the very space under test does not "
    "inform the reading, it supplies it. A surveyor on site would have "
    "the spec; a blind pass being tested on whether it can SEE that "
    "space may not have the part that describes it")


def spec_for_a_blind_pass(spec, *, subject_terms=()) -> dict:
    """A project specification, minus the blocks about the spaces on test.

    The rest of the spec stays. A pass being tested on the ground-floor
    open zone still gets the stair and elevator sections, because a
    surveyor on a real job would have them and they say nothing about
    what is being read.
    """
    terms = tuple(t.upper() for t in subject_terms if t)
    kept, withheld = {}, []
    for key, block in (spec or {}).items():
        text = prov.canonical_text({key: block}).upper()
        if terms and any(t in text for t in terms):
            withheld.append(key)
            continue
        kept[key] = block
    kept["withheld_block_ids"] = withheld
    kept["withheld_because"] = "IT_DESCRIBES_A_SPACE_UNDER_TEST"
    return kept
