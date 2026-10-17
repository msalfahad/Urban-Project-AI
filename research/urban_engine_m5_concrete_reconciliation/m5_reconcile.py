"""M5 reconciliation: one canonical identity per physical element, four sources side by side, every difference
classified and located, and the drawing-supported Urban quantity rebuilt without double counting.

RECONCILIATION phase only. The freelancer and the MCP figures explain differences; no Urban quantity is chosen or
moved because of them. The Urban side is the frozen M4 engine run (route G) for the families it measures, plus the
frozen S-stage registers (through M1) for the families the generic route does not measure. Every M5 ownership
decision that moves an item in or out of the Urban total is recorded with its drawing evidence (DECISIONS).
"""

from __future__ import annotations

import math
import re
from collections import Counter, defaultdict

from shapely.geometry import Point, Polygon
from shapely.ops import unary_union

import m5_sources as S

FAMILY_ORDER = ("FOOTINGS", "STRAPS", "NECKS", "GROUND_BEAMS", "GB_PERIMETER", "GROUND_SLAB", "COLUMNS", "BEAMS",
                "SLABS", "LINTELS", "STAIRS", "DOMES", "POOL", "POOL_PUMP_ROOM", "LIFT", "CANTILEVER_PORTIONS",
                "WATER_TANK", "BOUNDARY_WALL", "PARAPETS")
FAMILY_TITLE = {"FOOTINGS": "Footings", "STRAPS": "Strap beams", "NECKS": "Foundation necks",
                "GROUND_BEAMS": "Ground beams", "GB_PERIMETER": "Perimeter tie beam (freelancer row)",
                "GROUND_SLAB": "Ground slab", "COLUMNS": "Columns GF-2F", "BEAMS": "Suspended beams",
                "SLABS": "Suspended slabs", "LINTELS": "Lintels", "STAIRS": "Stairs", "DOMES": "Domes and rings",
                "POOL": "Swimming pool", "POOL_PUMP_ROOM": "Pool pump room", "LIFT": "Lift pit walls",
                "CANTILEVER_PORTIONS": "Cantilever portions", "WATER_TANK": "Water tank (base / walls)",
                "BOUNDARY_WALL": "Boundary wall", "PARAPETS": "Parapets", "BLINDING": "Blinding (plain concrete)"}
M4_STOREY_SHEET = {"GF": "SH06", "1F": "SH04", "2F": "SH02", "GROUND": "SH08", "FOUNDATION": "SH10"}
STAGE_SHEET = {"GFRS": "SH06", "FFRS": "SH04", "SFRS": "SH02", "GBP": "SH08", "FP": "SH10"}
TOL_M3, TOL_FRAC = 0.02, 0.02


def r6(x):
    return None if x is None else round(float(x) + 0.0, 6) + 0.0


def kwd(m3, rate):
    return None if m3 is None else round(m3 * rate, 3) + 0.0


def mark_of(src):
    m = re.search(r"mark (\S+?)[ ;)]", (src or "") + " ")
    return m.group(1) if m else ""


# ================================================================== the Urban items (M4 + S-stage)
def m4_family(i):
    f, cid = i["family"], i["component_id"]
    if f == "COLUMNS":
        return "NECKS" if i["storey"] == "FOUNDATION" else "COLUMNS"
    if f == "GROUND_BEAMS":
        return "STRAPS" if ":FOUNDATION:" in cid else "GROUND_BEAMS"
    if f == "PLAIN_CONCRETE":
        return "BLINDING"
    return f


def m4_mark(i):
    if i["family"] == "FOOTINGS":
        m = re.search(r"FTG:SH\d+:([A-Z0-9]+)@", i["component_id"])
        if m:
            return m.group(1)
        return "F/F10" if i["blocker"] == "SOURCE_CONFLICT" else ""
    return mark_of(i.get("source"))


def urban_items(R, m1):
    """Every Urban concrete item with one canonical family. M4 for what the generic route measures; M1 (frozen
    S-stage registers) for stairs, domes, pool, lift, cantilever portions, water tank, boundary wall, parapets."""
    out = []
    for i in R["items"]:
        if i["trade"] != "CONCRETE":
            continue
        d = i.get("dimensions") or {}
        out.append({"UID": i["item_id"], "ORIGIN": "M4", "FAMILY": m4_family(i), "FLOOR": i["storey"],
                    "MARK": m4_mark(i), "CATEGORY": i["category"], "LOW": i["low"], "BASE": i["base"],
                    "HIGH": i["high"], "EXP_LOW": i.get("exposure_low"), "EXP_HIGH": i.get("exposure_high"),
                    "BLOCKER": i.get("blocker") or "", "SOURCE": i.get("source") or "", "DIMS": d,
                    "COMPONENT": i["component_id"], "FORMULA": i.get("formula") or "", "M5": "KEEP", "M5_NOTE": ""})
    fam_map = {"STAIRS": "STAIRS", "DOMES": "DOMES", "POOL": "POOL", "LIFT": "LIFT",
               "CANTILEVER_PORTIONS": "CANTILEVER_PORTIONS", "WATER_TANK_ROOF": "WATER_TANK",
               "BOUNDARY_WALL": "BOUNDARY_WALL", "PARAPETS": "PARAPETS"}
    for r in m1:
        fam = fam_map.get(r["FAMILY"])
        if not fam:
            continue
        cat = "PROVISIONAL" if r["M1_CATEGORY"] == "VERIFIED" else r["M1_CATEGORY"]
        out.append({"UID": "M1:" + r["COMPONENT_ID"], "ORIGIN": "M1 (" + r["M1_CATEGORY"] + ")", "FAMILY": fam,
                    "FLOOR": r["STOREY"], "MARK": r["COMPONENT_ID"], "CATEGORY": cat, "LOW": r["LOW"],
                    "BASE": r["BASE"], "HIGH": r["HIGH"], "EXP_LOW": r["EXPOSURE_LOW"],
                    "EXP_HIGH": r["EXPOSURE_HIGH"], "BLOCKER": r.get("BLOCKER") or "", "SOURCE": r.get("SOURCE") or "",
                    "DIMS": r.get("DIMENSIONS") or "", "COMPONENT": r["COMPONENT_ID"],
                    "FORMULA": r.get("FORMULA") or "", "M5": "KEEP", "M5_NOTE": ""})
    return out


# ================================================================== geometry helpers on the M4 drawing model
def sheet_origin(D, sh):
    return D["sheets"][sh]["sheet"]["origin"]


def to_world(D, sh, pts):
    ox, oy = sheet_origin(D, sh)
    return [(x + ox, y + oy) for x, y in pts]


def band_polygon(D, sh, band_id):
    for b in D["sheets"][sh].get("bands", []):
        if b["band_id"] == band_id:
            return Polygon(b["polygon"])
    return None


def face_polygons(D, sh):
    out = {}
    for f in D["sheets"][sh].get("slab", {}).get("faces", []):
        if len(f["polygon"]) >= 3:
            out[f["face_id"]] = (f, Polygon(f["polygon"]).buffer(0))
    return out


def dome_centres(D):
    """Dome plan circles (S-BOUN circles on the 2F sheet), mapped to the 1F slab sheet frame; radius in mm."""
    import ezdxf
    doc = ezdxf.readfile(str(S.DXF_ST))
    x0, y0, x1, y1 = D["sheets"]["SH02"]["sheet"]["box"]
    o2, o4 = sheet_origin(D, "SH02"), sheet_origin(D, "SH04")
    out = []
    for e in doc.modelspace().query("CIRCLE"):
        try:
            lay = e.dxf.layer.upper()
        except Exception:                                   # noqa: BLE001
            continue
        c = e.dxf.center
        if lay == "S-BOUN" and x0 <= c.x <= x1 and y0 <= c.y <= y1:
            out.append({"handle": e.dxf.handle, "r_mm": e.dxf.radius,
                        "sh02": (c.x, c.y), "sh04": (c.x - o2[0] + o4[0], c.y - o2[1] + o4[1])})
    return sorted(out, key=lambda r: r["sh02"][0])


# ================================================================== M5 ownership decisions (no double count)
def decisions(D, U, s9a, s81a, s87):
    """Apply the evidence-based ownership decisions to the Urban items (in place). Returns the decision register."""
    by_uid = {u["UID"]: u for u in U}
    reg = []

    def dec(did, kind, uids, action, m3_base, m3_exp_high, evidence, note):
        reg.append({"DECISION_ID": did, "KIND": kind, "ITEMS": ";".join(uids), "ACTION": action,
                    "BASE_M3_MOVED": r6(m3_base), "EXPOSURE_HIGH_M3_DROPPED": r6(m3_exp_high),
                    "EVIDENCE": evidence, "NOTE": note})

    # D-01 water-tank roof: the two 18 cm panels M4 measures on the 2F sheet are the S8.4 roof slabs
    wt = [u for u in U if u["FAMILY"] == "WATER_TANK" and u["CATEGORY"] == "PROVISIONAL"]
    m4_18 = [u for u in U if u["ORIGIN"] == "M4" and u["FAMILY"] == "SLABS" and u["FLOOR"] == "2F"
             and isinstance(u["DIMS"], dict) and u["DIMS"].get("t_m") == 0.18]
    matched = []
    for w in wt:
        hit = next((m for m in m4_18 if abs((m["BASE"] or 0) - (w["BASE"] or 0)) < 1e-6), None)
        if hit:
            w["M5"], w["M5_NOTE"] = "EXCLUDED_SAME_AS_M4", "same panel as " + hit["UID"]
            matched.append((w["UID"], hit["UID"], w["BASE"]))
    if matched:
        dec("D-01", "DOUBLE_COUNT_AVOIDED", [m[0] for m in matched], "EXCLUDE the S-stage rows; M4 SLABS owns them",
            sum(m[2] for m in matched), 0,
            "equal volume and 18 cm tag on both sides: " + "; ".join(f"{a} = {b}" for a, b, _ in matched),
            "the water-tank roof slabs are the 2F panels tagged T 18; counted once, in suspended slabs")

    # D-02 dome rings: M4 arc bands on the 1F sheet that lie in the drawn dome-ring annulus
    domes = dome_centres(D)
    arcs = []
    for b in D["sheets"]["SH04"].get("bands", []):
        for k, dm in enumerate(domes):
            ds = [math.dist(dm["sh04"], p) for p in b["polygon"]]
            if min(ds) >= dm["r_mm"] - 50 and max(ds) <= dm["r_mm"] + 250:
                u = by_uid.get(f"P-C:BEAMS:1F:{b['band_id']}") or by_uid.get(f"U-C:BEAMS:1F:{b['band_id']}")
                if u:
                    arcs.append((u, "AB"[k] if k < 2 else str(k), round(min(ds)), round(max(ds))))
    if arcs:
        for u, dome, r0, r1 in arcs:
            u["M5"] = "REALLOCATED_TO_DOMES"
            u["M5_NOTE"] = f"dome {dome} ring (r {r0}-{r1} mm about the drawn dome circle); S8.3 owns the ring"
        dec("D-02", "DOUBLE_COUNT_AVOIDED", [a[0]["UID"] for a in arcs],
            "REALLOCATE to DOMES: the S8.3 ring beam owns this concrete; M4 beam base and exposure removed",
            sum(a[0]["BASE"] or 0 for a in arcs), sum(a[0]["EXP_HIGH"] or 0 for a in arcs),
            "every polygon vertex lies between r = 2211 and 2411 mm of a dome circle (layer S-BOUN, radius 2211) "
            "carried from the 2F sheet to the 1F sheet by the sheet origins",
            "M4 reads the drawn ring arcs as beams (two bound to B4); S8.3 measures the same ring as a dome ring")

    # D-03 dome interiors: an M4 slab face containing a dome centre is the dome opening (S8.3: no slab inside)
    faces = face_polygons(D, "SH04")
    hits = []
    for k, dm in enumerate(domes):
        for fid, (f, P) in faces.items():
            if f["class"] == "PANEL" and P.contains(Point(dm["sh04"])):
                u = by_uid.get(f"U-C:SLABS:1F:{fid}") or by_uid.get(f"P-C:SLABS:1F:{fid}")
                if u:
                    hits.append((u, "AB"[k] if k < 2 else str(k), f))
    for u, dome, f in hits:
        u["M5"] = "NOT_SLAB_DOME_OPENING"
        u["M5_NOTE"] = (f"dome {dome}: the face holds the dome centre; M4 read the dome's radial lines as "
                        f"'{f.get('region_reason')}'; S8.3 records no slab inside the dome circle")
    if hits:
        dec("D-03", "FALSE_EXPOSURE_REMOVED", [h[0]["UID"] for h in hits],
            "DROP the exposure: the face is the dome opening, not a stair zone",
            sum(h[0]["BASE"] or 0 for h in hits), sum(h[0]["EXP_HIGH"] or 0 for h in hits),
            "the dome circle centre lies inside the face; S8.3 CQ-DOME-x-OPENING: 'no slab: the 1F roof is open "
            "inside the dome circle'", "M4 detection defect (radial dome lines read as winder treads); base unchanged")

    # D-04 cantilever portions (S9A hatched bands) against the M4 beam bands of the same sheet
    rows = []
    for b in s9a:
        sh = STAGE_SHEET.get(b["SHEET"])
        if not sh:
            continue
        poly = Polygon(S.read_json_str(b["POLYGON_MODEL_MM"]))
        st = {"SH06": "GF", "SH04": "1F", "SH02": "2F"}[sh]
        over = []
        for bb in D["sheets"][sh].get("bands", []):
            a = Polygon(bb["polygon"]).intersection(poly).area
            if a > 0.5 * poly.area:
                u = by_uid.get(f"P-C:BEAMS:{st}:{bb['band_id']}") or by_uid.get(f"U-C:BEAMS:{st}:{bb['band_id']}")
                over.append((bb["band_id"], u))
        m1u = by_uid.get("M1:" + b["BAND_ID"])
        rows.append((b, sh, over, m1u))
    moved_base, dropped, uids = 0.0, 0.0, []
    for b, sh, over, m1u in rows:
        m4u = [u for _, u in over if u]
        if m4u and all(u["CATEGORY"] == "PROVISIONAL" for u in m4u):
            if m1u:
                m1u["M5"], m1u["M5_NOTE"] = "EXCLUDED_SAME_AS_M4", "M4 measures this band as " + m4u[0]["UID"]
                moved_base += m1u["BASE"] or 0
                uids.append(m1u["UID"])
        elif m4u:
            for u in m4u:
                u["M5"] = "SUPERSEDED_BY_CANTILEVER"
                u["M5_NOTE"] = f"S9A band {b['BAND_ID']} (legend 'cantilever portion' hatch); thickness not printed"
                dropped += u["EXP_HIGH"] or 0
                uids.append(u["UID"])
            if m1u:
                m1u["M5"] = "CONDITIONAL"
        elif m1u:
            m1u["M5"] = "CONDITIONAL"
            m1u["M5_NOTE"] = "no M4 band at this hatch; S9A value at the adjacent slab thickness"
    for b, sh, over, m1u in rows:
        if m1u and m1u["M5"] == "KEEP":
            m1u["M5"] = "CONDITIONAL"
            m1u["M5_NOTE"] = m1u["M5_NOTE"] or "S9A band at the adjacent slab thickness; thickness not printed"
    dec("D-04", "OWNERSHIP_CHECKED", uids, "per band: M4 bound beam keeps it; an M4 unlabelled span is superseded "
        "by the cantilever portion; the cantilever value stays CONDITIONAL (thickness not printed)",
        moved_base, dropped, "S9A band polygons (model frame) intersected with the M4 bands of the same sheet "
        "(> 50 % of the band area)", f"{len(rows)} hatched bands checked")

    # D-05 the ground-slab cell holding the lift: decompose with the S8.1A recovered regions (same sheet frame)
    gsu = [u for u in U if u["ORIGIN"] == "M4" and u["FAMILY"] == "GROUND_SLAB" and u["CATEGORY"] == "UNRESOLVED"]
    faces8 = face_polygons(D, "SH08")
    decomposition = []
    for u in gsu:
        fid = u["UID"].split(":")[-1]
        if fid not in faces8:
            continue
        f, P = faces8[fid]
        parts = defaultdict(float)
        for g in s81a:
            pts = S.read_json_str(g["POLYGON_MM"])
            if len(pts) < 3:
                continue
            G = Polygon(to_world(D, "SH08", pts)).buffer(0)
            a = P.intersection(G).area * 1e-6
            if a > 1e-4:
                parts[(g["LANE"], g["KIND"], g["OWNER"])] += a
        if parts:
            decomposition.append((u, f, dict(parts)))
    for u, f, parts in decomposition:
        slab = sum(a for (lane, _, _), a in parts.items() if lane == "GROUND_SLAB_CANDIDATE")
        stair = sum(a for (lane, _, _), a in parts.items() if lane == "STAIR_OR_SPECIAL_STRUCTURE")
        u["M5"] = "CONDITIONAL_DECOMPOSED"
        u["M5_SLAB_HIGH_M2"] = slab + stair
        u["M5_NOTE"] = "; ".join(f"{k[1]} {a:.3f} m2 ({k[2]})" for k, a in sorted(parts.items(), key=lambda kv: -kv[1]))
        u["M5_SLAB_M2"] = slab
    if decomposition:
        dec("D-05", "UNRESOLVED_DECOMPOSED", [d[0]["UID"] for d in decomposition],
            "split the unresolved cell by the S8.1A regions: slab candidates are CONDITIONAL ground slab; the stair "
            "zone, lift walls and ground-beam pieces are not ground slab", 0, 0,
            "S8.1A recovered-region polygons (sheet frame + SH08 origin) intersected with the M4 face",
            "M4 already deducts the ground-beam bands inside the face; the lift void and the lift pit walls stay inside "
            "it (the S-BW pit outlines are not face edges); the face's one hole is the lift SE column")
    return reg, {"domes": domes, "decomposition": decomposition, "cantilever_rows": rows, "arcs": arcs,
                 "dome_faces": hits}


# ================================================================== family totals of the Urban reference
def urban_families(U):
    """Measured (low / base / high), conditional (low / high) and unmeasurable counts per family, after decisions."""
    fam = {f: {"MEAS_LOW": 0.0, "MEAS_BASE": 0.0, "MEAS_HIGH": 0.0, "COND_LOW": 0.0, "COND_HIGH": 0.0,
               "N_MEAS": 0, "N_COND": 0, "N_UNMEASURABLE": 0, "EXCLUDED_M3": 0.0}
           for f in FAMILY_ORDER + ("BLINDING",)}
    for u in U:
        F = fam.setdefault(u["FAMILY"], {"MEAS_LOW": 0.0, "MEAS_BASE": 0.0, "MEAS_HIGH": 0.0, "COND_LOW": 0.0,
                                         "COND_HIGH": 0.0, "N_MEAS": 0, "N_COND": 0, "N_UNMEASURABLE": 0,
                                         "EXCLUDED_M3": 0.0})
        st = u["M5"]
        if st in ("EXCLUDED_SAME_AS_M4", "REALLOCATED_TO_DOMES", "NOT_SLAB_DOME_OPENING", "SUPERSEDED_BY_CANTILEVER"):
            F["EXCLUDED_M3"] += (u["BASE"] or 0)
            continue
        if u["CATEGORY"] == "PROVISIONAL" and st == "KEEP":
            F["MEAS_LOW"] += u["LOW"] or 0
            F["MEAS_BASE"] += u["BASE"] or 0
            F["MEAS_HIGH"] += u["HIGH"] or 0
            F["N_MEAS"] += 1
        elif st == "CONDITIONAL_DECOMPOSED":
            t = (u["DIMS"] or {}).get("t_m") or 0.0
            F["COND_LOW"] += u.get("M5_SLAB_M2", 0.0) * t
            F["COND_HIGH"] += u.get("M5_SLAB_HIGH_M2", 0.0) * t
            F["N_COND"] += 1
        elif u["CATEGORY"] == "PROVISIONAL" and st == "CONDITIONAL":
            F["COND_LOW"] += u["LOW"] or 0
            F["COND_HIGH"] += u["HIGH"] or 0
            F["N_COND"] += 1
        elif u["EXP_HIGH"] is not None:
            F["COND_LOW"] += u["EXP_LOW"] or 0
            F["COND_HIGH"] += u["EXP_HIGH"] or 0
            F["N_COND"] += 1
        else:
            F["N_UNMEASURABLE"] += 1
    return fam


# ================================================================== freelancer per family / group
def fl_by(F, key=("FAMILY",)):
    out = defaultdict(float)
    for r in F["rows"]:
        out[tuple(r[k] for k in key)] += r["VALUE_M3"]
    return out


def classify(fl, ur, has_exposure=False, scope=None):
    """Difference class of one comparison row (freelancer vs Urban measured base)."""
    if scope:
        return scope
    fl, ur = fl or 0.0, ur or 0.0
    if not fl and not ur:
        return "UNRESOLVED_REQUIRES_ENGINEER (in neither base)"
    if abs(fl - ur) <= max(TOL_M3, TOL_FRAC * max(abs(fl), abs(ur))):
        return "MATCHED_WITHIN_TOLERANCE"
    if fl and not ur:
        return "MISSING_IN_URBAN" + ("_BASE (held as unresolved exposure)" if has_exposure else "")
    if ur and not fl:
        return "MISSING_IN_FREELANCER"
    return None


# ================================================================== items M5 adds from drawn evidence (conditional only)
def plot_frame_sh08(D):
    """The plot rectangle (S-BOUN, 31.37 x 15.00 m on the foundation plan) carried to the ground-beam plan frame."""
    import ezdxf
    doc = ezdxf.readfile(str(S.DXF_ST))
    x0, y0, x1, y1 = D["sheets"]["SH10"]["sheet"]["box"]
    best = None
    for e in doc.modelspace().query("LWPOLYLINE"):
        try:
            if e.dxf.layer.upper() != "S-BOUN" or not e.closed:
                continue
        except Exception:                                   # noqa: BLE001
            continue
        pts = [(p[0], p[1]) for p in e.get_points("xy")]
        if len(pts) == 4 and all(x0 <= x <= x1 and y0 <= y <= y1 for x, y in pts):
            P = Polygon(pts)
            if best is None or P.area > best[1].area:
                best = (e.dxf.handle, P)
    o10, o8 = sheet_origin(D, "SH10"), sheet_origin(D, "SH08")
    bx = best[1].bounds
    return {"handle": best[0], "bounds_sh08": (bx[0] - o10[0] + o8[0], bx[1] - o10[1] + o8[1],
                                               bx[2] - o10[0] + o8[0], bx[3] - o10[1] + o8[1]),
            "w_m": (bx[2] - bx[0]) / 1000.0, "d_m": (bx[3] - bx[1]) / 1000.0}


def m5_items(D, U, typ, runs, plot):
    """Conditional items from drawn evidence the frozen registers do not value: the boundary-wall beam on its drawn
    run, and the neighbour-side beam of p.1 note B (a CANDIDATE reading). Pads / columns stay unmeasurable."""
    L = sum(r["centreline_m"] for r in runs)
    add = [{"UID": "M5:BOUNDARY-WALL-BEAM", "ORIGIN": "M5 (drawn run x printed typical)", "FAMILY": "BOUNDARY_WALL",
            "FLOOR": "SITE", "MARK": "BEAM", "CATEGORY": "PROVISIONAL", "LOW": L * typ["gb_w"] * typ["gb_h"],
            "BASE": L * typ["gb_w"] * typ["gb_h"], "HIGH": L * typ["bw_w"] * typ["bw_h"], "EXP_LOW": None,
            "EXP_HIGH": None, "BLOCKER": "BOUNDARY_WALL_SCOPE_AND_SECTION",
            "SOURCE": "S-BOUN strips " + ", ".join(f"{r['handle']} {r['centreline_m']:.2f} m" for r in runs),
            "DIMS": {"length_m": L}, "COMPONENT": "BOUNDARY-WALL-BEAM", "M5": "CONDITIONAL",
            "FORMULA": f"drawn run x p.14 GB {typ['gb_w']:.2f} x {typ['gb_h']:.2f} (low) .. schedule B.W "
                       f"{typ['bw_w']:.2f} x {typ['bw_h']:.2f} (high)",
            "M5_NOTE": "scope (is the boundary wall in the contract?) and section (p.14 vs B.W row) unresolved"},
           {"UID": "M5:BOUNDARY-WALL-PADS-COLUMNS", "ORIGIN": "M5 (printed typical, spacing not printed)",
            "FAMILY": "BOUNDARY_WALL", "FLOOR": "SITE", "MARK": "PADS_COLUMNS", "CATEGORY": "UNRESOLVED", "LOW": None,
            "BASE": None, "HIGH": None, "EXP_LOW": None, "EXP_HIGH": None, "BLOCKER": "SPACING_NOT_PRINTED",
            "SOURCE": "p.14 typical: " + typ["typical_text"], "DIMS": {}, "COMPONENT": "BOUNDARY-WALL-PADS-COLUMNS",
            "M5": "KEEP", "FORMULA": "", "M5_NOTE": "column / pad spacing and which runs are RC: " + typ["missing"]}]
    # the neighbour-side exterior ground beams (both long plot edges)
    x0, y0, x1, y1 = plot["bounds_sh08"]
    nb = 0.0
    for u in U:
        if u["ORIGIN"] != "M4" or u["FAMILY"] != "GROUND_BEAMS" or u["CATEGORY"] != "PROVISIONAL":
            continue
        if (u["DIMS"] or {}).get("arch_class") != "EXTERIOR_WALL":
            continue
        bid = u["COMPONENT"].split(":")[-1]
        P = band_polygon(D, "SH08", bid)
        if P is None:
            continue
        bx = P.bounds
        if (bx[2] - bx[0]) > (bx[3] - bx[1]) and (abs(bx[1] - y0) <= 350 or abs(bx[3] - y1) <= 350):
            nb += u["DIMS"].get("length_m") or 0.0
    add.append({"UID": "M5:NEIGHBOUR-SIDE-UPPER-BEAM", "ORIGIN": "M5 (p.1 note B, CANDIDATE)",
                "FAMILY": "GB_PERIMETER", "FLOOR": "GROUND", "MARK": "PERIMETER", "CATEGORY": "UNRESOLVED",
                "LOW": None, "BASE": None, "HIGH": None, "EXP_LOW": 0.0, "EXP_HIGH": nb * typ["bw_w"] * typ["bw_h"],
                "BLOCKER": "NOTE_B_CANDIDATE", "SOURCE": "p.1 note B: " + typ["note_b"],
                "DIMS": {"length_m": nb}, "COMPONENT": "NEIGHBOUR-SIDE-UPPER-BEAM", "M5": "KEEP",
                "FORMULA": f"exterior GB length on the two neighbour edges {nb:.2f} m x B.W {typ['bw_w']:.2f} x "
                           f"{typ['bw_h']:.2f} as the upper bound of a second beam",
                "M5_NOTE": "only if note B means a second (upper) beam over the black-brick wall on the neighbour side"})
    # the S-stage boundary-wall row is the same element as the M5 beam (one owner)
    for u in U:
        if u["FAMILY"] == "BOUNDARY_WALL" and u["ORIGIN"].startswith("M1"):
            u["M5"], u["M5_NOTE"] = "EXCLUDED_SAME_AS_M4", "valued by M5:BOUNDARY-WALL-BEAM / PADS-COLUMNS"
    U.extend(add)
    return {"length_m": L, "neighbour_m": nb, **typ}


def planted_columns(D, conv):
    """Planted columns labelled on a slab plan with their printed section ('P.C 20x70'): they start on that slab and
    rise one storey. The generic route reads columns from the column plan only, so M4 has none of them (a detection
    gap, M5 finding); the S8.5 census records the same population."""
    above = {"SH06": "1F", "SH04": "2F"}
    out = []
    for sh, st in above.items():
        for t in D["sheets"][sh].get("texts", []) or []:
            m = re.fullmatch(r"\s*P\.?\s*C\s*(\d{2,3})\s*[xX*]\s*(\d{2,3})\s*", t.get("value") or "")
            if not m:
                continue
            w, d = int(m.group(1)) / 100.0, int(m.group(2)) / 100.0
            h = conv.base(f"STOREY_HEIGHT_{st}") if f"STOREY_HEIGHT_{st}" in conv.items else None
            v = w * d * h if h else None
            out.append({"UID": f"M5:PLANTED:{sh}:{round(t['x'])},{round(t['y'])}", "ORIGIN": "M5 (printed label)",
                        "FAMILY": "COLUMNS", "FLOOR": st, "MARK": "P.C", "CATEGORY": "PROVISIONAL", "LOW": v,
                        "BASE": v, "HIGH": v, "EXP_LOW": None, "EXP_HIGH": None, "BLOCKER": "M4_DETECTION_GAP",
                        "SOURCE": f"{sh} text '{t['value']}' at ({t['x']:.0f}, {t['y']:.0f}) layer {t.get('layer')}",
                        "DIMS": {"section_m": (w, d), "height_m": h}, "COMPONENT": f"PLANTED:{sh}:{t['id']}",
                        "M5": "KEEP", "FORMULA": f"{w:.2f} x {d:.2f} (label) x storey height {st} {h}",
                        "M5_NOTE": "planted column on the slab below; not read by the generic route (column plan only)"})
    return out
