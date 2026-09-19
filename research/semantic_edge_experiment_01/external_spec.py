"""§16 - is a specialised floor-plan detector reachable, and if not, spec it.

An external wall/door/window detector would be an EXTERNAL_SEMANTIC_
CANDIDATE and never a geometry authority. This checks, without delaying
the experiment, whether any credential for one is present, and writes the
specification a later run would need.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from research.semantic_edge_experiment_01 import protocol as P

OUT = Path("data/experiments/SEMANTIC_EDGE_EXPERIMENT_01") / "external"

CANDIDATE_ENV = ("KREO_API_KEY", "KREO_TOKEN", "FLOORPLAN_DETECTOR_API_KEY",
                 "FLOORPLAN_DETECTOR_URL", "EXTERNAL_DETECTOR_API_KEY",
                 "EXTERNAL_DETECTOR_URL")


def main() -> int:
    present = sorted(k for k in CANDIDATE_ENV if os.environ.get(k))
    body = {
        "EXPERIMENT_ID": P.EXPERIMENT_ID,
        "PROTOCOL_HASH": P.protocol_hash(),
        "ROLE_IF_IT_IS_EVER_RUN": "EXTERNAL_SEMANTIC_CANDIDATE",
        "it_is_never_a_geometry_authority":
            P.EXTERNAL_DETECTOR_IS_A_CANDIDATE_NEVER_AN_AUTHORITY,
        "CREDENTIAL_ENVIRONMENT_NAMES_LOOKED_FOR": list(CANDIDATE_ENV),
        "CREDENTIALS_PRESENT": present,
        "STATUS": ("CREDENTIAL_PRESENT_NOT_RUN_IN_THIS_EXPERIMENT" if present
                   else "NO_EXTERNAL_DETECTOR_WAS_REACHABLE"),
        "THE_EXPERIMENT_DID_NOT_WAIT_FOR_ONE": True,

        "WHAT_A_LATER_TEST_WOULD_DO": [
            "send each feature group's LEVEL_A and LEVEL_B source crops, "
            "as images, with no CAD entity ids and no coordinates",
            "receive whatever the detector returns for walls, doors and "
            "windows in that crop",
            "record every returned item as an EXTERNAL_SEMANTIC_CANDIDATE "
            "row carrying the crop it came from and the detector's own "
            "label vocabulary, unmapped",
            "map that vocabulary onto this experiment's FEATURE_ASSEMBLY "
            "types only in a separate, recorded step, so a mapping "
            "decision can be audited apart from a detection",
            "compare with A19 and with the deterministic classifier as a "
            "third opinion, never as a tie-break and never as truth",
        ],
        "WHAT_IT_MAY_NEVER_DO": [
            "supply a coordinate, a dimension, an area or a polygon that "
            "any downstream pass measures from",
            "overwrite a CAD-established position",
            "be averaged or voted with the other readers",
        ],
        "WHAT_WOULD_HAVE_TO_BE_RECORDED": [
            "the detector's product and version",
            "the exact crop bytes sent, by hash",
            "the exact response, unedited",
            "whether the crop left this machine, and to where",
            "that no benchmark, expected area or known quantity was sent",
        ],
        "A_PRIVACY_NOTE": (
            "the crops are client drawing content. Sending them to a "
            "third-party service is a disclosure decision for the owner "
            "to take, not a technical default, and no crop was sent here"),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "EXTERNAL_DETECTOR_TEST_SPEC.json").write_text(
        json.dumps(body, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    print(json.dumps({"STATUS": body["STATUS"],
                      "credentials_present": present}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
