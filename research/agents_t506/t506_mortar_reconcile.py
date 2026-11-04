"""T-506: BLACK-BLOCK LAYING MORTAR reconciliation (T-367 vs T-453 r2) + materials PRODUCER-ROLE map (F-C-T496-1).

Research reader, NOT wired: no candidate, engine, rule, knowledge or registry file changes; no candidate (V3.0.50) or
released (V2.9 + route G) line moves. Standard library only. Every villa; the development-villa run is main().

PHYSICAL ELEMENT (ERS s.2.1). The installed bed + head joint mortar of mortared black (cement) block walls: the wet
mortar that physically sits between the units of the masonry that is actually built, wall by wall, before any waste or
procurement term. Contract area (MAS.BLOCK m2), installed mortar (m3), materials (cement bags, loose sand) and
procurement (waste, purchase rounding) are four different quantities and are kept apart.

THE TWO LEDGERS (both merged, both Checker-verified on their own basis):
  T-367 MASONRY_JOINT_MORTAR_V1 (2026-10-30, V3.0.26): contract net m2 (openings deducted, Q-73) x joint geometry of the
        40 x 20 module (Q-75 decision 2026-10-23 + owner 2026-10-29 10 mm joint) for BOTH 0.15 and 0.20 m black walls.
  T-453 r2 (2026-11-03, V3.0.45): reads T-367's per-m2 rate, but on the MATERIAL BASE (contract net - every REQUIRED RC
        lintel face, R-T453-5) and only for the 0.20 m walls; 0.15 m HELD after the owner's Q-75 ANSWER of 2026-11-02
        (UPC-BLACK-BLOCK-001: 'the 0.15 m module is NOT stated', data item); a HELD lintel face makes the line a RANGE.

RULES (R-T506-n; provenance T-506; research rules, not rule-store versions):
  R-T506-1 RECONCILE IN UNITS  per wall: T-367 m3 = [material base m3] + [REQUIRED lintel face m3] and the material
           base m3 falls in exactly one bucket: PROVISIONAL-NET (0.20 m line computed), RANGE (0.20 m line with a HELD
           lintel face: low = base - held faces), HELD-0.15 (module not stated; figure beside, never 0). The sum over
           walls of every bucket must reproduce both ledgers' printed totals (residual 0 to 1e-6 m3) or the run stops.
  R-T506-2 GOVERNING LEDGER    the MATERIAL figure of black-block laying mortar (installed m3 -> cement bags, sand) is
           PRODUCED by T-453 r2 alone: (a) a lintel face is concrete, not laid block (Q-73 'only masonry that
           physically exists', R-T453-5); (b) the owner's 2026-11-02 Q-75 answer post-dates T-367's basis and states
           only the 0.20 m module; (c) Q-78 (1:4) now gives the mix T-367 held. T-367 is a READ input (the joint
           geometry per m2) and a BESIDE figure (0.15 m walls, contract-area basis); it is never wired as a second
           mortar figure. A B9-04 candidate line (T-372) carries T-453 r2's figures by line, the 0.15 m lines HELD with
           the T-367 figure beside, the F-T367-1 perimeter joints a separate HELD component.
  R-T506-3 ONE PRODUCER PER (line, material, kind)  every binding row carries a role: PRODUCER (derives the figure from
           its own inputs), READER (a declared read chain; its figure must equal the producer's), BESIDE (shown, never
           summed). A key with two PRODUCERS, or with a READER whose figure differs from its producer's, is refused.
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.agents_t367 import masonry_mortar_v1 as M  # noqa: E402  (joint geometry, independent of T-453)

SCHEMA = "URBAN_T506_MORTAR_RECONCILIATION_V1"
T367_WALLS = ROOT / "research/agents_t367/MORTAR_BY_WALL_T367.csv"
T453 = ROOT / "research/agents_t453/out/MATERIAL_LEDGER_T453.json"
T496 = ROOT / "research/agents_t496/out/BINDING_MAP_T496.json"
INDEX = ROOT / "research/agents_t483/out/LINE_INDEX_V3_0_50.json"
T367_SUMMARY = ROOT / "research/agents_t367/summary.json"
PINS = {T367_WALLS: "f658d79b9c44622ca684cebe3d2c73bebd9f5244e5c8dc188a558e1152de094b",
        T367_SUMMARY: "293f2f2b62900ba4a109478cbd483f3c4704c59656a55041eb04a81742ef43af",
        T453: "ad9bceee3bfdbc12218edec2a648e39104f3503bd73342c8ebb451b8394c13f9",
        T496: "270a13c46e74ef1f0167ba6b91b6320b1d3cb39edfa56be4b2d9418f41fe96b5",
        INDEX: "05de8b12e3352eadd805e6dc3ee240a9cdb1d42406c7fa017e8a331d41e69db2"}   # V3.0.50 d40c4ec5
TOL = 1e-6            # m3: the ledgers print 6 decimals
TOL_A = 5e-5          # m2: the candidate prints 4 decimals

PNET, RANGE, HELD015, LINTEL = "PROVISIONAL-NET", "RANGE-NET", "HELD-0.15-MODULE", "LINTEL-FACE-CONCRETE"
BUCKETS = (PNET, RANGE, HELD015, LINTEL)
CONFIRMED_T = (0.20,)    # UPC-BLACK-BLOCK-001 confirmed_modules_m (owner Q-75 answer 2026-11-02)
Q75_015 = ("owner Q-75 answer 2026-11-02 / UPC-BLACK-BLOCK-001: the 0.15 m black block installed module is NOT stated "
           "(block schedule / supplier data item): joint geometry, hence mortar, HELD; the T-367 40 x 20 figure beside")
PERIMETER_HELD = ("F-T367-1 (Checker 2026-10-30 09:58): perimeter joints at column faces and the soffit, bound "
                  "(L b + 2 H j) t per junction, about +5.5 .. +13.4 % on 4 walls (about 0.2 .. 0.5 m3): a physical "
                  "component in NEITHER ledger (T-453 r2 reads T-367's per-m2 rate): HELD by name, never 0, never "
                  "summed into the bed / head m3")

# R-T506-3 roles: (table, material, kind) -> role. Anything not listed is refused (a role is never guessed).
ROLE_RULES = {
    ("T-453", "MASONRY_UNITS", "units_nr"): "PRODUCER",
    ("T-453", "MASONRY_UNITS", "units_procurement_nr"): "PRODUCER",
    ("T-453", "MASONRY_LAYING", "laying_material"): "PRODUCER",
    ("T-453", "MASONRY_LAYING", "glue_kg"): "PRODUCER",
    ("T-453", "MASONRY_LAYING", "glue_bags_25kg_net"): "PRODUCER",
    ("T-453", "MASONRY_LAYING", "mortar_m3"): "PRODUCER",
    ("T-453", "MASONRY_LAYING", "cement_bags"): "PRODUCER",
    ("T-453", "MASONRY_LAYING", "sand_m3"): "PRODUCER",
    ("T-453", "LINTEL_RC", "concrete_m3"): "PRODUCER",
    # plaster: V1 (T-454) computes the installed mortar m3; V2 (T-489, UNWIRED_PRODUCER of the mix) reads it and
    # produces the cement / sand from the documented mix; V1's cement / sand rows (no mix) are superseded -> BESIDE
    ("T-454", "*", "mortar_m3"): "PRODUCER",
    ("T-489", "*", "mortar_m3"): "READER",
    ("T-454", "*", "cement_bags"): "BESIDE",
    ("T-454", "*", "sand_m3"): "BESIDE",
    ("T-489", "*", "cement_bags"): "PRODUCER",
    ("T-489", "*", "sand_m3"): "PRODUCER",
    ("T-455", "TILE_ADHESIVE", "adhesive_bags_20kg"): "PRODUCER",
    ("T-455", "TILE_UNITS", "tiles_nr"): "PRODUCER",
    ("T-495", "TILE_ADHESIVE", "adhesive_bags_20kg"): "PRODUCER",   # '@finish' options: alternatives, never summed
    ("T-495", "TILE_BED_MORTAR", "bed_mortar_m3"): "PRODUCER",
    ("T-367", "MASONRY_LAYING", "mortar_m3"): "BESIDE",               # R-T506-2: read input / beside, never wired
}
READS_FROM = {("T-489", "mortar_m3"): "T-454"}


class ReconcileError(ValueError):
    pass


def _r(x, n=6):
    return None if x is None else round(x + 0.0, n)


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def rate(t_m):
    """joint mortar m3 per m2 of wall face of the 40 x 20 module (T-367 geometry, re-derived here)."""
    return M.per_m2(M.MODULE_BLACK, t_m)["total"]


# ------------------------------------------------------------------------------------------- R-T506-1 reconcile
def t453_lines(ledger):
    """T-453 r2 black LAYING_MATERIAL rows -> {line_id: row}."""
    out = {}
    for m in ledger["block_materials"]:
        if m["item"] == "LAYING_MATERIAL" and m.get("material_type") == "BLACK":
            if m["line_id"] in out:
                raise ReconcileError(f"{m['line_id']}: two T-453 mortar rows")
            out[m["line_id"]] = m
    return out


def wall_rows(t367_walls, t453_by_line, index_lines=None):
    """T-367 established black walls x T-453 r2 line state -> one reconciliation row per wall (R-T506-1)."""
    rows, held = [], []
    seen = set()
    for w in t367_walls:
        if w["block_type"] != "BLACK":
            continue
        key = (w["floor"], w["wall_id"])
        if key in seen:
            raise ReconcileError(f"wall {key} twice in the T-367 ledger")
        seen.add(key)
        lid = (w.get("part_line_id_v3026") or "").strip()
        if w["mortar_installed_m3"].strip() == "":
            if w["area_m2"].strip():
                raise ReconcileError(f"{w['wall_id']}: a held wall carries an area")
            held.append({"floor": w["floor"], "wall_id": w["wall_id"], "kind": w["kind"], "t_m": float(w["t_m"]),
                         "state": "HELD IN BOTH LEDGERS (no established area): blank by name, never 0"})
            continue
        t, a, m3 = float(w["t_m"]), float(w["area_m2"]), float(w["mortar_installed_m3"])
        r = rate(t)
        if abs(a * r - m3) > TOL:
            raise ReconcileError(f"{w['wall_id']}: T-367 {m3} != area {a} x {r:.7f} (joint geometry)")
        ln = t453_by_line.get(lid)
        if ln is None:
            raise ReconcileError(f"{w['wall_id']}: line {lid!r} has no T-453 r2 mortar row")
        if index_lines is not None:
            c = index_lines.get(lid)
            if c is None or c["class"] == "HELD" or abs(c["measured_net"] - ln["net_m2"]) > TOL_A:
                raise ReconcileError(f"{lid}: not the same released net in the current candidate")
        req = [x for x in ln.get("lintel_deductions", []) if x["host"] == w["wall_id"]]
        hld = [x for x in ln.get("lintel_held_faces", []) if x["host"] == w["wall_id"]]
        if any(x.get("face_max_m2") is None for x in hld):
            raise ReconcileError(f"{w['wall_id']}: an unbounded held lintel face (the line is HELD, not a range)")
        req_m2 = _r(sum(x["face_m2"] for x in req))
        hld_m2 = _r(sum(x["face_max_m2"] for x in hld))
        if req_m2 > a + TOL_A:
            raise ReconcileError(f"{w['wall_id']}: lintel faces {req_m2} exceed the wall area {a}")
        base = a - req_m2
        row = {"floor": w["floor"], "wall_id": w["wall_id"], "kind": w["kind"], "t_m": t, "line_id": lid,
               "area_status": w["area_status"], "contract_m2": a, "t367_m3": m3, "rate_m3_per_m2": _r(r, 8),
               "required_lintels": [x["opening_id"] for x in req], "required_face_m2": req_m2,
               "lintel_face_m3": _r(req_m2 * r), "held_lintels": [x["opening_id"] for x in hld],
               "held_face_max_m2": hld_m2, "material_base_m2": _r(base), "t453_line_status": ln["status"]}
        if t not in CONFIRMED_T:
            if ln["status"] != "HELD":
                raise ReconcileError(f"{lid}: a 0.15 m black line released by T-453 (module not stated)")
            row.update(bucket=HELD015, governing_m3=None, beside_m3=_r(base * r),
                       beside_low_m3=_r((base - hld_m2) * r), why=Q75_015)
        elif ln["status"] == "COMPUTED":
            if hld:
                raise ReconcileError(f"{w['wall_id']}: held lintel on a COMPUTED line")
            row.update(bucket=PNET, governing_m3=_r(base * r), why="T-453 r2 R-T453-3 / R-T453-5")
        elif ln["status"] == "RANGE":
            row.update(bucket=RANGE, governing_m3=None, governing_range_m3=[_r((base - hld_m2) * r), _r(base * r)],
                       why=f"held lintel face(s) {', '.join(row['held_lintels']) or 'on another wall of the line'} "
                           "0 .. face (R-T453-5): a named range, never a point figure")
        else:
            raise ReconcileError(f"{lid}: 0.20 m line state {ln['status']!r} not COMPUTED / RANGE")
        rows.append(row)
    return rows, held


def totals(rows):
    t = {"t367_m3": _r(sum(r["t367_m3"] for r in rows)), "contract_m2": _r(sum(r["contract_m2"] for r in rows))}
    for b in BUCKETS:
        t[b] = {"m3": 0.0, "m2": 0.0, "walls": 0}
    for r in rows:
        k = r["bucket"]
        t[k]["walls"] += 1
        t[k]["m2"] += r["material_base_m2"]
        if k == PNET:
            t[k]["m3"] += r["governing_m3"]
        elif k == RANGE:
            t[k].setdefault("low_m3", 0.0)
            t[k]["low_m3"] += r["governing_range_m3"][0]
            t[k]["m3"] += r["governing_range_m3"][1]
        else:
            t[k].setdefault("low_m3", 0.0)
            t[k]["low_m3"] += r["beside_low_m3"]
            t[k]["m3"] += r["beside_m3"]
        t[LINTEL]["m3"] += r["lintel_face_m3"]
        t[LINTEL]["m2"] += r["required_face_m2"]
        t[LINTEL]["walls"] += 1 if r["required_lintels"] else 0
    for b in BUCKETS:
        for k in ("m3", "m2", "low_m3"):
            if k in t[b]:
                t[b][k] = _r(t[b][k])
    # the lintel faces carried by the 0.15 m walls vs the 0.20 m walls (both T-367 contract-basis m3)
    t["lintel_face_m3_by_t"] = {f"{tt:.2f}": _r(sum(r["lintel_face_m3"] for r in rows if r["t_m"] == tt))
                                for tt in sorted({r["t_m"] for r in rows})}
    t["residual_m3"] = _r(t["t367_m3"] - t[PNET]["m3"] - t[RANGE]["m3"] - t[HELD015]["m3"] - t[LINTEL]["m3"])
    if abs(t["residual_m3"]) > 1e-5:
        raise ReconcileError(f"unnamed residual {t['residual_m3']} m3 (R-T506-1)")
    return t


def check_against_ledgers(tot, t453_ledger, t367_total):
    """the wall buckets must reproduce both ledgers' printed totals."""
    mt = t453_ledger["mortar"]
    pn, rg = mt["black_0_20_provisional_net"], mt["range_net"]
    out = {"t367_printed_m3": t367_total, "t453_pnet_printed_m3": pn["m3"],
           "t453_range_printed_m3": rg.get("m3")}
    if abs(tot["t367_m3"] - t367_total) > 1e-5:
        raise ReconcileError(f"walls sum {tot['t367_m3']} != T-367 printed {t367_total}")
    if abs(tot[PNET]["m3"] - pn["m3"]) > 1e-5:
        raise ReconcileError(f"PROVISIONAL-NET {tot[PNET]['m3']} != T-453 printed {pn['m3']}")
    if rg.get("m3"):
        if abs(tot[RANGE]["low_m3"] - rg["m3"][0]) > 1e-5 or abs(tot[RANGE]["m3"] - rg["m3"][1]) > 1e-5:
            raise ReconcileError(f"RANGE {tot[RANGE]} != T-453 printed {rg['m3']}")
    out["agree"] = True
    return out


def t453_015_beside(t453_by_line):
    """T-453 prints the 0.15 m figure beside on the CONTRACT net; the reconciliation states it on the material base."""
    return _r(sum(m["beside_t367_40x20"]["mortar_installed_m3"] for m in t453_by_line.values()
                  if m["thickness_m"] == 0.15 and m.get("beside_t367_40x20")))


# ------------------------------------------------------------------------------------------- R-T506-3 roles
def role_of(b):
    kind = b["kind"].split("@")[0]
    for key in ((b["table"], b["material"], kind), (b["table"], "*", kind)):
        if key in ROLE_RULES:
            return ROLE_RULES[key]
    raise ReconcileError(f"no producer role declared for {b['table']} {b['material']} {b['kind']} (never guessed)")


def _carries(b):
    return not (b.get("value") is None and b.get("bound") is None and b.get("estimate_beside") is None)


def producer_census(bindings):
    """role on every binding row; census of (line, material, kind) keys: producers per key, reader agreement."""
    keyed = defaultdict(list)
    roles = []
    for b in bindings:
        role = role_of(b)
        roles.append(dict(b, role=role))
        if b.get("line_id") is None or b.get("stage") == "NO_CANDIDATE_LINE":
            continue
        keyed[(b["line_id"], b["material"], b["kind"].split("@")[0])].append(dict(b, role=role))
    two, diverge, multi = [], [], 0
    for key, lst in sorted(keyed.items()):
        prods = [b for b in lst if b["role"] == "PRODUCER"]
        ptabs = sorted({b["table"] for b in prods})
        if len({b["table"] for b in lst}) > 1:
            multi += 1
        if len(ptabs) > 1:
            two.append({"key": "|".join(key), "producers": ptabs})
        for rd in (b for b in lst if b["role"] == "READER"):
            src = READS_FROM.get((rd["table"], key[2]))
            pv = [b for b in prods if b["table"] == src]
            if not pv:
                if _carries(rd):
                    diverge.append({"key": "|".join(key), "reader": rd["table"], "why": "reader with no producer"})
                continue
            a = [rd.get("value"), rd.get("bound"), rd.get("estimate_beside")]
            p = [pv[0].get("value"), pv[0].get("bound"), pv[0].get("estimate_beside")]
            if a != p:
                diverge.append({"key": "|".join(key), "reader": rd["table"], "producer": src, "reader_value": a,
                                "producer_value": p})
    from collections import Counter
    c = Counter((b["table"], b["role"]) for b in roles)
    summable = [b for b in roles if b["role"] == "PRODUCER" and _carries(b)]
    return {"rows": len(roles), "roles": {f"{k[0]}|{k[1]}": v for k, v in sorted(c.items())},
            "keys": len(keyed), "keys_bound_by_two_tables": multi, "keys_with_two_producers": two,
            "reader_divergences": diverge, "summable_rows": len(summable)}, roles


def t367_bindings(t367_walls):
    """T-367 per part line as bindings (role BESIDE): what a wiring of 3.870113 m3 beside T-453 would add."""
    acc = defaultdict(float)
    for w in t367_walls:
        lid = (w.get("part_line_id_v3026") or "").strip()
        if w["block_type"] == "BLACK" and lid.startswith("L-") and w["mortar_installed_m3"].strip():
            acc[lid] += float(w["mortar_installed_m3"])
    return [{"table": "T-367", "row": f"MORTAR|{k}", "line_id": k, "material": "MASONRY_LAYING", "kind": "mortar_m3",
             "value": _r(v), "bound": None, "estimate_beside": None, "stage": "INSTALLED"} for k, v in sorted(acc.items())]


# ------------------------------------------------------------------------------------------- build
def build_from(t367_walls, t453_ledger, bindings, index_lines=None, t367_total=None):
    by = t453_lines(t453_ledger)
    rows, held = wall_rows(t367_walls, by, index_lines)
    tot = totals(rows)
    chk = check_against_ledgers(tot, t453_ledger, tot["t367_m3"] if t367_total is None else t367_total)
    census, roles = producer_census(list(bindings) + t367_bindings(t367_walls))
    if census["keys_with_two_producers"] or census["reader_divergences"]:
        raise ReconcileError(f"R-T506-3: {census['keys_with_two_producers'][:3]} {census['reader_divergences'][:3]}")
    return {"schema": SCHEMA, "rows": rows, "held_walls": held, "totals": tot, "ledger_check": chk,
            "t453_015_beside_on_contract_net_m3": t453_015_beside(by),
            "perimeter_joints": PERIMETER_HELD, "governing": GOVERNING, "producer_census": census,
            "released_quantities_changed": 0}, roles


GOVERNING = {
    "rule": "R-T506-2",
    "material_line_producer": "T-453 r2 (research/agents_t453, merged b16f686b; T-496 binding): installed m3 on the "
                              "material base, cement bags / loose sand by UPC-BLACK-MORTAR-001 (Q-78 1:4)",
    "t367_role": "READ input (joint geometry per m2 of the 40 x 20 module, 10 mm owner-provisional) + BESIDE figure for "
                 "the 0.15 m walls and the contract-area basis; never a second wired mortar figure",
    "t372_narrowed_to": "a B9-04 line per MAS.BLOCK part line carrying T-453 r2's figure for that line (COMPUTED / "
                        "RANGE), the 0.15 m lines HELD with the T-367 figure beside, F-T367-1 perimeter joints a "
                        "separate HELD component, cement / sand produced once (T-453 r2 or the B9-04 line, never both: "
                        "R-T496-4 cross-trade)",
    "why": ["Q-73 / R-T453-5: an RC lintel face is concrete, not laid block: T-367's contract-area basis carries "
            "mortar where no joint exists",
            "owner Q-75 answer 2026-11-02 (UPC-BLACK-BLOCK-001) post-dates T-367 (2026-10-30) and confirms the 40 x 20 "
            "module for 0.20 m only",
            "Q-78 (owner 2026-11-02) gives the 1:4 mix T-367 held: T-453 r2 already applies it"],
}


def load_inputs():
    pins = {}
    for p, h in PINS.items():
        got = _sha(p)
        if got != h:
            raise ReconcileError(f"{p.relative_to(ROOT)}: sha256 {got[:8]} is not the pinned {h[:8]}")
        pins[str(p.relative_to(ROOT))] = got
    walls = list(csv.DictReader(T367_WALLS.open(encoding="utf-8", newline="")))
    t453 = json.loads(T453.read_text(encoding="utf-8"))
    t496 = json.loads(T496.read_text(encoding="utf-8"))
    idx = json.loads(INDEX.read_text(encoding="utf-8"))
    lines = {ln["line_id"]: ln for ln in idx["lines"] if ln["item_code"] == "MAS.BLOCK"}
    t367_total = json.loads(T367_SUMMARY.read_text(encoding="utf-8"))["black_mortar_m3"]
    if t496.get("failures"):
        raise ReconcileError("the T-496 binding map carries failures: not a basis for a role census")
    return walls, t453, t496["bindings"], lines, idx["candidate_version"], pins, t367_total


def build():
    walls, t453, bs, lines, ver, pins, t367_total = load_inputs()
    out, roles = build_from(walls, t453, bs, lines, t367_total=t367_total)
    out["candidate_checked"] = ver
    out["inputs"] = pins
    return out, roles


def write(out, roles, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "RECONCILIATION_T506.json").write_text(
        json.dumps(out, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    cols = ["floor", "t_m", "wall_id", "kind", "line_id", "area_status", "contract_m2", "t367_m3", "required_lintels",
            "required_face_m2", "lintel_face_m3", "held_lintels", "held_face_max_m2", "material_base_m2", "bucket",
            "governing_m3", "governing_range_m3", "beside_m3", "beside_low_m3", "t453_line_status"]
    with (out_dir / "MORTAR_RECONCILIATION_T506.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        for r in sorted(out["rows"], key=lambda r: (r["floor"], r["t_m"], r["wall_id"])):
            w.writerow({k: (" ".join(v) if isinstance(v, list) and all(isinstance(x, str) for x in v) else
                            json.dumps(v) if isinstance(v, list) else ("" if v is None else v))
                        for k, v in r.items()})
    with (out_dir / "PRODUCER_ROLES_T506.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["table", "row", "line_id", "material", "kind", "role"])
        for b in sorted(roles, key=lambda b: (b["table"], b["row"], b["kind"])):
            w.writerow([b["table"], b["row"], b["line_id"] or "", b["material"], b["kind"], b["role"]])


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    out, roles = build()
    write(out, roles, argv[0] if argv else HERE / "out")
    t = out["totals"]
    print(json.dumps({"totals": t, "ledger_check": out["ledger_check"],
                      "t453_015_beside_on_contract_net_m3": out["t453_015_beside_on_contract_net_m3"],
                      "producer_census": out["producer_census"]}, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
