"""T-496: the MATERIALS BINDING MAP of the Checker-verified material tables onto the candidate of record
ARCH_TAKEOFF_V3.0.47 (e86a53a8), and the CHECK that guards any later wiring. Research reader, not wired: no candidate,
engine, rule, knowledge or registry file changes and no candidate or released (V2.9 + route G) line moves.

Physical element. A material row is the material of ONE installed element (a masonry panel, a plastered face, a tiled
surface); the candidate line is that element's measured quantity. The binding says which line a row reads, which
material and which quantity kind (count, kg, bags, m3, cement, sand) it produces, at which stage (theoretical,
installed, procurement / purchasing group), and what its status is. A material is labelled from its weakest input:
the bound line's class wins over the rate (a HELD line never yields a number; a candidate held range may yield a
BOUND only, never a figure).

Tables read (committed outputs, sha256-pinned, never edited; ids, codes, units and quantities only):
  T-453 r2  research/agents_t453/out/MATERIAL_LEDGER_T453.json   blockwork: units, AAC glue, black mortar, RC lintels
  T-454     research/agents_t454/out/PLASTER_MATERIALS_T454.json PLASTER_MATERIALS_TABLE_V1: coat mortar m3
  T-489     research/agents_t489/out/PLASTER_MIX_T489.json       PLASTER_MATERIALS_TABLE_V2: cement / sand (reads V1)
  T-455     research/agents_t455/out/TILE_PURCHASE_T455.json     FINISH_MATERIALS_TABLE_V4: adhesive bags, tile boxes
  T-495     research/agents_t495/out/TILE_PURCHASE_LEDGER_V2.json the finish-HELD outdoor rows (supersedes T-455 V1
            schema for those rows only; its T-455 re-run on V3.0.46 is a READ that must equal T-455)
Candidate (pinned):
  research/agents_t485/out/LINE_INDEX_V3_0_46.json (the V3.0.46 line index, BOQ_LINES 35d70129) + the T-443 change set
  research/agents_t443/summary_t443.json (V3.0.46 35d70129 -> V3.0.47 e86a53a8: 2 replaced + 7 added FIN.SKIRTING
  lines, 4865 byte-identical). A bound line in that change set would be STALE_AT_V3047 (none is).

Rules (R-T496-n):
  R-T496-1 PRESENCE    every bound line id exists in the candidate, with unit m2, and the table's read (class,
           net or held range) equals the candidate's line; otherwise ABSENT_LINE / UNIT / STALE_INPUT.
  R-T496-2 HELD STAYS HELD   a bound line of class HELD (or a row the table marks HELD) yields no FIGURE; a BOUND is
           allowed only where the candidate prints the held range (held_low / held_high); an EXCLUDED line yields
           nothing. A purchasing group with any held member prints no 'to buy' figure.
  R-T496-3 ONE PRODUCER   a (line, material, quantity kind) is produced by exactly one table; a declared READ chain
           (T-489 reads T-454 mortar m3; T-495 re-runs T-455) must reproduce the producer's value exactly
           (CHAIN_DIVERGES otherwise); any other second binding is DOUBLE_BOUND.
  R-T496-4 CROSS-TRADE    a candidate line that is itself a material layer (tile bed FIN.FLOOR.BED.*, spatter,
           masonry mortar, lintel) on a host element excludes the same material bound by a table on that host's
           surface line (host = element id minus its trailing trade suffix); otherwise CROSS_TRADE_DOUBLE.
  R-T496-5 SCOPE         every candidate line of an item code a table declares in scope is read by that table, or is
           listed in KNOWN_GAPS with its reason (SCOPE_LINE_UNREAD otherwise): a line no table reads is never 0.
  R-T496-6 OWNER ARITHMETIC   each figure is re-derived from the owner rules (AGENT_BRIEF): 12.5 black blocks / m2;
           AAC glue 3.5 / 4.5 kg/m2, 25 kg bag; black mortar 1:4 = 8 bags + 1.1 m3 sand per m3; adhesive 5 / 3 / 3 m2
           per 20 kg bag; and per row from the table's own stated inputs (thickness, mortar per m2, lintel face);
           a difference over 1e-6 relative is ARITHMETIC.

    python3 -I research/agents_t496/t496_binding_map.py [OUT_DIR]   # writes BINDING_MAP_T496.json / .csv (./out)
    python3 -I research/agents_t496/t496_binding_map.py --check     # exit 1 on any failure, prints them
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent

SCHEMA = "URBAN_T496_MATERIAL_BINDING_MAP_V1"
CANDIDATE = "ARCH_TAKEOFF_V3.0.47"
CANDIDATE_SHA = "e86a53a8981725d6247039419325f2242316c45056c8d747aca56df5c88c2f58"
BASE_SHA = "35d70129d8bf59b4c0f874a11edeacca26f45a51001b03a4d6ca57e3942546a4"

INDEX = ROOT / "research/agents_t485/out/LINE_INDEX_V3_0_46.json"
T443 = ROOT / "research/agents_t443/summary_t443.json"
T453 = ROOT / "research/agents_t453/out/MATERIAL_LEDGER_T453.json"
T454 = ROOT / "research/agents_t454/out/PLASTER_MATERIALS_T454.json"
T489 = ROOT / "research/agents_t489/out/PLASTER_MIX_T489.json"
T455 = ROOT / "research/agents_t455/out/TILE_PURCHASE_T455.json"
T495 = ROOT / "research/agents_t495/out/TILE_PURCHASE_LEDGER_V2.json"
PINS = {INDEX: "d9e0a7e46b2e17a1cef78d8630cf2b1f6c2aa8bbe5dbe0f29037e6f1e54f2dd0",
        T443: "bdf1c5956cc5200e142aca09b1aad72933e93060b8a9610f6f1f9198624799c5",
        T453: "ad9bceee3bfdbc12218edec2a648e39104f3503bd73342c8ebb451b8394c13f9",
        T454: "dd144416850ca735e114a7c6ee3d56fbcdc3e41eacc89bea9297fb3af4a57f66",
        T489: "f04659307895198813cc378462dc14e68d98865ff58b8415def74d158fa173f7",
        T455: "30f3c90eeee907b9e531d73c9e43f3ec8dae8d249a4151963046c48e0ec9bed8",
        T495: "56aa1813c08ff738c496a4189b896af47a383a816ea55527eae2b1fd4ff5b94d"}

TOL_Q = 5e-5          # m2: the candidate prints 4-6 decimals
TOL_REL = 1e-6
TOL_ABS = 1e-5        # the tables print 6 decimals and derive bags / sand from a rounded m3: x 8 keeps it under 1e-5

# Owner rules (AGENT_BRIEF 'OWNER CONFIRMED rules'; the tables cite the same rulebook records)
BLACK_PER_M2 = 12.5                       # Q-75, UPC-BLACK-BLOCK-001 (40 x 20 module, black 0.20 m)
GLUE_KG_M2 = {0.15: 3.5, 0.2: 4.5}        # UPC-AAC-GLUE-001, owner 2026-11-02
GLUE_BAG_KG = 25.0
MORTAR_BAGS_M3, MORTAR_SAND_M3 = 8.0, 1.1  # Q-78 1:4
ADHESIVE_M2_PER_BAG = (5.0, 3.0)          # Q-45 / UPC-ADHESIVE-001: 5 (normal incl. 60x60) .. 3 (120x60, 160x80)
LINTEL_BEARING_M = 0.40                   # printed project LINTEL SCHEDULE (T-453 R-T453-4)

# Item codes each table declares in scope (from the tables' own census / scope text).
SCOPE = {
    "T-453": ("MAS.BLOCK",),
    "T-454": ("FIN.PLASTER", "EXT.FENCE.PLASTER"),
    "T-455": ("FIN.FLOOR.PORCELAIN", "FIN.FLOOR.WET_TILE", "FIN.WALL.TILE", "FIN.FLOOR.FINISH_HELD",
              "EXT.FLOOR.PORCELAIN"),
    "T-495": ("EXT.FLOOR.OUTDOOR",),
}
# Lines in a scope that no table reads, with why (R-T496-5). A wiring row must carry them HELD, never 0.
KNOWN_GAPS = {
    "L-7503af7cc1eea4e6735d": "MAS.BLOCK added at V3.0.46 (T-419 house below-ground masonry, HOUSE_BELOW_NG:MAIN_S), "
                              "HELD in the candidate; T-453 r2 was built on V3.0.45 and does not read it: its units / "
                              "glue or mortar are HELD and it joins the HELD members of the PROJECT glue group",
    "L-ee857398614d817e6917": "MAS.BLOCK added at V3.0.46 (T-419, HOUSE_BELOW_NG:ANNEX_S), HELD; as above",
}
# Candidate item codes outside every table, named so they are not silently dropped (material families with no table).
NOT_IN_ANY_TABLE = {
    "FIN.FLOOR.BED.DRY": "tile bed (Q-45 1:4, 3-4 cm) is its own candidate line; its mortar / cement / sand material "
                         "has no verified table yet",
    "FIN.FLOOR.BED.WET": "wet-floor tile bed (Q-45 1:4, 4-6 cm); as above",
    "EXT.PAVING.INTERLOCK": "declared out by T-495 (no owner material rule for pavers or their sand bed)",
    "FIN.EXT.FINISH": "facade finish system: T-454 not in scope (T-162 / B4 exterior rows)",
    "FIN.STAIR.SOFFIT": "stair soffit finish: T-454 not in scope (B7 stair rows)",
}
# R-T496-4: candidate codes that are themselves a material layer on a host element.
LAYER_CODES = ((re.compile(r"^FIN\.FLOOR\.BED\."), "TILE_BED_MORTAR"),
               (re.compile(r"SPATTER"), "BOND_COAT"),
               (re.compile(r"^MAS\.MORTAR"), "MASONRY_LAYING"),
               (re.compile(r"LINTEL"), "LINTEL_RC"))
TRADE_SUFFIX = re.compile(r":(bed|spatter|plaster|mortar|lintel)$")

# Declared READ chains (R-T496-3): (reader, producer) for a quantity kind.
READS = {("T-489", "T-454"): ("mortar_m3",)}   # T-495's T-455 re-run is compared whole (check_chain_tables)

FAIL_KINDS = ("PIN", "ABSENT_LINE", "UNIT", "STALE_INPUT", "STALE_AT_V3047", "HELD_YIELDS_FIGURE",
              "UNSOURCED_BOUND", "GROUP_HELD_FIGURE", "DOUBLE_BOUND", "CHAIN_DIVERGES", "CROSS_TRADE_DOUBLE",
              "SCOPE_LINE_UNREAD", "ARITHMETIC", "ZERO_SUBTOTAL")


class MapError(ValueError):
    pass


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _load(p, pins=True):
    p = Path(p)
    if pins and p in PINS and _sha(p) != PINS[p]:
        raise MapError(f"PIN: {p.name} sha256 {_sha(p)[:8]} is not the pinned {PINS[p][:8]}")
    return json.loads(p.read_text(encoding="utf-8"))


def _near(a, b, tol=TOL_Q):
    if a is None or b is None:
        return a is None and b is None
    return abs(a - b) <= tol


def _rel(a, b):
    return abs(a - b) <= max(TOL_REL * max(abs(a), abs(b)), TOL_ABS)


def _host(eid):
    return TRADE_SUFFIX.sub("", eid or "")


# --------------------------------------------------------------------------------------------- candidate V3.0.47
def candidate_v3047(index, t443):
    """The V3.0.47 view: the V3.0.46 index plus the T-443 change set (ids only; every changed line is FIN.SKIRTING)."""
    if index["inputs"]["lines"] != t443["base_sha256"]:
        raise MapError("PIN: the T-443 change set is not on the indexed V3.0.46 lines")
    if t443["candidate_sha256"] != CANDIDATE_SHA or t443["method"] != CANDIDATE:
        raise MapError("PIN: T-443 summary is not the candidate of record V3.0.47 e86a53a8")
    lines = {ln["line_id"]: dict(ln) for ln in index["lines"]}
    changed = {r["line_id"] for r in t443["rows"]} | set(t443["parents"])
    added = {r["line_id"] for r in t443["rows"] if r.get("change") == "ADD"}
    n = t443["lines"]
    if len(lines) != n["base"] or len(lines) + n["added"] != n["v3_0_47"] or len(added - set(lines)) != n["added"]:
        raise MapError("PIN: line counts of V3.0.46 + T-443 do not give V3.0.47")
    for lid in added:
        lines[lid] = {"line_id": lid, "item_code": "FIN.SKIRTING", "unit": "lm", "class": "T443_ADDED",
                      "element_id": None, "measured_net": None, "held_low": None, "held_high": None}
    return {"lines": lines, "changed": changed, "version": CANDIDATE, "sha256": CANDIDATE_SHA}


# --------------------------------------------------------------------------------------------- bindings per table
def _b(table, row, line_id, material, kind, value=None, bound=None, stage="THEORETICAL", status=None, group=None,
       read=None, note=None, estimate=None):
    return {"table": table, "row": row, "line_id": line_id, "material": material, "kind": kind, "value": value,
            "bound": bound, "stage": stage, "status": status, "group": group, "read": read or {}, "note": note,
            "estimate_beside": estimate}


def bind_t453(d):
    out, base = [], {}
    for s in d["source_lines"]:
        base[s["line_id"]] = s
    for r in d["block_materials"]:
        lid, held = r["line_id"], r["status"] == "HELD"
        read = {"class_read": "HELD" if base[lid]["class"] == "HELD" else base[lid]["class"],
                "net_read": base[lid]["net_m2"], "unit_read": "m2"}
        row = f"{r['item']}|{lid}"
        if r["item"] == "BLOCK_COUNT":
            out.append(_b("T-453", row, lid, "MASONRY_UNITS", "units_nr", r.get("theoretical_count"),
                          r.get("theoretical_count_range"), status=r["label"], read=read,
                          note=r.get("why") or r.get("procurement_why")))
            if r.get("procurement_count") is not None:
                out.append(_b("T-453", row, lid, "MASONRY_UNITS", "units_procurement_nr", r["procurement_count"],
                              stage="PROCUREMENT", status=r["label"], read=read))
            continue
        mt = r.get("material_type")
        if held or mt is None:
            out.append(_b("T-453", row, lid, "MASONRY_LAYING", "laying_material", None, None, status="HELD",
                          group="PROJECT" if mt != "BLACK" else None, read=read, note=r.get("why")))
            continue
        if mt == "WHITE":
            out.append(_b("T-453", row, lid, "MASONRY_LAYING", "glue_kg", r.get("consumption_kg"),
                          r.get("consumption_kg_range"), status=r["label"], group="PROJECT", read=read))
            out.append(_b("T-453", row, lid, "MASONRY_LAYING", "glue_bags_25kg_net", r.get("bags_25kg_net"),
                          r.get("bags_25kg_net_range"), status=r["label"], group="PROJECT", read=read))
        else:
            for k_out, k in (("mortar_m3", "mortar_installed_m3"), ("cement_bags", "cement_bags"),
                             ("sand_m3", "sand_m3_loose")):
                out.append(_b("T-453", row, lid, "MASONRY_LAYING", k_out, r.get(k), r.get(k + "_range"),
                              stage="INSTALLED" if k_out == "mortar_m3" else "THEORETICAL", status=r["label"],
                              read=read))
    hosts = {}
    for rec in d["reconciliation"]:
        for w in rec["walls"]:
            hosts[w] = rec["line_id"]
    for lt in d["lintels"]:
        lid = hosts.get(lt["host"])
        out.append(_b("T-453", f"LINTEL|{lt['opening_id']}", lid, "LINTEL_RC", "concrete_m3", lt.get("concrete_m3"),
                      stage="NO_CANDIDATE_LINE", status=lt["decision"],
                      read={"host_wall": lt["host"], "line_on_host": lid, "class_read": "LINTEL"},
                      note="B9-02 has no candidate line (T-487 wires it); the face is deducted from the host's "
                           "masonry material base (R-T453-5), never from the MAS.BLOCK contract line"
                           + ("" if lid else "; host wall sits on a HELD MAS.BLOCK line (not split per wall): no "
                                             "host line id, nothing deducted (material already HELD)")))
    return out


def _layers(table, d, stage_kinds):
    out = []
    for r in d["table"]["rows"]:
        read = {"class_read": r["line_class"], "net_read": r["area_m2"], "unit_read": "m2",
                "held_read": [r["held_low"], r["held_high"]]}
        for L in r["layers"]:
            for kind, key, bkey in stage_kinds:
                v = L.get(key)
                bound = L.get(bkey) if bkey else None
                if bkey == "mortar_m3_at_least" and L.get(bkey) is not None:
                    bound = [L[bkey], None]
                if bound is None and L.get("mortar_m3_bound_beside") is not None and kind == "mortar_m3":
                    bound = L["mortar_m3_bound_beside"]
                status, est = L.get("s5_status") or L.get("label"), None
                if L.get("thickness_basis") == "ENGINEERING ESTIMATE" and v is not None:
                    # R-T496-2 / WORKFLOW_CONTROLS s.5 (F-C-T454-1): a level-4 thickness gives an estimate BESIDE a
                    # HELD figure, whichever label the table printed (T-454 ESTIMATED-NET, T-489 s5 HELD agree here)
                    status, est, v = "HELD (s.5: level-4 thickness, estimate beside)", v, None
                out.append(_b(table, f"{r['id']}|{L['layer']}", r["id"], L["layer"], kind, v, bound,
                              stage="INSTALLED" if kind == "mortar_m3" else "THEORETICAL",
                              status=status, read=read, note=L.get("thickness_m"), estimate=est))
    return out


def bind_t454(d):
    return _layers("T-454", d, (("mortar_m3", "mortar_m3", "mortar_m3_at_least"),
                                ("cement_bags", "cement_bags", None), ("sand_m3", "sand_m3", None)))


def bind_t489(d):
    return _layers("T-489", d, (("mortar_m3", "mortar_m3", "mortar_m3_at_least"),
                                ("cement_bags", "cement_bags", "cement_bags_at_least"),
                                ("sand_m3", "sand_m3", "sand_m3_at_least")))


def bind_t455(d, table="T-455"):
    out = []
    for r in d["rows"]:
        read = {"class_read": "HELD" if r["status"] == "HELD" else r["status"], "net_read": r["area_m2"],
                "unit_read": "m2"}
        bb = r.get("adhesive_bound_bags")
        out.append(_b(table, f"ADH|{r['id']}", r["id"], "TILE_ADHESIVE", "adhesive_bags_20kg", r["adhesive_bags"],
                      [bb["low"], bb["high"]] if bb else None, status=r["adhesive_status"], group="PROJECT",
                      read=read, note=r.get("adhesive_reason")))
        out.append(_b(table, f"TILE|{r['id']}", r["id"], "TILE_UNITS", "tiles_nr", r.get("tiles_conservative"),
                      stage="THEORETICAL", status="HELD" if r.get("tiles_conservative") is None else "COMPUTED",
                      group=r.get("tile_product"), read=read, note=r.get("tiles_reason")))
    return out


def bind_t495(d):
    out = []
    for r in d["finish_held_rows"]:
        read = {"class_read": "HELD", "net_read": r["area_m2"], "unit_read": "m2",
                "held_read": [r["area_held_low_m2"], r["area_held_high_m2"]]}
        for o in r["options"]:
            a, bed = o.get("adhesive_bags_20kg"), o.get("bed")
            out.append(_b("T-495", f"ADH|{r['id']}|{o['finish']}", r["id"], "TILE_ADHESIVE",
                          f"adhesive_bags_20kg@{o['finish']}", None, [a["low"], a["high"]] if a else None,
                          status=o["status"], group="PROJECT", read=read,
                          note="finish option, never summed across options"))
            out.append(_b("T-495", f"BED|{r['id']}|{o['finish']}", r["id"], "TILE_BED_MORTAR",
                          f"bed_mortar_m3@{o['finish']}", None,
                          [bed["mortar_m3"]["low"], bed["mortar_m3"]["high"]] if bed else None,
                          stage="INSTALLED", status=o["status"], read=read,
                          note=None if bed else o.get("bed_reason")))
    return out


def bindings(tables):
    return (bind_t453(tables["T-453"]) + bind_t454(tables["T-454"]) + bind_t489(tables["T-489"])
            + bind_t455(tables["T-455"]) + bind_t495(tables["T-495"]))


# --------------------------------------------------------------------------------------------- checks
def _fail(fails, kind, where, why):
    fails.append({"kind": kind, "where": where, "why": why})


def check_presence(bs, cand, fails):
    for b in bs:
        lid = b["line_id"]
        if b["stage"] == "NO_CANDIDATE_LINE":
            if lid is not None and lid not in cand["lines"]:
                _fail(fails, "ABSENT_LINE", b["row"], f"lintel host line {lid} not in {cand['version']}")
            continue
        ln = cand["lines"].get(lid)
        if ln is None:
            _fail(fails, "ABSENT_LINE", f"{b['table']} {b['row']}", f"line {lid} is not in {cand['version']}")
            continue
        if lid in cand["changed"]:
            _fail(fails, "STALE_AT_V3047", f"{b['table']} {b['row']}", f"{lid} changed between V3.0.46 and V3.0.47")
        r = b["read"]
        if ln["unit"] != r.get("unit_read", "m2"):
            _fail(fails, "UNIT", f"{b['table']} {b['row']}", f"line unit {ln['unit']} != read {r.get('unit_read')}")
        if (r["class_read"] == "HELD") != (ln["class"] == "HELD"):
            _fail(fails, "STALE_INPUT", f"{b['table']} {b['row']}",
                  f"class read {r['class_read']} vs candidate {ln['class']}")
        elif ln["class"] == "RELEASED" and not _near(r.get("net_read"), ln["measured_net"]):
            _fail(fails, "STALE_INPUT", f"{b['table']} {b['row']}",
                  f"net read {r.get('net_read')} vs candidate {ln['measured_net']}")
        elif "held_read" in r and ln["class"] == "HELD":
            if not (_near(r["held_read"][0], ln["held_low"]) and _near(r["held_read"][1], ln["held_high"])):
                _fail(fails, "STALE_INPUT", f"{b['table']} {b['row']}",
                      f"held range read {r['held_read']} vs candidate {[ln['held_low'], ln['held_high']]}")


def check_held(bs, cand, tables, fails):
    for b in bs:
        if b["stage"] == "NO_CANDIDATE_LINE":
            if b["status"] in ("HELD", "FLAGGED") and b["value"] is not None:
                _fail(fails, "HELD_YIELDS_FIGURE", b["row"], f"{b['status']} lintel prints {b['value']} m3")
            continue
        ln = cand["lines"].get(b["line_id"])
        if ln is None:
            continue
        held_row = (b["status"] or "").upper() == "HELD"
        if ln["class"] in ("HELD", "EXCLUDED") or held_row:
            if b["value"] is not None:
                _fail(fails, "HELD_YIELDS_FIGURE", f"{b['table']} {b['row']}",
                      f"{b['kind']} = {b['value']} from a {ln['class'] if not held_row else 'HELD row'} input")
            if ln["class"] == "HELD" and b["bound"] is not None and ln["held_low"] is None and ln["held_high"] is None:
                _fail(fails, "UNSOURCED_BOUND", f"{b['table']} {b['row']}",
                      f"bound {b['bound']} on a HELD line without a candidate range")
            if ln["class"] == "EXCLUDED" and b["bound"] is not None:
                _fail(fails, "UNSOURCED_BOUND", f"{b['table']} {b['row']}", "bound on an EXCLUDED line")
    # A purchasing group is one product bought once (one ceil): the group is keyed by material and group, across
    # tables (T-455 and T-495 adhesive rows are one PROJECT adhesive group). A member without a figure (HELD, a
    # range or a bound only) leaves the group without a 'to buy' figure.
    groups, members = {}, {}
    for b in bs:
        if b["group"] and b["line_id"] in cand["lines"]:
            key = (b["material"], b["group"])
            members.setdefault(key, set()).add(b["line_id"])
            g = groups.setdefault(key, set())
            if b["value"] is None:
                g.add(b["line_id"])
    for lid in KNOWN_GAPS:            # unread MAS.BLOCK lines (type not known) are open members of the glue group
        if lid in cand["lines"] and cand["lines"][lid]["item_code"] == "MAS.BLOCK":
            groups.setdefault(("MASONRY_LAYING", "PROJECT"), set()).add(lid)
            members.setdefault(("MASONRY_LAYING", "PROJECT"), set()).add(lid)
    printed = {("MASONRY_LAYING", "PROJECT"): tables["T-453"]["glue_groups"]["PROJECT"]["bags_to_buy"],
               ("TILE_ADHESIVE", "PROJECT"): tables["T-455"]["purchase"]["adhesive"]["PROJECT"]["bags_to_buy"]}
    for key, held in groups.items():
        if held and printed.get(key) is not None:
            _fail(fails, "GROUP_HELD_FIGURE", "/".join(key), f"to-buy {printed[key]} with {len(held)} open member(s)")
    return {"/".join(k): {"members": len(members[k]), "without_figure": sorted(v), "to_buy": printed.get(k)}
            for k, v in sorted(groups.items())}


def check_double(bs, cand, fails):
    seen = {}
    for b in bs:      # a binding that carries nothing (HELD, no bound) produces nothing: it cannot double count
        if b["line_id"] is None or b["stage"] == "NO_CANDIDATE_LINE" or (b["value"] is None and b["bound"] is None
                                                                             and b["estimate_beside"] is None):
            continue
        # '@option' kinds are alternatives of one table on one line (never summed); across tables they still collide
        seen.setdefault((b["line_id"], b["material"], b["kind"].split("@")[0]), []).append(b)
    for key, lst in seen.items():
        tabs = {b["table"] for b in lst}
        if len(lst) == len(tabs) == 1:
            continue
        options_only = len(tabs) == 1 and len({b["kind"] for b in lst}) == len(lst) and all("@" in b["kind"] for b in lst)
        if options_only:
            continue
        if len(tabs) < len(lst):
            _fail(fails, "DOUBLE_BOUND", "|".join(key), f"bound {len(lst)} times inside {sorted(tabs)}")
            continue
        declared = any(set(pair) == tabs and key[2] in kinds for pair, kinds in READS.items())
        if not declared:
            _fail(fails, "DOUBLE_BOUND", "|".join(key), f"one line bound by {sorted(tabs)} for {key[1]} {key[2]}")
            continue
        vals = {json.dumps([b["value"], b["bound"], b["estimate_beside"]]) for b in lst}
        if len(vals) > 1:
            _fail(fails, "CHAIN_DIVERGES", "|".join(key), f"reader and producer differ: {sorted(vals)}")
    # R-T496-4 cross-trade: a candidate layer line on the same host as a table's material
    layer_hosts = {}
    for ln in cand["lines"].values():
        for rx, mat in LAYER_CODES:
            if rx.search(ln["item_code"] or "") and ln["class"] != "EXCLUDED":
                layer_hosts.setdefault((mat, _host(ln.get("element_id"))), []).append(ln["line_id"])
    for b in bs:
        ln = cand["lines"].get(b["line_id"])
        if ln is None or b["stage"] == "NO_CANDIDATE_LINE":
            continue
        hit = layer_hosts.get((b["material"], _host(ln.get("element_id"))))
        if hit and (b["value"] is not None or b["bound"] is not None):
            _fail(fails, "CROSS_TRADE_DOUBLE", f"{b['table']} {b['row']}",
                  f"{b['material']} also carried by candidate line(s) {hit} on host {_host(ln['element_id'])}")


def check_scope(bs, cand, tables, fails):
    read = {}
    for b in bs:
        read.setdefault(b["table"], set()).add(b["line_id"])
    read.setdefault("T-454", set()).update(x["line_id"] for x in tables["T-454"]["excluded"])
    read.setdefault("T-455", set()).update(tables["T-455"]["excluded_lines"])
    census = {}
    for t, codes in SCOPE.items():
        for code in codes:
            lines = [ln for ln in cand["lines"].values() if ln["item_code"] == code]
            unread = [ln["line_id"] for ln in lines if ln["line_id"] not in read.get(t, set())]
            gaps = [x for x in unread if x in KNOWN_GAPS]
            for x in unread:
                if x not in KNOWN_GAPS:
                    _fail(fails, "SCOPE_LINE_UNREAD", f"{t} {code}", f"{x} ({cand['lines'][x]['class']}) read by no row")
            census[f"{t}|{code}"] = {"lines": len(lines), "read": len(lines) - len(unread), "known_gaps": gaps}
    return census


def check_arithmetic(tables, fails):
    """R-T496-6: each figure from the owner rule and the row's own stated inputs (an independent re-derivation)."""
    n = 0
    d = tables["T-453"]
    req = {}
    for lt in d["lintels"]:
        if lt["decision"] == "REQUIRED":
            face = (lt["width_m"] + 2 * LINTEL_BEARING_M) * lt["section_m"][1]
            if not _rel(face, lt["face_m2"]):
                _fail(fails, "ARITHMETIC", f"T-453 LINTEL|{lt['opening_id']}", f"face {lt['face_m2']} != {face}")
            conc = lt["section_m"][0] * lt["section_m"][1] * (lt["width_m"] + 2 * LINTEL_BEARING_M)
            if lt.get("concrete_m3") is not None and not _rel(conc, lt["concrete_m3"]):
                _fail(fails, "ARITHMETIC", f"T-453 LINTEL|{lt['opening_id']}", f"concrete {lt['concrete_m3']} != {conc}")
            req[lt["opening_id"]] = face
            n += 2
    for r in d["block_materials"]:
        if r["status"] == "HELD":
            continue
        where = f"T-453 {r['item']}|{r['line_id']}"
        ded = sum(x.get("face_m2") or 0.0 for x in r.get("lintel_deductions") or [])
        if not _rel(r["contract_net_m2"] - ded, r["material_base_m2"]):
            _fail(fails, "ARITHMETIC", where, f"base {r['material_base_m2']} != net {r['contract_net_m2']} - {ded}")

        def vals(key):          # the range when the row prints one, else the single figure (None kept, never 0)
            return list(r.get(key + "_range") or []) or ([r[key]] if r.get(key) is not None else [])

        bases = list(r.get("material_base_range_m2") or []) or [r["material_base_m2"]]
        if r["item"] == "BLOCK_COUNT":
            got, want = vals("theoretical_count"), [x * BLACK_PER_M2 for x in bases]
        elif r["material_type"] == "WHITE":
            rate = GLUE_KG_M2[round(r["thickness_m"], 2)]
            got = vals("consumption_kg") + vals("bags_25kg_net")
            want = [x * rate for x in bases] + [x * rate / GLUE_BAG_KG for x in bases]
            want = want[:len(got)] if len(got) == len(bases) else want
        else:
            m3 = [x * r["mortar_per_m2"] for x in bases]
            got = vals("mortar_installed_m3") + vals("cement_bags") + vals("sand_m3_loose")
            want = m3 + ([x * MORTAR_BAGS_M3 for x in m3] + [x * MORTAR_SAND_M3 for x in m3]
                         if len(got) > len(m3) else [])
        for g, w in zip(got, want):
            n += 1
            if g is None or not _rel(g, w):
                _fail(fails, "ARITHMETIC", where, f"{g} != owner-rule {w}")
        if len(got) != len(want):
            _fail(fails, "ARITHMETIC", where, f"{len(got)} figures vs {len(want)} re-derived")
    for t in ("T-454", "T-489"):
        for r in tables[t]["table"]["rows"]:
            for L in r["layers"]:
                if L.get("mortar_m3") is not None:
                    n += 1
                    if not _rel(L["mortar_m3"], L["area_m2"] * L["thickness_m"]):
                        _fail(fails, "ARITHMETIC", f"{t} {r['id']}|{L['layer']}", f"{L['mortar_m3']} != area x t")
                if L.get("mortar_m3_at_least") is not None:
                    n += 1
                    if not _rel(L["mortar_m3_at_least"], L["area_m2"] * L["thickness_m"]):
                        _fail(fails, "ARITHMETIC", f"{t} {r['id']}|{L['layer']}", "render bound != area x t")
    for r in tables["T-455"]["rows"]:
        bb = r.get("adhesive_bound_bags")
        if bb and r["area_m2"] is not None:
            n += 2
            if not (_rel(bb["low"], r["area_m2"] / ADHESIVE_M2_PER_BAG[0]) and
                    _rel(bb["high"], r["area_m2"] / ADHESIVE_M2_PER_BAG[1])):
                _fail(fails, "ARITHMETIC", f"T-455 ADH|{r['id']}", f"bound {bb} != area / 5 .. area / 3")
    for r in tables["T-495"]["finish_held_rows"]:
        if r["area_held_low_m2"] is None or r["area_held_high_m2"] is None:
            continue        # no candidate range: a bound here is UNSOURCED_BOUND (R-T496-2), not an arithmetic case
        for o in r["options"]:
            a = o.get("adhesive_bags_20kg")
            if a:
                n += 2
                if not (_rel(a["low"], r["area_held_low_m2"] / 5.0) and _rel(a["high"], r["area_held_high_m2"] / 3.0)):
                    _fail(fails, "ARITHMETIC", f"T-495 {r['id']}|{o['finish']}", "adhesive bound != low/5 .. high/3")
            bed = o.get("bed")
            if bed:
                m = bed["mortar_m3"]
                n += 4
                ok = (_rel(m["low"], r["area_held_low_m2"] * bed["bed_m"][0] * 1.05)
                      and _rel(m["high"], r["area_held_high_m2"] * bed["bed_m"][1] * 1.05)
                      and _rel(bed["cement_bags_50kg"]["low"], m["low"] * MORTAR_BAGS_M3)
                      and _rel(bed["sand_m3_loose"]["high"], m["high"] * MORTAR_SAND_M3))
                if not ok:
                    _fail(fails, "ARITHMETIC", f"T-495 {r['id']}|{o['finish']}", "bed bound != Q-45 B 1:4 x 1.05")
    return n


# Printed subtotals that are 0.0 over rows of which none carries a number (R-T496-2: missing is never 0). Each is
# declared here with the finding that names it; an undeclared one fails ZERO_SUBTOTAL. A wiring reads them as None.
KNOWN_TABLE_DEFECTS = {
    "T-455 by_item_code.FIN.FLOOR.FINISH_HELD.bound_low": "F-T496-1",
    "T-455 by_item_code.FIN.FLOOR.FINISH_HELD.bound_high": "F-T496-1",
    "T-455 by_item_code.FIN.FLOOR.FINISH_HELD.v3_flat_bags": "F-T496-1",
    "T-455 by_item_code.EXT.FLOOR.PORCELAIN.v4_bags_known": "F-T496-1",
    "T-455 by_item_code.FIN.FLOOR.FINISH_HELD.v4_bags_known": "F-T496-1",
    "T-455 by_item_code.FIN.FLOOR.PORCELAIN.v4_bags_known": "F-T496-1",
    "T-455 by_item_code.FIN.FLOOR.WET_TILE.v4_bags_known": "F-T496-1",
    "T-455 by_item_code.FIN.WALL.TILE.v4_bags_known": "F-T496-1",
    "T-455 purchase.adhesive.PROJECT.bags_known": "F-T496-1",
}
FINDINGS = {
    "F-T496-1": "T-455 (and its re-run inside T-495) prints 0.0 for subtotals over rows none of which carries a "
                "number: v4_bags_known 0.0 on every code and on the PROJECT adhesive group (all 64 rows HELD), and "
                "bound_low / bound_high / v3_flat_bags 0.0 on FIN.FLOOR.FINISH_HELD (3 lines, no row bounded). The "
                "status beside each says HELD, so no released figure is wrong, but a wiring that sums these fields "
                "adds a 0 for a HELD quantity. The wiring row must read them as None (unknown); a later T-455 "
                "version prints None.",
}


def check_zero_subtotals(bs, cand, tables, fails, declared):
    t = tables["T-455"]
    rows_by_code = {}
    for b in bs:
        if b["table"] == "T-455" and b["material"] == "TILE_ADHESIVE":
            ln = cand["lines"].get(b["line_id"])
            if ln is not None:
                rows_by_code.setdefault(ln["item_code"], []).append(b)
    fields = {"bound_low": lambda b: b["bound"], "bound_high": lambda b: b["bound"],
              "v3_flat_bags": lambda b: b["bound"], "v4_bags_known": lambda b: b["value"]}
    found = []
    for code, tot in t["by_item_code"].items():
        for f, carrier in fields.items():
            if tot.get(f) == 0 and not any(carrier(b) is not None for b in rows_by_code.get(code, [])):
                found.append(f"T-455 by_item_code.{code}.{f}")
    grp = t["purchase"]["adhesive"]["PROJECT"]
    if grp.get("bags_known") == 0 and not any(b["value"] is not None for v in rows_by_code.values() for b in v):
        found.append("T-455 purchase.adhesive.PROJECT.bags_known")
    for w in found:
        if w not in declared:
            _fail(fails, "ZERO_SUBTOTAL", w, "0.0 printed over rows none of which carries a number")
    return found


def check_chain_tables(tables, fails):
    """T-495 re-ran the T-455 ledger on V3.0.46: equal to T-455 on V3.0.45 means those lines did not move."""
    a = tables["T-495"]["t455_ledger_on_this_input"]
    t = tables["T-455"]
    for k, v in (("adhesive", t["purchase"]["adhesive"]), ("by_item_code", t["by_item_code"]),
                 ("excluded_lines", t["excluded_lines"])):
        if a.get(k) != v:
            _fail(fails, "CHAIN_DIVERGES", f"T-495 t455_ledger_on_this_input.{k}", "differs from T-455's own output")


def aggregation(bs, tables):
    """Component -> subtotal: sums of the bound rows against each table's printed totals (labels never mixed)."""
    out, s = [], lambda it: round(sum(it), 6)
    t453 = [b for b in bs if b["table"] == "T-453"]
    pairs = [
        ("T-453 black 0.20 blocks VERIFIED-NET nr",
         s(b["value"] for b in t453 if b["kind"] == "units_nr" and b["status"] == "VERIFIED-NET"),
         tables["T-453"]["block_totals"]["black_0_20_by_label"]["VERIFIED-NET"]["theoretical_blocks"]),
        ("T-453 AAC glue VERIFIED-NET kg",
         s(b["value"] for b in t453 if b["kind"] == "glue_kg" and b["status"] == "VERIFIED-NET"),
         tables["T-453"]["glue_groups"]["known_part_by_label"]["VERIFIED-NET"]["kg"]),
        ("T-453 AAC glue PROVISIONAL-NET kg",
         s(b["value"] for b in t453 if b["kind"] == "glue_kg" and b["status"] == "PROVISIONAL-NET"),
         tables["T-453"]["glue_groups"]["known_part_by_label"]["PROVISIONAL-NET"]["kg"]),
        ("T-453 black mortar PROVISIONAL-NET m3",
         s(b["value"] for b in t453 if b["kind"] == "mortar_m3" and b["status"] == "PROVISIONAL-NET"),
         tables["T-453"]["mortar"]["black_0_20_provisional_net"]["m3"]),
        ("T-454 dry WALL_PLASTER mortar m3 (ESTIMATED-NET)",
         s(b["estimate_beside"] for b in bs if b["table"] == "T-454" and b["material"] == "WALL_PLASTER"
           and b["kind"] == "mortar_m3" and b["estimate_beside"] is not None),
         tables["T-454"]["table"]["sums"]["WALL_PLASTER"]["mortar_m3"]),
        ("T-454 wet LEVELLING_RENDER mortar m3 AT_LEAST",
         s(b["bound"][0] for b in bs if b["table"] == "T-454" and b["material"] == "LEVELLING_RENDER"
           and b["kind"] == "mortar_m3" and b["bound"] and b["bound"][1] is None),
         tables["T-454"]["table"]["sums"]["LEVELLING_RENDER"]["mortar_m3_at_least"]),
    ]
    # UPC-WETWALL-001: the tiler's levelling render lies under every tiled wall face, so the released render face
    # (T-454 FIN.PLASTER wet lines) and the released wall-tile face (T-455 FIN.WALL.TILE) are one physical area read
    # by two trades for two different materials (render mortar, adhesive): equal, never added.
    rend = {r["id"]: r["area_m2"] for r in tables["T-454"]["table"]["rows"]
            if r["class"] == "WET_WALL_RENDER" and r["area_m2"] is not None}   # reveal rows (class HELD) excluded
    wall = {r["id"]: r["area_m2"] for r in tables["T-455"]["rows"] if r["kind"] == "WET_WALL" and r["area_m2"]}
    pairs.append(("wet-wall face: T-454 render m2 = T-455 wall-tile m2 (one face, two trades)",
                  s(rend.values()), round(sum(wall.values()), 6)))
    for code, tot in tables["T-455"]["by_item_code"].items():   # summed per item code in _t455_code_sums
        pairs.append((f"T-455 {code} adhesive bound low bags", None, tot["bound_low"]))
    for name, got, printed in pairs:
        out.append({"total": name, "sum_of_bound_rows": got, "table_prints": printed,
                    "agree": None if got is None else _near(got, printed, 1e-5)})
    return out


def _t455_code_sums(bs, cand, tables, agg):
    for a in agg:
        if a["total"].startswith("T-455 "):
            code = a["total"].split()[1]
            a["sum_of_bound_rows"] = round(sum(b["bound"][0] for b in bs if b["table"] == "T-455"
                                               and b["kind"] == "adhesive_bags_20kg" and b["bound"]
                                               and (cand["lines"].get(b["line_id"]) or {}).get("item_code") == code), 6)
            a["agree"] = _near(a["sum_of_bound_rows"], a["table_prints"], 1e-5)


# --------------------------------------------------------------------------------------------- build
def run(tables=None, cand=None, pins=True):
    declared = {}
    if tables is None:            # the declarations belong to the pinned committed tables only, never to other inputs
        declared = KNOWN_TABLE_DEFECTS
        tables = {"T-453": _load(T453, pins), "T-454": _load(T454, pins), "T-489": _load(T489, pins),
                  "T-455": _load(T455, pins), "T-495": _load(T495, pins)}
    if cand is None:
        cand = candidate_v3047(_load(INDEX, pins), _load(T443, pins))
    bs = bindings(tables)
    fails = []
    check_presence(bs, cand, fails)
    groups = check_held(bs, cand, tables, fails)
    check_double(bs, cand, fails)
    census = check_scope(bs, cand, tables, fails)
    n_arith = check_arithmetic(tables, fails)
    if "t455_ledger_on_this_input" in tables["T-495"]:
        check_chain_tables(tables, fails)
    zeros = check_zero_subtotals(bs, cand, tables, fails, declared)
    agg = aggregation(bs, tables)
    _t455_code_sums(bs, cand, tables, agg)
    for a in agg:
        if a["agree"] is False:
            _fail(fails, "ARITHMETIC", a["total"], f"rows sum {a['sum_of_bound_rows']} != printed {a['table_prints']}")
    for b in bs:
        ln = cand["lines"].get(b["line_id"]) or {}
        b["item_code"], b["unit"], b["candidate_class"] = ln.get("item_code"), ln.get("unit"), ln.get("class")
        b["wiring_state"] = ("NO_CANDIDATE_LINE" if b["stage"] == "NO_CANDIDATE_LINE" else
                             "WIREABLE_FIGURE" if b["value"] is not None else
                             "ESTIMATE_BESIDE_HELD" if b["estimate_beside"] is not None else
                             "BOUND_ONLY" if b["bound"] is not None else "HELD")
    return {"schema": SCHEMA, "candidate": cand["version"], "candidate_sha256": cand["sha256"],
            "inputs": {str(p.relative_to(ROOT)): h for p, h in PINS.items()},
            "bindings": bs, "purchasing_groups_held_members": groups, "scope_census": census,
            "known_gaps": KNOWN_GAPS, "not_in_any_table": NOT_IN_ANY_TABLE, "aggregation": agg,
            "arithmetic_figures_rederived": n_arith, "failures": fails,
            "zero_subtotals_declared": {z: KNOWN_TABLE_DEFECTS.get(z) for z in zeros}, "findings": FINDINGS,
            "released_quantities_changed": 0}


def summary(m):
    from collections import Counter
    c = Counter((b["table"], b["material"], b["wiring_state"]) for b in m["bindings"])
    return {f"{k[0]}|{k[1]}|{k[2]}": v for k, v in sorted(c.items())}


def write(m, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    m = dict(m, summary=summary(m))
    (out_dir / "BINDING_MAP_T496.json").write_text(json.dumps(m, indent=1, sort_keys=True, ensure_ascii=False) + "\n",
                                                   encoding="utf-8")
    cols = ("table", "row", "line_id", "item_code", "unit", "candidate_class", "material", "kind", "stage", "value",
            "bound", "estimate_beside", "status", "group", "wiring_state")
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(cols)
    for b in sorted(m["bindings"], key=lambda b: (b["table"], b["row"], b["kind"])):
        w.writerow([json.dumps(b[c]) if isinstance(b[c], list) else ("" if b[c] is None else b[c]) for c in cols])
    (out_dir / "BINDING_MAP_T496.csv").write_text(buf.getvalue(), encoding="utf-8")


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    m = run()
    if "--check" in argv:
        for f in m["failures"]:
            print(f"FAIL {f['kind']}: {f['where']}: {f['why']}")
        print(f"T-496 binding check on {m['candidate']}: {len(m['bindings'])} bindings, "
              f"{m['arithmetic_figures_rederived']} figures re-derived, {len(m['failures'])} failure(s)")
        return 1 if m["failures"] else 0
    write(m, argv[0] if argv else HERE / "out")
    print(json.dumps(m["summary"] if "summary" in m else summary(m), indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
