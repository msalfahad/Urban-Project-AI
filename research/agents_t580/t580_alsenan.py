"""T-580 MANIFEST OVERLAY DRY RUN on the training villa (lane I, non-candidate; research only).

Applies the WIRING MANIFESTS V6 / V7 / V8 and the earlier unwired rows they carry forward (V2 / V3 / V5, the T-498
stage) to a COPY of the pinned V3.0.58 line index (LINE_INDEX_V3_0_57, 4,994 lines, + the 5 T-507 lines = 4,999), in
the Gate B merge order the Lead set: T-498 -> T-423 r2 -> T-563 -> T-513 -> V7 / V8 rows, then the F package (no
board row) as a separate step. Nothing is wired; no candidate, released, rule, knowledge or registry file is touched.

Inputs are committed, numbers-only outputs pinned by sha256; the T-498 stage rows (agents/task-T-498 @ e3e2ebb5,
unmerged) are a committed extract (in/T498_STAGE_ROWS.json, source commit / path / sha256 inside), re-made with
`--extract <summary_t498.json>`. Rebuild: `python3 -I research/agents_t580/t580_alsenan.py` (`--check`).
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import overlay as OV                                                  # noqa: E402

OUT_JSON = HERE / "out/OVERLAY_T580.json"
STAGE = HERE / "in/T498_STAGE_ROWS.json"
STAGE_SOURCE = {"branch": "agents/task-T-498", "commit": "e3e2ebb5a4af5f8b5bfeb1bd2b517845531409eb",
                "path": "research/agents_t498/summary_t498.json"}
V = {
    "V2": ROOT / "research/agents_t536/WIRING_MANIFEST_V2.json",
    "V3": ROOT / "research/agents_t538/WIRING_MANIFEST_V3.json",
    "V4": ROOT / "research/agents_t549/WIRING_MANIFEST_V4.json",
    "V5": ROOT / "research/agents_t555/WIRING_MANIFEST_V5.json",
    "V6": ROOT / "research/agents_t558/WIRING_MANIFEST_V6.json",
    "V7": ROOT / "research/agents_t564/WIRING_MANIFEST_V7.json",
    "V8": ROOT / "research/agents_t569/WIRING_MANIFEST_V8.json",
}
INDEX57 = ROOT / "research/agents_t507/out/LINE_INDEX_V3_0_57.json"
M530 = ROOT / "tests/t530_wiring_manifest/manifest_t530.py"
PINS = {
    V["V2"]: "305c2cf0c712824ea3cd6ceaa7aee2781642deb0274d193554c846d49febacf3",
    V["V3"]: "8d524c53e952ba9128c33dbed6c9243f587925278605b8225315943a34eb0ab2",
    V["V4"]: "b0a8c6736122522e44690f9b49d2781eb1508cf8be3514f472cc169d5e5fc387",
    V["V5"]: "fbdfa500039b11e9c43edf901e468bf5693f11e5faa66575291b8c9ae7149636",
    V["V6"]: "b44b919e4ef749e7d283da6d080e1a806f590a9eba9ef474eeb833c23c78cfe9",
    V["V7"]: "72d2714cb46d190890e591a03b2db9531bcd5d9877a86161b25f80a68c2b8ed0",
    V["V8"]: "c71ecdc0eb11cba4e593ce31e3ec2d3bbad89d55fbc86a596f5b5890a474cf6b",
    INDEX57: "fed5141ea31bfdd9c5f3d89c7fb1fa01365ddbf07b797002780a22016a7f5738",
}
CANDIDATE = "ARCH_TAKEOFF_V3.0.58 (V3.0.57 line index 25a8b406, 4,994 lines, + the 5 T-507 roof WP lines = 4,999)"

# T-423 r1 (agents/task-T-423 a12153ab, research/agents_t423/T-423_SPLIT_REMAINDER.md s.1-2): 22 CHANGED_TEXT_ONLY,
# totals moved {}: 5 FIN.CEILING (ids in its private ledger only), the 1F-02 tile + backing face
# lines, 14 FIN.MARBLE.THRESHOLD, the D-1F-03 dry strip (id not printed) = 22; its 2 set-aside ceilings are named
# and unchanged (checked too). Printed figures are checked as 'before'.
T423 = {
    "prefixes": {"L-a34d0920": "1F-02 tile face piece (F1)", "L-3eba04f2": "1F-02 backing face piece (F1)",
                 "L-eb3be58f": "GF open plan ceiling (set aside, named)", "L-fc116bb6": "1F open plan ceiling (set aside)"},
    "codes": {"FIN.MARBLE.THRESHOLD": 14},
    "stated": {"L-eb3be58f": {"class": "RELEASED", "measured_net": 101.137092}},
    "unaddressed": ["5 FIN.CEILING dome-deduction lines (ids only in T-423's private integration ledger)",
                    "the D-1F-03 dry strip FIN.FLOOR.PORCELAIN line (id not printed)"],
    "text_only_total": 22,
}

# declared cross-trade rulings (a conflict on one host is EXPLAINED only by one of these)
RULINGS = [
    {"layer": "MAS.MORTAR", "host_re": r"^(GF|1F|2F)-WALLS:walls t=0\.20$", "sources": ["T-498", "T-498:perimeter"],
     "ruling": "B9-04 perimeter joint mortar is its own producer key beside the panel bed-joint mortar, never inside "
               "it (R-T520-1 / T-526 / T-532; V2 stream_S.perimeter_lines 'own key')",
     "fix_row": "T-498 step 6 (perimeter mortar) carries both lines apart"},
]


def sha256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _load(p, name):
    spec = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def manifests():
    for p, pin in PINS.items():
        if sha256(p) != pin:
            raise OV.OverlayError(f"PIN: {p.name} sha256 {sha256(p)[:8]} is not the pinned {pin[:8]}")
    return {k: _json(p) for k, p in V.items()}


def base_index():
    d = _json(INDEX57)
    if d["candidate_version"] != "ARCH_TAKEOFF_V3.0.57" or len(d["lines"]) != 4994:
        raise OV.OverlayError("STALE_INPUT: LINE_INDEX_V3_0_57 is not the 4,994-line index of record")
    idx = {l["line_id"]: {k: l[k] for k in ("line_id", "item_code", "unit", "element_id") + OV.QFIELDS}
           for l in d["lines"]}
    t507 = _load(M530, "manifest_t530_t580")._v3058_t507_lines()
    for lid, l in t507.items():
        if lid in idx:
            raise OV.OverlayError(f"{lid}: a T-507 line already in the V3.0.57 index")
        idx[lid] = {"line_id": lid, **{k: l[k] for k in ("item_code", "unit", "element_id") + OV.QFIELDS}}
    return idx


# ---- state helpers ------------------------------------------------------------------------------------------------

def held(lo=None, hi=None):
    return {"class": "HELD", "measured_net": None, "held_low": lo, "held_high": hi}


def released(v):
    return {"class": "RELEASED", "measured_net": v, "held_low": None, "held_high": None}


def stage_state(s, value, low, high):
    if s == "BLOCKED_RFI":
        return held()
    if s.startswith("BOUNDED"):
        return held(low, high)
    if s in ("PROVISIONAL", "SOURCE_DERIVED"):
        return released(value)
    raise OV.OverlayError(f"unknown stage state {s}")


def _op(pkg, row, kind, lid, before=None, after=None, code=None, unit=None, elem=None, src=None, beside=None,
        note=None):
    op = {"op_id": f"{pkg}|{row}|{lid}", "package": pkg, "row": row, "kind": kind, "line_id": lid,
          "before": before, "after": after, "source": src or pkg}
    if code:
        op.update(item_code=code, unit=unit, element_id=elem)
    if beside is not None:
        op["beside"] = beside
    if note:
        op["note"] = note
    return op


# ---- T-498 stage extract --------------------------------------------------------------------------------------------

def extract_stage(summary_path):
    d = _json(summary_path)
    rows = [{"line_id": r["line_id"], "item_code": r["item_code"], "unit": r["unit"], "element_id": r["element_id"],
             "source_line_id": r["source_line_id"], "state": r["after"]["state"], "value": r["after"]["value"],
             "low": r["after"]["low"], "high": r["after"]["high"]} for r in d["rows"]]
    return {"schema": "URBAN_T580_T498_STAGE_ROWS", "source": dict(STAGE_SOURCE, sha256=sha256(summary_path)),
            "stage_identity": {k: d["identity"][k] for k in ("added", "base_lines", "replaced")},
            "stage_extends": d["extends"], "stage_method": d["method"],
            "totals_moved_by_code": d["totals_moved_by_code"], "rows": rows}


def stage():
    s = _json(STAGE)
    if len(s["rows"]) != s["stage_identity"]["added"] or s["stage_identity"]["replaced"] != 0:
        raise OV.OverlayError("T-498 stage extract: rows != added, or the stage replaces lines")
    return s


# ---- packages ------------------------------------------------------------------------------------------------------

def pkg_t498(m, st):
    P, ops = "T-498", []
    for r in st["rows"]:                                                       # step 2: the 74 staged material lines
        ops.append(_op(P, "STAGE_74", "ADD", r["line_id"], None,
                       stage_state(r["state"], r["value"], r["low"], r["high"]), r["item_code"], r["unit"],
                       r["element_id"], note=f"host {r['source_line_id']}"))
    v2 = m["V2"]
    for r in v2["stream_S"]["lintel_lines"]:                                    # step 4: lintel lines, V3 basis
        a, b = r["after"], r["before"]
        if a["state"] == "BOUNDED_MIN_BEARING":
            after, beside = held(a["low"], a["high"]), None
        elif a["state"] == "HELD_BY_NAME":
            after, beside = held(), ({"bound_m3": a["bound_m3"]} if a.get("bound_m3") else None)
        else:
            raise OV.OverlayError(f"lintel state {a['state']}")
        ops.append(_op(P, "LINTEL_V3", "SET", r["line_id"], released(b["value"]) if b["class"] == "RELEASED"
                       else held(), after, beside=beside, note=a["state"]))
    befores = {m2["line_id"]: m2["before"] for m2 in v2["line_moves"]}
    legacy = {}
    for x in m["V5"]["v4_to_v5"]:
        if x["what"].startswith("glue host") and "legacy_kg_range" in x["v4"]:
            legacy[x["what"].split("stage ")[1].rstrip(")")] = x["v4"]["legacy_kg_range"]
    for h in m["V5"]["glue_hosts"]["hosts"]:                                   # step 5: host faces (V5 newest)
        lid, a = h["t498_stage_line"], h["v5_expected_after"]["glue_kg"]
        b = befores.get(lid)
        if b is not None:
            before = released(b["kg"]) if b["state"] == "COMPUTED" else held(*b["kg_range"])
        elif lid in legacy:
            before = held(*legacy[lid])
        else:
            before = None
        if a["state"] == "BOUNDED_EXPOSURE":
            after, beside = held(*a["range"]), None
        else:
            after, beside = held(), {"conditional_range_beside_kg": a.get("conditional_range_beside")}
        ops.append(_op(P, "HOST_FACES_V5", "SET", lid, before, after, beside=beside, note=h["cause"]))
    for r in v2["stream_S"]["perimeter_lines"]:                                # step 6: perimeter joint mortar
        a = r["after"]
        ops.append(_op(P, "PERIMETER_MORTAR", "ADD", f"NEW:MAS.MORTAR.BLACK:PERIMETER:{r['host_line_id']}", None,
                       released(a["value"]), r["item_code"], "m3", r["host_element"], src="T-498:perimeter",
                       beside={"cement_bags": a["cement_bags_beside"], "sand_m3": a["sand_m3_beside"]}))
    for r in m["V3"]["lintel_bars"]["added_lines"]:                            # step 8: lintel bars
        a = r["after"]
        ops.append(_op(P, "LINTEL_BARS_V3", "ADD", r["line_id"], None, held(a["held_low"], a["held_high"]),
                       r["item_code"], r["unit"], r["element_id"], note="AT_LEAST"))
    for r in m["V5"]["lintel_ends"]["part1"]:                                  # T-544 ceilings beside, line HELD
        ops.append(_op(P, "LINTEL_END_CEILINGS", "BESIDE", r["line_id"], held(), None,
                       beside={"at_most_m3": r["after"]["at_most_beside_m3"]}))
    return ops


def pkg_t423(idx):
    P, ops = "T-423 r2", []
    lids = [k for k in idx for p in T423["prefixes"] if k.startswith(p)]
    if len(lids) != len(T423["prefixes"]):
        raise OV.OverlayError("T-423 named lines not all found by prefix")
    for code, n in T423["codes"].items():
        got = sorted(k for k, l in idx.items() if l["item_code"] == code)
        if len(got) != n:
            raise OV.OverlayError(f"T-423: {code} {len(got)} lines, its report names {n}")
        lids += got
    for lid in lids:
        st = next((v for p, v in T423["stated"].items() if lid.startswith(p)), None)
        before = dict(OV.state(idx[lid]), **st) if st else OV.state(idx[lid])
        ops.append(_op(P, "TEXT_ONLY_22", "TEXT_ONLY", lid, before, None,
                       note="printed figure checked" if st else "no figure printed: state read at this step"))
    return ops


def pkg_t563(m):
    P, ops = "T-563", []
    for r in m["V6"]["plaster_lines"]["rows"]:
        b, a = r["before"], r["v6_expected_after"]
        before = released(b["value"]) if b["class"] == "RELEASED" else held(*(b["held_m2"] or (None, None)))
        ops.append(_op(P, "PLASTER_HEIGHT_V1", "SET", r["line_id"], before, held(a["held_low"], a["held_high"]),
                       note=r["room"]))
    for p in m["V6"]["paint"]["pairs"]:                                        # paint stays at G1
        pb = p["paint_before"]
        ops.append(_op(P, "PAINT_UNCHANGED", "TEXT_ONLY", p["paint_line"],
                       released(pb["value"]) if pb["class"] == "RELEASED" else held(*pb["held"]), None))
    return ops


def pkg_floor(m):
    P, ops = "FLOOR_FINISH_COMPLETENESS_WIRING", []
    for a in m["V7"]["floor_census"]["adds"]:
        st = (released(a["measured_net"]) if a["class"] == "RELEASED" else held(a["held_low"], a["held_high"]))
        ops.append(_op(P, "F-T553-1", "ADD", a["line_id"], None, st, a["item_code"], a["unit"], a["element_id"],
                       note=("A08 ESTIMATED class " + m["V8"]["dressing_class"]["expected_after"]["finish_class"])
                       if a["item_code"].endswith("FINISH_HELD") else None))
    fx = next(r for r in m["V7"]["fix_rows"]["rows"] if r["closes"] == "F-T553-2")
    lid = fx["id"].split(":", 1)[1]
    ops.append(_op(P, "F-T553-2", "RECODE", lid, dict(released(fx["before"]["m2"]), item_code=fx["before"]["item_code"]),
                   dict(released(fx["expected_after"]["m2"]), item_code=fx["expected_after"]["item_code"])))
    return ops


def pkg_v8(m):
    out = {}
    rp = m["V8"]["return_paint"]
    P = "RETURN_PAINT_FACES"
    out[P] = [_op(P, "R-T569-1", "ADD", f"NEW:FIN.PAINT:{f['face_id']}", None, held(), f["paint_row"]["item_code"],
                  f["paint_row"]["unit"], f["paint_row"]["element_id"],
                  beside={"bound_m2": f["paint_row"]["bound_beside_m2"], "plaster_line": f["plaster_line"]})
              for f in rp["valued"] + rp["held"]]
    pr = m["V8"]["pier_returns"]
    P = "PIER_RETURNS_EXT (with T-314)"
    out[P] = [_op(P, "R-T567-6", "LEDGER", pr["owner_line"], held(), None,
                  beside={"ledger": pr["ledger_entries"]})]
    w = m["V8"]["w17"]
    P = "W17_Q76A"
    out[P] = [_op(P, "Q-76A", "RETIRE", w["before"]["held_line"], held(*w["before"]["held_m2"])),
              _op(P, "Q-76A", "SET", w["before"]["settled_line"], released(w["before"]["settled_m2"]),
                  released(w["expected_after"]["settled_m2"]))]
    P = "REBAR_OMISSION"
    out[P] = []
    for r in m["V8"]["rebar_omission"]["rows"]:
        a = r["expected_after"]
        out[P].append(_op(P, "T-560", "ADD", f"NEW:STR.REBAR:{a['element_id']}", None, held(), a["item_code"],
                          a["unit"], a["element_id"], beside={"concrete_line": r["concrete_line"]}))
    return out


def pkg_f(m):
    P, ops = "F package (no board row)", []
    for r in m["V2"]["stream_F"]["lines"]:
        a, b = r["after"], r["before"]
        ops.append(_op(P, "T-522/T-529", "SET", r["line_id"], held(b["held_low"], b["held_high"]),
                       released(a["value"]), note=a["state"]))
    for r in m["V2"]["line_moves"]:
        if r["item_code"].startswith("FIN.ROOF."):
            a = r["after_v2"]
            st = released(a["value"]) if a["state"] == "MEASURED" else held()
            ops.append(_op(P, "T-517", "ADD", f"NEW:{r['item_code']}:{r['element_id']}", None, st, r["item_code"],
                           r["unit"], r["element_id"], beside={"bound_m2": a.get("bound_m2")} if a.get("bound_m2")
                           else None))
    return ops


def packages(m, idx, st):
    v8 = pkg_v8(m)
    order = [("T-498", pkg_t498(m, st)), ("T-423 r2", pkg_t423(idx)), ("T-563", pkg_t563(m)), ("T-513", []),
             ("FLOOR_FINISH_COMPLETENESS_WIRING", pkg_floor(m))]
    order += [(k, v) for k, v in v8.items()]
    order += [("F package (no board row)", pkg_f(m))]
    return order


# ---- binding checks (material tables read their line) ----------------------------------------------------------

def binding_checks(m, idx_before_t563, idx_after_t563, idx_after_floor):
    out = {"T-563 (T-454 / T-489 plaster)": {"rows": 0, "before_stale": [], "after_mismatch": []},
           "FLOOR (T-455 tile)": {"rows": 0, "before_stale": [], "after_mismatch": []}}
    o = out["T-563 (T-454 / T-489 plaster)"]
    for b in m["V6"]["bindings"]["rows"]:
        o["rows"] += 1
        lb, la = idx_before_t563[b["line_id"]], idx_after_t563[b["line_id"]]
        br, ar = b["before"], b["expected_after"]
        net_b = OV._d(lb["measured_net"]) if lb["class"] == "RELEASED" else None
        if br["class_read"] != lb["class"] or OV._d(br["net_read"]) != net_b:
            o["before_stale"].append({"key": b["key"], "read": [br["class_read"], br["net_read"]],
                                      "index": [lb["class"], lb["measured_net"]]})
        if ar["class_read"] != la["class"] or [OV._d(x) for x in ar["held_read"]] != [OV._d(la["held_low"]),
                                                                                       OV._d(la["held_high"])]:
            o["after_mismatch"].append({"key": b["key"], "expected": [ar["class_read"], ar["held_read"]],
                                        "line_after": [la["class"], la["held_low"], la["held_high"]]})
    o = out["FLOOR (T-455 tile)"]
    for t in m["V7"]["tile_bindings"]["rows"]:
        o["rows"] += 1
        lid = t["row"].split("|", 1)[1]
        if lid.startswith("NEW:"):
            lid = next(k for k, l in idx_after_floor.items() if k.startswith("NEW:")
                       and l["element_id"] == lid[4:])
        elif t["before"]["item_code"] != idx_before_t563[lid]["item_code"]:
            o["before_stale"].append({"row": t["row"], "read": t["before"]["item_code"],
                                      "index": idx_before_t563[lid]["item_code"]})
        if t["expected_after"]["item_code"] != idx_after_floor[lid]["item_code"]:
            o["after_mismatch"].append({"row": t["row"], "expected": t["expected_after"]["item_code"],
                                        "line_after": idx_after_floor[lid]["item_code"]})
    return out


def block_module_check(m, st):
    """R-T533-1 (V4 block_module): every staged material line on a 0.15 m black host stays HELD blank by name."""
    hosts = {h["host_line"] for h in m["V4"]["block_module"]["host_lines"]}
    rows = [r for r in st["rows"] if r["source_line_id"] in hosts]
    bad = [r["line_id"] for r in rows if stage_state(r["state"], r["value"], r["low"], r["high"]) != held()]
    return {"hosts": len(hosts), "stage_lines_on_them": len(rows), "not_held_blank": bad}


def census_after(after):
    """R-T564-1 floor census and R-T569-1 return pairing re-run on the OVERLAID index (all packages together)."""
    m8 = _load(ROOT / "research/agents_t569/manifest_v8.py", "manifest_v8_t580")
    lines = [dict(l, binding=None, unbound_records=[]) for l in after.values()]
    c = m8.M7.FC.census(lines)
    pairs = m8.check_pairs(lines)
    return {"rule": "R-T564-1 + R-T569-1 on the overlaid index",
            "C1": sorted(h["key"] for h in c["C1_missing_floor"]), "C2": len(c["C2_wet_bed_dry_finish"]),
            "C4": len(c["C4_bed_pair"]),
            "C3": {s: [v["residual_m2"], v["state"]] for s, v in sorted(c["C3_wp_floor_cover"].items())},
            "return_pairs_ok": pairs}


def run(m=None, idx=None, st=None):
    m = m or manifests()
    idx = idx if idx is not None else base_index()
    st = st or stage()
    pk = packages(m, idx, st)
    after, rep = OV.apply(idx, pk, RULINGS)
    # replay to the T-563 and floor steps for the binding checks
    names = [n for n, _ in pk]
    i563, ifl = names.index("T-563"), names.index("FLOOR_FINISH_COMPLETENESS_WIRING")
    pre563, _ = OV.apply(idx, pk[:i563], RULINGS)
    post563, _ = OV.apply(idx, pk[:i563 + 1], RULINGS)
    postfl, _ = OV.apply(idx, pk[:ifl + 1], RULINGS)
    return pk, after, rep, binding_checks(m, pre563, post563, postfl)


def build():
    m = manifests()
    idx = base_index()
    st = stage()
    pk, after, rep, bc = run(m, idx, st)
    status = {}
    for r in rep["rows"]:
        status.setdefault(r["package"], {}).setdefault(r["status"], 0)
        status[r["package"]][r["status"]] += 1
    flagged = [r for r in rep["rows"] if r["status"] != "APPLIED"]
    t0, t1 = OV.totals(idx), OV.totals(after)
    return {
        "schema": "URBAN_T580_MANIFEST_OVERLAY", "rule": "R-T580-1", "task": "T-580", "candidate": CANDIDATE,
        "inputs": {str(p.relative_to(ROOT)): sha256(p) for p in list(V.values()) + [INDEX57, STAGE, M530]},
        "stage_source": st["source"], "stage_extends": st["stage_extends"], "stage_method": st["stage_method"],
        "lines": {"before": len(idx), "after": len(after)},
        "order": [{"package": n, "ops": len(o), "status": status.get(n, {})} for n, o in pk],
        "t423_unaddressed": T423["unaddressed"],
        "flagged_rows": flagged,
        "conflicts": rep["conflicts"],
        "unexplained_conflicts": sum(c["status"] == "UNEXPLAINED" for c in rep["conflicts"]),
        "bindings": bc,
        "census_after": census_after(after),
        "block_module_r_t533_1": block_module_check(m, st),
        "steps": rep["steps"],
        "totals_changed_overall": OV.diff_totals(t0, t1),
        "rows": rep["rows"],
        "candidate_files_touched": 0, "released_quantities_changed": 0,
    }


def dumps(o):
    return json.dumps(o, indent=1, sort_keys=True, default=str) + "\n"


def main(argv):
    if len(argv) > 2 and argv[1] == "--extract":
        STAGE.parent.mkdir(parents=True, exist_ok=True)
        STAGE.write_text(dumps(extract_stage(argv[2])), encoding="utf-8")
        return 0
    text = dumps(build())
    if "--check" in argv:
        ok = OUT_JSON.read_text(encoding="utf-8") == text
        print("T-580 overlay: committed output", "is the rebuild" if ok else "DIFFERS from the rebuild")
        return 0 if ok else 1
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
