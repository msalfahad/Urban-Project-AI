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

# An ABSOLUTE numerical tolerance, in millimetres. Floating-point summation
# over thousands of edges does not land on exactly zero, and a gate that claims
# "= 0" while the implementation accepts 0.2 mm is lying about its own rule.
# This is NOT a percentage: it does not grow with the drawing, so it can never
# hide a proportional loss.
ABSOLUTE_NUMERICAL_EPSILON_MM = 1.0

PASS = "PASS"
FAIL = "FAIL"
NOT_MEASURED = "NOT_MEASURED"
# Reported so a regression is visible, but never gating. A number I chose is
# not a physical truth, and G4 was one.
DIAGNOSTIC = "DIAGNOSTIC_ONLY"


@dataclass(frozen=True)
class Gate:
    """One measurable condition, with the reason it is a condition at all."""

    gate_id: str
    question: str
    threshold: str
    why_a_face_walk_needs_it: str


GATES = (
    Gate("G1-LENGTH",
         "Is unexplained wall-length drift within numerical epsilon?",
         f"abs(drift) <= {ABSOLUTE_NUMERICAL_EPSILON_MM} mm "
         "(ABSOLUTE, never a percentage), with duplicate removal itemised",
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
    Gate("G4-CONCENTRATION",
         "Where is the wall length concentrated?",
         "DIAGNOSTIC ONLY — reported, never gating",
         "80% was a number I chose, not one the building justifies. Length "
         "concentration does not decide whether a face can be walked: a "
         "component holding 90% of the metres and no cycle bounds nothing, "
         "and one holding 3% around a shaft bounds a real room. The question "
         "that matters is G8's. This stays visible as a diagnostic so a "
         "regression is noticeable, and it does not gate."),
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
         "every IN_SCOPE mapped region has at least one possibly-enclosing "
         "cycle (a NECESSARY condition; failure is conclusive, passing is not "
         "proof)",
         "This is the only gate that checks the graph against the building "
         "rather than against itself. A graph can satisfy every other gate and "
         "still describe no rooms. It is the most meaningful gate here and it "
         "now carries the weight G4 was wrongly given."),
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
        else PASS if abs(drift) <= ABSOLUTE_NUMERICAL_EPSILON_MM else FAIL,
        f"{drift} mm (epsilon {ABSOLUTE_NUMERICAL_EPSILON_MM} mm, absolute)"
        if drift is not None else None)

    rej = h.get("rejected_clusters")
    add(g["G2-CLUSTERS"], NOT_MEASURED if rej is None
        else PASS if rej == 0 else FAIL, rej)

    hist = conn.get("terminus_histogram", {})
    unres = hist.get("UNRESOLVED")
    add(g["G3-TERMINI"], NOT_MEASURED if unres is None
        else PASS if unres == 0 else FAIL,
        f"{unres} of {conn.get('termini')} termini unresolved")

    share = conn.get("share_of_length_in_major_components_pct")
    add(g["G4-CONCENTRATION"], DIAGNOSTIC,
        f"{share}% of wall length in {conn.get('major_components')} major "
        "components",
        "diagnostic only — does not gate, and a low value is not a failure")

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

    cyc = diagnostic.get("cycles_over_regions")
    if not cyc:
        add(g["G8-CYCLES-IN-REAL-ROOMS"], NOT_MEASURED, None,
            "no region correspondence supplied to this run")
    else:
        bad = cyc.get("regions_with_no_possible_enclosing_cycle")
        add(g["G8-CYCLES-IN-REAL-ROOMS"], PASS if bad == 0 else FAIL,
            f"{cyc.get('regions_with_a_possible_enclosing_cycle')} of "
            f"{cyc.get('regions_tested')} regions could be enclosed; "
            f"{cyc.get('total_independent_cycles')} independent cycles in "
            f"{cyc.get('components_with_cycles')} components",
            cyc.get("basis"))

    passed = sum(1 for r in results if r["status"] == PASS)
    failed = [r["gate_id"] for r in results if r["status"] == FAIL]
    unmeasured = [r["gate_id"] for r in results if r["status"] == NOT_MEASURED]
    diagnostics = [r["gate_id"] for r in results if r["status"] == DIAGNOSTIC]
    return {
        "gates": results,
        "passed": passed, "failed": failed, "not_measured": unmeasured,
        "diagnostic_only": diagnostics,
        "ready_for_e31a": not failed and not unmeasured,
        "verdict": (
            "READY" if not failed and not unmeasured else
            f"NOT READY — {len(failed)} gate(s) failing, "
            f"{len(unmeasured)} not yet measurable"),
    }
