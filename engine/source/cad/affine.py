"""2D affine maps for K1: x' = a x + c y + e, y' = b x + d y + f.

Composition is explicit (`outer @ inner` applies `inner` first) because the
ORDER is the whole content of a CAD placement.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Affine2:
    a: float = 1.0
    b: float = 0.0
    c: float = 0.0
    d: float = 1.0
    e: float = 0.0
    f: float = 0.0

    @staticmethod
    def identity() -> "Affine2":
        return Affine2()

    @staticmethod
    def translation(x: float, y: float) -> "Affine2":
        return Affine2(e=float(x), f=float(y))

    @staticmethod
    def rotation(theta: float) -> "Affine2":
        co, si = math.cos(theta), math.sin(theta)
        return Affine2(co, si, -si, co)

    @staticmethod
    def scale(sx: float, sy: float) -> "Affine2":
        return Affine2(float(sx), 0.0, 0.0, float(sy))

    @staticmethod
    def linear(a: float, b: float, c: float, d: float) -> "Affine2":
        return Affine2(a, b, c, d)

    def __matmul__(self, inner: "Affine2") -> "Affine2":
        o, i = self, inner
        return Affine2(o.a * i.a + o.c * i.b, o.b * i.a + o.d * i.b,
                       o.a * i.c + o.c * i.d, o.b * i.c + o.d * i.d,
                       o.a * i.e + o.c * i.f + o.e, o.b * i.e + o.d * i.f + o.f)

    def apply(self, p) -> tuple:
        x, y = float(p[0]), float(p[1])
        return (self.a * x + self.c * y + self.e, self.b * x + self.d * y + self.f)

    def apply_linear(self, v) -> tuple:
        x, y = float(v[0]), float(v[1])
        return (self.a * x + self.c * y, self.b * x + self.d * y)

    def det(self) -> float:
        return self.a * self.d - self.b * self.c

    def is_similarity(self, rel_tol: float) -> bool:
        """Conformal linear part: equal column lengths, orthogonal columns."""
        n1 = self.a * self.a + self.b * self.b
        n2 = self.c * self.c + self.d * self.d
        s = max(n1, n2)
        if s == 0.0:
            return False
        return abs(n1 - n2) <= rel_tol * s and abs(self.a * self.c + self.b * self.d) <= rel_tol * s
