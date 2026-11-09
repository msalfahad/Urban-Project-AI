"""T-572 development-villa register: every HELD structural component of B10 concrete (columns, necks, lift, keyed
footing line: F10 + F, boundary band, strap pieces in footings; blinding) and B1 earthworks (excavation, backfill,
disposal) of ARCH_TAKEOFF_V3.0.58 (NOT RELEASED) with the bound the drawings alone support or the item that prevents
one (R-T572-1 .. 4), then the like-for-like comparison on the measured set.

Committed inputs only (no drawing is opened here; every printed value below is cited to the merged task that read it):
  lines      research/agents_t507/out/LINE_INDEX_V3_0_57.json (structural lines of V3.0.58, R-T507-1 (e))
  necks      research/agents_t205/ALSENAN_NECK_INPUT.json (section candidates, footing type / H per neck; T-205)
  positions  research/agents_t566/out/T566_REGISTRATION.json (neck position -> GF member; T-566)
  GF bases   research/agents_t394/summary_t394.json (member base datum; T-394 / T-287)
  hold items research/agents_t449/out/CORRECTION_REGISTER_CONCRETE_T449.json (column hold items)
  his side   research/agents_t551/out/T551_COLUMN_FOOTING_RECONCILE.json (family totals only) and, when the private
             workbook is present, research/agents_t551/t551_alsenan.build (in memory; only m3 aggregates are written)

    python3 -I research/agents_t572/t572_alsenan.py [--freelancer .work/private/concrete_rebar.xlsx] [--write]
"""
from __future__ import annotations

import importlib
import json
import re
import sys
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
RES = HERE.parent
sys.path.insert(0, str(HERE))
import t572_rules as R  # noqa: E402

LINE_INDEX = RES / "agents_t507" / "out" / "LINE_INDEX_V3_0_57.json"
T205 = RES / "agents_t205" / "ALSENAN_NECK_INPUT.json"
T566 = RES / "agents_t566" / "out" / "T566_REGISTRATION.json"
T394 = RES / "agents_t394" / "summary_t394.json"
T449 = RES / "agents_t449" / "out" / "CORRECTION_REGISTER_CONCRETE_T449.json"
T551 = RES / "agents_t551" / "out" / "T551_COLUMN_FOOTING_RECONCILE.json"
T565 = RES / "agents_t565" / "out" / "T565_EARTHWORKS_RECONCILE.json"
OUT = HERE / "out" / "T572_HELD_BOUNDS.json"
D = Decimal

# ---- printed / drawing-confirmed datums (each cited; none is a default) -------------------------------------------
MIN_DEPTH = D("1.50")      # ST p.9 note 1: excavation / founding 'not less than 1.50 m below the plot level' (minimum)
EG = D("0.00")             # existing ground +-0.00 (T-357 DERIVED); the 1.50 is measured from it
STACK = D("0.17")          # under every footing: underlay 0.07 (T-206 DRAWING-CONFIRMED) + blinding 0.10 (ST p.13)
TOP_ANNEX = D("0.25")      # annex FFL +0.30 less the drawn 0.05 build-up (T-287 G1 / T-214): lowest drawn GF top
NOTE1 = "ST p.9 note 1 printed minimum 1.50 below EG +-0.00 (T-357)"
FORMATION_ITEM = "Q-21 C / T-042 B4: formation below the printed 1.50 minimum not printed (no maximum)"
FRAME = (75968, 14448)     # T-205 neck ids -> V3.0.58 neck element ids (T-350 r2 frame_offset_mm, all 36 agree)
F10F_H = (D("0.50"), D("0.30"))   # T-233: one outline tagged F10 (0.50) and F (0.30); Q-31 C


def _lines():
    d = json.loads(LINE_INDEX.read_text(encoding="utf-8"))
    assert d["candidate_version"] == "ARCH_TAKEOFF_V3.0.57"
    return d["lines"]


def _num(x):
    return None if x is None else D(str(x))


# ------------------------------------------------------------------------------------------------- necks
def neck_table(lines):
    """R-T572-2 per neck: drawn LOWER bound = min section x (top_low + 1.50 - 0.17 - H_max); upper on the formation."""
    pos = {p["position"]: p for p in json.loads(T566.read_text(encoding="utf-8"))["positions"]}
    base = {r["member"]: r for r in json.loads(T394.read_text(encoding="utf-8"))["per_line_engine"]}
    hold = {x["line_id"]: (x.get("patch") or {}).get("held_item") or ""
            for x in json.loads(T449.read_text(encoding="utf-8"))["entries"]}
    t205 = {}
    for n in json.loads(T205.read_text(encoding="utf-8"))["necks"]:
        m, x, y = re.search(r":(C\w*|CN)@(\d+),(\d+)", n["id"]).groups()
        t205[(m, int(x) + FRAME[0], int(y) + FRAME[1])] = n
    rows = []
    for ln in sorted((x for x in lines if x["item_code"] == "STR.CONC.NECK"), key=lambda x: x["element_id"]):
        assert ln["class"] == "HELD", ln["element_id"]
        m, x, y = re.search(r":(C\w*|CN)@(\d+),(\d+)", ln["element_id"]).groups()
        hit = [v for (mm, a, b), v in t205.items() if mm == m and abs(a - int(x)) <= 2 and abs(b - int(y)) <= 2]
        assert len(hit) == 1, ln["element_id"]
        n = hit[0]
        p = pos[n["outline_handle"]]
        secs = sorted({D(str(s["W"])) * D(str(s["D"])) / 10000 for s in n["sections"]})
        ft = n["footing"]["type"]
        H = F10F_H if ft == "F10|F" else (D(str(n["footing"]["H"])),)
        flags = []
        gf = p["members"].get("GF")
        if gf is None:
            top, tb = TOP_ANNEX, "no GF member (neck-only CN): lowest drawn GF structural top +0.25 (T-287 / T-214)"
            flags.append("TOP_LOWEST_DRAWN")
        else:
            b = D(str(base[gf["handle"]]["base"]))
            if "Q-54B" in hold.get(gf["line_id"], ""):
                top, tb = min(b, TOP_ANNEX), (f"annex member {gf['handle']}: T-394 base +{b} vs annex FFL +0.30 - 0.05 "
                                              f"= +0.25 (two readings, the lower taken)")
                flags.append("TOP_TWO_READINGS")
            else:
                top, tb = b, f"GF column base +{b} at {gf['handle']} (same datum as the neck top, R-NECK-ENDS-1; T-394)"
        if ft == "FF":
            flags.append("NOTE1_ON_LIFT_RAFT")
        if len(secs) > 1:
            flags.append("SECTION_CANDIDATES")
        h = R.neck_low_height(top, MIN_DEPTH, STACK, H)
        lo = R.volume(secs, h)
        cand = None if ln["held_low"] is None else (ln["held_low"], ln["held_high"])
        c = R.component(ln["element_id"], "B10 NECK", "m3", low=lo,
                        low_basis=f"min section {min(secs)} m2 x h {h} = top +{top} ({tb}) + {MIN_DEPTH} ({NOTE1}) - "
                                  f"{STACK} stack - H {max(H)} ({ft}, footing schedule; T-205)",
                        high_item=FORMATION_ITEM + ("; D-43 lift pit depth; D-63 section" if ft == "FF" else ""),
                        candidate_range=cand, flags=flags)
        c.update(line_id=ln["line_id"], mark=m, position=n["outline_handle"], footing=ft,
                 h_low_m=str(h), section_candidates_m2=[str(s) for s in secs])
        rows.append(c)
    return rows


def s01_neck_check(rows):
    """Cross-check of the join: the 29 pit necks at S01 (footing underside -1.50) with the printed section reproduce
    the merged T-350 r2 / T-565 displacement term 5.154 m3 exactly."""
    n205 = {n["outline_handle"]: n for n in json.loads(T205.read_text(encoding="utf-8"))["necks"]}
    tot = sa = D(0)
    for r in rows:
        if r["footing"] in ("FF", "F10|F") or r["position"] == "10E0":
            continue
        n = n205[r["position"]]
        a = D(str(n["sections"][0]["W"])) * D(str(n["sections"][0]["D"])) / 10000
        tot += a * (MIN_DEPTH - D(str(n["footing"]["H"])))
        sa += a
    return R.d6(tot), R.d6(sa)


# ------------------------------------------------------------------------------------------------- columns
def column_table(lines):
    hold = {x["line_id"]: x for x in json.loads(T449.read_text(encoding="utf-8"))["entries"]}
    out = []
    for ln in sorted((x for x in lines if x["item_code"] == "STR.CONC.COLUMN" and x["class"] == "HELD"),
                     key=lambda x: x["element_id"]):
        e, h = ln["element_id"], hold.get(ln["line_id"])
        st = (re.search(r"\|(GF|1F|2F)$", e) or [None, "2F" if "PC-2F" in e else None])[1]
        if e.startswith("U-C:COL:SH12:CN@"):
            c = R.component(e, "B10 COLUMN", "m3", candidate_range=None if ln["held_low"] is None else
                            (ln["held_low"], ln["held_high"]), flags=["CANDIDATE_EXPOSURE_NOT_A_BOUND"]
                            if ln["held_low"] is not None else [],
                            not_present_basis="column schedule CN row: FOUNDATION 30 x 30 only, GF / 1F / 2F struck "
                                              "(printed; T-075, T-042): the plan symbol is the CN neck (no column above)")
        elif h and h["action"] == "CONFLICT_RANGE":
            c = R.component(e, "B10 COLUMN", "m3", low=ln["held_low"], high=ln["held_high"],
                            low_basis="R-COL-SECTION-CONFLICT-1: smaller of the two printed / drawn sections x the "
                                      "drawn storey height (T-394, T-217, T-566)",
                            high_basis="larger printed section x the same height (D-16 / D-63 section CONFLICT)")
        else:
            item = (h or {}).get("patch", {}).get("held_item") or "D-39_ROOF_DATUM (planted column, text 'P.C 20x50' " \
                                                                  "vs drawn 0.20 x 0.40)"
            blk = ("Q-54B / D-39: annex roof slab-top datum not printed" if "Q-54B" in item
                   else "D-39: main roof slab-top datum and roof build-up not printed")
            if "D-44" in item:
                blk += "; D-44 B15 upstand / downstand"
            if "SECTION_CONFLICT" in item or "PC-2F" in e:
                blk += "; section CONFLICT"
            c = R.component(e, "B10 COLUMN", "m3", low_item=blk, high_item=blk)
        c.update(line_id=ln["line_id"], storey=st)
        out.append(c)
    return out


# ------------------------------------------------------------------------------------------------- lift / footing / blinding
def lift_table(lines):
    pit = [x for x in lines if x["element_id"] == "LIFT_PIT:WALLS"]
    tie = [x for x in lines if x["element_id"] == "LIFT_TIE_BEAM:GF"]
    assert len(pit) == len(tie) == 1 and pit[0]["held_low"] is None and tie[0]["held_low"] is None
    h = R.neck_low_height(D("0.95"), MIN_DEPTH, STACK, (D("0.55"),))
    ring = D("1.10")      # net ring 2.20^2 - 1.80^2 less the four lift column pieces 0.50 (R-T394-6, T-551)
    a = R.component("LIFT_PIT:WALLS", "B10 LIFT", "m3", low=R.d6(ring * h),
                    low_basis=f"net ring {ring} m2 (R-T394-6) x h {h} = GF top +0.95 (lift GF columns' base, T-394) + "
                              f"{MIN_DEPTH} ({NOTE1}) - {STACK} stack - FF raft H 0.55",
                    high_item="D-43 pit depth 'as per lift manufacturer' (ST p.14)", flags=["NOTE1_ON_LIFT_RAFT"])
    b = R.component("LIFT_TIE_BEAM:GF", "B10 LIFT", "m3", low_item="D-43 tie-beam section not printed (ST p.8 note 19)",
                    high_item="D-43 tie-beam section not printed (ST p.8 note 19)")
    a["line_id"], b["line_id"] = pit[0]["line_id"], tie[0]["line_id"]
    return [a, b]


FOOTING_BASIS = {
    "P-C:FTG:SH10:T652:10A5": dict(
        low_basis="T-233 reading A: F10 2.80 x 1.40 x 0.50 + F 0.90 x 0.80 x 0.30 as scheduled rows",
        high_basis="T-233 reading B: the one drawn outline 1B1B at the deepest tagged depth 0.50", item="Q-31 C"),
    "P-C:SCOPE:BOUNDARY_WALL:FOUNDATION:CC-9fd936ab60:BEAM": dict(
        low=D("5.639"), high=D("11.033"),
        low_basis="T-065 / T-233: band 0.20 x 0.40 (E4), 70.49 m free of footings = 5.639",
        high_basis="T-065 / T-233: band 0.20 x 0.60 (E3) over the closed 91.94 m = 11.033 gross (8.459 net of the 21.45 m "
                   "inside 9 footing outlines, which the pads own)", flags=["LINE_POINT_7.2204_IS_Q-28A_READING"]),
    "HL:STRAP_CONCRETE:SB1:IN_FOOTING:F10_F": dict(
        low_basis="SB1 end piece inside the F10 + F outline may be no separate solid (follows Q-31 C; T-233)",
        high_basis="SB1 1.00 x 0.50 section over its drawn length inside the outline (T-231 / T-233)", existence=True),
    "HL:STRAP_CONCRETE:SB3:IN_FOOTING:F3": dict(
        low_basis="SB3 0.50 x 0.40 soffit at the F3 top (T-230)",
        high_basis="SB3 soffit at the F3 underside (D-15 strap soffit; T-230 / T-350)"),
    "FENCE:BAND:PADS": dict(item="pad count / spacing of the boundary-wall pads not printed (ST p.14; Q-28 A, T-478)"),
}
BLINDING_BASIS = {
    "BLINDING_FOOTING:FTG:SH10:T652:10A5": ("T-233 / T-478: 0.10 under the F10 + F readings A / B, 10 cm past each face",
                                       False, "Q-31 C"),
    "BLINDING_BEYOND_PLOT_LINE": ("D-14: projection beyond the plot line may not be built (0) .. full 10 cm (T-100)",
                                  True, "D-14"),
    "BLINDING_LIFT_RAFT_FF": ("T-478: 0.10 under the FF raft, projection readings", False, "D-14 / D-43"),
    "BLINDING_STRAP": ("D-15: p.13 prints no blinding under straps (0) .. 0.10 under the 3 straps (T-100 / T-350)",
                       True, "D-15"),
    "BLINDING_GROUND_BEAM": ("T-478: 0.10 under the ground beams, plan-distinct of the pit layer; D-33 / D-35 sections",
                             False, "D-33 / D-35"),
    "BLINDING_BOUNDARY_WALL_BASE": (None, False, "pad count not printed (Q-28 A, T-478)"),
}


def footing_blinding_table(lines):
    out = []
    for ln in lines:
        e = ln["element_id"]
        if ln["class"] != "HELD":
            continue
        if ln["item_code"] in ("STR.CONC.FOOTING", "STR.CONC.STRAP", "STR.CONC.BOUNDARY_WALL", "STR.CONC.BOUNDARY_PAD"):
            b = FOOTING_BASIS[e]
            if "item" in b and "low_basis" not in b:
                c = R.component(e, "B10 FOOTING LINE", "m3", low_item=b["item"], high_item=b["item"])
            else:
                lo, hi = b.get("low", ln["held_low"]), b.get("high", ln["held_high"])
                c = R.component(e, "B10 FOOTING LINE", "m3", low=lo, high=hi, low_basis=b["low_basis"],
                                high_basis=b["high_basis"], existence_open=b.get("existence", False),
                                flags=b.get("flags", ()),
                                candidate_range=None if lo == ln["held_low"] else (ln["held_low"], ln["held_high"]))
        elif ln["item_code"] == "STR.CONC.BLINDING":
            key = next(k for k in BLINDING_BASIS if e.endswith(k))
            basis, ex, item = BLINDING_BASIS[key]
            if basis is None:
                c = R.component(e, "B10 BLINDING (plain)", "m3", low_item=item, high_item=item)
            else:
                c = R.component(e, "B10 BLINDING (plain)", "m3", low=ln["held_low"], high=ln["held_high"],
                                low_basis=basis, high_basis=basis, existence_open=ex)
        else:
            continue
        c["line_id"] = ln["line_id"]
        out.append(c)
    return out


# ------------------------------------------------------------------------------------------------- earthworks
def earthworks_table(lines, necks):
    t565 = json.loads(T565.read_text(encoding="utf-8"))
    pmin = D(str(t565["printed_minimum_bound_pits_m3"]))
    parts = t565["pits_verified_displacement_parts"]
    out = []
    s01, sum_a = s01_neck_check(necks)
    assert s01 == D("5.154000"), s01           # the join reproduces T-350 r2 / T-565
    # pits backfill, drawn LOWER end (R-T572-2 / R-T565-4): excavation at the printed minimum depth less the largest
    # buried volume at that formation; backfill rises with depth (plan 124.65 m2 > the neck sections 5.13 m2), so the
    # printed minimum gives the least backfill.
    fixed = sum((D(str(v)) for v in parts.values()), D(0)) if isinstance(parts, dict) else D(str(parts))
    necks_min = s01 - STACK * sum_a                       # 29 necks below EG at formation -1.50 (printed sections)
    c8_max = R.d6(D("0.27") * (MIN_DEPTH - STACK - D("0.50")))   # 10E0 C8 / C7 conflict, larger section, F14 0.50
    strap_ends, gb_max = D("0.179618"), D("10.672549")   # T-565 s.3 (strap ends; GB solids, deepest reading)
    bf_low = R.d6(pmin - fixed - necks_min - c8_max - strap_ends - gb_max)
    zone = {
        "B1-02:Z1-TRENCH-EXT-GB-MAIN": ("bounded",),
        "B1-02:Z1-PIT-F10F": ("low", R.d6(D("4.35") * MIN_DEPTH),
                              f"smallest S02 in-plot plan 4.350 m2 (F10 alone; T-350 r2) x {MIN_DEPTH} ({NOTE1})",
                              FORMATION_ITEM + "; Q-31 C", False, []),
        "B1-02:Z1-PIT-FF": ("low", R.d6(D("20.700") * MIN_DEPTH),
                            f"FF raft plan 20.700 m2 DRAWING-CONFIRMED (T-350) x {MIN_DEPTH} ({NOTE1})",
                            "D-43 pit floor 'as per lift manufacturer' (ST p.14)", False, ["NOTE1_ON_LIFT_RAFT"]),
        "B1-02:Z1-TRENCH-ANNEX": ("blank", "D-34 / D-33 interior and D-35 exterior ground-beam sections"),
        "B1-02:Z1-TRENCH-COURT": ("blank", "no court ground-beam section printed (T-350)"),
        "B1-02:Z1-TRENCH-STRAPS": ("blank", "D-15 strap soffit (footprint 7.889 m2 drawn, depth not)"),
        "B1-02:Z1-TRENCH-BOUNDARY": ("blank", "boundary-wall foundation depth not printed (Q-28 A provisional)"),
        "B1-02:Z1-TRENCH-INT-GB-MAIN-D33": ("blank", "D-33 loaded ground-beam sections"),
        "B1-02:Z1-TRENCH-INT-GB-MAIN-ZERO": ("low", D(0), "13 runs wholly above EG while the wet build-up b_wet <= 0.30 "
                                             "(T-350 / T-214 / T-221): may be no excavation", "D-40 wet-zone build-up",
                                             True, []),
        "B1-02:Z1-LOWER-GB-ROW": ("low", D(0), "p.13 two-beam detail only when GB top - footing underside > 2.50; at "
                                  "the printed minimum 0.95 + 1.33 = 2.28 (not required)", FORMATION_ITEM +
                                  "; no plan draws the row", True, []),
        "B1-03:Z1-PITS-24": ("low", bf_low, f"printed-minimum excavation {pmin} (T-565) - verified buried {R.d6(fixed)} "
                             f"- 29 necks below EG at formation -1.50 {R.d6(necks_min)} - C8 conflict {c8_max} - strap "
                             f"ends {strap_ends} - ground-beam solids deepest reading {gb_max}",
                             FORMATION_ITEM + "; working space OQ-13", False, []),
        "B1-03:Z1-POOL": ("low", D(0), "neat envelope part calculated 0.000 (T-350 r2): backfill only in the "
                          "working space / blinding projection", "OQ-13 working space; blinding projection", True, []),
        "B1-03:Z1-TRENCH-EXT-GB-MAIN": ("low", D(0), "neat cut filled by the blinding, calculated 0.000 (T-350 r2)",
                                        "OQ-13 working space", True, []),
        "B1-03:Z1-OTHER-TRENCHES": ("blank", "as their excavation zones: D-33 / D-34 / D-35 / D-15 / Q-28 A"),
        "B1-03:Z1-PIT-F10F": ("blank", "Q-31 C outline and the C10 / C necks; formation (Q-21 C)"),
        "B1-03:Z1-PIT-FF": ("blank", "D-43 lift pit depth"),
        "B1-03:Z2": ("blank", "Z2 extent, D-40 wet-floor build-up, D-33 / D-34"),
        "B1-04:ALL": ("blank", "in-situ / compacted dry densities not sourced; Z2 draw; excavation and backfill held"),
    }
    fam = {"STR.EARTH.EXCAVATION": ("B1-02 EXCAVATION", "m3"), "STR.EARTH.BACKFILL": ("B1-03 BACKFILL", "m3"),
           "STR.EARTH.DISPOSAL": ("B1-04 DISPOSAL", "m3")}
    for ln in lines:
        if ln["item_code"] not in fam or ln["class"] != "HELD":
            continue
        key = ln["element_id"].split("EW-T350:", 1)[1]
        z = zone[key]
        f, u = fam[ln["item_code"]]
        cand = None if ln["held_low"] is None else (ln["held_low"], ln["held_high"])
        if z[0] == "bounded":
            c = R.component(ln["element_id"], f, u, low=ln["held_low"], high=ln["held_high"],
                            low_basis="neat blinding cut L 55.99 x 0.50 x 0.10 less run ends dug with the pits, "
                                      "upper reading (T-350 r2 / T-497 ownership)",
                            high_basis="same, lower in-pit reading (T-350 r2 / T-497)", flags=["WORKING_SPACE_EXCLUDED"])
        elif z[0] == "low":
            c = R.component(ln["element_id"], f, u, low=z[1], low_basis=z[2], high_item=z[3], existence_open=z[4],
                            flags=z[5] + (["S01_RANGE_BESIDE_OWNER_ESTIMATED"] if cand else []), candidate_range=cand)
        else:
            c = R.component(ln["element_id"], f, u, low_item=z[1], high_item=z[1])
        c["line_id"] = ln["line_id"]
        out.append(c)
    return out


# ------------------------------------------------------------------------------------------------- freelancer side
def his_family_totals():
    t = json.loads(T551.read_text(encoding="utf-8"))
    return {"COLUMN": sum(D(t["columns"][s]["his_m3"]) for s in ("GF", "1F", "2F")), "NECK": D(t["necks"]["his_m3"]),
            "LIFT_HELD_SHARE": -D(t["lift_walls"]["components"]["HELD"]["m3"]),
            "F10": D("1.960"), "BAND": D("8.604"), "BLINDING": D(t["blinding"]["his_m3"])}


def measured_set(freelancer, necks):
    """R-T572-4 on the private workbook (in memory): columns and footing pads where every engine line of the mark is
    valued and he has a row; necks on his count per mark against the drawn LOWER bounds. Only m3 aggregates return."""
    sys.path.insert(0, str(RES / "agents_t551"))
    A = importlib.import_module("t551_alsenan")
    doc, _ = A.build(freelancer)
    out = {}
    for st in ("GF", "1F"):
        e = h = D(0)
        n = 0
        split = defaultdict(D)
        for r in doc["columns"]["marks"]:
            if r["storey"] != st or "HELD" in r:
                continue
            tm = {k: D(v) for k, v in r.items() if k not in ("storey", "mark", "engine_m3")}
            eng = D(r["engine_m3"])
            his = eng - sum(tm.values(), D(0))
            if eng > 0 and his > 0:
                e, h, n = e + eng, h + his, n + 1
                for k, v in tm.items():
                    split[k] += v
        assert sum(split.values(), D(0)) == e - h
        out[f"columns_{st}"] = dict(R.like_for_like(e, h), marks=n,
                                    split_m3={k: str(v.quantize(R.Q6)) for k, v in split.items()})
    e = h = D(0)
    n = 0
    for r in doc["footing_line"]["marks"]:
        if "HELD" in r or r["mark"] in ("BAND",) or "in footing" in r["mark"]:
            continue
        terms = sum((D(v) for k, v in r.items() if k not in ("mark", "engine_m3", "cause")), D(0))
        eng = D(r["engine_m3"])
        his = eng - terms
        if eng > 0 and his > 0:
            e, h, n = e + eng, h + his, n + 1
    out["footing_pads_and_straps"] = dict(R.like_for_like(e, h), marks=n)
    # necks: his count per mark against the his_n SMALLEST drawn lower bounds of that mark (valid for any binding)
    lows = defaultdict(list)
    for c in necks:
        lows[c["mark"]].append(D(c["low"]))
    his_n, his_v = defaultdict(int), defaultdict(D)
    for r in doc["necks"]["held_beside_his"]:
        if r["his_share_m3"]:
            his_n[r["mark"]] += 1
            his_v[r["mark"]] += D(r["his_share_m3"])
    eng_low = sum((sum(sorted(lows[m])[:his_n[m]], D(0)) for m in his_n), D(0))
    his_tot = sum(his_v.values(), D(0))
    below = sum(1 for m in his_n if his_v[m] < sum(sorted(lows[m])[:his_n[m]], D(0)))
    out["necks_on_his_count"] = {"engine_drawn_lower_m3": str(R.d6(eng_low)), "his_m3": str(R.d6(his_tot)),
                                 "his_minus_engine_lower_m3": str((his_tot - eng_low).quantize(R.Q6)),
                                 "his_count": sum(his_n.values()), "marks": len(his_n), "marks_his_below_drawn_lower":
                                 below, "class": R.against_bound(his_tot, eng_low, None)}
    return out


# ------------------------------------------------------------------------------------------------- build
def build(freelancer=None):
    lines = _lines()
    necks = neck_table(lines)
    cols = column_table(lines)
    lift = lift_table(lines)
    fb = footing_blinding_table(lines)
    ew = earthworks_table(lines, necks)
    comps = cols + necks + lift + fb + ew
    assert len({c["line_id"] for c in comps}) == len(comps)
    valued = defaultdict(D)
    code_fam = {"STR.CONC.COLUMN": "B10 COLUMN", "STR.CONC.NECK": "B10 NECK", "STR.CONC.LIFT": "B10 LIFT",
                "STR.CONC.FOOTING": "B10 FOOTING LINE", "STR.CONC.STRAP": "B10 FOOTING LINE",
                "STR.CONC.BOUNDARY_WALL": "B10 FOOTING LINE", "STR.CONC.BOUNDARY_PAD": "B10 FOOTING LINE",
                "STR.CONC.BLINDING": "B10 BLINDING (plain)", "STR.EARTH.EXCAVATION": "B1-02 EXCAVATION",
                "STR.EARTH.BACKFILL": "B1-03 BACKFILL", "STR.EARTH.DISPOSAL": "B1-04 DISPOSAL"}
    for x in lines:
        if x["item_code"] in code_fam and x["class"] == "RELEASED":
            valued[code_fam[x["item_code"]]] += D(str(x["measured_net"]))
    fams = {}
    for f in dict.fromkeys(code_fam.values()):
        cc = [c for c in comps if c["family"] == f]
        tot = R.family_total(valued[f], cc)
        tot["kinds"] = {k: sum(1 for c in cc if c["kind"] == k) for k in R.KINDS if any(c["kind"] == k for c in cc)}
        fams[f] = tot
    his = his_family_totals()
    nk = fams["B10 NECK"]
    beside = {
        "B10 NECK": {"his_m3": str(his["NECK"]), "engine_drawn_lower_all36_m3": nk["bounded_part_low"],
                     "candidate_generic_range_m3": ["3.075000", "15.375000"]},
        "B10 LIFT pit walls": {"his_held_share_m3": str(his["LIFT_HELD_SHARE"]), "engine_drawn_lower_m3": lift[0]["low"],
                               "class": R.against_bound(his["LIFT_HELD_SHARE"], lift[0]["low"], None)},
        "F10 + F": {"his_m3": str(his["F10"]), "engine": [fb_get(fb, "P-C:FTG:SH10:T652:10A5", "low"), fb_get(fb, "P-C:FTG:SH10:T652:10A5", "high")],
                    "class": R.against_bound(his["F10"], fb_get(fb, "P-C:FTG:SH10:T652:10A5", "low"), fb_get(fb, "P-C:FTG:SH10:T652:10A5", "high"))},
        "boundary band": {"his_m3": str(his["BAND"]), "engine": [fb_get(fb, "BOUNDARY_WALL", "low"),
                                                                 fb_get(fb, "BOUNDARY_WALL", "high")],
                          "class": R.against_bound(his["BAND"], fb_get(fb, "BOUNDARY_WALL", "low"),
                                                   fb_get(fb, "BOUNDARY_WALL", "high"))},
        "B1 earthworks": {"his": "NO_ROW (T-565: 0 hits in 885 rows)", "pct": None},
        "blinding": {"his_m3": str(his["BLINDING"]), "class": "NOT_LIKE_FOR_LIKE (one plate over the plot, T-478 "
                                                               "RULE_DIFFERENCE)", "pct": None},
    }
    doc = {"schema": "T572_HELD_BOUNDS_V1",
           "candidate": "ARCH_TAKEOFF_V3.0.58 (structural lines = V3.0.57 LINE_INDEX); NOT RELEASED",
           "note": "engine figures, bounds, bases and items only; no row, dimension or count of the freelancer "
                   "(his family totals as already tracked by T-551 / T-565; measured-set sums only)",
           "datums": {"min_depth_m": str(MIN_DEPTH), "stack_m": str(STACK), "top_annex_m": str(TOP_ANNEX),
                      "eg_m": str(EG)},
           "s01_neck_join_check_m3": str(s01_neck_check(necks)[0]),
           "families": fams, "beside_his": beside, "components": comps}
    if freelancer:
        doc["measured_set"] = measured_set(freelancer, necks)
    return doc


def fb_get(fb, key, end):
    c = [x for x in fb if key in x["element_id"] and x["family"] == "B10 FOOTING LINE"]
    assert len(c) == 1, key
    return c[0][end]


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--freelancer")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    doc = build(a.freelancer)
    if a.write:
        OUT.parent.mkdir(exist_ok=True)
        OUT.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: doc[k] for k in ("families", "beside_his") + (("measured_set",) if a.freelancer else ())},
                     indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
