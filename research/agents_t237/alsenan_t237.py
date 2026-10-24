"""T-237 development villa (Alsenan): room face -> block wall crosswalk and cross-trade consistency, READ ONLY on the
merged ledgers (no drawing is opened; every input is a merged research CSV in this repository):

  plaster / paint   research/agents_t128/ROOMS_T128_R3.csv, OPENINGS_T128_R3.csv          (T-128 r3, MERGED a6ac2c66)
  opening hosts     research/agents_t175/T175_OPENING_HOSTS.csv                           (T-175, MERGED b903360c)
  opening heads     research/agents_t201/HEADS_T201.csv, agents_t207/CLOSURE_T207.csv,
                    agents_t238/DELTA_T238.csv                                            (MERGED 5dade783 / e081911c / 242e50b2)
  block walls       research/agents_t225/BLOCKWORK_WALL_REGISTER_V1.csv + agents_t226/register_delta.csv
                    + agents_t227/register_delta.csv                                      (MERGED 48e6f08a / a04f8e21 / ebce3d97)

Usage: python3 -I research/agents_t237/alsenan_t237.py [OUT_DIR]   (default: this folder)
Nothing here changes a merged ledger: the per-room change (part 4) is reported, lane I applies it.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RES = HERE.parent
sys.path.insert(0, str(HERE))
import face_consistency as F  # noqa: E402

SLAB_T = 0.16   # ST general note "all slabs 16 cm" (T-128 calc_r2.py SLAB; T-225 register slab pieces 't 0.16')

# T-128 room row -> the room names the merged opening ledgers (T-175 SIDE_A / SIDE_B) use for the same space
ALIAS = {
    "GF-01": ["dewaneya"], "GF-02": ["wash by the dewaneya"], "GF-03": ["W.C. by the dewaneya"],
    "GF-04": ["driver room"], "GF-05": ["driver W.C."], "GF-06": ["kitchen"], "GF-07": ["pantry (open room)"],
    "GF-08": ["dining / entrance (open room)", "saloon (open room)", "GF master bed room / pool court"],
    "GF-15": ["GF master bed room", "GF master bed room / pool court"], "GF-16": ["bath of the master bed room"],
    "GF-10": ["W.C. 175 x 135 by the stair"], "GF-11": ["basin space 110 x 135", "stair passage / basin space"],
    "GF-12": ["W.C. core wedge A"], "GF-13": ["W.C. core wedge B"], "GF-14": ["wash lobby"],
    "1F-01": ["1F master bed room west 425 x 450"], "1F-04": ["1F master bed room 500 x 365"],
    "1F-10": ["1F master bed room 380 x 430", "dressing passage of the 380 x 430 bed room", "dressing passage"],
    "1F-11": ["1F master bed room east (curved W17)", "1F master bed room east"],
    "1F-07": ["laundry"], "1F-08": ["W.C. 147 x 180"], "1F-02": ["bath west upper 245 x 205"],
    "1F-03": ["bath west lower 245 x 205"], "1F-12": ["bath east 210 x 225", "1F bath east 210 x 225"],
    "1F-09": ["bath by the laundry 200 x 180"],
    "1F-13": ["living / landing (open zone)", "living / corridor (open zone)", "1F living (open zone)",
              "living / landing", "stair landing (shaft side)"],
    "2F-03": ["maid room 300 x 645"], "2F-02": ["W.C. 300 x 185"], "2F-01": ["2F stair lobby"],
    "ST-GF": ["stair hall GF", "GF stair hall", "stair passage / basin space"],
    "ST-1F": ["1F stair hall", "1F stair hall (north)", "stair landing (shaft side)"],
    "ST-2F": ["2F stair hall", "2F stair hall (north)"],
}
# words in a T-128 opening name that name the room on its OTHER side (T-128 r3 walk labels)
HINT = [("stair hall", "ST-GF"), ("master bed", "GF-15"), ("wedge A", "GF-12"), ("wedge B", "GF-13"),
        ("laundry", "1F-07"), ("bed 380 x 430", "1F-10"), ("bed east", "1F-11"), ("bed 500 x 365", "1F-04"),
        ("bed west", "1F-01"), ("basin space", "GF-11"), ("maid", "2F-03"), ("to the open room", "GF-08")]
DOOR_BLOCK = {"d115": 1.00, "d120": 1.00, "d215": 0.90, "d220": 0.90, "d315": 0.80}   # frame = leaf + 0.11 (T-128 s.1)
VOID_ZONES = {"SHAFT"}       # faces rising through the stair void (no slab soffit at the face)
HEIGHT_CAUSES = {"annex datum (Q-54 B)", "beam depth / register conflict", "lift tie beam size (ST p.8 n.19)",
                 "no member drawn above", "no wall band or member bound (glazed line / held strip)"}
KIND = {"window": {"WINDOW"}, "door": {"DOOR"}, "main": {"DOOR"}, "lift": {"LIFT"},
        "arch": {"OPENING"}, "doorway": {"OPENING", "NOT IN THE T-150 CENSUS"}}


def fnum(s):
    try:
        return float(str(s).strip())
    except (TypeError, ValueError):
        return None


def rng(s):
    """'3.59 .. 3.69' -> (3.59, 3.69); '3.84' -> (3.84, 3.84); 'HELD' / '' -> (None, None)."""
    s = str(s or "").strip()
    if ".." in s:
        a, b = s.split("..")
        return fnum(a), fnum(b)
    v = fnum(s)
    return v, v


def read(p):
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load():
    rooms = read(RES / "agents_t128/ROOMS_T128_R3.csv")
    ops = read(RES / "agents_t128/OPENINGS_T128_R3.csv")
    hosts = {h["ID"]: h for h in read(RES / "agents_t175/T175_OPENING_HOSTS.csv")}
    reg = {r["wall_id"]: dict(r, _src="register v1") for r in read(RES / "agents_t225/BLOCKWORK_WALL_REGISTER_V1.csv")}
    for pkg in ("agents_t226", "agents_t227"):
        for r in read(RES / pkg / "register_delta.csv"):
            reg[r["wall_id"]] = dict(r, _src=f"register v1 + {r['package']} delta")
    return rooms, ops, hosts, reg


def merged_sizes(hosts):
    """Current merged opening size per census id for the FINISH deduction (w, sill / head above FFL, fixed m2 or a
    deduction bound for a HELD outline). Later merged ledgers override earlier ones: T-175 -> T-201 -> T-207 -> T-238."""
    m = {}
    for cid, h in hosts.items():
        w, hh, s = fnum(h["WIDTH_M"]), fnum(h["HEIGHT_M"]), fnum(h["SILL_ABOVE_FFL_M"])
        st = h["HEIGHT_STATUS_T150"] or "HELD"
        known = hh is not None and s is not None and st != "HELD"
        m[cid] = dict(w=w, sill=s if known else None, head=(s + hh) if known else None, h=hh if known else None,
                      status=st if known else "HELD", src="T-175 hosts")
    for r in read(RES / "agents_t201/HEADS_T201.csv"):
        if r["STATUS"] != "DRAWING-CONFIRMED":
            continue
        w, hh = fnum(r["WIDTH_M"]), fnum(r["HEIGHT_M"])
        s, hd = fnum(r["SILL_ABOVE_FFL_M"]), fnum(r["HEAD_ABOVE_FFL_M"])
        e = m.setdefault(r["ID"], {})
        if s is not None and hd is not None:
            e.update(w=w, sill=s, head=hd, h=hh, status="DRAWING-CONFIRMED", src="T-201 heads")
        else:                       # height known, sill / head not: the area is known, the band is not
            e.update(w=w, sill=None, head=None, h=hh, cap_m2=w * hh, status="HELD (sill)", src="T-201 heads (height only)")
    for r in read(RES / "agents_t207/CLOSURE_T207.csv"):
        if r["ID"] in ("W11", "W12") and r["AFTER_STATUS"] == "DRAWING-CONFIRMED":
            e = m[r["ID"]]
            e.update(h=2.20, sill=None, head=None, cap_m2=round(e["w"] * 2.20, 4), status="HELD (sill: datum not printed)",
                     src="T-207 closure (h 2.20 DRAWING-CONFIRMED; sill HELD)")
    for r in read(RES / "agents_t238/DELTA_T238.csv"):
        if r["item"] != "finish deduction" and not (r["opening"] == "W17" and r["item"] == "opening deduction"):
            continue
        e = m.setdefault(r["opening"], {})
        if r["opening"] == "W17":
            e.update(sill=None, head=None, cap_m2=10.024, status="HELD (T-238: archivolt, developed outline)",
                     src="T-238 delta (upper bound 10.024)")
        else:
            e.update(fixed_m2=fnum(r["new"]), status=r["new_status"], src="T-238 delta (arched outline)")
    return m


def match(ops, hosts):
    """T-128 opening face -> census id. Basis: explicit id in the T-128 name, else the room (alias), kind and width."""
    out = []
    for o in ops:
        rid, name, cls, w = o["ROOM_ROW"], o["OPENING"], o["CLASS"], fnum(o["WIDTH_M"])
        if cls in ("virtual", "wall"):
            out.append(dict(o, cid=None, basis=f"{cls}: no deduction", cands=""))
            continue
        names = set(ALIAS.get(rid, []))
        cand = [c for c, h in hosts.items() if (h["SIDE_A"] in names or h["SIDE_B"] in names)
                and h["KIND_T150"] in KIND.get(cls, set())]
        tok = name.split()[0]
        explicit = []
        if tok.startswith("W") and tok[1:3].isdigit():
            if "-" in tok:                        # 'W05-07', 'W19-23': a family; the room decides
                a, b = tok[1:].split("-")
                fam = {f"W{i:02d}" for i in range(int(a), int(b) + 1)}
                explicit = [c for c in cand if c in fam]
            else:
                explicit = [tok] if tok in hosts else []
        if name.startswith("D01"):
            explicit = ["D-GF-07"]
        if name.startswith("D26"):
            explicit = ["D-2F-01"]
        hint = [t for k, t in HINT if k in name and t != rid]
        if explicit:
            pick, basis = explicit, "id in the T-128 name" + (" + room" if "-" in tok else "")
        elif hint and cls in ("door", "doorway", "arch"):
            other = set(ALIAS.get(hint[0], []))
            pick = [c for c in cand if (hosts[c]["SIDE_A"] in other or hosts[c]["SIDE_B"] in other)]
            basis = f"room + kind + the other side named in the T-128 label ({hint[0]})"
            nominal = next((v for k, v in DOOR_BLOCK.items() if name.lower().startswith(k)), None)
            if not pick and nominal is not None:
                # a split face of a region the census does not name as a side: the hint room's door of this block
                fl = rid[:2] if rid[:2] in ("GF", "1F", "2F") else rid[3:]
                pick = [c for c, h in hosts.items() if h["FLOOR"] == fl and h["KIND_T150"] == "DOOR"
                        and (h["SIDE_A"] in other or h["SIDE_B"] in other)
                        and abs(fnum(h["WIDTH_M"]) - nominal) <= 0.01 and w < nominal - 0.06]
                basis = (f"door block {name.split()[0]} ({nominal:.2f}) of the room named in the label ({hint[0]}); "
                         "the census does not name this region as a side")
            if len(pick) > 1 and nominal is not None:
                pick = [c for c in pick if abs(fnum(hosts[c]["WIDTH_M"]) - nominal) <= 0.01] or pick
            if len(pick) == 1 and fnum(hosts[pick[0]]["WIDTH_M"]) - w > 0.06:
                basis += "; split face (part of the opening width)"
        else:
            pick = [c for c in cand if fnum(hosts[c]["WIDTH_M"]) is not None and abs(fnum(hosts[c]["WIDTH_M"]) - w) <= 0.06]
            basis = "room + kind + width (0.06)"
            if len(pick) > 1:
                best = min(abs(fnum(hosts[c]["WIDTH_M"]) - w) for c in pick)
                near = [c for c in pick if abs(abs(fnum(hosts[c]["WIDTH_M"]) - w) - best) < 1e-9]
                pick, basis = (near, basis + ", nearest width") if len(near) == 1 else (pick, basis)
            if not pick and cand and cls in ("door",):
                # a split face: part of a door seen from a second region (width smaller than the opening)
                part = [c for c in cand if fnum(hosts[c]["WIDTH_M"]) and w < fnum(hosts[c]["WIDTH_M"]) - 0.06]
                if len(part) == 1:
                    pick, basis = part, "room + kind; split face (part of the opening width)"
        cid = pick[0] if len(pick) == 1 else None
        if len(pick) > 1:
            basis = "AMBIGUOUS: " + basis
        if not pick:
            basis = "UNMATCHED: no census opening on this room's sides with this kind and width"
        out.append(dict(o, cid=cid, basis=basis, cands=";".join(sorted(pick))))
    return out


def resolve_ambiguous(rows, hosts):
    """Within one room, an ambiguous face takes the candidate no other face of the room took (one id per face)."""
    by_room = {}
    for r in rows:
        by_room.setdefault(r["ROOM_ROW"], []).append(r)
    for rid, rs in by_room.items():
        taken = {r["cid"] for r in rs if r["cid"]}
        for r in rs:
            if r["cid"] is None and r["basis"].startswith("AMBIGUOUS"):
                left = [c for c in r["cands"].split(";") if c not in taken]
                if len(left) == 1:
                    r["cid"] = left[0]; taken.add(left[0])
                    r["basis"] = r["basis"].replace("AMBIGUOUS: ", "") + ", the other candidate taken by a sibling face"
    # a window family label ('W05-07') with no family member on this room's census sides: the one member no other
    # room deducts (the room assignment then DIFFERS between the ledgers and is reported, never silently accepted)
    taken_all = {r["cid"] for r in rows if r["cid"]}
    for r in rows:
        tok = r["OPENING"].split()[0]
        if r["cid"] is None and tok.startswith("W") and "-" in tok and tok[1:3].isdigit():
            a, b = tok[1:].split("-")
            left = [f"W{i:02d}" for i in range(int(a), int(b) + 1) if f"W{i:02d}" in hosts and f"W{i:02d}" not in taken_all]
            if len(left) == 1:
                r["cid"] = left[0]; taken_all.add(left[0]); r["cands"] = left[0]
                r["basis"] = "family label: the one member no other room deducts (room assignment DIFFERS from T-175)"
    # doorless openings outside the T-150 census (T-198 P- rows carry no sides): candidates by floor and width only
    for r in rows:
        if r["cid"] is None and r["CLASS"] == "doorway":
            fl = r["ROOM_ROW"][:2] if r["ROOM_ROW"][:2] in ("GF", "1F", "2F") else r["ROOM_ROW"][3:]
            c = [k for k, h in hosts.items() if k.startswith("P-") and h["FLOOR"] == fl
                 and fnum(h["WIDTH_M"]) is not None and abs(fnum(h["WIDTH_M"]) - fnum(r["WIDTH_M"])) <= 0.06]
            r["cands"] = ";".join(c)
            r["basis"] = ("UNMATCHED: the census row has no sides; width-only candidate(s) " + (", ".join(c) or "none")
                          + " (not taken: width alone does not identify an opening)")
    return rows


def build(out_dir: Path):
    rooms, ops, hosts, reg = load()
    sizes = merged_sizes(hosts)
    rows = resolve_ambiguous(match(ops, hosts), hosts)
    R = {r["ROW"]: r for r in rooms}

    # ---------------------------------------------------------------- part 1 + 2: crosswalk and per-face checks
    faces = {}
    xw = []
    for r in rows:
        rid = r["ROW"] if "ROW" in r else r["ROOM_ROW"]
        room = R[r["ROOM_ROW"]]
        cid = r["cid"]
        wall = hosts[cid]["HOST_ROW"] if cid and cid in hosts else ""
        xw.append(dict(room=r["ROOM_ROW"], room_name=room["ROOM"], t128_opening=r["OPENING"], t128_class=r["CLASS"],
                       t128_width_m=r["WIDTH_M"], census_id=cid or "", match_basis=r["basis"], candidates=r["cands"],
                       host_wall=wall or ("" if cid else "-")))
        if wall:
            faces.setdefault((r["ROOM_ROW"], wall), []).append(dict(id=cid, w=fnum(r["WIDTH_M"]), t128=r["OPENING"]))

    face_rows, findings = [], []
    for (rid, wall), deds in sorted(faces.items()):
        room = R[rid]
        pl = fnum(room["DWG_PLASTER_H_TOP_M"])
        p_lo, p_hi = rng(room["DWG_PAINT_TILE_H_M"])
        wr = reg.get(wall)
        try:
            F.check_deductions(deds)
            ded_code = "ONE PER FACE"
        except F.ConsistencyRefused as e:
            ded_code = str(e)
            findings.append(dict(kind="DOUBLE_DEDUCTION", room=rid, wall=wall, detail=str(e)))
        if wr is None:
            hc = dict(code="WALL_NOT_IN_REGISTER", delta_m=None, band_m=None, residual_m=None,
                      storey_plaster_m=None, storey_block_m=None)
            bh = bcls = None; pieces = []
        else:
            # the register's gross is HELD for length / opening causes too; its HEIGHT is held only for a height cause
            height_held = wr["gross_class"].startswith("HELD") and wr["held_cause_class"] in HEIGHT_CAUSES
            bh = None if height_held else fnum(wr["height_weighted_m"])
            bcls = ("HELD (" + wr["held_cause_class"] + ")") if height_held else (
                "height established; gross / net " + wr["gross_class"] + (f" ({wr['held_cause_class']})" if wr["held_cause_class"] else ""))
            pieces = F.member_pieces(wr["evidence"])
            try:
                hc = F.height_check(pl, SLAB_T, bh, bcls, pieces, void=room["ZONE"] in VOID_ZONES)
            except F.ConsistencyRefused as e:
                hc = dict(code=str(e).split(":")[0], delta_m=None, band_m=None, residual_m=None,
                          storey_plaster_m=None, storey_block_m=None)
                findings.append(dict(kind=hc["code"], room=rid, wall=wall, detail=str(e)))
        dwg_status = room["DWG_GROSS_STATUS"] or room["DWG_STATUS"]
        held_pair = ""
        if wr is not None:
            b_held = bh is None
            p_held = pl is None or dwg_status.startswith("HELD")
            if b_held != p_held:
                if p_held and "roof datum" in dwg_status:
                    kind = "HEIGHT_DATUM_SPLIT_ROOF"
                    held_pair = (f"{kind}: the block register forms this face's height from the storey interval and the "
                                 f"members ({bh} m), the plaster ledger HOLDS the same storey interval on the roof "
                                 f"build-up (DCR-6); one datum, two answers")
                elif p_held:
                    kind = "HEIGHT_DATUM_SPLIT_LEVEL"
                    held_pair = (f"{kind}: block height {bh} m formed on the storey interval; plaster HELD "
                                 f"({dwg_status[:70]})")
                else:
                    kind = "BLOCK_HEIGHT_HELD_PLASTER_ESTABLISHED"
                    top = "the storey (stair void)" if room["ZONE"] in VOID_ZONES else "the slab soffit"
                    held_pair = (f"{kind}: block height HELD ({wr['held_cause_class']}); the plaster top {pl} m is "
                                 f"{top} and does not need the member, but the block / concrete-band split of the face "
                                 f"does: the band m2 (and the substrate split) stays HELD")
                findings.append(dict(kind=kind, room=rid, wall=wall, detail=held_pair))
            elif b_held:
                held_pair = "both HELD: " + (wr["held_cause_class"] or "") + " / " + dwg_status[:60]
        # a register height that rests on the annex storey (+4.30 - 0.30 = 4.00, Q-54 B / D-39) while the register names
        # another cause: the datum hold is masked by the single cause column
        if (bh is not None and hc.get("storey_block_m") is not None and abs(hc["storey_block_m"] - 4.00) <= F.TOL_M
                and "annex" not in (wr["held_cause_class"] or "")):
            findings.append(dict(kind="MASKED_DATUM_CAUSE", room=rid, wall=wall,
                                 detail=f"block height {bh} m = annex storey 4.00 - member: rests on the +4.30 annex datum "
                                        f"(Q-54 B HOLD, D-39) like GF-W00, but the register's cause is "
                                        f"'{wr['held_cause_class'] or wr['gross_class']}'; the height is not established"))
            face_masked = True
        else:
            face_masked = False
        if hc["code"] == "DATUM_RESIDUAL":
            findings.append(dict(kind="DATUM_RESIDUAL", room=rid, wall=wall,
                                 detail=f"plaster top {pl} vs block {bh}: delta {hc['delta_m']} m, members explain "
                                        f"{hc['band_m']} m, residual {hc['residual_m']} m (storey {hc['storey_plaster_m']} "
                                        f"from the plaster ledger vs {hc['storey_block_m']} from the block register)"))
        face_rows.append(dict(
            room=rid, room_name=room["ROOM"], wall_id=wall, register_source=(wr or {}).get("_src", "-"),
            plaster_top_m=pl if pl is not None else "HELD", paint_h_m=room["DWG_PAINT_TILE_H_M"] or "HELD",
            owner_h_m=room["OWNER_H_M"], block_h_m=bh if bh is not None else "HELD", block_gross_class=bcls or "-",
            members_over=("; ".join(f"d {d:.2f} x {L:.2f} m" for d, L, h in pieces) or "-"),
            height_code=hc["code"], delta_m=hc["delta_m"], band_explained_m=hc["band_m"], residual_m=hc["residual_m"],
            band_m2_per_m_face=hc["band_m"] if hc["band_m"] is not None else "",
            band_substrate=(("stair void: beam side + slab edge, full member depth (plastered concrete, not block)"
                             if room["ZONE"] in VOID_ZONES else "concrete beam side face below the slab (plastered, not block)")
                            if (hc["band_m"] or 0) > F.TOL_M else ""),
            status_pair=held_pair, openings_on_face=";".join(d["id"] for d in deds), deduction_check=ded_code))

    # rule (a) across faces
    width_of = {c: fnum(h["WIDTH_M"]) for c, h in hosts.items()}
    pop = F.check_id_population([(x["room"], x["host_wall"], x["census_id"], fnum(x["t128_width_m"])) for x in xw
                                 if x["census_id"]], width_of)
    for p in pop:
        findings.append(dict(kind=p["code"], room=",".join(p["rooms"]), wall=hosts[p["id"]]["HOST_ROW"],
                             detail=f"{p['id']}: split parts sum - census width = {p['d_w_m']} m"
                                    + (f" (= {p['d_w_m'] * (fnum(hosts[p['id']]['HEIGHT_M']) or 0):.3f} m2 at the "
                                       f"printed height)" if p["code"] == "SPLIT_FACE_SUM_DIFFERS" else "")))
    for x in xw:
        if x["census_id"] == "" and x["t128_class"] not in ("virtual", "wall"):
            findings.append(dict(kind="OPENING_NOT_CROSSWALKED", room=x["room"], wall="", detail=f"{x['t128_opening']}: {x['match_basis']}"))
    # room assignment: the census id's sides vs the room that deducts it
    for x in xw:
        cid = x["census_id"]
        if not cid:
            continue
        h = hosts[cid]
        if not ({h["SIDE_A"], h["SIDE_B"]} & set(ALIAS.get(x["room"], []))):
            findings.append(dict(kind=("REGION_NOT_A_CENSUS_SIDE" if "does not name this region" in x["match_basis"]
                                       else "ROOM_ASSIGNMENT_DIFFERS"), room=x["room"], wall=h["HOST_ROW"],
                                 detail=f"{cid}: T-128 deducts it in {x['room']} ({x['t128_opening']}); T-175 sides "
                                        f"'{h['SIDE_A']}' / '{h['SIDE_B']}'"))

    # ---------------------------------------------------------------- rule (d): sizes per ledger
    size_rows = []
    for r in rows:
        cid = r["cid"]
        if not cid:
            continue
        w128, s128, h128 = fnum(r["WIDTH_M"]), fnum(r["SILL_M"]), fnum(r["HEAD_M"])
        z = sizes.get(cid, {})
        hh128 = (h128 - s128) if (h128 is not None and s128 is not None) else None
        code, dw, dh, dm2 = F.size_check(cid, w128, hh128, z.get("w"), z.get("h"))
        whole_w = z.get("w")
        if code in ("WIDTH_DIFFERS", "SIZE_DIFFERS") and whole_w and w128 < whole_w - 3 * F.TOL_M:
            code = "SPLIT_FACE (part width)"      # the sum of the parts is checked across faces (rule (a))
        if z.get("fixed_m2") is not None and h128 is not None and s128 is not None:
            t128_m2 = w128 * (h128 - s128)
            code, dm2 = ("OUTLINE_DIFFERS (arched, T-238)" if abs(t128_m2 - z["fixed_m2"]) > F.TOL_M2 else code,
                         round(t128_m2 - z["fixed_m2"], 4))
        if z.get("status", "").startswith("HELD") and h128 is not None and z.get("fixed_m2") is None:
            code = "T-128 DEDUCTS A HEIGHT THE MERGED LEDGER HOLDS"
        size_rows.append(dict(room=r["ROOM_ROW"], t128_opening=r["OPENING"], census_id=cid,
                              t128_w=w128, t128_sill=s128 if s128 is not None else "HELD",
                              t128_head=h128 if h128 is not None else "HELD", merged_w=whole_w,
                              merged_sill=z.get("sill") if z.get("sill") is not None else "HELD",
                              merged_head=z.get("head") if z.get("head") is not None else "HELD",
                              merged_fixed_m2=z.get("fixed_m2", ""), merged_cap_m2=z.get("cap_m2", ""),
                              merged_status=z.get("status", "-"), merged_src=z.get("src", "-"),
                              code=code, d_w_m=dw, d_h_m=dh, d_m2_per_face=dm2))
        if code not in ("AGREES", "AGREES_WIDTH_HEIGHT_HELD", "WIDTH_HELD", "SPLIT_FACE (part width)"):
            if code == "WIDTH_DIFFERS" and abs(dw) <= 0.06 and r["CLASS"] == "door":
                code2 = "DOOR_WIDTH_FACE_RULE"
            else:
                code2 = code
            findings.append(dict(kind=code2, room=r["ROOM_ROW"], wall=hosts[cid]["HOST_ROW"],
                                 detail=f"{cid} ({r['OPENING']}): T-128 {w128} x {hh128} vs merged {whole_w} x {z.get('h')} "
                                        f"[{z.get('src')}]; d_w {dw}, d_m2 {dm2}"))

    # ---------------------------------------------------------------- part 3 + 4: per room old / new (not applied)
    room_rows = []
    by_room = {}
    for r in rows:
        by_room.setdefault(r["ROOM_ROW"], []).append(r)
    for room in rooms:
        rid = room["ROW"]
        face = fnum(room["FACE_M"])
        lo, hi = rng(room["DWG_PAINT_TILE_H_M"])
        ow = fnum(room["OWNER_H_M"])
        old_ops, new_ops = [], []
        for r in by_room.get(rid, []):
            if r["CLASS"] in ("virtual", "wall"):
                continue
            w = fnum(r["WIDTH_M"]); s = fnum(r["SILL_M"]); h = fnum(r["HEAD_M"])
            old_ops.append(dict(id=r["OPENING"], w=w, sill=s, head=h))
            z = sizes.get(r["cid"]) if r["cid"] else None
            if (z is not None and r["CLASS"] == "door" and z.get("w") and 0.005 < abs(z["w"] - w) <= 0.06
                    and "split" not in r["basis"]):
                new_ops.append(dict(id=r["cid"], w=z["w"], sill=s, head=h))   # rule (d): the census frame width
            elif z is None or r["CLASS"] in ("door", "main"):
                # doors keep their T-128 face (Q-55 C 2.20 head and the one-width rule); unmatched faces unchanged
                new_ops.append(dict(id=r["OPENING"], w=w, sill=s, head=h))
            elif z.get("fixed_m2") is not None:
                new_ops.append(dict(id=r["cid"], w=w, fixed_m2=z["fixed_m2"]))
            elif z.get("sill") is not None and z.get("head") is not None:
                new_ops.append(dict(id=r["cid"], w=w, sill=z["sill"], head=z["head"]))
            else:
                new_ops.append(dict(id=r["cid"], w=w, sill=None, head=None, cap_m2=z.get("cap_m2")))

        def nets(H_lo, H_hi, opl):
            if face is None or H_lo is None:
                return None, None, []
            g_lo, g_hi = face * H_lo, face * H_hi
            k_lo = k_hi = 0.0; held = []
            for o in opl:
                if o.get("fixed_m2") is not None:
                    k_lo += o["fixed_m2"]; k_hi += o["fixed_m2"]; continue
                d_lo = F.band_deduction(o["w"], o.get("sill"), o.get("head"), H_lo)
                d_hi = F.band_deduction(o["w"], o.get("sill"), o.get("head"), H_hi)
                if d_lo is None:
                    held.append(o["id"])
                    k_lo += min(o["w"] * H_lo, o["cap_m2"]) if o.get("cap_m2") is not None else o["w"] * H_lo
                else:
                    k_lo += d_lo; k_hi += d_hi
            return round(g_lo - k_lo, 2), round(g_hi - k_hi, 2), held

        o_old = nets(lo, hi, old_ops); o_new = nets(lo, hi, new_ops)
        w_old = nets(ow, ow, old_ops); w_new = nets(ow, ow, new_ops)
        # reproduction guard: the old drawing-derived net must equal T-128 r3's own DWG_NET_M2
        t_lo, t_hi = rng(room["DWG_NET_M2"])
        repro = ("-" if t_lo is None or o_old[0] is None else
                 ("REPRODUCED" if abs(o_old[0] - t_lo) <= 0.015 and abs(o_old[1] - t_hi) <= 0.015
                  else f"DIFFERS ({o_old[0]} .. {o_old[1]} vs T-128 {t_lo} .. {t_hi})"))
        missing = []
        if lo is None:
            missing.append("room level / height (T-128 HELD)")
        if "roof datum" in (room["DWG_GROSS_STATUS"] or ""):
            missing.append("roof structural slab top / build-up over the face (DCR-6"
                           + (", annex D-39)" if room["ZONE"] == "GF_ANNEX" else ")"))
        for h_ in o_new[2]:
            missing.append(f"{h_} head / sill")
        if room["OWNER_H_M"] == "HELD":
            missing.append("owner shaft height (Q-72)")
        def f2(t):
            return "HELD" if t[0] is None else (f"{t[0]:.2f}" if abs(t[1] - t[0]) < 0.005 else f"{t[0]:.2f} .. {t[1]:.2f}")
        room_rows.append(dict(
            room=rid, room_name=room["ROOM"], face_m=face, dwg_paint_h=room["DWG_PAINT_TILE_H_M"],
            dwg_net_old_m2=f2(o_old), dwg_net_new_m2=f2(o_new),
            dwg_d_lo_m2=(round(o_new[0] - o_old[0], 2) if o_old[0] is not None else ""),
            dwg_d_hi_m2=(round(o_new[1] - o_old[1], 2) if o_old[0] is not None else ""),
            owner_h=room["OWNER_H_M"], owner_net_old_m2=f2(w_old), owner_net_new_m2=f2(w_new),
            owner_d_lo_m2=(round(w_new[0] - w_old[0], 2) if w_old[0] is not None else ""),
            owner_d_hi_m2=(round(w_new[1] - w_old[1], 2) if w_old[0] is not None else ""),
            held_old=";".join(o_old[2]), held_new=";".join(o_new[2]),
            reproduction=repro, room_status=("HELD" if (lo is None or "HELD" in (room["DWG_GROSS_STATUS"] or "")
                                                         or o_new[2]) else "SOURCE-SUPPORTED (not VERIFIED)"),
            missing_items="; ".join(missing) or "none",
            walls_crosswalked=";".join(sorted({w for (rr, w) in faces if rr == rid})) or "NONE (no opening hosted)"))

    out_dir.mkdir(parents=True, exist_ok=True)

    def wcsv(name, rs):
        with open(out_dir / name, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rs[0].keys()), lineterminator="\n")
            w.writeheader(); w.writerows(rs)
    wcsv("CROSSWALK_T237.csv", xw)
    wcsv("FACES_T237.csv", face_rows)
    wcsv("OPENING_SIZES_T237.csv", size_rows)
    wcsv("ROOMS_T237.csv", room_rows)
    wcsv("FINDINGS_T237.csv", findings)
    kinds = {}
    for f_ in findings:
        kinds[f_["kind"]] = kinds.get(f_["kind"], 0) + 1
    def tot(key):
        return round(sum(float(r[key]) for r in room_rows if r[key] != ""), 2)
    summ = dict(
        rooms=len(room_rows), rooms_with_a_crosswalked_wall=sum(1 for r in room_rows if not r["walls_crosswalked"].startswith("NONE")),
        opening_faces=sum(1 for x in xw if x["t128_class"] not in ("virtual", "wall")),
        opening_faces_crosswalked=sum(1 for x in xw if x["census_id"]), faces=len(face_rows),
        height_codes={c: sum(1 for r in face_rows if r["height_code"] == c) for c in sorted({r["height_code"] for r in face_rows})},
        findings=kinds, reproduced_rooms=sum(1 for r in room_rows if r["reproduction"] == "REPRODUCED"),
        dwg_net_change_m2=dict(lo=tot("dwg_d_lo_m2"), hi=tot("dwg_d_hi_m2")),
        owner_net_change_m2=dict(lo=tot("owner_d_lo_m2"), hi=tot("owner_d_hi_m2")),
        held_openings_old=sum(len(r["held_old"].split(";")) for r in room_rows if r["held_old"]),
        held_openings_new=sum(len(r["held_new"].split(";")) for r in room_rows if r["held_new"]),
        applied_to_merged_ledgers=False)
    (out_dir / "summary.json").write_text(json.dumps(summ, indent=1) + "\n", encoding="utf-8")
    return summ, dict(xw=xw, faces=face_rows, sizes=size_rows, rooms=room_rows, findings=findings)


if __name__ == "__main__":
    s, _ = build(Path(sys.argv[1]) if len(sys.argv) > 1 else HERE)
    print(json.dumps(s, indent=1))
