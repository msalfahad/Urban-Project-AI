"""T-143 hand ledger builder (research only, NOT engine code): block m2 / m3 / block counts per wall run.

Inputs (scratchpad): above.json (heights.py), t125_v2.json (MASONRY_CENTRELINE_V2 runs, T-125), the merged hand
tables T-103 (wall runs) and T-107 (block type per run). Writes the research CSVs to <out>.
Usage: python3 -I build.py <scratch> <out_dir>

Rules applied (cited per row): owner Q-60 A (block to the underside of the member above: storey - beam depth, or
storey - slab thickness; member HELD / CONFLICT -> HELD naming it), Q-69 B CONDITIONAL (five lengths), Q-65 C
(parapets / street fence HELD), UP-WALL-GEOM-001 (run to the node), UP-COL-ORIENT-001 (columns out), UP-QTY-STATUS-001
(held never 0), structural p.8 note 18 (slabs 16 cm unless stated), note 19 (tie beams round the lift at 3.00 m where the
storey exceeds 4.30 m), note 20 (designer D-12 thickness conflict, both shown elsewhere), Q-54 B (annex datum HELD).
"""
import csv
import json
import os
import sys
from collections import defaultdict

S, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
above = json.load(open(f"{S}/above.json"))
v2 = json.load(open(f"{S}/t125_v2.json"))
hand = {r["row_id"]: r for r in csv.DictReader(open(f"{S}/wb/research/agents_t103/WALLS_BY_FLOOR_THICKNESS.csv"))}
btype = {r["row_id"]: r for r in csv.DictReader(open(f"{S}/wb/research/agents_t107/BLOCK_TYPE_BY_RUN.csv"))}
vmap = list(csv.DictReader(open(f"{S}/v2map.csv")))
# candidate depths of HELD register members: the T-110 m3 range / (b x L) (Q-61 C candidates; never released)
CAND = {}
for r in csv.DictReader(open(f"{S}/wb/research/agents_t110/BEAM_MEMBER_REGISTER.csv")):
    try:
        b_, L_ = float(r["width_m"]), float(r["length_m"])
        lo, hi = float(r["m3_low"]) / (b_ * L_), float(r["m3_high"]) / (b_ * L_)
    except (TypeError, ValueError):
        continue
    a, z = CAND.get(r["member_id"], (9, 0))
    CAND[r["member_id"]] = (min(a, round(lo * 20) / 20), max(z, round(hi * 20) / 20))

# printed floor-to-floor (FFL marks, the owner's Q-60 worked example basis: GF 4.50, 1F 4.20; 2F +9.70 -> +13.90)
STOREY = {"GF": 4.50, "1F": 4.20, "2F": 4.20}
ANNEX_STOREY = 4.00          # +0.30 -> +4.30 on the marks: datum HELD (owner Q-54 B), shown PROVISIONAL only
ANNEX_X_MAX = -148.90        # GF drawing metres: the annex lies west of the 1.20 m side passage (between GF-W17 and W16)
LIFT_BOX = (-142.60, -140.30, -797.25, -794.95)   # GF lift shaft centreline box + 0.15 (walls GF-W08 / 09 / 13 / 14)
MERGE_END_M = 0.10           # a piece under another member shorter than this, at a junction, joins the band's main piece
FULL_GLAZED = {"GF-W11", "GF-W37", "1F-W25"}     # owner Q-69 B: glass lines are not blockwork
WHITE_RATES = (6.4, 8.33)    # owner Q-60 supplier sheet: 62.5 x 25 face, 60 x 20 face (blocks per m2)

# ---- run -> hand rows (T-125 V2_VS_V1_VS_HAND_BY_RUN.csv; multi-row bands split by run order) -----------------------
RUN_ROWS = {
    ("GF", "WB-FL0001-FL0002", 1): ["GF-W00"], ("GF", "WB-FL0001-FL0002", 2): ["GF-W01"],
    ("GF", "WB-FL0007-FL0008", 1): ["GF-W02"], ("GF", "WB-FL0007-FL0008", 2): ["GF-W03"],
    ("GF", "WB-FL0017-FL0018", 1): ["GF-W04"], ("GF", "WB-FL0017-FL0018", 2): ["GF-W05"],
    ("GF", "WB-FL0063-FL0064", 1): ["GF-W21"], ("GF", "WB-FL0063-FL0064", 2): ["GF-W20"],
    ("1F", "WB-FL0041-FL0042", 1): ["1F-W00"], ("1F", "WB-FL0041-FL0042", 2): ["1F-W01"],
    ("1F", "WB-FL0054-FL0055", 1): ["1F-W20"], ("1F", "WB-FL0054-FL0055", 2): ["1F-W20"],
    ("1F", "WB-FL0022-FL0023", 1): ["1F-W14", "1F-W15"],
}
for r in vmap:
    rows = [h.strip() for h in r["hand_rows"].split("+") if h.strip()]
    if rows and not any(k[:2] == (r["floor"], r["band"]) for k in RUN_ROWS):
        RUN_ROWS[(r["floor"], r["band"], 1)] = rows
RUN_ROWS[("1F", "1F-STUB-001", 1)] = ["1F-W25"]          # the bay's only masonry piece (V2 bays.masonry_pieces)

# V2 run records by (floor, band, index)
V2RUN = {}
for fl, f in v2["floors"].items():
    for r in f["v2"]["runs"]:
        rid = r["run_id"]
        if rid.startswith("BAY|"):
            V2RUN[(fl, "BAY", rid[4:])] = r
            continue
        band, _, k = rid.partition("#")
        V2RUN[(fl, band, int(k or 1))] = r


def member_height(fl, zone, key):
    """(height_m or None, status, label)"""
    storey = ANNEX_STOREY if zone == "annex" else STOREY[fl]
    sfx = " (annex: datum HELD Q-54 B, marks +0.30 -> +4.30)" if zone == "annex" else ""
    if key[0] == "BEAM":
        _, band, mid, mark, status, b, h = key
        lab = f"{mark} {mid} b {b} h {h} [{status}]"
        try:
            d = float(h)
        except ValueError:
            if mark == "CB10":       # schedule CB10 25x50: the D-02 conflict is the WIDTH (0.25 / 0.30), depth 0.50 either way
                hh = round(storey - 0.50, 3)
                return (hh, hh), "HELD", lab + f": CONFLICT D-02 on width only, schedule depth 0.50 -> candidate {hh} m"
            if mark.startswith("CB3 and B3"):   # two marks on one span (D-03): CB3 20x75 or B3 20x40
                return (round(storey - 0.75, 3), round(storey - 0.40, 3)), "HELD", lab + ": two marks D-03, candidate CB3 0.75 / B3 0.40"
            if mid in CAND:
                dlo, dhi = CAND[mid]
                return (round(storey - dhi, 3), round(storey - dlo, 3)), "HELD", lab + (
                    f": depth not printed; T-110 candidate depths {dlo:.2f} .. {dhi:.2f} (Q-61 C, designer)")
            return None, "HELD", lab + ": depth not printed / not identified (T-110 register)"
        hh = round(storey - d, 3)
        if status != "CALCULATED":
            return (hh, hh), "HELD", lab + f": member {status} in the T-110 register (Q-61 C); candidate {hh} m"
        return hh, ("PROVISIONAL" if zone == "annex" else "CALCULATED"), lab + sfx
    if key[0] == "FACE":
        _, fid, cls, t = key
        if cls == "SLAB" and t:
            hh = round(storey - float(t), 3)
            return hh, ("PROVISIONAL" if zone == "annex" else "CALCULATED"), f"slab {fid} t {t} (ST p.8 note 18 / printed tag; T-139){sfx}"
        return None, "HELD", f"{cls} face {fid} above (T-139): no beam or slab underside to stop at"
    return None, "HELD", "nothing drawn above on the roof-slab plan"


# ---- aggregate the sampled stretches per (floor, band, run index, zone) ---------------------------------------------
pieces = defaultdict(lambda: defaultdict(float))
merged_total = defaultdict(float)
samples = json.load(open(f"{S}/samples.json"))
for k, lst in samples.items():
    fl, band = k.split("|", 1)
    for run_ix, zone, lift, key, ds in lst:
        pieces[(fl, band, run_ix, zone, lift)][tuple(key)] += ds

rows_out = {}
for (fl, band, run_ix, zone, lift), d in pieces.items():
    rk = (fl, band, run_ix)
    rows = RUN_ROWS.get(rk)
    if rows is None and (fl, band, 1) in RUN_ROWS and not any(k[:2] == (fl, band) and k[2] > 1 for k in RUN_ROWS):
        rows = RUN_ROWS[(fl, band, 1)]
        run_ix = 1
    if not rows:
        continue
    tot = sum(d.values())
    main = max(d, key=d.get)
    for key in list(d):
        if key != main and d[key] < MERGE_END_M:
            d[main] += d.pop(key)
            merged_total[fl] += 0
    for row in rows:
        R = rows_out.setdefault(row, {"bands": set(), "pieces": defaultdict(float), "zones": set(), "lift_m": 0.0})
        share = 1.0 / len(rows) if len(rows) > 1 else 1.0
        if len(rows) > 1:      # split by hand lengths
            Ls = [float(hand[x]["gross_minus_columns_m"]) for x in rows]
            share = float(hand[row]["gross_minus_columns_m"]) / sum(Ls)
        R["bands"].add(f"{band}#{run_ix}")
        R["zones"].add(zone)
        for key, ds in d.items():
            R["pieces"][(zone,) + key] += ds * share
        if lift:
            R["lift_m"] += tot * share

# ---- one row per hand wall run ---------------------------------------------------------------------------------------
fields = ["row_id", "floor", "zone", "group", "t_m", "block_type", "type_source", "type_status",
          "L1_arch_run_m", "L2a_q69_physical_m", "L2b_plan_cut_solid_m", "L3_glass_alu_m", "openings_other_m",
          "L4_masonry_above_below", "members_above", "height_m_weighted", "sampled_m", "held_len_m",
          "gross_m2_owner_run", "gross_m2_q69_physical", "held_m2_candidate", "m3_q69_physical", "status", "reason",
          "white_blocks_6.4", "white_blocks_8.33", "net_m2", "v2_runs"]
OUTROWS = []
for rid, h in hand.items():
    if rid == "TOTAL" or rid.startswith(("P-", "F-")):
        continue
    fl = h["floor"]
    t = float(h["thickness_m"] or 0)
    L1 = float(h["gross_minus_columns_m"] or 0)
    solid = float(h["solid_m"] or 0)
    L2a = solid if rid in FULL_GLAZED else L1
    bt = btype.get(rid, {})
    R = rows_out.get(rid)
    v2r = []
    glass = 0.0
    other = 0.0
    for (f2, band, ix), rows in RUN_ROWS.items():
        if f2 == fl and rid in rows:
            rr = V2RUN.get((fl, band, ix))
            if rr:
                share = 1.0 / len(rows)
                glass += rr["glass_aluminium_lm"] * share
                other += (rr["openings_lm"] - rr["glass_aluminium_lm"]) * share
                v2r.append(rr["run_id"])
    if rid == "1F-W25":
        rr = V2RUN.get(("1F", "BAY", "WB-FL0041-FL0042"))
        glass = rr["glass_aluminium_lm"] if rr else 0
        v2r.append("BAY|WB-FL0041-FL0042")
    if rid in ("GF-W11", "GF-W37"):
        glass = L1 - solid
    row = {"row_id": rid, "floor": fl, "zone": h["zone"], "group": h["group"], "t_m": h["thickness_m"],
           "block_type": bt.get("block_type", ""), "type_source": bt.get("source", ""),
           "type_status": bt.get("status", ""), "L1_arch_run_m": L1, "L2a_q69_physical_m": round(L2a, 3),
           "L2b_plan_cut_solid_m": solid, "L3_glass_alu_m": round(glass, 3), "openings_other_m": round(other, 3),
           "L4_masonry_above_below": "HELD (Q-69 B (4): head / sill heights or elevations, T-144)" if glass > 0 else "none (no glazing in run)",
           "v2_runs": " ".join(v2r)}
    if not R or h["status"].startswith("HELD"):
        why = h["note"][:120] if h["status"].startswith("HELD") else (
            "no wall band on the plan run (T-125 MISSING: the wall stage forms no band), member above not bound"
            if rid == "GF-W30" else "glazed line, no wall band: member above not bound by this run")
        row.update(status="HELD", reason=why, net_m2="HELD", held_len_m=L2a,
                   gross_m2_owner_run="HELD", gross_m2_q69_physical="HELD", m3_q69_physical="HELD",
                   held_m2_candidate="", members_above="not bound")
        if rid == "GF-H01" and R:
            ps = R["pieces"]
            row["members_above"] = "; ".join(f"{member_height(fl, k[0], k[1:])[2]}: {v:.2f} m" for k, v in ps.items())
        OUTROWS.append(row)
        continue
    ps = R["pieces"]
    S_len = sum(ps.values())
    scale1 = L1 / S_len if S_len else 0
    scale2 = L2a / S_len if S_len else 0
    m2a = m2b = held_len = 0.0
    held_lo = held_hi = 0.0
    held_unknown = 0.0
    labs, st, reasons = [], set(), []
    for k, v in sorted(ps.items(), key=lambda kv: -kv[1]):
        zone = k[0]
        hh, s, lab = member_height(fl, zone, k[1:])
        hs = (f" -> h {hh:.2f}" if isinstance(hh, float) else (f" -> h HELD (candidate {hh[0]:.2f}" + (f"-{hh[1]:.2f}" if hh[1] != hh[0] else "") + ")" if hh else " -> h HELD"))
        labs.append(f"{lab}: {v:.2f} m" + hs)
        st.add(s)
        if s in ("CALCULATED", "PROVISIONAL"):
            m2a += v * scale1 * hh
            m2b += v * scale2 * hh
        else:
            held_len += v * scale2
            if hh:
                held_lo += v * scale2 * hh[0]
                held_hi += v * scale2 * hh[1]
            else:
                held_unknown += v * scale2
            reasons.append(lab)
    if fl == "GF" and R["lift_m"] > 0.30:
        st.add("PROVISIONAL")
        reasons.append(f"lift-shaft wall {R['lift_m']:.2f} m sampled: structural p.8 note 19 tie beam at 3.00 m (GF storey "
                       f"4.50 > 4.30), its size not printed: deduction HELD, gross PROVISIONAL")
    if "annex" in R["zones"]:
        reasons.append("annex datum HELD (owner Q-54 B): heights on the printed marks, PROVISIONAL")
    status = "HELD" if st == {"HELD"} else ("PARTLY HELD" if "HELD" in st else
                                             ("PROVISIONAL" if "PROVISIONAL" in st else "CALCULATED"))
    hw = (m2b / (L2a - held_len)) if (L2a - held_len) > 1e-9 else None
    row.update(members_above="; ".join(labs), height_m_weighted=round(hw, 3) if hw else "",
               sampled_m=round(S_len, 3), held_len_m=round(held_len, 3),
               gross_m2_owner_run=round(m2a, 3), gross_m2_q69_physical=round(m2b, 3),
               held_m2_candidate=(f"{held_lo:.3f}" + (f"-{held_hi:.3f}" if abs(held_hi - held_lo) > 1e-6 else "") +
                                  (f" + {held_unknown:.3f} m with no candidate height" if held_unknown > 1e-6 else "")) if held_len else "",
               m3_q69_physical=round(m2b * t, 4), status=status, reason=" | ".join(reasons),
               net_m2="HELD (no Urban masonry opening rule: UP-GEN-003 table has no MASONRY row)")
    if bt.get("block_type") == "WHITE":
        row["white_blocks_6.4"] = round(m2b * WHITE_RATES[0], 1)
        row["white_blocks_8.33"] = round(m2b * WHITE_RATES[1], 1)
    elif bt.get("block_type") == "BLACK":
        row["white_blocks_6.4"] = "n/a: black block, no supplier face size given (HELD)"
    OUTROWS.append(row)

with open(f"{OUT}/T143_BLOCK_BY_WALL_RUN.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=fields)
    w.writeheader()
    for r in OUTROWS:
        w.writerow(r)
json.dump(OUTROWS, open(f"{S}/t143_rows.json", "w"), indent=1, default=str)
print(len(OUTROWS), "rows")
