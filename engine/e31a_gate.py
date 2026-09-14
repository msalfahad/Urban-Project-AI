"""E31A gate — measurable conditions for starting planar face extraction.

The review's instruction was to propose gates rather than arbitrary perfection,
and to report them before using them. These are the proposal. Nothing in the
engine enforces them until they are approved; `evaluate()` reports PASS or FAIL
per gate with the number that decided it, so the decision is the owner's and
the evidence is on the table.

WHY GATES AT ALL. A DCEL over a disconnected graph is not wrong — it is
correct and produces nothing. Building it first would prove the face-walker
works on a graph that has no faces to walk, which is the most convincing way to
be wrong. Each gate below names a property a face walk actually depends on.

WHAT IS DELIBERATELY NOT A GATE:

    graph_components == 1     A drawing legitimately contains shafts, detached
                              walls, balconies, external structures and
                              separate blocks. Forcing one component would mean
                              joining things that are not joined in the
                              building. The gate is that every disconnect is
                              EXPLAINED, not that none exists.

    zero termini              A wall genuinely ends at an opening and at the
                              building edge. The gate is that each terminus has
                              a classification, not that none remains.

    a perfect length match    Already covered, and already strict: unexplained
                              drift must be exactly zero, with duplicate
                              removal itemised rather than tolerated.
"""

from __future__ import annotations

from dataclasses import dataclass

PASS = "PASS"
FAIL = "FAIL"
NOT_MEASURED = "NOT_MEASURED"


@dataclass(frozen=True)
class Gate:
    """One measurable condition, with the reason it is a condition at all."""

    gate_id: str
    question: str
    threshold: str
    why_a_face_walk_needs_it: str


GATES = (
    Gate("G1-LENGTH",
         "Is unexplained wall-length drift exactly zero?",
         "drift == 0.0 mm, with duplicate removal itemised separately",
         "A face walk sums edges. Length that vanished without a reason is "
         "geometry the walk will not find, and a percentage tolerance would "
         "hide exactly the loss that matters."),
    Gate("G2-CLUSTERS",
         "Is every over-spread cluster resolved or explicitly refused?",
         "rejected_clusters == 0, or every one named in the exceptions",
         "An unresolved node is a place where the walk does not know which "
         "edges meet. It will either skip a turn or invent one."),
    Gate("G3-TERMINI",
         "Is every terminus classified?",
         "UNRESOLVED termini == 0",
         "An unclassified wall end is an open face boundary of unknown cause. "
         "The walk cannot tell a doorway from a missing wall, and one closes "
         "a room while the other leaves it open."),
    Gate("G4-MAJOR-CONNECTIVITY",
         "Do the major components hold most of the wall length, and is each "
         "internally connected enough to contain cycles?",
         "major components hold >= 80% of wall length AND each has at least "
         "one closed cycle",
         "A face needs a cycle. A component with no cycle contributes no room "
         "however much wall it holds."),
    Gate("G5-EXPLAINED-DISCONNECTS",
         "Is every disconnect either valid or explicitly unresolved?",
         "components with cause J_UNRESOLVED == 0",
         "An unexplained disconnect is an unknown: it may be a real separate "
         "structure or a wall the extractor lost. The walk gives a different "
         "answer for each and cannot tell which it is looking at."),
    Gate("G6-JUNCTIONS",
         "Is there any systematic junction failure?",
         "UNRESOLVED_JUNCTION == 0 and CORNER_OVERLAP correctly separated "
         "from TRUE_CROSS_JUNCTION",
         "Degree decides how many half-edges leave a node. A corner read as a "
         "crossing gives the walk four exits where there are two, and false "
         "half-edges make false rooms."),
    Gate("G7-FRAGMENTATION",
         "Is source-path fragmentation understood?",
         "measured and reported, whatever the answer",
         "If flattening broke architectural paths, the fragments must be "
         "reassembled before pairing; if it did not, reassembly would join "
         "unrelated geometry. The walk depends on which is true."),
    Gate("G8-CYCLES-IN-REAL-ROOMS",
         "Do closed cycles exist where the raster says rooms are?",
         ">= 1 closed cycle coincident with each IN_SCOPE mapped region",
         "This is the only gate that checks the graph against the building "
         "rather than against itself. A graph can satisfy every other gate and "
         "still describe no rooms."),
)


def evaluate(diagnostic: dict) -> dict:
    """Score the gates against a graph diagnostic. Reports; enforces nothing.

    A gate whose input is absent reads NOT_MEASURED, never PASS. An unmeasured
    condition is not a satisfied one.
    """
    h = diagnostic.get("noded_graph", {})
    conn = diagnostic.get("connectivity", {})
    src = diagnostic.get("source", {})
    results = []

    def add(gate, status, observed, note=""):
        results.append({"gate_id": gate.gate_id, "question": gate.question,
                        "threshold": gate.threshold, "status": status,
                        "observed": observed,
                        "why": gate.why_a_face_walk_needs_it, "note": note})

    g = {x.gate_id: x for x in GATES}

    drift = h.get("length_difference_mm")
    add(g["G1-LENGTH"], NOT_MEASURED if drift is None
        else PASS if abs(drift) <= 1.0 else FAIL,
        f"{drift} mm" if drift is not None else None)

    rej = h.get("rejected_clusters")
    add(g["G2-CLUSTERS"], NOT_MEASURED if rej is None
        else PASS if rej == 0 else FAIL, rej)

    hist = conn.get("terminus_histogram", {})
    unres = hist.get("UNRESOLVED")
    add(g["G3-TERMINI"], NOT_MEASURED if unres is None
        else PASS if unres == 0 else FAIL,
        f"{unres} of {conn.get('termini')} termini unresolved")

    share = conn.get("share_of_length_in_major_components_pct")
    add(g["G4-MAJOR-CONNECTIVITY"], NOT_MEASURED if share is None
        else PASS if share >= 80.0 else FAIL,
        f"{share}% of wall length in {conn.get('major_components')} major "
        "components",
        "the cycle half of this gate is not yet measured")

    causes = conn.get("cause_histogram", {})
    unexplained = causes.get("J_UNRESOLVED")
    add(g["G5-EXPLAINED-DISCONNECTS"], NOT_MEASURED if unexplained is None
        else PASS if unexplained == 0 else FAIL,
        f"{unexplained} components with no explanation")

    bad_j = h.get("UNRESOLVED_JUNCTION")
    add(g["G6-JUNCTIONS"], NOT_MEASURED if bad_j is None
        else PASS if bad_j == 0 else FAIL,
        f"{bad_j} unresolved junctions, {h.get('CORNER_OVERLAP')} corner "
        f"overlaps, {h.get('TRUE_CROSS_JUNCTION')} true crossings")

    frag = src.get("path_fragmentation")
    add(g["G7-FRAGMENTATION"], NOT_MEASURED if frag is None else PASS,
        frag and (f"{frag['short_in_a_path_that_also_has_a_long_run']} of "
                  f"{frag['short_segments']} short marks share a path with a "
                  "long run"))

    add(g["G8-CYCLES-IN-REAL-ROOMS"], NOT_MEASURED, None,
        "not yet implemented: needs the raster correspondence step")

    passed = sum(1 for r in results if r["status"] == PASS)
    failed = [r["gate_id"] for r in results if r["status"] == FAIL]
    unmeasured = [r["gate_id"] for r in results if r["status"] == NOT_MEASURED]
    return {
        "gates": results,
        "passed": passed, "failed": failed, "not_measured": unmeasured,
        "ready_for_e31a": not failed and not unmeasured,
        "verdict": (
            "READY" if not failed and not unmeasured else
            f"NOT READY — {len(failed)} gate(s) failing, "
            f"{len(unmeasured)} not yet measurable"),
    }
