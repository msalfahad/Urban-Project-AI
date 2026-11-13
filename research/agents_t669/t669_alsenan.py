"""T-669 concrete close-out ledger (development villa): (a) Checker F-T665-1, the annex SE ground-beam corner square;
(b) a drawn lower end for the 6 UPPER_ONLY roof columns of V3.0.63; (c) the census of every B10 line still HELD in
ARCH_TAKEOFF_V3.0.63, one row each, by cause. Research only: nothing wired, nothing released (wiring is lane I).

Committed inputs (no drawing is opened here):
  candidate lines  research/agents_t665/out/LINE_INDEX_V3_0_63.json (V3.0.63, T-665 Gate B PASS, engine b5df949c)
  family census    rules/coverage/BOQ_FAMILY_MASTER_1.64.0.json candidate_census (B10-01 .. B10-12, m3)
  causes           research/agents_t658/out/T658_LEDGER.json (ground beams, columns, straps, footing),
                   research/agents_t657/out/T657_NECK_LEDGER.json, research/agents_t660/out/T660_BEAM_LEDGER.json,
                   research/agents_t659/out/T659_LEDGER.json (small B10), research/agents_t647/out/HELD_CAUSE_CENSUS_T647.json
                   (CN fix rows), research/agents_t666/out/T666_LEDGER.json, research/agents_t667/out/T667_LEDGER.json
Printed facts re-read this run (own read, Drive 'Alsenan chalet project': 'ST7757 dxf.dxf', 'p7757_arch_sheet10.pdf',
decoded into .work/private only; `t669_extract.py` prints the DXF values; sheet 10 read by eye): READS below, local
frames in m, no absolute coordinate.

    python3 -I research/agents_t669/t669_alsenan.py [--write]
"""
from __future__ import annotations

import json
import sys
from collections import OrderedDict
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import t669_rules as R  # noqa: E402

D = Decimal
RES = ROOT / "research"
INDEX = RES / "agents_t665" / "out" / "LINE_INDEX_V3_0_63.json"
MASTER = ROOT / "rules" / "coverage" / "BOQ_FAMILY_MASTER_1.64.0.json"
T647 = RES / "agents_t647" / "out" / "HELD_CAUSE_CENSUS_T647.json"
T657 = RES / "agents_t657" / "out" / "T657_NECK_LEDGER.json"
T658 = RES / "agents_t658" / "out" / "T658_LEDGER.json"
T659 = RES / "agents_t659" / "out" / "T659_LEDGER.json"
T660 = RES / "agents_t660" / "out" / "T660_BEAM_LEDGER.json"
T667 = RES / "agents_t667" / "out" / "T667_LEDGER.json"
OUT = HERE / "out" / "T669_LEDGER.json"
OUT_MD = HERE / "out" / "T669_HELD_CENSUS.md"

B10 = OrderedDict([
    ("B10-01", ("STR.CONC.BLINDING",)), ("B10-02", ("STR.CONC.FOOTING",)), ("B10-03", ("STR.CONC.NECK",)),
    ("B10-04", ("STR.CONC.GROUND_BEAM", "STR.CONC.STRAP")), ("B10-05", ("STR.CONC.GROUND_SLAB",)),
    ("B10-06", ("STR.CONC.COLUMN",)), ("B10-07", ("STR.CONC.BEAM",)), ("B10-08", ("STR.CONC.SLAB",)),
    ("B10-09", ("STR.CONC.DOME",)), ("B10-10", ("STR.CONC.LIFT", "STR.CONC.POOL")),
    ("B10-11", ("STR.CONC.BOUNDARY_PAD", "STR.CONC.BOUNDARY_WALL")), ("B10-12", ("STR.CONC.PARAPET",)),
])
CODE_FAMILY = {c: f for f, cs in B10.items() for c in cs}

# ---- (a) F-T665-1: annex SE corner (GROUND BEAMS PLAN); origin = outer corner, x along run #2, y along run #1 ------
READS_A = {
    "run1": {"name": "10B / 7D1 (BAND0012.1 + BAND0012.2)", "outer": ("0", "0", "4.90"), "inner": ("0.30", "0", "4.60"),
             "axis": "y", "spans": {"L-6bf14711ae0b84d0f8b9": ("0.30", "1.50"), "L-3284f440": ("2.00", "4.30")}},
    "run2": {"name": "F8 / 7D4 (BAND0015)", "outer": ("0", "0", "10.43"), "inner": ("0.30", "0.30", "10.50"),
             "axis": "x", "spans": {"L-402dbe61": ("0.30", "4.55")}},
    "square": ("0", "0", "0.30", "0.30"),
    "columns": {"22C": ("0", "1.50", "0.30", "2.00"), "223": ("0", "4.30", "0.30", "4.90"),
                "20B": ("4.55", "0", "4.95", "0.30"), "207": ("10.40", "0", "10.80", "0.30")},
    "touching_square": "F8, 10B, 7D1, 7D4 (layer 1) only; S-BOUN 810 / hatch 80F abut the outer corner from outside "
                       "(x -1.20 .. 0); S-AXIS 1498 (axis line, not a member); no S-COL.BON outline",
}
FLOOR_DEPTH_D35 = "0.25"   # R-T658-3 literal floor of the annex exterior G.B (+0.25 .. N.G. 0.00), D-35 high open
WIDTH = "0.30"
L_OWNER = "L-6bf14711ae0b84d0f8b9"

# ---- (b) roof columns ----------------------------------------------------------------------------------------------
READS_B = {
    "sheet10_A_A": "arch sheet 10 SECTION A-A (own render): one continuous hatched roof slab across the 2F storey, "
                   "+13.90 on its top line, parapet 50 above, storey 420 from +9.70; the arched stair window drawn "
                   "under it (scaled check only: sill ~ +10.85, apex ~ +12.58 at 1.28 cm/px, not used as a value)",
    "W26_apex": "+12.50 = printed sill +10.80 + printed 170 (PDF SE elevation chain 170 / 5 / 88 / 97 to +14.40; "
                "T-194 / RFI-1 closure, merged); the highest printed opening top on the 2F storey",
    "ST_2F_roof_plan": "SECOND FLOOR ROOF SLAB plan, one layer-1 outline 8.175 x 6.80 m holding all 8 2F column "
                       "outlines (40F / 412 / 415 / 418 / 41B / 41E / 421 / 424); inside it the only thickness texts "
                       "are 'T' / '18' (x2, handles 7B3 / 7B4, 1A7D / 1A7E) and NO level text; the two '+9.70' LEVEL "
                       "texts (3F4, 3F6) lie outside the outline (lower roofs)",
}
BASE_2F = "9.65"      # APPROVED structural datum (facts register, DESIGNER 2026-10-24/-25): not printed text
FINISHED_2F = "13.90"  # printed, arch sheet 10
W26_APEX = "12.50"
SLAB_T_2F = "0.18"
UPPER_ONLY = {  # line: (member, least section m2 = the single scheduled = drawn section, storey)
    "L-d79d17d1": ("C1 2F 20x50", "0.10", "2F"), "L-26f6b6f2": ("C2 2F 20x50", "0.10", "2F"),
    "L-33a9b772": ("C2 2F 20x50", "0.10", "2F"), "L-919a5749": ("C2 2F 20x50", "0.10", "2F"),
    "L-53f223b0": ("C9 2F 20x70", "0.14", "2F"), "L-fad18af6": ("C3 GF 25x50 (annex)", "0.125", "ANNEX"),
}


def _load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _f(v):
    return None if v is None else format(D(str(v)).quantize(R.Q6), "f")


def part_a():
    a = READS_A
    r1 = R.both_edges_box("y", a["run1"]["outer"], a["run1"]["inner"])
    r2 = R.both_edges_box("x", a["run2"]["outer"], a["run2"]["inner"])
    owner = R.corner_owner(a["square"], runs=[("run1", r1), ("run2", r2)],
                           columns=list(a["columns"].items()))
    assert owner == ("RUN", "run1"), owner
    s0, s1 = (D(v) for v in a["run1"]["spans"][L_OWNER])
    span_before = s1 - s0
    span_after = R.span_with_square(span_before, "0.30")
    before = R.prism(span_before, WIDTH, FLOOR_DEPTH_D35)
    after = R.prism(span_after, WIDTH, FLOOR_DEPTH_D35)
    return {
        "finding": "F-T665-1", "reads": a,
        "run1_both_edges_box": [_f(v) for v in r1], "run2_both_edges_box": [_f(v) for v in r2],
        "owner": {"kind": owner[0], "run": a["run1"]["name"], "line_id": L_OWNER, "member": "ground BAND0012.1"},
        "why": "10B and 7D1 (run #1) are both drawn across the square to F8 (y 0); 7D4 (run #2 inner face) stops at "
               "x 0.30 on 7D1; no column outline; R-T669-1 (b)",
        "span_m": [_f(span_before), _f(span_after)],
        "line_status": "LOWER_ONLY (D-35 high open), unchanged class",
        "floor_m3": {"before_V3_0_63": _f(before), "after": _f(after), "delta": _f(after - before)},
        "square_m3_at_floor": _f(R.prism("0.30", "0.30", FLOOR_DEPTH_D35)),
        "residual_m3": "0.000000",
        "other_lines": "BAND0012.2 L-3284f440 (2.30) and BAND0015 L-402dbe61 (5.45 + 4.25) unchanged",
    }


def part_b():
    rows, low_sum, ceil_sum = [], D(0), D(0)
    for lid, (member, sec, storey) in UPPER_ONLY.items():
        if storey == "2F":
            h_low, m3_low, h_c = R.column_low(section_min=sec, base=BASE_2F, opening_top=W26_APEX,
                                              slab_t_min=SLAB_T_2F, finished_top=FINISHED_2F, single_plane=True)
            ceil = (D(sec) * h_c).quantize(R.Q6)
            low_sum += m3_low
            ceil_sum += ceil
            rows.append({"line": lid, "member": member, "section_m2": sec, "status_after": "BOUNDED (HELD)",
                         "low_m3": _f(m3_low), "high_m3": _f(ceil), "height_m": [_f(h_low), _f(h_c)],
                         "low_basis": f"R-T669-2: {sec} x ({W26_APEX} W26 apex printed + {SLAB_T_2F} printed 2F roof "
                                      f"slab T18 - {BASE_2F} base APPROVED datum)",
                         "high_basis": "R-T658-4 ceiling unchanged (13.90 printed - 9.65 approved)",
                         "still_open": "D-39 roof slab-top level / build-up (the true height inside 3.03 .. 4.25)"})
        else:
            try:
                R.column_low(section_min=sec, base="0.25", opening_top=None, slab_t_min=None, finished_top="4.30",
                             single_plane=True)
            except R.Refused as exc:
                why = str(exc)
            ceil = (D(sec) * (D("4.30") - D("0.25"))).quantize(R.Q6)
            rows.append({"line": lid, "member": member, "section_m2": sec, "status_after": "UPPER_ONLY (HELD)",
                         "low_m3": None, "high_m3": _f(ceil),
                         "why_no_low": "R-T669-2 refused: " + why + "; the annex prints no opening head or sill "
                                       "(T-201 / T-227: 'no opening height, sill or head is printed' on the annex) "
                                       "and no annex roof slab thickness or slab-top level (Q-54 B / D-39); arch "
                                       "sheet 9 prints +0.30 / +4.30 finished only"})
    return {"rows": rows, "five_2f_low_m3": _f(low_sum), "five_2f_high_m3": _f(ceil_sum),
            "annex_ceiling_m3": "0.506250", "reads": READS_B}


# ---- (c) census ----------------------------------------------------------------------------------------------------
def _short(lid):
    return lid[:10]


def causes():
    """line_id (full) -> (cause class, named item, text, beside dict or None) from the merged ledgers."""
    out = {}
    t658 = _load(T658)
    for r in t658["rows"]:
        lid, st, item, basis = r["line_id"], r["status"], r.get("item") or "", r.get("basis") or ""
        txt = (item + " " + basis).strip()
        beside = None
        if r["item_code"] == "STR.CONC.GROUND_BEAM":
            if "BOUNDARY_GB" in r["element_id"]:
                c = ("DESIGNER ITEM", "Q-28 (RFI)")
            elif "D-33" in item:
                c = ("DESIGNER ITEM", "D-33")
            elif "D-35" in item:
                c = ("DESIGNER ITEM", "D-35")
            elif "COURT" in item:
                c = ("DESIGNER ITEM", "D-35 (court G.B depth basis; court structural top / ground level unprinted)")
            elif "NECK-CUT" in item:
                c = ("OPEN BOUND", "neck-cut sliver section not printed (R-GB-NECK-CUT-1)")
            else:
                c = ("DESIGNER ITEM", "D-34 (title precedence, 30x30 .. 30x40)")
            if st == "LOWER_ONLY":
                beside = {"AT_LEAST_M3": r["low"]}
        elif r["item_code"] == "STR.CONC.COLUMN":
            if st == "BOUNDED":
                c = ("DESIGNER ITEM", "D-66 (schedule vs drawn outline CONFLICT, held member by member)")
            elif st == "UPPER_ONLY":
                c = ("DESIGNER ITEM", "D-39" + (" / Q-54 B" if "Q-54" in item else ""))
                beside = {"AT_MOST_M3": r["high"]}
            else:
                names = ["D-39"] + [n for n in ("Q-54B", "D-44") if n in item]
                if "CONFLICT" in item:
                    names.append("D-66")
                c = ("DESIGNER ITEM", " / ".join(names))
        elif r["item_code"] == "STR.CONC.STRAP":
            c = ("DESIGNER ITEM", "Q-31 C (SB1 end inside F10 + F)") if "SB1" in r["element_id"] else \
                ("DESIGNER ITEM", "D-15 (strap soffit)")
        else:  # footing
            c = ("DESIGNER ITEM", "Q-31 C readings under the V3.0.11 conflict record (F10 + F); T-595 third reading "
                                  "named WAITING")
        out[lid] = (c[0], c[1], txt[:300], beside)
    for n in _load(T657)["necks"]:
        if n["status"] == "HELD_LOWER_ONLY":
            out[n["line_id"]] = ("DESIGNER ITEM", "D-43 / D-63 (lift raft depth, lift necks)", n["high_item"],
                                 {"AT_LEAST_M3": n["m3_low"]})
        else:
            out[n["line_id"]] = ("OPEN BOUND", "founding level not printed (ST p.9 note 1 minimum, p.13 'LESS THAN "
                                 "2.5m'; Q-21 C: decided on site with engineering approval)",
                                 (n["low_basis"] or "")[:300], None)
    for b in _load(T660)["beams"]:
        if not b["line_id"].startswith("L-"):
            continue
        di = b["designer_item"]
        out[b["line_id"]] = ("DESIGNER ITEM", f"{di} ({b['cls']})", b["basis"][:300], None)
    for r in _load(T659)["rows"]:
        out[r["line_id"]] = (None, None, (r.get("item") or "")[:300],
                             {"FLOOR_BESIDE_M3": r["floor"]["m3"]} if r.get("floor") else None)
    small = {
        "L-1d419b64": ("DESIGNER ITEM", "Q-65 C + D-39 (parapet material above the upstand; roof build-up)"),
        "L-b5ffc172": ("DESIGNER ITEM", "Q-65 C + D-39 (parapet material above the upstand; roof build-up)"),
        "L-9a2c8116": ("DESIGNER ITEM", "Q-65 C + D-39 (parapet material above the upstand; roof build-up)"),
        "L-030538dd": ("DESIGNER ITEM", "Q-65 C + D-39 (parapet material above the upstand; roof build-up)"),
        "L-cda8f415": ("DESIGNER ITEM", "Q-28 (boundary columns 'SEE ARCH PLAN', none drawn: pad count)"),
        "L-6290a9f3": ("MEASURABLE NOW", "T-659 bound 5.6392 .. 11.0328 merged (T-666 confirmed, residual 0): wire "
                                         "in T-668; then Q-28 (B.W 20x60 vs 20x40) keeps it bounded"),
        "L-080c97f5": ("DESIGNER ITEM", "Q-31 C (F10 + F readings A / B)"),
        "L-10032bf9": ("DESIGNER ITEM", "D-14 (blinding beyond the plot line)"),
        "L-16b95607": ("OPEN BOUND", "FF lift-raft blinding projection drawn, not dimensioned (ST p.14)"),
        "L-35382b18": ("DESIGNER ITEM", "D-15 (blinding under straps)"),
        "L-7a5214a3": ("DESIGNER ITEM", "D-33 / D-35 (ground-beam sections under the blinding)"),
        "L-d0313e5d": ("DESIGNER ITEM", "Q-28 (pad count; pad blinding projections not dimensioned)"),
        "L-d5401fa8": ("DESIGNER ITEM", "consultant 2026-10-24 G3 (upper-roof dome: no structural detail)"),
        "L-b62a7065": ("DESIGNER ITEM", "consultant 2026-10-23 row 3 / P-2 (pool steps not drawn)"),
        "L-5ae06fda": ("DESIGNER ITEM", "D-43 (lift tie beam section not printed)"),
        "L-684fcad3": ("DESIGNER ITEM", "D-43 (lift pit depth 'as per manufacturer')"),
    }
    for lid in list(out):
        if lid[:10] in small:
            c, n = small[lid[:10]]
            _, _, txt, beside = out[lid]
            out[lid] = (c, n, txt, beside)
    # CN columns: T-647 fix rows (schedule prints CN at foundation only)
    for fr in _load(T647)["fix_rows"]:
        out[fr["line_id"]] = ("MEASURABLE NOW", f"{fr['id']}: {fr['proposed_state']} (ST p.9 CN row: GF / 1F / 2F "
                                                "struck; DRAWING-CONFIRMED T-075); not wired",
                              fr["hand_calculation"][:300], None)
    return out


OVERRIDES_THIS_RUN = {  # what T-669 itself changes (unwired proposals)
    "L-6bf14711": {"beside_after": {"AT_LEAST_M3": "0.112500"}, "note": "T-669 (a): owns the annex SE corner square "
                   "(R-T669-1); floor 0.090 -> 0.1125; still D-35 high open"},
    "L-efd3f780": {"class": "MEASURABLE NOW", "named": "T-642 FR-T642-2 split (0.05 released at B4 0.50 + companion "
                   "0 .. 0.025, B7 alternative) merged, unwired: wire in an integration row"},
}


def census(index, master):
    by_cause = causes()
    held = [x for x in index["lines"] if x["item_code"] in CODE_FAMILY and x["class"] == "HELD"]
    b = {r["line"]: r for r in part_b()["rows"]}
    rows = []
    for x in sorted(held, key=lambda x: (CODE_FAMILY[x["item_code"]], x["item_code"], x["element_id"])):
        lid = x["line_id"]
        c = by_cause.get(lid)
        if c is None and lid[:10] in OVERRIDES_THIS_RUN and "class" in OVERRIDES_THIS_RUN[lid[:10]]:
            c = (None, None, "T-661: the T-642 split wiring carries this unsplit range (0.04 .. 0.12 = any W20 depth "
                             "0.40 .. 1.20); T-660 ledger row NEW:...BAND0030.2~T642_DEPTH_B4_B7", None)
        elif c is None or c[0] is None:
            raise SystemExit(f"no cause for {lid} {x['element_id']}")
        cls, named, txt, beside = c
        ov = OVERRIDES_THIS_RUN.get(lid[:10], {})
        row = {"family": CODE_FAMILY[x["item_code"]], "item_code": x["item_code"], "line_id": lid,
               "member": x["element_id"], "bound_V3_0_63": [_f(x["held_low"]), _f(x["held_high"])]
               if x["held_low"] is not None else None, "cause_class": ov.get("class", cls),
               "named": ov.get("named", named), "evidence": txt, "beside": beside}
        if "beside_after" in ov:
            row["beside_after_T669"] = ov["beside_after"]
            row["note"] = ov["note"]
        if lid[:10] in b and b[lid[:10]].get("low_m3"):
            row["bound_after_T669"] = [b[lid[:10]]["low_m3"], b[lid[:10]]["high_m3"]]
            row["note"] = "T-669 (b): drawn lower end R-T669-2; still D-39 inside the bound"
        rows.append(row)
    # totals per family (m3); held never summed into a released total
    fam = OrderedDict()
    for r in rows:
        f = fam.setdefault(r["family"], {"lines": 0, "bounded": 0, "low": D(0), "high": D(0), "blank": 0,
                                         "by_class": {}})
        f["lines"] += 1
        f["by_class"][r["cause_class"]] = f["by_class"].get(r["cause_class"], 0) + 1
        if r["bound_V3_0_63"]:
            f["bounded"] += 1
            f["low"] += D(r["bound_V3_0_63"][0])
            f["high"] += D(r["bound_V3_0_63"][1])
        else:
            f["blank"] += 1
    # reconcile with the master's candidate census, family by family
    cc = master["candidate_census"]["families"]
    for f, v in fam.items():
        m = cc[f]["units"]["m3"]
        assert v["lines"] == m["held_lines"], (f, v["lines"], m["held_lines"])
        assert v["blank"] == m["held_unknown_lines"], (f, v["blank"], m["held_unknown_lines"])
        assert abs(v["low"] - D(str(m["held_low"]))) < D("0.000002"), (f, v["low"], m["held_low"])
        assert abs(v["high"] - D(str(m["held_high"]))) < D("0.000002"), (f, v["high"], m["held_high"])
    for f in B10:
        m = cc[f]["units"].get("m3", {})
        assert m.get("held_lines", 0) == fam.get(f, {"lines": 0})["lines"], f
    fam_out = OrderedDict((f, {"lines": v["lines"], "bounded": v["bounded"], "bounded_low_m3": _f(v["low"]),
                               "bounded_high_m3": _f(v["high"]), "blank": v["blank"], "by_class": v["by_class"]})
                          for f, v in fam.items())
    tot = {"lines": len(rows), "bounded": sum(v["bounded"] for v in fam.values()),
           "bounded_low_m3": _f(sum(v["low"] for v in fam.values())),
           "bounded_high_m3": _f(sum(v["high"] for v in fam.values())),
           "blank": sum(v["blank"] for v in fam.values()),
           "by_class": {k: sum(1 for r in rows if r["cause_class"] == k) for k in
                        ("DESIGNER ITEM", "MEASURABLE NOW", "OPEN BOUND")}}
    assert tot["lines"] == sum(tot["by_class"].values())
    return rows, fam_out, tot


def build():
    index, master = _load(INDEX), _load(MASTER)
    assert index["candidate_version"] == "ARCH_TAKEOFF_V3.0.63"
    assert index["inputs"]["lines"].startswith("09ec4c1a")
    rows, fam, tot = census(index, master)
    pool = _load(T667)["rows"][0]
    return {
        "schema": "URBAN_T669_LEDGER_V1", "task": "T-669",
        "candidate": {"version": "ARCH_TAKEOFF_V3.0.63", "lines_sha256": index["inputs"]["lines"],
                      "index": "research/agents_t665/out/LINE_INDEX_V3_0_63.json"},
        "a_corner_square": part_a(), "b_roof_columns": part_b(),
        "c_census": {"rows": rows, "families": fam, "totals": tot,
                     "not_in_V3_0_63_named": [{"what": "pool blinding (T-667 MERGED, NEW line, unwired)",
                                               "line": pool["line_id"], "AT_LEAST_M3": pool["low"],
                                               "wiring": "T-668"}]},
        "rules": ["R-T669-1", "R-T669-2"],
    }


def markdown(doc):
    c = doc["c_census"]
    out = ["# T-669 census: every B10 line HELD in ARCH_TAKEOFF_V3.0.63, by cause (generated)", "",
           f"Lines {c['totals']['lines']}: bounded {c['totals']['bounded']} "
           f"({c['totals']['bounded_low_m3']} .. {c['totals']['bounded_high_m3']} m3), blank {c['totals']['blank']}; "
           f"by class {c['totals']['by_class']}. Held never 0, never summed into a released total.", "",
           "| Family | Lines | Bounded | low .. high m3 | Blank | By class |", "|---|---|---|---|---|---|"]
    for f, v in c["families"].items():
        out.append(f"| {f} | {v['lines']} | {v['bounded']} | {v['bounded_low_m3']} .. {v['bounded_high_m3']} | "
                   f"{v['blank']} | {', '.join(f'{k} {n}' for k, n in v['by_class'].items())} |")
    out += ["", "| Family | Line | Member | Bound V3.0.63 | Class | Named | Beside / after T-669 |",
            "|---|---|---|---|---|---|---|"]
    for r in c["rows"]:
        bnd = " .. ".join(r["bound_V3_0_63"]) if r["bound_V3_0_63"] else "blank"
        bes = []
        if r.get("beside"):
            bes.append(", ".join(f"{k} {v}" for k, v in r["beside"].items()))
        if r.get("bound_after_T669"):
            bes.append("T-669 bound " + " .. ".join(r["bound_after_T669"]))
        if r.get("beside_after_T669"):
            bes.append("T-669 " + ", ".join(f"{k} {v}" for k, v in r["beside_after_T669"].items()))
        out.append(f"| {r['family']} | {r['line_id'][:10]} | {r['member']} | {bnd} | {r['cause_class']} | "
                   f"{r['named']} | {'; '.join(bes)} |")
    return "\n".join(out) + "\n"


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    doc = build()
    text = json.dumps(doc, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    if "--write" in argv:
        OUT.parent.mkdir(exist_ok=True)
        OUT.write_text(text, encoding="utf-8")
        OUT_MD.write_text(markdown(doc), encoding="utf-8")
    t = doc["c_census"]["totals"]
    print(json.dumps({"a": doc["a_corner_square"]["floor_m3"], "b": {k: doc["b_roof_columns"][k] for k in
                      ("five_2f_low_m3", "five_2f_high_m3")}, "census": t}, indent=1))


if __name__ == "__main__":
    main()
