"""ALSENAN S3 - column reinforcement through the GENERIC engine (engine/source/column_rebar.py).

Project adapter only: it reads the frozen S1 census and the S2 flags by sha256, records the project claims and evidence
given by Mohammad (PROJECT_ONLY), maps the census into the engine's generic segment shape and writes the registers.
Every Alsenan value (storey heights, tie rule, cover, bands, claims) is read from the registers here and passed in as
data - nothing project-specific lives in the engine.

Benchmark firewall: no external comparison total and no per-volume allowance is read in this round.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
S1 = ROOT / "research" / "alsenan_structural_census_s1"
S2 = ROOT / "research" / "alsenan_structural_s2"
R4 = ROOT / "research" / "alsenan_rebar_source_exhaustion_04" / "registers"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(S2))

from engine.source import column_rebar as CR  # noqa: E402
from engine.source import engineering_flags as EF  # noqa: E402
from engine.source import project_claims as PC  # noqa: E402
import build_flags_s2 as S2A  # noqa: E402

PROJECT_ID = S2A.PROJECT_ID
REVISION = S2A.REVISION
CONTEXT = {"project_id": PROJECT_ID, "drawing_revision": REVISION}
STOREYS = ["FOUNDATION", "GF", "1F", "2F"]
STOREY_BAND = {"FOUNDATION": "FOU", "GF": "GR", "1F": "1ST", "2F": "2ND"}
CLAIM_DATE = "2026-10-06"
CLAIM_PERSON = "Mohammad (Urban Projects)"
S1_USED = ["COLUMN_OCCURRENCE_REGISTER", "COLUMN_VERTICAL_CHAIN_REGISTER", "COLUMN_DEFINITION_REGISTER",
           "COLUMN_TIE_TOPOLOGY_RULES", "STRUCTURAL_LEVEL_REGISTER", "STRUCTURAL_PROJECT_RULE_REGISTER",
           "BEAM_OCCURRENCE_REGISTER", "BEAM_DEFINITION_REGISTER", "FOOTING_OCCURRENCE_REGISTER",
           "FOOTING_DEFINITION_REGISTER", "SLAB_PANEL_REGISTER", "SPECIAL_STRUCTURAL_OCCURRENCE_REGISTER"]
R4_USED = ["PROJECT_REBAR_RULE_REGISTER.json"]


def sha(b):
    return hashlib.sha256(b).hexdigest()


# ================================================================================================ load (hash-checked)
def load():
    idx, regs = S2A.load_s1()                                      # raises if any S1 register moved
    s2_idx = json.loads((S2 / "INDEX.json").read_text(encoding="utf-8"))
    raw = (S2 / "ALSENAN_ENGINEERING_FLAGS.json").read_bytes()
    if sha(raw) != s2_idx["outputs"]["ALSENAN_ENGINEERING_FLAGS.json"]:
        raise SystemExit("S2 flags do not match the frozen S2 index")
    s2_flags = json.loads(raw)["flags"]
    r4 = {}
    for f in R4_USED:
        b = (R4 / f).read_bytes()
        r4[f] = (json.loads(b), sha(b))
    return idx, regs, s2_idx, s2_flags, r4


def rows(regs, name):
    return regs[name]["rows"]


# ================================================================================================ claims + evidence
def find_flag(flags, detector, fact):
    hit = [f for f in flags if f["detector"] == detector and fact in f["affected_facts"]]
    if len(hit) != 1:
        raise SystemExit(f"expected one {detector}/{fact} flag, found {len(hit)}")
    return hit[0]


def claims_and_evidence(flags, regs):
    rate = find_flag(flags, "transverse_rules", "transverse_count")
    gap = find_flag(flags, "band_gaps", "transverse_arrangement")
    gap_L = float(gap["source_b"]["value"].split()[0])                     # "80.0 cm" (S2 flag text)
    band_above = next(b for b in rows(regs, "COLUMN_TIE_TOPOLOGY_RULES") if b["closed_ties_in_section"] == 3)
    claims = [
        PC.make_claim(project_id=PROJECT_ID, claim_id="ALS-S3-CLAIM-001", kind=PC.ADJUDICATION,
                      fact="TIE_RATE_SEMANTICS", value=CR.SETS_PER_M, source_person=CLAIM_PERSON, date=CLAIM_DATE,
                      drawing_revision=REVISION, flag_keys=[rate["flag_key"]],
                      scope_note="'ST. OF COLUMN- 6Ø8/m' = six complete tie levels (sets) per metre: 1 link per "
                                 "level -> 6 links/m, 2 -> 12 links/m, 3 -> 18 links/m. Applies to this project's "
                                 "tie rule only; not a generic reading of 'n Ø d/m'."),
        PC.make_claim(project_id=PROJECT_ID, claim_id="ALS-S3-CLAIM-002", kind=PC.ADJUDICATION,
                      fact="TIE_TOPOLOGY_BAND", value={"long_side_mm": int(round(gap_L * 10)),
                                                       "band_id": band_above["band_id"]},
                      source_person=CLAIM_PERSON, date=CLAIM_DATE, drawing_revision=REVISION,
                      flag_keys=[gap["flag_key"]],
                      scope_note="A column whose long side is exactly on the printed limit between the 2-link and "
                                 "3-link bands uses the 3-link arrangement on this project. Generic code keeps the "
                                 "RULE_GAP for any other project, revision or value."),
    ]
    occ = rows(regs, "COLUMN_OCCURRENCE_REGISTER")
    ch = {c["chain_id"]: c for c in rows(regs, "COLUMN_VERTICAL_CHAIN_REGISTER")}
    cn = [o for o in occ if o["column_type"] == "CN"]
    on_cap = [o for o in cn if "CAP" in ch[o["chain_id"]]["members_by_sheet"]]
    on_fp = [o for o in cn if "FP" in ch[o["chain_id"]]["members_by_sheet"]]
    evidence = [
        {"evidence_id": "ALS-S3-EV-001", "kind": "HUMAN_VERIFICATION", "source_person": CLAIM_PERSON,
         "date": CLAIM_DATE, "drawing_revision": REVISION, "promotion_state": "PROJECT_ONLY",
         "statement": "All column-type counts in the S1 census were checked manually and accepted.",
         "census_check": dict(Counter(o["column_type"] for o in occ)), "engine_logic": False},
        {"evidence_id": "ALS-S3-EV-002", "kind": "HUMAN_VERIFICATION", "source_person": CLAIM_PERSON,
         "date": CLAIM_DATE, "drawing_revision": REVISION, "promotion_state": "PROJECT_ONLY",
         "statement": "The axis / column plan shows 5 CN and the foundation plan shows 6 CN. This does not mean six "
                      "CN continue upward: the sixth CN is a foundation-level occurrence unless a source says "
                      "otherwise.",
         "census_check": {"CN_on_axis_plan": len(on_cap), "CN_on_foundation_plan": len(on_fp),
                          "CN_occurrences_by_floor": dict(Counter(o["floor"] for o in cn)),
                          "CN_continuing_above": sum(1 for o in cn if o["continues_above"])},
         "agrees_with_census": len(on_cap) == 5 and len(on_fp) == 6 and all(o["floor"] == "FOUNDATION" for o in cn)
         and not any(o["continues_above"] for o in cn), "engine_logic": False},
    ]
    return claims, evidence


# ================================================================================================ project inputs
def nearest(fr, xs):
    return min(range(len(xs)), key=lambda i: abs(xs[i] - fr))


def topology_bands(regs):
    """Bands from the S1 tie-topology register. Each link's bar range (per long face, in the detail's own indices) is
    read from the detail sketch: the drawn link ends snap to the nearest drawn bar of the evenly drawn bar line."""
    t = regs["COLUMN_TIE_TOPOLOGY_RULES"]
    lim = {b["band_id"]: b for b in t["band_limits"]}
    out = []
    for r in t["rows"]:
        b = lim[r["band_id"]]
        k = r["bars_per_long_face_drawn"]
        offs, spans = r["tie_offsets_as_fraction_of_L"], r["tie_spans_as_fraction_of_L"]
        a = min(offs)
        z = max(o + s for o, s in zip(offs, spans))
        xs = [a + i * (z - a) / (k - 1) for i in range(k)]
        links = [{"bar_range": [nearest(o, xs), nearest(o + s, xs)]} for o, s in zip(offs, spans)]
        topo = {1: CR.ONE_LINK, 2: CR.TWO_OVERLAPPING_LINKS}.get(r["closed_ties_in_section"], CR.MULTI_LINK_SET)
        out.append({"band_id": r["band_id"], "printed": b["printed"],
                    "lo_mm": None if b["lo"] is None else b["lo"] * 10, "lo_incl": b["lo_incl"],
                    "hi_mm": None if b["hi"] is None else b["hi"] * 10, "hi_incl": b["hi_incl"],
                    "topology": topo, "drawn_bars_per_face": k, "links": links,
                    "source_ref": {"drawing": "ST7757.dxf", "page": 9, "tie_handles": r["tie_handles"],
                                   "sketch_handles": r["sketch_handles"]},
                    "reading": "link bar ranges from the detail sketch (topology only); link dimensions are "
                               "derived from section, cover and bar positions, not from sketch proportions"})
    return out


def project_inputs(regs, r4, claims):
    rules = {r["rule_id"]: r for r in rows(regs, "STRUCTURAL_PROJECT_RULE_REGISTER")}
    ties, dev, ftg = rules["P9-COL-TIES"], rules["P8-N09"], rules["P13-FOOTING-TYP"]
    r4rules = {r["rule_id"]: r for r in r4["PROJECT_REBAR_RULE_REGISTER.json"][0]["rules"]}
    cov = next(r for r in r4rules.values() if "COLUMN" in r["applies_to"])
    soil = next(r for r in r4rules.values() if "COLUMN_STARTERS" in r["applies_to"])
    foot_cm = int(re.search(r"Min\. (\d+)cm", ftg["raw_text"]).group(1))
    proj_d = int(re.search(r"(\d+)Ø", ftg["raw_text"]).group(1))
    return {
        "context": dict(CONTEXT), "steel_density_kg_m3": 7850,
        "tie_rule": {"rule_id": ties["rule_id"], "dia_mm": ties["values"]["dia_mm"],
                     "rate_per_m": ties["values"]["per_m"], "per_metre_semantics": CR.UNRESOLVED,
                     "raw": ties["raw_text"], "source_ref": {"page": ties["page"], "handles": ties["dxf_handles"]},
                     "zones": [{"zone_id": "UNIFORM", "rate_per_m": ties["values"]["per_m"], "length_mm": None}]},
        "topology_bands": topology_bands(regs),
        "bar_arrangement": {"method": "CORNERS_PLUS_LONG_FACES",
                            "authority": "p.9 detail sketches draw bars on the long faces only (corner + long-face "
                                         "bars); internal bar positions by equal spacing (method)"},
        "cover": {"rule_id": cov["rule_id"], "cover_mm": cov["value"], "source_ref": cov["claim_id"],
                  "authority": cov["source_state"]},
        "lap_rule": {"rule_id": dev["rule_id"], "state": "UNRESOLVED", "current_D": dev["values"]["compression_D"],
                     "alternatives_D": [dev["values"]["tension_D"]],
                     "why": "the printed note gives starter development 40D (compression) / 70D (tension); column "
                            "splice laps take the compression value provisionally"},
        "anchorage_rule": {"rule_id": dev["rule_id"], "state": "UNRESOLVED",
                           "current_D": dev["values"]["compression_D"], "alternatives_D": [dev["values"]["tension_D"]],
                           "why": "no top-anchorage / planted-column anchorage length printed; development length of "
                                  "the same note used provisionally"},
        "starter_rule": {"rule_id": ftg["rule_id"], "state": ftg["status"], "foot_mm": foot_cm * 10,
                         "projection_D": proj_d, "bottom_cover_mm": soil["value"],
                         "bottom_cover_rule": soil["rule_id"]},
        "hook_method": {"method_id": "URBAN-PROV-HOOK135-6D-75", "extension_d": 6, "min_extension_mm": 75,
                        "hooks_per_link": 2, "authority": "URBAN_FALLBACK (ACI 318 135-degree tie hook) - "
                                                          "PROVISIONAL_ENGINEERING_METHOD, not printed on ST7757"},
        "claims": claims}


# ================================================================================================ segments
def gb_depth_mm(defn):
    m = re.search(r"(\d+)\s*x\s*(\d+)", defn.get("normalized_rule") or "")
    return int(m.group(2)) * 10 if m else None


def framing(regs):
    """Members framing each column member, by plan sheet, from the beam supports (S1 refs 'sheet:handle')."""
    chains = rows(regs, "COLUMN_VERTICAL_CHAIN_REGISTER")
    mem = {f"{s}:{h}": c["chain_id"] for c in chains for s, h in c["members_by_sheet"].items()}
    bdef = {d["beam_type"]: d for d in rows(regs, "BEAM_DEFINITION_REGISTER")}
    out = defaultdict(list)
    for b in rows(regs, "BEAM_OCCURRENCE_REGISTER"):
        for k in ("start_support", "end_support"):
            for x in (b.get(k) or {}).get("refs", []):
                if x["kind"] == "COLUMN" and x["ref"] in mem:
                    d = bdef.get(b.get("beam_type"), {})
                    depth = d.get("H_cm") * 10 if d.get("H_cm") else gb_depth_mm(d)
                    out[(mem[x["ref"]], b["sheet"])].append({"beam_id": b["beam_id"], "beam_type": b.get("beam_type"),
                                                             "depth_mm": depth, "binding": b.get("binding")})
    max_sched = max(d["H_cm"] * 10 for d in bdef.values() if d.get("H_cm") and d.get("state") == "DEFINED")
    return out, max_sched


def clear_zone(chain_id, sheet, fr, max_sched, slab_max):
    beams = fr.get((chain_id, sheet), [])
    if not beams:
        if sheet in slab_max:
            return {"framing_depth_mm": slab_max[sheet], "state": CR.BOUNDED, "framing": [],
                    "basis": f"no framing beam bound - thickest slab on {sheet} ({slab_max[sheet]} mm)"}
        return {"framing_depth_mm": None, "state": CR.BLOCKED, "framing": [],
                "basis": f"no framing member bound on {sheet}"}
    unknown = [b for b in beams if b["depth_mm"] is None]
    if unknown and any((b["beam_type"] or "").startswith("GB_EXTERIOR") for b in unknown):
        return {"framing_depth_mm": None, "state": CR.BLOCKED, "framing": beams,
                "basis": "exterior ground beam depth 'FOLLOW ARCH' not dimensioned"}
    known = [b["depth_mm"] for b in beams if b["depth_mm"] is not None]
    if unknown:
        return {"framing_depth_mm": max(known + [max_sched]), "state": CR.BOUNDED, "framing": beams,
                "basis": f"{len(unknown)} framing member(s) of unknown depth bounded by the deepest scheduled beam "
                         f"({max_sched} mm)"}
    return {"framing_depth_mm": max(known), "state": CR.ESTABLISHED, "framing": beams,
            "basis": f"deepest framing beam on {sheet} ({max(known)} mm, FFL-to-FFL basis)"}


def footing_of(regs):
    fo = regs["FOOTING_OCCURRENCE_REGISTER"]
    fdef = {d["footing_type"]: d for d in rows(regs, "FOOTING_DEFINITION_REGISTER")}
    by = {}
    for r in fo["rows"]:
        by[r["outline"]["handle"]] = r
        by[r["outline"].get("via")] = r
    out = {}
    for chain, fs in fo["column_to_footing"].items():
        recs = []
        for x in fs:
            r = by.get(x.split(":", 1)[1])
            if r is None:
                recs.append({"ref": x, "depth_mm": None, "state": "UNRESOLVED_FOOTING"})
                continue
            types = r.get("candidate_types") or [r["type"]]
            ds = sorted({fdef[t]["D_cm"] * 10 for t in types if t in fdef})
            recs.append({"ref": r["footing_id"], "types": types, "depths_mm": ds,
                         "depth_mm": ds[0] if len(ds) == 1 else None,
                         "max_depth_mm": ds[-1] if ds else None,
                         "state": "DEFINED" if len(ds) == 1 else "TYPE_CONFLICT"})
        out[chain] = recs
    max_any = max(d["D_cm"] * 10 for d in fdef.values() if d.get("D_cm"))
    return out, max_any


def definition(o):
    return {"B_mm": int(round(o["schedule_section_cm"][0] * 10)), "D_mm": int(round(o["schedule_section_cm"][1] * 10)),
            "bars": {"count": o["longitudinal_bars"]["count"], "dia_mm": o["longitudinal_bars"]["dia_mm"]}}


def def_from_row(row):
    return {"B_mm": int(round(row["B_cm"] * 10)), "D_mm": int(round(row["D_cm"] * 10)),
            "bars": {"count": row["longitudinal_bars"]["count"], "dia_mm": row["longitudinal_bars"]["dia_mm"]}}


def candidate_sections(o, flags, defs, fl):
    """Every definition the occurrence may take: its census definition and, under a type conflict, each candidate's."""
    out = [definition(o)]
    for f in flags:
        if f["detector"] == "type_conflicts" and o["column_id"] in f["element_ids"]:
            for t in (f["source_a"]["value"], f["source_b"]["value"]):
                r2, _ = CR.schedule_row(defs, t, fl, STOREY_BAND)
                if r2:
                    out.append(def_from_row(r2))
    return out


def build_segments(regs, flags):
    occ = rows(regs, "COLUMN_OCCURRENCE_REGISTER")
    defs = rows(regs, "COLUMN_DEFINITION_REGISTER")
    lv = regs["STRUCTURAL_LEVEL_REGISTER"]
    iv = {i["storey"]: i for i in lv["intervals"]}
    lvl = {r["level"]: r for r in lv["rows"]}
    found_max = lvl["FOUNDATION"]["bound_m"]["max"]
    gf_ffl = iv["GF"]["lower_ffl_m"]
    closing = {s: iv[s].get("closing_slab_sheet") for s in STOREYS}
    closing["FOUNDATION"] = "GBP"                                    # the ground-beam plan closes the foundation storey
    fr, max_sched = framing(regs)
    slab_max = defaultdict(int)
    for p in rows(regs, "SLAB_PANEL_REGISTER"):
        if p.get("effective_thickness_mm") and p["sheet"] in ("GFRS", "FFRS", "SFRS"):
            slab_max[p["sheet"]] = max(slab_max[p["sheet"]], p["effective_thickness_mm"])
    ftg, max_ftg = footing_of(regs)
    aliases = defaultdict(list)
    turned = {}
    for s in rows(regs, "SPECIAL_STRUCTURAL_OCCURRENCE_REGISTER"):
        if s.get("bound_chain"):
            aliases[s["bound_chain"]].append(s["special_id"])
            if s["kind"] == "TURN_COLUMN":
                turned[s["bound_chain"]] = s
    rules = {r["rule_id"]: r for r in rows(regs, "STRUCTURAL_PROJECT_RULE_REGISTER")}
    tie_rule_id = next(r["rule_id"] for r in rules.values() if r.get("topic") == "COLUMN_TIES"
                       and (r.get("values") or {}).get("per_m"))
    by_chain = defaultdict(dict)
    for o in occ:
        by_chain[o["chain_id"]][o["floor"]] = o
    segs, joins = [], []
    for o in sorted(occ, key=lambda x: (STOREYS.index(x["floor"]), x["column_id"])):
        cid, fl = o["chain_id"], o["floor"]
        si = STOREYS.index(fl)
        ids = {o["column_id"], cid} | set(aliases[cid])
        fk = [f["flag_key"] for f in flags if ids & set(f["element_ids"])]
        # a rule-scoped flag (subject = the column tie rule) covers every column governed by that rule
        for g in flags:
            if g["detector"] == "transverse_rules" and str(g["element_id"]).startswith(tie_rule_id + ":") \
                    and g["flag_key"] not in fk:
                fk.append(g["flag_key"])
        # a band-gap flag is scoped by VALUE (the uncovered limit): a candidate section with that long side is in it
        for g in flags:
            if g["detector"] == "band_gaps" and g["flag_key"] not in fk:
                gap_mm = int(round(float(g["source_b"]["value"].split()[0]) * 10))
                if any(max(c["B_mm"], c["D_mm"]) == gap_mm
                       for c in candidate_sections(o, flags, defs, fl)):
                    fk.append(g["flag_key"])
        conflict = [f for f in flags if f["detector"] == "type_conflicts" and ids & set(f["element_ids"])]
        res_def = definition(o)
        row, row_state = CR.schedule_row(defs, o["column_type"], fl, STOREY_BAND)
        join_ok = row is None or def_from_row(row) == res_def
        cands = [{"type": o["column_type"], "definition": res_def, "source": "S1 occurrence (census join)",
                  "schedule_row": None if row is None else row["definition_id"]}]
        if conflict:
            f = conflict[0]
            corr = {e["value"] for e in f["context"].get("supporting_evidence", [])}
            cands = []
            for t in (f["source_a"]["value"], f["source_b"]["value"]):
                r2, st2 = CR.schedule_row(defs, t, fl, STOREY_BAND)
                if r2 is None:
                    continue
                cands.append({"type": t, "definition": def_from_row(r2), "schedule_row": r2["definition_id"],
                              "corroborated": t in corr and len(corr) == 1,
                              "source": f"{'axis' if t == f['source_a']['value'] else 'ground-beam'} plan tag"})
        # interval
        if fl == "FOUNDATION":
            fs = ftg.get(cid) or []
            d = [x.get("depth_mm") if x.get("depth_mm") is not None else x.get("max_depth_mm") for x in fs]
            d = [x for x in d if x is not None]
            dep = max(d) if d else max_ftg
            interval = {"length_mm": int(round((gf_ffl - found_max) * 1000)) - dep,
                        "state": CR.BOUND_LOWER if d else CR.BOUNDED,
                        "basis": f"GF FFL {gf_ffl:+.2f} m minus founding level <= {found_max:.2f} m minus footing "
                                 f"depth {dep} mm ({'bound footing' if d else 'deepest scheduled footing - unbound'})"}
        else:
            interval = {"length_mm": int(round(iv[fl]["floor_to_floor_m"] * 1000)), "state": CR.ESTABLISHED,
                        "basis": f"printed floor-to-floor {iv[fl]['floor_to_floor_m']} m (FFL basis)"}
        cz = clear_zone(cid, closing[fl], fr, max_sched, slab_max)
        # below / above
        if fl == "FOUNDATION":
            fs = ftg.get(cid) or []
            one = fs[0] if len(fs) == 1 else None
            below = {"kind": "FOOTING", "footing": {"depth_mm": one["depth_mm"] if one else None,
                                                    "ref": one["ref"] if one else [x["ref"] for x in fs],
                                                    "state": one["state"] if one else "NO_SINGLE_FOOTING"}}
        elif o.get("planted_on"):
            below = {"kind": "PLANTED_SUPPORT", "on": o["planted_on"]}
        else:
            below = {"kind": "COLUMN"}
        up = by_chain[cid].get(STOREYS[si + 1]) if si + 1 < len(STOREYS) else None
        above = {"exists": bool(o["continues_above"] and up)}
        if above["exists"]:
            above["bars"] = definition(up)["bars"]
            upc = [f for f in flags if f["detector"] == "type_conflicts" and up["column_id"] in f["element_ids"]]
            if upc:
                bb = {}
                for t in (upc[0]["source_a"]["value"], upc[0]["source_b"]["value"]):
                    r2, _ = CR.schedule_row(defs, t, up["floor"], STOREY_BAND)
                    if r2:
                        bb[t] = def_from_row(r2)["bars"]
                above["bars_by_candidate"] = bb
        extras = []
        tc = turned.get(cid)
        if tc and tc["source_id"].split(":")[1] == closing[fl]:
            r = rules[tc["rule"]]
            extras.append({"extra_id": "TURN_EXTRA_BARS", "count": 4, "dia_mm": 16, "length_mm": 2000,
                           "state": CR.PROVISIONAL, "rule_id": r["rule_id"],
                           "why": f"{r['raw_text']} - 4 extra bars over 1 m above + 1 m below the turn "
                                  f"({r['status']} detail)"})
            extras.append({"extra_id": "TURN_SPIRAL", "count": None, "dia_mm": 8, "length_mm": None,
                           "state": CR.BLOCKED, "rule_id": r["rule_id"],
                           "why": "spiral stirrups 6Ø8/m over 2 x 1 m - spiral diameter / pitch geometry not "
                                  "dimensioned"})
        alt = []
        if o["drawn_vs_schedule"] == "MISMATCH" and o.get("drawn_section_cm"):
            ds = sorted(o["drawn_section_cm"])
            alt.append({"label": "DRAWN", "B_mm": int(round(ds[0] * 10)), "D_mm": int(round(ds[1] * 10))})
        segs.append({"segment_id": f"SEG-{o['column_id']}", "occurrence_id": o["column_id"], "chain_id": cid,
                     "floor": fl, "storey_index": si, "resolved_type": o["column_type"], "candidates": cands,
                     "interval": interval, "clear_zone": cz, "above": above, "below": below, "extras": extras,
                     "flag_keys": fk, "conflict_flag_keys": [f["flag_key"] for f in conflict],
                     "element_aliases": aliases[cid], "section_alternatives": alt,
                     "grid": o["grid"], "plan_centre_mm": o["plan_centre_mm"], "orientation": o["orientation"]})
        joins.append({"occurrence_id": o["column_id"], "schedule_row": None if row is None else row["definition_id"],
                      "row_state": row_state, "join_matches_census": join_ok})
    return segs, joins


# ================================================================================================ run
def run():
    idx, regs, s2_idx, s2_flags, r4 = load()
    claims, evidence = claims_and_evidence(s2_flags, regs)
    flags_c, log = PC.apply_to_flags(s2_flags, claims, project_id=PROJECT_ID, drawing_revision=REVISION,
                                     at=CLAIM_DATE)
    P = project_inputs(regs, r4, claims)
    segs, joins = build_segments(regs, flags_c)
    occ_ids = [o["column_id"] for o in rows(regs, "COLUMN_OCCURRENCE_REGISTER")]
    res1 = CR.evaluate(segs, P, flags_c, expected_occurrences=occ_ids)
    where = {
        "TIE_ZONE_METHOD_REQUIRED": "ST7757 p.9 'ST. OF COLUMN- 6Ø8/m' (handle 1BAA) and the column details; beam "
                                    "schedules p.10-12 for beam depths",
        "END_LEVEL_COUNT_METHOD_REQUIRED": "ST7757 p.9 'ST. OF COLUMN- 6Ø8/m' (handle 1BAA)",
        "HOOK_METHOD_REQUIRED": "ST7757 p.9 column tie details (handles 1BAB, 1BBA, 1BBF, 1BB6, 1BD3, 1BDA)",
        "LAP_METHOD_REQUIRED": "ST7757 p.8 general note 9 (development length 70D / 40D); p.13 footing detail "
                               "(40Ø); p.15 planted-column detail",
        "TIE_TOPOLOGY_RULE_GAP": "ST7757 p.9 band conditions"}
    col_s2 = [f for f in flags_c if f["element_type"] == "COLUMN"]
    new, sup, q = CR.method_flags(res1, P, col_s2, where=where)
    sup_keys = {f["flag_key"] for f in sup}
    last = max(int(f["flag_id"].split("-")[-1]) for f in col_s2)
    for i, f in enumerate(sorted(new, key=lambda f: f["context"]["s3_kind"]), start=1):
        f["flag_id"] = f"STR-COL-{last + i:03d}"
    final_flags = [f for f in flags_c if f["flag_key"] not in sup_keys] + sup + new
    res = CR.evaluate(segs, P, final_flags, expected_occurrences=occ_ids)
    return {"idx": idx, "regs": regs, "s2_idx": s2_idx, "r4": r4, "claims": claims, "evidence": evidence,
            "claim_log": log, "P": P, "segs": segs, "joins": joins, "res": res, "flags": final_flags,
            "new_flags": new, "superseded": sup, "q": q}


# ================================================================================================ registers
def r3(x):
    return None if x is None else round(x, 3)


def sum_kg(parts, pred=lambda p: True):
    return sum(p["kg"] for p in parts if p["kg"] is not None and pred(p))


def bucket_kg(parts):
    b = {k: 0.0 for k in ("verified", "lower_bound", "provisional", "blocked")}
    for p in parts:
        if p["kg"] is not None:
            b[CR.BUCKET[p["release_state"]]] += p["kg"]
    return {k: r3(v) for k, v in b.items()}


def flag_view(flags):
    return {f["flag_key"]: f for f in flags}


def quantify_s2_flags(R):
    """kg view of the S2 column flags that touch reinforcement (copies; S2 outputs are not modified)."""
    res, P = R["res"], R["P"]
    by_seg = {r["segment"]["segment_id"]: r for r in res["segments"]}
    out = {}
    for f in R["flags"]:
        if f["element_type"] != "COLUMN":
            continue
        parts = [p for p in res["parts"] if f["flag_key"] in p["flags"]]
        cur = sum_kg(parts, lambda p: p["release_state"] != CR.BLOCKED)
        q = {"parts": len(parts), "kg_in_flagged_parts": r3(sum_kg(parts)), "current_released_kg": r3(cur)}
        if f["detector"] == "type_conflicts":
            alt = defaultdict(float)
            for p in parts:
                for t, v in (p.get("alternatives_kg") or {}).items():
                    alt[t] += v or 0.0
            q["kg_by_candidate"] = {t: r3(v) for t, v in alt.items()}
            q["shared_lower_bound_kg"] = r3(sum_kg(parts, lambda p: p.get("conflict_shared")))
            q["differing_kg_by_candidate"] = {t: r3(sum((p.get("alternatives_kg") or {}).get(t) or 0
                                                        for p in parts if not p.get("conflict_shared")))
                                              for t in alt}
            q["likely_candidate"] = next((p.get("likely_type") for p in parts if p.get("likely_type")), None)
            cur_t = q["likely_candidate"] or next(iter(sorted(alt)), None)
            for p in parts:
                if p.get("likely_type") is None:
                    cur_t = p["candidate_type"]
                    break
            others = [t for t in alt if t != cur_t]
            q["current_kg"] = q["kg_by_candidate"].get(cur_t)
            q["current_basis"] = f"candidate {cur_t} ({'likely - corroborated' if q['likely_candidate'] else 'census reading'})"
            q["alternative_kg"] = q["kg_by_candidate"].get(others[0]) if others else None
            q["alternative"] = f"candidate {others[0]}" if others else None
            q["quantity_affected_kg"] = q["differing_kg_by_candidate"].get(cur_t)
        if f["detector"] in ("section_overrides", "minimum_shortfalls"):
            sched = drawn = 0.0
            for e in f["element_ids"]:
                r = by_seg.get(f"SEG-{e}")
                if not r:
                    continue
                tparts = [p for p in r["parts"] if p["component"] == CR.C_TIES and p["kg"] is not None]
                sched += sum_kg(tparts)
                a = CR.alt_section_tie_kg(r, P, "DRAWN")
                drawn += a if a is not None else sum_kg(tparts)
            q["ties_kg_schedule_section"] = r3(sched)
            q["ties_kg_drawn_section"] = r3(drawn)
            q["current_kg"], q["current_basis"] = r3(sched), "ties on the schedule section"
            q["alternative_kg"], q["alternative"] = r3(drawn), "ties on the drawn section"
            q["quantity_affected_kg"] = r3(drawn - sched)
        q.setdefault("current_kg", q["kg_in_flagged_parts"])
        q.setdefault("current_basis", "kg of the parts this flag touches")
        q.setdefault("quantity_affected_kg", r3(sum_kg(parts, lambda p: p["release_state"] == CR.BLOCKED))
                     if any(p["release_state"] == CR.BLOCKED for p in parts) else q["kg_in_flagged_parts"])
        q.setdefault("alternative_kg", None)
        q.setdefault("alternative", "not quantified - depends on the answer (see answer options)")
        out[f["flag_key"]] = q
    for k, v in R["q"].items():
        for f in R["new_flags"]:
            if f["context"]["s3_kind"] == k:
                out[f["flag_key"]] = dict(out.get(f["flag_key"], {}), **{kk: (r3(vv) if isinstance(vv, float) else vv)
                                                                         for kk, vv in v.items()
                                                                         if kk not in ("elements",)})
    return out


def build_registers(R):
    res, P, segs = R["res"], R["P"], R["segs"]
    regs = R["regs"]
    occ = {o["column_id"]: o for o in rows(regs, "COLUMN_OCCURRENCE_REGISTER")}
    fv = flag_view(R["flags"])
    joins = {j["occurrence_id"]: j for j in R["joins"]}
    tr = P["tie_rule"]
    sets_claim = next(c for c in R["claims"] if c["fact"] == "TIE_RATE_SEMANTICS")
    out = defaultdict(list)
    for r in res["segments"]:
        s, o = r["segment"], occ[r["segment"]["occurrence_id"]]
        t = CR._released_type(r)
        ev = r["evals"][t]
        tz = ev["ties"][ev["base_zone"]]
        parts = r["parts"]
        open_fk = sorted({k for p in parts for k in p["flags"] if EF.is_open(fv[k])})
        main = [p for p in parts if p["component"] == CR.C_MAIN]
        lap = [p for p in parts if p["component"] in (CR.C_LAP, CR.C_STARTER, CR.C_ANCH)]
        tie = [p for p in parts if p["component"] == CR.C_TIES]
        hooks = [p for p in tie if p["length_kind"] in (CR.HOOK_1, CR.HOOK_2)]
        sec = ev["ties"][ev["base_zone"]]["section_mm"]
        links = tz.get("links") or []
        band = tz["band"]
        out["COLUMN_REBAR_REGISTER"].append({
            "occurrence_id": s["occurrence_id"], "segment_id": s["segment_id"], "chain_id": s["chain_id"],
            "floor": s["floor"], "grid": s["grid"], "plan_tag": o["column_type"], "type_authority": o["type_authority"],
            "resolved_type": s["resolved_type"], "released_candidate": t,
            "candidates": [c["type"] for c in s["candidates"]],
            "schedule_row": joins[s["occurrence_id"]]["schedule_row"],
            "schedule_join": joins[s["occurrence_id"]]["row_state"],
            "join_matches_census": joins[s["occurrence_id"]]["join_matches_census"],
            "section_mm": sec, "main_bars": f"{main[0]['count']}Ø{main[0]['dia_mm']}" if main else None,
            "tie_rule": tr["raw"], "tie_band": None if band["band"] is None else band["band"]["band_id"],
            "tie_band_state": band["state"], "topology": None if band["band"] is None else band["band"]["topology"],
            "links_per_level": tz.get("links_per_level"), "source_state": o["status"],
            "census_terminal_state": o["terminal_state"],
            "components": r["components"], "occurrence_state": r["occurrence_state"],
            "kg": {"main_core": r3(sum_kg(main)), "lap_starter_anchorage": r3(sum_kg(lap)),
                   "tie_core": r3(sum_kg(tie, lambda p: p["length_kind"] == CR.TIE_CORE)),
                   "tie_hooks_provisional": r3(sum_kg(hooks)),
                   "extras": r3(sum_kg(parts, lambda p: p["component"] == CR.C_EXTRA)),
                   "total": r3(sum_kg(parts)), **bucket_kg(parts)},
            "open_flags": [fv[k]["flag_id"] for k in open_fk],
            "source_refs": {"plan": o["plan_source"], "schedule_row": joins[s["occurrence_id"]]["schedule_row"]}})
        for p in main + lap + [p for p in parts if p["component"] == CR.C_EXTRA]:
            reg = "COLUMN_MAIN_BAR_REGISTER" if p["component"] in (CR.C_MAIN, CR.C_EXTRA) else \
                "COLUMN_LAP_STARTER_REGISTER"
            row = {"part_id": p["part_id"], "occurrence_id": s["occurrence_id"], "chain_id": s["chain_id"],
                   "floor": s["floor"], "type": p["candidate_type"], "component": p["component"],
                   "length_kind": p["length_kind"], "count": p["count"], "dia_mm": p["dia_mm"],
                   "length_per_piece_mm": r3(p["length_per_piece_mm"]), "total_length_m": r3(p["total_length_m"]),
                   "kg": r3(p["kg"]), "basis_state": p["basis_state"], "release_state": p["release_state"],
                   "rule_id": p.get("rule_id"), "why": p.get("why"),
                   "flags": [fv[k]["flag_id"] for k in p["flags"]],
                   "alternatives_kg": {k: r3(v) for k, v in (p.get("alternatives_kg") or {}).items()}}
            if p["component"] == CR.C_MAIN:
                row.update({"section_mm": sec, "chain_continues_below": s["below"]["kind"] == "COLUMN",
                            "chain_continues_above": s["above"]["exists"], "interval": s["interval"]})
            if p.get("alternatives_D"):
                row["alternative_D"] = p["alternatives_D"]
                rule = P["lap_rule"]
                row["kg_at_alternative"] = r3(p["kg"] * p["alternatives_D"][0] / rule["current_D"]) \
                    if p["kg"] is not None else None
            if p["component"] == CR.C_STARTER:
                row.update({"footing": s["below"]["footing"]})
            out[reg].append(row)
        sem_used = tz.get("semantics_used")
        out["COLUMN_TIE_REGISTER"].append({
            "occurrence_id": s["occurrence_id"], "segment_id": s["segment_id"], "floor": s["floor"], "type": t,
            "section_mm": sec, "tie_rule_id": tr["rule_id"], "tie_rule_raw": tr["raw"], "tie_diameter_mm": tr["dia_mm"],
            "rate_per_m": tr["rate_per_m"], "per_metre_semantics_source": tz.get("semantics"),
            "per_metre_semantics_used": sem_used, "semantics_claim": tz.get("semantics_claim"),
            "tie_sets_per_m": tr["rate_per_m"] if sem_used == CR.SETS_PER_M else None,
            "links_per_m": None if not tz.get("links_per_level") else (
                tr["rate_per_m"] * tz["links_per_level"] if sem_used == CR.SETS_PER_M else tr["rate_per_m"]),
            "equivalent_spacing_mm": 1000 / tr["rate_per_m"],
            "band": None if band["band"] is None else band["band"]["band_id"], "band_state": band["state"],
            "band_claim": band.get("claim_id"), "topology": None if band["band"] is None else band["band"]["topology"],
            "links_per_level": tz.get("links_per_level"), "link_ranges_state": tz.get("ranges_state"),
            "zones": {z: {**ev["zones"][z], "levels": (ev["ties"][z].get("levels") or {})} for z in CR.ZONES},
            "base_zone": ev["base_zone"],
            "levels_rate_count": (tz.get("by_method") or {}).get(CR.RATE_COUNT),
            "levels_spacing_with_ends": (tz.get("by_method") or {}).get(CR.SPACING_WITH_ENDS),
            "framing_members": s["clear_zone"].get("framing"),
            "perimeter_mm": r3(tz.get("perimeter_mm")), "sum_link_paths_mm": r3(tz.get("sum_link_paths_mm")),
            "parts": [{"part_id": p["part_id"], "length_kind": p["length_kind"], "count": p["count"],
                       "length_per_piece_mm": r3(p["length_per_piece_mm"]), "kg": r3(p["kg"]),
                       "basis_state": p["basis_state"], "release_state": p["release_state"],
                       "flags": [fv[k]["flag_id"] for k in p["flags"]], "why": p.get("why")} for p in tie],
            "tie_core_kg": r3(sum_kg(tie, lambda p: p["length_kind"] == CR.TIE_CORE)),
            "hook_kg_provisional": r3(sum_kg(hooks))})
        for lk in links:
            out["COLUMN_LINK_GEOMETRY_REGISTER"].append({
                "occurrence_id": s["occurrence_id"], "segment_id": s["segment_id"], "floor": s["floor"], "type": t,
                "section_mm": sec, "link_id": lk["link_id"], "bar_range_per_long_face": lk["bar_range_per_long_face"],
                "bars_restrained": lk["bars_restrained"], "encloses_all_bars": lk["encloses_all_bars"],
                "across_mm": r3(lk["across_mm"]), "along_mm": r3(lk["along_mm"]),
                "core_path_mm": r3(lk["core_path_mm"]), "hook_1_mm": tz["hook_mm"], "hook_2_mm": tz["hook_mm"],
                "hook_state": "PROVISIONAL_ENGINEERING_METHOD", "geometry_state": lk["geometry_state"],
                "bar_positions_mm": [r3(x) for x in tz["layout"]["positions_mm"]],
                "bar_position_method": tz["layout"]["internal_positions"],
                "cover_rule_id": tz["cover"]["rule_id"], "cover_mm": tz["cover"]["cover_mm"],
                "cover_source_ref": tz["cover"]["source_ref"], "tie_dia_mm": tr["dia_mm"],
                "bend_method": "centreline rectangle; no bend deduction or allowance (BEND-OTHER = 0)",
                "link_ranges_state": tz["ranges_state"]})
        for p in parts:
            out["COLUMN_RELEASE_REGISTER"].append({
                "part_id": p["part_id"], "occurrence_id": s["occurrence_id"], "floor": s["floor"],
                "component": p["component"], "length_kind": p["length_kind"], "candidate_type": p["candidate_type"],
                "kg": r3(p["kg"]), "basis_state": p["basis_state"], "release_state": p["release_state"],
                "depends_on": p["depends_on"], "flags": [fv[k]["flag_id"] for k in p["flags"]],
                "conflict_shared": p.get("conflict_shared"), "likely_type": p.get("likely_type"),
                "alternatives_kg": {k: r3(v) for k, v in (p.get("alternatives_kg") or {}).items()}})
        sc = CR.tie_scenarios(r, P)
        sc_row = {"occurrence_id": s["occurrence_id"], "floor": s["floor"], "type": t}
        for k, v in sc.items():
            if "|" in k:
                sc_row[k] = None if v is None else {kk: r3(vv) if isinstance(vv, float) else vv for kk, vv in
                                                    v.items()}
        alt = CR.alt_section_tie_kg(r, P, "DRAWN") if s["section_alternatives"] else None
        sc_row["drawn_section_mm"] = [s["section_alternatives"][0]["B_mm"], s["section_alternatives"][0]["D_mm"]] \
            if s["section_alternatives"] else None
        sc_row["ties_kg_drawn_section"] = r3(alt)
        sc_row["lap_kg_current"] = r3(sum_kg(lap, lambda p: p["length_kind"] in (CR.LAP, CR.ANCHORAGE)))
        sc_row["lap_kg_alternative"] = r3(sum(p["kg"] * p["alternatives_D"][0] / P["lap_rule"]["current_D"]
                                              for p in lap if p.get("alternatives_D") and p["kg"] is not None))
        out["COLUMN_SENSITIVITY_REGISTER"].append(sc_row)
    return out


def summarise(R, regsout):
    res = R["res"]
    mc = CR.mass_conservation(res, lambda s: s["floor"])
    parts = res["parts"]
    fv = flag_view(R["flags"])

    def by_floor(pred):
        d = defaultdict(float)
        for p in parts:
            if p["kg"] is not None and pred(p):
                d[p["occurrence_id"].rsplit("-", 1)[-1]] += p["kg"]
        return {f: r3(d.get(f, 0.0)) for f in STOREYS}
    open_parts = [p for p in parts if any(EF.is_open(fv[k]) for k in p["flags"])]
    rr = regsout["COLUMN_REBAR_REGISTER"]
    s = {
        "occurrences_in": len(R["segs"]), "terminal_records_out": len(rr),
        "occurrence_states": dict(Counter(x["occurrence_state"] for x in rr)),
        "component_states": {c: dict(Counter(x["components"][c] for x in rr)) for c in CR.COMPONENTS},
        "main_bar_coverage": sum(1 for x in rr if x["components"][CR.C_MAIN] != CR.BLOCKED),
        "tie_topology_coverage": sum(1 for x in rr if x["tie_band_state"] in (CR.EXACT_RULE, CR.RESOLVED_BY_CLAIM)),
        "links_per_level_counts": dict(Counter(f"{x['links_per_level']}L" for x in rr)),
        "tie_band_states": dict(Counter(x["tie_band_state"] for x in rr)),
        "main_core_kg_by_floor": by_floor(lambda p: p["component"] == CR.C_MAIN),
        "tie_core_kg_by_floor": by_floor(lambda p: p["length_kind"] == CR.TIE_CORE),
        "hook_kg_provisional_by_floor": by_floor(lambda p: p["length_kind"] in (CR.HOOK_1, CR.HOOK_2)),
        "lap_starter_anchorage_kg_by_floor": by_floor(lambda p: p["component"] in (CR.C_LAP, CR.C_STARTER, CR.C_ANCH)),
        "extras_kg_by_floor": by_floor(lambda p: p["component"] == CR.C_EXTRA),
        "release_kg": {k: r3(v) for k, v in mc["project"].items() if k != "unquantified_blocked_parts"},
        "unquantified_blocked_parts": int(mc["project"].get("unquantified_blocked_parts", 0)),
        "mass_conservation_checks": mc["checks"],
        "de_duplicated_kg_in_parts_with_open_flags": r3(sum_kg(open_parts)),
        "input_problems": res["input_problems"],
        "schedule_join_all_match": all(j["join_matches_census"] for j in R["joins"]),
    }
    sens = regsout["COLUMN_SENSITIVITY_REGISTER"]

    def tot(key, f="core_kg"):
        return r3(sum((x.get(key) or {}).get(f, 0) or 0 for x in sens))
    both = [x for x in sens if x.get(f"{CR.CLEAR_ZONE}|{CR.RATE_COUNT}") and x.get(f"{CR.FULL_ZONE}|{CR.RATE_COUNT}")]
    s["zone_clear_vs_full"] = {
        "segments_compared": len(both),
        "clear_rate_count_core_kg": r3(sum(x[f"{CR.CLEAR_ZONE}|{CR.RATE_COUNT}"]["core_kg"] for x in both)),
        "full_rate_count_core_kg": r3(sum(x[f"{CR.FULL_ZONE}|{CR.RATE_COUNT}"]["core_kg"] for x in both)),
        "clear_levels": sum(x[f"{CR.CLEAR_ZONE}|{CR.RATE_COUNT}"]["levels"] for x in both),
        "full_levels": sum(x[f"{CR.FULL_ZONE}|{CR.RATE_COUNT}"]["levels"] for x in both),
        "clear_links": sum(x[f"{CR.CLEAR_ZONE}|{CR.RATE_COUNT}"]["links"] for x in both),
        "full_links": sum(x[f"{CR.FULL_ZONE}|{CR.RATE_COUNT}"]["links"] for x in both),
        "clear_hook_kg": r3(sum(x[f"{CR.CLEAR_ZONE}|{CR.RATE_COUNT}"]["hook_kg"] for x in both)),
        "full_hook_kg": r3(sum(x[f"{CR.FULL_ZONE}|{CR.RATE_COUNT}"]["hook_kg"] for x in both)),
        "segments_clear_zone_not_established": len(sens) - len(both)}
    s["zone_clear_vs_full"]["difference_core_kg"] = r3(s["zone_clear_vs_full"]["full_rate_count_core_kg"] -
                                                       s["zone_clear_vs_full"]["clear_rate_count_core_kg"])
    s["rate_count_vs_spacing_with_ends"] = {
        "quantification": {k: r3(v) if isinstance(v, float) else v for k, v in
                           R["q"]["END_LEVEL_COUNT_METHOD_REQUIRED"].items() if k != "elements"}}
    reg_t = regsout["COLUMN_TIE_REGISTER"]
    s["rate_count_vs_spacing_with_ends"]["levels_rate_count"] = sum(
        (x["levels_rate_count"] or {}).get("levels", 0) for x in reg_t)
    s["rate_count_vs_spacing_with_ends"]["levels_spacing_with_ends"] = sum(
        (x["levels_spacing_with_ends"] or {}).get("levels", 0) for x in reg_t)
    s["lap_starter_status"] = dict(Counter(f"{p['component']}:{p['release_state']}" for p in parts
                                           if p["component"] in (CR.C_LAP, CR.C_STARTER, CR.C_ANCH)))
    open_col = [f for f in R["flags"] if f["element_type"] == "COLUMN" and EF.is_open(f)]
    s["open_column_flags"] = len(open_col)
    s["resolved_by_claim"] = [f["flag_id"] for f in R["flags"] if f["status"] == EF.RESOLVED]
    s["superseded"] = [f["flag_id"] for f in R["superseded"]]
    s["new_flags"] = {f["flag_id"]: f["context"]["s3_kind"] for f in R["new_flags"]}
    return s, mc


def dumps(o):
    return json.dumps(o, indent=1, sort_keys=True, ensure_ascii=False, default=str) + "\n"


def build():
    R = run()
    regsout = build_registers(R)
    s, mc = summarise(R, regsout)
    qv = quantify_s2_flags(R)
    flags_out = []
    for f in sorted([f for f in R["flags"] if f["element_type"] == "COLUMN"], key=lambda f: f["flag_id"]):
        g = dict(f)
        g["s3_quantification_kg"] = qv.get(f["flag_key"])
        g["s3_kind"] = (f.get("context") or {}).get("s3_kind") or {
            "type_conflicts": "SOURCE_CONFLICT", "section_overrides": "SOURCE_CONFLICT",
            "band_gaps": "TIE_TOPOLOGY_RULE_GAP", "transverse_rules": "TIE_RATE_SEMANTICS" if
            "transverse_count" in f["affected_facts"] else "TIE_ZONE_METHOD_REQUIRED"}.get(f["detector"], f["issue_type"])
        flags_out.append(g)
    files = {
        "COLUMN_REBAR_REGISTER.json": {"rows": regsout["COLUMN_REBAR_REGISTER"]},
        "COLUMN_MAIN_BAR_REGISTER.json": {"rows": regsout["COLUMN_MAIN_BAR_REGISTER"]},
        "COLUMN_TIE_REGISTER.json": {"tie_rule": {k: v for k, v in R["P"]["tie_rule"].items()},
                                     "rows": regsout["COLUMN_TIE_REGISTER"]},
        "COLUMN_LINK_GEOMETRY_REGISTER.json": {"bands": R["P"]["topology_bands"],
                                               "bar_arrangement": R["P"]["bar_arrangement"],
                                               "cover": R["P"]["cover"], "hook_method": R["P"]["hook_method"],
                                               "rows": regsout["COLUMN_LINK_GEOMETRY_REGISTER"]},
        "COLUMN_LAP_STARTER_REGISTER.json": {"lap_rule": R["P"]["lap_rule"], "anchorage_rule": R["P"]["anchorage_rule"],
                                             "starter_rule": R["P"]["starter_rule"],
                                             "rows": regsout["COLUMN_LAP_STARTER_REGISTER"]},
        "COLUMN_RELEASE_REGISTER.json": {"rows": regsout["COLUMN_RELEASE_REGISTER"],
                                         "totals_kg": s["release_kg"], "occurrence_states": s["occurrence_states"],
                                         "component_states": s["component_states"]},
        "COLUMN_MASS_CONSERVATION.json": {"checks": mc["checks"],
                                          "project": {k: r3(v) for k, v in mc["project"].items()},
                                          "floors": {f: {k: r3(v) for k, v in d.items()} for f, d in
                                                     sorted(mc["floors"].items())},
                                          "segments": {k: {kk: r3(vv) for kk, vv in v.items()} for k, v in
                                                       sorted(mc["segments"].items())},
                                          "occurrences_in": s["occurrences_in"],
                                          "terminal_records_out": s["terminal_records_out"]},
        "COLUMN_ENGINEERING_FLAGS.json": {"project_id": PROJECT_ID, "drawing_revision": REVISION,
                                          "flags": flags_out, "claim_application_log": R["claim_log"],
                                          "front_summary": {
                                              "open_column_flags": s["open_column_flags"],
                                              "de_duplicated_kg_in_parts_with_open_flags":
                                                  s["de_duplicated_kg_in_parts_with_open_flags"],
                                              "note": "kg per flag overlaps between flags; the front figure counts "
                                                      "every part once"}},
        "COLUMN_SENSITIVITY_REGISTER.json": {"rows": regsout["COLUMN_SENSITIVITY_REGISTER"],
                                             "zone_clear_vs_full": s["zone_clear_vs_full"],
                                             "rate_count_vs_spacing_with_ends": s["rate_count_vs_spacing_with_ends"]},
        "ALSENAN_COLUMN_PROJECT_CLAIMS.json": {"project_id": PROJECT_ID, "drawing_revision": REVISION,
                                               "claims": R["claims"], "project_evidence": R["evidence"],
                                               "s2_claim_store_untouched": True},
        "COLUMN_REBAR_SUMMARY.json": s,
    }
    return R, files, s


def main(write=True):
    R, files, s = build()
    blobs = {k: dumps(v).encode() for k, v in files.items()}
    if write:
        for k, b in blobs.items():
            (HERE / k).write_bytes(b)
        index = {"round": "S3", "project_id": PROJECT_ID, "drawing_revision": REVISION,
                 "engine": "engine/source/column_rebar.py", "engine_policy": CR.POLICY_ID,
                 "outputs": {k: sha(b) for k, b in sorted(blobs.items())},
                 "s1_registers_consumed": {k: R["idx"]["registers"][k]["sha256"] for k in S1_USED},
                 "s2_outputs_consumed": {"ALSENAN_ENGINEERING_FLAGS.json":
                                         R["s2_idx"]["outputs"]["ALSENAN_ENGINEERING_FLAGS.json"]},
                 "r4_registers_consumed": {k: v[1] for k, v in R["r4"].items()},
                 "s1_census_modified": False, "s2_outputs_modified": False, "round4_rebar_modified": False,
                 "frozen_before_benchmark": True, "benchmark_read": False,
                 "scope": "columns only - footings, beams and slabs not calculated",
                 "occurrences": s["occurrences_in"], "terminal_records": s["terminal_records_out"]}
        (HERE / "INDEX.json").write_text(dumps(index), encoding="utf-8")
    return R, files, s, blobs


if __name__ == "__main__":
    twice = "--twice" in sys.argv
    _, _, s, b1 = main()
    if twice:
        _, _, _, b2 = main(write=False)
        same = all(b1[k] == b2[k] for k in b1)
        print("built twice identical:", same)
        if not same:
            raise SystemExit(1)
    print(json.dumps({k: s[k] for k in ("occurrences_in", "terminal_records_out", "occurrence_states",
                                        "release_kg", "mass_conservation_checks", "input_problems")}, indent=1))
