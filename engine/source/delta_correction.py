"""DELTA CORRECTION (ERRATA) - an explicit correction layer over a frozen delta release (generic, stdlib only).

A normal delta round (engine.source.delta_release) can only ADD known steel: its records refuse a negative delta,
and that rule stays unchanged. When an audit finds that a released quantity did not have the authority it was
released with, the frozen delta is not edited. A separate CORRECTION_ERRATA record is written instead:

    ORIGINAL_DELTA_COMPONENT_ID  ORIGINAL_KG  CORRECTION_REASON  SOURCE_EVIDENCE  NEW_AUTHORITY_STATE
    NEW_RELEASE_STATE            CORRECTION_KG  RETAINED_KG

Rules:
  * an erratum never adds steel: CORRECTION_KG <= 0; new steel needs a release round;
  * RETAINED_KG = ORIGINAL_KG + CORRECTION_KG, with 0 <= RETAINED_KG <= ORIGINAL_KG;
  * only a SOURCE_DERIVED_CUT_LENGTH or a PROVEN_LOWER_BOUND may keep kg; a MODELLED_POLYGONAL_EQUIVALENT, QA_ONLY
    or REJECT_FOR_MASS quantity keeps none (it may be reported as a QA value, never as known steel);
  * conservation: original known + sum(CORRECTION_KG) == corrected known.

Link geometry used to decide the authority of a sharp-corner link path:

  sharp_loop_mm(W, T)        = 2W + 2T                      (centreline rectangle, corners sharp)
  rounded_loop_mm(W, T, R)   = 2W + 2T - (8 - 2 pi) R       (same envelope, four 90-degree bends of centreline radius R)
  corner_deficit_mm(R)       = (8 - 2 pi) R  > 0 for every R > 0

Each sharp corner counts 2R of path; its arc is (pi / 2) R. So a physically bent closed loop is always shorter
than the sharp polygon of the same envelope. The sharp path is therefore NOT a lower bound unless R is bounded and
the deficit is deducted. Unknown hooks or closure extensions can never be used to cover the deficit.
"""

from __future__ import annotations

import math

RECORD_TYPE = "CORRECTION_ERRATA"
FIELDS = ("ORIGINAL_DELTA_COMPONENT_ID", "ORIGINAL_KG", "CORRECTION_REASON", "SOURCE_EVIDENCE", "NEW_AUTHORITY_STATE",
          "NEW_RELEASE_STATE", "CORRECTION_KG", "RETAINED_KG")

SOURCE_DERIVED_CUT_LENGTH = "SOURCE_DERIVED_CUT_LENGTH"
PROVEN_LOWER_BOUND = "PROVEN_LOWER_BOUND"
MODELLED_POLYGONAL_EQUIVALENT = "MODELLED_POLYGONAL_EQUIVALENT"
QA_ONLY = "QA_ONLY"
REJECT_FOR_MASS = "REJECT_FOR_MASS"
AUTHORITY_STATES = (SOURCE_DERIVED_CUT_LENGTH, PROVEN_LOWER_BOUND, MODELLED_POLYGONAL_EQUIVALENT, QA_ONLY,
                    REJECT_FOR_MASS)
RETAINING_STATES = (SOURCE_DERIVED_CUT_LENGTH, PROVEN_LOWER_BOUND)

LOWER_BOUND = "LOWER_BOUND"
BLOCKED_UNQUANTIFIED = "BLOCKED_UNQUANTIFIED"
RELEASE_STATES = (LOWER_BOUND, BLOCKED_UNQUANTIFIED)
TOL = 1e-9


class CorrectionError(ValueError):
    pass


# ------------------------------------------------------------------ geometry
def _envelope(W, T):
    if W is None or T is None or W <= 0 or T <= 0:
        raise CorrectionError("the link envelope needs positive centreline sides")


def sharp_loop_mm(W, T):
    _envelope(W, T)
    return 2.0 * W + 2.0 * T


def corner_deficit_mm(R):
    if R is None or R < 0:
        raise CorrectionError("bend radius must be a known non-negative number")
    return (8.0 - 2.0 * math.pi) * R


def rounded_loop_mm(W, T, R):
    """Closed loop in a W x T centreline envelope with four 90-degree bends of centreline radius R."""
    _envelope(W, T)
    if R is None or R < 0 or R > min(W, T) / 2.0:
        raise CorrectionError("bend radius must lie in [0, min(W, T) / 2]")
    return sharp_loop_mm(W, T) - corner_deficit_mm(R)


def corner_lengths_mm(R):
    """(sharp corner path, arc) for one 90-degree corner of centreline radius R."""
    if R is None or R < 0:
        raise CorrectionError("bend radius must be a known non-negative number")
    return 2.0 * R, math.pi * R / 2.0


def classify_link_path(*, bend_radius_mm=None, bend_radius_max_mm=None, hook_length_known=False,
                       closure_known=False, envelope_exact=False):
    """Authority of a sharp-corner link path.

    * SOURCE_DERIVED_CUT_LENGTH: bend radius, hooks, closure and the envelope are all project-source facts;
    * PROVEN_LOWER_BOUND: the envelope is exact and a project source bounds R from above (R <= R_max). The bound is
      then rounded_loop(R_max), with hooks taken as zero. It is never the sharp loop itself;
    * MODELLED_POLYGONAL_EQUIVALENT: anything else. Unknown hooks never promote the path."""
    if envelope_exact and bend_radius_mm is not None and hook_length_known and closure_known:
        return SOURCE_DERIVED_CUT_LENGTH
    if envelope_exact and (bend_radius_mm is not None or bend_radius_max_mm is not None):
        return PROVEN_LOWER_BOUND
    return MODELLED_POLYGONAL_EQUIVALENT


# ------------------------------------------------------------------ records
def correction(*, correction_id, original_delta_component_id, original_kg, correction_kg, correction_reason,
               source_evidence, new_authority_state, new_release_state, **extra):
    if new_authority_state not in AUTHORITY_STATES:
        raise CorrectionError(f"{correction_id}: unknown authority state {new_authority_state!r}")
    if new_release_state not in RELEASE_STATES:
        raise CorrectionError(f"{correction_id}: unknown release state {new_release_state!r}")
    orig = float(original_kg or 0.0)
    corr = float(correction_kg or 0.0)
    if orig < 0:
        raise CorrectionError(f"{correction_id}: original kg cannot be negative")
    if corr > TOL:
        raise CorrectionError(f"{correction_id}: an erratum never adds steel (use a release round)")
    retained = orig + corr
    if retained < -1e-6:
        raise CorrectionError(f"{correction_id}: a correction cannot remove more than was released")
    retained = max(retained, 0.0)
    if new_authority_state not in RETAINING_STATES and retained > 1e-6:
        raise CorrectionError(f"{correction_id}: {new_authority_state} keeps no known steel")
    if retained > 1e-6 and new_release_state != LOWER_BOUND:
        raise CorrectionError(f"{correction_id}: retained steel stays a LOWER_BOUND")
    if retained <= 1e-6 and new_release_state != BLOCKED_UNQUANTIFIED:
        raise CorrectionError(f"{correction_id}: a fully corrected mass is BLOCKED_UNQUANTIFIED")
    if not str(correction_reason).strip() or not source_evidence:
        raise CorrectionError(f"{correction_id}: a correction states its reason and evidence")
    rec = {"CORRECTION_ID": correction_id, "RECORD_TYPE": RECORD_TYPE,
           "ORIGINAL_DELTA_COMPONENT_ID": original_delta_component_id, "ORIGINAL_KG": orig,
           "CORRECTION_REASON": correction_reason, "SOURCE_EVIDENCE": source_evidence,
           "NEW_AUTHORITY_STATE": new_authority_state, "NEW_RELEASE_STATE": new_release_state,
           "CORRECTION_KG": corr, "RETAINED_KG": retained}
    rec.update(extra)
    return rec


def conservation(original_known, corrections, corrected_known, tol=1e-6):
    corr = sum(c["CORRECTION_KG"] for c in corrections)
    checks = {"original_plus_correction_is_corrected": abs(original_known + corr - corrected_known) <= tol,
              "no_positive_correction": all(c["CORRECTION_KG"] <= TOL for c in corrections),
              "retained_plus_removed_is_original": all(abs(c["RETAINED_KG"] - c["CORRECTION_KG"] - c["ORIGINAL_KG"])
                                                       <= tol for c in corrections)}
    return {"original_known": original_known, "correction_kg": corr, "corrected_known": corrected_known,
            "checks": checks, "all_pass": all(checks.values())}


def policy_record():
    return {"record_type": RECORD_TYPE, "fields": list(FIELDS), "authority_states": list(AUTHORITY_STATES),
            "retaining_states": list(RETAINING_STATES),
            "geometry": {"sharp_loop": "2W + 2T", "rounded_loop": "2W + 2T - (8 - 2 pi) R",
                         "corner": "sharp 2R vs arc (pi / 2) R"},
            "rules": ["an erratum never adds steel", "only a source-derived cut length or a proven lower bound "
                      "keeps kg", "unknown hooks / closures never prove a lower bound",
                      "original known + corrections == corrected known"]}
