# InkChroma

[![CI](https://github.com/KanadeK/inkchroma/actions/workflows/ci.yml/badge.svg)](https://github.com/KanadeK/inkchroma/actions/workflows/ci.yml)
[![GitHub release](https://img.shields.io/github/v/release/KanadeK/inkchroma)](https://github.com/KanadeK/inkchroma/releases/latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**Turn marked paper-chromatography strip scans into inspectable color profiles and
ranked relative distances, entirely offline.**

InkChroma is for fountain-pen ink hobbyists who want to compare how inks separate
on paper without sending scans to a service or treating visual similarity as a
chemical identification. It reads real PNG/JPEG pixels, subtracts the local paper
color, normalizes the travel interval, detects visible bands, and compares every
sample pair.

## 60-second quick start

Requires Python 3.11–3.14. The v0.1.0 wheel and example bundle are attached to the
[GitHub Release](https://github.com/KanadeK/inkchroma/releases/tag/v0.1.0).

```console
python -m pip install https://github.com/KanadeK/inkchroma/releases/download/v0.1.0/inkchroma-0.1.0-py3-none-any.whl
curl -LO https://github.com/KanadeK/inkchroma/releases/download/v0.1.0/inkchroma-examples-v0.1.0.zip
python -m zipfile -e inkchroma-examples-v0.1.0.zip inkchroma-examples-v0.1.0
inkchroma compare inkchroma-examples-v0.1.0/blue-family/project.json --out inkchroma-report
```

The final command prints:

```text
Wrote 4 reports to inkchroma-report
Open inkchroma-report/report.html
```

Open `report.html` locally. The bundled synthetic example produces this real pair
ranking (lower is closer):

```csv
left,right,distance,right_index_shift
midnight-a,midnight-b,3.231115,-1
midnight-b,pine-green,45.417560,0
midnight-a,pine-green,46.833682,0
```

## What you provide

For each straight strip scan, identify:

- the lane's left edge (`x_start`, inclusive) and right edge (`x_end`, exclusive);
- the solvent-front row near the top;
- the origin row near the bottom.

Leave at least two visible paper pixels on both sides of the lane. Put two or more
samples in a UTF-8 JSON project file. Image paths are relative to that file.

```json
{
  "schema_version": 1,
  "profile_points": 96,
  "minimum_signal_delta_e": 2.0,
  "samples": [
    {
      "name": "blue-a",
      "image": "blue-a.png",
      "lane": {"x_start": 24, "x_end": 56},
      "solvent_front_y": 18,
      "origin_y": 220
    },
    {
      "name": "blue-b",
      "image": "blue-b.jpg",
      "lane": {"x_start": 24, "x_end": 56},
      "solvent_front_y": 18,
      "origin_y": 220
    }
  ]
}
```

Run it into a new output directory:

```console
inkchroma compare project.json --out inkchroma-report
```

## What you get

| File | Purpose |
| --- | --- |
| `analysis.json` | Settings, limitations, full signed CIE Lab profiles, detected bands, and comparisons |
| `distances.csv` | Spreadsheet-ready pairs ordered from lowest to highest relative distance |
| `profiles.svg` | Standalone vector plot of paper-normalized signal against Rf |
| `report.html` | Self-contained, script-free local report with the plot and summary tables |

InkChroma averages each scan row inside the lane and on the surrounding paper,
converts both colors to CIE Lab, and stores the signed lane-minus-paper vector. It
resamples origin-to-front travel to a common Rf grid, smooths once, groups contiguous
above-threshold points into bands, then calculates RMS vector distance with a
transparent ±2-point alignment search.

Positive `right_index_shift` means each left profile point was compared with a
higher-Rf index in the right profile. Distance is only useful relative to other
pairs from comparable scans; it is not a probability or pass/fail decision.

## Included examples

The [`examples`](examples) directory contains deterministic synthetic PNG inputs,
not hard-coded analysis results:

- `blue-family`: complete three-sample success path;
- `different-sizes`: boundary case proving scans of different heights normalize to
  the same profile length;
- `blank-strip`: deliberate failure with no output directory left behind.

From a source checkout:

```console
uv sync --locked --group dev
uv run inkchroma compare examples/blue-family/project.json --out demo-output
```

## Known limits

- InkChroma measures visible separation in comparable consumer scans. It cannot
  establish ink identity, concentration, authenticity, safety, or forensic proof.
- Results assume similar paper, scanner/camera, lighting, exposure, and sRGB-like
  color. v0.1.0 does not apply ICC profiles or cross-device calibration.
- Cropping and lane/origin/front coordinates are manual. There is no perspective
  correction, automatic lane detection, or peak-model fitting.
- Band detection is one Delta E threshold and comparison alignment is limited to
  two profile points. Large geometric differences should be rescanned.
- PNG and JPEG are the supported inputs. Other Pillow-decodable formats are
  rejected in v0.1.0.
- Output is intentionally non-destructive: its parent must exist and the selected
  output directory must be new.

## Troubleshooting

InkChroma exits with code `2`, names the affected input, and gives a repair action.
It completes analysis before creating the output directory.

| Message contains | What to do |
| --- | --- |
| `project file ... does not exist` | Correct the project path. |
| `image ... does not exist` | Correct the image path relative to the JSON file. |
| `cannot decode image` | Export the scan as PNG or JPEG. |
| `lane needs at least two paper pixels on each side` | Crop wider or narrow the lane coordinates. |
| `coordinates exceed the ... image` | Recheck lane, origin, and front against the intended image. |
| `no measurable ink signal` | Rescan with more contrast or deliberately lower `minimum_signal_delta_e`. |
| `output directory ... already exists` | Choose a new `--out` path or remove the old report yourself. |

## Development

The single local/CI acceptance command installs no shortcuts and exercises real
images, failures, packaging, a clean wheel install, and the installed console entry:

```console
uv sync --locked --group dev
uv run python scripts/check.py
```

See [`docs/spec.md`](docs/spec.md) for the exact processing contract and
[`docs/selection.md`](docs/selection.md) for the candidate and nearest-neighbor
study. InkChroma has no runtime network calls; your scans stay on your machine.

Released under the MIT License.
