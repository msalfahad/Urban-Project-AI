"""T-756 exterior render / paint face ledger re-based onto ARCH_TAKEOFF_V3.0.77 (research; nothing wired).

Inputs (committed, merged, sha-pinned below; no private input needed): T-305 face / opening ledgers, T-311 component
owners, the T-314 r2 stage faces (T-747 extract) and stage line ids (T-737 rows), T-747 face paint, T-751 bounds,
T-754 residuals, the V3.0.73 .. V3.0.77 line indexes.
Writes out/T756_*.csv and out/T756_SUMMARY.json.

    python -I research/agents_t756/t756_alsenan.py            # build
    python -I research/agents_t756/t756_alsenan.py --check    # rebuild and compare with the committed outputs
    python -I research/agents_t756/t756_alsenan.py --recheck <LINE_INDEX_V3_0_78.json>   # step E after T-738 merges
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import t756_rules as R  # noqa: E402

T305F = "research/agents_t305/FACE_LINE_LEDGER_T305.csv"
T305O = "research/agents_t305/OPENING_HOLES_T305.csv"
T311C = "research/agents_t311/COMPONENT_OWNER_T311.csv"
STAGE = "research/agents_t747/in/T314_FACES_T747.json"
T747F = "research/agents_t747/out/T747_FACES.csv"
T737R = "research/agents_t737/out/T737_ROWS.csv"
T737S = "research/agents_t737/in/T314_STAGE_T737.json"
T751 = "research/agents_t751/out/T751_EDGE_BOUNDS.json"
T754 = "research/agents_t754/out/T754_EDGE_RESIDUALS.json"
IDX77 = "research/agents_t749/out/LINE_INDEX_V3_0_77.json"
LEDGER77 = "research/agents_t749/out/V3_0_77_INTEGRATION_LEDGER.csv"
OLDER = {"V3.0.73": "research/agents_t722/out/LINE_INDEX_V3_0_73.json",
         "V3.0.74": "research/agents_t717/out/LINE_INDEX_V3_0_74.json",
         "V3.0.75": "research/agents_t729/out/LINE_INDEX_V3_0_75.json",
         "V3.0.76": "research/agents_t736/out/LINE_INDEX_V3_0_76.json"}
PINS = [T305F, T305O, T311C, STAGE, T747F, T737R, T737S, T751, T754, IDX77, LEDGER77] + list(OLDER.values())
OUT = HERE / "out"
SCHEMA = "URBAN_T756_FACE_LEDGER_REBASE_V1"
FREELANCER_SIGMA = Decimal("1469.9675")   # his Sigma net m2 (T-567 / T-747 like for like; workbook not copied)

# T-305 rows whose stage figure differs from T-305, by named merged record (asserted: any other difference stops)
T305_CAUSES = {
    "1F/NW-2/PARAPET/parapet": ("T-348 r2 (merged): above +9.70 the parapet runs straight at the screen front; "
                                "re-measured on the chord 3.059412 x 1.30 = 3.977236 (T-305 4.5853 on the arc)"),
    "1F/NW-2/SLAB_EDGE_BELOW/slab_edge": ("T-348 r2 (merged): void ring landward arc 2.675 m x depth 0.20 .. 0.75 "
                                          "HELD bounded = 0.535 .. 2.00625 (T-305: no area, depth not printed)"),
}
NOT_A_FACE = {
    "1F/NW-1/SLAB_EDGE_BELOW/slab_edge": "T-348 (merged) / T-754: the pier stands on the GF roof band running 1.50 m seaward",
    "1F/NW-3/SLAB_EDGE_BELOW/slab_edge": "T-348 (merged) / T-754: the pier stands on the GF roof band running 1.50 m seaward",
}
# stage faces with no T-305 row: the merged record that created each (T-314 r2 stage inputs)
STAGE_ADDED = {
    "GF/NE-6x/EDGE/parapet": "T-324 C5 (merged): annex divider run NE-6x on the boundary line AC7, outer face owner HELD 0 .. 0.60 (Q-65 C)",
    "1F/NW-2/SCREEN-FRONT/storey": "T-348 r2 (merged): screen front storey band, NEW face",
    "1F/NW-2/SCREEN-BACK/storey": "T-348 r2 (merged): screen back storey band, NEW face",
    "1F/NW-2/SCREEN-MOULDING-STEPS/storey": "T-348 r2 (merged): three arched step returns 0 .. 1.776291 HELD (no Urban rule for 0.05 / 0.10 m returns)",
    "1F/NW-1/CORNER-ARC/storey": "T-348 r2 (merged): pier NW-1 corner arc beyond the ring key, +0.170245 m",
    "1F/NW-1/CORNER-ARC/parapet": "T-348 r2 (merged): pier NW-1 corner arc beyond the ring key, parapet band",
    "1F/NW-3/SW-RETURN/storey": "T-348 r2 (merged): pier NW-3 SW end return (1F plan CA2)",
    "1F/NW-3/SW-RETURN/parapet": "T-348 r2 (merged): pier NW-3 SW end return, parapet band (2F plan 1311)",
    "GF/AT225/RING-INNER/slab_edge": "T-348 r2 (merged): void ring inner face, depth not printed, HELD bounded",
    "GF/POOL-COURT-FRONT/slab_edge": "T-348 r2 (merged): pool-court front slab edge +5.30 -> +5.50 (trade open, Q-65 C)",
    "1F/NW-5/SW-PIER-RETURNS/storey": "T-567 (merged): NW-5 SW pier returns 0.536522 x 4.20",
    "1F/NW-5/SW-PIER-RETURNS/parapet": "T-567 (merged) + T-751 closure 0.697479 (pier top 27CA +11.00)",
    "PARAPET_INNER/ANNEX": "T-311 / T-324 (merged): parapet inner face above the upturn, split height D-39 HELD",
    "PARAPET_INNER/GF": "T-311 / T-324 (merged): parapet inner face above the upturn, split height D-39 HELD",
    "PARAPET_INNER/1F": "T-311 / T-324 (merged): parapet inner face above the upturn, split height D-39 HELD",
    "PARAPET_INNER/2F": "T-311 / T-324 (merged): parapet inner face above the upturn, split height D-39 HELD",
    "PARAPET_TOP/ANNEX": "T-311 / T-324 D bands (merged): parapet top width",
    "PARAPET_TOP/GF": "T-311 / T-324 D bands (merged): parapet top width",
    "PARAPET_TOP/1F": "T-311 / T-324 D bands (merged): parapet top width",
    "PARAPET_TOP/2F": "T-311 / T-324 D bands (merged): parapet top width",
}
# T-311 component -> V3.0.77 binding
ROOF = {"ANNEX": "ANNEX_ROOF", "GF": "GF_TERRACE", "1F": "1F_ROOF", "2F": "2F_ROOF"}
STAGE_ROOF = {"ANNEX": "ANNEX +4.30", "GF": "GF +5.50", "1F": "1F +9.70", "2F": "2F +13.90"}
REBAR_PARKED = "owner decision 2026-11-11 15:30 (board): rebar parked, no new rebar rows (Q-81 deferred)"
TOP_ARRIS_MISSING = ("horizontal arrises: T-337 FIN.EXT.CORNERS 710.171878 .. 821.858800 m.l (stage missing item; "
                     "T-749: not restated); no line in V3.0.77")
SE1_SLAB = ("T-754 (merged): 2.300000 m over the porch mouth is ONE_PLANE (no horizontal between the mouth piece top "
            "+4.70 (2232) and +5.60): 0 slab-edge arris; its band 2.30 x 0.80 = 1.840 m2 belongs to no stage face yet "
            "(bind against GF/SE-2 and T-360 C-1 before valuing); the other 1.800000 m lies behind the annex: HELD "
            "blank -> the face stays blank")


def sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def jload(p):
    return json.loads((ROOT / p).read_text())


def rows(p):
    with open(ROOT / p, newline="") as f:
        return list(csv.DictReader(f))


def D(x):
    return R.D(x)


def s6(x):
    return R.s6(x)


def stage_lines():
    """stage key -> {'line_id', 'element_id', 'after', 'floor'} from the T-737 pin of the T-314 r2 stage."""
    out = {}
    for r in rows(T737R):
        if r["kind"] == "STAGE_LINE":
            out[r["id"]] = {"line_id": r["line"], "element_id": r["element_id"], "after": r["stage_after"],
                            "floor": r["floor"], "action": r["stage_action"]}
    return out


def ref_for_key(key, sl, by_id):
    s = sl[key]
    if s["action"] == "CHANGE":
        return {"kind": "LINE", "line_id": s["line_id"], "item_code": "FIN.EXT.FINISH",
                "element_id": s["element_id"], "unit": "m2"}
    return {"kind": "NEW", "line_id": s["line_id"], "element_id": s["element_id"]}


def build():
    idx = jload(IDX77)
    assert idx["candidate_version"] == "ARCH_TAKEOFF_V3.0.77"
    maps = R.index_maps(idx["lines"])
    by_id = maps[0]
    sl = stage_lines()
    assert len(sl) == 18
    st = jload(STAGE)
    faces = {f["face_id"]: f for f in st["faces"]}
    assert len(faces) == 126

    # ---- (A1) T-305 face rows -> stage faces -> V3.0.77 -------------------------------------------------------
    t305 = rows(T305F)
    assert len(t305) == 98
    tkeys = {"%s/%s/%s/%s" % (r["floor"], r["side"], r["portion"], r["band"]) for r in t305}
    face_rows, rb_in, used = [], [], {}
    for r in t305:
        pre = "%s/%s/%s/" % (r["floor"], r["side"], r["portion"])
        key = pre + r["band"]
        b, t = D(r["bottom_m"]), D(r["top_m"])
        m = []
        for fid, f in faces.items():
            if not fid.startswith(pre):
                continue
            if fid == key:
                m.append(f)
            elif fid not in tkeys and None not in (b, t, f["bottom"], f["top"]) \
                    and D(f["bottom"]) >= b and D(f["top"]) <= t:
                m.append(f)          # a T-305 band the stage split at a printed level (storey | parapet)
        g = D(r["geometric_m2"])
        rlo = g if g is not None else D(r["held_lo_m2"])
        rhi = g if g is not None else D(r["held_hi_m2"])
        own = R.rebase("t305-own:" + key, {"kind": "LINE", "line_id": r["finish_line_id"], "item_code": "FIN.EXT.FINISH",
                                           "unit": "m2"} if r["finish_line_id"] else {"kind": "NONE"}, maps)
        geo = R.rebase("t305-geo:" + key, {"kind": "LINE", "line_id": r["geometry_line_id"], "unit": "m2"}
                       if r["geometry_line_id"] else {"kind": "NONE"}, maps)
        if key in NOT_A_FACE:
            assert not m
            rb_in.append(("t305:" + key, {"kind": "NOT_A_FACE", "cite": NOT_A_FACE[key]}))
            face_rows.append({"t305_key": key, "t305_state": r["ledger_state"], "t305_m2": "", "stage_face": "",
                              "stage_line_key": "", "stage_m2": "", "residual_m2": "", "cause": NOT_A_FACE[key],
                              "t305_own_line": (f"{r['finish_line_id']} {own['state']}" if r["finish_line_id"] else "NO_LINE (T-305)"),
                              "t305_geometry_line": (f"{r['geometry_line_id']} {geo['state']}" if r["geometry_line_id"] else "NO_LINE (T-305)")})
            continue
        assert m, key
        slo = sum((D(f["lo"]) for f in m if f["lo"] is not None), Decimal(0))
        shi = sum((D(f["hi"]) for f in m if f["hi"] is not None), Decimal(0))
        blank = any(f["lo"] is None for f in m)
        if blank or rlo is None:
            res, cause = "", ("T-305 no area (depth not printed); stage face HELD" if rlo is None else "")
            if key in T305_CAUSES:
                cause = T305_CAUSES[key]
            elif blank and rlo is None:
                cause = "T-305 no area; stage face HELD blank (never 0)"
        else:
            dl, dh = slo - rlo, shi - rhi
            res = f"{s6(dl)} .. {s6(dh)}"
            cause = ""
            if dl != 0 or dh != 0:
                assert key in T305_CAUSES, (key, dl, dh)
                cause = T305_CAUSES[key]
        for f in m:
            used.setdefault(f["face_id"], []).append(key)
            rid = f"t305:{key}|{f['face_id']}"
            rb_in.append((rid, ref_for_key(f["line"], sl, by_id)))
            face_rows.append({"t305_key": key, "t305_state": r["ledger_state"],
                              "t305_m2": "" if rlo is None else f"{s6(rlo)} .. {s6(rhi)}",
                              "stage_face": f["face_id"], "stage_line_key": f["line"],
                              "stage_m2": "" if f["lo"] is None else f"{s6(f['lo'])} .. {s6(f['hi'])}",
                              "residual_m2": res, "cause": cause,
                              "t305_own_line": (f"{r['finish_line_id']} {own['state']}" if r["finish_line_id"] else "NO_LINE (T-305)"),
                              "t305_geometry_line": (f"{r['geometry_line_id']} {geo['state']}" if r["geometry_line_id"] else "NO_LINE (T-305)")})
    assert all(len(v) == 1 for v in used.values()), "a stage face claimed by two T-305 rows"
    added = sorted(set(faces) - set(used))
    assert set(added) == set(STAGE_ADDED), set(added) ^ set(STAGE_ADDED)
    for fid in added:
        f = faces[fid]
        rb_in.append(("stage:" + fid, ref_for_key(f["line"], sl, by_id)))
        face_rows.append({"t305_key": "", "t305_state": "", "t305_m2": "", "stage_face": fid,
                          "stage_line_key": f["line"],
                          "stage_m2": "" if f["lo"] is None else f"{s6(f['lo'])} .. {s6(f['hi'])}",
                          "residual_m2": "", "cause": "STAGE_ADDED: " + STAGE_ADDED[fid],
                          "t305_own_line": "", "t305_geometry_line": ""})
    rb = R.rebase_all(rb_in, maps)
    for fr, x in zip(face_rows, rb):
        fr["v3077_line_id"], fr["v3077_state"] = x["line_id"], x["state"]

    # ---- (A2) T-311 components ------------------------------------------------------------------------------
    comp_rows = []
    lines77 = idx["lines"]
    for c in rows(T311C):
        name, trade = c["component"], c["trade"]
        part = name.split(" ")[0]
        refs = []
        if trade == "CONCRETE" and part in ROOF:
            el = f"{ROOF[part]}#PARAPET_RC"
            refs = [{"kind": "LINE", "line_id": by_el, "item_code": "STR.CONC.PARAPET", "element_id": el, "unit": "m3"}
                    for by_el in maps[1].get(el, [])] or [{"kind": "NONE", "cite": f"no {el} line"}]
        elif trade == "FORMWORK" and part in ROOF:
            pre = f"FW:FACE:T332-PARAPET-{part}-"
            refs = [{"kind": "LINE", "line_id": l["line_id"], "item_code": "STR.FORMWORK",
                     "element_id": l["element_id"], "unit": "m2"}
                    for l in sorted(lines77, key=lambda l: l["element_id"]) if l["element_id"].startswith(pre)]
        elif trade == "BLOCKWORK" and part in ROOF:
            n = sum(1 for l in lines77 if l["item_code"].startswith("MAS.") and "PARAPET" in l["element_id"].upper())
            assert n == 0
            refs = [{"kind": "NONE", "cite": "no MAS.* line carries a parapet run (V3.0.77 element census: 0; "
                                             "T-311 R-T311-2); masonry part 0 .. solid HELD (Q-65 C / D-39)"}]
        elif trade == "REBAR":
            refs = [{"kind": "PARKED", "cite": REBAR_PARKED}]
        elif trade == "PLASTER_EXT" and part in ROOF:
            refs = [ref_for_key(f"NEW FIN.EXT.FINISH PARAPET-OUTER {STAGE_ROOF[part]}", sl, by_id)]
        elif trade == "PLASTER_PARAPET_INNER":
            refs = [ref_for_key(f"NEW FIN.EXT.PARAPET-INNER {STAGE_ROOF[part]}", sl, by_id)]
        elif trade == "COPING_TOP":
            refs = [ref_for_key(f"NEW FIN.EXT.PARAPET-TOP {STAGE_ROOF[part]}", sl, by_id)]
        elif trade == "CORNERS":
            refs = [{"kind": "NONE", "cite": TOP_ARRIS_MISSING}]
        elif trade == "WATERPROOFING":
            refs = [{"kind": "LINE", "line_id": c["candidate_line"], "unit": "lm"}]
        elif trade == "PLASTER_EXT" and part == "plinth":
            refs = [ref_for_key("NEW FIN.EXT.FINISH PLINTH GF", sl, by_id)]
        elif trade == "PLASTER_EXT" and part == "annex-roof":
            f = faces["1F/SE-1/OVER_LOWER_ROOF/over_lower_roof"]
            refs = [ref_for_key(f["line"], sl, by_id)]
        elif trade == "CONCRETE" and part == "plinth" and c["candidate_line"].startswith("OTHER_LINE"):
            n = sum(1 for l in lines77 if l["item_code"] == "STR.CONC.GROUND_BEAM")
            refs = [{"kind": "OTHER_TRADE", "cite": f"substrate face of STR.CONC.GROUND_BEAM ({n} lines in V3.0.77; "
                                                    f"T-311 counted 59): not a finish line"}]
        elif trade == "BLOCKWORK" and part == "plinth":
            refs = [{"kind": "LINE", "line_id": c["candidate_line"], "item_code": "MAS.BLOCK", "unit": "m2"}]
        elif trade == "CONCRETE" and part == "plinth":
            refs = [{"kind": "NONE", "cite": "passage substrate split HELD (T-311): no quantity, no line"}]
        else:
            raise AssertionError(f"unmapped T-311 component {name}")
        old = R.rebase("t311-own:" + name, {"kind": "LINE", "line_id": c["candidate_line"]}
                       if c["candidate_line"].startswith("L-") else {"kind": "NONE"}, maps)
        assert refs, name
        for i, ref in enumerate(refs):
            x = R.rebase(f"t311:{name}#{i}", ref, maps)
            comp_rows.append({"component": name, "trade": trade, "t311_line": c["candidate_line"],
                              "t311_line_state": old["state"] if c["candidate_line"].startswith("L-") else "",
                              "qty": f"{c['qty_lo']} .. {c['qty_hi']}".strip(" ."), "unit": c["unit"],
                              "v3077_line_id": x["line_id"], "v3077_state": x["state"], "why": x["why"]})

    # ---- (A3) T-305 openings -> stage hole face -> line; their exterior edge line ------------------------------
    open_rows = []
    so = {}
    for o in st["openings"]:
        so.setdefault(o["opening_id"], []).append(o)
    for r in rows(T305O):
        oid = r["opening"].split(" ")[0]
        side = r["side"]
        if oid == "none":
            open_rows.append({"opening": r["opening"], "face": f"{r['floor']}/{side}", "stage_line_key": "",
                              "v3077_line_id": "", "v3077_state": "NOT_A_FACE", "edge_line_id": "", "edge_state": "",
                              "why": "T-109 WALL_END_GAP drafting gap (T-305): not an opening"})
            continue
        cand = [o for o in so.get(r["opening"], []) if o["face_id"].startswith(f"{r['floor']}/{side}/")]
        assert len(cand) == 1, (oid, side)
        f = faces[cand[0]["face_id"]]
        x = R.rebase(f"t305-open:{r['opening']}", ref_for_key(f["line"], sl, by_id), maps)
        if oid.startswith("W"):
            el = f"{r['floor']}-FACADE:PAINT_EDGE:{oid}"
            ids = maps[1].get(el, [])
            assert len(ids) == 1, el
            e = R.rebase(f"edge:{r['opening']}", {"kind": "LINE", "line_id": ids[0], "item_code": "FIN.EXT.PAINT.EDGE",
                                                  "element_id": el, "unit": "lm"}, maps)
            why = "window outside edge (T-747 / T-751), FIN.EXT.PAINT.EDGE"
        else:
            el = f"{r['floor']}-OPENING-{r['engine_ref']}:door jambs and head:PAINT_EDGE"
            ids = maps[1].get(el, [])
            assert len(ids) == 1, el
            e = R.rebase(f"edge:{r['opening']}", {"kind": "LINE", "line_id": ids[0], "item_code": "FIN.PAINT.EDGE",
                                                  "element_id": el, "unit": "lm"}, maps)
            why = "exterior door reveal = its return edge, counted once under FIN.PAINT.EDGE (T-749 F-T749-1)"
        open_rows.append({"opening": r["opening"], "face": cand[0]["face_id"], "stage_line_key": f["line"],
                          "v3077_line_id": x["line_id"], "v3077_state": x["state"], "edge_line_id": e["line_id"],
                          "edge_state": e["state"], "why": why})
    assert len(open_rows) == len(rows(T305O)) == 39

    # ---- (B) T-754 deltas on the FIN.EXT.PAINT.EDGE lines -------------------------------------------------------
    t754 = jload(T754)
    led = {r["line_id"]: r for r in rows(LEDGER77) if r["item_code"] == "FIN.EXT.PAINT.EDGE"}
    edge = [l for l in lines77 if l["item_code"] == "FIN.EXT.PAINT.EDGE"]
    assert len(edge) == len(led) == 38
    vals = {l["line_id"]: (l["held_low"], l["held_high"]) for l in edge if l["held_low"] is not None}
    el_of = {l["element_id"]: l["line_id"] for l in edge}
    pe = el_of["1F-FACADE:CORNER_EDGE:PARAPET-OUTER_1F_9.70"]
    nh = el_of["GF-FACADE:CORNER_EDGE:PASSAGE_MOUTH_NO_HOST"]
    assert s6(vals[pe][0]) == "9.185812"
    after_pe = D(t754["corners"]["parapet_ends_after"])
    nac = t754["corners"]["not_a_corner_lm"]
    deltas = [{"line_id": pe, "before": vals[pe], "after": (after_pe, after_pe)}]
    after = R.apply_deltas(vals, deltas, (-D(nac[0]), -D(nac[1])))
    assert t754["no_host"]["host_line"] == led[nh]["beside"].split()[-1] == "L-b05f70c92405dbcfbe62"
    corner_ids = [l["line_id"] for l in edge if ":CORNER_EDGE:" in l["element_id"]]
    win_ids = [l["line_id"] for l in edge if ":PAINT_EDGE:" in l["element_id"]]
    cb = [sum((D(vals[i][k]) for i in corner_ids), Decimal(0)) for k in (0, 1)]
    ca = [sum((D(after[i][k]) for i in corner_ids), Decimal(0)) for k in (0, 1)]
    assert [s6(x) for x in cb] == t754["corners"]["before_physical"]
    assert [s6(x) for x in ca] == t754["corners"]["after_physical"] == t754["corners"]["after_hosted"]
    wsum = sum((D(vals[i][0]) for i in win_ids if i in vals), Decimal(0))
    assert s6(wsum) == jload(T751)["windows"]["after_lm"]
    # host after r3: by the face key the corner line names; windows by their hole face's stage line
    key_host = {"PARAPET-OUTER_ANNEX_4.30": "NEW FIN.EXT.FINISH PARAPET-OUTER ANNEX +4.30",
                "PARAPET-OUTER_GF_5.50": "NEW FIN.EXT.FINISH PARAPET-OUTER GF +5.50",
                "PARAPET-OUTER_1F_9.70": "NEW FIN.EXT.FINISH PARAPET-OUTER 1F +9.70",
                "PARAPET-OUTER_2F_13.90": "NEW FIN.EXT.FINISH PARAPET-OUTER 2F +13.90",
                "PLINTH_GF": "NEW FIN.EXT.FINISH PLINTH GF"}
    win_face = {}
    for o in st["openings"]:
        win_face.setdefault(o["opening_id"], set()).add(faces[o["face_id"]]["line"])
    edge_rows = []
    for l in sorted(edge, key=lambda l: l["element_id"]):
        i = l["line_id"]
        tail = l["element_id"].split(":")[-1]
        host_now = led[i]["beside"].split()[-1]
        if ":CORNER_EDGE:" in l["element_id"]:
            hk = key_host.get(tail)
            host_after = sl[hk]["line_id"] if hk else host_now
        else:
            ks = win_face[tail]
            assert len(ks) == 1, tail
            host_after = sl[ks.pop()]["line_id"]
        b = vals.get(i)
        a = after.get(i)
        note = ""
        if i == pe:
            note = ("T-754 F-T754-1: NW-1/NW-2 and NW-2/NW-3 above +9.70 NOT_A_CORNER (top line 27CB projected "
                    "4.807698 = 0.578 + 3.059412 + 1.170294, no vertical in the band): -2.60")
        elif i == nh:
            note = ("T-754: HOSTED on faces GF/P-1 + GF/P-2 (+4.80 .. +5.50; both on L-b05f70c9): quantity unchanged, "
                    "the NO_HOST label is a re-binding (element id rename = a next version, not here)")
        elif tail == "PARAPET-OUTER_GF_5.50":
            note = "stop-end 0 .. 1.20 HELD (T-754: free vs abutting end on no vector view)"
        elif b is None:
            note = "HELD blank (opening size / developed outline not established): never 0"
        edge_rows.append({"line_id": i, "element_id": l["element_id"], "before": "" if b is None else f"{s6(b[0])} .. {s6(b[1])}",
                          "after": "" if a is None else f"{s6(a[0])} .. {s6(a[1])}",
                          "delta": "" if b is None else f"{s6(D(a[0]) - D(b[0]))} .. {s6(D(a[1]) - D(b[1]))}",
                          "host_now": host_now, "host_after_r3": host_after, "note": note})

    # ---- (C) per face render = paint ---------------------------------------------------------------------------
    t751 = jload(T751)
    chg = {c["face_id"]: c for c in t751["paint"]["face_changes"]}
    seg = {c["face"]: c for c in t754["slab_edge_1f"]} if isinstance(t754["slab_edge_1f"], list) else {}
    paint_rows, per_line = [], {}
    for r in rows(T747F):
        fid = r["face_id"]
        lo, hi = (r["render_lo"] or None), (r["render_hi"] or None)
        if fid in chg:
            assert [s6(lo), s6(hi)] == chg[fid]["render"]
            lo, hi = chg[fid]["render_after"]
        res = R.face_paint(fid, lo, hi, printed=False)
        if fid in chg:
            assert res["paint"] == chg[fid]["paint_after"], fid
        side = fid.split("/")[1]
        cause = ""
        if res["paint"] is None:
            cause = SE1_SLAB if side == "SE-1" else seg.get(side, {}).get("cause", "HELD blank")
        elif fid in chg:
            cause = "T-751: " + chg[fid]["what"]
        paint_rows.append({"face_id": fid, "line_key": r["line_key"], "line_id": sl[r["line_key"]]["line_id"],
                           "element": r["element"], "holes": r["holes"],
                           "render": "" if res["render"] is None else " .. ".join(res["render"]),
                           "paint": "" if res["paint"] is None else " .. ".join(res["paint"]),
                           "state": res["state"], "cause": cause})
        per_line.setdefault(r["line_key"], []).append(res)
    assert len(paint_rows) == 126
    blanks = [p["face_id"] for p in paint_rows if not p["paint"]]
    assert blanks == t751["paint"]["blank_faces"]
    tot = [Decimal(0)] * 4
    for p in paint_rows:
        if p["paint"]:
            a, b = (D(x) for x in p["render"].split(" .. "))
            c, d = (D(x) for x in p["paint"].split(" .. "))
            tot = [tot[0] + a, tot[1] + b, tot[2] + c, tot[3] + d]
    assert [s6(tot[2]), s6(tot[3])] == t751["paint"]["total_after"]["paint"] == t754["paint"]["after"]
    assert tot[0] == tot[2] and tot[1] == tot[3]

    # ---- (D) ready-to-wire table -------------------------------------------------------------------------------
    stage_ev = {r["line_key"]: r["evidence_status"] for r in jload(T737S)["rows"]}
    assert set(stage_ev) == set(sl)
    wire = []
    for key in sorted(sl, key=lambda k: (sl[k]["floor"], k)):
        s = sl[key]
        lt = R.line_total(per_line[key])
        x = R.rebase("wire:" + key, ref_for_key(key, sl, by_id), maps)
        st_tok = s["after"].split()[0] if s["after"] else ""
        ev = stage_ev[key]
        if lt["render"] is None or lt["render"][0] != lt["render"][1]:
            assert ev == "HELD", (key, ev)
        elif st_tok == "PROVISIONAL":
            assert ev.startswith("ASSUMED")
            ev += " (Q-55 C door 2.20 m)"
        before = None
        if x["state"] == "LIVE":
            l = by_id[x["line_id"]]
            assert l["held_low"] is None and l["measured_net"] is None   # HELD blank in V3.0.77
        aft = None if lt["render"] is None else tuple(lt["render"])
        w = R.wire_row(x["line_id"], x["state"], before, aft, ev,
                       "T-314 r2 stage (T-737 pin) + T-747 + T-751 (+ T-305 / T-311 / T-324 / T-337 / T-348 / T-567)")
        w.update({"key": key, "element_id": s["element_id"],
                  "item_code": "FIN.EXT.FINISH" if not key.startswith("NEW") or key.split()[1] == "FIN.EXT.FINISH"
                  else key.split()[1] + " (stage key; item code at T-314 r3, Lead naming)", "unit": "m2", "paint_after": "" if lt["paint"] is None
                  else " .. ".join(lt["paint"]), "valued_part": "" if not lt["valued_part"] else
                  " .. ".join(lt["valued_part"]["render"]), "blank_faces": ";".join(lt["blank_faces"])})
        wire.append(w)
    for e in edge_rows:
        b = None if not e["before"] else tuple(e["before"].split(" .. "))
        a = None if not e["after"] else tuple(e["after"].split(" .. "))
        lrow = by_id[e["line_id"]]
        w = R.wire_row(e["line_id"], "LIVE", b, a, "HELD",
                       "T-749 V3.0.77" + (" + T-754" if e["line_id"] in (pe, nh) else ""))
        w.update({"key": e["element_id"], "element_id": e["element_id"], "item_code": lrow["item_code"],
                  "unit": "lm", "paint_after": "", "valued_part": "", "blank_faces": "",
                  "host_after_r3": e["host_after_r3"]})
        wire.append(w)

    # ---- (E) re-check: every mapped LIVE id and every NEW id across V3.0.73 .. V3.0.77 -----------------------------
    live_ids = sorted({fr["v3077_line_id"] for fr in face_rows if fr["v3077_state"] == "LIVE"}
                      | {c["v3077_line_id"] for c in comp_rows if c["v3077_state"] == "LIVE"}
                      | {o["v3077_line_id"] for o in open_rows if o["v3077_state"] == "LIVE"}
                      | {o["edge_line_id"] for o in open_rows if o["edge_line_id"]}
                      | {e["line_id"] for e in edge_rows})
    new = sorted((s["line_id"], s["element_id"]) for s in sl.values() if s["action"] == "ADD")
    recheck = {v: recheck_index(jload(p), live_ids, new, idx) for v, p in OLDER.items()}
    recheck["V3.0.77"] = recheck_index(idx, live_ids, new, idx)
    assert recheck["V3.0.77"]["changed"] == [] and recheck["V3.0.77"]["absent"] == []

    states = {}
    for fr in face_rows:
        states[fr["v3077_state"]] = states.get(fr["v3077_state"], 0) + 1
    cstates = {}
    for c in comp_rows:
        cstates[c["v3077_state"]] = cstates.get(c["v3077_state"], 0) + 1
    stale = sum(1 for x in face_rows + comp_rows + open_rows if x.get("v3077_state") in ("STALE", "COLLISION")) \
        + sum(1 for o in open_rows if o["edge_state"] in ("STALE", "COLLISION")) \
        + sum(1 for f in face_rows if "STALE" in f["t305_own_line"] + f["t305_geometry_line"]) \
        + sum(1 for c in comp_rows if c["t311_line_state"] == "STALE")
    rl = [w for w in wire if w["unit"] == "m2"]
    valued = [w for w in rl if w["after"]]
    vl = sum((D(w["after"].split(" .. ")[0]) for w in valued), Decimal(0))
    vh = sum((D(w["after"].split(" .. ")[1]) for w in valued), Decimal(0))
    part = [D(x) for w in rl if w["valued_part"] for x in w["valued_part"].split(" .. ")]
    summary = {
        "schema": SCHEMA, "version": R.VERSION, "rules": list(R.RULE_IDS), "target": idx["candidate_version"],
        "pins": {p: sha(p)[:16] for p in PINS},
        "A_faces": {"t305_rows": len(t305), "rows_out": len(face_rows), "states": states,
                    "stage_added": len(added), "t305_named_differences": sorted(T305_CAUSES),
                    "not_a_face": sorted(NOT_A_FACE)},
        "A_components": {"t311_rows": len(rows(T311C)), "rows_out": len(comp_rows), "states": cstates},
        "A_openings": {"rows": len(open_rows)},
        "stale_or_collision": stale,
        "B_edges": {"lines": len(edge_rows), "changed": [pe], "rehosted_no_qty": [nh],
                    "corners_before": [s6(x) for x in cb], "corners_after": [s6(x) for x in ca],
                    "windows_lm": s6(wsum), "edge_total_before": [s6(cb[0] + wsum), s6(cb[1] + wsum)],
                    "edge_total_after": [s6(ca[0] + wsum), s6(ca[1] + wsum)], "residual": "0.000000"},
        "C_faces": {"faces": len(paint_rows), "blank": blanks,
                    "render": [s6(tot[0]), s6(tot[1])], "paint": [s6(tot[2]), s6(tot[3])],
                    "render_minus_paint": [s6(tot[0] - tot[2]), s6(tot[1] - tot[3])]},
        "D_wire": {"render_lines": len(rl), "change": sum(1 for w in rl if w["action"] == "CHANGE"),
                   "add": sum(1 for w in rl if w["action"] == "ADD"),
                   "valued_lines_m2": [s6(vl), s6(vh)], "blank_line_valued_part": [s6(x) for x in part],
                   "edge_lines": len(edge_rows), "edge_change": sum(1 for w in wire if w["unit"] == "lm" and w["action"] == "CHANGE"),
                   "freelancer_sigma_m2": s6(FREELANCER_SIGMA),
                   "paint_vs_freelancer_pct": [s6((tot[2] / FREELANCER_SIGMA - 1) * 100),
                                               s6((tot[3] / FREELANCER_SIGMA - 1) * 100)]},
        "E_recheck": {"ids": len(live_ids), "new_ids": len(new),
                      "by_index": {v: {"changed": r["changed"], "absent": len(r["absent"]), "new_taken": r["new_taken"]}
                                   for v, r in recheck.items()},
                      "after_T738": "PENDING: T-738 not merged at this run; run --recheck on LINE_INDEX_V3_0_78.json"},
    }
    return {"face_map": face_rows, "component_map": comp_rows, "opening_map": open_rows, "edge_deltas": edge_rows,
            "face_paint": paint_rows, "wire": wire}, summary, live_ids, new


def sig(l):
    return [l["item_code"], l["element_id"], l["unit"], l["class"], l["measured_net"], l["held_low"], l["held_high"]]


def recheck_index(tgt, live_ids, new, ref):
    rm = {l["line_id"]: l for l in ref["lines"]}
    tm = {l["line_id"]: l for l in tgt["lines"]}
    tel = {l["element_id"] for l in tgt["lines"]}
    changed = sorted(i for i in live_ids if i in tm and sig(tm[i]) != sig(rm[i]))
    absent = sorted(i for i in live_ids if i not in tm)
    taken = sorted(i for i, e in new if i in tm or e in tel)
    return {"changed": changed, "absent": absent, "new_taken": taken}


def to_csv(rs):
    if not rs:
        return ""
    keys = list(rs[0].keys())
    for r in rs:
        for k in r:
            if k not in keys:
                keys.append(k)
    b = io.StringIO()
    w = csv.DictWriter(b, fieldnames=keys, lineterminator="\n")
    w.writeheader()
    for r in rs:
        w.writerow({k: r.get(k, "") for k in keys})
    return b.getvalue()


NAMES = {"face_map": "T756_FACE_MAP.csv", "component_map": "T756_COMPONENT_MAP.csv",
         "opening_map": "T756_OPENING_MAP.csv", "edge_deltas": "T756_EDGE_DELTAS.csv",
         "face_paint": "T756_FACE_PAINT.csv", "wire": "T756_WIRE_TABLE.csv"}


def render():
    tables, summary, _, _ = build()
    files = {NAMES[k]: to_csv(v) for k, v in tables.items()}
    files["T756_SUMMARY.json"] = json.dumps(summary, indent=1, sort_keys=True) + "\n"
    return files


def main(argv):
    if len(argv) > 1 and argv[1] == "--recheck":
        _, _, live, new = build()
        r = recheck_index(json.loads(Path(argv[2]).read_text()), live, new, jload(IDX77))
        print(json.dumps(r, indent=1))
        return 0 if not (r["changed"] or r["absent"] or r["new_taken"]) else 1
    files = render()
    if len(argv) > 1 and argv[1] == "--check":
        bad = [n for n, t in files.items() if (OUT / n).read_text() != t]
        print("T756 check:", "OK" if not bad else f"DIFFER {bad}")
        return 1 if bad else 0
    OUT.mkdir(exist_ok=True)
    for n, t in files.items():
        (OUT / n).write_text(t)
    print(json.dumps(json.loads(files["T756_SUMMARY.json"]), indent=1)[:4000])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
