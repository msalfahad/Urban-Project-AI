"""T-084 hand arithmetic (stdlib only). Inputs are the readings in README.md; nothing is read from any file.
One step = 1/2 x riser x tread x width (owner Q-19); riser = rise / counted risers (UP-STAIR-009)."""
from math import hypot

def step(r, t, w):
    return 0.5 * r * t * w

def flight(name, rise, n_total, n_flight, t, w):
    r = rise / n_total
    return name, r, n_flight, step(r, t, w), n_flight * step(r, t, w)

T = 0.30
rows = [
    # released (counts agree between the section and the plan)
    flight("E1 entrance court +0.15 -> GF +1.00", 0.85, 5, 5, T, 2.80),
    flight("D1 GF hall +1.00 -> lobby +0.30", 0.70, 4, 4, T, 1.20),
    # held: GF -> 1F candidates (section A-A 27 / arch GF plan 25 / structural 28)
    flight("MS1 C27 lower (section)", 4.50, 27, 10, T, 1.20),
    flight("MS1 C27 upper (section)", 4.50, 27, 12, T, 1.20),
    flight("MS1 C25 lower (arch plan)", 4.50, 25, 10, T, 1.20),
    flight("MS1 C25 upper (arch plan)", 4.50, 25, 11, T, 1.20),
    flight("MS1 C28 lower (structural)", 4.50, 28, 12, T, 1.20),
    flight("MS1 C28 upper (structural)", 4.50, 28, 12, T, 1.20),
    # held: 1F -> 2F candidates (section 25 / arch 1F plan 27 / structural 24)
    flight("MS2 C25 lower (section)", 4.20, 25, 12, T, 1.20),
    flight("MS2 C25 upper (section)", 4.20, 25, 12, T, 1.20),
    flight("MS2 C27 lower (arch plan)", 4.20, 27, 12, T, 1.20),
    flight("MS2 C27 upper (arch plan)", 4.20, 27, 11, T, 1.20),
    flight("MS2 C24 lower (structural)", 4.20, 24, 12, T, 1.20),
    flight("MS2 C24 upper (structural)", 4.20, 24, 11, T, 1.20),
    # held: round stair, plan count only (no section)
    flight("RS straight (plan 28)", 4.50, 28, 11, T, 1.20),
    flight("RS arrival (plan 28)", 4.50, 28, 5, T, 1.25),
]
for name, r, n, one, tot in rows:
    print(f"{name:40s} riser {r:.6f}  n {n:2d}  one {one:.6f}  steps {tot:.4f}")

def waist(n_risers, n_goings, r, t=T, w=1.20, th=0.16):
    L = hypot(n_goings * t, n_risers * r)
    return L, w * L * th

print("candidate waists at the 'T 16' slab tag (HELD, owner Q-47):")
for name, n, g, r in [("MS1 lower", 10, 10, 4.5 / 27), ("MS1 upper", 12, 11, 4.5 / 27),
                      ("MS2 lower", 12, 11, 4.2 / 25), ("MS2 upper", 12, 11, 4.2 / 25)]:
    L, v = waist(n, g, r)
    print(f"  {name:10s} sloped {L:.3f} m  x 1.20 x 0.16 = {v:.4f} m3")
print("candidate landings at 0.16: MS1 flat quarter 1.20 x 1.25 =", round(1.20 * 1.25 * 0.16, 4),
      "; MS2 half landing 2.50 x 1.25 =", round(2.50 * 1.25 * 0.16, 4))
print("freelancer: main 4x1.2x5.3x0.28 =", round(4 * 1.2 * 5.3 * 0.28, 3), "+ landings 3x1.2x1.4x0.20 =",
      round(3 * 1.2 * 1.4 * 0.20, 3), "; entrance 1.8x2.8x0.28 =", round(1.8 * 2.8 * 0.28, 3),
      "; stair 2 1.2x16.4x0.28 =", round(1.2 * 16.4 * 0.28, 3))
