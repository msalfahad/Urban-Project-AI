"""Run P7757 as a supervised development set and report the geometry effect.

    python3 -m tools.run_supervised_benchmark \
        data/golden/7757/source_c/P7757_ARCHITECTURAL.dwg \
        --decode-json data/runs/cad_convert/P7757_ARCHITECTURAL.json \
        --json data/runs/7757/P7757_SUPERVISED_GEOMETRY.json

This is the step-5 stop in §16: the geometry result, reported on its own,
before any trade or BOQ layer can hide it. Three scoreboards are printed
separately and never combined.

No Excel, no take-off total, no manual measurement and no structural or
sanitary quantity is read. The owner's disclosed figures are carried in
`supervised_benchmark` as training examples and are reported beside the
engine's own without being optimised against.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from engine import cad_adapter as adapter
from engine import cad_measure as measure
from engine import cad_profile as profile
from engine import freeze_manifest as fmanifest
from engine import round2_selftest as round2
from engine import round3_selftest as round3
from engine import round4_selftest as round4
from engine import round5_selftest as round5
from engine import round6_selftest as round6
from engine import round6a_selftest as round6a
from engine import supervised_benchmark as supervised
from engine.reference_mapping import refuse_if_sealed
from tools import run_cad_pipeline as pipeline

# What round 5 recorded, for a side-by-side. Read out of the frozen
# artefact's own numbers and never recomputed.
ROUND_5_FROZEN = {
    "PROJECT_2_CAD_ROUND5_HASH": "8a90def3ac70301a1398aed5",
    "physical_space_polygons": 57,
    "release_eligible": 4,
    "observed_wall_bands": 3272,
    "recovered_partition_spans": 4159,
    "recovered_partition_length_m": 3743.0,
    "void_or_shaft": 43,
    "unresolved_gaps": 4212,
}

# What round 6 steps 1-5 recorded at commit bc8e96f. Read-only: round 6A
# is compared AGAINST it, and never recomputed as though it were this run.
ROUND_6_STEPS_1_5 = {
    "commit": "bc8e96f",
    "physical_space_polygons": 67,
    "release_eligible": 6,
    "observed_wall_bands": 389,
    "recovered_partition_spans": 511,
    "recovered_partition_length_m": 566.1,
    "unresolved_gaps": 299,
    "kitchen_m2": 5.553,
    "kitchen_dims_mm": [2200.0, 2550.0],
    "by_space_role": {"INTERIOR_SPACE_UNCLASSIFIED": 45,
                      "VOID_OR_SHAFT_ON_EVIDENCE": 13,
                      "INTERIOR_ROOM": 9},
}


def run(dwg: str, *, decode_json: str) -> dict:
    refuse_if_sealed(dwg)
    path = Path(dwg)
    src = pipeline._hash(path)

    # Every earlier suite still has to pass. A hash may move — the manifest
    # predicts which — but a PASS may not.
    r2 = round2.assert_frozen()
    r3 = round3.assert_frozen()
    r4 = round4.assert_frozen()
    r5 = round5.assert_frozen()
    r6 = round6.assert_geometry_frozen()
    r6a = round6a.assert_frozen()
    fmanifest.assert_no_artifact_was_rewritten()

    decoded = json.loads(Path(decode_json).read_text(errors="replace"))
    nd = adapter.normalize(decoded, source_file=path.name, source_hash=src)
    prof = profile.build(nd)
    rep = measure.measure(nd, prof)

    counts = rep.counts()
    walls = [w for wr in rep.walls for w in wr.walls]
    spans = [s for c in rep.continuity for s in c.spans]
    recovered = [s for s in spans if s.may_subdivide]
    roles = rep.space_roles
    modes = Counter()
    for wr in rep.walls:
        for t in wr.thickness_modes:
            modes[t] += 1

    now = {
        "physical_space_polygons": counts["space_candidates"],
        "release_eligible": counts["release_eligible"],
        "observed_wall_bands": len(walls),
        "pairs_offered": sum(wr.pairs_offered for wr in rep.walls),
        "pairs_refused_because_the_line_was_taken": sum(
            wr.pairs_refused_for_overlap for wr in rep.walls),
        "recovered_partition_spans": len(recovered),
        "recovered_partition_length_m": round(
            sum(s.length_mm for s in recovered) / 1000, 1),
        "unresolved_gaps": sum(1 for s in spans
                               if s.verdict.startswith("UNRESOLVED")),
        "thicknesses_this_drawing_repeats": dict(modes.most_common(10)),
        "by_space_role": (roles.counts()["by_role"] if roles else {}),
        "interior_spaces": (roles.counts()["interior"] if roles else 0),
        "exterior_spaces": (roles.counts()["exterior"] if roles else 0),
        "vertical_penetrations": (
            roles.counts()["vertical_penetrations"] if roles else 0),
        "regions_with_an_envelope": (
            roles.counts()["regions_with_an_envelope"] if roles else 0),
        "identity_established": counts["identity_established"],
        "identity_unknown": counts["identity_unknown"],
        "functional_zone_groups": counts["functional_zone_groups"],
        "spaces_on_the_clear_internal_basis": sum(
            1 for r in rep.rows
            if r.clear is not None and r.clear.basis_established),
        "lines_standing_inside_a_space": sum(
            len(o.dropped) for o in rep.ownership),
        "established_wall_faces": sum(len(o.faces) for o in rep.ownership),
    }

    return {
        "run_outcome": "COMPLETED",
        "stage": "ROUND_6A_GEOMETRY_ONLY",
        "source": {"file": path.name, "sha256_16": src},
        "three_scoreboards": {
            "1_HISTORICAL_FROZEN": {
                "note": ("blind predictions. Read-only, never recomputed "
                         "as though they were this run"),
                "round_5": dict(ROUND_5_FROZEN),
                "freeze_manifest": fmanifest.manifest(),
            },
            "2_SUPERVISED_P7757": supervised.evaluate(rep),
            "3_SYNTHETIC": {
                "round_2": {"passed": r2["passed"], "cases": r2["cases"]},
                "round_3": {"passed": r3["passed"], "cases": r3["cases"]},
                "round_4": {"passed": r4["passed"], "cases": r4["cases"]},
                "round_5": {"passed": r5["passed"], "cases": r5["cases"]},
                "round_6_geometry": {
                    "passed": r6["geometry_passed"],
                    "cases": r6["geometry_cases"],
                    "awaiting_the_trade_layer":
                        r6["trade_cases_awaiting_implementation"]},
                "ROUND_6_SYNTHETIC_HASH": r6["ROUND_6_SYNTHETIC_HASH"],
                "round_6a": {"passed": r6a["passed"],
                             "cases": r6a["cases"]},
                "ROUND_6A_SYNTHETIC_HASH": r6a["ROUND_6A_SYNTHETIC_HASH"],
            },
        },
        "geometry_before_and_after": {
            "before_round_5_frozen": dict(ROUND_5_FROZEN),
            "after_round_6_steps_3_and_4": dict(ROUND_6_STEPS_1_5),
            "after_round_6a": now,
        },
        "named_spaces": _named(rep),
        "all_interior_polygons": _interior(rep),
        "outside_the_building": _outside(rep),
        "space_roles": (roles.record() if roles else None),
        "physical_walls": [wr.record(limit=4) for wr in rep.walls],
        "measurement_counts": counts,
        "wall_face_ownership": [o.record(limit=6) for o in rep.ownership],
        "what_this_run_is_not": (
            "no trade zone, no floor ceramic, no wall ceramic, no waste "
            "factor and no BOQ row. Round 6A is geometry only, and the "
            "1.05 x 1.50 kitchen recess is deliberately NOT merged: that "
            "is the TradeMeasurementZone question, and it comes later"),
        "no_sealed_reference_was_opened": True,
    }


WANTED = ("KITCHEN", "W.C", "WC", "WASH", "MOSL")


def _labels(r) -> str:
    return " ".join(str(t) for z in r.zones for t in z.label_observations)


def _space_record(r) -> dict:
    """§11: the polygon, its dimensions, and why every side is where it is."""
    c = r.clear
    out = {
        "space_id": r.space_id,
        "drawing_region_id": r.region_id,
        "labels_observed": _labels(r),
        "normalized_identity": getattr(r.identity, "normalized_identity",
                                       "") if r.identity else "",
        "OBSTRUCTED_EXTENT": {
            "what_it_is": ("the frozen flood, which stops at the first "
                           "line it meets — a worktop included. Kept as a "
                           "diagnostic, never as a floor area"),
            "area_m2": (None if not r.enclosure or r.enclosure.area_m2 is
                        None else round(r.enclosure.area_m2, 3)),
        },
    }
    if c is None:
        out["CLEAR_INTERNAL"] = None
        return out
    out["CLEAR_INTERNAL"] = c.record(limit=64)
    return out


def _named(rep) -> list:
    rows = []
    for r in rep.rows:
        text = _labels(r).upper()
        if any(w in text for w in WANTED):
            rows.append(_space_record(r))
    return rows


def _interior(rep, limit: int = 200) -> list:
    roles = getattr(rep, "space_roles", None)
    role_of = ({v.space_id: v.role for v in roles.verdicts}
               if roles else {})
    out = []
    for r in rep.rows:
        role = role_of.get(r.space_id, "")
        if role not in ("INTERIOR_ROOM", "INTERIOR_SPACE_UNCLASSIFIED"):
            continue
        c = r.clear
        out.append({
            "space_id": r.space_id,
            "drawing_region_id": r.region_id,
            "SPACE_ROLE": role,
            "labels_observed": _labels(r),
            "measurement_basis": (c.basis if c else
                                  "MEASUREMENT_BASIS_NOT_ESTABLISHED"),
            "clear_internal_area_m2": (round(c.area_m2, 3) if c else None),
            "principal_dims_mm": (list(c.principal_dims_mm) if c else []),
            "sides_with_no_established_face": (
                sum(1 for f in c.boundary_faces
                    if f.basis == "MEASUREMENT_BASIS_NOT_ESTABLISHED")
                if c else None),
        })
    return out[:limit]


def _outside(rep) -> dict:
    """§9: what lies outside the building, and how far it goes."""
    roles = getattr(rep, "space_roles", None)
    if roles is None:
        return {"space_role_classifier": None}
    out = []
    for v in roles.verdicts:
        if v.role not in ("EXTERIOR_EXTENT_UNRESOLVED",
                          "EXTERIOR_SPACE_UNCLASSIFIED", "EXTERNAL_SPACE"):
            continue
        out.append(v.record())
    return {
        "candidates": out,
        "regions_with_an_envelope": roles.counts()[
            "regions_with_an_envelope"],
        "regions_with_a_site_boundary": sum(
            1 for m in roles.envelopes.values() if m.site is not None),
        "what_a_missing_site_means": (
            "the BUILDING question is answered by the envelope and the "
            "EXTENT question by the site boundary. P7757 draws no site "
            "boundary in any region, so any ground outside the envelope is "
            "EXTERIOR_EXTENT_UNRESOLVED — kept out of an internal floor "
            "finish, and not measured as a yard. No site polygon is "
            "invented"),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("dwg")
    ap.add_argument("--decode-json", required=True)
    ap.add_argument("--json", default="")
    a = ap.parse_args(argv)
    rec = run(a.dwg, decode_json=a.decode_json)
    if a.json:
        Path(a.json).parent.mkdir(parents=True, exist_ok=True)
        Path(a.json).write_text(
            json.dumps(rec, indent=2, ensure_ascii=False, default=str)
            + "\n", encoding="utf-8")
        print(f"wrote {a.json}")
    print(json.dumps({
        "geometry_before_and_after": rec["geometry_before_and_after"],
        "supervised": rec["three_scoreboards"]["2_SUPERVISED_P7757"][
            "by_scoreboard"],
        "synthetic": rec["three_scoreboards"]["3_SYNTHETIC"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
