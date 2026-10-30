"""T-349 on the development villa: the merged T-317 spatter-dash ledger (B4-05) bound face by face to the candidate of
record ARCH_TAKEOFF_V3.0.24 (interior plaster / backing lines) and to the merged T-337 exterior face keys, with the
concrete / block substrate beside each face, the closure on T-317 and a FILL table for a later lane I row.
Research only: no engine module, rule, knowledge or registry file, candidate line or released line is changed.

Inputs (all MERGED in this repository; no drawing is read, no coordinate or client text is written):
  candidate  research/agents_t340/CANDIDATE_V3022_T340.json (V3.0.22 json 7199c8b6: every FIN.PLASTER and FIN.WALL.TILE
             line) + research/agents_t338/V3_0_24_LINE_STATE_FIXES.csv (T-338 MERGED dd4c9f8f: the 7 FIN.PLASTER text
             fixes of V3.0.24, quantity fields asserted equal) + research/agents_t347/CANDIDATE_V3024_BURIED_LINES.json
             (V3.0.24 json 19394733 item-code census: FIN.PLASTER 67, FIN.WALL.TILE 18, FIN.EXT.FINISH 3). V3.0.23
             (T-319) adds STR.CONC.PARAPET lines only and asserts every V3.0.22 line byte-identical; V3.0.24 changes text /
             state fields only ('no quantity, no state word, no range and no line id changes').
  wet faces  research/agents_t329/BACKING_FACE_LEDGER_T329.csv (T-329 MERGED 1c82807b; = the T-331 backing lines)
  dry faces  research/agents_t292/FACE_TO_LINE_LEDGER_T292.csv + LINE_SUMMARY_T292.csv (T-292 MERGED a9754a67)
  exterior   research/agents_t337/BINDING_T337.csv, OPENINGS_T337.csv, ITEMS_T337.csv, FILL_T314_T337.csv (T-337 MERGED)
  reveals    research/agents_t340/FILL_T326_T340.csv (T-340 MERGED 25c1f52c: the T-326 carriers not yet in a line)
  T-317      research/agents_t317/SPATTER_T317.csv (MERGED 328a7095) and t317_alsenan.ledger() (wall-side split)

    python3 -I research/agents_t349/t349_alsenan.py [--write | --check]
"""

from __future__ import annotations

import csv
import io
import json
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
RES = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(RES / "agents_t317"))
import t349_spatter_binding as B  # noqa: E402

OA = "ASSUMED — OWNER-APPROVED"
DC = "DRAWING-CONFIRMED"
SCOPE = B.Scope("B4-05", "OD-V3B-4 / OD-V3B-5 / OD-V3B-6 / OD-V3B-7 (owner 2026-10-04, Alsenan); "
                "URBAN-FINISH-EXTRAS-SEPARATE-ITEMS@v1 (OD-V3-4)",
                frozenset({"PLASTER", "TILE", "SIGMA", "CLADDING", "EXT_UNPRINTED"}))
# EXT_UNPRINTED: an exterior face whose final finish is not printed (plinth, parapet top): every answered exterior
# finish (Sigma OD-V3B-7, stone / marble OD-V3B-6) starts with SPATTER DASH, so the spatter scope holds either way.
OWNER_H = {"GF": 3.65, "1F": 3.35, "2F": 3.35}       # Q-43 / Q-48 A: the owner band of FACES_T317 (0.10 .. +H)
PINS = {"plaster_lines": 67, "tile_lines": 18, "wet_faces": 115, "ext_faces": 109, "t317_hosts": 60,
        "int_det": 575.2519, "ext_det": 873.3746}


def rd(p):
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def fnum(s):
    return None if s in (None, "") else float(s)


def r6(x):
    return None if x is None else round(x, 6)


# ------------------------------------------------------------------------------------------------ the candidate

def candidate():
    d = json.loads((RES / "agents_t340/CANDIDATE_V3022_T340.json").read_text(encoding="utf-8"))
    assert d["lines_total"]["V3_0_22"] == 3706, d["lines_total"]
    pl = {x["line_id"]: x for x in d["lines"] if x["item_code"] == "FIN.PLASTER"}
    ti = {x["line_id"]: x for x in d["lines"] if x["item_code"] == "FIN.WALL.TILE"}
    cen = json.loads((RES / "agents_t347/CANDIDATE_V3024_BURIED_LINES.json").read_text(encoding="utf-8"))
    assert cen["candidate"] == "ARCH_TAKEOFF_V3.0.24" and cen["candidate_lines_json_sha256"].startswith("19394733")
    c = cen["item_code_census"]
    if (c["FIN.PLASTER"], c["FIN.WALL.TILE"], c["FIN.EXT.FINISH"]) != (len(pl), len(ti), 3):
        raise SystemExit(f"V3.0.24 census differs from the V3.0.22 extract: {c}")
    if any("SPATTER" in k.upper() or k.upper().startswith("B4-05") for k in c):
        raise SystemExit("a spatter line is already in the candidate: re-bind instead of a FILL")
    # V3.0.24 text fixes on FIN.PLASTER: quantity fields must equal the V3.0.22 line
    for f in rd(RES / "agents_t338/V3_0_24_LINE_STATE_FIXES.csv"):
        if f["item_code"] != "FIN.PLASTER":
            continue
        x = pl[f["line_id"]]
        same = (fnum(f["measured_net"]) == x["measured_net"] and fnum(f["range_low"]) == x["low"]
                and fnum(f["range_high"]) == x["high"] and f["evidence_state"] == x["evidence_state"])
        if not same:
            raise SystemExit(f"V3.0.24 fix {f['line_id']} moved a quantity field")
    return pl, ti


def line_state(x):
    """(state, m2, lo, hi, held) of a candidate plaster line as a spatter host (T-317 convention)."""
    es = x["evidence_state"]
    if es == "PROVISIONAL" and x["measured_net"] is not None:
        return OA, x["measured_net"], None, None, ""
    if es == "BOUNDED_EXPOSURE":
        return "HELD", None, x["low"], x["high"], "host line HELD (bounded)"
    if es == "BLOCKED_RFI":
        return "HELD", None, None, None, "host line HELD blank (BLOCKED_RFI)"
    if es.startswith("NOT_APPLICABLE"):
        return "NA", None, None, None, "taken off (NOT_APPLICABLE_WITH_EVIDENCE)"
    raise SystemExit(f"{x['line_id']}: state {es}")


# ------------------------------------------------------------------------------------------------ interior

def interior(pl):
    wet = rd(RES / "agents_t329/BACKING_FACE_LEDGER_T329.csv")
    wet_lines = {f["plaster_line_id"] for f in wet if f["plaster_line_id"]}
    tile_of = {}
    for f in wet:
        if f["plaster_line_id"]:
            tile_of.setdefault(f["plaster_line_id"], set()).add(f["tile_line_id"] or "NO TILE LINE (pantry)")
    rows, na = [], []
    # wet / pantry faces: under the backing (tile-preparation) line, the tile line named as via (R-T349-2)
    for f in wet:
        if f["tile_scope"] != "TILED":
            continue                                       # OPEN_EDGE: no face
        lid = f["plaster_line_id"]
        st, m2, lo, hi, held = line_state(pl[lid])
        fam = "INT_WET_RESIDUAL" if f["piece"] == "WALK CLASS RESIDUAL" else "INT_WET_FACE"
        if st == OA:
            rows.append(B.Row(f"S-{f['face_id']}", fam, f["face_id"], "TILE", lid, lid, OA,
                              m2=float(f["backing_owner_m2"]), via=f["tile_line_id"] or "NO TILE LINE (pantry)"))
        else:
            rows.append(B.Row(f"S-{f['face_id']}", fam, f["face_id"], "TILE", lid, lid, "HELD",
                              held=(f["held_item"] or held)[:160], via=f["tile_line_id"]))
    # dry lines: one row per host line; its faces (T-292 DRY / SHAFT) named for traceability, never re-measured here
    summ = {x["line_id"]: x for x in rd(RES / "agents_t292/LINE_SUMMARY_T292.csv") if x["item_code"] == "FIN.PLASTER"}
    dry_faces = defaultdict(list)
    room_line = {s["ledger_rooms"]: lid for lid, s in summ.items() if s["ledger_rooms"] and lid not in wet_lines}
    t292 = [x for x in rd(RES / "agents_t292/FACE_TO_LINE_LEDGER_T292.csv") if x["item_code"] == "FIN.PLASTER"]
    for x in t292:
        if x["finish_class"] in ("DRY", "SHAFT") and x["room"] in room_line:
            dry_faces[room_line[x["room"]]].append(x["face_id"])
    wet_ids = {f["face_id"] for f in wet}
    clash = wet_ids & {fid for v in dry_faces.values() for fid in v}
    if clash:
        raise SystemExit(f"faces both wet and dry: {sorted(clash)[:5]}")
    for lid, x in sorted(pl.items(), key=lambda kv: (kv[1]["floor"], kv[1]["element_id"])):
        if lid in wet_lines:
            continue
        st, m2, lo, hi, held = line_state(x)
        if st == "NA":
            na.append({"line_id": lid, "element_id": x["element_id"], "why": held})
            continue
        rows.append(B.Row(f"S-{lid}", "INT_DRY_LINE", f"LINE:{lid}", "PLASTER", lid, lid, st, m2=m2, lo=lo, hi=hi,
                          held=held, via=";".join(sorted(dry_faces.get(lid, [])))))
    return rows, na, wet, tile_of


# ------------------------------------------------------------------------------------------------ exterior

def exterior():
    faces = rd(RES / "agents_t337/BINDING_T337.csv")
    ops = defaultdict(list)
    for o in rd(RES / "agents_t337/OPENINGS_T337.csv"):
        if o["face_key"] not in ("", "-"):
            ops[o["face_key"]].append(o)
    rows = []
    for f in faces:
        lo, hi = fnum(f["lo"]), fnum(f["hi"])
        fixed = sum(fnum(o["fixed"]) or 0.0 for o in ops[f["key"]])
        hlo = sum(fnum(o["lo"]) or 0.0 for o in ops[f["key"]] if o["status"] == "HELD")
        hhi = sum(fnum(o["hi"]) or 0.0 for o in ops[f["key"]] if o["status"] == "HELD")
        assumed = any(o["status"] == OA for o in ops[f["key"]])
        finish = "EXT_UNPRINTED" if f["kind"] == "plinth" else "SIGMA"
        tgt = f"T337:{f['key']}"
        if lo is None:
            rows.append(B.Row(f"S-{f['key']}", "EXT_FACE", f["key"], finish, tgt, f["line"], "HELD",
                              held=f["why"][:160]))
            continue
        nlo, nhi = lo - fixed - hhi, hi - fixed - hlo
        if f["status"] == "HELD" or abs(nhi - nlo) > 1e-9:
            rows.append(B.Row(f"S-{f['key']}", "EXT_FACE", f["key"], finish, tgt, f["line"], "HELD",
                              lo=r6(nlo), hi=r6(nhi), held=(f["why"] or "held hole on this face")[:160]))
        else:
            rows.append(B.Row(f"S-{f['key']}", "EXT_FACE", f["key"], finish, tgt, f["line"], OA if assumed else DC,
                              m2=r6(nlo)))
    items = []
    for it in rd(RES / "agents_t337/ITEMS_T337.csv"):
        name = it["item"]
        if name.startswith("parapet inner_face_above_upturn") or name.startswith("parapet top_surface"):
            fin = "PLASTER" if "inner_face" in name else "EXT_UNPRINTED"
            lo, hi = fnum(it["lo"]), fnum(it["hi"])
            if it["status"] == DC and lo == hi:
                items.append(B.Row(f"S-{name}", "EXT_ITEM", name, fin, f"T337:{name}", it["line"], DC, m2=lo))
            else:
                items.append(B.Row(f"S-{name}", "EXT_ITEM", name, fin, f"T337:{name}", it["line"], "HELD",
                                   lo=lo, hi=hi, held=it["why"][:160]))
        elif it["line"] in ("NEW FIN.EXT.FRAME (m2)", "NEW FIN.EXT.FINISH DIVIDER (m2)"):
            items.append(B.Row(f"S-{name}", "EXT_ITEM", name, "EXT_UNPRINTED", f"T337:{name}", it["line"], "UNKNOWN",
                               held=f"host {it['status']}: {it['why']}"[:160]))
    return rows, items


def pending_reveals():
    out = []
    for r in rd(RES / "agents_t340/FILL_T326_T340.csv"):
        if r["action"] not in ("ADD_ROW", "ADD_HELD_ROW", "NARROW"):
            continue
        out.append({"carrier": r["carrier"], "opening": r["opening"], "item": r["item"], "action": r["action"],
                    "m2": r["m2"], "status": r["status"].split(" (")[0] + (f"; HELD beside: {r['held']}" if r["held"] and r["m2"] else ""),
                    "spatter": ("the line's own row (V3.0.24 range kept until T-326 narrows it)" if r["action"] == "NARROW"
                                else "PENDING_CARRIER: no V3.0.24 line yet; a B4-05 row follows the T-326 carrier")})
    return out


# ------------------------------------------------------------------------------------------------ substrate

def substrate_rows(rows):
    import t317_alsenan as T
    L = T.ledger()
    side = defaultdict(lambda: {"face": 0.0, "conc": 0.0, "blk": 0.0, "held": 0, "items": [], "len": 0.0})
    for f in L["F_own"]:
        if f["side"] not in ("INT", "INT-A"):
            continue                                       # an internal wall's two sides are symmetric: one counted
        s = side[f["wall_id"]]
        if f["state"] != "MEASURED":
            s["held"] += 1
            continue
        s["face"] += f["face_m2"]
        s["conc"] += f["concrete_m2"]
        s["blk"] += f["block_m2"]
        s["len"] += f["face_m2"] / OWNER_H[f["floor"]]
        s["items"] += [f"{k}:{m or '-'}" for k, m, _a in f["items"]]
    t292 = {x["face_id"]: x for x in rd(RES / "agents_t292/FACE_TO_LINE_LEDGER_T292.csv")}
    wet = {x["face_id"]: x for x in rd(RES / "agents_t329/BACKING_FACE_LEDGER_T329.csv")}
    out = []
    for r in rows:
        fids = r.via.split(";") if r.family == "INT_DRY_LINE" else [r.face_id]
        for fid in fids:
            if not fid or r.family.startswith("EXT"):
                continue
            src = wet.get(fid) or t292.get(fid)
            wid = fid.split("|", 1)[1] if "|" in fid else ""
            s = side.get(wid)
            rec = {"face_id": fid, "row_id": r.row_id, "line": r.carrier_line, "wall_id": wid,
                   "face_length_m": src["length_m"] if src else ""}
            if s is None:
                rec.update(state="HELD", why="not a register wall side (column face, residual, off-wall piece or "
                                              "a wall with no census run): substrate not measured here")
            elif s["held"] and not s["face"]:
                rec.update(state="HELD", why="wall side split HELD in T-317 (band or block top not established)")
            else:
                whole = (not s["held"]) and src is not None and abs(float(src["length_m"]) - s["len"]) < 0.005
                sp = B.substrate(round(s["face"], 6), round(s["conc"], 6), round(s["blk"], 6), whole)
                rec.update(state=sp["state"], why=sp.get("why", ""), side_face_m2=round(s["face"], 6),
                           side_concrete_m2=round(s["conc"], 6), side_block_m2=round(s["blk"], 6),
                           side_length_m=round(s["len"], 4), concrete_sources=" ".join(sorted(set(s["items"])))[:300])
            out.append(rec)
    ext = {}
    for f in L["F_ext"]:
        a = ext.setdefault(f["floor"], {"face": 0.0, "conc": 0.0, "blk": 0.0, "held": 0})
        if f["state"] == "MEASURED":
            a["face"] += f["face_m2"]
            a["conc"] += f["concrete_m2"]
            a["blk"] += f["block_m2"]
        else:
            a["held"] += 1
    return out, {k: {x: round(y, 4) for x, y in v.items()} for k, v in sorted(ext.items())}


# ------------------------------------------------------------------------------------------------ closure on T-317

def closure(rows, items, pl):
    t317 = rd(RES / "agents_t317/SPATTER_T317.csv")
    by_line = defaultdict(list)
    for r in rows + items:
        by_line[r.carrier_line].append(r)
    wet = rd(RES / "agents_t329/BACKING_FACE_LEDGER_T329.csv")
    backing_of_tile = {f["tile_line_id"]: f["plaster_line_id"] for f in wet if f["tile_line_id"]}

    def agg(rs):
        m2 = sum(r.m2 for r in rs if r.m2 is not None)
        lo = sum(r.lo for r in rs if r.lo is not None)
        hi = sum(r.hi for r in rs if r.hi is not None)
        return m2, lo, hi

    out = []
    for h in t317:
        before = (fnum(h["quantity"]), fnum(h["lo"]), fnum(h["hi"]))
        hl = h["host_line"]
        if h["host_item"] == "FIN.PLASTER":
            tgt, cause = hl, "same line"
        elif h["host_item"] == "FIN.WALL.TILE":
            tgt, cause = backing_of_tile[hl], ("re-bound from the tile line to its backing (tile-preparation) line, "
                                               "T-331 V3.0.22; faces equal the tile faces (closure 0, T-329)")
        else:
            tgt, cause = None, "T-337 re-binding of the exterior faces"
        if tgt:
            rs = by_line[tgt]
            m2, lo, hi = agg(rs)
            st = {r.state for r in rs}
            after = (m2 if st <= set(B.DET) else None, lo if "HELD" in st and lo else None,
                     hi if "HELD" in st and hi else None)
            if hl == "L-721a0f1441436193978c":
                cause = ("pantry room-face line FILLED by T-331 (V3.0.22): backing 32.3422 under the pantry tile "
                         "(T-312 NO LINE): blank -> ASSUMED — OWNER-APPROVED")
            if before[1] is not None or after[1] is not None:
                dl, dh = (after[1] or 0.0) - (before[1] or 0.0), (after[2] or 0.0) - (before[2] or 0.0)
                d = f"lo {dl:+.6f} / hi {dh:+.6f}"
                if abs(dl) > 1e-9 or abs(dh) > 1e-9:
                    if max(abs(dl), abs(dh)) > 0.0001 + 1e-9:
                        raise SystemExit(f"{hl}: held range moved {d} without a named cause")
                    cause += ("; T-317 took the 6-dp T-244 constants (61.46265 / 61.71775), the line prints 4 dp: "
                              "rounding, not a change")
            else:
                d = f"{(after[0] or 0.0) - (before[0] or 0.0):+.6f}"
            out.append({"t317_host": hl, "t317_item": h["host_item"], "t317_state": h["state"],
                        "t317_m2": h["quantity"], "t317_lo": h["lo"], "t317_hi": h["hi"], "t349_target": tgt,
                        "t349_rows": len(rs), "t349_m2": r6(after[0]) if after[0] is not None else "",
                        "t349_lo": r6(after[1]) if after[1] is not None else "",
                        "t349_hi": r6(after[2]) if after[2] is not None else "", "delta_m2": d, "cause": cause})
        else:
            out.append({"t317_host": hl, "t317_item": h["host_item"], "t317_state": h["state"],
                        "t317_m2": h["quantity"], "t317_lo": h["lo"], "t317_hi": h["hi"], "t349_target": "see EXTERIOR",
                        "t349_rows": "", "t349_m2": "", "t349_lo": "", "t349_hi": "", "delta_m2": "", "cause": cause})
    return out, backing_of_tile


EXT_MOVES = [   # T-317 exterior host -> T-337 line(s), each move physical (T-337 s.2 table), m2
    ("1F storey L-8bb83e16", "234.5255 DC", "234.525528 DC", "0", "unchanged"),
    ("2F storey L-d52c4f76", "132.2050 OA", "117.305000 OA", "-14.900000",
     "band +13.90 -> +14.40 above the 2F roof moved to PARAPET-OUTER 2F (T-337 rule 1, T-311)"),
    ("GF storey L-b05f70c9", "387.2852 .. 420.7702 HELD", "376.694149 .. 410.179149 HELD", "-14.671022 + 4.080000",
     "annex band +4.30 -> +4.80 moved to PARAPET-OUTER ANNEX; the 1F SE-1 face on the annex roof (T-317 NO_LINE "
     "4.0800) is inside the GF storey by levels"),
    ("NO_LINE lower-roof face", "4.0800 DC", "0 (in the GF storey line)", "-4.080000", "moved, not lost"),
    ("NO_LINE parapet outer", "68.2978 .. 73.6758 HELD", "97.506666 .. 103.846858 HELD + DC", "+14.671022 +14.900000 "
     "-0.362192 lo / +0.600000 hi", "the two bands above; T-324 C3 (1F NW-2 chord vs arc, lo -0.362192), C5 (annex "
     "B34 face 0 .. 0.600)"),
    ("NO_LINE plinth", "71.6886 .. 72.7498 HELD", "71.688590 .. 72.749795 HELD", "0", "unchanged"),
    ("(not in T-317) parapet inner face above the upturn", "-", "67.411393 .. 99.557545 HELD", "+",
     "a finished plaster face (owner trade PLASTER_PARAPET_INNER, T-324 / T-337) missed by T-317: OMISSION"),
    ("(not in T-317) parapet top surface", "-", "5.415000 DC + 21.421476 .. 21.557520 HELD", "+",
     "plain top (section A-A), a finished exterior face: OMISSION of T-317"),
    ("(not in T-317) slab edge over open air", "-", "BLANK HELD (9 faces, depth not printed Q-68 C)", "+ blank",
     "finished face, area HELD blank"),
]


# ------------------------------------------------------------------------------------------------ fill

def fill(rows, items, pend):
    by = defaultdict(list)
    for r in rows + items:
        by[r.carrier_line].append(r)
    out = []
    for line, rs in sorted(by.items()):
        st = {r.state for r in rs}
        m2 = sum(r.m2 for r in rs if r.m2 is not None)
        lo = sum((r.m2 if r.m2 is not None else (r.lo or 0.0)) for r in rs)
        hi = sum((r.m2 if r.m2 is not None else (r.hi or 0.0)) for r in rs)
        blank = sum(1 for r in rs if r.m2 is None and r.lo is None)
        if st <= set(B.DET):
            status = sorted(st)[0] if len(st) == 1 else OA + " part"
            q, l_, h_ = r6(m2), "", ""
        elif blank == len(rs):
            status, q, l_, h_ = ("UNKNOWN" if st == {"UNKNOWN"} else "HELD (blank)"), "", "", ""
        else:
            status, q, l_, h_ = "HELD (bounded)" + (f"; {blank} face(s) blank beside" if blank else ""), "", r6(lo), r6(hi)
        out.append({"proposed_line": f"NEW B4-05 SPATTER DASH under {line}", "host_line": line, "unit": "m2",
                    "family": rs[0].family.split("_")[0], "rows": len(rs), "rows_blank": blank, "quantity": q,
                    "lo": l_, "hi": h_, "status": status, "evidence_source": SCOPE.source})
    for p in pend:
        if p["action"] == "NARROW":
            continue
        out.append({"proposed_line": f"NEW B4-05 SPATTER DASH under {p['carrier']} (after T-326)",
                    "host_line": p["carrier"], "unit": "m2", "family": "PENDING", "rows": 1,
                    "rows_blank": 0 if p["m2"] else 1, "quantity": p["m2"] if p["status"] != "UNKNOWN" and p["m2"] else "",
                    "lo": "", "hi": "", "status": (p["status"] if p["m2"] else "HELD (blank)") + " (PENDING_CARRIER)",
                    "evidence_source": "T-340 FILL_T326 " + p["action"]})
    return out


def line_level(fl):
    """per family, at the granularity T-317 used (one figure per host line): a HELD line contributes its range even
    where most of its faces are determinate (the face-level split is in SPATTER_BINDING_T349.csv)."""
    out = {}
    for f in fl:
        fam = f["family"]
        a = out.setdefault(fam, {"determinate": 0.0, "held_lo": 0.0, "held_hi": 0.0, "blank_lines": 0, "lines": 0})
        a["lines"] += 1
        if f["quantity"] not in ("", None):
            a["determinate"] += float(f["quantity"])
        elif f["lo"] not in ("", None):
            a["held_lo"] += float(f["lo"])
            a["held_hi"] += float(f["hi"])
        else:
            a["blank_lines"] += 1
    return {k: {x: (round(y, 6) if isinstance(y, float) else y) for x, y in v.items()} for k, v in sorted(out.items())}


# ------------------------------------------------------------------------------------------------ build

def build():
    pl, ti = candidate()
    rows, na, wet, tile_of = interior(pl)
    erows, items = exterior()
    allrows = rows + erows + items
    clos, backing_of_tile = closure(rows, items, pl)
    B.bind(allrows, SCOPE, backing_of_tile)
    # R-T349-5: each interior host line closes on its candidate figure; each exterior line on the T-337 FILL net
    for lid in {r.carrier_line for r in rows}:
        st, m2, lo, hi, _h = line_state(pl[lid])
        B.close_on_host(rows, lid, m2, lo, hi)
    for f in rd(RES / "agents_t337/FILL_T314_T337.csv"):
        lo, hi = fnum(f["net_lo"]), fnum(f["net_hi"])
        mine = [r for r in erows if r.carrier_line == f["line"]]
        if lo is None:
            assert all(r.m2 is None and r.lo is None for r in mine), f["line"]
            continue
        B.close_on_host(erows, f["line"], lo if abs(hi - lo) < 1e-9 and "HELD" not in f["status"] else None,
                        None if abs(hi - lo) < 1e-9 and "HELD" not in f["status"] else lo,
                        None if abs(hi - lo) < 1e-9 and "HELD" not in f["status"] else hi)
    pend = pending_reveals()
    sub, ext_split = substrate_rows(rows)
    fl = fill(rows, erows + items, pend)
    tot_int, tot_ext = B.totals(rows), B.totals(erows + items)
    det_int = sum(v["m2"] for k, v in tot_int.items() if k in B.DET)
    det_ext = sum(v["m2"] for k, v in tot_ext.items() if k in B.DET)
    pins = {"plaster_lines": len(pl), "tile_lines": len(ti), "wet_faces": sum(1 for r in rows if r.family.startswith("INT_WET")),
            "ext_faces": len(erows), "t317_hosts": len(clos), "int_det": round(det_int, 4), "ext_det": round(det_ext, 4)}
    if pins != PINS:
        raise SystemExit(f"pins moved: {pins} != {PINS}")
    summary = {
        "schema": "T349_SPATTER_BINDING_V1", "candidate": "ARCH_TAKEOFF_V3.0.24 (json 19394733; plaster / tile lines "
        "= V3.0.22 json 7199c8b6, quantity fields asserted)", "scope": SCOPE.source, "pins": pins,
        "interior": tot_int, "exterior": tot_ext,
        "interior_determinate_equals_FIN_PLASTER_live_V3_0_24": round(det_int, 4),
        "not_applicable_plaster_lines": len(na), "pending_reveal_carriers": len(pend),
        "substrate_states": {k: sum(1 for s in sub if s["state"] == k) for k in ("ESTABLISHED", "HELD")},
        "exterior_wall_side_split_T317_by_floor": ext_split,
        "double_count_m2": 0.0,
        "line_level": line_level(fl),
        "t317_line_level": {"determinate": 913.7202, "held_lo": 1016.7526, "held_hi": 1112.6565, "blank_hosts": 10},
    }
    return {"rows": allrows, "na": na, "closure": clos, "pending": pend, "substrate": sub, "fill": fl,
            "summary": summary}


ROW_COLS = ["row_id", "family", "face_id", "finish", "target", "carrier_line", "state", "m2", "lo", "hi", "held", "via"]
CLOS_COLS = ["t317_host", "t317_item", "t317_state", "t317_m2", "t317_lo", "t317_hi", "t349_target", "t349_rows",
             "t349_m2", "t349_lo", "t349_hi", "delta_m2", "cause"]
SUB_COLS = ["face_id", "row_id", "line", "wall_id", "face_length_m", "state", "why", "side_length_m", "side_face_m2",
            "side_concrete_m2", "side_block_m2", "concrete_sources"]
FILL_COLS = ["proposed_line", "host_line", "unit", "family", "rows", "rows_blank", "quantity", "lo", "hi", "status",
             "evidence_source"]
PEND_COLS = ["carrier", "opening", "item", "action", "m2", "status", "spatter"]


def csv_text(rows, cols):
    s = io.StringIO()
    w = csv.DictWriter(s, fieldnames=cols, lineterminator="\n", extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in cols})
    return s.getvalue()


def outputs():
    b = build()
    rows = [{c: getattr(r, c) for c in ROW_COLS} for r in b["rows"]]
    ext = [{"t317_host": a, "t317_m2": x, "t349_m2": y, "delta_m2": d, "cause": c, "t317_item": "FIN.EXT.FINISH",
            "t349_target": "T-337 lines"} for a, x, y, d, c in EXT_MOVES]
    return {
        "SPATTER_BINDING_T349.csv": csv_text(rows, ROW_COLS),
        "CLOSURE_T349.csv": csv_text(b["closure"] + ext, CLOS_COLS),
        "SUBSTRATE_T349.csv": csv_text(b["substrate"], SUB_COLS),
        "FILL_T349.csv": csv_text(b["fill"], FILL_COLS),
        "PENDING_T349.csv": csv_text(b["pending"], PEND_COLS),
        "NOT_APPLICABLE_T349.csv": csv_text(b["na"], ["line_id", "element_id", "why"]),
        "summary.json": json.dumps(b["summary"], indent=1, sort_keys=True, ensure_ascii=False) + "\n",
    }


def main(argv):
    out = outputs()
    if "--write" in argv:
        for k, v in out.items():
            (HERE / k).write_text(v, encoding="utf-8")
        print("written:", ", ".join(out))
    elif "--check" in argv:
        bad = [k for k, v in out.items() if not (HERE / k).exists() or (HERE / k).read_text(encoding="utf-8") != v]
        print("stale:", bad or "none")
        return 1 if bad else 0
    else:
        print(out["summary.json"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
