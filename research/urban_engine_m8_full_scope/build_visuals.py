"""M8 visual QA (14_VISUAL_QA.pdf, built on demand, never committed). Geometry pages show SYNTHETIC villas only (the
generator's drawings, regenerated here); ST7757 appears as numbers only, and external positions only as the
differences the ST7757 runner wrote.

    python3 -I research/urban_engine_m8_full_scope/build_visuals.py OUT.pdf
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
from matplotlib.patches import Rectangle                   # noqa: E402

INK, MUTED, GRID = "#1f2933", "#616e7c", "#d9e2ec"
RUN = {"S_A": "#2f6fb0", "S_B": "#7b61c4"}
STATE = {"MEASURED": "#2e8540", "BOUNDED": "#e8890c", "QUALIFIER": "#9aa5b1", "EXPLAINED": "#9aa5b1",
         "HELD_BY_ITEMS": "#9aa5b1"}
POS = {"STAGE_RECONCILIATION": "#2f6fb0", "FREELANCE_QS": "#e8890c", "MCP_RUN_1": "#7b61c4", "MCP_RUN_2": "#c2185b"}
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": MUTED, "axes.labelcolor": INK,
                     "xtick.color": MUTED, "ytick.color": MUTED, "axes.grid": True, "grid.color": GRID,
                     "axes.spines.top": False, "axes.spines.right": False, "pdf.compression": 9})
A4L = (11.69, 8.27)


def _rows(p):
    return list(csv.DictReader((PKG / p).open(encoding="utf-8")))


def _f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _text(pdf, title, lines):
    fig = plt.figure(figsize=A4L)
    fig.text(0.06, 0.92, title, fontsize=17, color=INK, weight="bold")
    y = 0.85
    for ln in lines:
        fig.text(0.06, y, ln, fontsize=10.5, color=MUTED if ln.startswith("  ") else INK)
        y -= 0.034
    pdf.savefig(fig)
    plt.close(fig)


def page_acceptance(pdf):
    acc = _rows("06_ACCEPTANCE.csv")
    kinds = sorted({r["KIND"] for r in acc})
    fig, axes = plt.subplots(1, 2, figsize=A4L)
    for ax, col, title, target in ((axes[0], "DETECTED_PCT", "Detected (% of drawn elements)", 95),
                                   (axes[1], "IN_RANGE_CONVENTION_PCT", "Truth inside the range, convention "
                                                                         "dimensions (%)", 80)):
        for k, run in enumerate(("S_A", "S_B")):
            vals = [_f(next((r[col] for r in acc if r["RUN"] == run and r["KIND"] == kd), None)) or 0 for kd in kinds]
            ys = [i + (k - 0.5) * 0.38 for i in range(len(kinds))]
            ax.barh(ys, vals, 0.36, color=RUN[run], label={"S_A": "development vocabulary",
                                                          "S_B": "held-out vocabulary"}[run])
        ax.axvline(target, color=INK, lw=1, ls="--")
        ax.text(target, len(kinds) - 0.3, f" target {target} %", color=INK, fontsize=8)
        ax.set_yticks(range(len(kinds)))
        ax.set_yticklabels([k.replace("_", " ").lower() for k in kinds])
        ax.set_xlim(0, 105)
        ax.set_title(title, color=INK, loc="left", fontsize=11)
    axes[0].legend(loc="lower left", frameon=False)
    fig.suptitle("Held-out seeds 401 - 440: every drawn scope element against its design truth", x=0.06, ha="left",
                 fontsize=14, color=INK, weight="bold")
    pdf.savefig(fig)
    plt.close(fig)


def page_errors(pdf):
    acc = _rows("06_ACCEPTANCE.csv")
    kinds = [k for k in sorted({r["KIND"] for r in acc}) if any(r["KIND"] == k and r["N_PRINTED_MEASURED"] not in
                                                                  ("", "0") for r in acc)]
    fig, ax = plt.subplots(figsize=A4L)
    for k, (col, lab, c) in enumerate((("PRINTED_ERROR_MAX", "printed dimensions (largest)", "#2e8540"),
                                       ("CONVENTION_ERROR_MEDIAN", "convention dimensions (median)", "#e8890c"))):
        vals = [max((_f(r[col]) or 0) for r in acc if r["KIND"] == kd) * 100 for kd in kinds]
        xs = [i + (k - 0.5) * 0.38 for i in range(len(kinds))]
        ax.bar(xs, vals, 0.36, color=c, label=lab)
    ax.axhline(5, color=INK, lw=1, ls="--")
    ax.text(len(kinds) - 0.6, 5.3, "printed target 5 %", color=INK, fontsize=8)
    ax.set_xticks(range(len(kinds)))
    ax.set_xticklabels([k.replace("_", " ").lower() for k in kinds])
    ax.set_ylabel("| base - truth | / truth (%)")
    ax.legend(frameon=False)
    ax.set_title("Measured scope elements: error of the base value (both held-out runs)", loc="left", color=INK,
                 fontsize=13)
    pdf.savefig(fig)
    plt.close(fig)


def page_villas(pdf):
    S = json.loads((PKG / "heldout_postfix" / "S_A.json").read_text(encoding="utf-8"))
    vs = [(r["seed"], r["villa"]) for r in S["drawings"] if r.get("villa")]
    fig, ax = plt.subplots(figsize=A4L)
    for k, (sd, v) in enumerate(vs):
        m = v["measured_base_m3"]
        ax.plot([k, k], [v["bounded_low_m3"] / m, v["bounded_high_m3"] / m], color="#2f6fb0", lw=4, alpha=0.6,
                solid_capstyle="butt")
        ax.plot([k, k], [v["truth_low_m3"] / m, v["truth_high_m3"] / m], color=INK, lw=1.6)
    ax.axhline(1.0, color=MUTED, lw=0.8)
    ax.set_xticks(range(len(vs)))
    ax.set_xticklabels([str(sd) for sd, _ in vs], rotation=90, fontsize=7)
    ax.set_ylabel("multiple of the measured RC base")
    ax.set_title("Each held-out villa (development vocabulary): bounded total (blue band) and the whole RC truth "
                 "(black)", loc="left", color=INK, fontsize=12)
    pdf.savefig(fig)
    plt.close(fig)


def page_st_family(pdf):
    rows = [r for r in _rows("st7757/BY_FAMILY.csv") if r["TRADE"] == "CONCRETE"]
    fams = sorted({r["FAMILY"] for r in rows})
    v5 = [sum(_f(r["V5_MEASURED"]) or 0 for r in rows if r["FAMILY"] == f) for f in fams]
    v6 = [sum(_f(r["V6_MEASURED"]) or 0 for r in rows if r["FAMILY"] == f) for f in fams]
    fig, ax = plt.subplots(figsize=A4L)
    ys = list(range(len(fams)))
    ax.barh([y - 0.19 for y in ys], v5, 0.36, color="#9aa5b1", label="V5 (M7 engine)")
    ax.barh([y + 0.19 for y in ys], v6, 0.36, color="#2f6fb0", label="V6 (M8 engine)")
    ax.set_yticks(ys)
    ax.set_yticklabels([f.replace("_", " ").lower() for f in fams])
    ax.set_xlabel("measured concrete, m3 (planning base)")
    ax.legend(frameon=False, loc="lower right")
    S = json.loads((PKG / "st7757" / "SUMMARY.json").read_text(encoding="utf-8"))
    rc = S["rc_v6"]
    ax.set_title(f"ST7757 (post-discovery): measured by family.  RC V5 {S['rc_v5_measured_base']:.1f} m3 -> V6 "
                 f"{rc['measured_base']:.1f} m3, bounded {rc['bounded_low']:.1f} - {rc['bounded_high']:.1f} m3",
                 loc="left", color=INK, fontsize=11)
    pdf.savefig(fig)
    plt.close(fig)


def page_positions(pdf):
    rows = _rows("st7757/POSITIONS.csv")
    fams = [r["FAMILY"] for r in rows]
    fig, ax = plt.subplots(figsize=A4L)
    ys = list(range(len(fams)))
    for k, tag in enumerate(POS):
        vals = [_f(r[f"{tag}_V6_DIFF_PCT"]) for r in rows]
        yy = [y + (k - 1.5) * 0.2 for y in ys]
        ax.barh([y for y, v in zip(yy, vals) if v is not None], [max(min(v, 150), -150) for v in vals if v is not None],
                0.19, color=POS[tag], label=tag.replace("_", " ").lower())
    ax.axvline(0, color=INK, lw=0.8)
    ax.set_yticks(ys)
    ax.set_yticklabels([f.replace("_", " ").lower() for f in fams])
    ax.set_xlabel("V6 measured base relative to the position (%), clipped at +/- 150; missing bar: not in that source "
                  "or a zero position")
    ax.legend(frameon=False, loc="lower right", fontsize=8)
    ax.set_title("ST7757 positions after the freeze (differences only; the positions themselves stay in the M5 record)",
                 loc="left", color=INK, fontsize=11)
    pdf.savefig(fig)
    plt.close(fig)


def page_geometry(pdf):
    """a synthetic villa (seed 21): the foundation and top roof plans with every scope finding outlined by its state."""
    from tools import synthetic_villa_m8 as SM8
    from tools import urban_boq_m2 as CLI
    with tempfile.TemporaryDirectory() as td:
        dxf = SM8.generate(td, 21)
        R = CLI.compute([str(dxf)], profile=str(Path(td) / "villa_m8_21.profile.json"), route="G",
                        conventions=str(ROOT / "engine/profiles/URBAN_M8_GENERIC_CONVENTIONS_V6.json"),
                        completeness=True)
    g = R["generic"]
    D, I, u = g["D"], g["intake"], g["D"]["unit_m"]
    fig, axes = plt.subplots(1, 2, figsize=A4L)
    sheets = [(sid, rec) for sid, rec in sorted(D["sheets"].items()) if rec["sheet"]["role"] in
              ("FOUNDATION_PLAN", "SLAB_PLAN")]
    pick = [sheets[0], sheets[-1]] if len(sheets) > 1 else sheets
    for ax, (sid, rec) in zip(axes, pick):
        sh = rec["sheet"]
        org = sh.get("origin") or (0.0, 0.0)
        b = sh["box"]
        for s in I["segments"]:
            if b[0] <= s["a"][0] <= b[2] and b[1] <= s["a"][1] <= b[3]:
                ax.plot([(s["a"][0] - org[0]) * u, (s["b"][0] - org[0]) * u],
                        [(s["a"][1] - org[1]) * u, (s["b"][1] - org[1]) * u], color="#9aa5b1", lw=0.4)
        for f in g["scope"]["findings"]:
            if f["SHEET"] != sid or not f.get("BOX_M"):
                continue
            x0, y0, x1, y1 = f["BOX_M"]
            ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, lw=1.4,
                                   ec=STATE.get(f["SCOPE_STATE"], MUTED)))
            if f["SCOPE_STATE"] in ("MEASURED", "BOUNDED"):
                ax.text(x0, y1 + 0.15, f"{f['FAMILY'].lower()} {f['SCOPE_LOW_M3']:.2f}-{f['SCOPE_HIGH_M3']:.2f}",
                        fontsize=6.5, color=STATE[f["SCOPE_STATE"]])
        ax.set_aspect("equal")
        ax.set_title(f"{sh['role'].replace('_', ' ').lower()} {sh.get('storey')}", loc="left", color=INK)
        ax.grid(False)
    fig.suptitle("Synthetic villa 21: scope findings - green measured, orange bounded, grey qualifier / explained "
                 "(m3 range beside each)", x=0.06, ha="left", fontsize=12, color=INK, weight="bold")
    pdf.savefig(fig)
    plt.close(fig)


def build(out):
    H = json.loads((PKG / "heldout_postfix" / "POSTFIX_SUMMARY.json").read_text(encoding="utf-8"))
    S = json.loads((PKG / "st7757" / "SUMMARY.json").read_text(encoding="utf-8"))
    with PdfPages(out, metadata={"Title": "Urban Project AI M8 visual QA", "Creator": "build_visuals.py",
                                 "CreationDate": None, "ModDate": None}) as pdf:
        _text(pdf, "M8 full-scope generic BOQ - visual QA", [
            "Every structural family on a drawing ends measured (from the drawn plan and named conventions) or bounded",
            "(a stated range), and the BOQ reports a measured total and a bounded total.",
            "",
            f"Held-out (synthetic seeds 401 - 440, engine frozen at {H['frozen_commit']}, post-freeze fixes P1 - P4):",
            f"  villas whose whole RC truth lies inside the bounded total: "
            f"{H['runs']['S_A']['villa_total']['truth_in_bounded']} / {H['runs']['S_A']['villa_total']['n']} "
            f"(development vocabulary), {H['runs']['S_B']['villa_total']['truth_in_bounded']} / "
            f"{H['runs']['S_B']['villa_total']['n']} (held-out vocabulary)",
            f"  findings without a range: {H['runs']['S_A']['findings_without_range']} and "
            f"{H['runs']['S_B']['findings_without_range']}",
            "",
            f"ST7757 (post-discovery, not blind): RC measured {S['rc_v5_measured_base']:.1f} m3 (V5) -> "
            f"{S['rc_v6']['measured_base']:.1f} m3 (V6); bounded {S['rc_v6']['bounded_low']:.1f} - "
            f"{S['rc_v6']['bounded_high']:.1f} m3",
            f"  findings without a range: {S['scope_totals']['findings_without_range']}",
            "",
            "Verdict: NOT quotation-ready. No engineer-released quantities and no blind second project exist.",
            "  Synthetic pages test that the rules read geometry and printed notes; they are not real-drawing accuracy."])
        page_acceptance(pdf)
        page_errors(pdf)
        page_villas(pdf)
        page_st_family(pdf)
        page_positions(pdf)
        page_geometry(pdf)
    return out


if __name__ == "__main__":
    print(build(sys.argv[1] if len(sys.argv) > 1 else str(PKG / "14_VISUAL_QA.pdf")))
