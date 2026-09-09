"""The reference villa programme — Urban Projects' 52-week template.

Encoded from the owner's sample timeline (28 activities, 8 stages, ~52 weeks for
a villa). It is the *starting* structure; the durations of the quantity-driven
activities are recomputed per project from that project's real quantities via the
Schedule Engine (E12). Cycle-driven activities (a concrete floor, testing,
handover) keep a fixed duration because the pour/cure cycle, not the volume,
sets their pace.

Everything is PROVISIONAL until Urban Projects' own production rates exist (E19);
after three or four projects these rates stop being a template and become a
measurement of how the company actually builds.

`reference_programme(quantities)` returns the activity list with the driven
durations filled in from `quantities` (falling back to the template's own
assumed quantities when a value isn't supplied).
"""

from __future__ import annotations

from engine.schedule import Activity

# Provisional production rates (units per week, one crew) and the template's own
# assumed quantities for a reference villa — replace with measured rates (E19).
RATES = {
    "footings_m3": 40.0,       # concrete footings
    "blockwork_m2": 210.0,     # block + partitions
    "plaster_m2": 450.0,       # internal + external
    "screed_m2": 170.0,        # floor screed / prep
    "ceramic_m2": 120.0,       # tiling install
    "paint_m2": 90.0,          # primer + putty + coats
}

TEMPLATE_QTY = {
    "footings_m3": 78.0,
    "blockwork_m2": 1260.0,
    "plaster_m2": 2660.0,
    "screed_m2": 843.0,
    "ceramic_m2": 843.0,
    "paint_m2": 540.0,
}


def reference_programme(quantities: dict | None = None) -> list[Activity]:
    """Build the reference programme, driven by a project's quantities."""
    q = {**TEMPLATE_QTY, **(quantities or {})}

    def driven(key):
        return q.get(key), RATES[key]

    fq, fr = driven("footings_m3")
    bq, br = driven("blockwork_m2")
    pq, pr = driven("plaster_m2")
    sq, sr = driven("screed_m2")
    cq, cr = driven("ceramic_m2")
    ptq, ptr = driven("paint_m2")

    return [
        Activity("site", "Site preparation", "Enabling", fixed_weeks=1),
        Activity("earth", "Earthworks", "Enabling", fixed_weeks=1, depends_on=["site"]),
        Activity("lean", "Lean concrete", "Foundations", fixed_weeks=2, depends_on=["earth"]),
        Activity("footings", "Footings", "Foundations", quantity=fq, unit="m3",
                 production_rate=fr, depends_on=["lean"]),
        Activity("backfill", "Backfill & under-slab", "Foundations", fixed_weeks=2,
                 depends_on=["footings"]),
        Activity("frame_g", "Frame — ground", "Structure", fixed_weeks=3, depends_on=["backfill"]),
        Activity("frame_1", "Frame — first floor", "Structure", fixed_weeks=3, depends_on=["frame_g"]),
        Activity("frame_2", "Frame — second floor", "Structure", fixed_weeks=3, depends_on=["frame_1"]),
        Activity("frame_r", "Frame — roof rooms", "Structure", fixed_weeks=3, depends_on=["frame_2"]),
        # blockwork starts on finished floors while the frame still rises
        Activity("block", "Blockwork & partitions", "Envelope", quantity=bq, unit="m2",
                 production_rate=br, overlaps=[("frame_g", 1.0)], depends_on=["frame_1"],
                 notes="starts on finished floors during the frame"),
        Activity("mep1", "MEP first fix", "Services", fixed_weeks=7, depends_on=["block", "frame_r"]),
        Activity("ac", "AC ducting", "Services", fixed_weeks=6, overlaps=[("mep1", 0.5)]),
        Activity("plaster", "Plaster", "Finishes", quantity=pq, unit="m2",
                 production_rate=pr, depends_on=["mep1"]),
        Activity("waterproof", "Waterproofing", "Finishes", fixed_weeks=4, overlaps=[("plaster", 0.5)]),
        # aluminium measured & fabricated off site for weeks before install
        Activity("alu_fab", "Aluminium — measure & fabricate", "Envelope", fixed_weeks=8,
                 overlaps=[("plaster", 0.0)], notes="off-site fabrication in parallel"),
        Activity("screed", "Screed & floor prep", "Finishes", quantity=sq, unit="m2",
                 production_rate=sr, depends_on=["plaster"]),
        Activity("facade", "Facades — stone/cladding", "Envelope", fixed_weeks=7,
                 overlaps=[("plaster", 1.0)]),
        Activity("ceramic", "Ceramic & marble", "Finishes", quantity=cq, unit="m2",
                 production_rate=cr, depends_on=["screed"]),
        Activity("alu_inst", "Aluminium — install", "Envelope", fixed_weeks=3,
                 depends_on=["alu_fab", "facade"]),
        Activity("paint", "Paint", "Finishes", quantity=ptq, unit="m2",
                 production_rate=ptr, depends_on=["ceramic"]),
        Activity("carpentry", "Carpentry & doors", "Finishes", fixed_weeks=4, overlaps=[("paint", 0.5)]),
        Activity("mep2", "MEP second fix", "Services", fixed_weeks=4, overlaps=[("paint", 0.6)]),
        Activity("kitchen", "Kitchen & cabinets", "Finishes", fixed_weeks=4, depends_on=["paint"]),
        Activity("external", "External works — courtyard", "External", fixed_weeks=5,
                 overlaps=[("paint", 0.0)]),
        Activity("testing", "Testing & commissioning", "Handover", fixed_weeks=2,
                 depends_on=["mep2", "kitchen"]),
        Activity("snagging", "Snagging", "Handover", fixed_weeks=2, depends_on=["testing"]),
        # the safety allowance is its own activity, never smeared into every task
        Activity("buffer", "Safety buffer (float)", "Handover", fixed_weeks=2, depends_on=["snagging"],
                 notes="kept as its own activity so the programme can't hide its float"),
        Activity("handover", "Handover", "Handover", fixed_weeks=1, depends_on=["buffer"]),
    ]
