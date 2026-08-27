from __future__ import annotations

import csv
import json
from html import escape
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from inkchroma.model import Analysis, InputError, Profile, Project

REPORT_NAMES = ("analysis.json", "distances.csv", "profiles.svg", "report.html")


def _rounded(value: float) -> float:
    result = round(value, 6)
    return 0.0 if result == 0 else result


def _analysis_json(project: Project, analysis: Analysis) -> str:
    payload: dict[str, object] = {
        "schema_version": 1,
        "settings": {
            "profile_points": project.profile_points,
            "minimum_signal_delta_e": project.minimum_signal_delta_e,
            "alignment_max_shift_points": 2,
            "distance_metric": "RMS Euclidean distance between signed CIE Lab vectors",
        },
        "warnings": list(analysis.warnings),
        "samples": [
            {
                "name": profile.name,
                "peak_signal_delta_e": _rounded(profile.peak_signal),
                "bands": [
                    {
                        "rf_start": _rounded(band.rf_start),
                        "rf_end": _rounded(band.rf_end),
                        "rf_center": _rounded(band.rf_center),
                        "peak_signal_delta_e": _rounded(band.peak_signal),
                        "rgb": list(band.rgb),
                    }
                    for band in profile.bands
                ],
                "profile": [
                    {
                        "rf": _rounded(point.rf),
                        "delta_l": _rounded(point.delta_l),
                        "delta_a": _rounded(point.delta_a),
                        "delta_b": _rounded(point.delta_b),
                        "strength_delta_e": _rounded(point.strength),
                        "rgb": list(point.rgb),
                    }
                    for point in profile.points
                ],
            }
            for profile in analysis.profiles
        ],
        "comparisons": [
            {
                "left": comparison.left,
                "right": comparison.right,
                "distance": _rounded(comparison.distance),
                "right_index_shift": comparison.right_index_shift,
            }
            for comparison in analysis.comparisons
        ],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def _distances_csv(analysis: Analysis) -> str:
    output = StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(("left", "right", "distance", "right_index_shift"))
    for comparison in analysis.comparisons:
        writer.writerow(
            (
                comparison.left,
                comparison.right,
                f"{comparison.distance:.6f}",
                comparison.right_index_shift,
            )
        )
    return output.getvalue()


def _series_color(profile: Profile) -> str:
    red, green, blue = max(profile.points, key=lambda point: point.strength).rgb
    return f"#{red:02x}{green:02x}{blue:02x}"


def _profiles_svg(analysis: Analysis) -> str:
    plot_left = 72
    plot_right = 848
    plot_top = 50
    plot_bottom = 330
    maximum = max(profile.peak_signal for profile in analysis.profiles)
    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 420" '
        'role="img" aria-labelledby="plot-title plot-description">',
        '<title id="plot-title">InkChroma signal profiles</title>',
        '<desc id="plot-description">Paper-normalized Delta E signal by normalized Rf.</desc>',
        '<rect width="900" height="420" fill="#fbfaf6"/>',
        f'<path d="M {plot_left} {plot_top} V {plot_bottom} H {plot_right}" '
        'fill="none" stroke="#504c46" stroke-width="1.5"/>',
    ]
    for tick in (0.0, 0.5, 1.0):
        x = plot_left + tick * (plot_right - plot_left)
        lines.append(
            f'<path d="M {x:.1f} {plot_bottom} v 6" stroke="#504c46"/>'
            f'<text x="{x:.1f}" y="354" text-anchor="middle">{tick:.1f}</text>'
        )
    lines.extend(
        (
            '<text x="460" y="385" text-anchor="middle">Normalized Rf</text>',
            '<text x="20" y="190" text-anchor="middle" transform="rotate(-90 20 190)">'
            "Paper-normalized signal (Delta E 76)</text>",
            f'<text x="{plot_left - 8}" y="{plot_bottom + 5}" text-anchor="end">0</text>',
            f'<text x="{plot_left - 8}" y="{plot_top + 5}" text-anchor="end">{maximum:.2f}</text>',
        )
    )
    for index, profile in enumerate(analysis.profiles):
        coordinates = " ".join(
            f"{plot_left + point.rf * (plot_right - plot_left):.2f},"
            f"{plot_bottom - point.strength / maximum * (plot_bottom - plot_top):.2f}"
            for point in profile.points
        )
        color = _series_color(profile)
        lines.append(
            f'<polyline points="{coordinates}" fill="none" stroke="{color}" '
            'stroke-width="2.5" vector-effect="non-scaling-stroke"/>'
        )
        legend_y = 30 + index * 22
        lines.append(
            f'<path d="M 620 {legend_y} h 24" stroke="{color}" stroke-width="3"/>'
            f'<text x="652" y="{legend_y + 4}">{escape(profile.name)}</text>'
        )
    lines.append("<style>text{font:14px system-ui,sans-serif;fill:#292724}</style></svg>\n")
    return "".join(lines)


def _report_html(analysis: Analysis, svg: str) -> str:
    warning_items = "".join(f"<li>{escape(warning)}</li>" for warning in analysis.warnings)
    sample_rows = "".join(
        "<tr>"
        f"<td>{escape(profile.name)}</td>"
        f"<td>{profile.peak_signal:.2f}</td>"
        f"<td>{len(profile.bands)}</td>"
        "</tr>"
        for profile in analysis.profiles
    )
    band_rows = "".join(
        "<tr>"
        f"<td>{escape(profile.name)}</td>"
        f"<td>{band.rf_center:.3f}</td>"
        f"<td>{band.rf_start:.3f}&ndash;{band.rf_end:.3f}</td>"
        f"<td>{band.peak_signal:.2f}</td>"
        f'<td><span class="swatch" style="background:rgb{band.rgb}"></span> {band.rgb}</td>'
        "</tr>"
        for profile in analysis.profiles
        for band in profile.bands
    )
    comparison_rows = "".join(
        "<tr>"
        f"<td>{escape(comparison.left)}</td>"
        f"<td>{escape(comparison.right)}</td>"
        f"<td>{comparison.distance:.3f}</td>"
        f"<td>{comparison.right_index_shift:+d}</td>"
        "</tr>"
        for comparison in analysis.comparisons
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>InkChroma report</title>
<style>
body{{max-width:980px;margin:36px auto;padding:0 20px;color:#292724;
background:#fbfaf6;font:16px/1.5 system-ui,sans-serif}}
h1,h2{{line-height:1.15}}
table{{border-collapse:collapse;width:100%;margin:12px 0 28px}}
th,td{{border-bottom:1px solid #d8d2c7;padding:8px;text-align:left}}
th{{background:#eee9df}}
.notice{{padding:12px 18px;background:#f1ead5;border-left:4px solid #aa7b20}}
.swatch{{display:inline-block;width:1em;height:1em;border:1px solid #777;
vertical-align:-.12em}}
svg{{width:100%;height:auto;border:1px solid #d8d2c7;background:#fff}}
</style>
</head>
<body>
<h1>InkChroma comparison</h1>
<p>Lower distance means more visually similar paper-normalized profiles within this project.</p>
<div class="notice"><strong>Interpretation limits</strong><ul>{warning_items}</ul></div>
<h2>Samples</h2>
<table>
<thead><tr><th>Sample</th><th>Peak Delta E</th><th>Bands</th></tr></thead>
<tbody>{sample_rows}</tbody>
</table>
<h2>Signal profiles</h2>{svg}
<h2>Detected bands</h2>
<table>
<thead><tr><th>Sample</th><th>Rf center</th><th>Rf span</th>
<th>Peak Delta E</th><th>Representative RGB</th></tr></thead>
<tbody>{band_rows}</tbody>
</table>
<h2>Pair distances</h2>
<table>
<thead><tr><th>Left</th><th>Right</th><th>Distance</th>
<th>Right index shift</th></tr></thead>
<tbody>{comparison_rows}</tbody>
</table>
<p>The shift is the right profile index paired with each left index;
positive values sample the right profile at a higher Rf position.</p>
</body>
</html>
"""


def write_reports(project: Project, analysis: Analysis, output: Path) -> tuple[Path, ...]:
    if output.exists():
        raise InputError(
            f"output directory '{output}' already exists; choose a new --out path or remove it"
        )
    if not output.parent.is_dir():
        raise InputError(
            f"output parent '{output.parent}' does not exist; create it or choose a new --out path"
        )

    svg = _profiles_svg(analysis)
    rendered = {
        "analysis.json": _analysis_json(project, analysis),
        "distances.csv": _distances_csv(analysis),
        "profiles.svg": svg,
        "report.html": _report_html(analysis, svg),
    }
    try:
        with TemporaryDirectory(prefix=f".{output.name}.", dir=output.parent) as temporary:
            temporary_path = Path(temporary)
            for name in REPORT_NAMES:
                (temporary_path / name).write_text(
                    rendered[name],
                    encoding="utf-8",
                    newline="\n",
                )
            temporary_path.replace(output)
    except OSError as error:
        detail = error.strerror or str(error)
        raise InputError(
            f"cannot write output directory '{output}': {detail}; check the parent permissions"
        ) from error
    return tuple(output / name for name in REPORT_NAMES)
