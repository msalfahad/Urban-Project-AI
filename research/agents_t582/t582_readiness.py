"""T-582 GATE B READINESS for T-498 and T-423 r2 (lane I, non-candidate, research only; R-T582-1).

Closes the four T-580 dry-run findings that stop the two Gate B packages, without wiring anything and without
choosing any quantity:

  F-T580-1  a quantity CLASS per lintel row (RELEASED / AT_LEAST / HELD), set by the source state of the Checker-
            merged verdicts (T-516 bearing state -> V2 lintel state; T-524 deficit-end bounds; T-571 count), never by
            the size of the total. Class -> index state is one fixed map (CLASS_STATE).
  F-T580-2  the T-498 stage identity regenerated on V3.0.58 (4,999 lines) as far as no unmerged script must run.
  F-T580-3  L-4ccc5dc2's before stated from the T-498 stage extract row it was added by.
  F-T580-4  T-423 r2: old -> new line id per line, by element id (the 6 lines T-580 could not address are addressed
            from committed sources: T-335 FILL / T-283 dome table / T-327 strip), with its renumbered version slot.

Then the R-T580-1 overlay (research/agents_t580/overlay.py, read only, never edited) is re-run on the pinned V3.0.58
index with these rows in place of T-580's T-498 / T-423 packages; every other package is T-580's own, unchanged.

R-T582-1 (every villa on the line-index scheme): a line handed to Gate B carries (a) one quantity class from
CLASS_BY_SOURCE_STATE, keyed by the source verdict's own state, with the verdict named; (b) a stated before; (c) an
address resolvable on the candidate of record by line id AND element id (a renumbered id must point at the same
element). A class missing, a HELD printed as 0, or an id pointing at another element is refused.

Rebuild: python3 -I research/agents_t582/t582_readiness.py  (--check compares with out/T582_READINESS.json).
"""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT_JSON = HERE / "out/T582_READINESS.json"

T580_DIR = ROOT / "research/agents_t580"
V2 = ROOT / "research/agents_t536/WIRING_MANIFEST_V2.json"
T516 = ROOT / "research/agents_t516/out/JAMB_BEARING_T516.json"
T524 = ROOT / "research/agents_t524/t524_lintel_end_ownership.py"
T571 = ROOT / "research/agents_t571/out/T571_LINTEL_COUNT.json"
T335_FILL = ROOT / "research/agents_t335/FILL_T284_T335.csv"
T283_DOMES = ROOT / "research/agents_t283/DOMES_T283.csv"
STAGE = T580_DIR / "in/T498_STAGE_ROWS.json"
INPUTS = {
    V2: "305c2cf0c712824ea3cd6ceaa7aee2781642deb0274d193554c846d49febacf3",
    T516: None, T571: None, T335_FILL: None, T283_DOMES: None, T524: None,
    STAGE: None, T580_DIR / "overlay.py": None, T580_DIR / "t580_alsenan.py": None,
}

# ---- R-T582-1 class map ------------------------------------------------------------------------------------------
# source state (V2 stream_S lintel state, the Checker-merged T-516 / T-519 / T-524 reading) -> quantity class.
# BOUNDED states are ranges (the V2 / V4 / V5 manifest convention: BOUNDED_* -> HELD with the range); a printed minimum
# is the low end, not the built value (T-516 s.6: no built bearing printed, MEASURED never reached on this villa).
CLASS_BY_SOURCE_STATE = {
    "MEASURED": "RELEASED",
    "PROVISIONAL": "RELEASED",
    "BOUNDED_MIN_BEARING": "AT_LEAST",
    "HELD_BY_NAME": "HELD",
}
CLASSES = ("RELEASED", "AT_LEAST", "HELD")


class ReadinessError(Exception):
    pass


def _d(x):
    return None if x is None else Decimal(str(x))


def _f(x):
    return None if x is None else float(format(x.normalize() if isinstance(x, Decimal) else Decimal(str(x)), "f"))


def sha256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _load(p, name):
    if str(Path(p).parent) not in sys.path:
        sys.path.insert(0, str(Path(p).parent))
    spec = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ---- generic rule (any villa) ------------------------------------------------------------------------------------

def class_state(qclass, low=None, high=None, value=None):
    """quantity class -> index state (overlay schema). AT_LEAST / HELD are never released; HELD never prints 0."""
    if qclass not in CLASSES:
        raise ReadinessError(f"CLASS_MISSING: {qclass!r} is not one of {CLASSES}")
    if qclass == "RELEASED":
        if value is None:
            raise ReadinessError("RELEASED_BLANK: a RELEASED class needs its value")
        return {"class": "RELEASED", "measured_net": value, "held_low": None, "held_high": None}
    if qclass == "AT_LEAST":
        if low is None or _d(low) <= 0:
            raise ReadinessError("AT_LEAST_NO_LOW: an AT_LEAST class needs a positive drawn low")
        if high is not None and _d(high) < _d(low):
            raise ReadinessError("AT_LEAST_HIGH_BELOW_LOW")
        return {"class": "HELD", "measured_net": None, "held_low": low, "held_high": high}
    if value is not None or (low is not None and _d(low) == 0 and high is not None and _d(high) == 0):
        raise ReadinessError("HELD_AS_0: a HELD class carries no figure on the line (bounds go beside)")
    return {"class": "HELD", "measured_net": None, "held_low": None, "held_high": None}


def classify(row):
    """row: {line_id, source_state, verdicts[...]} -> quantity class. Refuses a row with no class source."""
    s = row.get("source_state")
    if not s or s not in CLASS_BY_SOURCE_STATE:
        raise ReadinessError(f"CLASS_MISSING: {row.get('line_id')} source state {s!r} has no class")
    if not row.get("verdicts"):
        raise ReadinessError(f"CLASS_UNSOURCED: {row.get('line_id')} names no source verdict")
    return CLASS_BY_SOURCE_STATE[s]


def class_totals(rows):
    """per class: lines, released m3, low / high sums (open highs counted apart, never 0), beside bounds (pairs once)."""
    out = {c: {"lines": 0, "released": Decimal(0), "low": Decimal(0), "high": Decimal(0), "high_open_n": 0,
               "blank_n": 0, "beside_low": Decimal(0), "beside_high": Decimal(0), "beside_none_n": 0}
           for c in CLASSES}
    pairs_seen = set()
    for r in rows:
        t = out[r["qclass"]]
        t["lines"] += 1
        a = r["after"]
        if a["class"] == "RELEASED":
            t["released"] += _d(a["measured_net"])
        elif a["held_low"] is None and a["held_high"] is None:
            t["blank_n"] += 1
        else:
            t["low"] += _d(a["held_low"])
            if a["held_high"] is None:
                t["high_open_n"] += 1
            else:
                t["high"] += _d(a["held_high"])
        b = r.get("beside_bound")
        if r["qclass"] == "HELD":
            if b is None:
                t["beside_none_n"] += 1
            elif b.get("pair"):
                k = tuple(b["pair"])
                if k not in pairs_seen:
                    pairs_seen.add(k)
                    t["beside_low"] += _d(b["low"])
                    t["beside_high"] += _d(b["high"])
            else:
                t["beside_low"] += _d(b["low"])
                t["beside_high"] += _d(b["high"])
    return {c: {k: (_f(v) if isinstance(v, Decimal) else v) for k, v in t.items()} for c, t in out.items()}


def remap(old_index, new_index, old_ids):
    """old line id -> new line id by element id (+ item code, unit). A new id on another element is refused."""
    out = []
    by_elem = {}
    for lid, l in new_index.items():
        by_elem.setdefault((l["item_code"], l["element_id"], l.get("unit")), []).append(lid)
    for oid in old_ids:
        o = old_index.get(oid)
        if o is None:
            out.append({"old": oid, "new": None, "status": "NO_LINE", "cause": "id not in the old index"})
            continue
        key = (o["item_code"], o["element_id"], o.get("unit"))
        hits = by_elem.get(key, [])
        if len(hits) != 1:
            out.append({"old": oid, "new": None, "status": "NO_LINE",
                        "cause": f"{len(hits)} lines carry {key} on the new index"})
            continue
        nid = hits[0]
        if new_index[nid]["element_id"] != o["element_id"]:
            raise ReadinessError(f"REMAP_OTHER_ELEMENT: {oid} -> {nid}")
        out.append({"old": oid, "new": nid, "status": "SAME_ID" if nid == oid else "RENUMBERED",
                    "element_id": o["element_id"], "item_code": o["item_code"]})
    return out


def check_remap(m, new_index):
    """adverse guard for a hand-written map: the new id must exist and carry the old element."""
    for r in m:
        if r.get("new") is None:
            continue
        if r["new"] not in new_index:
            raise ReadinessError(f"REMAP_UNKNOWN_ID: {r['new']}")
        if new_index[r["new"]]["element_id"] != r["element_id"]:
            raise ReadinessError(f"REMAP_OTHER_ELEMENT: {r['old']} -> {r['new']} is "
                                 f"{new_index[r['new']]['element_id']}, not {r['element_id']}")
    return True


# ---- training villa: F-T580-1 lintel classes ---------------------------------------------------------------------

def t524_bounds():
    m = _load(T524, "t524_for_t582")
    b = m.build()
    per = {k: {"low": v["concrete_lo_m3"], "high": v["concrete_hi_m3"]} for k, v in b["lintels"].items()}
    pairs = {tuple(p["pair"]): {"low": p["concrete_lo_m3"], "high": p["concrete_hi_m3"]} for p in b["pairs"]}
    return per, pairs, b["summary"]


def lintel_rows(idx):
    v2 = _json(V2)
    t516 = _json(T516)
    t571 = _json(T571)
    per524, pairs524, sum524 = t524_bounds()
    paired = {o: k for k in pairs524 for o in k}
    ok = set(t516["summary"]["lintels_bearing_ok"])
    deficit = set(t516["summary"]["lintels_deficit"])
    req571 = {p["ours"] for p in t571["pairs_project_min_0.40"] if p["state_ours"] == "REQUIRED"}
    rows = []
    for r in v2["stream_S"]["lintel_lines"]:
        lid, a, b = r["line_id"], r["after"], r["before"]
        opening = r["element_id"].split(":", 1)[1]
        cur = idx.get(lid)
        if cur is None or cur["element_id"] != r["element_id"]:
            raise ReadinessError(f"{lid}: not on the index as {r['element_id']}")
        if cur["class"] != b["class"] or _d(cur["measured_net"]) != _d(b["value"]):
            raise ReadinessError(f"{lid}: V2 before {b} is not the index {cur['class']} {cur['measured_net']}")
        t516_state = "BEARING_OK" if opening in ok else ("DEFICIT" if opening in deficit else None)
        verdicts = [f"T-516 {t516_state} (merge 35db84c3, Gate A)", "T-519 PROJECT_RC (merge dd9e24c3)",
                    "T-571 REQUIRED 1 nr (Gate A)" if opening in req571 else None]
        if opening in deficit:
            verdicts.append("T-524 deficit-end bounds (merge 66ca67b4)")
        verdicts = [v for v in verdicts if v]
        row = {"line_id": lid, "element_id": r["element_id"], "opening": opening, "source_state": a["state"],
               "verdicts": verdicts, "t571_required": opening in req571}
        q = classify(row)
        # cross-checks: the class source agrees with the bearing state and the count
        if (q == "AT_LEAST") != (opening in ok) or (q == "HELD") != (opening in deficit):
            raise ReadinessError(f"{lid}: V2 state {a['state']} disagrees with T-516 {t516_state}")
        if opening not in req571:
            raise ReadinessError(f"{lid}: {opening} not REQUIRED in the T-571 count")
        if q == "AT_LEAST":
            after = class_state(q, low=a["low"], high=a["high"])
            beside = None
        else:
            after = class_state(q)
            if opening in paired:
                k = paired[opening]
                beside = {"pair": list(k), **pairs524[k], "source": "T-524 pair (shared pier, per-lintel split HELD)"}
            else:
                beside = {**per524[opening], "source": "T-524 per lintel"}
                v2b = a.get("bound_m3")
                if v2b is not None and [_d(x) for x in v2b] != [_d(beside["low"]), _d(beside["high"])]:
                    raise ReadinessError(f"{lid}: V2 bound {v2b} is not T-524 {beside}")
        rows.append(dict(row, qclass=q, before={"class": cur["class"], "measured_net": cur["measured_net"],
                                                "held_low": cur["held_low"], "held_high": cur["held_high"]},
                         after=after, beside_bound=beside,
                         evidence_status=("DRAWING-CONFIRMED low (printed MIN 0.40 m, piers measured); high pier-"
                                          "bounded or OPEN" if q == "AT_LEAST" else
                                          "HELD by name (designer item: jamb cannot take the printed minimum)")))
    if len(rows) != 16 or len({r["line_id"] for r in rows}) != 16:
        raise ReadinessError("lintel rows: not 16 distinct lines")
    return rows, sum524


# ---- training villa: F-T580-2 / F-T580-3 T-498 stage ----------------------------------------------------------------

def stage_identity(idx58, st):
    rows = st["rows"]
    ids = [r["line_id"] for r in rows]
    hosts = {r["source_line_id"] for r in rows}
    t507 = [k for k in idx58 if k not in _base57_ids()]
    problems = []
    if len(set(ids)) != len(ids):
        problems.append("duplicate stage line ids")
    clash = sorted(set(ids) & set(idx58))
    if clash:
        problems.append(f"stage ids already on V3.0.58: {clash}")
    missing = sorted(h for h in hosts if h not in idx58)
    if missing:
        problems.append(f"hosts not on V3.0.58: {missing}")
    if set(t507) & hosts:
        problems.append("a T-507 line hosts a stage row")
    live = {(l["item_code"], l["element_id"], l.get("unit")) for l in idx58.values() if l["class"] != "EXCLUDED"}
    dup = sorted(r["line_id"] for r in rows if (r["item_code"], r["element_id"], r["unit"]) in live)
    if dup:
        problems.append(f"stage rows duplicate a live line: {dup}")
    if problems:
        raise ReadinessError("; ".join(problems))
    return {
        "stale_on_branch": {"method": st["stage_method"], "extends": st["stage_extends"],
                            "base_lines": st["stage_identity"]["base_lines"],
                            "branch_commit": st["source"]["commit"][:8]},
        "regenerated": {"method": "ARCH_TAKEOFF_V3.0.59", "extends": "ARCH_TAKEOFF_V3.0.58",
                        "base_lines": len(idx58), "added": len(rows), "replaced": 0,
                        "expected_lines": len(idx58) + len(rows), "t507_lines_in_base": len(t507),
                        "stage_ids_disjoint_from_base": True, "hosts_on_base": len(hosts),
                        "t507_lines_hosting_a_stage_row": 0, "duplicate_live_lines": 0},
        "line_ids_stable_because": "engine/source/boq_line.py line_id() hashes project, item code, element id, rule "
                                   "id / version and unit, not the candidate version: renumbering V3.0.58 -> V3.0.59 "
                                   "moves no stage line id",
        "blocked_part": {
            "what": "outside_rows_sha256 and the full V3.0.59 run table on the 4,999-line V3.0.58 rows (the branch "
                    "runner research/agents_t498/v3059_run.py on the private drawings)",
            "refusal": "AGENT_ENV FAIL: run allows only tools/alsenan_scoreboard.py or tools/alsenan_keymap.py",
            "owner": "T-498 package (its own runner), or the wrapper allow-list (owner item)"},
    }


_B57 = None


def _base57_ids():
    global _B57
    if _B57 is None:
        t580 = _load(T580_DIR / "t580_alsenan.py", "t580_for_t582_ids")
        _B57 = {l["line_id"] for l in _json(t580.INDEX57)["lines"]}
    return _B57


def l4ccc_before(st, idx58):
    lid = "L-4ccc5dc26bd2472b03ad"
    r = next(x for x in st["rows"] if x["line_id"] == lid)
    host = idx58[r["source_line_id"]]
    if r["state"] != "BLOCKED_RFI" or host["class"] != "HELD" or host["measured_net"] is not None:
        raise ReadinessError("L-4ccc: stage state or host state is not the HELD blank T-580 read")
    return {"line_id": lid, "element_id": r["element_id"], "item_code": r["item_code"], "unit": r["unit"],
            "before": {"class": "HELD", "measured_net": None, "held_low": None, "held_high": None},
            "before_source": f"T-498 stage row (state BLOCKED_RFI, branch {st['source']['commit'][:8]}, extract "
                             f"sha256 {st['source']['sha256'][:8]}): the line it adds is HELD blank",
            "host": {"line_id": r["source_line_id"], "class": host["class"], "measured_net": None,
                     "why": "2F block contract line HELD (D-39); T-523 STALE_CLASS"},
            "after": {"class": "HELD", "measured_net": None, "held_low": None, "held_high": None},
            "beside": {"conditional_range_kg": [63.82125, 71.62425], "source": "V5 glue_hosts v5_expected_after",
                       "not_a_bound_of": "the V4 legacy low 65.14425 (R-T544-1 part 2: the D x (w + 0.80) low end is "
                                         "no bound)"},
            "quantity_moved": 0}


# ---- training villa: F-T580-4 T-423 r2 --------------------------------------------------------------------------------

T423_NAMED = {  # prefix -> what T-423 r1 s.2 says it is
    "L-a34d0920": "1F-02 tile face piece (FACE_PIECE, T-388 F1)",
    "L-3eba04f2": "1F-02 backing face piece (FACE_PIECE, T-388 F1)",
    "L-eb3be58f": "GF open plan ceiling (set aside, named; residual 9.785604)",
    "L-fc116bb6": "1F open plan ceiling (set aside, named; BLOCKED_RFI)",
}
T423_GAPS = {  # the 5 CEILING_LIST lines: gross - net printed in T-423 r1 s.2
    "1.4227": "DOME:WEST", "11.5808": "DOME:WEST", "0.341845": "DOME:EAST", "1.2410": "DOME:WEST",
    "0.4472": "DOME:EAST"}


def _domes():
    out = {}
    with T283_DOMES.open(encoding="utf-8") as f:
        for r in csv.reader(f):
            if not r or r[0] not in ("west", "east"):
                continue
            for part in r[4].split(";"):
                room, gap = part.split()
                out[room] = (f"DOME:{r[0].upper()}", gap)
    return out


def t423_rows(idx57, idx58):
    rows = []
    for p, what in T423_NAMED.items():
        hit = [k for k in idx57 if k.startswith(p)]
        if len(hit) != 1:
            raise ReadinessError(f"T-423 {p}: {len(hit)} lines")
        rows.append({"old": hit[0], "piece": what, "address_source": "T-423 r1 s.2 (id prefix printed)"})
    thr = sorted(k for k, l in idx57.items() if l["item_code"] == "FIN.MARBLE.THRESHOLD")
    if len(thr) != 14:
        raise ReadinessError(f"FIN.MARBLE.THRESHOLD: {len(thr)} lines, T-423 names 14")
    rows += [{"old": k, "piece": "THRESHOLD_FIELDS (O-T327-1 / -2)", "address_source": "item code, 14 of 14"}
             for k in thr]
    domes = _domes()
    with T335_FILL.open(encoding="utf-8") as f:
        fill = {r["line_key"]: r for r in csv.DictReader(f)}
    found = {}
    for lk, r in fill.items():
        if not (r.get("horizontal_change_m2") or "").strip():
            continue
        gap = Decimal(r["horizontal_change_m2"]).copy_negate()
        for g in T423_GAPS:
            if gap == Decimal(g):
                found.setdefault(g, []).append((lk, r))
    for g, dome in T423_GAPS.items():
        hits = found.get(g, [])
        if len(hits) != 1:
            raise ReadinessError(f"CEILING_LIST gap {g}: {len(hits)} T-335 rows")
        lk, r = hits[0]
        room = r["elements"].split(":")[0]
        l = idx57.get(lk)
        if l is None or l["element_id"] != r["elements"] or _d(l["measured_net"]) != _d(r["after_horizontal_m2"]):
            raise ReadinessError(f"CEILING_LIST {g}: T-335 row {lk} is not the index line")
        d_dome, d_gap = domes.get(room, (None, None))
        if d_dome != dome or abs(Decimal(d_gap) - Decimal(g)) > Decimal("0.00005"):
            raise ReadinessError(f"CEILING_LIST {g}: T-283 dome table says {d_dome} {d_gap} for {room}")
        rows.append({"old": lk, "piece": f"CEILING_LIST: one deduction {dome}:over:{room}, gap {g} m2",
                     "address_source": f"T-335 FILL (gross {r['before_m2']} - net {r['after_horizontal_m2']}) + "
                                       f"T-283 dome table ({dome} {room} {d_gap})", "was_unaddressable": True})
    strip = [k for k, l in idx57.items() if l["item_code"] == "FIN.FLOOR.PORCELAIN"
             and l["element_id"] == "1F-THRESHOLD-D-1F-03:doorway strip"]
    if len(strip) != 1:
        raise ReadinessError(f"D-1F-03 dry strip: {len(strip)} lines")
    rows.append({"old": strip[0], "piece": "THRESHOLD_FIELDS (O-T327-2): the D-1F-03 dry strip measure pair",
                 "address_source": "element 1F-THRESHOLD-D-1F-03:doorway strip (T-327 s.2: 0.150 m2 / 1.000 lm / 1)",
                 "was_unaddressable": True})
    if len(rows) != 24:
        raise ReadinessError(f"T-423: {len(rows)} lines, its report names 22 text-only + 2 set aside")
    m = remap(idx57, idx58, [r["old"] for r in rows])
    check_remap(m, idx58)
    out = []
    for r, x in zip(rows, m):
        if x["status"] == "NO_LINE":
            raise ReadinessError(f"T-423 {r['old']}: {x['cause']}")
        l = idx58[x["new"]]
        out.append(dict(r, new=x["new"], status=x["status"], element_id=l["element_id"], item_code=l["item_code"],
                        state=OVS(l)))
    return out


def OVS(l):
    return {k: l.get(k) for k in ("class", "measured_net", "held_low", "held_high")}


T423_SLOT = {
    "r1": {"module": "engine/source/arch_v3058.py", "registry": "rules/coverage/BOQ_FAMILY_MASTER_1.55.0.json",
           "method": "ARCH_TAKEOFF_V3.0.58", "base": "V3.0.57 (4,994)", "taken_by": "T-507 (merged)"},
    "r2": {"module": "engine/source/arch_v3060.py", "registry": "rules/coverage/BOQ_FAMILY_MASTER_1.57.0.json",
           "method": "ARCH_TAKEOFF_V3.0.60", "base": "V3.0.59 = T-498 (5,073 expected)",
           "registry_content": "1.56.0 (T-498) + T-498 promotion by R-T485-1 once merged + pending V3.0.60 + the "
                               "B3-01 / B3-04 / B4-01 / B4-03 / B5-01 text; r1's T-310 promotion is already in 1.55.0 "
                               "(same PROMOTIONS_SOURCE sha256 9933a9c3): drop it",
           "condition": "after T-498 merges (Lead order T-498 -> T-423 r2); if T-498 does not merge first, r2 takes "
                        "V3.0.59 / 1.56.0 on V3.0.58 instead (one free number each, never shared)"},
}


# ---- overlay re-run ---------------------------------------------------------------------------------------------------

def run():
    t580 = _load(T580_DIR / "t580_alsenan.py", "t580_for_t582")
    OV = t580.OV
    m = t580.manifests()
    idx58 = t580.base_index()
    st = t580.stage()
    idx57 = {k: v for k, v in idx58.items() if k in _base57_ids()}
    lrows, sum524 = lintel_rows(idx58)
    l4 = l4ccc_before(st, idx58)
    sid = stage_identity(idx58, st)
    trows = t423_rows(idx57, idx58)

    # T-498: T-580's ops with the classed lintel rows and L-4ccc's stated before
    ops = []
    cls = {r["line_id"]: r for r in lrows}
    for op in t580.pkg_t498(m, st):
        if op["row"] == "LINTEL_V3":
            r = cls[op["line_id"]]
            op = dict(op, after=r["after"], note=f"class {r['qclass']} ({r['source_state']})",
                      beside=({"bound_m3": [r["beside_bound"]["low"], r["beside_bound"]["high"]],
                               **({"pair": r["beside_bound"]["pair"]} if "pair" in r["beside_bound"] else {})}
                              if r["beside_bound"] else None))
        if op["line_id"] == l4["line_id"] and op["row"] == "HOST_FACES_V5":
            op = dict(op, before=l4["before"])
        ops.append(op)
    t423ops = [t580._op("T-423 r2", "TEXT_ONLY_24", "TEXT_ONLY", r["new"], r["state"], None, note=r["piece"])
               for r in trows]
    pk = t580.packages(m, idx58, st)
    pk = [("T-498", ops) if n == "T-498" else ("T-423 r2", t423ops) if n == "T-423 r2" else (n, o) for n, o in pk]
    after, rep = OV.apply(idx58, pk, t580.RULINGS)
    status = {}
    for r in rep["rows"]:
        status.setdefault(r["package"], {}).setdefault(r["status"], 0)
        status[r["package"]][r["status"]] += 1
    flagged = [r for r in rep["rows"] if r["status"] != "APPLIED"]
    t498 = next(s for s in rep["steps"] if s["package"] == "T-498")
    t423 = next(s for s in rep["steps"] if s["package"] == "T-423 r2")
    ct = class_totals(lrows)
    released_before = sum(_d(r["before"]["measured_net"]) for r in lrows if r["before"]["class"] == "RELEASED")
    fpk = next(o for n, o in pk if n.startswith("F package"))
    return {
        "schema": "URBAN_T582_GATE_B_READINESS", "rule": "R-T582-1", "task": "T-582", "candidate": t580.CANDIDATE,
        "inputs": {str(p.relative_to(ROOT)): sha256(p) for p in sorted(INPUTS, key=str)},
        "F_T580_1_lintel_classes": {
            "class_by_source_state": CLASS_BY_SOURCE_STATE,
            "rows": [{k: r[k] for k in ("line_id", "element_id", "source_state", "qclass", "verdicts", "before",
                                         "after", "beside_bound", "evidence_status")} for r in lrows],
            "per_class": ct,
            "released_m3": {"before": _f(released_before), "after": ct["RELEASED"]["released"],
                            "change": _f(Decimal(str(ct["RELEASED"]["released"])) - released_before)},
            "at_least_low_m3": ct["AT_LEAST"]["low"],
            "t524_set_bound_m3": [sum524["corrected_lo_m3"], sum524["corrected_hi_m3"]],
            "reading": "released lintel concrete 1.016 -> 0.000 m3: no lintel has a built value on the drawings; 6 "
                       "carry an AT_LEAST low 0.502 m3 (printed MIN 0.40 m both ends, DRAWING-CONFIRMED) with the "
                       "pier-bounded high beside (5) or OPEN (D-2F-01), 10 are HELD by name with the T-524 bounds "
                       "beside (8 per lintel + the D-GF-11 / 12 pair once). The class follows the source state, not "
                       "the total; the low is never added to a released total and HELD is never 0.",
            "freelancer": "no lintel concrete row in his workbooks (T-571 Checker own read): NOT_COMPARABLE, no %",
        },
        "F_T580_2_t498_identity": sid,
        "F_T580_3_l4ccc": l4,
        "F_T580_4_t423_r2": {"slot": T423_SLOT, "lines": trows,
                             "summary": {"lines": len(trows), "same_id": sum(r["status"] == "SAME_ID" for r in trows),
                                         "renumbered": sum(r["status"] == "RENUMBERED" for r in trows),
                                         "formerly_unaddressable_now_addressed":
                                             sum(bool(r.get("was_unaddressable")) for r in trows),
                                         "no_line": 0}},
        "F_T580_5_f_package": [{"op": o["kind"], "line_id": o["line_id"], "row": o["row"],
                                "item_code": o.get("item_code") or idx58[o["line_id"]]["item_code"],
                                "element_id": o.get("element_id") or idx58[o["line_id"]]["element_id"],
                                "before": o.get("before"), "after": o.get("after")} for o in fpk],
        "overlay": {"lines": {"before": len(idx58), "after": len(after)},
                    "order": [{"package": n, "ops": len(o), "status": status.get(n, {})} for n, o in pk],
                    "flagged_rows": flagged,
                    "stale": sum(r["status"] == "STALE" for r in rep["rows"]),
                    "no_before": sum(r["status"] == "NO_BEFORE" for r in rep["rows"]),
                    "missing_line": sum(r["status"] == "MISSING_LINE" for r in rep["rows"]),
                    "unexplained_conflicts": sum(c["status"] == "UNEXPLAINED" for c in rep["conflicts"]),
                    "conflicts": rep["conflicts"],
                    "t498_totals_changed": t498["totals_changed"],
                    "t423_totals_changed": t423["totals_changed"]},
        "candidate_files_touched": 0, "released_quantities_changed": 0,
    }


def dumps(o):
    return json.dumps(o, indent=1, sort_keys=True, default=str) + "\n"


def main(argv):
    text = dumps(run())
    if "--check" in argv:
        ok = OUT_JSON.read_text(encoding="utf-8") == text
        print("T-582 readiness: committed output", "is the rebuild" if ok else "DIFFERS from the rebuild")
        return 0 if ok else 1
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
