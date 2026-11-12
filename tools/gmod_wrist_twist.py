"""Model-specific Source wrist-twist drivers for existing MMD helper bones."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from collections.abc import Mapping


GENERATED_HEADER = "// MCI generated wrist twist drivers\n"
GENERATED_FILENAME = "mci_generated_wrist_twist.vrd"


@dataclass(frozen=True)
class BonePose:
    parent: str
    position: tuple[float, float, float]
    rotation: tuple[float, float, float]


def multiply(a, b):
    x, y, z, w = a
    X, Y, Z, W = b
    return (w*X+x*W+y*Z-z*Y, w*Y-x*Z+y*W+z*X,
            w*Z+x*Y-y*X+z*W, w*W-x*X-y*Y-z*Z)


def from_euler(rotation):
    x, y, z = (v / 2 for v in rotation)
    sx, cx, sy, cy, sz, cz = math.sin(x), math.cos(x), math.sin(y), math.cos(y), math.sin(z), math.cos(z)
    return (sx*cy*cz-cx*sy*sz, cx*sy*cz+sx*cy*sz,
            cx*cy*sz-sx*sy*cz, cx*cy*cz+sx*sy*sz)


def to_euler(q):
    x, y, z, w = q
    return (math.atan2(2*(w*x+y*z), 1-2*(x*x+y*y)),
            math.asin(max(-1.0, min(1.0, 2*(w*y-z*x)))),
            math.atan2(2*(w*z+x*y), 1-2*(y*y+z*z)))


def axis_rotation(axis, degrees):
    angle = math.radians(degrees) / 2
    return (*(v*math.sin(angle) for v in axis), math.cos(angle))


def _short(name: str) -> str:
    return name.removeprefix("ValveBiped.")


def _degrees(q):
    return " ".join(f"{math.degrees(v):.6f}" for v in to_euler(q))


def build_vrd(poses: Mapping[str, BonePose], declared: set[str], existing: str = "") -> tuple[str, list[str]]:
    """Return only missing wrist helpers; authored VRD helpers take precedence.

    Rotate an existing ZHandTwist halfway with the hand's axial rotation. Its
    parent-relative position stays fixed, and hand/forearm transforms are never
    changed. The trigger grid has 25 entries, below Source's 32-entry array.
    """
    existing = existing.lstrip("\ufeff")
    authored = {_short(match).casefold() for match in
                re.findall(r"^\s*<helper>\s+\"?([^\s\"]+)", existing, re.MULTILINE | re.IGNORECASE)}
    blocks = []
    generated = []
    for side in ("L", "R"):
        helper = f"ZHandTwist_{side}"
        hand = f"ValveBiped.Bip01_{side}_Hand"
        forearm = f"ValveBiped.Bip01_{side}_Forearm"
        if helper.casefold() in authored or not {helper, hand, forearm} <= declared:
            continue
        if not {helper, hand, forearm} <= poses.keys():
            continue
        hp, wp = poses[hand], poses[helper]
        if hp.parent != forearm or wp.parent != forearm:
            continue
        values = (*hp.position, *hp.rotation, *wp.position, *wp.rotation)
        if not all(math.isfinite(v) for v in values):
            continue
        length = math.sqrt(sum(v*v for v in hp.position))
        if length < 1e-5:
            continue
        axis = tuple(v / length for v in hp.position)
        distance = sum(a*b for a, b in zip(axis, wp.position))
        off_axis = math.sqrt(sum((p-distance*a)**2 for p, a in zip(wp.position, axis)))
        if not 0 < distance < length or off_axis > length * 0.2:
            continue
        # Build an orthogonal swing basis around the actual forearm segment.
        seed = (0.0, 1.0, 0.0) if abs(axis[1]) < 0.9 else (0.0, 0.0, 1.0)
        dot = sum(a*b for a, b in zip(axis, seed))
        perpendicular = tuple(s-dot*a for s, a in zip(seed, axis))
        norm = math.sqrt(sum(v*v for v in perpendicular))
        y = tuple(v / norm for v in perpendicular)
        z = (axis[1]*y[2]-axis[2]*y[1], axis[2]*y[0]-axis[0]*y[2], axis[0]*y[1]-axis[1]*y[0])
        hand_rest, helper_rest = from_euler(hp.rotation), from_euler(wp.rotation)
        lines = [f"<helper> {helper} {_short(forearm)} {_short(forearm)} {_short(hand)}\n",
                 "<basepos> " + " ".join(f"{v:.6f}" for v in wp.position) + "\n"]
        swings = [axis_rotation(y, 0), axis_rotation(y, -60), axis_rotation(y, 60),
                  axis_rotation(z, -60), axis_rotation(z, 60)]
        for swing in swings:
            for roll in (0, -60, 60, -120, 120):
                driver = multiply(multiply(swing, axis_rotation(axis, roll)), hand_rest)
                target = multiply(axis_rotation(axis, roll * 0.5), helper_rest)
                lines.append(f"<trigger> 60.0 {_degrees(driver)} {_degrees(target)} 0 0 0\n")
        blocks.append("".join(lines))
        generated.append(helper)
    return "\n".join(blocks), generated
