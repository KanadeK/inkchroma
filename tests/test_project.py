from __future__ import annotations

import json
from pathlib import Path

import pytest

from inkchroma.model import InputError
from inkchroma.project import load_project


def write_project(tmp_path: Path, overrides: dict[str, object] | None = None) -> Path:
    (tmp_path / "strips").mkdir()
    (tmp_path / "strips" / "blue-a.png").touch()
    (tmp_path / "strips" / "blue-b.png").touch()
    data: dict[str, object] = {
        "schema_version": 1,
        "profile_points": 96,
        "minimum_signal_delta_e": 2.0,
        "samples": [
            {
                "name": "blue-a",
                "image": "strips/blue-a.png",
                "lane": {"x_start": 10, "x_end": 30},
                "solvent_front_y": 5,
                "origin_y": 100,
            },
            {
                "name": "blue-b",
                "image": "strips/blue-b.png",
                "lane": {"x_start": 12, "x_end": 32},
                "solvent_front_y": 8,
                "origin_y": 110,
            },
        ],
    }
    if overrides:
        data.update(overrides)
    path = tmp_path / "project.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_load_project_resolves_image_paths_and_settings(tmp_path: Path) -> None:
    path = write_project(tmp_path)

    project = load_project(path)

    assert project.profile_points == 96
    assert project.minimum_signal_delta_e == 2.0
    assert [sample.name for sample in project.samples] == ["blue-a", "blue-b"]
    assert project.samples[0].image == (tmp_path / "strips" / "blue-a.png").resolve()


def test_load_project_rejects_duplicate_sample_names(tmp_path: Path) -> None:
    path = write_project(tmp_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    data["samples"][1]["name"] = "blue-a"
    path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(InputError, match="duplicate sample name 'blue-a'"):
        load_project(path)


def test_load_project_rejects_unsupported_schema(tmp_path: Path) -> None:
    path = write_project(tmp_path, {"schema_version": 2})

    with pytest.raises(InputError, match="schema_version must be 1"):
        load_project(path)


def test_load_project_requires_two_samples(tmp_path: Path) -> None:
    path = write_project(tmp_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    data["samples"] = data["samples"][:1]
    path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(InputError, match="at least two samples"):
        load_project(path)


def test_load_project_names_missing_image_and_repair(tmp_path: Path) -> None:
    path = write_project(tmp_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    data["samples"][0]["image"] = "strips/missing.png"
    path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(
        InputError,
        match=r"sample 'blue-a'.*does not exist.*fix the image path",
    ):
        load_project(path)


def test_load_project_rejects_impossible_lane_coordinates(tmp_path: Path) -> None:
    path = write_project(tmp_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    data["samples"][0]["lane"] = {"x_start": 30, "x_end": 10}
    path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(InputError, match=r"sample 'blue-a'.*x_start must be less than x_end"):
        load_project(path)
