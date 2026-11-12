"""T-737 EXTERIOR PLASTER READINESS on ARCH_TAKEOFF_V3.0.73 (development villa; method R-T737-1 in t737_rules.py,
every villa). Research only: no candidate, released, hub, registry, rule / knowledge version file is touched; no
quantity is measured, changed or wired.

(a) census of the QUEUED T-314 r2 stage (pinned extract in/T314_STAGE_T737.json) against LINE_INDEX_V3_0_73 by line id;
(a2) its merged sources by git blob id (stage commit vs this tree) and the later merged records that restate one of its
     faces / holes / levels (cited with the literal they must contain, so a changed record breaks --check);
(c) the 43 exterior bead rows of T-728 re-bound onto the stage's face lines (vertical arrises cut at the face levels,
    rings on the line of the face that holds the hole) with their post-stage state by R-T728-1;
(d) the rebase plan is in T-737_EXTERIOR_READINESS.md.

Rebuild:  bash scripts/agent_env.sh run --tree task-T-737 research/agents_t737/t737_alsenan.py --write
Check:    bash scripts/agent_env.sh run --tree task-T-737 research/agents_t737/t737_alsenan.py --check
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (HERE, ROOT / "research" / "agents_t728"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import t737_rules as R  # noqa: E402
import t728_rules as B  # noqa: E402

SCHEMA = "URBAN_T737_EXTERIOR_READINESS_V1"
CANDIDATE = "ARCH_TAKEOFF_V3.0.73"
STAGE = "research/agents_t737/in/T314_STAGE_T737.json"
IDX73 = "research/agents_t722/out/LINE_INDEX_V3_0_73.json"
IDX_HISTORY = {61: "research/agents_t655/out/LINE_INDEX_V3_0_61.json", 62: "research/agents_t661/out/LINE_INDEX_V3_0_62.json",
               63: "research/agents_t665/out/LINE_INDEX_V3_0_63.json", 64: "research/agents_t668/out/LINE_INDEX_V3_0_64.json",
               65: "research/agents_t671/out/LINE_INDEX_V3_0_65.json", 66: "research/agents_t677/out/LINE_INDEX_V3_0_66.json",
               67: "research/agents_t682/out/LINE_INDEX_V3_0_67.json", 68: "research/agents_t672/out/LINE_INDEX_V3_0_68.json",
               69: "research/agents_t687/out/LINE_INDEX_V3_0_69.json", 70: "research/agents_t693/out/LINE_INDEX_V3_0_70.json",
               71: "research/agents_t704/out/LINE_INDEX_V3_0_71.json", 72: "research/agents_t703/out/LINE_INDEX_V3_0_72.json",
               73: IDX73}
BEADS = "research/agents_t728/out/T728_BEAD_ROWS.csv"
CORNERS = "research/agents_t172/VERTICAL_CORNERS_T172.csv"
BINDING = "research/agents_t337/BINDING_T337.csv"
OPENINGS = "research/agents_t337/OPENINGS_T337.csv"
PINS = [STAGE, BEADS, CORNERS, BINDING, OPENINGS] + [IDX_HISTORY[k] for k in sorted(IDX_HISTORY)]
OUT_JSON = HERE / "out" / "T737_READINESS.json"
OUT_CSV = HERE / "out" / "T737_ROWS.csv"
ITEM, UNIT = "FIN.EXT.FINISH", "m2"
HOSTS = ["L-b05f70c92405dbcfbe62", "L-8bb83e16cc7b104ab88b", "L-d52c4f763b19aedf8b8b",
         "L-c0e9a4c62171de1f369b", "L-cc7dc0a51f3319a99482", "L-43527ae4e8ec75c56636", "L-348c4d8d32f3f6d35fe5"]

# later merged records that read one of the stage's held / printed figures (rule 3); each must still contain `lit`
EVIDENCE = [
    {"id": "E1", "row": "hole W02 (GF NW-7, 0 .. 28.485 m2 HELD)", "file": "research/agents_t627/T-627_OPENING_AREA_EVIDENCE.md",
     "lit": "W02 27.219: waits on D-53", "verdict": "AGREES", "note": "still HELD on D-53 (count 1 drawn vs 2 rendered)"},
    {"id": "E2", "row": "hole D-GF-07 sill / head (+1.00 / +3.50, 2.50 m)", "file": "research/agents_t682/T-682_CONCRETE_GATE_B6.md",
     "lit": "D-GF-07 (head 2.50 PRINTED)", "verdict": "AGREES", "note": "lintel round: head 2.50 printed = 3.50 - 1.00"},
    {"id": "E3", "row": "hole D-GF-07 width (0 .. 5.000 m2 HELD)", "file": "research/agents_t713/T-713_MASONRY_REST.md",
     "lit": "opening widths not drawn (L-GF-01, P-GF-01, D-GF-07", "verdict": "AGREES",
     "note": "masonry round still holds the D-GF-07 width"},
    {"id": "E4", "row": "D-GF-07 width: bead / reveal ledgers vs face ledger", "file": "research/agents_t405/T-405_CORNER_BEADS.md",
     "lit": "7.00 (D-GF-07, printed 2.50 x 2.00)", "verdict": "CONFLICT",
     "note": "T-405 / T-697 ring 7.00 m.l and T-313 reveal head 0.200 x 2.000 carry the 2.00 width DRAWING-CONFIRMED; "
             "T-305 / T-337 hold the same width (render single leaf vs plan 2.00 x 2.50, T-175, D-53). Carried as "
             "CONFLICT; decider: Lead ruling on the evidence hierarchy (printed plan tag vs render) or designer D-53"},
    {"id": "E4b", "row": "D-GF-07 width (face ledger)", "file": "research/agents_t305/OPENING_HOLES_T305.csv",
     "lit": "leaf / hole width HELD", "verdict": "CONFLICT", "note": "the other side of E4"},
    {"id": "E5", "row": "name 'D-GF-07' in the WP round", "file": "research/agents_t710/out/T710_WP_ROUND3.json",
     "lit": "DOOR:D-GF-07-PANTRY", "verdict": "NOT_THE_SAME_ELEMENT",
     "note": "the WP doorway 'D-GF-07' is the GF-07 pantry door (gap 1.000), not the main door on GF SE-2: an id "
             "collision, never a source for the facade hole"},
    {"id": "E6", "row": "parapet tops (4 roofs) vs the merged parapet concrete floors", "file":
     "research/agents_t722/T-722_CONCRETE_GATE_B9.md", "lit": "V3.0.23 floors 1.799103 / 2.949453 / 1.6245",
     "verdict": "AGREES", "note": "top run x 0.30 upstand = concrete floor (checked in numbers below)"},
    {"id": "E6b", "row": "GF terrace parapet top", "file": "research/agents_t722/T-722_CONCRETE_GATE_B9.md",
     "lit": "5.592956 x 0.30 = 1.6778868", "verdict": "AGREES", "note": "same run as the stage GF parapet top low"},
    {"id": "E7", "row": "F-T314-2 (t199 first-writer helper)", "file": "tests/t199_formwork_metalwork/test_family_master_1_25_0.py",
     "lit": "(T-655, F-T314-2)", "verdict": "FIXED", "note": "T-655 merged the helper fix: no r3 blocker"},
]
PARAPET_TOPS = {  # stage line key -> merged concrete floor (m3) of the same parapet; floor = top run low x 0.30 m
    "NEW FIN.EXT.PARAPET-TOP ANNEX +4.30": 1.799103, "NEW FIN.EXT.PARAPET-TOP GF +5.50": 1.677886,
    "NEW FIN.EXT.PARAPET-TOP 1F +9.70": 2.949453, "NEW FIN.EXT.PARAPET-TOP 2F +13.90": 1.6245}
BEAD_GROUPS = {  # T-728 row -> T-172 vertical corners it sums (floor, types, which part)
    "EXT#GF-CONVEX": ("GF", ("CONVEX (external arris)",), "confirmed"),
    "EXT#1F-CONVEX": ("1F", ("CONVEX (external arris)",), "confirmed"),
    "EXT#2F-CONVEX": ("2F", ("CONVEX (external arris)",), "confirmed"),
    "EXT#GF-MOUTHS": ("GF", ("MOUTH_END (facade-side arris)", "MOUTH_END (passage-side arris)"), "confirmed"),
    "EXT#1F-CONVEX-PARAPET-ENDS": ("1F", ("CONVEX (external arris)",), "held_extra"),
}
# held rows with no level split: host named by the face element their ledger cause names
NAMED_HOSTS = {
    "EXT#GF-CONVEX-PLINTH": ("NEW FIN.EXT.FINISH PLINTH GF", "T-697 cause '3 pool-court convex corners below the "
                             "F.F.L. ... plinth': the plinth faces of NW-3 .. NW-6 bind to the stage PLINTH line"),
    "EXT#GF-MOUTHS-STOP": ("NEW FIN.EXT.FINISH PARAPET-OUTER GF +5.50", "T-172 'GF house +5.50 -> +6.00 ... "
                           "passage-mouth end UNKNOWN: stop-end HELD 0 .. 1.20 m.l': on the GF parapet outer face"),
}
CSV_COLS = ["kind", "id", "floor", "stage_action", "line", "element_id", "census", "host_now", "stage_after",
            "bead_class", "ledger_m", "ledger_low", "ledger_high", "split", "host_after", "host_after_state",
            "part_m", "bead_state_after", "value", "low", "high", "note"]


def _p(rel):
    return ROOT / rel


def sha(rel):
    return hashlib.sha256(_p(rel).read_bytes()).hexdigest()


def jload(rel):
    return json.loads(_p(rel).read_text(encoding="utf-8"))


def rows(rel):
    with open(_p(rel), encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _f(x):
    return None if x in ("", None) else float(x)


def line_census(stage, idx):
    out = []
    for r in stage["rows"]:
        c = R.classify_stage_line(r, idx, item_code=ITEM, unit=UNIT)
        out.append(dict(key=r["line_key"], line_id=r.get("line_id"), element_id=r["element_id"], floor=r["floor"],
                        element=r["element"], action=r["action"], census=c["census"], why=c["why"],
                        host_now=c["host_now"], before=r["before"], after=r["after"], net=r["net"],
                        evidence_status=r["evidence_status"]))
    return out


def host_history():
    sig, out = None, []
    for v in sorted(IDX_HISTORY):
        L = {x["line_id"]: x for x in jload(IDX_HISTORY[v])["lines"]}
        s = json.dumps([L.get(h) for h in HOSTS], sort_keys=True)
        out.append({"version": f"V3.0.{v}", "lines": len(L), "hosts": "first" if sig is None else
                    ("same" if s == sig else "MOVED")})
        if sig is not None and s != sig:
            raise R.CensusError(f"a facade host moved at V3.0.{v}: restate before wiring")
        sig = s
    a = {x["line_id"]: x for x in jload(IDX_HISTORY[61])["lines"]}
    b = {x["line_id"]: x for x in jload(IDX73)["lines"]}
    ch = sorted(k for k in a if k in b and a[k] != b[k])
    ad = sorted(k for k in b if k not in a)
    fam = Counter(".".join(b[k]["item_code"].split(".")[:2]) for k in ch + ad)
    ext = [k for k in ch + ad if b[k]["item_code"].startswith(("FIN.EXT", "ARCH.FACADE"))]
    return {"versions": out, "v61_to_v73": {"changed": len(ch), "added": len(ad),
                                            "removed": len([k for k in a if k not in b]),
                                            "by_family": dict(sorted(fam.items())), "facade_lines_moved": ext}}


def source_census(stage):
    tgt = {p: (R.git_blob_id(_p(p).read_bytes()) if _p(p).exists() else None) for p in stage["source_blobs"]}
    return R.source_census(stage["source_blobs"], tgt)


def evidence():
    out = []
    for e in EVIDENCE:
        text = _p(e["file"]).read_text(encoding="utf-8")
        if e["lit"] not in text:
            raise R.CensusError(f"{e['id']}: {e['file']} no longer contains {e['lit']!r}: re-read the record")
        out.append(dict(e, sha256=sha(e["file"])[:8]))
    return out


def parapet_tops(stage):
    by = {r["line_key"]: r for r in stage["rows"]}
    out = []
    for k, conc in PARAPET_TOPS.items():
        r = by[k]
        lo = r["after"]["value"] if r["after"]["value"] is not None else r["after"]["low"]
        calc = lo * 0.30
        agree = abs(calc - conc) <= 1e-5      # the concrete floors are floored to 6 dp
        if not agree:
            raise R.CensusError(f"{k}: top {lo} x 0.30 = {calc} vs concrete floor {conc}")
        out.append({"line": k, "top_run_low_m": lo, "x_0_30_m3": R.r6(calc), "concrete_floor_m3": conc,
                    "verdict": "AGREES"})
    return out


def _faces():
    out = []
    for r in rows(BINDING):
        out.append({"floor": r["floor"], "side": r["side"], "portion": r["portion"], "kind": r["kind"],
                    "bottom": _f(r["bottom"]), "top": _f(r["top"]), "line": r["line"], "key": r["key"]})
    return out


def stage_after(stage):
    by = {}
    for r in stage["rows"]:
        st = R.post_stage_host_state(r["after"])
        by[r["line_key"]] = {"state": st, "after": r["after"], "element": r["element"], "floor": r["floor"]}
    return by


def bead_rows(stage):
    faces, after = _faces(), stage_after(stage)
    corners = rows(CORNERS)
    holes = defaultdict(set)
    for o in rows(OPENINGS):
        if o["status"] != "NOT_AN_OPENING":
            holes[o["opening"].split(" ")[0]].add(o["line"])
    beads = [b for b in rows(BEADS) if b["scope"] == "EXTERIOR"]
    if len(beads) != 43:
        raise R.CensusError(f"{len(beads)} exterior bead rows, expected 43 (T-728)")
    out, splits = [], {}
    for b in beads:
        eid = b["edge_id"]
        form, length, low, high = B.ledger_form(_f(b["ledger_m"]), _f(b["ledger_low"]), _f(b["ledger_high"]))
        if b["ledger_status"] == "HELD" and form == B.MEASURED:
            raise R.CensusError(f"{eid}: a HELD ledger row with a length")
        base = dict(kind="BEAD", id=eid, floor=b["floor"], stage_action="", line=b["host_line"], element_id="",
                    census="", host_now=b["host_state"], stage_after="", bead_class=b["class"],
                    ledger_m=length, ledger_low=low, ledger_high=high)
        if eid in BEAD_GROUPS:
            fl, types, part = BEAD_GROUPS[eid]
            segs, detail = [], []
            for c in corners:
                if c["floor"] != fl or c["type"] not in types:
                    continue
                lo, hi = (float(c["bottom"]), float(c["top"])) if part == "confirmed" else \
                    (float(c["top"]), float(c["held_top"]))
                if hi - lo <= R.EPS:
                    continue
                res = R.split_arris({"id": f"{fl} {c['corner']}", "floor": fl, "sides": c["corner"].split("/"),
                                     "bottom": lo, "top": hi}, faces)
                if res["state"] == "AMBIGUOUS":
                    raise R.CensusError(f"{eid} {c['corner']}: {res['why']}")
                detail.append({"corner": c["corner"], "type": c["type"], "span": [lo, hi], "state": res["state"],
                               "segments": [list(s) for s in res["segments"]]})
                segs += [(s[2], s[3]) for s in res["segments"]]
            tot = R.r6(sum(m for _, m in segs))
            want = length if form == B.MEASURED else high
            if abs(tot - want) > 1e-5:
                raise R.CensusError(f"{eid}: corners sum {tot} != ledger {want}")
            by_line = defaultdict(float)
            for line, m in segs:
                by_line[line] += m
            splits[eid] = {"corners": detail, "by_line": {str(k): R.r6(v) for k, v in by_line.items()},
                           "sum": tot, "ledger": want}
            items = sorted(by_line.items(), key=lambda x: str(x[0]))
            if form != B.MEASURED:   # a held own bound is one row on the line holding most of it (parts above the
                hosts = [x for x in items if x[0] is not None]       # faces' low tops are the held heights)
                items = [max(hosts, key=lambda x: x[1])]
                splits[eid]["note"] = ("parts above the stage faces' low tops are the HELD parapet end heights "
                                       "(the stage line is bounded on them), not a missing host")
            for line, m in items:
                m = R.r6(m)
                if line is None:
                    hs = None
                    st = {"state": B.HELD_BLANK, "value": None, "low": None, "high": None,
                          "cause": f"NO_HOST: {m} m of DRAWING-CONFIRMED arris above every face the stage holds "
                                   f"(passage wall end above the annex parapet top +4.80 to +5.50); ledger {m} m "
                                   f"(reference text, not a quantity)"}
                else:
                    hs = after[line]["state"] if line in after else None
                    if hs is None:
                        raise R.CensusError(f"{eid}: host {line} is not a stage line")
                    if form == B.MEASURED:
                        st = B.bead_state(B.MEASURED, m, None, None, hs, host_cause="stage after-state")
                    else:   # a held own bound is carried whole on its host (never re-split by the level cut)
                        st = B.bead_state(form, None, low, high, hs, own_cause="parapet end height HELD (T-172)",
                                          host_cause="stage after-state")
                out.append(dict(base, split="SPLIT" if len(by_line) > 1 else "ONE_HOST", host_after=line or "NO_HOST",
                                host_after_state=hs or "", part_m=m if form == B.MEASURED else None,
                                bead_state_after=st["state"], value=st["value"], low=st["low"], high=st["high"],
                                note=st.get("cause", "")))
        elif eid in NAMED_HOSTS:
            line, why = NAMED_HOSTS[eid]
            hs = after[line]["state"]
            st = B.bead_state(form, length, low, high, hs, own_cause=b["cause"][:80], host_cause="stage after-state")
            out.append(dict(base, split="RE-HOSTED", host_after=line, host_after_state=hs, part_m=None,
                            bead_state_after=st["state"], value=st["value"], low=st["low"], high=st["high"], note=why))
        else:   # a ring: the line of the face that holds the hole
            op = eid.split("#")[0]
            lines = holes.get(op)
            if not lines or len(lines) != 1:
                raise R.CensusError(f"{eid}: hole {op} on {lines!r}")
            line = next(iter(lines))
            if line != b["host_line"]:
                raise R.CensusError(f"{eid}: ring host {b['host_line']} vs hole line {line}")
            hs = after[line]["state"]
            st = B.bead_state(form, length, low, high, hs, own_cause="opening HELD (T-728 own cause)",
                              host_cause="stage after-state")
            note = ""
            if op == "D-GF-07":
                note = "CONFLICT E4: ring 7.00 DC uses the 2.00 width the face ledger holds (D-53); carried, not picked"
            out.append(dict(base, split="ONE_HOST", host_after=line, host_after_state=hs, part_m=length,
                            bead_state_after=st["state"], value=st["value"], low=st["low"], high=st["high"], note=note))
    return out, splits


def summarise_beads(brows):
    s = defaultdict(lambda: {"rows": 0, "value": 0.0, "low": 0.0, "high": 0.0, "blank": 0})
    for r in brows:
        k = (r["host_after"], r["bead_state_after"])
        d = s[k]
        d["rows"] += 1
        if r["bead_state_after"] == B.RELEASED:
            d["value"] = R.r6(d["value"] + r["value"])
        elif r["bead_state_after"] == B.HELD_BOUND:
            d["low"], d["high"] = R.r6(d["low"] + r["low"]), R.r6(d["high"] + r["high"])
        else:
            d["blank"] += 1
    return [dict(host=k[0], state=k[1], **v) for k, v in sorted(s.items())]


def reconcile(brows):
    """arris once: the measured parts sum, per floor, to the T-728 exterior measured ledger (rows x ledger m)"""
    led, parts = defaultdict(float), defaultdict(float)
    seen = set()
    for r in brows:
        if r["ledger_m"] is not None and r["id"] not in seen:
            led[r["floor"]] += r["ledger_m"]
            seen.add(r["id"])
        if r["part_m"] is not None:
            parts[r["floor"]] += r["part_m"]
    out = {fl: {"ledger_m": R.r6(led[fl]), "parts_m": R.r6(parts[fl])} for fl in sorted(led)}
    for fl, v in out.items():
        if abs(v["ledger_m"] - v["parts_m"]) > 1e-5:
            raise R.CensusError(f"{fl}: re-bound parts {v['parts_m']} != ledger {v['ledger_m']} (arris once)")
    out["total"] = {"ledger_m": R.r6(sum(led.values())), "parts_m": R.r6(sum(parts.values()))}
    by_state = defaultdict(float)
    for r in brows:
        if r["part_m"] is not None:
            by_state[r["bead_state_after"] if r["host_after"] != "NO_HOST" else "NO_HOST"] += r["part_m"]
    out["measured_parts_by_state"] = {k: R.r6(v) for k, v in sorted(by_state.items())}
    return out


def build():
    stage = jload(STAGE)
    idx = jload(IDX73)
    if idx.get("candidate_version") != CANDIDATE:
        raise R.CensusError(f"index is {idx.get('candidate_version')}")
    lines = line_census(stage, idx["lines"])
    cnt = Counter(x["census"] for x in lines)
    src = source_census(stage)
    brows, splits = bead_rows(stage)
    out = {
        "schema": SCHEMA, "rule": f"{R.RULE} {R.VERSION}", "candidate": CANDIDATE,
        "pins": {p: sha(p) for p in PINS},
        "stage": stage["stage"], "stage_identity": stage["identity"],
        "line_census": lines, "line_census_counts": dict(sorted(cnt.items())),
        "stale_lines": [x["key"] for x in lines if x["census"] in (R.STALE, R.GONE, R.COLLISION)],
        "host_history": host_history(), "sources": src,
        "sources_changed": [p for p, v in src.items() if v != R.SAME],
        "evidence": evidence(), "parapet_tops": parapet_tops(stage),
        "beads": {"rows": brows, "splits": splits, "by_host_state": summarise_beads(brows),
                  "rows_in": 43, "rows_out": len(brows), "reconciliation": reconcile(brows)},
        "missing_items": stage["missing_items"],
    }
    return out


def _after_text(a):
    if a["value"] is not None:
        return f"{a['state']} {a['value']}"
    if a["low"] is not None:
        return f"{a['state']} {a['low']} .. {a['high']}"
    return f"{a['state']} blank"


def to_csv(d):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=CSV_COLS, lineterminator="\n")
    w.writeheader()
    for x in d["line_census"]:
        a = x["after"]
        w.writerow({"kind": "STAGE_LINE", "id": x["key"], "floor": x["floor"], "stage_action": x["action"],
                    "line": x["line_id"] or "", "element_id": x["element_id"], "census": x["census"],
                    "host_now": (x["host_now"] or {}).get("class", "") if x["host_now"] else "free",
                    "stage_after": _after_text(a),
                    "note": x["why"]})
    for r in d["beads"]["rows"]:
        w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in CSV_COLS})
    return buf.getvalue()


def main(argv):
    d = build()
    js = json.dumps(d, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    cs = to_csv(d)
    if "--write" in argv:
        OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
        OUT_JSON.write_text(js, encoding="utf-8")
        OUT_CSV.write_text(cs, encoding="utf-8")
        print("T737 outputs written")
    elif "--check" in argv:
        ok = OUT_JSON.read_text(encoding="utf-8") == js and OUT_CSV.read_text(encoding="utf-8") == cs
        print("T737 outputs AGREE" if ok else "T737 outputs DIFFER")
        return 0 if ok else 1
    print(json.dumps({"census": d["line_census_counts"], "stale": d["stale_lines"],
                      "sources_changed": d["sources_changed"], "beads": d["beads"]["by_host_state"]}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
