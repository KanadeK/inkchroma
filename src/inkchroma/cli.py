from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from inkchroma.analysis import analyze_project
from inkchroma.model import InputError
from inkchroma.project import load_project
from inkchroma.report import write_reports


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="inkchroma",
        description="Compare marked paper-chromatography strip scans offline.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    compare = commands.add_parser("compare", help="analyze and compare two or more strip scans")
    compare.add_argument("project", type=Path, metavar="PROJECT.json")
    compare.add_argument("--out", type=Path, required=True, metavar="OUTPUT_DIR")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        project = load_project(args.project)
        analysis = analyze_project(project)
        reports = write_reports(project, analysis, args.out)
    except InputError as error:
        print(f"inkchroma: error: {error}", file=sys.stderr)
        return 2

    print(f"Wrote {len(reports)} reports to {args.out}")
    print(f"Open {args.out / 'report.html'}")
    return 0
