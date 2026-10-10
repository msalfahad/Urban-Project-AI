"""Generic curve engine (PA05 §7).  Arc length, sector / segment / semicircle
areas, polyarc chains and offset curves from parameters only; no project
radii."""

from __future__ import annotations

import math


def arc_length(radius, sweep_rad):
    if radius <= 0 or sweep_rad <= 0:
        raise ValueError("radius and sweep must be positive")
    return radius * sweep_rad


def sector_area(radius, sweep_rad):
    return 0.5 * radius * radius * sweep_rad


def segment_area(radius, sweep_rad):
    """Circular segment between chord and arc."""
    return 0.5 * radius * radius * (sweep_rad - math.sin(sweep_rad))


def segment_from_chord_rise(chord, rise):
    """Radius, sweep and area of a circular segment given chord and rise (sagitta)."""
    if chord <= 0 or rise <= 0:
        raise ValueError("chord and rise must be positive")
    half = chord / 2
    r = (half * half + rise * rise) / (2 * rise)
    sweep = 2 * math.asin(min(1.0, half / r))
    kind = "SEMICIRCLE" if abs(rise - half) < 1e-9 else ("SEGMENT_LESS_THAN_SEMICIRCLE" if rise < half else "SEGMENT_MORE_THAN_SEMICIRCLE")
    if rise > half:
        sweep = 2 * math.pi - sweep
    return {"R": r, "SWEEP_RAD": sweep, "AREA": segment_area(r, sweep), "ARC_LENGTH": arc_length(r, sweep), "KIND": kind, "BOUNDING_BOX_USED": False}


def semicircle(width):
    r = width / 2
    return {"R": r, "AREA": math.pi * r * r / 2, "ARC_LENGTH": math.pi * r, "KIND": "SEMICIRCLE"}


def arched_opening(width, rect_height, rise=None):
    """Rectangle plus a circular head: semicircular when rise is None or equals width/2, else a segment."""
    head = semicircle(width) if rise is None or abs(rise - width / 2) < 1e-9 else segment_from_chord_rise(width, rise)
    return {"RECT_M2": width * rect_height, "HEAD_M2": head["AREA"], "TOTAL_M2": width * rect_height + head["AREA"], "HEAD": head,
            "TOTAL_HEIGHT": rect_height + (width / 2 if rise is None else rise), "JAMB_LENGTH": 2 * rect_height, "HEAD_ARC_LENGTH": head["ARC_LENGTH"], "BOUNDING_BOX_USED": False}


def polyarc_length(pieces):
    """pieces: [{"KIND": "LINE", "LENGTH": l} | {"KIND": "ARC", "R": r, "SWEEP_RAD": s}] -> developed length."""
    L = 0.0
    for p in pieces:
        if p["KIND"] == "LINE":
            L += p["LENGTH"]
        elif p["KIND"] == "ARC":
            L += arc_length(p["R"], p["SWEEP_RAD"])
        else:
            raise ValueError(f"unknown piece {p['KIND']}")
    return L


def offset_arc(radius, sweep_rad, offset):
    """An offset curve of an arc is an arc with radius +- offset (established only when the source draws it; this is geometry, not evidence)."""
    r2 = radius + offset
    if r2 <= 0:
        raise ValueError("offset collapses the arc")
    return {"R": r2, "SWEEP_RAD": sweep_rad, "ARC_LENGTH": arc_length(r2, sweep_rad)}


def sweep_of(start_angle, end_angle):
    s = (end_angle - start_angle) % (2 * math.pi)
    return s if s > 1e-12 else 2 * math.pi


def arc_from_primitive(p):
    """Length and endpoints of a normalised ARC primitive (cx, cy, radius, start_angle, end_angle)."""
    s = sweep_of(p.start_angle, p.end_angle)
    a = (p.cx + p.radius * math.cos(p.start_angle), p.cy + p.radius * math.sin(p.start_angle))
    b = (p.cx + p.radius * math.cos(p.end_angle), p.cy + p.radius * math.sin(p.end_angle))
    return {"R": p.radius, "SWEEP_RAD": s, "LENGTH": arc_length(p.radius, s), "START": a, "END": b, "CHORD": math.dist(a, b)}
