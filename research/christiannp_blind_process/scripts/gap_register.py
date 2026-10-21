"""CHRISTIANNP_VS_URBAN_GAP_REGISTER rows (text + numbers from build_crosschecks; every Urban value is version-stamped,
every christiannp value is REPORT_EXPLICIT)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DASH = ROOT / "research" / "coverage_recovery_round" / "QUANTITY_COVERAGE_DASHBOARD.json"
KEY = {"A": "MORE COMPLETE AND SOURCE-SUPPORTED", "B": "MORE COMPLETE BUT ASSUMPTION-DEPENDENT",
       "C": "DIFFERENT MEASUREMENT BASIS", "D": "DONOR ERROR", "E": "UNKNOWN"}


def register(R, V, gb, sl, col, ftg, bm, pl, wp, agr):
    cov = {r["trade"]: r for r in json.loads(DASH.read_text(encoding="utf-8"))["rows"]}
    ag = {r["element"]: r["class"] for r in agr["rows"]}

    def u(trade):
        r = cov[trade]
        return {"official_before": r["official_before"], "verified": r["verified"], "best": r["best_provisional"],
                "low": r["low"], "high": r["high"], "release": r["release"], "version": V["CR_DASH"]}

    def row(trade, element, urban, report, **kw):
        base = dict(trade=trade, element=element, urban=urban,
                    christiannp=dict(report, evidence="REPORT_EXPLICIT", report_file_check="PENDING"))
        base.update(kw)
        return base

    rows = [
        row("GROUND_BEAMS", "interior + exterior ground beams", u("GROUND_BEAMS"),
            {"m3": R("GROUND_BEAMS_m3"), "length_m": R("GBP_LENGTH_m"), "paired_strips": R("GBP_PAIRED_STRIPS"),
             "raw_lines": R("GBP_RAW_LINES"), "width_mm": R("GBP_STRIP_WIDTH_mm"), "depth": "0.60 ASSUMPTION A5"},
            same_basis="geometry YES (length +%.2f %%, 42 strips vs 43 Urban bands); volume NO (A5 section)"
                       % gb["length_difference_pct"],
            christiannp_method="85 raw lines -> 42 paired strips; volume = drawn width x 0.60 (A5) x length",
            christiannp_assumptions=["A5"], urban_blocker="exterior depth unprinted -> BOUNDED scenario",
            root_cause="section assumption + Urban technical-only release; NOT extraction",
            donor_likely_correct="geometry yes; depth no (27 of 31 interior spans printed 0.30 / 0.40)",
            urban_likely_correct="geometry and interior sections yes; exterior depth needs the consultant",
            agreement=ag["GROUND BEAMS (length)"] + " (length) / " + ag["GROUND BEAMS (volume)"] + " (volume, vs U-C4N)",
            classification="B", generic_lesson="a measured network survives a missing depth; compare network length, "
                                               "connectivity and segmentation, not span counts",
            production_change="none new (ground_beam_recovery); add the network comparison test",
            regression_test="test_ground_beam_network_length_connectivity_segmentation",
            must_not_hardcode=["0.60 m", "200.036 m", "42 strips", "85 lines"]),
        row("GROUND_SLAB", "slab on grade", u("GROUND_SLAB"),
            {"m3": R("GROUND_SLAB_m3"), "area_m2": R("GROUND_SLAB_AREA_m2"), "t_m": R("GROUND_SLAB_T_m"),
             "area_authority": "A7 GF gross outline", "thickness_authority": "T=10 cm text"},
            same_basis="NO - area authority differs (A7 outline vs cells between ground beams)",
            christiannp_method="GF gross outline x 0.10", christiannp_assumptions=["A7"],
            urban_blocker="label scope (recovered as CANDIDATE cells in the coverage round)",
            root_cause="AREA_AUTHORITY: the outline includes ground-beam and column footprints",
            donor_likely_correct="thickness source yes; area no as verified scope",
            urban_likely_correct="cells are the physical slab; T=10 scope is a consultant question",
            agreement=ag["GROUND SLAB"], classification="B",
            generic_lesson="thickness authority and area authority are separate facts",
            production_change="none", regression_test="test_floor_outline_never_verified_as_slab_on_grade",
            must_not_hardcode=["324.038 m2", "0.10 m for every panel"]),
        row("COLUMN_CONCRETE", "columns + joints per storey", u("COLUMNS_AND_JOINTS"),
            {k: R(k) for k in ("COL_FOU_m3", "COL_GF_m3", "COL_1F_m3", "COL_2F_m3")} |
            {"height_model": "A2 GF base +/-0.00; A3 neck 1.00; A4 roof +13.90; A12 levels = FFL; A8 CN continued"},
            same_basis="NO - storey split by A2/A3; FOU+GF totals agree (%s vs %s m3)"
                       % (col["FOU_plus_GF"]["report_m3"], col["FOU_plus_GF"]["urban_m3"]),
            christiannp_method="outlines + labels per floor (logic NOT_HELD) x the report's level model",
            christiannp_assumptions=["A2", "A3", "A4", "A8", "A12"], urban_blocker="none (95/95)",
            root_cause="FOU/GF: convention (A2, A3); 1F/2F: implied section sums smaller than Urban's - population "
                       "or section difference, not height; GF: A8 adds sections",
            donor_likely_correct="total FOU+GF yes; split no; A8 no", urban_likely_correct="census yes",
            agreement=ag["COLUMNS"] + " (vs U-C4N) / " + ag["COLUMNS (FOU+GF total)"] + " (FOU+GF vs Urban)",
            classification="C", generic_lesson="storey boundaries are a declared convention on every column record",
            production_change="none", regression_test="test_column_storey_split_declared_and_total_conserved",
            must_not_hardcode=["1.00 m neck", "+/-0.00 base"]),
        row("BEAMS", "downstands per floor", u("BEAMS"), {f: R(f"BEAMS_{f}_m3") for f in ("GF", "1F", "2F")} |
            {"allocation_rules": "R1-R5"},
            same_basis="PARTLY - allocation by R1-R5 (R5 shares leftover length arithmetically)",
            christiannp_method="strips + labels + R1-R5", christiannp_assumptions=["R3 2 m", "R4 60 mm", "R5"],
            urban_blocker="8 tags without a band; CB8 span count", root_cause="occurrence binding",
            donor_likely_correct="UNKNOWN per floor; R5 allocations are not geometry",
            urban_likely_correct="lower bound safe; best 45.537 m3", agreement="UNDETERMINED",
            classification="B", generic_lesson="unallocated length stays a residue with identity; never shared",
            production_change="width gate (R4 idea) as a recorded check", regression_test="see R1-R5 tests",
            must_not_hardcode=["per-floor volumes", "2 m", "60 mm"]),
        row("SLAB_NET_AREA", "net slab plate per floor",
            {"net_m2": {f: sl["floors"][f]["urban_net_m2"] for f in sl["floors"]}, "version": V["CR"]},
            {f: R(f"NET_SLAB_{f}_m2") for f in ("GF", "1F", "2F")} | {"method": "50 mm raster, 5 classes"},
            same_basis="MOSTLY - gross minus openings; class allocation of edge / unresolved cells differs",
            christiannp_method="raster (see CHRISTIANNP_RASTER_METHOD_SPEC)", christiannp_assumptions=["A1 (volume)"],
            urban_blocker="GF conflict void carried as SOURCE_CONFLICT",
            root_cause="opening classification; hypothesis H-SLAB-1 (stair wells kept) pending the report's class areas",
            donor_likely_correct="UNKNOWN until class areas are imported", urban_likely_correct="vector deductions with ids",
            agreement=ag["SLAB NET AREA"], classification="C",
            generic_lesson="every deduction has an id and a role; raster is an oracle", production_change="none",
            regression_test="test_stair_well_deducted_from_slab_plate",
            must_not_hardcode=["290.555", "179.325", "55.275"]),
        row("SLAB_OPENINGS", "voids / stair wells / conflict voids",
            {"openings_m2": {f: sl["floors"][f]["urban_openings_m2"] for f in sl["floors"]}, "version": V["CR"]},
            {"classes": ["OPENING", "UNRESOLVED_ENCLOSED", "EDGE_LINE_CELLS"], "areas": "in the report, not imported"},
            same_basis="UNKNOWN", christiannp_method="raster classes", christiannp_assumptions=[],
            urban_blocker="GF void with a T16 tag", root_cause="awaiting the report's class areas",
            donor_likely_correct="UNKNOWN", urban_likely_correct="UNKNOWN for the GF conflict void",
            agreement="UNDETERMINED", classification="E",
            generic_lesson="a tagged face inside an opening is a conflict", production_change="none",
            regression_test="existing OPENING_CONFLICT test", must_not_hardcode=["opening areas"]),
        row("WALLS_150", "150 mm blockwork length", u("BLOCKWORK_150_LENGTH"), {"m": R("BLOCK_150_m")},
            same_basis="CLOSE", christiannp_method="parallel-face pairing (parameters NOT_HELD)",
            christiannp_assumptions=[], urban_blocker="none material", root_cause="pairing vs classified bands",
            donor_likely_correct="close", urban_likely_correct="close", agreement="UNDETERMINED (vs U-C4N 71.589)",
            classification="C", generic_lesson="positive control for any pairing route", production_change="none",
            regression_test="150 mm Method B vs Method A within explained classes", must_not_hardcode=["79.971 m"]),
        row("WALLS_200", "200 mm blockwork length", u("BLOCKWORK_200_LENGTH"), {"m": R("BLOCK_200_m")},
            same_basis="NO - report total = raw pairs before classification (ARITHMETIC_INFERENCE)",
            christiannp_method="parallel-face pairing (parameters NOT_HELD)", christiannp_assumptions=[],
            urban_blocker="12 ambiguous bands (now CANDIDATE)",
            root_cause="donor counts opening spans, column faces and duplicate faces as wall",
            donor_likely_correct="NO", urban_likely_correct="best 134.076 m physical",
            agreement="UNDETERMINED (vs U-C4N 148.095: different classification)", classification="D",
            generic_lesson="pair, then classify every metre",
            production_change="wall_band_reconciliation as a required cross-route",
            regression_test="test_pairs_across_door_classify_as_opening_span", must_not_hardcode=["183.497 m"],
            version_note="the earlier ~79 m Urban figure came from an older Urban snapshot; current frozen value "
                         "89.74 m (see version)"),
        row("PLASTER", "wall face area",
            {"physical_faces_verified_m2": pl["urban_physical_faces"]["verified_m2"],
             "physical_faces_best_m2": pl["urban_physical_faces"]["best_m2"], "version": V["CR"]},
            {"gross_faces_m2": R("WALL_FACES_GROSS_m2"), "height_rule": "A10", "door_height": "A13 2.10"},
            same_basis="NO - gross faces with A10 heights; composition includes faces beyond the wall pairs",
            christiannp_method="length x faces x A10 height (composition in the report, not imported)",
            christiannp_assumptions=["A10", "A13", "A1 (via A10)"],
            urban_blocker="finish certification (physical faces now measured)",
            root_cause="finish-gated Urban release vs donor gross faces",
            donor_likely_correct="NO as a finish quantity", urban_likely_correct="physical faces yes",
            agreement="UNDETERMINED", classification="B",
            generic_lesson="PHYSICAL_WALL_FACE_AREA before finish semantics",
            production_change="physical_wall_faces feeding plaster / paint",
            regression_test="test_wall_face_height_is_interval_minus_member", must_not_hardcode=["2364.7 m2"]),
        row("FOOTINGS", "isolated / combined footings",
            {"released_m3": ftg["urban_released_m3"], "occurrences": ftg["urban_occurrences"],
             "blocked": ftg["urban_blocked_outlines"], "version": V["V3B"]},
            {"m3": R("FOOTINGS_m3")}, same_basis="YES (schedule L x W x H)",
            christiannp_method="closed outlines + tags + schedule ATTRIB", christiannp_assumptions=["A6 (blinding)"],
            urban_blocker="F / F10 source conflict", root_cause="occurrence counts (F3, F/F10, FN) - NON_UNIQUE",
            donor_likely_correct="UNKNOWN", urban_likely_correct="25 released occurrences",
            agreement="SHARED_SOURCE_AGREEMENT", classification="E",
            generic_lesson="outline route and tag route agree occurrence by occurrence",
            production_change="footing dual route", regression_test="test_footing_outline_two_tags_is_source_conflict",
            must_not_hardcode=["65.669 m3"]),
        row("STAIRS", "stair concrete", {"status": "V3b stair lines (not compared here)", "version": V["V3B"]},
            {"m3": R("STAIRS_m3"), "assumptions": "A9 waist / landing"}, same_basis="UNKNOWN",
            christiannp_method="breakdown in the report, not imported", christiannp_assumptions=["A9"],
            urban_blocker="see V3b", root_cause="A9 values", donor_likely_correct="UNKNOWN",
            urban_likely_correct="UNKNOWN", agreement="UNDETERMINED", classification="B",
            generic_lesson="flights, landings and waists as separate records", production_change="none",
            regression_test="none until the breakdown is imported", must_not_hardcode=["5.048 m3"]),
        row("FLOOR_CEILING", "floor / ceiling finish areas", {"status": "room-based (not compared here)"},
            {"basis": "A11 ceiling = net slab above; A14 floor / ceiling = slab net area"},
            same_basis="NO", christiannp_method="slab net area", christiannp_assumptions=["A11", "A14"],
            urban_blocker="n/a", root_cause="slab net area includes wall footprints and non-room area",
            donor_likely_correct="NO", urban_likely_correct="room polygons", agreement="UNDETERMINED",
            classification="D", generic_lesson="finish areas come from rooms, not slabs", production_change="none",
            regression_test="test_floor_finish_area_excludes_wall_footprint", must_not_hardcode=[]),
        row("ROOF_WATERPROOFING", "roof waterproofing", {"status": "V3b WP split (not compared here)"},
            {"basis": "A15 SFRS slab only, no upturns"}, same_basis="NO",
            christiannp_method="SFRS slab area", christiannp_assumptions=["A15"], urban_blocker="n/a",
            root_cause="upturns and other exposed roofs omitted", donor_likely_correct="NO (incomplete)",
            urban_likely_correct="UNKNOWN", agreement="UNDETERMINED", classification="D",
            generic_lesson="waterproofing includes upturns and every exposed roof", production_change="none",
            regression_test="test_roof_waterproofing_includes_upturns", must_not_hardcode=[]),
    ]
    return {"classification_key": KEY, "versioning": "every Urban value carries ENGINE_COMMIT / REGISTER_VERSION / "
                                                     "DRAWING_SHA / CALCULATION_ROUND",
            "rule": "christiannp values are REPORT_EXPLICIT (imported from the owner's quotation; file check "
                    "PENDING); per-object donor lists are NOT_HELD", "rows": rows}
