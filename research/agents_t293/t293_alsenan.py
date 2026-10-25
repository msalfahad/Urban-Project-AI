"""T-293 Alsenan formwork face-to-line ledger, part 1 (foundations, ground beams, columns), from committed inputs only.

    python3 -I research/agents_t293/t293_alsenan.py            # build, check closure, print totals (writes nothing)
    python3 -I research/agents_t293/t293_alsenan.py --write    # also write the committed outputs in this folder

Inputs (all committed, all merged unless stated):
  research/agents_t264/FORMWORK_LINES_R4.csv         formwork r4 (T-264 MERGED 90203feb): 361 rows, the face source
  research/agents_t282/DELTA_T282_GROUND_BEAM_SIDES  ground-beam side / end fixes r3 (T-282 MERGED aa3a7bb4): delta rows
  research/agents_t289/BAND_PAIRING_T289.json        engine band id -> T-242 run (T-289 MERGED 455c93c4)
  research/agents_t289/BASIS_LEDGER_T289.csv         the ground-beam / column basis per candidate line (T-289)
  research/agents_t248/LEDGER_T248.csv               column member register: formwork column id <-> engine column id
  research/agents_t253/LEDGER_T253.csv               boundary ground-beam runs (T-253 MERGED c2d5b3cd)
  research/agents_t293/CANDIDATE_V3016_CONCRETE_LINES.json   own ARCH_TAKEOFF_V3.0.16 run (t293_extract.py)
  research/agents_t293/OBLIQUE_BAND_PAIRING_T293.json        the 3 oblique bands T-289's X / Y pairing skipped

Every r4 row and every non-AGREES T-282 row becomes one face record (or, where one row holds several members whose
shares the row's own basis prints, one record per member, counted once in the closure). Part 1 ties FOOTING, STRAP,
NECK, BOUNDARY, LIFT, POOL, GROUND_BEAM and COLUMN faces; slab-level rows (SLAB, BEAM, SLAB_EDGE, JOINT), stairs, domes
and the tank are listed NAMED_NOT_TIED with their quantity and the reason (part 2: they are per-slab aggregates of the
T-139 face walk and must be split per member before they can be tied).
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
sys.path.insert(0, str(HERE))
import face_line_ledger as F  # noqa: E402

R4_REV = "FORMWORK_R4 (T-264 MERGED 90203feb) FORMWORK_LINES_R4.csv row {i}"
T282_REV = "FORMWORK EDGES r3 (T-282 MERGED aa3a7bb4) DELTA_T282_GROUND_BEAM_SIDES.csv {span} {side}"
T289 = "T-289 MERGED 455c93c4"
PART1 = {"FOOTING", "STRAP", "NECK", "BOUNDARY", "LIFT", "POOL", "GROUND_BEAM", "COLUMN"}
CAND_FILE = HERE / "CANDIDATE_V3016_CONCRETE_LINES.json"
OBLIQUE_FILE = HERE / "OBLIQUE_BAND_PAIRING_T293.json"
RUN_RE = re.compile(r"((?:ARC:)?[0-9A-F]{2,4}\+[0-9A-F]{2,4}(?:\+[0-9A-F]{2,4})?(?:#\d+)?)")
T290 = "T-290 MERGED 891dbd4d (Gate A PASS, 2026-10-25)"
T290_DELTA = {   # T-290 s.5 cross-trade findings 1 - 2: drawn readings replace two r4 stair rows (part-2 rows)
    "MS2-LD landing soffit": (-0.065, "drawn plates 1.495 + 1.440 = 2.935 m2 (T-281) vs r4 3.000 on the retired 0.480 "
                                      "reading: -0.065 = 1.30 x 0.05, the MS2-L last going"),
    "RS-A riser forms": (-0.040, "structural lane 1.200: 5 x 1.20 x 0.1607 = 0.964 m2 vs r4 1.004 on the 1.25 width"),
}
T290_NOTE = {
    "E1 waist soffit": "CONFLICT (T-290 s.5 (3)): formwork NOT_APPLICABLE vs the concrete waist HELD G2-w; HELD, never "
                       "NA by default, until the Checker settles it",
    "RS-LD landing soffit": "rests on the pre-r2 0.2256 m3 reading (T-290 s.5 (2)); T-281 measures the soffit directly",
}


def _f(v):
    return None if v in (None, "") else float(v)


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def r4_rows():
    return list(csv.DictReader((ROOT / "research/agents_t264/FORMWORK_LINES_R4.csv").open(encoding="utf-8")))


def t282_rows():
    return list(csv.DictReader((ROOT / "research/agents_t282/DELTA_T282_GROUND_BEAM_SIDES.csv").open(encoding="utf-8")))


# ---------------------------------------------------------------- classification of one r4 row (no quantity changed)

def contact_alt(x):
    """(contact, alternative) from the row's own words: above N.G. = formed against air (outside OQ-10); EARTH_CAST =
    the OQ-10 earth alternative; a FORMED face below ground = the OQ-10 FORMED alternative; above ground = FORM"""
    it, el = x["item"], x["element"]
    below = el in ("FOOTING", "NECK", "GROUND_BEAM", "STRAP", "BOUNDARY", "LIFT")
    if "EARTH_CAST" in it:
        return "EARTH", "OQ10_EARTH_CAST"
    if "above N.G." in it:
        return "FORM", ""
    if below and ("FORMED" in it or it.startswith("tee:") or "soffit" in it):
        return "OQ10", "OQ10_FORMED" if "soffit" not in it else "OQ10_SOFFIT"
    if below:
        return "OQ10", ""
    return "FORM", ""


def face_kind(x):
    it = x["item"].lower()
    for k, w in (("COVER", "covered by"), ("COVER", "tee:"), ("NOTCH", "notch"), ("END", "end face"),
                 ("SOFFIT", "soffit"), ("JOINT", "joint"), ("RISER", "riser"), ("EDGE_BAND", "band"),
                 ("SHAFT", "shaft"), ("ARC_FACE", " face (")):
        if w in it:
            return k
    return "SIDE"


def member_of(x):
    """the member a row's faces bound (one key per member), or None for an aggregate the row's text names"""
    el, it = x["element"], x["item"]
    if el == "COLUMN":
        m = re.match(r"(COL-\w+-\d+)", it)
        return ("COLUMN:" + m.group(1)) if m else None
    if el == "GROUND_BEAM":
        if it.startswith("tee:"):
            m = re.search(r"ends on (\S+)", it)
            return "GB:" + m.group(1)
        m = RUN_RE.search(it)
        return "GB:" + m.group(1)
    if el == "FOOTING":
        m = re.match(r"(FF|FN|F\d*)\b", it)
        return "FOOTING:" + m.group(1)
    if el == "STRAP":
        return "STRAP:" + it.split()[0]
    if el == "BOUNDARY":
        if it.startswith("boundary G.B run"):
            return "BOUNDARY_GB:" + it.split()[3]
        return {"M1": "BOUNDARY_FDN_M1", "boundary-wall": "BOUNDARY_PADS", "boundary columns": "BOUNDARY_COLUMNS"}.get(
            next((k for k in ("M1", "boundary-wall", "boundary columns") if k in it), ""), None)
    if el in ("LIFT", "POOL", "TANK"):
        return el
    return None


def basis_of(x):
    b = x["basis"]
    if "court run" in b:
        return "HELD_SECTION", "court run: section not established (T-253 s.4 / T-289 HELD)"
    if "0.95" in b or "Outer Normal ground level" in b:
        return "DEPTH_PRINTED", f"D 0.95 by two printed levels (T-253 s.2; basis ledger {T289}: DRAWING-CONFIRMED)"
    if "class only" in b or "title / length basis" in b or "2 L D (T-242" in b:
        return "CLASS_PRINTED", "interior ground-beam class depth printed by span (p.13); D-33 / D-34 where named"
    if "annex exterior CONFLICT" in b:
        return "CONFLICT", "annex depth D-35 CONFLICT (T-253 s.3 / T-289): no value adopted"
    return "", ""


def faces_r4(rows, boundary_runs):
    """every r4 row -> one or more face records (split only where the row's own basis prints each member's share)"""
    src, faces, named, extra = [], [], {}, []
    for i, x in enumerate(rows):
        c, alt = contact_alt(x)
        b, bnote = basis_of(x)
        rec = {"face_id": f"R4-{i:03d}", "revision": R4_REV.format(i=i), "element": x["element"], "floor": x["floor"],
               "item": x["item"], "face_kind": face_kind(x), "contact": c, "alternative": alt, "method": x["method"],
               "m2": _f(x["m2"]), "lo": _f(x["held_lo"]), "hi": _f(x["held_hi"]), "status": x["status"],
               "refs": x["refs"], "basis": b, "basis_note": bnote, "unit": "m2"}
        mem = member_of(x)
        rec["members"] = [mem or f"AGGREGATE:{x['element']}:{x['floor']}"]
        src.append(rec)
        if x["status"] == "S1_NOT_RELEASED":
            named[rec["face_id"]] = (F.SCENARIO, "client-request scenario S1: never a candidate face (ScenarioLeak guard)")
        elif x["status"] == "INFO":
            named[rec["face_id"]] = (F.INFO, "information row (comparison walk or line split), not a quantity")
        elif x["element"] not in PART1:
            why = "part 2: per-slab-level aggregate of the T-139 face walk; split per member before tying"
            if x["element"] == "STAIR":
                why = "part 2: stairs (flight / landing lines from the T-290 basis ledger)"
                for k, (dm2, v) in T290_DELTA.items():
                    if x["item"].startswith(k):
                        rec = dict(rec, basis_note=f"re-based by {T290} delta row T290-{k.split()[0]}: {v}")
                        d = dict(rec, face_id=f"T290-{k.split()[0]}", revision=f"{T290} BASIS_LEDGER s.5",
                                 item=f"delta {k}: {v}", m2=dm2, status="CALCULATED", basis_note=v)
                        extra.append(d)
                for k, v in T290_NOTE.items():
                    if x["item"].startswith(k):
                        rec = dict(rec, basis_note=v)
            elif x["element"] == "DOME":
                why = "part 2: domes (ring / drum / shell lines from the T-290 basis ledger)"
            elif x["element"] == "TANK":
                why = "part 2: water-tank walls (D-44 side of the slab not printed)"
            named[rec["face_id"]] = (F.NAMED, why)
        elif x["status"] == "NOT_APPLICABLE":
            named[rec["face_id"]] = (F.NAMED, "F7 scheduled, not drawn (T-065): no outline, no face, no concrete line")
        elif x["status"] == "OWNED_BY_OTHER_LINE":
            named[rec["face_id"]] = (F.NAMED, "owned by another formwork line (r4)")
        if mem is None and rec["face_id"] not in named:
            named[rec["face_id"]] = (F.NAMED, "aggregate row of several members with no per-member value printed")
        # rows that hold several members whose shares the row's own basis prints
        if x["element"] == "BOUNDARY" and x["item"].startswith("boundary G.B 20 x 40 at N.G., 5 runs"):
            tot = sum(boundary_runs.values())
            assert abs(tot - 44.07) < 1e-9, tot
            for run, L in sorted(boundary_runs.items()):
                m2 = None if rec["m2"] is None else round(2 * L * 0.40, 6) if rec["m2"] else 0.0
                faces.append(dict(rec, face_id=f"{rec['face_id']}.{run}", split_of=rec["face_id"],
                                  members=["BOUNDARY_GB:" + run], m2=m2,
                                  basis_note=f"2 faces x {L} m x 0.40 (T-253 run {run}; the row's 5 runs = 44.07 m)"))
            continue
        if x["element"] == "FOOTING" and "notch" in x["item"]:
            for m in ("FN", "F9"):
                faces.append(dict(rec, face_id=f"{rec['face_id']}.{m}", split_of=rec["face_id"],
                                  members=["FOOTING:" + m], m2=round(rec["m2"] / 2, 6),
                                  basis_note=f"{m}'s faces along the notch (0.40 + 0.35) x 0.30 = 0.225 (row basis)"))
            continue
        faces.append(rec)
    for d in extra:
        src.append(dict(d))
        faces.append(d)
        named[d["face_id"]] = (F.NAMED, "part 2: stairs (T-290 drawn reading, delta on the r4 row)")
    return src, faces, named


def faces_t282(rows):
    """each T-282 r3 row that changes r4 (status DRAWING-CONFIRMED or HELD) -> one delta face record on its run"""
    out = []
    for x in rows:
        if x["status"] == "AGREES":
            continue
        lo, hi = _f(x["delta_m2_lo"]), _f(x["delta_m2_hi"])
        kind = x["r4_kind"]
        rec = {"face_id": f"T282-{x['span_id']}-{x['side']}", "revision": T282_REV.format(span=x["span_id"], side=x["side"]),
               "element": "GROUND_BEAM", "floor": "GF", "item": f"delta {x['span_id']} side {x['side']}: "
               f"r4 {x['r4_L_m']} m -> traced {x['traced_plus_gaps_m']} m ({x['delta_m']} m); {x['cause']}",
               "face_kind": "END" if x["side"] == "END" else "SIDE", "method": "G", "unit": "m2",
               "members": ["GB:" + x["span_id"]], "refs": "T-282 r3", "delta_m": _f(x["delta_m"])}
        if x["status"] == "DRAWING-CONFIRMED" and kind == "CALC" and lo is not None and lo == hi:
            rec.update(contact="FORM", alternative="", m2=lo, lo=None, hi=None, status="CALCULATED",
                       basis="DEPTH_PRINTED", basis_note=f"D 0.95 (T-253; {T289})")
        elif x["status"] == "DRAWING-CONFIRMED" and kind == "FORMED" and lo is not None and lo == hi:
            rec.update(contact="OQ10", alternative="OQ10_FORMED", m2=lo, lo=None, hi=None, status="ALTERNATIVE")
        elif kind == "CONFLICT":
            rec.update(contact="OQ10", alternative="", m2=None, lo=None, hi=None, status="HELD", basis="CONFLICT",
                       basis_note=f"annex depth CONFLICT: {x['delta_m']} m of face, no depth (m only)")
        else:
            rec.update(contact="OQ10", alternative="OQ10_FORMED", m2=None, lo=lo, hi=hi, status="HELD",
                       basis_note=f"depth HELD {x['D_lo']} .. {x['D_hi']}" + ("" if x["status"] != "HELD" else
                                                                          "; length not settled (T-282 HELD)"))
        out.append(rec)
    return out


# ---------------------------------------------------------------- binding: member -> candidate concrete line id(s)

def candidate():
    return json.loads(CAND_FILE.read_text(encoding="utf-8"))


def boundary_runs():
    return {r["item"]: float(r["L_m"]) for r in
            csv.DictReader((ROOT / "research/agents_t253/LEDGER_T253.csv").open(encoding="utf-8"))
            if r["component"].startswith("BOUNDARY-GB at N.G.")}


def t248():
    return list(csv.DictReader((ROOT / "research/agents_t248/LEDGER_T248.csv").open(encoding="utf-8")))


def binding(cand, members_used=()):
    """member key -> [line id]; '_reason' -> member key -> why no line"""
    import t289_bind as TB
    return TB.bind_all(cand, t248(), json.loads((ROOT / "research/agents_t289/BAND_PAIRING_T289.json").read_text()),
                       json.loads(OBLIQUE_FILE.read_text()), members_used)


TYPE_RE = re.compile(r"^(FF|FN|F\d*) x(\d+) ")


def expand_foundations(faces, cand, named=()):
    """footing type rows 'X xN' -> one record per footing of that mark (the row's basis is per footing: 2 (L + W) H of
    one schedule size, so each footing carries 1 / N); handle-named rows -> that handle's footing; the 1B1B outline (F10
    + F) -> its CONFLICT line; the pool row -> its wall faces and its floor edges (no quantity in either)"""
    import t289_bind as TB
    marks = TB.footing_marks(cand["lines"])
    hand = cand["footing_handles"]
    out = []
    for f in faces:
        if f["face_id"] in named:
            out.append(f)
            continue
        if f["element"] == "FOOTING" and f["members"][0].startswith("FOOTING:"):
            mk = f["members"][0].split(":", 1)[1]
            m = TYPE_RE.match(f["item"])
            if m:
                n, ids = int(m.group(2)), marks.get(m.group(1), [])
                if len(ids) != n:
                    raise F.Refused(f"{f['face_id']}: {m.group(1)} x{n} but the candidate has {len(ids)} lines")
                for lid in ids:
                    q = {k: (None if f.get(k) is None else round(f[k] / n, 6)) for k in ("m2", "lo", "hi")}
                    out.append(dict(f, **q, face_id=f"{f['face_id']}.{lid}", split_of=f.get("split_of") or f["face_id"],
                                    members=["FOOTING_LINE:" + lid],
                                    basis_note=f"one of the {n} {m.group(1)} footings (row / {n})"))
                continue
            h = re.search(r"\((1B[0-9A-F]{2}|16[0-9A-F]{2})\)", f["item"]) or re.search(r"FN (180C)", f["item"])
            if mk == "F10" or "1B1B" in f["item"]:
                ids = marks.get("F10", [])
            elif h and h.group(1) in hand and mk in ("F3", "F15", "F11", "F6", "F8", "FN"):
                ids = [hand[h.group(1)]["line_id"]]
                if hand[h.group(1)]["mark"] != mk:
                    raise F.Refused(f"{f['face_id']}: handle {h.group(1)} is a {hand[h.group(1)]['mark']}, row says {mk}")
            elif mk == "FN" and "notch" in f["item"]:
                ids = [hand["180C"]["line_id"]]
            else:
                ids = marks.get(mk, [])
            if len(ids) != 1:
                raise F.Refused(f"{f['face_id']}: footing {mk} resolves to {len(ids)} lines")
            out.append(dict(f, members=["FOOTING_LINE:" + ids[0]]))
            continue
        if f["element"] == "POOL":
            for k, w in (("WALLS", "pool walls, two faces"), ("BASE", "pool floor edges (floor on blinding: no soffit)")):
                out.append(dict(f, face_id=f"{f['face_id']}.{k}", split_of=f["face_id"], members=["POOL:" + k],
                                basis_note=w))
            continue
        out.append(f)
    return out


def build():
    cand = candidate()
    lines = {l["line_id"]: l for l in cand["lines"]}
    src, faces, named = faces_r4(r4_rows(), boundary_runs())
    d = faces_t282(t282_rows())
    src += [dict(f) for f in d]
    faces = expand_foundations(faces + d, cand, named)
    b = binding(cand, {f["members"][0] for f in faces})
    out = F.tie(faces, b, lines, named=named, source=src)
    basis = {r["line_id"]: r for r in csv.DictReader((ROOT / "research/agents_t289/BASIS_LEDGER_T289.csv").open())}
    for r in out["rows"]:
        if r.get("line_id") in basis:
            r["concrete_basis_t289"] = f"{basis[r['line_id']]['status']} ({basis[r['line_id']]['group']})"
    return cand, lines, b, out


def summary(cand, b, out):
    s = collections.Counter(r["tie"] for r in out["rows"])
    per = collections.defaultdict(lambda: collections.Counter())
    for r in out["rows"]:
        per[r["element"]][r["tie"]] += 1
    lines_used = {r["line_id"] for r in out["rows"] if r.get("line_id")}
    return {"schema": F.SCHEMA, "candidate": cand["candidate"], "project": cand["project"],
            "candidate_lines_csv_sha256": cand.get("candidate_lines_csv_sha256"),
            "faces": len(out["rows"]), "by_tie": dict(sorted(s.items())),
            "by_element": {k: dict(sorted(v.items())) for k, v in sorted(per.items())},
            "concrete_lines_with_faces": len(lines_used),
            "members_without_line": sorted(b.get("_reason", {})),
            "closure": out["closure"]}


def write(outdir=HERE):
    cand, lines, b, out = build()
    cols = ["face_id", "revision", "element", "floor", "item", "face_kind", "contact", "alternative", "method", "m2",
            "lo", "hi", "status", "status_in", "members", "tie", "line_id", "line_item_code", "line_element_id",
            "line_state", "concrete_basis_t289", "tie_reason", "basis", "basis_note", "held_reason", "held_from",
            "pending_from", "split_of", "split_lines", "refs"]
    with (outdir / "FORMWORK_FACE_TO_LINE_T293.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(cols)
        for r in out["rows"]:
            w.writerow(["" if r.get(c) is None else ("|".join(r[c]) if isinstance(r.get(c), list) else
                        (f"{r[c]:.6f}" if isinstance(r.get(c), float) else r[c])) for c in cols])
    (outdir / "T199_FORMWORK_BY_LINE_T293.json").write_text(
        json.dumps(F.consumer(out["rows"], lines, cand["candidate"], cand["project"]), indent=1, ensure_ascii=False)
        + "\n", encoding="utf-8")
    (outdir / "summary_t293.json").write_text(json.dumps(summary(cand, b, out), indent=1) + "\n", encoding="utf-8")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    if a.write:
        write()
    cand, lines, b, out = build()
    print(json.dumps(summary(cand, b, out), indent=1)[:4000])
    return 0


if __name__ == "__main__":
    main()
