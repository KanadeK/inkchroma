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
