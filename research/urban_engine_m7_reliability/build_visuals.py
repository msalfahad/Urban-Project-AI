"""M7 visual engineering QA (14_VISUAL_ENGINEERING_QA.pdf). Geometry pages show SYNTHETIC villas only (the generator's
drawings, regenerated here); ST7757 appears as numbers only - no client drawing is rendered or committed.

    python3 -I research/urban_engine_m7_reliability/build_visuals.py
"""

from __future__ import annotations

import csv
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKG = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import matplotlib                                          # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt                            # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages       # noqa: E402
from matplotlib.patches import Polygon as MPoly            # noqa: E402

V4 = "engine/profiles/URBAN_M5_GENERIC_CONVENTIONS_V4.json"
V5 = "engine/profiles/URBAN_M7_GENERIC_CONVENTIONS_V5.json"
INK, MUTED, GRID = "#1f2933", "#616e7c", "#d9e2ec"
CLS = {"PANEL": "#7fb77e", "BEAM": "#9aa5b1", "COLUMN": "#1f2933", "OPENING": "#d64545", "OPENING_SUSPECT": "#f0a43a",
       "JUNCTION_GAP": "#7b61c4", "DETAIL": "#e4e7eb", "OPEN_BOUNDARY": "#f7d070"}
SERIES = {"V4": "#9aa5b1", "V5": "#2f6fb0"}
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": MUTED, "axes.labelcolor": INK,
                     "xtick.color": MUTED, "ytick.color": MUTED, "axes.grid": True, "grid.color": GRID,
                     "axes.spines.top": False, "axes.spines.right": False})


def _text_page(pdf, title, lines):
    fig = plt.figure(figsize=(11.69, 8.27))
    fig.text(0.06, 0.92, title, fontsize=17, color=INK, weight="bold")
    y = 0.85
    for ln in lines:
        fig.text(0.06, y, ln, fontsize=10.5, color=INK if not ln.startswith("  ") else MUTED, family="DejaVu Sans")
        y -= 0.034
    pdf.savefig(fig)
    plt.close(fig)


def _held():
    return json.loads((PKG / "heldout" / "HELDOUT_SUMMARY.json").read_text(encoding="utf-8"))["runs"]


def page_silent(pdf, H):
    fig, axes = plt.subplots(1, 2, figsize=(11.69, 8.27))
    fams = ["COLUMNS", "SLABS", "BEAMS", "FOOTINGS"]
    for ax, cfg, name in ((axes[0], "Q_A", "development vocabulary"), (axes[1], "Q_B", "held-out vocabulary")):
        for k, tag in enumerate(("V4", "V5")):
            s = H[f"{cfg}_{tag}"]["states_by_family"]
            vals = [s.get(f, {}).get("SILENT", 0) for f in fams]
            xs = [i + (k - 0.5) * 0.38 for i in range(len(fams))]
            bars = ax.bar(xs, vals, 0.36, color=SERIES[tag], label=f"{tag} ({'M6 engine' if tag == 'V4' else 'M7'})")
            for b, v in zip(bars, vals):
                ax.text(b.get_x() + b.get_width() / 2, v + 0.4, str(v), ha="center", color=INK, fontsize=9)
        ax.set_xticks(range(len(fams)), fams)
        ax.set_title(f"seeds 301-340, {name}", color=INK, fontsize=10.5, loc="left")
        ax.set_ylabel("rows (of 83 slab / 80 column / 83 beam / 40 footing rows)")
        ax.legend(frameon=False)
    fig.suptitle("Held-out quantities: SILENT family/storey rows - an error the engine did not report (frozen engine "
                 "af2822a)", x=0.06, ha="left", color=INK, fontsize=12)
    fig.subplots_adjust(wspace=0.3)
    pdf.savefig(fig)
    plt.close(fig)


def page_properties(pdf, H):
    ops = ["translate", "rot90", "rot180", "rot270", "mirror_x", "reorder", "explode", "dup_text", "noise_layer",
           "units_m"]
    fig, ax = plt.subplots(figsize=(11.69, 8.27))
    for k, tag in enumerate(("V4", "V5")):
        P = H[f"P_{tag}"]
        vals = [P[o]["pass"] for o in ops]
        xs = [i + (k - 0.5) * 0.38 for i in range(len(ops))]
        bars = ax.bar(xs, vals, 0.36, color=SERIES[tag], label=tag)
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v + 0.15, str(v), ha="center", color=INK, fontsize=9)
    ax.set_xticks(range(len(ops)), ops, rotation=20)
    ax.set_ylim(0, 11.5)
    ax.set_ylabel("drawings whose every quantity is unchanged (of 10)")
    ax.set_title("Metamorphic properties on held-out cluttered villas 301-310: the drawing changes, the building does "
                 "not", loc="left", color=INK)
    ax.legend(frameon=False)
    pdf.savefig(fig)
    plt.close(fig)


def page_shortfall(pdf):
    import collections
    fig, axes = plt.subplots(1, 2, figsize=(11.69, 8.27))
    for ax, fam in zip(axes, ("SLABS", "BEAMS")):
        d = json.loads((PKG / "heldout" / "Q_A_V5.json").read_text(encoding="utf-8"))
        agg = collections.Counter()
        tot = 0.0
        for r in d["drawings"]:
            for x in r["rows"]:
                if x["family"] != fam:
                    continue
                tot += x["truth_m3"]
                st = x["state"]
                if st == "REPORTED" and x["engine_m3"] == 0 and x["unresolved_high_m3"] == 0:
                    st = "storey plan missing (reported)"
                elif st == "REPORTED":
                    st = "inside unresolved range"
                elif st == "IN_RANGE":
                    st = "stair bay (ambiguous scope)"
                agg[st] += x["truth_m3"] - x["engine_m3"]
        colour = {"inside unresolved range": "#2f6fb0", "stair bay (ambiguous scope)": "#7fb77e",
                  "storey plan missing (reported)": "#f0a43a", "SILENT": "#d64545"}
        keys = [k for k in colour if agg.get(k)]
        labels = [k.replace(" (", "\n(") for k in keys]
        bars = ax.barh(labels, [agg[k] for k in keys], color=[colour[k] for k in keys])
        for b, k in zip(bars, keys):
            ax.text(b.get_width() + 1, b.get_y() + b.get_height() / 2, f"{agg[k]:.1f} m3", va="center", color=INK)
        ax.set_xlim(0, max(agg.values()) * 1.25)
        ax.set_title(f"{fam}: design truth {tot:.0f} m3", loc="left", color=INK, fontsize=10.5)
        ax.set_xlabel("m3 not in the measured total (V5, seeds 301-340)")
    fig.suptitle("No silent shortfall is not no shortfall: every missing m3 is inside a reported range, an ambiguous\n"
                 "stair bay or a storey whose plan is reported missing", x=0.06, ha="left", color=INK, fontsize=11.5)
    fig.subplots_adjust(left=0.17, wspace=0.55, top=0.84)
    pdf.savefig(fig)
    plt.close(fig)


def _faces(seed, conv, td, **kw):
    from tools import synthetic_villa_m6 as SM6
    from tools import urban_boq_m2 as CLI
    dxf = SM6.generate(td, seed, **kw)
    R = CLI.compute([str(dxf)], profile=str(Path(td) / f"villa_m6_{seed}.profile.json"), route="G",
                    conventions=str(ROOT / conv))
    return R


def _draw_sheet(ax, R, storey, title, mark_cols=None):
    D = R["generic"]["D"]
    s = next(s for s in D["model"]["sheets"] if s.get("storey") == storey and s["role"] == "SLAB_PLAN")
    rec = D["sheets"][s["sheet_id"]]
    ox, oy = s["box"][0], s["box"][1]
    u = D["unit_m"]
    for f in (rec.get("slab") or {}).get("faces", []):
        pts = [((x - ox) * u, (y - oy) * u) for x, y in f["polygon"]]
        ax.add_patch(MPoly(pts, closed=True, facecolor=CLS.get(f["class"], "#e4e7eb"), edgecolor="white", lw=0.6))
    for c in rec.get("column_boxes", []):
        ax.add_patch(MPoly([((x - ox) * u, (y - oy) * u) for x, y in
                            [(c[0], c[1]), (c[2], c[1]), (c[2], c[3]), (c[0], c[3])]], closed=True, facecolor="none",
                           edgecolor="#d64545" if mark_cols and tuple(c) not in mark_cols else INK, lw=1.2))
    ax.set_aspect("equal")
    ax.autoscale_view()
    ax.set_title(title, loc="left", color=INK, fontsize=10)
    ax.grid(False)
    return rec


def page_overlays(pdf):
    with tempfile.TemporaryDirectory() as td:
        # W7: bays merged into the design's opening bay and dropped (V4) / kept as slab with the suspect face (V5)
        a = _faces(240, V4, td, vocabulary="heldout", hard=True, m6v2=True)
        b = _faces(240, V5, td, vocabulary="heldout", hard=True, m6v2=True)
        fig, axes = plt.subplots(1, 2, figsize=(11.69, 8.27))
        _draw_sheet(axes[0], a, "GF", "V4 (M6 engine): merged bays read as one opening, not counted")
        _draw_sheet(axes[1], b, "GF", "V5: junction gaps close the cells; only the drawn void bay is opening")
        handles = [plt.Rectangle((0, 0), 1, 1, color=v) for v in CLS.values()]
        fig.legend(handles, list(CLS), loc="lower center", ncol=8, frameon=False)
        fig.suptitle("Synthetic villa 240 (M6 V2 seed, held-out vocabulary), ground-floor slab faces - W7 before / "
                     "after", x=0.06, ha="left", color=INK, fontsize=11.5)
        pdf.savefig(fig)
        plt.close(fig)
        # unrelated layer: a furniture rectangle on a column mark became a column (V4) / stays evidence only (V5)
        from tools import m7_metamorphic as MM
        from tools import synthetic_villa_m6 as SM6
        from tools import urban_boq_m2 as CLI
        dxf = SM6.generate(td, 4, hard=True, m6v2=True)
        noisy = Path(td) / "noise.dxf"
        MM.transform(dxf, noisy, "noise_layer")
        prof = str(Path(td) / "villa_m6_4.profile.json")
        fig, axes = plt.subplots(1, 2, figsize=(11.69, 8.27))
        for ax, conv, ttl in ((axes[0], V4, "V4: a furniture square read as a column cuts a beam"),
                              (axes[1], V5, "V5: layer evidence - the furniture square is no member")):
            R0 = CLI.compute([str(dxf)], profile=prof, route="G", conventions=str(ROOT / conv))
            R1 = CLI.compute([str(noisy)], profile=prof, route="G", conventions=str(ROOT / conv))
            st0 = next(s for s in R0["generic"]["D"]["model"]["sheets"] if s.get("storey") == "1F")
            base = {tuple(c) for c in R0["generic"]["D"]["sheets"][st0["sheet_id"]].get("column_boxes", [])}
            _draw_sheet(ax, R1, "1F", ttl, mark_cols=base)
        fig.suptitle("Synthetic villa 4 with an unrelated furniture layer added (1F): red outline = a column the "
                     "original drawing does not have", x=0.06, ha="left", color=INK, fontsize=11.5)
        pdf.savefig(fig)
        plt.close(fig)


def page_st7757(pdf):
    rows = [r for r in csv.DictReader((PKG / "st7757" / "BY_FAMILY.csv").open(encoding="utf-8"))
            if r["TRADE"] == "CONCRETE" and (abs(float(r["DELTA_MEASURED"])) > 1e-4 or
                                              abs(float(r["DELTA_UNRESOLVED_HIGH"])) > 1e-4)]
    fig, ax = plt.subplots(figsize=(11.69, 8.27))
    labels = [f"{r['FAMILY']} {r['STOREY']}" for r in rows]
    dm = [float(r["DELTA_MEASURED"]) for r in rows]
    du = [float(r["DELTA_UNRESOLVED_HIGH"]) for r in rows]
    ys = range(len(rows))
    ax.barh([y + 0.2 for y in ys], dm, 0.38, color="#2f6fb0", label="measured (provisional) m3")
    ax.barh([y - 0.2 for y in ys], du, 0.38, color="#f0a43a", label="unresolved exposure high m3")
    ax.set_yticks(list(ys), labels)
    ax.axvline(0, color=MUTED, lw=0.8)
    ax.set_xlabel("V5 minus V4 (m3)")
    ax.set_title("ST7757 concrete, V5 - V4 by family / storey (post-discovery; numbers only, no drawing rendered)",
                 loc="left", color=INK)
    ax.legend(frameon=False)
    pdf.savefig(fig)
    plt.close(fig)


def build(out=None):
    H = _held()
    out = out or PKG / "14_VISUAL_ENGINEERING_QA.pdf"
    with PdfPages(out, metadata={"Title": "Urban engine M7 - visual engineering QA", "CreationDate": None,
                                 "ModDate": None, "Producer": "matplotlib"}) as pdf:
        _text_page(pdf, "Urban engine M7 - visual engineering QA", [
            "Geometry pages: synthetic villas only (the generator's drawings, regenerated by this script).",
            "ST7757: numbers only. No client drawing, render or crop is in this file.",
            "",
            "1  Held-out silent quantity rows, V4 (M6 engine) vs V5 (M7), seeds 301-340",
            "2  Metamorphic properties on held-out villas 301-310",
            "3  Where the V5 shortfall is reported (no silent shortfall is not no shortfall)",
            "4  W7 before / after: bays merged into an opening (synthetic villa 240)",
            "5  Unrelated layer before / after: a furniture square as a column (synthetic villa 4)",
            "6  ST7757 V5 - V4 concrete by family / storey",
            "",
            "Colours: panel green, beam strip grey, column black, opening red, opening suspect amber,",
            "junction gap violet. Bars: V4 grey, V5 blue."])
        page_silent(pdf, H)
        page_properties(pdf, H)
        page_shortfall(pdf)
        page_overlays(pdf)
        page_st7757(pdf)
    return out


if __name__ == "__main__":
    print(build())
