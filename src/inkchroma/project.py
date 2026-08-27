from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from inkchroma.model import InputError, LaneSpec, Project, SampleSpec


def _integer(value: object, field: str) -> int:
    if type(value) is not int:
        raise InputError(f"{field} must be an integer; fix the project JSON")
    return value


def _number(value: object, field: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise InputError(f"{field} must be a number; fix the project JSON")
    return float(value)


def load_project(path: Path) -> Project:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise InputError(f"project file '{path}' does not exist; fix the project path") from error
    except UnicodeDecodeError as error:
        raise InputError(f"project file '{path}' is not UTF-8; save it as UTF-8 JSON") from error
    except json.JSONDecodeError as error:
        raise InputError(
            f"project file '{path}' is invalid JSON at line {error.lineno}, column {error.colno}; "
            "fix the JSON syntax"
        ) from error

    if not isinstance(raw, dict):
        raise InputError("project root must be a JSON object; fix the project JSON")

    data: dict[str, Any] = raw
    schema_version = _integer(data.get("schema_version"), "schema_version")
    if schema_version != 1:
        raise InputError("schema_version must be 1; update the project JSON")

    profile_points = _integer(data.get("profile_points"), "profile_points")
    if not 16 <= profile_points <= 512:
        raise InputError("profile_points must be between 16 and 512; fix the project JSON")

    minimum_signal = _number(data.get("minimum_signal_delta_e"), "minimum_signal_delta_e")
    if minimum_signal <= 0:
        raise InputError("minimum_signal_delta_e must be greater than 0; fix the project JSON")

    raw_samples = data.get("samples")
    if not isinstance(raw_samples, list) or len(raw_samples) < 2:
        raise InputError("project must contain at least two samples; add another sample")

    samples: list[SampleSpec] = []
    names: set[str] = set()
    base = path.resolve().parent
    for index, raw_sample in enumerate(raw_samples):
        if not isinstance(raw_sample, dict):
            raise InputError(f"sample {index + 1} must be a JSON object; fix that sample")

        name = raw_sample.get("name")
        if not isinstance(name, str) or not name.strip():
            raise InputError(f"sample {index + 1} needs a non-empty name; fix that sample")
        if name in names:
            raise InputError(f"duplicate sample name '{name}'; give every sample a unique name")
        names.add(name)

        image_value = raw_sample.get("image")
        if not isinstance(image_value, str) or not image_value:
            raise InputError(f"sample '{name}': image must be a path string; fix the image path")
        image = (base / image_value).resolve()
        if not image.is_file():
            raise InputError(
                f"sample '{name}': image '{image_value}' does not exist; fix the image path"
            )

        raw_lane = raw_sample.get("lane")
        if not isinstance(raw_lane, dict):
            raise InputError(f"sample '{name}': lane must be an object; add x_start and x_end")
        x_start = _integer(raw_lane.get("x_start"), f"sample '{name}' lane.x_start")
        x_end = _integer(raw_lane.get("x_end"), f"sample '{name}' lane.x_end")
        if x_start < 0:
            raise InputError(f"sample '{name}': x_start must be at least 0; fix the lane")
        if x_start >= x_end:
            raise InputError(
                f"sample '{name}': x_start must be less than x_end; fix the lane coordinates"
            )

        solvent_front_y = _integer(
            raw_sample.get("solvent_front_y"), f"sample '{name}' solvent_front_y"
        )
        origin_y = _integer(raw_sample.get("origin_y"), f"sample '{name}' origin_y")
        if solvent_front_y < 0:
            raise InputError(
                f"sample '{name}': solvent_front_y must be at least 0; fix the row coordinate"
            )
        if solvent_front_y >= origin_y:
            raise InputError(
                f"sample '{name}': solvent_front_y must be above origin_y; fix the row coordinates"
            )

        samples.append(
            SampleSpec(
                name=name,
                image=image,
                lane=LaneSpec(x_start=x_start, x_end=x_end),
                solvent_front_y=solvent_front_y,
                origin_y=origin_y,
            )
        )

    return Project(
        profile_points=profile_points,
        minimum_signal_delta_e=minimum_signal,
        samples=tuple(samples),
    )
