"""T-530 WIRING MANIFEST builder: the merged, Checker-verified, UNWIRED pieces T-516 .. T-528 mapped onto the lines of
the candidate of record ARCH_TAKEOFF_V3.0.58 (= the V3.0.57 line index 25a8b406 + the 5 T-507 roof WP lines).

Research / integration-preparation only (lane I, non-candidate). Nothing here writes a candidate, released, rule,
knowledge or registry file; the manifest says what the next Gate B packages will move, in what order, and why.
Every figure in the manifest is RECOMPUTED here from the merged piece outputs (committed out/ files, the pieces' own
functions) and the V3.0.57 line index; no quantity is typed in this file. Constants below are identifiers only (task
ids, merge commits, line ids that the pieces themselves name, rule ids) and the Checker's verdict words.

Two inputs need the private drawing (Drive "Alsenan chalet project" / P7757_DXF_COMPRESSED.zip -> P7757.dxf, decoded
into the git-excluded private folder): the T-517 finish hatch and the T-522 window / bay reads. Without it the stream F
section is built with those rows HELD 'drawing not read here' (never 0) and the full-manifest test is skipped.
"""

from __future__ import annotations

import copy
import csv
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SCHEMA = "URBAN_T530_WIRING_MANIFEST_V1"
CANDIDATE = ("ARCH_TAKEOFF_V3.0.58 (T-507 c94b35c1: V3.0.57 line index 25a8b406, 4,994 lines byte-identical, + 5 "
             "FIN.WP.ROOF / ROOF_UPTURN lines = 4,999)")
OUT_JSON = ROOT / "research/agents_t530/WIRING_MANIFEST_T530.json"

INDEX57 = ROOT / "research/agents_t507/out/LINE_INDEX_V3_0_57.json"
T453_CSV = ROOT / "research/agents_t453/out/LINTELS_T453.csv"
T453_LEDGER = ROOT / "research/agents_t453/out/MATERIAL_LEDGER_T453.json"
T516_OUT = ROOT / "research/agents_t516/out/JAMB_BEARING_T516.json"
T520_WALLS = ROOT / "research/agents_t520/out/PERIMETER_BY_WALL_T520.csv"
T520_SUM = ROOT / "research/agents_t520/out/SUMMARY_T520.json"
T526_ENDS = ROOT / "research/agents_t526/out/MISSED_ENDS_T526.csv"
T511_OUT = ROOT / "research/agents_t511/out/CEMENT_SAND_CENSUS_T511.json"
T507_MD = ROOT / "research/agents_t507/T-507_EXPOSED_SLAB_WP.md"
PINS = {
    INDEX57: "fed5141ea31bfdd9c5f3d89c7fb1fa01365ddbf07b797002780a22016a7f5738",
    T453_CSV: None, T453_LEDGER: None, T516_OUT: "155ed68bc3f356d3011d342d836205e596ac7127f81bc8f8efc262d69fc5fef3",
    T520_WALLS: None, T520_SUM: None, T526_ENDS: None,
    T511_OUT: "a2716399281fbf9dde2e5e762b57562dabe8edccb53af9781da82bc58678aea5",
}

# ---- the pieces (identifiers and the Checker's words; numbers come from their outputs) --------------------------------
PIECES = {
    "T-507": {"merge": "c94b35c1", "gate": "B", "verdict": "Verifier 2026-11-05T02:22Z GATE B PASS: ARCH_TAKEOFF_V3.0.58, "
              "the candidate of record (4,994 lines byte-identical + 5 roof WP lines)", "rules": ["R-T507-1"]},
    "T-453": {"merge": "b16f686b", "gate": "A", "verdict": "MERGED r2: blockwork material ledger, R-T453-5 lintel faces "
              "leave the material base", "rules": ["R-T453-2", "R-T453-5"]},
    "T-516": {"merge": "35db84c3", "gate": "A", "verdict": "Verifier 2026-11-05T06:05Z GATE A PASS, own re-measure of 4 "
              "ends AGREE; T-453 lintel length w + 0.80 = LOWER bound on BEARING_OK, not buildable on deficit ends",
              "rules": ["R-T516-1"]},
    "T-517": {"merge": "54b95ad6", "gate": "A", "verdict": "Verifier 2026-11-05T06:06Z GATE A PASS, finish hatch "
              "re-measured 4.519172 m2 AGREE; ENGINE_WRONG (omission of the stack) ENDORSED", "rules":
              ["R-T517-1", "R-T517-2", "R-T517-3", "R-T517-4", "R-T517-5", "R-T517-6"]},
    "T-518": {"merge": "7f7b7564", "gate": "A", "verdict": "Verifier 2026-11-05T06:07Z GATE A PASS: D-T518-1 / D-T518-2 "
              "confirmed; F-T518-2 stair bed 5 % scope open", "rules": ["R-T518-1", "R-T518-2", "R-T518-3"]},
    "T-519": {"merge": "dd9e24c3", "gate": "A", "verdict": "Verifier 2026-11-05T10:00Z GATE A PASS: PROJECT_RC 16 / 16, "
              "6 PRODUCED + 10 HELD; F-C-T519-1 W18 END 0.578 vs 0.478 (T-527)", "rules": ["R-T519-1"]},
    "T-520": {"merge": "3e0dafa6", "gate": "A", "verdict": "Verifier 2026-11-05T11:58Z GATE A PASS: perimeter joint as "
              "the increment over the panel (block count), ENGINE_RIGHT proposal for the method", "rules": ["R-T520-1"]},
    "T-521": {"merge": "ba35e0e2", "gate": "A", "verdict": "Verifier 2026-11-05 08:58 GATE A PASS: FINISH V6 installed = "
              "V5 / 1.05, procurement == V5 (UNWIRED)", "rules": ["R-T521-1"]},
    "T-522": {"merge": "4777890b", "gate": "A", "verdict": "Verifier 2026-11-05T12:02Z GATE A PASS: sill '84' printed, "
              "window run MEASURED; ledge upturn split; ledge membrane UNRESOLVED (exposure)", "rules":
              ["R-T522-1", "R-T522-2", "R-T522-3", "R-T522-4"]},
    "T-523": {"merge": "9a28e927", "gate": "A", "verdict": "Verifier 2026-11-05T10:00Z GATE A PASS: binding map V2, 21 "
              "stale bindings on 7 T-453 lines, one ceiling per purchasing group", "rules":
              ["R-T523-1", "R-T523-2", "R-T523-3", "R-T523-4", "R-T523-5"]},
    "T-524": {"merge": "97e5ce74", "gate": "A", "verdict": "Verifier 2026-11-05T12:00Z GATE A PASS: deficit lintel set "
              "0.514 -> 0.372692 .. 0.437542 m3, conservation inside column + lintel on lintel + not built",
              "rules": ["R-T524-1"]},
    "T-526": {"merge": "1c0ac911", "gate": "A", "verdict": "Verifier 2026-11-05 14:10 GATE A PASS: 12 run ends on RC "
              "columns; 1F-W09 perimeter 0.003334 -> 0.010355 m3 COMPUTED", "rules": ["R-T526-1"]},
    "T-528": {"merge": "046b9ad3", "gate": "A", "verdict": "Verifier 2026-11-05T13:00Z GATE A PASS: FINISH V7 stair 1:3 "
              "rate from UP-STAIR-017 (UNWIRED)", "rules": ["R-T528-1"]},
}
# T-498 stage (NOT merged: agents/task-T-498 @ e3e2ebb5, BLOCKED on the wrapper allow-list): the material line ids it
# stages on each host masonry line, named so the S package can find them; no figure is read from the stage.
T498_STAGE = "agents/task-T-498 @ e3e2ebb5 (ARCH_TAKEOFF_V3.0.59 stage, 74 material lines; not merged)"
T498_LINE_ON_HOST = {("L-2fdc0f971a94348ec855", "glue_kg"): "L-4b9a29d424ea40e0af8a",
                     ("L-a3f88ecda2402f67c500", "glue_kg"): "L-d14c6c9b738045c797ec",
                     ("L-1c53fadb2f92d1f36d4e", "mortar_m3"): "L-1bacf0e3cec97219a455",
                     ("L-10dd62f66ad05488e63b", "mortar_m3"): "L-e74c15038f1e32dbefe0"}
# the 5 T-507 lines (V3.0.58 adds them to the V3.0.57 index); the pieces T-517 / T-522 name them in their own inputs
T507_LINES = ("L-eff54f96bfcfcf175d58", "L-cf8d5ed40b0d546427d6", "L-1954878bb02c91139e1b", "L-2361d6ec13c952bd2ae3",
              "L-d7d1bf8c5991ccf69ea2")

REG_LINTEL = ("ELEMENT_REGISTER 'RC LINTEL over an opening vs the host masonry wall' (Lead 2026-11-03 08:17) + "
              "'LINTEL END VOLUME at a FLAGGED_DEFICIT end' (Lead 2026-11-05 12:20): B9-02 owns the lintel piece; a "
              "volume inside a column is STR.CONC.COLUMN; the host MATERIAL base loses the lintel face, the MAS.BLOCK "
              "contract area is untouched")
REG_POOL = ("ELEMENT_REGISTER 'POOL-COURT SLAB round the void vs ROOF WP vs CEILING' (Lead 2026-11-03 20:20): the "
            "open-sky slab top is WATERPROOFING B8-06, the ledge HELD; soffit = CEILING PL-03")
REG_ROOF = ("ELEMENT_REGISTER 'ROOF BUILD-UP' (screed SCREED one m3 per roof, finish ROOFING B13-01, insulation / "
            "protection UNKNOWN)")
TOL = 1e-6


class ManifestError(ValueError):
    pass


# ---------------------------------------------------------------------------------------------------------- helpers
def _r(x, n=6):
    return None if x is None else round(float(x) + 0.0, n)


def sha256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _json(p):
    pin = PINS.get(p)
    if pin is not None and sha256(p) != pin:
        raise ManifestError(f"PIN: {Path(p).name} sha256 {sha256(p)[:8]} is not the pinned {pin[:8]}")
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _csv(p):
    return list(csv.DictReader(open(p, encoding="utf-8")))


def _module(rel, name):
    p = ROOT / rel
    if str(p.parent) not in sys.path:
        sys.path.insert(0, str(p.parent))
    spec = importlib.util.spec_from_file_location(name, p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def line_index():
    """V3.0.58 lines: the V3.0.57 index + the 5 T-507 lines (by id; their figures from T-507's run table)."""
    d = _json(INDEX57)
    if d["candidate_version"] != "ARCH_TAKEOFF_V3.0.57" or len(d["lines"]) != 4994:
        raise ManifestError("STALE_INPUT: the V3.0.57 line index is not the candidate of record (4,994 lines)")
    idx = {l["line_id"]: l for l in d["lines"]}
    for lid in T507_LINES:
        if lid in idx:
            raise ManifestError(f"{lid}: a T-507 line already in the V3.0.57 index")
    return idx


def _v3058_t507_lines():
    """the 5 T-507 lines from its committed run table (T-507 s.6), read from the report, not retyped."""
    out = {}
    for ln in T507_MD.read_text(encoding="utf-8").splitlines():
        c = [x.strip() for x in ln.strip().strip("|").split("|")]
        if len(c) == 4 and c[0] in T507_LINES:
            code, unit = c[1].split()
            v = c[3]
            if v.startswith("HELD 0 .."):
                hi = float(v.split("..")[1].split()[0])
                out[c[0]] = {"item_code": code, "unit": unit, "element_id": c[2], "class": "HELD", "measured_net": None,
                             "held_low": 0.0, "held_high": hi}
            else:
                out[c[0]] = {"item_code": code, "unit": unit, "element_id": c[2], "class": "RELEASED",
                             "measured_net": float(v.split()[0]), "held_low": None, "held_high": None}
    if set(out) != set(T507_LINES):
        raise ManifestError(f"T-507 run table: lines {sorted(set(T507_LINES) - set(out))} not found")
    return out


def _before(l):
    if l["class"] == "RELEASED":
        return {"class": "RELEASED", "value": l["measured_net"]}
    return {"class": l["class"], "value": None, "held_low": l.get("held_low"), "held_high": l.get("held_high")}


def _piece(*tids):
    return [{"task": t, "merge": PIECES[t]["merge"], "checker": PIECES[t]["verdict"]} for t in tids]


# --------------------------------------------------------------------------------------------- stream S: lintels
def lintel_inputs():
    t453 = {r["opening_id"]: r for r in _csv(T453_CSV)}
    t516 = {r["opening_id"]: r for r in _json(T516_OUT)["rows"]}
    t519 = {r["opening_id"]: r for r in _module("research/agents_t519/t519_lintel_pieces.py", "t519_m").build()["rows"]}
    t524 = _module("research/agents_t524/t524_lintel_end_ownership.py", "t524_m").build()
    return t453, t516, t519, t524


def lintel_rows(idx):
    t453, t516, t519, t524 = lintel_inputs()
    by_el = {l["element_id"]: l for l in idx.values() if l["item_code"] == "STR.CONC.LINTEL"}
    pair = {x: p for p in t524["pairs"] for x in p["pair"]}
    rows, req = [], [k for k, r in t516.items() if r["decision"] == "REQUIRED"]
    for oid in sorted(req):
        l = by_el.get(f"LINTEL:{oid}")
        if l is None or l["class"] != "RELEASED":
            raise ManifestError(f"{oid}: REQUIRED lintel without a valued V3.0.58 STR.CONC.LINTEL line")
        c = t453[oid]
        B = float(c["wall_t_m"])
        L453 = float(c["length_m"])
        D = float(c["face_m2"]) / L453
        if abs(l["measured_net"] - float(c["concrete_m3"])) > TOL or abs(B * D * L453 - l["measured_net"]) > 5e-4:
            raise ManifestError(f"{oid}: candidate line {l['measured_net']} is not the T-453 B x D x (w + 0.80)")
        s16, s19 = t516[oid], t519[oid]
        if s19["system"] != "PROJECT_RC":
            raise ManifestError(f"{oid}: T-519 system {s19['system']} (only PROJECT_RC is wired here)")
        base = {"line_id": l["line_id"], "item_code": "STR.CONC.LINTEL", "unit": "m3", "element_id": l["element_id"],
                "before": _before(l), "section_B_D_m": [B, _r(D)], "t453_length_m": L453,
                "cross_trade_owner": REG_LINTEL, "stream": "S", "stale_binding_keys": [f"T-453|LINTEL|{oid}|concrete_m3"]}
        if s16["state"] == "BEARING_OK":
            if s19["state"] != "PRODUCED" or s19["rc"]["length_lo_m"] != s16["length_lo_m"] \
                    or s19["rc"]["length_hi_m"] != s16["length_hi_m"]:
                raise ManifestError(f"{oid}: T-519 PRODUCED piece disagrees with the T-516 lengths")
            lo, hi = s16["length_lo_m"], s16["length_hi_m"]
            if abs(lo - L453) > TOL:
                raise ManifestError(f"{oid}: T-516 lower length {lo} is not the T-453 length {L453}")
            after = {"state": "BOUNDED_MIN_BEARING", "low": _r(B * D * lo),
                     "high": None if hi is None else _r(B * D * hi),
                     "high_reason": None if hi is not None else "pier upper bound not measured (T-516: >= 3.0 m, no "
                                                                 "ceiling): HELD, never the low",
                     "length_m": [lo, hi], "pieces_nr": 1,
                     "why": "both ends carry at least the printed MIN 40 cm: the T-453 length w + 0.80 is the LOWER "
                            "bound; the built length lies in [w + 0.80, w + a_s + a_e] (R-T516-1); 1 piece cast to "
                            "length (R-T519-1 PROJECT_RC, no stock length)"}
            ev = "DRAWING-CONFIRMED lower bound (MIN.40cm printed, piers measured); upper HELD where no pier ceiling"
            src = _piece("T-516", "T-519")
            rules = ["R-T516-1", "R-T519-1"]
        else:
            if s19["state"] != "HELD":
                raise ManifestError(f"{oid}: deficit lintel but T-519 state {s19['state']}")
            if oid in pair:
                p = pair[oid]
                after = {"state": "HELD_BY_NAME", "low": None, "high": None,
                         "pair": p["pair"], "pair_bound_m3": [p["concrete_lo_m3"], p["concrete_hi_m3"]],
                         "pair_carried_on": p["pair"][0],
                         "why": f"two lintels over one {p['pier_m']} m pier: the pair occupies the pier once "
                                f"(lintel on lintel {p['lintel_on_lintel_m3']} m3 removed); the per-lintel split is a "
                                f"designer item: the pair bound is carried ONCE (on {p['pair'][0]}), never per line"}
            else:
                r = t524["lintels"][oid]
                after = {"state": "HELD_BY_NAME", "low": None, "high": None,
                         "bound_m3": [r["concrete_lo_m3"], r["concrete_hi_m3"]],
                         "length_m": [r["length_lo_m"], r["length_hi_m"]],
                         "why": "an end has less masonry than the printed MIN 40 cm (T-516 FLAGGED_DEFICIT): the "
                                "lintel stops at its host (column face / cross wall / pier); the volume inside a "
                                "column is column concrete, beyond a far face nothing is built (R-T524-1); connection "
                                "= designer RFI, HELD by name with the bound beside, never 0"}
            ev = "HELD (designer RFI: lintel connection at a deficit end); bound DRAWING-CONFIRMED"
            src = _piece("T-516", "T-519", "T-524")
            rules = ["R-T516-1", "R-T519-1", "R-T524-1"]
        rows.append(dict(base, after=after, evidence_status=ev, source=src, rules=rules,
                         order=["T-516 (label / bounds)", "T-519 (system, pieces)"]
                         + (["T-524 (deficit-end volume)"] if len(src) == 3 else [])))
    return rows, t524


def lintel_code_view(rows, t524):
    before = _r(sum(r["before"]["value"] for r in rows))
    ok = [r for r in rows if r["after"]["state"] == "BOUNDED_MIN_BEARING"]
    held = [r for r in rows if r["after"]["state"] == "HELD_BY_NAME"]
    lows = sum(r["after"]["low"] for r in ok) + t524["summary"]["corrected_lo_m3"]
    his = [r["after"]["high"] for r in ok]
    return {"code": "STR.CONC.LINTEL m3", "lines": len(rows), "before_released": before,
            "after": {"valued_lines": 0, "bounded_lines": len(ok), "held_by_name_lines": len(held),
                      "at_least_m3": _r(lows),
                      "upper_known_part_m3": _r(sum(h for h in his if h is not None)
                                                + t524["summary"]["corrected_hi_m3"]),
                      "upper_held_lines": [r["element_id"] for r in ok if r["after"]["high"] is None],
                      "view": f"HELD ({len(rows)} lines: {len(ok)} bounded, {len(held)} held by name), AT_LEAST "
                              f"{_r(lows)} m3; no 0.0, no single released figure"},
            "removed_from_b9_02_m3": t524["summary"]["removed_m3"],
            "removed_owner": {"STR.CONC.COLUMN (already counted there, lines untouched)":
                              t524["summary"]["inside_column_total_m3"],
                              "lintel on lintel (pier occupied once)": t524["summary"]["lintel_on_lintel_m3"],
                              "not built (designer item)": t524["summary"]["not_built_m3"]}}


# --------------------------------------------------------------------------------------------- stream S: host faces
def _face_bounds(rows_by_oid, t524):
    """face of each REQUIRED lintel in its host wall after the lintel wiring: [D L_lo, D L_hi]."""
    fb = {}
    for oid, r in rows_by_oid.items():
        B, D = r["section_B_D_m"]
        a = r["after"]
        if a["state"] == "BOUNDED_MIN_BEARING":
            lo, hi = a["length_m"]
        elif "length_m" in a:
            lo, hi = a["length_m"]
        else:                                      # a pair: the pair length less the union, split HELD -> its own bound
            p = [x for x in t524["pairs"] if oid in x["pair"]][0]
            lo, hi = None, None
            fb[oid] = {"pair": p["pair"], "pair_face_m2": [_r(D * p["length_lo_m"]), _r(D * p["length_hi_m"])]}
            continue
        fb[oid] = {"face_m2": [_r(D * lo), None if hi is None else _r(D * hi)]}
    return fb


def host_material_rows(lrows, t524, t523):
    led = _json(T453_LEDGER)
    by_oid = {r["element_id"].split(":", 1)[1]: r for r in lrows}
    fb = _face_bounds(by_oid, t524)
    bind = {(b["line_id"], b["kind"]): b for b in t523["bindings"] if b["table"] == "T-453"}
    out, unchanged = [], []
    for m in led["block_materials"]:
        deds = [d for d in (m.get("lintel_deductions") or []) if d["opening_id"] in by_oid]
        if not deds:
            continue
        b_fig = bind.get((m["line_id"], "glue_kg")) or bind.get((m["line_id"], "mortar_m3"))
        if b_fig is not None and b_fig["value"] is None and b_fig["bound"] is None and m.get("status") != "HELD":
            unchanged.append({"host_line": m["line_id"], "item": m["item"],
                              "lintels": sorted(d["opening_id"] for d in deds),
                              "why": f"host figure of the T-453 ledger (V3.0.45 basis) is not fresh on V3.0.58: "
                                     f"T-523 {b_fig['fresh']} (held, figure beside, never read): stays blank by name"})
            continue
        if m.get("status") == "HELD" or m.get("net_m2") is None:
            unchanged.append({"host_line": m["line_id"], "item": m["item"],
                              "lintels": sorted(d["opening_id"] for d in deds),
                              "why": "host material HELD (source line blank): stays blank by name; only the face "
                                     "binding moves to the lintel line id"})
            continue
        if m["item"] != "LAYING_MATERIAL" or m.get("kg_per_m2") is None:
            raise ManifestError(f"{m['line_id']} {m['item']}: a valued host row of an unhandled kind")
        net = m["net_m2"]
        held_max = sum(h["face_max_m2"] for h in m.get("lintel_held_faces") or [])
        f_lo, f_hi, open_hi, faces = 0.0, 0.0, [], []
        for d in deds:
            f = fb[d["opening_id"]]
            if "pair" in f:
                raise ManifestError(f"{m['line_id']}: a paired lintel face on a valued host (split HELD)")
            lo, hi = f["face_m2"]
            f_lo += lo
            if hi is None:
                open_hi.append(d["opening_id"])
            else:
                f_hi += hi
            faces.append({"opening_id": d["opening_id"], "lintel_line_id": by_oid[d["opening_id"]]["line_id"],
                          "t453_face_m2": d["face_m2"], "face_after_m2": [lo, hi],
                          "lintel_after": by_oid[d["opening_id"]]["after"]["state"]})
        base_hi = net - f_lo
        base_lo = None if open_hi else net - f_hi - held_max
        rate = m["kg_per_m2"]
        before_kg = m.get("consumption_kg")
        before_rng = m.get("consumption_kg_range")
        b_kg, b_bags = bind[(m["line_id"], "glue_kg")], bind[(m["line_id"], "glue_bags_25kg_net")]
        if (b_kg["value"], b_kg["bound"]) != (before_kg, before_rng):
            raise ManifestError(f"{m['line_id']}: T-523 binding {b_kg['value']} / {b_kg['bound']} is not the ledger")
        after_kg = [None if base_lo is None else _r(base_lo * rate), _r(base_hi * rate)]
        out.append({
            "host_line_id": m["line_id"], "host_element": m["element_id"], "material": m["material"], "unit": "kg",
            "t498_stage_line": T498_LINE_ON_HOST.get((m["line_id"], "glue_kg")), "t498_stage": T498_STAGE,
            "kg_per_m2": rate, "contract_net_m2": net, "held_faces_max_m2": _r(held_max),
            "before": {"material_base_m2": m.get("material_base_m2"), "range_m2": m.get("material_base_range_m2"),
                       "kg": before_kg, "kg_range": before_rng, "state": m["status"]},
            "after": {"material_base_range_m2": [None if base_lo is None else _r(base_lo), _r(base_hi)],
                      "kg_range": after_kg,
                      "bags_25kg_range": [None if after_kg[0] is None else _r(after_kg[0] / 25.0),
                                          _r(after_kg[1] / 25.0)],
                      "state": "BOUNDED_EXPOSURE (range by name)", "open_upper_faces": open_hi},
            "faces": faces,
            "rule_gap": "RG-1: R-T498-1 (staged) knows a VALUED face (deducted) and a HELD face (0 .. face); after the "
                        "lintel wiring a REQUIRED lintel line is BOUNDED (lo .. hi) or HELD with a bound: the S package "
                        "needs a rule version 'ranged face = [D L_lo, D L_hi] of the lintel line' (computed here)",
            "source": _piece("T-453", "T-516", "T-524", "T-523"), "rules": ["R-T453-5", "R-T516-1", "R-T524-1"],
            "cross_trade_owner": REG_LINTEL, "stream": "S",
            "stale_binding_keys": [f"T-453|{m['line_id']}|glue_kg", f"T-453|{m['line_id']}|glue_bags_25kg_net"],
        })
    return out, unchanged


def glue_group(t523, host_rows):
    """AAC glue villa group (R-T523-1) re-run with the T-523 function on the bindings the host rows move."""
    m523 = _module("research/agents_t523/t523_binding_map_v2.py", "t523_m")
    before = t523["groups"]["AAC_GLUE_25KG"]
    bs = copy.deepcopy(t523["bindings"])
    mv = {h["host_line_id"]: h["after"]["bags_25kg_range"] for h in host_rows}
    for b in bs:
        if b["table"] == "T-453" and b["kind"] == "glue_bags_25kg_net" and b["line_id"] in mv:
            lo, hi = mv[b["line_id"]]
            if lo is None:
                b["value"], b["bound"] = None, None
            else:
                b["value"], b["bound"] = None, [lo, hi]
    after = m523.glue_and_adhesive(bs)["AAC_GLUE_25KG"]
    rec = {k: before[k] for k in ("at_least", "to_buy_at_least", "status")}
    return {"group": "AAC_GLUE_25KG (25 kg bags, villa)", "before": rec,
            "after": {k: after[k] for k in ("at_least", "to_buy_at_least", "status")},
            "rule": "R-T523-1 one ceiling per group; loss HELD -> installed contributes", "source": _piece("T-523")}


# --------------------------------------------------------------------------------------------- stream S: perimeter
def perimeter_rows(idx):
    walls = _csv(T520_WALLS)
    summ = _json(T520_SUM)
    fac = {round(float(k), 3): float(v) for k, v in summ["factor_m3_per_m"].items()}
    by_line, held = {}, []
    for w in walls:
        if w["status"] == "COMPUTED":
            by_line.setdefault(w["line_id"], []).append(w)
        else:
            held.append({"wall": w["wall_id"], "host_line": w["line_id"], "t_m": float(w["t_m"]),
                         "figure_beside_m3": [_r(float(w["perimeter_low_m3"])) if w["perimeter_low_m3"] else None,
                                              _r(float(w["perimeter_high_m3"])) if w["perimeter_high_m3"] else None],
                         "why": w["held"] or w["expression"]})
    cem = summ["materials_perimeter_020"]
    q78 = cem["cement_bags"] / summ["computed_020"]["perimeter_m3"], cem["sand_m3"] / summ["computed_020"]["perimeter_m3"]
    t526 = {(r["wall_id"], r["end"]): r for r in _csv(T526_ENDS)}
    rows, tot = [], 0.0
    for lid, ws in sorted(by_line.items()):
        host = idx[lid]
        if host["class"] != "RELEASED" or host["item_code"] != "MAS.BLOCK":
            raise ManifestError(f"{lid}: perimeter host is not a valued MAS.BLOCK line")
        v = sum(float(w["perimeter_m3"]) for w in ws)
        for w in ws:                                  # the method's own sum: soffit + vertical - corners
            f = fac[round(float(w["t_m"]), 3)]
            chk = f * (float(w["soffit_m"]) + float(w["vertical_exact_m"])) - f * 0.01 * int(w["top_corners"])
            if abs(chk - float(w["perimeter_m3"])) > 2e-6:
                raise ManifestError(f"{w['wall_id']}: perimeter {w['perimeter_m3']} is not kappa b j (L + H) - corners")
        tot += v
        confirm = [{"wall": k[0], "end": k[1], "t526_after_m3": float(r["perimeter_after_m3"]),
                    "t520_wall_m3": float([w for w in ws if w["wall_id"] == k[0]][0]["perimeter_m3"])}
                   for k, r in t526.items() if k[0] in {w["wall_id"] for w in ws} and r["perimeter_state"] == "COMPUTED"]
        rows.append({"line_id": "NEW (S package assigns)", "item_code": "MAS.MORTAR.BLACK", "unit": "m3",
                     "kind": "PERIMETER_JOINT (own producer key 'B9-04 PERIMETER JOINT MORTAR (T-520)')",
                     "host_line_id": lid, "host_element": host["element_id"],
                     "panel_line_beside": T498_LINE_ON_HOST.get((lid, "mortar_m3")), "t498_stage": T498_STAGE,
                     "walls": sorted(w["wall_id"] for w in ws),
                     "before": {"class": "NO_LINE", "value": None},
                     "after": {"state": "COMPUTED PROVISIONAL (joint 10 mm owner-provisional)", "value": _r(v),
                               "cement_bags_beside": _r(v * q78[0]), "sand_m3_beside": _r(v * q78[1])},
                     "t526_confirms": confirm,
                     "evidence_status": "ASSUMED - OWNER-APPROVED (10 mm joint, Q-75 module, Q-78 mix); geometry "
                                        "DRAWING-CONFIRMED",
                     "source": _piece("T-520", "T-526"), "rules": ["R-T520-1", "R-T526-1"],
                     "cross_trade_owner": "B9-04 masonry mortar (own key beside the panel mortar, never inside it)",
                     "stream": "S", "stale_binding_keys": []})
    if abs(tot - summ["computed_020"]["perimeter_m3"]) > 2e-6:
        raise ManifestError(f"perimeter lines {tot} != T-520 computed 0.20 total {summ['computed_020']['perimeter_m3']}")
    return rows, held


def cement_group(t523, prow):
    m523 = _module("research/agents_t523/t523_binding_map_v2.py", "t523_m")
    t511 = _json(T511_OUT)
    t514 = _json(m523.T514)
    by = m523.cement_members(t511, t514, "CEMENT_50KG")
    allm = [m for v in by.values() for m in v]
    before = m523.group_purchase("CEMENT_50KG", allm, 1.0)
    if before["at_least"] != t523["groups"]["CEMENT_SAND"]["CEMENT_50KG"]["group"]["at_least"]:
        raise ManifestError("cement group: T-523 function does not reproduce its own print")
    add = [m523.member(f"T-520|{r['host_line_id']}|PERIMETER_JOINT",
                       installed=(r["after"]["cement_bags_beside"], r["after"]["cement_bags_beside"]),
                       loss_state="HELD") for r in prow]
    after = m523.group_purchase("CEMENT_50KG", allm + add, 1.0)
    return {"group": "CEMENT_50KG (villa, every trade)", "before": {k: before[k] for k in ("at_least", "to_buy_at_least")},
            "after": {k: after[k] for k in ("at_least", "to_buy_at_least", "status")},
            "added_members": [m["id"] for m in add],
            "rule": "R-T523-1; the perimeter loss is HELD (no sourced mortar waste: UPC-BLACK-MORTAR-001), so the "
                    "installed bags join the AT_LEAST part", "source": _piece("T-523", "T-520")}


def stale_bindings(t523, lrows, host_rows, idx):
    lintel_line = {r["element_id"]: r["line_id"] for r in lrows}
    all_lintels = {l["element_id"]: l["line_id"] for l in idx.values() if l["item_code"] == "STR.CONC.LINTEL"}
    no_line = [b for b in t523["bindings"] if b["fresh"] == "NO_CANDIDATE_LINE"]
    unmapped = [b["row"] for b in no_line if "LINTEL:" + b["row"].split("|", 1)[1] not in all_lintels]
    already = [{"line_id": b["line_id"], "material": b["material"], "kind": b["kind"], "fresh": b["fresh"]}
               for b in t523["bindings"] if b["fresh"].startswith("STALE")]
    return {
        "stale_on_v3_0_57_carried": {"count": len(already), "lines": sorted({a["line_id"] for a in already}),
                                     "keys": already, "resolution": "the T-498 resume reads the T-523 V2 fresh figures "
                                                                   "(T-523 s.5); never the V1 figure"},
        "go_stale_by_this_wiring": sorted(
            [f"T-453|LINTEL|{e.split(':', 1)[1]}|concrete_m3 -> {lid}" for e, lid in lintel_line.items()]
            + [k for h in host_rows for k in h["stale_binding_keys"]]),
        "lintel_bindings_without_line": {
            "count": len(no_line), "unmapped": unmapped,
            "finding": "F-T530-1: T-523 marks the 60 T-453 lintel bindings NO_CANDIDATE_LINE ('B9-02 has no "
                       "candidate line'), but V3.0.57 / V3.0.58 carry 60 STR.CONC.LINTEL lines (T-487) with the same "
                       "element ids: every lintel binding maps 1 : 1 by 'LINTEL:<opening>' (asserted, 0 unmapped); the "
                       "S package binds them to those line ids before it moves a lintel line"},
    }


# --------------------------------------------------------------------------------------------- stream F: pool court
def _dxf():
    a = _module("research/agents_t486/t486_alsenan.py", "t486_m")
    return a.default_dxf()


def poolcourt_rows(t507, drawing=True):
    have = drawing and _dxf() is not None
    rows, added, notes = [], [], []
    if not have:
        for lid in ("L-1954878bb02c91139e1b", "L-d7d1bf8c5991ccf69ea2", "L-2361d6ec13c952bd2ae3"):
            l = t507[lid]
            rows.append({"line_id": lid, "item_code": l["item_code"], "unit": l["unit"], "element_id": l["element_id"],
                         "before": _before(l), "after": {"state": "HELD", "why": "private drawing not read in this "
                                                                                 "run: T-522 values not recomputed"},
                         "stream": "F"})
        return rows, added, {"drawing_read": False}
    m522 = _module("research/agents_t522/t522_alsenan.py", "t522_m").build()
    m517 = _module("research/agents_t517/t517_alsenan.py", "t517_m").build()
    # T-522: the window run and the ledge
    win = [r for r in m522["rows_open_sky"] if r.get("run") == "window_face"]
    if len(win) != 1 or win[0]["status"] != "MEASURED":
        raise ManifestError("T-522 window run not MEASURED")
    l = t507["L-1954878bb02c91139e1b"]
    rows.append({"line_id": "L-1954878bb02c91139e1b", "item_code": l["item_code"], "unit": l["unit"],
                 "element_id": l["element_id"], "before": _before(l),
                 "after": {"state": "MEASURED", "value": win[0]["length_lm"],
                           "m2_at_0_20": _r(win[0]["length_lm"] * win[0]["height_m"])},
                 "evidence_status": "DRAWING-CONFIRMED (sill '84' printed: DXF NW elevation DIMENSION 2EEC + PDF)",
                 "source": _piece("T-507", "T-522"), "rules": ["R-T522-1", "R-WP-APPL-UPTURN-1"],
                 "cross_trade_owner": REG_POOL, "stream": "F", "stale_binding_keys": []})
    ups = [r for r in m522["rows_ledge"] if r["component"] == "UPTURN"]
    trs = [r for r in m522["rows_ledge"] if r["component"] == "WINDOW_TRANSITION"]
    l = t507["L-d7d1bf8c5991ccf69ea2"]
    up_lm = _r(sum(r["length_lm"] for r in ups))
    tr_lm = _r(sum(r["held_bound"] for r in trs))
    if abs(up_lm + tr_lm - l["held_high"]) > TOL:
        raise ManifestError(f"ledge face pieces {up_lm} + {tr_lm} != the T-507 bound {l['held_high']}")
    rows.append({"line_id": "L-d7d1bf8c5991ccf69ea2", "item_code": l["item_code"], "unit": l["unit"],
                 "element_id": l["element_id"], "before": _before(l),
                 "after": {"state": "HELD", "held_low": 0.0, "held_high": up_lm,
                           "why": "the ledge exposure is undecided (R-T522-4: binary, theta_c 10.1 .. 10.6 deg): the "
                                  "two solid wall-end pieces only; the glazing piece leaves this line"},
                 "evidence_status": "HELD (exposure); pieces DRAWING-CONFIRMED", "source": _piece("T-507", "T-522"),
                 "rules": ["R-T522-2", "R-T522-4"], "cross_trade_owner": REG_POOL, "stream": "F",
                 "stale_binding_keys": []})
    added.append({"line_id": "NEW (F package assigns)", "item_code": "FIN.WP.DOORWAY_TRANSITION", "unit": "m2",
                  "element_id": "1F-POOLCOURT-550-LEDGE:wp_window_transition (bay glazing BCE on the slab)",
                  "before": {"class": "NO_LINE"},
                  "after": {"state": "HELD", "value": None, "length_beside_lm": tr_lm,
                            "why": "floor-level frame on the slab: a transition by the threshold detail "
                                   "(UP-WP-DOOR-001), not an upturn; every candidate FIN.WP.DOORWAY_TRANSITION line is "
                                   "m2 and no transition width / detail is printed: blank m2 line, length beside "
                                   "(a lm line would split the code total by unit)"},
                  "evidence_status": "HELD (detail not printed)", "source": _piece("T-522"), "rules": ["R-T522-2"],
                  "cross_trade_owner": "window / WP interface (F-T522-3), never the room skirting", "stream": "F"})
    l = t507["L-2361d6ec13c952bd2ae3"]
    led = [r for r in m522["rows_ledge"] if r["component"] == "FLAT_MEMBRANE"][0]
    if abs(led["held_bound"] - l["held_high"]) > TOL:
        raise ManifestError("ledge membrane bound moved")
    rows.append({"line_id": "L-2361d6ec13c952bd2ae3", "item_code": l["item_code"], "unit": l["unit"],
                 "element_id": l["element_id"], "before": _before(l),
                 "after": {"state": "UNCHANGED (HELD 0 .. bound)", "held_low": 0.0, "held_high": led["held_bound"],
                           "why": "exposure: one binary decision, needs a rule V2 with a sourced driven-rain "
                                  "criterion (R-T522-4); no line move"},
                 "source": _piece("T-522"), "rules": ["R-T522-4"], "cross_trade_owner": REG_POOL, "stream": "F",
                 "stale_binding_keys": []})
    # T-517: the build-up stack, one line per layer and zone (codes from the piece rows)
    for r in m517["rows"]:
        val = r["quantity"] if r["state"] == "MEASURED" else None
        added.append({"line_id": "NEW (F package assigns)", "item_code": r["item_code"], "unit": r["unit"],
                      "element_id": f"1F-{r['zone']}:{r['layer'].lower()}", "before": {"class": "NO_LINE"},
                      "after": {"state": r["state"], "value": val, "area_basis_m2": r["area_m2"],
                                "bound_m2": r.get("area_bound_m2"), "missing": r["missing"]},
                      "evidence_status": ("DRAWING-CONFIRMED extent (hatch 1250 + 1253), material HELD (BY_SPEC)"
                                          if val is not None else "HELD (" + "; ".join(x.split(":")[0]
                                                                                        for x in r["missing"]) + ")"),
                      "source": _piece("T-517"), "rules": ["R-T517-1", "R-T517-2", "R-T517-3"],
                      "cross_trade_owner": REG_ROOF + "; " + REG_POOL, "stream": "F"})
    notes.append({"conflict": "C-F1", "pieces": ["T-522", "T-517"],
                  "what": "the T-517 upstand rows (screed / insulation / protection / finish) take 5.193544 lm = the "
                          "T-494 valued runs, stating 'the bath-window run 0.500002 lm stays HELD (sill unknown)'; "
                          "T-522 measured that run (sill 0.84 >= 0.20)",
                  "upstand_lm_before": [e["length_lm"] for e in m517["edge_rows"] if e["kind"] == "UPSTAND"][0],
                  "upstand_lm_after": _r([e["length_lm"] for e in m517["edge_rows"] if e["kind"] == "UPSTAND"][0]
                                         + win[0]["length_lm"]),
                  "order": "T-522 first; the F package re-derives the T-517 edge rows on the T-522 run set (upstand "
                           "height HELD: no quantity moves, the length named beside changes)"})
    return rows, added, {"drawing_read": True, "notes": notes, "hatch_m2": m517["hatch"]["hatch_m2"]}


def roof_code_views(idx, t507, prow, padd):
    def released(code):
        ls = [l for l in idx.values() if l["item_code"] == code] + [l for l in t507.values() if l["item_code"] == code]
        val = [l["measured_net"] for l in ls if l["class"] == "RELEASED"]
        return (_r(sum(val)) if val else None), len(ls)
    out = {}
    for code in ("FIN.WP.ROOF_UPTURN", "FIN.ROOF.FINISH", "FIN.ROOF.SCREED", "FIN.ROOF.INSULATION",
                 "FIN.ROOF.PROTECTION", "FIN.WP.DOORWAY_TRANSITION"):
        v, n = released(code)
        dv = sum(r["after"]["value"] for r in prow if r["item_code"] == code and r["after"].get("state") == "MEASURED"
                 and r["before"]["class"] != "RELEASED")
        dv += sum(r["after"]["value"] or 0.0 for r in padd if r["item_code"] == code)
        nn = len([r for r in padd if r["item_code"] == code])
        valued_after = v is not None or any(r["item_code"] == code and r["after"].get("value") is not None
                                            for r in prow + padd)
        out[code] = {"released_before": v, "lines_before": n, "lines_after": n + nn,
                     "released_after": _r((v or 0.0) + dv) if valued_after else None,
                     "change": _r(dv) if valued_after else None,
                     "change_pct": None if not v else _r(100 * dv / v, 4),
                     "view_after": None if valued_after else f"HELD ({n + nn} lines, no valued line): never 0.0"}
    return out


# --------------------------------------------------------------------------------------------- FINISH V6 / V7
def finish_v6_v7():
    from engine.source import finish_materials_table_v6 as V6
    from engine.source import finish_materials_table_v7 as V7
    t511 = _json(T511_OUT)
    rows = t511["rows"]
    loss = V6.LOSS_Q45["value"]
    k = lambda r: (r["line_id"], r["material"], r["layer"])
    t500 = {(k(r), r["stage"]): r for r in rows if r["table"] == "T-500"}
    rd = [r for r in rows if r["table"] == "FINISH_MATERIALS_TABLE_V1"]
    worst = 0.0
    for r in rd:
        p, i = t500[(k(r), "PROCUREMENT")], t500[(k(r), "INSTALLED")]
        for side in ("low", "high"):
            worst = max(worst, abs(r[side] - p[side]), abs(r[side] / (1 + loss) - i[side]))
    stair = [r for r in rows if r["table"] == "STAIR_BED_V1" and r["status"] == "COMPUTED"]
    rate, why = V7.stair_rate()
    if rate is None:
        raise ManifestError(f"V7 stair rate HELD: {why}")
    cem_i = sum(r["low"] for r in stair if r["material"] == "CEMENT_50KG" and r["stage"] == "INSTALLED")
    sand_i = sum(r["low"] for r in stair if r["material"] == "SAND_LOOSE" and r["stage"] == "INSTALLED")
    cem_p = sum(r["low"] for r in stair if r["material"] == "CEMENT_50KG" and r["stage"] == "PROCUREMENT")
    m3_c, m3_s = cem_i / rate["cement_bags_per_m3"], sand_i / rate["sand_m3_per_m3"]
    hosts = len({r["line_id"] for r in stair})
    return {
        "candidate_lines_moved": 0,
        "why_no_line": "FINISH_MATERIALS_TABLE V1..V7 are read by no candidate method (UNWIRED_PRODUCER); the "
                       "FIN.FLOOR.BED.* m3 lines stay HELD; V6 / V7 reach the BOQ only as material keys",
        "v6_tile_bed": {"reader_rows": len(rd), "keys": len({k(r) for r in rd}), "producer": "T-500",
                        "max_abs_diff": _r(worst, 9),
                        "result": "V6 procurement == the T-500 PROCUREMENT and V6 installed (= V5 / (1 + 0.05)) == the "
                                  "T-500 INSTALLED on every key: V6 stays a READER of the T-500 keys (one producer per "
                                  "key); no binding goes stale, no figure moves",
                        "source": _piece("T-521", "T-518")},
        "v7_stair_bed": {
            "keys_computed": hosts, "producer_now": "STAIR_BED_V1 (T-511 census)",
            "installed_cement_bags": _r(cem_i), "installed_sand_m3": _r(sand_i),
            "mortar_m3_from_cement": _r(m3_c), "mortar_m3_from_sand": _r(m3_s),
            "v7_rate": {"cement_bags_per_m3": rate["cement_bags_per_m3"], "sand_m3_per_m3": rate["sand_m3_per_m3"]},
            "installed_agrees": abs(m3_c - m3_s) < 1e-5,
            "procurement_stair_bed_v1_bags": _r(cem_p),
            "procurement_v7_q45_bags": _r(m3_c * (1 + loss) * rate["cement_bags_per_m3"]),
            "conflict": "C-V7: two procurement figures for the same 11 keys (STAIR_BED_V1 purchasing allowance vs V7 "
                        "installed + Q-45 5 %): F-T518-2 left the stair-bed loss scope OPEN (never stacked without a "
                        "ruling). Wiring order: V7 becomes the stair INSTALLED producer only by replacing STAIR_BED_V1 "
                        "(one producer per key, R-T523-4), and its procurement stays HELD until the Lead / Checker "
                        "rule F-T518-2",
            "source": _piece("T-528", "T-518")},
    }


# --------------------------------------------------------------------------------------------- packages
def packages(lrows, hrows, prows, frows, fadd, v67):
    s_lines = len(lrows)
    return {
        "S": {"base": f"T-498 r3 stage ({T498_STAGE}) after the T-525 registry promotion of T-507",
              "moves": {"STR.CONC.LINTEL lines": s_lines, "T-498 material lines (host faces)": len(hrows)},
              "adds": {"MAS.MORTAR.BLACK perimeter lines": len(prows)},
              "order": ["1 T-525: promote T-507 in a new master (the t485 gate)",
                        "2 T-498: 74 material lines (V3.0.59 stage) on V3.0.58",
                        "3 bind the 60 lintel material bindings to their STR.CONC.LINTEL line ids (F-T530-1)",
                        "4 lintel lines: T-516 label / bounds, T-519 pieces, T-524 deficit volumes (16 lines)",
                        "5 host faces: the 2 valued glue lines re-based on the lintel bounds (RG-1 rule version)",
                        "6 perimeter mortar: 2 new lines on the 0.20 black hosts (T-520, confirmed by T-526)",
                        "7 groups: AAC glue and cement AT_LEAST re-run (R-T523-1)"],
              "size": f"{s_lines} lines moved + {len(hrows)} staged material lines moved + {len(prows)} added",
              "blocked_by": "wrapper allow-list (the Drive chain / master / binding tools are research scripts)"},
        "F": {"base": "V3.0.58 (independent of S: no shared line, file or material key)",
              "moves": {"FIN.WP.ROOF_UPTURN lines": len([r for r in frows if r["after"]["state"] not in
                                                         ("UNCHANGED (HELD 0 .. bound)",)])},
              "adds": {"FIN.ROOF.* / FIN.WP.DOORWAY_TRANSITION lines": len(fadd)},
              "order": ["1 T-522: window run MEASURED, ledge upturn split (+ transition line)",
                        "2 T-517: 8 build-up lines (finish MEASURED, 7 blank) with the edge rows re-derived on the "
                        "T-522 runs (C-F1)",
                        "3 FINISH V6: reader of the T-500 keys only (no line, no figure)",
                        "4 FINISH V7 stair: only after the F-T518-2 ruling (C-V7); installed agrees, procurement HELD"],
              "size": f"{len(frows) - 1} lines moved, 1 unchanged named, {len(fadd)} added; V6 / V7: 0 lines",
              "blocked_by": "wrapper allow-list (same)"},
        "numbering": "S and F both extend V3.0.58: the package merged first takes V3.0.59 (T-498 holds that stage), "
                     "the second renumbers (merge-order rule, T-507 precedent)",
    }


# --------------------------------------------------------------------------------------------- build
def build(drawing=True):
    idx = line_index()
    t507 = _v3058_t507_lines()
    t523 = _module("research/agents_t523/t523_binding_map_v2.py", "t523_m").run()
    if t523["failures"]:
        raise ManifestError("T-523 map fails its own checks")
    lrows, t524 = lintel_rows(idx)
    hrows, hunch = host_material_rows(lrows, t524, t523)
    prows, pheld = perimeter_rows(idx)
    frows, fadd, finfo = poolcourt_rows(t507, drawing)
    v67 = finish_v6_v7()
    man = {
        "schema": SCHEMA, "candidate": CANDIDATE, "task": "T-530",
        "inputs": {str(p.relative_to(ROOT)): sha256(p) for p in sorted(PINS, key=str)},
        "pieces": {k: dict(v) for k, v in sorted(PIECES.items())},
        "stream_S": {
            "lintel_lines": lrows, "lintel_code_view": lintel_code_view(lrows, t524),
            "host_material_lines": hrows, "host_material_unchanged": hunch,
            "glue_group": glue_group(t523, hrows),
            "perimeter_lines": prows, "perimeter_held_beside": pheld,
            "cement_group": cement_group(t523, prows),
        },
        "stream_F": {"lines": frows, "added_lines": fadd, "drawing": finfo,
                     "code_views": roof_code_views(idx, t507, frows, fadd) if finfo["drawing_read"] else None},
        "finish_v6_v7": v67,
        "stale_bindings": stale_bindings(t523, lrows, hrows, idx),
        "conflicts": [
            {"id": "C-S1", "line_set": "the 10 deficit STR.CONC.LINTEL lines", "pieces": ["T-516", "T-524"],
             "order": "T-516 relabels (lower bound / FLAGGED), T-524 sets the HELD bound; one write per line"},
            {"id": "C-S2", "line_set": "the 2 valued T-498 glue lines", "pieces": ["T-498 (staged)", "T-516", "T-524"],
             "order": "T-498 first (it creates the lines), then the ranged face (RG-1)"},
            {"id": "C-S3", "line_set": "1F-W09 perimeter", "pieces": ["T-520", "T-526"],
             "order": "same value (T-526 confirms the column end T-520 read from the drawing): one write, T-520"},
            {"id": "C-S4", "line_set": "W18 / curved-bay ends", "pieces": ["T-519", "T-527 (TODO)"],
             "order": "F-C-T519-1 (W18 END 0.578 vs 0.478) is open in T-527; it touches no deficit end and no "
                      "value in this manifest (W18 is HELD on its START): re-check the W18 row when T-527 merges"},
        ] + finfo.get("notes", []) + [{"id": "C-V7", "pieces": ["T-528", "STAIR_BED_V1"],
                                       "what": v67["v7_stair_bed"]["conflict"]}],
        "findings": [
            "F-T530-1 (T-523): 60 lintel bindings NO_CANDIDATE_LINE although the candidate carries 60 STR.CONC.LINTEL "
            "lines; mapped 1 : 1 by element id (stale_bindings)",
            "F-T530-2 (rule gap RG-1, T-498 staged R-T498-1): no case for a BOUNDED / ranged lintel face; the S "
            "package needs a rule version (ranged face [D L_lo, D L_hi])",
            "F-T530-3 (register): 'POOL-COURT SLAB' says 'FIN.WP.ROOF never takes it' while T-507 (Gate B PASS) books "
            "the open-sky membrane on FIN.WP.ROOF (B8-06 by function): register wording for the Lead",
            "F-T530-4 (code / unit): the ledge window transition is lm in T-522 but every FIN.WP.DOORWAY_TRANSITION "
            "line is m2: blank m2 line, length beside",
        ],
        "packages": packages(lrows, hrows, prows, frows, fadd, v67),
        "released_quantities_changed": 0, "candidate_files_touched": 0,
    }
    return man


def dumps(man):
    return json.dumps(man, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
