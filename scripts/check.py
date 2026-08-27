from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path
from typing import Final
from zipfile import ZIP_DEFLATED, ZipFile

from inkchroma import __version__

ROOT: Final = Path(__file__).resolve().parents[1]
DIST: Final = ROOT / "dist"
WORK: Final = ROOT / ".check-work"
EXAMPLES: Final = ROOT / "examples"
REPORT_NAMES: Final = {"analysis.json", "distances.csv", "profiles.svg", "report.html"}


def run(
    label: str,
    args: list[str | Path],
    *,
    expected: int = 0,
    capture: bool = False,
) -> subprocess.CompletedProcess[str]:
    command = [str(item) for item in args]
    print(f"\n==> {label}\n$ {' '.join(command)}", flush=True)
    result = subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        capture_output=capture,
        text=True,
    )
    if capture:
        if result.stdout:
            print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, end="", file=sys.stderr)
    if result.returncode != expected:
        raise SystemExit(f"{label} failed with exit code {result.returncode}; expected {expected}")
    return result


def verify(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def verify_success_output(output: Path) -> None:
    verify(output.is_dir(), f"expected output directory: {output}")
    verify({path.name for path in output.iterdir()} == REPORT_NAMES, "incomplete report set")
    analysis: dict[str, object] = json.loads((output / "analysis.json").read_text(encoding="utf-8"))
    comparisons = analysis["comparisons"]
    if not isinstance(comparisons, list) or not comparisons:
        raise SystemExit("missing comparisons")
    closest = comparisons[0]
    verify(
        isinstance(closest, dict)
        and (closest.get("left"), closest.get("right")) == ("midnight-a", "midnight-b"),
        "blue-family closest pair changed",
    )
    verify(
        "<script" not in (output / "report.html").read_text(encoding="utf-8").lower(),
        "report.html must remain script-free",
    )


def create_example_bundle(destination: Path) -> None:
    with ZipFile(destination, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(candidate for candidate in EXAMPLES.rglob("*") if candidate.is_file()):
            archive.write(path, path.relative_to(EXAMPLES).as_posix())


def main() -> int:
    os.chdir(ROOT)
    uv = shutil.which("uv")
    if uv is None:
        raise SystemExit("uv is required; install uv 0.11.20 and rerun the gate")

    run("Lockfile is current", [uv, "lock", "--check"])
    run(
        "Formatting", [sys.executable, "-m", "ruff", "format", "--check", "src", "tests", "scripts"]
    )
    run("Static lint", [sys.executable, "-m", "ruff", "check", "src", "tests", "scripts"])
    run("Strict types", [sys.executable, "-m", "mypy", "src", "tests", "scripts"])
    run(
        "Tests and branch coverage",
        [
            sys.executable,
            "-m",
            "pytest",
            "--cov=inkchroma",
            "--cov-branch",
            "--cov-report=term-missing",
            "--cov-fail-under=90",
        ],
    )
    run(
        "Locked dependency audit",
        [uv, "audit", "--preview-features", "audit-command", "--locked", "--no-progress"],
    )

    for generated in (DIST, ROOT / "build", ROOT / "src" / "inkchroma.egg-info", WORK):
        if generated.exists():
            shutil.rmtree(generated)
    DIST.mkdir()
    WORK.mkdir()

    run("Wheel and source distribution", [sys.executable, "-m", "build"])
    wheel = DIST / f"inkchroma-{__version__}-py3-none-any.whl"
    source = DIST / f"inkchroma-{__version__}.tar.gz"
    bundle = DIST / f"inkchroma-examples-v{__version__}.zip"
    verify(wheel.is_file(), f"missing wheel: {wheel.name}")
    verify(source.is_file(), f"missing source distribution: {source.name}")
    create_example_bundle(bundle)
    verify(bundle.is_file(), f"missing example bundle: {bundle.name}")
    source_prefix = f"inkchroma-{__version__}/"
    with tarfile.open(source, "r:gz") as archive:
        source_members = set(archive.getnames())
    expected_source_members = {
        f"{source_prefix}CHANGELOG.md",
        f"{source_prefix}docs/spec.md",
        f"{source_prefix}examples/blue-family/project.json",
        f"{source_prefix}scripts/check.py",
        f"{source_prefix}uv.lock",
    }
    verify(
        expected_source_members <= source_members,
        "source distribution is missing development, documentation, or example files",
    )

    source_demo = ROOT / "demo-output"
    verify(
        not source_demo.exists(),
        "demo-output already exists; move or remove it before running the release gate",
    )
    run(
        "README source command",
        [
            uv,
            "run",
            "--locked",
            "inkchroma",
            "compare",
            "examples/blue-family/project.json",
            "--out",
            "demo-output",
        ],
    )
    verify_success_output(source_demo)
    documented_csv = (source_demo / "distances.csv").read_text(encoding="utf-8").strip()
    verify(
        documented_csv in (ROOT / "README.md").read_text(encoding="utf-8"),
        "README pair-distance example does not match the real output",
    )
    shutil.rmtree(source_demo)

    environment = WORK / "clean-venv"
    run("Create clean environment", [sys.executable, "-m", "venv", environment])
    clean_python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    installed_cli = environment / ("Scripts/inkchroma.exe" if os.name == "nt" else "bin/inkchroma")
    run(
        "Install built wheel without the source tree",
        [
            uv,
            "pip",
            "install",
            "--offline",
            "--strict",
            "--link-mode",
            "copy",
            "--python",
            clean_python,
            wheel,
        ],
    )
    run(
        "Verify installed metadata",
        [
            clean_python,
            "-c",
            (
                "from importlib.metadata import version; import inkchroma; "
                f"assert version('inkchroma') == inkchroma.__version__ == '{__version__}'"
            ),
        ],
    )
    verify(installed_cli.is_file(), f"installed console entry is missing: {installed_cli}")

    extracted_examples = WORK / "release-examples"
    with ZipFile(bundle) as archive:
        archive.extractall(extracted_examples)

    installed_output = WORK / "installed-output"
    run(
        "Installed CLI success example",
        [
            installed_cli,
            "compare",
            extracted_examples / "blue-family/project.json",
            "--out",
            installed_output,
        ],
    )
    verify_success_output(installed_output)

    boundary_output = WORK / "boundary-output"
    run(
        "Installed CLI boundary example",
        [
            installed_cli,
            "compare",
            extracted_examples / "different-sizes/project.json",
            "--out",
            boundary_output,
        ],
    )
    boundary: dict[str, object] = json.loads(
        (boundary_output / "analysis.json").read_text(encoding="utf-8")
    )
    samples = boundary["samples"]
    verify(
        isinstance(samples, list)
        and all(isinstance(sample, dict) and len(sample["profile"]) == 64 for sample in samples),
        "different-sizes example did not normalize every profile to 64 points",
    )

    failure_output = WORK / "failure-output"
    failure = run(
        "Installed CLI documented failure",
        [
            installed_cli,
            "compare",
            extracted_examples / "blank-strip/project.json",
            "--out",
            failure_output,
        ],
        expected=2,
        capture=True,
    )
    verify(
        "sample 'blank-a': no measurable ink signal" in (failure.stderr or ""),
        "installed failure did not name blank-a and its signal problem",
    )
    verify(not failure_output.exists(), "failed installed run left an output directory")

    shutil.rmtree(WORK)
    print("\nINKCHROMA_CHECK=PASS")
    print(f"release assets: {wheel.name}, {source.name}, {bundle.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
