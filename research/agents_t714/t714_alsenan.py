"""T-714 development-villa build (research, unwired): the 370 HELD BLANK B10-13 STR.FORMWORK lines of the candidate of
record ARCH_TAKEOFF_V3.0.70 (line index of T-693; its formwork lines are identical in V3.0.71, T-704) given, under
R-T714-1 (t714_rules.py), the bound their concrete members now carry, or kept HELD BLANK with the cause named; plus the
T-638 fix rows FR-T638-1 .. 54 restated by V3.0.70 line id under R-T714-2 (the wiring form for the formwork Gate B).

Reads only merged repository files (sha256-pinned below); no drawing is opened. Writes out/T714_FORMWORK_BOUNDS.json,
out/T714_CENSUS.md and out/T714_WIRING_FORM.csv. No candidate, released (V2.9 + route G), rule / knowledge version or
registry file is touched; nothing is wired, released or VERIFIED.

Member states: V3.0.70 line index (released / bounded / blank), then the MERGED research ledgers that bound concrete
lines still blank in it: T-711 (1e06f656: lift necks, pit walls, parapets, stair pieces), T-712 (dfeb0240: ground
beams), T-721 (9e1ed6c5: east dome ring). A concrete bound 0 .. x has no floor and counts as blank.

    python3 -I research/agents_t714/t714_alsenan.py [--write]
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import t714_rules as R  # noqa: E402

D, BR = R.D, R.BR
SCHEMA = "URBAN_T714_FORMWORK_BOUNDS_V1"
CANDIDATE = "ARCH_TAKEOFF_V3.0.70"
INDEX = "research/agents_t693/out/LINE_INDEX_V3_0_70.json"
INDEX71 = "research/agents_t704/out/LINE_INDEX_V3_0_71.json"
T638 = "research/agents_t638/out/FORMWORK_HOLD_CENSUS_T638.json"
T402 = "research/agents_t402/HELD_LINES_T402.csv"
T711 = "research/agents_t711/out/T711_LEDGER.json"
T712 = "research/agents_t712/out/T712_LEDGER.json"
T721 = "research/agents_t721/out/T721_LEDGER.json"
PINS = {INDEX: None, INDEX71: None, T638: None, T402: None, T711: None, T712: None, T721: None}
PIN_FILE = HERE / "PINS.json"
OUT_JSON = HERE / "out" / "T714_FORMWORK_BOUNDS.json"
OUT_MD = HERE / "out" / "T714_CENSUS.md"
OUT_CSV = HERE / "out" / "T714_WIRING_FORM.csv"
ITEM = "STR.FORMWORK"

BLOCK_KINDS = {
    "C_OQ10": "OQ-10: below natural ground the face is formed or earth-cast; the drawings print neither (working space / "
              "excavation method, one designer item with B1 OQ-13)",
    "C_METHOD": "dome casting method not printed (a top form exists only if cast between two forms, T-185)",
    "C_THICKNESS": "material / thickness not printed (dome drum / tower shell, T-185, Q-18)",
    "C_SECTION": "no section / mark for the member (dome ring, D-28)",
    "C_MARK": "unmarked band piece (no register member)",
    "C_COUNT": "boundary pads: count not printed",
    "C_DROP": "sunken drop D-41 not printed",
    "C_CONTACT": "contact with the adjacent member not printed",
}


def sha16(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()[:16]


def check_pins():
    pins = json.loads(PIN_FILE.read_text(encoding="utf-8"))
    bad = {p: (sha16(p), v) for p, v in pins.items() if sha16(p) != v}
    if bad:
        raise R.Refused(f"input drift (sha256[:16] now, pinned): {bad}")
    return pins


def load():
    pins = check_pins()
    idx = json.loads((ROOT / INDEX).read_text(encoding="utf-8"))
    idx71 = json.loads((ROOT / INDEX71).read_text(encoding="utf-8"))
    led = {}
    for path, key, src in ((T711, "lines", "T-711"), (T712, "lines", "T-712"), (T721, "rows", "T-721")):
        for r in json.loads((ROOT / path).read_text(encoding="utf-8"))[key]:
            led[r["line_id"]] = dict(r, _src=src)
    with open(ROOT / T402, encoding="utf-8", newline="") as fh:
        t402 = {r["line_id"]: r for r in csv.DictReader(fh)}
    return {"pins": pins, "index": {x["line_id"]: x for x in idx["lines"]},
            "index71": {x["line_id"]: x for x in idx71["lines"]},
            "t638": json.loads((ROOT / T638).read_text(encoding="utf-8")), "ledgers": led, "t402": t402}


# ---- member ----------------------------------------------------------------------------------------------------------

def line_state(lid, data):
    """(class, low, high, cause, source) of one concrete line on the candidate + merged ledgers."""
    if lid in data["ledgers"]:
        r = data["ledgers"][lid]
        b = r.get("bound") or r.get("class")
        if b == "AT_LEAST":
            return "AT_LEAST", D(r["at_least_m3"]), None, f"{r['_src']} AT_LEAST: {r.get('item') or r.get('why', '')}", r["_src"]
        return "BLANK", None, None, f"{r['_src']} BLANK_NAMED: {r.get('item') or r.get('why', '')}", r["_src"]
    x = data["index"].get(lid)
    if x is None:
        return "BLANK", None, None, "concrete line not in the candidate", "-"
    if x["measured_net"] is not None:
        return "RELEASED", D(repr(x["measured_net"])), D(repr(x["measured_net"])), "", "V3.0.70"
    if x["held_low"] is not None and x["held_high"] is not None:
        lo, hi = D(repr(x["held_low"])), D(repr(x["held_high"]))
        if lo <= 0:
            return "BLANK", None, None, f"concrete bound {lo} .. {hi}: no floor", "V3.0.70"
        return "BOUNDED", lo, hi, "", "V3.0.70"
    return "BLANK", None, None, "concrete line HELD BLANK (no figure, no bound)", "V3.0.70"


def member_of(row, data):
    lines = [row["concrete_line"]] if row.get("concrete_line") else list(row.get("member_lines") or [])
    states = [(lid,) + line_state(lid, data) for lid in lines]
    if not states:
        return R.member("BLANK", cause="no concrete line carries the member (missing category / no register member)"), states
    if any(s[1] == "BLANK" for s in states):
        why = "; ".join(f"{s[0][:10]} {s[4]}" for s in states if s[1] == "BLANK")
        return R.member("BLANK", cause=why), states
    if all(s[1] == "RELEASED" for s in states):
        return R.member("RELEASED"), states
    if any(s[1] == "AT_LEAST" for s in states):
        return R.member("AT_LEAST", low=min(s[2] for s in states if s[2] is not None and s[2] > 0)), states
    held = [s for s in states if s[1] == "BOUNDED"]
    return R.member("BOUNDED", low=BR.add(*[s[2] for s in held]), high=BR.add(*[s[3] for s in held])), states


def hold_kind(states, data, element):
    kinds = {data["t402"][s[0]]["cls"] for s in states if s[0] in data["t402"]}
    if kinds:
        if len(kinds) > 1:
            raise R.Refused(f"one member, several T-402 hold kinds {kinds}")
        return kinds.pop()
    return element


# ---- faces -----------------------------------------------------------------------------------------------------------

def _num(v):
    return None if v in (None, "") else D(v)


def width_ratio(states, data, face_id):
    """SCALED soffit: the walk figure is at the DRAWN width; ratio = schedule width / drawn width (the two readings that
    bound the member, T-402), checked against each member line's own concrete ratio within 1 % (the concrete prints
    at 4 dp)."""
    ratios = set()
    for s in states:
        rec = data["t402"].get(s[0])
        if rec is None or s[1] != "BOUNDED":
            continue
        m = re.search(r"schedule b (\d+\.\d+)", rec["why_held"])
        b_s, b_d = D(m.group(1)), D(rec["drawn_width_m"])
        conc = (s[2] / s[3]) if b_d > b_s else (s[3] / s[2])      # figure at drawn = high end when drawn is wider
        printed = b_s / b_d
        if abs(conc - printed) > D("0.01") * printed:
            raise R.Refused(f"{face_id}: concrete ratio {conc} vs printed widths {printed}: not one width conflict")
        ratios.add(printed)
    if len(ratios) != 1:
        raise R.Refused(f"{face_id}: no single width ratio over the member lines ({ratios})")
    return ratios.pop()


def face_dep(f, mem, hk, states, data, rfi=False):
    """the R-T714-1 class of one T-638 face record under its member; returns R.face(...). `rfi`: the member's bound rests
    on a designer RFI over its section / depth / EXTENT (BLOCKED_RFI): a two-reading face range carries the section
    readings only, not the extent, so it does not follow the member's bound (DEPENDENT)."""
    fid, kind, el, ck = f["face_id"], f["kind"], f["element"], f["cause_kind"]
    lo, hi, m2, hf = _num(f["lo"]), _num(f["hi"]), _num(f["m2"]), _num(f["held_from"])
    fig = m2 if m2 is not None else hf
    if fig is None and lo is not None and hi is not None and lo == hi:
        fig = lo
    if ck == "C_SECTION" and el == "DOME" and kind == "SOFFIT" and mem["cls"] in ("AT_LEAST", "BOUNDED"):
        plans = [data["ledgers"][s[0]].get("plan_area_readings_m2") for s in states if s[0] in data["ledgers"]]
        plans = [p for p in plans if p]
        if len(plans) == 1:
            least = min(D(x) for x in plans[0])
            return R.face(fid, "FLOOR_ONLY", value=least,
                          cause="ring faces (soffit + inner / outer over the unprinted depth, D-28): soffit = plan band, "
                                "least drawn reading (T-721); the faces over the depth open")
    if ck in BLOCK_KINDS:
        return R.face(fid, "BLOCK", cause=BLOCK_KINDS[ck])
    if ck == "C_CONFLICT":
        if lo is not None and hi is not None and lo < hi and rfi:
            return R.face(fid, "DEPENDENT", cause="member BLOCKED_RFI (section / depth / extent): the face range "
                                                   "carries the section readings, not the extent the concrete bound uses")
        if lo is not None and hi is not None and lo < hi:
            return R.face(fid, "TWO_READINGS", lo=lo, hi=hi, cause="section CONFLICT: the face at both readings")
        return R.face(fid, "BLOCK", cause="section CONFLICT with no face figure at either reading (" + f["cause"][:90] + ")")
    if ck == "C_FRAMING_D":
        return R.face(fid, "CAP_ONLY", hi=hi, cause="framing depth not printed (D-26): shaft upper bound only")
    if ck == "C_LEVEL":
        if lo is None and hi is not None:
            return R.face(fid, "CAP_ONLY", hi=hi, cause="D-39: finished level caps the shaft")
        return R.face(fid, "DEPENDENT", cause="Q-54 B: the annex slab top is not proven, the shaft height follows it")
    if ck in ("SHAFT_D_SETTLED", "SPLIT_RELEASED"):
        if mem["cls"] == "RELEASED":
            return R.face(fid, "INDEPENDENT", value=fig, cause="measured, member RELEASED")
        return R.face(fid, "DEPENDENT", cause="shaft at one reading of a held column")
    if ck == "B_ADJ":
        if lo is not None and hi is not None:
            if lo == 0 and hi == 0:
                return R.face(fid, "INDEPENDENT", value=D(0), cause="contact 0 .. 0")
            if lo == 0:
                return R.face(fid, "CAP_ONLY", hi=hi, cause="contact 0 .. x decided by a neighbour")
            if lo < hi:
                return R.face(fid, "TWO_READINGS", lo=lo, hi=hi, cause="joint at the drawn and the stated outline")
        return R.face(fid, "DEPENDENT", cause="joint strip of a held column at one reading")
    if ck == "B_LINE":
        if el == "PARAPET" and lo is not None and hi is not None:
            return R.face(fid, "TWO_READINGS", lo=lo, hi=hi,
                          cause="2 x RC height x centreline: P1 upstand 0.30 (= T-711 floor) .. all RC")
        if el == "SLAB_EDGE" and fig is not None:
            if hk in ("WIDTH", "UNLABELLED", "TWO_MARKS"):
                return R.face(fid, "INDEPENDENT", value=fig, cause="edge band L x t along the beam: no beam width / depth in it")
            return R.face(fid, "DEPENDENT", cause="edge band over a held column: its length follows the column reading")
        if el == "BEAM" and fig is not None:
            side, soffit = fid.endswith("BEAM_SIDE"), fid.endswith("BEAM_SOFFIT")
            if hk == "WIDTH" and side:
                return R.face(fid, "INDEPENDENT", value=fig, cause="beam side L x (D - t): width not in it")
            if hk == "WIDTH" and soffit:
                if fig == 0:
                    return R.face(fid, "INDEPENDENT", value=D(0), cause="0 soffit")
                return R.face(fid, "SCALED", value=fig, ratio=width_ratio(states, data, fid),
                              cause="soffit b x L at the drawn width, other end at the schedule width")
            if hk == "UNLABELLED" and soffit:
                return R.face(fid, "INDEPENDENT", value=fig, cause="soffit b x L: drawn width, depth not in it")
            if hk == "UNLABELLED" and side:
                return R.face(fid, "DEPENDENT", cause="beam side follows the unprinted depth")
            return R.face(fid, "DEPENDENT", cause=f"beam face under hold {hk}")
        if fig is None and lo is None:
            return R.face(fid, "BLOCK", cause="no face figure recorded (" + f["cause"][:100] + ")")
        return R.face(fid, "DEPENDENT", cause=f"face of a held member at one reading ({hk})")
    raise R.Refused(f"{fid}: cause kind {ck} has no R-T714-1 class")


# ---- build -----------------------------------------------------------------------------------------------------------

def _s(x):
    return None if x is None else format(x, "f")


def build(data):
    rows_out, wiring = [], []
    for row in sorted(data["t638"]["lines"], key=lambda r: r["line_id"]):
        lid = row["line_id"]
        ix = data["index"].get(lid)
        assert ix is not None and ix["item_code"] == ITEM and ix["class"] == "HELD", lid
        assert ix["measured_net"] is None and ix["held_low"] is None and ix["held_high"] is None, lid
        assert data["index71"][lid] == ix, f"{lid}: V3.0.71 differs from V3.0.70"
        mem, states = member_of(row, data)
        hk = hold_kind(states, data, row["faces"][0]["element"] if row["faces"] else "-")
        if row["class"] == "A_FIX":
            fx = row["fix"]
            w = R.restate_fix(fx["id"], lid, row["element_id"], ix)
            after = fx["after"]
            comp = fx.get("companion")
            wiring.append(dict(w, kind=fx["kind"], before="HELD blank", after_class=after["class"],
                               after_m2=after["measured_net"], companion_low=(comp or {}).get("held_low"),
                               companion_high=(comp or {}).get("held_high"), basis=fx["basis"]))
            res = {"line_id": lid, "cls": "FIX_ROW", "low": None, "high": None,
                   "why": f"T-638 {fx['id']} {fx['kind']} {after['measured_net']} m2 (wiring form, R-T714-2: {w['state']})",
                   "cap_beside": None}
            faces = []
        else:
            rfi = "BLOCKED_RFI" in row["cause"] and mem["cls"] == "BOUNDED"
            faces = [face_dep(f, mem, hk, states, data, rfi) for f in row["faces"]]
            res = R.combine(lid, mem, faces)
        rows_out.append({
            "line_id": lid, "element_id": row["element_id"], "t638_class": row["class"],
            "member": {"class": mem["cls"], "low": _s(mem["low"]), "high": _s(mem["high"]), "hold": hk,
                       "lines": [{"line_id": s[0], "class": s[1], "low": _s(s[2]), "high": _s(s[3]), "source": s[5]}
                                 for s in states]},
            "faces": [{"face_id": f["face_id"], "dep": f["dep"],
                       "low": _s(None if f["low"] is None else BR.round_low(f["low"])),
                       "high": _s(None if f["high"] is None else BR.round_high(f["high"])),
                       "cause": f["cause"]} for f in faces],
            "class_after": res["cls"], "low": _s(res["low"]), "high": _s(res["high"]),
            "cap_beside": _s(res.get("cap_beside")), "why": res["why"]})
    return rows_out, wiring


def summarise(rows, wiring):
    by = Counter(r["class_after"] for r in rows)
    mem_by = Counter((r["member"]["class"], r["class_after"]) for r in rows)
    bounded = [r for r in rows if r["class_after"] == "BOUNDED"]
    atl = [r for r in rows if r["class_after"] == "AT_LEAST"]
    s = {
        "lines": len(rows), "by_class": dict(sorted(by.items())),
        "by_member_class": {f"{a} -> {b}": n for (a, b), n in sorted(mem_by.items())},
        "bounded_low_m2": _s(BR.add(*[D(r["low"]) for r in bounded])) if bounded else "0",
        "bounded_high_m2": _s(BR.add(*[D(r["high"]) for r in bounded])) if bounded else "0",
        "at_least_m2": _s(BR.add(*[D(r["low"]) for r in atl])) if atl else "0",
        "fix_rows": len(wiring), "fix_rows_stale": sum(w["state"] == "STALE" for w in wiring),
        "fix_rows_m2": _s(BR.add(*[D(w["after_m2"]) for w in wiring])),
        "blank_named": by.get("BLANK_NAMED", 0),
        "cap_beside_lines": sum(r["cap_beside"] is not None for r in rows),
    }
    return s


def why_counts(rows):
    c = Counter()
    for r in rows:
        if r["class_after"] == "BLANK_NAMED":
            c[r["why"][:120]] += 1
    return c


def render_md(rows, wiring, s):
    out = [f"# T-714 census: {s['lines']} HELD BLANK STR.FORMWORK lines on {CANDIDATE} (R-T714-1 / R-T714-2)", "",
           "Research only: nothing wired, released or VERIFIED; bounds are beside, never summed into a released total.",
           "", "| class after | lines |", "|---|---|"]
    out += [f"| {k} | {v} |" for k, v in s["by_class"].items()]
    out += ["", f"BOUNDED beside: {s['bounded_low_m2']} .. {s['bounded_high_m2']} m2; AT_LEAST beside: "
            f"{s['at_least_m2']} m2; fix rows {s['fix_rows']} = {s['fix_rows_m2']} m2 (stale {s['fix_rows_stale']}).",
            "", "| member class -> line class | lines |", "|---|---|"]
    out += [f"| {k} | {v} |" for k, v in s["by_member_class"].items()]
    out += ["", "## Bounded / AT_LEAST lines", "", "| line | member (hold) | concrete m3 | faces | formwork m2 |",
            "|---|---|---|---|---|"]
    for r in rows:
        if r["class_after"] in ("BOUNDED", "AT_LEAST"):
            m = r["member"]
            fs = "; ".join(f"{f['face_id'][-30:]} {f['dep']} {f['low']}..{f['high']}" for f in r["faces"])
            fw = f"{r['low']} .. {r['high']}" if r["class_after"] == "BOUNDED" else f">= {r['low']}"
            out.append(f"| {r['line_id'][:10]} | {m['class']} ({m['hold']}) | {m['low']} .. {m['high']} | {fs} | {fw} |")
    out += ["", "## BLANK_NAMED causes (first 120 characters)", "", "| lines | cause |", "|---|---|"]
    out += [f"| {n} | {k} |" for k, n in why_counts(rows).most_common()]
    return "\n".join(out) + "\n"


def write():
    data = load()
    rows, wiring = build(data)
    s = summarise(rows, wiring)
    doc = {"schema": SCHEMA, "task": "T-714", "candidate": CANDIDATE, "rules": R.RULES, "pins": data["pins"],
           "not_claimed": "development villa; nothing wired, released or VERIFIED; no freelancer formwork row exists "
                          "(FREELANCER_NO_ROW): no %; V2.9 + route G unchanged",
           "summary": s, "lines": rows, "wiring_form": wiring}
    OUT_JSON.parent.mkdir(exist_ok=True)
    OUT_JSON.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    OUT_MD.write_text(render_md(rows, wiring, s), encoding="utf-8")
    cols = ["fix", "line_id", "state", "why", "kind", "before", "after_class", "after_m2", "companion_low",
            "companion_high", "basis"]
    with open(OUT_CSV, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, lineterminator="\n")
        w.writeheader()
        for x in sorted(wiring, key=lambda x: int(x["fix"].split("-")[-1])):
            w.writerow({k: x.get(k) for k in cols})
    return doc


if __name__ == "__main__":
    if "--pin" in sys.argv:
        PIN_FILE.write_text(json.dumps({p: sha16(p) for p in PINS}, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    if "--write" in sys.argv:
        d = write()
    else:
        data = load()
        rows, wiring = build(data)
        d = {"summary": summarise(rows, wiring)}
        for k, n in why_counts(rows).most_common():
            print(n, k)
    print(json.dumps(d["summary"], indent=1))
