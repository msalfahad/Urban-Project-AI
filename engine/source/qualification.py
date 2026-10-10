"""DECODER_QUALIFICATION (R8.4 §11-§13) — a decoder build is qualified for an ENVELOPE, never globally.

A decoder build earns trust only for the source features an independent-parser comparison
actually EXERCISED. A qualification records that envelope; a later source may rely on it only
when the source's own FEATURE PROFILE lies inside it:

    target features  ⊆  qualified envelope          (QualificationEnvelope.covers)

Anything outside — an entity kind never compared, a transform class never exercised, deeper
block nesting, a dynamic block, an xref, a MINSERT, OCS, a handle representation wider than
the one compared — is UNCOVERED, and the parser policy then requires an independent parser for
that source exactly as if no qualification existed.

HANDLE RISK (§13) is judged by REPRESENTATION, never by an object count:
    byte size vs value     a DWG handle's byte size is the minimal size of its value; a value that
                           does not need its declared size lost high bytes (HANDLE_SIZE_VALUE_INCONSISTENT)
    collisions             two objects share a printed own-handle value
    reference resolution   absolute references (codes 2-5) that name no object in the decode
    max size / value       the widest representation present, compared with the envelope's

No project name, file, count threshold or quantity appears here.
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field

from . import observations as O

# transform classes a placed INSERT can exercise
IDENTITY = "IDENTITY"
TRANSLATION = "TRANSLATION"
ROTATION = "ROTATION"
REFLECTION = "REFLECTION"
UNIFORM_SCALE = "UNIFORM_SCALE"
NON_UNIFORM_SCALE = "NON_UNIFORM_SCALE"
OCS_NON_DEFAULT = "OCS_NON_DEFAULT"
TRANSFORM_CLASSES = (IDENTITY, TRANSLATION, ROTATION, REFLECTION, UNIFORM_SCALE, NON_UNIFORM_SCALE, OCS_NON_DEFAULT)

# qualification status
QUALIFIED = "QUALIFIED"
NOT_EXECUTED = "NOT_EXECUTED"
BLOCKED_EXTERNAL_INPUT = "BLOCKED_EXTERNAL_INPUT"
FAILED = "FAILED"
STATUSES = (QUALIFIED, NOT_EXECUTED, BLOCKED_EXTERNAL_INPUT, FAILED)

ABSOLUTE_REF_CODES = frozenset({2, 3, 4, 5})
_EPS = 1e-9


@dataclass(frozen=True)
class HandleRepresentation:
    max_byte_size: int = 0
    max_value: int = 0
    size_value_inconsistent: int = 0     # declared size larger than the value needs (high bytes lost)
    value_collisions: int = 0            # distinct objects sharing one printed own-handle value
    unresolved_absolute_refs: int = 0    # absolute references naming no object of the decode
    objects: int = 0

    def as_dict(self):
        return dict(self.__dict__)


def _min_bytes(v: int) -> int:
    return max(1, (int(v).bit_length() + 7) // 8)


def handle_representation(decode) -> HandleRepresentation:
    """Representation facts of every OWN handle and absolute reference in a D1 (LibreDWG JSON)
    decode. [code, size, value] lists; anything else is ignored (no guess)."""
    objs = decode.get("OBJECTS", []) if isinstance(decode, dict) else []
    own = [o["handle"] for o in objs if isinstance(o.get("handle"), list) and len(o["handle"]) >= 3]
    sizes = [int(h[1]) for h in own]
    vals = [int(h[-1]) for h in own]
    inconsistent = sum(1 for s, v in zip(sizes, vals) if s > _min_bytes(v))
    counts = Counter(vals)
    known = {(int(h[1]), int(h[-1])) for h in own} | set(vals)
    unresolved = 0
    for o in objs:
        for k, ref in o.items():
            if k == "handle" or not isinstance(ref, list) or len(ref) < 3 or not all(isinstance(x, int) for x in ref[:3]):
                continue
            code, size, v = ref[0], ref[1], ref[-1]
            if code in ABSOLUTE_REF_CODES and v and (size, v) not in known and v not in known:
                unresolved += 1
    return HandleRepresentation(max(sizes, default=0), max(vals, default=0), inconsistent,
                                sum(1 for c in counts.values() if c > 1), unresolved, len(own))


@dataclass(frozen=True)
class SourceFeatureProfile:
    """The capabilities a source actually USES (what a decoder must be qualified for)."""
    entity_kinds: frozenset
    transform_classes: frozenset
    max_block_depth: int
    minsert: bool
    dynamic_blocks: bool
    xref: bool
    handle: HandleRepresentation = field(default_factory=HandleRepresentation)

    def as_dict(self):
        return {"entity_kinds": sorted(self.entity_kinds), "transform_classes": sorted(self.transform_classes),
                "max_block_depth": self.max_block_depth, "minsert": self.minsert,
                "dynamic_blocks": self.dynamic_blocks, "xref": self.xref, "handle": self.handle.as_dict()}


def _insert_classes(obs) -> set:
    g = obs.geometry
    out = set()
    sx, sy = (float(g.scale[0]), float(g.scale[1])) if g.scale else (1.0, 1.0)
    if tuple(obs.extrusion or O.DEFAULT_EXTRUSION)[:3] != tuple(O.DEFAULT_EXTRUSION)[:3]:
        out.add(OCS_NON_DEFAULT)
    if abs(float(g.rotation or 0.0)) > _EPS:
        out.add(ROTATION)
    if sx * sy < 0:
        out.add(REFLECTION)
    if abs(abs(sx) - abs(sy)) > _EPS * max(abs(sx), abs(sy), 1.0):
        out.add(NON_UNIFORM_SCALE)
    elif abs(abs(sx) - 1.0) > _EPS:
        out.add(UNIFORM_SCALE)
    if any(abs(float(c)) > _EPS for c in (g.insertion or ())[:2]):
        out.add(TRANSLATION)
    return out or {IDENTITY}


def source_feature_profile(document: O.SourceDocument, decode=None) -> SourceFeatureProfile:
    """Walk model space and every block REACHED from it (depth-first, cycle-safe)."""
    kinds, classes = set(), set()
    flags = {"minsert": False, "dynamic": False, "xref": False}
    max_depth = 0

    def walk(entities, depth, stack):
        nonlocal max_depth
        for obs in entities:
            kinds.add(obs.kind)
            if obs.kind != O.INSERT or not isinstance(obs.geometry, O.InsertGeom):
                continue
            classes.update(_insert_classes(obs))
            if obs.geometry.grid is not None:
                flags["minsert"] = True
            blk = document.blocks.get(obs.geometry.block_key)
            if blk is None or blk.key in stack:
                continue
            if blk.xref is not None:
                flags["xref"] = True
            if blk.anonymous or blk.parent_ref is not None:
                flags["dynamic"] = True
            max_depth = max(max_depth, depth + 1)
            walk(blk.entities, depth + 1, stack | {blk.key})

    walk(document.entities, 0, frozenset())
    for _, obs in document.other_layouts:
        kinds.add(obs.kind)
    return SourceFeatureProfile(frozenset(kinds), frozenset(classes or {IDENTITY}), max_depth, flags["minsert"],
                                flags["dynamic"], flags["xref"],
                                handle_representation(decode) if decode is not None else HandleRepresentation())


@dataclass(frozen=True)
class QualificationEnvelope:
    """What an independent comparison EXERCISED (PASS rows only)."""
    entity_kinds: frozenset = frozenset()
    transform_classes: frozenset = frozenset()
    max_block_depth: int = 0
    minsert: bool = False
    dynamic_blocks: bool = False
    xref: bool = False
    max_handle_bytes: int = 0
    handle_size_value_inconsistency_exercised: bool = False
    handle_collisions_exercised: bool = False

    def covers(self, p: SourceFeatureProfile) -> tuple:
        """() when the profile is inside the envelope, else the uncovered features."""
        out = [f"ENTITY_KIND:{k}" for k in sorted(p.entity_kinds - self.entity_kinds)]
        out += [f"TRANSFORM:{t}" for t in sorted(p.transform_classes - self.transform_classes)]
        if p.max_block_depth > self.max_block_depth:
            out.append(f"BLOCK_DEPTH:{p.max_block_depth}>{self.max_block_depth}")
        for name in ("minsert", "dynamic_blocks", "xref"):
            if getattr(p, name) and not getattr(self, name):
                out.append(f"FEATURE:{name.upper()}")
        h = p.handle
        if h.max_byte_size > self.max_handle_bytes:
            out.append(f"HANDLE_BYTES:{h.max_byte_size}>{self.max_handle_bytes}")
        if h.size_value_inconsistent and not self.handle_size_value_inconsistency_exercised:
            out.append("HANDLE_SIZE_VALUE_INCONSISTENT")
        if h.value_collisions and not self.handle_collisions_exercised:
            out.append("HANDLE_VALUE_COLLISIONS")
        if h.unresolved_absolute_refs:
            out.append("HANDLE_UNRESOLVED_ABSOLUTE_REFERENCES")   # outside every envelope
        return tuple(out)

    def as_dict(self):
        d = dict(self.__dict__)
        d["entity_kinds"], d["transform_classes"] = sorted(self.entity_kinds), sorted(self.transform_classes)
        return d


@dataclass(frozen=True)
class DecoderQualification:
    qualification_id: str
    decoder_route: str
    decoder_binary_sha256: str | None
    status: str
    envelope: QualificationEnvelope = field(default_factory=QualificationEnvelope)
    reference_source_sha256: tuple = ()
    independent_route: str | None = None
    reconciliation_verdict: str | None = None
    non_pass_items: tuple = ()               # ((handle, instance_path, verdict, field_class), ...)
    excluded_capabilities: tuple = ()        # features seen but NOT qualified (non-PASS rows, not exercised)
    evidence: str = ""
    notes: str = ""

    def __post_init__(self):
        if self.status not in STATUSES:
            raise ValueError(self.status)
        if self.status == QUALIFIED and (self.reconciliation_verdict != "PASS" or not self.reference_source_sha256
                                         or not self.independent_route):
            raise ValueError("QUALIFIED needs an independent route, a reference source and a PASS reconciliation")

    def as_dict(self):
        d = dict(self.__dict__)
        d["envelope"] = self.envelope.as_dict()
        d["reference_source_sha256"] = list(self.reference_source_sha256)
        d["non_pass_items"] = [list(x) for x in self.non_pass_items]
        d["excluded_capabilities"] = list(self.excluded_capabilities)
        return d


def qualification_for(decoder_binary_sha256, profile: SourceFeatureProfile | None, qualifications) -> dict:
    """{covered, qualification_id, uncovered, reason}. Fails closed: no profile, no active
    qualification for this build, or any uncovered feature -> covered False."""
    active = [q for q in qualifications if q.status == QUALIFIED and q.decoder_binary_sha256 == decoder_binary_sha256
              and decoder_binary_sha256 is not None]
    if not active:
        others = sorted({q.status for q in qualifications if q.decoder_binary_sha256 == decoder_binary_sha256})
        return {"covered": False, "qualification_id": None, "uncovered": (),
                "reason": "no QUALIFIED envelope for this decoder build" + (f" (status {','.join(others)})" if others else "")}
    if profile is None:
        return {"covered": False, "qualification_id": active[0].qualification_id, "uncovered": ("FEATURE_PROFILE_ABSENT",),
                "reason": "source feature profile not computed; coverage cannot be shown"}
    best = None
    for q in active:
        miss = q.envelope.covers(profile)
        if not miss:
            return {"covered": True, "qualification_id": q.qualification_id, "uncovered": (),
                    "reason": f"source features inside envelope {q.qualification_id}"}
        if best is None or len(miss) < len(best[1]):
            best = (q, miss)
    return {"covered": False, "qualification_id": best[0].qualification_id, "uncovered": best[1],
            "reason": "outside envelope: " + ", ".join(best[1])}


# ====================================================================== V2: capability signatures (R8.5)
# R8.4's envelope (V1 above, kept reproducible) records MARGINAL features: "ARC occurs somewhere" and
# "REFLECTION occurs somewhere". That over-states qualification: ARC-under-translation plus
# LINE-under-reflection does not establish ARC-under-reflection. V2 qualifies INTERACTIONS: one
# signature per realised occurrence, carrying every dimension that selects a different decoder field
# or kernel code path for that occurrence.
#
# Minimum dimensions (and why each is needed):
#   KIND     entity kind with its curve class (LWPOLYLINE_STRAIGHT vs LWPOLYLINE_BULGE, ELLIPSE_FULL vs
#            ELLIPSE_ARC): the bulge / parameter fields are decoded and transformed separately
#   CHAIN    the set of transform classes along the instance chain (TRANSLATION, ROTATION, REFLECTION,
#            UNIFORM_SCALE, NON_UNIFORM_SCALE, OCS_NON_DEFAULT) or DEFAULT_FRAME at top level
#   NET      the composed orientation (NET_REFLECTED / NET_DIRECT): two reflections cancel, one does not
#   DEPTH    exact nesting depth (no buckets: depth 3 is not proven by depth 1)
#   EXT      the entity's own extrusion class (DEFAULT, NEG_Z, TILTED, UNREADABLE)
#   CTX      block contexts on the chain (ARRAY = MINSERT, DYNAMIC_ANONYMOUS, XREF) or '-'
#   VIS      VISIBLE / HIDDEN (hidden geometry is carried, not realised)
#   HANDLE   the occurrence's own handle representation (H12, H3_CONSISTENT, H3_SIZE_VALUE_INCONSISTENT)
# Reference domains get their own signatures: REF=INSERT_LINEAGE and REF=BLOCK_RECORD_LINEAGE with the
# handle classes of the insert and of the block record it names.

QUALIFICATION_SCHEMA_V1 = "URBAN_DECODER_QUALIFICATION_V1"
QUALIFICATION_SCHEMA_V2 = "URBAN_DECODER_QUALIFICATION_V2"
EXERCISED_AND_PASS = "EXERCISED_AND_PASS"
EXERCISED_NONPASS = "EXERCISED_NONPASS"
NOT_EXERCISED = "NOT_EXERCISED"
PASS_VERDICTS = frozenset({"PASS"})          # WARN / BLOCK / KNOWN_LIBRARY_LIMITATION / UNMATCHED / AMBIGUOUS are non-pass
H12, H3_CONSISTENT, H3_INCONSISTENT = "H12", "H3_CONSISTENT", "H3_SIZE_VALUE_INCONSISTENT"
_TRANSFORMS = (TRANSLATION, ROTATION, REFLECTION, UNIFORM_SCALE, NON_UNIFORM_SCALE, OCS_NON_DEFAULT)


def handle_class(handle_id: str | None) -> str:
    """From the D1 handle identity ('v' for 1-2 byte handles, 'v+3B' for a 3-byte one)."""
    if not handle_id or "+" not in str(handle_id):
        return H12
    v, size = str(handle_id).split("+", 1)
    try:
        nbytes = int(size.rstrip("B"))
        return H3_INCONSISTENT if nbytes > _min_bytes(int(v)) else H3_CONSISTENT
    except ValueError:
        return H3_INCONSISTENT


def extrusion_class(extrusion) -> str:
    try:
        x, y, z = (float(v) for v in tuple(extrusion)[:3])
    except (TypeError, ValueError):
        return "UNREADABLE"
    if not all(math.isfinite(v) for v in (x, y, z)) or (x, y, z) == (0.0, 0.0, 0.0):
        return "UNREADABLE"
    n = math.sqrt(x * x + y * y + z * z)
    if abs(x) / n < 1e-9 and abs(y) / n < 1e-9:
        return "DEFAULT" if z > 0 else "NEG_Z"
    return "TILTED"


def _kind_class(obs) -> str:
    g = obs.geometry
    if obs.kind == O.LWPOLYLINE and isinstance(g, O.PolylineGeom):
        return "LWPOLYLINE_BULGE" if any(abs(float(b or 0.0)) > 1e-12 for b in g.bulges) else "LWPOLYLINE_STRAIGHT"
    if obs.kind == O.ELLIPSE and isinstance(g, O.EllipseGeom):
        full = abs(abs(float(g.end_param) - float(g.start_param)) - 2 * math.pi) < 1e-9
        return "ELLIPSE_FULL" if full else "ELLIPSE_ARC"
    if obs.kind == O.UNSUPPORTED_KIND:
        return f"UNSUPPORTED:{obs.source_type}"
    return obs.kind


def _level_orientation(obs) -> int:
    g = obs.geometry
    sx, sy = (float(g.scale[0]), float(g.scale[1])) if g.scale else (1.0, 1.0)
    sign = -1 if sx * sy < 0 else 1
    if extrusion_class(obs.extrusion) == "NEG_Z":
        sign = -sign
    return sign


def signature(kind_class, chain, net_sign, depth, ext, ctx, visible, hcls) -> str:
    ch = "+".join(sorted(chain)) if chain else "DEFAULT_FRAME"
    return (f"KIND={kind_class}|CHAIN={ch}|NET={'NET_REFLECTED' if net_sign < 0 else 'NET_DIRECT'}|DEPTH={depth}"
            f"|EXT={ext}|CTX={'+'.join(sorted(ctx)) if ctx else '-'}|VIS={'VISIBLE' if visible else 'HIDDEN'}"
            f"|HANDLE={hcls}")


def capability_signatures(document: O.SourceDocument, max_depth: int = 16) -> dict:
    """{signature: [(obs_id, instance_path), ...]} for every occurrence a K1 traversal reaches.
    Instance paths follow the kernel's convention (INSERT obs_id + MINSERT cell label)."""
    from .cad.kernel import grid_offsets
    out = {}

    def add(sig, key):
        out.setdefault(sig, []).append(key)

    def walk(entities, chain, net, depth, ctx, visible, path, stack):
        for obs in entities:
            vis = visible and obs.visible
            kc = _kind_class(obs)
            add(signature(kc, chain, net, depth, extrusion_class(obs.extrusion), ctx, vis,
                          handle_class(obs.source_handle)), (obs.obs_id, path))
            if obs.kind != O.INSERT or not isinstance(obs.geometry, O.InsertGeom):
                continue
            g = obs.geometry
            blk = document.blocks.get(g.block_key)
            hb = handle_class(g.block_key[1:] if g.block_key and g.block_key.startswith("H") else None)
            add(f"REF=INSERT_LINEAGE|HANDLE={handle_class(obs.source_handle)}|TARGET={hb}", (obs.obs_id, path))
            if blk is None or blk.key in stack or depth + 1 > max_depth:
                continue
            add(f"REF=BLOCK_RECORD_LINEAGE|TARGET={hb}|DEPTH={depth + 1}", (obs.obs_id, path))
            cls = {c for c in _insert_classes(obs) if c in _TRANSFORMS}
            c2 = set(ctx)
            if g.grid is not None:
                c2.add("ARRAY")
            if blk.anonymous or blk.parent_ref is not None:
                c2.add("DYNAMIC_ANONYMOUS")
            if blk.xref is not None:
                c2.add("XREF")
            for label, _ in grid_offsets(g.grid, g.rotation):
                walk(blk.entities, set(chain) | cls, net * _level_orientation(obs), depth + 1, frozenset(c2), vis,
                     path + (obs.obs_id + label,), stack | {blk.key})

    walk(document.entities, set(), 1, 0, frozenset(), True, (), frozenset())
    return out


@dataclass(frozen=True)
class EquivalenceRule:
    """An explicit, reviewed statement that a qualified signature pattern also covers another.
    `covers(qualified, target)` must be a pure function of the two signatures."""
    equivalence_rule_id: str
    from_pattern: str
    to_class: str
    technical_reason: str
    tests: tuple
    covers: object = None

    def applies(self, qualified: str, target: str) -> bool:
        return bool(self.covers and self.covers(qualified, target))


# No production equivalence is admitted in R8.5: none is proven for BOTH the decoder field path and the
# kernel path. The mechanism is exercised by tests with a test-local rule.
EQUIVALENCE_RULES: tuple = ()


@dataclass(frozen=True)
class DecoderQualificationV2:
    qualification_id: str
    decoder_route: str
    decoder_binary_sha256: str | None
    status: str
    signatures: tuple = ()                 # ((signature, state, pass_count, nonpass_count), ...)
    reference_source_sha256: tuple = ()
    independent_route: str | None = None
    reconciliation_verdict: str | None = None
    equivalence_rules: tuple = ()
    evidence: str = ""
    notes: str = ""
    schema: str = QUALIFICATION_SCHEMA_V2

    def __post_init__(self):
        if self.status not in STATUSES:
            raise ValueError(self.status)
        if self.status == QUALIFIED and (not self.independent_route or not self.reference_source_sha256
                                         or not any(s[1] == EXERCISED_AND_PASS for s in self.signatures)):
            raise ValueError("QUALIFIED V2 needs an independent route, a reference source and >=1 PASS signature")
        for s in self.signatures:
            if s[1] not in (EXERCISED_AND_PASS, EXERCISED_NONPASS):
                raise ValueError(s)

    def passed(self) -> frozenset:
        return frozenset(s[0] for s in self.signatures if s[1] == EXERCISED_AND_PASS)

    def as_dict(self):
        d = dict(self.__dict__)
        d["signatures"] = [dict(zip(("signature", "state", "pass", "nonpass"), s)) for s in self.signatures]
        d["reference_source_sha256"] = list(self.reference_source_sha256)
        d["equivalence_rules"] = [r.equivalence_rule_id for r in self.equivalence_rules]
        return d


def signature_states(sig_keys: dict, verdict_by_key: dict) -> tuple:
    """Per signature: EXERCISED_AND_PASS only if EVERY occurrence carrying it was compared and PASSED.
    One non-pass (WARN, BLOCK, limitation, unmatched, ambiguous, or not compared) -> EXERCISED_NONPASS.
    No percentage: 999 passes and one failure is NONPASS."""
    rows = []
    for sig in sorted(sig_keys):
        keys = sig_keys[sig]
        ok = sum(1 for k in keys if verdict_by_key.get(k) in PASS_VERDICTS)
        rows.append((sig, EXERCISED_AND_PASS if ok == len(keys) and keys else EXERCISED_NONPASS, ok, len(keys) - ok))
    return tuple(rows)


def coverage_v2(target_signatures, qualifications, decoder_binary_sha256, rules=EQUIVALENCE_RULES) -> dict:
    """{covered, uncovered: [(signature, NOT_EXERCISED|EXERCISED_NONPASS)], via_equivalence, qualification_ids}."""
    active = [q for q in qualifications if isinstance(q, DecoderQualificationV2) and q.status == QUALIFIED
              and decoder_binary_sha256 is not None and q.decoder_binary_sha256 == decoder_binary_sha256]
    passed = frozenset().union(*(q.passed() for q in active)) if active else frozenset()
    nonpass = frozenset(s[0] for q in active for s in q.signatures if s[1] == EXERCISED_NONPASS)
    uncovered, via = [], []
    for t in sorted(set(target_signatures)):
        if t in passed:
            continue
        rule = next((r for r in rules for p in passed if r.applies(p, t)), None)
        if rule is not None:
            via.append((t, rule.equivalence_rule_id))
            continue
        uncovered.append((t, EXERCISED_NONPASS if t in nonpass else NOT_EXERCISED))
    return {"covered": bool(active) and not uncovered, "uncovered": uncovered, "via_equivalence": via,
            "qualification_ids": [q.qualification_id for q in active],
            "reason": ("no QUALIFIED V2 record for this decoder build" if not active else
                       "all target signatures qualified" if not uncovered else
                       f"{len(uncovered)} target signatures not qualified")}
