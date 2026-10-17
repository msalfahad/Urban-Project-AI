"""E1.4 — bind every local source file the analytical run actually executed.

THE DEFECT THIS REPLACES

E1_3_FREEZE.json carried CODE_VERSION_HASHES, a list of 33 files kept by
hand. engine/boundary_walk.py - the module that walks every boundary,
selects the room-side face, turns at a wall end and enforces the ring
invariant - was not in it. The freeze did not bind the source of its own
central mechanism, and nothing noticed, because nothing was checking the
list against what the run had actually imported.

MODEL_HASHES was not a substitute. A model_hash() hashes a handful of
chosen constants and strings; it says a module's declared vocabulary has
not changed. It says nothing about the code around them, so the whole
algorithm can be rewritten under a model hash that never moves.

WHAT REPLACES IT

The manifest is GENERATED from the interpreter, not maintained. Whatever
local repository module the run imported is in it, with the sha256 of the
file on disk. A module cannot be forgotten, because nobody lists it.

What is still declared by hand is each module's PURPOSE, and a module
whose purpose nobody declared is recorded as PURPOSE_NOT_DECLARED rather
than left out - an undeclared purpose is a documentation gap, never a
reason to drop a file from provenance.

No compiled file is provenance: a .pyc is a build artefact of a source
file that is itself hashed here.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

MODEL = "PROVENANCE_IS_GENERATED_FROM_WHAT_RAN_NOT_MAINTAINED_BY_HAND_V1"

PURPOSE_NOT_DECLARED = "PURPOSE_NOT_DECLARED"

A_MODEL_HASH_IS_NOT_A_FILE_HASH = (
    "model_hash() hashes a module's declared vocabulary - a few constants "
    "and strings. The algorithm around them can be replaced entirely "
    "without moving it. Only the sha256 of the source file binds what ran")

NO_COMPILED_FILE_IS_PROVENANCE = (
    "a __pycache__ entry is a build artefact of a source file that is "
    "itself hashed here. It is never recorded as provenance in its own "
    "right, and its presence or absence changes nothing")

WHY_IT_IS_GENERATED = (
    "a hand-kept list of hashed files omitted the central mechanism of the "
    "run it was meant to bind. This manifest is read off the interpreter "
    "after the analysis has run, so a module that was imported cannot be "
    "missing from it, and adding a module to the code cannot quietly leave "
    "provenance behind")

# The purposes E1.4 declares. A module absent from here is still hashed.
DECLARED_PURPOSE = {
    "engine.boundary_walk": "boundary walk, room-side face selection, ring invariant",
    "engine.boundary_capability": "semantic role separated from boundary capability",
    "engine.interval_role": "atomic interval semantic roles",
    "engine.atomic_interval": "cutting entities into atomic intervals",
    "engine.column_ownership": "column exposure and clear-face ownership",
    "engine.column_validation": "column existence and derived-geometry self-consistency",
    "engine.gap_ontology": "what a gap between two wall ends is",
    "engine.gap_pass": "classifying every candidate gap against drawing evidence",
    "engine.opening_discovery": "door-first and gap-first opening discovery, reconciled",
    "engine.line_semantics": "visible, overhead, below-cut-plane and annotation linework",
    "engine.label_grouping": "grouping glyphs into label groups",
    "engine.label_anchor": "candidate identity anchors and seed validation",
    "engine.label_ontology": "what a label is and whether it names a space",
    "engine.curve_semantics": "what a curve is, independently of its shape",
    "engine.cad_geometry": "CAD geometry, tracing, noding, openings",
    "engine.cad_adapter": "reading the decoded CAD into primitives",
    "engine.cad_profile": "drawing profile and unit resolution",
    "engine.cad_regions": "drawing region isolation",
    "engine.drawing_region": "drawing region roles and floor assignment",
    "engine.boundary_fragment": "independently established boundary fragments",
    "engine.traversal_geometry": "traversal path against unique boundary against material",
    "engine.ring_qa": "ring continuity, closure and isoperimetric QA",
    "engine.arbitration_dimensions": "physical topology, boundary role and identity arbitration",
    "engine.decision_ledger": "the one ledger every account of a decision derives from",
    "engine.visual_challenger": "cold visual challenge, first generation",
    "engine.visual_challenger_v2": "cold two-stage visual challenge",
    "engine.visual_finding": "what a visual finding affects, and whether it can block",
    "engine.space_status": "physical geometry status against functional identity status",
    "engine.boundary_chain": "the ordered boundary chain vocabulary",
    "engine.edge_relation": "the relation a side of a candidate stands in",
    "engine.deterministic_qa": "deterministic drawing QA state",
    "engine.stair_completeness": "stair assemblies and coverage",
    "engine.raster_qa": "raster corroboration of the source sheet",
    "engine.e1_inputs": "E1 run identity",
    "engine.e1_1_inputs": "E1.1 run identity",
    "engine.e1_2_inputs": "E1.2 run identity",
    "engine.e1_3_inputs": "E1.3 run identity",
    "engine.e1_4_inputs": "E1.4 run identity",
    "engine.e1_region": "region identity",
    "engine.e1_release": "release state",
    "engine.agent_sandbox": "the sealed input sandbox",
    "engine.admission_ledger": "what was admitted to the sandbox and when",
    "engine.blind_input_contract": "the blind input contract",
    "engine.provenance": "canonical hashing",
    "engine.execution_provenance": "this manifest",
    "engine.visible_boundary": "superseded visibility construction, kept for audit",
    "tools.run_e1_2": "E1.2 runner, imported for its frozen helpers",
    "tools.run_e1_3": "E1.3 runner, imported for its frozen helpers",
    "tools.run_e1_4": "E1.4 runner",
}


def model_hash() -> str:
    return hashlib.sha256(MODEL.encode("utf-8")).hexdigest()[:24]


def _local_modules(repo_root):
    root = Path(repo_root).resolve()
    out = {}
    for name, mod in list(sys.modules.items()):
        f = getattr(mod, "__file__", None)
        if not f:
            continue
        p = Path(f)
        if p.suffix != ".py":
            continue                      # no compiled file is provenance
        try:
            rel = p.resolve().relative_to(root)
        except ValueError:
            continue                      # not a local repository module
        if "__pycache__" in rel.parts or "/site-packages/" in str(p):
            continue
        out[name] = rel.as_posix()
    return out


def manifest(repo_root=".", *, loaded_during_run=True) -> dict:
    """Every local repository module the interpreter has imported."""
    root = Path(repo_root).resolve()
    rows, undeclared = [], []
    for name, rel in sorted(_local_modules(root).items()):
        p = root / rel
        purpose = DECLARED_PURPOSE.get(name, PURPOSE_NOT_DECLARED)
        if purpose == PURPOSE_NOT_DECLARED:
            undeclared.append(name)
        rows.append({
            "MODULE_NAME": name,
            "RELATIVE_FILE_PATH": rel,
            "SHA256": hashlib.sha256(p.read_bytes()).hexdigest()
            if p.exists() else "",
            "FILE_IS_PRESENT": p.exists(),
            "LOADED_DURING_RUN": bool(loaded_during_run),
            "PURPOSE": purpose,
            # Imported and therefore hashed, but not declared as part of
            # the E1.4 analysis. Recorded so the manifest is honest about
            # which files the analysis depends on and which merely came
            # along through a package import.
            "DECLARED_FOR_E1_4_ANALYSIS": name in DECLARED_PURPOSE,
        })
    return {
        "MODEL": MODEL,
        "why_it_is_generated": WHY_IT_IS_GENERATED,
        "a_model_hash_is_not_a_file_hash": A_MODEL_HASH_IS_NOT_A_FILE_HASH,
        "no_compiled_file_is_provenance": NO_COMPILED_FILE_IS_PROVENANCE,
        "modules": rows,
        "module_count": len(rows),
        "modules_with_no_declared_purpose": sorted(undeclared),
        "modules_declared_for_the_e1_4_analysis": sum(
            1 for r in rows if r["DECLARED_FOR_E1_4_ANALYSIS"]),
        "modules_imported_but_not_declared_for_the_analysis": sum(
            1 for r in rows if not r["DECLARED_FOR_E1_4_ANALYSIS"]),
        "an_undeclared_purpose_is_not_a_reason_to_omit_a_file": (
            "a module whose purpose nobody declared is still hashed. The "
            "gap is in the documentation, never in the provenance"),
    }


def unhashed_executed_modules(man, repo_root=".") -> list:
    """Local modules the interpreter has now that the manifest does not."""
    have = {r["MODULE_NAME"] for r in man.get("modules", ())}
    return sorted(set(_local_modules(repo_root)) - have)


def assert_every_executed_local_module_is_hashed(man, repo_root=".") -> dict:
    """The freeze gate. A module that ran and is not bound fails the freeze."""
    missing = unhashed_executed_modules(man, repo_root)
    no_hash = sorted(r["MODULE_NAME"] for r in man.get("modules", ())
                     if not r.get("SHA256"))
    if missing or no_hash:
        raise ValueError(
            "EVERY_EXECUTED_LOCAL_ANALYTICAL_MODULE_IS_HASHED = false. "
            f"imported but not in the manifest: {missing}; "
            f"in the manifest with no file hash: {no_hash}. "
            "A freeze may not claim to bind a run whose code it does not "
            "carry")
    return {
        "EVERY_EXECUTED_LOCAL_ANALYTICAL_MODULE_IS_HASHED": True,
        "modules_bound": len(man.get("modules", ())),
    }


def frozen_parameters() -> dict:
    return {
        "MODEL": MODEL,
        "why": {
            "it_is_generated": WHY_IT_IS_GENERATED,
            "a_model_hash_is_not_a_file_hash": A_MODEL_HASH_IS_NOT_A_FILE_HASH,
            "no_compiled_file_is_provenance": NO_COMPILED_FILE_IS_PROVENANCE,
        },
        "declared_purposes": len(DECLARED_PURPOSE),
    }
