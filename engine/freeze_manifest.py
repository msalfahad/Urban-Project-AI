"""A freeze is a record of a moment. Replaying it later is a different act.

Round 4's report said round 3 "did not preserve" `ROUND_2_SYNTHETIC_HASH`
because the value moved. That was the wrong way to describe what happened,
and the wrong description invites the wrong fix — going back and editing an
old record until the number matches.

    A HISTORICAL FREEZE IS IMMUTABLE.

What round 2 recorded is what round 2 recorded, for ever. Round 3 rewrote
the semantic seed classifier, so re-running round 2's twelve cases under
round-3 code produced a different hash — and that is not round 2's freeze
changing. It is a REPLAY, which is a separate object with a separate name:

    HISTORICAL_ARTIFACT_HASH      what the run recorded, at the time
    CODE_HASH_AT_FREEZE           the module hashes it recorded with it
    DEPENDENCY_HASHES_AT_FREEZE   what those modules stood on, then
    CURRENT_REPLAY_HASH           what the same self-test computes TODAY

A divergence between the last two is expected in any project that keeps
improving, and it is information — it says exactly which later round
changed which classifier. It is not a violation, and it is never grounds
for editing an artefact.

WHY THE TABLE IS DECLARED HERE AND NOT READ FROM THE ARTEFACTS

The run artefacts live under `data/runs/`, which is gitignored because it
holds client drawings. A record that only exists in an ignored directory is
a record that leaves with the container. So the historical values are
DECLARED in this file, which is committed, and verified against the
artefacts whenever those are present. If the two ever disagree, the
manifest says so loudly rather than picking one.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

SCHEMA = "PROJECT_2_FREEZE_MANIFEST_V1"

MATCHES = "REPLAY_MATCHES_THE_FREEZE"
DIVERGED = "REPLAY_DIVERGED_UNDER_LATER_CODE"
NOT_REPLAYABLE = "NOT_REPLAYABLE_FROM_CODE_ALONE"

WHAT_DIVERGENCE_MEANS = (
    "the frozen value is unchanged and unchangeable. A later round altered "
    "a module this self-test stands on, so replaying it today computes "
    "something else. That is a fact about the code's history, not a "
    "failure, and it is never a reason to edit an artefact")

WHAT_IS_NOT_REPLAYABLE = (
    "a PROJECT output hash is a property of a run over a client drawing: "
    "it depends on the source file, the decode and the measurement of the "
    "day. It is recorded, never recomputed, and a later round that measures "
    "differently does not invalidate it")


@dataclass(frozen=True)
class Freeze:
    """One round's freeze, exactly as that round recorded it."""

    round_name: str
    commit: str
    source_file: str
    source_sha256_16: str
    artifact_path: str
    artifact_sha256_16: str
    project_output_hash: dict = field(default_factory=dict)
    synthetic_artifact_hash: dict = field(default_factory=dict)
    code_hashes_at_freeze: dict = field(default_factory=dict)
    dependency_hashes_at_freeze: dict = field(default_factory=dict)
    note: str = ""

    def record(self) -> dict:
        return {
            "round": self.round_name,
            "commit": self.commit,
            "source_file": self.source_file,
            "source_sha256_16": self.source_sha256_16,
            "HISTORICAL_ARTIFACT": {
                "path": self.artifact_path,
                "file_sha256_16": self.artifact_sha256_16,
                "PROJECT_OUTPUT_HASH": dict(self.project_output_hash),
                "SYNTHETIC_ARTIFACT_HASH": dict(self.synthetic_artifact_hash),
            },
            "CODE_HASH_AT_FREEZE": dict(self.code_hashes_at_freeze),
            "DEPENDENCY_HASHES_AT_FREEZE": dict(
                self.dependency_hashes_at_freeze),
            "immutable": True,
            "note": self.note,
        }


# --------------------------------------------------------------- the table
#
# Every value below was READ OUT OF the artefact that round produced. None
# was recomputed, and none may be edited to make a later replay agree.

ROUNDS = (
    Freeze(
        round_name="ROUND_1_CAD_BASELINE",
        commit="f2113b3",
        source_file="P7757_ARCHITECTURAL.dwg",
        source_sha256_16="7f61f3acdd62d62d",
        artifact_path="data/runs/7757/P7757_CAD_baseline.json",
        artifact_sha256_16="8323169dcad1053a",
        project_output_hash={
            "PROJECT_2_CAD_BASELINE_HASH": "3edf12c66f0984330d77e248"},
        synthetic_artifact_hash={
            "CAD_FIXTURE_FREEZE_HASH": "b0bf6a13f057aa1578262e3c"},
        code_hashes_at_freeze={
            "CAD_ADAPTER_HASH": "bd331c8074806e8b19711417"},
        dependency_hashes_at_freeze={
            "LOCAL_ENCLOSURE_HASH": "01ff128e7ffdab820805dce1",
            "NORMALIZATION_HASH": "ac71926278166cfed5c927ee",
            "SOURCE_PROFILE_HASH": "483314a55f04932564a9bac6"},
        note="the generic CAD adapter, frozen on 29 fixtures before P7757 "
             "was measured at all",
    ),
    Freeze(
        round_name="ROUND_2_ENCLOSURE_ROLE",
        commit="0b417f6",
        source_file="P7757_ARCHITECTURAL.dwg",
        source_sha256_16="7f61f3acdd62d62d",
        artifact_path="data/runs/7757/P7757_CAD_round2.json",
        artifact_sha256_16="70574e47ee249df9",
        project_output_hash={
            "PROJECT_2_CAD_ROUND2_HASH": "70e2f4c34a6b1374687fb20f"},
        synthetic_artifact_hash={
            "ROUND_2_SYNTHETIC_HASH": "de1caf07e16e738b3e34dcc5"},
        code_hashes_at_freeze={
            "ENCLOSURE_ROLE_CLASSIFIER_HASH": "844448ed7de88dea5c27ac75",
            "SEMANTIC_SEED_CLASSIFIER_HASH": "64c01b36653f579fafc113a0",
            "WALL_ROLE_HASH": "e2ed8a68a37d1ed74d7e2e18"},
        dependency_hashes_at_freeze={
            "CAD_ADAPTER_HASH": "bd331c8074806e8b19711417",
            "LOCAL_ENCLOSURE_HASH": "01ff128e7ffdab820805dce1"},
        note="zero site, envelope, super-region or frame released as a room",
    ),
    Freeze(
        round_name="ROUND_3_BOUNDARY_AUTHORITY_AND_IDENTITY",
        commit="d9de019",
        source_file="P7757_ARCHITECTURAL.dwg",
        source_sha256_16="7f61f3acdd62d62d",
        artifact_path="data/runs/7757/P7757_CAD_round3.json",
        artifact_sha256_16="2b46d85d4235c91d",
        project_output_hash={
            "PROJECT_2_CAD_ROUND3_HASH": "e95a4c3c4a298339d9e0adb1"},
        synthetic_artifact_hash={
            "ROUND_3_SYNTHETIC_HASH": "20fd3ed87d05f40ba6cf6123"},
        code_hashes_at_freeze={
            "ROOM_BOUNDARY_AUTHORITY_HASH": "2a79508559556c622fd0dabe",
            "MULTILINGUAL_IDENTITY_HASH": "0611990f77db86d2d4854830",
            "ONTOLOGY_HASH": "1f157903072fd3531a2ef079",
            "SEMANTIC_SEED_CLASSIFIER_HASH": "356ad3ea44f5b1cefec31208"},
        dependency_hashes_at_freeze={
            "CAD_ADAPTER_HASH": "bd331c8074806e8b19711417",
            "LOCAL_ENCLOSURE_HASH": "01ff128e7ffdab820805dce1",
            "ROUND_2_SYNTHETIC_HASH_REPLAYED_HERE":
                "55b221fa624f5e2d5d8ba32b"},
        note="round 3 rewrote the semantic seed classifier, so its record "
             "carries a REPLAY of round 2's self-test rather than round 2's "
             "own freeze. Both numbers are correct; they are different "
             "objects",
    ),
    Freeze(
        round_name="ROUND_4_OPENINGS_AND_DRAWING_REGIONS",
        commit="ef71098",
        source_file="P7757_ARCHITECTURAL.dwg",
        source_sha256_16="7f61f3acdd62d62d",
        artifact_path="data/runs/7757/P7757_CAD_round4.json",
        artifact_sha256_16="2d9028a7831db27b",
        project_output_hash={
            "PROJECT_2_CAD_ROUND4_HASH": "75d831180085a81a2b38506f"},
        synthetic_artifact_hash={
            "ROUND_4_SYNTHETIC_HASH": "f025dbe323a251a75b7dcc42"},
        code_hashes_at_freeze={
            "DRAWING_REGION_HASH": "bd1c391980507d3e18f5d9db",
            "CAD_OPENING_CLASSIFIER_HASH": "336c6f1bc5bb0a3ea42bb698",
            "PORTAL_MATCHER_HASH": "42e7bb997ecbad74fa58e2cf",
            "ROOM_PARTITION_GRAPH_HASH": "6bd4f2ff9ac748948e441baa"},
        dependency_hashes_at_freeze={
            "CAD_ADAPTER_HASH": "bd331c8074806e8b19711417",
            "LOCAL_ENCLOSURE_HASH": "01ff128e7ffdab820805dce1",
            "ROUND_2_SYNTHETIC_HASH_REPLAYED_HERE":
                "55b221fa624f5e2d5d8ba32b",
            "ROUND_3_SYNTHETIC_HASH_REPLAYED_HERE":
                "20fd3ed87d05f40ba6cf6123"},
        note="2 complete physical spaces became 36, release stayed 0",
    ),
    Freeze(
        round_name="ROUND_5_PARTITION_CONTINUITY",
        commit="accf8ec",
        source_file="P7757_ARCHITECTURAL.dwg",
        source_sha256_16="7f61f3acdd62d62d",
        artifact_path="data/runs/7757/P7757_CAD_round5.json",
        artifact_sha256_16="57edcd4f2f23206b",
        project_output_hash={
            "PROJECT_2_CAD_ROUND5_HASH": "8a90def3ac70301a1398aed5"},
        synthetic_artifact_hash={
            "ROUND_5_SYNTHETIC_HASH": "852363123a94453174791e42"},
        code_hashes_at_freeze={
            "PHYSICAL_WALL_BAND_HASH": "35449c817a74f5c1e3e45cf1",
            "PARTITION_CONTINUITY_HASH": "f9b9742aa125bfd028b75166",
            "JUNCTION_RECOVERY_HASH": "cbe777aa922d5ad948ad4189",
            "FACE_SUBDIVISION_HASH": "1313a956a735565e0905a42e",
            "FREEZE_MANIFEST_SCHEMA_HASH": "da9588f4cbed1014d0af91ba"},
        dependency_hashes_at_freeze={
            "CAD_ADAPTER_HASH": "bd331c8074806e8b19711417",
            "LOCAL_ENCLOSURE_HASH": "01ff128e7ffdab820805dce1",
            "DRAWING_REGION_HASH": "bd1c391980507d3e18f5d9db",
            "CAD_OPENING_CLASSIFIER_HASH": "336c6f1bc5bb0a3ea42bb698",
            "PORTAL_MATCHER_HASH": "42e7bb997ecbad74fa58e2cf",
            "ROOM_PARTITION_GRAPH_HASH": "6bd4f2ff9ac748948e441baa"},
        note="36 physical-space polygons became 57 and four released. The "
             "benchmark export of this state is "
             "ROUND5_BENCHMARK_EXPORT_MANIFEST_HASH "
             "a656bb0005d6bee6cbc508c1, written before round 6 began "
             "because round 6 edits physical_wall and the export's own "
             "hash gate will correctly refuse to regenerate it afterwards",
    ),
    Freeze(
        round_name="ROUND_6_GEOMETRY_STEPS_1_TO_5",
        commit="bc8e96f",
        source_file="P7757_ARCHITECTURAL.dwg",
        source_sha256_16="7f61f3acdd62d62d",
        artifact_path="data/runs/7757/P7757_SUPERVISED_GEOMETRY.json",
        artifact_sha256_16="",
        project_output_hash={},
        synthetic_artifact_hash={
            "ROUND_6_SYNTHETIC_HASH": "ac4752e4fc44ce02932586a3"},
        code_hashes_at_freeze={
            "PHYSICAL_WALL_BAND_HASH": "b6d79d2b5c5e2c13eb5d546d",
            "CAD_SPACE_ROLE_HASH": "cf6191908829d6a7d3b022d1",
            "INTERIOR_EXTERIOR_HASH": "752d9d9cb8e5fb51f9145e2d",
            "SUPERVISED_BENCHMARK_HASH": "3047a37c2c8a7c5a45cfe44f",
            "FREEZE_MANIFEST_SCHEMA_HASH": "71df459e2520865be23091a4"},
        dependency_hashes_at_freeze={
            "CAD_ADAPTER_HASH": "bd331c8074806e8b19711417",
            "LOCAL_ENCLOSURE_HASH": "01ff128e7ffdab820805dce1",
            "DRAWING_REGION_HASH": "bd1c391980507d3e18f5d9db",
            "CAD_OPENING_CLASSIFIER_HASH": "336c6f1bc5bb0a3ea42bb698",
            "ROOM_PARTITION_GRAPH_HASH": "6bd4f2ff9ac748948e441baa"},
        note="3,272 wall bands became 389, 43 of 57 VOID became 13 of 67, "
             "and the kitchen measured 5.553 m2 against a disclosed 9.675. "
             "That last number is why round 6A exists: the polygon was "
             "stopping at a kitchen counter",
    ),
    Freeze(
        round_name="ROUND_6A_WALL_FACE_OWNERSHIP",
        commit="b646fb6",
        source_file="P7757_ARCHITECTURAL.dwg",
        source_sha256_16="7f61f3acdd62d62d",
        artifact_path="data/runs/7757/P7757_ROUND6A_GEOMETRY.json",
        artifact_sha256_16="",
        project_output_hash={},
        synthetic_artifact_hash={
            "ROUND_6A_SYNTHETIC_HASH": "57bf8257e7ff4051e2f77652"},
        code_hashes_at_freeze={
            "WALL_FACE_OWNERSHIP_HASH": "a36a3169568d9858ca913fda",
            "PHYSICAL_WALL_BAND_HASH": "550e36a8e313a7d0955a2cf9",
            "CAD_SPACE_ROLE_HASH": "bba19efe2c70dcba1e96f078",
            "INTERIOR_EXTERIOR_HASH": "5f5bd575cb14541a2679ab00",
            "SUPERVISED_BENCHMARK_HASH": "1330ff34ee82740c00d299c2"},
        dependency_hashes_at_freeze={
            "CAD_ADAPTER_HASH": "bd331c8074806e8b19711417",
            "LOCAL_ENCLOSURE_HASH": "01ff128e7ffdab820805dce1",
            "DRAWING_REGION_HASH": "bd1c391980507d3e18f5d9db"},
        note="the kitchen stopped at a worktop. 8.100 m2 at 2700 x 3000, "
             "the W.C at 3.375 and the WASH at 3.150, all on the "
             "clear-internal-finish-face basis; 36 of 70 polygons carried "
             "an established basis and 34 did not",
    ),
    Freeze(
        round_name="ROUND_6B_SINGLE_LINE_PARTITIONS",
        commit="931a1ae",
        source_file="P7757_ARCHITECTURAL.dwg",
        source_sha256_16="7f61f3acdd62d62d",
        artifact_path="data/runs/7757/P7757_ROUND6B_GEOMETRY.json",
        artifact_sha256_16="",
        project_output_hash={},
        synthetic_artifact_hash={
            "ROUND_6B_SYNTHETIC_HASH": "1010b2585e3d77fe4faa4c16"},
        code_hashes_at_freeze={
            "SINGLE_LINE_PARTITION_HASH": "2b9480e67e799c2b3d1f837f",
            "WALL_FACE_OWNERSHIP_HASH": "b2529201eefb569dc651db84",
            "PHYSICAL_WALL_BAND_HASH": "550e36a8e313a7d0955a2cf9",
            "ROOM_PARTITION_GRAPH_HASH": "6bd4f2ff9ac748948e441baa",
            "CAD_SPACE_ROLE_HASH": "bba19efe2c70dcba1e96f078",
            "INTERIOR_EXTERIOR_HASH": "5f5bd575cb14541a2679ab00",
            "SUPERVISED_BENCHMARK_HASH": "1330ff34ee82740c00d299c2"},
        dependency_hashes_at_freeze={
            "CAD_ADAPTER_HASH": "bd331c8074806e8b19711417",
            "LOCAL_ENCLOSURE_HASH": "01ff128e7ffdab820805dce1",
            "DRAWING_REGION_HASH": "bd1c391980507d3e18f5d9db"},
        note="one drawn line carries three authorities and only the first "
             "two are ever free: 213.4 m of partition held topology and "
             "0.0 m of it became material. 69 polygons measured, 40 with "
             "an established basis — which round 6C then had to divide "
             "into rooms, halves of rooms, sheet content and questions",
    ),
    Freeze(
        round_name="ROUND_6C_PHYSICAL_SPACE_REGISTER",
        commit="b5a2ce1",
        source_file="P7757_ARCHITECTURAL.dwg",
        source_sha256_16="7f61f3acdd62d62d",
        artifact_path="data/runs/7757/P7757_ROUND6C_REGISTER.json",
        artifact_sha256_16="",
        project_output_hash={},
        synthetic_artifact_hash={
            "ROUND_6C_SYNTHETIC_HASH": "c59e81b1ea572539377804da"},
        code_hashes_at_freeze={
            "DRAWING_ROLE_HASH": "db18783807179a48ccfd57a7",
            "SPACE_REGISTER_HASH": "a0e9ecb7a1aa008da91a5da9",
            "SINGLE_LINE_PARTITION_HASH": "2b9480e67e799c2b3d1f837f",
            "WALL_FACE_OWNERSHIP_HASH": "b2529201eefb569dc651db84",
            "PHYSICAL_WALL_BAND_HASH": "550e36a8e313a7d0955a2cf9"},
        dependency_hashes_at_freeze={
            "CAD_ADAPTER_HASH": "bd331c8074806e8b19711417",
            "LOCAL_ENCLOSURE_HASH": "01ff128e7ffdab820805dce1",
            "DRAWING_REGION_HASH": "bd1c391980507d3e18f5d9db"},
        note="69 polygons are not 69 rooms: 269.1838 m2 of measured "
             "candidate against 26.3085 m2 the release gate passes. The "
             "bundle of this state is ROUND6C_EXPORT_MANIFEST_HASH "
             "54003ad29e3863ceaa614c86, written before round 6D changed "
             "anything",
    ),
    Freeze(
        round_name="ROUND_6D_PANTRY_AND_STAIRS",
        commit="f53e854",
        source_file="P7757_ARCHITECTURAL.dwg",
        source_sha256_16="7f61f3acdd62d62d",
        artifact_path="data/runs/7757/round6d_export/"
                      "P7757_ROUND6D_REPORT.json",
        artifact_sha256_16="",
        project_output_hash={},
        synthetic_artifact_hash={
            "ROUND_6D_SYNTHETIC_HASH": "6ed47af8801d63e97e73778d"},
        code_hashes_at_freeze={
            "FITTING_BAND_HASH": "cc45efc4267d957cba16e0f5",
            "FUNCTIONAL_ZONE_HASH": "8fe062953599bfa5d748ccb1",
            "STAIR_ASSEMBLY_HASH": "971409c71db7e5520949ee90",
            "PHYSICAL_WALL_BAND_HASH": "8f17f155ca66db3f7970a5c4",
            "WALL_FACE_OWNERSHIP_HASH": "bc0eac5502ad84c53f8f2e13",
            "SINGLE_LINE_PARTITION_HASH": "1cdfe19e3fc2ff912a78d952",
            "SPACE_REGISTER_HASH": "a0e9ecb7a1aa008da91a5da9"},
        dependency_hashes_at_freeze={
            "CAD_ADAPTER_HASH": "bd331c8074806e8b19711417",
            "LOCAL_ENCLOSURE_HASH": "01ff128e7ffdab820805dce1",
            "DRAWING_REGION_HASH": "bd1c391980507d3e18f5d9db"},
        note="a pantry is not always a room and a stair is not a floor: "
             "279.7944 m2 of measured candidate, 26.3085 m2 released, "
             "P7757's pantry PANTRY_OPENNESS_UNKNOWN, and three stair "
             "assemblies of which none carried an established riser",
    ),
)

# Replays this project EXPECTS to diverge, and why. A divergence recorded
# here was predicted; one that is not recorded here is news.
PREDICTED_DIVERGENCES = {
    "ROUND_2_ENCLOSURE_ROLE": {
        "ROUND_2_SYNTHETIC_HASH": "round 3 rewrote the semantic seed "
                                  "classifier",
        "SEMANTIC_SEED_CLASSIFIER_HASH": "round 3 rewrote it",
    },
    "ROUND_6_GEOMETRY_STEPS_1_TO_5": {
        "PHYSICAL_WALL_BAND_HASH": "round 6A adds the evidence token "
                                   "OPEN_SPACE_LIES_OUTSIDE_EACH_FACE_AND_"
                                   "NONE_BETWEEN_THEM, and lets a pair own "
                                   "several disjoint stretches of a line "
                                   "rather than one hull",
        "CAD_SPACE_ROLE_HASH": "round 6A adds EXTERIOR_EXTENT_UNRESOLVED: "
                               "outside the building with no site ring",
        "INTERIOR_EXTERIOR_HASH": "round 6A separates the building "
                                  "question from the site question",
        "ROUND_6_SYNTHETIC_HASH": "it stands on the wall-band hash. The "
                                  "eighteen CASES must still hold; the "
                                  "hash is a replay, the pass is the score",
        "ROOM_PARTITION_GRAPH_HASH": "round 6A measures each space a "
                                     "second time on the clear-internal "
                                     "finish face",
        "SUPERVISED_BENCHMARK_HASH": "round 6A adds the MAIN KITCHEN "
                                     "geometry example the owner asked for",
    },
    "ROUND_6D_PANTRY_AND_STAIRS": {
        "STAIR_ASSEMBLY_HASH_6E_A": "round 6E-A names the four EDGE "
                                    "ROLES of a tread, the composite "
                                    "configuration, the commercial "
                                    "step basis and the visible riser. "
                                    "The nosing of a winder changed "
                                    "from its outer arc to its front "
                                    "edge, which is a behaviour change "
                                    "and is declared as one",
        "FUNCTIONAL_ZONE_HASH": "the owner rule addendum of 2026-09-17 "
                                "bumps the model to V2: a pantry "
                                "openness the OWNER established for a "
                                "project, the arrangement "
                                "OTHER_DRAWN_CONFIGURATION that a "
                                "drawing can show, and the refusal "
                                "PANTRY_TILE_WALLS_REQUIRE_OWNER_REVIEW",
        "SPACE_REGISTER_HASH": "round 6E puts the release vocabulary "
                               "into the model hash: one state, the "
                               "roles that may never carry a room "
                               "quantity, and every reason a candidate "
                               "is withheld",
        "STAIR_ASSEMBLY_HASH": "round 6E bumps the model to V2: the "
                               "vocabulary gains what a piece of floor "
                               "between two flights IS — STAIR_LANDING, "
                               "OPEN_VOID, FLOOR_PLATE, "
                               "CIRCULATION_FLOOR — and the roles a "
                               "staircase can have. A model hash freezes "
                               "a vocabulary, and this vocabulary grew",
        "ROUND_6D_SYNTHETIC_HASH": "round 6E corrected case SB, which "
                                   "expected the 200 mm well between two "
                                   "parallel flights to be a landing of "
                                   "0.36 m2. The geometry is unchanged "
                                   "and the expectation was wrong: the "
                                   "piece runs along both flights' sides "
                                   "and meets the end of neither. The "
                                   "nineteen CASES must still hold; the "
                                   "hash is a replay, the pass is the "
                                   "score",
    },
    "ROUND_6C_PHYSICAL_SPACE_REGISTER": {
        "SPACE_REGISTER_HASH": "round 6E puts the release vocabulary "
                               "into the model hash. The register's "
                               "ROLES are unchanged",
        "PHYSICAL_WALL_BAND_HASH": "round 6D gives a wall a SET of owned "
                                   "stretches instead of the span between "
                                   "its first and last millimetre",
        "WALL_FACE_OWNERSHIP_HASH": "round 6D reads a face where THAT face "
                                    "is drawn, and refuses the front face "
                                    "of a fitting",
        "SINGLE_LINE_PARTITION_HASH": "round 6D refuses a candidate that "
                                      "is the front of a fitting, whatever "
                                      "evidence it collects",
        "ROUND_6C_SYNTHETIC_HASH": "it stands on those hashes. The "
                                   "fourteen CASES must still hold; the "
                                   "hash is a replay, the pass is the "
                                   "score",
    },
    "ROUND_6B_SINGLE_LINE_PARTITIONS": {
        "WALL_FACE_OWNERSHIP_HASH": "round 6C did not touch it. If this "
                                    "diverges, something below it moved",
        "ROUND_6B_SYNTHETIC_HASH": "it stands on the partition and "
                                   "ownership hashes. The twelve CASES "
                                   "must still hold; the hash is a replay, "
                                   "the pass is the score",
        "PHYSICAL_WALL_BAND_HASH": "round 6D: stretches, not a hull",
        "SINGLE_LINE_PARTITION_HASH": "round 6D: a fitting front is never "
                                      "a partition",
    },
    "ROUND_6A_WALL_FACE_OWNERSHIP": {
        "WALL_FACE_OWNERSHIP_HASH": "round 6B adds the basis "
                                    "CLEAR_FACE_NOT_ESTABLISHED, and "
                                    "round 6D refuses a fitting's front "
                                    "face",
        "PHYSICAL_WALL_BAND_HASH": "round 6B stops a crossing wall from "
                                   "counting as a reveal, and round 6D "
                                   "gives a wall a SET of owned stretches",
        "ROUND_6A_SYNTHETIC_HASH": "it stands on the ownership hash. The "
                                   "nine CASES must still hold; the hash "
                                   "is a replay, the pass is the score",
    },
    "ROUND_5_PARTITION_CONTINUITY": {
        "PHYSICAL_WALL_BAND_HASH": "round 6 replaces many-to-many face "
                                   "pairing with a one-line-one-wall "
                                   "assignment",
        "ROUND_5_SYNTHETIC_HASH": "it stands on the wall-band hash. The "
                                  "twenty-three CASES must still pass; the "
                                  "hash is a replay, the pass is the score",
        "ROOM_PARTITION_GRAPH_HASH": "round 6 adds the material-only "
                                     "arrangement the trade layer needs",
        "PARTITION_CONTINUITY_HASH": "round 6 added the rule that a band "
                                     "paired on nothing but proximity may "
                                     "recover nothing",
        "FACE_SUBDIVISION_HASH": "it stands on the continuity hash and "
                                 "moves with it. The module itself is "
                                 "unchanged since round 5",
    },
}


def _live() -> dict:
    """Every named hash this code computes TODAY."""
    from engine import architectural_ontology as onto
    from engine import boundary_authority as authority
    from engine import cad_adapter as adapter
    from engine import cad_openings as openings
    from engine import cad_selftest as selftest
    from engine import drawing_region as dregion
    from engine import enclosure_role as roles
    from engine import identity_reconcile as ident
    from engine import portal_match as pmatch
    from engine import room_partition_graph as rpg
    from engine import semantic_seed as seeds
    from engine import space_enclosure as enc
    from engine import wall_role as wroles

    return {
        "CAD_ADAPTER_HASH": adapter.adapter_hash(),
        "CAD_FIXTURE_FREEZE_HASH": selftest.freeze_hash(),
        "LOCAL_ENCLOSURE_HASH": enc.freeze_hash(),
        "ENCLOSURE_ROLE_CLASSIFIER_HASH": roles.classifier_hash(),
        "SEMANTIC_SEED_CLASSIFIER_HASH": seeds.classifier_hash(),
        "WALL_ROLE_HASH": wroles.classifier_hash(),
        "ROOM_BOUNDARY_AUTHORITY_HASH": authority.authority_hash(),
        "MULTILINGUAL_IDENTITY_HASH": ident.reconciler_hash(),
        "ONTOLOGY_HASH": onto.ontology_hash(),
        "DRAWING_REGION_HASH": dregion.freeze_hash(),
        "CAD_OPENING_CLASSIFIER_HASH": openings.classifier_hash(),
        "PORTAL_MATCHER_HASH": pmatch.matcher_hash(),
        "ROOM_PARTITION_GRAPH_HASH": rpg.graph_hash(),
        "PHYSICAL_WALL_BAND_HASH": _one("physical_wall", "wall_band_hash"),
        "PARTITION_CONTINUITY_HASH": _one("partition_continuity",
                                          "continuity_hash"),
        "JUNCTION_RECOVERY_HASH": _one("junction_recovery",
                                       "recovery_hash"),
        "FACE_SUBDIVISION_HASH": _one("face_subdivision",
                                      "subdivision_hash"),
        "WALL_FACE_OWNERSHIP_HASH": _one("wall_face_ownership",
                                         "model_hash"),
        "SINGLE_LINE_PARTITION_HASH": _one("single_line_partition",
                                           "model_hash"),
        "DRAWING_ROLE_HASH": _one("drawing_role", "model_hash"),
        "SPACE_REGISTER_HASH": _one("space_register", "model_hash"),
        "FITTING_BAND_HASH": _one("fitting_band", "model_hash"),
        "FUNCTIONAL_ZONE_HASH": _one("functional_zone", "model_hash"),
        "STAIR_ASSEMBLY_HASH": _one("stair_assembly", "model_hash"),
        "CAD_SPACE_ROLE_HASH": _space_role_hash(),
        "INTERIOR_EXTERIOR_HASH": _interior_exterior_hash(),
        "SUPERVISED_BENCHMARK_HASH": _supervised_hash(),
    }


def _one(module_name: str, fn_name: str) -> str:
    """One module's own freeze hash, as it computes it TODAY."""
    import importlib

    try:
        mod = importlib.import_module(f"engine.{module_name}")
        return getattr(mod, fn_name)()
    except Exception:      # noqa: BLE001
        return ""


def _space_role_hash() -> str:
    from engine import cad_space_role as srole

    return srole.classifier_hash()


def _interior_exterior_hash() -> str:
    from engine import interior_exterior as ie

    return ie.model_hash()


def _supervised_hash() -> str:
    from engine import supervised_benchmark as sup

    return sup.harness_hash()


def _replay_synthetic() -> dict:
    """Re-run each round's own self-test under TODAY's code."""
    from engine import cad_selftest as r1
    from engine import round2_selftest as r2
    from engine import round3_selftest as r3
    from engine import round4_selftest as r4
    from engine import round6_selftest as r6

    return {
        "CAD_FIXTURE_FREEZE_HASH": r1.freeze_hash(),
        "ROUND_2_SYNTHETIC_HASH": r2.freeze_hash(),
        "ROUND_3_SYNTHETIC_HASH": r3.freeze_hash(),
        "ROUND_4_SYNTHETIC_HASH": r4.freeze_hash(),
        "ROUND_6_SYNTHETIC_HASH": r6.freeze_hash(),
        "ROUND_6A_SYNTHETIC_HASH": _replay_6a(),
        "ROUND_6B_SYNTHETIC_HASH": _one_selftest("round6b_selftest"),
        "ROUND_6C_SYNTHETIC_HASH": _one_selftest("round6c_selftest"),
        "ROUND_6D_SYNTHETIC_HASH": _one_selftest("round6d_selftest"),
    }


def _one_selftest(module_name: str) -> str:
    return _one(module_name, "freeze_hash")


def _replay_6a() -> str:
    from engine import round6a_selftest as r6a

    return r6a.freeze_hash()


def _artifact_agrees(fr: Freeze) -> dict:
    """If the artefact is on disk, does it still say what we declare?"""
    path = Path(fr.artifact_path)
    if not path.exists():
        return {"artifact_present": False,
                "why": ("data/runs is gitignored because it holds client "
                        "drawings. The declared values above are the "
                        "committed record")}
    try:
        payload = json.loads(path.read_text(errors="replace"))
    except Exception:       # noqa: BLE001
        return {"artifact_present": True, "readable": False}
    checked, bad = {}, []
    for name, want in {**fr.project_output_hash,
                       **fr.synthetic_artifact_hash}.items():
        got = _find(payload, name)
        checked[name] = {"declared": want, "in_artifact": got,
                         "agrees": got == want}
        if got is not None and got != want:
            bad.append(name)
    return {"artifact_present": True, "readable": True,
            "file_sha256_16": hashlib.sha256(
                path.read_bytes()).hexdigest()[:16],
            "declared_vs_artifact": checked,
            "disagreements": bad,
            "agrees": not bad}


def _find(payload, key: str):
    """Find a named hash anywhere in a run record."""
    if isinstance(payload, dict):
        if key in payload and isinstance(payload[key], str):
            return payload[key]
        for value in payload.values():
            got = _find(value, key)
            if got is not None:
                return got
    return None


def replay(fr: Freeze) -> dict:
    """What today's code computes for the objects that round froze."""
    live, synth = _live(), _replay_synthetic()
    rows = {}
    for name, frozen in {**fr.code_hashes_at_freeze,
                         **fr.dependency_hashes_at_freeze}.items():
        if name.endswith("_REPLAYED_HERE"):
            continue
        now = live.get(name) or synth.get(name)
        rows[name] = {
            "CODE_HASH_AT_FREEZE": frozen,
            "CURRENT_REPLAY_HASH": now,
            "status": (NOT_REPLAYABLE if now is None
                       else MATCHES if now == frozen else DIVERGED),
        }
    for name, frozen in fr.synthetic_artifact_hash.items():
        now = synth.get(name)
        rows[name] = {
            "SYNTHETIC_ARTIFACT_HASH_AT_FREEZE": frozen,
            "CURRENT_REPLAY_HASH": now,
            "status": (NOT_REPLAYABLE if now is None
                       else MATCHES if now == frozen else DIVERGED),
        }
    for name, frozen in fr.project_output_hash.items():
        rows[name] = {
            "HISTORICAL_ARTIFACT_HASH": frozen,
            "CURRENT_REPLAY_HASH": None,
            "status": NOT_REPLAYABLE,
            "why": WHAT_IS_NOT_REPLAYABLE,
        }
    diverged = sorted(k for k, v in rows.items() if v["status"] == DIVERGED)
    predicted = PREDICTED_DIVERGENCES.get(fr.round_name, {})
    return {
        "round": fr.round_name,
        "rows": rows,
        "diverged": diverged,
        "predicted": {k: predicted[k] for k in diverged if k in predicted},
        "UNPREDICTED_DIVERGENCE": [k for k in diverged if k not in predicted],
        "what_divergence_means": WHAT_DIVERGENCE_MEANS,
    }


def manifest() -> dict:
    """The whole committed record, plus today's replay of each round."""
    return {
        "schema": SCHEMA,
        "FREEZE_MANIFEST_SCHEMA_HASH": schema_hash(),
        "the_four_objects": {
            "HISTORICAL_ARTIFACT_HASH": (
                "what the run recorded at the time. Immutable"),
            "CODE_HASH_AT_FREEZE": (
                "the module hashes that run recorded beside it"),
            "DEPENDENCY_HASHES_AT_FREEZE": (
                "what those modules stood on, then"),
            "CURRENT_REPLAY_HASH": (
                "what the same self-test computes today. A DIFFERENT "
                "object, and a divergence is information rather than a "
                "failure"),
        },
        "rounds": [fr.record() for fr in ROUNDS],
        "predicted_divergences": dict(PREDICTED_DIVERGENCES),
        "replays": [replay(fr) for fr in ROUNDS],
        "artifact_checks": {fr.round_name: _artifact_agrees(fr)
                            for fr in ROUNDS},
        "rule": ("historical artefacts are never rewritten. Where an "
                 "earlier REPORT used the wrong words for one of these "
                 "objects, the report is corrected and the artefact is "
                 "left exactly as it was"),
    }


def assert_no_artifact_was_rewritten() -> dict:
    """Every artefact present on disk still says what the table declares."""
    rows = {fr.round_name: _artifact_agrees(fr) for fr in ROUNDS}
    bad = {k: v for k, v in rows.items()
           if v.get("artifact_present") and not v.get("agrees", True)}
    if bad:
        raise AssertionError(
            "a historical artefact no longer carries the hash the freeze "
            f"manifest declares for it: {sorted(bad)}. A freeze is "
            "immutable; this is a rewrite, not a divergence")
    return rows


def schema_hash() -> str:
    parts = [SCHEMA, MATCHES, DIVERGED, NOT_REPLAYABLE,
             ";".join(f"{r}:{','.join(sorted(v))}"
                      for r, v in sorted(PREDICTED_DIVERGENCES.items()))]
    for fr in ROUNDS:
        parts.append("|".join([
            fr.round_name, fr.commit, fr.source_sha256_16,
            fr.artifact_sha256_16,
            ",".join(f"{k}={v}" for k, v in
                     sorted(fr.project_output_hash.items())),
            ",".join(f"{k}={v}" for k, v in
                     sorted(fr.synthetic_artifact_hash.items())),
            ",".join(f"{k}={v}" for k, v in
                     sorted(fr.code_hashes_at_freeze.items())),
            ",".join(f"{k}={v}" for k, v in
                     sorted(fr.dependency_hashes_at_freeze.items())),
        ]))
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]
