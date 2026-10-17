"""Expected physical scope checks (generic internal completeness QA - no reference quantity is read).

The engine asks whether its own model is physically plausible:

  * a founded footprint exists but the ground slab covers only part of it            -> COVERAGE_ANOMALY
  * the paired wall-face network is much longer than the classified wall length      -> COVERAGE_ANOMALY
  * N column occurrences on a floor but concrete emitted for fewer                    -> CONSERVATION_FAILURE
  * N beam tags / face bands but fewer quantified                                     -> COVERAGE_ANOMALY

Each finding names the two internal measures it compared, the ratio and the threshold. Thresholds are parameters with
explicit defaults; they are QA triggers, never quantities. Stdlib only.
"""

from __future__ import annotations

COVERAGE_ANOMALY, CONSERVATION_FAILURE, OK = "COVERAGE_ANOMALY", "CONSERVATION_FAILURE", "OK"
DEFAULT_MIN_RATIO = 0.80


def ratio_check(check_id, covered, expected, *, min_ratio=DEFAULT_MIN_RATIO, what="", kind=COVERAGE_ANOMALY):
    if expected is None or expected <= 0:
        return {"check_id": check_id, "state": "NOT_EVALUABLE", "covered": covered, "expected": expected,
                "what": what}
    r = (covered or 0.0) / expected
    return {"check_id": check_id, "state": OK if r >= min_ratio else kind, "covered": covered, "expected": expected,
            "ratio": round(r, 3), "min_ratio": min_ratio, "what": what,
            "unexplained": round(expected - (covered or 0.0), 3) if r < min_ratio else 0.0}


def count_conservation(check_id, occurrences, emitted, what=""):
    """Counts must be equal: an occurrence without an emitted record is a conservation failure."""
    return {"check_id": check_id, "state": OK if emitted == occurrences else CONSERVATION_FAILURE,
            "occurrences": occurrences, "emitted": emitted, "missing": occurrences - emitted, "what": what}


def ground_slab_vs_footprint(slab_m2, footprint_net_m2, **kw):
    return ratio_check("GROUND_SLAB_FOOTPRINT", slab_m2, footprint_net_m2,
                       what="ground slab area vs founded footprint net of beams / columns", **kw)


def walls_vs_paired_faces(classified_m, paired_m, **kw):
    return ratio_check("WALL_NETWORK", classified_m, paired_m,
                       what="classified wall length vs paired wall-face length", **kw)


def beams_vs_tags(quantified, tags, **kw):
    return ratio_check("BEAM_TAGS", quantified, tags, what="quantified beam occurrences vs beam tags", **kw)


def summarise(findings):
    from collections import Counter
    return {"findings": findings, "by_state": dict(Counter(f["state"] for f in findings))}
