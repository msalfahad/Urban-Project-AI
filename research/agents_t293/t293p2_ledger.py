"""T-293 part 2: the slab-level formwork rows of formwork r4 tied, member by member, to the candidate concrete lines.

    python3 -I research/agents_t293/t293p2_ledger.py            # build + assert, print the summary
    python3 -I research/agents_t293/t293p2_ledger.py --write    # also write the committed outputs in this folder

Inputs (all in the repository; no drawing content): formwork r4 FORMWORK_LINES_R4.csv (T-264 MERGED 90203feb) = the
SOURCE rows; T293P2_WALK_RECORDS.json (t293p2_walk.py: the merged r3 face walk per face and member, re-run on the Drive
copy 'ST7757 dxf.dxf' 9f9d1179); the r4 ring inputs (ALSENAN_R4_INPUT.json, formwork_r4.ring_delta); the T-139 panels;
the T-298 slab panel join (SLAB_PANEL_JOIN_V3016.csv); the T-146 V3.0.12 beam runs and the T-241 run ledger; the T-149
spans (t163_formwork.beam_rows); r3 JOINT_BY_COLUMN.csv; the part-1 column bindings (FORMWORK_FACE_TO_LINE_T293.csv);
the candidate concrete lines (CANDIDATE_V3016_CONCRETE_LINES.json; slab and beam lines are byte-identical in V3.0.17:
T-254 changed only ground-beam and column lines, Gate B PASS 2026-10-25 13:35).

Scope (row size rule, Lead 16:15 'slabs first'): every r4 row of element SLAB, SLAB_EDGE, BEAM and JOINT on the GF / 1F
/ 2F roof slabs. Stairs, domes and the tank stay NAMED (part 3). Nothing is wired, no quantity changes.

Rules added here (research scope, any villa; provenance T-293 part 2 on T-163 r3 / T-264 r4 / T-234 / T-298 / T-241):

R-FW-P2-1  a slab-level aggregate row is split into the pieces its own walk produced (one piece per walked face and
           category), and the pieces close on the row: CALCULATED m2, HELD low / high, each to 0.0005 m2. A row whose
           printed value is rounded (3 dp) carries the unrounded recomputation as its source quantity, asserted to round
           to the printed value; nothing else moves.
R-FW-P2-2  owner of a piece = the member whose walked face it bounds (beam / column / slab panel). A slab-thickness band
           at a free edge beside a BEAM or COLUMN face is that member's own full-depth face (T-234 C1 BEAM > SLAB; one
           owner per face, D-T163-3), never the slab line's; beside a SLAB face it is the panel's.
R-FW-P2-3  slab soffits are tied by PANEL ID (T-298 R-T298-SLAB-JOIN-1); an INTERCHANGEABLE pair (two lines of identical
           volume) keeps the join's choice and is flagged: either line carries the same m2 within its volume difference.
R-FW-P2-4  element-method (E) pieces are per T-149 span; a span is tied to a candidate run only by the run's own recorded
           length (T-241 length_m = the span's length, exact); else SPLIT_UNRESOLVED.
R-FW-P2-5  drawing-face (G) pieces of a member that the candidate splits over several runs are SPLIT_UNRESOLVED (listed on
           the member, the run lines named, HELD by name): a walked face is never divided between runs by its length or
           position (T-264 oblique-end evidence: a run's edges can run along a face that another run's length matches).
"""

from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RES = ROOT / "research"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(RES / "agents_t163"))
sys.path.insert(0, str(RES / "agents_t264"))
import face_line_ledger as F  # noqa: E402
import t163_formwork as T  # noqa: E402  (merged r3, read-only)
import formwork_r4 as R4  # noqa: E402  (merged r4, read-only)

R4_REV = "FORMWORK_R4 (T-264 MERGED 90203feb) FORMWORK_LINES_R4.csv row {i}"
WALK_FILE = HERE / "T293P2_WALK_RECORDS.json"
CAND_FILE = HERE / "CANDIDATE_V3016_CONCRETE_LINES.json"
P1_FILE = HERE / "FORMWORK_FACE_TO_LINE_T293.csv"
SLAB_LEVEL = {"BEAM", "SLAB", "SLAB_EDGE", "JOINT"}
CALC, HELD = "CALCULATED", "HELD"
FLR = {"GF": "GF roof slab (p.4)", "1F": "1F roof slab (p.5)", "2F": "2F roof slab (p.6)"}
C59 = ("BM-GF-046", "BM-GF-059", 0.50 * 1.501, 2 * 1.501 * (0.75 - 0.16))   # r3 alsenan c59 (B24 cantilever end)
RING_R3_FACES = ("GF-035", "GF-060")        # r3 bound them to BM-GF-049; r4 replaces them by the T-252 ring
RING_MEMBER = "BM-GF-050"                   # T-149 B7 ring arc pieces; the candidate run BM-GF-050.r2#RING-B7
RING_ALIASES = {"BM-GF-050": "BM-GF-050.r2", "BM-GF-051": "BM-GF-050.r2", "BM-GF-052": "BM-GF-050.r2",
                "BM-GF-060": "BM-GF-050.r2"}   # V3012 run RING-B7 supersedes BAND0050 / 0051 / 0052 / 0053 (T-252)
CB1 = "BM-GF-042"
DUP = "DUPLICATE_IN_SOURCE"


def _f(v):
    return None if v in (None, "") else float(v)


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def rd(rel):
    return list(csv.DictReader((ROOT / rel).open(encoding="utf-8")))


# ------------------------------------------------------------------------------------------------ bindings

def candidate():
    return json.loads(CAND_FILE.read_text(encoding="utf-8"))


def beam_binding(lines_by_el):
    """T-149 member -> [candidate line ids] via the V3.0.12 runs (T-146), and run -> line"""
    runs = rd("research/agents_t146/V3012_BEAM_RUNS.csv")
    by_member, by_run, why = collections.defaultdict(list), {}, {}
    for r in runs:
        fl, run = r["floor"], r["run"]
        hl = f"HL:BEAM_LEDGER:{fl}:{run}"
        sup = re.findall(r"((?:[PU]-C:BEAMS:\w\w:BAND[\d.]+)|(?:HL:DOME_RING:[\w:-]+)) \(kept\)", r["supersedes"])
        el = hl if hl in lines_by_el else (sup[0] if sup and sup[0] in lines_by_el else None)
        if el is None:
            raise F.Refused(f"run {run}: no candidate line")
        lid = lines_by_el[el]["line_id"]
        by_run[run] = lid
        if run.endswith(".r2"):
            by_run[run[:-3]] = lid             # T-241 names the run before its T-252 r2 re-issue (BAND0021.1)
        m = run.split("#")[0].replace(".r2", "")
        by_member[m].append(lid)
    for a in RING_ALIASES:                     # BM-GF-050.r2#RING-B7 is keyed BM-GF-050 above
        by_member[a] = list(by_member["BM-GF-050"])
    return by_member, by_run


def t241_runs():
    out = collections.defaultdict(list)
    for r in rd("research/agents_t241/LEDGER_T241.csv"):
        out[r["member"]].append(r)
    return out


def column_binding():
    """part 1 (Gate A PASS 12:19): COLUMN:<T-119 id> -> line id"""
    out = {}
    for r in csv.DictReader(P1_FILE.open(encoding="utf-8")):
        m = r["members"]
        if m.startswith("COLUMN:") and r["tie"] == F.TIED:
            out.setdefault(m, r["line_id"])
    return out


def panel_binding():
    return {r["panel"]: r for r in rd("research/agents_t298/SLAB_PANEL_JOIN_V3016.csv")}


# ------------------------------------------------------------------------------------------------ the pieces

def r4_rows():
    return rd("research/agents_t264/FORMWORK_LINES_R4.csv")


def walk():
    return json.loads(WALK_FILE.read_text(encoding="utf-8"))["records"]


def ring():
    inp = json.loads((RES / "agents_t264/ALSENAN_R4_INPUT.json").read_text(encoding="utf-8"))
    return R4.ring_delta(inp)


def piece(src, n, member, m2=None, lo=None, hi=None, note="", face=None):
    p = dict(src, face_id=f"{src['face_id']}.{n}", split_of=src["face_id"], members=[member], m2=m2, lo=lo, hi=hi,
             basis_note=note)
    if face:
        p["walk_face"] = face
    return p


def beam_key(m):
    return "BEAM:" + m


def classify(rows, W, rg, by_run, t241):
    """r4 slab-level rows -> (sources, pieces, named). Each source row's pieces close on it (asserted)."""
    src, pieces, named = [], [], {}
    pan = [p for p in rd("research/agents_t139/PANELS.csv") if p["cls"] == "SLAB"]
    beams = T.beam_rows()
    span_len = {r["row_id"]: r["length_m"] for r in rd("research/agents_t149/T149_SPANS_INPUT.csv")}
    joints = {r["column"]: r for r in rd("research/agents_t163/JOINT_BY_COLUMN.csv")}
    inp = json.loads((RES / "agents_t264/ALSENAN_R4_INPUT.json").read_text(encoding="utf-8"))
    by = collections.defaultdict(list)
    for r in W:
        by[(r["floor"], r["category"])].append(r)

    def walk_pieces(rec, fl, cats, status, held=False, skip=()):
        out = []
        for c in cats:
            for w in sorted(by[(fl, c)], key=lambda q: q["face"]):
                if w["owner_status"] != status and status is not None:
                    continue
                if w["face"] in skip:
                    continue
                if w["owner_kind"] == "SLAB":
                    mem = "PANELFACE:" + w["face"]
                elif w["owner_kind"] == "BEAM":
                    mem = ("RUN:" + w["run"]) if w.get("run") not in (None, "REST") else beam_key(w["owner"])
                elif w["owner_kind"] == "COLUMN":
                    mem = "COLUMN:" + w["owner"]
                else:
                    mem = "UNMATCHED:" + w["face"]
                v = w["m2"]
                note = f"walk face {w['face']} {c}" + (f" (run {w['run']}: R-FW-P2-5 positional attribution)"
                                                        if w.get("run") else "")
                tag = f"{w['face']}~{w['run']}" if w.get("run") else w["face"]
                if held:
                    out.append(piece(rec, f"{tag}.{c.split(':')[0]}", mem, None, 0.0 if held == "range" else v,
                                     v, note, w["face"]))
                else:
                    out.append(piece(rec, f"{tag}.{c}", mem, v, None, None, note, w["face"]))
        return out

    for i, x in enumerate(rows):
        if x["element"] not in SLAB_LEVEL:
            continue
        rec = {"face_id": f"R4-{i:03d}", "revision": R4_REV.format(i=i), "element": x["element"], "floor": x["floor"],
               "item": x["item"], "face_kind": x["element"], "contact": "FORM", "alternative": "", "method": x["method"],
               "m2": _f(x["m2"]), "lo": _f(x["held_lo"]), "hi": _f(x["held_hi"]), "status": x["status"],
               "refs": x["refs"], "basis": "", "basis_note": "", "unit": "m2",
               "members": [f"AGGREGATE:{x['element']}:{x['floor']}"]}
        fl, it, el, me, st = x["floor"], x["item"], x["element"], x["method"], x["status"]
        P = []
        if st in ("INFO",):
            named[rec["face_id"]] = (F.INFO, "information row (comparison walk), not a quantity")
        elif st == "OWNED_BY_OTHER_LINE":
            named[rec["face_id"]] = (F.NAMED, "owned by another formwork line (r4: the ring / CB1 or the dome ring "
                                              "line, D-T163-3); part 3 (domes) ties the dome-opening face")
        elif el == "SLAB" and "sunken-slab" in it:
            named[rec["face_id"]] = (F.NAMED, "HELD, no quantity: drop not printed (D-41); 50.885 m of sunken-panel "
                                              "edges are beam faces (owners: the beams around the sunken panels)")
        elif el == "SLAB" and "winders" in it:
            named[rec["face_id"]] = (F.NAMED, "part 3 (stairs): slab under the main-stair winders, a T-111 / T-139 "
                                              "NEW line; tied with the stair lines")
        elif el == "SLAB" and "soffit, net panels" in it:
            for p in sorted((p for p in pan if p["floor"] == fl), key=lambda q: q["id"]):
                P.append(piece(rec, p["id"], "PANEL:" + p["id"], float(p["area"]), note=f"T-139 panel {p['id']} net "
                               f"area (C1: between beam and column faces)"))
        elif el == "BEAM" and me == "E" and ("beam soffits" in it or "beam sides" in it):
            side = "beam sides" in it
            for b in beams:
                if b["floor"] != fl or "upstand" in b["type"] or b["status"] != "CALCULATED" or not (b["B"] and b["D"]
                                                                                                  and b["L"]):
                    continue
                v = T.beam_sides(b["L"], b["D"], 0.16) if side else b["B"] * b["L"]
                mem = span_member(b["member"], _f(span_len.get(b["row"])), t241.get(b["member"], []))
                f = ("2 x %.4f x (%.2f - 0.16)" % (b["L"], b["D"])) if side else ("%.2f x %.4f" % (b["B"], b["L"]))
                pid = b["row"]
                if any(q["face_id"] == f"{rec['face_id']}.{pid}" for q in P):
                    # r3 beam_rows() appends R138 (CB5 span 2, T-145) although T149_SPANS_INPUT.csv already holds it:
                    # the E row counts that span twice. Kept so the row closes; never tied (finding F-T293-P2-01)
                    pid += ".DUP"
                    named[f"{rec['face_id']}.{pid}"] = (DUP, "span counted twice in the r3 / r4 element method "
                                                             "(beam_rows() re-appends R138, already in the T-149 spans "
                                                             "csv): formwork defect F-T293-P2-01, not a face")
                P.append(piece(rec, pid, mem, v, note=f"T-149 span {b['row']} {b['member']} {b['mark']}: {f}"))
        elif el == "BEAM" and me == "E=G" and "upstand" in it:
            for b in beams:
                if b["floor"] == fl and "upstand" in b["type"]:
                    P.append(piece(rec, b["row"], beam_key(b["member"]), 2 * b["D"] * b["L"],
                                   note=f"T-149 {b['row']} {b['member']}: 2 x {b['D']} x {b['L']}"))
        elif el == "BEAM" and me == "G" and it.endswith("beam soffits"):
            P = walk_pieces(rec, fl, ["BEAM_SOFFIT"], CALC, skip=RING_R3_FACES if fl == "GF" else ())
            if fl == "GF":
                P.append(piece(rec, "C59", beam_key(C59[0]), -C59[2], note="r3 c59: the B24 east cantilever end "
                               "BM-GF-059 (HELD, Q-61 C(4)) lies inside the B24 face GF-011: 0.50 x 1.501 leaves B24"))
                P.append(piece(rec, "RING", beam_key(RING_MEMBER), rg["ring"]["soffit"], note="r4: ring B7 soffit "
                               "from its own arcs (T-252 plan 0.666406) replaces r3's GF-035 / GF-060 (BM-GF-049)"))
        elif el == "BEAM" and me == "G" and it.endswith("beam sides below the slab"):
            P = walk_pieces(rec, fl, ["BEAM_SIDE"], CALC, skip=RING_R3_FACES if fl == "GF" else ())
            if fl == "GF":
                P.append(piece(rec, "C59", beam_key(C59[0]), -C59[3], note="r3 c59: 2 x 1.501 x (0.75 - 0.16) of "
                               "BM-GF-059 leaves B24"))
                P.append(piece(rec, "RING", beam_key(RING_MEMBER), rg["ring"]["side"], note="r4: ring B7 faces on its "
                               "arcs (T-252 R-BEAM-CURVED-AREA-2)"))
                P.append(piece(rec, "CB1", beam_key(CB1), rg["cb1"]["side"], note="r4: the CB1 face the void reaches "
                               "(2A9, %.4f m)" % rg["cb1"]["L"]))
        elif el == "BEAM" and "held / conflict members" in it:
            P = walk_pieces(rec, fl, ["BEAM_SOFFIT", "BEAM_SIDE"], HELD, held="point")
            if fl == "GF":
                for n, v in (("C59S", C59[2]), ("C59D", C59[3])):
                    P.append(piece(rec, n, beam_key(C59[1]), None, v, v, note="r3 c59: BM-GF-059 inside the B24 face"))
        elif el in ("BEAM", "JOINT", "SLAB_EDGE") and " next to " in it and me == "G" and st == HELD:
            nk = it.split(" next to ")[1].split(" (")[0]
            pre = {"beam_side": "BEAM_SIDE_HELD_M2", "junction": "JUNCTION_HELD_M2", "joint": "JOINT_HELD_M2",
                   "edge": "EDGE_HELD_M2"}[it.split(") ")[1].split(" faces")[0]]
            cat = pre if nk == "held member" else f"{pre}:{nk}"
            P = walk_pieces(rec, fl, [cat], None, held="range")
        elif el == "BEAM" and "bound to no member" in it:
            P = walk_pieces(rec, fl, ["UNMATCHED_PLAN"], None, held="point")
        elif el == "SLAB_EDGE" and "every free edge" in it:
            P = walk_pieces(rec, fl, ["EDGE_BAND"], None)
            if fl == "GF":
                P.append(piece(rec, "RING", beam_key(RING_MEMBER), rg["ring"]["band"], note="r4: slab band of the "
                               "pool-court void on the ring's void arcs (one owner per face, D-T163-3)"))
                P.append(piece(rec, "CB1", beam_key(CB1), rg["cb1"]["band"], note="r4: slab band on CB1 (2A9)"))
        elif el == "JOINT" and st == CALC and "at the STATED section" in it:
            cf = set(re.findall(r"COL-1F-\d+", next(r["item"] for r in rows if "section-CONFLICT columns" in r["item"]))) \
                if fl == "1F" else set()
            for c, j in sorted(joints.items()):
                if j["storey"] == fl and j["status"] == CALC and j["stated_status"] == CALC and c not in cf:
                    P.append(piece(rec, c, "COLUMN:" + c, float(j["joint_stated_lo"]), note=f"r3 JOINT_BY_COLUMN {c} "
                                   "stated-section joint"))
            if fl == "1F":
                P.append(piece(rec, "COL-1F-57", "COLUMN:COL-1F-57", inp["planted_col_1f_57"]["joint_stated_lo"],
                               note="r4: planted COL-1F-57 (T-248) stated = drawn 0.20 x 0.70"))
        elif el == "JOINT" and "section-CONFLICT columns" in it:
            for c in sorted(set(re.findall(r"COL-1F-\d+", it))):
                j = joints[c]
                v = sorted([float(j["joint_m2"]), float(j["joint_stated_lo"])])
                P.append(piece(rec, c, "COLUMN:" + c, None, v[0], v[1], note=f"{c}: drawn-outline vs stated joint"))
        elif el == "JOINT" and "whose stated section cannot be placed" in it:
            for c in ("COL-GF-14", "COL-GF-24", "COL-GF-30"):
                j = joints[c]
                P.append(piece(rec, c, "COLUMN:" + c, None, min(float(j["joint_m2"]), float(j["joint_stated_lo"])),
                               max(float(j["joint_m2"]), float(j["joint_stated_hi"])), note=f"{c}: T-256 CONFLICT"))
        elif el == "JOINT" and it.endswith("joint faces of HELD columns"):
            P = walk_pieces(rec, fl, ["JOINT_FACE"], HELD, held="point")
            if fl == "1F":
                P = [p for p in P if p["members"][0] != "COLUMN:COL-1F-57"]
        else:
            raise F.Refused(f"slab-level r4 row {rec['face_id']} not classified: {it}")
        if rec["face_id"] not in named and not P:
            raise F.Refused(f"{rec['face_id']}: no pieces ({it})")
        if P:
            close_row(rec, P)
        src.append(rec)
        if rec["face_id"] in named:
            pieces.append(rec)
        pieces.extend(P)
    return src, pieces, named


def span_member(member, span_length, runs):
    """R-FW-P2-4: an element-method span goes to the candidate run whose own recorded length equals the span's
    (exact); a member with one run keeps its member key (its one line); anything else stays on the member (SPLIT)"""
    if len(runs) <= 1:
        return beam_key(member)
    rr = [r for r in runs if span_length is not None and _f(r["length_m"]) is not None
          and abs(float(r["length_m"]) - span_length) < 1e-9]
    return ("RUN:" + rr[0]["run"]) if len(rr) == 1 else beam_key(member)


def close_row(rec, P):
    """R-FW-P2-1: the pieces close on their row; a 3-dp printed value takes the unrounded recomputation"""
    for k in ("m2", "lo", "hi"):
        s = sum(p[k] or 0.0 for p in P)
        want = rec[k]
        if want is None:
            if any(p[k] for p in P):
                raise F.Refused(f"{rec['face_id']}: pieces carry {k} the row has not")
            continue
        if abs(s - want) <= 1e-6:
            rec[k] = s
        elif abs(round(s, 3) - want) < 1e-9 or abs(s - want) <= 0.0005 + 1e-9:
            # r4 prints 3 dp, or a 3-dp r3 value + an unrounded r4 delta: the residual is that rounding only
            rec.setdefault("printed", {})[k] = want
            rec.setdefault("printed_residual", {})[k] = round(want - s, 6)
            rec[k] = s
        else:
            raise F.Refused(f"{rec['face_id']} {rec['item'][:50]}: pieces {k} {s:.6f} != row {want}")


def binding_all(cand, by_member, by_run, cols, pj):
    lines = {x["line_id"]: x for x in cand["lines"]}
    b = {"_reason": {}}
    for m, ids in by_member.items():
        b[beam_key(m)] = sorted(set(ids))
    for run, lid in by_run.items():
        b["RUN:" + run] = [lid]
    for m, lid in cols.items():
        b[m] = [lid]
    for p, r in pj.items():
        b["PANEL:" + p] = [r["line_id"]]
        if "/" not in p:
            b["PANELFACE:" + p] = [r["line_id"]]
    return b, lines


def build():
    cand = candidate()
    lines_by_el = {x["element_id"]: x for x in cand["lines"]}
    by_member, by_run = beam_binding(lines_by_el)
    rows = r4_rows()
    src, faces, named = classify(rows, walk(), ring(), by_run, t241_runs())
    b, lines = binding_all(cand, by_member, by_run, column_binding(), panel_binding())
    # T-241 (MERGED): 'BM-GF-062#GF-112 ... partition face GF-112 0.20 x 0.50' -> the walk's unmatched face GF-112
    b["UNMATCHED:GF-112"] = list(b[beam_key("BM-GF-062")])
    b["_reason"].update({k: "band piece bound to no register member (no mark in or near it): no concrete line"
                         for f in faces for k in f["members"] if k.startswith("UNMATCHED:")})
    out = F.tie(faces, b, lines, named, source=src)
    pj = panel_binding()
    for r in out["rows"]:
        m = r["members"][0]
        if m.startswith("PANEL") and r["tie"] == F.TIED:
            j = pj.get(m.split(":", 1)[1])
            if j and j["join"] != "EXACT":
                r["tie_reason"] = f"T-298 join {j['join']} ({j['group']}): either line of the pair carries the same " \
                                  f"m2 within its volume difference {j['diff_m3']} m3 (R-FW-P2-3)"
    v17 = v3017_changes()
    for r in out["rows"]:
        lid = r.get("line_id")
        if not lid:
            continue
        if lid in v17:
            r["line_v3017"] = "V3.0.17 changed: %s (%s)" % v17[lid]
            if v17[lid][0] == "NOT_APPLICABLE_WITH_EVIDENCE":
                raise F.Refused(f"{r['face_id']}: tied to {lid}, NOT_APPLICABLE in V3.0.17 (no drawn member)")
        else:
            r["line_v3017"] = "byte-identical to V3.0.16"
        eff = ("BLOCKED_RFI" if v17[lid][0] == "BLOCKED_RFI" else "MEASURED") if lid in v17 else r.get("line_state")
        if r["status"] == CALC and eff in ("BOUNDED_EXPOSURE", "BLOCKED_RFI"):
            r["line_flag"] = "CALC_FACE_ON_UNMEASURED_LINE: the face is calculated, its concrete line is not " \
                             "measured (R-FW-LINE-5: shown beside the line, never as a measured element)"
    return cand, src, out


def v3017_changes():
    """T-254 (Gate B PASS 13:35): the 49 lines V3.0.17 changed or added, by line id -> (V3.0.17 cell, evidence)"""
    out = {}
    for ln in (RES / "agents_t254/T-254_BASIS_CORRECTION.md").read_text(encoding="utf-8").splitlines():
        if ln.startswith("| L-"):
            c = [x.strip() for x in ln.strip("|").split("|")]
            out[c[0]] = (c[6], c[7])
    if len(out) != 49:
        raise F.Refused(f"T-254 per-line table: {len(out)} rows, expected 49 (48 changed + 1 added)")
    return out


def totals(out):
    t = collections.defaultdict(lambda: collections.defaultdict(lambda: [0.0, 0.0, 0.0, 0]))
    for r in out["rows"]:
        k = (r.get("element"), r.get("floor"), r["status_in"], r.get("method"))
        for i, f in enumerate(("m2", "lo", "hi")):
            v = r.get(f)
            if f == "m2" and v is None:
                v = r.get("held_from")
            t[r["tie"]][k][i] += v or 0.0
        t[r["tie"]][k][3] += 1
    return {tie: {"|".join(map(str, k)): [round(v[0], 6), round(v[1], 6), round(v[2], 6), v[3]] for k, v in
                  sorted(d.items())} for tie, d in sorted(t.items())}


KEYS = ["face_id", "revision", "element", "floor", "item", "face_kind", "method", "m2", "lo", "hi", "status",
        "status_in", "members", "walk_face", "tie", "line_id", "line_item_code", "line_element_id", "line_state",
        "line_v3017", "line_flag", "tie_reason", "held_from", "split_of", "split_lines", "basis_note"]


def write(outdir=HERE):
    cand, src, out = build()
    with (outdir / "FORMWORK_FACE_TO_LINE_T293_P2.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=KEYS, extrasaction="ignore")
        w.writeheader()
        for r in out["rows"]:
            x = dict(r)
            x["members"] = ";".join(r["members"])
            x["split_lines"] = ";".join(r.get("split_lines") or [])
            for k in ("m2", "lo", "hi", "held_from"):
                if isinstance(x.get(k), float):
                    x[k] = "%.6f" % x[k]
            w.writerow(x)
    lines = {x["line_id"]: x for x in cand["lines"]}
    cons = F.consumer(out["rows"], lines, "ARCH_TAKEOFF_V3.0.17 (slab / beam / column lines byte-identical to "
                      "V3.0.16, T-254)", cand["project"])
    cons["part"] = "2 (slab-level rows); union with T199_FORMWORK_BY_LINE_T293.json (part 1): the part-1 NAMED rows " \
                   "R4-nnn of element BEAM / SLAB / SLAB_EDGE / JOINT are replaced by the R4-nnn.* pieces here"
    (outdir / "T199_FORMWORK_BY_LINE_T293_P2.json").write_text(json.dumps(cons, indent=1, sort_keys=True) + "\n",
                                                               encoding="utf-8")
    summ = summary(cand, src, out)
    (outdir / "summary_t293_p2.json").write_text(json.dumps(summ, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return summ


def summary(cand, src, out):
    rows = out["rows"]
    lines_tied = collections.defaultdict(set)
    for r in rows:
        if r["tie"] == F.TIED:
            lines_tied[r["line_item_code"]].add(r["line_id"])
    cl = {x["line_id"]: x for x in cand["lines"]}
    live = collections.defaultdict(set)
    for x in cand["lines"]:
        if x["item_code"] in ("STR.CONC.SLAB", "STR.CONC.BEAM") and x["evidence_state"] != "NOT_APPLICABLE_WITH_EVIDENCE":
            live[x["item_code"]].add(x["line_id"])
    return {"schema": "T293_P2_SUMMARY_V1", "source_rows": len(src), "pieces": len(rows),
            "by_tie": dict(collections.Counter(r["tie"] for r in rows)),
            "closure": out["closure"], "totals_by_tie": totals(out),
            "lines_with_faces": {k: len(v) for k, v in sorted(lines_tied.items())},
            "live_lines_without_faces": {k: sorted(v - lines_tied[k]) for k, v in sorted(live.items())},
            "na_lines_with_faces": sorted(l for v in lines_tied.values() for l in v
                                          if cl[l]["evidence_state"] == "NOT_APPLICABLE_WITH_EVIDENCE"),
            "inputs_sha256": {p: _sha(ROOT / p)[:8] for p in (
                "research/agents_t264/FORMWORK_LINES_R4.csv", "research/agents_t293/T293P2_WALK_RECORDS.json",
                "research/agents_t139/PANELS.csv", "research/agents_t298/SLAB_PANEL_JOIN_V3016.csv",
                "research/agents_t146/V3012_BEAM_RUNS.csv", "research/agents_t241/LEDGER_T241.csv",
                "research/agents_t163/JOINT_BY_COLUMN.csv", "research/agents_t293/CANDIDATE_V3016_CONCRETE_LINES.json")}}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    if a.write:
        s = write()
    else:
        cand, src, out = build()
        s = summary(cand, src, out)
    print(json.dumps({k: s[k] for k in ("source_rows", "pieces", "by_tie", "lines_with_faces")}, indent=1))


if __name__ == "__main__":
    main()
