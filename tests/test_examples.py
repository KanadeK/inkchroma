from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def run_example(name: str, output: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "inkchroma",
            "compare",
            str(ROOT / "examples" / name / "project.json"),
            "--out",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )


@pytest.mark.parametrize("name", ["blue-family", "different-sizes"])
def test_success_examples_run_through_real_cli(name: str, tmp_path: Path) -> None:
    output = tmp_path / name

    result = run_example(name, output)

    assert result.returncode == 0
    assert result.stderr == ""
    analysis = json.loads((output / "analysis.json").read_text(encoding="utf-8"))
    expected_points = 96 if name == "blue-family" else 64
    assert all(len(sample["profile"]) == expected_points for sample in analysis["samples"])
    if name == "blue-family":
        closest = analysis["comparisons"][0]
        assert (closest["left"], closest["right"]) == ("midnight-a", "midnight-b")


def test_blank_example_has_documented_failure_and_no_output(tmp_path: Path) -> None:
    output = tmp_path / "blank"

    result = run_example("blank-strip", output)

    assert result.returncode == 2
    assert "sample 'blank-a': no measurable ink signal" in result.stderr
    assert "rescan or lower minimum_signal_delta_e" in result.stderr
    assert not output.exists()
