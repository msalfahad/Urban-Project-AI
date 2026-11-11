"""T-698 WIRING READINESS (development villa; method R-T698-1 in t698_rules.py is every villa). Research only: no
candidate, released, rule / knowledge version or registry file is touched; no quantity is produced or wired.

For the merged-but-unwired families T-692 put first (B4-04 external plaster -> T-314 r3, B4-05 spatter dash -> T-364,
B9-03 masonry accessories -> T-363, B7-01 stair flight -> the T-645 fix rows on the T-135 once-only rule), every ledger
row is mapped by id to the candidate of record ARCH_TAKEOFF_V3.0.68 (line index d1de50cb, T-672 Gate B PASS) or named
stale, the hosts that moved since the ledger are listed with their before / after state, the dependencies on the two
pending packages (T-314 r2 stage 080ccaa5, T-687 a8cf49c8) are resolved from their pinned extracts, and the expected
census before / after per unit and the build order are stated.

Inputs: merged repository files only (sha256-pinned in PINS) + in/PENDING_STAGES_T698.json (git blob ids of the two
pending summaries; re-extract with t698_extract_pending.py). No drawing is opened; no client data is read or written.

Rebuild:  bash scripts/agent_env.sh run --tree task-T-698 research/agents_t698/t698_alsenan.py --write
Check:    bash scripts/agent_env.sh run --tree task-T-698 research/agents_t698/t698_alsenan.py --check
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
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import t698_rules as R  # noqa: E402

SCHEMA = "URBAN_T698_WIRING_READINESS_V1"
CANDIDATE = "ARCH_TAKEOFF_V3.0.68"
IDX68 = "research/agents_t672/out/LINE_INDEX_V3_0_68.json"
IDX61 = "research/agents_t655/out/LINE_INDEX_V3_0_61.json"
IDX45 = "research/agents_t479/out/LINE_INDEX_V3_0_45.json"
T349_BIND = "research/agents_t349/SPATTER_BINDING_T349.csv"
T349_PEND = "research/agents_t349/PENDING_T349.csv"
T349_FILL = "research/agents_t349/FILL_T349.csv"
T349_SUM = "research/agents_t349/summary.json"
T337_BIND = "research/agents_t337/BINDING_T337.csv"
T337_ITEMS = "research/agents_t337/FILL_ITEMS_T314_T337.csv"
T355_WALL = "research/agents_t355/MESH_BY_WALL_T355.csv"
T355_SHAR = "research/agents_t355/SHARMAT_T355.csv"
T355_JOINT = "research/agents_t355/JOINT_MESH_CLASS_T355.csv"
T355_SUM = "research/agents_t355/summary.json"
T449_REG = "research/agents_t449/round3/out/CORRECTION_REGISTER_BLOCKWORK_T449.json"
T135 = "research/agents_t135/FLIGHTS_ONCE.csv"
T645 = "research/agents_t645/out/STAIR_HOLD_CENSUS_T645.json"
T425 = "research/agents_t425/FLIGHT_TABLE_T425.csv"
PENDING = "research/agents_t698/in/PENDING_STAGES_T698.json"
PINS = [IDX68, IDX61, IDX45, T349_BIND, T349_PEND, T349_FILL, T349_SUM, T337_BIND, T337_ITEMS, T355_WALL, T355_SHAR,
        T355_JOINT, T355_SUM, T449_REG, T135, T645, T425, PENDING]
# merge commits of the ledgers (board MERGED cells; Checker verdicts there)
SOURCES = {
    "B4-04": "T-305 face ledger (MERGED) -> T-337 binding (MERGED) -> T-314 r2 stage 080ccaa5 (QUEUED r3)",
    "B4-05": "T-317 spatter ledger -> T-349 binding (MERGED 2d22bce1) -> T-364 (QUEUED)",
    "B9-03": "T-355 r2 masonry accessories (MERGED 21f7b58a) -> T-363 (QUEUED); wall -> line crosswalk T-449 round 3",
    "B7-01": "T-135 STAIR_FLIGHT_ONCE_V1 (MERGED 05e2eab) + T-645 R-T645-1 fix rows (MERGED) via T-425 flight table",
}
OUT_JSON = HERE / "out" / "T698_READINESS.json"
OUT_CSV = HERE / "out" / "T698_ROWS.csv"
EXT_CODES = {"FIN.EXT.FINISH", "FIN.EXT.PARAPET-INNER", "FIN.EXT.PARAPET-TOP"}
SPATTER_CODES = {"FIN.PLASTER", "FIN.WALL.TILE", "FIN.EXT.FINISH", "ARCH.WINDOW_REVEAL"} | EXT_CODES


def _p(rel):
    return ROOT / rel


def sha(rel):
    return hashlib.sha256(_p(rel).read_bytes()).hexdigest()


def jload(rel):
    return json.loads(_p(rel).read_text(encoding="utf-8"))


def cload(rel):
    with open(_p(rel), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def index(rel):
    return {ln["line_id"]: ln for ln in jload(rel)["lines"]}


def num(s):
    return None if s in (None, "") else float(s)


def slug(s):
    return "".join(c if c.isalnum() else "_" for c in str(s)).strip("_")


def row(family, ledger, key, cls, host, reason, **kw):
    return dict({"family": family, "ledger": ledger, "row": key, "class": cls, "host_line_id": host, "reason": reason},
                **kw)


# ============================================================================================ pending packages
def pending():
    p = jload(PENDING)
    s314 = p["T-314"]
    keys314 = {r["line_key"]: r["line_id"] for r in s314["rows"] if r["action"] == "ADD"}
    keys314.update({r["line_id"]: r["line_id"] for r in s314["rows"] if r["action"] == "ADD"})
    chg314 = {r["line_id"]: f"T-314 r2 {r['action']} {r['before']['state']} -> {r['after']['state']} "
                            f"{r['net']}" for r in s314["rows"] if r["action"] == "CHANGE"}
    chg687 = {r["line_id"]: f"T-687 {r['action']} {r['before']['state']} {r['before']['low']}..{r['before']['high']} -> "
                            f"{r['after']['state']} {r['after']['value'] or ''}{r['after']['low']}..{r['after']['high']}"
              for r in p["T-687"]["rows"] if r["change"] == "CHANGE"}
    add687 = [r["line_id"] for r in p["T-687"]["rows"] if r["change"] != "CHANGE"]
    missing314 = {m["key"]: m for m in s314["missing_items"]}
    return p, keys314, chg314, chg687, add687, missing314


def missing_of(name, missing314):
    """a 'NEW <code> ...' host that the T-314 stage lists among its MISSING items (no line by design): the entry whose
    code is the host's code, the one also naming the host's next word when several share the code."""
    words = name.replace("NEW ", "").replace("(m2)", "").replace("(m.l)", "").replace("(m.l, all floors)", "").split()
    if not words:
        return None
    same = [m for k, m in missing314.items() if k.split()[0] == words[0]]
    if len(same) > 1:
        same = [m for m in same if any(w in m["key"] for w in words[1:])] or \
               [m for m in same if len(m["key"].split()) == 1 or "(" in m["key"].split()[1]]
    return same[0] if same else None


def missing_reason(name, missing314, default):
    m = missing_of(name, missing314)
    return f"T-314 r2 lists it MISSING: {m['key']} {m['status']} ({m['why']})" if m else default


# ============================================================================================ B4-04 external plaster
def b404(i68, i61, P):
    p, keys314, chg314, _, _, missing314 = P
    out = []
    for r in cload(T337_BIND):
        cls, host, why = R.classify(r["line"], allowed_codes=EXT_CODES, target=i68, reference=i61,
                                    pending_lines=keys314, pending_name="T-314 r2")
        out.append(row("B4-04", "T-337 BINDING", r["key"], cls, host, why, ledger_state=r["status"], unit="m2",
                       qty=None if r["status"] in ("HELD", "UNKNOWN") else num(r["lo"]), lo=num(r["lo"]),
                       hi=num(r["hi"]), host_named=r["line"]))
    for r in cload(T337_ITEMS):
        cls, host, why = R.classify(r["line"], allowed_codes=EXT_CODES, target=i68, reference=i61,
                                    pending_lines=keys314, pending_name="T-314 r2")
        if cls == R.NO_HOST:
            why = missing_reason(r["line"], missing314, why)
        out.append(row("B4-04", "T-337 FILL_ITEMS", r["line"], cls, host, why, ledger_state=r["status"], unit=r["unit"],
                       qty=None, lo=num(r["qty_lo"]), hi=num(r["qty_hi"]), host_named=r["line"]))
    stage = []
    for r in p["T-314"]["rows"]:
        if r["action"] == "CHANGE":
            cls, host, why = R.classify(r["line_id"], allowed_codes=EXT_CODES, target=i68, reference=i61)
        else:   # an added stage line must not collide with a V3.0.68 id
            cls, host, why = ((R.STALE, None, "stage id collides with a V3.0.68 line") if r["line_id"] in i68 else
                              (R.PENDING_LINE, r["line_id"], "added by the T-314 stage; id free in V3.0.68"))
        stage.append(row("B4-04", "T-314 r2 stage", r["line_id"], cls, host, why, ledger_state=r["evidence_status"],
                         unit="m2", qty=None, lo=(r["net"] or [None])[0], hi=(r["net"] or [None, None])[-1],
                         host_named=r["line_key"], stage_after=r["after"]["state"]))
    return out, stage


# ============================================================================================ B4-05 spatter dash
def opening_host(i68, kind, opening):
    if kind in ("FIN.PLASTER", "REVEAL.ARCH"):
        want = [ln for ln in i68.values() if ln["item_code"] == "FIN.PLASTER"
                and f"-REVEAL-{opening}:THROUGH:JAMBS_HEAD" in ln["element_id"]]
    else:
        side = "IN" if kind == "REVEAL.WINDOW_IN" else "OUT"
        want = [ln for ln in i68.values() if ln["item_code"] == "ARCH.WINDOW_REVEAL"
                and f"-REVEAL-{opening}:{side}:JAMBS_HEAD" in ln["element_id"]]
    return want


def b405(i68, i45, P):
    _, keys314, chg314, chg687, _, missing314 = P
    chg = dict(chg314)
    chg.update(chg687)
    out = []
    for r in cload(T349_BIND):
        h = r["carrier_line"]
        cls, host, why = R.classify(h, allowed_codes=SPATTER_CODES, target=i68, reference=i45, pending_changed=chg,
                                    pending_lines=keys314, pending_name="T-314 r2 / T-687")
        if cls == R.NO_HOST:
            why = missing_reason(h, missing314, why)
        out.append(row("B4-05", "T-349 BINDING", r["row_id"], cls, host, why, ledger_state=r["state"], unit="m2",
                       qty=num(r["m2"]) if r["state"] not in ("HELD", "UNKNOWN") else None, lo=num(r["lo"]),
                       hi=num(r["hi"]), host_named=h, face_family=r["family"]))
    for k, r in enumerate(cload(T349_PEND)):
        key = f"PENDING:{r['item']}:{r['opening']}"
        if r["carrier"].startswith("L-"):
            cls, host, why = R.classify(r["carrier"], allowed_codes=SPATTER_CODES, target=i68, reference=i45,
                                        pending_changed=chg, pending_name="T-687")
        else:
            hits = opening_host(i68, r["item"], r["opening"])
            if not hits:
                cls, host, why = R.STALE, None, f"no V3.0.68 carrier for {r['item']} {r['opening']}"
            elif len(hits) > 1:
                cls, host, why = R.AMBIGUOUS, None, (f"{len(hits)} V3.0.68 carriers for {r['opening']}: "
                                                        + " / ".join(f"{h['line_id']} {R.state_text(h)}" for h in hits)
                                                        + ": the row must be split by carrier before wiring")
            else:
                h = hits[0]
                host = h["line_id"]
                want = num(r["m2"])
                if host in chg:
                    cls, why = R.PENDING_CHANGE, f"carrier {h['element_id']}: {chg[host]}"
                elif want is None:
                    cls, why = R.MAPPED, f"carrier {h['element_id']} {R.state_text(h)}; ledger row HELD blank"
                elif h["measured_net"] is not None and abs(h["measured_net"] - want) <= 1e-6:
                    cls, why = R.MAPPED, f"carrier {h['element_id']} {R.state_text(h)} = ledger {want}"
                else:
                    cls, why = R.HOST_CHANGED, (f"carrier {h['element_id']} {R.state_text(h)} differs from the "
                                                f"ledger {want} m2: restate the spatter row on the carrier")
        out.append(row("B4-05", "T-349 PENDING", key, cls, host, why, ledger_state=r["status"], unit="m2",
                       qty=num(r["m2"]), lo=None, hi=None, host_named=r["carrier"], face_family="PENDING"))
    return out


# ============================================================================================ B9-03 accessories
def wall_hosts(i68):
    """T-449 round 3 register (V3.0.26 statuses reproduced on V3.0.44): wall -> parent line, status; the part line is
    the parent element + '#BLOCKWORK:' + slug(status + ' ' + block type) (arch_v3026.part_element_id)."""
    by_eid = {ln["element_id"]: ln for ln in i68.values() if ln["item_code"] == "MAS.BLOCK"}
    reg = [x for x in jload(T449_REG)["entries"] if x.get("item_code") == "MAS.BLOCK"]
    return {x["element_id"]: x for x in reg}, by_eid


def b903(i68, i45):
    reg, by_eid = wall_hosts(i68)
    bt = {r["wall_id"]: r["block_type"] for r in cload(T355_WALL)}
    host_of, members, carried = {}, defaultdict(list), {}
    for w, x in reg.items():
        st = x["patch"]["status"]
        s = x["patch"]["part_status"] if st == "ESTABLISHED PART + HELD" else st
        parent = i68.get(x["line_id"])
        if s in ("HELD", "HELD ON DROP"):
            host_of[w] = (x["line_id"], f"wall {st} in the register: on its parent {parent['element_id']}")
            continue
        if w not in bt:
            host_of[w] = (None, f"register piece {w} ({s}, {x['patch']['carried']} m2) has no T-355 row: block "
                                f"type not established by the ledger")
            continue
        eid = f"{parent['element_id']}#BLOCKWORK:{slug(s + ' ' + bt[w])}"
        ln = by_eid.get(eid)
        host_of[w] = ((ln or {}).get("line_id"), f"part line {eid}" if ln else f"part line {eid} absent")
        if ln:
            members[ln["line_id"]].append(w)
            carried[w] = x["patch"]["carried"]
    memb = {}
    for h, ws in sorted(members.items()):
        st68, r68 = R.membership_check(ws, carried, i68[h])
        st45, r45 = R.membership_check(ws, carried, i45.get(h))
        named = None
        if st68 == "RESIDUAL":
            drop = [w for w in ws if abs(r68 + carried[w]) <= 1e-6]
            extra = [w for w, x in reg.items() if host_of[w][0] is None and x["line_id"] == next(
                x2["line_id"] for w2, x2 in reg.items() if w2 == ws[0]) and abs(r68 - x["patch"]["carried"]) <= 1e-6]
            pair = [(a, b) for a in reg for b in reg if a < b and host_of[a][0] is None and host_of[b][0] is None
                    and abs(r68 - reg[a]["patch"]["carried"] - reg[b]["patch"]["carried"]) <= 1e-6
                    and reg[a]["line_id"] == reg[b]["line_id"] == reg[ws[0]]["line_id"]]
            named = (f"{drop} left the line (V3.0.68 value = the other walls)" if drop else
                     f"{extra} carried on the line without a T-355 row" if extra else
                     f"{list(pair[0])} carried on the line without a T-355 row" if pair else "UNNAMED")
        memb[h] = {"element_id": i68[h]["element_id"], "walls": ws, "v3_0_68": [st68, r68], "v3_0_45": [st45, r45],
                   "residual_named": named}
    out = []
    left = {}
    for h, m in memb.items():
        if m["v3_0_68"][0] == "RESIDUAL" and "left the line" in (m["residual_named"] or ""):
            gone = [w for w in m["walls"] if abs(m["v3_0_68"][1] + carried[w]) <= 1e-6]
            rest = [w for w in m["walls"] if w not in gone]
            m["v3_0_68_without_left"] = list(R.membership_check(rest, carried, i68[h]))
            for w in gone:
                left[w] = (h, reg[w]["line_id"])
    moved = {h for h, m in memb.items() if m["v3_0_68"][0] == "RESIDUAL" and "without a T-355 row" not in
             (m["residual_named"] or "") and m.get("v3_0_68_without_left", ["RESIDUAL"])[0] != "CONFIRMED"}
    nonmesh = {h: m["residual_named"] for h, m in memb.items() if "without a T-355 row" in (m["residual_named"] or "")}

    def one(ledger, key, w, ledger_state, unit, qty, lo=None, hi=None):
        h, how = host_of.get(w, (None, f"wall {w} not in the T-449 register"))
        cls, host, why = R.classify(h, allowed_codes={"MAS.BLOCK"}, target=i68, reference=i45)
        if w in left:
            part, parent = left[w]
            out.append(row("B9-03", ledger, key, R.HOST_CHANGED, parent,
                           f"wall left part line {part} (its V3.0.68 value is the other walls, membership CONFIRMED "
                           f"without it); now on its parent {i68[parent]['element_id']} {R.state_text(i68[parent])}",
                           ledger_state=ledger_state, unit=unit, qty=qty, lo=lo, hi=hi, host_named=w))
            return
        if cls == R.HOST_CHANGED and any(h == v[0] for v in left.values()) and \
                memb[h].get("v3_0_68_without_left", [None])[0] == "CONFIRMED":
            cls, why = R.MAPPED, (f"host value moved only because {[k for k, v in left.items() if v[0] == h]} left "
                                  f"the line; this wall's membership CONFIRMED at V3.0.68")
        if cls == R.MAPPED and h in moved:
            cls, why = R.HOST_CHANGED, f"line membership moved: {memb[h]['residual_named']}"
        elif cls == R.MAPPED and h in nonmesh:
            why = f"{why} (line also holds {nonmesh[h]}: no mesh row, named)"
        if cls == R.NO_HOST:
            why = how
        out.append(row("B9-03", ledger, key, cls, host, f"{why}; {how}" if cls != R.NO_HOST else why,
                       ledger_state=ledger_state, unit=unit, qty=qty, lo=lo, hi=hi, host_named=w))

    for r in cload(T355_WALL):
        held = r["state"].startswith("HELD")
        one("T-355 MESH_BY_WALL", r["wall_id"], r["wall_id"], "HELD" if held else r["state"], "m",
            None if held else num(r["net_m"]), hi=num(r["held_m"]))
    for k, r in enumerate(cload(T355_SHAR)):
        one("T-355 SHARMAT", f"{r['wall_id']}|{r['column_at']}|{r['face']}", r["wall_id"], r["state"], "pcs",
            None if r["state"] == "HELD" else num(r["ties"]))
    for r in cload(T355_JOINT):
        one("T-355 JOINT_MESH_CLASS", f"{r['wall_id']}|{r['run']}|{r['side']}", r["wall_id"], f"class {r['class']}",
            "m", num(r["owner_band_m"]), hi=num(r["drawing_band_m"]))
    return out, memb


# ============================================================================================ B7-01 stair flight
def b701(i68):
    t645 = jload(T645)
    lines = {r["engine_flight"]: r for r in t645["lines"] if r["item_code"] == "FIN.STAIR.FLIGHT"}
    t425 = {}
    for r in cload(T425):
        for f in r["readings"].split():
            t425[f] = r
    out = []
    for r in cload(T135):
        L = lines.get(r["flight"])
        h = (L or {}).get("line_id")
        cls, host, why = R.classify(h, allowed_codes={"FIN.STAIR.FLIGHT"}, target=i68)
        d = t425.get(r["flight"], {})
        cnt = r["state"]
        if cls == R.MAPPED:   # the T-135 disposition against the later merged reading (T-425 table, T-645 class)
            c645 = L["class"]
            agree = ((cnt == "COUNTED" and c645 in ("A_DRAWN", "B_HELD", "C_OPEN")) or
                     (cnt in ("SEEN_THROUGH_VOID", "SEEN_ABOVE", "HELD") and c645 == "A_CARRIED"))
            same_q = (cnt != "COUNTED" or (d.get("tread_m2_drawn") and abs(float(r["counted_tread_m2"] or 0) -
                                                                               float(d["tread_m2_drawn"])) <= 1e-6))
            if not (agree and same_q):
                cls = R.HOST_CHANGED
            why = (f"T-135 {cnt} {r['counted_tread_m2'] or '-'} m2 / {r['counted_step_lm'] or '-'} lm; T-425 flight "
                   f"{d.get('flight', '?')} drawn {d.get('tread_m2_drawn') or '-'} m2 / {d.get('step_lm_drawn') or '-'} "
                   f"lm; T-645 {c645}" + ("" if agree else " (disposition differs)") +
                   ("" if same_q else " (quantity differs)"))
        out.append(row("B7-01", "T-135 FLIGHTS_ONCE", r["flight"], cls, host, why, ledger_state=cnt, unit="m2 / lm",
                       qty=None, lo=None, hi=None, host_named=r["flight"]))
    fix = []
    blank = {"class": "HELD", "measured_net": None, "held_low": None, "held_high": None}
    for f, L in sorted(lines.items()):
        ln = i68.get(L["line_id"])
        cls, host, why = R.classify(L["line_id"], allowed_codes={"FIN.STAIR.FLIGHT"}, target=i68)
        before = {k: L["before"][k] for k in blank}
        if cls == R.MAPPED and {k: ln[k] for k in blank} != before:
            cls, why = R.HOST_CHANGED, f"host {R.state_text(ln)} is not the T-645 before-state"
        a = (L.get("fix") or {}).get("after") or {}
        fix.append(row("B7-01", "T-645 FIN.STAIR.FLIGHT", L["line_id"], cls, host, why, ledger_state=L["class"],
                       unit="lm", qty=num(a.get("measured_net")), lo=num(a.get("held_low")), hi=num(a.get("held_high")),
                       host_named=f"{L['flight']} {f}", carrier=L.get("carrier")))
    return out, fix


# ============================================================================================ census before / after
def census_before(i68, codes):
    c = Counter()
    v = lo = hi = 0.0
    for ln in i68.values():
        if ln["item_code"] in codes:
            c[ln["class"] + (" blank" if ln["class"] == "HELD" and ln["held_low"] is None and ln["held_high"] is None
                             else "")] += 1
            v += ln["measured_net"] or 0
            lo += ln["held_low"] or 0
            hi += ln["held_high"] or 0
    return {"lines": sum(c.values()), "by_class": dict(sorted(c.items())), "released": round(v, 6),
            "held_low": round(lo, 6), "held_high": round(hi, 6)}


def rebase_delta(a, b, codes):
    """what r3 must re-assert: the lines that differ between the stage base and the candidate of record."""
    ch = [k for k in a if k in b and a[k] != b[k]]
    return {"changed": len(ch), "added": sum(1 for k in b if k not in a), "removed": sum(1 for k in a if k not in b),
            "changed_by_code": dict(sorted(Counter(b[k]["item_code"] for k in ch).items())),
            "family_lines_changed": sorted(k for k in ch if b[k]["item_code"] in codes)}


def mesh_split(rows):
    out = defaultdict(lambda: {"rows": 0, "determinate": 0.0, "held_rows": 0})
    for r in rows:
        k = f"{r['ledger']}|{r['class']}"
        o = out[k]
        o["rows"] += 1
        if r["qty"] is None:
            o["held_rows"] += 1
        else:
            o["determinate"] = round(o["determinate"] + r["qty"], 6)
    return dict(sorted(out.items()))


def build():
    i68, i61, i45 = index(IDX68), index(IDX61), index(IDX45)
    P = pending()
    fam = {}
    b404_rows, stage = b404(i68, i61, P)
    b405_rows = b405(i68, i45, P)
    b903_rows, memb = b903(i68, i45)
    b701_rows, b701_fix = b701(i68)
    n = {"B4-04": len(cload(T337_BIND)) + len(cload(T337_ITEMS)), "B4-04 stage": len(P[0]["T-314"]["rows"]),
         "B4-05": len(cload(T349_BIND)) + len(cload(T349_PEND)),
         "B9-03": len(cload(T355_WALL)) + len(cload(T355_SHAR)) + len(cload(T355_JOINT)),
         "B7-01": len(cload(T135)), "B7-01 fix": 14}
    for name, rows in (("B4-04", b404_rows), ("B4-04 stage", stage), ("B4-05", b405_rows), ("B9-03", b903_rows),
                       ("B7-01", b701_rows), ("B7-01 fix", b701_fix)):
        rc = R.reconcile(rows, n[name], name)
        R.check_hosts_present(rows, i68)
        R.check_no_zero_for_held(rows)
        fam[name] = {"rows": n[name], "classes": rc}
    allrows = b404_rows + stage + b405_rows + b903_rows + b701_rows + b701_fix
    # spatter census after (T-349 FILL proposed lines) split by host readiness
    fill = cload(T349_FILL)
    by_host = {r["host_named"]: r["class"] for r in b405_rows}
    split = defaultdict(lambda: {"lines": 0, "determinate_m2": 0.0, "held_lo": 0.0, "held_hi": 0.0, "blank": 0})
    for r in fill:
        cls = by_host.get(r["host_line"], "NOT_IN_BINDING")
        s = split[(r["family"], cls)]
        s["lines"] += 1
        s["determinate_m2"] = round(s["determinate_m2"] + (num(r["quantity"]) or 0), 6)
        s["held_lo"] = round(s["held_lo"] + (num(r["lo"]) or 0), 6)
        s["held_hi"] = round(s["held_hi"] + (num(r["hi"]) or 0), 6)
        s["blank"] += int(r["rows_blank"] or 0) > 0 and not r["lo"]
    p = P[0]
    t355 = jload(T355_SUM)
    t645 = jload(T645)
    census = {
        "B4-04": {"unit": "m2", "codes": sorted(EXT_CODES), "before_v3_0_68": census_before(i68, EXT_CODES),
                  "after_t314_stage": p["T-314"]["totals_moved"]["FIN.EXT.FINISH|m2"]["v3_0_62"],
                  "rebase_v3_0_61_to_v3_0_68": rebase_delta(i61, i68, EXT_CODES),
                  "note": "after = the T-314 r2 stage on V3.0.61; valid on V3.0.68 only because the 3 hosts are "
                          "byte-equal (stage rows MAPPED vs the V3.0.61 index); r3 re-runs it on V3.0.68"},
        "B4-05": {"unit": "m2", "before_v3_0_68": {"lines": 0, "note": "no B4-05 line in the candidate"},
                  "after_t349_fill_by_host_class": {f"{k[0]}|{k[1]}": v for k, v in sorted(split.items())},
                  "after_t349_line_level": jload(T349_SUM)["line_level"]},
        "B9-03": {"unit": "m / pcs", "before_v3_0_68": {"lines": 0, "note": "no mesh / sharmat / joint-mesh line"},
                  "after_t355": {"mesh_strip_net_m": t355["mesh_primary_total_net_m"],
                                 "mesh_strip_held_by_cause_m": t355["mesh_held_by_cause_m"],
                                 "sharmat_ties_pcs": t355["ties_primary_total"],
                                 "joint_mesh_by_class_owner_band_m": {k: v["owner_band_m"] for k, v in
                                                                      t355["joint_mesh_by_class"].items()},
                                 "by_host_class": mesh_split(b903_rows),
                                 "status": "ASSUMED - OWNER-APPROVED module 0.200 (Q-77 / Q-75), PROVISIONAL; "
                                           "white walls HELD by name; OPTIONAL items, never inside MAS.BLOCK m2"}},
        "B7-01": {"unit": "lm", "before_v3_0_68": census_before(i68, {"FIN.STAIR.FLIGHT"}),
                  "after_t645": {"by_class": Counter(r["ledger_state"] for r in b701_fix),
                                 "released_lm": round(sum(r["qty"] or 0 for r in b701_fix), 6),
                                 "bounded_low_lm": round(sum(r["lo"] or 0 for r in b701_fix), 6),
                                 "bounded_lines": sum(1 for r in b701_fix if r["lo"] is not None),
                                 "rule": t645["rule"]}},
    }
    changed_hosts = sorted({(r["family"], r["host_line_id"] or r["host_named"], r["reason"])
                            for r in allrows if r["class"] in (R.HOST_CHANGED, R.PENDING_CHANGE)})
    return {
        "schema": SCHEMA, "task": "T-698", "rule": f"{R.RULE_ID} {R.RULE_VERSION}", "candidate": CANDIDATE,
        "line_index_sha256": sha(IDX68), "pins": {k: sha(k)[:16] for k in PINS},
        "pending": {k: {"branch": v["branch"], "commit": v["commit"], "blob": v["blob"], "base": v["base"]}
                    for k, v in p.items() if k != "schema"},
        "sources": SOURCES, "families": fam, "census": census, "wall_line_membership": memb,
        "hosts_to_restate": [{"family": a, "host": b, "why": c} for a, b, c in changed_hosts],
        "rows": allrows,
    }


CSV_COLS = ("family", "ledger", "row", "class", "host_line_id", "host_named", "ledger_state", "unit", "qty", "lo", "hi",
            "reason")


def to_csv(d):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=CSV_COLS, extrasaction="ignore", lineterminator="\n")
    w.writeheader()
    for r in d["rows"]:
        w.writerow(r)
    return buf.getvalue()


def dumps(d):
    return json.dumps(d, indent=1, sort_keys=True, ensure_ascii=False, default=dict) + "\n"


def main(argv):
    d = build()
    js, cs = dumps(d), to_csv(d)
    if "--write" in argv:
        OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
        OUT_JSON.write_text(js, encoding="utf-8")
        OUT_CSV.write_text(cs, encoding="utf-8")
    elif "--check" in argv:
        ok = OUT_JSON.read_text(encoding="utf-8") == js and OUT_CSV.read_text(encoding="utf-8") == cs
        print("T698 check", "PASS" if ok else "FAIL (outputs differ from a rebuild)")
        if not ok:
            raise SystemExit(1)
    print(json.dumps(d["families"], sort_keys=True))


if __name__ == "__main__":
    main(sys.argv[1:])
