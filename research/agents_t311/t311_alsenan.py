"""T-311 on the development villa (P7757 / ST7757): PARAPETS AND PLINTH as physical elements, every component tied to
ONE owner trade and a candidate line id (ARCH_TAKEOFF_V3.0.19) or NO_LINE. Research only: prints and writes ids,
states, levels, lengths, areas and volumes; no coordinate, no name, no drawing content.

Sources (merged unless stated):
  parapet runs   research/agents_t172/PARAPET_COMPONENTS_T172.csv (per side: outer / inner top arris, t, height above
                 the printed roof level, outer face; T-172 MERGED dd1d6e4, Checker own 48.237 m2 of the outer faces 0.000)
  faces          research/agents_t305/FACE_LINE_LEDGER_T305.csv (T-305 MERGED 9d71ef09: every exterior band once)
  items          research/agents_t305/ITEMS_T305.csv (inner faces, tops; corners in m.l)
  candidate      CANDIDATE_V3019_T311.json (--extract <own V3.0.19 run dir>): the lines a parapet / plinth component
                 could sit in (concrete, blockwork, WP roof + upturn, facade / finish, formwork if any)
  drawing reads  this run (Drive 'Alsenan chalet project', read-only, private copies only): ST7757.pdf p.14 (three
                 parapet details, 400 dpi), p.13 (exterior ground beam), the three slab-plan notes in 'ST7757 dxf.dxf'
                 ('CHECK ARCHITECTURAL DETAIL OF PARAPET, BEFORE CASTING'), sections A-A (p7757_arch_sheet10.pdf) and
                 B-B (Alsenan_Architectural_P7757_Pages_11-12.pdf p.11) at 300 dpi: the hatch of every parapet.

    python3 -I research/agents_t311/t311_alsenan.py --extract <run>/t255/v3019   (needs the private run)
    python3 -I research/agents_t311/t311_alsenan.py --write
    python3 -I research/agents_t311/t311_alsenan.py --check
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RES = ROOT / "research"
sys.path.insert(0, str(HERE))
import parapet_plinth as R  # noqa: E402

CAND = HERE / "CANDIDATE_V3019_T311.json"
LINES_FILE = "V3_0_19_BOQ_LINES.json"
KEEP_PREFIX = ("STR.CONC.GROUND_BEAM", "STR.CONC.BEAM", "STR.CONC.SLAB", "MAS.", "ARCH.WALL", "FIN.WP.ROOF",
               "FIN.EXT.FINISH", "ARCH.FACADE", "STR.FORM", "FORM", "FIN.PLASTER", "FIN.EXT", "STR.CONC.PARAPET",
               "FIN.COPING", "ARCH.PARAPET")

# printed alternatives for a parapet run with no keyed detail (R-T311-1). Read this run, ST7757.pdf p.14 at 400 dpi:
#  P1 'TYPICAL DETAIL OF PARAPET SECTION.': edge beam 'AS PER SCH.' to the slab top, an RC upstand '30' above the slab
#     top with its own cage ('MUST BE MORE THAN THE HEIGHT OF ROOF FINISHING'), 'Brick Wall', an RC cap with a moulded
#     projection, its heights 'AS PER ARC.' (cap 5 d12/m, 5 d10/m).
#  P2 'DETAIL OF PARAPET SECTION.' (centre): RC parapet 130 with a 30 x 10 cap, stepped 10 + 10 onto a 60 x 40 beam.
#  P3 'DETAIL OF PARAPET SECTION.' (right): tapered RC parapet 105 high, 15 + 15 at the base, 15 at the top.
#  ARCH sections A-A / B-B: every parapet is cut in the hatch of the slab and the edge beams (the block walls below are
#     cut unhatched): an RC parapet the drawn wall thickness, plain top.
# No sheet keys P1 / P2 / P3 to a run; the slab plans say 'CHECK ARCHITECTURAL DETAIL OF PARAPET, BEFORE CASTING'.
# P2 / P3 profiles contradict the drawn 0.20 thickness of every run (plans, sections), so their volumes are not in the
# range: their only common fact used here is 'all RC'.
ALTERNATIVES = (
    R.Alternative("P1", 0.30, cap_m=None, cap_printed=False, block=True, source="ST7757 p.14 typical (brick on RC upstand, RC cap as per arc.)"),
    R.Alternative("RC", None, source="ST7757 p.14 P2 / P3 (RC) and P7757 sections A-A / B-B (parapet hatched as the slab)"),
)
# printed levels of each roof (finished roof / parapet top) and the structural slab top status (T-214 / T-221 D-39)
ROOFS = {"ANNEX": ("+4.30", "+4.80"), "GF": ("+5.50", "+6.00"), "1F": ("+9.70", "+11.00 printed NE / SW; CAD top lines"),
         "2F": ("+13.90", "+14.40")}
# T-214 floor datum chain (DRAWING-CONFIRMED): F.F.L. -> structural slab top = exterior ground-beam top (p.13
# 'Ground Floor slab level' at the beam top); house +1.00 -> +0.95, annex +0.30 -> +0.25. D-35 (T-253): main-house
# ground-beam soffit = natural ground +-0.00; annex depth CONFLICT (literal 0.25 vs the section's bar zones).
GB = {"house": {"ffl": 1.00, "top": 0.95, "soffit": 0.00, "status": "DRAWING-CONFIRMED (T-214 top, T-253 D-35 soffit)"},
      "annex": {"ffl": 0.30, "top": 0.25, "soffit": None, "status": "top DRAWING-CONFIRMED (T-214); depth CONFLICT (T-253)"}}
ANNEX_SIDES = {"SE-1", "SW-1", "SW-2", "NW-1", "SW-3", "NE-6"}   # T-305 / T-159 annex block sides
PASSAGE = {"P-1"}                                               # passage face at +0.30: no ground beam of its own read


def read(p):
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def f_(s):
    try:
        return float(str(s).strip())
    except (TypeError, ValueError):
        return None


def r6(x):
    return None if x is None else round(x + 0.0, 6)


def held_pair(s):
    """'HELD 1.0996..1.2996' -> (1.0996, 1.2996); a plain number -> None."""
    s = str(s)
    if ".." not in s:
        return None
    a, b = s.replace("HELD", "").strip().split("..")
    return float(a), float(b)


# --------------------------------------------------------------------------------------------- extract (needs the run)
def extract(run_dir, lines_file=LINES_FILE):
    run_dir = Path(run_dir)
    raw = (run_dir / lines_file).read_bytes()
    d = json.loads(raw.decode("utf-8"))
    lines = d if isinstance(d, list) else d["lines"]
    csvp = run_dir / lines_file.replace(".json", ".csv")
    keep, codes = [], {}
    for ln in lines:
        code = ln.get("item_code") or ""
        loc = ln.get("location") or {}
        hay = " ".join(str(x) for x in (code, loc.get("room_id"), loc.get("element_id"), ln.get("physical_element"),
                                        (ln.get("calculation") or {}).get("formula"))).upper()
        if not (code.startswith(KEEP_PREFIX) or "PARAPET" in hay or "PLINTH" in hay or "UPSTAND" in hay
                or "COPING" in hay):
            continue
        codes[code] = codes.get(code, 0) + 1
        calc = ln.get("calculation") or {}
        br = ln.get("bounded_range") or None
        keep.append({"line_id": ln["line_id"], "item_code": code, "floor": loc.get("floor"),
                     "room_id": loc.get("room_id"),
                     "element_id": re.sub(r"@-?[0-9.]+,-?[0-9.]+", "@<xy>", str(loc.get("element_id") or "")),
                     "physical_element": ln.get("physical_element"), "unit": ln.get("unit"),
                     "evidence_state": ln.get("evidence_state"), "measured_net": ln.get("measured_net"),
                     "range": None if not br else [br.get("low"), br.get("high")],
                     "formula": str(calc.get("formula") or "")[:220],
                     "names_parapet": "PARAPET" in hay, "names_plinth": "PLINTH" in hay,
                     "names_upstand": "UPSTAND" in hay,
                     "rfi_head": str((ln.get("rfi") or {}).get("question") or "")[:120]})
    out = {"lines_file": lines_file, "source": "own V3.0.19 run (research/agents_t255/v3019_run.py after research/agents_t167/v304_run.py) on "
                     "Drive 'Alsenan chalet project' P7757_DXF_COMPRESSED.zip -> P7757.dxf (ab54dd55) and "
                     "'ST7757 dxf.dxf' (9f9d1179)",
           "lines_json_sha256_8": hashlib.sha256(raw).hexdigest()[:8],
           "lines_csv_sha256_8": hashlib.sha256(csvp.read_bytes()).hexdigest()[:8] if csvp.exists() else None,
           "lines_total": len(lines), "kept_by_code": dict(sorted(codes.items())),
           "lines": sorted(keep, key=lambda x: (x["item_code"], x["floor"] or "", x["room_id"] or "",
                                                x["element_id"], x["line_id"]))}
    CAND.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {CAND.name}: {len(keep)} lines of {len(lines)}")


def candidate():
    return json.loads(CAND.read_text(encoding="utf-8"))


# ------------------------------------------------------------------------------------------------------ parapet runs
def parapet_runs():
    """one row per parapet run (T-172 per-side), with the solid, the material split and the faces."""
    rows = []
    for r in read(RES / "agents_t172" / "PARAPET_COMPONENTS_T172.csv"):
        outer, inner, t = f_(r["OUTER_TOP_ARRIS_ML"]), f_(r["INNER_TOP_ARRIS_ML"]), f_(r["T_M"])
        cl = (outer + inner) / 2.0                     # T-172 top surface = centreline x t (tops reproduced below)
        h = f_(r["H_ABOVE_ROOF_M"])
        hp = held_pair(r["H_ABOVE_ROOF_M"]) if h is None else None
        run = R.ParapetRun(r["CHAIN"], r["SIDE"], cl, t, h, h_held=hp)
        solid = R.solid_volume(run)
        split = R.material_split(run, ALTERNATIVES)
        c, b = split["concrete_m3"], split["block_m2"]
        rc_h = R.Rng(c.lo / (t * cl), c.hi / (t * cl), c.held) if cl > 0 else R.Rng(0, 0)
        form = R.formwork_faces(run, rc_h) if cl > 0 else R.Rng(0, 0)
        hh = (h, h) if h is not None else hp
        inner_face = (inner * hh[0], inner * hh[1])
        outer_face = (outer * hh[0], outer * hh[1])
        rows.append({
            "chain": r["CHAIN"], "side": r["SIDE"], "kind": r["KIND"], "roof_level": ROOFS[r["CHAIN"]][0],
            "parapet_top": ROOFS[r["CHAIN"]][1], "outer_top_arris_m": outer, "inner_top_arris_m": inner,
            "centreline_m": r6(cl), "t_m": t, "h_above_finish_m": h, "h_held_lo": hp[0] if hp else None,
            "h_held_hi": hp[1] if hp else None,
            "solid_m3_lo": r6(solid.lo), "solid_m3_hi": r6(solid.hi),
            "solid_held_increment_m3_per_m_b_edge": r6(t * cl),
            "concrete_m3_lo": r6(c.lo), "concrete_m3_hi": r6(c.hi),
            "block_m2_lo": r6(b.lo), "block_m2_hi": r6(b.hi),
            "formwork_m2_lo": r6(form.lo), "formwork_m2_hi": r6(form.hi),
            "outer_face_m2_lo": r6(outer_face[0]), "outer_face_m2_hi": r6(outer_face[1]),
            "inner_face_m2_lo": r6(inner_face[0]), "inner_face_m2_hi": r6(inner_face[1]),
            "top_m2": r6(cl * t), "wp_upturn_inner_m": inner,
            "geometry_status": r["STATUS"],
            "material_status": "HELD (no detail keyed to the run; P1 vs RC; owner Q-65 C material HELD; designer)",
            "alternatives": "+".join(split["alternatives"]),
        })
    return rows


# ------------------------------------------------------------------------------------------------------ plinth segments
def plinth_segments():
    """every T-305 plinth band once, split by substrate (R-T311-3)."""
    rows = []
    for r in read(RES / "agents_t305" / "FACE_LINE_LEDGER_T305.csv"):
        if r["band"] != "plinth":
            continue
        side, L, top = r["side"], f_(r["length_m"]), f_(r["top_m"])
        bottom = f_(r["bottom_m"])
        if side in PASSAGE:
            zone, gb = "passage", None
        elif side in ANNEX_SIDES:
            zone, gb = "annex", GB["annex"]
        else:
            zone, gb = "house", GB["house"]
        if gb is not None and abs(gb["ffl"] - top) > 1e-9:
            raise R.T311Error(f"{side}: plinth top {top} is not the {zone} F.F.L. {gb['ffl']}")
        row = {"floor": r["floor"], "side": side, "portion": r["portion"], "zone": zone, "length_m": L,
               "ground_m": bottom, "ffl_m": top, "gb_top_m": gb["top"] if gb else None,
               "gb_status": gb["status"] if gb else "HELD: no ground-beam top read for a passage face (T-214 covers the house and annex floors only)",
               "face_m2_lo": None, "face_m2_hi": None, "concrete_face_m2_lo": None, "concrete_face_m2_hi": None,
               "wall_course_m2": None, "evidence_status": r["evidence_status"], "t305_ledger_state": r["ledger_state"],
               "t305_geometry_line_id": r["geometry_line_id"]}
        if bottom is not None:
            c, k, tot = R.plinth_split(L, bottom, top, row["gb_top_m"], gb["soffit"] if gb else None)
            row.update(face_m2_lo=r6(tot), face_m2_hi=r6(tot), concrete_face_m2_lo=r6(c), concrete_face_m2_hi=r6(c),
                       wall_course_m2=r6(k))
        else:                                  # pool-court plinth: ground HELD (rim vs deck), T-305 bound kept
            lo, hi = f_(r["held_lo_m2"]), f_(r["held_hi_m2"])
            k = L * (top - gb["top"])
            row.update(face_m2_lo=r6(lo), face_m2_hi=r6(hi), concrete_face_m2_lo=r6(lo - k),
                       concrete_face_m2_hi=r6(hi - k), wall_course_m2=r6(k))
        rows.append(row)
    return rows


# ------------------------------------------------------------------------------------------------------ candidate lookups
def lines_where(d, code=None, prefix=None, floor=None, room=None, pred=None):
    out = []
    for ln in d["lines"]:
        if code and ln["item_code"] != code:
            continue
        if prefix and not ln["item_code"].startswith(prefix):
            continue
        if floor and ln["floor"] != floor:
            continue
        if room and ln["room_id"] != room:
            continue
        if pred and not pred(ln):
            continue
        out.append(ln)
    return out


def one(d, **kw):
    hit = lines_where(d, **kw)
    if len(hit) != 1:
        raise R.T311Error(f"expected exactly one candidate line for {kw}, found {len(hit)}")
    return hit[0]


# the roof whose membrane upturn runs along each parapet chain's inner face (UP-WP-003 0.20 m; the deprecated
# UP-WP-UPTURN-015 0.15 m is superseded). Identified by roof outline: AT216 = the GF house terrace strip (T-221
# TERRACE-550), AT220 = the annex roof (T-221 ROOF-430), AT379 = the 1F roof terraces (+9.70), ROOF-TOP = +13.90.
UPTURN_ROOF = {"GF": "1F-ROOF-AT216", "ANNEX": "1F-ROOF-AT220", "1F": "2F-ROOF-AT379", "2F": "2F-ROOF-TOP"}
FINISH_LINE = {"ANNEX": "GF", "2F": "2F"}      # chains whose outer face lies inside a floor's FIN.EXT.FINISH reach


# ------------------------------------------------------------------------------------------------------ components
def components(d, prows, plrows):
    """R-T311-4: every component once, its trade and its candidate line (or NO_LINE / OTHER_LINE / NOT_APPLICABLE)."""
    B = R.Book()
    out = []

    def add(key, trade, line, lo, hi, unit, status, state, reason):
        q = None if lo is None else R.Rng(lo, hi if hi is not None else lo)
        B.put(key, trade, line, q, unit, status, reason)
        out.append({"component": key, "trade": trade, "candidate_line": line, "ledger_state": state,
                    "qty_lo": r6(lo), "qty_hi": r6(hi if hi is not None else lo), "unit": unit, "status": status,
                    "reason": reason})

    conc_named = [ln for ln in d["lines"] if ln["item_code"].startswith("STR.CONC") and ln["names_parapet"]]
    if conc_named:
        raise R.T311Error(f"a concrete line names a parapet: {[x['line_id'] for x in conc_named]}")
    for ln in d["lines"]:                    # an 'upstand' word on a concrete line must be a non-parapet element
        if ln["item_code"].startswith("STR.CONC") and ln["names_upstand"] and "B15_UPSTAND" not in ln["formula"]:
            raise R.T311Error(f"{ln['line_id']}: names an upstand that is not the water-tank beam B15 (D-44)")
    blk_named = [ln for ln in d["lines"] if ln["item_code"].startswith(("MAS.", "ARCH.WALL")) and ln["names_parapet"]]
    if blk_named:
        raise R.T311Error(f"a blockwork line names a parapet: {[x['line_id'] for x in blk_named]}")
    for ch in ("ANNEX", "GF", "1F", "2F"):
        rr = [r for r in prows if r["chain"] == ch]
        s = lambda k: sum(r[k] or 0.0 for r in rr)          # noqa: E731
        held_1f = ch == "1F"
        st_geo = "HELD" if held_1f else "DRAWING-CONFIRMED"
        add(f"{ch} parapet / concrete (RC part above the slab top)", "CONCRETE", "NO_LINE", s("concrete_m3_lo"),
            s("concrete_m3_hi"), "m3", "HELD", "NO_LINE",
            f"no candidate concrete line names a parapet or upstand; beam lines stop at the slab top (R-T311-2); "
            f"P1 0.30 upstand .. all-RC solid; + HELD {s('solid_held_increment_m3_per_m_b_edge'):.6f} m3 per m of "
            f"build-up depth at the edge (D-39)")
        add(f"{ch} parapet / blockwork (masonry part)", "BLOCKWORK", "NO_LINE", s("block_m2_lo"), s("block_m2_hi"),
            "m2", "HELD", "NO_LINE",
            "0 (all RC: P2 / P3 / architectural hatch) .. solid less the 0.30 upstand (P1, cap 'as per arc.'); the "
            "wall network of the run holds no parapet run (every wall bounds a room), so MAS.BLOCK carries none; "
            f"type white / black HELD (owner Q-65 C); + HELD {s('centreline_m'):.6f} m2 per m of b_edge")
        add(f"{ch} parapet / formwork (cast faces)", "FORMWORK", "NO_LINE", s("formwork_m2_lo"), s("formwork_m2_hi"),
            "m2", "HELD", "NO_LINE", "2 x RC height x centreline (stop-ends at free ends HELD); no formwork family in "
                                     "the candidate (T-199 queued)")
        add(f"{ch} parapet / reinforcement", "REBAR", "NO_LINE", None, None, "t", "HELD", "NO_LINE",
            "detail not keyed to the run; P1 upstand bars unlabelled, cap 5 d12/m + 5 d10/m, P2 6 d12/m + 6 d10/m + "
            "5 d10/m, P3 6 d12/m + 5 d10/m ('/m' meaning not extended from footings, ERS s.3); no reinforcement code "
            "change before an approved stage (owner 2026-10-25 10:33)")
        if ch in FINISH_LINE:
            fl = one(d, code="FIN.EXT.FINISH", floor=FINISH_LINE[ch])
            add(f"{ch} parapet / exterior plaster outer face", "PLASTER_EXT", fl["line_id"], s("outer_face_m2_lo"),
                s("outer_face_m2_hi"), "m2", "DRAWING-CONFIRMED", "IN_LINE",
                f"inside the {FINISH_LINE[ch]} finish line's reach (T-305 IN_LINE bands); the line itself carries no "
                f"quantity ({fl['evidence_state']})")
        else:
            add(f"{ch} parapet / exterior plaster outer face", "PLASTER_EXT", "NO_LINE", s("outer_face_m2_lo"),
                s("outer_face_m2_hi"), "m2", st_geo, "NO_LINE",
                "above the next F.F.L.: no finish line reaches it (T-305 NO_LINE parapet bands)")
        add(f"{ch} parapet / plaster inner face", "PLASTER_PARAPET_INNER", "NO_LINE", s("inner_face_m2_lo"),
            s("inner_face_m2_hi"), "m2", st_geo, "NO_LINE",
            "inner run x height above the printed roof level (T-172); plaster scope UNKNOWN (no specification); the "
            "0.20 m membrane upturn sits on its lowest part (UP-WP-003)")
        add(f"{ch} parapet / top (cap / coping)", "COPING_TOP", "NO_LINE", s("top_m2"), s("top_m2"), "m2",
            "DRAWING-CONFIRMED", "NO_LINE", "centreline x t; cap profile P1 'as per arc.' / plain (sections) HELD")
        up = one(d, code="FIN.WP.ROOF_UPTURN", room=UPTURN_ROOF[ch])
        add(f"{ch} parapet / membrane upturn on the inner face", "WATERPROOFING", up["line_id"],
            s("wp_upturn_inner_m"), s("wp_upturn_inner_m"), "m.l (0.20 m high)",
            "DRAWING-CONFIRMED" if up["measured_net"] is not None else "HELD", "IN_LINE",
            f"part of the roof upturn line's boundary ({up['room_id']}, {up['evidence_state']}, line "
            f"{up['measured_net']} m.l >= this run); UP-WP-003 0.20 m (UP-WP-UPTURN-015 0.15 m deprecated)")
        add(f"{ch} parapet / top arrises (outer + inner)", "CORNERS", "NO_LINE", s("outer_top_arris_m") +
            s("inner_top_arris_m"), s("outer_top_arris_m") + s("inner_top_arris_m"), "m.l", "DRAWING-CONFIRMED",
            "NO_LINE", "own m.l line (owner notes 2026-10-22); never m2 (T-172 / T-305)")
    # plinth
    geo = one(d, code="ARCH.FACADE", floor="GF", pred=lambda x: "plinth" in x["element_id"])
    gb_lines = lines_where(d, code="STR.CONC.GROUND_BEAM")
    gf_block = one(d, code="MAS.BLOCK", floor="GF", pred=lambda x: x["element_id"].endswith("t=0.20"))
    for zone in ("house", "annex", "passage"):
        rr = [r for r in plrows if r["zone"] == zone]
        s = lambda k: sum(r[k] or 0.0 for r in rr)          # noqa: E731
        held = any(r["evidence_status"] == "HELD" for r in rr)
        add(f"plinth {zone} / exterior plaster face", "PLASTER_EXT", "NO_LINE", s("face_m2_lo"), s("face_m2_hi"),
            "m2", "HELD" if held else "DRAWING-CONFIRMED", "NO_LINE",
            f"no finish line reads below the F.F.L.; geometry carrier {geo['line_id']} ({geo['evidence_state']}) "
            f"only (T-305)")
        if zone == "passage":
            add("plinth passage / substrate split", "CONCRETE", "NO_LINE", None, None, "m2", "HELD", "NO_LINE",
                "no ground-beam top read for the passage face (T-214 covers the house and annex floors only)")
            continue
        add(f"plinth {zone} / concrete substrate face (ground-beam outer face)", "CONCRETE",
            f"OTHER_LINE: STR.CONC.GROUND_BEAM ({len(gb_lines)} lines)", s("concrete_face_m2_lo"),
            s("concrete_face_m2_hi"), "m2 of face (no m3)", "HELD" if held else "DRAWING-CONFIRMED", "OTHER_LINE",
            f"the beam's concrete stays in its own lines ({GB[zone]['status']}); the plinth adds a face, never m3; "
            f"spatter dash on it is the T-317 family (NOT_IMPLEMENTED)")
        add(f"plinth {zone} / wall course ground-beam top -> F.F.L.", "BLOCKWORK", gf_block["line_id"],
            s("wall_course_m2"), s("wall_course_m2"), "m2", "DRAWING-CONFIRMED", "OTHER_LINE",
            "the GF wall starts at the structural slab top (masonry_area_v1 Q-60 A: storey slab top to slab top), so "
            "the 0.05 m course is inside the GF t=0.20 wall panel already; never booked again")
    # the 1F face standing on the annex roof
    face = [r for r in read(RES / "agents_t305" / "FACE_LINE_LEDGER_T305.csv") if r["band"] == "over_lower_roof"]
    a = sum(f_(r["geometric_m2"]) for r in face)
    L = sum(f_(r["length_m"]) for r in face)
    add("annex-roof band (1F SE-1 +4.30 -> +5.50) / exterior plaster", "PLASTER_EXT", "NO_LINE", a, a, "m2",
        "DRAWING-CONFIRMED", "NO_LINE", "a face on a lower roof, below its own floor's F.F.L. (T-305)")
    up = one(d, code="FIN.WP.ROOF_UPTURN", room=UPTURN_ROOF["ANNEX"])
    add("annex-roof band / membrane upturn at its foot", "WATERPROOFING", up["line_id"], L, L, "m.l (0.20 m high)",
        "DRAWING-CONFIRMED", "IN_LINE", "the annex roof boundary includes the house wall it abuts (UP-WP-003)")
    return out, B


# ------------------------------------------------------------------------------------------------------ closure, freelancer
def closure(d, prows, plrows, comps):
    t305 = json.loads((RES / "agents_t305" / "summary.json").read_text(encoding="utf-8"))
    faces = read(RES / "agents_t305" / "FACE_LINE_LEDGER_T305.csv")
    items = read(RES / "agents_t305" / "ITEMS_T305.csv")

    def fsum(band, state, col):
        return sum(f_(r[col]) or 0.0 for r in faces if r["band"] == band and r["ledger_state"] == state)

    def ps(chains, k):
        return sum(r[k] or 0.0 for r in prows if r["chain"] in chains)

    def isum(kind, col):
        return sum(f_(r[col]) or 0.0 for r in items if r["kind"] == kind)

    rows = []

    def row(what, ours_lo, ours_hi, ref_lo, ref_hi, ref, cause):
        rows.append({"check": what, "this_ledger_lo": r6(ours_lo), "this_ledger_hi": r6(ours_hi),
                     "reference_lo": r6(ref_lo), "reference_hi": r6(ref_hi), "reference": ref,
                     "residual_lo": r6(ours_lo - ref_lo), "residual_hi": r6(ours_hi - ref_hi), "cause": cause})

    row("parapet outer faces GF + 1F (NO_LINE)", ps(("GF", "1F"), "outer_face_m2_lo"), ps(("GF", "1F"), "outer_face_m2_hi"),
        fsum("parapet", "NO_LINE", "geometric_m2") + fsum("parapet", "NO_LINE", "held_lo_m2"),
        fsum("parapet", "NO_LINE", "geometric_m2") + fsum("parapet", "NO_LINE", "held_hi_m2"),
        "T-305 FACE_LINE_LEDGER parapet bands (66.428 + 1.870 .. 7.248)",
        "T-305 rows carry 4-decimal face areas (T-159 table); this ledger multiplies T-172 run x height unrounded")
    an = sum(f_(r["length_m"]) * 0.5 for r in faces if r["floor"] == "GF" and r["ledger_state"] == "IN_LINE"
             and f_(r["top_m"]) == 4.80)
    row("annex parapet outer face inside the GF finish line (+4.30 -> +4.80 of the annex EDGE bands)",
        ps(("ANNEX",), "outer_face_m2_lo"), ps(("ANNEX",), "outer_face_m2_hi"), an, an,
        "T-305 IN_LINE annex EDGE bands, their top 0.50 m",
        "T-172 run lengths carry 4 decimals (SW-3 6.2001, NE-6 10.8 / 10.4001) against T-305's 3-decimal bands")
    f2 = sum(f_(r["length_m"]) * 0.5 for r in faces if r["floor"] == "2F" and r["ledger_state"] == "IN_LINE")
    row("2F parapet outer face inside the 2F finish line (+13.90 -> +14.40)", ps(("2F",), "outer_face_m2_lo"),
        ps(("2F",), "outer_face_m2_hi"), f2, f2, "T-305 IN_LINE 2F bands, their top 0.50 m", "none")
    pl_lo = fsum("plinth", "NO_LINE", "geometric_m2") + fsum("plinth", "NO_LINE", "held_lo_m2")
    pl_hi = fsum("plinth", "NO_LINE", "geometric_m2") + fsum("plinth", "NO_LINE", "held_hi_m2")
    row("plinth faces (all zones)", sum(r["face_m2_lo"] or 0 for r in plrows), sum(r["face_m2_hi"] or 0 for r in plrows),
        pl_lo, pl_hi, "T-305 plinth bands (66.736 + 4.952 .. 6.013)", "none")
    row("plinth substrate closes: concrete face + wall course = face (house + annex)",
        sum((r["concrete_face_m2_lo"] or 0) + (r["wall_course_m2"] or 0) for r in plrows if r["zone"] != "passage"),
        sum((r["concrete_face_m2_hi"] or 0) + (r["wall_course_m2"] or 0) for r in plrows if r["zone"] != "passage"),
        sum(r["face_m2_lo"] or 0 for r in plrows if r["zone"] != "passage"),
        sum(r["face_m2_hi"] or 0 for r in plrows if r["zone"] != "passage"), "this ledger", "none")
    row("parapet inner faces", ps(("ANNEX", "GF", "1F", "2F"), "inner_face_m2_lo"),
        ps(("ANNEX", "GF", "1F", "2F"), "inner_face_m2_hi"), isum("PARAPET_INNER_FACE", "qty_lo"),
        isum("PARAPET_INNER_FACE", "qty_hi"), "T-305 ITEMS (94.431 .. 99.534)", "T-305 items carry 3 decimals")
    row("parapet tops", ps(("ANNEX", "GF", "1F", "2F"), "top_m2"), ps(("ANNEX", "GF", "1F", "2F"), "top_m2"),
        isum("PARAPET_TOP", "qty_lo"), isum("PARAPET_TOP", "qty_hi"), "T-305 ITEMS (26.801)",
        "T-305 items carry 3 decimals")
    ob = ps(("ANNEX", "GF", "1F", "2F"), "outer_top_arris_m")
    ib = ps(("ANNEX", "GF", "1F", "2F"), "inner_top_arris_m")
    row("parapet top arrises outer + inner (m.l)", ob + ib, ob + ib, 138.481 + 133.482, 138.481 + 133.482,
        "T-305 ITEMS corners: parapet outer 138.481 + inner 133.482 m.l", "T-305 rounds the inner run to 3 decimals")
    # every upturn line holds at least the parapet / band runs this ledger books on it
    per_line = {}
    for c in comps:
        if c["trade"] == "WATERPROOFING":
            per_line[c["candidate_line"]] = per_line.get(c["candidate_line"], 0.0) + c["qty_lo"]
    for lid, booked in sorted(per_line.items()):
        ln = one(d, pred=lambda x, lid=lid: x["line_id"] == lid)
        if ln["measured_net"] is not None and booked > ln["measured_net"] + 1e-6:
            raise R.T311Error(f"{lid}: {booked} m.l booked on a line of {ln['measured_net']} m.l")
        row(f"upturn line {lid} ({ln['room_id']}) contains the runs booked on it (m.l)", booked, booked,
            ln["measured_net"] if ln["measured_net"] is not None else booked,
            ln["measured_net"] if ln["measured_net"] is not None else booked,
            f"candidate line ({ln['evidence_state']})",
            "the line also carries the roof's other walls / gap closures / openings (not parapet)" if ln["measured_net"]
            else "line BLOCKED_RFI (outline not drawn): no quantity to contain the run; the run stays HELD")
    return rows


FREELANCER = {   # comparison only (MISSION: development reference, never a target); tests/alsenan/registers_b1
    "BLK 172 'الدروه'": (66.00, 1.00), "BLK 177 'الدروه'": (42.85, 1.80), "BLK 178 (2F ring)": (29.80, 1.00)}


def freelancer_rows(prows):
    lens = {"ANNEX+GF": sum(r["centreline_m"] for r in prows if r["chain"] in ("ANNEX", "GF")),
            "1F": sum(r["centreline_m"] for r in prows if r["chain"] == "1F"),
            "2F": sum(r["centreline_m"] for r in prows if r["chain"] == "2F")}
    blk = {k: (sum(r["block_m2_lo"] for r in prows if r["chain"] in ks), sum(r["block_m2_hi"] for r in prows
                                                                              if r["chain"] in ks))
           for k, ks in (("ANNEX+GF", ("ANNEX", "GF")), ("1F", ("1F",)), ("2F", ("2F",)))}
    out = []
    for (name, (L, h)), key, printed in zip(FREELANCER.items(), ("ANNEX+GF", "1F", "2F"),
                                            ("0.50 above +4.30 / +5.50", "1.30 printed NE / SW; 0.448 .. 1.30 CAD",
                                             "0.50 above +13.90")):
        out.append({"freelancer_row": name, "his_length_m": L, "his_height_m": h, "his_m2": r6(L * h),
                    "drawing_centreline_m": r6(lens[key]), "length_diff_m": r6(L - lens[key]),
                    "drawing_height_above_finish": printed, "drawing_block_m2_lo": r6(blk[key][0]),
                    "drawing_block_m2_hi": r6(blk[key][1]),
                    "cause": "material: every printed alternative has >= 0.30 m RC above the slab top (P1 upstand) or "
                             "is all RC (P2 / P3 / sections), he books the whole height as block and no parapet "
                             "concrete in his RC workbook; height: his figure exceeds the printed height above the "
                             "finished roof (the slab-top increment b_edge is HELD, D-39)",
                    "verdict_proposal": "UNRESOLVED (material HELD Q-65 C / designer); height RULE_DIFFERENCE pending "
                                        "b_edge; concrete omission in his RC workbook (no parapet row) = MISSING both"})
    return out


# ------------------------------------------------------------------------------------------------------ outputs
def csv_text(rows, cols):
    b = io.StringIO()
    w = csv.DictWriter(b, fieldnames=cols, lineterminator="\n", extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow({k: ("" if r.get(k) is None else (f"{r[k]:.6f}" if isinstance(r[k], float) else r[k]))
                    for k in cols})
    return b.getvalue()


PCOLS = ["chain", "side", "kind", "roof_level", "parapet_top", "outer_top_arris_m", "inner_top_arris_m",
         "centreline_m", "t_m", "h_above_finish_m", "h_held_lo", "h_held_hi", "solid_m3_lo", "solid_m3_hi",
         "solid_held_increment_m3_per_m_b_edge", "concrete_m3_lo", "concrete_m3_hi", "block_m2_lo", "block_m2_hi",
         "formwork_m2_lo", "formwork_m2_hi", "outer_face_m2_lo", "outer_face_m2_hi", "inner_face_m2_lo",
         "inner_face_m2_hi", "top_m2", "wp_upturn_inner_m", "geometry_status", "material_status", "alternatives"]
LCOLS = ["floor", "side", "portion", "zone", "length_m", "ground_m", "ffl_m", "gb_top_m", "gb_status", "face_m2_lo",
         "face_m2_hi", "concrete_face_m2_lo", "concrete_face_m2_hi", "wall_course_m2", "evidence_status",
         "t305_ledger_state", "t305_geometry_line_id"]
CCOLS = ["component", "trade", "candidate_line", "ledger_state", "qty_lo", "qty_hi", "unit", "status", "reason"]
KCOLS = ["check", "this_ledger_lo", "this_ledger_hi", "reference_lo", "reference_hi", "reference", "residual_lo",
         "residual_hi", "cause"]
FCOLS = ["freelancer_row", "his_length_m", "his_height_m", "his_m2", "drawing_centreline_m", "length_diff_m",
         "drawing_height_above_finish", "drawing_block_m2_lo", "drawing_block_m2_hi", "cause", "verdict_proposal"]


def outputs():
    d = candidate()
    prows, plrows = parapet_runs(), plinth_segments()
    comps, _ = components(d, prows, plrows)
    clo = closure(d, prows, plrows, comps)
    fr = freelancer_rows(prows)

    def tot(trade, state=None, unit=None):
        rr = [c for c in comps if c["trade"] == trade and (state is None or c["ledger_state"] == state)
              and (unit is None or c["unit"] == unit) and c["qty_lo"] is not None]
        return [r6(sum(c["qty_lo"] for c in rr)), r6(sum(c["qty_hi"] for c in rr))]

    summ = {
        "candidate": {k: d[k] for k in ("lines_file", "source", "lines_json_sha256_8", "lines_csv_sha256_8",
                                         "lines_total")},
        "parapet_runs": len(prows), "plinth_segments": len(plrows), "components": len(comps),
        "by_state": {s: sum(1 for c in comps if c["ledger_state"] == s) for s in ("IN_LINE", "NO_LINE", "OTHER_LINE")},
        "double": 0,
        "parapet_concrete_m3": tot("CONCRETE", "NO_LINE", "m3"),
        "parapet_concrete_held_increment_m3_per_m_b_edge": r6(sum(r["solid_held_increment_m3_per_m_b_edge"]
                                                                  for r in prows)),
        "parapet_block_m2": tot("BLOCKWORK", "NO_LINE"),
        "parapet_formwork_m2": tot("FORMWORK"),
        "parapet_outer_face_no_line_m2": [r6(sum(r["outer_face_m2_lo"] for r in prows if r["chain"] in ("GF", "1F"))),
                                          r6(sum(r["outer_face_m2_hi"] for r in prows if r["chain"] in ("GF", "1F")))],
        "parapet_inner_face_m2": tot("PLASTER_PARAPET_INNER"), "parapet_top_m2": tot("COPING_TOP"),
        "parapet_arrises_ml": tot("CORNERS"),
        "wp_upturn_in_line_ml": tot("WATERPROOFING", "IN_LINE"),
        "plinth_face_m2": [r6(sum(r["face_m2_lo"] or 0 for r in plrows)), r6(sum(r["face_m2_hi"] or 0 for r in plrows))],
        "plinth_concrete_face_m2": [r6(sum(r["concrete_face_m2_lo"] or 0 for r in plrows)),
                                    r6(sum(r["concrete_face_m2_hi"] or 0 for r in plrows))],
        "plinth_wall_course_m2": r6(sum(r["wall_course_m2"] or 0 for r in plrows)),
        "closure_max_abs_residual": r6(max(max(abs(c["residual_lo"]), abs(c["residual_hi"])) for c in clo
                                           if not c["check"].startswith("upturn line"))),
        "freelancer_parapet_block_m2": r6(sum(L * h for L, h in FREELANCER.values())),
        "concrete_lines_naming_an_upstand_not_parapet": [
            {"line_id": ln["line_id"], "item_code": ln["item_code"], "why": "water-tank column held on D-44 (B15 "
             "upstand / downstand) and D-39; blank, not a parapet carrier"}
            for ln in d["lines"] if ln["item_code"].startswith("STR.CONC") and ln["names_upstand"]],
        "rebar_lines_naming_an_upstand": [ln["line_id"] for ln in d["lines"] if ln["item_code"] == "STR.REBAR"
                                          and ln["names_upstand"]],
    }
    return {"PARAPET_RUN_LEDGER_T311.csv": csv_text(prows, PCOLS),
            "PLINTH_SEGMENT_LEDGER_T311.csv": csv_text(plrows, LCOLS),
            "COMPONENT_OWNER_T311.csv": csv_text(comps, CCOLS),
            "CLOSURE_T311.csv": csv_text(clo, KCOLS),
            "FREELANCER_T311.csv": csv_text(fr, FCOLS),
            "summary.json": json.dumps(summ, indent=1, ensure_ascii=False) + "\n"}


def main(argv):
    if argv[:1] == ["--extract"]:
        extract(argv[1], *(argv[2:3] or []))
    elif argv[:1] == ["--write"]:
        for name, text in outputs().items():
            (HERE / name).write_text(text, encoding="utf-8")
            print("wrote", name)
    elif argv[:1] == ["--check"]:
        bad = [n for n, t in outputs().items() if (HERE / n).read_text(encoding="utf-8") != t]
        print("CHECK", "OK" if not bad else f"DIFFERS: {bad}")
        return 1 if bad else 0
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
