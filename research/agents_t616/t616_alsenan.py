"""T-616 training villa: statement V10 row T-571/lintel-count-implied (his 54 vs engine 60 AT_MOST, -6 nr) closed
opening by opening through R-T616-1 (t616_rules.py). Research only, unwired; no engine / rule / registry file changed.

Inputs (merged records, pinned by sha256[:16]; no private file is read here):
  research/agents_t571/out/T571_LINTEL_COUNT.json   engine openings (68: 60 in the lintel list + 8 NO_LINTEL)
  research/agents_t453/out/MATERIAL_LEDGER_T453.json lintel decisions, host walls, door clear-height margins
  research/agents_t198/OPENINGS_T198.csv             census r3 identity keys (certain keys only)
His side: his masonry workbook's deduction list (Drive 'Alsenan chalet project', blockwork workbook, read this run with
the Drive text reader) as counts by width per section, the same figures T-571 / T-559 already carry (no names).
Drawing evidence per opening is quoted from merged records (T-581 both faces, T-601 own reads, S8.6 bearing audit,
T-198 notes, T-302 band radii); the Checker re-reads three openings from the DXF.

Usage: python3 -I research/agents_t616/t616_alsenan.py [--check]
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import t616_rules as R  # noqa: E402

OUT = HERE / "out" / "T616_RESIDUAL.json"
IN = {
    "t571": ("research/agents_t571/out/T571_LINTEL_COUNT.json", "ede7c1fd982e42f9"),
    "ledger": ("research/agents_t453/out/MATERIAL_LEDGER_T453.json", "ad9bceee3bfdbc12"),
    "census": ("research/agents_t198/OPENINGS_T198.csv", "d79e6aa5d23edc0e"),
}

# his deduction list by section (each width one deducted opening; storey from his headings; his 20 cm section repeats
# the same five wall lengths on GF / 1F / 2F = the stacked lift shaft, T-559 s.1, so its openings form one group)
THEIRS = [
    {"group": "GF_EXT", "widths": [1.00] * 5 + [0.60] * 4 + [1.50] * 2 + [2.00, 1.20] + [1.95] * 2},
    {"group": "1F_EXT", "widths": [1.00] + [0.60] * 6 + [3.15] + [1.55] * 3 + [2.45, 1.20]},
    {"group": "2F_EXT", "widths": [1.00, 1.20, 0.60, 1.00, 1.20]},
    {"group": "GF_15", "widths": [0.80] * 6 + [1.00]},
    {"group": "1F_15", "widths": [0.80] * 4 + [0.90] * 4},
    {"group": "2F_15", "widths": [0.80, 0.90]},
    {"group": "SHAFT_20", "widths": [1.00] * 3 + [1.10]},
]

# openings in the lift-shaft walls (hosts GF-W08 / 1F-W07 / 2F-W00 at the lift front): the three landing doors and the
# GF lobby door D-GF-08 in GF-W08 (T-559 s.1; T-608 s.3). D-1F-05 / D-2F-02 sit in 0.20 walls outside his stacked
# shaft piece and are in his 15 cm section (T-559 notes); P-GF-01 (0.20 GF-W14) is not a stacked shaft wall.
SHAFT = {"L-GF-01", "L-1F-01", "L-2F-01", "D-GF-08"}

# drawing evidence per opening (merged records; 'beam' only where a trace states it)
BEAM_TRACED = {
    "A-1F-01": ("NONE", "S8.6 LT-OP-1F-018 (faces AD0/AD1/AD4/AD5): both bearings drawn masonry >= 400 mm, no beam band"),
    "P-1F-01": ("NONE", "S8.6 LT-OP-1F-021 (faces C09-C0C): L2 under no structural member; T-198: lintel + masonry to "
                        "the soffit built above it"),
    "P-GF-01": ("FULL_WIDTH", "S8.6 OP-GF-020 / T-198: an S1 beam band over the whole width, head not printed "
                              "(Q-HEAD-UNDER-BEAM)"),
}
HEAD_BY_ID = {"A-GF-01": "ARCH_DRAWN", "A-1F-01": "ARCH_DRAWN", "P-GF-01": "HEADER_LINES", "P-1F-01": "HEADER_LINES"}
# W17: curved on plan, arched head (census r3); wall band R 1.935 .. 2.135 (T-302 hand geometry, arcs BCD / BCE / BD0
# and BD1 / BD2 / BD6), outer arc 3.2895 (DXF COP-001), lintel section of a 0.20 wall 0.20 wide (ledger section_m)
W17_CURVE = {"r_out_m": 2.135, "arc_m": 3.2895, "wall_t_m": 0.20, "piece_w_m": 0.20}
# drawn in a masonry wall, both faces read (T-581 frame blocks; T-601 doorless / lift gaps; census r3 windows)
DRAWN_SOURCE = "T-581 s.2 (26 frame-block doors + 2 arch blocks, both faces) / T-601 s.2 (doorless + lift gaps)"


def sha16(rel):
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()[:16]


def load():
    for k, (rel, pin) in IN.items():
        got = sha16(rel)
        if got != pin:
            raise SystemExit(f"{rel}: sha {got} is not the pinned {pin} (stale input)")
    t571 = json.loads((ROOT / IN["t571"][0]).read_text())
    led = json.loads((ROOT / IN["ledger"][0]).read_text())
    cen = {r["ID"]: r for r in csv.DictReader((ROOT / IN["census"][0]).open(encoding="utf-8"))}
    return t571, led, cen


def build():
    t571, led, cen = load()
    lint = {x["opening_id"]: x for x in led["lintels"]}
    ours, req, drawn = [], {}, set()
    for p in t571["pairs_owner_0.15"]:
        oid = p["ours"]
        st = p["storey"]
        counts = 0 if p["state_ours"] == "NO_LINTEL" else 1
        group = "SHAFT_20" if oid in SHAFT else (f"{st}_EXT" if p["wall_class"] == "EXT" else f"{st}_15")
        ours.append({"id": oid, "storey": st, "group": group, "width_m": p["w_ours"], "counts": counts})
        x = lint.get(oid)
        if x is not None:
            drawn.add(oid)
            kind = x["kind"]
            head = HEAD_BY_ID.get(oid, {"DOOR": "DOOR_FRAME", "LIFT": "NONE"}.get(kind, "NONE"))
            beam, beam_src = BEAM_TRACED.get(oid, ("UNKNOWN", "no trace of the member over the opening in a record"))
            op = {"id": oid, "host": "MASONRY", "head": head, "beam_over": beam}
            if x["decision"] == "REQUIRED" and kind == "DOOR":
                op["clear_margin_m"] = x["spare_margin_m"]
            r = R.requirement(op)
            req[oid] = {**r, "ledger_decision": x["decision"], "host_wall": x["host"], "wall_t_m": x["wall_t_m"],
                        "kind": kind, "beam_source": beam_src, "piece_m": R.stock_piece(p["w_ours"])}
        elif oid == "W17":
            r = R.requirement({"id": oid, "host": "MASONRY", "head": "ARCH_DRAWN", "beam_over": "UNKNOWN",
                               "curved": W17_CURVE})
            req[oid] = {**r, "ledger_decision": "NO_LINTEL", "kind": "WINDOW",
                        "note": "T-302: elevation draws wall round the hole; head vs CB12 (0.75) soffit = DCR-3; "
                                "the head support (CB12 or a curved cast element) stays HELD by name, never a piece"}
    keys = {}
    key_skipped = []
    their_by_group = {g["group"]: g["widths"] for g in THEIRS}
    for o in ours:
        c = cen.get(o["id"]) or {}
        k = (c.get("FREELANCER_KEY") or "").strip()
        if not k or k == "none" or k.endswith("?") or not c.get("FREELANCER_W"):
            continue
        w = float(c["FREELANCER_W"])
        if any(abs(w - x) <= R.WIDTH_TOL for x in their_by_group.get(o["group"], [])):
            keys[o["id"]] = (o["group"], w)
        else:
            key_skipped.append({"id": o["id"], "key": k, "w": w,
                                "why": "his aluminium-workbook key width is not in his deduction list of this group"})
    closed = R.close_residual(ours, THEIRS, keys)
    v = R.verdicts(closed, req, drawn)
    # the T-571 attribution beside (its ENGINE_ONLY ids) and what changes
    t571_only = sorted(p["ours"] for p in t571["pairs_owner_0.15"] if p["cause"] == "ENGINE_ONLY")
    firm = sorted(i for g in closed["groups"] for i in g["ours_only_firm"])
    poss = sorted(i for g in closed["groups"] for i in g["ours_only_possible"])
    # beside: T-571's identity for his 20 cm 1.10 (P-GF-01 read on its 1.10 face, T-175) instead of D-GF-08
    alt_ours = [dict(o, group="SHAFT_20") if o["id"] == "P-GF-01" else o for o in ours]
    alt_keys = dict(keys, **{"P-GF-01": ("SHAFT_20", 1.10)})
    alt = R.close_residual(alt_ours, THEIRS, alt_keys)
    alt_v = R.verdicts(alt, req, drawn)
    beside = {"why": "admissible, not chosen: his 20 cm rows repeat the same five shaft lengths on all three storeys "
                     "(a stacked shaft); P-GF-01's wall GF-W14 is not stacked, D-GF-08 sits in the lift-front GF-W08",
              "closure_nr": alt["closure_nr"],
              "ours_only": {g["group"]: {"firm": g["ours_only_firm"], "possible": g["ours_only_possible"]}
                            for g in alt["groups"] if g["ours_only_k"]},
              "engine_right_nr": [sum(v["engine_right_nr"][0] for v in alt_v),
                                  sum(v["engine_right_nr"][1] for v in alt_v)]}
    er = [sum(x["engine_right_nr"][0] for x in v), sum(x["engine_right_nr"][1] for x in v)]
    un = [sum(x["unresolved_nr"][0] for x in v), sum(x["unresolved_nr"][1] for x in v)]
    neg = sum(1 for x in v for y in x["their_piece_on_no_lintel"] if y["verdict"] == R.ENGINE_RIGHT)
    summary = {"at_most_basis": "every ours-only candidate is a drawn opening in a masonry wall: ENGINE_RIGHT; W17 "
                                "takes no straight piece: ENGINE_RIGHT; residual 0 nr on the AT_MOST basis",
               "established_basis_ours_only_engine_right_nr": er, "established_basis_unresolved_nr": un,
               "their_piece_engine_right_nr": neg,
               "statement_sign_his_minus_ours": {"ENGINE_RIGHT": [-er[1] + neg, -er[0] + neg],
                                                 "UNRESOLVED": [-un[1], -un[0]], "total": -closed["closure_nr"]}}
    out = {
        "rule": R.RULE_ID, "summary": summary, "beside_t571_identity": beside, "inputs": {k: {"path": rel, "sha16": pin} for k, (rel, pin) in IN.items()},
        "statement_row": "T-571/lintel-count-implied (V10): his 54 vs engine 60 AT_MOST, -6 nr",
        "ours_nr": closed["ours_nr"], "theirs_nr": closed["theirs_nr"], "difference_nr": closed["difference_nr"],
        "closure_nr": closed["closure_nr"], "keys_used": sorted(keys), "keys_skipped": key_skipped,
        "groups": closed["groups"], "verdicts": v,
        "requirement": {k: req[k] for k in sorted(req) if k in set(firm) | set(poss) | {"W17", "L-GF-01"}},
        "ours_only_firm": firm, "ours_only_possible": poss, "t571_engine_only": t571_only,
        "drawn_source": DRAWN_SOURCE,
    }
    return out


def dump(o):
    return json.dumps(o, indent=1, sort_keys=True, ensure_ascii=False) + "\n"


def main(argv):
    out = dump(build())
    if "--check" in argv:
        if OUT.read_text() != out:
            raise SystemExit("T616_RESIDUAL.json differs from a rebuild")
        print("T616_RESIDUAL.json: byte-identical")
        return
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(out)
    print(OUT)


if __name__ == "__main__":
    main(sys.argv[1:])
