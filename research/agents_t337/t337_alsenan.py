"""T-337 builder: every exterior face, opening and facade component of the development villa bound to ONE owner line
of the ARCH_TAKEOFF_V3.0.22 candidate (an existing FIN.EXT.FINISH line id, another candidate line, or a NEW row that
T-314 must add), from the Checker-merged ledgers T-305 (faces, openings), T-311 (parapet runs, plinth) and T-324
(parapet components, corrections). Research only: no engine module, rule, knowledge file or candidate line changes.

    python3 -I research/agents_t337/t337_alsenan.py --extract <own V3.0.22 run>/v3022   # CANDIDATE_V3022_T337.json
    python3 -I research/agents_t337/t337_alsenan.py --write                            # every other output
    python3 -I research/agents_t337/t337_alsenan.py --check                            # rebuild byte for byte

No coordinates, client names or drawing content are written: lengths, levels, areas, line ids and engine ids only.
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
sys.path.insert(0, str(HERE))

import facade_binding as FB  # noqa: E402

T305 = ROOT / "research" / "agents_t305"
T311 = ROOT / "research" / "agents_t311"
T324 = ROOT / "research" / "agents_t324"
T162 = ROOT / "research" / "agents_t162"
T342 = ROOT / "research" / "agents_t342"
RAW = ROOT / "tests" / "alsenan" / "registers_b1" / "FREELANCER_RAW_ROWS.json"
CAND = HERE / "CANDIDATE_V3022_T337.json"

FACADE_CODES = ("ARCH.FACADE_RUN", "ARCH.FACADE", "FIN.EXT.FINISH")
# Lines of other families this ledger cites as OTHER_LINE owners (verified present in V3.0.22 by --extract)
CITED_OTHER = {
    "L-23072352a28aeca7b051": "pool-court soffit (FIN.CEILING, owner item 4 accepts 12.834)",
    "L-d4c73babd2a275c28929": "annex roof membrane upturn (m.l)",
    "L-994b88140f2ea50f1b31": "GF terrace membrane upturn (m.l)",
    "L-5ce5ba49792e8f9d1f6f": "1F roof membrane upturn (m.l)",
    "L-aac1f35e08f85b643692": "2F roof membrane upturn (m.l)",
    "L-4165954ce4871eda30cc": "GF block t=0.20 (plinth wall course substrate)",
}
STOREY_LINE = {"GF": "L-b05f70c92405dbcfbe62", "1F": "L-8bb83e16cc7b104ab88b", "2F": "L-d52c4f763b19aedf8b8b"}
GEOM_LINE = {"GF": "L-cc7dc0a51f3319a99482", "1F": "L-43527ae4e8ec75c56636", "2F": "L-348c4d8d32f3f6d35fe5",
             "PLINTH": "L-c0e9a4c62171de1f369b"}
ROOF_OF_CHAIN = {"ANNEX": "ANNEX", "GF": "GF", "1F": "1F", "2F": "2F"}


def NEW(kind, where):
    return f"NEW FIN.EXT.{kind} {where}"


def f_(s):
    s = (s or "").strip()
    return None if s == "" else float(s)


def r6(x):
    return None if x is None else round(x, 6) + 0.0


def fmt(x):
    return "" if x is None else f"{x:.6f}"


def lead(s):
    """Leading printed level of a cell such as '+11.00 printed NE / SW; ...'."""
    m = re.match(r"\s*([+-]?\d+(?:\.\d+)?)", s or "")
    if not m:
        raise FB.BindingError(f"no level in {s!r}")
    return float(m.group(1))


def read(p):
    with open(p, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


# --------------------------------------------------------------------------------------------- extract (needs the run)
def extract(run_dir):
    run_dir = Path(run_dir)
    raw = (run_dir / "V3_0_22_BOQ_LINES.json").read_bytes()
    d = json.loads(raw.decode("utf-8"))
    lines = d if isinstance(d, list) else d["lines"]
    keep, cited = [], {}
    for ln in lines:
        code = ln.get("item_code") or ""
        loc = ln.get("location") or {}
        row = {"line_id": ln["line_id"], "item_code": code, "floor": loc.get("floor"),
               "element": str(loc.get("element_id", "")).split(":", 1)[-1], "unit": ln.get("unit"),
               "evidence_state": ln.get("evidence_state"), "measured_net": ln.get("measured_net"),
               "rfi_head": str((ln.get("rfi") or {}).get("question") or "")[:120]}
        if code in FACADE_CODES:
            keep.append(row)
        if ln["line_id"] in CITED_OTHER:
            cited[ln["line_id"]] = row
    csvp = run_dir / "V3_0_22_BOQ_LINES.csv"
    out = {"source": "own ARCH_TAKEOFF_V3.0.22 run (research/agents_t167/v304_run.py then research/agents_t331/"
                     "v3022_run.py) on Drive 'Alsenan chalet project' P7757_DXF_COMPRESSED.zip -> P7757.dxf "
                     "(ab54dd55) and 'ST7757 dxf.dxf' (9f9d1179)",
           "lines_json_sha256_8": hashlib.sha256(raw).hexdigest()[:8],
           "lines_csv_sha256_8": hashlib.sha256(csvp.read_bytes()).hexdigest()[:8] if csvp.exists() else None,
           "lines_total": len(lines),
           "facade_lines": sorted(keep, key=lambda x: (x["floor"] or "", x["item_code"], x["element"], x["line_id"])),
           "cited_other_lines": [cited.get(k, {"line_id": k, "missing": True}) for k in sorted(CITED_OTHER)]}
    CAND.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {CAND.name}: {len(keep)} facade lines, {len(cited)} / {len(CITED_OTHER)} cited lines of {len(lines)}")


def candidate():
    d = json.loads(CAND.read_text(encoding="utf-8"))
    by = {x["line_id"]: x for x in d["facade_lines"]}
    for lid in list(STOREY_LINE.values()) + list(GEOM_LINE.values()):
        if lid not in by:
            raise FB.BindingError(f"{lid} is not a V3.0.22 facade line")
    for x in d["cited_other_lines"]:
        if x.get("missing"):
            raise FB.BindingError(f"{x['line_id']} is not in V3.0.22")
    return d, by


# ------------------------------------------------------------------------------------------------ levels and parts
def parts_and_roofs():
    """Parts and roof levels from the merged T-311 run ledger (chain -> roof level / parapet top) and the T-305 bands."""
    runs = read(T311 / "PARAPET_RUN_LEDGER_T311.csv")
    roof, top, annex_sides = {}, {}, set()
    for r in runs:
        c = r["chain"]
        roof.setdefault(c, float(r["roof_level"]))
        top.setdefault(c, lead(r["parapet_top"]))
        if abs(roof[c] - float(r["roof_level"])) > FB.EPS:
            raise FB.BindingError(f"chain {c}: two roof levels")
        if c == "ANNEX":
            annex_sides.add(r["side"])
    house = FB.Part("HOUSE", (("GF", 1.00), ("1F", 5.50), ("2F", 9.70)), roof["2F"])
    annex = FB.Part("ANNEX", (("GF", 0.30),), roof["ANNEX"])
    passage = FB.Part("PASSAGE", (("GF", 0.30),), 5.50)  # covered: the 1F plate at +5.50 (T-305 bands)
    return {"HOUSE": house, "ANNEX": annex, "PASSAGE": passage}, roof, top, annex_sides


def part_of(row, annex_sides):
    if row["floor"] == "GF" and row["portion"] == "EDGE" and row["side"] in annex_sides:
        return "ANNEX"
    if row["floor"] == "GF" and row["band"] == "storey" and abs(float(row["bottom_m"]) - 0.30) < FB.EPS:
        return "PASSAGE"  # P-1 and the 0.20 m covered strip of SW-3 stand on the annex F.F.L. under the 1F plate
    return "HOUSE"


# ------------------------------------------------------------------------------------------------------ face rows
C3_CHORD, C3_ARC = 3.2496, 3.5283     # T-324 C3: roof plan 12A7 chord vs the 1F floor outline bay arc (NW-2)
C5_OUTER = 0.600                       # T-324 C5: B34 extension, outer face on the boundary line AC7 (owner HELD)


def face_rows():
    parts, roof, top, annex_sides = parts_and_roofs()
    out = []
    for r in read(T305 / "FACE_LINE_LEDGER_T305.csv"):
        fl, band = r["floor"], r["band"]
        key0 = f"{fl}/{r['side']}/{r['portion']}"
        L = float(r["length_m"])
        bot, tp = f_(r["bottom_m"]), f_(r["top_m"])
        g, hlo, hhi = f_(r["geometric_m2"]), f_(r["held_lo_m2"]), f_(r["held_hi_m2"])
        base = {"floor": fl, "side": r["side"], "portion": r["portion"], "length_m": L, "t305_band": band,
                "t305_state": r["ledger_state"], "t305_line": r["finish_line_id"] or "NO_LINE",
                "status": r["evidence_status"], "geometry_line": r["geometry_line_id"]}
        pname = part_of(r, annex_sides)
        part = parts[pname]
        if band == "slab_edge":
            out.append({**base, "key": key0 + "/slab_edge", "part": pname, "kind": "slab_edge", "bottom": None,
                        "top": bot, "lo": None, "hi": None, "owner_q07": None, "owner_floor": "1F",
                        "line": NEW("FINISH", "SLAB-EDGE 1F"), "line_state": "NEW", "status": "HELD",
                        "why": "plate edge over open air: depth not printed (Q-68 C); its own line, HELD blank"})
            continue
        if band == "plinth":
            kind, owner = FB.band_kind(bot if bot is not None else part.lowest_ffl() - 1.0, tp, part)
            assert kind == "plinth"
            out.append({**base, "key": key0 + "/plinth", "part": pname, "kind": "plinth", "bottom": bot, "top": tp,
                        "lo": g if g is not None else hlo, "hi": g if g is not None else hhi, "owner_q07": None,
                        "owner_floor": None, "line": NEW("FINISH", "PLINTH GF"), "line_state": "NEW",
                        "why": "outer ground -> lowest F.F.L.; outside the owner's Q-07 B bands (RFI); finish not "
                               "printed (T-317: plaster / Sigma or cladding); area bound here"})
            continue
        # storey / parapet / over_lower_roof bands
        chain = {"GF": "GF", "1F": "1F", "2F": "2F"}[fl] if pname == "HOUSE" else ("ANNEX" if pname == "ANNEX" else None)
        rf = roof.get(chain) if chain else None
        segs = FB.split_at(bot, tp, rf) if (tp is not None and rf is not None) else [(bot, tp)]
        for (b, t) in segs:
            tt = t if t is not None else b
            kind, owner = FB.band_kind(b, tt, part, roof=rf)
            if len(segs) == 1:
                lo = g if g is not None else hlo
                hi = g if g is not None else hhi
            else:  # split the T-305 face in proportion to the band heights: the face total stays exactly T-305's
                lo = hi = r6(g * (t - b) / (tp - bot))
            st = base["status"]
            sub = band if len(segs) == 1 else ("storey" if kind == "storey" else "parapet")
            row = {**base, "key": f"{key0}/{sub}", "part": pname, "kind": kind, "bottom": b, "top": t, "lo": lo,
                   "hi": hi, "owner_q07": lo if st != "HELD" else None, "owner_floor": owner, "status": st}
            if kind == "storey":
                row.update(line=STOREY_LINE[owner], line_state="EXISTING",
                           why=f"storey band of {owner} by levels ({pname} part)")
            else:
                row.update(line=NEW("FINISH", f"PARAPET-OUTER {chain} +{rf:.2f}"), line_state="NEW",
                           why=f"parapet outer face above the {chain} roof +{rf:.2f} to its top +{top[chain]:.2f}: "
                               "never in a storey line")
            if len(segs) == 2:
                row["why"] += f" (T-305 band {bot:.2f}->{tp:.2f} split at the roof +{rf:.2f})"
            if band == "over_lower_roof":
                row["why"] = ("face on the annex roof +4.30 below the 1F F.F.L. +5.50: inside the GF house storey "
                              "levels +1.00 -> +5.50, so the GF storey line (T-305: NO_LINE)")
            if fl == "1F" and r["side"] == "NW-2" and kind == "parapet":
                # T-324 C3: the roof plan draws the parapet straight (chord) over the bay arc of the floor outline
                row.update(lo=r6(g * C3_CHORD / C3_ARC), hi=g, owner_q07=None, status="HELD",
                           why=row["why"] + "; T-324 C3: roof plan draws the parapet on the 3.2496 m chord, the 1F "
                               "outline on the 3.5283 m arc: outer edge = frame profile, HELD")
            out.append(row)
    # T-324 C5: the B34 extension's outer face stands on the boundary line AC7 (one face, two readings, Q-65 C)
    out.append({"floor": "GF", "side": "NE-6x", "portion": "EDGE", "length_m": 1.2, "t305_band": "-",
                "t305_state": "NOT_IN_T305", "t305_line": "-", "status": "HELD", "geometry_line": "",
                "key": "GF/NE-6x/EDGE/parapet", "part": "ANNEX", "kind": "parapet", "bottom": roof["ANNEX"],
                "top": top["ANNEX"], "lo": 0.0, "hi": C5_OUTER, "owner_q07": None, "owner_floor": None,
                "line": NEW("FINISH", f"PARAPET-OUTER ANNEX +{roof['ANNEX']:.2f}"), "line_state": "NEW",
                "why": "T-324 C5: B34 runs 1.400 m past the house wall line; its outer face stands on the boundary line "
                       "AC7 (boundary wall or annex face: Q-65 C, boundary package): 0 .. 0.600 HELD"})
    return out


def opening_rows(faces):
    by_face = {}
    for f in faces:
        if f["kind"] == "storey":
            by_face.setdefault((f["floor"], f["side"]), []).append(f)
    ffl = {"HOUSE": {"GF": 1.00, "1F": 5.50, "2F": 9.70}, "ANNEX": {"GF": 0.30}, "PASSAGE": {"GF": 0.30}}
    out = []
    for r in read(T305 / "OPENING_HOLES_T305.csv"):
        name = r["opening"]
        if r["deduct_status"] == "NOT_AN_OPENING":
            out.append({"floor": r["floor"], "side": r["side"], "opening": name, "face_key": "-", "line": "-",
                        "hole_m2": None, "fixed": None, "lo": None, "hi": None, "status": "NOT_AN_OPENING",
                        "sill_abs": None, "head_abs": None, "check": "OP-001 0.200 m drafting gap (T-109): wall face",
                        "t305_line": r["finish_line_id"]})
            continue
        cands = sorted(by_face[(r["floor"], r["side"])], key=lambda f: -(f["hi"] or 0.0))
        face = cands[0]
        z = ffl[face["part"]][face["floor"]]
        sill, head = f_(r["sill_m"]), f_(r["head_m"])
        sa = None if sill is None else r6(z + sill)
        ha = None if head is None else r6(z + head)
        if sa is not None and ha is not None:
            FB.hole_on_band(sa, ha, face["bottom"], face["top"])
            chk = f"hole {sa:.2f} -> {ha:.2f} inside the band {face['bottom']:.2f} -> {face['top']:.2f}"
        else:
            chk = (f"datum not printed (area established): band {face['bottom']:.2f} -> {face['top']:.2f} "
                   f"({face['top'] - face['bottom']:.2f} m) holds the hole; a window cannot rise into the roof "
                   "slab / parapet above the band top")
        st = r["deduct_status"]
        fixed = f_(r["deduct_fixed_m2"])
        lo, hi = f_(r["deduct_lo_m2"]), f_(r["deduct_hi_m2"])
        out.append({"floor": r["floor"], "side": r["side"], "opening": name, "face_key": face["key"],
                    "line": face["line"], "hole_m2": f_(r["hole_m2"]), "fixed": fixed if st != "HELD" else None,
                    "lo": lo if st == "HELD" else None, "hi": hi if st == "HELD" else None, "status": st,
                    "sill_abs": sa, "head_abs": ha, "check": chk, "t305_line": r["finish_line_id"]})
    return out


# ------------------------------------------------------------------------------------------- non-face components
def item_rows():
    comp = read(T324 / "COMPONENT_SUMMARY_T324.csv")
    roof = {r["chain"]: float(r["roof_level"]) for r in read(T311 / "PARAPET_RUN_LEDGER_T311.csv")}
    out = []

    def add(item, line, unit, lo, hi, status, state, source, why):
        out.append({"item": item, "line": line, "unit": unit, "lo": lo, "hi": hi, "status": status,
                    "line_state": state, "source": source, "why": why})

    names = {"INNER_FACE_ABOVE_UPTURN": ("PARAPET-INNER", "m2", "inner face above the membrane upturn top (plaster "
                                         "scope: owner trade PLASTER_PARAPET_INNER; split height HELD, D-39)"),
             "INNER_FACE_UPTURN_ZONE": (None, "m2", "exposed upturn zone: protection over the membrane, WATERPROOFING "
                                        "edge detail (never plaster, never 0 as a split)"),
             "TOP_SURFACE": ("PARAPET-TOP", "m2", "plain top (section A-A); a printed coping would replace it")}
    for c in comp:
        k = c["component"]
        if k in names:
            nm, unit, why = names[k]
            ch = c["chain"]
            line = (NEW(nm, f"{ch} +{roof[ch]:.2f}") if nm else f"NEW FIN.WP.UPTURN-ZONE-FACE {ch} +{roof[ch]:.2f}")
            add(f"parapet {k.lower()} {ch}", line, unit, float(c["qty_lo"]), float(c["qty_hi"]), c["status"], "NEW",
                "T-324 COMPONENT_SUMMARY", why)
    corners = NEW("CORNERS", "(m.l, all floors)")
    for c in comp:
        if c["component"] in ("OUTER_TOP_ARRIS", "INNER_TOP_ARRIS"):
            add(f"{c['component'].lower()} {c['chain']}", corners, "m.l", float(c["qty_lo"]), float(c["qty_hi"]),
                c["status"], "NEW", "T-324 COMPONENT_SUMMARY", "parapet top arris: its own m.l, never m2")
    for item, q, src in (("vertical convex arrises GF", 66.900, "T-162 r2 / T-172"),
                         ("vertical convex arrises 1F", 39.000, "T-162 r2 / T-172"),
                         ("vertical convex arrises 2F", 18.800, "T-162 r2 / T-172"),
                         ("GF wall ends at the two passage mouths", 43.100, "T-162 r2 / T-172"),
                         ("opening arrises (head + 2 jambs + sill)", 137.110, "T-162 r2")):
        add(item, corners, "m.l", q, q, "DRAWING-CONFIRMED", "NEW", src, "external arris, full physical length")
    add("door arrises at the 2.20 m door height", corners, "m.l", 32.200, 32.200, "ASSUMED — OWNER-APPROVED", "NEW",
        "T-162 r2; Q-55 C", "doors without a printed height: 2.20 m (owner Q-55 C)")
    for item, lo, hi, why in (
            ("GF pool-court corners below the court level", 2.100, 2.550, "3 x 0.70 .. 0.85: pool-court plinth HELD"),
            ("1F vertical arrises: parapet end parts", 0.0, 11.900, "parapet end heights NE-1 / SW-1 / SW-2 HELD"),
            ("GF passage-mouth parapet stop-end", 0.0, 1.200, "T-324 STOP_END = T-162 r2 mouth held part (one item)"),
            ("arch frames SE stair tower / NW pool court", 98.002, 195.180, "frame profile not detailed (designer)")):
        add(item, corners, "m.l", lo, hi, "HELD", "NEW", "T-162 r2 / T-324", why)
    add("1F slab edge over open air (lower arris)", corners, "m.l", None, None, "HELD", "NEW", "T-162 r2",
        "13.079 m run; finish / depth not printed (Q-68 C): blank, never 0")
    for item, line, unit, why in (
            ("coping", NEW("COPING", "(m.l)"), "m.l", "none printed; ST p.14 P1 cap 'as per arc.'"),
            ("drip / throat", NEW("DRIP", "(m.l)"), "m.l", "nothing drawn; owner not answered"),
            ("corner beads", NEW("CORNERS", "(m.l, all floors)") + " accessory", "m.l",
             "accessory ON the arrises (same edges, never a second length); no specification"),
            ("SE projecting band 0.20 m return faces", NEW("FRAME", "(m2)"), "m2", "Checker T-159 observation"),
            ("parapet divider faces / top (annex | GF terrace)", NEW("FINISH", "DIVIDER (m2)"), "m2",
             "no top level printed (T-324)")):
        add(item, line, unit, None, None, "UNKNOWN", "NEW", "T-305 / T-324", why)
    add("facade frame mouldings (SE stair tower, NW pool court)", NEW("FRAME", "(m2)"), "m2", None, None, "HELD",
        "NEW", "T-305 / T-172", "profile not detailed: blank, never 0")
    for item, line, state, unit, q, status, why in (
            ("pool-court soffit", "L-23072352a28aeca7b051", "OTHER_LINE", "m2", 12.834, "VERIFIED (Checker 12.8343)",
             "ceiling side, not a wall face (owner item 4 accepts 12.834)"),
            ("membrane upturn base (inner base junction), annex", "L-d4c73babd2a275c28929", "OTHER_LINE", "m.l", None,
             "IN_LINE", "the roof WP line's m.l contains it (T-311 / T-324)"),
            ("membrane upturn base, GF terrace", "L-994b88140f2ea50f1b31", "OTHER_LINE", "m.l", None, "IN_LINE",
             "as above"),
            ("membrane upturn base, 1F roof", "L-5ce5ba49792e8f9d1f6f", "OTHER_LINE", "m.l", None, "IN_LINE",
             "as above"),
            ("membrane upturn base, 2F roof", "L-aac1f35e08f85b643692", "OTHER_LINE", "m.l", None, "HELD",
             "line BLOCKED_RFI: 2F run HELD"),
            ("plinth wall course substrate", "L-4165954ce4871eda30cc", "OTHER_LINE", "m2", 5.059, "DRAWING-CONFIRMED",
             "block substrate of the plinth face (T-311): the wall's own line, not a second finish"),
            ("spatter dash under the exterior plaster (B4-05)", "T-317 B4-05 item (no candidate line yet)",
             "OTHER_ITEM", "m2", None, "per T-317",
             "a separate item on the same faces (URBAN-FINISH-EXTRAS-SEPARATE-ITEMS@v1), never inside these m2 lines"),
            ("boundary / street fence faces", "site boundary element", "OTHER_TRADE", "m2", None, "HELD",
             "not a house face (owner Q-65 C)"),
            ("domes inside and outside", "-", "NOT_APPLICABLE", "m2", None, "NOT_APPLICABLE",
             "owner item 3: no domes")):
        out.append({"item": item, "line": line, "unit": unit, "lo": q, "hi": q, "status": status,
                    "line_state": state, "source": "cited", "why": why})
    return out


# ------------------------------------------------------------------------------------------------------ the book
def book_all(faces, openings, items):
    bk = FB.Book()
    for f in faces:
        bk.line(f["line"], "m2")
        bk.add_face(f["key"], f["line"], f["lo"], f["hi"], f["status"])
    for o in openings:
        if o["status"] == "NOT_AN_OPENING":
            continue
        bk.add_opening(f"{o['floor']}/{o['side']}/{o['opening']}", o["face_key"], o["fixed"] or 0.0, o["lo"],
                       o["hi"], o["status"])
    for i in items:
        if i["line_state"] == "NEW":
            bk.add_item(i["item"], i["line"], i["unit"], i["lo"], i["hi"], i["status"])
    return bk


def fill_rows(faces, openings, bk):
    lines = []
    for f in faces:
        if f["line"] not in [x[0] for x in lines]:
            lines.append((f["line"], f["line_state"]))
    out = []
    for ln, state in lines:
        fr = [f for f in faces if f["line"] == ln]
        orow = [o for o in openings if o["line"] == ln]
        g_lo, g_hi, d_fix, d_lo, d_hi, n_lo, n_hi, n, m = bk.totals(ln)
        assumed = sum(o["fixed"] or 0.0 for o in orow if o["status"].startswith("ASSUMED"))
        sts = {f["status"] for f in fr} | {o["status"] for o in orow}
        blanks = sum(1 for f in fr if f["lo"] is None)
        if blanks == len(fr):
            status = "HELD (blank: no area)"
        elif "HELD" in sts:
            status = "HELD (bounded)"
        elif any(s.startswith("ASSUMED") for s in sts):
            status = "ASSUMED — OWNER-APPROVED part"
        else:
            status = "DRAWING-CONFIRMED"
        q07 = (None if all(f["owner_q07"] is None for f in fr)
               else sum(f["owner_q07"] or 0.0 for f in fr))  # blank: outside the owner's Q-07 B bands
        out.append({"line": ln, "line_state": state, "unit": "m2",
                    "floor": fr[0]["owner_floor"] or fr[0]["floor"], "faces": n, "faces_blank": blanks,
                    "gross_lo": None if blanks == len(fr) else r6(g_lo),
                    "gross_hi": None if blanks == len(fr) else r6(g_hi), "openings": m, "deduct_fixed": r6(d_fix),
                    "of_which_assumed": r6(assumed), "deduct_held_lo": r6(d_lo), "deduct_held_hi": r6(d_hi),
                    "net_lo": None if blanks == len(fr) else r6(n_lo),
                    "net_hi": None if blanks == len(fr) else r6(n_hi), "owner_q07_drawing_confirmed_part": r6(q07),
                    "status": status, "point_value": fmt(r6(n_lo)) if abs(n_hi - n_lo) < 1e-6 and blanks == 0 else "",
                    "geometry_carrier": (GEOM_LINE[fr[0]["owner_floor"]] if state == "EXISTING" else
                                         GEOM_LINE["PLINTH"] if "PLINTH" in ln else "")})
    return out


def item_fill(items):
    out = {}
    for i in items:
        if i["line_state"] != "NEW":
            continue
        k = (i["line"], i["unit"])
        o = out.setdefault(k, {"line": i["line"], "line_state": "NEW", "unit": i["unit"], "rows": 0, "lo": 0.0,
                               "hi": 0.0, "blank": 0, "statuses": set()})
        o["rows"] += 1
        o["statuses"].add(i["status"])
        if i["lo"] is None:
            o["blank"] += 1
        else:
            o["lo"] += i["lo"]
            o["hi"] += i["hi"]
    rows = []
    for (_ln, _u), o in out.items():
        st = o["statuses"]
        status = ("UNKNOWN (no number)" if st == {"UNKNOWN"} else "HELD (blank)" if o["blank"] == o["rows"]
                  else "HELD (bounded)" if ("HELD" in st or "UNKNOWN" in st) else
                  "ASSUMED — OWNER-APPROVED part" if any(s.startswith("ASSUMED") for s in st) else "DRAWING-CONFIRMED")
        rows.append({"line": o["line"], "line_state": "NEW", "unit": o["unit"], "rows": o["rows"],
                     "rows_blank": o["blank"], "qty_lo": "" if o["blank"] == o["rows"] else fmt(r6(o["lo"])),
                     "qty_hi": "" if o["blank"] == o["rows"] else fmt(r6(o["hi"])), "status": status})
    return rows


# -------------------------------------------------------------------------------------------------------- closure
def closure(faces, fill):
    t305 = read(T305 / "FACE_LINE_LEDGER_T305.csv")
    g305 = sum(f_(r["geometric_m2"]) or 0.0 for r in t305)
    h305_lo = sum(f_(r["held_lo_m2"]) or 0.0 for r in t305)
    h305_hi = sum(f_(r["held_hi_m2"]) or 0.0 for r in t305)
    dc = sum(f["lo"] for f in faces if f["status"] != "HELD" and f["lo"] is not None)
    h_lo = sum(f["lo"] or 0.0 for f in faces if f["status"] == "HELD")
    h_hi = sum(f["hi"] or 0.0 for f in faces if f["status"] == "HELD")
    nw2 = [f for f in faces if f["key"] == "1F/NW-2/PARAPET/parapet"][0]
    c3 = nw2["hi"] - nw2["lo"]
    rows = [("T-305 faces measured (every drawn face once)", g305, g305, "T-305 FACE_LINE_LEDGER"),
            ("T-305 HELD faces", h305_lo, h305_hi, "T-305 FACE_LINE_LEDGER"),
            ("this binding: drawing-confirmed faces", dc, dc, "BINDING_T337"),
            ("this binding: HELD faces (incl. NW-2 now HELD, C5 added)", h_lo, h_hi, "BINDING_T337"),
            ("named: 1F NW-2 parapet moved from measured to HELD (T-324 C3)", -nw2["hi"], -nw2["hi"],
             "measured part leaves DC"), ("named: 1F NW-2 as HELD", nw2["lo"], nw2["hi"], f"chord: -{c3:.6f} m2"),
            ("named: annex C5 outer face on AC7 (not in T-305)", 0.0, C5_OUTER, "T-324 C5")]
    res_dc = dc - (g305 - nw2["hi"])
    res_h = (h_lo - (h305_lo + nw2["lo"] + 0.0), h_hi - (h305_hi + nw2["hi"] + C5_OUTER))
    rows.append(("residual DC (must be 0)", res_dc, res_dc, "named closure"))
    rows.append(("residual HELD (must be 0)", res_h[0], res_h[1], "named closure"))
    # component cross-checks against T-311 / T-324
    by = {f["line"]: f for f in fill}
    comp = {(r["component"], r["chain"]): r for r in read(T324 / "COMPONENT_SUMMARY_T324.csv")}
    roof = {r["chain"]: float(r["roof_level"]) for r in read(T311 / "PARAPET_RUN_LEDGER_T311.csv")}
    for ch in ("ANNEX", "GF", "1F", "2F"):
        ln = NEW("FINISH", f"PARAPET-OUTER {ch} +{roof[ch]:.2f}")
        c = comp[("OUTER_FACE", ch)]
        rows.append((f"parapet outer {ch}: binding gross vs T-324 OUTER_FACE", by[ln]["gross_lo"] - float(c["qty_lo"]),
                     by[ln]["gross_hi"] - float(c["qty_hi"]),
                     "named: annex lo = C5 taken 0 .. 0.600 (T-324 carries 0.600); 1F lo = C3 chord -0.362192; "
                     "<= 0.0007 = T-305 4-decimal faces vs T-311 / T-324 run lengths"))
    pl = read(T311 / "PLINTH_SEGMENT_LEDGER_T311.csv")
    p_lo = sum(float(r["face_m2_lo"]) for r in pl)
    p_hi = sum(float(r["face_m2_hi"]) for r in pl)
    ln = NEW("FINISH", "PLINTH GF")
    rows.append(("plinth: binding gross vs T-311 PLINTH_SEGMENT (29 segments)", by[ln]["gross_lo"] - p_lo,
                 by[ln]["gross_hi"] - p_hi, "T-311 4-decimal segments"))
    return [{"check": a, "lo": fmt(r6(b)), "hi": fmt(r6(c)), "note": d} for a, b, c, d in rows]


# ------------------------------------------------------------------------------------------------- the freelancer
MAP = {  # his row -> owner lines of this binding (T-162 TERMS mapping of his row to drawn faces; T-324 for parapets)
    "51": "GF storey; PARAPET-OUTER GF; PLINTH", "52": "GF storey; 1F storey; PARAPET-OUTER 1F; PLINTH",
    "53": "GF storey; 1F storey; 2F storey; PARAPET-OUTER 2F; PLINTH", "54": "GF storey; PARAPET-OUTER ANNEX; PLINTH",
    "55": "GF storey; PARAPET-OUTER ANNEX; PLINTH", "58": "GF storey; 1F storey; 2F storey; PARAPET-OUTER 2F; PLINTH",
    "59": "1F storey; PARAPET-OUTER 1F; GF storey (the 4.080 face on the annex roof)",
    "60": "GF storey; PARAPET-OUTER ANNEX; PLINTH", "61": "FRAME (HELD)",
    "63": "GF storey; PARAPET-OUTER ANNEX; PLINTH", "64": "GF storey; 1F storey; PARAPET-OUTER GF; PARAPET-OUTER 1F; PLINTH",
    "65": "none (no such face drawn: possible double count)", "68": "none (no such face drawn)",
    "69": "none (2F sea face is row 77: double count)", "70+71+74": "1F storey; PARAPET-OUTER 1F",
    "72": "NOT_APPLICABLE (owner item 3)", "73": "L-23072352a28aeca7b051 (FIN.CEILING 12.834)", "75": "FRAME (HELD)",
    "77": "2F storey; PARAPET-OUTER 2F", "78": "PARAPET-INNER 1F; UPTURN-ZONE 1F; PARAPET-TOP 1F",
    "79": "PARAPET-INNER ANNEX; UPTURN-ZONE ANNEX; PARAPET-TOP ANNEX",
    "83+84": "PARAPET-INNER GF + 2F; UPTURN-ZONE GF + 2F; PARAPET-TOP GF + 2F",
    "87-90": "OTHER_TRADE boundary (HELD, Q-65 C)", "92": "NEW FIN.EXT.DRIP (UNKNOWN)"}


def his_cells():
    d = json.loads(RAW.read_text(encoding="utf-8"))
    rows = {}
    for x in d["rows"]:
        if x["file"] == "PLS":
            rows[(x["sheet"], x["row"])] = {k: v["v"] for k, v in x["cells"].items()}
    return rows


def freelancer_rows():
    cells = his_cells()
    sheet = [s for (s, r) in cells if r == 93 and "J93" in cells[(s, r)]][0]
    inv = [s for (s, r) in cells if r == 25 and "F25" in cells[(s, r)]][0]
    terms = read(T162 / "TERMS_T162.csv")
    t324 = {r["his_row"]: r for r in read(T324 / "FREELANCER_T324.csv")}
    out = []
    for key in MAP:
        nums = [int(k) for k in key.replace("+", " ").replace("-", " ").split()]
        if key == "87-90":
            nums = [87, 88, 89, 90]
        his = 0.0
        form = []
        for n in nums:
            c = cells.get((sheet, n), {})
            i = c.get(f"I{n}")
            if i is None and n == 92:
                i = c.get("J92")
            his += float(i or 0.0)
            form.append(f"r{n}: E{c.get(f'E{n}', '')} F{c.get(f'F{n}', '')} G{c.get(f'G{n}', '')} "
                        f"H{c.get(f'H{n}', '')} = {float(i or 0.0):.4f}")
        t = [x for x in terms if x["HIS_ROW"] == key]
        drawn, status, cause = "", "", ""
        if key in t324:
            r = t324[key]
            drawn = f"{float(r['drawing_inner_plus_top_lo']):.3f} .. {float(r['drawing_inner_plus_top_hi']):.3f}"
            status = "per T-324"
            cause = "inner face + top (his 0.70 = 0.50 + 0.20); see T-324 FREELANCER"
        elif t:
            drawn = t[0]["DRAWING_GEOMETRIC_M2"]
            status, cause = t[0]["STATUS"], t[0]["CAUSE"]
        elif key == "87-90":
            status, cause = "HELD_Q-65", "boundary wall: not a house face"
        out.append({"his_rows": key, "his_cells": " | ".join(form), "his_m2": fmt(r6(his)), "drawing_m2": drawn,
                    "owner_lines_here": MAP[key], "t162_status": status, "cause": cause})
    gross = float(cells[(sheet, 93)]["J93"])
    half = float(cells[(inv, 25)]["D25"])
    net = float(cells[(inv, 25)]["F25"])
    wall_rows = (51, 52, 53, 54, 55, 58, 59, 60, 63, 64, 65, 68, 69, 70, 71, 74, 77)
    walls = sum(float(cells[(sheet, n)][f"I{n}"]) for n in wall_rows)
    par = sum(float(cells[(sheet, n)][f"I{n}"]) for n in (78, 79, 83, 84))
    return out, {"his_walls_rows_51_77": r6(walls), "his_parapet_rows_78_84": r6(par), "his_gross_J93": gross, "his_openings_half_D25": half, "his_net_F25": net,
                 "his_openings_full_J97": float(cells[(sheet, 97)]["J97"])}


# --------------------------------------------------------------------------------------------------------- outputs
FACE_COLS = ["key", "floor", "side", "portion", "part", "kind", "bottom", "top", "length_m", "lo", "hi", "owner_q07",
             "status", "line", "line_state", "owner_floor", "t305_band", "t305_state", "t305_line", "geometry_line", "why"]
OPEN_COLS = ["floor", "side", "opening", "face_key", "line", "hole_m2", "fixed", "lo", "hi", "status", "sill_abs",
             "head_abs", "t305_line", "check"]
ITEM_COLS = ["item", "line", "line_state", "unit", "lo", "hi", "status", "source", "why"]
FILL_COLS = ["line", "line_state", "unit", "floor", "faces", "faces_blank", "gross_lo", "gross_hi", "openings",
             "deduct_fixed", "of_which_assumed", "deduct_held_lo", "deduct_held_hi", "net_lo", "net_hi",
             "point_value", "owner_q07_drawing_confirmed_part", "status", "geometry_carrier"]
IFILL_COLS = ["line", "line_state", "unit", "rows", "rows_blank", "qty_lo", "qty_hi", "status"]


def csv_text(rows, cols):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(cols)
    for r in rows:
        w.writerow([fmt(r[c]) if isinstance(r[c], float) else ("" if r[c] is None else r[c]) for c in cols])
    return buf.getvalue()


def outputs():
    cand, _by = candidate()
    faces = face_rows()
    openings = opening_rows(faces)
    items = item_rows()
    bk = book_all(faces, openings, items)
    fill = fill_rows(faces, openings, bk)
    ifill = item_fill(items)
    clo = closure(faces, fill)
    fr, his = freelancer_rows()
    ours = {}
    for f in fill:
        ours[f["line"]] = (f["net_lo"], f["net_hi"])
    st = [f for f in fill if f["line_state"] == "EXISTING"]
    st_lo, st_hi = sum(f["net_lo"] for f in st), sum(f["net_hi"] for f in st)
    allm2_lo = sum(f["net_lo"] or 0.0 for f in fill)
    allm2_hi = sum(f["net_hi"] or 0.0 for f in fill)
    rec = {r["reference"]: r for r in read(T324 / "RECONCILIATION_T324.csv")}
    inner = rec["T-305 parapet items m2: inner faces"]
    tops = rec["T-305 parapet items m2: tops"]
    # the inner face is ONE face split at the upturn top (above + upturn zone): its total, not the sum of the split hi's
    it_lo = float(inner["this_ledger_lo"]) + float(tops["this_ledger_lo"])
    it_hi = float(inner["this_ledger_hi"]) + float(tops["this_ledger_hi"])
    summary = {
        "candidate": {k: cand[k] for k in ("lines_json_sha256_8", "lines_csv_sha256_8", "lines_total")},
        "faces": len(faces), "openings": len(openings), "items": len(items),
        "lines_m2": {f["line"]: {"gross": [f["gross_lo"], f["gross_hi"]], "net": [f["net_lo"], f["net_hi"]],
                                 "status": f["status"]} for f in fill},
        "storey_lines_net": [r6(st_lo), r6(st_hi)],
        "all_face_lines_net": [r6(allm2_lo), r6(allm2_hi)],
        "parapet_inner_face_total_plus_top_m2": [r6(it_lo), r6(it_hi)],
        "wall_face_lines_plus_parapet_inner_and_top_net": [r6(allm2_lo + it_lo), r6(allm2_hi + it_hi)],
        "his_walls_net_rows_51_77_minus_half_openings": r6(his["his_walls_rows_51_77"] - his["his_openings_half_D25"]),
        "freelancer": his,
        "closure_residuals": {c["check"]: [c["lo"], c["hi"]] for c in clo if c["check"].startswith("residual")},
    }
    return {
        "BINDING_T337.csv": csv_text(faces, FACE_COLS),
        "OPENINGS_T337.csv": csv_text(openings, OPEN_COLS),
        "ITEMS_T337.csv": csv_text(items, ITEM_COLS),
        "FILL_T314_T337.csv": csv_text(fill, FILL_COLS),
        "FILL_ITEMS_T314_T337.csv": csv_text(ifill, IFILL_COLS),
        "CLOSURE_T337.csv": csv_text(clo, ["check", "lo", "hi", "note"]),
        "FREELANCER_T337.csv": csv_text(fr, ["his_rows", "his_cells", "his_m2", "drawing_m2", "owner_lines_here",
                                             "t162_status", "cause"]),
        "summary.json": json.dumps(summary, indent=1, ensure_ascii=False, sort_keys=True) + "\n",
    }


def main(argv):
    if argv[:1] == ["--extract"]:
        extract(argv[1])
        return 0
    outs = outputs()
    if argv[:1] == ["--write"]:
        for name, text in outs.items():
            (HERE / name).write_text(text, encoding="utf-8")
        print(f"wrote {len(outs)} files")
        return 0
    if argv[:1] == ["--check"]:
        bad = [n for n, t in outs.items() if (HERE / n).read_text(encoding="utf-8") != t]
        print("check:", "OK" if not bad else f"DIFFER {bad}")
        return 1 if bad else 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
