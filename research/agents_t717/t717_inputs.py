"""T-717: the URBAN_V3074_INPUTS_V1 project inputs of ARCH_TAKEOFF_V3.0.74 (engine.source.arch_v3074), built ONLY from
Checker-merged files, each pinned by sha256 (an edited file stops the build) and each ledger REBUILT by its own merged
builder and asserted equal to the committed file:

  research/agents_t701/out/T701_RECONCILE.json   T-701 (MERGED 65083ee7, Verifier 2026-11-11T10:03Z Gate A PASS, own
      re-measure GF-04 12.500 lm / 34.33 .. 43.78 AGREE, GF-01 47.960668 .. 66.26068 arithmetic AGREE): R-T701-2 annex
      plaster ENGINE_WRONG (bound too narrow) -> the datum bound;
  research/agents_t702/out/T702_TILES_ROUND3.json T-702 (MERGED b90d85af, Verifier 2026-11-11T12:01Z Gate A PASS): part
      (c) beam crossings / sunken panels over the GF-07 / GF-14 wet bands;
  research/agents_t709/out/T709_RESIDUALS.json   T-709 (MERGED fe461c6e, Verifier 2026-11-11T13:59Z Gate A PASS, own
      re-measure of the ST-02 well run 11.170 lm and the GF solid run 4.000 (F-V709-1), band by hand AGREE, return
      bridge AGREE, W12 4.300824 arithmetic AGREE): R-T709-1 band, R-T709-4 return paint, F-T709-1;
  research/agents_t719/out/T719_VOIDS.json       T-719 (MERGED 302e002d, Verifier 2026-11-11T23:53Z Gate A PASS): V-01
      names the ST-02 light well and its two double-height walls (west 4.00 / south 7.02 = the R-T709-1 runs): the
      first band prerequisite of T-723;
  research/agents_t723/out/T723_READINESS.json   T-723 (MERGED 5d00f738, Verifier 2026-11-11T23:51Z Gate A PASS): the
      line-by-line map, hub T-717 (36 rows: 4 CHANGE, 32 ADD);
  research/agents_t722/out/LINE_INDEX_V3_0_73.json T-722 (Gate B PASS, MERGED 931dc8d9): class and range of each line on
      the candidate of record V3.0.73 (the binding; asserted again on the live run).

T-723 action -> V3.0.74: CHANGE -> restate BOUND (T-701 / T-702 bound; GF-01 with F-T709-1, the RESTATE_FIRST flag of
the map); ADD (T-709 (c)) -> RETURN_PAINT; ADD (T-709 (a)) -> DH_BAND. The second band prerequisite (the T-147 region of
GF-08 carries face 336) is checked on the live run by the run script (t717 region check), not here.

    python3 -I research/agents_t717/t717_inputs.py [project_id]      # prints the inputs summary
"""

from __future__ import annotations

import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
for p in (ROOT, HERE):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

R = "research"
F701 = ROOT / R / "agents_t701/out/T701_RECONCILE.json"
F702 = ROOT / R / "agents_t702/out/T702_TILES_ROUND3.json"
F709 = ROOT / R / "agents_t709/out/T709_RESIDUALS.json"
F719 = ROOT / R / "agents_t719/out/T719_VOIDS.json"
F723 = ROOT / R / "agents_t723/out/T723_READINESS.json"
INDEX = ROOT / R / "agents_t722/out/LINE_INDEX_V3_0_73.json"
PINS = {F701: "9ef9a219deebd3b44db920e56a4dc204856cca378a12cbfc046d4c6a53b220a2",
        F702: "ae5b37e75a1635cbcc6e6214c64566e1e831c7d0b62e3b988596f0f0fcbc72bd",
        F709: "fcbd5aa7d9a12018358a757a284fa746302f44b9ddb122f51c9ad7a53bd82151",
        F719: "8ffcd16db639aaec2a19e3cfb5917c1f4d8fba48f3632da207e96f7aa3ba1508",
        F723: "b016f62d0871f085e74f9efe38ef2a146989c18c1b7ca1a971c91fe356adf827",
        INDEX: "af8d567d8a8ae8288ddf3c4c8207d2cbfcf2f322513af84e63a4448898ad7b23"}
BUILDERS = {"T-701": ("agents_t701", "t701_alsenan", F701), "T-702": ("agents_t702", "t702_alsenan", F702),
            "T-709": ("agents_t709", "t709_alsenan", F709), "T-719": ("agents_t719", "t719_alsenan", F719),
            "T-723": ("agents_t723", "t723_alsenan", F723)}
CHECKER = {
    "T-701": ("65083ee7", "Verifier 2026-11-11T10:03Z Gate A PASS (own P7757 re-measure GF-04 12.500 lm, 34.33 .. "
                          "43.78 AGREE; GF-01 47.960668 .. 66.26068 arithmetic AGREE; R-T701-2 ENGINE_WRONG CONFIRMED)"),
    "T-702": ("b90d85af", "Verifier 2026-11-11T12:01Z Gate A PASS (part (c) beam crossings / sunken panels; statuses "
                          "HELD bounded)"),
    "T-709": ("fe461c6e", "Verifier 2026-11-11T13:59Z Gate A PASS (own ST-02 well run 11.170 lm AGREE; GF solid 4.000 "
                          "vs 3.997201 F-V709-1 immaterial; band by hand 0.840 .. 0.8715 AGREE; return bridge AGREE; "
                          "W12 4.300824 arithmetic AGREE; return paint HELD 0 .. 24.150 status correct)"),
    "T-719": ("302e002d", "Verifier 2026-11-11T23:53Z Gate A PASS (void register; V-01 walls AF7 4.00 / AEC 7.02 = the "
                          "R-T709-1 runs)"),
    "T-723": ("5d00f738", "Verifier 2026-11-11T23:51Z Gate A PASS (map rebuilt by --check; hub T-717 36 rows)"),
}
SCHEMA = "URBAN_V3074_INPUTS_V1"
HUB = "T-717"
X = Decimal
STATUS_HELD = {"status": "HELD", "basis": "merged ledger bound; open datum named (WORKFLOW_CONTROLS s.5)"}
ANNEX_OPEN = {"GF-01": "annex roof datum held (Q-54 B: slab top bounded, R-T678-2 / T-686: bounds only, no point); "
                       "A-GF-01 arch reveal height printed nowhere (D-45: 0 .. 1.0 x S)",
              "GF-04": "annex roof datum held (Q-54 B: slab top bounded, R-T678-2 / T-686: bounds only, no point)"}


def _sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _load():
    for p, s in PINS.items():
        if _sha(p) != s:
            raise SystemExit(f"{p.relative_to(ROOT)}: sha256 {_sha(p)[:8]} is not the pinned {s[:8]} (edited file)")
    return {k: json.loads(p.read_text(encoding="utf-8")) for k, p in (("701", F701), ("702", F702), ("709", F709),
                                                                       ("719", F719), ("723", F723),
                                                                       ("index", INDEX))}


def rebuild_ledgers():
    """each merged ledger rebuilt by its own merged builder, equal to the committed file (field by field)"""
    out = {}
    for task, (folder, mod, path) in BUILDERS.items():
        d = str(ROOT / R / folder)
        if d not in sys.path:
            sys.path.insert(0, d)
        m = __import__(mod)
        got = json.loads(json.dumps(m.build(), sort_keys=True, default=str))
        if got != json.loads(json.dumps(json.loads(path.read_text(encoding="utf-8")), sort_keys=True)):
            raise SystemExit(f"{task}: the merged builder does not reproduce {path.name}")
        out[task] = True
    return out


def _sources():
    files = {"T-701": F701, "T-702": F702, "T-709": F709, "T-719": F719, "T-723": F723}
    return {t: {"task": t, "file": str(p.relative_to(ROOT)), "sha256": PINS[p], "merge_commit": CHECKER[t][0],
                "checker_run": CHECKER[t][1]} for t, p in files.items()}


def _f(s):
    return None if s is None else float(X(str(s)))


def _host(ix, lid):
    x = ix.get(lid)
    if x is None:
        raise SystemExit(f"{lid}: not on V3.0.73 (stale map)")
    return x


def _restates(d, ix, rows):
    ents = []
    annex = d["701"]["annex_plaster_coverage"]
    wet = {r["line_id"]: r for r in d["702"]["c_beam_crossings"]["rooms"]}
    w12 = [f for f in d["709"]["d_findings"] if f["id"] == "W12" and f["room"] == "GF-01"]
    for r in rows:
        lid = r["host_line_id"]
        x = _host(ix, lid)
        if x["class"] != "HELD" or x["measured_net"] is not None or x["held_low"] is None:
            raise SystemExit(f"{lid}: not a HELD range on V3.0.73")
        exp = {"class": "HELD", "low": x["held_low"], "high": x["held_high"], "element_id": x["element_id"]}
        a = r["after"]
        if r["piece"] == "T-701":
            room = r["row"].split(":")[1]
            L = annex[room]
            if not L["line"].startswith(lid[:10]) or L["status"] != "NARROW":
                raise SystemExit(f"{lid}: T-701 {room} is not this line or not NARROW")
            if [_f(v) for v in L["line_range"]] != [x["held_low"], x["held_high"]]:
                raise SystemExit(f"{lid}: T-701 started from {L['line_range']}, V3.0.73 is {exp}")
            la = [_f(v) for v in L["datum_bound"]]
            if abs(la[0] - a["low"]) > 1e-9 or abs(la[1] - a["high"]) > 1e-9:
                raise SystemExit(f"{lid}: T-723 after {a} is not the T-701 bound {la}")
            cor = None
            if room == "GF-01":
                if len(w12) != 1 or not any("F-T709-1" in f for f in r["flags"]):
                    raise SystemExit("GF-01: the F-T709-1 W12 finding / RESTATE_FIRST flag is not single")
                f = w12[0]
                dl = X(f["ledger_minus_own"])
                if dl != X(f["ledger_m2"][0]) - X(f["own_m2"]) or X(f["own_m2"]) != X(f["drawn_width"]) * X(
                        f["head_used"]):
                    raise SystemExit("GF-01: the W12 finding does not close")
                cor = {"finding": "F-T709-1", "delta_m2": float(dl),
                       "why": f"W12 deduction {f['ledger_m2'][0]} -> {f['own_m2']} m2 ({f['drawn_width']} x "
                              f"{f['head_used']}); both ends {f['ledger_minus_own']}"}
            t = L["terms"]
            basis = (f"R-T701-2 ENGINE_WRONG (bound too narrow): the V3.0.69 figure ({L['line_range'][0]} .. "
                     f"{L['line_range'][1]}, S 3.79) lies inside the merged R-T678-2 / T-686 datum bound "
                     f"{L['datum_bound'][0]} .. {L['datum_bound'][1]} m2; fixed deductions {t['fixed']} ({t['fixed_note']}), "
                     f"beam ends {t['beam_ends']}")
            ents.append({"line_id": lid, "item_code": "FIN.PLASTER", "action": "BOUND", "expect": exp,
                         "ledger_after": la, "correction": cor,
                         "after": None, "basis": basis, "status": dict(STATUS_HELD),
                         "still_open": ANNEX_OPEN[room], "source_tasks": ["T-701", "T-723"] + (
                             ["T-709"] if cor else []), "map_row": r["row"]})
        elif r["piece"] == "T-702":
            L = wet.get(lid)
            if L is None:
                raise SystemExit(f"{lid}: not a T-702 (c) room")
            if [_f(v) for v in L["before"]["band"]] != [x["held_low"], x["held_high"]]:
                raise SystemExit(f"{lid}: T-702 started from {L['before']['band']}, V3.0.73 is {exp}")
            la = [_f(v) for v in L["after"]["band"]]
            if abs(la[0] - a["low"]) > 1e-9 or abs(la[1] - a["high"]) > 1e-9:
                raise SystemExit(f"{lid}: T-723 after {a} is not the T-702 band {la}")
            terms = "; ".join(f"{k} {v}" for k, v in L["after"]["terms"].items())
            basis = (f"T-702 (c) {L['room']} wet band: {L['count']}; {L['beam']}; terms {terms}")
            ents.append({"line_id": lid, "item_code": "FIN.PLASTER", "action": "BOUND", "expect": exp,
                         "ledger_after": la, "correction": None, "after": None, "basis": basis[:900],
                         "status": dict(STATUS_HELD), "still_open": L["after"]["status"],
                         "source_tasks": ["T-702", "T-723"], "map_row": r["row"]})
        else:
            raise SystemExit(f"{lid}: CHANGE from {r['piece']} is not wired by T-717")
    import engine.source.arch_v3074 as A
    for e in ents:
        e["after"] = dict(zip(("low", "high"), A.corrected(e["ledger_after"], e["correction"])))
    return ents


def _returns(d, ix, rows):
    led = {x["plaster_line"]: x for x in d["709"]["c_return_paint"]["rows"]}
    ents = []
    for r in rows:
        lid = r["host_line_id"]
        L = led.get(lid)
        if L is None:
            raise SystemExit(f"{lid}: not a T-709 (c) return face")
        x = _host(ix, lid)
        pr = L["paint_row"]
        if x["element_id"] != L["face_id"] or pr["element_id"] != r["new_line_key"]:
            raise SystemExit(f"{lid}: face {x['element_id']} / key {r['new_line_key']} is not the ledger's")
        if x["class"] != L["plaster_class"]:
            raise SystemExit(f"{lid}: plaster face {x['class']} on V3.0.73, the ledger read {L['plaster_class']}")
        flag = pr["flag"]
        nf = "NOT_ESTABLISHED" in flag
        if nf != any("NOT_ESTABLISHED" in f for f in r["flags"]):
            raise SystemExit(f"{lid}: NOT_ESTABLISHED flag differs between T-709 and T-723")
        if pr["bound_beside_m2"] is None:
            if L["plaster_m2"] is not None or x["measured_net"] is not None or r["after"]["kind"] != "BLANK":
                raise SystemExit(f"{lid}: a blank return binds a blank plaster face")
            after = {"kind": "BLANK"}
            hv = None
            still = f"the plaster return face is HELD blank ({flag}); paint follows its face"
        else:
            lo, hi = (_f(v) for v in pr["bound_beside_m2"])
            if lo != 0.0 or hi != _f(L["plaster_m2"]) or x["measured_net"] != hi or \
                    abs(r["after"]["high"] - hi) > 1e-9 or r["after"]["low"] != 0.0:
                raise SystemExit(f"{lid}: bound {pr['bound_beside_m2']} vs plaster {L['plaster_m2']} / "
                                 f"{x['measured_net']} / map {r['after']}")
            after = {"kind": "BOUND", "low": 0.0, "high": hi}
            hv = hi
            still = ("frame-covered jamb depth printed nowhere (frame / casing detail, DESIGNER datum)"
                     + ("; NOT_ESTABLISHED: wet rooms both sides, one finish per face (R-T701-3): whether this "
                        "return is painted at all is not established; the 0 .. face bound covers both" if nf else ""))
        ents.append({"host_line_id": lid, "face_id": L["face_id"], "element_id": pr["element_id"],
                     "expect_host": {"item_code": "FIN.PLASTER", "class": x["class"], "value": hv},
                     "after": after, "flag": flag if (nf or after["kind"] == "BLANK") else None,
                     "basis": f"R-T709-4 return paint row keyed by the plaster face id ({L['v8_form']}, T-569 V8)",
                     "status": dict(STATUS_HELD), "still_open": still, "source_tasks": ["T-709", "T-723"],
                     "map_row": r["row"]})
    return ents


def _bands(d, ix, rows):
    a = d["709"]["a_double_height"]
    v01 = [v for v in d["719"]["register"] if str(v.get("id", v.get("void", ""))).startswith("V-01")] \
        if isinstance(d["719"].get("register"), list) else None
    ents = []
    for r in rows:
        lid = r["host_line_id"]
        x = _host(ix, lid)
        plaster = r["row"].endswith(":plaster")
        b = a["plaster_band" if plaster else "paint_band"]
        lo, hi = (_f(v) for v in b["m2"])
        if abs(lo - r["after"]["low"]) > 1e-9 or abs(hi - r["after"]["high"]) > 1e-9:
            raise SystemExit(f"{lid}: T-723 band {r['after']} is not T-709's {b['m2']}")
        code = "FIN.PLASTER" if plaster else "FIN.PAINT"
        if x["item_code"] != code or x["class"] != "HELD" or x["held_low"] is None:
            raise SystemExit(f"{lid}: host is {x['item_code']} {x['class']}")
        run = a["gf_solid_under_lm"]
        ret = "0.15"                         # 3 column returns x 0.050 proud (T-709 (a); Checker 300E x 2 + 3008)
        ded = None if plaster else "0.052900"   # ST-02 corner landing +4.696 over <= 1.15 m (paint low only)
        ents.append({"host_line_id": lid, "expect_host": {"item_code": code, "class": "HELD", "low": x["held_low"],
                                                          "high": x["held_high"], "element_id": x["element_id"]},
                     "item_code": code, "element_id": r["new_line_key"], "run_m": run, "levels_m": list(b["levels"]),
                     "returns_lm": ret, "low_deduction_max_m2": ded, "low": lo, "high": hi,
                     "status": dict(STATUS_HELD, basis="drawing-derived band on held datums: run by handle, levels "
                                                       "T-556 / G1; bounded by the column returns" + (
                                                           "" if plaster else " and the corner landing")),
                     "still_open": (b["status"] + "; beam faces under the 1F well walls HELD by name (depth on the "
                                    "structural GF roof slab plan)")[:600],
                     "source_tasks": ["T-709", "T-719", "T-723"], "map_row": r["row"], "void": "V-01 (T-719)",
                     "_v01": bool(v01) if v01 is not None else None})
    return ents


def build(project_id=None, bands=True):
    d = _load()
    if d["index"]["candidate_version"] != "ARCH_TAKEOFF_V3.0.73":
        raise SystemExit("candidate of record moved (expected V3.0.73)")
    ix = {r["line_id"]: r for r in d["index"]["lines"]}
    rows = [r for r in d["723"]["rows"] if r.get("hub") == HUB]
    if len(rows) != 36 or any(r["live"] != "LIVE" or r["class"] != "MAPPED" for r in rows):
        raise SystemExit(f"T-723 hub {HUB}: {len(rows)} rows (expected 36 live MAPPED)")
    ch = [r for r in rows if r["action"] == "CHANGE"]
    ret = [r for r in rows if r["action"] == "ADD" and r["piece"] == "T-709" and ":band:" not in r["row"]]
    bnd = [r for r in rows if r["action"] == "ADD" and ":band:" in r["row"]]
    if (len(ch), len(ret), len(bnd)) != (4, 30, 2):
        raise SystemExit(f"hub rows {len(ch)} / {len(ret)} / {len(bnd)} (expected 4 / 30 / 2)")
    walls = d["719"]
    if "AF7" not in json.dumps(walls) or "AEC" not in json.dumps(walls):
        raise SystemExit("T-719 does not name the V-01 double-height walls (band prerequisite 1)")
    doc = {"schema": SCHEMA, "project_id": project_id, "sources": list(_sources().values()),
           "restate": _restates(d, ix, ch), "returns": _returns(d, ix, ret),
           "bands": _bands(d, ix, bnd) if bands else []}
    for b in doc["bands"]:
        b.pop("_v01", None)
    return doc


def summary(doc):
    return {"restate": [(e["line_id"], e["expect"]["low"], e["expect"]["high"], e["after"]["low"], e["after"]["high"])
                        for e in doc["restate"]],
            "returns": {"BOUND": sum(e["after"]["kind"] == "BOUND" for e in doc["returns"]),
                        "BLANK": sum(e["after"]["kind"] == "BLANK" for e in doc["returns"]),
                        "flagged_not_established": sum("NOT_ESTABLISHED" in (e["flag"] or "") for e in doc["returns"]),
                        "high_sum": round(sum(e["after"].get("high") or 0 for e in doc["returns"]), 6)},
            "bands": [(b["element_id"], b["low"], b["high"]) for b in doc["bands"]]}


if __name__ == "__main__":
    print(json.dumps(rebuild_ledgers()))
    print(json.dumps(summary(build(sys.argv[1] if len(sys.argv) > 1 else None)), indent=1))
