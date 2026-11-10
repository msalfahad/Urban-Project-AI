"""T-670 (lane A, research piece, every villa): the B9 MATERIAL lines still HELD in the candidate ARCH_TAKEOFF_V3.0.63
(black block units, black mortar, AAC glue, white AAC units) restated line by line to a quantity from the drawings or a
named cause. Nothing is wired: no candidate, no released line, no rule / rulebook version file is changed.

Method (R-T670-1, PROPOSED; it re-uses the MERGED producer functions of ARCH_TAKEOFF_V3.0.59, never re-implements them):
  (1) every MAS.BLOCK line of the candidate is the host; its material lines are found by element id
      'MATERIAL:<host element id>' + item code (one per code, asserted);
  (2) REPRODUCE: the merged producer (engine.source.arch_v3059 material_base / black_rate / aac_bond_rate /
      joint_m3_per_m2) on the CURRENT candidate's host and lintel lines with the rulebook the candidate was built on
      (COMPANY_RULEBOOK 1.0.0) must give every V3.0.63 material figure back (value, range or blank) - else stop;
  (3) RESTATE: the same producer with the rulebook version that carries the owner answers since (1.1.0: UPC-BLACK-BLOCK-001
      confirmed_modules_m 0.15 = 40 x 20, Q-80 owner 2026-11-07); the change per line is the 'after';
  (4) a host that is itself HELD keeps its material lines blank, the host's committed cause named (T-654 trial BOQ r4
      per-line cause, merged); a host bound would be carried in the material's own unit, never summed across units;
  (5) the white AAC unit count has no project face (drawings silent, T-615 s.2) and no company count rule: HELD, the two
      owner supplier faces (Q-60: 62.5 x 25 -> 6.4 / m2, 60 x 20 -> 8.33 / m2) BESIDE only, never on the line;
  (6) installed (theoretical) only: waste / procurement HELD (no owner rule);
  (7) sensitivity F-T498-4: if the T-582 V2 lintel classes were wired (no lintel RELEASED), every REQUIRED face becomes
      a named range 0 .. face (R-T498-1 (1)); the resulting band is printed BESIDE, not applied.

    bash scripts/agent_env.sh run --tree task-T-670 research/agents_t670/t670_masonry_materials.py
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, ROOT / "research" / "agents_t498"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from engine.source import arch_v3059 as P  # noqa: E402  (the merged producer; read-only use)

INDEX = ROOT / "research/agents_t665/out/LINE_INDEX_V3_0_63.json"
INDEX_LINES_SHA = "09ec4c1ac012982d372b2b5251ad07570d5f2a895af0f2a02bcdfc9d3480a9a1"   # inputs.lines of V3.0.63
CAUSES = ROOT / "research/agents_t654/out/TRIAL_BOQ_R4_T654.json"
RB_NEW = ROOT / "rules/rulebook/URBAN_COMPANY_RULEBOOK_1.1.0.json"
T615_WALLS = ROOT / "research/agents_t615/out/WALLS_015_T615.csv"
OUT = ROOT / "research/agents_t670/out"
RIDS = (P.R_BLOCK, P.R_GLUE, P.R_MORTAR)
CODES = (P.U_BLACK, P.MORTAR, P.GLUE, P.U_WHITE)
# owner Q-60 supplier sheet (product data, OWNER_QUESTIONS_ANSWERED Q-60): BESIDE only, never a line figure
AAC_FACES_BESIDE = {"62.5x25": 6.4, "60x20": round(1.0 / (0.60 * 0.20), 6)}
VALUED = ("MEASURED", "PROVISIONAL")


class T670Error(ValueError):
    pass


def _r(x, n=6):
    return None if x is None else round(float(x) + 0.0, n)


# ------------------------------------------------------------------------------------------------ inputs
def rulebook_doc(path):
    """a COMPANY_RULEBOOK_V1 file -> the inputs shape arch_v3059.load_rulebook reads (no value typed here)."""
    book = json.loads(Path(path).read_text(encoding="utf-8"))
    recs = {r["rule_id"]: r for r in book["records"]}
    out = {}
    for rid in RIDS:
        r = recs[rid]
        out[rid] = {"status": r.get("status"),
                    "params": {k: (v.get("value") if isinstance(v, dict) else v) for k, v in r["params"].items()}}
    dig = hashlib.sha256(json.dumps(book, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
    return {"method": P.RULEBOOK_METHOD, "version": book["version"], "digest": dig, "records": out}


def host_view(ln):
    """an index line -> the fields the producer reads (class RELEASED -> a valued state)."""
    return {"line_id": ln["line_id"], "measured_net": ln["measured_net"],
            "evidence_state": "MEASURED" if ln["class"] == "RELEASED" else "BLOCKED_RFI",
            "location": {"element_id": ln["element_id"]}, "class": ln["class"]}


def lintel_view(lines):
    out = {}
    for ln in lines:
        if ln["item_code"] != P.LINTEL_CODE:
            continue
        if not ln["element_id"].startswith("LINTEL:"):
            raise T670Error(f"lintel line {ln['line_id']} has no LINTEL: element id")
        k = ln["element_id"][7:]
        if k in out:
            raise T670Error(f"lintel {k} has two lines")
        out[k] = {"line_id": ln["line_id"], "measured_net": ln["measured_net"],
                  "evidence_state": "MEASURED" if ln["class"] == "RELEASED" else "BLOCKED_RFI"}
    return out


# ------------------------------------------------------------------------------------------------ producer
def produce(src, faces, lintels, rb, joint):
    """one host -> {code: ('VALUE', v) | ('RANGE', [lo, hi]) | ('HELD', why)} by the merged arch_v3059 functions."""
    m = P.EID.match(src["location"]["element_id"])
    colour = m.group("mat") if m else None
    t = float(m.group("t")) if m else None
    if src["evidence_state"] not in VALUED:
        return {c: ("HELD", "host HELD") for c in P.BY_COLOUR[colour]}, None
    if colour is None or t is None:
        raise T670Error(f"{src['line_id']}: a released masonry line with no block type or thickness")
    mb = P.material_base(src, faces, lintels)
    out = {}
    if colour == "BLACK":
        b = P.black_rate(rb, t)
        if b["status"] != P.OK:
            return {P.U_BLACK: ("HELD", b["why"]), P.MORTAR: ("HELD", "joint geometry: module not stated")}, mb
        if mb["base_state"] == "HELD":
            return {P.U_BLACK: ("HELD", mb["why"]), P.MORTAR: ("HELD", mb["why"])}, mb
        rate, jr = b["blocks_per_m2"], P.joint_m3_per_m2(joint, t)
        if mb["base_state"] == "RANGE":
            lo, hi = mb["range_m2"]
            out[P.U_BLACK] = ("RANGE", [_r(lo * rate), _r(hi * rate)])
            out[P.MORTAR] = ("RANGE", [_r(lo * jr), _r(hi * jr)])
        else:
            out[P.U_BLACK] = ("VALUE", _r(mb["material_base_m2"] * rate))
            out[P.MORTAR] = ("VALUE", _r(mb["material_base_m2"] * jr))
        return out, mb
    g = P.aac_bond_rate(rb, t)
    if g["status"] != P.OK or mb["base_state"] == "HELD":
        out[P.GLUE] = ("HELD", g.get("why") or mb["why"])
    elif mb["base_state"] == "RANGE":
        out[P.GLUE] = ("RANGE", [_r(mb["range_m2"][0] * g["kg_per_m2"]), _r(mb["range_m2"][1] * g["kg_per_m2"])])
    else:
        out[P.GLUE] = ("VALUE", _r(mb["material_base_m2"] * g["kg_per_m2"]))
    out[P.U_WHITE] = ("HELD", "AAC face not selected by the project; no company AAC count rule")
    return out, mb


def as_state(ln):
    """an index material line -> the same tuple form."""
    if ln["measured_net"] is not None:
        return ("VALUE", _r(ln["measured_net"]))
    if ln["held_low"] is not None or ln["held_high"] is not None:
        return ("RANGE", [_r(ln["held_low"]), _r(ln["held_high"])])
    return ("HELD", None)


def statement(lines, faces, rb_old, rb_new, joint, causes):
    """-> rows (one per material line), after asserting the reproduction on rb_old."""
    rbo, rbn = P.load_rulebook(rb_old), P.load_rulebook(rb_new)
    lintels = lintel_view(lines)
    hosts = {ln["element_id"]: ln for ln in lines if ln["item_code"] == P.SRC_CODE}
    mats = {}
    for ln in lines:
        if ln["item_code"] in CODES:
            if not ln["element_id"].startswith("MATERIAL:"):
                raise T670Error(f"{ln['line_id']}: material line without a MATERIAL: element id")
            key = (ln["element_id"][9:], ln["item_code"])
            if key in mats:
                raise T670Error(f"two {key[1]} lines on host {key[0]}")
            mats[key] = ln
    for (heid, _), ln in mats.items():
        if heid not in hosts:
            raise T670Error(f"{ln['line_id']}: host {heid} is not a {P.SRC_CODE} line")
    for lid, f in faces.items():
        h = next((x for x in hosts.values() if x["line_id"] == lid), None)
        if h is None:
            raise T670Error(f"lintel faces named on {lid}: not a host line of this candidate")
        if h["class"] != "RELEASED" and (f.get("required") or f.get("held")):
            raise T670Error(f"lintel faces named on the HELD host {lid}: its material is HELD, nothing to deduct")
    rows, mismatch = [], []
    for heid in sorted(hosts):
        h = host_view(hosts[heid])
        old, _ = produce(h, faces, lintels, rbo, joint)
        new, mb = produce(h, faces, lintels, rbn, joint)
        if set(old) != set(new):
            raise T670Error(f"{heid}: the code set changed between rulebook versions")
        for code in sorted(old):
            ln = mats.get((heid, code))
            if ln is None:
                raise T670Error(f"{heid}: the candidate has no {code} line")
            before = as_state(ln)
            if (old[code][0], old[code][1] if old[code][0] != "HELD" else None) != before:
                mismatch.append({"line_id": ln["line_id"], "code": code, "candidate": before, "reproduced": old[code]})
            after = new[code]
            cause = None
            if after[0] == "HELD":
                # a held host names its own committed cause (T-647 / T-648: no cause without a source)
                cause = causes.get(h["line_id"]) if h["class"] != "RELEASED" else after[1]
                if not cause:
                    raise T670Error(f"{ln['line_id']}: HELD with no named cause")
            beside = None
            if code == P.U_WHITE and mb is not None:
                lo_hi = mb["range_m2"] or [mb["material_base_m2"], mb["material_base_m2"]]
                beside = {k: [_r(lo_hi[0] * v, 4), _r(lo_hi[1] * v, 4)] for k, v in AAC_FACES_BESIDE.items()}
            sens = None
            if mb is not None and mb["lintels"] and after[0] != "HELD" and code in (P.U_BLACK, P.MORTAR, P.GLUE):
                k = (after[1] if after[0] == "VALUE" else after[1][1]) / mb["material_base_m2"] \
                    if mb["material_base_m2"] else 0.0
                faces_req = sum(x["face_m2"] for x in mb["lintels"] if x["kind"] == "REQUIRED")
                lo = after[1] if after[0] == "VALUE" else after[1][0]
                sens = {"if_no_lintel_released": [_r(lo), _r(k * (mb["material_base_m2"] + faces_req))],
                        "required_faces_m2": _r(faces_req, 4)}
            rows.append({"material_line_id": ln["line_id"], "code": code, "unit": ln["unit"],
                         "host_line_id": h["line_id"], "host": heid, "host_class": h["class"],
                         "host_net_m2": h["measured_net"],
                         "material_base_m2": None if mb is None else mb["material_base_m2"],
                         "material_base_range_m2": None if mb is None else mb["range_m2"],
                         "lintels": None if mb is None else [{k: x.get(k) for k in ("opening_id", "lintel_line_id",
                                                                                    "kind", "face_m2", "face_max_m2")}
                                                             for x in mb["lintels"]],
                         "before": list(before), "after": [after[0], after[1] if after[0] != "HELD" else None],
                         "changed": list(before) != [after[0], after[1] if after[0] != "HELD" else None],
                         "cause": cause, "beside_aac_units": beside, "sensitivity_F_T498_4": sens})
    if mismatch:
        raise T670Error(f"the merged producer does not reproduce the candidate: {mismatch[:3]}")
    if len(rows) != len(mats):
        raise T670Error(f"{len(mats) - len(rows)} material lines have no host row")
    return rows


def totals(rows, which):
    """per code: valued sum, range sums (never added to the point), blank count."""
    out = {}
    for r in rows:
        st = r[which]
        t = out.setdefault(r["code"], {"unit": r["unit"], "lines": 0, "valued_n": 0, "valued": 0.0,
                                       "range_n": 0, "range": [0.0, 0.0], "blank_n": 0})
        t["lines"] += 1
        if st[0] == "VALUE":
            t["valued_n"] += 1
            t["valued"] = _r(t["valued"] + st[1])
        elif st[0] == "RANGE":
            t["range_n"] += 1
            t["range"] = [_r(t["range"][0] + st[1][0]), _r(t["range"][1] + st[1][1])]
        else:
            t["blank_n"] += 1
    return out


# ------------------------------------------------------------------------------------------------ project
def _pinned_index():
    idx = json.loads(INDEX.read_text(encoding="utf-8"))
    if idx["candidate_version"] != "ARCH_TAKEOFF_V3.0.63" or idx["inputs"]["lines"] != INDEX_LINES_SHA:
        raise T670Error("the line index is not V3.0.63 09ec4c1a")
    return idx


def project_causes():
    d = json.loads(CAUSES.read_text(encoding="utf-8"))
    return {r["line_id"]: r["cause"] for r in d["per_line"] if r.get("item_code") == P.SRC_CODE and r.get("cause")}


def t615_by_line():
    out = {}
    for r in csv.DictReader(T615_WALLS.open(encoding="utf-8", newline="")):
        o = out.setdefault(r["line_id"], {"contract": 0.0, "base": 0.0, "base_low": 0.0, "units": 0.0, "units_low": 0.0,
                                          "mortar": 0.0, "mortar_low": 0.0, "walls": []})
        o["walls"].append(r["wall_id"])
        for k, c in (("contract", "contract_m2"), ("base", "material_base_m2"), ("base_low", "material_base_low_m2"),
                     ("units", "units_nr"), ("units_low", "units_nr_low"), ("mortar", "panel_mortar_m3"),
                     ("mortar_low", "panel_mortar_m3_low")):
            o[k] = _r(o[k] + float(r[c]), 6)
    return out


def lintel_face_check(rows):
    """independent consistency: a REQUIRED face (w + 0.80) x D times the host thickness equals the bound lintel line's
    concrete (B = t: the lintel fills the wall width), so face and concrete describe the same piece (no double count)."""
    out, seen = [], set()
    for r in rows:
        m = P.EID.match(r["host"])
        for x in r["lintels"] or []:
            if x["kind"] != "REQUIRED" or (x["opening_id"], r["host"]) in seen:
                continue
            seen.add((x["opening_id"], r["host"]))
            out.append({"opening_id": x["opening_id"], "host": r["host"], "face_m2": x["face_m2"],
                        "t_m": float(m.group("t")), "face_x_t_m3": _r(x["face_m2"] * float(m.group("t"))),
                        "lintel_line_id": x["lintel_line_id"]})
    return out


def build():
    import t498_inputs as I498
    idx = _pinned_index()
    d = I498.build()
    rows = statement(idx["lines"], d["faces"], d["rulebook"], rulebook_doc(RB_NEW), d["joint"], project_causes())
    cross = []
    t615 = t615_by_line()
    for r in rows:
        if r["changed"] and r["code"] in (P.U_BLACK, P.MORTAR):
            o = t615.get(r["host_line_id"])
            k = "units" if r["code"] == P.U_BLACK else "mortar"
            a = r["after"][1]
            hi, lo = (a, a) if r["after"][0] == "VALUE" else (a[1], a[0])
            cross.append({"material_line_id": r["material_line_id"], "code": r["code"], "host": r["host"],
                          "line_level": [lo, hi], "t615_wall_level": None if o is None else [o[k + "_low"], o[k]],
                          "t615_walls": None if o is None else o["walls"],
                          "residual": None if o is None else [_r(lo - o[k + "_low"]), _r(hi - o[k])]})
    return {"task": "T-670", "rule": "R-T670-1 (PROPOSED)", "lintel_face_check": lintel_face_check(rows), "candidate": idx["candidate_version"],
            "index_lines_sha256": INDEX_LINES_SHA, "rulebook_before": d["rulebook"]["version"],
            "rulebook_after": rulebook_doc(RB_NEW)["version"], "joint": d["joint"],
            "pinned": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                       for p in (INDEX, CAUSES, RB_NEW, T615_WALLS)},
            "totals_before": totals(rows, "before"), "totals_after": totals(rows, "after"),
            "cross_check_t615": cross, "rows": rows}


def to_csv(rows):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["material_line_id", "code", "unit", "host", "host_class", "host_net_m2", "material_base_m2",
                "before", "after", "changed", "cause"])
    for r in rows:
        w.writerow([r["material_line_id"], r["code"], r["unit"], r["host"], r["host_class"], r["host_net_m2"],
                    r["material_base_m2"], json.dumps(r["before"]), json.dumps(r["after"]), r["changed"],
                    (r["cause"] or "")[:240]])
    return buf.getvalue()


if __name__ == "__main__":
    res = build()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "T670_MATERIALS.json").write_text(json.dumps(res, indent=1, sort_keys=True, ensure_ascii=False) + "\n",
                                             encoding="utf-8")
    (OUT / "T670_MATERIALS.csv").write_text(to_csv(res["rows"]), encoding="utf-8")
    print(json.dumps({"before": res["totals_before"], "after": res["totals_after"],
                      "changed": sum(r["changed"] for r in res["rows"]), "cross": res["cross_check_t615"]}, indent=1))
