"""T-626 builder (research, unwired): the 24 rows of the B8 waterproofing m2 lines (statement section T-546/floor,
18 rows, reference 72.01 vs engine 85.57571 m2; section T-541/membrane, 6 rows, reference 285 vs engine 209.65844 m2;
scorecard UNKNOWN 0 / 18 and 0 / 6) each given its own drawn area by handle (R-T626-1 with R-T621-1 statuses) from
the committed drawing read T626_DRAWN.json, the pinned statement and the merged T-546 / T-541 inputs (engine line
values and the reference's room cells, numbers only).

Built and compared by tests/t626_wet_roof_wp_evidence (the wrapper's pytest is the only execution path). Nothing here
changes a candidate, engine, rule / knowledge version, registry or statement file; nothing is released; no class of
the statement moves: one READING row (the roof residual) is found to DIFFER by 0.001332 m2 and its split is PROPOSED.
"""
from __future__ import annotations

import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (HERE, ROOT / "research" / "agents_t621", ROOT / "research" / "agents_t546", ROOT / "research" / "agents_t541"):
    sys.path.insert(0, str(p))
import t621_rules as R21  # noqa: E402  (evidence statuses, read only)
import t626_rules as R  # noqa: E402
import t546_inputs as I46  # noqa: E402  (engine floor lines + his room cells, read only)
import t541_inputs as I41  # noqa: E402  (engine roof lines, read only)

D = Decimal
Z = D("0")
DRAWN = HERE / "T626_DRAWN.json"
STATEMENT = ROOT / "research/agents_t620/out/RECONCILED_STATEMENT_T620.json"
STATEMENT_SHA = "db5f7bceb8b6b44b1d9f87c40e83022cdd1123789e4e3be81fe43e9bad298e69"
OUT_JSON = HERE / "out" / "T626_ROW_EVIDENCE.json"
OUT_MD = HERE / "out" / "T626_ROW_EVIDENCE.md"
FLOOR, ROOF = "T-546/floor", "T-541/membrane"

# wet basis per room: the sanitary drawing listing (T-074 hand table, MERGED, from Drive sanitary-7757.pdf) or the
# owner rule; drawn symbols inside the outline are recorded by the extractor beside it
SANITARY = {
    "GF lobby wash (2 basins)": "2 basins + FD", "GF basin space by the stair": "basin + FD",
    "GF master bath": "WC + basin + FD", "GF core W.C. 245 x 167 (wedge)": "WC + shower + basin + FD",
    "GF core W.C. 289 x 167 (wedge)": "WC + FD", "GF stair-core W.C. 175 x 135": "WC + basin + FD",
    "GF kitchen": "FD 4in", "GF driver W.C.": "WC + basin + FD", "GF W.C. by the reception room": "WC + basin + FD",
    "GF wash by the reception room": "2 basins + FD", "1F east bath 210 x 225": "WC + basin + FD",
    "1F bath by the laundry": "WC + basin + FD", "1F W.C. by the laundry": "WC + basin + FD",
    "1F west bath A 245 x 205": "WC + shower + basin + FD", "1F west bath B 245 x 205": "WC + shower + basin + FD",
    "1F laundry": "FD", "2F roof-floor W.C. 300 x 185": "WC + basin + shower + FD",
}
OWNER = {"GF pantry (wet zone, Q-37 A)": "Q-37 A (pantry is a wet zone)"}
SAN_SRC = "sanitary drawing via T-074 hand table"

# printed second read for non-rectangular rooms: expression of printed DIMENSION handles (+ the chain's own notch)
PRINTED_EXPR = {
    "GF kitchen": ("523 x 635 + 641 x (605 - 635) + notch", lambda d, n: d["523"] * d["635"] + d["641"] * (d["605"] - d["635"]) + n),
}

# statement rows -> evidence: (row name prefix, kind, terms)
#   ROOM: room key (own vs engine line); PIECE: list of (sign, measure); READING: callable(m) -> expected delta
FLOOR_SPEC = [
    ("GF lobby wash", "ROOM", "GF lobby wash (2 basins)"),
    ("GF basin space by the stair: passage reveal", "PIECE", [(1, ("rooms", "GF-BASIN-REVEAL"))]),
    ("GF basin space by the stair: his 1.705", "READING",
     lambda m: D("1.70") - (m["rooms"]["GF basin space by the stair"] + m["rooms"]["GF-BASIN-REVEAL"])),
    ("GF master bath", "ROOM", "GF master bath"),
    ("GF core W.C. 245", "ROOM", "GF core W.C. 245 x 167 (wedge)"),
    ("GF core W.C. 289", "ROOM", "GF core W.C. 289 x 167 (wedge)"),
    ("GF stair-core W.C.", "ROOM", "GF stair-core W.C. 175 x 135"),
    ("GF kitchen", "ROOM", "GF kitchen"),
    ("GF W.C. by the reception room", "ROOM", "GF W.C. by the reception room"),
    ("GF wash by the reception room", "ROOM", "GF wash by the reception room"),
    ("1F east bath", "ROOM", "1F east bath 210 x 225"),
    ("1F bath by the laundry", "ROOM", "1F bath by the laundry"),
    ("1F W.C. by the laundry", "ROOM", "1F W.C. by the laundry"),
    ("1F west bath A", "ROOM", "1F west bath A 245 x 205"),
    ("1F west bath B", "ROOM", "1F west bath B 245 x 205"),
    ("1F laundry", "ROOM", "1F laundry"),
    ("2F roof-floor W.C.", "ROOM", "2F roof-floor W.C. 300 x 185"),
    ("GF pantry", "PIECE", [(1, ("rooms", "GF pantry (wet zone, Q-37 A)"))]),
]
ENGINE_970_DEDUCTION = D("146.532") - D("115.832")   # the engine's own gross - net of line L-636fd3ff (T-321 AT379)


def _roof_specs():
    return [
        ("2F block top roof", "PIECE", [(1, ("roof", "ROOF-1390")), (-1, ("circle", "ROOF-1390", "DOME-3"))]),
        ("third dome footprint", "PIECE", [(1, ("circle", "ROOF-1390", "DOME-3"))]),
        ("two +9.70 dome footprints", "PIECE", [(1, ("circle", "ROOF-970", "DOME-W")), (1, ("circle", "ROOF-970", "DOME-E"))]),
        ("engine arc discretisation", "READING",
         lambda m: ENGINE_970_DEDUCTION - (m["circle"][("ROOF-970", "DOME-W")] + m["circle"][("ROOF-970", "DOME-E")])),
        ("pool-court slab", "PIECE", [(1, ("pool", "POOLCOURT-550-OPEN-SKY")), (1, ("pool", "POOLCOURT-550-LEDGE"))]),
        ("RESIDUAL", "READING",
         lambda m: D(I41.FREELANCER_MEMBRANE_M2) - (m["roof"]["TERRACE-550"] + m["roof"]["ROOF-430"]
                                                   + m["roof"]["ROOF-970"] + m["roof"]["ROOF-1390"])),
    ]


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load():
    drawn = json.loads(DRAWN.read_text(encoding="utf-8"))
    if _sha(STATEMENT) != STATEMENT_SHA:
        raise R.RuleError("statement changed since T-626 pinned it")
    st = json.loads(STATEMENT.read_text(encoding="utf-8"))
    secs = {s["section_id"]: s for s in st["sections"]}
    return drawn, secs[FLOOR], secs[ROOF]


def _measures(drawn):
    m = {"rooms": {}, "roof": {}, "circle": {}, "pool": {}}
    for k, v in drawn["rooms"].items():
        m["rooms"][k] = R21.evidence(v)
    for z, v in drawn["roof"].items():
        m["roof"][z] = R21.evidence(v)
        for c, cv in v["circles"].items():
            m["circle"][(z, c)] = R.q6(D(cv["area"]))
    for k, v in drawn["poolcourt"].items():
        m["pool"][k] = R21.evidence(v)
    return m


def _term(m, t):
    if t[0] == "circle":
        return m["circle"][(t[1], t[2])], f"{t[1]} {t[2]}"
    return m[t[0]][t[1]], t[1]


def _engine_floor():
    return {r[0]: D(r[2]) for r in I46.ROOMS}


def _his_floor():
    return {r[0]: (None if r[6] is None else D(r[6])) for r in I46.ROOMS}


def _row(srow, spec, m, drawn, sect):
    name, kind, terms = spec
    if not srow["name"].startswith(name):
        raise R.RuleError(f"{sect}: row {srow['name']!r} is not {name!r}")
    delta, cls = D(srow["delta"]), srow["class"]
    rec = {"section": sect, "name": srow["name"], "class": cls, "delta": str(delta), "kind": kind}
    if kind == "ROOM":
        eng, own = _engine_floor()[terms], m["rooms"][terms]
        his = _his_floor()[terms]
        ev, diff = R21.judge("ROOM", delta, own=own, engine=eng)
        R21.check_class(cls, delta, "ROOM", None if his is None else his - own)
        rec.update(measures=[terms], own=str(own), engine=str(eng), his=None if his is None else str(his),
                   own_minus_engine=str(R.q6(diff)), his_minus_own=None if his is None else str(R.q6(his - own)),
                   handles=drawn["rooms"][terms]["handles"])
    elif kind == "PIECE":
        own, ids, hs = Z, [], []
        for sign, t in terms:
            v, label = _term(m, t)
            own += sign * v
            ids.append(("+" if sign > 0 else "-") + label)
            hs += _handles(drawn, t)
        ev, diff = R21.judge("PIECE", delta, own=own)
        rec.update(measures=ids, own=str(R.q6(own)), own_minus_abs_delta=str(R.q6(diff)), handles=hs)
    else:
        exp = terms(m)
        ev, diff = R21.judge("READING", delta, expected=exp)
        rec.update(expected=str(R.q6(exp)), expected_minus_delta=str(R.q6(diff)))
    rec["evidence_status"] = ev
    return rec


def _handles(drawn, t):
    if t[0] == "circle":
        return [drawn["roof"][t[1]]["circles"][t[2]]["handle"]]
    src = drawn["poolcourt"] if t[0] == "pool" else drawn[t[0]]
    return list(src[t[1]]["handles"])


def room_table(drawn):
    """per wet room: engine line, own outline (handles), printed second read, wet basis, his cell."""
    eng, his = _engine_floor(), _his_floor()
    lids = {r[0]: r[1] for r in I46.ROOMS}
    hand = {r[0]: (None if r[8] is None else D(r[8])) for r in I46.ROOMS}   # T-074 hand boundary (T-546 upturn basis)
    out = []
    for room in eng:
        d = drawn["rooms"][room]
        own = D(d["area"])
        pr, prs = None, "chain only (printed sides listed)"
        if d.get("printed_rect"):
            pr = R.q6(D(d["printed_rect"]["area_less_notch"]))
            prs = "printed " + " x ".join(d["printed_rect"]["values"]) + " (" + " / ".join(d["printed_rect"]["handles"]) + ")"
            if D(d["notch_m2"]):
                prs += f" {d['notch_m2']} column notch {'/'.join(d['notch_columns'])}"
        elif room in PRINTED_EXPR:
            vals = {x["handle"]: D(x["m"]) for x in d["printed_dims"]}
            expr, f = PRINTED_EXPR[room]
            pr = R.q6(f(vals, D(d["notch_m2"])))
            prs = "printed " + expr
        basis = R.wet_basis(room, {"fixtures": [SANITARY[room]] if room in SANITARY else [],
                                   "fixture_source": SAN_SRC, "owner_rule": OWNER.get(room)})
        out.append({"room": room, "line_id": lids[room], "engine": str(eng[room]), "own": str(own),
                    "own_minus_engine": str(R.q6(own - eng[room])), "handles": d["handles"], "chain_from": d["chain_from"],
                    "perimeter_lm": d["perimeter"], "hand_boundary_lm_T074": None if hand[room] is None else str(hand[room]),
                    "perimeter_minus_hand_lm": None if hand[room] is None else str(R.q6(D(d["perimeter"]) - hand[room])),
                    "printed_second_read": None if pr is None else str(pr),
                    "printed_minus_own": None if pr is None else str(pr - own), "printed_basis": prs,
                    "printed_dims": [f"{x['handle']}={x['m']}{x['dir']}" for x in d["printed_dims"]],
                    "drawn_symbols_inside": d["symbols_inside"], "wet_basis": basis,
                    "his": None if his[room] is None else str(his[room])})
    return out


def build():
    drawn, fsec, rsec = load()
    m = _measures(drawn)
    rows = []
    if len(fsec["rows"]) != len(FLOOR_SPEC):
        raise R.RuleError("floor section row count changed")
    for srow, spec in zip(fsec["rows"], FLOOR_SPEC):
        rows.append(_row(srow, spec, m, drawn, FLOOR))
    rspec = _roof_specs()
    if len(rsec["rows"]) != len(rspec):
        raise R.RuleError("roof section row count changed")
    for srow, spec in zip(rsec["rows"], rspec):
        rows.append(_row(srow, spec, m, drawn, ROOF))
    fl = [r for r in rows if r["section"] == FLOOR]
    rf = [r for r in rows if r["section"] == ROOF]
    sp_f = R21.split(fl, _sec_diff(fsec))
    sp_r = R21.split(rf, _sec_diff(rsec))
    # the roof residual DIFFERS: split it (R-T626-1 (4)) into the engine chord tolerance on the +4.30 roof and the rest
    res = [r for r in rf if r["name"] == "RESIDUAL"][0]
    eng430 = D([x for x in I41.ENGINE_M2 if x["element"].startswith("1F-ROOF-AT220")][0]["qty"])
    chord430 = m["roof"]["ROOF-430"] - eng430
    proposal = R.split_residual(D(res["delta"]), [
        {"name": "engine arc discretisation of the +4.30 annex roof corner arc B2B (line L-d57d2dc2 55.559 vs own "
                 "exact-arc 55.560332)", "qty": str(chord430), "class": "TOLERANCE",
         "evidence": "READING: own ROOF-430 (T-321 handles, exact arc) - engine line; DRAWING_CONFIRMED"}])
    rem = D(proposal[-1]["qty"])
    rem_ev, rem_diff = R21.judge("READING", rem, expected=D(res["expected"]))
    tot_floor_own = sum((D(r["own"]) for r in room_table(drawn)), Z)
    return {
        "schema": "T626_ROW_EVIDENCE_V1", "rule": R.RULE_ID, "governing": R.GOVERNING,
        "statement": {"file": str(STATEMENT.relative_to(ROOT)), "sha256": STATEMENT_SHA, "sections": [FLOOR, ROOF]},
        "drawing": drawn["source"],
        "rows": rows,
        "split": {FLOOR: sp_f, ROOF: sp_r},
        "count": {"rows": len(rows), "by_evidence": _count(rows)},
        "room_table": room_table(drawn),
        "floor_own_total_m2": str(tot_floor_own),
        "upturn_boundary_check_lm": _boundary_check(drawn),
        "roof_fields_own_m2": {k: str(v) for k, v in m["roof"].items()},
        "roof_residual_proposal": {"row": "T-541/membrane RESIDUAL", "delta": res["delta"], "parts": proposal,
                                   "remainder_evidence": rem_ev, "remainder_expected_minus_delta": str(rem_diff)},
        "held": [{"row": r["name"], "delta": r["delta"], "lines": "L-3e8fe55da71851816dd4 / L-aac1f35e08f85b643692",
                  "waits_on": "Q-34 (top roof +13.90 has no roof plan)"} for r in rf if r["class"] == "HELD"],
    }


def _boundary_check(drawn):
    """own outline perimeters against the T-074 hand boundaries that the T-546 upturn (lm) table rests on: the faces
    that settle the floor rows also settle that basis (the doorway / open-edge segments stay as T-546 split them)."""
    own = hand = Z
    worst = ("", Z)
    for r in I46.ROOMS:
        if r[8] is None:
            continue
        p = D(drawn["rooms"][r[0]]["perimeter"])
        own, hand = own + p, hand + D(r[8])
        if (p - D(r[8])).copy_abs() > worst[1].copy_abs():
            worst = (r[0], p - D(r[8]))
    return {"rooms": 17, "own_perimeters_lm": str(R.q6(own)), "hand_boundaries_lm": str(hand),
            "difference_lm": str(R.q6(own - hand)), "largest_room_difference": [worst[0], str(R.q6(worst[1]))],
            "note": "pantry upturn HELD (open side, T-303 / T-310): not in the check"}


def _sec_diff(sec):
    return D(sec["difference"])


def _count(rows):
    c = {}
    for r in rows:
        c[r["evidence_status"]] = c.get(r["evidence_status"], 0) + 1
    return dict(sorted(c.items()))


def dumps(d) -> str:
    return json.dumps(d, indent=1, sort_keys=True, ensure_ascii=True) + "\n"


def render_md(d) -> str:
    L = ["# T-626 row evidence (generated by t626_alsenan.py; do not edit by hand)", "",
         f"Statement {d['statement']['file']} sha256 {d['statement']['sha256'][:12]}; drawing by Drive title only; "
         f"rule {d['rule']}. Evidence statuses: {d['count']['by_evidence']}.", "",
         "| section | row | class | delta (ref - engine) | kind | own / expected | check | evidence |", "|---|---|---|---|---|---|---|---|"]
    for r in d["rows"]:
        own = r.get("own") or r.get("expected")
        chk = r.get("own_minus_engine") or r.get("own_minus_abs_delta") or r.get("expected_minus_delta")
        L.append(f"| {r['section']} | {r['name'][:70]} | {r['class']} | {r['delta']} | {r['kind']} | {own} | {chk} | "
                 f"{r['evidence_status']} |")
    L += ["", "## Wet rooms: engine vs own outline vs printed second read", "",
          "| room | engine | own (chain) | own - engine | printed | printed - own | wet basis | his |", "|---|---|---|---|---|---|---|---|"]
    for t in d["room_table"]:
        L.append(f"| {t['room']} | {t['engine']} | {t['own']} | {t['own_minus_engine']} | {t['printed_second_read']} | "
                 f"{t['printed_minus_own']} | {t['wet_basis']} | {t['his']} |")
    b = d["upturn_boundary_check_lm"]
    L += ["", f"Upturn basis check (lm): own perimeters {b['own_perimeters_lm']} vs T-074 hand boundaries "
          f"{b['hand_boundaries_lm']}, difference {b['difference_lm']}; largest {b['largest_room_difference']}."]
    p = d["roof_residual_proposal"]
    L += ["", "## Roof residual split (PROPOSED)", "", f"Row delta {p['delta']} m2 ->"]
    for x in p["parts"]:
        L.append(f"- {x['class']} {x['qty']}: {x['name']}")
    L.append(f"- remainder evidence: {p['remainder_evidence']} (expected - delta {p['remainder_expected_minus_delta']})")
    return "\n".join(L) + "\n"
