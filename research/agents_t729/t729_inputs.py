"""T-729 (lane I, hub H5f + C10): the live after-state of every line the FORMWORK GATE B package wires, built from the
Checker-merged ledgers only (sha256-pinned below) as mapped by the merged T-730 readiness (R-T730-1), and checked line by
line against the candidate of record ARCH_TAKEOFF_V3.0.74 (T-717 r2, merge e6481b43; line index of record
research/agents_t717/out/LINE_INDEX_V3_0_74.json). Nothing here opens a drawing or forms a quantity: every figure is a
merged ledger's, restated by line id.

Precedence per line (one live statement per line, R-T730-1 (2); the later merged piece that DECLARES the restatement
wins, never a pick between undeclared figures):
  STR.FORMWORK          T-735 (R-T735-1/-2: 6 conflict columns + L-867e155d) > T-732 (R-T732-1/-2: 7 moved columns)
                        > T-724 (F-V714-1: 4 soffit lows) > T-714 (R-T714-1/-2: 370 lines incl. 54 fix rows)
  STR.FORMWORK.STAIR    T-731 (R-T731-1: L-9c3643da high, L-d9790e45 cap) > T-725 (R-T725-1..3: 20 lines)
  STR.CONC (C10)        T-724 R-T724-3 (L-fb7a6431: 0 .. 3.5256 range -> capped blank, AT_MOST beside),
                        T-731 (L-7863355d AT_LEAST 1.213429 -> 1.213428, rounding R-T696-1),
                        T-724 R-T724-4 (4 strip children: HELD blank, named; added lines)

Actions (one per line):
  RELEASE     T-714 fix row (T-638 R-T638): HELD blank -> RELEASED CALCULATED at the merged figure; a RELEASE_LOW_END
              row keeps its HELD companion (joint faces) beside, never summed.
  BOUND       HELD blank / bounded -> HELD BOUNDED low .. high (0 < low <= high).
  AT_LEAST    HELD blank, lower-end figure beside (never in the line, never summed into a code total).
  CAP         HELD blank, upper-end cap beside (AT_MOST, never a quantity, never 0: a 0 cap is refused, R-T730-1 (4)).
  NAMED       HELD blank, the holding cause named (text only; a figure is never removed by text).
  ADD_NAMED   a NEW HELD blank STR.CONC child line, named (T-724 R-T724-4).

    python3 -I research/agents_t729/t729_inputs.py [--check] [--write]

--write writes out/T729_ENTRIES.json (the entries + census projection); --check rebuilds and compares with the file.
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = HERE / "out" / "T729_ENTRIES.json"
SCHEMA = "URBAN_T729_ENTRIES_V1"
INDEX = "research/agents_t717/out/LINE_INDEX_V3_0_74.json"
FW, FWS = "STR.FORMWORK", "STR.FORMWORK.STAIR"
D = Decimal

# every input, sha256-pinned (first 16 hex); merge commit and Checker Gate A run as recorded on the board
PINS = {
    "research/agents_t714/out/T714_FORMWORK_BOUNDS.json": "17959a8de65c4707",
    "research/agents_t724/out/T724_FINDINGS.json": "9bba4b7414d58ca1",
    "research/agents_t725/out/T725_LEDGER.json": "280a08bd9814fe4e",
    "research/agents_t731/out/T731_LEDGER.json": "da436a9a8f9a51aa",
    "research/agents_t732/out/T732_FORMWORK_MOVED.json": "0a0991489622e886",
    "research/agents_t735/out/T735_DECIDER.json": "086954846170f59c",
    "research/agents_t730/out/T730_ROWS.csv": "737bdb55966b6ebd",
    INDEX: "6733cbc143cdfffd",
}
SOURCES = {
    "T-714": {"file": "research/agents_t714/out/T714_FORMWORK_BOUNDS.json", "merge_commit": "e6ebe28a", "checker_run": "Verifier 2026-11-11T23:49Z Gate A PASS"},
    "T-724": {"file": "research/agents_t724/out/T724_FINDINGS.json", "merge_commit": "cfca9394", "checker_run": "Verifier 2026-11-12 ~02:00Z Gate A PASS (session_01E6cPndwcoCFyW6yDFf3dsv)"},
    "T-725": {"file": "research/agents_t725/out/T725_LEDGER.json", "merge_commit": "b20fe25c", "checker_run": "Verifier 2026-11-12T03:48Z Gate A PASS (session_01E6cPnd1boTCdgLn15ZAk7E)"},
    "T-731": {"file": "research/agents_t731/out/T731_LEDGER.json", "merge_commit": "e9878f39", "checker_run": "Verifier 2026-11-12T05:59Z Gate A PASS (session_01E6cPnep7o5HWYiBduvqwbB)"},
    "T-732": {"file": "research/agents_t732/out/T732_FORMWORK_MOVED.json", "merge_commit": "35c0c09e", "checker_run": "Verifier 2026-11-12T07:56Z Gate A PASS (session_01E6cPneP2vRoV5ySBhUeVJ5)"},
    "T-735": {"file": "research/agents_t735/out/T735_DECIDER.json", "merge_commit": "870f15f5", "checker_run": "Verifier 2026-11-12T09:55Z Gate A PASS"},
    "T-730": {"file": "research/agents_t730/out/T730_ROWS.csv", "merge_commit": "6143f30d", "checker_run": "Verifier 2026-11-12T07:58Z Gate A PASS (session_01E6cPneP2vRoV5ySBhUeVJ5)"},
}


class InputsError(ValueError):
    pass


def sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def load(p):
    want = PINS.get(p)
    got = sha(p)
    if want is not None and not got.startswith(want):
        raise InputsError(f"{p}: sha256 {got[:16]} is not the pinned {want} (stale input)")
    return json.loads((ROOT / p).read_text(encoding="utf-8"))


def _s(x):
    """a ledger figure as a 6 dp string (Decimal, no float round trip)"""
    if x is None:
        return None
    v = D(str(x))
    if not v.is_finite() or v < 0:
        raise InputsError(f"figure {x!r}")
    return str(v.quantize(D("0.000001")))


def _faces(fs):
    out = []
    for f in fs or ():
        out.append({"face_id": f.get("face_id"), "dep": f.get("dep") or f.get("contact"),
                    "low": _s(f.get("low", f.get("lo"))), "high": _s(f.get("high", f.get("hi")))})
    return out


def _cause(row):
    why = row.get("why") or row.get("cause") or ""
    if not why:
        cs = sorted({f.get("cause") for f in row.get("faces") or () if isinstance(f, dict) and f.get("cause")})
        why = "; ".join(cs)
    return why[:400]


# ============================================================================================ formwork (370 lines)
def formwork_live():
    t714 = load(SOURCES["T-714"]["file"])
    t724 = load(SOURCES["T-724"]["file"])
    t732 = load(SOURCES["T-732"]["file"])
    t735 = load(SOURCES["T-735"]["file"])
    live = {}
    fixes = {w["line_id"]: w for w in t714["wiring_form"]}
    for r in t714["lines"]:
        lid, c = r["line_id"], r["class_after"]
        e = {"line_id": lid, "item_code": FW, "element_id": r["element_id"], "source": "T-714",
             "rule": "R-T714-1" if c != "FIX_ROW" else "R-T714-2 / R-T638", "faces": _faces(r["faces"])}
        if c == "FIX_ROW":
            w = fixes.pop(lid)
            if w["state"] != "CURRENT" or w["before"] != "HELD blank" or w["after_class"] != "RELEASED":
                raise InputsError(f"{lid}: fix row {w['fix']} not CURRENT HELD blank -> RELEASED")
            comp = None
            if w["kind"] == "RELEASE_LOW_END":
                comp = {"low": _s(w["companion_low"]), "high": _s(w["companion_high"]),
                        "why": "joint faces of the column stay HELD (T-638 companion): beside, never summed"}
            e.update(action="RELEASE", value=_s(w["after_m2"]), fix=w["fix"], kind=w["kind"], basis=w["basis"],
                     companion=comp)
        elif c == "BOUNDED":
            e.update(action="BOUND", low=_s(r["low"]), high=_s(r["high"]), why=_cause(r))
        elif c == "AT_LEAST":
            e.update(action="AT_LEAST", low=_s(r["low"]), why=_cause(r))
        elif c == "BLANK_NAMED":
            cap = r.get("cap_beside")
            if cap is not None and D(cap) > 0:
                e.update(action="CAP", cap=_s(cap), why=_cause(r))
            else:
                e.update(action="NAMED", why=_cause(r), cap_zero=cap is not None)
        else:
            raise InputsError(f"{lid}: T-714 class {c}")
        live[lid] = e
    if fixes:
        raise InputsError(f"fix rows without a T-714 line: {sorted(fixes)}")
    # T-724 F-V714-1: four soffit lows (SCALED at the true edge width)
    f = [x for x in t724["findings"] if x.get("finding") == "F-V714-1"]
    if len(f) != 1:
        raise InputsError("T-724 F-V714-1 not found once")
    for r in f[0]["restated"]:
        lid = r["line_id"]
        b = live[lid]
        lo0, hi0 = [x.strip() for x in r["before"].split("..")]
        if b["action"] != "BOUND" or b["low"] != _s(lo0) or b["high"] != _s(hi0) or r["class"] != "BOUNDED":
            raise InputsError(f"{lid}: T-724 restates {r['before']}, T-714 carries {b.get('low')} .. {b.get('high')}")
        lo, hi = [x.strip() for x in r["after"].split("..")]
        live[lid] = dict(b, source="T-724", rule="R-T724-1 (F-V714-1)", low=_s(lo), high=_s(hi),
                         supersedes=[{"piece": "T-714", "low": b["low"], "high": b["high"]}],
                         faces=_faces(r.get("faces")) or b["faces"])
    # T-732 R-T732-1: seven columns whose concrete moved
    for r in t732["restated"]:
        lid = r["line_id"]
        b = live[lid]
        a = {"BOUNDED": "BOUND", "AT_LEAST": "AT_LEAST"}[r["class_after"]]
        n = dict(b, source="T-732", rule="R-T732-1", action=a, low=_s(r["low"]),
                 high=_s(r["high"]) if a == "BOUND" else None, faces=_faces(r["faces"]),
                 supersedes=[{"piece": b["source"], "action": b["action"], "low": b.get("low"),
                              "high": b.get("high"), "cap": b.get("cap")},
                             {"piece": "T-707", "low": _s((r.get("t707_beside") or [None, None])[0]),
                              "high": _s((r.get("t707_beside") or [None, None])[1]),
                              "why": "UPPER_BOUND_METHOD_NOT_A_FLOOR (F-T732-1)"}],
                 why=str(r.get("basis") or "")[:400])
        n.pop("cap", None)
        n.pop("cap_zero", None)
        if a == "AT_LEAST":
            n.pop("high", None)
        live[lid] = n
    # T-735 R-T735-1/-2: six conflict columns + the beam side L-867e155d
    for r in t735["columns"]:
        lid = r["line_id"]
        b = live[lid]
        lv = r["live"]
        a = {"BOUNDED": "BOUND", "AT_LEAST": "AT_LEAST"}[lv["cls"]]
        n = dict(b, source="T-735", rule="R-T735-1", action=a, low=_s(lv["low"]),
                 faces=_faces(r["faces"]), supersedes=[dict(s["form"], piece=s["piece"], cause=s["cause"])
                                                       for s in r["superseded"]],
                 why=f"{r['column']} shaft floored at P_min x (least panel top - base - D_max) (R-T732-1 / R-T735-1)")
        n.pop("cap", None)
        n.pop("cap_zero", None)
        if a == "BOUND":
            n["high"] = _s(lv["high"])
        else:
            n.pop("high", None)
        live[lid] = n
    bs = t735["beam_side"]
    lid = bs["line_id"]
    b = live[lid]
    if not (b["action"] == "NAMED" and b.get("cap_zero")):
        raise InputsError(f"{lid}: T-735 restates the T-714 cap-0 line; T-714 carries {b['action']}")
    lv = bs["live"]
    live[lid] = dict({k: v for k, v in b.items() if k != "cap_zero"}, source="T-735", rule="R-T735-2",
                     action="BOUND", low=_s(lv["low"]), high=_s(lv["high"]),
                     faces=[{"face_id": bs["element_id"].split(":", 2)[2], "dep": bs["dep"], "low": _s(lv["low"]),
                             "high": _s(lv["high"])}],
                     supersedes=[dict(s["form"], piece=s["piece"], cause=s["cause"]) for s in bs["superseded"]],
                     why=f"{bs['member']}: side L x (d - t) = exact {bs['exact_m2']} m2, one figure both ends "
                         f"(held until D-02 decides the width: the side does not contain it)")
    return live, {"t714": t714["summary"], "t735_family": t735["family"]}


# ============================================================================================ stair formwork (20)
def stair_live():
    t725 = load(SOURCES["T-725"]["file"])
    t731 = load(SOURCES["T-731"]["file"])
    live = {}
    for r in t725["lines"]:
        lid, c = r["line_id"], r["class_after"]
        e = {"line_id": lid, "item_code": FWS, "element_id": r["element_id"], "source": "T-725", "rule": "R-T725-1..3",
             "why": (r.get("cause") or r.get("note") or "")[:400],
             "faces": [dict(x, face_id=x.get("face_id")) for k in sorted(r.get("faces") or {})
                       for x in _faces(r["faces"][k])]}
        if c == "BOUNDED":
            e.update(action="BOUND", low=_s(r["low"]), high=_s(r["high"]))
        elif c == "AT_LEAST":
            e.update(action="AT_LEAST", low=_s(r["low"]))
        elif c == "BLANK_NAMED":
            if r.get("cap") is not None and D(r["cap"]) > 0:
                e.update(action="CAP", cap=_s(r["cap"]))
            else:
                e.update(action="NAMED")
        else:
            raise InputsError(f"{lid}: T-725 class {c}")
        live[lid] = e
    for r in t731["restated"]:
        lid = r["line_id"]
        if r["item"] != FWS:
            continue
        b = live[lid]
        if "high_new" in r and r.get("high_new") is not None and b["action"] == "BOUND":
            if b["high"] != _s(r["high_old"]) or b["low"] != _s(r["low_old"]):
                raise InputsError(f"{lid}: T-731 restates {r['low_old']} .. {r['high_old']}, T-725 {b}")
            live[lid] = dict(b, source="T-731", rule="R-T731-1", low=_s(r["low_new"]), high=_s(r["high_new"]),
                             supersedes=[{"piece": "T-725", "low": b["low"], "high": b["high"]}],
                             why=str(r["note"])[:400])
        elif "cap_new" in r:
            if b["action"] != "CAP" or b["cap"] != _s(r["cap_old"]):
                raise InputsError(f"{lid}: T-731 restates cap {r['cap_old']}, T-725 {b}")
            live[lid] = dict(b, source="T-731", rule="R-T731-1", cap=_s(r["cap_new"]),
                             supersedes=[{"piece": "T-725", "cap": b["cap"]}], why=str(r["note"])[:400])
        elif b["action"] == "AT_LEAST" and _s(r.get("low_new")) == b["low"]:
            pass                                      # confirmed unchanged (DUPLICATE in T-730), not restated
        else:
            raise InputsError(f"{lid}: T-731 row not understood {r}")
    return live, {"t725_census": t725["census"]}


# ============================================================================================ concrete round 10 (C10)
def concrete_live():
    t724 = load(SOURCES["T-724"]["file"])
    t731 = load(SOURCES["T-731"]["file"])
    out = {}
    f = [x for x in t724["findings"] if x.get("finding") == "F-T723-3"]
    if len(f) != 1:
        raise InputsError("T-724 F-T723-3 not found once")
    f = f[0]
    lo, hi = [x.strip() for x in f["index"].split("..")]
    out[f["line_id"]] = {"line_id": f["line_id"], "item_code": "STR.CONC.GROUND_BEAM", "source": "T-724",
                         "rule": "R-T724-3", "action": "CAP", "cap": _s(f["state"].split("cap ")[1].split(" ")[0]),
                         "was_range": [_s(lo), _s(hi)], "unit": "m3",
                         "why": "a 0 low is no floor (R-T724-3): the 0 .. 3.5256 range record becomes a capped blank; "
                                "gross 44.07 m x 0.20 x 0.40 DRAWING-CONFIRMED, net = 3.5256 - n x 0.024 with the "
                                "boundary-column count n not printed (M4 / Q-28)", "evidence": f["evidence"][:600]}
    for r in t731["restated"]:
        if r["item"] == "STR.CONC.STAIR":
            out[r["line_id"]] = {"line_id": r["line_id"], "item_code": "STR.CONC.STAIR", "source": "T-731",
                                 "rule": "R-T731-1 / R-T696-1", "action": "AT_LEAST", "low": _s(r["low_new"]),
                                 "restates": {"value": _s(r["low_old"]), "why": "T-711 printed half-up; the exact "
                                              "reading A sum 1.213428296 floors to 1.213428 (R-T696-1)"},
                                 "unit": "m3", "why": str(r["note"])[:400]}
    g = [x for x in t724["findings"] if x.get("finding") == "T-721 strip pieces"]
    if len(g) != 1:
        raise InputsError("T-724 strip pieces not found once")
    for p in g[0]["pieces"]:
        if p["state"] != "NAMED_BLANK_CHILD":
            raise InputsError(f"{p['piece']}: {p['state']}")
        out[f"ADD:{p['piece']}"] = {"line_id": None, "child_key": p["piece"], "item_code": None, "source": "T-724",
                                    "rule": p["rule"], "action": "ADD_NAMED", "unit": "m3", "member": p["member"],
                                    "item": p["item"], "per_unit": f"{p['m3_per_m_depth']} m3 per m of depth "
                                    f"(plan {p['area_m2']} m2; information, never a bound)",
                                    "record_slivers_m2": p.get("record_slivers_m2"), "where": p.get("where")}
    return out


# ============================================================================================ check vs V3.0.74
def check_index(entries):
    """every entry binds to its V3.0.74 line as T-730 mapped it (item, element, unit, HELD, range / blank) -> stale list"""
    idx = {x["line_id"]: x for x in load(INDEX)["lines"]}
    stale = []
    for e in entries:
        if e["action"] == "ADD_NAMED":
            continue
        x = idx.get(e["line_id"])
        if x is None:
            stale.append((e["line_id"], "absent"))
            continue
        if e.get("element_id") and x["element_id"] != e["element_id"]:
            stale.append((e["line_id"], f"element {x['element_id']}"))
        if e.get("item_code") and x["item_code"] != e["item_code"]:
            stale.append((e["line_id"], f"item {x['item_code']}"))
        e.setdefault("item_code", x["item_code"])
        e["before"] = {"class": x["class"], "low": x["held_low"], "high": x["held_high"], "value": x["measured_net"],
                       "unit": x["unit"], "element_id": x["element_id"]}
        if x["class"] != "HELD":
            stale.append((e["line_id"], f"class {x['class']}"))
    return stale


def census(entries):
    z = {}
    for e in entries:
        k = (e.get("item_code") or "ADD", e["action"])
        c = z.setdefault(f"{k[0]}|{k[1]}", {"lines": 0, "value": D(0), "low": D(0), "high": D(0), "cap": D(0)})
        c["lines"] += 1
        for f in ("value", "low", "high", "cap"):
            if e.get(f) is not None:
                c[f] += D(e[f])
    return {k: {f: (str(v) if isinstance(v, Decimal) else v) for f, v in c.items()} for k, c in sorted(z.items())}


def check_t730(entries):
    """every T-730 hub T-729 / C10 row is covered by exactly one entry or a declared supersession / duplicate"""
    rows = list(csv.DictReader(open(ROOT / SOURCES["T-730"]["file"], encoding="utf-8")))
    hub = [r for r in rows if r["hub"] in ("T-729", "C10")]
    ids = {e["line_id"] for e in entries if e["line_id"]}
    missing = sorted({r["host_line_id"] for r in hub if r["host_line_id"] and r["host_line_id"] not in ids
                      and not (r["action"] == "KEEP" and r["live"] == "DUPLICATE")})
    keep = sorted(r["row"] for r in hub if r["action"] == "KEEP")
    adds = sum(1 for r in hub if r["action"] == "ADD")
    return {"rows": len(hub), "missing_hosts": missing, "keep_unchanged": keep, "adds": adds,
            "add_entries": sum(1 for e in entries if e["action"] == "ADD_NAMED")}


def build():
    fw, fam = formwork_live()
    st, st_c = stair_live()
    cc = concrete_live()
    entries = sorted(fw.values(), key=lambda e: e["line_id"]) + sorted(st.values(), key=lambda e: e["line_id"]) + \
        [cc[k] for k in sorted(cc)]
    stale = check_index(entries)
    if stale:
        raise InputsError(f"stale on V3.0.74: {stale[:10]} ({len(stale)})")
    t730 = check_t730(entries)
    if t730["missing_hosts"] or t730["adds"] != t730["add_entries"]:
        raise InputsError(f"T-730 coverage: {t730}")
    # the 370-line formwork family after wiring must be the T-735 family exactly (by class and m2)
    cen = census(entries)
    fam_t735 = fam["t735_family"]
    got = {"AT_LEAST": cen.get(f"{FW}|AT_LEAST", {}).get("lines", 0),
           "BOUNDED": cen.get(f"{FW}|BOUND", {}).get("lines", 0),
           "FIX_ROW": cen.get(f"{FW}|RELEASE", {}).get("lines", 0),
           "BLANK_NAMED": cen.get(f"{FW}|CAP", {}).get("lines", 0) + cen.get(f"{FW}|NAMED", {}).get("lines", 0)}
    if got != fam_t735["by_class"]:
        raise InputsError(f"formwork family by class {got} is not the T-735 family {fam_t735['by_class']}")
    for k, f, want in ((f"{FW}|AT_LEAST", "low", "at_least_m2"), (f"{FW}|BOUND", "low", "bounded_low_m2"),
                       (f"{FW}|BOUND", "high", "bounded_high_m2")):
        if D(cen[k][f]) != D(fam_t735[want]):
            raise InputsError(f"{k} {f} {cen[k][f]} is not the T-735 family {want} {fam_t735[want]}")
    if D(cen[f"{FW}|RELEASE"]["value"]) != D(fam["t714"]["fix_rows_m2"]):
        raise InputsError("fix rows m2 is not T-714's")
    return {"schema": SCHEMA, "task": "T-729", "candidate": "ARCH_TAKEOFF_V3.0.74", "index": INDEX,
            "sources": {t: dict(s, sha256=sha(s["file"])) for t, s in SOURCES.items()},
            "index_sha256": sha(INDEX), "entries": entries, "census": cen, "t730_coverage": t730,
            "family_check": {"t735_family": fam_t735, "got_by_class": got}, "stair": st_c,
            "not_claimed": "development villa; nothing released to the default, nothing VERIFIED; no freelancer "
                           "formwork row (NOT_COMPARABLE)"}


# ============================================================================================ V3.0.75 inputs
V3075_SCHEMA = "URBAN_V3075_INPUTS_V1"
CHILD_HOST = {   # the member band line a named child sits on (location / documents only; never summed into it)
    "GF-STRIP-AT-COL": "L-634cefe5e8a7fb458e16",   # BAND0031.1: the line whose record reaches the piece (sliver)
    "GF-NW-CORNER": "L-634cefe5e8a7fb458e16",      # BAND0031 north strip starts at the corner square
    "1F-STRIP-AT-COL": "L-67f3d325019e618328eb",   # BAND0013.1
    "1F-NW-CORNER": "L-67f3d325019e618328eb",      # BAND0013 north strip starts at the corner square
}


def inputs(doc=None):
    """the URBAN_V3075_INPUTS_V1 document for engine.source.arch_v3075 from the entries (one per line)"""
    doc = doc or build()
    srcs = [{"task": t, "file": s["file"], "sha256": s["sha256"], "merge_commit": s["merge_commit"],
             "checker_run": s["checker_run"]} for t, s in sorted(doc["sources"].items())]
    out = []
    for e in doc["entries"]:
        piece = "FW_WIRE" if e.get("item_code") in (FW, FWS) else "CONC_C10"
        x = {"piece": piece, "action": e["action"], "line_id": e["line_id"],
             "source_tasks": sorted({e["source"], "T-730"}), "rule": e["rule"], "status": "HELD",
             "why": e.get("why") or "", "faces": e.get("faces"), "supersedes": e.get("supersedes")}
        if e["action"] == "ADD_NAMED":
            x.update(line_id=None, child_key=e["child_key"], host_line_id=CHILD_HOST[e["child_key"]],
                     item=e["item"], member=e["member"], per_unit=e["per_unit"],
                     why=f"{e['item']}: whether the piece is cast with the strip and to what depth is not printed",
                     record_slivers_m2=e.get("record_slivers_m2"))
            out.append(x)
            continue
        b = e["before"]
        x["expect"] = {"item_code": e["item_code"], "element_id": b["element_id"], "unit": b["unit"],
                       "class": b["class"], "low": b["low"], "high": b["high"]}
        a = e["action"]
        if a == "RELEASE":
            x.update(fix=e["fix"], kind=e["kind"], value=e["value"], basis=e["basis"], companion=e.get("companion"),
                     why=e["basis"])
        elif a == "BOUND":
            x.update(low=e["low"], high=e["high"])
        elif a == "AT_LEAST":
            x.update(low=e["low"])
            if e.get("restates"):
                x["restates"] = e["restates"]
                x["expect"]["beside"] = {"kind": "AT_LEAST_M3", "value": float(e["restates"]["value"])}
        elif a == "CAP":
            x.update(cap=e["cap"])
        if not x["why"]:
            x["why"] = "cause as the merged ledger names it"
        out.append(x)
    return {"schema": V3075_SCHEMA, "project_id": None, "sources": srcs, "entries": out}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    doc = build()
    text = json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    if "--write" in argv:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(text, encoding="utf-8")
    if "--check" in argv:
        if OUT.read_text(encoding="utf-8") != text:
            raise SystemExit("T729_ENTRIES.json differs from the rebuild")
    for k, v in doc["census"].items():
        print(k, json.dumps(v, sort_keys=True))
    print("t730:", json.dumps(doc["t730_coverage"]))
    return 0


if __name__ == "__main__":
    main()
