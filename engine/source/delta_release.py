"""DELTA RELEASE - a frozen accurate-rebar release plus a delta, never a rewritten historical result.

Generic, stdlib only. A delta round (S4.1, S5.1, S6.1, ...) never edits the frozen outputs of its baseline. It reads
them through their freeze manifest (every hash must still match), and writes one DELTA RECORD per change:

    FROZEN_BASELINE  BASELINE_COMPONENT_ID  OLD_STATE  OLD_KNOWN_QUANTITY  NEW_PROJECT_SOURCE  SOURCE_PAGE
    SOURCE_HANDLES   GRAPHIC_EVIDENCE_CLASS  NEW_COMPONENT_MODEL  DELTA_KNOWN_QUANTITY  NEW_BLOCKED_COMPONENTS
    NEW_RELEASE_STATE

Rules enforced here:
  * the frozen known quantity is never subtracted: DELTA_KNOWN_QUANTITY >= 0 (a state correction with no new steel
    is a zero delta, recorded, never hidden);
  * a delta never raises a component to VERIFIED;
  * a positive delta needs a quantity basis the graphic policy allows (engine.source.graphic_evidence): a printed
    dimension (class A), a project-source geometry derivation with all four conditions (class B), or a schedule /
    plan length the graphic only identifies (topology / applicability); a plotted-scale basis is refused;
  * an ownership transfer moves a component to another stage and carries no quantity;
  * conservation: baseline known + sum(delta) == new known.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from engine.source import graphic_evidence as GE

FIELDS = ("FROZEN_BASELINE", "BASELINE_COMPONENT_ID", "OLD_STATE", "OLD_KNOWN_QUANTITY", "NEW_PROJECT_SOURCE",
          "SOURCE_PAGE", "SOURCE_HANDLES", "GRAPHIC_EVIDENCE_CLASS", "NEW_COMPONENT_MODEL", "DELTA_KNOWN_QUANTITY",
          "NEW_BLOCKED_COMPONENTS", "NEW_RELEASE_STATE")

# change kinds
NO_CHANGE = "NO_CHANGE"
SEMANTIC_CORRECTION = "SEMANTIC_CORRECTION"          # the release claim changes, the known quantity does not
PORTION_DECOMPOSITION = "PORTION_DECOMPOSITION"      # one modelled bar split into classified portions
FACET_ADDED = "FACET_ADDED"                          # a missing / found facet is named; state and quantity kept
QUANTITY_RELEASED = "QUANTITY_RELEASED"              # new known steel (lower bound)
TOPOLOGY_RECORDED = "TOPOLOGY_RECORDED"              # link / bar topology found, no quantity from it
OWNERSHIP_TRANSFER = "OWNERSHIP_TRANSFER"            # the component belongs to another stage
CHANGE_KINDS = (NO_CHANGE, SEMANTIC_CORRECTION, PORTION_DECOMPOSITION, FACET_ADDED, QUANTITY_RELEASED,
                TOPOLOGY_RECORDED, OWNERSHIP_TRANSFER)

# release states a delta may write
LOWER_BOUND = "LOWER_BOUND"
BLOCKED_UNQUANTIFIED = "BLOCKED_UNQUANTIFIED"
NOT_APPLICABLE = "NOT_APPLICABLE"
TRANSFERRED_OUT = "TRANSFERRED_OUT"
SOURCE_CONFLICT = "SOURCE_CONFLICT"
PENDING_ENGINEER_CLARIFICATION = "PENDING_ENGINEER_CLARIFICATION"
VERIFIED = "VERIFIED"
UNCHANGED_FROZEN_STATES = (VERIFIED,)                 # a frozen VERIFIED may be carried unchanged, never created
DELTA_STATES = (LOWER_BOUND, BLOCKED_UNQUANTIFIED, NOT_APPLICABLE, TRANSFERRED_OUT, SOURCE_CONFLICT,
                PENDING_ENGINEER_CLARIFICATION)

# quantity bases for a positive delta
BASIS_NONE = "NONE"
BASIS_FROZEN = "FROZEN_SOURCE_QUANTITY"
BASIS_PRINTED = "GRAPHIC_PRINTED_DIMENSION"
BASIS_DERIVED = "GRAPHIC_SOURCE_GEOMETRY_DERIVATION"
BASIS_SCHEDULE = "SCHEDULE_AND_PLAN_GEOMETRY"
BASIS_PLOTTED = "PLOTTED_SCALE"
BASES = (BASIS_NONE, BASIS_FROZEN, BASIS_PRINTED, BASIS_DERIVED, BASIS_SCHEDULE, BASIS_PLOTTED)


class DeltaReleaseError(ValueError):
    pass


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_frozen(manifest_path, root):
    """Every code / input / output hash in a freeze manifest must still match. Returns
    {"manifest": rel path, "manifest_sha256", "engine_commit_stamp", "round", "files_checked"}."""
    manifest_path = Path(manifest_path)
    root = Path(root)
    m = json.loads(manifest_path.read_text(encoding="utf-8"))
    pkg = manifest_path.parent
    n = 0
    for group, base in (("code", root), ("inputs", root), ("outputs", pkg)):
        for rel, h in sorted(m.get(group, {}).items()):
            if sha256(base / rel) != h:
                raise DeltaReleaseError(f"frozen baseline altered: {group} {rel}")
            n += 1
    if n == 0:
        raise DeltaReleaseError("freeze manifest lists no files")
    return {"manifest": str(manifest_path.relative_to(root)), "manifest_sha256": sha256(manifest_path),
            "engine_commit_stamp": m.get("engine_commit_stamp"), "round": m.get("round"), "files_checked": n}


def baseline_label(frozen):
    return f"{frozen['manifest']} ({frozen['engine_commit_stamp']})"


def record(*, delta_id, change_kind, frozen_baseline, baseline_component_id, old_state, old_known_quantity,
           new_project_source, source_page, source_handles, graphic_evidence_class, new_component_model,
           delta_known_quantity, new_blocked_components, new_release_state, quantity_basis=BASIS_NONE,
           derivation_conditions=None, portion="WHOLE_COMPONENT", portion_state="", why="", **extra):
    """Build and validate one delta record. Quantities are kg (None counts as 0 known)."""
    if change_kind not in CHANGE_KINDS:
        raise DeltaReleaseError(f"unknown change kind {change_kind!r}")
    if graphic_evidence_class not in GE.CLASSES and graphic_evidence_class != GE.NO_GRAPHIC_EVIDENCE:
        raise DeltaReleaseError(f"unknown graphic evidence class {graphic_evidence_class!r}")
    if quantity_basis not in BASES:
        raise DeltaReleaseError(f"unknown quantity basis {quantity_basis!r}")
    if quantity_basis == BASIS_PLOTTED:
        raise DeltaReleaseError("a plotted-scale reading is never a quantity basis")
    old = float(old_known_quantity or 0.0)
    delta = float(delta_known_quantity or 0.0)
    if delta < 0:
        raise DeltaReleaseError(f"{delta_id}: a delta never subtracts frozen known steel")
    if new_release_state == VERIFIED and old_state != VERIFIED:
        raise DeltaReleaseError(f"{delta_id}: a delta never raises a component to VERIFIED")
    if new_release_state not in DELTA_STATES + UNCHANGED_FROZEN_STATES:
        raise DeltaReleaseError(f"{delta_id}: unknown release state {new_release_state!r}")
    if new_release_state == VERIFIED and (change_kind != NO_CHANGE or delta):
        raise DeltaReleaseError(f"{delta_id}: only an unchanged frozen VERIFIED may stay VERIFIED")
    if delta > 0:
        if change_kind != QUANTITY_RELEASED:
            raise DeltaReleaseError(f"{delta_id}: new known steel must be a QUANTITY_RELEASED record")
        if new_release_state != LOWER_BOUND:
            raise DeltaReleaseError(f"{delta_id}: a released delta is a LOWER_BOUND")
        if quantity_basis == BASIS_PRINTED and graphic_evidence_class != GE.GRAPHIC_EXPLICIT_DIMENSIONED:
            raise DeltaReleaseError(f"{delta_id}: a printed-dimension basis needs a dimensioned graphic")
        if quantity_basis == BASIS_DERIVED:
            ok, why_not = GE.may_quantify(graphic_evidence_class, derivation_conditions)
            if graphic_evidence_class != GE.GRAPHIC_DERIVED_FROM_SOURCE_GEOMETRY or not ok:
                raise DeltaReleaseError(f"{delta_id}: derived basis refused ({why_not})")
        if quantity_basis in (BASIS_NONE, BASIS_FROZEN):
            raise DeltaReleaseError(f"{delta_id}: a positive delta needs a quantity basis")
    if change_kind == OWNERSHIP_TRANSFER and (delta or new_release_state != TRANSFERRED_OUT):
        raise DeltaReleaseError(f"{delta_id}: a transfer carries no quantity and ends TRANSFERRED_OUT")
    if change_kind == OWNERSHIP_TRANSFER and old:
        raise DeltaReleaseError(f"{delta_id}: a component with known steel cannot be transferred silently")
    rec = {"DELTA_ID": delta_id, "CHANGE_KIND": change_kind, "FROZEN_BASELINE": frozen_baseline,
           "BASELINE_COMPONENT_ID": baseline_component_id, "PORTION": portion, "OLD_STATE": old_state,
           "OLD_KNOWN_QUANTITY": old, "NEW_PROJECT_SOURCE": new_project_source, "SOURCE_PAGE": source_page,
           "SOURCE_HANDLES": source_handles, "GRAPHIC_EVIDENCE_CLASS": graphic_evidence_class,
           "NEW_COMPONENT_MODEL": new_component_model, "PORTION_STATE": portion_state,
           "QUANTITY_BASIS": quantity_basis, "DELTA_KNOWN_QUANTITY": delta, "NEW_KNOWN_QUANTITY": old + delta,
           "NEW_BLOCKED_COMPONENTS": list(new_blocked_components or []), "NEW_RELEASE_STATE": new_release_state,
           "WHY": why}
    for k, v in extra.items():
        rec[k] = v
    return rec


def conservation(baseline_known, records, new_known, tol=1e-6):
    """baseline + sum(delta) == new known, and the frozen known is carried unchanged in OLD_KNOWN_QUANTITY."""
    carried = sum(r["OLD_KNOWN_QUANTITY"] for r in records)
    delta = sum(r["DELTA_KNOWN_QUANTITY"] for r in records)
    checks = {"frozen_known_carried": abs(carried - baseline_known) <= tol,
              "baseline_plus_delta_is_new": abs(baseline_known + delta - new_known) <= tol,
              "no_negative_delta": all(r["DELTA_KNOWN_QUANTITY"] >= 0 for r in records)}
    return {"baseline_known": baseline_known, "carried_known": carried, "delta_known": delta,
            "new_known": new_known, "checks": checks, "all_pass": all(checks.values())}
