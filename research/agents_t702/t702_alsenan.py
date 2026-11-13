"""T-702 builder (development villa; research only, unwired): tiles round 3 on candidate ARCH_TAKEOFF_V3.0.69.

    python3 -I research/agents_t702/t702_alsenan.py [--check]

(a) roof / terrace build-up layer ledger by line id (R-T702-3); (b) stair-core floor surfaces and their one owner
(R-T702-4) + the two stair-core wet-room wall-tile lines (R-T702-5); (c) the beam crossings T-690 left as 0 .. 2 ends,
measured by this run's overlay (t702_probe.py, relative stations only), with the sunken panels over the same faces
(R-T702-1 / -2); (d) the 104 HELD tile lines restated. Inputs: merged repository files pinned by sha256; own-read
constants below (local metres / entity handles; no coordinate, text or client data).
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import t702_rules as R  # noqa: E402

P = {
    "v3069": ("research/agents_t687/out/LINE_INDEX_V3_0_69.json", "e908a5f105197d44"),
    "v3066": ("research/agents_t677/out/LINE_INDEX_V3_0_66.json", "02065c41e79dd9df"),
    "t681": ("research/agents_t681/out/T681_TILES_CENSUS.json", "2ca16110154e890f"),
    "t690": ("research/agents_t690/out/T690_TILES_ROUND2.json", "764caabc39caada1"),
    "t646": ("research/agents_t646/out/ROOF_FENCE_HOLD_CENSUS_T646.json", "fd4988c7f2f9cf0d"),
    "t691": ("research/agents_t691/out/T691_WP_ROUND2.json", "2e190feefd0bd16c"),
    "t493": ("research/agents_t493/CENSUS_T493.csv", "231e2ae24b03e588"),
    "t686": ("research/agents_t686/out/T686_ROUND3.json", "f755ea4f6154e008"),
}
OUT = HERE / "out"
TILE_SCOPE = ("FIN.FLOOR.PORCELAIN", "FIN.FLOOR.WET_TILE", "FIN.FLOOR.FINISH_HELD", "EXT.FLOOR.PORCELAIN",
              "EXT.FLOOR.OUTDOOR", "FIN.WALL.TILE", "FIN.SKIRTING", "FIN.STAIR.SKIRTING.SLOPED",
              "FIN.STAIR.SKIRTING.ZIGZAG", "FIN.FLOOR.BED.DRY", "FIN.FLOOR.BED.WET")

# ---------------------------------------------------------------- own read this run (t702_probe.py)
OWN = {
    "drawings": "Drive 'Alsenan chalet project': P7757_DXF_COMPRESSED.zip -> P7757.dxf (sha256 ab54dd55) and "
                "'ST7757 dxf.dxf' (sha256 9f9d1179), own decode this run into the private folder",
    "overlay": "ST S-COL.BON 35C -> arch S-COL.BON 2FAE (1.10 x 0.25 both); checked: 22 ST column outlines within 12 m of 35C "
               "match an arch S-COL.BON outline, worst corner residual 0.0 mm",
    "text_census": "ST7757 2,237 TEXT / MTEXT / ATTRIB / DIMENSION entities, P7757 497: no roof or terrace layer "
                   "callout and no layer thickness; the only 'INSULATION' print is the pool detail ('5cm INSULATION "
                   "MEMBRANE.' with '10cm PLAIN CONCRETE.'); structural level texts +0.15 / +0.30 / +1.00 / +9.70 "
                   "only (no slab level under a terrace or roof); 'CHECK ARCHITECTURAL DETAIL OF PARAPET, BEFORE "
                   "CASTING' x3 is a title-area note with no dimension; 'T min = 20 / 25 / 30 cm' is the column-"
                   "thickness-by-storey-height note (H, 4.3 / 4.7 / 5 m), not a roof build-up",
}
# GF-07 pantry frame: origin = start of A6 (south face), x east, y north (metres)
PANTRY = {
    "faces": "AE west face 0 .. 4.45, column 2FAE south face 0 .. 0.90 at 4.45 + return 0.05, 158 north wall 0.90 .. "
             "3.00 at 4.50 (door D-GF-06 1.659 .. 2.659), A6 south face 0 .. 3.00; B3 east edge (layer 5) OPEN; "
             "walk 10.500 m (T-690 uses 10.491, T-128 walk: residual 0.009 named)",
    "B27_edges": "325 (0.900, 4.700) -> (4.369, 0.000); 326 (-0.034, 4.450) -> (3.398, -0.200): width 0.900, "
                 "angle 53.571 deg to the x axis",
    "B27_on_faces": {"column 2FAE south face": "0.9000", "column return": "0.0500", "158 north wall": "0.1476",
                     "AE west face": "0.0462", "A6 south face": "0", "B3 open east edge": "1.5156 (open: 0)"},
    "B27_total_m": "1.143764",
    "panels": {"280": {"plan_m2": "3.0784", "faces": {"AE west face": "2.7236"}},
               "287": {"plan_m2": "2.0804", "faces": {"158 north wall": "1.7524"}}},
    "B27_under_panel_m": "0",
}
# GF-14 wash-lobby frame: origin = start of D2 (south face, east end)
LOBBY = {
    "faces": "D2 south 0.794, BE east 1.024, 318 W_C 1.341, 324 W_B 1.323, 317 0.142, door 320 0.800 (D315, head "
             "2.20 below H: wall above it in the band), 31A 0.238, door 321 0.800, 31B 0.938, west face 0.844; 2DB "
             "(layer 2, above the cut) OPEN 1.256; walk 8.243 m (T-690 / T-128 8.267: residual 0.024 named)",
    "B11_edges": "28F / 428 at x -0.580 / -0.380, N-S (0.20 wide)",
    "B11_on_faces": {"D2 south face (square)": "0.200000", "over door 320 (45 deg)": "0.282868"},
    "panels": {"275": {"W_B 324": "1.000", "317": "0.142", "over door 320": "0.414"},
               "276": {"over door 320": "0.103", "31A": "0.059"}},
    "panel_faces_m": "1.718",
}


def sha(rel):
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()


def load(key):
    rel, pin = P[key]
    if sha(rel)[:16] != pin:
        raise R.RuleError(f"{rel}: sha256 changed (pinned {pin})")
    p = ROOT / rel
    return json.loads(p.read_text()) if p.suffix == ".json" else list(csv.DictReader(p.open()))


def s(x):
    if isinstance(x, float):
        x = repr(x)
    return None if x is None else str(R.q(x)).rstrip("0").rstrip(".") if "." in str(R.q(x)) else str(R.q(x))


def by_id(lines):
    return {l["line_id"]: l for l in lines}


# ---------------------------------------------------------------- (d) census

def census(v69, v66, t681):
    a = {k: l for k, l in by_id(v66["lines"]).items() if l["item_code"] in TILE_SCOPE}
    b = {k: l for k, l in by_id(v69["lines"]).items() if l["item_code"] in TILE_SCOPE}
    if set(a) != set(b) or any(a[k] != b[k] for k in a):
        raise R.RuleError("tile-scope lines changed V3.0.66 -> V3.0.69: census must be rebuilt")
    held = sorted(k for k, l in b.items() if l["class"] == "HELD")
    ids = sorted(e["line_id"] for e in t681["entries"])
    if ids != held:
        raise R.RuleError("T-681 census != V3.0.69 HELD tile filter")
    by_class = {}
    for e in t681["entries"]:
        by_class[e["class"]] = by_class.get(e["class"], 0) + 1
    return {"scope_lines": len(b), "identical_v3066_v3069": True, "held": len(held), "by_class": by_class}


# ---------------------------------------------------------------- (a) roof layers

ZONES = ("ROOF-430", "TERRACE-550", "ROOF-970", "ROOF-1390")
FINISH_EDGE = {"ROOF-430": "finish hatch D1F + B2A (T-321)", "TERRACE-550": "finish hatch AE0 + D1A + 1252 (T-321)",
               "ROOF-970": "finish hatch 2F21 + drafting gaps, domes excluded (T-321)"}


def part_a(v69, t646, t691):
    lines = [l for l in v69["lines"] if l["item_code"].startswith("FIN.ROOF.")]
    t646_fix = {r["line_id"]: r for r in t646["lines"]}
    membrane = {"ROOF-430": "55.560 (AT220 released; D-band 54.920 .. 55.560, T-321)",
                "TERRACE-550": "32.721 (AT216 released)",
                "ROOF-970": f"{t691['roof_F_V685_1']['corrected']['band_m2'][0]} .. "
                            f"{t691['roof_F_V685_1']['corrected']['band_m2'][1]} (T-691 MERGED; candidate 115.832 is "
                            "0.018 above its band: chord-deducted domes)",
                "ROOF-1390": "HELD (Q-34 PARKED)"}
    rows = []
    for l in sorted(lines, key=lambda l: (l["element_id"], l["item_code"])):
        zone, layer = l["element_id"].split(":")[1], l["element_id"].split(":")[2]
        fix = t646_fix.get(l["line_id"], {}).get("fix", {}).get("after") if l["line_id"] in t646_fix else None
        if zone == "ROOF-1390":
            r = {"state": "HELD blank", "why": "owner Q-34 PARKED (top roof; no roof plan D-62)"}
        elif layer == "FINISH":
            r = R.layer_row(zone, layer, area=repr(l["measured_net"]), area_edge=FINISH_EDGE[zone])
        elif layer == "FALLS_SCREED":
            r = R.layer_row(zone, layer, owner_rule="Q-41 'roof -> screed' own line (ASSUMED - OWNER-APPROVED)",
                            at_least_m3=fix["held_low"] if fix else None, designer_item="D-39")
        elif layer == "PROTECTION":
            r = R.layer_row(zone, layer, owner_rule="Q-41 gives ONE roof screed line ('falls / protection'), carried "
                                                    "by FIN.ROOF.SCREED: no second layer printed or ruled")
        else:
            r = R.layer_row(zone, layer, designer_item="D-39 (no insulation printed; pool-detail insulation not "
                                                       "extended to a roof, ERS s.3)")
        rows.append({"line_id": l["line_id"], "item_code": l["item_code"], "zone": zone, "layer": layer,
                     "v3069": {"class": l["class"], "measured_net": l["measured_net"], "held_low": l["held_low"],
                               "held_high": l["held_high"], "unit": l["unit"]},
                     "t702": {k: (s(v) if isinstance(v, Decimal) else v) for k, v in r.items()},
                     "membrane_face_basis_m2": membrane[zone]})
    # the cited cap of T-250 / T-690 (b_roof < 0.30) is refused as a screed bound until located
    try:
        R.layer_row("ROOF-970", "FALLS_SCREED", owner_rule="Q-41", area="115.81396", at_least_m3="4.791492",
                    cap=("0.30", False, "parapet note ST p.14 (T-250 s.(d))"))
        cap_state = "USED"
    except R.RuleError as e:
        cap_state = f"REFUSED: {e}"
    bed_on_roof = [l["line_id"] for l in v69["lines"] if l["item_code"].startswith("FIN.FLOOR.BED")
                   and any(z in l["element_id"] for z in ZONES)]
    return {"rule": "R-T702-3", "rows": rows, "own_text_census": OWN["text_census"],
            "cap_b_roof_030": cap_state, "falls_once": {"tile_bed_lines_on_roof_zones": bed_on_roof,
                                                        "reading": "Q-45 'roof depending on slope' and Q-41 'roof -> "
                                                        "screed' describe ONE falls volume: carried once by "
                                                        "FIN.ROOF.SCREED; no FIN.FLOOR.BED line sits on a roof zone "
                                                        "(0 found): no double count"},
            "adhesive": "roof finish material and tile size not printed: adhesive HELD (T-448 rule needs a size)",
            "terrace_soffit": "TERRACE-550 over GF-07 / GF-16: the structural set draws one 0.16 plate (no step, "
                              "T-128 / T-220); on that plate the slab top is 5.451 and the build-up under the printed "
                              "+5.50 would be 0.049 m, less than the printed 1 % falls rise 0.190 .. 0.203 m (T-321 "
                              "Checker): the plate reading and the printed finished level cannot both hold (DCR-6). "
                              "The roof-part soffit bound of T-690 (S 3.65 .. 4.34 above the GF FFL) stands; no "
                              "printed fact narrows it"}


# ---------------------------------------------------------------- (b) stair core

def part_b(v69, t493, t686):
    L = by_id(v69["lines"])
    find = lambda p: next(l for k, l in L.items() if k.startswith(p))  # noqa: E731
    surfaces, rows = [], []
    owner = {"FLOOR_OR_LANDING": "FLOOR", "FLOOR": "FLOOR", "STAIR_LANDING": "B7-04", "STAIR_ARRIVAL": "B7-04",
             "WINDER": "TREAD"}
    for r in t493:
        tr = owner[r["element"]]
        surfaces.append((r["id"], tr, r["line"] or None))
        cand = find(r["line"]) if r["line"] else None
        rows.append({"surface": r["id"], "level": r["level"], "area_m2": r["area_m2"] or None, "owner_trade": tr,
                     "t493_line_state": r["line_state"],
                     "v3069": None if cand is None else {"line_id": cand["line_id"], "item_code": cand["item_code"],
                                                         "class": cand["class"], "measured_net": cand["measured_net"],
                                                         "held_low": cand["held_low"], "held_high": cand["held_high"]}})
    R.single_owner(surfaces)
    bounds = {k: {"item_code": L[k]["item_code"], "class": L[k]["class"], "held": [L[k]["held_low"], L[k]["held_high"]]}
              for k in L if k.startswith(("L-1983e89d", "L-5d2be30d", "L-a788de46"))}
    # R-T702-5: the two stair-core wet-room wall-tile lines follow their backing (T-686 MERGED -> V3.0.69 wired)
    tiles = []
    for tile_p, back_p, room in (("L-1341e041", "L-3f7fb1b3", "GF-10"), ("L-de4088e7", "L-a636dabc", "GF-11")):
        t, b = find(tile_p), find(back_p)
        if (t["measured_net"], t["held_low"], t["held_high"]) != (None, None, None):
            raise R.RuleError(f"{t['line_id']} is no longer blank")
        after = R.tile_follows_backing({k: repr(v) if isinstance(v, float) else v for k, v in b.items()})
        src = next(x for x in t686["lines"] if x["line_id"] == b["line_id"])
        tiles.append({"room": room, "line_id": t["line_id"], "before": "HELD blank (DESIGNER_ITEM, C-SH-2)",
                      "after": {k: s(v) if isinstance(v, Decimal) else v for k, v in after.items()},
                      "backing": b["line_id"], "basis": f"{src['length_m']} m x tile top {src['height_m'][0]} .. "
                      f"{src['height_m'][1]} (R-T686-3: highest head 2.20 .. G1 +4.65 - floor +0.30) less "
                      f"{src['calc']['deducted_at_low']} .. {src['calc']['deducted_at_high']} m2 openings",
                      "status": "OPEN BOUND (ASSUMED - OWNER-APPROVED Q-55 C head / Q-48 A top; floor level C-SH-2 "
                                "designer item stays named)"})
    lo = sum(Decimal(x["after"]["held_low"]) for x in tiles)
    hi = sum(Decimal(x["after"]["held_high"]) for x in tiles)
    return {"rule": "R-T702-4 / R-T702-5", "surfaces": rows, "one_owner": "PASS: 11 surfaces, 0 claimed twice",
            "bounds_v3069": bounds,
            "landings_unwired": "T-493 (MERGED 2a02de31) proposals still not in V3.0.69: MS1-LD 1.4375, MS2-LD "
                                "2.9325, 2F arrival 4.865, RS-LD 1.3525 m2 (B7-04 own lines); L-1983e89d NOT_APPLICABLE "
                                "as a landing bound; L-5d2be30d = 7.7975 landings + 1.4275 named non-landing",
            "gf_core_floor": "GF hall 4.805 (+1.00) and back lobby 1.3225 (+0.30) are floor-level surfaces at flight "
                             "ends: owner trade FLOOR (A6), material HELD (no finish source, RFI-B-A12); centre strip "
                             "GF-ST-CN 0 .. 0.23 HELD; under-stair porcelain 2.07 released",
            "wet_core_floor_level": "own read this run (GF plan): the level marks +0.30 (back lobby, north) and +1.00 "
                                    "(hall, south) lie outside GF-10 / GF-11; neither room carries a mark, and the "
                                    "basin space's leafless 0.90 doorway opens toward the stair lanes: both floor "
                                    "options stay carried (C-SH-2, designer)",
            "wall_tile": tiles, "wall_tile_total": [s(lo), s(hi)]}


# ---------------------------------------------------------------- (c) beam crossings

def part_c(t690):
    rooms = {r["room"]: r for r in t690["c_wet_band"]["rooms"]}
    g7, g14 = rooms["GF-07"], rooms["GF-14"]
    share = Decimal(g7["under_roof_share"])
    L7 = Decimal(g7["face_length_m"])
    roof7 = (L7 * share).quantize(Decimal("0.00001"))
    floor7 = L7 - roof7
    panel7 = sum(Decimal(v) for p in PANTRY["panels"].values() for v in p["faces"].values())
    b27 = Decimal(PANTRY["B27_total_m"])
    free7 = floor7 - panel7 - b27
    lo7, hi7 = R.room_band(free7, [(b27, "0.85", "0.16", False)], panel7, roof7, "4.29", "3.65",
                           roof_S=g7["S_roof_m"])
    L14 = Decimal(g14["face_length_m"])
    panel14 = Decimal(LOBBY["panel_faces_m"])
    sq, ob = (Decimal(v) for v in LOBBY["B11_on_faces"].values())
    free14 = L14 - panel14 - sq - ob
    lo14, hi14 = R.room_band(free14, [(sq, "0.75", "0.16", False), (ob, "0.75", "0.16", True)], panel14, 0,
                             "4.29", "3.65")
    return {"rule": "R-T702-1 / R-T702-2", "overlay": OWN["overlay"], "drawings": OWN["drawings"], "rooms": [
        {"room": "GF-07", "line_id": "L-ea586fea86188a18bb67", "beam": "B27 90 x 85 (T-110 BM-GF-048), soffit 3.60 "
         "above the FFL: fills the band [H 3.65, S 4.29]", "geometry": PANTRY,
         "count": "1 crossing (north end into column 2FAE); the south end leaves through the open east edge "
                  "(B3) and frames into the S-COL.BON column south-east of that edge (local x 3.275 .. 4.375): 0 on a wall",
         "before": {"band": [g7["band_low_m2"], g7["band_high_m2"]], "beam_term": g7["deducted_m2"],
                    "cause": g7["status"]},
         "after": {"band": [s(lo7), s(hi7)],
                   "terms": {"floor part (T-690 split)": s(floor7), "roof part (terrace, share)": s(roof7),
                             "under sunken panels 280 / 287 (D-41)": s(panel7), "B27 stretch (band 0)": s(b27),
                             "free floor faces": s(free7)},
                   "status": "HELD (bounded): terrace build-up D-39 / DCR-6 and sunken drop D-41 (new); beam count "
                             "established (1)"}},
        {"room": "GF-14", "line_id": "L-ef7a16664d12b68a6e71", "beam": "B11 20 x 75 (T-110 BM-GF-001): depth 0.59 "
         "below the slab, a 0.05 strip of wall stays under it in the 0.64 band", "geometry": LOBBY,
         "count": "2 crossings: square on the south face D2, at 45 deg over door 320 (between sunken panels 275 / "
                  "276, its top unprinted, T-213 s.4)",
         "before": {"band": [g14["band_low_m2"], g14["band_high_m2"]], "beam_term": g14["deducted_m2"],
                    "cause": g14["status"]},
         "after": {"band": [s(lo14), s(hi14)],
                   "terms": {"walk (T-690)": s(L14), "under sunken panels 275 / 276 (D-41)": s(panel14),
                             "B11 square": s(sq), "B11 oblique": s(ob), "free faces": s(free14)},
                   "status": "HELD (bounded): sunken drop D-41 (new); beam count established (2)"}}],
        "finding": "F-T702-2: T-690 (MERGED, wired in V3.0.69) took the GF wet-room soffit as the flat 1F slab (S 4.29, "
                   "DRAWING-CONFIRMED); the five GF-roof-slab 'Sunken slab.' panels (T-213: 275 / 276 / 280 / 287 / "
                   "298, drop d printed nowhere, D-41) lie over GF-07 (4.476 m of faces) and GF-14 (1.718 m) by this "
                   "overlay, and 275 / 276 cover the plan zone behind doors 320 / 321 (the W.C. wedges GF-12 / GF-13; "
                   "not traced face by face this run): those bands are HELD on d, not fixed"}


# ---------------------------------------------------------------- build

def build():
    v69, v66, t681, t690 = load("v3069"), load("v3066"), load("t681"), load("t690")
    t646, t691, t493, t686 = load("t646"), load("t691"), load("t493"), load("t686")
    d = {"task": "T-702", "candidate": v69["candidate_version"], "inputs": {k: v[0] for k, v in P.items()},
         "rules": ["R-T702-1", "R-T702-2", "R-T702-3", "R-T702-4", "R-T702-5"],
         "d_census_before": census(v69, v66, t681), "a_roof_layers": part_a(v69, t646, t691),
         "b_stair_core": part_b(v69, t493, t686), "c_beam_crossings": part_c(t690)}
    blank_wall_tile = 6 - len(d["b_stair_core"]["wall_tile"])
    d["d_census_after"] = {"held": 104, "moved_blank_to_bounded": [x["line_id"] for x in d["b_stair_core"]["wall_tile"]],
                           "FIN.WALL.TILE blank": f"6 -> {blank_wall_tile}",
                           "DESIGNER_ITEM": "7 -> 5 blank (+2 OPEN BOUND; class change for the Lead: DESIGNER -> "
                                            "OPEN_BOUND)",
                           "unchanged": "OWNER_OPEN 46, OPEN_BOUND 44 (+2), MEASURABLE_NOW 6 (T-681 fixes, unwired), "
                                        "WIRING_GAP 1 (T-690 closed, unwired); (a) and (c) move no tile-scope line "
                                        "(roof layers, landings and the plaster bands are other codes)",
                           "never_summed": "the two new bounds stay beside the released wall tile, never added"}
    return d


def md(d):
    c = d["c_beam_crossings"]["rooms"]
    out = [f"# T-702 tiles round 3 (generated; do not edit) on {d['candidate']}", "",
           f"Census: {d['d_census_before']['scope_lines']} tile-scope lines identical V3.0.66 -> V3.0.69; HELD "
           f"{d['d_census_before']['held']} {d['d_census_before']['by_class']}.", "",
           "## (a) roof layers", "", "| line | zone | layer | V3.0.69 | T-702 | membrane face basis m2 |",
           "|---|---|---|---|---|---|"]
    for r in d["a_roof_layers"]["rows"]:
        v, t = r["v3069"], r["t702"]
        vv = v["measured_net"] if v["measured_net"] is not None else f"{v['held_low']} .. {v['held_high']}"
        tt = t.get("quantity") or f"{t.get('low')} .. {t.get('high') or 'OPEN'}" if t.get("state") == "HELD" \
            else t.get("quantity") or t["state"]
        out.append(f"| {r['line_id'][:10]} | {r['zone']} | {r['layer']} | {v['class']} {vv} | {t['state']}: {tt} | "
                   f"{r['membrane_face_basis_m2']} |")
    out += ["", f"Cap b_roof < 0.30: {d['a_roof_layers']['cap_b_roof_030']}", "", "## (b) stair core", "",
            "| surface | level | m2 | owner | V3.0.69 |", "|---|---|---|---|---|"]
    for r in d["b_stair_core"]["surfaces"]:
        v = r["v3069"]
        out.append(f"| {r['surface']} | {r['level']} | {r['area_m2']} | {r['owner_trade']} | "
                   f"{'-' if v is None else v['line_id'][:10] + ' ' + v['class']} |")
    out += ["", "| wall tile | room | before | after |", "|---|---|---|---|"]
    for t in d["b_stair_core"]["wall_tile"]:
        out.append(f"| {t['line_id'][:10]} | {t['room']} | blank | {t['after']['held_low']} .. "
                   f"{t['after']['held_high']} m2 |")
    out += ["", "## (c) beam crossings", "", "| room | line | before m2 | after m2 | count |", "|---|---|---|---|---|"]
    for r in c:
        out.append(f"| {r['room']} | {r['line_id'][:10]} | {r['before']['band'][0]} .. {r['before']['band'][1]} | "
                   f"{r['after']['band'][0]} .. {r['after']['band'][1]} | {r['count']} |")
    out += ["", d["c_beam_crossings"]["finding"], ""]
    return "\n".join(out)


def main(argv):
    d = build()
    js = json.dumps(d, indent=1, sort_keys=True, default=str) + "\n"
    m = md(d)
    if "--check" in argv:
        if (OUT / "T702_TILES_ROUND3.json").read_text() != js or (OUT / "T702_TILES_ROUND3.md").read_text() != m:
            print("T-702 outputs differ from the rebuild")
            return 1
        print("T-702 outputs reproduce")
        return 0
    OUT.mkdir(exist_ok=True)
    (OUT / "T702_TILES_ROUND3.json").write_text(js)
    (OUT / "T702_TILES_ROUND3.md").write_text(m)
    print("written", d["c_beam_crossings"]["rooms"][0]["after"]["band"], d["c_beam_crossings"]["rooms"][1]["after"]["band"],
          d["b_stair_core"]["wall_tile_total"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
