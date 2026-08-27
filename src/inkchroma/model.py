from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


class InputError(ValueError):
    """The user can repair the supplied project or image input."""


@dataclass(frozen=True)
class LaneSpec:
    x_start: int
    x_end: int


@dataclass(frozen=True)
class SampleSpec:
    name: str
    image: Path
    lane: LaneSpec
    solvent_front_y: int
    origin_y: int


@dataclass(frozen=True)
class Project:
    profile_points: int
    minimum_signal_delta_e: float
    samples: tuple[SampleSpec, ...]


@dataclass(frozen=True)
class ProfilePoint:
    rf: float
    delta_l: float
    delta_a: float
    delta_b: float
    strength: float
    rgb: tuple[int, int, int]


@dataclass(frozen=True)
class Band:
    rf_start: float
    rf_end: float
    rf_center: float
    peak_signal: float
    rgb: tuple[int, int, int]


@dataclass(frozen=True)
class Profile:
    name: str
    points: tuple[ProfilePoint, ...]
    peak_signal: float
    bands: tuple[Band, ...]


@dataclass(frozen=True)
class Comparison:
    left: str
    right: str
    distance: float
    right_index_shift: int


@dataclass(frozen=True)
class Analysis:
    profiles: tuple[Profile, ...]
    comparisons: tuple[Comparison, ...]
