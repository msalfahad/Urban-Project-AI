"""T-713: MASONRY REST on ARCH_TAKEOFF_V3.0.70: every HELD / EXCLUDED masonry line by cause, the 7 parent MAS.BLOCK
lines decomposed into their held walls / pieces (component -> cause -> designer item / owner rule / method gap), and
R-T713-1 PARENT_ONE_END_V1: a parent's one-ended bound from its components, its material lines following it.

Physical element first (ERS s.2.1): a parent MAS.BLOCK line is the block face of the held walls / pieces of one
floor and thickness that no colour part line carries. Its area is the SUM of its components; a sum has an upper end only
when EVERY component has one (an open term opens the sum), and a lower end only from components with a drawn minimum.
Its units / mortar / glue are the materials of that same face: they exist only as far as the face does, so they are
never firmer than the parent (lesson T-698): blank parent -> blank material, AT_MOST parent -> AT_MOST material (colour
not split: the black part, the black mortar and the AAC glue are each at most the whole face x their rate), white
units / perimeter joint HELD (no AAC count rule; no piece ends). Installed quantities only; waste / procurement HELD.

R-T713-1 component ends (every villa):
  - DROP (wall under a sunken panel, U - L x d, d >= 0 not printed; D-41): AT_MOST U; no drawn lower end.
  - UNLABELLED_MEMBER piece (a piece under a member whose depth is not printed; D-04 / Q-61 C(4)): AT_MOST
    L x (top of the plate above - top of the plate below - the printed depth of the deeper KNOWN member it frames
    into, 0 if none), with the plate-above top at its physical maximum (a structural top cannot sit above the
    finished level printed over it: roof build-up b_r >= 0). Only when both plate tops are drawn (or bounded so).
  - every other cause: no drawn end (named, never 0).
A parent with every component bounded above gets AT_MOST = sum (rounded UP, R-T696-1); otherwise it stays blank with
the blocking components named. A parent AT_LEAST is printed only when some component has a positive drawn minimum.

Sources (merged, sha-pinned; nothing typed but the datum levels and member depths, each with its source):
  - research/agents_t693/out/LINE_INDEX_V3_0_70.json (T-693 run of record e8e001de): the lines and their states;
  - research/agents_t672/out/LINE_INDEX_V3_0_68.json: asserted MAS-identical to V3.0.70 (so T-696 applies);
  - research/agents_t696/out/T696_B9_CENSUS.json (Checker-merged): the 61 blank material rows and their causes;
  - research/agents_t449/round3/out/CORRECTION_REGISTER_BLOCKWORK_T449.json: the held walls / pieces of each parent;
  - research/agents_t670/out/T670_MATERIALS.json: the bounded material ranges (HELD lintel faces).
Levels: FFRS (p.5) top +9.65 DRAWING-CONFIRMED (T-482 / T-214: 2F FFL +9.70, drawn 0.05); main roof finished +13.90
(section A-A, T-482): structural top +13.90 - b_r, b_r >= 0 (D-39). B1 / B2 band depth 0.40 (printed schedule, as the
register's held text itself states 'the deeper of B2 / B1 (0.40)').

    bash scripts/agent_env.sh run --tree task-T-713 research/agents_t713/t713_masonry_rest.py [--json OUT]
        [--candidate <private V3_0_70_BOQ_LINES.json>]   (every parent's components against the candidate rfi text)

No drawing, workbook, client name or coordinate is read or written here: only merged research ledgers.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
for _p in (HERE, ROOT / "research" / "agents_t696"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import bound_rounding_v1 as BR  # noqa: E402

RULE_ID, RULE_VERSION, METHOD = "R-T713-1", "1.0.0", "PARENT_ONE_END_V1"

IDX70 = ROOT / "research/agents_t693/out/LINE_INDEX_V3_0_70.json"
IDX68 = ROOT / "research/agents_t672/out/LINE_INDEX_V3_0_68.json"
T696 = ROOT / "research/agents_t696/out/T696_B9_CENSUS.json"
REG = ROOT / "research/agents_t449/round3/out/CORRECTION_REGISTER_BLOCKWORK_T449.json"
T670 = ROOT / "research/agents_t670/out/T670_MATERIALS.json"
T482 = ROOT / "research/agents_t482/out/T482_CONDITIONS.json"
RB = ROOT / "rules/rulebook/URBAN_COMPANY_RULEBOOK_1.1.0.json"
PINS = {IDX70: "6c12da07", IDX68: "fc485958", T696: "6810a8ea", REG: "4f1c794c", T670: "4c58a226", T482: "ddb013b0", RB: "da38d121"}
LINES70_SHA = "e8e001de"

BLOCKS_PER_M2 = "12.5"                      # Q-75 / Q-80, 40 x 20 face, 0.15 and 0.20 (owner 2026-11-07)
UNIT_M, MODULE_M = ("0.39", "0.19"), ("0.40", "0.20")

# Plate tops (m) used by R-T713-1; (value, kind, source). A 'max' top is the physical maximum of an unprinted top.
PLATE_TOP = {
    "2F": {"below": ("9.65", "drawn", "FFRS p.5 top: 2F FFL +9.70 - drawn 0.05 (T-482 / T-214, DRAWING-CONFIRMED)"),
           "above": ("13.90", "max", "main roof +13.90 finished (A-A); structural top 13.90 - b_r, b_r >= 0 (D-39)")},
    "1F": {"below": ("5.45", "drawn", "GFRS p.4 top (T-482)"),
           "above": ("9.65", "drawn", "FFRS p.5 top (T-482)")},
}

# Component cause classes: (regex on the register's held text, class, cause / designer reference, end kind)
CLASSES = [
    (r"drop d of the sunken panel", "DROP", "D-41 sunken-panel drop not printed (R-MAS-DROP-1)", "AT_MOST_U"),
    (r"STOREY_HEIGHT\.GF\.ANNEX", "ANNEX_DATUM", "D-06 / D-17 annex roof +4.30 not a structural datum (owner Q-54 B "
     "HOLD); annex floor build-up not printed", "NONE"),
    (r"lift tie beam", "LIFT_TIE_BEAM", "D-43 lift tie beam at +3.00 printed, size not (ST p.8 n.19)", "NONE"),
    (r"width not drawn", "OPENING_WIDTH", "opening width not drawn on any sheet (no D-id yet: T-716 to assign)", "NONE"),
    (r"DOME_OPENING|dome opening|east ring|no B4 label", "DOME", "D-20 / D-42 wall top inside the dome openings not "
     "drawn (T-227); east ring band unlabelled (Q-44 A)", "NONE"),
    (r"SF B3", "STAIR_SHAFT", "stair-shaft piece: no floor on the shaft line, landing member level not printed "
     "(A-A sheet 10; D-03 'B3 (With Stair)')", "NONE"),
    (r"D-04|BM-[G12]F-0\d\d \((?:depth )?not p", "UNLABELLED_MEMBER", "D-04 unlabelled member, depth not printed (Q-61 C(4))", "AT_MOST_PLATE"),
    (r"no drawn wall piece", "NO_PIECE", "no wall band or member over the wall (GF-H01 / GF-H02 / GF-W37 glazed line "
     "or strip: material, base, top designer, T-228; GF-W30 0.30 stub + door: method gap, T-125 D)", "NONE"),
    (r"CB3 and", "LABEL", "D-03 'CB3' and 'B3 (with stair)' on one line (owner Q-61 (2))", "NONE"),
    (r"BEAM_OR_COLUMN face", "MEMBER_FACE", "member face of unknown kind over the piece (method gap, T-228)", "NONE"),
    (r"length residual", "RESIDUAL", "length residual between drawn faces and ledger pieces, location not "
     "established (method gap, T-017)", "NONE"),
    (r"openings .* exceed the closable part", "OPENING_POSITION", "opening position against held pieces not read "
     "(with the dome piece)", "NONE"),
]
PIECE_RE = re.compile(r"^(\d+):(?:H |SF |R |)?(.*?) (\d+\.\d{4}) m: (.*)$")


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def classify(text):
    for rx, cls, cause, end in CLASSES:
        if re.search(rx, text):
            return cls, cause, end
    raise ValueError(f"unclassified held text (census incomplete): {text[:120]}")


def piece_length(text):
    m = PIECE_RE.match(text)
    return BR.D(m.group(3)) if m else None


def known_depth(text):
    """the printed depth of the deeper KNOWN member a piece frames into, as the held text states it."""
    m = re.search(r"deeper of B\d(?: / B\d)? \((\d+\.\d+)\)", text)
    return BR.D(m.group(1)) if m else BR.D(0)


def component_end(cls, end, floor, text, drop_upper=None, plate_tops=None):
    """R-T713-1: the drawn ends of one component -> {'upper': Decimal|None, 'lower': Decimal|None, 'why': str}."""
    if end == "AT_MOST_U":
        if drop_upper is None:
            raise ValueError("a DROP component needs its U (net at d = 0); never 0")
        return {"upper": BR.D(drop_upper), "lower": None, "why": "U at d = 0 (d >= 0); lower open"}
    if end == "AT_MOST_PLATE":
        pt = (PLATE_TOP if plate_tops is None else plate_tops).get(floor)
        L = piece_length(text)
        if pt is None or L is None:
            return {"upper": None, "lower": None, "why": "plate tops or piece length not drawn: open"}
        if L > 100:
            raise ValueError(f"piece length {L} is not in metres (mm read as m?)")
        if pt["below"][1] != "drawn":
            return {"upper": None, "lower": None, "why": "plate below not drawn: open"}
        h = BR.add(pt["above"][0], -BR.D(pt["below"][0]), -known_depth(text))
        if h <= 0:
            raise ValueError(f"non-positive height bound {h} for {text[:60]}")
        return {"upper": BR.mul(L, h), "lower": None, "length_m": str(L), "height_max_m": str(h),
                "why": f"L x ({pt['above'][0]} - {pt['below'][0]} - {known_depth(text)}) with member depth >= 0"
                       + (" and b_r >= 0" if pt["above"][1] == "max" else "")}
    return {"upper": None, "lower": None, "why": "no drawn end"}


def parent_bound(components):
    """sum of components: AT_MOST only if every component has an upper end; AT_LEAST only from positive minima."""
    if not components:
        raise ValueError("a parent with no component: census incomplete (never 0)")
    ups = [c["end"]["upper"] for c in components]
    lows = [c["end"]["lower"] for c in components if c["end"]["lower"] is not None and c["end"]["lower"] > 0]
    blockers = [c["id"] for c in components if c["end"]["upper"] is None]
    out = {"blocking_components": blockers}
    if not blockers:
        ex = BR.add(*ups)
        out.update(kind="AT_MOST", exact_m2=str(ex), printed_m2=float(BR.round_high(ex)))
    elif lows:
        ex = BR.add(*lows)
        out.update(kind="AT_LEAST", exact_m2=str(ex), printed_m2=float(BR.round_low(ex)))
    else:
        out.update(kind="NONE")
    return out


def joint_rate(t):
    k = BR.D(BR._CTX.divide(BR.mul(*UNIT_M), BR.mul(*MODULE_M)))
    return BR.mul(t, BR.add(1, -k))


def glue_rate(rb, t):
    for r in rb["records"]:
        if r.get("rule_id") == "UPC-AAC-GLUE-001":
            if r.get("status") != "OWNER_CONFIRMED":
                raise SystemExit("UPC-AAC-GLUE-001 is not OWNER_CONFIRMED")
            v = r["params"]["kg_per_m2_by_thickness_m"]["value"].get(f"{float(t):.2f}")
            return None if v is None else BR.D(v)
    raise SystemExit("rulebook: no UPC-AAC-GLUE-001 record")


def material_follow(parent, code, t, glue):
    """the material line follows its parent: never firmer (lesson T-698)."""
    if parent["kind"] == "NONE":
        return {"kind": "NONE", "why": "parent blank: the material exists only as far as the face does"}
    if code == "MAS.UNITS.WHITE":
        return {"kind": "NONE", "why": "no AAC count rule (Q-60 faces beside only): HELD with the parent"}
    if code == "MAS.MORTAR.BLACK.PERIMETER":
        return {"kind": "NONE", "why": "perimeter joint needs the piece ends / soffit courses: HELD with the parent"}
    base = BR.D(parent["exact_m2"])
    if code == "MAS.UNITS.BLACK":
        ex = BR.mul(base, BLOCKS_PER_M2)
    elif code == "MAS.MORTAR.BLACK":
        ex = BR.mul(base, joint_rate(t))
    elif code == "MAS.GLUE.AAC":
        if glue is None:
            return {"kind": "NONE", "why": "AAC glue rate missing for this thickness: HELD, never borrowed"}
        ex = BR.mul(base, glue)
    else:
        raise ValueError(code)
    pr = BR.round_high(ex) if parent["kind"] == "AT_MOST" else BR.round_low(ex)
    return {"kind": parent["kind"], "exact": str(ex), "printed": float(pr),
            "why": "colour not split: each colour's part is at most the whole face" if parent["kind"] == "AT_MOST"
            else "one-ended like its parent"}


def drop_u_overrides(t482):
    """T-482 R-MAS-WIDTH-CONFLICT-1 (Checker-merged): a DROP wall's U is the max over its D-27 readings."""
    return {w["element_id"]: w["U_m2"] for w in t482["width_conflicts"] if "U_m2" in w}


def parents(reg, mas70, u_over=None):
    """the held walls / pieces each parent holds (register round 3), classified; 2F established parts excluded (they
    moved to the colour part lines with R-MAS-ROOF-DATUM-1, T-488)."""
    by = {}
    for e in reg["entries"]:
        if e.get("item_code") != "MAS.BLOCK" or e["action"] in ("VERIFIED", "DRAWING-CONFIRMED",
                                                                 "ASSUMED - OWNER-APPROVED"):
            continue
        lid = e["line_id"]
        if mas70.get(lid, {}).get("class") != "HELD" or mas70[lid]["element_id"].count("#"):
            raise SystemExit(f"{lid}: register parent is not a HELD parent line on V3.0.70")
        rr = e["rule_result"]
        floor = e["floor"]
        for i, h in enumerate(rr.get("held") or []):
            cls, cause, end = classify(h)
            u = (u_over or {}).get(e["element_id"], rr.get("upper_m2"))
            ce = component_end(cls, end, floor, h, u if cls == "DROP" else None)
            by.setdefault(lid, []).append({
                "id": f"{e['element_id']}#{i}", "wall": e["element_id"], "state": e["action"], "class": cls,
                "cause": cause, "length_m": str(piece_length(h)) if piece_length(h) is not None else None,
                "held_text": h[:200], "end": ce})
    return by


def census(idx70, t696, t670):
    rows = []
    t696_by = {r["line_id"]: r for r in t696["rows"]}
    t670_by = {r["material_line_id"]: r for r in t670["rows"] if "material_line_id" in r}
    for ln in sorted(idx70["lines"], key=lambda r: (r["item_code"], r["element_id"])):
        if not ln["item_code"].startswith("MAS.") or ln["class"] == "RELEASED":
            continue
        row = {"line_id": ln["line_id"], "item_code": ln["item_code"], "unit": ln["unit"], "host": ln["element_id"],
               "class": ln["class"], "held_low": ln["held_low"], "held_high": ln["held_high"]}
        if ln["class"] == "EXCLUDED":
            row.update(state="NOT_APPLICABLE", cause_class="NOT APPLICABLE",
                       cause="black block below N.G. (ST p.1 note 2; R-T675-1): no AAC material")
        elif ln["item_code"] == "MAS.BLOCK":
            row.update(state="HELD blank", cause_class="HOST", cause="see parents / T-696 hosts")
        elif ln["held_low"] is not None:
            row["state"] = "HELD bounded"
            if ln["item_code"] == "MAS.MORTAR.BLACK.LINTEL_BEARING":
                row.update(cause_class="DESIGNER ITEM", cause="built bearing at a FLAGGED_DEFICIT lintel end (T-675 "
                           "R-T675-2; DESIGNER_QUESTIONS row 2)" if ln["held_low"] > 0 else
                           "D-1F-09 lintel in the east dome piece (D-42; T-675)")
            elif ln["item_code"] == "MAS.MORTAR.BLACK.PERIMETER":
                row.update(cause_class="DESIGNER ITEM", cause="lintel-deficit / dome-piece junction bands and range "
                           "block ends (T-520 / T-675 R-T675-3; D-42, DESIGNER_QUESTIONS row 2)")
            else:
                r670 = t670_by.get(ln["line_id"])
                held = [x["opening_id"] for x in (r670 or {}).get("lintels", []) if x["kind"] == "HELD_RANGE"]
                row.update(cause_class="DESIGNER ITEM", cause="HELD lintel faces in the host (0 .. face each): "
                           + (", ".join(held) if held else "D-1F-09 (dome piece, D-42)")
                           + " (lintel lines held: DESIGNER_QUESTIONS row 2 / T-704)")
        else:
            r = t696_by.get(ln["line_id"])
            if r is None:
                raise SystemExit(f"{ln['line_id']}: a blank material line T-696 did not census")
            row.update(state="HELD blank", cause_class=r["cause_class"], cause=r["cause"][:240],
                       host_line_id=r["host_line_id"], t696_beside=r["beside"])
        rows.append(row)
    return rows


def build(candidate=None):
    for p, want in PINS.items():
        if not _sha(p).startswith(want):
            raise SystemExit(f"{p.name}: sha256 {_sha(p)[:8]} is not {want}")
    idx70, idx68 = _load(IDX70), _load(IDX68)
    if not idx70["inputs"]["lines"].startswith(LINES70_SHA):
        raise SystemExit("line index is not the V3.0.70 run of record")
    m70 = {r["line_id"]: r for r in idx70["lines"] if r["item_code"].startswith("MAS.")}
    m68 = {r["line_id"]: r for r in idx68["lines"] if r["item_code"].startswith("MAS.")}
    if m70 != m68:
        raise SystemExit("MAS lines differ V3.0.68 -> V3.0.70: the T-696 census does not carry over")
    rows = census(idx70, _load(T696), _load(T670))
    blk = {k: v for k, v in m70.items() if v["item_code"] == "MAS.BLOCK"}
    comps = parents(_load(REG), blk, drop_u_overrides(_load(T482)))
    rb = _load(RB)
    pres = {}
    for lid, cs in sorted(comps.items()):
        b = parent_bound(cs)
        t = blk[lid]["element_id"].split("t=")[1]
        mats = {}
        for r in idx70["lines"]:
            if r["item_code"].startswith("MAS.") and r["item_code"] != "MAS.BLOCK" and r["class"] == "HELD" \
                    and r["element_id"].replace("MATERIAL:", "").replace("#PERIMETER_JOINT", "") \
                    == blk[lid]["element_id"]:
                mats[r["line_id"]] = dict(code=r["item_code"], **material_follow(
                    b, r["item_code"], t, glue_rate(rb, t) if r["item_code"] == "MAS.GLUE.AAC" else None))
        by_cls = {}
        for c in cs:
            s = by_cls.setdefault(c["class"], {"components": 0, "length_m": BR.D(0), "upper_m2": BR.D(0),
                                               "cause": c["cause"]})
            s["components"] += 1
            if c["length_m"]:
                s["length_m"] = BR.add(s["length_m"], c["length_m"])
            if c["end"]["upper"] is not None:
                s["upper_m2"] = BR.add(s["upper_m2"], c["end"]["upper"])
        pres[lid] = {"host": blk[lid]["element_id"], "bound": b, "components": [
            dict(c, end={k: (str(v) if hasattr(v, "as_tuple") else v) for k, v in c["end"].items()}) for c in cs],
            "by_class": {k: dict(v, length_m=str(v["length_m"]), upper_m2=str(v["upper_m2"])) for k, v in
                         by_cls.items()}, "materials": mats}
    missing = [k for k, v in blk.items() if v["class"] == "HELD" and "#" not in v["element_id"]
               and not v["element_id"].startswith("HOUSE_BELOW_NG") and k not in pres]
    if missing:
        raise SystemExit(f"parents with no register components: {missing}")
    items = {}
    for lid, p in pres.items():
        for c in p["components"]:
            s = items.setdefault(c["class"], {"cause": c["cause"], "blocks_parents": set(), "components": 0,
                                              "length_m": BR.D(0)})
            s["components"] += 1
            if c["length_m"]:
                s["length_m"] = BR.add(s["length_m"], c["length_m"])
            if c["end"]["upper"] is None:
                s["blocks_parents"].add(lid)
    by_item = {k: dict(v, blocks_parents=sorted(v["blocks_parents"]), length_m=str(v["length_m"]))
               for k, v in sorted(items.items())}
    counts = {}
    for x in rows:
        k = (x["item_code"], x["state"])
        counts[f"{k[0]} | {k[1]}"] = counts.get(f"{k[0]} | {k[1]}", 0) + 1
    out = {"schema": "T713_MASONRY_REST_V1", "candidate": "ARCH_TAKEOFF_V3.0.70", "line_index": LINES70_SHA,
           "rule": f"{RULE_ID} {METHOD} {RULE_VERSION}", "counts": counts, "census": rows, "parents": pres, "by_cause_item": by_item,
           "plate_tops": PLATE_TOP, "pins": {str(p.relative_to(ROOT)): _sha(p)[:8] for p in PINS}}
    if candidate:
        out["candidate_check"] = check_candidate(pres, candidate)
    return out


def check_candidate(pres, path):
    """every parent on the private V3.0.70 run: still blank, and every register wall named in its question text."""
    data = _load(path)
    lines = data["lines"] if isinstance(data, dict) else data
    by = {ln["line_id"]: ln for ln in lines}
    res = {}
    for lid, p in pres.items():
        ln = by[lid]
        txt = json.dumps({k: ln.get(k) for k in ("rfi", "notes", "calculation")}, ensure_ascii=False)
        walls = sorted({c["wall"] for c in p["components"]})
        res[lid] = {"blank": ln.get("measured_net") is None and not ln.get("bounded_range"),
                    "walls_named": [w for w in walls if w.split(" + ")[0] in txt],
                    "walls_not_named": [w for w in walls if w.split(" + ")[0] not in txt],
                    "other_walls_named": sorted(set(re.findall(r"\b[G12]F-[WH]\d\d\b", txt)) -
                                                {x for w in walls for x in w.split(" + ")})}
    return {"file_sha256": _sha(path)[:8], "parents": res}


if __name__ == "__main__":
    cand = sys.argv[sys.argv.index("--candidate") + 1] if "--candidate" in sys.argv else None
    doc = build(cand)
    if "--json" in sys.argv:
        Path(sys.argv[sys.argv.index("--json") + 1]).write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n",
                                                                 encoding="utf-8")
    print(json.dumps(doc["counts"], indent=1))
    for lid, p in doc["parents"].items():
        b = p["bound"]
        print(lid[:10], p["host"], b["kind"], b.get("printed_m2", ""), "blocking", len(b["blocking_components"]),
              "of", len(p["components"]))
        for k, v in p["by_class"].items():
            print("    ", k, v["components"], "L", v["length_m"], "U", v["upper_m2"])
        for m, v in p["materials"].items():
            print("    mat", m[:10], v["code"][4:], v["kind"], v.get("printed", ""))
    if "candidate_check" in doc:
        print(json.dumps(doc["candidate_check"], indent=1))
