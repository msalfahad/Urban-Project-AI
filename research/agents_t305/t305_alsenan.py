"""T-305 on the development villa (P7757): the EXTERIOR PLASTER / SIGMA FACE-TO-LINE LEDGER. Every drawn exterior face
band (T-159) once against the candidate's line ids (ARCH_TAKEOFF_V3.0.18), every facade opening once as a hole on its
face, and the items beside the faces (parapet inner faces and tops, corners in m.l, frames, drip, boundary wall, domes)
with their owner. Research only: prints and writes ids, states, levels, lengths and areas; no coordinate, no name, no
drawing content.

Sources (merged unless stated):
  faces           research/agents_t159/FACADE_SIDES_T159.csv (T-159 MERGED 349251f; Checker re-measured 1F NE-2, SE-1)
  opening ids     research/agents_t249/OPENINGS_T249.csv ENGINE_REF (engine OP-nnn per storey -> census id)
  opening sizes   research/agents_t237/OPENING_SIZES_T237.csv merged (T-175 -> T-201 -> T-207 -> T-238)
  physical scope  research/agents_t175/T175_OPENING_CONSEQUENCES.csv (construction BLOCK / GLAZED, exterior family)
  W17 hole        research/agents_t302/W17_HOLE_LEDGER_T302.csv (EXTERIOR developed hole 8.1434 m2)
  parapets        research/agents_t162/PARAPETS_T162.csv (T-162 r2 MERGED 4cc2847; T-172 MERGED dd1d6e4)
  corners         research/agents_t162/CORNERS_R2_T162.csv
  face geometry   FACE_GEOMETRY_T305.json (--geometry: two glazing bindings read this run from the plan DXF by handle)
  candidate       CANDIDATE_V3018_FACADE_LINES.json (--extract <own V3.0.18 run>/v3018)

    python3 -I research/agents_t305/t305_alsenan.py --extract <run>/t266/v3018
    python3 -I research/agents_t305/t305_alsenan.py --geometry <t159 rings json> <P7757.dxf>
    python3 -I research/agents_t305/t305_alsenan.py --write
    python3 -I research/agents_t305/t305_alsenan.py --check
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RES = ROOT / "research"
sys.path.insert(0, str(HERE))
import facade_line_ledger as R  # noqa: E402

CAND = HERE / "CANDIDATE_V3018_FACADE_LINES.json"
GEOM = HERE / "FACE_GEOMETRY_T305.json"
LINES_FILE = "V3_0_18_BOQ_LINES.json"
FACADE_CODES = ("ARCH.FACADE_RUN", "ARCH.FACADE", "FIN.EXT.FINISH")

# printed levels (T-159 section 2 table, each with its sheet); the reach of each candidate line's formula
FFL = {"GF": {"house": 1.00, "annex": 0.30}, "1F": 5.50, "2F": 9.70}
NEXT_FFL = {"GF": 5.50, "1F": 9.70, "2F": None}
PARAPET_TOP_2F = 14.40          # '1440' and 420 + 50 on all four elevations (UP-FACADE-001 TO_PARAPET for the top floor)
ANNEX_SIDES = {"SE-1", "SW-1", "SW-2", "NW-1", "SW-3", "NE-6"}   # T-159 GF_OUTSIDE["annex"] (sides on the annex block)
P1_ANNEX = {"P-1"}                                              # the passage face of the annex (+0.30 F.F.L.)


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


# --------------------------------------------------------------------------------------------- extract (needs the run)
def extract(run_dir):
    run_dir = Path(run_dir)
    lp = run_dir / LINES_FILE
    raw = lp.read_bytes()
    d = json.loads(raw.decode("utf-8"))
    lines = d if isinstance(d, list) else d["lines"]
    csvp = run_dir / LINES_FILE.replace(".json", ".csv")
    keep, census = [], {}
    words = ("FACADE", "EXT", "PARAPET", "SIGMA", "COPING", "SOFFIT", "BOUNDARY", "FENCE")
    for ln in lines:
        code = ln.get("item_code") or ""
        loc = ln.get("location") or {}
        hay = " ".join(str(x) for x in (code, loc.get("room_id"), loc.get("element_id"))).upper()
        if any(w in hay for w in words):
            census[code] = census.get(code, 0) + 1
        if code not in FACADE_CODES:
            continue
        calc = ln.get("calculation") or {}
        inp = calc.get("inputs") or {}
        br = ln.get("bounded_range") or None
        v3 = inp.get("v3_0") or {}
        keep.append({"line_id": ln["line_id"], "item_code": code, "floor": loc.get("floor"),
                     "room_id": loc.get("room_id"), "element": str(loc.get("element_id", "")).split(":", 1)[-1],
                     "unit": ln.get("unit"), "evidence_state": ln.get("evidence_state"),
                     "approval_state": ln.get("approval_state"), "measured_net": ln.get("measured_net"),
                     "gross": ln.get("gross"),
                     "range": None if not br else [br.get("low"), br.get("high")],
                     "perimeter_m": inp.get("perimeter_m"),
                     "height_state": (inp.get("height") or {}).get("state"),
                     "v3_0_geometric_m": v3.get("geometric_perimeter_m"), "v3_0_billable_m": v3.get("billable_run_m"),
                     "v3_0_passages_released": v3.get("passages_released"),
                     "rfi_head": str((ln.get("rfi") or {}).get("question") or "")[:120]})
    out = {"source": "own V3.0.18 run (research/agents_t266/v3018_run.py after research/agents_t167/v304_run.py) on "
                     "Drive 'Alsenan chalet project' P7757_DXF_COMPRESSED.zip -> P7757.dxf (ab54dd55) and "
                     "'ST7757 dxf.dxf' (9f9d1179)",
           "lines_json_sha256_8": hashlib.sha256(raw).hexdigest()[:8],
           "lines_csv_sha256_8": hashlib.sha256(csvp.read_bytes()).hexdigest()[:8] if csvp.exists() else None,
           "lines_total": len(lines),
           "census_by_code_of_lines_naming_facade_ext_parapet_soffit_boundary": dict(sorted(census.items())),
           "facade_lines": sorted(keep, key=lambda x: (x["floor"] or "", x["item_code"], x["element"]))}
    CAND.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {CAND.name}: {len(keep)} facade lines of {len(lines)}")


# ----------------------------------------------------------------------------------- geometry (needs the DXF + rings)
def geometry(rings_path, dxf_path):
    """two bindings the face table does not carry: W18 (1F, no engine opening) and W03 (GF curved glazing, no engine
    opening) against the T-159 sides, from the plan glazing entities by handle (T-249 HANDLES). Lengths only."""
    sys.path.insert(0, str(RES / "agents_t159"))
    import t159_alsenan as A   # noqa: E402
    import t159_sides as S     # noqa: E402
    import ezdxf               # noqa: E402
    Rg = json.loads(Path(rings_path).read_text(encoding="utf-8"))
    doc = ezdxf.readfile(dxf_path)

    def sides_of(fl):
        E = A.local(Rg, fl)
        drop = ()
        if fl == "GF":
            p = Rg["floors"]["GF"]["passage"]
            drop = [m["edge_index"] for ps in p["passages"] if ps["state"] == "OPEN_AIR" for m in ps["mouths"]
                    if m["edge_index"] not in p["wall_end_gaps"]]
        return {s["name"]: s for s in S.name_sides(S.split_sides(E, A.AXES, drop))}

    def ys(fl, handles):
        b = Rg["floors"][fl]["box"]
        out = []
        for h in handles:
            e = doc.entitydb.get(h)
            if e is None or e.dxftype() != "LINE":
                continue
            out += [e.dxf.start[1] / 1000.0 - b[1], e.dxf.end[1] / 1000.0 - b[1]]
        return min(out), max(out)

    s1 = sides_of("1F")
    lo, hi = ys("1F", "C33 C34 C36 C37 C38 C39 C3A C3C C3D C3E".split())
    nw4 = s1["NW-4"]
    f_lo, f_hi = sorted((nw4["a"][1], nw4["b"][1]))
    w18 = {"face": "1F NW-4", "face_len_m": r6(f_hi - f_lo), "symbol_width_m": r6(hi - lo), "on_face_m": r6(min(hi, f_hi) - max(lo, f_lo)),
           "beyond_face_m": r6((hi - lo) - (min(hi, f_hi) - max(lo, f_lo)))}
    s0 = sides_of("GF")
    g_lo, g_hi = ys("GF", ["26D", "275"])
    pieces = {}
    for nm in ("NW-3", "NW-4", "NW-5"):
        s = s0[nm]
        a, b = sorted((s["a"][1], s["b"][1]))
        if s["kind"] == "ARC":
            pieces[nm] = {"kind": "ARC", "len_m": r6(s["len_m"]),
                          "glazed_m": r6(s["len_m"]) if (g_lo <= a + 1e-6 and g_hi >= b - 1e-6) else None}
        else:
            pieces[nm] = {"kind": s["kind"], "len_m": r6(s["len_m"]),
                          "glazed_m": r6(max(0.0, min(b, g_hi) - max(a, g_lo)))}
    w03 = {"glazing_end_lines": "26D / 275 (T-249 handles)", "glazing_span_m": r6(g_hi - g_lo), "pieces": pieces}
    GEOM.write_text(json.dumps({"source": "P7757.dxf (ab54dd55) plan glazing entities by handle (T-249) against the "
                                          "T-159 sides (t159_extract rings); lengths only",
                                "W18": w18, "W03": w03}, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"W18": w18, "W03": w03}, indent=1))


# ------------------------------------------------------------------------------------------------------ the ledger
def candidate():
    d = json.loads(CAND.read_text(encoding="utf-8"))
    by = {}
    for ln in d["facade_lines"]:
        by.setdefault((ln["floor"], ln["item_code"], ln["element"]), []).append(ln)
    return d, by


def lines_model(by):
    """R.FacadeLine per floor for the FINISH owner (FIN.EXT.FINISH) and the geometry carrier (ARCH.FACADE)."""
    fin, geo = [], []
    for fl in ("GF", "1F", "2F"):
        top = NEXT_FFL[fl] if NEXT_FFL[fl] is not None else PARAPET_TOP_2F
        for code, bucket in (("FIN.EXT.FINISH", fin), ("ARCH.FACADE", geo)):
            for ln in by.get((fl, code, "facade"), []):
                bucket.append(R.FacadeLine(ln["line_id"], code, fl, "STOREY", 0.0, top, ln["evidence_state"],
                                           ln["measured_net"]))
        for ln in by.get((fl, "ARCH.FACADE", "facade below F.F.L. (plinth)"), []):
            geo.append(R.FacadeLine(ln["line_id"], "ARCH.FACADE", fl, "PLINTH", None, None, ln["evidence_state"],
                                    ln["measured_net"]))
    return fin, geo


def side_ffl(fl, side):
    if fl != "GF":
        return FFL[fl]
    return FFL["GF"]["annex"] if side in ANNEX_SIDES or side in P1_ANNEX else FFL["GF"]["house"]


def portions():
    """T-159 bands -> R.Portion, cut at the next F.F.L. where a band crosses it (GF house edge faces to +6.00)."""
    out, notface = [], []
    for r in read(RES / "agents_t159" / "FACADE_SIDES_T159.csv"):
        fl, side = r["FLOOR"], r["SIDE"]
        if r["KIND"] == "NOT_A_FACE":
            notface.append({"floor": fl, "side": side, "length_m": None, "why": r["SOURCE"]})
            continue
        L = f_(r["PORTION_LEN_M"])
        bot, top, area = f_(r["BOTTOM_M"]), f_(r["TOP_M"]), f_(r["AREA_M2"])
        hr = [f_(x) for x in r["HELD_RANGE_H_M"].split("..")] if r["HELD_RANGE_H_M"] else [None, None]
        ffl = side_ffl(fl, side)
        nxt = NEXT_FFL[fl]
        base = dict(floor=fl, side=side, facing=r["FACING"], portion=r["PORTION"], length_m=L, status=r["STATUS"])
        if r["PORTION"] == "SLAB_EDGE_BELOW":
            out.append(R.Portion(**base, bottom=None, top=top, area_m2=None, band_kind="slab_edge"))
            continue
        if area is None:            # HELD band: a height range on a known length
            lo_h, hi_h = hr
            if bot is None:          # pool-court plinth: bottom HELD, top the F.F.L.
                kind = "plinth"
            else:
                kind = "parapet" if (nxt is not None and bot >= nxt - 1e-9) else "storey"
            out.append(R.Portion(**base, bottom=bot, top=top, area_m2=None, band_kind=kind,
                                 held_lo=r6(L * lo_h), held_hi=r6(L * hi_h)))
            continue
        if r["PORTION"] == "STOREY+PARAPET":
            out.append(R.Portion(**base, bottom=bot, top=top, area_m2=area, band_kind="storey"))
            continue
        parts = R.split_at(bot, top, nxt)
        for b0, b1 in parts:
            kind = R.band_kind(fl, b0, b1, ffl, nxt, r["PORTION"])
            # an unsplit band keeps T-159's own area (CAD-top-line parapets are integrated, not length x rounded top);
            # a band cut at the next F.F.L. has printed levels at both ends: length x height
            a = area if len(parts) == 1 else r6(L * (b1 - b0))
            out.append(R.Portion(**base, bottom=b0, top=b1, area_m2=a, band_kind=kind))
    return out, notface


# --- openings: census id per (floor, engine OP) and the hole on its face (R-T305-2)
DOOR_FALLBACK = "ASSUMED — OWNER-APPROVED"


def opening_rows(geom):
    eng = {}
    for r in read(RES / "agents_t249" / "OPENINGS_T249.csv"):
        for tok in str(r["ENGINE_REF"]).replace("/", " ").split():
            if tok.startswith(("OP-", "COP-")):
                eng[(r["FLOOR"], tok)] = r["ID"]
    sizes = {}
    for r in read(RES / "agents_t237" / "OPENING_SIZES_T237.csv"):
        sizes.setdefault(r["census_id"], r)
    cons = {r["opening"]: r for r in read(RES / "agents_t175" / "T175_OPENING_CONSEQUENCES.csv")}
    w17 = next(r for r in read(RES / "agents_t302" / "W17_HOLE_LEDGER_T302.csv") if r["face"].startswith("EXTERIOR"))
    # (floor, side) -> engine refs on that side, from the face table (one listing per side)
    on_side = {}
    for r in read(RES / "agents_t159" / "FACADE_SIDES_T159.csv"):
        if r["KIND"] == "NOT_A_FACE" or not r["OPENINGS_ON_OUTLINE_M"]:
            continue
        refs = [t.split()[0] for t in r["OPENINGS_ON_OUTLINE_M"].split(";")]
        on_side.setdefault((r["FLOOR"], r["SIDE"]), refs)
    rows = []

    def add(fl, side, cid, eref, w, h_lo, h_hi, hole, status, cap=None, window=None, src="", note=""):
        rows.append({"floor": fl, "side": side, "opening": cid, "engine_ref": eref, "width_m": r6(w),
                     "sill_m": r6(h_lo), "head_m": r6(h_hi), "hole_m2": r6(hole), "status": status,
                     "cap_m2": r6(cap), "window_measure_m2": r6(window), "source": src, "note": note})

    for (fl, side), refs in sorted(on_side.items()):
        for eref in refs:
            cid = eng.get((fl, eref))
            if fl == "GF" and eref == "OP-001":
                # T-109: 0.200 m of the boundary-wall end lies over the annex wall end (a drafting gap closed by the
                # wall cap): it is that wall's outer face, kept in the run; not a building opening, no hole
                add(fl, side, "none (OP-001 0.200 m)", eref, 0.2, None, None, 0.0, "NOT_AN_OPENING",
                    src="T-109 WALL_END_GAP", note="drafting gap: wall face, no hole (T-109)")
                continue
            if cid is None:
                raise R.LedgerError(f"{fl} {side} {eref}: no census id")
            sz = sizes[cid]
            con = cons.get(cid) or {}
            w = f_(sz["merged_w"])
            sill, head = f_(sz["merged_sill"]), f_(sz["merged_head"])
            fixed = f_(sz["merged_fixed_m2"])
            cap = f_(sz["merged_cap_m2"])
            st = sz["merged_status"]
            kind = con.get("kind") or ""
            if cid == "W17":
                add(fl, side, cid, eref, w, None, None, f_(w17["hole_m2"]), "DRAWING-CONFIRMED",
                    window=9.870, src="T-302 W17_HOLE_LEDGER (EXTERIOR developed hole)",
                    note="window line measure 9.870 (owner Q-76 A) is the aluminium item, never the hole")
            elif kind == "DOOR" and st == "ASSUMED":
                add(fl, side, cid, eref, w, 0.0, head, w * head, DOOR_FALLBACK,
                    src="T-175 / T-237 (Q-55 C: 2.20 m where no height is printed)")
            elif cid == "D-GF-07":
                add(fl, side, cid, eref, w, 0.0, head, None, "HELD", cap=w * head,
                    src="T-175 hold (T-161 F07c: render single leaf vs printed 2.00 x 2.50 double; designer D-53)",
                    note="printed 2.00 x 2.50 = 5.000 is the cap; leaf / hole width HELD")
            elif fixed is not None:
                rect = w * (head - sill)
                add(fl, side, cid, eref, w, sill, head, fixed, "DRAWING-CONFIRMED", window=rect,
                    src=sz["merged_src"], note="arched hole outline (T-238); Q-32 A rectangle is the window measure")
            elif sill is not None and head is not None:
                add(fl, side, cid, eref, w, sill, head, w * (head - sill),
                    "DRAWING-CONFIRMED" if st in ("PRINTED", "DRAWING-CONFIRMED") else st, src=sz["merged_src"])
            elif cap is not None and "sill" in st:
                # the window's own height is established (cap = width x height); only its sill datum is HELD,
                # which moves the hole inside the band, not its area
                add(fl, side, cid, eref, w, None, None, cap, "DRAWING-CONFIRMED", src=sz["merged_src"],
                    note="area = width x established height; sill position HELD (does not move the area)")
            else:
                add(fl, side, cid, eref, w, None, None, None, "HELD", cap=None, src=sz["merged_src"] +
                    " / T-175 " + (con.get("hold_cause") or ""), note="height HELD: cap = width x the face band")
    # census openings on exterior faces with no engine opening (T-249: V2.9 misses them), bound by geometry
    g = geom
    w18 = g["W18"]
    sz = sizes["W18"]
    sill, head = f_(sz["merged_sill"]), f_(sz["merged_head"])
    add("1F", "NW-4", "W18", "none (V2.9 misses it)", f_(sz["merged_w"]), sill, head,
        w18["on_face_m"] * (head - sill), "DRAWING-CONFIRMED",
        window=f_(sz["merged_w"]) * (head - sill), src="T-249 plan symbol + T-237 printed 50 / 84 / 216",
        note=f"symbol {w18['symbol_width_m']} m, face {w18['on_face_m']} m: {w18['beyond_face_m']} m of frame "
             "behind the recess return (no face there)")
    sz = sizes["W03"]
    head = f_(sz["merged_head"])
    for nm, pc in g["W03"]["pieces"].items():
        if not pc["glazed_m"]:
            continue
        add("GF", nm, "W03" if nm == "NW-4" else f"W03 (frame end on {nm})", "none (V2.9 misses it)",
            pc["glazed_m"], 0.0, head, pc["glazed_m"] * head, "DRAWING-CONFIRMED",
            window=(f_(sz["merged_w"]) * head) if nm == "NW-4" else None,
            src="T-249 glazing lines + T-237 printed 657 / 4300 from +1.00 (Q-38 A width for the window line)",
            note="glazed line (T-175 GLAZED; Q-69 B: no masonry in the span): the face is glass from +1.00 to +5.30")
    return rows


# --- the ledger itself
def build():
    d, by = candidate()
    fin, geo = lines_model(by)
    P, notface = portions()
    geom = json.loads(GEOM.read_text(encoding="utf-8"))
    ops = opening_rows(geom)
    floors_reach = {fl: (0.0, NEXT_FFL[fl] if NEXT_FFL[fl] is not None else PARAPET_TOP_2F) for fl in FFL}
    book = R.Book()
    face_rows = []
    for k, p in enumerate(P):
        ffl = side_ffl(p.floor, p.side)
        floors = {p.floor: (ffl, NEXT_FFL[p.floor] if NEXT_FFL[p.floor] is not None else PARAPET_TOP_2F)}
        st, ln, why = R.owner_of(p, fin + [g for g in geo if g.kind == "PLINTH"], floors, lowest="GF")
        geo_ln = None
        if st == "IN_LINE" and ln.kind == "PLINTH":
            # the plinth has a geometry line only: no finish line reads it (FIN.EXT.FINISH = ARCH.FACADE storey)
            geo_ln, st, ln = ln, "NO_LINE", None
            why = ("plinth: geometry carried by the HELD plinth line; no FIN.EXT.FINISH line reads the plinth, so the "
                   "plaster below the F.F.L. has no finish line")
        elif st == "IN_LINE":
            g = [x for x in geo if x.floor == p.floor and x.kind == "STOREY"]
            geo_ln = g[0] if len(g) == 1 else None
        key = f"{p.floor}|{p.side}|{p.portion}|{p.bottom}|{p.top}"
        status = p.status if p.area_m2 is not None else "HELD"
        book.add(key, st, ln.line_id if ln else None, side=p.side)
        face_rows.append({
            "floor": p.floor, "side": p.side, "facing": p.facing, "portion": p.portion, "band": p.band_kind,
            "length_m": r6(p.length_m), "bottom_m": r6(p.bottom), "top_m": r6(p.top),
            "geometric_m2": r6(p.area_m2), "held_lo_m2": p.held_lo, "held_hi_m2": p.held_hi,
            "owner_manual_q07_m2": (r6(p.area_m2) if p.band_kind in ("storey", "parapet", "over_lower_roof")
                                    else None),
            "owner_manual_note": ("Q-07 B band" if p.band_kind in ("storey", "parapet", "over_lower_roof") else
                                  "plinth: outside the Q-07 B bands (UP-FACADE-001 RFI)" if p.band_kind == "plinth"
                                  else "slab edge: depth not printed"),
            "evidence_status": status, "ledger_state": st, "finish_line_id": ln.line_id if ln else "",
            "geometry_line_id": geo_ln.line_id if geo_ln else "", "reason": why})
    # openings onto faces: the storey band of the side holds the hole (all heads <= the band height)
    face_by_side = {}
    for fr in face_rows:
        if fr["band"] == "storey":
            face_by_side.setdefault((fr["floor"], fr["side"]), []).append(fr)
    op_rows = []
    seen = set()
    for o in ops:
        if o["opening"] in seen and not o["opening"].startswith("none"):
            raise R.LedgerError(f"{o['opening']} on two faces")
        seen.add(o["opening"])
        bands = face_by_side.get((o["floor"], o["side"]), [])
        if not bands:
            raise R.LedgerError(f"{o['opening']}: no storey band on {o['floor']} {o['side']}")
        lines_ = {(b["finish_line_id"], b["geometry_line_id"]) for b in bands}
        if len(lines_) != 1:
            raise R.LedgerError(f"{o['opening']}: storey bands of {o['side']} on two lines")
        band_area = sum(b["geometric_m2"] or 0.0 for b in bands)
        h_band = max(b["top_m"] for b in bands) - min(b["bottom_m"] for b in bands)
        side_len = sum(b["length_m"] for b in bands)
        if o["status"] == "NOT_AN_OPENING":
            ded = {"fixed": 0.0, "lo": 0.0, "hi": 0.0, "status": "NOT_AN_OPENING"}
        else:
            cap = o["cap_m2"] if o["cap_m2"] is not None else (
                None if o["width_m"] is None else min(o["width_m"], side_len) * h_band)
            op = R.Opening(o["opening"], o["floor"], o["side"], o["width_m"], o["sill_m"], o["head_m"], o["hole_m2"],
                           o["status"] if o["status"] != DOOR_FALLBACK else DOOR_FALLBACK, cap_m2=cap,
                           window_measure_m2=o["window_measure_m2"])
            ded = R.deduction(op, band_area)
        fl_, gl_ = next(iter(lines_))
        op_rows.append(dict(o, band_m2=r6(band_area), deduct_fixed_m2=r6(ded["fixed"]), deduct_lo_m2=r6(ded["lo"]),
                            deduct_hi_m2=r6(ded["hi"]), deduct_status=ded["status"], finish_line_id=fl_,
                            geometry_line_id=gl_))
    items = item_rows()
    for it in items:
        book.add("ITEM|" + it["item"], it["ledger_state"], None, unit=it["unit"])
    return d, face_rows, op_rows, items, notface


def item_rows():
    out = []
    for r in read(RES / "agents_t162" / "PARAPETS_T162.csv"):
        ch = r["CHAIN"]
        if ch not in ("ANNEX", "GF", "1F", "2F"):     # the file's second table (his rows) is a comparison, not an item
            continue
        inner = r["INNER_FACE_M2"]
        lo, hi = (inner.split("..") + [inner])[:2] if ".." in inner else (inner, inner)
        st, why = R.item_owner("PARAPET_INNER_FACE")
        out.append({"item": f"parapet inner face {ch}", "kind": "PARAPET_INNER_FACE", "unit": "m2",
                    "qty_lo": r6(f_(lo)), "qty_hi": r6(f_(hi)),
                    "evidence_status": "DRAWING-CONFIRMED" if lo == hi else "HELD",
                    "ledger_state": st, "reason": why + "; plaster scope UNKNOWN (no specification); upper bound "
                    "from the slab top (roof build-up not printed)", "source": "T-162 r2 PARAPETS / T-172"})
        st, why = R.item_owner("PARAPET_TOP")
        out.append({"item": f"parapet top {ch}", "kind": "PARAPET_TOP", "unit": "m2", "qty_lo": r6(f_(r["TOP_M2"])),
                    "qty_hi": r6(f_(r["TOP_M2"])), "evidence_status": "DRAWING-CONFIRMED", "ledger_state": st,
                    "reason": why + "; cap profile P1 / P2 / P3 not keyed (ST p.14 'as per arc.')",
                    "source": "T-162 r2 PARAPETS / T-172"})
    for r in read(RES / "agents_t162" / "CORNERS_R2_T162.csv"):
        st, why = R.item_owner("CORNER_ML")
        q = f_(r["PHYSICAL_ML"])
        out.append({"item": "corners: " + r["COMPONENT"], "kind": "CORNER_ML", "unit": "m.l", "qty_lo": r6(q),
                    "qty_hi": r6(q), "evidence_status": r["STATUS"] if q is not None else "HELD",
                    "ledger_state": st, "reason": why + ("; " + r["HELD_OR_UNKNOWN"] if r["HELD_OR_UNKNOWN"] not in
                                                         ("", "-") else ""),
                    "source": "T-162 r2 CORNERS_R2"})
    for kind, item, why2 in (("BOUNDARY_WALL", "boundary / street fence faces", "freelancer 107.240 m2 in his Sigma; the candidate carries the boundary-wall foundation only (STR.CONC.BOUNDARY_WALL)"),
                             ("DOME", "domes inside and outside", "freelancer 181.806 m2: EXCLUDED (owner item 3)"),
                             ("DRIP_EDGE", "drip edge band", "freelancer 0.28 x 181.7 = 50.876 m2; owner not answered"),
                             ("FRAME_MOULDING", "facade frames (SE stair tower, NW pool court)",
                              "freelancer 28.868 m2 (SE 24.930 + NW 3.938); profile not detailed (designer)")):
        st, why = R.item_owner(kind)
        out.append({"item": item, "kind": kind, "unit": "m2", "qty_lo": None, "qty_hi": None,
                    "evidence_status": "HELD" if kind in ("BOUNDARY_WALL", "FRAME_MOULDING") else
                    ("UNKNOWN" if kind == "DRIP_EDGE" else "NOT_APPLICABLE (owner)"),
                    "ledger_state": st, "reason": why + "; " + why2, "source": "owner notes Sigma 2026-10-21; T-162"})
    out.append({"item": "SE projecting band 0.20 m outside the 1F SE-1 / GF SE faces", "kind": "FRAME_MOULDING",
                "unit": "m2", "qty_lo": None, "qty_hi": None, "evidence_status": "UNKNOWN", "ledger_state": "NO_LINE",
                "reason": "Checker T-159 observation (layer D 1F / layer 2 GF line 0.200 m outside the face): its "
                          "return faces UNKNOWN, not 0", "source": "T-159 verdict 2026-10-22 04:05"})
    return out


# ------------------------------------------------------------------------------------------------- summaries
def sums(face_rows, op_rows):
    tot = {}
    for fr in face_rows:
        k = (fr["ledger_state"], fr["finish_line_id"] or fr["reason"].split(":")[0][:60])
        t = tot.setdefault(k, {"m2": 0.0, "held_lo": 0.0, "held_hi": 0.0, "rows": 0, "slab_edge_m": 0.0})
        t["rows"] += 1
        if fr["geometric_m2"] is not None:
            t["m2"] += fr["geometric_m2"]
        elif fr["held_lo_m2"] is not None:
            t["held_lo"] += fr["held_lo_m2"]
            t["held_hi"] += fr["held_hi_m2"]
        else:
            t["slab_edge_m"] += fr["length_m"]
    return tot


def line_summary(d, face_rows, op_rows):
    rows = []
    lines = {ln["line_id"]: ln for ln in d["facade_lines"]}
    fins = sorted({fr["finish_line_id"] for fr in face_rows if fr["finish_line_id"]})
    for lid in fins:
        ln = lines[lid]
        fr = [x for x in face_rows if x["finish_line_id"] == lid]
        orr = [x for x in op_rows if x["finish_line_id"] == lid]
        gross = sum(x["geometric_m2"] for x in fr)
        fixed = sum(x["deduct_fixed_m2"] or 0.0 for x in orr if x["deduct_status"] not in ("HELD",))
        held_hi = sum(x["deduct_hi_m2"] for x in orr if x["deduct_status"] == "HELD")
        assumed = sum(x["deduct_fixed_m2"] for x in orr if x["deduct_status"] == DOOR_FALLBACK)
        rows.append({"finish_line_id": lid, "item_code": ln["item_code"], "floor": ln["floor"],
                     "candidate_state": ln["evidence_state"], "candidate_quantity": ln["measured_net"],
                     "geometry_line_id": fr[0]["geometry_line_id"], "faces": len({x["side"] for x in fr}),
                     "bands": len(fr), "gross_m2": r6(gross), "openings": len([x for x in orr
                                                                                  if x["deduct_status"] != "NOT_AN_OPENING"]),
                     "deduct_fixed_m2": r6(fixed), "of_which_assumed_m2": r6(assumed),
                     "deduct_held_cap_m2": r6(held_hi), "net_hi_m2": r6(gross - fixed),
                     "net_lo_m2": r6(gross - fixed - held_hi),
                     "status": "HELD (bounded: openings without an established hole)" if held_hi > 0 else
                     ("ASSUMED — OWNER-APPROVED part (doors 2.20)" if assumed else "DRAWING-CONFIRMED")})
    return rows


def csv_text(rows, cols):
    b = io.StringIO()
    w = csv.DictWriter(b, fieldnames=cols, lineterminator="\n", extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow({k: ("" if r.get(k) is None else (f"{r[k]:.6f}" if isinstance(r[k], float) else r[k]))
                    for k in cols})
    return b.getvalue()


FACE_COLS = ["floor", "side", "facing", "portion", "band", "length_m", "bottom_m", "top_m", "geometric_m2",
             "held_lo_m2", "held_hi_m2", "owner_manual_q07_m2", "owner_manual_note", "evidence_status",
             "ledger_state", "finish_line_id", "geometry_line_id", "reason"]
OP_COLS = ["floor", "side", "opening", "engine_ref", "width_m", "sill_m", "head_m", "hole_m2", "status", "cap_m2",
           "window_measure_m2", "band_m2", "deduct_fixed_m2", "deduct_lo_m2", "deduct_hi_m2", "deduct_status",
           "finish_line_id", "geometry_line_id", "source", "note"]
ITEM_COLS = ["item", "kind", "unit", "qty_lo", "qty_hi", "evidence_status", "ledger_state", "reason", "source"]
LINE_COLS = ["finish_line_id", "item_code", "floor", "candidate_state", "candidate_quantity", "geometry_line_id",
             "faces", "bands", "gross_m2", "openings", "deduct_fixed_m2", "of_which_assumed_m2", "deduct_held_cap_m2",
             "net_lo_m2", "net_hi_m2", "status"]


def outputs():
    d, face_rows, op_rows, items, notface = build()
    lines = line_summary(d, face_rows, op_rows)
    t = sums(face_rows, op_rows)
    by_state = {}
    for (st, _), v in t.items():
        s = by_state.setdefault(st, {"m2": 0.0, "held_lo": 0.0, "held_hi": 0.0, "rows": 0, "slab_edge_m": 0.0})
        for k2 in s:
            s[k2] += v[k2]
    measured = sum(fr["geometric_m2"] for fr in face_rows if fr["geometric_m2"] is not None)
    held_lo = sum(fr["held_lo_m2"] for fr in face_rows if fr["held_lo_m2"] is not None)
    held_hi = sum(fr["held_hi_m2"] for fr in face_rows if fr["held_hi_m2"] is not None)
    t159 = json.loads((RES / "agents_t159" / "summary.json").read_text(encoding="utf-8"))
    csv_sum = sum(f_(r["AREA_M2"]) for r in read(RES / "agents_t159" / "FACADE_SIDES_T159.csv") if r["AREA_M2"])
    # formula illustration: run x one storey height per floor (the line's own formula), against the in-line faces
    runs = {ln["floor"]: ln for ln in d["facade_lines"] if ln["item_code"] == "ARCH.FACADE_RUN"
            and ln["element"] == "facade"}
    formula = {}
    for fl, H in (("GF", 4.50), ("1F", 4.20), ("2F", 4.70)):
        run = runs[fl]["measured_net"]
        inl = sum(fr["geometric_m2"] for fr in face_rows if fr["floor"] == fl and fr["ledger_state"] == "IN_LINE")
        formula[fl] = {"run_m": run, "printed_storey_h_m": H, "run_x_h_m2": r6(run * H) if run is not None else None,
                       "in_line_faces_m2": r6(inl),
                       "difference_m2": r6(inl - run * H) if run is not None else None}
    summ = {
        "candidate": {k: d[k] for k in ("source", "lines_json_sha256_8", "lines_csv_sha256_8", "lines_total")},
        "candidate_facade_lines": [{k: ln[k] for k in ("line_id", "item_code", "floor", "element",
                                                        "evidence_state", "measured_net")} for ln in
                                   d["facade_lines"]],
        "census_other_lines": d["census_by_code_of_lines_naming_facade_ext_parapet_soffit_boundary"],
        "faces": {"bands": len(face_rows), "measured_m2": r6(measured), "held_m2": [r6(held_lo), r6(held_hi)],
                  "t159_measured_m2": t159["measured_m2"], "t159_held_m2": t159["held_m2"],
                  "t159_csv_area_sum_m2": r6(csv_sum),
                  "residual_measured_vs_t159_csv_m2": r6(measured - csv_sum),
                  "slab_edge_over_open_air_m": r6(sum(fr["length_m"] for fr in face_rows if fr["band"] == "slab_edge")),
                  "not_a_face_sides": [f"{x['floor']} {x['side']}" for x in notface]},
        "by_ledger_state": {k: {k2: r6(v2) if isinstance(v2, float) else v2 for k2, v2 in v.items()}
                            for k, v in sorted(by_state.items())},
        "by_state_and_line": [{"state": k[0], "line_or_cause": k[1], **{k2: r6(v2) if isinstance(v2, float) else v2
                                                                        for k2, v2 in v.items()}}
                              for k, v in sorted(t.items())],
        "owner_manual_q07_m2": r6(sum(fr["owner_manual_q07_m2"] or 0.0 for fr in face_rows)),
        "openings": {"rows": len(op_rows),
                     "fixed_drawing_m2": r6(sum(o["deduct_fixed_m2"] or 0.0 for o in op_rows
                                                if o["deduct_status"] == "DRAWING-CONFIRMED")),
                     "assumed_doors_m2": r6(sum(o["deduct_fixed_m2"] for o in op_rows
                                                if o["deduct_status"] == DOOR_FALLBACK)),
                     "held_cap_m2": r6(sum(o["deduct_hi_m2"] for o in op_rows if o["deduct_status"] == "HELD")),
                     "held_ids": [o["opening"] for o in op_rows if o["deduct_status"] == "HELD"]},
        "lines": lines, "formula_run_x_h": formula,
        "items": {"rows": len(items)},
    }
    files = {"FACE_LINE_LEDGER_T305.csv": csv_text(face_rows, FACE_COLS),
             "OPENING_HOLES_T305.csv": csv_text(op_rows, OP_COLS),
             "ITEMS_T305.csv": csv_text(items, ITEM_COLS),
             "LINE_SUMMARY_T305.csv": csv_text(lines, LINE_COLS),
             "summary.json": json.dumps(summ, indent=1, ensure_ascii=False) + "\n"}
    return files


def main(argv):
    if argv[:1] == ["--extract"]:
        extract(argv[1])
    elif argv[:1] == ["--geometry"]:
        geometry(argv[1], argv[2])
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
