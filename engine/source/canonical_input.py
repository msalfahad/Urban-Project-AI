"""CANONICAL_MEASUREMENT_INPUT (R8.7): the one input a deterministic measurement method receives, and the
fail-closed check of the provenance each method declares it needs.

Why it exists
    Identical geometry with lossily mapped provenance (block identity blanked, part identity collapsed) silently
    changed a room from 36.37 to 25.09 m2 in a real drawing. Geometry alone is not a measurement input. A method
    therefore DECLARES the fields it consumes (MethodContract) and `validate` refuses the input when any declared
    field is absent, duplicated, cross-revision or unresolved. Nothing is substituted: no "", no None, no first
    match, no nearest object, no coordinate-derived identity.

Identity
    A part's identity is source-derived: SOURCE_REVISION_ID + SOURCE_HANDLE + INSTANCE_PATH (insert handles) +
    PART_KIND + PART_INDEX (the part's ordinal among the parts of that kind realised from one source entity
    occurrence, in the source's own vertex order). Coordinates verify; they never identify.

Block identity
    Each instance-path step carries the INSERT handle and the BLOCK RECORD handle. A block name is presentation
    metadata only.

Project-agnostic: no project, file or person names; stdlib only.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

# visibility of one record in the measured view
VISIBLE = "VISIBLE"
HIDDEN_SOURCE = "HIDDEN_SOURCE"                     # the source's own invisibility flag
HIDDEN_DYNAMIC_STATE = "HIDDEN_DYNAMIC_STATE"        # hidden by a resolved dynamic-block visibility state
VISIBILITY_UNRESOLVED = "VISIBILITY_UNRESOLVED"     # e.g. under a dynamic block whose state was not read
VISIBILITY_STATES = (VISIBLE, HIDDEN_SOURCE, HIDDEN_DYNAMIC_STATE, VISIBILITY_UNRESOLVED)

# validation outcomes
COMPLETE = "COMPLETE"
METHOD_INPUT_INCOMPLETE = "METHOD_INPUT_INCOMPLETE"
SOURCE_REVISION_MISMATCH = "SOURCE_REVISION_MISMATCH"
REGION_NOT_SELECTED = "REGION_NOT_SELECTED"

# region membership of a record (assigned by the builder that clips to a region)
IN_REGION = "SELECTED_MEASUREMENT_REGION"
REVIEW_REQUIRED = "REVIEW_REQUIRED"                 # crosses the region boundary or cannot be placed
OUTSIDE_REGION = "OUTSIDE_SELECTED_MEASUREMENT_REGION"

# anchor kinds of a source revision
EXACT_SOURCE = "EXACT_SOURCE"                       # the authored file itself (e.g. the DWG) is hashed
DERIVED_PENDING_SOURCE = "DERIVED_PENDING_SOURCE"   # only a derived file (e.g. a DXF) is hashed; source awaited


@dataclass(frozen=True)
class SourceRevision:
    revision_id: str
    anchor_kind: str
    anchor_sha256: str
    drawing_lineage: str | None = None              # e.g. the drawing's lineage GUID
    status: str = ""


@dataclass(frozen=True)
class LineageStep:
    insert_handle: str | None
    block_record_handle: str | None
    block_name: str | None = None                   # presentation only; never identity


@dataclass(frozen=True)
class SourceIdentity:
    revision_id: str | None
    source_handle: str | None
    instance_handles: tuple | None
    part_kind: str | None
    part_index: int | None

    @property
    def key(self) -> str | None:
        """The durable identity string, or None when any component is missing (never a partial key)."""
        if (not self.revision_id or not self.source_handle or self.instance_handles is None
                or not self.part_kind or self.part_index is None):
            return None
        return "|".join((self.revision_id, "H" + self.source_handle, "/".join(self.instance_handles),
                         self.part_kind, str(self.part_index)))


@dataclass(frozen=True)
class CanonicalPart:
    """One realised curve. geometry: SEGMENT (x1, y1, x2, y2); ARC (cx, cy, r, a0, a1) counter-clockwise radians;
    CIRCLE (cx, cy, r); ELLIPTICAL_ARC (cx, cy, ux, uy, vx, vy, t0, t1)."""
    identity: SourceIdentity
    kind: str
    geometry: tuple
    layer: str | None
    visibility: str
    lineage: tuple                                   # LineageStep per instance-path level
    obs_id: str | None = None
    entity_type: str | None = None
    region: str = IN_REGION


@dataclass(frozen=True)
class PlacedText:
    identity: SourceIdentity
    value: str | None
    x: float | None
    y: float | None
    height: float | None
    layer: str | None
    visibility: str
    lineage: tuple
    entity_type: str | None = None
    region: str = IN_REGION


@dataclass(frozen=True)
class PlacedDimension:
    """Dimension EVIDENCE: what the author measured and printed. Never physical wall geometry."""
    identity: SourceIdentity
    definition_points: tuple | None                  # local (block) coordinates, as authored
    placed_points: tuple | None                      # ((x1, y1), (x2, y2)) in world coordinates
    measurement: float | None                        # the authored / stored measurement
    user_text: str | None
    dimlfac: float | None
    dimension_type: str | None                       # source object type code (e.g. '21' linear), not a style
    layer: str | None
    visibility: str
    lineage: tuple
    style: str | None = None                         # dimension style name (presentation)
    region: str = IN_REGION


@dataclass(frozen=True)
class CanonicalMeasurementInput:
    revision: SourceRevision | None
    region_id: str | None
    frame_id: str | None
    unit_native_to_mm: float | None
    unit_claim_id: str | None
    parts: tuple = ()
    texts: tuple = ()
    dimensions: tuple = ()
    region_review: dict = field(default_factory=dict)  # {record key: REVIEW_REQUIRED reason} found while clipping
    notes: dict = field(default_factory=dict)


@dataclass(frozen=True)
class MethodExclusion:
    """R8.8: a method may leave a part KIND unconsumed only with authority. `allowed_roles` names the geometry roles
    (geometry_role) that positively establish an occurrence as irrelevant to this method's domain; every excluded
    part must carry one of them, or the input is METHOD_INPUT_INCOMPLETE. UNSUPPORTED_BY_METHOD is never read as
    IRRELEVANT_TO_QUANTITY."""
    kind: str
    domain: str
    reason: str
    authority: str
    allowed_roles: tuple = ()


@dataclass(frozen=True)
class MethodContract:
    """What one method consumes. Only declared fields are required; a field a method does not read is not."""
    method_id: str
    version: str
    input_fields: tuple = ("revision", "region_id")
    part_fields: tuple = ()
    text_fields: tuple = ()
    dimension_fields: tuple = ()
    accepted_part_kinds: tuple = ("SEGMENT", "ARC", "CIRCLE")
    declared_exclusions: dict = field(default_factory=dict)    # R8.7 bare {kind: reason}: NO authority (R8.8)
    visibility_relevant: bool = True
    region_review_blocks: bool = True
    evidence: dict = field(default_factory=dict)                 # {field: ablation evidence}
    exclusions: tuple = ()                                        # R8.8 MethodExclusion records (role authority)
    hidden_excluded: bool = False                                 # R8.8: HIDDEN_* records are not consumed


# ---------------------------------------------------------------- field readers (None = absent)
def _blank(v) -> bool:
    return v is None or (isinstance(v, str) and not v.strip())


def _block_identity(rec):
    """Every instance-path level carries an INSERT handle and a BLOCK RECORD handle, and the insert handles are
    the identity's own instance path. Anything else is absent (None) or ambiguous (False)."""
    path = rec.identity.instance_handles
    if path is None or rec.lineage is None:
        return None
    if len(rec.lineage) != len(path):
        return None
    for step, h in zip(rec.lineage, path):
        if _blank(step.insert_handle) or _blank(step.block_record_handle):
            return None
        if step.insert_handle != h:
            return False
    return True


COMMON_READERS = {
    "source_revision_id": lambda r: r.identity.revision_id,
    "source_handle": lambda r: r.identity.source_handle,
    "instance_path": lambda r: r.identity.instance_handles,
    "block_identity": _block_identity,
    "layer": lambda r: r.layer,
    "visibility": lambda r: r.visibility,
}
PART_READERS = dict(COMMON_READERS, **{
    "source_part_id": lambda r: r.identity.key,
    "part_index": lambda r: r.identity.part_index,
    "curve_kind": lambda r: r.kind,
    "geometry": lambda r: r.geometry if r.geometry and all(v is not None for v in r.geometry) else None,
})
TEXT_READERS = dict(COMMON_READERS, **{
    "text_identity": lambda r: r.identity.key,
    "text_value": lambda r: r.value,
    "world_placement": lambda r: None if r.x is None or r.y is None else (r.x, r.y),
    "text_height": lambda r: r.height,
})
DIMENSION_READERS = dict(COMMON_READERS, **{
    "dimension_identity": lambda r: r.identity.key,
    "definition_points": lambda r: r.definition_points,
    "placed_points": lambda r: r.placed_points,
    "measurement": lambda r: r.measurement,
    "user_text": lambda r: r.user_text,           # "" is a valid user text (no override): only None is absent
    "dimlfac": lambda r: r.dimlfac,
    "dimension_type": lambda r: r.dimension_type,
})
INPUT_READERS = {
    "revision": lambda i: i.revision.anchor_sha256 if i.revision is not None else None,
    "region_id": lambda i: i.region_id,
    "frame_id": lambda i: i.frame_id,
    "unit_native_to_mm": lambda i: i.unit_native_to_mm,
    "unit_claim_id": lambda i: i.unit_claim_id,
}
IDENTITY_FIELDS = {"parts": "source_part_id", "texts": "text_identity", "dimensions": "dimension_identity"}
OPTIONAL_STRING_FIELDS = {"user_text"}


def _check(collection, records, fields, readers, out, rev_id):
    missing, ambiguous = Counter(), Counter()
    examples = out["examples"]
    for r in records:
        for f in fields:
            v = readers[f](r)
            absent = v is None if f in OPTIONAL_STRING_FIELDS else _blank(v)     # () and 0 are present values
            if f == "block_identity" and v is False:
                ambiguous[f"{collection}.{f}"] += 1
                examples.setdefault(f"{collection}.{f}", r.identity.key or repr(r.identity))
            elif absent:
                missing[f"{collection}.{f}"] += 1
                examples.setdefault(f"{collection}.{f}", r.identity.key or repr(r.identity))
        if r.identity.revision_id is not None and rev_id is not None and r.identity.revision_id != rev_id:
            out["revision_conflicts"].append({"collection": collection, "record": r.identity.key,
                                              "record_revision": r.identity.revision_id, "input_revision": rev_id})
    key_field = IDENTITY_FIELDS[collection]
    if key_field in fields:
        keys = Counter(readers[key_field](r) for r in records if readers[key_field](r) is not None)
        dup = {k: n for k, n in keys.items() if n > 1}
        if dup:
            ambiguous[f"{collection}.{key_field}"] += sum(dup.values())
            examples.setdefault(f"{collection}.{key_field}", sorted(dup)[0])
    for k, n in missing.items():
        out["missing_fields"][k] = n
    for k, n in ambiguous.items():
        out["ambiguous_fields"][k] = n


HIDDEN_STATES = (HIDDEN_SOURCE, HIDDEN_DYNAMIC_STATE)
EXCLUSION_WITHOUT_AUTHORITY = "EXCLUSION_WITHOUT_ROLE_AUTHORITY"


def validate(inp: CanonicalMeasurementInput, contract: MethodContract, *, expected_revision_id: str | None = None,
             selected_region_id: str | None = None, roles: dict | None = None) -> dict:
    """The fail-closed check. Returns {state, missing_fields, ambiguous_fields, revision_conflicts,
    region_conflicts, visibility_unresolved, unsupported_part_kinds, excluded_by_declaration,
    exclusion_without_authority, hidden_excluded, examples}.

    R8.8: `roles` ({part key: object with .role}) is the role authority for MethodExclusion records. A part of an
    excluded kind is excluded only when its role is one the exclusion allows; otherwise it is counted under
    exclusion_without_authority and the input is METHOD_INPUT_INCOMPLETE. A bare R8.7 `declared_exclusions` entry
    carries no authority at all. With `hidden_excluded`, HIDDEN_SOURCE / HIDDEN_DYNAMIC_STATE records are not
    consumed (listed, never checked); VISIBILITY_UNRESOLVED always counts."""
    out = {"method_id": contract.method_id, "contract_version": contract.version, "missing_fields": {},
           "ambiguous_fields": {}, "revision_conflicts": [], "region_conflicts": [], "visibility_unresolved": {},
           "unsupported_part_kinds": {}, "excluded_by_declaration": {}, "exclusion_without_authority": {},
           "hidden_excluded": {}, "region_review_required": 0, "examples": {}}
    for f in contract.input_fields:
        if _blank(INPUT_READERS[f](inp)):
            out["missing_fields"][f"input.{f}"] = 1
    rev_id = inp.revision.revision_id if inp.revision is not None else None
    if expected_revision_id is not None and rev_id != expected_revision_id:
        out["revision_conflicts"].append({"collection": "input", "record": None, "record_revision": rev_id,
                                          "input_revision": expected_revision_id})
    if selected_region_id is not None and inp.region_id != selected_region_id:
        out["region_conflicts"].append({"input_region": inp.region_id, "selected_region": selected_region_id})

    def visible(recs, name):
        if not contract.hidden_excluded:
            return list(recs)
        keep = []
        for r in recs:
            if r.visibility in HIDDEN_STATES:
                out["hidden_excluded"][name] = out["hidden_excluded"].get(name, 0) + 1
            else:
                keep.append(r)
        return keep
    ex_by_kind = {e.kind: e for e in contract.exclusions}
    parts = []
    for p in visible(inp.parts, "parts"):
        ex = ex_by_kind.get(p.kind)
        if ex is not None:
            a = (roles or {}).get(p.identity.key)
            role = getattr(a, "role", None)
            if role is not None and role in ex.allowed_roles:
                out["excluded_by_declaration"][p.kind] = out["excluded_by_declaration"].get(p.kind, 0) + 1
            else:
                k = f"{p.kind}:{role or 'NO_ROLE'}"
                out["exclusion_without_authority"][k] = out["exclusion_without_authority"].get(k, 0) + 1
                out["examples"].setdefault(f"exclusion.{p.kind}", p.identity.key or repr(p.identity))
            continue
        if p.kind in contract.declared_exclusions:
            k = f"{p.kind}:BARE_DECLARATION"
            out["exclusion_without_authority"][k] = out["exclusion_without_authority"].get(k, 0) + 1
            out["examples"].setdefault(f"exclusion.{p.kind}", p.identity.key or repr(p.identity))
            continue
        if p.kind not in contract.accepted_part_kinds:
            out["unsupported_part_kinds"][p.kind] = out["unsupported_part_kinds"].get(p.kind, 0) + 1
        parts.append(p)
    texts, dims = visible(inp.texts, "texts"), visible(inp.dimensions, "dimensions")
    _check("parts", parts, contract.part_fields, PART_READERS, out, rev_id)
    _check("texts", texts, contract.text_fields, TEXT_READERS, out, rev_id)
    _check("dimensions", dims, contract.dimension_fields, DIMENSION_READERS, out, rev_id)
    if contract.visibility_relevant:
        for name, recs in (("parts", parts), ("texts", texts), ("dimensions", dims)):
            bad = Counter(r.visibility for r in recs if r.visibility != VISIBLE)
            if bad:
                out["visibility_unresolved"][name] = dict(bad)
    out["region_review_required"] = len(inp.region_review)
    if out["revision_conflicts"]:
        state = SOURCE_REVISION_MISMATCH
    elif out["region_conflicts"]:
        state = REGION_NOT_SELECTED
    elif (out["missing_fields"] or out["ambiguous_fields"] or out["visibility_unresolved"]
          or out["unsupported_part_kinds"] or out["exclusion_without_authority"]
          or (contract.region_review_blocks and inp.region_review)):
        state = METHOD_INPUT_INCOMPLETE
    else:
        state = COMPLETE
    out["state"] = state
    return out


def guarded_measure(inp: CanonicalMeasurementInput, contract: MethodContract, method, **expect) -> dict:
    """Run `method(inp)` only on a COMPLETE input. Otherwise the quantity is None: never a fallback value."""
    v = validate(inp, contract, **expect)
    if v["state"] != COMPLETE:
        return {"state": v["state"], "quantity": None, "validation": v}
    return {"state": COMPLETE, "quantity": method(inp), "validation": v}


def contract_record(c: MethodContract) -> dict:
    return {"method_id": c.method_id, "version": c.version, "input_fields": list(c.input_fields),
            "part_fields": list(c.part_fields), "text_fields": list(c.text_fields),
            "dimension_fields": list(c.dimension_fields), "accepted_part_kinds": list(c.accepted_part_kinds),
            "declared_exclusions": dict(c.declared_exclusions), "visibility_relevant": c.visibility_relevant,
            "region_review_blocks": c.region_review_blocks, "evidence": dict(c.evidence),
            "exclusions": [{"kind": e.kind, "domain": e.domain, "reason": e.reason, "authority": e.authority,
                            "allowed_roles": list(e.allowed_roles)} for e in c.exclusions],
            "hidden_excluded": c.hidden_excluded}


SCHEMA = {
    "SCHEMA": "URBAN_CANONICAL_MEASUREMENT_INPUT_V1",
    "input": {"revision": "SourceRevision (revision_id, anchor_kind EXACT_SOURCE | DERIVED_PENDING_SOURCE, anchor_sha256, "
                          "drawing_lineage, status)",
              "region_id": "the selected measurement region", "frame_id": "measurement frame id",
              "unit_native_to_mm": "from an owner / project claim scoped to this revision", "unit_claim_id": "that claim"},
    "identity": "revision_id | H<source handle> | insert handles joined by '/' | part kind | part index; "
                "None when any component is missing (never a partial key); coordinates are verification only",
    "lineage_step": "insert_handle + block_record_handle (+ block_name, presentation only)",
    "visibility_states": list(VISIBILITY_STATES),
    "region_membership": [IN_REGION, REVIEW_REQUIRED, OUTSIDE_REGION],
    "records": {"parts": sorted(PART_READERS), "texts": sorted(TEXT_READERS), "dimensions": sorted(DIMENSION_READERS)},
    "outcomes": [COMPLETE, METHOD_INPUT_INCOMPLETE, SOURCE_REVISION_MISMATCH, REGION_NOT_SELECTED],
    "exclusion_contract": "R8.8 MethodExclusion(kind, domain, reason, authority, allowed_roles): an excluded part must "
                          "carry an allowed geometry role; a bare declaration has no authority",
    "rule": "a method declares its fields; any declared field absent, duplicated, cross-revision or unresolved -> "
            "no quantity; nothing is substituted",
}
