"""DXF CONVERSION ACCEPTANCE CHECK (T-066, read-only research tool; no engine code imports it).

A DXF made from a DWG may feed the engine only when it holds what the DWG holds. The reference is the DWG's own
object stream, decoded by LibreDWG `dwgread -O JSON` (its entity counts and entity modes come from the object bits,
not from the DXF writer). The check compares the DXF with that reference and prints PASS / FAIL per step.
Rule: UP-QTY-STATUS-001 (a lost entity is reported, never silently absent); owner answers Q-10, Q-11, Q-15.

usage:  python -I dxf_acceptance_check.py <dwgread.json> <candidate.dxf> [--out result.json]
        python -I dxf_acceptance_check.py --selftest
Counts, type names and layer names only are printed; no text content, no coordinates.

Steps (numbering matches research/agents_t066/CONVERSION_LOSS_AUDIT.md section 5):
 C1 reference clean     the decode has no colliding handle values (else the pinned 16-bit handle mask is active and
                        per-layer / per-block checks cannot be trusted; entity-mode counts still can)
 C2 structure           DXF has HEADER, CLASSES, TABLES, BLOCKS, ENTITIES, OBJECTS and EOF; ezdxf.readfile (strict) opens it
 C3 handles             no handle written twice; every handle <= $HANDSEED
 C4 units               $INSUNITS equal to the DWG's
 C5 model space         top-level entity count per type equal to the decode's model-space entities (entity mode 2)
 C6 all entities        entity count per type over ENTITIES + BLOCKS equal to the decode's (all spaces, all blocks)
 C7 block definitions   number of BLOCK records equal to the decode's BLOCK_HEADER objects
 C8 references          0 INSERT / DIMENSION naming a block that is not defined (ezdxf audit UNDEFINED_BLOCK = 0)
 C9 layers              (clean reference only) model-space count per layer equal
 C10 geometry checksum  (clean reference only) model-space LINE length sum per layer equal (rel. 1e-9) and the
                        LINE / LWPOLYLINE vertex extents equal (abs. 1e-6 drawing units)
 C11 text and dims      model-space TEXT + MTEXT and DIMENSION counts equal (part of C5, reported on their own)
Known types with no DXF form in the writer (NOT_CONVERTIBLE, e.g. Express Tools RTEXT) are allowed only in paper
space; each is listed with its count as HELD, never dropped silently. Any other difference fails the step.
"""
import hashlib
import json
import math
import sys
from collections import Counter, defaultdict

REQUIRED_SECTIONS = ("HEADER", "CLASSES", "TABLES", "BLOCKS", "ENTITIES", "OBJECTS")
DWG_TO_DXF = {"DIMENSION_LINEAR": "DIMENSION", "DIMENSION_ALIGNED": "DIMENSION", "DIMENSION_ANG2LN": "DIMENSION",
              "DIMENSION_ANG3PT": "DIMENSION", "DIMENSION_RADIUS": "DIMENSION", "DIMENSION_DIAMETER": "DIMENSION",
              "DIMENSION_ORDINATE": "DIMENSION", "LARGE_RADIAL_DIMENSION": "LARGE_RADIAL_DIMENSION",
              "VERTEX_2D": "VERTEX", "VERTEX_3D": "VERTEX", "VERTEX_MESH": "VERTEX", "VERTEX_PFACE": "VERTEX",
              "VERTEX_PFACE_FACE": "VERTEX", "POLYLINE_2D": "POLYLINE", "POLYLINE_3D": "POLYLINE",
              "POLYLINE_MESH": "POLYLINE", "POLYLINE_PFACE": "POLYLINE", "PROXY_ENTITY": "ACAD_PROXY_ENTITY",
              "MULTILEADER": "MULTILEADER"}
NOT_CONVERTIBLE_PAPER_ONLY = {"RTEXT"}
SUB_ENTITIES = {"ATTRIB", "VERTEX", "SEQEND", "BLOCK", "ENDBLK"}


def dxf_type(o):
    k = o.get("entity")
    if k == "UNKNOWN_ENT":
        return o.get("dxfname") or "UNKNOWN_ENT"
    return DWG_TO_DXF.get(k, k)


# ------------------------------------------------------------------ reference (DWG decode)
def reference(decode):
    O = decode["OBJECTS"]
    vals = Counter(o["handle"][-1] for o in O if isinstance(o.get("handle"), list))
    colliding = sum(1 for n in vals.values() if n > 1)
    layers = {o["handle"][-1]: o.get("name") for o in O if o.get("object") == "LAYER"}
    ms, paper, alltypes = Counter(), Counter(), Counter()
    ms_layers, ms_len, ext = Counter(), defaultdict(float), [math.inf, math.inf, -math.inf, -math.inf]
    for o in O:
        if "entity" not in o:
            continue
        t = dxf_type(o)
        alltypes[t] += 1
        if o.get("entmode") == 1:
            paper[t] += 1
        if o.get("entmode") != 2 or t in SUB_ENTITIES:
            continue
        ms[t] += 1
        lay = layers.get((o.get("layer") or [None])[-1], "?")
        ms_layers[lay] += 1
        pts = []
        if t == "LINE":
            a, b = o["start"], o["end"]
            ms_len[lay] += math.dist(a[:2], b[:2])
            pts = [a, b]
        elif t == "LWPOLYLINE":
            pts = o.get("points") or []
        for p in pts:
            ext = [min(ext[0], p[0]), min(ext[1], p[1]), max(ext[2], p[0]), max(ext[3], p[1])]
    nblocks = sum(1 for o in O if o.get("object") == "BLOCK_HEADER")
    return {"clean": colliding == 0, "colliding_handle_values": colliding, "insunits": decode["HEADER"].get("INSUNITS"),
            "model_by_type": dict(ms), "paper_active_by_type": dict(paper), "all_by_type": dict(alltypes),
            "block_definitions": nblocks, "model_by_layer": dict(ms_layers), "model_line_length_by_layer": dict(ms_len),
            "model_vertex_extents": ext}


# ------------------------------------------------------------------ candidate (DXF)
def scan_tags(path):
    """raw group-code scan: sections, EOF, handles; robust where ezdxf refuses the file."""
    lines = open(path, "rb").read().decode("utf-8", "replace").splitlines()
    sections, eof, handles, types = [], False, Counter(), defaultdict(Counter)
    sec, want_name, own_seen = None, False, True
    for i in range(0, len(lines) - 1, 2):
        code, val = lines[i].strip(), lines[i + 1].strip()
        if code == "0":
            own_seen = False                                  # the record's own handle is its first code 5;
            if val == "SECTION":                              # SORTENTSTABLE repeats code 5 for sort handles
                want_name = True
            elif val == "ENDSEC":
                sec = None
            elif val == "EOF":
                eof = True
            elif sec in ("ENTITIES", "BLOCKS"):
                types[sec][val] += 1
        elif code == "2" and want_name:
            sec, want_name = val, False
            sections.append(val)
        elif code == "5" and sec not in ("HEADER", None) and not own_seen:
            handles[val.upper()] += 1
            own_seen = True
    return {"sections": sections, "eof": eof, "duplicate_handles": sum(1 for n in handles.values() if n > 1),
            "max_handle": max((int(h, 16) for h in handles if all(c in "0123456789ABCDEF" for c in h)), default=0),
            "types": {k: dict(v) for k, v in types.items()}}


def candidate(path):
    import ezdxf
    tags = scan_tags(path)
    out = {"tags": tags, "readfile": "OK"}
    try:
        doc = ezdxf.readfile(path)
    except Exception as ex:                                   # report, never repair: the DXF is refused
        out["readfile"] = f"{type(ex).__name__}: {str(ex)[:120]}"
        return out, None
    msp = doc.modelspace()
    ms, ms_layers, ms_len = Counter(), Counter(), defaultdict(float)
    ext = [math.inf, math.inf, -math.inf, -math.inf]
    for e in msp:
        t = e.dxftype()
        ms[t] += 1
        ms_layers[e.dxf.layer] += 1
        pts = []
        if t == "LINE":
            a, b = e.dxf.start, e.dxf.end
            ms_len[e.dxf.layer] += math.dist((a.x, a.y), (b.x, b.y))
            pts = [a, b]
        elif t == "LWPOLYLINE":
            pts = list(e.vertices())
        for p in pts:
            ext = [min(ext[0], p[0]), min(ext[1], p[1]), max(ext[2], p[0]), max(ext[3], p[1])]
    hs = doc.header.get("$HANDSEED", "0")
    out.update({"insunits": doc.header.get("$INSUNITS"), "handseed": int(str(hs), 16),
                "model_by_type": dict(ms), "model_by_layer": dict(ms_layers),
                "model_line_length_by_layer": dict(ms_len), "model_vertex_extents": ext,
                "block_definitions": len(doc.blocks)})
    aud = doc.audit()                                         # in memory only; the file is never written
    out["undefined_block_refs"] = sum(1 for f in aud.fixes if int(f.code) == 103)
    out["audit_fix_codes"] = dict(Counter(f.code.name for f in aud.fixes))
    return out, doc


# ------------------------------------------------------------------ comparison
def _diff(ref, got):
    keys = set(ref) | set(got)
    return {k: (ref.get(k, 0), got.get(k, 0)) for k in sorted(keys) if ref.get(k, 0) != got.get(k, 0)}


def check(ref, cand):
    R = []

    def step(cid, ok, detail):
        R.append({"step": cid, "result": "PASS" if ok else "FAIL", "detail": detail})

    step("C1 reference clean", ref["clean"], {"colliding_handle_values": ref["colliding_handle_values"]})
    t = cand["tags"]
    miss = [s for s in REQUIRED_SECTIONS if s not in t["sections"]]
    step("C2 structure", not miss and t["eof"] and cand["readfile"] == "OK",
         {"missing_sections": miss, "eof": t["eof"], "ezdxf_readfile": cand["readfile"]})
    if cand["readfile"] != "OK":
        allt = Counter()
        for sec in t["types"].values():
            allt.update(sec)
        step("C6 all entities", False, {"differences_ref_vs_dxf": _diff(ref["all_by_type"], allt),
                                        "lost": sum(ref["all_by_type"].values()) - sum(allt.values())})
        return R
    step("C3 handles", t["duplicate_handles"] == 0 and t["max_handle"] <= cand["handseed"],
         {"duplicate_handles": t["duplicate_handles"], "max_handle": hex(t["max_handle"]),
          "handseed": hex(cand["handseed"])})
    step("C4 units", ref["insunits"] == cand["insunits"], {"dwg": ref["insunits"], "dxf": cand["insunits"]})
    d5 = _diff(ref["model_by_type"], cand["model_by_type"])
    step("C5 model space", not d5, {"differences_ref_vs_dxf": d5})
    allt = Counter()
    for sec in t["types"].values():
        allt.update(sec)
    d6 = _diff(ref["all_by_type"], allt)
    held = {k: v for k, v in d6.items() if k in NOT_CONVERTIBLE_PAPER_ONLY and v[1] == 0
            and ref["paper_active_by_type"].get(k, 0) == v[0]}
    d6 = {k: v for k, v in d6.items() if k not in held}
    step("C6 all entities", not d6, {"differences_ref_vs_dxf": d6,
                                     "held_not_convertible_paper_only": {k: v[0] for k, v in held.items()}})
    step("C7 block definitions", ref["block_definitions"] == cand["block_definitions"],
         {"dwg": ref["block_definitions"], "dxf": cand["block_definitions"]})
    step("C8 references", cand["undefined_block_refs"] == 0, {"undefined_block_refs": cand["undefined_block_refs"]})
    if ref["clean"]:
        d9 = _diff(ref["model_by_layer"], cand["model_by_layer"])
        step("C9 layers", not d9, {"differences_ref_vs_dxf": d9})
        bad = {k: (round(v, 6), round(cand["model_line_length_by_layer"].get(k, 0.0), 6))
               for k, v in ref["model_line_length_by_layer"].items()
               if not math.isclose(v, cand["model_line_length_by_layer"].get(k, 0.0), rel_tol=1e-9, abs_tol=1e-9)}
        ex_ok = all(math.isclose(a, b, abs_tol=1e-6) for a, b in
                    zip(ref["model_vertex_extents"], cand["model_vertex_extents"]))
        step("C10 geometry checksum", not bad and ex_ok, {"line_length_layers_differing": bad, "extents_equal": ex_ok})
    else:
        step("C9 layers", False, {"not_checkable": "reference not clean (C1)"})
        step("C10 geometry checksum", False, {"not_checkable": "reference not clean (C1)"})
    tx = {k: d5[k] for k in ("TEXT", "MTEXT", "DIMENSION") if k in d5}
    step("C11 text and dims", not tx, {"differences_ref_vs_dxf": tx})
    return R


def verdict(R):
    return "ACCEPTED" if all(r["result"] == "PASS" for r in R) else "REFUSED"


def run(decode_path, dxf_path):
    raw = open(decode_path, "rb").read().decode("utf-8", "replace")
    ref = reference(json.loads(raw))
    cand, _doc = candidate(dxf_path)
    R = check(ref, cand)
    return {"decode_sha256": hashlib.sha256(open(decode_path, "rb").read()).hexdigest(),
            "dxf_sha256": hashlib.sha256(open(dxf_path, "rb").read()).hexdigest(),
            "verdict": verdict(R), "steps": R,
            "audit_fix_codes": cand.get("audit_fix_codes")}


# ------------------------------------------------------------------ self-test (synthetic, not a client drawing)
def _synthetic(tmp):
    """a 2-storey synthetic plan: walls (LINE / LWPOLYLINE), doors as an anonymous block, a room label, a dimension;
    returns (decode-like reference dict built by hand, dxf path)."""
    import ezdxf
    doc = ezdxf.new("R2018", setup=True)
    doc.header["$INSUNITS"] = 4
    msp = doc.modelspace()
    doc.layers.add("A-WALL")
    doc.layers.add("A-DOOR")
    for x0 in (0.0, 20000.0):                                   # two storeys side by side, mm
        msp.add_lwpolyline([(x0, 0), (x0 + 12000, 0), (x0 + 12000, 9000), (x0, 9000)], close=True,
                           dxfattribs={"layer": "A-WALL"})
        msp.add_line((x0 + 4000, 0), (x0 + 4000, 9000), dxfattribs={"layer": "A-WALL"})
        msp.add_text("BEDROOM", dxfattribs={"layer": "A-TEXT"}).set_placement((x0 + 1000, 1000))
    blk = doc.blocks.new_anonymous_block("U")                   # anonymous door block, the defect case
    blk.add_arc((0, 0), 900, 0, 90, dxfattribs={"layer": "A-DOOR"})
    blk.add_line((0, 0), (900, 0), dxfattribs={"layer": "A-DOOR"})
    msp.add_blockref(blk.name, (4000, 3000), dxfattribs={"layer": "A-DOOR"})
    msp.add_blockref(blk.name, (24000, 3000), dxfattribs={"layer": "A-DOOR", "rotation": 90})
    dim = msp.add_linear_dim(base=(0, -1000), p1=(0, 0), p2=(12000, 0), dxfattribs={"layer": "A-DIM"})
    dim.render()
    p = f"{tmp}/synthetic.dxf"
    doc.saveas(p)
    doc = ezdxf.readfile(p)
    m = doc.modelspace()
    lay_len = defaultdict(float)
    ext = [math.inf, math.inf, -math.inf, -math.inf]
    for e in m:
        if e.dxftype() == "LINE":
            lay_len[e.dxf.layer] += math.dist((e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y))
            pts = [e.dxf.start, e.dxf.end]
        elif e.dxftype() == "LWPOLYLINE":
            pts = list(e.vertices())
        else:
            pts = []
        for q in pts:
            ext = [min(ext[0], q[0]), min(ext[1], q[1]), max(ext[2], q[0]), max(ext[3], q[1])]
    allt = Counter(scan_tags(p)["types"].get("ENTITIES", {}))
    allt.update(scan_tags(p)["types"].get("BLOCKS", {}))
    ref = {"clean": True, "colliding_handle_values": 0, "insunits": 4,
           "model_by_type": dict(Counter(e.dxftype() for e in m)), "paper_active_by_type": {},
           "all_by_type": dict(allt), "block_definitions": len(doc.blocks),
           "model_by_layer": dict(Counter(e.dxf.layer for e in m)), "model_line_length_by_layer": dict(lay_len),
           "model_vertex_extents": ext}
    return ref, p


def _mutate(src, dst, fn):
    lines = open(src).read().splitlines()
    open(dst, "w").write("\n".join(fn(lines)) + "\n")


def selftest():
    import tempfile
    tmp = tempfile.mkdtemp()
    ref, p = _synthetic(tmp)
    cases = {}
    cases["identical"] = check(ref, candidate(p)[0])

    def drop_entities(lines):                                   # the pinned-writer failure: no ENTITIES section
        out, skip = [], False
        for i in range(0, len(lines) - 1, 2):
            c, v = lines[i].strip(), lines[i + 1].strip()
            if c == "2" and v == "ENTITIES" and out[-1].strip() == "SECTION":
                out = out[:-2]
                skip = True
                continue
            if skip:
                if c == "0" and v == "ENDSEC":
                    skip = False
                continue
            out += [lines[i], lines[i + 1]]
        return out

    def unnumber_anonymous(lines):                              # the writer naming defect: INSERT names '*U'
        out, in_insert = [], False
        for i in range(0, len(lines) - 1, 2):
            c, v = lines[i].strip(), lines[i + 1].strip()
            if c == "0":
                in_insert = v == "INSERT"
            if in_insert and c == "2" and v.startswith("*U"):
                v = "*U"
            out += [lines[i], v if c == "2" and in_insert else lines[i + 1]]
        return out

    def lose_one_wall(lines):                                   # a single LINE removed from model space
        out, i, done, sec = [], 0, False, None
        while i < len(lines) - 1:
            c, v = lines[i].strip(), lines[i + 1].strip()
            if c == "2" and out and out[-1].strip() == "SECTION":
                sec = v
            if not done and sec == "ENTITIES" and c == "0" and v == "LINE":
                j = i + 2
                while not (lines[j].strip() == "0"):
                    j += 2
                i, done = j, True
                continue
            out += [lines[i], lines[i + 1]]
            i += 2
        return out

    def scale_units(lines):                                     # mm drawing saved as metres
        out = list(lines)
        for i in range(0, len(out) - 1, 2):
            if out[i + 1].strip() == "$INSUNITS":
                out[i + 3] = "6"
        return out

    def duplicate_handle(lines):                                # the 16-bit mask symptom: two records, one handle
        out, sec, first = list(lines), None, None
        for i in range(0, len(out) - 1, 2):
            c, v = out[i].strip(), out[i + 1].strip()
            if c == "2" and out[i - 1].strip() == "SECTION":
                sec = v
            if sec == "ENTITIES" and c == "5":
                if first is None:
                    first = v
                else:
                    out[i + 1] = first
                    break
        return out

    for name, fn in (("no_entities_section", drop_entities), ("anonymous_block_unnumbered", unnumber_anonymous),
                     ("one_wall_line_lost", lose_one_wall), ("units_changed", scale_units),
                     ("duplicate_handle", duplicate_handle)):
        q = f"{tmp}/{name}.dxf"
        _mutate(p, q, fn)
        cases[name] = check(ref, candidate(q)[0])
    # ezdxf opens a DXF without an ENTITIES section (empty model space), so every count step fails as well
    expect = {"identical": set(), "no_entities_section": {"C2 structure", "C5 model space", "C6 all entities",
                                                          "C9 layers", "C10 geometry checksum", "C11 text and dims"},
              "anonymous_block_unnumbered": {"C8 references"},
              "one_wall_line_lost": {"C5 model space", "C6 all entities", "C9 layers", "C10 geometry checksum"},
              "units_changed": {"C4 units"}, "duplicate_handle": {"C3 handles"}}
    ok = True
    for name, R in cases.items():
        failed = {r["step"] for r in R if r["result"] == "FAIL"}
        good = failed == expect[name]
        ok &= good
        print(f"{'OK ' if good else 'BAD'} {name:28s} verdict={verdict(R):8s} failed={sorted(failed)}")
    print("SELFTEST", "PASSED" if ok else "FAILED")
    return ok


if __name__ == "__main__":
    if sys.argv[1:2] == ["--selftest"]:
        sys.exit(0 if selftest() else 1)
    res = run(sys.argv[1], sys.argv[2])
    if "--out" in sys.argv:
        json.dump(res, open(sys.argv[sys.argv.index("--out") + 1], "w"), indent=1, default=str)
    print("VERDICT", res["verdict"])
    for r in res["steps"]:
        print(f"{r['result']}  {r['step']}: {json.dumps(r['detail'], default=str)[:300]}")
