"""T-638 development-villa build (research, unwired): the 370 HELD-blank B10-13 STR.FORMWORK lines of the 10 Nov trial
BOQ dry run (T-630, candidate ARCH_TAKEOFF_V3.0.58 = V3.0.57 line index + 5 roof WP lines, overlay V15) classed one by
one under R-T638-1 (t638_rules.py), with a fix row FR-T638-n wherever the member's concrete is RELEASED and the face
figure of the same formwork method is proven; plus (D) the T-632 slab-edge strip.

Rebuild (wrapper only): `URBAN_T638_WRITE=1 bash scripts/agent_env.sh pytest --tree task-T-638 tests/t638/test_t638.py::
test_write_outputs`; check: `bash scripts/agent_env.sh pytest --tree task-T-638 tests/t638`.

Reads only merged repository files (sha256-pinned below). Writes out/FORMWORK_HOLD_CENSUS_T638.json and .md. No
coordinate, no drawing text, no client name. No candidate, released (V2.9 + route G), rule / knowledge version or
registry file is touched; the fix rows are proposals for the wiring manifest (lane I), not applied here."""
from __future__ import annotations

import ast
import csv
import hashlib
import json
import re
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import t638_rules as R  # noqa: E402

D, S, q = R.D, R.S, R.q
SCHEMA, RULE = "URBAN_T638_FORMWORK_HOLD_CENSUS_V1", "R-T638-1"
T630 = "research/agents_t630/out/E2E_BOQ_DRY_RUN_T630.json"
INDEX = "research/agents_t507/out/LINE_INDEX_V3_0_57.json"
T474 = "research/agents_t474/out/FORMWORK_LINE_MAP_T474.csv"
T332 = "research/agents_t332/FORMWORK_T332_BY_FACE.csv"
R4 = "research/agents_t264/FORMWORK_LINES_R4.csv"
T119 = "research/agents_t119/COLUMNS_TO_CONTROLLING_MEMBER.csv"
T632 = "research/agents_t632/out/T632_UPSTAND_CENSUS.json"
PINS = {T630: "e5dde7867c8fe6ad", INDEX: "fed5141ea31bfdd9", T474: "7a3bfa6a56628172", T332: "15c188724a60d580",
        R4: "8681948753f37c81", T119: "dbe1ce155c7d7356", T632: "57bcb9c0219c3cfd"}
OUT_JSON = HERE / "out" / "FORMWORK_HOLD_CENSUS_T638.json"
OUT_MD = HERE / "out" / "FORMWORK_HOLD_CENSUS_T638.md"
FAMILY, ITEM = "B10-13", "STR.FORMWORK"
SHAFT_TOL = Decimal("0.002")     # m2: the method's drawn-outline perimeter vs the printed section (named residual)

STATE_CAUSE = {
    "BLOCKED_RFI": "concrete line BLOCKED_RFI (a designer RFI holds its section / depth / extent)",
    "BOUNDED_EXPOSURE": "concrete line BOUNDED_EXPOSURE (column exposure / section bounded, not settled: T-397)",
    "PROVISIONAL": "concrete line HELD on a range (two drawn readings, not settled)",
    "SOURCE_DERIVED": "concrete line HELD",
}
NEIGHBOUR = {
    "RING_MIX": "the 1F void ring / dome ring mix (RING_MIX) whose faces are not settled on this storey",
    "STAIR": "the stair concrete beside it (flight / landing contact not settled, T-345 flights)",
    "HELD_EDGE": "a held slab edge beside it (edge position / drop not settled)",
    "UNMATCHED": "an unmatched band piece beside it (no register member)",
    "": "a held member beside it (its section is held)",
}


def sha16(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()[:16]


def check_pins():
    bad = {p: (sha16(p), v) for p, v in PINS.items() if sha16(p) != v}
    if bad:
        raise R.RuleError(f"input drift (sha256[:16] now, pinned): {bad}")


def _csv(p):
    with open(ROOT / p, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def load():
    check_pins()
    t630 = json.loads((ROOT / T630).read_text(encoding="utf-8"))
    idx = json.loads((ROOT / INDEX).read_text(encoding="utf-8"))
    return {"t630": t630, "lines": {x["line_id"]: x for x in idx["lines"]},
            "map": {r["line_id"]: r for r in _csv(T474)}, "faces": _csv(T332), "r4": _csv(R4),
            "t119": {r["id"]: r for r in _csv(T119)},
            "t632": json.loads((ROOT / T632).read_text(encoding="utf-8"))}


# ---- face causes ----------------------------------------------------------------------------------------------------

def face_cause(f, data):
    """(kind, cause) for one T-332 face record. kind: SHAFT_D_SETTLED (the only face kind this task frees), B_ADJ,
    B_LINE, C_*."""
    fid, note = f["face_id"], f.get("basis_note") or ""
    m = re.match(r"R4-(\d+)$", fid)
    if m:
        row = data["r4"][int(m.group(1))]
        basis = row["basis"]
        if "FRAMING_MEMBER_HELD_D_SETTLED" in basis:
            return "SHAFT_D_SETTLED", "column shaft: framing member held, controlling depth settled by calculated " \
                                      "members (T-119 r2 FRAMING_MEMBER_HELD_D_SETTLED)"
        if "FRAMING_MEMBER_HELD_D_OPEN" in basis:
            return "C_FRAMING_D", "column shaft: depth of an unlabelled framing member not printed (T-119 " \
                                  "FRAMING_MEMBER_HELD_D_OPEN, designer D-26): D_ctrl >= 0.75, the shaft is an " \
                                  "upper bound only (AT_MOST)"
        if "LEVEL_Q54B" in basis:
            return "C_LEVEL", "annex datum: +4.30 is a roof mark, not a proven slab top (owner Q-54 B HOLD)"
        if "CONFLICT" in basis:
            return "C_CONFLICT", "section CONFLICT in the issued set: " + basis[basis.find("CONFLICT"):][:120]
        if "casting method not specified" in basis or "as DOME-A" in basis and "extrados" in row["item"]:
            return "C_METHOD", "dome shell top (extrados) form: the casting method is not specified on the dome " \
                               "detail (T-185); a top form exists only if the shell is cast between two forms"
        if "material and thickness not printed" in basis or ("as DOME-A" in basis and "drum" in row["item"]):
            return "C_THICKNESS", "dome drum (section B-B 1.30 m): material and thickness not printed (T-185)"
        if "no section mark" in basis:
            return "C_SECTION", "dome ring: " + basis[basis.find("no section mark"):][:140]
        if "D-39" in basis:
            return "C_LEVEL", "2F roof structural top not printed, only the finished +13.90 (D-39, T-248): shaft " \
                              "is an upper bound only (AT_MOST)"
        if "UPSTAND_DOWNSTAND_D44" in basis:
            return "C_SECTION", "framing band read as upstand or downstand not settled (D-44): shaft range"
        if "no structural detail" in basis:
            return "C_THICKNESS", "tower dome shell: no structural detail, thickness / support not printed (owner " \
                                  "Q-18: never a default)"
        if "T-185" in basis:
            return "C_SECTION", "dome: " + basis[:150]
        if note.startswith("annex depth D-35"):
            return "C_CONFLICT", "annex ground-beam depth D-35 CONFLICT (T-253 s.3 / T-289): no value adopted"
        if "court run" in note:
            return "C_SECTION", "court ground-beam run: section not established (T-253 s.4)"
        if "D-33" in note or "D-34" in note:
            return "C_SECTION", "interior ground-beam depth by span (ST p.13), D-33 / D-34 where named: range only"
        if f.get("element") == "GROUND_BEAM" and f.get("face_kind") == "COVER":
            return "C_SECTION", "tee cover 0.30 x min(D_in, D): the incoming member's depth is a candidate range"
        if f.get("element") in ("FOOTING", "STRAP", "BOUNDARY", "POOL", "GROUND_BEAM", "NECK"):
            return "C_SECTION", f"{f['element'].lower()} face held in formwork r4: {(basis or note)[:120]}"
        return "C_OTHER", (basis or note)[:160] or "held in formwork r4"
    if fid.startswith("R4-") and "." in fid:
        kind = fid.split(".")[-1]
        nb = ""
        mm = re.search(r"_HELD_M2:(\w+)", note)
        if mm:
            nb = mm.group(1)
        if kind.endswith("_HELD_M2") or "HELD_M2" in kind:
            return "B_ADJ", f"{kind.split(':')[0]}: contact 0 .. its range, decided by " + NEIGHBOUR.get(nb, nb)
        if kind == "JOINT_FACE":
            return "B_ADJ", "joint face of a HELD column (the column's framing / section hold decides the strip)"
        if kind in ("BEAM_SIDE", "BEAM_SOFFIT", "EDGE_BAND") and "held / conflict" in (f.get("item") or "") + note:
            return "B_LINE", "member held / in conflict: its sides and soffit follow its concrete line"
        if kind in ("BEAM_SIDE", "BEAM_SOFFIT", "EDGE_BAND"):
            return "B_LINE", f"{kind}: measured, held with its concrete line (R-T308-5 / R-T332-2)"
        return "B_ADJ", f"{kind}: {note[:120]}"
    if fid.startswith("T282-"):
        return "C_SECTION", "end / side delta on a ground-beam run whose depth or length is held (T-282): " + note[:80]
    if fid.startswith("T332-POOL-BACK"):
        return "C_CONTACT", "pool back on the boundary-wall line: what it is cast against is not established " \
                            "(T-320 F-T320-05, Q-28 lower band)"
    if fid.startswith("T332-F8-POOL"):
        return "C_CONFLICT", "F8 faces inside the pool envelope (CONFLICT, T-320)"
    if fid.startswith("R5-BAND0049"):
        return "B_ADJ", "BAND0049 side next to the unbound partition piece (drawn arcs, B7 20 x 75; T-308 walk delta)"
    return "C_OTHER", note[:160] or "held face"


def face_record(f, cause_kind, cause):
    return {"face_id": f["face_id"], "element": f["element"], "floor": f["floor"], "kind": f["face_kind"],
            "status": f["status"], "m2": f["m2"] or None, "lo": f["lo"] or None, "hi": f["hi"] or None,
            "held_from": f["held_from"] or None, "cause_kind": cause_kind, "cause": cause}


# ---- per line -------------------------------------------------------------------------------------------------------

def concrete_cause(cl, data):
    c = data["lines"].get(cl)
    m = next((r for r in data["map"].values() if r["concrete_line"] == cl), None)
    st = (m or {}).get("concrete_state_live") or "HELD"
    txt = STATE_CAUSE.get(st, "concrete line HELD")
    if c and (c.get("held_low") is not None or c.get("held_high") is not None):
        txt += f" [{S(c.get('held_low'))} .. {S(c.get('held_high'))} m3]"
    return f"{cl} {c['item_code'] if c else '?'} {c['element_id'] if c else ''}: {txt}"


def column_check(f, data):
    """prove the D_SETTLED shaft face with T-119 r2: perimeter x (interval - D_ctrl) by hand from the printed section."""
    row = data["r4"][int(f["face_id"][3:])]
    col = re.match(r"(COL-\w+-\d+)", row["item"]).group(1)
    t = data["t119"][col]
    if t["hold_cause"] != "FRAMING_MEMBER_HELD_D_SETTLED":
        raise R.RuleError(f"{col}: T-119 cause {t['hold_cause']}")
    a, c = (D(x) for x in t["section"].split("x"))
    hand = q(2 * (a + c) * (D(t["interval"]) - D(t["D_ctrl"])))
    face = D(f["lo"])
    if f["lo"] != f["hi"] or abs(face - hand) > SHAFT_TOL:
        raise R.RuleError(f"{col}: face {f['lo']}..{f['hi']} vs hand {hand}")
    return {"column": col, "section": t["section"], "interval": t["interval"], "D_ctrl": t["D_ctrl"],
            "hand_m2": S(hand), "method_m2": S(face), "residual_m2": S(face - hand),
            "held_member": t["framing"].split("| held:")[-1].strip()}


def classify(lid, data, faces_by_key, faces_by_id):
    line = data["lines"][lid]
    el = line["element_id"]
    p = el.split(":")
    mrow = data["map"].get(lid)
    base = {"line_id": lid, "item_code": ITEM, "family": FAMILY, "element_id": el}

    # lift tie beam (T-419 ADD_HELD, after the T-474 map)
    if el.startswith("LIFT_TIE_BEAM:"):
        cl = "L-5ae06fda7d729d54c033"
        part = p[-1]
        return dict(base, **{"class": "B_HELD", "concrete_line": cl, "concrete_class": data["lines"][cl]["class"],
                             "cause": f"lift tie beam {part.lower()}: concrete {cl} STR.CONC.LIFT HELD (section D-43 not "
                                      "printed; 5.500 m DRAWING-CONFIRMED, T-419): 2 x L x d / L x b with d, b HELD",
                             "faces": [], "sources": ["research/agents_t419/T-419_TIE_GB_MASONRY_INTEGRATION.md"]})

    if p[0] == "FW" and p[1].startswith("L-"):
        cl = p[1]
        cc = data["lines"][cl]["class"]
        if p[2] == "OQ10":
            fs = [x for x in data["faces"] if x["new_line_id"] == cl and x["alternative"].startswith("OQ10")
                  and x["method"] == p[3] and x["status"] == "ALTERNATIVE"]
            faces = [face_record(x, "C_OQ10", "below natural ground: formed vs earth-cast not printed (OQ-10)")
                     for x in fs]
            if cc != "RELEASED":
                return dict(base, **{"class": "B_HELD", "concrete_line": cl, "concrete_class": cc,
                                     "cause": concrete_cause(cl, data) + "; and OQ-10 below natural ground",
                                     "faces": faces, "sources": [T474, T332]})
            return dict(base, **{
                "class": "C_HELD", "concrete_line": cl, "concrete_class": cc,
                "cause": "OQ-10 pair (FORMED / EARTH_CAST) below the natural ground: the foundation sections (ST p.9 / "
                         "p.13 / p.14) print no working space or excavation method, so whether the face is cast "
                         "against a form or against the trench side is not drawn; the same missing item holds the "
                         "B1 excavation working space (UP-EXC-001, OQ-13). EARTH_CAST reads 0, so no proven low end "
                         "> 0; FORMED figure beside: " + (mrow["bounds"] if mrow else ""),
                "faces": faces, "sources": [T474, T332, "research/agents_t264/T-264_FORMWORK_R4.md s.4"]})
        if p[2] == "FACES":
            fs = faces_by_key.get((cl, p[3], p[4], p[5]), [])
            if not fs:
                raise R.RuleError(f"{lid}: no face for {el}")
            recs = []
            for x in fs:
                k, c = face_cause(x, data)
                if p[4].startswith("OQ10"):
                    k, c = "C_OQ10", c + "; below natural ground: OQ-10 formed vs earth-cast not printed"
                recs.append(face_record(x, k, c))
            if cc != "RELEASED":
                why = concrete_cause(cl, data)
                if p[3] == "CALCULATED":
                    why += "; the faces are CALCULATED but DEPENDENT_HELD on that line (V3.0.33, T-397)"
                return dict(base, **{"class": "B_HELD", "concrete_line": cl, "concrete_class": cc, "cause": why,
                                     "faces": recs, "sources": [T474, T332, INDEX]})
            proven = [r for r in recs if r["cause_kind"] == "SHAFT_D_SETTLED"]
            open_ = [r for r in recs if r["cause_kind"] != "SHAFT_D_SETTLED"]
            checks = [column_check(x, data) for x in fs if face_cause(x, data)[0] == "SHAFT_D_SETTLED"]
            stair = [c["column"] for c in checks if "stair" in c["held_member"].lower()] + \
                [r["face_id"] for r in open_ if "stair" in r["cause"].lower()]
            if proven and stair:
                # a stair flight / landing beside the column may bear on the shaft below the controlling soffit: the
                # method's check 'no framing face below the controlling soffit' covers beams only -> not proven
                for r in proven:
                    r["cause_kind"], r["cause"] = "B_ADJ", r["cause"] + "; NOT freed: a stair element frames at " \
                        "this column (" + ", ".join(stair) + "), its contact with the shaft below the controlling " \
                        "soffit is not settled (T-345 flights)"
                return dict(base, **{"class": "B_HELD", "concrete_line": cl, "concrete_class": cc,
                                     "cause": "concrete RELEASED; shaft depth settled but a stair element frames at "
                                              "the column: shaft contact not proven; faces held: " +
                                              "; ".join(sorted({r["cause"] for r in open_})),
                                     "faces": recs, "checks": checks, "sources": [T474, T332, R4, T119]})
            if proven:
                rel = sum((D(r["lo"]) for r in proven), Decimal(0))
                comp = None
                if open_:
                    lo = sum((D(r["lo"]) for r in open_), Decimal(0)) if all(r["lo"] for r in open_) else None
                    hi = sum((D(r["hi"]) for r in open_), Decimal(0)) if all(r["hi"] for r in open_) else None
                    comp = {"class": "HELD", "measured_net": None, "held_low": S(lo), "held_high": S(hi),
                            "faces": [r["face_id"] for r in open_],
                            "cause": "; ".join(sorted({r["cause"] for r in open_}))}
                return dict(base, **{
                    "class": "A_FIX", "concrete_line": cl, "concrete_class": cc,
                    "cause": "column RELEASED; shaft hold was the held framing member only, its depth does not "
                             "change D_ctrl (T-119 r2): shaft perimeter x (interval - D_ctrl) proven; joint faces "
                             "stay HELD (companion)",
                    "faces": recs, "checks": checks, "sources": [T474, T332, R4, T119],
                    "fix": {"kind": "RELEASE_LOW_END", "before": dict(R.BLANK),
                            "after": {"class": "RELEASED", "measured_net": S(rel), "held_low": None,
                                      "held_high": None, "status": "CALCULATED"},
                            "open_faces": [r["face_id"] for r in open_], "companion": comp,
                            "basis": " + ".join(f"{c['column']} {c['section']} x ({c['interval']} - {c['D_ctrl']}) "
                                                f"= {c['hand_m2']} (method {c['method_m2']})" for c in checks)}})
            kinds = {r["cause_kind"] for r in recs}
            cls = "B_HELD" if kinds & {"B_ADJ", "B_LINE"} else "C_HELD"
            return dict(base, **{"class": cls, "concrete_line": cl, "concrete_class": cc,
                                 "cause": "concrete RELEASED; faces held: " + "; ".join(sorted({r["cause"] for r in recs})),
                                 "faces": recs, "sources": [T474, T332, R4]})
        raise R.RuleError(f"{lid}: unknown FW element {el}")

    if p[0] == "FW" and p[1] == "FACE":
        fid = el.split(":", 2)[2]
        f = faces_by_id.get(fid)
        b = mrow["basis"] if mrow else ""
        rec = None
        if "SPLIT_UNRESOLVED" in b:
            targets = ast.literal_eval(re.search(r"(\[.*?\])", b).group(1))
            tcls = [data["lines"][t]["class"] for t in targets]
            member = re.search(r"member (\S+)", b).group(1)
            if f is None:
                raise R.RuleError(f"{lid}: split face {fid} not in the face ledger")
            if any(c != "RELEASED" for c in tcls):
                k, c = "B_LINE", f"member {member} concrete lines {targets} HELD: " + \
                    "; ".join(concrete_cause(t, data) for t in targets if data["lines"][t]["class"] != "RELEASED")
                return dict(base, **{"class": "B_HELD", "concrete_line": None, "concrete_class": "HELD",
                                     "member": member, "member_lines": targets, "cause": c,
                                     "faces": [face_record(f, k, c)], "sources": [T474, T332]})
            if f["held_from"]:
                rec = face_record(f, "SPLIT_RELEASED", "measured CALCULATED face (walk, same method as the released "
                                  "lines) held only because the member lies in several candidate lines with no length "
                                  "per line; every one of them is RELEASED")
                return dict(base, **{
                    "class": "A_FIX", "concrete_line": None, "concrete_class": "RELEASED", "member": member,
                    "member_lines": targets,
                    "cause": f"member {member}: all {len(targets)} concrete lines RELEASED; the face was measured "
                             f"whole by the walk (R-FW-P2-5 REST piece) and held for the per-line split only, which "
                             f"does not change the B10-13 total: release on its own member-level line",
                    "faces": [rec], "sources": [T474, T332],
                    "fix": {"kind": "RELEASE", "before": dict(R.BLANK),
                            "after": {"class": "RELEASED", "measured_net": S(D(f["held_from"])), "held_low": None,
                                      "held_high": None, "status": "CALCULATED"},
                            "open_faces": [], "companion": None,
                            "basis": f"face {fid} {f['held_from']} m2 (formwork r5 CALCULATED, T-308 / T-332); binding "
                                     f"stays member-level ({member}); per-line split by T-149 spans is a later "
                                     "attribution, not a quantity"}})
            k, c = face_cause(f, data)
            return dict(base, **{"class": "B_HELD", "concrete_line": None, "concrete_class": "RELEASED",
                                 "member": member, "member_lines": targets, "cause": c,
                                 "faces": [face_record(f, k, c)], "sources": [T474, T332]})
        if "parapet RC" in b:
            pl = sorted(x["line_id"] for x in data["lines"].values() if x["item_code"] == "STR.CONC.PARAPET")
            c = ("parapet RC concrete: the STR.CONC.PARAPET lines " + ", ".join(pl) + " are all HELD (T-319: >= 0.30 m RC "
                 "in every alternative, the rest held on the material and the build-up depth); the T-332 face is "
                 "not yet bound to one of them (T-474 s.6 item 2); figure beside " + (mrow["bounds"] or ""))
            return dict(base, **{"class": "B_HELD", "concrete_line": None, "concrete_class": "HELD",
                                 "member_lines": pl, "cause": c,
                                 "faces": [face_record(f, "B_LINE", c)] if f else [], "sources": [T474, T332]})
        if "lift-pit" in b:
            c = ("lift-pit wall: concrete L-684fcad323adc0c8a267 STR.CONC.LIFT LIFT_PIT:WALLS HELD (pit depth D-43 not "
                 "printed, 'as per lift manufacturer'); inner face per m height beside (T-474 s.6 item 3)")
            return dict(base, **{"class": "B_HELD", "concrete_line": "L-684fcad323adc0c8a267", "concrete_class": "HELD",
                                 "cause": c, "faces": [face_record(f, "B_LINE", c)] if f else [],
                                 "sources": [T474, T332]})
        if "neck" in b.lower() or (f and f["element"] == "NECK"):
            c = ("neck sides: an aggregate row of several necks with no per-member value; every STR.CONC.NECK line is "
                 "HELD on a height range (founding level 'not less than 1.5 m', Q-21 C)")
            return dict(base, **{"class": "B_HELD", "concrete_line": None, "concrete_class": "HELD", "cause": c,
                                 "faces": [face_record(f, "B_LINE", c)] if f else [], "sources": [T474, T332]})
        mapping = [("band piece bound to no register member", "C_MARK",
                    "band piece with no member mark in or near it on the slab plan: section / member not printed, no "
                    "concrete line"),
                   ("boundary-wall pads", "C_COUNT", "boundary-wall pads: count not printed (T-065 C3), no concrete line"),
                   ("drop not printed", "C_DROP", "sunken-panel edges: the drop is not printed (D-41); 50.885 m of edge "
                    "are beam faces owned by the beams round the sunken panels"),
                   ("drum", "C_THICKNESS", "dome drum: drawn (section B-B 1.30 m) but material / thickness not printed "
                    "(G3-b); the candidate has no drum line")]
        for key, k, c in mapping:
            if key in b:
                return dict(base, **{"class": "C_HELD", "concrete_line": None, "concrete_class": "NO_LINE",
                                     "cause": c, "faces": [face_record(f, k, c)] if f else [],
                                     "sources": [T474, T332]})
        raise R.RuleError(f"{lid}: untied line with no rule: {b[:80]}")
    raise R.RuleError(f"{lid}: element {el} not classed")


def strip_entry(data):
    """(D) T-632: the slab-edge strip beyond the edge beam, 0.20 m x 4.325 m = 0.865 m2 per storey, billed by no line."""
    s = data["t632"]["b20_strip"]
    rows = []
    for st in ("GF", "1F"):
        r = s[st]
        plan = D(r["plan_m2"])
        if q(D(r["width_m"]) * D(r["length_m"])) != q(plan):
            raise R.RuleError(f"strip {st}: width x length != plan")
        rows.append({"storey": st, "band": r["band"], "faces": r["faces"], "plan_m2": S(plan),
                     "length_m": r["length_m"], "width_m": r["width_m"], "cut": r["crossed_by_cut"],
                     "status": "HELD",
                     "beside_if_slab_t_0_16": {"concrete_m3": S(q(plan * D("0.16"))),
                                               "soffit_form_m2": S(plan),
                                               "edge_form_m2_straight_face_only": S(q(D(r["length_m"]) * D("0.16")))}})
    return {"id": "D-T638-STRIP", "class": "C_HELD", "storeys": rows,
            "cause": "the strip is a slab-edge outline 0.20 m beyond the edge-beam face (T-632 R-T632-2, Checker "
                     "VERIFIED identity) but no section prints it: section A-A (GF, cut 55A) and B-B (1F, cut 76E) cross "
                     "it and draw only the beam band; no thickness tag sits on the strip. Its thickness (and whether "
                     "it is the slab plate continued or a drip / finish line) is not printed: concrete, soffit and edge "
                     "forms stay HELD, never 0. Figures beside are the reading 'slab T 16 continues' only, not chosen; "
                     "the outer edge beyond the straight face (corner arc, run along the stair) is not measured here",
            "missing": "strip thickness / profile: a section through the strip, or a level / thickness tag on it "
                       "(ST7757 GF and 1F roof-slab plans, the sheets of sections A-A / B-B)",
            "sources": [T632, "research/agents_t632/T-632_UPSTAND_EXTENT.md s.1"]}


def build():
    data = load()
    scope = [r["line_id"] for r in data["t630"]["per_line"]
             if r["family"] == FAMILY and r["class"] == "HELD" and r["measured_net"] is None
             and r["held_low"] is None and r["held_high"] is None]
    idx_scope = sorted(k for k, v in data["lines"].items() if v["item_code"] == ITEM and v["class"] == "HELD"
                       and v["held_low"] is None and v["held_high"] is None)
    if sorted(scope) != idx_scope:
        raise R.RuleError("T-630 scope differs from the V3.0.57 line index")
    fk, fi = {}, {}
    for f in data["faces"]:
        fk.setdefault((f["new_line_id"], f["status"], f["alternative"] or "-", f["method"]), []).append(f)
        fi[f["face_id"]] = f
    entries = [classify(lid, data, fk, fi) for lid in sorted(scope)]
    n = 0
    for e in entries:
        if e.get("fix"):
            n += 1
            e["fix"]["id"] = f"FR-T638-{n}"
    by_face = {}
    for e in entries:
        for f in e["faces"]:
            if f["face_id"] in by_face:
                raise R.RuleError(f"face {f['face_id']} on two lines")
            by_face[f["face_id"]] = e["line_id"]
    return assemble(entries, strip_entry(data))


def _split_key(f):
    fid = f["face_id"]
    part = "soffit" if "SOFFIT" in fid else "side" if "SIDE" in fid else "edge band" if "EDGE" in fid else \
        ("side" if fid.startswith("R4-256") else "edge band")
    return f"{f['element']} {part} (split member)"


def assemble(entries, strip):
    c = R.census_counts(entries)
    kinds = {}
    for e in entries:
        for f in e["faces"]:
            kinds[f["cause_kind"]] = kinds.get(f["cause_kind"], 0) + 1
    by_el = {}
    for e in entries:
        if not e.get("fix"):
            continue
        k = "COLUMN shaft" if e["fix"]["kind"] == "RELEASE_LOW_END" else \
            _split_key(e["faces"][0])
        v = by_el.setdefault(k, {"fix_rows": 0, "released_m2": Decimal(0), "companions": 0})
        v["fix_rows"] += 1
        v["released_m2"] += D(e["fix"]["after"]["measured_net"])
        v["companions"] += 1 if e["fix"].get("companion") else 0
    by_el = {k: {"fix_rows": v["fix_rows"], "released_m2": S(q(v["released_m2"])), "companions": v["companions"]}
             for k, v in sorted(by_el.items())}
    return {"schema": SCHEMA, "rule": RULE, "task": "T-638",
            "candidate": "ARCH_TAKEOFF_V3.0.58 (V3.0.57 line index 25a8b406 + 5 roof WP lines) + WIRING MANIFEST V15 "
                         "overlay (T-630 dry run)",
            "pins": PINS, "scope": "B10-13 STR.FORMWORK m2 lines HELD with no figure and no bound (T-630 per_line)",
            "counts": c, "face_cause_kinds": dict(sorted(kinds.items())), "fix_rows_by_element": by_el,
            "strip_D": strip,
            "not_claimed": "development villa; nothing wired, released or verified; fix rows are CALCULATED proposals "
                           "for the lane I manifest; V3.0.58 NOT RELEASED; V2.9 + route G unchanged; no freelancer "
                           "formwork row exists (FREELANCER_NO_ROW, T-163 / T-474 s.8): no %",
            "lines": entries}


def dumps(o):
    return json.dumps(o, indent=1, ensure_ascii=False, sort_keys=True) + "\n"


def render_md(b):
    c = b["counts"]
    out = [f"# T-638 formwork hold census (R-T638-1): {c['lines']} HELD-blank B10-13 STR.FORMWORK lines", "",
           f"Candidate {b['candidate']}. {b['not_claimed']}.", "",
           f"Classes: {', '.join(f'{k} {v}' for k, v in c['by_class'].items())}. Fix rows {c['fix_rows']} "
           f"(released {c['released_m2']} m2 CALCULATED, {c['companions']} with a HELD companion); "
           f"{c['stay_held_blank']} stay HELD blank with a named cause.", "",
           "Face causes: " + ", ".join(f"{k} {v}" for k, v in b["face_cause_kinds"].items()) + ".", "",
           "| Fix rows by element | Rows | Released m2 | HELD companions |", "|---|---|---|---|"]
    for k, v in b["fix_rows_by_element"].items():
        out.append(f"| {k} | {v['fix_rows']} | {v['released_m2']} | {v['companions']} |")
    s = b["strip_D"]
    out += ["", f"(D) {s['id']} {s['class']}: {s['cause']}", "", f"Missing: {s['missing']}", "",
            "| Storey | Plan m2 | Beside if T 16: m3 / soffit m2 / straight edge m2 |", "|---|---|---|"]
    for r in s["storeys"]:
        bz = r["beside_if_slab_t_0_16"]
        out.append(f"| {r['storey']} | {r['plan_m2']} | {bz['concrete_m3']} / {bz['soffit_form_m2']} / "
                   f"{bz['edge_form_m2_straight_face_only']} |")
    out += ["", "| Line | Element | Class | Fix | Cause |", "|---|---|---|---|---|"]
    for e in b["lines"]:
        fx = e.get("fix")
        fs = "-" if not fx else (f"{fx['id']} RELEASE {fx['after']['measured_net']}" +
                                 (f" + HELD {fx['companion']['held_low']} .. {fx['companion']['held_high']}"
                                  if fx.get("companion") else ""))
        out.append(f"| {e['line_id']} | {e['element_id'][:60]} | {e['class']} | {fs} | {e['cause'][:170]} |")
    return "\n".join(out) + "\n"


def write_outputs():
    b = build()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(dumps(b), encoding="utf-8")
    OUT_MD.write_text(render_md(b), encoding="utf-8")
    return b
