"""T-696 part (a): census of every B9 material line left blank on ARCH_TAKEOFF_V3.0.68, by host and cause, with the
drawn bound of the host area where the drawings give one and the material bound it carries (Q-80 / Q-75 module, Q-78
mix, owner 2026-10-29 10 mm joint, UPC-AAC-GLUE-001), every end rounded by R-T696-1 (BOUND_ROUNDING_V1).

Physical element first: each blank line describes the units / joint mortar / perimeter joint / AAC glue of ONE host
masonry line (MAS.BLOCK). Its quantity exists only as far as the host's block area exists: a host whose area has no
drawn end gives its materials no end. A one-ended host bound (AT_MOST from a datum whose sign is physical, AT_LEAST
from a printed minimum height) gives a one-ended material figure that stays BESIDE the HELD blank line (never a range,
never a point, never 0); a line is only valued or bounded by a wiring row.

Sources (merged, sha-pinned; nothing typed but the T-488 wall -> part line map, asserted against the T-488 carried
figures of each part line):
  - research/agents_t672/out/LINE_INDEX_V3_0_68.json (T-672 run of record d1de50cb): the blank lines and their hosts;
  - research/agents_t488/t488_inputs.py roof_datum walls (T-482 / T-488, Checker-merged): U = net at b_r = 0, L;
  - research/agents_t487/T-487_LINTEL_LINES.md faces of the 2F REQUIRED lintels (D-2F-01 0.36, D-2F-03 0.32 m2),
    via the merged T-498 faces_on_held_hosts decisions;
  - research/agents_t449/round3/out/CORRECTION_REGISTER_BLOCKWORK_T449.json: the held walls each parent holds;
  - research/agents_t675/out/T675_MASONRY_ROUND2.json: MAIN_S / ANNEX_S (note 2 BLACK; AT_LEAST 11.389 m2 net).

    bash scripts/agent_env.sh run --tree task-T-696 research/agents_t696/t696_b9_census.py [--json OUT]
        [--candidate <private V3_0_68_BOQ_LINES.json>]    (asserts every census row against the candidate lines)
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
for _p in (HERE, ROOT, ROOT / "research" / "agents_t488"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import bound_rounding_v1 as BR  # noqa: E402
import t696_b9_bounds as BB  # noqa: E402

IDX = BB.IDX
REG = ROOT / "research/agents_t449/round3/out/CORRECTION_REGISTER_BLOCKWORK_T449.json"
T675 = BB.T675
PINS = {IDX: "fc485958", REG: None, T675: "66e63dfc"}
CODES_BLACK = ("MAS.UNITS.BLACK", "MAS.MORTAR.BLACK", "MAS.MORTAR.BLACK.PERIMETER")
CODES_WHITE = ("MAS.GLUE.AAC", "MAS.UNITS.WHITE")
UNIT = {"MAS.UNITS.BLACK": "pcs", "MAS.MORTAR.BLACK": "m3", "MAS.MORTAR.BLACK.PERIMETER": "m3",
        "MAS.GLUE.AAC": "kg", "MAS.UNITS.WHITE": "pcs"}

# T-488 s.3 (merged): roof-datum wall -> its V3.0.55 part line (by colour / basis); asserted below against the
# V3.0.54 carried figures of each part line (T-488 table, column V3.0.54).
PART_OF = {"2F-W01": "L-76a4d8e5", "2F-W06": "L-76a4d8e5", "2F-W04": "L-e90c9dd5", "2F-W05": "L-a6eedf5e",
           "2F-W02": "L-bbb82de2", "2F-W07": "L-bbb82de2", "2F-W08": "L-e1e06ec1", "2F-W03": "L-9056ebed"}
CARRIED_V3054 = {"L-76a4d8e5": "21.66", "L-e90c9dd5": "21.476", "L-a6eedf5e": "3.80", "L-bbb82de2": "15.9165",
                 "L-e1e06ec1": "9.64", "L-9056ebed": "25.885"}
# T-487 (merged): the 2F REQUIRED lintel faces (length x 0.20 m lintel depth); T-498 decisions name their hosts.
REQ_FACE_2F = {"D-2F-01": ("2F-W03", "0.36"), "D-2F-03": ("2F-W08", "0.32")}

CAUSE = {
    "ROOF_DATUM": ("DESIGNER ITEM", "D-39: the main-roof structural level / build-up b_r is not printed; each wall is "
                   "U - L x b_r with b_r >= 0 (the structural top cannot sit above the finished +13.90), so the host "
                   "area has a drawn UPPER end only; no printed upper limit of b_r keyed to this roof (P1 note b_r < "
                   "0.30 is not keyed to it, T-482): the lower end is open"),
    "PARENT": ("OPEN BOUND", "BLOCK_WALL_NOT_ESTABLISHED parent: the held walls / pieces of this thickness that no part "
               "line carries (colour not split); at least one of them has no drawn end (see its walls)"),
    "AAC_FACE": ("RULE NOT GIVEN", "the AAC block face the project uses is not printed and the company rules give no "
                 "AAC count rule (Q-60 records two supplier faces, 62.5 x 25 and 60 x 20, without choosing): host area "
                 "VALUED, the count HELD; never the black 12.5 / m2"),
    "MAIN_S": ("OPEN BOUND", "black block below the neighbour-side ground beams (ST p.1 note 2): height only h >= 0.70 m, "
               "no section prints the leaf thickness or bottom level: AT_LEAST only"),
    "ANNEX_S": ("DESIGNER ITEM", "annex neighbour-side ground-beam soffit CONFLICT (D-35 / RFI-S09): no bound"),
}


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def material_one_end(kind, area_m2, req_face_m2, code, t, glue_kg_per_m2=None):
    """a one-ended host area bound -> the one-ended material figure (every villa).
    kind AT_MOST: base = area - REQUIRED lintel faces (a HELD face deducts 0: the end stays an upper end), rounded
    UP; kind AT_LEAST: base = area (no face deducted unless required), rounded DOWN. Units 12.5 / m2 (40 x 20, Q-75 /
    Q-80), mortar t x (1 - kappa), AAC glue UPC-AAC-GLUE-001; white units and the perimeter joint have no area rule:
    None (HELD). A missing area or thickness is an error, never 0."""
    if kind not in ("AT_MOST", "AT_LEAST"):
        raise ValueError(f"not a one-ended kind: {kind}")
    if area_m2 is None or t is None:
        raise ValueError("a one-ended figure needs the host area end and the thickness (never 0)")
    base = BR.add(area_m2, -BR.D(req_face_m2 or 0))
    if base < 0:
        raise ValueError(f"REQUIRED lintel faces {req_face_m2} exceed the host area end {area_m2}")
    if code == "MAS.UNITS.BLACK":
        fig = BR.mul(base, BB.BLOCKS_PER_M2)
    elif code == "MAS.MORTAR.BLACK":
        fig = BR.mul(base, BB.joint_rate(t))
    elif code == "MAS.GLUE.AAC":
        if glue_kg_per_m2 is None:
            raise ValueError("AAC glue rate missing for this thickness: HELD, never borrowed")
        fig = BR.mul(base, glue_kg_per_m2)
    else:
        return None
    printed = BR.round_high(fig) if kind == "AT_MOST" else BR.round_low(fig)
    return {"kind": kind, "base_m2": str(base), "exact": str(fig), "printed": float(printed)}


def roof_hosts():
    import t488_inputs as I488
    walls = I488.build()["roof_datum"]["walls"]
    hosts = {}
    for w in walls:
        pid = PART_OF[w["wall_id"]]
        h = hosts.setdefault(pid, {"walls": [], "U": BR.D(0), "L": BR.D(0), "carried": BR.D(0)})
        h["walls"].append(w["wall_id"])
        h["U"] = BR.add(h["U"], w["upper_m2"])
        h["L"] = BR.add(h["L"], w["length_m"])
        h["carried"] = BR.add(h["carried"], w["carried_m2"])
    for pid, h in hosts.items():
        if h["carried"] != BR.D(CARRIED_V3054[pid]):
            raise SystemExit(f"{pid}: walls carry {h['carried']} m2, not the T-488 V3.0.54 {CARRIED_V3054[pid]}")
        if abs(BR.add(h["U"], -BR.mul(h["L"], "0.05")) - h["carried"]) > BR.D("0.0005"):
            raise SystemExit(f"{pid}: U - 0.05 L is not the carried figure within its 3 dp print (T-488)")
        h["req_face"] = BR.add(*[BR.D(f) for o, (w, f) in REQ_FACE_2F.items() if w in h["walls"]]) \
            if any(w in h["walls"] for w, _ in REQ_FACE_2F.values()) else BR.D(0)
    return hosts


def parent_walls(reg):
    out = {}
    for e in reg["entries"]:
        if e.get("item_code") != "MAS.BLOCK" or e["action"] in ("VERIFIED", "DRAWING-CONFIRMED",
                                                                 "ASSUMED - OWNER-APPROVED"):
            continue
        rr = e["rule_result"]
        held = rr.get("held") or []
        if e["action"] == "HELD ON DROP":
            end = "AT_MOST (U - L x d, d >= 0 not printed)"
        elif e["action"] == "ESTABLISHED PART + HELD":
            end = "held pieces: no drawn end"
        else:
            end = "no drawn end"
        out.setdefault(e["line_id"][:10], []).append({"wall_id": e["element_id"], "state": e["action"], "end": end,
                                                      "held": [h[:160] for h in held]})
    return out


def build(candidate=None):
    for p, want in PINS.items():
        if want and not _sha(p).startswith(want):
            raise SystemExit(f"{p.name}: sha256 {_sha(p)[:8]} is not {want}")
    idx = _load(IDX)
    lines = idx["lines"]
    blk = {r["line_id"][:10]: r for r in lines if r["item_code"] == "MAS.BLOCK"}
    by_eid = {r["element_id"]: r for r in lines if r["item_code"] == "MAS.BLOCK"}
    rh = roof_hosts()
    pw = parent_walls(_load(REG))
    t675 = _load(T675)
    rows = []
    for r in sorted(lines, key=lambda r: (r["item_code"], r["element_id"])):
        if r["item_code"] not in UNIT or r["class"] != "HELD" or r["held_low"] is not None:
            continue
        eid = r["element_id"].replace("MATERIAL:", "").replace("#PERIMETER_JOINT", "")
        host = by_eid[eid]
        hid = host["line_id"][:10]
        code, t = r["item_code"], (BB._t_of(eid) if "t=" in eid else None)
        row = {"line_id": r["line_id"], "item_code": code, "unit": UNIT[code], "host_line_id": host["line_id"],
               "host": eid, "state_v3_0_68": "HELD blank"}
        if host["class"] != "HELD":
            if code != "MAS.UNITS.WHITE":
                raise SystemExit(f"{r['line_id']}: blank on a valued host {hid}")
            row.update(cause_class=CAUSE["AAC_FACE"][0], cause=CAUSE["AAC_FACE"][1],
                       host_area_m2={"contract_net": host["measured_net"]})
            row["beside"] = {"kind": "NONE", "why": "the producer's 62.5 x 25 (6.4 / m2) and 60 x 20 (8.33 / m2) "
                                                    "alternatives stay beside on the line (V3.0.59); no face chosen"}
            rows.append(row)
            continue
        if hid in rh:
            h = rh[hid]
            base_hi = BR.add(h["U"], -h["req_face"])
            row.update(cause_class=CAUSE["ROOF_DATUM"][0], cause=CAUSE["ROOF_DATUM"][1], walls=h["walls"],
                       host_area_m2={"U_at_b_r_0": str(h["U"]), "L_m": str(h["L"]), "form": f"{h['U']} - {h['L']} b_r",
                                     "required_lintel_faces_m2": str(h["req_face"]),
                                     "material_base_AT_MOST_m2": str(base_hi)})
            gr = BB.glue_rate(_load(BB.RB), t) if code == "MAS.GLUE.AAC" else None
            m = material_one_end("AT_MOST", h["U"], h["req_face"], code, t, gr)
            if m is not None:
                row["beside"] = dict(m, why="one-ended: b_r >= 0 only; the line stays HELD blank (never a range / "
                                            "point, never 0)")
            elif code == "MAS.UNITS.WHITE":
                row["beside"] = {"kind": "NONE", "why": "AAC face not selected (Q-60 supplier faces 62.5 x 25 / "
                                                        "60 x 20 beside only): no count rule, HELD"}
            else:
                row["beside"] = {"kind": "NONE", "why": "perimeter joint of the 2F walls: vertical bands depend on "
                                                        "b_r (T-520 figure only), HELD with the host"}
        elif eid.startswith("HOUSE_BELOW_NG:"):
            k = eid.split(":")[1]
            row.update(cause_class=CAUSE[k][0], cause=CAUSE[k][1])
            if k == "MAIN_S" and code in ("MAS.UNITS.BLACK", "MAS.MORTAR.BLACK"):
                net = BR.D("11.389")
                a = next(x for x in t675["part_a"] if x["material_line_id"] == r["line_id"])
                was = a["beside_conditional"]["AT_LEAST_pcs" if code == "MAS.UNITS.BLACK" else "AT_LEAST_m3"]
                m = material_one_end("AT_LEAST", net, 0, code, "0.15")
                row["host_area_m2"] = {"net_AT_LEAST": "11.389", "source": "T-407 / T-675 (h >= 0.70 m)"}
                row["beside"] = dict(m, condition="CONDITIONAL: one leaf of at least 0.15 m (thickness not printed)",
                                     t675_printed=was, delta=round(m["printed"] - was, 6))
            else:
                row["beside"] = {"kind": "NONE", "why": "no host bound" if k == "ANNEX_S" else
                                 "perimeter joint below N.G.: no drawn wall ends / soffit course: HELD"}
        else:
            ws = pw.get(hid) or []
            if not ws:
                raise SystemExit(f"{hid}: a parent host with no held wall in the register")
            openw = [w["wall_id"] for w in ws if not w["end"].startswith("AT_MOST")]
            row.update(cause_class=CAUSE["PARENT"][0], cause=CAUSE["PARENT"][1], walls=ws,
                       host_area_m2={"bound": "NONE", "walls_with_no_drawn_end": openw})
            row["beside"] = {"kind": "NONE", "why": f"{len(openw)} of {len(ws)} held walls / pieces have no drawn "
                                                    "end and the colour is not split: no material bound"}
            if not openw:
                raise SystemExit(f"{hid}: every held wall is bounded: a host bound exists, census incomplete")
        rows.append(row)
    counts = {}
    for x in rows:
        counts[x["item_code"]] = counts.get(x["item_code"], 0) + 1
    out = {"schema": "T696_B9_CENSUS_V1", "candidate": "ARCH_TAKEOFF_V3.0.68", "line_index": BB.IDX_LINES_SHA,
           "rule": f"{BR.RULE_ID} {BR.METHOD} {BR.RULE_VERSION}", "blank_counts": counts, "rows": rows,
           "pins": {str(p.relative_to(ROOT)): _sha(p)[:8] for p in PINS}}
    if candidate:
        out["candidate_check"] = check_candidate(rows, candidate)
    return out


def check_candidate(rows, path):
    """every census row against the private candidate run: blank, BLOCKED_RFI, its host named in the rfi."""
    data = _load(path)
    lines = data["lines"] if isinstance(data, dict) else data
    by = {ln["line_id"]: ln for ln in lines}
    bad = []
    for x in rows:
        ln = by.get(x["line_id"])
        if ln is None or ln.get("measured_net") is not None or ln.get("bounded_range"):
            bad.append(x["line_id"])
            continue
        blocks = ((ln.get("rfi") or {}).get("blocks") or [])
        if x["host_line_id"] not in blocks and x["item_code"] != "MAS.MORTAR.BLACK.PERIMETER":
            bad.append(x["line_id"])
    return {"file_sha256": _sha(path)[:8], "rows": len(rows), "disagree": bad}


if __name__ == "__main__":
    cand = sys.argv[sys.argv.index("--candidate") + 1] if "--candidate" in sys.argv else None
    doc = build(cand)
    if "--json" in sys.argv:
        Path(sys.argv[sys.argv.index("--json") + 1]).write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n",
                                                                 encoding="utf-8")
    for x in doc["rows"]:
        b = x["beside"]
        print(f"{x['line_id'][:10]} {x['item_code'][4:]:<22} host {x['host_line_id'][:10]} {x['cause_class']:<13} "
              f"{b['kind']} {b.get('printed', '')}")
    print(json.dumps({k: doc[k] for k in ("blank_counts", "pins")} | ({"candidate_check": doc["candidate_check"]}
                                                                     if "candidate_check" in doc else {}), indent=1))
