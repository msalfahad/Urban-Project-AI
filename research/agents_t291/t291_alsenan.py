"""T-291 Alsenan (development villa) wall-to-line ledger: blockwork register v4 (T-288, MERGED 643b310b) wall by wall
against the ARCH_TAKEOFF_V3.0.15 candidate's masonry line ids (= the T-245 V3.0.16 lines, byte-identical), with the
opening deductions by opening id. Research only: no engine module, candidate line or released line changes; lane I
(T-279) applies it.

    python3 -I research/agents_t291/t291_alsenan.py --extract <run>/v3015      # writes CANDIDATE_V3015_MASONRY_LINES.json
    python3 -I research/agents_t291/t291_alsenan.py --write                    # writes the ledger files
    python3 -I research/agents_t291/t291_alsenan.py --check                    # rebuilds in memory, compares bytes

Inputs (committed): research/agents_t288/BLOCKWORK_WALL_REGISTER_V4.csv; CANDIDATE_V3015_MASONRY_LINES.json (line id,
item code, storey, element, unit, state, quantity, RFI text; no coordinates, no names); the opening table below, each
row citing the merged ledger it comes from (T-175 / T-227 / T-261 / T-274 / T-288).
"""
from __future__ import annotations

import argparse
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
import wall_line_ledger as R  # noqa: E402

REGISTER = ROOT / "research" / "agents_t288" / "BLOCKWORK_WALL_REGISTER_V4.csv"
CANDIDATE = HERE / "CANDIDATE_V3015_MASONRY_LINES.json"
SCHEMA = "T291_BLOCKWORK_WALL_TO_LINE_LEDGER_V1"
MASONRY_ITEMS = ("ARCH.WALL_PANEL", "ARCH.WALL_VOLUME", "MAS.BLOCK", "ARCH.WALL_RUN")
AREA_VOLUME = ("ARCH.WALL_PANEL", "MAS.BLOCK", "ARCH.WALL_VOLUME")

# --- opening deductions by opening id (register v4 hosts) -------------------------------------------------------
# (opening_id, host wall, deduction m2 or None, state, source). DEDUCTED = in a carried net or in a drop wall's U;
# ON_HELD_WALL = established deduction on a HELD wall (shown, summed nowhere); IN_HELD_PIECE = in the held piece of an
# ESTABLISHED PART + HELD wall; HELD = the deduction itself not established; NOT_APPLICABLE = the host builds no
# masonry; NO_HOST = in no register wall.
T175 = "T-175 T175_OPENING_CONSEQUENCES.csv"
T227 = "T-227 s.6 opening heights (T-227_ANNEX_LIFT_STRIPS_DOMES_HEADS.md)"
T261 = "T-261 T261_SPLIT.csv piece"
OPENINGS = [
    ("D-GF-03", "GF-W04", 1.980, "ON_HELD_WALL", T175 + " (ASSUMED - OWNER-APPROVED head)"),
    ("W04", "GF-W04", 0.480, "ON_HELD_WALL", T227),
    ("W08", "GF-W04", 2.250, "ON_HELD_WALL", T227),
    ("D-GF-06", "GF-W05", 2.200, "DEDUCTED", T175 + " (ASSUMED - OWNER-APPROVED head)"),
    ("D-GF-01", "GF-W06", 2.200, "ON_HELD_WALL", T175 + " (ASSUMED - OWNER-APPROVED head)"),
    ("D-GF-08", "GF-W08", 2.200, "ON_HELD_WALL", T175 + " (ASSUMED - OWNER-APPROVED head)"),
    ("L-GF-01", "GF-W08", None, "HELD", T175 + " (width or height not established)"),
    ("W05", "GF-W10", 0.480, "DEDUCTED", T261 + " E1 CB2 span 1"),
    ("W06", "GF-W10", 0.480, "DEDUCTED", T261 + " E1 CB2 span 1"),
    ("W07", "GF-W10", 0.480, "DEDUCTED", T261 + " E2 CB2 span 2"),
    ("D-GF-09", "GF-W10", 1.980, "IN_HELD_PIECE", T261 + " SF B3 (With Stair) stair-foot (HELD)"),
    ("W02", "GF-W11", None, "NOT_APPLICABLE", T175 + " (host GLAZED: no masonry built in the line)"),
    ("P-GF-01", "GF-W14", None, "HELD", T175 + " (doorless opening, width or height not established)"),
    ("W01", "GF-W15", 2.400, "ON_HELD_WALL", T175 + " (DRAWING-CONFIRMED)"),
    ("D-GF-07", "GF-W15", None, "HELD", T175 + " (width or height not established)"),
    ("W09", "GF-W16", 2.250, "DEDUCTED", T227 + "; wall HELD ON DROP: in its U"),
    ("W10", "GF-W16", 1.500, "DEDUCTED", T227 + "; wall HELD ON DROP: in its U"),
    ("D-GF-05", "GF-W17", 2.200, "ON_HELD_WALL", T175 + " (ASSUMED - OWNER-APPROVED head)"),
    ("W11", "GF-W18", 4.290, "ON_HELD_WALL", T227 + " (1.95 x 2.20, T-201)"),
    ("W12", "GF-W18", 4.290, "ON_HELD_WALL", T227 + " (1.95 x 2.20, T-201)"),
    ("D-GF-04", "GF-W24", 1.760, "ON_HELD_WALL", T175 + " (ASSUMED - OWNER-APPROVED head)"),
    ("A-GF-01", "GF-W26", None, "HELD", T175 + " (width or height not established)"),
    ("D-GF-02", "GF-W27", 1.760, "ON_HELD_WALL", T175 + " (ASSUMED - OWNER-APPROVED head)"),
    ("D-GF-13", "GF-W28", 2.200, "DEDUCTED", T175 + " (ASSUMED - OWNER-APPROVED head)"),
    ("D-GF-10", "GF-W29", 1.760, "DEDUCTED", T175 + " (ASSUMED - OWNER-APPROVED head)"),
    ("D-GF-14", "GF-W30", None, "HELD", T175 + " (no V2 band; width or height not established)"),
    ("D-GF-11", "GF-W32", 1.760, "DEDUCTED", T175 + " (ASSUMED - OWNER-APPROVED head); wall HELD ON DROP: in its U"),
    ("D-GF-12", "GF-W32", 1.760, "DEDUCTED", T175 + " (ASSUMED - OWNER-APPROVED head); wall HELD ON DROP: in its U"),
    ("W03", "GF-W37", None, "NOT_APPLICABLE", T175 + " (host GLAZED); its WINDOW line is T-255 (owner Q-76 A)"),
    ("W15", "1F-W00", 4.363, "DEDUCTED", "T-274 s.4 (arched outline 4.363); wall VERIFIED Checker 2026-10-25 02:01"),
    ("W16", "1F-W00", 4.363, "DEDUCTED", "T-274 s.4 (arched outline 4.363); wall VERIFIED Checker 2026-10-25 02:01"),
    ("W18", "1F-W00", 1.0094, "DEDUCTED", "T-274 s.4: 0.4673 m inside the masonry x 2.160 (not 0.50 x 2.16 = 1.080); "
                                         "its WINDOW line is T-255"),
    ("W13", "1F-W04", 2.760, "DEDUCTED", T261 + " E B2 BM-1F-006"),
    ("W14", "1F-W05", 3.920, "DEDUCTED", T175 + "; wall VERIFIED Checker 2026-10-25 02:06 (W14 2.4498 x 1.60)"),
    ("W19", "1F-W06", 0.480, "DEDUCTED", T227),
    ("W20", "1F-W06", 0.480, "DEDUCTED", T227),
    ("W24", "1F-W06", 2.32845, "DEDUCTED", "T-288 s.3: drawn jamb 1.5523 x 1.50 (T-227 1.55 x 1.50 = 2.325 + 0.0035); "
                                          "wall VERIFIED Checker 2026-10-25 02:03"),
    ("D-1F-05", "1F-W07", 1.980, "ON_HELD_WALL", T175 + " (ASSUMED - OWNER-APPROVED head)"),
    ("L-1F-01", "1F-W07", None, "HELD", T175 + " (width or height not established)"),
    ("W21", "1F-W10", 0.480, "DEDUCTED", T261 + " E1 CB9 span 1"),
    ("W22", "1F-W10", 0.480, "DEDUCTED", T261 + " E1 CB9 span 1"),
    ("W23", "1F-W10", 0.480, "DEDUCTED", T261 + " E2 CB9 span 2"),
    ("W25", "1F-W10", 1.500, "IN_HELD_PIECE", T261 + " SF B3 (With Stair) (HELD)"),
    ("D-1F-01", "1F-W11", 1.760, "ON_HELD_WALL", T175 + " (ASSUMED - OWNER-APPROVED head)"),
    ("D-1F-03", "1F-W12", 2.200, "DEDUCTED", T175 + " (ASSUMED - OWNER-APPROVED head)"),
    ("D-1F-08", "1F-W13", 1.980, "DEDUCTED", T261 + " E slab 1F-065 (spans three pieces)"),
    ("D-1F-09", "1F-W13", 1.980, "IN_HELD_PIECE", T261 + " H east dome opening 1F-077 (HELD)"),
    ("P-1F-01", "1F-W14 + 1F-W15", None, "HELD", "register v2 (T-228) held opening of the HELD wall; T-175 read it "
                                                "outside the measured run (both readings kept, the wall is HELD)"),
    ("D-1F-06", "1F-W16", 1.760, "ON_HELD_WALL", T175 + " (ASSUMED - OWNER-APPROVED head)"),
    ("A-1F-01", "1F-W16", None, "HELD", T175 + " (width or height not established)"),
    ("D-1F-10", "1F-W17", 1.760, "DEDUCTED", T261 + " E slab 1F-057 (spans three pieces)"),
    ("D-1F-07", "1F-W19", 1.760, "DEDUCTED", T175 + " (ASSUMED - OWNER-APPROVED head)"),
    ("D-1F-02", "1F-W23", 2.200, "DEDUCTED", T175 + " (ASSUMED - OWNER-APPROVED head)"),
    ("D-1F-04", "1F-W23", 1.760, "DEDUCTED", T175 + " (ASSUMED - OWNER-APPROVED head)"),
    ("W17", "1F-W25", None, "NOT_APPLICABLE", T175 + " (host GLAZED: concave glazed bay)"),
    ("L-2F-01", "2F-W00", None, "HELD", T175 + " (width or height not established)"),
    ("W28", "2F-W02", 0.480, "DEDUCTED", T261 + " E1 B8"),
    ("W29", "2F-W02", 1.800, "DEDUCTED", T261 + " E1 B8"),
    ("W27", "2F-W02", 1.500, "IN_HELD_PIECE", T261 + " SF B3 (HELD)"),
    ("D-2F-01", "2F-W03", 2.200, "DEDUCTED", T261 + " E B2 BM-2F-004"),
    ("D-2F-02", "2F-W05", 1.980, "IN_HELD_PIECE", T261 + " H BM-2F-017 (HELD)"),
    ("W26", "2F-W07", 1.875, "DEDUCTED", T261 + " E B15 BM-2F-007 (supersedes T-175 2.040)"),
    ("D-2F-03", "2F-W08", 1.760, "DEDUCTED", T175 + " (ASSUMED - OWNER-APPROVED head)"),
    ("D-GF-15", "", None, "NO_HOST", T175 + " (gate in the fence: no masonry built in the line)"),
    ("SX-01", "", None, "NO_HOST", T175 + " (outside the measured gross run)"),
    ("SX-03", "", None, "NO_HOST", T175 + " (outside the measured gross run)"),
    ("U-01", "", None, "NO_HOST", T175 + " (identity not established)"),
    ("P-GF-02", "", None, "NO_HOST", T175 + " (open side between jambs)"),
    ("P-GF-03", "", None, "NO_HOST", T175 + " (open side in no run)"),
    ("P-GF-04", "", None, "NO_HOST", T175 + " (open side in no run)"),
    ("P-GF-05", "", None, "NO_HOST", T175 + " (open side; the register's 'GF P-GF-05 ABOVE-LINTEL' piece is the "
                                     "masonry over it, not a deduction)"),
]
# register deduction per wall (m2): v3 deductions_m2_v3 (T-285) with the v4 correction of 1F-W06 (T-288 W24 jamb)
DEDUCTION_OVERRIDES_V4 = {"1F-W06": 3.28845}


def _f(v):
    return None if v in (None, "") else float(v)


def register_walls():
    v3 = {r["wall_id"]: r for r in csv.DictReader(open(ROOT / "research/agents_t285/BLOCKWORK_WALL_REGISTER_V3.csv",
                                                       encoding="utf-8"))}
    out = []
    for r in csv.DictReader(open(REGISTER, encoding="utf-8")):
        w = {"wall_id": r["wall_id"], "floor": r["floor"], "t_m": float(r["t_m"]), "block_type": r["block_type"],
             "group": r["group"], "length_m": float(r["length_m"]), "basis": r["basis"] or None,
             "state": r["state_v4"], "class": r["class_v4"], "net_m2": _f(r["net_m2_v4"]),
             "upper_m2": _f(r["upper_m2_v4"]), "drop_length_m": _f(r["drop_length_m"]),
             "verified_by": r["verified_by_v4"] or None, "conflict": r["conflict"] or None,
             "conflict_increment_m2": _f(r["conflict_increment_m2"]), "held_items": r["held_items"] or None}
        if w["class"] == "VERIFIED" and w["verified_by"] and "WITHDRAWN" in w["verified_by"]:
            w["verified_by"] = None
        d = DEDUCTION_OVERRIDES_V4.get(w["wall_id"], _f((v3.get(w["wall_id"]) or {}).get("deductions_m2_v3")))
        w["deductions_m2"] = d
        out.append(w)
    return out


def openings():
    return [{"opening_id": o, "host": h, "deduction_m2": d, "state": s, "source": src}
            for o, h, d, s, src in OPENINGS]


def _family(element_id):
    m = re.search(r"walls t=([0-9.]+)", element_id or "")
    return R.family_key(m.group(1)) if m else None


# --- extract (needs a finished V3.0.15 run, outside the repository) --------------------------------------------
def extract(run_dir):
    run = Path(run_dir)
    src = run / "V3_0_15_BOQ_LINES.json"
    d = json.loads(src.read_text(encoding="utf-8"))
    L = d if isinstance(d, list) else d["lines"]
    keep = []
    for l in L:
        if l["item_code"] not in MASONRY_ITEMS and l.get("trade") != "MASONRY":
            continue
        c = l.get("calculation") or {}
        i = c.get("inputs") or {}
        keep.append({"line_id": l["line_id"], "item_code": l["item_code"], "trade": l.get("trade"),
                     "floor": l["location"]["floor"], "element_id": l["location"]["element_id"], "unit": l["unit"],
                     "evidence_state": l["evidence_state"], "measured_net": l.get("measured_net"),
                     "bounded_range": l.get("bounded_range"), "formula": c.get("formula"),
                     "walls_in_line": i.get("walls"), "rfi_question": (l.get("rfi") or {}).get("question"),
                     "source_wall_band_entities": len(((l.get("source") or {}).get("entities") or {}).get("entities")
                                                      or ()),
                     "project_id": (l.get("project") or {}).get("project_id"),
                     "revision_set_sha256": (l.get("project") or {}).get("revision_set_sha256")})
    csv_p = run / "V3_0_15_BOQ_LINES.csv"
    out = {"task": "T-291", "candidate": "ARCH_TAKEOFF_V3.0.15",
           "candidate_lines_json_sha256": hashlib.sha256(src.read_bytes()).hexdigest(),
           "candidate_lines_csv_sha256": hashlib.sha256(csv_p.read_bytes()).hexdigest() if csv_p.exists() else None,
           "lines_total": len(L), "masonry_lines": keep}
    CANDIDATE.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return out


def candidate():
    return json.loads(CANDIDATE.read_text(encoding="utf-8"))


# --- build -----------------------------------------------------------------------------------------------------
def build():
    cand = candidate()
    walls = register_walls()
    ops = openings()
    lines = []
    for l in cand["masonry_lines"]:
        fam = _family(l["element_id"])
        lines.append(dict(l, family=fam, quantity=l["measured_net"]))
    av = [l for l in lines if l["item_code"] in AREA_VOLUME]
    binding, unmatched_w, unmatched_l = R.bind(walls, av)
    rows = R.ledger_rows(walls, av, binding)
    closures = {it: R.closure(walls, rows, it, "m3" if it == "ARCH.WALL_VOLUME" else "m2")
                for it in sorted({l["item_code"] for l in av})}
    per_wall_deductions = R.opening_ledger(ops, walls)
    # per line summary
    summ = []
    for l in sorted(av, key=lambda x: (x["item_code"], x["floor"], x["family"] or "")):
        rr = [r for r in rows if r["line_id"] == l["line_id"]]
        t = {s: round(sum(r["carried"] for r in rr if r["status"] == s and r["carried"] is not None), 6)
             for s in R.STATUSES}
        summ.append({
            "line_id": l["line_id"], "item_code": l["item_code"], "unit": l["unit"], "floor": l["floor"],
            "family": l["family"], "engine_state": l["evidence_state"], "engine_quantity": l["measured_net"],
            "engine_rfi": (l["rfi_question"] or "")[:160],
            "walls": len(rr), "walls_ids": " ".join(r["wall_id"] for r in rr),
            "verified": t[R.VERIFIED], "drawing_confirmed": t[R.DC], "owner_approved": t[R.AOA],
            "determinate": round(t[R.VERIFIED] + t[R.DC] + t[R.AOA], 6),
            "part_plus_held_part": t[R.PART_PLUS_HELD],
            "drop_upper_at_d0": round(sum(r["upper"] or 0 for r in rr if r["status"] == R.HELD_ON_DROP), 6),
            "drop_coefficient": round(sum(r["drop_coefficient"] or 0 for r in rr if r["status"] == R.HELD_ON_DROP), 6),
            "held_walls": " ".join(r["wall_id"] for r in rr if r["status"] == R.HELD),
            "conflict_increments_outside": round(sum(r["conflict_increment"] or 0 for r in rr), 6),
            "line_expression": _expr(rr, l["unit"])})
    run_rows = wall_run_lengths(walls, [l for l in lines if l["item_code"] == "ARCH.WALL_RUN"])
    return {"candidate": cand, "walls": walls, "lines": lines, "rows": rows, "unmatched_walls": unmatched_w,
            "unmatched_lines": unmatched_l, "closures": closures, "deductions": per_wall_deductions,
            "openings": ops, "summary": summ, "runs": run_rows}


def _expr(rr, unit):
    det = sum(r["carried"] or 0 for r in rr if r["status"] in R.DETERMINATE)
    part = sum(r["carried"] or 0 for r in rr if r["status"] == R.PART_PLUS_HELD)
    up = sum(r["upper"] or 0 for r in rr if r["status"] == R.HELD_ON_DROP)
    co = sum(r["drop_coefficient"] or 0 for r in rr if r["status"] == R.HELD_ON_DROP)
    held = [r["wall_id"] for r in rr if r["status"] in (R.HELD, R.PART_PLUS_HELD)]
    s = f"{det:.4f} determinate"
    if part:
        s += f" + {part:.4f} established parts"
    if co:
        s += f" + ({up:.4f} - {co:.4f} x d) drop walls"
    if held:
        s += f" + HELD [{len(held)} walls / pieces, blank]"
    return s + f" {unit}"


def wall_run_lengths(walls, run_lines):
    """the length item (ARCH.WALL_RUN, lm, the engine's net band run) beside the register's census length per storey
    and family: a comparison only (the run is the line's geometry, coverage_census B9-01), never a carried figure."""
    out = []
    for l in sorted(run_lines, key=lambda x: (x["floor"], x["family"] or "")):
        ws = [w for w in walls if w["floor"] == l["floor"] and R.family_key(w["t_m"]) == l["family"]]
        census = round(sum(w["length_m"] for w in ws), 4)
        out.append({"line_id": l["line_id"], "floor": l["floor"], "family": l["family"],
                    "engine_run_lm": l["measured_net"], "engine_walls": l["walls_in_line"],
                    "register_walls": len(ws), "register_census_lm": census,
                    "difference_lm": None if l["measured_net"] is None else round(l["measured_net"] - census, 4)})
    return out


# --- outputs ---------------------------------------------------------------------------------------------------
LEDGER_COLS = ["schema", "project_id", "revision_set_sha256", "candidate", "line_id", "item_code", "unit", "floor",
               "family", "wall_id", "block_type", "status", "share", "carried", "upper_at_d0", "drop_length_m",
               "drop_coefficient", "part_status", "verified_by", "held_item", "conflict", "conflict_increment_outside",
               "opening_deductions"]


def _csv(rows, cols):
    b = io.StringIO()
    w = csv.DictWriter(b, fieldnames=cols, lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in cols})
    return b.getvalue()


def _num(v, nd=4):
    return None if v is None else f"{v:.{nd}f}"


def outputs(B):
    proj = next((l for l in B["candidate"]["masonry_lines"]), {})
    ops_by_host = {}
    for o in B["openings"]:
        if o["state"] in ("DEDUCTED", "ON_HELD_WALL", "IN_HELD_PIECE", "HELD"):
            ops_by_host.setdefault(o["host"], []).append(
                f"{o['opening_id']} {'' if o['deduction_m2'] is None else format(o['deduction_m2'], '.4f')} "
                f"{o['state']}".replace("  ", " "))
    led = []
    for r in sorted(B["rows"], key=lambda r: (r["item_code"], r["floor"], r["family"], r["wall_id"])):
        nd = 6 if r["unit"] == "m3" else 4
        led.append({"schema": SCHEMA, "project_id": proj.get("project_id"),
                    "revision_set_sha256": proj.get("revision_set_sha256"), "candidate": B["candidate"]["candidate"],
                    "line_id": r["line_id"], "item_code": r["item_code"], "unit": r["unit"], "floor": r["floor"],
                    "family": r["family"], "wall_id": r["wall_id"], "block_type": r["block_type"],
                    "status": r["status"], "share": f"{r['share']:g}", "carried": _num(r["carried"], nd),
                    "upper_at_d0": _num(r["upper"], nd), "drop_length_m": _num(r["drop_length_m"]),
                    "drop_coefficient": _num(r["drop_coefficient"], nd), "part_status": r["part_status"],
                    "verified_by": r["verified_by"], "held_item": r["held_item"], "conflict": r["conflict"],
                    "conflict_increment_outside": _num(r["conflict_increment"], nd),
                    "opening_deductions": "; ".join(ops_by_host.get(r["wall_id"], []))})
    files = {
        "WALL_TO_LINE_LEDGER_T291.csv": _csv(led, LEDGER_COLS),
        "LINE_SUMMARY_T291.csv": _csv(B["summary"], list(B["summary"][0])),
        "OPENING_DEDUCTIONS_T291.csv": _csv([dict(o, deduction_m2=_num(o["deduction_m2"], 5)) for o in B["openings"]],
                                            ["opening_id", "host", "deduction_m2", "state", "source"]),
        "WALL_RUN_LENGTHS_T291.csv": _csv(B["runs"], list(B["runs"][0])) if B["runs"] else "",
    }
    det = {s: round(sum(w["net_m2"] for w in B["walls"] if R.wall_status(w) == s), 4) for s in R.DETERMINATE}
    summary = {
        "task": "T-291", "rule": R.RULE_ID, "candidate": B["candidate"]["candidate"],
        "candidate_lines_csv_sha256": B["candidate"]["candidate_lines_csv_sha256"],
        "candidate_lines_json_sha256": B["candidate"]["candidate_lines_json_sha256"],
        "register_v4_csv_sha256": hashlib.sha256(REGISTER.read_bytes()).hexdigest(),
        "walls": len(B["walls"]), "masonry_lines": len(B["lines"]),
        "area_volume_lines": len({r["line_id"] for r in B["rows"]}) + len(B["unmatched_lines"]),
        "ledger_rows": len(B["rows"]),
        "unmatched_walls": B["unmatched_walls"], "unmatched_lines": B["unmatched_lines"],
        "engine_lines_with_quantity": sum(1 for l in B["lines"] if l["item_code"] in AREA_VOLUME
                                          and l["measured_net"] is not None),
        "by_status_m2": {**det,
                         "ESTABLISHED PART (basis B)": round(sum(w["net_m2"] for w in B["walls"]
                                                                 if R.wall_status(w) == R.PART_PLUS_HELD), 4),
                         "HELD ON DROP upper at d=0 (not a quantity)": round(sum(
                             w["upper_m2"] for w in B["walls"] if R.wall_status(w) == R.HELD_ON_DROP), 4),
                         "HELD ON DROP length (m)": round(sum(
                             w["drop_length_m"] for w in B["walls"] if R.wall_status(w) == R.HELD_ON_DROP), 4)},
        "held_walls": sorted(w["wall_id"] for w in B["walls"] if R.wall_status(w) == R.HELD),
        "closures": B["closures"],
        "openings": {s: sum(1 for o in B["openings"] if o["state"] == s)
                     for s in ("DEDUCTED", "ON_HELD_WALL", "IN_HELD_PIECE", "HELD", "NOT_APPLICABLE", "NO_HOST")},
        "deductions_by_wall_m2": B["deductions"],
    }
    files["summary.json"] = json.dumps(summary, indent=1, ensure_ascii=False) + "\n"
    return files


def main(argv=None):
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--extract")
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    if a.extract:
        out = extract(a.extract)
        print(f"masonry lines {len(out['masonry_lines'])} of {out['lines_total']}; csv {out['candidate_lines_csv_sha256'][:8]}")
        return 0
    files = outputs(build())
    if a.write:
        for n, s in files.items():
            (HERE / n).write_text(s, encoding="utf-8")
        print("written:", ", ".join(files))
        return 0
    bad = [n for n, s in files.items() if not (HERE / n).exists() or (HERE / n).read_text(encoding="utf-8") != s]
    print("CHECK", "FAIL " + ", ".join(bad) if bad else "PASS")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
