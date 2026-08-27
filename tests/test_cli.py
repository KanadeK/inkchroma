from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw


def save_strip(
    path: Path,
    *,
    color: tuple[int, int, int] | None,
    y_start: int = 42,
) -> None:
    image = Image.new("RGB", (60, 120), (242, 239, 229))
    if color is not None:
        ImageDraw.Draw(image).rectangle((20, y_start, 39, y_start + 20), fill=color)
    image.save(path)


def save_project(path: Path, samples: list[tuple[str, Path]]) -> None:
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "profile_points": 32,
                "minimum_signal_delta_e": 2.0,
                "samples": [
                    {
                        "name": name,
                        "image": image.name,
                        "lane": {"x_start": 20, "x_end": 40},
                        "solvent_front_y": 10,
                        "origin_y": 110,
                    }
                    for name, image in samples
                ],
            }
        ),
        encoding="utf-8",
    )


def run_cli(project: Path, output: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "inkchroma", "compare", str(project), "--out", str(output)],
        check=False,
        capture_output=True,
        text=True,
    )


def test_compare_command_writes_complete_deterministic_reports(tmp_path: Path) -> None:
    blue_a = tmp_path / "blue-a.png"
    blue_b = tmp_path / "blue-b.png"
    save_strip(blue_a, color=(45, 76, 155))
    save_strip(blue_b, color=(48, 78, 152), y_start=43)
    project = tmp_path / "project.json"
    save_project(project, [("blue <A>", blue_a), ("blue & B", blue_b)])
    first_output = tmp_path / "first-output"
    second_output = tmp_path / "second-output"

    first = run_cli(project, first_output)
    second = run_cli(project, second_output)

    assert first.returncode == second.returncode == 0
    assert first.stderr == second.stderr == ""
    assert "report.html" in first.stdout
    expected_files = {"analysis.json", "distances.csv", "profiles.svg", "report.html"}
    assert {path.name for path in first_output.iterdir()} == expected_files
    assert {path.name for path in second_output.iterdir()} == expected_files
    assert {path.name: path.read_bytes() for path in first_output.iterdir()} == {
        path.name: path.read_bytes() for path in second_output.iterdir()
    }

    analysis = json.loads((first_output / "analysis.json").read_text(encoding="utf-8"))
    assert analysis["schema_version"] == 1
    assert [sample["name"] for sample in analysis["samples"]] == ["blue <A>", "blue & B"]
    assert len(analysis["samples"][0]["profile"]) == 32
    assert analysis["warnings"]
    assert analysis["comparisons"][0]["left"] == "blue & B"

    csv_text = (first_output / "distances.csv").read_text(encoding="utf-8")
    assert csv_text.startswith("left,right,distance,right_index_shift\n")
    csv_pairs = list(csv.DictReader(csv_text.splitlines()))
    assert (csv_pairs[0]["left"], csv_pairs[0]["right"]) == (
        analysis["comparisons"][0]["left"],
        analysis["comparisons"][0]["right"],
    )
    svg_text = (first_output / "profiles.svg").read_text(encoding="utf-8")
    html_text = (first_output / "report.html").read_text(encoding="utf-8")
    assert svg_text.startswith('<svg xmlns="http://www.w3.org/2000/svg"')
    assert "blue &lt;A&gt;" in svg_text
    assert svg_text.index("blue &lt;A&gt;") < svg_text.index("blue &amp; B")
    assert "blue &amp; B" in html_text
    assert html_text.index("blue &lt;A&gt;") < html_text.index("blue &amp; B")
    pair_table = html_text[html_text.index("<h2>Pair distances</h2>") :]
    assert pair_table.index("blue &amp; B") < pair_table.index("blue &lt;A&gt;")
    assert "<script" not in html_text.lower()


def test_compare_command_fails_before_creating_output_for_blank_strip(tmp_path: Path) -> None:
    blank_a = tmp_path / "blank-a.png"
    blank_b = tmp_path / "blank-b.png"
    save_strip(blank_a, color=None)
    save_strip(blank_b, color=None)
    project = tmp_path / "blank.json"
    save_project(project, [("blank-a", blank_a), ("blank-b", blank_b)])
    output = tmp_path / "should-not-exist"

    result = run_cli(project, output)

    assert result.returncode == 2
    assert result.stdout == ""
    assert "sample 'blank-a': no measurable ink signal" in result.stderr
    assert "rescan or lower minimum_signal_delta_e" in result.stderr
    assert not output.exists()


def test_compare_command_refuses_to_overwrite_output_directory(tmp_path: Path) -> None:
    blue_a = tmp_path / "blue-a.png"
    blue_b = tmp_path / "blue-b.png"
    save_strip(blue_a, color=(45, 76, 155))
    save_strip(blue_b, color=(48, 78, 152))
    project = tmp_path / "project.json"
    save_project(project, [("blue-a", blue_a), ("blue-b", blue_b)])
    output = tmp_path / "existing"
    output.mkdir()
    marker = output / "keep.txt"
    marker.write_text("keep", encoding="utf-8")

    result = run_cli(project, output)

    assert result.returncode == 2
    assert "output directory" in result.stderr
    assert "already exists" in result.stderr
    assert "choose a new --out path" in result.stderr
    assert list(output.iterdir()) == [marker]
    assert marker.read_text(encoding="utf-8") == "keep"
