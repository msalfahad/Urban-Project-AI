"""T-139: hand slab panels (PANELS.csv) against the engine's slab panels (route G M5 panel table, committed:
research/urban_engine_m5_concrete_reconciliation/06A_SLAB_PANELS.csv = the m7 release register's SLABS lines).

Matches each hand SLAB row to one engine MEASURED panel of the same floor by net area (within 0.002 m2); prints the
engine panels with no hand row (each one is explained in T-139_SLABS_PANEL_BY_PANEL.md section 3) and the per-floor
totals. Reads no drawing. Usage: python -I reconcile_engine.py <PANELS.csv> <06A_SLAB_PANELS.csv>"""
import csv
import sys


def main(argv=None):
    pf, ef = (argv or sys.argv[1:])[:2]
    H = [r for r in csv.DictReader(open(pf)) if r["cls"] == "SLAB"]
    E = list(csv.DictReader(open(ef)))
    out = {}
    for fl in ("GF", "1F", "2F"):
        h = sorted(((float(r["area"]), r["id"], float(r["m3"])) for r in H if r["floor"] == fl), reverse=True)
        e = [(float(r["NET_AREA_M2"]), r["PANEL_ID"], r["M5_STATE"], float(r["VOLUME_M3"])) for r in E if r["FLOOR"] == fl]
        used, miss = set(), []
        for a, i, _ in h:
            c = [(abs(a - x[0]), k) for k, x in enumerate(e) if k not in used and x[2] == "MEASURED"]
            d, k = min(c)
            if d < 0.002:
                used.add(k)
            else:
                miss.append(i)
        extra = [e[k] for k in range(len(e)) if k not in used]
        hm3, em3 = sum(x[2] for x in h), sum(x[3] for x in e)
        out[fl] = (round(hm3, 4), round(em3, 4))
        print(f"{fl}: hand {len(h)} panels {sum(x[0] for x in h):.4f} m2 {hm3:.4f} m3 | engine {em3:.4f} m3 | "
              f"hand rows without an engine panel: {miss or 'none'}")
        for a, pid, st, v in extra:
            print(f"   engine panel without a hand slab row: {pid} {a:.4f} m2 {v:.4f} m3 {st}")
    th, te = sum(v[0] for v in out.values()), sum(v[1] for v in out.values())
    print(f"TOTAL hand {th:.4f} m3, engine {te:.4f} m3, engine - hand {te - th:+.4f} m3")


if __name__ == "__main__":
    main()
